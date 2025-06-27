// Dashboard state
let memoryChart = null;
let syncChart = null;
const memoryData = [];
const syncData = [];
let syncInProgress = false;

// Dark mode toggle functionality
function initializeDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const html = document.documentElement;
    const darkIcon = document.getElementById('darkModeIcon');
    const lightIcon = document.getElementById('lightModeIcon');
    
    // Check for saved dark mode preference or default to light mode
    const darkMode = localStorage.getItem('darkMode') === 'true';
    
    // Apply initial theme
    if (darkMode) {
        html.classList.add('dark');
        darkIcon.classList.remove('hidden');
        lightIcon.classList.add('hidden');
    } else {
        html.classList.remove('dark');
        darkIcon.classList.add('hidden');
        lightIcon.classList.remove('hidden');
    }
    
    // Toggle dark mode on button click
    darkModeToggle.addEventListener('click', () => {
        const isDark = html.classList.toggle('dark');
        localStorage.setItem('darkMode', isDark);
        
        // Toggle icons
        if (isDark) {
            darkIcon.classList.remove('hidden');
            lightIcon.classList.add('hidden');
        } else {
            darkIcon.classList.add('hidden');
            lightIcon.classList.remove('hidden');
        }
        
        // Update chart colors
        updateChartColors(isDark);
    });
}

// Update chart colors based on theme
function updateChartColors(isDark) {
    const textColor = isDark ? '#e5e7eb' : '#374151';
    const gridColor = isDark ? '#374151' : '#e5e7eb';
    
    if (memoryChart) {
        memoryChart.options.scales.x.ticks.color = textColor;
        memoryChart.options.scales.y.ticks.color = textColor;
        memoryChart.options.scales.x.grid.color = gridColor;
        memoryChart.options.scales.y.grid.color = gridColor;
        memoryChart.options.plugins.legend.labels.color = textColor;
        memoryChart.update();
    }
    
    if (syncChart) {
        syncChart.options.scales.x.ticks.color = textColor;
        syncChart.options.scales.y.ticks.color = textColor;
        syncChart.options.scales.x.grid.color = gridColor;
        syncChart.options.scales.y.grid.color = gridColor;
        syncChart.options.plugins.legend.labels.color = textColor;
        syncChart.update();
    }
    
    if (successRateChart) {
        successRateChart.options.scales.x.ticks.color = textColor;
        successRateChart.options.scales.y.ticks.color = textColor;
        successRateChart.options.scales.x.grid.color = gridColor;
        successRateChart.options.scales.y.grid.color = gridColor;
        successRateChart.update();
    }
}

// Initialize charts
function initializeCharts() {
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#e5e7eb' : '#374151';
    const gridColor = isDark ? '#374151' : '#e5e7eb';
    
    const chartConfig = {
        responsive: true,
        scales: {
            x: {
                ticks: { color: textColor },
                grid: { color: gridColor }
            },
            y: {
                beginAtZero: true,
                ticks: { color: textColor },
                grid: { color: gridColor }
            }
        },
        plugins: {
            legend: {
                labels: { color: textColor }
            }
        },
        animation: {
            duration: 750
        }
    };

    // Memory usage chart
    const memoryCtx = document.getElementById('memoryChart').getContext('2d');
    memoryChart = new Chart(memoryCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Memory Usage (MB)',
                data: [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: chartConfig
    });

    // Sync performance chart
    const syncCtx = document.getElementById('syncChart').getContext('2d');
    syncChart = new Chart(syncCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Issues/s',
                data: [],
                backgroundColor: 'rgb(59, 130, 246)'
            }]
        },
        options: chartConfig
    });
}

// Update status display
function updateStatus(status) {
    const statusElement = document.getElementById('syncStatus');
    const progressBar = document.getElementById('syncProgress');
    statusElement.className = 'sync-status';
    
    if (status.sync_in_progress) {
        statusElement.textContent = 'Running';
        statusElement.className = 'px-3 py-1 text-sm font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
        document.getElementById('startSync').disabled = true;
        document.getElementById('forceSync').disabled = true;
        progressBar.classList.remove('hidden');
        syncInProgress = true;
    } else if (status.sync_stopped) {
        statusElement.textContent = 'Stopped';
        statusElement.className = 'px-3 py-1 text-sm font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
        document.getElementById('startSync').disabled = false;
        document.getElementById('forceSync').disabled = false;
        progressBar.classList.add('hidden');
        syncInProgress = false;
    } else {
        statusElement.textContent = 'Idle';
        statusElement.className = 'px-3 py-1 text-sm font-medium rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
        document.getElementById('startSync').disabled = false;
        document.getElementById('forceSync').disabled = false;
        progressBar.classList.add('hidden');
        syncInProgress = false;
    }

    // Update sync interval display
    document.getElementById('syncInterval').value = status.current_interval || 2;

    // Update last sync time if available
    if (status.last_sync) {
        const lastSync = new Date(status.last_sync);
        document.getElementById('syncDuration').textContent = 
            `${Math.round((new Date() - lastSync) / 1000)}s ago`;
    }
}

