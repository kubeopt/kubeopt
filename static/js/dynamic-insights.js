/**
 * ============================================================================
 * AKS COST INTELLIGENCE - DYNAMIC INSIGHTS GENERATOR (FIXED)
 * ============================================================================
 * Generates insights dynamically from actual analysis data
 * NO DUPLICATE API CALLS - Works with charts.js
 * ============================================================================
 */

import { showNotification } from './notifications.js';
import { getInsightIcon } from './utils.js';

/**
 * Enhanced dynamic insights generator using REAL analysis data
 */
export function generateRealDynamicInsights(data) {
    console.log('🧠 Generating REAL dynamic insights from analysis data:', data);
    
    const metrics = data.metrics || {};
    const costBreakdown = data.costBreakdown || {};
    const insights = {};
    
    // ============================================================================
    // COST INSIGHT - DYNAMIC FROM REAL DATA
    // ============================================================================
    
    if (costBreakdown.labels && costBreakdown.values && costBreakdown.values.length > 0) {
        // Find the highest cost component
        const maxIndex = costBreakdown.values.indexOf(Math.max(...costBreakdown.values));
        const topCostCategory = costBreakdown.labels[maxIndex];
        const topCostValue = costBreakdown.values[maxIndex];
        const totalCost = costBreakdown.values.reduce((a, b) => a + b, 0);
        const percentage = totalCost > 0 ? Math.round((topCostValue / totalCost) * 100) : 0;
        
        // Generate personalized insight based on the category
        let categoryAdvice = '';
        const categoryLower = topCostCategory.toLowerCase();
        
        if (categoryLower.includes('vm') || categoryLower.includes('scale')) {
            categoryAdvice = 'Consider implementing right-sizing recommendations and scheduled scaling';
        } else if (categoryLower.includes('storage') || categoryLower.includes('disk')) {
            categoryAdvice = 'Optimize storage tiers and implement automated cleanup policies';
        } else if (categoryLower.includes('network')) {
            categoryAdvice = 'Review network architecture and implement traffic optimization';
        } else if (categoryLower.includes('control') || categoryLower.includes('plane')) {
            categoryAdvice = 'Control plane costs are fixed, focus on optimizing workload resources';
        } else {
            categoryAdvice = 'Analyze usage patterns and implement cost optimization strategies';
        }
        
        insights.cost = `${topCostCategory} accounts for ${percentage}% of your monthly budget ($${topCostValue.toLocaleString()}). ${categoryAdvice}.`;
        
    } else if (metrics.total_cost && metrics.total_cost > 0) {
        // Fallback with total cost data
        const monthlyCost = Math.round(metrics.total_cost);
        insights.cost = `Current monthly spend is $${monthlyCost.toLocaleString()}. Primary optimization opportunities identified in compute resources.`;
        
    } else {
        insights.cost = `Cost analysis completed. Review the breakdown above to identify your highest spending categories.`;
    }
    
    // ============================================================================
    // HPA INSIGHT - DYNAMIC FROM REAL DATA
    // ============================================================================
    
    const hpaReduction = metrics.hpa_reduction || metrics.hpa_efficiency || 0;
    const hpaSavings = metrics.hpa_savings || 0;
    const totalSavings = metrics.total_savings || 0;
    
    if (hpaReduction > 0 && hpaSavings > 0) {
        // Real HPA data available
        const reductionPct = Math.round(hpaReduction);
        const monthlySavings = Math.round(hpaSavings);
        const annualSavings = Math.round(monthlySavings * 12);
        
        insights.hpa = `Memory-based HPA optimization could reduce replica count by ${reductionPct}%, saving $${monthlySavings.toLocaleString()}/month ($${annualSavings.toLocaleString()}/year) through intelligent auto-scaling.`;
        
    } else if (totalSavings > 0) {
        // Estimate HPA portion from total savings
        const estimatedHpaSavings = Math.round(totalSavings * 0.3); // Assume 30% from HPA
        insights.hpa = `HPA optimization represents significant opportunity. Estimated potential savings of $${estimatedHpaSavings.toLocaleString()}/month through improved auto-scaling efficiency.`;
        
    } else if (metrics.cpu_gap || metrics.memory_gap) {
        // Use resource gap data
        const cpuGap = metrics.cpu_gap || 0;
        const memoryGap = metrics.memory_gap || 0;
        const avgGap = Math.round((cpuGap + memoryGap) / 2);
        
        if (avgGap > 20) {
            insights.hpa = `Resource utilization shows ${avgGap}% efficiency gap. Memory-based HPA could significantly optimize replica scaling.`;
        } else {
            insights.hpa = `Resource utilization is well-optimized. Monitor scaling patterns to maintain efficiency as workload demands change.`;
        }
        
    } else {
        insights.hpa = `HPA analysis in progress. Memory-based scaling optimization opportunities will be identified.`;
    }
    
    // ============================================================================
    // ADDITIONAL DYNAMIC INSIGHTS
    // ============================================================================
    
    // Right-sizing insight
    if (metrics.right_sizing_savings > 0) {
        const rightSizingSavings = Math.round(metrics.right_sizing_savings);
        insights.rightsizing = `Right-sizing recommendations could save $${rightSizingSavings.toLocaleString()}/month by matching resource allocation to actual usage patterns.`;
    }
    
    // Storage insight
    if (metrics.storage_savings > 0) {
        const storageSavings = Math.round(metrics.storage_savings);
        insights.storage = `Storage optimization could save $${storageSavings.toLocaleString()}/month through tier optimization and cleanup automation.`;
    }
    
    // Overall optimization insight
    if (totalSavings > 0) {
        const savingsPct = metrics.savings_percentage || 0;
        const monthlySavings = Math.round(totalSavings);
        const annualSavings = Math.round(totalSavings * 12);
        
        insights.overall = `Total optimization potential: ${Math.round(savingsPct)}% reduction ($${monthlySavings.toLocaleString()}/month, $${annualSavings.toLocaleString()}/year) through comprehensive resource optimization.`;
    }
    
    // Performance insight
    if (metrics.performance_score || metrics.optimization_score) {
        const score = metrics.performance_score || metrics.optimization_score || 0;
        if (score >= 80) {
            insights.performance = `Excellent cluster performance score of ${Math.round(score)}%. Minor optimizations available to maintain peak efficiency.`;
        } else if (score >= 60) {
            insights.performance = `Good cluster performance score of ${Math.round(score)}%. Several optimization opportunities identified for improvement.`;
        } else {
            insights.performance = `Performance score of ${Math.round(score)}% indicates significant optimization potential. Comprehensive improvements recommended.`;
        }
    }
    
    // Security insight
    if (metrics.security_score) {
        const secScore = metrics.security_score;
        if (secScore >= 90) {
            insights.security = `Strong security posture with ${Math.round(secScore)}% compliance. Continue monitoring for emerging threats.`;
        } else if (secScore >= 70) {
            insights.security = `Good security baseline at ${Math.round(secScore)}%. Address identified vulnerabilities to strengthen protection.`;
        } else {
            insights.security = `Security score of ${Math.round(secScore)}% requires immediate attention. Implement recommended security improvements.`;
        }
    }
    
    console.log('✅ Generated REAL dynamic insights:', insights);
    return insights;
}

