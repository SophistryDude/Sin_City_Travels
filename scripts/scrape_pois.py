#!/usr/bin/env python3
"""
Sin City Travels - POI Scraper
Scrapes SmarterVegas.com for Points of Interest data across all Las Vegas Strip properties.
Generates JSON files in the established POI format.

Usage:
    python scrape_pois.py --category restaurants
    python scrape_pois.py --category shows
    python scrape_pois.py --category nightlife
    python scrape_pois.py --category attractions
    python scrape_pois.py --category all
    python scrape_pois.py --category all --details   (scrapes individual pages - slower)
"""

import json
import os
import re
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Rate limiting
REQUEST_DELAY = 1.5  # seconds between requests

BASE_URL = "https://www.smartervegas.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# All properties with coordinates, addresses, and Strip areas
PROPERTIES = {
    "Aria": {
        "lat": 36.1067, "lng": -115.1761,
        "address": "3730 Las Vegas Blvd S, Las Vegas, NV 89158",
        "area": "Mid Strip"
    },
    "Bellagio": {
        "lat": 36.1127, "lng": -115.1765,
        "address": "3600 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "Caesars Palace": {
        "lat": 36.1162, "lng": -115.1744,
        "address": "3570 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "Casino Royale": {
        "lat": 36.1200, "lng": -115.1721,
        "address": "3411 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "Circus Circus": {
        "lat": 36.1367, "lng": -115.1631,
        "address": "2880 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "North Strip"
    },
    "Cosmopolitan": {
        "lat": 36.1095, "lng": -115.1742,
        "address": "3708 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "Encore": {
        "lat": 36.1289, "lng": -115.1650,
        "address": "3121 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "North Strip"
    },
    "Excalibur": {
        "lat": 36.0987, "lng": -115.1754,
        "address": "3850 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "South Strip"
    },
    "Fashion Show Mall": {
        "lat": 36.1268, "lng": -115.1700,
        "address": "3200 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "North Strip"
    },
    "Flamingo": {
        "lat": 36.1162, "lng": -115.1714,
        "address": "3555 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "Fontainebleau": {
        "lat": 36.1361, "lng": -115.1568,
        "address": "2777 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "North Strip"
    },
    "Four Seasons": {
        "lat": 36.0909, "lng": -115.1753,
        "address": "3960 Las Vegas Blvd S, Las Vegas, NV 89119",
        "area": "South Strip"
    },
    "Hard Rock": {
        "lat": 36.1246, "lng": -115.1679,
        "address": "3580 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "Harrah's": {
        "lat": 36.1190, "lng": -115.1726,
        "address": "3475 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "Horseshoe": {
        "lat": 36.1190, "lng": -115.1726,
        "address": "3475 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "Luxor": {
        "lat": 36.0955, "lng": -115.1761,
        "address": "3900 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "South Strip"
    },
    "Mandalay Bay": {
        "lat": 36.0909, "lng": -115.1743,
        "address": "3950 Las Vegas Blvd S, Las Vegas, NV 89119",
        "area": "South Strip"
    },
    "MGM Grand": {
        "lat": 36.1024, "lng": -115.1698,
        "address": "3799 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "South Strip"
    },
    "New York New York": {
        "lat": 36.1022, "lng": -115.1745,
        "address": "3790 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "South Strip"
    },
    "NoMad": {
        "lat": 36.1028, "lng": -115.1709,
        "address": "3772 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "South Strip"
    },
    "Palazzo": {
        "lat": 36.1228, "lng": -115.1693,
        "address": "3325 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "North Strip"
    },
    "Paris": {
        "lat": 36.1125, "lng": -115.1707,
        "address": "3655 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "Park MGM": {
        "lat": 36.1028, "lng": -115.1709,
        "address": "3770 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "South Strip"
    },
    "Planet Hollywood": {
        "lat": 36.1097, "lng": -115.1708,
        "address": "3663 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "Resorts World": {
        "lat": 36.1380, "lng": -115.1652,
        "address": "3000 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "North Strip"
    },
    "Sahara": {
        "lat": 36.1413, "lng": -115.1567,
        "address": "2535 Las Vegas Blvd S, Las Vegas, NV 89104",
        "area": "North Strip"
    },
    "The Cromwell": {
        "lat": 36.1168, "lng": -115.1722,
        "address": "3595 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "The LINQ": {
        "lat": 36.1176, "lng": -115.1710,
        "address": "3535 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "The Palazzo": {
        "lat": 36.1228, "lng": -115.1693,
        "address": "3325 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "North Strip"
    },
    "The Signature": {
        "lat": 36.1024, "lng": -115.1665,
        "address": "145 E Harmon Ave, Las Vegas, NV 89109",
        "area": "South Strip"
    },
    "The STRAT": {
        "lat": 36.1474, "lng": -115.1557,
        "address": "2000 Las Vegas Blvd S, Las Vegas, NV 89104",
        "area": "North Strip"
    },
    "The Strip": {
        "lat": 36.1147, "lng": -115.1728,
        "address": "Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "Mid Strip"
    },
    "The Venetian": {
        "lat": 36.1212, "lng": -115.1697,
        "address": "3355 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "North Strip"
    },
    "Treasure Island": {
        "lat": 36.1247, "lng": -115.1709,
        "address": "3300 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "North Strip"
    },
    "Tropicana": {
        "lat": 36.1012, "lng": -115.1730,
        "address": "3801 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "South Strip"
    },
    "Trump": {
        "lat": 36.1270, "lng": -115.1686,
        "address": "2000 Fashion Show Dr, Las Vegas, NV 89109",
        "area": "North Strip"
    },
    "Vdara": {
        "lat": 36.1080, "lng": -115.1773,
        "address": "2600 W Harmon Ave, Las Vegas, NV 89158",
        "area": "Mid Strip"
    },
    "W Las Vegas": {
        "lat": 36.1024, "lng": -115.1665,
        "address": "3950 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "South Strip"
    },
    "Waldorf Astoria": {
        "lat": 36.1070, "lng": -115.1755,
        "address": "3752 Las Vegas Blvd S, Las Vegas, NV 89158",
        "area": "Mid Strip"
    },
    "Wynn": {
        "lat": 36.1264, "lng": -115.1660,
        "address": "3131 Las Vegas Blvd S, Las Vegas, NV 89109",
        "area": "North Strip"
    },
}

