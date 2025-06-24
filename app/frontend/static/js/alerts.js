/**
 * ============================================================================
 * FIXED ALERTS MANAGEMENT - FRONTEND WITH ERROR HANDLING
 * ============================================================================
 * Enhanced version with proper error handling and fallback behavior
 * ============================================================================
 */

// Global alerts state
const AlertsState = {
    alerts: [],
    loading: false,
    currentClusterId: null,
    emailConfigured: false,
    systemAvailable: true,
    lastError: null
};

/**
 * Initialize alerts system with enhanced error handling
 */
function initializeAlertsSystem() {
    console.log('🔔 Initializing enhanced alerts system...');
    
    // First check if alerts system is available
    checkAlertsSystemStatus()
        .then(() => {
            if (AlertsState.systemAvailable) {
                // Check email configuration
                checkEmailConfiguration();
                
                // Load existing alerts
                loadAlerts();
                
                // Setup event listeners
                setupAlertsEventListeners();
                
                // Check if we're on a cluster-specific page
                const urlPath = window.location.pathname;
                const clusterMatch = urlPath.match(/\/cluster\/([^\/]+)/);
                if (clusterMatch) {
                    AlertsState.currentClusterId = clusterMatch[1];
                    loadClusterAlerts(AlertsState.currentClusterId);
                }
                
                console.log('✅ Alerts system initialized successfully');
            } else {
                console.warn('⚠️ Alerts system not available - showing fallback UI');
                showAlertsUnavailableMessage();
            }
        })
        .catch(error => {
            console.error('❌ Failed to initialize alerts system:', error);
            AlertsState.systemAvailable = false;
            showAlertsUnavailableMessage();
        });
}

/**
 * Check if alerts system is available
 */
function checkAlertsSystemStatus() {
    return fetch('/api/alerts/system-status')
        .then(response => {
            if (!response.ok) {
                throw new Error(`System status check failed: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                AlertsState.systemAvailable = data.alerts_available && data.alerts_manager_initialized;
                AlertsState.emailConfigured = data.email_configured;
                
                console.log('📊 Alerts system status:', {
                    available: AlertsState.systemAvailable,
                    emailConfigured: AlertsState.emailConfigured,
                    managerType: data.alerts_manager_type
                });
                
                return true;
            } else {
                throw new Error(data.message || 'System status check failed');
            }
        })
        .catch(error => {
            console.warn('⚠️ Alerts system status check failed:', error);
            AlertsState.systemAvailable = false;
            throw error;
        });
}

/**
 * Show message when alerts system is unavailable
 */
function showAlertsUnavailableMessage() {
    const containers = [
        document.getElementById('alerts-list-container'),
        document.querySelector('.email-config-status')
    ];
    
    containers.forEach(container => {
        if (container) {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <h6><i class="fas fa-exclamation-triangle me-2"></i>Alerts System Unavailable</h6>
                    <p class="mb-2">The alerts system is not currently available. This may be due to:</p>
                    <ul class="mb-2">
                        <li>Alerts manager not properly initialized</li>
                        <li>Database connection issues</li>
                        <li>Service configuration problems</li>
                    </ul>
                    <p class="mb-0">
                        <small class="text-muted">
                            Contact your administrator or check the server logs for more information.
                        </small>
                    </p>
                </div>
            `;
        }
    });
    
    // Disable form submissions
    const forms = document.querySelectorAll('#budget-alert-form, #advanced-alerts-form');
    forms.forEach(form => {
        if (form) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Service Unavailable';
            }
        }
    });
}

/**
 * Check email configuration status with error handling
 */
function checkEmailConfiguration() {
    if (!AlertsState.systemAvailable) return;
    
    fetch('/api/alerts/email-config')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Email config check failed: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                AlertsState.emailConfigured = data.email_configured;
                updateEmailConfigStatus(data.email_configured);
            } else {
                throw new Error(data.message || 'Email config check failed');
            }
        })
        .catch(error => {
            console.error('❌ Error checking email config:', error);
            updateEmailConfigStatus(false, error.message);
        });
}

/**
 * Update email configuration status in UI with error handling
 */
