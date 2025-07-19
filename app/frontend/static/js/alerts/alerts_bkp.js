/**
 * ============================================================================
 * ENHANCED ALERTS MANAGEMENT - FRONTEND WITH MULTI-CHANNEL SUPPORT (COMPLETE)
 * ============================================================================
 * Complete version with all functions restored and undefined references fixed
 * ============================================================================
 */

// Global alerts state with enhanced features
const AlertsState = {
    alerts: [],
    loading: false,
    currentClusterId: null,
    emailConfigured: false,
    slackConfigured: false,
    systemAvailable: true,
    lastError: null,
    currentFilter: 'all',
    inAppNotifications: [],
    unreadNotificationsCount: 0,
    notificationChannels: {
        email: false,
        slack: false,
        inApp: true
    },
    // 🆕 FREQUENCY CONFIGURATIONS
    frequencyConfigs: [],
    defaultFrequency: 'daily',
    frequencyMap: {
        'immediate': { 
            display: 'Immediate', 
            description: 'Send notification as soon as alert is triggered',
            icon: 'fa-bolt',
            color: 'danger'
        },
        'hourly': { 
            display: 'Hourly', 
            description: 'Send notifications once per hour',
            icon: 'fa-clock',
            color: 'warning'
        },
        'daily': { 
            display: 'Daily', 
            description: 'Send one notification per day at 9:00 AM',
            icon: 'fa-calendar-day',
            color: 'primary'
        },
        'weekly': { 
            display: 'Weekly', 
            description: 'Send notifications once per week',
            icon: 'fa-calendar-week',
            color: 'info'
        },
        'monthly': { 
            display: 'Monthly', 
            description: 'Send notifications once per month',
            icon: 'fa-calendar-alt',
            color: 'secondary'
        },
        'custom_4h': { 
            display: 'Every 4 Hours', 
            description: 'Send notifications every 4 hours',
            icon: 'fa-history',
            color: 'success'
        }
    }
};

const BootstrapHelper = {
    isAvailable: function() {
        return typeof bootstrap !== 'undefined' || typeof $ !== 'undefined';
    },
    
    showModal: function(modalElement) {
        if (typeof bootstrap !== 'undefined') {
            // Bootstrap 5
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            return modal;
        } else if (typeof $ !== 'undefined' && $.fn.modal) {
            // Bootstrap 4 with jQuery
            $(modalElement).modal('show');
            return {
                hide: function() { $(modalElement).modal('hide'); }
            };
        } else {
            // Fallback: simple show/hide
            modalElement.style.display = 'block';
            modalElement.classList.add('show');
            document.body.classList.add('modal-open');
            
            // Add backdrop
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            backdrop.id = 'fallback-backdrop';
            document.body.appendChild(backdrop);
            
            return {
                hide: function() {
                    modalElement.style.display = 'none';
                    modalElement.classList.remove('show');
                    document.body.classList.remove('modal-open');
                    const backdrop = document.getElementById('fallback-backdrop');
                    if (backdrop) backdrop.remove();
                }
            };
        }
    },
    
    hideModal: function(modalElement) {
        if (typeof bootstrap !== 'undefined') {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) modal.hide();
        } else if (typeof $ !== 'undefined' && $.fn.modal) {
            $(modalElement).modal('hide');
        } else {
            // Fallback
            modalElement.style.display = 'none';
            modalElement.classList.remove('show');
            document.body.classList.remove('modal-open');
            const backdrop = document.getElementById('fallback-backdrop');
            if (backdrop) backdrop.remove();
        }
    },
    
    showToast: function(toastElement, options = {}) {
        if (typeof bootstrap !== 'undefined') {
            const toast = new bootstrap.Toast(toastElement, options);
            toast.show();
            return toast;
        } else {
            // Fallback: simple show with timeout
            toastElement.style.display = 'block';
            toastElement.classList.add('show');
            
            setTimeout(() => {
                toastElement.style.display = 'none';
                toastElement.classList.remove('show');
                toastElement.remove();
            }, options.delay || 5000);
            
            return {
                hide: function() {
                    toastElement.style.display = 'none';
                    toastElement.classList.remove('show');
                    toastElement.remove();
                }
            };
        }
    }
};

function closeDeleteAlertModal() {
    const modalElement = document.getElementById('deleteAlertModal');
    if (modalElement) {
        BootstrapHelper.hideModal(modalElement);
        
        // Remove from DOM after animation
        setTimeout(() => {
            modalElement.remove();
        }, 300);
    }
    window.currentDeleteModal = null;
}

function loadFrequencyConfigurations() {
    fetch('/api/alerts/frequency-configs')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load frequency configs: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                AlertsState.frequencyConfigs = data.configurations || [];
                console.log('✅ Loaded frequency configurations:', AlertsState.frequencyConfigs.length);
            } else {
                throw new Error(data.message || 'Failed to load frequency configurations');
            }
        })
        .catch(error => {
            console.warn('⚠️ Using default frequency configurations:', error.message);
            // Use default configurations if backend doesn't have the endpoint
            AlertsState.frequencyConfigs = Object.keys(AlertsState.frequencyMap).map(key => ({
                frequency_type: key,
                display_name: AlertsState.frequencyMap[key].display,
                description: AlertsState.frequencyMap[key].description
            }));
        });
}

function getFrequencyInfo(frequency) {
    // Ensure we never return undefined
    if (!frequency || frequency === 'undefined' || frequency === '') {
        frequency = AlertsState.defaultFrequency;
    }
    
    // Try to get from loaded configs first
    const config = AlertsState.frequencyConfigs.find(c => c.frequency_type === frequency);
    if (config) {
        return {
            display: config.display_name,
            description: config.description,
            icon: AlertsState.frequencyMap[frequency]?.icon || 'fa-clock',
            color: AlertsState.frequencyMap[frequency]?.color || 'primary'
        };
    }
    
    // Fallback to hardcoded map
    const fallback = AlertsState.frequencyMap[frequency];
    if (fallback) {
        return fallback;
    }
    
    // Ultimate fallback
    return {
        display: 'Daily',
        description: 'Send notifications daily',
        icon: 'fa-calendar-day',
        color: 'primary'
    };
}

/**
 * Initialize alerts system with enhanced error handling and multi-channel support
 */
