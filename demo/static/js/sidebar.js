const Sidebar = {
    activeCategories: new Set(['restaurant', 'shopping', 'entertainment', 'nightlife']),
    allPois: [],

    init(pois) {
        this.allPois = pois;
        this.setupFilters(pois);
        this.setupRoutePanel(pois);
        this.setupNearbyPanel();
        this.setupDetailPanel();
        this.loadRecommended();
    },

    // --- Category Filters ---
    setupFilters(pois) {
        const counts = {};
        pois.forEach(p => {
            counts[p.category] = (counts[p.category] || 0) + 1;
        });

        Object.entries(counts).forEach(([cat, count]) => {
            const el = document.getElementById(`count-${cat}`);
            if (el) el.textContent = count;
        });

        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const cat = btn.dataset.category;
                btn.classList.toggle('active');
                if (this.activeCategories.has(cat)) {
                    this.activeCategories.delete(cat);
                } else {
                    this.activeCategories.add(cat);
                }
                SinCityMap.filterMarkers(this.activeCategories);
            });
        });

        // Update header stats
        document.getElementById('header-stats').textContent =
            `${pois.length} POIs across 9 properties`;
    },

    // --- Route Planner ---
    setupRoutePanel(pois) {
        const startSelect = document.getElementById('route-start');
        const endSelect = document.getElementById('route-end');

        // Group POIs by property
        const grouped = {};
        pois.forEach(p => {
            const prop = p.casino_property || 'Other';
            if (!grouped[prop]) grouped[prop] = [];
            grouped[prop].push(p);
        });

        [startSelect, endSelect].forEach(select => {
            Object.entries(grouped).sort().forEach(([prop, propPois]) => {
                const group = document.createElement('optgroup');
                group.label = prop;
                propPois.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.id;
                    opt.textContent = p.name;
                    group.appendChild(opt);
                });
                select.appendChild(group);
            });
        });

        document.getElementById('btn-find-route').addEventListener('click', () => Navigate.startNavigation());
        document.getElementById('btn-clear-route').addEventListener('click', () => Navigate.clear());
    },

    async findRoute() {
        const startId = document.getElementById('route-start').value;
        const endId = document.getElementById('route-end').value;

        if (!startId || !endId) return;
        if (startId === endId) return;

        const resultDiv = document.getElementById('route-result');
        resultDiv.classList.remove('hidden');
        resultDiv.innerHTML = '<div style="text-align:center;padding:12px;color:#95a5a6">Calculating route...</div>';

        try {
            const route = await API.getRoute(startId, endId);
            SinCityMap.showRoute(route);
            this.renderRouteResult(route);
        } catch (err) {
            resultDiv.innerHTML = `<div style="color:#e74c3c;padding:8px">Error: ${err.message}</div>`;
        }
    },

    renderRouteResult(route) {
        const div = document.getElementById('route-result');
        const dist = route.distance_meters;
        const time = route.estimated_time_seconds;
        const minutes = Math.floor(time / 60);
        const seconds = time % 60;

        let accessHtml = '';
        if (route.has_stairs) accessHtml += '<span class="access-badge stairs">Has Stairs</span>';
        if (route.has_elevator) accessHtml += '<span class="access-badge elevator">Elevator Available</span>';
        if (route.accessibility_score) accessHtml += `<span class="access-badge score">Score: ${route.accessibility_score}/5</span>`;

        div.innerHTML = `
            <div class="route-info">
                <h4>${route.found ? 'Route Found' : 'Direct Path'}</h4>
                <div class="route-stats">
                    <div class="route-stat">
                        <div class="value">${Math.round(dist)}m</div>
                        <div class="label">Distance</div>
                    </div>
                    <div class="route-stat">
                        <div class="value">${minutes}:${String(seconds).padStart(2, '0')}</div>
                        <div class="label">Walk Time</div>
                    </div>
                </div>
                ${accessHtml ? `<div class="accessibility-info">${accessHtml}</div>` : ''}
            </div>
        `;
    },

    clearRoute() {
        SinCityMap.clearRoute();
        document.getElementById('route-result').classList.add('hidden');
        document.getElementById('route-start').value = '';
        document.getElementById('route-end').value = '';
    },

    // --- Find Nearby ---
    setupNearbyPanel() {
        const slider = document.getElementById('radius-slider');
        const display = document.getElementById('radius-value');

        slider.addEventListener('input', () => {
            display.textContent = slider.value;
        });

        document.getElementById('btn-find-nearby').addEventListener('click', () => this.findNearby());
    },

    async findNearby(lat, lng) {
        const radius = parseInt(document.getElementById('radius-slider').value);
        const center = (lat && lng) ? { lat, lng } : SinCityMap.getCenter();

        const resultsDiv = document.getElementById('nearby-results');
        resultsDiv.classList.remove('hidden');
        resultsDiv.innerHTML = '<div style="padding:8px;color:#95a5a6">Searching...</div>';

        try {
            SinCityMap.showNearbyRadius(center.lat, center.lng, radius);
            const results = await API.getNearby(center.lat, center.lng, radius);

            if (results.length === 0) {
                resultsDiv.innerHTML = '<div style="padding:8px;color:#95a5a6">No POIs found within radius</div>';
                return;
            }

            resultsDiv.innerHTML = results.map(r => `
                <div class="nearby-item" data-id="${r.id}">
                    <div>
                        <div class="name">${r.name}</div>
                        <div style="font-size:0.75rem;color:#95a5a6">${r.category}</div>
                    </div>
                    <div class="distance">${Math.round(r.distance_meters)}m</div>
                </div>
            `).join('');

            resultsDiv.querySelectorAll('.nearby-item').forEach(item => {
                item.addEventListener('click', () => {
                    const poi = this.allPois.find(p => p.id === item.dataset.id);
                    if (poi) {
                        this.showDetail(poi);
                        SinCityMap.panTo(poi.lat, poi.lng);
                    }
                });
            });
        } catch (err) {
            resultsDiv.innerHTML = `<div style="color:#e74c3c;padding:8px">Error: ${err.message}</div>`;
        }
    },

    // --- POI Detail ---
    setupDetailPanel() {
        document.getElementById('btn-close-detail').addEventListener('click', () => {
            document.getElementById('detail-panel').classList.add('hidden');
        });
    },

    showDetail(poi) {
        const panel = document.getElementById('detail-panel');
        const content = document.getElementById('detail-content');

        panel.classList.remove('hidden');

        let html = `
            <span class="category-badge ${poi.category}">${poi.category}</span>
            <div class="detail-name">${poi.name}</div>
            <div class="detail-property">${poi.casino_property || ''} ${poi.area ? '&middot; ' + poi.area : ''}</div>
        `;

        // Meta info
        html += '<div class="detail-meta">';
        if (poi.price_range) {
            html += `<div class="meta-item"><span class="meta-label">Price</span><span class="meta-value">${poi.price_range}</span></div>`;
        }
        if (poi.chef) {
            html += `<div class="meta-item"><span class="meta-label">Chef</span><span class="meta-value">${poi.chef}</span></div>`;
        }
        if (poi.average_per_person) {
            html += `<div class="meta-item"><span class="meta-label">Per Person</span><span class="meta-value">${poi.average_per_person}</span></div>`;
        }
        if (poi.dress_code) {
            html += `<div class="meta-item"><span class="meta-label">Dress Code</span><span class="meta-value">${poi.dress_code}</span></div>`;
        }
        if (poi.level) {
            html += `<div class="meta-item"><span class="meta-label">Level</span><span class="meta-value">${poi.level}</span></div>`;
        }
        html += '</div>';

        // Ratings
        if (poi.ratings && Object.keys(poi.ratings).length > 0) {
            html += '<div class="detail-section"><h4>Awards & Ratings</h4>';
            if (poi.ratings.michelin) {
                const stars = poi.ratings.michelin.stars || 0;
                html += `<span class="rating-badge">Michelin ${'&#9733;'.repeat(stars)}</span> `;
            }
            if (poi.ratings.aaa) {
                const diamonds = poi.ratings.aaa.diamonds || 0;
                html += `<span class="rating-badge">AAA ${'&#9830;'.repeat(diamonds)}</span> `;
            }
            html += '</div>';
        }

        // Description
        if (poi.description) {
            html += `
                <div class="detail-section">
                    <h4>About</h4>
                    <p class="detail-description">${poi.description}</p>
                </div>
            `;
        }

        // Cuisine tags
        if (poi.cuisine && poi.cuisine.length > 0) {
            html += '<div class="detail-section"><h4>Cuisine</h4><div class="cuisine-tags">';
            poi.cuisine.forEach(c => {
                html += `<span class="cuisine-tag">${c}</span>`;
            });
            html += '</div></div>';
        }

        // Features
        if (poi.features && poi.features.length > 0) {
            html += '<div class="detail-section"><h4>Features</h4><div>';
            poi.features.forEach(f => {
                html += `<span class="feature-tag">${f.replace(/_/g, ' ')}</span>`;
            });
            html += '</div></div>';
        }

        // Hours
        if (poi.hours && Object.keys(poi.hours).length > 0) {
            const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
            html += '<div class="detail-section"><h4>Hours</h4><div class="hours-grid">';
            days.forEach(day => {
                if (poi.hours[day]) {
                    const today = new Date().toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
                    const isToday = day === today;
                    html += `<span class="hours-day" style="${isToday ? 'color:#f1c40f;font-weight:600' : ''}">${day.slice(0, 3)}</span>`;
                    html += `<span class="hours-time" style="${isToday ? 'color:#f1c40f' : ''}">${poi.hours[day]}</span>`;
                }
            });
            html += '</div></div>';
        }

        // Links
        if (poi.phone || poi.website) {
            html += '<div class="detail-section detail-links">';
            if (poi.phone) html += `<a href="tel:${poi.phone}">${poi.phone}</a>`;
            if (poi.website) html += `<a href="${poi.website}" target="_blank">Website</a>`;
            html += '</div>';
        }

        // Actions
        html += `
            <div class="detail-actions">
                <button onclick="Sidebar.routeFromHere('${poi.id}')">Navigate From</button>
                <button onclick="Sidebar.routeToHere('${poi.id}')">Navigate To</button>
                <button onclick="Sidebar.findNearby(${poi.lat}, ${poi.lng})">Nearby</button>
            </div>
        `;

        content.innerHTML = html;

        // Scroll detail panel into view
        panel.scrollIntoView({ behavior: 'smooth' });
    },

    routeFromHere(poiId) {
        document.getElementById('route-start').value = poiId;
        document.getElementById('route-panel').scrollIntoView({ behavior: 'smooth' });
    },

    routeToHere(poiId) {
        document.getElementById('route-end').value = poiId;
        document.getElementById('route-panel').scrollIntoView({ behavior: 'smooth' });
    },

    // --- Recommended Spots ---
    async loadRecommended() {
        const list = document.getElementById('recommended-list');

        try {
            const spots = await API.getRecommended();
            this.recommendedPois = spots;

            // Merge into allPois if not already present
            spots.forEach(spot => {
                if (!this.allPois.find(p => p.id === spot.id)) {
                    this.allPois.push(spot);
                }
            });

            if (spots.length === 0) {
                list.innerHTML = '<div style="padding:8px;color:#95a5a6">No recommended spots yet</div>';
                return;
            }

            list.innerHTML = spots.map(spot => this.renderRecommendedCard(spot)).join('');

            // Wire up card click handlers
            list.querySelectorAll('.rec-card').forEach(card => {
                card.addEventListener('click', () => {
                    const poi = this.allPois.find(p => p.id === card.dataset.id);
                    if (poi) {
                        SinCityMap.panTo(poi.lat, poi.lng);
                        SinCityMap.highlightMarker(poi.id);
                        this.showDetail(poi);
                    }
                });
            });

            // Stop propagation on call buttons so card click doesn't fire
            list.querySelectorAll('.rec-call-btn').forEach(btn => {
                btn.addEventListener('click', (e) => e.stopPropagation());
            });

        } catch (err) {
            list.innerHTML = '<div style="padding:8px;color:#95a5a6">Could not load recommendations</div>';
            console.error('Failed to load recommended spots:', err);
        }
    },

    renderRecommendedCard(poi) {
        const subcatDisplay = (poi.subcategory || 'bar').replace(/_/g, ' ');
        const locationText = poi.casino_property
            ? `${poi.casino_property} &middot; ${poi.area || ''}`
            : (poi.area || '');
        const truncDesc = poi.description
            ? (poi.description.length > 120 ? poi.description.substring(0, 120) + '...' : poi.description)
            : '';
        const callBtn = poi.phone
            ? `<a href="tel:${poi.phone}" class="rec-call-btn" title="Call ${poi.name}">&#128222; ${poi.phone}</a>`
            : '';

        return `
            <div class="rec-card" data-id="${poi.id}">
                <div class="rec-card-header">
                    <span class="rec-badge nightlife">${subcatDisplay}</span>
                    ${poi.price_range ? `<span class="rec-price">${poi.price_range}</span>` : ''}
                </div>
                <div class="rec-card-name">${poi.name}</div>
                <div class="rec-card-location">${locationText}</div>
                <div class="rec-card-desc">${truncDesc}</div>
                ${callBtn ? `<div class="rec-card-contact">${callBtn}</div>` : ''}
            </div>
        `;
    }
};
