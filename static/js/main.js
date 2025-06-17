/**
 * ============================================================================
 * AKS COST INTELLIGENCE - MAIN DASHBOARD JAVASCRIPT
 * ============================================================================
 * Comprehensive cost optimization dashboard for Azure Kubernetes Service
 * Author: AKS Cost Intelligence Team
 * Version: 2.0.0
 * ============================================================================
 */

// ============================================================================
// GLOBAL CONFIGURATION & STATE
// ============================================================================

const AppConfig = {
    API_BASE_URL: '/api',
    CHART_REFRESH_INTERVAL: 30000, // 30 seconds
    NOTIFICATION_DURATION: 5000,   // 5 seconds
    MIN_VALIDATION_LENGTH: 3
};

const AppState = {
    chartInstances: {},
    analysisCompleted: false,
    currentAnalysis: null,
    alerts: [],
    deployments: [],
    notifications: [],
    autoAnalysis: {
        active: {},  // Track active analyses
        pollingIntervals: {},  // Store polling intervals
        statusCache: {}  // Cache status updates
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
 * Copy text to clipboard with fallback support
 */
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Failed to copy:', err);
            showNotification('Failed to copy to clipboard', 'error');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showNotification('Copied to clipboard!', 'success');
        } catch (err) {
            console.error('Failed to copy:', err);
            showNotification('Failed to copy to clipboard', 'error');
        }
        document.body.removeChild(textArea);
    }
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
// NOTIFICATION SYSTEM
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
// FORM VALIDATION & HANDLERS
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
    // Add cluster form handler
    const possibleFormIds = ['addClusterForm', 'add-cluster-form', 'clusterForm'];
    let formFound = false;
    
    for (const formId of possibleFormIds) {
        const form = document.getElementById(formId);
        if (form) {
            console.log(`✅ Found form: ${formId}`);
            form.addEventListener('submit', handleAddClusterSubmission);
            formFound = true;
            break;
        }
    }
    
    if (!formFound) {
        console.warn('⚠️ No add cluster form found');
    }
    
    // Analysis form handler
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
            startAnalysisTracking(clusterId, clusterData.cluster_name);
            
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
            if (autoAnalysisStarted) {
                // Keep modal area updated but don't reload immediately
                showAnalysisProgressModal(clusterId, clusterData.cluster_name);
            }
            refreshClusterList();
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
    window.location.href = `/cluster/${clusterId}`;
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

/**
 * Enhanced cluster list refresh with status preservation
 */
function refreshClusterList() {
    console.log('🔄 Enhanced cluster list refresh...');
    
    fetch(`${AppConfig.API_BASE_URL}/clusters`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.clusters) {
                // Update cluster list while preserving real-time status
                updateClusterListUI(data.clusters);
                
                // Re-apply any active analysis tracking
                Object.keys(AppState.autoAnalysis.active).forEach(clusterId => {
                    updateAnalysisStatus(clusterId);
                });
            }
        })
        .catch(error => {
            console.error('❌ Error refreshing cluster list:', error);
        });
}

// ============================================================================
// ANALYSIS MANAGEMENT
// ============================================================================

/**
 * Handles analysis form submission with progress tracking
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

    // Submit analysis with enhanced completion handling
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
                initializeCharts();
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
// AUTO-ANALYSIS SYSTEM
// ============================================================================


/**
 * Updates cluster list UI with new data
 */
function updateClusterListUI(clusters) {
    // This function should update the DOM with cluster data
    // Implementation depends on your HTML structure
    console.log('🔄 Updating cluster list UI with', clusters.length, 'clusters');
    
    // Example implementation - adjust based on your HTML structure
    const clusterContainer = document.getElementById('cluster-list') || document.querySelector('.cluster-grid');
    if (!clusterContainer) {
        console.warn('⚠️ Cluster container not found');
        return;
    }
    
    // Refresh the page or update specific cluster cards
    // You may want to implement specific cluster card updates here
}

/**
 * Updates progress bar in cluster status
 */
function updateProgressBar(progressBar, progress, status) {
    if (!progressBar) return;
    
    const progressFill = progressBar.querySelector('.progress-bar') || progressBar;
    if (progressFill) {
        progressFill.style.width = `${progress}%`;
        progressFill.setAttribute('aria-valuenow', progress);
        
        // Update color based on status
        progressFill.className = progressFill.className.replace(/bg-\w+/g, '');
        switch (status) {
            case 'analyzing':
                progressFill.classList.add('bg-primary');
                break;
            case 'completed':
                progressFill.classList.add('bg-success');
                break;
            case 'failed':
                progressFill.classList.add('bg-danger');
                break;
            default:
                progressFill.classList.add('bg-secondary');
        }
    }
}

/**
 * Creates analysis progress modal
 */
