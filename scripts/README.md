# Sin City Travels - Scripts

Automation scripts for data collection and processing.

---

## Available Scripts

### `bulk_collect_pois.js`

Bulk collection script that queries Yelp Fusion API for restaurants, bars, shops, and attractions near all 31 Las Vegas casino properties.

**Prerequisites**:
1. Sign up for Yelp API: https://www.yelp.com/developers
2. Create `.env` file in project root with `YELP_API_KEY=your_key_here`
3. Install dependencies: `npm install dotenv`

**Usage**:
```bash
# Collect all restaurants
node scripts/bulk_collect_pois.js restaurants

# Collect bars and nightlife
node scripts/bulk_collect_pois.js bars

# Collect shopping venues
node scripts/bulk_collect_pois.js shopping

# Collect attractions
node scripts/bulk_collect_pois.js attractions

# Collect everything
node scripts/bulk_collect_pois.js all
```

**Features**:
- Queries 31 casino properties with 500m radius each
- Rate-limited to 200ms between requests (5 QPS max)
- Deduplicates businesses by Yelp ID
- Converts Yelp data to our POI JSON format
- Generates summary statistics
- Saves raw data to `data/pois/raw/`

**Expected Results**:
- **Restaurants**: 500-800 POIs
- **Bars/Nightlife**: 200-400 POIs
- **Shopping**: 100-300 POIs
- **Attractions**: 150-300 POIs
- **All**: 1,000-1,500 POIs

**Output**:
- Saves to: `data/pois/raw/yelp_{category}_{date}.json`
- Example: `data/pois/raw/yelp_restaurants_2026-02-03.json`

**API Rate Limits**:
- Yelp Free Tier: 5,000 API calls per day
- This script uses ~31 calls per category
- You can run it ~160 times per day (or collect 5 categories 32 times)

**Example Output**:
```
🎰 Starting bulk POI collection for category: restaurants

Querying 31 casino properties...

[1/31] Searching near Caesars Palace...
  ✓ Found 50 businesses (47 new)
[2/31] Searching near Bellagio...
  ✓ Found 50 businesses (38 new)
...

✅ Collection complete!
Total unique POIs collected: 687

💾 Saved 687 POIs to: yelp_restaurants_2026-02-03.json

📊 Summary Statistics:

By Category:
  - restaurant: 687

Top 10 Casinos by POI count:
  - Caesars Palace: 45
  - Bellagio: 42
  - MGM Grand: 41
  ...

Average Yelp Rating: 4.2/5.0

Price Range Distribution:
  - $: 89
  - $$: 312
  - $$$: 198
  - $$$$: 88
```

---

## Future Scripts

### `query_yelp.js` (Planned)
Single POI lookup by name or ID

### `enrich_pois.js` (Planned)
Enrich POI data with additional sources (Google Places, Foursquare)

### `georeference_maps.js` (Planned)
Georeference PDF floor plans to real-world coordinates

### `vectorize_maps.js` (Planned)
Convert raster floor plans to vector format

### `generate_routing_graph.js` (Planned)
Generate indoor routing nodes and edges from floor plans

---

## Development

**Installing Dependencies**:
```bash
npm install dotenv
```

**Environment Variables**:
Create a `.env` file in project root:
```bash
YELP_API_KEY=your_yelp_api_key_here
GOOGLE_PLACES_API_KEY=your_google_api_key_here
FOURSQUARE_API_KEY=your_foursquare_api_key_here
```

**Testing**:
```bash
# Test with a single casino (modify script to limit casinos array)
node scripts/bulk_collect_pois.js restaurants
```

---

## API Documentation

- **Yelp Fusion API**: https://docs.developer.yelp.com/
- **Google Places API**: https://developers.google.com/maps/documentation/places
- **Foursquare Places API**: https://location.foursquare.com/developer/

---

**Created**: February 3, 2026
**Last Updated**: February 3, 2026
