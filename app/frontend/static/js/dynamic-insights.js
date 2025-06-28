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
    console.log('🧠 Generating REAL dynamic insights from ML analysis data:', data);
    
    const metrics = data.metrics || {};
    const costBreakdown = data.costBreakdown || {};
    const hpaComparison = data.hpaComparison || {};
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
    }
    
    // ============================================================================
    // ML-INTEGRATED HPA INSIGHT (PRIMARY)
    // ============================================================================
    
    if (hpaComparison.ml_workload_type && hpaComparison.recommendation_text) {
        // Use ML classification and recommendation directly
        const workloadType = hpaComparison.ml_workload_type;
        const mlConfidence = hpaComparison.ml_confidence || 0;
        const savings = hpaComparison.actual_hpa_savings || 0;
        const efficiency = hpaComparison.actual_hpa_efficiency || 0;
        
        // Create rich ML-based insight
        const confidenceText = mlConfidence > 0.9 ? 'Very High' : 
                              mlConfidence > 0.8 ? 'High' : 
                              mlConfidence > 0.7 ? 'Good' : 'Medium';
        
        let workloadDescription = '';
        switch (workloadType) {
            case 'LOW_UTILIZATION':
                workloadDescription = 'over-provisioned resources with significant waste detected';
                break;
            case 'CPU_INTENSIVE':
                workloadDescription = 'CPU-bound workload requiring responsive scaling';
                break;
            case 'MEMORY_INTENSIVE':
                workloadDescription = 'memory-bound workload needing careful allocation';
                break;
            case 'BURSTY':
                workloadDescription = 'variable traffic patterns requiring predictive scaling';
                break;
            case 'BALANCED':
                workloadDescription = 'well-balanced resource usage across CPU and memory';
                break;
            default:
                workloadDescription = 'specialized workload pattern';
        }
        
        insights.hpa = `🤖 <strong>ML Analysis (${confidenceText} Confidence)</strong>: Classified as <strong>${workloadType}</strong> - ${workloadDescription}. ${hpaComparison.recommendation_text}`;
        
        console.log(`✅ Generated ML-integrated HPA insight: ${workloadType} with $${savings} savings`);
    }
    
    // ============================================================================
    // ML CLASSIFICATION INSIGHT
    // ============================================================================
    
    if (hpaComparison.ml_workload_type) {
        const workloadType = hpaComparison.ml_workload_type;
        const confidence = hpaComparison.ml_confidence || 0;
        const efficiency = hpaComparison.actual_hpa_efficiency || 0;
        
        let actionableAdvice = '';
        let urgencyLevel = '';
        let expectedImpact = '';
        
        switch (workloadType) {
            case 'LOW_UTILIZATION':
                actionableAdvice = 'Immediate scale-down opportunities identified. Reduce resource requests to eliminate waste.';
                urgencyLevel = 'High Priority';
                expectedImpact = 'Significant cost reduction with no performance impact';
                break;
            case 'CPU_INTENSIVE':
                actionableAdvice = 'Implement CPU-based HPA with aggressive scaling policies. Monitor for CPU bottlenecks.';
                urgencyLevel = 'Medium Priority';
                expectedImpact = 'Improved responsiveness and automatic scaling';
                break;
            case 'MEMORY_INTENSIVE':
                actionableAdvice = 'Deploy memory-based HPA to prevent OOM kills. Consider memory-optimized instance types.';
                urgencyLevel = 'High Priority';
                expectedImpact = 'Reduced application crashes and better stability';
                break;
            case 'BURSTY':
                actionableAdvice = 'Implement predictive scaling with custom metrics. Consider scheduled scaling for known patterns.';
                urgencyLevel = 'Medium Priority';
                expectedImpact = 'Better handling of traffic spikes and cost optimization';
                break;
            case 'BALANCED':
                actionableAdvice = 'Fine-tune existing HPA configurations. Implement hybrid CPU+Memory scaling approach.';
                urgencyLevel = 'Low Priority';
                expectedImpact = 'Optimized resource allocation and scaling precision';
                break;
        }
        
        insights.ml_classification = `🎯 <strong>${urgencyLevel}:</strong> ${workloadType} workload detected with ${(confidence * 100).toFixed(0)}% confidence (Efficiency: ${efficiency.toFixed(1)}%). ${actionableAdvice} <em>${expectedImpact}</em>.`;
    }
    
    // ============================================================================
    // COST OPTIMIZATION INSIGHTS
    // ============================================================================
    
    // Right-sizing insight with ML context
    if (metrics.right_sizing_savings > 0) {
        const rightSizingSavings = Math.round(metrics.right_sizing_savings);
        const cpuGap = metrics.cpu_gap || 0;
        const memoryGap = metrics.memory_gap || 0;
        
        insights.rightsizing = `💡 <strong>Right-sizing Opportunity:</strong> ${cpuGap.toFixed(1)}% CPU gap and ${memoryGap.toFixed(1)}% memory gap detected. ML-guided resource optimization could save <strong>$${rightSizingSavings.toLocaleString()}/month</strong>.`;
    }
    
    // Storage insight with specific recommendations
    if (metrics.storage_savings > 0) {
        const storageSavings = Math.round(metrics.storage_savings);
        insights.storage = `💾 <strong>Storage Optimization:</strong> ML analysis identified $${storageSavings.toLocaleString()}/month savings through automated tier management, volume cleanup, and snapshot optimization.`;
    }
    
    // Overall optimization summary with ML confidence
    if (metrics.total_savings > 0) {
        const savingsPct = metrics.savings_percentage || 0;
        const monthlySavings = Math.round(metrics.total_savings);
        const annualSavings = Math.round(metrics.total_savings * 12);
        const confidenceLevel = metrics.analysis_confidence || 0;
        
        let confidenceText = confidenceLevel > 0.8 ? 'High-Confidence' : 
                            confidenceLevel > 0.6 ? 'Validated' : 'Estimated';
        
        insights.overall = `🚀 <strong>${confidenceText} ML Analysis:</strong> Total optimization potential of <strong>${Math.round(savingsPct)}%</strong> identified. Monthly savings: <strong>$${monthlySavings.toLocaleString()}</strong> | Annual impact: <strong>$${annualSavings.toLocaleString()}</strong>.`;
    }
    
    // ============================================================================
    // PERFORMANCE & EFFICIENCY INSIGHTS
    // ============================================================================
    
    // Performance insight based on ML analysis
    if (hpaComparison.actual_hpa_efficiency !== undefined) {
        const efficiency = hpaComparison.actual_hpa_efficiency;
        const wasteDetected = 100 - efficiency;
        
        if (efficiency > 80) {
            insights.performance = `✅ <strong>High Efficiency:</strong> Current HPA efficiency of ${efficiency.toFixed(1)}% indicates well-optimized resource allocation. Monitor for drift.`;
        } else if (efficiency > 50) {
            insights.performance = `⚠️ <strong>Optimization Needed:</strong> HPA efficiency of ${efficiency.toFixed(1)}% shows ${wasteDetected.toFixed(1)}% resource waste. Immediate optimization recommended.`;
        } else {
            insights.performance = `🚨 <strong>Critical Inefficiency:</strong> Only ${efficiency.toFixed(1)}% HPA efficiency detected. ${wasteDetected.toFixed(1)}% resource waste requires urgent attention.`;
        }
    }
    
    // Resource utilization pattern insight
    if (hpaComparison.current_cpu_avg !== undefined && hpaComparison.current_memory_avg !== undefined) {
        const cpuUtil = hpaComparison.current_cpu_avg;
        const memoryUtil = hpaComparison.current_memory_avg;
        const resourceBalance = Math.abs(cpuUtil - memoryUtil);
        
        if (resourceBalance > 30) {
            const dominantResource = cpuUtil > memoryUtil ? 'CPU' : 'Memory';
            const dominantValue = Math.max(cpuUtil, memoryUtil);
            const underutilizedResource = cpuUtil < memoryUtil ? 'CPU' : 'Memory';
            const underutilizedValue = Math.min(cpuUtil, memoryUtil);
            
            insights.resource_balance = `⚖️ <strong>Resource Imbalance:</strong> ${dominantResource} utilization (${dominantValue.toFixed(1)}%) significantly exceeds ${underutilizedResource} (${underutilizedValue.toFixed(1)}%). Consider ${dominantResource.toLowerCase()}-optimized scaling strategies.`;
        } else {
            insights.resource_balance = `⚖️ <strong>Balanced Resources:</strong> CPU (${cpuUtil.toFixed(1)}%) and Memory (${memoryUtil.toFixed(1)}%) utilization are well-balanced. Current allocation strategy is appropriate.`;
        }
    }
    
    // ============================================================================
    // PREDICTIVE INSIGHTS
    // ============================================================================
    
    // Growth prediction based on current patterns
    if (metrics.total_cost > 0) {
        const currentCost = metrics.total_cost;
        const potentialSavings = metrics.total_savings || 0;
        const optimizedCost = currentCost - potentialSavings;
        const annualCostWithoutOptimization = currentCost * 12;
        const annualCostWithOptimization = optimizedCost * 12;
        
        insights.prediction = `📈 <strong>12-Month Projection:</strong> Without optimization: $${annualCostWithoutOptimization.toLocaleString()}/year. With ML-guided optimization: $${annualCostWithOptimization.toLocaleString()}/year. <strong>Net benefit: $${(annualCostWithoutOptimization - annualCostWithOptimization).toLocaleString()}</strong>.`;
    }
    
    // ============================================================================
    // ACTIONABLE RECOMMENDATIONS
    // ============================================================================
    
    // Immediate actions based on ML analysis
    if (hpaComparison.ml_workload_type) {
        const workloadType = hpaComparison.ml_workload_type;
        let immediateActions = [];
        
        switch (workloadType) {
            case 'LOW_UTILIZATION':
                immediateActions = [
                    'Scale down over-provisioned deployments',
                    'Reduce resource requests by 30-50%',
                    'Implement cluster autoscaling',
                    'Enable vertical pod autoscaling'
                ];
                break;
            case 'CPU_INTENSIVE':
                immediateActions = [
                    'Deploy CPU-based HPA configurations',
                    'Set CPU target utilization to 70%',
                    'Monitor for CPU throttling',
                    'Consider CPU-optimized node types'
                ];
                break;
            case 'MEMORY_INTENSIVE':
                immediateActions = [
                    'Implement memory-based HPA',
                    'Set memory target utilization to 75%',
                    'Enable memory optimization',
                    'Monitor for OOM kills'
                ];
                break;
            case 'BURSTY':
                immediateActions = [
                    'Implement predictive autoscaling',
                    'Configure scheduled scaling',
                    'Set up custom metrics monitoring',
                    'Enable burst-friendly scaling policies'
                ];
                break;
            case 'BALANCED':
                immediateActions = [
                    'Fine-tune existing HPA policies',
                    'Implement multi-metric scaling',
                    'Optimize scaling thresholds',
                    'Enable advanced scaling behaviors'
                ];
                break;
        }
        
        insights.actions = `🎯 <strong>Immediate Actions for ${workloadType}:</strong> ${immediateActions.slice(0, 3).join(' • ')}. Implement these changes within 48 hours for optimal impact.`;
    }
    
    console.log('✅ Generated comprehensive ML-integrated insights:', Object.keys(insights));
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