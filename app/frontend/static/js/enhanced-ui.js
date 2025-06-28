/**
 * ============================================================================
 * UI ENHANCEMENTS FOR AKS COST INTELLIGENCE DASHBOARD
 * ============================================================================
 * Add this to complement your existing JavaScript files
 * ============================================================================
 */

/**
 * Enhanced UI Manager for better visual feedback
 */
class EnhancedUIManager {
    constructor() {
        this.animationQueue = [];
        this.isAnimating = false;
        this.observers = new Map();
        this.init();
    }

    init() {
        console.log('🎨 Initializing Enhanced UI Manager...');
        this.setupIntersectionObservers();
        this.setupProgressAnimations();
        this.setupMetricAnimations();
        this.setupInsightAnimations();
        this.enhanceFormInteractions();
        this.setupChartEnhancements();
    }

    /**
     * Setup intersection observers for scroll animations
     */
    setupIntersectionObservers() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    
                    if (element.classList.contains('metric-card')) {
                        this.animateMetricCard(element);
                    } else if (element.classList.contains('insight-item')) {
                        this.animateInsightItem(element);
                    } else if (element.classList.contains('chart-container')) {
                        this.animateChartContainer(element);
                    }
                }
            });
        }, observerOptions);

        // Observe all animatable elements
        document.querySelectorAll('.metric-card, .insight-item, .chart-container').forEach(el => {
            observer.observe(el);
        });

        this.observers.set('intersection', observer);
    }

    /**
     * Animate metric cards on scroll
     */
    animateMetricCard(element) {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, 100);
    }

    /**
     * Animate insight items with stagger effect
     */
    animateInsightItem(element) {
        const siblings = Array.from(element.parentElement.children);
        const index = siblings.indexOf(element);
        
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
            element.classList.add('insight-fade-in');
        }, index * 150);
    }

    /**
     * Animate chart containers
     */
    animateChartContainer(element) {
        element.style.opacity = '0';
        element.style.transform = 'scale(0.95)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
            element.style.opacity = '1';
            element.style.transform = 'scale(1)';
        }, 200);
    }

    /**
     * Enhanced progress animations
     */
    setupProgressAnimations() {
        this.createProgressAnimator();
    }

    createProgressAnimator() {
        window.enhancedProgressAnimator = {
            start: (progressElement, textElement) => {
                const progress = progressElement || document.getElementById('progressFill');
                const text = textElement || document.getElementById('progressText');
                
                if (!progress || !text) return;

                const steps = [
                    { width: 0, text: 'Initializing analysis...', duration: 500 },
                    { width: 15, text: 'Connecting to Azure APIs...', duration: 1000 },
                    { width: 30, text: 'Gathering cluster metrics...', duration: 1500 },
                    { width: 50, text: 'Analyzing resource utilization...', duration: 2000 },
                    { width: 70, text: 'Processing ML recommendations...', duration: 1500 },
                    { width: 85, text: 'Calculating cost optimizations...', duration: 1000 },
                    { width: 95, text: 'Generating insights...', duration: 800 },
                    { width: 100, text: 'Analysis complete!', duration: 500 }
                ];

                let currentStep = 0;

                const animate = () => {
                    if (currentStep >= steps.length) return;

                    const step = steps[currentStep];
                    progress.style.width = step.width + '%';
                    text.textContent = step.text;

                    // Add pulse effect for progress bar
                    progress.style.boxShadow = `0 0 10px rgba(0, 123, 255, ${step.width / 100})`;

                    currentStep++;
                    if (currentStep < steps.length) {
                        setTimeout(animate, step.duration);
                    }
                };

                animate();
            }
        };
    }

    /**
     * Enhanced metric animations
     */
    setupMetricAnimations() {
        window.enhancedMetricAnimator = {
            updateValue: (elementId, newValue, format = 'currency', duration = 1000) => {
                const element = document.getElementById(elementId) || document.querySelector(elementId);
                if (!element) return;

                // Add loading state
                element.classList.add('metric-updating');
                element.style.opacity = '0.5';
                element.style.transform = 'scale(0.95)';

                setTimeout(() => {
                    // Format the value
                    let formattedValue;
                    if (format === 'currency') {
                        formattedValue = '$' + (newValue || 0).toLocaleString();
                    } else if (format === 'percentage') {
                        formattedValue = (newValue || 0).toFixed(1) + '%';
                    } else {
                        formattedValue = (newValue || 0).toString();
                    }

                    // Animate value change
                    element.textContent = formattedValue;
                    element.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
                    element.style.opacity = '1';
                    element.style.transform = 'scale(1)';
                    
                    // Add success indicator
                    element.classList.remove('metric-updating');
                    element.classList.add('metric-updated');
                    
                    // Remove success indicator after animation
                    setTimeout(() => {
                        element.classList.remove('metric-updated');
                    }, 2000);
                }, 300);
            },

            pulseMetric: (elementId) => {
                const element = document.getElementById(elementId) || document.querySelector(elementId);
                if (!element) return;

                element.style.animation = 'metricPulse 0.8s ease-out';
                setTimeout(() => {
                    element.style.animation = '';
                }, 800);
            }
        };
    }

    /**
     * Enhanced insight animations
     */
    setupInsightAnimations() {
        window.enhancedInsightAnimator = {
            updateInsight: (containerId, newContent, delay = 0) => {
                const container = document.getElementById(containerId) || document.querySelector(containerId);
                if (!container) return;

                setTimeout(() => {
                    // Add updating animation
                    container.style.transition = 'all 0.3s ease';
                    container.style.opacity = '0.3';
                    container.style.transform = 'translateY(10px)';

                    setTimeout(() => {
                        container.innerHTML = newContent;
                        container.style.opacity = '1';
                        container.style.transform = 'translateY(0)';
                        
                        // Add the insight-updated class for sparkle effect
                        container.classList.add('insight-updated');
                        container.closest('.insight-box')?.classList.add('loaded');
                        
                        setTimeout(() => {
                            container.classList.remove('insight-updated');
                        }, 2000);
                    }, 300);
                }, delay);
            },

            showLoadingState: (containerId, message = 'Generating insights...') => {
                const container = document.getElementById(containerId) || document.querySelector(containerId);
                if (!container) return;

                container.innerHTML = `
                    <div class="loading-text">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>${message}</span>
                    </div>
                `;
            }
        };
    }

    /**
     * Enhanced form interactions
     */
    enhanceFormInteractions() {
        // Add floating labels and validation feedback
        document.querySelectorAll('.smooth-input').forEach(input => {
            this.enhanceInput(input);
        });

        // Enhanced button interactions
        document.querySelectorAll('.smooth-btn').forEach(button => {
            this.enhanceButton(button);
        });

        // Form validation enhancements
        this.enhanceFormValidation();
    }

    enhanceInput(input) {
        input.addEventListener('focus', () => {
            input.parentElement.classList.add('input-focused');
        });

        input.addEventListener('blur', () => {
            input.parentElement.classList.remove('input-focused');
            if (input.value) {
                input.parentElement.classList.add('input-filled');
            } else {
                input.parentElement.classList.remove('input-filled');
            }
        });

        input.addEventListener('input', () => {
            this.validateInput(input);
        });
    }

    enhanceButton(button) {
        button.addEventListener('click', (e) => {
            // Create ripple effect
            const ripple = document.createElement('span');
            ripple.className = 'ripple';
            
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.6);
                transform: scale(0);
                animation: ripple 0.6s linear;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                pointer-events: none;
            `;
            
            button.style.position = 'relative';
            button.style.overflow = 'hidden';
            button.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    }

    validateInput(input) {
        const value = input.value.trim();
        const parent = input.parentElement;
        
        // Remove existing feedback
        parent.querySelector('.validation-feedback')?.remove();
        parent.classList.remove('validation-success', 'validation-error');
        
        if (input.hasAttribute('required') && !value) {
            this.showValidationError(parent, 'This field is required');
        } else if (input.type === 'email' && value && !this.isValidEmail(value)) {
            this.showValidationError(parent, 'Please enter a valid email address');
        } else if (value) {
            this.showValidationSuccess(parent);
        }
    }

    showValidationError(parent, message) {
        parent.classList.add('validation-error');
        const feedback = document.createElement('div');
        feedback.className = 'validation-feedback text-danger small mt-1';
        feedback.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i>${message}`;
        parent.appendChild(feedback);
    }

    showValidationSuccess(parent) {
        parent.classList.add('validation-success');
        const feedback = document.createElement('div');
        feedback.className = 'validation-feedback text-success small mt-1';
        feedback.innerHTML = `<i class="fas fa-check-circle me-1"></i>Looks good!`;
        parent.appendChild(feedback);
    }

    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    enhanceFormValidation() {
        const forms = document.querySelectorAll('.enhanced-form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });
        });
    }

    validateForm(form) {
        let isValid = true;
        const inputs = form.querySelectorAll('.smooth-input[required]');
        
        inputs.forEach(input => {
            this.validateInput(input);
            if (input.parentElement.classList.contains('validation-error')) {
                isValid = false;
            }
        });
        
        return isValid;
    }

    /**
     * Chart enhancement setup
     */
    setupChartEnhancements() {
        window.enhancedChartManager = {
            addMLBadge: (chartContainer, workloadType, confidence) => {
                const existingBadge = chartContainer.querySelector('.ml-classification-badge');
                if (existingBadge) {
                    existingBadge.remove();
                }

                const badge = document.createElement('div');
                badge.className = 'ml-classification-badge ml-workload-badge';
                badge.innerHTML = `ML: ${workloadType} (${(confidence * 100).toFixed(0)}% confidence)`;
                
                chartContainer.style.position = 'relative';
                chartContainer.appendChild(badge);
            },

            showChartLoading: (canvasId) => {
                const canvas = document.getElementById(canvasId);
                if (!canvas) return;

                const container = canvas.parentElement;
                const loading = document.createElement('div');
                loading.className = 'chart-loading';
                loading.innerHTML = `
                    <div class="d-flex align-items-center justify-content-center h-100">
                        <div class="text-center">
                            <i class="fas fa-spinner fa-spin fa-2x text-primary mb-3"></i>
                            <p class="text-muted">Loading chart data...</p>
                        </div>
                    </div>
                `;
                
                container.appendChild(loading);
                canvas.style.opacity = '0.3';
            },

            hideChartLoading: (canvasId) => {
                const canvas = document.getElementById(canvasId);
                if (!canvas) return;

                const container = canvas.parentElement;
                const loading = container.querySelector('.chart-loading');
                if (loading) {
                    loading.remove();
                }
                
                canvas.style.transition = 'opacity 0.5s ease';
                canvas.style.opacity = '1';
            }
        };
    }

    /**
     * Enhanced notification system
     */
    static createNotificationSystem() {
        window.enhancedNotifications = {
            show: (message, type = 'info', duration = 5000) => {
                const notification = document.createElement('div');
                notification.className = `alert alert-${type} notification-enhanced position-fixed`;
                notification.style.cssText = `
                    top: 20px;
                    right: 20px;
                    z-index: 9999;
                    min-width: 300px;
                    max-width: 400px;
                `;
                
                const icons = {
                    success: 'check-circle',
                    error: 'exclamation-triangle',
                    warning: 'exclamation-circle',
                    info: 'info-circle'
                };
                
                notification.innerHTML = `
                    <div class="d-flex align-items-center">
                        <i class="fas fa-${icons[type]} me-2"></i>
                        <span>${message}</span>
                        <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
                    </div>
                `;
                
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    notification.style.opacity = '0';
                    notification.style.transform = 'translateX(100%)';
                    setTimeout(() => notification.remove(), 300);
                }, duration);
            }
        };
    }
}

