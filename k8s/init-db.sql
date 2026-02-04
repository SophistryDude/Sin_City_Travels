-- Sin City Travels Database Initialization
-- PostgreSQL + PostGIS for spatial data

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Create enum types
CREATE TYPE poi_category AS ENUM (
    'restaurant',
    'shopping',
    'entertainment',
    'nightlife',
    'pool_spa',
    'attraction',
    'casino',
    'hotel'
);

-- Note: subcategory is VARCHAR(100) instead of ENUM to support the wide variety
-- of venue types across restaurants, nightlife, shows, and attractions.

CREATE TYPE price_range AS ENUM ('$', '$$', '$$$', '$$$$', '$$$$+');

-- POIs table with spatial indexing
CREATE TABLE pois (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category poi_category NOT NULL,
    subcategory VARCHAR(100),
    casino_property VARCHAR(100),

    -- Location data
    address TEXT,
    city VARCHAR(100) DEFAULT 'Las Vegas',
    state VARCHAR(2) DEFAULT 'NV',
    zip VARCHAR(10),
    level VARCHAR(50),
    area VARCHAR(50),
    location GEOGRAPHY(POINT, 4326),

    -- Contact information
    phone VARCHAR(20),
    website TEXT,
    reservations_url TEXT,

    -- Operating details
    hours JSONB,
    price_range price_range,
    average_per_person VARCHAR(50),

    -- Content
    description TEXT,
    cuisine TEXT[],
    features TEXT[],
    chef VARCHAR(100),
    dress_code VARCHAR(50),
    tags TEXT[],

    -- Ratings and awards
    ratings JSONB,

    -- Additional data
    special_features JSONB,
    size_details JSONB,

    -- Metadata
    data_sources TEXT[],
    image_url TEXT,
    is_closed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Spatial index
    CONSTRAINT valid_location CHECK (location IS NOT NULL)
);

-- Create spatial index on location
CREATE INDEX idx_pois_location ON pois USING GIST(location);

-- Create indexes for common queries
CREATE INDEX idx_pois_category ON pois(category);
CREATE INDEX idx_pois_subcategory ON pois(subcategory);
CREATE INDEX idx_pois_casino_property ON pois(casino_property);
CREATE INDEX idx_pois_area ON pois(area);
CREATE INDEX idx_pois_tags ON pois USING GIN(tags);
CREATE INDEX idx_pois_features ON pois USING GIN(features);
CREATE INDEX idx_pois_cuisine ON pois USING GIN(cuisine);

-- Casinos/Properties table
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50),
    address TEXT,
    location GEOGRAPHY(POINT, 4326),
    area VARCHAR(50),
    opened_year INTEGER,
    owner VARCHAR(100),
    room_count INTEGER,
    casino_sq_ft INTEGER,

    -- Property features
    features TEXT[],
    amenities TEXT[],

    -- Floor plan data
    has_floor_plan BOOLEAN DEFAULT FALSE,
    floor_plan_url TEXT,

    -- Metadata
    data_sources TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_properties_location ON properties USING GIST(location);
CREATE INDEX idx_properties_area ON properties(area);

