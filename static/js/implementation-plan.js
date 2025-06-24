/**
 * COMPLETE Implementation Plan Manager with Better Command Layout
 * Includes all sections and improved command organization
 */

import { showNotification } from './notifications.js';
import { escapeHtml, getPriorityColor, getRiskColor } from './utils.js';
import { copyCommand } from './copy-functionality.js';

export function loadImplementationPlan() {
    console.log('📋 Loading complete implementation plan...');
    
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
    
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
            <h5 class="text-primary">Loading Complete Implementation Plan...</h5>
            <p class="text-muted">Generating comprehensive optimization recommendations...</p>
        </div>
    `;

    makeClusterAwareAPICall('/api/implementation-plan')
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(planData => {
            if (planData.implementation_phases && planData.implementation_phases.length > 0) {
                displayImplementationPlan(planData);
            } else {
                showNoAnalysisMessage(container);
            }
        })
        .catch(error => {
            console.error('❌ Error:', error);
            displayImplementationError(container, error.message);
        });
}

export function displayImplementationPlan(planData) {
    console.log('🎨 Displaying complete implementation plan');
    
    const container = document.getElementById('implementation-plan-container');
    const phases = planData.implementation_phases || [];
    const summary = planData.executive_summary || {};
    const intelligence = planData.intelligence_insights || {};
    const costProtection = planData.cost_protection || {};
    const governance = planData.governance_framework || {};
    const monitoring = planData.monitoring_strategy || {};
    const contingency = planData.contingency_planning || {};
    const success = planData.success_criteria || {};
    const timeline = planData.timeline_optimization || {};
    const risk = planData.risk_mitigation || {};
    
    const totalSavings = phases.reduce((sum, phase) => sum + (phase.projected_savings || 0), 0);
    const clusterName = planData.api_metadata?.cluster_name || 'Unknown';
    const resourceGroup = planData.api_metadata?.resource_group || 'Unknown';

    const html = `
    <!-- Hero Header -->
    <div class="card border-0 shadow-lg mb-4" style="background: linear-gradient(135deg, #28a745, #20c997);">
        <div class="card-body text-white">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                    <h3 class="mb-2">
                        <i class="fas fa-rocket me-2"></i>Complete Implementation Plan Ready!
                    </h3>
                    <p class="mb-1">
                        <strong>Cluster:</strong> ${clusterName} • 
                        <strong>Resource Group:</strong> ${resourceGroup} •
                        <strong>Strategy:</strong> ${planData.metadata?.strategy_type || 'Conservative'}
                    </p>
                    <small class="opacity-75">
                        Generated: ${new Date(planData.metadata?.generated_at || Date.now()).toLocaleDateString()} • 
                        Intelligence: ${planData.metadata?.intelligence_level || 'Advanced'} •
                        Version: ${planData.metadata?.version || '2.0.0'}
                    </small>
                </div>
                <div class="btn-group">
                    <button class="btn btn-outline-light btn-sm" onclick="expandAllImplementationSections()">
                        <i class="fas fa-expand-alt"></i> Expand All
                    </button>
                    <button class="btn btn-outline-light btn-sm" onclick="collapseAllImplementationSections()">
                        <i class="fas fa-compress-alt"></i> Collapse All
                    </button>
                </div>
            </div>
            
            <div class="row g-3">
                <div class="col-6 col-md-2">
                    <div class="text-center p-3 rounded bg-white bg-opacity-25">
                        <div class="h4 mb-1">${phases.length}</div>
                        <small>Phases</small>
                    </div>
                </div>
                <div class="col-6 col-md-2">
                    <div class="text-center p-3 rounded bg-white bg-opacity-25">
                        <div class="h4 mb-1">${timeline?.total_weeks || 0}</div>
                        <small>Weeks</small>
                    </div>
                </div>
                <div class="col-6 col-md-2">
                    <div class="text-center p-3 rounded bg-white bg-opacity-25">
                        <div class="h4 mb-1">$${totalSavings.toLocaleString()}</div>
                        <small>Monthly Savings</small>
                    </div>
                </div>
                <div class="col-6 col-md-2">
                    <div class="text-center p-3 rounded bg-white bg-opacity-25">
                        <div class="h4 mb-1">${planData.executable_commands?.commands_generated || 0}</div>
                        <small>Commands</small>
                    </div>
                </div>
                <div class="col-6 col-md-2">
                    <div class="text-center p-3 rounded bg-white bg-opacity-25">
                        <div class="h4 mb-1">${risk?.overall_risk || 'Low'}</div>
                        <small>Risk</small>
                    </div>
                </div>
                <div class="col-6 col-md-2">
                    <div class="text-center p-3 rounded bg-white bg-opacity-25">
                        <div class="h4 mb-1">${Math.round((timeline?.timeline_confidence || 0.8) * 100)}%</div>
                        <small>Confidence</small>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Executive Summary -->
    ${renderExecutiveSummary(summary, intelligence)}
    
    <!-- Cost Protection -->
    ${renderCostProtection(costProtection)}
    
    <!-- Interactive Timeline -->
    ${renderInteractiveTimeline(phases, timeline)}
    
    <!-- Executable Commands (Improved Layout) -->
    ${renderExecutableCommandsImproved(planData)}
    
    <!-- Implementation Phases -->
    ${renderImplementationPhases(phases)}
    
    <!-- Intelligence Insights -->
    ${renderIntelligenceInsights(intelligence)}
    
    <!-- Governance Framework -->
    ${renderGovernanceFramework(governance)}
    
    <!-- Monitoring Strategy -->
    ${renderMonitoringStrategy(monitoring)}
    
    <!-- Contingency Planning -->
    ${renderContingencyPlanning(contingency)}
    
    <!-- Success Criteria -->
    ${renderSuccessCriteria(success)}
    
    <!-- Timeline Optimization -->
    ${renderTimelineOptimization(timeline)}
    
    <!-- Risk Mitigation -->
    ${renderRiskMitigation(risk)}
    
    <!-- Action Buttons -->
    ${renderActionButtons(totalSavings, planData)}
    `;

    container.innerHTML = html;
    initializeImplementationCollapse();
    console.log('✅ Complete implementation plan displayed successfully');
}

function renderExecutiveSummary(summary, intelligence) {
    return `
        <div class="card shadow mb-4">
            <div class="card-header bg-info text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#executive-summary">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-brain me-2"></i>Executive Summary & AI Insights</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="executive-summary">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6 class="text-primary"><i class="fas fa-lightbulb me-2"></i>Key Recommendations</h6>
                            ${summary.key_recommendations?.length ? `
                                <ul class="list-unstyled">
                                    ${summary.key_recommendations.map(rec => `
                                        <li class="mb-2"><i class="fas fa-check-circle text-success me-2"></i>${rec}</li>
                                    `).join('')}
                                </ul>
                            ` : '<p class="text-muted">No recommendations available</p>'}
                            
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
                            <h6 class="text-primary"><i class="fas fa-robot me-2"></i>AI Intelligence Analysis</h6>
                            ${renderIntelligenceSummary(intelligence)}
                            
                            <h6 class="text-info mt-4 mb-3"><i class="fas fa-chart-line me-2"></i>Financial Impact</h6>
                            ${renderOptimizationSummary(summary.optimization_opportunity)}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderCostProtection(costProtection) {
    if (!costProtection || Object.keys(costProtection).length === 0) return '';
    
    return `
        <div class="card shadow mb-4">
            <div class="card-header bg-warning text-dark" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#cost-protection">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-shield-alt me-2"></i>Cost Protection & Monitoring</h6>
                    <div class="d-flex align-items-center">
                        <span class="badge bg-${costProtection.real_time_monitoring?.status === 'active' ? 'success' : 'secondary'} me-2">
                            ${costProtection.real_time_monitoring?.status === 'active' ? 'ACTIVE' : 'INACTIVE'}
                        </span>
                        <i class="fas fa-chevron-down collapse-icon"></i>
                    </div>
                </div>
            </div>
            <div class="collapse" id="cost-protection">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card border-start border-4 border-primary">
                                <div class="card-body">
                                    <h6><i class="fas fa-radar-chart me-2"></i>Real-time Monitoring</h6>
                                    <p><strong>Status:</strong> 
                                        <span class="badge bg-${costProtection.real_time_monitoring?.status === 'active' ? 'success' : 'secondary'}">
                                            ${costProtection.real_time_monitoring?.status || 'Unknown'}
                                        </span>
                                    </p>
                                    <p><strong>Detection:</strong> ${costProtection.real_time_monitoring?.anomaly_detection || 'Standard'}</p>
                                    <p><strong>Interval:</strong> ${costProtection.real_time_monitoring?.detection_interval_minutes || 5} minutes</p>
                                    <p><strong>Guardrails:</strong> ${costProtection.real_time_monitoring?.guardrails_active || 0} active</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card border-start border-4 border-danger">
                                <div class="card-body">
                                    <h6><i class="fas fa-exclamation-triangle me-2"></i>Spike Prevention</h6>
                                    <p><strong>Plan Active:</strong> 
                                        <span class="badge bg-${costProtection.cost_spike_prevention?.prevention_plan_active ? 'success' : 'warning'}">
                                            ${costProtection.cost_spike_prevention?.prevention_plan_active ? 'Yes' : 'No'}
                                        </span>
                                    </p>
                                    <p><strong>Risk Score:</strong> 
                                        <span class="badge bg-${getRiskScoreColor(costProtection.cost_spike_prevention?.risk_score || 5)}">
                                            ${costProtection.cost_spike_prevention?.risk_score || 5}/10
                                        </span>
                                    </p>
                                    <p><strong>Success Probability:</strong> ${((costProtection.cost_spike_prevention?.success_probability || 0) * 100).toFixed(1)}%</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderInteractiveTimeline(phases, timeline) {
    return `
        <div class="card shadow mb-4">
            <div class="card-header bg-secondary text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#timeline-overview">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-project-diagram me-2"></i>Interactive Timeline</h6>
                    <div class="d-flex gap-2">
                        <span class="badge bg-light text-dark">${phases.length} Phases</span>
                        <span class="badge bg-light text-dark">${timeline?.total_weeks || 0} Weeks</span>
                        <i class="fas fa-chevron-down collapse-icon"></i>
                    </div>
                </div>
            </div>
            <div class="collapse" id="timeline-overview">
                <div class="card-body">
                    <div class="timeline-container mb-4">
                        <div class="d-flex bg-light rounded p-3" style="height: 80px;">
                            ${phases.map((phase, index) => {
                                const phaseWidth = ((phase.duration_weeks || 1) / (timeline?.total_weeks || phases.length)) * 100;
                                const phaseColor = getPhaseColor(index);
                                return `
                                    <div class="d-flex align-items-center justify-content-center text-white fw-bold rounded me-1" 
                                         style="width: ${phaseWidth}%; background: ${phaseColor}; cursor: pointer; font-size: 0.8rem;"
                                         onclick="scrollToPhase(${index + 1})"
                                         title="Phase ${phase.phase_number || index + 1}: ${phase.title || 'Phase'} - ${phase.duration_weeks || 1} weeks - $${(phase.projected_savings || 0).toLocaleString()}/mo">
                                        <div class="text-center">
                                            <div>P${phase.phase_number || index + 1}</div>
                                            <div style="font-size: 0.7rem;">${phase.duration_weeks || 1}w</div>
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-3">
                            <div class="card border-0 bg-light">
                                <div class="card-body text-center">
                                    <h5 class="card-title text-primary">${timeline?.total_weeks || 0}</h5>
                                    <p class="card-text">Total Weeks</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card border-0 bg-light">
                                <div class="card-body text-center">
                                    <h5 class="card-title text-success">${Math.round((timeline?.timeline_confidence || 0.8) * 100)}%</h5>
                                    <p class="card-text">Confidence</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card border-0 bg-light">
                                <div class="card-body text-center">
                                    <h5 class="card-title text-info">${timeline?.resource_requirements?.total_hours || 'TBD'}</h5>
                                    <p class="card-text">Total Hours</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card border-0 bg-light">
                                <div class="card-body text-center">
                                    <h5 class="card-title text-warning">${timeline?.complexity_adjustment || 'Standard'}</h5>
                                    <p class="card-text">Complexity</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderExecutableCommandsImproved(planData) {
    const phases = planData.implementation_phases || [];
    const intelligence = planData.intelligence_insights || {};
    
    // Group commands by category as requested
    const commandCategories = {};
    
    // Commands from AI priority areas
    if (intelligence.dynamic_strategy_insights?.priority_areas) {
        intelligence.dynamic_strategy_insights.priority_areas.forEach((area, areaIndex) => {
            if (area.executable_commands && Array.isArray(area.executable_commands)) {
                const categoryName = area.type?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Priority Area';
                
                if (!commandCategories[categoryName]) {
                    commandCategories[categoryName] = {
                        commands: [],
                        savingsPotential: area.savings_potential_monthly || 0,
                        riskLevel: area.risk_assessment < 0.3 ? 'Low' : area.risk_assessment < 0.6 ? 'Medium' : 'High',
                        timeline: area.timeline_weeks,
                        targetWorkloads: area.target_workloads || []
                    };
                }
                
                area.executable_commands.forEach((cmd, cmdIndex) => {
                    if (cmd && cmd.trim() !== '') {
                        commandCategories[categoryName].commands.push(cmd.trim());
                    }
                });
            }
        });
    }
    
    // Commands from phases
    phases.forEach((phase, phaseIndex) => {
        if (phase.tasks) {
            phase.tasks.forEach((task, taskIndex) => {
                if (task.command) {
                    const categoryName = `Phase ${phase.phase_number || phaseIndex + 1} Commands`;
                    
                    if (!commandCategories[categoryName]) {
                        commandCategories[categoryName] = {
                            commands: [],
                            savingsPotential: phase.projected_savings || 0,
                            riskLevel: phase.risk_level || 'Low'
                        };
                    }
                    
                    commandCategories[categoryName].commands.push(task.command.trim());
                }
            });
        }
    });

    if (Object.keys(commandCategories).length === 0) {
        return `
            <div class="card shadow mb-4">
                <div class="card-header bg-dark text-white">
                    <h5 class="mb-0"><i class="fas fa-terminal me-2"></i>Executable Commands</h5>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        No executable commands generated yet. Run an analysis to generate optimization commands.
                    </div>
                </div>
            </div>
        `;
    }

    return `
        <div class="card shadow mb-4">
            <div class="card-header bg-dark text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#executable-commands" aria-expanded="true">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="fas fa-terminal me-2"></i>Executable Commands (${Object.keys(commandCategories).length} categories)</h5>
                    <div class="d-flex gap-2">
                        <span class="badge bg-info">${Object.values(commandCategories).reduce((sum, cat) => sum + cat.commands.length, 0)} total commands</span>
                        <i class="fas fa-chevron-down collapse-icon"></i>
                    </div>
                </div>
            </div>
            <div class="collapse show" id="executable-commands">
                <div class="card-body">
                    ${Object.entries(commandCategories).map(([categoryName, categoryData]) => {
                        const categoryId = categoryName.replace(/\s+/g, '-').toLowerCase();
                        const allCommands = categoryData.commands.join('\n\n');
                        
                        return `
                            <div class="command-category-improved mb-4">
                                <div class="card border-start border-4 border-primary">
                                    <div class="card-header bg-light" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#category-${categoryId}" aria-expanded="false">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <h6 class="text-primary mb-1">
                                                    <i class="fas fa-cogs me-2"></i>
                                                    ${categoryName} (${categoryData.commands.length} commands)
                                                </h6>
                                                <div class="d-flex gap-2 flex-wrap">
                                                    ${categoryData.savingsPotential ? `<span class="badge bg-success">${categoryData.savingsPotential.toFixed(2)}/mo</span>` : ''}
                                                    ${categoryData.riskLevel ? `<span class="badge bg-${getRiskLevelColor(categoryData.riskLevel)}">${categoryData.riskLevel} Risk</span>` : ''}
                                                    ${categoryData.timeline ? `<span class="badge bg-info">${categoryData.timeline} weeks</span>` : ''}
                                                    ${categoryData.targetWorkloads?.length ? `<span class="badge bg-secondary">${categoryData.targetWorkloads.length} workloads</span>` : ''}
                                                </div>
                                            </div>
                                            <div class="d-flex gap-2 align-items-center">
                                                <button class="btn btn-sm btn-outline-success stable-btn" onclick="copyCategoryCommands('category-${categoryId}')">
                                                    <i class="fas fa-copy me-1"></i>Copy All
                                                </button>
                                                <i class="fas fa-chevron-down collapse-icon"></i>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="collapse" id="category-${categoryId}">
                                        <div class="card-body">
                                            <div class="commands-combined-container">
                                                <div class="d-flex justify-content-between align-items-center mb-2">
                                                    <small class="text-muted">Combined Commands (${categoryData.commands.length} total)</small>
                                                    <button class="btn btn-sm btn-outline-primary stable-btn" onclick="copyAllCommands('${categoryId}')">
                                                        <i class="fas fa-copy me-1"></i>Copy All Commands
                                                    </button>
                                                </div>
                                                <pre class="command-code-combined bg-dark text-light p-3 rounded" style="max-height: 350px; overflow-y: auto; font-size: 0.85rem; white-space: pre-wrap; word-wrap: break-word;"><code>${escapeHtml(allCommands)}</code></pre>
                                            </div>
                                            
                                            ${categoryData.targetWorkloads?.length ? `
                                                <div class="mt-3">
                                                    <h6 class="text-info"><i class="fas fa-server me-2"></i>Target Workloads</h6>
                                                    <div class="d-flex gap-2 flex-wrap">
                                                        ${categoryData.targetWorkloads.map(workload => `<span class="badge bg-info">${workload}</span>`).join('')}
                                                    </div>
                                                </div>
                                            ` : ''}
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

function renderImplementationPhases(phases) {
    return `
        <div class="card shadow mb-4">
            <div class="card-header bg-primary text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#implementation-phases" aria-expanded="true">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="fas fa-cogs me-2"></i>Implementation Phases (${phases.length})</h5>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse show" id="implementation-phases">
                <div class="card-body p-0">
                    ${phases.map((phase, index) => `
                        <div class="border-bottom p-3" id="phase-${index + 1}">
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="flex-grow-1">
                                    <h6 class="text-primary">
                                        <i class="fas fa-cog me-2"></i>
                                        Phase ${phase.phase_number || index + 1}: ${phase.title || 'Untitled Phase'}
                                    </h6>
                                    <div class="d-flex gap-2 flex-wrap mb-2">
                                        <span class="badge bg-light text-dark">${phase.duration_weeks || 'N/A'} weeks</span>
                                        <span class="badge bg-success">$${(phase.projected_savings || 0).toLocaleString()}/mo</span>
                                        <span class="badge bg-info">${phase.priority_level || 'Medium'} Priority</span>
                                        <span class="badge bg-warning">${phase.risk_level || 'Low'} Risk</span>
                                        <span class="badge bg-secondary">${phase.complexity_level || 'Medium'} Complexity</span>
                                    </div>
                                    <p class="text-muted mb-2">
                                        <small>Week ${phase.start_week || 'N/A'} - ${phase.end_week || 'N/A'} • 
                                        ${phase.type || 'Optimization'}</small>
                                    </p>
                                </div>
                                <div class="text-end">
                                    <div class="h5 text-success mb-0">$${(phase.projected_savings || 0).toLocaleString()}</div>
                                    <small class="text-muted">Monthly Savings</small>
                                </div>
                            </div>
                            
                            ${phase.success_criteria?.length ? `
                                <div class="mt-3">
                                    <h6 class="text-success"><i class="fas fa-check-circle me-2"></i>Success Criteria</h6>
                                    <ul class="list-unstyled">
                                        ${phase.success_criteria.map(criteria => `
                                            <li class="mb-1"><i class="fas fa-check text-success me-2"></i>${criteria}</li>
                                        `).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                            
                            ${phase.tasks?.length ? `
                                <div class="mt-3">
                                    <h6 class="text-info"><i class="fas fa-tasks me-2"></i>Tasks (${phase.tasks.length})</h6>
                                    <div class="row">
                                        ${phase.tasks.map(task => `
                                            <div class="col-md-6 mb-2">
                                                <div class="card border-start border-4 border-info">
                                                    <div class="card-body p-3">
                                                        <h6 class="card-title">${task.title || 'Task'}</h6>
                                                        <p class="card-text text-muted">${task.description || 'No description'}</p>
                                                        ${task.estimated_hours ? `<small class="text-muted">Estimated: ${task.estimated_hours} hours</small>` : ''}
                                                        ${task.skills_required?.length ? `
                                                            <div class="mt-2">
                                                                ${task.skills_required.map(skill => `<span class="badge bg-secondary me-1">${skill}</span>`).join('')}
                                                            </div>
                                                        ` : ''}
                                                    </div>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

function renderIntelligenceInsights(intelligence) {
    if (!intelligence || Object.keys(intelligence).length === 0) return '';
    
    return `
        <div class="card shadow mb-4">
            <div class="card-header bg-purple text-white" style="cursor: pointer; background-color: #6f42c1 !important;" data-bs-toggle="collapse" data-bs-target="#intelligence-insights">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-brain me-2"></i>AI Intelligence Insights</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="intelligence-insights">
                <div class="card-body">
                    ${intelligence.cluster_dna_analysis ? `
                        <div class="mb-4">
                            <h6 class="text-primary"><i class="fas fa-dna me-2"></i>Cluster DNA Analysis</h6>
                            <div class="alert alert-light border-start border-4 border-primary">
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>🧬 Personality:</strong> ${(intelligence.cluster_dna_analysis.cluster_personality || 'Unknown').replace(/-/g, ' ')}<br>
                                        <strong>📊 Efficiency Score:</strong> ${Math.round((intelligence.cluster_dna_analysis.efficiency_score || 0) * 100)}%<br>
                                        <strong>🎯 Optimization Potential:</strong> ${intelligence.cluster_dna_analysis.optimization_potential || 'Unknown'}
                                    </div>
                                    <div class="col-md-6">
                                        ${intelligence.cluster_dna_analysis.unique_characteristics?.length ? `
                                            <strong>✨ Unique Characteristics:</strong><br>
                                            <div class="mt-2">
                                                ${intelligence.cluster_dna_analysis.unique_characteristics.map(char => `
                                                    <span class="badge bg-info me-1 mb-1">${typeof char === 'string' ? char : JSON.stringify(char)}</span>
                                                `).join('')}
                                            </div>
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
                                        <strong>🔧 Optimization Approach:</strong> ${intelligence.dynamic_strategy_insights.optimization_approach || 'Balanced'}<br>
                                        <strong>📋 Priority Areas:</strong> ${intelligence.dynamic_strategy_insights.priority_areas?.length || 0} identified
                                    </div>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${intelligence.learning_engine_insights ? `
                        <div class="mb-4">
                            <h6 class="text-success"><i class="fas fa-graduation-cap me-2"></i>Learning Engine Insights</h6>
                            <div class="alert alert-light border-start border-4 border-success">
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>🎯 Confidence Boost:</strong> ${(intelligence.learning_engine_insights.confidence_boost * 100).toFixed(1)}%<br>
                                        <strong>📊 Pattern Matches:</strong> ${intelligence.learning_engine_insights.pattern_matches || 0}
                                    </div>
                                    <div class="col-md-6">
                                        <strong>📈 Success Rate Prediction:</strong> ${Math.round((intelligence.learning_engine_insights.success_rate_prediction || 0) * 100)}%<br>
                                        <strong>💡 Recommendations:</strong> ${intelligence.learning_engine_insights.optimization_recommendations?.length || 0}
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

function renderGovernanceFramework(governance) {
    if (!governance || Object.keys(governance).length === 0) return '';
    
    return `
        <div class="card shadow mb-4">
            <div class="card-header bg-dark text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#governance-framework">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-gavel me-2"></i>Governance Framework</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="governance-framework">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6 class="text-primary"><i class="fas fa-check-circle me-2"></i>Approval Requirements</h6>
                            ${governance.approval_requirements?.length ? `
                                <ul class="list-unstyled">
                                    ${governance.approval_requirements.map(req => `
                                        <li class="mb-2"><i class="fas fa-arrow-right text-primary me-2"></i>${req}</li>
                                    `).join('')}
                                </ul>
                            ` : '<p class="text-muted">No approval requirements defined</p>'}
                        </div>
                        <div class="col-md-6">
                            <h6 class="text-info"><i class="fas fa-cogs me-2"></i>Governance Details</h6>
                            <div class="alert alert-light">
                                <strong>Governance Level:</strong> ${governance.governance_level || 'Standard'}<br>
                                <strong>Review Cycle:</strong> ${governance.review_cycle || 'Monthly'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderMonitoringStrategy(monitoring) {
    if (!monitoring || Object.keys(monitoring).length === 0) return '';
    
    return `
        <div class="card shadow mb-4">
            <div class="card-header bg-warning text-dark" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#monitoring-strategy">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-chart-bar me-2"></i>Monitoring Strategy</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="monitoring-strategy">
                <div class="card-body">
                    ${monitoring.monitoring_strategy ? `
                        <div class="row">
                            <div class="col-md-6">
                                <h6 class="text-primary"><i class="fas fa-chart-line me-2"></i>Key Metrics</h6>
                                ${monitoring.monitoring_strategy.key_metrics?.length ? `
                                    <ul class="list-unstyled">
                                        ${monitoring.monitoring_strategy.key_metrics.map(metric => `
                                            <li class="mb-2"><i class="fas fa-dot-circle text-warning me-2"></i>${metric}</li>
                                        `).join('')}
                                    </ul>
                                ` : '<p class="text-muted">No key metrics defined</p>'}
                            </div>
                            <div class="col-md-6">
                                <h6 class="text-danger"><i class="fas fa-bell me-2"></i>Alert Thresholds</h6>
                                ${monitoring.monitoring_strategy.alert_thresholds ? `
                                    <div class="alert alert-light">
                                        ${Object.entries(monitoring.monitoring_strategy.alert_thresholds).map(([key, value]) => `
                                            <strong>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> ${value}<br>
                                        `).join('')}
                                    </div>
                                ` : '<p class="text-muted">No alert thresholds defined</p>'}
                            </div>
                        </div>
                    ` : '<p class="text-muted">No monitoring strategy defined</p>'}
                </div>
            </div>
        </div>
    `;
}

function renderContingencyPlanning(contingency) {
    if (!contingency || Object.keys(contingency).length === 0) return '';
    
    return `
        <div class="card shadow mb-4">
            <div class="card-header bg-secondary text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#contingency-planning">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-shield-alt me-2"></i>Contingency Planning</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="contingency-planning">
                <div class="card-body">
                    <div class="row">
                        ${contingency.business_contingencies?.length ? `
                            <div class="col-md-6">
                                <h6 class="text-primary"><i class="fas fa-briefcase me-2"></i>Business Contingencies</h6>
                                <ul class="list-unstyled">
                                    ${contingency.business_contingencies.map(cont => `
                                        <li class="mb-2"><i class="fas fa-arrow-right text-primary me-2"></i>${cont}</li>
                                    `).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        ${contingency.technical_contingencies?.length ? `
                            <div class="col-md-6">
                                <h6 class="text-info"><i class="fas fa-cogs me-2"></i>Technical Contingencies</h6>
                                <ul class="list-unstyled">
                                    ${contingency.technical_contingencies.map(cont => `
                                        <li class="mb-2"><i class="fas fa-arrow-right text-info me-2"></i>${cont}</li>
                                    `).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderSuccessCriteria(success) {
    if (!success || Object.keys(success).length === 0) return '';
    
    return `
        <div class="card shadow mb-4">
            <div class="card-header bg-success text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#success-criteria">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-target me-2"></i>Success Criteria & Metrics</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="success-criteria">
                <div class="card-body">
                    <div class="row">
                        ${success.financial_success_criteria ? `
                            <div class="col-md-6">
                                <h6 class="text-success"><i class="fas fa-dollar-sign me-2"></i>Financial Success</h6>
                                <div class="alert alert-light border-start border-4 border-success">
                                    ${Object.entries(success.financial_success_criteria).map(([key, value]) => `
                                        <strong>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> ${value}<br>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                        ${success.technical_success_criteria?.length ? `
                            <div class="col-md-6">
                                <h6 class="text-primary"><i class="fas fa-cogs me-2"></i>Technical Success</h6>
                                <ul class="list-unstyled">
                                    ${success.technical_success_criteria.map(criteria => `
                                        <li class="mb-2"><i class="fas fa-check text-success me-2"></i>${criteria}</li>
                                    `).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderTimelineOptimization(timeline) {
    if (!timeline || Object.keys(timeline).length === 0) return '';
    
    return `
        <div class="card shadow mb-4">
            <div class="card-header bg-info text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#timeline-optimization">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-calendar-alt me-2"></i>Timeline Optimization</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="timeline-optimization">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6 class="text-info"><i class="fas fa-calendar me-2"></i>Timeline Details</h6>
                            <div class="alert alert-light border-start border-4 border-info">
                                <strong>📅 Base Timeline:</strong> ${timeline.base_timeline_weeks || 'N/A'} weeks<br>
                                <strong>⚡ Parallelization Benefit:</strong> ${timeline.parallelization_benefit || 0} weeks saved<br>
                                <strong>🔧 Complexity Adjustment:</strong> ${timeline.complexity_adjustment || 0} weeks<br>
                                <strong>🎯 Total Timeline:</strong> ${timeline.total_weeks || timeline.base_timeline_weeks || 'N/A'} weeks
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6 class="text-success"><i class="fas fa-chart-line me-2"></i>Confidence Metrics</h6>
                            <div class="alert alert-light border-start border-4 border-success">
                                <strong>📊 Timeline Confidence:</strong> ${Math.round((timeline.timeline_confidence || 0.8) * 100)}%<br>
                                <strong>🚀 Risk Adjustment:</strong> ${timeline.risk_adjustment || 0} weeks<br>
                                <strong>🎯 Delivery Confidence:</strong> ${timeline.delivery_confidence || 'High'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderRiskMitigation(risk) {
    if (!risk || Object.keys(risk).length === 0) return '';
    
    return `
        <div class="card shadow mb-4">
            <div class="card-header bg-danger text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#risk-mitigation">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-exclamation-triangle me-2"></i>Risk Mitigation</h6>
                    <span class="badge bg-light text-dark">${risk.overall_risk || 'Low'} Risk</span>
                </div>
            </div>
            <div class="collapse" id="risk-mitigation">
                <div class="card-body">
                    <div class="row mb-4">
                        <div class="col-md-4">
                            <div class="text-center p-3 rounded bg-light">
                                <div class="h4 mb-1 text-danger">${risk.overall_risk || 'Low'}</div>
                                <small class="text-muted">Overall Risk</small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="text-center p-3 rounded bg-light">
                                <div class="h4 mb-1 text-danger">${risk.mitigation_strategies?.length || 0}</div>
                                <small class="text-muted">Mitigations</small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="text-center p-3 rounded bg-light">
                                <div class="h4 mb-1 text-danger">${risk.monitoring_requirements?.length || 0}</div>
                                <small class="text-muted">Requirements</small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        ${risk.mitigation_strategies?.length ? `
                            <div class="col-md-6">
                                <h6 class="text-success"><i class="fas fa-shield-alt me-2"></i>Mitigation Strategies</h6>
                                <ul class="list-unstyled">
                                    ${risk.mitigation_strategies.map(strategy => `
                                        <li class="mb-2"><i class="fas fa-check-circle text-success me-2"></i>${strategy}</li>
                                    `).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        ${risk.monitoring_requirements?.length ? `
                            <div class="col-md-6">
                                <h6 class="text-warning"><i class="fas fa-eye me-2"></i>Monitoring Requirements</h6>
                                <ul class="list-unstyled">
                                    ${risk.monitoring_requirements.map(req => `
                                        <li class="mb-2"><i class="fas fa-dot-circle text-warning me-2"></i>${req}</li>
                                    `).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderActionButtons(totalSavings, planData) {
    return `
        <div class="card shadow mt-4" style="background: linear-gradient(135deg, #f8f9fa, #e9ecef);">
            <div class="card-body text-center">
                <h5 class="mb-3 text-primary">🚀 Ready to Transform Your Infrastructure?</h5>
                <p class="text-muted mb-4">Deploy your optimization plan and start saving immediately</p>
                
                <div class="d-flex gap-2 justify-content-center flex-wrap mb-4">
                    <button class="btn btn-success btn-lg" onclick="deployOptimizations()">
                        <i class="fas fa-rocket me-2"></i>Deploy Phase 1
                    </button>
                    <button class="btn btn-primary btn-lg" onclick="exportImplementationPlan()">
                        <i class="fas fa-download me-2"></i>Export Complete Plan
                    </button>
                    <button class="btn btn-outline-primary btn-lg" onclick="scheduleOptimization()">
                        <i class="fas fa-calendar me-2"></i>Schedule Review
                    </button>
                    <button class="btn btn-outline-secondary btn-lg" onclick="loadImplementationPlan()">
                        <i class="fas fa-redo me-2"></i>Refresh Plan
                    </button>
                </div>
                
                <div class="row text-center pt-3 border-top">
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
    `;
}

// Helper functions
function getPhaseColor(index) {
    const colors = [
        'linear-gradient(135deg, #3498db, #2980b9)',
        'linear-gradient(135deg, #e74c3c, #c0392b)',
        'linear-gradient(135deg, #2ecc71, #27ae60)',
        'linear-gradient(135deg, #f39c12, #e67e22)',
        'linear-gradient(135deg, #9b59b6, #8e44ad)',
        'linear-gradient(135deg, #1abc9c, #16a085)'
    ];
    return colors[index % colors.length];
}

function getRiskScoreColor(score) {
    if (score <= 3) return 'success';
    if (score <= 6) return 'warning';
    return 'danger';
}

function getRiskLevelColor(level) {
    switch(level?.toLowerCase()) {
        case 'low': return 'success';
        case 'medium': return 'warning';
        case 'high': return 'danger';
        default: return 'secondary';
    }
}

function scrollToPhase(phaseNumber) {
    const phaseElement = document.getElementById(`phase-${phaseNumber}`);
    if (phaseElement) {
        phaseElement.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
        
        // Highlight briefly
        phaseElement.style.backgroundColor = 'rgba(0, 123, 255, 0.1)';
        setTimeout(() => {
            phaseElement.style.backgroundColor = '';
        }, 2000);
    }
}

function renderIntelligenceSummary(intelligence) {
    if (!intelligence.cluster_dna_analysis && !intelligence.dynamic_strategy_insights) {
        return '<p class="text-muted">AI analysis not available</p>';
    }
    
    const dna = intelligence.cluster_dna_analysis || {};
    const strategy = intelligence.dynamic_strategy_insights || {};
    
    return `
        <div class="alert alert-light border-start border-4 border-primary">
            <div class="mb-2">
                <strong>🧬 Cluster Personality:</strong> ${(dna.cluster_personality || 'Unknown').replace(/-/g, ' ')}
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

// Copy functions
function copyAllCommands(categoryId) {
    const categoryElement = document.getElementById(`category-${categoryId}`);
    if (!categoryElement) return;
    
    const commandCode = categoryElement.querySelector('.command-code-combined code');
    if (commandCode) {
        const allCommands = commandCode.textContent;
        navigator.clipboard.writeText(allCommands).then(() => {
            if (window.smoothNotificationManager) {
                window.smoothNotificationManager.show(`📋 Copied all commands from this category!`, 'success', 3000);
            }
        }).catch(err => {
            console.error('Failed to copy commands:', err);
        });
    }
}

function copyCategoryCommands(categoryId) {
    copyAllCommands(categoryId.replace('category-', ''));
}

function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        if (window.smoothNotificationManager) {
            window.smoothNotificationManager.show('📋 Command copied!', 'success', 2000);
        }
    });
}

function initializeImplementationCollapse() {
    // Add stable button styles to prevent shivering
    const style = document.createElement('style');
    style.textContent = `
        .stable-btn {
            transition: background-color 0.2s ease, border-color 0.2s ease;
        }
        .stable-btn:hover {
            transform: none !important;
            box-shadow: none !important;
        }
        .card:hover {
            transform: none !important;
        }
        .command-category-improved:hover {
            transform: none !important;
        }
        .command-code-combined {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            line-height: 1.4;
        }
    `;
    document.head.appendChild(style);
    
    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(element => {
        element.addEventListener('click', function() {
            const icon = this.querySelector('.collapse-icon');
            if (icon) {
                setTimeout(() => {
                    const isExpanded = this.getAttribute('aria-expanded') === 'true';
                    icon.style.transform = isExpanded ? 'rotate(180deg)' : 'rotate(0deg)';
                    icon.style.transition = 'transform 0.3s ease';
                }, 50);
            }
        });
    });
}

function showNoAnalysisMessage(container) {
    container.innerHTML = `
        <div class="text-center py-5">
            <i class="fas fa-info-circle fa-3x text-muted mb-3"></i>
            <h4 class="text-muted">No Implementation Plan Available</h4>
            <p class="text-muted">Run an analysis first to generate your implementation plan</p>
            <button class="btn btn-primary" onclick="switchToTab('#analysis')">
                <i class="fas fa-chart-bar me-1"></i> Run Analysis
            </button>
        </div>
    `;
}

function displayImplementationError(container, message) {
    container.innerHTML = `
        <div class="alert alert-danger text-center m-4">
            <h4>Error Loading Implementation Plan</h4>
            <p>${message}</p>
            <button class="btn btn-outline-primary" onclick="refreshImplementationPlan()">
                <i class="fas fa-redo me-2"></i>Try Again
            </button>
        </div>
    `;
}

// Export functions
export function refreshImplementationPlan() {
    console.log('🔄 Refreshing implementation plan...');
    loadImplementationPlan();
}

export function expandAllSections() {
    document.querySelectorAll('.collapse:not(.show)').forEach(element => {
        if (typeof bootstrap !== 'undefined') {
            new bootstrap.Collapse(element, { show: true });
        }
    });
}

export function collapseAllSections() {
    document.querySelectorAll('.collapse.show').forEach(element => {
        if (typeof bootstrap !== 'undefined') {
            new bootstrap.Collapse(element, { hide: true });
        }
    });
}

export function exportImplementationPlan() {
    const content = document.getElementById('implementation-plan-container');
    if (content) {
        const text = content.innerText;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `implementation-plan-${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        window.URL.revokeObjectURL(url);
    }
}

// Global assignments
if (typeof window !== 'undefined') {
    window.loadImplementationPlan = loadImplementationPlan;
    window.displayImplementationPlan = displayImplementationPlan;
    window.expandAllImplementationSections = expandAllSections;
    window.collapseAllImplementationSections = collapseAllSections;
    window.refreshImplementationPlan = refreshImplementationPlan;
    window.exportImplementationPlan = exportImplementationPlan;
    window.copyCategoryCommands = copyCategoryCommands;
    window.copyText = copyText;
    window.scrollToPhase = scrollToPhase;
    
    console.log('✅ Complete Implementation Plan Manager loaded successfully');
}