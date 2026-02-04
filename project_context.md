# Sin City Travels - Project Context

**Project Type**: Indoor Navigation & Wayfinding App for Las Vegas Casinos
**Created**: February 3, 2026
**Status**: Phase 1 Complete - Data Collection & Infrastructure
**Repository**: https://github.com/SophistryDude/Sin_City_Travels

---

## Project Overview

Sin City Travels is an indoor navigation application for Las Vegas casinos and hotels that helps visitors navigate complex casino layouts with:
- **3D Indoor Maps**: Visualize casino layouts and hotel interiors
- **Turn-by-Turn Directions**: Navigate inside massive casino properties
- **Ride-Share Integration**: Connect with Uber/Lyft for inter-property travel
- **POI Discovery**: Find restaurants, shops, shows, and attractions
- **Efficient Pathfinding**: ML-powered routing with Google Maps API integration

### End Goal
Build a model using Google Maps API that helps people figure out efficient walking pathways between locations with various POIs, combining:
- Indoor navigation within casino properties
- Outdoor routing between properties (Google Maps)
- Accessibility considerations
- Real-time directions

---

## Current Status

### Phase 1: Data Collection ✅ COMPLETE

**Floor Plans & Maps**:
- ✅ 31 casino properties with PDF floor plans (7.3 MB)
- ✅ OpenStreetMap data for Las Vegas Strip (94 hotels, 36 casinos, 523 KB GeoJSON)
- ✅ Data tracking CSV for all properties

**Points of Interest (POIs)**: 43 POIs created
- **Restaurants** (37): Fine dining, celebrity chefs, Michelin-starred
  - MGM Grand (3), Park MGM (1), Bellagio (3), Caesars Palace (5)
  - Aria (5), The Venetian (4), The Cosmopolitan (5)
  - Wynn/Encore (5), Mandalay Bay (5), Off-Strip (1)
- **Shopping** (4): Forum Shops, Grand Canal Shoppes, Crystals, Miracle Mile
- **Entertainment** (2): "O" and KÀ by Cirque du Soleil

**Celebrity Chefs Featured**: 15+
- Wolfgang Puck, Gordon Ramsay, José Andrés, Bobby Flay, Thomas Keller
- Michael Mina, David Chang, Akira Back, Jean-Georges Vongerichten, etc.

**Awards**:
- 3 Michelin-starred restaurants (Hakkasan, Wing Lei, Restaurant Guy Savoy)
- 2 AAA Five-Diamond restaurants (Picasso, Le Cirque)

### Phase 1: Database Infrastructure ✅ COMPLETE

**Kubernetes Deployment**:
- PostgreSQL 16 + PostGIS 3.4
- Namespace: `sin-city-travels`
- PersistentVolumeClaim: 10GB storage
- ConfigMaps, Secrets, Service
- Health checks and resource limits
- Docker Compose for local development

**Database Schema**:
```sql
Tables Created:
├── pois                 # 43 POIs with spatial indexing
├── properties           # 9 major casino properties
├── navigation_nodes     # Indoor navigation graph nodes
├── navigation_edges     # Connections for pathfinding
└── synthetic_routes     # ML training data
```

**PostGIS Features**:
- Spatial indexing (GIST) for performance
- Geography data type for accurate distance calculations
- Custom functions: `find_nearby_pois()`, `calculate_poi_distance()`
- Proximity search with category filtering

**Python Scripts**:
- `scripts/import_pois.py` - Import all POI JSON files
- `scripts/generate_synthetic_routes.py` - Generate navigation data:
  - Navigation nodes (entrances, junctions, elevators)
  - Navigation edges (walkways, stairs, elevators)
  - Synthetic routes between POIs for ML training

---

## Technology Stack

### Current (Implemented)
- **Database**: PostgreSQL 16 + PostGIS 3.4
- **Container Orchestration**: Kubernetes / Docker Compose
- **Data Format**: JSON, GeoJSON
- **Scripting**: Python 3.x
- **Spatial Queries**: PostGIS geography/geometry

### Planned
- **Frontend**: React Native (iOS/Android)
- **3D Visualization**: Three.js / React Three Fiber
- **Backend API**: Node.js / Python Flask
- **Outdoor Navigation**: Google Maps API
- **Indoor Positioning**: Bluetooth beacons / WiFi triangulation
- **ML/Pathfinding**: A* algorithm, Dijkstra, or ML-based routing

---

## Project Structure

