/**
 * ============================================================================
 * ENHANCED SMOOTH UI TRANSITIONS - JAVASCRIPT
 * ============================================================================
 * Provides smooth transitions, better loading states, and enhanced UX
 * ============================================================================
 */

// Enhanced configuration for smoother interactions
const SmoothConfig = {
    TRANSITION_DURATION: 300,
    LONG_TRANSITION_DURATION: 600,
    PAGE_TRANSITION_DELAY: 200,
    TAB_TRANSITION_DELAY: 150,
    CHART_LOAD_DELAY: 500
};

// Enhanced state management
const SmoothState = {
    isTransitioning: false,
    currentTab: null,
    implementationLoaded: false,
    pageLoading: false
};

/**
 * ============================================================================
 * PAGE TRANSITION MANAGEMENT
 * ============================================================================
 */

class PageTransitionManager {
    constructor() {
        this.overlay = this.createOverlay();
        this.setupNavigationInterception();
    }
    
    createOverlay() {
        let overlay = document.getElementById('page-transition-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'page-transition-overlay';
            overlay.className = 'page-transition-overlay';
            overlay.innerHTML = `
                <div class="page-transition-content">
                    <div class="spinner-grow text-primary mb-3" style="width: 3rem; height: 3rem;"></div>
                    <h5 class="text-primary mb-2">Loading...</h5>
                    <p class="text-muted">Please wait while we prepare your data</p>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        return overlay;
    }
    
    show(message = 'Loading...') {
        if (SmoothState.pageLoading) return;
        
        SmoothState.pageLoading = true;
        const messageElement = this.overlay.querySelector('h5');
        if (messageElement) {
            messageElement.textContent = message;
        }
        
        this.overlay.classList.add('show');
        document.body.classList.add('page-transitioning');
    }
    
    hide() {
        setTimeout(() => {
            this.overlay.classList.remove('show');
            document.body.classList.remove('page-transitioning');
            SmoothState.pageLoading = false;
        }, SmoothConfig.PAGE_TRANSITION_DELAY);
    }
    
    setupNavigationInterception() {
        // Intercept cluster navigation for smooth transitions
        document.addEventListener('click', (event) => {
            const clusterCard = event.target.closest('.cluster-card');
            if (clusterCard && !event.target.closest('.cluster-actions')) {
                event.preventDefault();
                const clusterId = clusterCard.getAttribute('data-cluster-id');
                if (clusterId) {
                    this.navigateToCluster(clusterId);
                }
            }
        });
    }
    
    navigateToCluster(clusterId) {
        this.show('Loading cluster dashboard...');
        
        // Add visual feedback to the clicked card
        const clusterCard = document.querySelector(`[data-cluster-id="${clusterId}"]`);
        if (clusterCard) {
            clusterCard.style.transform = 'scale(0.95)';
            clusterCard.style.opacity = '0.7';
        }
        
        setTimeout(() => {
            window.location.href = `/cluster/${clusterId}`;
        }, SmoothConfig.TRANSITION_DURATION);
    }
}

/**
 * ============================================================================
 * TAB NAVIGATION ENHANCEMENT
 * ============================================================================
 */

class SmoothTabManager {
    constructor() {
        this.setupTabHandlers();
        this.setupImplementationTabOptimization();
    }
    
    setupTabHandlers() {
        // Enhanced tab switching with smooth transitions
        document.addEventListener('show.bs.tab', (event) => {
            const targetTab = event.target.getAttribute('data-bs-target');
            this.handleTabTransition(targetTab, event.target);
        });
        
        document.addEventListener('shown.bs.tab', (event) => {
            const targetTab = event.target.getAttribute('data-bs-target');
            this.handleTabShown(targetTab);
        });
    }
    
    handleTabTransition(targetTab, tabElement) {
    if (SmoothState.isTransitioning) return;
    
    SmoothState.isTransitioning = true;
    SmoothState.currentTab = targetTab;
    
    // Don't modify tab text during transition - this causes issues
    // Just handle the content transition
    
    // Hide current content smoothly
    const currentActivePane = document.querySelector('.tab-pane.show.active');
    if (currentActivePane && currentActivePane !== document.querySelector(targetTab)) {
        currentActivePane.style.transition = 'opacity 0.2s ease';
        currentActivePane.style.opacity = '0';
    }
    
    // Prepare the target tab content immediately
    this.prepareTabContent(targetTab);
}
    
    handleTabShown(targetTab) {
    // Immediately show new content without delay
    const newActivePane = document.querySelector(targetTab);
    if (newActivePane) {
        newActivePane.style.transition = 'opacity 0.3s ease';
        newActivePane.style.opacity = '1';
        newActivePane.style.transform = 'none'; // Remove transform issues
    }
    
    // Tab-specific initialization with minimal delay
    setTimeout(() => {
        switch (targetTab) {
            case '#dashboard':
                this.initializeDashboardTab();
                break;
            case '#implementation':
                this.initializeImplementationTab();
                break;
            case '#alerts':
                this.initializeAlertsTab();
                break;
        }
        
        SmoothState.isTransitioning = false;
    }, 50); // Reduced from 100ms to 50ms
}
    
    prepareTabContent(targetTab) {
        const tabPane = document.querySelector(targetTab);
        if (tabPane) {
            // Add preparation classes for smooth animation
            tabPane.classList.add('preparing');
            
            setTimeout(() => {
                tabPane.classList.remove('preparing');
            }, 50);
        }
    }
    
    initializeDashboardTab() {
        logDebug('🎨 Initializing dashboard tab with smooth animations...');
        
        // Animate metric cards
        const metricCards = document.querySelectorAll('#dashboard .metric-card');
        metricCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
        
        // Initialize charts with delay for smooth loading
        setTimeout(() => {
            if (typeof initializeCharts === 'function') {
                initializeCharts();
            }
        }, SmoothConfig.CHART_LOAD_DELAY);
    }
    
    initializeImplementationTab() {
        logDebug('🚀 Initializing implementation tab with enhanced loading...');
        
        if (SmoothState.implementationLoaded) {
            this.showImplementationContent();
            return;
        }
        
        this.showImplementationLoading();
        this.loadImplementationContent();
    }
    
    initializeAnalysisTab() {
        logDebug('🔍 Initializing analysis tab...');
        
        // Animate form elements
        const formElements = document.querySelectorAll('#analysis .form-group, #analysis .form-check');
        formElements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateX(-20px)';
            
            setTimeout(() => {
                element.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
                element.style.opacity = '1';
                element.style.transform = 'translateX(0)';
            }, index * 100);
        });
    }
    
    initializeAlertsTab() {
        logDebug('🔔 Initializing alerts tab...');
        // Enterprise mode: No animations for professional appearance
    }
    
    setupImplementationTabOptimization() {
        // Preload implementation content when hovering over tab
        const implementationTab = document.querySelector('[data-bs-target="#implementation"]');
        if (implementationTab) {
            implementationTab.addEventListener('mouseenter', () => {
                if (!SmoothState.implementationLoaded) {
                    this.preloadImplementationContent();
                }
            });
        }
    }
    
    showImplementationLoading() {
        const container = document.getElementById('implementation-plan-container');
        if (container) {
            container.innerHTML = `
                <div class="implementation-loading">
                    <div class="spinner-border text-primary mb-3" style="width: 3rem; height: 3rem;"></div>
                    <h5 class="text-primary mb-2">Loading Implementation Plan</h5>
                    <p class="text-muted">Generating your personalized optimization roadmap...</p>
                    <div class="progress mt-4" style="height: 6px; width: 300px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             style="width: 100%"></div>
                    </div>
                </div>
            `;
        }
    }
    
    loadImplementationContent() {
        // Check if implementation plan features are enabled
        if (window.checkFeatureAccess && !window.checkFeatureAccess('implementation_plan')) {
            logDebug('🔒 Implementation plan features are locked - skipping API call');
            return;
        }
        
        // Use existing loadImplementationPlan function if available
        if (typeof loadImplementationPlan === 'function') {
            loadImplementationPlan();
        } else {
            // Fallback API call
            fetch('/api/implementation-plan')
                .then(response => response.json())
                .then(data => {
                    this.renderImplementationContent(data);
                    SmoothState.implementationLoaded = true;
                })
                .catch(error => {
                    logError('Failed to load implementation plan:', error);
                    this.showImplementationError(error.message);
                });
        }
    }
    
    preloadImplementationContent() {
        // Check if implementation plan features are enabled
        if (window.checkFeatureAccess && !window.checkFeatureAccess('implementation_plan')) {
            logDebug('🔒 Implementation plan features are locked - skipping preload API call');
            return;
        }
        
        // Silent preload for faster tab switching
        if (!SmoothState.implementationLoaded) {
            fetch('/api/implementation-plan')
                .then(response => response.json())
                .then(data => {
                    // Cache the data
                    window.implementationPlanCache = data;
                    SmoothState.implementationLoaded = true;
                })
                .catch(error => {
                    logWarn('Preload failed:', error);
                });
        }
    }
    
    showImplementationContent() {
        const container = document.getElementById('implementation-plan-container');
        if (container && window.implementationPlanCache) {
            this.renderImplementationContent(window.implementationPlanCache);
        } else if (typeof loadImplementationPlan === 'function') {
            loadImplementationPlan();
        }
    }
    
    renderImplementationContent(data) {
        const container = document.getElementById('implementation-plan-container');
        if (!container) return;
        
        // Animate content appearance
        container.style.opacity = '0';
        container.style.transform = 'translateY(30px)';
        
        // If displayImplementationPlan function exists, use it
        if (typeof displayImplementationPlan === 'function') {
            displayImplementationPlan(data);
        } else {
            // Fallback simple rendering
            container.innerHTML = `
                <div class="p-4">
                    <div class="alert alert-success">
                        <h5><i class="fas fa-check-circle me-2"></i>Implementation Plan Ready</h5>
                        <p class="mb-0">Your personalized optimization plan has been generated successfully.</p>
                    </div>
                </div>
            `;
        }
        
        // Animate in
        setTimeout(() => {
            container.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            container.style.opacity = '1';
            container.style.transform = 'translateY(0)';
        }, 100);
    }
    
    showImplementationError(message) {
        const container = document.getElementById('implementation-plan-container');
        if (container) {
            container.innerHTML = `
                <div class="p-4 text-center">
                    <div class="alert alert-danger">
                        <h5><i class="fas fa-exclamation-triangle me-2"></i>Error Loading Plan</h5>
                        <p class="mb-3">${message}</p>
                        <button class="btn btn-outline-primary" onclick="location.reload()">
                            <i class="fas fa-redo me-1"></i>Retry
                        </button>
                    </div>
                </div>
            `;
        }
    }
}

/**
 * ============================================================================
 * ENHANCED CHART LOADING
 * ============================================================================
 */

class SmoothChartManager {
    constructor() {
        this.loadingStates = new Map();
    }
    
    showChartLoading(chartId) {
        const canvas = document.getElementById(chartId);
        if (!canvas) return;
        
        const container = canvas.closest('.chart-container');
        if (!container) return;
        
        if (!this.loadingStates.has(chartId)) {
            const loadingOverlay = document.createElement('div');
            loadingOverlay.className = 'chart-loading-overlay';
            loadingOverlay.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary mb-3"></div>
                    <p class="text-muted">Loading chart data...</p>
                </div>
            `;
            loadingOverlay.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(5px);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10;
                border-radius: 15px;
            `;
            
            container.style.position = 'relative';
            container.appendChild(loadingOverlay);
            this.loadingStates.set(chartId, loadingOverlay);
        }
    }
    
    hideChartLoading(chartId) {
        const overlay = this.loadingStates.get(chartId);
        if (overlay) {
            overlay.style.transition = 'opacity 0.3s ease';
            overlay.style.opacity = '0';
            
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
                this.loadingStates.delete(chartId);
            }, 300);
        }
    }
    
    enhanceChartInitialization() {
        // Override the global initializeCharts function if it exists
        if (typeof window.initializeCharts === 'function') {
            const originalInitializeCharts = window.initializeCharts;
            
            window.initializeCharts = () => {
                logDebug('📊 Enhanced chart initialization started...');
                
                // Show loading for all charts
                const chartIds = [
                    'mainTrendChart', 'costBreakdownChart', 'hpaComparisonChart',
                    'nodeUtilizationChart', 'savingsBreakdownChart', 'namespaceCostChart',
                    'workloadCostChart'
                ];
                
                chartIds.forEach(id => this.showChartLoading(id));
                
                // Call original function
                const result = originalInitializeCharts();
                
                // Hide loading after delay
                setTimeout(() => {
                    chartIds.forEach(id => this.hideChartLoading(id));
                }, 1000);
                
                return result;
            };
        }
    }
}

/**
 * ============================================================================
 * ENHANCED FORM INTERACTIONS
 * ============================================================================
 */

class SmoothFormManager {
    constructor() {
        this.setupFormEnhancements();
    }
    
    setupFormEnhancements() {
        // Enhanced input focus effects
        document.addEventListener('focusin', (event) => {
            if (event.target.matches('.form-control, .form-select')) {
                this.enhanceInputFocus(event.target);
            }
        });
        
        document.addEventListener('focusout', (event) => {
            if (event.target.matches('.form-control, .form-select')) {
                this.removeInputFocus(event.target);
            }
        });
        
        // Enhanced button interactions
        this.setupButtonEnhancements();
    }
    
    enhanceInputFocus(input) {
        const formGroup = input.closest('.form-group, .mb-3');
        if (formGroup) {
            formGroup.classList.add('focused');
        }
        
        // Add floating label effect if applicable
        const label = formGroup?.querySelector('.form-label');
        if (label && !input.value) {
            label.style.transform = 'translateY(-10px) scale(0.85)';
            label.style.color = '#007bff';
        }
    }
    
    removeInputFocus(input) {
        const formGroup = input.closest('.form-group, .mb-3');
        if (formGroup) {
            formGroup.classList.remove('focused');
        }
        
        const label = formGroup?.querySelector('.form-label');
        if (label && !input.value) {
            label.style.transform = '';
            label.style.color = '';
        }
    }
    
    setupButtonEnhancements() {
        document.addEventListener('click', (event) => {
            if (event.target.matches('.btn, .btn *')) {
                const button = event.target.closest('.btn');
                if (button) {
                    this.createRippleEffect(button, event);
                }
            }
        });
    }
    
    createRippleEffect(button, event) {
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            transform: scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
        `;
        
        // Add ripple animation styles if not present
        if (!document.querySelector('#ripple-styles')) {
            const style = document.createElement('style');
            style.id = 'ripple-styles';
            style.textContent = `
                @keyframes ripple {
                    to {
                        transform: scale(4);
                        opacity: 0;
                    }
                }
                .btn {
                    position: relative;
                    overflow: hidden;
                }
            `;
            document.head.appendChild(style);
        }
        
        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);
        
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 600);
    }
}

