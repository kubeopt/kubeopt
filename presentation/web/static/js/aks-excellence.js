/**
 * ============================================================================
 * AKS COST EXCELLENCE FRAMEWORK - Frontend Implementation
 * ============================================================================
 * Handles the display and interaction of Build Quality and Cost Excellence scores
 * ============================================================================
 */

// Global state for AKS Excellence scores
window.aksExcellenceState = {
    buildQualityScore: null,
    costExcellenceScore: null,
    isLoading: false,
    lastUpdate: null
};

/**
 * Initialize AKS Excellence framework on page load
 */
export function initializeAKSExcellence() {
    console.log('🎯 Initializing AKS Cost Excellence Framework...');
    
    // Make functions globally available
    window.refreshAKSScores = refreshAKSScores;
    window.showAKSScoreDetails = showAKSScoreDetails;
    
    // Load initial scores
    loadAKSScores();
    
    // Set up periodic refresh (every 15 minutes)
    setInterval(loadAKSScores, 15 * 60 * 1000);
}

/**
 * Load AKS Excellence scores from existing analysis data
 */
async function loadAKSScores() {
    const buildQualityElement = document.getElementById('build-quality-score');
    const costExcellenceElement = document.getElementById('cost-excellence-score');
    const buildBreakdownElement = document.getElementById('build-quality-breakdown');
    const costBreakdownElement = document.getElementById('cost-excellence-breakdown');
    
    if (!buildQualityElement || !costExcellenceElement) {
        console.warn('⚠️ AKS Excellence score elements not found');
        return;
    }
    
    try {
        // Show loading state
        setLoadingState(true);
        
        // Check if analysis data is available from the template
        if (!window.analysisData) {
            console.warn('⚠️ No analysis data available in window.analysisData');
            showErrorState('Analysis data not available. Please refresh the page or run analysis first.');
            return;
        }
        
        const analysisData = window.analysisData;
        
        // Check if AKS Excellence scores are available
        const buildQualityScore = analysisData.build_quality_score;
        const costExcellenceScore = analysisData.cost_excellence_score;
        
        if (buildQualityScore === null || buildQualityScore === undefined || 
            costExcellenceScore === null || costExcellenceScore === undefined) {
            console.warn('⚠️ AKS Excellence scores not yet calculated');
            console.log('📊 Available analysis keys:', Object.keys(analysisData));
            showErrorState('AKS Excellence scores not yet calculated. Please run analysis first.');
            
            // Still update savings opportunities if available
            updateSavingsOpportunities(analysisData.aks_savings_opportunities || []);
            return;
        }
        
        // Format analysis data for UI (same as API response format)
        const scores = {
            buildQuality: {
                score: buildQualityScore,
                label: getScoreLabel(buildQualityScore),
                color: getScoreColor(buildQualityScore)
            },
            costExcellence: {
                score: costExcellenceScore,
                label: getScoreLabel(costExcellenceScore),
                color: getScoreColor(costExcellenceScore)
            },
            buildQualityBreakdown: formatBreakdownForUI(analysisData.build_quality_breakdown || {}, {}),
            costExcellenceBreakdown: formatBreakdownForUI(analysisData.cost_excellence_breakdown || {}, {}),
            savingsOpportunities: analysisData.aks_savings_opportunities || []
        };
        
        updateUI(scores);
        
        // Also update HPA count display if the function is available
        if (typeof window.updateHPACount === 'function') {
            console.log('🔍 Calling updateHPACount from aks-excellence.js');
            window.updateHPACount(analysisData);
        } else {
            console.warn('⚠️ window.updateHPACount function not available');
        }
        
        console.log('✅ AKS Excellence scores loaded from existing analysis data');
        console.log('📊 Build Quality:', buildQualityScore, 'Cost Excellence:', costExcellenceScore);
        
    } catch (error) {
        console.error('❌ Failed to load AKS Excellence scores:', error);
        showErrorState('Failed to load AKS Excellence scores from analysis data.');
    } finally {
        setLoadingState(false);
    }
}

/**
 * Helper function to update UI with scores
 */
function updateUI(scores) {
    const buildQualityElement = document.getElementById('build-quality-score');
    const costExcellenceElement = document.getElementById('cost-excellence-score');
    const buildBreakdownElement = document.getElementById('build-quality-breakdown');
    const costBreakdownElement = document.getElementById('cost-excellence-breakdown');
    
    // Update the global state
    window.aksExcellenceState = {
        buildQualityScore: scores.buildQuality,
        costExcellenceScore: scores.costExcellence,
        isLoading: false,
        lastUpdate: new Date()
    };
    
    // Update the UI
    updateScoreDisplay(buildQualityElement, scores.buildQuality);
    updateScoreDisplay(costExcellenceElement, scores.costExcellence);
    
    // Update breakdowns
    if (buildBreakdownElement && scores.buildQualityBreakdown) {
        updateScoreBreakdown(buildBreakdownElement, scores.buildQualityBreakdown);
    }
    if (costBreakdownElement && scores.costExcellenceBreakdown) {
        updateScoreBreakdown(costBreakdownElement, scores.costExcellenceBreakdown);
    }
    
    // Update savings opportunities
    updateSavingsOpportunities(scores.savingsOpportunities || []);
    
    // Update recommendations if available
    const buildRecommendations = analysisData.build_quality_recommendations || [];
    const costRecommendations = analysisData.cost_excellence_recommendations || [];
    updateRecommendations([...buildRecommendations, ...costRecommendations]);
}

