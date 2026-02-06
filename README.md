# Sin City Travels

**Navigate Las Vegas Like a Pro**

An indoor navigation app for Las Vegas casinos, hotels, and attractions featuring 3D models, turn-by-turn directions, and integration with ride-sharing services.

## Overview

Sin City Travels helps visitors navigate the complex layouts of Las Vegas casinos and hotels with:
- **3D Indoor Maps**: Visualize casino layouts, hotel lobbies, and attraction interiors
- **Turn-by-Turn Directions**: Get guided navigation inside massive casino properties
- **Ride-Share Integration**: Seamless connection to Uber/Lyft for getting between properties
- **Attraction Database**: Comprehensive map of all Las Vegas hotels, casinos, and attractions

## Current Status

**Phase 1: Data Collection** (In Progress)
- ✅ Downloaded floor plans for 31 major casino properties (7.3 MB)
- ✅ Collected OpenStreetMap data for Las Vegas Strip (94 hotels, 36 casinos)
- ✅ Created POI collection infrastructure with Yelp API integration
- ✅ Collected restaurant POI data (37 POIs created across 8 major properties)
- 📋 Michelin-starred and celebrity chef restaurants documented
- 📋 Researching 3D mapping technologies

## Features (Planned)

### Core Features
- Indoor GPS navigation for major casino properties
- 3D visualization of building interiors
- Search and locate amenities (restaurants, shops, restrooms, exits)
- Save favorite locations and routes
- Accessibility features (elevator routes, wheelchair access)

### Integration Features
- Uber/Lyft pickup point recommendations
- Real-time crowd density (future)
- Event scheduling and venue navigation
- Multi-property route planning

## Technology Stack (Planned)

### Frontend
- React Native (iOS/Android)
- Three.js / React Three Fiber (3D visualization)
- Mapbox / Google Maps API (outdoor navigation)

### Backend
- Node.js / Python Flask
- PostgreSQL + PostGIS (geospatial data)
- Indoor positioning system (Bluetooth beacons / WiFi triangulation)

### Data Sources
- OpenStreetMap
- Official casino floor plans (where available)
- Photogrammetry / LiDAR scanning
- Crowdsourced mapping data

## Data Collection Progress

### Floor Plans & Maps
- **31 casino properties** with PDF floor plans downloaded
- **Tier 1**: Caesars Palace, Bellagio, MGM Grand, Aria (1.5MB - 133KB each)
- **Tier 2 & 3**: Venetian, Palazzo, Wynn, Cosmopolitan, and 23 more properties
- **Source**: SmarterVegas.com property maps

### OpenStreetMap Data
- **94 hotels** and **36 casinos** with building footprints
- Geographic coordinates for all major Strip properties
- Downloaded via Overpass API (523 KB GeoJSON)

### Points of Interest (POIs)
- **37 restaurant POIs** created with complete data across 8 major properties:
  - **MGM Grand** (3): Hakkasan (Michelin), Craftsteak, Morimoto
  - **Park MGM** (1): Bavette's Steakhouse
  - **Bellagio** (3): Picasso (AAA 5-Diamond), Spago, Le Cirque (AAA 5-Diamond)
  - **Caesars Palace** (5): Hell's Kitchen, Nobu, Guy Savoy (Michelin 2-star), Amalfi, Peter Luger
  - **Aria** (5): Carbone, Jean Georges Steakhouse, CATCH, Bardot Brasserie, Din Tai Fung
  - **The Venetian** (4): Bouchon, TAO, CARNEVINO, CUT
  - **The Cosmopolitan** (5): é by José Andrés, Zuma, Scarpetta, Momofuku, Jaleo
  - **Wynn/Encore** (5): Wing Lei (Michelin), SW Steakhouse, Mizumi, Delilah, Sinatra
  - **Mandalay Bay** (5): Orla, STRIPSTEAK, Kumi, Border Grill, Aureole
  - **Off-Strip** (1): Golden Steer Steakhouse

- **15+ celebrity chefs** featured: Wolfgang Puck, Gordon Ramsay, José Andrés, Bobby Flay, Thomas Keller, Michael Mina, David Chang, and more
- **3 Michelin-starred restaurants** documented
- **Alternative collection methods** implemented (web scraping + manual curation)

See [docs/](docs/) for detailed guides on Yelp API setup, POI collection plan, and data tracking.

## Project Structure

```
sin-city-travels/
├── data/
│   ├── maps/                    # Vector/raster maps (OSM data)
│   ├── attractions/             # Casino floor plans (31 properties)
│   ├── pois/
│   │   ├── restaurants/         # Restaurant POI JSON files
│   │   ├── shopping/            # Shopping venues
│   │   ├── shows/               # Entertainment venues
│   │   └── raw/                 # Bulk import raw data
│   └── LAS_VEGAS_DATA_TRACKING.csv
├── scripts/
│   ├── bulk_collect_pois.js     # Yelp API bulk collection
│   └── README.md                # Scripts documentation
├── docs/
│   ├── DATA_COLLECTION_PLAN.md
│   ├── YELP_API_SETUP.md
│   ├── POI_COLLECTION_PLAN.md
│   └── OSM_DATA_SUMMARY.md
├── frontend/                    # Mobile app (React Native)
├── backend/                     # API server
└── models/                      # 3D models and assets
```

## Roadmap

### Phase 1: Data Collection (Current)
- [x] Compile list of all major Las Vegas properties (40+ properties tracked)
- [x] Collect publicly available floor plans and maps (31 casinos, 32 PDFs)
- [x] Download OpenStreetMap data for Las Vegas Strip
- [x] Set up POI collection infrastructure (Yelp API integration)
- [x] Create POI JSON schema and sample data (8 restaurants)
- [ ] Bulk collect 500-1,500 POIs (restaurants, bars, shops, attractions)
- [ ] Research indoor mapping APIs and SDKs
- [ ] Evaluate 3D modeling options
- [ ] Georeference floor plans to real-world coordinates
- [ ] Vectorize floor plans (convert raster to vector)

### Phase 2: MVP Development
- [ ] Basic 2D indoor maps for 5-10 major casinos
- [ ] Simple navigation (point A to point B)
- [ ] Mobile app prototype (iOS/Android)
- [ ] Uber/Lyft API integration

### Phase 3: 3D Visualization
- [ ] 3D models of major casino interiors
- [ ] Augmented reality navigation
- [ ] Advanced pathfinding with accessibility options

### Phase 4: Expansion
- [ ] Cover all major Strip properties
- [ ] Downtown Las Vegas coverage
- [ ] Off-strip attractions
- [ ] User-generated content (reviews, photos)

## Getting Started

(Instructions for setup will be added as development progresses)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Project Lead: Nicholas
