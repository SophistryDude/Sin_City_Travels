# POI Collection Plan - Restaurants, Shops & Attractions

**Goal**: Build comprehensive database of Points of Interest (POIs) inside and around Las Vegas casinos

---

## POI Categories

### 1. Restaurants & Dining 🍴

**Examples**:
- Golden Steer Steakhouse (legendary steakhouse, est. 1958)
- Gordon Ramsay Hell's Kitchen (Caesars Palace)
- Joel Robuchon (MGM Grand)
- é by José Andrés (Cosmopolitan)
- Joe's Seafood (Forum Shops)

**Data to Collect**:
- Name
- Type (Fine Dining, Casual, Buffet, Food Court, Bar)
- Location (Casino property, floor/level)
- Cuisine type
- Price range ($-$$$$)
- Hours of operation
- Geographic coordinates (lat/long)

**Sources**:
- Yelp API
- Google Places API
- Foursquare/Swarm API
- OpenStreetMap (some data)
- Casino websites (official menus/directories)

---

### 2. Shopping 🛍️

**Examples**:
- Forum Shops at Caesars (240+ stores)
- Grand Canal Shoppes at Venetian (160+ stores)
- Miracle Mile Shops at Planet Hollywood (170+ stores)
- Crystals at CityCenter (luxury brands)
- The Shops at Aria

**Data to Collect**:
- Store name
- Category (Luxury, Clothing, Jewelry, Souvenirs, etc.)
- Location (casino property, floor/level)
- Brand (Gucci, Louis Vuitton, etc.)
- Hours of operation

**Sources**:
- Mall directories (official websites)
- OpenStreetMap
- Yelp/Google Places

---

### 3. Shows & Entertainment 🎭

**Examples**:
- Cirque du Soleil shows (O, Mystère, KÀ, LOVE, Michael Jackson ONE, etc.)
- Colosseum at Caesars (concert venue)
- MGM Grand Garden Arena
- Park Theater at Park MGM
- Allegiant Stadium (Raiders, concerts)

**Data to Collect**:
- Venue name
- Type (Theater, Arena, Lounge, Nightclub)
- Capacity
- Current shows/performers
- Location

**Sources**:
- Ticketmaster/AXS
- Casino event calendars
- OpenStreetMap

---

### 4. Attractions & Activities 🎢

**Examples**:
- High Roller (observation wheel, 550 ft tall)
- Eiffel Tower Experience (Paris Las Vegas, half-scale replica)
- Gondola Rides (Venetian)
- Shark Reef Aquarium (Mandalay Bay)
- Fremont Street Experience (Downtown)
- SlotZilla Zipline (Fremont Street)
- Fly LINQ Zipline

**Data to Collect**:
- Attraction name
- Type (Observation deck, Ride, Museum, Aquarium, etc.)
- Location
- Ticket prices
- Hours

**Sources**:
- TripAdvisor
- Official attraction websites
- OpenStreetMap

---

### 5. Nightlife 🍸

**Examples**:
- Omnia (Caesars Palace)
- XS (Encore)
- Hakkasan (MGM Grand)
- Marquee (Cosmopolitan)
- Drai's (Cromwell)
- On The Record (Park MGM)

**Data to Collect**:
- Club/Bar name
- Type (Nightclub, Dayclub, Lounge, Rooftop Bar)
- Location
- Cover charge
- Dress code
- DJ lineup

**Sources**:
- Yelp
- Vegas club websites
- Eventbrite/Dice

---

### 6. Pools & Spas 🏊

**Examples**:
- Encore Beach Club (dayclub + pool)
- Garden of the Gods Pool Oasis (Caesars)
- Mandalay Bay Beach (wave pool)
- Marquee Dayclub (Cosmopolitan)
- Qua Baths & Spa (Caesars)
- Canyon Ranch Spa (Venetian/Palazzo)

**Data to Collect**:
- Pool/Spa name
- Type (Dayclub, Pool complex, Spa, Beach)
- Location
- Amenities
- Hours (seasonal)