function createAnalysisProgressModal() {
    // Check if modal already exists
    let modal = document.getElementById('analysisProgressModal');
    if (modal) return modal;
    
    // Create modal HTML
    const modalHTML = `
        <div class="modal fade" id="analysisProgressModal" tabindex="-1" aria-labelledby="analysisProgressModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="analysisProgressModalLabel">Analysis in Progress</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center mb-4">
                            <div class="progress-circle mx-auto mb-3" style="width: 120px; height: 120px;">
                                <svg viewBox="0 0 36 36" class="circular-chart">
                                    <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#eee" stroke-width="2"/>
                                    <path class="circle" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#007bff" stroke-width="2" stroke-linecap="round" stroke-dasharray="0, 100"/>
                                </svg>
                                <div class="percentage position-absolute top-50 start-50 translate-middle">0%</div>
                            </div>
                            <p class="cluster-name-progress fw-bold">Analyzing cluster...</p>
                            <p class="current-step text-muted">Initializing analysis...</p>
                            <small class="time-remaining text-muted">Estimated time remaining: ~5min</small>
                        </div>
                        
                        <div class="analysis-steps">
                            <div class="step-item d-flex align-items-center mb-2">
                                <div class="step-status me-3"><i class="fas fa-clock text-muted"></i></div>
                                <span>Connecting to Azure</span>
                            </div>
                            <div class="step-item d-flex align-items-center mb-2">
                                <div class="step-status me-3"><i class="fas fa-clock text-muted"></i></div>
                                <span>Fetching cost data</span>
                            </div>
                            <div class="step-item d-flex align-items-center mb-2">
                                <div class="step-status me-3"><i class="fas fa-clock text-muted"></i></div>
                                <span>Analyzing metrics</span>
                            </div>
                            <div class="step-item d-flex align-items-center mb-2">
                                <div class="step-status me-3"><i class="fas fa-clock text-muted"></i></div>
                                <span>Generating recommendations</span>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Run in Background</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add CSS for progress circle
    const style = document.createElement('style');
    style.textContent = `
        .circular-chart { width: 100%; height: 100%; }
        .circle { transition: stroke-dasharray 0.3s ease; }
        .progress-circle { position: relative; }
        .step-item.active .step-status i { color: #007bff !important; }
        .step-item.completed .step-status i { color: #28a745 !important; }
    `;
    document.head.appendChild(style);
    
    return document.getElementById('analysisProgressModal');
}

/**
 * Start real-time analysis tracking for a cluster
 */
function startAnalysisTracking(clusterId, clusterName) {
    console.log(`🔄 Starting analysis tracking for ${clusterId}`);
    
    // Mark as active
    AppState.autoAnalysis.active[clusterId] = {
        clusterId: clusterId,
        clusterName: clusterName,
        startTime: new Date(),
        lastUpdate: new Date()
    };
    
    // Start polling for status updates
    const pollInterval = setInterval(() => {
        updateAnalysisStatus(clusterId);
    }, 3000); // Poll every 3 seconds
    
    AppState.autoAnalysis.pollingIntervals[clusterId] = pollInterval;
    
    // Auto-stop polling after 10 minutes
    setTimeout(() => {
        stopAnalysisTracking(clusterId);
    }, 10 * 60 * 1000);
}

/**
 * Update analysis status for a specific cluster
 */
function updateAnalysisStatus(clusterId) {
    fetch(`${AppConfig.API_BASE_URL}/clusters/${clusterId}/analysis-status`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const status = data.status;
                const progress = data.progress || 0;
                const message = data.message || 'Processing...';
                
                console.log(`📊 Status update for ${clusterId}: ${status} (${progress}%) - ${message}`);
                
                // Update UI elements
                updateClusterStatusInUI(clusterId, status, progress, message);
                
                // Check if completed or failed
                if (status === 'completed') {
                    handleAnalysisComplete(clusterId, data);
                    stopAnalysisTracking(clusterId);
                } else if (status === 'failed') {
                    handleAnalysisFailure(clusterId, message);
                    stopAnalysisTracking(clusterId);
                }
                
                // Cache the status
                AppState.autoAnalysis.statusCache[clusterId] = {
                    status: status,
                    progress: progress,
                    message: message,
                    timestamp: new Date().toISOString()
                };
            }
        })
        .catch(error => {
            console.error(`❌ Error updating status for ${clusterId}:`, error);
        });
}

/**
 * Stop analysis tracking for a cluster
 */
function stopAnalysisTracking(clusterId) {
    console.log(`⏹️ Stopping analysis tracking for ${clusterId}`);
    
    // Clear polling interval
    if (AppState.autoAnalysis.pollingIntervals[clusterId]) {
        clearInterval(AppState.autoAnalysis.pollingIntervals[clusterId]);
        delete AppState.autoAnalysis.pollingIntervals[clusterId];
    }
    
    // Remove from active tracking
    delete AppState.autoAnalysis.active[clusterId];
}

/**
 * Update cluster status in the UI
 */
function updateClusterStatusInUI(clusterId, status, progress, message) {
    // Find cluster cards/elements with this ID
    const clusterElements = document.querySelectorAll(`[data-cluster-id="${clusterId}"]`);
    
    clusterElements.forEach(element => {
        const statusElement = element.querySelector('.cluster-status');
        const actionButton = element.querySelector('.cluster-action-btn');
        const progressBar = element.querySelector('.analysis-progress');
        
        if (statusElement) {
            statusElement.innerHTML = getEnhancedStatusHTML(status, message, progress);
        }
        
        if (actionButton) {
            updateActionButton(actionButton, status, clusterId, progress);
        }
        
        if (progressBar) {
            updateProgressBar(progressBar, progress, status);
        }
    });
    
    // Update any open progress modals
    updateProgressModal(clusterId, status, progress, message);
}

/**
 * Generate enhanced status HTML
 */
function getEnhancedStatusHTML(status, message, progress) {
    switch (status) {
        case 'analyzing':
            return `
                <div class="d-flex align-items-center">
                    <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                        <span class="visually-hidden">Analyzing...</span>
                    </div>
                    <div class="flex-grow-1">
                        <div class="fw-semibold text-primary">Analyzing</div>
                        <small class="text-muted">${message}</small>
                        <div class="progress mt-1" style="height: 4px;">
                            <div class="progress-bar bg-primary" style="width: ${progress}%"></div>
                        </div>
                    </div>
                </div>
            `;
            
        case 'completed':
            return `
                <div class="d-flex align-items-center">
                    <i class="fas fa-check-circle text-success me-2 fa-lg"></i>
                    <div>
                        <div class="fw-semibold text-success">Analysis Complete</div>
                        <small class="text-muted">Results available</small>
                    </div>
                </div>
            `;
            
        case 'failed':
            return `
                <div class="d-flex align-items-center">
                    <i class="fas fa-exclamation-triangle text-warning me-2 fa-lg"></i>
                    <div>
                        <div class="fw-semibold text-warning">Analysis Failed</div>
                        <small class="text-muted">${message}</small>
                    </div>
                </div>
            `;
            
        default:
            return `
                <div class="d-flex align-items-center">
                    <i class="fas fa-clock text-muted me-2"></i>
                    <div>
                        <div class="fw-semibold text-muted">Ready to Analyze</div>
                        <small class="text-muted">Click to start analysis</small>
                    </div>
                </div>
            `;
    }
}

/**
 * Update action button based on analysis status
 */
function updateActionButton(button, status, clusterId, progress = 0) {
    switch (status) {
        case 'analyzing':
            button.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i>Analyzing... ${progress}%`;
            button.disabled = true;
            button.className = 'btn btn-sm btn-outline-primary cluster-action-btn';
            break;
            
        case 'completed':
            button.innerHTML = '<i class="fas fa-eye me-1"></i>View Results';
            button.disabled = false;
            button.className = 'btn btn-sm btn-success cluster-action-btn';
            button.onclick = () => selectCluster(clusterId);
            break;
            
        case 'failed':
            button.innerHTML = '<i class="fas fa-redo me-1"></i>Retry Analysis';
            button.disabled = false;
            button.className = 'btn btn-sm btn-warning cluster-action-btn';
            button.onclick = () => analyzeCluster(clusterId);
            break;
            
        default:
            button.innerHTML = '<i class="fas fa-play me-1"></i>Analyze Now';
            button.disabled = false;
            button.className = 'btn btn-sm btn-primary cluster-action-btn';
            button.onclick = () => analyzeCluster(clusterId);
            break;
    }
}

/**
 * Handle analysis completion
 */
function handleAnalysisComplete(clusterId, statusData) {
    const clusterName = AppState.autoAnalysis.active[clusterId]?.clusterName || 'Cluster';
    
    console.log(`🎉 Analysis completed for ${clusterName}`);
    
    // Show enhanced completion notification
    const results = statusData.results || {};
    const savings = results.total_savings || 0;
    const cost = results.total_cost || 0;
    
    showEnhancedCompletionNotification(clusterName, cost, savings, clusterId);
    
    // Refresh cluster list to show updated data
    setTimeout(() => {
        refreshClusterList();
    }, 2000);
}

/**
 * Handle analysis failure
 */
function handleAnalysisFailure(clusterId, errorMessage) {
    const clusterName = AppState.autoAnalysis.active[clusterId]?.clusterName || 'Cluster';
    
    console.log(`❌ Analysis failed for ${clusterName}: ${errorMessage}`);
    
    showNotification(
        `Analysis failed for "${clusterName}": ${errorMessage}. You can retry the analysis manually.`,
        'warning',
        10000
    );
    
    setTimeout(() => {
        refreshClusterList();
    }, 2000);
}

/**
 * Show enhanced completion notification with results preview
 */
function showEnhancedCompletionNotification(clusterName, cost, savings, clusterId) {
    const savingsPercent = cost > 0 ? ((savings / cost) * 100).toFixed(1) : 0;
    
    // Create enhanced notification
    const notificationHTML = `
        <div class="analysis-complete-notification">
            <div class="d-flex align-items-start">
                <div class="notification-icon me-3">
                    <i class="fas fa-trophy text-warning fa-2x"></i>
                </div>
                <div class="flex-1">
                    <h6 class="mb-1">🎉 Analysis Complete!</h6>
                    <p class="mb-2">Results for <strong>${clusterName}</strong> are ready</p>
                    <div class="quick-stats">
                        <span class="badge bg-success me-2">$${cost.toLocaleString()} monthly cost</span>
                        <span class="badge bg-primary me-2">$${savings.toLocaleString()} savings potential</span>
                        <span class="badge bg-warning">${savingsPercent}% optimization</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Create enhanced toast
    const toastContainer = notificationManager.container;
    const toastElement = document.createElement('div');
    toastElement.className = 'toast align-items-start border-0 shadow-lg';
    toastElement.style.minWidth = '400px';
    
    toastElement.innerHTML = `
        <div class="toast-header bg-success text-white">
            <i class="fas fa-chart-line me-2"></i>
            <strong class="me-auto">Analysis Complete</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${notificationHTML}
            <div class="mt-3">
                <button class="btn btn-primary btn-sm me-2" onclick="selectCluster('${clusterId}')">
                    <i class="fas fa-eye me-1"></i>View Results
                </button>
                <button class="btn btn-outline-secondary btn-sm" data-bs-dismiss="toast">
                    <i class="fas fa-check me-1"></i>Got it
                </button>
            </div>
        </div>
    `;
    
    toastContainer.appendChild(toastElement);
    
    const toast = new bootstrap.Toast(toastElement, {
        autohide: false // Don't auto-hide completion notifications
    });
    toast.show();
    
    // Auto-remove after 30 seconds
    setTimeout(() => {
        if (toastElement.parentNode) {
            toastElement.parentNode.removeChild(toastElement);
        }
    }, 30000);
}

/**
 * Show analysis progress modal for ongoing analysis
 */
function showAnalysisProgressModal(clusterId, clusterName) {
    // Create or update progress modal
    let modal = document.getElementById('analysisProgressModal');
    if (!modal) {
        modal = createAnalysisProgressModal();
    }
    
    // Update modal content
    const modalTitle = modal.querySelector('.modal-title');
    const clusterNameElement = modal.querySelector('.cluster-name-progress');
    
    if (modalTitle) modalTitle.textContent = `Analysis in Progress - ${clusterName}`;
    if (clusterNameElement) clusterNameElement.textContent = `Analyzing ${clusterName}...`;
    
    // Show modal
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    // Store modal reference for updates
    modal.setAttribute('data-cluster-id', clusterId);
}

/**
 * Update progress modal with current status
 */
function updateProgressModal(clusterId, status, progress, message) {
    const modal = document.querySelector(`#analysisProgressModal[data-cluster-id="${clusterId}"]`);
    if (!modal) return;
    
    const progressCircle = modal.querySelector('.progress-circle');
    const currentStepElement = modal.querySelector('.current-step');
    const timeRemainingElement = modal.querySelector('.time-remaining');
    
    if (progressCircle) {
        const circle = progressCircle.querySelector('.circle');
        const percentage = progressCircle.querySelector('.percentage');
        
        if (circle && percentage) {
            circle.style.strokeDasharray = `${progress}, 100`;
            percentage.textContent = `${progress}%`;
        }
    }
    
    if (currentStepElement) {
        currentStepElement.textContent = message;
    }
    
    if (timeRemainingElement) {
        const estimatedTotal = 300; // 5 minutes
        const elapsed = (100 - progress) / 100;
        const remaining = Math.max(30, elapsed * estimatedTotal);
        timeRemainingElement.textContent = `~${Math.round(remaining)}s`;
    }
    
    // Update step indicators
    updateStepIndicators(modal, progress);
    
    // Auto-close modal when complete
    if (status === 'completed' || status === 'failed') {
        setTimeout(() => {
            const bootstrapModal = bootstrap.Modal.getInstance(modal);
            if (bootstrapModal) {
                bootstrapModal.hide();
            }
        }, 3000);
    }
}

/**
 * Update step indicators in progress modal
 */
function updateStepIndicators(modal, progress) {
    const steps = modal.querySelectorAll('.step-item');
    
    steps.forEach((step, index) => {
        const stepProgress = (index + 1) * 25; // 4 steps total
        const stepIcon = step.querySelector('.step-status i');
        
        if (progress >= stepProgress) {
            // Step completed
            if (stepIcon) {
                stepIcon.className = 'fas fa-check text-success';
            }
            step.classList.add('completed');
        } else if (progress >= stepProgress - 25) {
            // Step in progress
            if (stepIcon) {
                stepIcon.className = 'fas fa-spinner fa-spin text-primary';
            }
            step.classList.add('active');
        } else {
            // Step pending
            if (stepIcon) {
                stepIcon.className = 'fas fa-clock text-muted';
            }
            step.classList.remove('active', 'completed');
        }
    });
}

/**
 * Initialize auto-analysis system on page load
 */
function initializeAutoAnalysisSystem() {
    console.log('🚀 Initializing auto-analysis system...');
    
    // Check for any clusters currently being analyzed
    fetch(`${AppConfig.API_BASE_URL}/clusters`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.clusters) {
                data.clusters.forEach(cluster => {
                    if (cluster.analysis_status === 'analyzing') {
                        console.log(`🔄 Resuming tracking for cluster: ${cluster.id}`);
                        startAnalysisTracking(cluster.id, cluster.name);
                    }
                });
            }
        })
        .catch(error => {
            console.error('❌ Error initializing auto-analysis:', error);
        });
}

