/**
 * ============================================================================
 * AKS COST INTELLIGENCE - MAIN INITIALIZATION MODULE (FIXED)
 * ============================================================================
 * Main entry point that imports and initializes all dashboard modules
 * FIXES: Module loading timeout and implementation plan loading issues
 * ============================================================================
 */

// Import all modules
import { AppConfig, AppState } from './config.js';
import { showNotification, showProgressNotification } from './notifications.js';
import { setupFormHandlers, setupInputValidation } from './forms.js';
import { testAPIConnectivity } from './utils.js';
import { initializeCharts } from './charts.js';
import { loadImplementationPlan } from './implementation-plan.js';

// Import functions that need to be globally available
import './cluster-management.js';
import './copy-functionality.js';
import './ui-navigation.js';
import './dynamic-insights.js';
import './css-injection.js';

/**
 * ✅ FIXED: Ensure functions are available both as imports and globals
 */
function ensureGlobalFunctions() {
    console.log('🔧 Ensuring functions are globally available...');
    
    // Assign imported functions to window for backward compatibility
    if (typeof window !== 'undefined') {
        window.initializeCharts = initializeCharts;
        window.loadImplementationPlan = loadImplementationPlan;
        window.showNotification = showNotification;
        
        // These should be available from other modules
        if (typeof window.switchToTab !== 'function') {
            console.warn('⚠️ switchToTab not found, defining fallback...');
            window.switchToTab = function(selector) {
                console.log('🔄 Fallback switchToTab called for:', selector);
                
                // Simple tab switching logic
                const tabButton = document.querySelector(`[data-bs-target="${selector}"]`);
                if (tabButton) {
                    tabButton.click();
                } else {
                    console.warn('Tab button not found for:', selector);
                }
            };
        }
        
        console.log('✅ Global functions ensured');
    }
}

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
            if (typeof window.switchToTab === 'function') {
                window.switchToTab('#dashboard');
            }
        }
        
        // Alt + I to switch to implementation tab
        if (event.altKey && event.key === 'i') {
            event.preventDefault();
            if (typeof window.switchToTab === 'function') {
                window.switchToTab('#implementation');
            }
        }
    });
    
    console.log('⌨️ Keyboard shortcuts enabled');
}

/**
 * ✅ FIXED: Enhanced tab switching with guaranteed module loading
 */
function setupTabHandlers() {
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    
    tabButtons.forEach(button => {
        button.addEventListener('shown.bs.tab', function(event) {
            const tabId = event.target.getAttribute('data-bs-target');
            console.log('📑 Tab switched to:', tabId);
            
            // Handle specific tab activations
            if (tabId === '#dashboard') {
                setTimeout(() => {
                    console.log('🔄 Dashboard tab - initializing charts...');
                    if (typeof initializeCharts === 'function') {
                        initializeCharts();
                    } else {
                        console.error('❌ initializeCharts function not available');
                    }
                }, 200);
                
            } else if (tabId === '#implementation') {
                console.log('🔄 Implementation tab activated - loading plan...');
                
                setTimeout(() => {
                    console.log('🔄 Attempting to load implementation plan...');
                    
                    // ✅ FIXED: Use the imported function directly first
                    try {
                        if (typeof loadImplementationPlan === 'function') {
                            console.log('✅ Using imported loadImplementationPlan');
                            loadImplementationPlan();
                        } else if (typeof window.loadImplementationPlan === 'function') {
                            console.log('✅ Using window.loadImplementationPlan');
                            window.loadImplementationPlan();
                        } else {
                            console.warn('⚠️ loadImplementationPlan not found, showing fallback');
                            showImplementationFallback();
                        }
                    } catch (error) {
                        console.error('❌ Error loading implementation plan:', error);
                        showImplementationFallback();
                    }
                }, 200);
            }
        });
    });
    
    console.log('✅ Tab handlers setup complete');
}

/**
 * ✅ FIXED: Fallback function if implementation plan fails to load
 */
function showImplementationFallback() {
    const container = document.getElementById('implementation-plan-container');
    if (container) {
        container.innerHTML = `
            <div class="alert alert-warning text-center m-4">
                <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                <h4>Implementation Plan Loading Issue</h4>
                <p>There was an issue loading the implementation plan. This usually happens when:</p>
                <ul class="text-start mt-3">
                    <li>No analysis has been run yet for this cluster</li>
                    <li>The implementation plan API is not responding</li>
                    <li>JavaScript modules are still loading</li>
                </ul>
                <div class="mt-3">
                    <button class="btn btn-primary me-2" onclick="forceLoadImplementationPlan()">
                        <i class="fas fa-redo me-1"></i> Force Reload Plan
                    </button>
                    <button class="btn btn-outline-secondary me-2" onclick="window.switchToTab && window.switchToTab('#analysis')">
                        <i class="fas fa-chart-bar me-1"></i> Run Analysis First
                    </button>
                    <button class="btn btn-outline-info" onclick="window.location.reload()">
                        <i class="fas fa-refresh me-1"></i> Reload Page
                    </button>
                </div>
            </div>
        `;
    }
}

