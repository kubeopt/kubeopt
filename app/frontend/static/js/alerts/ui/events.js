// frontend/static/js/alerts/ui/events.js

import { AlertsState, StateActions } from '../core/state.js';
import { createAlert, updateAlert, deleteAlert as deleteAlertAPI, testAlert as testAlertAPI, pauseResumeAlert as pauseResumeAlertAPI } from '../api/alerts.js';
import { markNotificationAsRead as markNotificationAsReadAPI, dismissNotification as dismissNotificationAPI } from '../api/notifications.js';
import { displayAlerts, displayInAppNotifications, updateNotificationBadge } from './display.js';
import { validateAlertForm } from '../utils/validation.js';
import { getSelectedCheckboxes, getFormData, setButtonLoading } from '../utils/dom.js';
import { createToast } from '../utils/dom.js';
import { closeCreateAlertModal, closeEditAlertModal, closeDeleteAlertModal } from './modals.js';

/**
 * Event handling for alerts system
 */

/**
 * Setup all event listeners
 */
export function setupEventListeners() {
    // Form submissions
    setupFormListeners();
    
    // Global click handlers
    setupGlobalClickHandlers();
    
    // Close menus when clicking outside
    setupOutsideClickHandlers();
}

/**
 * Setup form submission listeners
 */
function setupFormListeners() {
    // Budget alert form
    const budgetForm = document.getElementById('budget-alert-form');
    if (budgetForm) {
        budgetForm.addEventListener('submit', handleBudgetAlertSubmission);
    }
    
    // Advanced alerts form  
    const advancedForm = document.getElementById('advanced-alerts-form');
    if (advancedForm) {
        advancedForm.addEventListener('submit', handleAdvancedAlertSubmission);
    }
}

/**
 * Setup global click handlers
 */
function setupGlobalClickHandlers() {
    document.addEventListener('click', function(event) {
        if (!AlertsState.systemAvailable) {
            if (event.target.closest('.test-alert-btn, .pause-alert-btn, .delete-alert-btn, .edit-frequency-btn')) {
                createToast('warning', 'Unavailable', 'Alerts system is currently unavailable');
                event.preventDefault();
                return;
            }
        }
        
        // Test alert
        if (event.target.closest('.test-alert-btn, [onclick*="testAlert"]')) {
            event.preventDefault();
            const alertId = event.target.closest('[data-alert-id]')?.dataset.alertId;
            if (alertId) handleTestAlert(alertId);
        }
        
        // Pause/Resume alert
        if (event.target.closest('.pause-alert-btn, [onclick*="pauseResumeAlert"]')) {
            event.preventDefault();
            const button = event.target.closest('.pause-alert-btn, [onclick*="pauseResumeAlert"]');
            const alertId = button?.dataset.alertId || button?.closest('[data-alert-id]')?.dataset.alertId;
            const action = button?.dataset.action;
            if (alertId && action) handlePauseResumeAlert(alertId, action);
        }
        
        // Delete alert
        if (event.target.closest('.delete-alert-btn, [onclick*="deleteAlert"], [onclick*="showDeleteAlertModal"]')) {
            event.preventDefault();
            const alertId = event.target.closest('[data-alert-id]')?.dataset.alertId;
            if (alertId) window.showDeleteAlertModal(alertId);
        }
        
        // Mark notification as read
        if (event.target.closest('[onclick*="markNotificationAsRead"]')) {
            event.preventDefault();
            const notificationId = event.target.closest('[data-notification-id]')?.dataset.notificationId;
            if (notificationId) handleMarkNotificationAsRead(notificationId);
        }
        
        // Dismiss notification
        if (event.target.closest('[onclick*="dismissNotification"]')) {
            event.preventDefault();
            const notificationId = event.target.closest('[data-notification-id]')?.dataset.notificationId;
            if (notificationId) handleDismissNotification(notificationId);
        }
    });
}

/**
 * Setup outside click handlers
 */