/**
 * Get current cluster ID from page URL or elements
 */
function getCurrentClusterId() {
    // Try to get from URL path
    const path = window.location.pathname;
    const clusterMatch = path.match(/\/cluster\/([^\/]+)/);
    if (clusterMatch) {
        return clusterMatch[1];
    }
    
    // Try to get from data attributes
    const clusterElement = document.querySelector('[data-cluster-id]');
    if (clusterElement) {
        return clusterElement.getAttribute('data-cluster-id');
    }
    
    return null;
}

/**
 * Format breakdown data from API for UI display (follows cost display pattern)
 */
function formatBreakdownForUI(breakdown, weights = {}) {
    if (!breakdown || typeof breakdown !== 'object') {
        return [];
    }
    
    // Convert API breakdown to UI format (same pattern as cost breakdown)
    return Object.entries(breakdown).map(([key, score]) => ({
        category: formatCategoryName(key),
        score: Math.round(score * 100), // Convert to percentage if needed
        weight: getWeightForCategory(key, weights)
    }));
}

/**
 * Format category names for display
 */
function formatCategoryName(key) {
    const categoryMap = {
        'UE': 'Utilization Efficiency',
        'AE': 'Autoscaling Efficacy',
        'CE': 'Cost Efficiency',
        'RS': 'Reliability & Saturation',
        'CH': 'Configuration Hygiene',
        'compute': 'Compute Optimization',
        'storage': 'Storage Efficiency',
        'network_lb': 'Network & Load Balancer',
        'observability': 'Observability Cost Control',
        'images': 'Container Images',
        'sec_tools': 'Security Tools',
        'platform_hygiene': 'Platform Hygiene',
        'idle_abandoned': 'Idle & Abandoned Resources'
    };
    
    return categoryMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Get display weight from API response (from YAML config via backend)
 */
function getWeightForCategory(key, weights = {}) {
    if (weights && weights[key]) {
        const weight = weights[key];
        // Convert decimal to percentage if needed
        if (weight < 1) {
            return `${Math.round(weight * 100)}%`;
        }
        return `${weight}%`;
    }
    return '';
}


/**
 * Get score label based on numeric score
 */
function getScoreLabel(score) {
    if (score >= 85) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 55) return 'Fair';
    return 'Needs Improvement';
}

/**
 * Get score color based on numeric score
 */
function getScoreColor(score) {
    if (score >= 85) return '#059669'; // Green
    if (score >= 70) return '#7FB069'; // Light green
    if (score >= 55) return '#d97706'; // Orange
    return '#dc2626'; // Red
}

/**
 * Update score display element
 */
function updateScoreDisplay(element, scoreData) {
    element.textContent = scoreData.score;
    element.style.color = scoreData.color;
    element.className = `score-value ${scoreData.label.toLowerCase().replace(' ', '-')}`;
    
    // Animate the score update
    element.style.transform = 'scale(1.1)';
    setTimeout(() => {
        element.style.transform = 'scale(1)';
    }, 200);
}

/**
 * Update score breakdown display
 */
function updateScoreBreakdown(element, breakdown) {
    const breakdownHTML = breakdown.map(item => `
        <div class="breakdown-item">
            <div class="breakdown-category">
                <span class="category-name">${item.category}</span>
                <span class="category-weight">${item.weight}</span>
            </div>
            <div class="breakdown-score">
                <div class="score-bar">
                    <div class="score-fill" style="width: ${item.score}%; background-color: ${getScoreColor(item.score)};"></div>
                </div>
                <span class="score-number">${item.score}</span>
            </div>
        </div>
    `).join('');
    
    element.innerHTML = breakdownHTML;
}

/**
 * Set loading state for score elements
 */
function setLoadingState(isLoading) {
    const buildElement = document.getElementById('build-quality-score');
    const costElement = document.getElementById('cost-excellence-score');
    
    if (isLoading) {
        if (buildElement) {
            buildElement.innerHTML = '<span class="excellence-score-loading"><span class="spinner"></span> Loading...</span>';
        }
        if (costElement) {
            costElement.innerHTML = '<span class="excellence-score-loading"><span class="spinner"></span> Loading...</span>';
        }
    }
    
    window.aksExcellenceState.isLoading = isLoading;
}

