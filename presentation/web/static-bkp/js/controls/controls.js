/**
 * Project Controls Manager - Clean Dashboard Version
 */

class ProjectControlsManager {
    constructor() {
        this.clusterId = null;
        this.frameworkData = null;
        this.isLoading = false;
        this.charts = {};
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        document.getElementById('refresh-controls')?.addEventListener('click', () => {
            this.loadProjectControls();
        });

        document.getElementById('export-controls')?.addEventListener('click', () => {
            this.exportFrameworkData();
        });
    }

    async loadProjectControls(clusterId = null) {
        if (clusterId) {
            this.clusterId = clusterId;
        }

        if (!this.clusterId) {
            this.clusterId = this.extractClusterIdFromUrl();
        }

        if (!this.clusterId) {
            this.showError('No cluster ID available. Please select a cluster first.');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`/api/project-controls?cluster_id=${this.clusterId}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load project controls: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.status === 'error') {
                throw new Error(data.message);
            }
            
            if (data.status === 'migrated') {
                this.showMigrationMessage(data);
                this.hideLoading();
                return;
            }

            this.frameworkData = data;
            this.renderFrameworkComponents();
            this.renderCharts();
            this.hideLoading();

        } catch (error) {
            console.error('Error loading project controls:', error);
            this.showError(error.message);
            this.hideLoading();
        }
    }

    extractClusterIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/cluster\/([^\/]+)/);
        return match ? match[1] : null;
    }

    showLoading() {
        this.isLoading = true;
        document.getElementById('controls-loading')?.classList.remove('hidden');
        document.getElementById('controls-main-content')?.classList.add('hidden');
        document.getElementById('controls-error')?.classList.add('hidden');
    }

    hideLoading() {
        this.isLoading = false;
        document.getElementById('controls-loading')?.classList.add('hidden');
        document.getElementById('controls-main-content')?.classList.remove('hidden');
    }

    showMigrationMessage(data) {
        const container = document.getElementById('projectcontrols-content');
        if (!container) return;
        
        container.innerHTML = `
            <div class="bg-blue-900 border border-blue-500 rounded-lg p-8 text-center">
                <div class="flex flex-col items-center space-y-4">
                    <i class="fas fa-arrow-up text-blue-500 text-4xl"></i>
                    <h3 class="text-2xl font-semibold text-white">System Upgraded!</h3>
                    <p class="text-blue-200 max-w-2xl">${data.message}</p>
                    
                    <div class="bg-blue-800 rounded-lg p-6 mt-6 w-full max-w-4xl">
                        <h4 class="text-lg font-semibold text-white mb-4">New Enterprise Features:</h4>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-left">
                            ${data.migration_info.benefits.map(benefit => 
                                `<div class="flex items-center space-x-2">
                                    <i class="fas fa-check text-green-500"></i>
                                    <span class="text-blue-100">${benefit}</span>
                                </div>`
                            ).join('')}
                        </div>
                    </div>
                    
                    <button onclick="showContent('enterprise-metrics', document.querySelector('[data-target=\\"#enterprise-metrics-content\\"]'))" 
                            class="mt-6 px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg transition-colors flex items-center space-x-2">
                        <i class="fas fa-building"></i>
                        <span>Go to Enterprise Metrics</span>
                        <i class="fas fa-arrow-right"></i>
                    </button>
                </div>
            </div>
        `;
    }

    showError(message) {
        document.getElementById('controls-loading')?.classList.add('hidden');
        document.getElementById('controls-main-content')?.classList.add('hidden');
        document.getElementById('controls-error')?.classList.remove('hidden');
        
        const errorElement = document.getElementById('controls-error-message');
        if (errorElement) {
            errorElement.textContent = message;
        }
    }

    renderFrameworkComponents() {
        if (!this.frameworkData?.framework) {
            this.showError('No framework data available');
            return;
        }

        this.updateKeyMetrics();
        this.renderCostProtection();
        this.renderGovernanceFramework();
        this.renderMonitoringStrategy();
        this.renderRiskMitigation();
        this.renderContingencyPlanning();
        this.renderSuccessCriteria();
        this.renderTimelineOptimization();
        this.renderIntelligenceInsights();
        this.renderFinancialMetrics();
    }

    updateKeyMetrics() {
        const framework = this.frameworkData.framework;
        
        const enabledControls = Object.values(framework).filter(control => control?.enabled === true).length;
        const mlConfidence = Math.round((this.frameworkData.ml_confidence || 0) * 100);
        const governanceLevel = framework.governance_framework?.governanceLevel || 'standard';
        
        // Update metrics
        const confidenceEl = document.getElementById('ml-confidence-score');
        const confidenceBar = document.getElementById('ml-confidence-bar');
        if (confidenceEl) confidenceEl.textContent = `${mlConfidence}%`;
        if (confidenceBar) confidenceBar.style.width = `${mlConfidence}%`;
        
        this.updateElement('governance-level', governanceLevel.charAt(0).toUpperCase() + governanceLevel.slice(1));
        this.updateElement('enabled-controls-count', `${enabledControls}/8`);
        
        // Determine risk level
        const riskCount = framework.risk_mitigation?.identifiedRisks?.length || 0;
        const riskLevel = riskCount > 5 ? 'High' : riskCount > 2 ? 'Medium' : 'Low';
        const riskEl = document.getElementById('risk-level');
        if (riskEl) {
            riskEl.textContent = riskLevel;
            riskEl.className = riskLevel === 'High' ? 'text-2xl font-bold text-red-500' : 
                               riskLevel === 'Medium' ? 'text-2xl font-bold text-orange-500' : 
                               'text-2xl font-bold text-white';
        }
    }

    renderFinancialMetrics() {
        const costProtection = this.frameworkData.framework.cost_protection;
        if (!costProtection) return;

        const budgetLimits = costProtection.budgetLimits || {};
        const savingsProtection = costProtection.savingsProtection || {};

        const metricsHtml = `
            <div class="text-center">
                <div class="text-gray-400 text-xs uppercase">Monthly Budget</div>
                <div class="text-white font-bold">$${this.formatNumber(budgetLimits.monthlyBudget || 0)}</div>
            </div>
            <div class="text-center">
                <div class="text-gray-400 text-xs uppercase">Alert Threshold</div>
                <div class="text-orange-500 font-bold">$${this.formatNumber(budgetLimits.alertThreshold || 0)}</div>
            </div>
            <div class="text-center">
                <div class="text-gray-400 text-xs uppercase">Hard Limit</div>
                <div class="text-red-500 font-bold">$${this.formatNumber(budgetLimits.hardLimit || 0)}</div>
            </div>
            <div class="text-center">
                <div class="text-gray-400 text-xs uppercase">Predicted Savings</div>
                <div class="text-white font-bold">$${this.formatNumber(savingsProtection.predicted_savings || 0)}</div>
            </div>
        `;

        const metricsContainer = document.getElementById('financial-metrics');
        if (metricsContainer) metricsContainer.innerHTML = metricsHtml;
    }

    renderCharts() {
        // Destroy all existing charts first
        Object.keys(this.charts).forEach(key => {
            if (this.charts[key]) {
                this.charts[key].destroy();
                delete this.charts[key];
            }
        });

        // Budget Allocation Chart
        const budgetCanvas = document.getElementById('budget-chart');
        if (budgetCanvas && window.Chart) {
            const costProtection = this.frameworkData.framework.cost_protection;
            const budgetLimits = costProtection?.budgetLimits || {};
            
            // Set fixed dimensions
            budgetCanvas.style.maxWidth = '400px';
            budgetCanvas.style.maxHeight = '250px';
            
            const ctx = budgetCanvas.getContext('2d');
            ctx.clearRect(0, 0, budgetCanvas.width, budgetCanvas.height);
            
            this.charts.budget = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Used', 'Available', 'Reserved'],
                    datasets: [{
                        data: [
                            budgetLimits.monthlyBudget * 0.6 || 0,
                            budgetLimits.monthlyBudget * 0.3 || 0,
                            budgetLimits.monthlyBudget * 0.1 || 0
                        ],
                        backgroundColor: ['#10b981', '#374151', '#1f2937'],
                        borderColor: '#111827',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: false,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#9ca3af', font: { size: 11 } }
                        }
                    }
                }
            });
        }

        // Savings Trend Chart
        const savingsCanvas = document.getElementById('savings-chart');
        if (savingsCanvas && window.Chart) {
            // Set fixed dimensions
            savingsCanvas.style.maxWidth = '400px';
            savingsCanvas.style.maxHeight = '250px';
            
            const ctx = savingsCanvas.getContext('2d');
            ctx.clearRect(0, 0, savingsCanvas.width, savingsCanvas.height);
            
            this.charts.savings = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Projected Savings',
                        data: [100, 150, 180, 220, 280, 350],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: false,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            grid: { color: '#374151' },
                            ticks: { color: '#9ca3af' }
                        },
                        x: {
                            grid: { color: '#374151' },
                            ticks: { color: '#9ca3af' }
                        }
                    }
                }
            });
        }

        // Risk Matrix Chart
        const riskCanvas = document.getElementById('risk-matrix-chart');
        if (riskCanvas && window.Chart) {
            const risks = this.frameworkData.framework.risk_mitigation?.identifiedRisks || [];
            
            // Set fixed dimensions
            riskCanvas.style.maxWidth = '800px';
            riskCanvas.style.maxHeight = '300px';
            
            const ctx = riskCanvas.getContext('2d');
            ctx.clearRect(0, 0, riskCanvas.width, riskCanvas.height);
            
            this.charts.risk = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: risks.map(r => r.risk_id || 'Unknown'),
                    datasets: [{
                        label: 'Risk Score',
                        data: risks.map(r => {
                            const prob = r.probability?.toLowerCase() || 'low';
                            return prob === 'high' ? 3 : prob === 'medium' ? 2 : 1;
                        }),
                        backgroundColor: risks.map(r => {
                            const prob = r.probability?.toLowerCase() || 'low';
                            return prob === 'high' ? '#ef4444' : prob === 'medium' ? '#f97316' : '#10b981';
                        })
                    }]
                },
                options: {
                    responsive: false,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 3,
                            ticks: {
                                stepSize: 1,
                                callback: value => ['', 'Low', 'Medium', 'High'][value],
                                color: '#9ca3af'
                            },
                            grid: { color: '#374151' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af' }
                        }
                    }
                }
            });
        }
    }

    renderCostProtection() {
        const costProtection = this.frameworkData.framework.cost_protection;
        this.updateStatusBadge('cost-protection-status', costProtection?.enabled);
        
        const content = document.getElementById('cost-protection-content');
        if (!content || !costProtection) return;

        const savingsProtection = costProtection.savingsProtection || {};

        content.innerHTML = `
            <div class="space-y-2">
                <div class="flex justify-between">
                    <span class="text-gray-400">Minimum Savings Target:</span>
                    <span class="text-white">$${this.formatNumber(savingsProtection.minimumSavingsTarget || 0)}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Opportunities Identified:</span>
                    <span class="text-white">${savingsProtection.optimization_opportunities_identified || 0}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">ML Confidence:</span>
                    <span class="text-white">${Math.round((costProtection.ml_confidence || 0) * 100)}%</span>
                </div>
            </div>
        `;
    }

    renderGovernanceFramework() {
        const governance = this.frameworkData.framework.governance_framework;
        this.updateStatusBadge('governance-status', governance?.enabled);
        
        const content = document.getElementById('governance-content');
        if (!content || !governance) return;

        const approvalRequirements = governance.approvalRequirements || {};
        const changeManagement = governance.changeManagement || {};

        content.innerHTML = `
            <div class="space-y-2">
                <div class="flex justify-between">
                    <span class="text-gray-400">Governance Level:</span>
                    <span class="text-white">${governance.governanceLevel || 'Standard'}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Complexity:</span>
                    <span class="text-white">${governance.cluster_complexity || 'Medium'}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Business Approval:</span>
                    <span class="${approvalRequirements.business_approval ? 'text-white' : 'text-gray-500'}">
                        ${approvalRequirements.business_approval ? 'Required' : 'Not Required'}
                    </span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Technical Approval:</span>
                    <span class="${approvalRequirements.technical_approval ? 'text-white' : 'text-gray-500'}">
                        ${approvalRequirements.technical_approval ? 'Required' : 'Not Required'}
                    </span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Rollback Procedures:</span>
                    <span class="text-white text-xs">${changeManagement.rollback_procedures || 'Manual'}</span>
                </div>
            </div>
        `;
    }

    renderMonitoringStrategy() {
        const monitoring = this.frameworkData.framework.monitoring_strategy;
        this.updateStatusBadge('monitoring-status', monitoring?.enabled);
        
        const content = document.getElementById('monitoring-content');
        if (!content || !monitoring) return;

        const alerting = monitoring.alerting || {};
        const keyMetrics = monitoring.keyMetrics || [];

        content.innerHTML = `
            <div class="space-y-2">
                <div class="flex justify-between">
                    <span class="text-gray-400">Monitoring Frequency:</span>
                    <span class="text-white">${monitoring.monitoringFrequency || 'Frequent'}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Key Metrics:</span>
                    <span class="text-white">${keyMetrics.length} configured</span>
                </div>
                <div class="mt-3 pt-3 border-t border-gray-700">
                    <div class="text-gray-400 mb-2">Active Alerts:</div>
                    <div class="space-y-1">
                        <div class="flex items-center justify-between">
                            <span class="text-gray-500 text-sm">Cost Spike</span>
                            <i class="fas fa-${alerting.cost_spike_alerts ? 'check text-green-500' : 'times text-gray-600'} text-sm"></i>
                        </div>
                        <div class="flex items-center justify-between">
                            <span class="text-gray-500 text-sm">Performance</span>
                            <i class="fas fa-${alerting.performance_degradation_alerts ? 'check text-green-500' : 'times text-gray-600'} text-sm"></i>
                        </div>
                        <div class="flex items-center justify-between">
                            <span class="text-gray-500 text-sm">Scaling</span>
                            <i class="fas fa-${alerting.scaling_inefficiency_alerts ? 'check text-green-500' : 'times text-gray-600'} text-sm"></i>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderRiskMitigation() {
        const riskMitigation = this.frameworkData.framework.risk_mitigation;
        this.updateStatusBadge('risk-status', riskMitigation?.enabled);
        
        const content = document.getElementById('risk-content');
        if (!content || !riskMitigation) return;

        const identifiedRisks = riskMitigation.identifiedRisks || [];
        const mlRiskAssessment = riskMitigation.ml_risk_assessment || {};

        content.innerHTML = `
            <div class="space-y-2">
                <div class="flex justify-between">
                    <span class="text-gray-400">Identified Risks:</span>
                    <span class="${identifiedRisks.length > 5 ? 'text-red-500' : identifiedRisks.length > 2 ? 'text-orange-500' : 'text-white'}">
                        ${identifiedRisks.length}
                    </span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Security Posture:</span>
                    <span class="text-white">${riskMitigation.security_posture || 'Enterprise'}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Model Confidence:</span>
                    <span class="text-white">${Math.round((mlRiskAssessment.model_confidence || 0) * 100)}%</span>
                </div>
                ${identifiedRisks.length > 0 ? `
                <div class="mt-3 pt-3 border-t border-gray-700">
                    <div class="text-gray-400 mb-2">Top Risks:</div>
                    <div class="space-y-1">
                        ${identifiedRisks.slice(0, 3).map(risk => `
                            <div class="flex items-center justify-between">
                                <span class="text-gray-500 text-sm">${risk.risk_id}</span>
                                <span class="text-xs ${risk.probability?.toLowerCase() === 'high' ? 'text-red-500' : 
                                    risk.probability?.toLowerCase() === 'medium' ? 'text-orange-500' : 'text-gray-400'}">
                                    ${risk.probability || 'Low'}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }

    renderContingencyPlanning() {
        const contingency = this.frameworkData.framework.contingency_planning;
        this.updateStatusBadge('contingency-status', contingency?.enabled);
        
        const content = document.getElementById('contingency-content');
        if (!content || !contingency) return;

        const contingencyTriggers = contingency.contingencyTriggers || [];
        const rollbackProcedures = contingency.rollbackProcedures || {};

        content.innerHTML = `
            <div class="space-y-2">
                <div class="flex justify-between">
                    <span class="text-gray-400">Configured Triggers:</span>
                    <span class="text-white">${contingencyTriggers.length}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Rollback Time:</span>
                    <span class="text-white">${rollbackProcedures.rollback_time_estimate || '15 minutes'}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Auto Rollback:</span>
                    <span class="${rollbackProcedures.automated_rollback_available ? 'text-white' : 'text-gray-500'}">
                        ${rollbackProcedures.automated_rollback_available ? 'Available' : 'Manual Only'}
                    </span>
                </div>
            </div>
        `;
    }

    renderSuccessCriteria() {
        const successCriteria = this.frameworkData.framework.success_criteria;
        this.updateStatusBadge('success-status', successCriteria?.enabled);
        
        const content = document.getElementById('success-content');
        if (!content || !successCriteria) return;

        const financialTargets = successCriteria.financialTargets || {};
        const technicalTargets = successCriteria.technicalTargets || {};

        content.innerHTML = `
            <div class="space-y-2">
                <div class="flex justify-between">
                    <span class="text-gray-400">Monthly Savings Target:</span>
                    <span class="text-white">$${this.formatNumber(financialTargets.monthly_savings_target || 0)}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Opportunities Addressed:</span>
                    <span class="text-white">${financialTargets.optimization_opportunities_addressed || 0}</span>
                </div>
                <div class="mt-3 pt-3 border-t border-gray-700">
                    <div class="text-gray-400 mb-2">Technical Targets:</div>
                    <div class="space-y-1">
                        <div class="flex items-center justify-between">
                            <span class="text-gray-500 text-sm">Zero Downtime</span>
                            <i class="fas fa-${technicalTargets.zero_downtime_during_implementation ? 'check text-green-500' : 'times text-gray-600'} text-sm"></i>
                        </div>
                        <div class="flex items-center justify-between">
                            <span class="text-gray-500 text-sm">ML Accuracy</span>
                            <i class="fas fa-${technicalTargets.ml_prediction_accuracy_maintained ? 'check text-green-500' : 'times text-gray-600'} text-sm"></i>
                        </div>
                        <div class="flex items-center justify-between">
                            <span class="text-gray-500 text-sm">Config Consistency</span>
                            <i class="fas fa-${technicalTargets.cluster_config_consistency_maintained ? 'check text-green-500' : 'times text-gray-600'} text-sm"></i>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderTimelineOptimization() {
        const timelineOpt = this.frameworkData.framework.timeline_optimization;
        this.updateStatusBadge('timeline-status', timelineOpt?.enabled);
        
        const content = document.getElementById('timeline-content');
        if (!content || !timelineOpt) return;

        const savedWeeks = (timelineOpt.originalTimelineWeeks || 0) - (timelineOpt.optimizedTimelineWeeks || 0);
        const savingPercent = timelineOpt.originalTimelineWeeks ? 
            Math.round((savedWeeks / timelineOpt.originalTimelineWeeks) * 100) : 0;

        content.innerHTML = `
            <div class="space-y-2">
                <div class="flex justify-between">
                    <span class="text-gray-400">Original Timeline:</span>
                    <span class="text-white">${timelineOpt.originalTimelineWeeks || 0} weeks</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Optimized Timeline:</span>
                    <span class="text-white">${timelineOpt.optimizedTimelineWeeks || 0} weeks</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Time Saved:</span>
                    <span class="text-green-500">${savedWeeks} weeks (${savingPercent}%)</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Complexity Factor:</span>
                    <span class="text-white">${(timelineOpt.cluster_complexity_factor || 0).toFixed(1)}x</span>
                </div>
            </div>
        `;
    }

    renderIntelligenceInsights() {
        const intelligence = this.frameworkData.framework.intelligence_insights;
        this.updateStatusBadge('intelligence-status', intelligence?.enabled);
        
        const content = document.getElementById('intelligence-content');
        if (!content || !intelligence) return;

        const recommendations = intelligence.recommendations || {};

        content.innerHTML = `
            <div class="space-y-2">
                <div class="flex justify-between">
                    <span class="text-gray-400">Analysis Confidence:</span>
                    <span class="text-white">${Math.round((intelligence.analysisConfidence || 0) * 100)}%</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">CV Score:</span>
                    <span class="text-white">${((intelligence.actual_cv_score || 0) * 100).toFixed(1)}%</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Opportunities:</span>
                    <span class="text-white">${intelligence.optimization_opportunities || 0}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Total Workloads:</span>
                    <span class="text-white">${intelligence.total_workloads || 0}</span>
                </div>
                <div class="mt-3 pt-3 border-t border-gray-700">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Priority:</span>
                        <span class="${recommendations.priority === 'High' ? 'text-orange-500' : 'text-white'}">
                            ${recommendations.priority || 'Medium'}
                        </span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Azure Optimizations:</span>
                        <span class="${recommendations.azure_optimizations_available ? 'text-white' : 'text-gray-500'}">
                            ${recommendations.azure_optimizations_available ? 'Available' : 'None'}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    updateStatusBadge(elementId, enabled) {
        const element = document.getElementById(elementId);
        if (!element) return;

        if (enabled) {
            element.textContent = 'Enabled';
            element.className = 'text-xs px-2 py-1 rounded bg-gray-700 text-green-500 border border-green-500';
        } else {
            element.textContent = 'Disabled';
            element.className = 'text-xs px-2 py-1 rounded bg-gray-700 text-gray-500 border border-gray-600';
        }
    }

    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    formatNumber(num) {
        return Number(num).toLocaleString();
    }

    exportFrameworkData() {
        // Export functionality disabled to prevent data exposure
        alert('Framework data export has been disabled for security purposes');
    }
}

// Initialize Project Controls Manager
let projectControlsManager;

document.addEventListener('DOMContentLoaded', function() {
    projectControlsManager = new ProjectControlsManager();
    console.log('✅ Project Controls Manager initialized');
});

// Global function for tab loading
function loadProjectControlsTab() {
    if (projectControlsManager && !projectControlsManager.isLoading) {
        projectControlsManager.loadProjectControls();
    }
}

// Debug function
window.debugProjectControls = function() {
    if (projectControlsManager?.frameworkData) {
        console.log('Project Controls Data:', projectControlsManager.frameworkData);
    } else {
        console.log('No project controls data available');
    }
};