-- Indoor navigation nodes (for pathfinding)
CREATE TABLE navigation_nodes (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES properties(id),
    node_type VARCHAR(50), -- 'entrance', 'elevator', 'stairs', 'poi', 'junction'
    level VARCHAR(50),
    location GEOGRAPHY(POINT, 4326),
    indoor_x FLOAT, -- Indoor coordinate system
    indoor_y FLOAT,
    indoor_level INTEGER,

    -- Node metadata
    name VARCHAR(255),
    entrance_role VARCHAR(50),  -- 'main', 'rideshare_pickup', 'valet', etc.
    accessibility_features TEXT[],

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_nav_nodes_location ON navigation_nodes USING GIST(location);
CREATE INDEX idx_nav_nodes_property ON navigation_nodes(property_id);
CREATE INDEX idx_nav_nodes_level ON navigation_nodes(level);

-- Navigation edges (connections between nodes)
CREATE TABLE navigation_edges (
    id SERIAL PRIMARY KEY,
    from_node_id INTEGER REFERENCES navigation_nodes(id),
    to_node_id INTEGER REFERENCES navigation_nodes(id),
    edge_type VARCHAR(50), -- 'walkway', 'stairs', 'elevator', 'escalator'
    distance_meters FLOAT,
    estimated_time_seconds INTEGER,
    accessibility_rating INTEGER, -- 1-5, 5 being fully accessible
    is_bidirectional BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_nav_edges_from ON navigation_edges(from_node_id);
CREATE INDEX idx_nav_edges_to ON navigation_edges(to_node_id);

-- User routes (synthetic data for training)
CREATE TABLE synthetic_routes (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES properties(id),
    start_poi_id VARCHAR(20) REFERENCES pois(id),
    end_poi_id VARCHAR(20) REFERENCES pois(id),

    -- Route data
    total_distance_meters FLOAT,
    estimated_time_seconds INTEGER,
    path_nodes INTEGER[],

    -- Route characteristics
    has_stairs BOOLEAN DEFAULT FALSE,
    has_elevator BOOLEAN DEFAULT FALSE,
    accessibility_score INTEGER,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_synthetic_routes_property ON synthetic_routes(property_id);
CREATE INDEX idx_synthetic_routes_start ON synthetic_routes(start_poi_id);
CREATE INDEX idx_synthetic_routes_end ON synthetic_routes(end_poi_id);

-- Function to calculate distance between two POIs
CREATE OR REPLACE FUNCTION calculate_poi_distance(poi1_id VARCHAR, poi2_id VARCHAR)
RETURNS FLOAT AS $$
DECLARE
    distance FLOAT;
BEGIN
    SELECT ST_Distance(
        (SELECT location FROM pois WHERE id = poi1_id),
        (SELECT location FROM pois WHERE id = poi2_id)
    ) INTO distance;

    RETURN distance;
END;
$$ LANGUAGE plpgsql;

-- Function to find POIs within radius
CREATE OR REPLACE FUNCTION find_nearby_pois(
    target_lat FLOAT,
    target_lng FLOAT,
    radius_meters FLOAT,
    poi_category_filter poi_category DEFAULT NULL
)
RETURNS TABLE (
    id VARCHAR,
    name VARCHAR,
    category poi_category,
    distance_meters FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.name,
        p.category,
        ST_Distance(
            p.location,
            ST_SetSRID(ST_MakePoint(target_lng, target_lat), 4326)::geography
        ) AS distance
    FROM pois p
    WHERE
        (poi_category_filter IS NULL OR p.category = poi_category_filter)
        AND ST_DWithin(
            p.location,
            ST_SetSRID(ST_MakePoint(target_lng, target_lat), 4326)::geography,
            radius_meters
        )
    ORDER BY distance;
END;
$$ LANGUAGE plpgsql;

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_pois_updated_at BEFORE UPDATE ON pois
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_properties_updated_at BEFORE UPDATE ON properties
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert property data for all properties with POIs
-- Names MUST match the casino_property field in POI JSON files exactly
INSERT INTO properties (name, location, area, owner, has_floor_plan) VALUES
-- ═══════════════════════════════════════════════════════════════
-- SOUTH STRIP (Tropicana to Mandalay Bay)
-- ═══════════════════════════════════════════════════════════════
('Mandalay Bay',       ST_SetSRID(ST_MakePoint(-115.1743, 36.0909), 4326)::geography, 'South Strip', 'MGM Resorts International', TRUE),
('Four Seasons',       ST_SetSRID(ST_MakePoint(-115.1753, 36.0909), 4326)::geography, 'South Strip', 'MGM Resorts International', FALSE),
('Luxor',              ST_SetSRID(ST_MakePoint(-115.1761, 36.0955), 4326)::geography, 'South Strip', 'MGM Resorts International', TRUE),
('Excalibur',          ST_SetSRID(ST_MakePoint(-115.1754, 36.0987), 4326)::geography, 'South Strip', 'MGM Resorts International', TRUE),
('Tropicana',          ST_SetSRID(ST_MakePoint(-115.1730, 36.1012), 4326)::geography, 'South Strip', 'Bally''s Corporation', FALSE),
('New York New York',  ST_SetSRID(ST_MakePoint(-115.1745, 36.1022), 4326)::geography, 'South Strip', 'MGM Resorts International', TRUE),
('MGM Grand',          ST_SetSRID(ST_MakePoint(-115.1698, 36.1024), 4326)::geography, 'South Strip', 'MGM Resorts International', TRUE),
('The Signature',      ST_SetSRID(ST_MakePoint(-115.1665, 36.1024), 4326)::geography, 'South Strip', 'MGM Resorts International', FALSE),
('Park MGM',           ST_SetSRID(ST_MakePoint(-115.1709, 36.1028), 4326)::geography, 'South Strip', 'MGM Resorts International', TRUE),
('NoMad',              ST_SetSRID(ST_MakePoint(-115.1709, 36.1028), 4326)::geography, 'South Strip', 'MGM Resorts International', FALSE),

-- ═══════════════════════════════════════════════════════════════
-- MID STRIP (Aria to Flamingo)
-- ═══════════════════════════════════════════════════════════════
('Aria',               ST_SetSRID(ST_MakePoint(-115.1761, 36.1067), 4326)::geography, 'Mid Strip', 'MGM Resorts International', TRUE),
('Waldorf Astoria',    ST_SetSRID(ST_MakePoint(-115.1755, 36.1070), 4326)::geography, 'Mid Strip', 'Hilton Hotels', FALSE),
('Vdara',              ST_SetSRID(ST_MakePoint(-115.1773, 36.1080), 4326)::geography, 'Mid Strip', 'MGM Resorts International', FALSE),
('Cosmopolitan',       ST_SetSRID(ST_MakePoint(-115.1742, 36.1095), 4326)::geography, 'Mid Strip', 'MGM Resorts International', TRUE),
('Planet Hollywood',   ST_SetSRID(ST_MakePoint(-115.1708, 36.1097), 4326)::geography, 'Mid Strip', 'Caesars Entertainment', TRUE),
('Paris',              ST_SetSRID(ST_MakePoint(-115.1707, 36.1125), 4326)::geography, 'Mid Strip', 'Caesars Entertainment', TRUE),
('Bellagio',           ST_SetSRID(ST_MakePoint(-115.1765, 36.1127), 4326)::geography, 'Mid Strip', 'MGM Resorts International', TRUE),
('Caesars Palace',     ST_SetSRID(ST_MakePoint(-115.1744, 36.1162), 4326)::geography, 'Mid Strip', 'Caesars Entertainment', TRUE),
('Flamingo',           ST_SetSRID(ST_MakePoint(-115.1714, 36.1162), 4326)::geography, 'Mid Strip', 'Caesars Entertainment', TRUE),
('The Cromwell',       ST_SetSRID(ST_MakePoint(-115.1722, 36.1168), 4326)::geography, 'Mid Strip', 'Caesars Entertainment', FALSE),
('The LINQ',           ST_SetSRID(ST_MakePoint(-115.1710, 36.1176), 4326)::geography, 'Mid Strip', 'Caesars Entertainment', TRUE),
('Horseshoe',          ST_SetSRID(ST_MakePoint(-115.1726, 36.1190), 4326)::geography, 'Mid Strip', 'Caesars Entertainment', TRUE),
('Harrah''s',          ST_SetSRID(ST_MakePoint(-115.1726, 36.1190), 4326)::geography, 'Mid Strip', 'Caesars Entertainment', TRUE),
('Casino Royale',      ST_SetSRID(ST_MakePoint(-115.1721, 36.1200), 4326)::geography, 'Mid Strip', 'Independent', FALSE),

-- ═══════════════════════════════════════════════════════════════
-- NORTH STRIP (Venetian to STRAT)
-- ═══════════════════════════════════════════════════════════════
('The Venetian',       ST_SetSRID(ST_MakePoint(-115.1697, 36.1212), 4326)::geography, 'North Strip', 'Apollo Global Management', TRUE),
('The Palazzo',        ST_SetSRID(ST_MakePoint(-115.1693, 36.1228), 4326)::geography, 'North Strip', 'Apollo Global Management', TRUE),
('Treasure Island',    ST_SetSRID(ST_MakePoint(-115.1709, 36.1247), 4326)::geography, 'North Strip', 'Radisson Hotel Group', TRUE),
('Fashion Show Mall',  ST_SetSRID(ST_MakePoint(-115.1700, 36.1268), 4326)::geography, 'North Strip', 'Brookfield Properties', FALSE),
('Wynn',               ST_SetSRID(ST_MakePoint(-115.1660, 36.1264), 4326)::geography, 'North Strip', 'Wynn Resorts', TRUE),
('Encore',             ST_SetSRID(ST_MakePoint(-115.1650, 36.1289), 4326)::geography, 'North Strip', 'Wynn Resorts', TRUE),
('Trump',              ST_SetSRID(ST_MakePoint(-115.1686, 36.1270), 4326)::geography, 'North Strip', 'Trump Organization', FALSE),
('W Las Vegas',        ST_SetSRID(ST_MakePoint(-115.1665, 36.1024), 4326)::geography, 'North Strip', 'Marriott International', FALSE),
('Fontainebleau',      ST_SetSRID(ST_MakePoint(-115.1568, 36.1361), 4326)::geography, 'North Strip', 'Fontainebleau Development', TRUE),
('Circus Circus',      ST_SetSRID(ST_MakePoint(-115.1631, 36.1367), 4326)::geography, 'North Strip', 'Phil Ruffin', TRUE),
('Resorts World',      ST_SetSRID(ST_MakePoint(-115.1652, 36.1380), 4326)::geography, 'North Strip', 'Genting Group', TRUE),
('Sahara',             ST_SetSRID(ST_MakePoint(-115.1567, 36.1413), 4326)::geography, 'North Strip', 'Meruelo Group', TRUE),
('The STRAT',          ST_SetSRID(ST_MakePoint(-115.1557, 36.1474), 4326)::geography, 'North Strip', 'Golden Entertainment', TRUE),

-- ═══════════════════════════════════════════════════════════════
-- DOWNTOWN (Fremont Street)
-- ═══════════════════════════════════════════════════════════════
('Downtown Grand',     ST_SetSRID(ST_MakePoint(-115.1424, 36.1699), 4326)::geography, 'Downtown', 'Fifth Street Gaming', FALSE),
('Golden Nugget',      ST_SetSRID(ST_MakePoint(-115.1445, 36.1708), 4326)::geography, 'Downtown', 'Tilman Fertitta', TRUE),
('Circa',              ST_SetSRID(ST_MakePoint(-115.1461, 36.1712), 4326)::geography, 'Downtown', 'Derek Stevens', TRUE),
('Binion''s',          ST_SetSRID(ST_MakePoint(-115.1443, 36.1705), 4326)::geography, 'Downtown', 'TLC Casino Enterprises', FALSE),
('California',         ST_SetSRID(ST_MakePoint(-115.1415, 36.1697), 4326)::geography, 'Downtown', 'Boyd Gaming', FALSE),
('The D',              ST_SetSRID(ST_MakePoint(-115.1456, 36.1698), 4326)::geography, 'Downtown', 'Derek Stevens', FALSE),
('Main Street Station', ST_SetSRID(ST_MakePoint(-115.1411, 36.1712), 4326)::geography, 'Downtown', 'Boyd Gaming', FALSE),

-- ═══════════════════════════════════════════════════════════════
-- OFF-STRIP (major properties)
-- ═══════════════════════════════════════════════════════════════
('Rio',                ST_SetSRID(ST_MakePoint(-115.1878, 36.1167), 4326)::geography, 'Off-Strip', 'Dreamscape Companies', TRUE),
('Palms',              ST_SetSRID(ST_MakePoint(-115.1848, 36.1145), 4326)::geography, 'Off-Strip', 'San Manuel Band', TRUE),
('Red Rock',           ST_SetSRID(ST_MakePoint(-115.3120, 36.1696), 4326)::geography, 'Off-Strip', 'Station Casinos', FALSE),
('Westgate',           ST_SetSRID(ST_MakePoint(-115.1530, 36.1340), 4326)::geography, 'Off-Strip', 'Westgate Resorts', FALSE),
('Durango',            ST_SetSRID(ST_MakePoint(-115.2797, 36.1464), 4326)::geography, 'Off-Strip', 'Station Casinos', FALSE),
('M Resort',           ST_SetSRID(ST_MakePoint(-115.1559, 36.0125), 4326)::geography, 'Off-Strip', 'Penn Entertainment', FALSE),
('Silverton',          ST_SetSRID(ST_MakePoint(-115.1863, 36.0765), 4326)::geography, 'Off-Strip', 'Ed Roski Jr.', FALSE),
('The Orleans',        ST_SetSRID(ST_MakePoint(-115.1973, 36.1012), 4326)::geography, 'Off-Strip', 'Boyd Gaming', FALSE),
('Gold Coast',         ST_SetSRID(ST_MakePoint(-115.1880, 36.1117), 4326)::geography, 'Off-Strip', 'Boyd Gaming', FALSE),
('Ellis Island',       ST_SetSRID(ST_MakePoint(-115.1680, 36.1151), 4326)::geography, 'Off-Strip', 'Ellis Island Hotel', FALSE),
('OYO',                ST_SetSRID(ST_MakePoint(-115.1529, 36.1012), 4326)::geography, 'Off-Strip', 'OYO Hotels & Homes', FALSE),
('Tuscany Suites',     ST_SetSRID(ST_MakePoint(-115.1594, 36.1095), 4326)::geography, 'Off-Strip', 'Independent', FALSE),
('Silver Sevens',      ST_SetSRID(ST_MakePoint(-115.1528, 36.1110), 4326)::geography, 'Off-Strip', 'Affinity Gaming', FALSE),
('Aliante',            ST_SetSRID(ST_MakePoint(-115.1262, 36.2873), 4326)::geography, 'Off-Strip', 'Boyd Gaming', FALSE),
('Cannery',            ST_SetSRID(ST_MakePoint(-115.0962, 36.2178), 4326)::geography, 'Off-Strip', 'Boyd Gaming', FALSE),

-- Station Casinos
('Sam''s Town',        ST_SetSRID(ST_MakePoint(-115.0562, 36.1143), 4326)::geography, 'Off-Strip', 'Boyd Gaming', FALSE),
('Boulder Station',    ST_SetSRID(ST_MakePoint(-115.0720, 36.1514), 4326)::geography, 'Off-Strip', 'Station Casinos', FALSE),
('Green Valley Ranch', ST_SetSRID(ST_MakePoint(-115.0630, 36.0467), 4326)::geography, 'Off-Strip', 'Station Casinos', FALSE),
('Santa Fe Station',   ST_SetSRID(ST_MakePoint(-115.2395, 36.2309), 4326)::geography, 'Off-Strip', 'Station Casinos', FALSE),
('Sunset Station',     ST_SetSRID(ST_MakePoint(-115.0634, 36.0713), 4326)::geography, 'Off-Strip', 'Station Casinos', FALSE);

-- Pre-calculated distances between casino properties
CREATE TABLE property_distances (
    id SERIAL PRIMARY KEY,
    from_property_name VARCHAR(100) NOT NULL,
    to_property_name VARCHAR(100) NOT NULL,
    distance_meters FLOAT NOT NULL,
    UNIQUE(from_property_name, to_property_name)
);

CREATE INDEX idx_property_distances_from ON property_distances(from_property_name);
CREATE INDEX idx_property_distances_to ON property_distances(to_property_name);

-- Populate property distances from properties table
INSERT INTO property_distances (from_property_name, to_property_name, distance_meters)
SELECT
    p1.name, p2.name,
    ST_Distance(p1.location, p2.location)
FROM properties p1
CROSS JOIN properties p2
WHERE p1.id != p2.id;

-- Function to find nearest entrance/exit node to a given POI
CREATE OR REPLACE FUNCTION find_nearest_entrance(
    poi_id_param VARCHAR,
    entrance_role_param VARCHAR DEFAULT 'main'
)
RETURNS TABLE (
    node_id INTEGER,
    node_name VARCHAR,
    node_lat FLOAT,
    node_lng FLOAT,
    distance_meters FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        nn.id AS node_id,
        nn.name AS node_name,
        ST_Y(nn.location::geometry)::FLOAT AS node_lat,
        ST_X(nn.location::geometry)::FLOAT AS node_lng,
        ST_Distance(nn.location, p.location)::FLOAT AS distance_meters
    FROM navigation_nodes nn
    JOIN pois p ON p.id = poi_id_param
    JOIN properties prop ON nn.property_id = prop.id AND prop.name = p.casino_property
    WHERE nn.node_type = 'entrance'
      AND (entrance_role_param = 'main' OR nn.entrance_role = entrance_role_param)
    ORDER BY ST_Distance(nn.location, p.location)
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scapp;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO scapp;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO scapp;

-- Display summary
DO $$
BEGIN
    RAISE NOTICE 'Database initialization complete!';
    RAISE NOTICE 'PostGIS extensions enabled';
    RAISE NOTICE 'Tables created: pois, properties, navigation_nodes, navigation_edges, synthetic_routes';
    RAISE NOTICE 'Spatial indexes created';
    RAISE NOTICE 'Helper functions created';
    RAISE NOTICE '63 properties inserted (Strip, Downtown, Off-Strip)';
END $$;