/**
 * Show error state
 */
function showErrorState(message = 'Error loading scores') {
    const buildElement = document.getElementById('build-quality-score');
    const costElement = document.getElementById('cost-excellence-score');
    
    if (buildElement) buildElement.innerHTML = `<div class="error-state text-danger">${message}</div>`;
    if (costElement) costElement.innerHTML = `<div class="error-state text-danger">${message}</div>`;
}

/**
 * Refresh AKS scores (called by button click) - triggers page reload to get fresh data
 */
async function refreshAKSScores() {
    console.log('🔄 Refreshing AKS Excellence scores by reloading page...');
    // Since we're now using data from the template, refresh means reloading the page
    // to get fresh analysis data from the backend
    window.location.reload();
}

/**
 * Show detailed AKS score information (called by click)
 */
function showAKSScoreDetails(scoreType) {
    const state = window.aksExcellenceState;
    const score = scoreType === 'build' ? state.buildQualityScore : state.costExcellenceScore;
    
    if (!score) {
        console.warn('⚠️ Score data not available');
        return;
    }
    
    // This could open a modal with detailed information
    console.log(`📊 ${scoreType} Quality Score Details:`, score);
    alert(`${scoreType === 'build' ? 'Build' : 'Cost'} Excellence Score: ${score.score}/100 (${score.label})`);
}

/**
 * Update savings opportunities display with real analysis data
 */
function updateSavingsOpportunities(opportunities) {
    const savingsContainer = document.getElementById('aks-savings-opportunities');
    if (!savingsContainer) {
        console.warn('⚠️ Savings opportunities container not found');
        return;
    }
    
    if (!opportunities || opportunities.length === 0) {
        savingsContainer.innerHTML = `
            <div class="savings-item">
                <div class="savings-icon">
                    <i class="fas fa-info-circle"></i>
                </div>
                <div class="savings-info">
                    <span class="savings-category">No Opportunities</span>
                    <span class="savings-description">No cost optimization opportunities identified at this time</span>
                </div>
                <div class="savings-amount">$0</div>
            </div>
        `;
        return;
    }
    
    // Display top 3 savings opportunities
    const topOpportunities = opportunities.slice(0, 3);
    const savingsHTML = topOpportunities.map(opp => {
        const monthlySavings = parseFloat(opp.monthly_savings || 0);
        const formattedSavings = monthlySavings >= 1000 ? 
            `$${(monthlySavings / 1000).toFixed(1)}k` : 
            `$${monthlySavings.toFixed(0)}`;
        
        // Get icon based on category
        const categoryIcon = getCategoryIcon(opp.category);
        const confidenceClass = (opp.confidence || '').toLowerCase();
        
        return `
            <div class="savings-item" data-confidence="${confidenceClass}">
                <div class="savings-icon">
                    <i class="fas ${categoryIcon}"></i>
                </div>
                <div class="savings-info">
                    <span class="savings-category">${opp.category || 'Optimization'}</span>
                    <span class="savings-description">${opp.description || 'Cost optimization opportunity'}</span>
                    <small class="savings-confidence">Confidence: ${opp.confidence || 'Medium'} | Effort: ${opp.effort || 'Medium'}</small>
                </div>
                <div class="savings-amount">${formattedSavings}/mo</div>
            </div>
        `;
    }).join('');
    
    savingsContainer.innerHTML = savingsHTML;
    console.log(`✅ Updated ${topOpportunities.length} savings opportunities`);
}

/**
 * Get appropriate icon for savings category
 */
function getCategoryIcon(category) {
    const categoryLower = (category || '').toLowerCase();
    
    if (categoryLower.includes('compute')) return 'fa-microchip';
    if (categoryLower.includes('storage')) return 'fa-hdd';
    if (categoryLower.includes('network')) return 'fa-network-wired';
    if (categoryLower.includes('observability') || categoryLower.includes('log')) return 'fa-chart-line';
    if (categoryLower.includes('idle') || categoryLower.includes('cleanup')) return 'fa-trash-alt';
    if (categoryLower.includes('reserved') || categoryLower.includes('spot')) return 'fa-coins';
    
    return 'fa-cog'; // Default icon
}

/**
 * Update recommendations display with data from AKS scoring system
 */
