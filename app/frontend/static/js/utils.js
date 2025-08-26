/**
 * ============================================================================
 * AKS COST INTELLIGENCE - UTILITY FUNCTIONS
 * ============================================================================
 * Common utility functions for formatting, validation, and general helpers
 * ============================================================================
 */

/**
 * Formats numeric values based on specified format type
 */
export function formatValue(value, format) {
    const num = parseFloat(value) || 0;
    if (isNaN(num)) {
        console.warn('⚠️ Invalid number for formatting:', value);
        return '0';
    }
    
    switch(format) {
        case 'currency':
            return '$' + Math.round(num).toLocaleString();
        case 'currency-monthly':
            return '$' + Math.round(num).toLocaleString() + '/mo';
        case 'percentage':
            return num.toFixed(1) + '%';
        case 'number':
            return Math.round(num).toString();
        default:
            return Math.round(num).toLocaleString();
    }
}

/**
 * Gets chart color scheme based on current theme
 */
export function getChartColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        textColor: '#f7fafc',
        gridColor: '#e2e8f0',
        backgroundColor: '#ffffff'
    };
}

/**
 * Calculates optimization score based on metrics
 */
export function calculateOptimizationScore(metrics) {
    const savingsPercentage = metrics.savings_percentage || 0;
    const hpaReduction = metrics.hpa_reduction || 0;
    const cpuGap = metrics.cpu_gap || 0;
    const memoryGap = metrics.memory_gap || 0;
    
    const savingsScore = Math.min(100, savingsPercentage * 2);
    const efficiencyScore = Math.min(100, hpaReduction * 1.5);
    const utilizationScore = Math.max(0, 100 - (cpuGap + memoryGap) / 2);
    
    return Math.round(savingsScore * 0.4 + efficiencyScore * 0.3 + utilizationScore * 0.3);
}

/**
 * Debounce function to limit API calls
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Escapes HTML characters to prevent XSS
 */
export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Gets accuracy badge class for pod analysis
 */
export function getAccuracyBadgeClass(accuracy) {
    switch (accuracy?.toLowerCase()) {
        case 'very high': return 'bg-success';
        case 'high': return 'bg-info';
        case 'good': return 'bg-warning';
        case 'basic': return 'bg-secondary';
        default: return 'bg-secondary';
    }
}

/**
 * Helper function to get priority color
 */
export function getPriorityColor(priority) {
    switch (priority?.toLowerCase()) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'success';
        default: return 'secondary';
    }
}

/**
 * Helper function to get risk color
 */
export function getRiskColor(risk) {
    switch (risk?.toLowerCase()) {
        case 'high': return 'danger';
        case 'medium': return 'warning';  
        case 'low': return 'success';
        default: return 'secondary';
    }
}

/**
 * Get cluster name from current context
 */
export function getClusterNameFromContext() {
    // Try to get from URL
    const urlPath = window.location.pathname;
    const clusterMatch = urlPath.match(/\/cluster\/([^\/]+)/);
    if (clusterMatch) {
        return clusterMatch[1];
    }
    
    // Try to get from page title or heading
    const heading = document.querySelector('h2, h4');
    if (heading && heading.textContent.includes('Analysis')) {
        const parts = heading.textContent.split(' ');
        return parts[0] || 'cluster';
    }
    
    return 'current-cluster';
}

/**
 * Get appropriate icon for insight type
 */
export function getInsightIcon(type) {
    const icons = {
        'rightsizing': 'expand-arrows-alt',
        'storage': 'hdd',
        'overall': 'chart-line',
        'cost': 'dollar-sign',
        'hpa': 'rocket'
    };
    return icons[type] || 'lightbulb';
}

/**
 * Tests API connectivity
 */
export function testAPIConnectivity() {
    const API_BASE_URL = '/api'; // Import from config if needed
    
    return fetch(`${API_BASE_URL}/clusters`)
        .then(response => response.json())
        .then(data => {
            console.log('✅ API connectivity test passed');
            if (data.clusters?.length > 0) {
                console.log(`📊 Found ${data.clusters.length} existing clusters`);
            }
            return { success: true, data };
        })
        .catch(error => {
            console.error('❌ API connectivity test failed:', error);
            return { success: false, error };
        });
}

/**
 * Validates form inputs with custom rules
 */
export function validateInput(value, rules = {}) {
    const errors = [];
    
    if (rules.required && (!value || value.trim() === '')) {
        errors.push('This field is required');
    }
    
    if (rules.minLength && value && value.length < rules.minLength) {
        errors.push(`Must be at least ${rules.minLength} characters`);
    }
    
    if (rules.maxLength && value && value.length > rules.maxLength) {
        errors.push(`Must be no more than ${rules.maxLength} characters`);
    }
    
    if (rules.pattern && value && !rules.pattern.test(value)) {
        errors.push(rules.patternMessage || 'Invalid format');
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
}

/**
 * Generates a unique ID
 */
export function generateId(prefix = 'id') {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Deep clone an object
 */
export function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }
    
    if (obj instanceof Date) {
        return new Date(obj.getTime());
    }
    
    if (obj instanceof Array) {
        return obj.map(item => deepClone(item));
    }
    
    if (typeof obj === 'object') {
        const cloned = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                cloned[key] = deepClone(obj[key]);
            }
        }
        return cloned;
    }
}

/**
 * Throttle function to limit function calls
 */
export function throttle(func, delay) {
    let timeoutId;
    let lastExecTime = 0;
    
    return function (...args) {
        const currentTime = Date.now();
        
        if (currentTime - lastExecTime > delay) {
            func.apply(this, args);
            lastExecTime = currentTime;
        } else {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
                lastExecTime = Date.now();
            }, delay - (currentTime - lastExecTime));
        }
    };
}