/**
 * Global Auto-Refresh Manager for AKS Cost Optimizer
 * Provides silent refresh functionality across all pages
 * 
 * Developer: Srinivas Kondepudi
 * Organization: Nivaya Technologies & kubeopt
 */

class GlobalRefreshManager {
    constructor() {
        this.refreshInterval = null;
        this.isRefreshing = false;
        this.refreshHandlers = new Map();
        this.currentPage = this.detectCurrentPage();
        this.refreshIntervalMs = 60000; // 60 seconds default
        this.fastRefreshIntervalMs = 15000; // 15 seconds during analysis
        this.isAnalysisActive = false;
        this.lastUserActivity = Date.now();
        this.currentInterval = this.refreshIntervalMs;
        
        this.init();
    }
    
    init() {
        console.log(`🔄 Initializing Global Refresh Manager for page: ${this.currentPage}`);
        
        // Register page-specific refresh handlers
        this.registerRefreshHandlers();
        
        // Start monitoring for analysis activity
        this.startAnalysisMonitoring();
        
        // Setup cleanup on page unload
        window.addEventListener('beforeunload', () => this.cleanup());
        
        // Track user activity to avoid interrupting them
        this.setupUserActivityTracking();
        
        // Start auto-refresh immediately (always on, not just during analysis)
        this.startAutoRefresh();
        
        console.log('✅ Global Refresh Manager initialized with auto-refresh active');
    }
    
    detectCurrentPage() {
        const path = window.location.pathname;
        
        if (path.includes('/clusters') || path === '/') {
            return 'clusters';
        } else if (path.includes('/cluster/')) {
            return 'cluster-detail';
        } else if (path.includes('/dashboard')) {
            return 'dashboard';
        } else if (path.includes('/analysis') || path.includes('/results')) {
            return 'implementation';
        } else if (path.includes('/enterprise')) {
            return 'enterprise';
        } else if (path.includes('/security')) {
            return 'security';
        } else if (path.includes('/alerts')) {
            return 'alerts';
        } else if (path.includes('/settings')) {
            return 'settings';
        } else {
            return 'unknown';
        }
    }
    
    setupUserActivityTracking() {
        // Track user activity to avoid interrupting them during refresh
        const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        
        const updateActivity = () => {
            this.lastUserActivity = Date.now();
        };
        
        activityEvents.forEach(event => {
            document.addEventListener(event, updateActivity, { passive: true });
        });
        
        console.log('👂 User activity tracking enabled');
    }
    
    registerRefreshHandlers() {
        // Clusters page refresh handlers
        if (this.currentPage === 'clusters') {
            // Use silent page refresh instead of API polling
            this.addRefreshHandler('silent-page-refresh', async () => {
                return await this.silentPageRefresh();
            });
        }
        
        // Cluster detail page refresh handlers
        if (this.currentPage === 'cluster-detail') {
            this.addRefreshHandler('cluster-analysis-status', async () => {
                return await this.refreshClusterAnalysisStatus();
            });
            
            this.addRefreshHandler('cluster-metrics', async () => {
                return await this.refreshClusterMetrics();
            });
        }
        
        // Dashboard page refresh handlers
        if (this.currentPage === 'dashboard') {
            this.addRefreshHandler('dashboard-overview', async () => {
                return await this.refreshDashboardOverview();
            });
            
            this.addRefreshHandler('recent-analysis', async () => {
                return await this.refreshRecentAnalysis();
            });
        }
        
        // Implementation plan page refresh handlers
        if (this.currentPage === 'implementation') {
            this.addRefreshHandler('implementation-status', async () => {
                return await this.refreshImplementationStatus();
            });
        }
        
        // Enterprise metrics page refresh handlers
        if (this.currentPage === 'enterprise') {
            this.addRefreshHandler('enterprise-metrics', async () => {
                return await this.refreshEnterpriseMetrics();
            });
        }
        
        // Security posture page refresh handlers
        if (this.currentPage === 'security') {
            this.addRefreshHandler('security-status', async () => {
                return await this.refreshSecurityStatus();
            });
        }
        
        // Alerts page refresh handlers
        if (this.currentPage === 'alerts') {
            this.addRefreshHandler('alerts-status', async () => {
                return await this.refreshAlertsStatus();
            });
        }
        
        // Settings page refresh handlers
        if (this.currentPage === 'settings') {
            this.addRefreshHandler('settings-status', async () => {
                return await this.refreshSettingsStatus();
            });
            
            this.addRefreshHandler('license-status', async () => {
                return await this.refreshLicenseStatus();
            });
        }
    }
    
    addRefreshHandler(name, handler) {
        this.refreshHandlers.set(name, handler);
        console.log(`📝 Registered refresh handler: ${name}`);
    }
    
