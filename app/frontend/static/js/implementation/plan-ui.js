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
 * ENHANCED HTML WITH IMPROVED STYLING
 */
export function getCompleteHTML(data) {
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
            
        
           

            <!-- Main Content - Timeline Only -->
            <div class="main-timeline-container">
                <div id="completeTimelineContent">${renderEnhancedCompleteTimeline(data)}</div>
            </div>
            
            <!-- Action Buttons -->
            ${renderEnhancedActionButtons(data)}
        </div>
    `;
}

export function renderEnhancedStyles() {
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
                background: linear-gradient(135deg, #429f9a 0%, #2b6e63 100%) !important
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
        </style>
    `;
}

export function renderEnhancedMainHeader(data) {
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

export function renderEnhancedExecutiveSummary(executiveSummary) {
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
            <h3 style="color: #2d3748; margin-bottom: 10px;">Framework Overview</h3>
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
                        <h4 style="margin: 0 0 10px 0; color: #2d3748;">${framework.name}</h4>
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
            <h3 style="color: #2d3748;">Cost Protection</h3>
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
            <h3 style="color: #2d3748;">Governance</h3>
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
            <h3 style="color: #2d3748;">Monitoring</h3>
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
                                            <span>💰</span> ${phase.projectedSavings.toLocaleString()}/month
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
                            <!--<div class="progress-circle" style="--progress: ${phase.progress * 3.6}deg;">
                                <div class="progress-text">${phase.progress}%</div>
                            </div>-->
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
                                                    <span style="background: #f8fafc; color: #4a5568; padding: 6px 12px; border-radius: 16px; font-size: 12px;">
                                                        ${commandGroup.commands.length} commands
                                                    </span>
                                                </div>
                                            </div>
                                            ${commandGroup.description ? `
                                                <p style="margin: 0 0 20px 0; color: #718096; font-size: 14px; font-style: italic;">
                                                    ${commandGroup.description}
                                                </p>
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
                                                            
                                                            return `
                                                            <div class="command-item" data-command-id="${commandId}" data-search-text="${cmd.toLowerCase()}">
                                                                <div class="command-item-header">
                                                                    <div style="display: flex; align-items: center; gap: 10px;">
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
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    });
    
    return html;
}

export function renderEnhancedActionButtons(data) {
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
                    <div class="final-stat-value" style="color: #48bb78;">${data.totalSavings.toLocaleString()}</div>
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
            console.log('✅ Timeline UI ready - all existing functions preserved');
        }, 100);
        
        console.log('✅ Complete Timeline UI initialized successfully');
    } catch (error) {
        console.error('❌ Error initializing complete UI:', error);
    }
}