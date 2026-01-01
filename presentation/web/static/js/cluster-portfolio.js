/**
 * Cluster Portfolio Page JavaScript
 * Handles cluster portfolio functionality including modals, analysis, and auto-refresh
 */

class ClusterPortfolio {
    constructor() {
        this.autoRefreshInterval = null;
        this.pollInterval = 5000; // 5 seconds
        this.maxPolls = 60; // 5 minutes max
        
        this.init();
    }

    init() {
        this.bindEventListeners();
        this.loadPortfolioStats();
        this.checkAllAnalysisStatus(); // Check status on page load
        this.startAutoRefresh();
        this.setupVisibilityListener(); // Recheck on tab focus
    }

    bindEventListeners() {
        // Modal close handlers
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.closeAddClusterModal();
                this.closeDeleteConfirmModal();
            }
        });

        // Delete confirmation checkbox handler
        const deleteCheckbox = document.getElementById('deleteConfirmCheck');
        const deleteButton = document.getElementById('confirmDeleteButton');
        
        if (deleteCheckbox && deleteButton) {
            deleteCheckbox.addEventListener('change', function() {
                deleteButton.disabled = !this.checked;
            });
        }


        // Filter functionality
        const environmentFilter = document.getElementById('environment-filter');
        if (environmentFilter) {
            environmentFilter.addEventListener('change', (e) => this.handleEnvironmentFilter(e));
        }
        
        // Sort functionality
        const sortBy = document.getElementById('sort-by');
        if (sortBy) {
            sortBy.addEventListener('change', (e) => this.handleSort(e));
        }
    }

    // Modal Management
    openAddClusterModal() {
        const modal = document.getElementById('addClusterModal');
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            
            this.loadSubscriptions();
            
            setTimeout(() => {
                const clusterNameInput = document.getElementById('clusterName');
                if (clusterNameInput) clusterNameInput.focus();
            }, 200);
        }
    }

    closeAddClusterModal(event) {
        if (event && event.target !== event.currentTarget) return;
        
        const modal = document.getElementById('addClusterModal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
            
            const form = document.getElementById('addClusterForm');
            if (form) form.reset();
        }
    }

    async loadSubscriptions() {
        const select = document.getElementById('subscriptionSelect');
        if (!select) return;
        
        try {
            const response = await fetch('/api/subscriptions/dropdown');
            const data = await response.json();
            
            if (data.status === 'success' && data.subscriptions) {
                select.innerHTML = '<option value="">Select a subscription...</option>';
                data.subscriptions.forEach(sub => {
                    const option = document.createElement('option');
                    option.value = sub.id;
                    option.textContent = sub.display_name;
                    select.appendChild(option);
                });
            } else {
                select.innerHTML = '<option value="">No subscriptions available</option>';
            }
        } catch (error) {
            console.error('Error loading subscriptions:', error);
            select.innerHTML = '<option value="">Error loading subscriptions</option>';
        }
    }

    // Form Validation
    clearFieldError(input) {
        const formGroup = input.closest('.form-group');
        if (formGroup) {
            formGroup.classList.remove('error');
        }
    }

    highlightEmptyRequiredFields() {
        let hasErrors = false;
        const requiredFields = ['subscriptionSelect', 'clusterName'];
        
        requiredFields.forEach(fieldId => {
            const input = document.getElementById(fieldId);
            const formGroup = input?.closest('.form-group');
            
            if (!input?.value?.trim()) {
                hasErrors = true;
                if (formGroup) formGroup.classList.add('error');
            } else {
                if (formGroup) formGroup.classList.remove('error');
            }
        });
        
        return !hasErrors;
    }

    async validateClusterAccess() {
        const subscriptionId = document.getElementById('subscriptionSelect')?.value;
        const clusterName = document.getElementById('clusterName')?.value?.trim();
        const resourceGroup = document.getElementById('resourceGroup')?.value?.trim();
        
        if (!subscriptionId || !clusterName) {
            return false;
        }
        
        try {
            const response = await fetch(`/api/subscriptions/${subscriptionId}/validate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cluster_name: clusterName,
                    resource_group: resourceGroup || ''
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success' && result.validation_result?.valid) {
                if (result.validation_result.auto_discovered && !resourceGroup) {
                    document.getElementById('resourceGroup').value = result.validation_result.discovered_resource_group;
                }
                return true;
            }
            return false;
            
        } catch (error) {
            console.error('Error validating cluster:', error);
            return false;
        }
    }

    async submitAddCluster(event) {
        if (event) event.preventDefault();
        
        const form = document.getElementById('addClusterForm');
        const submitBtn = document.getElementById('addClusterSubmit');
        
        if (!form || !submitBtn) return;
        
        const formData = new FormData(form);
        const clusterData = {
            subscription_id: formData.get('subscription_id'),
            cluster_name: formData.get('cluster_name'),
            resource_group: formData.get('resource_group') || '',
            environment: formData.get('environment') || '',
            region: formData.get('region') || '',
            description: formData.get('description') || '',
            auto_analyze: true
        };
        
        if (!this.highlightEmptyRequiredFields()) return;
        
        const validationPassed = await this.validateClusterAccess();
        if (!validationPassed) {
            const clusterFormGroup = document.getElementById('clusterName')?.closest('.form-group');
            if (clusterFormGroup) clusterFormGroup.classList.add('error');
            return;
        }
        
        // Show loading state
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoading = submitBtn.querySelector('.btn-loading');
        if (btnText && btnLoading) {
            btnText.classList.add('hidden');
            btnLoading.classList.remove('hidden');
        }
        submitBtn.disabled = true;
        
        try {
            const response = await fetch('/api/clusters', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(clusterData)
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                showToast(`Cluster "${clusterData.cluster_name}" added successfully!`, 'success');
                this.closeAddClusterModal();
                
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                throw new Error(result.message || 'Failed to add cluster');
            }
            
        } catch (error) {
            console.error('Error adding cluster:', error);
            showToast(`Failed to add cluster: ${error.message}`, 'error');
        } finally {
            if (btnText && btnLoading) {
                btnText.classList.remove('hidden');
                btnLoading.classList.add('hidden');
            }
            submitBtn.disabled = false;
        }
    }


    handleEnvironmentFilter(e) {
        const environment = e.target.value.toLowerCase();
        const clusterCards = document.querySelectorAll('.cluster-card');
        
        clusterCards.forEach(card => {
            const cardEnv = (card.dataset.environment || 'unknown').toLowerCase();
            
            // Handle different environment naming conventions
            const envMatch = {
                'production': ['production', 'prod', 'prd'],
                'staging': ['staging', 'stage', 'stg', 'uat'],
                'development': ['development', 'dev', 'develop']
            };
            
            if (!environment) {
                // Show all if no filter selected
                card.style.display = 'block';
            } else if (envMatch[environment]) {
                // Check if card environment matches any of the variations
                const matches = envMatch[environment].some(env => cardEnv.includes(env));
                card.style.display = matches ? 'block' : 'none';
            } else {
                // Direct match for unknown cases
                card.style.display = cardEnv === environment ? 'block' : 'none';
            }
        });
    }

    handleSort(e) {
        const sortBy = e.target.value;
        const container = document.querySelector('.clusters-grid');
        if (!container) return;
        
        const cards = Array.from(container.querySelectorAll('.cluster-card'));
        
        cards.sort((a, b) => {
            switch(sortBy) {
                case 'name':
                    const nameA = a.querySelector('.cluster-name')?.textContent || '';
                    const nameB = b.querySelector('.cluster-name')?.textContent || '';
                    return nameA.localeCompare(nameB);
                    
                case 'cost':
                    const costA = parseFloat(a.querySelector('.metric-value')?.textContent.replace(/[$,]/g, '') || '0');
                    const costB = parseFloat(b.querySelector('.metric-value')?.textContent.replace(/[$,]/g, '') || '0');
                    return costB - costA; // Higher cost first
                    
                case 'savings':
                    const savingsA = parseFloat(a.querySelectorAll('.metric-value')[1]?.textContent.replace(/[$,]/g, '') || '0');
                    const savingsB = parseFloat(b.querySelectorAll('.metric-value')[1]?.textContent.replace(/[$,]/g, '') || '0');
                    return savingsB - savingsA; // Higher savings first
                    
                case 'last_analyzed':
                    const dateA = a.querySelector('.cluster-status')?.textContent || '';
                    const dateB = b.querySelector('.cluster-status')?.textContent || '';
                    // Parse dates if they're in a specific format, or use as-is for simple comparison
                    return dateB.localeCompare(dateA); // Most recent first
                    
                default:
                    return 0;
            }
        });
        
        // Clear container and re-append sorted cards
        cards.forEach(card => container.appendChild(card));
    }

    // Cluster Analysis - Simple Implementation
    async analyzeCluster(clusterId) {
        if (!clusterId) {
            showToast('Invalid cluster ID', 'error');
            return;
        }
        
        
        const analyzeBtn = document.querySelector(`[data-cluster-id="${clusterId}"]`);
        const analyzeIcon = analyzeBtn?.querySelector('.analyze-icon');
        const spinner = analyzeBtn?.querySelector('.analyzing-spinner');
        
        // Show spinner with progress
        if (analyzeIcon && spinner) {
            analyzeIcon.classList.add('hidden');
            spinner.classList.remove('hidden');
            analyzeBtn.disabled = true;
            analyzeBtn.title = 'Analyzing...';
            
            // Add simple progress text
            const btnText = analyzeBtn.querySelector('.btn-text');
            if (btnText) {
                btnText.textContent = 'Starting...';
            }
        }
        
        this.updateClusterStatus(clusterId, 'analyzing');
        //showToast(`Starting analysis for cluster: ${clusterId}`, 'info');
        
        try {
            const response = await fetch(`/api/clusters/${encodeURIComponent(clusterId)}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            
            if (response.ok && data.status === 'success') {
                //showToast(`Analysis started successfully for ${clusterId}`, 'success');
                this.startAnalysisPolling(clusterId);
            } else {
                this.resetAnalyzeButton(clusterId, 'failed');
                this.updateClusterStatus(clusterId, 'failed');
                throw new Error(data.message || 'Analysis failed');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            showToast(`Failed to start analysis: ${error.message}`, 'error');
            this.resetAnalyzeButton(clusterId, 'failed');
            this.updateClusterStatus(clusterId, 'failed');
        }
    }

    updateClusterStatus(clusterId, status) {
        const statusInfo = document.querySelector(`[data-cluster-id="${clusterId}"] .status-info`);
        if (!statusInfo) return;
        
        statusInfo.innerHTML = '';
        
        switch (status) {
            case 'analyzing':
                statusInfo.innerHTML = `
                    <i class="fas fa-cog fa-spin analyzing-icon"></i>
                    <span class="analyzing-text">Analyzing...</span>
                `;
                break;
            case 'completed':
                statusInfo.innerHTML = `
                    <i class="fas fa-check-circle success-icon"></i>
                    <span class="status-text">Analyzed</span>
                `;
                break;
            case 'failed':
                statusInfo.innerHTML = `
                    <i class="fas fa-exclamation-triangle error-icon"></i>
                    <span class="status-text">Failed</span>
                `;
                break;
            default:
                statusInfo.innerHTML = `
                    <i class="fas fa-clock warning-icon"></i>
                    <span class="status-text">Pending</span>
                `;
        }
    }

    startAnalysisPolling(clusterId) {
        let pollCount = 0;
        
        const pollAnalysisStatus = async () => {
            pollCount++;
            
            try {
                const response = await fetch(`/api/clusters/${encodeURIComponent(clusterId)}/analysis-status`);
                
                if (!response.ok) {
                    if (pollCount >= this.maxPolls) {
                        this.resetAnalyzeButton(clusterId, 'error');
                        showToast(`Analysis status check failed for ${clusterId}`, 'error');
                        return;
                    }
                    setTimeout(pollAnalysisStatus, this.pollInterval);
                    return;
                }
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    if (data.analysis_status === 'completed') {
                        this.updateClusterStatus(clusterId, 'completed');
                        this.resetAnalyzeButton(clusterId, 'completed');
                        showToast(`Analysis completed for ${clusterId}`, 'success');
                        this.updateClusterMetrics(clusterId, data);
                        return;
                        
                    } else if (data.analysis_status === 'failed') {
                        this.updateClusterStatus(clusterId, 'failed');
                        this.resetAnalyzeButton(clusterId, 'failed');
                        showToast(`Analysis failed for ${clusterId}`, 'error');
                        return;
                        
                    } else if (data.analysis_status === 'analyzing' || data.analysis_status === 'running') {
                        this.updateClusterStatus(clusterId, 'analyzing');
                        
                        // Simple progress enhancement
                        const analyzeBtn = document.querySelector(`[data-cluster-id="${clusterId}"]`);
                        const btnText = analyzeBtn?.querySelector('.btn-text');
                        if (btnText) {
                            const dots = '.'.repeat((pollCount % 3) + 1);
                            btnText.textContent = `Analyzing${dots}`;
                        }
                    }
                    
                    if (pollCount < this.maxPolls) {
                        setTimeout(pollAnalysisStatus, this.pollInterval);
                    } else {
                        showToast(`Analysis polling timeout for ${clusterId}`, 'warning');
                        this.resetAnalyzeButton(clusterId, 'timeout');
                    }
                }
                
            } catch (error) {
                console.error('Error polling analysis status:', error);
                if (pollCount < this.maxPolls) {
                    setTimeout(pollAnalysisStatus, this.pollInterval);
                } else {
                    this.resetAnalyzeButton(clusterId, 'error');
                }
            }
        };
        
        setTimeout(pollAnalysisStatus, this.pollInterval);
    }

    resetAnalyzeButton(clusterId, result) {
        const analyzeBtn = document.querySelector(`[data-cluster-id="${clusterId}"]`);
        const analyzeIcon = analyzeBtn?.querySelector('.analyze-icon');
        const spinner = analyzeBtn?.querySelector('.analyzing-spinner');
        
        if (analyzeIcon && spinner) {
            analyzeIcon.classList.remove('hidden');
            spinner.classList.add('hidden');
            analyzeBtn.disabled = false;
            
            if (result === 'completed') {
                analyzeBtn.title = 'Re-analyze';
            } else {
                analyzeBtn.title = analyzeIcon.classList.contains('fa-refresh') ? 'Re-analyze' : 'Analyze';
            }
        }
    }

    updateClusterMetrics(clusterId, clusterData) {
        const clusterCard = document.querySelector(`[data-cluster-id="${clusterId}"]`);
        if (!clusterCard) return;
        
        const costValue = clusterCard.querySelector('.metric-value[data-metric="cost"]');
        if (costValue && clusterData.last_cost !== undefined) {
            costValue.textContent = `$${clusterData.last_cost.toFixed(2)}`;
        }
        
        const savingsValue = clusterCard.querySelector('.metric-value[data-metric="savings"]');
        if (savingsValue && clusterData.last_savings !== undefined) {
            savingsValue.textContent = `$${clusterData.last_savings.toFixed(2)}`;
        }
        
        const optimizationValue = clusterCard.querySelector('.metric-value[data-metric="optimization"]');
        if (optimizationValue && clusterData.optimization_score !== undefined) {
            optimizationValue.textContent = `${Math.round(clusterData.optimization_score)}%`;
        }
        
        const nodeValue = clusterCard.querySelector('.metric-value[data-metric="nodes"]');
        if (nodeValue && clusterData.node_count !== undefined) {
            nodeValue.textContent = clusterData.node_count.toString();
        }
    }

    // Delete Functionality
    deleteClusterConfirm(clusterId) {
        if (!clusterId) {
            showToast('Invalid cluster ID', 'error');
            return;
        }
        
        const clusterCard = document.querySelector(`[data-cluster-id="${clusterId}"]`);
        const clusterName = clusterCard?.querySelector('.cluster-name')?.textContent || clusterId;
        const clusterRegion = clusterCard?.querySelector('.cluster-region')?.textContent || 'Unknown Region';
        
        window.pendingDeleteClusterId = clusterId;
        
        document.getElementById('deleteClusterNameDisplay').textContent = clusterName;
        document.getElementById('deleteClusterNameInfo').textContent = clusterName;
        document.getElementById('deleteResourceGroupInfo').textContent = clusterRegion;
        
        const checkbox = document.getElementById('deleteConfirmCheck');
        const deleteButton = document.getElementById('confirmDeleteButton');
        checkbox.checked = false;
        deleteButton.disabled = true;
        
        const modal = document.getElementById('deleteConfirmModal');
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    closeDeleteConfirmModal(event) {
        if (event && event.target !== event.currentTarget) return;
        
        const modal = document.getElementById('deleteConfirmModal');
        modal.classList.remove('active');
        document.body.style.overflow = '';
        
        window.pendingDeleteClusterId = null;
    }

    executeClusterDelete() {
        const clusterId = window.pendingDeleteClusterId;
        if (!clusterId) {
            showToast('No cluster selected for deletion', 'error');
            return;
        }
        
        this.deleteCluster(clusterId);
        this.closeDeleteConfirmModal();
    }

    async deleteCluster(clusterId) {
        if (!clusterId) {
            showToast('Invalid cluster ID', 'error');
            return;
        }
        
        showToast(`Deleting cluster: ${clusterId}`, 'info');
        
        try {
            const response = await fetch(`/cluster/${encodeURIComponent(clusterId)}/remove`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (response.ok && data.status === 'success') {
                showToast(`Cluster ${clusterId} deleted successfully`, 'success');
                const clusterCard = document.querySelector(`[data-cluster-id="${clusterId}"]`);
                if (clusterCard) {
                    clusterCard.remove();
                }
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                throw new Error(data.message || 'Delete failed');
            }
        } catch (error) {
            console.error('Delete error:', error);
            showToast(`Failed to delete cluster: ${error.message}`, 'error');
        }
    }

    setupVisibilityListener() {
        // Recheck status when tab becomes visible
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.checkAllAnalysisStatus();
            }
        });
    }

    async checkAllAnalysisStatus() {
        // Find all cluster cards and check their analysis status
        const clusterCards = document.querySelectorAll('[data-cluster-id]');
        console.log(`🔍 Checking analysis status for ${clusterCards.length} clusters`);
        
        for (const card of clusterCards) {
            const clusterId = card.getAttribute('data-cluster-id');
            if (clusterId) {
                console.log(`🔍 Checking status for cluster: ${clusterId}`);
                await this.checkSingleClusterStatus(clusterId);
            }
        }
    }

    async checkSingleClusterStatus(clusterId) {
        try {
            const response = await fetch(`/api/clusters/${encodeURIComponent(clusterId)}/analysis-status`);
            
            if (!response.ok) {
                console.log(`❌ Failed to get status for ${clusterId}: ${response.status}`);
                return;
            }
            
            const data = await response.json();
            console.log(`📊 Status for ${clusterId}:`, data.analysis_status);
            
            // Check for both old and new API response formats
            const status = data.analysis_status || data.status;
            
            if (status === 'analyzing' || status === 'running') {
                console.log(`🔄 Setting analyzing state for ${clusterId}`);
                // Resume polling for running analysis
                this.updateClusterStatus(clusterId, 'analyzing');
                this.setAnalyzingState(clusterId);
                this.startAnalysisPolling(clusterId);
            } else if (status === 'completed') {
                console.log(`✅ Setting completed state for ${clusterId}`);
                this.updateClusterStatus(clusterId, 'completed');
                this.resetAnalyzeButton(clusterId, 'completed');
            } else if (status === 'failed') {
                console.log(`❌ Setting failed state for ${clusterId}`);
                this.updateClusterStatus(clusterId, 'failed');
                this.resetAnalyzeButton(clusterId, 'failed');
            } else {
                console.log(`⚪ Setting idle state for ${clusterId} (status: ${status})`);
                // idle or unknown - ensure button is reset
                this.resetAnalyzeButton(clusterId, 'idle');
            }
        } catch (error) {
            console.error(`Error checking status for cluster ${clusterId}:`, error);
        }
    }

    setAnalyzingState(clusterId) {
        // Set button to analyzing state without making API call
        const analyzeBtn = document.querySelector(`[data-cluster-id="${clusterId}"]`);
        console.log(`🔍 Setting analyzing state for ${clusterId}, button found:`, !!analyzeBtn);
        
        if (!analyzeBtn) {
            console.log(`❌ No button found with data-cluster-id="${clusterId}"`);
            return;
        }
        
        const analyzeIcon = analyzeBtn.querySelector('.analyze-icon');
        const spinner = analyzeBtn.querySelector('.analyzing-spinner');
        
        console.log(`🔍 Elements found - icon: ${!!analyzeIcon}, spinner: ${!!spinner}`);
        
        if (analyzeIcon && spinner) {
            analyzeIcon.classList.add('hidden');
            spinner.classList.remove('hidden');
            analyzeBtn.disabled = true;
            analyzeBtn.title = 'Analyzing...';
            
            const btnText = analyzeBtn.querySelector('.btn-text');
            if (btnText) {
                btnText.textContent = 'Analyzing...';
            }
            console.log(`✅ Successfully set analyzing state for ${clusterId}`);
        } else {
            console.log(`❌ Missing elements for ${clusterId} - icon: ${!!analyzeIcon}, spinner: ${!!spinner}`);
        }
    }

    // Auto-refresh functionality - disabled since global refresh handles it
    startAutoRefresh() {
        // Global auto-refresh in main.js now handles this
        console.log('🔄 Using global auto-refresh (cluster-specific refresh disabled)');
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            console.log('⏹️ Auto-refresh stopped');
        }
    }

    async silentRefresh() {
        try {
            await this.loadPortfolioStats();
        } catch (error) {
            console.error('❌ Silent refresh failed:', error);
        }
    }

    // Standalone method to refresh just the cluster cards
    async refreshAllClusterCards() {
        try {
            console.log('🔄 Fetching latest cluster data...');
            const response = await fetch('/api/clusters/dropdown');
            
            if (!response.ok) {
                console.error(`Clusters API not available: HTTP ${response.status}`);
                return;
            }
            
            const data = await response.json();
            
            if (data.status === 'success' && data.clusters) {
                this.refreshClusterCards(data.clusters);
            } else {
                console.error('Clusters data not available:', data.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Error refreshing cluster cards:', error);
        }
    }


    async loadPortfolioStats() {
        try {
            console.log('🔄 Refreshing cluster portfolio data...');
            const response = await fetch('/api/portfolio/summary');
            
            if (!response.ok) {
                console.error(`Portfolio stats endpoint not available: HTTP ${response.status}`);
                return;
            }
            
            const data = await response.json();
            
            if (data.status === 'success' && data.portfolio_summary) {
                this.updatePortfolioStats(data.portfolio_summary);
                
                // Also refresh cluster cards with latest data
                if (data.clusters && data.clusters.length > 0) {
                    this.refreshClusterCards(data.clusters);
                    
                    // Check analysis status for all clusters during refresh
                    this.checkAllAnalysisStatus();
                }
            } else {
                console.error('Portfolio stats not available:', data.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Error loading portfolio stats:', error);
        }
    }

    updatePortfolioStats(portfolioData) {
        const totalCostEl = document.getElementById('total-cost');
        if (totalCostEl && portfolioData.total_monthly_cost !== undefined) {
            totalCostEl.textContent = this.formatCurrency(portfolioData.total_monthly_cost);
        }
        
        const totalSavingsEl = document.getElementById('total-savings');
        if (totalSavingsEl && portfolioData.total_potential_savings !== undefined) {
            totalSavingsEl.textContent = this.formatCurrency(portfolioData.total_potential_savings);
        }
        
        const totalNodesEl = document.getElementById('total-nodes');
        if (totalNodesEl && portfolioData.total_nodes !== undefined && portfolioData.total_nodes !== null) {
            totalNodesEl.textContent = portfolioData.total_nodes.toString();
        }
    }

    refreshClusterCards(clustersData) {
        if (!clustersData || !Array.isArray(clustersData)) {
            console.log('🔄 No cluster data to refresh cards');
            return;
        }
        
        console.log(`🔄 Refreshing ${clustersData.length} cluster cards`);
        
        clustersData.forEach(cluster => {
            this.updateClusterCard(cluster);
        });
    }

    updateClusterCard(cluster) {
        if (!cluster || !cluster.id) return;
        
        const clusterCard = document.querySelector(`[data-cluster-id="${cluster.id}"]`);
        if (!clusterCard) {
            console.log(`⚠️ Cluster card not found for: ${cluster.id}`);
            return;
        }
        
        // Update cost metric
        const costValue = clusterCard.querySelector('.metric-value[data-metric="cost"]');
        if (costValue && cluster.last_cost !== undefined) {
            costValue.textContent = `$${cluster.last_cost.toFixed(2)}`;
        }
        
        // Update savings metric  
        const savingsValue = clusterCard.querySelector('.metric-value[data-metric="savings"]');
        if (savingsValue && cluster.last_savings !== undefined) {
            savingsValue.textContent = `$${cluster.last_savings.toFixed(2)}`;
        }
        
        // Update nodes metric
        const nodesValue = clusterCard.querySelector('.metric-value[data-metric="nodes"]');
        if (nodesValue && cluster.node_count !== undefined) {
            nodesValue.textContent = cluster.node_count.toString();
        }
        
        // Update optimization score metric
        const optimizationValue = clusterCard.querySelector('.metric-value[data-metric="optimization"]');
        if (optimizationValue && cluster.optimization_score !== undefined) {
            optimizationValue.textContent = `${cluster.optimization_score.toFixed(0)}%`;
        }
        
        // Update last analyzed status
        const statusIndicator = clusterCard.querySelector('.status-indicator');
        if (statusIndicator) {
            if (cluster.last_analyzed) {
                statusIndicator.className = 'status-indicator status-analyzed';
                statusIndicator.title = 'Recently analyzed';
            } else {
                statusIndicator.className = 'status-indicator status-pending';
                statusIndicator.title = 'Analysis pending';
            }
        }
        
        console.log(`✅ Updated cluster card: ${cluster.name} - $${cluster.last_cost?.toFixed(2) || 0}`);
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount || 0);
    }

}

// Initialize the cluster portfolio when DOM is loaded
let clusterPortfolio;

document.addEventListener('DOMContentLoaded', function() {
    clusterPortfolio = new ClusterPortfolio();
    // Make available globally for auto-refresh system
    window.ClusterPortfolio = clusterPortfolio;
});

// Global functions for template onclick handlers
function openAddClusterModal() {
    clusterPortfolio?.openAddClusterModal();
}

function closeAddClusterModal(event) {
    clusterPortfolio?.closeAddClusterModal(event);
}

function showLicenseRequired() {
    // Show a modal about license requirement
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <div class="modal-header">
                <h2><i class="fas fa-lock"></i> License Required</h2>
                <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
            </div>
            <div class="modal-body">
                <p style="margin-bottom: 1rem;">
                    A <strong>PRO</strong> or <strong>ENTERPRISE</strong> license is required to add clusters.
                </p>
                <p style="margin-bottom: 1.5rem;">
                    Please go to Settings to add your license key.
                </p>
                <div style="text-align: center;">
                    <a href="/settings" class="btn-primary">
                        <i class="fas fa-cog"></i> Go to Settings
                    </a>
                    <button class="btn-secondary" onclick="this.closest('.modal').remove()" style="margin-left: 1rem;">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function submitAddCluster(event) {
    clusterPortfolio?.submitAddCluster(event);
}

function clearFieldError(input) {
    clusterPortfolio?.clearFieldError(input);
}

function analyzeCluster(clusterId) {
    clusterPortfolio?.analyzeCluster(clusterId);
}

function deleteClusterConfirm(clusterId) {
    clusterPortfolio?.deleteClusterConfirm(clusterId);
}

function closeDeleteConfirmModal(event) {
    clusterPortfolio?.closeDeleteConfirmModal(event);
}

function executeClusterDelete() {
    clusterPortfolio?.executeClusterDelete();
}