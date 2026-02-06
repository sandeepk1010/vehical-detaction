// ==================== GLOBAL VARIABLES ====================
let vehicleChart = null;
let distributionChart = null;
let currentTab = 'dashboard';

// ==================== TIME UPDATE ====================
function updateTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

setInterval(updateTime, 1000);
updateTime();

// ==================== TAB NAVIGATION ====================
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Remove active class from all links and tabs
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        
        // Add active class to clicked link and corresponding tab
        link.classList.add('active');
        const tabName = link.dataset.tab;
        document.getElementById(tabName + '-tab').classList.add('active');
        
        currentTab = tabName;
        
        // Load data for specific tabs
        if (tabName === 'events') {
            loadEvents();
        } else if (tabName === 'cameras') {
            loadCameras();
        } else if (tabName === 'datewise') {
            loadDateWiseData();
        }
    });
});

// ==================== FETCH STATISTICS ====================
async function loadStatistics() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        // Update stat cards
        document.getElementById('total-vehicles').textContent = stats.total_vehicles;
        document.getElementById('active-cameras').textContent = Object.keys(stats.cameras).length;
        document.getElementById('detections-today').textContent = stats.total_vehicles;
        
        // Load DB stats
        loadDatabaseStats();
        
        // Update charts
        updateCharts(stats);
        
        // Update top plates
        updateTopPlates(stats.top_plates);
        
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// ==================== DATABASE STATS ====================
async function loadDatabaseStats() {
    try {
        const response = await fetch('/api/db-stats');
        const stats = await response.json();
        
        document.getElementById('db-records').textContent = stats.total_vehicles || 0;
    } catch (error) {
        console.error('Error loading DB stats:', error);
    }
}

// ==================== SYNC JSON TO DATABASE ====================
document.getElementById('sync-btn')?.addEventListener('click', syncJsonToDatabase);

async function syncJsonToDatabase() {
    const btn = document.getElementById('sync-btn');
    const originalHTML = btn?.innerHTML;
    
    try {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
        btn.disabled = true;
        
        const response = await fetch('/api/db/sync', { method: 'POST' });
        const result = await response.json();
        
        alert(`✓ Synced ${result.synced} events to database`);
        
        // Reload statistics
        loadStatistics();
    } catch (error) {
        console.error('Error syncing:', error);
        alert('Error syncing to database');
    } finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}

