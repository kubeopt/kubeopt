// frontend/static/js/alerts/ui/modals.js

import { BootstrapHelper } from '../utils/bootstrap.js';
import { getFrequencyInfo, escapeHtml } from '../utils/formatting.js';
import { FREQUENCY_MAP } from '../core/config.js';
import { StateActions, AlertsState } from '../core/state.js';

/**
 * Modal management functions
 */

/**
 * Show delete alert confirmation modal
 */
export function showDeleteAlertModal(alertId, alertName) {
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
    
    removeExistingModal('deleteAlertModal');
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    const modalElement = document.getElementById('deleteAlertModal');
    window.currentDeleteModal = BootstrapHelper.showModal(modalElement);
}

/**
 * Close delete alert modal
 */
export function closeDeleteAlertModal() {
    const modalElement = document.getElementById('deleteAlertModal');
    if (modalElement) {
        BootstrapHelper.hideModal(modalElement);
        setTimeout(() => modalElement.remove(), 300);
    }
    window.currentDeleteModal = null;
}

/**
 * Show create alert modal
 */
export function showCreateAlertModal() {
    const frequencyOptions = Object.keys(FREQUENCY_MAP).map(key => {
        const info = getFrequencyInfo(key);
        return `
            <option value="${key}" ${key === AlertsState.defaultFrequency ? 'selected' : ''}>
                ${info.display} - ${info.description}
            </option>
        `;
    }).join('');
    
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
                                        <label class="form-label">Threshold Amount ($)</label>
                                        <input type="number" class="form-control" name="threshold_amount" 
                                               min="0" step="0.01" placeholder="5000">
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
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Notification Frequency</label>
                                        <select class="form-select" name="notification_frequency">
                                            ${frequencyOptions}
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
    
    removeExistingModal('createAlertModal');
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    const modalElement = document.getElementById('createAlertModal');
    BootstrapHelper.showModal(modalElement);
}

/**
 * Close create alert modal (FIXED - properly cleans up)
 */
export function closeCreateAlertModal() {
    const modal = document.getElementById('createAlertModal');
    const backdrop = document.getElementById('createAlertBackdrop');
    
    if (modal) {
        // Hide modal
        modal.style.display = 'none';
        modal.classList.remove('show');
        modal.remove();
    }
    
    if (backdrop) {
        backdrop.remove();
    }
    
    // Remove modal-open class from body
    document.body.classList.remove('modal-open');
    
    console.log('✅ Create alert modal closed');
}

/**
 * Show edit alert modal
 */
export function showEditAlertModal(alertId) {
    const alert = AlertsState.alerts.find(a => a.id == alertId);
    if (!alert) return;
    
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
    
    removeExistingModal('editAlertModal');
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    const modalElement = document.getElementById('editAlertModal');
    BootstrapHelper.showModal(modalElement);
}

/**
 * Close edit alert modal
 */
export function closeEditAlertModal() {
    const modalElement = document.getElementById('editAlertModal');
    if (modalElement) {
        BootstrapHelper.hideModal(modalElement);
        setTimeout(() => modalElement.remove(), 300);
    }
}

/**
 * Show edit frequency modal - ENHANCED VERSION
 */
