#!/usr/bin/env python3
"""
Import POI JSON files into PostgreSQL + PostGIS database

Usage:
    python scripts/import_pois.py

Requirements:
    pip install psycopg2-binary
"""

import json
import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extras import Json

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'sincitytravels'),
    'user': os.getenv('DB_USER', 'scapp'),
    'password': os.getenv('DB_PASSWORD', 'changeme_in_production')
}

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def import_poi(cur, poi_data, filepath):
    """Import a single POI into the database"""
    try:
        # Extract coordinates
        coords = poi_data.get('location', {}).get('coordinates', {})
        lat = coords.get('lat')
        lng = coords.get('lng')

        if not lat or not lng:
            print(f"  ⚠️  Skipping {poi_data['name']}: Missing coordinates")
            return False

        # Prepare data
        hours_json = Json(poi_data.get('hours', {}))
        ratings_json = Json(poi_data.get('ratings', {}))
        special_features_json = Json(poi_data.get('special_features', {}))

        # Handle size data (can be 'size' or 'size_details')
        size_data = poi_data.get('size', {}) or poi_data.get('size_details', {})
        size_json = Json(size_data)

        # Extract nested location data
        location_data = poi_data.get('location', {})

        # Insert POI
        cur.execute("""
            INSERT INTO pois (
                id, name, category, subcategory, casino_property,
                address, city, state, zip, level, area,
                location,
                phone, website, reservations_url,
                hours, price_range, average_per_person,
                description, cuisine, features, chef, dress_code, tags,
                ratings, special_features, size_details,
                data_sources, image_url, is_closed
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                category = EXCLUDED.category,
                subcategory = EXCLUDED.subcategory,
                casino_property = EXCLUDED.casino_property,
                address = EXCLUDED.address,
                location = EXCLUDED.location,
                phone = EXCLUDED.phone,
                website = EXCLUDED.website,
                hours = EXCLUDED.hours,
                description = EXCLUDED.description,
                updated_at = CURRENT_TIMESTAMP
        """, (
            poi_data['id'],
            poi_data['name'],
            poi_data['category'],
            poi_data.get('subcategory'),
            poi_data.get('casino_property'),

            location_data.get('address'),
            location_data.get('city', 'Las Vegas'),
            location_data.get('state', 'NV'),
            location_data.get('zip'),
            location_data.get('level'),
            location_data.get('area'),

            lng, lat,  # PostGIS uses lng, lat order

            poi_data.get('contact', {}).get('phone'),
            poi_data.get('contact', {}).get('website'),
            poi_data.get('contact', {}).get('reservations'),

            hours_json,
            poi_data.get('pricing', {}).get('price_range'),
            poi_data.get('pricing', {}).get('average_per_person'),

            poi_data.get('description'),
            poi_data.get('cuisine', []),
            poi_data.get('features', []),
            poi_data.get('chef'),
            poi_data.get('dress_code'),
            poi_data.get('tags', []),

            ratings_json,
            special_features_json,
            size_json,

            poi_data.get('data_sources', []),
            poi_data.get('image_url'),
            poi_data.get('is_closed', False)
        ))

        return True

    except Exception as e:
        print(f"  ❌ Error importing {poi_data.get('name', 'Unknown')}: {e}")
        return False

def import_all_pois():
    """Import all POI JSON files from data/pois directory"""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    poi_dir = project_root / "data" / "pois"

    if not poi_dir.exists():
        print(f"Error: POI directory not found: {poi_dir}")
        sys.exit(1)

    # Connect to database
    print("Connecting to database...")
    conn = connect_db()
    cur = conn.cursor()

    # Statistics
    total_files = 0
    imported = 0
    skipped = 0
    errors = 0

    # Import POIs by category (recursively walk subdirectories)
    for category_dir in sorted(poi_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith('.'):
            continue

        category_name = category_dir.name.replace('_', ' ').title()
        print(f"\n📁 {category_name}")

        # Use rglob to recursively find JSON files in subdirectories
        # (e.g., nightlife/bars/*.json, nightlife/nightclubs/*.json)
        for poi_file in sorted(category_dir.rglob("*.json")):
            total_files += 1

            try:
                with open(poi_file, 'r', encoding='utf-8') as f:
                    poi_data = json.load(f)

                # Use savepoint so one error doesn't abort the whole transaction
                cur.execute("SAVEPOINT poi_import")
                success = import_poi(cur, poi_data, poi_file)
                if success:
                    cur.execute("RELEASE SAVEPOINT poi_import")
                    print(f"  ✅ {poi_data['name']}")
                    imported += 1
                else:
                    cur.execute("ROLLBACK TO SAVEPOINT poi_import")
                    skipped += 1

            except json.JSONDecodeError as e:
                print(f"  ❌ Invalid JSON in {poi_file.name}: {e}")
                errors += 1
            except Exception as e:
                cur.execute("ROLLBACK TO SAVEPOINT poi_import")
                print(f"  ❌ Error processing {poi_file.name}: {e}")
                errors += 1

    # Commit all changes
    conn.commit()

    # Close connection
    cur.close()
    conn.close()

    # Print summary
    print("\n" + "="*60)
    print("📊 Import Summary")
    print("="*60)
    print(f"Total files processed: {total_files}")
    print(f"Successfully imported: {imported}")
    print(f"Skipped (missing data): {skipped}")
    print(f"Errors: {errors}")
    print("="*60)

    # Verify import
    if imported > 0:
        print("\n✨ Verifying import...")
        conn = connect_db()
        cur = conn.cursor()

        # Count POIs by category
        cur.execute("""
            SELECT category, COUNT(*) as count
            FROM pois
            GROUP BY category
            ORDER BY count DESC
        """)

        print("\nPOIs by category:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}")

        # Total count
        cur.execute("SELECT COUNT(*) FROM pois")
        total = cur.fetchone()[0]
        print(f"\nTotal POIs in database: {total}")

        cur.close()
        conn.close()

    print("\n✅ Import complete!")

if __name__ == "__main__":
    print("="*60)
    print("Sin City Travels - POI Import")
    print("="*60)

    import_all_pois()
