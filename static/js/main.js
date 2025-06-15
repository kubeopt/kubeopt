/**
 * ============================================================================
 * AKS COST INTELLIGENCE - MAIN DASHBOARD JAVASCRIPT
 * ============================================================================
 * Comprehensive cost optimization dashboard for Azure Kubernetes Service
 * Author: AKS Cost Intelligence Team
 * Version: 2.0.0
 * ============================================================================
 */

// ============================================================================
// GLOBAL VARIABLES & CONFIGURATION
// ============================================================================

const AppConfig = {
    API_BASE_URL: '/api',
    CHART_REFRESH_INTERVAL: 30000, // 30 seconds
    NOTIFICATION_DURATION: 5000,   // 5 seconds
    MIN_VALIDATION_LENGTH: 3
};

const AppState = {
    chartInstances: {},
    analysisCompleted: false,
    currentAnalysis: null,
    alerts: [],
    deployments: [],
    notifications: []
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Formats numeric values based on specified format type
 */
function formatValue(value, format) {
    const num = parseFloat(value) || 0;
    if (isNaN(num)) return '0';
    
    switch(format) {
        case 'currency':
            return '$' + Math.round(num).toLocaleString();
        case 'currency-monthly':
            return '$' + Math.round(num).toLocaleString() + '/mo';
        case 'percentage':
            return num.toFixed(1) + '%';
        case 'number':
            return Math.round(num).toString();
        default:
            return Math.round(num).toLocaleString();
    }
}

/**
 * Gets chart color scheme based on current theme
 */
function getChartColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        textColor: isDark ? '#f7fafc' : '#2d3748',
        gridColor: isDark ? '#4a5568' : '#e2e8f0',
        backgroundColor: isDark ? '#2d3748' : '#ffffff'
    };
}

/**
 * Calculates optimization score based on metrics
 */
function calculateOptimizationScore(metrics) {
    const savingsPercentage = metrics.savings_percentage || 0;
    const hpaReduction = metrics.hpa_reduction || 0;
    const cpuGap = metrics.cpu_gap || 0;
    const memoryGap = metrics.memory_gap || 0;
    
    const savingsScore = Math.min(100, savingsPercentage * 2);
    const efficiencyScore = Math.min(100, hpaReduction * 1.5);
    const utilizationScore = Math.max(0, 100 - (cpuGap + memoryGap) / 2);
    
    return Math.round(savingsScore * 0.4 + efficiencyScore * 0.3 + utilizationScore * 0.3);
}

/**
 * Debounce function to limit API calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copy text to clipboard with fallback support
 */
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Failed to copy:', err);
            showNotification('Failed to copy to clipboard', 'error');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showNotification('Copied to clipboard!', 'success');
        } catch (err) {
            console.error('Failed to copy:', err);
            showNotification('Failed to copy to clipboard', 'error');
        }
        document.body.removeChild(textArea);
    }
}

// Export utility functions immediately
window.copyToClipboard = copyToClipboard;

// ============================================================================
// NOTIFICATION SYSTEM
// ============================================================================

/**
 * Enhanced notification manager for user feedback
 */
class NotificationManager {
    constructor() {
        this.container = this.createContainer();
    }
    
    createContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    }
    
    show(message, type = 'info', duration = AppConfig.NOTIFICATION_DURATION) {
        const toastElement = document.createElement('div');
        toastElement.className = `toast align-items-center text-white bg-${this.getBootstrapColor(type)} border-0`;
        toastElement.setAttribute('role', 'alert');
        toastElement.setAttribute('aria-live', 'assertive');
        toastElement.setAttribute('aria-atomic', 'true');
        
        toastElement.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${this.getIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        this.container.appendChild(toastElement);
        
        if (window.bootstrap && bootstrap.Toast) {
            const toast = new bootstrap.Toast(toastElement, {
                autohide: duration > 0,
                delay: duration
            });
            toast.show();
            
            toastElement.addEventListener('hidden.bs.toast', () => {
                if (toastElement.parentNode) {
                    toastElement.parentNode.removeChild(toastElement);
                }
            });
        }
    }
    
    getBootstrapColor(type) {
        const colors = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'primary'
        };
        return colors[type] || 'primary';
    }
    
    getIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Initialize notification manager
const notificationManager = new NotificationManager();

/**
 * Global notification function for backward compatibility
 */
function showNotification(message, type = 'info', duration = AppConfig.NOTIFICATION_DURATION) {
    notificationManager.show(message, type, duration);
}

// Alias for existing code compatibility
const showToast = showNotification;

// Export notification functions immediately
window.showNotification = showNotification;
window.showToast = showToast;

// ============================================================================
// FORM VALIDATION
// ============================================================================

/**
 * Validates analysis form inputs
 */
function validateAnalysisForm() {
    const resourceGroup = document.getElementById('resource_group')?.value.trim();
    const clusterName = document.getElementById('cluster_name')?.value.trim();
    
    if (!resourceGroup || !clusterName) return false;
    
    // Clear previous validation styles
    document.querySelectorAll('.form-control').forEach(input => {
        input.classList.remove('is-invalid', 'is-valid');
    });
    
    let isValid = true;
    
    // Validate Resource Group
    const rgInput = document.getElementById('resource_group');
    if (rgInput) {
        if (resourceGroup.length < AppConfig.MIN_VALIDATION_LENGTH) {
            rgInput.classList.add('is-invalid');
            showNotification('Resource Group name must be at least 3 characters', 'error');
            isValid = false;
        } else {
            rgInput.classList.add('is-valid');
        }
    }
    
    // Validate Cluster Name
    const cnInput = document.getElementById('cluster_name');
    if (cnInput) {
        if (clusterName.length < AppConfig.MIN_VALIDATION_LENGTH) {
            cnInput.classList.add('is-invalid');
            showNotification('Cluster name must be at least 3 characters', 'error');
            isValid = false;
        } else {
            cnInput.classList.add('is-valid');
        }
    }
    
    return isValid;
}

/**
 * Sets up real-time input validation
 */
function setupInputValidation() {
    const resourceGroupInput = document.getElementById('resource_group');
    const clusterNameInput = document.getElementById('cluster_name');
    
    if (resourceGroupInput) {
        resourceGroupInput.addEventListener('input', function() {
            if (this.value.trim().length >= AppConfig.MIN_VALIDATION_LENGTH) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                if (this.value.trim().length > 0) {
                    this.classList.add('is-invalid');
                }
            }
        });
    }
    
    if (clusterNameInput) {
        clusterNameInput.addEventListener('input', function() {
            if (this.value.trim().length >= AppConfig.MIN_VALIDATION_LENGTH) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                if (this.value.trim().length > 0) {
                    this.classList.add('is-invalid');
                }
            }
        });
    }
}

// ============================================================================
// CLUSTER MANAGEMENT
// ============================================================================

/**
 * Handles add cluster form submission
 */
