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
            
            // Get current cluster ID for cluster-specific alerts
            const clusterId = getCurrentClusterId();
            console.log('Loading alerts for cluster:', clusterId);
            
            const alertsData = await window.API.getAlerts(clusterId);
            
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
     * Get current cluster ID from various sources
     */
    function getCurrentClusterId() {
        // Method 1: From URL pattern /cluster/{cluster_id}
        const urlPath = window.location.pathname;
        const clusterMatch = urlPath.match(/\/cluster\/([^\/]+)/);
        
        if (clusterMatch) {
            return clusterMatch[1];
        }
        
        // Method 2: From global window objects
        if (window.AppState && window.AppState.currentClusterId) {
            return window.AppState.currentClusterId;
        }
        
        if (window.clusterInfo && window.clusterInfo.id) {
            return window.clusterInfo.id;
        }
        
        return null;
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
                            <div class="alert-menu-container">
                                <button class="alert-menu-trigger" onclick="toggleAlertMenu('${alert.id}'); event.stopPropagation();">
                                    <i class="fas fa-ellipsis-v"></i>
                                </button>
                                <div class="alert-menu" id="alert-menu-${alert.id}" style="display: none;">
                                    <button class="alert-menu-item" onclick="editAlert('${alert.id}'); closeAlertMenu('${alert.id}');">
                                        <i class="fas fa-edit"></i> Edit Alert
                                    </button>
                                    <button class="alert-menu-item delete-item" onclick="deleteAlert('${alert.id}'); closeAlertMenu('${alert.id}');">
                                        <i class="fas fa-trash"></i> Delete
                                    </button>
                                </div>
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
     * Toggle alert menu
     */
    function toggleAlertMenu(alertId) {
        if (!alertId) return;
        
        // Close all other menus first
        const allMenus = document.querySelectorAll('.alert-menu');
        allMenus.forEach(menu => {
            if (menu.id !== `alert-menu-${alertId}`) {
                menu.style.display = 'none';
            }
        });
        
        // Toggle the specific menu
        const menu = document.getElementById(`alert-menu-${alertId}`);
        if (menu) {
            menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        }
    }
    
    /**
     * Close alert menu
     */
    function closeAlertMenu(alertId) {
        if (!alertId) return;
        
        const menu = document.getElementById(`alert-menu-${alertId}`);
        if (menu) {
            menu.style.display = 'none';
        }
    }
    
    /**
     * Close all alert menus
     */
    function closeAllAlertMenus() {
        const allMenus = document.querySelectorAll('.alert-menu');
        allMenus.forEach(menu => {
            menu.style.display = 'none';
        });
    }
    
    /**
     * Edit alert
     */
    async function editAlert(alertId) {
        if (!alertId) return;
        
        console.log('Edit alert:', alertId);
        
        try {
            console.log('🔍 Debug edit alert:');
            console.log('- Looking for alertId:', alertId, typeof alertId);
            console.log('- Current cached alerts:', currentAlerts);
            
            // Use cached alerts instead of refetching
            if (!currentAlerts || !currentAlerts.alerts) {
                console.log('No cached alerts, refetching...');
                const clusterId = getCurrentClusterId();
                currentAlerts = await window.API.getAlerts(clusterId);
            }
            
            const alerts = currentAlerts.alerts || [];
            console.log('- Available alerts:', alerts.map(a => ({id: a.id, type: typeof a.id})));
            
            // Try flexible comparison to handle type mismatches
            const currentAlert = alerts.find(alert => {
                console.log(`Comparing alert.id: ${alert.id} (${typeof alert.id}) with alertId: ${alertId} (${typeof alertId})`);
                return alert.id == alertId; // Use loose equality to handle string/number differences
            });
            
            if (!currentAlert) {
                console.error('❌ Alert not found with ID:', alertId);
                console.error('Available alert IDs:', alerts.map(a => a.id));
                if (window.showToast) {
                    window.showToast(`Alert not found (ID: ${alertId})`, 'error');
                }
                return;
            }
            
            console.log('✅ Found alert:', currentAlert);
            
            // Show modal with pre-populated data
            showEditAlertModal(currentAlert);
            
        } catch (error) {
            console.error('Error loading alert for editing:', error);
            if (window.showToast) {
                window.showToast('Failed to load alert data', 'error');
            }
        }
    }
    
    /**
     * Show edit alert modal with pre-populated data
     */
    function showEditAlertModal(alertData) {
        const clusterId = window.AppState?.currentClusterId;
        const clusterName = window.AppState?.currentClusterName || 'Current Cluster';
        
        const modal = document.createElement('div');
        modal.className = 'alert-modal-overlay';
        modal.innerHTML = `
            <div class="alert-modal">
                <div class="alert-modal-header">
                    <h3>Edit Alert</h3>
                    <button onclick="this.closest('.alert-modal-overlay').remove()" class="alert-modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="alert-modal-body">
                    <form id="edit-alert-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="edit-alert-name">Alert Name *</label>
                                <input type="text" id="edit-alert-name" name="name" required 
                                       value="${alertData.name || ''}"
                                       placeholder="e.g., High CPU Usage Alert">
                            </div>
                            <div class="form-group">
                                <label for="edit-alert-severity">Severity *</label>
                                <select id="edit-alert-severity" name="severity" required>
                                    <option value="">Select severity</option>
                                    <option value="critical" ${alertData.severity === 'critical' ? 'selected' : ''}>Critical</option>
                                    <option value="warning" ${alertData.severity === 'warning' ? 'selected' : ''}>Warning</option>
                                    <option value="info" ${alertData.severity === 'info' ? 'selected' : ''}>Info</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-alert-description">Description</label>
                            <textarea id="edit-alert-description" name="description" rows="3"
                                      placeholder="Describe what this alert monitors">${alertData.description || ''}</textarea>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="edit-alert-metric">Metric *</label>
                                <select id="edit-alert-metric" name="metric_name" required>
                                    <option value="">Select metric</option>
                                    <option value="cpu_usage" ${alertData.metric_name === 'cpu_usage' ? 'selected' : ''}>CPU Usage</option>
                                    <option value="memory_usage" ${alertData.metric_name === 'memory_usage' ? 'selected' : ''}>Memory Usage</option>
                                    <option value="cost_threshold" ${alertData.metric_name === 'cost_threshold' ? 'selected' : ''}>Cost Threshold</option>
                                    <option value="node_count" ${alertData.metric_name === 'node_count' ? 'selected' : ''}>Node Count</option>
                                    <option value="pod_count" ${alertData.metric_name === 'pod_count' ? 'selected' : ''}>Pod Count</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="edit-alert-operator">Condition *</label>
                                <select id="edit-alert-operator" name="operator" required>
                                    <option value="">Select condition</option>
                                    <option value="greater_than" ${alertData.operator === 'greater_than' ? 'selected' : ''}>Greater than</option>
                                    <option value="less_than" ${alertData.operator === 'less_than' ? 'selected' : ''}>Less than</option>
                                    <option value="equals" ${alertData.operator === 'equals' ? 'selected' : ''}>Equals</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="edit-alert-threshold">Threshold *</label>
                                <input type="number" id="edit-alert-threshold" name="threshold_amount" required
                                       value="${alertData.threshold_amount || ''}"
                                       placeholder="e.g., 80" step="0.01">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="edit-alert-frequency">Notification Frequency *</label>
                                <select id="edit-alert-frequency" name="notification_frequency" required>
                                    <option value="immediate" ${alertData.notification_frequency === 'immediate' ? 'selected' : ''}>Immediate</option>
                                    <option value="hourly" ${alertData.notification_frequency === 'hourly' ? 'selected' : ''}>Hourly</option>
                                    <option value="daily" ${alertData.notification_frequency === 'daily' ? 'selected' : ''}>Daily</option>
                                    <option value="weekly" ${alertData.notification_frequency === 'weekly' ? 'selected' : ''}>Weekly</option>
                                    <option value="monthly" ${alertData.notification_frequency === 'monthly' ? 'selected' : ''}>Monthly</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="edit-alert-email">Email *</label>
                                <input type="email" id="edit-alert-email" name="email" required
                                       value="${alertData.email || ''}"
                                       placeholder="admin@company.com">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-alert-enabled">
                                <input type="checkbox" id="edit-alert-enabled" name="enabled" ${alertData.enabled ? 'checked' : ''}>
                                Enable this alert
                            </label>
                        </div>
                        
                        <input type="hidden" name="cluster_id" value="${clusterId || ''}">
                        <input type="hidden" name="cluster_name" value="${clusterName}">
                        <input type="hidden" name="alert_id" value="${alertData.id}">
                    </form>
                </div>
                <div class="alert-modal-footer">
                    <button type="button" onclick="this.closest('.alert-modal-overlay').remove()" class="alert-modal-btn alert-modal-btn-secondary">
                        Cancel
                    </button>
                    <button type="submit" onclick="submitEditAlert(event)" class="alert-modal-btn alert-modal-btn-primary">
                        <i class="fas fa-save"></i>
                        Update Alert
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Focus on the name field
        const nameField = document.getElementById('edit-alert-name');
        if (nameField) {
            nameField.focus();
        }
    }
    
    /**
     * Submit edit alert form
     */
    async function submitEditAlert(event) {
        event?.preventDefault();
        
        const form = document.getElementById('edit-alert-form');
        const submitBtn = event?.target;
        
        if (!form) return;
        
        // Set button loading state
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating Alert...';
        }
        
        try {
            const formData = new FormData(form);
            const alertId = formData.get('alert_id');
            
            if (!alertId) {
                throw new Error('Alert ID is missing');
            }
            
            // Convert FormData to regular object
            const alertData = {};
            for (let [key, value] of formData.entries()) {
                if (key === 'enabled') {
                    alertData[key] = document.getElementById('edit-alert-enabled')?.checked || false;
                } else if (key !== 'alert_id') {  // Don't include alert_id in the update data
                    alertData[key] = value;
                }
            }
            
            console.log('🔍 Alert data being sent to API for update:', alertData);
            
            // Call API to update alert
            const result = await window.API.updateAlert(alertId, alertData);
            
            if (result && (result.status === 'success' || result.success)) {
                if (window.showToast) {
                    window.showToast('Alert updated successfully!', 'success');
                }
                
                // Close modal
                const modal = document.querySelector('.alert-modal-overlay');
                if (modal) modal.remove();
                
                // Refresh alerts list
                await loadAlerts();
                
            } else {
                throw new Error(result?.message || 'Failed to update alert');
            }
            
        } catch (error) {
            console.error('Error updating alert:', error);
            if (window.showToast) {
                window.showToast(`Failed to update alert: ${error.message}`, 'error');
            }
        } finally {
            // Reset button
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Update Alert';
            }
        }
    }
    
    /**
     * Delete alert
     */
    async function deleteAlert(alertId) {
        if (!alertId) return;
        
        // Find the alert data using flexible comparison
        const alert = currentAlerts?.alerts?.find(a => a.id == alertId);
        if (!alert) {
            console.error('Alert not found for deletion:', alertId);
            console.log('Available alerts:', currentAlerts?.alerts?.map(a => ({id: a.id, type: typeof a.id})));
            if (window.showToast) {
                window.showToast('Alert not found', 'error');
            }
            return;
        }
        
        // Show confirmation modal
        showDeleteAlertModal(alertId, alert);
    }
    
    /**
     * Show delete alert confirmation modal
     */
    function showDeleteAlertModal(alertId, alert) {
        const modal = document.createElement('div');
        modal.className = 'alert-modal-overlay';
        modal.innerHTML = `
            <div class="alert-modal delete-modal">
                <div class="alert-modal-header">
                    <h3>Delete Alert</h3>
                    <button onclick="this.closest('.alert-modal-overlay').remove()" class="alert-modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="alert-modal-body">
                    <div class="delete-warning">
                        <div class="warning-icon">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <h4>Are you sure?</h4>
                        <p>
                            Are you sure you want to delete this alert? This action cannot be undone.
                        </p>
                        <div class="alert-name-display">
                            Alert: <strong>${escapeHtml(alert.name || alert.title || 'Unknown Alert')}</strong>
                        </div>
                    </div>
                </div>
                <div class="alert-modal-footer">
                    <button type="button" onclick="this.closest('.alert-modal-overlay').remove()" class="alert-modal-btn alert-modal-btn-secondary">
                        Cancel
                    </button>
                    <button type="button" onclick="confirmDeleteAlert('${alertId}')" class="alert-modal-btn alert-modal-btn-danger" id="delete-alert-btn">
                        <i class="fas fa-trash"></i> Delete Alert
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    /**
     * Confirm delete alert
     */
    async function confirmDeleteAlert(alertId) {
        if (!alertId) return;
        
        const deleteBtn = document.getElementById('delete-alert-btn');
        
        try {
            // Show loading state
            deleteBtn.disabled = true;
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
            
            // Call API to delete alert
            const result = await window.API.deleteAlert(alertId);
            
            if (result && result.status === 'success') {
                if (window.showToast) {
                    window.showToast('Alert deleted successfully!', 'success');
                }
                
                // Close modal
                const modal = document.querySelector('.alert-modal-overlay');
                if (modal) modal.remove();
                
                // Refresh alerts list
                await loadAlerts();
                
            } else {
                throw new Error(result?.message || 'Failed to delete alert');
            }
            
        } catch (error) {
            console.error('Error deleting alert:', error);
            if (window.showToast) {
                window.showToast(`Failed to delete alert: ${error.message}`, 'error');
            }
        } finally {
            // Reset button
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Delete Alert';
        }
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
        submitEditAlert,
        showAlertDetails,
        toggleAlertStatus,
        toggleAlertMenu,
        closeAlertMenu,
        closeAllAlertMenus,
        editAlert,
        deleteAlert,
        confirmDeleteAlert
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

window.submitEditAlert = function(event) {
    if (window.Alerts && window.Alerts.submitEditAlert) {
        return window.Alerts.submitEditAlert(event);
    }
};

window.toggleAlertMenu = function(alertId) {
    if (window.Alerts && window.Alerts.toggleAlertMenu) {
        return window.Alerts.toggleAlertMenu(alertId);
    }
};

window.closeAlertMenu = function(alertId) {
    if (window.Alerts && window.Alerts.closeAlertMenu) {
        return window.Alerts.closeAlertMenu(alertId);
    }
};

window.editAlert = function(alertId) {
    if (window.Alerts && window.Alerts.editAlert) {
        return window.Alerts.editAlert(alertId);
    }
};

window.deleteAlert = function(alertId) {
    if (window.Alerts && window.Alerts.deleteAlert) {
        return window.Alerts.deleteAlert(alertId);
    }
};

window.confirmDeleteAlert = function(alertId) {
    if (window.Alerts && window.Alerts.confirmDeleteAlert) {
        return window.Alerts.confirmDeleteAlert(alertId);
    }
};

// Add global click listener to close menus when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('.alert-menu-container') && window.Alerts && window.Alerts.closeAllAlertMenus) {
        window.Alerts.closeAllAlertMenus();
    }
});