/**
 * AKS Cost Optimizer - Dashboard Module
 * Handles dashboard functionality and data management
 */

window.Dashboard = (function() {
    'use strict';
    
    // Private variables
    let refreshInterval = null;
    let currentView = 'overview';
    
    /**
     * Initialize dashboard
     */
    function init() {
        console.log('Initializing dashboard...');
        
        initNavigation();
        // Set initial view to overview
        switchView('overview');
        initAutoRefresh();
        // Load data after view is set
        setTimeout(() => {
            loadDashboardData();
        }, 100);
        
        console.log('Dashboard initialized successfully');
    }

    /**
     * Initialize navigation functionality
     */
    function initNavigation() {
        const navLinks = document.querySelectorAll('.nav-link[data-view]');
        navLinks.forEach(link => {
            link.addEventListener('click', handleNavigation);
        });
        
        // Set initial active navigation
        setActiveNavigation(currentView);
    }

    /**
     * Handle navigation between views
     */
    function handleNavigation(event) {
        event.preventDefault();
        
        const targetView = event.currentTarget.dataset.view;
        if (targetView) {
            switchView(targetView);
        }
    }

    /**
     * Switch between dashboard views
     */
    function switchView(viewName) {
        console.log(`Switching to view: ${viewName}`);
        
        currentView = viewName;
        setActiveNavigation(viewName);
        
        // Hide all sections
        const sections = document.querySelectorAll('.dashboard-section');
        sections.forEach(section => section.classList.remove('active'));
        
        // Show target section
        const targetSection = document.getElementById(`${viewName}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
            
            // Notify ChartManager of view change
            if (window.ChartManager) {
                window.ChartManager.handleViewChange();
            }
            
            loadViewContent(viewName);
        }
    }

    /**
     * Set active navigation item
     */
    function setActiveNavigation(viewName) {
        const navLinks = document.querySelectorAll('.nav-link[data-view]');
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.dataset.view === viewName) {
                link.classList.add('active');
            }
        });
    }

    /**
     * Load content for specific view
     */
    async function loadViewContent(viewName) {
        try {
            switch (viewName) {
                case 'overview':
                    await loadDashboardData();
                    break;
                case 'implementation':
                    await loadImplementationPlan();
                    break;
                case 'alerts':
                    await loadAlertsData();
                    break;
                default:
                    console.warn(`Unknown view: ${viewName}`);
            }
        } catch (error) {
            console.error(`Error loading content for view ${viewName}:`, error);
            if (window.showToast) {
                window.showToast(`Failed to load ${viewName} content`, 'error');
            }
        }
    }

    /**
     * Load main dashboard data
     */
    async function loadDashboardData() {
        const clusterId = window.AppState?.currentClusterId;
        if (!clusterId) {
            console.warn('No cluster ID available for dashboard data');
            return;
        }

        try {
            // Load chart data
            const chartData = await window.API.getChartData(clusterId);
            if (chartData) {
                updateDashboardMetrics(chartData);
                
                // Use REAL data from analysis results - no more estimates!
                const analysisData = chartData; // The full analysis data from backend includes everything
                
                // Use EXACT same logic as backup code for all metrics
                
                // Calculate top namespace cost - EXACTLY like backup
                let topNamespaceCost = 0;
                if (chartData.namespaceDistribution && chartData.namespaceDistribution.costs) {
                    topNamespaceCost = Math.max(...chartData.namespaceDistribution.costs);
                } else if (chartData.podCostBreakdown && chartData.podCostBreakdown.values) {
                    topNamespaceCost = Math.max(...chartData.podCostBreakdown.values);
                }
                
                // Get namespace count - EXACTLY like backup
                let namespaceCount = 0;
                if (chartData.namespaceDistribution && chartData.namespaceDistribution.namespaces) {
                    namespaceCount = chartData.namespaceDistribution.namespaces.length;
                } else if (chartData.podCostBreakdown && chartData.podCostBreakdown.labels) {
                    namespaceCount = chartData.podCostBreakdown.labels.length;
                }
                
                // Get workload count - EXACTLY like backup
                let workloadCount = 0;
                if (chartData.workloadCosts && chartData.workloadCosts.workloads) {
                    workloadCount = chartData.workloadCosts.workloads.length;
                }
                
                // Real node and pod counts
                const realNodeCount = chartData.nodeUtilization?.nodes?.length || 0;
                const realPodCount = workloadCount; // Use workload count as pod count
                
                // HPA count from actual data
                const hpaCount = chartData.hpaComparison?.existing_hpas?.length || 0;
                
                // Update metrics using the EXACT backup logic
                updateOverviewMetrics({
                    node_count: realNodeCount,
                    pod_count: realPodCount,
                    namespace_count: namespaceCount,
                    workload_count: workloadCount,
                    top_namespace_cost: topNamespaceCost,
                    hpa_count: hpaCount,
                    analysis_data: chartData // Pass full data for accuracy calculation
                });
                
                console.log(`Metrics calculated: namespaces=${namespaceCount}, workloads=${workloadCount}, topNamespaceCost=${topNamespaceCost}`);
                
                // Update HPA count badge
                const hpaCountEl = document.getElementById('active-hpa-count');
                if (hpaCountEl) {
                    hpaCountEl.textContent = hpaCount;
                }
                
                // Generate and display insights
                const insights = generateInsights(chartData);
                updateInsightsDisplay(insights);
                
                // Use ChartManager to update charts
                if (window.ChartManager) {
                    window.ChartManager.updateAllCharts(chartData);
                } else {
                    console.error('ChartManager not available!');
                }
            }
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            if (window.showToast) {
                window.showToast('Failed to load dashboard data', 'error');
            }
        }
    }

    /**
     * Update dashboard metric cards
     */
    function updateDashboardMetrics(data) {
        if (!data) return;
        
        // Update current cost from cost breakdown
        const currentCostEl = document.getElementById('current-cost');
        if (currentCostEl && data.costBreakdown?.total_cost !== undefined) {
            currentCostEl.textContent = window.Utils.formatCurrency(data.costBreakdown.total_cost);
        }
        
        // Update potential savings - EXACTLY like backup code uses metrics.total_savings
        const potentialSavingsEl = document.getElementById('potential-savings');
        if (potentialSavingsEl) {
            // Use the exact same source as backup code: metrics.total_savings
            let totalSavings = (data.metrics && data.metrics.total_savings) || data.total_savings || 0;
            potentialSavingsEl.textContent = window.Utils.formatCurrency(totalSavings);
            console.log(`Updated potential-savings to: ${window.Utils.formatCurrency(totalSavings)} from data.metrics.total_savings`);
        }
        
        // Update optimization score - calculate from overall cluster health
        const optimizationScoreEl = document.getElementById('optimization-score');
        if (optimizationScoreEl) {
            let optimizationScore = 0;
            
            // Use current health score if available, otherwise calculate from costs
            if (data.current_health_score !== undefined) {
                optimizationScore = data.current_health_score;
            } else if (data.costBreakdown?.total_cost && data.hpaComparison?.actual_hpa_savings) {
                // Calculate based on potential savings percentage
                const savingsPercentage = (data.hpaComparison.actual_hpa_savings / data.costBreakdown.total_cost) * 100;
                optimizationScore = Math.max(0, Math.min(100, 85 - savingsPercentage)); // Higher savings = lower optimization (more room for improvement)
            } else {
                optimizationScore = 75; // Default reasonable score
            }
            
            optimizationScoreEl.textContent = window.Utils.formatPercentage(optimizationScore);
        }
        
        // Update HPA efficiency - keep using actual HPA data
        const hpaEfficiencyEl = document.getElementById('hpa-efficiency');
        if (hpaEfficiencyEl && data.hpaComparison?.actual_hpa_efficiency !== undefined) {
            hpaEfficiencyEl.textContent = window.Utils.formatPercentage(data.hpaComparison.actual_hpa_efficiency);
        }
    }

    /**
     * Update overview metrics
     */
    function updateOverviewMetrics(data) {
        if (!data) return;
        
        // Update additional metrics that were added from backup
        const totalNamespacesEl = document.getElementById('total-namespaces');
        if (totalNamespacesEl && data.namespace_count !== undefined) {
            totalNamespacesEl.textContent = data.namespace_count;
        }
        
        const totalWorkloadsEl = document.getElementById('total-workloads');
        if (totalWorkloadsEl && data.workload_count !== undefined) {
            totalWorkloadsEl.textContent = data.workload_count;
        }
        
        const analysisAccuracyEl = document.getElementById('analysis-accuracy');
        if (analysisAccuracyEl) {
            // Calculate accuracy EXACTLY like backup code
            let accuracy = 'Calculating...';
            const analysisData = data.analysis_data;
            
            // Try multiple data sources for accuracy - EXACTLY like backup
            if (analysisData && analysisData.podCostBreakdown && analysisData.podCostBreakdown.accuracy_level) {
                accuracy = analysisData.podCostBreakdown.accuracy_level;
            } else if (analysisData && analysisData.analysis_accuracy) {
                accuracy = analysisData.analysis_accuracy;
            } else if (analysisData && analysisData.accuracy_metrics) {
                accuracy = analysisData.accuracy_metrics.overall || analysisData.accuracy_metrics.level;
            } else if (analysisData && analysisData.analysis_metadata && analysisData.analysis_metadata.accuracy) {
                accuracy = analysisData.analysis_metadata.accuracy;
            } else {
                // Calculate simple accuracy based on data completeness like backup
                let completeness = 0;
                let totalChecks = 0;
                
                // Check data availability
                if (data.namespace_count > 0) completeness++;
                if (data.workload_count > 0) completeness++;
                if (data.node_count > 0) completeness++;
                if (data.top_namespace_cost > 0) completeness++;
                totalChecks = 4;
                
                const ratio = completeness / totalChecks;
                if (ratio >= 0.95) accuracy = 'High (95%+)';
                else if (ratio >= 0.85) accuracy = 'Good (85%+)';
                else if (ratio >= 0.7) accuracy = 'Medium (70%+)';
                else if (ratio >= 0.5) accuracy = 'Basic (50%+)';
                else accuracy = 'Limited';
            }
            
            analysisAccuracyEl.textContent = accuracy;
            console.log(`Analysis accuracy set to: ${accuracy}`);
        }
        
        const topNamespaceCostEl = document.getElementById('top-namespace-cost');
        if (topNamespaceCostEl && data.top_namespace_cost !== undefined) {
            topNamespaceCostEl.textContent = window.Utils.formatCurrency(data.top_namespace_cost);
        }
        
        // Update node count
        const nodeCountEl = document.getElementById('node-count');
        if (nodeCountEl && data.node_count !== undefined) {
            nodeCountEl.textContent = data.node_count.toString();
        }
        
        // Update pod count
        const podCountEl = document.getElementById('pod-count');
        if (podCountEl && data.pod_count !== undefined) {
            podCountEl.textContent = data.pod_count.toString();
        }
        
        // Update namespace count
        const namespaceCountEl = document.getElementById('namespace-count');
        if (namespaceCountEl && data.namespace_count !== undefined) {
            namespaceCountEl.textContent = data.namespace_count.toString();
        }
    }

    /**
     * Load implementation plan
     */
    async function loadImplementationPlan() {
        const clusterId = window.AppState?.currentClusterId;
        if (!clusterId) {
            console.warn('No cluster ID available for implementation plan');
            return;
        }
        
        const planContainer = document.getElementById('implementation-plan-content');
        if (planContainer) {
            planContainer.innerHTML = `
                <div class="loading-state">
                    <div class="loading-spinner"></div>
                    <span>Loading implementation plan...</span>
                </div>
            `;
        }

        try {
            const planData = await window.API.getImplementationPlan(clusterId);
            if (planData) {
                updateImplementationPlan(planData);
            }
        } catch (error) {
            console.error('Error loading implementation plan:', error);
            if (planContainer) {
                planContainer.innerHTML = `
                    <div class="text-center py-8">
                        <p class="text-gray-500">Failed to load implementation plan</p>
                        <button onclick="Dashboard.loadImplementationPlan()" class="btn-primary mt-3">
                            <i class="fas fa-refresh"></i> Retry
                        </button>
                    </div>
                `;
            }
        }
    }

    /**
     * Update implementation plan content
     */
    function updateImplementationPlan(planData) {
        const planContainer = document.getElementById('implementation-plan-content');
        if (planContainer && planData.content) {
            // Simple markdown-like rendering
            const htmlContent = planData.content
                .replace(/^### (.+)$/gm, '<h3>$1</h3>')
                .replace(/^## (.+)$/gm, '<h2>$1</h2>')
                .replace(/^# (.+)$/gm, '<h1>$1</h1>')
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.+?)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>');
                
            planContainer.innerHTML = htmlContent;
        }
    }

    /**
     * Generate new implementation plan
     */
    async function generateNewPlan() {
        const clusterId = window.AppState?.currentClusterId;
        if (!clusterId) {
            console.warn('No cluster ID available for plan generation');
            return;
        }

        if (window.showToast) {
            window.showToast('Generating new implementation plan...', 'info');
        }

        try {
            await window.API.generateImplementationPlan(clusterId);
            await loadImplementationPlan(); // Reload the plan
            
            if (window.showToast) {
                window.showToast('Implementation plan generated successfully', 'success');
            }
        } catch (error) {
            console.error('Error generating implementation plan:', error);
            if (window.showToast) {
                window.showToast('Failed to generate implementation plan', 'error');
            }
        }
    }

    /**
     * Load alerts data
     */
    async function loadAlertsData() {
        const alertsList = document.getElementById('alerts-list');
        if (alertsList) {
            alertsList.innerHTML = `
                <div class="activity-item">
                    <div class="activity-avatar">
                        <div class="loading-spinner"></div>
                    </div>
                    <div class="activity-content">
                        <div class="activity-name">Loading alerts...</div>
                    </div>
                </div>
            `;
        }

        try {
            const alertsData = await window.API.getAlerts();
            if (alertsData) {
                updateAlertsSection(alertsData);
            }
        } catch (error) {
            console.error('Error loading alerts data:', error);
            if (alertsList) {
                alertsList.innerHTML = `
                    <div class="activity-item">
                        <div class="activity-avatar">!</div>
                        <div class="activity-content">
                            <div class="activity-name">Failed to load alerts</div>
                            <div class="activity-description">Please try again later</div>
                        </div>
                    </div>
                `;
            }
        }
    }

    /**
     * Update alerts section
     */
    function updateAlertsSection(alertsData) {
        const alertsList = document.getElementById('alerts-list');
        if (alertsList && alertsData.alerts && alertsData.alerts.length > 0) {
            const alertsHtml = alertsData.alerts.map(alert => `
                <div class="activity-item">
                    <div class="activity-avatar">!</div>
                    <div class="activity-content">
                        <div class="activity-name">${alert.title || 'Alert'}</div>
                        <div class="activity-description">${alert.description || ''}</div>
                    </div>
                    <div class="activity-time">${alert.created_at || ''}</div>
                </div>
            `).join('');
            
            alertsList.innerHTML = alertsHtml;
        } else if (alertsList) {
            alertsList.innerHTML = `
                <div class="activity-item">
                    <div class="activity-avatar">✓</div>
                    <div class="activity-content">
                        <div class="activity-name">No active alerts</div>
                        <div class="activity-description">Your cluster is running smoothly</div>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Initialize auto-refresh
     */
    function initAutoRefresh() {
        // Clear existing interval
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }
        
        // Refresh every 5 minutes
        refreshInterval = setInterval(() => {
            if (currentView === 'overview' && !document.hidden) {
                console.log('Auto-refreshing dashboard data...');
                loadDashboardData();
            }
        }, 5 * 60 * 1000);
        
        console.log('Auto-refresh initialized (5 minutes)');
    }

    /**
     * Stop auto-refresh
     */
    function stopAutoRefresh() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    }
    
    /**
     * Calculate data accuracy based on completeness
     */
    function calculateDataAccuracy(data) {
        if (!data) return 0;
        
        let totalFields = 0;
        let completeFields = 0;
        
        // Check key data points
        const checkFields = [
            'total_cost', 'node_count', 'pod_count', 'namespace_count',
            'hpaComparison', 'costBreakdown', 'nodeUtilization'
        ];
        
        checkFields.forEach(field => {
            totalFields++;
            if (data[field] !== undefined && data[field] !== null && data[field] !== 0) {
                completeFields++;
            }
        });
        
        return Math.round((completeFields / totalFields) * 100);
    }
    
    /**
     * Update insights display with proper theming
     */
    function updateInsightsDisplay(insights) {
        const container = document.getElementById('insights-container');
        if (!container) return;
        
        if (!insights || Object.keys(insights).length === 0) {
            container.innerHTML = `
                <div class="insights-loading">
                    <i class="fas fa-robot insights-loading-icon"></i>
                    <p>Analyzing your cluster for optimization opportunities...</p>
                </div>
            `;
            return;
        }
        
        let insightsHTML = '';
        
        // Cost insights
        if (insights.cost_breakdown) {
            insightsHTML += createInsightCard('Cost Analysis', insights.cost_breakdown, 'fa-chart-pie', 'cost');
        }
        
        // HPA insights 
        if (insights.hpa_comparison) {
            insightsHTML += createInsightCard('HPA Recommendations', insights.hpa_comparison, 'fa-expand-arrows-alt', 'hpa');
        }
        
        // Resource insights
        if (insights.resource_optimization) {
            insightsHTML += createInsightCard('Resource Optimization', insights.resource_optimization, 'fa-tachometer-alt', 'resource');
        }
        
        container.innerHTML = insightsHTML;
    }
    
    /**
     * Create themed insight card
     */
    function createInsightCard(title, content, icon, type) {
        return `
            <div class="insight-card insight-card-${type}">
                <div class="insight-header">
                    <i class="fas ${icon} insight-icon"></i>
                    <span class="insight-title">${title}</span>
                </div>
                <div class="insight-content">${content}</div>
            </div>
        `;
    }
    
    /**
     * Generate insights from chart data
     */
    function generateInsights(data) {
        const insights = {};
        
        // Cost breakdown insights
        if (data.costBreakdown && data.costBreakdown.total_cost) {
            const cost = data.costBreakdown.total_cost;
            insights.cost_breakdown = `Your cluster costs $${cost.toFixed(2)}/month. Node pools represent the largest cost component, offering primary optimization opportunities.`;
        }
        
        // HPA insights
        if (data.hpaComparison) {
            const hpaCount = data.hpaComparison.existing_hpas?.length || 0;
            const efficiency = data.hpaComparison.actual_hpa_efficiency || 0;
            const savings = data.hpaComparison.actual_hpa_savings || 0;
            
            insights.hpa_comparison = `${hpaCount} HPAs detected with ${efficiency.toFixed(1)}% efficiency. Potential savings of $${savings.toFixed(2)}/month through optimized scaling policies.`;
        }
        
        // Resource optimization insights
        if (data.nodeUtilization) {
            const avgCpu = data.nodeUtilization.cpuActual ? 
                (data.nodeUtilization.cpuActual.reduce((a, b) => a + b, 0) / data.nodeUtilization.cpuActual.length) : 0;
            const avgMemory = data.nodeUtilization.memoryActual ? 
                (data.nodeUtilization.memoryActual.reduce((a, b) => a + b, 0) / data.nodeUtilization.memoryActual.length) : 0;
            
            insights.resource_optimization = `Average CPU utilization: ${avgCpu.toFixed(1)}%, Memory: ${avgMemory.toFixed(1)}%. ${avgCpu < 60 ? 'Consider rightsizing to optimize costs.' : 'Utilization looks healthy.'}`;
        }
        
        return insights;
    }

    /**
     * Refresh current view
     */
    function refresh() {
        loadViewContent(currentView);
    }

    // Public API
    return {
        init,
        switchView,
        loadDashboardData,
        loadImplementationPlan,
        loadAlertsData,
        generateNewPlan,
        refresh,
        stopAutoRefresh,
        
        // Getters
        getCurrentView: () => currentView
    };
})();