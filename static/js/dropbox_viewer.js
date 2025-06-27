// Dark mode toggle
const darkModeToggle = document.getElementById('darkModeToggle');
const html = document.documentElement;

// Load dark mode preference
if (localStorage.getItem('darkMode') === 'true') {
    html.classList.add('dark');
}

darkModeToggle.addEventListener('click', () => {
    html.classList.toggle('dark');
    localStorage.setItem('darkMode', html.classList.contains('dark'));
});

// URL history management
let urlHistory = JSON.parse(localStorage.getItem('dropboxUrlHistory') || '[]');

function updateUrlHistory(url) {
    // Remove if already exists and add to front
    urlHistory = urlHistory.filter(u => u !== url);
    urlHistory.unshift(url);
    
    // Keep only last 10 URLs
    urlHistory = urlHistory.slice(0, 10);
    
    localStorage.setItem('dropboxUrlHistory', JSON.stringify(urlHistory));
    renderUrlHistory();
}

function renderUrlHistory() {
    const historyContainer = document.getElementById('recentUrls');
    
    if (urlHistory.length === 0) {
        historyContainer.innerHTML = '<p class="text-gray-500 dark:text-gray-400">No recent URLs</p>';
        return;
    }
    
    historyContainer.innerHTML = urlHistory.map(url => `
        <div class="flex items-center justify-between p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
            <button 
                onclick="fetchMetadata('${url}')" 
                class="text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer text-left truncate flex-1"
                title="${url}"
            >
                ${url.length > 60 ? url.substring(0, 60) + '...' : url}
            </button>
            <button 
                onclick="copyToClipboard('${url}')" 
                class="ml-2 p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                title="Copy URL"
            >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
            </button>
        </div>
    `).join('');
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('URL copied to clipboard', 'success');
    });
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg transition-all duration-300 ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } text-white`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Fetch functionality
const fetchBtn = document.getElementById('fetchBtn');
const urlInput = document.getElementById('dropboxUrl');
const errorMessage = document.getElementById('errorMessage');
const resultsSection = document.getElementById('resultsSection');
const loadingSpinner = document.getElementById('loadingSpinner');
const metadataResults = document.getElementById('metadataResults');
const fileListSection = document.getElementById('fileListSection');

fetchBtn.addEventListener('click', () => {
    const url = urlInput.value.trim();
    if (url) {
        fetchMetadata(url);
    }
});

urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const url = urlInput.value.trim();
        if (url) {
            fetchMetadata(url);
        }
    }
});

async function fetchMetadata(url) {
    // Update input and history
    urlInput.value = url;
    updateUrlHistory(url);
    
    // Reset UI
    errorMessage.classList.add('hidden');
    resultsSection.classList.remove('hidden');
    loadingSpinner.classList.remove('hidden');
    metadataResults.classList.add('hidden');
    fileListSection.classList.add('hidden');
    
    // Disable fetch button
    fetchBtn.disabled = true;
    fetchBtn.textContent = 'Fetching...';
    
    try {
        const response = await fetch(`/api/dropbox/metadata`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch metadata');
        }
        
        loadingSpinner.classList.add('hidden');
        displayMetadata(data);
        
    } catch (error) {
        loadingSpinner.classList.add('hidden');
        errorMessage.textContent = error.message;
        errorMessage.classList.remove('hidden');
        resultsSection.classList.add('hidden');
    } finally {
        fetchBtn.disabled = false;
        fetchBtn.textContent = 'Fetch Metadata';
    }
}

function displayMetadata(data) {
    const metadataContent = document.getElementById('metadataContent');
    const fileListContent = document.getElementById('fileListContent');
    
    // Display general metadata
    metadataContent.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="border-b border-gray-200 dark:border-gray-700 pb-2">
                <span class="font-medium text-gray-600 dark:text-gray-400">Share Type:</span>
                <span class="ml-2">${data.share_type || 'N/A'}</span>
            </div>
            <div class="border-b border-gray-200 dark:border-gray-700 pb-2">
                <span class="font-medium text-gray-600 dark:text-gray-400">Total Files:</span>
                <span class="ml-2">${data.file_count || 0}</span>
            </div>
            <div class="border-b border-gray-200 dark:border-gray-700 pb-2">
                <span class="font-medium text-gray-600 dark:text-gray-400">Total Size:</span>
                <span class="ml-2">${formatBytes(data.total_size || 0)}</span>
            </div>
            <div class="border-b border-gray-200 dark:border-gray-700 pb-2">
                <span class="font-medium text-gray-600 dark:text-gray-400">Folder Name:</span>
                <span class="ml-2">${data.folder_name || 'N/A'}</span>
            </div>
        </div>
    `;
    
    // Display file list if available
    if (data.files && data.files.length > 0) {
        const fileTable = `
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead>
                    <tr>
                        <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Name</th>
                        <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Type</th>
                        <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Size</th>
                        <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Modified</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                    ${data.files.map(file => `
                        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                            <td class="px-4 py-2 text-sm">${file.name}</td>
                            <td class="px-4 py-2 text-sm">${file.type}</td>
                            <td class="px-4 py-2 text-sm">${formatBytes(file.size)}</td>
                            <td class="px-4 py-2 text-sm">${formatDate(file.modified)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        fileListContent.innerHTML = fileTable;
        fileListSection.classList.remove('hidden');
    }
    
    // Display raw metadata in expandable section
    if (data.raw_metadata) {
        metadataContent.innerHTML += `
            <div class="mt-4">
                <button onclick="toggleRawMetadata()" class="font-semibold text-indigo-600 dark:text-indigo-400 hover:underline">
                    Show Raw Metadata ▼
                </button>
                <div id="rawMetadata" class="hidden mt-2">
                    <pre class="bg-gray-100 dark:bg-gray-700 p-4 rounded overflow-x-auto text-xs">${JSON.stringify(data.raw_metadata, null, 2)}</pre>
                </div>
            </div>
        `;
    }
    
    metadataResults.classList.remove('hidden');
}

function toggleRawMetadata() {
    const rawMetadata = document.getElementById('rawMetadata');
    rawMetadata.classList.toggle('hidden');
    
    const button = rawMetadata.previousElementSibling;
    if (rawMetadata.classList.contains('hidden')) {
        button.textContent = 'Show Raw Metadata ▼';
    } else {
        button.textContent = 'Hide Raw Metadata ▲';
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Initialize
renderUrlHistory();