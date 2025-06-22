/**
 * ============================================================================
 * AKS COST INTELLIGENCE - IMPLEMENTATION PLAN MANAGEMENT
 * ============================================================================
 * Loads, displays, and manages implementation plans with collapsible sections
 * ============================================================================
 */

import { showNotification } from './notifications.js';
import { escapeHtml, getPriorityColor, getRiskColor } from './utils.js';
import { copyCommand } from './copy-functionality.js';

/**
 * Loads and displays implementation plan
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
            console.log('📊 Data keys:', Object.keys(planData));
            
            // Validate cluster metadata in response
            if (planData.api_metadata && planData.api_metadata.cluster_id) {
                const responseClusterId = planData.api_metadata.cluster_id;
                const currentClusterId = window.getCurrentClusterId ? window.getCurrentClusterId() : null;
                
                if (currentClusterId && responseClusterId !== currentClusterId) {
                    console.error('🚨 CLUSTER MISMATCH in implementation plan response!');
                    console.error(`   Expected: ${currentClusterId}`);
                    console.error(`   Received: ${responseClusterId}`);
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

export function refreshImplementationPlan() {
    const validateClusterContext = window.validateClusterContext || (() => true);
    
    if (!validateClusterContext('refreshImplementationPlan')) {
        console.error('❌ BLOCKED: refreshImplementationPlan - invalid cluster context');
        return;
    }
    
    console.log('🔄 Refreshing implementation plan with cluster isolation...');
    
    // Clear any cached plan data
    if (window.implementationPlanCache) {
        delete window.implementationPlanCache;
    }
    
    // Reload with cluster isolation
    loadImplementationPlan();
}

/**
 * Analysis completion handler with cluster validation
 */
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
 * Displays implementation plan content with collapsible sections
 */
