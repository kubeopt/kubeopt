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
            console.log(`⚠️ Element '${id}' not found in context: ${context}`);
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
        // Skip loading indicators during silent refresh to prevent flicker
        if (window.GlobalRefreshManager && window.GlobalRefreshManager.isRefreshing) {
            console.log('🔇 Skipping LoadingManager.show during silent refresh');
            return;
        }
        
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
            console.log('⚠️ LoadingManager.button: button element is null');
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
                option.textContent = `${sub.display_name} ([Protected])`;
                if (sub.is_default) {
                    option.selected = true;
                }
                subscriptionSelect.appendChild(option);
            });
            
            AppState.subscriptions = data.subscriptions;
            
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
            console.log(`⚠️ AnalysisStateManager: Cluster card not found for ID: ${clusterId}`);
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
        // Apply essential positioning and centering while preserving CSS styles
        form.style.display = 'flex';
        form.style.position = 'fixed';
        form.style.top = '0';
        form.style.left = '0';
        form.style.width = '100%';
        form.style.height = '100%';
        form.style.alignItems = 'center';
        form.style.justifyContent = 'center';
        form.style.background = 'rgba(0, 0, 0, 0.6)';  // Dark backdrop
        form.style.zIndex = '10000';
        
        // Properly set aria attributes for accessibility
        form.setAttribute('aria-hidden', 'false');
        form.setAttribute('aria-modal', 'true');
        AppState.currentModal = 'delete';
        
        // Add click outside to close functionality
        form.addEventListener('click', (e) => {
            // Close modal if clicking on the backdrop (not the modal content)
            if (e.target === form) {
                DeleteFormManager.hide();
            }
        });
        
        setTimeout(() => {
            form.classList.remove('hidden');
            form.classList.add('show');
            
            // Apply dark theme styled modal
            const formContent = form.querySelector('.delete-form-content');
            if (formContent) {
                // Dark theme modal styling
                formContent.style.background = 'linear-gradient(145deg, #1f2937, #111827)';
                formContent.style.borderRadius = '24px';
                formContent.style.padding = '36px';
                formContent.style.maxWidth = '500px';
                formContent.style.width = '92%';
                formContent.style.boxShadow = '0 32px 64px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(75, 85, 99, 0.3)';
                formContent.style.transform = 'scale(1) translateY(0)';
                formContent.style.transition = 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
                formContent.style.border = '1px solid rgba(75, 85, 99, 0.4)';
                
                // Enhanced header styling
                const header = formContent.querySelector('.delete-form-header');
                if (header) {
                    header.style.display = 'flex';
                    header.style.alignItems = 'flex-start';
                    header.style.gap = '24px';
                    header.style.marginBottom = '28px';
                }
                
                // Better delete icon - trash can instead of triangle
                const iconWrapper = formContent.querySelector('.delete-icon-wrapper');
                if (iconWrapper) {
                    iconWrapper.style.width = '64px';
                    iconWrapper.style.height = '64px';
                    iconWrapper.style.borderRadius = '16px';
                    iconWrapper.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
                    iconWrapper.style.display = 'flex';
                    iconWrapper.style.alignItems = 'center';
                    iconWrapper.style.justifyContent = 'center';
                    iconWrapper.style.fontSize = '24px';
                    iconWrapper.style.color = 'white';
                    iconWrapper.style.boxShadow = '0 8px 32px rgba(239, 68, 68, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)';
                    
                    // Change icon to trash can
                    const icon = iconWrapper.querySelector('i');
                    if (icon) {
                        icon.className = 'fas fa-trash-alt';
                    }
                }
                
                // Dark theme title styling
                const title = formContent.querySelector('#deleteTitle');
                if (title) {
                    title.style.color = '#f9fafb';
                    title.style.fontSize = '24px';
                    title.style.fontWeight = '700';
                    title.style.marginBottom = '8px';
                    title.style.letterSpacing = '-0.025em';
                }
                
                // Dark theme description text
                const description = formContent.querySelector('.delete-form-info p');
                if (description) {
                    description.style.color = '#d1d5db';
                    description.style.fontSize = '16px';
                    description.style.lineHeight = '1.6';
                    description.style.margin = '0';
                }
                
                // Dark theme form details
                const details = formContent.querySelector('.delete-form-details');
                if (details) {
                    details.style.background = 'linear-gradient(145deg, #374151, #2d3748)';
                    details.style.borderRadius = '16px';
                    details.style.padding = '24px';
                    details.style.marginBottom = '28px';
                    details.style.border = '1px solid rgba(75, 85, 99, 0.4)';
                    details.style.boxShadow = 'inset 0 1px 3px rgba(0, 0, 0, 0.2)';
                    
                    // Style detail items for dark theme
                    const detailItems = details.querySelectorAll('.detail-item');
                    detailItems.forEach(item => {
                        item.style.display = 'flex';
                        item.style.justifyContent = 'space-between';
                        item.style.alignItems = 'center';
                        item.style.marginBottom = '12px';
                        
                        const label = item.querySelector('.detail-label');
                        const value = item.querySelector('.detail-value');
                        
                        if (label) {
                            label.style.fontWeight = '600';
                            label.style.color = '#e5e7eb';
                            label.style.fontSize = '14px';
                        }
                        
                        if (value) {
                            value.style.fontWeight = '500';
                            value.style.color = '#f9fafb';
                            value.style.fontSize = '14px';
                            value.style.fontFamily = 'monospace';
                            value.style.background = 'rgba(55, 65, 81, 0.8)';
                            value.style.padding = '4px 8px';
                            value.style.borderRadius = '6px';
                            value.style.border = '1px solid rgba(75, 85, 99, 0.4)';
                        }
                    });
                }
                
                // Fix checkbox styling and functionality
                const checkboxContainer = formContent.querySelector('.confirmation-checkbox');
                if (checkboxContainer) {
                    checkboxContainer.style.marginBottom = '32px';
                    checkboxContainer.style.display = 'flex';
                    checkboxContainer.style.alignItems = 'center';
                    checkboxContainer.style.gap = '12px';
                    checkboxContainer.style.padding = '16px';
                    checkboxContainer.style.background = 'rgba(251, 191, 36, 0.1)';
                    checkboxContainer.style.borderRadius = '12px';
                    checkboxContainer.style.border = '1px solid rgba(251, 191, 36, 0.3)';
                    checkboxContainer.style.color = '#f9fafb';
                    
                    // Style the checkbox properly
                    const checkbox = checkboxContainer.querySelector('input[type="checkbox"]');
                    const checkmark = checkboxContainer.querySelector('.checkmark');
                    const label = checkboxContainer.querySelector('.checkbox');
                    
                    if (checkbox && checkmark) {
                        // Hide default checkbox
                        checkbox.style.display = 'none';
                        
                        // Style custom checkmark
                        checkmark.style.display = 'flex';
                        checkmark.style.alignItems = 'center';
                        checkmark.style.justifyContent = 'center';
                        checkmark.style.width = '20px';
                        checkmark.style.height = '20px';
                        checkmark.style.borderRadius = '4px';
                        checkmark.style.border = '2px solid #6b7280';
                        checkmark.style.background = 'transparent';
                        checkmark.style.transition = 'all 0.2s ease';
                        checkmark.style.cursor = 'pointer';
                        
                        // Hide checkmark initially
                        const checkIcon = checkmark.querySelector('i');
                        if (checkIcon) {
                            checkIcon.style.color = 'white';
                            checkIcon.style.fontSize = '12px';
                            checkIcon.style.opacity = '0';
                            checkIcon.style.transition = 'opacity 0.2s ease';
                        }
                        
                        // Remove any existing event listeners and add fresh ones
                        if (label) {
                            label.style.cursor = 'pointer';
                            
                            // Remove existing event listener if present
                            if (label._checkboxClickHandler) {
                                label.removeEventListener('click', label._checkboxClickHandler);
                            }
                            
                            // Create new event handler
                            label._checkboxClickHandler = (e) => {
                                e.preventDefault();
                                checkbox.checked = !checkbox.checked;
                                
                                console.log('📋 Checkbox toggled:', checkbox.checked);
                                
                                if (checkbox.checked) {
                                    checkmark.style.background = '#10b981';
                                    checkmark.style.borderColor = '#10b981';
                                    if (checkIcon) checkIcon.style.opacity = '1';
                                } else {
                                    checkmark.style.background = 'transparent';
                                    checkmark.style.borderColor = '#6b7280';
                                    if (checkIcon) checkIcon.style.opacity = '0';
                                }
                                
                                // Enable/disable delete button
                                const deleteBtn = formContent.querySelector('.btn:not(.secondary)');
                                if (deleteBtn) {
                                    deleteBtn.disabled = !checkbox.checked;
                                    if (checkbox.checked) {
                                        deleteBtn.style.opacity = '1';
                                        deleteBtn.style.cursor = 'pointer';
                                    } else {
                                        deleteBtn.style.opacity = '0.5';
                                        deleteBtn.style.cursor = 'not-allowed';
                                    }
                                }
                            };
                            
                            // Add the new event listener
                            label.addEventListener('click', label._checkboxClickHandler);
                        }
                    }
                }
                
                // Dark theme button styling
                const buttonContainer = formContent.querySelector('.delete-form-actions');
                if (buttonContainer) {
                    buttonContainer.style.display = 'flex';
                    buttonContainer.style.gap = '16px';
                    buttonContainer.style.justifyContent = 'flex-end';
                }
                
                const buttons = formContent.querySelectorAll('.btn');
                buttons.forEach(btn => {
                    btn.style.padding = '14px 28px';
                    btn.style.borderRadius = '14px';
                    btn.style.fontWeight = '600';
                    btn.style.fontSize = '15px';
                    btn.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                    btn.style.border = 'none';
                    btn.style.cursor = 'pointer';
                    btn.style.position = 'relative';
                    btn.style.overflow = 'hidden';
                    
                    if (btn.classList.contains('secondary')) {
                        btn.style.background = 'linear-gradient(145deg, #4b5563, #374151)';
                        btn.style.color = '#e5e7eb';
                        btn.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)';
                        
                        btn.addEventListener('mouseover', () => {
                            btn.style.background = 'linear-gradient(145deg, #374151, #2d3748)';
                            btn.style.transform = 'translateY(-2px)';
                            btn.style.boxShadow = '0 8px 20px rgba(0, 0, 0, 0.3)';
                        });
                        
                        btn.addEventListener('mouseout', () => {
                            btn.style.background = 'linear-gradient(145deg, #4b5563, #374151)';
                            btn.style.transform = 'translateY(0)';
                            btn.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
                        });
                    } else {
                        btn.style.background = 'linear-gradient(145deg, #ef4444, #dc2626)';
                        btn.style.color = 'white';
                        btn.style.boxShadow = '0 4px 12px rgba(239, 68, 68, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)';
                        btn.style.opacity = '0.5';
                        btn.style.cursor = 'not-allowed';
                        btn.disabled = true;
                        
                        btn.addEventListener('mouseover', () => {
                            if (!btn.disabled) {
                                btn.style.background = 'linear-gradient(145deg, #dc2626, #b91c1c)';
                                btn.style.transform = 'translateY(-2px)';
                                btn.style.boxShadow = '0 8px 20px rgba(239, 68, 68, 0.5)';
                            }
                        });
                        
                        btn.addEventListener('mouseout', () => {
                            if (!btn.disabled) {
                                btn.style.background = 'linear-gradient(145deg, #ef4444, #dc2626)';
                                btn.style.transform = 'translateY(0)';
                                btn.style.boxShadow = '0 4px 12px rgba(239, 68, 68, 0.4)';
                            }
                        });
                    }
                });
            }
            
            // Add CSS animation keyframes
            if (!document.querySelector('#delete-modal-animations')) {
                const style = document.createElement('style');
                style.id = 'delete-modal-animations';
                style.textContent = `
                    @keyframes pulse {
                        0%, 100% { transform: scale(1); }
                        50% { transform: scale(1.05); }
                    }
                `;
                document.head.appendChild(style);
            }
            
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
            // Reset checkbox state for next time
            const checkbox = form.querySelector('input[type="checkbox"]');
            const checkmark = form.querySelector('.checkmark');
            const deleteBtn = form.querySelector('.btn:not(.secondary)');
            
            if (checkbox) {
                checkbox.checked = false;
                console.log('📋 Checkbox reset to unchecked');
            }
            
            if (checkmark) {
                checkmark.style.background = 'transparent';
                checkmark.style.borderColor = '#6b7280';
                const checkIcon = checkmark.querySelector('i');
                if (checkIcon) checkIcon.style.opacity = '0';
            }
            
            if (deleteBtn) {
                deleteBtn.disabled = true;
                deleteBtn.style.opacity = '0.5';
                deleteBtn.style.cursor = 'not-allowed';
            }
            
            // Properly hide by removing show class and adding hidden class
            form.classList.remove('show');
            form.classList.add('hidden');
            // Remove inline styles that override CSS classes
            form.style.display = '';
            AppState.currentModal = null;
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
        console.log('⚠️ Delete form not found - handlers not initialized');
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
            console.log('⚠️ Notification container not found, using console.log');
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
            
            // Apply dark theme styling to add cluster modal
            this.applyDarkTheme(overlay);
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
        // Only prevent closing if clicking inside modal content (not overlay or close button)
        if (event && event.target.closest && event.target.closest('.modal-container') && 
            !event.target.closest('.modal-close') && !event.target.closest('[onclick*="closeModal"]')) {
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
    },
    
    applyDarkTheme(overlay) {
        // Apply dark theme styling to add cluster modal
        if (overlay) {
            // Dark theme modal overlay
            overlay.style.background = 'rgba(0, 0, 0, 0.7)';
            
            const modalContainer = overlay.querySelector('.modal-container');
            if (modalContainer) {
                // Dark theme modal container with optimized size
                modalContainer.style.background = 'linear-gradient(145deg, #1f2937, #111827)';
                modalContainer.style.border = '1px solid rgba(75, 85, 99, 0.4)';
                modalContainer.style.boxShadow = '0 32px 64px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(75, 85, 99, 0.3)';
                modalContainer.style.maxWidth = '600px';  // Slightly wider for better field arrangement
                modalContainer.style.width = '95%';  // More responsive
                modalContainer.style.maxHeight = '85vh';  // Prevent modal from being too tall
                modalContainer.style.overflowY = 'auto';  // Allow scrolling if needed
                
                // Style form labels with compact sizing
                const labels = modalContainer.querySelectorAll('.form-label');
                labels.forEach(label => {
                    label.style.color = '#e5e7eb';
                    label.style.fontWeight = '600';
                    label.style.fontSize = '14px';  // Consistent label size
                    label.style.marginBottom = '6px';  // Reduced label spacing
                    label.style.display = 'block';
                });
                
                // Style form inputs and selects with compact sizing
                const inputs = modalContainer.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    input.style.background = 'rgba(55, 65, 81, 0.8)';
                    input.style.border = '1px solid rgba(75, 85, 99, 0.5)';
                    input.style.borderRadius = '10px';  // Slightly smaller radius
                    input.style.color = '#f9fafb';
                    input.style.padding = '10px 14px';  // More compact padding
                    input.style.fontSize = '14px';  // Consistent font size
                    input.style.width = '100%';  // Full width within grid
                    
                    // Focus states
                    input.addEventListener('focus', () => {
                        input.style.borderColor = '#3b82f6';
                        input.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
                    });
                    
                    input.addEventListener('blur', () => {
                        input.style.borderColor = 'rgba(75, 85, 99, 0.5)';
                        input.style.boxShadow = 'none';
                    });
                });
                
                // Style help text
                const helpTexts = modalContainer.querySelectorAll('.help-text, .form-help');
                helpTexts.forEach(help => {
                    help.style.color = '#9ca3af';
                });
                
                // Optimize layout and reduce wasted space
                const modalBody = modalContainer.querySelector('.modal-body');
                if (modalBody) {
                    modalBody.style.padding = '20px';  // Reduced from 32px
                }
                
                // Style subscription section with reduced spacing
                const subscriptionSection = modalContainer.querySelector('.subscription-selection-section');
                if (subscriptionSection) {
                    subscriptionSection.style.background = 'rgba(55, 65, 81, 0.3)';
                    subscriptionSection.style.border = '1px solid rgba(75, 85, 99, 0.3)';
                    subscriptionSection.style.borderRadius = '16px';
                    subscriptionSection.style.padding = '20px';  // Reduced padding
                    subscriptionSection.style.marginBottom = '16px';  // Reduced gap
                }
                
                // Create more compact form rows
                const formRows = modalContainer.querySelectorAll('.form-row');
                formRows.forEach(row => {
                    row.style.display = 'grid';
                    row.style.gridTemplateColumns = '1fr 1fr';  // Two equal columns
                    row.style.gap = '16px';  // Reduced gap between fields
                    row.style.marginBottom = '16px';  // Reduced bottom margin
                });
                
                // Style individual form fields for better spacing
                const formFields = modalContainer.querySelectorAll('.form-field');
                formFields.forEach(field => {
                    field.style.marginBottom = '0';  // Remove individual margins since we use grid gap
                });
                
                // Style other sections
                const sections = modalContainer.querySelectorAll('.form-section');
                sections.forEach(section => {
                    section.style.background = 'rgba(55, 65, 81, 0.3)';
                    section.style.border = '1px solid rgba(75, 85, 99, 0.3)';
                    section.style.borderRadius = '16px';
                    section.style.padding = '20px';
                    section.style.marginBottom = '16px';
                });
                
                // Style buttons
                const buttons = modalContainer.querySelectorAll('button');
                buttons.forEach(btn => {
                    if (btn.classList.contains('btn-primary') || btn.id === 'addClusterBtn') {
                        // Primary button (Add Cluster)
                        btn.style.background = 'linear-gradient(145deg, #3b82f6, #2563eb)';
                        btn.style.color = 'white';
                        btn.style.border = 'none';
                        btn.style.borderRadius = '14px';
                        btn.style.padding = '14px 28px';
                        btn.style.fontWeight = '600';
                        btn.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2)';
                        btn.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                        
                        btn.addEventListener('mouseover', () => {
                            if (!btn.disabled) {
                                btn.style.background = 'linear-gradient(145deg, #2563eb, #1d4ed8)';
                                btn.style.transform = 'translateY(-2px)';
                                btn.style.boxShadow = '0 8px 20px rgba(59, 130, 246, 0.4)';
                            }
                        });
                        
                        btn.addEventListener('mouseout', () => {
                            if (!btn.disabled) {
                                btn.style.background = 'linear-gradient(145deg, #3b82f6, #2563eb)';
                                btn.style.transform = 'translateY(0)';
                                btn.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
                            }
                        });
                    } else {
                        // Secondary buttons (Cancel, etc.)
                        btn.style.background = 'linear-gradient(145deg, #4b5563, #374151)';
                        btn.style.color = '#e5e7eb';
                        btn.style.border = 'none';
                        btn.style.borderRadius = '14px';
                        btn.style.padding = '14px 28px';
                        btn.style.fontWeight = '600';
                        btn.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)';
                        btn.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                        
                        btn.addEventListener('mouseover', () => {
                            btn.style.background = 'linear-gradient(145deg, #374151, #2d3748)';
                            btn.style.transform = 'translateY(-2px)';
                            btn.style.boxShadow = '0 8px 20px rgba(0, 0, 0, 0.3)';
                        });
                        
                        btn.addEventListener('mouseout', () => {
                            btn.style.background = 'linear-gradient(145deg, #4b5563, #374151)';
                            btn.style.transform = 'translateY(0)';
                            btn.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
                        });
                    }
                });
                
                // Style modal footer with reduced padding
                const footer = modalContainer.querySelector('.modal-footer');
                if (footer) {
                    footer.style.background = 'rgba(17, 24, 39, 0.8)';
                    footer.style.borderTop = '1px solid rgba(75, 85, 99, 0.3)';
                    footer.style.padding = '16px 20px';  // Reduced from default
                    footer.style.display = 'flex';
                    footer.style.gap = '12px';
                    footer.style.justifyContent = 'flex-end';
                    footer.style.alignItems = 'center';
                }
                
                // Style checkboxes and radio buttons
                const checkboxes = modalContainer.querySelectorAll('input[type="checkbox"], input[type="radio"]');
                checkboxes.forEach(cb => {
                    const parent = cb.parentElement;
                    if (parent) {
                        parent.style.color = '#e5e7eb';
                    }
                });
                
                // Style any icons
                const icons = modalContainer.querySelectorAll('i.fas, i.fab');
                icons.forEach(icon => {
                    if (!icon.closest('button')) {
                        icon.style.color = '#3b82f6';
                    }
                });
            }
        }
    }
};