```
sin-city-travels/
├── data/
│   ├── maps/
│   │   └── las_vegas_strip_hotels_casinos.json (523 KB OSM data)
│   ├── attractions/          # 31 casino floor plan PDFs
│   │   ├── Caesars_Palace/
│   │   ├── Bellagio/
│   │   ├── MGM_Grand/
│   │   └── ... (28 more)
│   ├── pois/
│   │   ├── restaurants/      # 37 restaurant POI JSON files
│   │   ├── shopping/         # 4 shopping center JSON files
│   │   ├── shows/            # 2 show JSON files
│   │   ├── MGM_RESORTS_RESTAURANTS_SUMMARY.md
│   │   └── POI_COLLECTION_SUMMARY.md
│   ├── LAS_VEGAS_DATA_TRACKING.csv
│   └── OSM_DATA_SUMMARY.md
├── docs/
│   ├── DATA_COLLECTION_PLAN.md
│   ├── YELP_API_SETUP.md (paid subscription required)
│   ├── POI_COLLECTION_PLAN.md
│   └── GOOGLE_INDOOR_MAPS_SURVEY.md
├── k8s/                      # Kubernetes infrastructure
│   ├── postgres-deployment.yaml
│   ├── postgres-init-configmap.yaml
│   ├── init-db.sql           # Complete database schema
│   └── README.md             # Infrastructure documentation
├── scripts/
│   ├── bulk_collect_pois.js  # Yelp API bulk collection (not used - paid)
│   ├── import_pois.py        # Import POIs to PostgreSQL
│   ├── generate_synthetic_routes.py  # Generate navigation data
│   └── README.md
├── docker-compose.yml        # Local development environment
├── README.md                 # Project overview
└── project_context.md        # This file
```

---

## Data Collection Methods

### Successfully Used
1. **Web Scraping**: SmarterVegas.com, LaVegasRestaurants.com
2. **Manual Curation**: Official casino websites, OpenTable
3. **Web Search**: 2026-updated information verification
4. **OpenStreetMap**: Overpass API for geographic data

### Not Used (Limitations)
1. **Yelp API**: Requires paid subscription ($$ for 30-day trial)
2. **Google Indoor Maps**: Discontinued/limited in 2026
3. **Foursquare API**: Not implemented (alternative option)

---

## Database Schema Details

### POIs Table
```sql
CREATE TABLE pois (
    id VARCHAR(20) PRIMARY KEY,           -- poi_001, poi_002, etc.
    name VARCHAR(255) NOT NULL,
    category poi_category NOT NULL,       -- restaurant, shopping, entertainment, etc.
    subcategory poi_subcategory,
    casino_property VARCHAR(100),

    -- Location (PostGIS)
    location GEOGRAPHY(POINT, 4326),      -- Spatial index
    address TEXT,
    level VARCHAR(50),                    -- ground, level_2, etc.
    area VARCHAR(50),                     -- North Strip, Mid Strip, South Strip

    -- Contact
    phone VARCHAR(20),
    website TEXT,
    reservations_url TEXT,

    -- Details
    hours JSONB,                          -- Flexible JSON structure
    price_range price_range,              -- $, $$, $$$, $$$$, $$$$+
    description TEXT,
    cuisine TEXT[],                       -- Array of cuisine types
    features TEXT[],                      -- Array of features
    tags TEXT[],                          -- Array of tags

    -- Ratings
    ratings JSONB,                        -- Michelin, AAA, etc.

    -- Metadata
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Spatial index for proximity queries
CREATE INDEX idx_pois_location ON pois USING GIST(location);
```

### Navigation Tables
```sql
-- Indoor navigation nodes
CREATE TABLE navigation_nodes (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES properties(id),
    node_type VARCHAR(50),                -- entrance, elevator, stairs, junction
    location GEOGRAPHY(POINT, 4326),
    indoor_x FLOAT,                       -- Indoor coordinate system
    indoor_y FLOAT,
    indoor_level INTEGER,
    accessibility_features TEXT[]
);

-- Connections between nodes
CREATE TABLE navigation_edges (
    id SERIAL PRIMARY KEY,
    from_node_id INTEGER REFERENCES navigation_nodes(id),
    to_node_id INTEGER REFERENCES navigation_nodes(id),
    edge_type VARCHAR(50),                -- walkway, stairs, elevator
    distance_meters FLOAT,
    estimated_time_seconds INTEGER,
    accessibility_rating INTEGER,         -- 1-5, 5 = fully accessible
    is_bidirectional BOOLEAN
);

-- Synthetic training data
CREATE TABLE synthetic_routes (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES properties(id),
    start_poi_id VARCHAR(20) REFERENCES pois(id),
    end_poi_id VARCHAR(20) REFERENCES pois(id),
    total_distance_meters FLOAT,
    estimated_time_seconds INTEGER,
    path_nodes INTEGER[],                 -- Array of node IDs
    has_stairs BOOLEAN,
    has_elevator BOOLEAN,
    accessibility_score INTEGER
);
```

