#!/usr/bin/env python3
"""
Generate synthetic navigation data for pathfinding model training

Creates:
1. Navigation nodes (entrances, junctions, POI connections)
2. Navigation edges (walkways, stairs, elevators)
3. Synthetic routes between POIs

Usage:
    python scripts/generate_synthetic_routes.py

Requirements:
    pip install psycopg2-binary numpy
"""

import os
import sys
import random
import numpy as np
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_batch

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'sincitytravels'),
    'user': os.getenv('DB_USER', 'scapp'),
    'password': os.getenv('DB_PASSWORD', 'changeme_in_production')
}

# Constants for synthetic data generation
NODES_PER_PROPERTY = 50  # Average number of nav nodes per property
EDGES_PER_NODE = 3  # Average connections per node
ROUTES_PER_PROPERTY = 100  # Synthetic routes to generate

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def get_properties(cur):
    """Get all properties from database"""
    cur.execute("""
        SELECT id, name, ST_X(location::geometry) as lng, ST_Y(location::geometry) as lat
        FROM properties
        ORDER BY id
    """)
    return cur.fetchall()

def get_pois_for_property(cur, property_name):
    """Get all POIs for a property"""
    cur.execute("""
        SELECT id, name, category, ST_X(location::geometry) as lng, ST_Y(location::geometry) as lat
        FROM pois
        WHERE casino_property = %s
    """, (property_name,))
    return cur.fetchall()

def generate_navigation_nodes(cur, property_id, property_name, center_lng, center_lat, poi_count):
    """Generate synthetic navigation nodes for a property"""
    nodes = []

    # Property bounds (approximate 500m radius)
    radius_degrees = 0.005  # ~500 meters

    # Generate entrance nodes (4 main entrances per property)
    entrance_count = 4
    for i in range(entrance_count):
        angle = (2 * np.pi / entrance_count) * i
        lng = center_lng + radius_degrees * np.cos(angle)
        lat = center_lat + radius_degrees * np.sin(angle)

        nodes.append({
            'property_id': property_id,
            'node_type': 'entrance',
            'level': 'ground',
            'lng': lng,
            'lat': lat,
            'indoor_x': np.cos(angle) * 100,
            'indoor_y': np.sin(angle) * 100,
            'indoor_level': 0,
            'name': f"{property_name} Entrance {i+1}",
            'accessibility_features': ['wheelchair_accessible', 'automatic_doors']
        })

    # Generate elevator nodes (3 per property)
    elevator_count = 3
    for i in range(elevator_count):
        angle = random.uniform(0, 2 * np.pi)
        distance = random.uniform(0.3, 0.7) * radius_degrees
        lng = center_lng + distance * np.cos(angle)
        lat = center_lat + distance * np.sin(angle)

        nodes.append({
            'property_id': property_id,
            'node_type': 'elevator',
            'level': 'ground',
            'lng': lng,
            'lat': lat,
            'indoor_x': np.cos(angle) * 50,
            'indoor_y': np.sin(angle) * 50,
            'indoor_level': 0,
            'name': f"Elevator {i+1}",
            'accessibility_features': ['wheelchair_accessible', 'elevator']
        })

    # Generate junction nodes (random walkway intersections)
    junction_count = max(20, poi_count * 2)  # At least 20, or 2x POI count
    for i in range(junction_count):
        angle = random.uniform(0, 2 * np.pi)
        distance = random.uniform(0.1, 0.9) * radius_degrees
        lng = center_lng + distance * np.cos(angle)
        lat = center_lat + distance * np.sin(angle)

        nodes.append({
            'property_id': property_id,
            'node_type': 'junction',
            'level': 'ground',
            'lng': lng,
            'lat': lat,
            'indoor_x': random.uniform(-100, 100),
            'indoor_y': random.uniform(-100, 100),
            'indoor_level': 0,
            'name': f"Junction {i+1}",
            'accessibility_features': ['wheelchair_accessible']
        })

    # Insert nodes
    execute_batch(cur, """
        INSERT INTO navigation_nodes (
            property_id, node_type, level, location,
            indoor_x, indoor_y, indoor_level, name, accessibility_features
        ) VALUES (
            %(property_id)s, %(node_type)s, %(level)s,
            ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
            %(indoor_x)s, %(indoor_y)s, %(indoor_level)s,
            %(name)s, %(accessibility_features)s
        )
    """, nodes)

    print(f"  Generated {len(nodes)} navigation nodes")
    return len(nodes)