/**
 * ============================================================================
 * NOTIFICATION SYSTEM ENHANCEMENT
 * ============================================================================
 */

class SmoothNotificationManager {
    constructor() {
        this.container = this.createContainer();
        this.queue = [];
        this.activeNotifications = new Set();
    }
    
    createContainer() {
        let container = document.getElementById('smooth-notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'smooth-notification-container';
            container.style.cssText = `
                position: fixed;
                top: 100px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }
    
    show(message, type = 'info', duration = 5000) {
        const notification = this.createNotification(message, type, duration);
        this.container.appendChild(notification);
        
        // Trigger animation
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        });
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                this.remove(notification);
            }, duration);
        }
        
        return notification;
    }
    
    createNotification(message, type, duration) {
        const notification = document.createElement('div');
        const id = Date.now() + Math.random();
        
        notification.className = `smooth-notification notification-${type}`;
        notification.dataset.id = id;
        notification.style.cssText = `
            background: ${this.getBackground(type)};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 15px;
            margin-bottom: 1rem;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transform: translateX(100%);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            cursor: pointer;
        `;
        
        notification.innerHTML = `
            <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center">
                    <i class="fas fa-${this.getIcon(type)} me-3"></i>
                    <span>${message}</span>
                </div>
                <button class="btn-close btn-close-white ms-3" 
                        onclick="event.stopPropagation(); this.closest('.smooth-notification').remove()"></button>
            </div>
        `;
        
        // Click to dismiss
        notification.addEventListener('click', () => {
            this.remove(notification);
        });
        
        this.activeNotifications.add(id);
        return notification;
    }
    
    remove(notification) {
        notification.style.transform = 'translateX(100%)';
        notification.style.opacity = '0';
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            this.activeNotifications.delete(notification.dataset.id);
        }, 400);
    }
    
    getBackground(type) {
        const backgrounds = {
            'success': 'linear-gradient(135deg, #28a745, #20c997)',
            'error': 'linear-gradient(135deg, #dc3545, #fd7e14)',
            'warning': 'linear-gradient(135deg, #ffc107, #fd7e14)',
            'info': 'linear-gradient(135deg, #007bff, #0056b3)'
        };
        return backgrounds[type] || backgrounds.info;
    }
    
    getIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || icons.info;
    }
}

/**
 * ============================================================================
 * ENHANCED GLOBAL FUNCTIONS
 * ============================================================================
 */

// Enhanced global cluster selection
window.selectClusterSmooth = function(clusterId) {
    if (window.pageTransitionManager) {
        window.pageTransitionManager.navigateToCluster(clusterId);
    } else {
        window.location.href = `/cluster/${clusterId}`;
    }
};

// Enhanced global notification
window.showSmoothNotification = function(message, type = 'info', duration = 5000) {
    if (window.smoothNotificationManager) {
        return window.smoothNotificationManager.show(message, type, duration);
    } else {
        // Use the global logger based on type
        if (type === 'error') {
            logError(message);
        } else if (type === 'warn') {
            logWarn(message);
        } else if (type === 'debug') {
            logDebug(message);
        } else {
            logDebug(message);
        }
    }
};

// Override existing functions for smooth transitions
if (typeof window.showNotification === 'function') {
    const originalShowNotification = window.showNotification;
    window.showNotification = function(message, type = 'info', duration = 5000) {
        if (window.smoothNotificationManager) {
            return window.smoothNotificationManager.show(message, type, duration);
        } else {
            return originalShowNotification(message, type, duration);
        }
    };
}

/**
 * ============================================================================
 * INITIALIZATION
 * ============================================================================
 */

class SmoothUIManager {
    constructor() {
        this.pageTransitionManager = new PageTransitionManager();
        this.tabManager = new SmoothTabManager();
        this.chartManager = new SmoothChartManager();
        this.formManager = new SmoothFormManager();
        this.notificationManager = new SmoothNotificationManager();
        
        this.init();
    }
    
    init() {
        // Make managers available globally
        window.pageTransitionManager = this.pageTransitionManager;
        window.smoothTabManager = this.tabManager;
        window.smoothChartManager = this.chartManager;
        window.smoothFormManager = this.formManager;
        window.smoothNotificationManager = this.notificationManager;
        
        // Enhance existing chart initialization
        this.chartManager.enhanceChartInitialization();
        
        // Setup page-wide smooth transitions
        this.setupPageTransitions();
        
        // Initialize current tab if active
        this.initializeActiveTab();
        
        logDebug('🚀 Smooth UI Manager initialized successfully');
    }
    
    setupPageTransitions() {
        // Add smooth entrance animation to page
        document.body.style.opacity = '0';
        document.body.style.transform = 'translateY(20px)';
        
        window.addEventListener('load', () => {
            setTimeout(() => {
                document.body.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
                document.body.style.opacity = '1';
                document.body.style.transform = 'translateY(0)';
                
                // Hide page loading overlay if present
                this.pageTransitionManager.hide();
            }, 100);
        });
    }
    
    initializeActiveTab() {
        const activeTab = document.querySelector('.nav-link.active');
        if (activeTab) {
            const targetTab = activeTab.getAttribute('data-bs-target');
            if (targetTab) {
                setTimeout(() => {
                    this.tabManager.handleTabShown(targetTab);
                }, 500);
            }
        }
    }
}

/**
 * ============================================================================
 * MAIN INITIALIZATION
 * ============================================================================
 */

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Create global smooth UI manager
    window.smoothUIManager = new SmoothUIManager();
    
    // Add CSS for smooth transitions if not present
    if (!document.querySelector('#smooth-ui-styles')) {
        const style = document.createElement('style');
        style.id = 'smooth-ui-styles';
        style.textContent = `
            .page-transition-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,249,250,0.95));
                backdrop-filter: blur(20px);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: 0;
                visibility: hidden;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            .page-transition-overlay.show {
                opacity: 1;
                visibility: visible;
            }
            
