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

CREATE TYPE poi_subcategory AS ENUM (
    'fine_dining_steakhouse',
    'fine_dining_italian',
    'fine_dining_french',
    'fine_dining_japanese',
    'fine_dining_chinese',
    'fine_dining_american',
    'fine_dining_spanish',
    'fine_dining_mediterranean',
    'fine_dining_asian',
    'fine_dining_supper_club',
    'casual_asian',
    'casual_mexican',
    'luxury_mall',
    'ultra_luxury_mall',
    'lifestyle_mall',
    'cirque_du_soleil_show',
    'nightclub',
    'bar',
    'lounge',
    'speakeasy',
    'craft_cocktail_bar',
    'tiki_bar',
    'cocktail_lounge'
);

CREATE TYPE price_range AS ENUM ('$', '$$', '$$$', '$$$$', '$$$$+');

-- POIs table with spatial indexing
CREATE TABLE pois (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category poi_category NOT NULL,
    subcategory poi_subcategory,
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

-- Insert initial property data (8 major casinos we have POI data for)
INSERT INTO properties (name, location, area, owner, has_floor_plan) VALUES
('MGM Grand', ST_SetSRID(ST_MakePoint(-115.1698, 36.1024), 4326)::geography, 'South Strip', 'MGM Resorts International', TRUE),
('Park MGM', ST_SetSRID(ST_MakePoint(-115.1709, 36.1028), 4326)::geography, 'South Strip', 'MGM Resorts International', TRUE),
('Bellagio', ST_SetSRID(ST_MakePoint(-115.1765, 36.1127), 4326)::geography, 'Mid Strip', 'MGM Resorts International', TRUE),
('Caesars Palace', ST_SetSRID(ST_MakePoint(-115.1744, 36.1162), 4326)::geography, 'Mid Strip', 'Caesars Entertainment', TRUE),
('Aria Resort Casino', ST_SetSRID(ST_MakePoint(-115.1761, 36.1067), 4326)::geography, 'Mid Strip', 'MGM Resorts International', TRUE),
('The Venetian', ST_SetSRID(ST_MakePoint(-115.1697, 36.1212), 4326)::geography, 'North Strip', 'Las Vegas Sands', TRUE),
('The Cosmopolitan', ST_SetSRID(ST_MakePoint(-115.1742, 36.1095), 4326)::geography, 'Mid Strip', 'MGM Resorts International', TRUE),
('Wynn Las Vegas', ST_SetSRID(ST_MakePoint(-115.1657, 36.1278), 4326)::geography, 'North Strip', 'Wynn Resorts', TRUE),
('Mandalay Bay', ST_SetSRID(ST_MakePoint(-115.1743, 36.0909), 4326)::geography, 'South Strip', 'MGM Resorts International', TRUE);

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
    RAISE NOTICE '9 properties inserted';
END $$;
