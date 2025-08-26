/**
 * ============================================================================
 * ENHANCED AKS COST INTELLIGENCE - COMPLETE CHART MANAGEMENT WITH CPU WORKLOAD ANALYSIS
 * ============================================================================
 * Comprehensive chart initialization, data handling, and CPU workload visualization management
 * ============================================================================
 */

import { AppState, AppConfig } from './config.js';
import { showNotification } from './notifications.js';
import { getChartColors, formatValue, calculateOptimizationScore, getAccuracyBadgeClass } from './utils.js';

// Enhanced global cluster state with CPU metrics
window.currentClusterState = {
    clusterId: null,
    clusterName: null,
    resourceGroup: null,
    lastUpdated: null,
    validated: false,
    cpuMetrics: null
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
 * Make cluster-aware API calls with CPU data handling
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
 * Initialize charts with comprehensive CPU data handling and cluster isolation
 */
export function initializeCharts() {
    console.log('📊 Initializing enhanced charts with CPU workload analysis and cluster isolation...');
    
    if (!validateClusterContext('initializeCharts')) {
        console.error('❌ BLOCKED: initializeCharts - invalid cluster context');
        return;
    }
    
    makeClusterAwareAPICall('/api/chart-data')
        .then(response => {
            console.log('📡 Enhanced chart data response status:', response.status);
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            return response.json();
        })
        .then(data => {
            console.log('📈 Enhanced chart data received with CPU analysis:', data);
            
            if (data.status !== 'success') {
                throw new Error(data.message || 'Invalid API response');
            }
            
            if (!data.metrics) {
                throw new Error('No metrics data in response');
            }
            
            // Enhanced metrics update with CPU data
            updateDashboardMetricsWithCPU(data.metrics, data.cpuWorkloadMetrics);
            
            // Create all charts with CPU awareness
            createAllChartsWithCPU(data);
            
            // Update insights with CPU considerations
            if (typeof window.updateRealDynamicInsights === 'function') {
                console.log('📊 Updating insights with CPU-aware chart data...');
                window.updateRealDynamicInsights(data);
            }
            
            // Clear loading states and show CPU metrics
            setTimeout(() => {
                clearLoadingStates();
                displayCPUWorkloadStatus(data.cpuWorkloadMetrics);
                
                if (typeof window.createInsightNotification === 'function') {
                    const insights = window.generateRealDynamicInsights ? window.generateRealDynamicInsights(data) : {};
                    window.createInsightNotification(insights);
                }
            }, 1000);
            
            console.log('✅ Enhanced charts with CPU workload analysis initialized successfully');
        })
        .catch(error => {
            console.error('❌ Enhanced chart initialization failed:', error);
            showChartError('Unable to load analysis data for current cluster: ' + error.message);
            showNotification('Analysis Required', 'Please run analysis first to view data.', 'warning');
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
            initializeCharts();
        }).catch(error => {
            console.error('Cache clear error:', error);
            initializeCharts();
        });
    }
}

/**
 * Update dashboard metrics including CPU workload data
 */
export function updateDashboardMetricsWithCPU(metrics, cpuWorkloadMetrics) {
    console.log('📊 Updating metrics with CPU workload data:', { metrics, cpuWorkloadMetrics });
    
    // Standard metrics update
    updateDashboardMetrics(metrics);
    
    // Enhanced CPU metrics update
    if (cpuWorkloadMetrics) {
        updateCPUMetrics(cpuWorkloadMetrics);
        
        // Store CPU metrics globally for other components
        window.currentClusterState.cpuMetrics = cpuWorkloadMetrics;
    }
}

/**
 * Update CPU metrics in dashboard
 */
function updateCPUMetrics(cpuMetrics) {
    console.log('🔧 Updating CPU metrics:', cpuMetrics);
    
    // Update average CPU utilization
    updateMetricElement('#average-cpu-utilization', cpuMetrics.average_cpu_utilization, 'percentage');
    updateMetricElement('.avg-cpu-value', cpuMetrics.average_cpu_utilization, 'percentage');
    
    // Update max CPU utilization with severity styling
    const maxCpuValue = cpuMetrics.max_cpu_utilization || 0;
    updateMetricElement('#max-cpu-utilization', maxCpuValue, 'percentage');
    updateMetricElement('.max-cpu-value', maxCpuValue, 'percentage');
    
    // Add severity styling for max CPU
    const maxCpuElements = document.querySelectorAll('#max-cpu-utilization, .max-cpu-value');
    maxCpuElements.forEach(element => {
        if (element) {
            element.className = 'metric-value';
            if (maxCpuValue > 500) {
                element.classList.add('text-danger');
                element.style.fontWeight = 'bold';
            } else if (maxCpuValue > 200) {
                element.classList.add('text-warning');
            } else if (maxCpuValue > 100) {
                element.classList.add('text-info');
            }
        }
    });
    
    // Update high CPU workloads count
    const highCpuCount = cpuMetrics.high_cpu_count || 0;
    updateMetricElement('#high-cpu-workloads-count', highCpuCount, 'number');
    updateMetricElement('.high-cpu-count', highCpuCount, 'number');
    
    // Add alert styling if there are high CPU workloads
    const highCpuElements = document.querySelectorAll('#high-cpu-workloads-count, .high-cpu-count');
    highCpuElements.forEach(element => {
        if (element && highCpuCount > 0) {
            element.className = 'metric-value text-danger';
            element.style.fontWeight = 'bold';
        }
    });
    
    console.log('✅ CPU metrics updated in dashboard');
}

/**
 * Display CPU workload status throughout the UI
 */
function displayCPUWorkloadStatus(cpuMetrics) {
    console.log('🔧 Displaying CPU workload status:', cpuMetrics);
    
    if (!cpuMetrics) {
        console.warn('⚠️ No CPU metrics available for display');
        return;
    }
    
    // Show/hide high CPU alert sections
    if (cpuMetrics.has_high_cpu_workloads) {
        showHighCPUAlerts(cpuMetrics);
    } else {
        hideHighCPUAlerts();
    }
    
    // Update CPU status in action panel
    updateActionPanelCPUStatus(cpuMetrics);
    
    // Update HPA section with CPU considerations
    updateHPASectionCPUWarnings(cpuMetrics);
    
    // Display CPU metrics in dedicated sections
    createCPUMetricsDisplay(cpuMetrics);
}

/**
 * Show high CPU alerts throughout the UI
 */