# Fast food / chain restaurants to exclude
CHAINS_TO_SKIP = {
    "starbucks", "subway", "mcdonald's", "burger king", "pizza hut",
    "pizza hut express", "dunkin donuts", "dunkin'", "popeyes",
    "panda express", "dairy queen", "krispy kreme", "cinnabon",
    "auntie anne's", "einstein bros bagels", "einstein bros",
    "sbarro", "johnny rockets", "del taco", "baja fresh",
    "jimmy john's", "chipotle", "nathan's famous", "nathan's famous hotdogs",
    "white castle", "pressed juicery", "wok to walk", "ben & jerry's",
}

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "pois"


def fetch_page(url, delay=REQUEST_DELAY):
    """Fetch a page with rate limiting and error handling."""
    time.sleep(delay)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as e:
        print(f"  [ERROR] Failed to fetch {url}: {e}")
        return None


def make_filename(name, property_name):
    """Generate a snake_case filename from a POI name and property."""
    slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
    prop_slug = re.sub(r'[^a-z0-9]+', '_', property_name.lower()).strip('_')
    return f"{slug}_{prop_slug}"


def get_next_poi_id():
    """Scan all existing POI files to find the next available ID number."""
    max_id = 49  # Current max from existing POIs
    for root, dirs, files in os.walk(DATA_DIR):
        for f in files:
            if f.endswith('.json'):
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                        if 'id' in data:
                            num = int(data['id'].replace('poi_', ''))
                            max_id = max(max_id, num)
                except (json.JSONDecodeError, ValueError, KeyError):
                    pass
    return max_id + 1


def create_poi_json(poi_id, name, category, subcategory, property_name,
                    description="", features=None, tags=None,
                    price_range=None, cuisine=None, cuisine_raw=None,
                    hours=None, phone=None, website=None, extra_fields=None):
    """Create a POI JSON object in the established format."""
    prop = PROPERTIES.get(property_name, {})
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    poi = {
        "id": f"poi_{poi_id:03d}",
        "name": name,
        "category": category,
        "subcategory": subcategory,
        "casino_property": property_name,
        "location": {
            "address": prop.get("address", "Las Vegas, NV"),
            "casino": property_name,
            "coordinates": {
                "lat": prop.get("lat", 36.1147),
                "lng": prop.get("lng", -115.1728)
            },
            "level": "ground",
            "area": prop.get("area", "Las Vegas Strip")
        },
        "contact": {},
        "description": description,
        "features": features or [],
        "tags": tags or [],
        "data_sources": ["smartervegas", "web_search_2026-02"],
        "created_at": now,
        "updated_at": now
    }

    if phone:
        poi["contact"]["phone"] = phone
    if website:
        poi["contact"]["website"] = website

    # Category-specific fields
    if category == "restaurant":
        poi["cuisine"] = cuisine or []
        if cuisine_raw:
            poi["cuisine_raw"] = cuisine_raw
        if price_range:
            poi["pricing"] = {"price_range": price_range}
        if hours:
            poi["hours"] = hours
    elif category in ("entertainment", "nightlife", "attraction"):
        if price_range:
            poi["pricing"] = {"price_range": price_range}
        if hours:
            poi["hours"] = hours

    if extra_fields:
        poi.update(extra_fields)

    return poi


# ======================================================================
# RESTAURANT SCRAPING
# ======================================================================

