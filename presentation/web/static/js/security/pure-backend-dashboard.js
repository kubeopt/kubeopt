/**
 * Pure Backend Security Dashboard
 * ==============================
 * 100% real data from your security analysis engine - NO fake/demo/static data
 * Uses only your rich backend analysis: security_posture, compliance_frameworks, policy_compliance
 */

class PureBackendSecurityDashboard {
    constructor(apiBaseUrl = '/api/security') {
        this.apiBaseUrl = apiBaseUrl;
        this.charts = new Map();
        this.refreshTimer = null;
        this.currentData = null;
        
        this.init();
    }

    async init() {
        console.log('🔒 Initializing Pure Backend Security Dashboard...');
        
        if (document.getElementById('securityposture-content')) {
            await this.createDashboardLayout();
            await this.loadRealSecurityData();
            this.startAutoRefresh();
        }
        
        console.log('✅ Pure Backend Security Dashboard initialized');
    }

    async createDashboardLayout() {
        const container = document.getElementById('securityposture-content');
        if (!container) return;

        container.innerHTML = `
            <div class="security-dashboard-unified">
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div>
                        <h2 style="font-size: 18px; margin: 0; display: flex; align-items: center; gap: 8px;">
                            <i class="fas fa-shield-alt"></i>
                            Security Posture Analysis
                        </h2>
                        <p style="font-size: 12px; margin: 4px 0 0 0; color: #666;">
                            Last analysis: <span id="last-update-time">Loading...</span>
                        </p>
                    </div>
                    <div>
                        <button onclick="window.pureSecurityDashboard?.exportAnalysis()" class="security-btn accent">
                            <i class="fas fa-download"></i>Export
                        </button>
                    </div>
                </div>

                <!-- Real Data Metrics -->
                <div class="security-metrics-row fade-in" id="metrics-container">
                    <!-- Metrics populated from real backend data -->
                </div>

                <!-- Real Data Charts -->
                <div class="security-charts-grid fade-in">
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3 class="chart-title">
                                <div class="chart-icon"><i class="fas fa-certificate"></i></div>
                                Compliance Frameworks
                            </h3>
                        </div>
                        <div class="chart-container chart-clickable small">
                            <canvas id="compliance-chart"></canvas>
                        </div>
                    </div>

                    <div class="chart-card">
                        <div class="chart-header">
                            <h3 class="chart-title">
                                <div class="chart-icon"><i class="fas fa-exclamation-triangle"></i></div>
                                Security Alerts
                            </h3>
                        </div>
                        <div class="chart-container chart-clickable small">
                            <canvas id="alerts-chart"></canvas>
                        </div>
                    </div>

                    <div class="chart-card">
                        <div class="chart-header">
                            <h3 class="chart-title">
                                <div class="chart-icon"><i class="fas fa-chart-area"></i></div>
                                Security Score Breakdown
                            </h3>
                        </div>
                        <div class="chart-container">
                            <canvas id="breakdown-chart"></canvas>
                        </div>
                    </div>

                    <div class="chart-card">
                        <div class="chart-header">
                            <h3 class="chart-title">
                                <div class="chart-icon"><i class="fas fa-ban"></i></div>
                                Policy Violations
                            </h3>
                        </div>
                        <div class="chart-container chart-clickable small">
                            <canvas id="violations-chart"></canvas>
                        </div>
                    </div>

                    <div class="chart-card">
                        <div class="chart-header">
                            <h3 class="chart-title">
                                <div class="chart-icon"><i class="fas fa-bug"></i></div>
                                Vulnerabilities
                            </h3>
                        </div>
                        <div class="chart-container chart-clickable small">
                            <canvas id="vulnerabilities-chart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Real Data Details -->
                <div id="security-details" class="fade-in" style="display: none;">
                    <!-- Dynamic details populated from backend -->
                </div>
            </div>

            <!-- Details Modal -->
            <div id="details-overlay" class="security-details-overlay" onclick="window.pureSecurityDashboard?.closeDetails()"></div>
            <div id="details-modal" class="security-details-modal">
                <div class="modal-header">
                    <h2 class="modal-title" id="modal-title">Details</h2>
                    <button class="modal-close" onclick="window.pureSecurityDashboard?.closeDetails()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-content" id="modal-content"></div>
            </div>
        `;
    }

