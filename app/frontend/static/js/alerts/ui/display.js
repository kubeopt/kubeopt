// frontend/static/js/alerts/ui/display.js

import { AlertsState } from '../core/state.js';
import { formatDateTime, formatCurrency, getFrequencyInfo, getStatusBadgeClass, escapeHtml } from '../utils/formatting.js';

/**
 * FIXED: Display alerts function with proper dropdown functionality
 */
export function displayAlerts() {
    const container = document.getElementById('alerts-list-container');
    if (!container) {
        console.warn('❌ alerts-list-container not found');
        return;
    }
    
    const alerts = AlertsState.alerts;
    console.log(`📋 Displaying ${alerts.length} alerts from state`);
    
    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-bell-slash fa-2x mb-3"></i>
                <h6>No alerts configured yet</h6>
                <p>Create your first alert using the button above</p>
                <button class="btn btn-primary" onclick="showCreateAlertModal()">
                    <i class="fas fa-plus me-2"></i>Create Alert
                </button>
            </div>
        `;
        
        // Update filter counts for empty state
        updateAlertCounts();
        return;
    }
    
    // Update summary counters
    updateAlertSummaryCounters(alerts);
    
    // Enhanced alerts HTML with FIXED dropdown functionality
    const alertsHTML = `
        <div class="alerts-table-container">
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th style="width: 100px;">Status</th>
                            <th>Alert Details</th>
                            <th style="width: 120px;">Budget</th>
                            <th style="width: 200px;">Contact</th>
                            <th style="width: 150px;">Frequency</th>
                            <th style="width: 80px;">Enable</th>
                            <th style="width: 60px;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${alerts.map(alert => {
                            const isActive = (alert.status || 'active') === 'active';
                            const statusColor = isActive ? 'success' : 'secondary';
                            const frequency = alert.notification_frequency || 'daily';
                            const frequencyInfo = getFrequencyInfo(frequency);
                            const healthScore = calculateAlertHealthScore(alert);
                            
                            return `
                                <tr class="alert-row" 
                                    data-alert-id="${alert.id}" 
                                    data-status="${alert.status || 'active'}">
                                    <td>
                                        <div class="d-flex flex-column align-items-center">
                                            <span class="badge bg-${statusColor} px-2 py-1 mb-1">
                                                ${isActive ? 'Active' : 'Paused'}
                                            </span>
                                            ${healthScore < 80 ? `
                                                <small class="text-warning" title="Alert health: ${healthScore}%">
                                                    <i class="fas fa-exclamation-triangle"></i> ${healthScore}%
                                                </small>
                                            ` : ''}
                                        </div>
                                    </td>
                                    <td>
                                        <div>
                                            <strong class="text-dark">${escapeHtml(alert.name)}</strong>
                                            <br><small class="text-muted">
                                                Type: ${alert.alert_type || 'cost_threshold'}
                                            </small>
                                            ${alert.threshold_percentage ? `
                                                <br><small class="text-info">
                                                    ${alert.threshold_percentage}% threshold
                                                </small>
                                            ` : ''}
                                            ${alert.last_triggered ? `
                                                <br><small class="text-success">
                                                    <i class="fas fa-history"></i> Last: ${formatDateTime(alert.last_triggered)}
                                                </small>
                                            ` : ''}
                                        </div>
                                    </td>
                                    <td>
                                        <span class="fw-bold text-primary">
                                            ${alert.threshold_amount > 0 ? formatCurrency(alert.threshold_amount) : 'N/A'}
                                        </span>
                                        ${alert.current_cost ? `
                                            <br><small class="text-muted">
                                                Current: ${formatCurrency(alert.current_cost)}
                                            </small>
                                        ` : ''}
                                    </td>
                                    <td>
                                        <div>
                                            <small class="text-muted">
                                                <i class="fas fa-envelope me-1"></i>
                                                ${alert.email ? escapeHtml(alert.email) : 'Not set'}
                                            </small>
                                            <br><small class="text-info">
                                                ${getNotificationChannelsDisplay(alert)}
                                            </small>
                                        </div>
                                    </td>
                                    <td>
                                        <div class="text-center">
                                            <span class="badge bg-${frequencyInfo.color} bg-opacity-10 text-${frequencyInfo.color} px-2 py-1">
                                                <i class="fas ${frequencyInfo.icon} me-1"></i>
                                                ${frequencyInfo.display}
                                            </span>
                                            ${alert.frequency_at_time ? `
                                                <br><small class="text-muted">at ${alert.frequency_at_time}</small>
                                            ` : ''}
                                            ${alert.max_notifications_per_day ? `
                                                <br><small class="text-muted">max ${alert.max_notifications_per_day}/day</small>
                                            ` : ''}
                                        </div>
                                    </td>
                                    <td>
                                        <div class="form-check form-switch d-flex justify-content-center">
                                            <input class="form-check-input" type="checkbox" 
                                                   ${isActive ? 'checked' : ''} 
                                                   onchange="handleToggleAlert('${alert.id}', this.checked)"
                                                   id="toggle-${alert.id}">
                                        </div>
                                    </td>
                                    <td>
                                        <div class="dropdown position-relative">
                                            <button class="btn btn-light btn-sm border-0" 
                                                    type="button" 
                                                    onclick="toggleSimpleMenu('${alert.id}')"
                                                    title="More actions"
                                                    id="dropdown-${alert.id}">
                                                <i class="fas fa-ellipsis-v"></i>
                                            </button>
                                            
                                            <!-- FIXED: Proper dropdown menu structure -->
                                            <div class="dropdown-menu dropdown-menu-end" 
                                                 id="simple-menu-${alert.id}" 
                                                 style="display: none;">
                                                <button class="dropdown-item" onclick="event.preventDefault(); testAlert('${alert.id}'); closeMenu('${alert.id}');">
                                                    <i class="fas fa-paper-plane me-2 text-primary"></i>Test Alert
                                                </button>
                                                <button class="dropdown-item" onclick="event.preventDefault(); showEditAlertModal('${alert.id}'); closeMenu('${alert.id}');">
                                                    <i class="fas fa-edit me-2 text-info"></i>Edit Alert
                                                </button>
                                                <button class="dropdown-item" onclick="event.preventDefault(); showEditFrequencyModal('${alert.id}'); closeMenu('${alert.id}');">
                                                    <i class="fas fa-clock me-2 text-warning"></i>Edit Frequency
                                                </button>
                                                <div class="dropdown-divider"></div>
                                                <button class="dropdown-item text-danger" onclick="event.preventDefault(); showDeleteAlertModal('${alert.id}', '${escapeHtml(alert.name)}'); closeMenu('${alert.id}');">
                                                    <i class="fas fa-trash me-2"></i>Delete
                                                </button>
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = alertsHTML;
    
    // CRITICAL: Update counts after display
    updateAlertCounts();
    
    // Setup filter buttons if they don't exist
    setupFilterButtons();
    
    console.log(`✅ Successfully displayed ${alerts.length} enhanced alerts`);
}

/**
 * FIXED: Calculate alert health score
 */
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

/**
 * Enhanced notification channels display
 */
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
        return `${icon} ${name}`;
    }).join(' ');
    
    return activeChannels || '<i class="fas fa-envelope text-primary"></i> Email';
}

/**
 * FIXED: Update alert summary counters
 */
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

/**
 * FIXED: Setup filter buttons if they don't exist
 */
function setupFilterButtons() {
    const alertsContainer = document.getElementById('alerts-list-container');
    if (alertsContainer && !document.getElementById('alerts-filter-buttons')) {
        const filterButtonsHtml = `
            <div id="alerts-filter-buttons" class="mb-3">
                <div class="btn-group" role="group" aria-label="Alert filters">
                    <button type="button" class="btn btn-outline-primary active filter-btn" 
                            onclick="filterAlerts('all')" style="transition: all 0.3s ease;">
                        <i class="fas fa-list me-1"></i>All (<span id="all-count">0</span>)
                    </button>
                    <button type="button" class="btn btn-outline-success filter-btn" 
                            onclick="filterAlerts('active')" style="transition: all 0.3s ease;">
                        <i class="fas fa-play me-1"></i>Active (<span id="active-count">0</span>)
                    </button>
                    <button type="button" class="btn btn-outline-warning filter-btn" 
                            onclick="filterAlerts('paused')" style="transition: all 0.3s ease;">
                        <i class="fas fa-pause me-1"></i>Paused (<span id="paused-count">0</span>)
                    </button>
                </div>
            </div>
        `;
        
        alertsContainer.insertAdjacentHTML('beforebegin', filterButtonsHtml);
    }
    
    // Initial count update
    updateAlertCounts();
}

/**
 * FIXED: Update alert counts in filter buttons
 */
function updateAlertCounts() {
    const alerts = AlertsState.alerts;
    const allCount = alerts.length;
    const activeCount = alerts.filter(a => (a.status || 'active') === 'active').length;
    const pausedCount = alerts.filter(a => a.status === 'paused').length;
    
    const elements = {
        'all-count': allCount,
        'active-count': activeCount,
        'paused-count': pausedCount,
        'total-alerts-count': allCount
    };
    
    Object.entries(elements).forEach(([id, count]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = count;
        }
    });
    
    console.log('📊 Alert counts updated:', { allCount, activeCount, pausedCount });
}

/**
 * Display in-app notifications - SIMPLIFIED
 */
export function displayInAppNotifications() {
    const container = document.getElementById('in-app-notifications-container');
    if (!container) return;
    
    const notifications = AlertsState.inAppNotifications;
    
    if (notifications.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-bell-slash fa-2x mb-2"></i>
                <p class="mb-0">No notifications yet</p>
            </div>
        `;
        return;
    }
    
    const notificationsHTML = `
        <div class="notifications-list">
            ${notifications.map(notification => `
                <div class="notification-item ${notification.read ? 'read' : 'unread'} p-3 border-bottom" 
                     data-notification-id="${notification.id}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="notification-content flex-grow-1">
                            <div class="d-flex align-items-center mb-1">
                                <strong class="me-2">${escapeHtml(notification.title)}</strong>
                                ${!notification.read ? '<span class="badge bg-primary">New</span>' : ''}
                            </div>
                            <div class="text-muted small mb-1">
                                ${escapeHtml(notification.message)}
                            </div>
                            <div class="text-muted small">
                                <i class="fas fa-clock me-1"></i>
                                ${formatDateTime(notification.timestamp)}
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
            `).join('')}
        </div>
    `;
    
    container.innerHTML = notificationsHTML;
}

/**
 * Update notification badge
 */
export function updateNotificationBadge() {
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

// Export the new functions for global access
window.calculateAlertHealthScore = calculateAlertHealthScore;
window.getNotificationChannelsDisplay = getNotificationChannelsDisplay;
window.updateAlertSummaryCounters = updateAlertSummaryCounters;
window.updateAlertCounts = updateAlertCounts;
window.setupFilterButtons = setupFilterButtons;