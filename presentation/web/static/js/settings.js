/**
 * Settings Page JavaScript
 * Handles settings navigation, form management, and configuration persistence
 */

class SettingsPage {
    constructor() {
        this.navLinks = null;
        this.sections = null;
        this.init();
    }

    init() {
        this.bindEventListeners();
        this.loadCurrentSettings();
    }

    bindEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.onDOMContentLoaded();
        });
    }

    onDOMContentLoaded() {
        this.navLinks = document.querySelectorAll('.settings-nav-link');
        this.sections = document.querySelectorAll('.settings-section');
        
        this.setupNavigation();
        this.setupThemeHandler();
        this.loadCurrentSettings();
    }

    // Navigation Management
    setupNavigation() {
        if (!this.navLinks) return;

        this.navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleNavigation(e.target.closest('.settings-nav-link'));
            });
        });
    }

    handleNavigation(link) {
        if (!link) return;

        const targetSection = link.dataset.section;
        
        // Update navigation
        this.navLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        
        // Update sections
        this.sections.forEach(s => s.classList.remove('active'));
        const targetElement = document.getElementById(targetSection + '-section');
        if (targetElement) {
            targetElement.classList.add('active');
        }
    }

    // Settings Management
    loadCurrentSettings() {
        this.loadThemeSetting();
        this.loadSettingsFromAPI();
    }
    
    async loadSettingsFromAPI() {
        try {
            const response = await fetch('/api/settings');
            if (response.ok) {
                const settings = await response.json();
                this.populateFormFields(settings);
            }
        } catch (error) {
            console.error('Error loading settings from API:', error);
        }
    }
    
    populateFormFields(settings) {
        // Map backend field names to UI form field IDs
        const fieldMapping = {
            'AZURE_TENANT_ID': 'azure-tenant-id',
            'AZURE_SUBSCRIPTION_ID': 'azure-subscription-id', 
            'AZURE_CLIENT_ID': 'azure-client-id',
            'AZURE_CLIENT_SECRET': 'azure-client-secret',
            'SLACK_ENABLED': 'slack-notifications',
            'SLACK_WEBHOOK_URL': 'slack-webhook-url',
            'SLACK_CHANNEL': 'slack-channel',
            'EMAIL_ENABLED': 'email-notifications',
            'SMTP_SERVER': 'smtp-server',
            'SMTP_PORT': 'smtp-port',
            'SMTP_USERNAME': 'smtp-username',
            'SMTP_PASSWORD': 'smtp-password',
            'FROM_EMAIL': 'from-email',
            'EMAIL_RECIPIENTS': 'email-recipients',
            'COST_ALERT_THRESHOLD': 'cost-threshold',
            'ANALYSIS_REFRESH_INTERVAL': 'refresh-interval',
            'LOG_LEVEL': 'log-level',
            'PRODUCTION_MODE': 'production-mode',
            'AUTO_ANALYSIS_ENABLED': 'auto-refresh',
            'AUTO_ANALYSIS_INTERVAL': 'auto-analysis-interval'
        };
        
        Object.entries(fieldMapping).forEach(([backendKey, uiFieldId]) => {
            const element = document.getElementById(uiFieldId);
            const value = settings[backendKey];
            
            if (element && value !== undefined) {
                if (element.type === 'checkbox') {
                    element.checked = value === 'true' || value === true;
                } else {
                    element.value = value;
                }
            }
        });
    }
    
    mapToBackendFields(settings) {
        // Map UI settings to backend expected field names
        const backendMapping = {
            theme: 'theme',
            autoRefresh: 'auto_analysis_enabled',
            refreshInterval: 'analysis_refresh_interval',
            emailNotifications: 'email_enabled',
            slackNotifications: 'slack_enabled',
            costThreshold: 'cost_alert_threshold',
            defaultSubscription: 'azure_subscription_id',
            costApi: 'cost_api_enabled',
            sessionTimeout: 'session_timeout',
            auditLogging: 'audit_logging',
            debugMode: 'debug_mode',
            rateLimit: 'rate_limit',
            cacheDuration: 'cache_duration'
        };
        
        const backendSettings = {};
        Object.entries(settings).forEach(([key, value]) => {
            const backendKey = backendMapping[key] || key;
            backendSettings[backendKey] = value;
        });
        
        return backendSettings;
    }
    
    validateCurrentSettings() {
        const errors = [];
        
        // Validate cost threshold
        const costThreshold = document.getElementById('cost-threshold')?.value;
        if (costThreshold && (isNaN(parseFloat(costThreshold)) || parseFloat(costThreshold) < 0)) {
            errors.push('Cost threshold must be a positive number');
        }
        
        // Validate refresh interval
        const refreshInterval = document.getElementById('refresh-interval')?.value;
        if (refreshInterval && (isNaN(parseInt(refreshInterval)) || parseInt(refreshInterval) < 1)) {
            errors.push('Refresh interval must be a positive number');
        }
        
        // Validate rate limit
        const rateLimit = document.getElementById('rate-limit')?.value;
        if (rateLimit && (isNaN(parseInt(rateLimit)) || parseInt(rateLimit) < 1)) {
            errors.push('Rate limit must be a positive number');
        }
        
        return errors;
    }

    loadThemeSetting() {
        const currentTheme = localStorage.getItem('theme') || 'light';
        const themeSelect = document.getElementById('theme-setting');
        if (themeSelect) {
            themeSelect.value = currentTheme;
        }
    }

    setupThemeHandler() {
        const themeSelect = document.getElementById('theme-setting');
        if (themeSelect) {
            themeSelect.addEventListener('change', (e) => {
                const theme = e.target.value;
                if (theme !== 'auto') {
                    document.documentElement.setAttribute('data-theme', theme);
                }
            });
        }
    }

    // Settings Actions
    async saveSettings() {
        const validationErrors = this.validateCurrentSettings();
        if (validationErrors.length > 0) {
            this.showValidationErrors(validationErrors);
            return;
        }
        
        const settings = this.gatherSettingsData();
        
        // Save theme immediately to localStorage
        localStorage.setItem('theme', settings.theme);
        document.documentElement.setAttribute('data-theme', settings.theme);
        
        try {
            // Save to backend API
            await this.saveToAPI(settings);
                this.showToast('Settings saved successfully', 'success');
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showToast('Failed to save settings: ' + error.message, 'error');
        }
    }

    gatherSettingsData() {
        return {
            theme: document.getElementById('theme-setting')?.value || 'light',
            autoRefresh: document.getElementById('auto-refresh')?.checked || false,
            refreshInterval: document.getElementById('refresh-interval')?.value || '5',
            emailNotifications: document.getElementById('email-notifications')?.checked || false,
            slackNotifications: document.getElementById('slack-notifications')?.checked || false,
            costThreshold: document.getElementById('cost-threshold')?.value || '',
            defaultSubscription: document.getElementById('default-subscription')?.value || '',
            costApi: document.getElementById('cost-api')?.checked || false,
            sessionTimeout: document.getElementById('session-timeout')?.value || '60',
            auditLogging: document.getElementById('audit-logging')?.checked || false,
            debugMode: document.getElementById('debug-mode')?.checked || false,
            rateLimit: document.getElementById('rate-limit')?.value || '60',
            cacheDuration: document.getElementById('cache-duration')?.value || '1800',
            
            // Additional fields for backend integration
            azureTenantId: document.getElementById('azure-tenant-id')?.value || '',
            azureSubscriptionId: document.getElementById('azure-subscription-id')?.value || '',
            azureClientId: document.getElementById('azure-client-id')?.value || '',
            azureClientSecret: document.getElementById('azure-client-secret')?.value || '',
            slackWebhookUrl: document.getElementById('slack-webhook-url')?.value || '',
            slackChannel: document.getElementById('slack-channel')?.value || '',
            smtpServer: document.getElementById('smtp-server')?.value || '',
            smtpPort: document.getElementById('smtp-port')?.value || '',
            smtpUsername: document.getElementById('smtp-username')?.value || '',
            smtpPassword: document.getElementById('smtp-password')?.value || '',
            fromEmail: document.getElementById('from-email')?.value || '',
            emailRecipients: document.getElementById('email-recipients')?.value || ''
        };
    }

    async saveToAPI(settings) {
        try {
            // Map UI field names to backend field names
            const backendSettings = this.mapToBackendFields(settings);
            
            // Create FormData for the API call
            const formData = new FormData();
            Object.entries(backendSettings).forEach(([key, value]) => {
                formData.append(key, value);
            });
            
            const response = await fetch('/save_settings', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                console.log('Settings saved successfully:', settings);
            } else {
                throw new Error(data.message || 'Failed to save settings');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            throw error; // Re-throw for proper error handling in saveSettings
        }
    }

    resetSettings() {
        if (confirm('Are you sure you want to reset all settings to defaults?')) {
            this.loadDefaultSettings();
            this.showToast('Settings reset to defaults', 'info');
        }
    }

    loadDefaultSettings() {
        // Reset all form elements to their default values
        const defaults = {
            'theme-setting': 'light',
            'auto-refresh': true,
            'refresh-interval': '5',
            'email-notifications': false,
            'slack-notifications': false,
            'cost-threshold': '',
            'default-subscription': '',
            'cost-api': true,
            'session-timeout': '60',
            'audit-logging': true,
            'debug-mode': false,
            'rate-limit': '60',
            'cache-duration': '1800'
        };

        Object.entries(defaults).forEach(([elementId, value]) => {
            const element = document.getElementById(elementId);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = value;
                } else {
                    element.value = value;
                }
            }
        });

        // Apply theme immediately
        localStorage.setItem('theme', 'light');
        document.documentElement.setAttribute('data-theme', 'light');
    }

    // Azure Integration Actions
    async testAzureConnection() {
        this.showToast('Testing Azure connection...', 'info');
        
        try {
            // First save current Azure settings before testing
            const azureSettings = {
                azure_tenant_id: document.getElementById('azure-tenant-id')?.value || '',
                azure_subscription_id: document.getElementById('azure-subscription-id')?.value || '',
                azure_client_id: document.getElementById('azure-client-id')?.value || '',
                azure_client_secret: document.getElementById('azure-client-secret')?.value || ''
            };
            
            // Save Azure settings first
            const formData = new FormData();
            formData.append('section', 'azure');
            Object.entries(azureSettings).forEach(([key, value]) => {
                formData.append(key, value);
            });
            
            await fetch('/save_settings', {
                method: 'POST',
                body: formData
            });
            
            // Now test the connection
            const response = await fetch('/test_azure', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Azure connection test successful! ' + result.message, 'success');
            } else {
                this.showToast('Azure connection test failed: ' + result.message, 'error');
            }
            
        } catch (error) {
            console.error('Azure connection test failed:', error);
            this.showToast('Azure connection test failed: ' + error.message, 'error');
        }
    }

    async refreshSubscriptions() {
        this.showToast('Refreshing Azure subscriptions...', 'info');
        
        try {
            const response = await fetch('/api/azure/subscriptions', { method: 'GET' });
            const result = await response.json();
            
            if (result.success && result.subscriptions) {
                this.updateSubscriptionDropdown(result.subscriptions);
                this.showToast('Azure subscriptions refreshed', 'success');
            } else {
                this.showToast('Failed to refresh subscriptions: ' + (result.message || 'Unknown error'), 'error');
            }
            
        } catch (error) {
            console.error('Failed to refresh subscriptions:', error);
            this.showToast('Failed to refresh subscriptions: ' + error.message, 'error');
        }
    }
    
    async testSlackIntegration() {
        this.showToast('Testing Slack integration...', 'info');
        
        try {
            const response = await fetch('/test_slack', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Slack test message sent successfully! ' + result.message, 'success');
            } else {
                this.showToast('Slack test failed: ' + result.message, 'error');
            }
            
        } catch (error) {
            console.error('Slack test failed:', error);
            this.showToast('Slack test failed: ' + error.message, 'error');
        }
    }
    
    async testEmailConfiguration() {
        this.showToast('Testing email configuration...', 'info');
        
        try {
            const formData = new FormData();
            formData.append('test_email', 'true');
            formData.append('smtp_server', document.getElementById('smtp-server')?.value || '');
            formData.append('smtp_port', document.getElementById('smtp-port')?.value || '');
            formData.append('smtp_username', document.getElementById('smtp-username')?.value || '');
            formData.append('smtp_password', document.getElementById('smtp-password')?.value || '');
            formData.append('from_email', document.getElementById('from-email')?.value || '');
            formData.append('email_recipients', document.getElementById('email-recipients')?.value || '');
            
            const response = await fetch('/test_email', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Test email sent successfully! ' + result.message, 'success');
            } else {
                this.showToast('Email test failed: ' + result.message, 'error');
            }
            
        } catch (error) {
            console.error('Email test failed:', error);
            this.showToast('Email test failed: ' + error.message, 'error');
        }
    }

    updateSubscriptionDropdown(subscriptions = []) {
        const dropdown = document.getElementById('default-subscription');
        if (dropdown && subscriptions) {
            // Clear existing options except the first one
            while (dropdown.children.length > 1) {
                dropdown.removeChild(dropdown.lastChild);
            }
            
            // Add new subscription options
            subscriptions.forEach(sub => {
                const option = document.createElement('option');
                option.value = sub.subscriptionId;
                option.textContent = `${sub.displayName} (${sub.subscriptionId.substring(0, 8)}...)`;
                dropdown.appendChild(option);
            });
            
            console.log(`Updated subscription dropdown with ${subscriptions.length} subscriptions`);
        }
    }

    // Advanced Actions
    clearCache() {
        if (confirm('Are you sure you want to clear the cache? This action cannot be undone.')) {
            this.performCacheClear();
        }
    }

    async performCacheClear() {
        try {
            const response = await fetch('/api/cache/clear', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Cache cleared successfully', 'success');
            } else {
                throw new Error(result.message || 'Unknown error');
            }
            
        } catch (error) {
            console.error('Failed to clear cache:', error);
            this.showToast('Failed to clear cache: ' + error.message, 'error');
        }
    }

    exportSettings() {
        this.showToast('Exporting settings...', 'info');
        
        try {
            const settings = this.gatherSettingsData();
            const settingsBlob = new Blob([JSON.stringify(settings, null, 2)], {
                type: 'application/json'
            });
            
            const url = URL.createObjectURL(settingsBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'aks-optimizer-settings.json';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            URL.revokeObjectURL(url);
            
            this.showToast('Settings exported successfully', 'success');
            
        } catch (error) {
            console.error('Failed to export settings:', error);
            this.showToast('Failed to export settings', 'error');
        }
    }

    // Utility Methods
    validateSettings(settings) {
        const errors = [];

        if (settings.costThreshold && isNaN(parseFloat(settings.costThreshold))) {
            errors.push('Cost threshold must be a valid number');
        }

        if (settings.rateLimit && (isNaN(parseInt(settings.rateLimit)) || parseInt(settings.rateLimit) < 1)) {
            errors.push('Rate limit must be a positive number');
        }

        return errors;
    }

    showValidationErrors(errors) {
        errors.forEach(error => {
            this.showToast(error, 'error');
        });
    }
    
    showToast(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `flash-message flash-${type}`;
        
        // Create message content
        const messageSpan = document.createElement('span');
        messageSpan.textContent = message;
        
        // Create close button
        const closeBtn = document.createElement('button');
        closeBtn.className = 'flash-close';
        closeBtn.innerHTML = '×';
        closeBtn.onclick = () => notification.remove();
        
        notification.appendChild(messageSpan);
        notification.appendChild(closeBtn);
        
        // Add to flash messages container
        let flashContainer = document.querySelector('.flash-messages');
        if (!flashContainer) {
            flashContainer = document.createElement('div');
            flashContainer.className = 'flash-messages';
            document.body.appendChild(flashContainer);
        }
        
        flashContainer.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize the settings page when DOM is loaded
let settingsPage;

document.addEventListener('DOMContentLoaded', function() {
    settingsPage = new SettingsPage();
});

// Working backend integration functions from backup
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
            showToast('Azure connection successful! ' + data.message, 'success');
        } else {
            showToast('Azure connection failed: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showToast('Error testing Azure connection: ' + error, 'error');
    })
    .finally(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    });
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
            showToast('Test email sent successfully!', 'success');
        } else {
            showToast('Test email failed: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showToast('Error testing email: ' + error, 'error');
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
            showToast('Test Slack message sent successfully!', 'success');
        } else {
            showToast('Slack test failed: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showToast('Error testing Slack: ' + error, 'error');
    })
    .finally(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function showToast(message, type = 'info') {
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
    notification.style.padding = '1rem';
    notification.style.borderRadius = '0.5rem';
    notification.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.1)';
    notification.style.fontWeight = '500';
    
    // Set colors based on type
    if (type === 'success') {
        notification.style.background = '#10b981';
        notification.style.color = 'white';
    } else if (type === 'error') {
        notification.style.background = '#ef4444';
        notification.style.color = 'white';
    } else {
        notification.style.background = '#3b82f6';
        notification.style.color = 'white';
    }
    
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

// Global functions for template onclick handlers
function testAzureConnection() {
    settingsPage?.testAzureConnection();
}

function refreshSubscriptions() {
    settingsPage?.refreshSubscriptions();
}

function clearCache() {
    settingsPage?.clearCache();
}

function exportSettings() {
    settingsPage?.exportSettings();
}

function resetSettings() {
    settingsPage?.resetSettings();
}

function saveSettings() {
    settingsPage?.saveSettings();
}

// Navigation function for settings tabs
function showSection(sectionName) {
    // Hide all sections
    const sections = document.querySelectorAll('.settings-section');
    sections.forEach(section => section.classList.remove('active'));
    
    // Remove active class from all nav links
    const links = document.querySelectorAll('.settings-nav-link');
    links.forEach(link => link.classList.remove('active'));
    
    // Show selected section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Add active class to clicked link
    const targetLink = document.querySelector(`[data-section="${sectionName}"]`);
    if (targetLink) {
        targetLink.classList.add('active');
    }
}