export function showEditFrequencyModal(alertId) {
    const alert = AlertsState.alerts.find(a => a.id == alertId);
    if (!alert) return;
    
    const frequencyOptions = Object.keys(FREQUENCY_MAP).map(key => {
        const info = getFrequencyInfo(key);
        const selected = alert.notification_frequency === key ? 'selected' : '';
        return `<option value="${key}" ${selected}>${info.display}</option>`;
    }).join('');
    
    const modalHTML = `
        <div class="modal fade" id="editFrequencyModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-md">
                <div class="modal-content">
                    <div class="modal-header bg-info text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-clock me-2"></i>Edit Frequency Settings
                        </h5>
                        <button type="button" class="btn-close btn-close-white" 
                                onclick="closeEditFrequencyModal()" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="edit-frequency-form">
                            <div class="form-group mb-3">
                                <label class="form-label">Notification Frequency</label>
                                <select class="form-select" name="notification_frequency" id="edit-frequency-select">
                                    ${frequencyOptions}
                                </select>
                            </div>
                            
                            <div class="form-group mb-3">
                                <label class="form-label">Time (for daily/weekly alerts)</label>
                                <input type="time" class="form-control" name="frequency_at_time" 
                                       value="${alert.frequency_at_time || '09:00'}">
                            </div>
                            
                            <div class="form-group mb-3">
                                <label class="form-label">Max notifications per day</label>
                                <input type="number" class="form-control" name="max_notifications_per_day" 
                                       value="${alert.max_notifications_per_day || ''}" min="1" max="100"
                                       placeholder="No limit">
                            </div>
                            
                            <div class="form-group mb-3">
                                <label class="form-label">Cooldown period (hours)</label>
                                <input type="number" class="form-control" name="cooldown_period_hours" 
                                       value="${alert.cooldown_period_hours || 4}" min="0" max="168">
                                <small class="form-text text-muted">Minimum time between notifications</small>
                            </div>
                            
                            <div class="alert alert-light" id="edit-frequency-preview-text">
                                Preview will appear here...
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="closeEditFrequencyModal()">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="saveFrequencySettings(${alertId})">
                            <i class="fas fa-save me-2"></i>Save Settings
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    removeExistingModal('editFrequencyModal');
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    const modalElement = document.getElementById('editFrequencyModal');
    BootstrapHelper.showModal(modalElement);
    
    // Setup preview
    setupEditFrequencyPreview();
}

/**
 * Close edit frequency modal
 */
export function closeEditFrequencyModal() {
    const modalElement = document.getElementById('editFrequencyModal');
    if (modalElement) {
        BootstrapHelper.hideModal(modalElement);
        setTimeout(() => modalElement.remove(), 300);
    }
}

/**
 * Setup frequency preview in edit modal - ENHANCED VERSION
 */
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
        
        // Add recommendation
        if (frequency === 'immediate' && (!cooldown || cooldown === '0')) {
            preview += `<br><span class="text-warning"><i class="fas fa-exclamation-triangle me-1"></i>Recommendation: Add cooldown period to prevent spam</span>`;
        }
        
        previewText.innerHTML = preview;
    }
    
    // Add event listeners
    const inputs = [
        document.getElementById('edit-frequency-select'),
        document.querySelector('#editFrequencyModal [name="max_notifications_per_day"]'),
        document.querySelector('#editFrequencyModal [name="cooldown_period_hours"]'),
        document.querySelector('#editFrequencyModal [name="frequency_at_time"]')
    ];
    
    inputs.forEach(input => {
        if (input) {
            input.addEventListener('change', updatePreview);
        }
    });
    
    // Initial preview
    updatePreview();
}

/**
 * Save frequency settings - NEW ENHANCED FUNCTION
 */
window.saveFrequencySettings = async function(alertId) {
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
    
    try {
        const response = await fetch(`/api/alerts/${alertId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // Show success message (assuming createToast function exists)
            if (typeof createToast === 'function') {
                createToast('success', 'Success', 'Frequency settings saved successfully!');
            } else {
                console.log('✅ Frequency settings saved successfully!');
            }
            
            closeEditFrequencyModal();
            
            // Update the alert in state
            const alert = AlertsState.alerts.find(a => a.id == alertId);
            if (alert) {
                Object.assign(alert, updates);
            }
            
            // Refresh alerts display
            if (window.refreshAlertsData) {
                await window.refreshAlertsData();
            }
        } else {
            throw new Error(result.message || 'Failed to save frequency settings');
        }
    } catch (error) {
        console.error('❌ Error saving frequency settings:', error);
        if (typeof createToast === 'function') {
            createToast('error', 'Error', `Failed to save frequency settings: ${error.message}`);
        } else {
            alert(`Failed to save frequency settings: ${error.message}`);
        }
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
};

/**
 * Remove existing modal if present
 */
function removeExistingModal(modalId) {
    const existingModal = document.getElementById(modalId);
    if (existingModal) {
        existingModal.remove();
    }
}

// Global exports for onclick handlers
window.showEditFrequencyModal = showEditFrequencyModal;
window.closeDeleteAlertModal = closeDeleteAlertModal;
window.closeCreateAlertModal = closeCreateAlertModal;
window.closeEditAlertModal = closeEditAlertModal;
window.closeEditFrequencyModal = closeEditFrequencyModal;