---

## Quick Start Guide

### 1. Start Database (Local)
```bash
# Start PostgreSQL + PostGIS + PGAdmin
cd sin-city-travels
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f postgres
```

**Access**:
- PostgreSQL: `localhost:5432`
- Database: `sincitytravels`
- User: `scapp`
- Password: `changeme_in_production`
- PGAdmin: `http://localhost:5050` (admin@sincity.local / admin)

### 2. Import POI Data
```bash
# Install dependencies
pip install psycopg2-binary

# Import all 43 POIs
python scripts/import_pois.py
```

### 3. Generate Synthetic Navigation Data
```bash
# Install dependencies
pip install psycopg2-binary numpy

# Generate nodes, edges, and routes
python scripts/generate_synthetic_routes.py
```

### 4. Query Database
```sql
-- Connect to database
psql -h localhost -U scapp -d sincitytravels

-- Find nearby restaurants
SELECT * FROM find_nearby_pois(
    36.1127,      -- Bellagio latitude
    -115.1765,    -- Bellagio longitude
    500,          -- 500 meters radius
    'restaurant'  -- category filter
);

-- Count POIs by category
SELECT category, COUNT(*) FROM pois GROUP BY category;

-- Calculate distance between two POIs
SELECT calculate_poi_distance('poi_001', 'poi_002');
```

---

## Next Steps

### Phase 2: MVP Development

#### A. Google Maps API Integration
**Goal**: Combine indoor + outdoor navigation

**Architecture**:
```
User Journey: Restaurant at Bellagio → Shopping at Caesars Palace

1. Indoor Navigation (Bellagio):
   - Query navigation_nodes for path to nearest entrance
   - Calculate route through navigation_edges
   - Display turn-by-turn: "Walk 50m, turn right, elevator to ground floor"

2. Outdoor Navigation (Google Maps API):
   - Get walking directions: Bellagio entrance → Caesars entrance
   - Display: "Walk 0.4 miles (7 minutes) via Las Vegas Blvd"

3. Indoor Navigation (Caesars):
   - Query navigation_nodes from entrance to Forum Shops
   - Calculate route through navigation_edges
   - Display turn-by-turn to destination
```

**Implementation Steps**:
1. Set up Google Maps Directions API
2. Create API endpoints for:
   - Indoor pathfinding (A* or Dijkstra on navigation graph)
   - Outdoor routing (Google Maps API wrapper)
   - Combined route generation
3. Build route optimization logic:
   - Minimize total time
   - Respect accessibility preferences
   - Consider user preferences (avoid stairs, etc.)

#### B. Pathfinding Model
**Train ML model on synthetic routes**:

**Input Features**:
- Start POI coordinates, category
- End POI coordinates, category
- User preferences (accessibility, speed)
- Time of day
- Property layout complexity

**Output**:
- Predicted optimal path (node IDs)
- Estimated time
- Accessibility score

**Training Data**: `synthetic_routes` table
- 100+ routes per property
- 900+ total routes (9 properties × 100)
- Distance, time, accessibility metrics

#### C. Mobile App Prototype
**React Native app with**:
- POI search and discovery
- Route planning interface
- Turn-by-turn navigation
- 2D indoor maps (SVG from PDFs)
- Uber/Lyft integration

### Phase 3: 3D Visualization
- 3D models of casino interiors (Three.js)
- Augmented reality navigation
- Real-time positioning (Bluetooth beacons)

### Phase 4: Expansion
- Cover all 31+ Strip properties
- Add Downtown Las Vegas
- Off-strip attractions
- User-generated content (reviews, photos)

---

## Key Decisions & Rationale

### Why PostgreSQL + PostGIS?
- **Spatial indexing**: Fast proximity queries
- **Mature ecosystem**: Well-documented, stable
- **Complex queries**: SQL for route optimization
- **Scalability**: Handle millions of POIs and routes

### Why Kubernetes?
- **Production-ready**: Industry standard
- **Scalability**: Easy to add replicas
- **Portability**: Run anywhere (cloud, on-prem)
- **Declarative**: YAML config, GitOps-friendly

### Why Synthetic Routes?
- **ML Training**: Need labeled data for pathfinding model
- **Testing**: Validate algorithms before production
- **Baseline**: Compare ML predictions vs. actual routes

### Why Manual Curation over API?
- **Quality**: Higher accuracy from official sources
- **Cost**: Free vs. paid API subscriptions
- **Control**: Cherry-pick best restaurants/venues
- **Curation**: Focus on tourist-relevant POIs

