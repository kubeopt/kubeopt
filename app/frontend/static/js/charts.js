/**
 * ============================================================================
 * AKS COST INTELLIGENCE - CHART MANAGEMENT
 * ============================================================================
 * Chart initialization, data handling, and visualization management
 * ============================================================================
 */

import { AppState, AppConfig } from './config.js';
import { showNotification } from './notifications.js';
import { getChartColors, formatValue, calculateOptimizationScore, getAccuracyBadgeClass } from './utils.js';


// Global cluster state with validation
window.currentClusterState = {
    clusterId: null,
    clusterName: null,
    resourceGroup: null,
    lastUpdated: null,
    validated: false
};

/**
 * CRITICAL: Extract cluster ID from current URL - not cached state
 */
export function getCurrentClusterId() {
    const path = window.location.pathname;
    const match = path.match(/\/cluster\/([^\/\?]+)/);
    
    if (match && match[1]) {
        const clusterId = match[1];
        console.log(`🎯 CLUSTER ID from URL: ${clusterId}`);
        
        // Validate this is the expected cluster
        if (window.currentClusterState.clusterId && 
            window.currentClusterState.clusterId !== clusterId) {
            console.error(`🚨 CLUSTER MISMATCH DETECTED!`);
            console.error(`   Expected: ${window.currentClusterState.clusterId}`);
            console.error(`   Current:  ${clusterId}`);
            
            // Force page refresh to sync state
            window.location.reload();
            return null;
        }
        
        // Update global state
        window.currentClusterState.clusterId = clusterId;
        window.currentClusterState.lastUpdated = new Date().toISOString();
        window.currentClusterState.validated = true;
        
        return clusterId;
    }
    
    console.error('❌ CRITICAL: No cluster ID found in URL!');
    console.error(`   Current URL: ${window.location.pathname}`);
    return null;
}

/**
 * CRITICAL: Validate cluster context before ANY action
 */
export function validateClusterContext(actionName) {
    const currentClusterId = getCurrentClusterId();
    const expectedCluster = window.currentClusterState.clusterId;
    
    if (!currentClusterId) {
        console.error(`❌ No cluster context for action: ${actionName}`);
        return false;
    }
    
    if (expectedCluster && currentClusterId !== expectedCluster) {
        console.error(`❌ CLUSTER MISMATCH in ${actionName}!`);
        console.error(`   Expected: ${expectedCluster}`);
        console.error(`   Current:  ${currentClusterId}`);
        return false;
    }
    
    console.log(`✅ Cluster context validated for ${actionName}: ${currentClusterId}`);
    return true;
}

/**
 * CRITICAL: Make cluster-aware API calls
 */
export function makeClusterAwareAPICall(endpoint, options = {}) {
    const clusterId = getCurrentClusterId();
    
    if (!clusterId) {
        console.error('❌ CRITICAL: Cannot make API call without cluster ID!');
        return Promise.reject(new Error('No cluster ID available'));
    }
    
    // Add cluster_id parameter to all requests
    const separator = endpoint.includes('?') ? '&' : '?';
    const clusterAwareEndpoint = `${endpoint}${separator}cluster_id=${clusterId}`;
    
    console.log(`🔒 Cluster-aware API call: ${clusterAwareEndpoint}`);
    
    // Add cluster isolation headers
    const headers = {
        'X-Cluster-ID': clusterId,
        'X-Request-Source': 'cluster-dashboard',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        ...options.headers
    };
    
    return fetch(clusterAwareEndpoint, {
        ...options,
        headers
    });
}

/**
 * FIXED: Initializes all dashboard charts with cluster isolation + insights
 */
