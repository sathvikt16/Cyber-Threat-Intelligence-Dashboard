// // document.addEventListener('DOMContentLoaded', function () {
// //     const pulseListContainer = document.getElementById('pulse-list');
// //     const pulseDetailContainer = document.getElementById('pulse-detail-container');
// //     let activePulseId = null;

// //     // --- Geolocation Data ---
// //     const countryCoords = { "USA": [39.8, -98.6], "United States": [39.8, -98.6], "Russia": [61.5, 105.3], "China": [35.9, 104.2], "Germany": [51.2, 10.5], "UK": [55.4, -3.4], "United Kingdom": [55.4, -3.4], "Brazil": [-14.2, -51.9], "India": [20.6, 78.9], "Australia": [-25.3, 133.8], "Canada": [56.1, -106.3], "France": [46.6, 1.9], "Iran": [32.4, 53.7], "North Korea": [40.3, 127.5], "Ukraine": [48.4, 31.2], "Global": [20, 0] };

// //     // --- Map Initialization ---
// //     const map = L.map('threat-map').setView([25, 10], 2); // Set initial view
// //     L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
// //         attribution: '&copy; <a href="https://carto.com/attributions">CARTO</a>',
// //         subdomains: 'abcd',
// //         maxZoom: 19
// //     }).addTo(map);
// //     let threatMarkers = L.layerGroup().addTo(map);

// //     // --- Fetch and Render the list of pulses in the sidebar ---
// //     async function fetchAndRenderPulseList() {
// //         try {
// //             const response = await fetch('/api/pulses');
// //             const pulses = await response.json();
// //             pulseListContainer.innerHTML = ''; 

// //             if (pulses.length === 0) {
// //                 pulseListContainer.innerHTML = '<p class="loading">No pulses found.</p>';
// //                 return;
// //             }

// //             // Update both the sidebar and the map
// //             updateSidebar(pulses);
// //             updateMap(pulses);

// //         } catch (error) {
// //             console.error("Failed to fetch pulse list:", error);
// //             pulseListContainer.innerHTML = '<p class="loading">Error loading data.</p>';
// //         }
// //     }

// //     function updateSidebar(pulses) {
// //         pulses.forEach(pulse => {
// //             const pulseItem = document.createElement('div');
// //             pulseItem.className = 'pulse-item';
// //             pulseItem.dataset.pulseId = pulse.id;
// //             pulseItem.innerHTML = `
// //                 <h3>${pulse.title}</h3>
// //                 <div class="meta">
// //                     <span class="category-tag">${pulse.threat_category || 'General'}</span>
// //                     <span>${new Date(pulse.published_at).toLocaleDateString()}</span>
// //                 </div>
// //             `;
// //             pulseItem.addEventListener('click', () => fetchAndRenderPulseDetail(pulse.id));
// //             pulseListContainer.appendChild(pulseItem);
// //         });
// //     }

// //     function updateMap(pulses) {
// //         threatMarkers.clearLayers();
// //         pulses.forEach(pulse => {
// //             const countries = JSON.parse(pulse.targeted_countries || '[]');
// //             if (countries.length === 0) countries.push("Global");

// //             countries.forEach(countryName => {
// //                 const coords = countryCoords[countryName.trim()];
// //                 if (coords) {
// //                     const marker = L.circleMarker(coords, {
// //                         radius: 6, color: '#e83e8c', weight: 1.5,
// //                         fillColor: '#e83e8c', fillOpacity: 0.6
// //                     }).bindPopup(`<b>${pulse.title}</b>`);
                    
// //                     marker.on('mouseover', function (e) { this.openPopup(); });
// //                     marker.on('mouseout', function (e) { this.closePopup(); });
// //                     marker.on('click', () => fetchAndRenderPulseDetail(pulse.id));
                    
// //                     threatMarkers.addLayer(marker);
// //                 }
// //             });
// //         });
// //     }

// //     async function fetchAndRenderPulseDetail(pulseId) {
// //         if (activePulseId === pulseId) return;

// //         try {
// //             const response = await fetch(`/api/pulse/${pulseId}`);
// //             const pulse = await response.json();
            
