//------------------------------------
//---------- UI enhanced JS ----------

// --- Safety utilities to prevent selector errors ---
function safeQuerySelector(selector) {
    try {
        if (!selector || selector === '#' || selector === '' || typeof selector !== 'string') {
            console.warn('Invalid selector provided:', selector);
            return null;
        }
        return document.querySelector(selector);
    } catch (error) {
        console.error('QuerySelector error with selector:', selector, error);
        return null;
    }
}

function safeQuerySelectorAll(selector) {
    try {
        if (!selector || selector === '#' || selector === '' || typeof selector !== 'string') {
            console.warn('Invalid selector provided:', selector);
            return [];
        }
        return document.querySelectorAll(selector);
    } catch (error) {
        console.error('QuerySelectorAll error with selector:', selector, error);
        return [];
    }
}

// Override global error handler to catch and silence querySelector errors temporarily
window.addEventListener('error', function(event) {
    if (event.error && event.error.message && 
        event.error.message.includes("'#' is not a valid selector")) {
        console.warn('Caught and handled invalid selector error:', event.error.message);
        event.preventDefault(); // Prevent the error from bubbling up
        return false;
    }
});

// Also override unhandled promise rejections for fetch errors
window.addEventListener('unhandledrejection', function(event) {
    if (event.reason && event.reason.message && 
        event.reason.message.includes("'#' is not a valid selector")) {
        console.warn('Caught and handled invalid selector in promise:', event.reason.message);
        event.preventDefault();
        return false;
    }
});

// --- Global chart instances (Backend Compatibility) - KEEP EXISTING LOGIC ---
if (!window.chartInstances) {
    window.chartInstances = {};
}

// --- Content Panel Management ---

function initializeSecurityDashboard() {
    console.log('🔐 Initializing security dashboard...');
    
    // Check if security dashboard is already initialized
    const securityContainer = document.getElementById('securityposture-content');
    if (!securityContainer) {
        console.error('Security posture container not found');
        return;
    }
    
    // If already has content, don't reinitialize
    if (securityContainer.children.length > 0 && !securityContainer.innerHTML.includes('Security dashboard will be dynamically loaded here')) {
        console.log('Security dashboard already initialized');
        return;
    }
    
    console.log('Creating new security dashboard instance...');
    
    // Initialize the enhanced security dashboard
    if (window.SecurityPostureDashboard) {
        try {
            // Create new security dashboard instance
            window.securityDashboard = new window.SecurityPostureDashboard();
            console.log('✅ Security dashboard initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize security dashboard:', error);
            
            // Fallback: create basic security content
            securityContainer.innerHTML = `
                <div class="flex items-center justify-center min-h-screen">
                    <div class="text-center">
                        <div class="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto mb-4"></div>
                        <h3 class="text-xl font-semibold text-white mb-2">Loading Security Dashboard...</h3>
                        <p class="text-slate-400">Initializing security posture analysis...</p>
                    </div>
                </div>
            `;
            
            // Try to load security dashboard after a short delay
            setTimeout(() => {
                if (window.SecurityPostureDashboard) {
                    try {
                        window.securityDashboard = new window.SecurityPostureDashboard();
                        console.log('✅ Security dashboard initialized on retry');
                    } catch (retryError) {
                        console.error('❌ Security dashboard initialization failed on retry:', retryError);
                    }
                }
            }, 1000);
        }
    } else {
        console.warn('⚠️ SecurityPostureDashboard class not available, showing loading state...');
        
        // Show loading state while waiting for security scripts to load
        securityContainer.innerHTML = `
            <div class="flex items-center justify-center min-h-screen">
                <div class="text-center">
                    <div class="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <h3 class="text-xl font-semibold text-white mb-2">Loading Security Components...</h3>
                    <p class="text-slate-400">Please wait while security modules are loading...</p>
                </div>
            </div>
        `;
        
        // Try to initialize when SecurityPostureDashboard becomes available
        const checkForSecurityDashboard = setInterval(() => {
            if (window.SecurityPostureDashboard) {
                clearInterval(checkForSecurityDashboard);
                try {
                    window.securityDashboard = new window.SecurityPostureDashboard();
                    console.log('✅ Security dashboard initialized after waiting for scripts');
                } catch (error) {
                    console.error('❌ Security dashboard initialization failed after waiting:', error);
                }
            }
        }, 500);
        
        // Stop trying after 10 seconds
        setTimeout(() => {
            clearInterval(checkForSecurityDashboard);
        }, 10000);
    }
}

