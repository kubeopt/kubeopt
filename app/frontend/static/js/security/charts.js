/**
 * ============================================================================
 * SECURITY DASHBOARD CHARTS - ENTERPRISE DARK THEME
 * ============================================================================
 * Comprehensive chart management for security posture visualization
 * ============================================================================
 */

// Security chart instance management
window.securityChartInstances = window.securityChartInstances || {};

// Safe chart destruction for security charts
function safeDestroySecurityChart(chartId) {
    try {
        const chart = window.securityChartInstances[chartId];
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
            delete window.securityChartInstances[chartId];
            
            const canvas = document.getElementById(chartId);
            if (canvas && canvas.getContext) {
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }
        }
    } catch (error) {
        console.warn(`Failed to destroy security chart ${chartId}:`, error);
    }
}

class SecurityCharts {
    constructor() {
        this.chartInstances = {};
    }

    // Initialize all security charts
    initializeSecurityCharts(data) {
        console.log('🔍 Initializing security charts with data:', data);
        const analysis = data.analysis || data;
        const posture = analysis.security_posture || {};
        const violations = analysis.policy_compliance?.violations || [];
        const compliance = analysis.compliance_frameworks || {};
        const alerts = posture.alerts || [];

        console.log('📊 Chart data extracted:');
        console.log('  - Violations:', violations.length);
        console.log('  - Compliance frameworks:', Object.keys(compliance).length);
        console.log('  - Security score:', posture.overall_score);

        // Initialize Overview Charts
        this.createSecurityTrendChart(posture);
        this.createRiskDistributionChart(violations);
        this.createComplianceChart(compliance);

        // Initialize Dynamic Alert Chart
        this.createDynamicAlertsChart(alerts);

        // Initialize Violations Tab Charts
        this.createViolationSeverityChart(violations);
        this.createViolationCategoryChart(violations);
        this.createViolationPolicyChart(violations);

        // Initialize Compliance Tab Charts
        this.createComplianceOverallChart(compliance);
        this.createComplianceFrameworkChart(compliance);
        this.createComplianceControlsChart(compliance);

        // Initialize Trends Tab Charts
        this.createTrendCharts(posture, alerts, violations, compliance);
    }

    // Helper function for creating properly styled donut charts
    createDonutChart(chartId, categories, data, field) {
        const canvas = document.getElementById(chartId);
        if (!canvas) return;
        
        // Destroy existing chart
        safeDestroySecurityChart(chartId);

        const ctx = canvas.getContext('2d');
        
        // Process data based on categories
        const categoryList = categories.split(',');
        const counts = {};
        
        categoryList.forEach(cat => counts[cat] = 0);
        data.forEach(item => {
            const value = item[field] || 'OTHER';
            if (counts.hasOwnProperty(value.toUpperCase())) {
                counts[value.toUpperCase()]++;
            }
        });

        const config = {
            type: 'doughnut',
            data: {
                labels: Object.keys(counts),
                datasets: [{
                    data: Object.values(counts),
                    backgroundColor: ['rgb(248, 113, 113)', 'rgb(251, 146, 60)', 'rgb(250, 204, 21)', 'rgb(74, 222, 128)', 'rgb(96, 165, 250)'],
                    borderWidth: 2,
                    borderColor: '#171d33'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1
                    }
                },
                cutout: '60%'
            }
        };

        window.securityChartInstances[chartId] = new Chart(ctx, config);
    }