def scrape_dining_page():
    """Scrape the SmarterVegas dining page for all restaurants by property.

    The page uses div.category-name-seperator as property headers,
    followed by restaurant card divs with links to /dining/restaurant/*.aspx
    """
    print("\n=== Scraping SmarterVegas Dining Page ===")
    url = f"{BASE_URL}/dining.aspx"
    soup = fetch_page(url)
    if not soup:
        return {}

    restaurants_by_property = {}

    # Property sections are delineated by div.category-name-seperator
    separators = soup.find_all('div', class_='category-name-seperator')
    print(f"  Found {len(separators)} property sections")

    for sep in separators:
        prop_name = sep.get_text(strip=True)
        restaurants_by_property[prop_name] = []

        # Walk siblings until the next separator
        sibling = sep.find_next_sibling()
        while sibling:
            if (hasattr(sibling, 'get') and sibling.get('class')
                    and 'category-name-seperator' in sibling.get('class', [])):
                break

            # Find restaurant links within this element
            rest_links = sibling.find_all('a', href=lambda h: h and '/dining/restaurant/' in h)
            for link in rest_links:
                name = link.get_text(strip=True)
                href = link.get('href', '')
                # Skip empty names and action labels
                if name and name not in ('', 'More Info', 'Deals', 'Website'):
                    # Extract cuisine from the card
                    cuisine_raw = ''
                    parent_div = link.find_parent('div', class_=lambda c: c and 'col-xs-24' in str(c))
                    if parent_div:
                        cuisine_text = parent_div.find(string=lambda s: s and 'Cuisine:' in str(s))
                        if cuisine_text:
                            cuisine_raw = str(cuisine_text).replace('Cuisine:', '').strip()

                    restaurants_by_property[prop_name].append({
                        'name': name,
                        'url': BASE_URL + href if href.startswith('/') else href,
                        'cuisine_raw': cuisine_raw,
                    })

            sibling = sibling.find_next_sibling()

    # Deduplicate by URL within each property
    for prop in restaurants_by_property:
        seen = set()
        unique = []
        for r in restaurants_by_property[prop]:
            if r['url'] not in seen:
                seen.add(r['url'])
                unique.append(r)
        restaurants_by_property[prop] = unique

    total = sum(len(v) for v in restaurants_by_property.values())
    print(f"  Total: {total} unique restaurants across {len(restaurants_by_property)} properties\n")
    for prop, rests in sorted(restaurants_by_property.items()):
        print(f"    {prop}: {len(rests)} restaurants")

    return restaurants_by_property


def scrape_restaurant_detail(url):
    """Scrape an individual restaurant page for more details."""
    soup = fetch_page(url)
    if not soup:
        return {}

    details = {}
    text = soup.get_text(' ', strip=True)

    # Meta description often has a good summary
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta:
        details['description'] = meta.get('content', '')[:500]

    # Look for phone numbers
    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_match:
        details['phone'] = phone_match.group(0)

    # Look for price indicators
    price_match = re.search(r'(\${2,5}\+?)', text)
    if price_match:
        details['price_range'] = price_match.group(1)

    # Look for hours patterns
    hours_match = re.search(
        r'(?:hours|open)\s*:?\s*((?:mon|tue|wed|thu|fri|sat|sun|daily)[\s\S]{5,200})',
        text, re.I
    )
    if hours_match:
        details['hours_raw'] = hours_match.group(1)[:200]

    return details


def generate_restaurant_pois(restaurants_by_property, scrape_details=False):
    """Generate POI JSON files for restaurants."""
    output_dir = str(DATA_DIR / "restaurants")
    os.makedirs(output_dir, exist_ok=True)
    poi_id = get_next_poi_id()
    created = 0
    skipped_chains = 0
    skipped_existing = 0

    for property_name, restaurants in sorted(restaurants_by_property.items()):
        print(f"\n  {property_name} ({len(restaurants)} restaurants)...")

        for rest in restaurants:
            name = rest['name']

            # Skip chain restaurants
            if name.lower().strip() in CHAINS_TO_SKIP:
                skipped_chains += 1
                continue

            filename = make_filename(name, property_name)
            filepath = os.path.join(output_dir, f"{filename}.json")

            if os.path.exists(filepath):
                skipped_existing += 1
                continue

            # Optionally get more details from individual page
            details = {}
            if scrape_details and rest.get('url'):
                details = scrape_restaurant_detail(rest['url'])

            cuisine_raw = rest.get('cuisine_raw', '')
            cuisine_list = parse_cuisine(cuisine_raw)
            subcategory = infer_restaurant_subcategory(name, cuisine_raw)
            description = details.get('description', '')
            price_range = details.get('price_range') or infer_price_range(name, cuisine_raw)
            phone = details.get('phone')

            poi = create_poi_json(
                poi_id=poi_id,
                name=name,
                category="restaurant",
                subcategory=subcategory,
                property_name=property_name,
                description=description,
                features=infer_restaurant_features(name, cuisine_raw),
                tags=infer_restaurant_tags(name, property_name, cuisine_raw),
                price_range=price_range,
                cuisine=cuisine_list,
                cuisine_raw=cuisine_raw,
                phone=phone,
                website=rest.get('url', ''),
            )

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(poi, f, indent=2, ensure_ascii=False)

            print(f"    [NEW] poi_{poi_id:03d} - {name} ({cuisine_raw or 'unknown'})")
            poi_id += 1
            created += 1

    print(f"\n  === Restaurant Summary ===")
    print(f"  Created: {created}")
    print(f"  Skipped chains: {skipped_chains}")
    print(f"  Skipped existing: {skipped_existing}")
    return created


