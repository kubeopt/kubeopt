/**
 * ============================================================================
 * AKS COST INTELLIGENCE - NOTIFICATION SYSTEM
 * ============================================================================
 * Enhanced notification manager for user feedback
 * ============================================================================
 */

import { AppConfig } from './config.js';

/**
 * Enhanced notification manager for user feedback
 */
class NotificationManager {
    constructor() {
        this.container = this.createContainer();
    }
    
    createContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            container.style.top = '100px'; // Below navbar
            document.body.appendChild(container);
        }
        return container;
    }
    
    show(message, type = 'info', duration = AppConfig.NOTIFICATION_DURATION) {
        //  Ensure duration is always a number
        let numericDuration = duration;
        if (typeof duration === 'string') {
            numericDuration = parseInt(duration, 10);
            if (isNaN(numericDuration)) {
                numericDuration = AppConfig.NOTIFICATION_DURATION || 5000;
            }
        }
        
        const toastElement = document.createElement('div');
        toastElement.className = `toast align-items-center text-white bg-${this.getBootstrapColor(type)} border-0`;
        toastElement.setAttribute('role', 'alert');
        toastElement.setAttribute('aria-live', 'assertive');
        toastElement.setAttribute('aria-atomic', 'true');
        toastElement.style.cssText = `
            backdrop-filter: blur(10px);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            margin-bottom: 0.75rem;
            min-width: 300px;
        `;
        
        toastElement.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${this.getIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        this.container.appendChild(toastElement);
        
        if (window.bootstrap && bootstrap.Toast) {
            try {
                //  Pass numeric duration and proper options
                const toastOptions = {
                    autohide: numericDuration > 0,
                    delay: numericDuration // This must be a number, not a string
                };
                
                console.log(`Creating Bootstrap Toast with options:`, toastOptions);
                
                const toast = new bootstrap.Toast(toastElement, toastOptions);
                toast.show();
                
                toastElement.addEventListener('hidden.bs.toast', () => {
                    if (toastElement.parentNode) {
                        toastElement.parentNode.removeChild(toastElement);
                    }
                });
                
            } catch (error) {
                console.error('Bootstrap Toast error:', error);
                // Fallback if Bootstrap Toast fails
                this.fallbackToast(toastElement, numericDuration);
            }
        } else {
            // Fallback if Bootstrap is not available
            this.fallbackToast(toastElement, numericDuration);
        }
    }
    
    fallbackToast(toastElement, duration) {
        // Manual fade-in effect
        toastElement.style.opacity = '0';
        toastElement.style.transform = 'translateX(100%)';
        toastElement.style.transition = 'all 0.3s ease';
        
        setTimeout(() => {
            toastElement.style.opacity = '1';
            toastElement.style.transform = 'translateX(0)';
        }, 100);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                toastElement.style.opacity = '0';
                toastElement.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (toastElement.parentNode) {
                        toastElement.parentNode.removeChild(toastElement);
                    }
                }, 300);
            }, duration);
        }
        
        // Manual close button functionality
        const closeBtn = toastElement.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                toastElement.style.opacity = '0';
                toastElement.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (toastElement.parentNode) {
                        toastElement.parentNode.removeChild(toastElement);
                    }
                }, 300);
            });
        }
    }
    
    getBootstrapColor(type) {
        const colors = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'primary'
        };
        return colors[type] || 'primary';
    }
    
    getIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Initialize notification manager
const notificationManager = new NotificationManager();

/**
 * Global notification function (FIXED)
 */
export function showNotification(message, type = 'info', duration = AppConfig.NOTIFICATION_DURATION) {
    //  Ensure duration is numeric before passing to manager
    let numericDuration = duration;
    if (typeof duration === 'string') {
        numericDuration = parseInt(duration, 10);
        if (isNaN(numericDuration)) {
            numericDuration = AppConfig.NOTIFICATION_DURATION || 5000;
        }
    }
    
    console.log(`Showing notification: ${message} (type: ${type}, duration: ${numericDuration})`);
    notificationManager.show(message, type, numericDuration);
}

// Alias for compatibility
export const showToast = showNotification;

/**
 * Enhanced notification with custom positioning (FIXED)
 */
export function showNotificationFixed(message, type = 'info', duration = 5000) {
    //  Ensure duration is numeric
    let numericDuration = duration;
    if (typeof duration === 'string') {
        numericDuration = parseInt(duration, 10);
        if (isNaN(numericDuration)) {
            numericDuration = 5000;
        }
    }
    
    // Remove existing notifications
    document.querySelectorAll('.notification-toast').forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed notification-toast`;
    toast.style.cssText = `
        top: 100px; 
        right: 20px; 
        z-index: 9999; 
        min-width: 350px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        backdrop-filter: blur(10px);
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;
    
    const iconMap = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas fa-${iconMap[type] || 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" onclick="this.parentNode.remove()"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto-remove
    if (numericDuration > 0) {
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, numericDuration);
    }
}

