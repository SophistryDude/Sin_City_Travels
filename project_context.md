# Sin City Travels - Project Context

**Project Type**: Indoor Navigation & Wayfinding App for Las Vegas Casinos
**Created**: February 3, 2026
**Status**: Phase 2 Complete - Interactive Web Demo Deployed
**Repository**: https://github.com/SophistryDude/Sin_City_Travels
**Live Demo**: http://3.140.78.15:8888/

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

**Points of Interest (POIs)**: 994 POIs across 63 properties
- **Restaurants** (518): Fine dining, casual, buffets, celebrity chefs
  - 37 hand-curated originals (Michelin-starred, celebrity chef venues)
  - 481 scraped from SmarterVegas.com covering 40+ properties
  - All mapped to correct casino properties with enriched metadata
- **Nightlife** (296): Nightclubs, bars, lounges
  - 16 nightclubs (XS, Hakkasan, Zouk, EBC, etc.)
  - 274 bars/lounges across 58 properties
  - 6 original curated speakeasies (The Laundry Room, Herbs & Rye, etc.)
- **Shows/Entertainment** (90): Resident shows, Cirque du Soleil, comedy, music
  - 72 enriched with property mappings from SmarterVegas
  - Covers residencies, magic shows, comedy clubs, tribute acts
- **Attractions** (86): Experiences, museums, thrill rides, golf
  - 32 off-strip attractions (AREA15, Neon Museum, etc.)
  - 54 on-property attractions
- **Shopping** (4): Forum Shops, Grand Canal Shoppes, Crystals, Miracle Mile

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
├── pois                 # 994 POIs with spatial indexing
├── properties           # 63 casino/hotel properties (Strip, Downtown, Off-Strip)
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

### Phase 2: Interactive Web Demo ✅ COMPLETE

**Live Demo**: http://3.140.78.15:8888/

**Flask Web Application** (`demo/`):
- Interactive Leaflet.js map of the Las Vegas Strip
- 994 POIs rendered as color-coded markers by category
- Category filter buttons (Restaurant, Shopping, Entertainment, Nightlife, Attraction)
- Click-to-view detail panel with full POI information
- "Recommended Spots" sidebar panel showcasing speakeasies & hidden gems
- Route navigation panel with walk/rideshare cost estimates
- "Find Nearby" geolocation-based POI discovery
- Responsive dark-themed UI

**Backend** (`demo/app.py` - 750 lines):
- Flask REST API with 10+ endpoints
- `/api/pois` - All POIs with optional category filter
- `/api/pois/recommended` - Curated recommended spots (tagged)
- `/api/pois/<id>` - Single POI detail
- `/api/pois/nearby` - Proximity search with distance
- `/api/route` - Route calculation with walk/rideshare breakdown
- `/api/properties` - Casino property data
- `/api/walkable-pairs` - Walkable POI pairs within threshold
- Connection pooling with retry logic and lazy initialization
- Custom JSON provider for Decimal serialization

**Frontend** (`demo/static/`):
- `js/map.js` - Leaflet map with category-colored markers, highlight animations
- `js/sidebar.js` - Category filters, detail panel, recommended spots cards
- `js/navigate.js` - Route display with polylines and step markers
- `js/api.js` - API client module
- `js/app.js` - Application initialization
- `css/style.css` - Dark theme, responsive panels, card styles

**Deployment** (`deploy.sh`):
- Automated EC2 deployment script (Ubuntu/Debian)
- Installs PostGIS, creates database/user, imports POI data
- Sets up Python venv with gunicorn (port 5050)
- Configures systemd service with auto-restart
- Nginx reverse proxy on port 8888
- Environment file with generated DB password

**Infrastructure**:
- EC2 instance (3.140.78.15) running Ubuntu
- PostgreSQL 16 + PostGIS 3.4 (local)
- gunicorn WSGI server (2 workers, 30s timeout)
- Nginx reverse proxy with static file caching
- systemd service management
- ufw firewall (ports 22, 8888)

**Phase 2.5: Massive POI Expansion** (945 new POIs):
- Web scraping pipeline built (`scripts/scrape_pois.py`)
- Scraped SmarterVegas.com for 580+ restaurants, 310 nightlife venues, 88 shows, 86 attractions
- Enrichment script (`scripts/enrich_pois.py`) for property detection and metadata
- Nightlife property mapping via listing page structure (by-property section headers)
- Property name normalization across all POIs
- Database schema updated: 63 properties, subcategory changed to VARCHAR(100)

---

## Technology Stack

### Current (Implemented)
- **Database**: PostgreSQL 16 + PostGIS 3.4
- **Backend**: Python Flask + gunicorn WSGI
- **Frontend**: Leaflet.js interactive map, vanilla JS
- **Deployment**: EC2 + Nginx + systemd
- **Container Orchestration**: Kubernetes / Docker Compose (local dev)
- **Data Format**: JSON, GeoJSON
- **Scripting**: Python 3.x
- **Spatial Queries**: PostGIS geography/geometry
- **Connection Management**: psycopg2 connection pooling with retry logic

