document.addEventListener('DOMContentLoaded', function () {
    // --- State Management ---
    let allPulses = [];
    let filteredPulses = [];
    let threatChart = null;
    let currentFilter = null;
    let activePulseId = null;
    let map = null;
    let threatMarkers = null;

    // --- Element References ---
    const detailPane = document.getElementById('detail-pane');
    const cardFeedContainer = document.getElementById('card-feed-container');
    const resetFilterBtn = document.getElementById('reset-filter-btn');

    // --- Geolocation Data ---
    const countryCoords = {"USA":[39.8,-98.6],"United States":[39.8,-98.6],"China":[35.9,104.2],"Russia":[61.5,105.3],"Germany":[51.2,10.5],"UK":[55.4,-3.4],"United Kingdom":[55.4,-3.4],"France":[46.6,1.9],"Canada":[56.1,-106.3],"Australia":[-25.3,133.8],"India":[20.6,78.9],"Brazil":[-14.2,-51.9],"Japan":[36.2,138.3],"South Korea":[35.9,127.8],"North Korea":[40.3,127.5],"Iran":[32.4,53.7],"Israel":[31.0,34.8],"Turkey":[38.9,35.2],"Ukraine":[48.4,31.2],"Poland":[51.9,19.1],"Netherlands":[52.1,5.3],"Belgium":[50.5,4.5],"Spain":[40.4,-3.7],"Italy":[41.9,12.6],"Taiwan":[23.7,120.9],"Vietnam":[14.1,108.3],"Singapore":[1.3,103.8],"Malaysia":[4.2,101.9],"Indonesia":[-0.8,113.9],"Philippines":[12.9,121.8],"South Africa":[-30.6,22.9],"Nigeria":[9.1,8.7],"Egypt":[26.8,30.8],"Saudi Arabia":[23.9,45.1],"UAE":[23.4,53.8],"Mexico":[23.6,-102.5],"Colombia":[4.6,-74.1],"Argentina":[-38.4,-63.6],"Sweden":[60.1,18.6],"Norway":[60.5,8.5],"Finland":[61.9,25.7],"Global":[20,0]};
    
    // --- View Rendering ---

    function renderPlaceholderDetailView() {
        detailPane.innerHTML = `
            <div class="placeholder-content">
                <h3 class="text-xl font-semibold text-gray-400">Threat Details</h3>
                <p class="text-gray-500">Select an item from the feed to see the details.</p>
            </div>
        `;
    }

    async function renderDetailView(pulseId) {
        try {
            const response = await fetch(`/api/pulse/${pulseId}`);
            if (!response.ok) throw new Error('Network response was not ok');
            const pulse = await response.json();

            const severity = pulse.severity || 'unprocessed';
            const severityClasses = { critical: 'tag severity-critical', high: 'tag severity-high', medium: 'tag severity-medium', low: 'tag severity-low', unprocessed: 'tag severity-unprocessed' };
            const industries = (JSON.parse(pulse.targeted_industries || '[]')).map(ind => `<span class="tag industry">${ind}</span>`).join('');
            const countries = (JSON.parse(pulse.targeted_countries || '[]')).map(ctry => `<span class="tag country">${ctry}</span>`).join('');
            
            let indicatorsHTML = '<p>No indicators found.</p>';
            if (pulse.indicators && pulse.indicators.length > 0) {
                indicatorsHTML = pulse.indicators.map(ioc => `<div class="ioc-item"><strong>${ioc.type.toUpperCase()}:</strong> <span>${ioc.value}</span></div>`).join('');
            }
            
            detailPane.innerHTML = `
                <div class="threat-detail-view">
                    <h1 class="text-2xl font-bold text-blue-400 mb-4">${pulse.title}</h1>
                    <div class="flex flex-wrap items-center gap-2 mb-4">
                        <span class="${severityClasses[severity.toLowerCase()]}">${severity}</span>
                        <span class="tag category">${pulse.threat_category || 'General'}</span>
                        ${countries} ${industries}
                    </div>
                    <p class="summary text-gray-300 mb-4 italic border-l-4 border-blue-500 pl-4">${pulse.summary || 'Summary not available.'}</p>
                    <h2 class="section-title text-xl font-semibold mb-2 border-b border-gray-700 pb-2">Indicators of Compromise</h2>
                    <div id="indicators-list">${indicatorsHTML}</div>
                    <div class="source-link mt-4"><a href="${pulse.url}" target="_blank" rel="noopener noreferrer" class="inline-block bg-blue-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors text-sm">Read Full Report</a></div>
                </div>`;
        } catch (error) {
            console.error("Error fetching pulse details:", error);
            renderPlaceholderDetailView(); // Revert to placeholder on error
        }
    }

    // --- Chart, Feed, and Map Logic ---
    function initializeMap() {
        if (map) map.remove();
        map = L.map('threat-map').setView([25, 10], 2);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; CARTO', subdomains: 'abcd', maxZoom: 20 }).addTo(map);
        threatMarkers = L.layerGroup().addTo(map);
    }

    function renderChart() {
        if (threatChart) threatChart.destroy();
        const ctx = document.getElementById('threat-chart').getContext('2d');
        const categoryCounts = allPulses.reduce((acc, pulse) => {
            const category = pulse.threat_category || 'Unprocessed';
            acc[category] = (acc[category] || 0) + 1;
            return acc;
        }, {});
        const sortedCategories = Object.entries(categoryCounts).sort(([,a],[,b]) => b-a);
        const labels = sortedCategories.map(item => item[0]);
        const data = sortedCategories.map(item => item[1]);
        threatChart = new Chart(ctx, {
            type: 'bar',
            data: { labels, datasets: [{ label: 'Report Count', data, backgroundColor: '#007bff' }] },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, title: { display: true, text: 'Threats by Category', color: '#e0e0e0', font: {size: 16} } },
                scales: { x: { ticks: { color: '#a0a0a0' }, grid: { color: '#444' } }, y: { ticks: { color: '#a0a0a0' }, grid: { color: 'transparent' } } },
                onClick: (event, elements) => { if (elements.length > 0) filterByCategory(labels[elements[0].index]); }
            }
        });
    }

    function updateChartHighlight() {
        if (!threatChart) return;
        const colors = threatChart.data.labels.map(label => (currentFilter && label !== currentFilter) ? '#4a5568' : '#007bff');
        threatChart.data.datasets[0].backgroundColor = colors;
        threatChart.update();
    }

    function renderCardFeed() {
        cardFeedContainer.innerHTML = '';
        const pulsesToRender = currentFilter ? filteredPulses : allPulses;
        if (pulsesToRender.length === 0) cardFeedContainer.innerHTML = '<p class="p-4 text-center">No threats to show.</p>';
        pulsesToRender.forEach(pulse => cardFeedContainer.appendChild(createThreatCardElement(pulse)));
        highlightActiveCard();
    }

    function createThreatCardElement(pulse) {
        const severity = pulse.severity || 'unprocessed';
        const card = document.createElement('div');
        card.className = `threat-card severity-${severity.toLowerCase()}`;
        card.dataset.pulseId = pulse.id;
        card.innerHTML = `<h2>${pulse.title}</h2><div class="card-footer"><div class="card-tags"><span class="tag severity-${severity.toLowerCase()}">${severity}</span></div><span>${pulse.source}</span></div>`;
        card.addEventListener('click', () => {
            activePulseId = pulse.id;
            renderDetailView(pulse.id);
            highlightActiveCard();
        });
        return card;
    }

    function highlightActiveCard() {
        document.querySelectorAll('.threat-card').forEach(c => c.classList.remove('active'));
        if (activePulseId) {
            const card = document.querySelector(`.threat-card[data-pulse-id='${activePulseId}']`);
            if (card) card.classList.add('active');
        }
    }

    function updateMapData() {
        if (!map || !threatMarkers) return;
        threatMarkers.clearLayers();
        const pulsesToRender = currentFilter ? filteredPulses : allPulses;
        const severityColors = { Critical: '#dc2626', High: '#fd7e14', Medium: '#ffc107', Low: '#28a745', Unprocessed: '#6b7280' };
        pulsesToRender.forEach(pulse => {
            try {
                const countries = JSON.parse(pulse.targeted_countries || '[]');
                countries.forEach(countryName => {
                    const coords = countryCoords[countryName.trim()];
                    if (coords) {
                        const color = severityColors[pulse.severity] || '#6b7280';
                        const marker = L.circleMarker(coords, { radius: 8, color: "white", weight: 1, fillColor: color, fillOpacity: 0.9 });
                        marker.bindPopup(`<b>${pulse.title}</b>`).on('click', () => {
                            activePulseId = pulse.id;
                            renderDetailView(pulse.id);
                            highlightActiveCard();
                        });
                        threatMarkers.addLayer(marker);
                    }
                });
            } catch (e) { /* ignore */ }
        });
    }

    function filterByCategory(category) {
        currentFilter = category;
        filteredPulses = allPulses.filter(p => (p.threat_category || 'Unprocessed') === category);
        resetFilterBtn.classList.remove('hidden');
        renderCardFeed();
        updateMapData();
        updateChartHighlight();
    }

    function resetFilter() {
        currentFilter = null;
        filteredPulses = allPulses;
        resetFilterBtn.classList.add('hidden');
        renderPlaceholderDetailView();
        activePulseId = null;
        renderCardFeed();
        updateMapData();
        updateChartHighlight();
    }
    
    resetFilterBtn.addEventListener('click', resetFilter);

    // --- Initial Load ---
    async function initialLoad() {
        try {
            const response = await fetch('/api/pulses');
            allPulses = await response.json();
            initializeMap();
            renderChart();
            renderCardFeed();
            renderPlaceholderDetailView();
            updateMapData();
        } catch (error) {
            console.error("Failed to fetch pulses:", error);
            cardFeedContainer.innerHTML = `<div class="p-4"><p class="text-red-500">Error: Could not load data.</p></div>`;
        }
    }

    initialLoad();
});
