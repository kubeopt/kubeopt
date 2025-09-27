/**
 * ============================================================================
 * MODAL INPUT FIX - COMPLETE SOLUTION
 * ============================================================================
 * Fixes modal form input issues, cancel button, and z-index problems
 * ============================================================================
 */

// ============================================================================
// 1. FORCE REMOVE ALL MODAL EVENT LISTENERS AND RESET
// ============================================================================

function forceResetModal() {
    console.log('🔧 Force resetting modal state...');
    
    // Remove any existing modal instances
    const existingModals = document.querySelectorAll('.modal');
    existingModals.forEach(modal => {
        const instance = bootstrap.Modal.getInstance(modal);
        if (instance) {
            instance.dispose();
        }
    });
    
    // Remove any stuck backdrops
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
    
    // Remove modal-open class from body
    document.body.classList.remove('modal-open');
    document.body.style.paddingRight = '';
    document.body.style.overflow = '';
    
    console.log('✅ Modal state reset complete');
}

// ============================================================================
// 2. COMPREHENSIVE MODAL CSS FIX
// ============================================================================

function addModalInputFix() {
    console.log('🎨 Adding comprehensive modal CSS fix...');
    
    // Remove any existing fix
    const existingStyle = document.getElementById('modal-input-fix');
    if (existingStyle) existingStyle.remove();
    
    const style = document.createElement('style');
    style.id = 'modal-input-fix';
    style.textContent = `
        /* CRITICAL: Fix modal z-index hierarchy */
        .modal-backdrop {
            z-index: 1040 !important;
        }
        
        .modal {
            z-index: 1050 !important;
        }
        
        .modal-dialog {
            z-index: 1051 !important;
            position: relative !important;
        }
        
        .modal-content {
            z-index: 1052 !important;
            position: relative !important;
        }
        
        /* CRITICAL: Ensure all form inputs are fully accessible */
        .modal .form-control,
        .modal .form-select,
        .modal .form-check-input,
        .modal textarea,
        .modal input {
            position: relative !important;
            z-index: 1060 !important;
            background: #ffffff !important;
            border: 1px solid #ced4da !important;
            pointer-events: auto !important;
            user-select: auto !important;
            -webkit-user-select: auto !important;
            -moz-user-select: auto !important;
            touch-action: manipulation !important;
        }
        
        /* CRITICAL: Ensure focus states work */
        .modal .form-control:focus,
        .modal .form-select:focus,
        .modal input:focus,
        .modal textarea:focus {
            z-index: 1061 !important;
            border-color: #007bff !important;
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
            outline: none !important;
            background: #ffffff !important;
        }
        
        /* CRITICAL: Ensure buttons work */
        .modal .btn {
            position: relative !important;
            z-index: 1055 !important;
            pointer-events: auto !important;
            touch-action: manipulation !important;
        }
        
        /* CRITICAL: Ensure labels are clickable */
        .modal .form-label,
        .modal label {
            position: relative !important;
            z-index: 1055 !important;
            pointer-events: auto !important;
            cursor: pointer !important;
        }
        
        /* CRITICAL: Ensure modal header buttons work */
        .modal-header .btn-close,
        .modal-footer .btn {
            z-index: 1065 !important;
            pointer-events: auto !important;
        }
        
        /* CRITICAL: Prevent backdrop from interfering */
        .modal-backdrop {
            pointer-events: auto !important;
        }
        
        .modal-content {
            pointer-events: auto !important;
        }
        
        /* Fix for disabled inputs */
        .modal input:disabled,
        .modal .form-control:disabled,
        .modal .form-select:disabled {
            pointer-events: none !important;
            background-color: #e9ecef !important;
        }
        
        /* Dark theme fixes */
        [data-theme="dark"] .modal .form-control,
        [data-theme="dark"] .modal .form-select,
        [data-theme="dark"] .modal input,
        [data-theme="dark"] .modal textarea {
            background: #2d3748 !important;
            border-color: #4a5568 !important;
            color: #f7fafc !important;
        }
        
        [data-theme="dark"] .modal .form-control:focus,
        [data-theme="dark"] .modal .form-select:focus,
        [data-theme="dark"] .modal input:focus,
        [data-theme="dark"] .modal textarea:focus {
            background: #2d3748 !important;
            border-color: #4299e1 !important;
            color: #f7fafc !important;
        }
    `;
    
    document.head.appendChild(style);
    console.log('✅ Modal CSS fix applied');
}

