// frontend/static/js/alerts/main.js - MERGED ENHANCED ALERTS SYSTEM

/**
 * Professional modals, notifications panel, proper counts, and global bell icon functionality
 */

// Global state
window.AlertsState = {
    alerts: [],
    notifications: [],
    globalNotifications: [],
    loading: false,
    currentClusterId: null,
    systemAvailable: true,
    currentFilter: 'all',
    unreadNotificationsCount: 0,
    globalUnreadCount: 0
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
 * ENHANCED LOAD NOTIFICATIONS - WITH DEBUGGING
 */
function loadNotifications() {
    console.log('🔄 Loading notifications with enhanced debugging...');
    
    const clusterId = window.AlertsState.currentClusterId;
    
    let url = '/api/notifications/in-app?unread_only=false&limit=50';
    if (clusterId) {
        url += `&cluster_id=${encodeURIComponent(clusterId)}`;
    }
    
    console.log(`📡 Loading notifications from: ${url}`);
    console.log(`🎯 Cluster ID: ${clusterId || 'all clusters'}`);
    
    fetch(url)
        .then(response => {
            console.log(`📡 Notifications API response: ${response.status} ${response.statusText}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📥 Full notifications response:', data);
            
            if (data.status === 'success') {
                window.AlertsState.notifications = data.notifications || [];
                window.AlertsState.unreadNotificationsCount = data.unread_count || 0;
                
                console.log(`✅ Loaded ${window.AlertsState.notifications.length} notifications`);
                console.log(`📬 Unread count: ${window.AlertsState.unreadNotificationsCount}`);
                console.log('📋 Notifications data:', window.AlertsState.notifications);
                
                updateNotificationBadge();
                
                // If we're on the notifications tab, refresh the display
                if (document.querySelector('.nav-tab.active')?.textContent?.includes('Notifications')) {
                    displayNotificationsInTab();
                }
            } else {
                console.log('📭 API returned error:', data.message || 'Unknown error');
                window.AlertsState.notifications = [];
                window.AlertsState.unreadNotificationsCount = 0;
                updateNotificationBadge();
            }
        })
        .catch(error => {
            console.error('❌ Error loading notifications:', error);
            window.AlertsState.notifications = [];
            window.AlertsState.unreadNotificationsCount = 0;
            updateNotificationBadge();
        });
}

/**
 * GLOBAL ALERTS/NOTIFICATIONS LOADER - ALL CLUSTERS
 * This loads alerts and notifications from ALL clusters for the header bell
 */
function loadGlobalNotifications() {
    console.log('🌍 Loading global notifications from all clusters...');
    
    // Load notifications without cluster filter to get ALL notifications
    fetch('/api/notifications/in-app?unread_only=false&limit=100')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.AlertsState.globalNotifications = data.notifications || [];
                window.AlertsState.globalUnreadCount = data.unread_count || 0;
                
                console.log(`🌍 Loaded ${window.AlertsState.globalNotifications.length} global notifications`);
                console.log(`🌍 Global unread count: ${window.AlertsState.globalUnreadCount}`);
                
                // Update header bell with global count
                updateGlobalNotificationBadge();
            }
        })
        .catch(error => {
            console.error('❌ Error loading global notifications:', error);
        });
}

/**
 * ENHANCED NOTIFICATION BADGE UPDATE - TARGETS HEADER BELL ICON
 */
function updateNotificationBadge() {
    console.log(`📬 Updating notification badges with count: ${window.AlertsState.unreadNotificationsCount}`);
    
    // TARGET THE HEADER BELL ICON SPECIFICALLY
    const headerBellIcon = document.querySelector('.fa-bell, .fa-regular.fa-bell');
    const headerBellContainer = headerBellIcon?.closest('div');
    
    if (headerBellIcon && headerBellContainer) {
        // Remove existing badge if any
        const existingBadge = headerBellContainer.querySelector('.notification-count-badge');
        if (existingBadge) {
            existingBadge.remove();
        }
        
        // Add new badge if there are unread notifications
        if (window.AlertsState.unreadNotificationsCount > 0) {
            const badge = document.createElement('span');
            badge.className = 'notification-count-badge absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold animate-pulse';
            badge.textContent = window.AlertsState.unreadNotificationsCount;
            badge.style.cssText = `
                position: absolute;
                top: -4px;
                right: -4px;
                width: 20px;
                height: 20px;
                background-color: #ef4444;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 11px;
                font-weight: bold;
                z-index: 10;
                animation: pulse 2s infinite;
            `;
            
            // Make sure parent is positioned relatively
            headerBellContainer.style.position = 'relative';
            headerBellContainer.appendChild(badge);
            
            console.log(`✅ Header bell badge updated: ${window.AlertsState.unreadNotificationsCount}`);
        } else {
            console.log('📭 Header bell badge hidden (no unread notifications)');
        }
    } else {
        console.log('⚠️ Header bell icon not found');
    }
    
    // ALSO UPDATE TAB BADGE
    const tabNotificationBadge = document.getElementById('notification-badge');
    if (tabNotificationBadge) {
        if (window.AlertsState.unreadNotificationsCount > 0) {
            tabNotificationBadge.textContent = window.AlertsState.unreadNotificationsCount;
            tabNotificationBadge.style.display = 'inline-block';
        } else {
            tabNotificationBadge.style.display = 'none';
        }
    }
    
    // UPDATE TAB TEXT
    const notificationsTab = document.getElementById('notifications-tab-btn');
    if (notificationsTab) {
        const baseText = 'Recent Notifications';
        if (window.AlertsState.unreadNotificationsCount > 0) {
            notificationsTab.innerHTML = `${baseText} <span class="ml-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">${window.AlertsState.unreadNotificationsCount}</span>`;
        } else {
            notificationsTab.innerHTML = baseText;
        }
    }
}

/**
 * UPDATE GLOBAL NOTIFICATION BADGE (HEADER BELL)
 */
function updateGlobalNotificationBadge() {
    const globalCount = window.AlertsState.globalUnreadCount || 0;
    console.log(`🌍 Updating global notification badge with count: ${globalCount}`);
    
    const headerBellIcon = document.querySelector('.fa-bell, .fa-regular.fa-bell');
    const headerBellContainer = headerBellIcon?.closest('div');
    
    if (headerBellIcon && headerBellContainer) {
        // Remove existing global badge
        const existingBadge = headerBellContainer.querySelector('.global-notification-badge');
        if (existingBadge) {
            existingBadge.remove();
        }
        
        // Add new global badge
        if (globalCount > 0) {
            const badge = document.createElement('span');
            badge.className = 'global-notification-badge';
            badge.textContent = globalCount > 99 ? '99+' : globalCount;
            badge.style.cssText = `
                position: absolute;
                top: -4px;
                right: -4px;
                width: 20px;
                height: 20px;
                background-color: #ef4444;
                border: 2px solid white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 10px;
                font-weight: bold;
                z-index: 10;
                animation: pulse 2s infinite;
            `;
            
            headerBellContainer.style.position = 'relative';
            headerBellContainer.appendChild(badge);
            
            console.log(`✅ Global bell badge updated: ${globalCount}`);
        }
    }
}

/**
 * BELL ICON CLICK HANDLER - SHOW GLOBAL NOTIFICATIONS DROPDOWN
 */
function setupBellIconInteraction() {
    const headerBellIcon = document.querySelector('.fa-bell, .fa-regular.fa-bell');
    
    if (headerBellIcon) {
        // Make bell clickable
        headerBellIcon.style.cursor = 'pointer';
        headerBellIcon.title = 'View all notifications';
        
        headerBellIcon.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            console.log('🔔 Bell icon clicked - showing global notifications');
            
            // Show global notifications dropdown
            showGlobalNotificationsDropdown(event);
        });
        
        console.log('✅ Bell icon interaction setup complete');
    }
}

/**
 * SHOW GLOBAL NOTIFICATIONS DROPDOWN
 */
function showGlobalNotificationsDropdown(event) {
    // Remove existing dropdown
    const existingDropdown = document.getElementById('global-notifications-dropdown');
    if (existingDropdown) {
        existingDropdown.remove();
    }
    
    const notifications = window.AlertsState.globalNotifications || [];
    const recentNotifications = notifications.slice(0, 5); // Show last 5
    
    const dropdown = document.createElement('div');
    dropdown.id = 'global-notifications-dropdown';
    dropdown.style.cssText = `
        position: absolute;
        top: 60px;
        right: 20px;
        width: 350px;
        max-height: 400px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        z-index: 1000;
        overflow: hidden;
        border: 1px solid #e5e7eb;
    `;
    
    const dropdownContent = `
        <div style="padding: 16px; border-bottom: 1px solid #e5e7eb; background: #f9fafb;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; font-size: 14px; font-weight: 600; color: #374151;">
                    🔔 All Notifications
                </h3>
                <button onclick="document.getElementById('global-notifications-dropdown').remove()" 
                        style="background: none; border: none; font-size: 18px; cursor: pointer; color: #6b7280;">×</button>
            </div>
            ${window.AlertsState.globalUnreadCount > 0 ? 
                `<p style="margin: 4px 0 0 0; font-size: 12px; color: #ef4444;">${window.AlertsState.globalUnreadCount} unread</p>` : 
                `<p style="margin: 4px 0 0 0; font-size: 12px; color: #6b7280;">All caught up!</p>`
            }
        </div>
        
        <div style="max-height: 300px; overflow-y: auto;">
            ${recentNotifications.length === 0 ? `
                <div style="padding: 32px; text-align: center; color: #6b7280;">
                    <i class="fas fa-bell-slash" style="font-size: 32px; margin-bottom: 8px; display: block;"></i>
                    <p style="margin: 0;">No notifications yet</p>
                </div>
            ` : recentNotifications.map(notification => `
                <div style="padding: 12px 16px; border-bottom: 1px solid #f3f4f6; ${!notification.read ? 'background: #fef3c7;' : ''}" 
                     data-notification-id="${notification.id}">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex-grow: 1;">
                            <div style="font-weight: 500; font-size: 13px; color: #374151; margin-bottom: 4px;">
                                ${escapeHtml(notification.title)}
                                ${!notification.read ? '<span style="color: #ef4444; font-size: 11px; margin-left: 8px;">NEW</span>' : ''}
                            </div>
                            <p style="margin: 0; font-size: 12px; color: #6b7280; line-height: 1.4;">
                                ${escapeHtml(notification.message)}
                            </p>
                            <div style="font-size: 11px; color: #9ca3af; margin-top: 4px;">
                                ${formatDateTime(notification.timestamp)}
                            </div>
                        </div>
                        ${!notification.read ? `
                            <button onclick="markAsReadAndUpdateGlobal('${notification.id}')" 
                                    style="background: #3b82f6; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; margin-left: 8px;">
                                Mark Read
                            </button>
                        ` : ''}
                    </div>
                </div>
            `).join('')}
        </div>
        
        ${recentNotifications.length > 0 ? `
            <div style="padding: 12px 16px; background: #f9fafb; border-top: 1px solid #e5e7eb; text-align: center;">
                <button onclick="navigateToAlertsTab(); document.getElementById('global-notifications-dropdown').remove();" 
                        style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-size: 13px; cursor: pointer;">
                    View All Notifications
                </button>
            </div>
        ` : ''}
    `;
    
    dropdown.innerHTML = dropdownContent;
    document.body.appendChild(dropdown);
    
    // Close on click outside
    setTimeout(() => {
        document.addEventListener('click', function closeDropdown(e) {
            if (!dropdown.contains(e.target)) {
                dropdown.remove();
                document.removeEventListener('click', closeDropdown);
            }
        });
    }, 100);
}

/**
 * AUTO-REFRESH NOTIFICATIONS POLLING
 */
function startNotificationPolling() {
    console.log('🔄 Starting notification polling every 30 seconds...');
    
    setInterval(() => {
        if (window.AlertsState) {
            console.log('🔄 Auto-refreshing notifications...');
            loadNotifications();
            loadGlobalNotifications();
        }
    }, 30000);
}

/**
 * FIXED TAB SWITCHING - MATCHES YOUR ACTUAL HTML STRUCTURE
 */
function switchAlertsTab(tabName) {
    console.log(`📑 Switching to tab: ${tabName}`);
    
    // Remove active class from ALL tab buttons
    const allTabButtons = document.querySelectorAll('.alerts-tab-button');
    allTabButtons.forEach(button => {
        button.classList.remove('active');
        // Reset styling to inactive state
        button.classList.remove('border-blue-500', 'text-blue-600');
        button.classList.add('border-transparent', 'text-gray-500');
    });
    
    // Hide all tab content
    const alertsTabContent = document.getElementById('alerts-tab-content');
    const notificationsTabContent = document.getElementById('notifications-tab-content');
    
    if (tabName === 'alerts') {
        // Show alerts content
        if (alertsTabContent) {
            alertsTabContent.classList.remove('hidden');
            alertsTabContent.classList.add('alerts-tab-content');
        }
        if (notificationsTabContent) {
            notificationsTabContent.classList.add('hidden');
        }
        
        // Activate alerts tab button
        const alertsTabBtn = document.getElementById('alerts-tab-btn');
        if (alertsTabBtn) {
            alertsTabBtn.classList.add('active');
            alertsTabBtn.classList.remove('border-transparent', 'text-gray-500');
            alertsTabBtn.classList.add('border-blue-500', 'text-blue-600');
        }
        
        // Load and display alerts
        displayAlerts();
        
        console.log('✅ Showing alerts tab with content');
        
    } else if (tabName === 'notifications') {
        // Show notifications content
        if (notificationsTabContent) {
            notificationsTabContent.classList.remove('hidden');
        }
        if (alertsTabContent) {
            alertsTabContent.classList.add('hidden');
        }
        
        // Activate notifications tab button
        const notificationsTabBtn = document.getElementById('notifications-tab-btn');
        if (notificationsTabBtn) {
            notificationsTabBtn.classList.add('active');
            notificationsTabBtn.classList.remove('border-transparent', 'text-gray-500');
            notificationsTabBtn.classList.add('border-blue-500', 'text-blue-600');
        }
        
        // Load and display notifications
        displayNotificationsInTab();
        
        console.log('✅ Showing notifications tab with content');
    }
    
    console.log(`✅ Successfully switched to ${tabName} tab`);
}

/**
 * UPDATED DISPLAY ALERTS - NO LONGER REGENERATES TABS
 */
function displayAlerts() {
    const container = document.getElementById('alerts-list-container');
    if (!container) {
        console.log('⚠️ Alerts container not found');
        return;
    }
    
    const alerts = window.AlertsState.alerts;
    console.log(`📋 Displaying ${alerts.length} alerts`);
    
    // Calculate counts for display
    const allCount = alerts.length;
    const activeCount = alerts.filter(a => (a.status || 'active') === 'active').length;
    const pausedCount = alerts.filter(a => a.status === 'paused').length;
    
    // Update the total alerts count in the tab
    const totalCountElement = document.getElementById('total-alerts-count');
    if (totalCountElement) {
        totalCountElement.textContent = allCount;
    }
    
    if (alerts.length === 0) {
        container.innerHTML = `
            <!-- Filter Buttons -->
            <div class="filter-buttons mb-4">
                <div class="flex space-x-2">
                    <button class="filter-btn ${window.AlertsState.currentFilter === 'all' ? 'active' : ''} px-3 py-1 text-sm rounded-full ${window.AlertsState.currentFilter === 'all' ? 'bg-blue-100 text-blue-700 border border-blue-200' : 'bg-gray-100 text-gray-600 border border-gray-200'}" onclick="filterAlerts('all')">
                        All (<span id="all-count">0</span>)
                    </button>
                    <button class="filter-btn ${window.AlertsState.currentFilter === 'active' ? 'active' : ''} px-3 py-1 text-sm rounded-full ${window.AlertsState.currentFilter === 'active' ? 'bg-blue-100 text-blue-700 border border-blue-200' : 'bg-gray-100 text-gray-600 border border-gray-200'}" onclick="filterAlerts('active')">
                        Active (<span id="active-count">0</span>)
                    </button>
                    <button class="filter-btn ${window.AlertsState.currentFilter === 'paused' ? 'active' : ''} px-3 py-1 text-sm rounded-full ${window.AlertsState.currentFilter === 'paused' ? 'bg-blue-100 text-blue-700 border border-blue-200' : 'bg-gray-100 text-gray-600 border border-gray-200'}" onclick="filterAlerts('paused')">
                        Paused (<span id="paused-count">0</span>)
                    </button>
                </div>
            </div>
            
            <div class="empty-state text-center py-8">
                <i class="fas fa-bell-slash text-4xl text-gray-300 mb-4"></i>
                <h3 class="text-lg font-semibold text-gray-600 mb-2">No alerts found</h3>
                <p class="text-gray-500 mb-4">Create your first alert to get started</p>
                <button onclick="showCreateAlertModal()" class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-all duration-300">
                    <i class="fas fa-plus mr-2"></i>Create Alert
                </button>
            </div>
        `;
        return;
    }
    
    // Filter alerts
    const filteredAlerts = filterAlertsArray(alerts, window.AlertsState.currentFilter);
    
    const alertsHTML = `
        <!-- Filter Buttons -->
        <div class="filter-buttons mb-4">
            <div class="flex justify-between items-center">
                <div class="flex space-x-2">
                    <button class="filter-btn ${window.AlertsState.currentFilter === 'all' ? 'active' : ''} px-3 py-1 text-sm rounded-full ${window.AlertsState.currentFilter === 'all' ? 'bg-blue-100 text-blue-700 border border-blue-200' : 'bg-gray-100 text-gray-600 border border-gray-200'}" onclick="filterAlerts('all')">
                        All (<span id="all-count">${allCount}</span>)
                    </button>
                    <button class="filter-btn ${window.AlertsState.currentFilter === 'active' ? 'active' : ''} px-3 py-1 text-sm rounded-full ${window.AlertsState.currentFilter === 'active' ? 'bg-blue-100 text-blue-700 border border-blue-200' : 'bg-gray-100 text-gray-600 border border-gray-200'}" onclick="filterAlerts('active')">
                        Active (<span id="active-count">${activeCount}</span>)
                    </button>
                    <button class="filter-btn ${window.AlertsState.currentFilter === 'paused' ? 'active' : ''} px-3 py-1 text-sm rounded-full ${window.AlertsState.currentFilter === 'paused' ? 'bg-blue-100 text-blue-700 border border-blue-200' : 'bg-gray-100 text-gray-600 border border-gray-200'}" onclick="filterAlerts('paused')">
                        Paused (<span id="paused-count">${pausedCount}</span>)
                    </button>
                </div>
                <button onclick="exportAlerts()" class="bg-orange-500 text-white px-3 py-1 text-sm rounded-lg hover:bg-orange-600 transition-all duration-300">
                    <i class="fas fa-download mr-1"></i>Export Excel
                </button>
            </div>
        </div>
        
        <!-- Alerts List -->
        <div class="alerts-list space-y-3">
            ${filteredAlerts.map((alert, index) => `
                <div class="alert-item bg-gray-50 border rounded-lg p-4 hover:shadow-md transition-all duration-300" data-alert-id="${alert.id}" data-status="${alert.status || 'active'}">
                    <div class="flex items-center justify-between">
                        <div class="flex-grow">
                            <div class="flex items-center gap-3 mb-2">
                                <span class="alert-id font-mono text-sm text-gray-500">#${String(alert.id).padStart(3, '0')}</span>
                                <h4 class="font-semibold text-gray-800">${escapeHtml(alert.name)}</h4>
                                <span class="status-badge px-2 py-1 rounded-full text-xs font-medium ${(alert.status || 'active') === 'active' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}">
                                    ${(alert.status || 'active').charAt(0).toUpperCase() + (alert.status || 'active').slice(1)}
                                </span>
                            </div>
                            <div class="grid grid-cols-3 gap-4 text-sm text-gray-600">
                                <div>
                                    <span class="font-medium">Email:</span> ${escapeHtml(alert.email || 'Not set')}
                                </div>
                                <div>
                                    <span class="font-medium">Budget:</span> $${alert.threshold_amount ? alert.threshold_amount.toLocaleString() : '0'}
                                    ${alert.threshold_percentage ? ` (${alert.threshold_percentage}%)` : ''}
                                </div>
                                <div>
                                    <span class="font-medium">Cluster:</span> ${escapeHtml(alert.cluster_name || 'All clusters')}
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center gap-3">
                            <!-- Toggle Switch -->
                            <div class="alert-toggle-container">
                                <label class="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" class="sr-only peer" ${(alert.status || 'active') === 'active' ? 'checked' : ''} onchange="handleToggleAlert('${alert.id}', this.checked)">
                                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                </label>
                            </div>
                            <!-- Actions Menu -->
                            <div class="relative">
                                <button class="action-btn p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100" onclick="toggleSimpleMenu('${alert.id}')" id="dropdown-${alert.id}">
                                    <i class="fas fa-ellipsis-v"></i>
                                </button>
                                <div class="dropdown-menu absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10 hidden" id="simple-menu-${alert.id}">
                                    <button class="dropdown-item w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center" onclick="testAlert('${alert.id}'); closeMenu('${alert.id}');">
                                        <i class="fas fa-paper-plane mr-2 text-blue-500"></i>Test Alert
                                    </button>
                                    <button class="dropdown-item w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center" onclick="showEditAlertModal('${alert.id}'); closeMenu('${alert.id}');">
                                        <i class="fas fa-edit mr-2 text-green-500"></i>Edit Alert
                                    </button>
                                    <div class="border-t border-gray-200"></div>
                                    <button class="dropdown-item w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center" onclick="showDeleteAlertModal('${alert.id}'); closeMenu('${alert.id}');">
                                        <i class="fas fa-trash mr-2"></i>Delete
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    container.innerHTML = alertsHTML;
    console.log(`✅ Successfully displayed ${filteredAlerts.length}/${alerts.length} alerts`);
}

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

/**
 * ENHANCED DISPLAY NOTIFICATIONS IN TAB
 */
function displayNotificationsInTab() {
    const container = document.getElementById('in-app-notifications-container');
    if (!container) {
        console.log('⚠️ Notifications container not found');
        return;
    }
    
    const notifications = window.AlertsState.notifications;
    console.log(`📬 Displaying ${notifications.length} notifications in tab`);
    
    // Update notification badge in tab
    const notificationBadge = document.getElementById('notification-badge');
    if (notificationBadge) {
        if (window.AlertsState.unreadNotificationsCount > 0) {
            notificationBadge.textContent = window.AlertsState.unreadNotificationsCount;
            notificationBadge.style.display = 'inline-block';
        } else {
            notificationBadge.style.display = 'none';
        }
    }
    
    if (notifications.length === 0) {
        container.innerHTML = `
            <div class="empty-state text-center py-8">
                <i class="fas fa-bell-slash text-4xl text-gray-300 mb-4"></i>
                <h3 class="text-lg font-semibold text-gray-600 mb-2">No notifications yet</h3>
                <p class="text-gray-500">Notifications will appear here when alerts are triggered</p>
            </div>
        `;
        return;
    }
    
    const notificationsHTML = `
        <div class="notifications-header mb-4 flex justify-between items-center">
            <h3 class="font-semibold text-gray-700">Recent Notifications</h3>
            <button onclick="markAllAsRead()" class="bg-blue-500 text-white px-3 py-1 text-sm rounded-lg hover:bg-blue-600 transition-all duration-300">
                <i class="fas fa-check-double mr-1"></i>Mark All Read
            </button>
        </div>
        
        <div class="notifications-list space-y-3">
            ${notifications.map(notification => `
                <div class="notification-item bg-gray-50 border rounded-lg p-4 hover:shadow-md transition-all duration-300 ${notification.read ? 'opacity-70' : ''}" data-notification-id="${notification.id}">
                    <div class="flex items-start justify-between">
                        <div class="flex-grow">
                            <div class="flex items-center gap-2 mb-2">
                                <h4 class="font-semibold text-gray-800">${escapeHtml(notification.title)}</h4>
                                ${!notification.read ? '<span class="bg-red-500 text-white text-xs px-2 py-1 rounded-full">New</span>' : ''}
                            </div>
                            <p class="text-gray-600 text-sm mb-2">${escapeHtml(notification.message)}</p>
                            <div class="text-xs text-gray-500">
                                <i class="fas fa-clock mr-1"></i>${formatDateTime(notification.timestamp)}
                            </div>
                        </div>
                        <div class="flex items-center gap-2 ml-4">
                            ${!notification.read ? `
                                <button onclick="markAsRead('${notification.id}')" class="bg-blue-500 text-white px-2 py-1 text-xs rounded hover:bg-blue-600 transition-all duration-300">
                                    <i class="fas fa-check"></i>
                                </button>
                            ` : ''}
                            <button onclick="dismissNotification('${notification.id}')" class="bg-gray-500 text-white px-2 py-1 text-xs rounded hover:bg-gray-600 transition-all duration-300">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    container.innerHTML = notificationsHTML;
    console.log(`✅ Displayed ${notifications.length} notifications in UI`);
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
    
    const deleteBtn = document.querySelector('#deleteAlertModal .btn-danger-sleek');
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
            loadGlobalNotifications();
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
            loadGlobalNotifications();
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
    
    // First, try to get all notification IDs and mark them individually
    const unreadNotifications = window.AlertsState.notifications.filter(n => !n.read);
    
    if (unreadNotifications.length === 0) {
        showToast('info', 'No unread notifications to mark');
        return;
    }
    
    console.log(`📖 Marking ${unreadNotifications.length} notifications as read individually`);
    
    // Mark each notification as read individually
    const markPromises = unreadNotifications.map(notification => 
        fetch(`/api/notifications/${notification.id}/mark-read`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        }).then(response => response.json())
    );
    
    Promise.all(markPromises)
        .then(results => {
            const successful = results.filter(r => r.status === 'success').length;
            const failed = results.length - successful;
            
            if (failed === 0) {
                console.log('✅ All notifications marked as read via individual API calls');
                showToast('success', `All ${successful} notifications marked as read`);
            } else {
                console.log(`⚠️ ${successful} notifications marked as read, ${failed} failed`);
                showToast('warning', `${successful} marked as read, ${failed} failed`);
            }
            
            // Reload notifications to get updated state from backend
            loadNotifications();
            loadGlobalNotifications();
            // Re-display notifications if we're on that tab
            if (window.AlertsState.notifications) {
                displayNotificationsInTab();
            }
        })
        .catch(error => {
            console.error('❌ Error marking notifications as read:', error);
            showToast('error', `Error: ${error.message}`);
        });
}

/**
 * HELPER FUNCTIONS FOR GLOBAL NOTIFICATIONS
 */
function markAsReadAndUpdateGlobal(notificationId) {
    markAsRead(notificationId);
    // Reload global notifications after marking as read
    setTimeout(() => {
        loadGlobalNotifications();
    }, 500);
}

function navigateToAlertsTab() {
    // Click the alerts navigation item
    const alertsNavLink = document.querySelector('[onclick*="showContent(\'alerts\'"]');
    if (alertsNavLink) {
        alertsNavLink.click();
        // Then switch to notifications tab
        setTimeout(() => {
            if (typeof window.switchAlertsTab === 'function') {
                window.switchAlertsTab('notifications');
            }
        }, 200);
    }
}

/**
 * TOAST NOTIFICATIONS
 */
function showToast(type, message) {
    const colors = {
        'success': '#28a745',
        'error': '#dc3545', 
        'warning': '#ffc107',
        'info': '#17a2b8'
    };
    
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-times-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    
    const toastHTML = `
        <div class="toast" id="toast-${Date.now()}" style="
            position: fixed; 
            top: 20px; 
            right: 20px; 
            background: ${colors[type] || colors.info}; 
            color: ${type === 'warning' ? '#000' : 'white'}; 
            padding: 15px 20px; 
            border-radius: 4px; 
            z-index: 3000;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        ">
            <i class="fas ${icons[type] || icons.info}"></i>
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
 * ENHANCED INITIALIZATION WITH POLLING AND DEBUG HELPERS
 */
function initializeEnhancedAlerts() {
    console.log('🔔 Initializing enhanced alerts system with your real APIs...');
    
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
    
    // Setup bell icon interaction
    setupBellIconInteraction();
    
    // Load real data from your APIs
    loadAlerts();
    loadNotifications();
    loadGlobalNotifications();
    
    // Start polling for new notifications
    startNotificationPolling();
    
    // Initialize with alerts tab active
    setTimeout(() => {
        switchAlertsTab('alerts');
    }, 200);
    
    // Add debug helper to window
    window.debugNotifications = function() {
        console.log('🔍 === NOTIFICATION DEBUG INFO ===');
        console.log('Current State:', window.AlertsState);
        console.log('Notifications:', window.AlertsState.notifications);
        console.log('Global Notifications:', window.AlertsState.globalNotifications);
        console.log('Unread Count:', window.AlertsState.unreadNotificationsCount);
        console.log('Global Unread Count:', window.AlertsState.globalUnreadCount);
        console.log('Cluster ID:', window.AlertsState.currentClusterId);
        
        // Check API directly
        fetch('/api/notifications/in-app?cluster_id=' + window.AlertsState.currentClusterId)
            .then(r => r.json())
            .then(data => console.log('API Result:', data));
    };
    
    // Add alert debugging helper
    window.debugAlertSystem = function() {
        console.log('🚨 === ALERT SYSTEM DEBUG ===');
        console.log('Current cluster costs and thresholds:');
        
        // Check current cluster costs
        fetch(`/api/cluster-costs?cluster_id=${window.AlertsState.currentClusterId}`)
            .then(r => r.json())
            .then(data => {
                console.log('💰 Current cluster costs:', data);
                
                // Compare with alert thresholds
                window.AlertsState.alerts.forEach(alert => {
                    console.log(`🔔 Alert "${alert.name}": threshold ${alert.threshold_amount}, status: ${alert.status}`);
                    if (data.current_cost && alert.threshold_amount) {
                        const diff = data.current_cost - alert.threshold_amount;
                        console.log(`   Current cost ${data.current_cost} vs threshold ${alert.threshold_amount} = ${diff > 0 ? 'EXCEEDED by $' + Math.abs(diff) : 'OK, $' + Math.abs(diff) + ' remaining'}`);
                    }
                });
            })
            .catch(e => console.log('❌ Could not fetch cluster costs:', e));
            
        // Check alert evaluation endpoint
        fetch(`/api/alerts/evaluate?cluster_id=${window.AlertsState.currentClusterId}`)
            .then(r => r.json())
            .then(data => console.log('🔄 Alert evaluation result:', data))
            .catch(e => console.log('❌ Could not evaluate alerts:', e));
    };
    
    console.log('✅ Enhanced alerts system initialized - using your real backend APIs only');
    console.log('💡 Debug helpers available:');
    console.log('   - window.debugNotifications() - Debug notification system');
    console.log('   - window.debugAlertSystem() - Debug alert thresholds vs costs');
}

// Global exports - COMPREHENSIVE MERGED SYSTEM
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
window.loadNotifications = loadNotifications;
window.loadGlobalNotifications = loadGlobalNotifications;
window.updateNotificationBadge = updateNotificationBadge;
window.updateGlobalNotificationBadge = updateGlobalNotificationBadge;
window.setupBellIconInteraction = setupBellIconInteraction;
window.markAsReadAndUpdateGlobal = markAsReadAndUpdateGlobal;
window.navigateToAlertsTab = navigateToAlertsTab;
window.AlertsState = window.AlertsState;

// Debug functions - COMPREHENSIVE MERGED SYSTEM
window.debugAlertsState = function() {
    console.log('🔍 Current AlertsState:', window.AlertsState);
    console.log('🔍 Current URL:', window.location.href);
    console.log('🔍 Detected cluster:', window.AlertsState.currentClusterId);
    console.log('🔍 Alerts count:', window.AlertsState.alerts.length);
    console.log('🔍 Notifications count:', window.AlertsState.notifications.length);
    console.log('🔍 Global notifications count:', window.AlertsState.globalNotifications.length);
    return window.AlertsState;
};

window.forceLoadAlerts = function() {
    console.log('🔄 Force loading alerts from real API...');
    loadAlerts();
};

window.forceLoadNotifications = function() {
    console.log('🔄 Force loading notifications from real API...');
    loadNotifications();
    loadGlobalNotifications();
};

window.redetectCluster = function() {
    console.log('🔄 Re-detecting cluster...');
    const newCluster = detectCurrentCluster();
    window.AlertsState.currentClusterId = newCluster;
    console.log('🎯 New cluster detected:', newCluster);
    loadAlerts();
    loadNotifications();
    loadGlobalNotifications();
    return newCluster;
};

window.debugClusterDetection = function() {
    console.log('🔍 Cluster Detection Debug:');
    console.log('- Full URL:', window.location.href);
    console.log('- Pathname:', window.location.pathname);
    
    // Check detection
    const detected = detectCurrentCluster();
    console.log('✅ Detected cluster:', detected);
    
    // Check API URLs that will be called
    const alertsUrl = detected ? `/api/alerts?cluster_id=${detected}` : '/api/alerts';
    const notificationsUrl = detected ? `/api/notifications/in-app?unread_only=false&limit=50&cluster_id=${detected}` : '/api/notifications/in-app?unread_only=false&limit=50';
    const globalNotificationsUrl = '/api/notifications/in-app?unread_only=false&limit=100';
    
    console.log('📡 Would call alerts API:', alertsUrl);
    console.log('📡 Would call notifications API:', notificationsUrl);
    console.log('📡 Would call global notifications API:', globalNotificationsUrl);
    
    return {
        url: window.location.href,
        clusterId: detected,
        alertsApiUrl: alertsUrl,
        notificationsApiUrl: notificationsUrl,
        globalNotificationsApiUrl: globalNotificationsUrl
    };
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEnhancedAlerts);
} else {
    initializeEnhancedAlerts();
}

console.log('✅ Merged Enhanced alerts system loaded with global bell icon functionality');