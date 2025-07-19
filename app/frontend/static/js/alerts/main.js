// frontend/static/js/alerts/main.js

import { AlertsState, StateActions } from './core/state.js';
import { FREQUENCY_MAP, DEFAULTS } from './core/config.js';
import { checkSystemStatus, checkNotificationChannels, fetchFrequencyConfigurations, checkAlertsHealth } from './api/system.js';
import { fetchAlerts } from './api/alerts.js';
import { fetchInAppNotifications } from './api/notifications.js';
import { displayAlerts, displayInAppNotifications, updateNotificationBadge } from './ui/display.js';
import { setupEventListeners } from './ui/events.js';
import { createToast } from './utils/dom.js';
import { BootstrapHelper } from './utils/bootstrap.js';
import { escapeHtml, formatCurrency, getFrequencyInfo } from './utils/formatting.js';

/**
 * GLOBAL FUNCTIONS - DEFINED DIRECTLY HERE TO ENSURE AVAILABILITY
 */

/**
 * Show create alert modal - VANILLA JS VERSION (No Bootstrap required)
 */
window.showCreateAlertModal = function() {
    console.log('➕ Showing create alert modal');
    
    const modalHTML = `
        <div id="createAlertModal" class="custom-modal" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1055;
        ">
            <div class="custom-modal-dialog" style="
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                width: 90%;
                max-width: 600px;
                max-height: 90vh;
                overflow-y: auto;
            ">
                <div class="custom-modal-header" style="
                    background-color: #198754;
                    color: white;
                    padding: 1rem;
                    border-radius: 8px 8px 0 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <h5 style="margin: 0; font-size: 1.25rem;">
                        <i class="fas fa-plus" style="margin-right: 8px;"></i>Create New Alert
                    </h5>
                    <button type="button" onclick="closeCreateAlertModal()" style="
                        background: none;
                        border: none;
                        color: white;
                        font-size: 1.5rem;
                        cursor: pointer;
                        padding: 0;
                        width: 32px;
                        height: 32px;
                        border-radius: 4px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    " onmouseover="this.style.backgroundColor='rgba(255,255,255,0.1)'" 
                       onmouseout="this.style.backgroundColor='transparent'">
                        ×
                    </button>
                </div>
                <div class="custom-modal-body" style="padding: 1.5rem;">
                    <form id="create-alert-form">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                            <div>
                                <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Alert Name *</label>
                                <input type="text" name="name" required 
                                       placeholder="Monthly Budget Alert"
                                       style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Email Address *</label>
                                <input type="email" name="email" required 
                                       placeholder="admin@company.com"
                                       style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <div>
                                <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Threshold Amount ($)</label>
                                <input type="number" name="threshold_amount" 
                                       min="0" step="0.01" placeholder="5000"
                                       style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Threshold Percentage (%)</label>
                                <input type="number" name="threshold_percentage" 
                                       min="0" max="100" placeholder="80"
                                       style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
                            </div>
                        </div>
                    </form>
                </div>
                <div class="custom-modal-footer" style="
                    padding: 1rem 1.5rem;
                    border-top: 1px solid #dee2e6;
                    display: flex;
                    justify-content: flex-end;
                    gap: 0.5rem;
                ">
                    <button type="button" onclick="closeCreateAlertModal()" style="
                        padding: 0.5rem 1rem;
                        border: 1px solid #6c757d;
                        background: #6c757d;
                        color: white;
                        border-radius: 4px;
                        cursor: pointer;
                    ">Cancel</button>
                    <button type="button" onclick="handleCreateAlertSubmission()" style="
                        padding: 0.5rem 1rem;
                        border: 1px solid #198754;
                        background: #198754;
                        color: white;
                        border-radius: 4px;
                        cursor: pointer;
                    ">
                        <i class="fas fa-plus" style="margin-right: 4px;"></i>Create Alert
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal
    const existingModal = document.getElementById('createAlertModal');
    if (existingModal) existingModal.remove();
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Prevent body scrolling
    document.body.style.overflow = 'hidden';
    
    // Focus first input
    setTimeout(() => {
        const firstInput = document.querySelector('#create-alert-form input[name="name"]');
        if (firstInput) firstInput.focus();
    }, 100);
};

/**
 * Close create alert modal - VANILLA JS VERSION
 */
window.closeCreateAlertModal = function() {
    const modal = document.getElementById('createAlertModal');
    if (modal) {
        modal.remove();
    }
    
    // Restore body scrolling
    document.body.style.overflow = '';
    
    console.log('✅ Create alert modal closed');
};

/**
 * Handle create alert form submission
 */
window.handleCreateAlertSubmission = async function() {
    const form = document.getElementById('create-alert-form');
    if (!form) return;
    
    const formData = new FormData(form);
    const alertData = {
        name: formData.get('name'),
        alert_type: 'cost_threshold',
        threshold_amount: parseFloat(formData.get('threshold_amount')) || 0,
        threshold_percentage: parseFloat(formData.get('threshold_percentage')) || 0,
        email: formData.get('email'),
        notification_frequency: 'daily',
        cluster_id: AlertsState.currentClusterId,
        notification_channels: ['email', 'inapp']
    };
    
    // Basic validation
    if (!alertData.name || !alertData.email) {
        createToast('error', 'Error', 'Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch('/api/alerts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(alertData)
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            createToast('success', 'Success', 'Alert created successfully!');
            window.closeCreateAlertModal();
            await refreshAlertsData();
        } else {
            createToast('error', 'Error', 'Failed to create alert');
        }
    } catch (error) {
        createToast('error', 'Error', 'Failed to create alert: ' + error.message);
    }
};

/**
 * Filter alerts
 */
window.filterAlerts = function(filter) {
    console.log('🔍 Filtering alerts by:', filter);
    AlertsState.currentFilter = filter;
    
    // Update button states
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase().includes(filter) || 
            (filter === 'all' && btn.textContent.toLowerCase().includes('all'))) {
            btn.classList.add('active');
        }
    });
    
    // Filter alerts
    const alertRows = document.querySelectorAll('.alert-row');
    alertRows.forEach(row => {
        const status = row.dataset.status || 'active';
        let show = false;
        
        switch (filter) {
            case 'all': show = true; break;
            case 'active': show = status === 'active'; break;
            case 'paused': show = status === 'paused'; break;
        }
        
        row.style.display = show ? '' : 'none';
    });
};

/**
 * Switch alerts tab - FIXED to prevent conflicts
 */
window.switchAlertsTab = function(tabName) {
    console.log('📑 Switching to tab:', tabName);
    
    // Hide all tab contents first
    const allTabContents = document.querySelectorAll('.tab-content, .alerts-tab-content, .notifications-tab-content');
    allTabContents.forEach(content => {
        content.style.display = 'none';
        content.classList.add('hidden');
    });
    
    // Remove active class from all tab buttons
    const allTabButtons = document.querySelectorAll('.tab-button, .alerts-tab-button, .nav-link');
    allTabButtons.forEach(btn => {
        btn.classList.remove('active', 'border-blue-500', 'text-blue-600');
        btn.classList.add('border-transparent', 'text-gray-500');
    });
    
    // Show selected tab content
    if (tabName === 'alerts') {
        // Show alerts content
        const alertsContent = document.getElementById('alerts-tab-content') || 
                             document.querySelector('.alerts-content') ||
                             document.querySelector('[data-tab="alerts"]');
        if (alertsContent) {
            alertsContent.style.display = 'block';
            alertsContent.classList.remove('hidden');
        }
        
        // Activate alerts tab button
        const alertsTabBtn = document.getElementById('alerts-tab-btn') || 
                            document.querySelector('[onclick*="alerts"]') ||
                            document.querySelector('button[onclick*="switchAlertsTab(\'alerts\')"]') ||
                            document.querySelector('[data-tab="alerts"]');
        if (alertsTabBtn) {
            alertsTabBtn.classList.add('active', 'border-blue-500', 'text-blue-600');
            alertsTabBtn.classList.remove('border-transparent', 'text-gray-500');
        }
        
    } else if (tabName === 'notifications') {
        // Show notifications content
        const notificationsContent = document.getElementById('notifications-tab-content') || 
                                    document.querySelector('.notifications-content') ||
                                    document.querySelector('[data-tab="notifications"]');
        if (notificationsContent) {
            notificationsContent.style.display = 'block';
            notificationsContent.classList.remove('hidden');
        }
        
        // Activate notifications tab button
        const notificationsTabBtn = document.getElementById('notifications-tab-btn') || 
                                   document.querySelector('[onclick*="notifications"]') ||
                                   document.querySelector('button[onclick*="switchAlertsTab(\'notifications\')"]') ||
                                   document.querySelector('[data-tab="notifications"]');
        if (notificationsTabBtn) {
            notificationsTabBtn.classList.add('active', 'border-blue-500', 'text-blue-600');
            notificationsTabBtn.classList.remove('border-transparent', 'text-gray-500');
        }
    }
    
    console.log(`✅ Switched to ${tabName} tab`);
};

/**
 * Toggle simple alert menu - COMPLETELY FIXED
 */
window.toggleSimpleMenu = function(alertId) {
    console.log('🔧 Toggling menu for alert:', alertId);
    
    // Close all other menus first
    document.querySelectorAll('[id^="simple-menu-"]').forEach(menu => {
        if (menu.id !== `simple-menu-${alertId}`) {
            menu.style.display = 'none';
        }
    });
    
    // Toggle current menu
    const menu = document.getElementById(`simple-menu-${alertId}`);
    if (menu) {
        const isHidden = menu.style.display === 'none' || menu.style.display === '';
        
        if (isHidden) {
            // Position and show menu
            menu.style.display = 'block';
            menu.style.position = 'absolute';
            menu.style.top = '100%';
            menu.style.right = '0';
            menu.style.left = 'auto';
            menu.style.zIndex = '1050';
            menu.style.minWidth = '160px';
            menu.style.backgroundColor = '#fff';
            menu.style.border = '1px solid #dee2e6';
            menu.style.borderRadius = '0.375rem';
            menu.style.boxShadow = '0 0.5rem 1rem rgba(0, 0, 0, 0.15)';
            menu.style.padding = '0.5rem 0';
            console.log('✅ Menu opened for alert:', alertId);
        } else {
            menu.style.display = 'none';
            console.log('✅ Menu closed for alert:', alertId);
        }
    } else {
        console.error('❌ Menu not found for alert:', alertId);
    }
};

/**
 * Close specific menu
 */
window.closeMenu = function(alertId) {
    const menu = document.getElementById(`simple-menu-${alertId}`);
    if (menu) {
        menu.style.display = 'none';
    }
};

/**
 * Toggle alert menu (backward compatibility)
 */
window.toggleAlertMenu = function(alertId) {
    window.toggleSimpleMenu(alertId);
};

/**
 * Handle toggle alert
 */
window.handleToggleAlert = async function(alertId, isChecked) {
    console.log('🔄 Toggling alert:', alertId, isChecked);
    
    const action = isChecked ? 'resume' : 'pause';
    
    try {
        const response = await fetch(`/api/alerts/${alertId}/pause`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // Update UI
            const row = document.querySelector(`[data-alert-id="${alertId}"]`);
            if (row) {
                row.dataset.status = action === 'pause' ? 'paused' : 'active';
                const badge = row.querySelector('.badge');
                if (badge) {
                    badge.className = `badge bg-${isChecked ? 'success' : 'secondary'} px-2 py-1`;
                    badge.textContent = isChecked ? 'Active' : 'Paused';
                }
            }
        } else {
            // Revert toggle
            const toggle = document.getElementById(`toggle-${alertId}`);
            if (toggle) toggle.checked = !isChecked;
            createToast('error', 'Error', 'Failed to update alert');
        }
    } catch (error) {
        // Revert toggle
        const toggle = document.getElementById(`toggle-${alertId}`);
        if (toggle) toggle.checked = !isChecked;
        createToast('error', 'Error', 'Failed to update alert: ' + error.message);
    }
};

/**
 * Test alert
 */
window.testAlert = async function(alertId) {
    try {
        const response = await fetch(`/api/alerts/${alertId}/test`, { method: 'POST' });
        const result = await response.json();
        
        if (result.status === 'success') {
            createToast('success', 'Success', 'Test notification sent!');
        } else {
            createToast('error', 'Error', 'Failed to send test');
        }
    } catch (error) {
        createToast('error', 'Error', 'Failed to send test: ' + error.message);
    }
};

/**
 * Show delete alert modal
 */
window.showDeleteAlertModal = function(alertId, alertName) {
    if (confirm(`Are you sure you want to delete "${alertName}"?`)) {
        window.deleteAlert(alertId);
    }
};

/**
 * Delete alert
 */
window.deleteAlert = async function(alertId) {
    try {
        const response = await fetch(`/api/alerts/${alertId}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.status === 'success') {
            createToast('success', 'Success', 'Alert deleted successfully');
            await refreshAlertsData();
        } else {
            createToast('error', 'Error', 'Failed to delete alert');
        }
    } catch (error) {
        createToast('error', 'Error', 'Failed to delete alert: ' + error.message);
    }
};

