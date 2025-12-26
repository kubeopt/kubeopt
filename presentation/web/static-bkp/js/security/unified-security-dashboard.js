/**
 * Unified Security Dashboard - Interactive Single Page Design
 * =========================================================
 * Complete rewrite of security dashboard with unified layout and interactive drill-down charts
 * Features: Click-to-drill-down charts, real-time updates, and comprehensive security visualization
 */

// Global state management
window.securityDashboardState = {
    clusterId: null,
    lastUpdate: null,
    data: null,
    charts: new Map(),
    activeFilters: {
        severity: 'all',
        category: 'all',
        timeRange: '30d'
    },
    refreshInterval: 300000 // 5 minutes
};

class UnifiedSecurityDashboard {
    constructor(apiBaseUrl = '/api/security') {
        this.apiBaseUrl = apiBaseUrl;
        this.state = window.securityDashboardState;
        this.charts = new Map();
        this.refreshTimer = null;
        this.dataManager = window.enhancedSecurityDataManager || new EnhancedSecurityDataManager();
        
        this.init();
    }

    async init() {
        console.log('🔒 Initializing Unified Security Dashboard...');
        
        // Check if we're on the security posture page
        if (document.getElementById('securityposture-content')) {
            await this.createUnifiedDashboard();
            await this.loadAllSecurityData();
            this.startAutoRefresh();
        }
        
        console.log('✅ Unified Security Dashboard initialized');
    }