function handleAddClusterSubmission(event) {
    event.preventDefault();
    console.log('📝 Form submission started');
    
    const formData = new FormData(event.target);
    const clusterData = {
        cluster_name: formData.get('cluster_name'),
        resource_group: formData.get('resource_group'),
        environment: formData.get('environment') || 'development',
        region: formData.get('region') || '',
        description: formData.get('description') || ''
    };
    
    console.log('📋 Cluster data:', clusterData);
    
    // Validate required fields
    if (!clusterData.cluster_name || !clusterData.resource_group) {
        showNotification('Cluster name and resource group are required', 'error');
        return;
    }
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    if (!submitBtn) {
        console.error('❌ Submit button not found');
        return;
    }
    
    // Show loading state
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding...';
    submitBtn.disabled = true;
    
    console.log('📤 Sending API request...');
    
    // Make API call
    fetch(`${AppConfig.API_BASE_URL}/clusters`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(clusterData)
    })
    .then(response => {
        console.log('📡 API response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('✅ API success:', data);
        showNotification('Cluster added successfully!', 'success');
        
        // Close modal if exists
        const modalElement = document.getElementById('addClusterModal');
        if (modalElement && window.bootstrap) {
            const modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
            modal.hide();
        }
        
        // Reset form and reload
        event.target.reset();
        setTimeout(() => window.location.reload(), 1000);
    })
    .catch(error => {
        console.error('❌ Error:', error);
        showNotification('Error adding cluster: ' + error.message, 'error');
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

/**
 * Selects a cluster and navigates to its detail page
 */
function selectCluster(clusterId) {
    console.log('🎯 Selecting cluster:', clusterId);
    window.location.href = `/cluster/${clusterId}`;
}

/**
 * Analyzes a specific cluster
 */
function analyzeCluster(clusterId) {
    if (event) event.stopPropagation();
    console.log('🔍 Analyzing cluster:', clusterId);
    
    const button = event.target.closest('button');
    if (button) {
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        button.disabled = true;
    }
    
    fetch(`/cluster/${clusterId}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: 30, enable_pod_analysis: true })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Analysis completed successfully!', 'success');
            setTimeout(() => window.location.href = `/cluster/${clusterId}`, 1000);
        } else {
            throw new Error(data.message || 'Analysis failed');
        }
    })
    .catch(error => {
        console.error('❌ Analysis error:', error);
        showNotification('Analysis failed: ' + error.message, 'error');
    })
    .finally(() => {
        if (button) {
            button.innerHTML = '<i class="fas fa-play me-1"></i>Analyze Now';
            button.disabled = false;
        }
    });
}

/**
 * Removes a cluster after confirmation
 */
function removeCluster(clusterId) {
    if (event) event.stopPropagation();
    
    if (!confirm('Are you sure you want to remove this cluster? This will delete all analysis data.')) {
        return;
    }
    
    console.log('🗑️ Removing cluster:', clusterId);
    
    fetch(`/cluster/${clusterId}/remove`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Cluster removed successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            throw new Error(data.message || 'Failed to remove cluster');
        }
    })
    .catch(error => {
        console.error('❌ Remove error:', error);
        showNotification('Failed to remove cluster: ' + error.message, 'error');
    });
}

// Export cluster management functions immediately
window.selectCluster = selectCluster;
window.analyzeCluster = analyzeCluster;
window.removeCluster = removeCluster;

// ============================================================================
// ANALYSIS MANAGEMENT
// ============================================================================

/**
 * Handles analysis form submission with progress tracking
 */
function handleAnalysisSubmit(event) {
    event.preventDefault();
    
    if (!validateAnalysisForm()) return;
    
    console.log('📊 Form submitted for analysis');
    const btn = document.getElementById('analyzeBtn');
    const progress = document.getElementById('analysisProgress');
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');
    
    // Set loading state
    if (btn) {
        btn.classList.add('loading');
        btn.disabled = true;
    }
    if (progress) progress.classList.add('visible');

    // Progress steps
    const progressSteps = [
        { percentage: 10, text: 'Connecting to Azure...' },
        { percentage: 25, text: 'Fetching cost data...' },
        { percentage: 45, text: 'Analyzing cluster metrics...' },
        { percentage: 65, text: 'Calculating optimization opportunities...' },
        { percentage: 85, text: 'Generating insights...' },
        { percentage: 95, text: 'Finalizing analysis...' }
    ];
    
    let stepIndex = 0;
    function advanceProgress() {
        if (stepIndex < progressSteps.length && fill && text) {
            const step = progressSteps[stepIndex];
            fill.style.width = step.percentage + '%';
            text.textContent = step.text;
            stepIndex++;
            setTimeout(advanceProgress, 800);
        }
    }
    advanceProgress();

    // Submit analysis
    fetch('/analyze', { 
        method: 'POST', 
        body: new FormData(event.target) 
    })
    .then(response => {
        if (!response.ok) throw new Error(response.statusText);
        return response.text();
    })
    .then(() => {
        if (fill) fill.style.width = '100%';
        if (text) text.textContent = 'Analysis completed successfully!';
        
        AppState.analysisCompleted = true;
        
        setTimeout(() => {
            showNotification('Analysis completed! Found significant optimization opportunities.', 'success');
            setTimeout(() => {
                switchToTab('#dashboard');
                resetAnalysisForm();
                initializeCharts();
            }, 1500);
        }, 1000);
    })
    .catch(error => {
        console.error('❌ Analysis failed:', error);
        showNotification('Analysis failed: ' + error.message, 'error');
        resetAnalysisForm();
    });

    function resetAnalysisForm() {
        if (btn) {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
        if (progress) progress.classList.remove('visible');
        if (fill) fill.style.width = '0%';
        if (text) text.textContent = 'Initializing analysis...';
        stepIndex = 0;
    }
}

// ============================================================================
// CHART MANAGEMENT
// ============================================================================

/**
 * Initializes all dashboard charts
 */
function initializeCharts() {
    console.log('📊 Initializing charts...');
    
    fetch(`${AppConfig.API_BASE_URL}/chart-data`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            return response.json();
        })
        .then(data => {
            console.log('📈 Chart data received:', data);
            if (data.status !== 'success') {
                throw new Error(data.message || 'Unexpected response');
            }
            
            // Update metrics if available
            if (data.metrics) updateDashboardMetrics(data.metrics);
            
            // Create all charts
            createAllCharts(data);
            console.log('✅ Charts initialized successfully');
        })
        .catch(error => {
            console.error('❌ Chart init error:', error);
            showChartError('Unable to load chart data: ' + error.message);
        });
}

// Export chart functions immediately
window.initializeCharts = initializeCharts;

/**
 * Updates dashboard metrics with animation
 */
function updateDashboardMetrics(metrics) {
    console.log('📊 Updating metrics:', metrics);
    
    const metricUpdates = [
        { selectors: ['#current-cost'], value: metrics.total_cost, format: 'currency' },
        { selectors: ['#potential-savings'], value: metrics.total_savings, format: 'currency' },
        { selectors: ['#hpa-efficiency'], value: metrics.hpa_reduction, format: 'percentage' },
        { selectors: ['#optimization-score'], value: calculateOptimizationScore(metrics), format: 'number' },
        { selectors: ['#savings-percentage'], value: metrics.savings_percentage, format: 'percentage' },
        { selectors: ['#annual-savings'], value: metrics.annual_savings, format: 'currency' }
    ];
    
    metricUpdates.forEach((metric, index) => {
        animateMetricUpdate(metric, index * 100);
    });
    
    updateCostTrend(metrics);
    updateDataSourceIndicator(metrics);
}

/**
 * Animates metric value updates
 */
function animateMetricUpdate(metric, delay) {
    let element = null;
    
    // Find the first matching element
    for (const selector of metric.selectors) {
        element = document.querySelector(selector);
        if (element) break;
    }
    
    if (!element) return;

    setTimeout(() => {
        element.style.transition = 'all 0.3s';
        element.style.opacity = '0.5';
        element.style.transform = 'scale(0.9)';
        
        setTimeout(() => {
            const formattedValue = formatValue(metric.value, metric.format);
            element.textContent = formattedValue;
            element.style.opacity = '1';
            element.style.transform = 'scale(1)';
            
            // Add update indicator
            element.classList.add('metric-updated');
            setTimeout(() => element.classList.remove('metric-updated'), 2000);
        }, 300);
    }, delay);
}

/**
 * Updates cost trend indicator
 */
function updateCostTrend(metrics) {
    document.querySelectorAll('#cost-trend').forEach(element => {
        const percentage = metrics.savings_percentage || 0;
        if (percentage > 20) {
            element.innerHTML = '<i class="fas fa-arrow-down text-success"></i> High Savings Potential';
        } else if (percentage > 10) {
            element.innerHTML = '<i class="fas fa-arrow-down text-warning"></i> Moderate Savings';
        } else {
            element.innerHTML = '<i class="fas fa-minus text-info"></i> Limited Optimization';
        }
    });
}

/**
 * Updates data source indicator
 */
function updateDataSourceIndicator(metrics) {
    const isRealData = !metrics.is_sample_data;
    let indicator = document.querySelector('#data-source-indicator');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'data-source-indicator';
        indicator.className = 'data-source-indicator';
        (document.querySelector('#dashboard') || document.body).appendChild(indicator);
    }
    
    indicator.innerHTML = `
        <div class="data-source-badge ${isRealData ? 'real-data' : 'sample-data'}">
            <i class="fas fa-${isRealData ? 'cloud' : 'flask'}"></i>
            <span>${isRealData ? 'Live Azure Data' : 'Demo Mode'}</span>
            <small>${metrics.data_source || ''}</small>
        </div>
    `;
}

/**
 * Creates all charts from provided data
 */
function createAllCharts(data) {
    console.log('🎨 Creating all charts...');
    
    try {
        destroyAllCharts();
        
        const metadata = data.metadata || {};
        const isRealData = metadata.is_real_data === true || 
                          metadata.force_real_data === true ||
                          parseFloat(metadata.total_cost_verification?.replace(/[^0-9.]/g, '') || '0') > 100;

        // Create individual charts
        if (data.costBreakdown?.values?.length) {
            createCostBreakdownChart(data.costBreakdown, isRealData);
        }
        
        if (data.hpaComparison) {
            createHPAComparisonChart(data.hpaComparison, isRealData);
        }
        
        if (data.nodeUtilization) {
            createNodeUtilizationChart(data.nodeUtilization, isRealData);
        }
        
        if (data.savingsBreakdown) {
            createSavingsBreakdownChart(data.savingsBreakdown, isRealData);
        }
        
        if (data.trendData?.labels && data.trendData?.datasets) {
            createMainTrendChart(data.trendData, isRealData);
        }
        
        if (data.podCostBreakdown?.labels?.length) {
            createNamespaceCostChart(data.podCostBreakdown);
            const podSection = document.getElementById('pod-cost-section');
            if (podSection) podSection.style.display = 'block';
        }
        
        if (data.workloadCosts?.workloads?.length > 0) {
            createWorkloadCostChart(data.workloadCosts);
        }
        
        if (data.insights) {
            updateInsights(data.insights);
        }
        
        // Update pod cost metrics if available
        if (data.namespaceDistribution || data.workloadCosts || data.podCostBreakdown) {
            updatePodCostMetrics(data);
        }
        
        console.log('✅ All charts creation completed');
        
    } catch (error) {
        console.error('❌ Error building charts:', error);
        showChartError('Failed to render charts: ' + error.message);
    }
}

/**
 * Destroys all existing chart instances
 */
function destroyAllCharts() {
    const chartIds = [
        'mainTrendChart', 'costBreakdownChart', 'hpaComparisonChart', 
        'nodeUtilizationChart', 'savingsBreakdownChart', 'savingsProjectionChart',
        'namespaceCostChart', 'workloadCostChart'
    ];
    
    chartIds.forEach(id => {
        const canvas = document.getElementById(id);
        if (canvas && AppState.chartInstances[id]) {
            AppState.chartInstances[id].destroy();
            delete AppState.chartInstances[id];
        }
    });
}

/**
 * Creates cost breakdown chart
 */
function createCostBreakdownChart(data, isRealData) {
    const canvas = document.getElementById('costBreakdownChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();
    
    const filteredData = data.labels.map((label, index) => ({
        label: label,
        value: data.values[index] || 0
    })).filter(item => item.value > 0);

    if (filteredData.length === 0) {
        canvas.parentElement.innerHTML = '<div class="text-center text-muted p-4">No cost data available</div>';
        return;
    }

    const config = {
        type: 'doughnut',
        data: {
            labels: filteredData.map(item => item.label),
            datasets: [{
                data: filteredData.map(item => item.value),
                backgroundColor: ['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6', '#1abc9c', '#95a5a6'],
                borderWidth: 2,
                borderColor: colors.backgroundColor,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: colors.textColor,
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };

    AppState.chartInstances['costBreakdownChart'] = new Chart(ctx, config);
}

/**
 * Creates main trend chart
 */
function createMainTrendChart(data, isRealData) {
    const canvas = document.getElementById('mainTrendChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const datasets = (data.datasets || []).map((dataset, index) => ({
        label: dataset.name,
        data: dataset.data,
        borderColor: index === 0 ? '#e74c3c' : '#2ecc71',
        backgroundColor: index === 0 ? 'rgba(231, 76, 60, 0.1)' : 'rgba(46, 204, 113, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4
    }));

    const config = {
        type: 'line',
        data: {
            labels: data.labels || [],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: colors.textColor } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: colors.textColor },
                    grid: { color: colors.gridColor }
                },
                y: {
                    ticks: {
                        color: colors.textColor,
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: { color: colors.gridColor }
                }
            }
        }
    };

    AppState.chartInstances['mainTrendChart'] = new Chart(ctx, config);
}

/**
 * Creates HPA comparison chart
 */
function createHPAComparisonChart(data, isRealData) {
    const canvas = document.getElementById('hpaComparisonChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const config = {
        type: 'bar',
        data: {
            labels: data.timePoints || [],
            datasets: [
                {
                    label: 'CPU-based HPA',
                    data: data.cpuReplicas || [],
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderColor: '#e74c3c',
                    borderWidth: 2
                },
                {
                    label: 'Memory-based HPA',
                    data: data.memoryReplicas || [],
                    backgroundColor: 'rgba(46, 204, 113, 0.7)',
                    borderColor: '#2ecc71',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: colors.textColor } }
            },
            scales: {
                x: {
                    ticks: { color: colors.textColor },
                    grid: { color: colors.gridColor }
                },
                y: {
                    ticks: { color: colors.textColor },
                    grid: { color: colors.gridColor },
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Replica Count',
                        color: colors.textColor
                    }
                }
            }
        }
    };

    AppState.chartInstances['hpaComparisonChart'] = new Chart(ctx, config);
}

/**
 * Creates node utilization chart
 */
function createNodeUtilizationChart(data, isRealData) {
    const canvas = document.getElementById('nodeUtilizationChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const config = {
        type: 'bar',
        data: {
            labels: data.nodes || [],
            datasets: [
                {
                    label: 'CPU Request',
                    data: data.cpuRequest || [],
                    backgroundColor: 'rgba(52, 152, 219, 0.3)',
                    borderColor: '#3498db',
                    borderWidth: 2
                },
                {
                    label: 'CPU Actual',
                    data: data.cpuActual || [],
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderColor: '#e74c3c',
                    borderWidth: 2
                },
                {
                    label: 'Memory Request',
                    data: data.memoryRequest || [],
                    backgroundColor: 'rgba(155, 89, 182, 0.3)',
                    borderColor: '#9b59b6',
                    borderWidth: 2
                },
                {
                    label: 'Memory Actual',
                    data: data.memoryActual || [],
                    backgroundColor: 'rgba(46, 204, 113, 0.7)',
                    borderColor: '#2ecc71',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: colors.textColor } }
            },
            scales: {
                x: {
                    ticks: { color: colors.textColor },
                    grid: { color: colors.gridColor }
                },
                y: {
                    ticks: {
                        color: colors.textColor,
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: { color: colors.gridColor },
                    max: 100,
                    title: {
                        display: true,
                        text: 'Utilization %',
                        color: colors.textColor
                    }
                }
            }
        }
    };

    AppState.chartInstances['nodeUtilizationChart'] = new Chart(ctx, config);
}

/**
 * Creates savings breakdown chart
 */
function createSavingsBreakdownChart(data, isRealData) {
    const canvas = document.getElementById('savingsBreakdownChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const config = {
        type: 'pie',
        data: {
            labels: data.categories || [],
            datasets: [{
                data: data.values || [],
                backgroundColor: ['#3498db', '#e74c3c', '#2ecc71'],
                borderWidth: 2,
                borderColor: colors.backgroundColor
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: colors.textColor,
                        padding: 10,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: $${context.parsed.toLocaleString()}`;
                        }
                    }
                }
            }
        }
    };

    AppState.chartInstances['savingsBreakdownChart'] = new Chart(ctx, config);
}

/**
 * Creates namespace cost chart
 */
