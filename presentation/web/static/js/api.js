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
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error(`API request failed for ${endpoint}:`, error);
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
    async function getAlerts() {
        return await request('/api/alerts');
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
        
        // Notifications methods
        getNotifications,
        markNotificationRead,
        
        // System methods
        clearCache,
        testAzureConnection,
        getSystemStatus
    };
})();