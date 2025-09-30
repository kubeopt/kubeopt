/**
 * Global Auto-Refresh Manager for AKS Cost Optimizer
 * Provides silent refresh functionality across all pages
 * 
 * Developer: Srinivas Kondepudi
 * Organization: Nivaya Technologies & KubeVista
 */

class GlobalRefreshManager {
    constructor() {
        this.refreshInterval = null;
        this.isRefreshing = false;
        this.refreshHandlers = new Map();
        this.currentPage = this.detectCurrentPage();
        this.refreshIntervalMs = 60000; // 60 seconds default
        this.isAnalysisActive = false;
        
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
        
        // Start auto-refresh immediately (always on, not just during analysis)
        this.startAutoRefresh();
        
        console.log('✅ Global Refresh Manager initialized with auto-refresh active');
    }
    
    detectCurrentPage() {
        const path = window.location.pathname;
        
        if (path.includes('/clusters') || path === '/') {
            return 'clusters';
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
    
    registerRefreshHandlers() {
        // Clusters page refresh handlers
        if (this.currentPage === 'clusters') {
            this.addRefreshHandler('portfolio-metrics', async () => {
                return await this.refreshPortfolioData();
            });
            
            this.addRefreshHandler('cluster-status', async () => {
                return await this.refreshClusterStatus();
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
        // Check for active analysis every 5 seconds
        setInterval(async () => {
            try {
                const hasActiveAnalysis = await this.checkForActiveAnalysis();
                
                if (hasActiveAnalysis) {
                    // During analysis: refresh every 30 seconds
                    if (this.refreshIntervalMs !== 30000) {
                        this.setRefreshInterval(30000);
                        console.log('🔄 Analysis active: switched to 30s refresh interval');
                    }
                } else {
                    // No active analysis: refresh every 60 seconds  
                    if (this.refreshIntervalMs !== 60000) {
                        this.setRefreshInterval(60000);
                        console.log('⏸️ Analysis complete: switched to 60s refresh interval');
                    }
                }
            } catch (error) {
                console.error('❌ Error checking analysis status:', error);
            }
        }, 5000);
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
                console.log('⚠️ No refresh handlers registered');
                return;
            }
            
            console.log(`🔄 Executing ${this.refreshHandlers.size} refresh handlers...`);
            
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
        }, this.refreshIntervalMs);
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
    
    async refreshClusterStatus() {
        try {
            const response = await fetch('/api/clusters', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'success' && data.clusters) {
                // Update cluster cards if the function exists
                if (typeof updateClusterCardsStatus === 'function') {
                    updateClusterCardsStatus(data.clusters);
                }
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Failed to refresh cluster status:', error);
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
    
    getClusterIdFromUrl() {
        const pathParts = window.location.pathname.split('/');
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