            .page-transitioning {
                overflow: hidden;
            }
            
            .tab-pane {
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            .tab-pane:not(.active) {
                transform: translateY(20px);
                opacity: 0;
            }
            
            .tab-pane.active {
                transform: translateY(0);
                opacity: 1;
            }
            
            .form-group.focused .form-label {
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            .smooth-notification {
                animation: smoothSlideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            @keyframes smoothSlideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            /* Loading states */
            .cluster-card.selecting {
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                transform: scale(0.95);
                opacity: 0.7;
            }
            
            /* Implementation tab specific */
            .implementation-loading {
                padding: 3rem 2rem;
                text-align: center;
                background: linear-gradient(135deg, rgba(0, 123, 255, 0.02), rgba(0, 123, 255, 0.05));
                border-radius: 15px;
                margin: 2rem 0;
            }
            
            /* Dark mode adjustments */
            [data-theme="dark"] .page-transition-overlay {
                background: linear-gradient(135deg, rgba(26,26,26,0.95), rgba(42,42,42,0.95));
            }
        `;
        document.head.appendChild(style);
    }
    
    logDebug('✨ Enhanced smooth UI system loaded successfully');
});

// Export for external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        SmoothUIManager,
        PageTransitionManager,
        SmoothTabManager,
        SmoothChartManager,
        SmoothFormManager,
        SmoothNotificationManager
    };
}