---

### 7. Convention & Meeting Spaces 🏢

**Examples**:
- Las Vegas Convention Center (3.2M sq ft)
- Sands Expo (Venetian)
- Mandalay Bay Convention Center
- MGM Grand Conference Center
- Caesars Forum Convention Center

**Data to Collect**:
- Venue name
- Square footage
- Number of rooms
- Capacity
- Location

---

## Data Collection Methods

### Method 1: Yelp API

**API**: Yelp Fusion API (free tier: 5,000 requests/day)

**How to Use**:
```bash
# Search for restaurants in Las Vegas
curl -X GET "https://api.yelp.com/v3/businesses/search?location=Las%20Vegas&categories=restaurants&limit=50" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Pros**:
- Rich data (ratings, reviews, photos, hours)
- Free tier available
- Well-documented API

**Cons**:
- Rate limits (5K requests/day on free tier)
- May not have all indoor locations

**Action Items**:
- [ ] Sign up for Yelp Developer account
- [ ] Get API key
- [ ] Test search for "Golden Steer" specifically
- [ ] Bulk search for restaurants near each casino

---

### Method 2: Google Places API

**API**: Google Places API (paid, $17 per 1,000 requests after free tier)

**Free Tier**: $200/month credit (~11,750 requests)

**How to Use**:
```javascript
// Search for places near a location
const response = await fetch(
  `https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=${lat},${lng}&radius=500&type=restaurant&key=${API_KEY}`
);
```

**Pros**:
- Most comprehensive POI data
- Excellent accuracy
- Indoor mapping data for some casinos

**Cons**:
- Costs money after free tier
- Complex pricing structure

**Action Items**:
- [ ] Enable Google Places API in GCP
- [ ] Set up billing (with budget alerts)
- [ ] Test queries for casino POIs

---

### Method 3: Foursquare Places API

**API**: Foursquare Places API (free tier: 99,000 requests/month)

**How to Use**:
```bash
curl "https://api.foursquare.com/v3/places/search?ll=36.1215,-115.1739&radius=1000&categories=13065" \
  -H "Authorization: YOUR_API_KEY"