# ======================================================================
# SHOW / ENTERTAINMENT SCRAPING
# ======================================================================

def scrape_shows_page():
    """Scrape shows/entertainment from SmarterVegas."""
    print("\n=== Scraping SmarterVegas Shows Page ===")
    url = f"{BASE_URL}/shows"
    soup = fetch_page(url)
    if not soup:
        return []

    shows = []
    all_links = soup.find_all('a', href=lambda h: h and '/shows/' in h)

    seen_urls = set()
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)

        if (text and text not in ('', 'More Info', 'Deals', 'Buy Tickets', 'Website')
                and not href.endswith('/shows') and not href.endswith('/shows/')
                and '/shows/' in href):
            full_url = BASE_URL + href if href.startswith('/') else href
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                shows.append({'name': text, 'url': full_url})

    print(f"  Found {len(shows)} shows")
    return shows


def scrape_show_detail(url):
    """Scrape an individual show page for details."""
    soup = fetch_page(url)
    if not soup:
        return {}

    details = {}
    text = soup.get_text(' ', strip=True)

    # Property from text
    for prop_name in PROPERTIES:
        if prop_name.lower() in text.lower():
            details['property'] = prop_name
            break

    # Meta description
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta:
        details['description'] = meta.get('content', '')[:500]

    # Price
    price_match = re.search(r'from\s*\$(\d+)', text, re.I)
    if price_match:
        details['price_from'] = int(price_match.group(1))

    return details


def generate_show_pois(shows, scrape_details=False):
    """Generate POI JSON files for shows."""
    output_dir = str(DATA_DIR / "shows")
    os.makedirs(output_dir, exist_ok=True)
    poi_id = get_next_poi_id()
    created = 0

    print(f"\n  Processing {len(shows)} shows...")

    for show in shows:
        name = show['name']

        details = {}
        if scrape_details and show.get('url'):
            details = scrape_show_detail(show['url'])

        property_name = details.get('property') or infer_show_property(name)
        description = details.get('description', '')
        subcategory = infer_show_subcategory(name)

        filename = make_filename(name, property_name or 'las_vegas')
        filepath = os.path.join(output_dir, f"{filename}.json")

        if os.path.exists(filepath):
            continue

        price_from = details.get('price_from')
        price_range = "$$$$" if price_from and price_from > 80 else "$$$" if price_from and price_from > 40 else "$$"

        poi = create_poi_json(
            poi_id=poi_id,
            name=name,
            category="entertainment",
            subcategory=subcategory,
            property_name=property_name if property_name in PROPERTIES else None,
            description=description,
            features=["show", "entertainment", "live_performance"],
            tags=[subcategory.replace('_', ' '), "show", "las_vegas_entertainment"],
            price_range=price_range,
            website=show.get('url', ''),
        )

        if not poi['casino_property']:
            poi['casino_property'] = "Las Vegas Strip"
            poi['location']['area'] = 'Las Vegas Strip'

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(poi, f, indent=2, ensure_ascii=False)

        print(f"    [NEW] poi_{poi_id:03d} - {name} ({property_name or 'TBD'})")
        poi_id += 1
        created += 1

    print(f"\n  Created {created} show POIs")
    return created


# ======================================================================
# NIGHTLIFE SCRAPING (nightclubs, dayclubs/pools, bars)
# ======================================================================