/**
 * Enhanced Analysis Form Handler
 */
class EnhancedAnalysisForm {
    constructor() {
        this.form = document.getElementById('analysisForm');
        this.button = document.getElementById('analyzeBtn');
        this.progress = document.getElementById('analysisProgress');
        this.init();
    }

    init() {
        if (!this.form) return;

        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        this.setupFormEnhancements();
    }

    setupFormEnhancements() {
        // Auto-focus first input
        const firstInput = this.form.querySelector('.smooth-input');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }

        // Add character counters for text inputs
        this.form.querySelectorAll('input[type="text"]').forEach(input => {
            if (input.hasAttribute('maxlength')) {
                this.addCharacterCounter(input);
            }
        });
    }

    addCharacterCounter(input) {
        const maxLength = input.getAttribute('maxlength');
        const counter = document.createElement('small');
        counter.className = 'character-counter text-muted';
        counter.textContent = `0/${maxLength}`;
        
        input.parentElement.appendChild(counter);
        
        input.addEventListener('input', () => {
            const current = input.value.length;
            counter.textContent = `${current}/${maxLength}`;
            counter.className = `character-counter ${current > maxLength * 0.8 ? 'text-warning' : 'text-muted'}`;
        });
    }

    handleSubmit(e) {
        // Enhanced form submission with better UX
        this.showLoadingState();
        this.startProgressAnimation();
        
        // Let the form submit normally, but with enhanced UI feedback
    }

    showLoadingState() {
        if (!this.button) return;

        this.button.classList.add('loading');
        this.button.disabled = true;
        
        if (this.progress) {
            this.progress.classList.add('active');
            
            if (window.enhancedProgressAnimator) {
                window.enhancedProgressAnimator.start();
            }
        }
    }

    startProgressAnimation() {
        // This will be called by the existing form submission logic
        if (window.enhancedProgressAnimator) {
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            window.enhancedProgressAnimator.start(progressFill, progressText);
        }
    }
}