    async loadRealSecurityData() {
        try {
            const clusterId = this.getCurrentClusterId();
            if (!clusterId) {
                this.showError('No cluster ID found');
                return;
            }

            console.log('🔄 Loading real security analysis data (same as Issues tab)...');
            
            // Use the same data loading approach as your existing Issues tab
            const data = await this.loadSecurityDataFromBackend(clusterId);
            
            if (!data) {
                this.showNoData();
                return;
            }

            this.currentData = data;
            
            // Also load alerts separately using the same method as Issues tab
            const alerts = await this.loadAlertsFromBackend(clusterId);
            const violations = await this.loadViolationsFromBackend(clusterId);
            
            // Merge alerts and violations into data structure
            if (data.analysis) {
                if (!data.analysis.security_posture) data.analysis.security_posture = {};
                if (!data.analysis.policy_compliance) data.analysis.policy_compliance = {};
                
                data.analysis.security_posture.alerts = alerts;
                data.analysis.policy_compliance.violations = violations;
            }
            
            console.log('📊 Loaded real backend data:', {
                alerts: alerts.length,
                violations: violations.length,
                frameworks: Object.keys(data.analysis?.compliance_frameworks || {}).length,
                sampleViolation: violations[0],
                dataStructure: data.analysis
            });
            
            await this.updateDashboardWithRealData(data);
            
            document.getElementById('last-update-time').textContent = 
                new Date().toLocaleString();

        } catch (error) {
            console.error('❌ Failed to load real security data:', error);
            this.showError('Failed to load security analysis: ' + error.message);
        }
    }