// ===== ENHANCED COUNTER ANIMATION =====
const CounterManager = {
    animate() {
        // Animate metric values
        const counters = document.querySelectorAll('.metric-value[data-target]');
        console.log(`🎯 CounterManager: Found ${counters.length} metric elements to animate`);
        
        counters.forEach((counter, index) => {
            const target = parseFloat(counter.getAttribute('data-target'));
            const isDollar = counter.textContent.includes('$'); 
            const isPercent = counter.textContent.includes('%');
            
            console.log(`📊 Animating metric ${index + 1}: target=${target}, isDollar=${isDollar}, isPercent=${isPercent}`);
            
            // Stagger animations for better visual effect
            setTimeout(() => {
                this.animateValue(counter, 0, target, 1800, isDollar, isPercent);
            }, index * 200);
        });
        
        // Animate trend percentages
        setTimeout(() => {
            this.animateTrends();
        }, 1000);
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
            
            // Add visual feedback during animation
            if (progress < 1) {
                element.style.color = '#10b981';
                element.style.transform = 'scale(1.02)';
                element.style.transition = 'color 0.3s ease, transform 0.3s ease';
                requestAnimationFrame(animate);
            } else {
                // Reset styles after animation
                setTimeout(() => {
                    element.style.color = '';
                    element.style.transform = '';
                }, 300);
            }
        };
        
        requestAnimationFrame(animate);
    },

    animateTrends() {
        const trendElements = document.querySelectorAll('.metric-trend span');
        console.log(`📈 CounterManager: Found ${trendElements.length} trend elements to animate`);
        
        trendElements.forEach((element, index) => {
            const metricCard = element.closest('.metric-card');
            let trendPercent = 0;
            
            // Generate realistic trend percentages based on metric type
            if (metricCard?.classList.contains('cost-card')) {
                trendPercent = (Math.random() * 15) - 5; // -5% to +10%
            } else if (metricCard?.classList.contains('savings-card')) {
                trendPercent = (Math.random() * 25) + 5; // +5% to +30%
            } else if (metricCard?.classList.contains('optimization-card')) {
                trendPercent = (Math.random() * 20) + 2; // +2% to +22%
            } else {
                trendPercent = (Math.random() * 20) - 10; // -10% to +10%
            }
            
            console.log(`📈 Animating trend ${index + 1}: ${trendPercent.toFixed(1)}%`);
            
            // Animate trend with delay
            setTimeout(() => {
                this.animateTrendValue(element, trendPercent);
            }, index * 150);
        });
    },

    animateTrendValue(element, targetPercent) {
        if (!element) return;
        
        const duration = 1000;
        const startTime = performance.now();
        const isPositive = targetPercent >= 0;
        
        // Update trend direction and styling
        const trendContainer = element.closest('.metric-trend');
        if (trendContainer) {
            const icon = trendContainer.querySelector('i');
            if (icon) {
                icon.className = isPositive ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
            }
            trendContainer.className = `metric-trend ${isPositive ? 'up' : 'down'}`;
        }
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = targetPercent * progress;
            const sign = current >= 0 ? '+' : '';
            element.textContent = sign + current.toFixed(1) + '%';
            
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
                
                // Use enhanced message if available, otherwise default
                let successMessage = '✅ Cluster access validated successfully';
                if (result.message) {
                    successMessage = `✅ ${result.message}`;
                }
                
                if (validationText) {
                    validationText.textContent = successMessage;
                }
                if (validationIcon) {
                    validationIcon.className = 'fas fa-check-circle';
                }
                
                // Auto-populate resource group if discovered
                if (result.validation_result?.discovered_resource_group) {
                    const resourceGroupInput = document.getElementById('resourceGroup') || document.getElementById('resource_group');
                    if (resourceGroupInput && !resourceGroupInput.value.trim()) {
                        resourceGroupInput.value = result.validation_result.discovered_resource_group;
                        
                        // Show user that we auto-filled
                        if (result.validation_result.auto_discovered) {
                            const rgLabel = resourceGroupInput.parentElement?.querySelector('label');
                            if (rgLabel) {
                                rgLabel.style.color = '#28a745';
                                setTimeout(() => {
                                    if (rgLabel) rgLabel.style.color = '';
                                }, 3000);
                            }
                        }
                    }
                }
                
                setTimeout(() => {
                    validationStatus.style.display = 'none';
                }, 5000); // Extended timeout for user to see auto-discovery message
            } else {
                validationStatus.classList.add('error');
                
                // Use enhanced error message if available
                let errorMessage = `❌ Validation failed: ${result.validation_result?.error || 'Unknown error'}`;
                if (result.message) {
                    errorMessage = `❌ ${result.message}`;
                }
                
                if (validationText) {
                    validationText.textContent = errorMessage;
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
            environment: Utils.withElement('environment', el => el.value) || '',
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

        // PROPER FLOW: Start analysis and let server response drive status updates
        AppState.analyzingClusters.add(clusterId);
        
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
                
                // PROPER FLOW: Just trigger a refresh to get updated status from server
                LoadingManager.hide();
                
                NotificationManager.show(
                    'Analysis Started!', 
                    `Analysis for "${clusterName}" has been initiated`,
                    'success',
                    3000
                );
                
                // Force immediate refresh to show analyzing status
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
                
                // ✅ REFRESH NOTIFICATIONS: Analysis may have triggered new alerts
             
                
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
            AppState.analyzingClusters.delete(clusterId);
            
            // ✅  Update the status-info element to show failed state
            const statusInfoElement = clusterCard?.querySelector('.status-info');
            if (statusInfoElement) {
                statusInfoElement.innerHTML = `
                    <i class="fas fa-exclamation-triangle error-icon"></i>
                    <span class="status-text">Failed</span>
                `;
                console.log(`✅ Updated status-info for ${clusterId} to show failed state`);
            }
            
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
    // Find cluster data from the DOM
    const clusterCard = document.querySelector(`[data-cluster-id="${clusterId}"]`);
    let clusterName = 'Unknown Cluster';
    let resourceGroup = 'Unknown Resource Group';
    
    if (clusterCard) {
        const nameElement = clusterCard.querySelector('.cluster-name, h3');
        if (nameElement) {
            clusterName = nameElement.textContent.trim();
        }
        
        // Try to extract resource group from cluster ID or data attributes
        const rgElement = clusterCard.querySelector('[data-resource-group]');
        if (rgElement) {
            resourceGroup = rgElement.dataset.resourceGroup;
        } else {
            // Try to extract from cluster ID format: "rg-xxx_cluster-name"
            const parts = clusterId.split('_');
            if (parts.length >= 2) {
                resourceGroup = parts[0];
            }
        }
    }
    
    DeleteFormManager.show(clusterId, clusterName, resourceGroup);
}

function closeModal(event) {
    ModalManager.close(event);
}

function addCluster() {
    ClusterManager.add();
}

// Ensure functions are available globally
document.addEventListener('DOMContentLoaded', function() {
    window.selectCluster = selectCluster;
    window.analyzeCluster = analyzeCluster;
    window.deleteCluster = deleteCluster;
    window.closeModal = closeModal;
    window.addCluster = addCluster;
    window.hideDeleteForm = hideDeleteForm;
});

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
    
    // ✅ NEW: Global auto-refresh is now handled by GlobalRefreshManager
    console.log('✅ Global auto-refresh system active for clusters page');

    console.log('✨ Enhanced multi-subscription dashboard fully loaded!');
});

