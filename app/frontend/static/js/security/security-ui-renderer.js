/**
 * Security UI Renderer - User Interface and Visualization
 * ======================================================
 * Handles all UI rendering, layout generation, and visual presentation for security dashboard
 */

// Initialize global cluster state if not exists
window.currentClusterState = window.currentClusterState || {
    clusterId: null,
    lastUpdated: null,
    validated: false
};

class SecurityUIRenderer {
    constructor() {
        this.dataManager = new window.SecurityDataManager();
        this.init();
    }

    async init() {
        console.log('🔒 Initializing Security UI Renderer...');
        
        // Check if we're on the security posture page
        if (document.getElementById('securityposture-content')) {
            await this.initializeSecurityDashboard();
            this.dataManager.startAutoRefresh((data) => {
                this.updateDashboardFromData(data);
            });
        }
        
        console.log('✅ Security UI Renderer initialized');
    }

    async initializeSecurityDashboard() {
        // Create dashboard layout if it doesn't exist
        this.createDashboardLayout();
        
        // Load initial data
        const data = await this.dataManager.loadSecurityOverview();
        if (data) {
            this.updateDashboardFromData(data);
            
            // Initialize security charts using global charts module
            if (window.securityCharts) {
                window.securityCharts.initializeSecurityCharts(data);
            }
        } else {
            this.showNoDataMessage('Security analysis data not available. Please run a cluster analysis.');
        }
    }

    async updateDashboardFromData(data) {
        // Update UI with the enhanced data display
        if (data.analysis || data.security_posture) {
            this.updateEnhancedSecurityOverview(data);
        } else {
            this.updateSecurityOverview(data);
        }
        
        // Load all components with the cached data
        await Promise.all([
            this.displayAlertsFromData(),
            this.displayViolationsFromData(),
            this.displayComplianceFromData(),
            this.displayVulnerabilitiesFromData()
        ]).catch(error => {
            console.error('⚠️ Some additional security data failed to load:', error);
        });
    }

