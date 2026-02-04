import os

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'sincitytravels'),
    'user': os.getenv('DB_USER', 'scapp'),
    'password': os.getenv('DB_PASSWORD', 'changeme_in_production')
}

MAP_CONFIG = {
    'center_lat': 36.1115,
    'center_lng': -115.1728,
    'default_zoom': 15,
    'min_zoom': 13,
    'max_zoom': 19
}

# Navigation thresholds
WALK_THRESHOLD_METERS = 500
WALK_SPEED_MPS = 1.4  # meters per second (~3.1 mph)

# Rideshare fare estimates (Las Vegas averages)
UBER_RATES = {
    'base_fare': 1.55,
    'per_minute': 0.35,
    'per_mile': 1.75,
    'booking_fee': 2.55,
    'min_fare': 8.00
}

LYFT_RATES = {
    'base_fare': 1.46,
    'per_minute': 0.30,
    'per_mile': 1.60,
    'booking_fee': 2.75,
    'min_fare': 7.50
}

RIDESHARE_AVG_SPEED_MPH = 15  # Las Vegas Strip average
