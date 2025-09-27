/**
 * Feature Lock UI Handler
 * =======================
 * Handles UI interactions for locked features and upgrade prompts.
 */

class FeatureLockManager {
    constructor() {
        this.featureFlags = null;
        this.licenseInfo = null;
        this.init();
    }

    async init() {
        await this.loadLicenseInfo();
        this.setupFeatureLocks();
        this.setupUpgradePrompts();
    }

    async loadLicenseInfo() {
        try {
            const response = await fetch('/api/license/info');
            if (response.ok) {
                const data = await response.json();
                this.featureFlags = data.feature_flags;
                this.licenseInfo = data.license;
                
            } else {
                console.log('⚠️ Could not load license info');
                this.featureFlags = {};
                this.licenseInfo = { tier: 'free' };
            }
        } catch (error) {
            console.error('❌ Error loading license info:', error);
            this.featureFlags = {};
            this.licenseInfo = { tier: 'free' };
        }
    }

    setupFeatureLocks() {
        // Lock main navigation tabs based on license
        if (!this.featureFlags.implementation_plan) {
            this.lockNavigationTab('implementation', 'IMPLEMENTATION', 'Pro', 'fas fa-rocket');
        }

        if (!this.featureFlags.enterprise_metrics) {
            this.lockNavigationTab('enterprise-metrics', 'ENTERPRISE METRICS', 'Enterprise', 'fas fa-building');
        }

        if (!this.featureFlags.security_posture) {
            this.lockNavigationTab('securityposture', 'SECURITY POSTURE', 'Enterprise', 'fas fa-shield-alt');
        }

        if (!this.featureFlags.email_alerts && !this.featureFlags.slack_alerts) {
            this.lockNavigationTab('alerts', 'ALERTS', 'Pro', 'fas fa-bell');
        }

        // Also hide old selectors for backwards compatibility
        if (!this.featureFlags.implementation_plan) {
            this.hideFeature('.implementation-plan-btn', 'Implementation Plan', 'Pro');
            this.hideFeature('[data-feature="implementation_plan"]', 'Implementation Plan', 'Pro');
        }

        if (!this.featureFlags.enterprise_metrics) {
            this.hideFeature('.enterprise-metrics-btn', 'Enterprise Metrics', 'Enterprise');
            this.hideFeature('[data-feature="enterprise_metrics"]', 'Enterprise Metrics', 'Enterprise');
        }

        if (!this.featureFlags.security_posture) {
            this.hideFeature('.security-posture-btn', 'Security Posture', 'Enterprise');
            this.hideFeature('[data-feature="security_posture"]', 'Security Posture', 'Enterprise');
        }

        if (!this.featureFlags.auto_analysis) {
            this.hideFeature('.auto-analysis-btn', 'Auto-Analysis', 'Pro');
            this.hideFeature('[data-feature="auto_analysis"]', 'Auto-Analysis', 'Pro');
        }
    }

    lockNavigationTab(tabId, featureName, requiredTier, iconClass) {
        // Find navigation link for this tab (targets the unified dashboard nav structure)
        const navLink = document.querySelector(`a[href="#${tabId}-content"], a[onclick*="showContent('${tabId}',"]`);
        
        if (navLink) {
            // Make the tab look locked with visual indicators
            navLink.style.opacity = '0.5';
            navLink.style.cursor = 'not-allowed';
            navLink.classList.add('feature-locked');
            
            // Add lock icon if not already present
            if (!navLink.querySelector('.fa-lock')) {
                const lockIcon = document.createElement('i');
                lockIcon.className = 'fas fa-lock ml-2 text-yellow-500 text-xs';
                navLink.appendChild(lockIcon);
                
                // Add tier badge
                const tierBadge = document.createElement('span');
                tierBadge.className = 'ml-1 px-2 py-1 text-xs bg-yellow-600 text-white rounded';
                tierBadge.textContent = requiredTier;
                navLink.appendChild(tierBadge);
            }
            
            // Prevent navigation and show upgrade prompt
            navLink.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.showUpgradeModal(featureName, requiredTier);
                return false;
            });
            
