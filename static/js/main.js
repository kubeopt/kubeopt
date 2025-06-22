/**
 * ============================================================================
 * AKS COST INTELLIGENCE - MAIN INITIALIZATION MODULE
 * ============================================================================
 * Main entry point that imports and initializes all dashboard modules
 * ============================================================================
 */

// Import all modules
import { AppConfig, AppState } from './config.js';
import { showNotification, showProgressNotification } from './notifications.js';
import { setupFormHandlers, setupInputValidation } from './forms.js';
import { testAPIConnectivity } from './utils.js';
import { initializeCharts } from './charts.js';

// Import functions that need to be globally available
import './cluster-management.js';
import './copy-functionality.js';
import './implementation-plan.js';
import './ui-navigation.js';
import './dynamic-insights.js';
import './css-injection.js';

/**
 * Sets up keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (event) => {
        // Ctrl/Cmd + R to refresh charts
        if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
            event.preventDefault();
            if (typeof initializeCharts === 'function') {
                initializeCharts();
                showNotification('Charts refreshed', 'info', 2000);
            }
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) modalInstance.hide();
            });
        }
        
        // Alt + A to open add cluster modal
        if (event.altKey && event.key === 'a') {
            event.preventDefault();
            const addClusterModal = document.getElementById('addClusterModal');
            if (addClusterModal) {
                const modal = new bootstrap.Modal(addClusterModal);
                modal.show();
            }
        }
        
        // Alt + D to switch to dashboard tab
        if (event.altKey && event.key === 'd') {
            event.preventDefault();
            if (typeof switchToTab === 'function') {
                switchToTab('#dashboard');
            }
        }
        
        // Alt + I to switch to implementation tab
        if (event.altKey && event.key === 'i') {
            event.preventDefault();
            if (typeof switchToTab === 'function') {
                switchToTab('#implementation');
            }
        }
    });
    
    console.log('⌨️ Keyboard shortcuts enabled: Ctrl+R (refresh), Esc (close modals), Alt+A (add cluster), Alt+D (dashboard), Alt+I (implementation)');
}

/**
 * Sets up auto-refresh functionality
 */
function setupAutoRefresh() {
    let autoRefreshInterval;
    
    function startAutoRefresh() {
        // Only auto-refresh if dashboard tab is active
        const dashboardTab = document.querySelector('#dashboard');
        if (dashboardTab && dashboardTab.classList.contains('active')) {
            if (typeof initializeCharts === 'function') {
                console.log('🔄 Auto-refreshing charts...');
                initializeCharts();
            }
        }
    }
    
    // Start auto-refresh timer
    autoRefreshInterval = setInterval(startAutoRefresh, AppConfig.CHART_REFRESH_INTERVAL);
    
    // Pause auto-refresh when window is not visible
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            clearInterval(autoRefreshInterval);
            console.log('⏸️ Auto-refresh paused (window hidden)');
        } else {
            autoRefreshInterval = setInterval(startAutoRefresh, AppConfig.CHART_REFRESH_INTERVAL);
            console.log('▶️ Auto-refresh resumed (window visible)');
        }
    });
    
    console.log(`🔄 Auto-refresh enabled (${AppConfig.CHART_REFRESH_INTERVAL / 1000}s interval)`);
}

/**
 * Sets up tab switching handlers
 */
function setupTabHandlers() {
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    
    tabButtons.forEach(button => {
        button.addEventListener('shown.bs.tab', function(event) {
            const tabId = event.target.getAttribute('data-bs-target');
            console.log('📑 Tab switched to:', tabId);
            
            // Handle specific tab activations
            if (tabId === '#dashboard') {
                // Auto-load charts when dashboard tab is shown
                setTimeout(() => {
                    if (typeof initializeCharts === 'function') {
                        initializeCharts();
                    }
                }, 500);
                
            } else if (tabId === '#implementation') {
                // Auto-load implementation plan when implementation tab is shown
                setTimeout(() => {
                    if (typeof loadImplementationPlan === 'function') {
                        loadImplementationPlan();
                    }
                }, 500);
            }
        });
    });
}

/**
 * Sets up error handling
 */
function setupErrorHandling() {
    // Global error handler
    window.addEventListener('error', (event) => {
        console.error('🚨 Global error:', event.error);
        
        // Don't show notifications for minor script errors
        if (event.error && event.error.name !== 'TypeError') {
            showNotification('An unexpected error occurred. Please refresh the page.', 'error');
        }
    });
    
    // Promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
        console.error('🚨 Unhandled promise rejection:', event.reason);
        
        // Don't show notifications for fetch errors (they're handled elsewhere)
        if (!event.reason?.message?.includes('fetch')) {
            showNotification('A network error occurred. Please check your connection.', 'warning');
        }
    });
}

/**
 * Sets up performance monitoring
 */
