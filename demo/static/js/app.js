document.addEventListener('DOMContentLoaded', async () => {
    // Initialize map
    SinCityMap.init();

    try {
        // Load data in parallel
        const [pois, properties] = await Promise.all([
            API.getPois(),
            API.getProperties()
        ]);

        // Add property labels
        properties.forEach(prop => SinCityMap.addPropertyLabel(prop));

        // Add POI markers
        pois.forEach(poi => SinCityMap.addMarker(poi));

        // Store for reference
        SinCityMap.allPois = pois;

        // Initialize sidebar
        Sidebar.init(pois);

        console.log(`Loaded ${pois.length} POIs and ${properties.length} properties`);
    } catch (err) {
        console.error('Failed to load data:', err);
        document.getElementById('header-stats').textContent = 'Error loading data';
    }
});
