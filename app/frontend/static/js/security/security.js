/**
 * Security Posture Frontend Integration
 * ===================================
 * JavaScript integration for AKS Security Posture dashboard.
 * Connects with the FastAPI backend and provides dynamic UI updates.
 */

class SecurityPostureDashboard {
    constructor(apiBaseUrl = '/api/security') {
        this.apiBaseUrl = apiBaseUrl;
        this.refreshInterval = 30000; // 30 seconds
        this.activeIntervals = new Map();
        this.charts = new Map();
        this.lastUpdate = null;
        
        this.init();
    }

    async init() {
        console.log('🔐 Initializing Security Posture Dashboard...');
        
        // Check if we're on the security posture page
        if (document.getElementById('securityposture-content')) {
            await this.initializeSecurityDashboard();
            this.startAutoRefresh();
        }
        
        console.log('✅ Security Posture Dashboard initialized');
    }

    async initializeSecurityDashboard() {
        // Create dashboard layout if it doesn't exist
        this.createDashboardLayout();
        
        // Load initial data
        await this.loadSecurityOverview();
        await this.loadPolicyViolations();
        await this.loadCompliance();
        await this.loadVulnerabilities();
        await this.loadSecurityTrends();
        await this.loadAuditTrail();
    }

    createDashboardLayout() {
        const container = document.getElementById('securityposture-content');
        if (!container) return;

        container.innerHTML = `
            <!-- Security Overview Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="bg-slate-800 rounded-lg p-6 border border-slate-700">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-slate-400">Security Score</p>
                            <p class="text-2xl font-bold text-white" id="security-score">--</p>
                            <p class="text-xs text-slate-400" id="security-grade">Loading...</p>
                        </div>
                        <div class="h-12 w-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
                            <i class="fas fa-shield-alt text-blue-400 text-xl"></i>
                        </div>
                    </div>
                    <div class="mt-4">
                        <div class="flex items-center text-sm" id="security-trend">
                            <span class="text-slate-400">Trend: </span>
                            <span class="ml-1 text-slate-300">--</span>
                        </div>
                    </div>
                </div>

                <div class="bg-slate-800 rounded-lg p-6 border border-slate-700">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-slate-400">Critical Alerts</p>
                            <p class="text-2xl font-bold text-white" id="critical-alerts">--</p>
                            <p class="text-xs text-slate-400">Active alerts requiring attention</p>
                        </div>
                        <div class="h-12 w-12 bg-red-500/20 rounded-lg flex items-center justify-center">
                            <i class="fas fa-exclamation-triangle text-red-400 text-xl"></i>
                        </div>
                    </div>
                </div>

                <div class="bg-slate-800 rounded-lg p-6 border border-slate-700">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-slate-400">Vulnerabilities</p>
                            <p class="text-2xl font-bold text-white" id="critical-vulns">--</p>
                            <p class="text-xs text-slate-400">Critical vulnerabilities found</p>
                        </div>
                        <div class="h-12 w-12 bg-orange-500/20 rounded-lg flex items-center justify-center">
                            <i class="fas fa-bug text-orange-400 text-xl"></i>
                        </div>
                    </div>
                </div>

                <div class="bg-slate-800 rounded-lg p-6 border border-slate-700">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-slate-400">Compliance</p>
                            <p class="text-2xl font-bold text-white" id="compliance-score">--</p>
                            <p class="text-xs text-slate-400">Overall compliance percentage</p>
                        </div>
                        <div class="h-12 w-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                            <i class="fas fa-check-circle text-green-400 text-xl"></i>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main Dashboard Tabs -->
            <div class="bg-slate-800 rounded-lg border border-slate-700">
                <!-- Tab Navigation -->
                <div class="border-b border-slate-700">
                    <nav class="flex space-x-8 px-6" aria-label="Tabs">
                        <button class="security-tab-btn border-blue-500 text-blue-400 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm active" 
                                data-tab="overview">
                            <i class="fas fa-tachometer-alt mr-2"></i>Overview
                        </button>
                        <button class="security-tab-btn border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm" 
                                data-tab="policy">
                            <i class="fas fa-clipboard-list mr-2"></i>Policy Violations
                        </button>
                        <button class="security-tab-btn border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm" 
                                data-tab="compliance">
                            <i class="fas fa-medal mr-2"></i>Compliance
                        </button>
                        <button class="security-tab-btn border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm" 
                                data-tab="vulnerabilities">
                            <i class="fas fa-bug mr-2"></i>Vulnerabilities
                        </button>
                        <button class="security-tab-btn border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm" 
                                data-tab="audit">
                            <i class="fas fa-history mr-2"></i>Audit Trail
                        </button>
                    </nav>
                </div>

                <!-- Tab Content -->
                <div class="p-6">
                    <!-- Overview Tab -->
                    <div id="overview-tab" class="security-tab-content">
                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            <div>
                                <h3 class="text-lg font-semibold text-white mb-4">Security Score Breakdown</h3>
                                <div class="space-y-4" id="security-breakdown">
                                    <!-- Dynamic content -->
                                </div>
                            </div>
                            <div>
                                <h3 class="text-lg font-semibold text-white mb-4">Security Trends (30 days)</h3>
                                <div class="h-64 bg-slate-900 rounded-lg p-4">
                                    <canvas id="security-trends-chart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Policy Violations Tab -->
                    <div id="policy-tab" class="security-tab-content hidden">
                        <div class="flex justify-between items-center mb-6">
                            <h3 class="text-lg font-semibold text-white">Policy Violations</h3>
                            <div class="flex space-x-4">
                                <select id="severity-filter" class="bg-slate-700 border border-slate-600 text-white rounded-md px-3 py-2 text-sm">
                                    <option value="">All Severities</option>
                                    <option value="CRITICAL">Critical</option>
                                    <option value="HIGH">High</option>
                                    <option value="MEDIUM">Medium</option>
                                    <option value="LOW">Low</option>
                                </select>
                                <button id="refresh-violations" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm">
                                    <i class="fas fa-sync-alt mr-2"></i>Refresh
                                </button>
                            </div>
                        </div>
                        <div id="policy-violations-list" class="space-y-4">
                            <!-- Dynamic content -->
                        </div>
                    </div>

                    <!-- Compliance Tab -->
                    <div id="compliance-tab" class="security-tab-content hidden">
                        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            <div class="lg:col-span-2">
                                <h3 class="text-lg font-semibold text-white mb-4">Compliance Frameworks</h3>
                                <div id="compliance-frameworks" class="space-y-4">
                                    <!-- Dynamic content -->
                                </div>
                            </div>
                            <div>
                                <h3 class="text-lg font-semibold text-white mb-4">Compliance Heatmap</h3>
                                <div class="bg-slate-900 rounded-lg p-4 h-96">
                                    <canvas id="compliance-heatmap"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Vulnerabilities Tab -->
                    <div id="vulnerabilities-tab" class="security-tab-content hidden">
                        <div class="flex justify-between items-center mb-6">
                            <h3 class="text-lg font-semibold text-white">Vulnerabilities</h3>
                            <div class="flex space-x-4">
                                <select id="vuln-severity-filter" class="bg-slate-700 border border-slate-600 text-white rounded-md px-3 py-2 text-sm">
                                    <option value="">All Severities</option>
                                    <option value="CRITICAL">Critical</option>
                                    <option value="HIGH">High</option>
                                    <option value="MEDIUM">Medium</option>
                                    <option value="LOW">Low</option>
                                </select>
                                <button id="trigger-scan" class="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-md text-sm">
                                    <i class="fas fa-search mr-2"></i>New Scan
                                </button>
                            </div>
                        </div>
                        <div class="mb-4 p-4 bg-slate-900 rounded-lg">
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center" id="vuln-summary">
                                <!-- Dynamic content -->
                            </div>
                        </div>
                        <div id="vulnerabilities-list" class="space-y-4">
                            <!-- Dynamic content -->
                        </div>
                    </div>

                    <!-- Audit Trail Tab -->
                    <div id="audit-tab" class="security-tab-content hidden">
                        <div class="flex justify-between items-center mb-6">
                            <h3 class="text-lg font-semibold text-white">Audit Trail</h3>
                            <div class="flex space-x-4">
                                <select id="event-type-filter" class="bg-slate-700 border border-slate-600 text-white rounded-md px-3 py-2 text-sm">
                                    <option value="">All Events</option>
                                    <option value="ASSESSMENT">Assessment</option>
                                    <option value="REMEDIATION">Remediation</option>
                                    <option value="CONFIG_CHANGE">Configuration Change</option>
                                    <option value="ACCESS">Access</option>
                                </select>
                                <button id="export-audit" class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm">
                                    <i class="fas fa-download mr-2"></i>Export
                                </button>
                            </div>
                        </div>
                        <div id="audit-trail-list" class="space-y-2">
                            <!-- Dynamic content -->
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Setup tab switching
        this.setupTabSwitching();
        
        // Setup event listeners
        this.setupEventListeners();
    }

    setupTabSwitching() {
        const tabButtons = document.querySelectorAll('.security-tab-btn');
        const tabContents = document.querySelectorAll('.security-tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabId = button.getAttribute('data-tab');

                // Update button states
                tabButtons.forEach(btn => {
                    btn.classList.remove('border-blue-500', 'text-blue-400', 'active');
                    btn.classList.add('border-transparent', 'text-slate-400');
                });
                button.classList.remove('border-transparent', 'text-slate-400');
                button.classList.add('border-blue-500', 'text-blue-400', 'active');

                // Update content visibility
                tabContents.forEach(content => content.classList.add('hidden'));
                document.getElementById(`${tabId}-tab`).classList.remove('hidden');
            });
        });
    }

    setupEventListeners() {
        // Severity filter for policy violations
        const severityFilter = document.getElementById('severity-filter');
        if (severityFilter) {
            severityFilter.addEventListener('change', () => {
                this.loadPolicyViolations(severityFilter.value);
            });
        }

        // Refresh violations button
        const refreshBtn = document.getElementById('refresh-violations');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadPolicyViolations();
            });
        }

        // Vulnerability severity filter
        const vulnSeverityFilter = document.getElementById('vuln-severity-filter');
        if (vulnSeverityFilter) {
            vulnSeverityFilter.addEventListener('change', () => {
                this.loadVulnerabilities(vulnSeverityFilter.value);
            });
        }

        // Trigger vulnerability scan
        const triggerScanBtn = document.getElementById('trigger-scan');
        if (triggerScanBtn) {
            triggerScanBtn.addEventListener('click', () => {
                this.triggerVulnerabilityScan();
            });
        }

        // Event type filter for audit trail
        const eventTypeFilter = document.getElementById('event-type-filter');
        if (eventTypeFilter) {
            eventTypeFilter.addEventListener('change', () => {
                this.loadAuditTrail(eventTypeFilter.value);
            });
        }

        // Export audit trail
        const exportAuditBtn = document.getElementById('export-audit');
        if (exportAuditBtn) {
            exportAuditBtn.addEventListener('click', () => {
                this.exportAuditTrail();
            });
        }
    }

    async loadSecurityOverview() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/overview`);
            const data = await response.json();