/**
 * FIXED: Update insights using data passed from charts.js (NO API CALL)
 */
export function updateRealDynamicInsights(data) {
    console.log('📊 Updating insights with REAL dynamic content from:', data);
    
    const insights = generateRealDynamicInsights(data);
    
    // Update cost insight with animation
    const costInsightElement = document.querySelector('#cost-insight');
    if (costInsightElement) {
        animateInsightUpdate(costInsightElement, insights.cost);
        console.log('✅ Updated cost insight with real data');
    }
    
    // Update HPA insight with animation
    const hpaInsightElement = document.querySelector('#hpa-insight');
    if (hpaInsightElement) {
        animateInsightUpdate(hpaInsightElement, insights.hpa);
        console.log('✅ Updated HPA insight with real data');
    }
    
    // Update additional insights if container exists
    const insightsContainer = document.querySelector('#insights-container');
    if (insightsContainer) {
        updateAdditionalInsights(insightsContainer, insights);
    }
    
    // Update specific insight cards if they exist
    updateSpecificInsightCards(insights);
}

/**
 * Animate insight update with smooth transition
 */
function animateInsightUpdate(element, newContent) {
    if (!element || !newContent) return;
    
    // Add loading complete class
    element.closest('.insight-box, .saving-box')?.classList.add('loaded');
    
    // Smooth transition
    element.style.transition = 'all 0.4s ease';
    element.style.opacity = '0.3';
    element.style.transform = 'translateY(10px)';
    
    setTimeout(() => {
        element.innerHTML = newContent;
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
        
        // Add success indicator
        element.classList.add('insight-updated');
        setTimeout(() => {
            element.classList.remove('insight-updated');
        }, 2000);
    }, 200);
}

