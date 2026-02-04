# Data Collection Plan - Las Vegas Attractions & Indoor Maps

**Goal**: Build a comprehensive database of Las Vegas attractions with indoor maps and 3D models.

---

## Phase 1: Attraction Database

### Major Las Vegas Strip Properties (Priority 1)

**North Strip:**
1. The STRAT Hotel, Casino & Tower
2. Circus Circus Las Vegas
3. Wynn Las Vegas
4. Encore at Wynn Las Vegas
5. The Venetian Resort
6. The Palazzo at The Venetian

**Central Strip:**
7. Treasure Island (TI)
8. The Mirage
9. Harrah's Las Vegas
10. The LINQ Hotel + Experience
11. Flamingo Las Vegas
12. Caesars Palace
13. The Cromwell
14. Bellagio
15. Paris Las Vegas
16. Bally's Las Vegas
17. Planet Hollywood Resort & Casino

**South Strip:**
18. The Cosmopolitan of Las Vegas
19. Aria Resort & Casino
20. Vdara Hotel & Spa
21. Park MGM
22. New York-New York Hotel & Casino
23. MGM Grand Las Vegas
24. Tropicana Las Vegas
25. Excalibur Hotel & Casino
26. Luxor Hotel and Casino
27. Mandalay Bay Resort and Casino

**Off-Strip (Priority 2):**
28. The Palms Casino Resort
29. Rio All-Suite Hotel & Casino
30. Orleans Hotel & Casino
31. Red Rock Casino Resort & Spa
32. Virgin Hotels Las Vegas
33. Resorts World Las Vegas

**Downtown Las Vegas (Priority 2):**
34. Golden Nugget Las Vegas
35. The D Las Vegas
36. Fremont Hotel & Casino
37. Four Queens Hotel and Casino
38. Golden Gate Hotel & Casino
39. Downtown Grand Hotel & Casino
40. Circa Resort & Casino

---

## Data Sources for Indoor Maps

### 1. OpenStreetMap (OSM)
**Status**: Free, Open Source
**Coverage**: Basic building outlines, some indoor mapping

**How to Access**:
- Download OSM data for Las Vegas: https://www.openstreetmap.org/
- Use Overpass API for querying specific buildings
- Check for indoor mapping tags (`level`, `room`, `indoor=yes`)

**Tools**:
- JOSM (Java OpenStreetMap Editor)
- OverpassTurbo (web-based query tool)
- OSM2World (3D visualization)

**Action Items**:
- [ ] Download Las Vegas OSM data
- [ ] Query for buildings with `tourism=hotel` and `amenity=casino`
- [ ] Extract indoor mapping data (if available)
- [ ] Contribute back to OSM with missing data

---

### 2. Google Maps / Google Earth

**Status**: Proprietary, some API access
**Coverage**: Excellent outdoor, limited indoor

**Google Indoor Maps**:
- Some casinos have Google Indoor Maps
- Check: Google Maps → Search casino → "View Indoor Maps" (if available)
- Major properties like MGM Grand, Caesars Palace may have floor plans

**Google Earth Pro**:
- Free desktop app with 3D building models
- Useful for outdoor context and building footprints

**Action Items**:
- [ ] Survey which casinos have Google Indoor Maps
- [ ] Document coverage gaps
- [ ] Extract building footprints from Google Earth

---

### 3. Mapbox / Here Maps

**Status**: Commercial API, some free tier
**Coverage**: Building data, possible indoor maps

**Mapbox**:
- Excellent vector maps and 3D terrain
- Supports custom indoor mapping layers
- Can import GeoJSON floor plans

**Action Items**:
- [ ] Sign up for Mapbox free tier
- [ ] Check for existing Las Vegas indoor data
- [ ] Plan custom layer integration

---

### 4. Official Casino/Hotel Floor Plans

**Status**: Publicly available (limited), request from properties
**Coverage**: Varies by property

**Public Sources**:
- Hotel/casino websites (often have simplified maps)
- Convention center floor plans (for meeting spaces)
- Fire safety diagrams (sometimes accessible)

**Request Process**:
1. Contact property marketing/PR departments
2. Request floor plans for "accessibility app development"
3. Offer to credit their property and drive foot traffic

**Action Items**:
- [ ] Identify which casinos publish floor plans online
- [ ] Draft request email template for property management
- [ ] Track responses and permissions

---

### 5. Crowdsourced Data

**Status**: User-generated, accuracy varies
**Coverage**: Gaps filled by community

**MappedIn**:
- Indoor mapping platform, some Las Vegas venues

**Foursquare / Yelp**:
- Amenity locations (restaurants, shops) inside casinos
- Can be used to validate floor plan accuracy

**Reddit / TripAdvisor**:
- User-submitted maps and directions
- Verify with ground truth

**Action Items**:
- [ ] Scrape Yelp/Foursquare for POIs inside casinos
- [ ] Cross-reference with official maps
- [ ] Implement user correction system in app

---

### 6. Photogrammetry & LiDAR (Advanced)

**Status**: DIY, requires on-site access
**Coverage**: High precision, labor-intensive

