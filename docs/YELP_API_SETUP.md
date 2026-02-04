# Yelp API Setup Guide

**Goal**: Set up Yelp Fusion API to query for restaurants, bars, and attractions in Las Vegas

---

## Step 1: Sign Up for Yelp Developer Account

1. Go to https://www.yelp.com/developers
2. Click **"Get Started"** or **"Create App"**
3. Log in with your Yelp account (or create one)
4. Accept the API Terms of Service

---

## Step 2: Create an App

1. Navigate to: https://www.yelp.com/developers/v3/manage_app
2. Fill out the form:
   - **App Name**: `Sin City Travels POI Collector`
   - **Industry**: Travel & Tourism
   - **Company**: (Your name or company)
   - **Website**: https://github.com/SophistryDude/Sin_City_Travels
   - **Description**: Indoor navigation app for Las Vegas casinos and attractions
   - **Country**: United States

3. Click **"Create New App"**

---

## Step 3: Get Your API Key

Once your app is created:

1. You'll see your **API Key** displayed (long string like `abc123...xyz`)
2. **IMPORTANT**: Copy this key immediately
3. **DO NOT** commit this key to Git!

**Save it securely**:
```bash
# Create a .env file (already in .gitignore)
echo "YELP_API_KEY=your_key_here" > ../../.env
```

---

## Step 4: Test the API

### Test with cURL:

```bash
curl -X GET "https://api.yelp.com/v3/businesses/search?term=Golden+Steer&location=Las+Vegas" \
  -H "Authorization: Bearer YOUR_API_KEY_HERE"
```

**Expected Response**:
```json
{
  "businesses": [
    {
      "id": "golden-steer-steakhouse-las-vegas",
      "name": "Golden Steer Steakhouse Las Vegas",
      "rating": 4.5,
      "review_count": 2810,
      "coordinates": {
        "latitude": 36.1441,
        "longitude": -115.1486
      },
      "location": {
        "address1": "308 W Sahara Ave"
      },
      "price": "$$$$",
      ...
    }
  ]
}
```

---

## Step 5: Node.js Integration

Create a Yelp query script:

**File**: `scripts/query_yelp.js`

```javascript
const https = require('https');
require('dotenv').config(); // Load .env file

const YELP_API_KEY = process.env.YELP_API_KEY;

function searchYelp(term, location, categories = 'restaurants') {
    return new Promise((resolve, reject) => {
        const params = new URLSearchParams({
            term: term,
            location: location,
            categories: categories,
            limit: 50
        });

        const options = {
            hostname: 'api.yelp.com',
            path: `/v3/businesses/search?${params}`,
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${YELP_API_KEY}`
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                if (res.statusCode === 200) {
                    resolve(JSON.parse(data));
                } else {
                    reject(new Error(`API returned ${res.statusCode}: ${data}`));
                }
            });
        });

        req.on('error', reject);
        req.end();
    });
}

// Example usage
async function main() {
    try {
        const results = await searchYelp('Golden Steer', 'Las Vegas, NV', 'steakhouses');
        console.log('Found', results.businesses.length, 'businesses');

        results.businesses.forEach(biz => {
            console.log(`\n${biz.name}`);
            console.log(`  Rating: ${biz.rating} (${biz.review_count} reviews)`);
            console.log(`  Price: ${biz.price || 'N/A'}`);
            console.log(`  Address: ${biz.location.address1}`);
            console.log(`  Coordinates: ${biz.coordinates.latitude}, ${biz.coordinates.longitude}`);
        });
    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();
```

**Run it**:
```bash
node scripts/query_yelp.js
```

---

## Step 6: Bulk Collection Strategy

### Query all casinos for nearby restaurants:

```javascript
const casinos = [
    { name: 'Bellagio', lat: 36.1127, lng: -115.1765 },
    { name: 'Caesars Palace', lat: 36.1162, lng: -115.1744 },
    { name: 'MGM Grand', lat: 36.1024, lng: -115.1698 },
    // ... add all 31 casinos
];

async function collectAllPOIs() {
    const allPOIs = [];

    for (const casino of casinos) {
        console.log(`Searching near ${casino.name}...`);

        // Search for restaurants
        const restaurants = await searchNearby(casino.lat, casino.lng, 'restaurants', 500);

        // Search for bars/nightlife
        const bars = await searchNearby(casino.lat, casino.lng, 'bars,nightlife', 500);

        // Search for shopping
        const shops = await searchNearby(casino.lat, casino.lng, 'shopping', 500);

        allPOIs.push(...restaurants, ...bars, ...shops);

        // Rate limit: 5000 requests/day, so pause between queries
        await sleep(1000); // 1 second between requests
    }

    // Deduplicate by Yelp ID
    const unique = [...new Map(allPOIs.map(poi => [poi.id, poi])).values()];

    console.log(`Collected ${unique.length} unique POIs`);
    return unique;
}

function searchNearby(lat, lng, categories, radius = 500) {
    return new Promise((resolve, reject) => {
        const params = new URLSearchParams({
            latitude: lat,
            longitude: lng,
            categories: categories,
            radius: radius,
            limit: 50
        });

        // ... same as searchYelp but with lat/lng
    });
}
```

---

## Yelp API Limits & Best Practices

### Free Tier Limits:
- **5,000 API calls per day**
- **25,000 API calls per year** (technically, but resets daily)

### Rate Limiting:
- **5 queries per second (QPS)** maximum
- Add `sleep(200)` between requests to be safe

### Best Practices:
1. **Cache results** - Don't re-query the same data
2. **Batch queries** - Group by location to minimize API calls
3. **Use categories** - Narrow searches with category filters
4. **Monitor usage** - Track API call count

### API Call Budget:

| Task | Calls | Strategy |
|------|-------|----------|
| 31 casinos × 3 categories | 93 | Query restaurants, bars, shops near each casino |
| Unique POI details | ~500 | Get full details for each unique POI |
| **Total** | ~600 | Well under 5K daily limit |

---

## Alternative: Foursquare API

If Yelp limits are too restrictive, Foursquare offers:
- **99,000 requests/month** (free tier)
- Similar data quality
- Fewer reviews/ratings than Yelp

**Setup**: https://location.foursquare.com/developer/

---

## Data Storage

Save results to JSON files:

```javascript
const fs = require('fs');

function savePOIs(pois, filename) {
    fs.writeFileSync(
        `data/pois/raw/${filename}.json`,
        JSON.stringify(pois, null, 2)
    );
    console.log(`Saved ${pois.length} POIs to ${filename}.json`);
}

// Usage
const restaurants = await collectAllPOIs();
savePOIs(restaurants, 'yelp_restaurants_2026-02-03');
```

---

## Next Steps

1. **Sign up** for Yelp API (5 minutes)
2. **Test** with Golden Steer query
3. **Run bulk collection** for all 31 casinos
4. **Deduplicate** and save to database
5. **Enrich** with data from Foursquare/Google Places

**Expected Result**: 500-1500 POIs with accurate coordinates, ratings, and details

---

**Created**: February 3, 2026
**API Docs**: https://docs.developer.yelp.com/
