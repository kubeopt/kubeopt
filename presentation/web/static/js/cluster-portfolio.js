/* Cluster Portfolio JavaScript - Extracted from HTML template */


// ===== ENHANCED APPLICATION STATE =====
const AppState = {
    clusters: [],
    subscriptions: [],
    notifications: new Map(),
    isLoading: false,
    analyzingClusters: new Set(),
    currentModal: null,
    debugMode: false
};

// ===== ENHANCED UTILITY FUNCTIONS =====
const Utils = {
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.toString().replace(/[&<>"']/g, (m) => map[m]);
    },

    generateId() {
        return 'id-' + Math.random().toString(36).substr(2, 9);
    },

    // ✅ ENHANCED: Safe element getter with comprehensive logging
    safeGetElement(id, context = 'Unknown') {
        const element = document.getElementById(id);
        if (!element && AppState.debugMode) {
            console.warn(`⚠️ Element '${id}' not found in context: ${context}`);
        }
        return element;
    },

    // ✅ ENHANCED: Safe element access with callback and error handling
    withElement(id, callback, context = 'Unknown') {
        const element = this.safeGetElement(id, context);
        if (element && typeof callback === 'function') {
            try {
                return callback(element);
            } catch (error) {
                console.error(`❌ Error in withElement callback for '${id}':`, error);
                return null;
            }
        }
        return null;
    },

    // ✅ NEW: Robust form validation with enhanced patterns
    validateInput(element, rules = {}) {
        if (!element) return { valid: false, errors: ['Element not found'] };
        
        const value = element.value.trim();
        const errors = [];
        
        if (rules.required && !value) {
            errors.push(`${element.name || 'Field'} is required`);
        }
        
        if (rules.minLength && value.length < rules.minLength) {
            errors.push(`Minimum length is ${rules.minLength} characters`);
        }
        
        if (rules.maxLength && value.length > rules.maxLength) {
            errors.push(`Maximum length is ${rules.maxLength} characters`);
        }
        
        if (rules.pattern && !rules.pattern.test(value)) {
            errors.push(rules.message || 'Invalid format');
        }
        
        return { valid: errors.length === 0, errors };
    }
};

// ===== ENHANCED FORM VALIDATION =====
function validateForm() {
    // Clear previous validation errors
    document.querySelectorAll('.field-error').forEach(error => {
        error.textContent = '';
    });
    document.querySelectorAll('.enhanced-input, .enhanced-select').forEach(input => {
        input.classList.remove('error');
    });
    
    let isValid = true;
    
    // Validate cluster name
    const clusterNameInput = document.getElementById('clusterName');
    const clusterNameError = document.getElementById('clusterNameError');
    const clusterNameValue = clusterNameInput?.value?.trim();
    
    if (!clusterNameValue) {
        if (clusterNameInput) clusterNameInput.classList.add('error');
        if (clusterNameError) clusterNameError.textContent = 'Cluster name is required';
        isValid = false;
    } else if (clusterNameValue.length < 3) {
        if (clusterNameInput) clusterNameInput.classList.add('error');
        if (clusterNameError) clusterNameError.textContent = 'Cluster name must be at least 3 characters';
        isValid = false;
    } else if (!/^[a-zA-Z0-9-_]+$/.test(clusterNameValue)) {
        if (clusterNameInput) clusterNameInput.classList.add('error');
        if (clusterNameError) clusterNameError.textContent = 'Cluster name can only contain letters, numbers, hyphens, and underscores';
        isValid = false;
    }
    
    // Validate resource group
    const resourceGroupInput = document.getElementById('resourceGroup');
    const resourceGroupError = document.getElementById('resourceGroupError');
    const resourceGroupValue = resourceGroupInput?.value?.trim();
    
    if (!resourceGroupValue) {
        if (resourceGroupInput) resourceGroupInput.classList.add('error');
        if (resourceGroupError) resourceGroupError.textContent = 'Resource group is required';
        isValid = false;
    } else if (resourceGroupValue.length < 3) {
        if (resourceGroupInput) resourceGroupInput.classList.add('error');
        if (resourceGroupError) resourceGroupError.textContent = 'Resource group must be at least 3 characters';
        isValid = false;
    }
    
    // Validate subscription
    const subscriptionSelect = document.getElementById('subscriptionSelect');
    const subscriptionError = document.getElementById('subscriptionError');
    const subscriptionValue = subscriptionSelect?.value;
    
    if (!subscriptionValue) {
        if (subscriptionSelect) subscriptionSelect.classList.add('error');
        if (subscriptionError) subscriptionError.textContent = 'Azure subscription is required';
        isValid = false;
    }
    
    return isValid;
}

// ===== ENHANCED LOADING MANAGEMENT =====
const LoadingManager = {
    show(message = 'Processing...') {
        const toast = Utils.safeGetElement('loadingToast', 'LoadingManager.show');
        if (toast) {
            const text = toast.querySelector('.loading-text');
            if (text) text.textContent = message;
            toast.classList.add('show');
            AppState.isLoading = true;
        }
    },

    hide() {
        const toast = Utils.safeGetElement('loadingToast', 'LoadingManager.hide');
        if (toast) {
            toast.classList.remove('show');
            AppState.isLoading = false;
        }
    },

    // ✅ ENHANCED: Better button loading state management
    button(button, loading = true) {
        if (!button) {
            console.warn('⚠️ LoadingManager.button: button element is null');
            return;
        }
        
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
            
            // Show loading spinner if available
            const spinner = button.querySelector('.loading-spinner');
            const content = button.querySelector('.btn-content');
            if (spinner) spinner.style.display = 'flex';
            if (content) content.style.opacity = '0';
        } else {
            button.classList.remove('loading');
            button.disabled = false;
            
            // Hide loading spinner
            const spinner = button.querySelector('.loading-spinner');
            const content = button.querySelector('.btn-content');
            if (spinner) spinner.style.display = 'none';
            if (content) content.style.opacity = '1';
        }
    }
};