    async startAnalysisMonitoring() {
        // Disabled API-based analysis monitoring to reduce server load
        // Auto-refresh will use a fixed interval with silent page refresh
        console.log('📴 Analysis monitoring disabled - using fixed refresh interval');
    }
    
    async checkForActiveAnalysis() {
        try {
            const response = await fetch('/api/clusters', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) return false;
            
            const data = await response.json();
            
            if (data.status === 'success' && data.clusters) {
                const analyzingClusters = data.clusters.filter(cluster => 
                    cluster.analysis_status === 'analyzing' || cluster.analysis_status === 'running'
                );
                
                this.isAnalysisActive = analyzingClusters.length > 0;
                return this.isAnalysisActive;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Error checking for active analysis:', error);
            return false;
        }
    }
    
    startAutoRefresh() {
        if (this.refreshInterval) return; // Already running
        
        console.log(`🔄 Starting auto-refresh for ${this.currentPage} page`);
        this.isRefreshing = true;
        
        this.refreshInterval = setInterval(async () => {
            if (this.refreshHandlers.size === 0) {
                return;
            }
            
            // Execute all registered refresh handlers
            const refreshPromises = Array.from(this.refreshHandlers.entries()).map(
                async ([name, handler]) => {
                    try {
                        await handler();
                        console.log(`✅ Refreshed: ${name}`);
                    } catch (error) {
                        console.error(`❌ Failed to refresh ${name}:`, error);
                    }
                }
            );
            
            await Promise.allSettled(refreshPromises);
        }, this.currentInterval);
    }
    
    adjustRefreshInterval(newInterval) {
        if (this.currentInterval === newInterval) return; // No change needed
        
        this.currentInterval = newInterval;
        
        if (this.refreshInterval) {
            this.stopAutoRefresh();
            this.startAutoRefresh();
        }
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            this.isRefreshing = false;
            console.log('⏹️ Stopped auto-refresh');
        }
    }
    
    cleanup() {
        this.stopAutoRefresh();
        this.refreshHandlers.clear();
        console.log('🧹 Global Refresh Manager cleaned up');
    }
    
