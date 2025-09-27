/**
 * Real-Time AKS Cost Intelligence Platform - Dashboard JavaScript
 * Handles all client-side functionality and real-time data visualization
 */

class AKSDashboard {
    constructor() {
        this.charts = {};
        this.websocket = null;
        this.currentAnalysis = null;
        this.isAnalyzing = false;
        
        // API Configuration - Auto-detect or use localhost:8000
        this.apiBaseUrl = this.detectApiBaseUrl();
        
        this.init();
    }
    
    detectApiBaseUrl() {
        // If we're served from the same origin as the backend, use relative URLs
        if (window.location.hostname === 'localhost' && window.location.port === '8000') {
            return ''; // Use relative URLs (same origin)
        }
        // Otherwise, assume backend is on localhost:8000
        return 'http://localhost:8000';
    }
    
    init() {
        
        
        
        // Test backend connectivity
        this.testBackendConnection();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize connection status
        this.updateConnectionStatus('connecting', 'Connecting...');
        
        // Connect WebSocket
        this.connectWebSocket();
    }
    
    async testBackendConnection() {
        try {
            const healthUrl = this.apiBaseUrl ? `${this.apiBaseUrl}/api/health` : '/api/health';
            const response = await fetch(healthUrl);
            if (response.ok) {
                const data = await response.json();
                
                this.updateConnectionStatus('online', 'Connected');
                
                // Check if frontend files are available on backend
                if (data.frontend_files_available) {
                    const { html, js } = data.frontend_files_available;
                    if (!html || !js) {
                        logWarn('⚠️ Some frontend files missing on backend');
                    }
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Backend connection failed:', error);
            this.updateConnectionStatus('error', 'Backend Offline');
            this.showError(`Cannot connect to backend at ${this.apiBaseUrl || 'same origin'}. Please ensure the backend server is running.`);
        }
    }
    
    setupEventListeners() {
        // Analysis form submission
        const analysisForm = document.getElementById('analysis-form');
        if (analysisForm) {
            analysisForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.startAnalysis();
            });
        }
        
        // Real-time data refresh
        setInterval(() => {
            if (this.currentAnalysis && !this.isAnalyzing) {
                this.refreshRealTimeData();
            }
        }, 60000); // Refresh every minute
    }
    
    updateConnectionStatus(status, text) {
        const indicator = document.getElementById('connection-status');
        const textElement = document.getElementById('connection-text');
        
        if (indicator) {
            indicator.className = `status-indicator status-${status}`;
        }
        
        if (textElement) {
            textElement.textContent = text;
        }
    }
    
