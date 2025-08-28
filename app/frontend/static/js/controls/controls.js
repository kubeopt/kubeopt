/**
 * Modern Project Controls Manager - Clean & User-Friendly Design
 */

class ProjectControlsManager {
    constructor() {
        this.clusterId = null;
        this.frameworkData = null;
        this.isLoading = false;
        
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

            this.frameworkData = data;
            this.renderFrameworkComponents();
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

        this.updateOverviewMetrics();
        
        // Render all components with new clean design
        this.renderCostProtection();
        this.renderGovernanceFramework();
        this.renderMonitoringStrategy();
        this.renderRiskMitigation();
        this.renderContingencyPlanning();
        this.renderSuccessCriteria();
        this.renderTimelineOptimization();
        this.renderIntelligenceInsights();
    }

    updateOverviewMetrics() {
        const framework = this.frameworkData.framework;
        
        const enabledControls = Object.values(framework).filter(control => control?.enabled === true).length;
        const mlConfidence = Math.round((this.frameworkData.ml_confidence || 0) * 100);
        const governanceLevel = framework.governance_framework?.governanceLevel || 'standard';
        const totalCommands = Object.values(framework).reduce((sum, component) => {
            return sum + (component?.total_commands || 0);
        }, 0);

        this.updateElement('enabled-controls-count', `${enabledControls}/8`);
        this.updateElement('ml-confidence-score', `${mlConfidence}%`);
        this.updateElement('governance-level', governanceLevel);
        this.updateElement('total-commands-count', totalCommands);
    }

