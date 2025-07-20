// frontend/static/js/alerts/main.js

/**
 * Professional modals, notifications panel, proper counts
 */

// Global state
window.AlertsState = {
    alerts: [],
    notifications: [],
    loading: false,
    currentClusterId: null,
    systemAvailable: true,
    currentFilter: 'all',
    unreadNotificationsCount: 0
};

/**
 * DYNAMIC CLUSTER DETECTION - RESPECTS YOUR URL STRUCTURE
 */
function detectCurrentCluster() {
    console.log('🔍 Detecting cluster from your URL structure...');
    
    const urlPath = window.location.pathname;
    console.log('📍 URL Path:', urlPath);
    
    // Your URL pattern: /cluster/rg-xxx_aks-cluster-name
    // Looking for: rg-dpl-mad-dev-ne2-2_aks-dpl-mad-dev-ne2-1
    const urlClusterMatch = urlPath.match(/\/cluster\/([^\/]+)/);
    if (urlClusterMatch) {
        const fullClusterId = urlClusterMatch[1];
        console.log('✅ Found full cluster ID from URL:', fullClusterId);
        return fullClusterId;
    }
    
    // Fallback: try to find any cluster-like pattern in URL
    const clusterPattern = urlPath.match(/(rg-[^_]+_aks-[^\/]+)/);
    if (clusterPattern) {
        console.log('✅ Found cluster pattern:', clusterPattern[1]);
        return clusterPattern[1];
    }
    
    console.log('⚠️ Could not detect cluster from URL structure');
    return null;
}

/**
 * LOAD ALERTS - PURE API CALL, NO OVERRIDES
 */
function loadAlerts() {
    console.log('🔄 Loading alerts from real API...');
    
    // Use your dynamic cluster detection
    const detectedCluster = detectCurrentCluster();
    if (detectedCluster) {
        window.AlertsState.currentClusterId = detectedCluster;
    }
    
    const url = window.AlertsState.currentClusterId 
        ? `/api/alerts?cluster_id=${encodeURIComponent(window.AlertsState.currentClusterId)}` 
        : '/api/alerts';
    
    console.log(`📡 Loading alerts from: ${url}`);
    console.log(`📡 Cluster ID: ${window.AlertsState.currentClusterId || 'all clusters'}`);
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Use exactly what your backend returns - no filtering or modifications
                window.AlertsState.alerts = data.alerts || [];
                console.log(`✅ Loaded ${window.AlertsState.alerts.length} alerts from real API`);
                displayAlerts();
            } else {
                console.log('📭 No alerts returned from API');
                window.AlertsState.alerts = [];
                displayAlerts();
            }
        })
        .catch(error => {
            console.error('❌ Error loading alerts from API:', error);
            // Don't use fallback data - just empty state
            window.AlertsState.alerts = [];
            displayAlerts();
        });
}

/**
 * LOAD NOTIFICATIONS - REAL API ONLY
 */
function loadNotifications() {
    console.log('🔄 Loading notifications from real API...');
    
    // Use the same cluster detection as alerts
    const clusterId = window.AlertsState.currentClusterId;
    
    let url = '/api/notifications/in-app?unread_only=false&limit=50';
    if (clusterId) {
        url += `&cluster_id=${encodeURIComponent(clusterId)}`;
    }
    
    console.log(`📡 Loading notifications from: ${url}`);
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.AlertsState.notifications = data.notifications || [];
                window.AlertsState.unreadNotificationsCount = data.unread_count || 0;
                
                console.log(`✅ Loaded ${window.AlertsState.notifications.length} notifications from real API`);
                console.log(`📬 Unread count: ${window.AlertsState.unreadNotificationsCount}`);
                
                updateNotificationBadge();
            } else {
                console.log('📭 No notifications returned from API');
                window.AlertsState.notifications = [];
                window.AlertsState.unreadNotificationsCount = 0;
                updateNotificationBadge();
            }
        })
        .catch(error => {
            console.error('❌ Error loading notifications from API:', error);
            // Don't use fallback data - just empty state
            window.AlertsState.notifications = [];
            window.AlertsState.unreadNotificationsCount = 0;
            updateNotificationBadge();
        });
}

/**
 * DISPLAY ALERTS - ENHANCED WITH PROPER COUNTS
 */
