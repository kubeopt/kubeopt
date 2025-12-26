/**
 * AKS Cost Optimizer - Main Application Entry Point
 * Orchestrates initialization of all modules
 */

/**
 * Initialize the application
 */
function initApp() {
    console.log('🚀 Initializing AKS Cost Optimizer...');
    
    try {
        // Initialize cluster context first
        if (window.Utils) {
            window.Utils.initClusterContext();
        }
        
        // Initialize core modules
        if (window.UI) {
            window.UI.init();
            window.UI.initKeyboardShortcuts();
        }
        
        if (window.Dashboard) {
            window.Dashboard.init();
        }
        
        if (window.ChartsModule) {
            console.log('Charts module available');
        }
        
        console.log('✅ Application initialized successfully');
        
    } catch (error) {
        console.error('❌ Error initializing application:', error);
        if (window.UI && window.UI.showToast) {
            window.UI.showToast('Application failed to initialize', 'error');
        }
    }
}

/**
 * Clean up application resources
 */
function cleanup() {
    console.log('🧹 Cleaning up application...');
    
    if (window.Dashboard) {
        window.Dashboard.stopAutoRefresh();
    }
    
    // Destroy all charts
    Object.keys(window.AppState.charts).forEach(chartId => {
        if (window.Utils) {
            window.Utils.destroyChart(chartId);
        }
    });
    
    console.log('✅ Application cleanup complete');
}

/**
 * Handle page visibility changes
 */
function handleVisibilityChange() {
    if (document.hidden) {
        console.log('⏸️ Page hidden, pausing auto-refresh');
        if (window.Dashboard) {
            window.Dashboard.stopAutoRefresh();
        }
    } else {
        console.log('▶️ Page visible, resuming operations');
        if (window.Dashboard) {
            window.Dashboard.refresh();
        }
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', initApp);
document.addEventListener('visibilitychange', handleVisibilityChange);
window.addEventListener('beforeunload', cleanup);

// Global functions for template compatibility

window.toggleTheme = function() {
    if (window.UI) {
        window.UI.toggleTheme();
    }
};

window.generateNewPlan = function() {
    if (window.Dashboard) {
        window.Dashboard.generateNewPlan();
    }
};

window.createAlert = function() {
    if (window.UI) {
        window.UI.showToast('Alert creation modal would open here', 'info');
    }
};

// Export for global access
window.AksApp = {
    init: initApp,
    cleanup: cleanup,
    
    // Module references
    get Dashboard() { return window.Dashboard; },
    get UI() { return window.UI; },
    get API() { return window.API; },
    get Utils() { return window.Utils; },
    get Charts() { return window.ChartsModule; }
};