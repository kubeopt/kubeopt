/**
 * AKS Cost Optimizer - API Module
 * Handles all API communication and data fetching
 */

window.API = (function() {
    'use strict';
    
    // Private variables
    const baseURL = '';
    const defaultHeaders = {
        'Content-Type': 'application/json'
    };

    /**
     * Make API request with cluster context
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Request options
     * @returns {Promise} Response data
     */
    async function request(endpoint, options = {}) {
        const clusterId = window.AppState?.currentClusterId;
        
        // Add cluster context to headers if available
        const headers = {
            ...defaultHeaders,
            ...options.headers
        };
        
        if (clusterId) {
            headers['X-Cluster-ID'] = clusterId;
        }
        
        const config = {
            method: 'GET',
            ...options,
            headers
        };
        
        try {
            const response = await fetch(baseURL + endpoint, config);
            
            if (!response.ok) {
                // Try to get error details from response body
                let errorMessage = `${response.status}: ${response.statusText}`;
                try {
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        const errorData = await response.json();
                        errorMessage = errorData.message || errorData.error || errorMessage;
                        window.logger.error('Backend error details:', errorData);
                    } else {
                        const textError = await response.text();
                        if (textError) {
                            errorMessage = textError;
                        }
                    }
                } catch (parseError) {
                    window.logger.error('Could not parse error response:', parseError);
                }
                throw new Error(`HTTP ${response.status}: ${errorMessage}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            window.logger.error(`API request failed for ${endpoint}:`, error);
            if (window.showToast) {
                window.showToast(`Request failed: ${error.message}`, 'error');
            }
            throw error;
        }
    }

    /**
     * Get cluster data
     */
    async function getClusterData(clusterId) {
        return await request(`/api/clusters/${clusterId}`);
    }

    /**
     * Get chart data for dashboard
     */
    async function getChartData(clusterId) {
        return await request(`/api/chart-data?cluster_id=${clusterId}`);
    }

    /**
     * Get dashboard overview data
     */
    async function getDashboardOverview(clusterId) {
        return await request(`/api/dashboard/overview?cluster_id=${clusterId}`);
    }

    /**
     * Get portfolio summary
     */
    async function getPortfolioSummary() {
        return await request('/api/portfolio/summary');
    }

    /**
     * Get implementation plan
     */
    async function getImplementationPlan(clusterId) {
        return await request(`/api/clusters/${clusterId}/plan`);
    }

    /**
     * Generate new implementation plan
     */
    async function generateImplementationPlan(clusterId) {
        return await request(`/api/clusters/${clusterId}/plan/generate`, {
            method: 'POST'
        });
    }

    /**
     * Get alerts data
     */
    async function getAlerts(clusterId) {
        const url = clusterId 
            ? `/api/alerts?cluster_id=${encodeURIComponent(clusterId)}`
            : '/api/alerts';
        return await request(url);
    }

    /**
     * Create new alert
     */
    async function createAlert(alertData) {
        return await request('/api/alerts', {
            method: 'POST',
            body: JSON.stringify(alertData)
        });
    }

    /**
     * Toggle alert status (pause/resume)
     */
    async function toggleAlert(alertId, action) {
        return await request(`/api/alerts/${alertId}/pause`, {
            method: 'POST',
            body: JSON.stringify({ action })
        });
    }

    /**
     * Update alert
     */
    async function updateAlert(alertId, alertData) {
        return await request(`/api/alerts/${alertId}`, {
            method: 'PUT',
            body: JSON.stringify(alertData)
        });
    }

    /**
     * Delete alert
     */
    async function deleteAlert(alertId) {
        return await request(`/api/alerts/${alertId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Get notifications
     */
    async function getNotifications() {
        return await request('/api/notifications/in-app');
    }

    /**
     * Mark notification as read
     */
    async function markNotificationRead(notificationId) {
        return await request(`/api/notifications/${notificationId}/mark-read`, {
            method: 'POST'
        });
    }

    /**
     * Clear cache
     */
    async function clearCache() {
        return await request('/api/cache/clear', {
            method: 'POST'
        });
    }

    /**
     * Test Azure connection
     */
    async function testAzureConnection() {
        return await request('/api/test_azure', {
            method: 'POST'
        });
    }

    /**
     * Get system status
     */
    async function getSystemStatus() {
        return await request('/api/system_status');
    }

    // Public API
    return {
        // Core API methods
        request,
        
        // Cluster methods
        getClusterData,
        getChartData,
        getDashboardOverview,
        
        // Portfolio methods
        getPortfolioSummary,
        
        // Implementation plan methods
        getImplementationPlan,
        generateImplementationPlan,
        
        // Alerts methods
        getAlerts,
        createAlert,
        updateAlert,
        toggleAlert,
        deleteAlert,
        
        // Notifications methods
        getNotifications,
        markNotificationRead,
        
        // System methods
        clearCache,
        testAzureConnection,
        getSystemStatus
    };
})();