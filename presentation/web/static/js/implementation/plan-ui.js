/**
 * IMPLEMENTATION PLAN UI - HTML Generation and Rendering
 * Handles all UI components, templates, and visual elements
 */

import { processCompleteImplementationData, extractRealConfidence, getConfidenceLabel, getConfidenceBadgeStyle, formatCommandGroupTitle } from './plan-core.js';
import { convertToRichMarkdown, renderMarkdownData, getBadgeColor } from './plan-utils.js';

let UI_STABLE = false;

/**
 * COMPLETE UI INJECTION - All data sections, no fallbacks
 */
export function injectCompleteUI(planData) {
    
    
    const container = document.getElementById('implementation-plan-container');
    if (!container) {
        console.error('❌ Container not found during injection');
        return;
    }
    
    // Process real data first
    const processedData = processCompleteImplementationData(planData);
    
    
    // Inject complete HTML with all sections
    container.innerHTML = getCompleteHTML(processedData);
    
    // Use setTimeout pattern for stable initialization
    setTimeout(() => {
        const uiExists = !!container.querySelector('.complete-implementation-ui');
        
        
        if (uiExists) {
            initializeCompleteUI(processedData);
            UI_STABLE = true;
        } else {
            
            setTimeout(() => injectCompleteUI(planData), 200);
        }
    }, 100);
}

/**
 * ENHANCED HTML WITH IMPROVED STYLING
 * <!-- Intelligence Insights Section -->
            ${renderEnhancedIntelligenceInsights(data.intelligenceInsights)}
 */
export function getCompleteHTML(data) {
    return `
        <!-- Cluster details within implementation tab -->        
        <!-- Main Content -->
        <div class="main-timeline-container">
            <div id="completeTimelineContent">${renderEnhancedCompleteTimeline(data)}</div>
        </div>
    `;
}


// Executive Summary functionality has been integrated into the header tiles above
// This reduces duplication and provides a cleaner overview


