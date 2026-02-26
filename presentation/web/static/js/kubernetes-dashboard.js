/**
 * Kubernetes Dashboard JavaScript Module
 * =======================================
 * Modular frontend components for Kubernetes dashboard.
 * Follows .clauderc principles: fail fast, no silent failures, explicit parameters.
 * 
 * Developer: Srinivas Kondepudi
 * Organization: Nivaya Technologies & kubeopt
 * Project: AKS Cost Optimizer
 */

// Base class for Kubernetes dashboard components
class KubernetesDashboardBase {
    constructor(containerId, clusterId, subscriptionId) {
        if (!containerId) {
            throw new Error('containerId parameter is required');
        }
        if (!clusterId) {
            throw new Error('clusterId parameter is required');
        }
        if (!subscriptionId) {
            throw new Error('subscriptionId parameter is required');
        }
        
        this.containerId = containerId;
        this.clusterId = clusterId;
        this.subscriptionId = subscriptionId;
        this.container = document.getElementById(containerId);
        
        if (!this.container) {
            throw new Error(`Container element with id '${containerId}' not found`);
        }
        
        this.data = null;
        this.loading = false;
        this.error = null;
    }
    
    async fetchData(endpoint) {
        if (!endpoint) {
            throw new Error('Endpoint parameter is required');
        }
        
        this.loading = true;
        this.error = null;
        
        try {
            const response = await fetch(endpoint, {
                method: 'GET',
                credentials: 'include',  // Changed to 'include' for cross-origin requests
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                logger.error(`API Error ${response.status}: ${errorText}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.data = data;
            return data;
        } catch (error) {
            this.error = error.message;
            logger.error(`Failed to fetch data from ${endpoint}:`, error);
            throw error;
        } finally {
            this.loading = false;
        }
    }
    
    renderLoading() {
        this.container.innerHTML = `
            <div class="dashboard-loading">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading...</p>
            </div>
        `;
    }
    
    renderError(message) {
        this.container.innerHTML = `
            <div class="dashboard-error">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${this.escapeHtml(message)}</p>
                <button onclick="location.reload()" class="btn-small">Retry</button>
            </div>
        `;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Pods Dashboard Component
class PodsDashboard extends KubernetesDashboardBase {
    constructor(containerId, clusterId, subscriptionId) {
        super(containerId, clusterId, subscriptionId);
        this.sortBy = 'name';
        this.sortOrder = 'asc';
        this.filterNamespace = '';
        this.filterStatus = '';
        this.searchTerm = '';
    }
    
    async init() {
        try {
            this.renderLoading();
            const endpoint = `/api/kubernetes/pods/${this.clusterId}/${this.subscriptionId}`;
            await this.fetchData(endpoint);
            this.render();
        } catch (error) {
            this.renderError(error.message);
        }
    }
    
    render() {
        if (!this.data || !this.data.pods) {
            this.renderError('No pods data available');
            return;
        }
        
        const html = `
            <div class="pods-dashboard">
                <div class="dashboard-header">
                    <h3>Pods Overview</h3>
                    <div class="summary-stats">
                        <span class="stat">
                            <strong>${this.data.total_count}</strong> Total Pods
                        </span>
                        <span class="stat healthy">
                            <i class="fas fa-check-circle"></i> ${this.data.summary.healthy_count} Healthy
                        </span>
                        <span class="stat warning">
                            <i class="fas fa-exclamation-triangle"></i> ${this.data.summary.warning_count} Warning
                        </span>
                        <span class="stat critical">
                            <i class="fas fa-times-circle"></i> ${this.data.summary.critical_count} Critical
                        </span>
                    </div>
                </div>
                
                <!-- Resource Usage Charts -->
                <div class="resource-charts-row">
                    <div class="chart-card">
                        <div class="chart-container" id="cpu-usage-chart" style="height: 200px;">
                            <!-- CPU chart will be rendered here -->
                        </div>
                    </div>
                    <div class="chart-card">
                        <div class="chart-container" id="memory-usage-chart" style="height: 200px;">
                            <!-- Memory chart will be rendered here -->
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-filters">
                    <div class="search-box">
                        <i class="fas fa-search"></i>
                        <input type="text" 
                               id="${this.containerId}-search" 
                               class="search-input" 
                               placeholder="Search pods...">
                    </div>
                    <select id="${this.containerId}-namespace-filter" class="filter-select">
                        <option value="">All Namespaces</option>
                        ${this.getNamespaceOptions()}
                    </select>
                    <select id="${this.containerId}-status-filter" class="filter-select">
                        <option value="">All Statuses</option>
                        <option value="Running">Running</option>
                        <option value="Pending">Pending</option>
                        <option value="Failed">Failed</option>
                        <option value="Succeeded">Succeeded</option>
                    </select>
                    <button onclick="kubernetesDashboard.pods.refresh()" class="btn-small">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                </div>
                
                <div class="pods-table-container">
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th onclick="kubernetesDashboard.pods.sort('name')">
                                    Name ${this.getSortIcon('name')}
                                </th>
                                <th onclick="kubernetesDashboard.pods.sort('namespace')">
                                    Namespace ${this.getSortIcon('namespace')}
                                </th>
                                <th onclick="kubernetesDashboard.pods.sort('status')">
                                    Status ${this.getSortIcon('status')}
                                </th>
                                <th>Node</th>
                                <th onclick="kubernetesDashboard.pods.sort('restarts')">
                                    Restarts ${this.getSortIcon('restarts')}
                                </th>
                                <th>CPU Request</th>
                                <th>Memory Request</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.renderPodsRows()}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
        this.attachEventListeners();
        
        // Initialize charts after DOM is ready
        setTimeout(() => {
            if (window.kubernetesCharts) {
                // Calculate aggregate CPU/Memory data from pods
                const cpuData = this.data.pods.map(pod => pod.cpu_request);
                const memoryData = this.data.pods.map(pod => pod.memory_request * 1024); // Convert GB to MB
                
                window.kubernetesCharts.createCPUChart('cpu-usage-chart', cpuData.slice(0, 24));
                window.kubernetesCharts.createMemoryChart('memory-usage-chart', memoryData.slice(0, 24));
            }
        }, 100);
    }
    
    renderPodsRows() {
        let pods = [...this.data.pods];
        
        // Apply search filter
        if (this.searchTerm) {
            const term = this.searchTerm.toLowerCase();
            pods = pods.filter(pod => 
                pod.name.toLowerCase().includes(term) ||
                pod.namespace.toLowerCase().includes(term) ||
                pod.node.toLowerCase().includes(term) ||
                pod.status.toLowerCase().includes(term)
            );
        }
        
        // Apply filters
        if (this.filterNamespace) {
            pods = pods.filter(pod => pod.namespace === this.filterNamespace);
        }
        if (this.filterStatus) {
            pods = pods.filter(pod => pod.status === this.filterStatus);
        }
        
        // Apply sorting
        pods.sort((a, b) => {
            let aVal = a[this.sortBy];
            let bVal = b[this.sortBy];
            
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }
            
            if (this.sortOrder === 'asc') {
                return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
            } else {
                return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
            }
        });
        
        return pods.map(pod => `
            <tr>
                <td>${this.escapeHtml(pod.name)}</td>
                <td>${this.escapeHtml(pod.namespace)}</td>
                <td>
                    <span class="status-badge status-${pod.status.toLowerCase()}">
                        ${pod.status}
                    </span>
                </td>
                <td>${this.escapeHtml(pod.node)}</td>
                <td>
                    <span class="${pod.restarts > 0 ? 'text-warning' : ''}">
                        ${pod.restarts}
                    </span>
                </td>
                <td>
                    <div class="resource-usage-cell">
                        <div class="resource-bar-mini">
                            <div class="resource-bar-fill cpu-fill" style="width: ${Math.min(pod.cpu_request * 100, 100)}%"></div>
                        </div>
                        <span class="resource-value">${pod.cpu_request.toFixed(3)}</span>
                    </div>
                </td>
                <td>
                    <div class="resource-usage-cell">
                        <div class="resource-bar-mini">
                            <div class="resource-bar-fill memory-fill" style="width: ${Math.min((pod.memory_request / 2) * 100, 100)}%"></div>
                        </div>
                        <span class="resource-value">${(pod.memory_request * 1024).toFixed(0)} Mi</span>
                    </div>
                </td>
            </tr>
        `).join('');
    }
    
    getNamespaceOptions() {
        const namespaces = [...new Set(this.data.pods.map(pod => pod.namespace))];
        return namespaces.map(ns => 
            `<option value="${ns}">${this.escapeHtml(ns)}</option>`
        ).join('');
    }
    
    getSortIcon(field) {
        if (this.sortBy !== field) return '';
        return this.sortOrder === 'asc' ? '↑' : '↓';
    }
    
    sort(field) {
        if (this.sortBy === field) {
            this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortBy = field;
            this.sortOrder = 'asc';
        }
        this.render();
    }
    
    attachEventListeners() {
        // Search input
        const searchInput = document.getElementById(`${this.containerId}-search`);
        if (searchInput) {
            searchInput.value = this.searchTerm || '';
            
            searchInput.addEventListener('input', (e) => {
                e.stopPropagation();
                this.searchTerm = e.target.value;
                this.updateTable();
            });
            
            searchInput.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
        
        // Namespace filter
        const namespaceFilter = document.getElementById(`${this.containerId}-namespace-filter`);
        if (namespaceFilter) {
            // Store current value before re-render
            namespaceFilter.value = this.filterNamespace || '';
            
            namespaceFilter.addEventListener('click', (e) => {
                e.stopPropagation();
            });
            
            namespaceFilter.addEventListener('change', (e) => {
                e.stopPropagation();
                this.filterNamespace = e.target.value;
                this.updateTable(); // Update only table, not entire component
            });
        }
        
        // Status filter
        const statusFilter = document.getElementById(`${this.containerId}-status-filter`);
        if (statusFilter) {
            // Store current value before re-render
            statusFilter.value = this.filterStatus || '';
            
            statusFilter.addEventListener('click', (e) => {
                e.stopPropagation();
            });
            
            statusFilter.addEventListener('change', (e) => {
                e.stopPropagation();
                this.filterStatus = e.target.value;
                this.updateTable(); // Update only table, not entire component
            });
        }
    }
    
    updateTable() {
        // Update only the table content without re-rendering the entire component
        const tableBody = this.container.querySelector('.dashboard-table tbody');
        if (tableBody) {
            tableBody.innerHTML = this.renderPodsRows();
        }
    }
    
    async refresh() {
        await this.init();
    }
}

// Workloads Dashboard Component
class WorkloadsDashboard extends KubernetesDashboardBase {
    constructor(containerId, clusterId, subscriptionId) {
        super(containerId, clusterId, subscriptionId);
    }
    
    async init() {
        try {
            this.renderLoading();
            const endpoint = `/api/kubernetes/workloads/${this.clusterId}/${this.subscriptionId}`;
            await this.fetchData(endpoint);
            this.render();
        } catch (error) {
            this.renderError(error.message);
        }
    }
    
    render() {
        if (!this.data || !this.data.workloads) {
            this.renderError('No workloads data available');
            return;
        }
        
        // Store original data for filtering
        this.originalWorkloads = [...this.data.workloads];
        this.filteredWorkloads = [...this.data.workloads];
        this.sortColumn = null;
        this.sortDirection = 'asc';
        
        const html = `
            <div class="workloads-dashboard">
                <div class="dashboard-header">
                    <h3>Workloads Overview</h3>
                    <div class="summary-stats">
                        <span class="stat">
                            <strong>${this.data.total_count}</strong> Deployments
                        </span>
                        <span class="stat">
                            <strong>${this.data.summary.total_replicas}</strong> Total Replicas
                        </span>
                        <span class="stat">
                            Health Score: <strong>${this.data.summary.avg_health_score.toFixed(0)}%</strong>
                        </span>
                    </div>
                </div>
                
                <!-- Workload Distribution Charts -->
                <div class="workload-charts-row">
                    <div class="chart-card">
                        <h4>Health Status Overview</h4>
                        <div class="chart-container" id="workload-status-chart" style="height: 250px;">
                            <!-- Status chart will be rendered here -->
                        </div>
                    </div>
                    <div class="chart-card">
                        <h4>Namespace Distribution</h4>
                        <div class="chart-container" id="namespace-distribution-chart" style="height: 250px;">
                            <!-- Namespace chart will be rendered here -->
                        </div>
                    </div>
                    <div class="chart-card">
                        <h4>Top Replica Count</h4>
                        <div class="chart-container" id="replica-distribution-chart" style="height: 250px;">
                            <!-- Replica chart will be rendered here -->
                        </div>
                    </div>
                </div>
                
                <!-- Deployment Filters -->
                <div class="dashboard-filters">
                    <div class="search-box">
                        <i class="fas fa-search"></i>
                        <input type="text" class="search-input" id="workload-search" 
                               placeholder="Search deployments..." 
                               onkeyup="window.currentWorkloadsDashboard.filterDeployments()">
                    </div>
                    
                    <select class="filter-select" id="namespace-filter" 
                            onchange="window.currentWorkloadsDashboard.filterDeployments()">
                        <option value="">All Namespaces</option>
                        ${[...new Set(this.data.workloads.map(w => w.namespace))].sort().map(ns => 
                            `<option value="${ns}">${ns}</option>`
                        ).join('')}
                    </select>
                    
                    <select class="filter-select" id="status-filter"
                            onchange="window.currentWorkloadsDashboard.filterDeployments()">
                        <option value="">All Status</option>
                        <option value="Healthy">Healthy</option>
                        <option value="Warning">Warning</option>
                        <option value="Critical">Critical</option>
                    </select>
                    
                    <select class="filter-select" id="replica-filter"
                            onchange="window.currentWorkloadsDashboard.filterDeployments()">
                        <option value="">All Replicas</option>
                        <option value="0">No Replicas (0)</option>
                        <option value="1">Single Replica (1)</option>
                        <option value="2+">Multiple (2+)</option>
                    </select>
                    
                    <button class="btn-small" onclick="window.currentWorkloadsDashboard.resetFilters()">
                        <i class="fas fa-redo"></i> Reset
                    </button>
                </div>
                
                <!-- Workloads Table -->
                <div class="workloads-table-container">
                    <div class="table-header">
                        <h4>Deployment Details</h4>
                        <span class="filter-count" id="filter-count">
                            Showing ${this.filteredWorkloads.length} of ${this.originalWorkloads.length} deployments
                        </span>
                    </div>
                    <table class="dashboard-table workloads-table">
                        <thead>
                            <tr>
                                <th onclick="window.currentWorkloadsDashboard.sortTable('name')" class="sortable">
                                    Name <i class="fas fa-sort"></i>
                                </th>
                                <th onclick="window.currentWorkloadsDashboard.sortTable('namespace')" class="sortable">
                                    Namespace <i class="fas fa-sort"></i>
                                </th>
                                <th onclick="window.currentWorkloadsDashboard.sortTable('status')" class="sortable">
                                    Status <i class="fas fa-sort"></i>
                                </th>
                                <th onclick="window.currentWorkloadsDashboard.sortTable('replicas')" class="sortable">
                                    Replicas <i class="fas fa-sort"></i>
                                </th>
                                <th onclick="window.currentWorkloadsDashboard.sortTable('health')" class="sortable">
                                    Health <i class="fas fa-sort"></i>
                                </th>
                                <th>Image</th>
                            </tr>
                        </thead>
                        <tbody id="workloads-table-body">
                            ${this.renderWorkloadRows()}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
        
        // Store reference for filtering
        window.currentWorkloadsDashboard = this;
        
        // Initialize charts after DOM is ready
        setTimeout(() => {
            this.initializeWorkloadCharts();
        }, 100);
    }
    
    renderWorkloadRows(workloads = null) {
        const data = workloads || this.filteredWorkloads || this.data.workloads;
        return data.map(workload => `
            <tr>
                <td>
                    <strong>${this.escapeHtml(workload.name)}</strong>
                </td>
                <td>
                    <span class="namespace-badge">${this.escapeHtml(workload.namespace)}</span>
                </td>
                <td>
                    <span class="status-badge status-${workload.status}">
                        ${workload.status}
                    </span>
                </td>
                <td>
                    <div class="replica-display">
                        <span class="replica-current">${workload.replicas.current}</span>
                        <span class="replica-separator">/</span>
                        <span class="replica-desired">${workload.replicas.desired}</span>
                    </div>
                </td>
                <td>
                    <div class="health-display">
                        <div class="health-bar">
                            <div class="health-fill" style="width: ${workload.health_score}%; background: ${this.getHealthColor(workload.health_score)}"></div>
                        </div>
                        <span class="health-text">${workload.health_score}%</span>
                    </div>
                </td>
                <td>
                    <span class="image-tag" title="${this.escapeHtml(workload.image)}">${this.truncateImage(workload.image)}</span>
                </td>
            </tr>
        `).join('');
    }
    
    initializeWorkloadCharts() {
        if (!window.Chart || !this.data) return;
        
        // Get CSS variable values
        const styles = getComputedStyle(document.documentElement);
        const successColor = styles.getPropertyValue('--success-color').trim() || '#7FB069';
        const warningColor = styles.getPropertyValue('--warning-color').trim() || '#FFA500';
        const dangerColor = styles.getPropertyValue('--danger-color').trim() || '#FF6B6B';
        const primaryColor = styles.getPropertyValue('--primary-color').trim() || '#4A90E2';
        const infoColor = styles.getPropertyValue('--info-color').trim() || '#5DADE2';
        const textPrimary = styles.getPropertyValue('--text-primary').trim() || '#333';
        const textSecondary = styles.getPropertyValue('--text-secondary').trim() || '#666';
        const borderColor = styles.getPropertyValue('--border-color').trim() || '#e0e0e0';
        
        // Calculate health score distribution (group into buckets)
        const healthBuckets = {
            'Excellent (90-100%)': 0,
            'Good (70-89%)': 0,
            'Fair (50-69%)': 0,
            'Poor (30-49%)': 0,
            'Critical (0-29%)': 0
        };
        
        this.data.workloads.forEach(w => {
            const score = w.health_score || 0;
            if (score >= 90) healthBuckets['Excellent (90-100%)']++;
            else if (score >= 70) healthBuckets['Good (70-89%)']++;
            else if (score >= 50) healthBuckets['Fair (50-69%)']++;
            else if (score >= 30) healthBuckets['Poor (30-49%)']++;
            else healthBuckets['Critical (0-29%)']++;
        });
        
        // Create health distribution chart as stacked bar
        const statusContainer = document.getElementById('workload-status-chart');
        if (statusContainer) {
            // Create canvas element
            const canvas = document.createElement('canvas');
            statusContainer.appendChild(canvas);
            
            const bucketColors = [
                successColor + 'E6',  // Excellent - with transparency
                successColor + '99',  // Good
                warningColor + '99',  // Fair
                warningColor + 'E6',  // Poor
                dangerColor + 'CC'    // Critical
            ];
            
            const statusChart = new Chart(canvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: Object.keys(healthBuckets),
                    datasets: [{
                        label: 'Deployments',
                        data: Object.values(healthBuckets),
                        backgroundColor: bucketColors,
                        borderColor: [
                            successColor,
                            successColor,
                            warningColor,
                            warningColor,
                            dangerColor
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed.y;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${value} deployments (${percentage}%)`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,
                                color: textSecondary
                            },
                            grid: {
                                color: borderColor
                            }
                        },
                        x: {
                            ticks: {
                                color: textSecondary,
                                maxRotation: 45,
                                minRotation: 45,
                                font: {
                                    size: 10
                                }
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        }
        
        // Calculate namespace distribution
        const namespaceCounts = {};
        this.data.workloads.forEach(w => {
            namespaceCounts[w.namespace] = (namespaceCounts[w.namespace] || 0) + 1;
        });
        
        // Create namespace distribution chart
        const namespaceContainer = document.getElementById('namespace-distribution-chart');
        if (namespaceContainer) {
            // Create canvas element
            const canvas = document.createElement('canvas');
            namespaceContainer.appendChild(canvas);
            
            const namespaceChart = new Chart(canvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: Object.keys(namespaceCounts),
                    datasets: [{
                        label: 'Deployments',
                        data: Object.values(namespaceCounts),
                        backgroundColor: primaryColor + '99', // Add transparency
                        borderColor: primaryColor,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,
                                color: textSecondary
                            },
                            grid: {
                                color: borderColor
                            }
                        },
                        x: {
                            ticks: {
                                color: textSecondary
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        }
        
        // Calculate replica distribution
        const replicaData = this.data.workloads.map(w => ({
            name: w.name,
            replicas: w.replicas.current
        })).sort((a, b) => b.replicas - a.replicas).slice(0, 5); // Top 5
        
        // Create replica distribution chart
        const replicaContainer = document.getElementById('replica-distribution-chart');
        if (replicaContainer) {
            // Create canvas element
            const canvas = document.createElement('canvas');
            replicaContainer.appendChild(canvas);
            
            const replicaChart = new Chart(canvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: replicaData.map(r => r.name),
                    datasets: [{
                        label: 'Replicas',
                        data: replicaData.map(r => r.replicas),
                        backgroundColor: infoColor + '99', // Add transparency
                        borderColor: infoColor,
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y', // Make it horizontal
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,
                                color: textSecondary
                            },
                            grid: {
                                color: borderColor
                            }
                        },
                        y: {
                            ticks: {
                                color: textSecondary
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        }
    }
    
    getHealthColor(score) {
        if (score >= 80) return 'var(--success-color)';
        if (score >= 60) return 'var(--warning-color)';
        return 'var(--danger-color)';
    }
    
    truncateImage(image) {
        const parts = image.split('/');
        const imageName = parts[parts.length - 1];
        if (imageName.length > 30) {
            return '...' + imageName.substr(-30);
        }
        return imageName;
    }
    
    filterDeployments() {
        const searchValue = document.getElementById('workload-search')?.value.toLowerCase() || '';
        const namespaceFilter = document.getElementById('namespace-filter')?.value || '';
        const statusFilter = document.getElementById('status-filter')?.value || '';
        const replicaFilter = document.getElementById('replica-filter')?.value || '';
        
        this.filteredWorkloads = this.originalWorkloads.filter(workload => {
            // Search filter
            if (searchValue && !workload.name.toLowerCase().includes(searchValue) && 
                !workload.namespace.toLowerCase().includes(searchValue)) {
                return false;
            }
            
            // Namespace filter
            if (namespaceFilter && workload.namespace !== namespaceFilter) {
                return false;
            }
            
            // Status filter
            if (statusFilter && workload.status !== statusFilter) {
                return false;
            }
            
            // Replica filter
            if (replicaFilter) {
                const replicas = workload.replicas.current;
                if (replicaFilter === '0' && replicas !== 0) return false;
                if (replicaFilter === '1' && replicas !== 1) return false;
                if (replicaFilter === '2+' && replicas < 2) return false;
            }
            
            return true;
        });
        
        this.updateTable();
    }
    
    sortTable(column) {
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }
        
        this.filteredWorkloads.sort((a, b) => {
            let valA, valB;
            
            switch (column) {
                case 'name':
                    valA = a.name.toLowerCase();
                    valB = b.name.toLowerCase();
                    break;
                case 'namespace':
                    valA = a.namespace.toLowerCase();
                    valB = b.namespace.toLowerCase();
                    break;
                case 'status':
                    valA = a.status;
                    valB = b.status;
                    break;
                case 'replicas':
                    valA = a.replicas.current;
                    valB = b.replicas.current;
                    break;
                case 'health':
                    valA = a.health_score;
                    valB = b.health_score;
                    break;
                default:
                    return 0;
            }
            
            if (this.sortDirection === 'asc') {
                return valA > valB ? 1 : valA < valB ? -1 : 0;
            } else {
                return valA < valB ? 1 : valA > valB ? -1 : 0;
            }
        });
        
        this.updateTable();
    }
    
    resetFilters() {
        document.getElementById('workload-search').value = '';
        document.getElementById('namespace-filter').value = '';
        document.getElementById('status-filter').value = '';
        document.getElementById('replica-filter').value = '';
        
        this.filteredWorkloads = [...this.originalWorkloads];
        this.updateTable();
    }
    
    updateTable() {
        const tbody = document.getElementById('workloads-table-body');
        if (tbody) {
            tbody.innerHTML = this.renderWorkloadRows(this.filteredWorkloads);
        }
        
        // Update count
        const countElement = document.getElementById('filter-count');
        if (countElement) {
            countElement.textContent = `Showing ${this.filteredWorkloads.length} of ${this.originalWorkloads.length} deployments`;
        }
    }
}

// Resources Dashboard Component
class ResourcesDashboard extends KubernetesDashboardBase {
    constructor(containerId, clusterId, subscriptionId) {
        super(containerId, clusterId, subscriptionId);
        this.expandedNamespaces = new Set();
        this.expandedCategories = new Set(['application', 'infrastructure', 'monitoring', 'system']);
        this.allResourcesData = null;
        this.selectedNamespace = null;
        this.viewMode = 'pills'; // pills, cards, table, or explorer
        
        // Store reference for global functions
        currentResourcesDashboard = this;
    }
    
    async init() {
        try {
            this.renderLoading();
            const endpoint = `/api/kubernetes/resources/${this.clusterId}/${this.subscriptionId}`;
            await this.fetchData(endpoint);
            
            // Store the fetched data for namespace details
            this.allResourcesData = this.data;
            
            this.render();
        } catch (error) {
            this.renderError(error.message);
        }
    }
    
    render() {
        if (!this.data) {
            this.renderError('No resources data available');
            return;
        }
        
        // Ensure data structure exists
        const costs = this.data.costs || {};
        const metrics = this.data.metrics || {};
        const summary = this.data.summary || {};
        const storage = this.data.storage || [];
        const network = this.data.network || {};
        const anomalies = this.data.anomalies || {};
        const namespaces = this.data.namespaces || [];
        
        // Calculate values with defaults
        const totalCost = costs.total_cost || 0;
        const computeCost = costs.compute_cost || 0;
        const storageCost = costs.storage_cost || 0;
        const networkingCost = costs.networking_cost || 0;
        const otherCost = Math.max(0, totalCost - computeCost - storageCost - networkingCost);
        
        const cpuUtil = metrics.avg_cpu_utilization || 0;
        const memUtil = metrics.avg_memory_utilization || 0;
        const maxCpuUtil = metrics.max_cpu_utilization || cpuUtil;
        const maxMemUtil = metrics.max_memory_utilization || memUtil;
        
        const totalSavings = costs.total_savings || 0;
        const optimizationScore = costs.optimization_score || 0;
        const healthScore = summary.health_score || 0;
        
        const html = `
            <div class="resources-dashboard">
                <div class="dashboard-header">
                    <h3>Infrastructure Resources</h3>
                    <div class="summary-stats">
                        <span class="stat">
                            <i class="fas fa-hdd"></i>
                            <strong>${storage.length || 0}</strong> Storage Volumes
                        </span>
                        <span class="stat">
                            <i class="fas fa-network-wired"></i>
                            <strong>${network.load_balancer_count || 0}</strong> Load Balancers
                        </span>
                        <span class="stat">
                            <i class="fas fa-globe"></i>
                            <strong>${network.public_ip_count || 0}</strong> Public IPs
                        </span>
                        <span class="stat ${anomalies.total_anomalies > 0 ? 'warning' : 'healthy'}">
                            <i class="fas fa-exclamation-triangle"></i>
                            <strong>${anomalies.total_anomalies || 0}</strong> Anomalies
                        </span>
                    </div>
                </div>
                
                <!-- Namespaces Section -->
                <div class="section-header">
                    <h3>
                        <i class="fas fa-layer-group"></i> Namespaces
                        <div class="view-toggle">
                            <button class="btn-view ${this.viewMode === 'pills' ? 'active' : ''}" onclick="setNamespaceViewMode('pills')">
                                <i class="fas fa-th"></i> Compact
                            </button>
                            <button class="btn-view ${this.viewMode === 'cards' ? 'active' : ''}" onclick="setNamespaceViewMode('cards')">
                                <i class="fas fa-th-large"></i> Cards
                            </button>
                            <button class="btn-view ${this.viewMode === 'explorer' ? 'active' : ''}" onclick="setNamespaceViewMode('explorer')">
                                <i class="fas fa-sitemap"></i> Explorer
                            </button>
                        </div>
                    </h3>
                </div>
                <div class="namespaces-container">
                    ${this.renderNamespaces(namespaces)}
                </div>
                
                <!-- Namespace Details Modal -->
                <div id="namespace-details-modal" class="modal" style="display: none;">
                    <div class="modal-content">
                        <span class="close" onclick="closeNamespaceDetails()">&times;</span>
                        <div id="namespace-details-content"></div>
                    </div>
                </div>
                
                <!-- Storage Volumes Section -->
                <div class="section-header">
                    <h3><i class="fas fa-hdd"></i> Storage Volumes</h3>
                </div>
                <div class="storage-table-container">
                    ${this.renderStorageTable(storage)}
                </div>
                
                <!-- Network Resources Section -->
                <div class="section-header">
                    <h3><i class="fas fa-network-wired"></i> Network Resources</h3>
                </div>
                <div class="network-grid">
                    ${this.renderNetworkCards(network)}
                </div>
                
                <!-- Anomalies Section -->
                ${anomalies.total_anomalies > 0 ? `
                <div class="section-header">
                    <h3><i class="fas fa-exclamation-triangle"></i> Detected Anomalies</h3>
                </div>
                <div class="anomalies-container">
                    ${this.renderAnomalies(anomalies)}
                </div>` : ''}
                
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderNamespaces(namespaces) {
        if (!namespaces || namespaces.length === 0) {
            return '<div class="no-data">No namespaces found</div>';
        }
        
        // Store namespaces data for later use
        this.namespacesData = namespaces;
        
        // Render based on view mode
        switch(this.viewMode) {
            case 'cards':
                return this.renderNamespaceCards(namespaces);
            case 'table':
                return this.renderNamespaceTable(namespaces);
            case 'explorer':
                return this.renderNamespaceExplorer(namespaces);
            case 'pills':
            default:
                return this.renderNamespacePills(namespaces);
        }
    }
    
    renderNamespacePills(namespaces) {
        
        // Categorize namespaces
        const systemNs = ['kube-system', 'kube-public', 'kube-node-lease', 'default', 'gatekeeper-system'];
        const monitoringNs = [];
        const appNs = [];
        const infraNs = [];
        
        namespaces.forEach(ns => {
            const name = ns.name || ns;
            if (systemNs.includes(name)) {
                // System namespace
            } else if (name.includes('monitoring') || name.includes('grafana') || name.includes('kubecost')) {
                monitoringNs.push(ns);
            } else if (name.includes('cert') || name.includes('nginx') || name.includes('external') || 
                      name.includes('kapp') || name.includes('secretgen') || name.includes('dataprotection')) {
                infraNs.push(ns);
            } else {
                appNs.push(ns);
            }
        });
        
        // Create a compact, organized view
        return `
            <div class="namespaces-overview">
                <div class="namespace-summary-bar">
                    <div class="summary-item">
                        <span class="summary-count">${namespaces.length}</span>
                        <span class="summary-label">Total</span>
                    </div>
                    <div class="summary-item app">
                        <span class="summary-count">${appNs.length}</span>
                        <span class="summary-label">Apps</span>
                    </div>
                    <div class="summary-item infra">
                        <span class="summary-count">${infraNs.length}</span>
                        <span class="summary-label">Infra</span>
                    </div>
                    <div class="summary-item monitoring">
                        <span class="summary-count">${monitoringNs.length}</span>
                        <span class="summary-label">Monitor</span>
                    </div>
                    <div class="summary-item system">
                        <span class="summary-count">${systemNs.length}</span>
                        <span class="summary-label">System</span>
                    </div>
                </div>
                
                <div class="namespaces-compact-list">
                    ${appNs.length > 0 ? `
                    <div class="ns-category">
                        <div class="category-header">
                            <i class="fas fa-rocket"></i>
                            <span>Applications</span>
                        </div>
                        <div class="ns-pills">
                            ${appNs.map(ns => {
                                const name = ns.name || ns;
                                const podCount = ns.pod_count || 0;
                                return `<span class="ns-pill app-pill clickable" onclick="showNamespaceDetails('${name}')" title="Click for details">
                                    <i class="fas fa-rocket"></i>
                                    ${name} <span class="pill-count">${podCount || 0}</span>
                                </span>`;
                            }).join('')}
                        </div>
                    </div>` : ''}
                    
                    ${infraNs.length > 0 ? `
                    <div class="ns-category">
                        <div class="category-header">
                            <i class="fas fa-server"></i>
                            <span>Infrastructure</span>
                        </div>
                        <div class="ns-pills">
                            ${infraNs.map(ns => {
                                const name = ns.name || ns;
                                const podCount = ns.pod_count || 0;
                                return `<span class="ns-pill infra-pill" title="${podCount} pods">
                                    ${name} <span class="pill-count">${podCount || 0}</span>
                                </span>`;
                            }).join('')}
                        </div>
                    </div>` : ''}
                    
                    ${monitoringNs.length > 0 ? `
                    <div class="ns-category">
                        <div class="category-header">
                            <i class="fas fa-chart-line"></i>
                            <span>Monitoring</span>
                        </div>
                        <div class="ns-pills">
                            ${monitoringNs.map(ns => {
                                const name = ns.name || ns;
                                const podCount = ns.pod_count || 0;
                                return `<span class="ns-pill monitoring-pill" title="${podCount} pods">
                                    ${name} <span class="pill-count">${podCount || 0}</span>
                                </span>`;
                            }).join('')}
                        </div>
                    </div>` : ''}
                    
                    <div class="ns-category">
                        <div class="category-header">
                            <i class="fas fa-cogs"></i>
                            <span>System</span>
                        </div>
                        <div class="ns-pills">
                            ${systemNs.map(name => {
                                const ns = namespaces.find(n => (n.name || n) === name);
                                if (!ns) return '';
                                const podCount = ns.pod_count || 0;
                                return `<span class="ns-pill system-pill" title="${podCount} pods">
                                    ${name} <span class="pill-count">${podCount || 0}</span>
                                </span>`;
                            }).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderStorageTable(storage) {
        if (!storage || storage.length === 0) {
            return '<div class="no-data">No storage volumes found</div>';
        }
        
        // Store storage data for later use
        this.storageData = storage;
        this.displayedVolumes = 5; // Start with 5 volumes
        
        return `
            <div class="storage-table-wrapper">
                <div class="storage-table-scroll">
                    <table class="dashboard-table storage-volumes-table">
                        <thead>
                            <tr>
                                <th style="width: 25%">Volume Name</th>
                                <th style="width: 15%">Namespace</th>
                                <th style="width: 20%">Size & Usage</th>
                                <th style="width: 15%">Storage Class</th>
                                <th style="width: 12%">Cost/Month</th>
                                <th style="width: 13%">Status</th>
                            </tr>
                        </thead>
                        <tbody id="storage-tbody">
                            ${this.renderStorageRows(storage.slice(0, this.displayedVolumes))}
                        </tbody>
                    </table>
                </div>
                ${storage.length > this.displayedVolumes ? `
                <div class="table-footer">
                    <button class="btn btn-link" onclick="showMoreVolumes()">
                        <i class="fas fa-chevron-down"></i> Show ${storage.length - this.displayedVolumes} more volumes
                    </button>
                </div>` : ''}
            </div>
        `;
    }
    
    renderStorageRows(volumes) {
        return volumes.map(vol => {
            // Extract size value properly
            let sizeDisplay = 'N/A';
            let utilizationBar = '';
            if (vol.size) {
                if (typeof vol.size === 'object') {
                    const requested = vol.size.requested_gb || 0;
                    const utilization = vol.size.utilization_percentage || 0;
                    const used = (requested * utilization / 100).toFixed(1);
                    sizeDisplay = `${requested}GB`;
                    utilizationBar = `
                        <div class="usage-bar">
                            <div class="usage-fill ${utilization > 80 ? 'high' : utilization < 30 ? 'low' : ''}" 
                                 style="width: ${utilization}%"></div>
                        </div>
                        <small>${used}GB used (${utilization.toFixed(0)}%)</small>
                    `;
                } else {
                    sizeDisplay = vol.size;
                }
            }
            
            const statusClass = vol.optimization_candidate ? 'warning' : 'healthy';
            const statusText = vol.optimization_candidate ? 'Can Optimize' : 'Optimal';
            
            return `
            <tr>
                <td>
                    <div class="volume-name-cell">
                        <i class="fas fa-hdd"></i>
                        ${vol.pvc_name || vol.name || 'Unknown'}
                        ${vol.backup_enabled ? '<i class="fas fa-shield-alt" title="Backup enabled"></i>' : ''}
                    </div>
                </td>
                <td><span class="namespace-badge">${vol.namespace || 'default'}</span></td>
                <td>
                    <div class="size-usage-cell">
                        <strong>${sizeDisplay}</strong>
                        ${utilizationBar}
                    </div>
                </td>
                <td>
                    <div class="storage-class-cell">
                        ${vol.storage_class || 'standard'}
                        ${vol.performance_tier ? `<small>${vol.performance_tier}</small>` : ''}
                    </div>
                </td>
                <td class="cost-cell">$${(vol.monthly_cost || 0).toFixed(2)}</td>
                <td><span class="badge badge-${statusClass}">${statusText}</span></td>
            </tr>
            `;
        }).join('');
    }
    
    showMoreVolumes() {
        if (this.storageData && this.displayedVolumes < this.storageData.length) {
            this.displayedVolumes = this.storageData.length;
            const tbody = document.getElementById('storage-tbody');
            if (tbody) {
                tbody.innerHTML = this.renderStorageRows(this.storageData);
                // Update button
                const footer = tbody.closest('.storage-table-wrapper').querySelector('.table-footer');
                if (footer) {
                    footer.style.display = 'none';
                }
            }
        }
    }
    
    // New methods for namespace views
    renderNamespaceCards(namespaces) {
        return `
            <div class="namespace-cards-grid">
                ${namespaces.map(ns => {
                    const name = ns.name || ns;
                    const podCount = ns.pod_count || 0;
                    const deploymentCount = ns.deployment_count || Math.floor(podCount / 3); // Estimate
                    const serviceCount = ns.service_count || 0;
                    
                    // Determine type
                    let type = 'application';
                    let icon = 'fa-rocket';
                    let typeClass = 'app-card';
                    
                    if (['kube-system', 'kube-public', 'kube-node-lease', 'default'].includes(name)) {
                        type = 'system';
                        icon = 'fa-cogs';
                        typeClass = 'system-card';
                    } else if (name.includes('monitoring') || name.includes('grafana') || name.includes('kubecost')) {
                        type = 'monitoring';
                        icon = 'fa-chart-line';
                        typeClass = 'monitoring-card';
                    } else if (name.includes('cert') || name.includes('nginx') || name.includes('ingress')) {
                        type = 'infrastructure';
                        icon = 'fa-server';
                        typeClass = 'infra-card';
                    }
                    
                    return `
                        <div class="namespace-card-detailed ${typeClass}" onclick="showNamespaceDetails('${name}')">
                            <div class="card-header">
                                <i class="fas ${icon}"></i>
                                <span class="card-type">${type}</span>
                            </div>
                            <div class="card-body">
                                <h4>${name}</h4>
                                <div class="card-stats">
                                    <div class="stat-row">
                                        <span class="stat-label">Pods:</span>
                                        <span class="stat-value">${podCount}</span>
                                    </div>
                                    <div class="stat-row">
                                        <span class="stat-label">Deployments:</span>
                                        <span class="stat-value">${deploymentCount}</span>
                                    </div>
                                    <div class="stat-row">
                                        <span class="stat-label">Services:</span>
                                        <span class="stat-value">${serviceCount}</span>
                                    </div>
                                </div>
                                <div class="card-footer">
                                    <button class="btn-details">View Details →</button>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }
    
    renderNamespaceTable(namespaces) {
        return `
            <div class="namespace-table-wrapper">
                <table class="dashboard-table namespace-table">
                    <thead>
                        <tr>
                            <th>Namespace</th>
                            <th>Type</th>
                            <th>Pods</th>
                            <th>Deployments</th>
                            <th>Services</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${namespaces.map(ns => {
                            const name = ns.name || ns;
                            const podCount = ns.pod_count || 0;
                            const deploymentCount = ns.deployment_count || Math.floor(podCount / 3);
                            const serviceCount = ns.service_count || 0;
                            
                            let type = 'Application';
                            let typeClass = 'app';
                            if (['kube-system', 'kube-public', 'kube-node-lease', 'default'].includes(name)) {
                                type = 'System';
                                typeClass = 'system';
                            } else if (name.includes('monitoring') || name.includes('grafana') || name.includes('kubecost')) {
                                type = 'Monitoring';
                                typeClass = 'monitoring';
                            } else if (name.includes('cert') || name.includes('nginx')) {
                                type = 'Infrastructure';
                                typeClass = 'infra';
                            }
                            
                            const status = podCount > 0 ? 'Active' : 'Empty';
                            const statusClass = podCount > 0 ? 'healthy' : 'inactive';
                            
                            return `
                                <tr>
                                    <td><strong>${name}</strong></td>
                                    <td><span class="type-badge type-${typeClass}">${type}</span></td>
                                    <td>${podCount}</td>
                                    <td>${deploymentCount}</td>
                                    <td>${serviceCount}</td>
                                    <td><span class="badge badge-${statusClass}">${status}</span></td>
                                    <td>
                                        <button class="btn-action" onclick="showNamespaceDetails('${name}')">
                                            <i class="fas fa-eye"></i> Details
                                        </button>
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    renderNamespaceExplorer(namespaces) {
        // Modern tree-view explorer based on 2025 UX best practices
        const systemNs = ['kube-system', 'kube-public', 'kube-node-lease', 'default', 'gatekeeper-system'];
        const categories = {
            application: { namespaces: [], icon: 'fa-rocket', color: 'primary' },
            infrastructure: { namespaces: [], icon: 'fa-server', color: 'info' },
            monitoring: { namespaces: [], icon: 'fa-chart-line', color: 'warning' },
            system: { namespaces: [], icon: 'fa-cogs', color: 'secondary' }
        };
        
        // Categorize namespaces
        namespaces.forEach(ns => {
            const name = ns.name || ns;
            if (systemNs.includes(name)) {
                categories.system.namespaces.push(ns);
            } else if (name.includes('monitoring') || name.includes('grafana') || name.includes('kubecost')) {
                categories.monitoring.namespaces.push(ns);
            } else if (name.includes('cert') || name.includes('nginx') || name.includes('ingress') || name.includes('external') || name.includes('kapp')) {
                categories.infrastructure.namespaces.push(ns);
            } else {
                categories.application.namespaces.push(ns);
            }
        });
        
        return `
            <div class="namespace-explorer">
                <div class="explorer-header">
                    <h4><i class="fas fa-sitemap"></i> Namespace Explorer</h4>
                    <div class="explorer-stats">
                        <span class="stat-badge">${namespaces.length} Total</span>
                        <span class="stat-badge app">${categories.application.namespaces.length} Apps</span>
                        <span class="stat-badge infra">${categories.infrastructure.namespaces.length} Infra</span>
                        <span class="stat-badge monitoring">${categories.monitoring.namespaces.length} Monitor</span>
                        <span class="stat-badge system">${categories.system.namespaces.length} System</span>
                    </div>
                </div>
                
                <div class="explorer-tree">
                    ${Object.entries(categories).map(([categoryKey, category]) => {
                        if (category.namespaces.length === 0) return '';
                        
                        const categoryName = categoryKey.charAt(0).toUpperCase() + categoryKey.slice(1);
                        const isExpanded = this.expandedCategories ? this.expandedCategories.has(categoryKey) : true;
                        
                        return `
                            <div class="tree-category">
                                <div class="category-node" onclick="toggleCategory('${categoryKey}')">
                                    <i class="fas fa-chevron-${isExpanded ? 'down' : 'right'} expand-icon"></i>
                                    <i class="fas ${category.icon} category-icon ${category.color}"></i>
                                    <span class="category-label">${categoryName}</span>
                                    <span class="count-badge">${category.namespaces.length}</span>
                                </div>
                                
                                <div class="namespace-nodes ${!isExpanded ? 'collapsed' : ''}">
                                    ${category.namespaces.map(ns => {
                                        const name = ns.name || ns;
                                        const podCount = ns.pod_count || 0;
                                        const hasResources = podCount > 0;
                                        
                                        return `
                                            <div class="namespace-node ${hasResources ? 'has-resources' : 'empty'}" onclick="showNamespaceDetails('${name}')">
                                                <div class="node-content">
                                                    <i class="fas fa-folder${hasResources ? '-open' : ''} ns-icon"></i>
                                                    <span class="namespace-name">${name}</span>
                                                    <div class="node-stats">
                                                        <span class="pod-count">${podCount} pods</span>
                                                        ${hasResources ? '<i class="fas fa-circle active-indicator"></i>' : ''}
                                                    </div>
                                                </div>
                                                
                                                <div class="resource-preview">
                                                    ${podCount > 50 ? '<span class="resource-tag high">High Usage</span>' : ''}
                                                    ${podCount === 0 ? '<span class="resource-tag empty">Empty</span>' : ''}
                                                    ${podCount > 0 && podCount <= 50 ? '<span class="resource-tag normal">Normal</span>' : ''}
                                                </div>
                                            </div>
                                        `;
                                    }).join('')}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
                
                <div class="explorer-actions">
                    <button class="btn-explorer" onclick="expandAllCategories()">
                        <i class="fas fa-expand-arrows-alt"></i> Expand All
                    </button>
                    <button class="btn-explorer" onclick="collapseAllCategories()">
                        <i class="fas fa-compress-arrows-alt"></i> Collapse All
                    </button>
                    <button class="btn-explorer" onclick="showResourceSummary()">
                        <i class="fas fa-chart-bar"></i> Summary
                    </button>
                </div>
            </div>
        `;
    }
    
    setViewMode(mode) {
        this.viewMode = mode;
        const container = document.querySelector('.namespaces-container');
        if (container && this.namespacesData) {
            container.innerHTML = this.renderNamespaces(this.namespacesData);
        }
        
        // Update button states
        document.querySelectorAll('.btn-view').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeBtn = document.querySelector(`.btn-view[onclick*="${mode}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }
    
    async showNamespaceDetails(namespaceName) {
        const modal = document.getElementById('namespace-details-modal');
        const content = document.getElementById('namespace-details-content');
        
        if (!modal || !content) return;
        
        // Show modal with loading
        modal.style.display = 'block';
        content.innerHTML = '<div class="loading">Loading namespace details...</div>';
        
        // Get namespace data  
        const ns = this.namespacesData.find(n => (n.name || n) === namespaceName);
        const podCount = ns ? (ns.pod_count || 0) : 0;
        
        // Store selected namespace for other methods
        this.selectedNamespace = namespaceName;
        
        // Use existing data from the resources dashboard instead of API call
        const allData = this.allResourcesData;
        let detailsData = {};
        
        if (allData) {
            // Extract data from the main resources data
            const podsData = allData.pods || [];
            const deploymentsData = allData.deployments || [];
            const storageData = allData.storage || [];
            
            // Filter data for this namespace
            const namespacePods = podsData.filter(pod => pod.namespace === namespaceName);
            const namespaceDeployments = deploymentsData.filter(dep => dep.namespace === namespaceName);  
            const namespaceVolumes = storageData.filter(vol => vol.namespace === namespaceName);
            
            detailsData = {
                pods: namespacePods,
                deployments: namespaceDeployments,
                services: [], // No services data in our database
                volumes: namespaceVolumes
            };
        }
        
        // Render detailed view
        try {
            content.innerHTML = `
                <div class="namespace-details">
                    <div class="details-header">
                        <h2>${namespaceName}</h2>
                        <span class="namespace-type">${this.getNamespaceType(namespaceName)}</span>
                    </div>
                    
                    <div class="details-summary">
                        <div class="summary-card">
                            <i class="fas fa-cube"></i>
                            <div>
                                <span class="value">${podCount}</span>
                                <span class="label">Pods</span>
                            </div>
                        </div>
                        <div class="summary-card">
                            <i class="fas fa-layer-group"></i>
                            <div>
                                <span class="value">${detailsData.deployments?.length || 0}</span>
                                <span class="label">Deployments</span>
                            </div>
                        </div>
                        <div class="summary-card">
                            <i class="fas fa-network-wired"></i>
                            <div>
                                <span class="value">${detailsData.services?.length || 0}</span>
                                <span class="label">Services</span>
                            </div>
                        </div>
                        <div class="summary-card">
                            <i class="fas fa-hdd"></i>
                            <div>
                                <span class="value">${detailsData.volumes?.length || 0}</span>
                                <span class="label">Volumes</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="details-tabs">
                        <button class="tab-btn active" onclick="showNamespaceTab('pods')">Pods</button>
                        <button class="tab-btn" onclick="showNamespaceTab('deployments')">Deployments</button>
                        <button class="tab-btn" onclick="showNamespaceTab('services')">Services</button>
                        <button class="tab-btn" onclick="showNamespaceTab('resources')">Resource Usage</button>
                    </div>
                    
                    <div class="tab-content" id="pods-tab">
                        ${this.renderPodsTab(detailsData.pods || [])}
                    </div>
                    
                    <div class="tab-content" id="deployments-tab" style="display:none;">
                        ${this.renderDeploymentsTab(detailsData.deployments || [])}
                    </div>
                    
                    <div class="tab-content" id="services-tab" style="display:none;">
                        ${this.renderServicesTab(detailsData.services || [])}
                    </div>
                    
                    <div class="tab-content" id="resources-tab" style="display:none;">
                        ${this.renderResourcesTab(detailsData.pods || [])}
                    </div>
                </div>
            `;
        } catch (error) {
            content.innerHTML = `
                <div class="namespace-details">
                    <div class="details-header">
                        <h2>${namespaceName}</h2>
                    </div>
                    <div class="error-message">
                        <i class="fas fa-info-circle"></i>
                        Detailed namespace information is not available at the moment.
                        <br><br>
                        <strong>Quick Stats:</strong>
                        <ul>
                            <li>Pods: ${podCount}</li>
                            <li>Type: ${this.getNamespaceType(namespaceName)}</li>
                        </ul>
                    </div>
                </div>
            `;
        }
    }
    
    getNamespaceType(name) {
        if (['kube-system', 'kube-public', 'kube-node-lease', 'default'].includes(name)) {
            return 'System Namespace';
        } else if (name.includes('monitoring') || name.includes('grafana') || name.includes('kubecost')) {
            return 'Monitoring';
        } else if (name.includes('cert') || name.includes('nginx') || name.includes('ingress')) {
            return 'Infrastructure';
        }
        return 'Application';
    }
    
    renderPodsTab(pods) {
        if (!pods || pods.length === 0) {
            return '<div class="no-data">No pods found in this namespace</div>';
        }
        
        return `
            <div class="pods-details">
                <div class="pods-summary">
                    <h5>${pods.length} Pods in this namespace</h5>
                    <div class="status-breakdown">
                        <span class="stat running">Running: ${pods.filter(p => p.status === 'Running').length}</span>
                        <span class="stat pending">Pending: ${pods.filter(p => p.status === 'Pending').length}</span>
                        <span class="stat failed">Failed: ${pods.filter(p => p.status === 'Failed').length}</span>
                    </div>
                </div>
                
                <div class="pods-table-wrapper">
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>Pod Name</th>
                                <th>Status</th>
                                <th>Node</th>
                                <th>CPU Request</th>
                                <th>Memory Request</th>
                                <th>Restarts</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${pods.slice(0, 20).map(pod => `
                                <tr>
                                    <td class="pod-name">${pod.name || 'Unknown'}</td>
                                    <td><span class="status-badge ${pod.status?.toLowerCase() || 'unknown'}">${pod.status || 'Unknown'}</span></td>
                                    <td>${pod.node || 'Unknown'}</td>
                                    <td>${pod.cpu_request || '0'}</td>
                                    <td>${pod.memory_request || '0'}</td>
                                    <td>${pod.restarts || '0'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                    ${pods.length > 20 ? `<div class="table-note">Showing first 20 of ${pods.length} pods</div>` : ''}
                </div>
            </div>
        `;
    }
    
    renderDeploymentsTab(deployments) {
        if (!deployments || deployments.length === 0) {
            return '<div class="no-data">No deployments found in this namespace</div>';
        }
        
        // Handle deployments structure
        let deploymentsList = deployments;
        if (deployments.items) {
            deploymentsList = deployments.items;
        }
        
        return `
            <div class="deployments-details">
                <div class="deployments-summary">
                    <h5>${deploymentsList.length} Deployments in this namespace</h5>
                    <div class="replica-summary">
                        <span class="stat">Total Replicas: ${deploymentsList.reduce((sum, d) => sum + (parseInt(d.replicas) || 0), 0)}</span>
                        <span class="stat">Ready: ${deploymentsList.reduce((sum, d) => sum + (parseInt(d.ready) || 0), 0)}</span>
                    </div>
                </div>
                
                <div class="deployments-grid">
                    ${deploymentsList.map(deployment => {
                        const ready = parseInt(deployment.ready) || 0;
                        const desired = parseInt(deployment.replicas) || 0;
                        const healthPercent = desired > 0 ? (ready / desired * 100) : 0;
                        const healthClass = healthPercent === 100 ? 'healthy' : healthPercent > 0 ? 'warning' : 'critical';
                        
                        return `
                            <div class="deployment-card">
                                <div class="deployment-header">
                                    <h6>${deployment.name || 'Unknown'}</h6>
                                    <span class="health-indicator ${healthClass}">${healthPercent.toFixed(0)}%</span>
                                </div>
                                <div class="deployment-stats">
                                    <div class="stat-row">
                                        <span class="label">Replicas:</span>
                                        <span class="value">${ready}/${desired}</span>
                                    </div>
                                    <div class="stat-row">
                                        <span class="label">Image:</span>
                                        <span class="value mono">${deployment.image ? deployment.image.split('/').pop() : 'Unknown'}</span>
                                    </div>
                                    <div class="stat-row">
                                        <span class="label">Strategy:</span>
                                        <span class="value">${deployment.strategy || 'RollingUpdate'}</span>
                                    </div>
                                </div>
                                <div class="replica-bar">
                                    <div class="replica-fill" style="width: ${healthPercent}%"></div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }
    
    renderServicesTab(services) {
        return `
            <div class="services-details">
                <div class="info-message">
                    <i class="fas fa-info-circle"></i>
                    <p><strong>Services data not available</strong></p>
                    <p>The cluster analysis doesn't include Kubernetes services data at this time. 
                    This tab would typically show LoadBalancers, ClusterIPs, and NodePorts for this namespace.</p>
                </div>
                
                <div class="services-placeholder">
                    <h6>Typical Service Types:</h6>
                    <ul>
                        <li><strong>ClusterIP:</strong> Internal cluster communication</li>
                        <li><strong>LoadBalancer:</strong> External traffic (costs ~$18/month)</li>
                        <li><strong>NodePort:</strong> Node-level access</li>
                        <li><strong>Ingress:</strong> HTTP/HTTPS routing</li>
                    </ul>
                </div>
            </div>
        `;
    }
    
    renderResourcesTab(pods) {
        if (!pods || pods.length === 0) {
            return '<div class="no-data">No resource data available for this namespace</div>';
        }
        
        // Calculate actual resource requests from pod data
        let totalCpuRequests = 0;
        let totalMemoryRequests = 0;
        let totalCpuLimits = 0;
        let totalMemoryLimits = 0;
        
        pods.forEach(pod => {
            // Parse CPU requests (in millicores)
            const cpuRequest = pod.cpu_request || '0';
            if (cpuRequest.endsWith('m')) {
                totalCpuRequests += parseInt(cpuRequest.slice(0, -1));
            } else {
                totalCpuRequests += parseFloat(cpuRequest) * 1000;
            }
            
            // Parse memory requests (in Mi)
            const memRequest = pod.memory_request || '0';
            if (memRequest.endsWith('Mi')) {
                totalMemoryRequests += parseInt(memRequest.slice(0, -2));
            }
            
            // Parse CPU limits
            const cpuLimit = pod.cpu_limit || '0';
            if (cpuLimit.endsWith('m')) {
                totalCpuLimits += parseInt(cpuLimit.slice(0, -1));
            } else {
                totalCpuLimits += parseFloat(cpuLimit) * 1000;
            }
            
            // Parse memory limits
            const memLimit = pod.memory_limit || '0';
            if (memLimit.endsWith('Mi')) {
                totalMemoryLimits += parseInt(memLimit.slice(0, -2));
            }
        });
        
        const storageVolumes = this.allResourcesData?.storage?.filter(v => v.namespace === this.selectedNamespace) || [];
        
        return `
            <div class="resources-usage">
                <div class="resource-summary-cards">
                    <div class="resource-card">
                        <i class="fas fa-microchip"></i>
                        <div>
                            <span class="resource-label">CPU Requests</span>
                            <span class="resource-value">${(totalCpuRequests / 1000).toFixed(2)} cores</span>
                        </div>
                    </div>
                    <div class="resource-card">
                        <i class="fas fa-microchip"></i>
                        <div>
                            <span class="resource-label">CPU Limits</span>
                            <span class="resource-value">${(totalCpuLimits / 1000).toFixed(2)} cores</span>
                        </div>
                    </div>
                    <div class="resource-card">
                        <i class="fas fa-memory"></i>
                        <div>
                            <span class="resource-label">Memory Requests</span>
                            <span class="resource-value">${(totalMemoryRequests / 1024).toFixed(2)} GB</span>
                        </div>
                    </div>
                    <div class="resource-card">
                        <i class="fas fa-memory"></i>
                        <div>
                            <span class="resource-label">Memory Limits</span>
                            <span class="resource-value">${(totalMemoryLimits / 1024).toFixed(2)} GB</span>
                        </div>
                    </div>
                    <div class="resource-card">
                        <i class="fas fa-hdd"></i>
                        <div>
                            <span class="resource-label">Storage Volumes</span>
                            <span class="resource-value">${storageVolumes.length}</span>
                        </div>
                    </div>
                </div>
                
                ${storageVolumes.length > 0 ? `
                <div class="storage-details">
                    <h6>Storage Volumes:</h6>
                    <div class="volume-list">
                        ${storageVolumes.map(vol => `
                            <div class="volume-item">
                                <span class="volume-name">${vol.pvc_name || vol.name}</span>
                                <span class="volume-size">${vol.size?.requested_gb || 'Unknown'} GB</span>
                            </div>
                        `).join('')}
                    </div>
                </div>` : ''}
            </div>
        `;
    }
    
    showTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.style.display = 'none';
        });
        // Show selected tab
        const selectedTab = document.getElementById(`${tabName}-tab`);
        if (selectedTab) {
            selectedTab.style.display = 'block';
        }
        // Update button states
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeBtn = document.querySelector(`.tab-btn[onclick*="${tabName}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }
    
    closeNamespaceDetails() {
        const modal = document.getElementById('namespace-details-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    renderNetworkCards(network) {
        if (!network) {
            return '<div class="no-data">No network resources data available</div>';
        }
        
        return `
            <div class="network-card">
                <h4><i class="fas fa-globe"></i> Public IPs</h4>
                <div class="network-stats">
                    <div class="stat-item">
                        <span>Count:</span>
                        <strong>${network.public_ip_count || 0}</strong>
                    </div>
                    <div class="stat-item">
                        <span>Monthly Cost:</span>
                        <strong>$${(network.public_ip_cost || 0).toFixed(2)}</strong>
                    </div>
                    ${network.public_ips && network.public_ips.length > 0 ? `
                    <div class="ip-list">
                        ${network.public_ips.slice(0, 3).map(ip => 
                            `<span class="ip-badge">${ip.name || ip}</span>`
                        ).join('')}
                        ${network.public_ips.length > 3 ? 
                            `<span class="more-badge">+${network.public_ips.length - 3} more</span>` : ''}
                    </div>` : ''}
                </div>
            </div>
            
            <div class="network-card">
                <h4><i class="fas fa-balance-scale"></i> Load Balancers</h4>
                <div class="network-stats">
                    <div class="stat-item">
                        <span>Count:</span>
                        <strong>${network.load_balancer_count || 0}</strong>
                    </div>
                    <div class="stat-item">
                        <span>Monthly Cost:</span>
                        <strong>$${(network.load_balancer_cost || 0).toFixed(2)}</strong>
                    </div>
                    ${network.load_balancers && network.load_balancers.length > 0 ? `
                    <div class="lb-list">
                        ${network.load_balancers.slice(0, 2).map(lb => 
                            `<div class="lb-item">
                                <i class="fas fa-server"></i> ${lb.name || 'LoadBalancer'}
                            </div>`
                        ).join('')}
                    </div>` : ''}
                </div>
            </div>
            
            <div class="network-card">
                <h4><i class="fas fa-exchange-alt"></i> Network Traffic</h4>
                <div class="network-stats">
                    <div class="stat-item">
                        <span>Egress Cost:</span>
                        <strong>$${(network.egress_cost || 0).toFixed(2)}</strong>
                    </div>
                    <div class="stat-item">
                        <span>Ingress Cost:</span>
                        <strong>$${(network.ingress_cost || 0).toFixed(2)}</strong>
                    </div>
                    <div class="stat-item">
                        <span>Total Network Cost:</span>
                        <strong class="text-primary">$${(network.total_network_cost || 0).toFixed(2)}</strong>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderAnomalies(anomalies) {
        if (!anomalies || !anomalies.anomalies || anomalies.anomalies.length === 0) {
            return '<div class="no-data">No anomalies detected</div>';
        }
        
        return `
            <div class="anomaly-summary">
                <span class="anomaly-stat">
                    <i class="fas fa-exclamation-circle"></i>
                    Total: <strong>${anomalies.total_anomalies}</strong>
                </span>
                <span class="anomaly-stat">
                    Average Severity: <strong class="${anomalies.average_severity > 7 ? 'text-danger' : anomalies.average_severity > 4 ? 'text-warning' : 'text-success'}">
                        ${(anomalies.average_severity || 0).toFixed(1)}/10
                    </strong>
                </span>
            </div>
            <div class="anomaly-list">
                ${anomalies.anomalies.slice(0, 5).map(anomaly => `
                    <div class="anomaly-item severity-${anomaly.severity > 7 ? 'high' : anomaly.severity > 4 ? 'medium' : 'low'}">
                        <div class="anomaly-header">
                            <span class="anomaly-type">${anomaly.type || 'Unknown'}</span>
                            <span class="anomaly-severity">Severity: ${anomaly.severity}/10</span>
                        </div>
                        <div class="anomaly-description">${anomaly.description || 'No description available'}</div>
                        ${anomaly.recommendation ? 
                            `<div class="anomaly-recommendation">
                                <i class="fas fa-lightbulb"></i> ${anomaly.recommendation}
                            </div>` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    getEfficiencyRating(score) {
        if (score >= 90) return 'Excellent';
        if (score >= 75) return 'Good';
        if (score >= 60) return 'Fair';
        if (score >= 40) return 'Needs Improvement';
        return 'Poor';
    }
    
    initializeResourceCharts_REMOVED() {
        if (!window.Chart || !this.data) return;
        
        // Get CSS variable values
        const styles = getComputedStyle(document.documentElement);
        const primaryColor = styles.getPropertyValue('--primary-color').trim() || '#4A90E2';
        const successColor = styles.getPropertyValue('--success-color').trim() || '#7FB069';
        const warningColor = styles.getPropertyValue('--warning-color').trim() || '#FFA500';
        const dangerColor = styles.getPropertyValue('--danger-color').trim() || '#FF6B6B';
        const infoColor = styles.getPropertyValue('--info-color').trim() || '#5DADE2';
        const textPrimary = styles.getPropertyValue('--text-primary').trim() || '#333';
        const textSecondary = styles.getPropertyValue('--text-secondary').trim() || '#666';
        const borderColor = styles.getPropertyValue('--border-color').trim() || '#e0e0e0';
        
        const costs = this.data.costs || {};
        const metrics = this.data.metrics || {};
        
        // Create cost distribution chart
        const costContainer = document.getElementById('cost-distribution-chart');
        if (costContainer) {
            const canvas = document.createElement('canvas');
            costContainer.appendChild(canvas);
            
            const costData = [
                costs.compute_cost || 0,
                costs.storage_cost || 0,
                costs.networking_cost || 0,
                Math.max(0, (costs.total_cost || 0) - (costs.compute_cost || 0) - (costs.storage_cost || 0) - (costs.networking_cost || 0))
            ];
            
            new Chart(canvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Compute', 'Storage', 'Networking', 'Other'],
                    datasets: [{
                        data: costData,
                        backgroundColor: [
                            primaryColor + 'CC',
                            successColor + 'CC',
                            warningColor + 'CC',
                            infoColor + 'CC'
                        ],
                        borderColor: [
                            primaryColor,
                            successColor,
                            warningColor,
                            infoColor
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: textPrimary,
                                padding: 15,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    return context.label + ': $' + value.toFixed(2) + ' (' + percentage + '%)';
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Create utilization comparison chart
        const utilContainer = document.getElementById('utilization-chart');
        if (utilContainer) {
            const canvas = document.createElement('canvas');
            utilContainer.appendChild(canvas);
            
            new Chart(canvas.getContext('2d'), {
                type: 'radar',
                data: {
                    labels: ['CPU Average', 'CPU Peak', 'Memory Average', 'Memory Peak'],
                    datasets: [{
                        label: 'Current Utilization',
                        data: [
                            metrics.avg_cpu_utilization || 0,
                            metrics.max_cpu_utilization || 0,
                            metrics.avg_memory_utilization || 0,
                            metrics.max_memory_utilization || 0
                        ],
                        backgroundColor: primaryColor + '33',
                        borderColor: primaryColor,
                        borderWidth: 2,
                        pointBackgroundColor: primaryColor,
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: primaryColor
                    }, {
                        label: 'Optimal Range',
                        data: [70, 85, 70, 85], // Target utilization
                        backgroundColor: successColor + '22',
                        borderColor: successColor,
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointBackgroundColor: successColor,
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: successColor
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: textPrimary,
                                padding: 10,
                                font: {
                                    size: 11
                                }
                            }
                        }
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                stepSize: 20,
                                color: textSecondary
                            },
                            grid: {
                                color: borderColor
                            },
                            pointLabels: {
                                color: textPrimary,
                                font: {
                                    size: 11
                                }
                            }
                        }
                    }
                }
            });
        }
    }
}

// Global Kubernetes Dashboard Manager
class KubernetesDashboardManager {
    constructor() {
        this.pods = null;
        this.workloads = null;
        this.resources = null;
    }
    
    initPods(containerId, clusterId, subscriptionId) {
        this.pods = new PodsDashboard(containerId, clusterId, subscriptionId);
        return this.pods.init();
    }
    
    initWorkloads(containerId, clusterId, subscriptionId) {
        this.workloads = new WorkloadsDashboard(containerId, clusterId, subscriptionId);
        return this.workloads.init();
    }
    
    initResources(containerId, clusterId, subscriptionId) {
        this.resources = new ResourcesDashboard(containerId, clusterId, subscriptionId);
        return this.resources.init();
    }
}

// Create global instance
window.kubernetesDashboard = new KubernetesDashboardManager();

// Global initialization functions for dashboard.js
window.refreshPodsData = function() {
    if (!window.clusterInfo || !window.clusterInfo.id || !window.clusterInfo.subscription_id) {
        console.error('Missing cluster information for pods data');
        return;
    }
    
    kubernetesDashboard.initPods(
        'pod-overview-content',
        window.clusterInfo.id,
        window.clusterInfo.subscription_id
    );
};

window.refreshWorkloadsData = function() {
    if (!window.clusterInfo || !window.clusterInfo.id || !window.clusterInfo.subscription_id) {
        console.error('Missing cluster information for workloads data');
        return;
    }
    
    kubernetesDashboard.initWorkloads(
        'workload-cards-container',
        window.clusterInfo.id,
        window.clusterInfo.subscription_id
    );
};

window.refreshResourcesData = function() {
    if (!window.clusterInfo || !window.clusterInfo.id || !window.clusterInfo.subscription_id) {
        console.error('Missing cluster information for resources data');
        return;
    }
    
    kubernetesDashboard.initResources(
        'resource-charts-container',
        window.clusterInfo.id,
        window.clusterInfo.subscription_id
    );
};

// Global functions for namespace interactions
let currentResourcesDashboard = null;

function showNamespaceDetails(namespaceName) {
    if (currentResourcesDashboard) {
        currentResourcesDashboard.showNamespaceDetails(namespaceName);
    } else {
        console.error('Resources dashboard not initialized');
    }
}

function setNamespaceViewMode(mode) {
    if (currentResourcesDashboard) {
        currentResourcesDashboard.setViewMode(mode);
    } else {
        console.error('Resources dashboard not initialized');
    }
}

function closeNamespaceDetails() {
    if (currentResourcesDashboard) {
        currentResourcesDashboard.closeNamespaceDetails();
    } else {
        const modal = document.getElementById('namespace-details-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
}

function showNamespaceTab(tabName) {
    if (currentResourcesDashboard) {
        currentResourcesDashboard.showTab(tabName);
    } else {
        console.error('Resources dashboard not initialized');
    }
}

function showMoreVolumes() {
    if (currentResourcesDashboard) {
        currentResourcesDashboard.showMoreVolumes();
    } else {
        console.error('Resources dashboard not initialized');
    }
}

// Additional functions for the explorer view
function toggleCategory(categoryKey) {
    if (currentResourcesDashboard) {
        if (currentResourcesDashboard.expandedCategories.has(categoryKey)) {
            currentResourcesDashboard.expandedCategories.delete(categoryKey);
        } else {
            currentResourcesDashboard.expandedCategories.add(categoryKey);
        }
        // Re-render the explorer view
        const container = document.querySelector('.namespaces-container');
        if (container && currentResourcesDashboard.namespacesData) {
            container.innerHTML = currentResourcesDashboard.renderNamespaces(currentResourcesDashboard.namespacesData);
        }
    }
}

function expandAllCategories() {
    if (currentResourcesDashboard) {
        currentResourcesDashboard.expandedCategories.add('application');
        currentResourcesDashboard.expandedCategories.add('infrastructure');
        currentResourcesDashboard.expandedCategories.add('monitoring');
        currentResourcesDashboard.expandedCategories.add('system');
        // Re-render
        const container = document.querySelector('.namespaces-container');
        if (container && currentResourcesDashboard.namespacesData) {
            container.innerHTML = currentResourcesDashboard.renderNamespaces(currentResourcesDashboard.namespacesData);
        }
    }
}

function collapseAllCategories() {
    if (currentResourcesDashboard) {
        currentResourcesDashboard.expandedCategories.clear();
        // Re-render
        const container = document.querySelector('.namespaces-container');
        if (container && currentResourcesDashboard.namespacesData) {
            container.innerHTML = currentResourcesDashboard.renderNamespaces(currentResourcesDashboard.namespacesData);
        }
    }
}

function showResourceSummary() {
    if (currentResourcesDashboard && currentResourcesDashboard.namespacesData) {
        const totalPods = currentResourcesDashboard.namespacesData.reduce((sum, ns) => sum + (ns.pod_count || 0), 0);
        const activeNamespaces = currentResourcesDashboard.namespacesData.filter(ns => (ns.pod_count || 0) > 0).length;
        
        alert(`Cluster Resource Summary:
        
Total Namespaces: ${currentResourcesDashboard.namespacesData.length}
Active Namespaces: ${activeNamespaces}
Total Pods: ${totalPods}
Empty Namespaces: ${currentResourcesDashboard.namespacesData.length - activeNamespaces}

Highest Usage: ${currentResourcesDashboard.namespacesData
    .sort((a, b) => (b.pod_count || 0) - (a.pod_count || 0))[0]?.name || 'None'} 
    (${currentResourcesDashboard.namespacesData[0]?.pod_count || 0} pods)`);
    }
}