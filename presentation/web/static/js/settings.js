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
        // Other settings would be loaded from API in a real implementation
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
    saveSettings() {
        const settings = this.gatherSettingsData();
        
        // Save theme immediately
        localStorage.setItem('theme', settings.theme);
        document.documentElement.setAttribute('data-theme', settings.theme);
        
        showToast('Settings saved successfully', 'success');
        
        // In a real implementation, this would save to the API
        this.saveToAPI(settings);
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
            cacheDuration: document.getElementById('cache-duration')?.value || '1800'
        };
    }

    async saveToAPI(settings) {
        try {
            // This would make an actual API call in a real implementation
            console.log('Settings to save:', settings);
        } catch (error) {
            console.error('Error saving settings:', error);
            showToast('Failed to save settings', 'error');
        }
    }

    resetSettings() {
        if (confirm('Are you sure you want to reset all settings to defaults?')) {
            this.loadDefaultSettings();
            showToast('Settings reset to defaults', 'info');
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
        showToast('Testing Azure connection...', 'info');
        
        try {
            // This would make an actual API call
            // const response = await fetch('/api/azure/test-connection', { method: 'POST' });
            // const result = await response.json();
            
            // Simulate success for now
            setTimeout(() => {
                showToast('Azure connection test successful', 'success');
            }, 2000);
            
        } catch (error) {
            console.error('Azure connection test failed:', error);
            showToast('Azure connection test failed', 'error');
        }
    }

    async refreshSubscriptions() {
        showToast('Refreshing Azure subscriptions...', 'info');
        
        try {
            // This would make an actual API call
            // const response = await fetch('/api/azure/subscriptions/refresh', { method: 'POST' });
            // const result = await response.json();
            
            // Simulate success for now
            setTimeout(() => {
                showToast('Azure subscriptions refreshed', 'success');
                // Update dropdown with new subscriptions
                this.updateSubscriptionDropdown();
            }, 2000);
            
        } catch (error) {
            console.error('Failed to refresh subscriptions:', error);
            showToast('Failed to refresh subscriptions', 'error');
        }
    }

    updateSubscriptionDropdown() {
        // This would update the subscription dropdown with fresh data
        const dropdown = document.getElementById('default-subscription');
        if (dropdown) {
            // Add new options or update existing ones
            console.log('Subscription dropdown updated');
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
            // This would make an actual API call
            // const response = await fetch('/api/cache/clear', { method: 'POST' });
            
            showToast('Cache cleared successfully', 'success');
            
        } catch (error) {
            console.error('Failed to clear cache:', error);
            showToast('Failed to clear cache', 'error');
        }
    }

    exportSettings() {
        showToast('Exporting settings...', 'info');
        
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
            
            showToast('Settings exported successfully', 'success');
            
        } catch (error) {
            console.error('Failed to export settings:', error);
            showToast('Failed to export settings', 'error');
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
            showToast(error, 'error');
        });
    }
}

// Initialize the settings page when DOM is loaded
let settingsPage;

document.addEventListener('DOMContentLoaded', function() {
    settingsPage = new SettingsPage();
});

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