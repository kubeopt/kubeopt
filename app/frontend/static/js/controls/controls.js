/**
 * FIXED Project Controls Frontend - Themed & With Commands
 * Matches app theme and displays commands properly
 */

class FixedProjectControlsManager {
    constructor() {
        this.clusterId = null;
        this.frameworkData = null;
        this.isLoading = false;
        
        this.initializeEventListeners();
        this.setupDebugging();
    }

    setupDebugging() {
        window.projectControlsDebug = true;
        console.log('🔧 FIXED Project Controls Manager initialized');
    }

    initializeEventListeners() {
        // Refresh button
        document.getElementById('refresh-controls')?.addEventListener('click', () => {
            this.loadProjectControls();
        });

        // Export button
        document.getElementById('export-controls')?.addEventListener('click', () => {
            this.exportFrameworkData();
        });

        // Debug button
        document.getElementById('debug-controls')?.addEventListener('click', () => {
            this.debugFrameworkData();
        });
    }

    /**
     * Load project controls with comprehensive debugging
     */
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
            console.log('🔄 FIXED: Loading project controls for cluster:', this.clusterId);
            
            // Fetch from FIXED endpoint
            const response = await fetch(`/api/project-controls?cluster_id=${this.clusterId}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load project controls: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            
            // COMPREHENSIVE DEBUGGING
            console.group('🐛 FIXED PROJECT CONTROLS DEBUG');
            console.log('📊 COMPLETE DATA RECEIVED:', data);
            console.log('🔍 Framework components:', Object.keys(data.framework || {}));
            console.log('📋 Execution plan:', data.execution_plan);
            console.log('🎯 ML Confidence:', data.ml_confidence);
            console.log('🛠️ Commands extracted:', data.commands_extracted);
            console.log('📈 Debug info:', data.debug_info);
            
            // Log each framework component
            if (data.framework) {
                console.group('🔧 FRAMEWORK COMPONENTS WITH COMMANDS');
                Object.entries(data.framework).forEach(([key, value]) => {
                    console.log(`📋 ${key}:`, value);
                    if (value && value.commands_available) {
                        console.log(`   🛠️ Commands Available: ${value.total_commands} commands in ${value.total_command_groups} groups`);
                        if (value.related_commands) {
                            value.related_commands.forEach((cmd, idx) => {
                                console.log(`     Group ${idx + 1}: ${cmd.phase_title} (${cmd.total_commands} commands)`);
                            });
                        }
                    } else {
                        console.log(`   ⚠️ No commands available for ${key}`);
                    }
                });
                console.groupEnd();
            }
            console.groupEnd();
            
            if (data.status === 'error') {
                console.error('❌ API returned error:', data.message);
                throw new Error(data.message || 'Unknown error occurred');
            }

            this.frameworkData = data;
            this.renderFixedFrameworkComponents();
            this.hideLoading();
            
            console.log('✅ FIXED: Project controls loaded successfully with commands');

        } catch (error) {
            console.error('❌ Error loading FIXED project controls:', error);
            this.showError(error.message);
            this.hideLoading();
        }
    }

    debugFrameworkData() {
        if (!this.frameworkData) {
            console.warn('⚠️ No framework data to debug');
            return;
        }

        console.group('🐛 DETAILED FRAMEWORK DEBUG');
        console.log('📊 Complete Data Object:', this.frameworkData);
        console.log('🔍 Components Found:', this.frameworkData.components_found);
        console.log('📋 Commands Extracted:', this.frameworkData.commands_extracted);
        
        if (this.frameworkData.framework) {
            Object.entries(this.frameworkData.framework).forEach(([key, component]) => {
                console.group(`🔧 ${key.toUpperCase()}`);
                console.log('Component Data:', component);
                if (component.related_commands) {
                    console.log('Related Commands:', component.related_commands);
                }
                console.groupEnd();
            });
        }
        console.groupEnd();
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

    /**
     * Render framework components with FIXED theme and commands
     */
    renderFixedFrameworkComponents() {
        if (!this.frameworkData || !this.frameworkData.framework) {
            this.showError('No framework data available');
            return;
        }

        console.log('🎨 FIXED: Rendering themed components with commands...');

        // Update overview metrics
        this.updateFixedOverviewMetrics();

        // Render each component with commands
        this.renderFixedCostProtection();
        this.renderFixedGovernanceFramework();
        this.renderFixedMonitoringStrategy();
        this.renderFixedRiskMitigation();
        this.renderFixedContingencyPlanning();
        this.renderFixedSuccessCriteria();
        this.renderFixedTimelineOptimization();
        this.renderFixedIntelligenceInsights();

        // Render execution plan
        this.renderFixedExecutionPlan();
    }

    updateFixedOverviewMetrics() {
        const framework = this.frameworkData.framework || {};
        
        // Count enabled controls
        const enabledControls = Object.values(framework).filter(control => 
            control && control.enabled === true
        ).length;

        // Get ML confidence (handle > 1.0 values)
        let mlConfidence = this.frameworkData.ml_confidence || 0;
        if (mlConfidence > 1) mlConfidence = mlConfidence / 1; // Keep as percentage if > 100%
        const mlConfidencePercent = Math.round(mlConfidence * 100);

        // Get governance level
        const governance = framework.governance_framework || {};
        const governanceLevel = governance.governanceLevel || 'Standard';

        // Get total commands
        const totalCommands = Object.values(framework).reduce((sum, component) => {
            return sum + (component.total_commands || 0);
        }, 0);

        // Update UI elements
        this.updateElement('enabled-controls-count', `${enabledControls}/8`);
        this.updateElement('ml-confidence-score', `${mlConfidencePercent}%`);
        this.updateElement('governance-level', governanceLevel);
        
        // Add commands count if element exists
        const commandsElement = document.getElementById('total-commands-count');
        if (commandsElement) {
            commandsElement.textContent = totalCommands;
        }

        console.log(`📊 FIXED Overview: ${enabledControls}/8 controls, ${mlConfidencePercent}% ML confidence, ${totalCommands} total commands`);
    }

    /**
     * Get component data with proper error handling
     */
    getComponentData(primaryKey, fallbackKey = null) {
        const framework = this.frameworkData.framework || {};
        const component = framework[primaryKey] || (fallbackKey ? framework[fallbackKey] : null) || {};
        
        console.log(`🔍 FIXED: Getting ${primaryKey}:`, component);
        return component;
    }

    /**
     * Render Cost Protection with FIXED theme and commands
     */
    renderFixedCostProtection() {
        const costProtection = this.getComponentData('cost_protection', 'costProtection');
        
        console.log('🔒 FIXED: Rendering Cost Protection with commands:', costProtection);
        this.updateStatusBadge('cost-protection-status', costProtection.enabled);
        
        const content = document.getElementById('cost-protection-content');
        if (!content) return;

        const budgetLimits = costProtection.budgetLimits || {};
        const savingsProtection = costProtection.savingsProtection || {};
        const relatedCommands = costProtection.related_commands || [];

        content.innerHTML = `
            <div class="space-y-4">
                <!-- Budget & Savings Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg">
                        <h4 class="font-semibold text-green-400 mb-3 flex items-center">
                            <i class="fas fa-dollar-sign mr-2"></i>Budget Limits
                        </h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between text-gray-300">
                                <span>Monthly Budget:</span>
                                <span class="font-medium text-white">$${this.formatNumber(budgetLimits.monthlyBudget || 0)}</span>
                            </div>
                            <div class="flex justify-between text-gray-300">
                                <span>Alert Threshold:</span>
                                <span class="font-medium text-yellow-400">$${this.formatNumber(budgetLimits.alertThreshold || 0)}</span>
                            </div>
                            <div class="flex justify-between text-gray-300">
                                <span>Hard Limit:</span>
                                <span class="font-medium text-red-400">$${this.formatNumber(budgetLimits.hardLimit || 0)}</span>
                            </div>
                        </div>
                    </div>
                    <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg">
                        <h4 class="font-semibold text-blue-400 mb-3 flex items-center">
                            <i class="fas fa-piggy-bank mr-2"></i>Savings Protection
                        </h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between text-gray-300">
                                <span>Target Savings:</span>
                                <span class="font-medium text-white">$${this.formatNumber(savingsProtection.minimumSavingsTarget || 0)}</span>
                            </div>
                            <div class="flex justify-between text-gray-300">
                                <span>Predicted Savings:</span>
                                <span class="font-medium text-green-400">$${this.formatNumber(savingsProtection.predicted_savings || 0)}</span>
                            </div>
                            <div class="flex justify-between text-gray-300">
                                <span>Opportunities:</span>
                                <span class="font-medium text-white">${savingsProtection.optimization_opportunities_identified || 0}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Commands Section -->
                ${this.renderCommandsSection(relatedCommands, 'Cost Protection Commands')}

                <!-- ML Enhancement Status -->
                <div class="p-3 bg-gray-800/50 border border-gray-600 rounded-lg">
                    <div class="flex items-center justify-between text-sm">
                        <div class="flex items-center text-gray-300">
                            <i class="fas fa-robot text-blue-400 mr-2"></i>
                            <span>ML Enhanced: ${costProtection.ml_derived ? 'Yes' : 'No'}</span>
                            ${costProtection.ml_confidence ? `<span class="ml-4">Confidence: ${Math.round(costProtection.ml_confidence * 100)}%</span>` : ''}
                        </div>
                        <div class="flex items-center text-xs">
                            <i class="fas fa-database text-teal-400 mr-1"></i>
                            <span class="text-gray-400">Commands: ${costProtection.total_commands || 0}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render commands section with proper theme
     */
    renderCommandsSection(relatedCommands, title) {
        if (!relatedCommands || relatedCommands.length === 0) {
            return `
                <div class="p-4 bg-gray-700/30 border border-gray-600 rounded-lg">
                    <h4 class="font-semibold text-gray-400 mb-2 flex items-center">
                        <i class="fas fa-terminal mr-2"></i>${title}
                    </h4>
                    <p class="text-sm text-gray-500">No commands available for this component.</p>
                </div>
            `;
        }

        return `
            <div class="p-4 bg-gray-700/30 border border-gray-600 rounded-lg">
                <h4 class="font-semibold text-teal-400 mb-3 flex items-center">
                    <i class="fas fa-terminal mr-2"></i>${title} (${relatedCommands.length} groups)
                </h4>
                <div class="space-y-3">
                    ${relatedCommands.map((cmdGroup, idx) => `
                        <div class="border border-gray-600 rounded-lg">
                            <div class="p-3 bg-gray-800/50 border-b border-gray-600">
                                <div class="flex justify-between items-center">
                                    <h5 class="font-medium text-white text-sm">${cmdGroup.phase_title}</h5>
                                    <div class="flex items-center space-x-2 text-xs">
                                        <span class="px-2 py-1 bg-teal-600/20 text-teal-400 rounded">${cmdGroup.week_range}</span>
                                        <span class="text-gray-400">${cmdGroup.total_commands} commands</span>
                                    </div>
                                </div>
                            </div>
                            <div class="p-3">
                                <div class="space-y-2">
                                    ${cmdGroup.commands.slice(0, 2).map(cmd => `
                                        <div class="bg-gray-900/50 border border-gray-700 rounded p-2">
                                            <h6 class="text-xs font-medium text-teal-300 mb-1">${cmd.title}</h6>
                                            <p class="text-xs text-gray-400">${cmd.command_count} commands available</p>
                                        </div>
                                    `).join('')}
                                    ${cmdGroup.commands.length > 2 ? `
                                        <div class="text-xs text-gray-500 text-center py-1">
                                            +${cmdGroup.commands.length - 2} more command groups...
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Render Intelligence Insights with FIXED structure
     */
    renderFixedIntelligenceInsights() {
        const intelligence = this.getComponentData('intelligence_insights', 'intelligenceInsights');
        
        console.log('🧠 FIXED: Rendering Intelligence Insights:', intelligence);
        this.updateStatusBadge('intelligence-status', intelligence.enabled);
        
        const content = document.getElementById('intelligence-content');
        if (!content) return;

        const clusterProfile = intelligence.clusterProfile || {};
        const mlPredictions = intelligence.ml_predictions || {};
        const recommendations = intelligence.recommendations || {};

        content.innerHTML = `
            <div class="space-y-4">
                <!-- Intelligence Metrics Grid -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div class="text-center p-3 bg-gray-700/50 border border-gray-600 rounded-lg">
                        <div class="font-bold text-lg text-purple-400">${Math.round((intelligence.analysisConfidence || 0) * 100)}%</div>
                        <div class="text-xs text-gray-400">Analysis Confidence</div>
                    </div>
                    <div class="text-center p-3 bg-gray-700/50 border border-gray-600 rounded-lg">
                        <div class="font-bold text-lg text-blue-400">${intelligence.actual_cv_score ? (intelligence.actual_cv_score * 100).toFixed(1) : 0}%</div>
                        <div class="text-xs text-gray-400">CV Score</div>
                    </div>
                    <div class="text-center p-3 bg-gray-700/50 border border-gray-600 rounded-lg">
                        <div class="font-bold text-lg text-green-400">${intelligence.dataAvailable ? 'Yes' : 'No'}</div>
                        <div class="text-xs text-gray-400">Data Available</div>
                    </div>
                    <div class="text-center p-3 bg-gray-700/50 border border-gray-600 rounded-lg">
                        <div class="font-bold text-lg text-teal-400">${intelligence.azure_enhanced ? 'Yes' : 'No'}</div>
                        <div class="text-xs text-gray-400">Azure Enhanced</div>
                    </div>
                </div>

                <!-- Detailed Analysis Sections -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg">
                        <h4 class="font-semibold text-pink-400 mb-3 flex items-center">
                            <i class="fas fa-brain mr-2"></i>Cluster Profile
                        </h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between text-gray-300">
                                <span>ML Cluster Type:</span>
                                <span class="font-medium text-white">${clusterProfile.mlClusterType || 'Unknown'}</span>
                            </div>
                            <div class="flex justify-between text-gray-300">
                                <span>Complexity Score:</span>
                                <span class="font-medium text-white">${clusterProfile.complexityScore || 0}</span>
                            </div>
                            <div class="flex justify-between text-gray-300">
                                <span>Readiness Score:</span>
                                <span class="font-medium text-green-400">${Math.round((clusterProfile.readinessScore || 0) * 100)}%</span>
                            </div>
                        </div>
                    </div>
                    <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg">
                        <h4 class="font-semibold text-blue-400 mb-3 flex items-center">
                            <i class="fas fa-chart-line mr-2"></i>ML Predictions
                        </h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between text-gray-300">
                                <span>Confidence:</span>
                                <span class="font-medium text-white">${Math.round((mlPredictions.confidence || 0) * 100)}%</span>
                            </div>
                            <div class="flex justify-between text-gray-300">
                                <span>Model Performance:</span>
                                <span class="font-medium text-white">${mlPredictions.model_performance || 'Unknown'}</span>
                            </div>
                            <div class="flex items-center justify-between text-gray-300">
                                <span>Learning Enabled:</span>
                                <span class="flex items-center">
                                    <i class="fas fa-${mlPredictions.learning_enabled ? 'check text-green-400' : 'times text-red-400'} mr-1"></i>
                                    <span class="text-white">${mlPredictions.learning_enabled ? 'Yes' : 'No'}</span>
                                </span>
                            </div>
                        </div>
                    </div>
                    <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg">
                        <h4 class="font-semibold text-green-400 mb-3 flex items-center">
                            <i class="fas fa-lightbulb mr-2"></i>Recommendations
                        </h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between text-gray-300">
                                <span>Priority:</span>
                                <span class="font-medium text-white">${recommendations.priority || 'Medium'}</span>
                            </div>
                            <div class="flex justify-between text-gray-300">
                                <span>Implementation Readiness:</span>
                                <span class="font-medium text-white">${recommendations.implementation_readiness || 'Unknown'}</span>
                            </div>
                            <div class="flex justify-between text-gray-300">
                                <span>Azure Optimizations:</span>
                                <span class="font-medium text-teal-400">${recommendations.azure_optimizations_available ? 'Available' : 'Not Available'}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Commands Section for Intelligence -->
                ${this.renderCommandsSection(intelligence.related_commands || [], 'Intelligence Commands')}

                <!-- Enhancement Status -->
                <div class="p-3 bg-gray-800/50 border border-gray-600 rounded-lg">
                    <div class="flex items-center justify-between text-sm">
                        <div class="flex items-center text-gray-300">
                            <i class="fas fa-brain text-pink-400 mr-2"></i>
                            <span>ML Generated: ${intelligence.improved_ml_generated ? 'Yes' : 'No'}</span>
                            <span class="ml-4">Updated: ${intelligence.lastUpdated ? new Date(intelligence.lastUpdated).toLocaleDateString() : 'Unknown'}</span>
                        </div>
                        <div class="flex items-center text-xs">
                            <i class="fas fa-cogs text-teal-400 mr-1"></i>
                            <span class="text-gray-400">Opportunities: ${intelligence.optimization_opportunities || 0}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render execution plan with FIXED theme
     */
    renderFixedExecutionPlan() {
        const executionPlan = this.frameworkData.execution_plan;
        if (!executionPlan) return;

        console.log('🎯 FIXED: Rendering Execution Plan:', executionPlan);

        // Create execution plan section
        const mainContent = document.getElementById('controls-main-content');
        if (!mainContent) return;

        // Remove existing execution plan
        const existingPlan = document.getElementById('execution-plan-section');
        if (existingPlan) {
            existingPlan.remove();
        }

        const timeline = executionPlan.timeline_summary || {};
        const phases = executionPlan.phases || [];
        const metadata = executionPlan.metadata || {};

        const executionSection = document.createElement('div');
        executionSection.id = 'execution-plan-section';
        executionSection.innerHTML = `
            <div class="bg-gray-800 border border-gray-700 rounded-lg shadow-lg p-6 mt-6">
                <h3 class="text-lg font-semibold text-white mb-4 flex items-center">
                    <i class="fas fa-tasks text-teal-400 mr-2"></i>
                    Execution Plan
                </h3>
                <div class="space-y-6">
                    <!-- Timeline Summary -->
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="text-center p-3 bg-gray-700/50 border border-gray-600 rounded-lg">
                            <div class="font-bold text-lg text-blue-400">${timeline.totalWeeks || 0}</div>
                            <div class="text-sm text-gray-400">Total Weeks</div>
                        </div>
                        <div class="text-center p-3 bg-gray-700/50 border border-gray-600 rounded-lg">
                            <div class="font-bold text-lg text-green-400">${timeline.totalPhases || 0}</div>
                            <div class="text-sm text-gray-400">Total Phases</div>
                        </div>
                        <div class="text-center p-3 bg-gray-700/50 border border-gray-600 rounded-lg">
                            <div class="font-bold text-lg text-purple-400">${metadata.total_command_groups || 0}</div>
                            <div class="text-sm text-gray-400">Command Groups</div>
                        </div>
                        <div class="text-center p-3 bg-gray-700/50 border border-gray-600 rounded-lg">
                            <div class="font-bold text-lg text-yellow-400">$${this.formatNumber(timeline.totalSavings || 0)}</div>
                            <div class="text-sm text-gray-400">Total Savings</div>
                        </div>
                    </div>

                    <!-- Phases Overview -->
                    ${phases.length > 0 ? `
                    <div class="space-y-3">
                        <h4 class="font-semibold text-white flex items-center">
                            <i class="fas fa-list text-teal-400 mr-2"></i>
                            Implementation Phases (${phases.length})
                        </h4>
                        <div class="space-y-2 max-h-64 overflow-y-auto">
                            ${phases.map(phase => `
                                <div class="p-3 bg-gray-700/30 border border-gray-600 rounded-lg">
                                    <div class="flex justify-between items-start">
                                        <div class="flex-1">
                                            <h5 class="font-medium text-white text-sm">${phase.title || 'Unnamed Phase'}</h5>
                                            <p class="text-xs text-gray-400 mt-1">
                                                Week ${phase.week_range} • ${phase.type?.join(', ') || 'General'}
                                            </p>
                                        </div>
                                        <div class="text-right ml-4">
                                            <div class="text-sm font-medium text-green-400">$${this.formatNumber(phase.projected_savings || 0)}</div>
                                            <div class="text-xs text-gray-400">${phase.tasks_count || 0} tasks</div>
                                        </div>
                                    </div>
                                    <div class="mt-2 flex items-center justify-between">
                                        <span class="px-2 py-1 text-xs bg-${this.getRiskColor(phase.risk_level)}-600/20 text-${this.getRiskColor(phase.risk_level)}-400 border border-${this.getRiskColor(phase.risk_level)}-600/30 rounded">
                                            ${phase.risk_level || 'Unknown'} Risk
                                        </span>
                                        <div class="flex items-center text-xs text-gray-400">
                                            <i class="fas fa-${phase.commands_available ? 'check text-green-400' : 'times text-red-400'} mr-1"></i>
                                            Commands ${phase.commands_available ? 'Available' : 'Not Available'}
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}

                    <!-- Metadata -->
                    <div class="p-3 bg-gray-800/50 border border-gray-600 rounded-lg">
                        <div class="flex items-center justify-between text-sm text-gray-400">
                            <span>Execution plan extracted: ${metadata.extracted_at ? new Date(metadata.extracted_at).toLocaleString() : 'Unknown'}</span>
                            <span>Phases with commands: ${metadata.phases_with_commands || 0}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        mainContent.appendChild(executionSection);
    }

    getRiskColor(riskLevel) {
        const level = (riskLevel || '').toLowerCase();
        switch (level) {
            case 'high': return 'red';
            case 'medium': return 'yellow';
            case 'low': return 'green';
            default: return 'gray';
        }
    }

    updateStatusBadge(elementId, enabled) {
        const element = document.getElementById(elementId);
        if (!element) return;

        if (enabled) {
            element.textContent = 'Enabled';
            element.className = 'ml-auto px-2 py-1 text-xs rounded-full bg-green-600/20 text-green-400 border border-green-600/30';
        } else {
            element.textContent = 'Disabled';
            element.className = 'ml-auto px-2 py-1 text-xs rounded-full bg-red-600/20 text-red-400 border border-red-600/30';
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
        if (!this.frameworkData) {
            alert('No framework data available to export');
            return;
        }

        const dataStr = JSON.stringify(this.frameworkData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `fixed-project-controls-${this.clusterId}-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    }

    // Simplified render methods for other components (keeping core structure)
    renderFixedGovernanceFramework() {
        const governance = this.getComponentData('governance_framework', 'governance');
        this.updateStatusBadge('governance-status', governance.enabled);
        
        const content = document.getElementById('governance-content');
        if (!content) return;

        content.innerHTML = `
            <div class="space-y-4">
                <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg">
                    <h4 class="font-semibold text-blue-400 mb-3">Governance Level: ${governance.governanceLevel || 'Standard'}</h4>
                    <div class="text-sm text-gray-300">
                        <p>Cluster Complexity: ${governance.cluster_complexity || 'Unknown'}</p>
                        <p>ML Confidence: ${Math.round((governance.ml_confidence || 0) * 100)}%</p>
                    </div>
                </div>
                ${this.renderCommandsSection(governance.related_commands || [], 'Governance Commands')}
            </div>
        `;
    }

    renderFixedMonitoringStrategy() {
        const monitoring = this.getComponentData('monitoring_strategy', 'monitoring');
        this.updateStatusBadge('monitoring-status', monitoring.enabled);
        
        const content = document.getElementById('monitoring-content');
        if (!content) return;

        content.innerHTML = `
            <div class="space-y-4">
                <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg">
                    <h4 class="font-semibold text-yellow-400 mb-3">Monitoring Configuration</h4>
                    <div class="text-sm text-gray-300">
                        <p>Frequency: ${monitoring.monitoringFrequency || 'Standard'}</p>
                        <p>Scaling Readiness: ${monitoring.scaling_readiness || 'Unknown'}</p>
                        <p>Key Metrics: ${(monitoring.keyMetrics || []).length} configured</p>
                    </div>
                </div>
                ${this.renderCommandsSection(monitoring.related_commands || [], 'Monitoring Commands')}
            </div>
        `;
    }

    renderFixedRiskMitigation() {
        const riskMitigation = this.getComponentData('risk_mitigation', 'riskMitigation');
        this.updateStatusBadge('risk-status', riskMitigation.enabled);
        
        const content = document.getElementById('risk-content');
        if (!content) return;

        content.innerHTML = `
            <div class="space-y-4">
                <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg">
                    <h4 class="font-semibold text-red-400 mb-3">Risk Assessment</h4>
                    <div class="text-sm text-gray-300">
                        <p>Security Posture: ${riskMitigation.security_posture || 'Unknown'}</p>
                        <p>Identified Risks: ${(riskMitigation.identifiedRisks || []).length}</p>
                        <p>Model Confidence: ${Math.round((riskMitigation.ml_confidence || 0) * 100)}%</p>
                    </div>
                </div>
                ${this.renderCommandsSection(riskMitigation.related_commands || [], 'Risk Mitigation Commands')}
            </div>
        `;
    }

    renderFixedContingencyPlanning() {
        const contingency = this.getComponentData('contingency_planning', 'contingency');
        this.updateStatusBadge('contingency-status', contingency.enabled);
        
        const content = document.getElementById('contingency-content');
        if (!content) return;

        content.innerHTML = `
            <div class="space-y-4">
                <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg">
                    <h4 class="font-semibold text-orange-400 mb-3">Contingency Configuration</h4>
                    <div class="text-sm text-gray-300">
                        <p>Triggers: ${(contingency.contingencyTriggers || []).length} configured</p>
                        <p>Rollback Time: ${contingency.rollbackProcedures?.rollback_time_estimate || 'Unknown'}</p>
                        <p>Auto Rollback: ${contingency.rollbackProcedures?.automated_rollback_available ? 'Available' : 'Not Available'}</p>
                    </div>
                </div>
                ${this.renderCommandsSection(contingency.related_commands || [], 'Contingency Commands')}
            </div>
        `;
    }

    renderFixedSuccessCriteria() {
        const successCriteria = this.getComponentData('success_criteria', 'successCriteria');
        this.updateStatusBadge('success-status', successCriteria.enabled);
        
        const content = document.getElementById('success-content');
        if (!content) return;

        content.innerHTML = `
            <div class="space-y-4">
                <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg">
                    <h4 class="font-semibold text-green-400 mb-3">Success Targets</h4>
                    <div class="text-sm text-gray-300">
                        <p>Monthly Target: $${this.formatNumber(successCriteria.financialTargets?.monthly_savings_target || 0)}</p>
                        <p>Opportunities: ${successCriteria.financialTargets?.optimization_opportunities_addressed || 0}</p>
                        <p>Zero Downtime: ${successCriteria.technicalTargets?.zero_downtime_during_implementation ? 'Required' : 'Not Required'}</p>
                    </div>
                </div>
                ${this.renderCommandsSection(successCriteria.related_commands || [], 'Success Criteria Commands')}
            </div>
        `;
    }

    renderFixedTimelineOptimization() {
        const timelineOpt = this.getComponentData('timeline_optimization', 'timelineOptimization');
        this.updateStatusBadge('timeline-status', timelineOpt.enabled);
        
        const content = document.getElementById('timeline-content');
        if (!content) return;

        content.innerHTML = `
            <div class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg text-center">
                        <div class="text-2xl font-bold text-indigo-400 mb-1">
                            ${timelineOpt.originalTimelineWeeks || 0}
                        </div>
                        <div class="text-sm text-gray-400">Original Weeks</div>
                    </div>
                    <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg text-center">
                        <div class="text-2xl font-bold text-green-400 mb-1">
                            ${timelineOpt.optimizedTimelineWeeks || 0}
                        </div>
                        <div class="text-sm text-gray-400">Optimized Weeks</div>
                    </div>
                    <div class="p-4 bg-gray-700/50 border border-gray-600 rounded-lg text-center">
                        <div class="text-2xl font-bold text-purple-400 mb-1">
                            ${timelineOpt.cluster_complexity_factor ? (timelineOpt.cluster_complexity_factor * 100).toFixed(0) + '%' : '100%'}
                        </div>
                        <div class="text-sm text-gray-400">Complexity Factor</div>
                    </div>
                </div>
                ${this.renderCommandsSection(timelineOpt.related_commands || [], 'Timeline Commands')}
            </div>
        `;
    }
}

// Initialize Fixed Project Controls Manager
let fixedProjectControlsManager;

document.addEventListener('DOMContentLoaded', function() {
    fixedProjectControlsManager = new FixedProjectControlsManager();
    console.log('✅ FIXED Project Controls Manager ready with theming and commands');
});

function loadProjectControlsTab() {
    if (fixedProjectControlsManager && !fixedProjectControlsManager.isLoading) {
        fixedProjectControlsManager.loadProjectControls();
    }
}

window.debugProjectControls = function() {
    if (fixedProjectControlsManager) {
        fixedProjectControlsManager.debugFrameworkData();
    } else {
        console.warn('⚠️ FIXED Project Controls Manager not initialized');
    }
};