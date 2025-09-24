// frontend/static/js/alerts/main.js - COMPLETE FIXED ENHANCED ALERTS SYSTEM

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
 * CLUSTER-SPECIFIC NOTIFICATIONS LOADER - FILTERED BY CURRENT CLUSTER
 * This loads notifications only for the current cluster for the header bell
 */
function loadGlobalNotifications() {
    console.log('🔔 Loading cluster-specific notifications for bell icon...');
    
    const clusterId = window.AlertsState.currentClusterId;
    
    // Build URL with cluster filter if we have a cluster ID
    let url = '/api/notifications/in-app?unread_only=false&limit=100';
    if (clusterId) {
        url += `&cluster_id=${encodeURIComponent(clusterId)}`;
        console.log(`🎯 Loading notifications for cluster: ${clusterId}`);
    } else {
        console.log('🌍 No cluster detected, loading all notifications');
    }
    
    fetch(url)
        .then(response => {
            console.log(`🔔 Cluster notifications API response: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('🔔 Cluster notifications API data:', data);
            
            if (data.status === 'success') {
                window.AlertsState.globalNotifications = data.notifications || [];
                window.AlertsState.globalUnreadCount = data.unread_count || 0;
                
                console.log(`🔔 Loaded ${window.AlertsState.globalNotifications.length} cluster-specific notifications`);
                console.log(`🔔 Cluster unread count: ${window.AlertsState.globalUnreadCount}`);
                console.log(`🎯 Filtered for cluster: ${clusterId || 'all clusters'}`);
                
                // Update header bell with cluster-specific count
                updateGlobalNotificationBadge();
            } else {
                console.log('🔔 Cluster notifications API error:', data.message);
                window.AlertsState.globalNotifications = [];
                window.AlertsState.globalUnreadCount = 0;
                updateGlobalNotificationBadge();
            }
        })
        .catch(error => {
            console.error('❌ Error loading cluster notifications:', error);
            window.AlertsState.globalNotifications = [];
            window.AlertsState.globalUnreadCount = 0;
            updateGlobalNotificationBadge();
        });
}

/**
 * FIXED NOTIFICATION BADGE UPDATE - TARGETS HEADER BELL ICON
 */
function updateNotificationBadge() {
    console.log(`📬 Updating notification badges with count: ${window.AlertsState.unreadNotificationsCount}`);
    
    // TARGET THE HEADER BELL ICON SPECIFICALLY - Updated to match your HTML
    const headerBellIcon = document.querySelector('#global-notification-badge, .fa-regular.fa-bell');
    const headerBellContainer = headerBellIcon?.closest('.relative');
    
    if (headerBellIcon && headerBellContainer) {
        // Remove existing badges (both custom and the static one from your HTML)
        const existingBadges = headerBellContainer.querySelectorAll('.notification-count-badge, .absolute.-top-1.-right-1');
        existingBadges.forEach(badge => badge.remove());
        
        // Add new badge if there are unread notifications
        if (window.AlertsState.unreadNotificationsCount > 0) {
            const badge = document.createElement('span');
            badge.className = 'notification-count-badge absolute -top-1 -right-1 min-w-[20px] h-5 bg-red-500 rounded-full flex items-center justify-content text-white text-xs font-bold animate-pulse';
            badge.textContent = window.AlertsState.unreadNotificationsCount > 99 ? '99+' : window.AlertsState.unreadNotificationsCount;
            
            // Minimal inline styles for fine-tuning
            badge.style.cssText = `
                font-size: 10px;
                line-height: 1;
                padding: 2px 4px;
                z-index: 10;
            `;
            
            headerBellContainer.appendChild(badge);
            console.log(`✅ Header bell badge updated: ${window.AlertsState.unreadNotificationsCount}`);
        } else {
            // Show static dot when no count (optional - remove if you don't want this)
            const staticBadge = document.createElement('span');
            staticBadge.className = 'absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse';
            headerBellContainer.appendChild(staticBadge);
            console.log('📭 Header bell badge reset to static dot');
        }
    } else {
        console.log('⚠️ Header bell icon not found');
    }
    
    // UPDATE TAB BADGE (only if element exists)
    const tabNotificationBadge = document.getElementById('notification-badge');
    if (tabNotificationBadge) {
        if (window.AlertsState.unreadNotificationsCount > 0) {
            tabNotificationBadge.textContent = window.AlertsState.unreadNotificationsCount > 99 ? '99+' : window.AlertsState.unreadNotificationsCount;
            tabNotificationBadge.style.display = 'inline-block';
        } else {
            tabNotificationBadge.style.display = 'none';
        }
    }
    
    // UPDATE TAB TEXT (only if element exists)
    const notificationsTab = document.getElementById('notifications-tab-btn');
    if (notificationsTab) {
        const baseText = 'Recent Notifications';
        if (window.AlertsState.unreadNotificationsCount > 0) {
            const count = window.AlertsState.unreadNotificationsCount > 99 ? '99+' : window.AlertsState.unreadNotificationsCount;
            notificationsTab.innerHTML = `${baseText} <span class="ml-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">${count}</span>`;
        } else {
            notificationsTab.innerHTML = baseText;
        }
    }
}

/**
 * UPDATE CLUSTER NOTIFICATION BADGE (HEADER BELL) - CLUSTER-SPECIFIC FILTERING
 */
function updateGlobalNotificationBadge() {
    const globalCount = window.AlertsState.globalUnreadCount || 0;
    console.log(`🔔 Updating cluster notification badge with count: ${globalCount}`);
    
    // Target the specific bell icon by ID or class
    const headerBellIcon = document.querySelector('#global-notification-badge, .fa-regular.fa-bell');
    const headerBellContainer = headerBellIcon?.closest('.relative');
    
    if (headerBellIcon && headerBellContainer) {
        // Remove existing badge (both custom and static)
        const existingBadges = headerBellContainer.querySelectorAll('.global-notification-badge, .absolute.-top-1.-right-1, .notification-count-badge');
        existingBadges.forEach(badge => badge.remove());
        
        // Add new badge with count
        if (globalCount > 0) {
            const badge = document.createElement('span');
            badge.className = 'global-notification-badge absolute -top-1 -right-1 min-w-[20px] h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold animate-pulse';
            badge.textContent = globalCount > 99 ? '99+' : globalCount;
            
            // Additional inline styles for better positioning
            badge.style.cssText = `
                font-size: 10px;
                line-height: 1;
                padding: 2px 4px;
                z-index: 10;
            `;
            
            headerBellContainer.appendChild(badge);
            console.log(`✅ Cluster bell badge updated: ${globalCount}`);
        } else {
            // Show static dot when count is 0
            const staticBadge = document.createElement('span');
            staticBadge.className = 'absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse';
            headerBellContainer.appendChild(staticBadge);
            console.log(`✅ Cluster bell badge set to static dot (count: 0)`);
        }
    } else {
        console.warn('❌ Bell icon or container not found for cluster badge update');
    }
}

/**
 * FIXED BELL ICON INTERACTION - TARGETS YOUR SPECIFIC HTML
 */
function setupBellIconInteraction() {
    // Target your specific bell icon by ID first, then fallback to class
    const headerBellIcon = document.querySelector('#global-notification-badge') || 
                          document.querySelector('.fa-regular.fa-bell') || 
                          document.querySelector('.fa-bell');
    
    if (headerBellIcon) {
        console.log('✅ Found bell icon:', headerBellIcon);
        
        // Make bell clickable with better styling
        headerBellIcon.style.cursor = 'pointer';
        headerBellIcon.title = 'View all notifications';
        
        // Remove any existing listeners to prevent duplicates
        headerBellIcon.removeEventListener('click', bellClickHandler);
        headerBellIcon.addEventListener('click', bellClickHandler);
        
        console.log('✅ Bell icon interaction setup complete');
    } else {
        console.error('❌ Bell icon not found! Selectors tried: #global-notification-badge, .fa-regular.fa-bell, .fa-bell');
        
        // Debug: show what elements exist
        console.log('Available bell-like elements:');
        document.querySelectorAll('[class*="bell"], [id*="bell"], [id*="notification"]').forEach(el => {
            console.log('- Found element:', el.tagName, el.className, el.id);
        });
    }
}

/**
 * BELL CLICK HANDLER - SEPARATED FOR BETTER DEBUGGING
 */
function bellClickHandler(event) {
    event.preventDefault();
    event.stopPropagation();
    
    console.log('🔔 Bell icon clicked - showing cluster notifications');
    console.log('🔔 Cluster notifications count:', window.AlertsState.globalNotifications?.length || 0);
    console.log('🔔 Cluster unread count:', window.AlertsState.globalUnreadCount || 0);
    console.log('🎯 Current cluster:', window.AlertsState.currentClusterId || 'all clusters');
    
    // Show cluster notifications dropdown
    showGlobalNotificationsDropdown(event);
}

/**
 * ENHANCED CLUSTER NOTIFICATIONS DROPDOWN - CLUSTER-SPECIFIC FILTERING
 */
function showGlobalNotificationsDropdown(event) {
    console.log('🔔 Creating cluster notifications dropdown...');
    
    // Remove existing dropdown
    const existingDropdown = document.getElementById('global-notifications-dropdown');
    if (existingDropdown) {
        existingDropdown.remove();
    }
    
    // Get notifications data
    const notifications = window.AlertsState.globalNotifications || [];
    const recentNotifications = notifications.slice(0, 5); // Show last 5
    const unreadCount = window.AlertsState.globalUnreadCount || 0;
    
    console.log('🔔 Showing', recentNotifications.length, 'notifications, unread:', unreadCount);
    
    // Create dropdown with better positioning
    const dropdown = document.createElement('div');
    dropdown.id = 'global-notifications-dropdown';
    
    // Get bell icon position for better dropdown placement
    const bellIcon = event.target.closest('.relative') || event.target;
    const bellRect = bellIcon.getBoundingClientRect();
    
    dropdown.style.cssText = `
        position: fixed;
        top: ${bellRect.bottom + 10}px;
        right: ${window.innerWidth - bellRect.right}px;
        width: 350px;
        max-width: 90vw;
        max-height: 500px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        z-index: 99999;
        overflow: hidden;
        border: 1px solid #e5e7eb;
        transform: translateY(-5px);
        opacity: 0;
        transition: all 0.2s ease-out;
    `;
    
    // Create dropdown content
    const dropdownContent = `
        <div style="padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); background: #171d33; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; font-size: 16px; font-weight: 600;">
                    🔔 ${window.AlertsState.currentClusterId ? 'Cluster' : 'All'} Notifications
                </h3>
                <button onclick="closeNotificationsDropdown()" 
                        style="background: rgba(255,255,255,0.2); border: none; color: white; width: 28px; height: 28px; border-radius: 50%; font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center;">×</button>
            </div>
            ${window.AlertsState.currentClusterId ? 
                `<p style="margin: 4px 0 0 0; font-size: 12px; opacity: 0.7;">🎯 ${window.AlertsState.currentClusterId}</p>` : 
                ''
            }
            ${unreadCount > 0 ? 
                `<p style="margin: 8px 0 0 0; font-size: 14px; opacity: 0.9;">${unreadCount} unread notification${unreadCount === 1 ? '' : 's'}</p>` : 
                `<p style="margin: 8px 0 0 0; font-size: 14px; opacity: 0.9;">All caught up! 🎉</p>`
            }
        </div>
        
        <div style="max-height: 400px; overflow-y: auto;">
            ${recentNotifications.length === 0 ? `
                <div style="padding: 40px 20px; text-align: center; color: #6b7280;">
                    <div style="font-size: 48px; margin-bottom: 16px;">🔕</div>
                    <h4 style="margin: 0 0 8px 0; color: #374151;">No notifications yet</h4>
                    <p style="margin: 0; font-size: 14px;">When alerts are triggered, you'll see them here</p>
                </div>
            ` : recentNotifications.map(notification => `
                <div style="padding: 16px; border-bottom: 1px solid #f3f4f6; ${!notification.read ? 'background: linear-gradient(90deg, #fef3c7 0%, #fef3c7 4px, #ffffff 4px);' : ''} hover:background-color: #f9fafb; cursor: pointer;" 
                     data-notification-id="${notification.id}"
                     onclick="handleNotificationClick('${notification.id}')">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex-grow: 1; padding-right: 12px;">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                                <div style="font-weight: 600; font-size: 14px; color: #374151;">
                                    ${escapeHtml(notification.title)}
                                </div>
                                ${!notification.read ? '<div style="width: 8px; height: 8px; background: #ef4444; border-radius: 50%; flex-shrink: 0;"></div>' : ''}
                            </div>
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #6b807bff; line-height: 1.4;">
                                ${escapeHtml(notification.message)}
                            </p>
                            <div style="font-size: 12px; color: #9cafadff;">
                                ${formatDateTime(notification.timestamp)}
                            </div>
                        </div>
                        ${!notification.read ? `
                            <button id="mark-read-${notification.id}" class="mark-read-btn" data-notification-id="${notification.id}"
                                    style="background: #171d34; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; white-space: nowrap;">
                                Mark Read
                            </button>
                        ` : ''}
                    </div>
                </div>
            `).join('')}
        </div>
        
        ${recentNotifications.length > 0 ? `
            <div style="padding: 16px; background: #f9fafb; border-top: 1px solid #e5e7eb; display: flex; gap: 8px;">
                ${unreadCount > 0 ? `
                    <button id="mark-all-read-global" class="mark-all-read-btn"
                            style="flex: 1; background: #171d34; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer;">
                        Mark All Read
                    </button>
                ` : ''}
                <button onclick="navigateToAlertsTab(); closeNotificationsDropdown();" 
                        style="flex: 1; background: #171d34; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer;">
                    View All
                </button>
            </div>
        ` : ''}
    `;
    
    dropdown.innerHTML = dropdownContent;
    document.body.appendChild(dropdown);
    
    // Add event listeners for buttons IMMEDIATELY after creation
    setupDropdownEventListeners(dropdown);
    
    // Animate in
    requestAnimationFrame(() => {
        dropdown.style.opacity = '1';
        dropdown.style.transform = 'translateY(0)';
    });
    
    // Close on click outside
    setTimeout(() => {
        document.addEventListener('click', function closeDropdown(e) {
            if (!dropdown.contains(e.target) && !e.target.closest('#global-notification-badge')) {
                closeNotificationsDropdown();
                document.removeEventListener('click', closeDropdown);
            }
        });
    }, 100);
    
    console.log('✅ Notifications dropdown created and shown');
}

/**
 * CLOSE NOTIFICATIONS DROPDOWN
 */
function closeNotificationsDropdown() {
    const dropdown = document.getElementById('global-notifications-dropdown');
    if (dropdown) {
        dropdown.style.opacity = '0';
        dropdown.style.transform = 'translateY(-10px)';
        setTimeout(() => dropdown.remove(), 200);
    }
}

/**
 * SETUP EVENT LISTENERS FOR DROPDOWN BUTTONS - FIXES DOUBLE-CLICK ISSUE
 */
function setupDropdownEventListeners(dropdown) {
    console.log('🔧 Setting up dropdown event listeners...');
    
    // Setup individual "Mark Read" button listeners
    const markReadButtons = dropdown.querySelectorAll('.mark-read-btn');
    markReadButtons.forEach(button => {
        const notificationId = button.getAttribute('data-notification-id');
        button.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            console.log(`🔔 Mark Read clicked for notification: ${notificationId}`);
            markAsReadAndUpdateGlobal(notificationId);
        });
    });
    
    // Setup "Mark All Read" button listener
    const markAllButton = dropdown.querySelector('.mark-all-read-btn');
    if (markAllButton) {
        markAllButton.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            console.log('🔔 Mark All Read clicked');
            markAllGlobalAsRead();
        });
    }
    
    console.log(`✅ Setup ${markReadButtons.length} Mark Read buttons and ${markAllButton ? 1 : 0} Mark All Read button`);
}

/**
 * REFRESH NOTIFICATIONS DROPDOWN CONTENT - IN-PLACE UPDATE
 */
function refreshNotificationsDropdown() {
    const existingDropdown = document.getElementById('global-notifications-dropdown');
    if (existingDropdown) {
        console.log('🔄 Refreshing notifications dropdown content in-place...');
        
        // Hide all "Mark Read" buttons since all notifications are now read
        const markReadButtons = existingDropdown.querySelectorAll('[id^="mark-read-"]');
        markReadButtons.forEach(button => {
            if (button.parentElement) {
                button.parentElement.style.display = 'none';
            }
        });
        
        // Update the header to show "All caught up!"
        const headerText = existingDropdown.querySelector('p[style*="margin: 8px 0 0 0"]');
        if (headerText) {
            headerText.innerHTML = 'All caught up! 🎉';
        }
        
        // Hide the "Mark All Read" button
        const markAllButton = existingDropdown.querySelector('#mark-all-read-global');
        if (markAllButton && markAllButton.parentElement) {
            markAllButton.parentElement.style.display = 'none';
        }
        
        // Remove the unread indicators (yellow left border)
        const notificationItems = existingDropdown.querySelectorAll('[style*="linear-gradient(90deg, #fef3c7"]');
        notificationItems.forEach(item => {
            item.style.background = 'white';
        });
        
        // Remove unread dots
        const unreadDots = existingDropdown.querySelectorAll('[style*="width: 8px; height: 8px; background: #ef4444"]');
        unreadDots.forEach(dot => {
            dot.style.display = 'none';
        });
        
        console.log('✅ Dropdown content updated to reflect all notifications as read');
    }
}

/**
 * HANDLE NOTIFICATION CLICK
 */
function handleNotificationClick(notificationId) {
    console.log('📱 Notification clicked:', notificationId);
    
    const notification = window.AlertsState.globalNotifications.find(n => n.id === notificationId);
    if (notification && !notification.read) {
        markAsReadAndUpdateGlobal(notificationId);
    }
    
    // Could navigate to specific alert or take other action here
}

/**
 * MARK ALL GLOBAL NOTIFICATIONS AS READ
 */
function markAllGlobalAsRead() {
    console.log('📖 Marking all global notifications as read (DROPDOWN function)...');
    console.log('📊 Current state check:');
    console.log('  - notifications array length:', window.AlertsState.notifications?.length || 0);
    console.log('  - globalNotifications array length:', window.AlertsState.globalNotifications?.length || 0);
    console.log('  - unreadNotificationsCount:', window.AlertsState.unreadNotificationsCount || 0);
    console.log('  - globalUnreadCount:', window.AlertsState.globalUnreadCount || 0);
    
    // Check both notification arrays for unread notifications
    const unreadNotifications = window.AlertsState.notifications?.filter(n => !n.read) || [];
    const unreadGlobalNotifications = window.AlertsState.globalNotifications?.filter(n => !n.read) || [];
    
    console.log('  - unread in notifications array:', unreadNotifications.length);
    console.log('  - unread in globalNotifications array:', unreadGlobalNotifications.length);
    
    // Use the array with more unread notifications, prefer globalNotifications for dropdown
    const notificationsToMark = unreadGlobalNotifications.length > 0 ? unreadGlobalNotifications : unreadNotifications;
    
    if (notificationsToMark.length === 0) {
        console.log('⚠️ No unread notifications found in either array');
        showToast('info', 'No unread notifications');
        return;
    }
    
    // Disable the button to prevent double-clicking
    const button = document.getElementById('mark-all-read-global');
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Marking...';
        button.style.opacity = '0.6';
    }
    
    console.log(`📖 Marking ${notificationsToMark.length} global notifications as read individually`);
    
    // Mark each notification as read
    const markPromises = notificationsToMark.map(notification => 
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
            
            if (successful > 0) {
                showToast('success', `${successful} notifications marked as read`);
                
                // Immediately update counts and mark all notifications as read locally
                window.AlertsState.unreadNotificationsCount = 0;
                window.AlertsState.globalUnreadCount = 0;
                
                // Mark all notifications in both arrays as read
                if (window.AlertsState.notifications) {
                    window.AlertsState.notifications.forEach(notification => {
                        notification.read = true;
                    });
                }
                if (window.AlertsState.globalNotifications) {
                    window.AlertsState.globalNotifications.forEach(notification => {
                        notification.read = true;
                    });
                }
                
                updateNotificationBadge();
                updateGlobalNotificationBadge();
                
                loadGlobalNotifications();
                loadNotifications();
                
                // Close and reopen dropdown to show fresh data from backend
                setTimeout(() => {
                    closeNotificationsDropdown();
                    setTimeout(() => {
                        // Bell icon will show updated state when clicked again
                        console.log('✅ Dropdown closed - bell icon will show updated state when clicked');
                    }, 200);
                }, 500);
            }
            
            // Update button state
            if (button) {
                button.innerHTML = '✓ All Read';
                button.style.background = '#059669';
            }
        })
        .catch(error => {
            console.error('❌ Error marking all as read:', error);
            showToast('error', 'Failed to mark notifications as read');
            
            // Re-enable button on error
            if (button) {
                button.disabled = false;
                button.innerHTML = 'Mark All Read';
                button.style.opacity = '1';
                button.style.background = '#10b981';
            }
        });
}

/**
 * MANUAL REFRESH NOTIFICATIONS - TRIGGERED BY USER ACTION OR ANALYSIS COMPLETION
 * 
 * Call this function when:
 * - Analysis completes (new alerts may have been generated)
 * - User manually clicks a refresh button
 * - User navigates to notifications section
 * - After performing actions that might affect notifications
 * 
 * NO automatic polling - notifications only update when analysis runs!
 */
function refreshNotificationsManually() {
    console.log('🔄 Manually refreshing notifications (triggered by user action or analysis)...');
    
    if (window.AlertsState) {
        loadNotifications();
        loadGlobalNotifications();
    }
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
                <div class="alert-item border rounded p-4" style="background: rgba(51, 65, 85, 0.3); border: 1px solid rgba(255,255,255,0.1);" data-alert-id="${alert.id}" data-status="${alert.status || 'active'}">
                    <div class="flex items-center justify-between">
                        <div class="flex-grow">
                            <div class="flex items-center gap-3 mb-2">
                                <span class="alert-id font-mono text-sm" style="color: rgb(156, 163, 175);">#${String(alert.id).padStart(3, '0')}</span>
                                <h4 class="font-semibold" style="color: white;">${escapeHtml(alert.name)}</h4>
                                <span class="status-badge px-2 py-1 rounded text-xs font-medium" style="background: ${(alert.status || 'active') === 'active' ? 'rgba(34, 197, 94, 0.2); color: rgb(74, 222, 128)' : 'rgba(251, 191, 36, 0.2); color: rgb(250, 204, 21)'};">
                                    ${(alert.status || 'active').charAt(0).toUpperCase() + (alert.status || 'active').slice(1)}
                                </span>
                            </div>
                            <div class="grid grid-cols-3 gap-4 text-sm" style="color: rgb(203, 213, 225);">
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
                                    <div style="width: 2.75rem; height: 1.5rem; background: ${(alert.status || 'active') === 'active' ? 'rgb(22 28 50)' : 'rgba(107, 114, 128, 0.5)'}; border-radius: 9999px; position: relative;">
                                        <div style="position: absolute; top: 2px; left: ${(alert.status || 'active') === 'active' ? '22px' : '2px'}; width: 20px; height: 20px; background: white; border-radius: 50%;"></div>
                                    </div>
                                </label>
                            </div>
                            <!-- Actions Menu -->
                            <div class="relative">
                                <button class="action-btn p-2 rounded" style="color: rgb(156, 163, 175); background: rgba(75, 85, 99, 0.3);" onclick="toggleSimpleMenu('${alert.id}')" id="dropdown-${alert.id}">
                                    <i class="fas fa-ellipsis-v"></i>
                                </button>
                                <div class="dropdown-menu absolute right-0 mt-1 w-48 rounded border z-10 hidden" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);" id="simple-menu-${alert.id}">
                                    <button class="dropdown-item w-full text-left px-4 py-2 text-sm flex items-center" style="color: rgb(203, 213, 225);" onclick="testAlert('${alert.id}'); closeMenu('${alert.id}');">
                                        <i class="fas fa-paper-plane mr-2 text-blue-400"></i>Test Alert
                                    </button>
                                    <button class="dropdown-item w-full text-left px-4 py-2 text-sm flex items-center" style="color: rgb(203, 213, 225);" onclick="showEditAlertModal('${alert.id}'); closeMenu('${alert.id}');">
                                        <i class="fas fa-edit mr-2 text-emerald-400"></i>Edit Alert
                                    </button>
                                    <div style="border-top: 1px solid rgba(255,255,255,0.1);"></div>
                                    <button class="dropdown-item w-full text-left px-4 py-2 text-sm flex items-center" style="color: rgb(248, 113, 113);" onclick="showDeleteAlertModal('${alert.id}'); closeMenu('${alert.id}');">
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
        <div class="modal" id="createAlertModal" style="background: rgba(0,0,0,0.8);">
            <div class="modal-content" style="background: rgb(30, 41, 59); color: white; border: 1px solid rgba(255,255,255,0.1);">
                <div class="modal-header" style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                    <h3 class="modal-title" style="color: white;">Create New Alert</h3>
                    <button class="modal-close" onclick="closeModal('createAlertModal')" style="background: rgba(255,255,255,0.1); color: white;">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="createAlertForm">
                        <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <div class="form-group">
                                <label class="form-label" style="color: rgb(203, 213, 225); font-weight: 500; margin-bottom: 0.5rem;">Alert Name *</label>
                                <input type="text" class="form-control" name="name" required 
                                       style="background: rgba(51, 65, 85, 0.8); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.75rem; border-radius: 8px;"
                                       placeholder="Budget Alert - $1,400">
                            </div>
                            <div class="form-group">
                                <label class="form-label" style="color: rgb(203, 213, 225); font-weight: 500; margin-bottom: 0.5rem;">Email Address *</label>
                                <input type="email" class="form-control" name="email" required 
                                       style="background: rgba(51, 65, 85, 0.8); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.75rem; border-radius: 8px;"
                                       placeholder="admin@company.com">
                            </div>
                        </div>
                        
                        <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <div class="form-group">
                                <label class="form-label" style="color: rgb(203, 213, 225); font-weight: 500; margin-bottom: 0.5rem;">Threshold Amount ($) *</label>
                                <input type="number" class="form-control" name="threshold_amount" required 
                                       style="background: rgba(51, 65, 85, 0.8); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.75rem; border-radius: 8px;"
                                       min="0" step="0.01" placeholder="1400">
                            </div>
                            <div class="form-group">
                                <label class="form-label" style="color: rgb(203, 213, 225); font-weight: 500; margin-bottom: 0.5rem;">Threshold Percentage (%)</label>
                                <input type="number" class="form-control" name="threshold_percentage" 
                                       style="background: rgba(51, 65, 85, 0.8); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.75rem; border-radius: 8px;"
                                       min="0" max="100" placeholder="80">
                            </div>
                        </div>
                        
                        <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <div class="form-group">
                                <label class="form-label" style="color: rgb(203, 213, 225); font-weight: 500; margin-bottom: 0.5rem;">Notification Frequency</label>
                                <select class="form-control" name="notification_frequency" 
                                        style="background: rgba(51, 65, 85, 0.8); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.75rem; border-radius: 8px;">
                                    <option value="immediate">🚨 Immediate - Send right away</option>
                                    <option value="hourly">⏰ Hourly - Every hour</option>
                                    <option value="daily" selected>📅 Daily - Once per day</option>
                                    <option value="weekly">📊 Weekly - Once per week</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label" style="color: rgb(203, 213, 225); font-weight: 500; margin-bottom: 0.5rem;">Alert Type</label>
                                <select class="form-control" name="alert_type" 
                                        style="background: rgba(51, 65, 85, 0.8); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.75rem; border-radius: 8px;">
                                    <option value="cost_threshold">💰 Cost Threshold Alert</option>
                                    <option value="performance">⚡ Performance Alert</option>
                                    <option value="optimization">🎯 Optimization Alert</option>
                                    <option value="cpu_monitoring">🖥️ CPU Monitoring Alert</option>
                                </select>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer" style="border-top: 1px solid rgba(255,255,255,0.1); padding: 1rem 1.25rem; display: flex; gap: 0.75rem; justify-content: flex-end;">
                    <button class="btn btn-secondary" onclick="closeModal('createAlertModal')" 
                            style="background: rgba(75, 85, 99, 0.8); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.5rem 1rem; border-radius: 6px;">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button class="btn btn-primary" onclick="createAlert()" 
                            style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); border: none; color: white; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 500;">
                        <i class="fas fa-plus"></i> Create Alert
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    document.getElementById('createAlertModal').classList.add('show');
    
    // Add dynamic form field handling
    const alertTypeSelect = document.querySelector('#createAlertModal select[name="alert_type"]');
    if (alertTypeSelect) {
        alertTypeSelect.addEventListener('change', updateCreateFormFields);
        updateCreateFormFields(); // Initialize with default values
    }
}

function updateCreateFormFields() {
    const modal = document.getElementById('createAlertModal');
    if (!modal) return;
    
    const alertType = modal.querySelector('select[name="alert_type"]').value;
    const nameInput = modal.querySelector('input[name="name"]');
    const thresholdAmountGroup = modal.querySelector('input[name="threshold_amount"]').closest('.form-group');
    const thresholdAmountLabel = thresholdAmountGroup.querySelector('.form-label');
    const thresholdAmountInput = modal.querySelector('input[name="threshold_amount"]');
    
    if (alertType === 'cpu_monitoring') {
        // Update labels and placeholders for CPU monitoring
        nameInput.placeholder = 'CPU Monitoring Alert - High Usage';
        thresholdAmountLabel.textContent = 'CPU Threshold (%) *';
        thresholdAmountInput.placeholder = '80';
        thresholdAmountInput.min = '0';
        thresholdAmountInput.max = '100';
        thresholdAmountInput.step = '1';
    } else {
        // Default to cost/budget alert
        nameInput.placeholder = 'Budget Alert - $1,400';
        thresholdAmountLabel.textContent = 'Threshold Amount ($) *';
        thresholdAmountInput.placeholder = '1400';
        thresholdAmountInput.min = '0';
        thresholdAmountInput.max = '';
        thresholdAmountInput.step = '0.01';
    }
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
                                    <option value="cpu_monitoring" ${alert.alert_type === 'cpu_monitoring' ? 'selected' : ''}>🖥️ CPU Monitoring Alert</option>
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
    
    return fetch(`/api/notifications/${notificationId}/mark-read`, {
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
            
            // Immediately update local state for instant feedback
            if (window.AlertsState.notifications) {
                const notification = window.AlertsState.notifications.find(n => n.id === notificationId);
                if (notification) {
                    notification.read = true;
                    window.AlertsState.unreadNotificationsCount = Math.max(0, (window.AlertsState.unreadNotificationsCount || 0) - 1);
                }
            }
            
            if (window.AlertsState.globalNotifications) {
                const globalNotification = window.AlertsState.globalNotifications.find(n => n.id === notificationId);
                if (globalNotification) {
                    globalNotification.read = true;
                    window.AlertsState.globalUnreadCount = Math.max(0, (window.AlertsState.globalUnreadCount || 0) - 1);
                }
            }
            
            // Update badges immediately
            updateNotificationBadge();
            updateGlobalNotificationBadge();
            
            // Reload notifications to get updated state from backend
            loadNotifications();
            loadGlobalNotifications();
            // Re-display notifications if we're on that tab
            if (window.AlertsState.notifications) {
                displayNotificationsInTab();
            }
            return result;
        } else {
            console.error('❌ Failed to mark notification as read:', result.message);
            showToast('error', 'Failed to mark notification as read');
            throw new Error(result.message || 'Failed to mark notification as read');
        }
    })
    .catch(error => {
        console.error('❌ Error marking notification as read:', error);
        showToast('error', `Error: ${error.message}`);
        throw error;
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
    console.log('📖 Marking all notifications as read via API (TAB function)');
    console.log('📊 Current state check:');
    console.log('  - notifications array length:', window.AlertsState.notifications?.length || 0);
    console.log('  - globalNotifications array length:', window.AlertsState.globalNotifications?.length || 0);
    console.log('  - unreadNotificationsCount:', window.AlertsState.unreadNotificationsCount || 0);
    console.log('  - globalUnreadCount:', window.AlertsState.globalUnreadCount || 0);
    
    // Check both notification arrays for unread notifications
    const unreadNotifications = window.AlertsState.notifications?.filter(n => !n.read) || [];
    const unreadGlobalNotifications = window.AlertsState.globalNotifications?.filter(n => !n.read) || [];
    
    console.log('  - unread in notifications array:', unreadNotifications.length);
    console.log('  - unread in globalNotifications array:', unreadGlobalNotifications.length);
    
    // Use the array with more unread notifications
    const notificationsToMark = unreadNotifications.length > 0 ? unreadNotifications : unreadGlobalNotifications;
    
    if (notificationsToMark.length === 0) {
        console.log('⚠️ No unread notifications found in either array');
        showToast('info', 'No unread notifications to mark');
        return;
    }
    
    console.log(`📖 Marking ${notificationsToMark.length} notifications as read individually`);
    
    // Mark each notification as read individually
    const markPromises = notificationsToMark.map(notification => 
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
                
                // Immediately update counts and mark all notifications as read locally
                window.AlertsState.unreadNotificationsCount = 0;
                window.AlertsState.globalUnreadCount = 0;
                
                // Mark all notifications in both arrays as read
                if (window.AlertsState.notifications) {
                    window.AlertsState.notifications.forEach(notification => {
                        notification.read = true;
                    });
                }
                if (window.AlertsState.globalNotifications) {
                    window.AlertsState.globalNotifications.forEach(notification => {
                        notification.read = true;
                    });
                }
                
                updateNotificationBadge();
                updateGlobalNotificationBadge();
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
    console.log('📖 Marking notification as read and updating global state:', notificationId);
    
    // Disable the button to prevent double-clicking
    const button = document.getElementById(`mark-read-${notificationId}`);
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Reading...';
        button.style.opacity = '0.6';
    }
    
    return markAsRead(notificationId)
        .then(() => {
            console.log('✅ Global notification update completed');
            // The markAsRead function already handles the reloading, no need for additional calls
            if (button) {
                button.innerHTML = '✓ Read';
                button.style.background = '#10b981';
                setTimeout(() => {
                    // The dropdown will refresh anyway, but this provides immediate feedback
                    if (button.parentElement) {
                        button.parentElement.style.display = 'none';
                    }
                }, 500);
            }
        })
        .catch(error => {
            console.error('❌ Error in global notification update:', error);
            // Re-enable the button on error
            if (button) {
                button.disabled = false;
                button.innerHTML = 'Mark Read';
                button.style.opacity = '1';
                button.style.background = '#171d34';
            }
        });
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
 * DEBUGGING FUNCTIONS FOR NOTIFICATION SYSTEM
 */
function debugNotificationSystem() {
    console.log('🔍 === NOTIFICATION SYSTEM DEBUG ===');
    
    // Check if bell icon exists
    const bellIcon = document.querySelector('#global-notification-badge');
    console.log('🔔 Bell icon found:', !!bellIcon, bellIcon);
    
    if (bellIcon) {
        console.log('🔔 Bell icon details:');
        console.log('- ID:', bellIcon.id);
        console.log('- Classes:', bellIcon.className);
        console.log('- Parent:', bellIcon.parentElement);
        console.log('- Click listeners:', 'Check in DevTools with getEventListeners(bellIcon)');
    }
    
    // Check notifications data
    console.log('📊 Notifications data:');
    console.log('- Global notifications:', window.AlertsState.globalNotifications?.length || 0);
    console.log('- Global unread count:', window.AlertsState.globalUnreadCount || 0);
    console.log('- Regular notifications:', window.AlertsState.notifications?.length || 0);
    console.log('- Regular unread count:', window.AlertsState.unreadNotificationsCount || 0);
    
    // Check API endpoints
    console.log('🌐 Testing API endpoints...');
    fetch('/api/notifications/in-app?unread_only=false&limit=100')
        .then(r => r.json())
        .then(data => {
            console.log('✅ Global notifications API response:', data);
            if (data.notifications) {
                console.log('📝 Sample notification:', data.notifications[0]);
            }
        })
        .catch(e => console.error('❌ Global notifications API error:', e));
    
    // Check current cluster notifications
    if (window.AlertsState.currentClusterId) {
        fetch(`/api/notifications/in-app?cluster_id=${window.AlertsState.currentClusterId}&limit=50`)
            .then(r => r.json())
            .then(data => console.log('✅ Cluster notifications API response:', data))
            .catch(e => console.error('❌ Cluster notifications API error:', e));
    }
    
    return {
        bellIconFound: !!bellIcon,
        globalNotifications: window.AlertsState.globalNotifications?.length || 0,
        unreadCount: window.AlertsState.globalUnreadCount || 0,
        clusterId: window.AlertsState.currentClusterId
    };
}

function testBellIconClick() {
    console.log('🧪 Testing bell icon click...');
    
    const bellIcon = document.querySelector('#global-notification-badge') || 
                    document.querySelector('.fa-regular.fa-bell') ||
                    document.querySelector('.fa-bell');
    
    if (bellIcon) {
        console.log('✅ Found bell icon, triggering click...');
        
        // Create a fake event
        const fakeEvent = {
            target: bellIcon,
            preventDefault: () => {},
            stopPropagation: () => {}
        };
        
        // Call the dropdown function directly
        showGlobalNotificationsDropdown(fakeEvent);
    } else {
        console.error('❌ Bell icon not found for testing');
    }
}

function forceReloadNotifications() {
    console.log('🔄 Force reloading all notifications...');
    
    // Load global notifications
    loadGlobalNotifications();
    
    // Load cluster-specific notifications
    loadNotifications();
    
    // Update badges
    setTimeout(() => {
        updateGlobalNotificationBadge();
        updateNotificationBadge();
        console.log('✅ Notifications reloaded');
    }, 1000);
}

function checkDropdownVisibility() {
    const dropdown = document.getElementById('global-notifications-dropdown');
    
    if (dropdown) {
        console.log('🔍 Dropdown exists but might be hidden:');
        console.log('- Display:', window.getComputedStyle(dropdown).display);
        console.log('- Visibility:', window.getComputedStyle(dropdown).visibility);
        console.log('- Opacity:', window.getComputedStyle(dropdown).opacity);
        console.log('- Z-index:', window.getComputedStyle(dropdown).zIndex);
        console.log('- Position:', window.getComputedStyle(dropdown).position);
        console.log('- Top:', window.getComputedStyle(dropdown).top);
        console.log('- Right:', window.getComputedStyle(dropdown).right);
        
        // Try to make it visible
        dropdown.style.cssText = `
            position: fixed !important;
            top: 100px !important;
            right: 100px !important;
            width: 350px !important;
            background: white !important;
            border: 2px solid red !important;
            z-index: 99999 !important;
            opacity: 1 !important;
            display: block !important;
            visibility: visible !important;
        `;
        
        console.log('🔧 Forced dropdown to be visible for testing');
    } else {
        console.log('❌ No dropdown found in DOM');
    }
}

function reinitializeBellIcon() {
    console.log('🔄 Completely reinitializing bell icon...');
    
    // Remove any existing event listeners
    const bellIcon = document.querySelector('#global-notification-badge');
    if (bellIcon) {
        const newBellIcon = bellIcon.cloneNode(true);
        bellIcon.parentNode.replaceChild(newBellIcon, bellIcon);
    }
    
    // Wait a moment then setup again
    setTimeout(() => {
        setupBellIconInteraction();
        loadGlobalNotifications();
        console.log('✅ Bell icon reinitialized');
    }, 500);
}

/**
 * ENHANCED INITIALIZATION WITH DEBUGGING
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
    
    // Wait a bit for DOM to be fully ready, then setup bell icon
    setTimeout(() => {
        setupBellIconInteraction();
        loadGlobalNotifications();
        console.log('🔔 Bell icon setup complete');
    }, 1000);
    
    // Load real data from your APIs
    loadAlerts();
    loadNotifications();
    
    // Initialize with alerts tab active
    setTimeout(() => {
        switchAlertsTab('alerts');
    }, 200);
    
    // Add debug helpers to window
    window.debugNotificationSystem = debugNotificationSystem;
    window.testBellIconClick = testBellIconClick;
    window.forceReloadNotifications = forceReloadNotifications;
    window.checkDropdownVisibility = checkDropdownVisibility;
    window.reinitializeBellIcon = reinitializeBellIcon;
    
    console.log('✅ Enhanced alerts system initialized with debugging helpers');
    console.log('💡 Available commands:');
    console.log('   - debugNotificationSystem() - Check notification system status');
    console.log('   - testBellIconClick() - Test bell icon click manually');
    console.log('   - refreshNotificationsManually() - Manually refresh notifications');
    console.log('   - forceReloadNotifications() - Force reload all notifications');
    console.log('   - checkDropdownVisibility() - Check if dropdown is hidden');
    console.log('   - reinitializeBellIcon() - Completely reinitialize bell icon');
    console.log('ℹ️  Notifications auto-refresh ONLY when analysis runs - no background polling!');
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
window.refreshNotificationsManually = refreshNotificationsManually;
window.updateNotificationBadge = updateNotificationBadge;
window.updateGlobalNotificationBadge = updateGlobalNotificationBadge;
window.setupBellIconInteraction = setupBellIconInteraction;
window.markAsReadAndUpdateGlobal = markAsReadAndUpdateGlobal;
window.navigateToAlertsTab = navigateToAlertsTab;
window.closeNotificationsDropdown = closeNotificationsDropdown;
window.setupDropdownEventListeners = setupDropdownEventListeners;
window.refreshNotificationsDropdown = refreshNotificationsDropdown;
window.handleNotificationClick = handleNotificationClick;
window.markAllGlobalAsRead = markAllGlobalAsRead;
window.showGlobalNotificationsDropdown = showGlobalNotificationsDropdown;
window.AlertsState = window.AlertsState;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEnhancedAlerts);
} else {
    initializeEnhancedAlerts();
}

console.log('✅ Complete fixed enhanced alerts system loaded with bell icon notifications');