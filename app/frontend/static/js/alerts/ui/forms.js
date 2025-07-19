// frontend/static/js/alerts/ui/forms.js

import { validateAlertForm, isValidEmail } from '../utils/validation.js';
import { getFormData, getSelectedCheckboxes, clearForm, setButtonLoading } from '../utils/dom.js';
import { createAlert } from '../api/alerts.js';
import { AlertsState } from '../core/state.js';
import { createToast } from '../utils/dom.js';
import { getFrequencyInfo, escapeHtml } from '../utils/formatting.js';

/**
 * Form handling utilities for alerts system
 */

/**
 * Setup frequency preview functionality
 */
export function setupFrequencyPreview() {
    const frequencySelect = document.getElementById('notification-frequency');
    const previewText = document.getElementById('frequency-preview-text');
    const notificationTime = document.getElementById('notification-time');
    const maxNotifications = document.getElementById('max-notifications');
    const cooldownPeriod = document.getElementById('cooldown-period');
    
    if (!frequencySelect || !previewText) return;
    
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
        
        previewText.innerHTML = preview;
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

/**
 * Handle threshold type change in forms
 */
export function updateThresholdInput() {
    const thresholdType = document.getElementById('threshold-type');
    const thresholdSymbol = document.getElementById('threshold-symbol');
    const thresholdInput = document.getElementById('threshold-input');
    const thresholdLabel = document.getElementById('threshold-label');
    
    if (!thresholdType || !thresholdSymbol || !thresholdInput || !thresholdLabel) return;
    
    const type = thresholdType.value;
    
    if (type === 'amount') {
        thresholdSymbol.textContent = '$';
        thresholdInput.placeholder = '5000';
        thresholdInput.step = '0.01';
        thresholdInput.max = '';
        thresholdLabel.textContent = 'Threshold Amount *';
    } else if (type === 'percentage') {
        thresholdSymbol.textContent = '%';
        thresholdInput.placeholder = '80';
        thresholdInput.step = '1';
        thresholdInput.max = '100';
        thresholdLabel.textContent = 'Threshold Percentage *';
    }
}

/**
 * Validate form with visual feedback
 */
export function validateFormWithFeedback(form, validationFunction) {
    // Clear previous validation messages
    form.querySelectorAll('.is-invalid').forEach(el => {
        el.classList.remove('is-invalid');
    });
    
    form.querySelectorAll('.invalid-feedback').forEach(el => {
        el.remove();
    });
    
    const formData = getFormData(form);
    const errors = validationFunction(formData);
    
    if (errors.length > 0) {
        // Show first error as toast
        createToast('error', 'Validation Error', errors[0]);
        
        // Add visual feedback to form fields
        errors.forEach(error => {
            if (error.includes('name')) {
                addFieldError(form.querySelector('[name="name"]'), error);
            } else if (error.includes('email')) {
                addFieldError(form.querySelector('[name="email"]'), error);
            } else if (error.includes('threshold')) {
                addFieldError(form.querySelector('[name="threshold_amount"], [name="threshold_percentage"]'), error);
            }
        });
        
        return false;
    }
    
    return true;
}

/**
 * Add error styling and message to form field
 */
function addFieldError(field, message) {
    if (!field) return;
    
    field.classList.add('is-invalid');
    
    const feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    feedback.textContent = message;
    
    field.parentNode.appendChild(feedback);
}

/**
 * Auto-save form data to localStorage for recovery
 */
export function setupFormAutoSave(formId, key) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    // Load saved data
    const savedData = localStorage.getItem(`form_autosave_${key}`);
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            Object.entries(data).forEach(([name, value]) => {
                const field = form.querySelector(`[name="${name}"]`);
                if (field) {
                    if (field.type === 'checkbox') {
                        field.checked = value;
                    } else {
                        field.value = value;
                    }
                }
            });
        } catch (error) {
            console.warn('Failed to restore form data:', error);
        }
    }
    
    // Save data on change
    form.addEventListener('input', debounce(() => {
        const formData = getFormData(form);
        localStorage.setItem(`form_autosave_${key}`, JSON.stringify(formData));
    }, 500));
    
    // Clear saved data on successful submit
    form.addEventListener('submit', () => {
        localStorage.removeItem(`form_autosave_${key}`);
    });
}

/**
 * Create a form builder for dynamic forms
 */