def scrape_nightlife_page():
    """Scrape nightclubs, dayclubs/pools, and bars from SmarterVegas."""
    print("\n=== Scraping SmarterVegas Nightlife Page ===")
    url = f"{BASE_URL}/nightlife"
    soup = fetch_page(url)
    if not soup:
        return {"nightclubs": [], "dayclubs": [], "bars": []}

    venues = {"nightclubs": [], "dayclubs": [], "bars": []}

    all_links = soup.find_all('a', href=True)
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)

        if not text or text in ('', 'More Info', 'Deals', 'Website'):
            continue

        full_url = BASE_URL + href if href.startswith('/') else href

        if '/nightlife/nightclubs/' in href:
            venues['nightclubs'].append({"name": text, "url": full_url})
        elif '/nightlife/pool-clubs/' in href:
            venues['dayclubs'].append({"name": text, "url": full_url})
        elif '/nightlife/bars/' in href:
            venues['bars'].append({"name": text, "url": full_url})

    # Deduplicate
    for cat in venues:
        seen = set()
        unique = []
        for v in venues[cat]:
            if v['url'] not in seen:
                seen.add(v['url'])
                unique.append(v)
        venues[cat] = unique

    print(f"  Nightclubs: {len(venues['nightclubs'])}")
    print(f"  Dayclubs/Pools: {len(venues['dayclubs'])}")
    print(f"  Bars/Lounges: {len(venues['bars'])}")
    return venues


def scrape_nightlife_detail(url):
    """Scrape an individual nightlife venue page for details."""
    soup = fetch_page(url)
    if not soup:
        return {}

    details = {}
    text = soup.get_text(' ', strip=True)

    for prop_name in PROPERTIES:
        if prop_name.lower() in text.lower():
            details['property'] = prop_name
            break

    meta = soup.find('meta', attrs={'name': 'description'})
    if meta:
        details['description'] = meta.get('content', '')[:500]

    return details


def generate_nightlife_pois(venues, scrape_details=False):
    """Generate POI JSON files for nightlife venues."""
    poi_id = get_next_poi_id()
    created = 0

    type_config = {
        'nightclubs': {
            'subdir': 'nightclubs',
            'subcategory': 'nightclub',
            'features': ['nightclub', 'dancing', 'dj', 'nightlife'],
        },
        'dayclubs': {
            'subdir': 'dayclubs',
            'subcategory': 'dayclub_pool',
            'features': ['dayclub', 'pool_party', 'outdoor', 'daytime'],
        },
        'bars': {
            'subdir': 'bars',
            'subcategory': 'bar_lounge',
            'features': ['bar', 'lounge', 'cocktails'],
        },
    }

    for venue_type, venue_list in venues.items():
        config = type_config[venue_type]
        output_dir = str(DATA_DIR / "nightlife" / config['subdir'])
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n  Processing {venue_type} ({len(venue_list)} venues)...")

        for venue in venue_list:
            name = venue['name']

            details = {}
            if scrape_details and venue.get('url'):
                details = scrape_nightlife_detail(venue['url'])

            property_name = details.get('property') or infer_nightlife_property(name)
            description = details.get('description', '')

            filename = make_filename(name, property_name or 'las_vegas')
            filepath = os.path.join(output_dir, f"{filename}.json")

            if os.path.exists(filepath):
                continue

            poi = create_poi_json(
                poi_id=poi_id,
                name=name,
                category="nightlife",
                subcategory=config['subcategory'],
                property_name=property_name if property_name in PROPERTIES else None,
                description=description,
                features=config['features'],
                tags=[config['subcategory'].replace('_', ' '), "nightlife", "las_vegas"],
                price_range="$$$",
                website=venue.get('url', ''),
            )

            if not poi['casino_property']:
                poi['casino_property'] = "Las Vegas Strip"
                poi['location']['area'] = 'Las Vegas Strip'

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(poi, f, indent=2, ensure_ascii=False)

            print(f"    [NEW] poi_{poi_id:03d} - {name} ({property_name or 'TBD'})")
            poi_id += 1
            created += 1

    print(f"\n  Created {created} nightlife POIs total")
    return created


# ======================================================================
# ATTRACTIONS SCRAPING
# ======================================================================

def scrape_attractions_page():
    """Scrape attractions from SmarterVegas."""
    print("\n=== Scraping SmarterVegas Attractions Page ===")
    url = f"{BASE_URL}/attractions"
    soup = fetch_page(url)
    if not soup:
        return []

    attractions = []
    seen_urls = set()
    all_links = soup.find_all('a', href=lambda h: h and '/attractions/' in h)

    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)

        if (text and text not in ('', 'More Info', 'Deals', 'Website', 'Buy Tickets')
                and href != '/attractions'
                and not href.endswith('/attractions/')):
            full_url = BASE_URL + href if href.startswith('/') else href
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                attractions.append({'name': text, 'url': full_url})

    print(f"  Found {len(attractions)} attractions")
    return attractions


def scrape_attraction_detail(url):
    """Scrape an individual attraction page."""
    soup = fetch_page(url)
    if not soup:
        return {}

    details = {}
    text = soup.get_text(' ', strip=True)

    for prop_name in PROPERTIES:
        if prop_name.lower() in text.lower():
            details['property'] = prop_name
            break

    meta = soup.find('meta', attrs={'name': 'description'})
    if meta:
        details['description'] = meta.get('content', '')[:500]

    price_match = re.search(r'(?:from|starting at|tickets?)\s*\$(\d+)', text, re.I)
    if price_match:
        details['price_from'] = int(price_match.group(1))

    return details