function initializeAlertsSystem() {
    console.log('🔔 Initializing enhanced alerts system with frequency management...');
    
    // First check if alerts system is available
    checkAlertsSystemStatus()
        .then(() => {
            if (AlertsState.systemAvailable) {
                // Load frequency configurations
                loadFrequencyConfigurations();
                
                // Check notification channel configurations
                checkNotificationChannels();
                
                // Load existing alerts
                loadAlerts();
                
                // Load in-app notifications
                loadInAppNotifications();
                
                // Setup event listeners
                setupAlertsEventListeners();
                
                // Check if we're on a cluster-specific page
                const urlPath = window.location.pathname;
                const clusterMatch = urlPath.match(/\/cluster\/([^\/]+)/);
                if (clusterMatch) {
                    AlertsState.currentClusterId = clusterMatch[1];
                    loadClusterAlerts(AlertsState.currentClusterId);
                }
                
                // Setup periodic refresh
                if (AlertsState.systemAvailable) {
                    setInterval(loadInAppNotifications, 30000);
                }
                
                console.log('✅ Enhanced alerts system with frequency management initialized');
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
 * Check if alerts system is available with enhanced status checking
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
                
                // Enhanced notification channels detection
                if (data.notification_channels) {
                    AlertsState.notificationChannels.email = data.notification_channels.email?.configured || false;
                    AlertsState.notificationChannels.slack = data.notification_channels.slack?.configured || false;
                    AlertsState.notificationChannels.inApp = data.notification_channels.in_app?.available || true;
                }
                
                console.log('📊 Enhanced alerts system status:', {
                    available: AlertsState.systemAvailable,
                    channels: AlertsState.notificationChannels,
                    managerType: data.alerts_manager_type
                });
                
                // Update UI with channel status
                updateNotificationChannelsUI();
                
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
 * Check notification channel configurations
 */
function checkNotificationChannels() {
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
                AlertsState.notificationChannels.email = data.email_configured;
                AlertsState.notificationChannels.slack = data.slack_configured;
                AlertsState.notificationChannels.inApp = data.in_app_available;
                
                updateNotificationChannelsUI();
            } else {
                throw new Error(data.message || 'Notification config check failed');
            }
        })
        .catch(error => {
            console.error('❌ Error checking notification channels:', error);
            updateNotificationChannelsUI(error.message);
        });
}

/**
 * Update notification channels status in UI
 */
function updateNotificationChannelsUI(errorMessage = null) {
    const channelElements = document.querySelectorAll('.notification-channels-status');
    
    channelElements.forEach(element => {
        let channelsHtml = '';
        
        if (errorMessage) {
            channelsHtml = `
                <i class="fas fa-exclamation-triangle text-warning me-1"></i>
                Error checking channels: ${errorMessage}
            `;
        } else {
            const channels = [];
            
            if (AlertsState.notificationChannels.email) {
                channels.push('<i class="fas fa-envelope text-success me-1"></i>Email');
            } else {
                channels.push('<i class="fas fa-envelope text-muted me-1"></i><span class="text-muted">Email</span>');
            }
            
            if (AlertsState.notificationChannels.slack) {
                channels.push('<i class="fab fa-slack text-success me-1"></i>Slack');
            } else {
                channels.push('<i class="fab fa-slack text-muted me-1"></i><span class="text-muted">Slack</span>');
            }
            
            if (AlertsState.notificationChannels.inApp) {
                channels.push('<i class="fas fa-bell text-success me-1"></i>In-App');
            }
            
            channelsHtml = `
                <div class="notification-channels">
                    <small class="text-muted">Notification Channels:</small><br>
                    ${channels.join(' | ')}
                </div>
            `;
        }
        
        element.innerHTML = channelsHtml;
    });
    
    // Update individual channel status indicators
    updateIndividualChannelStatus();
}

/**
 * Update individual channel status indicators in the UI
 */
function updateIndividualChannelStatus() {
    // Update email status
    const emailStatus = document.getElementById('email-status-indicator');
    const emailChannelStatus = document.getElementById('email-channel-status');
    
    if (emailStatus) {
        emailStatus.innerHTML = AlertsState.notificationChannels.email 
            ? '<i class="fas fa-circle text-success"></i>' 
            : '<i class="fas fa-circle text-muted"></i>';
    }
    
    if (emailChannelStatus) {
        const statusText = emailChannelStatus.querySelector('.channel-status-text');
        const icon = emailChannelStatus.querySelector('.fa-envelope');
        
        if (statusText) {
            statusText.textContent = AlertsState.notificationChannels.email ? 'Configured' : 'Not Configured';
            statusText.className = AlertsState.notificationChannels.email 
                ? 'channel-status-text text-success' 
                : 'channel-status-text text-muted';
        }
        
        if (icon) {
            icon.className = AlertsState.notificationChannels.email 
                ? 'fas fa-envelope fa-2x text-success mb-2' 
                : 'fas fa-envelope fa-2x text-muted mb-2';
        }
    }
    
    // Update Slack status
    const slackStatus = document.getElementById('slack-status-indicator');
    const slackChannelStatus = document.getElementById('slack-channel-status');
    
    if (slackStatus) {
        slackStatus.innerHTML = AlertsState.notificationChannels.slack 
            ? '<i class="fas fa-circle text-success"></i>' 
            : '<i class="fas fa-circle text-muted"></i>';
    }
    
    if (slackChannelStatus) {
        const statusText = slackChannelStatus.querySelector('.channel-status-text');
        const icon = slackChannelStatus.querySelector('.fa-slack');
        
        if (statusText) {
            statusText.textContent = AlertsState.notificationChannels.slack ? 'Configured' : 'Not Configured';
            statusText.className = AlertsState.notificationChannels.slack 
                ? 'channel-status-text text-success' 
                : 'channel-status-text text-muted';
        }
        
        if (icon) {
            icon.className = AlertsState.notificationChannels.slack 
                ? 'fab fa-slack fa-2x text-success mb-2' 
                : 'fab fa-slack fa-2x text-muted mb-2';
        }
    }
    
    // Update test button states
    const testSlackBtn = document.getElementById('test-slack-btn');
    if (testSlackBtn) {
        testSlackBtn.disabled = !AlertsState.notificationChannels.slack;
        if (!AlertsState.notificationChannels.slack) {
            testSlackBtn.title = 'Slack webhook not configured';
        } else {
            testSlackBtn.title = 'Test Slack integration';
        }
    }
}

/**
 * Load in-app notifications (FIXED: with proper error handling)
 */

function loadInAppNotifications() {
    if (!AlertsState.systemAvailable) return;
    
    // Check if in-app notifications endpoint exists
    fetch('/api/alerts/health')
        .then(response => response.json())
        .then(healthData => {
            // Only try to load notifications if the system supports it
            if (healthData.health && 
                healthData.health.notification_channels && 
                healthData.health.notification_channels.in_app) {
                
                // 🆕 BUILD URL WITH CLUSTER FILTER
                let apiUrl = '/api/notifications/in-app?unread_only=false&limit=50';
                
                // Add cluster_id filter if we're on a specific cluster page
                if (AlertsState.currentClusterId) {
                    apiUrl += `&cluster_id=${encodeURIComponent(AlertsState.currentClusterId)}`;
                    console.log(`📱 Loading notifications for cluster: ${AlertsState.currentClusterId}`);
                } else {
                    console.log('📱 Loading all notifications (no cluster filter)');
                }
                
                return fetch(apiUrl);
            } else {
                // Mock empty notifications for now
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({
                        status: 'success',
                        notifications: [],
                        unread_count: 0
                    })
                });
            }
        })
        .then(response => {
            if (!response.ok) {
                // If endpoint doesn't exist, just use empty notifications
                if (response.status === 404) {
                    console.log('ℹ️ In-app notifications endpoint not available - using mock data');
                    AlertsState.inAppNotifications = [];
                    AlertsState.unreadNotificationsCount = 0;
                    updateInAppNotificationsUI();
                    updateNotificationBadge();
                    return;
                }
                throw new Error(`Failed to load notifications: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.status === 'success') {
                AlertsState.inAppNotifications = data.notifications || [];
                AlertsState.unreadNotificationsCount = data.unread_count || 0;
                
                updateInAppNotificationsUI();
                updateNotificationBadge();
                
                const clusterText = AlertsState.currentClusterId ? ` for cluster ${AlertsState.currentClusterId}` : '';
                console.log(`📱 Loaded ${data.notifications?.length || 0} in-app notifications${clusterText} (${data.unread_count || 0} unread)`);
            }
        })
        .catch(error => {
            console.log('ℹ️ In-app notifications not available:', error.message);
            // Use fallback empty state
            AlertsState.inAppNotifications = [];
            AlertsState.unreadNotificationsCount = 0;
            updateInAppNotificationsUI();
            updateNotificationBadge();
        });
}

/**
 * Update in-app notifications UI
 */
function updateInAppNotificationsUI() {
    const container = document.getElementById('in-app-notifications-container');
    if (!container) return;
    
    if (AlertsState.inAppNotifications.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-3">
                <i class="fas fa-bell-slash fa-2x mb-2"></i>
                <p>No notifications yet</p>
            </div>
        `;
        return;
    }
    
    const notificationsHtml = AlertsState.inAppNotifications.map(notification => `
        <div class="notification-item ${notification.read ? 'read' : 'unread'} ${notification.dismissed ? 'dismissed' : ''}" 
             data-notification-id="${notification.id}">
            <div class="d-flex justify-content-between align-items-start">
                <div class="notification-content flex-grow-1">
                    <div class="notification-header d-flex align-items-center">
                        <i class="fas fa-${getNotificationIcon(notification.type)} me-2 text-${getNotificationColor(notification.type)}"></i>
                        <strong>${escapeHtml(notification.title)}</strong>
                        ${!notification.read ? '<span class="badge bg-primary ms-2">New</span>' : ''}
                    </div>
                    <div class="notification-message mt-1">
                        ${escapeHtml(notification.message)}
                    </div>
                    <div class="notification-meta mt-2">
                        <small class="text-muted">
                            <i class="fas fa-clock me-1"></i>
                            ${formatDateTime(notification.timestamp)}
                            ${notification.cluster_id ? `| <i class="fas fa-dharmachakra me-1"></i>Cluster: ${notification.cluster_id}` : ''}
                        </small>
                    </div>
                </div>
                <div class="notification-actions">
                    <div class="btn-group btn-group-sm">
                        ${!notification.read ? `
                            <button class="btn btn-outline-primary btn-sm" 
                                    onclick="markNotificationAsRead('${notification.id}')" 
                                    title="Mark as read">
                                <i class="fas fa-check"></i>
                            </button>
                        ` : ''}
                        <button class="btn btn-outline-secondary btn-sm" 
                                onclick="dismissNotification('${notification.id}')" 
                                title="Dismiss">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = notificationsHtml;
}

/**
 * Update notification badge in UI
 */
function updateNotificationBadge() {
    const badges = document.querySelectorAll('.notification-badge, .notifications-counter');
    badges.forEach(badge => {
        if (AlertsState.unreadNotificationsCount > 0) {
            badge.textContent = AlertsState.unreadNotificationsCount;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    });
}

/**
 * Mark notification as read (FIXED: with endpoint check)
 */
function markNotificationAsRead(notificationId) {
    if (!AlertsState.systemAvailable) return;
    
    // Try to call the endpoint, but handle gracefully if it doesn't exist
    fetch('/api/notifications/in-app', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            notification_ids: [notificationId],
            action: 'mark_read'
        })
    })
    .then(response => {
        if (response.status === 404) {
            // Endpoint doesn't exist, just update locally
            console.log('ℹ️ In-app notifications API not available - updating locally');
            markNotificationAsReadLocally(notificationId);
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.status === 'success') {
            markNotificationAsReadLocally(notificationId);
        } else if (data) {
            showNotification('Failed to mark notification as read', 'error');
        }
    })
    .catch(error => {
        console.log('ℹ️ Marking notification as read locally:', error.message);
        markNotificationAsReadLocally(notificationId);
    });
}

/**
 * Mark notification as read locally
 */
function markNotificationAsReadLocally(notificationId) {
    const notification = AlertsState.inAppNotifications.find(n => n.id === notificationId);
    if (notification && !notification.read) {
        notification.read = true;
        AlertsState.unreadNotificationsCount = Math.max(0, AlertsState.unreadNotificationsCount - 1);
        updateInAppNotificationsUI();
        updateNotificationBadge();
    }
}

/**
 * Dismiss notification (FIXED: with endpoint check)
 */
function dismissNotification(notificationId) {
    if (!AlertsState.systemAvailable) return;
    
    // Try to call the endpoint, but handle gracefully if it doesn't exist
    fetch('/api/notifications/in-app', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            notification_ids: [notificationId],
            action: 'dismiss'
        })
    })
    .then(response => {
        if (response.status === 404) {
            // Endpoint doesn't exist, just update locally
            console.log('ℹ️ In-app notifications API not available - updating locally');
            dismissNotificationLocally(notificationId);
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.status === 'success') {
            dismissNotificationLocally(notificationId);
        } else if (data) {
            showNotification('Failed to dismiss notification', 'error');
        }
    })
    .catch(error => {
        console.log('ℹ️ Dismissing notification locally:', error.message);
        dismissNotificationLocally(notificationId);
    });
}

/**
 * Dismiss notification locally
 */
function dismissNotificationLocally(notificationId) {
    AlertsState.inAppNotifications = AlertsState.inAppNotifications.filter(n => n.id !== notificationId);
    updateInAppNotificationsUI();
    updateNotificationBadge();
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
 * Setup event listeners for alerts with enhanced features (FIXED)
 */
function setupAlertsEventListeners() {
    // Budget alert form submission
    const budgetForm = document.getElementById('budget-alert-form');
    if (budgetForm) {
        budgetForm.addEventListener('submit', handleBudgetAlertSubmission);
    }
    
    // Advanced alerts form
    const advancedForm = document.getElementById('advanced-alerts-form');
    if (advancedForm) {
        advancedForm.addEventListener('submit', handleAdvancedAlertSubmission);
    }
    
    // Alert filtering
    setupAlertFiltering();
    
    // Alert list interactions
    document.addEventListener('click', function(event) {
        if (!AlertsState.systemAvailable) {
            if (event.target.closest('.test-alert-btn, .pause-alert-btn, .delete-alert-btn, .edit-frequency-btn')) {
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
        
        // 🆕 EDIT FREQUENCY BUTTON
        if (event.target.closest('.edit-frequency-btn')) {
            const alertId = event.target.closest('.edit-frequency-btn').dataset.alertId;
            showEditFrequencyModal(alertId);
        }
    });
}

/**
 * FIXED: Setup alert filtering functionality
 */
function setupAlertFiltering() {
    // Create filter buttons if they don't exist
    const alertsContainer = document.getElementById('alerts-list-container');
    if (alertsContainer && !document.getElementById('alerts-filter-buttons')) {
        const filterButtonsHtml = `
            <div id="alerts-filter-buttons" class="mb-3">
                <div class="btn-group" role="group" aria-label="Alert filters">
                    <button type="button" class="btn btn-outline-primary active" 
                            data-filter="all" onclick="filterAlerts('all')">
                        <i class="fas fa-list me-1"></i>All (<span id="all-count">0</span>)
                    </button>
                    <button type="button" class="btn btn-outline-success" 
                            data-filter="active" onclick="filterAlerts('active')">
                        <i class="fas fa-play me-1"></i>Active (<span id="active-count">0</span>)
                    </button>
                    <button type="button" class="btn btn-outline-warning" 
                            data-filter="paused" onclick="filterAlerts('paused')">
                        <i class="fas fa-pause me-1"></i>Paused (<span id="paused-count">0</span>)
                    </button>
                </div>
            </div>
        `;
        
        alertsContainer.insertAdjacentHTML('beforebegin', filterButtonsHtml);
    }
}

/**
 * FIXED: Enhanced alert filtering with proper counting
 */
function filterAlerts(filter) {
    console.log(`🔍 Filtering alerts by: ${filter}`);
    
    AlertsState.currentFilter = filter;
    
    // Update button states
    const filterButtons = document.querySelectorAll('#alerts-filter-buttons .btn');
    filterButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.filter === filter) {
            btn.classList.add('active');
        }
    });
    
    // Filter and display alerts
    const alertItems = document.querySelectorAll('.alert-item');
    let visibleCount = 0;
    
    alertItems.forEach(item => {
        const alertStatus = item.dataset.status || 'active';
        let shouldShow = false;
        
        switch (filter) {
            case 'all':
                shouldShow = true;
                break;
            case 'active':
                shouldShow = alertStatus === 'active';
                break;
            case 'paused':
                shouldShow = alertStatus === 'paused';
                break;
            default:
                shouldShow = true;
        }
        
        if (shouldShow) {
            item.style.display = 'block';
            item.style.animation = 'fadeIn 0.3s ease-in';
            visibleCount++;
        } else {
            item.style.display = 'none';
        }
    });
    
    // Update filter counts
    updateFilterCounts();
    
    console.log(`✅ Filter applied: ${filter}, showing ${visibleCount} alerts`);
}

/**
 * Update filter button counts
 */
function updateFilterCounts() {
    const alertItems = document.querySelectorAll('.alert-item');
    
    let allCount = alertItems.length;
    let activeCount = 0;
    let pausedCount = 0;
    
    alertItems.forEach(item => {
        const status = item.dataset.status || 'active';
        if (status === 'active') {
            activeCount++;
        } else if (status === 'paused') {
            pausedCount++;
        }
    });
    
    // Update count displays
    const allCountEl = document.getElementById('all-count');
    const activeCountEl = document.getElementById('active-count');
    const pausedCountEl = document.getElementById('paused-count');
    
    if (allCountEl) allCountEl.textContent = allCount;
    if (activeCountEl) activeCountEl.textContent = activeCount;
    if (pausedCountEl) pausedCountEl.textContent = pausedCount;
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
    const alertName = formData.get('name') || `Budget Alert - ${formData.get('threshold_amount')}`;
    const budgetAmount = parseFloat(formData.get('threshold_amount'));
    const alertEmail = formData.get('email');
    const alertThreshold = parseFloat(formData.get('threshold_percentage'));
    const frequency = formData.get('notification_frequency') || 'daily';
    const frequencyAtTime = formData.get('frequency_at_time') || '09:00';
    const maxNotificationsPerDay = parseInt(formData.get('max_notifications_per_day')) || null;
    const cooldownPeriodHours = parseInt(formData.get('cooldown_period_hours')) || 4;
    
    // Enhanced validation
    if (!alertName.trim()) {
        showNotification('Please enter an alert name', 'error');
        return;
    }
    
    if (!budgetAmount || budgetAmount <= 0) {
        showNotification('Please enter a valid budget amount', 'error');
        return;
    }
    
    if (!alertEmail || !isValidEmail(alertEmail)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }
    
    // Get selected notification channels
    const selectedChannels = [];
    const channelCheckboxes = event.target.querySelectorAll('input[name="channels"]:checked');
    channelCheckboxes.forEach(checkbox => {
        selectedChannels.push(checkbox.value);
    });
    
    if (selectedChannels.length === 0) {
        showNotification('Please select at least one notification channel', 'error');
        return;
    }
    
    const alertData = {
        name: alertName,
        alert_type: 'cost_threshold',
        threshold_amount: budgetAmount,
        threshold_percentage: alertThreshold,
        email: alertEmail,
        
        // Enhanced frequency settings
        notification_frequency: frequency,
        frequency_at_time: frequencyAtTime,
        max_notifications_per_day: maxNotificationsPerDay,
        cooldown_period_hours: cooldownPeriodHours,
        
        cluster_id: AlertsState.currentClusterId,
        notification_channels: selectedChannels
    };
    
    // Show loading state
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating smart alert...';
    submitBtn.disabled = true;
    
    createAlert(alertData)
        .then(result => {
            if (result.status === 'success') {
                const frequencyInfo = getFrequencyInfo(frequency);
                showNotification(
                    'Smart Alert Created Successfully!', 
                    `Alert "${alertName}" created with ${frequencyInfo.display} frequency and ${selectedChannels.length} notification channels`,
                    'success'
                );
                
                event.target.reset();
                loadAlerts();
                
                // Update frequency preview after reset
                setTimeout(setupFrequencyPreview, 100);
                
                // Create in-app notification
                createLocalInAppNotification(
                    'New Smart Alert Created',
                    `Budget alert "${alertName}" created with ${frequencyInfo.display} frequency for $${budgetAmount.toLocaleString()}`,
                    'success'
                );
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
 * Handle advanced alert form submission (RESTORED FUNCTION)
 */
function handleAdvancedAlertSubmission(event) {
    event.preventDefault();
    
    if (!AlertsState.systemAvailable) {
        showNotification('Alerts system is currently unavailable', 'error');
        return;
    }
    
    const formData = new FormData(event.target);
    
    // Get selected notification channels
    const selectedChannels = [];
    const channelCheckboxes = event.target.querySelectorAll('input[name="channels"]:checked');
    channelCheckboxes.forEach(checkbox => {
        selectedChannels.push(checkbox.value);
    });
    
    const alertData = {
        name: formData.get('name'),
        alert_type: formData.get('alert_type'),
        threshold_amount: parseFloat(formData.get('threshold_amount')) || 0,
        threshold_percentage: parseFloat(formData.get('threshold_percentage')) || 0,
        email: formData.get('email'),
        notification_frequency: formData.get('notification_frequency'),
        cluster_id: AlertsState.currentClusterId,
        notification_channels: selectedChannels
    };
    
    // Validation
    if (!alertData.name) {
        showNotification('Please enter an alert name', 'error');
        return;
    }
    
    if (!alertData.email || !isValidEmail(alertData.email)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }
    
    if (alertData.threshold_amount <= 0 && alertData.threshold_percentage <= 0) {
        showNotification('Please set either a threshold amount or percentage', 'error');
        return;
    }
    
    // Show loading state
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating alert...';
    submitBtn.disabled = true;
    
    createAlert(alertData)
        .then(result => {
            if (result.status === 'success') {
                showNotification('Advanced alert created successfully!', 'success');
                event.target.reset();
                loadAlerts(); // Refresh alerts list
                
                // Create in-app notification locally
                createLocalInAppNotification(
                    'Advanced Alert Created',
                    `Alert "${alertData.name}" has been created with ${selectedChannels.length} notification channel(s)`,
                    'success'
                );
            } else {
                throw new Error(result.message || 'Failed to create alert');
            }
        })
        .catch(error => {
            console.error('❌ Error creating advanced alert:', error);
            showNotification(`Failed to create alert: ${error.message}`, 'error');
        })
        .finally(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
}

/**
 * Create a local in-app notification (fallback)
 */
function createLocalInAppNotification(title, message, type = 'info') {
    const notification = {
        id: Date.now().toString(),
        title: title,
        message: message,
        type: type,
        timestamp: new Date().toISOString(),
        read: false,
        dismissed: false,
        cluster_id: AlertsState.currentClusterId
    };
    
    AlertsState.inAppNotifications.unshift(notification);
    AlertsState.unreadNotificationsCount += 1;
    
    updateInAppNotificationsUI();
    updateNotificationBadge();
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
 * Load all alerts with enhanced error handling and filtering support
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
                updateFilterCounts();
                
                // Apply current filter
                filterAlerts(AlertsState.currentFilter);
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
 * Load cluster-specific alerts (RESTORED FUNCTION)
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
 * Display cluster-specific alerts (RESTORED FUNCTION)
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
 * Display alerts in the UI with enhanced status support
 */
function displayAlerts(alerts) {
    const container = document.getElementById('alerts-list-container');
    if (!container) return;
    
    if (!AlertsState.systemAvailable) {
        showAlertsUnavailableMessage();
        return;
    }
    
    // Update summary counters
    updateAlertSummaryCounters(alerts);
    
    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-bell-slash fa-3x mb-3"></i>
                <h5>No alerts configured yet</h5>
                <p>Create your first smart alert using the form above</p>
                <button class="btn btn-primary" onclick="document.getElementById('alert-name').focus()">
                    <i class="fas fa-plus me-2"></i>Create Alert
                </button>
            </div>
        `;
        return;
    }
    
    const alertsHTML = alerts.map(alert => {
        const frequency = alert.notification_frequency || AlertsState.defaultFrequency;
        const frequencyInfo = getFrequencyInfo(frequency);
        const nextNotification = alert.next_notification_time ? formatDateTime(alert.next_notification_time) : 'TBD';
        const statusClass = getStatusBadgeClass(alert.status || 'active');
        
        // Calculate alert health score
        const healthScore = calculateAlertHealthScore(alert);
        
        return `
            <div class="alert-item card border-0 shadow-sm mb-3" 
                 data-alert-id="${alert.id}" 
                 data-status="${alert.status || 'active'}"
                 data-frequency="${frequency}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center mb-2">
                                <h6 class="card-title mb-0 me-2">
                                    <i class="fas fa-bell me-1"></i>
                                    ${escapeHtml(alert.name)}
                                </h6>
                                <span class="badge ${statusClass} me-2">
                                    ${(alert.status || 'active').toUpperCase()}
                                </span>
                                <span class="frequency-badge ${frequency}">
                                    <i class="fas ${frequencyInfo.icon} me-1"></i>
                                    ${frequencyInfo.display}
                                </span>
                                ${healthScore < 80 ? `<span class="badge bg-warning text-dark ms-2" title="Alert needs attention">Health: ${healthScore}%</span>` : ''}
                            </div>
                            
                            <!-- Enhanced Alert Details -->
                            <div class="row text-sm mb-3">
                                <div class="col-md-6">
                                    <div class="alert-detail-item">
                                        <strong><i class="fas fa-dollar-sign me-1 text-success"></i>Budget:</strong>
                                        <span class="text-success">${alert.threshold_amount > 0 ? '$' + alert.threshold_amount.toLocaleString() : 'N/A'}</span>
                                    </div>
                                    <div class="alert-detail-item">
                                        <strong><i class="fas fa-percentage me-1 text-warning"></i>Threshold:</strong>
                                        <span class="text-warning">${alert.threshold_percentage || 0}%</span>
                                    </div>
                                    <div class="alert-detail-item">
                                        <strong><i class="fas fa-at me-1 text-info"></i>Email:</strong>
                                        <span class="text-info">${escapeHtml(alert.email || 'Not set')}</span>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="alert-detail-item">
                                        <strong><i class="fas fa-dharmachakra me-1 text-primary"></i>Cluster:</strong>
                                        <span class="text-primary">${escapeHtml(alert.cluster_name || 'All clusters')}</span>
                                    </div>
                                    <div class="alert-detail-item">
                                        <strong><i class="fas fa-layer-group me-1 text-secondary"></i>Resource Group:</strong>
                                        <span class="text-secondary">${escapeHtml(alert.resource_group || 'N/A')}</span>
                                    </div>
                                    <div class="alert-detail-item">
                                        <strong><i class="fas fa-paper-plane me-1 text-success"></i>Notifications:</strong>
                                        <span class="text-success">${alert.notification_count || 0} sent</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Enhanced Frequency Information -->
                            <div class="frequency-info-card p-3 bg-light rounded mb-3">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h6 class="mb-2">
                                            <i class="fas fa-clock me-2 text-primary"></i>
                                            Frequency Settings
                                        </h6>
                                        <div class="small">
                                            <div class="mb-1">
                                                <strong>Type:</strong> ${frequencyInfo.display}
                                                <span class="text-muted ms-2">${frequencyInfo.description}</span>
                                            </div>
                                            ${frequency === 'daily' && alert.frequency_at_time ? `
                                                <div class="mb-1">
                                                    <strong>Time:</strong> ${alert.frequency_at_time}
                                                </div>
                                            ` : ''}
                                            ${alert.max_notifications_per_day ? `
                                                <div class="mb-1">
                                                    <strong>Daily Limit:</strong> ${alert.max_notifications_per_day} notifications
                                                </div>
                                            ` : ''}
                                            ${alert.cooldown_period_hours ? `
                                                <div class="mb-1">
                                                    <strong>Cooldown:</strong> ${alert.cooldown_period_hours} hours
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <h6 class="mb-2">
                                            <i class="fas fa-broadcast-tower me-2 text-info"></i>
                                            Notification Channels
                                        </h6>
                                        <div class="small">
                                            ${getNotificationChannelsDisplay(alert)}
                                        </div>
                                        ${frequency !== 'immediate' && nextNotification !== 'TBD' ? `
                                            <div class="mt-2">
                                                <strong class="text-primary">Next notification:</strong>
                                                <span class="text-muted">${nextNotification}</span>
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Alert Activity -->
                            ${alert.last_triggered ? `
                                <div class="alert-activity mt-2">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <small class="text-muted">
                                                <i class="fas fa-history me-1"></i>
                                                Last triggered: ${formatDateTime(alert.last_triggered)}
                                            </small>
                                        </div>
                                        <div class="col-md-6">
                                            <small class="text-muted">
                                                <i class="fas fa-fire me-1"></i>
                                                Triggered ${alert.trigger_count || 0} times
                                            </small>
                                        </div>
                                    </div>
                                    ${alert.last_notification_sent ? `
                                        <div class="mt-1">
                                            <small class="text-success">
                                                <i class="fas fa-paper-plane me-1"></i>
                                                Last notification: ${formatDateTime(alert.last_notification_sent)}
                                            </small>
                                        </div>
                                    ` : ''}
                                </div>
                            ` : `
                                <div class="alert-activity mt-2">
                                    <small class="text-muted">
                                        <i class="fas fa-info-circle me-1"></i>
                                        Alert created but not yet triggered
                                    </small>
                                </div>
                            `}
                        </div>
                        
                        <!-- Enhanced Action Buttons -->
                        <div class="alert-actions">
                            <div class="btn-group-vertical btn-group-sm">
                                <button class="btn btn-outline-primary test-alert-btn" 
                                        data-alert-id="${alert.id}" 
                                        title="Send test notification">
                                    <i class="fas fa-paper-plane me-1"></i>Test
                                </button>
                                <button class="btn btn-outline-info edit-frequency-btn" 
                                        data-alert-id="${alert.id}" 
                                        title="Edit frequency settings">
                                    <i class="fas fa-clock me-1"></i>Edit
                                </button>
                                <button class="btn btn-outline-warning pause-alert-btn" 
                                        data-alert-id="${alert.id}" 
                                        data-action="${(alert.status || 'active') === 'active' ? 'pause' : 'resume'}"
                                        title="${(alert.status || 'active') === 'active' ? 'Pause' : 'Resume'} alert">
                                    <i class="fas fa-${(alert.status || 'active') === 'active' ? 'pause' : 'play'} me-1"></i>
                                    ${(alert.status || 'active') === 'active' ? 'Pause' : 'Resume'}
                                </button>
                                <button class="btn btn-outline-danger delete-alert-btn" 
                                        data-alert-id="${alert.id}" 
                                        title="Delete alert">
                                    <i class="fas fa-trash me-1"></i>Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = alertsHTML;
}

function updateAlertSummaryCounters(alerts) {
    const totalCount = alerts.length;
    const activeCount = alerts.filter(a => (a.status || 'active') === 'active').length;
    const pausedCount = alerts.filter(a => a.status === 'paused').length;
    const recentlyTriggered = alerts.filter(a => {
        if (!a.last_triggered) return false;
        const lastTriggered = new Date(a.last_triggered);
        const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
        return lastTriggered > dayAgo;
    }).length;
    
    // Update summary counters
    const elements = {
        'total-alerts-count': totalCount,
        'active-alerts-count': activeCount,
        'paused-alerts-count': pausedCount,
        'triggered-alerts-count': recentlyTriggered
    };
    
    Object.entries(elements).forEach(([id, count]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = count;
            element.classList.add('metric-updated');
            setTimeout(() => element.classList.remove('metric-updated'), 500);
        }
    });
}

// Calculate alert health score
function calculateAlertHealthScore(alert) {
    let score = 100;
    
    // Deduct points for missing configurations
    if (!alert.email) score -= 20;
    if (!alert.notification_channels || alert.notification_channels.length === 0) score -= 15;
    if (!alert.notification_frequency) score -= 10;
    
    // Deduct points for problematic settings
    if (alert.notification_frequency === 'immediate' && (!alert.cooldown_period_hours || alert.cooldown_period_hours === 0)) {
        score -= 15; // Immediate alerts without cooldown are problematic
    }
    
    // Deduct points for being paused too long
    if (alert.status === 'paused') {
        score -= 30;
    }
    
    // Boost score for good configurations
    if (alert.notification_channels && alert.notification_channels.length > 1) {
        score += 5; // Multiple channels are good
    }
    
    if (alert.max_notifications_per_day && alert.max_notifications_per_day > 0) {
        score += 5; // Having daily limits is good
    }
    
    return Math.max(0, Math.min(100, score));
}

// Enhanced notification channels display
function getNotificationChannelsDisplay(alert) {
    const channels = alert.notification_channels || ['email'];
    const channelIcons = {
        'email': '<i class="fas fa-envelope text-primary"></i>',
        'slack': '<i class="fab fa-slack text-success"></i>',
        'inapp': '<i class="fas fa-bell text-info"></i>',
        'in_app': '<i class="fas fa-bell text-info"></i>'
    };
    
    const activeChannels = channels.map(channel => {
        const icon = channelIcons[channel] || '<i class="fas fa-question text-muted"></i>';
        const name = channel.charAt(0).toUpperCase() + channel.slice(1);
        const isConfigured = checkChannelConfiguration(channel);
        
        return `
            <div class="d-flex align-items-center mb-1">
                ${icon}
                <span class="ms-2 ${isConfigured ? 'text-success' : 'text-muted'}">${name}</span>
                ${isConfigured ? '<i class="fas fa-check text-success ms-1"></i>' : '<i class="fas fa-times text-muted ms-1"></i>'}
            </div>
        `;
    }).join('');
    
    return activeChannels;
}

// Check if notification channel is configured
function checkChannelConfiguration(channel) {
    switch(channel) {
        case 'email':
            return AlertsState.notificationChannels.email;
        case 'slack':
            return AlertsState.notificationChannels.slack;
        case 'inapp':
        case 'in_app':
            return AlertsState.notificationChannels.inApp;
        default:
            return false;
    }
}

// Enhanced test alert trigger functionality
function testAlertTrigger(clusterId) {
    if (!clusterId) {
        showNotification('No cluster selected', 'error');
        return;
    }
    
    const testCost = prompt('Enter test cost amount for alert testing:', '6000');
    if (!testCost || isNaN(testCost) || testCost <= 0) {
        showNotification('Invalid test cost amount', 'error');
        return;
    }
    
    showNotification(
        'Testing Alert Trigger',
        `Simulating budget breach with cost $${parseFloat(testCost).toLocaleString()}...`,
        'info'
    );
    
    fetch(`/api/alerts/test-trigger/${clusterId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            test_cost: parseFloat(testCost)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const triggeredCount = data.triggered_alerts || 0;
            showNotification(
                'Alert Test Complete',
                `Test completed successfully. ${triggeredCount} alerts were triggered.`,
                'success'
            );
            
            // Refresh alerts and notifications
            setTimeout(() => {
                loadAlerts();
                loadInAppNotifications();
            }, 1000);
        } else {
            throw new Error(data.message || 'Test failed');
        }
    })
    .catch(error => {
        console.error('❌ Alert test error:', error);
        showNotification(`Alert test failed: ${error.message}`, 'error');
    });
}

// Enhanced initialization with frequency setup
function initializeAlertsSystem() {
    console.log('🔔 Initializing enhanced alerts system with frequency management...');
    
    // First check if alerts system is available
    checkAlertsSystemStatus()
        .then(() => {
            if (AlertsState.systemAvailable) {
                // Load frequency configurations
                loadFrequencyConfigurations();
                
                // Check notification channel configurations
                checkNotificationChannels();
                
                // Load existing alerts
                loadAlerts();
                
                // Load in-app notifications
                loadInAppNotifications();
                
                // Setup event listeners
                setupAlertsEventListeners();
                
                // Setup frequency preview
                setTimeout(setupFrequencyPreview, 500);
                
                // Check if we're on a cluster-specific page
                const urlPath = window.location.pathname;
                const clusterMatch = urlPath.match(/\/cluster\/([^\/]+)/);
                if (clusterMatch) {
                    AlertsState.currentClusterId = clusterMatch[1];
                    loadClusterAlerts(AlertsState.currentClusterId);
                }
                
                // Setup periodic refresh
                if (AlertsState.systemAvailable) {
                    setInterval(() => {
                        loadInAppNotifications();
                        loadAlerts(); // Refresh alerts periodically
                    }, 30000);
                }
                
                console.log('✅ Enhanced alerts system with frequency management initialized');
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



console.log('✅ Enhanced alerts system JavaScript loaded with frequency management')

/**
 * Test alert notification with enhanced multi-channel support
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
                const channels = result.channels_tested || [];
                const channelsText = channels.length > 0 ? channels.join(', ') : 'unknown channels';
                showNotification(`Test notification sent successfully via: ${channelsText}!`, 'success');
                
                // Show detailed channel status
                if (result.email_configured !== undefined || result.slack_configured !== undefined) {
                    const channelStatus = [];
                    if (result.email_configured) channelStatus.push('✅ Email');
                    else channelStatus.push('❌ Email');
                    
                    if (result.slack_configured) channelStatus.push('✅ Slack');
                    else channelStatus.push('❌ Slack');
                    
                    if (result.in_app_available) channelStatus.push('✅ In-App');
                    
                    console.log(`📧 Channel status: ${channelStatus.join(', ')}`);
                }
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
 * Pause or resume alert with enhanced error handling
 */
function pauseResumeAlert(alertId, action) {
    if (!AlertsState.systemAvailable) {
        showNotification('Alerts system is currently unavailable', 'warning');
        return;
    }
    
    console.log(`⏸️ ${action} alert:`, alertId);
    
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
            showNotification(`Alert ${action}d successfully!`, 'success');
            
            // Update the alert in state
            const alert = AlertsState.alerts.find(a => a.id == alertId);
            if (alert) {
                alert.status = action === 'pause' ? 'paused' : 'active';
            }
            
            // Update the specific row in UI
            const alertRow = document.querySelector(`[data-alert-id="${alertId}"]`);
            if (alertRow) {
                alertRow.dataset.status = action === 'pause' ? 'paused' : 'active';
                
                // Update status badge
                const statusBadge = alertRow.querySelector('.col-span-1:first-child span');
                if (statusBadge) {
                    const newStatus = action === 'pause' ? 'paused' : 'active';
                    const colorClass = newStatus === 'active' ? 'green' : 'yellow';
                    statusBadge.className = `text-xs px-2 py-1 bg-${colorClass}-100 text-${colorClass}-700 rounded uppercase font-medium`;
                    statusBadge.textContent = newStatus.toUpperCase();
                }
                
                // Update the toggle
                const toggle = alertRow.querySelector('input[type="checkbox"]');
                if (toggle) {
                    toggle.checked = action === 'resume';
                }
            }
            
            // Update filter counts
            updateFilterCounts();
            
            createLocalInAppNotification(
                `Alert ${action.charAt(0).toUpperCase() + action.slice(1)}d`,
                `Alert ${alertId} has been ${action}d successfully`,
                'info'
            );
        } else {
            throw new Error(result.message || `Failed to ${action} alert`);
        }
    })
    .catch(error => {
        console.error(`❌ Error ${action}ing alert:`, error);
        showNotification(`Failed to ${action} alert: ${error.message}`, 'error');
        
        // Revert the toggle
        const alertRow = document.querySelector(`[data-alert-id="${alertId}"]`);
        if (alertRow) {
            const toggle = alertRow.querySelector('input[type="checkbox"]');
            if (toggle) {
                toggle.checked = !toggle.checked; // Revert
            }
        }
    });
}

/**
 * Test Slack notification (RESTORED FUNCTION)
 */
function testSlackNotification() {
    if (!AlertsState.systemAvailable) {
        showNotification('Alerts system is currently unavailable', 'warning');
        return;
    }
    
    if (!AlertsState.notificationChannels.slack) {
        showNotification('Slack integration not configured. Please set SLACK_WEBHOOK_URL environment variable.', 'warning');
        return;
    }
    
    const button = document.getElementById('test-slack-btn');
    if (button) {
        const originalContent = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Testing...';
        button.disabled = true;
        
        fetch('/api/notifications/slack/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: 'Test Slack Integration',
                message: 'This is a test message from AKS Cost Intelligence alerts system.'
            })
        })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                showNotification('Slack test notification sent successfully!', 'success');
            } else {
                throw new Error(result.message || 'Failed to send Slack test');
            }
        })
        .catch(error => {
            console.error('❌ Error testing Slack:', error);
            showNotification(`Slack test failed: ${error.message}`, 'error');
        })
        .finally(() => {
            button.innerHTML = originalContent;
            button.disabled = false;
        });
    }
}