// ===== UPDATE FUNCTIONS (Called by Global Refresh Manager) =====

function updatePortfolioMetricsUI(portfolioSummary) {
    // Update total monthly cost
    const costElement = document.querySelector('.cost-card .metric-value');
    if (costElement) {
        const currentCost = portfolioSummary.total_monthly_cost || 0;
        animateValueUpdate(costElement, currentCost, true); // true for dollar format
    }
    
    // Update potential savings
    const savingsElement = document.querySelector('.savings-card .metric-value');
    if (savingsElement) {
        const currentSavings = portfolioSummary.total_potential_savings || 0;
        animateValueUpdate(savingsElement, currentSavings, true); // true for dollar format
    }
    
    // Update average optimization percentage
    const optimizationElement = document.querySelector('.optimization-card .metric-value');
    if (optimizationElement) {
        const currentOptimization = portfolioSummary.avg_optimization_pct || 0;
        animateValueUpdate(optimizationElement, currentOptimization, false, true); // false for dollar, true for percent
    }
    
    // Update environment count if needed
    const environmentsElement = document.querySelector('.environments-card .metric-value');
    if (environmentsElement && portfolioSummary.environments) {
        const envCount = portfolioSummary.environments.length || 0;
        animateValueUpdate(environmentsElement, envCount, false, false); // no formatting
    }
    
    console.log(`📊 Updated metrics: Cost=$${portfolioSummary.total_monthly_cost || 0}, Savings=$${portfolioSummary.total_potential_savings || 0}, Optimization=${portfolioSummary.avg_optimization_pct || 0}%`);
}