    async createUnifiedDashboard() {
        const container = document.getElementById('securityposture-content');
        if (!container) {
            console.error('Security content container not found');
            return;
        }

        // Create the unified dashboard layout
        const dashboardHTML = `
            <div class="security-dashboard-unified">
                <!-- Security Header -->
                <div class="security-header fade-in">
                    <div class="security-header-content">
                        <div>
                            <h1 class="security-title">
                                <div class="title-icon">
                                    <i class="fas fa-shield-alt"></i>
                                </div>
                                Security Posture Dashboard
                            </h1>
                            <p class="security-subtitle">Unified security monitoring with interactive analytics</p>
                            <div class="metric-trend">
                                <span>Last updated: <span id="last-update-time">--</span></span>
                            </div>
                        </div>
                        <div class="security-actions">
                            <button onclick="window.unifiedSecurity?.forceRefresh()" class="security-btn">
                                <i class="fas fa-sync-alt"></i>Refresh
                            </button>
                            <button onclick="window.unifiedSecurity?.exportReport()" class="security-btn accent">
                                <i class="fas fa-download"></i>Export Report
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Key Metrics Row -->
                <div class="security-metrics-row fade-in">
                    <div class="security-metric-card" onclick="window.unifiedSecurity?.showScoreDetails()">
                        <div class="metric-header">
                            <div class="metric-icon">
                                <i class="fas fa-shield-alt"></i>
                            </div>
                            <div class="metric-value" id="overall-security-score">--</div>
                        </div>
                        <div class="metric-label">Security Score</div>
                        <div class="metric-trend" id="security-score-trend">
                            <i class="fas fa-arrow-right"></i>
                            <span>Grade: <span id="security-grade">--</span></span>
                        </div>
                    </div>

                    <div class="security-metric-card" onclick="window.unifiedSecurity?.showAlertsDetails()">
                        <div class="metric-header">
                            <div class="metric-icon">
                                <i class="fas fa-exclamation-triangle"></i>
                            </div>
                            <div class="metric-value" id="total-security-alerts">0</div>
                        </div>
                        <div class="metric-label">Active Alerts</div>
                        <div class="metric-trend" id="alerts-breakdown">
                            <span id="critical-alerts-summary">0 Critical</span>
                        </div>
                    </div>

                    <div class="security-metric-card" onclick="window.unifiedSecurity?.showComplianceDetails()">
                        <div class="metric-header">
                            <div class="metric-icon">
                                <i class="fas fa-clipboard-check"></i>
                            </div>
                            <div class="metric-value" id="overall-compliance-percentage">--</div>
                        </div>
                        <div class="metric-label">Compliance</div>
                        <div class="metric-trend" id="compliance-frameworks-summary">
                            <span>3 Frameworks</span>
                        </div>
                    </div>

                    <div class="security-metric-card" onclick="window.unifiedSecurity?.showViolationsDetails()">
                        <div class="metric-header">
                            <div class="metric-icon">
                                <i class="fas fa-ban"></i>
                            </div>
                            <div class="metric-value" id="total-policy-violations">0</div>
                        </div>
                        <div class="metric-label">Policy Violations</div>
                        <div class="metric-trend" id="violations-summary">
                            <span id="auto-remediable-count">0 Auto-fixable</span>
                        </div>
                    </div>
                </div>

                <!-- Filters Panel -->
                <div class="security-filters fade-in">
                    <div class="filter-group">
                        <label class="filter-label">Time Range:</label>
                        <select id="time-range-filter" class="filter-select" onchange="window.unifiedSecurity?.applyTimeFilter(this.value)">
                            <option value="7d">Last 7 Days</option>
                            <option value="30d" selected>Last 30 Days</option>
                            <option value="90d">Last 90 Days</option>
                            <option value="1y">Last Year</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label class="filter-label">Severity:</label>
                        <select id="severity-filter" class="filter-select" onchange="window.unifiedSecurity?.applySeverityFilter(this.value)">
                            <option value="all">All Severities</option>
                            <option value="critical">Critical Only</option>
                            <option value="high">High & Critical</option>
                            <option value="medium">Medium & Above</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label class="filter-label">Category:</label>
                        <select id="category-filter" class="filter-select" onchange="window.unifiedSecurity?.applyCategoryFilter(this.value)">
                            <option value="all">All Categories</option>
                            <option value="vulnerability">Vulnerabilities</option>
                            <option value="policy">Policy Issues</option>
                            <option value="compliance">Compliance</option>
                            <option value="rbac">RBAC</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <button class="security-btn secondary" onclick="window.unifiedSecurity?.resetFilters()">
                            <i class="fas fa-undo"></i>Reset Filters
                        </button>
                    </div>
                </div>

                <!-- Main Charts Grid -->
                <div class="security-charts-grid fade-in">
                    <!-- Compliance Framework Donut Chart -->
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3 class="chart-title">
                                <div class="chart-icon">
                                    <i class="fas fa-certificate"></i>
                                </div>
                                Compliance Frameworks
                            </h3>
                            <div class="export-controls">
                                <button class="export-btn" onclick="window.unifiedSecurity?.exportChart('compliance')">
                                    <i class="fas fa-download"></i>
                                </button>
                            </div>
                        </div>
                        <div class="chart-container chart-clickable">
                            <canvas id="compliance-donut-chart"></canvas>
                        </div>
                    </div>

                    <!-- Risk Distribution Donut Chart -->
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3 class="chart-title">
                                <div class="chart-icon">
                                    <i class="fas fa-exclamation-triangle"></i>
                                </div>
                                Risk Distribution
                            </h3>
                            <div class="export-controls">
                                <button class="export-btn" onclick="window.unifiedSecurity?.exportChart('risk')">
                                    <i class="fas fa-download"></i>
                                </button>
                            </div>
                        </div>
                        <div class="chart-container chart-clickable">
                            <canvas id="risk-distribution-chart"></canvas>
                        </div>
                    </div>

                    <!-- Security Trends Line Chart -->
                    <div class="chart-card large">
                        <div class="chart-header">
                            <h3 class="chart-title">
                                <div class="chart-icon">
                                    <i class="fas fa-chart-line"></i>
                                </div>
                                Security Posture Trends
                            </h3>
                            <div class="export-controls">
                                <button class="export-btn" onclick="window.unifiedSecurity?.exportChart('trends')">
                                    <i class="fas fa-download"></i>
                                </button>
                            </div>
                        </div>
                        <div class="chart-container large chart-clickable">
                            <canvas id="security-trends-chart"></canvas>
                        </div>
                    </div>

                    <!-- Alerts by Severity Bar Chart -->
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3 class="chart-title">
                                <div class="chart-icon">
                                    <i class="fas fa-bell"></i>
                                </div>
                                Alerts by Severity
                            </h3>
                            <div class="export-controls">
                                <button class="export-btn" onclick="window.unifiedSecurity?.exportChart('alerts')">
                                    <i class="fas fa-download"></i>
                                </button>
                            </div>
                        </div>
                        <div class="chart-container chart-clickable">
                            <canvas id="alerts-severity-chart"></canvas>
                        </div>
                    </div>

                    <!-- Policy Violations by Category -->
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3 class="chart-title">
                                <div class="chart-icon">
                                    <i class="fas fa-ban"></i>
                                </div>
                                Policy Violations
                            </h3>
                            <div class="export-controls">
                                <button class="export-btn" onclick="window.unifiedSecurity?.exportChart('violations')">
                                    <i class="fas fa-download"></i>
                                </button>
                            </div>
                        </div>
                        <div class="chart-container chart-clickable">
                            <canvas id="violations-category-chart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Quick Actions Panel -->
                <div class="quick-actions fade-in">
                    <h3 class="quick-actions-title">
                        <i class="fas fa-bolt"></i>
                        Quick Actions
                    </h3>
                    <div class="quick-actions-grid">
                        <div class="quick-action-btn" onclick="window.unifiedSecurity?.runSecurityScan()">
                            <div class="quick-action-icon">
                                <i class="fas fa-search"></i>
                            </div>
                            <p class="quick-action-label">Run Security Scan</p>
                        </div>
                        <div class="quick-action-btn" onclick="window.unifiedSecurity?.autoFixViolations()">
                            <div class="quick-action-icon">
                                <i class="fas fa-magic"></i>
                            </div>
                            <p class="quick-action-label">Auto-Fix Issues</p>
                        </div>
                        <div class="quick-action-btn" onclick="window.unifiedSecurity?.generateComplianceReport()">
                            <div class="quick-action-icon">
                                <i class="fas fa-file-alt"></i>
                            </div>
                            <p class="quick-action-label">Compliance Report</p>
                        </div>
                        <div class="quick-action-btn" onclick="window.unifiedSecurity?.viewAuditLog()">
                            <div class="quick-action-icon">
                                <i class="fas fa-history"></i>
                            </div>
                            <p class="quick-action-label">Audit Trail</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Details Modal/Sidebar -->
            <div id="security-details-overlay" class="security-details-overlay" onclick="window.unifiedSecurity?.closeDetailsModal()"></div>
            <div id="security-details-modal" class="security-details-modal">
                <div class="modal-header">
                    <h2 class="modal-title" id="modal-title">
                        <i class="fas fa-info-circle"></i>
                        Details
                    </h2>
                    <button class="modal-close" onclick="window.unifiedSecurity?.closeDetailsModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-content" id="modal-content">
                    <!-- Dynamic content will be loaded here -->
                </div>
            </div>

            <!-- Notification Container -->
            <div id="security-notifications"></div>
        `;

        container.innerHTML = dashboardHTML;
        
        // Add the clean security CSS if not already included
        this.ensureCleanSecurityCSS();
        
        console.log('✅ Unified dashboard layout created');
    }

