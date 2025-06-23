/**
 * ============================================================================
 * AKS COST INTELLIGENCE - ENHANCED IMPLEMENTATION PLAN MANAGER
 * ============================================================================
 * Complete implementation plan management with rich data rendering,
 * collapsible sections, command execution, and comprehensive monitoring
 * ============================================================================
 */

import { showNotification } from './notifications.js';
import { escapeHtml, getPriorityColor, getRiskColor } from './utils.js';
import { copyCommand } from './copy-functionality.js';

/**
 * Main function to load and display implementation plan
 */
export function loadImplementationPlan() {
    console.log('📋 Enhanced: Loading implementation plan with cluster isolation...');
    
    // Import cluster isolation functions
    const validateClusterContext = window.validateClusterContext || (() => true);
    const makeClusterAwareAPICall = window.makeClusterAwareAPICall || fetch;
    
    if (!validateClusterContext('loadImplementationPlan')) {
        console.error('❌ BLOCKED: loadImplementationPlan - invalid cluster context');
        return;
    }
    
    const container = document.getElementById('implementation-plan-container');
    if (!container) {
        console.error('❌ Implementation plan container not found!');
        return;
    }
    
    // Show enhanced loading state
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
            <h5 class="text-primary">Loading Implementation Plan for Current Cluster...</h5>
            <p class="text-muted">Analyzing your cluster to generate personalized implementation recommendations...</p>
            <div class="mt-3">
                <div class="progress" style="height: 6px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
                </div>
            </div>
        </div>
    `;

    console.log('📤 Fetching cluster-specific implementation plan from API...');
    
    // Use cluster-aware API call
    makeClusterAwareAPICall('/api/implementation-plan')
        .then(response => {
            console.log('📡 Implementation Plan API Response Status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(planData => {
            console.log('📊 Cluster-specific implementation plan data received:', planData);
            
            // Validate cluster metadata in response
            if (planData.api_metadata && planData.api_metadata.cluster_id) {
                const responseClusterId = planData.api_metadata.cluster_id;
                const currentClusterId = window.getCurrentClusterId ? window.getCurrentClusterId() : null;
                
                if (currentClusterId && responseClusterId !== currentClusterId) {
                    console.error('🚨 CLUSTER MISMATCH in implementation plan response!');
                    throw new Error('Implementation plan cluster mismatch - possible data contamination');
                }
                
                console.log(`✅ Implementation plan cluster validated: ${responseClusterId}`);
            }
            
            // Check for implementation phases
            if (planData.implementation_phases && planData.implementation_phases.length > 0) {
                console.log(`✅ Found ${planData.implementation_phases.length} implementation phases for current cluster`);
                displayImplementationPlan(planData);
            } else {
                console.warn('⚠️ No implementation phases found in data for current cluster');
                showNoAnalysisMessage(container);
            }
        })
        .catch(error => {
            console.error('❌ Cluster-specific implementation plan loading error:', error);
            displayImplementationError(container, error.message);
        });
}

/**
 * Enhanced display function with complete data rendering
 */
export function displayImplementationPlan(planData) {
    console.log('🎨 Displaying COMPLETE implementation plan with ALL rich data:', planData);
    
    const container = document.getElementById('implementation-plan-container');
    if (!container) {
        console.error('❌ Implementation plan container not found!');
        return;
    }

    const phases = planData.implementation_phases || [];
    const summary = planData.executive_summary || {};
    const intelligence = planData.intelligence_insights || {};
    const governance = planData.governance_framework || {};
    const monitoring = planData.monitoring_strategy || {};
    const contingency = planData.contingency_planning || {};
    const success = planData.success_criteria || {};
    const timeline = planData.timeline_optimization || {};
    const risk = planData.risk_mitigation || {};
    const commands = planData.executable_commands || {};

    if (!phases || phases.length === 0) {
        console.warn('⚠️ No phases found to display');
        showNoAnalysisMessage(container);
        return;
    }

    // Calculate totals
    const totalSavings = phases.reduce((sum, phase) => sum + (phase.projected_savings || 0), 0);
    const totalWeeks = Math.max(...phases.map(phase => phase.end_week || phase.duration_weeks || 0));
    const clusterName = planData.cluster_metadata?.cluster_name || planData.api_metadata?.cluster_name || 'Unknown';
    const resourceGroup = planData.cluster_metadata?.resource_group || planData.api_metadata?.resource_group || 'Unknown';

    let html = `
    <!-- ENHANCED EXECUTIVE HEADER WITH FULL METADATA -->
    <div class="card border-0 shadow-lg mb-4" style="background: linear-gradient(135deg, #28a745, #20c997);">
        <div class="card-body text-white">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                    <h3 class="card-title mb-2">
                        <i class="fas fa-rocket me-2"></i>Complete Implementation Plan Ready!
                    </h3>
                    <div class="cluster-info mb-2">
                        <strong>🎯 Cluster:</strong> ${clusterName} 
                        <span class="mx-2">•</span>
                        <strong>📦 Resource Group:</strong> ${resourceGroup}
                        <span class="mx-2">•</span>
                        <strong>🧠 Strategy:</strong> ${planData.metadata?.strategy_type || 'Conservative'}
                    </div>
                    <small class="opacity-90">
                        Generated: ${new Date(planData.metadata?.generated_at || Date.now()).toLocaleDateString()} 
                        • Intelligence Level: ${planData.metadata?.intelligence_level || 'Advanced'}
                        • Version: ${planData.metadata?.version || '2.0.0'}
                    </small>
                </div>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-light btn-sm" onclick="expandAllImplementationSections()" title="Expand All">
                        <i class="fas fa-expand-alt"></i>
                    </button>
                    <button class="btn btn-outline-light btn-sm" onclick="collapseAllImplementationSections()" title="Collapse All">
                        <i class="fas fa-compress-alt"></i>
                    </button>
                </div>
            </div>
            
            <div class="row g-3">
                <div class="col-6 col-md-2">
                    <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                        <div class="h4 mb-1 text-white">${phases.length}</div>
                        <small class="opacity-90">Phases</small>
                    </div>
                </div>
                <div class="col-6 col-md-2">
                    <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                        <div class="h4 mb-1 text-white">${totalWeeks}</div>
                        <small class="opacity-90">Weeks</small>
                    </div>
                </div>
                <div class="col-6 col-md-2">
                    <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                        <div class="h4 mb-1 text-white">$${totalSavings.toLocaleString()}</div>
                        <small class="opacity-90">Monthly Savings</small>
                    </div>
                </div>
                <div class="col-6 col-md-2">
                    <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                        <div class="h4 mb-1 text-white">${commands.commands_generated || 0}</div>
                        <small class="opacity-90">Commands</small>
                    </div>
                </div>
                <div class="col-6 col-md-2">
                    <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                        <div class="h4 mb-1 text-white">${risk?.overall_risk || 'Low'}</div>
                        <small class="opacity-90">Risk Level</small>
                    </div>
                </div>
                <div class="col-6 col-md-2">
                    <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                        <div class="h4 mb-1 text-white">${Math.round((timeline?.timeline_confidence || 0.8) * 100)}%</div>
                        <small class="opacity-90">Confidence</small>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ENHANCED QUICK OVERVIEW -->
    ${renderEnhancedQuickOverview(summary, intelligence)}
    
    <!-- EXECUTIVE COMMANDS SECTION (HIGH PRIORITY) -->
    ${renderExecutableCommands(planData)}
    
    <!-- IMPLEMENTATION PHASES (ENHANCED) -->
    ${renderEnhancedImplementationPhases(phases)}
    
    <!-- INTELLIGENCE INSIGHTS -->
    ${renderIntelligenceInsights(intelligence)}
    
    <!-- GOVERNANCE FRAMEWORK -->
    ${renderGovernanceFramework(governance)}
    
    <!-- MONITORING STRATEGY -->
    ${renderMonitoringStrategy(monitoring)}
    
    <!-- CONTINGENCY PLANNING -->
    ${renderContingencyPlanning(contingency)}
    
    <!-- SUCCESS CRITERIA -->
    ${renderSuccessCriteria(success)}
    
    <!-- TIMELINE OPTIMIZATION -->
    ${renderTimelineOptimization(timeline)}
    
    <!-- RISK MITIGATION -->
    ${renderRiskMitigation(risk)}
    
    <!-- ACTION BUTTONS -->
    ${renderActionButtons(totalSavings, planData)}
    `;

    container.innerHTML = html;
    initializeImplementationCollapse();
    
    console.log('✅ COMPLETE Implementation plan displayed with ALL rich data');
}

/**
 * Enhanced quick overview with rich data
 */
function renderEnhancedQuickOverview(summary, intelligence) {
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-info text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#enhanced-overview" aria-expanded="false">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">
                        <i class="fas fa-brain me-2"></i>Strategic Overview & AI Insights
                    </h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="enhanced-overview">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6 class="text-primary mb-3"><i class="fas fa-lightbulb me-2"></i>Key Recommendations</h6>
                            ${summary.key_recommendations?.length ? `
                                <ul class="list-unstyled">
                                    ${summary.key_recommendations.map((rec, idx) => `
                                        <li class="mb-2"><i class="fas fa-check-circle text-success me-2"></i>${rec}</li>
                                    `).join('')}
                                </ul>
                            ` : '<p class="text-muted">No specific recommendations available</p>'}
                            
                            <h6 class="text-success mt-4 mb-3"><i class="fas fa-target me-2"></i>Strategic Priorities</h6>
                            ${summary.strategic_priorities?.length ? `
                                <ul class="list-unstyled">
                                    ${summary.strategic_priorities.map(priority => `
                                        <li class="mb-2"><i class="fas fa-star text-warning me-2"></i>${priority}</li>
                                    `).join('')}
                                </ul>
                            ` : '<p class="text-muted">No priorities defined</p>'}
                        </div>
                        <div class="col-md-6">
                            <h6 class="text-purple mb-3"><i class="fas fa-robot me-2"></i>AI Intelligence Analysis</h6>
                            ${renderIntelligenceSummary(intelligence)}
                            
                            <h6 class="text-info mt-4 mb-3"><i class="fas fa-chart-line me-2"></i>Optimization Potential</h6>
                            ${renderOptimizationSummary(summary.optimization_opportunity)}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render executable commands section (HIGH PRIORITY)
 */
function renderExecutableCommands(planData) {
    const commands = planData.executable_commands || {};
    const phases = planData.implementation_phases || [];
    
    // Collect ALL commands from phases
    let allCommands = [];
    phases.forEach((phase, phaseIndex) => {
        if (phase.tasks) {
            phase.tasks.forEach((task, taskIndex) => {
                if (task.command) {
                    allCommands.push({
                        phase: phase.phase_number || (phaseIndex + 1),
                        phaseTitle: phase.title,
                        taskTitle: task.title,
                        command: task.command,
                        description: task.description,
                        id: `cmd-p${phaseIndex}-t${taskIndex}`
                    });
                }
            });
        }
    });
    
    if (allCommands.length === 0) {
        return '';
    }
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-dark text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#executable-commands-section" aria-expanded="true">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">
                        <i class="fas fa-terminal me-2"></i>Executable Commands (${allCommands.length} commands)
                    </h5>
                    <div class="d-flex gap-2 align-items-center">
                        <button class="btn btn-outline-light btn-sm" onclick="copyAllCommands()">
                            <i class="fas fa-copy me-1"></i>Copy All
                        </button>
                        <i class="fas fa-chevron-down collapse-icon"></i>
                    </div>
                </div>
            </div>
            <div class="collapse show" id="executable-commands-section">
                <div class="card-body">
                    <div class="alert alert-info mb-4">
                        <i class="fas fa-info-circle me-2"></i>
                        <strong>Total Commands:</strong> ${allCommands.length} 
                        <span class="mx-2">•</span>
                        <strong>Validation:</strong> ${commands.validation_included ? 'Included' : 'Manual'} 
                        <span class="mx-2">•</span>
                        <strong>Monitoring:</strong> ${commands.monitoring_commands ? 'Automated' : 'Manual'}
                        <span class="mx-2">•</span>
                        <strong>Rollback:</strong> ${commands.rollback_procedures ? 'Available' : 'Manual'}
                    </div>
                    
                    ${allCommands.map((cmd, index) => `
                        <div class="command-block mb-4 border rounded">
                            <div class="command-header p-3 bg-light border-bottom" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#${cmd.id}" aria-expanded="false">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6 class="mb-1">
                                            <span class="badge bg-primary me-2">${index + 1}</span>
                                            Phase ${cmd.phase}: ${cmd.taskTitle}
                                            <i class="fas fa-chevron-down collapse-icon ms-2"></i>
                                        </h6>
                                        <small class="text-muted">${cmd.phaseTitle} • ${cmd.description?.substring(0, 80)}...</small>
                                    </div>
                                    <button class="btn btn-outline-primary btn-sm" onclick="copyCommand('${cmd.id}')">
                                        <i class="fas fa-copy me-1"></i>Copy
                                    </button>
                                </div>
                            </div>
                            <div class="collapse" id="${cmd.id}">
                                <div class="command-content p-3">
                                    <div class="mb-3">
                                        <strong>📝 Description:</strong><br>
                                        <span class="text-muted">${cmd.description}</span>
                                    </div>
                                    <div class="command-wrapper">
                                        <div class="d-flex justify-content-between align-items-center mb-2">
                                            <strong>💻 Command:</strong>
                                            <button class="btn btn-sm btn-outline-success" onclick="copyCommand('${cmd.id}-code')">
                                                <i class="fas fa-copy me-1"></i>Copy Command
                                            </button>
                                        </div>
                                        <pre class="command-code" id="${cmd.id}-code"><code>${escapeHtml(cmd.command)}</code></pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

/**
 * Enhanced phase rendering with better command display
 */
function renderEnhancedImplementationPhases(phases) {
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-primary text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#implementation-phases-section" aria-expanded="true">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">
                        <i class="fas fa-cogs me-2"></i>Implementation Phases (${phases.length} phases)
                    </h5>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse show" id="implementation-phases-section">
                <div class="card-body p-0">
                    ${phases.map((phase, idx) => renderEnhancedPhase(phase, idx)).join('')}
                </div>
            </div>
        </div>
    `;
}

/**
 * Enhanced individual phase rendering
 */
function renderEnhancedPhase(phase, index) {
    const phaseId = `enhanced-phase-${phase.phase_number || index + 1}`;
    
    return `
        <div class="phase-container border-bottom">
            <div class="phase-header p-3" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); cursor: pointer;" 
                 data-bs-toggle="collapse" data-bs-target="#${phaseId}" aria-expanded="false">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="flex-grow-1">
                        <h5 class="mb-2">
                            <i class="fas fa-cog me-2 text-primary"></i>
                            Phase ${phase.phase_number || index + 1}: ${phase.title || 'Untitled Phase'}
                        </h5>
                        <div class="d-flex gap-2 flex-wrap mb-2">
                            <span class="badge bg-light text-dark">${phase.duration_weeks || 'N/A'} weeks</span>
                            <span class="badge bg-success">$${(phase.projected_savings || 0).toLocaleString()}/mo</span>
                            <span class="badge bg-${getPriorityColor(phase.priority_level)}">${phase.priority_level || 'Medium'}</span>
                            <span class="badge bg-info">${(phase.tasks || []).length} tasks</span>
                            <span class="badge bg-warning">${phase.complexity_level || 'Medium'} complexity</span>
                        </div>
                        <small class="text-muted">
                            Week ${phase.start_week || 'N/A'} - ${phase.end_week || 'N/A'} • 
                            ${phase.type || 'Optimization'} • 
                            ${phase.risk_level || 'Low'} Risk
                        </small>
                    </div>
                    <div class="d-flex align-items-center gap-3">
                        <div class="alert alert-success mb-0 py-2 px-3">
                            <div class="text-center">
                                <div class="h5 mb-0">$${(phase.projected_savings || 0).toLocaleString()}</div>
                                <small>Monthly Savings</small>
                            </div>
                        </div>
                        <i class="fas fa-chevron-down collapse-icon text-primary"></i>
                    </div>
                </div>
            </div>
            
            <div class="collapse" id="${phaseId}">
                <div class="card-body">
                    ${renderPhaseDetails(phase, index)}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render detailed phase content
 */
function renderPhaseDetails(phase, index) {
    return `
        <!-- Phase Overview -->
        <div class="row mb-4">
            <div class="col-md-8">
                <h6 class="text-primary mb-3">📊 Phase Overview</h6>
                <div class="row">
                    <div class="col-md-6">
                        <ul class="list-unstyled">
                            <li><strong>Type:</strong> ${phase.type || 'Optimization'}</li>
                            <li><strong>Timeline:</strong> Week ${phase.start_week || 'N/A'} - ${phase.end_week || 'N/A'}</li>
                            <li><strong>Engineering Hours:</strong> ${phase.resource_requirements?.engineering_hours || 'TBD'}</li>
                            <li><strong>FTE Required:</strong> ${phase.resource_requirements?.fte_estimate || 'TBD'}</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <ul class="list-unstyled">
                            <li><strong>Complexity:</strong> ${phase.complexity_level || 'Medium'}</li>
                            <li><strong>Risk Level:</strong> ${phase.risk_level || 'Low'}</li>
                            <li><strong>Priority:</strong> ${phase.priority_level || 'Medium'}</li>
                            <li><strong>Dependencies:</strong> ${phase.dependencies?.length || 0}</li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <h6 class="text-success mb-3">✅ Success Criteria</h6>
                ${phase.success_criteria?.length ? `
                    <ul class="list-unstyled">
                        ${phase.success_criteria.slice(0, 3).map(criteria => `
                            <li class="mb-1"><i class="fas fa-check text-success me-2"></i>${criteria}</li>
                        `).join('')}
                        ${phase.success_criteria.length > 3 ? `<li class="text-muted"><small>+${phase.success_criteria.length - 3} more...</small></li>` : ''}
                    </ul>
                ` : '<p class="text-muted">No success criteria defined</p>'}
            </div>
        </div>

        <!-- Enhanced Tasks Section -->
        ${renderEnhancedTasksSection(phase, index)}
        
        <!-- Other collapsible sections -->
        ${renderCollapsibleValidation(phase, index)}
        ${renderCollapsibleMonitoring(phase, index)}
        ${renderCollapsibleRollback(phase, index)}
    `;
}

/**
 * Enhanced tasks section with better command handling
 */
function renderEnhancedTasksSection(phase, phaseIndex) {
    if (!phase.tasks?.length) return '';
    
    return `
        <div class="mb-4">
            <div class="d-flex justify-content-between align-items-center mb-3" style="cursor: pointer;" 
                 data-bs-toggle="collapse" data-bs-target="#enhanced-tasks-${phaseIndex}" aria-expanded="true">
                <h6 class="text-primary mb-0">
                    <i class="fas fa-tasks me-2"></i>Implementation Tasks (${phase.tasks.length} tasks)
                </h6>
                <i class="fas fa-chevron-down collapse-icon"></i>
            </div>
            
            <div class="collapse show" id="enhanced-tasks-${phaseIndex}">
                <div class="row">
                    ${phase.tasks.map((task, taskIdx) => {
                        const taskId = `enhanced-task-${phaseIndex}-${taskIdx}`;
                        const commandId = `enhanced-cmd-${phaseIndex}-${taskIdx}`;
                        
                        return `
                            <div class="col-12 mb-3">
                                <div class="card border-start border-4 border-primary">
                                    <div class="card-header bg-light" style="cursor: pointer;" 
                                         data-bs-toggle="collapse" data-bs-target="#${taskId}" aria-expanded="false">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div class="flex-grow-1">
                                                <h6 class="mb-1">
                                                    <span class="badge bg-primary me-2">${taskIdx + 1}</span>
                                                    ${task.title || 'Untitled Task'}
                                                    <i class="fas fa-chevron-down collapse-icon ms-2"></i>
                                                </h6>
                                                <small class="text-muted">${task.description?.substring(0, 100)}${task.description?.length > 100 ? '...' : ''}</small>
                                            </div>
                                            <div class="d-flex gap-2">
                                                <span class="badge bg-info">${task.estimated_hours || 'N/A'}h</span>
                                                ${task.command ? `
                                                    <button class="btn btn-sm btn-outline-primary" onclick="copyCommand('${commandId}')">
                                                        <i class="fas fa-copy me-1"></i>Copy
                                                    </button>
                                                ` : ''}
                                            </div>
                                        </div>
                                    </div>
                                    <div class="collapse" id="${taskId}">
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <div class="mb-3">
                                                        <strong>📝 Description:</strong><br>
                                                        <span class="text-muted">${task.description || 'No description available'}</span>
                                                    </div>
                                                    <div class="mb-3">
                                                        <strong>🎯 Expected Outcome:</strong><br>
                                                        <span class="text-muted">${task.expected_outcome || 'N/A'}</span>
                                                    </div>
                                                    
                                                    ${task.skills_required?.length ? `
                                                        <div class="mb-3">
                                                            <strong>🔧 Skills Required:</strong><br>
                                                            ${task.skills_required.map(skill => `<span class="badge bg-secondary me-1 mb-1">${skill}</span>`).join('')}
                                                        </div>
                                                    ` : ''}
                                                    
                                                    ${task.command ? `
                                                        <div class="command-section">
                                                            <div class="d-flex justify-content-between align-items-center mb-2">
                                                                <strong>💻 Command to Execute:</strong>
                                                                <button class="btn btn-sm btn-outline-success" onclick="copyCommand('${commandId}')">
                                                                    <i class="fas fa-copy me-1"></i>Copy Command
                                                                </button>
                                                            </div>
                                                            <div class="command-wrapper">
                                                                <pre class="command-code" id="${commandId}"><code>${escapeHtml(task.command)}</code></pre>
                                                            </div>
                                                        </div>
                                                    ` : '<p class="text-muted">No commands specified for this task</p>'}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        </div>
    `;
}

// =======================================================================
// RICH DATA RENDERING FUNCTIONS
// =======================================================================

/**
 * Render Intelligence Summary
 */
function renderIntelligenceSummary(intelligence) {
    if (!intelligence.cluster_dna_analysis && !intelligence.dynamic_strategy_insights) {
        return '<p class="text-muted">AI analysis not available</p>';
    }
    
    const dna = intelligence.cluster_dna_analysis || {};
    const strategy = intelligence.dynamic_strategy_insights || {};
    
    return `
        <div class="alert alert-light border-start border-4 border-purple">
            <div class="mb-2">
                <strong>🧬 Cluster Personality:</strong> ${dna.cluster_personality?.replace(/-/g, ' ') || 'Unknown'}
            </div>
            <div class="mb-2">
                <strong>📊 Efficiency Score:</strong> ${Math.round((dna.efficiency_score || 0) * 100)}%
            </div>
            <div class="mb-2">
                <strong>🎯 Strategy Type:</strong> ${strategy.strategy_type || 'Conservative'}
            </div>
            <div>
                <strong>📈 Success Probability:</strong> ${Math.round((strategy.success_probability || 0) * 100)}%
            </div>
        </div>
    `;
}

/**
 * Render Optimization Summary
 */
function renderOptimizationSummary(optimization) {
    if (!optimization) {
        return '<p class="text-muted">Optimization data not available</p>';
    }
    
    return `
        <div class="alert alert-light border-start border-4 border-info">
            <div class="mb-2">
                <strong>💰 Current Cost:</strong> $${Math.round(optimization.current_monthly_cost || 0).toLocaleString()}/month
            </div>
            <div class="mb-2">
                <strong>💡 Potential Savings:</strong> $${Math.round(optimization.projected_monthly_savings || 0).toLocaleString()}/month
            </div>
            <div class="mb-2">
                <strong>📊 Optimization %:</strong> ${(optimization.optimization_percentage || 0).toFixed(1)}%
            </div>
            <div>
                <strong>📈 Annual Impact:</strong> $${Math.round(optimization.annual_savings_potential || 0).toLocaleString()}/year
            </div>
        </div>
    `;
}

/**
 * Render Intelligence Insights section
 */
function renderIntelligenceInsights(intelligence) {
    if (!intelligence || Object.keys(intelligence).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-purple text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#intelligence-section" aria-expanded="false">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-brain me-2"></i>AI Intelligence Insights</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="intelligence-section">
                <div class="card-body">
                    ${intelligence.cluster_dna_analysis ? `
                        <div class="mb-4">
                            <h6 class="text-primary"><i class="fas fa-dna me-2"></i>Cluster DNA Analysis</h6>
                            <div class="alert alert-light border-start border-4 border-primary">
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>🧬 Personality:</strong> ${intelligence.cluster_dna_analysis.cluster_personality?.replace(/-/g, ' ') || 'Unknown'}<br>
                                        <strong>📊 Efficiency Score:</strong> ${Math.round((intelligence.cluster_dna_analysis.efficiency_score || 0) * 100)}%<br>
                                        <strong>🎯 Optimization Potential:</strong> ${intelligence.cluster_dna_analysis.optimization_potential || 'Unknown'}
                                    </div>
                                    <div class="col-md-6">
                                        ${intelligence.cluster_dna_analysis.unique_characteristics?.length ? `
                                            <strong>✨ Unique Characteristics:</strong><br>
                                            <ul class="list-unstyled mt-2">
                                                ${intelligence.cluster_dna_analysis.unique_characteristics.map(char => `
                                                    <li><i class="fas fa-star text-warning me-2"></i>${char}</li>
                                                `).join('')}
                                            </ul>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${intelligence.dynamic_strategy_insights ? `
                        <div class="mb-4">
                            <h6 class="text-info"><i class="fas fa-lightbulb me-2"></i>Dynamic Strategy Insights</h6>
                            <div class="alert alert-light border-start border-4 border-info">
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>🎯 Strategy Type:</strong> ${intelligence.dynamic_strategy_insights.strategy_type || 'Conservative'}<br>
                                        <strong>📈 Success Probability:</strong> ${Math.round((intelligence.dynamic_strategy_insights.success_probability || 0) * 100)}%
                                    </div>
                                    <div class="col-md-6">
                                        ${intelligence.dynamic_strategy_insights.priority_areas?.length ? `
                                            <strong>🎯 Priority Areas:</strong><br>
                                            <ul class="list-unstyled mt-2">
                                                ${intelligence.dynamic_strategy_insights.priority_areas.map(area => `
                                                    <li><i class="fas fa-target text-info me-2"></i>${area}</li>
                                                `).join('')}
                                            </ul>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Governance Framework section
 */
function renderGovernanceFramework(governance) {
    if (!governance || Object.keys(governance).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-dark text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#governance-section" aria-expanded="false">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-gavel me-2"></i>Governance Framework</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="governance-section">
                <div class="card-body">
                    ${governance.approval_workflows?.length ? `
                        <div class="mb-4">
                            <h6 class="text-primary"><i class="fas fa-check-circle me-2"></i>Approval Workflows (${governance.approval_workflows.length})</h6>
                            ${governance.approval_workflows.map((workflow, index) => `
                                <div class="alert alert-light border-start border-4 border-primary mb-3">
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <h6 class="mb-0">Workflow ${index + 1}: ${workflow.stage || 'Approval Stage'}</h6>
                                        <span class="badge bg-primary">${workflow.sla || 'Standard SLA'}</span>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <strong>👤 Approver:</strong> ${workflow.approver || 'Team Lead'}<br>
                                            <strong>📋 Requirements:</strong> ${workflow.requirements || 'Standard approval'}
                                        </div>
                                        <div class="col-md-6">
                                            <strong>⏱️ Timeline:</strong> ${workflow.timeline || 'Standard'}<br>
                                            <strong>📝 Documentation:</strong> ${workflow.documentation_required ? 'Required' : 'Optional'}
                                        </div>
                                    </div>
                                    ${workflow.description ? `
                                        <div class="mt-2">
                                            <strong>📄 Description:</strong> ${workflow.description}
                                        </div>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    ${governance.change_management ? `
                        <div class="mb-4">
                            <h6 class="text-warning"><i class="fas fa-exchange-alt me-2"></i>Change Management</h6>
                            <div class="alert alert-light border-start border-4 border-warning">
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>🔄 Process:</strong> ${governance.change_management.process || 'Standard change management'}<br>
                                        <strong>📋 Documentation:</strong> ${governance.change_management.documentation_required ? 'Required' : 'Optional'}
                                    </div>
                                    <div class="col-md-6">
                                        <strong>✅ Testing:</strong> ${governance.change_management.testing_requirements || 'Standard testing'}<br>
                                        <strong>🔙 Rollback Plan:</strong> ${governance.change_management.rollback_required ? 'Required' : 'Optional'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Monitoring Strategy section
 */
function renderMonitoringStrategy(monitoring) {
    if (!monitoring || Object.keys(monitoring).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-warning text-dark" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#monitoring-section" aria-expanded="false">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-chart-bar me-2"></i>Monitoring Strategy</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="monitoring-section">
                <div class="card-body">
                    ${monitoring.health_checks?.length ? `
                        <div class="mb-4">
                            <h6 class="text-danger"><i class="fas fa-heartbeat me-2"></i>Health Checks (${monitoring.health_checks.length})</h6>
                            <div class="row">
                                ${monitoring.health_checks.map(check => `
                                    <div class="col-md-6 mb-2">
                                        <div class="alert alert-light border-start border-4 border-danger">
                                            <i class="fas fa-heartbeat text-danger me-2"></i>${check}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${monitoring.automated_alerting?.length ? `
                        <div class="mb-4">
                            <h6 class="text-warning"><i class="fas fa-bell me-2"></i>Automated Alerting (${monitoring.automated_alerting.length})</h6>
                            ${monitoring.automated_alerting.map((alert, index) => `
                                <div class="alert alert-light border-start border-4 border-warning mb-3">
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <h6 class="mb-0">Alert ${index + 1}: ${alert.metric || 'Monitoring Alert'}</h6>
                                        <span class="badge bg-warning text-dark">${alert.severity || 'Medium'}</span>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-4">
                                            <strong>📊 Metric:</strong> ${alert.metric || 'N/A'}
                                        </div>
                                        <div class="col-md-4">
                                            <strong>🎯 Threshold:</strong> ${alert.threshold || 'N/A'}
                                        </div>
                                        <div class="col-md-4">
                                            <strong>⚡ Action:</strong> ${alert.action || 'Alert'}
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Contingency Planning section
 */
function renderContingencyPlanning(contingency) {
    if (!contingency || Object.keys(contingency).length === 0) return '';
    
    const contingencyTypes = [
        { key: 'business_contingencies', title: 'Business Contingencies', icon: 'briefcase', color: 'primary' },
        { key: 'technical_contingencies', title: 'Technical Contingencies', icon: 'cogs', color: 'info' },
        { key: 'resource_contingencies', title: 'Resource Contingencies', icon: 'users', color: 'warning' },
        { key: 'timeline_contingencies', title: 'Timeline Contingencies', icon: 'clock', color: 'danger' }
    ];
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-secondary text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#contingency-section" aria-expanded="false">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-shield-alt me-2"></i>Contingency Planning</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="contingency-section">
                <div class="card-body">
                    <div class="row">
                        ${contingencyTypes.map(type => {
                            const items = contingency[type.key] || [];
                            if (!items.length) return '';
                            
                            return `
                                <div class="col-md-6 mb-4">
                                    <h6 class="text-${type.color}"><i class="fas fa-${type.icon} me-2"></i>${type.title} (${items.length})</h6>
                                    ${items.map((item, index) => `
                                        <div class="alert alert-light border-start border-4 border-${type.color} mb-3">
                                            <div class="d-flex justify-content-between align-items-center mb-2">
                                                <h6 class="mb-0">Scenario ${index + 1}</h6>
                                                <div class="d-flex gap-1">
                                                    <span class="badge bg-${type.color}">${item.impact || 'Medium'} Impact</span>
                                                    <span class="badge bg-secondary">${item.probability || 'Low'} Probability</span>
                                                </div>
                                            </div>
                                            <div class="mb-2">
                                                <strong>🎯 Scenario:</strong> ${item.scenario || 'Contingency scenario'}
                                            </div>
                                            <div class="mb-2">
                                                <strong>📋 Response:</strong> ${item.response || 'Mitigation response'}
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            `;
                        }).filter(Boolean).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Success Criteria section
 */
function renderSuccessCriteria(success) {
    if (!success || Object.keys(success).length === 0) return '';
    
    const criteriaTypes = [
        { key: 'financial_success_criteria', title: 'Financial Success', icon: 'dollar-sign', color: 'success' },
        { key: 'operational_success_criteria', title: 'Operational Success', icon: 'cogs', color: 'primary' },
        { key: 'performance_success_criteria', title: 'Performance Success', icon: 'tachometer-alt', color: 'info' },
        { key: 'sustainability_metrics', title: 'Sustainability Metrics', icon: 'leaf', color: 'success' }
    ];
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-success text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#success-section" aria-expanded="false">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-target me-2"></i>Success Criteria & Metrics</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="success-section">
                <div class="card-body">
                    <div class="row">
                        ${criteriaTypes.map(type => {
                            const criteria = success[type.key];
                            if (!criteria || typeof criteria !== 'object') return '';
                            
                            return `
                                <div class="col-md-6 mb-4">
                                    <h6 class="text-${type.color}"><i class="fas fa-${type.icon} me-2"></i>${type.title}</h6>
                                    <div class="alert alert-light border-start border-4 border-${type.color}">
                                        ${Object.entries(criteria).map(([key, value]) => `
                                            <div class="mb-2">
                                                <strong>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> ${value}
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            `;
                        }).filter(Boolean).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Timeline Optimization section
 */
function renderTimelineOptimization(timeline) {
    if (!timeline || Object.keys(timeline).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-info text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#timeline-section" aria-expanded="false">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-calendar-alt me-2"></i>Timeline Optimization</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="timeline-section">
                <div class="card-body">
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <div class="alert alert-light border-start border-4 border-info">
                                <h6 class="text-info"><i class="fas fa-calendar me-2"></i>Timeline Details</h6>
                                <div class="mb-2"><strong>📅 Base Timeline:</strong> ${timeline.base_timeline_weeks || 'N/A'} weeks</div>
                                <div class="mb-2"><strong>⚡ Parallelization Benefit:</strong> ${timeline.parallelization_benefit || 0} weeks saved</div>
                                <div class="mb-2"><strong>🔧 Complexity Adjustment:</strong> ${timeline.complexity_adjustment || 0} weeks</div>
                                <div><strong>🎯 Total Timeline:</strong> ${timeline.total_weeks || timeline.base_timeline_weeks || 'N/A'} weeks</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="alert alert-light border-start border-4 border-success">
                                <h6 class="text-success"><i class="fas fa-chart-line me-2"></i>Confidence Metrics</h6>
                                <div class="mb-2"><strong>📊 Timeline Confidence:</strong> ${Math.round((timeline.timeline_confidence || 0.8) * 100)}%</div>
                                <div class="mb-2"><strong>🚀 Risk Adjustment:</strong> ${timeline.risk_adjustment || 0} weeks</div>
                                <div><strong>🎯 Delivery Confidence:</strong> ${timeline.delivery_confidence || 'High'}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Risk Mitigation section
 */
function renderRiskMitigation(risk) {
    if (!risk || Object.keys(risk).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-danger text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#risk-section" aria-expanded="false">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-exclamation-triangle me-2"></i>Risk Mitigation</h6>
                    <span class="badge bg-light text-dark">${risk.overall_risk || 'Low'} Risk</span>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="risk-section">
                <div class="card-body">
                    <div class="row mb-4">
                        <div class="col-md-4">
                            <div class="text-center p-3 rounded" style="background: rgba(220, 53, 69, 0.1);">
                                <div class="h4 mb-1 text-danger">${risk.overall_risk || 'Low'}</div>
                                <small class="text-muted">Overall Risk</small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="text-center p-3 rounded" style="background: rgba(220, 53, 69, 0.1);">
                                <div class="h4 mb-1 text-danger">${Math.round((risk.risk_score || 0.3) * 100)}%</div>
                                <small class="text-muted">Risk Score</small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="text-center p-3 rounded" style="background: rgba(220, 53, 69, 0.1);">
                                <div class="h4 mb-1 text-danger">${risk.mitigation_strategies?.length || 0}</div>
                                <small class="text-muted">Mitigations</small>
                            </div>
                        </div>
                    </div>
                    
                    ${risk.mitigation_strategies?.length ? `
                        <div class="mb-4">
                            <h6 class="text-success"><i class="fas fa-shield-alt me-2"></i>Mitigation Strategies</h6>
                            ${risk.mitigation_strategies.map((strategy, index) => `
                                <div class="alert alert-light border-start border-4 border-success mb-3">
                                    <h6 class="mb-2">Strategy ${index + 1}: ${strategy.title || 'Risk Mitigation'}</h6>
                                    <div class="mb-2"><strong>📋 Description:</strong> ${strategy.description || 'Mitigation strategy'}</div>
                                    <div class="mb-2"><strong>⚡ Implementation:</strong> ${strategy.implementation || 'Standard implementation'}</div>
                                    <div><strong>📊 Effectiveness:</strong> ${strategy.effectiveness || 'High'}</div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Action Buttons section
 */
function renderActionButtons(totalSavings, planData) {
    return `
        <div class="card border-0 shadow mt-4" style="background: linear-gradient(135deg, #f8f9fa, #e9ecef);">
            <div class="card-body text-center">
                <h5 class="mb-3 text-primary">🚀 Ready to Start Implementation?</h5>
                <div class="d-flex gap-2 justify-content-center flex-wrap mb-3">
                    <button class="btn btn-success btn-lg shadow-sm" onclick="deployOptimizations()">
                        <i class="fas fa-rocket me-2"></i>Deploy Phase 1
                    </button>
                    <button class="btn btn-primary btn-lg shadow-sm" onclick="exportImplementationPlan()">
                        <i class="fas fa-download me-2"></i>Export Complete Plan
                    </button>
                    <button class="btn btn-outline-primary btn-lg shadow-sm" onclick="scheduleOptimization()">
                        <i class="fas fa-calendar me-2"></i>Schedule Review
                    </button>
                    <button class="btn btn-outline-secondary btn-lg shadow-sm" onclick="loadImplementationPlan()">
                        <i class="fas fa-redo me-2"></i>Refresh Plan
                    </button>
                </div>
                
                <div class="pt-3 border-top">
                    <div class="row text-center">
                        <div class="col-md-3">
                            <strong class="text-success">$${totalSavings.toLocaleString()}</strong><br>
                            <small class="text-muted">Monthly Savings</small>
                        </div>
                        <div class="col-md-3">
                            <strong class="text-info">${planData.metadata?.confidence_level || 'High'}</strong><br>
                            <small class="text-muted">Confidence Level</small>
                        </div>
                        <div class="col-md-3">
                            <strong class="text-warning">${planData.executable_commands?.commands_generated || 0}</strong><br>
                            <small class="text-muted">Commands Ready</small>
                        </div>
                        <div class="col-md-3">
                            <strong class="text-primary">${planData.implementation_phases?.length || 0}</strong><br>
                            <small class="text-muted">Implementation Phases</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// =======================================================================
// UTILITY AND HELPER FUNCTIONS
// =======================================================================

/**
 * Render collapsible validation section
 */
function renderCollapsibleValidation(phase, index) {
    if (!phase.validation_steps?.length) return '';
    
    return `
        <div class="mb-4">
            <div class="d-flex justify-content-between align-items-center mb-3" 
                 style="cursor: pointer;" 
                 data-bs-toggle="collapse" 
                 data-bs-target="#validation-${index}"
                 aria-expanded="false">
                <h6 class="text-info mb-0">
                    <i class="fas fa-clipboard-check me-2"></i>Validation Steps (${phase.validation_steps.length})
                </h6>
                <i class="fas fa-chevron-down collapse-icon"></i>
            </div>
            <div class="collapse" id="validation-${index}">
                <div class="row">
                    ${phase.validation_steps.map(step => `
                        <div class="col-md-6 mb-2">
                            <div class="d-flex align-items-start">
                                <i class="fas fa-check-circle text-info me-2 mt-1"></i>
                                <span>${step}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render collapsible monitoring section
 */
function renderCollapsibleMonitoring(phase, index) {
    if (!phase.monitoring_requirements) return '';
    
    return `
        <div class="mb-4">
            <div class="d-flex justify-content-between align-items-center mb-3" 
                 style="cursor: pointer;" 
                 data-bs-toggle="collapse" 
                 data-bs-target="#monitoring-${index}"
                 aria-expanded="false">
                <h6 class="text-warning mb-0">
                    <i class="fas fa-chart-line me-2"></i>Monitoring Requirements
                </h6>
                <i class="fas fa-chevron-down collapse-icon"></i>
            </div>
            <div class="collapse" id="monitoring-${index}">
                <div class="alert alert-light border-start border-4 border-warning">
                    <div class="row">
                        <div class="col-md-6">
                            <strong>📊 Metrics to Track:</strong>
                            <ul class="list-unstyled mt-2">
                                ${(phase.monitoring_requirements.metrics_to_track || phase.monitoring_requirements.key_metrics || []).map(metric => `
                                    <li><i class="fas fa-dot-circle text-warning me-2"></i>${metric}</li>
                                `).join('')}
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <strong>🚨 Alert Thresholds:</strong>
                            <ul class="list-unstyled mt-2">
                                ${Object.entries(phase.monitoring_requirements.alert_thresholds || {}).map(([key, value]) => `
                                    <li><strong>${key.replace(/_/g, ' ')}:</strong> ${value}</li>
                                `).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render collapsible rollback section
 */
function renderCollapsibleRollback(phase, index) {
    if (!phase.rollback_plan) return '';
    
    return `
        <div class="mb-4">
            <div class="d-flex justify-content-between align-items-center mb-3" 
                 style="cursor: pointer;" 
                 data-bs-toggle="collapse" 
                 data-bs-target="#rollback-${index}"
                 aria-expanded="false">
                <h6 class="text-danger mb-0">
                    <i class="fas fa-undo me-2"></i>Rollback Plan
                </h6>
                <i class="fas fa-chevron-down collapse-icon"></i>
            </div>
            <div class="collapse" id="rollback-${index}">
                <div class="alert alert-light border-start border-4 border-danger">
                    <div class="row">
                        <div class="col-md-6">
                            <strong>⏱️ Estimated Time:</strong> ${phase.rollback_plan.estimated_time_minutes || 'N/A'} minutes<br>
                            <strong>📋 Commands Available:</strong> ${phase.rollback_plan.commands?.length || 0}
                        </div>
                        <div class="col-md-6">
                            ${phase.rollback_plan.commands?.length ? `
                                <strong>🔄 Rollback Commands:</strong>
                                <div class="command-wrapper mt-2">
                                    <pre class="command-code small"><code>${phase.rollback_plan.commands.join('\n')}</code></pre>
                                </div>
                            ` : '<p class="text-muted">No rollback commands specified</p>'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Initialize collapsible behavior and animations
 */
function initializeImplementationCollapse() {
    console.log('🎯 Initializing collapsible implementation plan...');
    
    // Add smooth animations for collapse icons
    const addCollapseIconHandlers = () => {
        document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(element => {
            element.addEventListener('click', function() {
                const icon = this.querySelector('.collapse-icon');
                if (icon) {
                    // Toggle rotation based on aria-expanded
                    setTimeout(() => {
                        const isExpanded = this.getAttribute('aria-expanded') === 'true';
                        icon.style.transform = isExpanded ? 'rotate(180deg)' : 'rotate(0deg)';
                        icon.style.transition = 'transform 0.3s ease';
                    }, 50);
                }
            });
        });
    };

    // Initialize after a short delay to ensure DOM is ready
    setTimeout(addCollapseIconHandlers, 100);
    
    // Add hover effects
    document.querySelectorAll('.phase-header, [data-bs-toggle="collapse"]').forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(0, 123, 255, 0.05)';
            this.style.transition = 'background-color 0.2s ease';
        });
        
        element.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
    
    // Initialize Bootstrap collapse elements
    if (typeof bootstrap !== 'undefined') {
        const collapseElements = document.querySelectorAll('.collapse');
        collapseElements.forEach(element => {
            if (!element.hasAttribute('data-bs-initialized')) {
                new bootstrap.Collapse(element, { toggle: false });
                element.setAttribute('data-bs-initialized', 'true');
            }
        });
        console.log(`✅ Initialized ${collapseElements.length} collapse elements`);
    } else {
        console.warn('⚠️ Bootstrap not found, collapse functionality may not work');
    }
}

/**
 * Copy all commands function
 */
function copyAllCommands() {
    const commandElements = document.querySelectorAll('.command-code');
    const allCommands = Array.from(commandElements).map(el => el.textContent).join('\n\n# =====================================\n\n');
    
    navigator.clipboard.writeText(allCommands).then(() => {
        if (window.smoothNotificationManager) {
            window.smoothNotificationManager.show(`📋 Copied ${commandElements.length} commands to clipboard!`, 'success', 3000);
        } else if (typeof showNotification === 'function') {
            showNotification(`📋 Copied ${commandElements.length} commands to clipboard!`, 'success');
        }
    }).catch(err => {
        console.error('Failed to copy commands:', err);
        if (window.smoothNotificationManager) {
            window.smoothNotificationManager.show('Failed to copy commands', 'error', 3000);
        }
    });
}

// =======================================================================
// REFRESH AND LIFECYCLE FUNCTIONS
// =======================================================================

export function refreshImplementationPlan() {
    const validateClusterContext = window.validateClusterContext || (() => true);
    
    if (!validateClusterContext('refreshImplementationPlan')) {
        console.error('❌ BLOCKED: refreshImplementationPlan - invalid cluster context');
        return;
    }
    
    console.log('🔄 Refreshing implementation plan with cluster isolation...');
    
    // Clear cache and reload
    if (window.implementationPlanCache) {
        delete window.implementationPlanCache;
    }
    
    // Reload the implementation plan
    loadImplementationPlan();
}

export function onAnalysisComplete() {
    console.log('🎯 Analysis completed - refreshing implementation plan with cluster validation...');
    
    const validateClusterContext = window.validateClusterContext || (() => true);
    
    if (!validateClusterContext('onAnalysisComplete')) {
        console.error('❌ BLOCKED: onAnalysisComplete - invalid cluster context');
        return;
    }
    
    // Wait a moment for cache to update
    setTimeout(() => {
        refreshImplementationPlan();
    }, 1000);
}

/**
 * Global expand/collapse functions
 */
export function expandAllSections() {
    document.querySelectorAll('#implementation-plan-container .collapse:not(.show)').forEach(element => {
        if (typeof bootstrap !== 'undefined') {
            const bsCollapse = new bootstrap.Collapse(element, { show: true });
        }
    });
    
    if (window.smoothNotificationManager) {
        window.smoothNotificationManager.show('📖 All sections expanded', 'info', 2000);
    }
}

export function collapseAllSections() {
    document.querySelectorAll('#implementation-plan-container .collapse.show').forEach(element => {
        if (typeof bootstrap !== 'undefined') {
            const bsCollapse = new bootstrap.Collapse(element, { hide: true });
        }
    });
    
    if (window.smoothNotificationManager) {
        window.smoothNotificationManager.show('📕 All sections collapsed', 'info', 2000);
    }
}

/**
 * Export implementation plan functionality
 */
export function exportImplementationPlan() {
    if (window.smoothNotificationManager) {
        window.smoothNotificationManager.show('Exporting complete implementation plan...', 'info');
    }
    
    fetch('/api/implementation-plan/export')
        .then(response => {
            if (!response.ok) throw new Error('Export failed');
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `aks-implementation-plan-${new Date().toISOString().split('T')[0]}.pdf`;
            a.click();
            window.URL.revokeObjectURL(url);
            if (window.smoothNotificationManager) {
                window.smoothNotificationManager.show('Implementation plan exported successfully!', 'success');
            }
        })
        .catch(error => {
            console.error('Export error:', error);
            createFallbackExport();
        });
}

function createFallbackExport() {
    // Create a simple text export as fallback
    const content = document.getElementById('implementation-plan-container');
    if (content) {
        const text = content.innerText;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `aks-implementation-plan-${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        window.URL.revokeObjectURL(url);
        if (window.smoothNotificationManager) {
            window.smoothNotificationManager.show('Plan exported as text file', 'info');
        }
    }
}

function showNoAnalysisMessage(container) {
    const currentClusterId = window.getCurrentClusterId ? window.getCurrentClusterId() : 'unknown';
    
    container.innerHTML = `
        <div class="text-center py-5">
            <i class="fas fa-info-circle fa-3x text-muted mb-3"></i>
            <h4 class="text-muted">No Implementation Plan Available</h4>
            <p class="text-muted">Run an analysis first to generate your implementation plan for this cluster</p>
            <small class="text-muted">Current cluster: ${currentClusterId}</small>
            <div class="mt-3">
                <button class="btn btn-primary me-2" onclick="switchToTab('#analysis')">
                    <i class="fas fa-chart-bar me-1"></i> Run Analysis
                </button>
                <button class="btn btn-outline-secondary" onclick="refreshImplementationPlan()">
                    <i class="fas fa-redo me-1"></i> Retry
                </button>
            </div>
        </div>
    `;
}

function displayImplementationError(container, message) {
    console.error('❌ Displaying implementation plan error:', message);
    
    const currentClusterId = window.getCurrentClusterId ? window.getCurrentClusterId() : 'unknown';
    
    container.innerHTML = `
        <div class="alert alert-danger text-center m-4">
            <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
            <h4>Error Loading Implementation Plan</h4>
            <p>${message}</p>
            <small class="text-muted">Cluster: ${currentClusterId}</small>
            <div class="mt-3">
                <button class="btn btn-outline-primary me-2" onclick="refreshImplementationPlan()">
                    <i class="fas fa-redo me-2"></i>Try Again
                </button>
                <button class="btn btn-outline-secondary" onclick="window.location.reload()">
                    <i class="fas fa-refresh me-2"></i>Reload Page
                </button>
            </div>
        </div>
    `;
}

// =======================================================================
// GLOBAL FUNCTION ASSIGNMENTS - CRITICAL FOR COMPATIBILITY
// =======================================================================

// Make functions globally available for backward compatibility
if (typeof window !== 'undefined') {
    window.loadImplementationPlan = loadImplementationPlan;
    window.displayImplementationPlan = displayImplementationPlan;
    window.expandAllSections = expandAllSections;
    window.collapseAllSections = collapseAllSections;
    window.exportImplementationPlan = exportImplementationPlan;
    window.refreshImplementationPlan = refreshImplementationPlan;
    window.onAnalysisComplete = onAnalysisComplete;
    window.initializeImplementationCollapse = initializeImplementationCollapse;
    window.copyAllCommands = copyAllCommands;
    //window.copyCommand = copyCommand;
    
    // Enhanced functions for collapsible UI
    window.expandAllImplementationSections = expandAllSections;
    window.collapseAllImplementationSections = collapseAllSections;
    
    console.log('✅ Enhanced AKS Implementation Plan Manager loaded successfully');
}