function updateEmailConfigStatus(configured, errorMessage = null) {
    const statusElements = document.querySelectorAll('.email-config-status');
    statusElements.forEach(element => {
        if (errorMessage) {
            element.innerHTML = `<i class="fas fa-exclamation-triangle text-warning me-1"></i>Email configuration check failed: ${errorMessage}`;
            element.className = 'email-config-status text-warning small';
        } else if (configured) {
            element.innerHTML = '<i class="fas fa-check-circle text-success me-1"></i>Email notifications enabled';
            element.className = 'email-config-status text-success small';
        } else {
            element.innerHTML = '<i class="fas fa-exclamation-triangle text-warning me-1"></i>Email not configured - alerts will be logged only';
            element.className = 'email-config-status text-warning small';
        }
    });
}

/**
 * Setup event listeners for alerts with error handling
 */
function setupAlertsEventListeners() {
    // Budget alert form submission
    const budgetForm = document.getElementById('budget-alert-form');
    if (budgetForm) {
        budgetForm.addEventListener('submit', handleBudgetAlertSubmission);
    }
    
    // Advanced alerts form if exists
    const advancedForm = document.getElementById('advanced-alerts-form');
    if (advancedForm) {
        advancedForm.addEventListener('submit', handleAdvancedAlertSubmission);
    }
    
    // Alert list interactions
    document.addEventListener('click', function(event) {
        if (!AlertsState.systemAvailable) {
            if (event.target.closest('.test-alert-btn, .pause-alert-btn, .delete-alert-btn')) {
                showNotification('Alerts system is currently unavailable', 'warning');
                event.preventDefault();
                return;
            }
        }
        
        if (event.target.closest('.test-alert-btn')) {
            const alertId = event.target.closest('.test-alert-btn').dataset.alertId;
            testAlert(alertId);
        }
        
        if (event.target.closest('.pause-alert-btn')) {
            const alertId = event.target.closest('.pause-alert-btn').dataset.alertId;
            const action = event.target.closest('.pause-alert-btn').dataset.action || 'pause';
            pauseResumeAlert(alertId, action);
        }
        
        if (event.target.closest('.delete-alert-btn')) {
            const alertId = event.target.closest('.delete-alert-btn').dataset.alertId;
            deleteAlert(alertId);
        }
    });
}

/**
 * Handle budget alert form submission with enhanced error handling
 */
function handleBudgetAlertSubmission(event) {
    event.preventDefault();
    
    if (!AlertsState.systemAvailable) {
        showNotification('Alerts system is currently unavailable', 'error');
        return;
    }
    
    const formData = new FormData(event.target);
    const budgetAmount = parseFloat(formData.get('budget_amount') || formData.get('threshold_amount'));
    const alertEmail = formData.get('alert_email') || formData.get('email');
    const alertThreshold = parseFloat(formData.get('alert_threshold') || formData.get('threshold_percentage'));
    
    // Validation
    if (!budgetAmount || budgetAmount <= 0) {
        showNotification('Please enter a valid budget amount', 'error');
        return;
    }
    
    if (!alertEmail || !isValidEmail(alertEmail)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }
    
    const alertData = {
        name: `Budget Alert - $${budgetAmount.toLocaleString()}`,
        alert_type: 'cost_threshold',
        threshold_amount: budgetAmount,
        threshold_percentage: alertThreshold,
        email: alertEmail,
        notification_frequency: 'immediate',
        cluster_id: AlertsState.currentClusterId
    };
    
    // Show loading state
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Setting up alert...';
    submitBtn.disabled = true;
    
    createAlert(alertData)
        .then(result => {
            if (result.status === 'success') {
                showNotification('Budget alert created successfully!', 'success');
                event.target.reset();
                loadAlerts(); // Refresh alerts list
            } else {
                throw new Error(result.message || 'Failed to create alert');
            }
        })
        .catch(error => {
            console.error('❌ Error creating budget alert:', error);
            showNotification(`Failed to create alert: ${error.message}`, 'error');
        })
        .finally(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
}

/**
 * Create a new alert with enhanced error handling
 */
function createAlert(alertData) {
    return fetch('/api/alerts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(alertData)
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 503) {
                throw new Error('Alerts system is currently unavailable');
            }
            throw new Error(`Request failed: ${response.status}`);
        }
        return response.json();
    })
    .catch(error => {
        if (error.message.includes('Failed to fetch')) {
            throw new Error('Unable to connect to server');
        }
        throw error;
    });
}

/**
 * Load all alerts with enhanced error handling
 */
