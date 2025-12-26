/**
 * Dashboard-specific update functions for Global Auto-Refresh Manager
 * 
 * Developer: Srinivas Kondepudi
 * Organization: Nivaya Technologies & kubeopt
 */

// ===== DASHBOARD UPDATE FUNCTIONS =====

function updateDashboardOverview(data) {
    if (!data || !data.dashboard_data) return;
    
    const dashboardData = data.dashboard_data;
    
    // Update portfolio metrics on dashboard
    if (dashboardData.portfolio_summary) {
        updateDashboardPortfolioMetrics(dashboardData.portfolio_summary);
    }
    
    // Update clusters overview
    if (dashboardData.clusters_overview) {
        updateDashboardClustersOverview(dashboardData.clusters_overview);
    }
    
    // Update alerts count
    if (typeof dashboardData.alerts_count !== 'undefined') {
        updateDashboardAlertsCount(dashboardData.alerts_count);
    }
    
    console.log('✅ Dashboard overview updated');
}

function updateDashboardPortfolioMetrics(portfolioSummary) {
    // Update current cost
    const currentCostElement = document.querySelector('#current-cost, [data-metric="current-cost"]');
    if (currentCostElement) {
        animateValueUpdate(currentCostElement, portfolioSummary.total_monthly_cost || 0, true);
    }
    
    // Update potential savings
    const potentialSavingsElement = document.querySelector('#potential-savings, [data-metric="potential-savings"]');
    if (potentialSavingsElement) {
        animateValueUpdate(potentialSavingsElement, portfolioSummary.total_potential_savings || 0, true);
    }
    
    // Update savings percentage
    const savingsPercentageElement = document.querySelector('#savings-percentage');
    if (savingsPercentageElement && portfolioSummary.total_monthly_cost > 0) {
        const savingsPercentage = ((portfolioSummary.total_potential_savings || 0) / portfolioSummary.total_monthly_cost) * 100;
        savingsPercentageElement.textContent = `${savingsPercentage.toFixed(1)}%`;
    }
    
    // Update HPA efficiency
    const hpaEfficiencyElement = document.querySelector('#hpa-efficiency, [data-metric="hpa-efficiency"]');
    if (hpaEfficiencyElement) {
        animateValueUpdate(hpaEfficiencyElement, portfolioSummary.hpa_efficiency || 85, false, true);
    }
    
    // Update optimization score
    const optimizationScoreElement = document.querySelector('#optimization-score, [data-metric="optimization-score"]');
    if (optimizationScoreElement) {
        animateValueUpdate(optimizationScoreElement, portfolioSummary.avg_optimization_pct || 0, false, true);
    }
}

function updateDashboardClustersOverview(clustersOverview) {
    // Update analyzing clusters count
    const analyzingElement = document.querySelector('.dashboard-analyzing-clusters, [data-metric="analyzing-clusters"]');
    if (analyzingElement) {
        animateValueUpdate(analyzingElement, clustersOverview.analyzing_clusters || 0);
    }
    
    // Update completed clusters count
    const completedElement = document.querySelector('.dashboard-completed-clusters, [data-metric="completed-clusters"]');
    if (completedElement) {
        animateValueUpdate(completedElement, clustersOverview.completed_clusters || 0);
    }
    
    // Update failed clusters count
    const failedElement = document.querySelector('.dashboard-failed-clusters, [data-metric="failed-clusters"]');
    if (failedElement) {
        animateValueUpdate(failedElement, clustersOverview.failed_clusters || 0);
    }
}

function updateDashboardAlertsCount(alertsCount) {
    const alertsElement = document.querySelector('.dashboard-alerts-count, [data-metric="alerts-count"]');
    if (alertsElement) {
        animateValueUpdate(alertsElement, alertsCount || 0);
        
        // Update alert indicator styling
        if (alertsCount > 0) {
            alertsElement.classList.add('has-alerts');
            alertsElement.classList.remove('no-alerts');
        } else {
            alertsElement.classList.add('no-alerts');
            alertsElement.classList.remove('has-alerts');
        }
    }
}