**Photogrammetry**:
- Take 100-500 photos of casino interior
- Use software (Reality Capture, Meshroom, Polycam) to generate 3D model
- Extract floor plan from model

**LiDAR Scanning**:
- iPhone 12 Pro+ has LiDAR sensor
- Apps: Polycam, SiteScape, Canvas
- Generate point cloud → mesh → floor plan

**Legal Considerations**:
- Check casino photography policies
- Many casinos restrict photos on casino floor
- Focus on public areas (lobbies, hallways, shops)

**Action Items**:
- [ ] Research casino photo policies
- [ ] Test photogrammetry on public areas (hotel lobbies)
- [ ] Evaluate LiDAR scanning apps

---

### 7. Computer-Aided Design (CAD) Files

**Status**: Industry-standard, rarely public
**Coverage**: Architectural blueprints (if obtainable)

**Autodesk Revit / AutoCAD**:
- Professional architectural plans
- May be available from architects/contractors

**Possible Sources**:
- Clark County Building Department (permit records)
- Architectural firms (with permission)
- Property management companies

**Action Items**:
- [ ] Check Clark County records for public building plans
- [ ] Research FOIA requests for casino blueprints
- [ ] Contact architectural firms (long shot)

---

## Data Processing Pipeline

### Step 1: Raw Data Collection
- Download OSM data, Google Maps screenshots, official PDFs
- Organize by property in `data/attractions/[property-name]/`

### Step 2: Georeferencing
- Align floor plans to real-world coordinates (lat/long)
- Use QGIS or similar GIS software
- Match to building footprints from OSM/Google Earth

### Step 3: Vectorization
- Convert raster images (PDFs, photos) to vector format
- Trace walls, doors, amenities in QGIS or Illustrator
- Export as GeoJSON or SVG

### Step 4: Metadata Enrichment
- Tag rooms with types (casino floor, restaurant, restroom, etc.)
- Add POIs (slot machines, table games, shops)
- Note accessibility features (elevators, ramps)

### Step 5: 3D Modeling (Phase 3)
- Create low-poly 3D models in Blender
- Texture with photos (if available)
- Optimize for mobile rendering

### Step 6: Database Import
- Load into PostgreSQL + PostGIS
- Create spatial indexes
- Set up API endpoints for mobile app

---

## Immediate Next Steps

### Week 1: Survey & Download
1. Download OpenStreetMap data for Las Vegas
2. Survey Google Indoor Maps coverage
3. Scrape casino websites for publicly available floor plans
4. Create spreadsheet tracking data availability per property

### Week 2: Pilot Property
1. Select 1-2 casinos with best data availability
2. Compile all available data (OSM, Google, website)
3. Georeference and vectorize floor plan
4. Test indoor navigation pathfinding algorithm

### Week 3: Documentation & Tools
1. Document data pipeline in detail
2. Set up QGIS project template
3. Create scripts for automated data processing
4. Build proof-of-concept web viewer

---

## Tools & Software

**GIS & Mapping**:
- QGIS (free, open-source GIS software)
- PostGIS (PostgreSQL geospatial extension)
- Mapbox Studio (custom map styling)
- Leaflet / Mapbox GL JS (web mapping libraries)

**3D Modeling**:
- Blender (3D modeling and rendering)
- SketchUp (architectural modeling)
- Polycam / Scaniverse (LiDAR scanning apps)
- Meshroom (photogrammetry, free)

**Data Processing**:
- Python (scripting, data wrangling)
- GDAL/OGR (geospatial data conversion)
- OpenStreetMap editing tools (JOSM, iD editor)

**Mobile Development**:
- React Native (cross-platform app)
- Mapbox Navigation SDK (turn-by-turn)
- Three.js / React Three Fiber (3D rendering)

---

## Budget Estimate (Minimal Viable)

| Item | Cost | Notes |
|------|------|-------|
| Mapbox API (free tier) | $0 | 50k map loads/month |
| Google Maps API (testing) | $200-500/mo | After free tier |
| Polycam Pro (LiDAR scanning) | $10/mo | For photogrammetry |
| Web hosting | $10-20/mo | Digital Ocean / AWS |
| **Total (MVP)** | **$20-50/mo** | Before scaling |

**Advanced** (with premium data):
- MappedIn or similar indoor mapping platform: $500-2000/mo
- Paid floor plan data: $5k-20k one-time
- Professional 3D scanning services: $1k-5k per casino

---

## Legal & Ethical Considerations

1. **Copyright**: Respect intellectual property of floor plans
2. **Photography**: Follow casino photo policies (no casino floor photos)
3. **Privacy**: Don't collect personal data without consent
4. **Terms of Service**: Comply with Google/Mapbox ToS
5. **Accessibility**: Ensure data benefits users with disabilities

---

## Success Metrics (Phase 1)

- [ ] Database of 40+ Las Vegas properties with basic info
- [ ] Indoor maps for 5-10 major Strip casinos
- [ ] 1-2 casinos with detailed 3D models
- [ ] Pathfinding algorithm working in test environment
- [ ] Proof-of-concept mobile app demo

---

**Last Updated**: February 3, 2026
**Next Review**: After Week 3 pilot completion