// ============================================================================
// ADVANCED ALERTS MODAL FUNCTIONALITY (RESTORED FUNCTIONS)
// ============================================================================

/**
 * Show advanced alerts modal
 */
function showAdvancedAlertsModal() {
    console.log('🔧 Showing advanced alerts modal');
    
    const frequencyOptions = Object.keys(AlertsState.frequencyMap).map(key => {
        const info = getFrequencyInfo(key);
        return `
            <option value="${key}" ${key === AlertsState.defaultFrequency ? 'selected' : ''}>
                ${info.display} - ${info.description}
            </option>
        `;
    }).join('');
    
    const modalHTML = `
        <div class="modal fade" id="advancedAlertsModal" tabindex="-1" 
             aria-labelledby="advancedAlertsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title" id="advancedAlertsModalLabel">
                            <i class="fas fa-cog me-2"></i>Advanced Alerts Configuration
                        </h5>
                        <button type="button" class="btn-close btn-close-white" 
                                onclick="closeAdvancedAlertsModal()" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="advanced-alerts-form">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Alert Name</label>
                                        <input type="text" class="form-control" name="name" required 
                                               placeholder="My Custom Alert">
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
                                        <input type="number" class="form-control" name="threshold_amount" 
                                               min="0" step="0.01" placeholder="1000">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Threshold Percentage (%)</label>
                                        <input type="number" class="form-control" name="threshold_percentage" 
                                               min="0" max="100" placeholder="80">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-8">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Email Address</label>
                                        <input type="email" class="form-control" name="email" required 
                                               placeholder="alerts@company.com">
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="form-group mb-3">
                                        <label class="form-label">
                                            <i class="fas fa-clock me-1"></i>Notification Frequency
                                        </label>
                                        <select class="form-select" name="notification_frequency" id="frequency-select">
                                            ${frequencyOptions}
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <!-- Notification Channels Selection -->
                            <div class="mb-3">
                                <label class="form-label">Notification Channels</label>
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" 
                                                   name="channels" value="email" id="channel-email" checked>
                                            <label class="form-check-label" for="channel-email">
                                                <i class="fas fa-envelope me-1"></i>Email
                                            </label>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" 
                                                   name="channels" value="slack" id="channel-slack" 
                                                   ${AlertsState.notificationChannels.slack ? 'checked' : ''}>
                                            <label class="form-check-label" for="channel-slack">
                                                <i class="fab fa-slack me-1"></i>Slack
                                            </label>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" 
                                                   name="channels" value="inapp" id="channel-inapp" checked>
                                            <label class="form-check-label" for="channel-inapp">
                                                <i class="fas fa-bell me-1"></i>In-App
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="closeAdvancedAlertsModal()">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="handleAdvancedAlertCreation()">
                            <i class="fas fa-plus me-2"></i>Create Advanced Alert
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
    
    // Update notification channels status in modal
    updateNotificationChannelsUI();
    
    // Show modal using Bootstrap helper
    const modalElement = document.getElementById('advancedAlertsModal');
    window.currentAdvancedModal = BootstrapHelper.showModal(modalElement);
    
    console.log('✅ Advanced alerts modal shown successfully');
}

function closeAdvancedAlertsModal() {
    const modalElement = document.getElementById('advancedAlertsModal');
    if (modalElement) {
        BootstrapHelper.hideModal(modalElement);
        
        // Remove from DOM after animation
        setTimeout(() => {
            modalElement.remove();
        }, 300);
    }
    window.currentAdvancedModal = null;
}

function setupFrequencyPreview() {
    const frequencySelect = document.getElementById('notification-frequency');
    const previewText = document.getElementById('frequency-preview-text');
    const notificationTime = document.getElementById('notification-time');
    const maxNotifications = document.getElementById('max-notifications');
    const cooldownPeriod = document.getElementById('cooldown-period');
    
    function updateFrequencyPreview() {
        const frequency = frequencySelect?.value || 'daily';
        const time = notificationTime?.value || '09:00';
        const maxPerDay = maxNotifications?.value || '3';
        const cooldown = cooldownPeriod?.value || '4';
        
        const frequencyInfo = getFrequencyInfo(frequency);
        let preview = `<strong>${frequencyInfo.display}:</strong> ${frequencyInfo.description}`;
        
        // Add specific timing information
        if (frequency === 'daily') {
            preview += `<br><i class="fas fa-clock me-1"></i>Will send daily notifications at ${time}`;
        } else if (frequency === 'weekly') {
            preview += `<br><i class="fas fa-calendar-week me-1"></i>Will send weekly notifications on Mondays at ${time}`;
        } else if (frequency === 'immediate') {
            preview += `<br><i class="fas fa-bolt me-1"></i>Notifications sent immediately when budget threshold is crossed`;
        }
        
        // Add limits information
        if (maxPerDay && maxPerDay !== '') {
            preview += `<br><i class="fas fa-limit me-1"></i>Maximum ${maxPerDay} notifications per day`;
        }
        
        if (cooldown && cooldown !== '0') {
            preview += `<br><i class="fas fa-pause-circle me-1"></i>Minimum ${cooldown} hour(s) between notifications`;
        }
        
        // Add recommendation
        if (frequency === 'immediate' && (!cooldown || cooldown === '0')) {
            preview += `<br><span class="text-warning"><i class="fas fa-exclamation-triangle me-1"></i>Recommendation: Add cooldown period to prevent spam</span>`;
        }
        
        if (previewText) {
            previewText.innerHTML = preview;
        }
    }
    
    // Update preview when any setting changes
    [frequencySelect, notificationTime, maxNotifications, cooldownPeriod].forEach(element => {
        if (element) {
            element.addEventListener('change', updateFrequencyPreview);
        }
    });
    
    // Initial preview
    updateFrequencyPreview();
}

function setupEditFrequencyPreview() {
    const frequencySelect = document.getElementById('edit-frequency-select');
    const previewText = document.getElementById('edit-frequency-preview-text');
    
    function updatePreview() {
        const frequency = frequencySelect.value;
        const frequencyInfo = getFrequencyInfo(frequency);
        const maxPerDay = document.querySelector('#editFrequencyModal [name="max_notifications_per_day"]').value;
        const cooldown = document.querySelector('#editFrequencyModal [name="cooldown_period_hours"]').value;
        const atTime = document.querySelector('#editFrequencyModal [name="frequency_at_time"]').value;
        
        let preview = `<strong>${frequencyInfo.display}:</strong> ${frequencyInfo.description}`;
        
        if (frequency === 'daily' && atTime) {
            preview += `<br><i class="fas fa-clock me-1"></i>Will send daily notifications at ${atTime}`;
        }
        
        if (maxPerDay) {
            preview += `<br><i class="fas fa-limit me-1"></i>Maximum ${maxPerDay} notifications per day`;
        }
        
        if (cooldown && cooldown > 0) {
            preview += `<br><i class="fas fa-pause-circle me-1"></i>Minimum ${cooldown} hour(s) between notifications`;
        }
        
        previewText.innerHTML = preview;
    }
    
    // Update preview when frequency changes
    frequencySelect.addEventListener('change', updatePreview);
    document.querySelector('#editFrequencyModal [name="max_notifications_per_day"]').addEventListener('change', updatePreview);
    document.querySelector('#editFrequencyModal [name="cooldown_period_hours"]').addEventListener('change', updatePreview);
    document.querySelector('#editFrequencyModal [name="frequency_at_time"]').addEventListener('change', updatePreview);
    
    // Initial preview
    updatePreview();
}

function saveFrequencySettings(alertId) {
    const form = document.getElementById('edit-frequency-form');
    const formData = new FormData(form);
    
    const updates = {
        notification_frequency: formData.get('notification_frequency'),
        frequency_at_time: formData.get('frequency_at_time'),
        max_notifications_per_day: parseInt(formData.get('max_notifications_per_day')) || null,
        cooldown_period_hours: parseInt(formData.get('cooldown_period_hours')) || 0
    };
    
    const button = document.querySelector('#editFrequencyModal .btn-primary');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
    button.disabled = true;
    
    fetch(`/api/alerts/${alertId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        if (result.status === 'success') {
            showNotification('Frequency settings saved successfully!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editFrequencyModal'));
            modal.hide();
            
            // Refresh alerts list
            loadAlerts();
        } else {
            throw new Error(result.message || 'Failed to save frequency settings');
        }
    })
    .catch(error => {
        console.error('❌ Error saving frequency settings:', error);
        showNotification(`Failed to save frequency settings: ${error.message}`, 'error');
    })
    .finally(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

/**
 * Handle advanced alert creation (RESTORED FUNCTION)
 */
function handleAdvancedAlertCreation() {
    console.log('🔧 Creating advanced alert');
    
    const form = document.getElementById('advanced-alerts-form');
    const formData = new FormData(form);
    
    // Get selected notification channels
    const selectedChannels = [];
    const channelCheckboxes = form.querySelectorAll('input[name="channels"]:checked');
    channelCheckboxes.forEach(checkbox => {
        selectedChannels.push(checkbox.value);
    });
    
    const alertData = {
        name: formData.get('name'),
        alert_type: formData.get('alert_type'),
        threshold_amount: parseFloat(formData.get('threshold_amount')) || 0,
        threshold_percentage: parseFloat(formData.get('threshold_percentage')) || 0,
        email: formData.get('email'),
        notification_frequency: formData.get('notification_frequency') || AlertsState.defaultFrequency,
        cluster_id: AlertsState.currentClusterId,
        notification_channels: selectedChannels
    };
    
    // Validation
    if (!alertData.name) {
        showNotification('Please enter an alert name', 'error');
        return;
    }
    
    if (!alertData.email || !isValidEmail(alertData.email)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }
    
    if (alertData.threshold_amount <= 0 && alertData.threshold_percentage <= 0) {
        showNotification('Please set either a threshold amount or percentage', 'error');
        return;
    }
    
    // Show loading state
    const createBtn = document.querySelector('#advancedAlertsModal .btn-primary');
    const originalText = createBtn.innerHTML;
    createBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating...';
    createBtn.disabled = true;
    
    createAlert(alertData)
        .then(result => {
            if (result.status === 'success') {
                const frequencyInfo = getFrequencyInfo(alertData.notification_frequency);
                showNotification(`Advanced alert created with ${frequencyInfo.display} frequency!`, 'success');
                
                // Close modal
                closeAdvancedAlertsModal();
                
                // Refresh alerts
                loadAlerts();
                
                // Send in-app notification
                createLocalInAppNotification(
                    'Advanced Alert Created',
                    `Alert "${alertData.name}" has been created with ${frequencyInfo.display} frequency and ${selectedChannels.length} notification channel(s)`,
                    'success'
                );
            } else {
                throw new Error(result.message || 'Failed to create alert');
            }
        })
        .catch(error => {
            console.error('❌ Error creating advanced alert:', error);
            showNotification(`Failed to create alert: ${error.message}`, 'error');
        })
        .finally(() => {
            createBtn.innerHTML = originalText;
            createBtn.disabled = false;
        });
}



/**
 * Dismiss toast notification
 */
function dismissToast(toastId) {
    const toastElement = document.getElementById(toastId);
    if (toastElement) {
        toastElement.style.transition = 'all 0.3s ease-out';
        toastElement.style.opacity = '0';
        toastElement.style.transform = 'translateX(100%)';
        
        setTimeout(() => {
            if (toastElement.parentNode) {
                toastElement.remove();
            }
            // Reposition remaining toasts
            repositionToasts();
        }, 300);
    }
}

function repositionToasts() {
    const toasts = document.querySelectorAll('[id^="toast-"]');
    toasts.forEach((toast, index) => {
        toast.style.top = `${20 + (index * 80)}px`;
    });
}

window.showDeleteAlertModal = showDeleteAlertModal;
window.closeDeleteAlertModal = closeDeleteAlertModal;
window.confirmDeleteAlert = confirmDeleteAlert;
window.showAdvancedAlertsModal = showAdvancedAlertsModal;
window.closeAdvancedAlertsModal = closeAdvancedAlertsModal;
window.handleAdvancedAlertCreation = handleAdvancedAlertCreation;

// Fixed notification functions
window.showEnhancedNotification = showEnhancedNotification;
window.dismissToast = dismissToast;

// Bootstrap helper
window.BootstrapHelper = BootstrapHelper;

/**
 * ============================================================================
 * SIMPLE FALLBACK DELETE CONFIRMATION (NO BOOTSTRAP REQUIRED)
 * ============================================================================
 */

/**
 * Simple delete confirmation using browser confirm dialog
 */
function simpleDeleteAlert(alertId) {
    const alert = AlertsState.alerts.find(a => a.id == alertId);
    const alertName = alert ? alert.name : `Alert ${alertId}`;
    
    const confirmed = confirm(
        `Are you sure you want to delete "${alertName}"?\n\n` +
        `This action cannot be undone. The alert will be permanently removed ` +
        `and will no longer monitor your cluster costs.`
    );
    
    if (confirmed) {
        executeAlertDeletion(alertId);
    }
}

/**
 * Update the deleteAlert function to use simple confirmation if Bootstrap fails
 */
function deleteAlert(alertId) {
    console.log('🗑️ Delete alert requested:', alertId);
    
    try {
        // Try to show the enhanced modal first
        const alert = AlertsState.alerts.find(a => a.id == alertId);
        const alertName = alert ? alert.name : `Alert ${alertId}`;
        showDeleteAlertModal(alertId, alertName);
    } catch (error) {
        console.warn('⚠️ Enhanced modal failed, using simple confirmation:', error);
        // Fallback to simple confirmation
        simpleDeleteAlert(alertId);
    }
}

// Export the updated delete function
window.deleteAlert = deleteAlert;
window.simpleDeleteAlert = simpleDeleteAlert;

/**
 * ============================================================================
 * CSS FALLBACK STYLES FOR NON-BOOTSTRAP MODALS
 * ============================================================================
 */

const fallbackModalCSS = `
<style>
/* Fallback modal styles when Bootstrap is not available */
.modal {
    display: none;
    position: fixed;
    z-index: 1050;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    outline: 0;
}

.modal.show {
    display: block !important;
}

.modal-dialog {
    position: relative;
    width: auto;
    margin: 0.5rem;
    pointer-events: none;
}

.modal-dialog-centered {
    display: flex;
    align-items: center;
    min-height: calc(100% - 1rem);
}

.modal-content {
    position: relative;
    display: flex;
    flex-direction: column;
    width: 100%;
    pointer-events: auto;
    background-color: #fff;
    background-clip: padding-box;
    border: 1px solid rgba(0, 0, 0, 0.2);
    border-radius: 0.3rem;
    outline: 0;
}

.modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1040;
    width: 100vw;
    height: 100vh;
    background-color: #000;
    opacity: 0.5;
}

.modal-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 1rem 1rem;
    border-bottom: 1px solid #dee2e6;
    border-top-left-radius: calc(0.3rem - 1px);
    border-top-right-radius: calc(0.3rem - 1px);
}

.modal-body {
    position: relative;
    flex: 1 1 auto;
    padding: 1rem;
}

.modal-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding: 0.75rem;
    border-top: 1px solid #dee2e6;
    border-bottom-right-radius: calc(0.3rem - 1px);
    border-bottom-left-radius: calc(0.3rem - 1px);
}

.btn-close {
    background: transparent url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%23000'%3e%3cpath d='m.235 1.027 4.73 4.73 4.73-4.74c.377-.377.99-.377 1.367 0s.377.99 0 1.367L6.33 6.117l4.73 4.73c.377.377.377.99 0 1.367s-.99.377-1.367 0L5.063 7.484.333 12.214c-.377.377-.99.377-1.367 0s-.377-.99 0-1.367L3.696 6.117-.034 1.387C-.41 1.01-.41.397.033-.046s.99-.377 1.367 0z'/%3e%3c/svg%3e") center/1em auto no-repeat;
    border: 0;
    border-radius: 0.25rem;
    opacity: 0.5;
    width: 1em;
    height: 1em;
    padding: 0.25em 0.25em;
    margin: -0.125rem -0.125rem -0.125rem auto;
}

.btn-close:hover {
    color: #000;
    text-decoration: none;
    opacity: 0.75;
}

.modal-open {
    overflow: hidden;
}

/* Toast fallback styles */
.toast {
    position: relative;
    max-width: 350px;
    font-size: 0.875rem;
    background-color: rgba(255, 255, 255, 0.85);
    background-clip: padding-box;
    border: 1px solid rgba(0, 0, 0, 0.1);
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    backdrop-filter: blur(10px);
    border-radius: 0.25rem;
    opacity: 0;
    transition: opacity 0.15s ease-in-out;
}

.toast.show {
    opacity: 1;
}

.toast-body {
    padding: 0.75rem;
}

/* Responsive modal for mobile */
@media (min-width: 576px) {
    .modal-dialog {
        max-width: 500px;
        margin: 1.75rem auto;
    }
    
    .modal-dialog-centered {
        min-height: calc(100% - 3.5rem);
    }
}

@media (min-width: 992px) {
    .modal-xl {
        max-width: 1140px;
    }
}
</style>
`;

// Inject fallback CSS
document.head.insertAdjacentHTML('beforeend', fallbackModalCSS);

console.log('✅ Bootstrap fallback system loaded - alerts will work with or without Bootstrap');



// ============================================================================
// ENHANCED DELETE ALERT MODAL - MODERN CONFIRMATION DIALOG
// ============================================================================

/**
 * Show enhanced delete confirmation modal
 */
function showDeleteAlertModal(alertId, alertName) {
    console.log('🗑️ Showing simple delete modal for alert:', alertId);
    
    const alert = AlertsState.alerts.find(a => a.id == alertId);
    const alertDisplayName = alertName || (alert ? alert.name : `Alert ${alertId}`);
    
    const modalHTML = `
        <div class="modal fade" id="deleteAlertModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered modal-sm">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-danger text-white border-0 text-center">
                        <h6 class="modal-title w-100">
                            <i class="fas fa-trash-alt me-2"></i>Delete Alert
                        </h6>
                        <button type="button" class="btn-close btn-close-white" 
                                onclick="closeDeleteAlertModal()" aria-label="Close"></button>
                    </div>
                    <div class="modal-body text-center p-4">
                        <div class="mb-3">
                            <i class="fas fa-exclamation-triangle text-warning fa-2x mb-2"></i>
                            <p class="mb-1"><strong>Delete "${escapeHtml(alertDisplayName)}"?</strong></p>
                            <small class="text-muted">This action cannot be undone.</small>
                        </div>
                    </div>
                    <div class="modal-footer border-0 pt-0">
                        <div class="w-100 d-flex gap-2">
                            <button type="button" class="btn btn-secondary flex-fill" onclick="closeDeleteAlertModal()">
                                Cancel
                            </button>
                            <button type="button" class="btn btn-danger flex-fill" 
                                    onclick="confirmDeleteAlert(${alertId})" data-alert-id="${alertId}">
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('deleteAlertModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Show modal
    const modalElement = document.getElementById('deleteAlertModal');
    window.currentDeleteModal = BootstrapHelper.showModal(modalElement);
}

/**
 * Confirm and execute alert deletion
 */
function confirmDeleteAlert(alertId) {
    console.log('🗑️ Confirming delete for alert:', alertId);
    
    const deleteBtn = document.querySelector(`[data-alert-id="${alertId}"]`);
    
    if (deleteBtn) {
        // Show loading state
        const originalContent = deleteBtn.innerHTML;
        deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Deleting...';
        deleteBtn.disabled = true;
        
        // Close modal first
        closeDeleteAlertModal();
        
        // Execute the actual deletion
        executeAlertDeletion(alertId)
            .then(() => {
                console.log('✅ Alert deleted successfully');
            })
            .catch(error => {
                console.error('❌ Delete confirmation error:', error);
                // Restore button state
                if (deleteBtn) {
                    deleteBtn.innerHTML = originalContent;
                    deleteBtn.disabled = false;
                }
            });
    }
}

/**
 * Execute the actual alert deletion (separated from UI logic)
 */
function executeAlertDeletion(alertId) {
    return new Promise((resolve, reject) => {
        if (!AlertsState.systemAvailable) {
            showNotification('Alerts system is currently unavailable', 'warning');
            reject(new Error('System unavailable'));
            return;
        }
        
        console.log('🗑️ Deleting specific alert:', alertId);
        
        // Find the specific alert item
        const alertItem = document.querySelector(`[data-alert-id="${alertId}"].alert-row`);
        
        if (alertItem) {
            // Add deletion animation to ONLY this alert
            alertItem.style.transition = 'all 0.3s ease-out';
            alertItem.style.opacity = '0.5';
            alertItem.style.transform = 'scale(0.95)';
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
                    // Success animation for ONLY this alert
                    alertItem.style.transition = 'all 0.5s ease-out';
                    alertItem.style.opacity = '0';
                    alertItem.style.transform = 'translateX(-100%) scale(0.8)';
                    
                    setTimeout(() => {
                        // Remove ONLY this alert from DOM
                        alertItem.remove();
                        
                        // Remove from AlertsState
                        AlertsState.alerts = AlertsState.alerts.filter(a => a.id != alertId);
                        
                        // Update counters
                        updateFilterCounts();
                        
                        // Show empty state if no alerts left
                        if (AlertsState.alerts.length === 0) {
                            displayAlerts([]);
                        }
                    }, 500);
                    
                    showEnhancedNotification('success', 'Alert Deleted', 
                        `Alert has been successfully deleted`);
                    
                    createLocalInAppNotification(
                        'Alert Deleted',
                        `Alert ${alertId} has been deleted successfully`,
                        'warning'
                    );
                    
                    resolve(result);
                } else {
                    throw new Error(result.message || 'Failed to delete alert');
                }
            })
            .catch(error => {
                console.error('❌ Error deleting alert:', error);
                
                // Restore UI state for ONLY this alert
                alertItem.style.transition = 'all 0.3s ease-out';
                alertItem.style.opacity = '1';
                alertItem.style.transform = 'scale(1)';
                alertItem.style.pointerEvents = 'auto';
                
                showEnhancedNotification('error', 'Delete Failed', 
                    `Failed to delete alert: ${error.message}`);
                
                reject(error);
            });
        } else {
            reject(new Error('Alert item not found in UI'));
        }
    });
}

/**
 * Enhanced notification function with better styling
 */
function showEnhancedNotification(type, title, message) {
    console.log(`📢 Showing notification: ${title} - ${message} (${type})`);
    
    // Try existing system first
    if (window.smoothNotificationManager) {
        window.smoothNotificationManager.show(`${title}: ${message}`, type);
        return;
    }
    
    // Create fixed-position toast
    const toastId = `toast-${Date.now()}`;
    const iconClass = {
        'success': 'fas fa-check-circle text-success',
        'error': 'fas fa-times-circle text-danger',
        'warning': 'fas fa-exclamation-triangle text-warning',
        'info': 'fas fa-info-circle text-info'
    }[type] || 'fas fa-info-circle text-info';
    
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger', 
        'warning': 'bg-warning',
        'info': 'bg-info'
    }[type] || 'bg-info';
    
    // Count existing toasts to stack them
    const existingToasts = document.querySelectorAll('[id^="toast-"]').length;
    const topPosition = 20 + (existingToasts * 80);
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0 shadow-lg" 
             role="alert" aria-live="assertive" aria-atomic="true" 
             style="position: fixed; top: ${topPosition}px; right: 20px; z-index: 9999; min-width: 350px; max-width: 400px;">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center">
                    <i class="${iconClass} me-2"></i>
                    <div>
                        <div class="fw-bold">${escapeHtml(title)}</div>
                        <div class="small">${escapeHtml(message)}</div>
                    </div>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        onclick="dismissToast('${toastId}')" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    toastElement.style.opacity = '0';
    toastElement.style.transform = 'translateX(100%)';
    
    // Animate in
    setTimeout(() => {
        toastElement.style.transition = 'all 0.3s ease-out';
        toastElement.style.opacity = '1';
        toastElement.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto remove
    setTimeout(() => {
        dismissToast(toastId);
    }, type === 'error' ? 8000 : 5000);
}

/**
 * Update the existing deleteAlert function to use the new modal
 */
function deleteAlert(alertId) {
    // Get alert details for better UX
    const alert = AlertsState.alerts.find(a => a.id == alertId);
    const alertName = alert ? alert.name : `Alert ${alertId}`;
    
    // Show the enhanced modal instead of basic confirm
    showDeleteAlertModal(alertId, alertName);
}

// ============================================================================
// MISSING FUNCTIONS FIX - ADDITIONAL NOTIFICATION FUNCTIONS
// ============================================================================

/**
 * Mark all notifications as read (MISSING FUNCTION)
 */
function markAllNotificationsAsRead() {
    if (!AlertsState.systemAvailable) {
        showNotification('Alerts system is currently unavailable', 'warning');
        return;
    }
    
    const unreadIds = AlertsState.inAppNotifications
        .filter(n => !n.read)
        .map(n => n.id);
    
    if (unreadIds.length === 0) {
        showNotification('No unread notifications to mark as read', 'info');
        return;
    }
    
    // Show loading state if there's a button
    const markAllBtn = document.querySelector('[onclick*="markAllNotificationsAsRead"]');
    if (markAllBtn) {
        const originalText = markAllBtn.innerHTML;
        markAllBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Marking all as read...';
        markAllBtn.disabled = true;
        
        // Restore button after operation
        setTimeout(() => {
            markAllBtn.innerHTML = originalText;
            markAllBtn.disabled = false;
        }, 2000);
    }
    
    fetch('/api/notifications/in-app', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            notification_ids: unreadIds,
            action: 'mark_read'
        })
    })
    .then(response => {
        if (response.status === 404) {
            // Endpoint doesn't exist, just update locally
            console.log('ℹ️ In-app notifications API not available - updating locally');
            markAllNotificationsAsReadLocally(unreadIds);
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.status === 'success') {
            markAllNotificationsAsReadLocally(unreadIds);
            showNotification(`Marked ${unreadIds.length} notifications as read`, 'success');
        } else if (data) {
            showNotification('Failed to mark notifications as read', 'error');
        }
    })
    .catch(error => {
        console.log('ℹ️ Marking all notifications as read locally:', error.message);
        markAllNotificationsAsReadLocally(unreadIds);
        showNotification(`Marked ${unreadIds.length} notifications as read (locally)`, 'success');
    });
}

/**
 * Mark all notifications as read locally
 */
function markAllNotificationsAsReadLocally(unreadIds) {
    AlertsState.inAppNotifications.forEach(n => {
        if (unreadIds.includes(n.id)) {
            n.read = true;
        }
    });
    AlertsState.unreadNotificationsCount = 0;
    updateInAppNotificationsUI();
    updateNotificationBadge();
}

/**
 * Clear all notifications (MISSING FUNCTION)
 */
function clearAllNotifications() {
    if (!AlertsState.systemAvailable) {
        showNotification('Alerts system is currently unavailable', 'warning');
        return;
    }
    
    if (AlertsState.inAppNotifications.length === 0) {
        showNotification('No notifications to clear', 'info');
        return;
    }
    
    if (!confirm('Are you sure you want to clear all notifications? This cannot be undone.')) {
        return;
    }
    
    // Clear locally immediately for better UX
    const clearedCount = AlertsState.inAppNotifications.length;
    AlertsState.inAppNotifications = [];
    AlertsState.unreadNotificationsCount = 0;
    updateInAppNotificationsUI();
    updateNotificationBadge();
    
    showNotification(`Cleared ${clearedCount} notifications`, 'success');
}

/**
 * Export configuration (MISSING FUNCTION)
 */
function exportAlertsConfig() {
    showNotification('Exporting alerts configuration...', 'info');
    
    const config = {
        alerts: AlertsState.alerts,
        notification_channels: AlertsState.notificationChannels,
        exported_at: new Date().toISOString(),
        cluster_id: AlertsState.currentClusterId,
        system_status: {
            available: AlertsState.systemAvailable,
            email_configured: AlertsState.notificationChannels.email,
            slack_configured: AlertsState.notificationChannels.slack
        }
    };
    
    const configContent = JSON.stringify(config, null, 2);
    const blob = new Blob([configContent], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `alerts_config_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    showNotification('Alerts configuration exported successfully!', 'success');
}
// Simplified alert display function
// function displayAlertsSimplified(alerts) {
//     const container = document.getElementById('alerts-list-container');
//     if (!container) return;
    
//     if (alerts.length === 0) {
//         container.innerHTML = `
//             <div class="text-center py-8 text-gray-500">
//                 <i class="fas fa-bell-slash text-3xl mb-2"></i>
//                 <p>No alerts configured</p>
//                 <button onclick="showCreateAlertModal()" class="mt-2 text-blue-500 hover:text-blue-600">
//                     Create your first alert
//                 </button>
//             </div>
//         `;
//         return;
//     }

//     const alertsHTML = alerts.map(alert => {
//         const statusColor = alert.status === 'active' ? 'green' : alert.status === 'paused' ? 'yellow' : 'gray';
//         const statusIcon = alert.status === 'active' ? 'play' : alert.status === 'paused' ? 'pause' : 'stop';
        
//         return `
//             <div class="alert-item bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all duration-200" 
//                  data-alert-id="${alert.id}" 
//                  data-status="${alert.status || 'active'}">
//                 <div class="flex items-center justify-between">
//                     <div class="flex-1">
//                         <div class="flex items-center space-x-2 mb-2">
//                             <div class="w-3 h-3 bg-${statusColor}-500 rounded-full"></div>
//                             <h4 class="font-medium text-gray-900">${escapeHtml(alert.name)}</h4>
//                             <span class="text-xs px-2 py-1 bg-${statusColor}-100 text-${statusColor}-700 rounded-full uppercase font-medium">
//                                 ${alert.status || 'active'}
//                             </span>
//                         </div>
//                         <div class="text-sm text-gray-600 space-y-1">
//                             ${alert.threshold_amount > 0 ? `<div><span class="font-medium">Budget:</span> $${alert.threshold_amount.toLocaleString()}</div>` : ''}
//                             ${alert.email ? `<div><span class="font-medium">Email:</span> ${escapeHtml(alert.email)}</div>` : ''}
//                             ${alert.cluster_name ? `<div><span class="font-medium">Cluster:</span> ${escapeHtml(alert.cluster_name)}</div>` : ''}
//                         </div>
//                     </div>
                    
//                     <!-- Three dots menu -->
//                     <div class="relative">
//                         <button onclick="toggleAlertMenu('${alert.id}')" class="text-gray-400 hover:text-gray-600 p-2">
//                             <i class="fas fa-ellipsis-v"></i>
//                         </button>
//                         <div id="menu-${alert.id}" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200">
//                             <div class="py-1">
//                                 <button onclick="viewAlert('${alert.id}')" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
//                                     <i class="fas fa-eye mr-2"></i>View Details
//                                 </button>
//                                 <button onclick="testAlert('${alert.id}')" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
//                                     <i class="fas fa-paper-plane mr-2"></i>Test Alert
//                                 </button>
//                                 <button onclick="pauseResumeAlert('${alert.id}', '${alert.status === 'active' ? 'pause' : 'resume'}')" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
//                                     <i class="fas fa-${alert.status === 'active' ? 'pause' : 'play'} mr-2"></i>${alert.status === 'active' ? 'Pause' : 'Resume'}
//                                 </button>
//                                 <hr class="my-1">
//                                 <button onclick="deleteAlert('${alert.id}')" class="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50">
//                                     <i class="fas fa-trash mr-2"></i>Delete
//                                 </button>
//                             </div>
//                         </div>
//                     </div>
//                 </div>
//             </div>
//         `;
//     }).join('');
    
//     container.innerHTML = alertsHTML;
// }

// Toggle alert menu
function toggleAlertMenu(alertId) {
    // Close all other menus first
    document.querySelectorAll('[id^="menu-"]').forEach(menu => {
        if (menu.id !== `menu-${alertId}`) {
            menu.classList.add('hidden');
        }
    });
    
    // Toggle current menu
    const menu = document.getElementById(`menu-${alertId}`);
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

// Close menus when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('[id^="menu-"]') && !event.target.closest('button[onclick*="toggleAlertMenu"]')) {
        document.querySelectorAll('[id^="menu-"]').forEach(menu => {
            menu.classList.add('hidden');
        });
    }
});

