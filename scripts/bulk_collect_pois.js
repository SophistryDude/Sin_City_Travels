#!/usr/bin/env node

/**
 * Bulk POI Collection Script
 *
 * Queries Yelp Fusion API for restaurants, bars, shops, and attractions
 * near all 31 Las Vegas casino properties.
 *
 * Prerequisites:
 * 1. Sign up for Yelp API: https://www.yelp.com/developers
 * 2. Create .env file with YELP_API_KEY=your_key_here
 * 3. Run: npm install dotenv (if not already installed)
 *
 * Usage:
 *   node scripts/bulk_collect_pois.js [category]
 *
 * Examples:
 *   node scripts/bulk_collect_pois.js restaurants
 *   node scripts/bulk_collect_pois.js bars
 *   node scripts/bulk_collect_pois.js shopping
 *   node scripts/bulk_collect_pois.js all
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// Load environment variables
require('dotenv').config();

const YELP_API_KEY = process.env.YELP_API_KEY;

if (!YELP_API_KEY) {
    console.error('❌ Error: YELP_API_KEY not found in .env file');
    console.error('Please create a .env file with: YELP_API_KEY=your_key_here');
    process.exit(1);
}

// 31 Las Vegas Casino Properties with coordinates
const CASINOS = [
    // Tier 1 - Major Properties
    { name: 'Caesars Palace', lat: 36.1162, lng: -115.1744, area: 'Mid Strip' },
    { name: 'Bellagio', lat: 36.1127, lng: -115.1765, area: 'Mid Strip' },
    { name: 'MGM Grand', lat: 36.1024, lng: -115.1698, area: 'South Strip' },
    { name: 'Aria Resort Casino', lat: 36.1067, lng: -115.1761, area: 'Mid Strip' },

    // Tier 2 - Popular Properties
    { name: 'The Venetian', lat: 36.1212, lng: -115.1697, area: 'North Strip' },
    { name: 'The Palazzo', lat: 36.1242, lng: -115.1697, area: 'North Strip' },
    { name: 'Wynn Las Vegas', lat: 36.1278, lng: -115.1657, area: 'North Strip' },
    { name: 'Encore', lat: 36.1308, lng: -115.1656, area: 'North Strip' },
    { name: 'The Cosmopolitan', lat: 36.1095, lng: -115.1742, area: 'Mid Strip' },
    { name: 'Mandalay Bay', lat: 36.0909, lng: -115.1743, area: 'South Strip' },
    { name: 'Paris Las Vegas', lat: 36.1125, lng: -115.1708, area: 'Mid Strip' },
    { name: 'Planet Hollywood', lat: 36.1097, lng: -115.1708, area: 'Mid Strip' },
    { name: 'Park MGM', lat: 36.1028, lng: -115.1709, area: 'South Strip' },

    // Tier 3 - Mid-Size Properties
    { name: 'The LINQ Hotel', lat: 36.1170, lng: -115.1724, area: 'Mid Strip' },
    { name: 'Flamingo Las Vegas', lat: 36.1176, lng: -115.1720, area: 'Mid Strip' },
    { name: 'Harrahs Las Vegas', lat: 36.1190, lng: -115.1726, area: 'Mid Strip' },
    { name: 'Luxor', lat: 36.0955, lng: -115.1761, area: 'South Strip' },
    { name: 'New York-New York', lat: 36.1021, lng: -115.1740, area: 'South Strip' },
    { name: 'Excalibur', lat: 36.0985, lng: -115.1758, area: 'South Strip' },
    { name: 'Treasure Island', lat: 36.1247, lng: -115.1722, area: 'North Strip' },
    { name: 'The Mirage', lat: 36.1212, lng: -115.1742, area: 'Mid Strip' },
    { name: 'Ballys Las Vegas', lat: 36.1131, lng: -115.1693, area: 'Mid Strip' },
    { name: 'Rio All-Suite Hotel', lat: 36.1172, lng: -115.1736, area: 'Off Strip West' },
    { name: 'Circus Circus', lat: 36.1368, lng: -115.1643, area: 'North Strip' },
    { name: 'Tropicana Las Vegas', lat: 36.1001, lng: -115.1717, area: 'South Strip' },
    { name: 'SLS Las Vegas', lat: 36.1444, lng: -115.1548, area: 'North Strip' },
    { name: 'The Cromwell', lat: 36.1146, lng: -115.1728, area: 'Mid Strip' },

    // Small Casinos
    { name: 'Casino Royale', lat: 36.1185, lng: -115.1726, area: 'Mid Strip' },
    { name: 'Ellis Island', lat: 36.1161, lng: -115.1618, area: 'Off Strip East' },
    { name: 'Stage Door Casino', lat: 36.1143, lng: -115.1488, area: 'Off Strip East' },
    { name: 'Tuscany Suites', lat: 36.1287, lng: -115.1559, area: 'Off Strip East' }
];

// POI Categories
const CATEGORIES = {
    restaurants: 'restaurants',
    bars: 'bars,nightlife',
    shopping: 'shopping',
    attractions: 'entertainment,tours,museums',
    all: 'restaurants,bars,nightlife,shopping,entertainment'
};

// Rate limiting: 5 queries per second max, we'll use 200ms between requests
const RATE_LIMIT_MS = 200;

// Search radius in meters (500m = 0.31 miles)
const SEARCH_RADIUS = 500;

/**
 * Search Yelp API for businesses near a location
 */