export class AlertFormBuilder {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.fields = [];
    }
    
    addTextField(name, label, required = false, placeholder = '') {
        this.fields.push({
            type: 'text',
            name,
            label,
            required,
            placeholder
        });
        return this;
    }
    
    addEmailField(name, label, required = false, placeholder = '') {
        this.fields.push({
            type: 'email',
            name,
            label,
            required,
            placeholder
        });
        return this;
    }
    
    addNumberField(name, label, required = false, min = 0, max = null, step = 1) {
        this.fields.push({
            type: 'number',
            name,
            label,
            required,
            min,
            max,
            step
        });
        return this;
    }
    
    addSelectField(name, label, options, required = false) {
        this.fields.push({
            type: 'select',
            name,
            label,
            options,
            required
        });
        return this;
    }
    
    addCheckboxGroup(name, label, options) {
        this.fields.push({
            type: 'checkbox-group',
            name,
            label,
            options
        });
        return this;
    }
    
    render() {
        if (!this.container) return;
        
        const formHTML = `
            <form class="dynamic-alert-form">
                ${this.fields.map(field => this.renderField(field)).join('')}
                <div class="form-group mt-3">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Create Alert
                    </button>
                    <button type="button" class="btn btn-secondary ms-2" onclick="this.closest('form').reset()">
                        Reset
                    </button>
                </div>
            </form>
        `;
        
        this.container.innerHTML = formHTML;
        
        // Setup form handling
        const form = this.container.querySelector('form');
        form.addEventListener('submit', this.handleSubmit.bind(this));
        
        return form;
    }
    
    renderField(field) {
        const requiredAttr = field.required ? 'required' : '';
        const requiredLabel = field.required ? ' *' : '';
        
        switch (field.type) {
            case 'text':
            case 'email':
            case 'number':
                return `
                    <div class="form-group mb-3">
                        <label class="form-label">${escapeHtml(field.label)}${requiredLabel}</label>
                        <input type="${field.type}" 
                               class="form-control" 
                               name="${field.name}" 
                               ${requiredAttr}
                               ${field.placeholder ? `placeholder="${escapeHtml(field.placeholder)}"` : ''}
                               ${field.min !== undefined ? `min="${field.min}"` : ''}
                               ${field.max !== undefined ? `max="${field.max}"` : ''}
                               ${field.step !== undefined ? `step="${field.step}"` : ''}>
                    </div>
                `;
            
            case 'select':
                const options = field.options.map(opt => 
                    `<option value="${escapeHtml(opt.value)}">${escapeHtml(opt.label)}</option>`
                ).join('');
                
                return `
                    <div class="form-group mb-3">
                        <label class="form-label">${escapeHtml(field.label)}${requiredLabel}</label>
                        <select class="form-select" name="${field.name}" ${requiredAttr}>
                            <option value="">Select ${field.label.toLowerCase()}</option>
                            ${options}
                        </select>
                    </div>
                `;
            
            case 'checkbox-group':
                const checkboxes = field.options.map(opt => `
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" 
                               name="${field.name}" value="${escapeHtml(opt.value)}" 
                               id="${field.name}_${opt.value}">
                        <label class="form-check-label" for="${field.name}_${opt.value}">
                            ${escapeHtml(opt.label)}
                        </label>
                    </div>
                `).join('');
                
                return `
                    <div class="form-group mb-3">
                        <label class="form-label">${escapeHtml(field.label)}${requiredLabel}</label>
                        <div class="checkbox-group">
                            ${checkboxes}
                        </div>
                    </div>
                `;
            
            default:
                return '';
        }
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = getFormData(form);
        
        // Get selected checkboxes
        const checkboxGroups = {};
        this.fields.filter(f => f.type === 'checkbox-group').forEach(field => {
            checkboxGroups[field.name] = getSelectedCheckboxes(form, field.name);
        });
        
        const alertData = {
            ...formData,
            ...checkboxGroups,
            cluster_id: AlertsState.currentClusterId
        };
        
        // Validate
        if (!validateFormWithFeedback(form, validateAlertForm)) {
            return;
        }
        
        const submitBtn = form.querySelector('button[type="submit"]');
        setButtonLoading(submitBtn, true, 'Creating...');
        
        try {
            const result = await createAlert(alertData);
            
            if (result.status === 'success') {
                createToast('success', 'Success', 'Alert created successfully!');
                clearForm(form);
                
                // Refresh alerts if function exists
                if (window.refreshAlertsData) {
                    await window.refreshAlertsData();
                }
            } else {
                throw new Error(result.message || 'Failed to create alert');
            }
        } catch (error) {
            console.error('❌ Error creating alert:', error);
            createToast('error', 'Error', `Failed to create alert: ${error.message}`);
        } finally {
            setButtonLoading(submitBtn, false);
        }
    }
}

/**
 * Debounce utility for form auto-save
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Global exports for HTML templates
window.setupFrequencyPreview = setupFrequencyPreview;
window.updateThresholdInput = updateThresholdInput;
window.AlertFormBuilder = AlertFormBuilder;