/**
 * Enhanced Tab Manager
 */
class EnhancedTabManager {
    constructor() {
        this.tabs = document.querySelectorAll('.nav-pills .nav-link');
        this.init();
    }

    init() {
        this.tabs.forEach(tab => {
            tab.addEventListener('click', (e) => this.handleTabClick(e));
        });
    }

    handleTabClick(e) {
        const tab = e.target;
        const targetId = tab.getAttribute('data-bs-target');
        
        // Add loading animation for tab content
        if (targetId) {
            const targetPane = document.querySelector(targetId);
            if (targetPane) {
                this.animateTabTransition(targetPane);
            }
        }
    }

    animateTabTransition(pane) {
        pane.style.opacity = '0';
        pane.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            pane.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
            pane.style.opacity = '1';
            pane.style.transform = 'translateY(0)';
        }, 100);
    }
}

/**
 * Integration with existing functions
 */
function enhanceExistingFunctions() {
    // Enhance the existing updateDashboardMetrics function
    const originalUpdateMetrics = window.updateDashboardMetrics;
    if (originalUpdateMetrics && window.enhancedMetricAnimator) {
        window.updateDashboardMetrics = function(metrics) {
            // Call original function
            originalUpdateMetrics(metrics);
            
            // Add enhanced animations
            setTimeout(() => {
                window.enhancedMetricAnimator.updateValue('current-cost', metrics.total_cost);
                window.enhancedMetricAnimator.updateValue('potential-savings', metrics.total_savings);
                window.enhancedMetricAnimator.updateValue('hpa-efficiency', metrics.hpa_efficiency, 'percentage');
                window.enhancedMetricAnimator.updateValue('optimization-score', metrics.optimization_score);
            }, 100);
        };
    }

    // Enhance the existing updateRealDynamicInsights function
    const originalUpdateInsights = window.updateRealDynamicInsights;
    if (originalUpdateInsights && window.enhancedInsightAnimator) {
        window.updateRealDynamicInsights = function(data) {
            // Show loading states first
            window.enhancedInsightAnimator.showLoadingState('cost-insight');
            window.enhancedInsightAnimator.showLoadingState('hpa-insight');
            
            // Call original function with delay for better UX
            setTimeout(() => {
                originalUpdateInsights(data);
            }, 500);
        };
    }
}