// //             pulseDetailContainer.innerHTML = createPulseDetailHTML(pulse);
            
// //             if (activePulseId) {
// //                 document.querySelector(`.pulse-item[data-pulse-id='${activePulseId}']`)?.classList.remove('active');
// //             }
// //             document.querySelector(`.pulse-item[data-pulse-id='${pulseId}']`)?.classList.add('active');
// //             activePulseId = pulseId;

// //             // --- INTERACTIVE MAP UPDATE ---
// //             const countries = JSON.parse(pulse.targeted_countries || '[]');
// //             if (countries.length > 0) {
// //                 const primaryCountry = countries[0].trim();
// //                 const coords = countryCoords[primaryCountry];
// //                 if (coords) {
// //                     map.flyTo(coords, 5, { animate: true, duration: 1.5 }); // Zoom to location
// //                 }
// //             }

// //         } catch (error) {
// //             console.error("Failed to fetch pulse details:", error);
// //             pulseDetailContainer.innerHTML = `<div class="placeholder"><p>Error loading pulse details.</p></div>`;
// //         }
// //     }

// //     function createPulseDetailHTML(pulse) {
// //         const industries = JSON.parse(pulse.targeted_industries || '[]').map(ind => `<span class="tag industry">${ind}</span>`).join(' ');
// //         const countries = JSON.parse(pulse.targeted_countries || '[]').map(ctry => `<span class="tag country">${ctry}</span>`).join(' ');
// //         const categoryTag = `<span class="tag category">${pulse.threat_category || 'General'}</span>`;

// //         let indicatorsHTML = '<p>No indicators found for this pulse.</p>';
// //         if (pulse.indicators && pulse.indicators.length > 0) {
// //             indicatorsHTML = pulse.indicators.map(ioc => {
// //                 let enrichmentHTML = '';
// //                 const enrichmentData = JSON.parse(ioc.enrichment_data || '{}');
// //                 if (enrichmentData && enrichmentData.abuseConfidenceScore) {
// //                     enrichmentHTML = `<span class="ioc-enrichment">AbuseIPDB Score: ${enrichmentData.abuseConfidenceScore}%</span>`;
// //                 }
// //                 return `<div class="ioc-item">
// //                             <div><span class="ioc-type">${ioc.type.toUpperCase()}:</span> <span class="ioc-value">${ioc.value}</span></div>
// //                             ${enrichmentHTML}
// //                         </div>`;
// //             }).join('');
// //         }

// //         return `
// //             <div class="pulse-detail-view">
// //                 <h1>${pulse.title}</h1>
// //                 <div class="tags-container">
// //                     ${categoryTag}
// //                     ${countries}
// //                     ${industries}
// //                 </div>
// //                 <p class="summary">${pulse.summary || 'No summary available.'}</p>
// //                 <h2 class="section-title">Indicators of Compromise (IoCs)</h2>
// //                 <div id="indicators-list">${indicatorsHTML}</div>
// //                 <div class="source-link">
// //                     <a href="${pulse.url}" target="_blank">Read Full Report at ${pulse.source}</a>
// //                 </div>
// //             </div>`;
// //     }

// //     // --- Initial Load ---
// //     fetchAndRenderPulseList();
// // });
// document.addEventListener('DOMContentLoaded', function () {
//     const pulseListContainer = document.getElementById('pulse-list');
//     const pulseDetailContainer = document.getElementById('pulse-detail-container');
//     let activePulseId = null;

//     const countryCoords = { "USA": [39.8, -98.6], "United States": [39.8, -98.6], "Russia": [61.5, 105.3], "China": [35.9, 104.2], "Germany": [51.2, 10.5], "UK": [55.4, -3.4], "United Kingdom": [55.4, -3.4], "Brazil": [-14.2, -51.9], "India": [20.6, 78.9], "Australia": [-25.3, 133.8], "Canada": [56.1, -106.3], "France": [46.6, 1.9], "Iran": [32.4, 53.7], "North Korea": [40.3, 127.5], "Ukraine": [48.4, 31.2], "Spain": [40.4, -3.7], "Netherlands": [52.1, 5.3] };