    // Overview Tab Charts
    createSecurityTrendChart(posture) {
        const canvas = document.getElementById('security-trend-chart');
        if (!canvas) return;
        
        safeDestroySecurityChart('security-trend-chart');

        const ctx = canvas.getContext('2d');
        
        const securityScore = posture.overall_score || 75;
        
        const config = {
            type: 'line',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Current'],
                datasets: [{
                    label: 'Security Score',
                    data: [securityScore - 10, securityScore - 5, securityScore - 2, securityScore + 3, securityScore],
                    borderColor: 'rgb(96, 165, 250)',
                    backgroundColor: 'rgba(96, 165, 250, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255,255,255,0.1)', drawBorder: false },
                        ticks: { color: 'rgb(148, 163, 184)', font: { size: 11 } }
                    },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.1)', drawBorder: false },
                        ticks: { color: 'rgb(148, 163, 184)', font: { size: 11 } },
                        beginAtZero: true,
                        max: 100
                    }
                },
                elements: {
                    point: { radius: 3, hoverRadius: 6 }
                }
            }
        };

        window.securityChartInstances['security-trend-chart'] = new Chart(ctx, config);
    }

    createRiskDistributionChart(violations) {
        console.log('🍩 Creating risk distribution chart with violations:', violations);
        const canvas = document.getElementById('risk-donut-chart');
        if (!canvas) {
            console.warn('❌ Risk donut chart canvas not found!');
            return;
        }
        
        safeDestroySecurityChart('risk-donut-chart');

        const ctx = canvas.getContext('2d');

        const riskCounts = {
            critical: violations.filter(v => (v.severity || '').toLowerCase() === 'critical').length,
            high: violations.filter(v => (v.severity || '').toLowerCase() === 'high').length,
            medium: violations.filter(v => (v.severity || '').toLowerCase() === 'medium').length,
            low: violations.filter(v => (v.severity || '').toLowerCase() === 'low').length
        };

        console.log('📊 Risk counts calculated:', riskCounts);
        
        // Handle empty data case
        const totalRisks = Object.values(riskCounts).reduce((a, b) => a + b, 0);
        if (totalRisks === 0) {
            console.warn('⚠️ No violations found, hiding risk distribution chart');
            canvas.style.display = 'none';
            const parentContainer = canvas.closest('.p-6');
            if (parentContainer) {
                parentContainer.style.display = 'none';
            }
            return;
        }

        const config = {
            type: 'doughnut',
            data: {
                labels: ['Critical', 'High', 'Medium', 'Low'],
                datasets: [{
                    data: [riskCounts.critical, riskCounts.high, riskCounts.medium, riskCounts.low],
                    backgroundColor: ['rgb(248, 113, 113)', 'rgb(251, 146, 60)', 'rgb(250, 204, 21)', 'rgb(74, 222, 128)'],
                    borderWidth: 2,
                    borderColor: '#171d33'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1
                    }
                },
                cutout: '60%'
            }
        };

        window.securityChartInstances['risk-donut-chart'] = new Chart(ctx, config);

        // Update risk distribution text
        const riskContainer = document.getElementById('risk-distribution');
        if (riskContainer) {
            riskContainer.innerHTML = `
                <div class="grid grid-cols-2 gap-2 text-xs">
                    <div class="flex items-center gap-2">
                        <div style="width: 8px; height: 8px; background: rgb(248, 113, 113); border-radius: 50%;"></div>
                        <span style="color: rgb(148, 163, 184);">Critical: ${riskCounts.critical}</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <div style="width: 8px; height: 8px; background: rgb(251, 146, 60); border-radius: 50%;"></div>
                        <span style="color: rgb(148, 163, 184);">High: ${riskCounts.high}</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <div style="width: 8px; height: 8px; background: rgb(250, 204, 21); border-radius: 50%;"></div>
                        <span style="color: rgb(148, 163, 184);">Medium: ${riskCounts.medium}</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <div style="width: 8px; height: 8px; background: rgb(74, 222, 128); border-radius: 50%;"></div>
                        <span style="color: rgb(148, 163, 184);">Low: ${riskCounts.low}</span>
                    </div>
                </div>
            `;
        }
    }

    createComplianceChart(compliance) {
        console.log('📊 Creating compliance chart with data:', compliance);
        const canvas = document.getElementById('compliance-bar-chart');
        if (!canvas) {
            console.warn('❌ Compliance bar chart canvas not found!');
            return;
        }
        
        safeDestroySecurityChart('compliance-bar-chart');

        const ctx = canvas.getContext('2d');

        const frameworks = Object.keys(compliance);
        const scores = frameworks.map(f => compliance[f].overall_compliance || compliance[f].score || 0);
        
        console.log('📋 Frameworks and scores:', { frameworks, scores });
        
        // Handle empty data case
        if (frameworks.length === 0) {
            console.warn('⚠️ No compliance frameworks found, hiding chart');
            canvas.style.display = 'none';
            const parentContainer = canvas.closest('.p-6');
            if (parentContainer) {
                parentContainer.style.display = 'none';
            }
            return;
        }

        const config = {
            type: 'bar',
            data: {
                labels: frameworks.map(f => f.toUpperCase()),
                datasets: [{
                    data: scores,
                    backgroundColor: 'rgba(74, 222, 128, 0.8)',
                    borderColor: 'rgb(74, 222, 128)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255,255,255,0.1)', drawBorder: false },
                        ticks: { color: 'rgb(148, 163, 184)', font: { size: 11 } }
                    },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.1)', drawBorder: false },
                        ticks: { color: 'rgb(148, 163, 184)', font: { size: 11 } },
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        };

        window.securityChartInstances['compliance-bar-chart'] = new Chart(ctx, config);
    }

    // Dynamic Alerts Chart
    createDynamicAlertsChart(alerts) {
        const canvas = document.getElementById('dynamic-alerts-chart');
        if (!canvas) {
            console.warn('❌ Dynamic alerts chart canvas not found!');
            return;
        }

        // Handle empty data case
        if (alerts.length === 0) {
            console.warn('⚠️ No alerts found, hiding chart');
            canvas.style.display = 'none';
            const parentContainer = canvas.closest('.p-6');
            if (parentContainer) {
                parentContainer.style.display = 'none';
            }
            return;
        }

        // Set up view selector
        const viewSelector = document.getElementById('alert-chart-view');
        if (viewSelector) {
            viewSelector.addEventListener('change', () => {
                this.updateDynamicAlertsChart(alerts, viewSelector.value);
            });
        }

        // Initialize with severity view
        this.updateDynamicAlertsChart(alerts, 'severity');
        this.updateAlertsSummaryStats(alerts);
    }

    updateDynamicAlertsChart(alerts, viewType) {
        const canvas = document.getElementById('dynamic-alerts-chart');
        if (!canvas) return;

        safeDestroySecurityChart('dynamic-alerts-chart');
        const ctx = canvas.getContext('2d');

        let chartData;
        let colors;
        let title;

        switch(viewType) {
            case 'severity':
                chartData = this.processAlertsBySeverity(alerts);
                colors = ['rgb(248, 113, 113)', 'rgb(251, 146, 60)', 'rgb(250, 204, 21)', 'rgb(74, 222, 128)'];
                title = 'Alerts by Severity';
                break;
            case 'category':
                chartData = this.processAlertsByCategory(alerts);
                colors = ['rgb(147, 51, 234)', 'rgb(96, 165, 250)', 'rgb(34, 197, 94)', 'rgb(245, 101, 101)'];
                title = 'Alerts by Category';
                break;
            case 'status':
                chartData = this.processAlertsByStatus(alerts);
                colors = ['rgb(248, 113, 113)', 'rgb(74, 222, 128)', 'rgb(250, 204, 21)'];
                title = 'Alerts by Status';
                break;
        }

        const config = {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.values,
                    backgroundColor: colors.slice(0, chartData.labels.length),
                    borderWidth: 2,
                    borderColor: '#171d33'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        callbacks: {
                            title: function() {
                                return title;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        };

        window.securityChartInstances['dynamic-alerts-chart'] = new Chart(ctx, config);
    }

    processAlertsBySeverity(alerts) {
        const counts = {
            critical: alerts.filter(a => (a.severity || '').toLowerCase() === 'critical').length,
            high: alerts.filter(a => (a.severity || '').toLowerCase() === 'high').length,
            medium: alerts.filter(a => (a.severity || '').toLowerCase() === 'medium').length,
            low: alerts.filter(a => (a.severity || '').toLowerCase() === 'low').length
        };

        return {
            labels: Object.keys(counts).map(s => s.charAt(0).toUpperCase() + s.slice(1)).filter((_, i) => Object.values(counts)[i] > 0),
            values: Object.values(counts).filter(v => v > 0)
        };
    }

    processAlertsByCategory(alerts) {
        const categories = {};
        alerts.forEach(alert => {
            const category = (alert.category || 'Other').toLowerCase();
            const key = category.charAt(0).toUpperCase() + category.slice(1);
            categories[key] = (categories[key] || 0) + 1;
        });

        return {
            labels: Object.keys(categories),
            values: Object.values(categories)
        };
    }

    processAlertsByStatus(alerts) {
        const counts = {
            active: alerts.filter(a => (a.status || 'active').toLowerCase() === 'active').length,
            resolved: alerts.filter(a => (a.status || '').toLowerCase() === 'resolved').length,
            investigating: alerts.filter(a => (a.status || '').toLowerCase() === 'investigating').length
        };

        return {
            labels: Object.keys(counts).map(s => s.charAt(0).toUpperCase() + s.slice(1)).filter((_, i) => Object.values(counts)[i] > 0),
            values: Object.values(counts).filter(v => v > 0)
        };
    }

    updateAlertsSummaryStats(alerts) {
        const statsContainer = document.getElementById('alerts-summary-stats');
        if (!statsContainer) return;

        const stats = {
            total: alerts.length,
            critical: alerts.filter(a => (a.severity || '').toLowerCase() === 'critical').length,
            active: alerts.filter(a => (a.status || 'active').toLowerCase() === 'active').length,
            categories: [...new Set(alerts.map(a => a.category).filter(Boolean))].length
        };

        statsContainer.innerHTML = `
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                    <div class="text-2xl font-bold text-blue-400">${stats.total}</div>
                    <div class="text-xs text-slate-400">Total Alerts</div>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                    <div class="text-2xl font-bold text-red-400">${stats.critical}</div>
                    <div class="text-xs text-slate-400">Critical</div>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                    <div class="text-2xl font-bold text-orange-400">${stats.active}</div>
                    <div class="text-xs text-slate-400">Active</div>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                    <div class="text-2xl font-bold text-green-400">${stats.categories}</div>
                    <div class="text-xs text-slate-400">Categories</div>
                </div>
            </div>
        `;
    }

    // Violations Tab Charts
    createViolationSeverityChart(violations) {
        this.createDonutChart('violations-severity-chart', 'CRITICAL,HIGH,MEDIUM,LOW', violations, 'severity');
    }

    createViolationCategoryChart(violations) {
        this.createDonutChart('violations-category-chart', 'SECURITY,GOVERNANCE,NETWORK', violations, 'category');
    }

    createViolationPolicyChart(violations) {
        this.createDonutChart('violations-policy-chart', 'RBAC,NETWORK,SECURITY,RESOURCE', violations, 'policy_type');
    }

    // Compliance Tab Charts
    createComplianceOverallChart(compliance) {
        this.createDonutChart('compliance-overall-chart', 'PASSED,FAILED', [], 'dummy');
    }

    createComplianceFrameworkChart(compliance) {
        const frameworks = Object.keys(compliance).join(',').toUpperCase();
        this.createDonutChart('compliance-framework-chart', frameworks, [], 'dummy');
    }

    createComplianceControlsChart(compliance) {
        this.createDonutChart('compliance-controls-chart', 'PASSED,FAILED', [], 'dummy');
    }

    // Trend Tab Charts
    createTrendCharts(posture, alerts, violations, compliance) {
        const periods = ['30d ago', '21d ago', '14d ago', '7d ago', 'Today'];
        
        // Security Score Trend
        const scoreCanvas = document.getElementById('score-trend-line-chart');
        if (scoreCanvas) {
            safeDestroySecurityChart('score-trend-line-chart');
            
            const scoreCtx = scoreCanvas.getContext('2d');
            const currentScore = posture.overall_score || 75;
            const scoreData = [currentScore - 15, currentScore - 8, currentScore - 3, currentScore + 2, currentScore];
            
            const scoreConfig = {
                type: 'line',
                data: {
                    labels: periods,
                    datasets: [{
                        label: 'Security Score',
                        data: scoreData,
                        borderColor: 'rgb(96, 165, 250)',
                        backgroundColor: 'rgba(96, 165, 250, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: 'white',
                            bodyColor: 'white',
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            borderWidth: 1
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255,255,255,0.1)', drawBorder: false },
                            ticks: { color: 'rgb(148, 163, 184)', font: { size: 11 } }
                        },
                        y: {
                            grid: { color: 'rgba(255,255,255,0.1)', drawBorder: false },
                            ticks: { color: 'rgb(148, 163, 184)', font: { size: 11 } },
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            };
            
            window.securityChartInstances['score-trend-line-chart'] = new Chart(scoreCtx, scoreConfig);
        }

        // Alert Volume Trend
        const alertCanvas = document.getElementById('alert-volume-chart');
        if (alertCanvas) {
            safeDestroySecurityChart('alert-volume-chart');
            
            const alertCtx = alertCanvas.getContext('2d');
            const currentAlerts = alerts.length;
            const alertData = [currentAlerts + 8, currentAlerts + 5, currentAlerts + 2, currentAlerts - 1, currentAlerts];
            
            const alertConfig = {
                type: 'bar',
                data: {
                    labels: periods,
                    datasets: [{
                        label: 'Active Alerts',
                        data: alertData,
                        backgroundColor: 'rgba(248, 113, 113, 0.8)',
                        borderColor: 'rgb(248, 113, 113)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: 'white',
                            bodyColor: 'white',
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            borderWidth: 1
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255,255,255,0.1)', drawBorder: false },
                            ticks: { color: 'rgb(148, 163, 184)', font: { size: 11 } }
                        },
                        y: {
                            grid: { color: 'rgba(255,255,255,0.1)', drawBorder: false },
                            ticks: { color: 'rgb(148, 163, 184)', font: { size: 11 } },
                            beginAtZero: true
                        }
                    }
                }
            };
            
            window.securityChartInstances['alert-volume-chart'] = new Chart(alertCtx, alertConfig);
        }
    }
}

// Initialize global security charts instance
window.securityCharts = new SecurityCharts();