    renderCostProtection() {
        const costProtection = this.frameworkData.framework.cost_protection;
        
        this.updateStatusBadge('cost-protection-status', costProtection?.enabled);
        
        const content = document.getElementById('cost-protection-content');
        if (!content || !costProtection) return;

        const budgetLimits = costProtection.budgetLimits || {};
        const savingsProtection = costProtection.savingsProtection || {};

        content.innerHTML = `
            <div class="space-y-4">
                <!-- Budget Overview - Clean Card -->
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <div class="flex items-center mb-6">
                        <div class="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center mr-3">
                            <i class="fas fa-dollar-sign text-white text-sm"></i>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-gray-500">Budget Management</h4>
                            <p class="text-sm text-gray-500">Monitor and control cluster spending</p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        <div class="text-center p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="text-2xl font-bold text-gray-900 mb-1">$${this.formatNumber(budgetLimits.monthlyBudget || 0)}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Monthly Budget</div>
                        </div>
                        <div class="text-center p-4 bg-orange-50 rounded-lg border border-orange-100">
                            <div class="text-2xl font-bold text-orange-600 mb-1">$${this.formatNumber(budgetLimits.alertThreshold || 0)}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Alert Threshold</div>
                        </div>
                        <div class="text-center p-4 bg-red-50 rounded-lg border border-red-100">
                            <div class="text-2xl font-bold text-red-600 mb-1">$${this.formatNumber(budgetLimits.hardLimit || 0)}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Hard Limit</div>
                        </div>
                        <div class="text-center p-4 bg-green-50 rounded-lg border border-green-100">
                            <div class="text-2xl font-bold text-green-600 mb-1">$${this.formatNumber(savingsProtection.predicted_savings || 0)}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Predicted Savings</div>
                        </div>
                    </div>
                </div>

                <!-- Savings Protection - Clean Card -->
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <div class="flex items-center mb-6">
                        <div class="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center mr-3">
                            <i class="fas fa-shield-alt text-white text-sm"></i>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-gray-500">Savings Protection</h4>
                            <p class="text-sm text-gray-500">Optimize costs and protect savings</p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div class="flex items-center p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="flex-1">
                                <div class="text-sm text-gray-500 mb-1">Minimum Target</div>
                                <div class="text-xl font-bold text-gray-900">$${this.formatNumber(savingsProtection.minimumSavingsTarget || 0)}</div>
                            </div>
                            <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                                <i class="fas fa-target text-green-600"></i>
                            </div>
                        </div>
                        
                        <div class="flex items-center p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="flex-1">
                                <div class="text-sm text-gray-500 mb-1">Opportunities</div>
                                <div class="text-xl font-bold text-gray-900">${savingsProtection.optimization_opportunities_identified || 0}</div>
                            </div>
                            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                                <i class="fas fa-lightbulb text-blue-600"></i>
                            </div>
                        </div>
                        
                        <div class="flex items-center p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="flex-1">
                                <div class="text-sm text-gray-500 mb-1">ML Confidence</div>
                                <div class="text-xl font-bold text-gray-900">${Math.round((costProtection.ml_confidence || 0) * 100)}%</div>
                            </div>
                            <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                                <i class="fas fa-brain text-purple-600"></i>
                            </div>
                        </div>
                    </div>
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
            <div class="space-y-4">
                <!-- Governance Overview -->
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <div class="flex items-center justify-between mb-6">
                        <div class="flex items-center">
                            <div class="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center mr-3">
                                <i class="fas fa-balance-scale text-white text-sm"></i>
                            </div>
                            <div>
                                <h4 class="text-lg font-semibold text-gray-500">Governance Framework</h4>
                                <p class="text-sm text-gray-500">Control and approval processes</p>
                            </div>
                        </div>
                        <span class="px-3 py-1 text-sm font-medium bg-purple-100 text-purple-800 rounded-full">
                            ${governance.governanceLevel || 'Standard'} Level
                        </span>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div class="text-center p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-layer-group text-gray-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${governance.cluster_complexity || 'Medium'}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Complexity</div>
                        </div>
                        
                        <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
                            <div class="w-12 h-12 bg-blue-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-${approvalRequirements.business_approval ? 'check' : 'times'} text-blue-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${approvalRequirements.business_approval ? 'Required' : 'Optional'}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Business Approval</div>
                        </div>
                        
                        <div class="text-center p-4 bg-green-50 rounded-lg border border-green-100">
                            <div class="w-12 h-12 bg-green-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-${approvalRequirements.technical_approval ? 'check' : 'times'} text-green-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${approvalRequirements.technical_approval ? 'Required' : 'Optional'}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Technical Approval</div>
                        </div>
                    </div>
                </div>

                <!-- Change Management -->
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <h5 class="text-base font-semibold text-gray-500 mb-4">Change Management</h5>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="flex items-start p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                                <i class="fas fa-undo text-orange-600 text-sm"></i>
                            </div>
                            <div>
                                <div class="text-sm font-medium text-gray-900 mb-1">Rollback Procedures</div>
                                <div class="text-sm text-gray-600">${changeManagement.rollback_procedures || 'Automated with Manual Override'}</div>
                            </div>
                        </div>
                        
                        <div class="flex items-start p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                                <i class="fas fa-clock text-blue-600 text-sm"></i>
                            </div>
                            <div>
                                <div class="text-sm font-medium text-gray-900 mb-1">Change Windows</div>
                                <div class="text-sm text-gray-600">${(changeManagement.change_windows || []).join(', ') || 'Maintenance Window'}</div>
                            </div>
                        </div>
                    </div>
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
            <div class="space-y-4">
                <!-- Monitoring Overview -->
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <div class="flex items-center mb-6">
                        <div class="w-10 h-10 bg-yellow-500 rounded-lg flex items-center justify-center mr-3">
                            <i class="fas fa-chart-line text-white text-sm"></i>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-gray-500">Monitoring Strategy</h4>
                            <p class="text-sm text-gray-500">Real-time cluster monitoring and alerts</p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div class="text-center p-4 bg-yellow-50 rounded-lg border border-yellow-100">
                            <div class="w-12 h-12 bg-yellow-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-tachometer-alt text-yellow-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${monitoring.monitoringFrequency || 'Frequent'}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Frequency</div>
                        </div>
                        
                        <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
                            <div class="w-12 h-12 bg-blue-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-list text-blue-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${keyMetrics.length}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Key Metrics</div>
                        </div>
                        
                        <div class="text-center p-4 bg-green-50 rounded-lg border border-green-100">
                            <div class="w-12 h-12 bg-green-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-brain text-green-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${Math.round((monitoring.ml_confidence || 0) * 100)}%</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">ML Confidence</div>
                        </div>
                    </div>
                </div>

                <!-- Alert Configuration -->
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <h5 class="text-base font-semibold text-gray-500 mb-4">Alert Configuration</h5>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="flex items-center p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="w-10 h-10 rounded-lg flex items-center justify-center mr-4 ${alerting.cost_spike_alerts ? 'bg-green-100' : 'bg-red-100'}">
                                <i class="fas fa-${alerting.cost_spike_alerts ? 'check text-green-600' : 'times text-red-600'}"></i>
                            </div>
                            <div>
                                <div class="font-medium text-gray-900">Cost Spike Alerts</div>
                                <div class="text-sm text-gray-500">${alerting.cost_spike_alerts ? 'Enabled' : 'Disabled'}</div>
                            </div>
                        </div>
                        
                        <div class="flex items-center p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="w-10 h-10 rounded-lg flex items-center justify-center mr-4 ${alerting.performance_degradation_alerts ? 'bg-green-100' : 'bg-red-100'}">
                                <i class="fas fa-${alerting.performance_degradation_alerts ? 'check text-green-600' : 'times text-red-600'}"></i>
                            </div>
                            <div>
                                <div class="font-medium text-gray-900">Performance Alerts</div>
                                <div class="text-sm text-gray-500">${alerting.performance_degradation_alerts ? 'Enabled' : 'Disabled'}</div>
                            </div>
                        </div>
                        
                        <div class="flex items-center p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="w-10 h-10 rounded-lg flex items-center justify-center mr-4 ${alerting.scaling_inefficiency_alerts ? 'bg-green-100' : 'bg-red-100'}">
                                <i class="fas fa-${alerting.scaling_inefficiency_alerts ? 'check text-green-600' : 'times text-red-600'}"></i>
                            </div>
                            <div>
                                <div class="font-medium text-gray-900">Scaling Alerts</div>
                                <div class="text-sm text-gray-500">${alerting.scaling_inefficiency_alerts ? 'Enabled' : 'Disabled'}</div>
                            </div>
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
            <div class="space-y-4">
                <!-- Risk Overview -->
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <div class="flex items-center mb-6">
                        <div class="w-10 h-10 bg-red-500 rounded-lg flex items-center justify-center mr-3">
                            <i class="fas fa-exclamation-triangle text-white text-sm"></i>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-gray-500">Risk Assessment</h4>
                            <p class="text-sm text-gray-500">Identify and mitigate potential risks</p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div class="text-center p-4 bg-red-50 rounded-lg border border-red-100">
                            <div class="w-12 h-12 bg-red-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-exclamation text-red-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${identifiedRisks.length}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Identified Risks</div>
                        </div>
                        
                        <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
                            <div class="w-12 h-12 bg-blue-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-shield-alt text-blue-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${riskMitigation.security_posture || 'Enterprise'}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Security Posture</div>
                        </div>
                        
                        <div class="text-center p-4 bg-green-50 rounded-lg border border-green-100">
                            <div class="w-12 h-12 bg-green-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-brain text-green-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${Math.round((mlRiskAssessment.model_confidence || 0) * 100)}%</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Model Confidence</div>
                        </div>
                    </div>
                </div>

                <!-- Risk Details -->
                ${identifiedRisks.length > 0 ? `
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <h5 class="text-base font-semibold text-gray-500 mb-4">Risk Details</h5>
                    <div class="space-y-3 max-h-64 overflow-y-auto">
                        ${identifiedRisks.map(risk => `
                            <div class="flex items-start p-4 bg-gray-50 rounded-lg border border-gray-100">
                                <div class="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                                    <i class="fas fa-warning text-orange-600 text-sm"></i>
                                </div>
                                <div class="flex-1">
                                    <div class="font-medium text-gray-900 mb-1">${risk.risk_id}</div>
                                    <div class="text-sm text-gray-600 mb-2">${risk.description}</div>
                                    <div class="flex items-center space-x-3">
                                        <span class="px-2 py-1 text-xs rounded-full ${this.getRiskBadgeClass(risk.probability)}">
                                            ${risk.probability} Probability
                                        </span>
                                        <span class="text-xs text-gray-500">${risk.mitigation}</span>
                                    </div>
                                </div>
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
            <div class="space-y-4">
                <!-- Contingency Overview -->
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <div class="flex items-center mb-6">
                        <div class="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center mr-3">
                            <i class="fas fa-life-ring text-white text-sm"></i>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-gray-500">Contingency Planning</h4>
                            <p class="text-sm text-gray-500">Emergency procedures and rollback plans</p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div class="text-center p-4 bg-orange-50 rounded-lg border border-orange-100">
                            <div class="w-12 h-12 bg-orange-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-bolt text-orange-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${contingencyTriggers.length}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Configured Triggers</div>
                        </div>
                        
                        <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
                            <div class="w-12 h-12 bg-blue-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-clock text-blue-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${rollbackProcedures.rollback_time_estimate || '15 minutes'}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Rollback Time</div>
                        </div>
                        
                        <div class="text-center p-4 bg-green-50 rounded-lg border border-green-100">
                            <div class="w-12 h-12 bg-green-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-${rollbackProcedures.automated_rollback_available ? 'check' : 'times'} text-green-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${rollbackProcedures.automated_rollback_available ? 'Yes' : 'No'}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Auto Rollback</div>
                        </div>
                    </div>
                </div>

                <!-- Triggers -->
                ${contingencyTriggers.length > 0 ? `
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <h5 class="text-base font-semibold text-gray-500 mb-4">Contingency Triggers</h5>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        ${contingencyTriggers.map(trigger => `
                            <div class="flex items-center p-3 bg-gray-50 rounded-lg border border-gray-100">
                                <div class="w-6 h-6 bg-orange-100 rounded flex items-center justify-center mr-3">
                                    <i class="fas fa-bolt text-orange-600 text-xs"></i>
                                </div>
                                <div class="text-sm font-medium text-gray-900">${trigger.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
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
            <div class="space-y-4">
                <!-- Success Overview -->
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <div class="flex items-center mb-6">
                        <div class="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center mr-3">
                            <i class="fas fa-trophy text-white text-sm"></i>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-gray-500">Success Criteria</h4>
                            <p class="text-sm text-gray-500">Measurable targets and goals</p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div class="text-center p-4 bg-green-50 rounded-lg border border-green-100">
                            <div class="w-12 h-12 bg-green-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-dollar-sign text-green-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">$${this.formatNumber(financialTargets.monthly_savings_target || 0)}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Monthly Savings Target</div>
                        </div>
                        
                        <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
                            <div class="w-12 h-12 bg-blue-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-bullseye text-blue-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${financialTargets.optimization_opportunities_addressed || 0}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Opportunities Addressed</div>
                        </div>
                        
                        <div class="text-center p-4 bg-purple-50 rounded-lg border border-purple-100">
                            <div class="w-12 h-12 bg-purple-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <i class="fas fa-brain text-purple-600"></i>
                            </div>
                            <div class="text-lg font-semibold text-gray-900 mb-1">${Math.round((financialTargets.ml_confidence_target || 0) * 100)}%</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">ML Confidence Target</div>
                        </div>
                    </div>
                </div>

                <!-- Technical Targets -->
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <h5 class="text-base font-semibold text-gray-500 mb-4">Technical Targets</h5>
                    <div class="space-y-3">
                        <div class="flex items-center p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="w-10 h-10 rounded-lg flex items-center justify-center mr-4 ${technicalTargets.zero_downtime_during_implementation ? 'bg-green-100' : 'bg-gray-100'}">
                                <i class="fas fa-${technicalTargets.zero_downtime_during_implementation ? 'check text-green-600' : 'times text-gray-400'}"></i>
                            </div>
                            <div>
                                <div class="font-medium text-gray-900">Zero Downtime Implementation</div>
                                <div class="text-sm text-gray-500">${technicalTargets.zero_downtime_during_implementation ? 'Target Set' : 'Not Required'}</div>
                            </div>
                        </div>
                        
                        <div class="flex items-center p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="w-10 h-10 rounded-lg flex items-center justify-center mr-4 ${technicalTargets.ml_prediction_accuracy_maintained ? 'bg-green-100' : 'bg-gray-100'}">
                                <i class="fas fa-${technicalTargets.ml_prediction_accuracy_maintained ? 'check text-green-600' : 'times text-gray-400'}"></i>
                            </div>
                            <div>
                                <div class="font-medium text-gray-900">ML Prediction Accuracy</div>
                                <div class="text-sm text-gray-500">${technicalTargets.ml_prediction_accuracy_maintained ? 'Maintained' : 'Not Tracked'}</div>
                            </div>
                        </div>
                        
                        <div class="flex items-center p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="w-10 h-10 rounded-lg flex items-center justify-center mr-4 ${technicalTargets.cluster_config_consistency_maintained ? 'bg-green-100' : 'bg-gray-100'}">
                                <i class="fas fa-${technicalTargets.cluster_config_consistency_maintained ? 'check text-green-600' : 'times text-gray-400'}"></i>
                            </div>
                            <div>
                                <div class="font-medium text-gray-900">Config Consistency</div>
                                <div class="text-sm text-gray-500">${technicalTargets.cluster_config_consistency_maintained ? 'Maintained' : 'Not Tracked'}</div>
                            </div>
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

        content.innerHTML = `
            <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                <div class="flex items-center mb-6">
                    <div class="w-10 h-10 bg-indigo-500 rounded-lg flex items-center justify-center mr-3">
                        <i class="fas fa-clock text-white text-sm"></i>
                    </div>
                    <div>
                        <h4 class="text-lg font-semibold text-gray-500">Timeline Optimization</h4>
                        <p class="text-sm text-gray-500">Optimized implementation schedule</p>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="text-center p-4 bg-indigo-50 rounded-lg border border-indigo-100">
                        <div class="w-12 h-12 bg-indigo-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                            <i class="fas fa-calendar-check text-indigo-600"></i>
                        </div>
                        <div class="text-lg font-semibold text-gray-900 mb-1">${timelineOpt.optimizedTimelineWeeks || 0}</div>
                        <div class="text-xs text-gray-500 uppercase tracking-wide">Optimized Weeks</div>
                    </div>
                    
                    <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
                        <div class="w-12 h-12 bg-blue-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                            <i class="fas fa-calendar text-blue-600"></i>
                        </div>
                        <div class="text-lg font-semibold text-gray-900 mb-1">${timelineOpt.originalTimelineWeeks || 0}</div>
                        <div class="text-xs text-gray-500 uppercase tracking-wide">Original Weeks</div>
                    </div>
                    
                    <div class="text-center p-4 bg-green-50 rounded-lg border border-green-100">
                        <div class="w-12 h-12 bg-green-200 rounded-lg flex items-center justify-center mx-auto mb-3">
                            <i class="fas fa-layer-group text-green-600"></i>
                        </div>
                        <div class="text-lg font-semibold text-gray-900 mb-1">${(timelineOpt.cluster_complexity_factor || 0).toFixed(1)}x</div>
                        <div class="text-xs text-gray-500 uppercase tracking-wide">Complexity Factor</div>
                    </div>
                </div>
            </div>
        `;
    }

    renderIntelligenceInsights() {
        const intelligence = this.frameworkData.framework.intelligence_insights;
        
        this.updateStatusBadge('intelligence-status', intelligence?.enabled);
        
        const content = document.getElementById('intelligence-content');
        if (!content || !intelligence) return;

        const clusterProfile = intelligence.clusterProfile || {};
        const mlPredictions = intelligence.ml_predictions || {};
        const recommendations = intelligence.recommendations || {};

        content.innerHTML = `
            <div class="space-y-4">
                <!-- Intelligence Overview -->
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <div class="flex items-center mb-6">
                        <div class="w-10 h-10 bg-pink-500 rounded-lg flex items-center justify-center mr-3">
                            <i class="fas fa-brain text-white text-sm"></i>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-gray-500">Intelligence Insights</h4>
                            <p class="text-sm text-gray-500">AI-powered analysis and recommendations</p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        <div class="text-center p-4 bg-pink-50 rounded-lg border border-pink-100">
                            <div class="w-10 h-10 bg-pink-200 rounded-lg flex items-center justify-center mx-auto mb-2">
                                <i class="fas fa-chart-line text-pink-600 text-sm"></i>
                            </div>
                            <div class="text-lg font-bold text-gray-900">${Math.round((intelligence.analysisConfidence || 0) * 100)}%</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Analysis Confidence</div>
                        </div>
                        
                        <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
                            <div class="w-10 h-10 bg-blue-200 rounded-lg flex items-center justify-center mx-auto mb-2">
                                <i class="fas fa-percentage text-blue-600 text-sm"></i>
                            </div>
                            <div class="text-lg font-bold text-gray-900">${(intelligence.actual_cv_score * 100).toFixed(1)}%</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">CV Score</div>
                        </div>
                        
                        <div class="text-center p-4 bg-green-50 rounded-lg border border-green-100">
                            <div class="w-10 h-10 bg-green-200 rounded-lg flex items-center justify-center mx-auto mb-2">
                                <i class="fas fa-lightbulb text-green-600 text-sm"></i>
                            </div>
                            <div class="text-lg font-bold text-gray-900">${intelligence.optimization_opportunities || 0}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Opportunities</div>
                        </div>
                        
                        <div class="text-center p-4 bg-purple-50 rounded-lg border border-purple-100">
                            <div class="w-10 h-10 bg-purple-200 rounded-lg flex items-center justify-center mx-auto mb-2">
                                <i class="fas fa-server text-purple-600 text-sm"></i>
                            </div>
                            <div class="text-lg font-bold text-gray-900">${intelligence.total_workloads || 0}</div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Workloads</div>
                        </div>
                    </div>
                </div>

                <!-- Recommendations -->
                <div class="bg-white border border-gray-100 rounded-lg p-6 shadow-sm">
                    <h5 class="text-base font-semibold text-gray-500 mb-4">AI Recommendations</h5>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="flex items-start p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                                <i class="fas fa-star text-yellow-600 text-sm"></i>
                            </div>
                            <div>
                                <div class="text-sm font-medium text-gray-900 mb-1">Priority</div>
                                <div class="text-sm text-gray-600">${recommendations.priority || 'Medium'}</div>
                            </div>
                        </div>
                        
                        <div class="flex items-start p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                                <i class="fas fa-cog text-blue-600 text-sm"></i>
                            </div>
                            <div>
                                <div class="text-sm font-medium text-gray-900 mb-1">Implementation</div>
                                <div class="text-sm text-gray-600">${recommendations.implementation_readiness || 'Review Needed'}</div>
                            </div>
                        </div>
                        
                        <div class="flex items-start p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                                <i class="fas fa-cloud text-green-600 text-sm"></i>
                            </div>
                            <div>
                                <div class="text-sm font-medium text-gray-900 mb-1">Azure Optimizations</div>
                                <div class="text-sm text-gray-600">${recommendations.azure_optimizations_available ? 'Available' : 'Not Available'}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Helper methods
    updateStatusBadge(elementId, enabled) {
        const element = document.getElementById(elementId);
        if (!element) return;

        if (enabled) {
            element.textContent = 'Enabled';
            element.className = 'ml-auto px-3 py-1 text-xs rounded-full bg-green-100 text-green-800 border border-green-200';
        } else {
            element.textContent = 'Disabled';
            element.className = 'ml-auto px-3 py-1 text-xs rounded-full bg-red-100 text-red-800 border border-red-200';
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

    getRiskBadgeClass(riskLevel) {
        const level = (riskLevel || '').toLowerCase();
        switch (level) {
            case 'high': return 'bg-red-100 text-red-800 border border-red-200';
            case 'medium': return 'bg-yellow-100 text-yellow-800 border border-yellow-200';
            case 'low': return 'bg-green-100 text-green-800 border border-green-200';
            default: return 'bg-gray-100 text-gray-800 border border-gray-200';
        }
    }

    exportFrameworkData() {
        if (!this.frameworkData) {
            alert('No framework data available to export');
            return;
        }

        const dataStr = JSON.stringify(this.frameworkData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `project-controls-${this.clusterId}-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
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
        console.warn('No project controls data available');
    }
};