//     const map = L.map('threat-map').setView([25, 10], 2);
//     L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; CARTO' }).addTo(map);
//     let threatMarkers = L.layerGroup().addTo(map);

//     async function fetchAndRenderPulseList() {
//         try {
//             const response = await fetch('/api/pulses');
//             const pulses = await response.json();
//             pulseListContainer.innerHTML = ''; 

//             if (pulses.length === 0) {
//                 pulseListContainer.innerHTML = '<p class="loading">No pulses found. Orchestrator may be running.</p>';
//                 return;
//             }
//             updateSidebar(pulses);
//             updateMap(pulses);

//         } catch (error) {
//             console.error("Failed to fetch pulse list:", error);
//             pulseListContainer.innerHTML = '<p class="loading">Error loading data.</p>';
//         }
//     }

//     function updateSidebar(pulses) {
//         pulses.forEach(pulse => {
//             const pulseItem = document.createElement('div');
//             // --- NEW: Add severity class for color-coding ---
//             pulseItem.className = `pulse-item severity-${(pulse.severity || 'low').toLowerCase()}`;
//             pulseItem.dataset.pulseId = pulse.id;
//             pulseItem.innerHTML = `
//                 <h3>${pulse.title}</h3>
//                 <div class="meta">
//                     <span class="category-tag">${pulse.threat_category || 'General'}</span>
//                     <span>${new Date(pulse.published_at).toLocaleDateString()}</span>
//                 </div>
//             `;
//             pulseItem.addEventListener('click', () => fetchAndRenderPulseDetail(pulse.id));
//             pulseListContainer.appendChild(pulseItem);
//         });
//     }

//     function updateMap(pulses) {
//         threatMarkers.clearLayers();
//         pulses.forEach(pulse => {
//             const countries = JSON.parse(pulse.targeted_countries || '[]');
//             // --- MODIFIED: Do not default to "Global" if list is empty ---
//             countries.forEach(countryName => {
//                 const coords = countryCoords[countryName.trim()];
//                 if (coords) {
//                     const marker = L.circleMarker(coords, {
//                         radius: 6, color: '#e83e8c', weight: 1.5,
//                         fillColor: '#e83e8c', fillOpacity: 0.6
//                     }).bindPopup(`<b>${pulse.title}</b>`);
//                     marker.on('mouseover', function (e) { this.openPopup(); });
//                     marker.on('mouseout', function (e) { this.closePopup(); });
//                     marker.on('click', () => fetchAndRenderPulseDetail(pulse.id));
//                     threatMarkers.addLayer(marker);
//                 }
//             });
//         });
//     }

//     async function fetchAndRenderPulseDetail(pulseId) {
//         // This function remains largely the same
//         if (activePulseId === pulseId) return;
//         try {
//             const response = await fetch(`/api/pulse/${pulseId}`);
//             const pulse = await response.json();
//             pulseDetailContainer.innerHTML = createPulseDetailHTML(pulse);
//             if (activePulseId) document.querySelector(`.pulse-item[data-pulse-id='${activePulseId}']`)?.classList.remove('active');
//             document.querySelector(`.pulse-item[data-pulse-id='${pulseId}']`)?.classList.add('active');
//             activePulseId = pulseId;
//             const countries = JSON.parse(pulse.targeted_countries || '[]');
//             if (countries.length > 0) {
//                 const primaryCountry = countries[0].trim();
//                 const coords = countryCoords[primaryCountry];
//                 if (coords) map.flyTo(coords, 5, { animate: true, duration: 1.5 });
//             }
//         } catch (error) {
//             console.error("Failed to fetch pulse details:", error);
//             pulseDetailContainer.innerHTML = `<div class="placeholder"><p>Error loading pulse details.</p></div>`;
//         }
//     }

//     function createPulseDetailHTML(pulse) {
//         // --- NEW: Add severity tag to the detail view ---
//         const industries = JSON.parse(pulse.targeted_industries || '[]').map(ind => `<span class="tag industry">${ind}</span>`).join(' ');
//         const countries = JSON.parse(pulse.targeted_countries || '[]').map(ctry => `<span class="tag country">${ctry}</span>`).join(' ');
//         const categoryTag = `<span class="tag category">${pulse.threat_category || 'General'}</span>`;
//         const severityTag = `<span class="tag severity-${(pulse.severity || 'low').toLowerCase()}">${pulse.severity || 'Low'}</span>`;

