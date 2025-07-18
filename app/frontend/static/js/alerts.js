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
                
                // Create in-app notification
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
        })
        .finally(() => {
            button.innerHTML = originalContent;
            button.disabled = false;
        });
    }
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
                    <div class="modal-header bg-gradient-primary text-white">
                        <h5 class="modal-title" id="advancedAlertsModalLabel">
                            <i class="fas fa-cog me-2"></i>Advanced Alerts Configuration
                        </h5>
                        <button type="button" class="btn-close btn-close-white" 
                                data-bs-dismiss="modal" aria-label="Close"></button>
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

                            <!-- 🆕 FREQUENCY CONFIGURATION SECTION -->
                            <div id="frequency-config-section" class="mb-4">
                                <div class="card border-info">
                                    <div class="card-header bg-info text-white">
                                        <h6 class="mb-0">
                                            <i class="fas fa-cog me-2"></i>Frequency Configuration
                                        </h6>
                                    </div>
                                    <div class="card-body">
                                        <div class="row">
                                            <div class="col-md-4">
                                                <div class="form-group mb-3">
                                                    <label class="form-label">Daily Time (for daily/weekly alerts)</label>
                                                    <input type="time" class="form-control" name="frequency_at_time" value="09:00">
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <div class="form-group mb-3">
                                                    <label class="form-label">Max Notifications per Day</label>
                                                    <select class="form-select" name="max_notifications_per_day">
                                                        <option value="">No limit</option>
                                                        <option value="1">1 per day</option>
                                                        <option value="3" selected>3 per day</option>
                                                        <option value="6">6 per day</option>
                                                        <option value="12">12 per day</option>
                                                        <option value="24">24 per day</option>
                                                    </select>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <div class="form-group mb-3">
                                                    <label class="form-label">Cooldown Period (hours)</label>
                                                    <select class="form-select" name="cooldown_period_hours">
                                                        <option value="0">No cooldown</option>
                                                        <option value="1">1 hour</option>
                                                        <option value="4" selected>4 hours</option>
                                                        <option value="8">8 hours</option>
                                                        <option value="24">24 hours</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                        <div id="frequency-preview" class="alert alert-light">
                                            <small id="frequency-preview-text">Preview will update based on your frequency selection</small>
                                        </div>
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
                            
                            <!-- Channel Status Info -->
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                <strong>Channel Status:</strong>
                                <div class="notification-channels-status mt-2"></div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
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
    
    // Setup frequency preview
    setupFrequencyPreview();
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('advancedAlertsModal'));
    modal.show();
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
        
        // 🆕 ENHANCED FREQUENCY SETTINGS
        notification_frequency: formData.get('notification_frequency') || AlertsState.defaultFrequency,
        frequency_at_time: formData.get('frequency_at_time'),
        max_notifications_per_day: parseInt(formData.get('max_notifications_per_day')) || null,
        cooldown_period_hours: parseInt(formData.get('cooldown_period_hours')) || 0,
        
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
    
    createAlert(alertData)
        .then(result => {
            if (result.status === 'success') {
                const frequencyInfo = getFrequencyInfo(alertData.notification_frequency);
                showNotification(`Advanced alert created with ${frequencyInfo.display} frequency!`, 'success');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('advancedAlertsModal'));
                modal.hide();
                
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
        });
}



// ============================================================================
// ENHANCED DELETE ALERT MODAL - MODERN CONFIRMATION DIALOG
// ============================================================================

/**
 * Show enhanced delete confirmation modal
 */
