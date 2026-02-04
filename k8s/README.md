# Sin City Travels - Kubernetes & Database Setup

PostgreSQL + PostGIS database infrastructure for the Sin City Travels navigation system.

---

## Overview

This directory contains Kubernetes deployment configurations and database initialization scripts for:
- **PostgreSQL 16** with **PostGIS 3.4** extension
- Spatial data storage for POIs, properties, and navigation
- Indoor navigation graph (nodes and edges)
- Pathfinding infrastructure

---

## Quick Start

### Option 1: Docker Compose (Local Development)

Fastest way to get started locally:

```bash
# Start PostgreSQL + PostGIS + PGAdmin
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f postgres

# Connect to database
docker-compose exec postgres psql -U scapp -d sincitytravels
```

**Access Details**:
- **PostgreSQL**: `localhost:5432`
- **Database**: `sincitytravels`
- **Username**: `scapp`
- **Password**: `changeme_in_production`
- **PGAdmin**: `http://localhost:5050` (admin@sincity.local / admin)

### Option 2: Kubernetes Deployment

Deploy to Kubernetes cluster:

```bash
# Apply all configurations
kubectl apply -f k8s/postgres-deployment.yaml

# Check deployment status
kubectl get pods -n sin-city-travels

# Get service endpoint
kubectl get svc -n sin-city-travels

# Port forward for local access
kubectl port-forward -n sin-city-travels svc/postgres-service 5432:5432

# Connect
psql -h localhost -U scapp -d sincitytravels
```

---

## Database Schema

### Core Tables

#### `pois` - Points of Interest
Stores all POIs (restaurants, shops, shows, etc.) with spatial indexing:
- Location data (lat/lng with PostGIS geography)
- Contact information
- Operating hours (JSONB)
- Ratings and awards (JSONB)
- Cuisine, features, tags (arrays)
- Spatial index for proximity queries

#### `properties` - Casino/Hotel Properties
Stores property information:
- Property location (spatial)
- Floor plan metadata
- Amenities and features
- Property details

#### `navigation_nodes` - Indoor Navigation Points
Navigation graph nodes for pathfinding:
- Node type (entrance, elevator, stairs, junction, POI)
- Indoor coordinates (x, y, level)
- Accessibility features
- Linked to properties

#### `navigation_edges` - Navigation Connections
Connections between navigation nodes:
- Distance and estimated time
- Edge type (walkway, stairs, elevator)
- Accessibility rating
- Bidirectional support

#### `synthetic_routes` - Training Data
Synthetic route data for ML model training:
- Start/end POIs
- Path through navigation graph
- Distance and time metrics
- Accessibility characteristics

---

## Database Functions

### `calculate_poi_distance(poi1_id, poi2_id)`
Calculate straight-line distance between two POIs.

```sql
SELECT calculate_poi_distance('poi_001', 'poi_002');
```

### `find_nearby_pois(lat, lng, radius_meters, category)`
Find POIs within a radius of a point.

```sql
-- Find restaurants within 500m of a point
SELECT * FROM find_nearby_pois(
    36.1127,      -- latitude
    -115.1765,    -- longitude
    500,          -- radius in meters
    'restaurant'  -- optional category filter
);
```

---

## Data Import

### Import POI JSON Files

Script to import all POI JSON files into the database:

```python
#!/usr/bin/env python3
import json
import os
import psycopg2
from pathlib import Path

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="sincitytravels",
    user="scapp",
    password="changeme_in_production"
)
cur = conn.cursor()

# Import all POI JSON files
poi_dir = Path("../data/pois")
for category_dir in poi_dir.iterdir():
    if not category_dir.is_dir():
        continue

    for poi_file in category_dir.glob("*.json"):
        with open(poi_file) as f:
            poi = json.load(f)

        # Insert POI
        cur.execute("""
            INSERT INTO pois (
                id, name, category, subcategory, casino_property,
                address, level, area,
                location,
                phone, website, reservations_url,
                hours, price_range, average_per_person,
                description, cuisine, features, chef, dress_code, tags,
                ratings, special_features, size_details,
                data_sources, image_url, is_closed
            ) VALUES (
                %(id)s, %(name)s, %(category)s, %(subcategory)s, %(casino_property)s,
                %(address)s, %(level)s, %(area)s,
                ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
                %(phone)s, %(website)s, %(reservations)s,
                %(hours)s::jsonb, %(price_range)s, %(avg_per_person)s,
                %(description)s, %(cuisine)s, %(features)s, %(chef)s, %(dress_code)s, %(tags)s,
                %(ratings)s::jsonb, %(special_features)s::jsonb, %(size_details)s::jsonb,
                %(data_sources)s, %(image_url)s, %(is_closed)s
            )
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                updated_at = CURRENT_TIMESTAMP
        """, {
            'id': poi['id'],
            'name': poi['name'],
            'category': poi['category'],
            'subcategory': poi.get('subcategory'),
            'casino_property': poi.get('casino_property'),
            'address': poi.get('location', {}).get('address'),
            'level': poi.get('location', {}).get('level'),
            'area': poi.get('location', {}).get('area'),
            'lat': poi.get('location', {}).get('coordinates', {}).get('lat'),
            'lng': poi.get('location', {}).get('coordinates', {}).get('lng'),
            'phone': poi.get('contact', {}).get('phone'),
            'website': poi.get('contact', {}).get('website'),
            'reservations': poi.get('contact', {}).get('reservations'),
            'hours': json.dumps(poi.get('hours', {})),
            'price_range': poi.get('pricing', {}).get('price_range'),
            'avg_per_person': poi.get('pricing', {}).get('average_per_person'),
            'description': poi.get('description'),
            'cuisine': poi.get('cuisine', []),
            'features': poi.get('features', []),
            'chef': poi.get('chef'),
            'dress_code': poi.get('dress_code'),
            'tags': poi.get('tags', []),
            'ratings': json.dumps(poi.get('ratings', {})),
            'special_features': json.dumps(poi.get('special_features', {})),
            'size_details': json.dumps(poi.get('size', {})) if 'size' in poi else json.dumps(poi.get('size_details', {})),
            'data_sources': poi.get('data_sources', []),
            'image_url': poi.get('image_url'),
            'is_closed': poi.get('is_closed', False)
        })

        print(f"Imported: {poi['name']}")

conn.commit()
cur.close()
conn.close()

print(f"\nImport complete!")
```

Save as `scripts/import_pois.py` and run:
```bash
python scripts/import_pois.py
```

---

## Kubernetes Configuration

### PersistentVolumeClaim
- **Size**: 10GB (adjust based on needs)
- **Access Mode**: ReadWriteOnce
- **Storage Class**: standard (change for production)

### Deployment
- **Image**: postgis/postgis:16-3.4
- **Replicas**: 1 (increase for HA)
- **Resources**:
  - Requests: 512Mi RAM, 0.5 CPU
  - Limits: 2Gi RAM, 1 CPU

### Service
- **Type**: ClusterIP (internal only)
- **Port**: 5432

### Secrets
**IMPORTANT**: Change the default password before production deployment!

```bash
# Create a secure password
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_PASSWORD='your_secure_password_here' \
  -n sin-city-travels
```

---

## Backup & Restore

### Backup Database

```bash
# Using kubectl exec
kubectl exec -n sin-city-travels $(kubectl get pod -n sin-city-travels -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- \
  pg_dump -U scapp sincitytravels > backup_$(date +%Y%m%d).sql

# Using docker-compose
docker-compose exec postgres pg_dump -U scapp sincitytravels > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
# Using kubectl
kubectl exec -i -n sin-city-travels $(kubectl get pod -n sin-city-travels -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- \
  psql -U scapp sincitytravels < backup_20260203.sql

# Using docker-compose
docker-compose exec -T postgres psql -U scapp sincitytravels < backup_20260203.sql
```

---

## Monitoring

### Check Database Health

```sql
-- Connection count
SELECT count(*) FROM pg_stat_activity;

-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- POI count by category
SELECT category, COUNT(*) FROM pois GROUP BY category;

-- Spatial index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE indexname LIKE '%location%';
```

---

## Troubleshooting

### Pod won't start
```bash
kubectl describe pod -n sin-city-travels <pod-name>
kubectl logs -n sin-city-travels <pod-name>
```

### Connection refused
```bash
# Check service
kubectl get svc -n sin-city-travels

# Port forward
kubectl port-forward -n sin-city-travels svc/postgres-service 5432:5432
```

### PostGIS extension not available
```sql
-- Check installed extensions
SELECT * FROM pg_available_extensions WHERE name LIKE '%postgis%';

-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
```

---

## Next Steps

1. **Import POI Data**: Run `import_pois.py` to load all JSON POIs
2. **Generate Synthetic Routes**: Create training data for pathfinding model
3. **Set up Google Maps API**: Configure for outdoor navigation
4. **Build Navigation Graph**: Add indoor nodes and edges for major properties

---

## Production Checklist

- [ ] Change default PostgreSQL password
- [ ] Configure proper storage class
- [ ] Set up automated backups
- [ ] Configure resource limits
- [ ] Enable monitoring (Prometheus/Grafana)
- [ ] Set up replication (if needed)
- [ ] Configure SSL/TLS
- [ ] Implement connection pooling (PgBouncer)
- [ ] Set up log aggregation

---

**Created**: February 3, 2026
**PostgreSQL Version**: 16
**PostGIS Version**: 3.4