function displayAlerts() {
    const container = document.getElementById('alerts-list-container');
    if (!container) return;
    
    const alerts = window.AlertsState.alerts;
    console.log(`📋 Displaying ${alerts.length} alerts`);
    
    // Calculate counts for filter buttons
    const allCount = alerts.length;
    const activeCount = alerts.filter(a => (a.status || 'active') === 'active').length;
    const pausedCount = alerts.filter(a => a.status === 'paused').length;
    document.getElementById('total-alerts-count').textContent = allCount;
    
    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="alerts-header">
                <h2 class="alerts-title">ALERTS</h2>
                <button class="export-btn" onclick="exportAlerts()">
                    <i class="fas fa-download"></i> Export Excel
                </button>
            </div>
            
            <!-- Filter Buttons with Counts -->
            <div class="filter-buttons">
                <button class="filter-btn ${window.AlertsState.currentFilter === 'all' ? 'active' : ''}" 
                        onclick="filterAlerts('all')">
                    All (<span id="all-count">0</span>)
                </button>
                <button class="filter-btn ${window.AlertsState.currentFilter === 'active' ? 'active' : ''}" 
                        onclick="filterAlerts('active')">
                    Active (<span id="active-count">0</span>)
                </button>
                <button class="filter-btn ${window.AlertsState.currentFilter === 'paused' ? 'active' : ''}" 
                        onclick="filterAlerts('paused')">
                    Paused (<span id="paused-count">0</span>)
                </button>
            </div>
            
            <div class="empty-state">
                <i class="fas fa-bell-slash"></i>
                <h3>No alerts found</h3>
                <p>Create your first alert to get started</p>
                <button onclick="showCreateAlertModal()" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Create Alert
                </button>
            </div>
        `;
        container.style.display = 'block';
        return;
    }
    
    // Filter alerts
    const filteredAlerts = filterAlertsArray(alerts, window.AlertsState.currentFilter);
    
    const tableHTML = `
        <!-- Header -->
        <div class="alerts-header">
            <h2 class="alerts-title">ALERTS</h2>
            <button class="export-btn" onclick="exportAlerts()">
                <i class="fas fa-download"></i> Export Excel
            </button>
        </div>
        
        <!-- Filter Buttons with Proper Counts -->
        <div class="filter-buttons">
            <button class="filter-btn ${window.AlertsState.currentFilter === 'all' ? 'active' : ''}" 
                    onclick="filterAlerts('all')">
                All (<span id="all-count">${allCount}</span>)
            </button>
            <button class="filter-btn ${window.AlertsState.currentFilter === 'active' ? 'active' : ''}" 
                    onclick="filterAlerts('active')">
                Active (<span id="active-count">${activeCount}</span>)
            </button>
            <button class="filter-btn ${window.AlertsState.currentFilter === 'paused' ? 'active' : ''}" 
                    onclick="filterAlerts('paused')">
                Paused (<span id="paused-count">${pausedCount}</span>)
            </button>
        </div>
        
        <!-- Table -->
        <div class="alerts-table">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>ALERT NAME</th>
                        <th>EMAIL</th>
                        <th>BUDGET</th>
                        <th>TYPE</th>
                        <th>ALERT</th>
                        <th>ACTION</th>
                    </tr>
                </thead>
                <tbody>
                    ${filteredAlerts.map((alert, index) => `
                        <tr data-alert-id="${alert.id}" data-status="${alert.status || 'active'}">
                            <td>${String(alert.id).padStart(3, '0')}</td>
                            <td>
                                <strong>${escapeHtml(alert.name)}</strong>
                                <br><small style="color: #6c757d;">${escapeHtml(alert.cluster_name || 'All clusters')}</small>
                            </td>
                            <td>${escapeHtml(alert.email || 'Not set')}</td>
                            <td>
                                <strong>${alert.threshold_amount ? alert.threshold_amount.toLocaleString() : '0'}</strong>
                                ${alert.threshold_percentage ? `<br><small>${alert.threshold_percentage}%</small>` : ''}
                            </td>
                            <td>
                                <span class="status-badge ${(alert.status || 'active')}">${(alert.status || 'active').charAt(0).toUpperCase() + (alert.status || 'active').slice(1)}</span>
                            </td>
                            <td>
                                <div class="alert-toggle ${(alert.status || 'active') === 'active' ? 'active' : ''}" 
                                     onclick="handleToggleAlert('${alert.id}', ${(alert.status || 'active') === 'paused'})"></div>
                            </td>
                            <td>
                                <div class="dropdown">
                                    <button class="action-btn" onclick="toggleSimpleMenu('${alert.id}')" id="dropdown-${alert.id}">
                                        <i class="fas fa-ellipsis-v"></i>
                                    </button>
                                    <div class="dropdown-menu" id="simple-menu-${alert.id}">
                                        <button class="dropdown-item" onclick="testAlert('${alert.id}'); closeMenu('${alert.id}');">
                                            <i class="fas fa-paper-plane me-2"></i>Test Alert
                                        </button>
                                        <button class="dropdown-item" onclick="showEditAlertModal('${alert.id}'); closeMenu('${alert.id}');">
                                            <i class="fas fa-edit me-2"></i>Edit Alert
                                        </button>
                                        <div class="dropdown-divider"></div>
                                        <button class="dropdown-item" onclick="showDeleteAlertModal('${alert.id}'); closeMenu('${alert.id}');" style="color: #dc3545;">
                                            <i class="fas fa-trash me-2"></i>Delete
                                        </button>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = tableHTML;
    container.style.display = 'block';
    
    console.log(`✅ Successfully displayed ${filteredAlerts.length}/${alerts.length} alerts with counts: All(${allCount}), Active(${activeCount}), Paused(${pausedCount})`);
}

// displayNotifications function removed - replaced with displayNotificationsInTab

/**
 * FILTER FUNCTIONS - ENHANCED
 */
function filterAlertsArray(alerts, filter) {
    switch (filter) {
        case 'active':
            return alerts.filter(a => (a.status || 'active') === 'active');
        case 'paused':
            return alerts.filter(a => a.status === 'paused');
        default:
            return alerts;
    }
}

function filterAlerts(filter) {
    console.log(`🔍 Filtering alerts by: ${filter}`);
    window.AlertsState.currentFilter = filter;
    
    // Regenerate the entire alerts display with the new filter
    displayAlerts();
}

// updateAlertCounts function removed - counts now calculated directly in displayAlerts()

/**
 * TAB SWITCHING - FIXED PROPERLY
 */
function switchAlertsTab(tabName) {
    console.log(`📑 Switching to tab: ${tabName}`);
    
    // Remove active class from all tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    if (tabName === 'alerts') {
        // Show alerts content by calling displayAlerts() to regenerate the content
        displayAlerts();
        
        console.log('✅ Showing alerts tab with content');
    } else if (tabName === 'notifications') {
        // Show notifications in the same container area
        displayNotificationsInTab();
        
        console.log('✅ Showing notifications tab with content');
    }
    
    // Activate the clicked tab
    const targetTab = document.querySelector(`[onclick*="switchAlertsTab('${tabName}')"]`);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    console.log(`✅ Switched to ${tabName} tab`);
}

/**
 * DISPLAY NOTIFICATIONS IN TAB - NEW FUNCTION
 */
function displayNotificationsInTab() {
    const container = document.getElementById('alerts-list-container');
    if (!container) return;
    
    const notifications = window.AlertsState.notifications;
    console.log(`📬 Displaying ${notifications.length} notifications in tab`);
    
    if (notifications.length === 0) {
        container.innerHTML = `
            <div class="notifications-container">
                <div class="empty-state">
                    <i class="fas fa-bell-slash"></i>
                    <h3>No notifications yet</h3>
                    <p>Notifications will appear here when alerts are triggered</p>
                </div>
            </div>
        `;
        container.style.display = 'block';
        return;
    }
    
    const notificationsHTML = `
        <div class="notifications-container">
            <div class="alerts-header">
                <h2 class="alerts-title">NOTIFICATIONS</h2>
                <button class="btn btn-secondary" onclick="markAllAsRead()">
                    <i class="fas fa-check-double"></i> Mark All as Read
                </button>
            </div>
            
            ${notifications.map(notification => `
                <div class="notification-item ${notification.read ? 'read' : 'unread'}" 
                     data-notification-id="${notification.id}">
                    <div class="notification-content">
                        <div class="notification-title">
                            ${escapeHtml(notification.title)}
                            ${!notification.read ? '<span class="notification-badge">New</span>' : ''}
                        </div>
                        <div class="notification-message">
                            ${escapeHtml(notification.message)}
                        </div>
                        <div class="notification-time">
                            <i class="fas fa-clock"></i> ${formatDateTime(notification.timestamp)}
                        </div>
                    </div>
                    <div class="notification-actions">
                        ${!notification.read ? `
                            <button class="btn btn-primary btn-sm" onclick="markAsRead('${notification.id}')">
                                <i class="fas fa-check"></i>
                            </button>
                        ` : ''}
                        <button class="btn btn-secondary btn-sm" onclick="dismissNotification('${notification.id}')">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    container.innerHTML = notificationsHTML;
    container.style.display = 'block';
}

/**
 * MENU FUNCTIONS - ENHANCED POSITIONING WITH DEBUG
 */
function toggleSimpleMenu(alertId) {
    console.log('🔧 Toggling menu for alert:', alertId);
    
    // Close all other menus
    document.querySelectorAll('[id^="simple-menu-"]').forEach(menu => {
        if (menu.id !== `simple-menu-${alertId}`) {
            menu.classList.remove('show', 'dropup');
            menu.style.display = 'none';
        }
    });
    
    // Toggle current menu
    const menu = document.getElementById(`simple-menu-${alertId}`);
    const button = document.getElementById(`dropdown-${alertId}`);
    
    if (menu && button) {
        const isHidden = !menu.classList.contains('show');
        
        if (isHidden) {
            // Show menu temporarily to measure its height
            menu.style.display = 'block';
            menu.style.visibility = 'hidden';
            menu.classList.remove('dropup');
            
            // Get measurements
            const buttonRect = button.getBoundingClientRect();
            const menuHeight = menu.offsetHeight || 200; // fallback height
            const viewportHeight = window.innerHeight;
            const spaceBelow = viewportHeight - buttonRect.bottom;
            const spaceAbove = buttonRect.top;
            
            // Reset styles
            menu.style.visibility = 'visible';
            
            // Determine if menu should show above (dropup) or below (dropdown)
            // Use dropup if there's not enough space below but there is space above
            if (spaceBelow < menuHeight + 10 && spaceAbove > menuHeight + 10) {
                menu.classList.add('dropup');
                console.log(`📍 Alert ${alertId}: Using dropup (space below: ${spaceBelow}px, space above: ${spaceAbove}px, menu height: ${menuHeight}px)`);
            } else {
                menu.classList.remove('dropup');
                console.log(`📍 Alert ${alertId}: Using dropdown (space below: ${spaceBelow}px, space above: ${spaceAbove}px, menu height: ${menuHeight}px)`);
            }
            
            menu.classList.add('show');
        } else {
            menu.classList.remove('show', 'dropup');
            menu.style.display = 'none';
            console.log(`🔧 Closed menu for alert ${alertId}`);
        }
    } else {
        console.error(`❌ Menu or button not found for alert ${alertId}`);
    }
}

function closeMenu(alertId) {
    const menu = document.getElementById(`simple-menu-${alertId}`);
    if (menu) {
        menu.classList.remove('show', 'dropup');
        menu.style.display = 'none';
    }
}

/**
 * MODAL FUNCTIONS
 */
function showCreateAlertModal() {
    const modalHTML = `
        <div class="modal" id="createAlertModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">Create New Alert</h3>
                    <button class="modal-close" onclick="closeModal('createAlertModal')">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="createAlertForm">
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Alert Name *</label>
                                <input type="text" class="form-control" name="name" required 
                                       placeholder="Budget Alert - $1,400">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Email Address *</label>
                                <input type="email" class="form-control" name="email" required 
                                       placeholder="admin@company.com">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Threshold Amount ($) *</label>
                                <input type="number" class="form-control" name="threshold_amount" required 
                                       min="0" step="0.01" placeholder="1400">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Threshold Percentage (%)</label>
                                <input type="number" class="form-control" name="threshold_percentage" 
                                       min="0" max="100" placeholder="80">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Notification Frequency</label>
                                <select class="form-control" name="notification_frequency">
                                    <option value="immediate">🚨 Immediate - Send right away</option>
                                    <option value="hourly">⏰ Hourly - Every hour</option>
                                    <option value="daily" selected>📅 Daily - Once per day</option>
                                    <option value="weekly">📊 Weekly - Once per week</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Alert Type</label>
                                <select class="form-control" name="alert_type">
                                    <option value="cost_threshold">💰 Cost Threshold Alert</option>
                                    <option value="performance">⚡ Performance Alert</option>
                                    <option value="optimization">🎯 Optimization Alert</option>
                                </select>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('createAlertModal')">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button class="btn btn-primary" onclick="createAlert()">
                        <i class="fas fa-plus"></i> Create Alert
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    document.getElementById('createAlertModal').classList.add('show');
}

function showEditAlertModal(alertId) {
    const alert = window.AlertsState.alerts.find(a => a.id == alertId);
    if (!alert) return;
    
    const modalHTML = `
        <div class="modal" id="editAlertModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">Edit Alert</h3>
                    <button class="modal-close" onclick="closeModal('editAlertModal')">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="editAlertForm">
                        <input type="hidden" name="alertId" value="${alert.id}">
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Alert Name *</label>
                                <input type="text" class="form-control" name="name" required 
                                       value="${escapeHtml(alert.name)}">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Email Address *</label>
                                <input type="email" class="form-control" name="email" required 
                                       value="${escapeHtml(alert.email || '')}">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Threshold Amount ($) *</label>
                                <input type="number" class="form-control" name="threshold_amount" required 
                                       min="0" step="0.01" value="${alert.threshold_amount || ''}">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Threshold Percentage (%)</label>
                                <input type="number" class="form-control" name="threshold_percentage" 
                                       min="0" max="100" value="${alert.threshold_percentage || ''}">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Notification Frequency</label>
                                <select class="form-control" name="notification_frequency">
                                    <option value="immediate" ${alert.notification_frequency === 'immediate' ? 'selected' : ''}>🚨 Immediate - Send right away</option>
                                    <option value="hourly" ${alert.notification_frequency === 'hourly' ? 'selected' : ''}>⏰ Hourly - Every hour</option>
                                    <option value="daily" ${alert.notification_frequency === 'daily' || !alert.notification_frequency ? 'selected' : ''}>📅 Daily - Once per day</option>
                                    <option value="weekly" ${alert.notification_frequency === 'weekly' ? 'selected' : ''}>📊 Weekly - Once per week</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Alert Type</label>
                                <select class="form-control" name="alert_type">
                                    <option value="cost_threshold" ${alert.alert_type === 'cost_threshold' || !alert.alert_type ? 'selected' : ''}>💰 Cost Threshold Alert</option>
                                    <option value="performance" ${alert.alert_type === 'performance' ? 'selected' : ''}>⚡ Performance Alert</option>
                                    <option value="optimization" ${alert.alert_type === 'optimization' ? 'selected' : ''}>🎯 Optimization Alert</option>
                                </select>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('editAlertModal')">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button class="btn btn-primary" onclick="updateAlert()">
                        <i class="fas fa-save"></i> Save Changes
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    document.getElementById('editAlertModal').classList.add('show');
}

function showDeleteAlertModal(alertId) {
    const alert = window.AlertsState.alerts.find(a => a.id == alertId);
    if (!alert) return;
    
    const modalHTML = `
        <div class="modal" id="deleteAlertModal">
            <div class="modal-content sleek-delete-modal">
                <div class="modal-body">
                    <div class="delete-modal-content">
                        <div class="warning-icon">⚠️</div>
                        <h3 class="delete-title">Delete Alert</h3>
                        <p class="delete-message">
                            Are you sure you want to delete this<br>
                            alert? This action cannot be undone.
                        </p>
                        <div class="alert-name-display">
                            Alert: <strong>${escapeHtml(alert.name)}</strong>
                        </div>
                    </div>
                </div>
                <div class="modal-footer sleek-footer">
                    <button class="btn btn-secondary-sleek" onclick="closeModal('deleteAlertModal')">
                        Cancel
                    </button>
                    <button class="btn btn-danger-sleek" onclick="confirmDeleteAlert('${alertId}')">
                        Delete Alert
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    document.getElementById('deleteAlertModal').classList.add('show');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 300);
    }
}

/**
 * ALERT ACTIONS
 */
function handleToggleAlert(alertId, shouldActivate) {
    console.log(`🔄 Toggling alert ${alertId} to ${shouldActivate ? 'active' : 'paused'}`);
    
    const alert = window.AlertsState.alerts.find(a => a.id == alertId);
    if (!alert) return;
    
    const newStatus = shouldActivate ? 'active' : 'paused';
    const action = shouldActivate ? 'resume' : 'pause';
    
    // Update UI immediately
    alert.status = newStatus;
    displayAlerts(); // Refresh the display with updated counts
    
    // Send to API
    fetch(`/api/alerts/${alertId}/pause`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            console.log(`✅ Alert ${alertId} ${action}d successfully`);
            showToast('success', `Alert ${action}d successfully`);
        } else {
            alert.status = shouldActivate ? 'paused' : 'active';
            displayAlerts(); // Revert and refresh
            showToast('error', `Failed to ${action} alert`);
        }
    })
    .catch(error => {
        alert.status = shouldActivate ? 'paused' : 'active';
        displayAlerts(); // Revert and refresh
        showToast('error', `Error: ${error.message}`);
    });
}