// ============================================================================
// CHART MANAGEMENT
// ============================================================================

/**
 * Initializes all dashboard charts
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
            
            // Update metrics FIRST
            updateDashboardMetrics(data.metrics);
            
            // Then create charts
            createAllCharts(data);
            
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
 * Updates dashboard metrics with animation
 */
function updateDashboardMetrics(metrics) {
    console.log('📊 Updating metrics with comprehensive element targeting:', metrics);
    
    // Validate metrics object
    if (!metrics || typeof metrics !== 'object') {
        console.error('❌ Invalid metrics object:', metrics);
        return;
    }
    
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
            value: metrics.hpa_reduction, 
            format: 'percentage',
            label: 'HPA Efficiency'
        },
        { 
            selectors: ['#optimization-score'], 
            value: calculateOptimizationScore(metrics), 
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
    
    // Update specific savings elements
    updateSpecificSavingsElements(metrics);
    
    // Update savings breakdown mini elements
    updateSavingsBreakdownMini(metrics);
    
    updateCostTrend(metrics);
    updateDataSourceIndicator(metrics);
}

/**
 * Update specific savings elements
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
 * Animates metric value updates
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
 * Updates cost trend indicator
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
 * Updates data source indicator
 */
function updateDataSourceIndicator(metrics) {
    const isRealData = !metrics.is_sample_data;
    let indicator = document.querySelector('#data-source-indicator');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'data-source-indicator';
        indicator.className = 'data-source-indicator';
        (document.querySelector('#dashboard') || document.body).appendChild(indicator);
    }
    
    indicator.innerHTML = `
        <div class="data-source-badge ${isRealData ? 'real-data' : 'sample-data'}">
            <i class="fas fa-${isRealData ? 'cloud' : 'flask'}"></i>
            <span>${isRealData ? 'Live Azure Data' : 'Demo Mode'}</span>
            <small>${metrics.data_source || ''}</small>
        </div>
    `;
}

/**
 * Creates all charts from provided data
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
 * Creates cost breakdown chart
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
 * Creates main trend chart
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
 * Creates HPA comparison chart
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
 * Creates node utilization chart
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
 * Creates savings breakdown chart
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
 * Creates namespace cost chart
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
 * Creates workload cost chart
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
 * Updates insights section
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
 * Updates pod cost metrics in the dashboard
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
 * Gets accuracy badge class for pod analysis
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
 * Shows chart error message with retry option
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
// IMPLEMENTATION PLAN MANAGEMENT
// ============================================================================

/**
 * Loads and displays implementation plan
 */
