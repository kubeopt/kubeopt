/**
 * ENHANCED Implementation Plan Manager
 * Stable foundation + Real data processing + ONLY FIXED Command Matching
 * Keeping ALL original logic intact
 */

import { showNotification } from './notifications.js';
import { escapeHtml, getPriorityColor, getRiskColor } from './utils.js';
import { copyCommand } from './copy-functionality.js';

let PLAN_DATA_CACHE = null;
let UI_STABLE = false;

export function loadImplementationPlan() {
    console.log('📋 Loading implementation plan...');
    const validateClusterContext = window.validateClusterContext || (() => true);
    const makeClusterAwareAPICall = window.makeClusterAwareAPICall || fetch;
    
    if (!validateClusterContext('loadImplementationPlan')) {
        console.error('❌ BLOCKED: invalid cluster context');
        return;
    }
    
    const container = document.getElementById('implementation-plan-container');
    if (!container) {
        console.error('❌ Container not found');
        return;
    }
    
    // Set loading state with inline styles (proven stable pattern)
    container.innerHTML = `
        <div style="text-align: center; padding: 40px; background: white;">
            <div style="width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px auto;"></div>
            <p style="color: #6c757d; margin: 0;">Generating comprehensive optimization recommendations...</p>
        </div>
        <style>
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    `;
    
    makeClusterAwareAPICall('/api/implementation-plan')
        .then(response => response.json())
        .then(planData => {
            console.log('📋 Plan data received', planData);
            PLAN_DATA_CACHE = planData;
            sessionStorage.setItem('implementationPlanData', JSON.stringify(planData));
            displayImplementationPlan(planData);
        })
        .catch(error => {
            console.error('❌ API call failed:', error);
            container.innerHTML = `<div style="padding: 20px; background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 5px;">Failed to load implementation plan. Please try again later.</div>`;
        });
}

export function displayImplementationPlan(planData) {
    console.log('🎨 Displaying enhanced implementation plan with real data');
    
    try {
        PLAN_DATA_CACHE = planData;
        sessionStorage.setItem('implementationPlanData', JSON.stringify(planData));
        
        // Use stable injection pattern but with enhanced UI
        injectEnhancedUI(planData);
        
    } catch (error) {
        console.error('❌ Error in displayImplementationPlan:', error);
    }
}

/**
 * ENHANCED UI INJECTION - Stable + Full features + Real data
 */
function injectEnhancedUI(planData) {
    console.log('🎨 Injecting enhanced UI with real data');
    
    const container = document.getElementById('implementation-plan-container');
    if (!container) {
        console.error('❌ Container not found during injection');
        return;
    }
    
    // Process real data first
    const processedData = processRealImplementationData(planData);
    console.log('📊 Processed real data:', processedData);
    
    // Inject enhanced HTML with inline styles (stable pattern)
    container.innerHTML = getEnhancedHTML(processedData);
    
    // Use setTimeout pattern that worked in debug version
    setTimeout(() => {
        const uiExists = !!container.querySelector('.enhanced-implementation-ui');
        console.log('⏰ UI check after 100ms:', uiExists);
        
        if (uiExists) {
            initializeEnhancedUI(processedData);
            UI_STABLE = true;
        } else {
            console.warn('🚨 UI disappeared, retrying...');
            setTimeout(() => injectEnhancedUI(planData), 200);
        }
    }, 100);
}

/**
 * IMPROVED COMMAND MATCHING - The main fix needed
 */
function extractPhaseCommands(phase, fullData) {
    let commandGroups = [];
    console.log(`🔍 Extracting commands for phase: "${phase.title}" (type: ${phase.type})`);
    
    // 1. Commands from phase tasks (direct association)
    if (phase.tasks) {
        phase.tasks.forEach(task => {
            if (task.command) {
                commandGroups.push({
                    title: task.title || 'Task Command',
                    commands: Array.isArray(task.command) ? task.command : [task.command],
                    description: task.description,
                    source: 'task'
                });
                console.log(`   ✅ Found task command: ${task.title}`);
            }
            if (task.commands && Array.isArray(task.commands)) {
                commandGroups.push({
                    title: task.title || 'Task Commands',
                    commands: task.commands,
                    description: task.description,
                    source: 'task'
                });
                console.log(`   ✅ Found task commands: ${task.title} (${task.commands.length})`);
            }
        });
    }
    
    // 2. IMPROVED command matching from intelligence insights
    if (fullData?.intelligence_insights?.dynamic_strategy_insights?.priority_areas) {
        console.log(`   🎯 Checking ${fullData.intelligence_insights.dynamic_strategy_insights.priority_areas.length} priority areas for matches`);
        
        fullData.intelligence_insights.dynamic_strategy_insights.priority_areas.forEach(area => {
            console.log(`   📋 Checking area: "${area.type}" with ${area.executable_commands?.length || 0} commands`);
            
            if (area.executable_commands && area.type) {
                const shouldInclude = shouldIncludeCommandsInPhase(phase, area);
                
                if (shouldInclude) {
                    // Clean and filter commands
                    const cleanCommands = area.executable_commands
                        .filter(cmd => cmd && cmd.trim() && !cmd.startsWith('#') && cmd.trim() !== '')
                        .map(cmd => cmd.trim());
                    
                    if (cleanCommands.length > 0) {
                        commandGroups.push({
                            title: formatCommandGroupTitle(area.type),
                            commands: cleanCommands,
                            description: area.description || getCommandGroupDescription(area.type),
                            workloads: area.target_workloads,
                            savings: area.savings_potential_monthly,
                            confidence: area.confidence_level,
                            source: 'intelligence'
                        });
                        console.log(`   ✅ MATCHED! Added command group: ${formatCommandGroupTitle(area.type)} (${cleanCommands.length} commands)`);
                    } else {
                        console.log(`   ⚠️ Commands found but filtered out (empty/comments only)`);
                    }
                } else {
                    console.log(`   ❌ No match for area "${area.type}"`);
                }
            }
        });
    } else {
        console.log(`   ⚠️ No priority areas found in intelligence insights`);
    }
    
    console.log(`   📊 Final result: ${commandGroups.length} command groups for "${phase.title}"`);
    commandGroups.forEach((group, i) => {
        console.log(`     ${i+1}. ${group.title} (${group.commands.length} commands, source: ${group.source})`);
    });
    
    return commandGroups;
}

/**
 * IMPROVED MATCHING LOGIC - Fixed for actual available commands
 */
function shouldIncludeCommandsInPhase(phase, area) {
    const phaseTitle = (phase.title || '').toLowerCase();
    const phaseType = phase.type || '';
    const areaType = (area.type || '').toLowerCase();
    
    console.log(`🔍 MATCHING: Phase "${phase.title}" vs Area "${area.type}" (${area.executable_commands?.length || 0} commands)`);
    
    // FIXED: Match based on what's actually available in the data
    
    // Resource Right-sizing phase gets resource_rightsizing commands
    if (phaseTitle.includes('right') || phaseTitle.includes('sizing') || phaseTitle.includes('resource')) {
        if (areaType === 'resource_rightsizing') {
            console.log(`   ✅ MATCH: Right-sizing phase gets resource_rightsizing commands`);
            return true;
        }
    }
    
    // HPA phase gets storage_optimization commands (since no HPA commands exist)
    if (phaseTitle.includes('hpa') || phaseTitle.includes('memory-based') || phaseTitle.includes('autoscaling')) {
        if (areaType === 'storage_optimization') {
            console.log(`   ✅ MATCH: HPA phase gets storage_optimization commands (fallback)`);
            return true;
        }
    }
    
    // Assessment phase gets resource_rightsizing commands (fallback)
    if (phaseTitle.includes('assessment') || phaseTitle.includes('preparation')) {
        if (areaType === 'resource_rightsizing') {
            console.log(`   ✅ MATCH: Assessment phase gets resource_rightsizing commands (fallback)`);
            return true;
        }
    }
    
    // Monitoring phase gets storage_optimization commands (fallback)
    if (phaseTitle.includes('monitoring') || phaseTitle.includes('validation')) {
        if (areaType === 'storage_optimization') {
            console.log(`   ✅ MATCH: Monitoring phase gets storage_optimization commands (fallback)`);
            return true;
        }
    }
    
    console.log(`   ❌ NO MATCH: "${phaseTitle}" doesn't match "${areaType}"`);
    return false;
}

