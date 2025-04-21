// Dashboard state
let memoryChart = null;
let syncChart = null;
const memoryData = [];
const syncData = [];
let syncInProgress = false;

// Initialize charts
function initializeCharts() {
    const chartConfig = {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true
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
        statusElement.className = 'px-3 py-1 text-sm font-medium rounded-full bg-green-100 text-green-800';
        document.getElementById('startSync').disabled = true;
        document.getElementById('forceSync').disabled = true;
        progressBar.classList.remove('hidden');
        syncInProgress = true;
    } else if (status.sync_stopped) {
        statusElement.textContent = 'Stopped';
        statusElement.className = 'px-3 py-1 text-sm font-medium rounded-full bg-red-100 text-red-800';
        document.getElementById('startSync').disabled = false;
        document.getElementById('forceSync').disabled = false;
        progressBar.classList.add('hidden');
        syncInProgress = false;
    } else {
        statusElement.textContent = 'Idle';
        statusElement.className = 'px-3 py-1 text-sm font-medium rounded-full bg-gray-100 text-gray-800';
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
    initializeCharts();
    fetchStatus();
    // Poll for updates every 2 seconds during sync, otherwise every 5 seconds
    setInterval(() => {
        fetchStatus();
    }, syncInProgress ? 2000 : 5000);
});