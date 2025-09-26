/**
 * ============================================================================
 * AKS COST INTELLIGENCE - CLUSTER MANAGEMENT
 * ============================================================================
 * Cluster CRUD operations, selection, analysis, and removal
 * ============================================================================
 */

import { showNotification } from './notifications.js';

/**
 * Selects a cluster and navigates to its detail page
 */
export function selectCluster(clusterId) {
    logDebug('🎯 Selecting cluster:', clusterId);
    
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
export function analyzeCluster(clusterId) {
    if (event) event.stopPropagation();
    logDebug('🔍 Analyzing cluster:', clusterId);
    
    const button = event?.target?.closest('button');
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
export function removeCluster(clusterId) {
    if (event) event.stopPropagation();
    
    if (!confirm('Are you sure you want to remove this cluster? This will delete all analysis data.')) {
        return;
    }
    
    logDebug('🗑️ Removing cluster:', clusterId);
    
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

/**
 * Enhanced cluster deletion with confirmation modal
 */
export function deleteClusterWithConfirmation(clusterId, clusterName) {
    // Set global variable for deletion handler
    window.currentlyDeletingCluster = clusterId;
    
    // Update modal content
    const modal = document.getElementById('deleteClusterModal');
    if (modal) {
        const clusterNameSpan = modal.querySelector('#deleteClusterName');
        if (clusterNameSpan) {
            clusterNameSpan.textContent = clusterName || clusterId;
        }
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    } else {
        // Fallback to simple confirmation
        removeCluster(clusterId);
    }
}

/**
 * Handle cluster deletion from confirmation modal
 */
export function handleClusterDeletion(event) {
    if (!window.currentlyDeletingCluster) {
        console.error('❌ No cluster selected for deletion');
        return;
    }
    
    const button = event.target;
    const originalHTML = button.innerHTML;
    
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Deleting...';
    button.disabled = true;
    
    fetch(`/cluster/${window.currentlyDeletingCluster}/remove`, {
        method: 'DELETE',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json' 
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Cluster deleted successfully!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteClusterModal'));
            if (modal) modal.hide();
            
            // Reload page after delay
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            throw new Error(data.message || 'Failed to delete cluster');
        }
    })
    .catch(error => {
        console.error('❌ Delete error:', error);
        showNotification('Failed to delete cluster: ' + error.message, 'error');
    })
    .finally(() => {
        button.innerHTML = originalHTML;
        button.disabled = false;
        window.currentlyDeletingCluster = null;
    });
}

/**
 * Gets cluster list from API
 */
export function fetchClusters() {
    return fetch('/api/clusters')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            logDebug('📊 Clusters fetched:', data);
            return data.clusters || [];
        })
        .catch(error => {
            console.error('❌ Failed to fetch clusters:', error);
            showNotification('Failed to load clusters: ' + error.message, 'error');
            return [];
        });
}

/**
 * Refreshes cluster list in the UI
 */
