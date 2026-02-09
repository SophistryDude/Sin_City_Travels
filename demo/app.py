#!/usr/bin/env python3
"""Sin City Travels - Interactive Web Demo"""
import math
import os
import re
import sys
import time as _time
from decimal import Decimal

from flask import Flask, render_template, jsonify, request
from flask.json.provider import DefaultJSONProvider
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    MAP_CONFIG, WALK_THRESHOLD_METERS, WALK_SPEED_MPS,
    UBER_RATES, LYFT_RATES, RIDESHARE_AVG_SPEED_MPH
)
from db import init_pool, query
import google_directions


class CustomJSONProvider(DefaultJSONProvider):
    """Handle Decimal serialization from PostgreSQL."""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


app = Flask(__name__)
app.json = CustomJSONProvider(app)

# Rate limiting (in-memory, no Redis needed for single-server)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per hour", "50 per minute"],
    storage_uri="memory://",
)

# ─── Validation ──────────────────────────────────────────────────────────────

VALID_CATEGORIES = {'restaurant', 'shopping', 'entertainment', 'nightlife',
                    'pool_spa', 'attraction', 'casino', 'hotel'}
POI_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,20}$')


def validate_poi_id(poi_id):
    return bool(POI_ID_PATTERN.match(poi_id))


# ─── Error handlers ─────────────────────────────────────────────────────────

@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': str(e.description)}), 400


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded', 'retry_after': e.description}), 429


@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f'Internal error: {e}')
    return jsonify({'error': 'Internal server error'}), 500


# Initialize DB pool (works with both gunicorn and direct python run)
init_pool()


# ─── Health check ────────────────────────────────────────────────────────────

@app.route('/api/health')
@limiter.exempt
def api_health():
    health = {
        'status': 'ok',
        'timestamp': _time.strftime('%Y-%m-%dT%H:%M:%SZ', _time.gmtime()),
        'version': '2.5',
    }
    try:
        query("SELECT 1 AS ok", fetchone=True)
        health['database'] = 'connected'
    except Exception:
        health['status'] = 'degraded'
        health['database'] = 'disconnected'
    status_code = 200 if health['status'] == 'ok' else 503
    return jsonify(health), status_code


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', map_config=MAP_CONFIG)


@app.route('/api/pois')
@limiter.limit("60 per minute")
def api_pois():
    category = request.args.get('category')
    if category and category not in VALID_CATEGORIES:
        return jsonify({'error': f'Invalid category. Must be one of: {", ".join(sorted(VALID_CATEGORIES))}'}), 400
    sql = """
        SELECT id, name, category::text, subcategory::text, casino_property,
               ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
               description, cuisine, features, chef, price_range::text,
               hours, ratings, phone, website, area, dress_code,
               average_per_person, level
        FROM pois
        WHERE (%s IS NULL OR category = %s::poi_category)
          AND is_closed = FALSE
        ORDER BY casino_property, name
    """
    rows = query(sql, (category, category))
    return jsonify(rows)


@app.route('/api/pois/recommended')
def api_pois_recommended():
    sql = """
        SELECT id, name, category::text, subcategory::text, casino_property,
               ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
               description, cuisine, features, chef, price_range::text,
               hours, ratings, phone, website, area, dress_code,
               average_per_person, level, tags
        FROM pois
        WHERE tags @> ARRAY['recommended']
          AND is_closed = FALSE
        ORDER BY name
    """
    rows = query(sql)
    return jsonify(rows)


@app.route('/api/properties')
def api_properties():
    sql = """
        SELECT id, name,
               ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
               area, owner, room_count, casino_sq_ft, features, amenities
        FROM properties ORDER BY id
    """
    return jsonify(query(sql))