def generate_attraction_pois(attractions, scrape_details=False):
    """Generate POI JSON files for attractions."""
    output_dir = str(DATA_DIR / "attractions")
    os.makedirs(output_dir, exist_ok=True)
    poi_id = get_next_poi_id()
    created = 0

    print(f"\n  Processing {len(attractions)} attractions...")

    for attr in attractions:
        name = attr['name']

        details = {}
        if scrape_details and attr.get('url'):
            details = scrape_attraction_detail(attr['url'])

        property_name = details.get('property') or infer_attraction_property(name)
        description = details.get('description', '')
        subcategory = infer_attraction_subcategory(name)

        filename = make_filename(name, property_name or 'las_vegas')
        filepath = os.path.join(output_dir, f"{filename}.json")

        if os.path.exists(filepath):
            continue

        price_from = details.get('price_from')
        price_range = "$$$" if price_from and price_from > 30 else "$$"

        poi = create_poi_json(
            poi_id=poi_id,
            name=name,
            category="attraction",
            subcategory=subcategory,
            property_name=property_name if property_name in PROPERTIES else None,
            description=description,
            features=["attraction", "experience"],
            tags=[subcategory.replace('_', ' '), "attraction", "las_vegas"],
            price_range=price_range,
            website=attr.get('url', ''),
        )

        if not poi['casino_property']:
            poi['casino_property'] = "Off-Strip"
            poi['location']['area'] = 'Las Vegas'

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(poi, f, indent=2, ensure_ascii=False)

        print(f"    [NEW] poi_{poi_id:03d} - {name} ({property_name or 'Las Vegas'})")
        poi_id += 1
        created += 1

    print(f"\n  Created {created} attraction POIs")
    return created


# ======================================================================
# INFERENCE HELPERS
# ======================================================================

def parse_cuisine(cuisine_raw):
    """Parse the SmarterVegas cuisine string into a list."""
    if not cuisine_raw:
        return ["american"]
    cuisines = [c.strip().lower().replace(' ', '_') for c in cuisine_raw.split(',')]
    return [c for c in cuisines if c]


def infer_restaurant_subcategory(name, cuisine_raw=''):
    """Infer subcategory from name and cuisine info."""
    combined = (name + ' ' + cuisine_raw).lower()
    if 'buffet' in combined:
        return 'buffet'
    if any(w in combined for w in ['steakhouse', 'steak house']):
        return 'steakhouse'
    if 'sushi' in combined and any(w in combined for w in ['fine', 'omakase']):
        return 'fine_dining_japanese'
    if any(w in combined for w in ['quickbites', 'quick bites', 'fast']):
        return 'quick_bites'
    if any(w in combined for w in ['cafe', 'coffee', 'bakery', 'patisserie', 'deli']):
        return 'cafe_bakery'
    if any(w in combined for w in ['pizza', 'pizzeria']):
        return 'pizza'
    if 'seafood' in combined:
        return 'seafood'
    if any(w in combined for w in ['french', 'brasserie', 'bistro']):
        return 'french'
    if any(w in combined for w in ['italian', 'trattoria', 'osteria']):
        return 'italian'
    if any(w in combined for w in ['japanese', 'sushi', 'ramen']):
        return 'japanese'
    if any(w in combined for w in ['chinese', 'dim sum', 'noodle']):
        return 'chinese'
    if any(w in combined for w in ['mexican', 'taco', 'cantina']):
        return 'mexican'
    if any(w in combined for w in ['korean', 'kbbq']):
        return 'korean'
    if any(w in combined for w in ['thai']):
        return 'thai'
    if any(w in combined for w in ['indian', 'curry']):
        return 'indian'
    if any(w in combined for w in ['spanish', 'tapas']):
        return 'spanish'
    if any(w in combined for w in ['asian']):
        return 'asian'
    if any(w in combined for w in ['bar ', 'pub ', 'sports', 'tavern']):
        return 'bar_restaurant'
    if any(w in combined for w in ['burger', 'grill', 'bbq', 'american']):
        return 'american'
    return 'restaurant'


def infer_price_range(name, cuisine_raw=''):
    """Guess price range from name and cuisine."""
    combined = (name + ' ' + cuisine_raw).lower()
    if any(w in combined for w in ['quickbites', 'fast', 'express', 'deli']):
        return '$'
    if any(w in combined for w in ['buffet', 'cafe', 'pizza', 'burger', 'bar ']):
        return '$$'
    if any(w in combined for w in ['steakhouse', 'seafood', 'french', 'japanese']):
        return '$$$$'
    return '$$'