function animateValueUpdate(element, newValue, isDollar = false, isPercent = false) {
    if (!element) return;
    
    // Get current value from element
    const currentText = element.textContent.replace(/[$%,]/g, '');
    const currentValue = parseFloat(currentText) || 0;
    
    // Only animate if value changed significantly (avoid micro-updates)
    if (Math.abs(newValue - currentValue) < 0.01) return;
    
    // Animate the change
    const duration = 1000; // 1 second animation
    const startTime = performance.now();
    
    function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Smooth easing
        const eased = progress < 0.5 
            ? 2 * progress * progress 
            : 1 - Math.pow(-2 * progress + 2, 2) / 2;
        
        const current = currentValue + (newValue - currentValue) * eased;
        
        // Format the value
        let formattedValue;
        if (isDollar) {
            formattedValue = `$${Math.round(current)}`;
        } else if (isPercent) {
            formattedValue = `${current.toFixed(1)}%`;
        } else {
            formattedValue = Math.round(current).toString();
        }
        
        element.textContent = formattedValue;
        
        // Add visual feedback for updates
        element.style.color = '#10b981'; // Green color during update
        element.style.transition = 'color 0.3s ease';
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            // Reset color after animation
            setTimeout(() => {
                element.style.color = '';
            }, 500);
        }
    }
    
    requestAnimationFrame(animate);
}

