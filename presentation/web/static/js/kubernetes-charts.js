/**
 * Kubernetes Charts Module
 * =========================
 * Chart components for Kubernetes dashboard visualizations.
 * Follows .clauderc principles: fail fast, no silent failures, explicit parameters.
 * 
 * Developer: Srinivas Kondepudi
 * Organization: Nivaya Technologies & kubeopt
 * Project: AKS Cost Optimizer
 */

class KubernetesCharts {
    constructor() {
        this.cpuChart = null;
        this.memoryChart = null;
        this.chartInstances = {};
    }
    
    /**
     * Create CPU usage chart
     */
    createCPUChart(containerId, data) {
        if (!containerId) {
            throw new Error('Container ID is required for CPU chart');
        }
        
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container ${containerId} not found`);
        }
        
        // Create canvas if it doesn't exist
        let canvas = container.querySelector('canvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.id = `${containerId}-canvas`;
            container.appendChild(canvas);
        }
        
        // Destroy existing chart
        if (this.chartInstances[containerId]) {
            this.chartInstances[containerId].destroy();
        }
        
        const ctx = canvas.getContext('2d');
        
        // Prepare time series data
        const labels = this.generateTimeLabels(24); // Last 24 data points
        const cpuData = data || new Array(24).fill(null);
        
        this.chartInstances[containerId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'CPU Usage (cores)',
                    data: cpuData,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'CPU Usage',
                        font: {
                            size: 14,
                            weight: 'normal'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 6
                        }
                    },
                    y: {
                        display: true,
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'CPU (cores)'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                }
            }
        });
        
        return this.chartInstances[containerId];
    }
    
    /**
     * Create Memory usage chart
     */
    createMemoryChart(containerId, data) {
        if (!containerId) {
            throw new Error('Container ID is required for Memory chart');
        }
        
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container ${containerId} not found`);
        }
        
        // Create canvas if it doesn't exist
        let canvas = container.querySelector('canvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.id = `${containerId}-canvas`;
            container.appendChild(canvas);
        }
        
        // Destroy existing chart
        if (this.chartInstances[containerId]) {
            this.chartInstances[containerId].destroy();
        }
        
        const ctx = canvas.getContext('2d');
        
        // Prepare time series data
        const labels = this.generateTimeLabels(24);
        const memoryData = data || new Array(24).fill(null);
        
        this.chartInstances[containerId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Memory Usage (Mi)',
                    data: memoryData,
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Memory Usage',
                        font: {
                            size: 14,
                            weight: 'normal'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 6
                        }
                    },
                    y: {
                        display: true,
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Memory (Mi)'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                }
            }
        });
        
        return this.chartInstances[containerId];
    }
    
    /**
     * Create resource utilization pie chart
     */
    createResourcePieChart(containerId, usedValue, totalValue, resourceType) {
        if (!containerId) {
            throw new Error('Container ID is required for pie chart');
        }
        
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container ${containerId} not found`);
        }
        
        // Create canvas if it doesn't exist
        let canvas = container.querySelector('canvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.id = `${containerId}-canvas`;
            container.appendChild(canvas);
        }
        
        // Destroy existing chart
        if (this.chartInstances[containerId]) {
            this.chartInstances[containerId].destroy();
        }
        
        const ctx = canvas.getContext('2d');
        const percentage = ((usedValue / totalValue) * 100).toFixed(1);
        
        this.chartInstances[containerId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Used', 'Available'],
                datasets: [{
                    data: [usedValue, totalValue - usedValue],
                    backgroundColor: [
                        resourceType === 'cpu' ? 'rgb(75, 192, 192)' : 'rgb(54, 162, 235)',
                        'rgba(200, 200, 200, 0.2)'
                    ],
                    borderWidth: 0
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
                                const label = context.label || '';
                                const value = context.parsed;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
        
        // Add center text
        const centerText = document.createElement('div');
        centerText.className = 'chart-center-text';
        centerText.innerHTML = `<span class="percentage">${percentage}%</span><br><span class="label">${resourceType.toUpperCase()}</span>`;
        container.appendChild(centerText);
        
        return this.chartInstances[containerId];
    }
    
    /**
     * Generate time labels for charts
     */
    generateTimeLabels(count) {
        const labels = [];
        const now = new Date();
        
        for (let i = count - 1; i >= 0; i--) {
            const time = new Date(now - i * 5 * 60 * 1000); // 5 minute intervals
            labels.push(time.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: false 
            }));
        }
        
        return labels;
    }
    
    /**
     * Generate empty data array (no data available)
     */
    generateEmptyData(count) {
        return new Array(count).fill(null);
    }
    
    /**
     * Update all charts with new data
     */
    updateCharts(cpuData, memoryData) {
        // Update CPU chart if exists
        if (this.chartInstances['cpu-chart']) {
            this.chartInstances['cpu-chart'].data.datasets[0].data = cpuData;
            this.chartInstances['cpu-chart'].update();
        }
        
        // Update Memory chart if exists
        if (this.chartInstances['memory-chart']) {
            this.chartInstances['memory-chart'].data.datasets[0].data = memoryData;
            this.chartInstances['memory-chart'].update();
        }
    }
    
    /**
     * Destroy all chart instances
     */
    destroyAll() {
        Object.keys(this.chartInstances).forEach(key => {
            if (this.chartInstances[key]) {
                this.chartInstances[key].destroy();
            }
        });
        this.chartInstances = {};
    }
}

// Create global instance
window.kubernetesCharts = new KubernetesCharts();