function testAlert(alertId) {
    console.log('🧪 Testing alert:', alertId);
    
    fetch(`/api/alerts/${alertId}/test`, { method: 'POST' })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                showToast('success', 'Test notification sent successfully!');
            } else {
                showToast('error', 'Failed to send test notification');
            }
        })
        .catch(error => {
            showToast('error', `Error: ${error.message}`);
        });
}

/**
 * ALERT ACTIONS - UPDATED WITH FREQUENCY
 */
function createAlert() {
    const form = document.getElementById('createAlertForm');
    const formData = new FormData(form);
    
    // Validate required fields
    const name = formData.get('name');
    const email = formData.get('email');
    const thresholdAmount = formData.get('threshold_amount');
    
    if (!name || !email || !thresholdAmount) {
        showToast('error', 'Please fill in all required fields');
        return;
    }
    
    const alertData = {
        name: name.trim(),
        email: email.trim(),
        threshold_amount: parseFloat(thresholdAmount) || 0,
        threshold_percentage: parseFloat(formData.get('threshold_percentage')) || 0,
        alert_type: formData.get('alert_type') || 'cost_threshold',
        notification_frequency: formData.get('notification_frequency') || 'daily',
        notification_channels: ['email', 'inapp'],
        status: 'active'
    };
    
    // Add cluster_id if we have one
    if (window.AlertsState.currentClusterId) {
        alertData.cluster_id = window.AlertsState.currentClusterId;
    }
    
    console.log('📤 Creating alert with data:', alertData);
    
    const createBtn = document.querySelector('#createAlertModal .btn-primary');
    const originalText = createBtn.innerHTML;
    createBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
    createBtn.disabled = true;
    
    fetch('/api/alerts', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(alertData)
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`HTTP ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(result => {
        console.log('📥 Create alert response:', result);
        
        if (result.status === 'success') {
            console.log('✅ Alert created successfully');
            showToast('success', 'Alert created successfully!');
            closeModal('createAlertModal');
            loadAlerts(); // Reload alerts to get the new one
        } else {
            throw new Error(result.message || 'Failed to create alert');
        }
    })
    .catch(error => {
        console.error('❌ Error creating alert:', error);
        showToast('error', `Failed to create alert: ${error.message}`);
    })
    .finally(() => {
        createBtn.innerHTML = originalText;
        createBtn.disabled = false;
    });
}

function updateAlert() {
    const form = document.getElementById('editAlertForm');
    const formData = new FormData(form);
    const alertId = formData.get('alertId');
    
    // Validate required fields
    const name = formData.get('name');
    const email = formData.get('email');
    const thresholdAmount = formData.get('threshold_amount');
    
    if (!name || !email || !thresholdAmount) {
        showToast('error', 'Please fill in all required fields');
        return;
    }
    
    const updateData = {
        name: name.trim(),
        email: email.trim(),
        threshold_amount: parseFloat(thresholdAmount) || 0,
        threshold_percentage: parseFloat(formData.get('threshold_percentage')) || 0,
        notification_frequency: formData.get('notification_frequency') || 'daily',
        alert_type: formData.get('alert_type') || 'cost_threshold'
    };
    
    console.log('📤 Updating alert with data:', updateData);
    
    const saveBtn = document.querySelector('#editAlertModal .btn-primary');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    saveBtn.disabled = true;
    
    fetch(`/api/alerts/${alertId}`, {
        method: 'PUT',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(updateData)
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`HTTP ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(result => {
        console.log('📥 Update alert response:', result);
        
        if (result.status === 'success') {
            console.log('✅ Alert updated successfully');
            showToast('success', 'Alert updated successfully!');
            closeModal('editAlertModal');
            loadAlerts(); // Reload alerts to get the updated data
        } else {
            throw new Error(result.message || 'Failed to update alert');
        }
    })
    .catch(error => {
        console.error('❌ Error updating alert:', error);
        showToast('error', `Failed to update alert: ${error.message}`);
    })
    .finally(() => {
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    });
}

function confirmDeleteAlert(alertId) {
    console.log('🗑️ Deleting alert:', alertId);
    
    const deleteBtn = document.querySelector('#deleteAlertModal .btn-danger');
    const originalText = deleteBtn.innerHTML;
    deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
    deleteBtn.disabled = true;
    
    fetch(`/api/alerts/${alertId}`, { 
        method: 'DELETE',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`HTTP ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(result => {
        console.log('📥 Delete alert response:', result);
        
        if (result.status === 'success') {
            // Remove from local state immediately
            window.AlertsState.alerts = window.AlertsState.alerts.filter(a => a.id != alertId);
            displayAlerts();
            showToast('success', 'Alert deleted successfully!');
            closeModal('deleteAlertModal');
        } else {
            throw new Error(result.message || 'Failed to delete alert');
        }
    })
    .catch(error => {
        console.error('❌ Error deleting alert:', error);
        showToast('error', `Failed to delete alert: ${error.message}`);
    })
    .finally(() => {
        deleteBtn.innerHTML = originalText;
        deleteBtn.disabled = false;
    });
}

/**
 * NOTIFICATION FUNCTIONS - REAL API CALLS
 */
function markAsRead(notificationId) {
    console.log('📖 Marking notification as read via API:', notificationId);
    
    fetch(`/api/notifications/${notificationId}/mark-read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            console.log('✅ Notification marked as read via API');
            // Reload notifications to get updated state from backend
            loadNotifications();
            // Re-display notifications if we're on that tab
            if (window.AlertsState.notifications) {
                displayNotificationsInTab();
            }
        } else {
            console.error('❌ Failed to mark notification as read:', result.message);
            showToast('error', 'Failed to mark notification as read');
        }
    })
    .catch(error => {
        console.error('❌ Error marking notification as read:', error);
        showToast('error', `Error: ${error.message}`);
    });
}