@app.route('/api/nearby')
@limiter.limit("30 per minute")
def api_nearby():
    try:
        lat = float(request.args['lat'])
        lng = float(request.args['lng'])
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'lat and lng are required and must be numbers'}), 400

    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return jsonify({'error': 'lat must be -90..90, lng must be -180..180'}), 400

    try:
        radius = float(request.args.get('radius', 500))
    except (ValueError, TypeError):
        return jsonify({'error': 'radius must be a number'}), 400
    radius = min(radius, 5000)  # cap at 5 km

    category = request.args.get('category') or None
    if category and category not in VALID_CATEGORIES:
        return jsonify({'error': f'Invalid category. Must be one of: {", ".join(sorted(VALID_CATEGORIES))}'}), 400

    if category:
        sql = "SELECT * FROM find_nearby_pois(%s, %s, %s, %s::poi_category)"
        rows = query(sql, (lat, lng, radius, category))
    else:
        sql = "SELECT * FROM find_nearby_pois(%s, %s, %s)"
        rows = query(sql, (lat, lng, radius))
    return jsonify(rows)


@app.route('/api/route/<start_id>/<end_id>')
def api_route(start_id, end_id):
    if not validate_poi_id(start_id) or not validate_poi_id(end_id):
        return jsonify({'error': 'Invalid POI ID format'}), 400
    # Get synthetic route
    route_sql = """
        SELECT sr.id, sr.total_distance_meters, sr.estimated_time_seconds,
               sr.path_nodes, sr.has_stairs, sr.has_elevator, sr.accessibility_score,
               sr.property_id
        FROM synthetic_routes sr
        WHERE sr.start_poi_id = %s AND sr.end_poi_id = %s
        LIMIT 1
    """
    route = query(route_sql, (start_id, end_id), fetchone=True)

    # Get start/end POI info
    poi_sql = """
        SELECT id, name, ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng
        FROM pois WHERE id IN (%s, %s)
    """
    pois_data = query(poi_sql, (start_id, end_id))
    poi_map = {p['id']: p for p in pois_data}

    start_poi = poi_map.get(start_id)
    end_poi = poi_map.get(end_id)

    if not route:
        # Fallback: straight line with calculated distance
        dist_sql = "SELECT calculate_poi_distance(%s, %s) AS dist"
        dist = query(dist_sql, (start_id, end_id), fetchone=True)
        distance = float(dist['dist']) if dist and dist['dist'] else 0
        return jsonify({
            'found': False,
            'start': start_poi,
            'end': end_poi,
            'distance_meters': distance,
            'estimated_time_seconds': int(distance / 1.4) if distance else 0,
            'waypoints': [start_poi, end_poi]
        })

    # Resolve path_nodes to coordinates
    waypoints = []
    if route['path_nodes']:
        nodes_sql = """
            SELECT id, ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
                   node_type, indoor_level
            FROM navigation_nodes
            WHERE id = ANY(%s) AND property_id = %s
        """
        nodes = query(nodes_sql, (route['path_nodes'], route['property_id']))
        node_map = {n['id']: n for n in nodes}
        for nid in route['path_nodes']:
            if nid in node_map:
                waypoints.append(node_map[nid])

    # Ensure start/end are included
    if len(waypoints) < 2:
        waypoints = [start_poi, end_poi]
    else:
        waypoints.insert(0, start_poi)
        waypoints.append(end_poi)

    return jsonify({
        'found': True,
        'start': start_poi,
        'end': end_poi,
        'distance_meters': route['total_distance_meters'],
        'estimated_time_seconds': route['estimated_time_seconds'],
        'has_stairs': route['has_stairs'],
        'has_elevator': route['has_elevator'],
        'accessibility_score': route['accessibility_score'],
        'waypoints': waypoints
    })


@app.route('/api/distance/<poi1_id>/<poi2_id>')
def api_distance(poi1_id, poi2_id):
    if not validate_poi_id(poi1_id) or not validate_poi_id(poi2_id):
        return jsonify({'error': 'Invalid POI ID format'}), 400
    sql = "SELECT calculate_poi_distance(%s, %s) AS distance_meters"
    result = query(sql, (poi1_id, poi2_id), fetchone=True)
    return jsonify(result)


