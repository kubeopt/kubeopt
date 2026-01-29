/**
 * AKS Cost Optimizer - Main Application Entry Point
 * Orchestrates initialization of all modules
 */

/**
 * Initialize the application
 */
function initApp() {
    window.logger.info('🚀 Initializing AKS Cost Optimizer...');
    
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
            window.logger.debug('Charts module available');
        }
        
        if (window.ImplementationPlan) {
            window.ImplementationPlan.init();
            window.logger.debug('Implementation plan module initialized');
        }
        
        if (window.Alerts) {
            window.Alerts.init();
            window.logger.debug('Alerts module initialized');
        }
        
        window.logger.info('✅ Application initialized successfully');
        
        // Start global auto-refresh for all pages
        window.startGlobalAutoRefresh();
        
    } catch (error) {
        window.logger.error('❌ Error initializing application:', error);
        if (window.UI && window.UI.showToast) {
            window.UI.showToast('Application failed to initialize', 'error');
        }
    }
}

/**
 * Clean up application resources
 */
function cleanup() {
    window.logger.debug('🧹 Cleaning up application...');
    
    // Stop global auto-refresh
    window.stopGlobalAutoRefresh();
    
    if (window.Dashboard) {
        window.Dashboard.stopAutoRefresh();
    }
    
    // Destroy all charts
    if (window.AppState && window.AppState.charts) {
        Object.keys(window.AppState.charts).forEach(chartId => {
            if (window.Utils) {
                window.Utils.destroyChart(chartId);
            }
        });
    }
    
    window.logger.debug('✅ Application cleanup complete');
}

/**
 * Handle page visibility changes
 */
function handleVisibilityChange() {
    if (document.hidden) {
        window.logger.debug('⏸️ Page hidden, pausing auto-refresh');
        if (window.Dashboard) {
            window.Dashboard.stopAutoRefresh();
        }
    } else {
        window.logger.debug('▶️ Page visible, resuming operations');
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

// Enhanced refresh everything function - works on all pages
window.refreshEverything = async function(silent = false) {
    const originalText = document.title;
    if (!silent) document.title = "🔄 Refreshing...";
    
    try {
        const promises = [];
        
        // Cluster Portfolio page
        if (window.ClusterPortfolio?.loadPortfolioStats) promises.push(window.ClusterPortfolio.loadPortfolioStats());
        
        // Alerts (all pages)
        if (window.Alerts?.loadAlerts) promises.push(window.Alerts.loadAlerts());
        
        // Dashboard page
        if (window.Dashboard?.refresh) promises.push(window.Dashboard.refresh());
        
        // Chart Manager (all pages with charts)
        if (window.ChartsModule?.refreshAll) promises.push(window.ChartsModule.refreshAll());
        
        // Settings page - reload current settings
        if (window.location.pathname === '/settings' && window.Settings?.loadCurrentSettings) {
            promises.push(window.Settings.loadCurrentSettings());
        }
        
        // Individual cluster page
        if (window.location.pathname.includes('/cluster/') && window.ClusterDetails?.refresh) {
            promises.push(window.ClusterDetails.refresh());
        }
        
        await Promise.all(promises);
        
        if (!silent && window.showToast) {
            window.showToast('✅ Page refreshed successfully', 'success');
        }
        
        window.logger.debug('🔄 Auto-refresh completed');
        
    } catch (error) {
        window.logger.error('Refresh failed:', error);
        if (!silent && window.showToast) {
            window.showToast('❌ Refresh failed', 'error');
        }
    } finally {
        document.title = originalText;
    }
};

// Global auto-refresh for all pages
window.startGlobalAutoRefresh = function() {
    // Don't start if already running
    if (window.globalAutoRefreshInterval) return;
    
    window.globalAutoRefreshInterval = setInterval(() => {
        window.refreshEverything(true); // silent = true for auto-refresh
    }, 300000); // Every 5 minutes
    
    window.logger.info('🔄 Global auto-refresh started (every 5 minutes)');
};

window.stopGlobalAutoRefresh = function() {
    if (window.globalAutoRefreshInterval) {
        clearInterval(window.globalAutoRefreshInterval);
        window.globalAutoRefreshInterval = null;
        window.logger.debug('⏹️ Global auto-refresh stopped');
    }
};


// createAlert function is now handled by the Alerts module

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