function updateRecentAnalysis(data) {
    if (!data || !data.recent_analyses) return;
    
    const recentAnalyses = data.recent_analyses;
    const recentAnalysisContainer = document.querySelector('.recent-analysis-list, [data-component="recent-analysis"]');
    
    if (!recentAnalysisContainer) return;
    
    // Clear existing content
    recentAnalysisContainer.innerHTML = '';
    
    if (recentAnalyses.length === 0) {
        recentAnalysisContainer.innerHTML = '<p class="text-muted">No recent analyses found</p>';
        return;
    }
    
    // Generate new content
    recentAnalyses.forEach(analysis => {
        const analysisItem = createRecentAnalysisItem(analysis);
        recentAnalysisContainer.appendChild(analysisItem);
    });
    
    console.log('✅ Recent analysis updated');
}

function createRecentAnalysisItem(analysis) {
    const item = document.createElement('div');
    item.className = 'recent-analysis-item d-flex justify-content-between align-items-center p-3 mb-2 border rounded';
    
    const date = new Date(analysis.analysis_date);
    const timeAgo = getTimeAgo(date);
    
    item.innerHTML = `
        <div class="analysis-info">
            <h6 class="mb-1">${analysis.cluster_name}</h6>
            <small class="text-muted">${analysis.environment} • ${timeAgo}</small>
        </div>
        <div class="analysis-metrics text-end">
            <div class="cost-savings">
                <span class="badge bg-primary">$${analysis.total_cost.toFixed(0)} cost</span>
                <span class="badge bg-success">$${analysis.total_savings.toFixed(0)} savings</span>
            </div>
            <small class="text-muted">${analysis.optimization_pct.toFixed(1)}% optimization</small>
        </div>
    `;
    
    return item;
}

function getTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
}

// ===== IMPLEMENTATION PLAN UPDATES =====

function updateImplementationStatus(data) {
    if (!data) return;
    
    // Update implementation progress if available
    const progressElement = document.querySelector('.implementation-progress, [data-component="implementation-progress"]');
    if (progressElement && data.analysis_status) {
        updateImplementationProgress(progressElement, data);
    }
    
    // Update implementation plan status
    const statusElement = document.querySelector('.implementation-status, [data-component="implementation-status"]');
    if (statusElement) {
        updateImplementationStatusDisplay(statusElement, data);
    }
    
    console.log('✅ Implementation status updated');
}

function updateImplementationProgress(element, data) {
    const progress = data.progress || 0;
    const status = data.analysis_status || 'pending';
    
    // Update progress bar if it exists
    const progressBar = element.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = `${progress}%`;
    }
    
    // Update status text
    const statusText = element.querySelector('.status-text');
    if (statusText) {
        statusText.textContent = data.message || `${status} (${progress}%)`;
    }
}

function updateImplementationStatusDisplay(element, data) {
    const status = data.analysis_status || 'pending';
    
    // Clear existing classes
    element.classList.remove('status-pending', 'status-analyzing', 'status-completed', 'status-failed');
    
    // Add appropriate class
    element.classList.add(`status-${status}`);
    
    // Update content based on status
    if (status === 'completed') {
        element.innerHTML = '<i class="fas fa-check-circle text-success"></i> Implementation plan ready';
    } else if (status === 'analyzing' || status === 'running') {
        const progress = data.progress || 0;
        element.innerHTML = `<i class="fas fa-cog fa-spin text-primary"></i> Generating plan... ${progress}%`;
    } else if (status === 'failed') {
        element.innerHTML = '<i class="fas fa-exclamation-triangle text-danger"></i> Plan generation failed';
    } else {
        element.innerHTML = '<i class="fas fa-clock text-muted"></i> Waiting for analysis';
    }
}

// ===== ENTERPRISE METRICS UPDATES =====

function updateEnterpriseMetrics(data) {
    if (!data) return;
    
    // Update enterprise metrics display
    const metricsContainer = document.querySelector('.enterprise-metrics-container, [data-component="enterprise-metrics"]');
    if (metricsContainer && data.enterprise_metrics) {
        updateEnterpriseMetricsDisplay(metricsContainer, data.enterprise_metrics);
    }
    
    console.log('✅ Enterprise metrics updated');
}