# ─── Multi-Leg Navigation ────────────────────────────────────────────────────

def calculate_bearing(lat1, lng1, lat2, lng2):
    """Calculate compass bearing between two points in degrees."""
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    d_lng = lng2 - lng1
    x = math.sin(d_lng) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lng)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def bearing_to_direction(bearing):
    """Convert bearing in degrees to cardinal direction string."""
    directions = ['north', 'northeast', 'east', 'southeast',
                  'south', 'southwest', 'west', 'northwest']
    idx = round(bearing / 45) % 8
    return directions[idx]


def turn_instruction(prev_bearing, curr_bearing):
    """Compute turn instruction from change in bearing."""
    diff = (curr_bearing - prev_bearing + 360) % 360
    if diff < 30 or diff > 330:
        return 'continue straight'
    elif diff < 170:
        return 'turn right' if diff < 90 else 'turn sharp right'
    elif diff > 190:
        return 'turn left' if diff > 270 else 'turn sharp left'
    else:
        return 'make a U-turn'


def haversine(lat1, lng1, lat2, lng2):
    """Calculate distance in meters between two lat/lng points."""
    R = 6371000
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_rideshare_fare(distance_meters):
    """Estimate Uber and Lyft fares from distance."""
    miles = distance_meters / 1609.34
    # Estimate travel time at avg Strip speed
    minutes = (miles / RIDESHARE_AVG_SPEED_MPH) * 60
    eta_minutes = max(3, round(minutes + 2))  # +2 min for pickup

    def calc_fare(rates):
        fare = (rates['base_fare'] +
                rates['per_minute'] * minutes +
                rates['per_mile'] * miles +
                rates['booking_fee'])
        return max(rates['min_fare'], round(fare, 2))

    uber_fare = calc_fare(UBER_RATES)
    lyft_fare = calc_fare(LYFT_RATES)

    return {
        'uber': {
            'estimate_low': round(uber_fare * 0.85, 2),
            'estimate_high': round(uber_fare * 1.25, 2),
            'eta_minutes': eta_minutes
        },
        'lyft': {
            'estimate_low': round(lyft_fare * 0.85, 2),
            'estimate_high': round(lyft_fare * 1.25, 2),
            'eta_minutes': eta_minutes
        },
        'distance_miles': round(miles, 2),
        'estimated_drive_minutes': round(minutes, 1)
    }


def generate_rideshare_links(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, dest_name):
    """Generate Uber and Lyft deep links."""
    return {
        'uber': (
            f"https://m.uber.com/ul/?action=setPickup"
            f"&pickup[latitude]={pickup_lat}&pickup[longitude]={pickup_lng}"
            f"&dropoff[latitude]={dropoff_lat}&dropoff[longitude]={dropoff_lng}"
            f"&dropoff[nickname]={dest_name}"
        ),
        'lyft': (
            f"https://lyft.com/ride?id=lyft"
            f"&pickup[latitude]={pickup_lat}&pickup[longitude]={pickup_lng}"
            f"&destination[latitude]={dropoff_lat}&destination[longitude]={dropoff_lng}"
        )
    }