function setupOutsideClickHandlers() {
    document.addEventListener('click', function(event) {
        // Close alert menus when clicking outside
        if (!event.target.closest('[id^="menu-"]') && !event.target.closest('button[onclick*="toggleAlertMenu"]')) {
            document.querySelectorAll('[id^="menu-"]').forEach(menu => {
                menu.classList.add('hidden');
            });
        }
    });
}

/**
 * Handle budget alert form submission
 */
async function handleBudgetAlertSubmission(event) {
    event.preventDefault();
    
    if (!AlertsState.systemAvailable) {
        createToast('error', 'Error', 'Alerts system is currently unavailable');
        return;
    }
    
    const form = event.target;
    const formData = getFormData(form);
    
    // Get selected channels
    const selectedChannels = getSelectedCheckboxes(form, 'channels');
    
    const alertData = {
        name: formData.name || `Budget Alert - ${formData.threshold_amount}`,
        alert_type: 'cost_threshold',
        threshold_amount: parseFloat(formData.threshold_amount) || 0,
        threshold_percentage: parseFloat(formData.threshold_percentage) || 0,
        email: formData.email,
        notification_frequency: formData.notification_frequency || 'daily',
        cluster_id: AlertsState.currentClusterId,
        notification_channels: selectedChannels
    };
    
    // Validate
    const errors = validateAlertForm(alertData);
    if (errors.length > 0) {
        createToast('error', 'Validation Error', errors[0]);
        return;
    }
    
    const submitBtn = form.querySelector('button[type="submit"]');
    setButtonLoading(submitBtn, true, 'Creating alert...');
    
    try {
        const result = await createAlert(alertData);
        
        if (result.status === 'success') {
            createToast('success', 'Success', 'Budget alert created successfully!');
            form.reset();
            await refreshAlerts();
        } else {
            throw new Error(result.message || 'Failed to create alert');
        }
    } catch (error) {
        console.error('❌ Error creating budget alert:', error);
        createToast('error', 'Error', `Failed to create alert: ${error.message}`);
    } finally {
        setButtonLoading(submitBtn, false);
    }
}

/**
 * Handle create alert modal submission
 */
window.handleCreateAlertSubmission = async function() {
    const form = document.getElementById('create-alert-form');
    if (!form) return;
    
    const formData = getFormData(form);
    const selectedChannels = getSelectedCheckboxes(form, 'channels');
    
    const alertData = {
        name: formData.name,
        alert_type: formData.alert_type || 'cost_threshold',
        threshold_amount: parseFloat(formData.threshold_amount) || 0,
        threshold_percentage: parseFloat(formData.threshold_percentage) || 0,
        email: formData.email,
        notification_frequency: formData.notification_frequency || 'daily',
        cluster_id: AlertsState.currentClusterId,
        notification_channels: selectedChannels
    };
    
    // Validate
    const errors = validateAlertForm(alertData);
    if (errors.length > 0) {
        createToast('error', 'Validation Error', errors[0]);
        return;
    }
    
    const createBtn = document.querySelector('#createAlertModal .btn-success');
    setButtonLoading(createBtn, true, 'Creating...');
    
    try {
        const result = await createAlert(alertData);
        
        if (result.status === 'success') {
            createToast('success', 'Success', 'Alert created successfully!');
            closeCreateAlertModal();
            await refreshAlerts();
        } else {
            throw new Error(result.message || 'Failed to create alert');
        }
    } catch (error) {
        console.error('❌ Error creating alert:', error);
        createToast('error', 'Error', `Failed to create alert: ${error.message}`);
    } finally {
        setButtonLoading(createBtn, false);
    }
};

/**
 * Handle edit alert submission
 */
