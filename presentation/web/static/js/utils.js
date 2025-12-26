/**
 * AKS Cost Optimizer - Utility Functions  
 * Core utilities for the application
 */

// Initialize global AppState immediately
window.AppState = {
    currentClusterId: null,
    currentClusterName: null,
    isLoading: false,
    charts: {},
    theme: 'light'
};

/**
 * Validate that a value is not null or undefined
 */
function validateNotNull(value, name) {
    if (value === null || value === undefined) {
        throw new Error(`${name} is required but was null or undefined`);
    }
    return value;
}

/**
 * Validate DOM element exists
 */
function validateElement(selector) {
    const element = document.querySelector(selector);
    if (!element) {
        throw new Error(`Required DOM element not found: ${selector}`);
    }
    return element;
}

/**
 * Set cluster context for the application
 */
window.setClusterContext = function(clusterInfo) {
    if (!clusterInfo) {
        console.warn('Cannot set cluster context: no cluster info provided');
        return false;
    }
    validateNotNull(clusterInfo.id, 'clusterInfo.id');
    
    window.AppState.currentClusterId = clusterInfo.id;
    window.AppState.currentClusterName = clusterInfo.name || clusterInfo.id;
    console.log(`Cluster context set: ${clusterInfo.id}`);
    return true;
};

/**
 * Get cluster info from global window object or URL
 */
window.getClusterInfo = function() {
    // Try to get from global window object first (set by template)
    if (window.clusterInfo) {
        return window.clusterInfo;
    }
    
    // Try to extract from URL
    const path = window.location.pathname;
    const match = path.match(/\/clusters?\/([^\/]+)/);
    if (match) {
        return { id: match[1], name: match[1] };
    }
    
    // Return null if no cluster info available (not on a cluster-specific page)
    return null;
};

/**
 * Initialize cluster context from template data
 */
window.initClusterContext = function() {
    const clusterInfo = window.getClusterInfo();
    if (clusterInfo) {
        window.setClusterContext(clusterInfo);
        console.log('Cluster context initialized:', clusterInfo);
        return true;
    }
    console.log('No cluster context available (not on cluster page)');
    return false;
};

/**
 * Show toast notification
 */
window.showToast = function(message, type = 'info', duration = 5000) {
    validateNotNull(message, 'message');
    
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" class="toast-close">&times;</button>
    `;
    
    // Add toast styles if not already present
    if (!document.querySelector('#toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            .toast {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 16px;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                font-weight: 500;
                box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                z-index: 1000;
                display: flex;
                align-items: center;
                gap: 12px;
                max-width: 400px;
                animation: slideIn 0.3s ease;
            }
            .toast-info { background: #3b82f6; }
            .toast-success { background: #10b981; }
            .toast-warning { background: #f59e0b; }
            .toast-error { background: #ef4444; }
            .toast-close {
                background: none;
                border: none;
                color: white;
                font-size: 16px;
                cursor: pointer;
                padding: 0;
                margin-left: auto;
            }
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Add to page
    document.body.appendChild(toast);
    
    // Auto remove
    if (duration > 0) {
        setTimeout(() => toast.remove(), duration);
    }
};

/**
 * Format number with appropriate units
 */
window.formatNumber = function(value, decimals = 1) {
    const num = parseFloat(value);
    if (isNaN(num)) {
        throw new Error(`Invalid number for formatting: ${value}`);
    }
    
    if (num >= 1000000) {
        return (num / 1000000).toFixed(decimals) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(decimals) + 'K';
    } else {
        return num.toFixed(decimals);
    }
};

/**
 * Format currency with appropriate symbol
 */
window.formatCurrency = function(value, currency = 'USD') {
    const num = parseFloat(value);
    if (isNaN(num)) {
        throw new Error(`Invalid number for currency formatting: ${value}`);
    }
    
    const formatter = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    
    return formatter.format(num);
};

/**
 * Format percentage
 */
window.formatPercentage = function(value, decimals = 1) {
    const num = parseFloat(value);
    if (isNaN(num)) {
        throw new Error(`Invalid number for percentage formatting: ${value}`);
    }
    
    return `${num.toFixed(decimals)}%`;
};

/**
 * Format value based on type
 */
window.formatValue = function(value, format) {
    const num = parseFloat(value);
    if (isNaN(num)) {
        throw new Error(`Invalid number for formatting: ${value}`);
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
};

/**
 * Debounce function calls
 */
window.debounce = function(func, wait) {
    validateNotNull(func, 'func');
    validateNotNull(wait, 'wait');
    
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

/**
 * Destroy Chart.js instance
 */
window.destroyChart = function(chartId) {
    validateNotNull(chartId, 'chartId');
    
    if (window.AppState.charts[chartId]) {
        window.AppState.charts[chartId].destroy();
        delete window.AppState.charts[chartId];
        console.log(`Chart destroyed: ${chartId}`);
    }
};

/**
 * Create Chart.js instance with validation
 */
window.createChart = function(canvasId, config) {
    validateNotNull(canvasId, 'canvasId');
    validateNotNull(config, 'config');
    
    // Destroy existing chart if present
    window.destroyChart(canvasId);
    
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        throw new Error(`Canvas element not found: ${canvasId}`);
    }
    
    const ctx = canvas.getContext('2d');
    if (!ctx) {
        throw new Error(`Failed to get 2D context for canvas: ${canvasId}`);
    }
    
    const chart = new Chart(ctx, config);
    window.AppState.charts[canvasId] = chart;
    console.log(`Chart created: ${canvasId}`);
    return chart;
};

/**
 * Toggle sidebar - Removed to avoid conflicts, now handled by UI module
 */

/**
 * Make API request with proper error handling
 */
window.apiRequest = async function(endpoint, options = {}) {
    validateNotNull(endpoint, 'endpoint');
    
    const config = {
        method: options.method || 'GET',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    
    // Add cluster context if available
    const clusterId = window.AppState.currentClusterId;
    if (clusterId) {
        config.headers['X-Cluster-ID'] = clusterId;
    }
    
    // Add body if provided
    if (options.body) {
        config.body = typeof options.body === 'string' 
            ? options.body 
            : JSON.stringify(options.body);
    }
    
    try {
        const response = await fetch(endpoint, config);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return await response.text();
        }
    } catch (error) {
        console.error(`API request failed for ${endpoint}:`, error);
        window.showToast(`Request failed: ${error.message}`, 'error');
        throw error;
    }
};

/**
 * Initialize utilities module
 */
window.initUtils = function() {
    console.log('Utilities initialized');
    
    // Set up global error handling for unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        window.showToast('An unexpected error occurred', 'error');
    });
    
    // Initialize cluster context if available
    window.initClusterContext();
};

// Create Utils namespace for compatibility
window.Utils = {
    formatValue: window.formatValue,
    formatNumber: window.formatNumber,
    formatCurrency: window.formatCurrency,
    formatPercentage: window.formatPercentage,
    showToast: window.showToast,
    createChart: window.createChart,
    destroyChart: window.destroyChart,
    debounce: window.debounce,
    setClusterContext: window.setClusterContext,
    getClusterInfo: window.getClusterInfo,
    initClusterContext: window.initClusterContext,
    apiRequest: window.apiRequest
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', window.initUtils);
} else {
    window.initUtils();
}