def infer_restaurant_features(name, cuisine_raw=''):
    """Generate feature tags for a restaurant."""
    features = ["dining"]
    combined = (name + ' ' + cuisine_raw).lower()
    if 'quickbites' in combined:
        features.append("quick_service")
    if any(w in combined for w in ['steak', 'seafood', 'french', 'italian']):
        features.append("sit_down_dining")
    if 'buffet' in combined:
        features.append("buffet")
        features.append("all_you_can_eat")
    if 'sushi' in combined:
        features.append("sushi_bar")
    return features


def infer_restaurant_tags(name, property_name, cuisine_raw=''):
    """Generate tags for a restaurant."""
    tags = [property_name.lower().replace(' ', '_')]
    cuisines = parse_cuisine(cuisine_raw)
    tags.extend(cuisines[:3])
    return tags


def infer_show_property(name):
    """Map show names to their known properties."""
    known = {
        "O by Cirque": "Bellagio", '"O"': "Bellagio",
        "KA": "MGM Grand", "KÀ": "MGM Grand",
        "Mystere": "Treasure Island", "Mystère": "Treasure Island",
        "Beatles LOVE": "Mandalay Bay", "LOVE": "Mandalay Bay",
        "Blue Man Group": "Luxor",
        "Absinthe": "Caesars Palace",
        "David Copperfield": "MGM Grand",
        "Michael Jackson ONE": "Mandalay Bay", "MJ ONE": "Mandalay Bay",
        "Mac King": "Excalibur",
        "Mat Franco": "The LINQ",
        "Shin Lim": "The LINQ",
        "Terry Fator": "New York New York",
        "Thunder From Down Under": "Excalibur",
        "Tournament of Kings": "Excalibur",
        "Mad Apple": "New York New York",
        "Carrot Top": "Luxor",
        "Fantasy": "Luxor",
        "Zombie Burlesque": "Planet Hollywood",
        "V - The Ultimate Variety": "Planet Hollywood",
        "Piff the Magic Dragon": "Flamingo",
        "RuPaul's Drag Race": "Flamingo",
        "Donny Osmond": "Harrah's",
        "Tape Face": "Harrah's",
        "Xavier Mortimer": "The STRAT",
        "Banachek": "The STRAT",
    }
    for key, prop in known.items():
        if key.lower() in name.lower():
            return prop
    return None


def infer_show_subcategory(name):
    """Infer show subcategory from name."""
    name_lower = name.lower()
    if 'cirque' in name_lower:
        return 'cirque_du_soleil'
    if any(w in name_lower for w in ['comedy', 'comic', 'funny', 'laugh']):
        return 'comedy'
    if any(w in name_lower for w in ['magic', 'magician', 'copperfield', 'franco', 'shin lim', 'piff']):
        return 'magic'
    if any(w in name_lower for w in ['burlesque', 'adult', 'fantasy', 'thunder from down under', 'chippendales']):
        return 'adult_show'
    if any(w in name_lower for w in ['tribute', 'impersonator']):
        return 'tribute_show'
    if any(w in name_lower for w in ['concert', 'residency']):
        return 'concert_residency'
    if any(w in name_lower for w in ['acrobat', 'cirque', 'variety']):
        return 'variety_show'
    return 'show'


def infer_nightlife_property(name):
    """Map nightlife venue names to properties."""
    known = {
        "XS Nightclub": "Encore", "XS": "Encore",
        "Encore Beach Club": "Encore", "EBC": "Encore",
        "Hakkasan": "MGM Grand",
        "JEWEL": "Aria", "Jewel": "Aria",
        "Marquee Nightclub": "Cosmopolitan", "Marquee Dayclub": "Cosmopolitan",
        "OMNIA": "Caesars Palace",
        "On The Record": "Park MGM",
        "LIV Nightclub": "Fontainebleau", "LIV Beach": "Fontainebleau",
        "Liquid": "Aria",
        "Venus Pool": "Caesars Palace",
        "Go Pool": "Flamingo",
        "Daylight": "Mandalay Bay", "Moorea": "Mandalay Bay",
        "Foundation Room": "Mandalay Bay",
        "Vanderpump": "Paris",
        "Chandelier": "Cosmopolitan",
        "Lily Bar": "Bellagio",
        "Hyde": "Bellagio",
        "Skyfall": "Mandalay Bay",
        "Drai's": "The Cromwell",
    }
    for key, prop in known.items():
        if key.lower() in name.lower():
            return prop
    return None


