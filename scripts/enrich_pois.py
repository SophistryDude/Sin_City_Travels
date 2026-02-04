#!/usr/bin/env python3
"""
Sin City Travels - POI Enrichment Script
Reads existing POI JSON files, scrapes their SmarterVegas pages for details
(description, property, phone, price), and updates files in place.

Usage:
    python enrich_pois.py --category shows
    python enrich_pois.py --category nightlife
    python enrich_pois.py --category attractions
    python enrich_pois.py --category restaurants
    python enrich_pois.py --category all
    python enrich_pois.py --category all --tbd-only   (only fix TBD properties)
"""

import json
import os
import re
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

REQUEST_DELAY = 1.2  # seconds between requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "pois"

# Canonical property coordinates for updating location data
PROPERTIES = {
    "Aria": {"lat": 36.1067, "lng": -115.1761, "address": "3730 Las Vegas Blvd S, Las Vegas, NV 89158", "area": "Mid Strip"},
    "Bellagio": {"lat": 36.1127, "lng": -115.1765, "address": "3600 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "Caesars Palace": {"lat": 36.1162, "lng": -115.1744, "address": "3570 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "Casino Royale": {"lat": 36.1200, "lng": -115.1721, "address": "3411 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "Circus Circus": {"lat": 36.1367, "lng": -115.1631, "address": "2880 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "North Strip"},
    "Cosmopolitan": {"lat": 36.1095, "lng": -115.1742, "address": "3708 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "Encore": {"lat": 36.1289, "lng": -115.1650, "address": "3121 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "North Strip"},
    "Excalibur": {"lat": 36.0987, "lng": -115.1754, "address": "3850 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "South Strip"},
    "Fashion Show Mall": {"lat": 36.1268, "lng": -115.1700, "address": "3200 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "North Strip"},
    "Flamingo": {"lat": 36.1162, "lng": -115.1714, "address": "3555 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "Fontainebleau": {"lat": 36.1361, "lng": -115.1568, "address": "2777 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "North Strip"},
    "Four Seasons": {"lat": 36.0909, "lng": -115.1753, "address": "3960 Las Vegas Blvd S, Las Vegas, NV 89119", "area": "South Strip"},
    "Hard Rock": {"lat": 36.1246, "lng": -115.1679, "address": "3580 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "Harrah's": {"lat": 36.1190, "lng": -115.1726, "address": "3475 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "Horseshoe": {"lat": 36.1190, "lng": -115.1726, "address": "3475 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "Luxor": {"lat": 36.0955, "lng": -115.1761, "address": "3900 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "South Strip"},
    "Mandalay Bay": {"lat": 36.0909, "lng": -115.1743, "address": "3950 Las Vegas Blvd S, Las Vegas, NV 89119", "area": "South Strip"},
    "MGM Grand": {"lat": 36.1024, "lng": -115.1698, "address": "3799 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "South Strip"},
    "New York New York": {"lat": 36.1022, "lng": -115.1745, "address": "3790 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "South Strip"},
    "NoMad": {"lat": 36.1028, "lng": -115.1709, "address": "3772 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "South Strip"},
    "Palazzo": {"lat": 36.1228, "lng": -115.1693, "address": "3325 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "North Strip"},
    "Paris": {"lat": 36.1125, "lng": -115.1707, "address": "3655 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "Park MGM": {"lat": 36.1028, "lng": -115.1709, "address": "3770 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "South Strip"},
    "Planet Hollywood": {"lat": 36.1097, "lng": -115.1708, "address": "3663 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "Resorts World": {"lat": 36.1380, "lng": -115.1652, "address": "3000 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "North Strip"},
    "Sahara": {"lat": 36.1413, "lng": -115.1567, "address": "2535 Las Vegas Blvd S, Las Vegas, NV 89104", "area": "North Strip"},
    "The Cromwell": {"lat": 36.1168, "lng": -115.1722, "address": "3595 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "The LINQ": {"lat": 36.1176, "lng": -115.1710, "address": "3535 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "The Palazzo": {"lat": 36.1228, "lng": -115.1693, "address": "3325 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "North Strip"},
    "The Signature": {"lat": 36.1024, "lng": -115.1665, "address": "145 E Harmon Ave, Las Vegas, NV 89109", "area": "South Strip"},
    "The STRAT": {"lat": 36.1474, "lng": -115.1557, "address": "2000 Las Vegas Blvd S, Las Vegas, NV 89104", "area": "North Strip"},
    "The Strip": {"lat": 36.1147, "lng": -115.1728, "address": "Las Vegas Blvd S, Las Vegas, NV 89109", "area": "Mid Strip"},
    "The Venetian": {"lat": 36.1212, "lng": -115.1697, "address": "3355 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "North Strip"},
    "Treasure Island": {"lat": 36.1247, "lng": -115.1709, "address": "3300 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "North Strip"},
    "Tropicana": {"lat": 36.1012, "lng": -115.1730, "address": "3801 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "South Strip"},
    "Trump": {"lat": 36.1270, "lng": -115.1686, "address": "2000 Fashion Show Dr, Las Vegas, NV 89109", "area": "North Strip"},
    "Vdara": {"lat": 36.1080, "lng": -115.1773, "address": "2600 W Harmon Ave, Las Vegas, NV 89158", "area": "Mid Strip"},
    "W Las Vegas": {"lat": 36.1024, "lng": -115.1665, "address": "3950 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "South Strip"},
    "Waldorf Astoria": {"lat": 36.1070, "lng": -115.1755, "address": "3752 Las Vegas Blvd S, Las Vegas, NV 89158", "area": "Mid Strip"},
    "Wynn": {"lat": 36.1264, "lng": -115.1660, "address": "3131 Las Vegas Blvd S, Las Vegas, NV 89109", "area": "North Strip"},
    # Downtown & Off-Strip
    "Downtown Grand": {"lat": 36.1699, "lng": -115.1424, "address": "206 N 3rd St, Las Vegas, NV 89101", "area": "Downtown"},
    "Golden Nugget": {"lat": 36.1708, "lng": -115.1445, "address": "129 E Fremont St, Las Vegas, NV 89101", "area": "Downtown"},
    "Circa": {"lat": 36.1712, "lng": -115.1461, "address": "8 Fremont St, Las Vegas, NV 89101", "area": "Downtown"},
    "Palms": {"lat": 36.1145, "lng": -115.1848, "address": "4321 W Flamingo Rd, Las Vegas, NV 89103", "area": "Off-Strip"},
    "Rio": {"lat": 36.1167, "lng": -115.1878, "address": "3700 W Flamingo Rd, Las Vegas, NV 89103", "area": "Off-Strip"},
    "Durango": {"lat": 36.1464, "lng": -115.2797, "address": "5770 S Durango Dr, Las Vegas, NV 89113", "area": "Off-Strip"},
    "M Resort": {"lat": 36.0125, "lng": -115.1559, "address": "12300 Las Vegas Blvd S, Henderson, NV 89044", "area": "Off-Strip"},
    "Red Rock": {"lat": 36.1696, "lng": -115.3120, "address": "11011 W Charleston Blvd, Las Vegas, NV 89135", "area": "Off-Strip"},
    "Silverton": {"lat": 36.0765, "lng": -115.1863, "address": "3333 Blue Diamond Rd, Las Vegas, NV 89139", "area": "Off-Strip"},
    "AREA15": {"lat": 36.1262, "lng": -115.1943, "address": "3215 S Rancho Dr, Las Vegas, NV 89102", "area": "Off-Strip"},
}

# Extended property detection patterns for page text matching
# Maps text patterns to canonical property names
PROPERTY_PATTERNS = [
    # Strip properties - most specific first
    (r'(?:at |inside |in )(?:the )?Encore(?:\s|,|\.|$)', 'Encore'),
    (r'(?:at |inside |in )(?:the )?Wynn(?:\s|,|\.|$)', 'Wynn'),
    (r'(?:at |inside |in )(?:the )?Bellagio(?:\s|,|\.|$)', 'Bellagio'),
    (r'(?:at |inside |in )(?:the )?Aria(?:\s|,|\.|$)', 'Aria'),
    (r'(?:at |inside |in )(?:the )?Cosmopolitan(?:\s|,|\.|$)', 'Cosmopolitan'),
    (r'(?:at |inside |in )(?:the )?MGM Grand(?:\s|,|\.|$)', 'MGM Grand'),
    (r'(?:at |inside |in )(?:the )?Mandalay Bay(?:\s|,|\.|$)', 'Mandalay Bay'),
    (r'(?:at |inside |in )(?:the )?Caesars Palace(?:\s|,|\.|$)', 'Caesars Palace'),
    (r'(?:at |inside |in )(?:the )?Venetian(?:\s|,|\.|$)', 'The Venetian'),
    (r'(?:at |inside |in )(?:the )?Palazzo(?:\s|,|\.|$)', 'The Palazzo'),
    (r'(?:at |inside |in )(?:the )?Paris(?:\s|,|\.|$)', 'Paris'),
    (r'(?:at |inside |in )(?:the )?Planet Hollywood(?:\s|,|\.|$)', 'Planet Hollywood'),
    (r'(?:at |inside |in )(?:the )?Flamingo(?:\s|,|\.|$)', 'Flamingo'),
    (r'(?:at |inside |in )(?:the )?LINQ(?:\s|,|\.|$)', 'The LINQ'),
    (r'(?:at |inside |in )(?:the )?Cromwell(?:\s|,|\.|$)', 'The Cromwell'),
    (r'(?:at |inside |in )(?:the )?Horseshoe(?:\s|,|\.|$)', 'Horseshoe'),
    (r"(?:at |inside |in )(?:the )?Harrah'?s(?:\s|,|\.|$)", 'Harrah\'s'),
    (r'(?:at |inside |in )(?:the )?Luxor(?:\s|,|\.|$)', 'Luxor'),
    (r'(?:at |inside |in )(?:the )?Excalibur(?:\s|,|\.|$)', 'Excalibur'),
    (r'(?:at |inside |in )(?:the )?New York.New York(?:\s|,|\.|$)', 'New York New York'),
    (r'(?:at |inside |in )(?:the )?Park MGM(?:\s|,|\.|$)', 'Park MGM'),
    (r'(?:at |inside |in )(?:the )?Treasure Island(?:\s|,|\.|$)', 'Treasure Island'),
    (r'(?:at |inside |in )(?:the )?Circus Circus(?:\s|,|\.|$)', 'Circus Circus'),
    (r'(?:at |inside |in )(?:the )?STRAT(?:\s|,|\.|$)', 'The STRAT'),
    (r'(?:at |inside |in )(?:the )?Resorts World(?:\s|,|\.|$)', 'Resorts World'),
    (r'(?:at |inside |in )(?:the )?Fontainebleau(?:\s|,|\.|$)', 'Fontainebleau'),
    (r'(?:at |inside |in )(?:the )?Sahara(?:\s|,|\.|$)', 'Sahara'),
    (r'(?:at |inside |in )(?:the )?Tropicana(?:\s|,|\.|$)', 'Tropicana'),
    # Downtown
    (r'(?:at |inside |in )(?:the )?Golden Nugget(?:\s|,|\.|$)', 'Golden Nugget'),
    (r'(?:at |inside |in )(?:the )?Downtown Grand(?:\s|,|\.|$)', 'Downtown Grand'),
    (r'(?:at |inside |in )(?:the )?Circa(?:\s|,|\.|$)', 'Circa'),
    (r'Fremont Street', 'Downtown'),
    # Off-Strip
    (r'(?:at |inside |in )(?:the )?Palms(?:\s|,|\.|$)', 'Palms'),
    (r'(?:at |inside |in )(?:the )?Rio(?:\s|,|\.|$)', 'Rio'),
    (r'AREA ?15', 'AREA15'),
]


def fetch_page(url, delay=REQUEST_DELAY):
    """Fetch a page with rate limiting."""
    time.sleep(delay)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as e:
        print(f"    [ERROR] {url}: {e}")
        return None


def detect_property(text):
    """Detect which property a venue belongs to from page text.

    Only uses the "at/inside/in" prefix patterns to avoid false positives
    from property names appearing in site navigation or ads.
    """
    for pattern, prop_name in PROPERTY_PATTERNS:
        if re.search(pattern, text, re.I):
            return prop_name
    return None


def detect_property_from_meta(meta_text):
    """Detect property from meta description - more reliable than full page text.

    Uses broader patterns since meta descriptions are short and specific.
    """
    if not meta_text:
        return None

    # Check for explicit property mentions in meta description
    prop_names_to_check = [
        ('Encore', 'Encore'), ('Wynn', 'Wynn'), ('Bellagio', 'Bellagio'),
        ('Cosmopolitan', 'Cosmopolitan'), ('MGM Grand', 'MGM Grand'),
        ('Mandalay Bay', 'Mandalay Bay'), ('Caesars Palace', 'Caesars Palace'),
        ('Venetian', 'The Venetian'), ('Palazzo', 'The Palazzo'),
        ('Paris Las Vegas', 'Paris'), ('Paris Hotel', 'Paris'),
        ('Planet Hollywood', 'Planet Hollywood'), ('Flamingo', 'Flamingo'),
        ('LINQ', 'The LINQ'), ('Cromwell', 'The Cromwell'),
        ('Horseshoe', 'Horseshoe'), ("Harrah's", "Harrah's"),
        ('Luxor', 'Luxor'), ('Excalibur', 'Excalibur'),
        ('New York-New York', 'New York New York'), ('New York New York', 'New York New York'),
        ('Park MGM', 'Park MGM'), ('Treasure Island', 'Treasure Island'),
        ('Circus Circus', 'Circus Circus'), ('STRAT', 'The STRAT'),
        ('Resorts World', 'Resorts World'), ('Fontainebleau', 'Fontainebleau'),
        ('Sahara', 'Sahara'), ('Golden Nugget', 'Golden Nugget'),
        ('Palms', 'Palms'), ('Rio', 'Rio'), ('Circa', 'Circa'),
        ('Downtown Grand', 'Downtown Grand'), ('AREA15', 'AREA15'),
    ]
    for search_name, canonical in prop_names_to_check:
        if search_name.lower() in meta_text.lower():
            return canonical
    return None


def extract_content_text(soup):
    """Extract text from the main content area only, excluding sidebars and nav.

    SmarterVegas pages have related-venue carousels and bar/lounge directory
    listings in the sidebar that contain text like 'Lobby Bar at Wynn' which
    causes false positive property detection. This extracts only the header
    and main content area.
    """
    # Try to find the h1 (venue name) and get content near it
    h1 = soup.find('h1')
    if h1:
        # Get the h1's parent container text (usually the main content section)
        parent = h1.parent
        if parent:
            # Walk up to find a reasonable container (not body)
            for _ in range(3):
                if parent.parent and parent.parent.name not in ('body', 'html', '[document]'):
                    parent = parent.parent
                else:
                    break
            content_text = parent.get_text(' ', strip=True)
            # Limit to first 2000 chars to avoid sidebar content
            return content_text[:2000]

    # Fallback: use first 1500 chars of full text (before sidebars/directories)
    full_text = soup.get_text(' ', strip=True)
    return full_text[:1500]


def scrape_venue_details(url):
    """Scrape a SmarterVegas venue page for description, property, phone, price."""
    soup = fetch_page(url)
    if not soup:
        return {}

    details = {}

    # Meta description - usually the best summary
    meta = soup.find('meta', attrs={'name': 'description'})
    meta_text = ''
    if meta:
        meta_text = meta.get('content', '').strip()
        if meta_text and len(meta_text) > 20:
            details['description'] = meta_text[:500]

    # Full text for phone/price extraction
    text = soup.get_text(' ', strip=True)

    # Detect property - prefer meta description (more specific)
    # then fall back to "at/inside/in" patterns in CONTENT text only
    # (not full page which includes sidebar directories like "Lobby Bar at Wynn")
    prop = detect_property_from_meta(meta_text)
    if not prop:
        content_text = extract_content_text(soup)
        prop = detect_property(content_text)

    if prop:
        details['property'] = prop

    # Phone number
    phone_match = re.search(r'\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})', text)
    if phone_match:
        details['phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"

    # Price
    price_match = re.search(r'from\s*\$(\d+)', text, re.I)
    if price_match:
        details['price_from'] = int(price_match.group(1))

    # Price range symbols
    range_match = re.search(r'(\${2,5}\+?)', text)
    if range_match:
        details['price_range'] = range_match.group(1)

    return details


def update_poi_file(filepath, details):
    """Update a POI JSON file with scraped details."""
    with open(filepath, 'r', encoding='utf-8') as f:
        poi = json.load(f)

    changed = False

    # Update description if missing or very short
    if details.get('description') and (not poi.get('description') or len(poi.get('description', '')) < 20):
        poi['description'] = details['description']
        changed = True

    # Update property if currently TBD/generic (Las Vegas Strip)
    # Do NOT change "Off-Strip" venues - those are intentionally off-strip
    if details.get('property'):
        current_prop = poi.get('casino_property', '')
        is_generic = current_prop in ('Las Vegas Strip', '', None)
        is_same = current_prop == details['property']
        if is_generic or is_same:
            prop_name = details['property']
            if prop_name in PROPERTIES:
                prop_data = PROPERTIES[prop_name]
                poi['casino_property'] = prop_name
                poi['location']['casino'] = prop_name
                poi['location']['address'] = prop_data['address']
                poi['location']['coordinates']['lat'] = prop_data['lat']
                poi['location']['coordinates']['lng'] = prop_data['lng']
                poi['location']['area'] = prop_data['area']
                changed = True

    # Update phone if missing
    if details.get('phone') and not poi.get('contact', {}).get('phone'):
        if 'contact' not in poi:
            poi['contact'] = {}
        poi['contact']['phone'] = details['phone']
        changed = True

    # Update price range if missing
    if details.get('price_range') and not poi.get('pricing', {}).get('price_range'):
        poi['pricing'] = poi.get('pricing', {})
        poi['pricing']['price_range'] = details['price_range']
        changed = True
    elif details.get('price_from'):
        price_from = details['price_from']
        if not poi.get('pricing'):
            if price_from > 80:
                poi['pricing'] = {'price_range': '$$$$'}
            elif price_from > 40:
                poi['pricing'] = {'price_range': '$$$'}
            else:
                poi['pricing'] = {'price_range': '$$'}
            changed = True

    if changed:
        poi['updated_at'] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if 'smartervegas_enriched' not in poi.get('data_sources', []):
            poi.setdefault('data_sources', []).append('smartervegas_enriched')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(poi, f, indent=2, ensure_ascii=False)

    return changed


def needs_enrichment(poi, tbd_only=False):
    """Check if a POI needs enrichment."""
    prop = poi.get('casino_property', '')
    has_desc = poi.get('description') and len(poi.get('description', '')) > 20
    is_tbd = prop in ('Las Vegas Strip', 'Off-Strip', '', None)

    if tbd_only:
        return is_tbd
    return is_tbd or not has_desc


def get_venue_url(poi):
    """Extract the SmarterVegas URL from a POI."""
    # Check contact.website
    url = poi.get('contact', {}).get('website', '')
    if 'smartervegas.com' in url:
        return url
    return None


def enrich_category(category_dir, tbd_only=False):
    """Enrich all POIs in a category directory."""
    enriched = 0
    skipped = 0
    failed = 0
    total = 0

    for root, dirs, files in os.walk(category_dir):
        json_files = [f for f in files if f.endswith('.json')]
        for filename in sorted(json_files):
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    poi = json.load(f)
            except (json.JSONDecodeError, ValueError):
                continue

            total += 1

            if not needs_enrichment(poi, tbd_only):
                skipped += 1
                continue

            url = get_venue_url(poi)
            if not url:
                skipped += 1
                continue

            name = poi.get('name', filename)
            prop = poi.get('casino_property', 'TBD')
            details = scrape_venue_details(url)

            if details:
                updated = update_poi_file(filepath, details)
                if updated:
                    new_prop = details.get('property', prop)
                    desc_preview = (details.get('description', '')[:60] + '...') if details.get('description') else 'no desc'
                    print(f"    [UPDATED] {name} | {prop} -> {new_prop} | {desc_preview}")
                    enriched += 1
                else:
                    skipped += 1
            else:
                failed += 1

    return total, enriched, skipped, failed


def main():
    parser = argparse.ArgumentParser(description='Enrich POI data from SmarterVegas')
    parser.add_argument('--category', choices=['restaurants', 'shows', 'nightlife',
                                               'attractions', 'all'],
                        default='all', help='Category to enrich')
    parser.add_argument('--tbd-only', action='store_true',
                        help='Only fix POIs with TBD/generic property names')
    args = parser.parse_args()

    print("=" * 70)
    print("Sin City Travels - POI Enrichment")
    print(f"Category: {args.category}")
    print(f"TBD-only mode: {args.tbd_only}")
    print("=" * 70)

    grand_total = 0
    grand_enriched = 0

    categories = {
        'restaurants': DATA_DIR / 'restaurants',
        'shows': DATA_DIR / 'shows',
        'nightlife': DATA_DIR / 'nightlife',
        'attractions': DATA_DIR / 'attractions',
    }

    for cat_name, cat_dir in categories.items():
        if args.category not in (cat_name, 'all'):
            continue
        if not cat_dir.exists():
            continue

        print(f"\n=== Enriching {cat_name} ===")
        total, enriched, skipped, failed = enrich_category(str(cat_dir), args.tbd_only)
        grand_total += total
        grand_enriched += enriched
        print(f"  Total: {total} | Enriched: {enriched} | Skipped: {skipped} | Failed: {failed}")

    print("\n" + "=" * 70)
    print(f"GRAND TOTAL: {grand_total} POIs checked, {grand_enriched} enriched")
    print("=" * 70)


if __name__ == '__main__':
    main()
