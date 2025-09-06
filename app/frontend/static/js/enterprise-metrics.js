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
        
        this.showLoading();
        this.hideError();
        this.hideMainContent();

        try {
            // Get cluster information from current page context
            const clusterId = this.getClusterIdFromUrl();
            const response = await fetch(`/api/enterprise-metrics?cluster_id=${clusterId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.status === 'error') {
                throw new Error(result.message || 'Failed to load enterprise metrics');
            }

            this.currentData = result.data;
            this.renderMetrics(result.data);
            this.hideLoading();
            this.showMainContent();

            console.log('✅ Enterprise metrics loaded successfully');

        } catch (error) {
            console.error('❌ Failed to load enterprise metrics:', error);
            this.showError(error.message);
            this.hideLoading();
        }
    }

    renderMetrics(data) {
        if (!data) return;

        // Update overall maturity
        this.updateMaturityOverview(data.enterprise_maturity);

        // Update individual metrics
        this.updateIndividualMetrics(data.operational_metrics);

        // Update action items
        this.updateActionItems(data.action_items || []);

        // Update timestamp
        this.updateTimestamp(data.enterprise_maturity.timestamp);
        
        // Update Quick Actions with specific issues
        this.updateQuickActions(data);
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
        if (!card) return;

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
        if (detailsEl && data.key_details) {
            const detailsHtml = this.formatMetricDetails(data.key_details);
            const viewReportLink = `
                <div class="mt-3 pt-2 border-t border-gray-600">
                    <button class="view-metric-report text-blue-400 hover:text-blue-300 text-xs font-medium" 
                            data-metric-key="${metricKey}">
                        📄 View Full Report →
                    </button>
                </div>
            `;
            detailsEl.innerHTML = detailsHtml + viewReportLink;
            
            // Add event listener to the button
            const reportBtn = detailsEl.querySelector('.view-metric-report');
            if (reportBtn) {
                reportBtn.addEventListener('click', () => this.showMetricDetails(metricKey, data));
            }
        }
    }

    formatMetricDetails(details) {
        const items = [];
        
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
        if (details.change_failure_rate !== undefined) {
            items.push(`Failure Rate: ${(details.change_failure_rate * 100).toFixed(1)}%`);
        }
        if (details.cpu_utilization_pct !== undefined) {
            items.push(`CPU Usage: ${details.cpu_utilization_pct.toFixed(1)}%`);
        }
        if (details.memory_utilization_pct !== undefined) {
            items.push(`Memory Usage: ${details.memory_utilization_pct.toFixed(1)}%`);
        }

        return items.map(item => `<div>${item}</div>`).join('');
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
                <div class="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-xs font-bold text-white">
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
            case 'ADVANCED': return 'text-blue-500';
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
        const match = path.match(/\/cluster\/([^\/]+)/);
        return match ? match[1] : 'default';
    }

    async exportMetrics() {
        if (!this.currentData) {
            console.warn('⚠️ No metrics data to export');
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
            console.warn('⚠️ No metrics data available for recommendations');
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
        
        // Create detailed modal content
        const modalHtml = `
            <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" id="metric-details-modal">
                <div class="bg-gray-800 rounded-lg p-6 max-w-4xl max-h-96 overflow-y-auto m-4">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-xl font-bold text-white">📊 ${metricName} - Detailed Report</h2>
                        <button onclick="document.getElementById('metric-details-modal').remove()" 
                                class="text-gray-400 hover:text-white text-2xl">&times;</button>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <!-- Score Summary -->
                        <div class="bg-gray-700 rounded-lg p-4">
                            <h3 class="font-semibold text-white mb-3">📈 Score Summary</h3>
                            <div class="space-y-2 text-sm">
                                <div class="flex justify-between">
                                    <span class="text-gray-300">Overall Score:</span>
                                    <span class="font-bold ${this.getRiskLevelColor(data.risk_level)}">${Math.round(data.score)}/100</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-300">Risk Level:</span>
                                    <span class="font-bold ${this.getRiskLevelColor(data.risk_level)}">${data.risk_level}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-300">Benchmark:</span>
                                    <span class="text-gray-300">${data.benchmark_source || 'Industry Standards'}</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Recommendations -->
                        <div class="bg-gray-700 rounded-lg p-4">
                            <h3 class="font-semibold text-white mb-3">💡 Recommendations</h3>
                            <div class="space-y-2">
                                ${(data.recommendations || []).map(rec => `
                                    <div class="text-sm text-gray-300 flex items-start">
                                        <span class="text-blue-400 mr-2">•</span>
                                        <span>${rec}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        <!-- Technical Details -->
                        <div class="bg-gray-700 rounded-lg p-4 md:col-span-2">
                            <h3 class="font-semibold text-white mb-3">🔧 Technical Details</h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
                                ${this.formatDetailedBreakdown(data.details)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    formatDetailedBreakdown(details) {
        if (!details) return '<span class="text-gray-400">No detailed data available</span>';
        
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
                    class="w-full text-left px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded transition-colors">
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
                             'bg-blue-600 hover:bg-blue-500'} text-white"
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
                <div class="bg-blue-900 border border-blue-600 rounded p-3">
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
        if (errorMsgEl) errorMsgEl.textContent = message;
    }

    hideError() {
        const errorEl = document.getElementById('enterprise-error');
        if (errorEl) errorEl.classList.add('hidden');
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