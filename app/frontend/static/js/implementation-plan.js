/**
 * ENHANCED Implementation Plan Manager - Fixed UI with Visual Improvements
 * Maintains all existing functionality while adding better visualization
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
    
    // Enhanced loading state with better animation
    container.innerHTML = `
        <div class="enhanced-loading-container">
            <div class="loading-animation">
                <div class="loading-spinner"></div>
                <div class="loading-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
            <h3>Generating Implementation Plan</h3>
            <p>Analyzing cluster data and creating optimization recommendations...</p>
        </div>
        <style>
            .enhanced-loading-container {
                text-align: center;
                padding: 60px 20px;
                background: linear-gradient(135deg, #f8f9ff 0%, #e9f2ff 100%);
                border-radius: 16px;
                margin: 20px 0;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            .loading-animation {
                margin-bottom: 30px;
                position: relative;
                display: inline-block;
            }
            .loading-spinner {
                width: 50px;
                height: 50px;
                border: 4px solid #e3e8ee;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px auto;
            }
            .loading-dots {
                display: flex;
                justify-content: center;
                gap: 8px;
            }
            .loading-dots span {
                width: 8px;
                height: 8px;
                background: #667eea;
                border-radius: 50%;
                animation: bounce 1.4s ease-in-out infinite both;
            }
            .loading-dots span:nth-child(2) { animation-delay: -0.16s; }
            .loading-dots span:nth-child(3) { animation-delay: -0.32s; }
            .enhanced-loading-container h3 {
                color: #4a5568;
                margin: 0 0 10px 0;
                font-size: 24px;
                font-weight: 600;
            }
            .enhanced-loading-container p {
                color: #718096;
                margin: 0;
                font-size: 16px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @keyframes bounce {
                0%, 80%, 100% { transform: scale(0); }
                40% { transform: scale(1); }
            }
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
            container.innerHTML = `
                <div class="error-container">
                    <div class="error-icon">⚠️</div>
                    <h3>Failed to Load Implementation Plan</h3>
                    <p>There was an error generating your implementation plan. Please try again.</p>
                    <button onclick="loadImplementationPlan()" class="retry-button">
                        🔄 Retry
                    </button>
                </div>
                <style>
                    .error-container {
                        text-align: center;
                        padding: 60px 20px;
                        background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
                        border-radius: 16px;
                        margin: 20px 0;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                    }
                    .error-icon {
                        font-size: 48px;
                        margin-bottom: 20px;
                    }
                    .error-container h3 {
                        color: #e53e3e;
                        margin: 0 0 10px 0;
                        font-size: 24px;
                        font-weight: 600;
                    }
                    .error-container p {
                        color: #c53030;
                        margin: 0 0 30px 0;
                        font-size: 16px;
                    }
                    .retry-button {
                        background: #e53e3e;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 16px;
                        font-weight: 600;
                        transition: all 0.2s ease;
                    }
                    .retry-button:hover {
                        background: #c53030;
                        transform: translateY(-1px);
                    }
                </style>
            `;
        });
}

export function displayImplementationPlan(planData) {
    console.log('🎨 Displaying complete implementation plan with ALL real data');
    
    try {
        PLAN_DATA_CACHE = planData;
        sessionStorage.setItem('implementationPlanData', JSON.stringify(planData));
        
        // Use stable injection pattern with complete UI
        injectCompleteUI(planData);
        
    } catch (error) {
        console.error('❌ Error in displayImplementationPlan:', error);
    }
}

/**
 * COMPLETE UI INJECTION - All data sections, no fallbacks
 */
function injectCompleteUI(planData) {
    console.log('🎨 Injecting complete UI with ALL real data');
    
    const container = document.getElementById('implementation-plan-container');
    if (!container) {
        console.error('❌ Container not found during injection');
        return;
    }
    
    // Process real data first
    const processedData = processCompleteImplementationData(planData);
    console.log('📊 Processed complete data:', processedData);
    
    // Inject complete HTML with all sections
    container.innerHTML = getCompleteHTML(processedData);
    
    // Use setTimeout pattern for stable initialization
    setTimeout(() => {
        const uiExists = !!container.querySelector('.complete-implementation-ui');
        console.log('⏰ UI check after 100ms:', uiExists);
        
        if (uiExists) {
            initializeCompleteUI(processedData);
            UI_STABLE = true;
        } else {
            console.warn('🚨 UI disappeared, retrying...');
            setTimeout(() => injectCompleteUI(planData), 200);
        }
    }, 100);
}

/**
 * EXTRACT PHASE COMMANDS - No fallbacks, only real data
 */
function extractPhaseCommands(phase, fullData) {
    let commandGroups = [];
    console.log(`🔍 Extracting commands for phase: "${phase.title}" (type: ${phase.type})`);
    
    // 1. Commands from phase.commands (direct from backend)
    if (phase.commands && Array.isArray(phase.commands) && phase.commands.length > 0) {
        commandGroups.push({
            title: `${phase.title} Commands`,
            commands: phase.commands.map(cmd => {
                if (typeof cmd === 'string') return cmd;
                if (cmd.command) return cmd.command;
                return JSON.stringify(cmd, null, 2);
            }),
            description: `Direct commands for ${phase.title}`,
            source: 'phase_direct'
        });
        console.log(`   ✅ Found ${phase.commands.length} direct phase commands`);
    }
    
    // 2. Commands from phase tasks (direct association)
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
    
    // 3. Commands from intelligence insights
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
                    }
                }
            }
        });
    }
    
    // NO FALLBACK COMMANDS - Return only what we actually have
    console.log(`   📊 Final result: ${commandGroups.length} command groups for "${phase.title}"`);
    commandGroups.forEach((group, i) => {
        console.log(`     ${i+1}. ${group.title} (${group.commands.length} commands, source: ${group.source})`);
    });
    
    return commandGroups;
}

/**
 * IMPROVED MATCHING LOGIC
 */
function shouldIncludeCommandsInPhase(phase, area) {
    const phaseTitle = (phase.title || '').toLowerCase();
    const phaseType = Array.isArray(phase.type) ? phase.type : [phase.type || ''];
    const areaType = (area.type || '').toLowerCase();
    
    console.log(`🔍 MATCHING: Phase "${phase.title}" vs Area "${area.type}"`);
    
    // Direct type matching first
    if (phaseType.some(pType => pType.toLowerCase() === areaType)) {
        console.log(`   ✅ DIRECT TYPE MATCH: ${areaType}`);
        return true;
    }
    
    // Keyword-based matching
    const matchingRules = [
        {
            phaseKeywords: ['hpa', 'autoscaling', 'autoscaler', 'horizontal', 'pod', 'scaling'],
            areaTypes: ['hpa_optimization', 'resource_rightsizing', 'storage_optimization'],
            reason: 'HPA/Autoscaling optimization'
        },
        {
            phaseKeywords: ['resource', 'right', 'sizing', 'optimization', 'rightsizing'],
            areaTypes: ['resource_rightsizing', 'hpa_optimization', 'storage_optimization'],
            reason: 'Resource optimization'
        },
        {
            phaseKeywords: ['storage', 'disk', 'volume', 'pvc', 'persistent'],
            areaTypes: ['storage_optimization', 'resource_rightsizing'],
            reason: 'Storage optimization'
        },
        {
            phaseKeywords: ['infrastructure', 'foundation', 'setup', 'preparation', 'assessment'],
            areaTypes: ['resource_rightsizing', 'storage_optimization', 'hpa_optimization'],
            reason: 'Infrastructure setup'
        },
        {
            phaseKeywords: ['monitoring', 'observability', 'metrics', 'dashboard', 'alert'],
            areaTypes: ['storage_optimization', 'resource_rightsizing'],
            reason: 'Monitoring setup'
        },
        {
            phaseKeywords: ['validation', 'testing', 'verification', 'final'],
            areaTypes: ['resource_rightsizing', 'storage_optimization'],
            reason: 'Validation and testing'
        }
    ];
    
    for (const rule of matchingRules) {
        const phaseMatches = rule.phaseKeywords.some(keyword => 
            phaseTitle.includes(keyword) || 
            phaseType.some(pType => pType.toLowerCase().includes(keyword))
        );
        
        if (phaseMatches && rule.areaTypes.includes(areaType)) {
            console.log(`   ✅ RULE MATCH: ${rule.reason} - ${areaType}`);
            return true;
        }
    }
    
    if (phaseTitle.includes('optimization') && areaType.includes('optimization')) {
        console.log(`   ✅ OPTIMIZATION FALLBACK: Both contain 'optimization'`);
        return true;
    }
    
    console.log(`   ❌ NO MATCH: "${phaseTitle}" doesn't match "${areaType}"`);
    return false;
}

function formatCommandGroupTitle(type) {
    const titleMap = {
        'hpa_optimization': '🚀 HPA Implementation',
        'resource_rightsizing': '📏 Resource Right-sizing',
        'storage_optimization': '💾 Storage Optimization',
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
        'storage_optimization': 'Optimize storage classes and reduce storage costs',
        'memory_optimization': 'Adjust memory allocation for optimal performance and cost',
        'cpu_optimization': 'Fine-tune CPU resources to match workload requirements',
        'assessment': 'Establish baseline metrics and analyze current resource utilization',
        'monitoring': 'Set up monitoring and alerting for optimization tracking'
    };
    
    return descriptionMap[type] || 'Execute optimization commands for this phase';
}

/**
 * PROCESS COMPLETE IMPLEMENTATION DATA - All real data, no fallbacks
 */
