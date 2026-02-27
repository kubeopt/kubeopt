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
        
        // Update sections - use the same logic as showSection() function
        this.sections.forEach(s => {
            s.classList.remove('active');
            s.style.display = 'none';  // Force hide like showSection does
        });
        const targetElement = document.getElementById(targetSection + '-section');
        if (targetElement) {
            targetElement.classList.add('active');
            targetElement.style.display = 'block';  // Force show like showSection does
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
            window.logger.error('Error loading settings from API:', error);
        }
    }
    
    populateFormFields(settings) {
        // Map backend field names to UI form field IDs
        // Support both uppercase (from env) and lowercase (from some endpoints)
        const fieldMapping = {
            'AZURE_TENANT_ID': 'azure-tenant-id',
            'AZURE_CLIENT_ID': 'azure-client-id',
            'AZURE_CLIENT_SECRET': 'azure-client-secret',
            'SLACK_ENABLED': 'slack-enabled',
            'SLACK_WEBHOOK_URL': 'slack-webhook-url',
            'SLACK_CHANNEL': 'slack-channel',
            'SLACK_COST_THRESHOLD': 'slack-cost-threshold',
            'APP_URL': 'app-url',
            'EMAIL_ENABLED': 'email-enabled',
            'SMTP_SERVER': 'smtp-server',
            'SMTP_PORT': 'smtp-port',
            'SMTP_USERNAME': 'smtp-username',
            'SMTP_PASSWORD': 'smtp-password',
            'FROM_EMAIL': 'from-email',
            'EMAIL_RECIPIENTS': 'email-recipients',
            'COST_ALERT_THRESHOLD': 'cost-threshold',
            'COST_CACHE_HOURS': 'cost-cache-hours',
            'ANALYSIS_REFRESH_INTERVAL': 'refresh-interval',
            'LOG_LEVEL': 'log-level',
            'PRODUCTION_MODE': 'production-mode',
            'AUTO_ANALYSIS_ENABLED': 'auto-analysis-enabled',
            'AUTO_ANALYSIS_INTERVAL': 'auto-analysis-interval',
            'DATABASE_CLEANUP_ENABLED': 'database-cleanup-enabled',
            'DATABASE_CLEANUP_INTERVAL_HOURS': 'database-cleanup-interval',
            'DATABASE_RETENTION_DAYS': 'database-retention-days',
            'SESSION_TIMEOUT': 'session-timeout',
            'JWT_SECRET_KEY': 'jwt-secret-key',
            'JWT_EXPIRY_MINUTES': 'jwt-expiry-minutes',
            'LOCAL_DEV': 'local-dev',
            'KUBEOPT_ENV': 'kubeopt-env',
            'LICENSE_API_URL': 'license-api-url',
            'PLAN_API_URL': 'plan-api-url',
            'TEST_KEY': 'test-key',
            'USER_PASSWORD_HASH': 'user-password-hash',
            'USER_ROLE': 'user-role', 
            'USER_USERNAME': 'user-username',
            'USER_ZDOTDIR': 'user-zdotdir',
            'KUBEOPT_LICENSE_KEY': 'license-key',
            // AI Configuration
            'AI_MODEL': 'ai-model',
            'ANTHROPIC_API_KEY': 'anthropic-api-key',
            'AI_ENABLE_COST_TRACKING': 'ai-cost-tracking',
            'AI_MAX_CONTEXT_TOKENS': 'ai-max-context',
            'AI_MAX_OUTPUT_TOKENS': 'ai-max-output',
            'AI_MAX_RETRIES': 'ai-max-retries',
            'AI_USE_SPLIT_MODE': 'ai-split-mode'
        };
        
        Object.entries(fieldMapping).forEach(([backendKey, uiFieldId]) => {
            const element = document.getElementById(uiFieldId);
            
            // Check for both uppercase (from env) and lowercase versions
            const upperKey = backendKey;
            const lowerKey = backendKey.toLowerCase();
            const value = settings[upperKey] || settings[lowerKey];
            
            if (element && value !== undefined && value !== null) {
                if (element.type === 'checkbox') {
                    element.checked = value === 'true' || value === true;
                } else {
                    element.value = value;
                }
            }
        });
    }
    
    mapToBackendFields(settings) {
        // Map UI settings to backend expected field names (matching .env keys)
        const backendMapping = {
            // General Settings
            theme: 'theme',
            appUrl: 'APP_URL',
            productionMode: 'PRODUCTION_MODE',
            
            // Azure Settings
            azureTenantId: 'AZURE_TENANT_ID',
            azureSubscriptionId: 'AZURE_SUBSCRIPTION_ID',
            azureClientId: 'AZURE_CLIENT_ID',
            azureClientSecret: 'AZURE_CLIENT_SECRET',
            
            // Notifications
            emailEnabled: 'EMAIL_ENABLED',
            slackEnabled: 'SLACK_ENABLED',
            slackWebhookUrl: 'SLACK_WEBHOOK_URL',
            slackChannel: 'SLACK_CHANNEL',
            slackCostThreshold: 'SLACK_COST_THRESHOLD',
            smtpServer: 'SMTP_SERVER',
            smtpPort: 'SMTP_PORT',
            smtpUsername: 'SMTP_USERNAME',
            smtpPassword: 'SMTP_PASSWORD',
            fromEmail: 'FROM_EMAIL',
            emailRecipients: 'EMAIL_RECIPIENTS',
            
            // Advanced - Auto Analysis
            autoAnalysisEnabled: 'AUTO_ANALYSIS_ENABLED',
            autoAnalysisInterval: 'AUTO_ANALYSIS_INTERVAL',
            
            // Advanced - AI Configuration
            aiModel: 'AI_MODEL',
            anthropicApiKey: 'ANTHROPIC_API_KEY',
            aiEnableCostTracking: 'AI_ENABLE_COST_TRACKING',
            aiMaxContextTokens: 'AI_MAX_CONTEXT_TOKENS',
            aiMaxOutputTokens: 'AI_MAX_OUTPUT_TOKENS',
            aiMaxRetries: 'AI_MAX_RETRIES',
            aiUseSplitMode: 'AI_USE_SPLIT_MODE',
            
            // Advanced - API Configuration
            licenseApiUrl: 'LICENSE_API_URL',
            planApiUrl: 'PLAN_API_URL',
            
            // Advanced - Developer Options
            localDev: 'LOCAL_DEV',
            logLevel: 'LOG_LEVEL',
            costThreshold: 'COST_ALERT_THRESHOLD',
            costCacheHours: 'COST_CACHE_HOURS',
            
            // Database Settings
            databaseCleanupEnabled: 'DATABASE_CLEANUP_ENABLED',
            databaseCleanupIntervalHours: 'DATABASE_CLEANUP_INTERVAL_HOURS',
            databaseRetentionDays: 'DATABASE_RETENTION_DAYS',
            
            // Environment Settings  
            kubeoptEnv: 'KUBEOPT_ENV',
            testKey: 'TEST_KEY',
            userPasswordHash: 'USER_PASSWORD_HASH',
            userRole: 'USER_ROLE', 
            userUsername: 'USER_USERNAME',
            userZdotdir: 'USER_ZDOTDIR',
            
            // Slack specific settings
            slackCostThreshold: 'SLACK_COST_THRESHOLD',
            
            // Security
            sessionTimeout: 'SESSION_TIMEOUT',
            
            // License
            kubeoptLicenseKey: 'KUBEOPT_LICENSE_KEY'
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
            window.logger.error('Error saving settings:', error);
            this.showToast('Failed to save settings: ' + error.message, 'error');
        }
    }

    gatherSettingsData() {
        return {
            // General Settings
            theme: document.getElementById('theme-setting')?.value || 'light',
            appUrl: document.getElementById('app-url')?.value || '',
            productionMode: document.getElementById('production-mode')?.checked || false,
            
            // Azure Settings
            azureTenantId: document.getElementById('azure-tenant-id')?.value || '',
            azureSubscriptionId: document.getElementById('azure-subscription-id')?.value || '',
            azureClientId: document.getElementById('azure-client-id')?.value || '',
            azureClientSecret: document.getElementById('azure-client-secret')?.value || '',
            
            // Notifications
            emailEnabled: document.getElementById('email-enabled')?.checked || false,
            slackEnabled: document.getElementById('slack-enabled')?.checked || false,
            slackWebhookUrl: document.getElementById('slack-webhook-url')?.value || '',
            slackChannel: document.getElementById('slack-channel')?.value || '',
            slackCostThreshold: document.getElementById('slack-cost-threshold')?.value || '',
            smtpServer: document.getElementById('smtp-server')?.value || '',
            smtpPort: document.getElementById('smtp-port')?.value || '',
            smtpUsername: document.getElementById('smtp-username')?.value || '',
            smtpPassword: document.getElementById('smtp-password')?.value || '',
            fromEmail: document.getElementById('from-email')?.value || '',
            emailRecipients: document.getElementById('email-recipients')?.value || '',
            
            // Advanced - Auto Analysis
            autoAnalysisEnabled: document.getElementById('auto-analysis-enabled')?.checked || false,
            autoAnalysisInterval: document.getElementById('auto-analysis-interval')?.value || '240',
            
            // Advanced - AI Configuration
            aiModel: document.getElementById('ai-model')?.value || '',
            anthropicApiKey: document.getElementById('anthropic-api-key')?.value || '',
            aiEnableCostTracking: document.getElementById('ai-cost-tracking')?.checked || false,
            aiMaxContextTokens: document.getElementById('ai-max-context')?.value || '',
            aiMaxOutputTokens: document.getElementById('ai-max-output')?.value || '',
            aiMaxRetries: document.getElementById('ai-max-retries')?.value || '',
            aiUseSplitMode: document.getElementById('ai-split-mode')?.checked || false,
            
            // Advanced - API Configuration
            licenseApiUrl: document.getElementById('license-api-url')?.value || '',
            planApiUrl: document.getElementById('plan-api-url')?.value || '',
            
            // Advanced - Developer Options
            localDev: document.getElementById('local-dev')?.checked || false,
            logLevel: document.getElementById('log-level')?.value || 'INFO',
            
            // Security
            sessionTimeout: document.getElementById('session-timeout')?.value || '60',
            
            // License
            kubeoptLicenseKey: document.getElementById('license-key')?.value || ''
        };
    }

    async saveToAPI(settings) {
        try {
            // Map UI field names to backend field names
            const backendSettings = this.mapToBackendFields(settings);
            
            // Use the new API endpoint that accepts JSON
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(backendSettings)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success || data.status === 'success') {
                window.logger.debug('Settings saved successfully');
                
                // If license key was updated, show success message instead of reload
                if (backendSettings.KUBEOPT_LICENSE_KEY) {
                    window.logger.debug('License key updated successfully - no reload needed');
                }
            } else {
                throw new Error(data.message || 'Failed to save settings');
            }
        } catch (error) {
            window.logger.error('Error saving settings:', error);
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
            window.logger.error('Azure connection test failed:', error);
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
            window.logger.error('Failed to refresh subscriptions:', error);
            this.showToast('Failed to refresh subscriptions: ' + error.message, 'error');
        }
    }
    
    async testSlackIntegration() {
        this.showToast('Testing Slack integration...', 'info');
        
        try {
            // Get current form values (like Azure test does)
            const formData = new FormData();
            const webhookUrl = document.getElementById('slack-webhook-url')?.value || '';
            const channel = document.getElementById('slack-channel')?.value || '';
            
            formData.append('slack_webhook_url', webhookUrl);
            formData.append('slack_channel', channel);
            
            const response = await fetch('/test_slack', { 
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Slack test message sent successfully! ' + result.message, 'success');
            } else {
                this.showToast('Slack test failed: ' + result.message, 'error');
            }
            
        } catch (error) {
            window.logger.error('Slack test failed:', error);
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
            window.logger.error('Email test failed:', error);
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
            
            window.logger.debug(`Updated subscription dropdown with ${subscriptions.length} subscriptions`);
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
            window.logger.error('Failed to clear cache:', error);
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
            window.logger.error('Failed to export settings:', error);
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

// Auto-save functionality for individual settings
class AutoSaveHandler {
    constructor() {
        this.saveTimeout = null;
        this.init();
    }
    
    init() {
        // Auto-save for dropdowns and checkboxes
        this.setupImmediateAutoSave();
        // Auto-save for text inputs with debouncing
        this.setupDebouncedAutoSave();
    }
    
    setupImmediateAutoSave() {
        // Log Level dropdown
        const logLevel = document.getElementById('log-level');
        if (logLevel) {
            logLevel.addEventListener('change', (e) => {
                this.saveSetting('LOG_LEVEL', e.target.value, e.target);
            });
        }
        
        // Session Timeout dropdown
        const sessionTimeout = document.getElementById('session-timeout');
        if (sessionTimeout) {
            sessionTimeout.addEventListener('change', (e) => {
                this.saveSetting('SESSION_TIMEOUT', e.target.value, e.target);
            });
        }
        
        // Auto-Analysis toggle
        const autoAnalysis = document.getElementById('auto-analysis-enabled');
        if (autoAnalysis) {
            autoAnalysis.addEventListener('change', (e) => {
                this.saveSetting('AUTO_ANALYSIS_ENABLED', e.target.checked ? 'true' : 'false', e.target);
            });
        }
    }
    
    setupDebouncedAutoSave() {
        // Auto-Analysis Interval
        const autoInterval = document.querySelector('input[name="auto_analysis_interval"]');
        if (autoInterval) {
            autoInterval.addEventListener('blur', (e) => {
                if (e.target.value.trim()) {
                    this.saveSetting('AUTO_ANALYSIS_INTERVAL', e.target.value, e.target);
                }
            });
        }
        
        // License Key - save on blur
        const licenseKey = document.getElementById('license-key');
        if (licenseKey) {
            licenseKey.addEventListener('blur', (e) => {
                const value = e.target.value.trim();
                if (value && value.length > 10) {
                    this.saveSetting('KUBEOPT_LICENSE_KEY', value, e.target);
                }
            });
        }
    }
    
    async saveSetting(key, value, element) {
        // Show saving indicator
        this.showSavingFeedback(element, 'saving');
        
        try {
            const response = await fetch('/api/settings/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ key, value })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showSavingFeedback(element, 'success');
                
                // Special handling for license key
                if (key === 'KUBEOPT_LICENSE_KEY' && data.license_info) {
                    // Update license display
                    const licenseDisplay = document.querySelector('.setting-description strong');
                    if (licenseDisplay) {
                        licenseDisplay.textContent = data.license_info.tier || 'Free';
                    }
                    // Show toast for license changes since it's important
                    this.showToast(data.message || 'License activated successfully', 'success');
                    // Update UI dynamically instead of reloading
                    window.logger.debug('License updated dynamically - no page reload needed');
                }
            } else {
                this.showSavingFeedback(element, 'error');
                // Only show toast for errors, not for normal saves
                this.showToast(data.error || 'Failed to save setting', 'error');
            }
        } catch (error) {
            window.logger.error('Error saving setting:', error);
            this.showSavingFeedback(element, 'error');
            this.showToast('Network error while saving', 'error');
        }
    }
    
    showSavingFeedback(element, status) {
        // Remove any existing feedback
        const existingFeedback = element.parentElement.querySelector('.save-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }
        
        // Only show subtle feedback for success and errors
        if (status === 'saving') {
            return; // Don't show saving state - just save silently
        }
        
        // Create subtle feedback element
        const feedback = document.createElement('span');
        feedback.className = 'save-feedback';
        feedback.style.marginLeft = '8px';
        feedback.style.fontSize = '12px';
        feedback.style.opacity = '0';
        feedback.style.transition = 'opacity 0.3s ease';
        
        switch (status) {
            case 'success':
                feedback.innerHTML = '<i class="fas fa-check" style="font-size: 10px;"></i>';
                feedback.style.color = '#10b981';
                feedback.style.opacity = '0.7';
                // Fade out gently after 2 seconds
                setTimeout(() => {
                    feedback.style.opacity = '0';
                    setTimeout(() => feedback.remove(), 300);
                }, 2000);
                break;
            case 'error':
                feedback.innerHTML = '<i class="fas fa-exclamation-triangle" style="font-size: 10px;"></i>';
                feedback.style.color = '#ef4444';
                feedback.style.opacity = '0.8';
                // Keep error visible longer
                setTimeout(() => {
                    feedback.style.opacity = '0';
                    setTimeout(() => feedback.remove(), 300);
                }, 4000);
                break;
        }
        
        element.parentElement.appendChild(feedback);
        
        // Trigger fade in
        setTimeout(() => {
            feedback.style.opacity = feedback.style.opacity;
        }, 10);
    }
    
    showToast(message, type = 'info') {
        if (window.settingsPage) {
            window.settingsPage.showToast(message, type);
        } else {
            window.logger.debug(`[${type}] ${message}`);
        }
    }
}

// Initialize the settings page when DOM is loaded
let settingsPage;
let autoSaveHandler;

document.addEventListener('DOMContentLoaded', function() {
    settingsPage = new SettingsPage();
    autoSaveHandler = new AutoSaveHandler();
});

// Working backend integration functions from backup
function testAzure() {
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    button.disabled = true;
    
    // Get current form values without saving them
    const testData = new FormData();
    testData.append('test_azure', 'true');
    
    // Get form values (subscription_id is optional)
    const tenantField = document.querySelector('input[name="azure_tenant_id"]');
    const subscriptionField = document.querySelector('input[name="azure_subscription_id"]'); // Optional
    const clientIdField = document.querySelector('input[name="azure_client_id"]');
    const clientSecretField = document.querySelector('input[name="azure_client_secret"]');
    
    testData.append('azure_tenant_id', tenantField ? tenantField.value : '');
    testData.append('azure_subscription_id', subscriptionField ? subscriptionField.value : ''); // Optional
    testData.append('azure_client_id', clientIdField ? clientIdField.value : '');
    testData.append('azure_client_secret', clientSecretField ? clientSecretField.value : '');
    
    // Test Azure connection with form values (without saving)
    fetch('/test_azure', {
        method: 'POST',
        body: testData
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
    
    // Get current form values (like Azure test does)
    const formData = new FormData();
    const webhookUrl = document.getElementById('slack-webhook-url')?.value || '';
    const channel = document.getElementById('slack-channel')?.value || '';
    
    formData.append('slack_webhook_url', webhookUrl);
    formData.append('slack_channel', channel);
    
    fetch('/test_slack', {
        method: 'POST',
        body: formData
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
    sections.forEach(section => {
        section.classList.remove('active');
        section.style.display = 'none';  // Force hide
    });
    
    // Remove active class from all nav links
    const links = document.querySelectorAll('.settings-nav-link');
    links.forEach(link => link.classList.remove('active'));
    
    // Show selected section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.classList.add('active');
        targetSection.style.display = 'block';  // Force show
    }
    
    // Add active class to clicked link
    const targetLink = document.querySelector(`[data-section="${sectionName}"]`);
    if (targetLink) {
        targetLink.classList.add('active');
    }
}

// Handle hash navigation on page load
function handleHashNavigation() {
    const hash = window.location.hash.substring(1); // Remove the #
    if (hash && ['general', 'notifications', 'azure', 'aws', 'gcp', 'security', 'advanced', 'user', 'support'].includes(hash)) {
        showSection(hash);
    } else {
        // Default to general section if no valid hash
        showSection('general');
    }
}

// Listen for hash changes
window.addEventListener('hashchange', handleHashNavigation);

// Initialize hash navigation on page load
document.addEventListener('DOMContentLoaded', function() {
    // Small delay to ensure DOM is fully ready
    setTimeout(handleHashNavigation, 100);
});

// Accordion toggle for Service Principal Setup Guide
function toggleAccordion(id) {
    const content = document.getElementById(id);
    if (!content) return;
    const header = content.previousElementSibling;
    const chevron = header ? header.querySelector('.accordion-chevron') : null;

    content.classList.toggle('expanded');
    if (chevron) {
        chevron.style.transform = content.classList.contains('expanded') ? 'rotate(90deg)' : '';
    }
}

// Reset profile form function
function resetProfileForm() {
    const form = document.getElementById('profile-form');
    if (form) {
        // Reset all password fields
        document.getElementById('current-password').value = '';
        document.getElementById('new-password').value = '';
        document.getElementById('confirm-password').value = '';
        
        // Reset username to original value (if it was changed)
        const originalUsername = form.querySelector('#profile-username').defaultValue;
        if (originalUsername) {
            document.getElementById('profile-username').value = originalUsername;
        }
        
        showToast('Form reset successfully', 'info');
    }
}

// Notification Settings Functions
async function saveNotificationSettings() {
    const formData = new FormData();
    
    // Email settings
    const emailEnabled = document.getElementById('email-enabled')?.checked || false;
    formData.append('section', 'email');
    formData.append('email_enabled', emailEnabled);
    
    if (emailEnabled) {
        formData.append('smtp_server', document.getElementById('smtp-server')?.value || '');
        formData.append('smtp_port', document.getElementById('smtp-port')?.value || '587');
        formData.append('smtp_username', document.getElementById('smtp-username')?.value || '');
        formData.append('smtp_password', document.getElementById('smtp-password')?.value || '');
        formData.append('from_email', document.getElementById('from-email')?.value || '');
        formData.append('email_recipients', document.getElementById('email-recipients')?.value || '');
    }
    
    try {
        // Save email settings
        const emailResponse = await fetch('/save_settings', {
            method: 'POST',
            body: formData
        });
        
        // Save Slack settings
        const slackFormData = new FormData();
        const slackEnabled = document.getElementById('slack-enabled')?.checked || false;
        slackFormData.append('section', 'slack');
        slackFormData.append('slack_enabled', slackEnabled);
        
        if (slackEnabled) {
            slackFormData.append('slack_webhook_url', document.getElementById('slack-webhook-url')?.value || '');
            slackFormData.append('slack_channel', document.getElementById('slack-channel')?.value || '');
            slackFormData.append('slack_cost_threshold', document.getElementById('slack-cost-threshold')?.value || '');
        }
        
        const slackResponse = await fetch('/save_settings', {
            method: 'POST',
            body: slackFormData
        });
        
        if (emailResponse.ok && slackResponse.ok) {
            showToast('Notification settings saved successfully!', 'success');
            loadNotificationSettings();
        } else {
            showToast('Failed to save notification settings', 'error');
        }
    } catch (error) {
        window.logger.error('Error saving notification settings:', error);
        showToast('Error saving notification settings', 'error');
    }
}

async function loadNotificationSettings() {
    try {
        const response = await fetch('/get_settings');
        if (!response.ok) return;
        
        const settings = await response.json();
        
        // Email settings
        const emailCheckbox = document.getElementById('email-enabled');
        if (emailCheckbox) {
            // Check both uppercase (from env) and lowercase (from some endpoints)
            emailCheckbox.checked = settings.EMAIL_ENABLED === 'true' || settings.email_enabled === 'true';
            document.getElementById('email-config').style.display = emailCheckbox.checked ? 'block' : 'none';
        }
        document.getElementById('smtp-server').value = settings.SMTP_SERVER || settings.smtp_server || '';
        document.getElementById('smtp-port').value = settings.SMTP_PORT || settings.smtp_port || '587';
        document.getElementById('smtp-username').value = settings.SMTP_USERNAME || settings.smtp_username || '';
        document.getElementById('from-email').value = settings.FROM_EMAIL || settings.from_email || '';
        document.getElementById('email-recipients').value = settings.EMAIL_RECIPIENTS || settings.email_recipients || '';
        // Don't load password for security
        
        // Slack settings
        const slackCheckbox = document.getElementById('slack-enabled');
        if (slackCheckbox) {
            // Check both uppercase (from env) and lowercase (from some endpoints)
            slackCheckbox.checked = settings.SLACK_ENABLED === 'true' || settings.slack_enabled === 'true';
            document.getElementById('slack-config').style.display = slackCheckbox.checked ? 'block' : 'none';
        }
        document.getElementById('slack-webhook-url').value = settings.SLACK_WEBHOOK_URL || settings.slack_webhook_url || '';
        document.getElementById('slack-channel').value = settings.SLACK_CHANNEL || settings.slack_channel || '';
        document.getElementById('slack-cost-threshold').value = settings.SLACK_COST_THRESHOLD || settings.slack_cost_threshold || '';
        
    } catch (error) {
        window.logger.error('Error loading notification settings:', error);
    }
}

// Toggle notification config visibility
document.addEventListener('DOMContentLoaded', function() {
    const emailToggle = document.getElementById('email-enabled');
    const slackToggle = document.getElementById('slack-enabled');
    const emailConfig = document.getElementById('email-config');
    const slackConfig = document.getElementById('slack-config');
    
    // Don't set initial state here - let loadNotificationSettings handle it
    
    // Email toggle logic
    if (emailToggle && emailConfig) {
        const emailActions = document.querySelector('#email-form .settings-actions');
        
        emailToggle.addEventListener('change', async function() {
            const isEnabled = this.checked;
            emailConfig.style.display = isEnabled ? 'block' : 'none';
            if (emailActions) {
                emailActions.style.display = isEnabled ? 'block' : 'none';
            }
            
            // Auto-save the checkbox state
            try {
                const response = await fetch('/api/settings/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        key: 'EMAIL_ENABLED', 
                        value: isEnabled ? 'true' : 'false' 
                    })
                });
                
                if (!response.ok) {
                    console.error('Failed to save email enabled state');
                }
            } catch (error) {
                console.error('Error saving email enabled state:', error);
            }
        });
        
        // Set initial state
        const emailEnabled = emailToggle.checked;
        emailConfig.style.display = emailEnabled ? 'block' : 'none';
        if (emailActions) {
            emailActions.style.display = emailEnabled ? 'block' : 'none';
        }
    }
    
    // Slack toggle logic
    if (slackToggle && slackConfig) {
        const slackActions = document.querySelector('#slack-form .settings-actions');
        
        slackToggle.addEventListener('change', async function() {
            const isEnabled = this.checked;
            slackConfig.style.display = isEnabled ? 'block' : 'none';
            if (slackActions) {
                slackActions.style.display = isEnabled ? 'block' : 'none';
            }
            
            // Auto-save the checkbox state
            try {
                const response = await fetch('/api/settings/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        key: 'SLACK_ENABLED', 
                        value: isEnabled ? 'true' : 'false' 
                    })
                });
                
                if (!response.ok) {
                    console.error('Failed to save slack enabled state');
                }
            } catch (error) {
                console.error('Error saving slack enabled state:', error);
            }
        });
        
        // Set initial state
        const slackEnabled = slackToggle.checked;
        slackConfig.style.display = slackEnabled ? 'block' : 'none';
        if (slackActions) {
            slackActions.style.display = slackEnabled ? 'block' : 'none';
        }
    }
    
    // Load settings on page load
    loadNotificationSettings();
});

function showToast(message, type = 'info') {
    // Create toast notification element
    const toast = document.createElement('div');
    toast.className = `flash-message flash-${type}`;
    
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'flash-close';
    closeBtn.innerHTML = '×';
    closeBtn.onclick = () => toast.remove();
    
    toast.appendChild(messageSpan);
    toast.appendChild(closeBtn);
    
    // Add to flash messages container or create one
    let flashContainer = document.querySelector('.flash-messages');
    if (!flashContainer) {
        flashContainer = document.createElement('div');
        flashContainer.className = 'flash-messages';
        document.body.appendChild(flashContainer);
    }
    
    flashContainer.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
    
    // Also log to console for debugging
    window.logger.debug(`[${type}] ${message}`);
}

// AJAX form submission to prevent page reload and tab switching
document.addEventListener('DOMContentLoaded', function() {
    // Handle Azure form submission
    const azureForm = document.getElementById('azure-form');
    if (azureForm) {
        azureForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await handleAjaxFormSubmit(this, 'Azure settings saved successfully! Azure credentials refreshed.');
        });
    }
    
    // Handle Email form submission  
    const emailForm = document.getElementById('email-form');
    if (emailForm) {
        emailForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await handleAjaxFormSubmit(this, 'Email settings saved successfully!');
        });
    }
    
    // Handle Slack form submission
    const slackForm = document.getElementById('slack-form');
    if (slackForm) {
        slackForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await handleAjaxFormSubmit(this, 'Slack settings saved successfully!');
        });
    }
    
    // Handle Advanced form submission
    const advancedForm = document.getElementById('advanced-form');
    if (advancedForm) {
        advancedForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await handleAjaxFormSubmit(this, 'Advanced settings saved successfully!');
        });
    }
});

async function handleAjaxFormSubmit(form, successMessage) {
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    
    // Show loading state
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    submitButton.disabled = true;
    
    try {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            showToast(successMessage, 'success');
        } else {
            showToast('Error saving settings. Please try again.', 'error');
        }
    } catch (error) {
        window.logger.error('Error submitting form:', error);
        showToast('Error saving settings. Please try again.', 'error');
    } finally {
        // Restore button state
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
    }
}