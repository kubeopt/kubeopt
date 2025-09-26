/**
 * Security Data Manager - Data Operations and API Integration
 * =========================================================
 * Handles all data fetching, caching, and API interactions for security dashboard
 */

class SecurityDataManager {
    constructor(apiBaseUrl = '/api/security') {
        this.apiBaseUrl = apiBaseUrl;
        this.cachedData = null;
        this.refreshInterval = 300000; // 5 minutes
        this.activeIntervals = new Map();
    }

    // Check if security features are enabled before making API calls
    isSecurityFeatureEnabled() {
        if (window.checkFeatureAccess) {
            return window.checkFeatureAccess('security_posture');
        }
        
        // Fallback: check global feature flags
        if (window.featureLockManager && window.featureLockManager.featureFlags) {
            return window.featureLockManager.featureFlags.security_posture;
        }
        
        // Default to false if we can't determine
        console.warn('⚠️ Cannot determine security feature status, assuming disabled');
        return false;
    }

    getCurrentClusterId() {
        // Extract cluster ID from URL - format: rg-dpl-mad-dev-ne2-2_aks-dpl-mad-dev-ne2-1
        const path = window.location.pathname;
        const match = path.match(/\/cluster\/([^\/\?]+)/);
        
        if (match && match[1]) {
            const clusterId = decodeURIComponent(match[1]);
            logDebug(`🎯 SECURITY: Extracted Cluster ID from URL: ${clusterId}`);
            
            // Validate the format (should contain underscore between RG and AKS name)
            if (clusterId.includes('_')) {
                logDebug(`✅ SECURITY: Valid cluster ID format: ${clusterId}`);
                
                // Update global state
                window.currentClusterState.clusterId = clusterId;
                window.currentClusterState.lastUpdated = new Date().toISOString();
                window.currentClusterState.validated = true;
                
                // Also update global cluster object if it exists
                if (window.currentCluster) {
                    window.currentCluster.id = clusterId;
                }
                
                return clusterId;
            } else {
                console.warn(`⚠️ SECURITY: Unexpected cluster ID format: ${clusterId}`);
            }
        }
        
        // Fallback: From global cluster object (if available from main page)
        if (window.currentCluster && window.currentCluster.id) {
            logDebug(`🎯 SECURITY: Cluster ID from global: ${window.currentCluster.id}`);
            return window.currentCluster.id;
        }
        
        // Last resort: try to get from backend
        console.warn('⚠️ SECURITY: No cluster ID found in URL, attempting other methods');
        return null;
    }

    async loadSecurityOverview() {
        // Check if security features are enabled
        if (!this.isSecurityFeatureEnabled()) {
            logDebug('🔒 Security features are locked - skipping API call');
            return null;
        }
        
        try {
            const clusterId = await this.getCurrentClusterId();
            
            if (!clusterId) {
                logDebug('ℹ️ No cluster ID available for security overview');
                return null;
            }
            
            logDebug(`🔍 Loading security overview for cluster: ${clusterId}`);
            
            // Try multiple API endpoints to find the data
            const endpoints = [
                `${this.apiBaseUrl}/results/${clusterId}`,
                `${this.apiBaseUrl}/overview?cluster_id=${clusterId}`,
                `/api/analysis/security/${clusterId}`,
                `${this.apiBaseUrl}/results/${clusterId.split('_')[1]}`,
                `${this.apiBaseUrl}/overview?cluster_id=${clusterId.split('_')[1]}`
            ];
            
            let data = null;
            let successfulEndpoint = null;
            
            for (const endpoint of endpoints) {
                try {
                    logDebug(`📡 Trying endpoint: ${endpoint}`);
                    const response = await fetch(endpoint);
                    logDebug(`   Response status: ${response.status}`);
                    
                    if (response.ok) {
                        const responseData = await response.json();
                        if (responseData && Object.keys(responseData).length > 0) {
                            data = responseData;
                            successfulEndpoint = endpoint;
                            logDebug(`   ✅ Data found! Keys:`, Object.keys(responseData));
                            break;
                        }
                    }
                } catch (error) {
                    console.warn(`   ❌ Failed:`, error.message);
                }
            }
            
            if (!data) {
                console.warn('⚠️ No security data found from any endpoint');
                return null;
            }
            
            // Cache the data for use in other functions
            this.cachedData = data;
            
            logDebug('📊 Security data received from:', successfulEndpoint);
            logDebug('Data structure:', Object.keys(data));
            
            return data;
            
        } catch (error) {
            console.error('❌ Failed to load security overview:', error);
            throw error;
        }
    }

    async loadSecurityAlerts() {
        // Check if security features are enabled
        if (!this.isSecurityFeatureEnabled()) {
            logDebug('🔒 Security features are locked - skipping alerts API call');
            return [];
        }
        
        try {
            // Use cached data if available
            if (this.cachedData && this.cachedData.analysis) {
                const analysis = this.cachedData.analysis || this.cachedData;
                const alerts = analysis.security_posture?.alerts || [];
                
                logDebug(`✅ Retrieved ${alerts.length} security alerts from cache`);
                return alerts;
            }

            // Otherwise fetch fresh data
            const clusterId = await this.getCurrentClusterId();
            if (!clusterId) return [];

            const response = await fetch(`${this.apiBaseUrl}/results/${clusterId}`);
            if (response.ok) {
                const data = await response.json();
                const alerts = data.analysis?.security_posture?.alerts || [];
                return alerts;
            }
            return [];
        } catch (error) {
            console.error('❌ Failed to load security alerts:', error);
            return [];
        }
    }

