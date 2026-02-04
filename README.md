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
- Collecting virtual maps and floor plans of Las Vegas properties
- Building database of attractions, hotels, and casinos
- Researching 3D mapping technologies

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

## Project Structure

```
sin-city-travels/
├── data/              # Raw data, maps, floor plans
│   ├── maps/          # Vector/raster maps
│   ├── attractions/   # Attraction metadata
│   └── hotels/        # Hotel/casino data
├── frontend/          # Mobile app (React Native)
├── backend/           # API server
├── models/            # 3D models and assets
└── docs/              # Documentation
```

## Roadmap

### Phase 1: Data Collection (Current)
- [ ] Compile list of all major Las Vegas properties
- [ ] Collect publicly available floor plans and maps
- [ ] Research indoor mapping APIs and SDKs
- [ ] Evaluate 3D modeling options

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

TBD

## Contact

Project Lead: [Your Name]