function showContent(contentType, element) {
    // Hide all content panels (expanded selector to include both classes)
    document.querySelectorAll('.tab-content-panel, .content-section').forEach(panel => {
        panel.classList.add('hidden');
        panel.style.display = 'none';  // Explicitly set display none
    });
    
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active-nav-link');
    });
    
    // Show the selected content panel
    const targetPanel = document.getElementById(`${contentType}-content`);
    if (targetPanel) {
        targetPanel.classList.remove('hidden');
        targetPanel.style.display = 'block';  // Explicitly set display block
    }
    
    // Initialize security dashboard if security posture tab is selected
    if (contentType === 'securityposture') {
        initializeSecurityDashboard();
    }
    
    // Add active class to clicked nav link
    if (element) {
        element.classList.add('active-nav-link');
    }
    
    // Handle specific tab logic
    switch (contentType) {
        case 'dashboard':
            // Load dashboard data
            if (typeof loadDashboardData === 'function') {
                loadDashboardData();
            }
            break;
            
        case 'implementation':
            // Load implementation plan
            if (typeof loadImplementationPlan === 'function') {
                loadImplementationPlan();
            }
            break;
            
        case 'projectcontrols':
            // Load project controls when tab is activated
            if (typeof loadProjectControlsTab === 'function') {
                loadProjectControlsTab();
            }
            break;
            
        case 'alerts':
            // Load alerts data
            if (typeof loadAlertsData === 'function') {
                loadAlertsData();
            }
            break;
            
        case 'enterprise-metrics':
            // Load enterprise metrics data
            if (typeof window.EnterpriseMetrics !== 'undefined' && window.EnterpriseMetrics.loadData) {
                window.EnterpriseMetrics.loadData();
            }
            break;
            
        case 'securityposture':
            // Load security posture data with reinitialization
            console.log('Security Posture tab selected');
            // Reinitialize security dashboard when switching to it
            if (window.securityDashboard) {
                setTimeout(() => {
                    window.securityDashboard.loadSecurityOverview();
                }, 100);
            }
            break;
            
        case 'compliance':
            // Load compliance data
            console.log('Compliance tab selected');
            break;
            
        case 'vulnerabilities':
            // Load vulnerabilities data
            console.log('Vulnerabilities tab selected');
            break;
            
        default:
            console.log(`Tab ${contentType} selected`);
    }
}

// --- Keep ALL existing backend integration functions ---
function extractChartData(data, key) {
    if (!data) return [];
    return data[key] || data.values || data.data || [];
}

function extractChartLabels(data) {
    if (!data) return [];
    return data.labels || data.categories || [];
}

function destroyChart(chartId) {
    if (window.chartInstances && window.chartInstances[chartId]) {
        window.chartInstances[chartId].destroy();
        delete window.chartInstances[chartId];
    }
}

function hideChartLoading(chartId) {
    const loadingEl = document.getElementById(`${chartId}-loading`);
    const container = document.getElementById(chartId)?.closest('.chart-container');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
    if (container) {
        container.classList.add('chart-loaded');
    }
}

function showChartLoading(chartId) {
    const loadingEl = document.getElementById(`${chartId}-loading`);
    const container = document.getElementById(chartId)?.closest('.chart-container');
    if (loadingEl) {
        loadingEl.style.display = 'flex';
    }
    if (container) {
        container.classList.remove('chart-loaded');
    }
}