// ============================================================================
// 3. ENHANCED MODAL INITIALIZATION
// ============================================================================

function initializeModalFixed() {
    console.log('🚀 Initializing modal with comprehensive fixes...');
    
    const addClusterModal = document.getElementById('addClusterModal');
    if (!addClusterModal) {
        console.error('❌ Modal not found');
        return;
    }
    
    // Force reset first
    forceResetModal();
    
    // Remove any existing event listeners by cloning
    const newModal = addClusterModal.cloneNode(true);
    addClusterModal.parentNode.replaceChild(newModal, addClusterModal);
    
    // Get fresh references
    const modal = document.getElementById('addClusterModal');
    const form = modal.querySelector('form');
    
    // CRITICAL: Set up proper modal events
    modal.addEventListener('show.bs.modal', function(event) {
        console.log('📝 Modal opening - setting up form');
        
        setTimeout(() => {
            // Ensure all inputs are enabled and focusable
            const inputs = this.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.disabled = false;
                input.readOnly = false;
                input.style.pointerEvents = 'auto';
                input.style.zIndex = '1060';
                input.style.position = 'relative';
                input.style.background = '#ffffff';
                input.removeAttribute('tabindex');
            });
            
            // Force focus on first input
            const firstInput = this.querySelector('input[type="text"]');
            if (firstInput) {
                firstInput.focus();
                firstInput.click();
                console.log('✅ Focused on first input');
            }
        }, 100);
    });
    
    modal.addEventListener('shown.bs.modal', function(event) {
        console.log('📝 Modal fully shown - ensuring accessibility');
        
        // Double-check all inputs are accessible
        const inputs = this.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.style.pointerEvents = 'auto';
            input.style.userSelect = 'auto';
            input.style.webkitUserSelect = 'auto';
            input.removeAttribute('readonly');
        });
        
        // Focus first input again
        const firstInput = this.querySelector('input[type="text"]');
        if (firstInput) {
            setTimeout(() => {
                firstInput.focus();
            }, 50);
        }
    });
    
    // CRITICAL: Handle modal close properly
    modal.addEventListener('hide.bs.modal', function(event) {
        console.log('📝 Modal closing - cleanup');
        if (form) {
            form.reset();
        }
    });
    
    // CRITICAL: Set up cancel buttons
    const cancelButtons = modal.querySelectorAll('[data-bs-dismiss="modal"], .btn-secondary');
    cancelButtons.forEach(btn => {
        btn.addEventListener('click', function(event) {
            console.log('❌ Cancel button clicked');
            event.preventDefault();
            event.stopPropagation();
            
            const modalInstance = bootstrap.Modal.getInstance(modal) || new bootstrap.Modal(modal);
            modalInstance.hide();
        });
    });
    
    // CRITICAL: Set up form submission
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            console.log('📝 Form submitted');
            handleFormSubmissionSafe(event);
        });
    }
    
    console.log('✅ Modal initialization complete');
}

// ============================================================================
// 4. SAFE FORM SUBMISSION HANDLER
// ============================================================================