export function displayImplementationPlan(planData) {
    console.log('🎨 Displaying COLLAPSIBLE implementation plan with ALL data:', planData);
    
    const container = document.getElementById('implementation-plan-container');
    if (!container) {
        console.error('❌ Implementation plan container not found!');
        return;
    }

    const phases = planData.implementation_phases || [];
    const summary = planData.executive_summary || {};
    const timeline = planData.timeline_optimization || {};
    const risk = planData.risk_mitigation || {};
    const governance = planData.governance_framework || {};
    const monitoring = planData.monitoring_strategy || {};
    const intelligence = planData.intelligence_insights || {};
    const contingency = planData.contingency_planning || {};
    const success = planData.success_criteria || {};

    if (!phases || phases.length === 0) {
        console.warn('⚠️ No phases found to display');
        showNoAnalysisMessage(container);
        return;
    }

    // Calculate totals
    const totalSavings = phases.reduce((sum, phase) => sum + (phase.projected_savings || 0), 0);
    const totalWeeks = Math.max(...phases.map(phase => phase.end_week || phase.duration_weeks || 0));

    let html = `
        <!-- EXECUTIVE SUMMARY HEADER (Always Visible) -->
        <div class="card border-0 shadow-lg mb-4">
            <div class="card-body text-white">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h3 class="card-title mb-3">
                            <i class="fas fa-rocket me-2"></i>Complete Implementation Plan Ready
                        </h3>
                        <div class="mb-3">
                            <strong>Cluster:</strong> ${summary.implementation_overview?.cluster_name || planData.metadata?.cluster_name || 'N/A'} 
                            <span class="mx-2">•</span>
                            <strong>Resource Group:</strong> ${summary.implementation_overview?.resource_group || planData.metadata?.resource_group || 'N/A'}
                        </div>
                        <p class="mb-0 opacity-90">
                            ${summary.implementation_overview?.summary || `This ${totalWeeks}-week implementation plan will optimize your AKS cluster through ${phases.length} carefully planned phases.`}
                        </p>
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="badge fs-6 px-3 py-2" style="background: rgba(255,255,255,0.2);">
                            <i class="fas fa-shield-alt me-1"></i>
                            ${risk.overall_risk || 'Low'} Risk
                        </div>
                    </div>
                </div>
                
                <div class="row g-3 mt-3">
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">${phases.length}</div>
                            <small class="opacity-90">Phases</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">${totalWeeks || timeline.base_timeline_weeks || 'TBD'}</div>
                            <small class="opacity-90">Total Weeks</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">$${totalSavings.toLocaleString()}</div>
                            <small class="opacity-90">Monthly Savings</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">${((planData.metadata?.confidence_level || 'High') === 'High' ? '95' : '85')}%</div>
                            <small class="opacity-90">Confidence</small>
                        </div>
                    </div>
                </div>
                
                <!-- EXPAND/COLLAPSE ALL CONTROLS -->
                <div class="text-center mt-4 pt-3 border-top border-light border-opacity-25">
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-light btn-sm" onclick="expandAllSections()">
                            <i class="fas fa-expand-alt me-1"></i>Expand All
                        </button>
                        <button type="button" class="btn btn-light btn-sm" onclick="collapseAllSections()">
                            <i class="fas fa-compress-alt me-1"></i>Collapse All
                        </button>
                        <button type="button" class="btn btn-light btn-sm" onclick="togglePhaseDetails()">
                            <i class="fas fa-eye me-1"></i>Toggle Details
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- COLLAPSIBLE QUICK OVERVIEW -->
        ${renderQuickOverview(summary, intelligence, phases)}
    `;

    // RENDER COLLAPSIBLE IMPLEMENTATION PHASES
    html += `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-primary text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#implementation-phases-section">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">
                        <i class="fas fa-cogs me-2"></i>Implementation Phases (${phases.length} phases)
                    </h5>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse show" id="implementation-phases-section">
                <div class="card-body p-0">
                    ${renderCollapsiblePhases(phases)}
                </div>
            </div>
        </div>
    `;

    // RENDER OTHER COLLAPSIBLE SECTIONS
    html += `
        <!-- GOVERNANCE & STRATEGY SECTIONS -->
        ${renderCollapsibleGovernanceFramework(governance)}
        ${renderCollapsibleMonitoringStrategy(monitoring)}
        ${renderCollapsibleContingencyPlanning(contingency)}
        ${renderCollapsibleSuccessCriteria(success)}
        ${renderCollapsibleTimelineOptimization(timeline)}
        
        <!-- ACTION BUTTONS -->
        ${renderActionButtons(totalSavings)}
    `;

    container.innerHTML = html;
    addImplementationPlanCSS();
    addCollapsibleCSS();
    
    console.log('✅ COLLAPSIBLE Implementation plan displayed successfully');
}

/**
 * Render Quick Overview Section
 */
