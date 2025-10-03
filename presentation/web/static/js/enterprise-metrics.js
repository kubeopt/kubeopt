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
            
            this.showLockedMessage();
            return;
        }
        
        this.showLoading();
        this.hideError();
        this.hideMainContent();

        try {
            // Get cluster information from current page context
            const clusterId = this.getClusterIdFromUrl();
            console.log('🔍 ENTERPRISE METRICS: Loading metrics for cluster:', clusterId);
            console.log('🔍 ENTERPRISE METRICS: Current page URL:', window.location.href);
            
            // Check if we have a valid cluster ID
            if (!clusterId) {
                throw new Error('No cluster found. Please navigate to a specific cluster page or ensure clusters are loaded.');
            }
            
            console.log('🚀 ENTERPRISE METRICS: Making API call for cluster:', clusterId);
            const response = await fetch(`/api/enterprise-metrics?cluster_id=${clusterId}`, {
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
            
            

        } catch (error) {
            console.error('❌ Failed to load enterprise metrics:', error);
            
            // Show the real error with detailed troubleshooting
            let errorMessage = `Failed to load enterprise metrics: ${error.message}`;
            
            this.showError(errorMessage);
            this.hideLoading();
        }
    }

    renderMetrics(data) {
        if (!data) {
            console.log('📊 No enterprise metrics data available - showing empty state');
            this.showNoDataMessage();
            return;
        }

        console.log('🎨 Starting to render enterprise metrics...');
        console.log('🔍 CLUSTER-SPECIFIC VERIFICATION: Rendering metrics for cluster:', this.getClusterIdFromUrl());
        console.log('🔍 CLUSTER-SPECIFIC VERIFICATION: Maturity score:', data.enterprise_maturity?.score);
        console.log('🔍 CLUSTER-SPECIFIC VERIFICATION: Metrics count:', data.operational_metrics?.length || 0);

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
        
        const levelEl = document.getElementById('maturity-level');
        const scoreEl = document.getElementById('maturity-score');
        const progressEl = document.getElementById('maturity-progress');

        if (levelEl) levelEl.textContent = maturity.level;
        if (scoreEl) scoreEl.textContent = Math.round(maturity.score);
        if (progressEl) progressEl.style.width = `${maturity.score}%`;

        // Update level styling based on maturity
        if (levelEl) {
            levelEl.className = 'text-2xl font-bold mt-2 ' + this.getMaturityLevelColor(maturity.level);
        }
    }

    updateIndividualMetrics(metrics) {
        for (const [metricKey, metricData] of Object.entries(metrics)) {
            this.updateMetricCard(metricKey, metricData);
        }
    }

    updateMetricCard(metricKey, data) {
        
        const card = document.querySelector(`[data-metric="${metricKey}"]`);
        
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
        console.log('🔍 Current URL path:', path);
        
        // FIXED: Check for cluster context set by unified dashboard first
        if (window.currentClusterId) {
            console.log('✅ Found cluster ID from window context:', window.currentClusterId);
            console.log('🔍 CLUSTER-SPECIFIC METRICS: Loading enterprise metrics for cluster:', window.currentClusterId);
            return window.currentClusterId;
        }
        
        if (window.clusterInfo && window.clusterInfo.id) {
            console.log('✅ Found cluster ID from clusterInfo:', window.clusterInfo.id);
            return window.clusterInfo.id;
        }
        
        // Try to get cluster ID from URL path (for individual cluster pages)
        const match = path.match(/\/cluster\/([^\/]+)/);
        if (match) {
            console.log('✅ Found cluster ID from URL:', match[1]);
            return match[1];
        }
        
        // If we're on clusters portfolio page, try to get from selected cluster
        const selectedCluster = document.querySelector('.cluster-card.selected [data-cluster-id]');
        if (selectedCluster) {
            const clusterId = selectedCluster.getAttribute('data-cluster-id');
            console.log('✅ Found cluster ID from selected card:', clusterId);
            return clusterId;
        }
        
        // LAST RESORT: Try to get first available cluster from the page
        const firstCluster = document.querySelector('[data-cluster-id]');
        if (firstCluster) {
            const clusterId = firstCluster.getAttribute('data-cluster-id');
            console.log('⚠️ Using first available cluster ID as fallback:', clusterId);
            return clusterId;
        }
        
        // If no cluster found, show error
        console.log('❌ No cluster ID found');
        return null;
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
                <div class="bg-white rounded-lg p-5 max-w-3xl max-h-[80vh] overflow-y-auto m-4 shadow-xl" style="border: 1px solid var(--border-color);">
                    <div class="flex justify-between items-center mb-3">
                        <h2 class="text-lg font-bold" style="color: var(--text-primary);">📋 Enterprise Recommendations</h2>
                        <button onclick="document.getElementById('recommendations-modal').remove()" 
                                class="text-xl" style="color: var(--text-secondary); transition: color 0.2s ease;" onmouseover="this.style.color='var(--text-primary)'" onmouseout="this.style.color='var(--text-secondary)'">&times;</button>
                    </div>
                    <div class="space-y-3">
                        ${allRecommendations.map(item => `
                            <div class="rounded-lg p-3" style="border: 1px solid var(--border-color); background: var(--bg-white);">
                                <div class="flex items-center justify-between mb-2">
                                    <h3 class="font-medium text-sm" style="color: var(--text-primary);">${item.metric}</h3>
                                    <span class="px-2 py-1 rounded text-xs font-medium" style="
                                        background: ${item.risk === 'LOW' ? 'var(--primary-green)' : 
                                                   item.risk === 'MEDIUM' ? '#f59e0b' : '#dc2626'};
                                        color: white;">
                                        ${Math.round(item.score)} | ${item.risk}
                                    </span>
                                </div>
                                <ul class="space-y-1">
                                    ${item.recommendations.slice(0, 3).map(rec => `
                                        <li class="text-xs" style="color: var(--text-primary);">• ${rec}</li>
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
                <div class="bg-white rounded-xl p-6 max-w-4xl max-h-[85vh] overflow-y-auto m-4 shadow-2xl" style="border: 1px solid var(--border-color);">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <h2 class="text-xl font-bold mb-1" style="color: var(--text-primary);">📊 ${metricName}</h2>
                            <p class="text-sm" style="color: var(--text-secondary);">Enterprise Intelligence Report</p>
                        </div>
                        <button onclick="document.getElementById('metric-details-modal').remove()" 
                                class="text-2xl font-bold leading-none" style="color: var(--text-secondary); transition: color 0.2s ease;" onmouseover="this.style.color='var(--text-primary)'" onmouseout="this.style.color='var(--text-secondary)'">&times;</button>
                    </div>
                    
                    <!-- Score Header -->
                    <div class="rounded-lg p-4 mb-4 text-center" style="background: var(--bg-primary); border: 1px solid var(--primary-green);">
                        <div class="text-4xl font-bold ${this.getScoreColor(score)} mb-1">${score}</div>
                        <div class="text-lg mb-1" style="color: var(--text-primary);">Overall Score</div>
                        <div class="inline-block px-3 py-1 rounded-full ${this.getRiskBadgeClass(riskLevel)} font-medium text-sm">
                            ${riskLevel} RISK
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <!-- Key Insights -->
                        <div class="rounded-lg p-4" style="background: var(--bg-white); border: 1px solid var(--border-color);">
                            <h3 class="font-semibold mb-3 flex items-center text-sm" style="color: var(--text-primary);">
                                <i class="fas fa-lightbulb mr-2" style="color: var(--primary-green);"></i>
                                Key Insights
                            </h3>
                            <div class="space-y-2">
                                ${insights.slice(0, 4).map(insight => `
                                    <div class="flex items-start">
                                        <span class="mr-2 mt-1 text-xs" style="color: var(--primary-green);">•</span>
                                        <span class="text-sm" style="color: var(--text-primary);">${insight}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        <!-- Action Items -->
                        <div class="rounded-lg p-4" style="background: var(--bg-white); border: 1px solid var(--border-color);">
                            <h3 class="font-semibold mb-3 flex items-center text-sm" style="color: var(--text-primary);">
                                <i class="fas fa-tasks mr-2" style="color: var(--primary-green);"></i>
                                Action Items
                            </h3>
                            <div class="space-y-2">
                                ${(data.recommendations || ['No specific recommendations available']).slice(0, 3).map((rec, index) => `
                                    <div class="flex items-start">
                                        <span class="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white mr-2" style="background: var(--primary-green);">
                                            ${index + 1}
                                        </span>
                                        <span class="text-sm" style="color: var(--text-primary);">${rec}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        <!-- Technical Analysis -->
                        <div class="rounded-lg p-4 lg:col-span-2" style="background: var(--bg-white); border: 1px solid var(--border-color);">
                            <h3 class="font-semibold mb-3 flex items-center text-sm" style="color: var(--text-primary);">
                                <i class="fas fa-cogs mr-2" style="color: var(--primary-green);"></i>
                                Technical Details
                            </h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                ${this.formatDetailedBreakdown(data.details || data.key_details)}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Footer Actions -->
                    <div class="mt-4 pt-3 flex justify-between items-center" style="border-top: 1px solid var(--border-color);">
                        <div class="text-xs" style="color: var(--text-secondary);">
                            📅 Updated: ${data.calculated_at || new Date().toLocaleString()}
                        </div>
                        <div class="space-x-2">
                            <button onclick="document.getElementById('metric-details-modal').remove()" 
                                    class="px-3 py-1.5 rounded text-sm transition-colors" style="background: var(--bg-primary); color: var(--text-primary); border: 1px solid var(--border-color);" onmouseover="this.style.background='var(--primary-green)'; this.style.color='white'" onmouseout="this.style.background='var(--bg-primary)'; this.style.color='var(--text-primary)'">
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
                    <strong>IMPROVEMENT:</strong> Deployment automation can be enhanced with GitOps
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
                } else if (details.backup_solution_count && !isNaN(details.backup_solution_count)) {
                    insights.push(`💾 ${details.backup_solution_count} backup solution(s) configured`);
                } else {
                    insights.push(`💾 Backup configuration analysis in progress`);
                }
                if (details.snapshot_coverage_pct < 50) {
                    insights.push(`📸 Only ${Math.round(details.snapshot_coverage_pct)}% of persistent volumes have snapshots`);
                }
                if (details.estimated_rto_hours) {
                    insights.push(`⏱️ Estimated recovery time: ${details.estimated_rto_hours} hours`);
                } else {
                    insights.push(`⏱️ Recovery time assessment requires backup configuration`);
                }
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
                
                
            case 'operational_maturity':
                const deployFreq = details.deployment_frequency_per_day;
                if (deployFreq !== undefined && !isNaN(deployFreq)) {
                    if (deployFreq < 0.1) {
                        insights.push(`🐌 Low deployment frequency (${deployFreq.toFixed(2)}/day) indicates manual processes`);
                    } else {
                        insights.push(`🚀 Good deployment frequency (${deployFreq.toFixed(2)}/day) shows automated CI/CD`);
                    }
                } else {
                    insights.push(`🔧 Deployment automation analysis based on HPA coverage and monitoring`);
                }
                const failureRate = details.change_failure_rate;
                if (failureRate !== undefined && !isNaN(failureRate)) {
                    insights.push(`📈 Change failure rate: ${(failureRate * 100).toFixed(1)}%`);
                }
                break;
                
            case 'team_velocity':
                const releaseFreq = details.release_frequency_per_week;
                if (releaseFreq !== undefined && !isNaN(releaseFreq)) {
                    insights.push(`📦 Release frequency: ${releaseFreq.toFixed(1)} releases per week`);
                } else {
                    insights.push(`📦 Team velocity based on cost optimization efficiency and deployment stability`);
                }
                const activeDeployments = details.active_deployments;
                const stableDeployments = details.stable_deployments;
                if (activeDeployments > 0 && stableDeployments !== undefined) {
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
        alert('Metric export has been disabled for security purposes');
    }


    showLoading() {
        const loadingEl = document.getElementById('enterprise-loading');
        if (loadingEl) loadingEl.classList.remove('hidden');
    }

    hideLoading() {
        const loadingEl = document.getElementById('enterprise-loading');
        if (loadingEl) loadingEl.classList.add('hidden');
    }

    showNoDataMessage() {
        // Clear all existing content and show no-data message
        const container = document.getElementById('enterprise-metrics-content');
        if (container) {
            container.innerHTML = `
                <div class="no-data-message text-center py-5">
                    <div class="mb-4">
                        <i class="fas fa-chart-line fa-3x text-muted"></i>
                    </div>
                    <h4 class="text-muted">No Enterprise Metrics Data</h4>
                    <p class="text-muted">
                        No analysis data is available for this cluster yet.
                        <br>
                        Please run a cluster analysis to populate enterprise metrics.
                    </p>
                    <button class="btn btn-primary mt-3" onclick="window.location.reload()">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                </div>
            `;
        }
        this.hideLoading();
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
    // Make it globally accessible for showContent function
    window.enterpriseMetricsManager = enterpriseMetricsManager;
    
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