function updateEnterpriseMetricsDisplay(container, metrics) {
    // Update operational efficiency if available
    const efficiencyElement = container.querySelector('[data-metric="operational-efficiency"]');
    if (efficiencyElement && metrics.operational_efficiency) {
        animateValueUpdate(efficiencyElement, metrics.operational_efficiency, false, true);
    }
    
    // Update cost governance score
    const governanceElement = container.querySelector('[data-metric="cost-governance"]');
    if (governanceElement && metrics.cost_governance) {
        animateValueUpdate(governanceElement, metrics.cost_governance, false, true);
    }
    
    // Update resource utilization
    const utilizationElement = container.querySelector('[data-metric="resource-utilization"]');
    if (utilizationElement && metrics.resource_utilization) {
        animateValueUpdate(utilizationElement, metrics.resource_utilization, false, true);
    }
}

// ===== SECURITY POSTURE UPDATES =====

function updateSecurityStatus(data) {
    if (!data || !data.security_status) return;
    
    const securityStatus = data.security_status;
    
    // Update security score elements
    const secureElement = document.querySelector('[data-metric="secure-clusters"]');
    if (secureElement) {
        animateValueUpdate(secureElement, securityStatus.secure_clusters || 0);
    }
    
    const atRiskElement = document.querySelector('[data-metric="at-risk-clusters"]');
    if (atRiskElement) {
        animateValueUpdate(atRiskElement, securityStatus.at_risk_clusters || 0);
    }
    
    const scansElement = document.querySelector('[data-metric="security-scans"]');
    if (scansElement) {
        animateValueUpdate(scansElement, securityStatus.security_scans_completed || 0);
    }
    
    console.log('✅ Security status updated');
}

// ===== ALERTS UPDATES =====

function updateAlertsStatus(data) {
    if (!data || !data.alerts) return;
    
    const alertsContainer = document.querySelector('.alerts-list, [data-component="alerts-list"]');
    if (!alertsContainer) return;
    
    // Update alerts display
    updateAlertsDisplay(alertsContainer, data.alerts);
    
    console.log('✅ Alerts status updated');
}

function updateAlertsDisplay(container, alerts) {
    // Clear existing content
    container.innerHTML = '';
    
    if (alerts.length === 0) {
        container.innerHTML = '<p class="text-muted">No active alerts</p>';
        return;
    }
    
    // Generate alert items
    alerts.forEach(alert => {
        const alertItem = createAlertItem(alert);
        container.appendChild(alertItem);
    });
}

function createAlertItem(alert) {
    const item = document.createElement('div');
    item.className = `alert alert-${alert.severity || 'info'} d-flex justify-content-between align-items-center`;
    
    item.innerHTML = `
        <div class="alert-content">
            <strong>${alert.title || 'Alert'}</strong>
            <p class="mb-0">${alert.message || 'No message'}</p>
        </div>
        <div class="alert-meta">
            <small class="text-muted">${getTimeAgo(new Date(alert.created_at || Date.now()))}</small>
        </div>
    `;
    
    return item;
}

// ===== UTILITY FUNCTIONS =====

// Re-use the animation function from cluster-portfolio.js if available
if (typeof animateValueUpdate !== 'function') {
    function animateValueUpdate(element, newValue, isDollar = false, isPercent = false) {
        if (!element) return;
        
        // Get current value from element
        const currentText = element.textContent.replace(/[$%,]/g, '');
        const currentValue = parseFloat(currentText) || 0;
        
        // Only animate if value changed significantly
        if (Math.abs(newValue - currentValue) < 0.01) return;
        
        // Simple update for now - can be enhanced with animation later
        let formattedValue;
        if (isDollar) {
            formattedValue = `$${Math.round(newValue)}`;
        } else if (isPercent) {
            formattedValue = `${newValue.toFixed(1)}%`;
        } else {
            formattedValue = Math.round(newValue).toString();
        }
        
        element.textContent = formattedValue;
        
        // Add visual feedback
        element.style.color = '#10b981';
        element.style.transition = 'color 0.3s ease';
        
        setTimeout(() => {
            element.style.color = '';
        }, 500);
    }
}

console.log('✅ Dashboard update functions loaded');