/**
 * ============================================================================
 * AKS COST INTELLIGENCE - FORM VALIDATION & HANDLERS
 * ============================================================================
 * Form validation, input handling, and submission management
 * ============================================================================
 */

import { AppConfig } from './config.js';
import { showNotification } from './notifications.js';
import { validateInput } from './utils.js';

/**
 * Validates analysis form inputs
 */
export function validateAnalysisForm() {
    const resourceGroup = document.getElementById('resource_group')?.value.trim();
    const clusterName = document.getElementById('cluster_name')?.value.trim();
    
    if (!resourceGroup || !clusterName) return false;
    
    // Clear previous validation styles
    document.querySelectorAll('.form-control').forEach(input => {
        input.classList.remove('is-invalid', 'is-valid');
    });
    
    let isValid = true;
    
    // Validate Resource Group
    const rgInput = document.getElementById('resource_group');
    if (rgInput) {
        if (resourceGroup.length < AppConfig.MIN_VALIDATION_LENGTH) {
            rgInput.classList.add('is-invalid');
            showNotification('Resource Group name must be at least 3 characters', 'error');
            isValid = false;
        } else {
            rgInput.classList.add('is-valid');
        }
    }
    
    // Validate Cluster Name
    const cnInput = document.getElementById('cluster_name');
    if (cnInput) {
        if (clusterName.length < AppConfig.MIN_VALIDATION_LENGTH) {
            cnInput.classList.add('is-invalid');
            showNotification('Cluster name must be at least 3 characters', 'error');
            isValid = false;
        } else {
            cnInput.classList.add('is-valid');
        }
    }
    
    return isValid;
}

/**
 * Sets up real-time input validation
 */
export function setupInputValidation() {
    // Support both old and new field naming conventions
    const resourceGroupInput = document.getElementById('resource_group') || document.getElementById('resourceGroup');
    const clusterNameInput = document.getElementById('cluster_name') || document.getElementById('clusterName');
    const subscriptionSelect = document.getElementById('subscriptionSelect');
    
    if (resourceGroupInput) {
        resourceGroupInput.addEventListener('input', function() {
            const validation = validateInput(this.value.trim(), {
                required: true,
                minLength: AppConfig.MIN_VALIDATION_LENGTH
            });
            
            this.classList.remove('is-invalid', 'is-valid');
            
            if (this.value.trim().length === 0) {
                // Don't show validation for empty fields
                return;
            }
            
            if (validation.isValid) {
                this.classList.add('is-valid');
            } else {
                this.classList.add('is-invalid');
            }
        });
    }
    
    if (clusterNameInput) {
        clusterNameInput.addEventListener('input', function() {
            const validation = validateInput(this.value.trim(), {
                required: true,
                minLength: AppConfig.MIN_VALIDATION_LENGTH,
                pattern: /^[a-zA-Z0-9-_]+$/
            });
            
            this.classList.remove('is-invalid', 'is-valid');
            
            if (this.value.trim().length === 0) {
                return;
            }
            
            if (validation.isValid) {
                this.classList.add('is-valid');
            } else {
                this.classList.add('is-invalid');
            }
        });
    }
    
    // Add subscription validation for cluster form
    if (subscriptionSelect) {
        subscriptionSelect.addEventListener('change', function() {
            this.classList.remove('is-invalid', 'is-valid');
            
            if (this.value && this.value !== '') {
                this.classList.add('is-valid');
            } else {
                this.classList.add('is-invalid');
            }
        });
    }
}

/**
 * Enhanced cluster form validation
 */