// Create alert modal
function showCreateAlertModal() {
    console.log('➕ Showing enhanced create alert modal');
    
    const modalHTML = `
        <div id="createAlertModal" class="modal fade" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-success text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-plus me-2"></i>Create New Alert
                        </h5>
                        <button type="button" class="btn-close btn-close-white" 
                                onclick="closeCreateAlertModal()" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="create-alert-form">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Alert Name *</label>
                                        <input type="text" class="form-control" name="name" required 
                                               placeholder="Monthly Budget Alert">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Email Address *</label>
                                        <input type="email" class="form-control" name="email" required 
                                               placeholder="admin@company.com">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Threshold Type *</label>
                                        <select class="form-select" name="threshold_type" id="threshold-type" 
                                                onchange="updateThresholdInput()" required>
                                            <option value="">Select threshold type</option>
                                            <option value="amount">Fixed Amount ($)</option>
                                            <option value="percentage">Percentage (%)</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label" id="threshold-label">Threshold Value *</label>
                                        <div class="input-group">
                                            <span class="input-group-text" id="threshold-symbol">$</span>
                                            <input type="number" class="form-control" name="threshold_value" 
                                                   id="threshold-input" required placeholder="5000" min="0" step="0.01">
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Notification Frequency</label>
                                        <select class="form-select" name="notification_frequency">
                                            <option value="immediate">Immediate</option>
                                            <option value="hourly">Hourly</option>
                                            <option value="daily" selected>Daily</option>
                                            <option value="weekly">Weekly</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Alert Type</label>
                                        <select class="form-select" name="alert_type">
                                            <option value="cost_threshold">Cost Threshold</option>
                                            <option value="performance">Performance</option>
                                            <option value="optimization">Optimization</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Notification Channels -->
                            <div class="mb-3">
                                <label class="form-label">Notification Channels</label>
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" 
                                                   name="channels" value="email" id="channel-email" checked>
                                            <label class="form-check-label" for="channel-email">
                                                <i class="fas fa-envelope me-1"></i>Email
                                            </label>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" 
                                                   name="channels" value="slack" id="channel-slack">
                                            <label class="form-check-label" for="channel-slack">
                                                <i class="fab fa-slack me-1"></i>Slack
                                            </label>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" 
                                                   name="channels" value="inapp" id="channel-inapp" checked>
                                            <label class="form-check-label" for="channel-inapp">
                                                <i class="fas fa-bell me-1"></i>In-App
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="closeCreateAlertModal()">
                            Cancel
                        </button>
                        <button type="button" class="btn btn-success" onclick="handleCreateAlertSubmission()">
                            <i class="fas fa-plus me-2"></i>Create Alert
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    const modalElement = document.getElementById('createAlertModal');
    BootstrapHelper.showModal(modalElement);
}

function updateThresholdInput() {
    const thresholdType = document.getElementById('threshold-type').value;
    const thresholdSymbol = document.getElementById('threshold-symbol');
    const thresholdInput = document.getElementById('threshold-input');
    const thresholdLabel = document.getElementById('threshold-label');
    
    if (thresholdType === 'amount') {
        thresholdSymbol.textContent = '$';
        thresholdInput.placeholder = '5000';
        thresholdInput.step = '0.01';
        thresholdInput.max = '';
        thresholdLabel.textContent = 'Threshold Amount *';
    } else if (thresholdType === 'percentage') {
        thresholdSymbol.textContent = '%';
        thresholdInput.placeholder = '80';
        thresholdInput.step = '1';
        thresholdInput.max = '100';
        thresholdLabel.textContent = 'Threshold Percentage *';
    }
}

function closeCreateAlertModal() {
    const modal = document.getElementById('createAlertModal');
    if (modal) {
        BootstrapHelper.hideModal(modal);
        setTimeout(() => modal.remove(), 300);
    }
}

function handleCreateAlertSubmission() {
    const form = document.getElementById('create-alert-form');
    const formData = new FormData(form);
    
    // Get selected notification channels
    const selectedChannels = [];
    const channelCheckboxes = form.querySelectorAll('input[name="channels"]:checked');
    channelCheckboxes.forEach(checkbox => {
        selectedChannels.push(checkbox.value);
    });
    
    const thresholdType = formData.get('threshold_type');
    const thresholdValue = parseFloat(formData.get('threshold_value'));
    
    const alertData = {
        name: formData.get('name'),
        alert_type: formData.get('alert_type'),
        email: formData.get('email'),
        notification_frequency: formData.get('notification_frequency'),
        cluster_id: AlertsState.currentClusterId,
        notification_channels: selectedChannels
    };
    
    // Set threshold based on type
    if (thresholdType === 'amount') {
        alertData.threshold_amount = thresholdValue;
        alertData.threshold_percentage = 0;
    } else if (thresholdType === 'percentage') {
        alertData.threshold_percentage = thresholdValue;
        alertData.threshold_amount = 0;
    }
    
    // Validation
    if (!alertData.name) {
        showNotification('Please enter an alert name', 'error');
        return;
    }
    
    if (!alertData.email || !isValidEmail(alertData.email)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }
    
    if (!thresholdType) {
        showNotification('Please select a threshold type', 'error');
        return;
    }
    
    if (!thresholdValue || thresholdValue <= 0) {
        showNotification('Please enter a valid threshold value', 'error');
        return;
    }
    
    if (selectedChannels.length === 0) {
        showNotification('Please select at least one notification channel', 'error');
        return;
    }
    
    const createBtn = document.querySelector('#createAlertModal .btn-success');
    const originalText = createBtn.innerHTML;
    createBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating...';
    createBtn.disabled = true;
    
    createAlert(alertData)
        .then(result => {
            if (result.status === 'success') {
                showNotification('Alert created successfully!', 'success');
                closeCreateAlertModal();
                loadAlerts(); // Refresh alerts list
                
                createLocalInAppNotification(
                    'New Alert Created',
                    `Alert "${alertData.name}" has been created successfully`,
                    'success'
                );
            } else {
                throw new Error(result.message || 'Failed to create alert');
            }
        })
        .catch(error => {
            console.error('❌ Error creating alert:', error);
            showNotification(`Failed to create alert: ${error.message}`, 'error');
        })
        .finally(() => {
            createBtn.innerHTML = originalText;
            createBtn.disabled = false;
        });
}

function closeCreateAlertModal() {
    const modal = document.getElementById('createAlertModal');
    if (modal) {
        modal.remove();
    }
}

function handleCreateAlertSubmission(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    const alertData = {
        name: formData.get('name'),
        alert_type: 'cost_threshold',
        threshold_amount: parseFloat(formData.get('threshold_amount')),
        email: formData.get('email'),
        notification_frequency: formData.get('notification_frequency'),
        cluster_id: AlertsState.currentClusterId,
        notification_channels: ['email', 'inapp']
    };
    
    createAlert(alertData)
        .then(result => {
            if (result.status === 'success') {
                showNotification('Alert Created', 'Alert created successfully!', 'success');
                closeCreateAlertModal();
                loadAlerts(); // Refresh the alerts list
            } else {
                throw new Error(result.message || 'Failed to create alert');
            }
        })
        .catch(error => {
            showNotification('Error', `Failed to create alert: ${error.message}`, 'error');
        });
}

// View alert details
function viewAlert(alertId) {
    const alert = AlertsState.alerts.find(a => a.id == alertId);
    if (!alert) return;
    
    const modalHTML = `
        <div id="viewAlertModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-xl shadow-2xl p-6 w-full max-w-lg mx-4">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">Alert Details</h3>
                    <button onclick="closeViewAlertModal()" class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-500">Name</label>
                            <p class="text-gray-900">${escapeHtml(alert.name)}</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-500">Status</label>
                            <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full ${alert.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                                ${(alert.status || 'active').toUpperCase()}
                            </span>
                        </div>
                    </div>
                    
                    ${alert.threshold_amount ? `
                        <div>
                            <label class="block text-sm font-medium text-gray-500">Budget Threshold</label>
                            <p class="text-gray-900">$${alert.threshold_amount.toLocaleString()}</p>
                        </div>
                    ` : ''}
                    
                    ${alert.email ? `
                        <div>
                            <label class="block text-sm font-medium text-gray-500">Email</label>
                            <p class="text-gray-900">${escapeHtml(alert.email)}</p>
                        </div>
                    ` : ''}
                    
                    ${alert.notification_frequency ? `
                        <div>
                            <label class="block text-sm font-medium text-gray-500">Frequency</label>
                            <p class="text-gray-900">${getFrequencyInfo(alert.notification_frequency).display}</p>
                        </div>
                    ` : ''}
                    
                    ${alert.cluster_name ? `
                        <div>
                            <label class="block text-sm font-medium text-gray-500">Cluster</label>
                            <p class="text-gray-900">${escapeHtml(alert.cluster_name)}</p>
                        </div>
                    ` : ''}
                    
                    ${alert.last_triggered ? `
                        <div>
                            <label class="block text-sm font-medium text-gray-500">Last Triggered</label>
                            <p class="text-gray-900">${formatDateTime(alert.last_triggered)}</p>
                        </div>
                    ` : ''}
                </div>
                
                <div class="flex justify-end pt-6">
                    <button onclick="closeViewAlertModal()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                        Close
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function closeViewAlertModal() {
    const modal = document.getElementById('viewAlertModal');
    if (modal) {
        modal.remove();
    }
}


// Tab switching functionality
function switchAlertsTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.alerts-tab-button').forEach(btn => {
        btn.classList.remove('active', 'border-blue-500', 'text-blue-600');
        btn.classList.add('border-transparent', 'text-gray-500');
    });
    
    // Update tab content
    document.querySelectorAll('.alerts-tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    
    if (tabName === 'alerts') {
        document.getElementById('alerts-tab-btn').classList.add('active', 'border-blue-500', 'text-blue-600');
        document.getElementById('alerts-tab-btn').classList.remove('border-transparent', 'text-gray-500');
        document.getElementById('alerts-tab-content').classList.remove('hidden');
    } else if (tabName === 'notifications') {
        document.getElementById('notifications-tab-btn').classList.add('active', 'border-blue-500', 'text-blue-600');
        document.getElementById('notifications-tab-btn').classList.remove('border-transparent', 'text-gray-500');
        document.getElementById('notifications-tab-content').classList.remove('hidden');
    }
}