def generate_turn_by_turn(waypoints):
    """Generate step-by-step text directions from an ordered list of waypoints."""
    if len(waypoints) < 2:
        return []

    steps = []
    prev_bearing = None

    for i in range(len(waypoints) - 1):
        wp = waypoints[i]
        wp_next = waypoints[i + 1]

        lat1, lng1 = wp['lat'], wp['lng']
        lat2, lng2 = wp_next['lat'], wp_next['lng']

        bearing = calculate_bearing(lat1, lng1, lat2, lng2)
        dist = haversine(lat1, lng1, lat2, lng2)
        direction = bearing_to_direction(bearing)

        # Build instruction
        node_type = wp.get('node_type', '')
        next_type = wp_next.get('node_type', '')
        node_name = wp.get('name', '')

        if i == 0:
            instruction = f"Head {direction}"
            if node_name:
                instruction += f" from {node_name}"
        elif node_type == 'elevator':
            target_level = wp_next.get('indoor_level', '')
            instruction = f"Take elevator to Level {target_level}" if target_level else "Take the elevator"
        elif node_type == 'stairs':
            instruction = "Take the stairs"
        elif node_type == 'entrance':
            role = wp.get('entrance_role', 'main')
            if role == 'rideshare_pickup':
                instruction = "Head to the rideshare pickup area"
            else:
                instruction = f"Exit through {node_name}" if node_name else "Exit through the main entrance"
        elif prev_bearing is not None:
            turn = turn_instruction(prev_bearing, bearing)
            if turn == 'continue straight':
                instruction = f"Continue straight {direction}"
            else:
                instruction = turn.capitalize()
                if wp_next.get('name'):
                    instruction += f" toward {wp_next['name']}"
        else:
            instruction = f"Continue {direction}"

        # Add distance info
        if next_type == 'entrance':
            next_name = wp_next.get('name', 'the entrance')
            next_role = wp_next.get('entrance_role', '')
            if next_role == 'rideshare_pickup':
                instruction += " to the rideshare pickup area"
            else:
                instruction += f" to {next_name}"

        time_secs = int(dist / WALK_SPEED_MPS) if dist > 0 else 0

        steps.append({
            'instruction': instruction,
            'distance_meters': round(dist, 1),
            'time_seconds': time_secs,
            'from': {'lat': lat1, 'lng': lng1},
            'to': {'lat': lat2, 'lng': lng2}
        })

        prev_bearing = bearing

    return steps


def get_indoor_waypoints(poi_id, entrance_node_id, property_name, reverse=False):
    """Get waypoints for an indoor leg from a POI to an entrance (or reverse)."""
    # Get the POI location
    poi_sql = """
        SELECT id, name, ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
               level, area, casino_property
        FROM pois WHERE id = %s
    """
    poi = query(poi_sql, (poi_id,), fetchone=True)

    # Get the entrance node
    node_sql = """
        SELECT id, name, node_type, entrance_role, indoor_level,
               ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng
        FROM navigation_nodes WHERE id = %s
    """
    entrance = query(node_sql, (entrance_node_id,), fetchone=True)

    if not poi or not entrance:
        return [], []

    # Find intermediate nodes along the path (within same property)
    path_sql = """
        SELECT nn.id, nn.name, nn.node_type, nn.entrance_role, nn.indoor_level,
               ST_Y(nn.location::geometry) AS lat, ST_X(nn.location::geometry) AS lng
        FROM navigation_nodes nn
        JOIN properties p ON nn.property_id = p.id
        WHERE p.name = %s
          AND nn.id != %s
          AND nn.node_type IN ('junction', 'elevator', 'stairs')
        ORDER BY ST_Distance(
            nn.location,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
        )
        LIMIT 3
    """
    intermediate = query(path_sql, (property_name, entrance_node_id, poi['lng'], poi['lat']))

    # Build waypoint sequence
    poi_wp = {
        'lat': float(poi['lat']), 'lng': float(poi['lng']),
        'name': poi['name'], 'node_type': 'poi'
    }
    ent_wp = {
        'lat': float(entrance['lat']), 'lng': float(entrance['lng']),
        'name': entrance['name'] or 'Entrance',
        'node_type': entrance['node_type'],
        'entrance_role': entrance.get('entrance_role', 'main'),
        'indoor_level': entrance.get('indoor_level')
    }

    if reverse:
        # Entrance -> intermediate -> POI
        waypoints = [ent_wp]
        for node in intermediate[:2]:
            waypoints.append({
                'lat': float(node['lat']), 'lng': float(node['lng']),
                'name': node['name'] or node['node_type'],
                'node_type': node['node_type'],
                'indoor_level': node.get('indoor_level')
            })
        waypoints.append(poi_wp)
    else:
        # POI -> intermediate -> Entrance
        waypoints = [poi_wp]
        for node in intermediate[:2]:
            waypoints.append({
                'lat': float(node['lat']), 'lng': float(node['lng']),
                'name': node['name'] or node['node_type'],
                'node_type': node['node_type'],
                'indoor_level': node.get('indoor_level')
            })
        waypoints.append(ent_wp)

    # Calculate total distance
    total_dist = 0
    for i in range(len(waypoints) - 1):
        total_dist += haversine(waypoints[i]['lat'], waypoints[i]['lng'],
                                waypoints[i+1]['lat'], waypoints[i+1]['lng'])

    return waypoints, total_dist


