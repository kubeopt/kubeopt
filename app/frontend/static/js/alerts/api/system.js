// frontend/static/js/alerts/api/system.js

import { API_ENDPOINTS } from '../core/config.js';

/**
 * API functions for system status and configuration
 */

/**
 * Check alerts system status
 */
export async function checkSystemStatus() {
    const response = await fetch(API_ENDPOINTS.systemStatus);
    
    if (!response.ok) {
        throw new Error(`System status check failed: ${response.status}`);
    }
    
    return response.json();
}

/**
 * Check email and notification channel configurations
 */
export async function checkNotificationChannels() {
    const response = await fetch(API_ENDPOINTS.emailConfig);
    
    if (!response.ok) {
        throw new Error(`Email config check failed: ${response.status}`);
    }
    
    return response.json();
}

/**
 * Load frequency configurations
 */
export async function fetchFrequencyConfigurations() {
    try {
        const response = await fetch(API_ENDPOINTS.frequencyConfigs);
        
        if (!response.ok) {
            throw new Error(`Failed to load frequency configs: ${response.status}`);
        }
        
        return response.json();
    } catch (error) {
        // Return default configurations if endpoint doesn't exist
        throw new Error(`Frequency configs endpoint not available: ${error.message}`);
    }
}

/**
 * Check alerts system health (with notification channels info)
 */
export async function checkAlertsHealth() {
    try {
        const response = await fetch('/api/alerts/health');
        
        if (!response.ok) {
            throw new Error(`Health check failed: ${response.status}`);
        }
        
        return response.json();
    } catch (error) {
        // Return basic health info if endpoint doesn't exist
        return {
            health: {
                notification_channels: {
                    in_app: false
                }
            }
        };
    }
}