def infer_attraction_property(name):
    """Map attraction names to properties."""
    known = {
        "Adventuredome": "Circus Circus", "Indoor Circus": "Circus Circus",
        "The Midway": "Circus Circus", "Slots-A-Fun": "Circus Circus",
        "Conservatory": "Bellagio", "Fountains": "Bellagio",
        "Gallery of Fine Art": "Bellagio",
        "High Roller": "The LINQ", "Fly LINQ": "The LINQ",
        "DreamBox": "The LINQ", "VR Adventures": "The LINQ",
        "Eiffel Tower": "Paris",
        "Gondola": "The Venetian", "Madame Tussauds": "The Venetian",
        "PanIQ": "The Venetian",
        "Shark Reef": "Mandalay Bay", "Swingers": "Mandalay Bay",
        "Bob Marley": "Mandalay Bay",
        "SkyJump": "The STRAT", "Big Shot": "The STRAT",
        "X Scream": "The STRAT", "STRAT Tower": "The STRAT",
        "Atomic Golf": "The STRAT",
        "Lake of Dreams": "Wynn", "Wynn Golf": "Wynn",
        "Hershey": "New York New York", "Roller Coaster": "New York New York",
        "BODIES": "Luxor", "King Tut": "Luxor", "Titanic": "Luxor",
        "HyperX": "Luxor", "Play Playground": "Luxor",
        "Fun Dungeon": "Excalibur", "Max Flight": "Excalibur",
        "Ultimate 4-D": "Excalibur",
        "Electric Playhouse": "Caesars Palace", "F1 Arcade": "Caesars Palace",
        "Escape Game": "Caesars Palace", "Atlantis Show": "Caesars Palace",
        "Arte Museum": "Cosmopolitan", "Museum of Illusions": "Cosmopolitan",
        "Arcade at Horseshoe": "Horseshoe", "BattleBots": "Horseshoe",
        "Real Bodies": "Horseshoe", "Twilight Zone": "Horseshoe",
        "Friends Experience": "MGM Grand", "Topgolf": "MGM Grand",
        "Virtual Reality": "MGM Grand",
        "Haus of Gaga": "Park MGM",
        "Wildlife Habitat": "Flamingo",
        "Princess Diana": "Aria", "Van Gogh": "Aria",
        "The Cove": "Treasure Island",
        "Hall of Excellence": "Fontainebleau",
    }
    for key, prop in known.items():
        if key.lower() in name.lower():
            return prop
    return None


def infer_attraction_subcategory(name):
    """Infer attraction subcategory."""
    name_lower = name.lower()
    if any(w in name_lower for w in ['museum', 'exhibit', 'exhibition', 'gallery', 'bodies']):
        return 'museum_exhibit'
    if any(w in name_lower for w in ['ride', 'coaster', 'shot', 'jump', 'scream', 'thrill']):
        return 'thrill_ride'
    if any(w in name_lower for w in ['pool', 'swim', 'water', 'aquarium', 'reef']):
        return 'aquatic'
    if any(w in name_lower for w in ['golf', 'topgolf', 'mini golf']):
        return 'golf'
    if any(w in name_lower for w in ['arcade', 'vr', 'virtual', 'esports', 'game', 'battlebot']):
        return 'gaming_vr'
    if any(w in name_lower for w in ['escape', 'mystery', 'paniq']):
        return 'escape_room'
    if any(w in name_lower for w in ['zip', 'fly', 'flyover']):
        return 'aerial_experience'
    if any(w in name_lower for w in ['show', 'fountain', 'spectacle', 'circus']):
        return 'free_show'
    if any(w in name_lower for w in ['shop', 'mall', 'store', 'chocolate']):
        return 'shopping_experience'
    return 'experience'


# ======================================================================
# MAIN
# ======================================================================

def main():
    parser = argparse.ArgumentParser(description='Scrape POI data from SmarterVegas')
    parser.add_argument('--category', choices=['restaurants', 'shows', 'nightlife',
                                               'attractions', 'all'],
                        default='all', help='Category to scrape')
    parser.add_argument('--details', action='store_true',
                        help='Scrape individual venue pages for details (slower)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be scraped without creating files')
    args = parser.parse_args()

    print("=" * 60)
    print("Sin City Travels - POI Scraper")
    print(f"Category: {args.category}")
    print(f"Scrape details: {args.details}")
    print(f"Dry run: {args.dry_run}")
    print(f"Output: {DATA_DIR}")
    print("=" * 60)

    total_created = 0

    if args.category in ('restaurants', 'all'):
        restaurants = scrape_dining_page()
        if restaurants and not args.dry_run:
            total_created += generate_restaurant_pois(restaurants, scrape_details=args.details)

    if args.category in ('shows', 'all'):
        shows = scrape_shows_page()
        if shows and not args.dry_run:
            total_created += generate_show_pois(shows, scrape_details=args.details)

    if args.category in ('nightlife', 'all'):
        nightlife = scrape_nightlife_page()
        if not args.dry_run:
            total_created += generate_nightlife_pois(nightlife, scrape_details=args.details)

    if args.category in ('attractions', 'all'):
        attractions = scrape_attractions_page()
        if attractions and not args.dry_run:
            total_created += generate_attraction_pois(attractions, scrape_details=args.details)

    print("\n" + "=" * 60)
    print(f"TOTAL NEW POIs CREATED: {total_created}")
    print("=" * 60)


if __name__ == '__main__':
    main()