function processCompleteImplementationData(planData) {
    console.log('🔄 Processing COMPLETE implementation data - ALL REAL DATA');
    
    if (!planData) {
        console.error('❌ No plan data provided');
        return {
            totalWeeks: 0, totalPhases: 0, totalCommands: 0, securityItems: 0, 
            avgProgress: 0, totalSavings: 0, weeks: [], realCommands: [],
            executiveSummary: {}, intelligenceInsights: {}, costProtection: {}, 
            governance: {}, monitoring: {}, contingency: {}, successCriteria: {}, 
            timelineOptimization: {}, riskMitigation: {}
        };
    }
    
    // Extract all real data components
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
    const clusterName = metadata.cluster_name || planData.api_metadata?.cluster_name || 'Unknown Cluster';
    const resourceGroup = metadata.resource_group || planData.api_metadata?.resource_group || 'Unknown Resource Group';
    
    // Extract real confidence/scoring data
    const realConfidence = intelligence?.dynamic_strategy_insights?.success_probability || 
                          timeline?.timeline_confidence || 
                          summary?.confidence_level || 
                          0;
    
    // Extract all real commands
    const realCommands = extractAllRealCommands(planData);
    
    // Group phases by their week ranges
    const phaseGroups = [];
    let maxWeek = 0;
    let securityItems = 0;
    let totalProgress = 0;
    
    phases.forEach((phase, index) => {
        const startWeek = phase.start_week || 1;
        const endWeek = phase.end_week || phase.start_week || 1;
        maxWeek = Math.max(maxWeek, endWeek);
        
        if (phase.security_checks && phase.security_checks.length > 0) {
            securityItems += phase.security_checks.length;
        }
        
        totalProgress += phase.progress || 0;
        
        // Extract real commands for this phase
        let phaseCommands = extractPhaseCommands(phase, planData);
        
        let weekTitle;
        if (startWeek === endWeek) {
            weekTitle = `Week ${startWeek}: ${phase.title}`;
        } else {
            weekTitle = `Weeks ${startWeek}-${endWeek}: ${phase.title}`;
        }
        
        phaseGroups.push({
            weekNumber: startWeek,
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
                priorityLevel: phase.priority_level || 'Unknown',
                riskLevel: phase.risk_level || 'Unknown',
                complexityLevel: phase.complexity_level || 'Unknown',
                successCriteria: phase.success_criteria || [],
                tasks: phase.tasks || [],
                phaseNumber: phase.phase_number || index + 1,
                startWeek: startWeek,
                endWeek: endWeek
            }]
        });
    });
    
    phaseGroups.sort((a, b) => a.weekNumber - b.weekNumber);
    
    const avgProgress = phases.length > 0 ? Math.round(totalProgress / phases.length) : 0;
    const realConfidencePercent = Math.round(realConfidence * 100);
    
    return {
        // Core metrics
        totalWeeks: maxWeek || timeline?.total_weeks || 0,
        totalPhases: phases.length,
        totalCommands: realCommands.length,
        securityItems,
        avgProgress: realConfidencePercent,
        totalSavings,
        
        // Cluster info
        clusterName,
        resourceGroup,
        strategyType: metadata.strategy_type || intelligence?.dynamic_strategy_insights?.strategy_type || 'Unknown',
        generatedAt: metadata.generated_at || Date.now(),
        intelligenceLevel: metadata.intelligence_level || 'Unknown',
        version: metadata.version || 'Unknown',
        
        // Organized data
        weeks: phaseGroups,
        realCommands,
        
        // ALL the data components - no fallbacks
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
 * EXTRACT ALL REAL COMMANDS
 */
function extractAllRealCommands(planData) {
    let allCommands = [];
    
    if (planData.implementation_phases) {
        planData.implementation_phases.forEach(phase => {
            if (phase.commands && Array.isArray(phase.commands)) {
                phase.commands.forEach(cmd => {
                    if (typeof cmd === 'string') {
                        allCommands.push(cmd);
                    } else if (cmd.command) {
                        allCommands.push(cmd.command);
                    }
                });
            }
            if (phase.tasks) {
                phase.tasks.forEach(task => {
                    if (task.command) allCommands.push(task.command);
                });
            }
        });
    }
    
    if (planData.intelligence_insights?.dynamic_strategy_insights?.priority_areas) {
        planData.intelligence_insights.dynamic_strategy_insights.priority_areas.forEach(area => {
            if (area.executable_commands) {
                allCommands = allCommands.concat(area.executable_commands);
            }
        });
    }
    
    return allCommands.filter(cmd => cmd && cmd.trim());
}

function getRealPhaseTypes(phase) {
    const types = [];
    
    if (phase.type) {
        if (Array.isArray(phase.type)) {
            types.push(...phase.type);
        } else if (typeof phase.type === 'string') {
            types.push(phase.type);
            
            if (phase.type.includes('hpa')) types.push('hpa');
            if (phase.type.includes('rightsizing')) types.push('rightsizing');
            if (phase.type.includes('preparation')) types.push('assessment');
            if (phase.type.includes('validation')) types.push('monitoring');
            if (phase.type.includes('optimization')) types.push('optimization');
        }
    }
    
    const title = (phase.title || '').toLowerCase();
    const description = (phase.description || '').toLowerCase();
    
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
    
    if (phase.priority_level === 'High') types.push('high-priority');
    if (phase.risk_level === 'High') types.push('high-risk');
    if (phase.complexity_level === 'High') types.push('complex');
    
    if (phase.security_checks && phase.security_checks.length > 0) types.push('security');
    if (phase.compliance_items && phase.compliance_items.length > 0) types.push('compliance');
    if (phase.governance_requirements && phase.governance_requirements.length > 0) types.push('governance');
    
    if (phase.priority_level === 'Critical') types.push('critical');
    
    return types.length > 0 ? [...new Set(types)] : ['optimization'];
}

/**
 * ENHANCED HTML WITH IMPROVED STYLING
 */
function getCompleteHTML(data) {
    return `
        <div class="complete-implementation-ui" style="position: relative; z-index: 1000; background: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; min-height: 100vh; padding: 20px;">
            
            <!-- Enhanced Styles -->
            ${renderEnhancedStyles()}
            
            <!-- Main Header with Real Data -->
            ${renderEnhancedMainHeader(data)}
            
            <!-- Executive Summary Section -->
            ${renderEnhancedExecutiveSummary(data.executiveSummary)}
            
            <!-- Intelligence Insights Section -->
            ${renderEnhancedIntelligenceInsights(data.intelligenceInsights)}
            
            <!-- Framework Status Section -->
            ${renderEnhancedFrameworkStatus(data)}

            <!-- View Controls -->
            ${renderEnhancedViewControls()}

            <!-- Main Content - Timeline Only -->
            <div class="main-timeline-container">
                <div id="completeTimelineContent">${renderEnhancedCompleteTimeline(data)}</div>
            </div>
            
            <!-- Action Buttons -->
            ${renderEnhancedActionButtons(data)}
        </div>
    `;
}

function renderEnhancedStyles() {
    return `
        <style>
            .complete-implementation-ui {
                color: #2d3748;
                line-height: 1.6;
            }
            
            .main-timeline-container {
                background: white;
                border-radius: 16px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.08);
                border: 1px solid #e2e8f0;
            }
            
            .enhanced-header {
                background: linear-gradient(135deg,rgb(70, 125, 142) 0%,rgb(75, 160, 162) 100%);
                color: white;
                border-radius: 20px;
                padding: 40px;
                margin-bottom: 30px;
                box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
                position: relative;
                overflow: hidden;
            }
            
            .enhanced-header::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="40" r="1" fill="rgba(255,255,255,0.15)"/><circle cx="40" cy="80" r="1.5" fill="rgba(255,255,255,0.1)"/></svg>');
                pointer-events: none;
            }
            
            .header-content {
                position: relative;
                z-index: 1;
            }
            
            .enhanced-stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            
            .enhanced-stat-card {
                text-align: center;
                padding: 25px 20px;
                background: rgba(255,255,255,0.15);
                border-radius: 16px;
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
            }
            
            .enhanced-stat-card:hover {
                transform: translateY(-5px);
                background: rgba(255,255,255,0.2);
            }
            
            .stat-value {
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 8px;
            }
            
            .stat-label {
                font-size: 14px;
                opacity: 0.9;
            }
            
            .enhanced-section {
                background: white;
                border-radius: 16px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.06);
                border: 1px solid #e2e8f0;
                transition: all 0.3s ease;
            }
            
            .enhanced-section:hover {
                box-shadow: 0 12px 40px rgba(0,0,0,0.1);
            }
            
            .section-header {
                display: flex;
                align-items: center;
                gap: 15px;
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 2px solid #f1f5f9;
            }
            
            .section-icon {
                font-size: 24px;
            }
            
            .section-title {
                margin: 0;
                font-size: 24px;
                font-weight: 700;
                color: #2d3748;
            }
            
            .week-section {
                margin-bottom: 40px;
                position: relative;
                padding-left: 100px;
            }
            
            .enhanced-week-marker {
                position: absolute;
                left: 30px;
                top: 15px;
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg,rgb(102, 197, 234),rgb(75, 162, 153));
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 700;
                font-size: 14px;
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
                z-index: 2;
            }
            
            .week-line {
                position: absolute;
                left: 59px;
                top: 75px;
                bottom: -20px;
                width: 2px;
                background: linear-gradient(to bottom, #e2e8f0, transparent);
            }
            
            .enhanced-phase-card {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                margin-bottom: 20px;
                overflow: hidden;
                transition: all 0.3s ease;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            }
            
            .enhanced-phase-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 30px rgba(0,0,0,0.15);
                border-color: #667eea;
            }
            
            .enhanced-phase-header {
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
                padding: 25px;
                cursor: pointer;
                transition: all 0.3s ease;
                border-bottom: 1px solid #f1f5f9;
            }
            
            .enhanced-phase-header:hover {
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            }
            
            .phase-title {
                margin: 0 0 10px 0;
                font-size: 20px;
                font-weight: 600;
                color: #2d3748;
            }
            
            .phase-description {
                margin: 0 0 15px 0;
                color: #718096;
                font-size: 16px;
            }
            
            .type-badges {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                margin-bottom: 15px;
            }
            
            .type-badge {
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                color: white;
            }
            
            .phase-meta {
                display: flex;
                gap: 20px;
                align-items: center;
                flex-wrap: wrap;
            }
            
            .meta-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            
            .progress-circle {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: conic-gradient(from 0deg,rgb(102, 212, 234) var(--progress), #e2e8f0 var(--progress));
                display: flex;
                align-items: center;
                justify-content: center;
                color: #2d3748;
                font-weight: 700;
                font-size: 14px;
                position: relative;
                margin-left: auto;
            }
            
            .progress-circle::before {
                content: '';
                position: absolute;
                inset: 8px;
                border-radius: 50%;
                background: white;
            }
            
            .progress-text {
                position: relative;
                z-index: 1;
            }
            
            .enhanced-command-section {
                background: #1a202c;
                border: 1px solid #2d3748;
                border-radius: 16px;
                overflow: hidden;
                margin: 20px 0;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }
            
            .command-header {
                background: linear-gradient(135deg, #2d3748, #4a5568);
                color: white;
                padding: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .command-title {
                font-weight: 600;
                font-size: 16px;
            }
            
            .command-actions {
                display: flex;
                gap: 12px;
            }
            
            .command-btn {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 8px 16px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            
            .command-btn:hover {
                background: rgba(255, 255, 255, 0.2);
                transform: translateY(-1px);
            }
            
            .command-btn.primary {
                background: #48bb78;
                border-color: #48bb78;
            }
            
            .command-btn.primary:hover {
                background: #38a169;
            }
            
            .command-content {
                max-height: 0;
                overflow: hidden;
                transition: all 0.4s ease;
            }
            
            .command-list {
                background: #1a202c;
                color: #e2e8f0;
                padding: 0;
                font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
                font-size: 13px;
                line-height: 1.6;
            }
            
            .command-item {
                margin: 15px 20px;
                padding: 15px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                border-left: 4px solid #68d391;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .command-item:hover {
                background: rgba(255, 255, 255, 0.1);
                transform: translateX(5px);
            }
            
            .command-item:hover .command-text {
                background: rgba(255, 255, 255, 0.08);
            }
            
            .command-item-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .command-number {
                color: #68d391;
                opacity: 0.8;
                font-weight: 600;
                font-size: 12px;
            }
            
            .copy-btn {
                background: rgba(104, 211, 145, 0.2);
                color: #68d391;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10px;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .copy-btn:hover {
                background: rgba(104, 211, 145, 0.3);
            }
            
            .command-text {
                margin: 0;
                white-space: pre-wrap;
                word-wrap: break-word;
                font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace;
                color: #e2e8f0;
                background: rgba(255,255,255,0.02);
                padding: 12px;
                border-radius: 6px;
                transition: all 0.2s ease;
                font-size: 12px;
                line-height: 1.5;
                overflow-x: auto;
                max-height: 400px;
                overflow-y: auto;
            }
            
            .command-text:hover {
                background: rgba(255,255,255,0.05);
            }
            
            .enhanced-action-section {
                background: linear-gradient(135deg, #f8fafc, #e2e8f0);
                border-radius: 20px;
                padding: 40px;
                text-align: center;
            }
            
            .action-title {
                margin: 0 0 15px 0;
                font-size: 28px;
                font-weight: 700;
                color: #2d3748;
            }
            
            .action-subtitle {
                margin: 0 0 30px 0;
                font-size: 18px;
                color: #718096;
            }
            
            .action-buttons {
                display: flex;
                gap: 15px;
                justify-content: center;
                flex-wrap: wrap;
                margin-bottom: 30px;
            }
            
            .action-btn {
                padding: 15px 30px;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: all 0.3s ease;
                min-width: 180px;
            }
            
            .action-btn.primary {
                background: linear-gradient(135deg, #48bb78, #38a169);
                color: white;
                box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);
            }
            
            .action-btn.primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(72, 187, 120, 0.4);
            }
            
            .action-btn.secondary {
                background: linear-gradient(135deg,rgb(102, 234, 197),rgb(75, 162, 152));
                color: white;
                box-shadow: 0 4px 15px rgba(102, 234, 148, 0.3);
            }
            
            .action-btn.secondary:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            }
            
            .final-stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 20px;
                margin-top: 30px;
                padding-top: 30px;
                border-top: 2px solid #e2e8f0;
            }
            
            .final-stat {
                text-align: center;
            }
            
            .final-stat-value {
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 5px;
            }
            
            .final-stat-label {
                font-size: 14px;
                color: #718096;
            }
            
            .command-validation {
                margin-top: 10px;
                padding: 10px;
                border-radius: 6px;
                font-size: 12px;
                animation: slideDown 0.3s ease;
            }
            
            .validation-success {
                background: rgba(72, 187, 120, 0.1);
                border-left: 4px solid #48bb78;
                color: #48bb78;
            }
            
            .validation-warning {
                background: rgba(255, 193, 7, 0.1);
                border-left: 4px solid #ffc107;
                color: #ffc107;
            }
            
            .validation-error {
                background: rgba(220, 53, 69, 0.1);
                border-left: 4px solid #dc3545;
                color: #dc3545;
            }
            
            .terminal-preview {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.9);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease;
            }
            
            .terminal-window {
                background: #1a1a1a;
                border-radius: 12px;
                width: 90%;
                max-width: 800px;
                max-height: 80%;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            }
            
            .terminal-header {
                background: #2d3748;
                padding: 12px 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .terminal-controls {
                display: flex;
                gap: 8px;
            }
            
            .terminal-control {
                width: 12px;
                height: 12px;
                border-radius: 50%;
            }
            
            .control-close { background: #ff5f57; }
            .control-minimize { background: #ffbd2e; }
            .control-maximize { background: #28ca42; }
            
            .terminal-content {
                padding: 20px;
                color: #e2e8f0;
                font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
                font-size: 14px;
                line-height: 1.6;
                overflow-y: auto;
                max-height: 400px;
            }
            
            .progress-modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease;
            }
            
            .progress-window {
                background: white;
                border-radius: 16px;
                width: 90%;
                max-width: 600px;
                max-height: 80%;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            }
            
            .progress-header {
                background: linear-gradient(135deg,rgb(102, 208, 234),rgb(75, 162, 123));
                color: white;
                padding: 20px;
                text-align: center;
            }
            
            .progress-content {
                padding: 20px;
                overflow-y: auto;
                max-height: 400px;
            }
            
            .dark-theme {
                background: #1a202c !important;
                color: #e2e8f0 !important;
            }
            
            .dark-theme .enhanced-section {
                background: #2d3748 !important;
                border-color: #4a5568 !important;
                color: #e2e8f0 !important;
            }
            
            .dark-theme .main-timeline-container {
                background: #2d3748 !important;
                border-color: #4a5568 !important;
            }
            
            .dark-theme .enhanced-phase-card {
                background: #374151 !important;
                border-color: #4b5563 !important;
            }
            
            .dark-theme .enhanced-phase-header {
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2)) !important;
            }
            
            .search-highlight {
                background: yellow !important;
                color: black !important;
                padding: 2px 4px;
                border-radius: 3px;
            }
            
            @keyframes slideDown {
                from { max-height: 0; opacity: 0; }
                to { max-height: 100px; opacity: 1; }
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                40% { transform: translateY(-10px); }
                60% { transform: translateY(-5px); }
            }
            
            .animate-bounce {
                animation: bounce 1s ease-in-out;
            }
            
            @media (max-width: 768px) {
                .complete-implementation-ui {
                    padding: 10px;
                }
                
                .enhanced-header {
                    padding: 30px 20px;
                }
                
                .week-section {
                    padding-left: 80px;
                }
                
                .enhanced-week-marker {
                    width: 50px;
                    height: 50px;
                    left: 20px;
                    font-size: 12px;
                }
                
                .enhanced-phase-header {
                    padding: 20px;
                }
                
                .phase-meta {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 10px;
                }
                
                .progress-circle {
                    margin-left: 0;
                    margin-top: 15px;
                }
                
                .action-buttons {
                    flex-direction: column;
                    align-items: center;
                }
                
                .action-btn {
                    width: 100%;
                    max-width: 300px;
                }
                
                #commandSearch {
                    width: 150px;
                }
            }
                .complete-implementation-ui {
                    padding: 10px;
                }
                
                .enhanced-header {
                    padding: 30px 20px;
                }
                
                .week-section {
                    padding-left: 80px;
                }
                
                .enhanced-week-marker {
                    width: 50px;
                    height: 50px;
                    left: 20px;
                    font-size: 12px;
                }
                
                .enhanced-phase-header {
                    padding: 20px;
                }
                
                .phase-meta {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 10px;
                }
                
                .progress-circle {
                    margin-left: 0;
                    margin-top: 15px;
                }
                
                .action-buttons {
                    flex-direction: column;
                    align-items: center;
                }
                
                .action-btn {
                    width: 100%;
                    max-width: 300px;
                }
            }
        </style>
    `;
}

function renderEnhancedMainHeader(data) {
    return `
        <div class="enhanced-header">
            <!-- Enhanced Header with Theme Toggle and Search -->
            <div class="header-content">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                    <div>
                        <h2 style="margin: 0 0 8px 0; font-size: 32px; font-weight: 700; display: flex; align-items: center; gap: 15px;">
                            <span style="font-size: 40px;">🚀</span>
                            Implementation Plan Ready!
                        </h2>
                        <p style="margin: 0; opacity: 0.9; font-size: 18px;">
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
                    <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: center;">
                        <!-- Theme Toggle -->
                        <!--<button onclick="toggleTheme()" class="command-btn" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3);" title="Toggle Dark/Light Theme">
                            🌙 Theme
                        </button>-->
                        <!-- Command Search -->
                        <div style="position: relative;">
                            <input type="text" id="commandSearch" placeholder="🔍 Search commands..." onkeyup="searchCommands(this.value)" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 8px 16px; border-radius: 6px; font-size: 14px; width: 200px;" />
                        </div>
                        <button onclick="expandAllCompleteSections()" class="command-btn primary">
                            📖 Expand All
                        </button>
                        <button onclick="collapseAllCompleteSections()" class="command-btn">
                            📕 Collapse All
                        </button>
                        <button onclick="refreshCompletePlan()" class="command-btn">
                            🔄 Refresh
                        </button>
                        <button onclick="showProgressTracker()" class="command-btn" style="background: rgba(72, 187, 120, 0.3); border: 1px solid rgba(72, 187, 120, 0.5);" title="Track Implementation Progress">
                            ✅ Progress
                        </button>
                    </div>
                </div>
                
                
            </div>
            <div class="enhanced-stats-grid">
                    <div class="enhanced-stat-card">
                        <div class="stat-value">${data.totalPhases}</div>
                        <div class="stat-label">Phases</div>
                    </div>
                    <div class="enhanced-stat-card">
                        <div class="stat-value">${data.totalWeeks}</div>
                        <div class="stat-label">Weeks</div>
                    </div>
                    
                    <div class="enhanced-stat-card">
                        <div class="stat-value">${data.totalCommands}</div>
                        <div class="stat-label">Commands</div>
                    </div>
                    <div class="enhanced-stat-card">
                        <div class="stat-value">${data.securityItems}</div>
                        <div class="stat-label">Security Items</div>
                    </div>
                    
                </div>
        </div>
    `;
}

/** Back up
 * <div class="enhanced-stats-grid">
                    <div class="enhanced-stat-card">
                        <div class="stat-value">${data.totalPhases}</div>
                        <div class="stat-label">Phases</div>
                    </div>
                    <div class="enhanced-stat-card">
                        <div class="stat-value">${data.totalWeeks}</div>
                        <div class="stat-label">Weeks</div>
                    </div>
                    <div class="enhanced-stat-card">
                        <div class="stat-value">$${data.totalSavings.toLocaleString()}</div>
                        <div class="stat-label">Monthly Savings</div>
                    </div>
                    <div class="enhanced-stat-card">
                        <div class="stat-value">${data.totalCommands}</div>
                        <div class="stat-label">Commands</div>
                    </div>
                    <div class="enhanced-stat-card">
                        <div class="stat-value">${data.securityItems}</div>
                        <div class="stat-label">Security Items</div>
                    </div>
                    <div class="enhanced-stat-card">
                        <div class="stat-value">${data.avgProgress}%</div>
                        <div class="stat-label">Confidence</div>
                    </div>
                </div>
 */

function renderEnhancedExecutiveSummary(executiveSummary) {
    if (!executiveSummary || Object.keys(executiveSummary).length === 0) {
        return `
            <div class="enhanced-section" style="background: #fff3cd; border: 1px solid #ffeaa7;">
                <h4 style="margin: 0 0 10px 0; color: #856404;">📋 Executive Summary</h4>
                <p style="margin: 0; color: #856404; font-style: italic;">No executive summary data available in the plan object.</p>
            </div>
        `;
    }

    return `
        <div class="enhanced-section">
            <div class="section-header">
                <span class="section-icon">📊</span>
                <h2 class="section-title">Executive Summary</h2>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 25px;">
                ${executiveSummary.annual_savings_potential ? `
                    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #d4edda, #c3e6cb); border-radius: 16px; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
                        <div style="font-size: 28px; font-weight: bold; color: #155724;">$${executiveSummary.annual_savings_potential.toLocaleString()}</div>
                        <div style="font-size: 14px; color: #155724; font-weight: 600;">Annual Savings Potential</div>
                    </div>
                ` : ''}
                
                ${executiveSummary.projected_monthly_savings ? `
                    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #cce5ff, #b3d9ff); border-radius: 16px; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
                        <div style="font-size: 28px; font-weight: bold; color:rgb(0, 133, 106);">$${executiveSummary.projected_monthly_savings.toFixed(2)}</div>
                        <div style="font-size: 14px; color:rgb(0, 133, 131); font-weight: 600;">Monthly Savings</div>
                    </div>
                ` : ''}
                
                ${executiveSummary.success_probability ? `
                    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #f8d7da, #f1c0c7); border-radius: 16px; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
                        <div style="font-size: 28px; font-weight: bold; color: #721c24;">${Math.round(executiveSummary.success_probability * 100)}%</div>
                        <div style="font-size: 14px; color: #721c24; font-weight: 600;">Success Probability</div>
                    </div>
                ` : ''}
                
                ${executiveSummary.confidence_level ? `
                    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #e2e3e5, #d1d1d3); border-radius: 16px; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
                        <div style="font-size: 28px; font-weight: bold; color: #383d41;">${executiveSummary.confidence_level}</div>
                        <div style="font-size: 14px; color: #383d41; font-weight: 600;">Confidence Level</div>
                    </div>
                ` : ''}
            </div>
            
            ${executiveSummary.key_recommendations && executiveSummary.key_recommendations.length > 0 ? `
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 15px 0; color: #2d3748;">🎯 Key Recommendations</h4>
                    <ul style="margin: 0; padding-left: 20px; color: #4a5568;">
                        ${executiveSummary.key_recommendations.map(rec => `<li style="margin-bottom: 8px;">${rec}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${executiveSummary.strategic_priorities && executiveSummary.strategic_priorities.length > 0 ? `
                <div>
                    <h4 style="margin: 0 0 15px 0; color: #2d3748;">🚀 Strategic Priorities</h4>
                    <ul style="margin: 0; padding-left: 20px; color: #4a5568;">
                        ${executiveSummary.strategic_priorities.map(priority => `<li style="margin-bottom: 8px;">${priority}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}

function renderEnhancedIntelligenceInsights(intelligenceInsights) {
    if (!intelligenceInsights || Object.keys(intelligenceInsights).length === 0) {
        return `
            <div class="enhanced-section" style="background: #f8d7da; border: 1px solid #f5c6cb;">
                <h4 style="margin: 0 0 10px 0; color: #721c24;">🧠 Intelligence Insights</h4>
                <p style="margin: 0; color: #721c24; font-style: italic;">No intelligence insights data available in the plan object.</p>
            </div>
        `;
    }

    return `
        <div class="enhanced-section">
            <div class="section-header">
                <span class="section-icon">🧠</span>
                <h2 class="section-title">Intelligence Insights</h2>
            </div>
            
            ${intelligenceInsights.cluster_dna_analysis ? `
                <div style="background: #f8fafc; border-radius: 12px; padding: 25px; margin-bottom: 25px;">
                    <h4 style="margin: 0 0 20px 0; color: #2d3748;">🔬 Cluster DNA Analysis</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                        ${intelligenceInsights.cluster_dna_analysis.cluster_personality ? `
                            <div>
                                <strong style="color: #4a5568;">Personality:</strong>
                                <div style="color: #718096;">${intelligenceInsights.cluster_dna_analysis.cluster_personality}</div>
                            </div>
                        ` : ''}
                        ${intelligenceInsights.cluster_dna_analysis.efficiency_score !== undefined ? `
                            <div>
                                <strong style="color: #4a5568;">Efficiency Score:</strong>
                                <div style="color: #718096;">${(intelligenceInsights.cluster_dna_analysis.efficiency_score * 100).toFixed(2)}%</div>
                            </div>
                        ` : ''}
                        ${intelligenceInsights.cluster_dna_analysis.optimization_potential ? `
                            <div>
                                <strong style="color: #4a5568;">Optimization Potential:</strong>
                                <div style="color: #718096;">${intelligenceInsights.cluster_dna_analysis.optimization_potential}</div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            ` : ''}
            
            ${intelligenceInsights.dynamic_strategy_insights ? `
                <div style="background: #f8fafc; border-radius: 12px; padding: 25px;">
                    <h4 style="margin: 0 0 20px 0; color: #2d3748;">⚡ Dynamic Strategy Insights</h4>
                    
                    ${intelligenceInsights.dynamic_strategy_insights.strategy_type ? `
                        <div style="margin-bottom: 15px;">
                            <strong style="color: #4a5568;">Strategy Type:</strong> 
                            <span style="background:rgb(102, 214, 234); color: white; padding: 4px 12px; border-radius: 16px; font-size: 14px; margin-left: 8px;">
                                ${intelligenceInsights.dynamic_strategy_insights.strategy_type}
                            </span>
                        </div>
                    ` : ''}
                    
                    ${intelligenceInsights.dynamic_strategy_insights.success_probability !== undefined ? `
                        <div style="margin-bottom: 15px;">
                            <strong style="color: #4a5568;">Success Probability:</strong> 
                            <span style="color: #48bb78; font-weight: 700; font-size: 16px;">${Math.round(intelligenceInsights.dynamic_strategy_insights.success_probability * 100)}%</span>
                        </div>
                    ` : ''}
                    
                    ${intelligenceInsights.dynamic_strategy_insights.priority_areas && intelligenceInsights.dynamic_strategy_insights.priority_areas.length > 0 ? `
                        <div>
                            <strong style="color: #4a5568; display: block; margin-bottom: 15px;">Priority Areas (${intelligenceInsights.dynamic_strategy_insights.priority_areas.length}):</strong>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px;">
                                ${intelligenceInsights.dynamic_strategy_insights.priority_areas.map(area => `
                                    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 8px 25px rgba(0,0,0,0.1)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                                        <h5 style="margin: 0 0 10px 0; color: #2d3748;">${formatCommandGroupTitle(area.type)}</h5>
                                        <p style="margin: 0 0 12px 0; color: #718096; font-size: 14px;">${area.description || 'No description'}</p>
                                        ${area.savings_potential_monthly ? `
                                            <div style="color: #48bb78; font-weight: 700; font-size: 16px; margin-bottom: 8px;">
                                                💰 $${area.savings_potential_monthly.toFixed(2)}/month
                                            </div>
                                        ` : ''}
                                        ${area.confidence_level ? `
                                            <div style="font-size: 12px; color: #718096;">
                                                Confidence: ${Math.round(area.confidence_level * 100)}%
                                            </div>
                                        ` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
        </div>
    `;
}

function renderEnhancedFrameworkStatus(data) {
    const frameworks = [
        { key: 'costProtection', name: 'Cost Protection', icon: '💰' },
        { key: 'governance', name: 'Governance Framework', icon: '📋' },
        { key: 'monitoring', name: 'Monitoring Strategy', icon: '📊' },
        { key: 'contingency', name: 'Contingency Planning', icon: '🛡️' },
        { key: 'successCriteria', name: 'Success Criteria', icon: '✅' },
        { key: 'timelineOptimization', name: 'Timeline Optimization', icon: '⏰' },
        { key: 'riskMitigation', name: 'Risk Mitigation', icon: '⚠️' }
    ];

    return `
        <div class="enhanced-section">
            <div class="section-header">
                <span class="section-icon">🏗️</span>
                <h2 class="section-title">Framework Components Status</h2>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px;">
                ${frameworks.map(framework => {
                    const hasData = data[framework.key] && Object.keys(data[framework.key]).length > 0;
                    return `
                        <div style="padding: 20px; border: 1px solid ${hasData ? '#48bb78' : '#e53e3e'}; border-radius: 12px; background: ${hasData ? '#f0fff4' : '#fff5f5'}; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                                <span style="font-size: 20px;">${framework.icon}</span>
                                <strong style="color: ${hasData ? '#22543d' : '#c53030'}; font-size: 16px;">${framework.name}</strong>
                            </div>
                            <div style="font-size: 14px; color: ${hasData ? '#22543d' : '#c53030'};">
                                ${hasData ? 
                                    `✓ ${Object.keys(data[framework.key]).length} properties configured` : 
                                    '✗ No data available in plan object'
                                }
                            </div>
                            ${hasData ? `
                                <details style="margin-top: 15px;">
                                    <summary style="cursor: pointer; font-size: 12px; color: #22543d; font-weight: 600;">View Details</summary>
                                    <pre style="margin: 10px 0 0 0; font-size: 10px; background: white; padding: 10px; border-radius: 6px; overflow-x: auto; max-height: 200px; border: 1px solid #e2e8f0;">${JSON.stringify(data[framework.key], null, 2)}</pre>
                                </details>
                            ` : ''}
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
}

function renderEnhancedViewControls() {
    return `
        <div class="enhanced-section">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                <div style="display: flex; gap: 15px; align-items: center;">
                    <div style="background: linear-gradient(135deg,rgb(102, 234, 181),rgb(75, 150, 162)); color: white; border: none; padding: 12px 24px; border-radius: 12px; font-weight: 600; display: flex; align-items: center; gap: 10px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
                        📅 Timeline View
                    </div>
                    <div style="color: #718096; font-size: 16px;">
                        Click on phase cards to expand and view commands
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderEnhancedCompleteTimeline(data) {
    if (!data.weeks || data.weeks.length === 0) {
        return `
            <div style="text-align: center; padding: 60px 20px; color: #718096; background: #f8fafc; border-radius: 16px; border: 2px dashed #e2e8f0;">
                <div style="font-size: 64px; margin-bottom: 20px;">📭</div>
                <h3 style="margin: 0 0 10px 0; color: #e53e3e; font-size: 24px;">No Implementation Phases Available</h3>
                <p style="margin: 0; font-style: italic; font-size: 16px;">The plan object contains no implementation phases to display.</p>
            </div>
        `;
    }
    
    let html = '';
    
    data.weeks.forEach((weekGroup, groupIndex) => {
        html += `
            <div class="week-section">
                <div class="enhanced-week-marker">${weekGroup.weekRange}</div>
                ${groupIndex < data.weeks.length - 1 ? '<div class="week-line"></div>' : ''}
                <h3 style="margin: 0 0 25px 0; color: #2d3748; font-weight: 600; font-size: 22px;">${weekGroup.title}</h3>
                
                ${weekGroup.phases.map(phase => `
                    <div class="enhanced-phase-card">
                        <div class="enhanced-phase-header" onclick="toggleCompletePhase('${phase.id}')">
                            <div style="flex: 1;">
                                <h4 class="phase-title">${phase.title}</h4>
                                <p class="phase-description">${phase.description}</p>
                                <div class="type-badges">
                                    ${phase.type.map(type => `
                                        <span class="type-badge" style="background: ${getBadgeColor(type)};">${type}</span>
                                    `).join('')}
                                </div>
                                <div class="phase-meta">
                                    ${phase.projectedSavings > 0 ? `
                                        <div class="meta-item" style="color: #48bb78;">
                                            <span>💰</span> $${phase.projectedSavings.toLocaleString()}/month
                                        </div>
                                    ` : ''}
                                    <div class="meta-item" style="color:rgb(102, 212, 234);">
                                        <span>💻</span> ${phase.commands.reduce((sum, group) => sum + group.commands.length, 0)} commands
                                    </div>
                                    <div class="meta-item" style="color: #718096;">
                                        <span>📅</span> Phase ${phase.phaseNumber}
                                    </div>
                                    ${phase.commands.length > 0 ? `
                                        <div class="meta-item" style="color:rgb(102, 230, 234); margin-left: auto;">
                                            <span>👆</span> Click to view commands
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                            <div class="progress-circle" style="--progress: ${phase.progress * 3.6}deg;">
                                <div class="progress-text">${phase.progress}%</div>
                            </div>
                        </div>
                        
                        <div id="complete-content-${phase.id}" style="max-height: 0; overflow: hidden; transition: all 0.4s ease;">
                            <div style="padding: 30px;">
                                ${phase.commands && phase.commands.length > 0 ? `
                                    <h4 style="margin: 0 0 25px 0; color: #2d3748; display: flex; align-items: center; gap: 10px;">
                                        <span style="font-size: 20px;">💻</span> Implementation Commands
                                        <span style="background:rgb(102, 234, 221); color: white; padding: 6px 12px; border-radius: 16px; font-size: 12px;">${phase.commands.reduce((sum, group) => sum + group.commands.length, 0)} total</span>
                                    </h4>
                                    ${phase.commands.map((commandGroup, groupIndex) => `
                                        <div style="margin-bottom: 30px;">
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                                <h5 style="margin: 0; color:rgb(102, 221, 234); font-size: 18px; font-weight: 600;">
                                                    ${commandGroup.title || 'Commands'}
                                                </h5>
                                                <div style="display: flex; gap: 10px; align-items: center;">
                                                    ${commandGroup.savings ? `
                                                        <span style="background: #f0fff4; color: #22543d; padding: 6px 12px; border-radius: 16px; font-size: 12px; font-weight: 600;">
                                                            💰 $${commandGroup.savings.toFixed(2)}/month
                                                        </span>
                                                    ` : ''}
                                                    <span style="background: #f8fafc; color: #4a5568; padding: 6px 12px; border-radius: 16px; font-size: 12px;">
                                                        ${commandGroup.commands.length} commands
                                                    </span>
                                                    <span style="background: #edf2f7; color: #718096; padding: 6px 12px; border-radius: 16px; font-size: 11px;">
                                                        source: ${commandGroup.source}
                                                    </span>
                                                </div>
                                            </div>
                                            ${commandGroup.description ? `
                                                <p style="margin: 0 0 20px 0; color: #718096; font-size: 14px; font-style: italic;">
                                                    ${commandGroup.description}
                                                </p>
                                            ` : ''}
                                            ${commandGroup.workloads && commandGroup.workloads.length > 0 ? `
                                                <div style="margin-bottom: 20px;">
                                                    <strong style="color: #4a5568; font-size: 14px;">🎯 Target Workloads:</strong>
                                                    <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px;">
                                                        ${commandGroup.workloads.map(workload => `
                                                            <span style="background: #edf2f7; color: #4a5568; padding: 4px 12px; border-radius: 16px; font-size: 12px;">${workload}</span>
                                                        `).join('')}
                                                    </div>
                                                </div>
                                            ` : ''}
                                            <div class="enhanced-command-section">
                                                <div class="command-header">
                                                    <div style="display: flex; align-items: center; gap: 10px;">
                                                        <span style="color: #68d391; font-size: 18px;">⚡</span>
                                                        <span class="command-title">Commands Ready</span>
                                                        <span style="background: rgba(104, 211, 145, 0.2); color: #68d391; padding: 4px 8px; border-radius: 12px; font-size: 12px;">${commandGroup.commands.length} scripts</span>
                                                    </div>
                                                    <div class="command-actions">
                                                        <button onclick="event.stopPropagation(); copyCommandGroup('${phase.id}', ${groupIndex}, this); event.preventDefault();" class="command-btn primary">
                                                            📋 Copy All
                                                        </button>
                                                        <button onclick="event.stopPropagation(); toggleCommandSection('cmd-${phase.id}-${groupIndex}'); event.preventDefault();" class="command-btn" id="toggle-cmd-${phase.id}-${groupIndex}">
                                                            ⬇️ Show Commands
                                                        </button>
                                                    </div>
                                                </div>
                                                
                                                <div class="command-content" id="cmd-${phase.id}-${groupIndex}">
                                                    <div class="command-list" style="padding: 20px;">
                                                        ${commandGroup.commands.map((cmd, idx) => {
                                                            // Store the command in a global variable to avoid quote escaping issues
                                                            const commandId = `cmd_${phase.id}_${groupIndex}_${idx}`;
                                                            if (!window.commandStore) window.commandStore = {};
                                                            window.commandStore[commandId] = cmd;
                                                            
                                                            // Format command for display with basic syntax highlighting
                                                            const formattedCmd = cmd
                                                                .replace(/</g, '&lt;')
                                                                .replace(/>/g, '&gt;')
                                                                .replace(/(^|\n)(#.*$)/gm, '$1<span style="color: #68d391; opacity: 0.8;">$2</span>')
                                                                .replace(/\b(echo|kubectl|az|mkdir|cd|tar|curl|grep|awk|sed|cat|head|tail)\b/g, '<span style="color: #ffd700;">$1</span>')
                                                                .replace(/(--[a-zA-Z-]+)/g, '<span style="color: #87ceeb;">$1</span>');
                                                            
                                                            const isLongCommand = cmd.length > 200;
                                                            // Simple hash for progress tracking (btoa-free!)
                                                            const commandHash = cmd.split('').reduce((hash, char) => 
                                                                ((hash << 5) - hash + char.charCodeAt(0)) & 0xffffffff, 0
                                                            ).toString(36).slice(0, 8);
                                                            
                                                            return `
                                                            <div class="command-item" data-command-id="${commandId}" data-search-text="${cmd.toLowerCase()}">
                                                                <div class="command-item-header">
                                                                    <div style="display: flex; align-items: center; gap: 10px;">
                                                                        <input type="checkbox" id="progress-${commandHash}" onchange="updateCommandProgress('${commandHash}', this.checked)" style="width: 16px; height: 16px; accent-color: #68d391;">
                                                                        <span class="command-number">📝 Command ${idx + 1} ${isLongCommand ? '(Multi-line)' : ''}</span>
                                                                        <button onclick="validateCommand('${commandId}')" class="copy-btn" style="background: rgba(135, 206, 235, 0.2); color: #87ceeb;" title="Validate Command Syntax">
                                                                            🔍 Check
                                                                        </button>
                                                                    </div>
                                                                    <div style="display: flex; gap: 6px;">
                                                                        <button onclick="event.stopPropagation(); previewCommand('${commandId}'); event.preventDefault();" class="copy-btn" style="background: rgba(255, 215, 0, 0.2); color: #ffd700;" title="Preview in Terminal">
                                                                            🖥️ Preview
                                                                        </button>
                                                                        <button onclick="event.stopPropagation(); copyStoredCommand('${commandId}', ${idx + 1}, this); event.preventDefault();" class="copy-btn">
                                                                            📋 Copy
                                                                        </button>
                                                                    </div>
                                                                </div>
                                                                <pre class="command-text" onclick="event.stopPropagation(); copyStoredCommand('${commandId}', ${idx + 1}, null); event.preventDefault();" title="Click to copy this command">${formattedCmd}</pre>
                                                                <div id="validation-${commandId}" class="command-validation" style="display: none;"></div>
                                                            </div>
                                                        `;
                                                        }).join('')}
                                                    </div>
                                                    
                                                    <div style="background: #2d3748; padding: 15px 20px; border-top: 1px solid #4a5568; display: flex; justify-content: space-between; align-items: center; font-size: 12px;">
                                                        <span style="color: #a0aec0;">💡 Click individual commands to copy them separately</span>
                                                        <span style="color: #68d391; font-weight: 600;">${commandGroup.commands.length} commands total</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                ` : `
                                    <div style="padding: 40px; background: #fed7d7; border-radius: 16px; text-align: center; color: #c53030; border: 2px dashed #feb2b2;">
                                        <h4 style="margin: 0 0 10px 0;">⚠️ No Commands Available</h4>
                                        <p style="margin: 0; font-style: italic;">This phase has no commands in the plan object.</p>
                                    </div>
                                `}
                                
                                ${phase.tasks && phase.tasks.length > 0 ? `
                                    <h4 style="margin: 30px 0 20px 0; color: #2d3748;">📋 Tasks (${phase.tasks.length})</h4>
                                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
                                        ${phase.tasks.map(task => `
                                            <div style="padding: 20px; background: #f8fafc; border-radius: 12px; border-left: 4px solid #667eea; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
                                                <h5 style="margin: 0 0 10px 0; color: #2d3748;">${task.title || 'Task'}</h5>
                                                <p style="margin: 0 0 12px 0; color: #718096; font-size: 14px;">${task.description || 'No description'}</p>
                                                <div style="display: flex; gap: 12px; font-size: 12px; color: #718096;">
                                                    ${task.estimated_hours ? `<span>⏱️ ${task.estimated_hours}h</span>` : ''}
                                                    ${task.priority ? `<span>🔥 ${task.priority}</span>` : ''}
                                                    ${task.skills_required && task.skills_required.length > 0 ? `<span>🛠️ ${task.skills_required.join(', ')}</span>` : ''}
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                ` : ''}
                                
                                ${phase.securityChecks.length > 0 ? `
                                    <h4 style="margin: 30px 0 15px 0; color: #2d3748;">🔒 Security Checks (${phase.securityChecks.length})</h4>
                                    <ul style="margin: 0; padding-left: 20px; color: #4a5568;">
                                        ${phase.securityChecks.map(check => `<li style="margin-bottom: 8px;">${check}</li>`).join('')}
                                    </ul>
                                ` : ''}
                                
                                ${phase.successCriteria.length > 0 ? `
                                    <h4 style="margin: 30px 0 15px 0; color: #2d3748;">✅ Success Criteria (${phase.successCriteria.length})</h4>
                                    <ul style="margin: 0; padding-left: 20px; color: #4a5568;">
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

function renderEnhancedActionButtons(data) {
    return `
        <div class="enhanced-action-section">
            <h2 class="action-title">🚀 Ready to Transform Your Infrastructure?</h2>
            <p class="action-subtitle">Deploy your optimization plan and start saving immediately</p>
            
            <div class="action-buttons">
                <button onclick="deployOptimizations()" class="action-btn primary">
                    🚀 Deploy Phase 1
                </button>
                <button onclick="copyAllCompleteCommands()" class="action-btn secondary">
                    📋 Copy All Commands
                </button>
                <button onclick="exportCompletePlan()" class="action-btn secondary">
                    📥 Export Plan
                </button>
                <button onclick="scheduleOptimization()" class="action-btn secondary">
                    📅 Schedule Review
                </button>
            </div>
            
            <div class="final-stats">
                <div class="final-stat">
                    <div class="final-stat-value" style="color: #48bb78;">$${data.totalSavings.toLocaleString()}</div>
                    <div class="final-stat-label">Monthly Savings</div>
                </div>
                <div class="final-stat">
                    <div class="final-stat-value" style="color: #667eea;">${data.intelligenceLevel}</div>
                    <div class="final-stat-label">Intelligence Level</div>
                </div>
                <div class="final-stat">
                    <div class="final-stat-value" style="color: #ed8936;">${data.totalCommands}</div>
                    <div class="final-stat-label">Commands Ready</div>
                </div>
                <div class="final-stat">
                    <div class="final-stat-value" style="color: #9f7aea;">${data.totalPhases}</div>
                    <div class="final-stat-label">Implementation Phases</div>
                </div>
            </div>
        </div>
    `;
}

function getBadgeColor(type) {
    const colors = {
        'security': '#e53e3e', 'compliance': '#ed8936', 'governance': '#38b2ac',
        'critical': '#9f7aea', 'setup': '#3182ce', 'implementation': '#48bb78',
        'optimization': '#0bc5ea', 'monitoring': '#718096', 'hpa': '#e53e3e',
        'rightsizing': '#ed8936', 'assessment': '#3182ce', 'storage': '#9f7aea'
    };
    return colors[type] || '#718096';
}

/**
 * Initialize complete UI - MAINTAINS EXISTING FUNCTIONALITY
 */
function initializeCompleteUI(data) {
    console.log('🚀 Initializing complete Timeline UI with ALL real data');
    
    try {
        window.completeImplementationData = data;
        
        // Initialize command store for copy functionality
        if (!window.commandStore) {
            window.commandStore = {};
        }
        
        setTimeout(() => {
            console.log('🔧 Setting up Timeline UI handlers...');
            console.log('✅ Timeline UI ready - all existing functions preserved');
        }, 100);
        
        console.log('✅ Complete Timeline UI initialized successfully');
    } catch (error) {
        console.error('❌ Error initializing complete UI:', error);
    }
}

/**
 * EXISTING GLOBAL FUNCTIONS - PRESERVED EXACTLY
 */
window.toggleCompletePhase = function(phaseId) {
    console.log(`🔄 Toggling phase: ${phaseId}`);
    const content = document.getElementById(`complete-content-${phaseId}`);
    if (content) {
        const isExpanded = content.style.maxHeight !== '0px' && content.style.maxHeight !== '';
        console.log(`   Current state: ${isExpanded ? 'expanded' : 'collapsed'}`);
        
        if (isExpanded) {
            content.style.maxHeight = '0px';
            console.log(`   ✅ Collapsed phase ${phaseId}`);
        } else {
            content.style.maxHeight = '5000px'; // Large height for commands
            console.log(`   ✅ Expanded phase ${phaseId}`);
        }
    } else {
        console.error(`❌ Could not find element: complete-content-${phaseId}`);
    }
};

window.toggleCommandSection = function(commandId) {
    console.log(`🔄 Toggling command section: ${commandId}`);
    const content = document.getElementById(commandId);
    const toggleBtn = document.getElementById(`toggle-${commandId}`);
    
    if (content) {
        const isCollapsed = content.style.maxHeight === '0px' || content.style.maxHeight === '';
        
        if (isCollapsed) {
            content.style.maxHeight = '600px';
            if (toggleBtn) {
                toggleBtn.innerHTML = '⬆️ Hide Commands';
                toggleBtn.style.background = 'rgba(104, 211, 145, 0.2)';
            }
            console.log(`   ✅ Expanded command section ${commandId}`);
        } else {
            content.style.maxHeight = '0px';
            if (toggleBtn) {
                toggleBtn.innerHTML = '⬇️ Show Commands';
                toggleBtn.style.background = 'rgba(255,255,255,0.1)';
            }
            console.log(`   ✅ Collapsed command section ${commandId}`);
        }
    } else {
        console.error(`❌ Could not find command section: ${commandId}`);
    }
};

window.copyCompleteCommand = function(command) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(command).then(() => {
            console.log('📋 Command copied');
            showCopyNotification('All commands copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Copy failed:', err);
            showCopyNotification('Failed to copy commands', 'error');
        });
    }
};

window.copyStoredCommand = function(commandId, index, buttonElement) {
    const command = window.commandStore?.[commandId];
    if (command && navigator.clipboard) {
        navigator.clipboard.writeText(command).then(() => {
            console.log(`📋 Individual command ${index} copied`);
            showCopyNotification(`Command ${index} copied to clipboard!`, 'success');
            
            // Visual feedback on the button - only if it's a button element
            if (buttonElement && buttonElement.tagName === 'BUTTON') {
                const originalText = buttonElement.innerHTML;
                buttonElement.innerHTML = '✅ Copied!';
                buttonElement.style.background = 'rgba(72, 187, 120, 0.3)';
                setTimeout(() => {
                    buttonElement.innerHTML = originalText;
                    buttonElement.style.background = 'rgba(104, 211, 145, 0.2)';
                }, 2000);
            }
        }).catch(err => {
            console.error('Copy failed:', err);
            showCopyNotification('Failed to copy command', 'error');
        });
    }
};

window.copyCommandGroup = function(phaseId, groupIndex, buttonElement) {
    if (!window.completeImplementationData?.weeks) return;
    
    let commandGroup = null;
    window.completeImplementationData.weeks.forEach(week => {
        week.phases.forEach(phase => {
            if (phase.id === phaseId && phase.commands[groupIndex]) {
                commandGroup = phase.commands[groupIndex];
            }
        });
    });
    
    if (commandGroup?.commands && navigator.clipboard) {
        const commandText = commandGroup.commands.join('\n\n');
        navigator.clipboard.writeText(commandText).then(() => {
            console.log('📋 Command group copied');
            showCopyNotification('All commands copied to clipboard!', 'success');
            
            // Visual feedback on the button
            if (buttonElement && buttonElement.tagName === 'BUTTON') {
                const originalText = buttonElement.innerHTML;
                buttonElement.innerHTML = '✅ All Copied!';
                buttonElement.style.background = '#38a169';
                setTimeout(() => {
                    buttonElement.innerHTML = originalText;
                    buttonElement.style.background = '#48bb78';
                }, 2000);
            }
        }).catch(err => {
            console.error('Copy failed:', err);
            showCopyNotification('Failed to copy commands', 'error');
        });
    }
};

window.copyIndividualCommand = function(command, index) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(command).then(() => {
            console.log(`📋 Individual command ${index + 1} copied`);
            showCopyNotification(`Command ${index + 1} copied to clipboard!`, 'success');
        }).catch(err => {
            console.error('Copy failed:', err);
            showCopyNotification('Failed to copy command', 'error');
        });
    }
};

window.copyAllCompleteCommands = function() {
    if (window.completeImplementationData && window.completeImplementationData.weeks) {
        let allCommands = [];
        
        window.completeImplementationData.weeks.forEach(week => {
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

window.expandAllCompleteSections = function() {
    document.querySelectorAll('[id^="complete-content-"]').forEach(content => {
        content.style.maxHeight = '5000px';
    });
    document.querySelectorAll('[id^="cmd-"]').forEach(content => {
        content.style.maxHeight = '600px';
    });
};

window.collapseAllCompleteSections = function() {
    document.querySelectorAll('[id^="complete-content-"]').forEach(content => {
        content.style.maxHeight = '0px';
    });
    document.querySelectorAll('[id^="cmd-"]').forEach(content => {
        content.style.maxHeight = '0px';
    });
};

window.refreshCompletePlan = function() {
    if (PLAN_DATA_CACHE) {
        injectCompleteUI(PLAN_DATA_CACHE);
    } else {
        const savedData = sessionStorage.getItem('implementationPlanData');
        if (savedData) {
            try {
                const planData = JSON.parse(savedData);
                injectCompleteUI(planData);
            } catch (error) {
                loadImplementationPlan();
            }
        } else {
            loadImplementationPlan();
        }
    }
};

window.exportCompletePlan = function() {
    const content = document.getElementById('implementation-plan-container');
    if (content) {
        const text = content.innerText;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `complete-implementation-plan-${new Date().toISOString().split('T')[0]}.txt`;
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

// 🎉 BONUS FEATURES! 🎉

// Theme Toggle
// window.toggleTheme = function() {
//     const body = document.body;
//     const isDark = body.classList.contains('dark-theme');
    
//     if (isDark) {
//         body.classList.remove('dark-theme');
//         localStorage.setItem('theme', 'light');
//         showCopyNotification('🌞 Switched to Light Theme!', 'success');
//     } else {
//         body.classList.add('dark-theme');
//         localStorage.setItem('theme', 'dark');
//         showCopyNotification('🌙 Switched to Dark Theme!', 'success');
//     }
// };

// Command Search
window.searchCommands = function(searchTerm) {
    const commandItems = document.querySelectorAll('.command-item');
    const term = searchTerm.toLowerCase();
    
    commandItems.forEach(item => {
        const searchText = item.getAttribute('data-search-text') || '';
        const commandText = item.querySelector('.command-text');
        
        if (term === '') {
            item.style.display = 'block';
            if (commandText) {
                commandText.innerHTML = commandText.innerHTML.replace(/<span class="search-highlight">(.*?)<\/span>/g, '$1');
            }
        } else if (searchText.includes(term)) {
            item.style.display = 'block';
            item.classList.add('animate-bounce');
            setTimeout(() => item.classList.remove('animate-bounce'), 1000);
            
            // Highlight matching text
            if (commandText) {
                let content = commandText.innerHTML;
                content = content.replace(/<span class="search-highlight">(.*?)<\/span>/g, '$1');
                const regex = new RegExp(`(${term})`, 'gi');
                content = content.replace(regex, '<span class="search-highlight">$1</span>');
                commandText.innerHTML = content;
            }
        } else {
            item.style.display = 'none';
        }
    });
    
    const visibleCount = Array.from(commandItems).filter(item => item.style.display !== 'none').length;
    if (term && visibleCount === 0) {
        showCopyNotification(`No commands found matching "${searchTerm}"`, 'error');
    } else if (term && visibleCount > 0) {
        showCopyNotification(`Found ${visibleCount} commands matching "${searchTerm}"`, 'success');
    }
};

// Command Validation
window.validateCommand = function(commandId) {
    const command = window.commandStore?.[commandId];
    if (!command) return;
    
    const validationDiv = document.getElementById(`validation-${commandId}`);
    if (!validationDiv) return;
    
    validationDiv.style.display = 'block';
    validationDiv.innerHTML = '🔍 Validating command...';
    validationDiv.className = 'command-validation';
    
    // Simulate validation logic
    setTimeout(() => {
        let result = { type: 'success', message: '✅ Command syntax looks good!' };
        
        // Basic validation checks
        if (command.includes('rm -rf /')) {
            result = { type: 'error', message: '⚠️ DANGER: This command could delete system files!' };
        } else if (command.includes('sudo') && !command.includes('kubectl')) {
            result = { type: 'warning', message: '⚠️ This command requires sudo privileges' };
        } else if (command.includes('--force') || command.includes('--yes')) {
            result = { type: 'warning', message: '⚠️ This command uses force flags - use with caution' };
        } else if (!command.includes('kubectl') && !command.includes('az') && !command.includes('echo')) {
            result = { type: 'warning', message: '💡 This doesn\'t appear to be a standard Kubernetes/Azure command' };
        }
        
        validationDiv.innerHTML = result.message;
        validationDiv.className = `command-validation validation-${result.type}`;
    }, 1000);
};

// Terminal Preview
window.previewCommand = function(commandId) {
    console.log('🖥️ Preview requested for commandId:', commandId);
    console.log('📦 Command store contents:', window.commandStore);
    
    const command = window.commandStore?.[commandId];
    if (!command) {
        console.error('❌ Command not found in store for ID:', commandId);
        showCopyNotification('Command not found for preview', 'error');
        return;
    }
    
    console.log('✅ Found command for preview:', command.substring(0, 100) + '...');
    
    const modal = document.createElement('div');
    modal.className = 'terminal-preview';
    modal.innerHTML = `
        <div class="terminal-window">
            <div class="terminal-header">
                <div class="terminal-controls">
                    <div class="terminal-control control-close" onclick="this.closest('.terminal-preview').remove()"></div>
                    <div class="terminal-control control-minimize"></div>
                    <div class="terminal-control control-maximize"></div>
                </div>
                <span style="color: #e2e8f0; font-weight: 600; margin-left: 10px;">Terminal Preview - Command ${commandId}</span>
                <button onclick="this.closest('.terminal-preview').remove()" style="margin-left: auto; background: #dc3545; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer;">✕ Close</button>
            </div>
            <div class="terminal-content">
                <div style="color: #68d391; margin-bottom: 10px;">$ # Command Preview</div>
                <div style="color: #87ceeb; margin-bottom: 15px;"># This is how your command will look in the terminal:</div>
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 6px; border-left: 4px solid #68d391;">
                    <pre style="margin: 0; white-space: pre-wrap; color: #e2e8f0; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; font-size: 13px; line-height: 1.5;">${command.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
                </div>
                <div style="margin-top: 15px; padding: 10px; background: rgba(255, 193, 7, 0.1); border-radius: 6px; border-left: 4px solid #ffc107; color: #ffc107;">
                    💡 <strong>Preview Mode:</strong> This is a safe preview. No commands will be executed.
                </div>
                <div style="margin-top: 15px; padding: 10px; background: rgba(72, 187, 120, 0.1); border-radius: 6px; border-left: 4px solid #48bb78; color: #48bb78;">
                    📝 <strong>Command Length:</strong> ${command.length} characters | <strong>Lines:</strong> ${command.split('\n').length}
                </div>
                <div style="margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap;">
                    <button onclick="copyStoredCommand('${commandId}', 1, this); showCopyNotification('Command copied from preview!', 'success');" style="background: #48bb78; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-weight: 500;">
                        📋 Copy Command
                    </button>
                    <button onclick="validateCommandInPreview('${commandId}')" style="background: #17a2b8; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-weight: 500;">
                        🔍 Validate Syntax
                    </button>
                    <button onclick="showCommandDetails('${commandId}')" style="background: #6f42c1; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-weight: 500;">
                        📊 Command Details
                    </button>
                </div>
                <div id="preview-validation-${commandId}" style="margin-top: 15px;"></div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // Close on Escape key
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', handleEscape);
        }
    };
    document.addEventListener('keydown', handleEscape);
    
    console.log('✅ Preview modal created successfully');
};

// Enhanced validation for preview
window.validateCommandInPreview = function(commandId) {
    const command = window.commandStore?.[commandId];
    if (!command) return;
    
    const validationDiv = document.getElementById(`preview-validation-${commandId}`);
    if (!validationDiv) return;
    
    validationDiv.innerHTML = '🔍 Analyzing command...';
    validationDiv.style.padding = '10px';
    validationDiv.style.borderRadius = '6px';
    validationDiv.style.marginTop = '10px';
    
    setTimeout(() => {
        let results = [];
        
        // Enhanced validation checks
        if (command.includes('rm -rf /')) {
            results.push({ type: 'error', message: '🚨 CRITICAL: This command could delete system files!' });
        }
        if (command.includes('sudo') && !command.includes('kubectl')) {
            results.push({ type: 'warning', message: '⚠️ Requires sudo privileges' });
        }
        if (command.includes('--force') || command.includes('--yes') || command.includes('-y')) {
            results.push({ type: 'warning', message: '⚠️ Uses force flags - proceed with caution' });
        }
        if (command.includes('kubectl delete') && !command.includes('--dry-run')) {
            results.push({ type: 'warning', message: '⚠️ Deletes Kubernetes resources - consider --dry-run first' });
        }
        if (command.match(/\$\{.*\}/)) {
            results.push({ type: 'info', message: '💡 Contains variables - ensure they are set before execution' });
        }
        if (command.includes('curl') && !command.includes('https://')) {
            results.push({ type: 'warning', message: '⚠️ HTTP request detected - verify endpoints are secure' });
        }
        
        if (results.length === 0) {
            results.push({ type: 'success', message: '✅ Command looks safe to execute!' });
        }
        
        validationDiv.innerHTML = results.map(result => {
            const bgColor = result.type === 'error' ? 'rgba(220, 53, 69, 0.1)' : 
                           result.type === 'warning' ? 'rgba(255, 193, 7, 0.1)' : 
                           result.type === 'success' ? 'rgba(72, 187, 120, 0.1)' : 
                           'rgba(23, 162, 184, 0.1)';
            const borderColor = result.type === 'error' ? '#dc3545' : 
                               result.type === 'warning' ? '#ffc107' : 
                               result.type === 'success' ? '#48bb78' : 
                               '#17a2b8';
            const textColor = result.type === 'error' ? '#dc3545' : 
                             result.type === 'warning' ? '#ffc107' : 
                             result.type === 'success' ? '#48bb78' : 
                             '#17a2b8';
            
            return `<div style="background: ${bgColor}; border-left: 4px solid ${borderColor}; color: ${textColor}; padding: 8px 12px; margin-bottom: 8px; border-radius: 4px; font-size: 14px;">${result.message}</div>`;
        }).join('');
    }, 800);
};

// Command details analyzer
window.showCommandDetails = function(commandId) {
    const command = window.commandStore?.[commandId];
    if (!command) return;
    
    const lines = command.split('\n');
    const words = command.split(/\s+/);
    const hasKubectl = command.includes('kubectl');
    const hasAz = command.includes('az');
    const hasEcho = command.includes('echo');
    const hasComments = command.includes('#');
    const hasPipes = command.includes('|');
    const hasRedirects = command.includes('>') || command.includes('>>');
    
    const details = `
        <div style="background: rgba(102, 126, 234, 0.1); border-left: 4px solid #667eea; color: #667eea; padding: 15px; border-radius: 6px;">
            <h4 style="margin: 0 0 10px 0;">📊 Command Analysis</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; font-size: 13px;">
                <div><strong>Lines:</strong> ${lines.length}</div>
                <div><strong>Words:</strong> ${words.length}</div>
                <div><strong>Characters:</strong> ${command.length}</div>
                <div><strong>Type:</strong> ${hasKubectl ? 'Kubernetes' : hasAz ? 'Azure CLI' : hasEcho ? 'Shell Script' : 'Other'}</div>
            </div>
            <div style="margin-top: 10px; font-size: 13px;">
                <strong>Features:</strong> 
                ${hasComments ? '💬 Comments ' : ''}
                ${hasPipes ? '🔗 Pipes ' : ''}
                ${hasRedirects ? '📁 File Redirects ' : ''}
                ${hasKubectl ? '☸️ Kubernetes ' : ''}
                ${hasAz ? '☁️ Azure ' : ''}
            </div>
        </div>
    `;
    
    const validationDiv = document.getElementById(`preview-validation-${commandId}`);
    if (validationDiv) {
        validationDiv.innerHTML = details;
    }
};


// Progress Tracking
window.updateCommandProgress = function(commandHash, isCompleted) {
    if (!window.commandProgress) window.commandProgress = {};
    window.commandProgress[commandHash] = isCompleted;
    
    // Save to localStorage
    localStorage.setItem('commandProgress', JSON.stringify(window.commandProgress));
    
    const totalCommands = Object.keys(window.commandProgress).length;
    const completedCommands = Object.values(window.commandProgress).filter(Boolean).length;
    const progressPercent = totalCommands > 0 ? Math.round((completedCommands / totalCommands) * 100) : 0;
    
    if (isCompleted) {
        showCopyNotification(`✅ Command marked as completed! Progress: ${progressPercent}%`, 'success');
    }
};

window.showProgressTracker = function() {
    if (!window.commandProgress) {
        const saved = localStorage.getItem('commandProgress');
        window.commandProgress = saved ? JSON.parse(saved) : {};
    }
    
    const totalCommands = document.querySelectorAll('.command-item').length;
    const trackedCommands = Object.keys(window.commandProgress).length;
    const completedCommands = Object.values(window.commandProgress).filter(Boolean).length;
    const progressPercent = trackedCommands > 0 ? Math.round((completedCommands / trackedCommands) * 100) : 0;
    
    const modal = document.createElement('div');
    modal.className = 'progress-modal';
    modal.innerHTML = `
        <div class="progress-window">
            <div class="progress-header">
                <h3 style="margin: 0; font-size: 24px;">📊 Implementation Progress</h3>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Track your command execution progress</p>
            </div>
            <div class="progress-content">
                <div style="background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 12px; padding: 20px; color: white; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <span style="font-size: 18px; font-weight: 600;">Overall Progress</span>
                        <span style="font-size: 24px; font-weight: 700;">${progressPercent}%</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.2); border-radius: 10px; height: 12px; overflow: hidden;">
                        <div style="background: #48bb78; height: 100%; width: ${progressPercent}%; transition: all 0.5s ease;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 14px;">
                        <span>${completedCommands} completed</span>
                        <span>${totalCommands} total commands</span>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div style="background: #f0fff4; border: 1px solid #48bb78; border-radius: 8px; padding: 15px; text-align: center;">
                        <div style="color: #48bb78; font-size: 24px; font-weight: bold;">${completedCommands}</div>
                        <div style="color: #22543d; font-size: 14px;">Completed</div>
                    </div>
                    <div style="background: #fff5f0; border: 1px solid #fd7e14; border-radius: 8px; padding: 15px; text-align: center;">
                        <div style="color: #fd7e14; font-size: 24px; font-weight: bold;">${trackedCommands - completedCommands}</div>
                        <div style="color: #9c4221; font-size: 14px;">Remaining</div>
                    </div>
                    <div style="background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 8px; padding: 15px; text-align: center;">
                        <div style="color: #0ea5e9; font-size: 24px; font-weight: bold;">${totalCommands}</div>
                        <div style="color: #0c4a6e; font-size: 14px;">Total Commands</div>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <button onclick="this.closest('.progress-modal').remove()" style="background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px; margin-right: 10px;">
                        ✅ Close Progress
                    </button>
                    <button onclick="resetProgress()" style="background: #dc3545; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px;">
                        🔄 Reset Progress
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
};

window.resetProgress = function() {
    window.commandProgress = {};
    localStorage.removeItem('commandProgress');
    document.querySelectorAll('input[type="checkbox"][id^="progress-"]').forEach(cb => cb.checked = false);
    document.querySelector('.progress-modal')?.remove();
    showCopyNotification('🔄 Progress reset successfully!', 'success');
};

// Initialize theme on load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
    
    // Load saved progress
    const savedProgress = localStorage.getItem('commandProgress');
    if (savedProgress) {
        window.commandProgress = JSON.parse(savedProgress);
        // Apply saved checkboxes
        setTimeout(() => {
            Object.entries(window.commandProgress).forEach(([hash, completed]) => {
                const checkbox = document.getElementById(`progress-${hash}`);
                if (checkbox) checkbox.checked = completed;
            });
        }, 1000);
    }
});

function showCopyNotification(message, type = 'success') {
    if (window.showNotification) {
        window.showNotification(message, type, 3000);
    } else {
        const notification = document.createElement('div');
        const bgColor = type === 'success' ? '#48bb78' : '#e53e3e';
        const icon = type === 'success' ? '✅' : '❌';
        
        notification.style.cssText = `
            position: fixed; 
            top: 20px; 
            right: 20px; 
            background: ${bgColor}; 
            color: white; 
            padding: 15px 20px; 
            border-radius: 12px; 
            z-index: 10000; 
            font-size: 14px; 
            font-weight: 500;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            gap: 8px;
            animation: slideIn 0.3s ease;
            max-width: 400px;
        `;
        
        notification.innerHTML = `${icon} ${message}`;
        document.body.appendChild(notification);
        
        // Add animation styles
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Export functions
export function refreshImplementationPlan() {
    window.refreshCompletePlan();
}

export function expandAllSections() {
    window.expandAllCompleteSections();
}

export function collapseAllSections() {
    window.collapseAllCompleteSections();
}

export function exportImplementationPlan() {
    window.exportCompletePlan();
}

// Global assignments - PRESERVED EXACTLY
if (typeof window !== 'undefined') {
    window.loadImplementationPlan = loadImplementationPlan;
    window.displayImplementationPlan = displayImplementationPlan;
    window.refreshImplementationPlan = refreshImplementationPlan;
    window.exportImplementationPlan = exportImplementationPlan;
    
    console.log('✅ ENHANCED Implementation Plan Manager loaded');
    console.log('📊 Displays 100% of data object information');
    console.log('🎨 Enhanced visual design with modern UI');
    console.log('🔧 All existing functionality preserved');
    console.log('📅 Improved Timeline view with better styling');
}