/**
 * Main alerts system initialization
 */
export async function initializeAlertsSystem() {
    console.log('🔔 Initializing alerts system...');
    
    try {
        // Check system status
        const statusData = await checkSystemStatus();
        if (statusData.status === 'success') {
            StateActions.setSystemAvailable(statusData.alerts_available);
            
            if (statusData.alerts_available) {
                // Load data
                await Promise.all([
                    loadAlerts(),
                    loadInAppNotifications()
                ]);
                
                // Setup UI
                setupEventListeners();
                setupPeriodicRefresh();
                detectClusterContext();
            } else {
                showAlertsUnavailableMessage();
            }
        }
        
        console.log('✅ Alerts system initialized');
    } catch (error) {
        console.error('❌ Failed to initialize alerts system:', error);
        showAlertsUnavailableMessage();
    }
}

/**
 * Load alerts - FIXED to ensure all alerts are loaded and displayed
 */
async function loadAlerts() {
    try {
        console.log('🔄 Loading alerts...');
        const data = await fetchAlerts(AlertsState.currentClusterId);
        
        if (data.status === 'success' && data.alerts) {
            console.log(`📋 Received ${data.alerts.length} alerts from API`);
            
            // Ensure all alerts have proper status
            const processedAlerts = data.alerts.map(alert => ({
                ...alert,
                status: alert.status || 'active' // Default to active if no status
            }));
            
            StateActions.setAlerts(processedAlerts);
            
            // Reset filter to 'all' to ensure all alerts are visible
            AlertsState.currentFilter = 'all';
            
            displayAlerts();
            console.log(`✅ Successfully loaded and displayed ${processedAlerts.length} alerts`);
            
            // Log alert statuses for debugging
            const statusCounts = processedAlerts.reduce((acc, alert) => {
                const status = alert.status || 'active';
                acc[status] = (acc[status] || 0) + 1;
                return acc;
            }, {});
            console.log('📊 Alert status breakdown:', statusCounts);
            
        } else {
            console.warn('⚠️ No alerts data received or invalid response');
            StateActions.setAlerts([]);
            displayAlerts();
        }
    } catch (error) {
        console.error('❌ Error loading alerts:', error);
        createToast('error', 'Error', 'Failed to load alerts');
        // Still try to display with empty array
        StateActions.setAlerts([]);
        displayAlerts();
    }
}