function loadAlerts() {
    if (!AlertsState.systemAvailable) {
        showAlertsUnavailableMessage();
        return;
    }
    
    AlertsState.loading = true;
    
    const url = AlertsState.currentClusterId 
        ? `/api/alerts?cluster_id=${AlertsState.currentClusterId}` 
        : '/api/alerts';
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                if (response.status === 503) {
                    throw new Error('Alerts system is currently unavailable');
                }
                throw new Error(`Request failed: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                AlertsState.alerts = data.alerts;
                displayAlerts(data.alerts);
                updateAlertsCounter(data.alerts.length);
            } else {
                throw new Error(data.message || 'Failed to load alerts');
            }
        })
        .catch(error => {
            console.error('❌ Error loading alerts:', error);
            AlertsState.lastError = error.message;
            
            if (error.message.includes('unavailable')) {
                AlertsState.systemAvailable = false;
                showAlertsUnavailableMessage();
            } else {
                showNotification(`Failed to load alerts: ${error.message}`, 'error');
                displayErrorMessage('Failed to load alerts', error.message);
            }
        })
        .finally(() => {
            AlertsState.loading = false;
        });
}

/**
 * Display error message in alerts container
 */
function displayErrorMessage(title, message) {
    const container = document.getElementById('alerts-list-container');
    if (!container) return;
    
    container.innerHTML = `
        <div class="alert alert-danger">
            <h6><i class="fas fa-exclamation-triangle me-2"></i>${escapeHtml(title)}</h6>
            <p class="mb-2">${escapeHtml(message)}</p>
            <button class="btn btn-sm btn-outline-danger" onclick="loadAlerts()">
                <i class="fas fa-sync me-1"></i>Retry
            </button>
        </div>
    `;
}

/**
 * Load alerts for specific cluster with error handling
 */
function loadClusterAlerts(clusterId) {
    if (!AlertsState.systemAvailable) return;
    
    fetch(`/api/alerts?cluster_id=${clusterId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Request failed: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                displayClusterAlerts(data.alerts);
                updateAlertsCounter(data.alerts.length);
            } else {
                throw new Error(data.message || 'Failed to load cluster alerts');
            }
        })
        .catch(error => {
            console.error('❌ Error loading cluster alerts:', error);
        });
}

/**
 * Display alerts in the UI with enhanced error handling
 */
function displayAlerts(alerts) {
    const container = document.getElementById('alerts-list-container');
    if (!container) return;
    
    if (!AlertsState.systemAvailable) {
        showAlertsUnavailableMessage();
        return;
    }
    
    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-bell-slash fa-2x mb-3"></i>
                <p>No alerts configured yet</p>
                <small>Create your first alert using the form above</small>
            </div>
        `;
        return;
    }
    
    const alertsHTML = alerts.map(alert => `
        <div class="alert-item card mb-3" data-alert-id="${alert.id}" data-status="${alert.status}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="card-title mb-2">
                            ${escapeHtml(alert.name)}
                            <span class="badge ${getStatusBadgeClass(alert.status)} ms-2">${alert.status}</span>
                        </h6>
                        <div class="row text-sm">
                            <div class="col-md-6">
                                <div class="mb-1">
                                    <strong>Threshold:</strong> 
                                    ${alert.threshold_amount > 0 ? '$' + alert.threshold_amount.toLocaleString() : alert.threshold_percentage + '%'}
                                </div>
                                <div class="mb-1">
                                    <strong>Email:</strong> ${escapeHtml(alert.email)}
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-1">
                                    <strong>Cluster:</strong> ${escapeHtml(alert.cluster_name || 'All clusters')}
                                </div>
                                <div class="mb-1">
                                    <strong>Frequency:</strong> ${alert.notification_frequency}
                                </div>
                            </div>
                        </div>
                        ${alert.last_triggered ? `
                            <div class="mt-2">
                                <small class="text-muted">
                                    <i class="fas fa-clock me-1"></i>
                                    Last triggered: ${formatDateTime(alert.last_triggered)} 
                                    (${alert.trigger_count} times)
                                </small>
                            </div>
                        ` : ''}
                    </div>
                    <div class="alert-actions">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary test-alert-btn" 
                                    data-alert-id="${alert.id}" 
                                    title="Send test notification">
                                <i class="fas fa-paper-plane"></i>
                            </button>
                            <button class="btn btn-outline-warning pause-alert-btn" 
                                    data-alert-id="${alert.id}" 
                                    data-action="${alert.status === 'active' ? 'pause' : 'resume'}"
                                    title="${alert.status === 'active' ? 'Pause' : 'Resume'} alert">
                                <i class="fas fa-${alert.status === 'active' ? 'pause' : 'play'}"></i>
                            </button>
                            <button class="btn btn-outline-danger delete-alert-btn" 
                                    data-alert-id="${alert.id}" 
                                    title="Delete alert">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = alertsHTML;
}