function showDeleteAlertModal(alertId, alertName) {
    // Get alert details for the modal
    const alert = AlertsState.alerts.find(a => a.id == alertId);
    const alertDisplayName = alertName || (alert ? alert.name : `Alert ${alertId}`);
    
    const modalHTML = `
        <div class="modal fade" id="deleteAlertModal" tabindex="-1" 
             aria-labelledby="deleteAlertModalLabel" aria-hidden="true" data-bs-backdrop="static">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-danger text-white border-0">
                        <h5 class="modal-title d-flex align-items-center" id="deleteAlertModalLabel">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Confirm Delete Alert
                        </h5>
                        <button type="button" class="btn-close btn-close-white" 
                                data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body p-4">
                        <div class="text-center mb-4">
                            <div class="text-danger mb-3">
                                <i class="fas fa-trash-alt fa-3x"></i>
                            </div>
                            <h6 class="fw-bold text-dark mb-3">Delete Alert Permanently?</h6>
                            <p class="text-muted mb-2">
                                You are about to permanently delete the following alert:
                            </p>
                        </div>
                        
                        <div class="alert alert-light border border-danger border-2 rounded-3">
                            <div class="d-flex align-items-start">
                                <div class="text-danger me-3 mt-1">
                                    <i class="fas fa-bell fa-lg"></i>
                                </div>
                                <div class="flex-grow-1">
                                    <h6 class="text-danger fw-bold mb-2">${escapeHtml(alertDisplayName)}</h6>
                                    ${alert ? `
                                        <div class="small text-muted">
                                            <div class="row">
                                                <div class="col-6">
                                                    <strong>Threshold:</strong> 
                                                    ${alert.threshold_amount > 0 
                                                        ? '$' + alert.threshold_amount.toLocaleString() 
                                                        : alert.threshold_percentage + '%'}
                                                </div>
                                                <div class="col-6">
                                                    <strong>Email:</strong> ${escapeHtml(alert.email || 'Not set')}
                                                </div>
                                            </div>
                                            <div class="row mt-1">
                                                <div class="col-6">
                                                    <strong>Cluster:</strong> ${escapeHtml(alert.cluster_name || 'All clusters')}
                                                </div>
                                                <div class="col-6">
                                                    <strong>Status:</strong> 
                                                    <span class="badge ${getStatusBadgeClass(alert.status || 'active')} ms-1">
                                                        ${(alert.status || 'active').toUpperCase()}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                        
                        <div class="bg-light rounded-3 p-3 mb-3">
                            <div class="d-flex align-items-start">
                                <div class="text-warning me-2 mt-1">
                                    <i class="fas fa-exclamation-circle"></i>
                                </div>
                                <div class="small text-muted">
                                    <strong class="text-dark">Warning:</strong> This action cannot be undone. 
                                    The alert will be permanently removed and will no longer monitor your cluster costs.
                                </div>
                            </div>
                        </div>
                        
                        <div class="text-center">
                            <p class="small text-muted mb-0">
                                Are you sure you want to continue?
                            </p>
                        </div>
                    </div>
                    <div class="modal-footer border-0 pt-0">
                        <div class="w-100 d-flex gap-2">
                            <button type="button" class="btn btn-light flex-fill border" data-bs-dismiss="modal">
                                <i class="fas fa-times me-2"></i>Cancel
                            </button>
                            <button type="button" class="btn btn-danger flex-fill" 
                                    onclick="confirmDeleteAlert(${alertId})" data-alert-id="${alertId}">
                                <i class="fas fa-trash-alt me-2"></i>Delete Alert
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
    
    // Show modal with animation
    const modal = new bootstrap.Modal(document.getElementById('deleteAlertModal'), {
        backdrop: 'static',
        keyboard: true
    });
    
    // Add entrance animation
    const modalElement = document.getElementById('deleteAlertModal');
    modalElement.addEventListener('shown.bs.modal', function () {
        modalElement.querySelector('.modal-content').style.animation = 'bounceIn 0.5s ease-out';
    });
    
    modal.show();
    
    // Focus on the cancel button initially (safer default)
    modalElement.addEventListener('shown.bs.modal', function () {
        modalElement.querySelector('[data-bs-dismiss="modal"]').focus();
    });
}

/**
 * Confirm and execute alert deletion
 */
function confirmDeleteAlert(alertId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById('deleteAlertModal'));
    const deleteBtn = document.querySelector(`[data-alert-id="${alertId}"]`);
    
    if (deleteBtn) {
        // Show loading state
        const originalContent = deleteBtn.innerHTML;
        deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Deleting...';
        deleteBtn.disabled = true;
        
        // Close modal first
        modal.hide();
        
        // Execute the actual deletion
        executeAlertDeletion(alertId)
            .then(() => {
                // Success handling is done in executeAlertDeletion
            })
            .catch(error => {
                // Error handling is done in executeAlertDeletion
                console.error('❌ Delete confirmation error:', error);
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
        
        const alertItem = document.querySelector(`[data-alert-id="${alertId}"]`);
        if (alertItem) {
            // Add deletion animation
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
                    // Success animation
                    alertItem.style.transition = 'all 0.5s ease-out';
                    alertItem.style.opacity = '0';
                    alertItem.style.transform = 'translateX(-100%) scale(0.8)';
                    
                    setTimeout(() => {
                        alertItem.remove();
                        
                        // Update counter
                        const remainingAlerts = document.querySelectorAll('.alert-item').length;
                        updateAlertsCounter(remainingAlerts);
                        updateFilterCounts();
                        
                        // Show empty state if no alerts left
                        if (remainingAlerts === 0) {
                            displayAlerts([]);
                        }
                    }, 500);
                    
                    // Show success notification with custom styling
                    showEnhancedNotification('success', 'Alert Deleted Successfully!', 
                        `The alert has been permanently removed from your system.`);
                    
                    // Create in-app notification
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
                
                // Restore UI state with error animation
                alertItem.style.transition = 'all 0.3s ease-out';
                alertItem.style.opacity = '1';
                alertItem.style.transform = 'scale(1)';
                alertItem.style.pointerEvents = 'auto';
                alertItem.style.animation = 'shake 0.5s ease-in-out';
                
                setTimeout(() => {
                    alertItem.style.animation = '';
                }, 500);
                
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
    // Try to use the existing notification system first
    if (window.smoothNotificationManager) {
        window.smoothNotificationManager.show(`${title}: ${message}`, type);
        return;
    }
    
    // Fallback: Create a custom toast notification
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
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0 shadow-lg" 
             role="alert" aria-live="assertive" aria-atomic="true" 
             style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center">
                    <i class="${iconClass} me-2"></i>
                    <div>
                        <div class="fw-bold">${title}</div>
                        <div class="small">${message}</div>
                    </div>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: type === 'error' ? 8000 : 5000
    });
    
    toast.show();
    
    // Remove from DOM after hiding
    toastElement.addEventListener('hidden.bs.toast', function () {
        toastElement.remove();
    });
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