function setupPerformanceMonitoring() {
    // Track page load time
    window.addEventListener('load', () => {
        const loadTime = performance.now();
        console.log(`⚡ Dashboard loaded in ${Math.round(loadTime)}ms`);
        
        if (loadTime > 3000) {
            console.warn('⚠️ Dashboard took longer than 3 seconds to load');
        }
    });
    
    // Monitor chart initialization time
    const originalInitializeCharts = window.initializeCharts;
    if (originalInitializeCharts) {
        window.initializeCharts = function() {
            const startTime = performance.now();
            const result = originalInitializeCharts.apply(this, arguments);
            const endTime = performance.now();
            console.log(`📊 Charts initialized in ${Math.round(endTime - startTime)}ms`);
            return result;
        };
    }
}

/**
 * Displays welcome message for first-time users
 */
function showWelcomeMessage() {
    const hasSeenWelcome = localStorage.getItem('aks-dashboard-welcome-seen');
    
    if (!hasSeenWelcome) {
        setTimeout(() => {
            showNotification(
                '👋 Welcome to AKS Cost Intelligence! Add your first cluster to get started with cost optimization.',
                'info',
                8000
            );
            localStorage.setItem('aks-dashboard-welcome-seen', 'true');
        }, 2000);
    }
}

/**
 * Main initialization function
 */
async function initializeDashboard() {
    console.log('🚀 Initializing AKS Cost Intelligence Dashboard');
    
    const progress = showProgressNotification([
        'Loading configuration...',
        'Setting up form handlers...',
        'Initializing charts system...',
        'Testing API connectivity...',
        'Setting up user interface...',
        'Finalizing dashboard...'
    ]);
    
    try {
        // Step 1: Configuration loaded (already done by imports)
        progress.updateStep(0);
        
        // Step 2: Setup form handlers
        progress.updateStep(1);
        setupFormHandlers();
        setupInputValidation();
        
        // Step 3: Initialize charts system
        progress.updateStep(2);
        // Charts will be initialized when tabs are switched or manually called
        
        // Step 4: Test API connectivity
        progress.updateStep(3);
        const apiTest = await testAPIConnectivity();
        if (!apiTest.success) {
            showNotification('API connection failed. Some features may not work.', 'warning');
        }
        
        // Step 5: Setup UI components
        progress.updateStep(4);
        setupTabHandlers();
        setupKeyboardShortcuts();
        setupAutoRefresh();
        setupErrorHandling();
        setupPerformanceMonitoring();
        
        // Step 6: Finalize
        progress.updateStep(5);
        
        // Auto-initialize charts if dashboard is active
        const dashboardTab = document.querySelector('#dashboard');
        if (dashboardTab && dashboardTab.classList.contains('active')) {
            setTimeout(() => {
                if (typeof initializeCharts === 'function') {
                    initializeCharts();
                }
            }, 500);
        }
        
        // Auto-load implementation plan if implementation tab is active
        const implementationTab = document.querySelector('#implementation');
        if (implementationTab && implementationTab.classList.contains('active')) {
            setTimeout(() => {
                if (typeof loadImplementationPlan === 'function') {
                    loadImplementationPlan();
                }
            }, 500);
        }
        
        // Complete progress
        progress.complete('Dashboard initialized successfully!');
        
        // Show welcome message for new users
        showWelcomeMessage();
        
        console.log('✅ Dashboard initialization completed successfully');
        
    } catch (error) {
        console.error('❌ Error during initialization:', error);
        progress.dismiss();
        showNotification('Dashboard initialization failed: ' + error.message, 'error');
    }
}

/**
 * Placeholder functions for features coming soon
 */
function showPortfolioAnalytics() {
    showNotification('Portfolio Analytics... Feature coming soon!', 'info');
}

function refreshCharts() {
    showNotification('Refreshing charts...', 'info');
    if (typeof initializeCharts === 'function') {
        initializeCharts();
    }
}

function exportReport() {
    showNotification('Report export coming soon!', 'info');
}

function deployOptimizations() {
    showNotification('Deployment feature coming soon!', 'info');
}

function scheduleOptimization() {
    showNotification('Scheduling feature coming soon!', 'info');
}

// Make functions available globally for HTML onclick handlers
if (typeof window !== 'undefined') {
    // Core functions
    window.initializeDashboard = initializeDashboard;
    window.showPortfolioAnalytics = showPortfolioAnalytics;
    window.refreshCharts = refreshCharts;
    window.exportReport = exportReport;
    window.deployOptimizations = deployOptimizations;
    window.scheduleOptimization = scheduleOptimization;
    
    // Configuration and state
    window.AppState = AppState;
    window.AppConfig = AppConfig;
    
    // Utility functions
    window.showNotification = showNotification;
}

/**
 * Initialize when DOM is ready
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
    initializeDashboard();
}

console.log('✅ AKS Cost Intelligence Dashboard main module loaded');

export { initializeDashboard };