// Simplified alert display function (replaces the card-based version)
function displayAlertsSimplified(alerts) {
    const container = document.getElementById('alerts-list-container');
    if (!container) return;
    
    // Update total count
    const totalCountEl = document.getElementById('total-alerts-count');
    if (totalCountEl) {
        totalCountEl.textContent = alerts.length;
    }
    
    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-bell-slash text-3xl mb-2"></i>
                <p>No alerts configured</p>
                <button onclick="showCreateAlertModal()" class="mt-2 text-blue-500 hover:text-blue-600">
                    Create your first alert
                </button>
            </div>
        `;
        return;
    }

    // Create table-style layout
    const alertsHTML = `
        <div class="alerts-table bg-white border border-gray-200 rounded-lg overflow-hidden">
            <!-- Table Header -->
            <div class="alerts-table-header bg-gray-50 px-4 py-3 border-b border-gray-200">
                <div class="grid grid-cols-12 gap-4 text-xs font-medium text-gray-500 uppercase tracking-wide">
                    <div class="col-span-1">STATUS</div>
                    <div class="col-span-3">ALERT NAME</div>
                    <div class="col-span-2">BUDGET</div>
                    <div class="col-span-3">EMAIL</div>
                    <div class="col-span-2">CLUSTER</div>
                    <div class="col-span-1">ACTION</div>
                </div>
            </div>
            
            <!-- Table Body -->
            <div class="alerts-table-body">
                ${alerts.map(alert => {
                    const statusColor = alert.status === 'active' ? 'green' : alert.status === 'paused' ? 'yellow' : 'gray';
                    const statusIcon = alert.status === 'active' ? 'play' : alert.status === 'paused' ? 'pause' : 'stop';
                    
                    return `
                        <div class="alert-row grid grid-cols-12 gap-4 px-4 py-4 border-b border-gray-100 hover:bg-gray-50 transition-colors duration-200 items-center" 
                             data-alert-id="${alert.id}" 
                             data-status="${alert.status || 'active'}">
                            
                            <!-- Status Column -->
                            <div class="col-span-1">
                                <div class="flex items-center space-x-2">
                                    <div class="w-2 h-2 bg-${statusColor}-500 rounded-full"></div>
                                    <span class="text-xs px-2 py-1 bg-${statusColor}-100 text-${statusColor}-700 rounded uppercase font-medium">
                                        ${alert.status || 'active'}
                                    </span>
                                </div>
                            </div>
                            
                            <!-- Alert Name Column -->
                            <div class="col-span-3">
                                <span class="font-medium text-gray-900">${escapeHtml(alert.name)}</span>
                            </div>
                            
                            <!-- Budget Column -->
                            <div class="col-span-2">
                                <span class="text-gray-700">
                                    ${alert.threshold_amount > 0 ? `$${alert.threshold_amount.toLocaleString()}` : 'N/A'}
                                </span>
                            </div>
                            
                            <!-- Email Column -->
                            <div class="col-span-3">
                                <span class="text-gray-600 truncate block">
                                    ${alert.email ? escapeHtml(alert.email) : 'Not set'}
                                </span>
                            </div>
                            
                            <!-- Cluster Column -->
                            <div class="col-span-2">
                                <span class="text-gray-600 truncate block">
                                    ${alert.cluster_name ? escapeHtml(alert.cluster_name) : 'All clusters'}
                                </span>
                            </div>
                            
                            <!-- Action Column -->
                            <div class="col-span-1 relative">
                                <div class="flex items-center space-x-2">
                                    <!-- Test button -->
                                    <button onclick="testAlert('${alert.id}')" class="text-blue-500 hover:text-blue-600 p-1" title="Test Alert">
                                        <i class="fas fa-paper-plane text-sm"></i>
                                    </button>
                                    
                                    <!-- Toggle button -->
                                    <label class="inline-flex relative items-center cursor-pointer" title="${alert.status === 'active' ? 'Pause' : 'Resume'} Alert">
                                        <input type="checkbox" ${alert.status === 'active' ? 'checked' : ''} 
                                               onchange="pauseResumeAlert('${alert.id}', this.checked ? 'resume' : 'pause')" 
                                               class="sr-only peer">
                                        <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-green-500"></div>
                                    </label>
                                    
                                    <!-- Menu button -->
                                    <button onclick="toggleAlertMenu('${alert.id}')" class="text-gray-400 hover:text-gray-600 p-1">
                                        <i class="fas fa-ellipsis-v text-sm"></i>
                                    </button>
                                </div>
                                
                                <!-- Dropdown menu -->
                                <div id="menu-${alert.id}" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                                    <div class="py-1">
                                        <button onclick="viewAlert('${alert.id}')" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                            <i class="fas fa-eye mr-2"></i>View Details
                                        </button>
                                        <button onclick="editAlert('${alert.id}')" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                            <i class="fas fa-edit mr-2"></i>Edit Alert
                                        </button>
                                        <hr class="my-1">
                                        <button onclick="deleteAlert('${alert.id}')" class="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50">
                                            <i class="fas fa-trash mr-2"></i>Delete
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
    
    container.innerHTML = alertsHTML;
}

// Edit alert function
function editAlert(alertId) {
    const alert = AlertsState.alerts.find(a => a.id == alertId);
    if (!alert) {
        showNotification('Alert not found', 'error');
        return;
    }
    
    console.log('✏️ Editing alert:', alertId);
    
    const modalHTML = `
        <div class="modal fade" id="editAlertModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-edit me-2"></i>Edit Alert
                        </h5>
                        <button type="button" class="btn-close btn-close-white" 
                                onclick="closeEditAlertModal()" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="edit-alert-form">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Alert Name</label>
                                        <input type="text" class="form-control" name="name" 
                                               value="${escapeHtml(alert.name)}" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Email Address</label>
                                        <input type="email" class="form-control" name="email" 
                                               value="${escapeHtml(alert.email || '')}" required>
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Threshold Amount ($)</label>
                                        <input type="number" class="form-control" name="threshold_amount" 
                                               value="${alert.threshold_amount || ''}" min="0" step="0.01">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Threshold Percentage (%)</label>
                                        <input type="number" class="form-control" name="threshold_percentage" 
                                               value="${alert.threshold_percentage || ''}" min="0" max="100">
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="closeEditAlertModal()">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="saveEditAlert(${alertId})">
                            <i class="fas fa-save me-2"></i>Save Changes
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal
    const existingModal = document.getElementById('editAlertModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Show modal
    const modalElement = document.getElementById('editAlertModal');
    BootstrapHelper.showModal(modalElement);
}

function saveEditAlert(alertId) {
    const form = document.getElementById('edit-alert-form');
    const formData = new FormData(form);
    
    const updateData = {
        name: formData.get('name'),
        email: formData.get('email'),
        threshold_amount: parseFloat(formData.get('threshold_amount')) || 0,
        threshold_percentage: parseFloat(formData.get('threshold_percentage')) || 0
    };
    
    // Validation
    if (!updateData.name) {
        showNotification('Please enter an alert name', 'error');
        return;
    }
    
    if (!updateData.email || !isValidEmail(updateData.email)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }
    
    const saveBtn = document.querySelector('#editAlertModal .btn-primary');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
    saveBtn.disabled = true;
    
    fetch(`/api/alerts/${alertId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        if (result.status === 'success') {
            showNotification('Alert updated successfully!', 'success');
            closeEditAlertModal();
            loadAlerts(); // Refresh alerts list
        } else {
            throw new Error(result.message || 'Failed to update alert');
        }
    })
    .catch(error => {
        console.error('❌ Error updating alert:', error);
        showNotification(`Failed to update alert: ${error.message}`, 'error');
    })
    .finally(() => {
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    });
}

function closeEditAlertModal() {
    const modalElement = document.getElementById('editAlertModal');
    if (modalElement) {
        BootstrapHelper.hideModal(modalElement);
        setTimeout(() => modalElement.remove(), 300);
    }
}

// Add to global exports
window.editAlert = editAlert;

// Simplified notifications display
function updateInAppNotificationsUI() {
    const container = document.getElementById('in-app-notifications-container');
    if (!container) return;
    
    if (AlertsState.inAppNotifications.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-bell-slash text-3xl mb-2"></i>
                <p>No notifications yet</p>
            </div>
        `;
        return;
    }
    
    // Create table-style layout for notifications
    const notificationsHTML = `
        <div class="notifications-table bg-white border border-gray-200 rounded-lg overflow-hidden">
            <!-- Table Header -->
            <div class="notifications-table-header bg-gray-50 px-4 py-3 border-b border-gray-200">
                <div class="grid grid-cols-12 gap-4 text-xs font-medium text-gray-500 uppercase tracking-wide">
                    <div class="col-span-1">TYPE</div>
                    <div class="col-span-3">TITLE</div>
                    <div class="col-span-4">MESSAGE</div>
                    <div class="col-span-2">DATE/TIME</div>
                    <div class="col-span-1">STATUS</div>
                    <div class="col-span-1">ACTION</div>
                </div>
            </div>
            
            <!-- Table Body -->
            <div class="notifications-table-body">
                ${AlertsState.inAppNotifications.map(notification => {
                    const typeColor = getNotificationTypeColor(notification.type);
                    const typeIcon = getNotificationTypeIcon(notification.type);
                    
                    return `
                        <div class="notification-row grid grid-cols-12 gap-4 px-4 py-4 border-b border-gray-100 hover:bg-gray-50 transition-colors duration-200 items-center ${notification.read ? 'opacity-75' : ''}" 
                             data-notification-id="${notification.id}">
                            
                            <!-- Type Column -->
                            <div class="col-span-1">
                                <div class="flex items-center justify-center">
                                    <div class="w-8 h-8 bg-${typeColor}-100 rounded-lg flex items-center justify-center">
                                        <i class="fas fa-${typeIcon} text-${typeColor}-600 text-sm"></i>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Title Column -->
                            <div class="col-span-3">
                                <div class="flex items-center space-x-2">
                                    <span class="font-medium text-gray-900">${escapeHtml(notification.title)}</span>
                                    ${!notification.read ? '<span class="w-2 h-2 bg-blue-500 rounded-full"></span>' : ''}
                                </div>
                            </div>
                            
                            <!-- Message Column -->
                            <div class="col-span-4">
                                <span class="text-gray-600 text-sm line-clamp-2">${escapeHtml(notification.message)}</span>
                            </div>
                            
                            <!-- Date/Time Column -->
                            <div class="col-span-2">
                                <div class="text-sm text-gray-500">
                                    <div>${formatDate(notification.timestamp)}</div>
                                    <div class="text-xs">${formatTime(notification.timestamp)}</div>
                                </div>
                            </div>
                            
                            <!-- Status Column -->
                            <div class="col-span-1">
                                <span class="text-xs px-2 py-1 rounded-full ${notification.read ? 'bg-gray-100 text-gray-600' : 'bg-blue-100 text-blue-700'}">
                                    ${notification.read ? 'Read' : 'New'}
                                </span>
                            </div>
                            
                            <!-- Action Column -->
                            <div class="col-span-1">
                                <div class="flex items-center space-x-1">
                                    ${!notification.read ? `
                                        <button onclick="markNotificationAsRead('${notification.id}')" class="text-blue-500 hover:text-blue-600 p-1" title="Mark as read">
                                            <i class="fas fa-check text-sm"></i>
                                        </button>
                                    ` : ''}
                                    <button onclick="dismissNotification('${notification.id}')" class="text-gray-400 hover:text-red-500 p-1" title="Dismiss">
                                        <i class="fas fa-times text-sm"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
    
    container.innerHTML = notificationsHTML;
}

// Helper functions for notification display
function getNotificationTypeColor(type) {
    const colors = {
        'info': 'blue',
        'success': 'green',
        'warning': 'yellow',
        'error': 'red',
        'alert': 'orange'
    };
    return colors[type] || 'blue';
}

function getNotificationTypeIcon(type) {
    const icons = {
        'info': 'info-circle',
        'success': 'check-circle',
        'warning': 'exclamation-triangle',
        'error': 'times-circle',
        'alert': 'bell'
    };
    return icons[type] || 'bell';
}

// Date/time formatting helpers
function formatDate(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
        });
    } catch {
        return 'Invalid date';
    }
}

function formatTime(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true
        });
    } catch {
        return 'Invalid time';
    }
}