//         let indicatorsHTML = '<p>No indicators found for this pulse.</p>';
//         if (pulse.indicators && pulse.indicators.length > 0) {
//             indicatorsHTML = pulse.indicators.map(ioc => {
//                 let enrichmentHTML = '';
//                 const enrichmentData = JSON.parse(ioc.enrichment_data || '{}');
//                 if (enrichmentData && enrichmentData.abuseConfidenceScore) enrichmentHTML = `<span class="ioc-enrichment">AbuseIPDB Score: ${enrichmentData.abuseConfidenceScore}%</span>`;
//                 return `<div class="ioc-item"><div><span class="ioc-type">${ioc.type.toUpperCase()}:</span> <span class="ioc-value">${ioc.value}</span></div>${enrichmentHTML}</div>`;
//             }).join('');
//         }

//         return `<div class="pulse-detail-view"><h1>${pulse.title}</h1><div class="tags-container">${severityTag}${categoryTag}${countries}${industries}</div><p class="summary">${pulse.summary || 'No summary available.'}</p><h2 class="section-title">Indicators of Compromise (IoCs)</h2><div id="indicators-list">${indicatorsHTML}</div><div class="source-link"><a href="${pulse.url}" target="_blank">Read Full Report at ${pulse.source}</a></div></div>`;
//     }
//     fetchAndRenderPulseList();
// });
document.addEventListener('DOMContentLoaded', function () {
    // --- Element References ---
    const cardGridContainer = document.getElementById('card-grid-container');
    const paginationContainer = document.getElementById('pagination-container');
    const modal = document.getElementById('pulse-modal');
    const closeModalButton = document.querySelector('.close-button');
    const modalBody = document.getElementById('modal-body');

    // --- State Management ---
    let allPulses = [];
    let currentPage = 1;
    const itemsPerPage = 12;
    let knownPulseIds = new Set(); // For real-time updates

    // --- Geolocation & Map Setup (Expanded List) ---
    const countryCoords = {
        "USA": [39.8, -98.6], "United States": [39.8, -98.6],
        "China": [35.9, 104.2], "Russia": [61.5, 105.3],
        "Germany": [51.2, 10.5], "UK": [55.4, -3.4], "United Kingdom": [55.4, -3.4],
        "France": [46.6, 1.9], "Canada": [56.1, -106.3], "Australia": [-25.3, 133.8],
        "India": [20.6, 78.9], "Brazil": [-14.2, -51.9], "Japan": [36.2, 138.3],
        "South Korea": [35.9, 127.8], "North Korea": [40.3, 127.5],
        "Iran": [32.4, 53.7], "Israel": [31.0, 34.8], "Turkey": [38.9, 35.2],
        "Ukraine": [48.4, 31.2], "Poland": [51.9, 19.1],
        "Netherlands": [52.1, 5.3], "Belgium": [50.5, 4.5],
        "Spain": [40.4, -3.7], "Italy": [41.9, 12.6],
        "Taiwan": [23.7, 120.9], "Vietnam": [14.1, 108.3],
        "Singapore": [1.3, 103.8], "Malaysia": [4.2, 101.9],
        "Indonesia": [-0.8, 113.9], "Philippines": [12.9, 121.8],
        "South Africa": [-30.6, 22.9], "Nigeria": [9.1, 8.7],
        "Egypt": [26.8, 30.8], "Saudi Arabia": [23.9, 45.1], "UAE": [23.4, 53.8],
        "Mexico": [23.6, -102.5], "Colombia": [4.6, -74.1], "Argentina": [-38.4, -63.6],
        "Sweden": [60.1, 18.6], "Norway": [60.5, 8.5], "Finland": [61.9, 25.7],
        "Global": [20, 0] // Fallback
    };
    const map = L.map('threat-map').setView([25, 10], 2);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; CARTO' }).addTo(map);
    let threatMarkers = L.layerGroup().addTo(map);

    // --- Data Fetching ---
    async function fetchAndRenderUpdates() {
        try {
            const response = await fetch('/api/pulses');
            const newPulseData = await response.json();
            const newPulses = newPulseData.filter(pulse => !knownPulseIds.has(pulse.id));
            if (newPulses.length > 0) {
                console.log(`Found ${newPulses.length} new pulses. Updating view...`);
                allPulses = [...newPulses, ...allPulses];
                if (currentPage === 1) {
                    displayPage(1); // Re-render page 1 to show new items
                }
                updateMap(allPulses);
            }
        } catch (error) {
            console.error("Error during real-time update:", error);
        }
    }

    // --- UI Rendering ---
    function displayPage(page) {
        currentPage = page;
        cardGridContainer.innerHTML = '';
        const start = (page - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        const paginatedItems = allPulses.slice(start, end);

        if (allPulses.length === 0) {
            cardGridContainer.innerHTML = '<p class="col-span-full text-center text-xl mt-10">No threat intelligence data found. The backend service may be collecting data.</p>';
        } else {
            paginatedItems.forEach(pulse => {
                knownPulseIds.add(pulse.id);
                const cardElement = createThreatCardElement(pulse);
                cardGridContainer.appendChild(cardElement);
            });
        }
        renderPagination();
    }

    function createThreatCardElement(pulse) {
        const severity = pulse.severity || 'unprocessed';
        const category = pulse.threat_category || 'Unprocessed';
        const severityClasses = { critical: 'bg-red-600 text-white', high: 'bg-orange-500 text-white', medium: 'bg-yellow-400 text-gray-900', low: 'bg-green-500 text-white', unprocessed: 'bg-gray-500 text-white' };
        const cardElement = document.createElement('div');
        cardElement.className = "threat-card bg-gray-800 rounded-lg p-5 border border-gray-700 flex flex-col justify-between cursor-pointer hover:border-blue-500 hover:-translate-y-1 transition-transform duration-200 new-item-fade-in";
        cardElement.dataset.pulseId = pulse.id;
        cardElement.innerHTML = `<div><h2 class="text-lg font-semibold text-blue-400 mb-2 leading-tight">${pulse.title}</h2></div><div class="flex justify-between items-center mt-4 pt-4 border-t border-gray-700"><div class="flex items-center gap-2"><span class="px-3 py-1 text-xs font-bold rounded-full ${severityClasses[severity.toLowerCase()]}">${severity}</span><span class="px-3 py-1 text-xs font-semibold rounded-full bg-gray-600">${category}</span></div><span class="text-xs text-gray-400">${pulse.source}</span></div>`;
        cardElement.addEventListener('click', () => openPulseModal(pulse.id));
        return cardElement;
    }

    function renderPagination() {
        paginationContainer.innerHTML = '';
        const totalPages = Math.ceil(allPulses.length / itemsPerPage);
        if (totalPages <= 1) return;
        const createButton = (text, page, isDisabled = false) => {
            const button = document.createElement('button');
            button.className = `px-4 py-2 mx-1 bg-gray-700 rounded-md ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-600'}`;
            if (page === currentPage) button.classList.add('bg-blue-600', 'font-bold');
            button.innerText = text;
            button.disabled = isDisabled;
            if (!isDisabled) button.addEventListener('click', () => displayPage(page));
            return button;
        };
        paginationContainer.appendChild(createButton('Previous', currentPage - 1, currentPage === 1));
        paginationContainer.appendChild(createButton('Next', currentPage + 1, currentPage === totalPages));
    }

    function updateMap(pulses) {
        threatMarkers.clearLayers();
        const severityColors = { Critical: '#dc2626', High: '#f97316', Medium: '#ffc107', Low: '#28a745' };
        pulses.forEach(pulse => {
            try {
                const countries = JSON.parse(pulse.targeted_countries || '[]');
                countries.forEach(countryName => {
                    const coords = countryCoords[countryName.trim()];
                    if (coords) {
                        const color = severityColors[pulse.severity] || '#6b7280';
                        const marker = L.circleMarker(coords, { radius: 8, color, weight: 2, fillColor: color, fillOpacity: 0.7 }).bindPopup(`<b>${pulse.title}</b><br>Severity: ${pulse.severity}`);
                        marker.on('click', () => openPulseModal(pulse.id));
                        threatMarkers.addLayer(marker);
                    } else {
                        console.warn(`No coordinates found for country: ${countryName}`);
                    }
                });
            } catch (e) { /* ignore json parse errors */ }
        });
    }

    async function openPulseModal(pulseId) {
        try {
            const response = await fetch(`/api/pulse/${pulseId}`);
            if (!response.ok) throw new Error('Network response was not ok');
            const pulse = await response.json();
            
            const severity = pulse.severity || 'unprocessed';
            const severityClasses = { critical: 'bg-red-600 text-white', high: 'bg-orange-500 text-white', medium: 'bg-yellow-400 text-gray-900', low: 'bg-green-500 text-white', unprocessed: 'bg-gray-500 text-white' };
            
            const industries = (JSON.parse(pulse.targeted_industries || '[]')).map(ind => `<span class="px-3 py-1 text-sm font-semibold rounded-full bg-red-800 text-red-200">${ind}</span>`).join('');
            const countries = (JSON.parse(pulse.targeted_countries || '[]')).map(ctry => `<span class="px-3 py-1 text-sm font-semibold rounded-full bg-green-800 text-green-200">${ctry}</span>`).join('');
            
            let indicatorsHTML = '<p>No indicators found for this pulse.</p>';
            if (pulse.indicators && pulse.indicators.length > 0) {
                indicatorsHTML = pulse.indicators.map(ioc => {
                    return `<div class="flex justify-between py-1 border-b border-gray-700 last:border-b-0">
                                <strong class="text-yellow-400">${ioc.type.toUpperCase()}:</strong> 
                                <span>${ioc.value}</span>
                            </div>`;
                }).join('');
            }
            
            modalBody.innerHTML = `
                <h1 class="text-3xl font-bold text-blue-400 mb-4">${pulse.title}</h1>
                <div class="flex flex-wrap items-center gap-2 mb-6">
                    <span class="px-3 py-1 text-sm font-bold rounded-full ${severityClasses[severity.toLowerCase()]}">${severity}</span>
                    <span class="px-3 py-1 text-sm font-semibold rounded-full bg-purple-800 text-purple-200">${pulse.threat_category || 'General'}</span>
                    ${countries}
                    ${industries}
                </div>
                <p class="text-lg text-gray-300 mb-6 italic border-l-4 border-blue-500 pl-4">${pulse.summary || 'Summary not available.'}</p>
                <h2 class="text-2xl font-semibold mb-4 border-b border-gray-700 pb-2">Indicators of Compromise (IoCs)</h2>
                <div class="bg-gray-900 p-4 rounded-md font-mono text-sm max-h-60 overflow-y-auto">${indicatorsHTML}</div>
                <div class="mt-8">
                    <a href="${pulse.url}" target="_blank" rel="noopener noreferrer" class="inline-block bg-blue-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-blue-700 transition-colors">Read Full Report at ${pulse.source}</a>
                </div>
            `;
            modal.classList.remove('hidden');
        } catch (error) {
            console.error("Error fetching pulse details:", error);
            modalBody.innerHTML = '<p class="text-red-500">Error: Could not load pulse details.</p>';
            modal.classList.remove('hidden');
        }
    }

    closeModalButton.addEventListener('click', () => modal.classList.add('hidden'));
    window.addEventListener('click', (event) => { if (event.target == modal) { modal.classList.add('hidden'); }});

    // --- Initial Load & Real-Time Polling ---
    async function initialLoad() {
        try {
            const response = await fetch('/api/pulses');
            allPulses = await response.json();
            allPulses.forEach(p => knownPulseIds.add(p.id));
            displayPage(1);
        } catch (error) {
            console.error("Failed to perform initial load:", error);
            cardGridContainer.innerHTML = '<p class="col-span-full text-center text-xl mt-10 text-red-500">Error: Could not load threat intelligence data.</p>';
        } finally {
            updateMap(allPulses);
        }
    }
    
    initialLoad();
    setInterval(fetchAndRenderUpdates, 30000);
});