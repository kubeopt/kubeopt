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
 * ENHANCED: Make cluster-aware API calls with CPU data handling
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
 * ENHANCED: Initialize charts with comprehensive CPU data handling and cluster isolation
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
 * ENHANCED: Update dashboard metrics including CPU workload data
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
 * ENHANCED: Update CPU metrics in dashboard
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
 * ENHANCED: Display CPU workload status throughout the UI
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
 * ENHANCED: Show high CPU alerts throughout the UI
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
 * ENHANCED: Hide high CPU alerts when not needed
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
 * ENHANCED: Create floating CPU alert notification
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
 * ENHANCED: Create dedicated CPU metrics display
 */
/**
 * ENHANCED: Create beautiful CPU metrics display that matches the dashboard design
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
                
                <div class="cpu-metric-item metric-status">
                    <div class="metric-icon-bg">
                        <i class="fas fa-shield-check text-white"></i>
                    </div>
                    <div class="metric-content">
                        <div class="metric-value">${getEfficiencyScore(avgCPU, maxCPU)}%</div>
                        <div class="metric-label">CPU Efficiency</div>
                        <div class="metric-trend text-blue-600">
                            <i class="fas fa-chart-pie"></i>
                            <span>Calculated Score</span>
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
        default:
            return 'Unknown';
    }
}

function getEfficiencyScore(avgCPU, maxCPU) {
    // Calculate efficiency score based on CPU usage patterns
    if (maxCPU === 0) return 100;
    
    const efficiency = Math.max(0, 100 - (maxCPU - avgCPU) / maxCPU * 100);
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
 * ENHANCED: Update action panel with CPU status
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
 * ENHANCED: Update HPA section with CPU warnings
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
 * ENHANCED: Create all charts with CPU awareness and improved layout
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
            createEnhancedNodeUtilizationChart(data.nodeUtilization, isRealData);
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
 * ENHANCED: Create HPA comparison chart with better CPU integration
 */
export function createEnhancedHPAComparisonChart(data, isRealData) {
    const canvas = document.getElementById('hpaComparisonChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    console.log('🤖 Creating enhanced HPA chart with comprehensive CPU data:', data);

    // Enhanced chart configuration with better responsiveness
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
                legend: { 
                    labels: { color: colors.textColor },
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const tooltipLines = [];
                            
                            // Add ML data to tooltips
                            if (data.ml_workload_type) {
                                tooltipLines.push(`ML Classification: ${data.ml_workload_type}`);
                            }
                            if (data.ml_confidence) {
                                tooltipLines.push(`ML Confidence: ${(data.ml_confidence * 100).toFixed(0)}%`);
                            }
                            if (data.actual_hpa_savings) {
                                tooltipLines.push(`Potential Savings: $${data.actual_hpa_savings.toFixed(2)}/month`);
                            }
                            if (data.actual_hpa_efficiency) {
                                tooltipLines.push(`Current Efficiency: ${data.actual_hpa_efficiency.toFixed(1)}%`);
                            }
                            
                            // Enhanced CPU workload information in tooltips
                            if (data.cpu_workload_metrics) {
                                const cpuMetrics = data.cpu_workload_metrics;
                                tooltipLines.push(`Average CPU: ${cpuMetrics.average_cpu_utilization.toFixed(1)}%`);
                                tooltipLines.push(`Max CPU: ${cpuMetrics.max_cpu_utilization.toFixed(1)}%`);
                                
                                if (cpuMetrics.has_high_cpu_workloads) {
                                    tooltipLines.push(`⚠️ ${cpuMetrics.high_cpu_count} high CPU workload(s) - optimize before scaling`);
                                }
                            }
                            
                            return tooltipLines;
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
    
    // Update ML workload badge with enhanced CPU info
    updateMLWorkloadBadgeWithCPU(data);
    
    // Update HPA recommendation text with CPU considerations
    updateHPARecommendationTextWithCPU(data);
    
    console.log('✅ Enhanced HPA chart created with comprehensive CPU integration');
}

/**
 * ENHANCED: Update ML workload badge with CPU information
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
 * ENHANCED: Update HPA recommendation with comprehensive CPU considerations
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
 * ENHANCED: Create node utilization chart with better layout and CPU awareness
 */
export function createEnhancedNodeUtilizationChart(data, isRealData) {
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
    
    // Enhanced chart configuration with better responsiveness
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