function dismissNotification(notificationId) {
    console.log('🗑️ Dismissing notification via API:', notificationId);
    
    fetch(`/api/notifications/${notificationId}/dismiss`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            console.log('✅ Notification dismissed via API');
            // Reload notifications to get updated state from backend
            loadNotifications();
            // Re-display notifications if we're on that tab
            if (window.AlertsState.notifications) {
                displayNotificationsInTab();
            }
        } else {
            console.error('❌ Failed to dismiss notification:', result.message);
            showToast('error', 'Failed to dismiss notification');
        }
    })
    .catch(error => {
        console.error('❌ Error dismissing notification:', error);
        showToast('error', `Error: ${error.message}`);
    });
}

function markAllAsRead() {
    console.log('📖 Marking all notifications as read via API');
    
    fetch('/api/notifications/mark-all-read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            cluster_id: window.AlertsState.currentClusterId
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            console.log('✅ All notifications marked as read via API');
            showToast('success', 'All notifications marked as read');
            // Reload notifications to get updated state from backend
            loadNotifications();
            // Re-display notifications if we're on that tab
            if (window.AlertsState.notifications) {
                displayNotificationsInTab();
            }
        } else {
            console.error('❌ Failed to mark all notifications as read:', result.message);
            showToast('error', 'Failed to mark all notifications as read');
        }
    })
    .catch(error => {
        console.error('❌ Error marking all notifications as read:', error);
        showToast('error', `Error: ${error.message}`);
    });
}