def generate_navigation_edges(cur, property_id):
    """Generate edges connecting navigation nodes"""
    # Get all nodes for this property
    cur.execute("""
        SELECT id, node_type, indoor_x, indoor_y,
               ST_X(location::geometry) as lng, ST_Y(location::geometry) as lat
        FROM navigation_nodes
        WHERE property_id = %s
    """, (property_id,))

    nodes = cur.fetchall()
    edges = []

    # Create a simple connectivity graph
    # Connect each node to its nearest neighbors
    for i, node in enumerate(nodes):
        node_id, node_type, x, y, lng, lat = node

        # Find k nearest neighbors
        distances = []
        for j, other_node in enumerate(nodes):
            if i == j:
                continue

            other_id, other_type, other_x, other_y, other_lng, other_lat = other_node

            # Calculate Euclidean distance in indoor coordinates
            distance = np.sqrt((x - other_x)**2 + (y - other_y)**2)
            distances.append((distance, j, other_id, other_type))

        # Sort by distance and connect to 3-5 nearest neighbors
        distances.sort()
        connections = random.randint(3, min(5, len(distances)))

        for k in range(connections):
            if k >= len(distances):
                break

            distance, _, other_id, other_type = distances[k]

            # Determine edge type
            if node_type == 'elevator' or other_type == 'elevator':
                edge_type = 'elevator'
                time_multiplier = 2.0  # Elevators take longer
            elif node_type == 'stairs' or other_type == 'stairs':
                edge_type = 'stairs'
                time_multiplier = 1.5
            else:
                edge_type = 'walkway'
                time_multiplier = 1.0

            # Calculate distance in meters (approximate)
            distance_meters = distance * 5  # Rough conversion from indoor units

            # Estimate walking time (average 1.4 m/s walking speed)
            estimated_time = int((distance_meters / 1.4) * time_multiplier)

            # Accessibility rating (stairs are less accessible)
            if edge_type == 'stairs':
                accessibility = 2
            elif edge_type == 'elevator':
                accessibility = 5
            else:
                accessibility = 5

            edges.append({
                'from_node_id': node_id,
                'to_node_id': other_id,
                'edge_type': edge_type,
                'distance_meters': distance_meters,
                'estimated_time_seconds': estimated_time,
                'accessibility_rating': accessibility,
                'is_bidirectional': True
            })

    # Insert edges
    execute_batch(cur, """
        INSERT INTO navigation_edges (
            from_node_id, to_node_id, edge_type,
            distance_meters, estimated_time_seconds,
            accessibility_rating, is_bidirectional
        ) VALUES (
            %(from_node_id)s, %(to_node_id)s, %(edge_type)s,
            %(distance_meters)s, %(estimated_time_seconds)s,
            %(accessibility_rating)s, %(is_bidirectional)s
        )
    """, edges)

    print(f"  Generated {len(edges)} navigation edges")
    return len(edges)