function renderQuickOverview(summary, intelligence, phases) {
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-info text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#quick-overview">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">
                        <i class="fas fa-eye me-2"></i>Quick Overview & Key Insights
                    </h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="quick-overview">
                <div class="card-body">
                    ${renderKeyRecommendations(summary)}
                    ${renderIntelligenceInsights(intelligence)}
                    ${renderPhasesSummary(phases)}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Phases Summary
 */
function renderPhasesSummary(phases) {
    return `
        <div class="row">
            <div class="col-12">
                <h6 class="text-primary mb-3"><i class="fas fa-list-ol me-2"></i>Phases Summary</h6>
                <div class="row">
                    ${phases.map((phase, idx) => `
                        <div class="col-md-6 col-lg-4 mb-3">
                            <div class="card border-start border-4 border-primary">
                                <div class="card-body p-3">
                                    <h6 class="card-title mb-2">Phase ${phase.phase_number || idx + 1}</h6>
                                    <p class="card-text small mb-2">${phase.title}</p>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="badge bg-success">$${phase.projected_savings.toLocaleString()}/mo</span>
                                        <small class="text-muted">${phase.duration_weeks}w</small>
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
 * Render Collapsible Phases
 */
function renderCollapsiblePhases(phases) {
    return phases.map((phase, idx) => `
        <div class="phase-container border-bottom">
            <!-- Phase Header (Always Visible) -->
            <div class="phase-header p-3" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); cursor: pointer;" 
                 data-bs-toggle="collapse" data-bs-target="#phase-${phase.phase_number || idx + 1}">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <h5 class="mb-0 me-3">
                            <i class="fas fa-cog me-2 text-primary"></i>
                            Phase ${phase.phase_number || idx + 1}: ${phase.title}
                        </h5>
                        <div class="d-flex gap-2">
                            <span class="badge bg-light text-dark">${phase.duration_weeks} weeks</span>
                            <span class="badge bg-success">$${phase.projected_savings.toLocaleString()}/mo</span>
                            <span class="badge bg-${getPriorityColor(phase.priority_level)}">${phase.priority_level}</span>
                        </div>
                    </div>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
                <div class="mt-2">
                    <small class="text-muted">
                        Week ${phase.start_week} - ${phase.end_week} • 
                        ${phase.complexity_level} Complexity • 
                        ${phase.risk_level} Risk • 
                        ${phase.tasks?.length || 0} Tasks
                    </small>
                </div>
            </div>
            
            <!-- Phase Details (Collapsible) -->
            <div class="collapse" id="phase-${phase.phase_number || idx + 1}">
                <div class="card-body">
                    <!-- Phase Overview -->
                    <div class="row mb-4">
                        <div class="col-md-8">
                            <div class="row">
                                <div class="col-sm-6">
                                    <strong>📅 Timeline:</strong> Week ${phase.start_week} - ${phase.end_week}<br>
                                    <strong>🔧 Complexity:</strong> ${phase.complexity_level}<br>
                                    <strong>🛡️ Risk Level:</strong> <span class="badge bg-${getRiskColor(phase.risk_level)}">${phase.risk_level}</span>
                                </div>
                                <div class="col-sm-6">
                                    <strong>👥 Engineering Hours:</strong> ${phase.resource_requirements?.engineering_hours || 'TBD'}<br>
                                    <strong>💼 FTE Estimate:</strong> ${phase.resource_requirements?.fte_estimate || 'TBD'}<br>
                                    <strong>🎯 Type:</strong> ${phase.type}
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="alert alert-success mb-0">
                                <div class="text-center">
                                    <div class="h4 mb-1">$${phase.projected_savings.toLocaleString()}</div>
                                    <small>Monthly Savings Target</small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- COLLAPSIBLE SUB-SECTIONS -->
                    ${renderCollapsibleImplementationTasks(phase)}
                    ${renderCollapsibleSuccessCriteria(phase)}
                    ${renderCollapsibleValidationSteps(phase)}
                    ${renderCollapsibleMonitoringRequirements(phase)}
                    ${renderCollapsibleRollbackPlan(phase)}
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * Render Collapsible Implementation Tasks
 */
function renderCollapsibleImplementationTasks(phase) {
    if (!phase.tasks?.length) return '';
    
    return `
        <div class="mb-4">
            <div class="collapsible-section-header" data-bs-toggle="collapse" data-bs-target="#tasks-${phase.phase_number}">
                <h6 class="text-primary mb-0">
                    <i class="fas fa-tasks me-2"></i>Implementation Tasks (${phase.tasks.length} tasks)
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </h6>
            </div>
            
            <div class="collapse show" id="tasks-${phase.phase_number}">
                <div class="mt-3">
                    ${phase.tasks.map((task, idx) => {
                        const taskId = `task-${phase.phase_number || 0}-${idx}`;
                        const commandId = `cmd-${phase.phase_number || 0}-${idx}`;
                        
                        return `
                            <div class="task-block mb-3 border rounded">
                                <!-- Task Header (Always Visible) -->
                                <div class="task-header p-3 bg-light border-bottom" style="cursor: pointer;" 
                                     data-bs-toggle="collapse" data-bs-target="#${taskId}">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div class="flex-grow-1">
                                            <h6 class="mb-1">
                                                <span class="badge bg-primary me-2">${idx + 1}</span>
                                                ${task.title}
                                                <i class="fas fa-chevron-down collapse-icon"></i>
                                            </h6>
                                            <p class="text-muted mb-2 small">${task.description}</p>
                                            <div class="row text-sm">
                                                <div class="col-md-6">
                                                    <small><strong>⏱️ Hours:</strong> ${task.estimated_hours} | <strong>🎯 ID:</strong> ${task.task_id}</small>
                                                </div>
                                                <div class="col-md-6">
                                                    <small><strong>📦 Deliverable:</strong> ${task.deliverable.substring(0, 50)}...</small>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Task Details (Collapsible) -->
                                <div class="collapse" id="${taskId}">
                                    <div class="task-commands p-3">
                                        <div class="mb-3">
                                            <strong>🎯 Expected Outcome:</strong><br>
                                            <small class="text-muted">${task.expected_outcome}</small>
                                        </div>
                                        
                                        <!-- Commands Section -->
                                        <div class="d-flex justify-content-between align-items-center mb-2">
                                            <h6 class="mb-0"><i class="fas fa-terminal me-2"></i>Commands to Execute</h6>
                                            <button class="btn btn-sm btn-outline-primary copy-btn" onclick="copyCommand('${commandId}')">
                                                <i class="fas fa-copy me-1"></i>Copy All Commands
                                            </button>
                                        </div>
                                        <div class="command-wrapper">
                                            <pre class="command-code" id="${commandId}"><code>${escapeHtml(task.command)}</code></pre>
                                        </div>
                                        
                                        ${task.skills_required?.length ? `
                                            <div class="mt-3">
                                                <strong>🔧 Skills Required:</strong>
                                                ${task.skills_required.map(skill => `<span class="badge bg-secondary me-1">${skill}</span>`).join('')}
                                            </div>
                                        ` : ''}
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

/**
 * Render other collapsible sections for phases
 */
// function renderCollapsibleSuccessCriteria(phase) {
//     if (!phase.success_criteria?.length) return '';
    
//     return `
//         <div class="mb-4">
//             <div class="collapsible-section-header" data-bs-toggle="collapse" data-bs-target="#success-${phase.phase_number}">
//                 <h6 class="text-success mb-0">
//                     <i class="fas fa-trophy me-2"></i>Success Criteria (${phase.success_criteria.length})
//                     <i class="fas fa-chevron-down collapse-icon"></i>
//                 </h6>
//             </div>
//             <div class="collapse" id="success-${phase.phase_number}">
//                 <ul class="list-group list-group-flush mt-2">
//                     ${phase.success_criteria.map(criteria => `
//                         <li class="list-group-item border-0 px-0">
//                             <i class="fas fa-check-circle text-success me-2"></i>${criteria}
//                         </li>
//                     `).join('')}
//                 </ul>
//             </div>
//         </div>
//     `;
// }

function renderCollapsibleValidationSteps(phase) {
    if (!phase.validation_steps?.length) return '';
    
    return `
        <div class="mb-4">
            <div class="collapsible-section-header" data-bs-toggle="collapse" data-bs-target="#validation-${phase.phase_number}">
                <h6 class="text-info mb-0">
                    <i class="fas fa-clipboard-check me-2"></i>Validation Steps (${phase.validation_steps.length})
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </h6>
            </div>
            <div class="collapse" id="validation-${phase.phase_number}">
                <ul class="list-group list-group-flush mt-2">
                    ${phase.validation_steps.map(step => `
                        <li class="list-group-item border-0 px-0">
                            <i class="fas fa-check text-info me-2"></i>${step}
                        </li>
                    `).join('')}
                </ul>
            </div>
        </div>
    `;
}

function renderCollapsibleMonitoringRequirements(phase) {
    if (!phase.monitoring_requirements) return '';
    
    const monitoring = phase.monitoring_requirements;
    return `
        <div class="mb-4">
            <div class="collapsible-section-header" data-bs-toggle="collapse" data-bs-target="#monitoring-${phase.phase_number}">
                <h6 class="text-warning mb-0">
                    <i class="fas fa-chart-line me-2"></i>Monitoring Requirements
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </h6>
            </div>
            <div class="collapse" id="monitoring-${phase.phase_number}">
                <div class="mt-2">
                    <div class="row">
                        <div class="col-md-6">
                            <strong>📊 Key Metrics:</strong>
                            <ul class="list-unstyled mt-1">
                                ${(monitoring.key_metrics || []).map(metric => `
                                    <li><i class="fas fa-dot-circle text-warning me-2"></i>${metric}</li>
                                `).join('')}
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <strong>🔔 Alert Thresholds:</strong>
                            <ul class="list-unstyled mt-1">
                                ${Object.entries(monitoring.alert_thresholds || {}).map(([key, value]) => `
                                    <li><strong>${key.replace(/_/g, ' ')}:</strong> ${value}</li>
                                `).join('')}
                            </ul>
                            <strong>📅 Frequency:</strong> ${monitoring.monitoring_frequency}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderCollapsibleRollbackPlan(phase) {
    if (!phase.rollback_plan) return '';
    
    const rollback = phase.rollback_plan;
    return `
        <div class="mb-4">
            <div class="collapsible-section-header" data-bs-toggle="collapse" data-bs-target="#rollback-${phase.phase_number}">
                <h6 class="text-danger mb-0">
                    <i class="fas fa-undo me-2"></i>Rollback Plan
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </h6>
            </div>
            <div class="collapse" id="rollback-${phase.phase_number}">
                <div class="alert alert-light border-start border-4 border-danger mt-2">
                    <div class="row">
                        <div class="col-md-6">
                            <strong>⏱️ Rollback Time:</strong> ${rollback.rollback_time_estimate}<br>
                            <strong>📢 Communication:</strong> ${rollback.communication_plan}
                        </div>
                        <div class="col-md-6">
                            <strong>🚨 Trigger Conditions:</strong>
                            <ul class="list-unstyled mt-1">
                                ${(rollback.trigger_conditions || []).map(condition => `
                                    <li><i class="fas fa-exclamation-triangle text-danger me-1"></i>${condition}</li>
                                `).join('')}
                            </ul>
                        </div>
                    </div>
                    
                    ${rollback.rollback_steps?.length ? `
                        <div class="mt-3">
                            <strong>📋 Rollback Steps:</strong>
                            <ol class="mt-2">
                                ${rollback.rollback_steps.map(step => `<li>${step}</li>`).join('')}
                            </ol>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

// Keep existing helper functions
function renderKeyRecommendations(summary) {
    if (!summary.key_recommendations?.length) return '';
    
    return `
        <div class="mb-4">
            <h6 class="text-info mb-3"><i class="fas fa-lightbulb me-2"></i>Key Recommendations</h6>
            <div class="row">
                ${summary.key_recommendations.map((rec, idx) => `
                    <div class="col-md-4 mb-2">
                        <div class="d-flex align-items-center">
                            <span class="badge bg-info rounded-circle me-2">${idx + 1}</span>
                            <span>${rec}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
            ${summary.strategic_priorities?.length ? `
                <div class="mt-3 pt-3 border-top">
                    <strong>🎯 Strategic Priority:</strong> ${summary.strategic_priorities[0]}
                </div>
            ` : ''}
        </div>
    `;
}

function renderIntelligenceInsights(intelligence) {
    if (!intelligence.ai_recommendations?.length) return '';
    
    return `
        <div class="mb-4">
            <h6 class="text-purple mb-3"><i class="fas fa-brain me-2"></i>AI Intelligence Insights</h6>
            ${intelligence.ai_recommendations.map(rec => `
                <div class="alert alert-light border-start border-4 border-purple">
                    <i class="fas fa-robot me-2 text-purple"></i>${rec}
                </div>
            `).join('')}
        </div>
    `;
}

// Simplified framework sections for brevity
function renderCollapsibleGovernanceFramework(governance) {
    if (!governance || Object.keys(governance).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-dark text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#governance-section">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-gavel me-2"></i>Governance Framework</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="governance-section">
                <div class="card-body">
                    <div class="text-center text-muted py-4">
                        <i class="fas fa-info-circle fa-2x mb-3"></i>
                        <p>Governance framework details available for enterprise plans.</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderCollapsibleMonitoringStrategy(monitoring) {
    if (!monitoring || Object.keys(monitoring).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-warning text-dark" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#monitoring-section">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-chart-bar me-2"></i>Monitoring Strategy</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="monitoring-section">
                <div class="card-body">
                    <div class="text-center text-muted py-4">
                        <i class="fas fa-chart-line fa-2x mb-3"></i>
                        <p>Advanced monitoring strategy details available.</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderCollapsibleContingencyPlanning(contingency) {
    if (!contingency || Object.keys(contingency).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-secondary text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#contingency-section">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-shield-alt me-2"></i>Contingency Planning</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="contingency-section">
                <div class="card-body">
                    <div class="text-center text-muted py-4">
                        <i class="fas fa-shield-alt fa-2x mb-3"></i>
                        <p>Contingency planning details configured for your environment.</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderCollapsibleSuccessCriteria(success) {
    if (!success || Object.keys(success).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-success text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#success-section">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-target me-2"></i>Success Criteria</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="success-section">
                <div class="card-body">
                    <div class="text-center text-muted py-4">
                        <i class="fas fa-target fa-2x mb-3"></i>
                        <p>Success criteria and KPIs configured for your implementation.</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderCollapsibleTimelineOptimization(timeline) {
    if (!timeline || Object.keys(timeline).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-info text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#timeline-section">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-calendar-alt me-2"></i>Timeline Optimization</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="timeline-section">
                <div class="card-body">
                    <div class="text-center text-muted py-4">
                        <i class="fas fa-calendar-alt fa-2x mb-3"></i>
                        <p>Timeline optimization details and critical path analysis.</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderActionButtons(totalSavings) {
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
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        Complete implementation plan generated on ${new Date().toLocaleDateString()} • 
                        Total potential savings: <strong>$${totalSavings.toLocaleString()}/month</strong>
                    </small>
                </div>
            </div>
        </div>
    `;
}

// Global expand/collapse functions
export function expandAllSections() {
    document.querySelectorAll('.collapse:not(.show)').forEach(element => {
        const collapse = new bootstrap.Collapse(element, { show: true });
    });
    showNotification('📖 All sections expanded', 'info', 2000);
}

export function collapseAllSections() {
    document.querySelectorAll('.collapse.show').forEach(element => {
        const collapse = new bootstrap.Collapse(element, { hide: true });
    });
    showNotification('📕 All sections collapsed', 'info', 2000);
}

export function togglePhaseDetails() {
    const phaseDetails = document.querySelectorAll('[id^="phase-"]');
    const anyExpanded = Array.from(phaseDetails).some(el => el.classList.contains('show'));
    
    if (anyExpanded) {
        phaseDetails.forEach(element => {
            if (element.classList.contains('show')) {
                const collapse = new bootstrap.Collapse(element, { hide: true });
            }
        });
        showNotification('📘 Phase details collapsed', 'info', 2000);
    } else {
        phaseDetails.forEach(element => {
            if (!element.classList.contains('show')) {
                const collapse = new bootstrap.Collapse(element, { show: true });
            }
        });
        showNotification('📗 Phase details expanded', 'info', 2000);
    }
}

/**
 * Export implementation plan functionality
 */
export function exportImplementationPlan() {
    showNotification('Exporting complete implementation plan...', 'info');
    
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
            showNotification('Implementation plan exported successfully!', 'success');
        })
        .catch(error => {
            console.error('Export error:', error);
            showNotification('Export failed. Creating fallback...', 'warning');
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
        showNotification('Plan exported as text file', 'info');
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

// Add collapsible-specific CSS
function addCollapsibleCSS() {
    if (document.getElementById('collapsible-plan-css')) return;
    
    const style = document.createElement('style');
    style.id = 'collapsible-plan-css';
    style.textContent = `
        .collapsible-section-header {
            cursor: pointer;
            padding: 0.5rem 0;
            border-radius: 4px;
            transition: all 0.3s ease;
        }
        
        .collapsible-section-header:hover {
            background-color: rgba(0, 123, 255, 0.05);
        }
        
        .collapse-icon {
            transition: transform 0.3s ease;
            font-size: 0.875rem;
        }
        
        .collapsed .collapse-icon,
        [aria-expanded="false"] .collapse-icon {
            transform: rotate(-90deg);
        }
        
        .phase-container {
            transition: all 0.3s ease;
        }
        
        .phase-container:hover {
            background-color: rgba(0, 0, 0, 0.02);
        }
        
        .phase-header {
            border-left: 4px solid transparent;
            transition: all 0.3s ease;
        }
        
        .phase-header:hover {
            border-left-color: #007bff;
            background: linear-gradient(135deg, #f8f9fa 0%, #e3f2fd 100%) !important;
        }
        
        .task-block {
            transition: all 0.3s ease;
        }
        
        .task-block:hover {
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .card-header[data-bs-toggle="collapse"] {
            transition: all 0.3s ease;
        }
        
        .card-header[data-bs-toggle="collapse"]:hover {
            background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.2)) !important;
        }
        
        @media (max-width: 768px) {
            .phase-header .d-flex {
                flex-direction: column;
                align-items: flex-start !important;
            }
            
            .phase-header .d-flex .d-flex {
                margin-top: 0.5rem;
            }
        }
    `;
    document.head.appendChild(style);
}

function addImplementationPlanCSS() {
    // Check if CSS is already loaded
    if (document.getElementById('implementation-plan-css')) return;
    
    const style = document.createElement('style');
    style.id = 'implementation-plan-css';
    style.textContent = `
        /* Enhanced Implementation Plan Styling */
        
        #implementation-plan-container {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #2d3748;
        }
        
        .task-block { 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #dee2e6; 
            border-radius: 12px; 
            margin-bottom: 2rem; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .task-header { 
            background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%) !important; 
            border-bottom: 2px solid rgb(0, 255, 234); 
            padding: 1.5rem !important;
            position: relative;
        }
        
        .command-wrapper { 
            background: #f8f9fa; 
            border: 1px solid #e9ecef; 
            border-radius: 8px; 
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-top: 1rem; 
        }
        
        .command-code { 
            margin: 0 !important; 
            padding: 1.25rem !important; 
            background: #ffffff !important; 
            border: none !important; 
            border-left: 3px solid rgb(0, 255, 162) !important; 
            overflow-x: auto; 
            white-space: pre;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace !important; 
            font-size: 0.85rem !important; 
            line-height: 1.5 !important; 
            max-height: 400px;
            min-height: 60px;
        }
        
        .copy-btn { 
            background: linear-gradient(135deg,rgb(0, 255, 157),rgb(0, 170, 179)) !important; 
            border: none !important; 
            color: white !important; 
            font-size: 0.8rem !important; 
            padding: 0.5rem 1rem !important; 
            border-radius: 6px !important;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
        }
        
        .copy-btn:hover { 
            background: linear-gradient(135deg,rgb(0, 179, 152), #004085) !important; 
            transform: translateY(-1px);
        }
        
        /* Cards and General Styling */
        .card { 
            border-radius: 12px !important; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
            border: 1px solid rgba(0,0,0,0.08) !important;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            box-shadow: 0 8px 25px rgba(0,0,0,0.1) !important;
            transform: translateY(-2px);
        }
        
        .badge { 
            border-radius: 50px; 
            font-size: 0.75rem; 
            font-weight: 500;
            padding: 0.375rem 0.75rem;
        }
    `;
    document.head.appendChild(style);
}

// Make functions globally available for backward compatibility
if (typeof window !== 'undefined') {
    window.loadImplementationPlan = loadImplementationPlan;
    window.displayImplementationPlan = displayImplementationPlan;
    window.expandAllSections = expandAllSections;
    window.collapseAllSections = collapseAllSections;
    window.togglePhaseDetails = togglePhaseDetails;
    window.exportImplementationPlan = exportImplementationPlan;
    window.refreshImplementationPlan = refreshImplementationPlan;
    window.onAnalysisComplete = onAnalysisComplete;
}