/**
 * Load in-app notifications
 */
async function loadInAppNotifications() {
    try {
        const data = await fetchInAppNotifications(AlertsState.currentClusterId);
        
        if (data.status === 'success') {
            StateActions.setInAppNotifications(data.notifications || []);
            StateActions.setUnreadCount(data.unread_count || 0);
            displayInAppNotifications();
            updateNotificationBadge();
        }
    } catch (error) {
        console.log('ℹ️ In-app notifications not available');
        StateActions.setInAppNotifications([]);
        StateActions.setUnreadCount(0);
    }
}

/**
 * Refresh alerts data - FIXED to preserve filter state
 */
async function refreshAlertsData() {
    console.log('🔄 Refreshing alerts data...');
    
    // Save current filter before refresh
    const currentFilter = AlertsState.currentFilter || 'all';
    
    await Promise.all([
        loadAlerts(),
        loadInAppNotifications()
    ]);
    
    // Restore filter after refresh
    setTimeout(() => {
        if (currentFilter && currentFilter !== 'all') {
            filterAlerts(currentFilter);
        }
    }, 100);
    
    console.log('✅ Alerts data refreshed');
}

/**
 * Setup periodic refresh
 */
function setupPeriodicRefresh() {
    setInterval(refreshAlertsData, 30000);
}