// Add these to your global exports
window.getNotificationTypeColor = getNotificationTypeColor;
window.getNotificationTypeIcon = getNotificationTypeIcon;
window.formatDate = formatDate;
window.formatTime = formatTime;

// Filter button styling update
function filterAlerts(filter) {
    AlertsState.currentFilter = filter;
    
    // Update button states
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active', 'bg-blue-100', 'text-blue-700', 'border-blue-200');
        btn.classList.add('bg-gray-100', 'text-gray-600', 'border-gray-200');
    });
    
    // Activate selected filter
    const activeBtn = document.querySelector(`[onclick="filterAlerts('${filter}')"]`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'bg-blue-100', 'text-blue-700', 'border-blue-200');
        activeBtn.classList.remove('bg-gray-100', 'text-gray-600', 'border-gray-200');
    }
    
    // Filter and display alerts
    const alertItems = document.querySelectorAll('.alert-item');
    alertItems.forEach(item => {
        const alertStatus = item.dataset.status || 'active';
        let shouldShow = false;
        
        switch (filter) {
            case 'all':
                shouldShow = true;
                break;
            case 'active':
                shouldShow = alertStatus === 'active';
                break;
            case 'paused':
                shouldShow = alertStatus === 'paused';
                break;
            default:
                shouldShow = true;
        }
        
        item.style.display = shouldShow ? 'flex' : 'none';
    });
    
    updateFilterCounts();
}