function searchYelpByLocation(lat, lng, categories, radius = 500) {
    return new Promise((resolve, reject) => {
        const params = new URLSearchParams({
            latitude: lat,
            longitude: lng,
            categories: categories,
            radius: radius,
            limit: 50,
            sort_by: 'rating'
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
                    reject(new Error(`Yelp API returned ${res.statusCode}: ${data}`));
                }
            });
        });

        req.on('error', reject);
        req.end();
    });
}

/**
 * Sleep utility for rate limiting
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Convert Yelp business data to our POI format
 */
function convertYelpToPOI(business, casinoName, casinoArea, poiId) {
    // Determine subcategory from Yelp categories
    let subcategory = 'other';
    if (business.categories && business.categories.length > 0) {
        const mainCategory = business.categories[0].alias;
        subcategory = mainCategory;
    }

    // Determine main category
    let mainCategory = 'attraction';
    if (business.categories) {
        const categories = business.categories.map(c => c.alias);
        if (categories.some(c => c.includes('restaurant') || c.includes('food'))) {
            mainCategory = 'restaurant';
        } else if (categories.some(c => c.includes('bar') || c.includes('nightlife'))) {
            mainCategory = 'nightlife';
        } else if (categories.some(c => c.includes('shop') || c.includes('shopping'))) {
            mainCategory = 'shopping';
        }
    }

    return {
        id: `poi_${poiId}`,
        name: business.name,
        category: mainCategory,
        subcategory: subcategory,
        casino_property: casinoName,
        location: {
            address: business.location.address1 || '',
            city: business.location.city || 'Las Vegas',
            state: business.location.state || 'NV',
            zip: business.location.zip_code || '',
            casino: casinoName,
            coordinates: {
                lat: business.coordinates.latitude,
                lng: business.coordinates.longitude
            },
            area: casinoArea
        },
        contact: {
            phone: business.phone || business.display_phone || '',
            website: business.url || ''
        },
        pricing: {
            price_range: business.price || 'N/A'
        },
        ratings: {
            yelp: {
                rating: business.rating || 0,
                review_count: business.review_count || 0
            }
        },
        description: '',
        cuisine: business.categories ? business.categories.map(c => c.title) : [],
        features: [],
        tags: business.categories ? business.categories.map(c => c.alias) : [],
        yelp_id: business.id,
        yelp_url: business.url,
        image_url: business.image_url || '',
        is_closed: business.is_closed || false,
        data_sources: [
            'yelp_api',
            `yelp_search_2026-02`
        ],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    };
}

/**
 * Main bulk collection function
 */