// Enhanced utility functions and other methods...
// (Rest of the functions remain the same with added error handling)

/**
 * Test alert notification with enhanced error handling
 */
function testAlert(alertId) {
    if (!AlertsState.systemAvailable) {
        showNotification('Alerts system is currently unavailable', 'warning');
        return;
    }
    
    const button = document.querySelector(`[data-alert-id="${alertId}"].test-alert-btn`);
    if (button) {
        const originalContent = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;
        
        fetch(`/api/alerts/${alertId}/test`, {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Request failed: ${response.status}`);
            }
            return response.json();
        })
        .then(result => {
            if (result.status === 'success') {
                showNotification('Test notification sent successfully!', 'success');
            } else {
                throw new Error(result.message || 'Failed to send test notification');
            }
        })
        .catch(error => {
            console.error('❌ Error testing alert:', error);
            showNotification(`Failed to send test: ${error.message}`, 'error');
        })
        .finally(() => {
            button.innerHTML = originalContent;
            button.disabled = false;
        });
    }
}

/**
 * Display alerts in cluster-specific view
 */
function displayClusterAlerts(alerts) {
    // Update alerts tab badge if exists
    const alertsTab = document.querySelector('#alerts-tab');
    if (alertsTab && alerts.length > 0) {
        const existingBadge = alertsTab.querySelector('.badge');
        if (existingBadge) {
            existingBadge.textContent = alerts.length;
        } else {
            alertsTab.innerHTML += ` <span class="badge bg-primary ms-1">${alerts.length}</span>`;
        }
    }
    
    // Update alerts list in the alerts tab
    displayAlerts(alerts);
}

/**
 * Pause or resume alert with enhanced error handling
 */
function pauseResumeAlert(alertId, action) {
    if (!AlertsState.systemAvailable) {
        showNotification('Alerts system is currently unavailable', 'warning');
        return;
    }
    
    const button = document.querySelector(`[data-alert-id="${alertId}"].pause-alert-btn`);
    if (button) {
        const originalContent = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;
        
        fetch(`/api/alerts/${alertId}/pause`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Request failed: ${response.status}`);
            }
            return response.json();
        })
        .then(result => {
            if (result.status === 'success') {
                showNotification(result.message, 'success');
                loadAlerts(); // Refresh to show updated status
            } else {
                throw new Error(result.message || `Failed to ${action} alert`);
            }
        })
        .catch(error => {
            console.error(`❌ Error ${action}ing alert:`, error);
            showNotification(`Failed to ${action} alert: ${error.message}`, 'error');
        })
        .finally(() => {
            button.innerHTML = originalContent;
            button.disabled = false;
        });
    }
}

/**
 * Delete alert with enhanced error handling
 */
function deleteAlert(alertId) {
    if (!AlertsState.systemAvailable) {
        showNotification('Alerts system is currently unavailable', 'warning');
        return;
    }
    
    if (!confirm('Are you sure you want to delete this alert? This action cannot be undone.')) {
        return;
    }
    
    const alertItem = document.querySelector(`[data-alert-id="${alertId}"]`);
    if (alertItem) {
        alertItem.style.opacity = '0.5';
        alertItem.style.pointerEvents = 'none';
        
        fetch(`/api/alerts/${alertId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Request failed: ${response.status}`);
            }
            return response.json();
        })
        .then(result => {
            if (result.status === 'success') {
                showNotification('Alert deleted successfully!', 'success');
                alertItem.remove();
                
                // Update counter
                const remainingAlerts = document.querySelectorAll('.alert-item').length;
                updateAlertsCounter(remainingAlerts);
                
                // Show empty state if no alerts left
                if (remainingAlerts === 0) {
                    displayAlerts([]);
                }
            } else {
                throw new Error(result.message || 'Failed to delete alert');
            }
        })
        .catch(error => {
            console.error('❌ Error deleting alert:', error);
            showNotification(`Failed to delete alert: ${error.message}`, 'error');
            
            // Restore UI state
            alertItem.style.opacity = '1';
            alertItem.style.pointerEvents = 'auto';
        });
    }
}