/**
 * Enhanced initialization
 */
function initializeEnhancedUI() {
    console.log('🎨 Initializing Enhanced UI System...');
    
    // Initialize main UI manager
    const uiManager = new EnhancedUIManager();
    
    // Initialize form enhancements
    const formManager = new EnhancedAnalysisForm();
    
    // Initialize tab enhancements
    const tabManager = new EnhancedTabManager();
    
    // Create notification system
    EnhancedUIManager.createNotificationSystem();
    
    // Enhance existing functions
    enhanceExistingFunctions();
    
    // Add CSS animations if not already present
    addEnhancedCSS();
    
    console.log('✅ Enhanced UI System initialized');
    
    // Return managers for global access
    return {
        uiManager,
        formManager,
        tabManager
    };
}

/**
 * Add required CSS for animations
 */
function addEnhancedCSS() {
    if (document.getElementById('enhanced-ui-css')) return;
    
    const style = document.createElement('style');
    style.id = 'enhanced-ui-css';
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        .input-focused .form-label {
            color: #007bff;
            transform: translateY(-2px);
        }
        
        .validation-error .smooth-input {
            border-color: #dc3545;
            animation: shake 0.5s ease-in-out;
        }
        
        .validation-success .smooth-input {
            border-color: #28a745;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        
        .character-counter {
            text-align: right;
            margin-top: 0.25rem;
        }
        
        .chart-loading {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.9);
            z-index: 10;
        }
        
        .metric-updating {
            position: relative;
        }
        
        .metric-updating::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.5) 50%, transparent 70%);
            animation: shimmer 1.5s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
    `;
    
    document.head.appendChild(style);
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEnhancedUI);
} else {
    // DOM is already ready
    setTimeout(initializeEnhancedUI, 100);
}

// Make available globally
window.initializeEnhancedUI = initializeEnhancedUI;

console.log('🎨 Enhanced UI JavaScript loaded');