export function validateClusterForm(formData) {
    const errors = [];
    
    const clusterName = formData.cluster_name?.trim();
    const resourceGroup = formData.resource_group?.trim();
    const subscriptionId = formData.subscription_id?.trim();
    
    if (!subscriptionId) {
        errors.push('Azure subscription is required');
    }
    
    if (!clusterName) {
        errors.push('Cluster name is required');
    } else if (clusterName.length < 3) {
        errors.push('Cluster name must be at least 3 characters');
    } else if (!/^[a-zA-Z0-9-_]+$/.test(clusterName)) {
        errors.push('Cluster name can only contain letters, numbers, hyphens, and underscores');
    }
    
    if (!resourceGroup) {
        errors.push('Resource group is required');
    } else if (resourceGroup.length < 3) {
        errors.push('Resource group name must be at least 3 characters');
    }
    
    // Validate environment if provided
    if (formData.environment && !['development', 'staging', 'production'].includes(formData.environment)) {
        errors.push('Environment must be one of: development, staging, production');
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
}

/**
 * Enhanced cluster form submission handler
 */
export function handleEnhancedClusterFormSubmission(event) {
    event.preventDefault();
    event.stopPropagation();
    
    logDebug('📝 Enhanced cluster form submission started');
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Get form values with proper validation - match actual form field names
    const clusterData = {
        cluster_name: (formData.get('clusterName') || '').trim(),
        resource_group: (formData.get('resourceGroup') || '').trim(),
        environment: formData.get('environment') || 'development',
        region: (formData.get('region') || '').trim(),
        description: (formData.get('description') || '').trim(),
        auto_analyze: formData.get('auto_analyze') === 'on' || document.getElementById('auto_analyze')?.checked === true,
        subscription_id: (formData.get('subscription_id') || '').trim()
    };
    
    logDebug('📋 Form data collected:', clusterData);
    
    // Enhanced validation
    const validation = validateClusterForm(clusterData);
    if (!validation.isValid) {
        validation.errors.forEach(error => {
            showNotification(error, 'error');
        });
        return;
    }
    
    // Get submit button
    const submitBtn = form.querySelector('button[type="submit"]');
    if (!submitBtn) {
        logError('❌ Submit button not found');
        return;
    }
    
    // Show loading state
    const originalHTML = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding Cluster...';
    submitBtn.disabled = true;
    
    // Disable form inputs during submission
    form.querySelectorAll('input, select, textarea').forEach(input => {
        input.disabled = true;
    });
    
    logDebug('📤 Sending API request...');
    
    // Make API call
    fetch('/api/clusters', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(clusterData)
    })
    .then(response => {
        logDebug('📡 API response status:', response.status);
        
        if (!response.ok) {
            return response.text().then(text => {
                try {
                    const errorData = JSON.parse(text);
                    throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
                } catch (parseError) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            });
        }
        
        return response.json();
    })
    .then(data => {
        logDebug('✅ API success response:', data);
        
        // Success notification
        const clusterId = data.cluster_id || data.id;
        if (clusterData.auto_analyze) {
            showNotification(
                `🎉 Cluster "${clusterData.cluster_name}" added successfully! Analysis is starting automatically.`, 
                'success', 
                6000
            );
        } else {
            showNotification(
                `✅ Cluster "${clusterData.cluster_name}" added successfully!`, 
                'success'
            );
        }
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('addClusterModal'));
        if (modal) {
            modal.hide();
        }
        
        // Reset form
        form.reset();
        
        // Redirect or reload after short delay
        setTimeout(() => {
            if (clusterId && clusterData.auto_analyze) {
                window.location.href = `/cluster/${clusterId}`;
            } else {
                window.location.reload();
            }
        }, 2000);
        
    })
    .catch(error => {
        logError('❌ API error:', error);
        showNotification(`Failed to add cluster: ${error.message}`, 'error');
    })
    .finally(() => {
        // Always restore button and form state
        submitBtn.innerHTML = originalHTML;
        submitBtn.disabled = false;
        
        // Re-enable form inputs
        form.querySelectorAll('input, select, textarea').forEach(input => {
            input.disabled = false;
        });
    });
}

/**
 * Sets up form event handlers
 */
export function setupFormHandlers() {
    logDebug('🔧 Setting up enhanced form handlers');
    
    // Handle analysis form ONLY ONCE
    const analysisForm = document.getElementById('analysisForm');
    if (analysisForm) {
        // Remove ALL existing event listeners by cloning
        const newForm = analysisForm.cloneNode(true);
        analysisForm.parentNode.replaceChild(newForm, analysisForm);
        
        // Add ONLY the fixed handler
        newForm.addEventListener('submit', handleAnalysisSubmit);
        logDebug('✅ Analysis form handler attached (fixed version)');
    }
    
    logDebug('✅ Form handlers setup complete - cluster validation will use enhanced validateForm()');
}

/**
 * Enhanced analysis form submission handler
 */
