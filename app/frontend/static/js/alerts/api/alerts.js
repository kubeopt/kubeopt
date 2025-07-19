// frontend/static/js/alerts/api/alerts.js

import { API_ENDPOINTS } from '../core/config.js';

/**
 * API functions for alert management
 */

/**
 * Fetch all alerts
 */
export async function fetchAlerts(clusterId = null) {
    const url = clusterId 
        ? `${API_ENDPOINTS.alerts}?cluster_id=${encodeURIComponent(clusterId)}` 
        : API_ENDPOINTS.alerts;
    
    const response = await fetch(url);
    
    if (!response.ok) {
        if (response.status === 503) {
            throw new Error('Alerts system is currently unavailable');
        }
        throw new Error(`Request failed: ${response.status}`);
    }
    
    return response.json();
}

/**
 * Create a new alert
 */
export async function createAlert(alertData) {
    const response = await fetch(API_ENDPOINTS.alerts, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(alertData)
    });
    
    if (!response.ok) {
        if (response.status === 503) {
            throw new Error('Alerts system is currently unavailable');
        }
        throw new Error(`Request failed: ${response.status}`);
    }
    
    return response.json();
}

/**
 * Update an existing alert
 */
export async function updateAlert(alertId, updates) {
    const response = await fetch(`${API_ENDPOINTS.alerts}/${alertId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
    });
    
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    
    return response.json();
}

/**
 * Delete an alert
 */
export async function deleteAlert(alertId) {
    const response = await fetch(`${API_ENDPOINTS.alerts}/${alertId}`, {
        method: 'DELETE'
    });
    
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    
    return response.json();
}

/**
 * Test an alert
 */
export async function testAlert(alertId) {
    const response = await fetch(`${API_ENDPOINTS.alerts}/${alertId}/test`, {
        method: 'POST'
    });
    
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    
    return response.json();
}

/**
 * Pause or resume an alert
 */
export async function pauseResumeAlert(alertId, action) {
    const response = await fetch(`${API_ENDPOINTS.alerts}/${alertId}/pause`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action })
    });
    
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    
    return response.json();
}

/**
 * Fetch alert triggers/history
 */
export async function fetchAlertTriggers() {
    const response = await fetch(API_ENDPOINTS.alertTriggers);
    
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    
    return response.json();
}

/**
 * Test alert trigger for a cluster
 */
export async function testAlertTrigger(clusterId, testCost) {
    const response = await fetch(`${API_ENDPOINTS.alerts}/test-trigger/${clusterId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            test_cost: parseFloat(testCost)
        })
    });
    
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    
    return response.json();
}