// ===== ENHANCED SUBSCRIPTION LOADING =====
async function loadSubscriptionsForDropdown() {
    try {
        const subscriptionSelect = Utils.safeGetElement('subscriptionSelect', 'loadSubscriptionsForDropdown');
        if (!subscriptionSelect) {
            console.error('❌ Cannot load subscriptions - select element missing');
            return;
        }
        
        subscriptionSelect.innerHTML = '<option value="">Loading subscriptions...</option>';
        subscriptionSelect.disabled = true;
        
        const response = await fetch('/api/subscriptions/dropdown');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && data.subscriptions) {
            subscriptionSelect.innerHTML = '<option value="">Select a subscription...</option>';
            
            data.subscriptions.forEach(sub => {
                const option = document.createElement('option');
                option.value = sub.id;
                option.textContent = `${sub.display_name} (${sub.subscription_id})`;
                if (sub.is_default) {
                    option.selected = true;
                }
                subscriptionSelect.appendChild(option);
            });
            
            AppState.subscriptions = data.subscriptions;
            console.log(`✅ Loaded ${data.subscriptions.length} subscriptions`);
        } else {
            throw new Error(data.message || 'Invalid response format');
        }
    } catch (error) {
        console.error('❌ Error loading subscriptions:', error);
        const subscriptionSelect = Utils.safeGetElement('subscriptionSelect', 'loadSubscriptionsForDropdown error');
        if (subscriptionSelect) {
            subscriptionSelect.innerHTML = '<option value="">Error loading subscriptions</option>';
            
            NotificationManager.show(
                'Subscription Load Failed',
                'Unable to load Azure subscriptions. Please refresh and try again.',
                'error',
                8000
            );
        }
    } finally {
        const subscriptionSelect = Utils.safeGetElement('subscriptionSelect', 'loadSubscriptionsForDropdown finally');
        if (subscriptionSelect) {
            subscriptionSelect.disabled = false;
        }
    }
}

// ===== ENHANCED ANALYSIS STATE MANAGEMENT =====
const AnalysisStateManager = {
    setAnalyzing(clusterId, analyzing = true) {
        console.log(`🔄 Setting analysis state for ${clusterId}: ${analyzing ? 'START' : 'END'}`);
        
        const clusterCard = document.querySelector(`[data-cluster-id="${clusterId}"]`);
        const analyzeBtn = document.querySelector(`.analyze-btn[data-cluster-id="${clusterId}"]`);
        const statusInfo = document.querySelector(`.status-info[data-cluster-id="${clusterId}"]`);
        
        if (!clusterCard) {
            console.warn(`⚠️ AnalysisStateManager: Cluster card not found for ID: ${clusterId}`);
            return;
        }

        if (analyzing) {
            AppState.analyzingClusters.add(clusterId);
            clusterCard.classList.add('analyzing');
            
            // ✅  Better button state management
            if (analyzeBtn) {
                analyzeBtn.classList.add('analyzing');
                analyzeBtn.disabled = true;
                analyzeBtn.setAttribute('aria-label', 'Analysis in progress');
                
                // Hide play icon and show spinner
                const playIcon = analyzeBtn.querySelector('.fa-play');
                const spinner = analyzeBtn.querySelector('.analyzing-spinner');
                if (playIcon) {
                    playIcon.style.display = 'none';
                }
                if (spinner) {
                    spinner.style.display = 'inline-block';
                } else {
                    // Create spinner if it doesn't exist
                    const newSpinner = document.createElement('i');
                    newSpinner.className = 'fas fa-spinner fa-spin analyzing-spinner';
                    newSpinner.style.position = 'absolute';
                    newSpinner.style.top = '50%';
                    newSpinner.style.left = '50%';
                    newSpinner.style.transform = 'translate(-50%, -50%)';
                    analyzeBtn.appendChild(newSpinner);
                }
                
                console.log(`✅ Button state set to analyzing for ${clusterId}`);
            }
            
            // ✅  Better status info management
            if (statusInfo) {
                // Hide existing status elements
                const existingIcons = statusInfo.querySelectorAll('.fa-clock, .fa-check-circle, .success-icon, .warning-icon');
                const statusText = statusInfo.querySelector('.status-text');
                
                existingIcons.forEach(icon => {
                    if (icon) icon.style.display = 'none';
                });
                if (statusText) statusText.style.display = 'none';
                
                // Show or create analyzing elements
                let analyzingIcon = statusInfo.querySelector('.analyzing-icon');
                let analyzingText = statusInfo.querySelector('.analyzing-text');
                
                if (!analyzingIcon) {
                    analyzingIcon = document.createElement('i');
                    analyzingIcon.className = 'fas fa-cog fa-spin analyzing-icon';
                    analyzingIcon.style.color = '#4f46e5';
                    statusInfo.insertBefore(analyzingIcon, statusInfo.firstChild);
                }
                
                if (!analyzingText) {
                    analyzingText = document.createElement('span');
                    analyzingText.className = 'analyzing-text';
                    analyzingText.style.color = '#4f46e5';
                    analyzingText.style.fontWeight = '500';
                    statusInfo.appendChild(analyzingText);
                }
                
                analyzingIcon.style.display = 'inline-block';
                analyzingText.style.display = 'inline-block';
                analyzingText.textContent = 'Analyzing...';
                
                console.log(`✅ Status info set to analyzing for ${clusterId}`);
            }
            
        } else {
            AppState.analyzingClusters.delete(clusterId);
            clusterCard.classList.remove('analyzing');
            
            // ✅  Reset button state
            if (analyzeBtn) {
                analyzeBtn.classList.remove('analyzing');
                analyzeBtn.disabled = false;
                analyzeBtn.setAttribute('aria-label', 'Analyze cluster');
                
                // Show play icon and hide spinner
                const playIcon = analyzeBtn.querySelector('.fa-play');
                const spinner = analyzeBtn.querySelector('.analyzing-spinner');
                if (playIcon) {
                    playIcon.style.display = 'inline-block';
                }
                if (spinner) {
                    spinner.style.display = 'none';
                }
                
                console.log(`✅ Button state reset for ${clusterId}`);
            }
            
            // ✅  Reset status info
            if (statusInfo) {
                // Hide analyzing elements
                const analyzingIcon = statusInfo.querySelector('.analyzing-icon');
                const analyzingText = statusInfo.querySelector('.analyzing-text');
                
                if (analyzingIcon) analyzingIcon.style.display = 'none';
                if (analyzingText) analyzingText.style.display = 'none';
                
                // Show success status
                let checkIcon = statusInfo.querySelector('.fa-check-circle, .success-icon');
                let statusText = statusInfo.querySelector('.status-text');
                
                if (!checkIcon) {
                    checkIcon = document.createElement('i');
                    checkIcon.className = 'fas fa-check-circle success-icon';
                    checkIcon.style.color = '#10b981';
                    statusInfo.insertBefore(checkIcon, statusInfo.firstChild);
                }
                
                if (!statusText) {
                    statusText = document.createElement('span');
                    statusText.className = 'status-text';
                    statusInfo.appendChild(statusText);
                }
                
                checkIcon.style.display = 'inline-block';
                statusText.style.display = 'inline-block';
                statusText.textContent = 'Analyzed';
                
                console.log(`✅ Status info reset to analyzed for ${clusterId}`);
            }
        }
    }
};