    async loadPolicyViolations() {
        // Check if security features are enabled
        if (!this.isSecurityFeatureEnabled()) {
            logDebug('🔒 Security features are locked - skipping policy violations API call');
            return [];
        }
        
        try {
            // Use cached data if available
            if (this.cachedData && this.cachedData.analysis) {
                const analysis = this.cachedData.analysis || this.cachedData;
                const violations = analysis.policy_compliance?.violations || [];
                
                logDebug(`✅ Retrieved ${violations.length} policy violations from cache`);
                return violations;
            }

            // Otherwise fetch fresh data
            const clusterId = await this.getCurrentClusterId();
            if (!clusterId) return [];

            const response = await fetch(`${this.apiBaseUrl}/results/${clusterId}`);
            if (response.ok) {
                const data = await response.json();
                const violations = data.analysis?.policy_compliance?.violations || [];
                return violations;
            }
            return [];
        } catch (error) {
            console.error('❌ Failed to load policy violations:', error);
            return [];
        }
    }

    async loadCompliance() {
        // Check if security features are enabled
        if (!this.isSecurityFeatureEnabled()) {
            logDebug('🔒 Security features are locked - skipping compliance API call');
            return {};
        }
        
        try {
            // Use cached data if available
            if (this.cachedData && this.cachedData.analysis) {
                const analysis = this.cachedData.analysis || this.cachedData;
                const complianceFrameworks = analysis.compliance_frameworks || {};
                
                logDebug(`✅ Retrieved ${Object.keys(complianceFrameworks).length} compliance frameworks from cache`);
                return complianceFrameworks;
            }

            // Otherwise fetch fresh data
            const clusterId = await this.getCurrentClusterId();
            if (!clusterId) return {};

            const response = await fetch(`${this.apiBaseUrl}/results/${clusterId}`);
            if (response.ok) {
                const data = await response.json();
                const complianceFrameworks = data.analysis?.compliance_frameworks || {};
                return complianceFrameworks;
            }
            return {};
        } catch (error) {
            console.error('❌ Failed to load compliance:', error);
            return {};
        }
    }

    async loadVulnerabilities() {
        // Check if security features are enabled
        if (!this.isSecurityFeatureEnabled()) {
            logDebug('🔒 Security features are locked - skipping vulnerabilities API call');
            return {};
        }
        
        try {
            const clusterId = await this.getCurrentClusterId();
            if (!clusterId) return null;

            // Use cached data if available
            if (this.cachedData && this.cachedData.analysis) {
                return this.cachedData.analysis.vulnerability_assessment;
            }

            return null;
        } catch (error) {
            console.error('❌ Failed to load vulnerabilities:', error);
            return null;
        }
    }

    filterAlerts(severity, category) {
        if (this.cachedData && this.cachedData.analysis) {
            let alerts = this.cachedData.analysis.security_posture?.alerts || [];
            
            if (severity) {
                alerts = alerts.filter(a => a.severity === severity);
            }
            if (category) {
                alerts = alerts.filter(a => a.category === category);
            }
            
            return alerts;
        }
        return [];
    }

    filterViolations(severity, category) {
        if (this.cachedData && this.cachedData.analysis) {
            let violations = this.cachedData.analysis.policy_compliance?.violations || [];
            
            if (severity) {
                violations = violations.filter(v => v.severity === severity);
            }
            if (category) {
                violations = violations.filter(v => v.policy_category === category);
            }
            
            return violations;
        }
        return [];
    }

    getCachedData() {
        return this.cachedData;
    }

    startAutoRefresh(callback) {
        const clusterId = this.getCurrentClusterId();
        if (!clusterId) {
            logDebug('ℹ️ Auto-refresh disabled - no cluster ID');
            return;
        }
        
        this.activeIntervals.forEach(interval => clearInterval(interval));
        this.activeIntervals.clear();

        const overviewInterval = setInterval(() => {
            if (document.getElementById('securityposture-content') && 
                !document.getElementById('securityposture-content').classList.contains('hidden')) {
                this.loadSecurityOverview().then(data => {
                    if (data && callback) {
                        callback(data);
                    }
                });
            }
        }, this.refreshInterval);
        
        this.activeIntervals.set('overview', overviewInterval);
        logDebug(`🔄 Auto-refresh started (${this.refreshInterval/1000}s interval)`);
    }

    stopAutoRefresh() {
        this.activeIntervals.forEach(interval => clearInterval(interval));
        this.activeIntervals.clear();
        logDebug('ℹ️ Auto-refresh stopped');
    }

    async debugClusterAndAPIs() {
        logDebug('🔍 === SECURITY DASHBOARD DEBUG ===');
        
        const clusterId = this.getCurrentClusterId();
        logDebug('📌 Current Cluster ID:', clusterId);
        logDebug('📌 Global State:', window.currentClusterState);
        logDebug('📌 Cached Data Available:', !!this.cachedData);
        
        if (this.cachedData) {
            logDebug('📌 Cached Data Structure:', Object.keys(this.cachedData));
            
            if (this.cachedData.analysis) {
                const analysis = this.cachedData.analysis;
                logDebug('📊 Security Score:', analysis.security_posture?.overall_score);
                logDebug('📊 Total Alerts:', analysis.security_posture?.alerts?.length);
                logDebug('📊 Total Violations:', analysis.policy_compliance?.violations?.length);
                logDebug('📊 Compliance Frameworks:', Object.keys(analysis.compliance_frameworks || {}));
            }
        }
        
        return clusterId;
    }
}

// Export for use by UI renderer
window.SecurityDataManager = SecurityDataManager;