/**
 * ✅ FIXED: Force load implementation plan function
 */
function forceLoadImplementationPlan() {
    console.log('🔄 Force loading implementation plan...');
    showNotification('Force reloading implementation plan...', 'info');
    
    try {
        if (typeof loadImplementationPlan === 'function') {
            console.log('✅ Using imported loadImplementationPlan');
            loadImplementationPlan();
        } else if (typeof window.loadImplementationPlan === 'function') {
            console.log('✅ Using window.loadImplementationPlan');
            window.loadImplementationPlan();
        } else {
            console.error('❌ loadImplementationPlan not available');
            showNotification('Implementation plan function not available. Please reload the page.', 'error');
        }
    } catch (error) {
        console.error('❌ Error in forceLoadImplementationPlan:', error);
        showNotification('Failed to load implementation plan: ' + error.message, 'error');
    }
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
 * Displays welcome message for first-time users
 */
function showWelcomeMessage() {
    // Check if localStorage is available
    try {
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
    } catch (error) {
        console.warn('⚠️ localStorage not available for welcome message');
    }
}

/**
 * ✅ FIXED: Initialize content based on current active tab
 */
function initializeActiveTabContent() {
    const activeTab = document.querySelector('.tab-pane.active');
    if (activeTab) {
        const tabId = '#' + activeTab.id;
        console.log(`🎯 Active tab detected: ${tabId}`);
        
        if (tabId === '#dashboard') {
            setTimeout(() => {
                console.log('🔄 Auto-initializing charts for active dashboard tab...');
                if (typeof initializeCharts === 'function') {
                    initializeCharts();
                } else {
                    console.warn('⚠️ initializeCharts not available');
                }
            }, 500);
        } else if (tabId === '#implementation') {
            setTimeout(() => {
                console.log('🔄 Auto-loading implementation plan for active tab...');
                if (typeof loadImplementationPlan === 'function') {
                    loadImplementationPlan();
                } else {
                    console.warn('⚠️ loadImplementationPlan not available');
                    showImplementationFallback();
                }
            }, 500);
        }
    }
}

/**
 * ✅ FIXED: Main initialization function without module loading timeout
 */
async function initializeDashboard() {
    console.log('🚀 Initializing AKS Cost Intelligence Dashboard (FIXED VERSION)');
    
    const progress = showProgressNotification([
        'Loading configuration...',
        'Setting up global functions...',
        'Setting up form handlers...',
        'Testing API connectivity...',
        'Setting up user interface...',
        'Initializing tab content...',
        'Finalizing dashboard...'
    ]);
    
    try {
        // Step 1: Configuration loaded (already done by imports)
        progress.updateStep(0);
        
        // Step 2: ✅ FIXED: Ensure global functions are available immediately
        progress.updateStep(1);
        ensureGlobalFunctions();
        
        // Step 3: Setup form handlers
        progress.updateStep(2);
        setupFormHandlers();
        setupInputValidation();
        
        // Step 4: Test API connectivity (don't wait for it)
        progress.updateStep(3);
        testAPIConnectivity().then(apiTest => {
            if (!apiTest.success) {
                showNotification('API connection failed. Some features may not work.', 'warning');
            }
        }).catch(error => {
            console.warn('API test failed:', error);
        });
        
        // Step 5: Setup UI components
        progress.updateStep(4);
        setupTabHandlers();
        setupKeyboardShortcuts();
        setupErrorHandling();
        
        // Step 6: ✅ FIXED: Initialize content based on current active tab
        progress.updateStep(5);
        initializeActiveTabContent();
        
        // Step 7: Finalize
        progress.updateStep(6);
        
        // Complete progress
        progress.complete('Dashboard initialized successfully!');
        
        // Show welcome message for new users
        showWelcomeMessage();
        
        console.log('✅ Dashboard initialization completed successfully (FIXED VERSION)');
        
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

// ✅ FIXED: Make functions available globally for HTML onclick handlers
if (typeof window !== 'undefined') {
    // Core functions
    window.initializeDashboard = initializeDashboard;
    window.showPortfolioAnalytics = showPortfolioAnalytics;
    window.refreshCharts = refreshCharts;
    window.exportReport = exportReport;
    window.deployOptimizations = deployOptimizations;
    window.scheduleOptimization = scheduleOptimization;
    
    // ✅ FIXED: Implementation plan functions
    window.forceLoadImplementationPlan = forceLoadImplementationPlan;
    window.showImplementationFallback = showImplementationFallback;
    
    // Configuration and state
    window.AppState = AppState;
    window.AppConfig = AppConfig;
    
    // Utility functions
    window.showNotification = showNotification;
}

/**
 * ✅ FIXED: Initialize when DOM is ready
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('📄 DOM loaded, initializing dashboard...');
        initializeDashboard();
    });
} else {
    console.log('📄 DOM already ready, initializing dashboard immediately...');
    initializeDashboard();
}

console.log('✅ AKS Cost Intelligence Dashboard main module loaded (FIXED VERSION)');

export { initializeDashboard };