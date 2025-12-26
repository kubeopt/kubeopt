/**
 * Enhanced Security Data Manager
 * ==============================
 * Advanced data management with cross-chart filtering, real-time updates, and caching
 * Supports the unified security dashboard with intelligent data handling
 */

class EnhancedSecurityDataManager {
    constructor(apiBaseUrl = '/api/security') {
        this.apiBaseUrl = apiBaseUrl;
        this.cache = new Map();
        this.filters = {
            timeRange: '30d',
            severity: 'all',
            category: 'all'
        };
        this.refreshCallbacks = new Set();
        this.refreshInterval = 300000; // 5 minutes
        this.retryAttempts = 3;
        this.retryDelay = 1000;
        
        this.init();
    }

    init() {
        console.log('📊 Enhanced Security Data Manager initialized');
        this.startCacheCleanup();
    }

    // Data fetching with retry logic
    async fetchWithRetry(url, options = {}, attempts = this.retryAttempts) {
        for (let i = 0; i < attempts; i++) {
            try {
                const response = await fetch(url, {
                    timeout: 10000,
                    ...options
                });
                
                if (response.ok) {
                    return await response.json();
                }
                
                if (response.status === 404 && i === attempts - 1) {
                    throw new Error(`Data not found: ${url}`);
                }
                
            } catch (error) {
                console.log(`Attempt ${i + 1} failed for ${url}:`, error.message);
                
                if (i === attempts - 1) {
                    throw error;
                }
                
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * (i + 1)));
            }
        }
    }

    // Main data loading method with intelligent endpoint selection
    async loadSecurityData(clusterId) {
        if (!clusterId) {
            throw new Error('Cluster ID is required');
        }

        const cacheKey = `security_${clusterId}_${this.filters.timeRange}`;
        
        // Check cache first
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            const age = Date.now() - cached.timestamp;
            
            // Use cache if less than 2 minutes old
            if (age < 120000) {
                console.log('📋 Using cached security data');
                this.trackCacheHit();
                return cached.data;
            }
        }
        
        // Track cache miss
        this.trackCacheMiss();

        console.log('🔄 Fetching fresh security data...');

        // Try multiple endpoints in order of preference
        const endpoints = [
            `${this.apiBaseUrl}/results/${clusterId}`,
            `${this.apiBaseUrl}/overview?cluster_id=${clusterId}`,
            `/api/analysis/security/${clusterId}`,
            `/api/security/posture/${clusterId}`,
            // Fallback endpoints with cluster name variations
            `${this.apiBaseUrl}/results/${clusterId.split('_')[1] || clusterId}`,
            `${this.apiBaseUrl}/overview?cluster_id=${clusterId.split('_')[1] || clusterId}`
        ];

        let data = null;
        let successfulEndpoint = null;

        for (const endpoint of endpoints) {
            try {
                data = await this.fetchWithRetry(endpoint);
                if (data && Object.keys(data).length > 0) {
                    successfulEndpoint = endpoint;
                    console.log(`✅ Data loaded from: ${endpoint}`);
                    break;
                }
            } catch (error) {
                console.log(`❌ Failed endpoint: ${endpoint} - ${error.message}`);
            }
        }

        if (!data) {
            throw new Error('No security data available from any endpoint');
        }

        // Process and enhance the data
        const enhancedData = this.enhanceSecurityData(data);

        // Cache the data
        this.cache.set(cacheKey, {
            data: enhancedData,
            timestamp: Date.now(),
            endpoint: successfulEndpoint
        });

        return enhancedData;
    }

    // Enhance security data with additional calculations and filters
    enhanceSecurityData(rawData) {
        const data = JSON.parse(JSON.stringify(rawData)); // Deep clone
        const analysis = data.analysis || data;

        // Enhance security posture data
        if (analysis.security_posture) {
            analysis.security_posture = this.enhancePostureData(analysis.security_posture);
        }

        // Enhance compliance data
        if (analysis.compliance_frameworks) {
            analysis.compliance_frameworks = this.enhanceComplianceData(analysis.compliance_frameworks);
        }

        // Enhance policy compliance data
        if (analysis.policy_compliance) {
            analysis.policy_compliance = this.enhancePolicyData(analysis.policy_compliance);
        }

        // Add cross-references and correlations
        analysis.correlations = this.calculateCorrelations(analysis);

        // Add summary statistics
        analysis.summary = this.calculateSummaryStats(analysis);

        return data;
    }

    enhancePostureData(posture) {
        const alerts = posture.alerts || [];
        
        // Add alert statistics
        posture.alert_stats = {
            by_severity: this.groupBy(alerts, 'severity'),
            by_category: this.groupBy(alerts, 'category'),
            by_namespace: this.groupBy(alerts, 'namespace'),
            by_resource_type: this.groupBy(alerts, 'resource_type'),
            average_risk_score: alerts.length > 0 
                ? alerts.reduce((sum, a) => sum + (a.risk_score || 0), 0) / alerts.length 
                : 0
        };

        // Add trend analysis
        if (!posture.trends) {
            posture.trends = this.generateTrendAnalysis(alerts);
        }

        // Filter alerts based on current filters
        if (this.filters.severity !== 'all') {
            posture.filtered_alerts = this.filterAlertsBySeverity(alerts, this.filters.severity);
        }

        if (this.filters.category !== 'all') {
            posture.filtered_alerts = this.filterAlertsByCategory(
                posture.filtered_alerts || alerts, 
                this.filters.category
            );
        }

        return posture;
    }

    enhanceComplianceData(frameworks) {
        const enhanced = {};
        
        Object.entries(frameworks).forEach(([name, framework]) => {
            enhanced[name] = {
                ...framework,
                risk_level: this.calculateFrameworkRisk(framework),
                improvement_suggestions: this.generateImprovementSuggestions(framework),
                priority_controls: this.identifyPriorityControls(framework)
            };
        });

        return enhanced;
    }

    enhancePolicyData(policyCompliance) {
        const violations = policyCompliance.violations || [];
        
        // Add violation statistics
        policyCompliance.violation_stats = {
            by_severity: this.groupBy(violations, 'severity'),
            by_category: this.groupBy(violations, 'policy_category'),
            by_namespace: this.groupBy(violations, 'namespace'),
            auto_remediable_count: violations.filter(v => v.auto_remediable).length,
            manual_fix_required: violations.filter(v => !v.auto_remediable).length
        };

        // Calculate remediation complexity
        policyCompliance.remediation_complexity = this.calculateRemediationComplexity(violations);

        // Filter violations based on current filters
        if (this.filters.severity !== 'all') {
            policyCompliance.filtered_violations = this.filterViolationsBySeverity(violations, this.filters.severity);
        }

        return policyCompliance;
    }

    // Statistical and analysis methods
    groupBy(array, key) {
        return array.reduce((groups, item) => {
            const value = item[key] || 'Unknown';
            groups[value] = (groups[value] || 0) + 1;
            return groups;
        }, {});
    }

    filterAlertsBySeverity(alerts, severity) {
        const severityMap = {
            'critical': ['CRITICAL'],
            'high': ['CRITICAL', 'HIGH'],
            'medium': ['CRITICAL', 'HIGH', 'MEDIUM'],
            'all': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        };
        
        const allowedSeverities = severityMap[severity] || [];
        return alerts.filter(alert => allowedSeverities.includes(alert.severity));
    }

    filterAlertsByCategory(alerts, category) {
        if (category === 'all') return alerts;
        
        const categoryMap = {
            'vulnerability': ['VULNERABILITY'],
            'policy': ['POLICY'],
            'compliance': ['COMPLIANCE'],
            'rbac': ['RBAC', 'POLICY'],
            'network': ['NETWORK', 'EXPOSURE']
        };
        
        const allowedCategories = categoryMap[category] || [category.toUpperCase()];
        return alerts.filter(alert => allowedCategories.includes(alert.category));
    }

    filterViolationsBySeverity(violations, severity) {
        return this.filterAlertsBySeverity(violations, severity); // Same logic
    }

    calculateFrameworkRisk(framework) {
        const compliance = framework.overall_compliance || 0;
        const failedControls = framework.failed_controls || 0;
        
        if (compliance >= 90 && failedControls <= 2) return 'LOW';
        if (compliance >= 70 && failedControls <= 5) return 'MEDIUM';
        if (compliance >= 50) return 'HIGH';
        return 'CRITICAL';
    }

    generateImprovementSuggestions(framework) {
        const suggestions = [];
        const compliance = framework.overall_compliance || 0;
        const failedControls = framework.failed_controls || 0;
        
        if (compliance < 80) {
            suggestions.push('Focus on critical control implementation');
        }
        if (failedControls > 5) {
            suggestions.push('Prioritize automated compliance checks');
        }
        if (framework.control_details) {
            const criticalFailed = framework.control_details.filter(
                c => c.compliance_status === 'NON_COMPLIANT' && c.severity === 'CRITICAL'
            ).length;
            if (criticalFailed > 0) {
                suggestions.push(`Address ${criticalFailed} critical control failures immediately`);
            }
        }
        
        return suggestions;
    }

    identifyPriorityControls(framework) {
        if (!framework.control_details) return [];
        
        return framework.control_details
            .filter(c => c.compliance_status === 'NON_COMPLIANT')
            .sort((a, b) => {
                const severityWeight = { 'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };
                return (severityWeight[b.severity] || 0) - (severityWeight[a.severity] || 0);
            })
            .slice(0, 5); // Top 5 priority controls
    }

    calculateRemediationComplexity(violations) {
        const autoRemediable = violations.filter(v => v.auto_remediable).length;
        const total = violations.length;
        
        if (total === 0) return 'NONE';
        
        const autoPercentage = (autoRemediable / total) * 100;
        
        if (autoPercentage >= 80) return 'LOW';
        if (autoPercentage >= 50) return 'MEDIUM';
        if (autoPercentage >= 20) return 'HIGH';
        return 'CRITICAL';
    }

    generateTrendAnalysis(alerts) {
        // Calculate trend analysis from real alert data only
        const severityWeights = { 'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };
        const totalRisk = alerts.reduce((sum, alert) => 
            sum + (severityWeights[alert.severity] || 1), 0);
        
        // Determine trend based on current alert distribution
        const criticalCount = alerts.filter(a => a.severity === 'CRITICAL').length;
        const trend = criticalCount === 0 ? 'improving' : 
                     criticalCount > 3 ? 'declining' : 'stable';
        
        return {
            trend,
            current_score: Math.max(0, 100 - (totalRisk * 5)), // Convert risk to score
            alert_count: alerts.length,
            compliance_score: null, // Will be calculated from real compliance data
            data_points: alerts.length,
            component_trends: this.extractComponentTrends(alerts),
            time_range: {
                oldest: this.getOldestAlertTime(alerts),
                newest: new Date().toISOString()
            }
        };
    }
    
    extractComponentTrends(alerts) {
        // Extract trends from real alert categories
        const categories = this.groupBy(alerts, 'category');
        const trends = {};
        
        Object.entries(categories).forEach(([category, count]) => {
            trends[category.toLowerCase()] = count > 2 ? 'declining' : 
                                           count === 0 ? 'improving' : 'stable';
        });
        
        return trends;
    }
    
    getOldestAlertTime(alerts) {
        if (alerts.length === 0) return new Date().toISOString();
        
        const times = alerts
            .map(a => a.detected_at)
            .filter(t => t)
            .sort();
            
        return times[0] || new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    }

    calculateCorrelations(analysis) {
        const correlations = {};
        
        // Correlation between alerts and compliance
        const alerts = analysis.security_posture?.alerts || [];
        const frameworks = analysis.compliance_frameworks || {};
        
        const criticalAlerts = alerts.filter(a => a.severity === 'CRITICAL').length;
        const avgCompliance = Object.values(frameworks).length > 0
            ? Object.values(frameworks).reduce((sum, f) => sum + (f.overall_compliance || 0), 0) / Object.values(frameworks).length
            : 0;
        
        correlations.alerts_compliance_correlation = {
            critical_alerts: criticalAlerts,
            average_compliance: avgCompliance,
            correlation_strength: criticalAlerts > 0 && avgCompliance < 70 ? 'HIGH' : 'LOW',
            insight: criticalAlerts > 5 ? 'High alert count indicates compliance gaps' : 
                    avgCompliance > 85 ? 'Good compliance reduces security risks' :
                    'Monitor both metrics for comprehensive security'
        };

        // Namespace risk concentration
        const namespaceRisks = {};
        alerts.forEach(alert => {
            const ns = alert.namespace || 'default';
            namespaceRisks[ns] = (namespaceRisks[ns] || 0) + (alert.risk_score || 1);
        });

        correlations.namespace_risk_distribution = namespaceRisks;
        correlations.highest_risk_namespace = Object.entries(namespaceRisks)
            .sort(([,a], [,b]) => b - a)[0]?.[0] || 'none';

        return correlations;
    }

    calculateSummaryStats(analysis) {
        const posture = analysis.security_posture || {};
        const compliance = analysis.policy_compliance || {};
        const frameworks = analysis.compliance_frameworks || {};
        
        const alerts = posture.alerts || [];
        const violations = compliance.violations || [];
        
        return {
            total_issues: alerts.length + violations.length,
            critical_issues: alerts.filter(a => a.severity === 'CRITICAL').length + 
                           violations.filter(v => v.severity === 'CRITICAL').length,
            auto_remediable_issues: violations.filter(v => v.auto_remediable).length,
            compliance_grade: this.calculateOverallComplianceGrade(frameworks),
            risk_level: this.calculateOverallRiskLevel(alerts, violations),
            improvement_potential: this.calculateImprovementPotential(analysis),
            next_actions: this.generateNextActions(analysis)
        };
    }

    calculateOverallComplianceGrade(frameworks) {
        const scores = Object.values(frameworks).map(f => f.overall_compliance || 0);
        if (scores.length === 0) return 'N/A';
        
        const avg = scores.reduce((sum, score) => sum + score, 0) / scores.length;
        
        if (avg >= 95) return 'A+';
        if (avg >= 90) return 'A';
        if (avg >= 85) return 'A-';
        if (avg >= 80) return 'B+';
        if (avg >= 75) return 'B';
        if (avg >= 70) return 'B-';
        if (avg >= 65) return 'C+';
        if (avg >= 60) return 'C';
        if (avg >= 55) return 'C-';
        if (avg >= 50) return 'D';
        return 'F';
    }

    calculateOverallRiskLevel(alerts, violations) {
        const criticalCount = alerts.filter(a => a.severity === 'CRITICAL').length + 
                            violations.filter(v => v.severity === 'CRITICAL').length;
        const highCount = alerts.filter(a => a.severity === 'HIGH').length + 
                         violations.filter(v => v.severity === 'HIGH').length;
        
        if (criticalCount > 5) return 'CRITICAL';
        if (criticalCount > 0 || highCount > 10) return 'HIGH';
        if (highCount > 0) return 'MEDIUM';
        return 'LOW';
    }

    calculateImprovementPotential(analysis) {
        const violations = analysis.policy_compliance?.violations || [];
        const autoRemediable = violations.filter(v => v.auto_remediable).length;
        const frameworks = analysis.compliance_frameworks || {};
        
        const avgCompliance = Object.values(frameworks).length > 0
            ? Object.values(frameworks).reduce((sum, f) => sum + (f.overall_compliance || 0), 0) / Object.values(frameworks).length
            : 0;
        
        const potential = (100 - avgCompliance) + (autoRemediable * 5);
        
        if (potential > 30) return 'HIGH';
        if (potential > 15) return 'MEDIUM';
        if (potential > 5) return 'LOW';
        return 'MINIMAL';
    }

    generateNextActions(analysis) {
        const actions = [];
        const alerts = analysis.security_posture?.alerts || [];
        const violations = analysis.policy_compliance?.violations || [];
        const criticalAlerts = alerts.filter(a => a.severity === 'CRITICAL');
        const autoRemediable = violations.filter(v => v.auto_remediable);
        
        if (criticalAlerts.length > 0) {
            actions.push({
                priority: 'CRITICAL',
                action: `Address ${criticalAlerts.length} critical security alerts`,
                estimated_time: `${criticalAlerts.length * 30} minutes`,
                impact: 'HIGH'
            });
        }
        
        if (autoRemediable.length > 0) {
            actions.push({
                priority: 'HIGH',
                action: `Auto-fix ${autoRemediable.length} policy violations`,
                estimated_time: `${autoRemediable.length * 5} minutes`,
                impact: 'MEDIUM'
            });
        }
        
        const frameworks = analysis.compliance_frameworks || {};
        const lowCompliance = Object.entries(frameworks)
            .filter(([, f]) => (f.overall_compliance || 0) < 70);
        
        if (lowCompliance.length > 0) {
            actions.push({
                priority: 'MEDIUM',
                action: `Improve compliance for ${lowCompliance.map(([name]) => name).join(', ')}`,
                estimated_time: '2-4 hours',
                impact: 'HIGH'
            });
        }
        
        return actions.slice(0, 5); // Top 5 actions
    }

    // Filter management
    setFilter(filterType, value) {
        this.filters[filterType] = value;
        console.log(`🔍 Filter applied: ${filterType} = ${value}`);
        
        // Invalidate relevant cache entries
        this.invalidateCache(filterType);
        
        // Notify all callbacks about filter change
        this.notifyFilterChange(filterType, value);
    }

    getFilters() {
        return { ...this.filters };
    }

    resetFilters() {
        this.filters = {
            timeRange: '30d',
            severity: 'all',
            category: 'all'
        };
        console.log('🔄 Filters reset to defaults');
        
        // Clear cache to force refresh
        this.cache.clear();
        
        // Notify callbacks
        this.refreshCallbacks.forEach(callback => {
            try {
                callback(null, 'filters_reset');
            } catch (error) {
                console.error('Error in refresh callback:', error);
            }
        });
    }

    // Real-time update management
    onDataUpdate(callback) {
        if (typeof callback === 'function') {
            this.refreshCallbacks.add(callback);
        }
    }

    offDataUpdate(callback) {
        this.refreshCallbacks.delete(callback);
    }

    notifyDataUpdate(data, updateType = 'refresh') {
        console.log(`📡 Notifying ${this.refreshCallbacks.size} callbacks of data update`);
        
        this.refreshCallbacks.forEach(callback => {
            try {
                callback(data, updateType);
            } catch (error) {
                console.error('Error in data update callback:', error);
            }
        });
    }

    notifyFilterChange(filterType, value) {
        this.refreshCallbacks.forEach(callback => {
            try {
                callback(null, 'filter_change', { filterType, value });
            } catch (error) {
                console.error('Error in filter change callback:', error);
            }
        });
    }

    // Cache management
    invalidateCache(filterType = null) {
        if (filterType === 'timeRange') {
            // Clear all cache when time range changes
            this.cache.clear();
        } else {
            // Clear specific cache entries for other filters
            const keysToDelete = [];
            this.cache.forEach((value, key) => {
                if (key.includes('filtered') || key.includes(filterType)) {
                    keysToDelete.push(key);
                }
            });
            keysToDelete.forEach(key => this.cache.delete(key));
        }
    }

    startCacheCleanup() {
        // Clean old cache entries every 10 minutes
        setInterval(() => {
            const now = Date.now();
            const maxAge = 600000; // 10 minutes
            
            const keysToDelete = [];
            this.cache.forEach((value, key) => {
                if (now - value.timestamp > maxAge) {
                    keysToDelete.push(key);
                }
            });
            
            keysToDelete.forEach(key => this.cache.delete(key));
            
            if (keysToDelete.length > 0) {
                console.log(`🧹 Cleaned ${keysToDelete.length} old cache entries`);
            }
        }, 600000);
    }

    // Data export methods
    async exportSecurityData(clusterId, format = 'json') {
        try {
            const data = await this.loadSecurityData(clusterId);
            
            if (format === 'csv') {
                return this.convertToCSV(data);
            } else if (format === 'excel') {
                return this.convertToExcel(data);
            }
            
            return JSON.stringify(data, null, 2);
        } catch (error) {
            console.error('Failed to export security data:', error);
            throw error;
        }
    }

    convertToCSV(data) {
        const analysis = data.analysis || data;
        const alerts = analysis.security_posture?.alerts || [];
        const violations = analysis.policy_compliance?.violations || [];
        
        // Create CSV for alerts
        const alertsCSV = [
            'Type,Severity,Category,Title,Description,Resource,Namespace,Risk Score,Detected At',
            ...alerts.map(alert => [
                'Alert',
                alert.severity,
                alert.category,
                `"${alert.title}"`,
                `"${alert.description}"`,
                alert.resource_name,
                alert.namespace || 'default',
                alert.risk_score || 0,
                alert.detected_at || new Date().toISOString()
            ].join(','))
        ];
        
        // Add violations
        const violationsRows = violations.map(violation => [
            'Violation',
            violation.severity,
            violation.policy_category,
            `"${violation.policy_name}"`,
            `"${violation.violation_description}"`,
            violation.resource_name,
            violation.namespace || 'default',
            violation.risk_score || 0,
            violation.detected_at || new Date().toISOString()
        ].join(','));
        
        return [...alertsCSV, ...violationsRows].join('\n');
    }

    // Fetch real historical data from backend
    async fetchHistoricalData(clusterId, days = 30) {
        try {
            const response = await this.fetchWithRetry(
                `${this.apiBaseUrl}/trends/${clusterId}?days=${days}`
            );
            
            if (response && response.historical_data) {
                return response.historical_data;
            }
            
            // If no historical data available, return current state as single point
            return this.createCurrentStateHistoricalPoint();
            
        } catch (error) {
            console.log('No historical data available:', error.message);
            return this.createCurrentStateHistoricalPoint();
        }
    }
    
    createCurrentStateHistoricalPoint() {
        // Create a single data point from current state when no historical data exists
        const now = new Date();
        return [{
            date: now.toISOString().split('T')[0],
            security_score: null, // Will be filled from current analysis
            alert_count: null,
            compliance_score: null,
            critical_issues: null,
            resolved_issues: 0
        }];
    }

    // Real-time data streaming (placeholder for future WebSocket implementation)
    startRealTimeUpdates(clusterId) {
        console.log('🔴 Real-time updates started for cluster:', clusterId);
        
        // Simulate real-time updates every 30 seconds
        const realTimeInterval = setInterval(async () => {
            try {
                // In a real implementation, this would use WebSocket or Server-Sent Events
                const latestData = await this.loadSecurityData(clusterId);
                this.notifyDataUpdate(latestData, 'real_time');
            } catch (error) {
                console.log('Real-time update failed:', error.message);
            }
        }, 30000);
        
        return realTimeInterval;
    }

    stopRealTimeUpdates(intervalId) {
        if (intervalId) {
            clearInterval(intervalId);
            console.log('🔴 Real-time updates stopped');
        }
    }

    // Performance monitoring
    getPerformanceMetrics() {
        return {
            cache_size: this.cache.size,
            cache_hit_ratio: this.calculateCacheHitRatio(),
            active_callbacks: this.refreshCallbacks.size,
            last_fetch_time: this.lastFetchTime || null,
            average_response_time: this.averageResponseTime || null
        };
    }

    calculateCacheHitRatio() {
        // Calculate actual cache hit ratio from tracked metrics
        if (!this.cacheStats) {
            this.cacheStats = { hits: 0, misses: 0 };
        }
        
        const total = this.cacheStats.hits + this.cacheStats.misses;
        return total > 0 ? this.cacheStats.hits / total : 0;
    }
    
    trackCacheHit() {
        if (!this.cacheStats) this.cacheStats = { hits: 0, misses: 0 };
        this.cacheStats.hits++;
    }
    
    trackCacheMiss() {
        if (!this.cacheStats) this.cacheStats = { hits: 0, misses: 0 };
        this.cacheStats.misses++;
    }

    // Cleanup
    destroy() {
        this.cache.clear();
        this.refreshCallbacks.clear();
        console.log('🗑️ Enhanced Security Data Manager destroyed');
    }
}

// Initialize enhanced data manager
window.enhancedSecurityDataManager = new EnhancedSecurityDataManager();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedSecurityDataManager;
}

window.EnhancedSecurityDataManager = EnhancedSecurityDataManager;