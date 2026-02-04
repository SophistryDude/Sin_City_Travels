const CATEGORY_COLORS = {
    restaurant:    '#e74c3c',
    shopping:      '#f39c12',
    entertainment: '#9b59b6',
    nightlife:     '#1abc9c'
};

const SinCityMap = {
    map: null,
    markers: {},
    markerLayer: null,
    propertyLayer: null,
    routeLayer: null,
    nearbyCircle: null,
    allPois: [],

    init() {
        this.map = L.map('map', {
            center: [MAP_CONFIG.center_lat, MAP_CONFIG.center_lng],
            zoom: MAP_CONFIG.default_zoom,
            minZoom: MAP_CONFIG.min_zoom,
            maxZoom: MAP_CONFIG.max_zoom,
            zoomControl: true
        });

        // CartoDB Dark Matter tiles (free, no API key)
        L.tileLayer(
            'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
            {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 20
            }
        ).addTo(this.map);

        this.markerLayer = L.layerGroup().addTo(this.map);
        this.propertyLayer = L.layerGroup().addTo(this.map);
        this.routeLayer = L.layerGroup().addTo(this.map);
        this.highlightLayer = L.layerGroup().addTo(this.map);
        this._highlightedMarker = null;
    },

    createMarkerIcon(category) {
        const color = CATEGORY_COLORS[category] || '#95a5a6';
        return L.divIcon({
            className: 'poi-marker',
            html: `<div class="marker-dot" style="background:${color}"></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7]
        });
    },

    addMarker(poi) {
        const marker = L.marker([poi.lat, poi.lng], {
            icon: this.createMarkerIcon(poi.category)
        });

        marker.bindTooltip(poi.name, {
            direction: 'top',
            className: 'dark-tooltip',
            offset: [0, -10]
        });

        marker.on('click', () => Sidebar.showDetail(poi));
        marker.poiData = poi;

        this.markers[poi.id] = marker;
        this.markerLayer.addLayer(marker);
    },

    addPropertyLabel(property) {
        const label = L.marker([property.lat, property.lng], {
            icon: L.divIcon({
                className: 'property-label',
                html: property.name,
                iconSize: [150, 20],
                iconAnchor: [75, 10]
            }),
            interactive: false
        });
        this.propertyLayer.addLayer(label);
    },

    filterMarkers(activeCategories) {
        Object.values(this.markers).forEach(marker => {
            const category = marker.poiData.category;
            if (activeCategories.has(category)) {
                if (!this.markerLayer.hasLayer(marker)) {
                    this.markerLayer.addLayer(marker);
                }
            } else {
                this.markerLayer.removeLayer(marker);
            }
        });
    },

    showRoute(routeData) {
        this.routeLayer.clearLayers();

        if (!routeData.waypoints || routeData.waypoints.length < 2) return;

        const latlngs = routeData.waypoints
            .filter(wp => wp && wp.lat && wp.lng)
            .map(wp => [wp.lat, wp.lng]);

        if (latlngs.length < 2) return;

        // Outer glow
        L.polyline(latlngs, {
            color: '#ff4444',
            weight: 8,
            opacity: 0.3,
            lineCap: 'round'
        }).addTo(this.routeLayer);

        // Inner dashed line
        L.polyline(latlngs, {
            color: '#ff6b6b',
            weight: 3,
            opacity: 0.9,
            dashArray: '10, 8',
            lineCap: 'round'
        }).addTo(this.routeLayer);

        // Start marker (green)
        L.circleMarker(latlngs[0], {
            radius: 8,
            color: '#2ecc71',
            fillColor: '#2ecc71',
            fillOpacity: 1,
            weight: 2
        }).bindTooltip('Start: ' + (routeData.start ? routeData.start.name : ''), {
            permanent: false,
            className: 'dark-tooltip'
        }).addTo(this.routeLayer);

        // End marker (red)
        L.circleMarker(latlngs[latlngs.length - 1], {
            radius: 8,
            color: '#e74c3c',
            fillColor: '#e74c3c',
            fillOpacity: 1,
            weight: 2
        }).bindTooltip('End: ' + (routeData.end ? routeData.end.name : ''), {
            permanent: false,
            className: 'dark-tooltip'
        }).addTo(this.routeLayer);

        // Fit map to route
        this.map.fitBounds(L.polyline(latlngs).getBounds().pad(0.3));
    },

    clearRoute() {
        this.routeLayer.clearLayers();
    },

    showNearbyRadius(lat, lng, radiusMeters) {
        this.clearNearby();
        this.nearbyCircle = L.circle([lat, lng], {
            radius: radiusMeters,
            color: '#e74c3c',
            fillColor: '#e74c3c',
            fillOpacity: 0.06,
            weight: 1,
            dashArray: '5, 5'
        }).addTo(this.map);

        // Center pin
        L.circleMarker([lat, lng], {
            radius: 5,
            color: '#f1c40f',
            fillColor: '#f1c40f',
            fillOpacity: 1,
            weight: 1
        }).addTo(this.routeLayer);
    },

    clearNearby() {
        if (this.nearbyCircle) {
            this.nearbyCircle.remove();
            this.nearbyCircle = null;
        }
    },

    getCenter() {
        const c = this.map.getCenter();
        return { lat: c.lat, lng: c.lng };
    },

    panTo(lat, lng) {
        this.map.setView([lat, lng], 17, { animate: true });
    },

    highlightMarker(poiId) {
        this.highlightLayer.clearLayers();

        const marker = this.markers[poiId];
        if (!marker) return;

        const poi = marker.poiData;
        const color = CATEGORY_COLORS[poi.category] || '#95a5a6';

        L.circleMarker([poi.lat, poi.lng], {
            radius: 18,
            color: color,
            fillColor: color,
            fillOpacity: 0.15,
            weight: 2,
            dashArray: '4, 4',
            className: 'highlight-pulse'
        }).addTo(this.highlightLayer);

        this._highlightedMarker = poiId;
    },

    clearHighlight() {
        this.highlightLayer.clearLayers();
        this._highlightedMarker = null;
    },

    showMultiLegRoute(navData) {
        this.routeLayer.clearLayers();

        const LEG_COLORS = {
            'indoor': '#3498db',
            'indoor_departure': '#3498db',
            'outdoor_walk': '#f1c40f',
            'rideshare': '#e74c3c',
            'indoor_arrival': '#2ecc71'
        };

        const allPoints = [];

        navData.legs.forEach(leg => {
            if (!leg.waypoints || leg.waypoints.length < 2) return;

            const latlngs = leg.waypoints
                .filter(wp => wp && wp.lat && wp.lng)
                .map(wp => [wp.lat, wp.lng]);

            if (latlngs.length < 2) return;

            allPoints.push(...latlngs);

            const color = LEG_COLORS[leg.leg_type] || '#95a5a6';

            // Outer glow
            L.polyline(latlngs, {
                color: color,
                weight: 8,
                opacity: 0.2,
                lineCap: 'round'
            }).addTo(this.routeLayer);

            // Inner line
            const lineOpts = {
                color: color,
                weight: 3,
                opacity: 0.9,
                lineCap: 'round'
            };

            if (leg.leg_type === 'rideshare') {
                lineOpts.weight = 4;
                lineOpts.dashArray = null;
            } else {
                lineOpts.dashArray = '8, 6';
            }

            L.polyline(latlngs, lineOpts).addTo(this.routeLayer);

            // Rideshare pickup/dropoff markers
            if (leg.leg_type === 'rideshare') {
                if (leg.pickup) {
                    L.marker([leg.pickup.lat, leg.pickup.lng], {
                        icon: L.divIcon({
                            className: 'rideshare-marker',
                            html: '<div class="rs-pin pickup">P</div>',
                            iconSize: [24, 24],
                            iconAnchor: [12, 12]
                        })
                    }).bindTooltip(leg.pickup.name || 'Pickup', {
                        className: 'dark-tooltip'
                    }).addTo(this.routeLayer);
                }
                if (leg.dropoff) {
                    L.marker([leg.dropoff.lat, leg.dropoff.lng], {
                        icon: L.divIcon({
                            className: 'rideshare-marker',
                            html: '<div class="rs-pin dropoff">D</div>',
                            iconSize: [24, 24],
                            iconAnchor: [12, 12]
                        })
                    }).bindTooltip(leg.dropoff.name || 'Dropoff', {
                        className: 'dark-tooltip'
                    }).addTo(this.routeLayer);
                }
            }

            // Leg transition markers (entrance/exit points between legs)
            if (leg.leg_type === 'indoor_departure') {
                const last = latlngs[latlngs.length - 1];
                L.circleMarker(last, {
                    radius: 6, color: '#3498db', fillColor: '#3498db',
                    fillOpacity: 1, weight: 2
                }).bindTooltip('Exit', { className: 'dark-tooltip' }).addTo(this.routeLayer);
            }
            if (leg.leg_type === 'indoor_arrival') {
                const first = latlngs[0];
                L.circleMarker(first, {
                    radius: 6, color: '#2ecc71', fillColor: '#2ecc71',
                    fillOpacity: 1, weight: 2
                }).bindTooltip('Enter', { className: 'dark-tooltip' }).addTo(this.routeLayer);
            }
        });

        // Start marker (green circle)
        if (allPoints.length > 0) {
            L.circleMarker(allPoints[0], {
                radius: 9, color: '#2ecc71', fillColor: '#2ecc71',
                fillOpacity: 1, weight: 3
            }).bindTooltip('Start: ' + (navData.start ? navData.start.name : ''), {
                permanent: false, className: 'dark-tooltip'
            }).addTo(this.routeLayer);

            // End marker (red circle)
            L.circleMarker(allPoints[allPoints.length - 1], {
                radius: 9, color: '#e74c3c', fillColor: '#e74c3c',
                fillOpacity: 1, weight: 3
            }).bindTooltip('End: ' + (navData.end ? navData.end.name : ''), {
                permanent: false, className: 'dark-tooltip'
            }).addTo(this.routeLayer);

            // Fit map to full route
            this.map.fitBounds(L.polyline(allPoints).getBounds().pad(0.3));
        }
    }
};
