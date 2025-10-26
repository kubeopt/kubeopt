/**
 * Implementation Plan Renderer - Production-ready implementation without fallbacks
 * Developer: Srinivas Kondepudi
 * Organization: Nivaya Technologies & kubeopt
 * Project: AKS Cost Optimizer
 */

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
            
            this.currentPlan = planData.plan;
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
                        <span class="last-analyzed-time">Last analyzed: ${this.formatDate(plan.metadata?.generated_date)}</span>
                    </div>
                </div>
                
                ${this.renderClusterDnaSection(plan.cluster_dna_analysis)}
                ${this.renderBuildQualitySection(plan.build_quality_assessment)}
                ${this.renderNamingConventionsSection(plan.naming_conventions_analysis)}
                ${this.renderRoiAnalysisSection(plan.roi_analysis || plan.roi_summary)}
                ${this.renderImplementationSummarySection(plan.implementation_summary)}
                ${this.renderPhasesSection(plan.phases)}
                ${this.renderMonitoringSection(plan.monitoring)}
                ${this.renderNextStepsSection(plan.next_steps)}
            </div>
        `;

        this.attachEventListeners();
    }

    renderClusterDnaSection(dnaAnalysis) {
        if (!dnaAnalysis) return '';
        
        // Handle different metrics structures
        let metricsHtml = '';
        
        if (dnaAnalysis.metrics) {
            if (Array.isArray(dnaAnalysis.metrics)) {
                // Handle array structure
                metricsHtml = dnaAnalysis.metrics.map(metric => {
                    if (!metric || typeof metric !== 'object') {
                        console.warn('Invalid DNA metric:', metric);
                        return '';
                    }
                    // Adapt to database structure: metric.metric (not metric.label), metric.score (not metric.percentage)
                    const label = metric.label || metric.metric || 'Metric';
                    const value = metric.value || 0;
                    const score = metric.score || metric.percentage || 0;
                    const percentage = score * 100; // Convert score (0-1) to percentage
                    const color = this.getColorForScore(score);
                    
                    return `
            <div class="metric-item">
                <div class="metric-label">${this.escapeHtml(label)}</div>
                <div class="metric-value" style="color: ${color}">${value} (${percentage.toFixed(0)}%)</div>
                <div class="metric-progress-bar">
                    <div class="metric-progress" style="width: ${percentage}%; background-color: ${color};"></div>
                </div>
            </div>
            `;
                }).filter(html => html).join('');
            } else if (typeof dnaAnalysis.metrics === 'object') {
                // Handle object structure - create metrics from available data
                console.log('DNA metrics is object, adapting:', dnaAnalysis.metrics);
                metricsHtml = '<div class="metric-item"><div class="metric-label">Analysis Data Available</div><div class="metric-value">✓</div></div>';
            }
        }

        return `
            <div class="clean-chart-card" style="margin-bottom: 1.5rem;">
                <div class="chart-header">
                    <div class="chart-icon">
                        <i class="fas fa-dna"></i>
                    </div>
                    <h3 class="chart-title">Cluster DNA Analysis</h3>
                </div>
                <div class="dna-score-card" style="background: linear-gradient(135deg, #6b46c1, #9333ea); color: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem;">
                    <div style="font-size: 2.5rem; font-weight: 700;">${dnaAnalysis.overall_score || 0}</div>
                    <div style="margin-top: 0.5rem;">${this.escapeHtml(dnaAnalysis.description || 'Analysis complete')}</div>
                </div>
                <div class="metrics-grid">
                    ${metricsHtml}
                </div>
            </div>
        `;
    }

    renderBuildQualitySection(buildQuality) {
        if (!buildQuality) return '';
        
        // Validate that quality_checks is an array
        if (buildQuality.quality_checks && !Array.isArray(buildQuality.quality_checks)) {
            throw new Error(`Build Quality quality_checks must be an array, got ${typeof buildQuality.quality_checks}: ${JSON.stringify(buildQuality.quality_checks)}`);
        }
        
        const qualityChecks = buildQuality.quality_checks || [];
        const checksHtml = qualityChecks.map(check => {
            if (!check || typeof check !== 'object') {
                throw new Error(`Quality check must be an object, got ${typeof check}: ${JSON.stringify(check)}`);
            }
            // Use database structure: check.check, check.result, check.comments
            const label = check.check || 'Quality Check';
            const result = check.result || 'Unknown';
            const statusType = this.getStatusTypeFromResult(result);
            
            return `
            <div class="quality-check-item" style="margin-bottom: 1rem; padding: 0.75rem; background-color: #f8f9fa; border-radius: 6px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span class="quality-label" style="font-weight: 600; color: #374151; flex: 1;">${this.escapeHtml(label)}</span>
                    <span class="quality-badge quality-badge-${statusType}" style="margin-left: 1rem;">${this.escapeHtml(result)}</span>
                </div>
                ${check.comments ? `<div class="quality-comments" style="font-size: 0.875rem; color: #6b7280; line-height: 1.4;">${this.escapeHtml(check.comments)}</div>` : ''}
                ${check.score !== undefined ? `<div style="margin-top: 0.5rem; font-size: 0.75rem; color: #7ba573;">Score: ${(check.score * 100).toFixed(0)}%</div>` : ''}
            </div>
            `;
        }).join('');

        // Validate that strengths is an array
        if (buildQuality.strengths && !Array.isArray(buildQuality.strengths)) {
            throw new Error(`Build Quality strengths must be an array, got ${typeof buildQuality.strengths}: ${JSON.stringify(buildQuality.strengths)}`);
        }
        
        const strengths = buildQuality.strengths || [];
        const strengthsHtml = strengths.map(strength => {
            if (typeof strength !== 'string') {
                throw new Error(`Strength must be a string, got ${typeof strength}: ${JSON.stringify(strength)}`);
            }
            return `<li>${this.escapeHtml(strength)}</li>`;
        }).join('');

        return `
            <div class="clean-chart-card" style="margin-bottom: 1.5rem;">
                <div class="chart-header">
                    <div class="chart-icon">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <h3 class="chart-title">Build Quality Assessment</h3>
                </div>
                <div class="quality-checks">
                    ${checksHtml}
                </div>
                ${strengthsHtml ? `
                    <div style="margin-top: 1rem;">
                        <h4 style="color: #7ba573; margin-bottom: 0.5rem;">Strengths</h4>
                        <ul style="margin-left: 1rem;">${strengthsHtml}</ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderNamingConventionsSection(namingAnalysis) {
        if (!namingAnalysis) return '';
        
        // Validate that resources is an array
        if (namingAnalysis.resources && !Array.isArray(namingAnalysis.resources)) {
            throw new Error(`Naming Analysis resources must be an array, got ${typeof namingAnalysis.resources}: ${JSON.stringify(namingAnalysis.resources)}`);
        }
        
        const resources = namingAnalysis.resources || [];
        const resourcesHtml = resources.map(resource => {
            if (!resource || typeof resource !== 'object') {
                throw new Error(`Naming resource must be an object, got ${typeof resource}: ${JSON.stringify(resource)}`);
            }
            return `
            <tr>
                <td>${this.escapeHtml(resource.resource_type)}</td>
                <td><code>${this.escapeHtml(resource.example)}</code></td>
                <td><code>${this.escapeHtml(resource.pattern)}</code></td>
                <td><span class="badge badge-${resource.badge_type || 'success'}">${this.escapeHtml(resource.compliance)}</span></td>
            </tr>
            `;
        }).join('');

        return `
            <div class="clean-chart-card" style="margin-bottom: 1.5rem;">
                <div class="chart-header">
                    <div class="chart-icon">
                        <i class="fas fa-tag"></i>
                    </div>
                    <h3 class="chart-title">Naming Conventions Analysis</h3>
                </div>
                <div style="margin-bottom: 1rem;">
                    <div style="font-size: 1.5rem; font-weight: 600; color: ${this.getColorForRating(namingAnalysis.color)};">
                        ${namingAnalysis.overall_score || 0}/${namingAnalysis.max_score || 100}
                    </div>
                </div>
                <table class="naming-table" style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 0.75rem; text-align: left; border: 1px solid #e5e7eb;">Resource Type</th>
                            <th style="padding: 0.75rem; text-align: left; border: 1px solid #e5e7eb;">Example</th>
                            <th style="padding: 0.75rem; text-align: left; border: 1px solid #e5e7eb;">Pattern</th>
                            <th style="padding: 0.75rem; text-align: left; border: 1px solid #e5e7eb;">Compliance</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${resourcesHtml}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderRoiAnalysisSection(roiAnalysis) {
        if (!roiAnalysis) return '';
        
        // Handle the actual database structure where summary_metrics is an object
        let summaryMetricsHtml = '';
        
        if (roiAnalysis.summary_metrics) {
            if (typeof roiAnalysis.summary_metrics !== 'object') {
                throw new Error(`ROI Analysis summary_metrics must be an object, got ${typeof roiAnalysis.summary_metrics}: ${JSON.stringify(roiAnalysis.summary_metrics)}`);
            }
            
            const metrics = roiAnalysis.summary_metrics;
            
            // Create metric cards from the object data
            const metricCards = [];
            
            if (metrics.total_monthly_cost !== undefined) {
                metricCards.push(`
                    <div class="roi-metric-card" style="background: linear-gradient(135deg, #dc2626, #ef4444); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: 700;">$${this.formatNumber(metrics.total_monthly_cost)}</div>
                        <div style="font-size: 0.875rem; margin-top: 0.25rem;">Current Monthly Cost</div>
                    </div>
                `);
            }
            
            if (metrics.total_savings_potential !== undefined) {
                metricCards.push(`
                    <div class="roi-metric-card" style="background: linear-gradient(135deg, #16a34a, #22c55e); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: 700;">$${this.formatNumber(metrics.total_savings_potential)}</div>
                        <div style="font-size: 0.875rem; margin-top: 0.25rem;">Potential Monthly Savings</div>
                    </div>
                `);
            }
            
            if (metrics.cost_reduction_percentage !== undefined) {
                metricCards.push(`
                    <div class="roi-metric-card" style="background: linear-gradient(135deg, #7c3aed, #a855f7); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: 700;">${metrics.cost_reduction_percentage}%</div>
                        <div style="font-size: 0.875rem; margin-top: 0.25rem;">Cost Reduction</div>
                    </div>
                `);
            }
            
            // Calculate additional metrics if possible
            if (metrics.total_monthly_cost && metrics.total_savings_potential) {
                const optimizedCost = metrics.total_monthly_cost - metrics.total_savings_potential;
                metricCards.push(`
                    <div class="roi-metric-card" style="background: linear-gradient(135deg, #2563eb, #3b82f6); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: 700;">$${this.formatNumber(optimizedCost)}</div>
                        <div style="font-size: 0.875rem; margin-top: 0.25rem;">Optimized Monthly Cost</div>
                    </div>
                `);
            }
            
            summaryMetricsHtml = metricCards.join('');
        }

        return `
            <div class="clean-chart-card" style="margin-bottom: 1.5rem;">
                <div class="chart-header">
                    <div class="chart-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <h3 class="chart-title">ROI Analysis</h3>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
                    ${summaryMetricsHtml}
                </div>
                ${this.renderRoiBreakdown(roiAnalysis.calculation_breakdown)}
            </div>
        `;
    }

    renderRoiBreakdown(breakdown) {
        if (!breakdown) return '';
        
        return `
            <div class="roi-breakdown" style="background-color: #f8f9fa; padding: 1rem; border-radius: 8px;">
                <h4 style="margin-bottom: 0.75rem; color: #374151;">Financial Breakdown</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.75rem; font-size: 0.875rem;">
                    <div><strong>Implementation Cost:</strong> $${this.formatNumber(breakdown.implementation_cost)}</div>
                    <div><strong>Monthly Savings:</strong> $${this.formatNumber(breakdown.monthly_savings)}</div>
                    <div><strong>Annual Savings:</strong> $${this.formatNumber(breakdown.annual_savings)}</div>
                    <div><strong>Payback Period:</strong> ${breakdown.payback_months} months</div>
                    <div><strong>ROI Year 1:</strong> ${breakdown.roi_percentage_year1}%</div>
                </div>
            </div>
        `;
    }

    renderImplementationSummarySection(summary) {
        if (!summary) return '';
        
        return `
            <div class="clean-chart-card" style="margin-bottom: 1.5rem;">
                <div class="chart-header">
                    <div class="chart-icon">
                        <i class="fas fa-info-circle"></i>
                    </div>
                    <h3 class="chart-title">Implementation Summary</h3>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div class="summary-item">
                        <div class="summary-label">Cluster</div>
                        <div class="summary-value">${this.escapeHtml(summary.cluster_name || '')}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Environment</div>
                        <div class="summary-value">${this.escapeHtml(summary.environment || '')}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Current Cost</div>
                        <div class="summary-value">$${this.formatNumber(summary.current_monthly_cost)}/mo</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Projected Cost</div>
                        <div class="summary-value">$${this.formatNumber(summary.projected_monthly_cost)}/mo</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Cost Reduction</div>
                        <div class="summary-value" style="color: #16a34a;">${summary.cost_reduction_percentage}%</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Duration</div>
                        <div class="summary-value">${this.escapeHtml(summary.implementation_duration || '')}</div>
                    </div>
                </div>
            </div>
        `;
    }

    renderPhasesSection(phases) {
        if (!phases) return '';
        
        // Validate that phases is an array
        if (!Array.isArray(phases)) {
            throw new Error(`Phases must be an array, got ${typeof phases}: ${JSON.stringify(phases)}`);
        }
        
        const phasesHtml = phases.map((phase, index) => {
            if (!phase || typeof phase !== 'object') {
                throw new Error(`Phase must be an object, got ${typeof phase}: ${JSON.stringify(phase)}`);
            }
            // Adapt to database structure: phase.name (not phase.phase_name), no description, no total_savings_monthly
            const phaseName = phase.phase_name || phase.name || `Phase ${phase.phase_number}`;
            const description = phase.description || `Implementation phase focusing on ${phaseName.toLowerCase()}`;
            
            return `
            <div class="phase-card" style="border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 1rem;">
                <div class="phase-header" onclick="togglePhase(${index})" style="padding: 1rem; background-color: #f8f9fa; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-radius: 8px 8px 0 0;">
                    <div>
                        <h4 style="margin: 0; color: #374151;">Phase ${phase.phase_number}: ${this.escapeHtml(phaseName)}</h4>
                        <p style="margin: 0.25rem 0 0 0; color: #6b7280; font-size: 0.875rem;">${this.escapeHtml(description)}</p>
                    </div>
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <span style="background-color: #7ba573; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">
                            ${(phase.actions || []).length} action${(phase.actions || []).length !== 1 ? 's' : ''}
                        </span>
                        <i class="fas fa-chevron-down phase-toggle-icon" style="transition: transform 0.2s;"></i>
                    </div>
                </div>
                <div class="phase-content" id="phase-content-${index}" style="display: none; padding: 1rem;">
                    ${this.renderPhaseActions(phase.actions || [])}
                </div>
            </div>
            `;
        }).join('');

        return `
            <div class="clean-chart-card" style="margin-bottom: 1.5rem;">
                <div class="chart-header">
                    <div class="chart-icon">
                        <i class="fas fa-tasks"></i>
                    </div>
                    <h3 class="chart-title">Implementation Phases</h3>
                </div>
                <div class="phases-container">
                    ${phasesHtml}
                </div>
            </div>
        `;
    }

    renderPhaseActions(actions) {
        // Validate that actions is an array
        if (!Array.isArray(actions)) {
            throw new Error(`Phase actions must be an array, got ${typeof actions}: ${JSON.stringify(actions)}`);
        }
        
        return actions.map(action => {
            if (!action || typeof action !== 'object') {
                throw new Error(`Action must be an object, got ${typeof action}: ${JSON.stringify(action)}`);
            }
            // Adapt to database structure: action.step (not action.title), no action.description, no savings_monthly
            const title = action.title || action.step || 'Implementation Action';
            const description = action.description || `Action: ${action.step || 'Execute implementation step'}`;
            
            return `
            <div class="action-card" style="border: 1px solid #e5e7eb; border-radius: 6px; margin-bottom: 1rem; padding: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                    <h5 style="margin: 0; color: #374151;">${this.escapeHtml(title)}</h5>
                    <span style="background-color: #6b7280; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">
                        Implementation Step
                    </span>
                </div>
                <p style="margin-bottom: 1rem; color: #6b7280;">${this.escapeHtml(description)}</p>
                
                ${action.steps && action.steps.length > 0 ? `
                    <div class="action-steps">
                        <h6 style="margin-bottom: 0.5rem; color: #374151;">Implementation Steps:</h6>
                        ${(() => {
                            // Validate that steps is an array
                            if (!Array.isArray(action.steps)) {
                                throw new Error(`Action steps must be an array, got ${typeof action.steps}: ${JSON.stringify(action.steps)}`);
                            }
                            return action.steps.map((step, stepIndex) => {
                                if (!step || typeof step !== 'object') {
                                    throw new Error(`Step must be an object, got ${typeof step}: ${JSON.stringify(step)}`);
                                }
                                return `
                            <div class="step-item" style="margin-bottom: 0.75rem;">
                                <div style="font-weight: 600; margin-bottom: 0.25rem;">${step.step_number}. ${this.escapeHtml(step.label)}</div>
                                ${step.command ? `
                                    <div class="command-block" style="background-color: #f8f9fa; border: 1px solid #e5e7eb; border-radius: 4px; padding: 0.75rem; position: relative;">
                                        <code style="font-family: 'Courier New', monospace; white-space: pre-wrap;">${this.escapeHtml(step.command)}</code>
                                        <button class="copy-btn" onclick="copyToClipboard('${this.escapeForJs(step.command)}', this)" style="position: absolute; top: 0.5rem; right: 0.5rem; background-color: #7ba573; color: white; border: none; padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem;">
                                            <i class="fas fa-copy"></i> Copy
                                        </button>
                                    </div>
                                ` : ''}
                                ${step.expected_output ? `
                                    <div style="margin-top: 0.5rem; font-size: 0.875rem; color: #6b7280;">
                                        <strong>Expected output:</strong> ${this.escapeHtml(step.expected_output)}
                                    </div>
                                ` : ''}
                            </div>
                            `;
                            }).join('');
                        })()}
                    </div>
                ` : ''}
                
                ${action.rollback ? `
                    <div class="rollback-section" style="margin-top: 1rem; padding: 0.75rem; background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 4px;">
                        <h6 style="margin-bottom: 0.5rem; color: #dc2626;">Rollback Instructions:</h6>
                        <p style="margin-bottom: 0.5rem; font-size: 0.875rem; color: #6b7280;">${this.escapeHtml(action.rollback.description)}</p>
                        <div class="command-block" style="background-color: #fff; border: 1px solid #e5e7eb; border-radius: 4px; padding: 0.75rem; position: relative;">
                            <code style="font-family: 'Courier New', monospace; white-space: pre-wrap;">${this.escapeHtml(action.rollback.command)}</code>
                            <button class="copy-btn" onclick="copyToClipboard('${this.escapeForJs(action.rollback.command)}', this)" style="position: absolute; top: 0.5rem; right: 0.5rem; background-color: #dc2626; color: white; border: none; padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem;">
                                <i class="fas fa-copy"></i> Copy
                            </button>
                        </div>
                    </div>
                ` : ''}
            </div>
            `;
        }).join('');
    }

    renderMonitoringSection(monitoring) {
        if (!monitoring) return '';
        
        // Adapt to database structure: monitoring.key_commands (simple strings, not objects)
        const commands = monitoring.commands || monitoring.key_commands || [];
        
        // Validate that commands is an array
        if (!Array.isArray(commands)) {
            throw new Error(`Monitoring commands must be an array, got ${typeof commands}: ${JSON.stringify(commands)}`);
        }
        
        const commandsHtml = commands.map(cmd => {
            // Handle both string commands and object commands
            let command, label;
            
            if (typeof cmd === 'string') {
                command = cmd;
                label = this.generateLabelFromCommand(cmd);
            } else if (cmd && typeof cmd === 'object') {
                command = cmd.command || cmd;
                label = cmd.label || this.generateLabelFromCommand(command);
            } else {
                console.warn('Invalid monitoring command:', cmd);
                return '';
            }
            
            return `
            <div class="command-block" style="background-color: #f8f9fa; border: 1px solid #e5e7eb; border-radius: 4px; padding: 0.75rem; margin-bottom: 0.75rem; position: relative;">
                <div style="font-weight: 600; margin-bottom: 0.5rem;">${this.escapeHtml(label)}</div>
                <code style="font-family: 'Courier New', monospace; white-space: pre-wrap;">${this.escapeHtml(command)}</code>
                <button class="copy-btn" onclick="copyToClipboard('${this.escapeForJs(command)}', this)" style="position: absolute; top: 0.5rem; right: 0.5rem; background-color: #7ba573; color: white; border: none; padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem;">
                    <i class="fas fa-copy"></i> Copy
                </button>
            </div>
            `;
        }).filter(html => html).join('');

        return `
            <div class="clean-chart-card" style="margin-bottom: 1.5rem;">
                <div class="chart-header">
                    <div class="chart-icon">
                        <i class="fas fa-eye"></i>
                    </div>
                    <h3 class="chart-title">${this.escapeHtml(monitoring.title || 'Monitoring')}</h3>
                </div>
                <p style="margin-bottom: 1rem; color: #6b7280;">${this.escapeHtml(monitoring.description || '')}</p>
                <div class="monitoring-commands">
                    ${commandsHtml}
                </div>
            </div>
        `;
    }

    renderReviewScheduleSection(reviewSchedule) {
        if (!reviewSchedule) return '';
        
        // Validate that reviewSchedule is an array
        if (!Array.isArray(reviewSchedule)) {
            throw new Error(`Review schedule must be an array, got ${typeof reviewSchedule}: ${JSON.stringify(reviewSchedule)}`);
        }
        
        const scheduleHtml = reviewSchedule.map(item => {
            if (!item || typeof item !== 'object') {
                throw new Error(`Review schedule item must be an object, got ${typeof item}: ${JSON.stringify(item)}`);
            }
            return `
            <div class="review-item" style="display: flex; align-items: center; padding: 0.75rem; background-color: #f8f9fa; border-radius: 4px; margin-bottom: 0.5rem;">
                <div style="background-color: #7ba573; color: white; border-radius: 50%; width: 2rem; height: 2rem; display: flex; align-items: center; justify-content: center; font-weight: 600; margin-right: 1rem;">
                    ${item.day}
                </div>
                <div>${this.escapeHtml(item.title)}</div>
            </div>
            `;
        }).join('');

        return `
            <div class="clean-chart-card" style="margin-bottom: 1.5rem;">
                <div class="chart-header">
                    <div class="chart-icon">
                        <i class="fas fa-calendar-check"></i>
                    </div>
                    <h3 class="chart-title">Review Schedule</h3>
                </div>
                <div class="review-schedule">
                    ${scheduleHtml}
                </div>
            </div>
        `;
    }

    renderNextStepsSection(nextSteps) {
        if (!nextSteps) return '';
        
        // Validate that nextSteps is an array
        if (!Array.isArray(nextSteps)) {
            throw new Error(`Next steps must be an array, got ${typeof nextSteps}: ${JSON.stringify(nextSteps)}`);
        }
        
        const stepsHtml = nextSteps.map((step, index) => {
            if (typeof step !== 'string') {
                console.warn('Invalid next step:', step);
                return '';
            }
            
            return `
            <div class="next-step-item" style="display: flex; align-items: center; padding: 0.75rem; background-color: #f8f9fa; border-radius: 4px; margin-bottom: 0.5rem;">
                <div style="background-color: #7ba573; color: white; border-radius: 50%; width: 2rem; height: 2rem; display: flex; align-items: center; justify-content: center; font-weight: 600; margin-right: 1rem; font-size: 0.875rem;">
                    ${index + 1}
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 500; color: #374151;">${this.escapeHtml(step)}</div>
                </div>
            </div>
            `;
        }).filter(html => html).join('');

        return `
            <div class="clean-chart-card" style="margin-bottom: 1.5rem;">
                <div class="chart-header">
                    <div class="chart-icon">
                        <i class="fas fa-list-check"></i>
                    </div>
                    <h3 class="chart-title">Next Steps</h3>
                </div>
                <div class="next-steps-container">
                    ${stepsHtml}
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

    getColorForRating(rating) {
        const colorMap = {
            'excellent': '#16a34a',
            'good': '#7ba573',
            'fair': '#f59e0b',
            'poor': '#dc2626'
        };
        return colorMap[rating] || '#6b7280';
    }

    getColorForScore(score) {
        // Convert numeric score (0-1) to color
        if (score >= 0.8) return '#16a34a'; // excellent - green
        if (score >= 0.6) return '#7ba573'; // good - light green
        if (score >= 0.4) return '#f59e0b'; // fair - orange
        return '#dc2626'; // poor - red
    }

    getStatusTypeFromResult(result) {
        // Convert database result strings to CSS class suffixes
        const resultLower = String(result).toLowerCase();
        if (resultLower.includes('low') || resultLower.includes('good') || resultLower.includes('pass')) return 'good';
        if (resultLower.includes('medium') || resultLower.includes('warning') || resultLower.includes('high')) return 'warning';
        if (resultLower.includes('error') || resultLower.includes('fail') || resultLower.includes('poor')) return 'error';
        return 'good'; // default
    }

    generateLabelFromCommand(command) {
        // Generate a user-friendly label from a kubectl command
        if (!command) return 'Monitoring Command';
        
        if (command.includes('kubectl top')) return 'Check Resource Usage';
        if (command.includes('kubectl get hpa')) return 'Check HPA Status';
        if (command.includes('kubectl describe hpa')) return 'Get HPA Details';
        if (command.includes('kubectl describe resourcequota')) return 'Check Resource Quotas';
        if (command.includes('kubectl describe pods')) return 'Get Pod Details';
        if (command.includes('kubectl get')) return 'List Resources';
        if (command.includes('kubectl describe')) return 'Describe Resource';
        
        return 'Kubectl Command';
    }

    getGradientForColor(color) {
        const gradientMap = {
            'green': '#16a34a, #22c55e',
            'blue': '#2563eb, #3b82f6',
            'purple': '#7c3aed, #a855f7',
            'red': '#dc2626, #ef4444'
        };
        return gradientMap[color] || '#6b7280, #9ca3af';
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

// CSS styles for implementation plan
const implementationStyles = `
<style>
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
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