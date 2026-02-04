# OpenStreetMap Data Summary - Las Vegas Strip

**Downloaded**: February 3, 2026
**Source**: Overpass API
**Bounding Box**: Las Vegas Strip area (36.091°N to 36.157°N, -115.177°W to -115.154°W)

---

## Data Overview

- **Total OSM Elements**: 4,668
- **Hotels Found**: 94
- **Casinos Found**: 36
- **Data File**: `data/maps/las_vegas_strip_hotels_casinos.json` (523 KB)

---

## Major Properties Identified

### High-Priority Strip Casinos (with OSM Data)

✅ **North Strip**:
- The Strat
- Circus Circus Las Vegas
- Wynn Las Vegas Casino
- Encore Casino at Wynn
- The Venetian Las Vegas
- The Palazzo

✅ **Central Strip**:
- Treasure Island
- Caesars Palace
- The LINQ Hotel + Experience
- Flamingo Las Vegas
- Bellagio
- Paris Las Vegas
- Planet Hollywood
- Horseshoe Las Vegas (formerly Bally's)

✅ **South Strip**:
- Aria Resort & Casino
- Park MGM
- New York New York Hotel and Casino
- MGM Grand
- Excalibur Hotel & Casino
- Luxor Las Vegas
- Mandalay Bay

✅ **Recently Added**:
- Resorts World Las Vegas
- Conrad Las Vegas at Resorts World
- Hard Rock Las Vegas (formerly The Mirage)

---

## Data Quality Assessment

### What We Have:
- ✅ Building footprints and outlines
- ✅ Property names and locations
- ✅ Basic amenity tags (hotel, casino)
- ✅ Geographic coordinates (lat/long)

### What's Missing:
- ❌ Indoor floor plans (not in OSM for most properties)
- ❌ Room-level details (casino floors, restaurants, shops)
- ❌ 3D building models
- ❌ Accessibility information (elevators, ramps)
- ❌ Real-time data (crowd density, wait times)

---

## Next Steps

1. **Enhance OSM Data**:
   - Download higher-resolution building geometry
   - Check for any existing `indoor=yes` tags
   - Look for level tags (`level=1`, `level=2`, etc.)

2. **Supplement with Additional Sources**:
   - Google Indoor Maps survey (Task 2)
   - Casino website floor plans
   - Photogrammetry/LiDAR scanning (Phase 2)

3. **Data Processing**:
   - Convert to GeoJSON for easier processing
   - Import into PostgreSQL + PostGIS
   - Create simplified 2D footprints for initial app

---

## Properties NOT in OSM

These major casinos were not found in the current OSM dataset:
- Cosmopolitan of Las Vegas
- Vdara Hotel & Spa
- Tropicana Las Vegas (may have been demolished/renamed)

**Action**: Manually add missing properties to OSM or our custom database.

---

## File Information

**Format**: JSON (Overpass API response)
**Size**: 523 KB
**Location**: `data/maps/las_vegas_strip_hotels_casinos.json`

**Sample Data Structure**:
```json
{
  "elements": [
    {
      "type": "way",
      "id": 123456789,
      "nodes": [node_ids...],
      "tags": {
        "name": "Bellagio",
        "tourism": "hotel",
        "amenity": "casino",
        "addr:street": "Las Vegas Boulevard South",
        "building": "yes"
      }
    }
  ]
}
```

---

**Last Updated**: February 3, 2026