export function refreshClusterList() {
    const container = document.querySelector('#clusters-container');
    if (!container) return;
    
    showNotification('Refreshing cluster list...', 'info', 2000);
    
    fetchClusters().then(clusters => {
        if (clusters.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-server fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">No Clusters Found</h5>
                    <p class="text-muted">Add your first AKS cluster to get started</p>
                    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addClusterModal">
                        <i class="fas fa-plus me-2"></i>Add Cluster
                    </button>
                </div>
            `;
        } else {
            renderClusterList(clusters, container);
        }
    });
}

/**
 * Renders cluster list in the container
 */
export function renderClusterList(clusters, container) {
    const clusterCards = clusters.map(cluster => createClusterCard(cluster)).join('');
    container.innerHTML = clusterCards;
}

/**
 * Creates a cluster card HTML
 */
export function createClusterCard(cluster) {
    const lastAnalysis = cluster.last_analysis ? new Date(cluster.last_analysis).toLocaleDateString() : 'Never';
    const statusBadge = getStatusBadge(cluster.status);
    const environmentBadge = getEnvironmentBadge(cluster.environment);
    
    return `
        <div class="col-lg-4 col-md-6 mb-4">
            <div class="card cluster-card h-100" data-cluster-id="${cluster.id}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">${cluster.cluster_name}</h6>
                    <div class="dropdown">
                        <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="dropdown">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="/cluster/${cluster.id}">
                                <i class="fas fa-eye me-2"></i>View Details
                            </a></li>
                            <li><a class="dropdown-item" onclick="analyzeCluster('${cluster.id}')">
                                <i class="fas fa-play me-2"></i>Run Analysis
                            </a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item text-danger" onclick="deleteClusterWithConfirmation('${cluster.id}', '${cluster.cluster_name}')">
                                <i class="fas fa-trash me-2"></i>Remove
                            </a></li>
                        </ul>
                    </div>
                </div>
                <div class="card-body" onclick="selectCluster('${cluster.id}')" style="cursor: pointer;">
                    <div class="row mb-3">
                        <div class="col-6">
                            <small class="text-muted">Resource Group</small>
                            <div class="fw-bold">${cluster.resource_group}</div>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Environment</small>
                            <div>${environmentBadge}</div>
                        </div>
                    </div>
                    
                    <div class="row mb-3">
                        <div class="col-6">
                            <small class="text-muted">Region</small>
                            <div>${cluster.region || 'Not specified'}</div>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Status</small>
                            <div>${statusBadge}</div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <small class="text-muted">Last Analysis</small>
                        <div>${lastAnalysis}</div>
                    </div>
                    
                    ${cluster.description ? `
                        <div class="mb-3">
                            <small class="text-muted">Description</small>
                            <div class="small">${cluster.description}</div>
                        </div>
                    ` : ''}
                    
                    ${cluster.monthly_cost ? `
                        <div class="alert alert-light border-start border-4 border-primary mb-0">
                            <div class="row">
                                <div class="col-6">
                                    <small class="text-muted">Monthly Cost</small>
                                    <div class="fw-bold text-primary">$${cluster.monthly_cost.toLocaleString()}</div>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Potential Savings</small>
                                    <div class="fw-bold text-success">$${(cluster.potential_savings || 0).toLocaleString()}</div>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                </div>
                <div class="card-footer">
                    <div class="d-flex gap-2">
                        <button class="btn btn-primary btn-sm flex-fill" onclick="selectCluster('${cluster.id}')">
                            <i class="fas fa-eye me-1"></i>View Dashboard
                        </button>
                        <button class="btn btn-outline-primary btn-sm" onclick="analyzeCluster('${cluster.id}'); event.stopPropagation();">
                            <i class="fas fa-play me-1"></i>Analyze
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Gets status badge HTML
 */
function getStatusBadge(status) {
    const statusMap = {
        'active': '<span class="badge bg-success">Active</span>',
        'analyzing': '<span class="badge bg-warning">Analyzing</span>',
        'error': '<span class="badge bg-danger">Error</span>',
        'inactive': '<span class="badge bg-secondary">Inactive</span>'
    };
    return statusMap[status] || '<span class="badge bg-secondary">Unknown</span>';
}

/**
 * Gets environment badge HTML
 */
function getEnvironmentBadge(environment) {
    const envMap = {
        'production': '<span class="badge bg-danger">Production</span>',
        'staging': '<span class="badge bg-warning">Staging</span>',
        'development': '<span class="badge bg-info">Development</span>'
    };
    return envMap[environment] || '<span class="badge bg-secondary">Unknown</span>';
}

/**
 * Bulk operations for clusters
 */
export function analyzeAllClusters() {
    showNotification('Analyzing all clusters... Feature coming soon!', 'info');
    
    // TODO: Implement bulk analysis
    // fetchClusters().then(clusters => {
    //     const promises = clusters.map(cluster => analyzeCluster(cluster.id));
    //     return Promise.all(promises);
    // });
}

/**
 * Export cluster data
 */
export function exportClusterData() {
    showNotification('Exporting cluster data...', 'info');
    
    fetchClusters().then(clusters => {
        const csvData = convertClustersToCSV(clusters);
        downloadCSV(csvData, 'aks-clusters.csv');
        showNotification('Cluster data exported successfully!', 'success');
    });
}

/**
 * Convert clusters to CSV format
 */
function convertClustersToCSV(clusters) {
    const headers = ['Name', 'Resource Group', 'Environment', 'Region', 'Status', 'Monthly Cost', 'Potential Savings', 'Last Analysis'];
    const rows = clusters.map(cluster => [
        cluster.cluster_name,
        cluster.resource_group,
        cluster.environment || '',
        cluster.region || '',
        cluster.status || 'unknown',
        cluster.monthly_cost || 0,
        cluster.potential_savings || 0,
        cluster.last_analysis || ''
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
}

/**
 * Download CSV file
 */
function downloadCSV(csvData, filename) {
    const blob = new Blob([csvData], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Make functions available globally for backward compatibility
if (typeof window !== 'undefined') {
    window.selectCluster = selectCluster;
    window.analyzeCluster = analyzeCluster;
    window.removeCluster = removeCluster;
    window.deleteClusterWithConfirmation = deleteClusterWithConfirmation;
    window.handleClusterDeletion = handleClusterDeletion;
    window.analyzeAllClusters = analyzeAllClusters;
    window.refreshClusterList = refreshClusterList;
    window.exportClusterData = exportClusterData;
}