            // Store info for upgrade modal
            navLink.setAttribute('data-locked-feature', featureName);
            navLink.setAttribute('data-required-tier', requiredTier);
        }
        
        // Also hide the content panel
        const contentPanel = document.querySelector(`#${tabId}-content`);
        if (contentPanel) {
            contentPanel.style.display = 'none';
            contentPanel.classList.add('feature-locked-content');
        }
    }

    hideFeature(selector, featureName, requiredTier) {
        const elements = document.querySelectorAll(selector);
        
        elements.forEach(element => {
            // Completely hide the element
            element.style.display = 'none';
            element.classList.add('feature-hidden');
            
            // Store info for potential upgrade prompts
            element.setAttribute('data-hidden-feature', featureName);
            element.setAttribute('data-required-tier', requiredTier);
        });
    }

    addUpgradePrompts() {
        // Add upgrade prompts in navigation or dashboard sections
        this.addTabUpgradePrompts();
    }

    addTabUpgradePrompts() {
        // Look for tab containers and add upgrade buttons for missing features
        const tabContainers = document.querySelectorAll('.nav-tabs, .tab-navigation, .dashboard-tabs');
        
        tabContainers.forEach(container => {
            // Check if we need to add upgrade prompts
            if (!this.featureFlags.implementation_plan) {
                this.addUpgradeTab(container, 'Implementation Plan', 'Pro', 'fas fa-clipboard-list');
            }
            
            if (!this.featureFlags.enterprise_metrics) {
                this.addUpgradeTab(container, 'Enterprise Metrics', 'Enterprise', 'fas fa-chart-line');
            }
            
            if (!this.featureFlags.security_posture) {
                this.addUpgradeTab(container, 'Security Posture', 'Enterprise', 'fas fa-shield-alt');
            }
        });
    }

    addUpgradeTab(container, featureName, requiredTier, iconClass) {
        const upgradeTab = document.createElement('li');
        upgradeTab.className = 'nav-item upgrade-tab';
        upgradeTab.innerHTML = `
            <button class="nav-link upgrade-tab-btn" type="button">
                <i class="${iconClass} mr-2"></i>
                ${featureName}
                <i class="fas fa-lock ml-2 text-yellow-500 text-xs"></i>
                <span class="badge badge-secondary text-xs ml-1">${requiredTier}</span>
            </button>
        `;
        
        upgradeTab.style.cssText = `
            opacity: 0.7;
            position: relative;
        `;
        
        upgradeTab.addEventListener('click', () => {
            this.showUpgradePrompt(featureName, requiredTier);
        });
        
        container.appendChild(upgradeTab);
    }

    lockFeature(selector, featureName, requiredTier) {
        // Fallback method for elements that should be locked instead of hidden
        const elements = document.querySelectorAll(selector);
        
        elements.forEach(element => {
            // Add visual lock indicator
            element.classList.add('feature-locked');
            element.style.position = 'relative';
            element.style.opacity = '0.6';
            element.style.cursor = 'not-allowed';
            
            // Add lock icon
            const lockIcon = document.createElement('div');
            lockIcon.className = 'feature-lock-overlay';
            lockIcon.innerHTML = `
                <i class="fas fa-lock text-yellow-600"></i>
                <span class="ml-1 text-xs">${requiredTier}</span>
            `;
            lockIcon.style.cssText = `
                position: absolute;
                top: 4px;
                right: 4px;
                background: rgba(255, 255, 255, 0.9);
                padding: 2px 6px;
                border-radius: 4px;
                border: 1px solid #e5e5e5;
                font-size: 10px;
                color: #d97706;
                z-index: 10;
            `;
            
            element.style.position = 'relative';
            element.appendChild(lockIcon);
            
            // Block clicks and show upgrade prompt
            element.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.showUpgradePrompt(featureName, requiredTier);
            });
            
            // Disable form inputs if any
            const inputs = element.querySelectorAll('input, button, select, textarea');
            inputs.forEach(input => {
                input.disabled = true;
                input.style.opacity = '0.5';
            });
        });
    }

    showUpgradeModal(featureName, requiredTier) {
        // Alias for showUpgradePrompt for consistency
        this.showUpgradePrompt(featureName, requiredTier);
    }

    showUpgradePrompt(featureName, requiredTier) {
        // Create modal backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'upgrade-modal-backdrop';
        backdrop.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        // Create modal
        const modal = document.createElement('div');
        modal.className = 'upgrade-modal';
        modal.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 24px;
            max-width: 480px;
            margin: 20px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        `;

        modal.innerHTML = `
            <div class="text-center">
                <div class="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-lock text-yellow-600 text-2xl"></i>
                </div>
                
                <h2 class="text-2xl font-bold text-gray-900 mb-2">Feature Locked</h2>
                <p class="text-gray-600 mb-6">${featureName} requires ${requiredTier} tier</p>
                
                <div class="bg-gray-50 rounded-lg p-4 mb-6">
                    <div class="flex justify-between items-center text-sm">
                        <div>
                            <span class="text-gray-500">Current:</span>
                            <span class="font-semibold text-gray-700">${this.licenseInfo.tier_display || this.licenseInfo.tier.charAt(0).toUpperCase() + this.licenseInfo.tier.slice(1)}</span>
                        </div>
                        <div>
                            <span class="text-gray-500">Required:</span>
                            <span class="font-semibold text-blue-600">${requiredTier}</span>
                        </div>
                    </div>
                </div>
                
                <div class="space-y-3">
                    <button onclick="window.open('https://kubevista.io/pricing', '_blank')" class="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                        <i class="fas fa-arrow-up mr-2"></i>
                        Upgrade to ${requiredTier}
                    </button>
                    
                    ${this.licenseInfo.tier === 'free' ? `
                        <button onclick="window.location.href='/'" class="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors">
                            <i class="fas fa-gift mr-2"></i>
                            Start Free Trial
                        </button>
                    ` : ''}
                    
                    <button onclick="this.closest('.upgrade-modal-backdrop').remove()" class="w-full bg-gray-500 text-white py-3 px-4 rounded-lg hover:bg-gray-600 transition-colors">
                        <i class="fas fa-times mr-2"></i>
                        Close
                    </button>
                </div>
                
                <p class="text-xs text-gray-500 mt-6">
                    Questions? <a href="mailto:support@kubevista.com" class="text-blue-600 hover:underline">Contact Support</a>
                </p>
            </div>
        `;

        backdrop.appendChild(modal);
        document.body.appendChild(backdrop);

        // Close on backdrop click
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                backdrop.remove();
            }
        });

        // Close on escape key
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                backdrop.remove();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
    }

    setupUpgradePrompts() {
        // Add upgrade prompts to navigation or dashboard
        this.addTierBadge();
        this.addUpgradeNotifications();
    }

    addTierBadge() {
        const nav = document.querySelector('nav') || document.querySelector('.navbar');
        if (!nav) return;

        // Add development mode indicator if in dev mode
        if (this.licenseInfo.dev_mode) {
            const devIndicator = document.createElement('div');
            devIndicator.className = 'dev-mode-indicator';
            devIndicator.innerHTML = '🔧 DEV MODE';
            devIndicator.title = 'Development mode active - all features unlocked';
            document.body.appendChild(devIndicator);
        }

        const tierBadge = document.createElement('div');
        tierBadge.className = 'tier-badge';
        tierBadge.style.cssText = `
            display: inline-flex;
            align-items: center;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 12px;
        `;

        const tier = this.licenseInfo.tier;
        if (tier === 'free') {
            tierBadge.style.background = '#f3f4f6';
            tierBadge.style.color = '#4b5563';
            tierBadge.innerHTML = '🆓 FREE';
        } else if (tier === 'pro') {
            tierBadge.style.background = '#dbeafe';
            tierBadge.style.color = '#1d4ed8';
            tierBadge.innerHTML = '🚀 PRO';
        } else if (tier === 'enterprise') {
            tierBadge.style.background = '#f3e8ff';
            tierBadge.style.color = '#7c3aed';
            tierBadge.innerHTML = '🏢 ENTERPRISE';
        }

        // Add to navigation
        const navContent = nav.querySelector('.navbar-nav') || nav.querySelector('ul') || nav;
        navContent.appendChild(tierBadge);
    }

    addUpgradeNotifications() {
        if (this.licenseInfo.tier === 'free') {
            this.showUpgradeBanner();
        }
    }

    showUpgradeBanner() {
        const banner = document.createElement('div');
        banner.className = 'upgrade-banner';
        banner.style.cssText = `
            background: linear-gradient(135deg, #2a385dff 100%);
            color: white;
            padding: 12px 20px;
            text-align: center;
            position: relative;
        `;

        banner.innerHTML = `
            <div class="flex items-center justify-center space-x-4">
                <span>🚀 Unlock Implementation Plans, Auto-Analysis & More!</span>
                <button onclick="window.location.href='/'" class="bg-white text-blue-600 px-4 py-1 rounded-full text-sm font-medium hover:bg-gray-100 transition-colors">
                    Start Free Trial
                </button>
                <button onclick="window.open('https://kubevista.io/pricing', '_blank')" class="bg-white text-purple-600 px-4 py-1 rounded-full text-sm font-medium hover:bg-gray-100 transition-colors">
                    Upgrade to Pro
                </button>
                <button onclick="this.parentElement.parentElement.remove()" class="text-white hover:text-gray-200 ml-2">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Insert at top of page
        document.body.insertBefore(banner, document.body.firstChild);
    }

    // Utility method to check feature access
    hasFeature(featureName) {
        return this.featureFlags && this.featureFlags[featureName] === true;
    }

    // Method to refresh license status
    async refreshLicenseStatus() {
        await this.loadLicenseInfo();
        // Reload page to refresh UI
        window.location.reload();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.featureLockManager = new FeatureLockManager();
});

// Global utility functions
window.checkFeatureAccess = (featureName) => {
    return window.featureLockManager && window.featureLockManager.hasFeature(featureName);
};

window.showUpgradePrompt = (featureName, requiredTier) => {
    if (window.featureLockManager) {
        window.featureLockManager.showUpgradePrompt(featureName, requiredTier);
    }
};