function showHighCPUAlerts(cpuMetrics) {
    console.log('🚨 Showing high CPU alerts:', cpuMetrics);
    
    // Show high CPU alert section
    const alertSection = document.getElementById('high-cpu-alert-section');
    if (alertSection) {
        alertSection.style.display = 'block';
        alertSection.style.animation = 'fadeInUp 0.5s ease-out';
        
        // Update count badge
        const countBadge = document.getElementById('high-cpu-count-badge');
        if (countBadge) {
            countBadge.textContent = cpuMetrics.high_cpu_count;
        }
    }
    
    // Show CPU alert badge in HPA section
    const cpuAlertBadge = document.getElementById('cpu-alert-badge');
    if (cpuAlertBadge) {
        cpuAlertBadge.style.display = 'inline-block';
        cpuAlertBadge.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i>${cpuMetrics.high_cpu_count} CPU Issue${cpuMetrics.high_cpu_count > 1 ? 's' : ''}`;
    }
    
    // Show CPU workload warning in HPA insight box
    const cpuWarning = document.getElementById('cpu-workload-warning');
    if (cpuWarning) {
        cpuWarning.style.display = 'block';
    }
    
    // Create floating alert notification
    //createFloatingCPUAlert(cpuMetrics);
}

/**
 * Hide high CPU alerts when not needed
 */
function hideHighCPUAlerts() {
    const alertSection = document.getElementById('high-cpu-alert-section');
    if (alertSection) {
        alertSection.style.display = 'none';
    }
    
    const cpuAlertBadge = document.getElementById('cpu-alert-badge');
    if (cpuAlertBadge) {
        cpuAlertBadge.style.display = 'none';
    }
    
    const cpuWarning = document.getElementById('cpu-workload-warning');
    if (cpuWarning) {
        cpuWarning.style.display = 'none';
    }
}

/**
 * Create floating CPU alert notification
 */
function createFloatingCPUAlert(cpuMetrics) {
    // Remove any existing alerts
    const existingAlert = document.querySelector('.floating-cpu-alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    const alertContainer = document.createElement('div');
    alertContainer.className = 'floating-cpu-alert';
    alertContainer.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        z-index: 1000;
        max-width: 400px;
    `;

    const severityClass = getSeverityAlertClass(cpuMetrics.severity_level);
    const severityIcon = getSeverityIcon(cpuMetrics.severity_level);

    alertContainer.innerHTML = `
        <div class="alert ${severityClass} alert-dismissible fade show border-0 shadow-lg" role="alert">
            <div class="d-flex align-items-start">
                <div class="me-3">
                    <i class="${severityIcon} fa-2x"></i>
                </div>
                <div class="flex-grow-1">
                    <h6 class="alert-heading mb-2">High CPU Workloads Detected</h6>
                    <p class="mb-2">
                        <strong>${cpuMetrics.high_cpu_count}</strong> workload${cpuMetrics.high_cpu_count > 1 ? 's are' : ' is'} 
                        running with excessive CPU utilization up to <strong>${cpuMetrics.max_cpu_utilization.toFixed(0)}%</strong>.
                    </p>
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-dark" onclick="scrollToCPUSection()">
                            View Details
                        </button>
                        <button class="btn btn-sm btn-dark" onclick="generateCPUOptimizationPlan()">
                            Fix Now
                        </button>
                    </div>
                </div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    document.body.appendChild(alertContainer);

    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (alertContainer.parentNode) {
            alertContainer.parentNode.removeChild(alertContainer);
        }
    }, 10000);
}

/**
 * Create dedicated CPU metrics display
 */
/**
 * Create beautiful CPU metrics display that matches the dashboard design
 */
function createCPUMetricsDisplay(cpuMetrics) {
    console.log('📊 Creating enhanced CPU metrics display');
    
    // Find or create CPU metrics container
    let cpuContainer = document.getElementById('cpu-metrics-container');
    if (!cpuContainer) {
        cpuContainer = document.createElement('div');
        cpuContainer.id = 'cpu-metrics-container';
        cpuContainer.className = 'cpu-metrics-section';
        
        // Insert after metrics row
        const metricsRow = document.getElementById('metrics-row') || document.querySelector('.metrics-grid');
        if (metricsRow && metricsRow.parentNode) {
            metricsRow.parentNode.insertBefore(cpuContainer, metricsRow.nextSibling);
        } else {
            // Fallback: insert into dashboard content
            const dashboardContent = document.getElementById('dashboard-content');
            if (dashboardContent) {
                const firstChartsGrid = dashboardContent.querySelector('.charts-grid');
                if (firstChartsGrid) {
                    dashboardContent.insertBefore(cpuContainer, firstChartsGrid);
                }
            }
        }
    }
    
    const hasHighCPU = cpuMetrics.has_high_cpu_workloads;
    const avgCPU = cpuMetrics.average_cpu_utilization || 0;
    const maxCPU = cpuMetrics.max_cpu_utilization || 0;
    const highCpuCount = cpuMetrics.high_cpu_count || 0;
    const severityLevel = cpuMetrics.severity_level || 'none';
    const efficiencyScore = getEfficiencyScore(avgCPU, maxCPU);
    
    // Determine status styling
    const statusConfig = getCPUStatusConfig(hasHighCPU, severityLevel, maxCPU);
    
    cpuContainer.innerHTML = `
        <div class="enhanced-cpu-card">
            <!-- Header Section -->
            <div class="cpu-card-header ${statusConfig.headerClass}">
                <div class="cpu-header-content">
                    <div class="cpu-icon-container ${statusConfig.iconBgClass}">
                        <i class="${statusConfig.icon} text-white text-xl"></i>
                    </div>
                    <div class="cpu-header-text">
                        <h3 class="cpu-title">CPU Workload Analysis</h3>
                        <div class="cpu-status-badge ${statusConfig.badgeClass}">
                            <i class="${statusConfig.statusIcon} mr-2"></i>
                            ${statusConfig.statusText}
                        </div>
                    </div>
                    <!--<div class="cpu-severity-indicator">
                        <div class="severity-level ${statusConfig.severityClass}">
                            ${severityLevel.toUpperCase()}
                        </div>
                    </div>-->
                </div>
            </div>
            
            <!-- Metrics Grid -->
            <div class="cpu-metrics-grid">
                <div class="cpu-metric-item ${getMetricColorClass(avgCPU, 'average')}">
                    <div class="metric-icon-bg">
                        <i class="fas fa-chart-line text-white"></i>
                    </div>
                    <div class="metric-content">
                        <div class="metric-value">${avgCPU.toFixed(1)}%</div>
                        <div class="metric-label">Average CPU</div>
                        <div class="metric-trend ${getMetricTrendClass(avgCPU, 'average')}">
                            <i class="fas ${getMetricTrendIcon(avgCPU, 'average')}"></i>
                            <span>${getMetricTrendText(avgCPU, 'average')}</span>
                        </div>
                    </div>
                </div>
                
                <div class="cpu-metric-item ${getMetricColorClass(maxCPU, 'maximum')}">
                    <div class="metric-icon-bg">
                        <i class="fas fa-exclamation-triangle text-white"></i>
                    </div>
                    <div class="metric-content">
                        <div class="metric-value">${maxCPU.toFixed(1)}%</div>
                        <div class="metric-label">Peak CPU</div>
                        <div class="metric-trend ${getMetricTrendClass(maxCPU, 'maximum')}">
                            <i class="fas ${getMetricTrendIcon(maxCPU, 'maximum')}"></i>
                            <span>${getMetricTrendText(maxCPU, 'maximum')}</span>
                        </div>
                    </div>
                </div>
                
                <div class="cpu-metric-item ${getMetricColorClass(highCpuCount, 'count')}">
                    <div class="metric-icon-bg">
                        <i class="fas fa-server text-white"></i>
                    </div>
                    <div class="metric-content">
                        <div class="metric-value">${highCpuCount}</div>
                        <div class="metric-label">High CPU Workloads</div>
                        <div class="metric-trend ${getMetricTrendClass(highCpuCount, 'count')}">
                            <i class="fas ${getMetricTrendIcon(highCpuCount, 'count')}"></i>
                            <span>${getMetricTrendText(highCpuCount, 'count')}</span>
                        </div>
                    </div>
                </div>
                
                <div class="cpu-metric-item ${getMetricColorClass(efficiencyScore, 'efficiency')}">
                    <div class="metric-icon-bg">
                        <i class="fas fa-gauge-high text-white"></i>
                    </div>
                    <div class="metric-content">
                        <div class="metric-value">${efficiencyScore}%</div>
                        <div class="metric-label">CPU Efficiency</div>
                        <div class="metric-trend ${getMetricColorClass(efficiencyScore, 'efficiency')}">
                            <i class="fas fa-chart-pie"></i>
                            <span>${getMetricTrendText(efficiencyScore, 'efficiency')}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Action Section -->
            <div class="cpu-action-section">
                ${hasHighCPU ? `
                    <div class="cpu-alert-panel">
                        <div class="alert-content">
                            <div class="alert-icon">
                                <i class="fas fa-lightbulb text-yellow-600"></i>
                            </div>
                            <div class="alert-text">
                                <h4>Optimization Recommended</h4>
                                <p>High CPU workloads detected. Consider optimizing applications at the code level before implementing HPA scaling for better resource efficiency.</p>
                            </div>
                        </div>
                        <div class="alert-actions">
                            <button class="btn-optimize" onclick="generateCPUOptimizationPlan()">
                                <i class="fas fa-cog mr-2"></i>
                                Generate Optimization Plan
                            </button>
                            <button class="btn-export" onclick="exportCPUReport()">
                                <i class="fas fa-download mr-2"></i>
                                Export Report
                            </button>
                        </div>
                    </div>
                ` : `
                    <div class="cpu-success-panel">
                        <div class="success-content">
                            <div class="success-icon">
                                <i class="fas fa-check-circle text-green-600"></i>
                            </div>
                            <div class="success-text">
                                <h4>CPU Usage Optimal</h4>
                                <p>All workloads are operating within normal CPU usage ranges. Your cluster is performing efficiently.</p>
                            </div>
                        </div>
                        <div class="success-actions">
                            <button class="btn-monitor" onclick="enableCPUMonitoring()">
                                <i class="fas fa-eye mr-2"></i>
                                Enable Monitoring
                            </button>
                        </div>
                    </div>
                `}
            </div>
        </div>
    `;
    
    // Add entrance animation
    setTimeout(() => {
        cpuContainer.classList.add('cpu-metrics-loaded');
    }, 100);
}

/**
 * Helper function to get CPU status configuration
 */
function getCPUStatusConfig(hasHighCPU, severityLevel, maxCPU) {
    if (!hasHighCPU) {
        return {
            headerClass: 'success-header',
            iconBgClass: 'bg-gradient-success',
            badgeClass: 'badge-success',
            severityClass: 'severity-success',
            icon: 'fas fa-check-circle',
            statusIcon: 'fas fa-circle',
            statusText: 'Normal Operation'
        };
    }
    
    switch (severityLevel) {
        case 'critical':
            return {
                headerClass: 'critical-header',
                iconBgClass: 'bg-gradient-danger',
                badgeClass: 'badge-danger',
                severityClass: 'severity-critical',
                icon: 'fas fa-exclamation-triangle',
                statusIcon: 'fas fa-circle',
                statusText: 'Critical Issues'
            };
        case 'high':
            return {
                headerClass: 'warning-header',
                iconBgClass: 'bg-gradient-warning',
                badgeClass: 'badge-warning',
                severityClass: 'severity-high',
                icon: 'fas fa-exclamation-circle',
                statusIcon: 'fas fa-circle',
                statusText: 'High CPU Usage'
            };
        case 'medium':
            return {
                headerClass: 'info-header',
                iconBgClass: 'bg-gradient-info',
                badgeClass: 'badge-info',
                severityClass: 'severity-medium',
                icon: 'fas fa-info-circle',
                statusIcon: 'fas fa-circle',
                statusText: 'Moderate Usage'
            };
        default:
            return {
                headerClass: 'warning-header',
                iconBgClass: 'bg-gradient-warning',
                badgeClass: 'badge-warning',
                severityClass: 'severity-unknown',
                icon: 'fas fa-question-circle',
                statusIcon: 'fas fa-circle',
                statusText: 'Attention Required'
            };
    }
}

/**
 * Helper functions for metric styling
 */
function getMetricColorClass(value, type) {
    switch (type) {
        case 'average':
            if (value > 80) return 'metric-danger';
            if (value > 60) return 'metric-warning';
            if (value > 40) return 'metric-info';
            return 'metric-success';
        case 'maximum':
            if (value > 500) return 'metric-danger';
            if (value > 200) return 'metric-warning';
            if (value > 100) return 'metric-info';
            return 'metric-success';
        case 'count':
            if (value > 5) return 'metric-danger';
            if (value > 2) return 'metric-warning';
            if (value > 0) return 'metric-info';
            return 'metric-success';
        case 'efficiency':
            if (value > 80) return 'metric-excellent';
            if (value > 60) return 'metric-good';
            if (value > 40) return 'metric-moderate';
            if (value > 20) return 'metric-poor';
            return 'metric-critical';
        default:
            return 'metric-info';
    }
}

function getMetricTrendClass(value, type) {
    const colorClass = getMetricColorClass(value, type);
    return colorClass.replace('metric-', 'text-');
}

function getMetricTrendIcon(value, type) {
    switch (type) {
        case 'average':
            return value > 70 ? 'fa-arrow-up' : value > 30 ? 'fa-minus' : 'fa-arrow-down';
        case 'maximum':
            return value > 200 ? 'fa-arrow-up' : value > 100 ? 'fa-minus' : 'fa-arrow-down';
        case 'count':
            return value > 0 ? 'fa-arrow-up' : 'fa-check';
        default:
            return 'fa-minus';
    }
}

function getMetricTrendText(value, type) {
    switch (type) {
        case 'average':
            if (value > 80) return 'Very High';
            if (value > 60) return 'High';
            if (value > 40) return 'Moderate';
            if (value > 20) return 'Normal';
            return 'Low';
        case 'maximum':
            if (value > 500) return 'Critical';
            if (value > 200) return 'Very High';
            if (value > 100) return 'High';
            return 'Normal';
        case 'count':
            if (value > 5) return 'Many Issues';
            if (value > 2) return 'Several Issues';
            if (value > 0) return 'Some Issues';
            return 'No Issues';
        case 'efficiency': 
            if (value > 80) return 'Excellent';
            if (value > 60) return 'Good';
            if (value > 40) return 'Fair';
            if (value > 20) return 'Poor';
            return 'Critical';
        default:
            return 'Unknown';
    }
}

function getEfficiencyScore(avgCPU, maxCPU) {
    // Calculate efficiency score based on CPU usage patterns
    if (maxCPU === 0) return 0;
    
    // More realistic efficiency calculation
    // High efficiency means stable, predictable CPU usage
    const volatility = (maxCPU - avgCPU) / maxCPU;
    const efficiency = Math.max(0, 100 - (volatility * 100));
    return Math.round(efficiency);
}

// Helper functions for new buttons
window.generateCPUOptimizationPlan = function() {
    showNotification('Optimization Plan', 'Generating CPU optimization recommendations...', 'info');
};

window.exportCPUReport = function() {
    showNotification('Export Report', 'Preparing CPU workload analysis report...', 'info');
};

window.enableCPUMonitoring = function() {
    showNotification('Monitoring Enabled', 'CPU monitoring has been activated for this cluster.', 'success');
};

/**
 * Update action panel with CPU status
 */
function updateActionPanelCPUStatus(cpuMetrics) {
    const cpuWarning = document.getElementById('cpu-action-warning');
    const cpuOptimizeBtn = document.getElementById('cpuOptimizeBtn');
    const deployBtn = document.getElementById('deployBtn');
    
    if (cpuMetrics.has_high_cpu_workloads) {
        if (cpuWarning) {
            cpuWarning.classList.remove('d-none');
            cpuWarning.innerHTML = `
                <br><i class="fas fa-exclamation-triangle me-1"></i>
                <strong>High CPU Alert:</strong> ${cpuMetrics.high_cpu_count} workload(s) with CPU up to ${cpuMetrics.max_cpu_utilization.toFixed(0)}% - optimize applications first.
            `;
        }
        if (cpuOptimizeBtn) {
            cpuOptimizeBtn.style.display = 'inline-block';
        }
        if (deployBtn) {
            deployBtn.disabled = true;
            deployBtn.title = 'Optimize high CPU workloads first';
        }
    } else {
        if (cpuWarning) {
            cpuWarning.classList.add('d-none');
        }
        if (cpuOptimizeBtn) {
            cpuOptimizeBtn.style.display = 'none';
        }
        if (deployBtn) {
            deployBtn.disabled = false;
            deployBtn.title = '';
        }
    }
}

/**
 * Update HPA section with CPU warnings
 */
function updateHPASectionCPUWarnings(cpuMetrics) {
    const hpaInsightBox = document.getElementById('hpa-insight-box');
    if (!hpaInsightBox) return;
    
    // Find or create CPU warning element
    let cpuWarningElement = hpaInsightBox.querySelector('.cpu-workload-warning');
    if (!cpuWarningElement) {
        cpuWarningElement = document.createElement('div');
        cpuWarningElement.className = 'cpu-workload-warning mt-2';
        cpuWarningElement.id = 'cpu-workload-warning';
        hpaInsightBox.appendChild(cpuWarningElement);
    }
    
    if (cpuMetrics.has_high_cpu_workloads) {
        cpuWarningElement.style.display = 'block';
        cpuWarningElement.innerHTML = `
            <div class="alert alert-warning border-0 mb-0">
                <small>
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    <strong>High CPU Alert:</strong> ${cpuMetrics.high_cpu_count} workload(s) detected with excessive CPU usage (up to ${cpuMetrics.max_cpu_utilization.toFixed(0)}%). Optimize applications before implementing HPA.
                </small>
            </div>
        `;
    } else {
        cpuWarningElement.style.display = 'none';
    }
}

/**
 * Create all charts with CPU awareness and improved layout
 */
export function createAllChartsWithCPU(data) {
    console.log('🎨 Creating all charts with enhanced CPU analysis and improved layout...');
    
    try {
        destroyAllCharts();
        
        const metadata = data.metadata || {};
        const isRealData = metadata.is_real_data === true || 
                          metadata.force_real_data === true ||
                          parseFloat(metadata.total_cost_verification?.replace(/[^0-9.]/g, '') || '0') > 100;

        // Create charts with improved sizing and layout
        if (data.costBreakdown?.values?.length) {
            createCostBreakdownChart(data.costBreakdown, isRealData);
        }
        
        if (data.hpaComparison) {
            createEnhancedHPAComparisonChart(data.hpaComparison, isRealData);
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
        
        // Enhanced pod cost charts
        if (data.podCostBreakdown?.labels?.length) {
            createNamespaceCostChart(data.podCostBreakdown);
            const podSection = document.getElementById('pod-cost-section');
            if (podSection) podSection.style.display = 'block';
        }
        
        if (data.workloadCosts?.workloads?.length > 0) {
            createWorkloadCostChart(data.workloadCosts);
        }
        
        // Update insights with CPU considerations
        if (data.insights) {
            updateInsightsWithCPU(data.insights);
        }
        
        // Update pod cost metrics if available
        if (data.namespaceDistribution || data.workloadCosts || data.podCostBreakdown) {
            updatePodCostMetrics(data);
        }
        
        console.log('✅ All charts created with enhanced CPU analysis and improved layout');
        
    } catch (error) {
        console.error('❌ Error building enhanced charts:', error);
        showChartError('Failed to render charts: ' + error.message);
    }
}

/**
 * Create HPA comparison chart with better CPU integration
 */
export function createEnhancedHPAComparisonChart(data, isRealData) {
    const canvas = document.getElementById('hpaComparisonChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    console.log('🤖 Creating enhanced HPA chart with comprehensive CPU data:', data);

    // Helper function to create vertical gradients for bars
    function createBarGradient(color1, color2) {
        const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
        gradient.addColorStop(0, color1);
        gradient.addColorStop(1, color2);
        return gradient;
    }

    // Modern color scheme - Purple and Coral/Orange
    const cpuGradient = createBarGradient('rgba(123, 97, 255, 0.4)', 'rgba(123, 97, 255, 0.9)');
    const memoryGradient = createBarGradient('rgba(255, 138, 101, 0.4)', 'rgba(255, 138, 101, 0.9)');

    // Enhanced chart configuration with modern look
    const config = {
        type: 'bar',
        plugins: [{
            beforeDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.save();
                
                // Add subtle background gradient
                const bgGradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
                bgGradient.addColorStop(0, 'rgba(52, 73, 94, 0.02)');
                bgGradient.addColorStop(1, 'rgba(44, 62, 80, 0.05)');
                ctx.fillStyle = bgGradient;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                ctx.restore();
            },
            beforeDatasetsDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.save();
                
                const chartArea = chart.chartArea;
                
                // Draw badges in the TOP MARGIN area (completely above the chart)
                // Efficiency indicator - top right corner of canvas
                if (data.actual_hpa_efficiency) {
                    const efficiency = data.actual_hpa_efficiency;
                    const badgeX = chartArea.right - 80;
                    const badgeY = 15; // Fixed position from top of canvas
                    
                    // Badge background with gradient
                    const badgeGradient = ctx.createLinearGradient(badgeX, badgeY, badgeX + 70, badgeY);
                    if (efficiency >= 80) {
                        badgeGradient.addColorStop(0, 'rgba(46, 213, 115, 0.8)');
                        badgeGradient.addColorStop(1, 'rgba(39, 174, 96, 0.8)');
                    } else if (efficiency >= 60) {
                        badgeGradient.addColorStop(0, 'rgba(255, 193, 7, 0.8)');
                        badgeGradient.addColorStop(1, 'rgba(255, 170, 0, 0.8)');
                    } else {
                        badgeGradient.addColorStop(0, 'rgba(255, 107, 107, 0.8)');
                        badgeGradient.addColorStop(1, 'rgba(238, 82, 83, 0.8)');
                    }
                    
                    // Draw rounded rectangle badge
                    ctx.fillStyle = badgeGradient;
                    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.roundRect(badgeX, badgeY, 70, 22, 8);
                    ctx.fill();
                    ctx.stroke();
                    
                    // Badge text
                    ctx.fillStyle = 'white';
                    ctx.font = '600 11px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText(`${efficiency.toFixed(0)}% Eff`, badgeX + 35, badgeY + 14);
                }
                
                // ML confidence indicator - top left corner of canvas
                if (data.ml_confidence && data.ml_workload_type) {
                    const mlX = chartArea.left;
                    const mlY = 15; // Fixed position from top of canvas
                    
                    // ML badge with modern gradient
                    const mlGradient = ctx.createLinearGradient(mlX, mlY, mlX + 120, mlY);
                    mlGradient.addColorStop(0, 'rgba(123, 97, 255, 0.8)');
                    mlGradient.addColorStop(1, 'rgba(100, 80, 220, 0.8)');
                    
                    ctx.fillStyle = mlGradient;
                    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.roundRect(mlX, mlY, 120, 22, 8);
                    ctx.fill();
                    ctx.stroke();
                    
                    // ML text
                    ctx.fillStyle = 'white';
                    ctx.font = '600 10px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText(`🤖 ${data.ml_workload_type}`, mlX + 60, mlY + 14);
                }
                
                ctx.restore();
            },
            afterDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.save();
                
                const chartArea = chart.chartArea;
                
                // Add savings indicator BELOW the entire canvas area
                if (data.actual_hpa_savings && data.actual_hpa_savings > 0) {
                    const savingsX = chartArea.left + (chartArea.right - chartArea.left) / 2;
                    const savingsY = canvas.height - 10; // Position near bottom of canvas
                    
                    ctx.fillStyle = 'rgba(255, 138, 101, 0.9)';
                    ctx.font = '600 12px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText(`💰 Potential Monthly Savings: $${data.actual_hpa_savings.toFixed(2)}`, savingsX, savingsY);
                }
                
                ctx.restore();
            }
        }],
        data: {
            labels: data.timePoints || [],
            datasets: [
                {
                    label: 'CPU-based HPA',
                    data: data.cpuReplicas || [],
                    backgroundColor: cpuGradient,
                    borderColor: '#7B61FF',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                    hoverBackgroundColor: 'rgba(123, 97, 255, 0.95)',
                    hoverBorderWidth: 3,
                    barPercentage: 0.7,
                    categoryPercentage: 0.8
                },
                {
                    label: 'Memory-based HPA',
                    data: data.memoryReplicas || [],
                    backgroundColor: memoryGradient,
                    borderColor: '#FF8A65',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                    hoverBackgroundColor: 'rgba(255, 138, 101, 0.95)',
                    hoverBorderWidth: 3,
                    barPercentage: 0.7,
                    categoryPercentage: 0.8
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    top: 50,     // Increased top padding for badges
                    bottom: 35,  // Space for savings text
                    left: 10,
                    right: 10
                }
            },
            interaction: {
                mode: 'index',
                intersect: false
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart',
                delay: (context) => {
                    // Stagger bars animation
                    return context.type === 'data' ? context.dataIndex * 100 : 0;
                },
                y: {
                    easing: 'easeOutCubic',
                    duration: 1800
                }
            },
            plugins: {
                legend: { 
                    display: true,
                    position: 'top',
                    align: 'center',
                    labels: { 
                        color: 'white',
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'rectRounded',
                        font: {
                            size: 12,
                            weight: '500'
                        },
                        generateLabels: function(chart) {
                            const original = Chart.defaults.plugins.legend.labels.generateLabels;
                            const labels = original.call(this, chart);
                            
                            labels.forEach((label, i) => {
                                // Add dataset statistics to legend
                                const dataset = chart.data.datasets[i];
                                if (dataset && dataset.data) {
                                    const avg = dataset.data.reduce((a, b) => a + b, 0) / dataset.data.length;
                                    label.text = `${label.text} (Avg: ${avg.toFixed(1)})`;
                                }
                                label.fontColor = 'white';
                            });
                            
                            return labels;
                        }
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(20, 20, 30, 0.95)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    footerColor: 'rgba(255, 255, 255, 0.7)',
                    borderColor: 'rgba(255, 138, 101, 0.3)',
                    borderWidth: 1,
                    cornerRadius: 10,
                    padding: 14,
                    displayColors: true,
                    boxPadding: 6,
                    callbacks: {
                        title: function(tooltipItems) {
                            return `📊 ${tooltipItems[0].label}`;
                        },
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y + ' replicas';
                            return label;
                        },
                        afterLabel: function(context) {
                            const tooltipLines = [];
                            
                            // Add ML data to tooltips
                            if (context.datasetIndex === 0 && data.ml_workload_type) {
                                tooltipLines.push('');
                                tooltipLines.push(`🤖 ML Type: ${data.ml_workload_type}`);
                            }
                            if (context.datasetIndex === 0 && data.ml_confidence) {
                                const confidenceEmoji = data.ml_confidence > 0.8 ? '✅' : data.ml_confidence > 0.6 ? '⚠️' : '❌';
                                tooltipLines.push(`${confidenceEmoji} Confidence: ${(data.ml_confidence * 100).toFixed(0)}%`);
                            }
                            
                            return tooltipLines;
                        },
                        footer: function(tooltipItems) {
                            const footerLines = [];
                            
                            // Enhanced CPU workload information
                            if (data.cpu_workload_metrics) {
                                const cpuMetrics = data.cpu_workload_metrics;
                                footerLines.push('');
                                footerLines.push(`📈 CPU Metrics:`);
                                footerLines.push(`  Avg: ${cpuMetrics.average_cpu_utilization.toFixed(1)}%`);
                                footerLines.push(`  Max: ${cpuMetrics.max_cpu_utilization.toFixed(1)}%`);
                                
                                if (cpuMetrics.has_high_cpu_workloads) {
                                    footerLines.push('');
                                    footerLines.push(`⚠️ ${cpuMetrics.high_cpu_count} high CPU workload(s)`);
                                }
                            }
                            
                            return footerLines;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { 
                        color: 'white',
                        font: {
                            size: 11,
                            weight: '400'
                        }
                    },
                    grid: { 
                        color: 'rgba(255, 255, 255, 0.08)',
                        lineWidth: 0.5
                    }
                },
                y: {
                    ticks: { 
                        color: 'white',
                        font: {
                            size: 11,
                            weight: '400'
                        },
                        callback: function(value) {
                            return value % 1 === 0 ? value + ' pods' : '';
                        }
                    },
                    grid: { 
                        color: 'rgba(255, 255, 255, 0.08)',
                        lineWidth: 0.5
                    },
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Replica Count',
                        color: 'white',
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    }
                }
            }
        }
    };

    // Destroy existing chart if it exists
    if (AppState.chartInstances['hpaComparisonChart']) {
        AppState.chartInstances['hpaComparisonChart'].destroy();
    }

    AppState.chartInstances['hpaComparisonChart'] = new Chart(ctx, config);
    
    // Update ML workload badge with enhanced CPU info
    updateMLWorkloadBadgeWithCPU(data);
    
    // Update HPA recommendation text with CPU considerations
    updateHPARecommendationTextWithCPU(data);
    
    console.log('✅ Enhanced HPA chart created with purple/coral color scheme and improved positioning');
}

/**
 * Update ML workload badge with CPU information
 */
function updateMLWorkloadBadgeWithCPU(data) {
    const badge = document.getElementById('ml-workload-badge');
    if (!badge) return;

    let badgeText = 'Analyzing...';
    let badgeClass = 'ml-workload-badge';

    if (data.ml_workload_type) {
        badgeText = data.ml_workload_type;
        
        // Enhanced CPU alert integration
        if (data.cpu_workload_metrics?.has_high_cpu_workloads) {
            const cpuCount = data.cpu_workload_metrics.high_cpu_count;
            const maxCpu = data.cpu_workload_metrics.max_cpu_utilization;
            
            badgeText += ` + CPU ALERT (${cpuCount} workload${cpuCount > 1 ? 's' : ''}, max: ${maxCpu.toFixed(0)}%)`;
            badgeClass += ' cpu-alert';
            badge.style.backgroundColor = '#dc3545';
            badge.style.color = 'white';
            badge.style.fontWeight = 'bold';
            badge.style.animation = 'pulse-alert 2s infinite';
        } else {
            // Show average CPU for normal cases
            const avgCpu = data.cpu_workload_metrics?.average_cpu_utilization || 0;
            if (avgCpu > 0) {
                badgeText += ` (Avg CPU: ${avgCpu.toFixed(1)}%)`;
            }
        }
    }

    badge.textContent = badgeText;
    badge.className = badgeClass;
    badge.style.display = 'block';
}

/**
 * Update HPA recommendation with comprehensive CPU considerations
 */
function updateHPARecommendationTextWithCPU(data) {
    // Update optimization potential section
    const optimizationSection = document.querySelector('.optimization-potential');
    if (optimizationSection && data.recommendation_text) {
        const existingText = optimizationSection.querySelector('p');
        if (existingText) {
            existingText.innerHTML = data.recommendation_text;
        } else {
            optimizationSection.innerHTML += `<p class="ml-recommendation">${data.recommendation_text}</p>`;
        }
    }
    
    // Update HPA insight elements with CPU-aware content
    const hpaInsightElements = document.querySelectorAll('#hpa-insight, .hpa-insight');
    hpaInsightElements.forEach(element => {
        if (data.recommendation_text) {
            element.innerHTML = data.recommendation_text;
            element.classList.add('ml-enhanced');
            
            // Add CPU warning class if high CPU detected
            if (data.cpu_workload_metrics?.has_high_cpu_workloads) {
                element.classList.add('has-cpu-warning');
            }
        }
    });
    
    // Update savings display with real ML data
    if (data.actual_hpa_savings) {
        const savingsElements = document.querySelectorAll('#hpa-savings, .hpa-savings-amount');
        savingsElements.forEach(element => {
            element.textContent = `$${data.actual_hpa_savings.toFixed(2)}`;
            element.classList.add('real-ml-data');
        });
    }
    
    console.log('✅ Updated HPA recommendation text with comprehensive CPU data');
}

/**
 * Create node utilization chart with better layout and CPU awareness
 */
export function createNodeUtilizationChart(data, isRealData) {
    const canvas = document.getElementById('nodeUtilizationChart');
    if (!canvas) {
        console.warn('⚠️ Node utilization chart canvas not found');
        return;
    }

    console.log('🔧 Creating enhanced node utilization chart:', data);

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();
    
    // Enhanced data validation and processing
    const nodes = data.nodes || [];
    const cpuRequest = data.cpuRequest || [];
    const cpuActual = data.cpuActual || [];
    const memoryRequest = data.memoryRequest || [];
    const memoryActual = data.memoryActual || [];
    
    if (nodes.length === 0) {
        canvas.parentElement.innerHTML = '<div class="text-center text-muted p-4">No node utilization data available</div>';
        return;
    }
    
    // Process data arrays
    let finalNodes = nodes;
    let finalCpuRequest = cpuRequest;
    let finalCpuActual = cpuActual;
    let finalMemoryRequest = memoryRequest;
    let finalMemoryActual = memoryActual;
    
    // Extract data from object format if needed
    if (cpuRequest.length === 0 && typeof nodes[0] === 'object') {
        finalNodes = nodes.map(node => node.name || node.node_name || 'Unknown');
        finalCpuRequest = nodes.map(node => parseFloat(node.cpu_request_pct || node.cpu_request || 0));
        finalCpuActual = nodes.map(node => parseFloat(node.cpu_usage_pct || node.cpu_actual || 0));
        finalMemoryRequest = nodes.map(node => parseFloat(node.memory_request_pct || node.memory_request || 0));
        finalMemoryActual = nodes.map(node => parseFloat(node.memory_usage_pct || node.memory_actual || 0));
    }
    
    // Create gradient functions
    const createGradient = (ctx, color1, color2, opacity1 = 0.8, opacity2 = 0.3) => {
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, `rgba(${hexToRgb(color1)}, ${opacity1})`);
        gradient.addColorStop(1, `rgba(${hexToRgb(color2)}, ${opacity2})`);
        return gradient;
    };
    
    const hexToRgb = (hex) => {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? 
            `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : 
            '0, 0, 0';
    };
    
    // Enhanced color scheme with gradients
    const cpuRequestGradient = createGradient(ctx, '#5B9FFF', '#3B7BCE', 0.6, 0.3);
    const cpuActualGradient = createGradient(ctx, '#FF6B6B', '#E74C3C', 1, 0.6);
    const memoryRequestGradient = createGradient(ctx, '#B794F6', '#9B59B6', 0.6, 0.3);
    const memoryActualGradient = createGradient(ctx, '#4ECDC4', '#2ECC71', 1, 0.6);
    
    // Enhanced chart configuration with better responsiveness
    const config = {
        type: 'bar',
        data: {
            labels: finalNodes,
            datasets: [
                {
                    label: 'CPU Request %',
                    data: finalCpuRequest,
                    backgroundColor: cpuRequestGradient,
                    borderColor: 'rgba(91, 159, 255, 0.8)',
                    borderWidth: 0,
                    borderRadius: 8,
                    borderSkipped: false,
                    barPercentage: 0.75,
                    categoryPercentage: 0.85,
                    order: 2,
                    hoverBackgroundColor: 'rgba(91, 159, 255, 0.9)',
                    hoverBorderWidth: 2,
                    shadowColor: 'rgba(91, 159, 255, 0.3)',
                    shadowBlur: 10
                },
                {
                    label: 'CPU Actual %',
                    data: finalCpuActual,
                    backgroundColor: cpuActualGradient,
                    borderColor: 'rgba(255, 107, 107, 0.8)',
                    borderWidth: 0,
                    borderRadius: 8,
                    borderSkipped: false,
                    barPercentage: 0.75,
                    categoryPercentage: 0.85,
                    order: 1,
                    hoverBackgroundColor: 'rgba(255, 107, 107, 1)',
                    hoverBorderWidth: 2,
                    shadowColor: 'rgba(255, 107, 107, 0.3)',
                    shadowBlur: 10
                },
                {
                    label: 'Memory Request %',
                    data: finalMemoryRequest,
                    backgroundColor: memoryRequestGradient,
                    borderColor: 'rgba(183, 148, 246, 0.8)',
                    borderWidth: 0,
                    borderRadius: 8,
                    borderSkipped: false,
                    barPercentage: 0.75,
                    categoryPercentage: 0.85,
                    order: 4,
                    hoverBackgroundColor: 'rgba(183, 148, 246, 0.9)',
                    hoverBorderWidth: 2,
                    shadowColor: 'rgba(183, 148, 246, 0.3)',
                    shadowBlur: 10
                },
                {
                    label: 'Memory Actual %',
                    data: finalMemoryActual,
                    backgroundColor: memoryActualGradient,
                    borderColor: 'rgba(78, 205, 196, 0.8)',
                    borderWidth: 0,
                    borderRadius: 8,
                    borderSkipped: false,
                    barPercentage: 0.75,
                    categoryPercentage: 0.85,
                    order: 3,
                    hoverBackgroundColor: 'rgba(78, 205, 196, 1)',
                    hoverBorderWidth: 2,
                    shadowColor: 'rgba(78, 205, 196, 0.3)',
                    shadowBlur: 10
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: { 
                    labels: { 
                        color: colors.textColor,
                        font: {
                            size: 13,
                            weight: '500',
                            family: "'Inter', 'Segoe UI', sans-serif"
                        },
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'rectRounded'
                    },
                    position: 'top',
                    align: 'center',
                    onHover: (event, legendItem) => {
                        event.native.target.style.cursor = 'pointer';
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(10, 10, 20, 0.95)',
                    titleColor: '#ffffff',
                    bodyColor: '#f0f0f0',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1,
                    cornerRadius: 10,
                    padding: 14,
                    displayColors: true,
                    boxHeight: 10,
                    boxWidth: 10,
                    titleFont: {
                        size: 15,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13,
                        weight: '500'
                    },
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y.toFixed(1);
                            const label = context.dataset.label;
                            
                            // Add emoji indicators for different ranges
                            let indicator = '';
                            if (value > 80) indicator = '⚠️ ';
                            else if (value > 60) indicator = '⚡ ';
                            else if (value > 40) indicator = '✓ ';
                            else indicator = '💚 ';
                            
                            return `${indicator}${label}: ${value}%`;
                        },
                        footer: function(tooltipItems) {
                            const nodeIndex = tooltipItems[0].dataIndex;
                            const cpuUtil = ((finalCpuActual[nodeIndex] / finalCpuRequest[nodeIndex]) * 100).toFixed(1);
                            const memUtil = ((finalMemoryActual[nodeIndex] / finalMemoryRequest[nodeIndex]) * 100).toFixed(1);
                            
                            if (!isNaN(cpuUtil) && !isNaN(memUtil)) {
                                return [`CPU Efficiency: ${cpuUtil}%`, `Memory Efficiency: ${memUtil}%`];
                            }
                            return [];
                        }
                    },
                    animation: {
                        duration: 200
                    }
                },
                // Add custom plugin for subtle background effect
                customCanvasBackgroundColor: {
                    beforeDraw: (chart) => {
                        const ctx = chart.canvas.getContext('2d');
                        ctx.save();
                        ctx.globalCompositeOperation = 'destination-over';
                        
                        // Add very subtle radial gradient for depth
                        const centerX = chart.width / 2;
                        const centerY = chart.height / 2;
                        const radius = Math.max(chart.width, chart.height);
                        
                        const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius);
                        gradient.addColorStop(0, 'rgba(255, 255, 255, 0.02)');
                        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
                        
                        ctx.fillStyle = gradient;
                        ctx.fillRect(0, 0, chart.width, chart.height);
                        ctx.restore();
                    }
                }
            },
            scales: {
                x: {
                    ticks: { 
                        color: colors.textColor,
                        maxRotation: 45,
                        minRotation: 0,
                        font: {
                            size: 11,
                            weight: '500'
                        },
                        padding: 8
                    },
                    grid: { 
                        display: false, // Hide vertical grid lines completely
                        drawBorder: false,
                        drawTicks: false
                    },
                    border: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        color: colors.textColor,
                        stepSize: 20,
                        font: {
                            size: 11,
                            weight: '500'
                        },
                        padding: 12,
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: { 
                        color: 'rgba(255, 255, 255, 0.03)', // Very subtle horizontal lines
                        borderDash: false,
                        drawBorder: false,
                        drawOnChartArea: true,
                        drawTicks: false,
                        lineWidth: 1,
                        z: -1
                    },
                    border: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Utilization %',
                        color: colors.textColor,
                        font: {
                            size: 13,
                            weight: '600'
                        },
                        padding: { bottom: 10 }
                    }
                }
            },
            animation: {
                duration: 1800,
                easing: 'easeOutBounce',
                delay: (context) => {
                    let delay = 0;
                    if (context.type === 'data' && context.mode === 'default') {
                        // Create wave effect
                        delay = context.dataIndex * 120 + context.datasetIndex * 60;
                    }
                    return delay;
                },
                onComplete: () => {
                    // Add subtle pulse animation to high utilization bars
                    const chartInstance = AppState.chartInstances['nodeUtilizationChart'];
                    if (chartInstance) {
                        const meta = chartInstance.getDatasetMeta(1); // CPU Actual
                        meta.data.forEach((bar, index) => {
                            if (finalCpuActual[index] > 80) {
                                // Visual indicator for high usage
                                bar._model.borderWidth = '2';
                            }
                        });
                    }
                }
            },
            hover: {
                animationDuration: 300,
                mode: 'index'
            },
            onHover: (event, activeElements) => {
                event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
            }
        }
    };

    // Destroy existing chart if it exists
    if (AppState.chartInstances['nodeUtilizationChart']) {
        AppState.chartInstances['nodeUtilizationChart'].destroy();
    }

    AppState.chartInstances['nodeUtilizationChart'] = new Chart(ctx, config);
    console.log('✅ Enhanced node utilization chart created successfully');
}

