/**
 * Enterprise Metrics Dashboard JavaScript
 * Handles loading, displaying, and interacting with enterprise operational metrics
 */

class EnterpriseMetricsManager {
    constructor() {
        this.currentData = null;
        this.refreshInterval = null;
        this.initialized = false;
        
        this.bindEvents();
        console.log('🏢 Enterprise Metrics Manager initialized');
    }

    bindEvents() {
        // Export button
        const exportBtn = document.getElementById('export-enterprise-metrics');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportMetrics());
        }

        // View Recommendations button
        const viewRecommendationsBtn = document.querySelector('.bg-blue-600');
        if (viewRecommendationsBtn && viewRecommendationsBtn.textContent.includes('View Recommendations')) {
            viewRecommendationsBtn.addEventListener('click', () => this.showRecommendationsModal());
        }

        // Event handlers are bound globally outside the constructor
    }

    async loadEnterpriseMetrics() {
        console.log('📊 Loading enterprise metrics...');
        
        // Check if enterprise metrics features are enabled
        if (window.checkFeatureAccess && !window.checkFeatureAccess('enterprise_metrics')) {
            console.log('🔒 Enterprise metrics features are locked - skipping API call');
            this.showLockedMessage();
            return;
        }
        
        this.showLoading();
        this.hideError();
        this.hideMainContent();

        try {
            // Get cluster information from current page context
            const clusterId = this.getClusterIdFromUrl();
            console.log('🔍 Loading metrics for cluster');
            
            // Check if we have a valid cluster ID
            if (clusterId === 'default') {
                throw new Error('No specific cluster selected. Please navigate to a cluster page first.');
            }
            
            const response = await fetch(`/api/enterprise-metrics?cluster_id=${clusterId}&force_refresh=true`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
            }

            const result = await response.json();
            console.log('📊 API Response:', result);
            
            if (result.status === 'error') {
                throw new Error(result.message || 'Failed to load enterprise metrics');
            }

            if (!result.data) {
                throw new Error('No data received from enterprise metrics API');
            }

            // Validate that we have the expected data structure
            if (!result.data.operational_metrics) {
                console.log('⚠️ No operational metrics in response, but will try to render anyway');
            }

            this.currentData = result.data;
            this.renderMetrics(result.data);
            this.hideLoading();
            this.showMainContent();

            console.log('✅ Enterprise metrics loaded successfully');
            console.log('📊 Data structure:', {
                hasEnterpriseMaturity: !!result.data.enterprise_maturity,
                hasOperationalMetrics: !!result.data.operational_metrics,
                metricsCount: result.data.operational_metrics ? Object.keys(result.data.operational_metrics).length : 0,
                hasActionItems: !!result.data.action_items,
                source: result.source
            });
            
            // Debug metric scores to identify zero values
            if (result.data.operational_metrics) {
                console.log('🔍 Metric Scores Debug:');
                Object.entries(result.data.operational_metrics).forEach(([key, metric]) => {
                    console.log(`  Metric processed: score=${metric.score}`);
                    if (metric.score === 0) {
                        console.log(`⚠️ Zero score for ${key}:`, metric);
                    }
                    if (typeof metric.details === 'string') {
                        console.log('✅ String details processed');
                    }
                });
            }

        } catch (error) {
            console.error('❌ Failed to load enterprise metrics:', error);
            
            // Show the real error with detailed troubleshooting
            let errorMessage = `Failed to load enterprise metrics: ${error.message}`;
            
            // Add specific troubleshooting based on error type
            if (error.message.includes('No analysis data available') || error.message.includes('Please run cluster analysis first')) {
                errorMessage = '📊 Latest Analysis Not Available Yet\n\n' +
                             '🔄 To view Enterprise Metrics, please run an analysis first:\n\n' +
                             '📋 Quick Steps:\n' +
                             '1. Click the "Run Analysis" button on this cluster\n' +
                             '2. Wait for the analysis to complete\n' +
                             '3. Return to this tab to view your metrics\n\n' +
                             '💡 Enterprise Metrics provide deep insights after analyzing your cluster data.';
            } else if (error.message.includes('No specific cluster selected')) {
                errorMessage = '🏠 Enterprise Metrics requires a specific cluster to be selected.\n\n' +
                             '📋 Steps to view metrics:\n' +
                             '1. Go to the home page\n' +
                             '2. Select a specific cluster from the list\n' +
                             '3. Navigate to the Enterprise Metrics tab\n\n' +
                             '💡 Enterprise Metrics analyzes real cluster data and requires a specific cluster context.';
            } else if (error.message.includes('cluster_id parameter required')) {
                errorMessage += '\n\nPlease ensure you are viewing this from a specific cluster page.';
            } else if (error.message.includes('not found')) {
                errorMessage += '\n\nThe cluster may need to be re-registered or may not be accessible.';
            } else if (error.message.includes('subscription')) {
                errorMessage += '\n\nCheck that the Azure subscription is properly configured and accessible.';
            } else if (error.message.includes('timeout') || error.message.includes('calculation failed')) {
                errorMessage += '\n\nThe cluster analysis is taking longer than expected. This may indicate connectivity issues.';
            }
            
            this.showError(errorMessage);
            this.hideLoading();
        }
    }

    renderMetrics(data) {
        if (!data) {
            console.error('❌ No data provided to renderMetrics');
            return;
        }

        console.log('🎨 Starting to render enterprise metrics...');

        // Update overall maturity
        console.log('🎯 Updating maturity overview...');
        this.updateMaturityOverview(data.enterprise_maturity);

        // Update individual metrics
        console.log('📊 Updating individual metrics...');
        this.updateIndividualMetrics(data.operational_metrics);

        // Update action items
        console.log('📋 Updating action items...');
        this.updateActionItems(data.action_items || []);

        // Update timestamp
        console.log('⏰ Updating timestamp...');
        this.updateTimestamp(data.enterprise_maturity.timestamp);
        
        // Update Quick Actions with specific issues
        console.log('⚡ Updating quick actions...');
        this.updateQuickActions(data);
        
        console.log('✅ Finished rendering enterprise metrics');
    }

    updateMaturityOverview(maturity) {
        console.log('🔍 DEBUG: updateMaturityOverview called with:', maturity);
        const levelEl = document.getElementById('maturity-level');
        const scoreEl = document.getElementById('maturity-score');
        const progressEl = document.getElementById('maturity-progress');
        
        console.log('🔍 DEBUG: DOM elements found:', {
            levelEl: !!levelEl,
            scoreEl: !!scoreEl,
            progressEl: !!progressEl
        });

        if (levelEl) levelEl.textContent = maturity.level;
        if (scoreEl) scoreEl.textContent = Math.round(maturity.score);
        if (progressEl) progressEl.style.width = `${maturity.score}%`;

        // Update level styling based on maturity
        if (levelEl) {
            levelEl.className = 'text-2xl font-bold mt-2 ' + this.getMaturityLevelColor(maturity.level);
        }
    }

    updateIndividualMetrics(metrics) {
        console.log('🔍 DEBUG: updateIndividualMetrics called with:', metrics);
        for (const [metricKey, metricData] of Object.entries(metrics)) {
            console.log('🔍 DEBUG: Processing metric');
            this.updateMetricCard(metricKey, metricData);
        }
    }

    updateMetricCard(metricKey, data) {
        console.log('🔍 DEBUG: updateMetricCard called');
        const card = document.querySelector(`[data-metric="${metricKey}"]`);
        console.log('🔍 DEBUG: Card lookup completed');
        if (!card) {
            console.error(`❌ DEBUG: No card found for metric ${metricKey}`);
            return;
        }

        // Make entire card clickable for better UX
        card.style.cursor = 'pointer';
        card.onclick = () => this.showMetricDetails(metricKey, data);

        // Update score with context and trend
        const scoreEl = card.querySelector('.metric-score');
        if (scoreEl) {
            const score = Math.round(data.score);
            const context = this.getScoreContext(metricKey, score, data);
            const trendArrow = this.getTrendArrow(metricKey, score, data);
            scoreEl.innerHTML = `${score} ${trendArrow}<span class="text-xs font-normal block text-gray-400">${context}</span>`;
            scoreEl.className = 'text-xl font-bold ' + this.getScoreColor(score);
        }

        // Update progress bar
        const progressBar = card.querySelector('.metric-progress div');
        if (progressBar) {
            progressBar.style.width = `${data.score}%`;
        }

        // Update details
        const detailsEl = card.querySelector('.metric-details');
        if (detailsEl && data.details) {
            const detailsHtml = this.formatMetricDetails(data.details);
            const viewReportLink = `
                <div class="mt-3 pt-2 border-t border-gray-600">
                    <button class="view-metric-report text-green-400 hover:text-green-300 text-xs font-medium" 
                            data-metric-key="${metricKey}">
                        📄 Click card for detailed analysis →
                    </button>
                </div>
            `;
            detailsEl.innerHTML = detailsHtml + viewReportLink;
        }

        // Add hover effects
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-2px)';
            card.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.4)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = '';
        });
    }

    formatMetricDetails(details) {
        // Handle string details (simple format)
        if (typeof details === 'string') {
            return `<div class="text-gray-300">${details}</div>`;
        }
        
        // Handle object details (structured format)
        const items = [];
        
        // Show summary first if available
        if (details.summary) {
            items.push(`<div class="text-gray-300 mb-2">${details.summary}</div>`);
        }
        
        // Common details to show for all metrics
        if (details.current_version) {
            items.push(`Version: ${details.current_version}`);
        }
        if (details.total_workloads !== undefined) {
            items.push(`Workloads: ${details.total_workloads}`);
        }
        if (details.backup_solutions && details.backup_solutions.length > 0) {
            items.push(`Backup Tools: ${details.backup_solutions.length}`);
        }
        if (details.deployment_frequency_per_day !== undefined) {
            items.push(`Deploy Freq: ${details.deployment_frequency_per_day.toFixed(2)}/day`);
        }
        if (details.release_frequency_per_week !== undefined) {
            items.push(`Release Freq: ${details.release_frequency_per_week.toFixed(1)}/week`);
        }
        if (details.change_failure_rate !== undefined) {
            items.push(`Failure Rate: ${(details.change_failure_rate * 100).toFixed(1)}%`);
        }
        if (details.cpu_utilization_pct !== undefined) {
            items.push(`CPU Usage: ${details.cpu_utilization_pct.toFixed(1)}%`);
        }
        if (details.memory_utilization_pct !== undefined) {
            items.push(`Memory Usage: ${details.memory_utilization_pct.toFixed(1)}%`);
        }
        if (details.requested_cpu_cores !== undefined) {
            items.push(`CPU Requests: ${details.requested_cpu_cores} cores`);
        }
        if (details.requested_memory_gb !== undefined) {
            items.push(`Memory Requests: ${details.requested_memory_gb} GB`);
        }

        return items.map(item => `<div class="text-xs text-gray-400">${item}</div>`).join('');
    }

    updateActionItems(actionItems) {
        const container = document.getElementById('action-items-list');
        if (!container) return;

        if (actionItems.length === 0) {
            container.innerHTML = '<div class="text-gray-400">No critical action items found.</div>';
            return;
        }

        container.innerHTML = actionItems.slice(0, 5).map((item, index) => `
            <div class="flex items-start space-x-3 p-3 bg-gray-700 rounded-lg">
                <div class="flex-shrink-0 w-6 h-6 bg-green-600 rounded-full flex items-center justify-center text-xs font-bold text-white">
                    ${index + 1}
                </div>
                <div class="flex-grow text-gray-300">
                    ${this.escapeHtml(item)}
                </div>
            </div>
        `).join('');
    }

    updateTimestamp(timestamp) {
        const timestampEl = document.getElementById('assessment-timestamp');
        if (timestampEl && timestamp) {
            const date = new Date(timestamp);
            timestampEl.textContent = date.toLocaleString();
        }
    }

    getMaturityLevelColor(level) {
        switch (level) {
            case 'OPTIMIZED': return 'text-green-500';
            case 'ADVANCED': return 'text-green-500';
            case 'INTERMEDIATE': return 'text-yellow-500';
            case 'BASIC': return 'text-orange-500';
            case 'AD-HOC': return 'text-red-500';
            default: return 'text-gray-400';
        }
    }

    getRiskLevelColor(riskLevel) {
        switch (riskLevel) {
            case 'OPTIMAL': return 'text-green-500';
            case 'ACCEPTABLE': return 'text-yellow-500';
            case 'NEEDS_ATTENTION': return 'text-orange-500';
            case 'CRITICAL': return 'text-red-500';
            default: return 'text-gray-400';
        }
    }
    
    getScoreColor(score) {
        if (score >= 81) return 'text-green-500';
        if (score >= 61) return 'text-yellow-500';
        if (score >= 41) return 'text-orange-500';
        return 'text-red-500';
    }
    
    getScoreContext(metricKey, score, data) {
        const details = data.details || {};
        
        switch (metricKey) {
            case 'kubernetes_upgrade_readiness':
                const deprecatedCount = details.deprecated_api_count || 0;
                const versionGap = details.version_gap || 0;
                if (deprecatedCount > 0) return `${deprecatedCount} deprecated APIs`;
                if (versionGap > 0) return `${versionGap} versions behind`;
                return score >= 81 ? 'Ready to upgrade' : 'Upgrade planning needed';
                
            case 'disaster_recovery_score':
                const backupCount = details.backup_solution_count || 0;
                const snapCoverage = details.snapshot_coverage_pct || 0;
                if (backupCount === 0) return 'No backups configured';
                if (snapCoverage < 50) return `${Math.round(snapCoverage)}% snapshot coverage`;
                return `RTO: ${details.estimated_rto_hours || 'unknown'}h`;
                
            case 'capacity_planning':
                const cpuUtil = details.cpu_utilization_pct || 0;
                const memUtil = details.memory_utilization_pct || 0;
                const requestedCpu = details.requested_cpu_cores || 0;
                if (requestedCpu === 0) return 'No resource requests';
                if (cpuUtil === 0 && memUtil === 0) return 'Resource governance missing';
                return `${Math.round((cpuUtil + memUtil) / 2)}% utilization`;
                
            case 'compliance_readiness':
                const criticalIssues = details.critical_issues || [];
                if (criticalIssues.length > 0) return `${criticalIssues.length} critical issues`;
                return score >= 81 ? 'CIS compliant' : 'Some gaps found';
                
            case 'operational_maturity':
                const deployFreq = details.deployment_frequency_per_day || 0;
                const gitopsTools = details.gitops_tools || [];
                if (gitopsTools.length === 0) return 'Manual deployments';
                if (deployFreq < 0.1) return `${deployFreq.toFixed(2)}/day deploys`;
                return 'DevOps practices active';
                
            case 'team_velocity':
                const releaseFreq = details.release_frequency_per_week || 0;
                const activeDeployments = details.active_deployments || 0;
                const stableDeployments = details.stable_deployments || 0;
                if (releaseFreq === 0 && activeDeployments > 0) return `${activeDeployments} legacy deployments`;
                if (releaseFreq < 0.5) return `${releaseFreq.toFixed(1)} releases/week`;
                return `${stableDeployments}/${activeDeployments} stable`;
                
            default:
                return score >= 81 ? 'Optimal' : score >= 61 ? 'Acceptable' : score >= 41 ? 'Needs attention' : 'Critical';
        }
    }

    getTrendArrow(metricKey, score, data) {
        const details = data.details || {};
        
        switch (metricKey) {
            case 'kubernetes_upgrade_readiness':
                const versionGap = details.version_gap || 0;
                if (versionGap === 0) return '<span class="text-green-500">↗</span>';
                if (versionGap <= 2) return '<span class="text-yellow-500">→</span>';
                return '<span class="text-red-500">↘</span>';
                
            case 'disaster_recovery_score':
                const backupCount = details.backup_solutions?.length || 0;
                const hasMultiAz = details.multi_az_deployment || false;
                if (backupCount >= 2 && hasMultiAz) return '<span class="text-green-500">↗</span>';
                if (backupCount >= 1) return '<span class="text-yellow-500">→</span>';
                return '<span class="text-red-500">↘</span>';
                
            case 'operational_maturity':
                const deployFreq = details.deployment_frequency_per_day || 0;
                const failureRate = details.change_failure_rate || 0;
                if (deployFreq > 1 && failureRate < 0.05) return '<span class="text-green-500">↗</span>';
                if (deployFreq > 0.1 && failureRate < 0.15) return '<span class="text-yellow-500">→</span>';
                return '<span class="text-red-500">↘</span>';
                
            case 'capacity_planning':
                const cpuUtil = details.cpu_utilization_pct || 0;
                const memUtil = details.memory_utilization_pct || 0;
                const hasRequests = details.total_requested_cpu > 0 || details.total_requested_memory > 0;
                if (hasRequests && cpuUtil > 10 && cpuUtil < 70) return '<span class="text-green-500">↗</span>';
                if (hasRequests && (cpuUtil > 5 || memUtil > 5)) return '<span class="text-yellow-500">→</span>';
                return '<span class="text-red-500">↘</span>';
                
            case 'compliance_readiness':
                const passedControls = details.passed_controls || 0;
                const totalControls = details.total_controls || 1;
                const passRate = passedControls / totalControls;
                if (passRate >= 0.9) return '<span class="text-green-500">↗</span>';
                if (passRate >= 0.7) return '<span class="text-yellow-500">→</span>';
                return '<span class="text-red-500">↘</span>';
                
            case 'team_velocity':
                const releaseFreq = details.release_frequency_per_week || 0;
                const activeDeployments = details.active_deployments || 0;
                if (releaseFreq >= 1 && activeDeployments > 0) return '<span class="text-green-500">↗</span>';
                if (releaseFreq > 0 && activeDeployments > 0) return '<span class="text-yellow-500">→</span>';
                return '<span class="text-red-500">↘</span>';
                
            default:
                if (score >= 81) return '<span class="text-green-500">↗</span>';
                if (score >= 61) return '<span class="text-yellow-500">→</span>';
                return '<span class="text-red-500">↘</span>';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getClusterIdFromUrl() {
        const path = window.location.pathname;
        console.log('🔍 Current URL path processed');
        
        const match = path.match(/\/cluster\/([^\/]+)/);
        const clusterId = match ? match[1] : 'default';
        
        console.log('🔍 Cluster ID extracted');
        
        // If we're on the home page, try to get cluster from registered clusters
        if (clusterId === 'default' && path === '/') {
            console.log('⚠️ On home page - no specific cluster selected');
            console.log('💡 Please navigate to a specific cluster page to view Enterprise Metrics');
        }
        
        return clusterId;
    }

    async exportMetrics() {
        if (!this.currentData) {
            console.log('⚠️ No metrics data to export');
            return;
        }

        try {
            const exportData = {
                timestamp: new Date().toISOString(),
                cluster_id: this.getClusterIdFromUrl(),
                metrics: this.currentData
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `enterprise-metrics-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            console.log('📄 Enterprise metrics exported successfully');

        } catch (error) {
            console.error('❌ Failed to export metrics:', error);
        }
    }

    showRecommendationsModal() {
        if (!this.currentData || !this.currentData.data) {
            console.log('⚠️ No metrics data available for recommendations');
            return;
        }

        // Collect all recommendations from all metrics
        const allRecommendations = [];
        const metrics = this.currentData.data.operational_metrics || [];
        
        metrics.forEach(metric => {
            if (metric.recommendations && metric.recommendations.length > 0) {
                allRecommendations.push({
                    metric: metric.metric_name,
                    score: metric.score,
                    risk: metric.risk_level,
                    recommendations: metric.recommendations,
                    details: metric.details
                });
            }
        });

        // Create modal content
        const modalHtml = `
            <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" id="recommendations-modal">
                <div class="bg-gray-800 rounded-lg p-6 max-w-4xl max-h-96 overflow-y-auto m-4">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-xl font-bold text-white">📋 Enterprise Recommendations</h2>
                        <button onclick="document.getElementById('recommendations-modal').remove()" 
                                class="text-gray-400 hover:text-white text-2xl">&times;</button>
                    </div>
                    <div class="space-y-4">
                        ${allRecommendations.map(item => `
                            <div class="border border-gray-600 rounded-lg p-4">
                                <div class="flex items-center justify-between mb-2">
                                    <h3 class="font-semibold text-white">${item.metric}</h3>
                                    <span class="px-2 py-1 rounded text-xs font-medium 
                                        ${item.risk === 'LOW' ? 'bg-green-600 text-green-100' : 
                                          item.risk === 'MEDIUM' ? 'bg-yellow-600 text-yellow-100' : 
                                          'bg-red-600 text-red-100'}">
                                        Score: ${Math.round(item.score)} | ${item.risk} Risk
                                    </span>
                                </div>
                                <ul class="space-y-1">
                                    ${item.recommendations.map(rec => `
                                        <li class="text-gray-300 text-sm">• ${rec}</li>
                                    `).join('')}
                                </ul>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    showMetricDetails(metricKey, data) {
        const metricName = data.metric_name || metricKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const score = Math.round(data.score);
        const riskLevel = data.risk_level || 'UNKNOWN';
        
        // Get detailed insights based on metric type
        const insights = this.getMetricInsights(metricKey, data);
        
        // Create comprehensive modal content
        const modalHtml = `
            <div class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" id="metric-details-modal">
                <div class="bg-gray-800 rounded-xl p-8 max-w-6xl max-h-[90vh] overflow-y-auto m-4 border border-gray-600">
                    <div class="flex justify-between items-start mb-6">
                        <div>
                            <h2 class="text-2xl font-bold text-white mb-2">📊 ${metricName}</h2>
                            <p class="text-gray-400">Enterprise Operational Intelligence Report</p>
                        </div>
                        <button onclick="document.getElementById('metric-details-modal').remove()" 
                                class="text-gray-400 hover:text-white text-3xl font-bold leading-none">&times;</button>
                    </div>
                    
                    <!-- Score Header -->
                    <div class="bg-gradient-to-r from-gray-800 to-gray-900 rounded-lg p-6 mb-6 text-center border border-green-500">
                        <div class="text-6xl font-bold ${this.getScoreColor(score)} mb-2">${score}</div>
                        <div class="text-xl text-white mb-1">Overall Score</div>
                        <div class="inline-block px-4 py-2 rounded-full ${this.getRiskBadgeClass(riskLevel)} font-semibold">
                            ${riskLevel} RISK
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <!-- Key Insights -->
                        <div class="bg-gray-700 rounded-lg p-6">
                            <h3 class="font-semibold text-white mb-4 flex items-center">
                                <i class="fas fa-lightbulb text-yellow-400 mr-2"></i>
                                Key Insights
                            </h3>
                            <div class="space-y-3">
                                ${insights.map(insight => `
                                    <div class="flex items-start">
                                        <span class="text-green-400 mr-3 mt-1">•</span>
                                        <span class="text-gray-300">${insight}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        <!-- Action Items -->
                        <div class="bg-gray-700 rounded-lg p-6">
                            <h3 class="font-semibold text-white mb-4 flex items-center">
                                <i class="fas fa-tasks text-green-400 mr-2"></i>
                                Action Items
                            </h3>
                            <div class="space-y-3">
                                ${(data.recommendations || ['No specific recommendations available']).map((rec, index) => `
                                    <div class="flex items-start">
                                        <span class="flex-shrink-0 w-6 h-6 bg-green-600 rounded-full flex items-center justify-center text-xs font-bold text-white mr-3">
                                            ${index + 1}
                                        </span>
                                        <span class="text-gray-300">${rec}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        <!-- Technical Analysis -->
                        <div class="bg-gray-700 rounded-lg p-6 lg:col-span-2">
                            <h3 class="font-semibold text-white mb-4 flex items-center">
                                <i class="fas fa-cogs text-green-400 mr-2"></i>
                                Technical Analysis
                            </h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                ${this.formatDetailedBreakdown(data.details || data.key_details)}
                            </div>
                        </div>
                        
                        <!-- Benchmark Comparison -->
                        <div class="bg-gray-700 rounded-lg p-6 lg:col-span-2">
                            <h3 class="font-semibold text-white mb-4 flex items-center">
                                <i class="fas fa-chart-bar text-orange-400 mr-2"></i>
                                Industry Benchmark Comparison
                            </h3>
                            <div class="space-y-4">
                                ${this.getBenchmarkComparison(metricKey, score)}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Footer Actions -->
                    <div class="mt-8 pt-6 border-t border-gray-600 flex justify-between items-center">
                        <div class="text-sm text-gray-400">
                            📅 Last Updated: ${data.calculated_at || new Date().toLocaleString()}
                        </div>
                        <div class="space-x-3">
                            <button onclick="enterpriseMetricsManager.exportMetricReport('${metricKey}')" 
                                    class="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors">
                                <i class="fas fa-download mr-2"></i>Export Report
                            </button>
                            <button onclick="document.getElementById('metric-details-modal').remove()" 
                                    class="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Add keyboard event to close modal with Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const modal = document.getElementById('metric-details-modal');
                if (modal) modal.remove();
            }
        });
    }

    formatDetailedBreakdown(details) {
        if (!details) return '<span class="text-gray-400">No detailed data available</span>';
        
        // Check if details is a string (which causes character-by-character iteration)
        if (typeof details === 'string') {
            console.error('❌ Details is a string, expected object:', details);
            return `<span class="text-red-400">Invalid data format: ${details.substring(0, 50)}...</span>`;
        }
        
        // Ensure details is an object
        if (typeof details !== 'object' || details === null) {
            console.error('❌ Details is not an object:', typeof details, details);
            return '<span class="text-gray-400">Invalid data format</span>';
        }
        
        const formatValue = (key, value) => {
            // Skip empty or undefined values
            if (value === undefined || value === null || value === '' || 
                (Array.isArray(value) && value.length === 0)) {
                return '';
            }
            
            // Handle arrays specially
            if (Array.isArray(value)) {
                const cleanItems = value.filter(item => item && item.trim() && !item.endsWith('@'));
                if (cleanItems.length === 0) return '';
                return `
                    <div class="mb-2">
                        <div class="font-medium text-gray-300 mb-1">${key.replace(/_/g, ' ')}:</div>
                        <div class="pl-2 space-y-1">
                            ${cleanItems.map(item => `
                                <div class="text-gray-300 text-xs">• ${item}</div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            // Handle objects
            if (typeof value === 'object' && value !== null) {
                const validEntries = Object.entries(value).filter(([k, v]) => 
                    v !== undefined && v !== null && v !== '' && !String(v).endsWith('@')
                );
                if (validEntries.length === 0) return '';
                
                return `
                    <div class="mb-2">
                        <div class="font-medium text-gray-300 mb-1">${key.replace(/_/g, ' ')}:</div>
                        <div class="pl-2 space-y-1">
                            ${validEntries.map(([k, v]) => `
                                <div class="flex justify-between">
                                    <span class="text-gray-400">${k.replace(/_/g, ' ')}:</span>
                                    <span class="text-gray-300">${v}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            // Handle primitive values - skip if 0 or empty
            if (value === 0 && !['score', 'total_'].some(prefix => key.includes(prefix))) {
                return '';
            }
            
            // Format numbers nicely
            let displayValue = value;
            if (typeof value === 'number') {
                if (value > 0 && value < 1) {
                    displayValue = (value * 100).toFixed(1) + '%';
                } else if (value > 100) {
                    displayValue = value.toFixed(0);
                } else if (value % 1 !== 0) {
                    displayValue = value.toFixed(2);
                }
            }
            
            return `
                <div class="flex justify-between mb-1">
                    <span class="text-gray-400">${key.replace(/_/g, ' ')}:</span>
                    <span class="text-gray-300">${displayValue}</span>
                </div>
            `;
        };
        
        return Object.entries(details)
            .map(([key, value]) => formatValue(key, value))
            .filter(html => html.trim() !== '')
            .join('');
    }

    updateQuickActions(data) {
        const quickActionsContainer = document.getElementById('quick-actions-header');
        if (!quickActionsContainer) return;
        
        const metrics = data.operational_metrics || {};
        const actions = [];
        
        // Analyze real issues and create specific actions
        Object.entries(metrics).forEach(([key, metric]) => {
            const details = metric.details || {};
            const score = metric.score || 0;
            
            if (key === 'capacity_planning' && details.requested_cpu_cores === 0) {
                actions.push({
                    text: '🚨 Fix Resource Governance',
                    description: 'Add CPU/Memory requests to workloads',
                    urgency: 'critical',
                    onClick: () => this.showResourceGovernanceGuide()
                });
            }
            
            if (key === 'disaster_recovery_score' && (details.backup_solution_count || 0) === 0) {
                actions.push({
                    text: '🔒 Enable Backup Solution',
                    description: 'Deploy Velero for cluster backups',
                    urgency: 'high',
                    onClick: () => this.showBackupSetupGuide()
                });
            }
            
            if (key === 'operational_maturity' && (details.deployment_frequency_per_day || 0) < 0.1) {
                actions.push({
                    text: '⚡ Setup GitOps Pipeline',
                    description: 'Automate deployments with FluxCD/ArgoCD',
                    urgency: 'medium',
                    onClick: () => this.showGitOpsGuide()
                });
            }
            
            if (key === 'compliance_readiness' && (details.critical_issues || []).length > 0) {
                actions.push({
                    text: '🛡️ Fix Critical Security Issues',
                    description: `${details.critical_issues.length} CIS violations found`,
                    urgency: 'critical',
                    onClick: () => this.showComplianceGuide()
                });
            }
        });
        
        // Sort by urgency and show top 3
        const urgencyOrder = { critical: 0, high: 1, medium: 2, low: 3 };
        actions.sort((a, b) => urgencyOrder[a.urgency] - urgencyOrder[b.urgency]);
        
        // Add default actions if no critical issues found
        const defaultActionsHtml = actions.length === 0 ? `
            <button onclick="enterpriseMetricsManager.showRecommendationsModal()" 
                    class="w-full text-left px-3 py-2 bg-green-600 hover:bg-green-500 text-white text-sm rounded transition-colors">
                📋 View All Recommendations
            </button>
            <button onclick="enterpriseMetricsManager.exportMetrics()" 
                    class="w-full text-left px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors">
                📄 Export Report
            </button>
        ` : '';
        
        // Generate HTML for specific actions in header format
        const actionsHtml = actions.slice(0, 3).map((action, index) => `
            <button class="quick-action-btn px-3 py-2 rounded transition-colors text-xs font-medium
                           ${action.urgency === 'critical' ? 'bg-red-600 hover:bg-red-500' :
                             action.urgency === 'high' ? 'bg-orange-600 hover:bg-orange-500' :
                             'bg-green-600 hover:bg-green-500'} text-white"
                    data-action-index="${index}">
                ${action.text}
            </button>
        `).join('');
        
        // Keep Export button and add Quick Actions
        const exportBtn = quickActionsContainer.innerHTML;
        quickActionsContainer.innerHTML = actionsHtml + exportBtn;
        
        // Add event listeners to action buttons
        actions.forEach((action, index) => {
            const btn = quickActionsContainer.querySelector(`[data-action-index="${index}"]`);
            if (btn) {
                btn.addEventListener('click', action.onClick);
            }
        });
    }

    showResourceGovernanceGuide() {
        this.showGuideModal('🚨 Fix Resource Governance', `
            <div class="space-y-4 text-sm">
                <div class="bg-red-900 border border-red-600 rounded p-3">
                    <strong>CRITICAL:</strong> No CPU/Memory requests found in workloads
                </div>
                <div>
                    <h4 class="font-semibold text-white mb-2">Immediate Actions:</h4>
                    <ol class="list-decimal list-inside space-y-1 text-gray-300">
                        <li>Add resource requests to all Deployments and StatefulSets</li>
                        <li>Implement ResourceQuotas for each namespace</li>
                        <li>Create LimitRanges to enforce minimum requests</li>
                    </ol>
                </div>
                <div class="bg-gray-700 p-3 rounded">
                    <strong class="text-yellow-400">Expected Improvement:</strong><br>
                    Capacity Planning score: 100 → 75+ (proper resource tracking)
                </div>
            </div>
        `);
    }

    showBackupSetupGuide() {
        this.showGuideModal('🔒 Enable Backup Solution', `
            <div class="space-y-4 text-sm">
                <div class="bg-orange-900 border border-orange-600 rounded p-3">
                    <strong>HIGH PRIORITY:</strong> No backup solution detected
                </div>
                <div>
                    <h4 class="font-semibold text-white mb-2">Recommended Actions:</h4>
                    <ol class="list-decimal list-inside space-y-1 text-gray-300">
                        <li>Deploy Velero backup solution</li>
                        <li>Configure storage class snapshots</li>
                        <li>Set up scheduled backups for StatefulSets</li>
                    </ol>
                </div>
                <div class="bg-gray-700 p-3 rounded">
                    <strong class="text-yellow-400">Expected Improvement:</strong><br>
                    Disaster Recovery score: 46 → 80+ (with proper backups)
                </div>
            </div>
        `);
    }

    showGitOpsGuide() {
        this.showGuideModal('⚡ Setup GitOps Pipeline', `
            <div class="space-y-4 text-sm">
                <div class="bg-gray-800 border border-green-600 rounded p-3">
                    <strong>IMPROVEMENT:</strong> Manual deployments detected (0.00/day frequency)
                </div>
                <div>
                    <h4 class="font-semibold text-white mb-2">Automation Steps:</h4>
                    <ol class="list-decimal list-inside space-y-1 text-gray-300">
                        <li>Install FluxCD or ArgoCD</li>
                        <li>Connect Git repository for GitOps workflow</li>
                        <li>Configure automated deployment pipelines</li>
                    </ol>
                </div>
                <div class="bg-gray-700 p-3 rounded">
                    <strong class="text-yellow-400">Expected Improvement:</strong><br>
                    Operational Maturity: 68 → 85+ (DORA elite practices)
                </div>
            </div>
        `);
    }

    showComplianceGuide() {
        this.showGuideModal('🛡️ Fix Critical Security Issues', `
            <div class="space-y-4 text-sm">
                <div class="bg-red-900 border border-red-600 rounded p-3">
                    <strong>CRITICAL:</strong> CIS Kubernetes benchmark violations found
                </div>
                <div>
                    <h4 class="font-semibold text-white mb-2">Security Actions:</h4>
                    <ol class="list-decimal list-inside space-y-1 text-gray-300">
                        <li>Review cluster-admin role bindings</li>
                        <li>Implement network policies</li>
                        <li>Configure Pod Security Standards</li>
                    </ol>
                </div>
                <div class="bg-gray-700 p-3 rounded">
                    <strong class="text-yellow-400">Expected Improvement:</strong><br>
                    Compliance Readiness: 52 → 75+ (CIS benchmark compliance)
                </div>
            </div>
        `);
    }

    showGuideModal(title, content) {
        const modalHtml = `
            <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" id="guide-modal">
                <div class="bg-gray-800 rounded-lg p-6 max-w-2xl m-4">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-xl font-bold text-white">${title}</h2>
                        <button onclick="document.getElementById('guide-modal').remove()" 
                                class="text-gray-400 hover:text-white text-2xl">&times;</button>
                    </div>
                    ${content}
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    getMetricInsights(metricKey, data) {
        const insights = [];
        const details = data.details || data.key_details || {};
        const score = data.score;
        
        switch (metricKey) {
            case 'kubernetes_upgrade_readiness':
                if (details.deprecated_api_count > 0) {
                    insights.push(`⚠️ Found ${details.deprecated_api_count} deprecated APIs that need updating before upgrade`);
                }
                if (details.version_gap > 0) {
                    insights.push(`📅 Cluster is ${details.version_gap} versions behind the latest Kubernetes release`);
                }
                if (score >= 80) {
                    insights.push(`✅ Cluster is ready for upgrade with minimal risk`);
                } else {
                    insights.push(`🔧 Preparation needed before upgrading to ensure compatibility`);
                }
                break;
                
            case 'disaster_recovery_score':
                if (details.backup_solution_count === 0) {
                    insights.push(`🚨 No backup solutions detected - critical data loss risk`);
                } else {
                    insights.push(`💾 ${details.backup_solution_count} backup solution(s) configured`);
                }
                if (details.snapshot_coverage_pct < 50) {
                    insights.push(`📸 Only ${Math.round(details.snapshot_coverage_pct)}% of persistent volumes have snapshots`);
                }
                insights.push(`⏱️ Estimated recovery time: ${details.estimated_rto_hours || 'unknown'} hours`);
                break;
                
            case 'capacity_planning':
                const cpuUtil = details.cpu_utilization_pct || 0;
                const memUtil = details.memory_utilization_pct || 0;
                if (cpuUtil < 20) {
                    insights.push(`💰 CPU utilization is low - potential cost savings available`);
                } else if (cpuUtil > 80) {
                    insights.push(`⚡ CPU utilization is high - scaling or optimization needed`);
                }
                if (details.requested_cpu_cores === 0) {
                    insights.push(`🚨 No resource requests found - cluster lacks resource governance`);
                }
                break;
                
            case 'compliance_readiness':
                const criticalIssues = details.critical_issues || [];
                if (criticalIssues.length > 0) {
                    insights.push(`🛡️ ${criticalIssues.length} critical security issues require immediate attention`);
                }
                const passRate = details.passed_controls / (details.total_controls || 1);
                insights.push(`📋 ${Math.round(passRate * 100)}% of CIS controls are passing`);
                break;
                
            case 'operational_maturity':
                const deployFreq = details.deployment_frequency_per_day || 0;
                if (deployFreq < 0.1) {
                    insights.push(`🐌 Low deployment frequency (${deployFreq.toFixed(2)}/day) indicates manual processes`);
                } else {
                    insights.push(`🚀 Good deployment frequency (${deployFreq.toFixed(2)}/day) shows automated CI/CD`);
                }
                const failureRate = details.change_failure_rate || 0;
                insights.push(`📈 Change failure rate: ${(failureRate * 100).toFixed(1)}%`);
                break;
                
            case 'team_velocity':
                const releaseFreq = details.release_frequency_per_week || 0;
                insights.push(`📦 Release frequency: ${releaseFreq.toFixed(1)} releases per week`);
                const activeDeployments = details.active_deployments || 0;
                const stableDeployments = details.stable_deployments || 0;
                if (activeDeployments > 0) {
                    insights.push(`📊 ${stableDeployments}/${activeDeployments} deployments are stable`);
                }
                break;
                
            default:
                insights.push(`📊 Current score: ${score}/100`);
                insights.push(`🎯 Benchmark: Industry standards for ${metricKey.replace(/_/g, ' ')}`);
        }
        
        return insights.length > 0 ? insights : ['No specific insights available for this metric'];
    }

    getRiskBadgeClass(riskLevel) {
        switch (riskLevel) {
            case 'LOW': return 'bg-green-600 text-green-100';
            case 'MEDIUM': return 'bg-yellow-600 text-yellow-100';
            case 'HIGH': return 'bg-orange-600 text-orange-100';
            case 'CRITICAL': return 'bg-red-600 text-red-100';
            default: return 'bg-gray-600 text-gray-100';
        }
    }

    getBenchmarkComparison(metricKey, score) {
        const benchmarks = {
            'kubernetes_upgrade_readiness': [
                { level: 'Industry Leader', threshold: 90, description: 'Top 10% of organizations' },
                { level: 'Above Average', threshold: 75, description: 'Better than 70% of organizations' },
                { level: 'Average', threshold: 60, description: 'Typical enterprise performance' },
                { level: 'Below Average', threshold: 40, description: 'Improvement needed' },
                { level: 'Poor', threshold: 0, description: 'Significant risks present' }
            ],
            'disaster_recovery_score': [
                { level: 'Enterprise Grade', threshold: 85, description: 'Mission-critical ready' },
                { level: 'Production Ready', threshold: 70, description: 'Good recovery capabilities' },
                { level: 'Basic Protection', threshold: 50, description: 'Minimal recovery setup' },
                { level: 'High Risk', threshold: 30, description: 'Inadequate protection' },
                { level: 'Critical Risk', threshold: 0, description: 'No disaster recovery' }
            ],
            'operational_maturity': [
                { level: 'DevOps Elite', threshold: 85, description: 'Top-performing teams' },
                { level: 'High Performing', threshold: 70, description: 'Strong DevOps practices' },
                { level: 'Medium Performing', threshold: 50, description: 'Some automation in place' },
                { level: 'Low Performing', threshold: 30, description: 'Mostly manual processes' },
                { level: 'Ad-hoc', threshold: 0, description: 'No formal processes' }
            ]
        };
        
        const metricBenchmarks = benchmarks[metricKey] || benchmarks['operational_maturity'];
        const currentLevel = metricBenchmarks.find(b => score >= b.threshold) || metricBenchmarks[metricBenchmarks.length - 1];
        
        return metricBenchmarks.map(benchmark => {
            const isCurrentLevel = benchmark === currentLevel;
            const barWidth = Math.min(100, (score / benchmark.threshold) * 100);
            
            return `
                <div class="flex items-center justify-between p-3 rounded-lg ${isCurrentLevel ? 'bg-gray-800 border border-green-500' : 'bg-gray-600'}">
                    <div class="flex-grow">
                        <div class="flex justify-between items-center mb-1">
                            <span class="font-semibold text-white">${benchmark.level}</span>
                            <span class="text-sm ${isCurrentLevel ? 'text-green-300' : 'text-gray-300'}">${benchmark.threshold}+</span>
                        </div>
                        <div class="text-xs text-gray-300">${benchmark.description}</div>
                        ${isCurrentLevel ? '<div class="text-xs text-green-300 mt-1">👈 Your current level</div>' : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    exportMetricReport(metricKey) {
        // Export functionality disabled to prevent data exposure
        console.log('📊 Metric report export requested but disabled for security:', metricKey);
        alert('Metric export has been disabled for security purposes');
    }

    loadDemoData() {
        console.log('🎭 Loading demo enterprise metrics...');
        
        const demoData = {
            enterprise_maturity: {
                score: 68,
                level: 'INTERMEDIATE',
                timestamp: new Date().toISOString()
            },
            operational_metrics: {
                kubernetes_upgrade_readiness: {
                    metric_name: 'Kubernetes Upgrade Readiness',
                    score: 75,
                    risk_level: 'MEDIUM',
                    key_details: {
                        current_version: 'v1.28.0',
                        latest_version: 'v1.31.0',
                        version_gap: 3,
                        deprecated_api_count: 2,
                        upgrade_blockers: ['Deprecated networking.k8s.io/v1beta1 Ingress', 'Old HPA apiVersion']
                    },
                    details: {
                        current_version: 'v1.28.0',
                        latest_version: 'v1.31.0',
                        version_gap: 3,
                        deprecated_api_count: 2,
                        upgrade_blockers: ['Deprecated networking.k8s.io/v1beta1 Ingress', 'Old HPA apiVersion']
                    },
                    recommendations: [
                        'Update Ingress resources to use networking.k8s.io/v1',
                        'Migrate HorizontalPodAutoscaler to autoscaling/v2',
                        'Test upgrade in staging environment first'
                    ],
                    benchmark_source: 'CIS Kubernetes Benchmark',
                    calculated_at: new Date().toISOString()
                },
                disaster_recovery_score: {
                    metric_name: 'Disaster Recovery Score',
                    score: 46,
                    risk_level: 'HIGH',
                    key_details: {
                        backup_solution_count: 0,
                        snapshot_coverage_pct: 0,
                        estimated_rto_hours: 24,
                        multi_az_deployment: false
                    },
                    details: {
                        backup_solution_count: 0,
                        snapshot_coverage_pct: 0,
                        estimated_rto_hours: 24,
                        multi_az_deployment: false,
                        backup_solutions: [],
                        persistent_volumes: 5,
                        critical_data_protection: 'none'
                    },
                    recommendations: [
                        'Deploy Velero for cluster backup and restore',
                        'Configure automated snapshots for persistent volumes',
                        'Implement multi-AZ deployment for high availability',
                        'Test disaster recovery procedures monthly'
                    ],
                    benchmark_source: 'NIST Cybersecurity Framework',
                    calculated_at: new Date().toISOString()
                },
                operational_maturity: {
                    metric_name: 'Operational Maturity',
                    score: 68,
                    risk_level: 'MEDIUM',
                    key_details: {
                        deployment_frequency_per_day: 0.3,
                        change_failure_rate: 0.15,
                        lead_time_hours: 48,
                        mttr_hours: 4
                    },
                    details: {
                        deployment_frequency_per_day: 0.3,
                        change_failure_rate: 0.15,
                        lead_time_hours: 48,
                        mttr_hours: 4,
                        gitops_tools: ['FluxCD'],
                        monitoring_tools: ['Prometheus', 'Grafana'],
                        automation_coverage: 70
                    },
                    recommendations: [
                        'Increase deployment frequency to improve DORA metrics',
                        'Implement automated testing to reduce change failure rate',
                        'Add chaos engineering practices',
                        'Set up automated rollback procedures'
                    ],
                    benchmark_source: 'DORA State of DevOps Report',
                    calculated_at: new Date().toISOString()
                },
                capacity_planning: {
                    metric_name: 'Capacity Planning',
                    score: 34,
                    risk_level: 'HIGH',
                    key_details: {
                        cpu_utilization_pct: 0,
                        memory_utilization_pct: 0,
                        requested_cpu_cores: 0,
                        total_cpu_cores: 12
                    },
                    details: {
                        cpu_utilization_pct: 0,
                        memory_utilization_pct: 0,
                        requested_cpu_cores: 0,
                        total_cpu_cores: 12,
                        total_requested_memory: 0,
                        total_memory_gb: 48,
                        workloads_without_requests: 15,
                        resource_governance: 'missing'
                    },
                    recommendations: [
                        'Add resource requests to all Deployments and StatefulSets',
                        'Implement ResourceQuotas for each namespace',
                        'Set up Vertical Pod Autoscaler for optimization',
                        'Create monitoring alerts for resource exhaustion'
                    ],
                    benchmark_source: 'Kubernetes Resource Management Best Practices',
                    calculated_at: new Date().toISOString()
                },
                compliance_readiness: {
                    metric_name: 'Compliance Readiness',
                    score: 52,
                    risk_level: 'MEDIUM',
                    key_details: {
                        passed_controls: 26,
                        total_controls: 50,
                        critical_issues: ['Privileged containers detected', 'Missing network policies']
                    },
                    details: {
                        passed_controls: 26,
                        total_controls: 50,
                        critical_issues: ['Privileged containers detected', 'Missing network policies'],
                        compliance_frameworks: ['CIS Kubernetes', 'PCI DSS'],
                        pod_security_standards: 'baseline',
                        network_policies_coverage: 30
                    },
                    recommendations: [
                        'Remove privileged containers or add security contexts',
                        'Implement network policies for all namespaces',
                        'Upgrade to restricted Pod Security Standards',
                        'Enable audit logging for compliance tracking'
                    ],
                    benchmark_source: 'CIS Kubernetes Benchmark v1.23',
                    calculated_at: new Date().toISOString()
                },
                team_velocity: {
                    metric_name: 'Team Velocity',
                    score: 71,
                    risk_level: 'MEDIUM',
                    key_details: {
                        release_frequency_per_week: 1.2,
                        active_deployments: 25,
                        stable_deployments: 20
                    },
                    details: {
                        release_frequency_per_week: 1.2,
                        active_deployments: 25,
                        stable_deployments: 20,
                        deployment_success_rate: 0.8,
                        average_lead_time_days: 3,
                        team_productivity_score: 75
                    },
                    recommendations: [
                        'Improve deployment success rate through better testing',
                        'Reduce lead time with more automation',
                        'Implement feature flags for safer releases',
                        'Add deployment health checks and monitoring'
                    ],
                    benchmark_source: 'DORA Metrics Benchmarks',
                    calculated_at: new Date().toISOString()
                }
            },
            action_items: [
                '🚨 CRITICAL: Fix 2 security violations: Privileged containers detected, Missing network policies',
                '🚨 CRITICAL: Add resource requests to all workloads - no resource governance detected',
                '🔴 HIGH: Deploy backup solution (Velero) - no data protection found',
                '🟡 MEDIUM: Update 2 deprecated APIs before Kubernetes upgrade',
                '🟡 MEDIUM: Implement GitOps/CI-CD pipeline - manual deployments detected'
            ]
        };

        this.currentData = demoData;
        this.renderMetrics(demoData);
        this.hideLoading();
        this.showMainContent();
        
        console.log('🎭 Demo enterprise metrics loaded successfully');
    }

    showLoading() {
        const loadingEl = document.getElementById('enterprise-loading');
        if (loadingEl) loadingEl.classList.remove('hidden');
    }

    hideLoading() {
        const loadingEl = document.getElementById('enterprise-loading');
        if (loadingEl) loadingEl.classList.add('hidden');
    }

    showError(message) {
        const errorEl = document.getElementById('enterprise-error');
        const errorMsgEl = document.getElementById('enterprise-error-message');
        
        if (errorEl) errorEl.classList.remove('hidden');
        if (errorMsgEl) {
            errorMsgEl.innerHTML = `
                <div class="mb-2">${message}</div>
                <div class="text-sm text-gray-500 mt-2">
                    <strong>Troubleshooting:</strong>
                    <ul class="list-disc list-inside mt-1 space-y-1">
                        <li>Ensure the cluster is accessible and kubectl commands work</li>
                        <li>Check that analysis has been run for this cluster first</li>
                        <li>Verify Azure subscription and resource group access</li>
                        <li>Check browser console for detailed error information</li>
                    </ul>
                </div>
            `;
        }
    }

    hideError() {
        const errorEl = document.getElementById('enterprise-error');
        if (errorEl) errorEl.classList.add('hidden');
    }

    showLockedMessage() {
        this.hideLoading();
        this.showError('Enterprise Metrics are available with Enterprise tier. Please upgrade your license to access these features.');
    }

    showMainContent() {
        const contentEl = document.getElementById('enterprise-main-content');
        if (contentEl) contentEl.classList.remove('hidden');
    }

    hideMainContent() {
        const contentEl = document.getElementById('enterprise-main-content');
        if (contentEl) contentEl.classList.add('hidden');
    }

    // Auto-refresh functionality
    startAutoRefresh(intervalMinutes = 15) {
        this.stopAutoRefresh();
        this.refreshInterval = setInterval(() => {
            if (this.initialized) {
                console.log('🔄 Auto-refreshing enterprise metrics...');
                this.loadEnterpriseMetrics();
            }
        }, intervalMinutes * 60 * 1000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Initialize enterprise metrics manager
let enterpriseMetricsManager;

document.addEventListener('DOMContentLoaded', () => {
    enterpriseMetricsManager = new EnterpriseMetricsManager();
    
    // Bind tab click handler with proper context
    const enterpriseTab = document.querySelector('[onclick*="enterprise-metrics"]');
    if (enterpriseTab) {
        enterpriseTab.addEventListener('click', () => {
            setTimeout(() => {
                if (!enterpriseMetricsManager.initialized) {
                    enterpriseMetricsManager.loadEnterpriseMetrics();
                    enterpriseMetricsManager.initialized = true;
                }
            }, 200);
        });
    }
    
    console.log('🏢 Enterprise Metrics Manager ready');
});

// Export for global access
window.EnterpriseMetricsManager = EnterpriseMetricsManager;
window.enterpriseMetricsManager = enterpriseMetricsManager;
window.enterpriseMetrics = enterpriseMetricsManager; // Alias for onclick handlers