// Update metrics display
function updateMetrics(status) {
    // Update memory usage
    const memoryMB = Math.round(status.memory.rss_bytes / 1024 / 1024);
    document.getElementById('memoryUsage').textContent = `${memoryMB} MB`;
    
    // Update memory chart
    const timestamp = new Date().toLocaleTimeString();
    memoryData.push({
        time: timestamp,
        value: memoryMB
    });
    
    if (memoryData.length > 20) memoryData.shift();
    
    memoryChart.data.labels = memoryData.map(d => d.time);
    memoryChart.data.datasets[0].data = memoryData.map(d => d.value);
    memoryChart.update();

    // Update sync performance if we have data
    if (status.sync_stats) {
        const { issues_per_second = 0 } = status.sync_stats;
        
        syncData.push({
            time: timestamp,
            value: issues_per_second
        });
        
        if (syncData.length > 20) syncData.shift();
        
        syncChart.data.labels = syncData.map(d => d.time);
        syncChart.data.datasets[0].data = syncData.map(d => d.value);
        syncChart.update();
    }

    // Update progress bar if sync is in progress
    if (status.sync_progress !== null && status.sync_progress !== undefined) {
        const progressBar = document.querySelector('#syncProgress > div');
        if (progressBar) {
            progressBar.style.width = `${status.sync_progress}%`;
            progressBar.textContent = `${Math.round(status.sync_progress)}%`;
            document.getElementById('syncProgress').classList.remove('hidden');
        }
    } else {
        document.getElementById('syncProgress').classList.add('hidden');
    }

    // Update total issues processed
    if (status.total_issues_processed !== undefined) {
        document.getElementById('issuesProcessed').textContent = status.total_issues_processed.toLocaleString();
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const container = document.createElement('div');
    container.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg text-white ${
        type === 'error' ? 'bg-red-500' : 
        type === 'success' ? 'bg-green-500' : 
        'bg-blue-500'
    }`;
    container.textContent = message;
    document.body.appendChild(container);
    setTimeout(() => container.remove(), 3000);
}

// API request handler with error handling
async function makeRequest(url, method = 'GET', body = null) {
    try {
        const options = {
            method,
            headers: method === 'POST' ? { 'Content-Type': 'application/json' } : {}
        };
        if (body) {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(url, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

// Fetch status from API
async function fetchStatus() {
    try {
        const status = await makeRequest('/api/status');
        updateStatus(status);
        updateMetrics(status);
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

// Sync History Functions
let successRateChart = null;

async function fetchSyncHistory() {
    try {
        const response = await fetch('/api/sync/history?per_page=10');
        const data = await response.json();
        
        if (response.ok) {
            updateSyncHistoryTable(data.syncs);
        }
    } catch (error) {
        console.error('Error fetching sync history:', error);
    }
}

async function fetchSyncStats() {
    try {
        const response = await fetch('/api/sync/stats?days=7');
        const data = await response.json();
        
        if (response.ok) {
            updateSyncStats(data);
        }
    } catch (error) {
        console.error('Error fetching sync stats:', error);
    }
}

function updateSyncHistoryTable(syncs) {
    const tbody = document.getElementById('syncHistoryTable');
    const loading = document.getElementById('syncHistoryLoading');
    const empty = document.getElementById('syncHistoryEmpty');
    
    loading.classList.add('hidden');
    
    if (!syncs || syncs.length === 0) {
        tbody.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    
    empty.classList.add('hidden');
    tbody.innerHTML = syncs.map(sync => {
        const status = sync.status || 'Unknown';
        const statusClass = status === 'Success' ? 'text-green-600 dark:text-green-400' : 
                          status === 'Failed' ? 'text-red-600 dark:text-red-400' : 
                          'text-gray-600 dark:text-gray-400';
        const statusIcon = status === 'Success' ? '✓' : 
                          status === 'Failed' ? '✗' : 
                          '○';
        
        const duration = sync.duration ? formatDuration(sync.duration) : '-';
        const records = sync.records_processed !== null ? sync.records_processed.toLocaleString() : '-';
        const time = sync.last_update_time ? formatRelativeTime(new Date(sync.last_update_time)) : '-';
        
        let rowHtml = `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer" onclick="toggleErrorRow(this)">
                <td class="px-3 py-4 whitespace-nowrap">
                    <span class="${statusClass} font-medium">${statusIcon}</span>
                </td>
                <td class="px-3 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                    ${sync.project_key || '-'}
                </td>
                <td class="px-3 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    ${duration}
                </td>
                <td class="px-3 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    ${records}
                </td>
                <td class="px-3 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    ${time}
                </td>
                <td class="px-3 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    ${sync.error_message ? '↓' : ''}
                </td>
            </tr>
        `;
        
        if (sync.error_message) {
            rowHtml += `
                <tr class="hidden bg-red-50 dark:bg-red-900/20">
                    <td colspan="6" class="px-3 py-4">
                        <div class="text-sm text-red-600 dark:text-red-400">
                            <strong>Error:</strong> ${sync.error_message}
                        </div>
                    </td>
                </tr>
            `;
        }
        
        return rowHtml;
    }).join('');
}

function updateSyncStats(stats) {
    // Update today's stats
    document.getElementById('todayTotal').textContent = stats.today.total;
    document.getElementById('todaySuccess').textContent = stats.today.successful;
    
    // Update average duration
    document.getElementById('avgDuration').textContent = formatDuration(stats.average_duration);
    
    // Update overall stats
    document.getElementById('overallSuccessRate').textContent = Math.round(stats.success_rate) + '%';
    document.getElementById('totalSyncsWeek').textContent = stats.total_syncs;
    
    // Update success rate chart
    updateSuccessRateChart(stats.syncs_by_day, stats.period_days);
}

function updateSuccessRateChart(syncsByDay, periodDays) {
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#e5e7eb' : '#374151';
    const gridColor = isDark ? '#374151' : '#e5e7eb';
    
    const ctx = document.getElementById('successRateChart').getContext('2d');
    
    // Generate labels for the last N days
    const labels = [];
    const data = [];
    const today = new Date();
    
    for (let i = periodDays - 1; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        const dayLabel = date.toLocaleDateString('en-US', { weekday: 'short' });
        
        labels.push(dayLabel);
        data.push(syncsByDay[dateStr] || 0);
    }
    
    if (successRateChart) {
        successRateChart.data.labels = labels;
        successRateChart.data.datasets[0].data = data;
        successRateChart.update();
    } else {
        successRateChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Syncs per Day',
                    data: data,
                    backgroundColor: 'rgba(59, 130, 246, 0.5)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        ticks: { color: textColor },
                        grid: { color: gridColor }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { 
                            color: textColor,
                            stepSize: 1
                        },
                        grid: { color: gridColor }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '-';
    
    if (seconds < 60) {
        return Math.round(seconds) + 's';
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.round(seconds % 60);
        return `${minutes}m ${secs}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

function formatRelativeTime(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
}

function toggleErrorRow(row) {
    const nextRow = row.nextElementSibling;
    if (nextRow && nextRow.classList.contains('bg-red-50')) {
        nextRow.classList.toggle('hidden');
    }
}

// Event Listeners
document.getElementById('startSync').addEventListener('click', async () => {
    try {
        showNotification('Starting sync...', 'info');
        await makeRequest('/api/sync/start', 'POST');
        showNotification('Sync started successfully', 'success');
        fetchStatus();
    } catch (error) {
        console.error('Error starting sync:', error);
    }
});

document.getElementById('stopSync').addEventListener('click', async () => {
    try {
        showNotification('Stopping sync...', 'info');
        await makeRequest('/api/sync/stop', 'POST');
        showNotification('Sync stopped successfully', 'success');
        fetchStatus();
    } catch (error) {
        console.error('Error stopping sync:', error);
    }
});

document.getElementById('forceSync').addEventListener('click', async () => {
    try {
        const button = document.getElementById('forceSync');
        button.disabled = true;
        button.textContent = 'Syncing...';
        
        showNotification('Starting force sync...', 'info');
        await makeRequest('/api/sync/force', 'POST');
        showNotification('Force sync completed successfully', 'success');
        
        button.textContent = 'Force Sync';
        button.disabled = false;
        fetchStatus();
    } catch (error) {
        console.error('Error forcing sync:', error);
        const button = document.getElementById('forceSync');
        button.textContent = 'Force Sync';
        button.disabled = false;
    }
});

document.getElementById('updateInterval').addEventListener('click', async () => {
    const interval = document.getElementById('syncInterval').value;
    try {
        showNotification('Updating sync interval...', 'info');
        await makeRequest('/api/interval', 'POST', { interval: parseInt(interval) });
        showNotification('Sync interval updated successfully', 'success');
        fetchStatus();
    } catch (error) {
        console.error('Error updating interval:', error);
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeDarkMode();
    initializeCharts();
    fetchStatus();
    fetchSyncHistory();
    fetchSyncStats();
    
    // Poll for updates every 2 seconds during sync, otherwise every 5 seconds
    setInterval(() => {
        fetchStatus();
    }, syncInProgress ? 2000 : 5000);
    
    // Update sync history every 30 seconds
    setInterval(() => {
        fetchSyncHistory();
        fetchSyncStats();
    }, 30000);
});