/**
 * Advanced alerts management modal
 */
function showAdvancedAlertsModal() {
    const modalHTML = `
        <div class="modal fade" id="advancedAlertsModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-cog me-2"></i>Advanced Alerts Configuration
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="advanced-alerts-form">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Alert Name</label>
                                        <input type="text" class="form-control" name="name" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Alert Type</label>
                                        <select class="form-select" name="alert_type">
                                            <option value="cost_threshold">Cost Threshold</option>
                                            <option value="performance">Performance</option>
                                            <option value="optimization">Optimization Opportunity</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Threshold Amount ($)</label>
                                        <input type="number" class="form-control" name="threshold_amount" min="0" step="0.01">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Threshold Percentage (%)</label>
                                        <input type="number" class="form-control" name="threshold_percentage" min="0" max="100">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-8">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Email Address</label>
                                        <input type="email" class="form-control" name="email" required>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Notification Frequency</label>
                                        <select class="form-select" name="notification_frequency">
                                            <option value="immediate">Immediate</option>
                                            <option value="daily">Daily</option>
                                            <option value="weekly">Weekly</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            
                            ${!AlertsState.emailConfigured ? `
                                <div class="alert alert-warning">
                                    <i class="fas fa-exclamation-triangle me-2"></i>
                                    Email notifications are not configured. Alerts will be logged but not sent via email.
                                </div>
                            ` : ''}
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="handleAdvancedAlertCreation()">
                            <i class="fas fa-plus me-2"></i>Create Alert
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('advancedAlertsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('advancedAlertsModal'));
    modal.show();
}

/**
 * Handle advanced alert creation
 */
function handleAdvancedAlertCreation() {
    const form = document.getElementById('advanced-alerts-form');
    const formData = new FormData(form);
    
    const alertData = {
        name: formData.get('name'),
        alert_type: formData.get('alert_type'),
        threshold_amount: parseFloat(formData.get('threshold_amount')) || 0,
        threshold_percentage: parseFloat(formData.get('threshold_percentage')) || 0,
        email: formData.get('email'),
        notification_frequency: formData.get('notification_frequency'),
        cluster_id: AlertsState.currentClusterId
    };
    
    createAlert(alertData)
        .then(result => {
            if (result.status === 'success') {
                showNotification('Advanced alert created successfully!', 'success');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('advancedAlertsModal'));
                modal.hide();
                
                // Refresh alerts
                loadAlerts();
            } else {
                throw new Error(result.message || 'Failed to create alert');
            }
        })
        .catch(error => {
            console.error('❌ Error creating advanced alert:', error);
            showNotification(`Failed to create alert: ${error.message}`, 'error');
        });
}

/**
 * Enhanced alert filtering
 */
function filterAlerts(status) {
    const buttons = document.querySelectorAll('.btn-group .btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    const alertItems = document.querySelectorAll('.alert-item');
    alertItems.forEach(item => {
        const alertStatus = item.dataset.status || 'active';
        if (status === 'all' || alertStatus === status) {
            item.style.display = 'block';
            item.style.animation = 'fadeIn 0.3s ease-in';
        } else {
            item.style.display = 'none';
        }
    });
}

// Utility functions
function getStatusBadgeClass(status) {
    const classes = {
        'active': 'bg-success',
        'paused': 'bg-warning',
        'triggered': 'bg-danger',
        'failed': 'bg-secondary'
    };
    return classes[status] || 'bg-secondary';
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function formatDateTime(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch {
        return dateString;
    }
}

function updateAlertsCounter(count) {
    const counter = document.querySelector('.alerts-counter');
    if (counter) {
        counter.textContent = count;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Notification function (use existing one or create simple fallback)
function showNotification(message, type = 'info') {
    if (window.smoothNotificationManager) {
        window.smoothNotificationManager.show(message, type);
    } else {
        // Fallback to simple alert
        console.log(`${type.toUpperCase()}: ${message}`);
        if (type === 'error') {
            alert(`Error: ${message}`);
        }
    }
}

// Initialize alerts when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAlertsSystem);
} else {
    initializeAlertsSystem();
}

// Make functions globally available
window.showAdvancedAlertsModal = showAdvancedAlertsModal;
window.loadAlerts = loadAlerts;
window.AlertsState = AlertsState;