/**
 * Detect cluster context
 */
function detectClusterContext() {
    const urlPath = window.location.pathname;
    const clusterMatch = urlPath.match(/\/cluster\/([^\/]+)/);
    
    if (clusterMatch) {
        StateActions.setCurrentCluster(clusterMatch[1]);
        console.log(`🎯 Detected cluster: ${AlertsState.currentClusterId}`);
    }
}

/**
 * Show unavailable message
 */
function showAlertsUnavailableMessage() {
    const container = document.getElementById('alerts-list-container');
    if (container) {
        container.innerHTML = `
            <div class="alert alert-warning">
                <h6><i class="fas fa-exclamation-triangle me-2"></i>Alerts System Unavailable</h6>
                <p>The alerts system is not currently available. Please contact your administrator.</p>
            </div>
        `;
    }
}

// Add essential CSS for modals and dropdowns
const style = document.createElement('style');
style.textContent = `
/* Custom modal styles */
.custom-modal {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.custom-modal input:focus {
    outline: none;
    border-color: #198754;
    box-shadow: 0 0 0 2px rgba(25, 135, 84, 0.2);
}

.custom-modal button:hover {
    opacity: 0.9;
}

/* Ensure dropdowns appear above everything */
.dropdown-menu {
    z-index: 1050 !important;
    border: 1px solid #dee2e6;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    border-radius: 0.375rem;
}

/* Form switches styling */
.form-check-input {
    width: 2.5rem;
    height: 1.25rem;
}

/* Clean table styling */
.table-hover tbody tr:hover {
    background-color: rgba(0, 0, 0, 0.025);
}

/* Button styling */
.btn-light:hover {
    background-color: #e9ecef;
    border-color: #adb5bd;
}

/* Tab fixing styles */
.tab-content, .alerts-tab-content, .notifications-tab-content {
    transition: all 0.2s ease;
}

.tab-content.hidden, .alerts-tab-content.hidden, .notifications-tab-content.hidden {
    display: none !important;
}
`;
document.head.appendChild(style);

// Global error handler to catch any issues
window.addEventListener('error', function(event) {
    console.log('🚨 Global error:', event.error);
});

// Global exports
window.initializeAlertsSystem = initializeAlertsSystem;
window.refreshAlertsData = refreshAlertsData;
window.AlertsState = AlertsState;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAlertsSystem);
} else {
    initializeAlertsSystem();
}

console.log('✅ Alerts main module loaded with vanilla JS modal and fixed tabs');