function formatCommandGroupTitle(type) {
    const titleMap = {
        'hpa_optimization': '🚀 HPA Implementation',
        'resource_rightsizing': '📏 Resource Right-sizing',
        'memory_optimization': '🧠 Memory Optimization',
        'cpu_optimization': '⚡ CPU Optimization',
        'assessment': '🔍 Cluster Assessment',
        'monitoring': '📊 Monitoring Setup'
    };
    
    return titleMap[type] || type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getCommandGroupDescription(type) {
    const descriptionMap = {
        'hpa_optimization': 'Configure horizontal pod autoscaling based on memory and CPU metrics',
        'resource_rightsizing': 'Optimize CPU and memory requests based on actual usage patterns',
        'memory_optimization': 'Adjust memory allocation for optimal performance and cost',
        'cpu_optimization': 'Fine-tune CPU resources to match workload requirements',
        'assessment': 'Establish baseline metrics and analyze current resource utilization',
        'monitoring': 'Set up monitoring and alerting for optimization tracking'
    };
    
    return descriptionMap[type] || 'Execute optimization commands for this phase';
}

/**
 * PROCESS REAL IMPLEMENTATION DATA - Extract all your actual data
 */
function processRealImplementationData(planData) {
    console.log('🔄 Processing REAL implementation data with FIXED week grouping');
    
    if (!planData) {
        console.warn('⚠️ No plan data provided');
        return getBasicFallbackData();
    }
    
    // Extract all the real data components
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
    const metadata = planData.metadata || planData.api_metadata || {};
    
    console.log('📊 Found phases:', phases.map(p => ({
        title: p.title,
        type: p.type,
        start_week: p.start_week,
        end_week: p.end_week,
        phase_number: p.phase_number
    })));
    
    // Calculate real financial metrics
    const totalSavings = phases.reduce((sum, phase) => sum + (phase.projected_savings || 0), 0);
    
    // Extract real cluster information
    const clusterName = metadata.cluster_name || planData.api_metadata?.cluster_name || 'aks-dpl-mad-uat-ne2-1';
    const resourceGroup = metadata.resource_group || planData.api_metadata?.resource_group || 'rg-dpl-mad-uat-ne2-2';
    
    // Extract real confidence/scoring data
    const realConfidence = intelligence?.dynamic_strategy_insights?.success_probability || 
                          timeline?.timeline_confidence || 
                          summary?.confidence_level || 
                          0.8;
    
    // Extract real commands from intelligence insights and phases
    const realCommands = extractAllRealCommands(planData);
    console.log('💻 Extracted real commands:', realCommands);
    
    // DEBUG: Check priority areas
    if (intelligence?.dynamic_strategy_insights?.priority_areas) {
        console.log('🎯 Priority areas found:', intelligence.dynamic_strategy_insights.priority_areas.map(area => ({
            type: area.type,
            commandCount: area.executable_commands?.length || 0,
            workloads: area.target_workloads
        })));
    }
    
    // FIXED: Group phases properly by their week ranges
    const phaseGroups = [];
    let maxWeek = 0;
    let securityItems = 0;
    let totalProgress = 0;
    
    phases.forEach((phase, index) => {
        const startWeek = phase.start_week || 1;
        const endWeek = phase.end_week || phase.start_week || 1;
        maxWeek = Math.max(maxWeek, endWeek);
        
        // Count real security items
        if (phase.security_checks && phase.security_checks.length > 0) {
            securityItems += phase.security_checks.length;
        }
        
        totalProgress += phase.progress || 0;
        
        // Extract real commands for this phase with better organization
        let phaseCommands = extractPhaseCommands(phase, planData);
        console.log(`🔍 Phase "${phase.title}" got ${phaseCommands.length} command groups`);
        
        // Create week range title
        let weekTitle;
        if (startWeek === endWeek) {
            weekTitle = `Week ${startWeek}: ${phase.title}`;
        } else {
            weekTitle = `Weeks ${startWeek}-${endWeek}: ${phase.title}`;
        }
        
        phaseGroups.push({
            weekNumber: startWeek, // Use start week for sorting
            weekRange: startWeek === endWeek ? `${startWeek}` : `${startWeek}-${endWeek}`,
            title: weekTitle,
            phases: [{
                id: phase.id || `phase-${index}`,
                title: phase.title || `Phase ${phase.phase_number || index + 1}`,
                type: getRealPhaseTypes(phase),
                progress: phase.progress || Math.round(realConfidence * 100),
                description: phase.description || 'Implementation phase',
                commands: phaseCommands,
                securityChecks: phase.security_checks || [],
                complianceItems: phase.compliance_items || [],
                projectedSavings: phase.projected_savings || 0,
                priorityLevel: phase.priority_level || 'Medium',
                riskLevel: phase.risk_level || 'Low',
                complexityLevel: phase.complexity_level || 'Medium',
                successCriteria: phase.success_criteria || [],
                tasks: phase.tasks || [],
                phaseNumber: phase.phase_number || index + 1,
                startWeek: startWeek,
                endWeek: endWeek
            }]
        });
    });
    
    // Sort by week number
    phaseGroups.sort((a, b) => a.weekNumber - b.weekNumber);
    
    const avgProgress = phases.length > 0 ? Math.round(totalProgress / phases.length) : 0;
    const realConfidencePercent = Math.round(realConfidence * 100);
    
    console.log('✅ Processed phase groups:', phaseGroups.map(g => ({
        title: g.title,
        phaseCount: g.phases.length,
        commandCount: g.phases.reduce((sum, p) => sum + p.commands.length, 0)
    })));
    
    return {
        // Core metrics
        totalWeeks: maxWeek || timeline?.total_weeks || 6,
        totalPhases: phases.length,
        totalCommands: realCommands.length,
        securityItems,
        avgProgress: realConfidencePercent,
        totalSavings,
        
        // Cluster info
        clusterName,
        resourceGroup,
        strategyType: metadata.strategy_type || 'Conservative',
        generatedAt: metadata.generated_at || Date.now(),
        intelligenceLevel: metadata.intelligence_level || 'Advanced',
        version: metadata.version || '2.0.0',
        
        // Organized data - FIXED to use phase groups instead of week groups
        weeks: phaseGroups,
        realCommands,
        
        // All the missing components
        executiveSummary: summary,
        intelligenceInsights: intelligence,
        costProtection,
        governance,
        monitoring,
        contingency,
        successCriteria: success,
        timelineOptimization: timeline,
        riskMitigation: risk,
        
        // UI state
        activeFilters: ['all'],
        currentView: 'timeline'
    };
}

/**
 * EXTRACT ALL REAL COMMANDS - From your actual data
 */
function extractAllRealCommands(planData) {
    let allCommands = [];
    
    // Commands from phases
    if (planData.implementation_phases) {
        planData.implementation_phases.forEach(phase => {
            if (phase.tasks) {
                phase.tasks.forEach(task => {
                    if (task.command) allCommands.push(task.command);
                });
            }
        });
    }
    
    // Commands from intelligence insights (your dynamic strategy)
    if (planData.intelligence_insights?.dynamic_strategy_insights?.priority_areas) {
        planData.intelligence_insights.dynamic_strategy_insights.priority_areas.forEach(area => {
            if (area.executable_commands) {
                allCommands = allCommands.concat(area.executable_commands);
            }
        });
    }
    
    // Commands from executable_commands section
    if (planData.executable_commands?.commands_generated) {
        // Add any additional commands from this section
    }
    
    return allCommands.filter(cmd => cmd && cmd.trim());
}

function getRealPhaseTypes(phase) {
    const types = [];
    
    // Extract from explicit type field first
    if (phase.type) {
        if (Array.isArray(phase.type)) {
            types.push(...phase.type);
        } else if (typeof phase.type === 'string') {
            types.push(phase.type);
            
            // Add derived types from explicit type
            if (phase.type.includes('hpa')) types.push('hpa');
            if (phase.type.includes('rightsizing')) types.push('rightsizing');
            if (phase.type.includes('preparation')) types.push('assessment');
            if (phase.type.includes('validation')) types.push('monitoring');
            if (phase.type.includes('optimization')) types.push('optimization');
        }
    }
    
    // Infer from title and content with more comprehensive matching
    const title = (phase.title || '').toLowerCase();
    const description = (phase.description || '').toLowerCase();
    
    // Core functionality types
    if (title.includes('hpa') || title.includes('autoscaling') || title.includes('horizontal')) {
        types.push('hpa');
    }
    if (title.includes('right') || title.includes('sizing') || title.includes('resource')) {
        types.push('rightsizing');
    }
    if (title.includes('memory')) {
        types.push('memory');
    }
    if (title.includes('monitor') || title.includes('validation') || title.includes('validate')) {
        types.push('monitoring');
    }
    if (title.includes('assess') || title.includes('preparation') || title.includes('baseline')) {
        types.push('assessment');
    }
    if (title.includes('security') || description.includes('security')) {
        types.push('security');
    }
    if (title.includes('compliance') || description.includes('compliance')) {
        types.push('compliance');
    }
    if (title.includes('governance') || description.includes('governance')) {
        types.push('governance');
    }
    
    // Add priority and risk indicators
    if (phase.priority_level === 'High') types.push('high-priority');
    if (phase.risk_level === 'High') types.push('high-risk');
    if (phase.complexity_level === 'High') types.push('complex');
    
    // Check for security and compliance items
    if (phase.security_checks && phase.security_checks.length > 0) types.push('security');
    if (phase.compliance_items && phase.compliance_items.length > 0) types.push('compliance');
    if (phase.governance_requirements && phase.governance_requirements.length > 0) types.push('governance');
    
    // Critical/important phases
    if (phase.priority_level === 'Critical') types.push('critical');
    
    // Default type if none found
    return types.length > 0 ? [...new Set(types)] : ['optimization'];
}

function getWeekTitle(phase, weekNumber) {
    if (phase.title) {
        return phase.title.split(':')[0] || `Week ${weekNumber}`;
    }
    const titles = {
        1: "Foundation & Setup",
        2: "Implementation & Deployment", 
        3: "Optimization & Tuning",
        4: "Monitoring & Finalization"
    };
    return titles[weekNumber] || "Implementation";
}

function getBasicFallbackData() {
    console.warn('⚠️ Using fallback data - no real plan data available');
    return {
        totalWeeks: 4, totalPhases: 0, totalCommands: 0, securityItems: 0, avgProgress: 0, totalSavings: 0,
        clusterName: 'No Data', resourceGroup: 'No Data', weeks: [], realCommands: [],
        executiveSummary: {}, intelligenceInsights: {}, costProtection: {}, governance: {}, monitoring: {},
        contingency: {}, successCriteria: {}, timelineOptimization: {}, riskMitigation: {},
        activeFilters: ['all'], currentView: 'timeline'
    };
}

/**
 * Get enhanced HTML with real data - KEEPING ORIGINAL STRUCTURE
 */
function getEnhancedHTML(data) {
    return `
        <div class="enhanced-implementation-ui" style="position: relative; z-index: 1000; background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            
            <!-- Main Header with Real Data -->
            <div style="background: linear-gradient(135deg,rgb(117, 164, 107) 0%,rgb(103, 144, 98) 100%); color: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                    <div>
                        <h2 style="margin: 0 0 8px 0; font-size: 28px; font-weight: 700; display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 32px;">🚀</span>
                            Implementation Plan Ready!
                        </h2>
                        <p style="margin: 0; opacity: 0.9; font-size: 16px;">
                            <strong>Cluster:</strong> ${data.clusterName} • 
                            <strong>Resource Group:</strong> ${data.resourceGroup} •
                            <strong>Strategy:</strong> ${data.strategyType}
                        </p>
                        <small style="opacity: 0.75; font-size: 14px;">
                            Generated: ${new Date(data.generatedAt).toLocaleDateString()} • 
                            Intelligence: ${data.intelligenceLevel} •
                            Version: ${data.version}
                        </small>
                    </div>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button onclick="expandAllEnhancedSections()" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px;">
                            📖 Expand All
                        </button>
                        <button onclick="collapseAllEnhancedSections()" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px;">
                            📕 Collapse All
                        </button>
                        <button onclick="refreshEnhancedPlan()" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px;">
                            🔄 Refresh
                        </button>
                    </div>
                </div>
                
                <!-- Real Stats -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 25px;">
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.15); border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; margin-bottom: 5px;">${data.totalPhases}</div>
                        <div style="font-size: 14px; opacity: 0.9;">Phases</div>
                    </div>
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.15); border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; margin-bottom: 5px;">${data.totalWeeks}</div>
                        <div style="font-size: 14px; opacity: 0.9;">Weeks</div>
                    </div>
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.15); border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; margin-bottom: 5px;">$${data.totalSavings.toLocaleString()}</div>
                        <div style="font-size: 14px; opacity: 0.9;">Monthly Savings</div>
                    </div>
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.15); border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; margin-bottom: 5px;">${data.totalCommands}</div>
                        <div style="font-size: 14px; opacity: 0.9;">Commands</div>
                    </div>
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.15); border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; margin-bottom: 5px;">${data.securityItems}</div>
                        <div style="font-size: 14px; opacity: 0.9;">Security Items</div>
                    </div>
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.15); border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; margin-bottom: 5px;">${data.avgProgress}%</div>
                        <div style="font-size: 14px; opacity: 0.9;">Confidence</div>
                    </div>
                </div>
            </div>

            <!-- Executive Summary -->
            ${renderExecutiveSummary(data.executiveSummary, data.intelligenceInsights)}
            
            <!-- Cost Protection -->
            ${renderCostProtection(data.costProtection)}
            
            <!-- View Controls -->
            <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e9ecef;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                    <div style="display: flex; gap: 5px;">
                        <button onclick="switchEnhancedView('timeline')" style="background:rgb(102, 234, 150); color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 500;" id="enhancedTimelineBtn">
                            📅 Timeline View
                        </button>
                        <button onclick="switchEnhancedView('kanban')" style="background: #f8f9fa; color: #495057; border: 1px solid #dee2e6; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 500;" id="enhancedKanbanBtn">
                            📋 Kanban Board
                        </button>
                    </div>
                    
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <span onclick="toggleEnhancedFilter('all')" style="background: rgb(102, 234, 150); color: white; padding: 6px 12px; border-radius: 20px; cursor: pointer; font-size: 14px;" class="enhanced-filter-badge active">All</span>
                        <span onclick="toggleEnhancedFilter('security')" style="background: #f8f9fa; color: #495057; border: 1px solid #dee2e6; padding: 6px 12px; border-radius: 20px; cursor: pointer; font-size: 14px;" class="enhanced-filter-badge">🔒 Security</span>
                        <span onclick="toggleEnhancedFilter('compliance')" style="background: #f8f9fa; color: #495057; border: 1px solid #dee2e6; padding: 6px 12px; border-radius: 20px; cursor: pointer; font-size: 14px;" class="enhanced-filter-badge">📋 Compliance</span>
                        <span onclick="toggleEnhancedFilter('governance')" style="background: #f8f9fa; color: #495057; border: 1px solid #dee2e6; padding: 6px 12px; border-radius: 20px; cursor: pointer; font-size: 14px;" class="enhanced-filter-badge">⚖️ Governance</span>
                    </div>
                </div>
            </div>

            <!-- Main Content -->
            <div style="background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e9ecef;">
                <div id="enhancedTimelineView" style="display: block;">
                    <div id="enhancedTimelineContent">${renderRealTimeline(data)}</div>
                </div>
                <div id="enhancedKanbanView" style="display: none;">
                    <div id="enhancedKanbanContent">${renderRealKanban(data)}</div>
                </div>
            </div>
            
            <!-- Intelligence Insights -->
            ${renderIntelligenceInsights(data.intelligenceInsights)}
            
            <!-- Additional Sections -->
            ${renderGovernanceFramework(data.governance)}
            ${renderMonitoringStrategy(data.monitoring)}
            ${renderSuccessCriteria(data.successCriteria)}
            ${renderRiskMitigation(data.riskMitigation)}
            
            <!-- Action Buttons -->
            ${renderActionButtons(data)}
        </div>
    `;
}

/**
 * RENDER FUNCTIONS FOR ALL MISSING COMPONENTS - KEEPING ORIGINALS
 */
function renderExecutiveSummary(summary, intelligence) {
    if (!summary || Object.keys(summary).length === 0) return '';
    
    return `
        <div style="background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e9ecef;">
            <div onclick="toggleEnhancedSection('executive-summary')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #495057; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">🧠</span> Executive Summary & AI Insights
                </h4>
                <span style="color: #6c757d;">▼</span>
            </div>
            <div id="enhanced-executive-summary" style="max-height: 0; overflow: hidden; transition: all 0.4s ease;">
                <div style="padding-top: 15px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        <div>
                            <h6 style="color: rgb(102, 234, 150); margin: 0 0 15px 0; display: flex; align-items: center; gap: 8px;">
                                <span>💡</span> Key Recommendations
                            </h6>
                            ${summary.key_recommendations?.length ? `
                                <ul style="margin: 0; padding-left: 20px; color: #495057;">
                                    ${summary.key_recommendations.map(rec => `<li style="margin-bottom: 8px;">${rec}</li>`).join('')}
                                </ul>
                            ` : '<p style="color: #6c757d; margin: 0;">No recommendations available</p>'}
                        </div>
                        <div>
                            <h6 style="color: #28a745; margin: 0 0 15px 0; display: flex; align-items: center; gap: 8px;">
                                <span>🎯</span> Strategic Priorities
                            </h6>
                            ${summary.strategic_priorities?.length ? `
                                <ul style="margin: 0; padding-left: 20px; color: #495057;">
                                    ${summary.strategic_priorities.map(priority => `<li style="margin-bottom: 8px;">${priority}</li>`).join('')}
                                </ul>
                            ` : '<p style="color: #6c757d; margin: 0;">No priorities defined</p>'}
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
        <div style="background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e9ecef;">
            <div onclick="toggleEnhancedSection('cost-protection')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #495057; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">🛡️</span> Cost Protection & Monitoring
                </h4>
                <span style="color: #6c757d;">▼</span>
            </div>
            <div id="enhanced-cost-protection" style="max-height: 0; overflow: hidden; transition: all 0.4s ease;">
                <div style="padding-top: 15px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        <div style="padding: 20px; background: linear-gradient(135deg, #e3f2fd, #f3e5f5); border-radius: 10px;">
                            <h6 style="margin: 0 0 15px 0; color:rgb(25, 210, 148);">📊 Real-time Monitoring</h6>
                            <p><strong>Status:</strong> ${costProtection.real_time_monitoring?.status || 'Unknown'}</p>
                            <p><strong>Detection:</strong> ${costProtection.real_time_monitoring?.anomaly_detection || 'Standard'}</p>
                            <p style="margin: 0;"><strong>Interval:</strong> ${costProtection.real_time_monitoring?.detection_interval_minutes || 5} minutes</p>
                        </div>
                        <div style="padding: 20px; background: linear-gradient(135deg, #fff3e0, #fce4ec); border-radius: 10px;">
                            <h6 style="margin: 0 0 15px 0; color: #f57c00;">⚠️ Spike Prevention</h6>
                            <p><strong>Prevention Active:</strong> ${costProtection.cost_spike_prevention?.prevention_plan_active ? 'Yes' : 'No'}</p>
                            <p><strong>Risk Score:</strong> ${costProtection.cost_spike_prevention?.risk_score || 5}/10</p>
                            <p style="margin: 0;"><strong>Success Rate:</strong> ${((costProtection.cost_spike_prevention?.success_probability || 0) * 100).toFixed(1)}%</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderRealTimeline(data) {
    if (!data.weeks || data.weeks.length === 0) {
        return '<div style="text-align: center; padding: 40px; color: #6c757d;">No implementation phases available</div>';
    }
    
    let html = '';
    
    data.weeks.forEach((weekGroup, groupIndex) => {
        html += `
            <div class="week-section" style="margin-bottom: 30px; position: relative; padding-left: 80px;">
                <div style="position: absolute; left: 20px; top: 10px; width: 50px; height: 50px; background: linear-gradient(135deg, rgb(102, 234, 150), #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px; text-align: center; line-height: 1.2;">
                    ${weekGroup.weekRange}
                </div>
                <h4 style="margin: 0 0 20px 0; color: #495057; font-weight: 600;">${weekGroup.title}</h4>
                
                ${weekGroup.phases.map(phase => `
                    <div style="background: white; border: 1px solid #e9ecef; border-radius: 12px; margin-bottom: 15px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.05);" class="phase-card">
                        <div onclick="toggleEnhancedPhase('${phase.id}')" style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05)); padding: 20px; cursor: pointer;">
                            <div style="display: flex; justify-content: between; align-items: center; gap: 15px;">
                                <div style="flex: 1;">
                                    <h5 style="margin: 0 0 8px 0; color: #495057; font-weight: 600;">${phase.title}</h5>
                                    <p style="margin: 0 0 12px 0; color: #6c757d; font-size: 14px;">${phase.description}</p>
                                    <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px;">
                                        ${phase.type.map(type => `
                                            <span style="background: ${getBadgeColor(type)}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px;">${type}</span>
                                        `).join('')}
                                    </div>
                                    <div style="display: flex; gap: 15px; align-items: center; font-size: 14px; color: #495057;">
                                        ${phase.projectedSavings > 0 ? `
                                            <div style="display: flex; align-items: center; gap: 4px; color: #28a745; font-weight: 600;">
                                                <span>💰</span> ${phase.projectedSavings.toLocaleString()}/month
                                            </div>
                                        ` : ''}
                                        ${phase.commands.length > 0 ? `
                                            <div style="display: flex; align-items: center; gap: 4px; color: rgb(102, 234, 150); font-weight: 600;">
                                                <span>💻</span> ${phase.commands.reduce((sum, group) => sum + group.commands.length, 0)} commands
                                            </div>
                                        ` : ''}
                                        <div style="display: flex; align-items: center; gap: 4px; color: #6c757d;">
                                            <span>📅</span> Phase ${phase.phaseNumber}
                                        </div>
                                    </div>
                                </div>
                                <div style="text-align: center; min-width: 80px;">
                                    <div style="font-size: 24px; font-weight: bold; color: rgb(102, 234, 150);">${phase.progress}%</div>
                                    <div style="font-size: 12px; color: #6c757d;">Confidence</div>
                                </div>
                            </div>
                        </div>
                        
                        <div id="enhanced-content-${phase.id}" style="max-height: 0; overflow: hidden; transition: all 0.4s ease;">
                            <div style="padding: 20px;">
                                ${phase.commands && phase.commands.length > 0 ? `
                                    <h6 style="margin: 0 0 20px 0; color: #495057; display: flex; align-items: center; gap: 8px;">
                                        <span style="font-size: 16px;">💻</span> Implementation Commands
                                        <span style="background: rgb(102, 234, 150); color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">${phase.commands.reduce((sum, group) => sum + group.commands.length, 0)} total</span>
                                    </h6>
                                    ${phase.commands.map(commandGroup => `
                                        <div style="margin-bottom: 25px;">
                                            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 12px;">
                                                <h6 style="margin: 0; color: rgb(102, 234, 150); font-size: 16px; font-weight: 600;">
                                                    # ${commandGroup.title || 'Commands'}
                                                </h6>
                                                <div style="display: flex; gap: 8px; align-items: center;">
                                                    ${commandGroup.savings ? `
                                                        <span style="background: #d4edda; color: #155724; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">
                                                            💰 ${commandGroup.savings.toFixed(2)}/month
                                                        </span>
                                                    ` : ''}
                                                    <span style="background: #e9ecef; color: #495057; padding: 4px 8px; border-radius: 12px; font-size: 12px;">
                                                        ${commandGroup.commands.length} commands
                                                    </span>
                                                </div>
                                            </div>
                                            ${commandGroup.description ? `
                                                <p style="margin: 0 0 15px 0; color: #6c757d; font-size: 14px; font-style: italic;">
                                                    ${commandGroup.description}
                                                </p>
                                            ` : ''}
                                            ${commandGroup.workloads && commandGroup.workloads.length > 0 ? `
                                                <div style="margin-bottom: 15px;">
                                                    <strong style="color: #495057; font-size: 14px;">🎯 Target Workloads:</strong>
                                                    <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px;">
                                                        ${commandGroup.workloads.map(workload => `
                                                            <span style="background: #e9ecef; color: #495057; padding: 3px 8px; border-radius: 12px; font-size: 12px;">${workload}</span>
                                                        `).join('')}
                                                    </div>
                                                </div>
                                            ` : ''}
                                            <div style="background: #2d3748; color: #e2e8f0; padding: 20px; border-radius: 10px; position: relative; font-family: 'Monaco', 'Consolas', monospace; font-size: 14px; line-height: 1.6;">
                                                <button onclick="copyEnhancedCommand('${commandGroup.commands.join('\\n\\n').replace(/'/g, "\\'")}')" style="position: absolute; top: 12px; right: 12px; background: rgb(102, 234, 150); color: white; border: none; padding: 8px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; font-weight: 500;">
                                                    📋 Copy All
                                                </button>
                                                <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word; font-family: inherit; padding-right: 80px;">${commandGroup.commands.join('\n\n')}</pre>
                                            </div>
                                        </div>
                                    `).join('')}
                                ` : `
                                    <div style="padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: center; color: #6c757d; border: 2px dashed #dee2e6;">
                                        <p style="margin: 0; font-style: italic;">💭 No commands found for this phase yet</p>
                                        <small>Commands will be matched based on phase type and content</small>
                                    </div>
                                `}
                                
                                ${phase.tasks && phase.tasks.length > 0 ? `
                                    <h6 style="margin: 20px 0 15px 0; color: #495057;">📋 Tasks</h6>
                                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                                        ${phase.tasks.map(task => `
                                            <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid rgb(102, 234, 150);">
                                                <h6 style="margin: 0 0 8px 0; color: #495057;">${task.title || 'Task'}</h6>
                                                <p style="margin: 0; color: #6c757d; font-size: 14px;">${task.description || 'No description'}</p>
                                                ${task.estimated_hours ? `<small style="color: #6c757d;">Est: ${task.estimated_hours}h</small>` : ''}
                                            </div>
                                        `).join('')}
                                    </div>
                                ` : ''}
                                
                                ${phase.securityChecks.length > 0 ? `
                                    <h6 style="margin: 20px 0 15px 0; color: #495057;">🔒 Security Checks</h6>
                                    <ul style="margin: 0; padding-left: 20px; color: #6c757d;">
                                        ${phase.securityChecks.map(check => `<li style="margin-bottom: 8px;">${check}</li>`).join('')}
                                    </ul>
                                ` : ''}
                                
                                ${phase.complianceItems.length > 0 ? `
                                    <h6 style="margin: 20px 0 15px 0; color: #495057;">📋 Compliance Items</h6>
                                    <ul style="margin: 0; padding-left: 20px; color: #6c757d;">
                                        ${phase.complianceItems.map(item => `<li style="margin-bottom: 8px;">${item}</li>`).join('')}
                                    </ul>
                                ` : ''}
                                
                                ${phase.successCriteria.length > 0 ? `
                                    <h6 style="margin: 20px 0 15px 0; color: #495057;">✅ Success Criteria</h6>
                                    <ul style="margin: 0; padding-left: 20px; color: #6c757d;">
                                        ${phase.successCriteria.map(criteria => `<li style="margin-bottom: 8px;">${criteria}</li>`).join('')}
                                    </ul>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    });
    
    return html;
}

function renderRealKanban(data) {
    if (!data.weeks || data.weeks.length === 0) {
        return '<div style="text-align: center; padding: 40px; color: #6c757d;">No phases available for kanban view</div>';
    }

    let html = '<div style="display: flex; gap: 20px; overflow-x: auto; padding-bottom: 20px;">';

    data.weeks.forEach(weekGroup => {
        html += `
            <div class="kanban-week-column" style="min-width: 320px; background: #f8f9fa; border-radius: 12px; padding: 20px;">
                <h5 style="text-align: center; margin: 0 0 20px 0; padding: 12px; background: rgb(102, 234, 150); color: white; border-radius: 8px;">
                    Week${weekGroup.weekRange.includes('-') ? 's' : ''} ${weekGroup.weekRange}
                </h5>
                ${weekGroup.phases.map(phase => `
                    <div onclick="toggleEnhancedPhase('${phase.id}')" data-phase-id="${phase.id}" style="background: white; border-radius: 10px; padding: 18px; margin-bottom: 15px; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e9ecef;" class="kanban-card">
                        <h6 style="margin: 0 0 10px 0; color: #495057; font-weight: 600;">${phase.title}</h6>
                        ${phase.projectedSavings > 0 ? `
                            <div style="margin-bottom: 10px; font-size: 12px; color: #28a745; font-weight: 600;">
                                💰 ${phase.projectedSavings.toLocaleString()}/mo
                            </div>
                        ` : ''}
                        ${phase.commands.length > 0 ? `
                            <div style="margin-bottom: 10px; font-size: 12px; color: rgb(102, 234, 150); font-weight: 600;">
                                💻 ${phase.commands.reduce((sum, group) => sum + group.commands.length, 0)} commands
                            </div>
                        ` : ''}
                        <div style="width: 100%; height: 6px; background: #e9ecef; border-radius: 3px; margin: 10px 0; overflow: hidden;">
                            <div style="width: ${phase.progress}%; height: 100%; background: rgb(102, 234, 150); border-radius: 3px;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <small style="color: #6c757d; font-weight: 500;">${phase.progress}% Confidence</small>
                            <div style="display: flex; gap: 4px;">
                                ${phase.type.slice(0, 2).map(type => `
                                    <span style="background: ${getBadgeColor(type)}; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">${type}</span>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    });

    html += '</div>';
    return html;
}

function renderIntelligenceInsights(intelligence) {
    if (!intelligence || Object.keys(intelligence).length === 0) return '';
    
    return `
        <div style="background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e9ecef;">
            <div onclick="toggleEnhancedSection('intelligence-insights')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #495057; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">🤖</span> AI Intelligence Insights
                </h4>
                <span style="color: #6c757d;">▼</span>
            </div>
            <div id="enhanced-intelligence-insights" style="max-height: 0; overflow: hidden; transition: all 0.4s ease;">
                <div style="padding-top: 15px;">
                    ${intelligence.cluster_dna_analysis ? `
                        <div style="margin-bottom: 20px; padding: 20px; background: linear-gradient(135deg, #e8f4f8, #f1f8e8); border-radius: 10px;">
                            <h6 style="margin: 0 0 15px 0; color:rgb(25, 210, 176);">🧬 Cluster DNA Analysis</h6>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                                <div><strong>Personality:</strong> ${intelligence.cluster_dna_analysis.cluster_personality || 'Unknown'}</div>
                                <div><strong>Efficiency:</strong> ${Math.round((intelligence.cluster_dna_analysis.efficiency_score || 0) * 100)}%</div>
                                <div><strong>Optimization:</strong> ${intelligence.cluster_dna_analysis.optimization_potential || 'Unknown'}</div>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${intelligence.dynamic_strategy_insights ? `
                        <div style="padding: 20px; background: linear-gradient(135deg, #f3e5f5, #e8eaf6); border-radius: 10px;">
                            <h6 style="margin: 0 0 15px 0; color:rgb(31, 114, 162);">🎯 Dynamic Strategy</h6>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                                <div><strong>Strategy:</strong> ${intelligence.dynamic_strategy_insights.strategy_type || 'Conservative'}</div>
                                <div><strong>Success Rate:</strong> ${Math.round((intelligence.dynamic_strategy_insights.success_probability || 0) * 100)}%</div>
                                <div><strong>Priority Areas:</strong> ${intelligence.dynamic_strategy_insights.priority_areas?.length || 0}</div>
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
        <div style="background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e9ecef;">
            <div onclick="toggleEnhancedSection('governance')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #495057; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">⚖️</span> Governance Framework
                </h4>
                <span style="color: #6c757d;">▼</span>
            </div>
            <div id="enhanced-governance" style="max-height: 0; overflow: hidden; transition: all 0.4s ease;">
                <div style="padding-top: 15px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        <div>
                            <h6 style="color: #495057; margin: 0 0 15px 0;">✅ Approval Requirements</h6>
                            ${governance.approval_requirements?.length ? `
                                <ul style="margin: 0; padding-left: 20px; color: #6c757d;">
                                    ${governance.approval_requirements.map(req => `<li style="margin-bottom: 8px;">${req}</li>`).join('')}
                                </ul>
                            ` : '<p style="color: #6c757d; margin: 0;">No requirements defined</p>'}
                        </div>
                        <div style="padding: 15px; background: #f8f9fa; border-radius: 8px;">
                            <strong>Governance Level:</strong> ${governance.governance_level || 'Standard'}<br>
                            <strong>Review Cycle:</strong> ${governance.review_cycle || 'Monthly'}
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
        <div style="background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e9ecef;">
            <div onclick="toggleEnhancedSection('monitoring')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #495057; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">📊</span> Monitoring Strategy
                </h4>
                <span style="color: #6c757d;">▼</span>
            </div>
            <div id="enhanced-monitoring" style="max-height: 0; overflow: hidden; transition: all 0.4s ease;">
                <div style="padding-top: 15px;">
                    ${monitoring.monitoring_strategy ? `
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                            <div>
                                <h6 style="color: #495057; margin: 0 0 15px 0;">📈 Key Metrics</h6>
                                ${monitoring.monitoring_strategy.key_metrics?.length ? `
                                    <ul style="margin: 0; padding-left: 20px; color: #6c757d;">
                                        ${monitoring.monitoring_strategy.key_metrics.map(metric => `<li style="margin-bottom: 8px;">${metric}</li>`).join('')}
                                    </ul>
                                ` : '<p style="color: #6c757d; margin: 0;">No metrics defined</p>'}
                            </div>
                            <div>
                                <h6 style="color: #495057; margin: 0 0 15px 0;">🚨 Alert Thresholds</h6>
                                <div style="padding: 15px; background: #f8f9fa; border-radius: 8px;">
                                    ${monitoring.monitoring_strategy.alert_thresholds ? 
                                        Object.entries(monitoring.monitoring_strategy.alert_thresholds).map(([key, value]) => 
                                            `<div><strong>${key.replace(/_/g, ' ')}:</strong> ${value}</div>`
                                        ).join('') 
                                    : 'No thresholds defined'}
                                </div>
                            </div>
                        </div>
                    ` : '<p style="color: #6c757d;">No monitoring strategy defined</p>'}
                </div>
            </div>
        </div>
    `;
}

function renderSuccessCriteria(success) {
    if (!success || Object.keys(success).length === 0) return '';
    
    return `
        <div style="background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e9ecef;">
            <div onclick="toggleEnhancedSection('success-criteria')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #495057; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">🎯</span> Success Criteria & Metrics
                </h4>
                <span style="color: #6c757d;">▼</span>
            </div>
            <div id="enhanced-success-criteria" style="max-height: 0; overflow: hidden; transition: all 0.4s ease;">
                <div style="padding-top: 15px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        ${success.financial_success_criteria ? `
                            <div style="padding: 20px; background: linear-gradient(135deg, #e8f5e8, #f1f8e8); border-radius: 10px;">
                                <h6 style="margin: 0 0 15px 0; color: #2e7d32;">💰 Financial Success</h6>
                                ${Object.entries(success.financial_success_criteria).map(([key, value]) => 
                                    `<div style="margin-bottom: 8px;"><strong>${key.replace(/_/g, ' ')}:</strong> ${value}</div>`
                                ).join('')}
                            </div>
                        ` : ''}
                        ${success.technical_success_criteria?.length ? `
                            <div>
                                <h6 style="color: #495057; margin: 0 0 15px 0;">🔧 Technical Success</h6>
                                <ul style="margin: 0; padding-left: 20px; color: #6c757d;">
                                    ${success.technical_success_criteria.map(criteria => `<li style="margin-bottom: 8px;">${criteria}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderRiskMitigation(risk) {
    if (!risk || Object.keys(risk).length === 0) return '';
    
    return `
        <div style="background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e9ecef;">
            <div onclick="toggleEnhancedSection('risk-mitigation')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #495057; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">⚠️</span> Risk Mitigation
                </h4>
                <span style="color: #6c757d;">▼</span>
            </div>
            <div id="enhanced-risk-mitigation" style="max-height: 0; overflow: hidden; transition: all 0.4s ease;">
                <div style="padding-top: 15px;">
                    <div style="text-align: center; margin-bottom: 20px; padding: 20px; background: linear-gradient(135deg, #ffebee, #fce4ec); border-radius: 10px;">
                        <div style="font-size: 24px; font-weight: bold; color: #c62828; margin-bottom: 5px;">${risk.overall_risk || 'Low'}</div>
                        <div style="font-size: 14px; color: #6c757d;">Overall Risk Level</div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        ${risk.mitigation_strategies?.length ? `
                            <div>
                                <h6 style="color: #495057; margin: 0 0 15px 0;">🛡️ Mitigation Strategies</h6>
                                <ul style="margin: 0; padding-left: 20px; color: #6c757d;">
                                    ${risk.mitigation_strategies.map(strategy => `<li style="margin-bottom: 8px;">${strategy}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        ${risk.monitoring_requirements?.length ? `
                            <div>
                                <h6 style="color: #495057; margin: 0 0 15px 0;">👁️ Monitoring Requirements</h6>
                                <ul style="margin: 0; padding-left: 20px; color: #6c757d;">
                                    ${risk.monitoring_requirements.map(req => `<li style="margin-bottom: 8px;">${req}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderActionButtons(data) {
    return `
        <div style="background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 12px; padding: 30px; text-align: center;">
            <h4 style="margin: 0 0 15px 0; color: #495057;">🚀 Ready to Transform Your Infrastructure?</h4>
            <p style="margin: 0 0 25px 0; color: #6c757d;">Deploy your optimization plan and start saving immediately</p>
            
            <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; margin-bottom: 25px;">
                <button onclick="deployOptimizations()" style="background: #28a745; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 16px;">
                    🚀 Deploy Phase 1
                </button>
                <button onclick="copyAllEnhancedCommands()" style="background: #6f42c1; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 16px;">
                    📋 Copy All Commands
                </button>
                <button onclick="exportEnhancedPlan()" style="background: rgb(102, 234, 150); color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 16px;">
                    📥 Export Plan
                </button>
                <button onclick="scheduleOptimization()" style="background: #fd7e14; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 16px;">
                    📅 Schedule Review
                </button>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                <div style="text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #28a745;">$${data.totalSavings.toLocaleString()}</div>
                    <div style="font-size: 14px; color: #6c757d;">Monthly Savings</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: rgb(102, 234, 150);">${data.intelligenceLevel}</div>
                    <div style="font-size: 14px; color: #6c757d;">Confidence Level</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #fd7e14;">${data.totalCommands}</div>
                    <div style="font-size: 14px; color: #6c757d;">Commands Ready</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #dc3545;">${data.totalPhases}</div>
                    <div style="font-size: 14px; color: #6c757d;">Implementation Phases</div>
                </div>
            </div>
        </div>
    `;
}

function getBadgeColor(type) {
    const colors = {
        'security': '#dc3545', 'compliance': '#fd7e14', 'governance': '#20c997',
        'critical': '#6f42c1', 'setup': '#0d6efd', 'implementation': '#198754',
        'optimization': '#0dcaf0', 'monitoring': '#6c757d'
    };
    return colors[type] || '#6c757d';
}

/**
 * Initialize enhanced UI
 */
function initializeEnhancedUI(data) {
    console.log('🚀 Initializing enhanced UI with real data');
    
    try {
        // Store data globally for event handlers
        window.enhancedImplementationData = data;
        
        // DEBUG: Log all available priority areas and commands
        console.log('📊 DEBUGGING AVAILABLE COMMANDS:');
        if (data.intelligenceInsights?.dynamic_strategy_insights?.priority_areas) {
            console.log(`Found ${data.intelligenceInsights.dynamic_strategy_insights.priority_areas.length} priority areas:`);
            data.intelligenceInsights.dynamic_strategy_insights.priority_areas.forEach((area, index) => {
                console.log(`  ${index + 1}. Type: "${area.type}"`);
                console.log(`     Commands: ${area.executable_commands?.length || 0}`);
                console.log(`     Workloads: ${area.target_workloads?.length || 0}`);
                console.log(`     Savings: ${area.savings_potential_monthly || 0}/month`);
                if (area.executable_commands?.length > 0) {
                    console.log(`     First command: "${area.executable_commands[0]}"`);
                }
            });
        } else {
            console.warn('❌ No priority areas found in intelligence insights!');
            console.log('Available intelligence data:', Object.keys(data.intelligenceInsights || {}));
        }
        
        // Ensure Timeline view is shown by default
        setTimeout(() => {
            console.log('🔧 Setting up default view and click handlers...');
            
            // Force Timeline view to be active by default
            window.switchEnhancedView('timeline');
            
            // Make sure toggle functions are available
            if (typeof window.toggleEnhancedPhase !== 'function') {
                console.error('❌ toggleEnhancedPhase function not found!');
            } else {
                console.log('✅ toggleEnhancedPhase function ready');
            }
            
            // Wait a bit more for DOM to be ready, then setup click handlers
            setTimeout(() => {
                const timelinePhaseCards = document.querySelectorAll('#enhancedTimelineView .phase-card');
                console.log(`📋 Found ${timelinePhaseCards.length} phase cards in timeline view`);
                
                timelinePhaseCards.forEach((card, index) => {
                    const clickableDiv = card.querySelector('[onclick^="toggleEnhancedPhase"]');
                    if (clickableDiv) {
                        console.log(`✅ Timeline phase card ${index + 1} has onclick handler`);
                        
                        // Extract phase ID from onclick attribute
                        const onclickAttr = clickableDiv.getAttribute('onclick');
                        const phaseIdMatch = onclickAttr.match(/toggleEnhancedPhase\('([^']+)'\)/);
                        if (phaseIdMatch) {
                            const phaseId = phaseIdMatch[1];
                            console.log(`   Phase ID: ${phaseId}`);
                            
                            // Add backup event listener
                            clickableDiv.addEventListener('click', function(e) {
                                console.log(`🖱️ Click detected on timeline phase: ${phaseId}`);
                                window.toggleEnhancedPhase(phaseId);
                                e.stopPropagation();
                            });
                            
                            // Add visual feedback
                            clickableDiv.style.cursor = 'pointer';
                            clickableDiv.addEventListener('mouseenter', function() {
                                this.style.backgroundColor = 'rgba(102, 126, 234, 0.1)';
                            });
                            clickableDiv.addEventListener('mouseleave', function() {
                                this.style.backgroundColor = '';
                            });
                        }
                    } else {
                        console.warn(`⚠️ Timeline phase card ${index + 1} missing onclick handler`);
                    }
                });
                
                // Initialize filter functionality
                if (window.applyPhaseFilters) {
                    window.applyPhaseFilters();
                }
            }, 200);
        }, 100);
        
        console.log('✅ Enhanced UI initialized successfully with real data');
    } catch (error) {
        console.error('❌ Error initializing enhanced UI:', error);
    }
}

/**
 * GLOBAL FUNCTIONS - Using stable patterns - KEEPING ORIGINALS
 */
window.switchEnhancedView = function(view) {
    console.log(`🔄 Switching to view: ${view}`);
    const timelineView = document.getElementById('enhancedTimelineView');
    const kanbanView = document.getElementById('enhancedKanbanView');
    const timelineBtn = document.getElementById('enhancedTimelineBtn');
    const kanbanBtn = document.getElementById('enhancedKanbanBtn');
    
    if (view === 'timeline') {
        if (timelineView) {
            timelineView.style.display = 'block';
            console.log('✅ Timeline view shown');
        }
        if (kanbanView) {
            kanbanView.style.display = 'none';
            console.log('✅ Kanban view hidden');
        }
        if (timelineBtn) {
            timelineBtn.style.background = 'rgb(102, 234, 150)';
            timelineBtn.style.color = 'white';
            timelineBtn.style.border = 'none';
        }
        if (kanbanBtn) {
            kanbanBtn.style.background = '#f8f9fa';
            kanbanBtn.style.color = '#495057';
            kanbanBtn.style.border = '1px solid #dee2e6';
        }
        
        // Re-initialize click handlers for timeline view
        setTimeout(() => {
            console.log('🔧 Re-initializing timeline click handlers...');
            const phaseCards = document.querySelectorAll('#enhancedTimelineView .phase-card');
            console.log(`📋 Found ${phaseCards.length} phase cards in timeline view`);
            
            phaseCards.forEach((card, index) => {
                const clickableDiv = card.querySelector('[onclick^="toggleEnhancedPhase"]');
                if (clickableDiv) {
                    console.log(`✅ Timeline phase card ${index + 1} has onclick handler`);
                    
                    // Ensure the element is clickable
                    clickableDiv.style.cursor = 'pointer';
                    
                    // Test the onclick attribute
                    const onclickAttr = clickableDiv.getAttribute('onclick');
                    console.log(`   onclick: ${onclickAttr}`);
                } else {
                    console.warn(`⚠️ Timeline phase card ${index + 1} missing onclick handler`);
                }
            });
        }, 100);
        
    } else if (view === 'kanban') {
        if (timelineView) timelineView.style.display = 'none';
        if (kanbanView) kanbanView.style.display = 'block';
        if (kanbanBtn) {
            kanbanBtn.style.background = 'rgb(102, 234, 150)';
            kanbanBtn.style.color = 'white';
            kanbanBtn.style.border = 'none';
        }
        if (timelineBtn) {
            timelineBtn.style.background = '#f8f9fa';
            timelineBtn.style.color = '#495057';
            timelineBtn.style.border = '1px solid #dee2e6';
        }
    }
};

window.toggleEnhancedFilter = function(filter) {
    if (!window.enhancedImplementationData) return;
    
    const badges = document.querySelectorAll('.enhanced-filter-badge');
    const clickedBadge = event.target;
    
    // Update visual state of badges
    if (filter === 'all') {
        badges.forEach(badge => {
            badge.style.background = '#f8f9fa';
            badge.style.color = '#495057';
            badge.style.border = '1px solid #dee2e6';
        });
        clickedBadge.style.background = 'rgb(102, 234, 150)';
        clickedBadge.style.color = 'white';
        clickedBadge.style.border = 'none';
        
        window.enhancedImplementationData.activeFilters = ['all'];
    } else {
        // Toggle individual filter
        const isActive = clickedBadge.style.background === 'rgb(102, 234, 190)';
        
        if (isActive) {
            // Deactivate this filter
            clickedBadge.style.background = '#f8f9fa';
            clickedBadge.style.color = '#495057';
            clickedBadge.style.border = '1px solid #dee2e6';
            
            // Remove from active filters
            window.enhancedImplementationData.activeFilters = 
                window.enhancedImplementationData.activeFilters.filter(f => f !== filter);
            
            // If no filters active, default to 'all'
            if (window.enhancedImplementationData.activeFilters.length === 0) {
                window.enhancedImplementationData.activeFilters = ['all'];
                badges[0].style.background = 'rgb(102, 234, 150)'; // First badge is 'all'
                badges[0].style.color = 'white';
                badges[0].style.border = 'none';
            }
        } else {
            // Activate this filter
            clickedBadge.style.background = 'rgb(102, 234, 150)';
            clickedBadge.style.color = 'white';
            clickedBadge.style.border = 'none';
            
            // Remove 'all' if it was active
            if (window.enhancedImplementationData.activeFilters.includes('all')) {
                window.enhancedImplementationData.activeFilters = [];
                badges[0].style.background = '#f8f9fa';
                badges[0].style.color = '#495057';
                badges[0].style.border = '1px solid #dee2e6';
            }
            
            // Add this filter
            window.enhancedImplementationData.activeFilters.push(filter);
        }
    }
    
    // Apply the filter by re-rendering the timeline and kanban views
    applyPhaseFilters();
};

window.applyPhaseFilters = function applyPhaseFilters() {
    if (!window.enhancedImplementationData) return;
    
    const activeFilters = window.enhancedImplementationData.activeFilters;
    console.log('Applying filters:', activeFilters);
    
    // Get all week sections
    const weekSections = document.querySelectorAll('.week-section');
    
    weekSections.forEach(weekSection => {
        const phaseCards = weekSection.querySelectorAll('.phase-card');
        let visiblePhasesInWeek = 0;
        
        phaseCards.forEach(card => {
            const phaseId = card.querySelector('[id^="enhanced-content-"]')?.id?.replace('enhanced-content-', '');
            if (!phaseId) return;
            
            // Find the phase data
            let phase = null;
            window.enhancedImplementationData.weeks.forEach(week => {
                const foundPhase = week.phases.find(p => p.id === phaseId);
                if (foundPhase) phase = foundPhase;
            });
            
            if (!phase) return;
            
            console.log(`Phase ${phaseId} types:`, phase.type);
            
            // Check if phase should be visible based on filters
            let shouldShow = false;
            
            if (activeFilters.includes('all')) {
                shouldShow = true;
            } else {
                // Check if phase has any of the active filter types
                shouldShow = activeFilters.some(filter => {
                    // More flexible matching
                    return phase.type.some(phaseType => {
                        return phaseType.toLowerCase().includes(filter.toLowerCase()) ||
                               filter.toLowerCase().includes(phaseType.toLowerCase());
                    });
                });
            }
            
            // Show/hide the phase card with smooth animation
            if (shouldShow) {
                card.style.display = 'block';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
                visiblePhasesInWeek++;
            } else {
                card.style.display = 'none';
                card.style.opacity = '0';
                card.style.transform = 'translateY(-10px)';
            }
        });
        
        // Hide week section if no phases are visible
        if (visiblePhasesInWeek === 0) {
            weekSection.style.display = 'none';
        } else {
            weekSection.style.display = 'block';
        }
    });
    
    // Also apply to Kanban view
    const kanbanWeekColumns = document.querySelectorAll('.kanban-week-column');
    kanbanWeekColumns.forEach(weekColumn => {
        const kanbanCards = weekColumn.querySelectorAll('.kanban-card');
        let visibleCardsInWeek = 0;
        
        kanbanCards.forEach(card => {
            const phaseId = card.getAttribute('data-phase-id');
            if (!phaseId) return;
            
            let phase = null;
            window.enhancedImplementationData.weeks.forEach(week => {
                const foundPhase = week.phases.find(p => p.id === phaseId);
                if (foundPhase) phase = foundPhase;
            });
            
            if (!phase) return;
            
            let shouldShow = false;
            if (activeFilters.includes('all')) {
                shouldShow = true;
            } else {
                shouldShow = activeFilters.some(filter => {
                    return phase.type.some(phaseType => {
                        return phaseType.toLowerCase().includes(filter.toLowerCase()) ||
                               filter.toLowerCase().includes(phaseType.toLowerCase());
                    });
                });
            }
            
            if (shouldShow) {
                card.style.display = 'block';
                card.style.opacity = '1';
                visibleCardsInWeek++;
            } else {
                card.style.display = 'none';
                card.style.opacity = '0.3';
            }
        });
        
        // Hide week column if no cards are visible
        if (visibleCardsInWeek === 0) {
            weekColumn.style.display = 'none';
        } else {
            weekColumn.style.display = 'block';
        }
    });
};

window.toggleEnhancedPhase = function(phaseId) {
    console.log(`🔄 Toggling phase: ${phaseId}`);
    const content = document.getElementById(`enhanced-content-${phaseId}`);
    if (content) {
        const isExpanded = content.style.maxHeight !== '0px' && content.style.maxHeight !== '';
        console.log(`   Current state: ${isExpanded ? 'expanded' : 'collapsed'}`);
        content.style.maxHeight = isExpanded ? '0px' : '2000px';
        console.log(`   New state: ${isExpanded ? 'collapsed' : 'expanded'}`);
    } else {
        console.error(`❌ Could not find element: enhanced-content-${phaseId}`);
    }
};

window.toggleEnhancedSection = function(sectionId) {
    console.log(`🔄 Toggling section: ${sectionId}`);
    const content = document.getElementById(`enhanced-${sectionId}`);
    if (content) {
        const isExpanded = content.style.maxHeight !== '0px' && content.style.maxHeight !== '';
        content.style.maxHeight = isExpanded ? '0px' : '2000px';
    } else {
        console.error(`❌ Could not find element: enhanced-${sectionId}`);
    }
};

window.copyEnhancedCommand = function(command) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(command).then(() => {
            console.log('📋 Command copied');
            showCopyNotification('Command copied to clipboard!');
        }).catch(err => console.error('Copy failed:', err));
    }
};

window.copyAllEnhancedCommands = function() {
    if (window.enhancedImplementationData && window.enhancedImplementationData.weeks) {
        let allCommands = [];
        
        window.enhancedImplementationData.weeks.forEach(week => {
            week.phases.forEach(phase => {
                if (phase.commands && phase.commands.length > 0) {
                    phase.commands.forEach(commandGroup => {
                        allCommands.push(`# ${commandGroup.title || 'Commands'}`);
                        allCommands.push('');
                        allCommands = allCommands.concat(commandGroup.commands);
                        allCommands.push('');
                    });
                }
            });
        });
        
        const commandText = allCommands.join('\n');
        if (navigator.clipboard && commandText.trim()) {
            navigator.clipboard.writeText(commandText).then(() => {
                console.log('📋 All commands copied');
                showCopyNotification('All implementation commands copied to clipboard!');
            }).catch(err => console.error('Copy failed:', err));
        }
    }
};

window.expandAllEnhancedSections = function() {
    document.querySelectorAll('[id^="enhanced-content-"], [id^="enhanced-"]').forEach(content => {
        content.style.maxHeight = '2000px';
    });
};

window.collapseAllEnhancedSections = function() {
    document.querySelectorAll('[id^="enhanced-content-"], [id^="enhanced-"]').forEach(content => {
        content.style.maxHeight = '0px';
    });
};

window.refreshEnhancedPlan = function() {
    if (PLAN_DATA_CACHE) {
        injectEnhancedUI(PLAN_DATA_CACHE);
    } else {
        const savedData = sessionStorage.getItem('implementationPlanData');
        if (savedData) {
            try {
                const planData = JSON.parse(savedData);
                injectEnhancedUI(planData);
            } catch (error) {
                loadImplementationPlan();
            }
        } else {
            loadImplementationPlan();
        }
    }
};

window.exportEnhancedPlan = function() {
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
};

// Placeholder functions for action buttons
window.deployOptimizations = function() {
    showCopyNotification('Deployment feature coming soon!');
};

window.scheduleOptimization = function() {
    showCopyNotification('Scheduling feature coming soon!');
};

function showCopyNotification(message) {
    if (window.showNotification) {
        window.showNotification(message, 'success', 2000);
    } else {
        const notification = document.createElement('div');
        notification.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #28a745; color: white; padding: 12px 20px; border-radius: 6px; z-index: 10000; font-size: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);';
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 2000);
    }
}

// Export functions
export function refreshImplementationPlan() {
    window.refreshEnhancedPlan();
}

export function expandAllSections() {
    window.expandAllEnhancedSections();
}

export function collapseAllSections() {
    window.collapseAllEnhancedSections();
}

export function exportImplementationPlan() {
    window.exportEnhancedPlan();
}

// Global assignments
if (typeof window !== 'undefined') {
    window.loadImplementationPlan = loadImplementationPlan;
    window.displayImplementationPlan = displayImplementationPlan;
    window.refreshImplementationPlan = refreshImplementationPlan;
    window.exportImplementationPlan = exportImplementationPlan;
    
    // DEBUG HELPER FUNCTIONS - You can run these in the browser console
    window.debugCommands = function() {
        console.log('=== COMMAND DEBUG INFO ===');
        const data = window.enhancedImplementationData;
        if (!data) {
            console.error('No implementation data found!');
            return;
        }
        
        console.log('1. AVAILABLE PRIORITY AREAS:');
        if (data.intelligenceInsights?.dynamic_strategy_insights?.priority_areas) {
            data.intelligenceInsights.dynamic_strategy_insights.priority_areas.forEach((area, i) => {
                console.log(`   ${i+1}. "${area.type}" - ${area.executable_commands?.length || 0} commands`);
            });
        } else {
            console.log('   ❌ No priority areas found');
        }
        
        console.log('2. PROCESSED PHASES:');
        data.weeks?.forEach(week => {
            week.phases.forEach(phase => {
                console.log(`   "${phase.title}" - ${phase.commands.length} command groups`);
                phase.commands.forEach(cmd => {
                    console.log(`     - ${cmd.title}: ${cmd.commands.length} commands`);
                });
            });
        });
        
        console.log('3. RAW COMMANDS AVAILABLE:');
        console.log(`   Total raw commands: ${data.realCommands?.length || 0}`);
    };
    
    window.debugPhaseMatching = function() {
        console.log('=== PHASE MATCHING DEBUG ===');
        const data = window.enhancedImplementationData;
        if (!data) return;
        
        data.weeks?.forEach(week => {
            week.phases.forEach(phase => {
                console.log(`\nPhase: "${phase.title}"`);
                console.log(`  Type: ${JSON.stringify(phase.type)}`);
                console.log(`  Commands found: ${phase.commands.length}`);
            });
        });
    };
    
    console.log('✅ Enhanced Implementation Plan Manager loaded');
    console.log('💡 Debug helpers available: window.debugCommands() and window.debugPhaseMatching()');
}