function updateClusterCardsStatus(clusters) {
    // Update each cluster card's status without full page reload
    console.log('🔄 updateClusterCardsStatus called with clusters:', clusters.length);
    clusters.forEach(cluster => {
        console.log(`🔄 Updating cluster ${cluster.id} status: ${cluster.analysis_status}`);
        const clusterCard = document.querySelector(`[data-cluster-id="${cluster.id}"]`);
        if (!clusterCard) {
            console.log(`❌ Cluster card not found for ${cluster.id}`);
            return;
        }
        console.log(`✅ Found cluster card for ${cluster.id}`);
        
        // PROPER FLOW: Always update with server status - server is source of truth
        if (cluster.analysis_status === 'analyzing') {
            AppState.analyzingClusters.add(cluster.id);
        } else {
            AppState.analyzingClusters.delete(cluster.id);
        }
        
        // Update status info (matches actual HTML structure)
        const statusElement = clusterCard.querySelector('.status-info');
        if (statusElement) {
            updateClusterStatusDisplay(statusElement, cluster);
        }
        
        // IMPROVED: Update analyze button state based on analysis status
        const analyzeBtn = clusterCard.querySelector('.analyze-btn');
        if (analyzeBtn) {
            updateAnalyzeButtonState(analyzeBtn, cluster);
        }
        
        // Update cost metric (matches actual HTML structure)
        const costElements = clusterCard.querySelectorAll('.metric-info .metric-value');
        if (costElements[0] && cluster.last_cost !== undefined) {
            animateValueUpdate(costElements[0], cluster.last_cost, true); // Dollar format
        }
        
        // Update savings metric (matches actual HTML structure)
        if (costElements[1] && cluster.last_savings !== undefined) {
            animateValueUpdate(costElements[1], cluster.last_savings, true); // Dollar format
        }
        
        // Update optimization percentage (matches actual HTML structure)
        if (costElements[2] && cluster.last_cost > 0) {
            const optimizationPct = (cluster.last_savings / cluster.last_cost) * 100;
            animateValueUpdate(costElements[2], optimizationPct, false, true); // Percent format
        }
        
        // Update status dot color
        const statusDot = clusterCard.querySelector('.status-dot');
        if (statusDot) {
            statusDot.className = 'status-dot ' + (cluster.analysis_status === 'completed' ? 
                (cluster.last_savings && cluster.last_savings > 100 ? 'healthy' : 'warning') : 'inactive');
        }
    });
}