// Add these to your global exports
window.switchAlertsTab = switchAlertsTab;
window.displayAlerts = displayAlertsSimplified;

// Add these to your global exports
window.showCreateAlertModal = showCreateAlertModal;
window.closeCreateAlertModal = closeCreateAlertModal;
window.toggleAlertMenu = toggleAlertMenu;
window.viewAlert = viewAlert;
window.closeViewAlertModal = closeViewAlertModal;
/**
 * View alert history (MISSING FUNCTION)
 */
function viewAlertHistory() {
    const modalHTML = `
        <div class="modal fade" id="alertHistoryModal" tabindex="-1" 
             aria-labelledby="alertHistoryModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-gradient-info text-white">
                        <h5 class="modal-title" id="alertHistoryModalLabel">
                            <i class="fas fa-history me-2"></i>Alert Trigger History
                        </h5>
                        <button type="button" class="btn-close btn-close-white" 
                                data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div id="alert-history-container">
                            <div class="text-center py-4">
                                <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
                                <p>Loading alert history...</p>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" onclick="exportAlertHistory()">
                            <i class="fas fa-download me-2"></i>Export History
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('alertHistoryModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('alertHistoryModal'));
    modal.show();
    
    // Load alert history
    loadAlertHistory();
}

/**
 * Load alert history
 */
function loadAlertHistory() {
    const container = document.getElementById('alert-history-container');
    if (!container) return;
    
    fetch('/api/alerts/triggers')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Request failed: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                displayAlertHistory(data.triggers);
            } else {
                throw new Error(data.message || 'Failed to load alert history');
            }
        })
        .catch(error => {
            console.error('❌ Error loading alert history:', error);
            container.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to load alert history: ${error.message}
                </div>
            `;
        });
}

