// frontend/static/js/alerts/utils/dom.js

import { escapeHtml } from './formatting.js';

/**
 * DOM manipulation utilities
 */

/**
 * Show/hide loading state on button
 */
export function setButtonLoading(button, loading, loadingText = 'Loading...') {
    if (!button) return;
    
    if (loading) {
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${loadingText}`;
        button.disabled = true;
    } else {
        button.innerHTML = button.dataset.originalText || button.innerHTML;
        button.disabled = false;
        delete button.dataset.originalText;
    }
}

/**
 * Create and show toast notification
 */
export function createToast(type, title, message, duration = 5000) {
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
    
    const existingToasts = document.querySelectorAll('[id^="toast-"]').length;
    const topPosition = 20 + (existingToasts * 80);
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0 shadow-lg" 
             role="alert" aria-live="assertive" aria-atomic="true" 
             style="position: fixed; top: ${topPosition}px; right: 20px; z-index: 9999; min-width: 350px; max-width: 400px;">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center">
                    <i class="${iconClass} me-2"></i>
                    <div>
                        <div class="fw-bold">${escapeHtml(title)}</div>
                        <div class="small">${escapeHtml(message)}</div>
                    </div>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        onclick="dismissToast('${toastId}')" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    toastElement.style.opacity = '0';
    toastElement.style.transform = 'translateX(100%)';
    
    // Animate in
    setTimeout(() => {
        toastElement.style.transition = 'all 0.3s ease-out';
        toastElement.style.opacity = '1';
        toastElement.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto remove
    setTimeout(() => {
        dismissToast(toastId);
    }, duration);
    
    return toastId;
}

/**
 * Dismiss toast notification
 */
export function dismissToast(toastId) {
    const toastElement = document.getElementById(toastId);
    if (toastElement) {
        toastElement.style.transition = 'all 0.3s ease-out';
        toastElement.style.opacity = '0';
        toastElement.style.transform = 'translateX(100%)';
        
        setTimeout(() => {
            if (toastElement.parentNode) {
                toastElement.remove();
            }
            repositionToasts();
        }, 300);
    }
}

/**
 * Reposition remaining toasts
 */
export function repositionToasts() {
    const toasts = document.querySelectorAll('[id^="toast-"]');
    toasts.forEach((toast, index) => {
        toast.style.top = `${20 + (index * 80)}px`;
    });
}

/**
 * Toggle element visibility
 */
export function toggleElement(element, show) {
    if (!element) return;
    
    if (show) {
        element.style.display = 'block';
        element.classList.remove('hidden');
    } else {
        element.style.display = 'none';
        element.classList.add('hidden');
    }
}

/**
 * Add loading skeleton to container
 */
export function showLoadingSkeleton(container, rows = 3) {
    if (!container) return;
    
    const skeletonHTML = Array.from({ length: rows }, () => `
        <div class="skeleton-item animate-pulse">
            <div class="flex items-center space-x-4 p-4">
                <div class="w-4 h-4 bg-gray-300 rounded-full"></div>
                <div class="flex-1">
                    <div class="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
                    <div class="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
                <div class="w-20 h-4 bg-gray-300 rounded"></div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = skeletonHTML;
}

/**
 * Get form data as object
 */
export function getFormData(form) {
    if (!form) return {};
    
    const formData = new FormData(form);
    const data = {};
    
    for (const [key, value] of formData.entries()) {
        if (data[key]) {
            // Handle multiple values (like checkboxes)
            if (Array.isArray(data[key])) {
                data[key].push(value);
            } else {
                data[key] = [data[key], value];
            }
        } else {
            data[key] = value;
        }
    }
    
    return data;
}

/**
 * Get selected checkbox values
 */
export function getSelectedCheckboxes(container, name) {
    if (!container) return [];
    
    const checkboxes = container.querySelectorAll(`input[name="${name}"]:checked`);
    return Array.from(checkboxes).map(cb => cb.value);
}

/**
 * Clear form
 */
export function clearForm(form) {
    if (!form) return;
    
    form.reset();
    
    // Clear any custom validation messages
    form.querySelectorAll('.is-invalid').forEach(el => {
        el.classList.remove('is-invalid');
    });
    
    form.querySelectorAll('.invalid-feedback').forEach(el => {
        el.remove();
    });
}

/**
 * Animate element removal
 */
export function animateRemoval(element, callback) {
    if (!element) return;
    
    element.style.transition = 'all 0.3s ease-out';
    element.style.opacity = '0';
    element.style.transform = 'scale(0.95)';
    
    setTimeout(() => {
        if (element.parentNode) {
            element.remove();
        }
        if (callback) callback();
    }, 300);
}

/**
 * Animate element addition
 */
export function animateAddition(element) {
    if (!element) return;
    
    element.style.opacity = '0';
    element.style.transform = 'scale(0.95)';
    
    setTimeout(() => {
        element.style.transition = 'all 0.3s ease-out';
        element.style.opacity = '1';
        element.style.transform = 'scale(1)';
    }, 10);
}

// Make dismissToast globally available for onclick handlers
window.dismissToast = dismissToast;