// Keep ALL existing chart update functions
window.updateMainTrendChart = function(data) {
    const chartId = 'mainTrendChart';
    destroyChart(chartId);
    hideChartLoading(chartId);
    const canvas = document.getElementById(chartId);
    if (!canvas || !data) return;
    const ctx = canvas.getContext('2d');
    window.chartInstances[chartId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: extractChartLabels(data),
            datasets: [{
                label: 'Cost ($)',
                data: extractChartData(data, 'values'),
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'top' } },
            scales: {
                x: { title: { display: true, text: 'Time Period' } },
                y: { title: { display: true, text: 'Cost ($)' }, beginAtZero: true }
            }
        }
    });
};

window.updateCostBreakdownChart = function(data) {
    const chartId = 'costBreakdownChart';
    destroyChart(chartId);
    hideChartLoading(chartId);
    const canvas = document.getElementById(chartId);
    if (!canvas || !data) return;
    const ctx = canvas.getContext('2d');
    window.chartInstances[chartId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: extractChartLabels(data),
            datasets: [{
                data: extractChartData(data, 'values'),
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'bottom' } }
        }
    });
};

window.updateSavingsBreakdownChart = function(data) {
    const chartId = 'savingsBreakdownChart';
    destroyChart(chartId);
    hideChartLoading(chartId);
    const canvas = document.getElementById(chartId);
    if (!canvas || !data) return;
    const ctx = canvas.getContext('2d');
    window.chartInstances[chartId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels || [],
            datasets: [{
                data: data.values || data.data || [],
                backgroundColor: ['#28a745', '#17a2b8', '#ffc107', '#6f42c1', '#e83e8c', '#fd7e14']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'bottom' } }
        }
    });
};

window.updateNodeUtilizationChart = function(data) {
    const chartId = 'nodeUtilizationChart';
    destroyChart(chartId);
    hideChartLoading(chartId);
    const canvas = document.getElementById(chartId);
    if (!canvas || !data) return;
    const ctx = canvas.getContext('2d');
    window.chartInstances[chartId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: 'CPU Utilization (%)',
                data: data.cpu || data.values || [],
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }, {
                label: 'Memory Utilization (%)',
                data: data.memory || [],
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'top' } },
            scales: {
                x: { title: { display: true, text: 'Nodes' } },
                y: { title: { display: true, text: 'Utilization (%)' }, beginAtZero: true, max: 100 }
            }
        }
    });
};

window.updateHpaComparisonChart = function(data) {
    const chartId = 'hpaComparisonChart';
    destroyChart(chartId);
    hideChartLoading(chartId);
    const canvas = document.getElementById(chartId);
    if (!canvas || !data) return;
    const ctx = canvas.getContext('2d');
    window.chartInstances[chartId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: 'Before HPA',
                data: data.before || [],
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }, {
                label: 'After HPA',
                data: data.after || [],
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'top' } },
            scales: {
                x: { title: { display: true, text: 'Metrics' } },
                y: { title: { display: true, text: 'Value' }, beginAtZero: true }
            }
        }
    });
};

window.updateNamespaceCostChart = function(data) {
    const chartId = 'namespaceCostChart';
    destroyChart(chartId);
    hideChartLoading(chartId);
    const canvas = document.getElementById(chartId);
    if (!canvas || !data) return;
    const ctx = canvas.getContext('2d');
    window.chartInstances[chartId] = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels || [],
            datasets: [{
                data: data.values || data.data || [],
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF', '#4BC0C0']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'bottom' } }
        }
    });
};

window.updateWorkloadCostChart = function(data) {
    const chartId = 'workloadCostChart';
    destroyChart(chartId);
    hideChartLoading(chartId);
    const canvas = document.getElementById(chartId);
    if (!canvas || !data) return;
    const ctx = canvas.getContext('2d');
    window.chartInstances[chartId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: 'Cost ($)',
                data: data.values || data.data || [],
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { title: { display: true, text: 'Workloads' } },
                y: { title: { display: true, text: 'Cost ($)' }, beginAtZero: true }
            }
        }
    });
};