/**
 * Display alert history
 */
function displayAlertHistory(triggers) {
    const container = document.getElementById('alert-history-container');
    if (!container) return;
    
    if (triggers.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-history fa-2x mb-3"></i>
                <p>No alert triggers recorded yet</p>
                <small>Alert triggers will appear here when alerts are triggered</small>
            </div>
        `;
        return;
    }
    
    const historyHTML = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-dark">
                    <tr>
                        <th>Date/Time</th>
                        <th>Alert</th>
                        <th>Cluster</th>
                        <th>Current Cost</th>
                        <th>Threshold</th>
                        <th>Exceeded By</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${triggers.map(trigger => `
                        <tr>
                            <td>${formatDateTime(trigger.triggered_at)}</td>
                            <td>${escapeHtml(trigger.alert_name || `Alert ${trigger.alert_id}`)}</td>
                            <td>${escapeHtml(trigger.cluster_name || 'Unknown')}</td>
                            <td>$${trigger.current_cost ? trigger.current_cost.toLocaleString() : '0'}</td>
                            <td>$${trigger.threshold_amount ? trigger.threshold_amount.toLocaleString() : '0'}</td>
                            <td>$${trigger.threshold_exceeded_by ? trigger.threshold_exceeded_by.toLocaleString() : '0'}</td>
                            <td>
                                <span class="badge ${trigger.notification_sent ? 'bg-success' : 'bg-warning'}">
                                    ${trigger.notification_sent ? 'Sent' : 'Pending'}
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = historyHTML;
}

/**
 * Export alert history
 */
function exportAlertHistory() {
    showNotification('Exporting alert history...', 'info');
    
    fetch('/api/alerts/triggers')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const csvContent = convertTriggersToCSV(data.triggers);
                downloadCSV(csvContent, 'alert_history.csv');
                showNotification('Alert history exported successfully!', 'success');
            } else {
                throw new Error(data.message || 'Failed to export history');
            }
        })
        .catch(error => {
            console.error('❌ Error exporting alert history:', error);
            showNotification(`Failed to export history: ${error.message}`, 'error');
        });
}

/**
 * Convert triggers to CSV format
 */
function convertTriggersToCSV(triggers) {
    const headers = ['Date/Time', 'Alert Name', 'Cluster', 'Current Cost', 'Threshold', 'Exceeded By', 'Notification Sent'];
    const csvRows = [headers.join(',')];
    
    triggers.forEach(trigger => {
        const row = [
            `"${trigger.triggered_at}"`,
            `"${trigger.alert_name || `Alert ${trigger.alert_id}`}"`,
            `"${trigger.cluster_name || 'Unknown'}"`,
            trigger.current_cost || 0,
            trigger.threshold_amount || 0,
            trigger.threshold_exceeded_by || 0,
            trigger.notification_sent ? 'Yes' : 'No'
        ];
        csvRows.push(row.join(','));
    });
    
    return csvRows.join('\n');
}

/**
 * Download CSV file
 */
function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// ============================================================================
// UTILITY FUNCTIONS (ALL RESTORED)
// ============================================================================

function getStatusBadgeClass(status) {
    const classes = {
        'active': 'bg-success',
        'paused': 'bg-warning text-dark',
        'triggered': 'bg-danger',
        'failed': 'bg-secondary'
    };
    return classes[status] || 'bg-secondary';
}

function getNotificationIcon(type) {
    const icons = {
        'info': 'info-circle',
        'success': 'check-circle',
        'warning': 'exclamation-triangle',
        'error': 'times-circle'
    };
    return icons[type] || 'bell';
}

function getNotificationColor(type) {
    const colors = {
        'info': 'info',
        'success': 'success',
        'warning': 'warning',
        'error': 'danger'
    };
    return colors[type] || 'secondary';
}

function getNotificationChannelsText(alert) {
    const channels = [];
    const notificationChannels = alert.notification_channels || ['email'];
    
    if (notificationChannels.includes('email') && AlertsState.notificationChannels.email) {
        channels.push('Email');
    }
    if (notificationChannels.includes('slack') && AlertsState.notificationChannels.slack) {
        channels.push('Slack');
    }
    if (notificationChannels.includes('inapp') || notificationChannels.includes('in_app')) {
        channels.push('In-App');
    }
    
    return channels.length > 0 ? channels.join(', ') : 'Email only';
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

// ============================================================================
// CSS ANIMATIONS AND STYLING
// ============================================================================

// Add CSS animations for better UX
const enhancedModalCSS = `
<style>
@keyframes bounceIn {
    0% {
        opacity: 0;
        transform: scale(0.3);
    }
    50% {
        opacity: 1;
        transform: scale(1.05);
    }
    70% {
        transform: scale(0.9);
    }
    100% {
        opacity: 1;
        transform: scale(1);
    }
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
    20%, 40%, 60%, 80% { transform: translateX(5px); }
}

.modal-content {
    border-radius: 15px !important;
    overflow: hidden;
}

.modal-header {
    border-radius: 15px 15px 0 0 !important;
}

.btn {
    border-radius: 8px !important;
    font-weight: 500;
    transition: all 0.2s ease;
}

.btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.alert-light {
    background: linear-gradient(45deg, #f8f9fa, #ffffff);
}

.toast {
    border-radius: 10px !important;
    backdrop-filter: blur(10px);
}

#deleteAlertModal .modal-content {
    animation: bounceIn 0.5s ease-out;
}

#deleteAlertModal .btn-danger:hover {
    background-color: #dc3545 !important;
    border-color: #dc3545 !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(220, 53, 69, 0.3);
}

#deleteAlertModal .btn-light:hover {
    background-color: #f8f9fa !important;
    border-color: #dee2e6 !important;
    transform: translateY(-1px);
}
    .alert-actions {
    position: relative !important;
}

.alert-actions [id^="menu-"] {
    position: absolute !important;
    top: 100% !important;
    right: 0 !important;
    z-index: 9999 !important;
    margin-top: 2px !important;
}

.alert-row {
    position: relative !important;
}
</style>
`;

// Inject CSS when the script loads
document.head.insertAdjacentHTML('beforeend', enhancedModalCSS);

// ============================================================================
// GLOBAL FUNCTION EXPORTS - MAKE ALL FUNCTIONS AVAILABLE GLOBALLY
// ============================================================================

// Main functions
window.initializeAlertsSystem = initializeAlertsSystem;
window.loadAlerts = loadAlerts;
window.loadClusterAlerts = loadClusterAlerts;
window.displayClusterAlerts = displayClusterAlerts;
window.filterAlerts = filterAlerts;
window.testAlert = testAlert;
window.pauseResumeAlert = pauseResumeAlert;
window.deleteAlert = deleteAlert;

// Notification functions
window.markNotificationAsRead = markNotificationAsRead;
window.markAllNotificationsAsRead = markAllNotificationsAsRead;
window.dismissNotification = dismissNotificationLocally;
window.clearAllNotifications = clearAllNotifications;

// Modal functions
window.showAdvancedAlertsModal = showAdvancedAlertsModal;
window.handleAdvancedAlertCreation = handleAdvancedAlertCreation;
window.showDeleteAlertModal = showDeleteAlertModal;
window.confirmDeleteAlert = confirmDeleteAlert;
window.executeAlertDeletion = executeAlertDeletion;

// History and export functions
window.viewAlertHistory = viewAlertHistory;
window.exportAlertHistory = exportAlertHistory;
window.exportAlertsConfig = exportAlertsConfig;

// Slack functions
window.testSlackNotification = testSlackNotification;

// Utility functions
window.showEnhancedNotification = showEnhancedNotification;
window.AlertsState = AlertsState;


// Make functions globally available
window.setupFrequencyPreview = setupFrequencyPreview;
window.testAlertTrigger = testAlertTrigger;
window.updateAlertSummaryCounters = updateAlertSummaryCounters;
window.calculateAlertHealthScore = calculateAlertHealthScore;

// Initialize alerts when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAlertsSystem);
} else {
    initializeAlertsSystem();
}