```

**Pros**:
- Very generous free tier
- Good POI categorization
- User tips and ratings

**Cons**:
- Less comprehensive than Google
- Some data quality issues

**Action Items**:
- [ ] Sign up for Foursquare Developer account
- [ ] Get API key
- [ ] Test search for Las Vegas POIs

---

### Method 4: OpenStreetMap

**Source**: Already have OSM data downloaded!

**POIs in OSM**:
```bash
# Query for restaurants
[out:json];
(
  node["amenity"="restaurant"](36.091,-115.177,36.157,-115.154);
  way["amenity"="restaurant"](36.091,-115.177,36.157,-115.154);
);
out body;
```

**Pros**:
- Free, open data
- Already have it
- Community-maintained

**Cons**:
- Incomplete coverage (especially indoors)
- Data quality varies

**Action Items**:
- [ ] Parse existing OSM data for POIs
- [ ] Extract restaurants, shops, attractions
- [ ] Cross-reference with Yelp/Google data

---

### Method 5: Web Scraping Casino Websites

**Target Sites**:
- Caesars.com (dining directory)
- MGMResorts.com (restaurant listings)
- Wynnlasvegas.com (dining & entertainment)
- Venetian.com (directory)

**Tools**:
- Python + BeautifulSoup
- Selenium (for JavaScript-heavy sites)
- Scrapy (for large-scale scraping)

**Legal Considerations**:
- Check robots.txt
- Respect rate limits
- Use only publicly available data

**Action Items**:
- [ ] Identify casino directory pages
- [ ] Write Python scraper for MGM properties
- [ ] Write scraper for Caesars Entertainment properties
- [ ] Parse HTML into structured POI data

---

## POI Database Schema

### PostgreSQL Table: `pois`

```sql
CREATE TABLE pois (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,  -- restaurant, shop, attraction, etc.
    subcategory VARCHAR(100),       -- fine_dining, luxury_retail, etc.
    casino_property VARCHAR(100),   -- Which casino (if inside one)
    level VARCHAR(20),               -- Floor/level (e.g., "1", "2", "Basement")
    location GEOGRAPHY(POINT),      -- PostGIS point (lat/long)
    address VARCHAR(255),
    phone VARCHAR(20),
    website VARCHAR(255),
    hours JSONB,                     -- Operating hours as JSON
    price_range VARCHAR(10),         -- $, $$, $$$, $$$$
    rating DECIMAL(2,1),             -- Average rating (0-5)
    rating_count INTEGER,            -- Number of ratings
    yelp_id VARCHAR(50),
    google_place_id VARCHAR(100),
    foursquare_id VARCHAR(50),
    osm_id BIGINT,
    description TEXT,
    tags JSONB,                      -- Flexible tags/metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON pois USING GIST(location);
CREATE INDEX ON pois(casino_property);
CREATE INDEX ON pois(category);
```

---

## Implementation Plan

### Week 1: API Setup & Testing
- [ ] Sign up for Yelp, Foursquare, Google Places APIs
- [ ] Get API keys and test authentication
- [ ] Query for "Golden Steer" specifically to verify
- [ ] Test bulk queries for top 5 casinos

### Week 2: Bulk Data Collection
- [ ] Parse OSM data for existing POIs
- [ ] Scrape casino websites for restaurant/shop directories
- [ ] Bulk query Yelp for all casinos (200-500 POIs/casino)
- [ ] Cross-reference and deduplicate data

### Week 3: Database Setup
- [ ] Set up PostgreSQL + PostGIS
- [ ] Create `pois` table with schema above
- [ ] Import POI data
- [ ] Add spatial indexes for fast queries

### Week 4: Manual Curation
- [ ] Review and correct duplicate entries
- [ ] Add missing famous POIs (Golden Steer, etc.)
- [ ] Verify locations on property maps
- [ ] Add floor/level information from PDFs

---

## Success Metrics

**Coverage Goals**:
- 50+ POIs per major casino (1,350+ total)
- All famous restaurants (Golden Steer, Joel Robuchon, etc.)
- All major shopping centers (Forum Shops, Grand Canal, etc.)
- All Cirque du Soleil venues
- All major nightclubs and pools

**Data Quality**:
- 95%+ have accurate coordinates
- 80%+ have floor/level information
- 90%+ have operating hours
- 70%+ have price range data

---

## Golden Steer Example

Let's test with the Golden Steer specifically:

**Golden Steer Steakhouse**:
- **Name**: Golden Steer Steakhouse
- **Category**: Restaurant
- **Subcategory**: Fine Dining, Steakhouse
- **Casino Property**: None (independent, off-Strip)
- **Address**: 308 W Sahara Ave, Las Vegas, NV 89102
- **Coordinates**: 36.1441°N, 115.1486°W
- **Hours**: Daily 4:30 PM - 10:30 PM
- **Price**: $$$$
- **Established**: 1958
- **Tags**: Historic, Classic Vegas, Steakhouse, Fine Dining

**Action**: Query Yelp API for this specific business:

```bash
curl "https://api.yelp.com/v3/businesses/search?term=Golden+Steer&location=Las+Vegas" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## Next Steps

1. **Immediate** (Today):
   - Sign up for Yelp API
   - Test query for Golden Steer
   - Parse existing OSM data for POIs

2. **Short-term** (This Week):
   - Set up Foursquare API
   - Scrape 3-5 casino websites for directories
   - Create POI database schema

3. **Medium-term** (Next Week):
   - Bulk import 500+ POIs
   - Set up database with PostGIS
   - Build POI search API endpoint

---

**Last Updated**: February 3, 2026
**Status**: Planning Phase
**Next Review**: After Week 1 data collection
