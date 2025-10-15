/*
 * Settings Page JavaScript
 * ========================
 * Handles settings page functionality, form interactions, and testing
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeSettingsPage();
});

function initializeSettingsPage() {
    // Initialize auto-save functionality
    initializeAutoSave();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize tooltips and help text
    initializeHelpSystem();
}

function showSection(sectionName) {
    // Check if the clicked tab is feature-locked
    const clickedTab = event.target.closest('.nav-tab');
    if (clickedTab && clickedTab.hasAttribute('data-feature')) {
        const featureName = clickedTab.getAttribute('data-feature');
        
        // Check if feature is available
        if (window.featureLockManager && !window.featureLockManager.hasFeature(featureName)) {
            // Show upgrade prompt instead of switching tabs
            const featureDisplayName = featureName === 'slack_alerts' ? 'Slack Integration' : 'Email Settings';
            window.featureLockManager.showUpgradePrompt(featureDisplayName, 'Pro');
            return;
        }
    }
    
    // Hide all sections
    const sections = document.querySelectorAll('.form-section');
    sections.forEach(section => section.classList.remove('active'));
    
    // Remove active class from all nav tabs
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Show selected section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Add active class to clicked tab
    if (clickedTab) {
        clickedTab.classList.add('active');
    }
}

function testEmail() {
    const form = new FormData();
    form.append('test_email', 'true');
    form.append('smtp_server', document.querySelector('input[name="smtp_server"]').value);
    form.append('smtp_port', document.querySelector('input[name="smtp_port"]').value);
    form.append('smtp_username', document.querySelector('input[name="smtp_username"]').value);
    form.append('smtp_password', document.querySelector('input[name="smtp_password"]').value);
    form.append('from_email', document.querySelector('input[name="from_email"]').value);
    form.append('email_recipients', document.querySelector('input[name="email_recipients"]').value);
    
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    button.disabled = true;
    
    fetch('/test_email', {
        method: 'POST',
        body: form
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Test email sent successfully!', 'success');
        } else {
            showNotification('Test email failed: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showNotification('Error testing email: ' + error, 'error');
    })
    .finally(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function testSlack() {
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    button.disabled = true;
    
    fetch('/test_slack', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Test Slack message sent successfully!', 'success');
        } else {
            showNotification('Slack test failed: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showNotification('Error testing Slack: ' + error, 'error');
    })
    .finally(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function testAzure() {
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    button.disabled = true;
    
    // First save the current Azure settings
    const form = new FormData();
    form.append('section', 'azure');
    form.append('azure_tenant_id', document.querySelector('input[name="azure_tenant_id"]').value);
    form.append('azure_subscription_id', document.querySelector('input[name="azure_subscription_id"]').value);
    form.append('azure_client_id', document.querySelector('input[name="azure_client_id"]').value);
    form.append('azure_client_secret', document.querySelector('input[name="azure_client_secret"]').value);
    
    // Save settings first, then test
    fetch('/save_settings', {
        method: 'POST',
        body: form
    })
    .then(() => {
        // Now test the Azure connection
        return fetch('/test_azure', {
            method: 'POST'
        });
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Azure connection successful! ' + data.message, 'success');
        } else {
            showNotification('Azure connection failed: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showNotification('Error testing Azure connection: ' + error, 'error');
    })
    .finally(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function initializeAutoSave() {
    let saveTimeout;
    const saveButton = document.querySelector('button[type="submit"]');
    
    if (!saveButton) return;
    
    document.querySelectorAll('input, select, textarea').forEach(element => {
        element.addEventListener('input', () => {
            clearTimeout(saveTimeout);
            
            // Show unsaved changes indicator
            saveButton.innerHTML = '<i class="fas fa-circle text-orange-400 mr-1"></i>Unsaved Changes';
            saveButton.classList.add('btn-warning');
            saveButton.classList.remove('btn-primary');
            
            saveTimeout = setTimeout(() => {
                // Reset button to normal state
                saveButton.innerHTML = '<i class="fas fa-save"></i>Save Settings';
                saveButton.classList.remove('btn-warning');
                saveButton.classList.add('btn-primary');
            }, 3000);
        });
    });
}

function initializeFormValidation() {
    const form = document.querySelector('form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        let isValid = true;
        const errors = [];
        
        // Validate Azure Tenant ID format
        const tenantId = document.querySelector('input[name="azure_tenant_id"]');
        if (tenantId && tenantId.value) {
            const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
            if (!uuidRegex.test(tenantId.value)) {
                errors.push('Azure Tenant ID must be a valid UUID format');
                isValid = false;
            }
        }
        
        // Validate Azure Subscription ID format
        const subscriptionId = document.querySelector('input[name="azure_subscription_id"]');
        if (subscriptionId && subscriptionId.value) {
            const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
            if (!uuidRegex.test(subscriptionId.value)) {
                errors.push('Azure Subscription ID must be a valid UUID format');
                isValid = false;
            }
        }
        
        // Validate Azure Client ID format
        const clientId = document.querySelector('input[name="azure_client_id"]');
        if (clientId && clientId.value) {
            const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
            if (!uuidRegex.test(clientId.value)) {
                errors.push('Azure Client ID must be a valid UUID format');
                isValid = false;
            }
        }
        
        // Validate email format
        const emailUsername = document.querySelector('input[name="email_username"]');
        if (emailUsername && emailUsername.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(emailUsername.value)) {
                errors.push('Email username must be a valid email address');
                isValid = false;
            }
        }
        
        // Validate SMTP port
        const smtpPort = document.querySelector('input[name="smtp_port"]');
        if (smtpPort && smtpPort.value) {
            const port = parseInt(smtpPort.value);
            if (isNaN(port) || port < 1 || port > 65535) {
                errors.push('SMTP port must be a number between 1 and 65535');
                isValid = false;
            }
        }
        
        // Validate Slack webhook URL
        const slackWebhook = document.querySelector('input[name="slack_webhook_url"]');
        if (slackWebhook && slackWebhook.value) {
            try {
                const url = new URL(slackWebhook.value);
                if (!url.hostname.includes('hooks.slack.com')) {
                    errors.push('Slack webhook URL must be a valid Slack webhook');
                    isValid = false;
                }
            } catch {
                errors.push('Slack webhook URL must be a valid URL');
                isValid = false;
            }
        }
        
        if (!isValid) {
            e.preventDefault();
            showNotification('Please fix the following errors:\n• ' + errors.join('\n• '), 'error');
        }
    });
}

function initializeHelpSystem() {
    // Add help tooltips to form fields
    const helpTexts = {
        'azure_tenant_id': 'Find this in Azure Portal → Azure Active Directory → Properties → Tenant ID',
        'azure_subscription_id': 'Find this in Azure Portal → Subscriptions → Your subscription → Subscription ID',
        'azure_client_id': 'The Application (client) ID from your registered app',
        'azure_client_secret': 'The client secret value (not the secret ID)',
        'slack_webhook_url': 'Create at https://api.slack.com/apps → Incoming Webhooks',
        'email_username': 'Your SMTP email address for sending notifications',
        'smtp_server': 'SMTP server address (e.g., smtp.gmail.com, smtp.outlook.com)'
    };
    
    Object.keys(helpTexts).forEach(fieldName => {
        const field = document.querySelector(`input[name="${fieldName}"]`);
        if (field) {
            field.setAttribute('title', helpTexts[fieldName]);
        }
    });
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification-toast`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    notification.style.maxWidth = '500px';
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
    
    // Allow manual dismissal on click
    notification.addEventListener('click', () => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    });
}

// Update functions for auto-refresh
function updateSettingsStatus(data) {
    // Refresh any status indicators on the settings page
    console.log('🔄 Settings status updated via auto-refresh');
    
    // Update feature availability if needed
    if (window.featureLockManager && data.features) {
        window.featureLockManager.updateFeatureStatus(data.features);
    }
    
    // Update any status indicators
    const statusElements = document.querySelectorAll('.status-indicator');
    statusElements.forEach(el => {
        el.classList.add('updated');
        setTimeout(() => el.classList.remove('updated'), 1000);
    });
}

function updateLicenseStatus(data) {
    // Update license information if displayed
    console.log('🔄 License status updated via auto-refresh');
    
    if (data.license) {
        // Update license info in any displayed elements
        const licenseElements = document.querySelectorAll('[data-license-info]');
        licenseElements.forEach(el => {
            const info = el.getAttribute('data-license-info');
            if (data.license[info]) {
                el.textContent = data.license[info];
                el.classList.add('updated');
                setTimeout(() => el.classList.remove('updated'), 1000);
            }
        });
    }
}

// Global functions for button clicks
window.showSection = showSection;
window.testEmail = testEmail;
window.testSlack = testSlack;
window.testAzure = testAzure;

// Global functions for auto-refresh
window.updateSettingsStatus = updateSettingsStatus;
window.updateLicenseStatus = updateLicenseStatus;