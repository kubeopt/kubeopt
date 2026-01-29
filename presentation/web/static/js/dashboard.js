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
        
        // Check URL hash first to determine initial view
        const hash = window.location.hash.substring(1); // Remove the #
        let initialView = 'overview'; // Default
        
        if (hash === 'implementation' || hash === 'alerts') {
            initialView = hash;
            console.log(`📍 URL hash detected: ${hash}, setting initial view to: ${initialView}`);
        } else if (hash) {
            console.log(`⚠️ Unknown hash: ${hash}, defaulting to overview`);
        }
        
        // Set initial view based on URL hash or default
        switchView(initialView);
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
        
        // Listen for hash changes (e.g., when navigating from settings page)
        window.addEventListener('hashchange', function() {
            const hash = window.location.hash.substring(1);
            console.log(`#️⃣ Hash changed to: ${hash}`);
            
            if (hash === 'implementation' || hash === 'alerts' || hash === 'overview') {
                switchView(hash);
            }
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
        console.log(`🔄 Switching to view: ${viewName}`);
        
        currentView = viewName;
        setActiveNavigation(viewName);
        
        // Hide all sections
        const sections = document.querySelectorAll('.dashboard-section');
        console.log(`📋 Found ${sections.length} dashboard sections`);
        sections.forEach(section => {
            section.classList.remove('active');
            console.log(`➡️ Removed active from: ${section.id}`);
        });
        
        // Show target section
        const targetSection = document.getElementById(`${viewName}-section`);
        console.log(`🎯 Target section: ${viewName}-section, found:`, !!targetSection);
        
        if (targetSection) {
            targetSection.classList.add('active');
            console.log(`✅ Added active to: ${targetSection.id}`);
            
            // Notify ChartManager of view change
            if (window.ChartManager) {
                window.ChartManager.handleViewChange();
            }
            
            loadViewContent(viewName);
        } else {
            console.error(`❌ Target section not found: ${viewName}-section`);
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
            console.log('ℹ️ No cluster ID available - likely on portfolio page, skipping dashboard data load');
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
                
                // Load node optimization recommendations
                loadNodeOptimizationData(chartData);
                
                // Load anomaly detection alerts
                loadAnomalyDetectionData(chartData);
                
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
        
        // Update optimization score - use real optimization score from analysis
        const optimizationScoreEl = document.getElementById('optimization-score');
        if (optimizationScoreEl) {
            // Use real optimization_score from metrics (stored in database)
            if (data.metrics?.optimization_score !== undefined && data.metrics.optimization_score !== null) {
                const optimizationScore = data.metrics.optimization_score;
                optimizationScoreEl.textContent = window.Utils.formatPercentage(optimizationScore);
            } else {
                throw new Error('No optimization score available in analysis data');
            }
        }
        
        // Update HPA efficiency - keep using actual HPA data
        const hpaEfficiencyEl = document.getElementById('hpa-efficiency');
        if (hpaEfficiencyEl && data.hpaComparison?.actual_hpa_efficiency !== undefined) {
            hpaEfficiencyEl.textContent = window.Utils.formatPercentage(data.hpaComparison.actual_hpa_efficiency);
        }
        
        // Update CPU metrics for Resource Utilization chart
        updateCPUMetrics(data);
    }
    
    /**
     * Update CPU metrics below Resource Utilization chart
     */
    function updateCPUMetrics(data) {
        let cpuOptimization = '--';
        let maxCPU = '--';
        let avgCPU = '--';
        
        try {
            if (data.cpuWorkloadMetrics) {
                const cpuMetrics = data.cpuWorkloadMetrics;
                
                if (cpuMetrics.avg_cpu_utilization !== undefined) {
                    avgCPU = `${Math.round(cpuMetrics.avg_cpu_utilization)}%`;
                }
                
                if (cpuMetrics.max_cpu_utilization !== undefined) {
                    maxCPU = `${Math.round(cpuMetrics.max_cpu_utilization)}%`;
                }
                
                if (cpuMetrics.optimization_score !== undefined) {
                    cpuOptimization = `${Math.round(cpuMetrics.optimization_score)}%`;
                }
            }
        } catch (error) {
            console.warn('Error extracting CPU metrics:', error);
        }
        
        const cpuOptimizationEl = document.getElementById('cpu-optimization-metric');
        if (cpuOptimizationEl && cpuOptimization !== '--') {
            cpuOptimizationEl.textContent = cpuOptimization;
        }
        
        const maxCPUEl = document.getElementById('max-cpu-metric');
        if (maxCPUEl && maxCPU !== '--') {
            maxCPUEl.textContent = maxCPU;
        }
        
        const avgCPUEl = document.getElementById('avg-cpu-metric');
        if (avgCPUEl && avgCPU !== '--') {
            avgCPUEl.textContent = avgCPU;
        }
    }
    
    // Make updateCPUMetrics globally available
    window.updateCPUMetrics = updateCPUMetrics;

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
        if (window.ImplementationPlan) {
            await window.ImplementationPlan.loadPlan();
        } else {
            console.error('ImplementationPlan module not available');
        }
    }

    /**
     * Generate new implementation plan
     */
    async function generateNewPlan() {
        if (window.ImplementationPlan) {
            await window.ImplementationPlan.generatePlan();
        } else {
            console.error('ImplementationPlan module not available');
        }
    }

    /**
     * Load alerts data
     */
    async function loadAlertsData() {
        if (window.Alerts) {
            await window.Alerts.loadAlerts();
        } else {
            console.error('Alerts module not available');
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
        
        // Dynamically display ALL insights from backend as clean bullet points
        const insightKeys = Object.keys(insights);
        
        insightKeys.forEach(key => {
            if (insights[key] && typeof insights[key] === 'string') {
                const icon = getInsightIcon(key);
                
                insightsHTML += `
                    <div class="insight-highlight">
                        <i class="fas ${icon} insight-bullet"></i>
                        <span class="insight-text">${insights[key]}</span>
                    </div>
                `;
            }
        });
        
        // Fallback message if no valid insights
        if (!insightsHTML) {
            container.innerHTML = `
                <div class="insights-loading">
                    <i class="fas fa-info-circle insights-loading-icon"></i>
                    <p>No insights available for this cluster yet. Analysis may still be processing.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <div class="insights-list">
                ${insightsHTML}
            </div>
        `;
    }
    
    /**
     * Format insight key to human-readable title
     */
    function formatInsightTitle(key) {
        const titleMap = {
            'cost_breakdown': 'Cost Analysis',
            'cost_analysis': 'Cost Analysis',
            'hpa_comparison': 'HPA Recommendations',
            'hpa_recommendations': 'HPA Recommendations',
            'resource_optimization': 'Resource Optimization',
            'resource_analysis': 'Resource Analysis',
            'security_analysis': 'Security Analysis',
            'performance_analysis': 'Performance Analysis',
            'workload_analysis': 'Workload Analysis',
            'namespace_analysis': 'Namespace Analysis',
            'node_analysis': 'Node Analysis',
            'storage_analysis': 'Storage Analysis',
            'network_analysis': 'Network Analysis'
        };
        
        return titleMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    /**
     * Get appropriate icon for insight type
     */
    function getInsightIcon(key) {
        const iconMap = {
            'cost_breakdown': 'fa-chart-pie',
            'cost_analysis': 'fa-dollar-sign',
            'hpa_comparison': 'fa-expand-arrows-alt',
            'hpa_recommendations': 'fa-expand-arrows-alt',
            'resource_optimization': 'fa-tachometer-alt',
            'resource_analysis': 'fa-microchip',
            'security_analysis': 'fa-shield-alt',
            'performance_analysis': 'fa-rocket',
            'workload_analysis': 'fa-cubes',
            'namespace_analysis': 'fa-layer-group',
            'node_analysis': 'fa-server',
            'storage_analysis': 'fa-hdd',
            'network_analysis': 'fa-network-wired'
        };
        
        return iconMap[key] || 'fa-lightbulb';
    }
    
    /**
     * Get insight category for styling
     */
    function getInsightCategory(key) {
        if (key.includes('cost')) return 'cost';
        if (key.includes('hpa')) return 'hpa';
        if (key.includes('resource')) return 'resource';
        if (key.includes('security')) return 'security';
        if (key.includes('performance')) return 'performance';
        return 'general';
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
        // Use backend-generated insights if available
        if (data.insights) {
            return data.insights;
        }
        
        // Fallback: minimal insights if backend insights not available
        console.warn('⚠️ No backend insights available, using fallback');
        const insights = {};
        
        if (data.costBreakdown && data.costBreakdown.total_cost) {
            const cost = data.costBreakdown.total_cost;
            insights.cost_analysis = `Your cluster costs $${cost.toFixed(2)}/month. Full analysis available after data processing.`;
        }
        
        return insights;
    }

    /**
     * Load node optimization recommendations data
     */
    function loadNodeOptimizationData(chartData) {
        if (!chartData || !chartData.enhanced_analysis_input) {
            console.log('No enhanced analysis data available for node optimization');
            return;
        }
        
        const nodeOptimization = chartData.enhanced_analysis_input.node_optimization;
        if (!nodeOptimization) {
            console.log('No node optimization data available');
            showNoNodeRecommendations();
            return;
        }
        
        console.log('Loading node optimization data:', nodeOptimization);
        
        // Update summary statistics
        updateNodeOptimizationSummary(nodeOptimization);
        
        // Populate recommendations
        populateNodeRecommendations(nodeOptimization.recommendations || []);
    }
    
    /**
     * Update node optimization summary statistics
     */
    function updateNodeOptimizationSummary(nodeOptimization) {
        const totalRecommendations = nodeOptimization.recommendations?.length || 0;
        const totalSavings = nodeOptimization.total_monthly_savings || 0;
        
        // Update UI elements
        const totalRecommendationsEl = document.getElementById('total-node-recommendations');
        const totalSavingsEl = document.getElementById('total-node-savings');
        
        if (totalRecommendationsEl) {
            totalRecommendationsEl.textContent = totalRecommendations;
        }
        
        if (totalSavingsEl) {
            totalSavingsEl.textContent = `$${totalSavings.toFixed(0)}`;
        }
        
        // Update node efficiency metric in main metrics
        const nodeEfficiencyEl = document.getElementById('node-efficiency-score');
        const nodeEfficiencyTrendEl = document.getElementById('node-efficiency-trend');
        
        if (nodeOptimization.efficiency_summary) {
            const avgEfficiency = nodeOptimization.efficiency_summary.average_efficiency_score || 0;
            
            if (nodeEfficiencyEl) {
                nodeEfficiencyEl.textContent = `${avgEfficiency.toFixed(0)}%`;
            }
            
            if (nodeEfficiencyTrendEl) {
                // Show trend based on efficiency score
                if (avgEfficiency >= 80) {
                    nodeEfficiencyTrendEl.textContent = '↗';
                    nodeEfficiencyTrendEl.className = 'metric-trend positive';
                } else if (avgEfficiency >= 60) {
                    nodeEfficiencyTrendEl.textContent = '→';
                    nodeEfficiencyTrendEl.className = 'metric-trend neutral';
                } else {
                    nodeEfficiencyTrendEl.textContent = '↘';
                    nodeEfficiencyTrendEl.className = 'metric-trend negative';
                }
            }
        }
    }
    
    /**
     * Populate node optimization recommendations
     */
    function populateNodeRecommendations(recommendations) {
        const gridEl = document.getElementById('node-recommendations-grid');
        const noRecommendationsEl = document.getElementById('no-node-recommendations');
        
        if (!gridEl) return;
        
        if (!recommendations || recommendations.length === 0) {
            showNoNodeRecommendations();
            return;
        }
        
        // Hide no recommendations message
        if (noRecommendationsEl) {
            noRecommendationsEl.classList.add('hidden');
        }
        
        // Clear existing content
        gridEl.innerHTML = '';
        
        // Create recommendation cards
        recommendations.forEach(rec => {
            const card = createNodeRecommendationCard(rec);
            gridEl.appendChild(card);
        });
    }
    
    /**
     * Create a node recommendation card
     */
    function createNodeRecommendationCard(recommendation) {
        const card = document.createElement('div');
        card.className = 'recommendation-card';
        
        const monthlySavings = Math.abs(recommendation.monthly_savings || 0);
        const savingsSign = (recommendation.monthly_savings || 0) < 0 ? 'Cost' : 'Savings';
        
        card.innerHTML = `
            <div class="recommendation-header">
                <div class="recommendation-title">${recommendation.node_name}</div>
                <div class="recommendation-priority ${recommendation.priority || 'medium'}">${recommendation.priority || 'medium'}</div>
            </div>
            <div class="recommendation-content">
                <div class="recommendation-description">${recommendation.reasoning || 'VM size optimization recommended'}</div>
                <div class="recommendation-change">
                    <div class="vm-change">
                        <span class="current-vm">${recommendation.current_vm_size}</span>
                        <span class="change-arrow">→</span>
                        <span class="recommended-vm">${recommendation.recommended_vm_size}</span>
                    </div>
                </div>
                <div class="recommendation-savings">
                    <div>
                        <div class="savings-amount">$${monthlySavings.toFixed(0)} ${savingsSign}</div>
                        <div class="savings-period">per month</div>
                    </div>
                    <div class="confidence-score">${(recommendation.confidence_score || 0).toFixed(0)}% confidence</div>
                </div>
            </div>
        `;
        
        return card;
    }
    
    /**
     * Show no node recommendations message
     */
    function showNoNodeRecommendations() {
        const gridEl = document.getElementById('node-recommendations-grid');
        const noRecommendationsEl = document.getElementById('no-node-recommendations');
        
        if (gridEl) {
            gridEl.innerHTML = '';
        }
        
        if (noRecommendationsEl) {
            noRecommendationsEl.classList.remove('hidden');
        }
        
        // Reset summary stats
        const totalRecommendationsEl = document.getElementById('total-node-recommendations');
        const totalSavingsEl = document.getElementById('total-node-savings');
        
        if (totalRecommendationsEl) totalRecommendationsEl.textContent = '0';
        if (totalSavingsEl) totalSavingsEl.textContent = '$0';
    }
    
    /**
     * Load anomaly detection alerts data
     */
    function loadAnomalyDetectionData(chartData) {
        if (!chartData || !chartData.enhanced_analysis_input) {
            console.log('No enhanced analysis data available for anomaly detection');
            return;
        }
        
        const anomalyData = chartData.enhanced_analysis_input.anomaly_detection;
        if (!anomalyData) {
            console.log('No anomaly detection data available');
            showNoAnomalyAlerts();
            return;
        }
        
        console.log('Loading anomaly detection data:', anomalyData);
        
        // Update summary statistics
        updateAnomalyAlertsSummary(anomalyData);
        
        // Populate alerts
        populateAnomalyAlerts(anomalyData.anomalies || []);
    }
    
    /**
     * Update anomaly alerts summary statistics
     */
    function updateAnomalyAlertsSummary(anomalyData) {
        const totalAnomalies = anomalyData.total_anomalies || 0;
        const criticalAnomalies = (anomalyData.anomalies || []).filter(a => 
            a.severity >= 0.8 || (a.impact && a.impact === 'critical')
        ).length;
        
        // Update UI elements
        const totalAnomaliesEl = document.getElementById('total-anomalies');
        const criticalAnomaliesEl = document.getElementById('critical-anomalies');
        
        if (totalAnomaliesEl) {
            totalAnomaliesEl.textContent = totalAnomalies;
        }
        
        if (criticalAnomaliesEl) {
            criticalAnomaliesEl.textContent = criticalAnomalies;
        }
    }
    
    /**
     * Populate anomaly alerts grid
     */
    function populateAnomalyAlerts(anomalies) {
        const gridEl = document.getElementById('anomaly-alerts-grid');
        const noAlertsEl = document.getElementById('no-anomaly-alerts');
        
        if (!gridEl) return;
        
        if (!anomalies || anomalies.length === 0) {
            showNoAnomalyAlerts();
            return;
        }
        
        // Hide no alerts message
        if (noAlertsEl) {
            noAlertsEl.classList.add('hidden');
        }
        
        // Clear existing content
        gridEl.innerHTML = '';
        
        // Create alert cards
        anomalies.forEach(anomaly => {
            const card = createAnomalyAlertCard(anomaly);
            gridEl.appendChild(card);
        });
    }
    
    /**
     * Create an anomaly alert card
     */
    function createAnomalyAlertCard(anomaly) {
        const card = document.createElement('div');
        const severityLevel = getSeverityLevel(anomaly.severity || 0);
        const typeIcon = getAnomalyTypeIcon(anomaly.type);
        const workloadName = anomaly.workload_name || 'System';
        
        card.className = `alert-card severity-${severityLevel}`;
        
        // Create details based on anomaly type
        const details = getAnomalyDetails(anomaly);
        
        card.innerHTML = `
            <div class="alert-header">
                <div class="alert-type">
                    <i class="fas ${typeIcon} alert-type-icon ${anomaly.type}"></i>
                    <span>${formatAnomalyType(anomaly.type)}</span>
                </div>
                <div class="alert-severity ${severityLevel}">${severityLevel}</div>
            </div>
            <div class="alert-content">
                <div class="alert-title">${workloadName}</div>
                <div class="alert-description">${anomaly.description || 'Anomaly detected'}</div>
                <div class="alert-details">
                    ${details}
                </div>
                <div class="alert-actions">
                    <div class="alert-action">${anomaly.action_required || 'Review and investigate'}</div>
                    <div class="alert-timestamp">${formatTimestamp(anomaly.timestamp)}</div>
                </div>
            </div>
        `;
        
        return card;
    }
    
    /**
     * Get severity level from numeric severity score
     */
    function getSeverityLevel(severityScore) {
        if (severityScore >= 0.8) return 'critical';
        if (severityScore >= 0.6) return 'high';
        if (severityScore >= 0.3) return 'medium';
        return 'low';
    }
    
    /**
     * Get icon for anomaly type
     */
    function getAnomalyTypeIcon(type) {
        const icons = {
            'memory_leak': 'fa-memory',
            'cpu_spike': 'fa-bolt',
            'resource_drift': 'fa-chart-line',
            'unusual_pattern': 'fa-question-circle',
            'cost_spike': 'fa-dollar-sign'
        };
        return icons[type] || 'fa-exclamation-circle';
    }
    
    /**
     * Format anomaly type for display
     */
    function formatAnomalyType(type) {
        const types = {
            'memory_leak': 'Memory Leak',
            'cpu_spike': 'CPU Spike',
            'resource_drift': 'Resource Drift',
            'unusual_pattern': 'Unusual Pattern',
            'cost_spike': 'Cost Spike'
        };
        return types[type] || 'Unknown Anomaly';
    }
    
    /**
     * Get anomaly-specific details
     */
    function getAnomalyDetails(anomaly) {
        const details = [];
        
        switch (anomaly.type) {
            case 'memory_leak':
                if (anomaly.current_usage) {
                    details.push(`<div class="alert-detail-item">
                        <span class="alert-detail-label">Current Usage:</span>
                        <span class="alert-detail-value warning-value">${anomaly.current_usage.toFixed(1)}%</span>
                    </div>`);
                }
                if (anomaly.trend_slope) {
                    details.push(`<div class="alert-detail-item">
                        <span class="alert-detail-label">Trend:</span>
                        <span class="alert-detail-value critical-value">+${anomaly.trend_slope.toFixed(1)}%/period</span>
                    </div>`);
                }
                if (anomaly.time_to_critical_hours && anomaly.time_to_critical_hours !== 'immediate') {
                    details.push(`<div class="alert-detail-item">
                        <span class="alert-detail-label">Critical in:</span>
                        <span class="alert-detail-value warning-value">${anomaly.time_to_critical_hours} hours</span>
                    </div>`);
                }
                break;
                
            case 'cpu_spike':
                if (anomaly.max_spike_value) {
                    details.push(`<div class="alert-detail-item">
                        <span class="alert-detail-label">Peak CPU:</span>
                        <span class="alert-detail-value critical-value">${anomaly.max_spike_value.toFixed(1)}%</span>
                    </div>`);
                }
                if (anomaly.baseline_cpu) {
                    details.push(`<div class="alert-detail-item">
                        <span class="alert-detail-label">Baseline:</span>
                        <span class="alert-detail-value">${anomaly.baseline_cpu.toFixed(1)}%</span>
                    </div>`);
                }
                break;
                
            case 'resource_drift':
                if (anomaly.cpu_drift_percentage) {
                    details.push(`<div class="alert-detail-item">
                        <span class="alert-detail-label">CPU Drift:</span>
                        <span class="alert-detail-value ${Math.abs(anomaly.cpu_drift_percentage) > 30 ? 'critical-value' : 'warning-value'}">
                            ${anomaly.cpu_drift_percentage > 0 ? '+' : ''}${anomaly.cpu_drift_percentage.toFixed(1)}%
                        </span>
                    </div>`);
                }
                if (anomaly.memory_drift_percentage) {
                    details.push(`<div class="alert-detail-item">
                        <span class="alert-detail-label">Memory Drift:</span>
                        <span class="alert-detail-value ${Math.abs(anomaly.memory_drift_percentage) > 30 ? 'critical-value' : 'warning-value'}">
                            ${anomaly.memory_drift_percentage > 0 ? '+' : ''}${anomaly.memory_drift_percentage.toFixed(1)}%
                        </span>
                    </div>`);
                }
                break;
                
            case 'cost_spike':
                if (anomaly.amount) {
                    details.push(`<div class="alert-detail-item">
                        <span class="alert-detail-label">Spike Amount:</span>
                        <span class="alert-detail-value critical-value">$${anomaly.amount.toFixed(2)}</span>
                    </div>`);
                }
                if (anomaly.baseline_cost) {
                    details.push(`<div class="alert-detail-item">
                        <span class="alert-detail-label">Normal Cost:</span>
                        <span class="alert-detail-value">$${anomaly.baseline_cost.toFixed(2)}</span>
                    </div>`);
                }
                break;
        }
        
        // Add confidence score if available
        if (anomaly.confidence_score && anomaly.confidence_score < 100) {
            details.push(`<div class="alert-detail-item">
                <span class="alert-detail-label">Confidence:</span>
                <span class="alert-detail-value">${anomaly.confidence_score.toFixed(0)}%</span>
            </div>`);
        }
        
        return details.join('');
    }
    
    /**
     * Format timestamp for display
     */
    function formatTimestamp(timestamp) {
        if (!timestamp) return 'Unknown time';
        
        try {
            const date = new Date(timestamp);
            return date.toLocaleString();
        } catch (e) {
            return 'Invalid time';
        }
    }
    
    /**
     * Show no anomaly alerts message
     */
    function showNoAnomalyAlerts() {
        const gridEl = document.getElementById('anomaly-alerts-grid');
        const noAlertsEl = document.getElementById('no-anomaly-alerts');
        
        if (gridEl) {
            gridEl.innerHTML = '';
        }
        
        if (noAlertsEl) {
            noAlertsEl.classList.remove('hidden');
        }
        
        // Reset summary stats
        const totalAnomaliesEl = document.getElementById('total-anomalies');
        const criticalAnomaliesEl = document.getElementById('critical-anomalies');
        
        if (totalAnomaliesEl) totalAnomaliesEl.textContent = '0';
        if (criticalAnomaliesEl) criticalAnomaliesEl.textContent = '0';
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