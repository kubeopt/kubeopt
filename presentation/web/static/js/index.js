/**
 * ============================================================================
 * AKS COST INTELLIGENCE - MAIN ENTRY POINT (FIXED)
 * ============================================================================
 * This is the main entry point that imports and initializes all modules
 * Fixed import order and circular dependency issues
 * ============================================================================
 */

// Import core configuration first
import { AppConfig, AppState } from './config.js';
import { showNotification } from './notifications.js';

// Import utility modules (no dependencies)
import './utils.js';
import './copy-functionality.js';

// Import feature modules (may depend on utils)
import './forms.js';
import './cluster-management.js';
import './charts.js';
import './ui-navigation.js';
import './css-injection.js';
import './progress-animations.js';
import './dynamic-insights.js';
// import './implementation-plan.js';

// Import main dashboard LAST (after all dependencies are loaded)
import { initializeDashboard } from './main.js';

/**
 * Main application initialization
 * This replaces the original DOMContentLoaded handler
 */
function initializeApplication() {
    console.log('🚀 Starting AKS Cost Intelligence Dashboard');
    console.log('📦 All modules loaded and ready');
    
    try {
        // Show loading notification
        showNotification('🚀 Initializing AKS Cost Intelligence Dashboard...', 'info', 3000);
        
        // ✅ Verify cluster isolation is working
        if (typeof window.validateClusterContext === 'function') {
            console.log('✅ Cluster isolation functions available');
            const clusterId = window.getCurrentClusterId();
            console.log(`🎯 Current cluster: ${clusterId}`);
        } else {
            console.log('⚠️ Cluster isolation functions not found');
        }
        
        // Initialize the dashboard (this handles all the setup)
        initializeDashboard();
        
        // Log successful initialization
        setTimeout(() => {
            console.log('✅ AKS Cost Intelligence Dashboard fully initialized');
            
            // Show available functions for debugging
            const availableFunctions = Object.keys(window).filter(key => 
                key.includes('cluster') || 
                key.includes('chart') || 
                key.includes('analysis') || 
                key.includes('implementation') ||
                key.includes('load') ||
                key.includes('refresh')
            );
            
            if (availableFunctions.length === 0) {
                console.log('⚠️ No global functions found - check module exports');
            }
        }, 1000);
        
    } catch (error) {
        console.error('❌ Application initialization failed:', error);
        showNotification('❌ Dashboard initialization failed: ' + error.message, 'error');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApplication);
} else {
    initializeApplication();
}

// Export for module systems
export { 
    AppConfig, 
    AppState, 
    initializeApplication,
    showNotification 
};

console.log('🎯 AKS Cost Intelligence - All modules loaded successfully');