function updateAnalyzeButtonState(analyzeBtn, cluster) {
    const analysisStatus = cluster.analysis_status || 'pending';
    
    if (analysisStatus === 'completed') {
        // Change button to "View Results" state
        analyzeBtn.classList.remove('analyzing');
        analyzeBtn.disabled = false;
        analyzeBtn.setAttribute('title', 'View Results');
        
        // Update icon to eye
        const icon = analyzeBtn.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-eye';
        }
        
        // Update onclick to go to results
        analyzeBtn.onclick = (e) => {
            e.stopPropagation();
            LoadingManager.show('Loading analysis results...');
            setTimeout(() => {
                if (window?.location) {
                    window.location.href = `/cluster/${cluster.id}`;
                }
            }, 500);
        };
        
        console.log(`✅ Updated analyze button for ${cluster.id} to 'View Results' state`);
        
    } else if (analysisStatus === 'analyzing' || analysisStatus === 'running') {
        // Update analyzing state based on server status
        if (cluster.analysis_status === 'analyzing') {
            AppState.analyzingClusters.add(cluster.id);
        }
        
    } else {
        // Reset to initial "Analyze" state
        analyzeBtn.classList.remove('analyzing');
        analyzeBtn.disabled = false;
        analyzeBtn.setAttribute('title', 'Analyze Cluster');
        
        // Update icon to play
        const icon = analyzeBtn.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-play';
        }
        
        // Hide any spinner
        const spinner = analyzeBtn.querySelector('.analyzing-spinner');
        if (spinner) {
            spinner.style.display = 'none';
        }
        
        // Reset onclick to analyze function
        analyzeBtn.onclick = (e) => {
            e.stopPropagation();
            analyzeCluster(cluster.id);
        };
        
        console.log(`✅ Reset analyze button for ${cluster.id} to 'Analyze' state`);
    }
}