@app.route('/api/navigate', methods=['POST'])
@limiter.limit("20 per minute")
def api_navigate():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    start_poi_id = data.get('start_poi_id')
    end_poi_id = data.get('end_poi_id')

    if not start_poi_id or not end_poi_id:
        return jsonify({'error': 'start_poi_id and end_poi_id required'}), 400
    if not validate_poi_id(start_poi_id) or not validate_poi_id(end_poi_id):
        return jsonify({'error': 'Invalid POI ID format'}), 400
    if start_poi_id == end_poi_id:
        return jsonify({'error': 'Start and end POI must be different'}), 400

    # 1. Look up both POIs
    poi_sql = """
        SELECT id, name, category::text, casino_property,
               ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
               level, area
        FROM pois WHERE id = %s
    """
    start_poi = query(poi_sql, (start_poi_id,), fetchone=True)
    end_poi = query(poi_sql, (end_poi_id,), fetchone=True)

    if not start_poi or not end_poi:
        return jsonify({'error': 'POI not found'}), 404

    start_property = start_poi['casino_property']
    end_property = end_poi['casino_property']

    legs = []

    if start_property == end_property:
        # ─── Same Property: single indoor leg ───
        # Find existing synthetic route
        route_sql = """
            SELECT total_distance_meters, estimated_time_seconds, path_nodes,
                   has_stairs, has_elevator
            FROM synthetic_routes
            WHERE start_poi_id = %s AND end_poi_id = %s
            LIMIT 1
        """
        route = query(route_sql, (start_poi_id, end_poi_id), fetchone=True)

        # Build waypoints from path_nodes if available
        waypoints = [{
            'lat': float(start_poi['lat']), 'lng': float(start_poi['lng']),
            'name': start_poi['name'], 'node_type': 'poi'
        }]

        if route and route['path_nodes']:
            nodes_sql = """
                SELECT id, name, node_type, indoor_level,
                       ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng
                FROM navigation_nodes WHERE id = ANY(%s)
            """
            nodes = query(nodes_sql, (route['path_nodes'],))
            node_map = {n['id']: n for n in nodes}
            for nid in route['path_nodes']:
                if nid in node_map:
                    n = node_map[nid]
                    waypoints.append({
                        'lat': float(n['lat']), 'lng': float(n['lng']),
                        'name': n['name'] or n['node_type'],
                        'node_type': n['node_type'],
                        'indoor_level': n.get('indoor_level')
                    })

        waypoints.append({
            'lat': float(end_poi['lat']), 'lng': float(end_poi['lng']),
            'name': end_poi['name'], 'node_type': 'poi'
        })

        total_dist = 0
        for i in range(len(waypoints) - 1):
            total_dist += haversine(waypoints[i]['lat'], waypoints[i]['lng'],
                                    waypoints[i+1]['lat'], waypoints[i+1]['lng'])

        # Use the larger of waypoint-path distance or stored route distance
        if route and float(route['total_distance_meters']) > total_dist:
            total_dist = float(route['total_distance_meters'])

        steps = generate_turn_by_turn(waypoints)

        legs.append({
            'leg_type': 'indoor',
            'leg_number': 1,
            'label': f'Walk through {start_property}',
            'transport': 'walk',
            'property': start_property,
            'distance_meters': round(total_dist, 1),
            'estimated_time_seconds': int(total_dist / WALK_SPEED_MPS),
            'steps': steps,
            'waypoints': waypoints,
            'has_stairs': route['has_stairs'] if route else False,
            'has_elevator': route['has_elevator'] if route else False
        })

    else:
        # ─── Different Property ───
        # Get property distance
        dist_sql = """
            SELECT distance_meters FROM property_distances
            WHERE from_property_name = %s AND to_property_name = %s
        """
        prop_dist = query(dist_sql, (start_property, end_property), fetchone=True)
        inter_property_dist = float(prop_dist['distance_meters']) if prop_dist else 1000

        # Find nearest entrances
        start_entrance_sql = """
            SELECT * FROM find_nearest_entrance(%s, %s)
        """
        end_entrance_sql = """
            SELECT * FROM find_nearest_entrance(%s, %s)
        """

        if inter_property_dist <= WALK_THRESHOLD_METERS:
            # Walking route: use main entrances
            start_ent = query(start_entrance_sql, (start_poi_id, 'main'), fetchone=True)
            end_ent = query(end_entrance_sql, (end_poi_id, 'main'), fetchone=True)
            transport_mode = 'walk'
        else:
            # Rideshare route: use rideshare pickup nodes
            start_ent = query(start_entrance_sql, (start_poi_id, 'rideshare_pickup'), fetchone=True)
            end_ent = query(end_entrance_sql, (end_poi_id, 'rideshare_pickup'), fetchone=True)
            transport_mode = 'rideshare'

        # Fallback if no rideshare nodes found
        if not start_ent:
            start_ent = query(start_entrance_sql, (start_poi_id, 'main'), fetchone=True)
        if not end_ent:
            end_ent = query(end_entrance_sql, (end_poi_id, 'main'), fetchone=True)

        # Fallback: use POI coords directly if no entrances
        if not start_ent:
            start_ent = {
                'node_id': None, 'node_name': start_property + ' Exit',
                'node_lat': float(start_poi['lat']), 'node_lng': float(start_poi['lng']),
                'distance_meters': 0
            }
        if not end_ent:
            end_ent = {
                'node_id': None, 'node_name': end_property + ' Entrance',
                'node_lat': float(end_poi['lat']), 'node_lng': float(end_poi['lng']),
                'distance_meters': 0
            }

        # ── Leg 1: Indoor departure ──
        if start_ent['node_id']:
            dep_waypoints, dep_dist = get_indoor_waypoints(
                start_poi_id, start_ent['node_id'], start_property, reverse=False
            )
        else:
            dep_waypoints = [
                {'lat': float(start_poi['lat']), 'lng': float(start_poi['lng']),
                 'name': start_poi['name'], 'node_type': 'poi'},
                {'lat': float(start_ent['node_lat']), 'lng': float(start_ent['node_lng']),
                 'name': start_ent['node_name'], 'node_type': 'entrance'}
            ]
            dep_dist = haversine(dep_waypoints[0]['lat'], dep_waypoints[0]['lng'],
                                 dep_waypoints[1]['lat'], dep_waypoints[1]['lng'])

        dep_steps = generate_turn_by_turn(dep_waypoints)

        legs.append({
            'leg_type': 'indoor_departure',
            'leg_number': 1,
            'label': f'Exit {start_property}',
            'transport': 'walk',
            'property': start_property,
            'distance_meters': round(dep_dist, 1),
            'estimated_time_seconds': int(dep_dist / WALK_SPEED_MPS),
            'steps': dep_steps,
            'waypoints': dep_waypoints
        })

        # ── Leg 2: Outdoor (walk or rideshare) ──
        outdoor_start = {
            'lat': float(start_ent['node_lat']),
            'lng': float(start_ent['node_lng'])
        }
        outdoor_end = {
            'lat': float(end_ent['node_lat']),
            'lng': float(end_ent['node_lng'])
        }
        outdoor_dist = haversine(outdoor_start['lat'], outdoor_start['lng'],
                                 outdoor_end['lat'], outdoor_end['lng'])

        if transport_mode == 'walk':
            # Try Google Directions for real walking route
            google_walk = google_directions.get_directions(
                origin=(outdoor_start['lat'], outdoor_start['lng']),
                destination=(outdoor_end['lat'], outdoor_end['lng']),
                mode='walking'
            )

            if google_walk:
                gw = google_walk['waypoints']
                if gw:
                    gw[0]['name'] = start_ent['node_name'] or start_property
                    gw[0]['node_type'] = 'entrance'
                    gw[-1]['name'] = end_ent['node_name'] or end_property
                    gw[-1]['node_type'] = 'entrance'

                legs.append({
                    'leg_type': 'outdoor_walk',
                    'leg_number': 2,
                    'label': f'Walk to {end_property}',
                    'transport': 'walk',
                    'distance_meters': google_walk['distance_meters'],
                    'estimated_time_seconds': google_walk['duration_seconds'],
                    'steps': google_walk['steps'],
                    'waypoints': gw,
                    'source': 'google_directions'
                })
            else:
                # Fallback: straight-line route
                outdoor_waypoints = [
                    {'lat': outdoor_start['lat'], 'lng': outdoor_start['lng'],
                     'name': start_ent['node_name'] or start_property, 'node_type': 'entrance'},
                    {'lat': outdoor_end['lat'], 'lng': outdoor_end['lng'],
                     'name': end_ent['node_name'] or end_property, 'node_type': 'entrance'}
                ]
                outdoor_steps = generate_turn_by_turn(outdoor_waypoints)

                legs.append({
                    'leg_type': 'outdoor_walk',
                    'leg_number': 2,
                    'label': f'Walk to {end_property}',
                    'transport': 'walk',
                    'distance_meters': round(outdoor_dist, 1),
                    'estimated_time_seconds': int(outdoor_dist / WALK_SPEED_MPS),
                    'steps': outdoor_steps,
                    'waypoints': outdoor_waypoints,
                    'source': 'straight_line'
                })
        else:
            # Rideshare leg — try Google Directions for driving route
            google_drive = google_directions.get_directions(
                origin=(outdoor_start['lat'], outdoor_start['lng']),
                destination=(outdoor_end['lat'], outdoor_end['lng']),
                mode='driving'
            )

            if google_drive:
                actual_distance = google_drive['distance_meters']
                actual_drive_seconds = google_drive['duration_seconds']
                ride_waypoints = google_drive['waypoints']
                if ride_waypoints:
                    ride_waypoints[0]['name'] = f'{start_property} Pickup'
                    ride_waypoints[0]['node_type'] = 'rideshare_pickup'
                    ride_waypoints[-1]['name'] = f'{end_property} Dropoff'
                    ride_waypoints[-1]['node_type'] = 'rideshare_dropoff'
                route_source = 'google_directions'
            else:
                actual_distance = outdoor_dist
                actual_drive_seconds = None
                ride_waypoints = [
                    {'lat': outdoor_start['lat'], 'lng': outdoor_start['lng'],
                     'name': f'{start_property} Pickup', 'node_type': 'rideshare_pickup'},
                    {'lat': outdoor_end['lat'], 'lng': outdoor_end['lng'],
                     'name': f'{end_property} Dropoff', 'node_type': 'rideshare_dropoff'}
                ]
                route_source = 'straight_line'

            fare_estimates = estimate_rideshare_fare(actual_distance)
            if actual_drive_seconds is not None:
                fare_estimates['estimated_drive_minutes'] = round(actual_drive_seconds / 60, 1)

            deep_links = generate_rideshare_links(
                outdoor_start['lat'], outdoor_start['lng'],
                outdoor_end['lat'], outdoor_end['lng'],
                end_property
            )
            ride_time = int(fare_estimates['estimated_drive_minutes'] * 60)

            legs.append({
                'leg_type': 'rideshare',
                'leg_number': 2,
                'label': f'Rideshare to {end_property}',
                'transport': 'rideshare',
                'distance_meters': round(actual_distance, 1),
                'estimated_time_seconds': ride_time,
                'fare_estimates': fare_estimates,
                'deep_links': deep_links,
                'pickup': {
                    'lat': outdoor_start['lat'],
                    'lng': outdoor_start['lng'],
                    'name': start_ent['node_name'] or f'{start_property} Rideshare Pickup'
                },
                'dropoff': {
                    'lat': outdoor_end['lat'],
                    'lng': outdoor_end['lng'],
                    'name': end_ent['node_name'] or f'{end_property} Rideshare Dropoff'
                },
                'steps': [
                    {'instruction': f"Head to the rideshare pickup area at {start_property}",
                     'distance_meters': 0, 'time_seconds': 0,
                     'from': outdoor_start, 'to': outdoor_start},
                    {'instruction': f"Request your ride via Uber or Lyft",
                     'distance_meters': 0, 'time_seconds': fare_estimates['uber']['eta_minutes'] * 60,
                     'from': outdoor_start, 'to': outdoor_start},
                    {'instruction': f"Ride to {end_property} ({fare_estimates['distance_miles']} mi)",
                     'distance_meters': round(actual_distance, 1), 'time_seconds': ride_time,
                     'from': outdoor_start, 'to': outdoor_end},
                ],
                'waypoints': ride_waypoints,
                'source': route_source
            })

        # ── Leg 3: Indoor arrival ──
        if end_ent['node_id']:
            arr_waypoints, arr_dist = get_indoor_waypoints(
                end_poi_id, end_ent['node_id'], end_property, reverse=True
            )
        else:
            arr_waypoints = [
                {'lat': float(end_ent['node_lat']), 'lng': float(end_ent['node_lng']),
                 'name': end_ent['node_name'], 'node_type': 'entrance'},
                {'lat': float(end_poi['lat']), 'lng': float(end_poi['lng']),
                 'name': end_poi['name'], 'node_type': 'poi'}
            ]
            arr_dist = haversine(arr_waypoints[0]['lat'], arr_waypoints[0]['lng'],
                                 arr_waypoints[1]['lat'], arr_waypoints[1]['lng'])

        arr_steps = generate_turn_by_turn(arr_waypoints)

        legs.append({
            'leg_type': 'indoor_arrival',
            'leg_number': 3,
            'label': f'Enter {end_property} to {end_poi["name"]}',
            'transport': 'walk',
            'property': end_property,
            'distance_meters': round(arr_dist, 1),
            'estimated_time_seconds': int(arr_dist / WALK_SPEED_MPS),
            'steps': arr_steps,
            'waypoints': arr_waypoints
        })

    # ── Build response ──
    total_distance = sum(leg['distance_meters'] for leg in legs)
    total_time = sum(leg['estimated_time_seconds'] for leg in legs)

    has_rideshare = any(leg['leg_type'] == 'rideshare' for leg in legs)
    mode = 'rideshare' if has_rideshare else 'walk'

    return jsonify({
        'start': {
            'id': start_poi['id'], 'name': start_poi['name'],
            'property': start_property,
            'lat': float(start_poi['lat']), 'lng': float(start_poi['lng'])
        },
        'end': {
            'id': end_poi['id'], 'name': end_poi['name'],
            'property': end_property,
            'lat': float(end_poi['lat']), 'lng': float(end_poi['lng'])
        },
        'mode': mode,
        'total_distance_meters': round(total_distance, 1),
        'total_time_seconds': total_time,
        'leg_count': len(legs),
        'legs': legs
    })


@app.route('/api/property-distances')
def api_property_distances():
    sql = """
        SELECT from_property_name, to_property_name,
               ROUND(distance_meters::numeric) AS distance_meters,
               CASE WHEN distance_meters <= %s THEN 'walk' ELSE 'rideshare' END AS mode
        FROM property_distances
        ORDER BY distance_meters
    """
    return jsonify(query(sql, (WALK_THRESHOLD_METERS,)))


if __name__ == '__main__':
    init_pool()
    print("\n  Sin City Travels Demo")
    print("  http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