    async loadSecurityDataFromBackend(clusterId) {
        // Try the same endpoints as your existing system
        const endpoints = [
            `${this.apiBaseUrl}/results/${clusterId}`,
            `${this.apiBaseUrl}/overview?cluster_id=${clusterId}`,
            `/api/analysis/security/${clusterId}`
        ];

        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint);
                if (response.ok) {
                    const data = await response.json();
                    if (data && (data.analysis || data.security_posture)) {
                        console.log(`✅ Security data loaded from: ${endpoint}`);
                        return data;
                    }
                }
            } catch (error) {
                console.log(`Endpoint failed: ${endpoint}`);
            }
        }
        return null;
    }

    async loadAlertsFromBackend(clusterId) {
        try {
            // Use the same dedicated alerts API endpoint as Issues tab
            const response = await fetch(`${this.apiBaseUrl}/alerts?cluster_id=${clusterId}`, {
                headers: {
                    'X-Cluster-ID': clusterId
                }
            });
            
            if (response.ok) {
                const alerts = await response.json();
                console.log(`🚨 Loaded ${alerts.length} security alerts from dedicated alerts API`);
                return alerts;
            }
            
            // Fallback: try to get from main results endpoint
            const fallbackResponse = await fetch(`${this.apiBaseUrl}/results/${clusterId}`);
            if (fallbackResponse.ok) {
                const data = await fallbackResponse.json();
                const alerts = data.analysis?.security_posture?.alerts || [];
                console.log(`🚨 Fallback: Loaded ${alerts.length} alerts from results endpoint`);
                return alerts;
            }
            
            return [];
        } catch (error) {
            console.error('Failed to load alerts:', error);
            return [];
        }
    }

    async loadViolationsFromBackend(clusterId) {
        try {
            // Use the same dedicated policy violations API endpoint as Issues tab
            const response = await fetch(`${this.apiBaseUrl}/policy-violations?cluster_id=${clusterId}`, {
                headers: {
                    'X-Cluster-ID': clusterId
                }
            });
            
            if (response.ok) {
                const violations = await response.json();
                console.log(`⚠️ Loaded ${violations.length} policy violations from dedicated API`);
                return violations;
            }
            
            // Fallback: try to get from main results endpoint
            const fallbackResponse = await fetch(`${this.apiBaseUrl}/results/${clusterId}`);
            if (fallbackResponse.ok) {
                const data = await fallbackResponse.json();
                const violations = data.analysis?.policy_compliance?.violations || [];
                console.log(`⚠️ Fallback: Loaded ${violations.length} violations from results endpoint`);
                return violations;
            }
            
            return [];
        } catch (error) {
            console.error('Failed to load violations:', error);
            return [];
        }
    }

    async updateDashboardWithRealData(data) {
        const analysis = data.analysis || data;
        
        // Extract real backend data structures
        const securityPosture = analysis.security_posture || {};
        const complianceFrameworks = analysis.compliance_frameworks || {};
        const policyCompliance = analysis.policy_compliance || {};
        const vulnerabilityAssessment = analysis.vulnerability_assessment || {};
        
        console.log('📊 Updating dashboard with real data:', {
            securityScore: securityPosture.overall_score,
            frameworks: Object.keys(complianceFrameworks),
            alertCount: securityPosture.alerts?.length || 0,
            violationsCount: policyCompliance.violations?.length || 0,
            hasBreakdown: !!securityPosture.breakdown,
            breakdownKeys: securityPosture.breakdown ? Object.keys(securityPosture.breakdown) : [],
            vulnerabilities: vulnerabilityAssessment.total_vulnerabilities || 0
        });

        // Log detailed alert information
        if (securityPosture.alerts && securityPosture.alerts.length > 0) {
            console.log('🚨 Alert details:', securityPosture.alerts.map(alert => ({
                id: alert.alert_id,
                severity: alert.severity,
                title: alert.title,
                category: alert.category
            })));
        }

        // Update metrics with real data
        this.updateRealMetrics(securityPosture, complianceFrameworks, policyCompliance, vulnerabilityAssessment);

        // Create charts with real data only
        await Promise.all([
            this.createRealComplianceChart(complianceFrameworks),
            this.createRealAlertsChart(securityPosture.alerts || [], policyCompliance.violations || []),
            this.createRealBreakdownChart(securityPosture.breakdown || {}),
            this.createRealViolationsChart(policyCompliance.violations || []),
            this.createRealVulnerabilitiesChart(vulnerabilityAssessment)
        ]);
    }

    updateRealMetrics(posture, frameworks, compliance, vulnerabilities) {
        const container = document.getElementById('metrics-container');
        if (!container) return;

        // Calculate real metrics from your backend data
        const overallScore = posture.overall_score || 0;
        const grade = posture.grade || 'N/A';
        const alertsCount = (posture.alerts || []).length;
        const violationsCount = (compliance.violations || []).length;
        const criticalVulns = vulnerabilities.critical_vulnerabilities || 0;
        
        // Average compliance across frameworks
        const frameworkScores = Object.values(frameworks).map(f => f.overall_compliance || 0);
        const avgCompliance = frameworkScores.length > 0 
            ? Math.round(frameworkScores.reduce((a, b) => a + b, 0) / frameworkScores.length)
            : 0;

        container.innerHTML = `
            <div class="security-metric-card" onclick="window.pureSecurityDashboard?.showScoreDetails()">
                <div class="metric-header">
                    <div class="metric-icon"><i class="fas fa-shield-alt"></i></div>
                    <div class="metric-value">${overallScore}%</div>
                </div>
                <div class="metric-label">Security Score</div>
                <div class="metric-trend">Grade: ${grade}</div>
            </div>

            <div class="security-metric-card" onclick="window.pureSecurityDashboard?.showAlertsDetails()">
                <div class="metric-header">
                    <div class="metric-icon"><i class="fas fa-exclamation-triangle"></i></div>
                    <div class="metric-value">${alertsCount}</div>
                </div>
                <div class="metric-label">Security Alerts</div>
                <div class="metric-trend">Active issues found</div>
            </div>

            <div class="security-metric-card" onclick="window.pureSecurityDashboard?.showComplianceDetails()">
                <div class="metric-header">
                    <div class="metric-icon"><i class="fas fa-clipboard-check"></i></div>
                    <div class="metric-value">${avgCompliance}%</div>
                </div>
                <div class="metric-label">Compliance</div>
                <div class="metric-trend">${Object.keys(frameworks).length} frameworks</div>
            </div>

            <div class="security-metric-card" onclick="window.pureSecurityDashboard?.showViolationsDetails()">
                <div class="metric-header">
                    <div class="metric-icon"><i class="fas fa-ban"></i></div>
                    <div class="metric-value">${violationsCount}</div>
                </div>
                <div class="metric-label">Policy Violations</div>
                <div class="metric-trend">${criticalVulns} critical vulnerabilities</div>
            </div>
        `;
    }

    async createRealComplianceChart(frameworks) {
        const canvas = document.getElementById('compliance-chart');
        if (!canvas || Object.keys(frameworks).length === 0) {
            this.showEmptyChart(canvas, 'No compliance data available');
            return;
        }

        if (this.charts.has('compliance')) {
            this.charts.get('compliance').destroy();
        }

        const ctx = canvas.getContext('2d');
        const frameworkNames = Object.keys(frameworks);
        const complianceScores = Object.values(frameworks).map(f => f.overall_compliance || 0);

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: frameworkNames,
                datasets: [{
                    data: complianceScores,
                    backgroundColor: ['#7FB069', '#4A90A4', '#F59E0B', '#EF4444'],
                    borderColor: '#ffffff',
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 5,
                        bottom: 5,
                        left: 5,
                        right: 5
                    }
                },
                plugins: {
                    legend: { 
                        position: 'bottom',
                        labels: {
                            font: { size: 10 },
                            padding: 8
                        }
                    },
                    tooltip: {
                        callbacks: {
                            afterBody: () => ['', '💡 Click to view controls']
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const frameworkName = frameworkNames[index];
                        this.showFrameworkDetails(frameworkName, frameworks[frameworkName]);
                    }
                }
            }
        });

        this.charts.set('compliance', chart);
    }

    async createRealAlertsChart(alerts, violations = []) {
        const canvas = document.getElementById('alerts-chart');
        if (!canvas) return;

        // Combine alerts and violations for comprehensive security issues display
        const allSecurityIssues = [
            ...alerts.map(a => ({...a, type: 'alert'})),
            ...violations.map(v => ({...v, type: 'violation'}))
        ];

        console.log(`🔍 Creating security issues chart with ${alerts.length} alerts + ${violations.length} violations = ${allSecurityIssues.length} total issues`);

        if (allSecurityIssues.length === 0) {
            this.showEmptyChart(canvas, '✅ No security issues found');
            return;
        }

        if (this.charts.has('alerts')) {
            this.charts.get('alerts').destroy();
        }

        const ctx = canvas.getContext('2d');
        
        // Count all security issues by severity
        const severityCounts = {
            'CRITICAL': allSecurityIssues.filter(item => item.severity === 'CRITICAL').length,
            'HIGH': allSecurityIssues.filter(item => item.severity === 'HIGH').length,
            'MEDIUM': allSecurityIssues.filter(item => item.severity === 'MEDIUM').length,
            'LOW': allSecurityIssues.filter(item => item.severity === 'LOW').length
        };

        console.log('📊 Security issues breakdown:', {
            alerts: alerts.length,
            violations: violations.length,
            severityCounts
        });

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(severityCounts),
                datasets: [{
                    label: 'Security Issues',
                    data: Object.values(severityCounts),
                    backgroundColor: ['#EF4444', '#F97316', '#EAB308', '#22C55E'],
                    borderColor: ['#DC2626', '#EA580C', '#D97706', '#16A34A'],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 5,
                        bottom: 5,
                        left: 5,
                        right: 5
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            font: { size: 10 }
                        }
                    },
                    y: { 
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            font: { size: 10 }
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const severity = context.label;
                                const count = context.parsed.y;
                                const alertsOfSeverity = alerts.filter(a => a.severity === severity).length;
                                const violationsOfSeverity = violations.filter(v => v.severity === severity).length;
                                return [
                                    `${count} ${severity} issues:`,
                                    `  • ${alertsOfSeverity} alerts`,
                                    `  • ${violationsOfSeverity} violations`
                                ];
                            },
                            afterBody: () => ['', '💡 Click to view details']
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
                        console.log(`🔍 Clicked ${severity} security issues`);
                        this.showSecurityIssuesDetailsBySeverity(severity, alerts, violations);
                    }
                }
            }
        });

        this.charts.set('alerts', chart);
    }

    async createRealBreakdownChart(breakdown) {
        const canvas = document.getElementById('breakdown-chart');
        if (!canvas) return;

        if (Object.keys(breakdown).length === 0) {
            this.showEmptyChart(canvas, 'No breakdown data available');
            return;
        }

        if (this.charts.has('breakdown')) {
            this.charts.get('breakdown').destroy();
        }

        const ctx = canvas.getContext('2d');
        
        // Create more readable labels for your security components
        const labelMap = {
            'rbac_score': 'RBAC',
            'network_score': 'Network',
            'encryption_score': 'Encryption', 
            'vulnerability_score': 'Vulnerabilities',
            'compliance_score': 'Compliance',
            'drift_score': 'Configuration Drift'
        };
        
        const components = Object.keys(breakdown);
        const scores = Object.values(breakdown);
        const labels = components.map(c => labelMap[c] || c.replace('_score', '').toUpperCase());
        
        console.log('📊 Security breakdown chart data:', {
            components,
            scores,
            labels,
            rawBreakdown: breakdown
        });

        // Color code points based on score ranges
        const pointColors = scores.map(score => {
            if (score >= 80) return '#22C55E'; // Green - Good
            if (score >= 60) return '#EAB308'; // Yellow - Warning  
            if (score >= 40) return '#F97316'; // Orange - Poor
            return '#EF4444'; // Red - Critical
        });

        const chart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Security Scores',
                    data: scores,
                    backgroundColor: 'rgba(127, 176, 105, 0.2)',
                    borderColor: '#7FB069',
                    borderWidth: 2,
                    pointBackgroundColor: pointColors,
                    pointBorderColor: pointColors,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 5,
                        bottom: 5,
                        left: 5,
                        right: 5
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            font: { size: 9 },
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: {
                            lineWidth: 1
                        },
                        angleLines: {
                            lineWidth: 1
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const component = components[context.dataIndex];
                                const score = context.parsed.r;
                                return [
                                    `${labels[context.dataIndex]}: ${score.toFixed(1)}%`,
                                    `Component: ${component}`
                                ];
                            }
                        }
                    }
                }
            }
        });

        this.charts.set('breakdown', chart);
    }

    async createRealViolationsChart(violations) {
        const canvas = document.getElementById('violations-chart');
        if (!canvas) return;

        console.log('🔍 Creating violations chart with data:', {
            violationsCount: violations.length,
            violationsData: violations.slice(0, 3)
        });

        if (violations.length === 0) {
            this.showEmptyChart(canvas, 'No policy violations');
            return;
        }

        if (this.charts.has('violations')) {
            this.charts.get('violations').destroy();
        }

        const ctx = canvas.getContext('2d');
        const categoryCounts = {};
        violations.forEach(v => {
            const category = v.policy_category || 'Other';
            categoryCounts[category] = (categoryCounts[category] || 0) + 1;
        });

        console.log('📊 Violations by category:', categoryCounts);

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(categoryCounts),
                datasets: [{
                    label: 'Violations',
                    data: Object.values(categoryCounts),
                    backgroundColor: '#F97316',
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                layout: {
                    padding: {
                        top: 5,
                        bottom: 5,
                        left: 5,
                        right: 5
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            font: { size: 10 }
                        }
                    },
                    y: {
                        ticks: {
                            font: { size: 10 }
                        }
                    }
                },
                plugins: { 
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            afterBody: () => ['', '💡 Click to view violations']
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
                        console.log(`🔍 Clicked ${category} violations, showing ${violations.length} total violations`);
                        this.showViolationsByCategory(category, violations);
                    }
                }
            }
        });

        this.charts.set('violations', chart);
    }

    async createRealVulnerabilitiesChart(vulnerabilities) {
        const canvas = document.getElementById('vulnerabilities-chart');
        if (!canvas) return;

        const total = vulnerabilities.total_vulnerabilities || 0;
        if (total === 0) {
            this.showEmptyChart(canvas, 'No vulnerabilities found');
            return;
        }

        if (this.charts.has('vulnerabilities')) {
            this.charts.get('vulnerabilities').destroy();
        }

        const ctx = canvas.getContext('2d');
        const vulnCounts = {
            'Critical': vulnerabilities.critical_vulnerabilities || 0,
            'High': vulnerabilities.high_vulnerabilities || 0,
            'Medium': vulnerabilities.medium_vulnerabilities || 0,
            'Low': vulnerabilities.low_vulnerabilities || 0
        };

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(vulnCounts),
                datasets: [{
                    data: Object.values(vulnCounts),
                    backgroundColor: ['#EF4444', '#F97316', '#EAB308', '#22C55E']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 5,
                        bottom: 5,
                        left: 5,
                        right: 5
                    }
                },
                plugins: { 
                    legend: { 
                        position: 'bottom',
                        labels: {
                            font: { size: 10 },
                            padding: 8
                        }
                    }
                }
            }
        });

        this.charts.set('vulnerabilities', chart);
    }

    // Detail view methods using real data
    showFrameworkDetails(name, framework) {
        const title = `${name} Compliance Details`;
        const controls = framework.control_details || [];
        
        let content = `
            <div class="details-section">
                <div class="metric-summary">
                    <div class="summary-item">
                        <span class="label">Overall Compliance:</span>
                        <span class="value">${framework.overall_compliance || 0}%</span>
                    </div>
                    <div class="summary-item">
                        <span class="label">Grade:</span>
                        <span class="value">${framework.grade || 'N/A'}</span>
                    </div>
                    <div class="summary-item">
                        <span class="label">Passed Controls:</span>
                        <span class="value">${framework.passed_controls || 0}</span>
                    </div>
                    <div class="summary-item">
                        <span class="label">Failed Controls:</span>
                        <span class="value">${framework.failed_controls || 0}</span>
                    </div>
                </div>
        `;

        if (controls.length > 0) {
            content += `
                <h4>Control Details</h4>
                <div class="controls-list">
                    ${controls.map(control => `
                        <div class="control-item">
                            <div class="control-header">
                                <span class="control-id">${control.control_id}</span>
                                <span class="status-badge ${control.compliance_status === 'COMPLIANT' ? 'success' : 'critical'}">
                                    ${control.compliance_status}
                                </span>
                            </div>
                            <div class="control-title">${control.title}</div>
                            <div class="control-description">${control.description || 'No description'}</div>
                            ${control.remediation_guidance ? `
                                <div class="remediation">
                                    <strong>Remediation:</strong> ${control.remediation_guidance}
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            `;
        }

        content += '</div>';
        this.openModal(title, content);
    }

    showAlertsDetailsBySeverity(severity, alerts) {
        const filteredAlerts = alerts.filter(a => a.severity === severity);
        const title = `${severity} Security Alerts (${filteredAlerts.length})`;
        
        const content = `
            <div class="alerts-list">
                ${filteredAlerts.map(alert => `
                    <div class="alert-item ${severity.toLowerCase()}">
                        <div class="alert-header">
                            <span class="alert-title">${alert.title}</span>
                            <span class="status-badge ${severity.toLowerCase()}">${severity}</span>
                        </div>
                        <div class="alert-description">${alert.description}</div>
                        <div class="alert-meta">
                            <span><strong>Resource:</strong> ${alert.resource_name}</span>
                            <span><strong>Namespace:</strong> ${alert.namespace || 'default'}</span>
                            <span><strong>Risk Score:</strong> ${alert.risk_score || 'N/A'}</span>
                        </div>
                        ${alert.remediation ? `
                            <div class="remediation">
                                <strong>Remediation:</strong> ${alert.remediation}
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
        
        this.openModal(title, content);
    }

    showSecurityIssuesDetailsBySeverity(severity, alerts, violations) {
        const filteredAlerts = alerts.filter(a => a.severity === severity);
        const filteredViolations = violations.filter(v => v.severity === severity);
        const totalCount = filteredAlerts.length + filteredViolations.length;
        const title = `${severity} Security Issues (${totalCount})`;
        
        let content = `<div class="security-issues-list">`;
        
        if (filteredAlerts.length > 0) {
            content += `
                <div class="issues-section">
                    <h4 class="section-title">🚨 Security Alerts (${filteredAlerts.length})</h4>
                    <div class="alerts-list">
                        ${filteredAlerts.map(alert => `
                            <div class="alert-item ${severity.toLowerCase()}">
                                <div class="alert-header">
                                    <span class="alert-title">${alert.title}</span>
                                    <span class="status-badge ${severity.toLowerCase()}">${severity}</span>
                                </div>
                                <div class="alert-description">${alert.description}</div>
                                <div class="alert-meta">
                                    <span><strong>Resource:</strong> ${alert.resource_name}</span>
                                    <span><strong>Namespace:</strong> ${alert.namespace || 'default'}</span>
                                    <span><strong>Risk Score:</strong> ${alert.risk_score || 'N/A'}</span>
                                </div>
                                ${alert.remediation ? `
                                    <div class="remediation">
                                        <strong>Remediation:</strong> ${alert.remediation}
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        if (filteredViolations.length > 0) {
            content += `
                <div class="issues-section">
                    <h4 class="section-title">⚠️ Policy Violations (${filteredViolations.length})</h4>
                    <div class="violations-list">
                        ${filteredViolations.map(violation => `
                            <div class="violation-item ${severity.toLowerCase()}">
                                <div class="violation-header">
                                    <span class="violation-title">${violation.policy_name}</span>
                                    <div class="violation-badges">
                                        <span class="status-badge ${violation.severity.toLowerCase()}">${violation.severity}</span>
                                        ${violation.auto_remediable ? '<span class="status-badge success">Auto-fix</span>' : ''}
                                    </div>
                                </div>
                                <div class="violation-description">${violation.violation_description}</div>
                                <div class="violation-meta">
                                    <span><strong>Resource:</strong> ${violation.resource_name}</span>
                                    <span><strong>Namespace:</strong> ${violation.namespace || 'default'}</span>
                                    <span><strong>Policy Category:</strong> ${violation.policy_category}</span>
                                </div>
                                ${violation.remediation_steps && violation.remediation_steps.length > 0 ? `
                                    <div class="remediation-steps">
                                        <strong>Remediation Steps:</strong>
                                        <ol>
                                            ${violation.remediation_steps.map(step => `<li>${step}</li>`).join('')}
                                        </ol>
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        content += '</div>';
        this.openModal(title, content);
    }

    showViolationsByCategory(category, violations) {
        const filteredViolations = violations.filter(v => v.policy_category === category);
        const title = `${category} Policy Violations (${filteredViolations.length})`;
        
        const content = `
            <div class="violations-list">
                ${filteredViolations.map(violation => `
                    <div class="violation-item">
                        <div class="violation-header">
                            <span class="violation-title">${violation.policy_name}</span>
                            <div class="violation-badges">
                                <span class="status-badge ${violation.severity.toLowerCase()}">${violation.severity}</span>
                                ${violation.auto_remediable ? '<span class="status-badge success">Auto-fix</span>' : ''}
                            </div>
                        </div>
                        <div class="violation-description">${violation.violation_description}</div>
                        <div class="violation-meta">
                            <span><strong>Resource:</strong> ${violation.resource_name}</span>
                            <span><strong>Namespace:</strong> ${violation.namespace || 'default'}</span>
                        </div>
                        ${violation.remediation_steps && violation.remediation_steps.length > 0 ? `
                            <div class="remediation-steps">
                                <strong>Remediation Steps:</strong>
                                <ol>
                                    ${violation.remediation_steps.map(step => `<li>${step}</li>`).join('')}
                                </ol>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
        
        this.openModal(title, content);
    }

    // Utility methods
    showEmptyChart(canvas, message) {
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#718096';
        ctx.textAlign = 'center';
        ctx.font = '16px Poppins';
        ctx.fillText(message, canvas.width / 2, canvas.height / 2);
    }

    openModal(title, content) {
        document.getElementById('modal-title').innerHTML = `<i class="fas fa-info-circle"></i> ${title}`;
        document.getElementById('modal-content').innerHTML = content;
        document.getElementById('details-overlay').classList.add('active');
        document.getElementById('details-modal').classList.add('active');
    }

    closeDetails() {
        document.getElementById('details-overlay').classList.remove('active');
        document.getElementById('details-modal').classList.remove('active');
    }

    getCurrentClusterId() {
        const path = window.location.pathname;
        const match = path.match(/\/cluster\/([^\/\?]+)/);
        return match ? decodeURIComponent(match[1]) : (window.currentCluster?.id || null);
    }

    showNoData() {
        const container = document.getElementById('securityposture-content');
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-shield-alt empty-state-icon"></i>
                <h3 class="empty-state-title">No Security Analysis Available</h3>
                <p class="empty-state-message">Run a cluster analysis to generate security data.</p>
            </div>
        `;
    }

    showError(message) {
        console.error('Security Dashboard Error:', message);
        const container = document.getElementById('securityposture-content');
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle empty-state-icon"></i>
                <h3 class="empty-state-title">Error Loading Security Data</h3>
                <p class="empty-state-message">${message}</p>
            </div>
        `;
    }

    async refreshData() {
        await this.loadRealSecurityData();
    }

    async exportAnalysis() {
        if (!this.currentData) return;
        
        const blob = new Blob([JSON.stringify(this.currentData, null, 2)], 
            { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `security-analysis-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            if (document.getElementById('securityposture-content')) {
                this.loadRealSecurityData();
            }
        }, 300000); // 5 minutes
    }

    destroy() {
        if (this.refreshTimer) clearInterval(this.refreshTimer);
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.pureSecurityDashboard = new PureBackendSecurityDashboard();
    
    window.addEventListener('beforeunload', () => {
        if (window.pureSecurityDashboard) {
            window.pureSecurityDashboard.destroy();
        }
    });
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = PureBackendSecurityDashboard;
}