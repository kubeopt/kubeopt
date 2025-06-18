/**
 * ============================================================================
 * AKS COST INTELLIGENCE - MAIN DASHBOARD JAVASCRIPT
 * ============================================================================
 * Author: Srinivas Kondepudi
 * ============================================================================
 */

// ============================================================================
// GLOBAL CONFIGURATION & STATE
// ============================================================================

const AppConfig = {
    API_BASE_URL: '/api',
    CHART_REFRESH_INTERVAL: 30000,
    NOTIFICATION_DURATION: 5000,
    MIN_VALIDATION_LENGTH: 3,
    TRANSITION_DURATION: 300,
    SMOOTH_SCROLL_DURATION: 600
};

const AppState = {
    chartInstances: {},
    analysisCompleted: false,
    currentAnalysis: null,
    alerts: [],
    deployments: [],
    notifications: [],
    autoAnalysis: {
        active: {},
        pollingIntervals: {},
        statusCache: {}
    },
    smoothTransitions: {
        isTransitioning: false,
        currentTab: null,
        implementationLoaded: false
    }
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Formats numeric values based on specified format type
 */
function formatValue(value, format) {
    const num = parseFloat(value) || 0;
    if (isNaN(num)) {
        console.warn('⚠️ Invalid number for formatting:', value);
        return '0';
    }
    
    switch(format) {
        case 'currency':
            return '$' + Math.round(num).toLocaleString();
        case 'currency-monthly':
            return '$' + Math.round(num).toLocaleString() + '/mo';
        case 'percentage':
            return num.toFixed(1) + '%';
        case 'number':
            return Math.round(num).toString();
        default:
            return Math.round(num).toLocaleString();
    }
}

/**
 * Gets chart color scheme based on current theme
 */
function getChartColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        textColor: isDark ? '#f7fafc' : '#2d3748',
        gridColor: isDark ? '#4a5568' : '#e2e8f0',
        backgroundColor: isDark ? '#2d3748' : '#ffffff'
    };
}

/**
 * Calculates optimization score based on metrics
 */
function calculateOptimizationScore(metrics) {
    const savingsPercentage = metrics.savings_percentage || 0;
    const hpaReduction = metrics.hpa_reduction || 0;
    const cpuGap = metrics.cpu_gap || 0;
    const memoryGap = metrics.memory_gap || 0;
    
    const savingsScore = Math.min(100, savingsPercentage * 2);
    const efficiencyScore = Math.min(100, hpaReduction * 1.5);
    const utilizationScore = Math.max(0, 100 - (cpuGap + memoryGap) / 2);
    
    return Math.round(savingsScore * 0.4 + efficiencyScore * 0.3 + utilizationScore * 0.3);
}

/**
 * Debounce function to limit API calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Escapes HTML characters to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// ENHANCED NOTIFICATION SYSTEM - FIXED
// ============================================================================

/**
 * Enhanced notification manager for user feedback
 */
class NotificationManager {
    constructor() {
        this.container = this.createContainer();
    }
    
    createContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            container.style.top = '100px'; // Below navbar
            document.body.appendChild(container);
        }
        return container;
    }
    
    show(message, type = 'info', duration = AppConfig.NOTIFICATION_DURATION) {
        const toastElement = document.createElement('div');
        toastElement.className = `toast align-items-center text-white bg-${this.getBootstrapColor(type)} border-0`;
        toastElement.setAttribute('role', 'alert');
        toastElement.setAttribute('aria-live', 'assertive');
        toastElement.setAttribute('aria-atomic', 'true');
        toastElement.style.cssText = `
            backdrop-filter: blur(10px);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            margin-bottom: 0.75rem;
            min-width: 300px;
        `;
        
        toastElement.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${this.getIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        this.container.appendChild(toastElement);
        
        if (window.bootstrap && bootstrap.Toast) {
            const toast = new bootstrap.Toast(toastElement, {
                autohide: duration > 0,
                delay: duration
            });
            toast.show();
            
            toastElement.addEventListener('hidden.bs.toast', () => {
                if (toastElement.parentNode) {
                    toastElement.parentNode.removeChild(toastElement);
                }
            });
        } else {
            // Fallback if Bootstrap is not available
            setTimeout(() => {
                if (toastElement.parentNode) {
                    toastElement.parentNode.removeChild(toastElement);
                }
            }, duration);
        }
    }
    
    getBootstrapColor(type) {
        const colors = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'primary'
        };
        return colors[type] || 'primary';
    }
    
    getIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Initialize notification manager
const notificationManager = new NotificationManager();

/**
 * Global notification function
 */
function showNotification(message, type = 'info', duration = AppConfig.NOTIFICATION_DURATION) {
    notificationManager.show(message, type, duration);
}

// Alias for compatibility
const showToast = showNotification;

// ============================================================================
// FORM VALIDATION & HANDLERS - FIXED
// ============================================================================

/**
 * Validates analysis form inputs
 */
function validateAnalysisForm() {
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
function setupInputValidation() {
    const resourceGroupInput = document.getElementById('resource_group');
    const clusterNameInput = document.getElementById('cluster_name');
    
    if (resourceGroupInput) {
        resourceGroupInput.addEventListener('input', function() {
            if (this.value.trim().length >= AppConfig.MIN_VALIDATION_LENGTH) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                if (this.value.trim().length > 0) {
                    this.classList.add('is-invalid');
                }
            }
        });
    }
    
    if (clusterNameInput) {
        clusterNameInput.addEventListener('input', function() {
            if (this.value.trim().length >= AppConfig.MIN_VALIDATION_LENGTH) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                if (this.value.trim().length > 0) {
                    this.classList.add('is-invalid');
                }
            }
        });
    }
}

/**
 * Sets up form event handlers
 */
function setupFormHandlers() {
    // Add cluster form handler - FIXED with proper modal handling
    const addClusterModal = document.getElementById('addClusterModal');
    if (addClusterModal) {
        // Clear form when modal opens
        addClusterModal.addEventListener('show.bs.modal', function() {
            const form = this.querySelector('form');
            if (form) {
                form.reset();
                // Clear validation classes
                form.querySelectorAll('.form-control').forEach(input => {
                    input.classList.remove('is-invalid', 'is-valid');
                });
            }
        });
        
        // Handle form submission
        const form = addClusterModal.querySelector('form');
        if (form) {
            form.addEventListener('submit', handleAddClusterSubmission);
            console.log('✅ Add cluster form handler attached');
        }
    }
    
    // Analysis form handler - FIXED
    const analysisForm = document.getElementById('analysisForm');
    if (analysisForm) {
        analysisForm.addEventListener('submit', handleAnalysisSubmit);
        console.log('✅ Analysis form handler attached');
    }
}

// ============================================================================
// CLUSTER MANAGEMENT
// ============================================================================

/**
 * Enhanced cluster form submission with auto-analysis
 */
