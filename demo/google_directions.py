"""Google Maps Directions API integration with caching and fallback."""

import hashlib
import json
import logging
import os
import re
import time
import urllib.request
import urllib.error

from config import (
    GOOGLE_MAPS_API_KEY, GOOGLE_DIRECTIONS_BASE_URL,
    DIRECTIONS_CACHE_DIR, DIRECTIONS_CACHE_TTL_DAYS, GOOGLE_API_TIMEOUT
)

logger = logging.getLogger(__name__)


def is_available():
    """Check if Google Directions API is configured."""
    return bool(GOOGLE_MAPS_API_KEY)


def decode_polyline(encoded):
    """Decode a Google Maps encoded polyline into a list of {lat, lng} dicts."""
    points = []
    index = 0
    lat = 0
    lng = 0

    while index < len(encoded):
        for _ in range(2):
            shift = 0
            result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if (result & 1) else (result >> 1)
            if _ == 0:
                lat += delta
            else:
                lng += delta
        points.append({'lat': lat / 1e5, 'lng': lng / 1e5})

    return points


def _build_cache_key(origin, destination, mode):
    """Build a deterministic cache key from coordinates and travel mode."""
    o_lat, o_lng = round(origin[0], 5), round(origin[1], 5)
    d_lat, d_lng = round(destination[0], 5), round(destination[1], 5)
    raw = f"{o_lat},{o_lng}_{d_lat},{d_lng}_{mode}"
    return hashlib.md5(raw.encode()).hexdigest()


def _load_from_cache(cache_key):
    """Load a cached directions response. Returns None if missing or expired."""
    cache_path = os.path.join(DIRECTIONS_CACHE_DIR, f"{cache_key}.json")
    if not os.path.exists(cache_path):
        return None

    age_days = (time.time() - os.path.getmtime(cache_path)) / 86400
    if age_days > DIRECTIONS_CACHE_TTL_DAYS:
        try:
            os.remove(cache_path)
        except OSError:
            pass
        return None

    try:
        with open(cache_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Cache read error for {cache_key}: {e}")
        return None


def _save_to_cache(cache_key, data):
    """Save a directions response to the file cache."""
    try:
        os.makedirs(DIRECTIONS_CACHE_DIR, exist_ok=True)
        cache_path = os.path.join(DIRECTIONS_CACHE_DIR, f"{cache_key}.json")
        with open(cache_path, 'w') as f:
            json.dump(data, f)
    except OSError as e:
        logger.warning(f"Cache write error for {cache_key}: {e}")


def _call_google_api(origin, destination, mode):
    """Make an HTTP request to the Google Directions API.

    Returns the parsed JSON response or None on failure.
    """
    params = (
        f"?origin={origin[0]},{origin[1]}"
        f"&destination={destination[0]},{destination[1]}"
        f"&mode={mode}"
        f"&alternatives=false"
        f"&units=metric"
        f"&key={GOOGLE_MAPS_API_KEY}"
    )
    url = GOOGLE_DIRECTIONS_BASE_URL + params

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=GOOGLE_API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            if data.get('status') != 'OK':
                logger.warning(f"Google Directions API status: {data.get('status')} - {data.get('error_message', '')}")
                return None
            if not data.get('routes'):
                logger.warning("Google Directions API returned no routes")
                return None
            return data['routes'][0]
    except urllib.error.URLError as e:
        logger.warning(f"Google Directions API network error: {e}")
        return None
    except Exception as e:
        logger.warning(f"Google Directions API error: {e}")
        return None


def get_directions(origin, destination, mode='walking'):
    """Get directions between two points.

    Args:
        origin: (lat, lng) tuple
        destination: (lat, lng) tuple
        mode: 'walking' or 'driving'

    Returns:
        Parsed route dict from parse_directions_to_waypoints(), or None on failure.
    """
    if not is_available():
        return None

    cache_key = _build_cache_key(origin, destination, mode)

    cached = _load_from_cache(cache_key)
    if cached:
        logger.debug(f"Directions cache hit: {mode} {origin} -> {destination}")
        return cached

    route = _call_google_api(origin, destination, mode)
    if not route:
        return None

    parsed = parse_directions_to_waypoints(route)
    _save_to_cache(cache_key, parsed)
    return parsed


def parse_directions_to_waypoints(route):
    """Convert a Google Directions API route into the app's waypoint/step format.

    Args:
        route: A single route object from Google's response.

    Returns:
        dict with keys: distance_meters, duration_seconds, waypoints, steps
    """
    leg = route['legs'][0]

    # Build waypoints from step-level polylines for high-resolution path
    waypoints = []
    for step in leg['steps']:
        encoded = step.get('polyline', {}).get('points', '')
        if encoded:
            decoded = decode_polyline(encoded)
            # Avoid duplicating the last point of the previous step
            if waypoints and decoded and waypoints[-1] == decoded[0]:
                decoded = decoded[1:]
            waypoints.extend(decoded)

    # If polyline decoding produced nothing, fall back to start/end locations
    if not waypoints:
        waypoints = [
            {'lat': leg['start_location']['lat'], 'lng': leg['start_location']['lng']},
            {'lat': leg['end_location']['lat'], 'lng': leg['end_location']['lng']}
        ]

    # Build step instructions
    steps = []
    for step in leg['steps']:
        instruction = step.get('html_instructions', '')
        instruction = re.sub(r'<[^>]+>', ' ', instruction).strip()
        instruction = re.sub(r'\s+', ' ', instruction)

        steps.append({
            'instruction': instruction,
            'distance_meters': step.get('distance', {}).get('value', 0),
            'time_seconds': step.get('duration', {}).get('value', 0),
            'from': {
                'lat': step['start_location']['lat'],
                'lng': step['start_location']['lng']
            },
            'to': {
                'lat': step['end_location']['lat'],
                'lng': step['end_location']['lng']
            }
        })

    return {
        'distance_meters': leg.get('distance', {}).get('value', 0),
        'duration_seconds': leg.get('duration', {}).get('value', 0),
        'waypoints': waypoints,
        'steps': steps
    }
