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

// Query history management
let queryHistory = JSON.parse(localStorage.getItem('jiraQueryHistory') || '[]');

function updateQueryHistory(issueKey) {
    // Remove if already exists and add to front
    queryHistory = queryHistory.filter(key => key !== issueKey);
    queryHistory.unshift(issueKey);
    
    // Keep only last 10 queries
    queryHistory = queryHistory.slice(0, 10);
    
    localStorage.setItem('jiraQueryHistory', JSON.stringify(queryHistory));
    renderQueryHistory();
}

function renderQueryHistory() {
    const historyContainer = document.getElementById('queryHistory');
    
    if (queryHistory.length === 0) {
        historyContainer.innerHTML = '<p class="text-gray-500 dark:text-gray-400">No recent queries</p>';
        return;
    }
    
    historyContainer.innerHTML = queryHistory.map(key => `
        <button 
            onclick="searchIssue('${key}')" 
            class="text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer"
        >
            ${key}
        </button>
    `).join(' • ');
}

// Search functionality
const searchBtn = document.getElementById('searchBtn');
const issueKeyInput = document.getElementById('issueKey');
const errorMessage = document.getElementById('errorMessage');
const resultsSection = document.getElementById('resultsSection');
const loadingSpinner = document.getElementById('loadingSpinner');
const instance1Results = document.getElementById('instance1Results');
const instance2Results = document.getElementById('instance2Results');
const noResults = document.getElementById('noResults');

searchBtn.addEventListener('click', () => {
    const issueKey = issueKeyInput.value.trim();
    if (issueKey) {
        searchIssue(issueKey);
    }
});

issueKeyInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const issueKey = issueKeyInput.value.trim();
        if (issueKey) {
            searchIssue(issueKey);
        }
    }
});

async function searchIssue(issueKey) {
    // Update input and history
    issueKeyInput.value = issueKey;
    updateQueryHistory(issueKey);
    
    // Reset UI
    errorMessage.classList.add('hidden');
    resultsSection.classList.remove('hidden');
    loadingSpinner.classList.remove('hidden');
    instance1Results.classList.add('hidden');
    instance2Results.classList.add('hidden');
    noResults.classList.add('hidden');
    
    // Disable search button
    searchBtn.disabled = true;
    searchBtn.textContent = 'Searching...';
    
    try {
        const response = await fetch(`/api/jira/issue/${encodeURIComponent(issueKey)}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch issue');
        }
        
        loadingSpinner.classList.add('hidden');
        
        // Display results
        let foundInAny = false;
        
        if (data.instance1) {
            foundInAny = true;
            displayIssueData('instance1', data.instance1);
        }
        
        if (data.instance2) {
            foundInAny = true;
            displayIssueData('instance2', data.instance2);
        }
        
        if (!foundInAny) {
            noResults.classList.remove('hidden');
        }
        
    } catch (error) {
        loadingSpinner.classList.add('hidden');
        errorMessage.textContent = error.message;
        errorMessage.classList.remove('hidden');
        resultsSection.classList.add('hidden');
    } finally {
        searchBtn.disabled = false;
        searchBtn.textContent = 'Search';
    }
}

function displayIssueData(instance, issueData) {
    const resultsContainer = document.getElementById(`${instance}Results`);
    const contentContainer = document.getElementById(`${instance}Content`);
    
    // Clear previous content
    contentContainer.innerHTML = '';
    
    // Basic info section
    const basicInfo = document.createElement('div');
    basicInfo.className = 'border-b border-gray-200 dark:border-gray-700 pb-4 mb-4';
    basicInfo.innerHTML = `
        <h4 class="font-semibold text-lg mb-2">${issueData.key} - ${escapeHtml(issueData.fields.summary || 'No summary')}</h4>
        <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
                <span class="font-medium">Type:</span> ${issueData.fields.issuetype?.name || 'N/A'}
            </div>
            <div>
                <span class="font-medium">Status:</span> 
                <span class="px-2 py-1 rounded text-xs font-medium ${getStatusColor(issueData.fields.status?.name)}">
                    ${issueData.fields.status?.name || 'N/A'}
                </span>
            </div>
            <div>
                <span class="font-medium">Priority:</span> ${issueData.fields.priority?.name || 'N/A'}
            </div>
            <div>
                <span class="font-medium">Reporter:</span> ${issueData.fields.reporter?.displayName || 'N/A'}
            </div>
            <div>
                <span class="font-medium">Assignee:</span> ${issueData.fields.assignee?.displayName || 'Unassigned'}
            </div>
            <div>
                <span class="font-medium">Created:</span> ${formatDate(issueData.fields.created)}
            </div>
        </div>
    `;
    contentContainer.appendChild(basicInfo);
    
    // Description
    if (issueData.fields.description) {
        const descSection = document.createElement('div');
        descSection.className = 'mb-4';
        descSection.innerHTML = `
            <h5 class="font-semibold mb-2">Description</h5>
            <div class="bg-gray-50 dark:bg-gray-700 p-3 rounded text-sm whitespace-pre-wrap">${escapeHtml(issueData.fields.description)}</div>
        `;
        contentContainer.appendChild(descSection);
    }
    
    // All fields (expandable)
    const allFieldsSection = document.createElement('div');
    allFieldsSection.className = 'mt-4';
    allFieldsSection.innerHTML = `
        <button onclick="toggleFields('${instance}')" class="font-semibold mb-2 text-indigo-600 dark:text-indigo-400 hover:underline">
            Show All Fields ▼
        </button>
        <div id="${instance}AllFields" class="hidden mt-2 space-y-2 text-sm">
            ${Object.entries(issueData.fields)
                .filter(([key, value]) => value !== null && value !== undefined)
                .map(([key, value]) => `
                    <div class="flex border-b border-gray-100 dark:border-gray-700 pb-1">
                        <span class="font-medium w-1/3">${key}:</span>
                        <span class="w-2/3 break-words">${formatFieldValue(value)}</span>
                    </div>
                `).join('')}
        </div>
    `;
    contentContainer.appendChild(allFieldsSection);
    
    // Show results
    resultsContainer.classList.remove('hidden');
}

function toggleFields(instance) {
    const fieldsContainer = document.getElementById(`${instance}AllFields`);
    fieldsContainer.classList.toggle('hidden');
    
    const button = fieldsContainer.previousElementSibling;
    if (fieldsContainer.classList.contains('hidden')) {
        button.textContent = 'Show All Fields ▼';
    } else {
        button.textContent = 'Hide All Fields ▲';
    }
}

function formatFieldValue(value) {
    if (typeof value === 'object' && value !== null) {
        if (Array.isArray(value)) {
            return value.map(v => formatFieldValue(v)).join(', ');
        }
        if (value.name) return value.name;
        if (value.displayName) return value.displayName;
        if (value.value) return value.value;
        return JSON.stringify(value, null, 2);
    }
    return escapeHtml(String(value));
}

function getStatusColor(status) {
    const statusLower = (status || '').toLowerCase();
    if (statusLower.includes('done') || statusLower.includes('closed')) {
        return 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100';
    } else if (statusLower.includes('progress')) {
        return 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100';
    } else if (statusLower.includes('blocked')) {
        return 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100';
    }
    return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100';
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
renderQueryHistory();