// ==================== UPDATE CHARTS ====================
function updateCharts(stats) {
    const ctx1 = document.getElementById('camera-chart');
    const ctx2 = document.getElementById('distribution-chart');
    
    if (!ctx1 || !ctx2) return;
    
    const cameras = Object.keys(stats.cameras);
    const counts = Object.values(stats.cameras);
    
    // Bar Chart
    if (vehicleChart) {
        vehicleChart.data.labels = cameras;
        vehicleChart.data.datasets[0].data = counts;
        vehicleChart.update();
    } else {
        vehicleChart = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: cameras,
                datasets: [{
                    label: 'Vehicle Count',
                    data: counts,
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.7)',
                        'rgba(46, 204, 113, 0.7)',
                        'rgba(155, 89, 182, 0.7)',
                        'rgba(230, 126, 34, 0.7)'
                    ],
                    borderColor: [
                        'rgba(52, 152, 219, 1)',
                        'rgba(46, 204, 113, 1)',
                        'rgba(155, 89, 182, 1)',
                        'rgba(230, 126, 34, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Pie Chart
    if (distributionChart) {
        distributionChart.data.labels = cameras;
        distributionChart.data.datasets[0].data = counts;
        distributionChart.update();
    } else {
        distributionChart = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: cameras,
                datasets: [{
                    data: counts,
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.7)',
                        'rgba(46, 204, 113, 0.7)',
                        'rgba(155, 89, 182, 0.7)',
                        'rgba(230, 126, 34, 0.7)'
                    ],
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// ==================== UPDATE TOP PLATES ====================
function updateTopPlates(plates) {
    const container = document.getElementById('top-plates-list');
    
    if (!plates || Object.keys(plates).length === 0) {
        container.innerHTML = '<p class="loading">No data available</p>';
        return;
    }
    
    // Only show top 5 plates to avoid listing all plates
    const entries = Object.entries(plates).slice(0, 5);
    container.innerHTML = entries.map(([plate, count]) => `
        <div class="plate-card">
            <div class="plate-number">${plate}</div>
            <div class="plate-count">${count} detection${count > 1 ? 's' : ''}</div>
        </div>
    `).join('');
}

// ==================== LOAD EVENTS ====================
async function loadEvents() {
    try {
        const response = await fetch('/api/events?limit=50');
        const events = await response.json();
        const container = document.getElementById('events-list');
        const cameraFilter = document.getElementById('events-camera-filter')?.value || 'all';
        const searchQuery = document.getElementById('events-search-input')?.value?.toLowerCase() || '';
        
        // apply camera filter and search filter client-side
        let filtered = events;
        if (cameraFilter && cameraFilter !== 'all') {
            filtered = filtered.filter(e => e.camera === cameraFilter);
        }
        if (searchQuery) {
            filtered = filtered.filter(e => (e.plate || '').toLowerCase().includes(searchQuery) || (e.camera || '').toLowerCase().includes(searchQuery));
        }

        if (filtered.length === 0) {
            container.innerHTML = '<p class="loading">No events recorded</p>';
            return;
        }
        
        container.innerHTML = filtered.map((event, idx) => {
            const time = new Date(event.timestamp).toLocaleString();
            const plate = event.plate;
            const camera = event.camera;
            
            // Build image gallery
            let imagesHtml = '';
            
            // JSON images (from base64 data)
            if (event.json_images && event.json_images.length > 0) {
                imagesHtml += '<div class="event-images">';
                event.json_images.forEach(img => {
                    imagesHtml += `
                        <div class="image-thumbnail" title="${img.type}">
                            <img src="${img.url}" alt="${img.type}" onerror="this.src='/static/placeholder.jpg'">
                            <span class="image-label">${img.type}</span>
                        </div>
                    `;
                });
                imagesHtml += '</div>';
            }
            
            // File system images
            if (event.file_images && event.file_images.length > 0) {
                imagesHtml += '<div class="event-images">';
                event.file_images.forEach(img => {
                    imagesHtml += `
                        <div class="image-thumbnail">
                            <img src="${img.path}" alt="${img.name}" onerror="this.src='/static/placeholder.jpg'">
                            <span class="image-label">file</span>
                        </div>
                    `;
                });
                imagesHtml += '</div>';
            }
            
            return `
                <div class="event-item" data-camera="${camera}" data-plate="${plate}">
                    <div class="event-header">
                        <span class="event-time">${time}</span>
                        <span class="event-plate">${plate}</span>
                        <span class="event-camera">${camera}</span>
                        <span class="event-badge">Detected</span>
                    </div>
                    <div class="event-details">
                        <span class="detail-item"><strong>Vehicle:</strong> ${event.vehicle_color || 'Unknown'}</span>
                        <span class="detail-item"><strong>Plate:</strong> ${event.plate_color || 'Unknown'}</span>
                    </div>
                    ${imagesHtml}
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading events:', error);
        document.getElementById('events-list').innerHTML = '<p class="loading">Error loading events</p>';
    }
}

// ==================== LOAD CAMERAS ====================
async function loadCameras() {
    try {
        const response = await fetch('/api/cameras');
        const cameras = await response.json();
        const container = document.getElementById('cameras-list');
        
        container.innerHTML = Object.entries(cameras).map(([id, camera]) => `
            <div class="camera-card">
                <div class="camera-placeholder">
                    <i class="fas fa-video"></i>
                </div>
                <div class="camera-info">
                    <h3>${camera.name}</h3>
                    <div class="camera-detail">
                        <span>IP Address:</span>
                        <span>${camera.ip}</span>
                    </div>
                    <div class="camera-detail">
                        <span>Location:</span>
                        <span>${camera.location}</span>
                    </div>
                    <div class="camera-detail">
                        <span>Status:</span>
                        <span>
                            <span class="camera-status"></span>
                            ${camera.status}
                        </span>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Load camera statistics
        loadCameraStats();
        
    } catch (error) {
        console.error('Error loading cameras:', error);
        document.getElementById('cameras-list').innerHTML = '<p class="loading">Error loading cameras</p>';
    }
}

// ==================== LOAD CAMERA STATS ====================
async function loadCameraStats() {
    try {
        const response = await fetch('/api/camera-stats');
        const cameraStats = await response.json();
        const container = document.getElementById('camera-stats');
        
        container.innerHTML = Object.entries(cameraStats).map(([camera, stats]) => {
            const cameraName = camera === 'camera1' ? 'Camera 1' : 'Camera 2';
            const topPlatesHtml = stats.top_plates && Object.keys(stats.top_plates).length > 0
                ? `<div class="plate-list">
                        <div style="font-size: 13px; color: var(--text-light); margin-bottom: 8px; font-weight: 600;">Top License Plates:</div>
                        ${Object.entries(stats.top_plates).map(([plate, count]) => `
                            <div class="plate-item">
                                <span class="plate-name">${plate}</span>
                                <span class="plate-count">${count} detections</span>
                            </div>
                        `).join('')}
                    </div>`
                : '';
            
            return `
                <div class="camera-stat-card">
                    <h4>${cameraName}</h4>
                    <div class="stat-row">
                        <span class="stat-label">Total Detections:</span>
                        <span class="stat-value">${stats.total_detections || 0}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Unique Plates:</span>
                        <span class="stat-value">${stats.unique_plates || 0}</span>
                    </div>
                    ${topPlatesHtml}
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading camera stats:', error);
        document.getElementById('camera-stats').innerHTML = '<p class="loading">Error loading statistics</p>';
    }
}

// ==================== LOAD DATE WISE DATA ====================
async function loadDateWiseData() {
    try {
        const response = await fetch('/api/db/date-wise');
        const dateData = await response.json();
        
        const summaryDiv = document.getElementById('datewise-summary');
        const detailDiv = document.getElementById('datewise-detail');
        
        if (!dateData || dateData.length === 0) {
            summaryDiv.innerHTML = '<p class="info-text">No data available</p>';
            return;
        }
        
        // Show date cards
        summaryDiv.innerHTML = dateData.map((item, idx) => `
            <div class="date-card" onclick="showDateDetails('${item.date}')">
                <div class="date-header">
                    <span class="date-label">${formatDate(item.date)}</span>
                    <span class="date-count">${item.count} detections</span>
                </div>
                <div class="date-plates">
                    ${item.plates.slice(0, 5).map(plate => `<span class="plate-badge">${plate}</span>`).join('')}
                    ${item.plates.length > 5 ? `<span class="plate-badge">+${item.plates.length - 5}</span>` : ''}
                </div>
            </div>
        `).join('');
        
        detailDiv.innerHTML = '';
        
    } catch (error) {
        console.error('Error loading date-wise data:', error);
        document.getElementById('datewise-summary').innerHTML = '<p class="loading">Error loading data</p>';
    }
}

// ==================== SHOW DATE DETAILS ====================
async function showDateDetails(date) {
    try {
        const response = await fetch(`/api/db/date/${date}`);
        const data = await response.json();
        const detailDiv = document.getElementById('datewise-detail');
        
        detailDiv.innerHTML = `
            <div class="date-detail-section">
                <h3>
                    <i class="fas fa-calendar"></i> ${formatDate(date)} 
                    <span class="record-count">${data.total} Records</span>
                </h3>
                <div class="records-table">
                    ${data.records.map(record => `
                        <div class="record-row">
                            <span class="record-time">${new Date(record.created_at).toLocaleTimeString()}</span>
                            <span class="record-plate">${record.plate}</span>
                            <span class="record-camera">${record.camera}</span>
                            <span class="record-color">${record.plate_color || 'Unknown'}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading date details:', error);
    }
}

// ==================== HELPER FUNCTIONS ====================
function formatDate(dateStr) {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
}

// ==================== SEARCH PLATES ====================
document.getElementById('search-btn').addEventListener('click', searchPlates);
document.getElementById('plate-search-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchPlates();
});

async function searchPlates() {
    const query = document.getElementById('plate-search-input').value.trim().toUpperCase();
    const resultsDiv = document.getElementById('search-results');
    
    if (!query) {
        resultsDiv.innerHTML = '<p class="info-text">Enter a plate number to search...</p>';
        return;
    }
    
    try {
        resultsDiv.innerHTML = '<p class="loading">Searching...</p>';
        
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const results = await response.json();
        
        if (results.length === 0) {
            resultsDiv.innerHTML = `<p class="info-text">No results found for "${query}"</p>`;
            return;
        }
        
        resultsDiv.innerHTML = results.map(result => {
            const time = new Date(result.time).toLocaleString();
            
            // Build image gallery
            let imagesHtml = '';
            
            // JSON images
            if (result.json_images && result.json_images.length > 0) {
                imagesHtml += '<div class="search-images">';
                result.json_images.forEach(img => {
                    imagesHtml += `
                        <div class="search-image-thumbnail">
                            <img src="${img.url}" alt="${img.type}" onerror="this.src='/static/placeholder.jpg'">
                            <span>${img.type}</span>
                        </div>
                    `;
                });
                imagesHtml += '</div>';
            }
            
            // File images
            if (result.images && result.images.length > 0) {
                imagesHtml += '<div class="search-images">';
                result.images.forEach(img => {
                    imagesHtml += `
                        <div class="search-image-thumbnail">
                            <img src="${img.path}" alt="${img.name}" onerror="this.src='/static/placeholder.jpg'">
                            <span>file</span>
                        </div>
                    `;
                });
                imagesHtml += '</div>';
            }
            
            return `
                <div class="search-result-item">
                    <div class="result-header">
                        <p><strong>Plate:</strong> ${result.plate}</p>
                        <p><strong>Camera:</strong> ${result.camera}</p>
                        <p><strong>Time:</strong> ${time}</p>
                    </div>
                    <div class="result-details">
                        <p><strong>Vehicle:</strong> ${result.vehicle_color || 'Unknown'}</p>
                        <p><strong>Plate Color:</strong> ${result.plate_color || 'Unknown'}</p>
                    </div>
                    ${imagesHtml}
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error searching plates:', error);
        resultsDiv.innerHTML = '<p class="loading">Error during search</p>';
    }
}

// ==================== FILTER EVENTS ====================
document.getElementById('filter-camera').addEventListener('input', filterEvents);
document.getElementById('filter-plate').addEventListener('input', filterEvents);
document.getElementById('refresh-events').addEventListener('click', loadEvents);
// camera filter change triggers reload
document.getElementById('events-camera-filter')?.addEventListener('change', loadEvents);
document.getElementById('events-search-input')?.addEventListener('input', () => { /* debounce if needed */ loadEvents(); });

function filterEvents() {
    const cameraFilter = document.getElementById('filter-camera').value.toLowerCase();
    const plateFilter = document.getElementById('filter-plate').value.toUpperCase();
    
    document.querySelectorAll('.event-item').forEach(item => {
        const camera = item.querySelector('.event-camera').textContent.toLowerCase();
        const plate = item.querySelector('.event-plate').textContent;
        
        const cameraMatch = camera.includes(cameraFilter);
        const plateMatch = plate.includes(plateFilter);
        
        item.style.display = (cameraMatch && plateMatch) ? 'flex' : 'none';
    });
}

// ==================== INITIAL LOAD ====================
window.addEventListener('load', () => {
    loadStatistics();
    
    // Refresh statistics every 10 seconds
    setInterval(loadStatistics, 10000);
    
    // Refresh events if they're visible
    setInterval(() => {
        if (currentTab === 'events') {
            loadEvents();
        }
    }, 15000);
});