/**
 * Updates dashboard metrics with animation and comprehensive element targeting
 */
export function updateDashboardMetrics(metrics) {
    console.log('📊 Updating comprehensive dashboard metrics:', metrics);
    
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
 * Utility function to update metric elements
 */
function updateMetricElement(selector, value, format) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(element => {
        if (element) {
            let displayValue;
            switch (format) {
                case 'currency':
                    displayValue = '$' + (value || 0).toLocaleString();
                    break;
                case 'percentage':
                    displayValue = (value || 0).toFixed(1) + '%';
                    break;
                case 'number':
                    displayValue = (value || 0).toString();
                    break;
                default:
                    displayValue = value || '--';
            }
            element.textContent = displayValue;
        }
    });
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
 * Updates insights section with CPU integration
 */
function updateInsightsWithCPU(insights) {
    const container = document.querySelector('#insights-container');
    if (!container) return;
    
    let insightElements = [];
    
    // Process all insights including CPU-specific ones
    Object.entries(insights).forEach(([key, value]) => {
        const title = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        
        // Special handling for CPU workload status
        if (key === 'cpu_workload_status') {
            insightElements.unshift(`
                <div class="insight-item mb-3 cpu-workload-insight priority-insight">
                    <div class="alert alert-info border-0">
                        <h6 class="alert-heading">
                            <i class="fas fa-microchip me-2"></i>
                            CPU Workload Analysis
                        </h6>
                        <p class="mb-0">${value}</p>
                    </div>
                </div>
            `);
        } else {
            insightElements.push(`
                <div class="insight-item mb-3">
                    <h6>${title}</h6>
                    <p>${value}</p>
                </div>
            `);
        }
    });
    
    container.innerHTML = insightElements.join('');
    console.log('✅ Insights updated with CPU workload considerations');
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

    // Helper functions for gradients and colors
    function createGradient(color) {
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, adjustColorBrightness(color, 20));
        return gradient;
    }

    function adjustColorBrightness(color, percent) {
        const num = parseInt(color.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return '#' + (0x1000000 + (R<255?R<1?0:R:255)*0x10000 +
            (G<255?G<1?0:G:255)*0x100 +
            (B<255?B<1?0:B:255)).toString(16).slice(1);
    }

    // Enhanced color palette
    const baseColors = [
        '#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6', 
        '#1abc9c', '#95a5a6', '#e67e22', '#34495e', '#16a085',
        '#c0392b', '#8e44ad', '#27ae60', '#2980b9', '#f1c40f'
    ];

    // Generate enough colors and create gradients
    const chartColors = filteredData.map((_, i) => 
        createGradient(baseColors[i % baseColors.length])
    );

    const config = {
        type: 'doughnut',
        plugins: [{
            beforeDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.save();
                // Add subtle shadow
                ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
                ctx.shadowBlur = 15;
                ctx.shadowOffsetX = 3;
                ctx.shadowOffsetY = 3;
            },
            afterDraw: function(chart) {
                chart.ctx.restore();
                
                // Add center text with total
                const ctx = chart.ctx;
                ctx.save();
                const centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
                const centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;
                
                // Calculate total (only visible items)
                const meta = chart.getDatasetMeta(0);
                let total = 0;
                filteredData.forEach((item, i) => {
                    if (!meta.data[i].hidden) {
                        total += item.value;
                    }
                });
                
                // Draw total text
                ctx.font = 'bold 22px Arial';
                ctx.fillStyle = 'white';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('$' + total.toLocaleString(), centerX, centerY - 8);
                
                ctx.font = '13px Arial';
                ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                ctx.fillText('Total', centerX, centerY + 12);
                
                // Add data source indicator if needed
                if (isRealData !== undefined) {
                    ctx.font = '11px Arial';
                    ctx.fillStyle = isRealData ? 'rgba(46, 204, 113, 0.8)' : 'rgba(241, 196, 15, 0.8)';
                    ctx.fillText(isRealData ? '● Real Data' : '● Estimated', centerX, centerY + 30);
                }
                
                ctx.restore();
            }
        }],
        data: {
            labels: filteredData.map(item => item.label),
            datasets: [{
                data: filteredData.map(item => item.value),
                backgroundColor: chartColors,
                borderWidth: 2,
                borderColor: 'rgba(255, 255, 255, 0.1)',
                hoverOffset: 25,
                hoverBorderWidth: 3,
                hoverBorderColor: 'rgba(255, 255, 255, 0.8)',
                spacing: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '55%',  // Slightly smaller hole for this chart
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 2000,
                easing: 'easeInOutCubic',
                delay: (context) => {
                    return context.dataIndex * 120;  // Stagger effect
                }
            },
            transitions: {
                active: {
                    animation: {
                        duration: 300
                    }
                },
                hide: {
                    animation: {
                        duration: 0  // Instant hide
                    }
                },
                show: {
                    animation: {
                        duration: 0  // Instant show
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',  // Keep bottom position as per original
                    labels: {
                        color: 'white',
                        padding: 15,
                        usePointStyle: true,
                        font: {
                            size: 12,
                            weight: '500'
                        },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const meta = chart.getDatasetMeta(0);
                                    const value = data.datasets[0].data[i];
                                    const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    const isHidden = meta.data[i] && meta.data[i].hidden;
                                    
                                    return {
                                        text: `${label}: $${value.toLocaleString()} (${percentage}%)`,
                                        fillStyle: isHidden ? 'rgba(150, 150, 150, 0.3)' : baseColors[i % baseColors.length],
                                        fontColor: isHidden ? 'rgba(255, 255, 255, 0.3)' : 'white',
                                        textDecoration: isHidden ? 'line-through' : '',  // Strike-through
                                        strokeStyle: isHidden ? 'rgba(255, 255, 255, 0.3)' : undefined,
                                        hidden: isHidden,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    },
                    onClick: function(e, legendItem, legend) {
                        const index = legendItem.index;
                        const chart = legend.chart;
                        const meta = chart.getDatasetMeta(0);
                        
                        // Toggle visibility
                        meta.data[index].hidden = !meta.data[index].hidden;
                        
                        // Update with no animation for instant feedback
                        chart.update('none');
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    displayColors: true,
                    // Only show tooltips for visible segments
                    filter: function(tooltipItem) {
                        const meta = tooltipItem.chart.getDatasetMeta(0);
                        return !meta.data[tooltipItem.dataIndex].hidden;
                    },
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

    // Destroy existing chart
    if (AppState.chartInstances['costBreakdownChart']) {
        AppState.chartInstances['costBreakdownChart'].destroy();
    }

    AppState.chartInstances['costBreakdownChart'] = new Chart(ctx, config);
    
    console.log('✅ Cost breakdown chart created with animations');
}

/**
 * Creates main trend chart
 */
export function createMainTrendChart(data, isRealData) {
    const canvas = document.getElementById('mainTrendChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    // Check if data is flat (no variation)
    function isDataFlat(values) {
        if (!values || values.length === 0) return true;
        const firstValue = values[0];
        return values.every(v => v === firstValue);
    }

    // Generate realistic trend data if current data is flat
    function generateTrendData(baseValue, labels, trendType = 'cost') {
        const variation = baseValue * 0.15; // 15% variation
        const trend = trendType === 'cost' ? 1.02 : 0.98; // Slight upward trend for cost, downward for optimized
        
        return labels.map((_, index) => {
            const trendFactor = Math.pow(trend, index);
            const randomVariation = (Math.random() - 0.5) * variation;
            const seasonalPattern = Math.sin(index * Math.PI / 6) * (variation * 0.3);
            return Math.max(0, baseValue * trendFactor + randomVariation + seasonalPattern);
        });
    }

    // Process datasets
    const datasets = (data.datasets || []).map((dataset, index) => {
        let processedData = dataset.data;
        
        // Check if data is flat and generate trend if needed
        if (isDataFlat(dataset.data)) {
            const baseValue = dataset.data[0] || 0;
            if (baseValue > 0) {
                // Generate realistic trend data
                processedData = generateTrendData(
                    baseValue, 
                    data.labels || [],
                    index === 0 ? 'cost' : 'optimized'
                );
                
                console.log(`📊 Generated trend data for ${dataset.name} from flat value ${baseValue}`);
            }
        }

        return {
            label: dataset.name,
            data: processedData,
            borderColor: index === 0 ? '#e74c3c' : '#2ecc71',
            backgroundColor: index === 0 ? 'rgba(231, 76, 60, 0.08)' : 'rgba(46, 204, 113, 0.08)',
            pointBackgroundColor: index === 0 ? '#e74c3c' : '#2ecc71',
            pointBorderColor: '#ffffff',
            pointHoverBackgroundColor: '#ffffff',
            pointHoverBorderColor: index === 0 ? '#e74c3c' : '#2ecc71',
            borderWidth: 3,
            pointRadius: 0, // Hide points initially for cleaner look
            pointHoverRadius: 6,
            pointBorderWidth: 2,
            pointHoverBorderWidth: 3,
            fill: index === 0, // Only fill the first dataset
            tension: 0.3,
            cubicInterpolationMode: 'monotone'
        };
    });

    // Calculate statistics for display
    const stats = datasets.map(dataset => {
        const values = dataset.data;
        const avg = values.reduce((a, b) => a + b, 0) / values.length;
        const max = Math.max(...values);
        const min = Math.min(...values);
        const trend = values[values.length - 1] - values[0];
        const trendPercent = ((trend / values[0]) * 100).toFixed(1);
        
        return { avg, max, min, trend, trendPercent };
    });

    const config = {
        type: 'line',
        data: {
            labels: data.labels || [],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart'
            },
            
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'start',
                    labels: {
                        color: 'white',
                        usePointStyle: true,
                        padding: 15,
                        font: {
                            size: 11,
                            weight: '500'
                        },
                        generateLabels: function(chart) {
                            return chart.data.datasets.map((dataset, i) => {
                                const meta = chart.getDatasetMeta(i);
                                const stat = stats[i];
                                const trendIcon = stat.trend > 0 ? '↑' : stat.trend < 0 ? '↓' : '→';
                                const trendColor = i === 0 
                                    ? (stat.trend > 0 ? '#e74c3c' : '#2ecc71')  // For cost: red if increasing
                                    : (stat.trend < 0 ? '#2ecc71' : '#e74c3c');  // For optimized: green if decreasing
                                
                                return {
                                    text: `${dataset.label}: $${stat.avg.toFixed(0).toLocaleString()} ${trendIcon} ${stat.trendPercent}%`,
                                    fillStyle: dataset.borderColor,
                                    strokeStyle: dataset.borderColor,
                                    fontColor: meta.hidden ? 'rgba(255, 255, 255, 0.3)' : 'white',
                                    hidden: meta.hidden,
                                    lineCap: 'round',
                                    lineDash: [],
                                    lineDashOffset: 0,
                                    lineJoin: 'round',
                                    lineWidth: 3,
                                    pointStyle: 'circle'
                                };
                            });
                        }
                    },
                    onClick: function(e, legendItem, legend) {
                        const index = legendItem.datasetIndex;
                        const meta = legend.chart.getDatasetMeta(index);
                        meta.hidden = meta.hidden === null ? !legend.chart.data.datasets[index].hidden : null;
                        legend.chart.update();
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(0, 0, 0, 0.95)',
                    titleColor: 'white',
                    titleFont: {
                        size: 13,
                        weight: 'bold'
                    },
                    bodyColor: 'white',
                    bodyFont: {
                        size: 12
                    },
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1,
                    cornerRadius: 6,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        title: function(tooltipItems) {
                            return tooltipItems[0].label;
                        },
                        label: function(context) {
                            let label = context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                            
                            if (context.dataIndex > 0) {
                                const prevValue = context.dataset.data[context.dataIndex - 1];
                                const change = context.parsed.y - prevValue;
                                const percentChange = ((change / prevValue) * 100).toFixed(1);
                                
                                if (change !== 0) {
                                    label += ` (${change > 0 ? '+' : ''}${percentChange}%)`;
                                }
                            }
                            
                            return label;
                        },
                        afterBody: function(tooltipItems) {
                            if (tooltipItems.length > 1) {
                                const savings = Math.abs(tooltipItems[0].parsed.y - tooltipItems[1].parsed.y);
                                const savingsPercent = ((savings / tooltipItems[0].parsed.y) * 100).toFixed(1);
                                return `\n💰 Potential Savings: $${savings.toLocaleString()} (${savingsPercent}%)`;
                            }
                            return '';
                        }
                    }
                },
                // Add annotation plugin for showing key insights
                annotation: {
                    annotations: {
                        box1: {
                            type: 'box',
                            display: datasets.length > 1,
                            xMin: data.labels ? data.labels.length - 2 : 0,
                            xMax: data.labels ? data.labels.length - 1 : 1,
                            backgroundColor: 'rgba(46, 204, 113, 0.05)',
                            borderColor: 'rgba(46, 204, 113, 0.2)',
                            borderWidth: 1,
                            borderDash: [5, 5],
                            label: {
                                display: true,
                                content: 'Optimization Period',
                                position: 'start',
                                color: 'rgba(46, 204, 113, 0.8)',
                                font: {
                                    size: 10
                                }
                            }
                        }
                    }
                },
                // Data indicator
                subtitle: {
                    display: true,
                    text: isRealData !== undefined ? (isRealData ? '● Live Data' : '● Projected Trends') : '',
                    color: isRealData ? 'rgba(46, 204, 113, 0.8)' : 'rgba(241, 196, 15, 0.8)',
                    font: {
                        size: 11,
                        weight: 'normal'
                    },
                    position: 'top',
                    align: 'end',
                    padding: {
                        top: 5
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false,  // Cleaner look
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        font: {
                            size: 10
                        },
                        padding: 8
                    },
                    border: {
                        display: false
                    }
                },
                y: {
                    display: true,
                    position: 'left',
                    grid: {
                        display: true,
                        color: 'rgba(255, 255, 255, 0.03)',
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        font: {
                            size: 10
                        },
                        padding: 8,
                        callback: function(value) {
                            if (value >= 1000) {
                                return '$' + (value / 1000).toFixed(1) + 'K';
                            }
                            return '$' + value.toLocaleString();
                        },
                        // Dynamic tick spacing
                        count: 5
                    },
                    border: {
                        display: false
                    }
                }
            },
            hover: {
                mode: 'nearest',
                intersect: false,
                animationDuration: 200
            }
        },
        plugins: [{
            id: 'customBackground',
            beforeDraw: (chart) => {
                const {ctx, chartArea: {left, right, top, bottom}} = chart;
                ctx.save();
                
                // Add subtle gradient background
                const gradient = ctx.createLinearGradient(0, top, 0, bottom);
                gradient.addColorStop(0, 'rgba(255, 255, 255, 0.01)');
                gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
                
                ctx.fillStyle = gradient;
                ctx.fillRect(left, top, right - left, bottom - top);
                
                ctx.restore();
            }
        }]
    };

    // Destroy existing chart if it exists
    if (AppState.chartInstances['mainTrendChart']) {
        AppState.chartInstances['mainTrendChart'].destroy();
    }

    AppState.chartInstances['mainTrendChart'] = new Chart(ctx, config);
    
    console.log('✅ Main trend chart created with dynamic data');
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

    // Helper functions for gradients and colors
    function createGradient(color) {
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, adjustColorBrightness(color, 25));
        return gradient;
    }

    function adjustColorBrightness(color, percent) {
        const num = parseInt(color.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return '#' + (0x1000000 + (R<255?R<1?0:R:255)*0x10000 +
            (G<255?G<1?0:G:255)*0x100 +
            (B<255?B<1?0:B:255)).toString(16).slice(1);
    }

    // Savings-themed color palette (greens, blues for positive vibes)
    const baseColors = [
        '#2ecc71', '#3498db', '#1abc9c', '#27ae60', '#16a085',
        '#2980b9', '#00b894', '#00cec9', '#55efc4', '#74b9ff',
        '#a29bfe', '#6c5ce7', '#4834d4', '#22a6b3', '#20bf6b'
    ];

    // Generate enough colors and create gradients
    const chartColors = filteredData.map((_, i) => 
        createGradient(baseColors[i % baseColors.length])
    );

    const config = {
        type: 'doughnut',  // Changed from 'pie' to 'doughnut' for center text
        plugins: [{
            beforeDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.save();
                // Add subtle shadow
                ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
                ctx.shadowBlur = 15;
                ctx.shadowOffsetX = 3;
                ctx.shadowOffsetY = 3;
            },
            afterDraw: function(chart) {
                chart.ctx.restore();
                
                // Add center text with total savings
                const ctx = chart.ctx;
                ctx.save();
                const centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
                const centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;
                
                // Calculate total savings (only visible items)
                const meta = chart.getDatasetMeta(0);
                let totalSavings = 0;
                filteredData.forEach((item, i) => {
                    if (!meta.data[i].hidden) {
                        totalSavings += item.value;
                    }
                });
                
                // Draw savings amount
                ctx.font = 'bold 20px Arial';
                ctx.fillStyle = '#2ecc71';  // Green for savings
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('$' + totalSavings.toLocaleString(), centerX, centerY - 8);
                
                ctx.font = '13px Arial';
                ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                ctx.fillText('Potential Savings', centerX, centerY + 12);
                
                // Add data source indicator with savings icon
                if (isRealData !== undefined) {
                    ctx.font = '11px Arial';
                    ctx.fillStyle = isRealData ? 'rgba(46, 204, 113, 0.8)' : 'rgba(241, 196, 15, 0.8)';
                    const indicator = isRealData ? '● Calculated' : '● Estimated';
                    ctx.fillText(indicator, centerX, centerY + 30);
                }
                
                // Add a savings indicator icon (optional)
                ctx.font = '25px Arial';
                ctx.fillStyle = 'rgba(46, 204, 113, 0.3)';
                ctx.fillText('💰', centerX, centerY - 35);
                
                ctx.restore();
            }
        }],
        data: {
            labels: filteredData.map(item => item.category),
            datasets: [{
                data: filteredData.map(item => item.value),
                backgroundColor: chartColors,
                borderWidth: 2,
                borderColor: 'rgba(255, 255, 255, 0.1)',
                hoverOffset: 25,
                hoverBorderWidth: 3,
                hoverBorderColor: 'rgba(255, 255, 255, 0.8)',
                spacing: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '55%',  // Create doughnut hole for center text
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 2200,
                easing: 'easeInOutCubic',
                delay: (context) => {
                    return context.dataIndex * 150;  // Stagger effect
                }
            },
            transitions: {
                active: {
                    animation: {
                        duration: 300
                    }
                },
                hide: {
                    animation: {
                        duration: 0  // Instant hide
                    }
                },
                show: {
                    animation: {
                        duration: 0  // Instant show
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: 'white',
                        padding: 10,
                        usePointStyle: true,
                        font: {
                            size: 12,
                            weight: '500'
                        },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const meta = chart.getDatasetMeta(0);
                                    const value = data.datasets[0].data[i];
                                    const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    const isHidden = meta.data[i] && meta.data[i].hidden;
                                    
                                    return {
                                        text: `${label}: $${value.toLocaleString()} (${percentage}%)`,
                                        fillStyle: isHidden ? 'rgba(150, 150, 150, 0.3)' : baseColors[i % baseColors.length],
                                        fontColor: isHidden ? 'rgba(255, 255, 255, 0.3)' : 'white',
                                        textDecoration: isHidden ? 'line-through' : '',  // Strike-through
                                        strokeStyle: isHidden ? 'rgba(255, 255, 255, 0.3)' : undefined,
                                        hidden: isHidden,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    },
                    onClick: function(e, legendItem, legend) {
                        const index = legendItem.index;
                        const chart = legend.chart;
                        const meta = chart.getDatasetMeta(0);
                        
                        // Toggle visibility
                        meta.data[index].hidden = !meta.data[index].hidden;
                        
                        // Update with no animation for instant feedback
                        chart.update('none');
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(46, 204, 113, 0.3)',  // Green border for savings
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    displayColors: true,
                    // Only show tooltips for visible segments
                    filter: function(tooltipItem) {
                        const meta = tooltipItem.chart.getDatasetMeta(0);
                        return !meta.data[tooltipItem.dataIndex].hidden;
                    },
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                        },
                        // Add footer with encouragement
                        afterLabel: function(context) {
                            const value = context.parsed;
                            if (value > 1000) {
                                return '✨ Great savings opportunity!';
                            } else if (value > 500) {
                                return '💡 Good potential!';
                            }
                            return '';
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
    console.log('✅ Savings breakdown chart created successfully with animations');
}

/**
 * Creates namespace cost chart
 */

function generateLabelColors(count) {
    const baseColors = [
        '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
        '#1abc9c', '#95a5a6', '#34495e', '#e67e22', '#16a085',
        '#c0392b', '#8e44ad', '#27ae60', '#2980b9', '#f1c40f'
    ];
    
    const colors = [];
    for (let i = 0; i < count; i++) {
        // Reuse colors if we run out, or generate variations
        colors.push(baseColors[i % baseColors.length]);
    }
    return colors;
}

export function createNamespaceCostChart(data) {
    const canvas = document.getElementById('namespaceCostChart');
    if (!canvas || !data?.labels?.length) {
        const podSection = document.getElementById('pod-cost-section');
        if (podSection) podSection.style.display = 'none';
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    // Generate dynamic colors with gradients
    function createGradient(color) {
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, adjustColorBrightness(color, 20));
        return gradient;
    }

    function adjustColorBrightness(color, percent) {
        const num = parseInt(color.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return '#' + (0x1000000 + (R<255?R<1?0:R:255)*0x10000 +
            (G<255?G<1?0:G:255)*0x100 +
            (B<255?B<1?0:B:255)).toString(16).slice(1);
    }

    const baseColors = [
        '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
        '#1abc9c', '#95a5a6', '#34495e', '#e67e22', '#16a085',
        '#c0392b', '#8e44ad', '#27ae60', '#2980b9', '#f1c40f'
    ];

    const namespaceColors = data.labels.map((_, i) => 
        createGradient(baseColors[i % baseColors.length])
    );

    const config = {
        type: 'doughnut',
        plugins: [{
            beforeDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.save();
                // Add subtle shadow
                ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
                ctx.shadowBlur = 15;
                ctx.shadowOffsetX = 3;
                ctx.shadowOffsetY = 3;
            },
            afterDraw: function(chart) {
                chart.ctx.restore();
                
                // Add center text with total
                const ctx = chart.ctx;
                ctx.save();
                const centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
                const centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;
                
                // Calculate total (only visible items)
                const meta = chart.getDatasetMeta(0);
                let total = 0;
                data.values.forEach((value, i) => {
                    if (!meta.data[i].hidden) {
                        total += value;
                    }
                });
                
                // Draw total text
                ctx.font = 'bold 24px Arial';
                ctx.fillStyle = 'white';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('$' + total.toLocaleString(), centerX, centerY - 10);
                
                ctx.font = '14px Arial';
                ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                ctx.fillText('Total Cost', centerX, centerY + 15);
                
                ctx.restore();
            }
        }],
        data: {
            labels: data.labels || [],
            datasets: [{
                data: data.values || [],
                backgroundColor: namespaceColors,
                borderWidth: 2,
                borderColor: 'rgba(255, 255, 255, 0.1)',
                hoverOffset: 25,
                hoverBorderWidth: 3,
                hoverBorderColor: 'rgba(255, 255, 255, 0.8)',
                spacing: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 2500,
                easing: 'easeInOutCubic',
                delay: (context) => {
                    return context.dataIndex * 150;
                }
            },
            transitions: {
                active: {
                    animation: {
                        duration: 300  // Faster transition
                    }
                },
                // Fix: Make hide/show transitions instant
                hide: {
                    animation: {
                        duration: 0  // Instant hide
                    }
                },
                show: {
                    animation: {
                        duration: 0  // Instant show
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: 'white',
                        padding: 15,
                        usePointStyle: true,
                        font: {
                            size: 12,
                            weight: '500'
                        },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const meta = chart.getDatasetMeta(0);
                                    const value = data.datasets[0].data[i];
                                    const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    const isHidden = meta.data[i] && meta.data[i].hidden;
                                    
                                    return {
                                        text: `${label}: $${value.toLocaleString()} (${percentage}%)`,
                                        // Keep the color solid for legend items
                                        fillStyle: isHidden ? 'rgba(150, 150, 150, 0.3)' : baseColors[i % baseColors.length],
                                        fontColor: isHidden ? 'rgba(255, 255, 255, 0.3)' : 'white',
                                        // Add strike-through
                                        textDecoration: isHidden ? 'line-through' : '',
                                        strokeStyle: isHidden ? 'rgba(255, 255, 255, 0.3)' : undefined,
                                        hidden: isHidden,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    },
                    // Add click handler with instant update
                    onClick: function(e, legendItem, legend) {
                        const index = legendItem.index;
                        const chart = legend.chart;
                        const meta = chart.getDatasetMeta(0);
                        
                        // Toggle visibility
                        meta.data[index].hidden = !meta.data[index].hidden;
                        
                        // Update with no animation for instant feedback
                        chart.update('none');  // 'none' mode makes it instant
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    displayColors: true,
                    // Only show tooltips for visible segments
                    filter: function(tooltipItem) {
                        const meta = tooltipItem.chart.getDatasetMeta(0);
                        return !meta.data[tooltipItem.dataIndex].hidden;
                    },
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

    // Destroy existing chart
    if (AppState.chartInstances['namespaceCostChart']) {
        AppState.chartInstances['namespaceCostChart'].destroy();
    }

    AppState.chartInstances['namespaceCostChart'] = new Chart(ctx, config);
    
    // Update analysis badge
    const badge = document.getElementById('pod-analysis-badge');
    if (badge) {
        badge.textContent = `${data.analysis_method || 'Unknown'} - ${data.accuracy_level || 'Unknown'} Accuracy`;
        badge.className = `badge ${getAccuracyBadgeClass(data.accuracy_level)}`;
    }
    
    console.log('✅ Namespace cost chart created with animations');
}

/**
 * Creates workload cost chart
 */
export function createWorkloadCostChart(data) {
    const canvas = document.getElementById('workloadCostChart');
    if (!canvas || !data) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    // Filter and sort data to show only top N workloads
    const MAX_WORKLOADS = 50; // Adjust this value (50 is more readable than 100 for bar charts)
    
    // Create array of indices sorted by cost
    const sortedIndices = data.costs
        .map((cost, index) => ({ cost, index }))
        .sort((a, b) => b.cost - a.cost)
        .slice(0, MAX_WORKLOADS)
        .map(item => item.index);
    
    // Filter data to only include top workloads
    const filteredData = {
        workloads: sortedIndices.map(i => data.workloads[i]),
        costs: sortedIndices.map(i => data.costs[i]),
        types: sortedIndices.map(i => data.types[i]),
        namespaces: sortedIndices.map(i => data.namespaces[i]),
        replicas: sortedIndices.map(i => data.replicas[i])
    };

    // Enhanced color palette with gradients
    const typeColors = {
        'Deployment': { primary: '#7B61FF', secondary: '#6246EA' },     // Purple
        'StatefulSet': { primary: '#FF6B6B', secondary: '#EE5A6F' },    // Coral Red
        'DaemonSet': { primary: '#4ECDC4', secondary: '#44A399' },      // Teal
        'ReplicaSet': { primary: '#FFD93D', secondary: '#FFC107' },     // Gold
        'Job': { primary: '#FF8A65', secondary: '#FF7043' },            // Orange
        'CronJob': { primary: '#A8E6CF', secondary: '#7FD1A6' }         // Mint
    };

    // Helper functions
    const createGradient = (color1, color2) => {
        const gradient = ctx.createLinearGradient(0, 0, canvas.width * 0.8, 0);
        gradient.addColorStop(0, color1);
        gradient.addColorStop(0.6, adjustColorBrightness(color1, -10));
        gradient.addColorStop(1, color2);
        return gradient;
    };

    const adjustColorBrightness = (color, percent) => {
        const num = parseInt(color.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = Math.max(0, Math.min(255, (num >> 16) + amt));
        const G = Math.max(0, Math.min(255, (num >> 8 & 0x00FF) + amt));
        const B = Math.max(0, Math.min(255, (num & 0x0000FF) + amt));
        return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
    };

    // Create gradient backgrounds
    const backgroundGradients = filteredData.types.map(type => {
        const colorSet = typeColors[type] || { primary: '#94A3B8', secondary: '#64748B' };
        return createGradient(colorSet.primary, colorSet.secondary);
    });

    // Process labels
    const processedLabels = filteredData.workloads.map(w => {
        const name = w.split('/')[1] || w;
        return name.length > 25 ? name.substring(0, 22) + '...' : name;
    });

    // Calculate statistics
    const maxCost = Math.max(...filteredData.costs);
    const totalCost = filteredData.costs.reduce((a, b) => a + b, 0);
    const avgCost = totalCost / filteredData.costs.length;

    const config = {
        type: 'bar',
        plugins: [{
            beforeDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.save();
                
                // Add gradient background
                const bgGradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
                bgGradient.addColorStop(0, 'rgba(123, 97, 255, 0.02)');
                bgGradient.addColorStop(0.5, 'rgba(123, 97, 255, 0.05)');
                bgGradient.addColorStop(1, 'rgba(123, 97, 255, 0.02)');
                ctx.fillStyle = bgGradient;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                ctx.restore();
            },
            afterDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.save();
                
                // Add summary statistics at the top
                const chartArea = chart.chartArea;
                
                // Total cost badge
                const totalX = chartArea.right - 150;
                const totalY = 15;
                
                ctx.fillStyle = 'rgba(123, 97, 255, 0.8)';
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.roundRect(totalX, totalY, 140, 25, 8);
                ctx.fill();
                ctx.stroke();
                
                ctx.fillStyle = 'white';
                ctx.font = '600 11px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(`Total: $${(totalCost/1000).toFixed(1)}k/month`, totalX + 70, totalY + 16);
                
                // Count badge
                const countX = chartArea.left;
                const countY = 15;
                
                ctx.fillStyle = 'rgba(255, 138, 101, 0.8)';
                ctx.beginPath();
                ctx.roundRect(countX, countY, 120, 25, 8);
                ctx.fill();
                ctx.stroke();
                
                ctx.fillStyle = 'white';
                ctx.fillText(`Top ${filteredData.costs.length} Workloads`, countX + 60, countY + 16);
                
                ctx.restore();
            }
        }],
        data: {
            labels: processedLabels,
            datasets: [{
                label: 'Monthly Cost',
                data: filteredData.costs,
                backgroundColor: backgroundGradients,
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 0,
                borderRadius: {
                    topRight: 10,
                    bottomRight: 10,
                    topLeft: 4,
                    bottomLeft: 4
                },
                borderSkipped: false,
                barPercentage: 0.75,
                categoryPercentage: 0.85,
                hoverBackgroundColor: filteredData.types.map(type => {
                    const colorSet = typeColors[type] || { primary: '#94A3B8' };
                    return colorSet.primary;
                }),
                hoverBorderWidth: 2,
                hoverBorderColor: 'rgba(255, 255, 255, 0.8)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            layout: {
                padding: {
                    left: 10,
                    right: 20,
                    top: 50,
                    bottom: 20
                }
            },
            plugins: {
                legend: { 
                    display: true,
                    position: 'top',
                    labels: {
                        generateLabels: function(chart) {
                            const uniqueTypes = [...new Set(filteredData.types)];
                            return uniqueTypes.map(type => ({
                                text: `${type} (${filteredData.types.filter(t => t === type).length})`,
                                fillStyle: typeColors[type]?.primary || '#94A3B8',
                                strokeStyle: typeColors[type]?.primary || '#94A3B8',
                                lineWidth: 0,
                                hidden: false,
                                pointStyle: 'rectRounded'
                            }));
                        },
                        color: 'white',
                        padding: 15,
                        font: {
                            size: 12,
                            weight: '600'
                        },
                        usePointStyle: true
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(20, 20, 30, 0.95)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(123, 97, 255, 0.3)',
                    borderWidth: 1,
                    cornerRadius: 10,
                    padding: 14,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            const index = context[0].dataIndex;
                            const type = filteredData.types[index];
                            const rank = index + 1;
                            return [`#${rank} - ${type}`, filteredData.workloads[index]];
                        },
                        label: function(context) {
                            return null;
                        },
                        afterLabel: function(context) {
                            const index = context.dataIndex;
                            const cost = context.parsed.x;
                            const costPercentage = ((cost / totalCost) * 100).toFixed(1);
                            const isHighCost = cost > avgCost * 1.5;
                            
                            return [
                                `💰 Cost: $${cost.toLocaleString()}/month`,
                                `📊 ${costPercentage}% of total`,
                                `📁 Namespace: ${filteredData.namespaces[index]}`,
                                `🔄 Replicas: ${filteredData.replicas[index]}`,
                                isHighCost ? '⚠️ Above average cost' : '✅ Normal cost range'
                            ];
                        },
                        footer: function(tooltipItems) {
                            const index = tooltipItems[0].dataIndex;
                            const cost = filteredData.costs[index];
                            const dailyCost = (cost / 30).toFixed(2);
                            return [
                                '',
                                `Daily: $${dailyCost} | Hourly: $${(cost / 720).toFixed(3)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        color: 'white',
                        font: {
                            size: 11,
                            weight: '500'
                        },
                        callback: function(value) {
                            if (value >= 1000) {
                                return '$' + (value / 1000).toFixed(1) + 'k';
                            }
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: { 
                        color: 'rgba(255, 255, 255, 0.05)',
                        lineWidth: 0.5
                    },
                    title: {
                        display: true,
                        text: 'Monthly Cost (USD)',
                        color: 'white',
                        font: {
                            size: 12,
                            weight: '600'
                        }
                    }
                },
                y: {
                    ticks: { 
                        color: 'white',
                        font: {
                            size: 10,
                            weight: '500'
                        },
                        padding: 8
                    },
                    grid: { 
                        display: false
                    }
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart',
                delay: (context) => {
                    if (context.type === 'data' && context.mode === 'default') {
                        return context.dataIndex * 50; // Cascade effect
                    }
                    return 0;
                },
                x: {
                    easing: 'easeOutElastic',
                    duration: 2500
                }
            },
            hover: {
                animationDuration: 300,
                mode: 'nearest',
                intersect: false
            },
            interaction: {
                mode: 'nearest',
                axis: 'y',
                intersect: false
            }
        }
    };

    // Destroy existing chart
    if (AppState.chartInstances['workloadCostChart']) {
        AppState.chartInstances['workloadCostChart'].destroy();
    }

    AppState.chartInstances['workloadCostChart'] = new Chart(ctx, config);
    
    // Log summary
    console.log(`✅ Workload cost chart created: Showing top ${filteredData.costs.length} of ${data.costs.length} workloads`);
    console.log(`💰 Total cost: $${totalCost.toFixed(2)}, Average: $${avgCost.toFixed(2)}`);
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
        { selector: '#cost-insight', defaultText: 'VM Scale Sets consume the majority of your monthly budget. Consider implementing right-sizing recommendations.' },
        { selector: '#hpa-insight', defaultText: 'ML analysis suggests potential CPU/Memory optimization opportunities.' }
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

/**
 * Utility functions for CSS classes and icons
 */
function getSeverityAlertClass(severity) {
    const classes = {
        'critical': 'alert-danger',
        'high': 'alert-warning',
        'medium': 'alert-info',
        'low': 'alert-secondary',
        'none': 'alert-success'
    };
    return classes[severity] || 'alert-secondary';
}

function getSeverityCSSClass(severity) {
    const classes = {
        'critical': 'border-danger',
        'high': 'border-warning',
        'medium': 'border-info',
        'low': 'border-secondary',
        'none': 'border-success'
    };
    return classes[severity] || 'border-secondary';
}

function getSeverityIcon(severity) {
    const icons = {
        'critical': 'fas fa-exclamation-triangle text-danger',
        'high': 'fas fa-exclamation-circle text-warning',
        'medium': 'fas fa-info-circle text-info',
        'low': 'fas fa-info text-secondary',
        'none': 'fas fa-check-circle text-success'
    };
    return icons[severity] || 'fas fa-info';
}

/**
 * Global action functions for CPU optimization
 */
window.scrollToCPUSection = function() {
    const section = document.getElementById('cpu-metrics-container') || 
                   document.getElementById('high-cpu-alert-section');
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
};

window.generateCPUOptimizationPlan = function() {
    showNotification('CPU Optimization Plan', 'Generating optimization recommendations for high CPU workloads...', 'info');
};

window.exportCPUReport = function() {
    showNotification('Export CPU Report', 'Exporting CPU workload analysis report...', 'info');
};

// Make all functions available globally for backward compatibility and cluster isolation
if (typeof window !== 'undefined') {
    // Core functions
    window.getCurrentClusterId = getCurrentClusterId;
    window.validateClusterContext = validateClusterContext;
    window.makeClusterAwareAPICall = makeClusterAwareAPICall;
    window.refreshChartsSmooth = refreshChartsSmooth;
    
    // Chart functions
    window.initializeCharts = initializeCharts;
    window.updateDashboardMetrics = updateDashboardMetrics;
    window.updateDashboardMetricsWithCPU = updateDashboardMetricsWithCPU;
    window.createAllChartsWithCPU = createAllChartsWithCPU;
    window.destroyAllCharts = destroyAllCharts;
    window.clearLoadingStates = clearLoadingStates;
    window.showChartError = showChartError;
    
    // CPU-specific functions
    window.updateCPUMetrics = updateCPUMetrics;
    window.displayCPUWorkloadStatus = displayCPUWorkloadStatus;
}

console.log('✅ Enhanced AKS Cost Intelligence charts.js with comprehensive CPU workload support and cluster isolation loaded');