// Keep ALL existing backend integration functions
function showNotification(title, message, type = 'info', duration = 5000) {
    try {
        // Handle both old format (title, message) and new format (message only)
        let finalMessage = message ? `${title}: ${message}` : title;
        
        // Don't show notifications for selector errors - they're handled now
        if (finalMessage && (
            finalMessage.includes("'#' is not a valid selector") ||
            finalMessage.includes("An unexpected error occurred")
        )) {
            console.log('Suppressed notification for handled error:', finalMessage);
            return;
        }
        
        console.log(`${type.toUpperCase()}: ${finalMessage}`);
        const toastContainer = document.createElement('div');
        toastContainer.className = `fixed top-20 right-5 z-50`;
        const toast = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-500' : (type === 'error' ? 'bg-red-500' : 'bg-blue-500');
        toast.className = `p-4 rounded-lg shadow-lg text-white ${bgColor}`;
        toast.innerHTML = `<strong>${title}</strong><p>${message || ''}</p>`;
        toastContainer.appendChild(toast);
        document.body.appendChild(toastContainer);
        setTimeout(() => {
            if (toastContainer && toastContainer.parentNode) {
                toastContainer.remove();
            }
        }, duration);
    } catch (error) {
        console.error('Error showing notification:', error);
    }
}

// Safer navigation helper
window.switchToTab = function(tabSelector) {
    try {
        if (!tabSelector || tabSelector === '#') {
            console.warn('Invalid tab selector:', tabSelector);
            return;
        }
        
        // Extract content name from selector
        const contentName = tabSelector.replace('#', '').replace('-content', '');
        if (contentName) {
            const navLink = safeQuerySelector(`[onclick*="showContent('${contentName}'"]`);
            showContent(contentName, navLink);
        }
    } catch (error) {
        console.error('Error switching tabs:', error);
    }
};