    // Page-specific refresh methods
    async refreshPortfolioData() {
        try {
            const response = await fetch('/api/portfolio/summary', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'success' && data.portfolio_summary) {
                // Update portfolio metrics if the function exists
                if (typeof updatePortfolioMetricsUI === 'function') {
                    updatePortfolioMetricsUI(data.portfolio_summary);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to refresh portfolio data:', error);
            return false;
        }
    }
    
    async silentPageRefresh() {
        try {
            // Only refresh if user hasn't interacted recently (to avoid interrupting them)
            const timeSinceLastActivity = Date.now() - (this.lastUserActivity || 0);
            const minInactivityTime = this.isAnalysisActive ? 10000 : 30000; // Shorter wait during analysis
            
            if (timeSinceLastActivity < minInactivityTime) {
                console.log(`🔄 Skipping refresh - user recently active (${Math.round(timeSinceLastActivity/1000)}s ago)`);
                return false;
            }
            
            // IMPROVED: Silent AJAX refresh instead of full page reload to prevent flickering
            console.log('🔄 Performing silent AJAX refresh...');
            
            // Fetch updated cluster data
            const response = await fetch('/api/clusters', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                console.warn('⚠️ Silent refresh failed, falling back to page reload');
                window.location.reload();
                return true;
            }
            
            const data = await response.json();
            
            if (data.status === 'success' && data.clusters) {
                // Check if any clusters are analyzing to adjust refresh frequency
                const analyzingClusters = data.clusters.filter(cluster => 
                    cluster.analysis_status === 'analyzing' || cluster.analysis_status === 'running'
                );
                
                const wasAnalysisActive = this.isAnalysisActive;
                this.isAnalysisActive = analyzingClusters.length > 0;
                
                // Adjust refresh interval based on analysis activity
                if (this.isAnalysisActive && !wasAnalysisActive) {
                    console.log('🚀 Analysis detected, increasing refresh frequency');
                    this.adjustRefreshInterval(this.fastRefreshIntervalMs);
                } else if (!this.isAnalysisActive && wasAnalysisActive) {
                    console.log('✅ Analysis completed, reducing refresh frequency');
                    this.adjustRefreshInterval(this.refreshIntervalMs);
                }
                
                // Update cluster cards silently without page reload
                if (typeof updateClusterCardsStatus === 'function') {
                    updateClusterCardsStatus(data.clusters);
                } else {
                    // Fallback to page reload if update function not available
                    window.location.reload();
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to perform silent refresh:', error);
            // Fallback to page reload only in case of error
            window.location.reload();
            return false;
        }
    }
    
    async refreshDashboardOverview() {
        try {
            const response = await fetch('/api/dashboard/overview', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update dashboard overview if the function exists
                if (typeof updateDashboardOverview === 'function') {
                    updateDashboardOverview(data);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to refresh dashboard overview:', error);
            return false;
        }
    }
    
    async refreshRecentAnalysis() {
        try {
            const response = await fetch('/api/dashboard/recent-analysis', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update recent analysis if the function exists
                if (typeof updateRecentAnalysis === 'function') {
                    updateRecentAnalysis(data);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to refresh recent analysis:', error);
            return false;
        }
    }
    
    async refreshImplementationStatus() {
        try {
            const clusterId = this.getClusterIdFromUrl();
            if (!clusterId) return false;
            
            const response = await fetch(`/api/clusters/${clusterId}/analysis-status`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update implementation status if the function exists
                if (typeof updateImplementationStatus === 'function') {
                    updateImplementationStatus(data);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to refresh implementation status:', error);
            return false;
        }
    }
    
    async refreshEnterpriseMetrics() {
        try {
            const response = await fetch('/api/enterprise-metrics', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update enterprise metrics if the function exists
                if (typeof updateEnterpriseMetrics === 'function') {
                    updateEnterpriseMetrics(data);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to refresh enterprise metrics:', error);
            return false;
        }
    }
    
    async refreshSecurityStatus() {
        try {
            const response = await fetch('/api/security/status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update security status if the function exists
                if (typeof updateSecurityStatus === 'function') {
                    updateSecurityStatus(data);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to refresh security status:', error);
            return false;
        }
    }
    
    async refreshAlertsStatus() {
        try {
            const response = await fetch('/api/alerts', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update alerts status if the function exists
                if (typeof updateAlertsStatus === 'function') {
                    updateAlertsStatus(data);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to refresh alerts status:', error);
            return false;
        }
    }
    
    async refreshSettingsStatus() {
        try {
            const response = await fetch('/api/settings/status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update settings status if the function exists
                if (typeof updateSettingsStatus === 'function') {
                    updateSettingsStatus(data);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to refresh settings status:', error);
            return false;
        }
    }
    
    async refreshLicenseStatus() {
        try {
            const response = await fetch('/api/license/status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update license status if the function exists
                if (typeof updateLicenseStatus === 'function') {
                    updateLicenseStatus(data);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to refresh license status:', error);
            return false;
        }
    }
    
    async refreshClusterAnalysisStatus() {
        try {
            // Extract cluster ID from URL
            const clusterId = this.getClusterIdFromUrl();
            if (!clusterId) {
                console.warn('⚠️ Cannot refresh cluster status - no cluster ID in URL');
                return false;
            }
            
            const response = await fetch(`/api/clusters/${clusterId}/analysis-status`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update cluster status if the function exists
                if (typeof updateClusterStatus === 'function') {
                    updateClusterStatus(data.cluster);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to refresh cluster analysis status:', error);
            return false;
        }
    }
    
    async refreshClusterMetrics() {
        try {
            // Extract cluster ID from URL  
            const clusterId = this.getClusterIdFromUrl();
            if (!clusterId) {
                console.warn('⚠️ Cannot refresh cluster metrics - no cluster ID in URL');
                return false;
            }
            
            const response = await fetch(`/api/chart-data?cluster_id=${encodeURIComponent(clusterId)}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update cluster metrics display if the function exists
                if (typeof updateClusterMetrics === 'function') {
                    updateClusterMetrics(data.metrics);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to refresh cluster metrics:', error);
            return false;
        }
    }
    
    getClusterIdFromUrl() {
        const pathParts = window.location.pathname.split('/');
        
        // Handle /cluster/cluster-id URLs
        const clusterIndex = pathParts.findIndex(part => part === 'cluster');
        if (clusterIndex !== -1 && pathParts[clusterIndex + 1]) {
            return decodeURIComponent(pathParts[clusterIndex + 1]);
        }
        
        // Handle /analysis/cluster-id URLs (legacy)
        const analysisIndex = pathParts.findIndex(part => part === 'analysis');
        if (analysisIndex !== -1 && pathParts[analysisIndex + 1]) {
            return decodeURIComponent(pathParts[analysisIndex + 1]);
        }
        
        return null;
    }
    
    // Public methods for manual refresh control
    forceRefresh() {
        console.log('🔄 Forcing immediate refresh...');
        if (this.refreshHandlers.size > 0) {
            this.startAutoRefresh();
        }
    }
    
    setRefreshInterval(intervalMs) {
        this.refreshIntervalMs = intervalMs;
        console.log(`⏱️ Refresh interval set to ${intervalMs}ms`);
        
        // Restart with new interval if currently running
        if (this.isRefreshing) {
            this.stopAutoRefresh();
            this.startAutoRefresh();
        }
    }
}

// Initialize global refresh manager
window.GlobalRefreshManager = new GlobalRefreshManager();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GlobalRefreshManager;
}