// ===== ENHANCED DELETE FORM MANAGEMENT =====
const DeleteFormManager = {
    show(clusterId, clusterName, resourceGroup) {
        const form = Utils.safeGetElement('deleteConfirmationForm', 'DeleteFormManager.show');
        if (!form) {
            console.error('❌ Delete confirmation form not found');
            NotificationManager.show(
                'UI Error',
                'Delete confirmation dialog is not available. Please refresh the page.',
                'error'
            );
            return;
        }

        const clusterNameEl = Utils.safeGetElement('deleteClusterName', 'DeleteFormManager.show');
        const resourceGroupEl = Utils.safeGetElement('deleteResourceGroup', 'DeleteFormManager.show');
        const clusterIdInput = Utils.safeGetElement('deleteClusterId', 'DeleteFormManager.show');
        const checkbox = Utils.safeGetElement('confirmDelete', 'DeleteFormManager.show');
        const submitBtn = Utils.safeGetElement('confirmDeleteBtn', 'DeleteFormManager.show');

        // ✅ SAFE: Populate form data with null checks
        if (clusterNameEl) clusterNameEl.textContent = clusterName || 'Unknown Cluster';
        if (resourceGroupEl) resourceGroupEl.textContent = resourceGroup || 'Unknown Resource Group';
        if (clusterIdInput) clusterIdInput.value = clusterId || '';

        // ✅ SAFE: Reset form state
        if (checkbox) {
            checkbox.checked = false;
            checkbox.focus();
        }
        if (submitBtn) {
            submitBtn.disabled = true;
            LoadingManager.button(submitBtn, false);
        }

        // ✅ ENHANCED: Show with proper ARIA and focus management
        form.style.display = 'flex';
        form.setAttribute('aria-hidden', 'false');
        AppState.currentModal = 'delete';
        
        setTimeout(() => {
            form.classList.add('show');
            if (checkbox) {
                checkbox.focus();
            }
        }, 10);
        
        if (document.body) {
            document.body.style.overflow = 'hidden';
        }

        console.log(`🗑️ Delete confirmation shown for cluster: ${clusterName}`);
    },

    hide() {
        const form = Utils.safeGetElement('deleteConfirmationForm', 'DeleteFormManager.hide');
        if (form) {
            form.classList.remove('show');
            form.setAttribute('aria-hidden', 'true');
            AppState.currentModal = null;
            
            setTimeout(() => {
                form.style.display = 'none';
            }, 300);
        }
        
        if (document.body) {
            document.body.style.overflow = '';
        }

        console.log('🗑️ Delete confirmation hidden');
    }
};