window.saveEditAlert = async function(alertId) {
    const form = document.getElementById('edit-alert-form');
    if (!form) return;
    
    const formData = getFormData(form);
    
    const updateData = {
        name: formData.name,
        email: formData.email,
        threshold_amount: parseFloat(formData.threshold_amount) || 0,
        threshold_percentage: parseFloat(formData.threshold_percentage) || 0
    };
    
    const saveBtn = document.querySelector('#editAlertModal .btn-primary');
    setButtonLoading(saveBtn, true, 'Saving...');
    
    try {
        const result = await updateAlert(alertId, updateData);
        
        if (result.status === 'success') {
            createToast('success', 'Success', 'Alert updated successfully!');
            closeEditAlertModal();
            await refreshAlerts();
        } else {
            throw new Error(result.message || 'Failed to update alert');
        }
    } catch (error) {
        console.error('❌ Error updating alert:', error);
        createToast('error', 'Error', `Failed to update alert: ${error.message}`);
    } finally {
        setButtonLoading(saveBtn, false);
    }
};

/**
 * Handle delete alert confirmation
 */
window.confirmDeleteAlert = async function(alertId) {
    closeDeleteAlertModal();
    
    try {
        const result = await deleteAlertAPI(alertId);
        
        if (result.status === 'success') {
            StateActions.removeAlert(alertId);
            displayAlerts();
            createToast('success', 'Success', 'Alert deleted successfully');
        } else {
            throw new Error(result.message || 'Failed to delete alert');
        }
    } catch (error) {
        console.error('❌ Error deleting alert:', error);
        createToast('error', 'Error', `Failed to delete alert: ${error.message}`);
    }
};

/**
 * Handle test alert
 */
async function handleTestAlert(alertId) {
    try {
        const result = await testAlertAPI(alertId);
        
        if (result.status === 'success') {
            const channels = result.channels_tested || [];
            const channelsText = channels.length > 0 ? channels.join(', ') : 'default channels';
            createToast('success', 'Test Sent', `Test notification sent via: ${channelsText}`);
        } else {
            throw new Error(result.message || 'Failed to send test');
        }
    } catch (error) {
        console.error('❌ Error testing alert:', error);
        createToast('error', 'Error', `Failed to send test: ${error.message}`);
    }
}

/**
 * Handle pause/resume alert
 */
async function handlePauseResumeAlert(alertId, action) {
    try {
        const result = await pauseResumeAlertAPI(alertId, action);
        
        if (result.status === 'success') {
            StateActions.updateAlert(alertId, { status: action === 'pause' ? 'paused' : 'active' });
            displayAlerts();
            createToast('success', 'Success', `Alert ${action}d successfully`);
        } else {
            throw new Error(result.message || `Failed to ${action} alert`);
        }
    } catch (error) {
        console.error(`❌ Error ${action}ing alert:`, error);
        createToast('error', 'Error', `Failed to ${action} alert: ${error.message}`);
    }
}

/**
 * Handle mark notification as read
 */
async function handleMarkNotificationAsRead(notificationId) {
    try {
        await markNotificationAsReadAPI(notificationId);
        StateActions.markNotificationRead(notificationId);
        displayInAppNotifications();
        updateNotificationBadge();
    } catch (error) {
        console.error('❌ Error marking notification as read:', error);
        // Still update locally for better UX
        StateActions.markNotificationRead(notificationId);
        displayInAppNotifications();
        updateNotificationBadge();
    }
}

/**
 * Handle dismiss notification
 */
async function handleDismissNotification(notificationId) {
    try {
        await dismissNotificationAPI(notificationId);
        StateActions.removeNotification(notificationId);
        displayInAppNotifications();
        updateNotificationBadge();
    } catch (error) {
        console.error('❌ Error dismissing notification:', error);
        // Still update locally for better UX
        StateActions.removeNotification(notificationId);
        displayInAppNotifications();
        updateNotificationBadge();
    }
}

/**
 * Refresh alerts data
 */
async function refreshAlerts() {
    // This will be imported from main.js
    if (window.refreshAlertsData) {
        await window.refreshAlertsData();
    }
}

// Global exports for onclick handlers
window.testAlert = handleTestAlert;
window.pauseResumeAlert = handlePauseResumeAlert;
window.markNotificationAsRead = handleMarkNotificationAsRead;
window.dismissNotification = handleDismissNotification;