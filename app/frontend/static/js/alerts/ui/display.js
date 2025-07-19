// frontend/static/js/alerts/ui/display.js

import { AlertsState } from '../core/state.js';
import { formatDateTime, formatCurrency, getFrequencyInfo, getStatusBadgeClass, escapeHtml } from '../utils/formatting.js';

/**
 * Display functions for alerts and notifications
 */

/**
 * Display alerts in clean, simple table format - COMPLETELY FIXED
 */
export function displayAlerts() {
    const container = document.getElementById('alerts-list-container');
    if (!container) return;
    
    const alerts = AlertsState.alerts;
    console.log('📋 Displaying alerts:', alerts.length, 'alerts');
    
    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-bell-slash fa-2x mb-3"></i>
                <h6>No alerts configured yet</h6>
                <p>Create your first alert using the button above</p>
            </div>
        `;
        return;
    }
    
    // Create clean, modern table layout with WORKING dropdowns
    const alertsHTML = `
        <div class="alerts-table-container">
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th style="width: 100px;">Status</th>
                            <th>Alert Name</th>
                            <th style="width: 120px;">Budget</th>
                            <th style="width: 200px;">Email</th>
                            <th style="width: 150px;">Cluster</th>
                            <th style="width: 80px;">Enable</th>
                            <th style="width: 60px;"></th>
                        </tr>
                    </thead>
                    <tbody>
                        ${alerts.map(alert => {
                            const isActive = (alert.status || 'active') === 'active';
                            const statusColor = isActive ? 'success' : 'secondary';
                            
                            return `
                                <tr class="alert-row" 
                                    data-alert-id="${alert.id}" 
                                    data-status="${alert.status || 'active'}">
                                    <td>
                                        <span class="badge bg-${statusColor} px-2 py-1">
                                            ${isActive ? 'Active' : 'Paused'}
                                        </span>
                                    </td>
                                    <td>
                                        <div>
                                            <strong class="text-dark">${escapeHtml(alert.name)}</strong>
                                            ${alert.notification_frequency ? `
                                                <br><small class="text-muted">
                                                    ${getFrequencyInfo(alert.notification_frequency).display}
                                                </small>
                                            ` : ''}
                                        </div>
                                    </td>
                                    <td>
                                        <span class="fw-bold text-primary">
                                            ${alert.threshold_amount > 0 ? formatCurrency(alert.threshold_amount) : 'N/A'}
                                        </span>
                                    </td>
                                    <td>
                                        <small class="text-muted">
                                            ${alert.email ? escapeHtml(alert.email) : 'Not set'}
                                        </small>
                                    </td>
                                    <td>
                                        <small class="text-muted">
                                            ${alert.cluster_name ? escapeHtml(alert.cluster_name) : 'All clusters'}
                                        </small>
                                    </td>
                                    <td>
                                        <div class="form-check form-switch">
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
                                            <div class="dropdown-menu dropdown-menu-end" 
                                                 id="simple-menu-${alert.id}" 
                                                 style="display: none;">
                                                <a class="dropdown-item" href="#" onclick="event.preventDefault(); testAlert('${alert.id}'); closeMenu('${alert.id}');">
                                                    <i class="fas fa-paper-plane me-2 text-primary"></i>Test Alert
                                                </a>
                                                <a class="dropdown-item" href="#" onclick="event.preventDefault(); showEditAlertModal('${alert.id}'); closeMenu('${alert.id}');">
                                                    <i class="fas fa-edit me-2 text-info"></i>Edit Alert
                                                </a>
                                                <div class="dropdown-divider"></div>
                                                <a class="dropdown-item text-danger" href="#" onclick="event.preventDefault(); showDeleteAlertModal('${alert.id}', '${escapeHtml(alert.name)}'); closeMenu('${alert.id}');">
                                                    <i class="fas fa-trash me-2"></i>Delete
                                                </a>
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
        
        <style>
        .alerts-table-container {
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .table {
            margin: 0;
        }
        
        .table th {
            border-top: none;
            font-weight: 600;
            color: #374151;
            background-color: #f8fafc !important;
        }
        
        .table td {
            border-color: #e5e7eb;
            vertical-align: middle;
        }
        
        .alert-row:hover {
            background-color: #f8fafc;
        }
        
        .dropdown-menu {
            border: 1px solid #e5e7eb;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border-radius: 6px;
            padding: 4px 0;
            min-width: 160px;
            z-index: 1050;
        }
        
        .dropdown-item {
            padding: 8px 16px;
            font-size: 14px;
            transition: all 0.15s ease;
        }
        
        .dropdown-item:hover {
            background-color: #f3f4f6;
            color: #1f2937;
        }
        
        .dropdown-item:active {
            background-color: #e5e7eb;
        }
        
        .form-check-input {
            width: 2.5rem;
            height: 1.25rem;
        }
        
        .badge {
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .btn-light {
            background-color: #f8fafc;
            border-color: #e5e7eb;
        }
        
        .btn-light:hover {
            background-color: #f1f5f9;
            border-color: #d1d5db;
        }
        </style>
    `;
    
    container.innerHTML = alertsHTML;
    updateAlertCounts();
    
    // Setup click outside handler for dropdowns
    setupDropdownHandlers();
    
    // Apply current filter if set
    setTimeout(() => {
        if (AlertsState.currentFilter && AlertsState.currentFilter !== 'all') {
            // Import filterAlerts function to apply filter
            import('./interactions.js').then(module => {
                module.filterAlerts(AlertsState.currentFilter);
            });
        }
    }, 50);
    
    console.log('✅ Alerts displayed successfully');
}

/**
 * Setup dropdown click handlers
 */
function setupDropdownHandlers() {
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.dropdown') && !event.target.closest('[id^="simple-menu-"]')) {
            document.querySelectorAll('[id^="simple-menu-"]').forEach(menu => {
                menu.style.display = 'none';
            });
        }
    });
}

/**
 * Display in-app notifications - CLEANED UP
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

/**
 * Update alert counts in filter buttons
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