export function initializeCharts() {
    console.log('📊 Initializing charts with cluster isolation...');
    
    if (!validateClusterContext('initializeCharts')) {
        console.error('❌ BLOCKED: initializeCharts - invalid cluster context');
        return;
    }
    
    makeClusterAwareAPICall('/api/chart-data')
        .then(response => {
            console.log('📡 Cluster-isolated chart data response status:', response.status);
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            return response.json();
        })
        .then(data => {
            console.log('📈 Cluster-isolated chart data received:', data);
            
            // Validate the response
            if (data.status !== 'success') {
                throw new Error(data.message || 'Invalid API response');
            }
            
            if (!data.metrics) {
                throw new Error('No metrics data in response');
            }
            
            // Log the actual values we're working with
            console.log('💰 Cost:', data.metrics.total_cost);
            console.log('💵 Savings:', data.metrics.total_savings);
            
            // Update metrics FIRST
            updateDashboardMetrics(data.metrics);
            
            // Then create charts
            createAllCharts(data);
            
            // FIXED: Update insights using the same data (NO DUPLICATE API CALL)
            if (typeof window.updateRealDynamicInsights === 'function') {
                console.log('📊 Updating insights with chart data...');
                window.updateRealDynamicInsights(data);
            }
            
            // Clear loading states after successful chart creation
            setTimeout(() => {
                clearLoadingStates();
                //updateDataSourceIndicator(data.metadata || {});
                
                // Create insight notifications if available
                if (typeof window.createInsightNotification === 'function') {
                    const insights = window.generateRealDynamicInsights ? window.generateRealDynamicInsights(data) : {};
                    window.createInsightNotification(insights);
                }
            }, 1000);
            
            console.log('✅ Cluster-isolated charts AND insights initialized successfully');
        })
        .catch(error => {
            console.error('❌ Cluster-isolated chart initialization failed:', error);
            showChartError('Unable to load data for current cluster: ' + error.message);
            
            // Don't fall back to sample data - show the error
            const errorMessage = `Failed to load analysis data for current cluster: ${error.message}. Please run analysis first.`;
            showNotification(errorMessage, 'error');
        });
}

/**
 * Enhanced chart refresh with cluster isolation
 */
export function refreshChartsSmooth() {
    if (!validateClusterContext('refreshChartsSmooth')) {
        console.error('❌ BLOCKED: refreshChartsSmooth - invalid cluster context');
        return;
    }
    
    if (window.smoothNotificationManager) {
        window.smoothNotificationManager.show('Refreshing charts for current cluster...', 'info', 3000);
    }
    
    // Clear any stale cache for current cluster
    const clusterId = getCurrentClusterId();
    if (clusterId) {
        makeClusterAwareAPICall('/api/cache/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cluster_id: clusterId })
        }).then(() => {
            console.log(`🧹 Cleared cache for cluster: ${clusterId}`);
            
            // Now refresh charts
            initializeCharts();
        }).catch(error => {
            console.error('Cache clear error:', error);
            // Still try to refresh charts
            initializeCharts();
        });
    }
}

// Make cluster isolation functions globally available
if (typeof window !== 'undefined') {
    window.getCurrentClusterId = getCurrentClusterId;
    window.validateClusterContext = validateClusterContext;
    window.makeClusterAwareAPICall = makeClusterAwareAPICall;
    window.refreshChartsSmooth = refreshChartsSmooth;
}

/**
 * Updates dashboard metrics with animation
 */
export function updateDashboardMetrics(metrics) {
    console.log('📊 Updating metrics with comprehensive element targeting:', metrics);
    
    // Validate metrics object
    if (!metrics || typeof metrics !== 'object') {
        console.error('❌ Invalid metrics object:', metrics);
        return;
    }
    
    // Calculate optimization score if not provided
    const optimizationScore = metrics.optimization_score || calculateOptimizationScore(metrics);
    
    // Calculate HPA efficiency if not provided
    const hpaEfficiency = metrics.hpa_efficiency || metrics.hpa_reduction || 0;
    
    // Enhanced metric updates with multiple selectors
    const metricUpdates = [
        { 
            selectors: ['#current-cost'], 
            value: metrics.total_cost, 
            format: 'currency',
            label: 'Current Monthly Cost'
        },
        { 
            selectors: ['#potential-savings', '#monthly-savings'], 
            value: metrics.total_savings, 
            format: 'currency',
            label: 'Potential Monthly Savings'
        },
        { 
            selectors: ['#hpa-efficiency'], 
            value: hpaEfficiency, 
            format: 'percentage',
            label: 'HPA Efficiency'
        },
        { 
            selectors: ['#optimization-score'], 
            value: optimizationScore, 
            format: 'number',
            label: 'Optimization Score'
        },
        { 
            selectors: ['#savings-percentage'], 
            value: metrics.savings_percentage, 
            format: 'percentage',
            label: 'Savings Percentage'
        },
        { 
            selectors: ['#annual-savings'], 
            value: metrics.annual_savings, 
            format: 'currency',
            label: 'Annual Savings'
        }
    ];
    
    // Log each update for debugging
    metricUpdates.forEach((metric, index) => {
        console.log(`📊 Updating metric ${index} (${metric.label}):`, metric.selectors[0], '=', metric.value);
        animateMetricUpdate(metric, index * 100);
    });
    
    // Update specific savings elements
    updateSpecificSavingsElements(metrics);
    
    // Update savings breakdown mini elements
    updateSavingsBreakdownMini(metrics);
    
    updateCostTrend(metrics);
}