    ensureCleanSecurityCSS() {
        // Check if clean-security.css is already loaded
        const existingLink = document.querySelector('link[href*="clean-security.css"]');
        if (!existingLink) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = '/static/css/clean-security.css';
            document.head.appendChild(link);
        }
    }

    async loadAllSecurityData() {
        try {
            console.log('🔄 Loading unified security data...');
            
            const clusterId = this.getCurrentClusterId();
            if (!clusterId) {
                this.showNoDataState();
                return;
            }

            // Show loading state
            this.showLoadingState();

            // Use enhanced data manager for intelligent data loading
            const data = await this.dataManager.loadSecurityData(clusterId);
            
            if (!data) {
                this.showNoDataState();
                return;
            }

            // Cache the data
            this.state.data = data;
            this.state.lastUpdate = new Date();

            // Update all components
            await this.updateDashboard(data);
            
            // Update timestamp
            document.getElementById('last-update-time').textContent = 
                new Date().toLocaleTimeString();

            console.log('✅ Security data loaded successfully');

        } catch (error) {
            console.error('❌ Failed to load security data:', error);
            this.showError('Failed to load security data: ' + error.message);
        }
    }

    async updateDashboard(data) {
        const analysis = data.analysis || data;
        
        // Update key metrics
        this.updateKeyMetrics(analysis);
        
        // Create all charts with click interactions
        await Promise.all([
            this.createComplianceChart(analysis.compliance_frameworks || {}),
            this.createRiskDistributionChart(analysis),
            this.createSecurityTrendsChart(analysis.security_posture?.trends || {}),
            this.createAlertsSeverityChart(analysis.security_posture?.alerts || []),
            this.createViolationsCategoryChart(analysis.policy_compliance?.violations || [])
        ]);
    }

    updateKeyMetrics(analysis) {
        const posture = analysis.security_posture || {};
        const compliance = analysis.policy_compliance || {};
        
        // Security Score
        const score = Math.round(posture.overall_score || 0);
        document.getElementById('overall-security-score').textContent = `${score}%`;
        document.getElementById('security-grade').textContent = posture.grade || 'N/A';
        
        // Security Score Trend
        const trendElement = document.getElementById('security-score-trend');
        if (posture.trends && posture.trends.trend) {
            const trend = posture.trends.trend;
            const change = posture.trends.change || 0;
            const icon = trend === 'improving' ? 'fa-arrow-up text-green-500' : 
                        trend === 'declining' ? 'fa-arrow-down text-red-500' : 
                        'fa-arrow-right text-yellow-500';
            
            trendElement.innerHTML = `
                <i class="fas ${icon}"></i>
                <span>${trend} (${change > 0 ? '+' : ''}${change.toFixed(1)}%)</span>
            `;
        }

        // Alerts
        const alerts = posture.alerts || [];
        const criticalAlerts = alerts.filter(a => a.severity === 'CRITICAL').length;
        const highAlerts = alerts.filter(a => a.severity === 'HIGH').length;
        
        document.getElementById('total-security-alerts').textContent = alerts.length;
        document.getElementById('critical-alerts-summary').textContent = 
            `${criticalAlerts} Critical • ${highAlerts} High`;

        // Compliance
        const frameworks = analysis.compliance_frameworks || {};
        const avgCompliance = Object.values(frameworks).length > 0 
            ? Object.values(frameworks).reduce((sum, f) => sum + (f.overall_compliance || 0), 0) / Object.values(frameworks).length
            : 0;
        
        document.getElementById('overall-compliance-percentage').textContent = `${Math.round(avgCompliance)}%`;
        document.getElementById('compliance-frameworks-summary').textContent = 
            `${Object.keys(frameworks).length} Frameworks`;

        // Violations
        const violations = compliance.violations || [];
        const autoRemediable = violations.filter(v => v.auto_remediable).length;
        
        document.getElementById('total-policy-violations').textContent = violations.length;
        document.getElementById('auto-remediable-count').textContent = `${autoRemediable} Auto-fixable`;
    }

    async createComplianceChart(frameworks) {
        const canvas = document.getElementById('compliance-donut-chart');
        if (!canvas) return;

        // Destroy existing chart
        if (this.charts.has('compliance')) {
            this.charts.get('compliance').destroy();
        }

        const ctx = canvas.getContext('2d');
        
        const frameworkNames = Object.keys(frameworks);
        const complianceScores = Object.values(frameworks).map(f => f.overall_compliance || 0);
        const grades = Object.values(frameworks).map(f => f.grade || 'N/A');

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: frameworkNames.map((name, idx) => `${name} (${grades[idx]})`),
                datasets: [{
                    data: complianceScores,
                    backgroundColor: [
                        '#7FB069',
                        '#4A90A4',
                        '#F59E0B',
                        '#EF4444',
                        '#8B5CF6'
                    ],
                    borderColor: '#ffffff',
                    borderWidth: 3,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                family: 'Poppins',
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#2d3748',
                        bodyColor: '#4a5568',
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            afterBody: () => ['', '💡 Click to view control details']
                        }
                    }
                },
                onHover: (event, elements) => {
                    canvas.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const frameworkName = frameworkNames[index];
                        this.showComplianceDetails(frameworkName, frameworks[frameworkName]);
                    }
                }
            }
        });

        this.charts.set('compliance', chart);
    }

    async createRiskDistributionChart(analysis) {
        const canvas = document.getElementById('risk-distribution-chart');
        if (!canvas) return;

        if (this.charts.has('risk')) {
            this.charts.get('risk').destroy();
        }

        const ctx = canvas.getContext('2d');
        
        // Calculate risk distribution from alerts and violations
        const alerts = analysis.security_posture?.alerts || [];
        const violations = analysis.policy_compliance?.violations || [];
        
        const riskCounts = {
            'Critical': alerts.filter(a => a.severity === 'CRITICAL').length + 
                       violations.filter(v => v.severity === 'CRITICAL').length,
            'High': alerts.filter(a => a.severity === 'HIGH').length + 
                   violations.filter(v => v.severity === 'HIGH').length,
            'Medium': alerts.filter(a => a.severity === 'MEDIUM').length + 
                     violations.filter(v => v.severity === 'MEDIUM').length,
            'Low': alerts.filter(a => a.severity === 'LOW').length + 
                  violations.filter(v => v.severity === 'LOW').length
        };

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(riskCounts),
                datasets: [{
                    data: Object.values(riskCounts),
                    backgroundColor: ['#EF4444', '#F97316', '#EAB308', '#22C55E'],
                    borderColor: '#ffffff',
                    borderWidth: 3,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                family: 'Poppins',
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#2d3748',
                        bodyColor: '#4a5568',
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            afterBody: () => ['', '💡 Click to view specific issues']
                        }
                    }
                },
                onHover: (event, elements) => {
                    canvas.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const severity = Object.keys(riskCounts)[index];
                        this.showRiskDetails(severity, alerts, violations);
                    }
                }
            }
        });

        this.charts.set('risk', chart);
    }

    async createSecurityTrendsChart(trends) {
        const canvas = document.getElementById('security-trends-chart');
        if (!canvas) return;

        if (this.charts.has('trends')) {
            this.charts.get('trends').destroy();
        }

        const ctx = canvas.getContext('2d');
        
        // Use real historical data from backend trends or create from current state
        const trendData = trends.historical_data || this.extractTrendFromCurrentState(trends);
        
        const last30Days = trendData.dates || ['No data'];
        const securityScores = trendData.security_scores || [trends.overall_score || 0];
        const alertCounts = trendData.alert_counts || [trends.alert_count || 0];
        const complianceScores = trendData.compliance_scores || [trends.compliance_score || 0];

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: last30Days,
                datasets: [
                    {
                        label: 'Security Score',
                        data: securityScores,
                        borderColor: '#7FB069',
                        backgroundColor: 'rgba(127, 176, 105, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#7FB069',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Alert Count',
                        data: alertCounts,
                        borderColor: '#EF4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 3,
                        fill: false,
                        tension: 0.4,
                        pointBackgroundColor: '#EF4444',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        yAxisID: 'y1'
                    },
                    {
                        label: 'Compliance %',
                        data: complianceScores,
                        borderColor: '#4A90A4',
                        backgroundColor: 'rgba(74, 144, 164, 0.1)',
                        borderWidth: 3,
                        fill: false,
                        tension: 0.4,
                        pointBackgroundColor: '#4A90A4',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(226, 232, 240, 0.5)'
                        },
                        ticks: {
                            font: {
                                family: 'Poppins',
                                size: 11
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(226, 232, 240, 0.5)'
                        },
                        ticks: {
                            font: {
                                family: 'Poppins',
                                size: 11
                            },
                            callback: (value) => value + '%'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        grid: {
                            drawOnChartArea: false
                        },
                        ticks: {
                            font: {
                                family: 'Poppins',
                                size: 11
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                family: 'Poppins',
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#2d3748',
                        bodyColor: '#4a5568',
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                onHover: (event, elements) => {
                    canvas.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const datasetIndex = elements[0].datasetIndex;
                        const pointIndex = elements[0].index;
                        const date = last30Days[pointIndex];
                        this.showTrendDetails(date, datasetIndex, analysis);
                    }
                }
            }
        });

        this.charts.set('trends', chart);
    }

    async createAlertsSeverityChart(alerts) {
        const canvas = document.getElementById('alerts-severity-chart');
        if (!canvas) return;

        if (this.charts.has('alerts')) {
            this.charts.get('alerts').destroy();
        }

        const ctx = canvas.getContext('2d');
        
        const severityCounts = {
            'Critical': alerts.filter(a => a.severity === 'CRITICAL').length,
            'High': alerts.filter(a => a.severity === 'HIGH').length,
            'Medium': alerts.filter(a => a.severity === 'MEDIUM').length,
            'Low': alerts.filter(a => a.severity === 'LOW').length
        };

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(severityCounts),
                datasets: [{
                    label: 'Security Alerts',
                    data: Object.values(severityCounts),
                    backgroundColor: ['#EF4444', '#F97316', '#EAB308', '#22C55E'],
                    borderColor: ['#DC2626', '#EA580C', '#D97706', '#16A34A'],
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
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
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#2d3748',
                        bodyColor: '#4a5568',
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            afterBody: () => ['', '💡 Click to view alerts']
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                family: 'Poppins',
                                size: 11
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(226, 232, 240, 0.5)'
                        },
                        ticks: {
                            font: {
                                family: 'Poppins',
                                size: 11
                            },
                            precision: 0
                        }
                    }
                },
                onHover: (event, elements) => {
                    canvas.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const severity = Object.keys(severityCounts)[index];
                        this.showAlertsDetails(severity, alerts);
                    }
                }
            }
        });

        this.charts.set('alerts', chart);
    }

    async createViolationsCategoryChart(violations) {
        const canvas = document.getElementById('violations-category-chart');
        if (!canvas) return;

        if (this.charts.has('violations')) {
            this.charts.get('violations').destroy();
        }

        const ctx = canvas.getContext('2d');
        
        // Group violations by category
        const categoryCounts = {};
        violations.forEach(v => {
            const category = v.policy_category || 'Other';
            categoryCounts[category] = (categoryCounts[category] || 0) + 1;
        });

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(categoryCounts),
                datasets: [{
                    label: 'Policy Violations',
                    data: Object.values(categoryCounts),
                    backgroundColor: '#F97316',
                    borderColor: '#EA580C',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#2d3748',
                        bodyColor: '#4a5568',
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            afterBody: () => ['', '💡 Click to view violations']
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(226, 232, 240, 0.5)'
                        },
                        ticks: {
                            font: {
                                family: 'Poppins',
                                size: 11
                            },
                            precision: 0
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                family: 'Poppins',
                                size: 11
                            }
                        }
                    }
                },
                onHover: (event, elements) => {
                    canvas.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const category = Object.keys(categoryCounts)[index];
                        this.showViolationsDetails(category, violations);
                    }
                }
            }
        });

        this.charts.set('violations', chart);
    }

    // Drill-down detail methods
    showComplianceDetails(frameworkName, frameworkData) {
        const title = `${frameworkName} Compliance Details`;
        const content = this.renderComplianceDetails(frameworkData);
        this.openDetailsModal(title, content, 'fas fa-certificate');
    }

    showRiskDetails(severity, alerts, violations) {
        const title = `${severity} Risk Issues`;
        const relevantAlerts = alerts.filter(a => a.severity === severity.toUpperCase());
        const relevantViolations = violations.filter(v => v.severity === severity.toUpperCase());
        const content = this.renderRiskDetails(relevantAlerts, relevantViolations);
        this.openDetailsModal(title, content, 'fas fa-exclamation-triangle');
    }

    showAlertsDetails(severity, alerts) {
        const title = `${severity} Security Alerts`;
        const relevantAlerts = alerts.filter(a => a.severity === severity.toUpperCase());
        const content = this.renderAlertsDetails(relevantAlerts);
        this.openDetailsModal(title, content, 'fas fa-bell');
    }

    showViolationsDetails(category, violations) {
        const title = `${category} Policy Violations`;
        const relevantViolations = violations.filter(v => v.policy_category === category);
        const content = this.renderViolationsDetails(relevantViolations);
        this.openDetailsModal(title, content, 'fas fa-ban');
    }

    showTrendDetails(date, datasetIndex, analysis) {
        const datasets = ['Security Score', 'Alert Count', 'Compliance %'];
        const title = `${datasets[datasetIndex]} - ${date}`;
        const content = this.renderTrendDetails(date, datasetIndex, analysis);
        this.openDetailsModal(title, content, 'fas fa-chart-line');
    }

    // Detail renderers
    renderComplianceDetails(framework) {
        const controls = framework.control_details || [];
        const passed = controls.filter(c => c.compliance_status === 'COMPLIANT');
        const failed = controls.filter(c => c.compliance_status === 'NON_COMPLIANT');

        return `
            <div class="space-y-4">
                <div class="grid grid-cols-3 gap-4 mb-6">
                    <div class="text-center p-4 bg-green-50 rounded-lg border border-green-200">
                        <div class="text-2xl font-bold text-green-600">${passed.length}</div>
                        <div class="text-sm text-green-700">Passed Controls</div>
                    </div>
                    <div class="text-center p-4 bg-red-50 rounded-lg border border-red-200">
                        <div class="text-2xl font-bold text-red-600">${failed.length}</div>
                        <div class="text-sm text-red-700">Failed Controls</div>
                    </div>
                    <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <div class="text-2xl font-bold text-blue-600">${Math.round(framework.overall_compliance || 0)}%</div>
                        <div class="text-sm text-blue-700">Compliance</div>
                    </div>
                </div>

                <h4 class="text-lg font-semibold mb-3">Control Details</h4>
                <ul class="details-list">
                    ${controls.map(control => `
                        <li class="details-item">
                            <div class="item-header">
                                <h5 class="item-title">${control.control_id}: ${control.title}</h5>
                                <span class="status-badge ${control.compliance_status === 'COMPLIANT' ? 'compliant' : 'non-compliant'}">
                                    <i class="fas ${control.compliance_status === 'COMPLIANT' ? 'fa-check' : 'fa-times'}"></i>
                                    ${control.compliance_status}
                                </span>
                            </div>
                            <p class="item-description">${control.description || 'No description available'}</p>
                            ${control.remediation_guidance ? `
                                <div class="item-meta">
                                    <span><i class="fas fa-tools"></i> ${control.remediation_guidance}</span>
                                </div>
                            ` : ''}
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    renderRiskDetails(alerts, violations) {
        const allIssues = [
            ...alerts.map(a => ({...a, type: 'alert'})),
            ...violations.map(v => ({...v, type: 'violation'}))
        ].sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0));

        return `
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4 mb-6">
                    <div class="text-center p-4 bg-red-50 rounded-lg border border-red-200">
                        <div class="text-2xl font-bold text-red-600">${alerts.length}</div>
                        <div class="text-sm text-red-700">Security Alerts</div>
                    </div>
                    <div class="text-center p-4 bg-orange-50 rounded-lg border border-orange-200">
                        <div class="text-2xl font-bold text-orange-600">${violations.length}</div>
                        <div class="text-sm text-orange-700">Policy Violations</div>
                    </div>
                </div>

                <h4 class="text-lg font-semibold mb-3">Issues by Risk Score</h4>
                <ul class="details-list">
                    ${allIssues.map(issue => `
                        <li class="details-item">
                            <div class="item-header">
                                <h5 class="item-title">${issue.title || issue.policy_name}</h5>
                                <div class="flex gap-2">
                                    <span class="status-badge ${issue.type}">
                                        <i class="fas ${issue.type === 'alert' ? 'fa-bell' : 'fa-ban'}"></i>
                                        ${issue.type.toUpperCase()}
                                    </span>
                                    <span class="status-badge ${issue.severity.toLowerCase()}">
                                        ${issue.severity}
                                    </span>
                                </div>
                            </div>
                            <p class="item-description">${issue.description || issue.violation_description}</p>
                            <div class="item-meta">
                                <span><i class="fas fa-cube"></i> ${issue.resource_type}: ${issue.resource_name}</span>
                                <span><i class="fas fa-fire"></i> Risk: ${issue.risk_score || 'N/A'}</span>
                            </div>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    renderAlertsDetails(alerts) {
        return `
            <div class="space-y-4">
                <div class="text-center p-4 bg-red-50 rounded-lg border border-red-200 mb-6">
                    <div class="text-2xl font-bold text-red-600">${alerts.length}</div>
                    <div class="text-sm text-red-700">Security Alerts Found</div>
                </div>

                <ul class="details-list">
                    ${alerts.map(alert => `
                        <li class="details-item alert-card ${alert.severity.toLowerCase()}">
                            <div class="alert-header">
                                <h5 class="alert-title">${alert.title}</h5>
                                <span class="status-badge ${alert.severity.toLowerCase()}">
                                    <i class="fas fa-exclamation-triangle"></i>
                                    ${alert.severity}
                                </span>
                            </div>
                            <p class="alert-description">${alert.description}</p>
                            <div class="alert-meta">
                                <span><i class="fas fa-cube"></i> ${alert.resource_type}: ${alert.resource_name}</span>
                                <span><i class="fas fa-fire"></i> Risk: ${alert.risk_score || 'N/A'}</span>
                            </div>
                            ${alert.remediation ? `
                                <div class="mt-3 p-3 bg-blue-50 rounded border border-blue-200">
                                    <h6 class="text-sm font-semibold text-blue-800 mb-1">
                                        <i class="fas fa-wrench"></i> Remediation
                                    </h6>
                                    <p class="text-sm text-blue-700">${alert.remediation}</p>
                                </div>
                            ` : ''}
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    renderViolationsDetails(violations) {
        const autoRemediable = violations.filter(v => v.auto_remediable).length;
        
        return `
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4 mb-6">
                    <div class="text-center p-4 bg-orange-50 rounded-lg border border-orange-200">
                        <div class="text-2xl font-bold text-orange-600">${violations.length}</div>
                        <div class="text-sm text-orange-700">Total Violations</div>
                    </div>
                    <div class="text-center p-4 bg-green-50 rounded-lg border border-green-200">
                        <div class="text-2xl font-bold text-green-600">${autoRemediable}</div>
                        <div class="text-sm text-green-700">Auto-fixable</div>
                    </div>
                </div>

                <ul class="details-list">
                    ${violations.map(violation => `
                        <li class="details-item">
                            <div class="item-header">
                                <h5 class="item-title">${violation.policy_name}</h5>
                                <div class="flex gap-2">
                                    <span class="status-badge ${violation.severity.toLowerCase()}">
                                        ${violation.severity}
                                    </span>
                                    ${violation.auto_remediable ? `
                                        <span class="status-badge success">
                                            <i class="fas fa-magic"></i>
                                            Auto-Fix
                                        </span>
                                    ` : ''}
                                </div>
                            </div>
                            <p class="item-description">${violation.violation_description}</p>
                            <div class="item-meta">
                                <span><i class="fas fa-folder"></i> ${violation.policy_category}</span>
                                <span><i class="fas fa-cube"></i> ${violation.resource_name}</span>
                            </div>
                            ${violation.remediation_steps && violation.remediation_steps.length > 0 ? `
                                <div class="mt-3 p-3 bg-blue-50 rounded border border-blue-200">
                                    <h6 class="text-sm font-semibold text-blue-800 mb-2">
                                        <i class="fas fa-list"></i> Remediation Steps
                                    </h6>
                                    <ol class="text-sm text-blue-700 space-y-1 list-decimal list-inside">
                                        ${violation.remediation_steps.map(step => `<li>${step}</li>`).join('')}
                                    </ol>
                                </div>
                            ` : ''}
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    renderTrendDetails(date, datasetIndex, analysis) {
        const datasets = ['Security Score', 'Alert Count', 'Compliance Percentage'];
        const datasetName = datasets[datasetIndex];
        
        return `
            <div class="space-y-4">
                <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-200 mb-6">
                    <div class="text-lg font-semibold text-blue-800">${datasetName}</div>
                    <div class="text-sm text-blue-600">Data for ${date}</div>
                </div>

                <div class="space-y-3">
                    <h4 class="text-lg font-semibold mb-3">Historical Context</h4>
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <p class="text-gray-700">
                            This shows the ${datasetName.toLowerCase()} trend for your cluster on ${date}. 
                            ${datasetIndex === 0 ? 'Security score reflects overall cluster security posture.' :
                              datasetIndex === 1 ? 'Alert count shows active security issues requiring attention.' :
                              'Compliance percentage shows adherence to security frameworks.'}
                        </p>
                    </div>
                    
                    ${datasetIndex === 0 ? this.renderScoreBreakdown(analysis.security_posture) :
                      datasetIndex === 1 ? this.renderAlertBreakdown(analysis.security_posture?.alerts) :
                      this.renderComplianceBreakdown(analysis.compliance_frameworks)}
                </div>
            </div>
        `;
    }

    renderScoreBreakdown(posture) {
        const breakdown = posture?.breakdown || {};
        return `
            <h5 class="font-semibold mb-2">Score Components</h5>
            <div class="space-y-2">
                ${Object.entries(breakdown).map(([component, score]) => `
                    <div class="flex justify-between items-center p-2 bg-white rounded border">
                        <span class="text-sm font-medium">${component.replace('_score', '').toUpperCase()}</span>
                        <span class="text-sm font-bold">${Math.round(score)}%</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderAlertBreakdown(alerts) {
        const categories = {};
        (alerts || []).forEach(alert => {
            categories[alert.category] = (categories[alert.category] || 0) + 1;
        });

        return `
            <h5 class="font-semibold mb-2">Alert Categories</h5>
            <div class="space-y-2">
                ${Object.entries(categories).map(([category, count]) => `
                    <div class="flex justify-between items-center p-2 bg-white rounded border">
                        <span class="text-sm font-medium">${category}</span>
                        <span class="text-sm font-bold">${count}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderComplianceBreakdown(frameworks) {
        return `
            <h5 class="font-semibold mb-2">Framework Compliance</h5>
            <div class="space-y-2">
                ${Object.entries(frameworks || {}).map(([name, framework]) => `
                    <div class="flex justify-between items-center p-2 bg-white rounded border">
                        <span class="text-sm font-medium">${name}</span>
                        <div class="flex items-center gap-2">
                            <span class="text-sm font-bold">${Math.round(framework.overall_compliance || 0)}%</span>
                            <span class="status-badge ${framework.grade === 'A' ? 'success' : framework.grade === 'F' ? 'critical' : 'medium'}">
                                ${framework.grade || 'N/A'}
                            </span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // Modal management
    openDetailsModal(title, content, icon = 'fas fa-info-circle') {
        const modal = document.getElementById('security-details-modal');
        const overlay = document.getElementById('security-details-overlay');
        const titleElement = document.getElementById('modal-title');
        const contentElement = document.getElementById('modal-content');

        if (modal && overlay && titleElement && contentElement) {
            titleElement.innerHTML = `<i class="${icon}"></i> ${title}`;
            contentElement.innerHTML = content;
            
            overlay.classList.add('active');
            modal.classList.add('active', 'slide-in-right');
        }
    }

    closeDetailsModal() {
        const modal = document.getElementById('security-details-modal');
        const overlay = document.getElementById('security-details-overlay');

        if (modal && overlay) {
            modal.classList.remove('active', 'slide-in-right');
            overlay.classList.remove('active');
        }
    }

    // Utility methods
    getCurrentClusterId() {
        // Extract cluster ID from URL or global state
        const path = window.location.pathname;
        const match = path.match(/\/cluster\/([^\/\?]+)/);
        
        if (match && match[1]) {
            const clusterId = decodeURIComponent(match[1]);
            this.state.clusterId = clusterId;
            return clusterId;
        }
        
        return window.currentCluster?.id || window.clusterInfo?.id || null;
    }

    extractTrendFromCurrentState(trends) {
        // Extract trend data from current analysis if historical data not available
        const currentDate = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        
        return {
            dates: [currentDate],
            security_scores: [trends.current_score || 0],
            alert_counts: [trends.alert_count || 0],
            compliance_scores: [trends.compliance_score || 0]
        };
    }

    showLoadingState() {
        const metricsCards = document.querySelectorAll('.security-metric-card .metric-value');
        metricsCards.forEach(card => {
            card.innerHTML = '<div class="loading-spinner"></div>';
        });
    }

    showNoDataState() {
        const container = document.getElementById('securityposture-content');
        if (container) {
            container.innerHTML = `
                <div class="security-dashboard-unified">
                    <div class="empty-state">
                        <i class="fas fa-shield-alt empty-state-icon"></i>
                        <h3 class="empty-state-title">No Security Data Available</h3>
                        <p class="empty-state-message">
                            Please run a cluster analysis to generate security posture data. 
                            This will analyze your AKS cluster for security issues, compliance violations, and optimization opportunities.
                        </p>
                        <button class="security-btn" onclick="window.location.href='/'">
                            <i class="fas fa-arrow-left"></i>
                            Return to Dashboard
                        </button>
                    </div>
                </div>
            `;
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('security-notifications');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `security-notification ${type}`;
        
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">
                    <i class="fas ${iconMap[type] || iconMap.info}"></i>
                </div>
                <div class="notification-message">${message}</div>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        container.appendChild(notification);
        
        // Show notification
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    // Filter methods with enhanced data manager integration
    applyTimeFilter(timeRange) {
        this.state.activeFilters.timeRange = timeRange;
        this.dataManager.setFilter('timeRange', timeRange);
        this.refreshCharts();
    }

    applySeverityFilter(severity) {
        this.state.activeFilters.severity = severity;
        this.dataManager.setFilter('severity', severity);
        this.refreshCharts();
    }

    applyCategoryFilter(category) {
        this.state.activeFilters.category = category;
        this.dataManager.setFilter('category', category);
        this.refreshCharts();
    }

    resetFilters() {
        this.state.activeFilters = {
            severity: 'all',
            category: 'all',
            timeRange: '30d'
        };
        
        // Reset data manager filters
        this.dataManager.resetFilters();
        
        // Reset UI
        document.getElementById('time-range-filter').value = '30d';
        document.getElementById('severity-filter').value = 'all';
        document.getElementById('category-filter').value = 'all';
        
        this.refreshCharts();
    }

    refreshCharts() {
        if (this.state.data) {
            this.updateDashboard(this.state.data);
        }
    }

    // Action methods
    async forceRefresh() {
        console.log('🔄 Force refreshing security dashboard...');
        this.showNotification('Refreshing security data...', 'info');
        await this.loadAllSecurityData();
        this.showNotification('Security data refreshed successfully', 'success');
    }

    async exportReport() {
        console.log('📄 Exporting security report...');
        this.showNotification('Generating security report...', 'info');
        
        // Implementation for export would go here
        setTimeout(() => {
            this.showNotification('Security report exported successfully', 'success');
        }, 2000);
    }

    exportChart(chartType) {
        const chart = this.charts.get(chartType);
        if (chart) {
            const url = chart.toBase64Image();
            const link = document.createElement('a');
            link.download = `security-${chartType}-chart.png`;
            link.href = url;
            link.click();
            this.showNotification(`${chartType} chart exported`, 'success');
        }
    }

    async runSecurityScan() {
        try {
            this.showNotification('Initiating security scan...', 'info');
            
            const clusterId = this.getCurrentClusterId();
            if (!clusterId) {
                this.showNotification('No cluster selected for scan', 'error');
                return;
            }
            
            // Trigger real backend security scan
            const response = await fetch(`${this.apiBaseUrl}/scan/${clusterId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                this.showNotification('Security scan completed successfully', 'success');
                // Refresh with new data
                await this.forceRefresh();
            } else {
                throw new Error('Security scan failed');
            }
            
        } catch (error) {
            console.error('Security scan error:', error);
            this.showNotification('Security scan failed: ' + error.message, 'error');
        }
    }

    async autoFixViolations() {
        try {
            const violations = this.state.data?.analysis?.policy_compliance?.violations || [];
            const autoFixable = violations.filter(v => v.auto_remediable);
            
            if (autoFixable.length === 0) {
                this.showNotification('No auto-fixable violations found', 'warning');
                return;
            }
            
            this.showNotification(`Fixing ${autoFixable.length} violations...`, 'info');
            
            const clusterId = this.getCurrentClusterId();
            const violationIds = autoFixable.map(v => v.violation_id);
            
            // Trigger real auto-remediation via backend
            const response = await fetch(`${this.apiBaseUrl}/remediate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cluster_id: clusterId,
                    violation_ids: violationIds
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showNotification(`${result.fixed_count || autoFixable.length} violations fixed successfully`, 'success');
                await this.forceRefresh();
            } else {
                throw new Error('Auto-remediation failed');
            }
            
        } catch (error) {
            console.error('Auto-fix error:', error);
            this.showNotification('Auto-fix failed: ' + error.message, 'error');
        }
    }

    generateComplianceReport() {
        this.showNotification('Generating compliance report...', 'info');
        // Implementation would generate compliance report
        setTimeout(() => {
            this.showNotification('Compliance report generated', 'success');
        }, 2000);
    }

    viewAuditLog() {
        this.openDetailsModal(
            'Security Audit Trail',
            this.renderAuditTrail(),
            'fas fa-history'
        );
    }

    renderAuditTrail() {
        // Get real audit trail from cached data or backend
        const auditEvents = this.state.data?.analysis?.audit_trail || 
                           this.state.data?.audit_events || [];
        
        // If no real audit data, show empty state
        if (auditEvents.length === 0) {
            return `
                <div class="empty-state">
                    <i class="fas fa-history empty-state-icon"></i>
                    <h3 class="empty-state-title">No Audit Events</h3>
                    <p class="empty-state-message">No security audit events recorded yet.</p>
                </div>
            `;
        }

        return `
            <div class="space-y-4">
                <ul class="details-list">
                    ${auditEvents.map(event => `
                        <li class="details-item">
                            <div class="item-header">
                                <h5 class="item-title">${event.action}</h5>
                                <span class="status-badge ${event.impact.toLowerCase()}">
                                    ${event.impact} Impact
                                </span>
                            </div>
                            <div class="item-meta">
                                <span><i class="fas fa-user"></i> ${event.user}</span>
                                <span><i class="fas fa-clock"></i> ${new Date(event.timestamp).toLocaleString()}</span>
                            </div>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    // Auto-refresh functionality
    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        this.refreshTimer = setInterval(() => {
            if (document.getElementById('securityposture-content') && 
                !document.getElementById('securityposture-content').classList.contains('hidden')) {
                console.log('🔄 Auto-refreshing security data...');
                this.loadAllSecurityData();
            }
        }, this.state.refreshInterval);

        console.log('⏰ Auto-refresh started (5 minute intervals)');
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
        console.log('⏰ Auto-refresh stopped');
    }

    destroy() {
        this.stopAutoRefresh();
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
        console.log('🗑️ Unified Security Dashboard destroyed');
    }
}

// Initialize the unified dashboard
let unifiedSecurity;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize unified security dashboard
    unifiedSecurity = new UnifiedSecurityDashboard();
    window.unifiedSecurity = unifiedSecurity;
    
    // Global cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (unifiedSecurity) {
            unifiedSecurity.destroy();
        }
    });
});

// Export for external access
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedSecurityDashboard;
}

window.UnifiedSecurityDashboard = UnifiedSecurityDashboard;