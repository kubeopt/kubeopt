/**
 * IMPLEMENTATION PLAN MAIN - Entry Point and Initialization
 * Loads all modules and initializes the implementation plan system
 */

import { loadImplementationPlan, displayImplementationPlan } from './plan-core.js';
import { injectCompleteUI } from './plan-ui.js';
import { setPlanDataCache } from './plan-interactions.js';
import { showCopyNotification } from './plan-utils.js';

// Initialize the implementation plan system
function initializeImplementationPlan() {
    console.log('🚀 Initializing Implementation Plan System...');
    
    // Set up event listener for when plan data is ready
    if (typeof window !== 'undefined') {
        window.addEventListener('implementationPlanDataReady', (event) => {
            const { planData } = event.detail;
            console.log('📊 Plan data received, injecting UI...');
            
            // Set cache for interactions module
            setPlanDataCache(planData);
            
            // Inject the UI
            injectCompleteUI(planData);
        });
        
        // Make core functions globally available
        window.loadImplementationPlan = loadImplementationPlan;
        window.displayImplementationPlan = displayImplementationPlan;
        window.showCopyNotification = showCopyNotification;
        
        console.log('✅ Implementation Plan System Ready');
        console.log('📋 Core functions:', {
            loadImplementationPlan: typeof window.loadImplementationPlan,
            displayImplementationPlan: typeof window.displayImplementationPlan
        });
    }
}

// Auto-initialize when module loads
initializeImplementationPlan();

// Export for manual initialization if needed
export { initializeImplementationPlan };