export function handleAnalysisSubmit(event) {
    event.preventDefault();
    
    if (!validateAnalysisForm()) return;
    
    logDebug('📊 Starting FIXED analysis with guaranteed completion');
    
    const btn = document.getElementById('analyzeBtn');
    const progress = document.getElementById('analysisProgress');
    
    // Show loading state
    if (btn) {
        btn.classList.add('loading');
        btn.disabled = true;
    }
    
    if (progress) {
        progress.classList.add('visible');
        progress.style.display = 'block';
    }
    
    // Start progress animation
    if (typeof startEnhancedProgressAnimation === 'function') {
        startEnhancedProgressAnimation();
    }
    
    // Submit analysis
    fetch('/analyze', {
        method: 'POST',
        body: new FormData(event.target)
    })
    .then(response => {
        if (!response.ok) throw new Error(response.statusText);
        return response.text();
    })
    .then(() => {
        logDebug('✅ Analysis completed successfully');
        
        // Complete progress
        if (typeof completeProgressWithSuccess === 'function') {
            completeProgressWithSuccess();
        }
        
        // Show success notification
        showNotification('🎉 Analysis completed! Loading dashboard...', 'success');
        
        // Wait a moment, then switch to dashboard and reset
        setTimeout(() => {
            // Switch to dashboard tab
            if (typeof switchToTab === 'function') {
                switchToTab('#dashboard');
            }
            
            // Reset form completely
            resetAnalysisForm();
            
            
        }, 2000);
    })
    .catch(error => {
        logError('❌ Analysis failed:', error);
        showNotification(`Analysis failed: ${error.message}`, 'error');
        resetAnalysisForm();
    });
}

/**
 * Resets analysis form to initial state
 */
export function resetAnalysisForm() {
    logDebug('🧹 Resetting analysis form to initial state');
    
    const btn = document.getElementById('analyzeBtn');
    const progress = document.getElementById('analysisProgress');
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');
    
    // Reset button to original state
    if (btn) {
        btn.classList.remove('loading');
        btn.disabled = false;
        btn.innerHTML = `
            <span class="btn-content">
                <i class="fas fa-play me-2"></i>
                <span class="btn-text">Start Analysis</span>
            </span>
            <div class="btn-loader d-none">
                <i class="fas fa-spinner fa-spin me-2"></i>
                <span>Analyzing...</span>
            </div>
        `;
    }
    
    // Hide and reset progress bar
    if (progress) {
        progress.classList.remove('visible');
        progress.style.display = 'none';
    }
    
    // Reset progress bar fill and text
    if (fill) {
        fill.style.width = '0%';
        fill.style.background = '';
        fill.style.boxShadow = '';
    }
    
    if (text) {
        text.textContent = 'Initializing analysis...';
    }
    
    logDebug('✅ Analysis form reset completed');
}

/**
 * Generic form submission handler
 */
export function handleFormSubmission(form, endpoint, options = {}) {
    return new Promise((resolve, reject) => {
        const formData = new FormData(form);
        const data = {};
        
        // Convert FormData to object
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        // Apply any data transformations
        if (options.transformData) {
            Object.assign(data, options.transformData(data));
        }
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalHTML = submitBtn?.innerHTML;
        
        // Show loading state
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = options.loadingText || '<i class="fas fa-spinner fa-spin me-2"></i>Submitting...';
        }
        
        fetch(endpoint, {
            method: options.method || 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...options.headers
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(result => {
            if (options.onSuccess) {
                options.onSuccess(result);
            }
            resolve(result);
        })
        .catch(error => {
            if (options.onError) {
                options.onError(error);
            } else {
                showNotification(`Submission failed: ${error.message}`, 'error');
            }
            reject(error);
        })
        .finally(() => {
            // Restore button state
            if (submitBtn && originalHTML) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHTML;
            }
        });
    });
}

// Make functions available globally for backward compatibility
if (typeof window !== 'undefined') {
    window.validateAnalysisForm = validateAnalysisForm;
    window.setupInputValidation = setupInputValidation;
    window.setupFormHandlers = setupFormHandlers;
    window.handleAnalysisSubmit = handleAnalysisSubmit;
    window.resetAnalysisForm = resetAnalysisForm;
    window.handleEnhancedClusterFormSubmission = handleEnhancedClusterFormSubmission;
    
    // validateForm is now directly implemented in the template - no override needed
}