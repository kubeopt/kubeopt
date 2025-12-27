/**
 * Implementation Plan Renderer - Markdown Display Mode
 * Developer: Srinivas Kondepudi
 * Organization: Nivaya Technologies & kubeopt
 * Project: AKS Cost Optimizer
 */

// Add marked.js for markdown rendering
if (!window.marked) {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
    document.head.appendChild(script);
}

class ImplementationPlanRenderer {
    constructor(containerId = 'implementation-content') {
        this.containerId = containerId;
        this.container = null;
        this.currentPlan = null;
        this.clusterInfo = null;
        
        this.validateConstructorParameters();
        this.initializeContainer();
    }

    validateConstructorParameters() {
        if (!this.containerId || typeof this.containerId !== 'string') {
            throw new Error('Container ID must be a valid non-empty string');
        }
    }

    initializeContainer() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            throw new Error(`Implementation plan container with ID '${this.containerId}' not found`);
        }
    }

    validateClusterInfo() {
        if (!window.clusterInfo) {
            throw new Error('Cluster information not available in window.clusterInfo');
        }
        
        const requiredFields = ['id', 'name', 'resource_group'];
        const missingFields = requiredFields.filter(field => !window.clusterInfo[field]);
        
        if (missingFields.length > 0) {
            throw new Error(`Missing required cluster information: ${missingFields.join(', ')}`);
        }
        
        this.clusterInfo = window.clusterInfo;
    }

    async loadImplementationPlan() {
        try {
            this.validateClusterInfo();
            this.showLoadingState();
            
            const planData = await this.fetchImplementationPlan();
            this.validatePlanData(planData);
            
            // For markdown format, use the data directly
            if (planData.plan_type === 'markdown') {
                this.currentPlan = planData;
            } else {
                // Legacy format with nested plan
                this.currentPlan = planData.plan;
            }
            this.renderImplementationPlan();
            
        } catch (error) {
            console.error('Failed to load implementation plan:', error);
            this.showErrorState(error.message);
            throw error;
        }
    }

    async fetchImplementationPlan() {
        const apiUrl = `/api/clusters/${encodeURIComponent(this.clusterInfo.id)}/plan`;
        
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            
            if (data.status !== 'success') {
                throw new Error(data.message || 'API returned error status');
            }

            return data;
        }

        // If plan doesn't exist (404), show helpful error
        if (response.status === 404) {
            throw new Error('No implementation plan found for this cluster. Please run a cluster analysis first to generate an implementation plan.');
        } else if (response.status >= 500) {
            throw new Error('Server error while fetching implementation plan. Please try again later.');
        } else {
            throw new Error(`Failed to fetch implementation plan: ${response.status} ${response.statusText}`);
        }
    }


    validatePlanData(data) {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid plan data received from API');
        }

        // For markdown format, check for markdown_content directly
        if (data.plan_type === 'markdown') {
            if (!data.markdown_content) {
                throw new Error('Markdown implementation plan data is missing markdown_content');
            }
            return; // Valid markdown plan
        }

        // Legacy plan format validation (if needed)
        if (!data.plan || typeof data.plan !== 'object') {
            throw new Error('Implementation plan data is missing or invalid');
        }

        // The plan structure can vary - be flexible about what's required
        const plan = data.plan.implementation_plan || data.plan;
        
        // Only validate that we have some kind of plan structure
        if (!plan || typeof plan !== 'object') {
            throw new Error('No valid implementation plan structure found');
        }
        
        // Log the plan structure for debugging
        console.log('Implementation plan structure:', Object.keys(plan));
    }

    showLoadingState(isGenerating = false) {
        const title = isGenerating ? 'Generating Implementation Plan' : 'Loading Implementation Plan';
        const description = isGenerating ? 
            'Creating your personalized optimization plan using AI analysis...' : 
            'Fetching your personalized optimization plan...';
        
        this.container.innerHTML = `
            <div class="clean-chart-card chart-card-full-width-mb">
                <div class="chart-header">
                    <div class="chart-header-left">
                        <div class="chart-icon">
                            <i class="fas fa-rocket"></i>
                        </div>
                        <h2 class="chart-title">Implementation Guide</h2>
                    </div>
                    <div class="chart-header-right">
                        <span class="last-analyzed-time">${isGenerating ? 'Generating...' : 'Loading...'}</span>
                    </div>
                </div>
                <div class="implementation-container">
                    <div class="loading-spinner" style="margin: 2rem auto; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #7ba573; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                    <h4 class="implementation-title">${title}</h4>
                    <p class="implementation-text">${description}</p>
                    ${isGenerating ? '<p class="implementation-text" style="margin-top: 0.5rem; font-size: 0.875rem; color: #6b7280;">This may take a few moments while we analyze your cluster and create customized optimization steps.</p>' : ''}
                </div>
            </div>
        `;
    }

    showErrorState(message) {
        const isAnalysisRequired = message.toLowerCase().includes('analysis') || message.toLowerCase().includes('run an analysis') || message.toLowerCase().includes('run a cluster analysis');
        
        this.container.innerHTML = `
            <div class="clean-chart-card chart-card-full-width-mb">
                <div class="chart-header">
                    <div class="chart-header-left">
                        <div class="chart-icon">
                            <i class="fas fa-rocket"></i>
                        </div>
                        <h2 class="chart-title">Implementation Guide</h2>
                    </div>
                    <div class="chart-header-right">
                        <span class="last-analyzed-time">Error</span>
                    </div>
                </div>
                <div class="implementation-container" style="text-align: center; padding: 2rem;">
                    <div style="color: #dc2626; font-size: 3rem; margin-bottom: 1rem;">
                        <i class="fas fa-${isAnalysisRequired ? 'chart-line' : 'exclamation-triangle'}"></i>
                    </div>
                    <h4 class="implementation-title" style="color: #dc2626;">${isAnalysisRequired ? 'Analysis Required' : 'Unable to Load Implementation Plan'}</h4>
                    <p class="implementation-text" style="color: #6b7280; margin-bottom: 1.5rem;">${this.escapeHtml(message)}</p>
                    <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                        ${isAnalysisRequired ? `
                            <button onclick="window.location.reload()" class="clean-btn clean-btn-primary">
                                <i class="fas fa-chart-line"></i> Go to Overview Tab
                            </button>
                        ` : ''}
                        <button onclick="implementationRenderer.loadImplementationPlan()" class="clean-btn ${isAnalysisRequired ? 'clean-btn-secondary' : 'clean-btn-primary'}">
                            <i class="fas fa-redo"></i> Retry
                        </button>
                    </div>
                    ${isAnalysisRequired ? `
                        <div style="margin-top: 1.5rem; padding: 1rem; background-color: #f3f4f6; border-radius: 6px; text-align: left;">
                            <h5 style="margin: 0 0 0.5rem 0; color: #374151;">To generate an implementation plan:</h5>
                            <ol style="margin: 0; padding-left: 1.5rem; color: #6b7280; font-size: 0.875rem;">
                                <li>Go to the Overview tab</li>
                                <li>Click the "Analyze" button to run cluster analysis</li>
                                <li>Return to this Implementation tab once analysis completes</li>
                            </ol>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    renderImplementationPlan() {
        const plan = this.currentPlan.implementation_plan || this.currentPlan;
        
        // Require markdown content
        const markdownContent = this.currentPlan.markdown_content || this.currentPlan.raw_markdown;
        if (!markdownContent) {
            throw new Error('Implementation plan must contain markdown_content or raw_markdown field. No fallback rendering allowed.');
        }
        
        this.renderMarkdownPlan(markdownContent, plan);
        this.attachEventListeners();
    }

    renderMarkdownPlan(markdownContent, plan) {
        this.container.innerHTML = `
            <div class="clean-chart-card chart-card-full-width-mb">
                <div class="chart-header">
                    <div class="chart-header-left">
                        <div class="chart-icon">
                            <i class="fas fa-rocket"></i>
                        </div>
                        <h2 class="chart-title">Implementation Guide</h2>
                    </div>
                    <div class="chart-header-right">
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <button onclick="implementationRenderer.downloadMarkdown()" class="clean-btn clean-btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">
                                <i class="fas fa-download"></i> Download MD
                            </button>
                            <span class="last-analyzed-time">Last analyzed: ${this.formatDate(plan.metadata?.generated_date)}</span>
                        </div>
                    </div>
                </div>
                
                <div class="markdown-content markdown-body" style="padding: 1.5rem; max-width: none;">
                    ${this.convertMarkdownToHtml(markdownContent)}
                </div>
            </div>
        `;
    }













    attachEventListeners() {
        // Phase toggle functionality
        window.togglePhase = (index) => {
            const content = document.getElementById(`phase-content-${index}`);
            const icon = content.parentElement.querySelector('.phase-toggle-icon');
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.style.transform = 'rotate(180deg)';
            } else {
                content.style.display = 'none';
                icon.style.transform = 'rotate(0deg)';
            }
        };

        // Copy to clipboard functionality
        window.copyToClipboard = async (text, button) => {
            try {
                await navigator.clipboard.writeText(text);
                
                const originalHTML = button.innerHTML;
                button.innerHTML = '<i class="fas fa-check"></i> Copied!';
                button.style.backgroundColor = '#16a34a';
                
                setTimeout(() => {
                    button.innerHTML = originalHTML;
                    button.style.backgroundColor = '#7ba573';
                }, 2000);
                
            } catch (error) {
                console.error('Failed to copy text to clipboard:', error);
                
                const originalHTML = button.innerHTML;
                button.innerHTML = '<i class="fas fa-times"></i> Failed';
                button.style.backgroundColor = '#dc2626';
                
                setTimeout(() => {
                    button.innerHTML = originalHTML;
                    button.style.backgroundColor = '#7ba573';
                }, 2000);
            }
        };
    }

    // Utility methods
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, (m) => map[m]);
    }

    convertMarkdownToHtml(markdown) {
        if (!markdown || typeof markdown !== 'string') {
            return '<p>No implementation plan content available.</p>';
        }

        // Use marked.js for proper markdown rendering
        if (window.marked) {
            try {
                // Configure marked.js for better code highlighting
                marked.setOptions({
                    highlight: function(code, language) {
                        // Basic syntax highlighting for bash/shell commands
                        if (language === 'bash' || language === 'shell') {
                            return code
                                .replace(/(kubectl|az|helm|docker)/g, '<span class="cmd-keyword">$1</span>')
                                .replace(/(get|apply|patch|scale|delete|create)/g, '<span class="cmd-verb">$1</span>')
                                .replace(/--[\w-]+/g, '<span class="cmd-flag">$&</span>');
                        }
                        return code;
                    },
                    breaks: true,
                    gfm: true
                });
                
                const html = marked.parse(markdown);
                return html;
            } catch (error) {
                console.error('Markdown parsing error:', error);
                return `<pre class="markdown-raw">${markdown}</pre>`;
            }
        }
        
        // Fallback if marked.js not loaded
        return `<pre class="markdown-raw">${markdown}</pre>`;
    }

    downloadMarkdown() {
        if (!this.currentPlan.markdown_content) {
            console.error('No markdown content available for download');
            return;
        }

        const blob = new Blob([this.currentPlan.markdown_content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `implementation-plan-${this.clusterInfo?.name || 'cluster'}-${new Date().toISOString().split('T')[0]}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }


    escapeForJs(text) {
        if (text === null || text === undefined) return '';
        return String(text).replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n').replace(/\r/g, '\\r');
    }

    formatDate(dateString) {
        if (!dateString) return '--';
        try {
            return new Date(dateString).toLocaleDateString();
        } catch (error) {
            return '--';
        }
    }

    formatNumber(num) {
        if (num === null || num === undefined || isNaN(num)) return '0';
        return new Intl.NumberFormat().format(num);
    }





}

// Global implementation renderer instance
window.implementationRenderer = null;

// Initialize implementation plan loading function
function loadImplementationPlan() {
    try {
        if (!window.implementationRenderer) {
            window.implementationRenderer = new ImplementationPlanRenderer('implementation-content');
        }
        
        window.implementationRenderer.loadImplementationPlan();
        
    } catch (error) {
        console.error('Failed to initialize implementation plan renderer:', error);
        
        const container = document.getElementById('implementation-content');
        if (container) {
            container.innerHTML = `
                <div class="clean-chart-card chart-card-full-width-mb">
                    <div class="chart-header">
                        <div class="chart-header-left">
                            <div class="chart-icon">
                                <i class="fas fa-rocket"></i>
                            </div>
                            <h2 class="chart-title">Implementation Guide</h2>
                        </div>
                        <div class="chart-header-right">
                            <span class="last-analyzed-time">Error</span>
                        </div>
                    </div>
                    <div class="implementation-container" style="text-align: center; padding: 2rem;">
                        <div style="color: #dc2626; font-size: 3rem; margin-bottom: 1rem;">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <h4 class="implementation-title" style="color: #dc2626;">Initialization Error</h4>
                        <p class="implementation-text" style="color: #6b7280;">${error.message}</p>
                    </div>
                </div>
            `;
        }
    }
}

// Global functions for markdown rendering
window.copyCodeBlock = function(codeId, button) {
    const codeElement = document.getElementById(codeId);
    if (!codeElement) return;
    
    const text = codeElement.textContent;
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i> Copied!';
        button.style.backgroundColor = '#22c55e';
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.backgroundColor = '#7ba573';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy code:', err);
        button.innerHTML = '<i class="fas fa-times"></i> Error';
        button.style.backgroundColor = '#ef4444';
        
        setTimeout(() => {
            button.innerHTML = '<i class="fas fa-copy"></i> Copy';
            button.style.backgroundColor = '#7ba573';
        }, 2000);
    });
};

// CSS styles for implementation plan
const implementationStyles = `
<style>
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Simple GitHub-like Markdown Styles */
.markdown-content {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #24292f;
    max-width: none;
}

.md-spacer {
    height: 8px;
}

.md-h1 {
    font-size: 2em;
    font-weight: 600;
    color: #24292f;
    margin: 16px 0 8px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #d1d9e0;
}

.md-h2 {
    font-size: 1.5em;
    font-weight: 600;
    color: #24292f;
    margin: 16px 0 8px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #d1d9e0;
}

.md-h3 {
    font-size: 1.25em;
    font-weight: 600;
    color: #24292f;
    margin: 12px 0 6px 0;
}

.md-h4 {
    font-size: 1em;
    font-weight: 600;
    color: #24292f;
    margin: 12px 0 6px 0;
}

.md-h5 {
    font-size: 0.875em;
    font-weight: 600;
    color: #24292f;
    margin: 10px 0 5px 0;
}

.md-hr {
    border: none;
    height: 1px;
    background-color: #e5e7eb;
    margin: 2rem 0;
}

.md-p {
    margin: 0 0 10px 0;
    line-height: 1.6;
    color: #24292f;
}

.md-p.command-step {
    margin: 8px 0;
    padding: 6px 0;
    color: #0969da;
    border-left: 3px solid #0969da;
    padding-left: 12px;
    background-color: rgba(9, 105, 218, 0.05);
}

.md-strong {
    font-weight: 600;
}

.md-em {
    font-style: italic;
}

.md-ul, .md-ol {
    margin: 0 0 10px 0;
    padding-left: 2em;
}

.md-ul {
    list-style-type: disc;
}

.md-ol {
    list-style-type: decimal;
}

.md-li, .md-li-ordered {
    margin: 2px 0;
    line-height: 1.6;
    color: #24292f;
}

.code-block-container {
    margin: 8px 0;
    border: 1px solid #d1d9e0;
    border-radius: 6px;
    overflow: hidden;
    background: #f6f8fa;
}

.code-block-header {
    background: #f6f8fa;
    border-bottom: 1px solid #d1d9e0;
    padding: 8px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: #656d76;
}

.code-block-language {
    font-weight: 600;
    text-transform: lowercase;
}

.code-copy-btn {
    background: none;
    border: 1px solid #d1d9e0;
    color: #24292f;
    padding: 4px 8px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    transition: background-color 0.2s;
}

.code-copy-btn:hover {
    background: #f3f4f6;
}

.code-block {
    background: #f6f8fa;
    padding: 16px;
    margin: 0;
    overflow-x: auto;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 14px;
    line-height: 1.45;
}

.code-block code {
    background: none;
    color: #24292f;
    white-space: pre;
}

.inline-code {
    background: rgba(175, 184, 193, 0.2);
    color: #24292f;
    padding: 0.2em 0.4em;
    border-radius: 6px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 85%;
}

.metric-item {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 6px;
}

.metric-label {
    font-size: 0.875rem;
    color: #6b7280;
    font-weight: 500;
}

.metric-value {
    font-size: 1.5rem;
    font-weight: 700;
}

.metric-progress-bar {
    height: 6px;
    background-color: #e5e7eb;
    border-radius: 3px;
    overflow: hidden;
}

.metric-progress {
    height: 100%;
    transition: width 0.3s ease;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}

.quality-check-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid #e5e7eb;
}

.quality-check-item:last-child {
    border-bottom: none;
}

.quality-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.quality-badge-good {
    background-color: #d1fae5;
    color: #065f46;
}

.quality-badge-warning {
    background-color: #fef3c7;
    color: #92400e;
}

.quality-badge-error {
    background-color: #fee2e2;
    color: #991b1b;
}

.badge-success {
    background-color: #d1fae5;
    color: #065f46;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}

.badge-warning {
    background-color: #fef3c7;
    color: #92400e;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}

.summary-item {
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 6px;
}

.summary-label {
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 0.25rem;
}

.summary-value {
    font-size: 1.25rem;
    font-weight: 600;
    color: #374151;
}

.naming-table td {
    padding: 0.75rem;
    border: 1px solid #e5e7eb;
    font-size: 0.875rem;
}

.command-block {
    position: relative;
}

.command-block code {
    display: block;
    padding-right: 4rem;
}

.copy-btn:hover {
    opacity: 0.8;
}

.phase-header:hover {
    background-color: #f3f4f6 !important;
}
</style>
`;

// Inject CSS styles
if (!document.getElementById('implementation-plan-styles')) {
    document.head.insertAdjacentHTML('beforeend', implementationStyles.replace('<style>', '<style id="implementation-plan-styles">'));
}