function triggerAnalysis(clusterId) {
    console.log(`🚀 Triggering analysis for ${clusterId || 'demo cluster'}`);
    const analyzeButton = document.querySelector(`button[onclick*="triggerAnalysis"]`);
    if (analyzeButton) {
        analyzeButton.disabled = true;
        analyzeButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyzing...';
    }
    
    const targetClusterId = clusterId || 'demo';
    fetch(`/api/clusters/${targetClusterId}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: 30, enable_pod_analysis: true })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Analysis Started!', 'Analysis initiated successfully', 'success');
            pollAnalysisProgress(targetClusterId);
        } else {
            throw new Error(data.message || 'Failed to start analysis');
        }
    })
    .catch(error => {
        console.error('Analysis trigger error:', error);
        if (analyzeButton) {
            analyzeButton.disabled = false;
            analyzeButton.innerHTML = '<i class="fas fa-play mr-1"></i>Analyze';
        }
        showNotification('Analysis Failed', error.message, 'error');
    });
}

function pollAnalysisProgress(clusterId) {
const pollInterval = setInterval(() => {
    fetch(`/api/clusters/${clusterId}/analysis-status`)
        .then(response => response.json())
        .then(data => {
            if (data.analysis_status === 'completed' || data.analysis_status === 'success') {
                clearInterval(pollInterval);
                showNotification('Analysis Complete!', 'Analysis completed successfully', 'success');
                setTimeout(() => window.location.reload(), 2000);
            }
        })
        .catch(error => {
            console.error('Polling error:', error);
            clearInterval(pollInterval);
        });
}, 20000);
}

function deleteCurrentCluster(clusterId) {
    window.currentClusterToDelete = clusterId;
    document.getElementById('deleteCurrentClusterModal').classList.remove('hidden');
}

// Keep ALL existing backend functions
function exportClusterReport() { showNotification('Feature Coming Soon', 'Export feature is a work in progress.', 'info'); }
function compareWithOtherClusters() { showNotification('Feature Coming Soon', 'Cluster comparison feature is a work in progress.', 'info'); }

// Toggle theme function
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('preferred-theme', newTheme);
}

// Initialize theme from localStorage
function initializeTheme() {
    const preferredTheme = localStorage.getItem('preferred-theme') || 'light';
    document.documentElement.setAttribute('data-theme', preferredTheme);
}

// Keep ALL existing functions available globally
window.updateCpuWorkloadDisplay = window.updateCpuWorkloadDisplay || function(data) { console.log('CPU workload display updated', data); };
window.initializeCharts = window.initializeCharts || function() { console.log('Charts initialized'); };
window.refreshCharts = window.refreshCharts || function() { console.log('Charts refreshed'); };
window.updateAllCharts = window.updateAllCharts || function(data) { console.log('All charts updated', data); };

// Enhanced insights rendering function to override dynamic-insights.js
window.updateInsightsDisplay = function(insights) {
    console.log('🔧 Updating insights with compact bullet-point style');
    console.log('🔧 Received insights:', insights);
    console.log('🔧 Insight keys:', Object.keys(insights));
    
    const container = document.getElementById('insights-container');
    if (!container || !insights) return;
    
    let insightsHTML = '';
    let hasInsights = false;
    
    // Convert insights object to array of items
    const insightItems = [];
    Object.entries(insights).forEach(([key, value]) => {
        if (value && typeof value === 'string' && value.length > 10) {
            hasInsights = true;
            const title = key.replace(/([A-Z])/g, ' $1')
                                .replace(/_/g, ' ')
                                .replace(/\b\w/g, l => l.toUpperCase());
            
            const icon = getInsightIcon(key);
            const colorClass = getInsightColorClass(key);
            
            insightItems.push({
                title,
                content: value,
                icon,
                colorClass,
                key
            });
        }
    });
    
    if (hasInsights) {
        insightsHTML = '<div class="insights-list space-y-3">';
        insightItems.forEach(item => {
            insightsHTML += `
                <div class="insight-item border-${item.colorClass}" data-insight="${item.key}">
                    <h6>
                        <i class="fas fa-${item.icon} mr-2 text-${item.colorClass}"></i>
                        ${item.title}
                    </h6>
                    <p>${item.content}</p>
                </div>
            `;
        });
        insightsHTML += '</div>';
    } else {
        insightsHTML = `
            <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500 p-6 rounded-lg">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 bg-gradient.to-common-600 rounded-xl flex items-center justify-center">
                        <i class="fas fa-robot text-white text-xl"></i>
                    </div>
                    <div>
                        <h4 class="text-gray-800 font-semibold mb-2">AI Analysis Ready</h4>
                        <p class="text-gray-600">AI analysis will generate personalized insights here...</p>
                        <p class="text-sm text-gray-500 mt-1">Run an analysis to see optimization recommendations</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = insightsHTML;
};

// Helper functions for insights
function getInsightIcon(type) {
    const icons = {
        'rightsizing': 'expand-arrows-alt',
        'storage': 'hdd',
        'overall': 'chart-line',
        'cost': 'dollar-sign',
        'hpa': 'rocket',
        'performance': 'tachometer-alt',
        'security': 'shield-alt',
        'ml_classification': 'robot',
        'actions': 'tasks',
        'prediction': 'chart-area',
        'resource_balance': 'balance-scale',
        // Add missing insight keys (original 4)
        'cost_breakdown': 'chart-pie',
        'hpa_comparison': 'rocket',
        'resource_gap': 'expand-arrows-alt',
        'savings_summary': 'piggy-bank',
        // Add new 2 insights
        'operational_efficiency': 'cogs',
        'business_impact': 'briefcase'
    };
    return icons[type] || 'lightbulb';
}

function getInsightColorClass(type) {
    const colors = {
        'rightsizing': 'primary',
        'storage': 'info',
        'overall': 'success',
        'performance': 'warning',
        'security': 'danger',
        'cost': 'primary',
        'hpa': 'success',
        'ml_classification': 'info',
        'actions': 'warning',
        'prediction': 'success',
        'resource_balance': 'primary',
        // Add missing insight keys (original 4)
        'cost_breakdown': 'info',
        'hpa_comparison': 'success',
        'resource_gap': 'warning',
        'savings_summary': 'primary',
        // Add new 2 insights
        'operational_efficiency': 'info',
        'business_impact': 'primary'
    };
    return colors[type] || 'primary';
}

// Override the dynamic-insights function if it exists
if (typeof window.updateRealDynamicInsights === 'function') {
    const originalUpdateInsights = window.updateRealDynamicInsights;
    window.updateRealDynamicInsights = function(data) {
        try {
            // Call original function to get the insights
            originalUpdateInsights(data);
            
            // Then update with our compact display
            if (data && data.insights) {
                window.updateInsightsDisplay(data.insights);
            }
        } catch (error) {
            console.error('Error updating insights:', error);
        }
    };
}

// Initialize when DOM is ready - PRESERVE BACKEND INTEGRATION
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Enhanced KubeVista Dashboard...');
    
    try {
        initializeTheme();
        
        const defaultActiveLink = safeQuerySelector('.nav-link.active-nav-link');
        if (defaultActiveLink) {
            showContent('dashboard', defaultActiveLink);
        }
        
        // Call existing backend initialization if available
        setTimeout(() => {
            try {
                if (typeof window.initializeCharts === 'function') {
                    console.log('🔄 Calling existing backend chart initialization...');
                    window.initializeCharts();
                }
            } catch (error) {
                console.error('Error initializing charts:', error);
            }
        }, 100);
        
        // Setup form handlers with error handling
        try {
            const budgetAlertForm = safeQuerySelector('#budget-alert-form');
            if (budgetAlertForm) {
                budgetAlertForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    showNotification('Alert Created', 'Budget alert has been configured.', 'success');
                    this.reset();
                });
            }
        } catch (error) {
            console.error('Error setting up form handlers:', error);
        }
        
        // Setup delete confirmation with error handling
        try {
            const confirmDeleteBtn = safeQuerySelector('#confirmCurrentDeleteBtn');
            if (confirmDeleteBtn) {
                confirmDeleteBtn.addEventListener('click', function() {
                    if (window.currentClusterToDelete) {
                        const confirmBtn = this;
                        confirmBtn.disabled = true;
                        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Deleting...';
                        
                        fetch(`/cluster/${window.currentClusterToDelete}/remove`, { method: 'DELETE' })
                            .then(response => response.json())
                            .then(data => {
                                if (data.status === 'success') {
                                    showNotification('Cluster Deleted!', 'Cluster deleted successfully', 'success');
                                    setTimeout(() => window.location.href = '/', 1500);
                                } else {
                                    throw new Error(data.message || 'Failed to delete cluster');
                                }
                            })
                            .catch(error => {
                                showNotification('Delete Failed', `Failed to delete cluster: ${error.message}`, 'error');
                            })
                            .finally(() => {
                                confirmBtn.disabled = false;
                                confirmBtn.innerHTML = '<i class="fas fa-trash mr-2"></i>Delete Cluster';
                                const modal = safeQuerySelector('#deleteCurrentClusterModal');
                                if (modal) {
                                    modal.classList.add('hidden');
                                }
                            });
                    }
                });
            }
        } catch (error) {
            console.error('Error setting up delete confirmation:', error);
        }
        
        console.log('✅ Enhanced dashboard initialization complete - Backend ready');
        
    } catch (error) {
        console.error('❌ Critical error during dashboard initialization:', error);
        // Still try to show basic functionality
        try {
            if (typeof window.initializeCharts === 'function') {
                window.initializeCharts();
            }
        } catch (fallbackError) {
            console.error('Fallback initialization also failed:', fallbackError);
        }
    }
});