    createDashboardLayout() {
        const container = document.getElementById('securityposture-content');
        if (!container) {
            console.warn('Security posture content container not found');
            return;
        }

        // Check if layout already exists
        if (container.querySelector('.security-dashboard-layout')) {
            return;
        }

        // Create the enhanced dashboard structure
        const dashboardHTML = `
            <div class="security-dashboard-layout">
                <!-- Tab Navigation -->
                <div class="border-b border-slate-700 mb-6">
                    <nav class="flex space-x-8 overflow-x-auto">
                        <button class="security-tab-btn active whitespace-nowrap" data-tab="overview">
                            <i class="fas fa-chart-line mr-2"></i>Overview
                        </button>
                        <button class="security-tab-btn whitespace-nowrap" data-tab="alerts">
                            <i class="fas fa-exclamation-triangle mr-2"></i>Alerts
                            <span id="alerts-badge" class="ml-2 px-2 py-0.5 bg-red-600 text-white text-xs rounded-full hidden">0</span>
                        </button>
                        <button class="security-tab-btn whitespace-nowrap" data-tab="violations">
                            <i class="fas fa-ban mr-2"></i>Policy Violations
                            <span id="violations-badge" class="ml-2 px-2 py-0.5 bg-orange-600 text-white text-xs rounded-full hidden">0</span>
                        </button>
                        <button class="security-tab-btn whitespace-nowrap" data-tab="compliance">
                            <i class="fas fa-clipboard-check mr-2"></i>Compliance
                        </button>
                        <button class="security-tab-btn whitespace-nowrap" data-tab="vulnerabilities">
                            <i class="fas fa-bug mr-2"></i>Vulnerabilities
                        </button>
                        <button class="security-tab-btn whitespace-nowrap" data-tab="trends">
                            <i class="fas fa-chart-area mr-2"></i>Trends
                        </button>
                        <button class="security-tab-btn whitespace-nowrap" data-tab="audit">
                            <i class="fas fa-history mr-2"></i>Audit Trail
                        </button>
                    </nav>
                </div>

                <!-- Tab Content -->
                <div class="security-tab-content">
                    <!-- Overview Tab -->
                    <div id="overview-tab" class="security-tab-pane active">
                        <!-- Executive Security Dashboard -->
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                            <div class="p-4 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <div class="flex items-center justify-between mb-3">
                                    <span style="color: rgb(148, 163, 184); font-size: 0.875rem; font-weight: 500;">SECURITY SCORE</span>
                                    <div style="width: 2rem; height: 2rem; background: rgba(59, 130, 246, 0.2); border-radius: 6px; display: flex; align-items: center; justify-content: center;">
                                        <i class="fas fa-shield-alt" style="color: rgb(96, 165, 250);"></i>
                                    </div>
                                </div>
                                <div id="security-score" class="text-3xl font-bold text-white mb-1">--</div>
                                <div id="security-grade" style="color: rgb(148, 163, 184); font-size: 0.75rem;">Loading...</div>
                                <div id="security-trend" style="font-size: 0.75rem; margin-top: 0.5rem;"></div>
                            </div>

                            <div class="p-4 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <div class="flex items-center justify-between mb-3">
                                    <span style="color: rgb(148, 163, 184); font-size: 0.875rem; font-weight: 500;">ACTIVE ALERTS</span>
                                    <div style="width: 2rem; height: 2rem; background: rgba(239, 68, 68, 0.2); border-radius: 6px; display: flex; align-items: center; justify-content: center;">
                                        <i class="fas fa-exclamation-triangle" style="color: rgb(248, 113, 113);"></i>
                                    </div>
                                </div>
                                <div id="total-alerts" class="text-3xl font-bold text-white mb-1">0</div>
                                <div style="font-size: 0.75rem; margin-top: 0.25rem;">
                                    <span id="critical-alerts-count" style="color: rgb(248, 113, 113);">0 Critical</span>
                                    <span style="color: rgb(148, 163, 184); margin: 0 0.25rem;">•</span>
                                    <span id="high-alerts-count" style="color: rgb(251, 146, 60);">0 High</span>
                                </div>
                            </div>

                            <div class="p-4 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <div class="flex items-center justify-between mb-3">
                                    <span style="color: rgb(148, 163, 184); font-size: 0.875rem; font-weight: 500;">VIOLATIONS</span>
                                    <div style="width: 2rem; height: 2rem; background: rgba(251, 146, 60, 0.2); border-radius: 6px; display: flex; align-items: center; justify-content: center;">
                                        <i class="fas fa-ban" style="color: rgb(251, 146, 60);"></i>
                                    </div>
                                </div>
                                <div id="total-violations" class="text-3xl font-bold text-white mb-1">0</div>
                                <div style="font-size: 0.75rem; margin-top: 0.25rem;">
                                    <span id="critical-violations-count" style="color: rgb(248, 113, 113);">0 Critical</span>
                                    <span style="color: rgb(148, 163, 184); margin: 0 0.25rem;">•</span>
                                    <span id="high-violations-count" style="color: rgb(251, 146, 60);">0 High</span>
                                </div>
                            </div>

                            <div class="p-4 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <div class="flex items-center justify-between mb-3">
                                    <span style="color: rgb(148, 163, 184); font-size: 0.875rem; font-weight: 500;">COMPLIANCE</span>
                                    <div style="width: 2rem; height: 2rem; background: rgba(34, 197, 94, 0.2); border-radius: 6px; display: flex; align-items: center; justify-content: center;">
                                        <i class="fas fa-clipboard-check" style="color: rgb(74, 222, 128);"></i>
                                    </div>
                                </div>
                                <div id="compliance-score" class="text-3xl font-bold text-white mb-1">--</div>
                                <div style="color: rgb(148, 163, 184); font-size: 0.75rem; margin-top: 0.25rem;">Policy adherence</div>
                                <div id="frameworks-status" style="font-size: 0.75rem; margin-top: 0.5rem;"></div>
                            </div>
                        </div>

                        <!-- Security Analytics Dashboard -->
                        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                            <!-- Security Trend Chart -->
                            <div class="lg:col-span-2 p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <div class="flex items-center justify-between mb-4">
                                    <h3 class="text-lg font-semibold text-white">Security Posture Trend</h3>
                                    <div class="flex items-center gap-2">
                                        <div style="width: 8px; height: 8px; background: rgb(96, 165, 250); border-radius: 50%;"></div>
                                        <span style="color: rgb(148, 163, 184); font-size: 0.75rem;">Score</span>
                                        <div style="width: 8px; height: 8px; background: rgb(248, 113, 113); border-radius: 50%; margin-left: 1rem;"></div>
                                        <span style="color: rgb(148, 163, 184); font-size: 0.75rem;">Alerts</span>
                                    </div>
                                </div>
                                <div class="chart-container">
                                    <canvas id="security-trend-chart"></canvas>
                                </div>
                            </div>
                            
                            <!-- Risk Level Distribution -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">Risk Distribution</h3>
                                <div class="chart-container">
                                    <canvas id="risk-donut-chart"></canvas>
                                </div>
                                <div id="risk-distribution" class="mt-4 space-y-2">
                                    <div class="text-center" style="color: rgb(148, 163, 184); font-size: 0.75rem;">Loading risk data...</div>
                                </div>
                            </div>
                        </div>

                        <!-- Compliance Framework Status -->
                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">Security Components</h3>
                                <div id="security-breakdown" class="space-y-3">
                                    <div class="text-center" style="color: rgb(148, 163, 184); padding: 1rem;">Loading security data...</div>
                                </div>
                            </div>
                            
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">Compliance Status</h3>
                                <div class="chart-container">
                                    <canvas id="compliance-bar-chart" style="width: 100%; height: 200px;"></canvas>
                                </div>
                                <div id="compliance-details" class="mt-4 space-y-2">
                                    <div class="text-center" style="color: rgb(148, 163, 184); font-size: 0.75rem;">Loading compliance data...</div>
                                </div>
                            </div>
                        </div>

                        <!-- Critical Findings Summary -->
                        <div id="critical-findings-summary" class="mb-8"></div>

                        <!-- Recent Alerts -->
                        <div id="security-alerts-container"></div>
                        
                        <!-- Recent Violations -->
                        <div id="recent-violations-container"></div>
                    </div>

                    <!-- Alerts Tab -->
                    <div id="alerts-tab" class="security-tab-pane hidden">
                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                            <!-- Dynamic Alerts Chart -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <div class="flex items-center justify-between mb-4">
                                    <h3 class="text-lg font-semibold text-white">Alerts Distribution</h3>
                                    <select id="alert-chart-view" style="background: rgba(51, 65, 85, 0.8); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.5rem; border-radius: 4px;">
                                        <option value="severity">By Severity</option>
                                        <option value="category">By Category</option>
                                        <option value="status">By Status</option>
                                    </select>
                                </div>
                                <div class="chart-container">
                                    <canvas id="dynamic-alerts-chart" style="width: 100%; height: 300px;"></canvas>
                                </div>
                            </div>
                            
                            <!-- Alert Summary Stats -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">Alert Summary</h3>
                                <div id="alerts-summary-stats" class="space-y-4">
                                    <!-- Stats will be populated dynamically -->
                                </div>
                            </div>
                        </div>
                        
                        <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                            <div class="flex justify-between items-center mb-4">
                                <h3 class="text-lg font-semibold text-white">Recent Alerts</h3>
                                <div class="flex space-x-2">
                                    <select id="alert-severity-filter" style="background: rgba(51, 65, 85, 0.8); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.5rem; border-radius: 4px;">
                                        <option value="">All Severities</option>
                                        <option value="CRITICAL">Critical</option>
                                        <option value="HIGH">High</option>
                                        <option value="MEDIUM">Medium</option>
                                        <option value="LOW">Low</option>
                                    </select>
                                </div>
                            </div>
                            <div id="alerts-list" class="space-y-3 max-h-96 overflow-y-auto"></div>
                        </div>
                    </div>

                    <!-- Policy Violations Tab -->
                    <div id="violations-tab" class="security-tab-pane hidden">
                        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                            <!-- Violations by Severity -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">By Severity</h3>
                                <div class="chart-container">
                                    <canvas id="violations-severity-chart" style="width: 100%; height: 200px;"></canvas>
                                </div>
                            </div>
                            
                            <!-- Violations by Category -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">By Category</h3>
                                <div class="chart-container">
                                    <canvas id="violations-category-chart" style="width: 100%; height: 200px;"></canvas>
                                </div>
                            </div>
                            
                            <!-- Violations by Policy Type -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">By Policy Type</h3>
                                <div class="chart-container">
                                    <canvas id="violations-policy-chart" style="width: 100%; height: 200px;"></canvas>
                                </div>
                            </div>
                        </div>
                        
                        <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                            <div class="flex justify-between items-center mb-4">
                                <h3 class="text-lg font-semibold text-white">Recent Violations</h3>
                                <div class="flex space-x-2">
                                    <select id="violation-severity-filter" style="background: rgba(51, 65, 85, 0.8); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.5rem; border-radius: 4px;">
                                        <option value="">All Severities</option>
                                        <option value="CRITICAL">Critical</option>
                                        <option value="HIGH">High</option>
                                        <option value="MEDIUM">Medium</option>
                                        <option value="LOW">Low</option>
                                    </select>
                                </div>
                            </div>
                            <div id="violations-list" class="space-y-3 max-h-96 overflow-y-auto"></div>
                        </div>
                    </div>

                    <!-- Compliance Tab -->
                    <div id="compliance-tab" class="security-tab-pane hidden">
                        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                            <!-- Overall Compliance Score -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">Overall Score</h3>
                                <div class="chart-container">
                                    <canvas id="compliance-overall-chart" style="width: 100%; height: 200px;"></canvas>
                                </div>
                            </div>
                            
                            <!-- Framework Compliance -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">By Framework</h3>
                                <div class="chart-container">
                                    <canvas id="compliance-framework-chart" style="width: 100%; height: 200px;"></canvas>
                                </div>
                            </div>
                            
                            <!-- Control Status -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">Control Status</h3>
                                <div class="chart-container">
                                    <canvas id="compliance-controls-chart" style="width: 100%; height: 200px;"></canvas>
                                </div>
                            </div>
                        </div>
                        
                        <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                            <h3 class="text-lg font-semibold text-white mb-4">Framework Details</h3>
                            <div id="compliance-frameworks" class="space-y-4 max-h-96 overflow-y-auto"></div>
                        </div>
                    </div>

                    <!-- Vulnerabilities Tab -->
                    <div id="vulnerabilities-tab" class="security-tab-pane hidden">
                        <div id="vulnerability-summary" class="mb-6"></div>
                        <div id="vulnerability-list" class="space-y-4"></div>
                    </div>

                    <!-- Trends Tab -->
                    <div id="trends-tab" class="security-tab-pane hidden">
                        <!-- Trend Analytics Dashboard -->
                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                            <!-- Security Score Over Time -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">Security Score Trend</h3>
                                <div class="chart-container">
                                    <canvas id="score-trend-line-chart" style="width: 100%; height: 250px;"></canvas>
                                </div>
                            </div>
                            
                            <!-- Alert Volume Trend -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">Alert Volume Trend</h3>
                                <div class="chart-container">
                                    <canvas id="alert-volume-chart" style="width: 100%; height: 250px;"></canvas>
                                </div>
                            </div>
                        </div>
                        
                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                            <!-- Compliance Trend -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">Compliance Progress</h3>
                                <div class="chart-container">
                                    <canvas id="compliance-trend-chart" style="width: 100%; height: 250px;"></canvas>
                                </div>
                            </div>
                            
                            <!-- Risk Level Changes -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">Risk Level Changes</h3>
                                <div class="chart-container">
                                    <canvas id="risk-trend-chart" style="width: 100%; height: 250px;"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Audit Trail Tab -->
                    <div id="audit-tab" class="security-tab-pane hidden">
                        <div id="audit-trail-list" class="space-y-4"></div>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = dashboardHTML;

        // Set up tab switching
        this.setupTabSwitching();
    }

    setupTabSwitching() {
        const tabButtons = document.querySelectorAll('.security-tab-btn');
        const tabPanes = document.querySelectorAll('.security-tab-pane');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;

                // Update button states
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');

                // Update pane visibility
                tabPanes.forEach(pane => {
                    if (pane.id === `${targetTab}-tab`) {
                        pane.classList.remove('hidden');
                        
                        // Load tab-specific data when switching
                        this.loadTabData(targetTab);
                    } else {
                        pane.classList.add('hidden');
                    }
                });
            });
        });

        // Set up filters
        this.setupFilters();
    }

    setupFilters() {
        // Alert filters
        const alertSeverityFilter = document.getElementById('alert-severity-filter');
        
        if (alertSeverityFilter) {
            alertSeverityFilter.addEventListener('change', () => {
                this.filterAlertsUI();
            });
        }

        // Violation filters
        const violationSeverityFilter = document.getElementById('violation-severity-filter');
        
        if (violationSeverityFilter) {
            violationSeverityFilter.addEventListener('change', () => {
                this.filterViolationsUI();
            });
        }
    }

    async loadTabData(tab) {
        switch(tab) {
            case 'alerts':
                await this.displayAlertsFromData();
                break;
            case 'violations':
                await this.displayViolationsFromData();
                break;
            case 'compliance':
                await this.displayComplianceFromData();
                break;
            case 'vulnerabilities':
                await this.displayVulnerabilitiesFromData();
                break;
            case 'trends':
                await this.displayTrendsFromData();
                break;
            case 'audit':
                await this.displayAuditTrailFromData();
                break;
        }
    }

    updateEnhancedSecurityOverview(data) {
        try {
            // Handle both direct analysis data and wrapped data
            const analysis = data.analysis || data;
            const posture = analysis.security_posture || {};
            const policyCompliance = analysis.policy_compliance || {};
            const complianceFrameworks = analysis.compliance_frameworks || {};
            
            // Update security score with color coding
            const scoreElement = document.getElementById('security-score');
            if (scoreElement) {
                const score = Math.round(posture.overall_score || 0);
                scoreElement.textContent = `${score}%`;
                
                // Update color based on score
                scoreElement.className = 'text-2xl font-bold';
                if (score >= 80) {
                    scoreElement.classList.add('text-green-400');
                } else if (score >= 60) {
                    scoreElement.classList.add('text-yellow-400');
                } else {
                    scoreElement.classList.add('text-red-400');
                }
            }

            // Update grade
            const gradeElement = document.getElementById('security-grade');
            if (gradeElement) {
                gradeElement.textContent = `Grade: ${posture.grade || 'N/A'}`;
            }

            // Update trend with detailed information
            const trendElement = document.getElementById('security-trend');
            if (trendElement && posture.trends) {
                const trend = posture.trends.trend || 'stable';
                const change = posture.trends.change || 0;
                const trendIcon = trend === 'improving' ? '↑' : trend === 'declining' ? '↓' : '→';
                const trendColor = trend === 'improving' ? 'text-green-400' : trend === 'declining' ? 'text-red-400' : 'text-yellow-400';
                
                trendElement.innerHTML = `
                    <span class="text-slate-400">Trend: </span>
                    <span class="ml-1 ${trendColor}">${trendIcon} ${trend} (${change > 0 ? '+' : ''}${change.toFixed(1)}%)</span>
                `;
            }

            // Update alerts count with breakdown
            const totalAlertsElement = document.getElementById('total-alerts');
            const criticalAlertsCount = document.getElementById('critical-alerts-count');
            const highAlertsCount = document.getElementById('high-alerts-count');
            
            if (totalAlertsElement && posture.alerts) {
                const alerts = posture.alerts || [];
                const criticalCount = alerts.filter(a => a.severity === 'CRITICAL').length;
                const highCount = alerts.filter(a => a.severity === 'HIGH').length;
                
                totalAlertsElement.textContent = posture.alerts_count || alerts.length;
                
                if (criticalAlertsCount) {
                    criticalAlertsCount.textContent = `${criticalCount} Critical`;
                }
                if (highAlertsCount) {
                    highAlertsCount.textContent = `${highCount} High`;
                }
                
                // Update badge
                const alertsBadge = document.getElementById('alerts-badge');
                if (alertsBadge && alerts.length > 0) {
                    alertsBadge.textContent = alerts.length;
                    alertsBadge.classList.remove('hidden');
                }
            }

            // Update violations count with breakdown
            const totalViolationsElement = document.getElementById('total-violations');
            const criticalViolationsCount = document.getElementById('critical-violations-count');
            const highViolationsCount = document.getElementById('high-violations-count');
            
            if (totalViolationsElement && policyCompliance) {
                const violations = policyCompliance.violations || [];
                const violationsBySeverity = policyCompliance.violations_by_severity || {};
                
                totalViolationsElement.textContent = policyCompliance.violations_count || violations.length;
                
                if (criticalViolationsCount) {
                    criticalViolationsCount.textContent = `${violationsBySeverity.CRITICAL || 0} Critical`;
                }
                if (highViolationsCount) {
                    highViolationsCount.textContent = `${violationsBySeverity.HIGH || 0} High`;
                }
                
                // Update badge
                const violationsBadge = document.getElementById('violations-badge');
                if (violationsBadge && violations.length > 0) {
                    violationsBadge.textContent = violations.length;
                    violationsBadge.classList.remove('hidden');
                }
            }

            // Update compliance with framework details
            const complianceElement = document.getElementById('compliance-score');
            const frameworksStatus = document.getElementById('frameworks-status');
            
            if (complianceElement) {
                const compliance = Math.round(policyCompliance.overall_compliance || 0);
                complianceElement.textContent = `${compliance}%`;
            }
            
            if (frameworksStatus && complianceFrameworks) {
                const frameworksSummary = Object.entries(complianceFrameworks)
                    .map(([name, data]) => `${name}: ${data.grade || 'N/A'}`)
                    .join(' • ');
                frameworksStatus.innerHTML = `<span class="text-slate-400">${frameworksSummary}</span>`;
            }

            // Update security breakdown with enhanced visualization
            this.updateEnhancedBreakdown(posture.breakdown);
            
            // Add critical findings summary
            this.updateCriticalFindings(posture.alerts, policyCompliance.violations);

            console.log('✅ Enhanced security overview updated successfully');
            
        } catch (error) {
            console.error('❌ Failed to update enhanced security overview:', error);
        }
    }

    updateEnhancedBreakdown(breakdown) {
        const breakdownContainer = document.getElementById('security-breakdown');
        if (!breakdownContainer || !breakdown) return;

        const breakdownHtml = Object.entries(breakdown).map(([key, value]) => {
            const label = key.replace('_score', '').replace(/_/g, ' ').toUpperCase();
            const percentage = Math.round(value);
            const color = percentage >= 80 ? 'green' : percentage >= 60 ? 'yellow' : 'red';
            
            // Add icons for each component
            const icons = {
                'RBAC': 'fa-user-shield',
                'NETWORK': 'fa-network-wired',
                'ENCRYPTION': 'fa-lock',
                'VULNERABILITY': 'fa-bug',
                'COMPLIANCE': 'fa-clipboard-check',
                'DRIFT': 'fa-code-branch'
            };
            const icon = icons[label.replace(' SCORE', '')] || 'fa-shield-alt';

            return `
                <div class="flex items-center justify-between py-2">
                    <div class="flex items-center space-x-2">
                        <i class="fas ${icon} text-slate-400 w-5"></i>
                        <span class="text-sm text-slate-300">${label}</span>
                    </div>
                    <div class="flex items-center space-x-3">
                        <div class="w-32 bg-slate-700 rounded-full h-2">
                            <div class="bg-${color}-500 h-2 rounded-full" style="width: ${percentage}%"></div>
                        </div>
                        <span class="text-sm text-white w-12 text-right font-medium">${percentage}%</span>
                    </div>
                </div>
            `;
        }).join('');
        
        breakdownContainer.innerHTML = breakdownHtml;
    }

    updateCriticalFindings(alerts, violations) {
        const container = document.getElementById('critical-findings-summary');
        if (!container) return;

        const criticalAlerts = (alerts || []).filter(a => a.severity === 'CRITICAL');
        const criticalViolations = (violations || []).filter(v => v.severity === 'CRITICAL');
        
        if (criticalAlerts.length === 0 && criticalViolations.length === 0) {
            container.innerHTML = '';
            return;
        }

        const findingsHtml = `
            <div class="bg-red-900/20 border border-red-700 rounded-lg p-6 mb-6">
                <h3 class="text-lg font-semibold text-red-400 mb-4">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    Critical Findings Requiring Immediate Attention
                </h3>
                <div class="space-y-4">
                    ${criticalAlerts.slice(0, 3).map(alert => `
                        <div class="bg-slate-900/50 rounded p-3 border-l-4 border-red-500">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h4 class="text-white font-medium">${alert.title}</h4>
                                    <p class="text-sm text-slate-400 mt-1">${alert.description}</p>
                                    <div class="mt-2">
                                        <span class="text-xs text-red-400">
                                            <i class="fas fa-fire mr-1"></i>Risk Score: ${alert.risk_score || 'N/A'}
                                        </span>
                                        <span class="text-xs text-slate-500 ml-4">
                                            ${alert.resource_name} • ${alert.namespace || 'default'}
                                        </span>
                                    </div>
                                </div>
                                <span class="px-2 py-1 bg-red-600 text-white text-xs rounded">CRITICAL</span>
                            </div>
                        </div>
                    `).join('')}
                    
                    ${criticalViolations.slice(0, 2).map(violation => `
                        <div class="bg-slate-900/50 rounded p-3 border-l-4 border-orange-500">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h4 class="text-white font-medium">${violation.policy_name}</h4>
                                    <p class="text-sm text-slate-400 mt-1">${violation.violation_description}</p>
                                    <div class="mt-2">
                                        <span class="text-xs text-orange-400">
                                            <i class="fas fa-ban mr-1"></i>${violation.policy_category}
                                        </span>
                                        <span class="text-xs text-slate-500 ml-4">
                                            ${violation.resource_name} • ${violation.namespace || 'default'}
                                        </span>
                                    </div>
                                </div>
                                <span class="px-2 py-1 bg-orange-600 text-white text-xs rounded">VIOLATION</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                ${(criticalAlerts.length > 3 || criticalViolations.length > 2) ? `
                    <div class="mt-4 text-center">
                        <button onclick="document.querySelector('[data-tab=alerts]').click()" 
                                class="text-sm text-red-400 hover:text-red-300">
                            View all ${criticalAlerts.length + criticalViolations.length} critical findings →
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
        
        container.innerHTML = findingsHtml;
    }

    async displayAlertsFromData() {
        const alerts = await this.dataManager.loadSecurityAlerts();
        this.displayEnhancedAlerts(alerts);
    }

    displayEnhancedAlerts(alerts) {
        // Display alerts
        const alertsList = document.getElementById('alerts-list');
        const overviewContainer = document.getElementById('security-alerts-container');
        
        if (alertsList) {
            this.renderAlertsList(alertsList, alerts);
        }
        
        if (overviewContainer) {
            overviewContainer.innerHTML = `
                <div class="bg-slate-800 rounded-lg p-6 border border-slate-700">
                    <h3 class="text-lg font-semibold text-white mb-4">
                        Recent Security Alerts (${alerts.length})
                    </h3>
                    <div id="security-alerts-list" class="space-y-2 max-h-96 overflow-y-auto"></div>
                </div>
            `;
            
            const overviewList = document.getElementById('security-alerts-list');
            if (overviewList) {
                this.renderAlertsList(overviewList, alerts.slice(0, 10));
            }
        }
    }

    renderAlertsList(container, alerts) {
        if (alerts.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-slate-400">
                    <i class="fas fa-check-circle text-4xl mb-4 text-green-400"></i>
                    <p>No active security alerts</p>
                </div>
            `;
            return;
        }

        container.innerHTML = alerts.map(alert => {
            const severityColor = {
                'CRITICAL': 'red',
                'HIGH': 'orange',
                'MEDIUM': 'yellow',
                'LOW': 'blue'
            }[alert.severity] || 'gray';

            const categoryIcon = {
                'VULNERABILITY': 'fa-bug',
                'POLICY': 'fa-ban',
                'DRIFT': 'fa-code-branch',
                'RBAC': 'fa-user-shield'
            }[alert.category] || 'fa-exclamation-triangle';

            return `
                <div class="bg-slate-900 rounded-lg p-4 border border-slate-700">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <div class="flex items-center space-x-2 mb-2">
                                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-${severityColor}-900/50 text-${severityColor}-400 border border-${severityColor}-700">
                                    ${alert.severity}
                                </span>
                                <span class="inline-flex items-center text-xs text-slate-500">
                                    <i class="fas ${categoryIcon} mr-1"></i>
                                    ${alert.category}
                                </span>
                                ${alert.risk_score ? `
                                    <span class="text-xs text-slate-600">
                                        Risk: ${alert.risk_score}
                                    </span>
                                ` : ''}
                            </div>
                            <h5 class="text-white text-sm font-medium mb-1">${alert.title}</h5>
                            <p class="text-slate-400 text-xs mb-2">${alert.description}</p>
                            
                            <div class="flex items-center justify-between">
                                <div class="text-xs text-slate-500">
                                    <i class="fas fa-cube mr-1"></i>
                                    ${alert.resource_type}: ${alert.resource_name}
                                    ${alert.namespace ? ` • ${alert.namespace}` : ''}
                                </div>
                                ${alert.remediation ? `
                                    <button onclick="alert('${alert.remediation.replace(/'/g, "\\'")}')" 
                                            class="text-xs text-blue-400 hover:text-blue-300">
                                        <i class="fas fa-wrench mr-1"></i>View Fix
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async displayViolationsFromData() {
        const violations = await this.dataManager.loadPolicyViolations();
        this.displayEnhancedViolations(violations);
    }

    displayEnhancedViolations(violations) {
        // Display violations
        const violationsList = document.getElementById('violations-list');
        const recentContainer = document.getElementById('recent-violations-container');
        
        if (violationsList) {
            this.renderViolationsList(violationsList, violations);
        }
        
        if (recentContainer && violations.length > 0) {
            recentContainer.innerHTML = `
                <div class="bg-slate-800 rounded-lg p-6 border border-slate-700">
                    <h3 class="text-lg font-semibold text-white mb-4">
                        Recent Policy Violations (${violations.length})
                    </h3>
                    <div id="recent-violations-list" class="space-y-2 max-h-64 overflow-y-auto"></div>
                </div>
            `;
            
            const recentList = document.getElementById('recent-violations-list');
            if (recentList) {
                this.renderViolationsList(recentList, violations.slice(0, 5));
            }
        }
    }

    renderViolationsList(container, violations) {
        if (violations.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-slate-400">
                    <i class="fas fa-check-circle text-4xl mb-4 text-green-400"></i>
                    <p>No policy violations detected</p>
                </div>
            `;
            return;
        }

        container.innerHTML = violations.map(violation => {
            const severityColor = {
                'CRITICAL': 'red',
                'HIGH': 'orange',
                'MEDIUM': 'yellow',
                'LOW': 'blue'
            }[violation.severity] || 'gray';

            return `
                <div class="bg-slate-900 rounded-lg p-4 border border-slate-700">
                    <div class="flex items-start justify-between mb-2">
                        <h5 class="text-white text-sm font-medium">${violation.policy_name}</h5>
                        <div class="flex items-center space-x-2">
                            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-${severityColor}-900/50 text-${severityColor}-400 border border-${severityColor}-700">
                                ${violation.severity}
                            </span>
                            ${violation.auto_remediable ? `
                                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-900/50 text-green-400 border border-green-700">
                                    <i class="fas fa-robot mr-1"></i>Auto-Fix
                                </span>
                            ` : ''}
                        </div>
                    </div>
                    
                    <p class="text-slate-400 text-xs mb-2">${violation.violation_description}</p>
                    
                    <div class="flex items-center justify-between text-xs">
                        <div class="text-slate-500">
                            <span class="inline-flex items-center">
                                <i class="fas fa-folder mr-1"></i>${violation.policy_category}
                            </span>
                            <span class="ml-3">
                                <i class="fas fa-cube mr-1"></i>${violation.resource_type}: ${violation.resource_name}
                            </span>
                        </div>
                        <div class="text-slate-600">
                            Risk: ${violation.risk_score || 'N/A'}
                        </div>
                    </div>
                    
                    ${violation.remediation_steps && violation.remediation_steps.length > 0 ? `
                        <details class="mt-3">
                            <summary class="cursor-pointer text-xs text-blue-400 hover:text-blue-300">
                                <i class="fas fa-tools mr-1"></i>View Remediation Steps
                            </summary>
                            <ol class="mt-2 space-y-1 text-xs text-slate-400 list-decimal list-inside">
                                ${violation.remediation_steps.map(step => `<li>${step}</li>`).join('')}
                            </ol>
                        </details>
                    ` : ''}
                    
                    ${violation.compliance_frameworks ? `
                        <div class="mt-2 flex flex-wrap gap-1">
                            ${violation.compliance_frameworks.map(fw => `
                                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-400">
                                    ${fw}
                                </span>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    async displayComplianceFromData() {
        const complianceFrameworks = await this.dataManager.loadCompliance();
        this.displayEnhancedCompliance(complianceFrameworks);
    }

    displayEnhancedCompliance(complianceFrameworks) {
        // Display frameworks
        const container = document.getElementById('compliance-frameworks');
        if (!container) return;

        if (Object.keys(complianceFrameworks).length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-slate-400">
                    <i class="fas fa-clipboard-check text-4xl mb-4"></i>
                    <p>No compliance data available</p>
                </div>
            `;
            return;
        }

        container.innerHTML = Object.entries(complianceFrameworks).map(([frameworkName, framework]) => 
            this.renderComplianceFramework(frameworkName, framework)
        ).join('');
    }

    renderComplianceFramework(frameworkName, framework) {
        const compliance = Math.round(framework.overall_compliance || 0);
        const grade = framework.grade || 'N/A';
        const passedControls = framework.passed_controls || 0;
        const failedControls = framework.failed_controls || 0;
        const totalControls = passedControls + failedControls;
        const riskLevel = framework.risk_level || 'UNKNOWN';
        
        const gradeColors = {
            'A+': 'green', 'A': 'green', 'A-': 'green',
            'B+': 'blue', 'B': 'blue', 'B-': 'blue',
            'C+': 'yellow', 'C': 'yellow', 'C-': 'yellow',
            'D+': 'orange', 'D': 'orange', 'D-': 'orange',
            'F': 'red'
        };
        const gradeColor = gradeColors[grade] || 'gray';
        
        const riskColors = {
            'LOW': 'green',
            'MEDIUM': 'yellow',
            'HIGH': 'orange',
            'CRITICAL': 'red'
        };
        const riskColor = riskColors[riskLevel] || 'gray';

        return `
            <div class="bg-slate-800 rounded-lg p-6 border border-slate-700">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-xl font-semibold text-white mb-2">${frameworkName}</h3>
                        <div class="flex items-center space-x-3">
                            <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-${gradeColor}-900/50 text-${gradeColor}-400 border border-${gradeColor}-700">
                                <i class="fas fa-graduation-cap mr-2"></i>
                                Grade: ${grade}
                            </span>
                            <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-${riskColor}-900/50 text-${riskColor}-400 border border-${riskColor}-700">
                                <i class="fas fa-shield-alt mr-2"></i>
                                Risk: ${riskLevel}
                            </span>
                            ${framework.based_on_actual_controls ? `
                                <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-900/30 text-green-400 border border-green-800">
                                    <i class="fas fa-database mr-1"></i>
                                    Live Data
                                </span>
                            ` : ''}
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="text-3xl font-bold ${compliance >= 80 ? 'text-green-400' : compliance >= 60 ? 'text-yellow-400' : 'text-red-400'}">
                            ${compliance}%
                        </div>
                        <div class="text-sm text-slate-500">Compliance Score</div>
                    </div>
                </div>
                
                <div class="grid grid-cols-3 gap-4 mb-4">
                    <div class="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                        <div class="text-green-400 text-2xl font-bold">${passedControls}</div>
                        <div class="text-xs text-slate-400">Passed</div>
                    </div>
                    <div class="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                        <div class="text-red-400 text-2xl font-bold">${failedControls}</div>
                        <div class="text-xs text-slate-400">Failed</div>
                    </div>
                    <div class="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                        <div class="text-blue-400 text-2xl font-bold">${totalControls}</div>
                        <div class="text-xs text-slate-400">Total</div>
                    </div>
                </div>
                
                ${totalControls > 0 ? `
                    <div class="mb-4">
                        <div class="flex items-center justify-between text-sm text-slate-400 mb-2">
                            <span>Control Coverage</span>
                            <span class="font-medium">${passedControls}/${totalControls} Passed</span>
                        </div>
                        <div class="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                            <div class="h-3 rounded-full" style="background: rgb(74, 222, 128); width: ${(passedControls/totalControls * 100)}%"></div>
                        </div>
                    </div>
                ` : ''}
                
                ${framework.control_details && framework.control_details.length > 0 ? `
                    <details class="mt-4 bg-slate-900/30 rounded-lg p-3 border border-slate-700">
                        <summary class="cursor-pointer text-sm text-slate-300 hover:text-white">
                            <i class="fas fa-list-check mr-2"></i>
                            View Control Details (${framework.control_details.length} controls)
                        </summary>
                        <div class="mt-4 space-y-2 max-h-64 overflow-y-auto">
                            ${framework.control_details.map(control => `
                                <div class="flex items-center justify-between py-2 px-3 rounded hover:bg-slate-800/50">
                                    <div class="flex-1">
                                        <span class="text-sm text-slate-300 font-medium">${control.control_id}</span>
                                        <span class="text-xs text-slate-500 ml-2">${control.title}</span>
                                    </div>
                                    <span class="ml-4 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                        control.compliance_status === 'COMPLIANT' 
                                            ? 'bg-green-900/50 text-green-400' 
                                            : 'bg-red-900/50 text-red-400'
                                    }">
                                        ${control.compliance_status === 'COMPLIANT' ? 
                                            '<i class="fas fa-check mr-1"></i>' : 
                                            '<i class="fas fa-times mr-1"></i>'
                                        }
                                        ${control.compliance_status}
                                    </span>
                                </div>
                            `).join('')}
                        </div>
                    </details>
                ` : ''}
            </div>
        `;
    }

    async displayVulnerabilitiesFromData() {
        const vulnerabilityData = await this.dataManager.loadVulnerabilities();
        
        const summaryContainer = document.getElementById('vulnerability-summary');
        
        if (!vulnerabilityData || vulnerabilityData.total_vulnerabilities === 0) {
            if (summaryContainer) {
                summaryContainer.innerHTML = `
                    <div class="text-center py-8 text-slate-400">
                        <i class="fas fa-shield-alt text-4xl mb-4 text-green-400"></i>
                        <p class="text-green-400">No vulnerabilities detected</p>
                        <p class="text-xs mt-2">Your cluster appears to be secure</p>
                    </div>
                `;
            }
            return;
        }
    }

    async displayTrendsFromData() {
        const data = this.dataManager.getCachedData();
        
        if (data && data.analysis) {
            const trends = data.analysis.security_posture?.trends;
            const trendsContent = document.getElementById('trends-content');
            
            if (trends && trends.component_trends && trendsContent) {
                trendsContent.innerHTML = `
                    <div class="bg-slate-800 rounded-lg p-6 border border-slate-700">
                        <h3 class="text-lg font-semibold text-white mb-4">Security Component Trends</h3>
                        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                            ${Object.entries(trends.component_trends).map(([component, trend]) => {
                                const icon = trend === 'improving' ? '↑' : trend === 'declining' ? '↓' : '→';
                                const color = trend === 'improving' ? 'green' : trend === 'declining' ? 'red' : 'yellow';
                                
                                return `
                                    <div class="bg-slate-900/50 rounded p-3 border border-slate-700">
                                        <div class="flex items-center justify-between">
                                            <span class="text-sm text-slate-300">${component.toUpperCase()}</span>
                                            <span class="text-${color}-400 font-bold">${icon}</span>
                                        </div>
                                        <div class="text-xs text-${color}-400 mt-1">${trend}</div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                        
                        <div class="mt-6 p-4 bg-slate-900/50 rounded border border-slate-700">
                            <h4 class="text-sm font-medium text-slate-300 mb-2">Trend Analysis</h4>
                            <div class="space-y-2 text-xs text-slate-400">
                                <div>• Overall trend: <span class="text-${trends.trend === 'improving' ? 'green' : trends.trend === 'declining' ? 'red' : 'yellow'}-400">${trends.trend}</span></div>
                                <div>• Change: <span class="text-white">${trends.change > 0 ? '+' : ''}${trends.change.toFixed(2)}%</span></div>
                                <div>• Data points analyzed: ${trends.data_points}</div>
                                <div>• Time range: ${new Date(trends.time_range.oldest).toLocaleDateString()} - ${new Date(trends.time_range.newest).toLocaleDateString()}</div>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
    }

    async displayAuditTrailFromData() {
        const container = document.getElementById('audit-trail-list');
        if (container) {
            container.innerHTML = `
                <div class="text-center py-8 text-slate-400">
                    <i class="fas fa-history text-4xl mb-4"></i>
                    <p>No audit events available</p>
                </div>
            `;
        }
    }

    filterAlertsUI() {
        const severity = document.getElementById('alert-severity-filter').value;
        const category = document.getElementById('alert-category-filter')?.value;
        
        const alerts = this.dataManager.filterAlerts(severity, category);
        
        const alertsList = document.getElementById('alerts-list');
        if (alertsList) {
            this.renderAlertsList(alertsList, alerts);
        }
    }

    filterViolationsUI() {
        const severity = document.getElementById('violation-severity-filter').value;
        const category = document.getElementById('violation-category-filter')?.value;
        
        const violations = this.dataManager.filterViolations(severity, category);
        
        const violationsList = document.getElementById('violations-list');
        if (violationsList) {
            this.renderViolationsList(violationsList, violations);
        }
    }

    showNoDataMessage(message) {
        const elements = {
            'security-score': '--',
            'security-grade': 'No data available',
            'total-alerts': '0',
            'total-violations': '0',
            'compliance-score': '--'
        };

        for (const [id, value] of Object.entries(elements)) {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        }
        
        const breakdownContainer = document.getElementById('security-breakdown');
        if (breakdownContainer) {
            breakdownContainer.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-shield-alt text-4xl mb-4 text-slate-500"></i>
                    <p class="text-slate-400">${message}</p>
                </div>
            `;
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 max-w-sm w-full px-4 py-3 rounded-lg shadow-lg`;
        
        const colors = {
            'success': 'bg-green-600 text-white',
            'error': 'bg-red-600 text-white',
            'warning': 'bg-yellow-600 text-white',
            'info': 'bg-blue-600 text-white'
        };
        
        notification.className += ` ${colors[type] || colors['info']}`;
        
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, 5000);
    }

    // For backward compatibility
    updateSecurityOverview(data) {
        this.updateEnhancedSecurityOverview(data);
    }

    async forceRefresh() {
        console.log('🔄 Force refreshing security dashboard...');
        const data = await this.dataManager.loadSecurityOverview();
        if (data) {
            this.updateDashboardFromData(data);
        }
    }
}

// Initialize UI Renderer and set up global access
let securityUIRenderer;

document.addEventListener('DOMContentLoaded', () => {
    const urlPath = window.location.pathname;
    if (urlPath.includes('/cluster/')) {
        const match = urlPath.match(/\/cluster\/([^\/\?]+)/);
        if (match && match[1]) {
            const clusterId = decodeURIComponent(match[1]);
            console.log(`🚀 Initializing with Cluster ID: ${clusterId}`);
            
            window.currentCluster = {
                id: clusterId,
                name: document.querySelector('h4 span.bg-gradient-to-r')?.textContent.trim() || clusterId
            };
            
            window.currentClusterState = {
                clusterId: clusterId,
                lastUpdated: new Date().toISOString(),
                validated: true
            };
        }
    }
    
    securityUIRenderer = new SecurityUIRenderer();
    window.securityUIRenderer = securityUIRenderer;
});

// Global debug functions
window.securityDebug = {
    test: async () => {
        if (!window.securityUIRenderer) {
            console.error('❌ Security UI Renderer not initialized!');
            return;
        }
        return await window.securityUIRenderer.dataManager.debugClusterAndAPIs();
    },
    refresh: async () => {
        if (!window.securityUIRenderer) {
            console.error('❌ Security UI Renderer not initialized!');
            return;
        }
        return await window.securityUIRenderer.forceRefresh();
    },
    getClusterId: () => {
        if (!window.securityUIRenderer) {
            console.error('❌ Security UI Renderer not initialized!');
            return;
        }
        return window.securityUIRenderer.dataManager.getCurrentClusterId();
    },
    getData: () => {
        if (!window.securityUIRenderer) {
            console.error('❌ Security UI Renderer not initialized!');
            return;
        }
        return window.securityUIRenderer.dataManager.getCachedData();
    }
};

console.log('💡 Enhanced Security UI Renderer Ready');
console.log('   window.securityDebug.test()     - Test cluster ID and APIs');
console.log('   window.securityDebug.refresh()  - Force refresh dashboard');
console.log('   window.securityDebug.getData()  - View cached security data');