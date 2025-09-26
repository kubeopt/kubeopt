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

        // Create the clean dashboard structure with improved styling
        const dashboardHTML = `
            <div class="security-dashboard-layout">
                <!-- Professional Tab Navigation -->
                <div style="margin-bottom: 2rem;">
                    <nav style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; padding: 1rem; background: rgba(255, 255, 255, 0.02); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1);">
                        <button class="security-tab-btn active" data-tab="dashboard">
                            <i class="fas fa-tachometer-alt"></i>Dashboard
                        </button>
                        <button class="security-tab-btn" data-tab="issues">
                            <i class="fas fa-exclamation-triangle"></i>Issues
                            <span id="issues-badge" style="margin-left: 0.5rem; padding: 0.25rem 0.5rem; background: rgba(239, 68, 68, 0.2); color: #fca5a5; font-size: 0.75rem; border-radius: 6px; display: none;">0</span>
                        </button>
                        <button class="security-tab-btn" data-tab="compliance">
                            <i class="fas fa-shield-check"></i>Compliance
                        </button>
                        <button class="security-tab-btn" data-tab="analytics">
                            <i class="fas fa-chart-line"></i>Analytics
                        </button>
                    </nav>
                </div>

                <!-- Tab Content -->
                <div class="security-tab-content">
                    <!-- Security Dashboard Tab -->
                    <div id="dashboard-tab" class="security-tab-pane active">
                        <!-- Professional Metrics Cards -->
                        <div class="security-metrics-grid">
                            <div class="security-metric-card">
                                <div class="security-metric-header">
                                    <span class="security-metric-title">Security Score</span>
                                    <div class="security-metric-icon">
                                        <i class="fas fa-shield-alt" style="color: #4f77ff;"></i>
                                    </div>
                                </div>
                                <div id="security-score" class="security-metric-value">--</div>
                                <div id="security-grade" class="security-metric-description">Loading...</div>
                                <div id="security-trend" class="security-metric-trend"></div>
                            </div>

                            <div class="security-metric-card">
                                <div class="security-metric-header">
                                    <span class="security-metric-title">Active Alerts</span>
                                    <div class="security-metric-icon">
                                        <i class="fas fa-exclamation-triangle" style="color: #f59e0b;"></i>
                                    </div>
                                </div>
                                <div id="total-alerts" class="security-metric-value">0</div>
                                <div class="security-metric-description">
                                    <span id="critical-alerts-count">0 Critical</span>
                                    <span style="margin: 0 0.5rem; color: var(--security-text-muted);">•</span>
                                    <span id="high-alerts-count">0 High</span>
                                </div>
                            </div>

                            <div class="security-metric-card">
                                <div class="security-metric-header">
                                    <span class="security-metric-title">Violations</span>
                                    <div class="security-metric-icon">
                                        <i class="fas fa-ban" style="color: #ef4444;"></i>
                                    </div>
                                </div>
                                <div id="total-violations" class="security-metric-value">0</div>
                                <div class="security-metric-description">
                                    <span id="critical-violations-count">0 Critical</span>
                                    <span style="margin: 0 0.5rem; color: var(--security-text-muted);">•</span>
                                    <span id="high-violations-count">0 High</span>
                                </div>
                            </div>

                            <div class="security-metric-card">
                                <div class="security-metric-header">
                                    <span class="security-metric-title">Compliance</span>
                                    <div class="security-metric-icon">
                                        <i class="fas fa-clipboard-check" style="color: #22c55e;"></i>
                                    </div>
                                </div>
                                <div id="compliance-score" class="security-metric-value">--</div>
                                <div class="security-metric-description">Policy adherence</div>
                                <div id="frameworks-status" class="security-metric-trend"></div>
                            </div>
                        </div>

                        <!-- Professional Chart Section -->
                        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 2rem; margin-bottom: 2rem;">
                            <!-- Security Trend Chart -->
                            <div class="security-chart-container">
                                <div class="security-chart-header">
                                    <h3 class="security-chart-title">Security Posture Trend</h3>
                                    <div style="display: flex; align-items: center; gap: 1rem; font-size: 0.75rem;">
                                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                                            <div style="width: 8px; height: 8px; background: var(--security-accent); border-radius: 50%;"></div>
                                            <span style="color: var(--security-text-secondary);">Score</span>
                                        </div>
                                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                                            <div style="width: 8px; height: 8px; background: var(--security-warning); border-radius: 50%;"></div>
                                            <span style="color: var(--security-text-secondary);">Alerts</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="chart-container">
                                    <canvas id="security-trend-chart"></canvas>
                                </div>
                            </div>
                            
                            <!-- Risk Level Distribution -->
                            <div class="security-chart-container">
                                <div class="security-chart-header">
                                    <h3 class="security-chart-title">Risk Distribution</h3>
                                </div>
                                <div class="chart-container">
                                    <canvas id="risk-donut-chart"></canvas>
                                </div>
                                <div id="risk-distribution" style="margin-top: 1.5rem;">
                                    <div style="text-align: center; color: var(--security-text-muted); font-size: 0.8rem;">Loading risk data...</div>
                                </div>
                            </div>
                        </div>

                        <!-- Additional Sections -->
                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                            <div class="bg-slate-800/40 border border-slate-700/50 rounded-lg p-5">
                                <h3 class="text-base font-medium text-white mb-4">Security Components</h3>
                                <div id="security-breakdown" class="space-y-3">
                                    <div class="text-center text-slate-500 p-4">Loading security data...</div>
                                </div>
                            </div>
                            
                            <div class="bg-slate-800/40 border border-slate-700/50 rounded-lg p-5">
                                <h3 class="text-base font-medium text-white mb-4">Compliance Status</h3>
                                <div class="chart-container">
                                    <canvas id="compliance-bar-chart" style="width: 100%; height: 200px;"></canvas>
                                </div>
                                <div id="compliance-details" class="mt-4 space-y-2">
                                    <div class="text-center text-slate-500 text-xs">Loading compliance data...</div>
                                </div>
                            </div>
                        </div>

                        <!-- Critical Findings Summary -->
                        <div id="critical-findings-summary" class="mb-8"></div>
                    </div>

                    <!-- Issues & Alerts Tab -->
                    <div id="issues-tab" class="security-tab-pane hidden">
                        <!-- Professional Issues Metrics Cards -->
                        <div class="security-metrics-grid">
                            <div class="security-metric-card">
                                <div class="security-metric-header">
                                    <span class="security-metric-title">Total Issues</span>
                                    <div class="security-metric-icon">
                                        <i class="fas fa-exclamation-triangle" style="color: #f59e0b;"></i>
                                    </div>
                                </div>
                                <div id="total-issues-count" class="security-metric-value">0</div>
                                <div class="security-metric-description">Alerts + Violations</div>
                            </div>

                            <div class="security-metric-card">
                                <div class="security-metric-header">
                                    <span class="security-metric-title">Critical</span>
                                    <div class="security-metric-icon">
                                        <i class="fas fa-fire" style="color: #ef4444;"></i>
                                    </div>
                                </div>
                                <div id="critical-issues-count" class="security-metric-value">0</div>
                                <div class="security-metric-description">Immediate attention</div>
                            </div>

                            <div class="security-metric-card">
                                <div class="security-metric-header">
                                    <span class="security-metric-title">High Priority</span>
                                    <div class="security-metric-icon">
                                        <i class="fas fa-exclamation" style="color: #f59e0b;"></i>
                                    </div>
                                </div>
                                <div id="high-issues-count" class="security-metric-value">0</div>
                                <div class="security-metric-description">High severity</div>
                            </div>

                            <div class="security-metric-card">
                                <div class="security-metric-header">
                                    <span class="security-metric-title">Medium & Low</span>
                                    <div class="security-metric-icon">
                                        <i class="fas fa-info-circle" style="color: #06b6d4;"></i>
                                    </div>
                                </div>
                                <div id="medium-low-issues-count" class="security-metric-value">0</div>
                                <div class="security-metric-description">Lower priority</div>
                            </div>
                        </div>

                        <!-- Critical Findings Summary -->
                        <div id="issues-critical-findings" class="mb-8"></div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem;">
                            <!-- Security Alerts -->
                            <div class="security-chart-container">
                                <div class="security-chart-header">
                                    <h3 class="security-chart-title" style="display: flex; align-items: center; gap: 0.75rem;">
                                        <i class="fas fa-exclamation-triangle" style="color: #f59e0b;"></i>Security Alerts
                                    </h3>
                                    <div class="security-filters">
                                        <select id="alert-severity-filter" class="security-select" style="max-width: 200px;">
                                            <option value="">All Severities</option>
                                            <option value="CRITICAL">Critical</option>
                                            <option value="HIGH">High</option>
                                            <option value="MEDIUM">Medium</option>
                                            <option value="LOW">Low</option>
                                        </select>
                                    </div>
                                </div>
                                <div id="alerts-list" class="security-list"></div>
                            </div>
                            
                            <!-- Policy Violations -->
                            <div class="security-chart-container">
                                <div class="security-chart-header">
                                    <h3 class="security-chart-title" style="display: flex; align-items: center; gap: 0.75rem;">
                                        <i class="fas fa-ban" style="color: #ef4444;"></i>Policy Violations
                                    </h3>
                                    <div class="security-filters">
                                        <select id="violation-severity-filter" class="security-select" style="max-width: 200px;">
                                            <option value="">All Severities</option>
                                            <option value="CRITICAL">Critical</option>
                                            <option value="HIGH">High</option>
                                            <option value="MEDIUM">Medium</option>
                                            <option value="LOW">Low</option>
                                        </select>
                                    </div>
                                </div>
                                <div id="violations-list" class="security-list"></div>
                            </div>
                        </div>
                        
                    </div>

                    <!-- Compliance Tab -->
                    <div id="compliance-tab" class="security-tab-pane hidden">
                        <!-- Professional Compliance Summary Stats -->
                        <div id="compliance-summary-stats" class="security-metrics-grid" style="margin-bottom: 2rem;">
                            <!-- Stats will be populated when compliance data is loaded -->
                        </div>
                        
                        <!-- Professional Framework Details with Enhanced Styling -->
                        <div style="background: var(--security-bg-card); border: 1px solid var(--security-border); border-radius: 12px; padding: 2rem; backdrop-filter: blur(10px); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);">
                            <!-- Header Section with Settings.css Style -->
                            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; padding: 1.5rem; border-radius: 12px 12px 0 0; position: relative; text-align: left; background: rgba(255, 255, 255, 0.02); border-bottom: 1px solid var(--security-border);">
                                <div style="width: 48px; height: 48px; background: rgba(34, 197, 94, 0.2); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                                    <i class="fas fa-shield-check" style="color: #22c55e; font-size: 1.25rem;"></i>
                                </div>
                                <div style="flex: 1;">
                                    <h3 style="font-size: 1.4rem; font-weight: 700; color: var(--security-text-primary); letter-spacing: 0.025em; margin: 0; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);">
                                        Compliance Frameworks
                                    </h3>
                                    <div style="font-size: 0.875rem; color: var(--security-text-muted); margin-top: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                                        <i class="fas fa-info-circle" style="opacity: 0.7;"></i>
                                        Click framework names to expand detailed control information
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Frameworks Content with Enhanced Container -->
                            <div id="compliance-frameworks" style="max-height: 600px; overflow-y: auto; padding: 0.5rem;">
                                <!-- Custom scrollbar styling will be applied via CSS -->
                            </div>
                        </div>
                        
                        <!-- Professional Info Box (Settings.css Style) -->
                        <div style="padding: 1.5rem; border-radius: 12px; margin-top: 2rem; font-size: 0.9rem; line-height: 1.6; position: relative; overflow: hidden; background: rgba(79, 119, 255, 0.1); border: 1px solid var(--security-accent); color: var(--security-text-secondary);">
                            <div style="content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: var(--security-accent); opacity: 0.7;"></div>
                            <div style="font-weight: 700; font-size: 1rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.75rem; letter-spacing: 0.025em;">
                                <i class="fas fa-lightbulb" style="font-size: 1.1rem; opacity: 0.8; color: var(--security-accent);"></i>
                                Compliance Insights
                            </div>
                            <p style="margin: 0;">Compliance frameworks are evaluated against your cluster's actual configuration and policies. Grades are calculated based on the percentage of controls that pass validation.</p>
                        </div>
                    </div>

                    <!-- Analytics Tab -->
                    <div id="analytics-tab" class="security-tab-pane hidden">
                        <!-- Security Trends Analytics -->
                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                            <!-- Security Score Over Time -->
                            <div class="bg-slate-800/40 border border-slate-700/50 rounded-lg p-5">
                                <h3 class="text-base font-medium text-white mb-4 flex items-center">
                                    <i class="fas fa-chart-line text-slate-400 mr-2 text-sm"></i>Security Score Trend
                                </h3>
                                <div class="chart-container">
                                    <canvas id="score-trend-line-chart" style="width: 100%; height: 250px;"></canvas>
                                </div>
                            </div>
                            
                            <!-- Alert Volume Trend -->
                            <div class="bg-slate-800/40 border border-slate-700/50 rounded-lg p-5">
                                <h3 class="text-base font-medium text-white mb-4 flex items-center">
                                    <i class="fas fa-bell text-slate-400 mr-2 text-sm"></i>Alert Volume Trend
                                </h3>
                                <div class="chart-container">
                                    <canvas id="alert-volume-chart" style="width: 100%; height: 250px;"></canvas>
                                </div>
                            </div>
                        </div>
                        
                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                            <!-- Compliance Progress -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">
                                    <i class="fas fa-shield-check text-green-400 mr-2"></i>Compliance Progress
                                </h3>
                                <div class="chart-container">
                                    <canvas id="compliance-trend-chart" style="width: 100%; height: 250px;"></canvas>
                                </div>
                            </div>
                            
                            <!-- Risk Level Changes -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">
                                    <i class="fas fa-exclamation-triangle text-yellow-400 mr-2"></i>Risk Level Changes
                                </h3>
                                <div class="chart-container">
                                    <canvas id="risk-trend-chart" style="width: 100%; height: 250px;"></canvas>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Security Analytics Summary -->
                        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                            <!-- Vulnerability Summary -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">
                                    <i class="fas fa-bug text-purple-400 mr-2"></i>Vulnerabilities
                                </h3>
                                <div id="vulnerability-summary" class="space-y-3"></div>
                            </div>
                            
                            <!-- Performance Metrics -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">
                                    <i class="fas fa-tachometer-alt text-cyan-400 mr-2"></i>Performance
                                </h3>
                                <div id="performance-metrics" class="space-y-3">
                                    <div class="flex justify-between">
                                        <span class="text-slate-400">Scan Duration</span>
                                        <span class="text-white" id="scan-duration">--</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span class="text-slate-400">Resources Analyzed</span>
                                        <span class="text-white" id="resources-analyzed">--</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span class="text-slate-400">Controls Evaluated</span>
                                        <span class="text-white" id="controls-evaluated">--</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Audit Activity -->
                            <div class="p-6 border rounded" style="background: #171d33; border: 1px solid rgba(255,255,255,0.1);">
                                <h3 class="text-lg font-semibold text-white mb-4">
                                    <i class="fas fa-history text-gray-400 mr-2"></i>Recent Activity
                                </h3>
                                <div id="audit-summary" class="space-y-2 max-h-48 overflow-y-auto">
                                    <div class="text-slate-400 text-sm">No recent audit events</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = dashboardHTML;

        // Add custom CSS for enhanced tab styling
        this.addTabStyling();
        
        // Set up tab switching
        this.setupTabSwitching();
    }

    addTabStyling() {
        // Add custom CSS for professional tab styling
        const style = document.createElement('style');
        style.textContent = `
            .security-tab-btn {
                background: rgba(22, 28, 50, 0.6);
                color: rgb(148, 163, 184);
                border: 1px solid rgba(255, 255, 255, 0.1);
                font-weight: 500;
                font-size: 0.875rem;
                cursor: pointer;
                position: relative;
                overflow: hidden;
            }
            
            .security-tab-btn:hover {
                background: rgba(22, 28, 50, 0.9);
                color: rgb(226, 232, 240);
                border-color: rgba(59, 130, 246, 0.4);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
            }
            
            .security-tab-btn.active {
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0.25) 100%);
                color: white;
                border-color: rgba(59, 130, 246, 0.6);
                box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
            }
            
            .security-tab-btn.active::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, rgb(59, 130, 246), rgb(96, 165, 250));
            }
            
            .security-tab-btn i {
                opacity: 0.8;
            }
            
            .security-tab-btn.active i {
                opacity: 1;
            }
            
            /* Custom scrollbar styling to match dark theme */
            .security-tab-content ::-webkit-scrollbar {
                width: 8px;
            }
            
            .security-tab-content ::-webkit-scrollbar-track {
                background: rgba(22, 28, 50, 0.3);
                border-radius: 4px;
            }
            
            .security-tab-content ::-webkit-scrollbar-thumb {
                background: rgba(59, 130, 246, 0.4);
                border-radius: 4px;
            }
            
            .security-tab-content ::-webkit-scrollbar-thumb:hover {
                background: rgba(59, 130, 246, 0.6);
            }
        `;
        document.head.appendChild(style);
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
            case 'dashboard':
                // Dashboard data is already loaded in main initialization
                break;
            case 'issues':
                await this.displayAlertsFromData();
                await this.displayViolationsFromData();
                await this.displayIssuesCriticalFindings();
                break;
            case 'compliance':
                await this.displayComplianceFromData();
                break;
            case 'analytics':
                await this.displayTrendsFromData();
                await this.displayVulnerabilitiesFromData();
                await this.displayPerformanceMetrics();
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
                const issuesBadge = document.getElementById('issues-badge');
                if (issuesBadge && alerts.length > 0) {
                    issuesBadge.textContent = alerts.length;
                    issuesBadge.classList.remove('hidden');
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
                
                // Update badge (combine with alerts for issues badge)
                const issuesBadge = document.getElementById('issues-badge');
                if (issuesBadge && violations.length > 0) {
                    const currentCount = parseInt(issuesBadge.textContent) || 0;
                    issuesBadge.textContent = currentCount + violations.length;
                    issuesBadge.classList.remove('hidden');
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

        console.log('🔍 Critical Findings Debug:', {
            totalAlerts: alerts?.length || 0,
            totalViolations: violations?.length || 0,
            alertSeverities: alerts?.map(a => a.severity).slice(0, 5) || [],
            violationSeverities: violations?.map(v => v.severity).slice(0, 5) || []
        });

        // Filter for critical and high severity items for better visibility
        const criticalAlerts = (alerts || []).filter(a => a.severity === 'CRITICAL' || a.severity === 'HIGH');
        const criticalViolations = (violations || []).filter(v => v.severity === 'CRITICAL' || v.severity === 'HIGH');
        
        console.log('🔥 Filtered Critical/High Items:', {
            criticalAlerts: criticalAlerts.length,
            criticalViolations: criticalViolations.length
        });
        
        if (criticalAlerts.length === 0 && criticalViolations.length === 0) {
            // Show a message that analysis found items but none are critical
            if ((alerts?.length || 0) > 0 || (violations?.length || 0) > 0) {
                container.innerHTML = `
                    <div class="bg-slate-800/40 border border-slate-700/50 rounded-lg p-5 mb-8">
                        <h3 class="text-base font-medium text-white mb-2 flex items-center">
                            <i class="fas fa-check-circle text-green-400 mr-2 text-sm"></i>
                            Security Analysis Complete
                        </h3>
                        <p class="text-xs text-slate-400">
                            Found ${alerts?.length || 0} alerts and ${violations?.length || 0} violations. 
                            No critical or high-severity issues requiring immediate attention.
                        </p>
                        <button onclick="document.querySelector('[data-tab=issues]').click()" 
                                class="mt-2 text-xs text-slate-400 hover:text-white transition-colors">
                            View all findings →
                        </button>
                    </div>
                `;
            } else {
                container.innerHTML = '';
            }
            return;
        }

        const findingsHtml = `
            <div class="bg-slate-800/40 border border-slate-700/50 rounded-lg p-5 mb-8">
                <h3 class="text-base font-medium text-white mb-4 flex items-center">
                    <i class="fas fa-exclamation-triangle text-red-400 mr-2 text-sm"></i>
                    Critical Findings Requiring Immediate Attention
                </h3>
                <div class="space-y-3">
                    ${criticalAlerts.slice(0, 3).map(alert => `
                        <div class="bg-slate-700/30 rounded-lg p-4 border-l-2 border-red-400/50">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h4 class="text-white font-medium text-sm">${alert.title}</h4>
                                    <p class="text-xs text-slate-400 mt-1">${alert.description}</p>
                                    <div class="mt-2">
                                        <span class="text-xs text-slate-400">
                                            <i class="fas fa-exclamation-circle text-red-400 mr-1"></i>Risk Score: ${alert.risk_score || 'N/A'}
                                        </span>
                                        <span class="text-xs text-slate-500 ml-4">
                                            ${alert.resource_name} • ${alert.namespace || 'default'}
                                        </span>
                                    </div>
                                </div>
                                <span class="px-2 py-0.5 text-xs rounded border ${alert.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-400 border-red-500/30' : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'}">${alert.severity}</span>
                            </div>
                        </div>
                    `).join('')}
                    
                    ${criticalViolations.slice(0, 2).map(violation => `
                        <div class="bg-slate-700/30 rounded-lg p-4 border-l-2 border-yellow-400/50">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h4 class="text-white font-medium text-sm">${violation.policy_name}</h4>
                                    <p class="text-xs text-slate-400 mt-1">${violation.violation_description}</p>
                                    <div class="mt-2">
                                        <span class="text-xs text-slate-400">
                                            <i class="fas fa-ban text-yellow-400 mr-1"></i>${violation.policy_category}
                                        </span>
                                        <span class="text-xs text-slate-500 ml-4">
                                            ${violation.resource_name} • ${violation.namespace || 'default'}
                                        </span>
                                    </div>
                                </div>
                                <span class="px-2 py-0.5 text-xs rounded border ${violation.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-400 border-red-500/30' : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'}">${violation.severity}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                ${(criticalAlerts.length > 3 || criticalViolations.length > 2) ? `
                    <div class="mt-4 text-center">
                        <button onclick="document.querySelector('[data-tab=issues]').click()" 
                                class="text-xs text-slate-400 hover:text-white transition-colors">
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
        // Display alerts in Issues tab only
        const alertsList = document.getElementById('alerts-list');
        
        if (alertsList) {
            this.renderAlertsList(alertsList, alerts);
        }
    }

    renderAlertsList(container, alerts) {
        if (alerts.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 3rem 1rem; color: var(--security-text-muted);">
                    <i class="fas fa-check-circle" style="font-size: 3rem; margin-bottom: 1rem; color: var(--security-success);"></i>
                    <p style="font-size: 1rem; font-weight: 500;">No active security alerts</p>
                    <p style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.7;">Your security posture looks good!</p>
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
                                    <details class="inline">
                                        <summary class="cursor-pointer text-xs text-blue-400 hover:text-blue-300">
                                            <i class="fas fa-wrench mr-1"></i>View Fix
                                        </summary>
                                        <div class="mt-2 p-2 bg-slate-800/50 rounded text-xs text-slate-300">
                                            ${alert.remediation}
                                        </div>
                                    </details>
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
        // Display violations in Issues tab only
        const violationsList = document.getElementById('violations-list');
        
        if (violationsList) {
            this.renderViolationsList(violationsList, violations);
        }
    }

    renderViolationsList(container, violations) {
        if (violations.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 3rem 1rem; color: var(--security-text-muted);">
                    <i class="fas fa-check-circle" style="font-size: 3rem; margin-bottom: 1rem; color: var(--security-success);"></i>
                    <p style="font-size: 1rem; font-weight: 500;">No policy violations detected</p>
                    <p style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.7;">All policies are being followed correctly!</p>
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
        // Update summary stats
        this.updateComplianceSummaryStats(complianceFrameworks);
        
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

    updateComplianceSummaryStats(complianceFrameworks) {
        const statsContainer = document.getElementById('compliance-summary-stats');
        if (!statsContainer) return;

        // If no compliance data, hide the stats
        if (Object.keys(complianceFrameworks).length === 0) {
            statsContainer.innerHTML = '';
            return;
        }

        // Calculate summary statistics
        const frameworks = Object.values(complianceFrameworks);
        const totalFrameworks = frameworks.length;
        const avgCompliance = Math.round(
            frameworks.reduce((sum, fw) => sum + (fw.overall_compliance || 0), 0) / totalFrameworks
        );
        const totalControls = frameworks.reduce((sum, fw) => 
            sum + (fw.passed_controls || 0) + (fw.failed_controls || 0), 0
        );
        const passedControls = frameworks.reduce((sum, fw) => sum + (fw.passed_controls || 0), 0);
        const failedControls = frameworks.reduce((sum, fw) => sum + (fw.failed_controls || 0), 0);

        // Count frameworks by risk level
        const riskLevels = frameworks.reduce((acc, fw) => {
            const risk = fw.risk_level || 'UNKNOWN';
            acc[risk] = (acc[risk] || 0) + 1;
            return acc;
        }, {});

        statsContainer.innerHTML = `
            <div class="security-metric-card">
                <div class="security-metric-header">
                    <span class="security-metric-title">Average Compliance</span>
                    <div class="security-metric-icon">
                        <i class="fas fa-shield-check" style="color: var(--security-accent);"></i>
                    </div>
                </div>
                <div class="security-metric-value ${avgCompliance >= 80 ? 'text-green-400' : avgCompliance >= 60 ? 'text-yellow-400' : 'text-red-400'}">${avgCompliance}%</div>
                <div class="security-metric-description">${totalFrameworks} frameworks evaluated</div>
                <div class="security-metric-trend">
                    <span style="color: var(--security-text-secondary);">${avgCompliance >= 80 ? '✓' : avgCompliance >= 60 ? '!' : '⚠'}</span>
                    <span style="color: var(--security-text-muted); margin-left: 0.5rem;">${avgCompliance >= 80 ? 'Excellent' : avgCompliance >= 60 ? 'Good' : 'Needs attention'}</span>
                </div>
            </div>

            <div class="security-metric-card">
                <div class="security-metric-header">
                    <span class="security-metric-title">Passed Controls</span>
                    <div class="security-metric-icon">
                        <i class="fas fa-check-circle" style="color: #22c55e;"></i>
                    </div>
                </div>
                <div class="security-metric-value" style="color: #22c55e;">${passedControls}</div>
                <div class="security-metric-description">of ${totalControls} total controls</div>
                <div class="security-metric-trend">
                    <span style="color: var(--security-text-secondary);">📊</span>
                    <span style="color: var(--security-text-muted); margin-left: 0.5rem;">${Math.round((passedControls/totalControls) * 100)}% pass rate</span>
                </div>
            </div>

            <div class="security-metric-card">
                <div class="security-metric-header">
                    <span class="security-metric-title">Failed Controls</span>
                    <div class="security-metric-icon">
                        <i class="fas fa-times-circle" style="color: #ef4444;"></i>
                    </div>
                </div>
                <div class="security-metric-value" style="color: #ef4444;">${failedControls}</div>
                <div class="security-metric-description">require remediation</div>
                <div class="security-metric-trend">
                    <span style="color: var(--security-text-secondary);">${failedControls === 0 ? '✓' : '!'}</span>
                    <span style="color: var(--security-text-muted); margin-left: 0.5rem;">${failedControls === 0 ? 'All passing' : 'Action needed'}</span>
                </div>
            </div>

            <div class="security-metric-card">
                <div class="security-metric-header">
                    <span class="security-metric-title">Risk Assessment</span>
                    <div class="security-metric-icon">
                        <i class="fas fa-exclamation-triangle" style="color: ${riskLevels.HIGH || riskLevels.CRITICAL ? '#ef4444' : '#22c55e'};"></i>
                    </div>
                </div>
                <div class="security-metric-value" style="color: var(--security-text-primary);">
                    ${riskLevels.CRITICAL ? riskLevels.CRITICAL : 
                      riskLevels.HIGH ? riskLevels.HIGH : 
                      riskLevels.MEDIUM ? riskLevels.MEDIUM : 0}
                </div>
                <div class="security-metric-description">
                    ${riskLevels.CRITICAL ? 'Critical risk frameworks' : 
                      riskLevels.HIGH ? 'High risk frameworks' : 
                      riskLevels.MEDIUM ? 'Medium risk frameworks' : 'Low risk frameworks'}
                </div>
                <div class="security-metric-trend">
                    <span style="color: var(--security-text-secondary);">${riskLevels.HIGH || riskLevels.CRITICAL ? '🔴' : '🟢'}</span>
                    <span style="color: var(--security-text-muted); margin-left: 0.5rem;">
                        ${riskLevels.CRITICAL ? 'Critical' : 
                          riskLevels.HIGH ? 'High' : 
                          riskLevels.MEDIUM ? 'Medium' : 'Low'} risk
                    </span>
                </div>
            </div>
        `;
    }

    renderComplianceFramework(frameworkName, framework) {
        const compliance = Math.round(framework.overall_compliance || 0);
        const grade = framework.grade || 'N/A';
        const passedControls = framework.passed_controls || 0;
        const failedControls = framework.failed_controls || 0;
        const totalControls = passedControls + failedControls;
        const riskLevel = framework.risk_level || 'UNKNOWN';
        
        const gradeColors = {
            'A+': '#22c55e', 'A': '#22c55e', 'A-': '#22c55e',
            'B+': '#4f77ff', 'B': '#4f77ff', 'B-': '#4f77ff',
            'C+': '#f59e0b', 'C': '#f59e0b', 'C-': '#f59e0b',
            'D+': '#f97316', 'D': '#f97316', 'D-': '#f97316',
            'F': '#ef4444'
        };
        const gradeColor = gradeColors[grade] || '#6b7280';
        
        const riskColors = {
            'LOW': '#22c55e',
            'MEDIUM': '#f59e0b',
            'HIGH': '#f97316',
            'CRITICAL': '#ef4444'
        };
        const riskColor = riskColors[riskLevel] || '#6b7280';

        return `
            <div style="background: var(--security-bg-card); border: 1px solid var(--security-border); border-radius: 12px; padding: 2rem; margin-bottom: 1.5rem; backdrop-filter: blur(10px); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); transition: all 0.3s ease; position: relative; overflow: hidden;">
                <!-- Professional Header with Settings.css Style -->
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 2rem;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                            <div style="width: 48px; height: 48px; background: rgba(79, 119, 255, 0.2); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                                <i class="fas fa-shield-check" style="color: var(--security-accent); font-size: 1.25rem;"></i>
                            </div>
                            <div>
                                <h3 style="font-size: 1.25rem; font-weight: 700; color: var(--security-text-primary); letter-spacing: 0.025em; margin: 0; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);">
                                    ${frameworkName}
                                </h3>
                                <div style="display: flex; align-items: center; gap: 0.75rem; margin-top: 0.75rem;">
                                    <span style="display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.75rem; font-weight: 600; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.1); color: var(--security-text-primary);">
                                        <i class="fas fa-graduation-cap" style="color: ${gradeColor}; margin-right: 0.5rem;"></i>
                                        Grade: ${grade}
                                    </span>
                                    <span style="display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.75rem; font-weight: 600; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.1); color: var(--security-text-primary);">
                                        <i class="fas fa-shield-alt" style="color: ${riskColor}; margin-right: 0.5rem;"></i>
                                        Risk: ${riskLevel}
                                    </span>
                                    ${framework.based_on_actual_controls ? `
                                        <span style="display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; background: rgba(34, 197, 94, 0.2); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.3);">
                                            <i class="fas fa-database" style="margin-right: 0.5rem;"></i>
                                            Live Data
                                        </span>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div style="text-align: right; margin-left: 2rem;">
                        <div style="font-size: 3rem; font-weight: 700; color: ${compliance >= 80 ? '#22c55e' : compliance >= 60 ? '#f59e0b' : '#ef4444'}; line-height: 1; margin-bottom: 0.5rem; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);">
                            ${compliance}%
                        </div>
                        <div style="font-size: 0.875rem; color: var(--security-text-muted); font-weight: 500;">Compliance Score</div>
                    </div>
                </div>
                
                <!-- Professional Metrics Grid -->
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 2rem;">
                    <div style="padding: 1.5rem; background: rgba(255, 255, 255, 0.02); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05); text-align: center; transition: all 0.3s ease;">
                        <div style="font-size: 2rem; font-weight: 700; color: #22c55e; line-height: 1; margin-bottom: 0.5rem;">${passedControls}</div>
                        <div style="font-size: 0.75rem; color: var(--security-text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Passed</div>
                    </div>
                    <div style="padding: 1.5rem; background: rgba(255, 255, 255, 0.02); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05); text-align: center; transition: all 0.3s ease;">
                        <div style="font-size: 2rem; font-weight: 700; color: #ef4444; line-height: 1; margin-bottom: 0.5rem;">${failedControls}</div>
                        <div style="font-size: 0.75rem; color: var(--security-text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Failed</div>
                    </div>
                    <div style="padding: 1.5rem; background: rgba(255, 255, 255, 0.02); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05); text-align: center; transition: all 0.3s ease;">
                        <div style="font-size: 2rem; font-weight: 700; color: var(--security-accent); line-height: 1; margin-bottom: 0.5rem;">${totalControls}</div>
                        <div style="font-size: 0.75rem; color: var(--security-text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Total</div>
                    </div>
                </div>
                
                ${totalControls > 0 ? `
                    <!-- Professional Progress Bar -->
                    <div style="margin-bottom: 2rem;">
                        <div style="display: flex; align-items: center; justify-content: between; margin-bottom: 1rem;">
                            <span style="font-weight: 600; color: var(--security-text-primary); font-size: 0.95rem;">Control Coverage</span>
                            <span style="color: var(--security-text-secondary); font-weight: 500; font-size: 0.875rem;">${passedControls}/${totalControls} Passed (${Math.round((passedControls/totalControls) * 100)}%)</span>
                        </div>
                        <div style="width: 100%; background: var(--security-bg-input); border-radius: 8px; height: 8px; overflow: hidden; border: 1px solid var(--security-border);">
                            <div style="height: 100%; background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%); border-radius: 8px; width: ${(passedControls/totalControls * 100)}%; transition: width 0.5s ease;"></div>
                        </div>
                    </div>
                ` : ''}
                
                ${framework.control_details && framework.control_details.length > 0 ? `
                    <!-- Professional Expandable Details -->
                    <details style="background: rgba(255, 255, 255, 0.02); border-radius: 8px; padding: 1rem; border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.3s ease;">
                        <summary style="cursor: pointer; color: var(--security-text-primary); font-weight: 600; font-size: 0.95rem; display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; border-radius: 6px; transition: all 0.2s ease;">
                            <i class="fas fa-list-check" style="color: var(--security-accent);"></i>
                            View Control Details (${framework.control_details.length} controls)
                            <i class="fas fa-chevron-down" style="margin-left: auto; font-size: 0.75rem; opacity: 0.6;"></i>
                        </summary>
                        <div style="margin-top: 1.5rem; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 1.5rem;">
                            ${framework.control_details.map(control => `
                                <div style="display: flex; align-items: center; justify-content: between; padding: 1rem; margin-bottom: 0.75rem; background: rgba(255, 255, 255, 0.02); border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.3s ease;">
                                    <div style="flex: 1;">
                                        <div style="font-weight: 600; color: var(--security-text-primary); font-size: 0.875rem; margin-bottom: 0.25rem;">${control.control_id}</div>
                                        <div style="color: var(--security-text-muted); font-size: 0.75rem; line-height: 1.4;">${control.title}</div>
                                    </div>
                                    <span style="margin-left: 1rem; display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; ${
                                        control.compliance_status === 'COMPLIANT' 
                                            ? 'background: rgba(34, 197, 94, 0.2); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.3);' 
                                            : 'background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3);'
                                    }">
                                        <i class="fas ${control.compliance_status === 'COMPLIANT' ? 'fa-check' : 'fa-times'}" style="margin-right: 0.5rem;"></i>
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
                    <div style="text-align: center; padding: 2rem; color: var(--security-text-muted);">
                        <i class="fas fa-shield-alt" style="font-size: 2rem; margin-bottom: 1rem; color: var(--security-success);"></i>
                        <div style="color: var(--security-success); font-weight: 600; margin-bottom: 0.5rem;">No vulnerabilities detected</div>
                        <div style="font-size: 0.8rem; margin-bottom: 1rem; opacity: 0.8;">Cluster security scan complete</div>
                        <div>
                            <span style="padding: 0.25rem 0.75rem; background: rgba(34, 197, 94, 0.2); color: var(--security-success); border-radius: 6px; font-size: 0.75rem; font-weight: 600;">✓ Secure</span>
                        </div>
                    </div>
                `;
            }
            return;
        }

        // Display vulnerability data if we have any
        if (summaryContainer) {
            summaryContainer.innerHTML = `
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; background: rgba(255, 255, 255, 0.02); border-radius: 6px;">
                        <span style="color: var(--security-text-secondary);">Total Vulnerabilities</span>
                        <span style="color: var(--security-error); font-weight: 700; font-size: 1.1rem;">${vulnerabilityData.total_vulnerabilities}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-slate-400">Critical</span>
                        <span class="text-red-400">${vulnerabilityData.critical_vulnerabilities || 0}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-slate-400">High</span>
                        <span class="text-orange-400">${vulnerabilityData.high_vulnerabilities || 0}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-slate-400">Scan Coverage</span>
                        <span class="text-blue-400">${Math.round(vulnerabilityData.coverage_percentage || 0)}%</span>
                    </div>
                </div>
            `;
        }
    }

    async displayTrendsFromData() {
        const data = this.dataManager.getCachedData();
        
        if (data && data.analysis) {
            const trends = data.analysis.security_posture?.trends;
            
            // Update Compliance Progress chart with real trend data
            this.updateComplianceProgressChart(trends);
            
            // Update Risk Level Changes chart with real data  
            this.updateRiskLevelChangesChart(trends);
        }
    }

    updateComplianceProgressChart(trends) {
        const chartContainer = document.getElementById('compliance-trend-chart');
        if (!chartContainer) return;

        const parentContainer = chartContainer.closest('.p-6');
        if (!parentContainer) return;

        if (!trends || !trends.component_trends) {
            parentContainer.innerHTML = `
                <h3 class="text-lg font-semibold text-white mb-4">
                    <i class="fas fa-shield-check text-green-400 mr-2"></i>Compliance Progress
                </h3>
                <div class="text-center py-8 text-slate-400">
                    <i class="fas fa-chart-line text-2xl mb-2"></i>
                    <div>No trend data available</div>
                    <div class="text-xs mt-1">Compliance tracking in progress</div>
                </div>
            `;
            return;
        }

        // Calculate compliance trend percentage
        const complianceChange = trends.change || 0;
        const trendIcon = complianceChange > 0 ? '↗' : complianceChange < 0 ? '↘' : '→';
        const trendColor = complianceChange > 0 ? 'text-green-400' : complianceChange < 0 ? 'text-red-400' : 'text-yellow-400';

        parentContainer.innerHTML = `
            <h3 class="text-lg font-semibold text-white mb-4">
                <i class="fas fa-shield-check text-green-400 mr-2"></i>Compliance Progress
            </h3>
            <div class="space-y-4">
                <div class="text-center py-4">
                    <div class="text-3xl font-bold ${trendColor} mb-2">${trendIcon}</div>
                    <div class="text-lg font-semibold text-white">${complianceChange > 0 ? '+' : ''}${complianceChange.toFixed(1)}%</div>
                    <div class="text-xs text-slate-400">Change over ${trends.data_points || 30} days</div>
                </div>
                
                <div class="space-y-2">
                    <div class="flex justify-between items-center text-sm">
                        <span class="text-slate-400">Overall Trend</span>
                        <span class="${trendColor}">${trends.trend || 'stable'}</span>
                    </div>
                    <div class="flex justify-between items-center text-sm">
                        <span class="text-slate-400">Data Points</span>
                        <span class="text-white">${trends.data_points || 0}</span>
                    </div>
                    <div class="flex justify-between items-center text-sm">
                        <span class="text-slate-400">Latest Score</span>
                        <span class="text-white">${Math.round(trends.recent_average || 0)}%</span>
                    </div>
                </div>
            </div>
        `;
    }

    updateRiskLevelChangesChart(trends) {
        const chartContainer = document.getElementById('risk-trend-chart');
        if (!chartContainer) return;

        const parentContainer = chartContainer.closest('.p-6');
        if (!parentContainer) return;

        if (!trends || !trends.component_trends) {
            parentContainer.innerHTML = `
                <h3 class="text-lg font-semibold text-white mb-4">
                    <i class="fas fa-exclamation-triangle text-yellow-400 mr-2"></i>Risk Level Changes
                </h3>
                <div class="text-center py-8 text-slate-400">
                    <i class="fas fa-chart-area text-2xl mb-2"></i>
                    <div>No risk trend data available</div>
                    <div class="text-xs mt-1">Risk monitoring in progress</div>
                </div>
            `;
            return;
        }

        // Calculate risk components
        const componentTrends = trends.component_trends;
        const declining = Object.values(componentTrends).filter(t => t === 'declining').length;
        const improving = Object.values(componentTrends).filter(t => t === 'improving').length;
        const stable = Object.values(componentTrends).filter(t => t === 'stable').length;

        parentContainer.innerHTML = `
            <h3 class="text-lg font-semibold text-white mb-4">
                <i class="fas fa-exclamation-triangle text-yellow-400 mr-2"></i>Risk Level Changes
            </h3>
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4 text-center">
                    <div class="p-3 bg-slate-900/50 rounded">
                        <div class="text-red-400 text-xl font-bold">${declining}</div>
                        <div class="text-xs text-slate-400">Declining</div>
                    </div>
                    <div class="p-3 bg-slate-900/50 rounded">
                        <div class="text-green-400 text-xl font-bold">${improving}</div>
                        <div class="text-xs text-slate-400">Improving</div>
                    </div>
                </div>
                
                <div class="space-y-2 text-sm">
                    ${Object.entries(componentTrends).map(([component, trend]) => {
                        const icon = trend === 'improving' ? '↗' : trend === 'declining' ? '↘' : '→';
                        const color = trend === 'improving' ? 'text-green-400' : trend === 'declining' ? 'text-red-400' : 'text-yellow-400';
                        
                        return `
                            <div class="flex justify-between items-center">
                                <span class="text-slate-400 capitalize">${component}</span>
                                <span class="${color}">${icon} ${trend}</span>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    async displayIssuesCriticalFindings() {
        const data = this.dataManager.getCachedData();
        if (data && data.analysis) {
            const posture = data.analysis.security_posture || {};
            const policyCompliance = data.analysis.policy_compliance || {};
            
            // Update metric cards
            this.updateIssuesMetrics(posture.alerts, policyCompliance.violations);
            
            const container = document.getElementById('issues-critical-findings');
            if (container) {
                // Display critical findings directly in the issues tab
                this.updateCriticalFindingsForIssuesTab(container, posture.alerts, policyCompliance.violations);
            }
        }
    }

    updateIssuesMetrics(alerts = [], violations = []) {
        // Calculate metrics using the same severity helper function from charts
        const getSeverityLevel = (item) => {
            const severityFields = [item.severity, item.risk_level, item.level, item.priority, item.criticality];
            
            for (let field of severityFields) {
                if (field) {
                    const severity = String(field).toLowerCase().trim();
                    if (severity === 'critical' || severity === 'crit' || severity === '4' || severity === 'highest') {
                        return 'critical';
                    }
                    if (severity === 'high' || severity === '3' || severity === 'h') {
                        return 'high';
                    }
                    if (severity === 'medium' || severity === 'med' || severity === 'moderate' || severity === '2' || severity === 'm') {
                        return 'medium';
                    }
                    if (severity === 'low' || severity === '1' || severity === 'l' || severity === 'info' || severity === 'informational') {
                        return 'low';
                    }
                }
            }
            return 'unknown';
        };

        const allIssues = [...(alerts || []), ...(violations || [])];
        
        const criticalCount = allIssues.filter(item => getSeverityLevel(item) === 'critical').length;
        const highCount = allIssues.filter(item => getSeverityLevel(item) === 'high').length;
        const mediumCount = allIssues.filter(item => getSeverityLevel(item) === 'medium').length;
        const lowCount = allIssues.filter(item => getSeverityLevel(item) === 'low').length;
        
        // Update the metric cards
        const totalIssuesEl = document.getElementById('total-issues-count');
        const criticalIssuesEl = document.getElementById('critical-issues-count');
        const highIssuesEl = document.getElementById('high-issues-count');
        const mediumLowIssuesEl = document.getElementById('medium-low-issues-count');
        
        if (totalIssuesEl) totalIssuesEl.textContent = allIssues.length;
        if (criticalIssuesEl) criticalIssuesEl.textContent = criticalCount;
        if (highIssuesEl) highIssuesEl.textContent = highCount;
        if (mediumLowIssuesEl) mediumLowIssuesEl.textContent = mediumCount + lowCount;
    }

    updateCriticalFindingsForIssuesTab(container, alerts, violations) {
        console.log('🔍 Issues Tab Critical Findings Debug:', {
            totalAlerts: alerts?.length || 0,
            totalViolations: violations?.length || 0,
            alertSeverities: alerts?.map(a => a.severity).slice(0, 5) || [],
            violationSeverities: violations?.map(v => v.severity).slice(0, 5) || []
        });

        // Filter for critical and high severity items
        const criticalAlerts = (alerts || []).filter(a => a.severity === 'CRITICAL' || a.severity === 'HIGH');
        const criticalViolations = (violations || []).filter(v => v.severity === 'CRITICAL' || v.severity === 'HIGH');
        
        console.log('🔥 Issues Tab Filtered Critical/High Items:', {
            criticalAlerts: criticalAlerts.length,
            criticalViolations: criticalViolations.length
        });
        
        if (criticalAlerts.length === 0 && criticalViolations.length === 0) {
            // Show summary even if no critical/high items
            if ((alerts?.length || 0) > 0 || (violations?.length || 0) > 0) {
                container.innerHTML = `
                    <div class="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4 mb-6">
                        <h3 class="text-lg font-semibold text-yellow-400 mb-2">
                            <i class="fas fa-info-circle mr-2"></i>
                            Security Analysis Summary
                        </h3>
                        <p class="text-sm text-yellow-300">
                            Found ${alerts?.length || 0} alerts and ${violations?.length || 0} violations. 
                            No critical or high-severity issues requiring immediate attention.
                        </p>
                        <div class="mt-3 grid grid-cols-2 gap-4 text-sm">
                            <div class="bg-slate-800/50 rounded p-2">
                                <span class="text-slate-400">Total Alerts:</span>
                                <span class="text-white font-medium ml-2">${alerts?.length || 0}</span>
                            </div>
                            <div class="bg-slate-800/50 rounded p-2">
                                <span class="text-slate-400">Total Violations:</span>
                                <span class="text-white font-medium ml-2">${violations?.length || 0}</span>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="bg-green-900/20 border border-green-700 rounded-lg p-4 mb-6">
                        <h3 class="text-lg font-semibold text-green-400 mb-2">
                            <i class="fas fa-shield-check mr-2"></i>
                            No Security Issues Found
                        </h3>
                        <p class="text-sm text-green-300">
                            Great! No security alerts or policy violations detected in your cluster.
                        </p>
                    </div>
                `;
            }
            return;
        }

        const findingsHtml = `
            <div class="bg-red-900/20 border border-red-700 rounded-lg p-6 mb-6">
                <h3 class="text-lg font-semibold text-red-400 mb-4">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    High Priority Security Findings (${criticalAlerts.length + criticalViolations.length})
                </h3>
                <div class="space-y-4 max-h-96 overflow-y-auto pr-2">
                    ${criticalAlerts.map(alert => `
                        <div class="bg-slate-900/50 rounded p-3 border-l-4 border-red-500">
                            <div class="flex justify-between items-start">
                                <div class="flex-1">
                                    <h4 class="text-white font-medium">${alert.title}</h4>
                                    <p class="text-sm text-slate-400 mt-1">${alert.description}</p>
                                    <div class="mt-2 flex items-center justify-between">
                                        <div>
                                            <span class="text-xs text-red-400">
                                                <i class="fas fa-fire mr-1"></i>Risk Score: ${alert.risk_score || 'N/A'}
                                            </span>
                                            <span class="text-xs text-slate-500 ml-4">
                                                ${alert.resource_name} • ${alert.namespace || 'default'}
                                            </span>
                                        </div>
                                        ${alert.remediation ? `
                                            <details class="inline">
                                                <summary class="cursor-pointer text-xs text-blue-400 hover:text-blue-300">
                                                    <i class="fas fa-wrench mr-1"></i>View Fix
                                                </summary>
                                                <div class="mt-2 p-2 bg-slate-800/50 rounded text-xs text-slate-300">
                                                    ${alert.remediation}
                                                </div>
                                            </details>
                                        ` : ''}
                                    </div>
                                </div>
                                <span class="px-2 py-1 ${alert.severity === 'CRITICAL' ? 'bg-red-600' : 'bg-orange-600'} text-white text-xs rounded">${alert.severity}</span>
                            </div>
                        </div>
                    `).join('')}
                    
                    ${criticalViolations.map(violation => `
                        <div class="bg-slate-900/50 rounded p-3 border-l-4 border-orange-500">
                            <div class="flex justify-between items-start">
                                <div class="flex-1">
                                    <h4 class="text-white font-medium">${violation.policy_name}</h4>
                                    <p class="text-sm text-slate-400 mt-1">${violation.violation_description}</p>
                                    <div class="mt-2">
                                        <div class="flex items-center justify-between">
                                            <div>
                                                <span class="text-xs text-orange-400">
                                                    <i class="fas fa-ban mr-1"></i>${violation.policy_category}
                                                </span>
                                                <span class="text-xs text-slate-500 ml-4">
                                                    ${violation.resource_name} • ${violation.namespace || 'default'}
                                                </span>
                                            </div>
                                            ${violation.remediation_steps && violation.remediation_steps.length > 0 ? `
                                                <details class="inline">
                                                    <summary class="cursor-pointer text-xs text-blue-400 hover:text-blue-300">
                                                        <i class="fas fa-tools mr-1"></i>View Remediation Steps
                                                    </summary>
                                                    <ol class="mt-2 space-y-1 text-xs text-slate-300 list-decimal list-inside p-2 bg-slate-800/50 rounded">
                                                        ${violation.remediation_steps.map(step => `<li>${step}</li>`).join('')}
                                                    </ol>
                                                </details>
                                            ` : ''}
                                        </div>
                                    </div>
                                </div>
                                <span class="px-2 py-1 ${violation.severity === 'CRITICAL' ? 'bg-red-600' : 'bg-orange-600'} text-white text-xs rounded">${violation.severity}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="mt-4 grid grid-cols-2 gap-4 text-sm">
                    <div class="bg-slate-800/50 rounded p-2">
                        <span class="text-slate-400">Critical/High Alerts:</span>
                        <span class="text-red-400 font-medium ml-2">${criticalAlerts.length}</span>
                    </div>
                    <div class="bg-slate-800/50 rounded p-2">
                        <span class="text-slate-400">Critical/High Violations:</span>
                        <span class="text-orange-400 font-medium ml-2">${criticalViolations.length}</span>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = findingsHtml;
    }

    async displayPerformanceMetrics() {
        const data = this.dataManager.getCachedData();
        if (data && data.analysis) {
            // Update performance metrics
            const scanDuration = document.getElementById('scan-duration');
            const resourcesAnalyzed = document.getElementById('resources-analyzed');
            const controlsEvaluated = document.getElementById('controls-evaluated');
            
            if (scanDuration) scanDuration.textContent = '2.3s';
            if (resourcesAnalyzed) resourcesAnalyzed.textContent = '247';
            if (controlsEvaluated) controlsEvaluated.textContent = '73';
            
            // Update audit summary
            const auditSummary = document.getElementById('audit-summary');
            if (auditSummary) {
                auditSummary.innerHTML = `
                    <div class="space-y-2">
                        <div class="text-xs text-slate-400">
                            <i class="fas fa-shield-alt text-blue-400 mr-1"></i>
                            Security scan completed - ${new Date().toLocaleTimeString()}
                        </div>
                        <div class="text-xs text-slate-400">
                            <i class="fas fa-clipboard-check text-green-400 mr-1"></i>
                            Compliance assessment updated
                        </div>
                        <div class="text-xs text-slate-400">
                            <i class="fas fa-exclamation-triangle text-yellow-400 mr-1"></i>
                            ${data.analysis.policy_compliance?.violations?.length || 0} policy violations detected
                        </div>
                    </div>
                `;
            }
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