function createNamespaceCostChart(data) {
    const canvas = document.getElementById('namespaceCostChart');
    if (!canvas || !data?.labels?.length) {
        const podSection = document.getElementById('pod-cost-section');
        if (podSection) podSection.style.display = 'none';
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const namespaceColors = [
        '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
        '#1abc9c', '#95a5a6', '#34495e', '#e67e22', '#16a085'
    ];

    const config = {
        type: 'doughnut',
        data: {
            labels: data.labels || [],
            datasets: [{
                data: data.values || [],
                backgroundColor: namespaceColors,
                borderWidth: 2,
                borderColor: colors.backgroundColor,
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: colors.textColor,
                        padding: 15,
                        usePointStyle: true,
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    return {
                                        text: `${label}: $${value.toLocaleString()} (${percentage}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };

    AppState.chartInstances['namespaceCostChart'] = new Chart(ctx, config);
    
    // Update analysis badge
    const badge = document.getElementById('pod-analysis-badge');
    if (badge) {
        badge.textContent = `${data.analysis_method || 'Unknown'} - ${data.accuracy_level || 'Unknown'} Accuracy`;
        badge.className = `badge ${getAccuracyBadgeClass(data.accuracy_level)}`;
    }
    
    console.log('✅ Namespace cost chart created');
}

/**
 * Creates workload cost chart
 */
function createWorkloadCostChart(data) {
    const canvas = document.getElementById('workloadCostChart');
    if (!canvas || !data) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const typeColors = {
        'Deployment': '#3498db',
        'StatefulSet': '#e74c3c', 
        'DaemonSet': '#2ecc71',
        'ReplicaSet': '#f39c12',
        'Job': '#9b59b6',
        'CronJob': '#1abc9c'
    };

    const backgroundColors = data.types.map(type => typeColors[type] || '#95a5a6');

    const config = {
        type: 'bar',
        data: {
            labels: data.workloads.map(w => w.split('/')[1] || w),
            datasets: [{
                label: 'Monthly Cost',
                data: data.costs || [],
                backgroundColor: backgroundColors,
                borderColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const index = context[0].dataIndex;
                            return `${data.types[index]}: ${data.workloads[index]}`;
                        },
                        label: function(context) {
                            const index = context.dataIndex;
                            return [
                                `Cost: $${context.parsed.x.toLocaleString()}/month`,
                                `Namespace: ${data.namespaces[index]}`,
                                `Replicas: ${data.replicas[index]}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: colors.textColor,
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: { color: colors.gridColor }
                },
                y: {
                    ticks: { 
                        color: colors.textColor,
                        maxTicksLimit: 15
                    },
                    grid: { color: colors.gridColor }
                }
            }
        }
    };

    AppState.chartInstances['workloadCostChart'] = new Chart(ctx, config);
}

/**
 * Updates insights section
 */
function updateInsights(insights) {
    const container = document.querySelector('#insights-container');
    if (!container) return;
    
    const insightElements = Object.entries(insights).map(([key, value]) => {
        const title = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        return `<div class="insight-item mb-3"><h6>${title}</h6><p>${value}</p></div>`;
    });
    
    container.innerHTML = insightElements.join('');
}

/**
 * Updates pod cost metrics in the dashboard
 */
function updatePodCostMetrics(data) {
    console.log('📊 Updating pod cost metrics with data:', data);
    
    if (!data) {
        console.warn('No data provided to updatePodCostMetrics');
        return;
    }
    
    // Calculate top namespace cost
    let topNamespaceCost = 0;
    if (data.namespaceDistribution && data.namespaceDistribution.costs) {
        topNamespaceCost = Math.max(...data.namespaceDistribution.costs);
    } else if (data.podCostBreakdown && data.podCostBreakdown.values) {
        topNamespaceCost = Math.max(...data.podCostBreakdown.values);
    }
    
    // Get namespace count
    let namespaceCount = 0;
    if (data.namespaceDistribution && data.namespaceDistribution.namespaces) {
        namespaceCount = data.namespaceDistribution.namespaces.length;
    } else if (data.podCostBreakdown && data.podCostBreakdown.labels) {
        namespaceCount = data.podCostBreakdown.labels.length;
    }
    
    // Get workload count
    let workloadCount = 0;
    if (data.workloadCosts && data.workloadCosts.workloads) {
        workloadCount = data.workloadCosts.workloads.length;
    }
    
    // Get analysis accuracy
    let accuracy = 'Unknown';
    if (data.podCostBreakdown && data.podCostBreakdown.accuracy_level) {
        accuracy = data.podCostBreakdown.accuracy_level;
    }
    
    console.log(`Updating metrics: topCost=${topNamespaceCost}, namespaces=${namespaceCount}, workloads=${workloadCount}, accuracy=${accuracy}`);
    
    // Update the metrics
    const updates = [
        { sel: '#top-namespace-cost', val: topNamespaceCost, fmt: 'currency' },
        { sel: '#total-namespaces', val: namespaceCount, fmt: 'number' },
        { sel: '#total-workloads', val: workloadCount, fmt: 'number' },
        { sel: '#analysis-accuracy', val: accuracy, fmt: 'text' }
    ];
    
    updates.forEach(update => {
        const element = document.querySelector(update.sel);
        if (element) {
            let displayValue;
            if (update.fmt === 'currency') {
                displayValue = '$' + (update.val || 0).toLocaleString();
            } else if (update.fmt === 'number') {
                displayValue = (update.val || 0).toString();
            } else {
                displayValue = update.val || 'Unknown';
            }
            
            element.textContent = displayValue;
            console.log(`Updated ${update.sel} to: ${displayValue}`);
        } else {
            console.warn(`Element not found: ${update.sel}`);
        }
    });
    
    // Show the pod cost section if we have data
    if (topNamespaceCost > 0 || namespaceCount > 0) {
        const podSection = document.getElementById('pod-cost-section');
        if (podSection) {
            podSection.style.display = 'block';
            console.log('Pod cost section made visible');
        }
    }
}

/**
 * Shows chart error message with retry option
 */
function showChartError(message) {
    console.error('Chart error:', message);
    
    const chartIds = ['costBreakdownChart', 'hpaComparisonChart', 'nodeUtilizationChart', 'savingsBreakdownChart'];
    chartIds.forEach(id => {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        
        canvas.parentElement.innerHTML = `
            <div class="text-center text-muted p-4">
                <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                <p>${message}</p>
                <button class="btn btn-outline-primary btn-sm" onclick="initializeCharts()">
                    <i class="fas fa-redo me-1"></i>Retry
                </button>
            </div>
        `;
    });
}

// ============================================================================
// IMPLEMENTATION PLAN MANAGEMENT
// ============================================================================

/**
 * Loads and displays implementation plan
 */
function loadImplementationPlan() {
    console.log('📋 Loading implementation plan...');
    
    const container = document.getElementById('implementation-plan-container');
    if (!container) {
        console.warn('Implementation plan container not found');
        return;
    }
    
    // Show loading state
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-muted">Loading implementation plan...</p>
        </div>
    `;
    
    fetch(`${AppConfig.API_BASE_URL}/implementation-plan`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayImplementationPlan(data);
            } else {
                throw new Error(data.message || 'Failed to load implementation plan');
            }
        })
        .catch(error => {
            console.error('❌ Failed to load implementation plan:', error);
            displayImplementationPlanError(container, error.message);
        });
}

// Export implementation plan functions immediately
window.loadImplementationPlan = loadImplementationPlan;

/**
 * Displays implementation plan content
 */
function displayImplementationPlan(planData) {
    const container = document.getElementById('implementation-plan-container');
    
    if (!planData?.phases?.length) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-info-circle fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">No Implementation Plan Available</h4>
                <p class="text-muted">Run an analysis first to generate your implementation plan</p>
                <button class="btn btn-primary" onclick="switchToTab('#analysis')">
                    <i class="fas fa-chart-bar"></i> Run Analysis
                </button>
            </div>
        `;
        return;
    }

    const summary = planData.summary || {};
    
    let html = `
        <div class="card border-0 shadow-lg mb-4" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div class="card-body text-white">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h3 class="card-title mb-3">
                            <i class="fas fa-rocket me-2"></i>Implementation Plan Summary
                        </h3>
                        <div class="mb-3">
                            <strong>Cluster:</strong> ${summary.cluster_name || 'N/A'} 
                            <span class="mx-2">•</span>
                            <strong>Resource Group:</strong> ${summary.resource_group || 'N/A'}
                        </div>
                        <p class="mb-0 opacity-90">
                            This ${summary.total_weeks || 0}-week implementation plan will optimize your AKS cluster 
                            through ${summary.total_phases || 0} carefully planned phases.
                        </p>
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="badge fs-6 px-3 py-2" style="background: rgba(255,255,255,0.2);">
                            <i class="fas fa-shield-alt me-1"></i>
                            ${summary.risk_level || 'Unknown'} Risk
                        </div>
                    </div>
                </div>
                
                <div class="row g-3 mt-3">
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">$${(summary.monthly_savings || 0).toLocaleString()}</div>
                            <small class="opacity-90">Monthly Savings</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">$${(summary.annual_savings || 0).toLocaleString()}</div>
                            <small class="opacity-90">Annual Savings</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">${summary.total_weeks || 0}</div>
                            <small class="opacity-90">Total Weeks</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">${(summary.complexity_score || 0).toFixed(1)}/10</div>
                            <small class="opacity-90">Complexity</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Render phases
    planData.phases.forEach((phase, index) => {
        html += renderPhaseCard(phase, index + 1);
    });

    // Add additional sections if available
    if (planData.monitoring_plan) {
        html += renderMonitoringSection(planData.monitoring_plan);
    }

    if (planData.governance_plan) {
        html += renderGovernanceSection(planData.governance_plan);
    }

    if (planData.success_metrics) {
        html += renderSuccessMetricsSection(planData.success_metrics);
    }

    if (planData.contingency_plans) {
        html += renderContingencySection(planData.contingency_plans);
    }

    container.innerHTML = html;
}

/**
 * Renders individual phase card
 */
function renderPhaseCard(phase, phaseNumber) {
    const riskColorClass = getRiskColorClass(phase.risk);
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header ${riskColorClass} text-white">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">
                        <i class="fas fa-${getPhaseIcon(phase.title)} me-2"></i>
                        Phase ${phaseNumber}: ${phase.title}
                    </h6>
                    <div class="d-flex gap-2">
                        <span class="badge bg-light text-dark">${phase.weeks || phase.duration} weeks</span>
                        <span class="badge bg-light text-dark">$${(phase.savings || 0).toLocaleString()}/month</span>
                        <span class="badge bg-light text-dark">${phase.risk} Risk</span>
                    </div>
                </div>
            </div>
            <div class="card-body">
                <p class="lead mb-4">${phase.description}</p>
                
                <div class="row">
                    <div class="col-lg-8">
                        <h6><i class="fas fa-tasks me-2"></i>Implementation Tasks</h6>
                        ${renderTasksAccordion(phase.tasks, phaseNumber)}
                    </div>
                    <div class="col-lg-4">
                        <h6><i class="fas fa-check-circle me-2"></i>Validation Steps</h6>
                        ${renderValidationList(phase.validation)}
                        
                        <div class="mt-4">
                            <h6><i class="fas fa-info-circle me-2"></i>Phase Summary</h6>
                            <div class="card bg-light">
                                <div class="card-body p-3">
                                    <div class="row text-center">
                                        <div class="col-6">
                                            <strong class="text-success">$${(phase.savings || 0).toLocaleString()}</strong>
                                            <small class="d-block text-muted">Monthly Savings</small>
                                        </div>
                                        <div class="col-6">
                                            <strong class="text-primary">${phase.weeks || phase.duration} weeks</strong>
                                            <small class="d-block text-muted">Duration</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Renders tasks accordion for a phase
 */
function renderTasksAccordion(tasks, phaseNumber) {
    if (!tasks?.length) return '<p class="text-muted">No tasks defined</p>';
    
    return `
        <div class="accordion accordion-flush" id="phase${phaseNumber}Tasks">
            ${tasks.map((task, index) => {
                const taskId = `task${phaseNumber}_${index}`;
                return `
                    <div class="accordion-item">
                        <h2 class="accordion-header">
                            <button class="accordion-button collapsed" type="button" 
                                    data-bs-toggle="collapse" data-bs-target="#${taskId}">
                                <strong>${task.task || `Task ${index + 1}`}</strong>
                                ${task.time_estimate ? `<small class="text-muted ms-2">(${task.time_estimate})</small>` : ''}
                            </button>
                        </h2>
                        <div id="${taskId}" class="accordion-collapse collapse" data-bs-parent="#phase${phaseNumber}Tasks">
                            <div class="accordion-body">
                                <p><strong>Description:</strong> ${task.description}</p>
                                ${task.command ? `
                                    <div class="mb-3">
                                        <strong>Command:</strong>
                                        <div class="bg-dark text-light p-3 rounded mt-2 position-relative">
                                            <code>${task.command}</code>
                                            <button class="btn btn-sm btn-outline-light position-absolute top-0 end-0 m-2" 
                                                    onclick="copyToClipboard('${task.command.replace(/'/g, "\\'")}')">
                                                <i class="fas fa-copy"></i>
                                            </button>
                                        </div>
                                    </div>
                                ` : ''}
                                ${task.template ? `
                                    <div class="mb-3">
                                        <strong>YAML Template:</strong>
                                        <div class="bg-light border rounded mt-2 position-relative" style="max-height: 300px; overflow-y: auto;">
                                            <pre class="p-3 mb-0"><code>${escapeHtml(task.template)}</code></pre>
                                            <button class="btn btn-sm btn-outline-primary position-absolute top-0 end-0 m-2" 
                                                    onclick="copyToClipboard(\`${task.template.replace(/`/g, '\\`')}\`)">
                                                <i class="fas fa-copy"></i>
                                            </button>
                                        </div>
                                    </div>
                                ` : ''}
                                <div class="alert alert-info">
                                    <strong>Expected Outcome:</strong> ${task.expected_outcome}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Renders validation steps list
 */
function renderValidationList(validationSteps) {
    if (!validationSteps?.length) return '<p class="text-muted">No validation steps defined</p>';
    
    return `
        <ul class="list-group list-group-flush">
            ${validationSteps.map(step => `
                <li class="list-group-item px-0 border-0">
                    <i class="fas fa-check text-success me-2"></i>${step}
                </li>
            `).join('')}
        </ul>
    `;
}

/**
 * Displays implementation plan error
 */
function displayImplementationPlanError(container, message) {
    container.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <h4 class="alert-heading">
                <i class="fas fa-exclamation-triangle"></i> Error Loading Implementation Plan
            </h4>
            <p class="mb-3">${message}</p>
            <hr>
            <div class="d-flex gap-2">
                <button class="btn btn-outline-danger btn-sm" onclick="loadImplementationPlan()">
                    <i class="fas fa-redo"></i> Retry
                </button>
                <button class="btn btn-outline-secondary btn-sm" onclick="location.reload()">
                    <i class="fas fa-refresh"></i> Refresh Page
                </button>
            </div>
        </div>
    `;
}

/**
 * Helper functions for implementation plan
 */
function getRiskColorClass(risk) {
    switch (risk?.toLowerCase()) {
        case 'high': return 'bg-danger';
        case 'medium': return 'bg-warning';
        case 'low': return 'bg-success';
        default: return 'bg-primary';
    }
}

function getPhaseIcon(title) {
    const titleLower = title.toLowerCase();
    if (titleLower.includes('resource') || titleLower.includes('right-sizing')) return 'cog';
    if (titleLower.includes('hpa') || titleLower.includes('scaling')) return 'expand-arrows-alt';
    if (titleLower.includes('storage')) return 'hdd';
    if (titleLower.includes('optimization')) return 'bullseye';
    return 'rocket';
}

/**
 * Updates implementation summary metrics
 */
function updateImplementationSummary(summary) {
    console.log('📊 Updating summary with data:', summary);

    // Update the annual savings in the summary box
    const annualSavingsElement = document.getElementById('annual-savings-impl');
    if (annualSavingsElement) {
        if (summary && summary.annual_savings) {
            annualSavingsElement.textContent = `${summary.annual_savings.toLocaleString()}`;
            console.log('✅ Updated annual savings to:', summary.annual_savings);
        } else {
            console.log('⚠️ No annual_savings in summary:', summary);
        }
    } else {
        console.log('⚠️ annual-savings-impl element not found');
    }

    // Update quick stats if they exist
    const totalPhasesElement = document.getElementById('total-phases-stat');
    if (totalPhasesElement) {
        totalPhasesElement.textContent = summary?.total_phases || 0;
    }

    const totalWeeksElement = document.getElementById('total-weeks-stat');
    if (totalWeeksElement) {
        totalWeeksElement.textContent = `${summary?.total_weeks || 0} weeks`;
    }

    const monthlySavingsElement = document.getElementById('monthly-savings-stat');
    if (monthlySavingsElement) {
        monthlySavingsElement.textContent = `${(summary?.monthly_savings || 0).toLocaleString()}`;
    }

    const riskLevelElement = document.getElementById('risk-level-stat');
    if (riskLevelElement) {
        riskLevelElement.textContent = summary?.risk_level || 'Unknown';
    }

    // Show the quick stats row if it exists
    const quickStatsRow = document.getElementById('implementation-quick-stats');
    if (quickStatsRow) {
        quickStatsRow.style.display = 'flex';
    }
}

/**
 * Renders implementation phases
 */
function renderImplementationPhases(container, data) {
    console.log('🏗️ Starting to render implementation phases');
    const { phases, summary, monitoring_plan, success_metrics } = data;

    if (!phases || phases.length === 0) {
        console.log('⚠️ No phases found, showing no optimization message');
        container.innerHTML = `
            <div class="text-center mt-4 mb-4">
                <div class="alert alert-info">
                    <h5><i class="fas fa-info-circle me-2"></i>No Major Optimizations Needed</h5>
                    <p>Your cluster is already well-optimized! Only minor improvements were identified.</p>
                    <p><strong>Current Status:</strong> ${summary?.message || 'Analysis complete'}</p>
                </div>
            </div>
        `;
        return;
    }

    console.log(`🏗️ Rendering ${phases.length} phases`);

    let html = `
        <div class="row mb-4">
            <div class="col-12">
                <div class="card bg-primary text-white">
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-md-3">
                                <h3 class="mb-1">${summary.total_phases}</h3>
                                <small>Implementation Phases</small>
                            </div>
                            <div class="col-md-3">
                                <h3 class="mb-1">${summary.total_weeks}</h3>
                                <small>Total Weeks</small>
                            </div>
                            <div class="col-md-3">
                                <h3 class="mb-1">${summary.monthly_savings.toLocaleString()}</h3>
                                <small>Monthly Savings</small>
                            </div>
                            <div class="col-md-3">
                                <h3 class="mb-1">${summary.risk_level}</h3>
                                <small>Overall Risk</small>
                            </div>
                        </div>
                        ${summary.resource_group && summary.cluster_name ? `
                        <div class="row mt-3">
                            <div class="col-12 text-center">
                                <small><i class="fas fa-server me-1"></i> ${summary.resource_group} / ${summary.cluster_name}</small>
                                ${summary.success_probability ? `<span class="ms-3"><i class="fas fa-chart-line me-1"></i> ${summary.success_probability} Success Rate</span>` : ''}
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;

    // Render each phase
    phases.forEach((phase, index) => {
        console.log(`🏗️ Rendering phase ${index + 1}:`, phase.title);
        html += renderPhaseCard(phase, index);
    });

    // Add success metrics if available
    if (success_metrics && Object.keys(success_metrics).length > 0) {
        console.log('🎯 Adding success metrics');
        html += renderSuccessMetrics(success_metrics);
    }

    console.log('🏗️ Setting innerHTML for container');
    container.innerHTML = html;
    console.log('✅ Implementation phases rendered successfully');
}

/**
 * Renders success metrics section
 */
function renderSuccessMetrics(successMetrics) {
    return `
        <div class="card border-0 shadow-sm mt-4">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0">
                    <i class="fas fa-bullseye me-2"></i>Success Metrics & KPIs
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-3">
                    ${Object.entries(successMetrics).map(([categoryKey, categoryData]) => {
                        if (!categoryData || typeof categoryData !== 'object') return '';
                        return `
                        <div class="col-md-4">
                            <div class="metric-summary-card">
                                <h6 class="text-info mb-3">
                                    <i class="fas fa-${getCategoryIcon(categoryKey)} me-2"></i>
                                    ${formatCategoryName(categoryKey)}
                                </h6>
                                ${Object.entries(categoryData).slice(0, 3).map(([key, value]) => `
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <span class="small text-muted">${formatMetricName(key)}</span>
                                        <span class="fw-bold text-primary">${value}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        `;
                    }).join('')}
                </div>
            </div>
        </div>
    `;
}

/**
 * Helper functions for implementation plan categories
 */
function getCategoryIcon(category) {
    const icons = {
        'cost_metrics': 'dollar-sign',
        'performance_metrics': 'tachometer-alt',
        'operational_metrics': 'cogs'
    };
    return icons[category] || 'chart-bar';
}

function formatCategoryName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatMetricName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Updates monitoring plan section
 */
function updateMonitoringPlan(monitoringPlan) {
    console.log('📈 Updating monitoring plan:', monitoringPlan);
    if (!monitoringPlan || Object.keys(monitoringPlan).length === 0) return;

    // Find the monitoring section and update it
    const monitoringSection = document.querySelector('#monitoring-section .card-body');
    if (monitoringSection) {
        let html = '<div class="row">';

        if (monitoringPlan.daily_checks && monitoringPlan.daily_checks.length > 0) {
            html += `
                <div class="col-md-6">
                    <h6><i class="fas fa-calendar-day me-2"></i>Daily Monitoring</h6>
                    <ul class="list-group list-group-flush">
            `;
            monitoringPlan.daily_checks.forEach(check => {
                html += `<li class="list-group-item px-0">${check}</li>`;
            });
            html += '</ul></div>';
        }

        if (monitoringPlan.weekly_reviews && monitoringPlan.weekly_reviews.length > 0) {
            html += `
                <div class="col-md-6">
                    <h6><i class="fas fa-calendar-week me-2"></i>Weekly Reviews</h6>
                    <ul class="list-group list-group-flush">
            `;
            monitoringPlan.weekly_reviews.forEach(review => {
                html += `<li class="list-group-item px-0">${review}</li>`;
            });
            html += '</ul></div>';
        }

        html += '</div>';
        monitoringSection.innerHTML = html;
        console.log('✅ Monitoring plan updated');
    } else {
        console.log('⚠️ Monitoring section not found');
    }
}

/**
 * Shows no analysis message
 */
function showNoAnalysisMessage(container) {
    container.innerHTML = `
        <div class="text-center mt-4 mb-4">
            <div class="alert alert-warning">
                <h4><i class="fas fa-exclamation-triangle me-2"></i>No Analysis Available</h4>
                <p>Please run a cost analysis first to generate your personalized implementation plan.</p>
                <button class="btn btn-primary" onclick="switchToTab('#analysis')">
                    <i class="fas fa-search me-2"></i>Run Analysis
                </button>
            </div>
        </div>
    `;
}

/**
 * Shows implementation error message
 */
function showImplementationError(container, message) {
    container.innerHTML = `
        <div class="text-center mt-4 mb-4">
            <div class="alert alert-danger">
                <h4><i class="fas fa-exclamation-circle me-2"></i>Error Loading Implementation Plan</h4>
                <p>${message}</p>
                <button class="btn btn-outline-primary" onclick="loadImplementationPlan()">
                    <i class="fas fa-redo me-2"></i>Retry
                </button>
            </div>
        </div>
    `;
}

/**
 * Test implementation API for debugging
 */
function testImplementationAPI() {
    console.log('🧪 Testing implementation API directly...');

    fetch('/api/implementation-plan')
        .then(response => response.json())
        .then(data => {
            console.log('🧪 Test result:', data);
            console.log('🧪 Phases:', data.phases);
            console.log('🧪 Summary:', data.summary);
        })
        .catch(error => {
            console.error('🧪 Test error:', error);
        });
}

/**
 * Escapes HTML characters to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Renders monitoring section for implementation plan
 */
function renderMonitoringSection(monitoringPlan) {
    return `
        <div class="card border-0 shadow-sm mt-5">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0">
                    <i class="fas fa-chart-line me-2"></i>Ongoing Monitoring & Optimization
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-4">
                    ${monitoringPlan.daily_checks ? `
                        <div class="col-md-6">
                            <h6 class="text-success">
                                <i class="fas fa-calendar-day me-2"></i>Daily Monitoring
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${monitoringPlan.daily_checks.map(check => `
                                    <li class="list-group-item border-0 px-0">${check}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${monitoringPlan.weekly_reviews ? `
                        <div class="col-md-6">
                            <h6 class="text-primary">
                                <i class="fas fa-calendar-week me-2"></i>Weekly Reviews
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${monitoringPlan.weekly_reviews.map(review => `
                                    <li class="list-group-item border-0 px-0">${review}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${monitoringPlan.monthly_assessments ? `
                        <div class="col-md-6">
                            <h6 class="text-warning">
                                <i class="fas fa-calendar-alt me-2"></i>Monthly Assessments
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${monitoringPlan.monthly_assessments.map(assessment => `
                                    <li class="list-group-item border-0 px-0">${assessment}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${monitoringPlan.automated_alerts ? `
                        <div class="col-md-6">
                            <h6 class="text-danger">
                                <i class="fas fa-exclamation-triangle me-2"></i>Automated Alerts
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${monitoringPlan.automated_alerts.map(alert => `
                                    <li class="list-group-item border-0 px-0">${alert}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Renders governance section for implementation plan
 */
function renderGovernanceSection(governancePlan) {
    return `
        <div class="card border-0 shadow-sm mt-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                    <i class="fas fa-shield-alt me-2"></i>Governance & Control Framework
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-4">
                    ${governancePlan.resource_policies ? `
                        <div class="col-md-4">
                            <h6 class="text-primary">
                                <i class="fas fa-cogs me-2"></i>Resource Policies
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${governancePlan.resource_policies.map(policy => `
                                    <li class="list-group-item border-0 px-0">${policy}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${governancePlan.cost_controls ? `
                        <div class="col-md-4">
                            <h6 class="text-success">
                                <i class="fas fa-dollar-sign me-2"></i>Cost Controls
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${governancePlan.cost_controls.map(control => `
                                    <li class="list-group-item border-0 px-0">${control}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${governancePlan.operational_procedures ? `
                        <div class="col-md-4">
                            <h6 class="text-warning">
                                <i class="fas fa-clipboard-list me-2"></i>Operational Procedures
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${governancePlan.operational_procedures.map(procedure => `
                                    <li class="list-group-item border-0 px-0">${procedure}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Renders success metrics section
 */
function renderSuccessMetricsSection(successMetrics) {
    return `
        <div class="card border-0 shadow-sm mt-4">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0">
                    <i class="fas fa-bullseye me-2"></i>Success Metrics & KPIs
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-3">
                    ${Object.entries(successMetrics).map(([categoryKey, categoryData]) => {
                        if (!categoryData || typeof categoryData !== 'object') return '';
                        return `
                        <div class="col-md-4">
                            <div class="metric-summary-card">
                                <h6 class="text-info mb-3">
                                    <i class="fas fa-${getCategoryIcon(categoryKey)} me-2"></i>
                                    ${formatCategoryName(categoryKey)}
                                </h6>
                                ${Object.entries(categoryData).slice(0, 3).map(([key, value]) => `
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <span class="small text-muted">${formatMetricName(key)}</span>
                                        <span class="fw-bold text-primary">${value}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        `;
                    }).join('')}
                </div>
            </div>
        </div>
    `;
}

/**
 * Renders contingency section
 */
function renderContingencySection(contingencyPlans) {
    return `
        <div class="card border-0 shadow-sm mt-4">
            <div class="card-header bg-warning text-dark">
                <h5 class="mb-0">
                    <i class="fas fa-exclamation-triangle me-2"></i>Contingency Plans
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-4">
                    ${Object.entries(contingencyPlans).map(([key, plan]) => `
                        <div class="col-md-4">
                            <div class="card h-100 border-warning">
                                <div class="card-header bg-warning bg-opacity-10">
                                    <h6 class="mb-0 text-capitalize">
                                        ${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                    </h6>
                                </div>
                                <div class="card-body">
                                    <p class="small text-muted mb-2">
                                        <strong>Scenario:</strong> ${plan.scenario}
                                    </p>
                                    <p class="small mb-2">
                                        <strong>Alternative:</strong> ${plan.alternative}
                                    </p>
                                    <div class="alert alert-warning alert-sm mb-0">
                                        <strong>Impact:</strong> ${plan.impact}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

// ============================================================================
// TAB NAVIGATION
// ============================================================================

/**
 * Switches to specified tab
 */
function switchToTab(selector) {
    const button = document.querySelector(`[data-bs-target="${selector}"]`);
    if (button) button.click();
}

/**
 * Handles tab switching events
 */
function onTabSwitch(event) {
    const target = event.target.getAttribute('data-bs-target');
    console.log('📑 Tab switched to:', target);
    
    switch (target) {
        case '#dashboard':
            setTimeout(initializeCharts, 500);
            break;
        case '#implementation':
            loadImplementationPlan();
            break;
    }
}

// Export tab navigation functions immediately
window.switchToTab = switchToTab;

// ============================================================================
// PLACEHOLDER FUNCTIONS (Future Features)
// ============================================================================

function analyzeAllClusters() {
    showNotification('Analyzing all clusters... Feature coming soon!', 'info');
}

function showPortfolioAnalytics() {
    showNotification('Portfolio Analytics... Feature coming soon!', 'info');
}

function refreshCharts() {
    showNotification('Refreshing charts...', 'info');
    initializeCharts();
}

function exportReport() {
    showNotification('Report export coming soon!', 'info');
}

function deployOptimizations() {
    showNotification('Deployment feature coming soon!', 'info');
}

function scheduleOptimization() {
    showNotification('Scheduling feature coming soon!', 'info');
}

// Export placeholder functions immediately
window.analyzeAllClusters = analyzeAllClusters;
window.showPortfolioAnalytics = showPortfolioAnalytics;
window.refreshCharts = refreshCharts;
window.exportReport = exportReport;
window.deployOptimizations = deployOptimizations;
window.scheduleOptimization = scheduleOptimization;

// ============================================================================
// CSS INJECTION
// ============================================================================

/**
 * Injects necessary CSS for enhanced functionality
 */
function injectEnhancedCSS() {
    if (document.getElementById('enhanced-dashboard-css')) return;
    
    const style = document.createElement('style');
    style.id = 'enhanced-dashboard-css';
    style.textContent = `
        .metric-updated { 
            position: relative; 
            transition: all 0.3s ease;
        }
        
        .metric-updated-indicator { 
            position: absolute; 
            top: -2px; 
            right: -2px; 
            animation: pulse 2s infinite; 
            color: #28a745;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .data-source-indicator { 
            position: fixed; 
            top: 90px; 
            right: 20px; 
            z-index: 1000; 
        }
        
        .data-source-badge { 
            background: rgba(255,255,255,0.95); 
            border-radius: 20px; 
            padding: 8px 16px; 
            display: flex; 
            align-items: center; 
            gap: 5px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            font-size: 0.875rem;
        }
        
        .data-source-badge.real-data { 
            border: 1px solid #28a745; 
            color: #28a745; 
        }
        
        .data-source-badge.sample-data { 
            border: 1px solid #ffc107; 
            color: #856404; 
            background: rgba(255,193,7,0.1); 
        }
        
        [data-theme="dark"] .data-source-badge { 
            background: rgba(45,55,72,0.95); 
            color: #f7fafc; 
        }
        
        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }
        
        @keyframes fadeIn {
            from { 
                opacity: 0; 
                transform: translateY(20px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
        
        .card:hover, .metric-card:hover {
            transform: translateY(-2px);
            transition: transform 0.2s ease;
        }
        
        .loading {
            position: relative;
            pointer-events: none;
        }
        
        .loading::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
        }
    `;
    document.head.appendChild(style);
}

// ============================================================================
// INITIALIZATION & EVENT HANDLERS
// ============================================================================

/**
 * Main initialization function
 */
function initializeDashboard() {
    console.log('🚀 Initializing AKS Cost Intelligence Dashboard');
    
    try {
        // Inject enhanced CSS
        injectEnhancedCSS();
        
        // Setup form handlers
        setupFormHandlers();
        
        // Setup input validation
        setupInputValidation();
        
        // Setup tab switching
        setupTabSwitching();
        
        // Setup keyboard shortcuts
        setupKeyboardShortcuts();
        
        // Auto-initialize charts if dashboard is active
        if (document.querySelector('#dashboard')?.classList.contains('active')) {
            setTimeout(initializeCharts, 500);
        }
        
        // Test API connectivity
        testAPIConnectivity();
        
        console.log('✅ Dashboard initialization completed');
        
    } catch (error) {
        console.error('❌ Error during initialization:', error);
        showNotification('Dashboard initialization failed: ' + error.message, 'error');
    }
}

/**
 * Sets up form event handlers
 */
function setupFormHandlers() {
    // Add cluster form handler
    const possibleFormIds = ['addClusterForm', 'add-cluster-form', 'clusterForm'];
    let formFound = false;
    
    for (const formId of possibleFormIds) {
        const form = document.getElementById(formId);
        if (form) {
            console.log(`✅ Found form: ${formId}`);
            form.addEventListener('submit', handleAddClusterSubmission);
            formFound = true;
            break;
        }
    }
    
    if (!formFound) {
        console.warn('⚠️ No add cluster form found');
    }
    
    // Analysis form handler
    const analysisForm = document.getElementById('analysisForm');
    if (analysisForm) {
        analysisForm.addEventListener('submit', handleAnalysisSubmit);
        console.log('✅ Analysis form handler attached');
    }
}

/**
 * Sets up tab switching functionality
 */
function setupTabSwitching() {
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(btn => {
        btn.addEventListener('shown.bs.tab', onTabSwitch);
    });
}

/**
 * Sets up keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (event) => {
        // Ctrl/Cmd + R to refresh charts
        if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
            event.preventDefault();
            refreshCharts();
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) modalInstance.hide();
            });
        }
    });
}

/**
 * Tests API connectivity
 */
function testAPIConnectivity() {
    fetch(`${AppConfig.API_BASE_URL}/clusters`)
        .then(response => response.json())
        .then(data => {
            console.log('✅ API connectivity test passed');
            if (data.clusters?.length > 0) {
                console.log(`📊 Found ${data.clusters.length} existing clusters`);
            }
        })
        .catch(error => {
            console.error('❌ API connectivity test failed:', error);
            showNotification('API connection failed. Some features may not work.', 'warning');
        });
}

// ============================================================================
// MAIN ENTRY POINT
// ============================================================================

/**
 * Single DOMContentLoaded event handler
 */
document.addEventListener('DOMContentLoaded', initializeDashboard);

// Export AppState for external access
window.AppState = AppState;
window.AppConfig = AppConfig;

console.log('✅ Enhanced AKS Cost Intelligence Dashboard loaded successfully');

/**
 * Gets accuracy badge class for pod analysis
 */
function getAccuracyBadgeClass(accuracy) {
    switch (accuracy?.toLowerCase()) {
        case 'very high': return 'bg-success';
        case 'high': return 'bg-info';
        case 'good': return 'bg-warning';
        case 'basic': return 'bg-secondary';
        default: return 'bg-secondary';
    }
}

/**
 * Shows chart error message with retry option
 */
function showChartError(message) {
    console.error('Chart error:', message);
    
    const chartIds = ['costBreakdownChart', 'hpaComparisonChart', 'nodeUtilizationChart', 'savingsBreakdownChart'];
    chartIds.forEach(id => {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        
        canvas.parentElement.innerHTML = `
            <div class="text-center text-muted p-4">
                <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                <p>${message}</p>
                <button class="btn btn-outline-primary btn-sm" onclick="initializeCharts()">
                    <i class="fas fa-redo me-1"></i>Retry
                </button>
            </div>
        `;
    });
}

// ============================================================================
// IMPLEMENTATION PLAN MANAGEMENT
// ============================================================================

/**
 * Loads and displays implementation plan
 */
function loadImplementationPlan() {
    console.log('📋 Loading implementation plan...');
    
    const container = document.getElementById('implementation-plan-container');
    if (!container) {
        console.warn('Implementation plan container not found');
        return;
    }
    
    // Show loading state
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-muted">Loading implementation plan...</p>
        </div>
    `;
    
    fetch(`${AppConfig.API_BASE_URL}/implementation-plan`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayImplementationPlan(data);
            } else {
                throw new Error(data.message || 'Failed to load implementation plan');
            }
        })
        .catch(error => {
            console.error('❌ Failed to load implementation plan:', error);
            displayImplementationPlanError(container, error.message);
        });
}

/**
 * Displays implementation plan content
 */
function displayImplementationPlan(planData) {
    const container = document.getElementById('implementation-plan-container');
    
    if (!planData?.phases?.length) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-info-circle fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">No Implementation Plan Available</h4>
                <p class="text-muted">Run an analysis first to generate your implementation plan</p>
                <button class="btn btn-primary" onclick="switchToTab('#analysis')">
                    <i class="fas fa-chart-bar"></i> Run Analysis
                </button>
            </div>
        `;
        return;
    }

    const summary = planData.summary || {};
    
    let html = `
        <div class="card border-0 shadow-lg mb-4" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div class="card-body text-white">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h3 class="card-title mb-3">
                            <i class="fas fa-rocket me-2"></i>Implementation Plan Summary
                        </h3>
                        <div class="mb-3">
                            <strong>Cluster:</strong> ${summary.cluster_name || 'N/A'} 
                            <span class="mx-2">•</span>
                            <strong>Resource Group:</strong> ${summary.resource_group || 'N/A'}
                        </div>
                        <p class="mb-0 opacity-90">
                            This ${summary.total_weeks || 0}-week implementation plan will optimize your AKS cluster 
                            through ${summary.total_phases || 0} carefully planned phases.
                        </p>
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="badge fs-6 px-3 py-2" style="background: rgba(255,255,255,0.2);">
                            <i class="fas fa-shield-alt me-1"></i>
                            ${summary.risk_level || 'Unknown'} Risk
                        </div>
                    </div>
                </div>
                
                <div class="row g-3 mt-3">
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">$${(summary.monthly_savings || 0).toLocaleString()}</div>
                            <small class="opacity-90">Monthly Savings</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">$${(summary.annual_savings || 0).toLocaleString()}</div>
                            <small class="opacity-90">Annual Savings</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">${summary.total_weeks || 0}</div>
                            <small class="opacity-90">Total Weeks</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">${(summary.complexity_score || 0).toFixed(1)}/10</div>
                            <small class="opacity-90">Complexity</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Render phases
    planData.phases.forEach((phase, index) => {
        html += renderPhaseCard(phase, index + 1);
    });

    container.innerHTML = html;
}

/**
 * Renders individual phase card
 */
function renderPhaseCard(phase, phaseNumber) {
    const riskColorClass = getRiskColorClass(phase.risk);
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header ${riskColorClass} text-white">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">
                        <i class="fas fa-${getPhaseIcon(phase.title)} me-2"></i>
                        Phase ${phaseNumber}: ${phase.title}
                    </h6>
                    <div class="d-flex gap-2">
                        <span class="badge bg-light text-dark">${phase.weeks || phase.duration} weeks</span>
                        <span class="badge bg-light text-dark">$${(phase.savings || 0).toLocaleString()}/month</span>
                        <span class="badge bg-light text-dark">${phase.risk} Risk</span>
                    </div>
                </div>
            </div>
            <div class="card-body">
                <p class="lead mb-4">${phase.description}</p>
                
                <div class="row">
                    <div class="col-lg-8">
                        <h6><i class="fas fa-tasks me-2"></i>Implementation Tasks</h6>
                        ${renderTasksAccordion(phase.tasks, phaseNumber)}
                    </div>
                    <div class="col-lg-4">
                        <h6><i class="fas fa-check-circle me-2"></i>Validation Steps</h6>
                        ${renderValidationList(phase.validation)}
                        
                        <div class="mt-4">
                            <h6><i class="fas fa-info-circle me-2"></i>Phase Summary</h6>
                            <div class="card bg-light">
                                <div class="card-body p-3">
                                    <div class="row text-center">
                                        <div class="col-6">
                                            <strong class="text-success">$${(phase.savings || 0).toLocaleString()}</strong>
                                            <small class="d-block text-muted">Monthly Savings</small>
                                        </div>
                                        <div class="col-6">
                                            <strong class="text-primary">${phase.weeks || phase.duration} weeks</strong>
                                            <small class="d-block text-muted">Duration</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Renders tasks accordion for a phase
 */
function renderTasksAccordion(tasks, phaseNumber) {
    if (!tasks?.length) return '<p class="text-muted">No tasks defined</p>';
    
    return `
        <div class="accordion accordion-flush" id="phase${phaseNumber}Tasks">
            ${tasks.map((task, index) => {
                const taskId = `task${phaseNumber}_${index}`;
                return `
                    <div class="accordion-item">
                        <h2 class="accordion-header">
                            <button class="accordion-button collapsed" type="button" 
                                    data-bs-toggle="collapse" data-bs-target="#${taskId}">
                                <strong>${task.task || `Task ${index + 1}`}</strong>
                                ${task.time_estimate ? `<small class="text-muted ms-2">(${task.time_estimate})</small>` : ''}
                            </button>
                        </h2>
                        <div id="${taskId}" class="accordion-collapse collapse" data-bs-parent="#phase${phaseNumber}Tasks">
                            <div class="accordion-body">
                                <p><strong>Description:</strong> ${task.description}</p>
                                ${task.command ? `
                                    <div class="mb-3">
                                        <strong>Command:</strong>
                                        <div class="bg-dark text-light p-3 rounded mt-2 position-relative">
                                            <code>${task.command}</code>
                                            <button class="btn btn-sm btn-outline-light position-absolute top-0 end-0 m-2" 
                                                    onclick="copyToClipboard('${task.command.replace(/'/g, "\\'")}')">
                                                <i class="fas fa-copy"></i>
                                            </button>
                                        </div>
                                    </div>
                                ` : ''}
                                ${task.template ? `
                                    <div class="mb-3">
                                        <strong>YAML Template:</strong>
                                        <div class="bg-light border rounded mt-2 position-relative" style="max-height: 300px; overflow-y: auto;">
                                            <pre class="p-3 mb-0"><code>${escapeHtml(task.template)}</code></pre>
                                            <button class="btn btn-sm btn-outline-primary position-absolute top-0 end-0 m-2" 
                                                    onclick="copyToClipboard(\`${task.template.replace(/`/g, '\\`')}\`)">
                                                <i class="fas fa-copy"></i>
                                            </button>
                                        </div>
                                    </div>
                                ` : ''}
                                <div class="alert alert-info">
                                    <strong>Expected Outcome:</strong> ${task.expected_outcome}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Renders validation steps list
 */
function renderValidationList(validationSteps) {
    if (!validationSteps?.length) return '<p class="text-muted">No validation steps defined</p>';
    
    return `
        <ul class="list-group list-group-flush">
            ${validationSteps.map(step => `
                <li class="list-group-item px-0 border-0">
                    <i class="fas fa-check text-success me-2"></i>${step}
                </li>
            `).join('')}
        </ul>
    `;
}

/**
 * Displays implementation plan error
 */
function displayImplementationPlanError(container, message) {
    container.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <h4 class="alert-heading">
                <i class="fas fa-exclamation-triangle"></i> Error Loading Implementation Plan
            </h4>
            <p class="mb-3">${message}</p>
            <hr>
            <div class="d-flex gap-2">
                <button class="btn btn-outline-danger btn-sm" onclick="loadImplementationPlan()">
                    <i class="fas fa-redo"></i> Retry
                </button>
                <button class="btn btn-outline-secondary btn-sm" onclick="location.reload()">
                    <i class="fas fa-refresh"></i> Refresh Page
                </button>
            </div>
        </div>
    `;
}

/**
 * Helper functions for implementation plan
 */
function getRiskColorClass(risk) {
    switch (risk?.toLowerCase()) {
        case 'high': return 'bg-danger';
        case 'medium': return 'bg-warning';
        case 'low': return 'bg-success';
        default: return 'bg-primary';
    }
}

function getPhaseIcon(title) {
    const titleLower = title.toLowerCase();
    if (titleLower.includes('resource') || titleLower.includes('right-sizing')) return 'cog';
    if (titleLower.includes('hpa') || titleLower.includes('scaling')) return 'expand-arrows-alt';
    if (titleLower.includes('storage')) return 'hdd';
    if (titleLower.includes('optimization')) return 'bullseye';
    return 'rocket';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// TAB NAVIGATION
// ============================================================================

/**
 * Switches to specified tab
 */
function switchToTab(selector) {
    const button = document.querySelector(`[data-bs-target="${selector}"]`);
    if (button) button.click();
}

/**
 * Handles tab switching events
 */
function onTabSwitch(event) {
    const target = event.target.getAttribute('data-bs-target');
    console.log('📑 Tab switched to:', target);
    
    switch (target) {
        case '#dashboard':
            setTimeout(initializeCharts, 500);
            break;
        case '#implementation':
            loadImplementationPlan();
            break;
    }
}

// ============================================================================
// PLACEHOLDER FUNCTIONS (Future Features)
// ============================================================================

function analyzeAllClusters() {
    showNotification('Analyzing all clusters... Feature coming soon!', 'info');
}

function showPortfolioAnalytics() {
    showNotification('Portfolio Analytics... Feature coming soon!', 'info');
}

function refreshCharts() {
    showNotification('Refreshing charts...', 'info');
    initializeCharts();
}

function exportReport() {
    showNotification('Report export coming soon!', 'info');
}

function deployOptimizations() {
    showNotification('Deployment feature coming soon!', 'info');
}

function scheduleOptimization() {
    showNotification('Scheduling feature coming soon!', 'info');
}

// ============================================================================
// CSS INJECTION
// ============================================================================

/**
 * Injects necessary CSS for enhanced functionality
 */
function injectEnhancedCSS() {
    if (document.getElementById('enhanced-dashboard-css')) return;
    
    const style = document.createElement('style');
    style.id = 'enhanced-dashboard-css';
    style.textContent = `
        .metric-updated { 
            position: relative; 
            transition: all 0.3s ease;
        }
        
        .metric-updated-indicator { 
            position: absolute; 
            top: -2px; 
            right: -2px; 
            animation: pulse 2s infinite; 
            color: #28a745;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .data-source-indicator { 
            position: fixed; 
            top: 90px; 
            right: 20px; 
            z-index: 1000; 
        }
        
        .data-source-badge { 
            background: rgba(255,255,255,0.95); 
            border-radius: 20px; 
            padding: 8px 16px; 
            display: flex; 
            align-items: center; 
            gap: 5px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            font-size: 0.875rem;
        }
        
        .data-source-badge.real-data { 
            border: 1px solid #28a745; 
            color: #28a745; 
        }
        
        .data-source-badge.sample-data { 
            border: 1px solid #ffc107; 
            color: #856404; 
            background: rgba(255,193,7,0.1); 
        }
        
        [data-theme="dark"] .data-source-badge { 
            background: rgba(45,55,72,0.95); 
            color: #f7fafc; 
        }
        
        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }
        
        @keyframes fadeIn {
            from { 
                opacity: 0; 
                transform: translateY(20px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
        
        .card:hover, .metric-card:hover {
            transform: translateY(-2px);
            transition: transform 0.2s ease;
        }
        
        .loading {
            position: relative;
            pointer-events: none;
        }
        
        .loading::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
        }
    `;
    document.head.appendChild(style);
}

// ============================================================================
// INITIALIZATION & EVENT HANDLERS
// ============================================================================

/**
 * Main initialization function
 */
function initializeDashboard() {
    console.log('🚀 Initializing AKS Cost Intelligence Dashboard');
    
    try {
        // Inject enhanced CSS
        injectEnhancedCSS();
        
        // Setup form handlers
        setupFormHandlers();
        
        // Setup input validation
        setupInputValidation();
        
        // Setup tab switching
        setupTabSwitching();
        
        // Setup keyboard shortcuts
        setupKeyboardShortcuts();
        
        // Auto-initialize charts if dashboard is active
        if (document.querySelector('#dashboard')?.classList.contains('active')) {
            setTimeout(initializeCharts, 500);
        }
        
        // Test API connectivity
        testAPIConnectivity();
        
        console.log('✅ Dashboard initialization completed');
        
    } catch (error) {
        console.error('❌ Error during initialization:', error);
        showNotification('Dashboard initialization failed: ' + error.message, 'error');
    }
}

/**
 * Sets up form event handlers
 */
function setupFormHandlers() {
    // Add cluster form handler
    const possibleFormIds = ['addClusterForm', 'add-cluster-form', 'clusterForm'];
    let formFound = false;
    
    for (const formId of possibleFormIds) {
        const form = document.getElementById(formId);
        if (form) {
            console.log(`✅ Found form: ${formId}`);
            form.addEventListener('submit', handleAddClusterSubmission);
            formFound = true;
            break;
        }
    }
    
    if (!formFound) {
        console.warn('⚠️ No add cluster form found');
    }
    
    // Analysis form handler
    const analysisForm = document.getElementById('analysisForm');
    if (analysisForm) {
        analysisForm.addEventListener('submit', handleAnalysisSubmit);
        console.log('✅ Analysis form handler attached');
    }
}

/**
 * Sets up tab switching functionality
 */
function setupTabSwitching() {
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(btn => {
        btn.addEventListener('shown.bs.tab', onTabSwitch);
    });
}

/**
 * Sets up keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (event) => {
        // Ctrl/Cmd + R to refresh charts
        if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
            event.preventDefault();
            refreshCharts();
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) modalInstance.hide();
            });
        }
    });
}

/**
 * Tests API connectivity
 */
function testAPIConnectivity() {
    fetch(`${AppConfig.API_BASE_URL}/clusters`)
        .then(response => response.json())
        .then(data => {
            console.log('✅ API connectivity test passed');
            if (data.clusters?.length > 0) {
                console.log(`📊 Found ${data.clusters.length} existing clusters`);
            }
        })
        .catch(error => {
            console.error('❌ API connectivity test failed:', error);
            showNotification('API connection failed. Some features may not work.', 'warning');
        });
}

/**
 * Enhanced Frontend Integration for Auto-Analysis
 * Add these enhancements to your existing main.js
 */

// Enhanced AppState for real-time tracking
AppState.autoAnalysis = {
    active: {},  // Track active analyses
    pollingIntervals: {},  // Store polling intervals
    statusCache: {}  // Cache status updates
};

/**
 * ENHANCED: Add cluster with automatic analysis
 * Replace your existing handleAddClusterSubmission function with this version
 */
function handleAddClusterSubmission(event) {
    event.preventDefault();
    console.log('📝 Enhanced form submission started with auto-analysis');
    
    const formData = new FormData(event.target);
    const autoAnalyze = document.getElementById('auto_analyze')?.checked !== false; // Default true
    
    const clusterData = {
        cluster_name: formData.get('cluster_name'),
        resource_group: formData.get('resource_group'),
        environment: formData.get('environment') || 'development',
        region: formData.get('region') || '',
        description: formData.get('description') || '',
        auto_analyze: autoAnalyze
    };
    
    console.log('📋 Enhanced cluster data:', clusterData);
    
    // Validate required fields
    if (!clusterData.cluster_name || !clusterData.resource_group) {
        showNotification('Cluster name and resource group are required', 'error');
        return;
    }
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    if (!submitBtn) {
        console.error('❌ Submit button not found');
        return;
    }
    
    // Show loading state
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding...';
    submitBtn.disabled = true;
    
    console.log('📤 Sending enhanced API request...');
    
    // Make API call
    fetch(`${AppConfig.API_BASE_URL}/clusters`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(clusterData)
    })
    .then(response => {
        console.log('📡 Enhanced API response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('✅ Enhanced API success:', data);
        
        const clusterId = data.cluster_id;
        const autoAnalysisStarted = data.auto_analysis;
        
        if (autoAnalysisStarted) {
            // Auto-analysis started - show enhanced notification
            showNotification(
                `🎉 Cluster "${clusterData.cluster_name}" added successfully! Analysis is running automatically in the background.`, 
                'success', 
                8000
            );
            
            // Start real-time status tracking
            startAnalysisTracking(clusterId, clusterData.cluster_name);
            
            // Update button to show analysis status
            submitBtn.innerHTML = '<i class="fas fa-cog fa-spin me-2"></i>Analysis Running...';
            
        } else {
            showNotification(`Cluster "${clusterData.cluster_name}" added successfully!`, 'success');
        }
        
        // Close modal if exists
        const modalElement = document.getElementById('addClusterModal');
        if (modalElement && window.bootstrap) {
            const modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
            modal.hide();
        }
        
        // Reset form
        event.target.reset();
        
        // Refresh the cluster list after a delay
        setTimeout(() => {
            if (autoAnalysisStarted) {
                // Keep modal area updated but don't reload immediately
                showAnalysisProgressModal(clusterId, clusterData.cluster_name);
            }
            refreshClusterList();
        }, 2000);
        
    })
    .catch(error => {
        console.error('❌ Enhanced API error:', error);
        showNotification('Error adding cluster: ' + error.message, 'error');
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

/**
 * Start real-time analysis tracking for a cluster
 */
function startAnalysisTracking(clusterId, clusterName) {
    console.log(`🔄 Starting analysis tracking for ${clusterId}`);
    
    // Mark as active
    AppState.autoAnalysis.active[clusterId] = {
        clusterId: clusterId,
        clusterName: clusterName,
        startTime: new Date(),
        lastUpdate: new Date()
    };
    
    // Start polling for status updates
    const pollInterval = setInterval(() => {
        updateAnalysisStatus(clusterId);
    }, 3000); // Poll every 3 seconds
    
    AppState.autoAnalysis.pollingIntervals[clusterId] = pollInterval;
    
    // Auto-stop polling after 10 minutes
    setTimeout(() => {
        stopAnalysisTracking(clusterId);
    }, 10 * 60 * 1000);
}

/**
 * Update analysis status for a specific cluster
 */
function updateAnalysisStatus(clusterId) {
    fetch(`${AppConfig.API_BASE_URL}/clusters/${clusterId}/analysis-status`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const status = data.status;
                const progress = data.progress || 0;
                const message = data.message || 'Processing...';
                
                console.log(`📊 Status update for ${clusterId}: ${status} (${progress}%) - ${message}`);
                
                // Update UI elements
                updateClusterStatusInUI(clusterId, status, progress, message);
                
                // Check if completed or failed
                if (status === 'completed') {
                    handleAnalysisComplete(clusterId, data);
                    stopAnalysisTracking(clusterId);
                } else if (status === 'failed') {
                    handleAnalysisFailure(clusterId, message);
                    stopAnalysisTracking(clusterId);
                }
                
                // Cache the status
                AppState.autoAnalysis.statusCache[clusterId] = {
                    status: status,
                    progress: progress,
                    message: message,
                    timestamp: new Date().toISOString()
                };
            }
        })
        .catch(error => {
            console.error(`❌ Error updating status for ${clusterId}:`, error);
        });
}

/**
 * Stop analysis tracking for a cluster
 */
function stopAnalysisTracking(clusterId) {
    console.log(`⏹️ Stopping analysis tracking for ${clusterId}`);
    
    // Clear polling interval
    if (AppState.autoAnalysis.pollingIntervals[clusterId]) {
        clearInterval(AppState.autoAnalysis.pollingIntervals[clusterId]);
        delete AppState.autoAnalysis.pollingIntervals[clusterId];
    }
    
    // Remove from active tracking
    delete AppState.autoAnalysis.active[clusterId];
}

/**
 * Update cluster status in the UI
 */
function updateClusterStatusInUI(clusterId, status, progress, message) {
    // Find cluster cards/elements with this ID
    const clusterElements = document.querySelectorAll(`[data-cluster-id="${clusterId}"]`);
    
    clusterElements.forEach(element => {
        const statusElement = element.querySelector('.cluster-status');
        const actionButton = element.querySelector('.cluster-action-btn');
        const progressBar = element.querySelector('.analysis-progress');
        
        if (statusElement) {
            statusElement.innerHTML = getEnhancedStatusHTML(status, message, progress);
        }
        
        if (actionButton) {
            updateActionButton(actionButton, status, clusterId, progress);
        }
        
        if (progressBar) {
            updateProgressBar(progressBar, progress, status);
        }
    });
    
    // Update any open progress modals
    updateProgressModal(clusterId, status, progress, message);
}

/**
 * Generate enhanced status HTML
 */
function getEnhancedStatusHTML(status, message, progress) {
    switch (status) {
        case 'analyzing':
            return `
                <div class="d-flex align-items-center">
                    <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                        <span class="visually-hidden">Analyzing...</span>
                    </div>
                    <div class="flex-grow-1">
                        <div class="fw-semibold text-primary">Analyzing</div>
                        <small class="text-muted">${message}</small>
                        <div class="progress mt-1" style="height: 4px;">
                            <div class="progress-bar bg-primary" style="width: ${progress}%"></div>
                        </div>
                    </div>
                </div>
            `;
            
        case 'completed':
            return `
                <div class="d-flex align-items-center">
                    <i class="fas fa-check-circle text-success me-2 fa-lg"></i>
                    <div>
                        <div class="fw-semibold text-success">Analysis Complete</div>
                        <small class="text-muted">Results available</small>
                    </div>
                </div>
            `;
            
        case 'failed':
            return `
                <div class="d-flex align-items-center">
                    <i class="fas fa-exclamation-triangle text-warning me-2 fa-lg"></i>
                    <div>
                        <div class="fw-semibold text-warning">Analysis Failed</div>
                        <small class="text-muted">${message}</small>
                    </div>
                </div>
            `;
            
        default:
            return `
                <div class="d-flex align-items-center">
                    <i class="fas fa-clock text-muted me-2"></i>
                    <div>
                        <div class="fw-semibold text-muted">Ready to Analyze</div>
                        <small class="text-muted">Click to start analysis</small>
                    </div>
                </div>
            `;
    }
}

/**
 * Update action button based on analysis status
 */
function updateActionButton(button, status, clusterId, progress = 0) {
    switch (status) {
        case 'analyzing':
            button.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i>Analyzing... ${progress}%`;
            button.disabled = true;
            button.className = 'btn btn-sm btn-outline-primary cluster-action-btn';
            break;
            
        case 'completed':
            button.innerHTML = '<i class="fas fa-eye me-1"></i>View Results';
            button.disabled = false;
            button.className = 'btn btn-sm btn-success cluster-action-btn';
            button.onclick = () => selectCluster(clusterId);
            break;
            
        case 'failed':
            button.innerHTML = '<i class="fas fa-redo me-1"></i>Retry Analysis';
            button.disabled = false;
            button.className = 'btn btn-sm btn-warning cluster-action-btn';
            button.onclick = () => analyzeCluster(clusterId);
            break;
            
        default:
            button.innerHTML = '<i class="fas fa-play me-1"></i>Analyze Now';
            button.disabled = false;
            button.className = 'btn btn-sm btn-primary cluster-action-btn';
            button.onclick = () => analyzeCluster(clusterId);
            break;
    }
}

/**
 * Handle analysis completion
 */
function handleAnalysisComplete(clusterId, statusData) {
    const clusterName = AppState.autoAnalysis.active[clusterId]?.clusterName || 'Cluster';
    
    console.log(`🎉 Analysis completed for ${clusterName}`);
    
    // Show enhanced completion notification
    const results = statusData.results || {};
    const savings = results.total_savings || 0;
    const cost = results.total_cost || 0;
    
    showEnhancedCompletionNotification(clusterName, cost, savings, clusterId);
    
    // Refresh cluster list to show updated data
    setTimeout(() => {
        refreshClusterList();
    }, 2000);
}

/**
 * Handle analysis failure
 */
function handleAnalysisFailure(clusterId, errorMessage) {
    const clusterName = AppState.autoAnalysis.active[clusterId]?.clusterName || 'Cluster';
    
    console.log(`❌ Analysis failed for ${clusterName}: ${errorMessage}`);
    
    showNotification(
        `Analysis failed for "${clusterName}": ${errorMessage}. You can retry the analysis manually.`,
        'warning',
        10000
    );
    
    setTimeout(() => {
        refreshClusterList();
    }, 2000);
}

/**
 * Show enhanced completion notification with results preview
 */
function showEnhancedCompletionNotification(clusterName, cost, savings, clusterId) {
    const savingsPercent = cost > 0 ? ((savings / cost) * 100).toFixed(1) : 0;
    
    // Create enhanced notification
    const notificationHTML = `
        <div class="analysis-complete-notification">
            <div class="d-flex align-items-start">
                <div class="notification-icon me-3">
                    <i class="fas fa-trophy text-warning fa-2x"></i>
                </div>
                <div class="flex-1">
                    <h6 class="mb-1">🎉 Analysis Complete!</h6>
                    <p class="mb-2">Results for <strong>${clusterName}</strong> are ready</p>
                    <div class="quick-stats">
                        <span class="badge bg-success me-2">$${cost.toLocaleString()} monthly cost</span>
                        <span class="badge bg-primary me-2">$${savings.toLocaleString()} savings potential</span>
                        <span class="badge bg-warning">${savingsPercent}% optimization</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Create enhanced toast
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toastElement = document.createElement('div');
    toastElement.className = 'toast align-items-start border-0 shadow-lg';
    toastElement.style.minWidth = '400px';
    
    toastElement.innerHTML = `
        <div class="toast-header bg-success text-white">
            <i class="fas fa-chart-line me-2"></i>
            <strong class="me-auto">Analysis Complete</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${notificationHTML}
            <div class="mt-3">
                <button class="btn btn-primary btn-sm me-2" onclick="selectCluster('${clusterId}')">
                    <i class="fas fa-eye me-1"></i>View Results
                </button>
                <button class="btn btn-outline-secondary btn-sm" data-bs-dismiss="toast">
                    <i class="fas fa-check me-1"></i>Got it
                </button>
            </div>
        </div>
    `;
    
    toastContainer.appendChild(toastElement);
    
    const toast = new bootstrap.Toast(toastElement, {
        autohide: false // Don't auto-hide completion notifications
    });
    toast.show();
    
    // Auto-remove after 30 seconds
    setTimeout(() => {
        if (toastElement.parentNode) {
            toastElement.parentNode.removeChild(toastElement);
        }
    }, 30000);
}

/**
 * Show analysis progress modal for ongoing analysis
 */
function showAnalysisProgressModal(clusterId, clusterName) {
    // Create or update progress modal
    let modal = document.getElementById('analysisProgressModal');
    if (!modal) {
        modal = createAnalysisProgressModal();
    }
    
    // Update modal content
    const modalTitle = modal.querySelector('.modal-title');
    const clusterNameElement = modal.querySelector('.cluster-name-progress');
    
    if (modalTitle) modalTitle.textContent = `Analysis in Progress - ${clusterName}`;
    if (clusterNameElement) clusterNameElement.textContent = `Analyzing ${clusterName}...`;
    
    // Show modal
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    // Store modal reference for updates
    modal.setAttribute('data-cluster-id', clusterId);
}

/**
 * Update progress modal with current status
 */
function updateProgressModal(clusterId, status, progress, message) {
    const modal = document.querySelector(`#analysisProgressModal[data-cluster-id="${clusterId}"]`);
    if (!modal) return;
    
    const progressCircle = modal.querySelector('.progress-circle');
    const currentStepElement = modal.querySelector('.current-step');
    const timeRemainingElement = modal.querySelector('.time-remaining');
    
    if (progressCircle) {
        const circle = progressCircle.querySelector('.circle');
        const percentage = progressCircle.querySelector('.percentage');
        
        if (circle && percentage) {
            circle.style.strokeDasharray = `${progress}, 100`;
            percentage.textContent = `${progress}%`;
        }
    }
    
    if (currentStepElement) {
        currentStepElement.textContent = message;
    }
    
    if (timeRemainingElement) {
        const estimatedTotal = 300; // 5 minutes
        const elapsed = (100 - progress) / 100;
        const remaining = Math.max(30, elapsed * estimatedTotal);
        timeRemainingElement.textContent = `~${Math.round(remaining)}s`;
    }
    
    // Update step indicators
    updateStepIndicators(modal, progress);
    
    // Auto-close modal when complete
    if (status === 'completed' || status === 'failed') {
        setTimeout(() => {
            const bootstrapModal = bootstrap.Modal.getInstance(modal);
            if (bootstrapModal) {
                bootstrapModal.hide();
            }
        }, 3000);
    }
}

/**
 * Update step indicators in progress modal
 */
function updateStepIndicators(modal, progress) {
    const steps = modal.querySelectorAll('.step-item');
    
    steps.forEach((step, index) => {
        const stepProgress = (index + 1) * 25; // 4 steps total
        const stepIcon = step.querySelector('.step-status i');
        
        if (progress >= stepProgress) {
            // Step completed
            if (stepIcon) {
                stepIcon.className = 'fas fa-check text-success';
            }
            step.classList.add('completed');
        } else if (progress >= stepProgress - 25) {
            // Step in progress
            if (stepIcon) {
                stepIcon.className = 'fas fa-spinner fa-spin text-primary';
            }
            step.classList.add('active');
        } else {
            // Step pending
            if (stepIcon) {
                stepIcon.className = 'fas fa-clock text-muted';
            }
            step.classList.remove('active', 'completed');
        }
    });
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Enhanced cluster list refresh with status preservation
 */
function refreshClusterList() {
    console.log('🔄 Enhanced cluster list refresh...');
    
    fetch(`${AppConfig.API_BASE_URL}/clusters`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.clusters) {
                // Update cluster list while preserving real-time status
                updateClusterListUI(data.clusters);
                
                // Re-apply any active analysis tracking
                Object.keys(AppState.autoAnalysis.active).forEach(clusterId => {
                    updateAnalysisStatus(clusterId);
                });
            }
        })
        .catch(error => {
            console.error('❌ Error refreshing cluster list:', error);
        });
}

/**
 * Initialize auto-analysis system on page load
 */
function initializeAutoAnalysisSystem() {
    console.log('🚀 Initializing auto-analysis system...');
    
    // Check for any clusters currently being analyzed
    fetch(`${AppConfig.API_BASE_URL}/clusters`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.clusters) {
                data.clusters.forEach(cluster => {
                    if (cluster.analysis_status === 'analyzing') {
                        console.log(`🔄 Resuming tracking for cluster: ${cluster.id}`);
                        startAnalysisTracking(cluster.id, cluster.name);
                    }
                });
            }
        })
        .catch(error => {
            console.error('❌ Error initializing auto-analysis:', error);
        });
}

// Add to your existing DOMContentLoaded event
document.addEventListener('DOMContentLoaded', function() {
    // Your existing initialization code...
    initializeDashboard();
    
    // Add grid/list toggle initialization
    setTimeout(() => {
        initializeViewToggle();
    }, 500);
    // Initialize auto-analysis system
    setTimeout(initializeAutoAnalysisSystem, 1000);
});

// Export enhanced functions
window.startAnalysisTracking = startAnalysisTracking;
window.stopAnalysisTracking = stopAnalysisTracking;
window.updateAnalysisStatus = updateAnalysisStatus;

// ============================================================================
// EXPORT GLOBAL FUNCTIONS
// ============================================================================

// Make functions available globally for HTML onclick handlers
window.selectCluster = selectCluster;
window.analyzeCluster = analyzeCluster;
window.removeCluster = removeCluster;
window.analyzeAllClusters = analyzeAllClusters;
window.showPortfolioAnalytics = showPortfolioAnalytics;
window.refreshCharts = refreshCharts;
window.exportReport = exportReport;
window.deployOptimizations = deployOptimizations;
window.scheduleOptimization = scheduleOptimization;
window.showNotification = showNotification;
window.showToast = showToast;
window.copyToClipboard = copyToClipboard;
window.switchToTab = switchToTab;
window.loadImplementationPlan = loadImplementationPlan;

// ============================================================================
// MAIN ENTRY POINT
// ============================================================================

/**
 * Single DOMContentLoaded event handler
 */
document.addEventListener('DOMContentLoaded', initializeDashboard);

// Export AppState for external access
window.AppState = AppState;
window.AppConfig = AppConfig;

console.log('✅ Enhanced AKS Cost Intelligence Dashboard loaded successfully');

// =======================
// Added UI improvements
// =======================

/**
 * Initializes grid/list view toggle functionality
 */
function initializeViewToggle() {
    console.log('🎯 Initializing grid/list view toggle...');
    
    const gridButton = document.querySelector('[data-view="grid"]');
    const listButton = document.querySelector('[data-view="list"]'); 
    const clusterGrid = document.getElementById('cluster-grid') || document.querySelector('.cluster-grid') || document.querySelector('.row');
    
    console.log('🔍 Grid button found:', !!gridButton);
    console.log('🔍 List button found:', !!listButton);
    console.log('🔍 Cluster grid found:', !!clusterGrid);
    
    if (!gridButton || !listButton) {
        console.warn('⚠️ View toggle buttons not found');
        return;
    }
    
    if (!clusterGrid) {
        console.warn('⚠️ Cluster grid container not found');
        return;
    }
    
    // Add click handlers
    gridButton.addEventListener('click', function(e) {
        e.preventDefault();
        console.log('📊 Switching to grid view');
        switchToGridView(gridButton, listButton, clusterGrid);
    });
    
    listButton.addEventListener('click', function(e) {
        e.preventDefault(); 
        console.log('📋 Switching to list view');
        switchToListView(gridButton, listButton, clusterGrid);
    });
    
    console.log('✅ Grid/List toggle initialized successfully');
}

/**
 * Switch to grid view
 */
function switchToGridView(gridButton, listButton, clusterGrid) {
    // Update button states
    gridButton.classList.add('active', 'view-toggle-active');
    listButton.classList.remove('active', 'view-toggle-active');
    
    // Update grid layout
    clusterGrid.classList.remove('list-view');
    clusterGrid.classList.add('grid-view');
    
    // Reset any list-specific styling
    const clusterCards = clusterGrid.querySelectorAll('.cluster-card');
    clusterCards.forEach(card => {
        card.style.display = '';
        card.classList.remove('list-item');
        
        const cardBody = card.querySelector('.card-body');
        if (cardBody) {
            cardBody.style.display = '';
            cardBody.style.flexDirection = '';
            cardBody.style.alignItems = '';
            cardBody.style.justifyContent = '';
            cardBody.style.width = '';
            cardBody.style.padding = '';
        }
        
        const clusterActions = card.querySelector('.cluster-actions');
        if (clusterActions) {
            clusterActions.style.position = '';
            clusterActions.style.opacity = '';
            clusterActions.style.transform = '';
            clusterActions.style.marginLeft = '';
        }
        
        const clusterInfo = card.querySelector('.cluster-info');
        if (clusterInfo) {
            clusterInfo.style.display = '';
            clusterInfo.style.alignItems = '';
            clusterInfo.style.gap = '';
            clusterInfo.style.flex = '';
        }
        
        const clusterMetrics = card.querySelector('.cluster-metrics');
        if (clusterMetrics) {
            clusterMetrics.style.display = '';
            clusterMetrics.style.gap = '';
            clusterMetrics.style.alignItems = '';
            clusterMetrics.style.flexDirection = '';
        }
    });
    
    // Update parent container if needed
    const parentRow = clusterGrid.closest('.row');
    if (parentRow) {
        parentRow.style.flexDirection = '';
    }
    
    console.log('✅ Switched to grid view');
}

/**
 * Switch to list view  
 */
function switchToListView(gridButton, listButton, clusterGrid) {
    // Update button states
    listButton.classList.add('active', 'view-toggle-active');
    gridButton.classList.remove('active', 'view-toggle-active');
    
    // Update grid layout
    clusterGrid.classList.add('list-view');
    clusterGrid.classList.remove('grid-view');
    
    // Apply list-specific styling
    const clusterCards = clusterGrid.querySelectorAll('.cluster-card');
    clusterCards.forEach(card => {
        card.classList.add('list-item');
        card.style.display = 'flex';
        card.style.alignItems = 'center';
        card.style.marginBottom = '1rem';
        
        const cardBody = card.querySelector('.card-body');
        if (cardBody) {
            cardBody.style.display = 'flex';
            cardBody.style.flexDirection = 'row';
            cardBody.style.alignItems = 'center';
            cardBody.style.justifyContent = 'space-between';
            cardBody.style.width = '100%';
            cardBody.style.padding = '1.5rem';
        }
        
        const clusterInfo = card.querySelector('.cluster-info');
        if (clusterInfo) {
            clusterInfo.style.display = 'flex';
            clusterInfo.style.alignItems = 'center';
            clusterInfo.style.gap = '1rem';
            clusterInfo.style.flex = '1';
        }
        
        const clusterMetrics = card.querySelector('.cluster-metrics');
        if (clusterMetrics) {
            clusterMetrics.style.display = 'flex';
            clusterMetrics.style.gap = '2rem';
            clusterMetrics.style.alignItems = 'center';
        }
        
        const clusterActions = card.querySelector('.cluster-actions');
        if (clusterActions) {
            clusterActions.style.position = 'static';
            clusterActions.style.opacity = '1';
            clusterActions.style.transform = 'none';
            clusterActions.style.marginLeft = '1rem';
        }
        
        // Adjust metric cards for list view
        const metricMinis = card.querySelectorAll('.metric-mini');
        metricMinis.forEach(mini => {
            mini.style.minWidth = '120px';
            mini.style.padding = '0.5rem';
            mini.style.margin = '0';
        });
    });
    
    // Update parent container for column layout
    const parentRow = clusterGrid.closest('.row');
    if (parentRow) {
        parentRow.style.flexDirection = 'column';
    }
    
    console.log('✅ Switched to list view');
}



/**
 * Enhanced Animations and Cost Savings Effects
 * Adds dynamic animations to cost savings elements and compact layout management
 */

// Enhanced Animation System
class AnimationManager {
    constructor() {
        this.savingsThreshold = 100; // Threshold for high savings animation
        this.init();
    }

    init() {
        this.setupContinuousAnimations();
        this.setupSavingsAnimations();
        this.setupCompactLayout();
        this.setupDynamicEffects();
    }

    /**
     * Setup continuous animations for brand icon and other elements
     */
    setupContinuousAnimations() {
        // Ensure Kubernetes icon spins continuously
        const brandIcon = document.querySelector('.brand-icon');
        if (brandIcon && !brandIcon.classList.contains('spinning-icon')) {
            brandIcon.classList.add('spinning-icon');
        }

        // Add floating animation to metric icons
        const metricIcons = document.querySelectorAll('.metric-icon');
        metricIcons.forEach((icon, index) => {
            icon.style.animationDelay = `${index * 0.5}s`;
        });
    }

    /**
     * Setup cost savings specific animations
     */
    setupSavingsAnimations() {
        // Enhanced savings metric card detection and animation
        this.updateSavingsCards();
        
        // Setup observer for dynamic content
        const observer = new MutationObserver(() => {
            this.updateSavingsCards();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class', 'id']
        });
    }

    /**
     * Update savings cards with animations based on values
     */
    updateSavingsCards() {
        // Find potential savings elements
        const savingsElements = [
            ...document.querySelectorAll('#potential-savings'),
            ...document.querySelectorAll('[id*="savings"]'),
            ...document.querySelectorAll('.metric-value:contains("$")')
        ];

        savingsElements.forEach(element => {
            const parentCard = element.closest('.metric-card');
            if (parentCard && this.isSavingsElement(element)) {
                this.applySavingsEffects(parentCard, element);
            }
        });

        // Handle mini metric savings
        this.updateMiniSavingsMetrics();
    }

    /**
     * Check if element represents savings
     */
    isSavingsElement(element) {
        const text = element.textContent?.toLowerCase() || '';
        const id = element.id?.toLowerCase() || '';
        
        return text.includes('savings') || 
               text.includes('save') || 
               id.includes('savings') || 
               id.includes('save') ||
               element.classList.contains('savings');
    }

    /**
     * Apply savings effects to metric cards
     */
    applySavingsEffects(card, valueElement) {
        // Add savings card class
        if (!card.classList.contains('savings-card')) {
            card.classList.add('savings-card');
        }

        // Parse savings value to determine intensity
        const value = this.parseMoneyValue(valueElement.textContent);
        
        if (value > this.savingsThreshold) {
            this.addHighSavingsEffects(card, valueElement);
        } else if (value > 50) {
            this.addMediumSavingsEffects(card, valueElement);
        } else if (value > 0) {
            this.addLowSavingsEffects(card, valueElement);
        }

        // Add cost efficiency badge
        this.addCostEfficiencyBadge(card, value);
    }

    /**
     * Add high savings effects
     */
    addHighSavingsEffects(card, valueElement) {
        card.style.animationDuration = '2s';
        
        // Create sparkle effect
        this.createSparkleEffect(card);
        
        // Add pulsing glow
        card.style.boxShadow = `
            0 8px 32px rgba(52, 199, 89, 0.4),
            0 0 50px rgba(52, 199, 89, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.2)
        `;
        
        // Animate the value with counting effect
        this.animateValueCounting(valueElement);
    }

    /**
     * Add medium savings effects
     */
    addMediumSavingsEffects(card, valueElement) {
        card.style.animationDuration = '3s';
        card.style.boxShadow = `
            0 6px 24px rgba(52, 199, 89, 0.3),
            0 0 30px rgba(52, 199, 89, 0.15)
        `;
    }

    /**
     * Add low savings effects
     */
    addLowSavingsEffects(card, valueElement) {
        card.style.animationDuration = '4s';
        card.style.boxShadow = `
            0 4px 16px rgba(52, 199, 89, 0.2),
            0 0 20px rgba(52, 199, 89, 0.1)
        `;
    }

    /**
     * Create sparkle effect for high savings
     */
    createSparkleEffect(card) {
        if (card.querySelector('.sparkle-container')) return;

        const sparkleContainer = document.createElement('div');
        sparkleContainer.className = 'sparkle-container';
        sparkleContainer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            overflow: hidden;
            border-radius: inherit;
        `;

        // Create multiple sparkles
        for (let i = 0; i < 8; i++) {
            const sparkle = document.createElement('div');
            sparkle.className = 'sparkle';
            sparkle.style.cssText = `
                position: absolute;
                width: 4px;
                height: 4px;
                background: radial-gradient(circle, #00ff88 0%, transparent 70%);
                border-radius: 50%;
                animation: sparkle-float ${2 + Math.random() * 3}s ease-in-out infinite;
                animation-delay: ${Math.random() * 2}s;
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
            `;
            sparkleContainer.appendChild(sparkle);
        }

        card.appendChild(sparkleContainer);
        
        // Add sparkle animation CSS if not exists
        this.addSparkleCSS();
    }

    /**
     * Add sparkle animation CSS
     */
    addSparkleCSS() {
        if (document.getElementById('sparkle-animations')) return;

        const style = document.createElement('style');
        style.id = 'sparkle-animations';
        style.textContent = `
            @keyframes sparkle-float {
                0%, 100% {
                    transform: translateY(0px) scale(0);
                    opacity: 0;
                }
                50% {
                    transform: translateY(-20px) scale(1);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Animate value counting effect
     */
    animateValueCounting(element) {
        const finalValue = this.parseMoneyValue(element.textContent);
        const duration = 2000;
        const startTime = Date.now();
        const startValue = 0;

        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function
            const easeOut = 1 - Math.pow(1 - progress, 3);
            
            const currentValue = startValue + (finalValue - startValue) * easeOut;
            element.textContent = `$${Math.round(currentValue).toLocaleString()}`;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.textContent = `$${finalValue.toLocaleString()}`;
            }
        };

        animate();
    }

    /**
     * Add cost efficiency badge
     */
    addCostEfficiencyBadge(card, value) {
        // Remove existing badge
        const existingBadge = card.querySelector('.cost-efficiency-badge');
        if (existingBadge) {
            existingBadge.remove();
        }

        const badge = document.createElement('div');
        badge.className = 'cost-efficiency-badge';
        
        if (value > 500) {
            badge.classList.add('high-savings');
            badge.textContent = '🔥 HIGH SAVINGS';
        } else if (value > 100) {
            badge.classList.add('medium-savings');
            badge.textContent = '💰 GOOD SAVINGS';
        } else if (value > 0) {
            badge.classList.add('low-savings');
            badge.textContent = '📈 SOME SAVINGS';
        }

        card.appendChild(badge);
    }

    /**
     * Update mini savings metrics
     */
    updateMiniSavingsMetrics() {
        const miniMetrics = document.querySelectorAll('.metric-mini');
        
        miniMetrics.forEach(mini => {
            const valueElement = mini.querySelector('.metric-value');
            const labelElement = mini.querySelector('.metric-label');
            
            if (valueElement && labelElement) {
                const label = labelElement.textContent.toLowerCase();
                const value = this.parseMoneyValue(valueElement.textContent);
                
                if (label.includes('savings') || label.includes('save')) {
                    mini.classList.add('savings-mini');
                    
                    if (value > 50) {
                        mini.style.animationDuration = '2s';
                    }
                }
            }
        });
    }

    /**
     * Setup compact layout management
     */
    setupCompactLayout() {
        // Apply compact spacing to containers
        const containers = document.querySelectorAll('.container, .container-fluid');
        containers.forEach(container => {
            container.classList.add('compact-spacing');
        });

        // Optimize metric grid layout
        this.optimizeMetricLayout();
        
        // Setup responsive mini metrics
        this.setupResponsiveMiniMetrics();
    }

    /**
     * Optimize metric layout for better space usage
     */
    optimizeMetricLayout() {
        const metricsRow = document.getElementById('metrics-row');
        if (metricsRow) {
            metricsRow.classList.add('metric-grid');
        }

        // Group mini metrics
        const miniMetrics = document.querySelectorAll('.metric-mini');
        if (miniMetrics.length > 2) {
            const container = miniMetrics[0].parentElement;
            const row = document.createElement('div');
            row.className = 'metric-mini-row';
            
            miniMetrics.forEach(mini => {
                row.appendChild(mini);
            });
            
            container.appendChild(row);
        }
    }

    /**
     * Setup responsive mini metrics
     */
    setupResponsiveMiniMetrics() {
        const handleResize = () => {
            const miniMetrics = document.querySelectorAll('.metric-mini');
            const screenWidth = window.innerWidth;
            
            miniMetrics.forEach(mini => {
                if (screenWidth < 768) {
                    mini.style.minWidth = 'auto';
                    mini.style.width = '100%';
                } else {
                    mini.style.minWidth = '80px';
                    mini.style.width = 'auto';
                }
            });
        };

        window.addEventListener('resize', handleResize);
        handleResize(); // Initial call
    }

    /**
     * Setup dynamic effects based on data changes
     */
    setupDynamicEffects() {
        // Monitor for data updates
        this.setupDataUpdateEffects();
        
        // Setup hover enhancement effects
        this.setupHoverEffects();
        
        // Setup loading state animations
        this.setupLoadingAnimations();
    }

    /**
     * Setup data update effects
     */
    setupDataUpdateEffects() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' || mutation.type === 'characterData') {
                    const target = mutation.target;
                    
                    // If a metric value was updated
                    if (target.classList?.contains('metric-value') || 
                        target.parentElement?.classList?.contains('metric-value')) {
                        this.animateDataUpdate(target);
                    }
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
    }

    /**
     * Animate data updates
     */
    animateDataUpdate(element) {
        const metricElement = element.classList?.contains('metric-value') ? 
            element : element.closest('.metric-value');
        
        if (metricElement) {
            metricElement.style.transform = 'scale(1.1)';
            metricElement.style.transition = 'transform 0.3s ease';
            
            setTimeout(() => {
                metricElement.style.transform = 'scale(1)';
            }, 300);
            
            // Add update indicator
            this.addUpdateIndicator(metricElement);
        }
    }

    /**
     * Add update indicator
     */
    addUpdateIndicator(element) {
        const indicator = document.createElement('div');
        indicator.style.cssText = `
            position: absolute;
            top: -5px;
            right: -5px;
            width: 8px;
            height: 8px;
            background: #00ff88;
            border-radius: 50%;
            animation: pulse-indicator 1s ease-in-out 3;
            z-index: 10;
        `;
        
        element.style.position = 'relative';
        element.appendChild(indicator);
        
        setTimeout(() => {
            indicator.remove();
        }, 3000);
        
        // Add pulse indicator CSS if not exists
        this.addPulseIndicatorCSS();
    }

    /**
     * Add pulse indicator CSS
     */
    addPulseIndicatorCSS() {
        if (document.getElementById('pulse-indicator-animations')) return;

        const style = document.createElement('style');
        style.id = 'pulse-indicator-animations';
        style.textContent = `
            @keyframes pulse-indicator {
                0%, 100% {
                    transform: scale(1);
                    opacity: 1;
                }
                50% {
                    transform: scale(1.5);
                    opacity: 0.7;
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Setup enhanced hover effects
     */
    setupHoverEffects() {
        // Enhanced metric card hover effects
        const metricCards = document.querySelectorAll('.metric-card');
        metricCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                const icon = card.querySelector('.metric-icon');
                if (icon) {
                    icon.style.transform = 'scale(1.2) rotate(10deg)';
                    icon.style.filter = 'brightness(1.2)';
                }
            });
            
            card.addEventListener('mouseleave', () => {
                const icon = card.querySelector('.metric-icon');
                if (icon) {
                    icon.style.transform = '';
                    icon.style.filter = '';
                }
            });
        });

        // Enhanced cluster card hover effects
        const clusterCards = document.querySelectorAll('.cluster-card');
        clusterCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                const miniMetrics = card.querySelectorAll('.metric-mini');
                miniMetrics.forEach((mini, index) => {
                    setTimeout(() => {
                        mini.style.transform = 'translateY(-4px) scale(1.05)';
                    }, index * 100);
                });
            });
            
            card.addEventListener('mouseleave', () => {
                const miniMetrics = card.querySelectorAll('.metric-mini');
                miniMetrics.forEach(mini => {
                    mini.style.transform = '';
                });
            });
        });
    }

    /**
     * Setup loading animations
     */
    setupLoadingAnimations() {
        const loadingElements = document.querySelectorAll('.loading, .loading-spinner');
        loadingElements.forEach(element => {
            if (!element.querySelector('.enhanced-loading-indicator')) {
                this.addEnhancedLoadingIndicator(element);
            }
        });
    }

    /**
     * Add enhanced loading indicator
     */
    addEnhancedLoadingIndicator(element) {
        const indicator = document.createElement('div');
        indicator.className = 'enhanced-loading-indicator';
        indicator.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, 
                transparent 0%, 
                rgba(0, 122, 255, 0.2) 50%, 
                transparent 100%);
            animation: loading-shimmer 2s ease-in-out infinite;
            border-radius: inherit;
            pointer-events: none;
        `;
        
        element.style.position = 'relative';
        element.appendChild(indicator);
        
        // Add loading shimmer CSS if not exists
        this.addLoadingShimmerCSS();
    }

    /**
     * Add loading shimmer CSS
     */
    addLoadingShimmerCSS() {
        if (document.getElementById('loading-shimmer-animations')) return;

        const style = document.createElement('style');
        style.id = 'loading-shimmer-animations';
        style.textContent = `
            @keyframes loading-shimmer {
                0% {
                    transform: translateX(-100%);
                }
                100% {
                    transform: translateX(100%);
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Parse money value from text
     */
    parseMoneyValue(text) {
        if (!text) return 0;
        
        // Remove currency symbols, commas, and extract numbers
        const cleaned = text.replace(/[$,\s]/g, '');
        const number = parseFloat(cleaned) || 0;
        
        return number;
    }

    /**
     * Public method to trigger savings animation on specific element
     */
    triggerSavingsAnimation(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            const card = element.closest('.metric-card');
            if (card) {
                this.applySavingsEffects(card, element);
                if (value > this.savingsThreshold) {
                    this.animateValueCounting(element);
                }
            }
        }
    }

    /**
     * Public method to update all animations
     */
    refreshAnimations() {
        this.updateSavingsCards();
        this.setupContinuousAnimations();
    }
}

// Initialize animation manager
let animationManager;

// Enhanced initialization
document.addEventListener('DOMContentLoaded', function() {
    animationManager = new AnimationManager();
    
    // Add continuous spinning to brand icon immediately
    const brandIcon = document.querySelector('.brand-icon');
    if (brandIcon) {
        brandIcon.style.animation = 'continuous-spin 8s linear infinite';
    }
    
    console.log('✨ Enhanced animations initialized');
});

// Export for global use
window.AnimationManager = AnimationManager;
window.animationManager = animationManager;

// Enhanced utility functions for external use
window.triggerSavingsAnimation = function(elementId, value) {
    if (animationManager) {
        animationManager.triggerSavingsAnimation(elementId, value);
    }
};

window.refreshAnimations = function() {
    if (animationManager) {
        animationManager.refreshAnimations();
    }
};

// Auto-refresh animations when data changes
window.updateDashboardMetrics = function(metrics) {
    // Original function logic here
    console.log('📊 Updating metrics:', metrics);
    
    const metricUpdates = [
        { selectors: ['#current-cost'], value: metrics.total_cost, format: 'currency' },
        { selectors: ['#potential-savings'], value: metrics.total_savings, format: 'currency' },
        { selectors: ['#hpa-efficiency'], value: metrics.hpa_reduction, format: 'percentage' },
        { selectors: ['#optimization-score'], value: calculateOptimizationScore(metrics), format: 'number' },
        { selectors: ['#savings-percentage'], value: metrics.savings_percentage, format: 'percentage' },
        { selectors: ['#annual-savings'], value: metrics.annual_savings, format: 'currency' }
    ];
    
    metricUpdates.forEach((metric, index) => {
        animateMetricUpdate(metric, index * 100);
    });
    
    // Trigger enhanced animations for savings
    if (metrics.total_savings > 0) {
        setTimeout(() => {
            if (animationManager) {
                animationManager.triggerSavingsAnimation('potential-savings', metrics.total_savings);
                animationManager.refreshAnimations();
            }
        }, 500);
    }
    
    updateCostTrend(metrics);
    updateDataSourceIndicator(metrics);
};

// Enhanced form analysis submit handler
window.handleAnalysisSubmit = function(event) {
    event.preventDefault();
    
    if (!validateAnalysisForm()) return;
    
    console.log('📊 Enhanced form submitted for analysis');
    const btn = document.getElementById('analyzeBtn');
    const progress = document.getElementById('analysisProgress');
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');
    
    // Enhanced loading state with animations
    if (btn) {
        btn.classList.add('loading');
        btn.disabled = true;
        
        // Add enhanced loading effect
        if (animationManager) {
            animationManager.addEnhancedLoadingIndicator(btn);
        }
    }
    
    if (progress) progress.classList.add('visible');

    // Enhanced progress steps with animations
    const progressSteps = [
        { percentage: 10, text: '🔌 Connecting to Azure...', color: '#007AFF' },
        { percentage: 25, text: '💰 Fetching cost data...', color: '#5AC8FA' },
        { percentage: 45, text: '📊 Analyzing cluster metrics...', color: '#AF52DE' },
        { percentage: 65, text: '🎯 Calculating optimization opportunities...', color: '#FF9500' },
        { percentage: 85, text: '💡 Generating insights...', color: '#34C759' },
        { percentage: 95, text: '✨ Finalizing analysis...', color: '#00C851' }
    ];
    
    let stepIndex = 0;
    function advanceProgress() {
        if (stepIndex < progressSteps.length && fill && text) {
            const step = progressSteps[stepIndex];
            fill.style.width = step.percentage + '%';
            fill.style.background = `linear-gradient(90deg, ${step.color}, ${step.color}dd)`;
            text.textContent = step.text;
            
            // Add ripple effect
            fill.style.boxShadow = `0 0 20px ${step.color}44`;
            
            stepIndex++;
            setTimeout(advanceProgress, 800);
        }
    }
    advanceProgress();

    // Submit analysis with enhanced completion handling
    fetch('/analyze', { 
        method: 'POST', 
        body: new FormData(event.target) 
    })
    .then(response => {
        if (!response.ok) throw new Error(response.statusText);
        return response.text();
    })
    .then(() => {
        if (fill) {
            fill.style.width = '100%';
            fill.style.background = 'linear-gradient(90deg, #00C851, #32CD32)';
            fill.style.boxShadow = '0 0 30px #00C85144';
        }
        if (text) text.textContent = '🎉 Analysis completed successfully!';
        
        AppState.analysisCompleted = true;
        
        setTimeout(() => {
            showNotification('🎉 Analysis completed! Found significant optimization opportunities.', 'success');
            
            // Enhanced completion effects
            if (animationManager) {
                // Create celebration effect
                document.body.style.animation = 'celebration-flash 0.5s ease-in-out';
                setTimeout(() => {
                    document.body.style.animation = '';
                }, 500);
            }
            
            setTimeout(() => {
                switchToTab('#dashboard');
                resetAnalysisForm();
                initializeCharts();
                
                // Refresh all animations after switching tabs
                setTimeout(() => {
                    if (animationManager) {
                        animationManager.refreshAnimations();
                    }
                }, 1000);
            }, 1500);
        }, 1000);
    })
    .catch(error => {
        console.error('❌ Analysis failed:', error);
        showNotification('❌ Analysis failed: ' + error.message, 'error');
        resetAnalysisForm();
    });

    function resetAnalysisForm() {
        if (btn) {
            btn.classList.remove('loading');
            btn.disabled = false;
            
            // Remove loading indicator
            const loadingIndicator = btn.querySelector('.enhanced-loading-indicator');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
        }
        if (progress) progress.classList.remove('visible');
        if (fill) {
            fill.style.width = '0%';
            fill.style.background = '';
            fill.style.boxShadow = '';
        }
        if (text) text.textContent = 'Initializing analysis...';
        stepIndex = 0;
    }
};

// Add celebration flash CSS
const celebrationStyle = document.createElement('style');
celebrationStyle.textContent = `
    @keyframes celebration-flash {
        0%, 100% { background: var(--glass-bg-primary); }
        50% { background: linear-gradient(45deg, rgba(0, 199, 81, 0.1), rgba(50, 205, 50, 0.1)); }
    }
`;
document.head.appendChild(celebrationStyle);

console.log('🚀 Enhanced animations and cost savings effects loaded');

window.initializeViewToggle = initializeViewToggle;
window.switchToGridView = switchToGridView;
window.switchToListView = switchToListView;