---

## Technical Challenges

### 1. Indoor Positioning
**Problem**: GPS doesn't work indoors
**Solutions**:
- Bluetooth beacons (iBeacon/Eddystone)
- WiFi triangulation
- Visual positioning (camera + AI)
- Manual check-in at known POIs

### 2. Floor Plan Georeferencing
**Problem**: PDF maps need real-world coordinates
**Solutions**:
- Manual georeferencing (QGIS)
- Extract coordinates from known POIs
- Use building footprints from OSM

### 3. Route Optimization
**Problem**: Balance distance, time, accessibility
**Solutions**:
- Multi-objective optimization
- User preference weighting
- A* with custom heuristics
- ML model for learned preferences

### 4. Data Freshness
**Problem**: Restaurants close, shows change
**Solutions**:
- Automated web scraping (weekly)
- User reporting (closed/moved)
- API integrations (OpenTable, etc.)
- Version tracking in database

---

## Performance Considerations

### Database Optimization
- **Spatial indexes**: GIST on all location columns
- **Array indexes**: GIN on tags, features, cuisine
- **Partitioning**: By property or geographic area
- **Connection pooling**: PgBouncer for API layer

### API Design
- **Caching**: Redis for frequent queries (nearby POIs)
- **Rate limiting**: Protect from abuse
- **Pagination**: Large result sets
- **GraphQL**: Flexible queries for mobile app

### Mobile App
- **Offline maps**: Pre-download property maps
- **Image optimization**: WebP, lazy loading
- **Bundle splitting**: Code splitting for faster load
- **Native modules**: Performance-critical pathfinding

---

## Security & Privacy

### Database
- ✅ Secrets management (Kubernetes Secrets)
- ⚠️ Default password must be changed in production
- 🔒 SSL/TLS for connections (TODO)
- 🔐 Row-level security (TODO)

### API
- 🔑 JWT authentication (TODO)
- 🛡️ Input validation and sanitization
- 🚦 Rate limiting (TODO)
- 📝 Audit logging (TODO)

### User Data
- 📍 Location data: Only while app is in use
- 🕵️ Privacy: No tracking, no selling data
- 🔒 GDPR compliance (TODO)

---

## Monitoring & Metrics

### Database Metrics (TODO)
- Query performance (pg_stat_statements)
- Connection count
- Table sizes and growth
- Index usage
- Replication lag (if applicable)

### Application Metrics (TODO)
- API response times
- Route calculation times
- Cache hit rates
- Error rates
- User engagement (routes calculated, POIs viewed)

### Business Metrics (TODO)
- DAU/MAU (Daily/Monthly Active Users)
- Route completion rate
- POI discovery rate
- Uber/Lyft integration usage

---

## Documentation

### Available
- [README.md](README.md) - Project overview
- [k8s/README.md](k8s/README.md) - Infrastructure setup
- [docs/DATA_COLLECTION_PLAN.md](docs/DATA_COLLECTION_PLAN.md) - Data collection strategy
- [docs/POI_COLLECTION_PLAN.md](docs/POI_COLLECTION_PLAN.md) - POI collection details
- [data/pois/POI_COLLECTION_SUMMARY.md](data/pois/POI_COLLECTION_SUMMARY.md) - POI statistics

### TODO
- API documentation (OpenAPI/Swagger)
- Mobile app architecture
- Deployment guide
- Contributing guidelines
- User manual

---

## Team & Contributors

**Project Lead**: SophistryDude
**AI Assistant**: Claude Sonnet 4.5 (February 3, 2026)

---

## Timeline

| Date | Milestone |
|------|-----------|
| Feb 3, 2026 | Project initialized, repository created |
| Feb 3, 2026 | Floor plans downloaded (31 properties) |
| Feb 3, 2026 | OSM data collected |
| Feb 3, 2026 | POI collection (43 POIs) |
| Feb 3, 2026 | Database schema designed |
| Feb 3, 2026 | Kubernetes infrastructure created |
| Feb 3, 2026 | Synthetic route generation |
| **TBD** | Google Maps API integration |
| **TBD** | ML pathfinding model training |
| **TBD** | Mobile app MVP |
| **TBD** | Public beta |

---

## Contact & Links

- **GitHub**: https://github.com/SophistryDude/Sin_City_Travels
- **Database**: PostgreSQL 16 + PostGIS 3.4
- **POIs**: 43 (37 restaurants, 4 shopping, 2 shows)
- **Properties**: 9 major Strip casinos
- **Floor Plans**: 31 casinos (7.3 MB PDFs)

---

**Last Updated**: February 3, 2026
**Version**: 1.0 (Phase 1 Complete)
