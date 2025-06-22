/**
 * ============================================================================
 * AKS COST INTELLIGENCE - MAIN ENTRY POINT
 * ============================================================================
 * This is the main entry point that imports and initializes all modules
 * Replace your original main.js with this structure
 * ============================================================================
 */

// Import all core modules
import { AppConfig, AppState } from './config.js';
import { showNotification } from './notifications.js';
import { initializeDashboard } from './main.js';

// Import all functionality modules (these will self-register their global functions)
import './utils.js';
import './forms.js';
import './cluster-management.js';
import './charts.js';
import './copy-functionality.js';
import './implementation-plan.js';
import './dynamic-insights.js';
import './ui-navigation.js';
import './css-injection.js';
import './progress-animations.js';

/**
 * Main application initialization
 * This replaces the original DOMContentLoaded handler
 */
function initializeApplication() {
    console.log('🚀 Starting AKS Cost Intelligence Dashboard');
    console.log('📦 All modules loaded and ready');
    
    // Show loading notification
    showNotification('🚀 Initializing AKS Cost Intelligence Dashboard...', 'info', 3000);
    
    // Initialize the dashboard (this handles all the setup)
    initializeDashboard();
    
    // Log successful initialization
    setTimeout(() => {
        console.log('✅ AKS Cost Intelligence Dashboard fully initialized');
        console.log('📊 Available functions:', Object.keys(window).filter(key => 
            key.includes('cluster') || 
            key.includes('chart') || 
            key.includes('analysis') || 
            key.includes('implementation')
        ));
    }, 1000);
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