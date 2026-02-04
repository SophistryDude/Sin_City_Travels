const API = {
    async get(path) {
        const response = await fetch(path);
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        return response.json();
    },

    async post(path, body) {
        const response = await fetch(path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        return response.json();
    },

    getPois(category) {
        const params = category ? `?category=${category}` : '';
        return this.get(`/api/pois${params}`);
    },

    getProperties() {
        return this.get('/api/properties');
    },

    getNearby(lat, lng, radius, category) {
        let params = `?lat=${lat}&lng=${lng}&radius=${radius}`;
        if (category) params += `&category=${category}`;
        return this.get(`/api/nearby${params}`);
    },

    getRoute(startId, endId) {
        return this.get(`/api/route/${startId}/${endId}`);
    },

    getDistance(poi1Id, poi2Id) {
        return this.get(`/api/distance/${poi1Id}/${poi2Id}`);
    },

    getRecommended() {
        return this.get('/api/pois/recommended');
    },

    navigate(startPoiId, endPoiId) {
        return this.post('/api/navigate', {
            start_poi_id: startPoiId,
            end_poi_id: endPoiId
        });
    }
};
