/**
 * ============================================================================
 * AKS COST INTELLIGENCE - DASHBOARD MANAGEMENT
 * ============================================================================
 * Dashboard-specific functions, polling, and cluster state management
 * ============================================================================
 */

import { getCurrentClusterId, validateClusterContext, makeClusterAwareAPICall } from './charts.js';
import { refreshImplementationPlan } from './implementation-plan.js';
import { showNotification } from './notifications.js';

/**
 * Dashboard initialization with cluster isolation
 */
export function initializeDashboard() {
    const clusterId = getCurrentClusterId();
    
    if (!clusterId) {
        console.error('❌ CRITICAL: Cannot initialize dashboard without cluster ID!');
        // Redirect to cluster portfolio
        window.location.href = '/clusters';
        return;
    }
    
    console.log(`🎯 Initializing dashboard for cluster: ${clusterId}`);
    
    // Clear any old timers that might reference other clusters
    if (window.dashboardTimers) {
        window.dashboardTimers.forEach(timer => clearInterval(timer));
        window.dashboardTimers = [];
    }
    
    // Initialize with cluster-specific data
    if (typeof window.initializeCharts === 'function') {
        window.initializeCharts();
    }
    
    if (typeof window.loadImplementationPlan === 'function') {
        window.loadImplementationPlan();
    }
    
    // Set up cluster-specific polling
    setupDashboardPolling();
    
    // Validate page state
    validatePageState();
}

/**
 * Setup cluster-specific polling to prevent cross-contamination
 */
export function setupDashboardPolling() {
    const clusterId = getCurrentClusterId();
    
    if (!clusterId) {
        console.error('❌ Cannot setup polling without cluster ID');
        return;
    }
    
    console.log(`🔄 Setting up polling for cluster: ${clusterId}`);
    
    // Clear any existing timers
    if (window.dashboardTimers) {
        window.dashboardTimers.forEach(timer => clearInterval(timer));
        window.dashboardTimers = [];
    }
    
    // Poll cache status every 30 seconds for THIS cluster only
    const cacheTimer = setInterval(() => {
        const currentClusterId = getCurrentClusterId();
        if (currentClusterId === clusterId) {
            makeClusterAwareAPICall('/api/cache/status')
                .then(response => response.json())
                .then(data => {
                    console.log('✅ Cache status for current cluster:', data);
                    updateCacheStatusIndicator(data);
                })
                .catch(error => {
                    console.error('Cache status error:', error);
                });
        } else {
            console.log(`🛑 Stopping polling for ${clusterId} - cluster changed to ${currentClusterId}`);
            clearInterval(cacheTimer);
        }
    }, 30000);
    
    // Store timer for cleanup
    if (!window.dashboardTimers) {
        window.dashboardTimers = [];
    }
    window.dashboardTimers.push(cacheTimer);
}

/**
 * Validate page state to prevent data contamination
 */
export function validatePageState() {
    const clusterId = getCurrentClusterId();
    
    if (!clusterId) {
        console.error('❌ Page state validation failed - no cluster ID');
        return false;
    }
    
    // Check for stale data indicators
    const dataElements = document.querySelectorAll('[data-cluster-id]');
    dataElements.forEach(element => {
        const elementClusterId = element.getAttribute('data-cluster-id');
        if (elementClusterId && elementClusterId !== clusterId) {
            console.warn(`⚠️ Found stale data element with cluster ID: ${elementClusterId}`);
            element.style.opacity = '0.5';
            element.title = 'Stale data detected - refreshing...';
        }
    });
    
    // Validate URL matches expected cluster
    const expectedUrl = `/cluster/${clusterId}`;
    if (!window.location.pathname.startsWith(expectedUrl)) {
        console.error(`❌ URL mismatch: expected ${expectedUrl}, got ${window.location.pathname}`);
        return false;
    }
    
    console.log(`✅ Page state validated for cluster: ${clusterId}`);
    return true;
}

/**
 * Update cache status indicator
 */
function updateCacheStatusIndicator(cacheData) {
    const indicator = document.getElementById('cache-status-indicator');
    if (indicator && cacheData.cache_status) {
        const status = cacheData.cache_status;
        const isValid = status.cache_valid;
        
        indicator.className = `badge ${isValid ? 'bg-success' : 'bg-warning'}`;
        indicator.textContent = isValid ? 'Cache Valid' : 'Cache Stale';
        indicator.title = `Last updated: ${status.cache_timestamp || 'Unknown'}`;
    }
}