function updateNotificationBadge() {
    const badges = document.querySelectorAll('.notification-badge-count');
    badges.forEach(badge => {
        if (window.AlertsState.unreadNotificationsCount > 0) {
            badge.textContent = window.AlertsState.unreadNotificationsCount;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    });
}

/**
 * TOAST NOTIFICATIONS
 */
function showToast(type, message) {
    const toastHTML = `
        <div class="toast" id="toast-${Date.now()}" style="
            position: fixed; 
            top: 20px; 
            right: 20px; 
            background: ${type === 'success' ? '#28a745' : '#dc3545'}; 
            color: white; 
            padding: 15px 20px; 
            border-radius: 4px; 
            z-index: 3000;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        ">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-times-circle'}"></i>
            ${message}
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', toastHTML);
    
    const toast = document.body.lastElementChild;
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * EXPORT ALERTS
 */
function exportAlerts() {
    const alerts = window.AlertsState.alerts;
    const csv = [
        ['ID', 'Name', 'Email', 'Budget', 'Status', 'Type'],
        ...alerts.map(a => [
            a.id,
            a.name,
            a.email || '',
            a.threshold_amount || 0,
            a.status || 'active',
            a.alert_type || 'cost_threshold'
        ])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'alerts.csv';
    a.click();
    URL.revokeObjectURL(url);
}

/**
 * UTILITY FUNCTIONS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDateTime(dateString) {
    try {
        return new Date(dateString).toLocaleString();
    } catch {
        return dateString || 'Invalid date';
    }
}

/**
 * CLICK OUTSIDE HANDLER - IMPROVED
 */
function setupClickHandlers() {
    document.addEventListener('click', function(event) {
        // Close modals when clicking outside
        if (event.target.classList.contains('modal')) {
            event.target.classList.remove('show');
            setTimeout(() => event.target.remove(), 300);
        }
        
        // Close menus when clicking outside - IMPROVED
        if (!event.target.closest('.dropdown') && 
            !event.target.closest('[id^="simple-menu-"]') &&
            !event.target.closest('button[onclick*="toggleSimpleMenu"]')) {
            
            document.querySelectorAll('[id^="simple-menu-"]').forEach(menu => {
                menu.classList.remove('show', 'dropup');
                menu.style.display = 'none';
            });
        }
    });
}

/**
 * INITIALIZE - PURE API INTEGRATION
 */
function initializeEnhancedAlerts() {
    console.log('🔔 Initializing alerts system with your real APIs...');
    
    // Detect cluster using your URL structure
    const detectedCluster = detectCurrentCluster();
    
    if (detectedCluster) {
        window.AlertsState.currentClusterId = detectedCluster;
        console.log('🎯 Detected cluster for API calls:', detectedCluster);
    } else {
        console.log('⚠️ No cluster detected, will call APIs without cluster filter');
    }
    
    // Setup click handlers
    setupClickHandlers();
    
    // Load real data from your APIs
    loadAlerts();
    loadNotifications();
    
    // Initialize with alerts tab active
    setTimeout(() => {
        switchAlertsTab('alerts');
    }, 200);
    
    console.log('✅ Alerts system initialized - using your real backend APIs only');
}

// Global exports - REAL API FOCUSED
window.switchAlertsTab = switchAlertsTab;
window.filterAlerts = filterAlerts;
window.toggleSimpleMenu = toggleSimpleMenu;
window.closeMenu = closeMenu;
window.handleToggleAlert = handleToggleAlert;
window.testAlert = testAlert;
window.showCreateAlertModal = showCreateAlertModal;
window.showEditAlertModal = showEditAlertModal;
window.showDeleteAlertModal = showDeleteAlertModal;
window.closeModal = closeModal;
window.createAlert = createAlert;
window.updateAlert = updateAlert;
window.confirmDeleteAlert = confirmDeleteAlert;
window.exportAlerts = exportAlerts;
window.displayAlerts = displayAlerts;
window.displayNotificationsInTab = displayNotificationsInTab;
window.markAsRead = markAsRead;
window.dismissNotification = dismissNotification;
window.markAllAsRead = markAllAsRead;
window.detectCurrentCluster = detectCurrentCluster;
window.AlertsState = window.AlertsState;

// Debug functions - REAL API FOCUSED
window.debugAlertsState = function() {
    console.log('🔍 Current AlertsState:', window.AlertsState);
    console.log('🔍 Current URL:', window.location.href);
    console.log('🔍 Detected cluster:', window.AlertsState.currentClusterId);
    console.log('🔍 Alerts count:', window.AlertsState.alerts.length);
    console.log('🔍 Notifications count:', window.AlertsState.notifications.length);
    return window.AlertsState;
};

window.forceLoadAlerts = function() {
    console.log('🔄 Force loading alerts from real API...');
    loadAlerts();
};

window.forceLoadNotifications = function() {
    console.log('🔄 Force loading notifications from real API...');
    loadNotifications();
};

window.redetectCluster = function() {
    console.log('🔄 Re-detecting cluster...');
    const newCluster = detectCurrentCluster();
    window.AlertsState.currentClusterId = newCluster;
    console.log('🎯 New cluster detected:', newCluster);
    loadAlerts();
    loadNotifications();
    return newCluster;
};

window.debugClusterDetection = function() {
    console.log('🔍 Cluster Detection Debug:');
    console.log('- Full URL:', window.location.href);
    console.log('- Pathname:', window.location.pathname);
    
    // Test detection
    const detected = detectCurrentCluster();
    console.log('✅ Detected cluster:', detected);
    
    // Check API URLs that will be called
    const alertsUrl = detected ? `/api/alerts?cluster_id=${detected}` : '/api/alerts';
    const notificationsUrl = detected ? `/api/notifications/in-app?unread_only=false&limit=50&cluster_id=${detected}` : '/api/notifications/in-app?unread_only=false&limit=50';
    
    console.log('📡 Would call alerts API:', alertsUrl);
    console.log('📡 Would call notifications API:', notificationsUrl);
    
    return {
        url: window.location.href,
        clusterId: detected,
        alertsApiUrl: alertsUrl,
        notificationsApiUrl: notificationsUrl
    };
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEnhancedAlerts);
} else {
    initializeEnhancedAlerts();
}

console.log('✅ Enhanced alerts system loaded');