/**
 * Update specific savings elements
 */
function updateSpecificSavingsElements(metrics) {
    console.log('🔧 Updating specific savings elements');
    
    // Update monthly savings in multiple locations
    const monthlySavingsElements = [
        '#monthly-savings',
        '#potential-savings',
        '#action-savings'
    ];
    
    monthlySavingsElements.forEach(selector => {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = formatValue(metrics.total_savings || 0, 'currency');
            console.log(`Updated ${selector} to: ${element.textContent}`);
        }
    });
    
    // Update annual savings
    const annualSavingsElement = document.querySelector('#annual-savings');
    if (annualSavingsElement) {
        annualSavingsElement.textContent = formatValue(metrics.annual_savings || 0, 'currency');
    }
    
    // Update savings percentage
    const savingsPercentageElements = document.querySelectorAll('#savings-percentage');
    savingsPercentageElements.forEach(element => {
        element.textContent = `${(metrics.savings_percentage || 0).toFixed(1)}% potential savings`;
    });
}

/**
 * Update savings breakdown mini elements
 */
function updateSavingsBreakdownMini(metrics) {
    console.log('🔧 Updating savings breakdown mini elements');
    
    const hpaElement = document.getElementById('hpa-savings-mini');
    const rightsizingElement = document.getElementById('rightsizing-savings-mini');
    const storageElement = document.getElementById('storage-savings-mini');
    
    if (hpaElement) {
        hpaElement.textContent = formatValue(metrics.hpa_savings || 0, 'currency');
    }
    if (rightsizingElement) {
        rightsizingElement.textContent = formatValue(metrics.right_sizing_savings || 0, 'currency');
    }
    if (storageElement) {
        storageElement.textContent = formatValue(metrics.storage_savings || 0, 'currency');
    }
    
    // Update gap displays
    const cpuGapElement = document.getElementById('cpu-gap-display');
    const memoryGapElement = document.getElementById('memory-gap-display');
    
    if (cpuGapElement) {
        cpuGapElement.textContent = (metrics.cpu_gap || 0).toFixed(1);
    }
    if (memoryGapElement) {
        memoryGapElement.textContent = (metrics.memory_gap || 0).toFixed(1);
    }
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
// export function updateDataSourceIndicator(metadata) {
//     const isRealData = !metadata.is_sample_data;
//     let indicator = document.querySelector('#data-source-indicator');
    
//     if (!indicator) {
//         indicator = document.createElement('div');
//         indicator.id = 'data-source-indicator';
//         indicator.className = 'data-source-indicator';
//         document.body.appendChild(indicator);
//     }
    
//     // Better positioning to avoid overlap
//     indicator.style.cssText = `
//         position: fixed;
//         top: 140px;
//         right: 20px;
//         z-index: 999;
//         max-width: 200px;
//     `;
    
//     indicator.innerHTML = `
//         <div class="data-source-badge ${isRealData ? 'real-data' : 'sample-data'}">
//             <i class="fas fa-${isRealData ? 'cloud' : 'flask'}"></i>
//             <span>${isRealData ? 'Live Azure Data' : 'Demo Mode'}</span>
//             <small>${metadata.data_source || ''}</small>
//         </div>
//     `;
// }

/**
 * Creates all charts from provided data
 */
export function createAllCharts(data) {
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
export function destroyAllCharts() {
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
export function createCostBreakdownChart(data, isRealData) {
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
export function createMainTrendChart(data, isRealData) {
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
export function createHPAComparisonChart(data, isRealData) {
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
export function createNodeUtilizationChart(data, isRealData) {
    const canvas = document.getElementById('nodeUtilizationChart');
    if (!canvas) {
        console.warn('⚠️ Node utilization chart canvas not found');
        return;
    }

    console.log('🔧 Creating node utilization chart with data:', data);

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();
    
    // Enhanced data validation and processing
    const nodes = data.nodes || [];
    const cpuRequest = data.cpuRequest || [];
    const cpuActual = data.cpuActual || [];
    const memoryRequest = data.memoryRequest || [];
    const memoryActual = data.memoryActual || [];
    
    console.log(`🔧 Raw data arrays:`, {
        nodesLength: nodes.length,
        cpuRequestLength: cpuRequest.length,
        cpuActualLength: cpuActual.length,
        memoryRequestLength: memoryRequest.length,
        memoryActualLength: memoryActual.length
    });
    
    // If arrays are empty but we have node names, this means the data structure is different
    if (nodes.length === 0) {
        console.warn('⚠️ No node data available for chart');
        canvas.parentElement.innerHTML = '<div class="text-center text-muted p-4">No node utilization data available</div>';
        return;
    }
    
    // If the utilization arrays are empty, extract data from a different structure
    let finalNodes = nodes;
    let finalCpuRequest = cpuRequest;
    let finalCpuActual = cpuActual;
    let finalMemoryRequest = memoryRequest;
    let finalMemoryActual = memoryActual;
    
    // Check if data is in a different format (like from the consistent analysis)
    if (cpuRequest.length === 0 && typeof nodes[0] === 'object') {
        console.log('🔧 Extracting data from object format nodes');
        
        finalNodes = nodes.map(node => node.name || node.node_name || 'Unknown');
        finalCpuRequest = nodes.map(node => parseFloat(node.cpu_request_pct || node.cpu_request || 0));
        finalCpuActual = nodes.map(node => parseFloat(node.cpu_usage_pct || node.cpu_actual || 0));
        finalMemoryRequest = nodes.map(node => parseFloat(node.memory_request_pct || node.memory_request || 0));
        finalMemoryActual = nodes.map(node => parseFloat(node.memory_usage_pct || node.memory_actual || 0));
        
        console.log('🔧 Extracted data:', {
            nodes: finalNodes,
            cpuRequest: finalCpuRequest,
            cpuActual: finalCpuActual,
            memoryRequest: finalMemoryRequest,
            memoryActual: finalMemoryActual
        });
    }
    
    // Validate we have actual data
    if (finalNodes.length === 0 || finalCpuActual.every(val => val === 0)) {
        console.warn('⚠️ No valid utilization data found');
        canvas.parentElement.innerHTML = '<div class="text-center text-muted p-4">No valid node utilization data found</div>';
        return;
    }

    const config = {
        type: 'bar',
        data: {
            labels: finalNodes,
            datasets: [
                {
                    label: 'CPU Request %',
                    data: finalCpuRequest,
                    backgroundColor: 'rgba(52, 152, 219, 0.3)',
                    borderColor: '#3498db',
                    borderWidth: 2,
                    order: 2
                },
                {
                    label: 'CPU Actual %',
                    data: finalCpuActual,
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderColor: '#e74c3c',
                    borderWidth: 2,
                    order: 1
                },
                {
                    label: 'Memory Request %',
                    data: finalMemoryRequest,
                    backgroundColor: 'rgba(155, 89, 182, 0.3)',
                    borderColor: '#9b59b6',
                    borderWidth: 2,
                    order: 4
                },
                {
                    label: 'Memory Actual %',
                    data: finalMemoryActual,
                    backgroundColor: 'rgba(46, 204, 113, 0.7)',
                    borderColor: '#2ecc71',
                    borderWidth: 2,
                    order: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    labels: { color: colors.textColor },
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { 
                        color: colors.textColor,
                        maxRotation: 45
                    },
                    grid: { color: colors.gridColor }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        color: colors.textColor,
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: { color: colors.gridColor },
                    title: {
                        display: true,
                        text: 'Utilization %',
                        color: colors.textColor
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    };

    // Destroy existing chart if it exists
    if (AppState.chartInstances['nodeUtilizationChart']) {
        AppState.chartInstances['nodeUtilizationChart'].destroy();
    }

    AppState.chartInstances['nodeUtilizationChart'] = new Chart(ctx, config);
    console.log('✅ Node utilization chart created successfully with real data');
}

/**
 * Creates savings breakdown chart
 */
export function createSavingsBreakdownChart(data, isRealData) {
    const canvas = document.getElementById('savingsBreakdownChart');
    if (!canvas) {
        console.warn('⚠️ Savings breakdown chart canvas not found');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();
    
    console.log('🔧 Creating savings breakdown chart with data:', data);

    // Validate data and filter out zero values
    const categories = data.categories || [];
    const values = data.values || [];
    
    // Filter out zero/negative values for better visualization
    const filteredData = categories.map((category, index) => ({
        category: category,
        value: Math.max(0, values[index] || 0)
    })).filter(item => item.value > 0);
    
    if (filteredData.length === 0) {
        console.warn('⚠️ No savings data to display');
        canvas.parentElement.innerHTML = '<div class="text-center text-muted p-4">No savings opportunities identified</div>';
        return;
    }
    
    console.log(`🔧 Processing ${filteredData.length} savings categories:`, filteredData);

    const config = {
        type: 'pie',
        data: {
            labels: filteredData.map(item => item.category),
            datasets: [{
                data: filteredData.map(item => item.value),
                backgroundColor: ['#3498db', '#e74c3c', '#2ecc71'],
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
                    position: 'bottom',
                    labels: {
                        color: colors.textColor,
                        padding: 10,
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

    // Destroy existing chart if it exists
    if (AppState.chartInstances['savingsBreakdownChart']) {
        AppState.chartInstances['savingsBreakdownChart'].destroy();
    }

    AppState.chartInstances['savingsBreakdownChart'] = new Chart(ctx, config);
    console.log('✅ Savings breakdown chart created successfully');
}

/**
 * Creates namespace cost chart
 */
export function createNamespaceCostChart(data) {
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
export function createWorkloadCostChart(data) {
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
export function showChartError(message) {
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

/**
 * Clears all loading states after analysis completion
 */
export function clearLoadingStates() {
    console.log('🧹 Clearing all loading states...');
    
    // Clear insight loading states
    const insightElements = [
        { selector: '#cost-insight', defaultText: 'VM Scale Sets consume 68% of your monthly budget. Consider implementing right-sizing recommendations.' },
        { selector: '#hpa-insight', defaultText: 'Memory-based HPA could reduce replica count by 23%, saving approximately $140/month.' }
    ];
    
    insightElements.forEach(({ selector, defaultText }) => {
        const element = document.querySelector(selector);
        if (element) {
            const loadingSpan = element.querySelector('.loading-text');
            if (loadingSpan) {
                element.innerHTML = defaultText;
                console.log(`✅ Cleared loading state for ${selector}`);
            }
        }
    });
    
    // Update metric labels that show "Run analysis to view"
    const metricLabels = [
        { selector: '#hpa-efficiency', parentSelector: '.metric-card', labelText: 'Memory-based optimization' },
        { selector: '#optimization-score', parentSelector: '.metric-card', labelText: 'Overall efficiency rating' }
    ];
    
    metricLabels.forEach(({ selector, parentSelector, labelText }) => {
        const metricElement = document.querySelector(selector);
        if (metricElement && metricElement.textContent === '--') {
            const parent = metricElement.closest(parentSelector);
            if (parent) {
                const labelElement = parent.querySelector('.text-muted');
                if (labelElement && labelElement.textContent.includes('Run analysis to view')) {
                    labelElement.innerHTML = `<i class="fas fa-info-circle me-1"></i>${labelText}`;
                }
            }
        }
    });
}

// Make functions available globally for backward compatibility
if (typeof window !== 'undefined') {
    window.initializeCharts = initializeCharts;
    window.updateDashboardMetrics = updateDashboardMetrics;
    //window.updateDataSourceIndicator = updateDataSourceIndicator;
    window.createAllCharts = createAllCharts;
    window.destroyAllCharts = destroyAllCharts;
    window.clearLoadingStates = clearLoadingStates;
    window.showChartError = showChartError;
}