### Planned
- **Mobile App**: React Native (iOS/Android)
- **3D Visualization**: Three.js / React Three Fiber
- **Outdoor Navigation**: Google Maps API
- **Indoor Positioning**: Bluetooth beacons / WiFi triangulation
- **ML/Pathfinding**: A* algorithm, Dijkstra, or ML-based routing
- **SSL/HTTPS**: Let's Encrypt for production

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
│   │   ├── restaurants/      # 518 restaurant POI JSON files
│   │   ├── shopping/         # 4 shopping center JSON files
│   │   ├── shows/            # 90 show/entertainment JSON files
│   │   ├── attractions/      # 86 attraction JSON files
│   │   ├── nightlife/        # 6 original curated nightlife POIs
│   │   │   ├── bars/         # 274 bar/lounge JSON files
│   │   │   └── nightclubs/   # 16 nightclub JSON files
│   │   ├── MGM_RESORTS_RESTAURANTS_SUMMARY.md
│   │   └── POI_COLLECTION_SUMMARY.md
│   ├── LAS_VEGAS_DATA_TRACKING.csv
│   └── OSM_DATA_SUMMARY.md
├── demo/                     # Interactive web demo (Flask)
│   ├── app.py                # Flask backend (750 lines, 10+ API endpoints)
│   ├── config.py             # DB, map, navigation, rideshare config
│   ├── db.py                 # Connection pooling with retry logic
│   ├── requirements.txt      # flask, gunicorn, psycopg2-binary
│   ├── templates/
│   │   └── index.html        # Main page with Leaflet map
│   └── static/
│       ├── css/style.css     # Dark theme, responsive panels
│       └── js/
│           ├── api.js        # API client module
│           ├── app.js        # Application initialization
│           ├── map.js        # Leaflet map, markers, highlights
│           ├── navigate.js   # Route display with polylines
│           └── sidebar.js    # Filters, detail panel, recommendations
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
│   ├── scrape_pois.py        # SmarterVegas.com scraper (restaurants, shows, nightlife, attractions)
│   ├── enrich_pois.py        # POI enrichment (property mapping, descriptions, metadata)
│   ├── import_pois.py        # Import POIs to PostgreSQL (recursive subdirectory walk)
│   ├── generate_synthetic_routes.py  # Generate navigation data
│   ├── bulk_collect_pois.js  # Yelp API bulk collection (not used - paid)
│   └── README.md
├── deploy.sh                 # Automated EC2 deployment script
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

### Option A: Deploy to EC2 (Production)
```bash
# On EC2 instance (Ubuntu/Debian with PostgreSQL + Nginx)
git clone https://github.com/SophistryDude/Sin_City_Travels.git
cd Sin_City_Travels
chmod +x deploy.sh
sudo ./deploy.sh
```
The script handles everything: PostGIS install, DB setup, POI import, venv creation, systemd service, and Nginx config. App will be at `http://<your-ec2-ip>:8888/`.

### Option B: Local Development
```bash
# 1. Start PostgreSQL + PostGIS
cd sin-city-travels
docker-compose up -d

# 2. Import POI data
pip install psycopg2-binary
python scripts/import_pois.py

# 3. Generate synthetic navigation data
pip install numpy
python scripts/generate_synthetic_routes.py

# 4. Run the Flask demo app
cd demo
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

**Database Access**:
- PostgreSQL: `localhost:5432`
- Database: `sincitytravels`
- User: `scapp`
- Password: `changeme_in_production`
- PGAdmin: `http://localhost:5050` (admin@sincity.local / admin)

### Query Examples
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

### Phase 3: Enhanced Navigation

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

#### D. Production Hardening
- SSL/HTTPS via Let's Encrypt
- Domain name setup
- Database backups (pg_dump cron)
- Monitoring and alerting
- Rate limiting on API endpoints

### Phase 4: 3D Visualization
- 3D models of casino interiors (Three.js)
- Augmented reality navigation
- Real-time positioning (Bluetooth beacons)

### Phase 5: Expansion
- ~~Cover all 31+ Strip properties~~ ✅ (36 Strip properties now covered)
- ~~Add Downtown Las Vegas~~ ✅ (7 Downtown properties)
- ~~Off-strip attractions~~ ✅ (20 Off-Strip properties)
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
- Contributing guidelines
- User manual

---

## Team & Contributors

**Project Lead**: SophistryDude
**AI Assistants**: Claude Sonnet 4.5 (Phase 1), Claude Opus 4.5 (Phase 2)

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
| Feb 4, 2026 | Interactive web demo built (Flask + Leaflet.js) |
| Feb 4, 2026 | Nightlife POIs added (6 speakeasies/bars) |
| Feb 4, 2026 | Recommended Spots feature implemented |
| Feb 4, 2026 | EC2 deployment (deploy.sh + Nginx + systemd) |
| Feb 4, 2026 | Live demo at http://3.140.78.15:8888/ |
| Feb 4, 2026 | POI expansion: 49 → 994 POIs via SmarterVegas scraping |
| Feb 4, 2026 | Property expansion: 9 → 63 properties (Strip + Downtown + Off-Strip) |
| Feb 4, 2026 | Walking directions reviewed for all 63 properties |
| **TBD** | Google Maps API integration |
| **TBD** | ML pathfinding model training |
| **TBD** | Mobile app MVP |
| **TBD** | Public beta |

---

## Contact & Links

- **GitHub**: https://github.com/SophistryDude/Sin_City_Travels
- **Live Demo**: http://3.140.78.15:8888/
- **Database**: PostgreSQL 16 + PostGIS 3.4
- **POIs**: 994 (518 restaurants, 296 nightlife, 90 shows, 86 attractions, 4 shopping)
- **Properties**: 63 (36 Strip, 7 Downtown, 20 Off-Strip)
- **Floor Plans**: 31 casinos (7.3 MB PDFs)

---

**Last Updated**: February 4, 2026
**Version**: 2.5 (Phase 2.5 - POI Expansion: 994 POIs across 63 properties)