    connectWebSocket() {
        try {
            let wsUrl;
            
            if (this.apiBaseUrl === '') {
                // Same origin - use current host
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                wsUrl = `${protocol}//${window.location.host}/ws/analytics/default`;
            } else {
                // Different origin
                const protocol = this.apiBaseUrl.startsWith('https') ? 'wss:' : 'ws:';
                const baseUrl = this.apiBaseUrl.replace(/^https?:\/\//, '');
                wsUrl = `${protocol}//${baseUrl}/ws/analytics/default`;
            }
            
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                
                this.updateWebSocketStatus('online', 'Connected');
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateWebSocketStatus('error', 'Connection Error');
            };
            
            this.websocket.onclose = () => {
                
                this.updateWebSocketStatus('warning', 'Disconnected');
                
                // Attempt to reconnect after 5 seconds
                setTimeout(() => {
                    this.connectWebSocket();
                }, 5000);
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateWebSocketStatus('error', 'Failed to Connect');
        }
    }
    
    updateWebSocketStatus(status, text) {
        const indicator = document.getElementById('ws-indicator');
        const textElement = document.getElementById('ws-text');
        
        if (indicator) {
            indicator.className = `status-indicator status-${status}`;
        }
        
        if (textElement) {
            textElement.textContent = text;
        }
    }
    
    handleWebSocketMessage(data) {
        
        
        if (data.type === 'metrics_update') {
            // Handle real-time metrics updates
            if (this.currentAnalysis) {
                this.refreshRealTimeData();
            }
        }
    }
    
    async startAnalysis() {
        const subscriptionId = document.getElementById('subscription-id').value.trim();
        const resourceGroup = document.getElementById('resource-group').value.trim();
        const clusterName = document.getElementById('cluster-name').value.trim();
        
        if (!subscriptionId || !resourceGroup || !clusterName) {
            this.showError('Please fill in all required fields');
            return;
        }
        
        this.isAnalyzing = true;
        this.showAnalysisProgress();
        this.hideError();
        
        try {
            // Update UI state
            this.updateAnalyzeButton(true);
            
            // Simulate progress updates
            this.simulateProgress();
            
            // Make API call to analyze cluster
            const analyzeUrl = this.apiBaseUrl ? `${this.apiBaseUrl}/api/analyze` : '/api/analyze';
            const response = await fetch(analyzeUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    subscription_id: subscriptionId,
                    resource_group: resourceGroup,
                    cluster_name: clusterName,
                    analysis_period: 30
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.currentAnalysis = result;
                this.displayAnalysisResults(result);
                this.updateConnectionStatus('online', 'Analysis Complete');
            } else {
                throw new Error('Analysis failed');
            }
            
        } catch (error) {
            console.error('Analysis error:', error);
            this.showError(`Analysis failed: ${error.message}`);
            this.updateConnectionStatus('error', 'Analysis Failed');
        } finally {
            this.isAnalyzing = false;
            this.hideAnalysisProgress();
            this.updateAnalyzeButton(false);
        }
    }
    
    simulateProgress() {
        const progressSteps = [
            { progress: 15, status: 'Connecting to Azure APIs...' },
            { progress: 30, status: 'Retrieving cost data...' },
            { progress: 45, status: 'Collecting cluster metrics...' },
            { progress: 60, status: 'Analyzing resource utilization...' },
            { progress: 75, status: 'Generating recommendations...' },
            { progress: 90, status: 'Creating implementation plan...' },
            { progress: 100, status: 'Analysis complete!' }
        ];
        
        let currentStep = 0;
        
        const updateProgress = () => {
            if (currentStep < progressSteps.length && this.isAnalyzing) {
                const step = progressSteps[currentStep];
                this.updateProgress(step.progress, step.status);
                currentStep++;
                
                setTimeout(updateProgress, 2000);
            }
        };
        
        updateProgress();
    }
    
    updateProgress(percentage, status) {
        const progressBar = document.getElementById('main-progress');
        const progressText = document.getElementById('progress-text');
        const progressStatus = document.getElementById('progress-status');
        
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
        
        if (progressText) {
            progressText.textContent = `${percentage}% Complete`;
        }
        
        if (progressStatus) {
            progressStatus.textContent = status;
        }
    }
    
    updateAnalyzeButton(analyzing) {
        const button = document.getElementById('analyze-button');
        const icon = document.getElementById('analyze-icon');
        const text = document.getElementById('analyze-text');
        
        if (button) {
            button.disabled = analyzing;
        }
        
        if (icon) {
            icon.className = analyzing ? 'fas fa-sync fa-spin mr-2' : 'fas fa-rocket mr-2';
        }
        
        if (text) {
            text.textContent = analyzing ? 'Analyzing...' : 'Analyze Cluster';
        }
    }
    
    showAnalysisProgress() {
        const progressDiv = document.getElementById('analysis-progress');
        if (progressDiv) {
            progressDiv.style.display = 'block';
            progressDiv.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    hideAnalysisProgress() {
        const progressDiv = document.getElementById('analysis-progress');
        if (progressDiv) {
            progressDiv.style.display = 'none';
        }
    }
    
    displayAnalysisResults(result) {
        
        
        // Show results dashboard
        const resultsDiv = document.getElementById('results-dashboard');
        if (resultsDiv) {
            resultsDiv.style.display = 'block';
            resultsDiv.scrollIntoView({ behavior: 'smooth' });
        }
        
        // Update metrics dashboard
        this.updateMetricsDashboard(result);
        
        // Create charts
        this.createCostChart(result.cost_data);
        this.createServiceChart(result.cost_data);
        
        // Display cluster information
        this.displayClusterInfo(result.metrics_data);
        
        // Display recommendations
        this.displayRecommendations(result.analysis);
        
        // Display implementation plan
        this.displayImplementationPlan(result.analysis);
    }
    
    updateMetricsDashboard(result) {
        const metricsDiv = document.getElementById('metrics-dashboard');
        if (metricsDiv) {
            metricsDiv.style.display = 'grid';
        }
        
        // Update cost metrics
        if (result.cost_data && result.cost_data.data) {
            const costData = result.cost_data.data;
            this.updateElement('total-cost', this.formatCurrency(costData.total_cost || 0));
            this.updateElement('cost-period', `Last ${result.cost_data.metadata?.days_analyzed || 30} days`);
        }
        
        // Update cluster metrics
        if (result.metrics_data && result.metrics_data.data) {
            const metricsData = result.metrics_data.data;
            
            this.updateElement('node-count', metricsData.node_count || 0);
            this.updateElement('cpu-utilization', this.sanitizeCpuDisplay(metricsData.cpu_utilization || 0));
            this.updateElement('memory-utilization', `${metricsData.memory_utilization || 0}%`);
            
            // Update progress bars
            this.updateProgressBar('cpu-progress', metricsData.cpu_utilization || 0);
            this.updateProgressBar('memory-progress', metricsData.memory_utilization || 0);
            this.updateProgressBar('node-progress', Math.min((metricsData.node_count || 0) * 10, 100));
        }
        
        // Update efficiency score
        if (result.analysis && result.analysis.efficiency_analysis) {
            const efficiency = result.analysis.efficiency_analysis;
            const score = efficiency.overall_efficiency_score || 0;
            
            this.updateElement('efficiency-score', `${score}%`);
            this.updateElement('efficiency-status', this.getEfficiencyStatus(score));
            this.updateProgressBar('efficiency-progress', score);
        }
    }
    
    createCostChart(costData) {
        if (!costData || !costData.data || !costData.data.daily_costs) {
            return;
        }
        
        const ctx = document.getElementById('cost-chart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.costChart) {
            this.charts.costChart.destroy();
        }
        
        const dailyCosts = costData.data.daily_costs;
        const labels = dailyCosts.map(item => item.date);
        const costs = dailyCosts.map(item => item.cost);
        
        this.charts.costChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Daily Cost ($)',
                    data: costs,
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: 'rgb(34, 197, 94)',
                    pointBorderColor: 'rgb(255, 255, 255)',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: 'white'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: 'white'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        ticks: {
                            color: 'white',
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }
    
    createServiceChart(costData) {
        if (!costData || !costData.data || !costData.data.service_breakdown) {
            return;
        }
        
        const ctx = document.getElementById('service-chart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.serviceChart) {
            this.charts.serviceChart.destroy();
        }
        
        const serviceBreakdown = costData.data.service_breakdown;
        const labels = Object.keys(serviceBreakdown);
        const data = Object.values(serviceBreakdown);
        
        // Generate colors for each service
        const colors = this.generateColors(labels.length);
        
        this.charts.serviceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.backgrounds,
                    borderColor: colors.borders,
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
                            color: 'white',
                            padding: 20
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    displayClusterInfo(metricsData) {
        if (!metricsData || !metricsData.data) {
            return;
        }
        
        const data = metricsData.data;
        
        // Display node status
        this.displayNodeStatus(data);
        
        // Display pod distribution
        this.displayPodDistribution(data);
    }
    
    displayNodeStatus(data) {
        const container = document.getElementById('node-status-list');
        if (!container) return;
        
        container.innerHTML = '';
        
        const nodeStatus = data.node_status || {};
        const nodeDetails = data.node_details || [];
        
        if (Object.keys(nodeStatus).length === 0) {
            container.innerHTML = '<div class="text-gray-400 text-sm">No node data available</div>';
            return;
        }
        
        Object.entries(nodeStatus).forEach(([nodeName, status]) => {
            const nodeDetail = nodeDetails.find(n => n.name === nodeName) || {};
            
            const statusClass = status === 'True' ? 'status-online' : 
                              status === 'False' ? 'status-error' : 'status-warning';
            
            const nodeElement = document.createElement('div');
            nodeElement.className = 'flex items-center justify-between p-3 bg-white/5 rounded-lg';
            nodeElement.innerHTML = `
                <div class="flex items-center space-x-3">
                    <span class="status-indicator ${statusClass}"></span>
                    <div>
                        <div class="text-white font-medium">${nodeName}</div>
                        <div class="text-xs text-gray-400">${nodeDetail.node_info?.osImage || 'Unknown OS'}</div>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-sm text-green-400">${status === 'True' ? 'Ready' : 'Not Ready'}</div>
                    <div class="text-xs text-gray-400">${nodeDetail.capacity?.cpu || '0'} CPU</div>
                </div>
            `;
            
            container.appendChild(nodeElement);
        });
    }
    
    displayPodDistribution(data) {
        const container = document.getElementById('pod-distribution');
        if (!container) return;
        
        container.innerHTML = '';
        
        const namespaceDistribution = data.namespace_distribution || {};
        const totalPods = data.pod_count || 0;
        
        if (Object.keys(namespaceDistribution).length === 0) {
            container.innerHTML = '<div class="text-gray-400 text-sm">No pod data available</div>';
            return;
        }
        
        // Sort namespaces by pod count
        const sortedNamespaces = Object.entries(namespaceDistribution)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 5); // Show top 5 namespaces
        
        sortedNamespaces.forEach(([namespace, podCount]) => {
            const percentage = totalPods > 0 ? Math.round((podCount / totalPods) * 100) : 0;
            
            const namespaceElement = document.createElement('div');
            namespaceElement.className = 'p-3 bg-white/5 rounded-lg';
            namespaceElement.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <div class="text-white font-medium">${namespace}</div>
                    <div class="text-yellow-400">${podCount} pods</div>
                </div>
                <div class="bg-yellow-400/20 h-2 rounded-full overflow-hidden">
                    <div class="bg-yellow-400 h-full transition-all duration-1000" style="width: ${percentage}%"></div>
                </div>
                <div class="text-xs text-gray-400 mt-1">${percentage}% of total pods</div>
            `;
            
            container.appendChild(namespaceElement);
        });
    }
    
    displayRecommendations(analysis) {
        if (!analysis || !analysis.recommendations) {
            return;
        }
        
        const container = document.getElementById('recommendations-grid');
        if (!container) return;
        
        container.innerHTML = '';
        
        const recommendations = analysis.recommendations;
        const totalSavings = analysis.potential_savings || 0;
        
        // Update total savings
        this.updateElement('total-savings', `${this.formatCurrency(totalSavings)} potential savings`);
        
        recommendations.forEach(rec => {
            const priorityClass = rec.priority === 'High' ? 'text-red-400' : 
                                rec.priority === 'Medium' ? 'text-yellow-400' : 'text-green-400';
            
            const confidenceColor = rec.confidence >= 90 ? 'text-green-400' :
                                   rec.confidence >= 70 ? 'text-yellow-400' : 'text-red-400';
            
            const recElement = document.createElement('div');
            recElement.className = 'bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all';
            recElement.innerHTML = `
                <div class="flex items-start justify-between mb-4">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                            <i class="fas fa-lightbulb text-white"></i>
                        </div>
                        <div>
                            <h5 class="font-bold text-white">${rec.title}</h5>
                            <p class="text-sm text-gray-400">${rec.category}</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="bg-green-400/20 px-3 py-1 rounded-full mb-1">
                            <span class="text-green-400 font-bold">${this.formatCurrency(rec.potential_savings || 0)}</span>
                        </div>
                        <div class="text-xs ${priorityClass}">
                            ${rec.priority} Priority
                        </div>
                    </div>
                </div>
                
                <p class="text-gray-300 mb-4">${rec.description}</p>
                
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4 text-sm">
                        <span class="text-blue-400">Effort: ${rec.implementation_effort}</span>
                        <span class="text-orange-400">Risk: ${rec.risk_level}</span>
                        <span class="${confidenceColor}">Confidence: ${rec.confidence || 0}%</span>
                    </div>
                    <button 
                        class="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg text-sm transition-all"
                        onclick="dashboard.showImplementationSteps('${rec.id}')"
                    >
                        View Steps
                    </button>
                </div>
            `;
            
            container.appendChild(recElement);
        });
    }
    
    displayImplementationPlan(analysis) {
        if (!analysis || !analysis.implementation_plan) {
            return;
        }
        
        const container = document.getElementById('implementation-plan');
        if (!container) return;
        
        container.innerHTML = '';
        
        const implementationPlan = analysis.implementation_plan;
        
        implementationPlan.forEach(phase => {
            const phaseElement = document.createElement('div');
            phaseElement.className = 'flex items-start space-x-4';
            phaseElement.innerHTML = `
                <div class="flex-shrink-0">
                    <div class="w-10 h-10 bg-gradient-to-r from-green-500 to-teal-500 rounded-full flex items-center justify-center font-bold text-white">
                        ${phase.phase}
                    </div>
                </div>
                <div class="flex-1 bg-white/5 border border-white/10 rounded-xl p-6">
                    <div class="flex items-start justify-between mb-4">
                        <div>
                            <h5 class="font-bold text-white text-lg">${phase.title}</h5>
                            <p class="text-gray-400 text-sm">${phase.duration}</p>
                        </div>
                        <div class="text-right">
                            <div class="bg-green-400/20 px-3 py-1 rounded-full">
                                <span class="text-green-400 font-bold">${this.formatCurrency(phase.estimated_savings || 0)} savings</span>
                            </div>
                        </div>
                    </div>
                    <p class="text-gray-300 mb-4">${phase.description}</p>
                    <div class="flex items-center justify-between">
                        <div class="text-sm text-blue-400">
                            ${phase.recommendations?.length || 0} recommendations in this phase
                        </div>
                        <div class="text-sm text-gray-400">
                            Risk Level: ${phase.risk_level || 'Medium'}
                        </div>
                    </div>
                </div>
            `;
            
            container.appendChild(phaseElement);
        });
    }
    
    showImplementationSteps(recommendationId) {
        if (!this.currentAnalysis || !this.currentAnalysis.analysis.recommendations) {
            return;
        }
        
        const recommendation = this.currentAnalysis.analysis.recommendations.find(r => r.id === recommendationId);
        if (!recommendation || !recommendation.implementation_steps) {
            alert('Implementation steps not available for this recommendation.');
            return;
        }
        
        const steps = recommendation.implementation_steps.map((step, index) => 
            `${index + 1}. ${step}`
        ).join('\n');
        
        alert(`Implementation Steps for: ${recommendation.title}\n\n${steps}`);
    }
    
    async refreshRealTimeData() {
        if (!this.currentAnalysis || this.isAnalyzing) {
            return;
        }
        
        try {
            const metadata = this.currentAnalysis.cost_data?.metadata;
            if (!metadata) return;
            
            // Get fresh metrics data
            const metricsUrl = this.apiBaseUrl ? 
                `${this.apiBaseUrl}/api/metrics/${metadata.resource_group}/${metadata.cluster_name}` :
                `/api/metrics/${metadata.resource_group}/${metadata.cluster_name}`;
            const response = await fetch(metricsUrl);
            if (response.ok) {
                const metricsData = await response.json();
                
                // Update only the metrics part of the dashboard
                if (metricsData.success) {
                    this.updateRealTimeMetrics(metricsData.data);
                }
            }
        } catch (error) {
            console.error('Failed to refresh real-time data:', error);
        }
    }
    
    updateRealTimeMetrics(metricsData) {
        // Update CPU and memory utilization
        this.updateElement('cpu-utilization', this.sanitizeCpuDisplay(metricsData.cpu_utilization || 0));
        this.updateElement('memory-utilization', `${metricsData.memory_utilization || 0}%`);
        
        // Update progress bars
        this.updateProgressBar('cpu-progress', metricsData.cpu_utilization || 0);
        this.updateProgressBar('memory-progress', metricsData.memory_utilization || 0);
        
        // Update node count if changed
        this.updateElement('node-count', metricsData.node_count || 0);
        this.updateProgressBar('node-progress', Math.min((metricsData.node_count || 0) * 10, 100));
        
        // Update cluster info displays
        this.displayNodeStatus(metricsData);
        this.displayPodDistribution(metricsData);
    }
    
    // Utility methods
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    updateProgressBar(id, percentage) {
        const progressBar = document.getElementById(id);
        if (progressBar) {
            progressBar.style.width = `${Math.min(Math.max(percentage, 0), 100)}%`;
        }
    }
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }
    
    getEfficiencyStatus(score) {
        if (score >= 80) return 'Excellent';
        if (score >= 60) return 'Good';
        if (score >= 40) return 'Fair';
        return 'Needs Improvement';
    }
    
    generateColors(count) {
        const baseColors = [
            'rgba(59, 246, 206, 0.8)',   // Blue
            'rgba(34, 197, 94, 0.8)',    // Green
            'rgba(168, 85, 247, 0.8)',   // Purple
            'rgba(249, 115, 22, 0.8)',   // Orange
            'rgba(236, 72, 153, 0.8)',   // Pink
            'rgba(14, 165, 233, 0.8)',   // Sky
            'rgba(132, 204, 22, 0.8)',   // Lime
            'rgba(239, 68, 68, 0.8)'     // Red
        ];
        
        const borderColors = baseColors.map(color => color.replace('0.8', '1'));
        
        const backgrounds = [];
        const borders = [];
        
        for (let i = 0; i < count; i++) {
            backgrounds.push(baseColors[i % baseColors.length]);
            borders.push(borderColors[i % borderColors.length]);
        }
        
        return { backgrounds, borders };
    }
    
    showError(message) {
        const errorDiv = document.getElementById('error-display');
        const errorMessage = document.getElementById('error-message');
        
        if (errorDiv && errorMessage) {
            // Enhanced error message with troubleshooting tips
            let enhancedMessage = message;
            
            if (message.includes('Cannot connect to backend')) {
                enhancedMessage += '\n\nTroubleshooting steps:\n';
                enhancedMessage += '1. Ensure backend is running: python enhanced_aks_platform.py\n';
                enhancedMessage += '2. Check if port 8000 is available\n';
                enhancedMessage += '3. Verify CORS settings if using different domains\n';
                enhancedMessage += '4. Check browser console for detailed errors';
            }
            
            if (message.includes('Analysis failed')) {
                enhancedMessage += '\n\nPossible causes:\n';
                enhancedMessage += '1. Azure CLI not authenticated (run: az login)\n';
                enhancedMessage += '2. Invalid subscription ID or resource group\n';
                enhancedMessage += '3. No access to the specified AKS cluster\n';
                enhancedMessage += '4. Cluster name is incorrect';
            }
            
            errorMessage.style.whiteSpace = 'pre-line';
            errorMessage.textContent = enhancedMessage;
            errorDiv.style.display = 'block';
            errorDiv.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    hideError() {
        const errorDiv = document.getElementById('error-display');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }
    sanitizeCpuDisplay(cpuValue) {
        // Sanitize CPU utilization display to avoid exposing exact values
        if (cpuValue > 80) return 'High';
        if (cpuValue > 60) return 'Medium-High';
        if (cpuValue > 40) return 'Medium';
        if (cpuValue > 20) return 'Low-Medium';
        return 'Low';
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new AKSDashboard();
});

// Handle page visibility changes for real-time updates
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && window.dashboard) {
        // Page became visible, refresh data
        window.dashboard.refreshRealTimeData();
    }
});