function updateClusterStatusDisplay(statusContainer, cluster) {
    const analysisStatus = cluster.analysis_status || 'pending';
    
    // Smooth update without DOM flicker - reuse existing elements
    let icon = statusContainer.querySelector('i');
    let statusText = statusContainer.querySelector('.status-text, .analyzing-text');
    
    // Create elements if they don't exist
    if (!icon) {
        icon = document.createElement('i');
        statusContainer.appendChild(icon);
    }
    if (!statusText) {
        statusText = document.createElement('span');
        statusText.className = 'status-text';
        statusContainer.appendChild(statusText);
    }
    
    // Update classes and text without innerHTML replacement
    if (analysisStatus === 'completed') {
        icon.className = 'fas fa-check-circle success-icon';
        statusText.className = 'status-text';
        statusText.textContent = 'Analyzed';
        
        // Remove from analyzing clusters tracking
        if (AppState.analyzingClusters.has(cluster.id)) {
            AppState.analyzingClusters.delete(cluster.id);
        }
        
    } else if (analysisStatus === 'analyzing' || analysisStatus === 'running') {
        const progress = cluster.analysis_progress || 0;
        icon.className = 'fas fa-cog fa-spin analyzing-icon';
        statusText.className = 'analyzing-text';
        statusText.textContent = 'Analyzing...';
        
        // Add to analyzing clusters tracking
        AppState.analyzingClusters.add(cluster.id);
        
    } else if (analysisStatus === 'failed') {
        icon.className = 'fas fa-exclamation-triangle error-icon';
        statusText.className = 'status-text';
        statusText.textContent = 'Failed';
        
    } else {
        icon.className = 'fas fa-clock warning-icon';
        statusText.className = 'status-text';
        statusText.textContent = 'Pending';
    }
    
    console.log(`✅ Updated status for cluster ${cluster.id}: ${analysisStatus}`);
}

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

// ===== GLOBAL EXPORTS FOR AUTO-REFRESH =====
// Make functions available globally for the GlobalRefreshManager
window.updateClusterCardsStatus = updateClusterCardsStatus;
window.updatePortfolioMetricsUI = function(portfolioData) {
    // Update portfolio metrics in the header
    if (portfolioData) {
        const totalCostEl = document.querySelector('[data-metric="total-cost"]');
        const totalSavingsEl = document.querySelector('[data-metric="total-savings"]'); 
        const avgOptimizationEl = document.querySelector('[data-metric="avg-optimization"]');
        
        if (totalCostEl && portfolioData.total_cost !== undefined) {
            animateValueUpdate(totalCostEl, portfolioData.total_cost, true);
        }
        if (totalSavingsEl && portfolioData.total_savings !== undefined) {
            animateValueUpdate(totalSavingsEl, portfolioData.total_savings, true);
        }
        if (avgOptimizationEl && portfolioData.total_cost > 0) {
            const optimizationPct = portfolioData.total_savings / portfolioData.total_cost * 100;
            animateValueUpdate(avgOptimizationEl, optimizationPct, false, '%');
        }
    }
};