/**
 * Update additional insights container
 */
function updateAdditionalInsights(container, insights) {
    const additionalInsights = ['rightsizing', 'storage', 'overall', 'performance', 'security'];
    let hasAdditional = false;
    
    let additionalHTML = '';
    
    additionalInsights.forEach(key => {
        if (insights[key]) {
            hasAdditional = true;
            const title = key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
            const icon = getInsightIcon(key);
            const colorClass = getInsightColorClass(key);
            
            additionalHTML += `
                <div class="insight-item mb-3 p-3 border rounded bg-light insight-fade-in border-${colorClass}">
                    <h6 class="text-${colorClass}">
                        <i class="fas fa-${icon} me-2"></i>${title} Insight
                    </h6>
                    <p class="mb-0">${insights[key]}</p>
                </div>
            `;
        }
    });
    
    if (hasAdditional) {
        container.innerHTML = additionalHTML;
        
        // Animate in the new insights
        setTimeout(() => {
            container.querySelectorAll('.insight-fade-in').forEach((insight, index) => {
                setTimeout(() => {
                    insight.style.opacity = '1';
                    insight.style.transform = 'translateY(0)';
                }, index * 150);
            });
        }, 100);
    } else {
        container.innerHTML = '<p class="text-muted">Additional insights will appear as more optimization opportunities are identified.</p>';
    }
}

/**
 * Update specific insight cards throughout the dashboard
 */
function updateSpecificInsightCards(insights) {
    // Update performance cards
    if (insights.performance) {
        const performanceCards = document.querySelectorAll('.performance-insight, [data-insight="performance"]');
        performanceCards.forEach(card => {
            animateInsightUpdate(card, insights.performance);
        });
    }
    
    // Update security cards
    if (insights.security) {
        const securityCards = document.querySelectorAll('.security-insight, [data-insight="security"]');
        securityCards.forEach(card => {
            animateInsightUpdate(card, insights.security);
        });
    }
    
    // Update optimization cards
    if (insights.overall) {
        const optimizationCards = document.querySelectorAll('.optimization-insight, [data-insight="optimization"]');
        optimizationCards.forEach(card => {
            animateInsightUpdate(card, insights.overall);
        });
    }
}

/**
 * Get color class for insight type
 */
function getInsightColorClass(type) {
    const colors = {
        'rightsizing': 'primary',
        'storage': 'info',
        'overall': 'success',
        'performance': 'warning',
        'security': 'danger',
        'cost': 'primary',
        'hpa': 'success'
    };
    return colors[type] || 'secondary';
}

/**
 * Generate insight summary for dashboard
 */
export function generateInsightSummary(insights) {
    const summaryItems = [];
    
    Object.entries(insights).forEach(([key, value]) => {
        if (value && value.length > 10) { // Only include meaningful insights
            const words = value.split(' ');
            const summary = words.slice(0, 15).join(' ') + (words.length > 15 ? '...' : '');
            summaryItems.push({
                type: key,
                summary: summary,
                icon: getInsightIcon(key),
                color: getInsightColorClass(key)
            });
        }
    });
    
    return summaryItems;
}

/**
 * Create insight notification for important findings
 */