function handleFormSubmissionSafe(event) {
    console.log('📝 Safe form submission handler');
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Extract data safely
    const clusterData = {
        cluster_name: (formData.get('cluster_name') || '').trim(),
        resource_group: (formData.get('resource_group') || '').trim(),
        environment: formData.get('environment') || '',
        region: (formData.get('region') || '').trim(),
        description: (formData.get('description') || '').trim(),
        auto_analyze: form.querySelector('#auto_analyze')?.checked === true
    };
    
    console.log('📋 Form data:', clusterData);
    
    // Basic validation
    if (!clusterData.cluster_name || clusterData.cluster_name.length < 3) {
        alert('Cluster name must be at least 3 characters long');
        return;
    }
    
    // Resource group is now optional - auto-discovery will handle it
    if (clusterData.resource_group && clusterData.resource_group.length > 0 && clusterData.resource_group.length < 3) {
        alert('Resource group name must be at least 3 characters long (or leave empty for auto-discovery)');
        return;
    }
    
    // Validate environment is selected
    if (!clusterData.environment || clusterData.environment === '') {
        alert('Please select an environment');
        return;
    }
    
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalHTML = submitBtn?.innerHTML || '';
    
    // Show loading
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding...';
        submitBtn.disabled = true;
    }
    
    // Make API call
    fetch('/api/clusters', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(clusterData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('✅ Cluster added:', data);
        alert('Cluster added successfully!');
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('addClusterModal'));
        if (modal) {
            modal.hide();
        }
        
        // Reload page
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    })
    .catch(error => {
        console.error('❌ Error:', error);
        alert('Error adding cluster: ' + error.message);
    })
    .finally(() => {
        if (submitBtn) {
            submitBtn.innerHTML = originalHTML;
            submitBtn.disabled = false;
        }
    });
}

// ============================================================================
// 5. EMERGENCY MODAL CLOSE FUNCTION
// ============================================================================

function emergencyCloseModal() {
    console.log('🚨 Emergency modal close');
    
    // Close all modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.classList.remove('show');
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
        modal.removeAttribute('aria-modal');
    });
    
    // Remove all backdrops
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
    
    // Reset body
    document.body.classList.remove('modal-open');
    document.body.style.paddingRight = '';
    document.body.style.overflow = '';
}

// ============================================================================
// 6. DEBUGGING FUNCTIONS
// ============================================================================

function debugModal() {
    const modal = document.getElementById('addClusterModal');
    const inputs = modal?.querySelectorAll('input, select, textarea');
    
    console.log('🔍 Modal debug info:');
    console.log('Modal element:', modal);
    console.log('Modal display:', modal?.style.display);
    console.log('Modal classes:', modal?.className);
    console.log('Input count:', inputs?.length);
    
    inputs?.forEach((input, index) => {
        console.log(`Input ${index}:`, {
            type: input.type,
            disabled: input.disabled,
            readonly: input.readOnly,
            pointerEvents: window.getComputedStyle(input).pointerEvents,
            zIndex: window.getComputedStyle(input).zIndex,
            background: window.getComputedStyle(input).backgroundColor
        });
    });
    
    const backdrops = document.querySelectorAll('.modal-backdrop');
    console.log('Backdrop count:', backdrops.length);
}

// ============================================================================
// 7. INITIALIZATION AND GLOBAL FUNCTIONS
// ============================================================================

// Make functions globally available
window.emergencyCloseModal = emergencyCloseModal;
window.debugModal = debugModal;
window.forceResetModal = forceResetModal;

// Auto-initialize
function autoInitializeModalFix() {
    console.log('🚀 Auto-initializing modal fix...');
    
    // Add CSS fix
    addModalInputFix();
    
    // Initialize modal
    initializeModalFixed();
    
    // Set up keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // ESC to close modal
        if (event.key === 'Escape') {
            emergencyCloseModal();
        }
        
        // Ctrl+Shift+M to debug modal
        if (event.ctrlKey && event.shiftKey && event.key === 'M') {
            debugModal();
        }
    });
    
    console.log('✅ Modal fix initialization complete');
    console.log('💡 If modal still doesn\'t work, try:');
    console.log('   - Press Ctrl+Shift+M to debug');
    console.log('   - Call emergencyCloseModal() in console');
    console.log('   - Press ESC to force close');
}

// Initialize immediately if DOM is ready, otherwise wait
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInitializeModalFix);
} else {
    autoInitializeModalFix();
}

console.log('✅ Modal Input Fix loaded successfully');
console.log('🔧 Available functions: emergencyCloseModal(), debugModal(), forceResetModal()');