// ===== ENHANCED DELETE FORM HANDLERS =====
function setupDeleteFormHandlers() {
        
    const form = Utils.safeGetElement('deleteClusterForm', 'setupDeleteFormHandlers');
    const checkbox = Utils.safeGetElement('confirmDelete', 'setupDeleteFormHandlers');
    const submitBtn = Utils.safeGetElement('confirmDeleteBtn', 'setupDeleteFormHandlers');
    
    if (!form) {
        console.warn('⚠️ Delete form not found - handlers not initialized');
        return;
    }

    // ✅ ENHANCED: Checkbox change handler with validation
    if (checkbox && submitBtn) {
        checkbox.addEventListener('change', () => {
            submitBtn.disabled = !checkbox.checked;
            
            if (checkbox.checked) {
                submitBtn.focus();
            }
        });
    }

    // ✅ ENHANCED: Form submit handler with comprehensive error handling
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const currentCheckbox = Utils.safeGetElement('confirmDelete', 'form submit');
        const currentSubmitBtn = Utils.safeGetElement('confirmDeleteBtn', 'form submit');
        const clusterIdInput = Utils.safeGetElement('deleteClusterId', 'form submit');
        const clusterNameEl = Utils.safeGetElement('deleteClusterName', 'form submit');
        
        if (!currentCheckbox || !currentSubmitBtn || !clusterIdInput) {
            console.error('❌ Required form elements missing during submission');
            NotificationManager.show(
                'Form Error',
                'Form elements are missing. Please refresh the page and try again.',
                'error'
            );
            return;
        }
        
        if (!currentCheckbox.checked) {
            // Highlight the checkbox and its container
            const checkboxContainer = currentCheckbox.closest('.confirmation-checkbox');
            if (checkboxContainer) {
                checkboxContainer.classList.add('error');
                checkboxContainer.style.border = '2px solid #ef4444';
                checkboxContainer.style.borderRadius = '8px';
                checkboxContainer.style.padding = '12px';
                checkboxContainer.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                checkboxContainer.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
                
                // Also highlight the checkbox itself
                const checkmark = checkboxContainer.querySelector('.checkmark');
                if (checkmark) {
                    checkmark.style.border = '2px solid #ef4444';
                    checkmark.style.backgroundColor = '#fef2f2';
                }
                
                // Remove highlight after 3 seconds
                setTimeout(() => {
                    checkboxContainer.classList.remove('error');
                    checkboxContainer.style.border = '';
                    checkboxContainer.style.backgroundColor = '';
                    checkboxContainer.style.padding = '';
                    checkboxContainer.style.boxShadow = '';
                    
                    if (checkmark) {
                        checkmark.style.border = '';
                        checkmark.style.backgroundColor = '';
                    }
                }, 3000);
            }
            
            // Focus on the checkbox
            currentCheckbox.focus();
            
            NotificationManager.show(
                'Confirmation Required',
                'Please confirm that you understand this action cannot be undone',
                'warning'
            );
            return;
        }

        const clusterId = clusterIdInput.value.trim();
        const clusterName = clusterNameEl ? 
            (clusterNameEl.textContent || clusterNameEl.innerText || 'Unknown Cluster') : 
            'Unknown Cluster';
        
        if (!clusterId) {
            console.error('❌ No cluster ID provided for deletion');
            NotificationManager.show(
                'Invalid Request',
                'No cluster ID specified for deletion',
                'error'
            );
            return;
        }

        // ✅ ENHANCED: Show loading state and progress
        LoadingManager.button(currentSubmitBtn, true);
        LoadingManager.show(`Deleting ${clusterName}...`);

        try {
            const response = await fetch(`/cluster/${clusterId}/remove`, {
                method: 'DELETE',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                LoadingManager.hide();
                DeleteFormManager.hide();
                
                NotificationManager.show(
                    'Cluster Deleted!', 
                    `"${clusterName}" has been permanently removed from your portfolio`, 
                    'success'
                );
                
                // ✅ ENHANCED: Smooth card removal with animation
                const clusterCard = document.querySelector(`[data-cluster-id="${clusterId}"]`);
                if (clusterCard) {
                    clusterCard.style.transition = 'all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
                    clusterCard.style.transform = 'scale(0.95) translateY(-10px)';
                    clusterCard.style.opacity = '0';
                    
                    setTimeout(() => {
                        const cardToRemove = document.querySelector(`[data-cluster-id="${clusterId}"]`);
                        if (cardToRemove && cardToRemove.parentNode) {
                            cardToRemove.remove();
                        }
                        
                        // Check if portfolio is now empty
                        const remainingCards = document.querySelectorAll('.cluster-card');
                        if (remainingCards.length === 0) {
                            setTimeout(() => {
                                LoadingManager.show('Refreshing portfolio...');
                                setTimeout(() => {
                                    if (window?.location?.reload) {
                                        window.location.reload();
                                    }
                                }, 800);
                            }, 1500);
                        }
                    }, 400);
                } else {
                    // We're on a detail page - redirect to portfolio
                    setTimeout(() => {
                        LoadingManager.show('Redirecting to portfolio...');
                        setTimeout(() => {
                            if (window && window.location) {
                                window.location.href = '/';
                            }
                        }, 800);
                    }, 1500);
                }
            } else {
                throw new Error(data.message || 'Delete operation failed');
            }
        } catch (error) {
            console.error('❌ Delete operation failed:', error);
            
            LoadingManager.hide();
            LoadingManager.button(currentSubmitBtn, false);
            
            NotificationManager.show(
                'Delete Failed', 
                'Failed to delete cluster: ' + error.message, 
                'error',
                8000
            );
        }
    });
    
    }

function hideDeleteForm() {
    DeleteFormManager.hide();
}

// ===== ENHANCED NOTIFICATION MANAGEMENT =====
const NotificationManager = {
    show(title, message, type = 'info', duration = 4000) {
        const container = Utils.safeGetElement('notificationContainer', 'NotificationManager.show');
        if (!container) {
            console.warn('⚠️ Notification container not found, using console log');
            console.log(`${type.toUpperCase()}: ${title} - ${message}`);
            return null;
        }
        
        const id = Utils.generateId();
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.setAttribute('data-id', id);
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'polite');
        
        const iconMap = {
            success: 'fas fa-check',
            warning: 'fas fa-exclamation-triangle',
            error: 'fas fa-times',
            info: 'fas fa-info'
        };
        
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="${iconMap[type]}"></i>
            </div>
            <div class="notification-content">
                <div class="notification-title">${Utils.escapeHtml(title)}</div>
                <div class="notification-message">${Utils.escapeHtml(message)}</div>
            </div>
            <button class="notification-close" onclick="NotificationManager.remove('${id}')" aria-label="Close notification">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(notification);
        AppState.notifications.set(id, notification);
        
        // ✅ ENHANCED: Smooth entrance animation
        setTimeout(() => notification.classList.add('show'), 50);
        
        // ✅ ENHANCED: Auto remove with hover pause
        if (duration > 0) {
            let timeoutId = setTimeout(() => this.remove(id), duration);
            
            // Pause auto-removal on hover
            notification.addEventListener('mouseenter', () => {
                clearTimeout(timeoutId);
            });
            
            notification.addEventListener('mouseleave', () => {
                timeoutId = setTimeout(() => this.remove(id), 2000);
            });
        }
        
        return id;
    },
    
    remove(id) {
        const notification = AppState.notifications.get(id);
        if (notification) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
                AppState.notifications.delete(id);
            }, 300);
        }
    },


};