async function bulkCollectPOIs(category = 'restaurants') {
    console.log(`\n🎰 Starting bulk POI collection for category: ${category}\n`);
    console.log(`Querying ${CASINOS.length} casino properties...\n`);

    const yelpCategory = CATEGORIES[category] || category;
    const allPOIs = [];
    const uniqueBusinessIds = new Set();
    let poiIdCounter = 1000; // Start from 1000 to avoid conflicts with manual entries

    for (let i = 0; i < CASINOS.length; i++) {
        const casino = CASINOS[i];
        console.log(`[${i + 1}/${CASINOS.length}] Searching near ${casino.name}...`);

        try {
            const results = await searchYelpByLocation(
                casino.lat,
                casino.lng,
                yelpCategory,
                SEARCH_RADIUS
            );

            let newCount = 0;
            if (results.businesses && results.businesses.length > 0) {
                results.businesses.forEach(business => {
                    // Deduplicate by Yelp business ID
                    if (!uniqueBusinessIds.has(business.id)) {
                        uniqueBusinessIds.add(business.id);
                        const poi = convertYelpToPOI(
                            business,
                            casino.name,
                            casino.area,
                            poiIdCounter++
                        );
                        allPOIs.push(poi);
                        newCount++;
                    }
                });
            }

            console.log(`  ✓ Found ${results.businesses ? results.businesses.length : 0} businesses (${newCount} new)`);

            // Rate limit: wait 200ms between requests
            if (i < CASINOS.length - 1) {
                await sleep(RATE_LIMIT_MS);
            }

        } catch (error) {
            console.error(`  ✗ Error: ${error.message}`);
        }
    }

    console.log(`\n✅ Collection complete!`);
    console.log(`Total unique POIs collected: ${allPOIs.length}\n`);

    return allPOIs;
}

/**
 * Save POIs to JSON file
 */
function savePOIs(pois, category) {
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `yelp_${category}_${timestamp}.json`;
    const outputDir = path.join(__dirname, '..', 'data', 'pois', 'raw');

    // Create directory if it doesn't exist
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const filepath = path.join(outputDir, filename);
    fs.writeFileSync(filepath, JSON.stringify(pois, null, 2));

    console.log(`💾 Saved ${pois.length} POIs to: ${filename}`);
    console.log(`📍 Full path: ${filepath}\n`);

    return filepath;
}

/**
 * Generate summary statistics
 */
function generateSummary(pois) {
    console.log('📊 Summary Statistics:\n');

    // Count by category
    const byCategory = {};
    pois.forEach(poi => {
        byCategory[poi.category] = (byCategory[poi.category] || 0) + 1;
    });

    console.log('By Category:');
    Object.entries(byCategory).forEach(([cat, count]) => {
        console.log(`  - ${cat}: ${count}`);
    });

    // Count by casino
    const byCasino = {};
    pois.forEach(poi => {
        byCasino[poi.casino_property] = (byCasino[poi.casino_property] || 0) + 1;
    });

    console.log('\nTop 10 Casinos by POI count:');
    Object.entries(byCasino)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .forEach(([casino, count]) => {
            console.log(`  - ${casino}: ${count}`);
        });

    // Average rating
    const ratings = pois
        .map(poi => poi.ratings.yelp.rating)
        .filter(r => r > 0);
    const avgRating = ratings.length > 0
        ? (ratings.reduce((a, b) => a + b, 0) / ratings.length).toFixed(2)
        : 'N/A';

    console.log(`\nAverage Yelp Rating: ${avgRating}/5.0`);

    // Price range distribution
    const priceRanges = {};
    pois.forEach(poi => {
        const price = poi.pricing.price_range;
        priceRanges[price] = (priceRanges[price] || 0) + 1;
    });

    console.log('\nPrice Range Distribution:');
    Object.entries(priceRanges).forEach(([price, count]) => {
        console.log(`  - ${price}: ${count}`);
    });
}

/**
 * Main execution
 */
async function main() {
    const args = process.argv.slice(2);
    const category = args[0] || 'restaurants';

    console.log('🎰 Sin City Travels - Bulk POI Collection');
    console.log('==========================================\n');

    if (!CATEGORIES[category] && category !== 'all') {
        console.error(`❌ Unknown category: ${category}`);
        console.error(`Valid categories: ${Object.keys(CATEGORIES).join(', ')}`);
        process.exit(1);
    }

    try {
        const pois = await bulkCollectPOIs(category);

        if (pois.length > 0) {
            savePOIs(pois, category);
            generateSummary(pois);

            console.log('\n✨ Next steps:');
            console.log('1. Review the collected POIs in data/pois/raw/');
            console.log('2. Manually curate high-quality POIs');
            console.log('3. Create individual JSON files for key POIs');
            console.log('4. Import to PostgreSQL database');
        } else {
            console.log('⚠️  No POIs collected. Check your API key and network connection.');
        }

    } catch (error) {
        console.error('\n❌ Error during collection:');
        console.error(error);
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    main();
}

module.exports = { bulkCollectPOIs, convertYelpToPOI };