export function createInsightNotification(insights) {
    const criticalInsights = [];
    
    // Check for high-impact insights
    Object.entries(insights).forEach(([key, value]) => {
        if (value && value.includes('$') && key !== 'cost') {
            // Extract dollar amounts
            const matches = value.match(/\$[\d,]+/g);
            if (matches) {
                const amounts = matches.map(match => 
                    parseInt(match.replace(/[$,]/g, ''))
                ).filter(amount => amount > 1000); // Significant amounts only
                
                if (amounts.length > 0) {
                    criticalInsights.push({
                        type: key,
                        amount: Math.max(...amounts),
                        insight: value.split('.')[0] + '.' // First sentence only
                    });
                }
            }
        }
    });
    
    // Show notification for highest impact insight
    if (criticalInsights.length > 0) {
        const topInsight = criticalInsights.reduce((prev, current) => 
            (prev.amount > current.amount) ? prev : current
        );
        
        setTimeout(() => {
            showNotification(
                `💡 Key Finding: ${topInsight.insight}`,
                'info',
                8000
            );
        }, 3000);
    }
}

/**
 * REMOVED: No more duplicate API calls - insights are updated by charts.js
 * This function now just sets up loading states
 */
export function showInsightLoadingStates() {
    const insightSelectors = ['#cost-insight', '#hpa-insight'];
    
    insightSelectors.forEach(selector => {
        const element = document.querySelector(selector);
        if (element) {
            element.innerHTML = `
                <span class="loading-text">
                    <i class="fas fa-spinner fa-spin me-2"></i>
                    Analyzing data to generate personalized insights...
                </span>
            `;
        }
    });
}

/**
 * FIXED: No more function overriding - work with charts.js
 */
export function initializeInsightsSystem() {
    console.log('🚀 Initializing insights system (no API duplicates)...');
    
    // DON'T override initializeCharts - let charts.js handle it
    // Just make our functions available
    if (typeof window !== 'undefined') {
        window.updateRealDynamicInsights = updateRealDynamicInsights;
        window.generateRealDynamicInsights = generateRealDynamicInsights;
        window.showInsightLoadingStates = showInsightLoadingStates;
    }
    
    console.log('✅ Insights system initialized (charts.js will handle API calls)');
}

// CSS for insight animations
function addInsightAnimationCSS() {
    if (document.getElementById('insight-animation-css')) return;
    
    const style = document.createElement('style');
    style.id = 'insight-animation-css';
    style.textContent = `
        .insight-updated {
            position: relative;
        }
        
        .insight-updated::before {
            content: '✨';
            position: absolute;
            top: -10px;
            right: -10px;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            border-radius: 50%;
            width: 25px;
            height: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            animation: sparkle 1s ease-out;
            box-shadow: 0 2px 10px rgba(40, 167, 69, 0.3);
        }
        
        .insight-fade-in {
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.5s ease;
        }
        
        .insight-box.loaded,
        .saving-box.loaded {
            border-left-color: #28a745 !important;
            background: linear-gradient(135deg, rgba(40, 167, 69, 0.05), rgba(40, 167, 69, 0.02)) !important;
        }
        
        .loading-text {
            color: #6c757d;
            font-style: italic;
        }
        
        @keyframes sparkle {
            0% { opacity: 0; transform: scale(0) rotate(0deg); }
            50% { opacity: 1; transform: scale(1.2) rotate(180deg); }
            100% { opacity: 1; transform: scale(1) rotate(360deg); }
        }
        
        .insight-item {
            transition: all 0.3s ease;
        }
        
        .insight-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .border-primary { border-left: 4px solid #007bff !important; }
        .border-success { border-left: 4px solid #28a745 !important; }
        .border-info { border-left: 4px solid #17a2b8 !important; }
        .border-warning { border-left: 4px solid #ffc107 !important; }
        .border-danger { border-left: 4px solid #dc3545 !important; }
        .border-secondary { border-left: 4px solid #6c757d !important; }
    `;
    document.head.appendChild(style);
}

// Make functions globally available (but don't override charts.js functions)
if (typeof window !== 'undefined') {
    window.generateRealDynamicInsights = generateRealDynamicInsights;
    window.updateRealDynamicInsights = updateRealDynamicInsights;
    window.generateInsightSummary = generateInsightSummary;
    window.createInsightNotification = createInsightNotification;
    window.showInsightLoadingStates = showInsightLoadingStates;
}

console.log('✅ REAL Dynamic Insights Generator loaded (fixed - no API duplicates)');