export function renderEnhancedIntelligenceInsights(intelligenceInsights) {
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
                    <h4 style="margin: 0 0 20px 0; color: #e2e8f0;">🔬 Cluster DNA Analysis</h4>
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
                    <h4 style="margin: 0 0 20px 0; color: #e2e8f0;">⚡ Dynamic Strategy Insights</h4>
                    
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
                                        <h5 style="margin: 0 0 10px 0; color: #e2e8f0;">${formatCommandGroupTitle(area.type)}</h5>
                                        <p style="margin: 0 0 12px 0; color: #718096; font-size: 14px;">${area.description || 'No description'}</p>
                                        ${area.savings_potential_monthly ? `
                                            <div style="color: #48bb78; font-weight: 700; font-size: 16px; margin-bottom: 8px;">
                                                💰 ${area.savings_potential_monthly.toFixed(2)}/month
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

// export function renderEnhancedFrameworkStatus(data) {
//     return `
//         <div class="enhanced-section">
//             <div class="section-header">
//                 <span class="section-icon">🏗️</span>
//                 <h2 class="section-title">AKS Optimization Framework</h2>
//                 <p style="margin: 5px 0 0 0; color: #718096; font-size: 16px;">AI-powered recommendations for your Azure Kubernetes Service cluster optimization</p>
//             </div>
            
//             <!-- Framework Tabs -->
//             <div class="framework-tabs-container">
//                 <div class="framework-tabs">
//                     <button class="framework-tab active" onclick="switchFrameworkTab('overview', this)" data-tab="overview">
//                         <span class="tab-icon">📊</span> Overview
//                     </button>
//                     <button class="framework-tab" onclick="switchFrameworkTab('cost-protection', this)" data-tab="cost-protection">
//                         <span class="tab-icon">💰</span> Cost Protection
//                     </button>
//                     <button class="framework-tab" onclick="switchFrameworkTab('governance', this)" data-tab="governance">
//                         <span class="tab-icon">⚖️</span> Governance
//                     </button>
//                     <button class="framework-tab" onclick="switchFrameworkTab('monitoring', this)" data-tab="monitoring">
//                         <span class="tab-icon">📈</span> Monitoring
//                     </button>
//                 </div>
                
//                 <!-- Tab Content -->
//                 <div class="framework-tab-content">
//                     <!-- Overview Tab -->
//                     <div id="framework-tab-overview" class="tab-panel active">
//                         ${renderOverviewTab(data)}
//                     </div>
                    
//                     <!-- Cost Protection Tab -->
//                     <div id="framework-tab-cost-protection" class="tab-panel">
//                         ${renderCostProtectionTab(data.costProtection)}
//                     </div>
                    
//                     <!-- Governance Tab -->
//                     <div id="framework-tab-governance" class="tab-panel">
//                         ${renderGovernanceTab(data.governance)}
//                     </div>
                    
//                     <!-- Monitoring Tab -->
//                     <div id="framework-tab-monitoring" class="tab-panel">
//                         ${renderMonitoringTab(data.monitoring)}
//                     </div>
//                 </div>
//             </div>
//         </div>
        
//         <!-- Tabbed Interface Styles -->
//         <style>
//             .framework-tabs-container {
//                 background: white;
//                 border-radius: 16px;
//                 box-shadow: 0 8px 32px rgba(0,0,0,0.08);
//                 overflow: hidden;
//                 border: 1px solid #e2e8f0;
//             }
            
//             .framework-tabs {
//                 display: flex;
//                 background: #f8fafc;
//                 border-bottom: 1px solid #e2e8f0;
//                 overflow-x: auto;
//                 padding: 0;
//             }
            
//             .framework-tab {
//                 background: none;
//                 border: none;
//                 padding: 20px 24px;
//                 cursor: pointer;
//                 font-size: 14px;
//                 font-weight: 600;
//                 color: #718096;
//                 white-space: nowrap;
//                 transition: all 0.3s ease;
//                 border-bottom: 3px solid transparent;
//                 display: flex;
//                 align-items: center;
//                 gap: 8px;
//                 min-width: fit-content;
//             }
            
//             .framework-tab:hover {
//                 color: #4a5568;
//                 background: rgba(102, 126, 234, 0.05);
//             }
            
//             .framework-tab.active {
//                 color: #667eea;
//                 background: white;
//                 border-bottom-color: #667eea;
//                 box-shadow: 0 -2px 8px rgba(102, 126, 234, 0.1);
//             }
            
//             .tab-icon {
//                 font-size: 16px;
//             }
            
//             .framework-tab-content {
//                 background: white;
//             }
            
//             .tab-panel {
//                 display: none;
//                 padding: 40px;
//                 min-height: 300px;
//                 animation: fadeIn 0.3s ease;
//             }
            
//             .tab-panel.active {
//                 display: block;
//             }
//         </style>
//     `;
// }

function renderOverviewTab(data) {
    const frameworks = [
        { key: 'costProtection', name: 'Cost Protection', icon: '💰', tabId: 'cost-protection' },
        { key: 'governance', name: 'Governance', icon: '⚖️', tabId: 'governance' },
        { key: 'monitoring', name: 'Monitoring', icon: '📈', tabId: 'monitoring' }
    ];
    
    const configuredCount = frameworks.filter(f => data[f.key] && Object.keys(data[f.key]).length > 0).length;
    const totalCount = frameworks.length;
    const completionPercentage = Math.round((configuredCount / totalCount) * 100);
    
    return `
        <div style="text-align: center; margin-bottom: 30px;">
            <h3 style="color: #e2e8f0; margin-bottom: 10px;">Framework Overview</h3>
            <div style="font-size: 48px; margin-bottom: 20px;">${completionPercentage}%</div>
            <div style="color: #718096;">${configuredCount}/${totalCount} components configured</div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
            ${frameworks.map(framework => {
                const hasData = data[framework.key] && Object.keys(data[framework.key]).length > 0;
                const confidence = extractRealConfidence(data[framework.key]);
                
                return `
                    <div style="background: #f8fafc; border-radius: 12px; padding: 20px; text-align: center; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
                        <div style="font-size: 32px; margin-bottom: 10px;">${framework.icon}</div>
                        <h4 style="margin: 0 0 10px 0; color: #e2e8f0;">${framework.name}</h4>
                        <div style="color: ${hasData ? '#48bb78' : '#e53e3e'}; font-weight: 600; margin-bottom: 10px;">
                            ${hasData ? '✓ Configured' : '✗ Not Available'}
                        </div>
                        <div style="color: #718096; font-size: 14px;">${confidence}% confidence</div>
                        <button onclick="switchFrameworkTabById('${framework.tabId}')" 
                                style="margin-top: 15px; background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 12px;">
                            View Details →
                        </button>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderCostProtectionTab(data) {
    const hasData = data && Object.keys(data).length > 0;
    const confidence = extractRealConfidence(data);
    const confidenceLabel = getConfidenceLabel(confidence);
    
    return `
        <div style="text-align: center; margin-bottom: 30px;">
            <h3 style="color: #e2e8f0;">Cost Protection</h3>
            <div style="color: #48bb78; font-size: 18px; font-weight: 600;">${confidenceLabel} (${confidence}%)</div>
        </div>
        
        <p style="color: #718096; margin-bottom: 30px;">
            ${hasData ? 
                'Budget limits and cost monitoring safeguards are configured.' :
                'Set up budget limits and automated cost controls to protect against unexpected Azure spending.'
            }
        </p>
        
        ${hasData ? renderMarkdownData(convertToRichMarkdown(data, 'Cost Protection Configuration'), 'Cost Protection Details') : ''}
    `;
}

function renderGovernanceTab(data) {
    const hasData = data && Object.keys(data).length > 0;
    const confidence = extractRealConfidence(data);
    const confidenceLabel = getConfidenceLabel(confidence);
    
    return `
        <div style="text-align: center; margin-bottom: 30px;">
            <h3 style="color: #e2e8f0;">Governance</h3>
            <div style="color: #48bb78; font-size: 18px; font-weight: 600;">${confidenceLabel} (${confidence}%)</div>
        </div>
        
        <p style="color: #718096; margin-bottom: 30px;">
            Approval processes and compliance requirements for AKS changes
        </p>
        
        ${hasData ? renderMarkdownData(convertToRichMarkdown(data, 'Governance Configuration'), 'Governance Details') : ''}
    `;
}

function renderMonitoringTab(data) {
    const hasData = data && Object.keys(data).length > 0;
    const confidence = extractRealConfidence(data);
    const confidenceLabel = getConfidenceLabel(confidence);
    
    return `
        <div style="text-align: center; margin-bottom: 30px;">
            <h3 style="color: #e2e8f0;">Monitoring</h3>
            <div style="color: #48bb78; font-size: 18px; font-weight: 600;">${confidenceLabel} (${confidence}%)</div>
        </div>
        
        <p style="color: #718096; margin-bottom: 30px;">
            ${hasData ? 
                'Monitoring strategy configured with comprehensive coverage.' :
                'Set up comprehensive monitoring to track your AKS cluster performance and costs in real-time.'
            }
        </p>
        
        ${hasData ? renderMarkdownData(convertToRichMarkdown(data, 'Monitoring Configuration'), 'Monitoring Setup Details') : ''}
    `;
}

// export function renderEnhancedViewControls() {
//     return `
//         <div class="enhanced-section">
//             <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
//                 <div style="display: flex; gap: 15px; align-items: center;">
//                     <div style="background: linear-gradient(135deg,rgb(102, 234, 181),rgb(75, 150, 162)); color: white; border: none; padding: 12px 24px; border-radius: 12px; font-weight: 600; display: flex; align-items: center; gap: 10px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
//                         📅 Timeline View
//                     </div>
//                     <div style="color: #718096; font-size: 16px;">
//                         Click on phase cards to expand and view commands
//                     </div>
//                 </div>
//             </div>
//         </div>
//     `;
// }

export function renderEnhancedCompleteTimeline(data) {
    if (!data.weeks || data.weeks.length === 0) {
        return `
            <div style="text-align: center; padding: 3.75rem 1.25rem; color: var(--text-secondary); background: var(--bg-card); border-radius: 16px; border: 2px dashed var(--border-light);">
                <div style="font-size: 4rem; margin-bottom: 1.25rem;">📭</div>
                <h3 style="margin: 0 0 0.625rem 0; color: var(--text-primary); font-size: 1.5rem;">No Implementation Commands Available</h3>
                <p style="margin: 0; font-style: italic; font-size: 1rem; color: var(--text-secondary);">The analysis found no optimization commands to display.</p>
            </div>
        `;
    }

    // Collect all commands by category for single-window display
    const commandsByCategory = {};
    let totalCommands = 0;
    let totalSavings = 0;
    let actualPhaseCount = 0;

    data.weeks.forEach(weekGroup => {
        weekGroup.phases.forEach(phase => {
            actualPhaseCount++; // Count actual phases with commands
            totalSavings += phase.projectedSavings || 0;
            phase.commands.forEach(commandGroup => {
                const category = commandGroup.title || commandGroup.category || 'General Commands';
                if (!commandsByCategory[category]) {
                    commandsByCategory[category] = {
                        commands: [],
                        description: commandGroup.description || '',
                        totalCount: 0,
                        phaseCount: 0
                    };
                }
                commandsByCategory[category].commands.push(...commandGroup.commands);
                commandsByCategory[category].totalCount += commandGroup.commands.length;
                commandsByCategory[category].phaseCount++;
                totalCommands += commandGroup.commands.length;
            });
        });
    });
    

    if (totalCommands === 0) {
        return `
            <div style="text-align: center; padding: 3.75rem 1.25rem; color: var(--text-secondary); background: var(--bg-card); border-radius: 16px; border: 2px dashed var(--border-light);">
                <div style="font-size: 4rem; margin-bottom: 1.25rem;">🔧</div>
                <h3 style="margin: 0 0 0.625rem 0; color: var(--text-primary); font-size: 1.5rem;">No Commands Found</h3>
                <p style="margin: 0; font-style: italic; font-size: 1rem; color: var(--text-secondary);">Implementation plan contains no executable commands.</p>
            </div>
        `;
    }
    
    // Generate clean flat implementation steps
    let stepCounter = 0;
    let html = `
        <div class="single-window-container" style="counter-reset: step-counter;">
            
            ${Object.entries(commandsByCategory).map(([category, categoryData]) => {
                stepCounter++;
                return `
                    <div class="implementation-step">
                        <div class="step-header">
                            <h3 class="step-title">${category}</h3>
                            ${categoryData.description ? `<p class="step-description">${categoryData.description}</p>` : ''}
                        </div>
                        
                        <ol class="command-list">
                            ${categoryData.commands.map((cmd, idx) => {
                                const commandId = `cmd_${category.replace(/[^a-zA-Z0-9]/g, '_')}_${idx}`;
                                if (!window.commandStore) window.commandStore = {};
                                
                                // Handle both ExecutableCommand objects and strings
                                let commandText, commandObj;
                                if (typeof cmd === 'object' && cmd !== null) {
                                    commandText = cmd.command || cmd.description || JSON.stringify(cmd);
                                    commandObj = cmd;
                                    window.commandStore[commandId] = cmd.command || cmd.description || JSON.stringify(cmd);
                                } else if (typeof cmd === 'string') {
                                    commandText = cmd;
                                    commandObj = { command: cmd, rollback_commands: [], validation_commands: [] };
                                    window.commandStore[commandId] = commandText;
                                } else {
                                    commandText = String(cmd);
                                    commandObj = { command: commandText, rollback_commands: [], validation_commands: [] };
                                    window.commandStore[commandId] = commandText;
                                }
                                
                                return `
                                    <li class="command-step">
                                        <p class="command-description">Run the following command:</p>
                                        <div class="command-block">
                                            <pre class="command-pre"><code>${commandText}</code></pre>
                                            <button onclick="copyStoredCommand('${commandId}', ${idx + 1}, this)" class="copy-button">Copy</button>
                                        </div>
                                        ${commandObj.validation_commands && commandObj.validation_commands.length > 0 ? `
                                            <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary); font-size: 0.875rem;">
                                                Verify with: <code style="background: #e8f5e8; padding: 0.125rem 0.25rem; border-radius: 3px; font-size: 0.8rem;">${commandObj.validation_commands[0]}</code>
                                            </p>
                                        ` : ''}
                                    </li>
                                `;
                            }).join('')}
                        </ol>
                    </div>
                `;
            }).join('')}
        </div>
    `;
    
    return html;
}

// export function renderEnhancedActionButtons(data) {
//     return `
//         <div class="enhanced-action-section">
//             <h2 class="action-title">🚀 Ready to Transform Your Infrastructure?</h2>
//             <p class="action-subtitle">Deploy your optimization plan and start saving immediately</p>
            
//             <div class="action-buttons">
//                 <button onclick="deployOptimizations()" class="action-btn primary">
//                     🚀 Deploy Phase 1
//                 </button>
//                 <button onclick="copyAllCompleteCommands()" class="action-btn secondary">
//                     📋 Copy All Commands
//                 </button>
//                 <button onclick="exportCompletePlan()" class="action-btn secondary">
//                     📥 Export Plan
//                 </button>
//                 <button onclick="scheduleOptimization()" class="action-btn secondary">
//                     📅 Schedule Review
//                 </button>
//             </div>
            
//             <div class="final-stats">
//                 <div class="final-stat">
//                     <div class="final-stat-value" style="color: #48bb78;">${data.totalSavings.toLocaleString()}</div>
//                     <div class="final-stat-label">Monthly Savings</div>
//                 </div>
//                 <div class="final-stat">
//                     <div class="final-stat-value" style="color: #667eea;">${data.intelligenceLevel}</div>
//                     <div class="final-stat-label">Intelligence Level</div>
//                 </div>
//                 <div class="final-stat">
//                     <div class="final-stat-value" style="color: #ed8936;">${data.totalCommands}</div>
//                     <div class="final-stat-label">Commands Ready</div>
//                 </div>
//                 <div class="final-stat">
//                     <div class="final-stat-value" style="color: #9f7aea;">${data.totalPhases}</div>
//                     <div class="final-stat-label">Implementation Phases</div>
//                 </div>
//             </div>
//         </div>
//     `;
// }

/**
 * Initialize complete UI - MAINTAINS EXISTING FUNCTIONALITY
 */
export function initializeCompleteUI(data) {
    console.log('🚀 Initializing complete Timeline UI with ALL real data');
    
    try {
        window.completeImplementationData = data;
        
        // Initialize command store for copy functionality
        if (!window.commandStore) {
            window.commandStore = {};
        }
        
        setTimeout(() => {
            console.log('🔧 Setting up Timeline UI handlers...');
        }, 100);
        
        console.log('✅ Complete Timeline UI initialized successfully');
    } catch (error) {
        console.error('❌ Error initializing complete UI:', error);
    }
}

// Global copy functionality for clean flat design
window.copyStoredCommand = function(commandId, commandNumber, button) {
    const command = window.commandStore ? window.commandStore[commandId] : null;
    if (command) {
        navigator.clipboard.writeText(command).then(() => {
            if (button) {
                const originalText = button.innerHTML;
                button.innerHTML = 'Copied!';
                button.style.backgroundColor = '#2b6e63';
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.style.backgroundColor = '';
                }, 1500);
            }
            console.log(`✅ Command ${commandNumber} copied to clipboard`);
        }).catch(err => {
            console.error('❌ Failed to copy command:', err);
        });
    }
};