function updateRecommendations(recommendations) {
    const recommendationsContainer = document.getElementById('aks-recommendations');
    if (!recommendationsContainer) {
        console.warn('⚠️ Recommendations container not found');
        return;
    }
    
    if (!recommendations || recommendations.length === 0) {
        recommendationsContainer.innerHTML = `
            <div class="recommendations-placeholder">
                <div class="recommendations-placeholder-icon">
                    <i class="fas fa-check-circle text-success"></i>
                </div>
                <h4 class="recommendations-placeholder-title">No Recommendations Needed</h4>
                <p class="recommendations-placeholder-text">Your cluster configuration meets the current optimization standards</p>
                <span class="recommendations-placeholder-note">Scores above 70% don't require immediate attention</span>
            </div>
        `;
        return;
    }
    
    // Group recommendations by priority
    const priorityOrder = ['Critical', 'High', 'Medium', 'Low'];
    const groupedRecs = recommendations.reduce((groups, rec) => {
        const priority = rec.priority || 'Medium';
        if (!groups[priority]) groups[priority] = [];
        groups[priority].push(rec);
        return groups;
    }, {});
    
    let recommendationsHTML = '';
    
    // Display recommendations by priority
    priorityOrder.forEach(priority => {
        if (groupedRecs[priority] && groupedRecs[priority].length > 0) {
            recommendationsHTML += `
                <div class="recommendations-priority-section">
                    <h5 class="recommendations-priority-header ${priority.toLowerCase()}">
                        <i class="fas ${getPriorityIcon(priority)}"></i>
                        ${priority} Priority (${groupedRecs[priority].length})
                    </h5>
                    <div class="recommendations-list">
            `;
            
            groupedRecs[priority].forEach(rec => {
                const isBasedOnRealMetrics = rec.based_on_real_metrics === true;
                const yamlStandard = rec.yaml_standard ? `Based on: ${rec.yaml_standard}` : '';
                
                recommendationsHTML += `
                    <div class="recommendation-item ${priority.toLowerCase()}" data-priority="${priority}">
                        <div class="recommendation-header">
                            <div class="recommendation-icon">
                                <i class="fas ${getRecommendationIcon(rec.category)}"></i>
                            </div>
                            <div class="recommendation-title">
                                <h6>${rec.category}</h6>
                                <div class="recommendation-badges">
                                    <span class="priority-badge ${priority.toLowerCase()}">${priority}</span>
                                    <span class="impact-badge ${rec.impact ? rec.impact.toLowerCase() : 'medium'}">${rec.impact || 'Medium'} Impact</span>
                                    ${isBasedOnRealMetrics ? '<span class="metrics-badge real-metrics">Real Metrics</span>' : '<span class="metrics-badge estimated">Estimated</span>'}
                                </div>
                            </div>
                        </div>
                        <div class="recommendation-content">
                            <p class="recommendation-description">${rec.description}</p>
                            <div class="recommendation-action">
                                <strong>Action:</strong> ${rec.action}
                            </div>
                            ${yamlStandard ? `<div class="recommendation-standard"><small><em>${yamlStandard}</em></small></div>` : ''}
                        </div>
                    </div>
                `;
            });
            
            recommendationsHTML += `
                    </div>
                </div>
            `;
        }
    });
    
    if (recommendationsHTML) {
        recommendationsContainer.innerHTML = recommendationsHTML;
        console.log(`✅ Updated ${recommendations.length} recommendations`);
    } else {
        recommendationsContainer.innerHTML = `
            <div class="recommendations-placeholder">
                <div class="recommendations-placeholder-icon">
                    <i class="fas fa-info-circle"></i>
                </div>
                <h4 class="recommendations-placeholder-title">No Active Recommendations</h4>
                <p class="recommendations-placeholder-text">All scoring components are within acceptable ranges</p>
            </div>
        `;
    }
}

/**
 * Get icon for recommendation priority
 */
function getPriorityIcon(priority) {
    switch (priority.toLowerCase()) {
        case 'critical': return 'fa-exclamation-triangle';
        case 'high': return 'fa-exclamation';
        case 'medium': return 'fa-info';
        case 'low': return 'fa-check';
        default: return 'fa-info';
    }
}

/**
 * Get icon for recommendation category
 */
function getRecommendationIcon(category) {
    const categoryLower = (category || '').toLowerCase();
    
    if (categoryLower.includes('cpu') || categoryLower.includes('utilization')) return 'fa-microchip';
    if (categoryLower.includes('memory')) return 'fa-memory';
    if (categoryLower.includes('autoscaling') || categoryLower.includes('hpa')) return 'fa-expand-arrows-alt';
    if (categoryLower.includes('cost') || categoryLower.includes('spot') || categoryLower.includes('reserved')) return 'fa-dollar-sign';
    if (categoryLower.includes('storage')) return 'fa-hdd';
    if (categoryLower.includes('network')) return 'fa-network-wired';
    if (categoryLower.includes('observability') || categoryLower.includes('log')) return 'fa-chart-line';
    if (categoryLower.includes('configuration') || categoryLower.includes('hygiene')) return 'fa-cog';
    if (categoryLower.includes('reliability')) return 'fa-shield-alt';
    
    return 'fa-tasks'; // Default icon
}

// Auto-initialize when script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAKSExcellence);
} else {
    initializeAKSExcellence();
}