// ===== ENHANCED MODAL MANAGEMENT =====
const ModalManager = {
    open() {
        const overlay = Utils.safeGetElement('modalOverlay', 'ModalManager.open');
        if (overlay) {
            overlay.classList.add('show');
            overlay.removeAttribute('aria-hidden');
            AppState.currentModal = 'add';
        }
        
        if (document.body) {
            document.body.style.overflow = 'hidden';
        }
        
        // ✅ ENHANCED: Load subscriptions and focus management
        loadSubscriptionsForDropdown();
        
        setTimeout(() => {
            const clusterNameField = Utils.safeGetElement('clusterName', 'ModalManager.open focus');
            if (clusterNameField) {
                clusterNameField.focus();
            }
        }, 200);

    },

    close(event = null) {
        if (event && event.target !== Utils.safeGetElement('modalOverlay', 'ModalManager.close')) {
            return;
        }
        
        const overlay = Utils.safeGetElement('modalOverlay', 'ModalManager.close');
        if (overlay) {
            overlay.classList.remove('show');
            // Remove aria-hidden entirely when modal is closed
            overlay.removeAttribute('aria-hidden');
            AppState.currentModal = null;
        }
        
        if (document.body) {
            document.body.style.overflow = '';
        }
        
        // Move focus back to the trigger element
        const addButton = document.querySelector('.add-btn');
        if (addButton) {
            addButton.focus();
        }
        
        this.resetForm();
    },

    resetForm() {
        const form = Utils.safeGetElement('clusterForm', 'ModalManager.resetForm');
        if (form) {
            form.reset();
        }
        
        // ✅ ENHANCED: Reset all form states
        const autoAnalyze = Utils.safeGetElement('autoAnalyze', 'ModalManager.resetForm');
        if (autoAnalyze) {
            autoAnalyze.checked = true;
        }
        
        const validationStatus = Utils.safeGetElement('validationStatus', 'ModalManager.resetForm');
        if (validationStatus) {
            validationStatus.style.display = 'none';
            validationStatus.classList.remove('error');
        }
        
        // Clear validation errors
        document.querySelectorAll('.field-error').forEach(el => {
            if (el) el.textContent = '';
        });
        document.querySelectorAll('.error').forEach(el => {
            if (el) el.classList.remove('error');
        });

        // Reset character count
        const charCount = Utils.safeGetElement('charCount', 'ModalManager.resetForm');
        if (charCount) {
            charCount.textContent = '0';
        }
    }
};

// ===== ENHANCED COUNTER ANIMATION =====
const CounterManager = {
    animate() {
        const counters = document.querySelectorAll('.metric-value[data-target]');
        counters.forEach(counter => {
            const target = parseFloat(counter.getAttribute('data-target'));
            // ✅  Proper string formatting for includes()
            const isDollar = counter.textContent.includes('$'); 
            const isPercent = counter.textContent.includes('%');
            
            this.animateValue(counter, 0, target, 1800, isDollar, isPercent);
        });
    },

    animateValue(element, start, end, duration, isDollar, isPercent) {
        if (!element) return;
        
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // ✅ ENHANCED: Smooth easing with cubic bezier
            const eased = progress < 0.5 
                ? 4 * progress * progress * progress 
                : 1 - Math.pow(-2 * progress + 2, 3) / 2;
            
            const current = start + (end - start) * eased;
            
            let value = Math.round(current);
            if (isPercent) {
                value = current.toFixed(1); // Keep decimal for percentages
            }
            
            // ✅  Correct dollar sign formatting
            element.textContent = (isDollar ? '$' : '') + value + (isPercent ? '%' : '');
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
};


// ===== ENHANCED VIEW MANAGEMENT =====
const ViewManager = {
    init() {
        const buttons = document.querySelectorAll('.view-btn');
        buttons.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => this.toggle(btn));
            }
        });
    },

    toggle(button) {
        if (!button) return;
        
        document.querySelectorAll('.view-btn').forEach(btn => {
            if (btn) btn.classList.remove('active');
        });
        button.classList.add('active');
        
        const view = button.getAttribute('data-view');
        const container = document.querySelector('.clusters-grid');
        
        if (!container) return;
        
        // ✅ ENHANCED: Smooth view transitions
        container.style.transition = 'grid-template-columns 0.3s ease';
        
        if (view === 'list') {
            container.style.gridTemplateColumns = '1fr';
        } else {
            container.style.gridTemplateColumns = 'repeat(auto-fill, minmax(280px, 1fr))';
        }

        console.log(`👀 View switched to: ${view}`);
    }
};

