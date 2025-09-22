/**
 * ============================================================================
 * AKS COST INTELLIGENCE - CONFIGURATION & STATE MANAGEMENT
 * ============================================================================
 * Author: Srinivas Kondepudi
 * ============================================================================
 */

// ============================================================================
// GLOBAL CONFIGURATION
// ============================================================================

export const AppConfig = {
    API_BASE_URL: '/api',
    CHART_REFRESH_INTERVAL: 30000,
    NOTIFICATION_DURATION: 5000,
    MIN_VALIDATION_LENGTH: 3,
    TRANSITION_DURATION: 300,
    SMOOTH_SCROLL_DURATION: 600
};

// ============================================================================
// APPLICATION STATE
// ============================================================================

export const AppState = {
    chartInstances: {},
    analysisCompleted: false,
    currentAnalysis: null,
    alerts: [],
    deployments: [],
    notifications: [],
    autoAnalysis: {
        active: {},
        pollingIntervals: {},
        statusCache: {}
    },
    smoothTransitions: {
        isTransitioning: false,
        currentTab: null,
        implementationLoaded: false
    }
};

// ============================================================================
// STATE MANAGEMENT FUNCTIONS
// ============================================================================

/**
 * Updates application state
 */
export function updateAppState(path, value) {
    const keys = path.split('.');
    let current = AppState;
    
    for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) {
            current[keys[i]] = {};
        }
        current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
}

/**
 * Gets application state value
 */
export function getAppState(path) {
    const keys = path.split('.');
    let current = AppState;
    
    for (const key of keys) {
        if (current === null || current === undefined) {
            return undefined;
        }
        current = current[key];
    }
    
    return current;
}

/**
 * Resets application state to initial values
 */
export function resetAppState() {
    AppState.chartInstances = {};
    AppState.analysisCompleted = false;
    AppState.currentAnalysis = null;
    AppState.alerts = [];
    AppState.deployments = [];
    AppState.notifications = [];
    AppState.autoAnalysis = {
        active: {},
        pollingIntervals: {},
        statusCache: {}
    };
    AppState.smoothTransitions = {
        isTransitioning: false,
        currentTab: null,
        implementationLoaded: false
    };
}

// Make state available globally for backward compatibility
if (typeof window !== 'undefined') {
    window.AppState = AppState;
    window.AppConfig = AppConfig;
}