/**
 * Show loading notification (FIXED)
 */
export function showLoadingNotification(message) {
    const loadingId = 'loading-notification-' + Date.now();
    const toast = document.createElement('div');
    toast.id = loadingId;
    toast.className = 'alert alert-info alert-dismissible fade show position-fixed notification-toast';
    toast.style.cssText = `
        top: 100px; 
        right: 20px; 
        z-index: 9999; 
        min-width: 350px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        backdrop-filter: blur(10px);
    `;
    
    toast.innerHTML = `
        <i class="fas fa-spinner fa-spin me-2"></i>
        ${message}
        <button type="button" class="btn-close" onclick="this.parentNode.remove()"></button>
    `;
    
    document.body.appendChild(toast);
    
    return {
        id: loadingId,
        dismiss: () => {
            const element = document.getElementById(loadingId);
            if (element) {
                element.remove();
            }
        },
        update: (newMessage) => {
            const element = document.getElementById(loadingId);
            if (element) {
                element.innerHTML = `
                    <i class="fas fa-spinner fa-spin me-2"></i>
                    ${newMessage}
                    <button type="button" class="btn-close" onclick="this.parentNode.remove()"></button>
                `;
            }
        }
    };
}

/**
 * Show progress notification with steps (FIXED)
 */
export function showProgressNotification(steps, currentStep = 0) {
    const progressId = 'progress-notification-' + Date.now();
    const toast = document.createElement('div');
    toast.id = progressId;
    toast.className = 'alert alert-info alert-dismissible fade show position-fixed notification-toast';
    toast.style.cssText = `
        top: 100px; 
        right: 20px; 
        z-index: 9999; 
        min-width: 400px;
        max-width: 500px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        backdrop-filter: blur(10px);
    `;
    
    function updateProgress(step) {
        const element = document.getElementById(progressId);
        if (!element) return;
        
        const progress = Math.round((step / steps.length) * 100);
        const currentStepText = steps[step] || 'Completing...';
        
        element.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-cogs fa-spin me-2"></i>
                <span>${currentStepText}</span>
                <button type="button" class="btn-close ms-auto" onclick="this.parentNode.parentNode.remove()"></button>
            </div>
            <div class="progress" style="height: 6px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     style="width: ${progress}%" role="progressbar"></div>
            </div>
            <small class="text-muted mt-1 d-block">Step ${step + 1} of ${steps.length}</small>
        `;
    }
    
    document.body.appendChild(toast);
    updateProgress(currentStep);
    
    return {
        id: progressId,
        updateStep: updateProgress,
        complete: (message = 'Completed successfully!') => {
            const element = document.getElementById(progressId);
            if (element) {
                element.className = element.className.replace('alert-info', 'alert-success');
                element.innerHTML = `
                    <i class="fas fa-check-circle me-2"></i>
                    ${message}
                    <button type="button" class="btn-close" onclick="this.parentNode.remove()"></button>
                `;
                
                setTimeout(() => {
                    if (element.parentNode) {
                        element.remove();
                    }
                }, 3000);
            }
        },
        dismiss: () => {
            const element = document.getElementById(progressId);
            if (element) {
                element.remove();
            }
        }
    };
}

//  Enhanced global showNotification function for backward compatibility
function createGlobalShowNotification() {
    return function(title, message, type = 'info', duration = 5000) {
        // Handle both old format (title, message) and new format (message only)
        let finalMessage = message ? `${title}: ${message}` : title;
        
        //  Ensure duration is numeric
        let numericDuration = duration;
        if (typeof duration === 'string') {
            numericDuration = parseInt(duration, 10);
            if (isNaN(numericDuration)) {
                numericDuration = 5000;
            }
        }
        
        console.log(`Global showNotification called: ${finalMessage} (type: ${type}, duration: ${numericDuration})`);
        
        // Use the notification manager
        notificationManager.show(finalMessage, type, numericDuration);
    };
}

// Make functions available globally for backward compatibility
if (typeof window !== 'undefined') {
    window.showNotification = createGlobalShowNotification();
    window.showToast = showToast;
    window.showNotificationFixed = showNotificationFixed;
    window.showLoadingNotification = showLoadingNotification;
    window.showProgressNotification = showProgressNotification;
    window.notificationManager = notificationManager;
    
    console.log('✅ Fixed notification system loaded - Bootstrap Toast compatible');
}