// ===== ENHANCED CLUSTER MANAGEMENT =====
const ClusterManager = {
    // ✅ NEW: Enhanced subscription validation
    async validateSubscriptionAccess() {
        const subscriptionId = Utils.withElement('subscriptionSelect', el => el.value);
        const resourceGroup = Utils.withElement('resourceGroup', el => el.value.trim());
        const clusterName = Utils.withElement('clusterName', el => el.value.trim());
        
        if (!subscriptionId || !resourceGroup || !clusterName) {
            return;
        }
        
        const validationStatus = Utils.safeGetElement('validationStatus', 'validateSubscriptionAccess');
        if (!validationStatus) return;
        
        const validationText = validationStatus.querySelector('.validation-text');
        const validationIcon = validationStatus.querySelector('.validation-icon i');
        
        validationStatus.style.display = 'flex';
        validationStatus.classList.remove('error');
        if (validationText) {
            validationText.textContent = 'Validating cluster access in subscription...';
        }
        if (validationIcon) {
            validationIcon.className = 'fas fa-spinner fa-spin';
        }
        
        try {
            const response = await fetch(`/api/subscriptions/${subscriptionId}/validate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    resource_group: resourceGroup,
                    cluster_name: clusterName
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.status === 'success' && result.validation_result?.valid) {
                validationStatus.classList.remove('error');
                if (validationText) {
                    validationText.textContent = '✅ Cluster access validated successfully';
                }
                if (validationIcon) {
                    validationIcon.className = 'fas fa-check-circle';
                }
                
                setTimeout(() => {
                    validationStatus.style.display = 'none';
                }, 3000);
            } else {
                validationStatus.classList.add('error');
                if (validationText) {
                    validationText.textContent = `❌ Validation failed: ${result.validation_result?.error || 'Unknown error'}`;
                }
                if (validationIcon) {
                    validationIcon.className = 'fas fa-exclamation-triangle';
                }
            }
            
        } catch (error) {
            validationStatus.classList.add('error');
            if (validationText) {
                validationText.textContent = 'Validation error: ' + error.message;
            }
            if (validationIcon) {
                validationIcon.className = 'fas fa-exclamation-triangle';
            }
        }
    },

    async add() {
        if (!validateForm()) {
            return;
        }

        // Collect form data
        const formData = {
            cluster_name: Utils.withElement('clusterName', el => el.value.trim()) || '',
            resource_group: Utils.withElement('resourceGroup', el => el.value.trim()) || '',
            subscription_id: Utils.withElement('subscriptionSelect', el => el.value) || '',
            environment: Utils.withElement('environment', el => el.value) || 'development',
            region: Utils.withElement('region', el => el.value.trim()) || '',
            description: Utils.withElement('description', el => el.value.trim()) || '',
            // Original checkbox-based approach (commented out)
            // auto_analyze: Utils.withElement('autoAnalyze', el => el.checked) || false,
            // enable_monitoring: Utils.withElement('enableMonitoring', el => el.checked) || false
            
            // New approach: Always auto-analyze new clusters
            auto_analyze: true, // Always start analysis automatically after adding cluster
            enable_monitoring: false // Default monitoring to false
        };

        const button = Utils.safeGetElement('addClusterBtn', 'ClusterManager.add');
        if (button) LoadingManager.button(button, true);
                        LoadingManager.show('Adding "' + formData.cluster_name + '" to subscription...');

        try {
            const response = await fetch('/api/clusters', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.status === 'success' || result.success) {
                LoadingManager.hide();
                NotificationManager.show(
                    'Cluster Added Successfully!', 
                    '"' + formData.cluster_name + '" is now part of your portfolio' + (formData.auto_analyze ? ' and analysis will begin shortly' : ''), 
                    'success',
                    6000
                );
                
                ModalManager.close();
                
                setTimeout(() => {
                    LoadingManager.show('Refreshing portfolio...');
                    setTimeout(() => {
                        if (window && window.location && window.location.reload) {
                            window.location.reload();
                        }
                    }, 800);
                }, 1500);
            } else {
                throw new Error(result.message || 'Failed to add cluster');
            }
        } catch (error) {
            console.error('❌ Add cluster failed:', error);
            LoadingManager.hide();
            NotificationManager.show(
                'Failed to Add Cluster', 
                'Error: ' + error.message, 
                'error',
                8000
            );
        } finally {
            if (button) LoadingManager.button(button, false);
        }
    },

    async analyze(clusterId) {
        if (AppState.analyzingClusters.has(clusterId)) {
            NotificationManager.show(
                'Analysis In Progress', 
                'This cluster is currently being analyzed. Please wait for completion.', 
                'warning'
            );
            return;
        }

        // ✅ ENHANCED: Get cluster context for better UX
        const clusterCard = document.querySelector(`[data-cluster-id="${clusterId}"]`);
        const clusterName = clusterCard?.querySelector('.cluster-name')?.textContent?.trim() || 'cluster';

        console.log(`🚀 Starting analysis for cluster: ${clusterName} (ID: ${clusterId})`);

        // ✅  Set analyzing state IMMEDIATELY
        AnalysisStateManager.setAnalyzing(clusterId, true);
        
        // ✅  Show loading after a brief delay to let UI update
        setTimeout(() => {
            LoadingManager.show(`Analyzing "${clusterName}"...`);
        }, 100);
        
        try {
            const response = await fetch(`/api/clusters/${clusterId}/analyze`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ 
                    days: 30, 
                    enable_pod_analysis: true,
                    enable_optimization_recommendations: true
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                console.log(`✅ Analysis completed successfully for ${clusterName}`);
                
                // ✅  Complete the analysis state FIRST
                AnalysisStateManager.setAnalyzing(clusterId, false);
                LoadingManager.hide();
                
                // ✅ ENHANCED: Show completion notification
                // NotificationManager.show(
                //     'Analysis Complete!', 
                //     `"${clusterName}" analysis finished successfully. Click to view results.`, 
                //     'success',
                //     5000
                // );
                
                // ✅  Add click handler to redirect to results instead of auto-redirect
                const clusterCardElement = document.querySelector(`[data-cluster-id="${clusterId}"]`);
                if (clusterCardElement) {
                    // Add a visual indicator that results are ready
                    clusterCardElement.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.3)';
                    clusterCardElement.style.borderColor = '#10b981';
                    
                    // Update the onclick to go to results
                    clusterCardElement.onclick = () => {
                        LoadingManager.show('Loading analysis results...');
                        setTimeout(() => {
                            if (window?.location) {
                                window.location.href = `/cluster/${clusterId}`;
                            }
                        }, 500);
                    };
                    
                    // Add a "View Results" button or update existing analyze button
                    const analyzeBtn = clusterCardElement.querySelector('.analyze-btn');
                    if (analyzeBtn) {
                        const playIcon = analyzeBtn.querySelector('.fa-play');
                        if (playIcon) {
                            playIcon.className = 'fas fa-eye';
                            analyzeBtn.setAttribute('title', 'View Results');
                            analyzeBtn.onclick = (e) => {
                                e.stopPropagation();
                                LoadingManager.show('Loading analysis results...');
                                setTimeout(() => {
                                    if (window?.location) {
                                        window.location.href = `/cluster/${clusterId}`;
                                    }
                                }, 500);
                            };
                        }
                    }
                }
                
                // ✅ OPTIONAL: Auto-redirect after a delay (user choice)
                // setTimeout(() => {
                //     LoadingManager.show('Loading analysis results...');
                //     setTimeout(() => {
                //         if (window?.location) {
                //             window.location.href = `/cluster/${clusterId}`;
                //         }
                //     }, 800);
                // }, 3000); // 3 second delay
                
            } else {
                throw new Error(data.message || 'Analysis failed');
            }
        } catch (error) {
            console.error('❌ Analysis failed:', error);
            
            // ✅  Reset state on error
            AnalysisStateManager.setAnalyzing(clusterId, false);
            LoadingManager.hide();
            
            NotificationManager.show(
                'Analysis Failed', 
                `Failed to analyze "${clusterName}": ${error.message}`, 
                'error',
                8000
            );
        }
    },

    delete(clusterId) {
        // ✅ ENHANCED: Collect cluster information with better fallbacks
        let clusterCard = document.querySelector(`[data-cluster-id="${clusterId}"]`);
        let clusterName = 'Unknown Cluster';
        let resourceGroup = 'Unknown Resource Group';

        if (clusterCard) {
            const nameElement = clusterCard.querySelector('.cluster-name');
            clusterName = nameElement?.textContent?.trim() || 'Unknown Cluster';
            
            const infoItems = clusterCard.querySelectorAll('.info-item');
            for (let item of infoItems) {
                if (item.querySelector('.fa-cube')) {
                    resourceGroup = item.textContent.trim() || 'Unknown Resource Group';
                    break;
                }
            }
        } else {
            // Fallback for detail pages
            const titleElement = document.querySelector('h1, .cluster-title, .page-title');
            if (titleElement) {
                clusterName = titleElement.textContent.trim();
            }
            
            const resourceGroupElement = document.querySelector('[data-resource-group], .resource-group');
            if (resourceGroupElement) {
                resourceGroup = resourceGroupElement.textContent.trim();
            }
        }

        DeleteFormManager.show(clusterId, clusterName, resourceGroup);
    },

    select(clusterId) {
        const clusterCard = document.querySelector(`[data-cluster-id="${clusterId}"]`);
        const clusterName = clusterCard?.querySelector('.cluster-name')?.textContent || 'cluster';
        
        LoadingManager.show('Loading "' + clusterName + '" details...');
        
        setTimeout(() => {
            if (window && window.location) {
                window.location.href = '/cluster/' + clusterId;
            }
        }, 800);
    }
};

// ===== ENHANCED CHARACTER COUNTER =====
function setupCharacterCounter() {
    const description = Utils.safeGetElement('description', 'setupCharacterCounter');
    const charCount = Utils.safeGetElement('charCount', 'setupCharacterCounter');
    
    if (description && charCount) {
        description.addEventListener('input', () => {
            const count = description.value.length;
            charCount.textContent = count;
            
            // Visual feedback for character limit
            if (count > 450) {
                charCount.style.color = '#ef4444';
            } else if (count > 400) {
                charCount.style.color = '#48bb78';
            } else {
                charCount.style.color = '#6b7280';
            }
        });
    }
}

// ===== GLOBAL FUNCTIONS =====
function openModal() {
    ModalManager.open();
}

function closeModal(event) {
    ModalManager.close(event);
}

function addCluster() {
    ClusterManager.add();
}

// Global functions for HTML onclick handlers
function selectCluster(clusterId) {
    ClusterManager.select(clusterId);
}

function analyzeCluster(clusterId) {
    ClusterManager.analyze(clusterId);
}

function deleteCluster(clusterId) {
    DeleteFormManager.show(clusterId);
}

function closeModal(event) {
    ModalManager.close(event);
}

function addCluster() {
    ClusterManager.add();
}

// Ensure functions are available globally
window.selectCluster = selectCluster;
window.analyzeCluster = analyzeCluster;
window.deleteCluster = deleteCluster;
window.closeModal = closeModal;
window.addCluster = addCluster;

// ===== ENHANCED EVENT LISTENERS =====
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        if (AppState.currentModal === 'delete') {
            DeleteFormManager.hide();
        } else if (AppState.currentModal === 'add') {
            ModalManager.close();
        }
    }
    
    // ✅ NEW: Keyboard shortcuts
    if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
            case 'k':
                e.preventDefault();
                if (!AppState.currentModal) {
                    openModal();
                }
                break;
            case 'r':
                if (AppState.currentModal) {
                    e.preventDefault();
                    if (AppState.currentModal === 'add') {
                        ModalManager.resetForm();
                    }
                }
                break;
        }
    }
});

// ===== ENHANCED INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌐 Enhanced Multi-Subscription AKS Dashboard Loading...');
    
    // ✅ ENHANCED: Initialize with comprehensive error handling
    const initTasks = [
        { name: 'ViewManager', fn: () => ViewManager.init() },
        { name: 'Delete Form Handlers', fn: () => setupDeleteFormHandlers() },
        { name: 'Character Counter', fn: () => setupCharacterCounter() }
    ];
    
    initTasks.forEach(task => {
        try {
            task.fn();
            console.log(`✅ ${task.name} initialized successfully`);
        } catch (error) {
            console.error(`❌ ${task.name} initialization failed:`, error);
        }
    });
    
    // Add form submit handler to prevent any form submission
    const clusterForm = Utils.safeGetElement('clusterForm', 'DOMContentLoaded');
    if (clusterForm) {
        clusterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            e.stopPropagation();
            return false;
        });
    }
    
    // Add button click handler
    const addClusterBtn = Utils.safeGetElement('addClusterBtn', 'DOMContentLoaded');
    if (addClusterBtn) {
        addClusterBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            addCluster();
        });
    }
    
    // Add subscription validation listeners with debouncing
    const subscriptionSelect = Utils.safeGetElement('subscriptionSelect', 'DOMContentLoaded');
    const resourceGroup = Utils.safeGetElement('resourceGroup', 'DOMContentLoaded');
    const clusterName = Utils.safeGetElement('clusterName', 'DOMContentLoaded');
    
    if (subscriptionSelect && resourceGroup && clusterName) {
        const validateOnChange = Utils.debounce(() => {
            if (subscriptionSelect.value && resourceGroup.value.trim() && clusterName.value.trim()) {
                ClusterManager.validateSubscriptionAccess();
            }
        }, 1500);
        
        subscriptionSelect.addEventListener('change', validateOnChange);
        resourceGroup.addEventListener('input', validateOnChange);
        clusterName.addEventListener('input', validateOnChange);
        
    }
    
    // ✅ ENHANCED: Counter animation with staggered start
    setTimeout(() => {
        try {
            CounterManager.animate();
                    } catch (error) {
            console.error('❌ Counter animation failed:', error);
        }
    }, 500);
    
    // ✅ ENHANCED: Welcome notification with better messaging
    // {% if clusters|length == 0 %}
    // setTimeout(() => {
    //     try {
    //         NotificationManager.show(
    //             'Welcome to AKS Cost Intelligence!', 
    //             'Connect your first cluster from any Azure subscription to start optimizing costs. Use Ctrl+K to quickly add a cluster.', 
    //             'info',
    //             8000
    //         );
    //     } catch (error) {
    //         console.error('❌ Welcome notification failed:', error);
    //     }
    // }, 1200);
    // {% endif %}
    
    // ✅ NEW: Debug mode detection
    AppState.debugMode = window.location.search.includes('debug=true');
    if (AppState.debugMode) {
        console.log('🐛 Debug mode enabled');
    }
    
    console.log('✨ Enhanced multi-subscription dashboard fully loaded!');
});

// ===== ENHANCED PERFORMANCE OPTIMIZATIONS =====
if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    if (document.documentElement?.style) {
        document.documentElement.style.setProperty('--transition', '0.01ms');
        document.documentElement.style.setProperty('--transition-slow', '0.01ms');
        console.log('♿ Reduced motion preferences applied');
    }
}

// ===== ENHANCED DEBUG UTILITIES =====
window.AKSDebug = {
    checkElements() {
        const elements = [
            'deleteClusterForm', 'deleteConfirmationForm', 'confirmDelete', 
            'confirmDeleteBtn', 'deleteClusterId', 'deleteClusterName', 'deleteResourceGroup',
            'clusterForm', 'modalOverlay', 'subscriptionSelect', 'clusterName', 'resourceGroup',
            'loadingToast', 'notificationContainer', 'validationStatus'
        ];
        
        console.log('🔍 Enhanced Element Check:');
        const results = {};
        elements.forEach(id => {
            const el = document.getElementById(id);
            const exists = !!el;
            results[id] = exists;
            console.log(`  ${id}: ${exists ? '✅' : '❌'}`);
        });
        return results;
    },
    
    state: AppState,
    managers: { 
        LoadingManager, 
        NotificationManager, 
        ModalManager, 
        DeleteFormManager,
        AnalysisStateManager,
        ClusterManager,
        CounterManager,
        ViewManager
    },
    
    // ✅ NEW: Test functions
    // testNotification: function(type) {
    //     type = type || 'info';
    //     return NotificationManager.show(
    //         'Test Notification',
    //         'This is a test ' + type + ' notification',
    //         type,
    //         3000
    //     );
    // },
    
    simulateAnalysis: function(clusterId) {
        clusterId = clusterId || 'test-cluster';
        AnalysisStateManager.setAnalyzing(clusterId, true);
        setTimeout(function() {
            AnalysisStateManager.setAnalyzing(clusterId, false);
        }, 3000);
    },
    
    getPerformanceMetrics: function() {
        if (performance.getEntriesByType) {
            var navigation = performance.getEntriesByType('navigation')[0];
            var paint = performance.getEntriesByType('paint');
            
            return {
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                firstPaint: paint.find(function(p) { return p.name === 'first-paint'; }) ? paint.find(function(p) { return p.name === 'first-paint'; }).startTime : null,
                firstContentfulPaint: paint.find(function(p) { return p.name === 'first-contentful-paint'; }) ? paint.find(function(p) { return p.name === 'first-contentful-paint'; }).startTime : null,
                totalLoadTime: navigation.loadEventEnd - navigation.navigationStart
            };
        }
        return null;
    }
};

console.log('  - window.AKSDebug.checkElements() - Check all form elements');
console.log('  - window.AKSDebug.testNotification(type) - Test notifications');
console.log('  - window.AKSDebug.simulateAnalysis(id) - Test analysis states');
console.log('  - window.AKSDebug.getPerformanceMetrics() - View load performance');
console.log('  - Add ?debug=true to URL for enhanced logging');