function loadImplementationPlan() {
    console.log('📋 Enhanced: Loading implementation plan...');
    
    const container = document.getElementById('implementation-plan-container');
    if (!container) {
        console.error('❌ Implementation plan container not found!');
        
        // Try to find alternative containers
        const alternatives = [
            '#implementation .container',
            '#implementation .container-fluid', 
            '#implementation .tab-pane',
            '#implementation'
        ];
        
        let foundContainer = null;
        for (const selector of alternatives) {
            foundContainer = document.querySelector(selector);
            if (foundContainer) {
                console.log(`✅ Found alternative container: ${selector}`);
                
                // Create the missing container
                if (foundContainer.id !== 'implementation-plan-container') {
                    const newContainer = document.createElement('div');
                    newContainer.id = 'implementation-plan-container';
                    newContainer.className = 'container-fluid p-4';
                    foundContainer.appendChild(newContainer);
                    console.log('✅ Created implementation-plan-container');
                }
                break;
            }
        }
        
        if (!foundContainer) {
            console.error('❌ No suitable container found');
            return;
        }
    }
    
    // Get the actual container (either found or created)
    const actualContainer = document.getElementById('implementation-plan-container');
    
    // Show enhanced loading state
    actualContainer.innerHTML = `
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
                analysisCompleted = true;
                displayImplementationPlan(planData);
                updateQuickStats(planData);
            } else {
                console.warn('⚠️ No implementation phases found in data');
                showNoAnalysisMessage(actualContainer);
            }
        })
        .catch(error => {
            console.error('❌ Implementation plan loading error:', error);
            displayError(error.message);
        });
}

/**
 * Displays implementation plan content
 */
function displayImplementationPlan(planData) {
    console.log('🎨 Displaying comprehensive implementation plan with data:', planData);
    
    const container = document.getElementById('implementation-plan-container');
    
    // Extract all sections
    const phases = planData.implementation_phases || planData.phases || [];
    const summary = planData.executive_summary || planData.summary || {};
    const timeline = planData.timeline_optimization || {};
    const risk = planData.risk_mitigation || {};
    const monitoring = planData.monitoring_strategy || {};
    const governance = planData.governance_framework || {};
    const success = planData.success_criteria || {};
    const contingency = planData.contingency_planning || {};
    
    console.log('📋 Processing all sections:', {
        phases: phases.length,
        hasSummary: !!summary,
        hasTimeline: !!timeline,
        hasRisk: !!risk,
        hasMonitoring: !!monitoring,
        hasGovernance: !!governance,
        hasSuccess: !!success,
        hasContingency: !!contingency
    });
    
    if (!phases || phases.length === 0) {
        container.innerHTML = showNoAnalysisMessage();
        return;
    }

    // Calculate totals for summary
    const totalSavings = phases.reduce((sum, phase) => sum + (phase.projected_savings || phase.savings || 0), 0);
    const totalWeeks = Math.max(...phases.map(phase => phase.end_week || phase.duration_weeks || 0));

    let html = `
        <!-- Executive Summary Header -->
        <div class="card border-0 shadow-lg mb-4" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div class="card-body text-white">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h3 class="card-title mb-3">
                            <i class="fas fa-rocket me-2"></i>Implementation Plan Ready
                        </h3>
                        <div class="mb-3">
                            <strong>Cluster:</strong> ${summary.cluster_name || planData.metadata?.cluster_name || 'N/A'} 
                            <span class="mx-2">•</span>
                            <strong>Resource Group:</strong> ${summary.resource_group || planData.metadata?.resource_group || 'N/A'}
                        </div>
                        <p class="mb-0 opacity-90">
                            This ${totalWeeks || timeline.total_weeks || 0}-week implementation plan will optimize your AKS cluster 
                            through ${phases.length} carefully planned phases.
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
                            <div class="h4 mb-1 text-white">${totalWeeks || timeline.total_weeks || 'TBD'}</div>
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
                            <div class="h4 mb-1 text-white">${((timeline.timeline_confidence || 0.8) * 100).toFixed(0)}%</div>
                            <small class="opacity-90">Confidence</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Render Implementation Phases
    phases.forEach((phase, idx) => {
        html += renderEnhancedPhaseCard(phase, idx + 1);
    });

    // Add Governance & Management Section
    html += renderGovernanceSection(governance, monitoring);
    
    // Add Success Criteria & Monitoring Section  
    html += renderSuccessAndMonitoringSection(success, monitoring);
    
    // Add Risk Management & Contingency Section
    html += renderRiskManagementSection(risk, contingency);
    
    // Add Timeline & Resource Management Section
    html += renderTimelineResourceSection(timeline);

    // Add action buttons
    html += `
        <div class="card border-0 bg-light mt-4">
            <div class="card-body text-center">
                <h5 class="mb-3">🚀 Ready to Start Implementation?</h5>
                <div class="d-flex gap-2 justify-content-center flex-wrap">
                    <button class="btn btn-success btn-lg" onclick="deployOptimizations()">
                        <i class="fas fa-rocket me-2"></i>Deploy Phase 1
                    </button>
                    <button class="btn btn-outline-primary btn-lg" onclick="exportReport()">
                        <i class="fas fa-download me-2"></i>Export Plan
                    </button>
                    <button class="btn btn-outline-secondary btn-lg" onclick="scheduleOptimization()">
                        <i class="fas fa-calendar me-2"></i>Schedule Review
                    </button>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
    console.log('✅ Comprehensive implementation plan displayed successfully');
}

// ============================================================================
// ADDITIONAL IMPLEMENTATION PLAN SECTIONS
// ============================================================================

function renderGovernanceSection(governance, monitoring) {
    if (!governance || Object.keys(governance).length === 0) return '';
    
    return `
        <div class="card border-0 shadow-lg mb-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                    <i class="fas fa-users-cog me-2"></i>Governance & Change Management
                </h5>
                <p class="mb-0 small opacity-90">Approval workflows, change control, and team coordination</p>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6 class="text-primary mb-3">
                            <i class="fas fa-clipboard-check me-2"></i>Approval Workflows
                        </h6>
                        ${renderApprovalWorkflows(governance.approval_workflows)}
                        
                        <h6 class="text-primary mb-3 mt-4">
                            <i class="fas fa-exchange-alt me-2"></i>Change Management
                        </h6>
                        ${renderChangeManagement(governance.change_management)}
                    </div>
                    <div class="col-md-6">
                        <h6 class="text-primary mb-3">
                            <i class="fas fa-calendar-alt me-2"></i>Regular Review Schedule
                        </h6>
                        ${renderReviewSchedule()}
                        
                        <h6 class="text-primary mb-3 mt-4">
                            <i class="fas fa-undo me-2"></i>Rollback Procedures
                        </h6>
                        ${renderRollbackProcedures(governance.rollback_procedures)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderSuccessAndMonitoringSection(success, monitoring) {
    return `
        <div class="card border-0 shadow-lg mb-4">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0">
                    <i class="fas fa-bullseye me-2"></i>Success Criteria & Monitoring
                </h5>
                <p class="mb-0 small opacity-90">KPIs, monitoring strategy, and success metrics</p>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <h6 class="text-success mb-3">
                            <i class="fas fa-dollar-sign me-2"></i>Financial Targets
                        </h6>
                        ${renderFinancialTargets(success.financial_targets || success.financial_success_criteria)}
                    </div>
                    <div class="col-md-4">
                        <h6 class="text-info mb-3">
                            <i class="fas fa-tachometer-alt me-2"></i>Performance Targets
                        </h6>
                        ${renderPerformanceTargets(success.performance_targets || success.performance_success_criteria)}
                    </div>
                    <div class="col-md-4">
                        <h6 class="text-warning mb-3">
                            <i class="fas fa-chart-line me-2"></i>Monitoring Strategy
                        </h6>
                        ${renderMonitoringStrategy(monitoring)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderRiskManagementSection(risk, contingency) {
    return `
        <div class="card border-0 shadow-lg mb-4">
            <div class="card-header bg-warning text-dark">
                <h5 class="mb-0">
                    <i class="fas fa-shield-alt me-2"></i>Risk Management & Contingency Planning
                </h5>
                <p class="mb-0 small opacity-75">Risk mitigation strategies and emergency procedures</p>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6 class="text-warning mb-3">
                            <i class="fas fa-exclamation-triangle me-2"></i>Risk Mitigation
                        </h6>
                        ${renderRiskMitigation(risk)}
                    </div>
                    <div class="col-md-6">
                        <h6 class="text-danger mb-3">
                            <i class="fas fa-life-ring me-2"></i>Contingency Plans
                        </h6>
                        ${renderContingencyPlans(contingency)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderTimelineResourceSection(timeline) {
    return `
        <div class="card border-0 shadow-lg mb-4">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0">
                    <i class="fas fa-project-diagram me-2"></i>Timeline & Resource Planning
                </h5>
                <p class="mb-0 small opacity-90">Resource allocation, critical path, and timeline optimization</p>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6 class="text-info mb-3">
                            <i class="fas fa-route me-2"></i>Critical Path
                        </h6>
                        ${renderCriticalPath(timeline.critical_path)}
                        
                        <h6 class="text-info mb-3 mt-4">
                            <i class="fas fa-clock me-2"></i>Timeline Confidence
                        </h6>
                        <div class="progress mb-2">
                            <div class="progress-bar bg-info" style="width: ${(timeline.timeline_confidence || 0.8) * 100}%"></div>
                        </div>
                        <small class="text-muted">${((timeline.timeline_confidence || 0.8) * 100).toFixed(0)}% confidence in timeline estimates</small>
                    </div>
                    <div class="col-md-6">
                        <h6 class="text-info mb-3">
                            <i class="fas fa-users me-2"></i>Resource Requirements
                        </h6>
                        ${renderResourceRequirements(timeline.resource_requirements)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Helper rendering functions
function renderApprovalWorkflows(workflows) {
    if (!workflows) {
        return `
            <ul class="list-group list-group-flush">
                <li class="list-group-item border-0 px-0">Team Lead approval for low-risk changes</li>
                <li class="list-group-item border-0 px-0">Manager approval for high-impact changes</li>
                <li class="list-group-item border-0 px-0">Change board review for critical modifications</li>
            </ul>
        `;
    }
    
    return `
        <ul class="list-group list-group-flush">
            ${Array.isArray(workflows) ? workflows.map(workflow => 
                `<li class="list-group-item border-0 px-0">${workflow.change_type || workflow}: ${workflow.approval_level || 'Team Lead'}</li>`
            ).join('') : '<li class="list-group-item border-0 px-0">Standard approval workflows configured</li>'}
        </ul>
    `;
}

function renderChangeManagement(changeManagement) {
    return `
        <ul class="list-group list-group-flush">
            <li class="list-group-item border-0 px-0">
                <i class="fas fa-calendar me-2 text-primary"></i>Scheduled maintenance windows
            </li>
            <li class="list-group-item border-0 px-0">
                <i class="fas fa-test me-2 text-success"></i>Pre-production testing required
            </li>
            <li class="list-group-item border-0 px-0">
                <i class="fas fa-backup me-2 text-warning"></i>Configuration backup mandatory
            </li>
        </ul>
    `;
}

function renderReviewSchedule() {
    return `
        <div class="row">
            <div class="col-12">
                <div class="card border border-primary bg-light mb-2">
                    <div class="card-body p-3">
                        <h6 class="card-title mb-1">📅 Weekly Progress Reviews</h6>
                        <small class="text-muted">Every Friday at 2:00 PM - Progress assessment and risk review</small>
                    </div>
                </div>
                <div class="card border border-success bg-light mb-2">
                    <div class="card-body p-3">
                        <h6 class="card-title mb-1">📊 Monthly Cost Reviews</h6>
                        <small class="text-muted">First Monday of month - Savings validation and optimization opportunities</small>
                    </div>
                </div>
                <div class="card border border-warning bg-light">
                    <div class="card-body p-3">
                        <h6 class="card-title mb-1">🎯 Quarterly Strategic Reviews</h6>
                        <small class="text-muted">End of quarter - Overall strategy assessment and planning</small>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderRollbackProcedures(procedures) {
    return `
        <ul class="list-group list-group-flush">
            <li class="list-group-item border-0 px-0">
                <i class="fas fa-stopwatch me-2 text-danger"></i>15-minute rollback window
            </li>
            <li class="list-group-item border-0 px-0">
                <i class="fas fa-bell me-2 text-warning"></i>Automated alerting on issues
            </li>
            <li class="list-group-item border-0 px-0">
                <i class="fas fa-undo me-2 text-info"></i>One-click configuration restore
            </li>
        </ul>
    `;
}

function renderFinancialTargets(targets) {
    if (!targets) {
        return `
            <ul class="list-group list-group-flush">
                <li class="list-group-item border-0 px-0">Monthly savings validation</li>
                <li class="list-group-item border-0 px-0">ROI tracking and reporting</li>
                <li class="list-group-item border-0 px-0">Cost trend analysis</li>
            </ul>
        `;
    }
    
    return `
        <ul class="list-group list-group-flush">
            <li class="list-group-item border-0 px-0">Target Savings: ${targets.monthly_savings_target || targets.target_monthly_savings || 'TBD'}</li>
            <li class="list-group-item border-0 px-0">Annual ROI: ${targets.annual_roi_target || targets.target_annual_roi || 'TBD'}</li>
            <li class="list-group-item border-0 px-0">Payback Period: ${targets.payback_period || '< 3 months'}</li>
        </ul>
    `;
}

function renderPerformanceTargets(targets) {
    if (!targets) {
        return `
            <ul class="list-group list-group-flush">
                <li class="list-group-item border-0 px-0">Availability > 99.9%</li>
                <li class="list-group-item border-0 px-0">Response time impact < 5%</li>
                <li class="list-group-item border-0 px-0">Zero service interruptions</li>
            </ul>
        `;
    }
    
    return `
        <ul class="list-group list-group-flush">
            <li class="list-group-item border-0 px-0">Availability: ${targets.availability_target || '> 99.9%'}</li>
            <li class="list-group-item border-0 px-0">Performance: ${targets.performance_impact || '< 5% degradation'}</li>
            <li class="list-group-item border-0 px-0">Efficiency: ${targets.resource_efficiency || '> 80%'}</li>
        </ul>
    `;
}

function renderMonitoringStrategy(monitoring) {
    return `
        <ul class="list-group list-group-flush">
            <li class="list-group-item border-0 px-0">
                <i class="fas fa-chart-line me-2 text-success"></i>Real-time cost tracking
            </li>
            <li class="list-group-item border-0 px-0">
                <i class="fas fa-bell me-2 text-warning"></i>Automated alert thresholds
            </li>
            <li class="list-group-item border-0 px-0">
                <i class="fas fa-dashboard me-2 text-info"></i>Performance dashboards
            </li>
        </ul>
    `;
}

function renderRiskMitigation(risk) {
    return `
        <ul class="list-group list-group-flush">
            <li class="list-group-item border-0 px-0">Phased implementation approach</li>
            <li class="list-group-item border-0 px-0">Comprehensive testing in staging</li>
            <li class="list-group-item border-0 px-0">24/7 monitoring during changes</li>
            <li class="list-group-item border-0 px-0">Immediate rollback capabilities</li>
        </ul>
    `;
}

function renderContingencyPlans(contingency) {
    return `
        <div class="row">
            <div class="col-12">
                <div class="alert alert-warning border-0 mb-2">
                    <strong>Performance Degradation:</strong> Immediate rollback with 15-minute RTO
                </div>
                <div class="alert alert-danger border-0 mb-2">
                    <strong>Service Outage:</strong> Emergency response team activation
                </div>
                <div class="alert alert-info border-0">
                    <strong>Budget Overrun:</strong> Scope adjustment and prioritization review
                </div>
            </div>
        </div>
    `;
}

function renderCriticalPath(criticalPath) {
    if (!criticalPath || !Array.isArray(criticalPath)) {
        return '<p class="text-muted">Critical path analysis not available</p>';
    }
    
    return `
        <ul class="list-group list-group-flush">
            ${criticalPath.map(item => 
                `<li class="list-group-item border-0 px-0">
                    <i class="fas fa-arrow-right me-2 text-danger"></i>${item}
                </li>`
            ).join('')}
        </ul>
    `;
}

function renderResourceRequirements(requirements) {
    if (!requirements) {
        return '<p class="text-muted">Resource requirements not specified</p>';
    }
    
    return `
        <ul class="list-group list-group-flush">
            <li class="list-group-item border-0 px-0">
                <strong>Engineering:</strong> ${requirements.engineering_fte || 'TBD'} FTE
            </li>
            <li class="list-group-item border-0 px-0">
                <strong>Total Effort:</strong> ${requirements.total_effort_hours || 'TBD'} hours
            </li>
            <li class="list-group-item border-0 px-0">
                <strong>Skills:</strong> ${requirements.specialized_skills_needed?.join(', ') || 'Kubernetes, Azure'}
            </li>
        </ul>
    `;
}

/**
 * Enhanced copy to clipboard function for code blocks
 */
function copyCodeToClipboard(elementId, buttonElement) {
    const codeElement = document.getElementById(elementId);
    if (!codeElement) {
        console.error('Code element not found:', elementId);
        return;
    }
    
    const text = codeElement.textContent || codeElement.innerText;
    
    navigator.clipboard.writeText(text).then(() => {
        // Update button to show success
        const originalHTML = buttonElement.innerHTML;
        buttonElement.innerHTML = '<i class="fas fa-check text-success"></i>';
        buttonElement.classList.add('btn-success');
        buttonElement.classList.remove('btn-outline-light');
        
        // Show success notification
        showNotification('Code copied to clipboard!', 'success', 2000);
        
        // Reset button after 2 seconds
        setTimeout(() => {
            buttonElement.innerHTML = originalHTML;
            buttonElement.classList.remove('btn-success');
            buttonElement.classList.add('btn-outline-light');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy to clipboard', 'error');
    });
}

/**
 * Get priority badge class with theme colors
 */
function getPriorityBadgeClass(priority) {
    const classes = {
        'Critical': 'bg-danger',
        'High': 'bg-warning text-dark',
        'Medium': 'bg-info',
        'Low': 'bg-secondary'
    };
    return classes[priority] || 'bg-secondary';
}

/**
 * Get risk badge color matching theme
 */
function getRiskBadgeColor(risk) {
    const colors = {
        'High': 'bg-danger bg-opacity-90',
        'Medium': 'bg-warning bg-opacity-90 text-dark',
        'Low': 'bg-success bg-opacity-90'
    };
    return colors[risk] || 'bg-success bg-opacity-90';
}

function renderEnhancedPhaseCard(phase, phaseNumber) {
    const riskColorClass = getRiskColorClass(phase.risk_level || phase.risk);
    const savings = phase.projected_savings || phase.savings || 0;
    const duration = phase.duration_weeks || phase.weeks || phase.duration || 'TBD';
    const title = phase.title || `Phase ${phaseNumber}`;
    
    return `
        <div class="card border-0 shadow mb-4 phase-card">
            <div class="card-header ${riskColorClass} text-white">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">
                        <i class="fas fa-${getPhaseIcon(title)} me-2"></i>
                        Phase ${phaseNumber}: ${title}
                    </h6>
                    <div class="d-flex gap-2">
                        <span class="badge bg-light text-dark">📅 ${duration} weeks</span>
                        <span class="badge bg-light text-dark">💰 $${savings.toLocaleString()}/mo</span>
                        <span class="badge bg-light text-dark">⚠️ ${phase.risk_level || phase.risk || 'Low'} Risk</span>
                    </div>
                </div>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-lg-8">
                        <h6 class="mb-3">📋 Implementation Tasks</h6>
                        ${renderEnhancedTasks(phase.tasks, phaseNumber)}
                        
                        ${phase.success_criteria && phase.success_criteria.length > 0 ? `
                            <h6 class="mt-4 mb-3">✅ Success Criteria</h6>
                            <ul class="list-group list-group-flush">
                                ${(phase.success_criteria || []).map(criteria => 
                                    `<li class="list-group-item border-0 px-0">
                                        <i class="fas fa-check text-success me-2"></i>${criteria}
                                    </li>`
                                ).join('')}
                            </ul>
                        ` : ''}
                    </div>
                    
                    <div class="col-lg-4">
                        <div class="card bg-light h-100">
                            <div class="card-body">
                                <h6 class="mb-3">📊 Phase Overview</h6>
                                
                                <div class="phase-detail-item mb-3">
                                    <strong>Timeline:</strong>
                                    <div>Week ${phase.start_week || 'TBD'} → Week ${phase.end_week || 'TBD'}</div>
                                </div>
                                
                                <div class="phase-detail-item mb-3">
                                    <strong>Priority:</strong>
                                    <span class="badge ${getPriorityBadgeClass(phase.priority_level || 'Medium')}">${phase.priority_level || 'Medium'}</span>
                                </div>
                                
                                <div class="phase-detail-item mb-3">
                                    <strong>Type:</strong>
                                    <span class="badge bg-secondary">${phase.type || 'optimization'}</span>
                                </div>
                                
                                <div class="text-center mt-4 p-3 bg-success text-white rounded">
                                    <div class="h4 mb-1">$${savings.toLocaleString()}</div>
                                    <small>Monthly Impact</small>
                                </div>
                                
                                ${phase.resource_requirements ? `
                                    <div class="mt-3">
                                        <h6 class="small text-muted mb-2">Resource Needs:</h6>
                                        <small class="text-muted">
                                            ${phase.resource_requirements.engineering_hours || 0}h engineering effort
                                        </small>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ——— Simple Task Renderer ———
/**
 * Enhanced Task Renderer with Expandable Sections and Copy Functionality
 */
/**
 * Enhanced Task Renderer with Horizontal Layout and Better Styling
 */
function renderEnhancedTasks(tasks, phaseNumber) {
    if (!tasks || !Array.isArray(tasks) || tasks.length === 0) {
        return '<p class="text-muted">No specific tasks defined for this phase.</p>';
    }
    
    return `
        <div class="accordion accordion-flush" id="tasksAccordion${phaseNumber}">
            ${tasks.map((task, index) => {
                const taskId = `task${phaseNumber}_${index}`;
                const hasCommand = task.command && task.command.trim();
                const hasTemplate = task.template && task.template.trim();
                
                return `
                    <div class="accordion-item border-0 rounded-3 mb-3 shadow-sm" style="border: 1px solid #e3f2fd !important;">
                        <h2 class="accordion-header" id="heading${taskId}">
                            <button class="accordion-button collapsed bg-light rounded-3" type="button" 
                                    data-bs-toggle="collapse" data-bs-target="#collapse${taskId}" 
                                    aria-expanded="false" aria-controls="collapse${taskId}"
                                    style="border: none; box-shadow: none;">
                                <div class="d-flex justify-content-between align-items-center w-100 me-3">
                                    <div class="d-flex align-items-center">
                                        <i class="fas fa-tasks text-primary me-3 fa-lg"></i>
                                        <div>
                                            <strong class="text-primary fs-6">${task.task || task.title || `Task ${index + 1}`}</strong>
                                            <div class="d-flex gap-2 mt-1">
                                                ${task.estimated_time ? `<span class="badge bg-secondary">${task.estimated_time}</span>` : ''}
                                                ${task.estimated_hours ? `<span class="badge bg-info">${task.estimated_hours}h</span>` : ''}
                                                ${hasCommand ? '<span class="badge bg-success"><i class="fas fa-terminal me-1"></i>Commands</span>' : ''}
                                                ${hasTemplate ? '<span class="badge bg-warning"><i class="fas fa-file-code me-1"></i>YAML</span>' : ''}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </button>
                        </h2>
                        <div id="collapse${taskId}" class="accordion-collapse collapse" 
                             aria-labelledby="heading${taskId}" data-bs-parent="#tasksAccordion${phaseNumber}">
                            <div class="accordion-body bg-white">
                                
                                <!-- Task Description Section -->
                                <div class="task-description-section mb-4">
                                    <h6 class="text-primary mb-3">
                                        <i class="fas fa-info-circle me-2"></i>Task Details
                                    </h6>
                                    <div class="row">
                                        <div class="col-md-8">
                                            <p class="mb-3">${task.description || 'No description provided'}</p>
                                            
                                            ${task.deliverable ? `
                                                <div class="alert alert-light border-start border-success border-4 mb-3">
                                                    <strong class="text-success">📦 Deliverable:</strong> ${task.deliverable}
                                                </div>
                                            ` : ''}
                                            
                                            ${task.expected_outcome ? `
                                                <div class="alert alert-primary bg-primary bg-opacity-10 border-0 mb-3">
                                                    <strong>🎯 Expected Outcome:</strong> ${task.expected_outcome}
                                                </div>
                                            ` : ''}
                                        </div>
                                        
                                        <div class="col-md-4">
                                            ${task.skills_required ? `
                                                <h6 class="text-muted mb-2">🛠️ Skills Required</h6>
                                                <div class="d-flex flex-wrap gap-1 mb-3">
                                                    ${task.skills_required.map(skill => 
                                                        `<span class="badge bg-light text-dark border">${skill}</span>`
                                                    ).join('')}
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Commands & Templates Section (Horizontal Layout) -->
                                ${hasCommand || hasTemplate ? `
                                    <div class="commands-templates-section">
                                        <h6 class="text-primary mb-3">
                                            <i class="fas fa-code me-2"></i>Implementation Resources
                                        </h6>
                                        
                                        <!-- Horizontal Tabs for Commands and Templates -->
                                        <ul class="nav nav-pills nav-fill mb-3" id="codeTabsNav${taskId}" role="tablist">
                                            ${hasCommand ? `
                                                <li class="nav-item" role="presentation">
                                                    <button class="nav-link active" id="commands-tab-${taskId}" data-bs-toggle="pill" 
                                                            data-bs-target="#commands-${taskId}" type="button" role="tab">
                                                        <i class="fas fa-terminal me-2"></i>Commands
                                                    </button>
                                                </li>
                                            ` : ''}
                                            ${hasTemplate ? `
                                                <li class="nav-item" role="presentation">
                                                    <button class="nav-link ${!hasCommand ? 'active' : ''}" id="template-tab-${taskId}" data-bs-toggle="pill" 
                                                            data-bs-target="#template-${taskId}" type="button" role="tab">
                                                        <i class="fas fa-file-code me-2"></i>YAML Template
                                                    </button>
                                                </li>
                                            ` : ''}
                                        </ul>
                                        
                                        <!-- Tab Content -->
                                        <div class="tab-content" id="codeTabsContent${taskId}">
                                            ${hasCommand ? `
                                                <div class="tab-pane fade show active" id="commands-${taskId}" role="tabpanel">
                                                    <div class="code-block-container position-relative">
                                                        <div class="code-header d-flex justify-content-between align-items-center bg-dark text-white px-3 py-2 rounded-top">
                                                            <span class="small"><i class="fas fa-terminal me-2"></i>Bash Commands</span>
                                                            <button class="btn btn-sm btn-outline-light copy-btn" 
                                                                    onclick="copyCodeToClipboard('${taskId}-command', this)"
                                                                    title="Copy to clipboard">
                                                                <i class="fas fa-copy"></i>
                                                            </button>
                                                        </div>
                                                        <div class="code-content bg-dark text-white p-3 rounded-bottom" 
                                                             style="max-height: 300px; overflow-x: auto; overflow-y: auto;">
                                                            <pre id="${taskId}-command" class="mb-0"><code class="text-white">${escapeHtml(task.command)}</code></pre>
                                                        </div>
                                                    </div>
                                                </div>
                                            ` : ''}
                                            
                                            ${hasTemplate ? `
                                                <div class="tab-pane fade ${!hasCommand ? 'show active' : ''}" id="template-${taskId}" role="tabpanel">
                                                    <div class="code-block-container position-relative">
                                                        <div class="code-header d-flex justify-content-between align-items-center bg-primary text-white px-3 py-2 rounded-top">
                                                            <span class="small"><i class="fas fa-file-code me-2"></i>YAML Configuration</span>
                                                            <button class="btn btn-sm btn-outline-light copy-btn" 
                                                                    onclick="copyCodeToClipboard('${taskId}-template', this)"
                                                                    title="Copy to clipboard">
                                                                <i class="fas fa-copy"></i>
                                                            </button>
                                                        </div>
                                                        <div class="code-content bg-light border p-3 rounded-bottom" 
                                                             style="max-height: 300px; overflow-x: auto; overflow-y: auto;">
                                                            <pre id="${taskId}-template" class="mb-0"><code class="text-dark">${escapeHtml(task.template)}</code></pre>
                                                        </div>
                                                    </div>
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Renders individual phase card
 */
function renderEnhancedPhaseCard(phase, phaseNumber) {
    const riskColorClass = getRiskColorClass(phase.risk_level || phase.risk);
    const savings = phase.projected_savings || phase.savings || 0;
    const duration = phase.duration_weeks || phase.weeks || phase.duration || 'TBD';
    const title = phase.title || `Phase ${phaseNumber}`;
    
    return `
        <div class="card border-0 shadow-lg mb-4 phase-card" style="border-radius: 15px; overflow: hidden;">
            <!-- Phase Header with Gradient -->
            <div class="card-header text-white position-relative" 
                 style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; padding: 1.5rem;">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h5 class="mb-2 fw-bold">
                            <i class="fas fa-${getPhaseIcon(title)} me-3"></i>
                            Phase ${phaseNumber}: ${title}
                        </h5>
                        <p class="mb-0 opacity-90">
                            ${phase.description || 'Strategic implementation phase for AKS optimization'}
                        </p>
                    </div>
                    <div class="phase-badges text-end">
                        <div class="badge bg-white bg-opacity-20 text-white mb-2 px-3 py-2">
                            <i class="fas fa-calendar me-1"></i>${duration} weeks
                        </div>
                        <div class="badge bg-white bg-opacity-20 text-white mb-2 px-3 py-2">
                            <i class="fas fa-dollar-sign me-1"></i>$${savings.toLocaleString()}/mo
                        </div>
                        <div class="badge ${getRiskBadgeColor(phase.risk_level || phase.risk)} px-3 py-2">
                            <i class="fas fa-shield-alt me-1"></i>${phase.risk_level || phase.risk || 'Low'} Risk
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Phase Content -->
            <div class="card-body p-0">
                <div class="row g-0">
                    <!-- Main Content Area -->
                    <div class="col-lg-8 p-4">
                        <h6 class="text-primary mb-4 fw-bold">
                            <i class="fas fa-list-check me-2"></i>Implementation Tasks
                        </h6>
                        ${renderEnhancedTasks(phase.tasks, phaseNumber)}
                        
                        ${phase.success_criteria && phase.success_criteria.length > 0 ? `
                            <div class="mt-4">
                                <h6 class="text-success mb-3 fw-bold">
                                    <i class="fas fa-check-circle me-2"></i>Success Criteria
                                </h6>
                                <div class="row">
                                    ${(phase.success_criteria || []).map((criteria, idx) => `
                                        <div class="col-md-6 mb-2">
                                            <div class="d-flex align-items-start">
                                                <i class="fas fa-check text-success me-2 mt-1"></i>
                                                <span class="small">${criteria}</span>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    
                    <!-- Sidebar -->
                    <div class="col-lg-4 bg-light p-4 border-start">
                        <h6 class="text-primary mb-4 fw-bold">
                            <i class="fas fa-info-circle me-2"></i>Phase Overview
                        </h6>
                        
                        <!-- Timeline Card -->
                        <div class="card border-0 bg-white shadow-sm mb-3">
                            <div class="card-body p-3">
                                <h6 class="card-title small text-muted mb-2">📅 Timeline</h6>
                                <div class="d-flex justify-content-between">
                                    <span class="small">Start:</span>
                                    <strong class="small text-primary">Week ${phase.start_week || 'TBD'}</strong>
                                </div>
                                <div class="d-flex justify-content-between">
                                    <span class="small">End:</span>
                                    <strong class="small text-primary">Week ${phase.end_week || 'TBD'}</strong>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Priority Card -->
                        <div class="card border-0 bg-white shadow-sm mb-3">
                            <div class="card-body p-3">
                                <h6 class="card-title small text-muted mb-2">⚡ Priority</h6>
                                <span class="badge ${getPriorityBadgeClass(phase.priority_level || 'Medium')} px-3 py-2">
                                    ${phase.priority_level || 'Medium'}
                                </span>
                            </div>
                        </div>
                        
                        <!-- Financial Impact Card -->
                        <div class="card border-0 shadow-sm mb-3" 
                             style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">
                            <div class="card-body text-white text-center p-3">
                                <h6 class="card-title small opacity-90 mb-2">💰 Monthly Impact</h6>
                                <div class="h4 mb-1 fw-bold">$${savings.toLocaleString()}</div>
                                <small class="opacity-90">Cost Savings</small>
                            </div>
                        </div>
                        
                        ${phase.resource_requirements ? `
                            <!-- Resource Requirements -->
                            <div class="card border-0 bg-white shadow-sm mb-3">
                                <div class="card-body p-3">
                                    <h6 class="card-title small text-muted mb-2">👥 Resources</h6>
                                    <div class="small">
                                        <div class="d-flex justify-content-between">
                                            <span>Engineering:</span>
                                            <strong>${phase.resource_requirements.engineering_hours || 0}h</strong>
                                        </div>
                                        <div class="d-flex justify-content-between">
                                            <span>FTE:</span>
                                            <strong>${phase.resource_requirements.fte_estimate || 0.5}</strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}


/**
 * Renders tasks accordion for a phase
 */
function renderTasksAccordion(tasks, phaseNumber) {
    if (!tasks?.length) return '<p class="text-muted">No tasks defined</p>';
    
    return `
        <div class="accordion accordion-flush" id="phase${phaseNumber}Tasks">
            ${tasks.map((task, index) => {
                const taskId = `task${phaseNumber}_${index}`;
                return `
                    <div class="accordion-item">
                        <h2 class="accordion-header">
                            <button class="accordion-button collapsed" type="button" 
                                    data-bs-toggle="collapse" data-bs-target="#${taskId}">
                                <strong>${task.task || `Task ${index + 1}`}</strong>
                                ${task.time_estimate ? `<small class="text-muted ms-2">(${task.time_estimate})</small>` : ''}
                            </button>
                        </h2>
                        <div id="${taskId}" class="accordion-collapse collapse" data-bs-parent="#phase${phaseNumber}Tasks">
                            <div class="accordion-body">
                                <p><strong>Description:</strong> ${task.description}</p>
                                ${task.command ? `
                                    <div class="mb-3">
                                        <strong>Command:</strong>
                                        <div class="bg-dark text-light p-3 rounded mt-2 position-relative">
                                            <code>${task.command}</code>
                                            <button class="btn btn-sm btn-outline-light position-absolute top-0 end-0 m-2" 
                                                    onclick="copyToClipboard('${task.command.replace(/'/g, "\\'")}')">
                                                <i class="fas fa-copy"></i>
                                            </button>
                                        </div>
                                    </div>
                                ` : ''}
                                ${task.template ? `
                                    <div class="mb-3">
                                        <strong>YAML Template:</strong>
                                        <div class="bg-light border rounded mt-2 position-relative" style="max-height: 300px; overflow-y: auto;">
                                            <pre class="p-3 mb-0"><code>${escapeHtml(task.template)}</code></pre>
                                            <button class="btn btn-sm btn-outline-primary position-absolute top-0 end-0 m-2" 
                                                    onclick="copyToClipboard(\`${task.template.replace(/`/g, '\\`')}\`)">
                                                <i class="fas fa-copy"></i>
                                            </button>
                                        </div>
                                    </div>
                                ` : ''}
                                <div class="alert alert-info">
                                    <strong>Expected Outcome:</strong> ${task.expected_outcome}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Renders validation steps list
 */
function renderValidationList(validationSteps) {
    if (!validationSteps?.length) return '<p class="text-muted">No validation steps defined</p>';
    
    return `
        <ul class="list-group list-group-flush">
            ${validationSteps.map(step => `
                <li class="list-group-item px-0 border-0">
                    <i class="fas fa-check text-success me-2"></i>${step}
                </li>
            `).join('')}
        </ul>
    `;
}

/**
 * Renders monitoring section for implementation plan
 */
function renderMonitoringSection(monitoringPlan) {
    return `
        <div class="card border-0 shadow-sm mt-5">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0">
                    <i class="fas fa-chart-line me-2"></i>Ongoing Monitoring & Optimization
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-4">
                    ${monitoringPlan.daily_checks ? `
                        <div class="col-md-6">
                            <h6 class="text-success">
                                <i class="fas fa-calendar-day me-2"></i>Daily Monitoring
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${monitoringPlan.daily_checks.map(check => `
                                    <li class="list-group-item border-0 px-0">${check}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${monitoringPlan.weekly_reviews ? `
                        <div class="col-md-6">
                            <h6 class="text-primary">
                                <i class="fas fa-calendar-week me-2"></i>Weekly Reviews
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${monitoringPlan.weekly_reviews.map(review => `
                                    <li class="list-group-item border-0 px-0">${review}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${monitoringPlan.monthly_assessments ? `
                        <div class="col-md-6">
                            <h6 class="text-warning">
                                <i class="fas fa-calendar-alt me-2"></i>Monthly Assessments
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${monitoringPlan.monthly_assessments.map(assessment => `
                                    <li class="list-group-item border-0 px-0">${assessment}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${monitoringPlan.automated_alerts ? `
                        <div class="col-md-6">
                            <h6 class="text-danger">
                                <i class="fas fa-exclamation-triangle me-2"></i>Automated Alerts
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${monitoringPlan.automated_alerts.map(alert => `
                                    <li class="list-group-item border-0 px-0">${alert}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Renders governance section for implementation plan
 */
function renderGovernanceSection(governancePlan) {
    return `
        <div class="card border-0 shadow-sm mt-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                    <i class="fas fa-shield-alt me-2"></i>Governance & Control Framework
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-4">
                    ${governancePlan.resource_policies ? `
                        <div class="col-md-4">
                            <h6 class="text-primary">
                                <i class="fas fa-cogs me-2"></i>Resource Policies
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${governancePlan.resource_policies.map(policy => `
                                    <li class="list-group-item border-0 px-0">${policy}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${governancePlan.cost_controls ? `
                        <div class="col-md-4">
                            <h6 class="text-success">
                                <i class="fas fa-dollar-sign me-2"></i>Cost Controls
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${governancePlan.cost_controls.map(control => `
                                    <li class="list-group-item border-0 px-0">${control}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${governancePlan.operational_procedures ? `
                        <div class="col-md-4">
                            <h6 class="text-warning">
                                <i class="fas fa-clipboard-list me-2"></i>Operational Procedures
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${governancePlan.operational_procedures.map(procedure => `
                                    <li class="list-group-item border-0 px-0">${procedure}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Renders success metrics section
 */
function renderSuccessMetricsSection(successMetrics) {
    return `
        <div class="card border-0 shadow-sm mt-4">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0">
                    <i class="fas fa-bullseye me-2"></i>Success Metrics & KPIs
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-3">
                    ${Object.entries(successMetrics).map(([categoryKey, categoryData]) => {
                        if (!categoryData || typeof categoryData !== 'object') return '';
                        return `
                        <div class="col-md-4">
                            <div class="metric-summary-card">
                                <h6 class="text-info mb-3">
                                    <i class="fas fa-${getCategoryIcon(categoryKey)} me-2"></i>
                                    ${formatCategoryName(categoryKey)}
                                </h6>
                                ${Object.entries(categoryData).slice(0, 3).map(([key, value]) => `
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <span class="small text-muted">${formatMetricName(key)}</span>
                                        <span class="fw-bold text-primary">${value}</span>
                                    </div>
                                `).join('')}
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
 * Renders contingency section
 */
function renderContingencySection(contingencyPlans) {
    return `
        <div class="card border-0 shadow-sm mt-4">
            <div class="card-header bg-warning text-dark">
                <h5 class="mb-0">
                    <i class="fas fa-exclamation-triangle me-2"></i>Contingency Plans
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-4">
                    ${Object.entries(contingencyPlans).map(([key, plan]) => `
                        <div class="col-md-4">
                            <div class="card h-100 border-warning">
                                <div class="card-header bg-warning bg-opacity-10">
                                    <h6 class="mb-0 text-capitalize">
                                        ${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                    </h6>
                                </div>
                                <div class="card-body">
                                    <p class="small text-muted mb-2">
                                        <strong>Scenario:</strong> ${plan.scenario}
                                    </p>
                                    <p class="small mb-2">
                                        <strong>Alternative:</strong> ${plan.alternative}
                                    </p>
                                    <div class="alert alert-warning alert-sm mb-0">
                                        <strong>Impact:</strong> ${plan.impact}
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
 * Helper functions for implementation plan categories
 */
function getCategoryIcon(category) {
    const icons = {
        'cost_metrics': 'dollar-sign',
        'performance_metrics': 'tachometer-alt',
        'operational_metrics': 'cogs'
    };
    return icons[category] || 'chart-bar';
}

function formatCategoryName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatMetricName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Helper functions for implementation plan
 */
function getRiskColorClass(risk) {
    switch (risk?.toLowerCase()) {
        case 'high': return 'bg-danger';
        case 'medium': return 'bg-warning';
        case 'low': return 'bg-success';
        default: return 'bg-primary';
    }
}

function getPhaseIcon(title) {
    const titleLower = title.toLowerCase();
    if (titleLower.includes('resource') || titleLower.includes('right-sizing')) return 'cog';
    if (titleLower.includes('hpa') || titleLower.includes('scaling')) return 'expand-arrows-alt';
    if (titleLower.includes('storage')) return 'hdd';
    if (titleLower.includes('optimization')) return 'bullseye';
    return 'rocket';
}

/**
 * Shows no analysis message
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
 * Shows implementation error message
 */
function showImplementationError(container, message) {
    container.innerHTML = `
        <div class="text-center mt-4 mb-4">
            <div class="alert alert-danger">
                <h4><i class="fas fa-exclamation-circle me-2"></i>Error Loading Implementation Plan</h4>
                <p>${message}</p>
                <button class="btn btn-outline-primary" onclick="loadImplementationPlan()">
                    <i class="fas fa-redo me-2"></i>Retry
                </button>
            </div>
        </div>
    `;
}

// ============================================================================
// UI COMPONENTS & NAVIGATION
// ============================================================================


function onTabSwitch(e) {
    const tgt = e.target.getAttribute('data-bs-target');
    console.log('🔄 Tab switched to:', tgt);
    console.log('🔄 Event target:', e.target);
    
    // Remove the manual tab management - let Bootstrap handle it
    // DON'T manually hide/show tabs - Bootstrap does this automatically
    
    // Only handle the specific logic for each tab
    if (tgt === '#dashboard') {
        console.log('📊 Loading dashboard charts...');
        setTimeout(initializeCharts, 500);
    } else if (tgt === '#implementation') {
        console.log('📋 Loading implementation plan...');
        
        // Multiple attempts with different delays for reliability
        setTimeout(() => {
            console.log('📋 Attempt 1: Loading implementation plan');
            loadImplementationPlan();
        }, 100);
        
        setTimeout(() => {
            console.log('📋 Attempt 2: Checking if container exists and plan loaded');
            const container = document.getElementById('implementation-plan-container');
            if (container) {
                // Check if it's still loading or empty
                if (container.innerHTML.includes('Loading implementation plan') || 
                    container.innerHTML.includes('spinner-border') ||
                    container.innerHTML.trim() === '') {
                    console.log('📋 Plan still loading or empty, retrying...');
                    loadImplementationPlan();
                }
            } else {
                console.warn('📋 Implementation container not found, retrying...');
                loadImplementationPlan();
            }
        }, 1000);
        
        // Final attempt with longer delay
        setTimeout(() => {
            const container = document.getElementById('implementation-plan-container');
            if (container && (container.innerHTML.includes('Loading') || container.innerHTML.trim() === '')) {
                console.log('📋 Final attempt: Loading implementation plan');
                loadImplementationPlan();
            }
        }, 2000);
    } else if (tgt === '#alerts') {
        console.log('🚨 Alerts tab activated');
    }
}

/**
 * Initialize tab switching event handlers
 */

/**
 * Initialize tab switching event handlers - FIXED VERSION
 */
function initializeTabEventHandlers() {
    console.log('🔧 Initializing tab event handlers...');
    
    // Handle Bootstrap tab show events (when tab becomes visible)
    document.addEventListener('shown.bs.tab', function (event) {
        const targetTab = event.target.getAttribute('data-bs-target') || event.target.getAttribute('href');
        console.log('📋 Tab shown event:', targetTab);
        
        if (targetTab === '#implementation') {
            console.log('📋 Implementation tab activated, loading plan...');
            loadImplementationPlan();
        } else if (targetTab === '#dashboard') {
            console.log('📊 Dashboard tab activated, loading charts...');
            setTimeout(initializeCharts, 500);
        }
    });
    
    // Also handle direct clicks as fallback
    document.querySelectorAll('[data-bs-target="#implementation"]').forEach(button => {
        button.addEventListener('click', function() {
            console.log('📋 Implementation tab clicked directly');
            setTimeout(() => {
                loadImplementationPlan();
            }, 100);
        });
    });
    
    console.log('✅ Tab event handlers initialized');
}

/**
 * Switches to specified tab
 */
function switchToTab(selector) {
    const button = document.querySelector(`[data-bs-target="${selector}"]`);
    if (button) button.click();
}

/**
 * Handles tab switching events
 */
function onTabSwitch(event) {
    const target = event.target.getAttribute('data-bs-target');
    console.log('📑 Tab switched to:', target);
    
    switch (target) {
        case '#dashboard':
            setTimeout(initializeCharts, 500);
            break;
        case '#implementation':
            loadImplementationPlan();
            break;
    }
}

/**
 * Sets up tab switching functionality
 */
function setupTabSwitching() {
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(btn => {
        btn.addEventListener('shown.bs.tab', onTabSwitch);
    });
}

/**
 * Initializes grid/list view toggle functionality
 */
function initializeViewToggle() {
    console.log('🎯 Initializing grid/list view toggle...');
    
    const gridButton = document.querySelector('[data-view="grid"]');
    const listButton = document.querySelector('[data-view="list"]'); 
    const clusterGrid = document.getElementById('cluster-grid') || document.querySelector('.cluster-grid') || document.querySelector('.row');
    
    console.log('🔍 Grid button found:', !!gridButton);
    console.log('🔍 List button found:', !!listButton);
    console.log('🔍 Cluster grid found:', !!clusterGrid);
    
    if (!gridButton || !listButton) {
        console.warn('⚠️ View toggle buttons not found');
        return;
    }
    
    if (!clusterGrid) {
        console.warn('⚠️ Cluster grid container not found');
        return;
    }
    
    // Add click handlers
    gridButton.addEventListener('click', function(e) {
        e.preventDefault();
        console.log('📊 Switching to grid view');
        switchToGridView(gridButton, listButton, clusterGrid);
    });
    
    listButton.addEventListener('click', function(e) {
        e.preventDefault(); 
        console.log('📋 Switching to list view');
        switchToListView(gridButton, listButton, clusterGrid);
    });
    
    console.log('✅ Grid/List toggle initialized successfully');
}

/**
 * Switch to grid view
 */
function switchToGridView(gridButton, listButton, clusterGrid) {
    // Update button states
    gridButton.classList.add('active', 'view-toggle-active');
    listButton.classList.remove('active', 'view-toggle-active');
    
    // Update grid layout
    clusterGrid.classList.remove('list-view');
    clusterGrid.classList.add('grid-view');
    
    // Reset any list-specific styling
    const clusterCards = clusterGrid.querySelectorAll('.cluster-card');
    clusterCards.forEach(card => {
        card.style.display = '';
        card.classList.remove('list-item');
        
        const cardBody = card.querySelector('.card-body');
        if (cardBody) {
            cardBody.style.display = '';
            cardBody.style.flexDirection = '';
            cardBody.style.alignItems = '';
            cardBody.style.justifyContent = '';
            cardBody.style.width = '';
            cardBody.style.padding = '';
        }
        
        const clusterActions = card.querySelector('.cluster-actions');
        if (clusterActions) {
            clusterActions.style.position = '';
            clusterActions.style.opacity = '';
            clusterActions.style.transform = '';
            clusterActions.style.marginLeft = '';
        }
        
        const clusterInfo = card.querySelector('.cluster-info');
        if (clusterInfo) {
            clusterInfo.style.display = '';
            clusterInfo.style.alignItems = '';
            clusterInfo.style.gap = '';
            clusterInfo.style.flex = '';
        }
        
        const clusterMetrics = card.querySelector('.cluster-metrics');
        if (clusterMetrics) {
            clusterMetrics.style.display = '';
            clusterMetrics.style.gap = '';
            clusterMetrics.style.alignItems = '';
            clusterMetrics.style.flexDirection = '';
        }
    });
    
    // Update parent container if needed
    const parentRow = clusterGrid.closest('.row');
    if (parentRow) {
        parentRow.style.flexDirection = '';
    }
    
    console.log('✅ Switched to grid view');
}

/**
 * Switch to list view  
 */
function switchToListView(gridButton, listButton, clusterGrid) {
    // Update button states
    listButton.classList.add('active', 'view-toggle-active');
    gridButton.classList.remove('active', 'view-toggle-active');
    
    // Update grid layout
    clusterGrid.classList.add('list-view');
    clusterGrid.classList.remove('grid-view');
    
    // Apply list-specific styling
    const clusterCards = clusterGrid.querySelectorAll('.cluster-card');
    clusterCards.forEach(card => {
        card.classList.add('list-item');
        card.style.display = 'flex';
        card.style.alignItems = 'center';
        card.style.marginBottom = '1rem';
        
        const cardBody = card.querySelector('.card-body');
        if (cardBody) {
            cardBody.style.display = 'flex';
            cardBody.style.flexDirection = 'row';
            cardBody.style.alignItems = 'center';
            cardBody.style.justifyContent = 'space-between';
            cardBody.style.width = '100%';
            cardBody.style.padding = '1.5rem';
        }
        
        const clusterInfo = card.querySelector('.cluster-info');
        if (clusterInfo) {
            clusterInfo.style.display = 'flex';
            clusterInfo.style.alignItems = 'center';
            clusterInfo.style.gap = '1rem';
            clusterInfo.style.flex = '1';
        }
        
        const clusterMetrics = card.querySelector('.cluster-metrics');
        if (clusterMetrics) {
            clusterMetrics.style.display = 'flex';
            clusterMetrics.style.gap = '2rem';
            clusterMetrics.style.alignItems = 'center';
        }
        
        const clusterActions = card.querySelector('.cluster-actions');
        if (clusterActions) {
            clusterActions.style.position = 'static';
            clusterActions.style.opacity = '1';
            clusterActions.style.transform = 'none';
            clusterActions.style.marginLeft = '1rem';
        }
        
        // Adjust metric cards for list view
        const metricMinis = card.querySelectorAll('.metric-mini');
        metricMinis.forEach(mini => {
            mini.style.minWidth = '120px';
            mini.style.padding = '0.5rem';
            mini.style.margin = '0';
        });
    });
    
    // Update parent container for column layout
    const parentRow = clusterGrid.closest('.row');
    if (parentRow) {
        parentRow.style.flexDirection = 'column';
    }
    
    console.log('✅ Switched to list view');
}

function updateQuickStats(planData) {
    console.log('📊 Updating quick stats with plan data:', planData);
    
    // Calculate stats from plan data
    const phases = planData.implementation_phases || [];
    const totalSavings = phases.reduce((sum, phase) => sum + (phase.projected_savings || phase.savings || 0), 0);
    const totalWeeks = Math.max(...phases.map(phase => phase.end_week || phase.duration_weeks || 0), 0);
    const confidence = planData.timeline_optimization?.timeline_confidence || 0.8;
    
    // Update DOM elements if they exist
    const statsElements = {
        '#total-phases': phases.length,
        '#total-weeks': totalWeeks,
        '#total-savings': `$${totalSavings.toLocaleString()}`,
        '#plan-confidence': `${(confidence * 100).toFixed(0)}%`
    };
    
    Object.entries(statsElements).forEach(([selector, value]) => {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = value;
            console.log(`Updated ${selector} to: ${value}`);
        }
    });
}

/**
 * Displays error message (missing function)
 */
function displayError(message) {
    console.error('❌ Displaying error:', message);
    
    const container = document.getElementById('implementation-plan-container');
    if (container) {
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
    
    // Also show notification
    showNotification('Error loading implementation plan: ' + message, 'error');
}
// ============================================================================
// PLACEHOLDER FUNCTIONS (Future Features)
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
        
        .data-source-indicator { 
            position: fixed; 
            top: 90px; 
            right: 20px; 
            z-index: 1000; 
        }
        
        .data-source-badge { 
            background: rgba(255,255,255,0.95); 
            border-radius: 20px; 
            padding: 8px 16px; 
            display: flex; 
            align-items: center; 
            gap: 5px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            font-size: 0.875rem;
        }
        
        .data-source-badge.real-data { 
            border: 1px solid #28a745; 
            color: #28a745; 
        }
        
        .data-source-badge.sample-data { 
            border: 1px solid #ffc107; 
            color: #856404; 
            background: rgba(255,193,7,0.1); 
        }
        
        [data-theme="dark"] .data-source-badge { 
            background: rgba(45,55,72,0.95); 
            color: #f7fafc; 
        }
        
        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }
        
        @keyframes fadeIn {
            from { 
                opacity: 0; 
                transform: translateY(20px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
        
        .card:hover, .metric-card:hover {
            transform: translateY(-2px);
            transition: transform 0.2s ease;
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
        
        @keyframes celebration-flash {
            0%, 100% { background: var(--glass-bg-primary); }
            50% { background: linear-gradient(45deg, rgba(0, 199, 81, 0.1), rgba(50, 205, 50, 0.1)); }
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
        
        // Setup tab switching
        setupTabSwitching();

        // Setup tab switching
        initializeTabEventHandlers();
        
        // Setup keyboard shortcuts
        setupKeyboardShortcuts();
        
        // Initialize view toggle
        setTimeout(() => {
            initializeViewToggle();
        }, 500);
        
        // Initialize auto-analysis system
        setTimeout(initializeAutoAnalysisSystem, 1000);
        
        // Auto-initialize charts if dashboard is active
        if (document.querySelector('#dashboard')?.classList.contains('active')) {
            setTimeout(initializeCharts, 500);
        }

        const implementationTab = document.querySelector('#implementation');
        if (implementationTab && implementationTab.classList.contains('active')) {
            setTimeout(() => {
                loadImplementationPlanWithRetry();
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
window.copyToClipboard = copyToClipboard;
window.switchToTab = switchToTab;
window.loadImplementationPlan = loadImplementationPlan;
window.initializeCharts = initializeCharts;
window.startAnalysisTracking = startAnalysisTracking;
window.stopAnalysisTracking = stopAnalysisTracking;
window.updateAnalysisStatus = updateAnalysisStatus;
window.initializeViewToggle = initializeViewToggle;
window.switchToGridView = switchToGridView;
window.switchToListView = switchToListView;

// Export state and config for external access
window.AppState = AppState;
window.AppConfig = AppConfig;

// ============================================================================
// MAIN ENTRY POINT
// ============================================================================

/**
 * Single DOMContentLoaded event handler
 */

// Find your existing DOMContentLoaded event and add this line
document.addEventListener('DOMContentLoaded', function() {
    //Initialize dashboards
    initializeDashboard();
    console.log('✅ initializeDashboard loaded successfully');
    
    // Initialize tab event handlers
    // initializeTabEventHandlers();
    // console.log('✅ initializeDashboard loaded successfully');

    
});


console.log('✅ Enhanced AKS Cost Intelligence Dashboard loaded successfully');