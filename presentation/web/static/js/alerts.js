/**
 * Alerts Module
 * Handles loading and displaying alerts for the cluster
 */

window.Alerts = (function() {
    'use strict';
    
    // Private variables
    let currentAlerts = null;
    let containerId = 'alerts-list';
    
    /**
     * Initialize alerts module
     */
    function init() {
        console.log('Initializing Alerts module...');
    }
    
    /**
     * Load alerts for current cluster
     */
    async function loadAlerts() {
        const container = document.getElementById(containerId);
        
        if (!container) {
            console.error('Alerts container not found:', containerId);
            return;
        }
        
        try {
            showLoadingState();
            const alertsData = await window.API.getAlerts();
            
            if (alertsData && alertsData.status === 'success') {
                currentAlerts = alertsData;
                renderAlerts(alertsData);
            } else {
                showErrorState(alertsData?.message || 'Failed to load alerts');
            }
            
        } catch (error) {
            console.error('Error loading alerts:', error);
            showErrorState(error.message || 'Failed to load alerts');
        }
    }
    
    /**
     * Create new alert
     */
    async function createAlert() {
        showCreateAlertModal();
    }
    
    /**
     * Show create alert modal
     */
    function showCreateAlertModal() {
        const clusterId = window.AppState?.currentClusterId;
        const clusterName = window.AppState?.currentClusterName || 'Current Cluster';
        
        const modal = document.createElement('div');
        modal.className = 'alert-modal-overlay';
        modal.innerHTML = `
            <div class="alert-modal">
                <div class="alert-modal-header">
                    <h3>Create New Alert</h3>
                    <button onclick="this.closest('.alert-modal-overlay').remove()" class="alert-modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="alert-modal-body">
                    <form id="create-alert-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="alert-name">Alert Name *</label>
                                <input type="text" id="alert-name" name="name" required 
                                       placeholder="e.g., High CPU Usage Alert">
                            </div>
                            <div class="form-group">
                                <label for="alert-severity">Severity *</label>
                                <select id="alert-severity" name="severity" required>
                                    <option value="">Select severity</option>
                                    <option value="critical">Critical</option>
                                    <option value="warning">Warning</option>
                                    <option value="info">Info</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="alert-description">Description</label>
                            <textarea id="alert-description" name="description" rows="3"
                                      placeholder="Describe what this alert monitors"></textarea>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="alert-metric">Metric *</label>
                                <select id="alert-metric" name="metric_name" required>
                                    <option value="">Select metric</option>
                                    <option value="cpu_usage">CPU Usage</option>
                                    <option value="memory_usage">Memory Usage</option>
                                    <option value="cost_threshold">Cost Threshold</option>
                                    <option value="node_count">Node Count</option>
                                    <option value="pod_count">Pod Count</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="alert-operator">Condition *</label>
                                <select id="alert-operator" name="operator" required>
                                    <option value="">Select condition</option>
                                    <option value="greater_than">Greater than</option>
                                    <option value="less_than">Less than</option>
                                    <option value="equals">Equals</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="alert-threshold">Threshold *</label>
                                <input type="number" id="alert-threshold" name="threshold_amount" required
                                       placeholder="e.g., 80" step="0.01">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="alert-frequency">Notification Frequency *</label>
                                <select id="alert-frequency" name="notification_frequency" required>
                                    <option value="immediate">Immediate</option>
                                    <option value="hourly">Hourly</option>
                                    <option value="daily" selected>Daily</option>
                                    <option value="weekly">Weekly</option>
                                    <option value="monthly">Monthly</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="alert-email">Email *</label>
                                <input type="email" id="alert-email" name="email" required
                                       placeholder="admin@company.com">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="alert-enabled">
                                <input type="checkbox" id="alert-enabled" name="enabled" checked>
                                Enable this alert immediately
                            </label>
                        </div>
                        
                        <input type="hidden" name="cluster_id" value="${clusterId || ''}">
                        <input type="hidden" name="cluster_name" value="${clusterName}">
                        <input type="hidden" name="resource_group" value="${window.AppState?.currentResourceGroup || ''}">
                        <input type="hidden" name="alert_type" value="cost_threshold">
                    </form>
                </div>
                <div class="alert-modal-footer">
                    <button type="button" onclick="this.closest('.alert-modal-overlay').remove()" class="btn-secondary">
                        Cancel
                    </button>
                    <button type="button" onclick="submitCreateAlert()" class="btn-primary" id="create-alert-btn">
                        <i class="fas fa-plus"></i> Create Alert
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Focus on first input
        setTimeout(() => {
            const firstInput = modal.querySelector('#alert-name');
            if (firstInput) firstInput.focus();
        }, 100);
    }
    
    /**
     * Submit create alert form
     */
    async function submitCreateAlert() {
        const form = document.getElementById('create-alert-form');
        const submitBtn = document.getElementById('create-alert-btn');
        
        if (!form) return;
        
        const formData = new FormData(form);
        const alertData = {};
        
        // Convert form data to object
        for (let [key, value] of formData.entries()) {
            if (key === 'enabled') {
                alertData[key] = true; // checkbox handling
            } else if (key === 'threshold_amount') {
                alertData[key] = parseFloat(value);
            } else {
                alertData[key] = value;
            }
        }
        
        // Ensure checkbox is handled properly - if not checked, it won't be in formData
        if (!formData.has('enabled')) {
            alertData.enabled = false;
        }
        
        // Validate required fields
        const requiredFields = ['name', 'severity', 'metric_name', 'operator', 'threshold_amount', 'email'];
        const missingFields = requiredFields.filter(field => !alertData[field]);
        
        if (missingFields.length > 0) {
            if (window.showToast) {
                window.showToast(`Please fill in: ${missingFields.join(', ')}`, 'warning');
            }
            return;
        }
        
        try {
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
            
            // Debug: Log the data being sent
            console.log('🔍 Alert data being sent to API:', alertData);
            
            // Call API
            const result = await window.API.createAlert(alertData);
            
            if (result && result.status === 'success') {
                if (window.showToast) {
                    window.showToast('Alert created successfully!', 'success');
                }
                
                // Close modal
                const modal = document.querySelector('.alert-modal-overlay');
                if (modal) modal.remove();
                
                // Refresh alerts list
                await loadAlerts();
                
            } else {
                throw new Error(result?.message || 'Failed to create alert');
            }
            
        } catch (error) {
            console.error('Error creating alert:', error);
            if (window.showToast) {
                window.showToast(`Failed to create alert: ${error.message}`, 'error');
            }
        } finally {
            // Reset button
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-plus"></i> Create Alert';
        }
    }
    
    /**
     * Show loading state
     */
    function showLoadingState() {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // Replace the entire content with our styled alerts card
        container.innerHTML = `
            <div class="alerts-card">
                <div class="alerts-header">
                    <h3 class="alerts-title">
                        <i class="fas fa-bell alerts-icon"></i>
                        Active Alerts
                    </h3>
                    <div class="alerts-actions">
                        <button onclick="Alerts.createAlert()" class="alerts-create-btn">
                            <i class="fas fa-plus"></i> New Alert
                        </button>
                    </div>
                </div>
                <div class="alerts-loading">
                    <div class="loading-spinner"></div>
                    <span>Loading alerts...</span>
                </div>
            </div>
        `;
    }
    
    /**
     * Show error state
     */
    function showErrorState(message) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = `
            <div class="alerts-card">
                <div class="alerts-header">
                    <h3 class="alerts-title">
                        <i class="fas fa-bell alerts-icon"></i>
                        Active Alerts
                    </h3>
                    <div class="alerts-actions">
                        <button onclick="Alerts.createAlert()" class="alerts-create-btn">
                            <i class="fas fa-plus"></i> New Alert
                        </button>
                    </div>
                </div>
                <div class="alerts-error">
                    <div class="alerts-error-icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <h4 class="alerts-error-title">Unable to Load Alerts</h4>
                    <p class="alerts-error-message">${message}</p>
                    <div class="alerts-error-actions">
                        <button onclick="Alerts.loadAlerts()" class="btn-secondary">
                            <i class="fas fa-refresh"></i> Retry
                        </button>
                        <button onclick="Alerts.createAlert()" class="btn-primary">
                            <i class="fas fa-plus"></i> Create Alert
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Render alerts
     */
    function renderAlerts(alertsData) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const alerts = alertsData.alerts || [];
        const totalAlerts = alertsData.total_alerts || alerts.length;
        
        if (alerts.length === 0) {
            // Show empty state
            container.innerHTML = `
                <div class="alerts-card">
                    <div class="alerts-header">
                        <h3 class="alerts-title">
                            <i class="fas fa-bell alerts-icon"></i>
                            Active Alerts
                        </h3>
                        <div class="alerts-actions">
                            <span class="alerts-stats">0 active</span>
                            <button onclick="Alerts.createAlert()" class="alerts-create-btn">
                                <i class="fas fa-plus"></i> New Alert
                            </button>
                        </div>
                    </div>
                    <div class="alerts-empty">
                        <div class="alerts-empty-icon">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <h4 class="alerts-empty-title">No Active Alerts</h4>
                        <p class="alerts-empty-description">
                            Your cluster is running smoothly with no active alerts. 
                            You can create custom alerts to monitor specific metrics and conditions.
                        </p>
                        <div class="alerts-empty-actions">
                            <button onclick="Alerts.createAlert()" class="btn-primary">
                                <i class="fas fa-plus"></i> Create Your First Alert
                            </button>
                            <button onclick="Alerts.loadAlerts()" class="btn-secondary">
                                <i class="fas fa-refresh"></i> Refresh
                            </button>
                        </div>
                    </div>
                </div>
            `;
        } else {
            // Show alerts list
            const alertsHtml = alerts.map(alert => {
                const severity = (alert.severity || 'info').toLowerCase();
                const avatarClass = `alert-avatar alert-${severity}`;
                const icon = getAlertIcon(severity);
                const timeFormatted = formatAlertTime(alert.created_at);
                const status = (alert.status || 'active').toLowerCase();
                const isActive = status === 'active';
                const statusLabel = isActive ? 'Active' : 'Paused';
                const statusClass = isActive ? 'alert-status-active' : 'alert-status-paused';
                
                return `
                    <div class="alert-item">
                        <div class="${avatarClass}">
                            <i class="${icon}"></i>
                        </div>
                        <div class="alert-content" onclick="Alerts.showAlertDetails('${alert.id || ''}')">
                            <div class="alert-title">${escapeHtml(alert.title || alert.name || 'Alert')}</div>
                            <div class="alert-description">${escapeHtml(alert.description || alert.message || 'No description available')}</div>
                            <div class="alert-meta">
                                <span class="alert-time">${timeFormatted}</span>
                                <span class="alert-status ${statusClass}">${statusLabel}</span>
                            </div>
                        </div>
                        <div class="alert-actions">
                            <div class="alert-toggle">
                                <label class="toggle-switch">
                                    <input type="checkbox" ${isActive ? 'checked' : ''} 
                                           onchange="Alerts.toggleAlertStatus('${alert.id}', '${status}')"
                                           onclick="event.stopPropagation()">
                                    <span class="toggle-slider"></span>
                                </label>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = `
                <div class="alerts-card">
                    <div class="alerts-header">
                        <h3 class="alerts-title">
                            <i class="fas fa-bell alerts-icon"></i>
                            Active Alerts
                        </h3>
                        <div class="alerts-actions">
                            <span class="alerts-stats">${totalAlerts} active</span>
                            <button onclick="Alerts.createAlert()" class="alerts-create-btn">
                                <i class="fas fa-plus"></i> New Alert
                            </button>
                        </div>
                    </div>
                    <div class="alerts-list">
                        ${alertsHtml}
                    </div>
                </div>
            `;
        }
    }
    
    /**
     * Toggle alert status
     */
    async function toggleAlertStatus(alertId, currentStatus) {
        if (!alertId) return;
        
        try {
            const action = currentStatus === 'active' ? 'pause' : 'resume';
            const result = await window.API.toggleAlert(alertId, action);
            
            if (result && result.status === 'success') {
                if (window.showToast) {
                    const message = action === 'pause' ? 'Alert paused successfully' : 'Alert resumed successfully';
                    window.showToast(message, 'success');
                }
                
                // Refresh alerts list
                await loadAlerts();
            } else {
                throw new Error(result?.message || `Failed to ${action} alert`);
            }
            
        } catch (error) {
            console.error(`Error toggling alert status:`, error);
            if (window.showToast) {
                window.showToast(`Failed to update alert: ${error.message}`, 'error');
            }
        }
    }

    /**
     * Show alert details (placeholder for future enhancement)
     */
    function showAlertDetails(alertId) {
        if (!alertId) return;
        
        console.log('Show alert details for:', alertId);
        
        if (window.showToast) {
            window.showToast('Alert details view coming soon!', 'info');
        }
        
        // TODO: Implement alert details modal/page
    }
    
    /**
     * Get appropriate icon for alert severity
     */
    function getAlertIcon(severity) {
        switch (severity) {
            case 'critical':
            case 'error':
                return 'fas fa-exclamation-triangle';
            case 'warning':
                return 'fas fa-exclamation-circle';
            case 'info':
                return 'fas fa-info-circle';
            case 'success':
                return 'fas fa-check-circle';
            default:
                return 'fas fa-bell';
        }
    }
    
    /**
     * Format alert timestamp for display
     */
    function formatAlertTime(timestamp) {
        if (!timestamp) return '--';
        
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / (1000 * 60));
            const diffHours = Math.floor(diffMins / 60);
            const diffDays = Math.floor(diffHours / 24);
            
            if (diffMins < 1) {
                return 'Just now';
            } else if (diffMins < 60) {
                return `${diffMins}m ago`;
            } else if (diffHours < 24) {
                return `${diffHours}h ago`;
            } else if (diffDays < 7) {
                return `${diffDays}d ago`;
            } else {
                return date.toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric'
                });
            }
        } catch (error) {
            return '--';
        }
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        if (!text) return '';
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Public API
    return {
        init,
        loadAlerts,
        createAlert,
        submitCreateAlert,
        showAlertDetails,
        toggleAlertStatus
    };
})();

// Make functions globally accessible for onclick handlers (following backup pattern)
window.createAlert = function() {
    if (window.Alerts && window.Alerts.createAlert) {
        return window.Alerts.createAlert();
    }
};

window.submitCreateAlert = function() {
    if (window.Alerts && window.Alerts.submitCreateAlert) {
        return window.Alerts.submitCreateAlert();
    }
};