def generate_synthetic_routes(cur, property_id, property_name):
    """Generate synthetic routes between POIs"""
    # Get POIs for this property
    pois = get_pois_for_property(cur, property_name)

    if len(pois) < 2:
        print(f"  Skipping routes (insufficient POIs)")
        return 0

    routes = []

    # Generate random routes between POIs
    route_count = min(ROUTES_PER_PROPERTY, len(pois) * (len(pois) - 1))

    for _ in range(route_count):
        # Pick random start and end POIs
        start_poi = random.choice(pois)
        end_poi = random.choice([p for p in pois if p[0] != start_poi[0]])

        # Calculate straight-line distance
        start_lng, start_lat = start_poi[3], start_poi[4]
        end_lng, end_lat = end_poi[3], end_poi[4]

        # Distance in degrees
        distance_deg = np.sqrt((end_lng - start_lng)**2 + (end_lat - start_lat)**2)

        # Convert to meters (rough approximation: 1 degree ≈ 111km)
        distance_meters = distance_deg * 111000

        # Add indoor routing overhead (1.3x longer than straight line)
        total_distance = distance_meters * 1.3

        # Estimate time (1.4 m/s walking speed)
        estimated_time = int(total_distance / 1.4)

        # Generate a simple path (random nodes)
        # In a real system, this would use Dijkstra's algorithm
        path_length = random.randint(5, 15)
        path_nodes = [random.randint(1, 100) for _ in range(path_length)]

        # Random accessibility features
        has_stairs = random.random() < 0.3
        has_elevator = random.random() < 0.5
        accessibility_score = 3 if has_stairs else 5

        routes.append({
            'property_id': property_id,
            'start_poi_id': start_poi[0],
            'end_poi_id': end_poi[0],
            'total_distance_meters': total_distance,
            'estimated_time_seconds': estimated_time,
            'path_nodes': path_nodes,
            'has_stairs': has_stairs,
            'has_elevator': has_elevator,
            'accessibility_score': accessibility_score
        })

    # Insert routes
    execute_batch(cur, """
        INSERT INTO synthetic_routes (
            property_id, start_poi_id, end_poi_id,
            total_distance_meters, estimated_time_seconds,
            path_nodes, has_stairs, has_elevator, accessibility_score
        ) VALUES (
            %(property_id)s, %(start_poi_id)s, %(end_poi_id)s,
            %(total_distance_meters)s, %(estimated_time_seconds)s,
            %(path_nodes)s, %(has_stairs)s, %(has_elevator)s, %(accessibility_score)s
        )
    """, routes)

    print(f"  Generated {len(routes)} synthetic routes")
    return len(routes)

def generate_all_synthetic_data():
    """Generate all synthetic navigation data"""
    print("Connecting to database...")
    conn = connect_db()
    cur = conn.cursor()

    # Get properties
    properties = get_properties(cur)
    print(f"\nFound {len(properties)} properties\n")

    total_nodes = 0
    total_edges = 0
    total_routes = 0

    for prop_id, prop_name, lng, lat in properties:
        print(f"🏨 {prop_name}")

        # Get POI count for this property
        pois = get_pois_for_property(cur, prop_name)
        poi_count = len(pois)
        print(f"  {poi_count} POIs")

        # Generate navigation nodes
        nodes = generate_navigation_nodes(cur, prop_id, prop_name, lng, lat, poi_count)
        total_nodes += nodes

        # Generate navigation edges
        edges = generate_navigation_edges(cur, prop_id)
        total_edges += edges

        # Generate synthetic routes
        routes = generate_synthetic_routes(cur, prop_id, prop_name)
        total_routes += routes

        # Commit after each property
        conn.commit()
        print()

    # Print summary
    print("="*60)
    print("📊 Generation Summary")
    print("="*60)
    print(f"Properties processed: {len(properties)}")
    print(f"Navigation nodes created: {total_nodes}")
    print(f"Navigation edges created: {total_edges}")
    print(f"Synthetic routes created: {total_routes}")
    print("="*60)

    cur.close()
    conn.close()

    print("\n✅ Synthetic data generation complete!")
    print("\n💡 Next steps:")
    print("   1. Query synthetic routes for ML training data")
    print("   2. Implement pathfinding algorithm (A*, Dijkstra)")
    print("   3. Integrate with Google Maps API for outdoor routing")

if __name__ == "__main__":
    print("="*60)
    print("Sin City Travels - Synthetic Navigation Data Generator")
    print("="*60)
    print("\nThis script generates:")
    print("  • Navigation nodes (entrances, junctions, elevators)")
    print("  • Navigation edges (walkways, stairs, elevators)")
    print("  • Synthetic routes between POIs")
    print("\n" + "="*60 + "\n")

    generate_all_synthetic_data()