function handleAddClusterSubmission(event) {
    event.preventDefault();
    console.log('📝 Enhanced form submission started with auto-analysis');
    
    const formData = new FormData(event.target);
    const autoAnalyze = document.getElementById('auto_analyze')?.checked !== false; // Default true
    
    const clusterData = {
        cluster_name: formData.get('cluster_name'),
        resource_group: formData.get('resource_group'),
        environment: formData.get('environment') || 'development',
        region: formData.get('region') || '',
        description: formData.get('description') || '',
        auto_analyze: autoAnalyze
    };
    
    console.log('📋 Enhanced cluster data:', clusterData);
    
    // Validate required fields
    if (!clusterData.cluster_name || !clusterData.resource_group) {
        showNotification('Cluster name and resource group are required', 'error');
        return;
    }
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    if (!submitBtn) {
        console.error('❌ Submit button not found');
        return;
    }
    
    // Show loading state
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding...';
    submitBtn.disabled = true;
    
    console.log('📤 Sending enhanced API request...');
    
    // Make API call
    fetch(`${AppConfig.API_BASE_URL}/clusters`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(clusterData)
    })
    .then(response => {
        console.log('📡 Enhanced API response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('✅ Enhanced API success:', data);
        
        const clusterId = data.cluster_id;
        const autoAnalysisStarted = data.auto_analysis;
        
        if (autoAnalysisStarted) {
            // Auto-analysis started - show enhanced notification
            showNotification(
                `🎉 Cluster "${clusterData.cluster_name}" added successfully! Analysis is running automatically in the background.`, 
                'success', 
                8000
            );
            
            // Start real-time status tracking
            if (typeof startAnalysisTracking === 'function') {
                startAnalysisTracking(clusterId, clusterData.cluster_name);
            }
            
            // Update button to show analysis status
            submitBtn.innerHTML = '<i class="fas fa-cog fa-spin me-2"></i>Analysis Running...';
            
        } else {
            showNotification(`Cluster "${clusterData.cluster_name}" added successfully!`, 'success');
        }
        
        // Close modal if exists
        const modalElement = document.getElementById('addClusterModal');
        if (modalElement && window.bootstrap) {
            const modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
            modal.hide();
        }
        
        // Reset form
        event.target.reset();
        
        // Refresh the cluster list after a delay
        setTimeout(() => {
            window.location.reload();
        }, 2000);
        
    })
    .catch(error => {
        console.error('❌ Enhanced API error:', error);
        showNotification('Error adding cluster: ' + error.message, 'error');
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

/**
 * Selects a cluster and navigates to its detail page
 */
function selectCluster(clusterId) {
    console.log('🎯 Selecting cluster:', clusterId);
    
    // Show loading notification
    showNotification('Loading cluster dashboard...', 'info', 2000);
    
    // Add smooth loading effect if available
    const clusterCard = document.querySelector(`[data-cluster-id="${clusterId}"]`);
    if (clusterCard) {
        clusterCard.style.transition = 'all 0.3s ease';
        clusterCard.style.transform = 'scale(0.95)';
        clusterCard.style.opacity = '0.7';
    }
    
    setTimeout(() => {
        window.location.href = `/cluster/${clusterId}`;
    }, 300);
}

/**
 * Analyzes a specific cluster
 */
function analyzeCluster(clusterId) {
    if (event) event.stopPropagation();
    console.log('🔍 Analyzing cluster:', clusterId);
    
    const button = event.target.closest('button');
    if (button) {
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        button.disabled = true;
    }
    
    showNotification('Starting analysis...', 'info', 3000);
    
    fetch(`/cluster/${clusterId}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: 30, enable_pod_analysis: true })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Analysis completed successfully!', 'success');
            setTimeout(() => window.location.href = `/cluster/${clusterId}`, 1000);
        } else {
            throw new Error(data.message || 'Analysis failed');
        }
    })
    .catch(error => {
        console.error('❌ Analysis error:', error);
        showNotification('Analysis failed: ' + error.message, 'error');
    })
    .finally(() => {
        if (button) {
            button.innerHTML = '<i class="fas fa-play me-1"></i>Analyze Now';
            button.disabled = false;
        }
    });
}

/**
 * Removes a cluster after confirmation
 */
function removeCluster(clusterId) {
    if (event) event.stopPropagation();
    
    if (!confirm('Are you sure you want to remove this cluster? This will delete all analysis data.')) {
        return;
    }
    
    console.log('🗑️ Removing cluster:', clusterId);
    
    showNotification('Removing cluster...', 'warning', 0);
    
    fetch(`/cluster/${clusterId}/remove`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Cluster removed successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            throw new Error(data.message || 'Failed to remove cluster');
        }
    })
    .catch(error => {
        console.error('❌ Remove error:', error);
        showNotification('Failed to remove cluster: ' + error.message, 'error');
    });
}

// ============================================================================
// ANALYSIS MANAGEMENT - FIXED
// ============================================================================

/**
 * Handles analysis form submission with progress tracking - FIXED
 */
function handleAnalysisSubmit(event) {
    event.preventDefault();
    
    if (!validateAnalysisForm()) return;
    
    console.log('📊 Enhanced form submitted for analysis');
    const btn = document.getElementById('analyzeBtn');
    const progress = document.getElementById('analysisProgress');
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');
    
    // Enhanced loading state with animations
    if (btn) {
        btn.classList.add('loading');
        btn.disabled = true;
    }
    
    if (progress) progress.classList.add('visible');

    // Enhanced progress steps with animations
    const progressSteps = [
        { percentage: 10, text: '🔌 Connecting to Azure...', color: '#007AFF' },
        { percentage: 25, text: '💰 Fetching cost data...', color: '#5AC8FA' },
        { percentage: 45, text: '📊 Analyzing cluster metrics...', color: '#AF52DE' },
        { percentage: 65, text: '🎯 Calculating optimization opportunities...', color: '#FF9500' },
        { percentage: 85, text: '💡 Generating insights...', color: '#34C759' },
        { percentage: 95, text: '✨ Finalizing analysis...', color: '#00C851' }
    ];
    
    let stepIndex = 0;
    function advanceProgress() {
        if (stepIndex < progressSteps.length && fill && text) {
            const step = progressSteps[stepIndex];
            fill.style.width = step.percentage + '%';
            fill.style.background = `linear-gradient(90deg, ${step.color}, ${step.color}dd)`;
            text.textContent = step.text;
            
            // Add ripple effect
            fill.style.boxShadow = `0 0 20px ${step.color}44`;
            
            stepIndex++;
            setTimeout(advanceProgress, 800);
        }
    }
    advanceProgress();

    // Submit analysis with enhanced completion handling - FIXED
    fetch('/analyze', { 
        method: 'POST', 
        body: new FormData(event.target) 
    })
    .then(response => {
        if (!response.ok) throw new Error(response.statusText);
        return response.text();
    })
    .then(() => {
        if (fill) {
            fill.style.width = '100%';
            fill.style.background = 'linear-gradient(90deg, #00C851, #32CD32)';
            fill.style.boxShadow = '0 0 30px #00C85144';
        }
        if (text) text.textContent = '🎉 Analysis completed successfully!';
        
        AppState.analysisCompleted = true;
        
        setTimeout(() => {
            showNotification('🎉 Analysis completed! Found significant optimization opportunities.', 'success');
            
            setTimeout(() => {
                switchToTab('#dashboard');
                resetAnalysisForm();
                
                // FIXED: Auto-load charts and clear loading states
                setTimeout(() => {
                    initializeCharts();
                    clearLoadingStates(); // NEW: Clear all loading states
                }, 500);
            }, 1500);
        }, 1000);
    })
    .catch(error => {
        console.error('❌ Analysis failed:', error);
        showNotification('❌ Analysis failed: ' + error.message, 'error');
        resetAnalysisForm();
    });

    function resetAnalysisForm() {
        if (btn) {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
        if (progress) progress.classList.remove('visible');
        if (fill) {
            fill.style.width = '0%';
            fill.style.background = '';
            fill.style.boxShadow = '';
        }
        if (text) text.textContent = 'Initializing analysis...';
        stepIndex = 0;
    }
}

// ============================================================================
// NEW: CLEAR LOADING STATES FUNCTION
// ============================================================================

/**
 * Clears all loading states after analysis completion - NEW
 */
function clearLoadingStates() {
    console.log('🧹 Clearing all loading states...');
    
    // Clear insight loading states
    const insightElements = [
        { selector: '#cost-insight', defaultText: 'VM Scale Sets consume 68% of your monthly budget. Consider implementing right-sizing recommendations.' },
        { selector: '#hpa-insight', defaultText: 'Memory-based HPA could reduce replica count by 23%, saving approximately $140/month.' }
    ];
    
    insightElements.forEach(({ selector, defaultText }) => {
        const element = document.querySelector(selector);
        if (element) {
            const loadingSpan = element.querySelector('.loading-text');
            if (loadingSpan) {
                element.innerHTML = defaultText;
                console.log(`✅ Cleared loading state for ${selector}`);
            }
        }
    });
    
    // Update metric labels that show "Run analysis to view"
    const metricLabels = [
        { selector: '#hpa-efficiency', parentSelector: '.metric-card', labelText: 'Memory-based optimization' },
        { selector: '#optimization-score', parentSelector: '.metric-card', labelText: 'Overall efficiency rating' }
    ];
    
    metricLabels.forEach(({ selector, parentSelector, labelText }) => {
        const metricElement = document.querySelector(selector);
        if (metricElement && metricElement.textContent === '--') {
            const parent = metricElement.closest(parentSelector);
            if (parent) {
                const labelElement = parent.querySelector('.text-muted');
                if (labelElement && labelElement.textContent.includes('Run analysis to view')) {
                    labelElement.innerHTML = `<i class="fas fa-info-circle me-1"></i>${labelText}`;
                }
            }
        }
    });
}

// ============================================================================
// CHART MANAGEMENT - FIXED VERSION
// ============================================================================

/**
 * Initializes all dashboard charts - FIXED
 */
function initializeCharts() {
    console.log('📊 Initializing charts with real data...');
    
    fetch(`${AppConfig.API_BASE_URL}/chart-data`)
        .then(response => {
            console.log('📡 Chart data response status:', response.status);
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            return response.json();
        })
        .then(data => {
            console.log('📈 Chart data received:', data);
            
            // Validate the response
            if (data.status !== 'success') {
                throw new Error(data.message || 'Invalid API response');
            }
            
            if (!data.metrics) {
                throw new Error('No metrics data in response');
            }
            
            // Log the actual values we're working with
            console.log('💰 Cost:', data.metrics.total_cost);
            console.log('💵 Savings:', data.metrics.total_savings);
            
            // Update metrics FIRST - FIXED
            updateDashboardMetrics(data.metrics);
            
            // Then create charts - FIXED
            createAllCharts(data);
            
            // FIXED: Clear loading states after successful chart creation
            setTimeout(() => {
                clearLoadingStates();
                updateDataSourceIndicator(data.metadata || {});
            }, 1000);
            
            console.log('✅ Charts initialized successfully with real data');
        })
        .catch(error => {
            console.error('❌ Chart initialization failed:', error);
            showChartError('Unable to load real data: ' + error.message);
            
            // Don't fall back to sample data - show the error
            const errorMessage = `Failed to load analysis data: ${error.message}. Please run analysis first.`;
            showNotification(errorMessage, 'error');
        });
}

/**
 * Updates dashboard metrics with animation - FIXED
 */
function updateDashboardMetrics(metrics) {
    console.log('📊 Updating metrics with comprehensive element targeting:', metrics);
    
    // Validate metrics object
    if (!metrics || typeof metrics !== 'object') {
        console.error('❌ Invalid metrics object:', metrics);
        return;
    }
    
    // FIXED: Calculate optimization score if not provided
    const optimizationScore = metrics.optimization_score || calculateOptimizationScore(metrics);
    
    // FIXED: Calculate HPA efficiency if not provided
    const hpaEfficiency = metrics.hpa_efficiency || metrics.hpa_reduction || 0;
    
    // Enhanced metric updates with multiple selectors
    const metricUpdates = [
        { 
            selectors: ['#current-cost'], 
            value: metrics.total_cost, 
            format: 'currency',
            label: 'Current Monthly Cost'
        },
        { 
            selectors: ['#potential-savings', '#monthly-savings'], 
            value: metrics.total_savings, 
            format: 'currency',
            label: 'Potential Monthly Savings'
        },
        { 
            selectors: ['#hpa-efficiency'], 
            value: hpaEfficiency, 
            format: 'percentage',
            label: 'HPA Efficiency'
        },
        { 
            selectors: ['#optimization-score'], 
            value: optimizationScore, 
            format: 'number',
            label: 'Optimization Score'
        },
        { 
            selectors: ['#savings-percentage'], 
            value: metrics.savings_percentage, 
            format: 'percentage',
            label: 'Savings Percentage'
        },
        { 
            selectors: ['#annual-savings'], 
            value: metrics.annual_savings, 
            format: 'currency',
            label: 'Annual Savings'
        }
    ];
    
    // Log each update for debugging
    metricUpdates.forEach((metric, index) => {
        console.log(`📊 Updating metric ${index} (${metric.label}):`, metric.selectors[0], '=', metric.value);
        animateMetricUpdate(metric, index * 100);
    });
    
    // Update specific savings elements - FIXED
    updateSpecificSavingsElements(metrics);
    
    // Update savings breakdown mini elements - FIXED
    updateSavingsBreakdownMini(metrics);
    
    updateCostTrend(metrics);
}

/**
 * Update specific savings elements - FIXED
 */
function updateSpecificSavingsElements(metrics) {
    console.log('🔧 Updating specific savings elements');
    
    // Update monthly savings in multiple locations
    const monthlySavingsElements = [
        '#monthly-savings',
        '#potential-savings',
        '#action-savings'
    ];
    
    monthlySavingsElements.forEach(selector => {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = formatValue(metrics.total_savings || 0, 'currency');
            console.log(`Updated ${selector} to: ${element.textContent}`);
        }
    });
    
    // Update annual savings
    const annualSavingsElement = document.querySelector('#annual-savings');
    if (annualSavingsElement) {
        annualSavingsElement.textContent = formatValue(metrics.annual_savings || 0, 'currency');
    }
    
    // Update savings percentage
    const savingsPercentageElements = document.querySelectorAll('#savings-percentage');
    savingsPercentageElements.forEach(element => {
        element.textContent = `${(metrics.savings_percentage || 0).toFixed(1)}% potential savings`;
    });
}

/**
 * Update savings breakdown mini elements - FIXED
 */
function updateSavingsBreakdownMini(metrics) {
    console.log('🔧 Updating savings breakdown mini elements');
    
    const hpaElement = document.getElementById('hpa-savings-mini');
    const rightsizingElement = document.getElementById('rightsizing-savings-mini');
    const storageElement = document.getElementById('storage-savings-mini');
    
    if (hpaElement) {
        hpaElement.textContent = formatValue(metrics.hpa_savings || 0, 'currency');
    }
    if (rightsizingElement) {
        rightsizingElement.textContent = formatValue(metrics.right_sizing_savings || 0, 'currency');
    }
    if (storageElement) {
        storageElement.textContent = formatValue(metrics.storage_savings || 0, 'currency');
    }
    
    // Update gap displays
    const cpuGapElement = document.getElementById('cpu-gap-display');
    const memoryGapElement = document.getElementById('memory-gap-display');
    
    if (cpuGapElement) {
        cpuGapElement.textContent = (metrics.cpu_gap || 0).toFixed(1);
    }
    if (memoryGapElement) {
        memoryGapElement.textContent = (metrics.memory_gap || 0).toFixed(1);
    }
}

/**
 * Animates metric value updates - FIXED
 */
function animateMetricUpdate(metric, delay) {
    let element = null;
    
    // Find the first matching element
    for (const selector of metric.selectors) {
        element = document.querySelector(selector);
        if (element) break;
    }
    
    if (!element) return;

    setTimeout(() => {
        element.style.transition = 'all 0.3s';
        element.style.opacity = '0.5';
        element.style.transform = 'scale(0.9)';
        
        setTimeout(() => {
            const formattedValue = formatValue(metric.value, metric.format);
            element.textContent = formattedValue;
            element.style.opacity = '1';
            element.style.transform = 'scale(1)';
            
            // Add update indicator
            element.classList.add('metric-updated');
            setTimeout(() => element.classList.remove('metric-updated'), 2000);
        }, 300);
    }, delay);
}

/**
 * Updates cost trend indicator - FIXED
 */
function updateCostTrend(metrics) {
    document.querySelectorAll('#cost-trend').forEach(element => {
        const percentage = metrics.savings_percentage || 0;
        if (percentage > 20) {
            element.innerHTML = '<i class="fas fa-arrow-down text-success"></i> High Savings Potential';
        } else if (percentage > 10) {
            element.innerHTML = '<i class="fas fa-arrow-down text-warning"></i> Moderate Savings';
        } else {
            element.innerHTML = '<i class="fas fa-minus text-info"></i> Limited Optimization';
        }
    });
}

/**
 * Updates data source indicator - FIXED POSITIONING
 */
// function updateDataSourceIndicator(metadata) {
//     const isRealData = !metadata.is_sample_data;
//     let indicator = document.querySelector('#data-source-indicator');
    
//     if (!indicator) {
//         indicator = document.createElement('div');
//         indicator.id = 'data-source-indicator';
//         indicator.className = 'data-source-indicator';
//         document.body.appendChild(indicator); // Append to body, not dashboard
//     }
    
//     // FIXED: Better positioning to avoid overlap
//     indicator.style.cssText = `
//         position: fixed;
//         top: 140px;
//         right: 20px;
//         z-index: 999;
//         max-width: 200px;
//     `;
    
//     indicator.innerHTML = `
//         <div class="data-source-badge ${isRealData ? 'real-data' : 'sample-data'}">
//             <i class="fas fa-${isRealData ? 'cloud' : 'flask'}"></i>
//             <span>${isRealData ? 'Live Azure Data' : 'Demo Mode'}</span>
//             <small>${metadata.data_source || ''}</small>
//         </div>
//     `;
// }

// Rest of the chart functions (createAllCharts, etc.) remain the same...
// [Include all the existing chart creation functions from the original code]

/**
 * Creates all charts from provided data - FIXED
 */
function createAllCharts(data) {
    console.log('🎨 Creating all charts...');
    
    try {
        destroyAllCharts();
        
        const metadata = data.metadata || {};
        const isRealData = metadata.is_real_data === true || 
                          metadata.force_real_data === true ||
                          parseFloat(metadata.total_cost_verification?.replace(/[^0-9.]/g, '') || '0') > 100;

        // Create individual charts
        if (data.costBreakdown?.values?.length) {
            createCostBreakdownChart(data.costBreakdown, isRealData);
        }
        
        if (data.hpaComparison) {
            createHPAComparisonChart(data.hpaComparison, isRealData);
        }
        
        if (data.nodeUtilization) {
            createNodeUtilizationChart(data.nodeUtilization, isRealData);
        }
        
        if (data.savingsBreakdown) {
            createSavingsBreakdownChart(data.savingsBreakdown, isRealData);
        }
        
        if (data.trendData?.labels && data.trendData?.datasets) {
            createMainTrendChart(data.trendData, isRealData);
        }
        
        if (data.podCostBreakdown?.labels?.length) {
            createNamespaceCostChart(data.podCostBreakdown);
            const podSection = document.getElementById('pod-cost-section');
            if (podSection) podSection.style.display = 'block';
        }
        
        if (data.workloadCosts?.workloads?.length > 0) {
            createWorkloadCostChart(data.workloadCosts);
        }
        
        if (data.insights) {
            updateInsights(data.insights);
        }
        
        // Update pod cost metrics if available
        if (data.namespaceDistribution || data.workloadCosts || data.podCostBreakdown) {
            updatePodCostMetrics(data);
        }
        
        console.log('✅ All charts creation completed');
        
    } catch (error) {
        console.error('❌ Error building charts:', error);
        showChartError('Failed to render charts: ' + error.message);
    }
}

/**
 * Destroys all existing chart instances
 */
function destroyAllCharts() {
    const chartIds = [
        'mainTrendChart', 'costBreakdownChart', 'hpaComparisonChart', 
        'nodeUtilizationChart', 'savingsBreakdownChart', 'savingsProjectionChart',
        'namespaceCostChart', 'workloadCostChart'
    ];
    
    chartIds.forEach(id => {
        const canvas = document.getElementById(id);
        if (canvas && AppState.chartInstances[id]) {
            AppState.chartInstances[id].destroy();
            delete AppState.chartInstances[id];
        }
    });
}

/**
 * Creates cost breakdown chart - FIXED
 */
function createCostBreakdownChart(data, isRealData) {
    const canvas = document.getElementById('costBreakdownChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();
    
    const filteredData = data.labels.map((label, index) => ({
        label: label,
        value: data.values[index] || 0
    })).filter(item => item.value > 0);

    if (filteredData.length === 0) {
        canvas.parentElement.innerHTML = '<div class="text-center text-muted p-4">No cost data available</div>';
        return;
    }

    const config = {
        type: 'doughnut',
        data: {
            labels: filteredData.map(item => item.label),
            datasets: [{
                data: filteredData.map(item => item.value),
                backgroundColor: ['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6', '#1abc9c', '#95a5a6'],
                borderWidth: 2,
                borderColor: colors.backgroundColor,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: colors.textColor,
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };

    AppState.chartInstances['costBreakdownChart'] = new Chart(ctx, config);
}

/**
 * Creates main trend chart - FIXED
 */
function createMainTrendChart(data, isRealData) {
    const canvas = document.getElementById('mainTrendChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const datasets = (data.datasets || []).map((dataset, index) => ({
        label: dataset.name,
        data: dataset.data,
        borderColor: index === 0 ? '#e74c3c' : '#2ecc71',
        backgroundColor: index === 0 ? 'rgba(231, 76, 60, 0.1)' : 'rgba(46, 204, 113, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4
    }));

    const config = {
        type: 'line',
        data: {
            labels: data.labels || [],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: colors.textColor } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: colors.textColor },
                    grid: { color: colors.gridColor }
                },
                y: {
                    ticks: {
                        color: colors.textColor,
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: { color: colors.gridColor }
                }
            }
        }
    };

    AppState.chartInstances['mainTrendChart'] = new Chart(ctx, config);
}

/**
 * Creates HPA comparison chart - FIXED
 */
function createHPAComparisonChart(data, isRealData) {
    const canvas = document.getElementById('hpaComparisonChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const config = {
        type: 'bar',
        data: {
            labels: data.timePoints || [],
            datasets: [
                {
                    label: 'CPU-based HPA',
                    data: data.cpuReplicas || [],
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderColor: '#e74c3c',
                    borderWidth: 2
                },
                {
                    label: 'Memory-based HPA',
                    data: data.memoryReplicas || [],
                    backgroundColor: 'rgba(46, 204, 113, 0.7)',
                    borderColor: '#2ecc71',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: colors.textColor } }
            },
            scales: {
                x: {
                    ticks: { color: colors.textColor },
                    grid: { color: colors.gridColor }
                },
                y: {
                    ticks: { color: colors.textColor },
                    grid: { color: colors.gridColor },
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Replica Count',
                        color: colors.textColor
                    }
                }
            }
        }
    };

    AppState.chartInstances['hpaComparisonChart'] = new Chart(ctx, config);
}

/**
 * Creates node utilization chart - FIXED
 */
function createNodeUtilizationChart(data, isRealData) {
    const canvas = document.getElementById('nodeUtilizationChart');
    if (!canvas) {
        console.warn('⚠️ Node utilization chart canvas not found');
        return;
    }

    console.log('🔧 Creating node utilization chart with data:', data);

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();
    
    // Enhanced data validation and processing
    const nodes = data.nodes || [];
    const cpuRequest = data.cpuRequest || [];
    const cpuActual = data.cpuActual || [];
    const memoryRequest = data.memoryRequest || [];
    const memoryActual = data.memoryActual || [];
    
    console.log(`🔧 Raw data arrays:`, {
        nodesLength: nodes.length,
        cpuRequestLength: cpuRequest.length,
        cpuActualLength: cpuActual.length,
        memoryRequestLength: memoryRequest.length,
        memoryActualLength: memoryActual.length
    });
    
    // If arrays are empty but we have node names, this means the data structure is different
    if (nodes.length === 0) {
        console.warn('⚠️ No node data available for chart');
        canvas.parentElement.innerHTML = '<div class="text-center text-muted p-4">No node utilization data available</div>';
        return;
    }
    
    // If the utilization arrays are empty, extract data from a different structure
    let finalNodes = nodes;
    let finalCpuRequest = cpuRequest;
    let finalCpuActual = cpuActual;
    let finalMemoryRequest = memoryRequest;
    let finalMemoryActual = memoryActual;
    
    // Check if data is in a different format (like from the consistent analysis)
    if (cpuRequest.length === 0 && typeof nodes[0] === 'object') {
        console.log('🔧 Extracting data from object format nodes');
        
        finalNodes = nodes.map(node => node.name || node.node_name || 'Unknown');
        finalCpuRequest = nodes.map(node => parseFloat(node.cpu_request_pct || node.cpu_request || 0));
        finalCpuActual = nodes.map(node => parseFloat(node.cpu_usage_pct || node.cpu_actual || 0));
        finalMemoryRequest = nodes.map(node => parseFloat(node.memory_request_pct || node.memory_request || 0));
        finalMemoryActual = nodes.map(node => parseFloat(node.memory_usage_pct || node.memory_actual || 0));
        
        console.log('🔧 Extracted data:', {
            nodes: finalNodes,
            cpuRequest: finalCpuRequest,
            cpuActual: finalCpuActual,
            memoryRequest: finalMemoryRequest,
            memoryActual: finalMemoryActual
        });
    }
    
    // Validate we have actual data
    if (finalNodes.length === 0 || finalCpuActual.every(val => val === 0)) {
        console.warn('⚠️ No valid utilization data found');
        canvas.parentElement.innerHTML = '<div class="text-center text-muted p-4">No valid node utilization data found</div>';
        return;
    }

    const config = {
        type: 'bar',
        data: {
            labels: finalNodes,
            datasets: [
                {
                    label: 'CPU Request %',
                    data: finalCpuRequest,
                    backgroundColor: 'rgba(52, 152, 219, 0.3)',
                    borderColor: '#3498db',
                    borderWidth: 2,
                    order: 2
                },
                {
                    label: 'CPU Actual %',
                    data: finalCpuActual,
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderColor: '#e74c3c',
                    borderWidth: 2,
                    order: 1
                },
                {
                    label: 'Memory Request %',
                    data: finalMemoryRequest,
                    backgroundColor: 'rgba(155, 89, 182, 0.3)',
                    borderColor: '#9b59b6',
                    borderWidth: 2,
                    order: 4
                },
                {
                    label: 'Memory Actual %',
                    data: finalMemoryActual,
                    backgroundColor: 'rgba(46, 204, 113, 0.7)',
                    borderColor: '#2ecc71',
                    borderWidth: 2,
                    order: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    labels: { color: colors.textColor },
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { 
                        color: colors.textColor,
                        maxRotation: 45
                    },
                    grid: { color: colors.gridColor }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        color: colors.textColor,
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: { color: colors.gridColor },
                    title: {
                        display: true,
                        text: 'Utilization %',
                        color: colors.textColor
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    };

    // Destroy existing chart if it exists
    if (AppState.chartInstances['nodeUtilizationChart']) {
        AppState.chartInstances['nodeUtilizationChart'].destroy();
    }

    AppState.chartInstances['nodeUtilizationChart'] = new Chart(ctx, config);
    console.log('✅ Node utilization chart created successfully with real data');
}

/**
 * Creates savings breakdown chart - FIXED
 */
function createSavingsBreakdownChart(data, isRealData) {
    const canvas = document.getElementById('savingsBreakdownChart');
    if (!canvas) {
        console.warn('⚠️ Savings breakdown chart canvas not found');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();
    
    console.log('🔧 Creating savings breakdown chart with data:', data);

    // Validate data and filter out zero values
    const categories = data.categories || [];
    const values = data.values || [];
    
    // Filter out zero/negative values for better visualization
    const filteredData = categories.map((category, index) => ({
        category: category,
        value: Math.max(0, values[index] || 0)
    })).filter(item => item.value > 0);
    
    if (filteredData.length === 0) {
        console.warn('⚠️ No savings data to display');
        canvas.parentElement.innerHTML = '<div class="text-center text-muted p-4">No savings opportunities identified</div>';
        return;
    }
    
    console.log(`🔧 Processing ${filteredData.length} savings categories:`, filteredData);

    const config = {
        type: 'pie',
        data: {
            labels: filteredData.map(item => item.category),
            datasets: [{
                data: filteredData.map(item => item.value),
                backgroundColor: ['#3498db', '#e74c3c', '#2ecc71'],
                borderWidth: 2,
                borderColor: colors.backgroundColor,
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: colors.textColor,
                        padding: 10,
                        usePointStyle: true,
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    return {
                                        text: `${label}: $${value.toLocaleString()} (${percentage}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };

    // Destroy existing chart if it exists
    if (AppState.chartInstances['savingsBreakdownChart']) {
        AppState.chartInstances['savingsBreakdownChart'].destroy();
    }

    AppState.chartInstances['savingsBreakdownChart'] = new Chart(ctx, config);
    console.log('✅ Savings breakdown chart created successfully');
}

/**
 * Creates namespace cost chart - FIXED
 */
function createNamespaceCostChart(data) {
    const canvas = document.getElementById('namespaceCostChart');
    if (!canvas || !data?.labels?.length) {
        const podSection = document.getElementById('pod-cost-section');
        if (podSection) podSection.style.display = 'none';
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const namespaceColors = [
        '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
        '#1abc9c', '#95a5a6', '#34495e', '#e67e22', '#16a085'
    ];

    const config = {
        type: 'doughnut',
        data: {
            labels: data.labels || [],
            datasets: [{
                data: data.values || [],
                backgroundColor: namespaceColors,
                borderWidth: 2,
                borderColor: colors.backgroundColor,
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: colors.textColor,
                        padding: 15,
                        usePointStyle: true,
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    return {
                                        text: `${label}: $${value.toLocaleString()} (${percentage}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };

    AppState.chartInstances['namespaceCostChart'] = new Chart(ctx, config);
    
    // Update analysis badge
    const badge = document.getElementById('pod-analysis-badge');
    if (badge) {
        badge.textContent = `${data.analysis_method || 'Unknown'} - ${data.accuracy_level || 'Unknown'} Accuracy`;
        badge.className = `badge ${getAccuracyBadgeClass(data.accuracy_level)}`;
    }
    
    console.log('✅ Namespace cost chart created');
}

/**
 * Creates workload cost chart - FIXED
 */
function createWorkloadCostChart(data) {
    const canvas = document.getElementById('workloadCostChart');
    if (!canvas || !data) return;

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const typeColors = {
        'Deployment': '#3498db',
        'StatefulSet': '#e74c3c', 
        'DaemonSet': '#2ecc71',
        'ReplicaSet': '#f39c12',
        'Job': '#9b59b6',
        'CronJob': '#1abc9c'
    };

    const backgroundColors = data.types.map(type => typeColors[type] || '#95a5a6');

    const config = {
        type: 'bar',
        data: {
            labels: data.workloads.map(w => w.split('/')[1] || w),
            datasets: [{
                label: 'Monthly Cost',
                data: data.costs || [],
                backgroundColor: backgroundColors,
                borderColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const index = context[0].dataIndex;
                            return `${data.types[index]}: ${data.workloads[index]}`;
                        },
                        label: function(context) {
                            const index = context.dataIndex;
                            return [
                                `Cost: $${context.parsed.x.toLocaleString()}/month`,
                                `Namespace: ${data.namespaces[index]}`,
                                `Replicas: ${data.replicas[index]}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: colors.textColor,
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: { color: colors.gridColor }
                },
                y: {
                    ticks: { 
                        color: colors.textColor,
                        maxTicksLimit: 15
                    },
                    grid: { color: colors.gridColor }
                }
            }
        }
    };

    AppState.chartInstances['workloadCostChart'] = new Chart(ctx, config);
}

/**
 * Updates insights section - FIXED
 */
function updateInsights(insights) {
    const container = document.querySelector('#insights-container');
    if (!container) return;
    
    const insightElements = Object.entries(insights).map(([key, value]) => {
        const title = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        return `<div class="insight-item mb-3"><h6>${title}</h6><p>${value}</p></div>`;
    });
    
    container.innerHTML = insightElements.join('');
}

/**
 * Updates pod cost metrics in the dashboard - FIXED
 */
function updatePodCostMetrics(data) {
    console.log('📊 Updating pod cost metrics with data:', data);
    
    if (!data) {
        console.warn('No data provided to updatePodCostMetrics');
        return;
    }
    
    // Calculate top namespace cost
    let topNamespaceCost = 0;
    if (data.namespaceDistribution && data.namespaceDistribution.costs) {
        topNamespaceCost = Math.max(...data.namespaceDistribution.costs);
    } else if (data.podCostBreakdown && data.podCostBreakdown.values) {
        topNamespaceCost = Math.max(...data.podCostBreakdown.values);
    }
    
    // Get namespace count
    let namespaceCount = 0;
    if (data.namespaceDistribution && data.namespaceDistribution.namespaces) {
        namespaceCount = data.namespaceDistribution.namespaces.length;
    } else if (data.podCostBreakdown && data.podCostBreakdown.labels) {
        namespaceCount = data.podCostBreakdown.labels.length;
    }
    
    // Get workload count
    let workloadCount = 0;
    if (data.workloadCosts && data.workloadCosts.workloads) {
        workloadCount = data.workloadCosts.workloads.length;
    }
    
    // Get analysis accuracy
    let accuracy = 'Unknown';
    if (data.podCostBreakdown && data.podCostBreakdown.accuracy_level) {
        accuracy = data.podCostBreakdown.accuracy_level;
    }
    
    console.log(`Updating metrics: topCost=${topNamespaceCost}, namespaces=${namespaceCount}, workloads=${workloadCount}, accuracy=${accuracy}`);
    
    // Update the metrics
    const updates = [
        { sel: '#top-namespace-cost', val: topNamespaceCost, fmt: 'currency' },
        { sel: '#total-namespaces', val: namespaceCount, fmt: 'number' },
        { sel: '#total-workloads', val: workloadCount, fmt: 'number' },
        { sel: '#analysis-accuracy', val: accuracy, fmt: 'text' }
    ];
    
    updates.forEach(update => {
        const element = document.querySelector(update.sel);
        if (element) {
            let displayValue;
            if (update.fmt === 'currency') {
                displayValue = '$' + (update.val || 0).toLocaleString();
            } else if (update.fmt === 'number') {
                displayValue = (update.val || 0).toString();
            } else {
                displayValue = update.val || 'Unknown';
            }
            
            element.textContent = displayValue;
            console.log(`Updated ${update.sel} to: ${displayValue}`);
        } else {
            console.warn(`Element not found: ${update.sel}`);
        }
    });
    
    // Show the pod cost section if we have data
    if (topNamespaceCost > 0 || namespaceCount > 0) {
        const podSection = document.getElementById('pod-cost-section');
        if (podSection) {
            podSection.style.display = 'block';
            console.log('Pod cost section made visible');
        }
    }
}

/**
 * Gets accuracy badge class for pod analysis - FIXED
 */
function getAccuracyBadgeClass(accuracy) {
    switch (accuracy?.toLowerCase()) {
        case 'very high': return 'bg-success';
        case 'high': return 'bg-info';
        case 'good': return 'bg-warning';
        case 'basic': return 'bg-secondary';
        default: return 'bg-secondary';
    }
}

/**
 * Shows chart error message with retry option - FIXED
 */
function showChartError(message) {
    console.error('Chart error:', message);
    
    const chartIds = ['costBreakdownChart', 'hpaComparisonChart', 'nodeUtilizationChart', 'savingsBreakdownChart'];
    chartIds.forEach(id => {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        
        canvas.parentElement.innerHTML = `
            <div class="text-center text-muted p-4">
                <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                <p>${message}</p>
                <button class="btn btn-outline-primary btn-sm" onclick="initializeCharts()">
                    <i class="fas fa-redo me-1"></i>Retry
                </button>
            </div>
        `;
    });
}

// ============================================================================
// IMPLEMENTATION PLAN MANAGEMENT - FIXED
// ============================================================================

/**
 * Loads and displays implementation plan - FIXED
 */
function loadImplementationPlan() {
    console.log('📋 Enhanced: Loading implementation plan...');
    
    const container = document.getElementById('implementation-plan-container');
    if (!container) {
        console.error('❌ Implementation plan container not found!');
        return;
    }
    
    // Show enhanced loading state
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
            <h5 class="text-primary">Loading Implementation Plan...</h5>
            <p class="text-muted">Analyzing your cluster to generate personalized implementation recommendations...</p>
            <div class="mt-3">
                <div class="progress" style="height: 6px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
                </div>
            </div>
        </div>
    `;

    console.log('📤 Fetching implementation plan from API...');
    
    fetch('/api/implementation-plan')
        .then(response => {
            console.log('📡 API Response Status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(planData => {
            console.log('📊 Implementation plan data received:', planData);
            console.log('📊 Data keys:', Object.keys(planData));
            
            // Check for implementation phases
            if (planData.implementation_phases && planData.implementation_phases.length > 0) {
                console.log(`✅ Found ${planData.implementation_phases.length} implementation phases`);
                AppState.analysisCompleted = true;
                displayImplementationPlan(planData);
            } else {
                console.warn('⚠️ No implementation phases found in data');
                showNoAnalysisMessage(container);
            }
        })
        .catch(error => {
            console.error('❌ Implementation plan loading error:', error);
            displayImplementationError(container, error.message);
        });
}

/**
 * Displays implementation plan content - COMPLETELY FIXED
 */
/**
 * COMPLETE IMPLEMENTATION PLAN DISPLAY
 * Shows ALL the rich data from your implementation plan
 */

/**
 * COLLAPSIBLE IMPLEMENTATION PLAN DISPLAY
 * Adds expandable sections to make the plan more manageable
 */

function displayImplementationPlan(planData) {
    console.log('🎨 Displaying COLLAPSIBLE implementation plan with ALL data:', planData);
    
    const container = document.getElementById('implementation-plan-container');
    if (!container) {
        console.error('❌ Implementation plan container not found!');
        return;
    }

    const phases = planData.implementation_phases || [];
    const summary = planData.executive_summary || {};
    const timeline = planData.timeline_optimization || {};
    const risk = planData.risk_mitigation || {};
    const governance = planData.governance_framework || {};
    const monitoring = planData.monitoring_strategy || {};
    const intelligence = planData.intelligence_insights || {};
    const contingency = planData.contingency_planning || {};
    const success = planData.success_criteria || {};

    if (!phases || phases.length === 0) {
        console.warn('⚠️ No phases found to display');
        showNoAnalysisMessage(container);
        return;
    }

    // Calculate totals
    const totalSavings = phases.reduce((sum, phase) => sum + (phase.projected_savings || 0), 0);
    const totalWeeks = Math.max(...phases.map(phase => phase.end_week || phase.duration_weeks || 0));

    let html = `
        <!-- EXECUTIVE SUMMARY HEADER (Always Visible) -->
        <div class="card border-0 shadow-lg mb-4">
            <div class="card-body text-white">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h3 class="card-title mb-3">
                            <i class="fas fa-rocket me-2"></i>Complete Implementation Plan Ready
                        </h3>
                        <div class="mb-3">
                            <strong>Cluster:</strong> ${summary.implementation_overview?.cluster_name || planData.metadata?.cluster_name || 'N/A'} 
                            <span class="mx-2">•</span>
                            <strong>Resource Group:</strong> ${summary.implementation_overview?.resource_group || planData.metadata?.resource_group || 'N/A'}
                        </div>
                        <p class="mb-0 opacity-90">
                            ${summary.implementation_overview?.summary || `This ${totalWeeks}-week implementation plan will optimize your AKS cluster through ${phases.length} carefully planned phases.`}
                        </p>
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="badge fs-6 px-3 py-2" style="background: rgba(255,255,255,0.2);">
                            <i class="fas fa-shield-alt me-1"></i>
                            ${risk.overall_risk || 'Low'} Risk
                        </div>
                    </div>
                </div>
                
                <div class="row g-3 mt-3">
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">${phases.length}</div>
                            <small class="opacity-90">Phases</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">${totalWeeks || timeline.base_timeline_weeks || 'TBD'}</div>
                            <small class="opacity-90">Total Weeks</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">$${totalSavings.toLocaleString()}</div>
                            <small class="opacity-90">Monthly Savings</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">${((planData.metadata?.confidence_level || 'High') === 'High' ? '95' : '85')}%</div>
                            <small class="opacity-90">Confidence</small>
                        </div>
                    </div>
                </div>
                
                <!-- EXPAND/COLLAPSE ALL CONTROLS -->
                <div class="text-center mt-4 pt-3 border-top border-light border-opacity-25">
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-light btn-sm" onclick="expandAllSections()">
                            <i class="fas fa-expand-alt me-1"></i>Expand All
                        </button>
                        <button type="button" class="btn btn-light btn-sm" onclick="collapseAllSections()">
                            <i class="fas fa-compress-alt me-1"></i>Collapse All
                        </button>
                        <button type="button" class="btn btn-light btn-sm" onclick="togglePhaseDetails()">
                            <i class="fas fa-eye me-1"></i>Toggle Details
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- COLLAPSIBLE QUICK OVERVIEW -->
        ${renderQuickOverview(summary, intelligence, phases)}
    `;

    // RENDER COLLAPSIBLE IMPLEMENTATION PHASES
    html += `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-primary text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#implementation-phases-section">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">
                        <i class="fas fa-cogs me-2"></i>Implementation Phases (${phases.length} phases)
                    </h5>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse show" id="implementation-phases-section">
                <div class="card-body p-0">
                    ${renderCollapsiblePhases(phases)}
                </div>
            </div>
        </div>
    `;

    // RENDER OTHER COLLAPSIBLE SECTIONS
    html += `
        <!-- GOVERNANCE & STRATEGY SECTIONS -->
        ${renderCollapsibleGovernanceFramework(governance)}
        ${renderCollapsibleMonitoringStrategy(monitoring)}
        ${renderCollapsibleContingencyPlanning(contingency)}
        ${renderCollapsibleSuccessCriteria(success)}
        ${renderCollapsibleTimelineOptimization(timeline)}
        
        <!-- ACTION BUTTONS -->
        <!--${renderActionButtons(totalSavings)}-->
    `;

    container.innerHTML = html;
    addImplementationPlanCSS();
    addCollapsibleCSS();
    
    console.log('✅ COLLAPSIBLE Implementation plan displayed successfully');
}

/**
 * Render Quick Overview Section
 */
function renderQuickOverview(summary, intelligence, phases) {
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-info text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#quick-overview">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">
                        <i class="fas fa-eye me-2"></i>Quick Overview & Key Insights
                    </h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="quick-overview">
                <div class="card-body">
                    ${renderKeyRecommendations(summary)}
                    ${renderIntelligenceInsights(intelligence)}
                    ${renderPhasesSummary(phases)}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Phases Summary
 */
function renderPhasesSummary(phases) {
    return `
        <div class="row">
            <div class="col-12">
                <h6 class="text-primary mb-3"><i class="fas fa-list-ol me-2"></i>Phases Summary</h6>
                <div class="row">
                    ${phases.map((phase, idx) => `
                        <div class="col-md-6 col-lg-4 mb-3">
                            <div class="card border-start border-4 border-primary">
                                <div class="card-body p-3">
                                    <h6 class="card-title mb-2">Phase ${phase.phase_number || idx + 1}</h6>
                                    <p class="card-text small mb-2">${phase.title}</p>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="badge bg-success">$${phase.projected_savings.toLocaleString()}/mo</span>
                                        <small class="text-muted">${phase.duration_weeks}w</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Collapsible Phases
 */
function renderCollapsiblePhases(phases) {
    return phases.map((phase, idx) => `
        <div class="phase-container border-bottom">
            <!-- Phase Header (Always Visible) -->
            <div class="phase-header p-3" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); cursor: pointer;" 
                 data-bs-toggle="collapse" data-bs-target="#phase-${phase.phase_number || idx + 1}">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <h5 class="mb-0 me-3">
                            <i class="fas fa-cog me-2 text-primary"></i>
                            Phase ${phase.phase_number || idx + 1}: ${phase.title}
                        </h5>
                        <div class="d-flex gap-2">
                            <span class="badge bg-light text-dark">${phase.duration_weeks} weeks</span>
                            <span class="badge bg-success">$${phase.projected_savings.toLocaleString()}/mo</span>
                            <span class="badge bg-${getPriorityColor(phase.priority_level)}">${phase.priority_level}</span>
                        </div>
                    </div>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
                <div class="mt-2">
                    <small class="text-muted">
                        Week ${phase.start_week} - ${phase.end_week} • 
                        ${phase.complexity_level} Complexity • 
                        ${phase.risk_level} Risk • 
                        ${phase.tasks?.length || 0} Tasks
                    </small>
                </div>
            </div>
            
            <!-- Phase Details (Collapsible) -->
            <div class="collapse" id="phase-${phase.phase_number || idx + 1}">
                <div class="card-body">
                    <!-- Phase Overview -->
                    <div class="row mb-4">
                        <div class="col-md-8">
                            <div class="row">
                                <div class="col-sm-6">
                                    <strong>📅 Timeline:</strong> Week ${phase.start_week} - ${phase.end_week}<br>
                                    <strong>🔧 Complexity:</strong> ${phase.complexity_level}<br>
                                    <strong>🛡️ Risk Level:</strong> <span class="badge bg-${getRiskColor(phase.risk_level)}">${phase.risk_level}</span>
                                </div>
                                <div class="col-sm-6">
                                    <strong>👥 Engineering Hours:</strong> ${phase.resource_requirements?.engineering_hours || 'TBD'}<br>
                                    <strong>💼 FTE Estimate:</strong> ${phase.resource_requirements?.fte_estimate || 'TBD'}<br>
                                    <strong>🎯 Type:</strong> ${phase.type}
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="alert alert-success mb-0">
                                <div class="text-center">
                                    <div class="h4 mb-1">$${phase.projected_savings.toLocaleString()}</div>
                                    <small>Monthly Savings Target</small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- COLLAPSIBLE SUB-SECTIONS -->
                    ${renderCollapsibleImplementationTasks(phase)}
                    ${renderCollapsibleSuccessCriteria(phase)}
                    ${renderCollapsibleValidationSteps(phase)}
                    ${renderCollapsibleMonitoringRequirements(phase)}
                    ${renderCollapsibleRollbackPlan(phase)}
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * Render Collapsible Implementation Tasks
 */
function renderCollapsibleImplementationTasks(phase) {
    if (!phase.tasks?.length) return '';
    
    return `
        <div class="mb-4">
            <div class="collapsible-section-header" data-bs-toggle="collapse" data-bs-target="#tasks-${phase.phase_number}">
                <h6 class="text-primary mb-0">
                    <i class="fas fa-tasks me-2"></i>Implementation Tasks (${phase.tasks.length} tasks)
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </h6>
            </div>
            
            <div class="collapse show" id="tasks-${phase.phase_number}">
                <div class="mt-3">
                    ${phase.tasks.map((task, idx) => {
                        const taskId = `task-${phase.phase_number || 0}-${idx}`;
                        const commandId = `cmd-${phase.phase_number || 0}-${idx}`;
                        
                        return `
                            <div class="task-block mb-3 border rounded">
                                <!-- Task Header (Always Visible) -->
                                <div class="task-header p-3 bg-light border-bottom" style="cursor: pointer;" 
                                     data-bs-toggle="collapse" data-bs-target="#${taskId}">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div class="flex-grow-1">
                                            <h6 class="mb-1">
                                                <span class="badge bg-primary me-2">${idx + 1}</span>
                                                ${task.title}
                                                <i class="fas fa-chevron-down collapse-icon"></i>
                                            </h6>
                                            <p class="text-muted mb-2 small">${task.description}</p>
                                            <div class="row text-sm">
                                                <div class="col-md-6">
                                                    <small><strong>⏱️ Hours:</strong> ${task.estimated_hours} | <strong>🎯 ID:</strong> ${task.task_id}</small>
                                                </div>
                                                <div class="col-md-6">
                                                    <small><strong>📦 Deliverable:</strong> ${task.deliverable.substring(0, 50)}...</small>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Task Details (Collapsible) -->
                                <div class="collapse" id="${taskId}">
                                    <div class="task-commands p-3">
                                        <div class="mb-3">
                                            <strong>🎯 Expected Outcome:</strong><br>
                                            <small class="text-muted">${task.expected_outcome}</small>
                                        </div>
                                        
                                        <!-- Commands Section -->
                                        <div class="d-flex justify-content-between align-items-center mb-2">
                                            <h6 class="mb-0"><i class="fas fa-terminal me-2"></i>Commands to Execute</h6>
                                            <button class="btn btn-sm btn-outline-primary copy-btn" onclick="copyCommand('${commandId}')">
                                                <i class="fas fa-copy me-1"></i>Copy All Commands
                                            </button>
                                        </div>
                                        <div class="command-wrapper">
                                            <pre class="command-code" id="${commandId}"><code>${escapeHtml(task.command)}</code></pre>
                                        </div>
                                        
                                        ${task.skills_required?.length ? `
                                            <div class="mt-3">
                                                <strong>🔧 Skills Required:</strong>
                                                ${task.skills_required.map(skill => `<span class="badge bg-secondary me-1">${skill}</span>`).join('')}
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render other collapsible sections
 */
function renderCollapsibleSuccessCriteria(phase) {
    if (!phase.success_criteria?.length) return '';
    
    return `
        <div class="mb-4">
            <div class="collapsible-section-header" data-bs-toggle="collapse" data-bs-target="#success-${phase.phase_number}">
                <h6 class="text-success mb-0">
                    <i class="fas fa-trophy me-2"></i>Success Criteria (${phase.success_criteria.length})
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </h6>
            </div>
            <div class="collapse" id="success-${phase.phase_number}">
                <ul class="list-group list-group-flush mt-2">
                    ${phase.success_criteria.map(criteria => `
                        <li class="list-group-item border-0 px-0">
                            <i class="fas fa-check-circle text-success me-2"></i>${criteria}
                        </li>
                    `).join('')}
                </ul>
            </div>
        </div>
    `;
}

function renderCollapsibleValidationSteps(phase) {
    if (!phase.validation_steps?.length) return '';
    
    return `
        <div class="mb-4">
            <div class="collapsible-section-header" data-bs-toggle="collapse" data-bs-target="#validation-${phase.phase_number}">
                <h6 class="text-info mb-0">
                    <i class="fas fa-clipboard-check me-2"></i>Validation Steps (${phase.validation_steps.length})
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </h6>
            </div>
            <div class="collapse" id="validation-${phase.phase_number}">
                <ul class="list-group list-group-flush mt-2">
                    ${phase.validation_steps.map(step => `
                        <li class="list-group-item border-0 px-0">
                            <i class="fas fa-check text-info me-2"></i>${step}
                        </li>
                    `).join('')}
                </ul>
            </div>
        </div>
    `;
}

function renderCollapsibleMonitoringRequirements(phase) {
    if (!phase.monitoring_requirements) return '';
    
    const monitoring = phase.monitoring_requirements;
    return `
        <div class="mb-4">
            <div class="collapsible-section-header" data-bs-toggle="collapse" data-bs-target="#monitoring-${phase.phase_number}">
                <h6 class="text-warning mb-0">
                    <i class="fas fa-chart-line me-2"></i>Monitoring Requirements
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </h6>
            </div>
            <div class="collapse" id="monitoring-${phase.phase_number}">
                <div class="mt-2">
                    <div class="row">
                        <div class="col-md-6">
                            <strong>📊 Key Metrics:</strong>
                            <ul class="list-unstyled mt-1">
                                ${(monitoring.key_metrics || []).map(metric => `
                                    <li><i class="fas fa-dot-circle text-warning me-2"></i>${metric}</li>
                                `).join('')}
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <strong>🔔 Alert Thresholds:</strong>
                            <ul class="list-unstyled mt-1">
                                ${Object.entries(monitoring.alert_thresholds || {}).map(([key, value]) => `
                                    <li><strong>${key.replace(/_/g, ' ')}:</strong> ${value}</li>
                                `).join('')}
                            </ul>
                            <strong>📅 Frequency:</strong> ${monitoring.monitoring_frequency}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderCollapsibleRollbackPlan(phase) {
    if (!phase.rollback_plan) return '';
    
    const rollback = phase.rollback_plan;
    return `
        <div class="mb-4">
            <div class="collapsible-section-header" data-bs-toggle="collapse" data-bs-target="#rollback-${phase.phase_number}">
                <h6 class="text-danger mb-0">
                    <i class="fas fa-undo me-2"></i>Rollback Plan
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </h6>
            </div>
            <div class="collapse" id="rollback-${phase.phase_number}">
                <div class="alert alert-light border-start border-4 border-danger mt-2">
                    <div class="row">
                        <div class="col-md-6">
                            <strong>⏱️ Rollback Time:</strong> ${rollback.rollback_time_estimate}<br>
                            <strong>📢 Communication:</strong> ${rollback.communication_plan}
                        </div>
                        <div class="col-md-6">
                            <strong>🚨 Trigger Conditions:</strong>
                            <ul class="list-unstyled mt-1">
                                ${(rollback.trigger_conditions || []).map(condition => `
                                    <li><i class="fas fa-exclamation-triangle text-danger me-1"></i>${condition}</li>
                                `).join('')}
                            </ul>
                        </div>
                    </div>
                    
                    ${rollback.rollback_steps?.length ? `
                        <div class="mt-3">
                            <strong>📋 Rollback Steps:</strong>
                            <ol class="mt-2">
                                ${rollback.rollback_steps.map(step => `<li>${step}</li>`).join('')}
                            </ol>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

// Keep existing helper functions
function renderKeyRecommendations(summary) {
    if (!summary.key_recommendations?.length) return '';
    
    return `
        <div class="mb-4">
            <h6 class="text-info mb-3"><i class="fas fa-lightbulb me-2"></i>Key Recommendations</h6>
            <div class="row">
                ${summary.key_recommendations.map((rec, idx) => `
                    <div class="col-md-4 mb-2">
                        <div class="d-flex align-items-center">
                            <span class="badge bg-info rounded-circle me-2">${idx + 1}</span>
                            <span>${rec}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
            ${summary.strategic_priorities?.length ? `
                <div class="mt-3 pt-3 border-top">
                    <strong>🎯 Strategic Priority:</strong> ${summary.strategic_priorities[0]}
                </div>
            ` : ''}
        </div>
    `;
}

function renderIntelligenceInsights(intelligence) {
    if (!intelligence.ai_recommendations?.length) return '';
    
    return `
        <div class="mb-4">
            <h6 class="text-purple mb-3"><i class="fas fa-brain me-2"></i>AI Intelligence Insights</h6>
            ${intelligence.ai_recommendations.map(rec => `
                <div class="alert alert-light border-start border-4 border-purple">
                    <i class="fas fa-robot me-2 text-purple"></i>${rec}
                </div>
            `).join('')}
        </div>
    `;
}

// Collapsible framework sections (simplified for brevity)
function renderCollapsibleGovernanceFramework(governance) {
    if (!governance || Object.keys(governance).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-dark text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#governance-section">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-gavel me-2"></i>Governance Framework</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="governance-section">
                <div class="card-body">
                    ${governance.approval_workflows?.length ? `
                        <div class="mb-4">
                            <h6 class="text-primary"><i class="fas fa-check-circle me-2"></i>Approval Workflows</h6>
                            ${governance.approval_workflows.map(workflow => `
                                <div class="alert alert-light border-start border-4 border-primary mb-3">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <strong>📋 Stage:</strong> ${workflow.stage || 'N/A'}<br>
                                            <strong>👤 Approver:</strong> ${workflow.approver || 'N/A'}
                                        </div>
                                        <div class="col-md-6">
                                            <strong>⏱️ SLA:</strong> ${workflow.sla || 'N/A'}<br>
                                            <strong>📝 Requirements:</strong> ${workflow.requirements || 'Standard approval process'}
                                        </div>
                                    </div>
                                    <div class="mt-2">
                                        <strong>📄 Description:</strong> ${workflow.description || 'Standard governance approval workflow'}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    ${governance.change_management ? `
                        <div class="mb-4">
                            <h6 class="text-warning"><i class="fas fa-exchange-alt me-2"></i>Change Management</h6>
                            <div class="alert alert-light border-start border-4 border-warning">
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>🔄 Process:</strong> ${governance.change_management.process || 'Standard change management'}<br>
                                        <strong>📋 Documentation:</strong> ${governance.change_management.documentation_requirements || 'Required'}
                                    </div>
                                    <div class="col-md-6">
                                        <strong>✅ Approval Required:</strong> ${governance.change_management.approval_required ? 'Yes' : 'No'}<br>
                                        <strong>🔙 Rollback Plan:</strong> ${governance.change_management.rollback_required ? 'Required' : 'Optional'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${governance.compliance_requirements ? `
                        <div class="mb-4">
                            <h6 class="text-info"><i class="fas fa-shield-alt me-2"></i>Compliance Requirements</h6>
                            <div class="alert alert-light border-start border-4 border-info">
                                <strong>📜 Standards:</strong> ${governance.compliance_requirements.standards || 'Industry standard compliance'}<br>
                                <strong>🔒 Security:</strong> ${governance.compliance_requirements.security_requirements || 'Standard security protocols'}<br>
                                <strong>📊 Auditing:</strong> ${governance.compliance_requirements.audit_requirements || 'Regular compliance audits'}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${governance.decision_framework ? `
                        <div class="mb-4">
                            <h6 class="text-success"><i class="fas fa-sitemap me-2"></i>Decision Framework</h6>
                            <div class="alert alert-light border-start border-4 border-success">
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>🎯 Decision Criteria:</strong><br>
                                        <ul class="list-unstyled mt-2">
                                            ${(governance.decision_framework.criteria || ['Cost impact', 'Risk level', 'Resource availability']).map(criteria => `
                                                <li><i class="fas fa-check text-success me-2"></i>${criteria}</li>
                                            `).join('')}
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <strong>🚨 Escalation Path:</strong> ${governance.decision_framework.escalation_path || 'Standard escalation'}<br>
                                        <strong>⏰ Timeline:</strong> ${governance.decision_framework.decision_timeline || '24-48 hours'}
                                    </div>
                                </div>
                                
                                ${governance.decision_framework.rollback_triggers?.length ? `
                                    <div class="mt-3">
                                        <strong>🔙 Rollback Triggers:</strong>
                                        <ul class="list-unstyled mt-2">
                                            ${governance.decision_framework.rollback_triggers.map(trigger => `
                                                <li><i class="fas fa-exclamation-triangle text-warning me-2"></i>${trigger}</li>
                                            `).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${!governance.approval_workflows?.length && !governance.change_management && !governance.compliance_requirements && !governance.decision_framework ? `
                        <div class="text-center text-muted py-4">
                            <i class="fas fa-info-circle fa-2x mb-3"></i>
                            <p>No specific governance framework defined for this implementation.</p>
                            <small>Standard organizational governance processes will apply.</small>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderCollapsibleMonitoringStrategy(monitoring) {
    if (!monitoring || Object.keys(monitoring).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-warning text-dark" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#monitoring-section">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-chart-bar me-2"></i>Monitoring Strategy</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="monitoring-section">
                <div class="card-body">
                    ${monitoring.health_checks?.length ? `
                        <div class="mb-4">
                            <h6 class="text-danger"><i class="fas fa-heartbeat me-2"></i>Health Checks (${monitoring.health_checks.length})</h6>
                            <div class="row">
                                ${monitoring.health_checks.map(check => `
                                    <div class="col-md-6 mb-2">
                                        <div class="alert alert-light border-start border-4 border-danger">
                                            <i class="fas fa-heartbeat text-danger me-2"></i>${check}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${monitoring.automated_alerting?.length ? `
                        <div class="mb-4">
                            <h6 class="text-warning"><i class="fas fa-bell me-2"></i>Automated Alerting (${monitoring.automated_alerting.length})</h6>
                            ${monitoring.automated_alerting.map(alert => `
                                <div class="alert alert-light border-start border-4 border-warning mb-3">
                                    <div class="row">
                                        <div class="col-md-4">
                                            <strong>📊 Metric:</strong> ${alert.metric || 'N/A'}
                                        </div>
                                        <div class="col-md-4">
                                            <strong>🎯 Threshold:</strong> ${alert.threshold || 'N/A'}
                                        </div>
                                        <div class="col-md-4">
                                            <strong>⚡ Action:</strong> ${alert.action || 'Alert'}
                                        </div>
                                    </div>
                                    <div class="mt-2">
                                        <strong>📝 Description:</strong> ${alert.description || 'Automated monitoring alert'}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    ${monitoring.cost_monitoring ? `
                        <div class="mb-4">
                            <h6 class="text-success"><i class="fas fa-dollar-sign me-2"></i>Cost Monitoring</h6>
                            <div class="alert alert-light border-start border-4 border-success">
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>📈 Tracking:</strong> ${monitoring.cost_monitoring.tracking_method || 'Azure Cost Management'}<br>
                                        <strong>📅 Frequency:</strong> ${monitoring.cost_monitoring.frequency || 'Daily'}
                                    </div>
                                    <div class="col-md-6">
                                        <strong>🎯 Budget Alerts:</strong> ${monitoring.cost_monitoring.budget_alerts ? 'Enabled' : 'Disabled'}<br>
                                        <strong>📊 Reporting:</strong> ${monitoring.cost_monitoring.reporting || 'Weekly reports'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${monitoring.performance_tracking ? `
                        <div class="mb-4">
                            <h6 class="text-info"><i class="fas fa-tachometer-alt me-2"></i>Performance Tracking</h6>
                            <div class="alert alert-light border-start border-4 border-info">
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>📊 Metrics:</strong> ${monitoring.performance_tracking.key_metrics || 'CPU, Memory, Network'}<br>
                                        <strong>⏱️ Interval:</strong> ${monitoring.performance_tracking.collection_interval || '1 minute'}
                                    </div>
                                    <div class="col-md-6">
                                        <strong>📈 Retention:</strong> ${monitoring.performance_tracking.data_retention || '30 days'}<br>
                                        <strong>🔍 Analysis:</strong> ${monitoring.performance_tracking.analysis_frequency || 'Weekly'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${!monitoring.health_checks?.length && !monitoring.automated_alerting?.length && !monitoring.cost_monitoring && !monitoring.performance_tracking ? `
                        <div class="text-center text-muted py-4">
                            <i class="fas fa-chart-line fa-2x mb-3"></i>
                            <p>No specific monitoring strategy defined.</p>
                            <small>Standard Kubernetes and Azure monitoring will be used.</small>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderCollapsibleContingencyPlanning(contingency) {
    if (!contingency || Object.keys(contingency).length === 0) return '';
    
    const contingencyTypes = [
        { key: 'business_contingencies', title: 'Business Contingencies', icon: 'briefcase', color: 'primary' },
        { key: 'technical_contingencies', title: 'Technical Contingencies', icon: 'cogs', color: 'info' },
        { key: 'resource_contingencies', title: 'Resource Contingencies', icon: 'users', color: 'warning' },
        { key: 'timeline_contingencies', title: 'Timeline Contingencies', icon: 'clock', color: 'danger' }
    ];
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-secondary text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#contingency-section">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-shield-alt me-2"></i>Contingency Planning</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="contingency-section">
                <div class="card-body">
                    <div class="row">
                        ${contingencyTypes.map(type => {
                            const items = contingency[type.key] || [];
                            if (!items.length) return '';
                            
                            return `
                                <div class="col-md-6 mb-4">
                                    <h6 class="text-${type.color}"><i class="fas fa-${type.icon} me-2"></i>${type.title}</h6>
                                    ${items.map(item => `
                                        <div class="alert alert-light border-start border-4 border-${type.color} mb-3">
                                            <div class="mb-2">
                                                <strong>🎯 Scenario:</strong> ${item.scenario || 'Contingency scenario'}
                                            </div>
                                            <div class="mb-2">
                                                <strong>📋 Response:</strong> ${item.response || 'Mitigation response'}
                                            </div>
                                            <div class="row">
                                                <div class="col-6">
                                                    <small><strong>💥 Impact:</strong> ${item.impact || 'Medium'}</small>
                                                </div>
                                                <div class="col-6">
                                                    <small><strong>📊 Probability:</strong> ${item.probability || 'Low'}</small>
                                                </div>
                                            </div>
                                            ${item.mitigation_steps?.length ? `
                                                <div class="mt-2">
                                                    <strong>🔧 Mitigation Steps:</strong>
                                                    <ol class="mt-1 mb-0">
                                                        ${item.mitigation_steps.map(step => `<li>${step}</li>`).join('')}
                                                    </ol>
                                                </div>
                                            ` : ''}
                                        </div>
                                    `).join('')}
                                </div>
                            `;
                        }).filter(Boolean).join('')}
                    </div>
                    
                    ${contingencyTypes.every(type => !(contingency[type.key]?.length)) ? `
                        <div class="text-center text-muted py-4">
                            <i class="fas fa-shield-alt fa-2x mb-3"></i>
                            <p>No specific contingency plans defined.</p>
                            <small>Standard risk mitigation procedures will apply.</small>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderCollapsibleSuccessCriteria(success) {
    if (!success || Object.keys(success).length === 0) return '';
    
    const criteriaTypes = [
        { key: 'financial_success_criteria', title: 'Financial Success', icon: 'dollar-sign', color: 'success' },
        { key: 'operational_success_criteria', title: 'Operational Success', icon: 'cogs', color: 'primary' },
        { key: 'performance_success_criteria', title: 'Performance Success', icon: 'tachometer-alt', color: 'info' },
        { key: 'timeline_success_criteria', title: 'Timeline Success', icon: 'clock', color: 'warning' },
        { key: 'sustainability_metrics', title: 'Sustainability Metrics', icon: 'leaf', color: 'success' }
    ];
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-success text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#success-section">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-target me-2"></i>Overall Success Criteria</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="success-section">
                <div class="card-body">
                    <div class="row">
                        ${criteriaTypes.map(type => {
                            const criteria = success[type.key];
                            if (!criteria || typeof criteria !== 'object') return '';
                            
                            return `
                                <div class="col-md-6 mb-4">
                                    <h6 class="text-${type.color}"><i class="fas fa-${type.icon} me-2"></i>${type.title}</h6>
                                    <div class="alert alert-light border-start border-4 border-${type.color}">
                                        ${Object.entries(criteria).map(([key, value]) => `
                                            <div class="mb-2">
                                                <strong>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> ${value}
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            `;
                        }).filter(Boolean).join('')}
                    </div>
                    
                    ${criteriaTypes.every(type => !success[type.key] || typeof success[type.key] !== 'object') ? `
                        <div class="text-center text-muted py-4">
                            <i class="fas fa-target fa-2x mb-3"></i>
                            <p>No specific success criteria defined.</p>
                            <small>Standard project success metrics will apply.</small>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderCollapsibleTimelineOptimization(timeline) {
    if (!timeline || Object.keys(timeline).length === 0) return '';
    
    return `
        <div class="card border-0 shadow mb-4">
            <div class="card-header bg-info text-white" style="cursor: pointer;" data-bs-toggle="collapse" data-bs-target="#timeline-section">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-calendar-alt me-2"></i>Timeline Optimization</h6>
                    <i class="fas fa-chevron-down collapse-icon"></i>
                </div>
            </div>
            <div class="collapse" id="timeline-section">
                <div class="card-body">
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <div class="alert alert-light border-start border-4 border-info">
                                <h6 class="text-info"><i class="fas fa-calendar me-2"></i>Timeline Details</h6>
                                <div class="mb-2"><strong>📅 Base Timeline:</strong> ${timeline.base_timeline_weeks || 'N/A'} weeks</div>
                                <div class="mb-2"><strong>⚡ Parallelization Benefit:</strong> ${timeline.parallelization_benefit || 0} weeks saved</div>
                                <div class="mb-2"><strong>🔧 Complexity Adjustment:</strong> ${timeline.complexity_adjustment || 0} weeks</div>
                                <div><strong>🎯 Total Optimized:</strong> ${timeline.total_timeline_weeks || timeline.base_timeline_weeks || 'N/A'} weeks</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="alert alert-light border-start border-4 border-success">
                                <h6 class="text-success"><i class="fas fa-chart-line me-2"></i>Efficiency Metrics</h6>
                                <div class="mb-2"><strong>📊 Timeline Confidence:</strong> ${((timeline.timeline_confidence || 0.8) * 100).toFixed(0)}%</div>
                                <div class="mb-2"><strong>🚀 Optimization Score:</strong> ${timeline.optimization_score || 'High'}</div>
                                <div><strong>🎯 Delivery Confidence:</strong> ${timeline.delivery_confidence || 'High'}</div>
                            </div>
                        </div>
                    </div>
                    
                    ${timeline.critical_path?.length ? `
                        <div class="mb-4">
                            <h6 class="text-danger"><i class="fas fa-route me-2"></i>Critical Path</h6>
                            <div class="alert alert-light border-start border-4 border-danger">
                                <ul class="list-unstyled mb-0">
                                    ${timeline.critical_path.map(path => `
                                        <li class="mb-2"><i class="fas fa-arrow-right text-danger me-2"></i>${path}</li>
                                    `).join('')}
                                </ul>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${timeline.resource_requirements ? `
                        <div class="mb-4">
                            <h6 class="text-warning"><i class="fas fa-users me-2"></i>Resource Requirements</h6>
                            <div class="alert alert-light border-start border-4 border-warning">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-2"><strong>👥 Team Size:</strong> ${timeline.resource_requirements.team_size || 'N/A'}</div>
                                        <div class="mb-2"><strong>⏱️ Total Hours:</strong> ${timeline.resource_requirements.total_hours || 'N/A'}</div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-2"><strong>💼 FTE Required:</strong> ${timeline.resource_requirements.fte_required || 'N/A'}</div>
                                        <div><strong>📅 Peak Period:</strong> ${timeline.resource_requirements.peak_period || 'N/A'}</div>
                                    </div>
                                </div>
                                
                                ${timeline.resource_requirements.specialized_skills_needed?.length ? `
                                    <div class="mt-3">
                                        <strong>🔧 Specialized Skills:</strong>
                                        <div class="mt-2">
                                            ${timeline.resource_requirements.specialized_skills_needed.map(skill => 
                                                `<span class="badge bg-warning text-dark me-1">${skill}</span>`
                                            ).join('')}
                                        </div>
                                    </div>
                                ` : `
                                    <div class="mt-3">
                                        <small class="text-muted"><i class="fas fa-info-circle me-1"></i>No specialized skills required beyond standard Kubernetes expertise</small>
                                    </div>
                                `}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${timeline.risks?.length ? `
                        <div class="mb-4">
                            <h6 class="text-danger"><i class="fas fa-exclamation-triangle me-2"></i>Timeline Risks</h6>
                            <div class="alert alert-light border-start border-4 border-danger">
                                <ul class="list-unstyled mb-0">
                                    ${timeline.risks.map(risk => `
                                        <li class="mb-2"><i class="fas fa-exclamation-triangle text-danger me-2"></i>${risk}</li>
                                    `).join('')}
                                </ul>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${!timeline.base_timeline_weeks && !timeline.critical_path?.length && !timeline.resource_requirements && !timeline.risks?.length ? `
                        <div class="text-center text-muted py-4">
                            <i class="fas fa-calendar-alt fa-2x mb-3"></i>
                            <p>Timeline optimization analysis not available.</p>
                            <small>Standard project timeline management will apply.</small>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderActionButtons(totalSavings) {
    return `
        <div class="card border-0 shadow mt-4" style="background: linear-gradient(135deg, #f8f9fa, #e9ecef);">
            <div class="card-body text-center">
                <h5 class="mb-3 text-primary">🚀 Ready to Start Implementation?</h5>
                <div class="d-flex gap-2 justify-content-center flex-wrap mb-3">
                    <button class="btn btn-success btn-lg shadow-sm" onclick="deployOptimizations()">
                        <i class="fas fa-rocket me-2"></i>Deploy Phase 1
                    </button>
                    <button class="btn btn-primary btn-lg shadow-sm" onclick="exportImplementationPlan()">
                        <i class="fas fa-download me-2"></i>Export Complete Plan
                    </button>
                    <button class="btn btn-outline-primary btn-lg shadow-sm" onclick="scheduleOptimization()">
                        <i class="fas fa-calendar me-2"></i>Schedule Review
                    </button>
                    <button class="btn btn-outline-secondary btn-lg shadow-sm" onclick="loadImplementationPlan()">
                        <i class="fas fa-redo me-2"></i>Refresh Plan
                    </button>
                </div>
                
                <div class="pt-3 border-top">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        Complete implementation plan generated on ${new Date().toLocaleDateString()} • 
                        Total potential savings: <strong>$${totalSavings.toLocaleString()}/month</strong>
                    </small>
                </div>
            </div>
        </div>
    `;
}

// Add this at the end of displayImplementationPlan() function
setTimeout(() => {
    // Hide empty sections
    document.querySelectorAll('.card-body').forEach(body => {
        if (body.textContent.includes('No specific') || 
            body.textContent.includes('Standard project') ||
            body.textContent.includes('details...')) {
            body.closest('.card').style.display = 'none';
        }
    });
}, 500);

// Global expand/collapse functions
function expandAllSections() {
    document.querySelectorAll('.collapse:not(.show)').forEach(element => {
        const collapse = new bootstrap.Collapse(element, { show: true });
    });
    showNotification('📖 All sections expanded', 'info', 2000);
}

function collapseAllSections() {
    document.querySelectorAll('.collapse.show').forEach(element => {
        const collapse = new bootstrap.Collapse(element, { hide: true });
    });
    showNotification('📕 All sections collapsed', 'info', 2000);
}

function togglePhaseDetails() {
    const phaseDetails = document.querySelectorAll('[id^="phase-"]');
    const anyExpanded = Array.from(phaseDetails).some(el => el.classList.contains('show'));
    
    if (anyExpanded) {
        phaseDetails.forEach(element => {
            if (element.classList.contains('show')) {
                const collapse = new bootstrap.Collapse(element, { hide: true });
            }
        });
        showNotification('📘 Phase details collapsed', 'info', 2000);
    } else {
        phaseDetails.forEach(element => {
            if (!element.classList.contains('show')) {
                const collapse = new bootstrap.Collapse(element, { show: true });
            }
        });
        showNotification('📗 Phase details expanded', 'info', 2000);
    }
}

// Add collapsible-specific CSS
function addCollapsibleCSS() {
    if (document.getElementById('collapsible-plan-css')) return;
    
    const style = document.createElement('style');
    style.id = 'collapsible-plan-css';
    style.textContent = `
        .collapsible-section-header {
            cursor: pointer;
            padding: 0.5rem 0;
            border-radius: 4px;
            transition: all 0.3s ease;
        }
        
        .collapsible-section-header:hover {
            background-color: rgba(0, 123, 255, 0.05);
        }
        
        .collapse-icon {
            transition: transform 0.3s ease;
            font-size: 0.875rem;
        }
        
        .collapsed .collapse-icon,
        [aria-expanded="false"] .collapse-icon {
            transform: rotate(-90deg);
        }
        
        .phase-container {
            transition: all 0.3s ease;
        }
        
        .phase-container:hover {
            background-color: rgba(0, 0, 0, 0.02);
        }
        
        .phase-header {
            border-left: 4px solid transparent;
            transition: all 0.3s ease;
        }
        
        .phase-header:hover {
            border-left-color: #007bff;
            background: linear-gradient(135deg, #f8f9fa 0%, #e3f2fd 100%) !important;
        }
        
        .task-block {
            transition: all 0.3s ease;
        }
        
        .task-block:hover {
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .card-header[data-bs-toggle="collapse"] {
            transition: all 0.3s ease;
        }
        
        .card-header[data-bs-toggle="collapse"]:hover {
            background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.2)) !important;
        }
        
        @media (max-width: 768px) {
            .phase-header .d-flex {
                flex-direction: column;
                align-items: flex-start !important;
            }
            
            .phase-header .d-flex .d-flex {
                margin-top: 0.5rem;
            }
        }
    `;
    document.head.appendChild(style);
}

// Helper functions (keep existing ones)
function getPriorityColor(priority) {
    switch (priority?.toLowerCase()) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'success';
        default: return 'secondary';
    }
}

function getRiskColor(risk) {
    switch (risk?.toLowerCase()) {
        case 'high': return 'danger';
        case 'medium': return 'warning';  
        case 'low': return 'success';
        default: return 'secondary';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// function copyCommand(elementId) {
//     const element = document.getElementById(elementId);
//     if (!element) return;
    
//     const text = element.textContent || element.innerText;
//     copyToClipboard(text);
// }

function showNoAnalysisMessage(container) {
    container.innerHTML = `
        <div class="text-center py-5">
            <i class="fas fa-info-circle fa-3x text-muted mb-3"></i>
            <h4 class="text-muted">No Implementation Plan Available</h4>
            <p class="text-muted">Run an analysis first to generate your implementation plan</p>
            <div class="mt-3">
                <button class="btn btn-primary me-2" onclick="switchToTab('#analysis')">
                    <i class="fas fa-chart-bar me-1"></i> Run Analysis
                </button>
                <button class="btn btn-outline-secondary" onclick="loadImplementationPlan()">
                    <i class="fas fa-redo me-1"></i> Retry
                </button>
            </div>
        </div>
    `;
}

// Make functions globally available
window.displayImplementationPlan = displayImplementationPlan;
window.expandAllSections = expandAllSections;
window.collapseAllSections = collapseAllSections;
window.togglePhaseDetails = togglePhaseDetails;
window.copyCommand = copyCommand;

/**
 * UPDATED CSS LOADER FOR IMPLEMENTATION PLAN
 * Replace the addImplementationPlanCSS function in your main.js with this:
 */

function addImplementationPlanCSS() {
    // Check if CSS is already loaded
    if (document.getElementById('implementation-plan-css')) return;
    
    // FIXED: Use correct filename and path
    const possiblePaths = [
        '/static/css/implan.css',           // Root-relative path
        '../static/css/implan.css',        // Parent directory
        '../../static/css/implan.css',     // Two levels up
        '/static/implan.css',              // Alternative location
        './static/css/implan.css'          // Current directory
    ];
    
    let pathIndex = 0;
    
    function tryNextPath() {
        if (pathIndex >= possiblePaths.length) {
            // All paths failed, use inline CSS
            console.log('📝 All CSS paths failed, loading inline CSS as fallback');
            loadInlineCSS();
            return;
        }
        
        const currentPath = possiblePaths[pathIndex];
        console.log(`🔍 Trying CSS path: ${currentPath}`);
        
        fetch(currentPath, { method: 'HEAD' })
            .then(response => {
                if (response.ok) {
                    // CSS file found, load it
                    const link = document.createElement('link');
                    link.id = 'implementation-plan-css';
                    link.rel = 'stylesheet';
                    link.type = 'text/css';
                    link.href = currentPath;
                    
                    // Add load event listener to confirm successful loading
                    link.onload = function() {
                        console.log(`✅ Successfully loaded CSS from: ${currentPath}`);
                    };
                    
                    link.onerror = function() {
                        console.log(`❌ Failed to load CSS from: ${currentPath}`);
                        // Remove the failed link and try next path
                        if (link.parentNode) {
                            link.parentNode.removeChild(link);
                        }
                        pathIndex++;
                        tryNextPath();
                    };
                    
                    document.head.appendChild(link);
                } else {
                    throw new Error(`CSS not found at ${currentPath}`);
                }
            })
            .catch(() => {
                pathIndex++;
                tryNextPath();
            });
    }
    
    // Start trying paths
    tryNextPath();
}

function loadInlineCSS() {
    const style = document.createElement('style');
    style.id = 'implementation-plan-css';
    style.textContent = `
        /* Enhanced Implementation Plan Styling - Inline Fallback */
        
        #implementation-plan-container {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #2d3748;
        }
        
        .task-block { 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #dee2e6; 
            border-radius: 12px; 
            margin-bottom: 2rem; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .task-block:hover {
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        .task-header { 
            background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%) !important; 
            border-bottom: 2px solid rgb(0, 255, 234); 
            padding: 1.5rem !important;
            position: relative;
        }
        
        .task-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg,rgb(0, 255, 200),rgb(0, 179, 173));
        }
        
        .task-header h6 {
            color: #2d3748;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .task-commands { 
            background: #ffffff; 
            padding: 1.5rem !important;
            border-top: 1px solid #e9ecef;
        }
        
        .command-wrapper { 
            background: #f8f9fa; 
            border: 1px solid #e9ecef; 
            border-radius: 8px; 
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-top: 1rem; 
        }
        
        .command-code { 
            margin: 0 !important; 
            padding: 1.25rem !important; 
            background: #ffffff !important; 
            border: none !important; 
            border-left: 3px solid rgb(0, 255, 162) !important; 
            overflow-x: auto; 
            overflow-y: hidden;
            white-space: pre;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace !important; 
            font-size: 0.85rem !important; 
            line-height: 1.5 !important; 
            max-height: 400px;
            min-height: 60px;
            scroll-behavior: smooth;
        }
        
        .command-code code { 
            color: #2d3748 !important; 
            background: none !important; 
            padding: 0 !important; 
            font-size: inherit !important;
            font-family: inherit !important;
            white-space: pre !important;
            word-wrap: normal !important;
            word-break: normal !important;
        }
        
        .copy-btn { 
            background: linear-gradient(135deg,rgb(0, 255, 157),rgb(0, 170, 179)) !important; 
            border: none !important; 
            color: white !important; 
            font-size: 0.8rem !important; 
            padding: 0.5rem 1rem !important; 
            border-radius: 6px !important;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
        }
        
        .copy-btn:hover { 
            background: linear-gradient(135deg,rgb(0, 179, 152), #004085) !important; 
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
        }
        
        .copy-btn:active {
            transform: translateY(0);
            box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
        }
        
        .copy-btn.copied { 
            background: linear-gradient(135deg, #28a745, #20c997) !important; 
            transform: scale(0.95);
            transition: all 0.2s ease;
        }
        
        .copy-btn.copied::after {
            content: ' ✓';
        }
        
        /* Enhanced Scrollbars */
        .command-code::-webkit-scrollbar { height: 8px; }
        .command-code::-webkit-scrollbar-track { 
            background: #f1f3f4; 
            border-radius: 4px; 
        }
        .command-code::-webkit-scrollbar-thumb { 
            background: linear-gradient(90deg,rgb(0, 255, 204),rgb(0, 179, 122)); 
            border-radius: 4px;
            transition: background 0.3s ease;
        }
        .command-code::-webkit-scrollbar-thumb:hover { 
            background: linear-gradient(90deg,rgb(0, 167, 179),rgb(0, 109, 133)); 
        }
        
        /* Firefox scrollbar */
        .command-code {
            scrollbar-width: thin;
            scrollbar-color:rgb(0, 255, 242) #f1f3f4;
        }
        
        /* Cards and General Styling */
        .card { 
            border-radius: 12px !important; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
            border: 1px solid rgba(0,0,0,0.08) !important;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            box-shadow: 0 8px 25px rgba(0,0,0,0.1) !important;
            transform: translateY(-2px);
        }
        
        .card-header {
            border-radius: 12px 12px 0 0 !important;
            font-weight: 600;
            border-bottom: 2px solid rgba(255,255,255,0.2) !important;
            padding: 1rem 1.5rem !important;
        }
        
        .card-body {
            padding: 1.5rem !important;
        }
        
        /* Badges */
        .badge { 
            border-radius: 50px; 
            font-size: 0.75rem; 
            font-weight: 500;
            padding: 0.375rem 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge.bg-success {
            background: linear-gradient(135deg, #28a745, #20c997) !important;
        }
        
        .badge.bg-primary {
            background: linear-gradient(135deg,rgb(0, 255, 157),rgb(0, 179, 137)) !important;
        }
        
        .badge.bg-warning {
            background: linear-gradient(135deg, #ffc107, #ff8f00) !important;
            color: #212529 !important;
        }
        
        .badge.bg-danger {
            background: linear-gradient(135deg, #dc3545, #c82333) !important;
        }
        
        /* Alerts */
        .alert { 
            border-radius: 8px !important; 
            border: none !important;
            padding: 1rem 1.25rem !important;
            margin-bottom: 1rem !important;
        }
        
        .alert-success {
            background: linear-gradient(135deg, rgba(40,167,69,0.1), rgba(32,201,151,0.1)) !important;
            border-left: 4px solid #28a745 !important;
            color: #155724 !important;
        }
        
        .alert-light {
            background: #f8f9fa !important;
            border-left: 4px solid #dee2e6 !important;
            color: #6c757d !important;
        }
        
        /* Lists */
        .list-group-item {
            border: none !important;
            padding: 0.75rem 0 !important;
            background: transparent !important;
            border-bottom: 1px solid #f1f3f4 !important;
        }
        
        .list-group-item:last-child {
            border-bottom: none !important;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .task-header {
                padding: 1rem !important;
            }
            
            .task-commands {
                padding: 1rem !important;
            }
            
            .command-code { 
                font-size: 0.8rem !important; 
                padding: 1rem !important; 
            }
            
            .copy-btn { 
                font-size: 0.75rem !important;
                padding: 0.375rem 0.75rem !important;
            }
            
            .card-body {
                padding: 1rem !important;
            }
            
            .card-header {
                padding: 0.75rem 1rem !important;
            }
        }
        
        @media (max-width: 576px) {
            .command-code {
                font-size: 0.75rem !important;
                padding: 0.75rem !important;
            }
            
            .copy-btn {
                width: 100%;
                margin-top: 0.5rem;
            }
        }
        
        /* Dark Mode Support */
        [data-theme="dark"] #implementation-plan-container {
            color: #f7fafc;
        }
        
        [data-theme="dark"] .task-block {
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            border-color: #4a5568;
        }
        
        [data-theme="dark"] .task-header {
            background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%) !important;
            color: #f7fafc !important;
        }
        
        [data-theme="dark"] .command-code {
            background: #1a202c !important;
            color: #f7fafc !important;
            border-left-color: #4299e1 !important;
        }
        
        [data-theme="dark"] .command-code code {
            color: #f7fafc !important;
        }
        
        [data-theme="dark"] .card {
            background: #2d3748 !important;
            border-color: #4a5568 !important;
        }
        
        /* Animations */
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .task-block {
            animation: slideInUp 0.6s ease-out;
        }
        
        .card {
            animation: slideInUp 0.4s ease-out;
        }
    `;
    document.head.appendChild(style);
    console.log('✅ Loaded comprehensive inline CSS');
}

// Make functions globally available
window.displayImplementationPlan = displayImplementationPlan;
window.copyCommand = copyCommand;


/**
 * FIXED: Renders implementation steps section
 */
function renderImplementationSteps(phase) {
    const steps = phase.implementation_steps || phase.steps || [];
    if (!steps.length) return '';
    
    return `
        <div class="mb-4">
            <h6 class="text-primary mb-3">
                <i class="fas fa-list-ol me-2"></i>Implementation Steps
            </h6>
            <div class="row">
                ${steps.map((step, idx) => `
                    <div class="col-md-6 mb-2">
                        <div class="d-flex align-items-start">
                            <span class="badge bg-primary rounded-pill me-2 mt-1">${idx + 1}</span>
                            <span class="flex-grow-1">${step.description || step}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

/**
 * FIXED: Renders commands section with horizontal scrolling and copy functionality
 */
function renderCommandsSection(phase) {
    const commands = phase.commands || phase.kubectl_commands || phase.azure_commands || [];
    if (!commands.length) return '';
    
    return `
        <div class="mb-4">
            <h6 class="text-primary mb-3">
                <i class="fas fa-terminal me-2"></i>Commands to Execute
            </h6>
            <div class="commands-container">
                ${commands.map((cmd, idx) => {
                    const command = typeof cmd === 'string' ? cmd : cmd.command || cmd.cmd;
                    const description = typeof cmd === 'object' ? (cmd.description || cmd.desc) : '';
                    const commandId = `cmd-${Date.now()}-${idx}`;
                    
                    return `
                        <div class="command-block mb-3">
                            ${description ? `<div class="command-description mb-2"><i class="fas fa-info-circle me-1"></i>${description}</div>` : ''}
                            <div class="command-wrapper">
                                <div class="command-header">
                                    <span class="command-label">Command ${idx + 1}</span>
                                    <button class="btn btn-sm btn-outline-primary copy-btn" onclick="copyCommand('${commandId}')">
                                        <i class="fas fa-copy me-1"></i>Copy
                                    </button>
                                </div>
                                <pre class="command-code" id="${commandId}"><code>${escapeHtml(command)}</code></pre>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
}

/**
 * FIXED: Renders configuration section with horizontal scrolling and copy functionality  
 */
function renderConfigurationSection(phase) {
    const configs = phase.configurations || phase.yaml_configs || phase.config_files || [];
    if (!configs.length) return '';
    
    return `
        <div class="mb-4">
            <h6 class="text-primary mb-3">
                <i class="fas fa-cogs me-2"></i>Configuration Files
            </h6>
            <div class="configs-container">
                ${configs.map((config, idx) => {
                    const content = typeof config === 'string' ? config : config.content || config.yaml;
                    const filename = typeof config === 'object' ? (config.filename || config.name || `config-${idx + 1}.yaml`) : `config-${idx + 1}.yaml`;
                    const configId = `config-${Date.now()}-${idx}`;
                    
                    return `
                        <div class="config-block mb-3">
                            <div class="config-wrapper">
                                <div class="config-header">
                                    <span class="config-label">
                                        <i class="fas fa-file-code me-1"></i>${filename}
                                    </span>
                                    <button class="btn btn-sm btn-outline-primary copy-btn" onclick="copyCommand('${configId}')">
                                        <i class="fas fa-copy me-1"></i>Copy
                                    </button>
                                </div>
                                <pre class="config-code" id="${configId}"><code>${escapeHtml(content)}</code></pre>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
}

/**
 * FIXED: Renders prerequisites section
 */
function renderPrerequisitesSection(phase) {
    const prerequisites = phase.prerequisites || phase.requirements || [];
    if (!prerequisites.length) return '';
    
    return `
        <div class="mb-4">
            <h6 class="text-warning mb-3">
                <i class="fas fa-exclamation-triangle me-2"></i>Prerequisites
            </h6>
            <ul class="list-group list-group-flush">
                ${prerequisites.map(req => `
                    <li class="list-group-item border-0 px-0">
                        <i class="fas fa-chevron-right text-warning me-2"></i>${req.description || req}
                    </li>
                `).join('')}
            </ul>
        </div>
    `;
}

/**
 * FIXED: Renders validation section
 */
function renderValidationSection(phase) {
    const validations = phase.validation_steps || phase.verification || [];
    if (!validations.length) return '';
    
    return `
        <div class="mb-4">
            <h6 class="text-success mb-3">
                <i class="fas fa-check-circle me-2"></i>Validation Steps
            </h6>
            <ul class="list-group list-group-flush">
                ${validations.map(validation => `
                    <li class="list-group-item border-0 px-0">
                        <i class="fas fa-check text-success me-2"></i>${validation.description || validation}
                    </li>
                `).join('')}
            </ul>
        </div>
    `;
}

/**
 * FIXED: Helper function to get priority color
 */
function getPriorityColor(priority) {
    switch (priority.toLowerCase()) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'success';
        default: return 'secondary';
    }
}

/**
 * FIXED: Helper function to get risk color
 */
function getRiskColor(risk) {
    switch (risk.toLowerCase()) {
        case 'high': return 'danger';
        case 'medium': return 'warning';  
        case 'low': return 'success';
        default: return 'secondary';
    }
}

/**
 * FIXED: Copy command functionality
 */
// function copyCommand(elementId) {
//     const element = document.getElementById(elementId);
//     if (!element) return;
    
//     const text = element.textContent || element.innerText;
//     copyToClipboard(text);
// }

/**
 * FIXED: Export implementation plan functionality
 */
function exportImplementationPlan() {
    showNotification('Exporting complete implementation plan...', 'info');
    
    fetch('/api/implementation-plan/export')
        .then(response => {
            if (!response.ok) throw new Error('Export failed');
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `aks-implementation-plan-${new Date().toISOString().split('T')[0]}.pdf`;
            a.click();
            window.URL.revokeObjectURL(url);
            showNotification('Implementation plan exported successfully!', 'success');
        })
        .catch(error => {
            console.error('Export error:', error);
            showNotification('Export failed. Creating fallback...', 'warning');
            createFallbackExport();
        });
}


/**
 * ============================================================================
 * FIXED COPY TO CLIPBOARD FUNCTIONALITY
 * ============================================================================
 * Fixes the "Cannot read properties of undefined (reading 'target')" error
 * ============================================================================
 */

/**
 * FIXED: Enhanced copy to clipboard function with proper error handling
 */
function copyToClipboard(text, buttonElement = null) {
    // Get the button element if not provided
    if (!buttonElement && typeof event !== 'undefined' && event.target) {
        buttonElement = event.target.closest('.copy-btn, button');
    }
    
    console.log('📋 Copy function called:', { text, buttonElement });
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            console.log('✅ Successfully copied to clipboard:', text.substring(0, 50) + '...');
            showCopySuccess(buttonElement, 'Copied to clipboard!');
            showNotification('📋 Copied to clipboard!', 'success', 2000);
        }).catch(err => {
            console.error('❌ Clipboard API failed:', err);
            fallbackCopy(text, buttonElement);
        });
    } else {
        console.log('📋 Using fallback copy method');
        fallbackCopy(text, buttonElement);
    }
}

/**
 * FIXED: Fallback copy method for older browsers
 */
function fallbackCopy(text, buttonElement = null) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.cssText = `
        position: fixed !important;
        top: -1000px !important;
        left: -1000px !important;
        width: 1px !important;
        height: 1px !important;
        opacity: 0 !important;
        pointer-events: none !important;
    `;
    
    document.body.appendChild(textArea);
    textArea.select();
    textArea.setSelectionRange(0, 99999);
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            console.log('✅ Fallback copy successful');
            showCopySuccess(buttonElement, 'Copied to clipboard!');
            showNotification('📋 Copied to clipboard!', 'success', 2000);
        } else {
            throw new Error('execCommand failed');
        }
    } catch (err) {
        console.error('❌ Fallback copy failed:', err);
        showCopyError(buttonElement, 'Copy failed');
        showNotification('❌ Failed to copy to clipboard', 'error');
    } finally {
        document.body.removeChild(textArea);
    }
}

/**
 * FIXED: Enhanced copyCommand function
 */
function copyCommand(elementId, buttonElement = null) {
    console.log('📋 copyCommand called with elementId:', elementId);
    
    const element = document.getElementById(elementId);
    if (!element) {
        console.error('❌ Element not found:', elementId);
        showNotification('❌ Content not found', 'error');
        return;
    }
    
    // Get the text content
    const text = element.textContent || element.innerText || element.value;
    if (!text || text.trim() === '') {
        console.error('❌ No text content found in element:', elementId);
        showNotification('❌ No content to copy', 'error');
        return;
    }
    
    // If buttonElement not provided, try to find it
    if (!buttonElement && typeof event !== 'undefined' && event.target) {
        buttonElement = event.target.closest('.copy-btn, button');
    }
    
    copyToClipboard(text.trim(), buttonElement);
}

/**
 * FIXED: Show copy success with visual feedback
 */
function showCopySuccess(buttonElement, message = 'Copied!') {
    if (!buttonElement) {
        console.log('✅ Copy successful (no button element for feedback)');
        return;
    }
    
    // Store original content
    const originalHTML = buttonElement.innerHTML;
    const originalText = buttonElement.textContent;
    
    // Show success state
    buttonElement.classList.add('copied');
    
    // Update button content
    if (buttonElement.querySelector('i')) {
        buttonElement.innerHTML = '<i class="fas fa-check"></i> Copied!';
    } else {
        buttonElement.textContent = 'Copied!';
    }
    
    // Add success styling
    buttonElement.style.background = 'linear-gradient(135deg, #059669, #047857)';
    buttonElement.style.transform = 'scale(0.95)';
    
    // Reset after delay
    setTimeout(() => {
        buttonElement.classList.remove('copied');
        buttonElement.innerHTML = originalHTML;
        buttonElement.style.background = '';
        buttonElement.style.transform = '';
        console.log('🔄 Button state reset');
    }, 2000);
}

/**
 * FIXED: Show copy error with visual feedback
 */
function showCopyError(buttonElement, message = 'Copy failed') {
    if (!buttonElement) {
        console.log('❌ Copy failed (no button element for feedback)');
        return;
    }
    
    const originalHTML = buttonElement.innerHTML;
    
    buttonElement.classList.add('copy-error');
    buttonElement.innerHTML = '<i class="fas fa-exclamation"></i> Failed';
    buttonElement.style.background = 'linear-gradient(135deg, #dc2626, #b91c1c)';
    
    setTimeout(() => {
        buttonElement.classList.remove('copy-error');
        buttonElement.innerHTML = originalHTML;
        buttonElement.style.background = '';
    }, 2000);
}

/**
 * FIXED: Enhanced event handler setup for copy buttons
 */
function setupCopyButtonHandlers() {
    console.log('🔧 Setting up copy button handlers...');
    
    // Remove existing handlers to prevent duplicates
    document.removeEventListener('click', handleCopyButtonClick);
    
    // Add global click handler for copy buttons
    document.addEventListener('click', handleCopyButtonClick);
    
    console.log('✅ Copy button handlers setup complete');
}

/**
 * FIXED: Global copy button click handler
 */
function handleCopyButtonClick(event) {
    const copyBtn = event.target.closest('.copy-btn, [onclick*="copy"], [data-copy]');
    if (!copyBtn) return;
    
    console.log('📋 Copy button clicked:', copyBtn);
    
    // Prevent default action
    event.preventDefault();
    event.stopPropagation();
    
    // Get copy target
    let copyTarget = null;
    let copyText = '';
    
    // Method 1: data-copy attribute
    if (copyBtn.hasAttribute('data-copy')) {
        copyText = copyBtn.getAttribute('data-copy');
        console.log('📋 Method 1: Using data-copy attribute');
    }
    
    // Method 2: data-copy-target attribute
    else if (copyBtn.hasAttribute('data-copy-target')) {
        const targetId = copyBtn.getAttribute('data-copy-target');
        copyTarget = document.getElementById(targetId);
        if (copyTarget) {
            copyText = copyTarget.textContent || copyTarget.innerText || copyTarget.value;
            console.log('📋 Method 2: Using data-copy-target attribute');
        }
    }
    
    // Method 3: Check onclick attribute for element ID
    else if (copyBtn.hasAttribute('onclick')) {
        const onclickValue = copyBtn.getAttribute('onclick');
        const match = onclickValue.match(/copyCommand\(['"]([^'"]+)['"]\)/);
        if (match) {
            const elementId = match[1];
            copyTarget = document.getElementById(elementId);
            if (copyTarget) {
                copyText = copyTarget.textContent || copyTarget.innerText || copyTarget.value;
                console.log('📋 Method 3: Using onclick attribute parsing');
            }
        }
    }
    
    // Method 4: Find nearest code block (fallback)
    else {
        copyTarget = copyBtn.closest('.command-wrapper, .code-block, .task-block')
                           ?.querySelector('.command-code, .code-content, pre, code');
        if (copyTarget) {
            copyText = copyTarget.textContent || copyTarget.innerText;
            console.log('📋 Method 4: Using nearest code block');
        }
    }
    
    // Execute copy if we found content
    if (copyText && copyText.trim()) {
        console.log('📋 Copying text:', copyText.substring(0, 50) + '...');
        copyToClipboard(copyText.trim(), copyBtn);
    } else {
        console.error('❌ No content found to copy');
        showCopyError(copyBtn, 'No content found');
        showNotification('❌ No content found to copy', 'error');
    }
}

/**
 * FIXED: Enhanced notification system
 */
function showNotificationFixed(message, type = 'info', duration = 5000) {
    // Remove existing notifications
    document.querySelectorAll('.notification-toast').forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed notification-toast`;
    toast.style.cssText = `
        top: 100px; 
        right: 20px; 
        z-index: 9999; 
        min-width: 350px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        backdrop-filter: blur(10px);
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;
    
    const iconMap = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas fa-${iconMap[type] || 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" onclick="this.parentNode.remove()"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto-remove
    if (duration > 0) {
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
    }
}

/**
 * FIXED: Replacement for main notification function
 */
if (typeof showNotification === 'undefined') {
    window.showNotification = showNotificationFixed;
}

/**
 * FIXED: Initialize copy functionality
 */
function initializeCopyFunctionality() {
    console.log('🚀 Initializing copy functionality...');
    
    // Setup event handlers
    setupCopyButtonHandlers();
    
    // Make functions globally available
    window.copyToClipboard = copyToClipboard;
    window.copyCommand = copyCommand;
    window.showCopySuccess = showCopySuccess;
    window.showCopyError = showCopyError;
    
    // Ensure copy buttons are visible
    setTimeout(() => {
        const copyButtons = document.querySelectorAll('.copy-btn');
        console.log(`🔍 Found ${copyButtons.length} copy buttons`);
        
        copyButtons.forEach((btn, index) => {
            // Make sure copy buttons are visible
            if (btn.style.opacity === '0' || btn.style.display === 'none') {
                btn.style.opacity = '0.8';
                btn.style.display = 'block';
                console.log(`👁️ Made copy button ${index + 1} visible`);
            }
            
            // Add data attributes for easier targeting
            if (!btn.hasAttribute('data-copy') && !btn.hasAttribute('data-copy-target')) {
                const commandWrapper = btn.closest('.command-wrapper, .code-block');
                const codeElement = commandWrapper?.querySelector('.command-code, .code-content, pre, code');
                if (codeElement && codeElement.id) {
                    btn.setAttribute('data-copy-target', codeElement.id);
                    console.log(`🔗 Added data-copy-target to button ${index + 1}`);
                }
            }
        });
    }, 1000);
    
    console.log('✅ Copy functionality initialization complete');
}


// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCopyFunctionality);
} else {
    initializeCopyFunctionality();
}

console.log('✅ Copy functionality script loaded successfully');

// Make functions globally available
window.copyCommand = copyCommand;
window.exportImplementationPlan = exportImplementationPlan;

/**
 * Shows no analysis message - FIXED
 */
function showNoAnalysisMessage(container) {
    container.innerHTML = `
        <div class="text-center mt-4 mb-4">
            <div class="alert alert-warning">
                <h4><i class="fas fa-exclamation-triangle me-2"></i>No Analysis Available</h4>
                <p>Please run a cost analysis first to generate your personalized implementation plan.</p>
                <button class="btn btn-primary" onclick="switchToTab('#analysis')">
                    <i class="fas fa-search me-2"></i>Run Analysis
                </button>
            </div>
        </div>
    `;
}

/**
 * Shows implementation error message - FIXED
 */
function displayImplementationError(container, message) {
    console.error('❌ Displaying error:', message);
    
    container.innerHTML = `
        <div class="alert alert-danger text-center m-4">
            <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
            <h4>Error Loading Implementation Plan</h4>
            <p>${message}</p>
            <button class="btn btn-outline-primary" onclick="loadImplementationPlan()">
                <i class="fas fa-redo me-2"></i>Try Again
            </button>
        </div>
    `;
}

// ============================================================================
// UI COMPONENTS & NAVIGATION - FIXED
// ============================================================================

/**
 * Switches to specified tab - FIXED
 */
function switchToTab(selector) {
    const button = document.querySelector(`[data-bs-target="${selector}"]`);
    if (button) {
        button.click();
    }
}

// ============================================================================
// PLACEHOLDER FUNCTIONS
// ============================================================================

function analyzeAllClusters() {
    showNotification('Analyzing all clusters... Feature coming soon!', 'info');
}

function showPortfolioAnalytics() {
    showNotification('Portfolio Analytics... Feature coming soon!', 'info');
}

function refreshCharts() {
    showNotification('Refreshing charts...', 'info');
    initializeCharts();
}

function exportReport() {
    showNotification('Report export coming soon!', 'info');
}

function deployOptimizations() {
    showNotification('Deployment feature coming soon!', 'info');
}

function scheduleOptimization() {
    showNotification('Scheduling feature coming soon!', 'info');
}

// ============================================================================
// CSS INJECTION
// ============================================================================

/**
 * Injects necessary CSS for enhanced functionality
 */
function injectEnhancedCSS() {
    if (document.getElementById('enhanced-dashboard-css')) return;
    
    const style = document.createElement('style');
    style.id = 'enhanced-dashboard-css';
    style.textContent = `
        .metric-updated { 
            position: relative; 
            transition: all 0.3s ease;
        }
        
        .metric-updated-indicator { 
            position: absolute; 
            top: -2px; 
            right: -2px; 
            animation: pulse 2s infinite; 
            color: #28a745;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* FIXED: Better data source indicator positioning */
        .data-source-indicator { 
            position: fixed !important; 
            top: 140px !important; 
            right: 20px !important; 
            z-index: 999 !important;
            max-width: 200px !important;
        }
        
        .data-source-badge { 
            background: rgba(255,255,255,0.95) !important; 
            border-radius: 20px !important; 
            padding: 8px 16px !important; 
            display: flex !important; 
            align-items: center !important; 
            gap: 5px !important; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
            font-size: 0.875rem !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .data-source-badge.real-data { 
            border: 1px solid #28a745 !important; 
            color: #28a745 !important; 
        }
        
        .data-source-badge.sample-data { 
            border: 1px solid #ffc107 !important; 
            color: #856404 !important; 
            background: rgba(255,193,7,0.1) !important; 
        }
        
        [data-theme="dark"] .data-source-badge { 
            background: rgba(45,55,72,0.95) !important; 
            color: #f7fafc !important; 
        }
        
        .loading {
            position: relative;
            pointer-events: none;
        }
        
        .loading::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .analysis-progress {
            transition: all 0.3s ease;
            opacity: 0;
            transform: translateY(10px);
        }
        
        .analysis-progress.visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        /* FIXED: Prevent modal backdrop from interfering with form inputs */
        .modal-backdrop {
            z-index: 1040 !important;
        }
        
        .modal {
            z-index: 1050 !important;
        }
        
        /* FIXED: Ensure form inputs are accessible */
        .modal .form-control,
        .modal .form-select {
            position: relative !important;
            z-index: 1055 !important;
        }
    `;
    document.head.appendChild(style);
}

// ============================================================================
// INITIALIZATION & EVENT HANDLERS
// ============================================================================

/**
 * Sets up keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (event) => {
        // Ctrl/Cmd + R to refresh charts
        if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
            event.preventDefault();
            refreshCharts();
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) modalInstance.hide();
            });
        }
    });
}

/**
 * Tests API connectivity
 */
function testAPIConnectivity() {
    fetch(`${AppConfig.API_BASE_URL}/clusters`)
        .then(response => response.json())
        .then(data => {
            console.log('✅ API connectivity test passed');
            if (data.clusters?.length > 0) {
                console.log(`📊 Found ${data.clusters.length} existing clusters`);
            }
        })
        .catch(error => {
            console.error('❌ API connectivity test failed:', error);
            showNotification('API connection failed. Some features may not work.', 'warning');
        });
}

/**
 * Main initialization function
 */
function initializeDashboard() {
    console.log('🚀 Initializing AKS Cost Intelligence Dashboard');
    
    try {
        // Inject enhanced CSS
        injectEnhancedCSS();
        
        // Setup form handlers
        setupFormHandlers();
        
        // Setup input validation
        setupInputValidation();
        
        // Setup keyboard shortcuts
        setupKeyboardShortcuts();
        
        // Auto-initialize charts if dashboard is active
        if (document.querySelector('#dashboard')?.classList.contains('active')) {
            setTimeout(initializeCharts, 500);
        }

        const implementationTab = document.querySelector('#implementation');
        if (implementationTab && implementationTab.classList.contains('active')) {
            setTimeout(() => {
                if (typeof loadImplementationPlan === 'function') {
                    loadImplementationPlan();
                }
            }, 500);
        }
        
        // Test API connectivity
        testAPIConnectivity();
        
        console.log('✅ Dashboard initialization completed');
        
    } catch (error) {
        console.error('❌ Error during initialization:', error);
        showNotification('Dashboard initialization failed: ' + error.message, 'error');
    }
}

// ============================================================================
// GLOBAL EXPORTS
// ============================================================================

// Make functions available globally for HTML onclick handlers
window.selectCluster = selectCluster;
window.analyzeCluster = analyzeCluster;
window.removeCluster = removeCluster;
window.analyzeAllClusters = analyzeAllClusters;
window.showPortfolioAnalytics = showPortfolioAnalytics;
window.refreshCharts = refreshCharts;
window.exportReport = exportReport;
window.deployOptimizations = deployOptimizations;
window.scheduleOptimization = scheduleOptimization;
window.showNotification = showNotification;
window.showToast = showToast;
window.copyToClipboard = window.copyToClipboard || function(text) { /* fallback */ };
window.switchToTab = switchToTab;
window.loadImplementationPlan = window.loadImplementationPlan || function() { /* fallback */ };
window.initializeCharts = initializeCharts;

// Export state and config for external access
window.AppState = AppState;
window.AppConfig = AppConfig;

// ============================================================================
// MAIN ENTRY POINT
// ============================================================================

/**
 * Single DOMContentLoaded event handler
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    initializeDashboard();
    console.log('✅ Fixed AKS Cost Intelligence Dashboard loaded successfully');
});

console.log('✅ Fixed AKS Cost Intelligence Dashboard JavaScript loaded');

// /**
//  * ============================================================================
//  * FIXED MODAL FORM HANDLER
//  * ============================================================================
//  * Fixes form input issues and cancel button functionality
//  * ============================================================================
//  */

// // Enhanced modal and form management
// function setupEnhancedModalHandlers() {
//     console.log('🎯 Setting up enhanced modal handlers...');
    
//     // Add Cluster Modal Handler
//     const addClusterModal = document.getElementById('addClusterModal');
//     if (addClusterModal) {
        
//         // FIXED: Clear form and reset state when modal opens
//         addClusterModal.addEventListener('show.bs.modal', function(event) {
//             console.log('📝 Modal opening - resetting form state');
            
//             const form = this.querySelector('form');
//             if (form) {
//                 // Reset form completely
//                 form.reset();
                
//                 // Clear all validation classes
//                 form.querySelectorAll('.form-control, .form-select').forEach(input => {
//                     input.classList.remove('is-invalid', 'is-valid');
//                     input.disabled = false; // Ensure inputs are enabled
//                     input.readOnly = false; // Ensure inputs are not readonly
//                 });
                
//                 // Reset submit button
//                 const submitBtn = form.querySelector('button[type="submit"]');
//                 if (submitBtn) {
//                     submitBtn.disabled = false;
//                     submitBtn.innerHTML = '<i class="fas fa-plus me-2"></i>Add Cluster & Analyze';
//                 }
                
//                 // Focus on first input after modal animation
//                 setTimeout(() => {
//                     const firstInput = form.querySelector('input[type="text"]');
//                     if (firstInput) {
//                         firstInput.focus();
//                     }
//                 }, 300);
//             }
//         });
        
//         // FIXED: Handle modal close/cancel properly
//         addClusterModal.addEventListener('hide.bs.modal', function(event) {
//             console.log('📝 Modal closing - cleaning up');
            
//             const form = this.querySelector('form');
//             if (form) {
//                 // Reset form state
//                 form.reset();
                
//                 // Clear validation classes
//                 form.querySelectorAll('.form-control, .form-select').forEach(input => {
//                     input.classList.remove('is-invalid', 'is-valid');
//                 });
                
//                 // Reset submit button
//                 const submitBtn = form.querySelector('button[type="submit"]');
//                 if (submitBtn) {
//                     submitBtn.disabled = false;
//                     submitBtn.classList.remove('loading');
//                     submitBtn.innerHTML = '<i class="fas fa-plus me-2"></i>Add Cluster & Analyze';
//                 }
//             }
//         });
        
//         // FIXED: Proper form submission handler
//         const form = addClusterModal.querySelector('form');
//         if (form) {
//             // Remove any existing event listeners to prevent duplicates
//             const newForm = form.cloneNode(true);
//             form.parentNode.replaceChild(newForm, form);
            
//             // Add fresh event listener
//             newForm.addEventListener('submit', handleEnhancedClusterFormSubmission);
//             console.log('✅ Fresh form submit handler attached');
//         }
        
//         // FIXED: Cancel button handler
//         const cancelButtons = addClusterModal.querySelectorAll('[data-bs-dismiss="modal"]');
//         cancelButtons.forEach(btn => {
//             btn.addEventListener('click', function(event) {
//                 console.log('❌ Cancel button clicked');
//                 event.preventDefault();
                
//                 // Close modal properly
//                 const modal = bootstrap.Modal.getInstance(addClusterModal);
//                 if (modal) {
//                     modal.hide();
//                 } else {
//                     addClusterModal.classList.remove('show');
//                     document.querySelector('.modal-backdrop')?.remove();
//                 }
//             });
//         });
//     }
    
//     // Delete Modal Handlers
//     const deleteModal = document.getElementById('deleteClusterModal');
//     if (deleteModal) {
//         const confirmBtn = deleteModal.querySelector('#confirmDeleteBtn');
//         if (confirmBtn) {
//             confirmBtn.addEventListener('click', handleClusterDeletion);
//         }
//     }
    
//     console.log('✅ Enhanced modal handlers setup complete');
// }

// /**
//  * FIXED: Enhanced cluster form submission
//  */
// function handleEnhancedClusterFormSubmission(event) {
//     event.preventDefault();
//     event.stopPropagation();
    
//     console.log('📝 Enhanced cluster form submission started');
    
//     const form = event.target;
//     const formData = new FormData(form);
    
//     // Get form values with proper validation
//     const clusterData = {
//         cluster_name: (formData.get('cluster_name') || '').trim(),
//         resource_group: (formData.get('resource_group') || '').trim(),
//         environment: formData.get('environment') || 'development',
//         region: (formData.get('region') || '').trim(),
//         description: (formData.get('description') || '').trim(),
//         auto_analyze: formData.get('auto_analyze') === 'on' || document.getElementById('auto_analyze')?.checked === true
//     };
    
//     console.log('📋 Form data collected:', clusterData);
    
//     // Enhanced validation
//     if (!clusterData.cluster_name || clusterData.cluster_name.length < 3) {
//         showNotification('Cluster name must be at least 3 characters long', 'error');
//         document.getElementById('cluster_name')?.focus();
//         return;
//     }
    
//     if (!clusterData.resource_group || clusterData.resource_group.length < 3) {
//         showNotification('Resource group name must be at least 3 characters long', 'error');
//         document.getElementById('resource_group')?.focus();
//         return;
//     }
    
//     // Get submit button
//     const submitBtn = form.querySelector('button[type="submit"]');
//     if (!submitBtn) {
//         console.error('❌ Submit button not found');
//         return;
//     }
    
//     // Show loading state
//     const originalHTML = submitBtn.innerHTML;
//     submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding Cluster...';
//     submitBtn.disabled = true;
    
//     // Disable form inputs during submission
//     form.querySelectorAll('input, select, textarea').forEach(input => {
//         input.disabled = true;
//     });
    
//     console.log('📤 Sending API request...');
    
//     // Make API call
//     fetch('/api/clusters', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json',
//             'Accept': 'application/json',
//             'X-Requested-With': 'XMLHttpRequest' // Help identify AJAX requests
//         },
//         body: JSON.stringify(clusterData)
//     })
//     .then(response => {
//         console.log('📡 API response status:', response.status);
        
//         if (!response.ok) {
//             // Try to get error message from response
//             return response.text().then(text => {
//                 try {
//                     const errorData = JSON.parse(text);
//                     throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
//                 } catch (parseError) {
//                     throw new Error(`HTTP ${response.status}: ${response.statusText}`);
//                 }
//             });
//         }
        
//         return response.json();
//     })
//     .then(data => {
//         console.log('✅ API success response:', data);
        
//         // Success notification
//         const clusterId = data.cluster_id || data.id;
//         if (clusterData.auto_analyze) {
//             showNotification(
//                 `🎉 Cluster "${clusterData.cluster_name}" added successfully! Analysis is starting automatically.`, 
//                 'success', 
//                 6000
//             );
//         } else {
//             showNotification(
//                 `✅ Cluster "${clusterData.cluster_name}" added successfully!`, 
//                 'success'
//             );
//         }
        
//         // Close modal
//         const modal = bootstrap.Modal.getInstance(document.getElementById('addClusterModal'));
//         if (modal) {
//             modal.hide();
//         }
        
//         // Reset form
//         form.reset();
        
//         // Redirect or reload after short delay
//         setTimeout(() => {
//             if (clusterId && clusterData.auto_analyze) {
//                 // Go to cluster page if auto-analysis is enabled
//                 window.location.href = `/cluster/${clusterId}`;
//             } else {
//                 // Reload current page to show new cluster
//                 window.location.reload();
//             }
//         }, 2000);
        
//     })
//     .catch(error => {
//         console.error('❌ API error:', error);
//         showNotification(`Failed to add cluster: ${error.message}`, 'error');
//     })
//     .finally(() => {
//         // Always restore button and form state
//         submitBtn.innerHTML = originalHTML;
//         submitBtn.disabled = false;
        
//         // Re-enable form inputs
//         form.querySelectorAll('input, select, textarea').forEach(input => {
//             input.disabled = false;
//         });
//     });
// }

// /**
//  * Enhanced cluster deletion handler
//  */
// function handleClusterDeletion(event) {
//     if (!window.currentlyDeletingCluster) {
//         console.error('❌ No cluster selected for deletion');
//         return;
//     }
    
//     const button = event.target;
//     const originalHTML = button.innerHTML;
    
//     button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Deleting...';
//     button.disabled = true;
    
//     fetch(`/cluster/${window.currentlyDeletingCluster}/remove`, {
//         method: 'DELETE',
//         headers: { 
//             'Content-Type': 'application/json',
//             'Accept': 'application/json' 
//         }
//     })
//     .then(response => response.json())
//     .then(data => {
//         if (data.status === 'success') {
//             showNotification('Cluster deleted successfully!', 'success');
            
//             // Close modal
//             const modal = bootstrap.Modal.getInstance(document.getElementById('deleteClusterModal'));
//             if (modal) modal.hide();
            
//             // Reload page after delay
//             setTimeout(() => {
//                 window.location.reload();
//             }, 1500);
//         } else {
//             throw new Error(data.message || 'Failed to delete cluster');
//         }
//     })
//     .catch(error => {
//         console.error('❌ Delete error:', error);
//         showNotification('Failed to delete cluster: ' + error.message, 'error');
//     })
//     .finally(() => {
//         button.innerHTML = originalHTML;
//         button.disabled = false;
//         window.currentlyDeletingCluster = null;
//     });
// }

// /**
//  * Enhanced modal CSS fixes
//  */
// function injectModalFixCSS() {
//     if (document.getElementById('modal-fix-css')) return;
    
//     const style = document.createElement('style');
//     style.id = 'modal-fix-css';
//     style.textContent = `
//         /* FIXED: Ensure modal z-index hierarchy */
//         .modal-backdrop {
//             z-index: 1040 !important;
//         }
        
//         .modal {
//             z-index: 1050 !important;
//         }
        
//         /* FIXED: Ensure form inputs are always accessible */
//         .modal .form-control,
//         .modal .form-select,
//         .modal .form-check-input,
//         .modal textarea {
//             position: relative !important;
//             z-index: 1055 !important;
//             background: white !important;
//             border: 1px solid #ced4da !important;
//             pointer-events: auto !important;
//         }
        
//         .modal .form-control:focus,
//         .modal .form-select:focus {
//             border-color: #007bff !important;
//             box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
//             outline: none !important;
//         }
        
//         /* FIXED: Ensure buttons work properly */
//         .modal .btn {
//             position: relative !important;
//             z-index: 1055 !important;
//             pointer-events: auto !important;
//         }
        
//         .modal .btn:disabled {
//             pointer-events: none !important;
//         }
        
//         /* FIXED: Ensure labels are clickable */
//         .modal .form-label {
//             position: relative !important;
//             z-index: 1055 !important;
//             pointer-events: auto !important;
//             cursor: pointer !important;
//         }
        
//         /* FIXED: Loading state for form submission */
//         .modal .btn.loading {
//             pointer-events: none !important;
//         }
        
//         /* FIXED: Form validation styling */
//         .modal .form-control.is-valid {
//             border-color: #28a745 !important;
//             background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3e%3cpath fill='%2328a745' d='m2.3 6.73.9.9 4.8-4.8-.9-.9-3.9 3.9-1.9-1.9-.9.9z'/%3e%3c/svg%3e") !important;
//             background-repeat: no-repeat !important;
//             background-position: right calc(0.375em + 0.1875rem) center !important;
//             background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem) !important;
//         }
        
//         .modal .form-control.is-invalid {
//             border-color: #dc3545 !important;
//             background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12' width='12' height='12' fill='none' stroke='%23dc3545'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath d='m5.8 4.6 1.4 1.4M5.8 7.4l1.4-1.4'/%3e%3c/svg%3e") !important;
//             background-repeat: no-repeat !important;
//             background-position: right calc(0.375em + 0.1875rem) center !important;
//             background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem) !important;
//         }
        
//         /* Dark theme modal fixes */
//         [data-theme="dark"] .modal .form-control,
//         [data-theme="dark"] .modal .form-select {
//             background: #2d3748 !important;
//             border-color: #4a5568 !important;
//             color: #f7fafc !important;
//         }
        
//         [data-theme="dark"] .modal .form-control:focus,
//         [data-theme="dark"] .modal .form-select:focus {
//             background: #2d3748 !important;
//             border-color: #4299e1 !important;
//             color: #f7fafc !important;
//         }
//     `;
//     document.head.appendChild(style);
// }

// // Initialize enhanced modal handlers when DOM is ready
// document.addEventListener('DOMContentLoaded', function() {
//     setupEnhancedModalHandlers();
//     injectModalFixCSS();
//     console.log('✅ Enhanced modal system initialized');
// });

// // Make functions globally available
// window.setupEnhancedModalHandlers = setupEnhancedModalHandlers;
// window.handleEnhancedClusterFormSubmission = handleEnhancedClusterFormSubmission;

////////// new fixes ////////////

/**
 * ============================================================================
 * COMPLETE DASHBOARD FIX - ALL ISSUES RESOLVED
 * ============================================================================
 * Fixes all 6 identified issues while preserving existing functionality
 * ============================================================================
 */

// ============================================================================
// 1. FIX ANALYSIS BACKEND EXECUTION
// ============================================================================

/**
 * Enhanced analysis completion handler that properly updates UI
 */
function handleAnalysisCompletion() {
    console.log('🎉 Analysis completed - updating all UI components');
    
    // Force load charts and update metrics
    setTimeout(() => {
        if (typeof initializeCharts === 'function') {
            initializeCharts();
        }
        
        // Clear all loading states
        clearAllLoadingStates();
        
        // Update data source indicator
        updateDataSourceIndicator({
            is_real_data: true,
            data_source: 'azure_api',
            cluster_name: getClusterNameFromContext()
        });
        
    }, 1000);
}

/**
 * Fixed analysis form submission that properly handles completion
 */
function handleAnalysisSubmitFixed(event) {
    event.preventDefault();
    
    if (!validateAnalysisForm()) return;
    
    console.log('📊 Starting enhanced analysis with proper completion handling');
    
    const btn = document.getElementById('analyzeBtn');
    const progress = document.getElementById('analysisProgress');
    
    // Show loading state
    if (btn) {
        btn.classList.add('loading');
        btn.disabled = true;
    }
    
    if (progress) progress.classList.add('visible');
    
    // Start progress animation
    startEnhancedProgressAnimation();
    
    // Submit analysis with proper completion handling
    fetch('/analyze', {
        method: 'POST',
        body: new FormData(event.target)
    })
    .then(response => {
        if (!response.ok) throw new Error(response.statusText);
        return response.text();
    })
    .then(() => {
        console.log('✅ Analysis completed successfully - triggering UI updates');
        
        // Complete progress with success state
        completeProgressWithSuccess();
        
        // Show success notification
        showNotification('🎉 Analysis completed! Loading optimized dashboard...', 'success');
        
        // Switch to dashboard and handle completion
        setTimeout(() => {
            switchToTab('#dashboard');
            resetAnalysisForm();
            
            // CRITICAL FIX: Properly handle analysis completion
            handleAnalysisCompletion();
        }, 2000);
    })
    .catch(error => {
        console.error('❌ Analysis failed:', error);
        showNotification(`Analysis failed: ${error.message}`, 'error');
        resetAnalysisForm();
    });
}

// ============================================================================
// 2. FIX DATA SOURCE INDICATOR POSITIONING
// ============================================================================

/**
 * Fixed data source indicator with proper positioning
 */
function updateDataSourceIndicatorFixed(metadata = {}) {
    console.log('🏷️ Updating data source indicator with fixed positioning:', metadata);
    
    const isRealData = metadata.is_real_data === true || 
                      metadata.data_source === 'azure_api' ||
                      !metadata.is_sample_data;
    
    let indicator = document.querySelector('#data-source-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'data-source-indicator';
        indicator.className = 'data-source-indicator-fixed';
        document.body.appendChild(indicator);
    }
    
    // FIXED: Proper positioning that doesn't overlap
    indicator.style.cssText = `
        position: fixed !important;
        top: 90px !important;
        right: 20px !important;
        z-index: 1100 !important;
        max-width: 200px !important;
        pointer-events: none !important;
    `;
    
    const badgeClass = isRealData ? 'real-data' : 'sample-data';
    const icon = isRealData ? 'cloud' : 'flask';
    const status = isRealData ? 'Live Azure Data' : 'Demo Mode';
    
    let sourceText = '';
    if (metadata.cluster_name) {
        sourceText = metadata.cluster_name;
    } else if (metadata.data_source && metadata.data_source !== 'global_variable') {
        sourceText = metadata.data_source.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    } else {
        sourceText = isRealData ? 'Azure API' : 'Sample Data';
    }
    
    indicator.innerHTML = `
        <div class="data-source-badge-fixed ${badgeClass}">
            <i class="fas fa-${icon}"></i>
            <span>${status}</span>
            <small>${sourceText}</small>
        </div>
    `;
    
    console.log(`✅ Data source indicator fixed: ${status} (${sourceText})`);
}

// ============================================================================
// 3. FIX METRICS CARD UPDATES
// ============================================================================

/**
 * Fixed metrics update that properly replaces loading states
 */
function updateDashboardMetricsFixed(metrics) {
    console.log('📊 Updating metrics with fixed loading state replacement:', metrics);
    
    if (!metrics || typeof metrics !== 'object') {
        console.error('❌ Invalid metrics object:', metrics);
        return;
    }
    
    // Calculate missing metrics
    const optimizationScore = metrics.optimization_score || calculateOptimizationScore(metrics);
    const hpaEfficiency = metrics.hpa_efficiency || metrics.hpa_reduction || 0;
    
    // FIXED: Define comprehensive metric updates
    const metricUpdates = [
        {
            selectors: ['#current-cost'],
            value: metrics.total_cost || 0,
            format: 'currency',
            label: 'Current Monthly Cost'
        },
        {
            selectors: ['#potential-savings', '#monthly-savings'],
            value: metrics.total_savings || 0,
            format: 'currency',
            label: 'Potential Monthly Savings'
        },
        {
            selectors: ['#hpa-efficiency'],
            value: hpaEfficiency,
            format: 'percentage',
            label: 'Memory-based optimization',
            replaceText: 'Run analysis to view'
        },
        {
            selectors: ['#optimization-score'],
            value: optimizationScore,
            format: 'number',
            label: 'Overall efficiency rating',
            replaceText: 'Run analysis to view'
        }
    ];
    
    // FIXED: Update each metric with proper text replacement
    metricUpdates.forEach((metric, index) => {
        setTimeout(() => {
            animateMetricUpdateFixed(metric);
        }, index * 150);
    });
    
    // Update other specific elements
    updateSpecificSavingsElements(metrics);
    updateSavingsBreakdownMini(metrics);
    updateCostTrend(metrics);
}

/**
 * Fixed metric animation that properly replaces loading text
 */
function animateMetricUpdateFixed(metric) {
    let element = null;
    let parentCard = null;
    
    // Find the element and its parent card
    for (const selector of metric.selectors) {
        element = document.querySelector(selector);
        if (element) {
            parentCard = element.closest('.metric-card') || element.closest('.card');
            break;
        }
    }
    
    if (!element) return;

    // FIXED: Replace loading text in parent card
    if (parentCard && metric.replaceText) {
        const textElements = parentCard.querySelectorAll('.text-muted, small');
        textElements.forEach(textEl => {
            if (textEl.textContent.includes(metric.replaceText)) {
                textEl.innerHTML = `<i class="fas fa-info-circle me-1"></i>${metric.label}`;
            }
        });
    }

    // Animate the value update
    element.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
    element.style.transform = 'scale(0.9)';
    element.style.opacity = '0.5';
    
    setTimeout(() => {
        const formattedValue = formatValue(metric.value, metric.format);
        element.textContent = formattedValue;
        
        element.style.transform = 'scale(1)';
        element.style.opacity = '1';
        
        // Add success indicator
        element.classList.add('metric-updated');
        setTimeout(() => {
            element.classList.remove('metric-updated');
        }, 2000);
        
        console.log(`✅ Fixed update ${metric.selectors[0]}: ${formattedValue}`);
    }, 200);
}


// ============================================================================
// 6. ENHANCED PROGRESS ANIMATION
// ============================================================================

/**
 * Enhanced progress animation with proper completion
 */
function startEnhancedProgressAnimation() {
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');
    
    if (!fill || !text) return;
    
    const steps = [
        { percentage: 15, text: '🔌 Connecting to Azure...', delay: 500, color: '#007bff' },
        { percentage: 35, text: '💰 Fetching cost data...', delay: 1200, color: '#17a2b8' },
        { percentage: 55, text: '📊 Analyzing metrics...', delay: 1800, color: '#6f42c1' },
        { percentage: 75, text: '🎯 Calculating optimizations...', delay: 2400, color: '#fd7e14' },
        { percentage: 90, text: '💡 Generating insights...', delay: 3000, color: '#28a745' }
    ];
    
    steps.forEach(step => {
        setTimeout(() => {
            fill.style.width = step.percentage + '%';
            fill.style.background = `linear-gradient(90deg, ${step.color}, ${step.color}dd)`;
            fill.style.boxShadow = `0 0 20px ${step.color}44`;
            text.textContent = step.text;
        }, step.delay);
    });
}

/**
 * Complete progress with success state
 */
function completeProgressWithSuccess() {
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');
    
    if (fill && text) {
        fill.style.width = '100%';
        fill.style.background = 'linear-gradient(90deg, #28a745, #32CD32)';
        fill.style.boxShadow = '0 0 30px #28a74544';
        text.textContent = '🎉 Analysis completed successfully!';
    }
}

// ============================================================================
// 7. HELPER FUNCTIONS
// ============================================================================

/**
 * Get cluster name from current context
 */
function getClusterNameFromContext() {
    // Try to get from URL
    const urlPath = window.location.pathname;
    const clusterMatch = urlPath.match(/\/cluster\/([^\/]+)/);
    if (clusterMatch) {
        return clusterMatch[1];
    }
    
    // Try to get from page title or heading
    const heading = document.querySelector('h2, h4');
    if (heading && heading.textContent.includes('Analysis')) {
        const parts = heading.textContent.split(' ');
        return parts[0] || 'cluster';
    }
    
    return 'current-cluster';
}



// ============================================================================
// 8. INITIALIZATION
// ============================================================================

/**
 * Initialize all fixes
 */
function initializeAllFixes() {
    console.log('🚀 Initializing comprehensive dashboard fixes...');
    
    // Override existing functions with fixed versions
    window.updateDataSourceIndicator = updateDataSourceIndicatorFixed;
    window.updateDashboardMetrics = updateDashboardMetricsFixed;
    window.clearAllLoadingStates = clearAllLoadingStatesFixed;
    window.showNotification = showNotificationFixed;
    
    // Initialize modal fixes
    initializeModalFixed();
    
    // Add CSS for fixed data source indicator
    addFixedDataSourceCSS();
    
    // Override analysis form handler
    const analysisForm = document.getElementById('analysisForm');
    if (analysisForm) {
        // Remove existing listeners and add fixed one
        const newForm = analysisForm.cloneNode(true);
        analysisForm.parentNode.replaceChild(newForm, analysisForm);
        newForm.addEventListener('submit', handleAnalysisSubmitFixed);
        console.log('✅ Analysis form handler fixed');
    }
    
    console.log('✅ All dashboard fixes initialized successfully');
}

/**
 * Add CSS for fixed data source indicator
 */
function addFixedDataSourceCSS() {
    if (document.getElementById('fixed-data-source-css')) return;
    
    const style = document.createElement('style');
    style.id = 'fixed-data-source-css';
    style.textContent = `
        .data-source-indicator-fixed {
            position: fixed !important;
            top: 90px !important;
            right: 20px !important;
            z-index: 1100 !important;
            max-width: 200px !important;
            pointer-events: none !important;
        }
        
        .data-source-badge-fixed {
            background: rgba(255,255,255,0.95) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 20px !important;
            padding: 8px 16px !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important;
            font-size: 0.875rem !important;
            border: 1px solid rgba(0,0,0,0.1) !important;
        }
        
        .data-source-badge-fixed.real-data {
            border-color: #28a745 !important;
            color: #28a745 !important;
        }
        
        .data-source-badge-fixed.sample-data {
            border-color: #ffc107 !important;
            color: #856404 !important;
            background: rgba(255,193,7,0.1) !important;
        }
        
        .data-source-badge-fixed small {
            display: block;
            font-size: 0.75rem;
            opacity: 0.8;
            margin-top: 2px;
        }
        
        /* Modal input fixes */
        .modal .form-control,
        .modal .form-select {
            position: relative !important;
            z-index: 1060 !important;
            background: white !important;
            border: 1px solid #ced4da !important;
        }
        
        .modal .form-control:focus,
        .modal .form-select:focus {
            border-color: #007bff !important;
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
            z-index: 1061 !important;
        }
        
        /* Metric update animation */
        .metric-updated {
            position: relative;
        }
        
        .metric-updated::after {
            content: '✓';
            position: absolute;
            top: -5px;
            right: -5px;
            background: #28a745;
            color: white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            animation: checkmark-appear 0.5s ease-out;
        }
        
        @keyframes checkmark-appear {
            0% { opacity: 0; transform: scale(0); }
            50% { opacity: 1; transform: scale(1.2); }
            100% { opacity: 1; transform: scale(1); }
        }
    `;
    document.head.appendChild(style);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAllFixes);
} else {
    initializeAllFixes();
}

console.log('✅ Complete dashboard fix script loaded - all issues addressed');

/**
 * ============================================================================
 * COMPREHENSIVE FIX - Dynamic Insights & Real Data Binding
 * ============================================================================
 * Fixes all remaining issues with dynamic content and proper data binding
 * ============================================================================
 */

/**
 * ============================================================================
 * DYNAMIC INSIGHTS GENERATOR - REAL DATA BASED
 * ============================================================================
 * Generates insights dynamically from actual analysis data
 * ============================================================================
 */

/**
 * Enhanced dynamic insights generator using REAL analysis data
 */
function generateRealDynamicInsights(data) {
    console.log('🧠 Generating REAL dynamic insights from analysis data:', data);
    
    const metrics = data.metrics || {};
    const costBreakdown = data.costBreakdown || {};
    const insights = {};
    
    // ============================================================================
    // COST INSIGHT - DYNAMIC FROM REAL DATA
    // ============================================================================
    
    if (costBreakdown.labels && costBreakdown.values && costBreakdown.values.length > 0) {
        // Find the highest cost component
        const maxIndex = costBreakdown.values.indexOf(Math.max(...costBreakdown.values));
        const topCostCategory = costBreakdown.labels[maxIndex];
        const topCostValue = costBreakdown.values[maxIndex];
        const totalCost = costBreakdown.values.reduce((a, b) => a + b, 0);
        const percentage = totalCost > 0 ? Math.round((topCostValue / totalCost) * 100) : 0;
        
        // Generate personalized insight based on the category
        let categoryAdvice = '';
        const categoryLower = topCostCategory.toLowerCase();
        
        if (categoryLower.includes('vm') || categoryLower.includes('scale')) {
            categoryAdvice = 'Consider implementing right-sizing recommendations and scheduled scaling';
        } else if (categoryLower.includes('storage') || categoryLower.includes('disk')) {
            categoryAdvice = 'Optimize storage tiers and implement automated cleanup policies';
        } else if (categoryLower.includes('network')) {
            categoryAdvice = 'Review network architecture and implement traffic optimization';
        } else if (categoryLower.includes('control') || categoryLower.includes('plane')) {
            categoryAdvice = 'Control plane costs are fixed, focus on optimizing workload resources';
        } else {
            categoryAdvice = 'Analyze usage patterns and implement cost optimization strategies';
        }
        
        insights.cost = `${topCostCategory} accounts for ${percentage}% of your monthly budget ($${topCostValue.toLocaleString()}). ${categoryAdvice}.`;
        
    } else if (metrics.total_cost && metrics.total_cost > 0) {
        // Fallback with total cost data
        const monthlyCost = Math.round(metrics.total_cost);
        insights.cost = `Current monthly spend is $${monthlyCost.toLocaleString()}. Primary optimization opportunities identified in compute resources.`;
        
    } else {
        insights.cost = `Cost analysis completed. Review the breakdown above to identify your highest spending categories.`;
    }
    
    // ============================================================================
    // HPA INSIGHT - DYNAMIC FROM REAL DATA
    // ============================================================================
    
    const hpaReduction = metrics.hpa_reduction || metrics.hpa_efficiency || 0;
    const hpaSavings = metrics.hpa_savings || 0;
    const totalSavings = metrics.total_savings || 0;
    
    if (hpaReduction > 0 && hpaSavings > 0) {
        // Real HPA data available
        const reductionPct = Math.round(hpaReduction);
        const monthlySavings = Math.round(hpaSavings);
        const annualSavings = Math.round(monthlySavings * 12);
        
        insights.hpa = `Memory-based HPA optimization could reduce replica count by ${reductionPct}%, saving $${monthlySavings.toLocaleString()}/month ($${annualSavings.toLocaleString()}/year) through intelligent auto-scaling.`;
        
    } else if (totalSavings > 0) {
        // Estimate HPA portion from total savings
        const estimatedHpaSavings = Math.round(totalSavings * 0.3); // Assume 30% from HPA
        insights.hpa = `HPA optimization represents significant opportunity. Estimated potential savings of $${estimatedHpaSavings.toLocaleString()}/month through improved auto-scaling efficiency.`;
        
    } else if (metrics.cpu_gap || metrics.memory_gap) {
        // Use resource gap data
        const cpuGap = metrics.cpu_gap || 0;
        const memoryGap = metrics.memory_gap || 0;
        const avgGap = Math.round((cpuGap + memoryGap) / 2);
        
        if (avgGap > 20) {
            insights.hpa = `Resource utilization shows ${avgGap}% efficiency gap. Memory-based HPA could significantly optimize replica scaling.`;
        } else {
            insights.hpa = `Resource utilization is well-optimized. Monitor scaling patterns to maintain efficiency as workload demands change.`;
        }
        
    } else {
        insights.hpa = `HPA analysis in progress. Memory-based scaling optimization opportunities will be identified.`;
    }
    
    // ============================================================================
    // ADDITIONAL DYNAMIC INSIGHTS
    // ============================================================================
    
    // Right-sizing insight
    if (metrics.right_sizing_savings > 0) {
        const rightSizingSavings = Math.round(metrics.right_sizing_savings);
        insights.rightsizing = `Right-sizing recommendations could save $${rightSizingSavings.toLocaleString()}/month by matching resource allocation to actual usage patterns.`;
    }
    
    // Storage insight
    if (metrics.storage_savings > 0) {
        const storageSavings = Math.round(metrics.storage_savings);
        insights.storage = `Storage optimization could save $${storageSavings.toLocaleString()}/month through tier optimization and cleanup automation.`;
    }
    
    // Overall optimization insight
    if (totalSavings > 0) {
        const savingsPct = metrics.savings_percentage || 0;
        const monthlySavings = Math.round(totalSavings);
        const annualSavings = Math.round(totalSavings * 12);
        
        insights.overall = `Total optimization potential: ${Math.round(savingsPct)}% reduction ($${monthlySavings.toLocaleString()}/month, $${annualSavings.toLocaleString()}/year) through comprehensive resource optimization.`;
    }
    
    console.log('✅ Generated REAL dynamic insights:', insights);
    return insights;
}

/**
 * Enhanced function to update insights with REAL dynamic content
 */
function updateRealDynamicInsights(data) {
    console.log('📊 Updating insights with REAL dynamic content from:', data);
    
    const insights = generateRealDynamicInsights(data);
    
    // Update cost insight with animation
    const costInsightElement = document.querySelector('#cost-insight');
    if (costInsightElement) {
        animateInsightUpdate(costInsightElement, insights.cost);
        console.log('✅ Updated cost insight with real data');
    }
    
    // Update HPA insight with animation
    const hpaInsightElement = document.querySelector('#hpa-insight');
    if (hpaInsightElement) {
        animateInsightUpdate(hpaInsightElement, insights.hpa);
        console.log('✅ Updated HPA insight with real data');
    }
    
    // Update additional insights if container exists
    const insightsContainer = document.querySelector('#insights-container');
    if (insightsContainer) {
        updateAdditionalInsights(insightsContainer, insights);
    }
}

/**
 * Animate insight update with smooth transition
 */
function animateInsightUpdate(element, newContent) {
    if (!element || !newContent) return;
    
    // Add loading complete class
    element.closest('.insight-box, .saving-box')?.classList.add('loaded');
    
    // Smooth transition
    element.style.transition = 'all 0.4s ease';
    element.style.opacity = '0.3';
    element.style.transform = 'translateY(10px)';
    
    setTimeout(() => {
        element.innerHTML = newContent;
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
        
        // Add success indicator
        element.classList.add('insight-updated');
        setTimeout(() => {
            element.classList.remove('insight-updated');
        }, 2000);
    }, 200);
}

/**
 * Update additional insights container
 */
function updateAdditionalInsights(container, insights) {
    const additionalInsights = ['rightsizing', 'storage', 'overall'];
    let hasAdditional = false;
    
    let additionalHTML = '';
    
    additionalInsights.forEach(key => {
        if (insights[key]) {
            hasAdditional = true;
            const title = key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
            const icon = getInsightIcon(key);
            
            additionalHTML += `
                <div class="insight-item mb-3 p-3 border rounded bg-light insight-fade-in">
                    <h6 class="text-primary">
                        <i class="fas fa-${icon} me-2"></i>${title}
                    </h6>
                    <p class="mb-0">${insights[key]}</p>
                </div>
            `;
        }
    });
    
    if (hasAdditional) {
        container.innerHTML = additionalHTML;
        
        // Animate in the new insights
        setTimeout(() => {
            container.querySelectorAll('.insight-fade-in').forEach((insight, index) => {
                setTimeout(() => {
                    insight.style.opacity = '1';
                    insight.style.transform = 'translateY(0)';
                }, index * 150);
            });
        }, 100);
    } else {
        container.innerHTML = '<p class="text-muted">Additional insights will appear as more optimization opportunities are identified.</p>';
    }
}

/**
 * Get appropriate icon for insight type
 */
function getInsightIcon(type) {
    const icons = {
        'rightsizing': 'expand-arrows-alt',
        'storage': 'hdd',
        'overall': 'chart-line',
        'cost': 'dollar-sign',
        'hpa': 'rocket'
    };
    return icons[type] || 'lightbulb';
}

/**
 * Enhanced chart initialization that includes real insights
 */
function initializeChartsWithRealInsights() {
    console.log('📊 Initializing charts with REAL dynamic insights...');
    
    fetch('/api/chart-data')
        .then(response => {
            console.log('📡 Chart data response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📈 Chart data received for dynamic insights:', data);
            
            if (data.status !== 'success') {
                throw new Error(data.message || 'Invalid API response');
            }
            
            if (!data.metrics) {
                throw new Error('No metrics data in response');
            }
            
            // Update all metrics
            if (typeof updateDashboardMetrics === 'function') {
                updateDashboardMetrics(data.metrics);
            }
            
            // Create charts
            if (typeof createAllCharts === 'function') {
                createAllCharts(data);
            }
            
            // REAL DYNAMIC INSIGHTS UPDATE
            updateRealDynamicInsights(data);
            
            // Update data source indicator
            if (typeof updateDataSourceIndicator === 'function') {
                updateDataSourceIndicator(data.metadata || {});
            }
            
            console.log('✅ Charts and REAL dynamic insights initialized successfully');
            
        })
        .catch(error => {
            console.error('❌ Chart/insights initialization failed:', error);
            
            // Show error in insights
            const costInsight = document.querySelector('#cost-insight');
            const hpaInsight = document.querySelector('#hpa-insight');
            
            if (costInsight) {
                costInsight.innerHTML = `Unable to load cost insights: ${error.message}. Please try running the analysis again.`;
            }
            
            if (hpaInsight) {
                hpaInsight.innerHTML = `Unable to load HPA insights: ${error.message}. Please try running the analysis again.`;
            }
            
            if (typeof showNotification === 'function') {
                showNotification(`Failed to load insights: ${error.message}`, 'error');
            }
        });
}

/**
 * Enhanced analysis completion handler with real insights
 */
function handleAnalysisCompletionWithRealInsights() {
    console.log('🎉 Analysis completed - updating with REAL dynamic insights');
    
    // Load charts and insights with real data
    setTimeout(() => {
        initializeChartsWithRealInsights();
    }, 1000);
}

/**
 * Override the existing functions
 */
function initializeRealInsights() {
    console.log('🚀 Initializing REAL dynamic insights system...');
    
    // Override existing functions
    if (typeof window.initializeCharts !== 'undefined') {
        window.originalInitializeCharts = window.initializeCharts;
    }
    window.initializeCharts = initializeChartsWithRealInsights;
    
    if (typeof window.updateDynamicInsights !== 'undefined') {
        window.originalUpdateDynamicInsights = window.updateDynamicInsights;
    }
    window.updateDynamicInsights = updateRealDynamicInsights;
    
    // Also override the completion handler if it exists
    if (typeof window.handleAnalysisCompletion !== 'undefined') {
        window.originalHandleAnalysisCompletion = window.handleAnalysisCompletion;
    }
    window.handleAnalysisCompletion = handleAnalysisCompletionWithRealInsights;
    
    console.log('✅ REAL dynamic insights system initialized');
}

// CSS for insight animations
function addInsightAnimationCSS() {
    if (document.getElementById('insight-animation-css')) return;
    
    const style = document.createElement('style');
    style.id = 'insight-animation-css';
    style.textContent = `
        .insight-updated {
            position: relative;
        }
        
        .insight-updated::before {
            content: '✨';
            position: absolute;
            top: -10px;
            right: -10px;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            border-radius: 50%;
            width: 25px;
            height: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            animation: sparkle 1s ease-out;
            box-shadow: 0 2px 10px rgba(40, 167, 69, 0.3);
        }
        
        .insight-fade-in {
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.5s ease;
        }
        
        .insight-box.loaded,
        .saving-box.loaded {
            border-left-color: #28a745 !important;
            background: linear-gradient(135deg, rgba(40, 167, 69, 0.05), rgba(40, 167, 69, 0.02)) !important;
        }
        
        @keyframes sparkle {
            0% { opacity: 0; transform: scale(0) rotate(0deg); }
            50% { opacity: 1; transform: scale(1.2) rotate(180deg); }
            100% { opacity: 1; transform: scale(1) rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initializeRealInsights();
        addInsightAnimationCSS();
    });
} else {
    initializeRealInsights();
    addInsightAnimationCSS();
}

console.log('✅ REAL Dynamic Insights Generator loaded successfully');