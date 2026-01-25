/**
 * Implementation Plan Module
 * Handles loading and rendering implementation plans with markdown support
 */

window.ImplementationPlan = (function() {
    'use strict';
    
    // Private variables
    let currentPlan = null;
    let containerId = 'implementation-plan-container';
    
    /**
     * Initialize implementation plan module
     */
    function init() {
        console.log('Initializing Implementation Plan module...');
        // Add marked.js for markdown rendering if not available
        loadMarkedJS();
    }
    
    /**
     * Load marked.js library for markdown rendering
     */
    function loadMarkedJS() {
        if (!window.marked) {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
            script.onload = () => console.log('Marked.js library loaded');
            document.head.appendChild(script);
        }
    }
    
    /**
     * Load implementation plan for current cluster
     */
    async function loadPlan() {
        const clusterId = window.AppState?.currentClusterId;
        const container = document.getElementById(containerId);
        
        if (!container) {
            console.error('Implementation plan container not found:', containerId);
            return;
        }
        
        if (!clusterId) {
            console.warn('No cluster ID available for implementation plan');
            showErrorState('No cluster selected');
            return;
        }
        
        try {
            showLoadingState();
            const planData = await window.API.getImplementationPlan(clusterId);
            
            if (planData && planData.status === 'success') {
                currentPlan = planData;
                renderPlan(planData);
            } else {
                showErrorState(planData?.message || 'No implementation plan found');
            }
            
        } catch (error) {
            console.error('Error loading implementation plan:', error);
            showErrorState(error.message || 'Failed to load implementation plan');
        }
    }
    
    /**
     * Generate new implementation plan
     */
    async function generatePlan() {
        const clusterId = window.AppState?.currentClusterId;
        if (!clusterId) {
            console.warn('No cluster ID available for plan generation');
            return;
        }
        
        try {
            showLoadingState('Generating new implementation plan...');
            
            await window.API.generateImplementationPlan(clusterId);
            
            // Reload the plan after generation
            await loadPlan();
            
            if (window.showToast) {
                window.showToast('Implementation plan generated successfully', 'success');
            }
            
        } catch (error) {
            console.error('Error generating implementation plan:', error);
            showErrorState('Failed to generate implementation plan: ' + error.message);
            
            if (window.showToast) {
                window.showToast('Failed to generate implementation plan', 'error');
            }
        }
    }
    
    /**
     * Show loading state
     */
    function showLoadingState(message = 'Loading implementation plan...') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = `
            <div class="implementation-plan-card">
                <div class="implementation-plan-header">
                    <h3 class="implementation-plan-title">
                        <i class="fas fa-rocket implementation-plan-icon"></i> 
                        Implementation Guide
                    </h3>
                </div>
                <div class="implementation-loading">
                    <div class="loading-spinner"></div>
                    <span>${message}</span>
                </div>
            </div>
        `;
    }
    
    /**
     * Check if user can generate plans based on feature flags
     */
    function checkCanGeneratePlans() {
        let canGeneratePlans = false;
        
        // Try to get from AppState first
        if (window.AppState && window.AppState.featureFlags) {
            canGeneratePlans = window.AppState.featureFlags.showAiPlans === true;
        }
        
        // If not found, check if it's set on window directly (fallback)
        if (!canGeneratePlans && window.featureFlags) {
            canGeneratePlans = window.featureFlags.show_ai_plans === true;
        }
        
        // For ENTERPRISE, always enable if the Implementation tab is visible
        // (tab is only shown for ENTERPRISE users)
        const implementationTabVisible = document.querySelector('[data-view="implementation"]');
        if (implementationTabVisible && !canGeneratePlans) {
            // If the implementation tab exists, user must be ENTERPRISE
            canGeneratePlans = true;
        }
        return canGeneratePlans;
    }
    
    /**
     * Show error state
     */
    function showErrorState(message) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const isAnalysisRequired = message.toLowerCase().includes('no implementation plan') || 
                                 message.toLowerCase().includes('not found');
        
        container.innerHTML = `
            <div class="implementation-plan-card">
                <div class="implementation-plan-header">
                    <h3 class="implementation-plan-title">
                        <i class="fas fa-rocket implementation-plan-icon"></i> 
                        Implementation Guide
                    </h3>
                </div>
                <div class="implementation-error">
                    <div class="implementation-error-icon">
                        <i class="fas fa-${isAnalysisRequired ? 'chart-line' : 'exclamation-triangle'}"></i>
                    </div>
                    <h4 class="implementation-error-title">
                        ${isAnalysisRequired ? 'Analysis Required' : 'Unable to Load Plan'}
                    </h4>
                    <p class="implementation-error-message">
                        ${message}
                    </p>
                    <div class="implementation-error-actions">
                        ${isAnalysisRequired ? `
                            <button onclick="Dashboard.switchView('overview')" class="btn-primary">
                                <i class="fas fa-chart-line"></i> Run Analysis
                            </button>
                        ` : ''}
                        ${checkCanGeneratePlans() ? `
                            <button onclick="ImplementationPlan.generatePlan()" class="btn-secondary">
                                <i class="fas fa-plus"></i> Generate Plan
                            </button>
                        ` : `
                            <button class="btn-secondary" disabled title="ENTERPRISE license required for AI plan generation">
                                <i class="fas fa-lock"></i> Generate Plan (ENTERPRISE Only)
                            </button>
                        `}
                        <button onclick="ImplementationPlan.loadPlan()" class="btn-secondary">
                            <i class="fas fa-refresh"></i> Retry
                        </button>
                    </div>
                    ${isAnalysisRequired ? `
                        <div class="implementation-help-box">
                            <h5 class="implementation-help-title">To generate an implementation plan:</h5>
                            <ol class="implementation-help-list">
                                <li>Go to the Overview tab</li>
                                <li>Wait for cluster analysis to complete</li>
                                <li>Return to this Implementation tab</li>
                            </ol>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * Render implementation plan
     */
    function renderPlan(planData) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Container not found in renderPlan:', containerId);
            return;
        }
        
        // Get markdown content from the API response
        const markdownContent = planData.markdown_content || planData.raw_markdown;
        
        if (!markdownContent) {
            showErrorState('Implementation plan does not contain markdown content');
            return;
        }
        
        // Convert markdown to HTML
        const htmlContent = convertMarkdownToHtml(markdownContent);
        
        // Check if user can generate plans (ENTERPRISE only)
        const canGeneratePlans = checkCanGeneratePlans();
        
        // Create the appropriate button HTML
        const generateButton = canGeneratePlans ? 
            `<button onclick="ImplementationPlan.generatePlan()" 
                     class="implementation-generate-btn">
                <i class="fas fa-refresh"></i> Generate New
            </button>` :
            `<button class="implementation-generate-btn" disabled 
                     title="ENTERPRISE license required for AI plan generation">
                <i class="fas fa-lock"></i> Generate New (ENTERPRISE Only)
            </button>`;
        
        container.innerHTML = `
            <div class="implementation-plan-card">
                <div class="implementation-plan-header">
                    <h3 class="implementation-plan-title">
                        <i class="fas fa-rocket implementation-plan-icon"></i> 
                        Implementation Guide
                    </h3>
                    <div class="implementation-plan-actions">
                        <button onclick="ImplementationPlan.downloadMarkdown()" 
                                class="implementation-download-btn"
                                title="Download Markdown">
                            <i class="fas fa-download"></i>
                        </button>
                        ${generateButton}
                        <span class="implementation-timestamp">
                            ${planData.generated_at ? 'Generated: ' + formatDate(planData.generated_at) : ''}
                        </span>
                    </div>
                </div>
                <div class="implementation-content">
                    ${htmlContent}
                </div>
            </div>
        `;
        
        attachEventListeners();
    }
    
    /**
     * Convert markdown to HTML with basic markdown support
     */
    function convertMarkdownToHtml(markdown) {
        if (window.marked) {
            // Use marked.js if available
            return marked.parse(markdown);
        } else {
            // Fallback to basic markdown conversion
            return markdown
                .replace(/^### (.+)$/gm, '<h3>$1</h3>')
                .replace(/^## (.+)$/gm, '<h2>$1</h2>')
                .replace(/^# (.+)$/gm, '<h1>$1</h1>')
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.+?)\*/g, '<em>$1</em>')
                .replace(/`(.+?)`/g, '<code>$1</code>')
                .replace(/^\- (.+)$/gm, '<ul><li>$1</li></ul>')
                .replace(/^\d+\. (.+)$/gm, '<ol><li>$1</li></ol>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/^(.+)$/gm, '<p>$1</p>')
                .replace(/<\/ul>\s*<ul>/g, '')
                .replace(/<\/ol>\s*<ol>/g, '');
        }
    }
    
    /**
     * Download markdown content
     */
    function downloadMarkdown() {
        if (!currentPlan) return;
        
        const markdownContent = currentPlan.markdown_content || currentPlan.raw_markdown;
        if (!markdownContent) {
            if (window.showToast) {
                window.showToast('No markdown content available for download', 'warning');
            }
            return;
        }
        
        const filename = `implementation-plan-${currentPlan.cluster_name || 'cluster'}.md`;
        const blob = new Blob([markdownContent], { type: 'text/markdown' });
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        if (window.showToast) {
            window.showToast('Implementation plan downloaded', 'success');
        }
    }
    
    /**
     * Format date for display
     */
    function formatDate(dateString) {
        if (!dateString) return '';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (error) {
            return dateString;
        }
    }
    
    /**
     * Attach event listeners for copy functionality, etc.
     */
    function attachEventListeners() {
        // Copy code block functionality
        const codeBlocks = document.querySelectorAll('.implementation-content pre code');
        codeBlocks.forEach(codeBlock => {
            const pre = codeBlock.parentElement;
            if (pre.style.position !== 'relative') {
                pre.style.position = 'relative';
                
                const copyBtn = document.createElement('button');
                copyBtn.className = 'copy-button';
                copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                copyBtn.style.cssText = `
                    position: absolute;
                    top: 0.5rem;
                    right: 0.5rem;
                    background: var(--primary-color);
                    color: white;
                    border: none;
                    padding: 0.25rem 0.5rem;
                    border-radius: var(--radius-sm);
                    font-size: 0.75rem;
                    cursor: pointer;
                    opacity: 0.7;
                    transition: opacity 0.3s ease;
                `;
                
                copyBtn.addEventListener('click', async () => {
                    try {
                        await navigator.clipboard.writeText(codeBlock.textContent);
                        copyBtn.innerHTML = '<i class="fas fa-check"></i>';
                        copyBtn.style.background = 'var(--success-color)';
                        
                        setTimeout(() => {
                            copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                            copyBtn.style.background = 'var(--primary-color)';
                        }, 2000);
                    } catch (error) {
                        console.error('Failed to copy code:', error);
                    }
                });
                
                pre.addEventListener('mouseenter', () => copyBtn.style.opacity = '1');
                pre.addEventListener('mouseleave', () => copyBtn.style.opacity = '0.7');
                
                pre.appendChild(copyBtn);
            }
        });
    }
    
    // Public API
    return {
        init,
        loadPlan,
        generatePlan,
        downloadMarkdown
    };
})();