            // Update overview cards
            document.getElementById('security-score').textContent = Math.round(data.overall_score);
            document.getElementById('security-grade').textContent = `Grade: ${data.grade}`;
            document.getElementById('critical-alerts').textContent = data.alerts_count;
            document.getElementById('critical-vulns').textContent = data.critical_vulnerabilities;
            document.getElementById('compliance-score').textContent = `${Math.round(data.compliance_percentage)}%`;

            // Update trend indicator
            const trendElement = document.getElementById('security-trend');
            const trendIcon = data.trend === 'improving' ? '📈' : data.trend === 'declining' ? '📉' : '➡️';
            trendElement.innerHTML = `<span class="text-slate-400">Trend: </span><span class="ml-1 text-slate-300">${trendIcon} ${data.trend}</span>`;

            // Load detailed breakdown
            await this.loadSecurityBreakdown();

            this.lastUpdate = new Date();
            console.log('✅ Security overview loaded');

        } catch (error) {
            console.error('❌ Failed to load security overview:', error);
            this.showError('Failed to load security overview');
        }
    }

    async loadSecurityBreakdown() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/score/detailed`);
            const data = await response.json();

            const breakdownContainer = document.getElementById('security-breakdown');
            const breakdown = data.breakdown;

            breakdownContainer.innerHTML = Object.entries(breakdown).map(([key, value]) => {
                const label = key.replace('_score', '').replace('_', ' ').toUpperCase();
                const percentage = Math.round(value);
                const color = percentage >= 80 ? 'green' : percentage >= 60 ? 'yellow' : 'red';

                return `
                    <div class="flex items-center justify-between py-2">
                        <span class="text-sm text-slate-300">${label}</span>
                        <div class="flex items-center space-x-3">
                            <div class="w-24 bg-slate-700 rounded-full h-2">
                                <div class="bg-${color}-500 h-2 rounded-full" style="width: ${percentage}%"></div>
                            </div>
                            <span class="text-sm text-white w-12 text-right">${percentage}%</span>
                        </div>
                    </div>
                `;
            }).join('');

        } catch (error) {
            console.error('❌ Failed to load security breakdown:', error);
        }
    }

    async loadPolicyViolations(severity = '') {
        try {
            const url = severity ? 
                `${this.apiBaseUrl}/policy-violations?severity=${severity}` : 
                `${this.apiBaseUrl}/policy-violations`;
            
            const response = await fetch(url);
            const violations = await response.json();

            const container = document.getElementById('policy-violations-list');
            
            if (violations.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-8 text-slate-400">
                        <i class="fas fa-check-circle text-4xl mb-4 text-green-500"></i>
                        <p>No policy violations found</p>
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
                        <div class="flex items-start justify-between">
                            <div class="flex-1">
                                <div class="flex items-center space-x-3 mb-2">
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${severityColor}-100 text-${severityColor}-800">
                                        ${violation.severity}
                                    </span>
                                    ${violation.auto_remediable ? 
                                        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Auto-fix Available</span>' : 
                                        ''
                                    }
                                </div>
                                <h4 class="text-white font-medium">${violation.policy_name}</h4>
                                <p class="text-slate-400 text-sm mt-1">${violation.description}</p>
                                <div class="mt-2 text-xs text-slate-500">
                                    <span>${violation.resource_name}</span> • 
                                    <span>${violation.namespace}</span> • 
                                    <span>${new Date(violation.detected_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                            <button class="text-slate-400 hover:text-white" onclick="securityDashboard.showViolationDetails('${violation.violation_id}')">
                                <i class="fas fa-chevron-right"></i>
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            console.log(`✅ Loaded ${violations.length} policy violations`);

        } catch (error) {
            console.error('❌ Failed to load policy violations:', error);
            this.showError('Failed to load policy violations');
        }
    }

    async loadCompliance() {
        try {
            // Load compliance frameworks
            const frameworksResponse = await fetch(`${this.apiBaseUrl}/compliance/frameworks`);
            const frameworksData = await frameworksResponse.json();

            const container = document.getElementById('compliance-frameworks');
            
            // Load compliance status for each framework
            const compliancePromises = frameworksData.frameworks.map(async (framework) => {
                try {
                    const response = await fetch(`${this.apiBaseUrl}/compliance/${framework.id}`);
                    const data = await response.json();
                    return { ...framework, ...data };
                } catch (error) {
                    return { ...framework, error: error.message };
                }
            });

            const complianceResults = await Promise.all(compliancePromises);

            container.innerHTML = complianceResults.map(result => {
                if (result.error) {
                    return `
                        <div class="bg-slate-900 rounded-lg p-4 border border-slate-700">
                            <div class="flex items-center justify-between">
                                <div>
                                    <h4 class="text-white font-medium">${result.name}</h4>
                                    <p class="text-red-400 text-sm">Error: ${result.error}</p>
                                </div>
                                <span class="text-slate-500">--</span>
                            </div>
                        </div>
                    `;
                }

                const percentage = Math.round(result.overall_compliance || 0);
                const gradeColor = {
                    'A': 'green', 'B': 'blue', 'C': 'yellow', 'D': 'orange', 'F': 'red'
                }[result.grade?.[0]] || 'gray';

                return `
                    <div class="bg-slate-900 rounded-lg p-4 border border-slate-700">
                        <div class="flex items-center justify-between">
                            <div class="flex-1">
                                <div class="flex items-center space-x-3 mb-2">
                                    <h4 class="text-white font-medium">${result.name}</h4>
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${gradeColor}-100 text-${gradeColor}-800">
                                        Grade ${result.grade}
                                    </span>
                                </div>
                                <div class="flex items-center space-x-4">
                                    <div class="flex-1">
                                        <div class="flex items-center justify-between text-sm mb-1">
                                            <span class="text-slate-400">Compliance</span>
                                            <span class="text-white">${percentage}%</span>
                                        </div>
                                        <div class="w-full bg-slate-700 rounded-full h-2">
                                            <div class="bg-${gradeColor}-500 h-2 rounded-full" style="width: ${percentage}%"></div>
                                        </div>
                                    </div>
                                    <div class="text-right text-sm">
                                        <div class="text-green-400">${result.passed_controls || 0} passed</div>
                                        <div class="text-red-400">${result.failed_controls || 0} failed</div>
                                    </div>
                                </div>
                            </div>
                            <button class="text-slate-400 hover:text-white ml-4" onclick="securityDashboard.showComplianceDetails('${result.framework}')">
                                <i class="fas fa-external-link-alt"></i>
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            console.log('✅ Compliance frameworks loaded');

        } catch (error) {
            console.error('❌ Failed to load compliance:', error);
            this.showError('Failed to load compliance data');
        }
    }

    async loadVulnerabilities(severity = '') {
        try {
            // Load vulnerability summary
            const summaryResponse = await fetch(`${this.apiBaseUrl}/vulnerabilities/summary`);
            const summary = await summaryResponse.json();

            // Update summary display
            const summaryContainer = document.getElementById('vuln-summary');
            summaryContainer.innerHTML = `
                <div class="text-center">
                    <div class="text-2xl font-bold text-red-400">${summary.by_severity?.CRITICAL || 0}</div>
                    <div class="text-sm text-slate-400">Critical</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-orange-400">${summary.by_severity?.HIGH || 0}</div>
                    <div class="text-sm text-slate-400">High</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-yellow-400">${summary.by_severity?.MEDIUM || 0}</div>
                    <div class="text-sm text-slate-400">Medium</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-blue-400">${summary.by_severity?.LOW || 0}</div>
                    <div class="text-sm text-slate-400">Low</div>
                </div>
            `;

            // Load vulnerability list
            const url = severity ? 
                `${this.apiBaseUrl}/vulnerabilities?severity=${severity}` : 
                `${this.apiBaseUrl}/vulnerabilities`;
            
            const response = await fetch(url);
            const vulnerabilities = await response.json();

            const container = document.getElementById('vulnerabilities-list');
            
            if (vulnerabilities.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-8 text-slate-400">
                        <i class="fas fa-shield-alt text-4xl mb-4 text-green-500"></i>
                        <p>No vulnerabilities found</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = vulnerabilities.map(vuln => {
                const severityColor = {
                    'CRITICAL': 'red',
                    'HIGH': 'orange',
                    'MEDIUM': 'yellow',
                    'LOW': 'blue'
                }[vuln.severity] || 'gray';

                return `
                    <div class="bg-slate-900 rounded-lg p-4 border border-slate-700">
                        <div class="flex items-start justify-between">
                            <div class="flex-1">
                                <div class="flex items-center space-x-3 mb-2">
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${severityColor}-100 text-${severityColor}-800">
                                        ${vuln.severity}
                                    </span>
                                    <span class="text-slate-400 text-sm">CVSS: ${vuln.cvss_score}</span>
                                    ${vuln.exploit_available ? 
                                        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Exploit Available</span>' : 
                                        ''
                                    }
                                </div>
                                <h4 class="text-white font-medium">${vuln.title}</h4>
                                ${vuln.cve_id ? `<p class="text-blue-400 text-sm font-mono">${vuln.cve_id}</p>` : ''}
                                <p class="text-slate-400 text-sm mt-1">${vuln.affected_component}</p>
                                <div class="mt-2 text-xs text-slate-500">
                                    Detected: ${new Date(vuln.detected_at).toLocaleDateString()}
                                </div>
                            </div>
                            <button class="text-slate-400 hover:text-white" onclick="securityDashboard.showVulnerabilityDetails('${vuln.vuln_id}')">
                                <i class="fas fa-chevron-right"></i>
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            console.log(`✅ Loaded ${vulnerabilities.length} vulnerabilities`);

        } catch (error) {
            console.error('❌ Failed to load vulnerabilities:', error);
            this.showError('Failed to load vulnerabilities');
        }
    }

    async loadSecurityTrends() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/trends/security_score?days=30`);
            const trendsData = await response.json();

            const ctx = document.getElementById('security-trends-chart').getContext('2d');
            
            if (this.charts.has('security-trends')) {
                this.charts.get('security-trends').destroy();
            }

            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: trendsData.data_points.map(point => 
                        new Date(point.date).toLocaleDateString()
                    ),
                    datasets: [{
                        label: 'Security Score',
                        data: trendsData.data_points.map(point => point.value),
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            grid: {
                                color: 'rgba(148, 163, 184, 0.1)'
                            },
                            ticks: {
                                color: 'rgba(148, 163, 184, 0.8)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(148, 163, 184, 0.1)'
                            },
                            ticks: {
                                color: 'rgba(148, 163, 184, 0.8)',
                                maxTicksLimit: 7
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                color: 'rgba(148, 163, 184, 0.8)'
                            }
                        }
                    }
                }
            });

            this.charts.set('security-trends', chart);
            console.log('✅ Security trends chart loaded');

        } catch (error) {
            console.error('❌ Failed to load security trends:', error);
        }
    }

    async loadAuditTrail(eventType = '') {
        try {
            const url = eventType ? 
                `${this.apiBaseUrl}/audit-trail?event_type=${eventType}` : 
                `${this.apiBaseUrl}/audit-trail`;
            
            const response = await fetch(url);
            const auditEntries = await response.json();

            const container = document.getElementById('audit-trail-list');
            
            if (auditEntries.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-8 text-slate-400">
                        <i class="fas fa-history text-4xl mb-4"></i>
                        <p>No audit trail entries found</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = auditEntries.map(entry => {
                const eventTypeColor = {
                    'ASSESSMENT': 'blue',
                    'REMEDIATION': 'green',
                    'CONFIG_CHANGE': 'yellow',
                    'ACCESS': 'purple'
                }[entry.event_type] || 'gray';

                return `
                    <div class="flex items-center space-x-4 py-3 px-4 bg-slate-900 rounded-lg">
                        <div class="flex-shrink-0">
                            <div class="w-2 h-2 bg-${eventTypeColor}-500 rounded-full"></div>
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center space-x-3">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${eventTypeColor}-100 text-${eventTypeColor}-800">
                                    ${entry.event_type}
                                </span>
                                <span class="text-slate-400 text-sm">${entry.user}</span>
                                <span class="text-slate-500 text-xs">${new Date(entry.timestamp).toLocaleString()}</span>
                            </div>
                            <p class="text-white text-sm mt-1">${entry.action}</p>
                            <p class="text-slate-400 text-xs">${entry.resource_name} • ${entry.compliance_impact}</p>
                        </div>
                    </div>
                `;
            }).join('');

            console.log(`✅ Loaded ${auditEntries.length} audit trail entries`);

        } catch (error) {
            console.error('❌ Failed to load audit trail:', error);
            this.showError('Failed to load audit trail');
        }
    }

    async triggerVulnerabilityScan() {
        try {
            const button = document.getElementById('trigger-scan');
            const originalText = button.innerHTML;
            
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Scanning...';
            button.disabled = true;

            const response = await fetch(`${this.apiBaseUrl}/vulnerabilities/scan`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            this.showNotification('Vulnerability scan started successfully', 'success');
            
            // Refresh vulnerabilities after a delay
            setTimeout(() => {
                this.loadVulnerabilities();
            }, 5000);

            button.innerHTML = originalText;
            button.disabled = false;

        } catch (error) {
            console.error('❌ Failed to trigger vulnerability scan:', error);
            this.showError('Failed to trigger vulnerability scan');
            
            const button = document.getElementById('trigger-scan');
            button.innerHTML = '<i class="fas fa-search mr-2"></i>New Scan';
            button.disabled = false;
        }
    }

    async exportAuditTrail() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/export/audit-trail?format=csv`);
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `audit-trail-${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            this.showNotification('Audit trail exported successfully', 'success');

        } catch (error) {
            console.error('❌ Failed to export audit trail:', error);
            this.showError('Failed to export audit trail');
        }
    }

    showViolationDetails(violationId) {
        // Implement modal or detailed view for policy violation
        console.log('Show violation details:', violationId);
        // You can implement a modal or navigate to a detailed view
    }

    showComplianceDetails(framework) {
        // Implement detailed compliance view
        console.log('Show compliance details:', framework);
        // You can implement navigation to detailed compliance report
    }

    showVulnerabilityDetails(vulnId) {
        // Implement detailed vulnerability view
        console.log('Show vulnerability details:', vulnId);
        // You can implement a modal with remediation guidance
    }

    startAutoRefresh() {
        // Clear existing intervals
        this.activeIntervals.forEach(interval => clearInterval(interval));
        this.activeIntervals.clear();

        // Set up auto-refresh for different components
        const overviewInterval = setInterval(() => {
            this.loadSecurityOverview();
        }, this.refreshInterval);
        
        this.activeIntervals.set('overview', overviewInterval);

        console.log(`🔄 Auto-refresh started (${this.refreshInterval/1000}s interval)`);
    }

    stopAutoRefresh() {
        this.activeIntervals.forEach(interval => clearInterval(interval));
        this.activeIntervals.clear();
        console.log('⏹️ Auto-refresh stopped');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 max-w-sm w-full px-4 py-3 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
        
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
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, 5000);
    }

    destroy() {
        this.stopAutoRefresh();
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
        console.log('🔐 Security Posture Dashboard destroyed');
    }
}

// Global instance
let securityDashboard;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    securityDashboard = new SecurityPostureDashboard();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SecurityPostureDashboard;
}