/**
 * Enhanced cluster refresh with validation
 */
export function refreshCurrentCluster() {
    if (!validateClusterContext('refreshCurrentCluster')) {
        console.error('❌ BLOCKED: refreshCurrentCluster - invalid cluster context');
        return;
    }
    
    const clusterId = getCurrentClusterId();
    console.log(`🔄 Refreshing data for cluster: ${clusterId}`);
    
    // Clear cache for current cluster
    makeClusterAwareAPICall('/api/cache/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cluster_id: clusterId })
    }).then(() => {
        console.log(`🧹 Cleared cache for cluster: ${clusterId}`);
        
        // Refresh all components
        if (typeof window.initializeCharts === 'function') {
            window.initializeCharts();
        }
        
        if (typeof refreshImplementationPlan === 'function') {
            refreshImplementationPlan();
        }
        
        showNotification(`Data refreshed for cluster: ${clusterId}`, 'success');
        
    }).catch(error => {
        console.error('Cache clear error:', error);
        showNotification(`Failed to refresh cluster data: ${error.message}`, 'error');
    });
}

/**
 * Analysis completion handler with cluster validation
 */
export function handleAnalysisCompletion() {
    if (!validateClusterContext('handleAnalysisCompletion')) {
        console.error('❌ BLOCKED: handleAnalysisCompletion - invalid cluster context');
        return;
    }
    
    const clusterId = getCurrentClusterId();
    console.log(`🎉 Analysis completed for cluster: ${clusterId}`);
    
    // Refresh dashboard components
    setTimeout(() => {
        if (typeof window.initializeCharts === 'function') {
            window.initializeCharts();
        }
        
        if (typeof refreshImplementationPlan === 'function') {
            refreshImplementationPlan();
        }
    }, 1000);
}

/**
 * Handle page visibility changes to prevent background contamination
 */
export function handleVisibilityChange() {
    if (document.hidden) {
        console.log('📱 Page hidden - pausing cluster polling');
        
        // Pause timers when page is hidden
        if (window.dashboardTimers) {
            window.dashboardTimers.forEach(timer => {
                timer.paused = true;
                clearInterval(timer);
            });
        }
    } else {
        console.log('📱 Page visible - resuming cluster polling');
        
        // Resume polling when page becomes visible
        const clusterId = getCurrentClusterId();
        if (clusterId) {
            setupDashboardPolling();
            
            // Validate we're still on the correct cluster
            if (!validatePageState()) {
                console.warn('⚠️ Page state invalid after visibility change - refreshing');
                window.location.reload();
            }
        }
    }
}

/**
 * Cleanup function for page unload
 */
export function cleanupDashboard() {
    console.log('🧹 Cleaning up dashboard timers and state');
    
    // Clear all timers
    if (window.dashboardTimers) {
        window.dashboardTimers.forEach(timer => clearInterval(timer));
        window.dashboardTimers = [];
    }
    
    // Clear cluster state
    if (window.currentClusterState) {
        window.currentClusterState.validated = false;
    }
}

/**
 * Debug function to check current state
 */
export function debugClusterState() {
    const clusterId = getCurrentClusterId();
    const state = window.currentClusterState;
    
    console.log('🔍 Current cluster state:', {
        urlClusterId: clusterId,
        stateClusterId: state?.clusterId,
        validated: state?.validated,
        lastUpdated: state?.lastUpdated,
        activeTimers: window.dashboardTimers?.length || 0,
        currentUrl: window.location.href
    });
    
    return {
        clusterId,
        state,
        valid: validateClusterContext('debug')
    };
}

// Event listeners
document.addEventListener('visibilitychange', handleVisibilityChange);
window.addEventListener('beforeunload', cleanupDashboard);

// Global functions for backward compatibility
if (typeof window !== 'undefined') {
    window.initializeDashboard = initializeDashboard;
    window.setupDashboardPolling = setupDashboardPolling;
    window.refreshCurrentCluster = refreshCurrentCluster;
    window.handleAnalysisCompletion = handleAnalysisCompletion;
    window.debugClusterState = debugClusterState;
    window.validatePageState = validatePageState;
}

console.log('✅ Dashboard management module loaded');