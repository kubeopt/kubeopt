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
        console.log('🍩 Creating enhanced risk distribution chart with violations:', violations);
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

        console.log('📊 Enhanced risk counts calculated:', riskCounts);
        
        // Handle empty data case with better UX
        const totalRisks = Object.values(riskCounts).reduce((a, b) => a + b, 0);
        if (totalRisks === 0) {
            // Show a "no risks" visualization instead of hiding
            this.showNoRisksVisualization(canvas);
            return;
        }

        // Filter out zero values for cleaner chart
        const nonZeroRisks = Object.entries(riskCounts).filter(([_, count]) => count > 0);
        const labels = nonZeroRisks.map(([level, _]) => level.charAt(0).toUpperCase() + level.slice(1));
        const data = nonZeroRisks.map(([_, count]) => count);
        
        // Enhanced color scheme with better contrast
        const colorMap = {
            'Critical': { bg: 'rgba(239, 68, 68, 0.9)', border: 'rgb(220, 38, 38)' },
            'High': { bg: 'rgba(245, 101, 101, 0.9)', border: 'rgb(239, 68, 68)' },
            'Medium': { bg: 'rgba(251, 146, 60, 0.9)', border: 'rgb(245, 101, 101)' },
            'Low': { bg: 'rgba(34, 197, 94, 0.9)', border: 'rgb(22, 163, 74)' }
        };
        
        const backgroundColors = labels.map(label => colorMap[label].bg);
        const borderColors = labels.map(label => colorMap[label].border);

        const config = {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 3,
                    hoverBorderWidth: 4,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: 'rgb(148, 163, 184)',
                            font: { size: 12, family: 'Poppins' },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(148, 163, 184, 0.3)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        titleFont: { size: 14, weight: 'bold' },
                        bodyFont: { size: 13 },
                        callbacks: {
                            label: function(context) {
                                const percentage = ((context.parsed / totalRisks) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '50%',
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        };

        window.securityChartInstances['risk-donut-chart'] = new Chart(ctx, config);

        // Enhanced risk distribution summary with better styling
        this.updateRiskDistributionSummary(riskCounts, totalRisks);
    }
    
    showNoRisksVisualization(canvas) {
        const ctx = canvas.getContext('2d');
        
        // Create a simple "no risks" donut chart
        const config = {
            type: 'doughnut',
            data: {
                labels: ['No Risks Detected'],
                datasets: [{
                    data: [1],
                    backgroundColor: ['rgba(34, 197, 94, 0.3)'],
                    borderColor: ['rgb(34, 197, 94)'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                cutout: '70%'
            }
        };
        
        window.securityChartInstances['risk-donut-chart'] = new Chart(ctx, config);
        
        // Add centered text
        const centerText = canvas.parentNode.querySelector('.center-text') || document.createElement('div');
        centerText.className = 'center-text absolute inset-0 flex items-center justify-center pointer-events-none';
        centerText.innerHTML = `
            <div class="text-center">
                <i class="fas fa-shield-check text-3xl text-green-400 mb-2"></i>
                <div class="text-sm text-slate-300 font-medium">No Security Risks</div>
                <div class="text-xs text-slate-500">All systems secure</div>
            </div>
        `;
        
        if (!canvas.parentNode.querySelector('.center-text')) {
            canvas.parentNode.classList.add('relative');
            canvas.parentNode.appendChild(centerText);
        }
    }
    
    updateRiskDistributionSummary(riskCounts, totalRisks) {
        const riskContainer = document.getElementById('risk-distribution');
        if (!riskContainer) return;

        // Calculate risk score (weighted)
        const riskScore = (
            (riskCounts.critical * 10) + 
            (riskCounts.high * 7) + 
            (riskCounts.medium * 4) + 
            (riskCounts.low * 1)
        );
        
        const maxPossibleScore = totalRisks * 10;
        const riskPercentage = maxPossibleScore > 0 ? ((riskScore / maxPossibleScore) * 100).toFixed(1) : 0;
        
        riskContainer.innerHTML = `
            <!-- Risk Summary Card -->
            <div class="bg-slate-800/50 rounded-lg p-4 mb-4 border border-slate-700">
                <div class="flex items-center justify-between mb-3">
                    <h4 class="text-sm font-semibold text-slate-200">Risk Assessment</h4>
                    <div class="text-right">
                        <div class="text-lg font-bold ${riskPercentage > 70 ? 'text-red-400' : riskPercentage > 40 ? 'text-yellow-400' : 'text-green-400'}">
                            ${riskPercentage}%
                        </div>
                        <div class="text-xs text-slate-500">Risk Level</div>
                    </div>
                </div>
                <div class="w-full bg-slate-700 rounded-full h-2 mb-3">
                    <div class="h-2 rounded-full transition-all duration-300 ${riskPercentage > 70 ? 'bg-red-500' : riskPercentage > 40 ? 'bg-yellow-500' : 'bg-green-500'}" 
                         style="width: ${riskPercentage}%"></div>
                </div>
            </div>
            
            <!-- Risk Breakdown -->
            <div class="space-y-3">
                ${Object.entries(riskCounts).map(([level, count]) => {
                    if (count === 0) return '';
                    const percentage = ((count / totalRisks) * 100).toFixed(1);
                    const colors = {
                        critical: { text: 'text-red-400', bg: 'bg-red-500' },
                        high: { text: 'text-orange-400', bg: 'bg-orange-500' },
                        medium: { text: 'text-yellow-400', bg: 'bg-yellow-500' },
                        low: { text: 'text-green-400', bg: 'bg-green-500' }
                    };
                    const color = colors[level] || { text: 'text-slate-400', bg: 'bg-slate-500' };
                    
                    return `
                        <div class="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-slate-600 transition-colors">
                            <div class="flex items-center space-x-3">
                                <div class="w-3 h-3 ${color.bg} rounded-full"></div>
                                <span class="text-sm font-medium text-slate-200">${level.charAt(0).toUpperCase() + level.slice(1)}</span>
                            </div>
                            <div class="flex items-center space-x-3">
                                <span class="${color.text} text-sm font-bold">${count}</span>
                                <span class="text-xs text-slate-500">${percentage}%</span>
                            </div>
                        </div>
                    `;
                }).filter(Boolean).join('')}
                
                <!-- Total Summary -->
                <div class="flex items-center justify-between p-3 bg-blue-900/20 rounded-lg border border-blue-700/50 mt-4">
                    <div class="flex items-center space-x-3">
                        <i class="fas fa-chart-pie text-blue-400"></i>
                        <span class="text-sm font-semibold text-blue-200">Total Issues</span>
                    </div>
                    <span class="text-lg font-bold text-blue-400">${totalRisks}</span>
                </div>
            </div>
        `;
    }

    createComplianceChart(compliance) {
        console.log('📊 Creating enhanced compliance chart with data:', compliance);
        const canvas = document.getElementById('compliance-bar-chart');
        if (!canvas) {
            console.warn('❌ Compliance bar chart canvas not found!');
            return;
        }
        
        safeDestroySecurityChart('compliance-bar-chart');

        const ctx = canvas.getContext('2d');

        const frameworks = Object.keys(compliance);
        const scores = frameworks.map(f => compliance[f].overall_compliance || compliance[f].score || 0);
        
        console.log('📋 Enhanced frameworks and scores:', { frameworks, scores });
        
        // Handle empty data case with better UX
        if (frameworks.length === 0) {
            this.showNoComplianceVisualization(canvas);
            return;
        }

        // Enhanced color coding based on compliance scores
        const backgroundColors = scores.map(score => {
            if (score >= 90) return 'rgba(34, 197, 94, 0.8)';   // Green - Excellent
            if (score >= 80) return 'rgba(59, 130, 246, 0.8)';  // Blue - Good  
            if (score >= 70) return 'rgba(251, 146, 60, 0.8)';  // Orange - Fair
            if (score >= 60) return 'rgba(245, 101, 101, 0.8)'; // Light Red - Poor
            return 'rgba(239, 68, 68, 0.8)';                    // Red - Critical
        });

        const borderColors = scores.map(score => {
            if (score >= 90) return 'rgb(34, 197, 94)';
            if (score >= 80) return 'rgb(59, 130, 246)';
            if (score >= 70) return 'rgb(251, 146, 60)';
            if (score >= 60) return 'rgb(245, 101, 101)';
            return 'rgb(239, 68, 68)';
        });

        // Enhanced framework labels with proper casing
        const enhancedLabels = frameworks.map(f => {
            const label = f.toUpperCase();
            return label.length > 8 ? label.substring(0, 8) + '...' : label;
        });

        const config = {
            type: 'bar',
            data: {
                labels: enhancedLabels,
                datasets: [{
                    label: 'Compliance Score (%)',
                    data: scores,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 2,
                    borderRadius: 4,
                    borderSkipped: false,
                    hoverBackgroundColor: backgroundColors.map(color => color.replace('0.8', '1.0')),
                    hoverBorderWidth: 3,
                    barThickness: 40,
                    maxBarThickness: 50
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        display: true,
                        position: 'top',
                        labels: {
                            color: 'rgb(148, 163, 184)',
                            font: { size: 12, family: 'Poppins' },
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(148, 163, 184, 0.3)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        titleFont: { size: 14, weight: 'bold' },
                        bodyFont: { size: 13 },
                        callbacks: {
                            title: function(context) {
                                return frameworks[context[0].dataIndex];
                            },
                            label: function(context) {
                                const score = context.parsed.y;
                                const grade = score >= 90 ? 'A+' : score >= 80 ? 'A' : score >= 70 ? 'B' : score >= 60 ? 'C' : 'F';
                                return `Compliance: ${score.toFixed(1)}% (Grade: ${grade})`;
                            },
                            afterLabel: function(context) {
                                const frameworkData = compliance[frameworks[context.dataIndex]];
                                if (frameworkData) {
                                    const passed = frameworkData.passed_controls || 0;
                                    const failed = frameworkData.failed_controls || 0;
                                    return `Controls: ${passed} passed, ${failed} failed`;
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { 
                            color: 'rgba(148, 163, 184, 0.1)', 
                            drawBorder: false 
                        },
                        ticks: { 
                            color: 'rgb(148, 163, 184)', 
                            font: { size: 11, family: 'Poppins' },
                            maxRotation: 45
                        }
                    },
                    y: {
                        grid: { 
                            color: 'rgba(148, 163, 184, 0.1)', 
                            drawBorder: false 
                        },
                        ticks: { 
                            color: 'rgb(148, 163, 184)', 
                            font: { size: 11, family: 'Poppins' },
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        beginAtZero: true,
                        max: 100
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        };

        window.securityChartInstances['compliance-bar-chart'] = new Chart(ctx, config);

        // Update compliance details summary
        this.updateComplianceDetails(compliance, frameworks, scores);
    }
    
    showNoComplianceVisualization(canvas) {
        const ctx = canvas.getContext('2d');
        
        // Create a placeholder chart
        const config = {
            type: 'bar',
            data: {
                labels: ['No Data'],
                datasets: [{
                    data: [0],
                    backgroundColor: ['rgba(148, 163, 184, 0.3)'],
                    borderColor: ['rgb(148, 163, 184)'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                scales: {
                    x: { display: false },
                    y: { display: false }
                }
            }
        };
        
        window.securityChartInstances['compliance-bar-chart'] = new Chart(ctx, config);
        
        // Add overlay message
        const overlay = canvas.parentNode.querySelector('.no-data-overlay') || document.createElement('div');
        overlay.className = 'no-data-overlay absolute inset-0 flex items-center justify-center pointer-events-none';
        overlay.innerHTML = `
            <div class="text-center">
                <i class="fas fa-clipboard-list text-3xl text-slate-400 mb-2"></i>
                <div class="text-sm text-slate-300 font-medium">No Compliance Data</div>
                <div class="text-xs text-slate-500">Run compliance analysis</div>
            </div>
        `;
        
        if (!canvas.parentNode.querySelector('.no-data-overlay')) {
            canvas.parentNode.classList.add('relative');
            canvas.parentNode.appendChild(overlay);
        }
    }
    
    updateComplianceDetails(compliance, frameworks, scores) {
        const detailsContainer = document.getElementById('compliance-details');
        if (!detailsContainer) return;

        const avgCompliance = frameworks.length > 0 ? (scores.reduce((a, b) => a + b, 0) / frameworks.length).toFixed(1) : 0;
        const totalPassed = frameworks.reduce((sum, f) => sum + (compliance[f].passed_controls || 0), 0);
        const totalFailed = frameworks.reduce((sum, f) => sum + (compliance[f].failed_controls || 0), 0);
        const totalControls = totalPassed + totalFailed;

        detailsContainer.innerHTML = `
            <!-- Overall Compliance Summary -->
            <div class="bg-slate-800/50 rounded-lg p-4 mb-4 border border-slate-700">
                <div class="flex items-center justify-between mb-3">
                    <h4 class="text-sm font-semibold text-slate-200">Overall Compliance</h4>
                    <div class="text-right">
                        <div class="text-lg font-bold ${avgCompliance >= 80 ? 'text-green-400' : avgCompliance >= 60 ? 'text-yellow-400' : 'text-red-400'}">
                            ${avgCompliance}%
                        </div>
                        <div class="text-xs text-slate-500">Average Score</div>
                    </div>
                </div>
                <div class="grid grid-cols-3 gap-3 text-center">
                    <div class="bg-slate-900/50 rounded p-2">
                        <div class="text-green-400 font-bold">${totalPassed}</div>
                        <div class="text-xs text-slate-500">Passed</div>
                    </div>
                    <div class="bg-slate-900/50 rounded p-2">
                        <div class="text-red-400 font-bold">${totalFailed}</div>
                        <div class="text-xs text-slate-500">Failed</div>
                    </div>
                    <div class="bg-slate-900/50 rounded p-2">
                        <div class="text-blue-400 font-bold">${totalControls}</div>
                        <div class="text-xs text-slate-500">Total</div>
                    </div>
                </div>
            </div>
            
            <!-- Framework Breakdown -->
            <div class="space-y-2">
                ${frameworks.map((framework, index) => {
                    const score = scores[index];
                    const data = compliance[framework];
                    const grade = score >= 90 ? 'A+' : score >= 80 ? 'A' : score >= 70 ? 'B' : score >= 60 ? 'C' : 'F';
                    const gradeColor = score >= 80 ? 'text-green-400' : score >= 60 ? 'text-yellow-400' : 'text-red-400';
                    
                    return `
                        <div class="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-slate-600 transition-colors">
                            <div class="flex items-center space-x-3">
                                <div class="text-sm font-medium text-slate-200">${framework.toUpperCase()}</div>
                                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${gradeColor} bg-slate-800 border border-slate-600">
                                    ${grade}
                                </span>
                            </div>
                            <div class="flex items-center space-x-3">
                                <div class="text-right">
                                    <div class="text-sm font-bold text-white">${score.toFixed(1)}%</div>
                                    <div class="text-xs text-slate-500">${data?.passed_controls || 0}/${(data?.passed_controls || 0) + (data?.failed_controls || 0)} controls</div>
                                </div>
                                <div class="w-16 bg-slate-700 rounded-full h-2">
                                    <div class="h-2 rounded-full transition-all duration-300 ${score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}" 
                                         style="width: ${score}%"></div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
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