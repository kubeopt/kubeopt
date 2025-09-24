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
        console.log('  - Alerts:', alerts.length);
        console.log('  - Compliance frameworks:', Object.keys(compliance).length);
        console.log('  - Security score:', posture.overall_score);
        
        // Debug cluster-specific data
        const clusterId = window.currentClusterState?.clusterId || 'unknown';
        console.log('🏷️ Current cluster:', clusterId);
        
        // Sample a few items to check data structure
        if (violations.length > 0) {
            console.log('📋 Sample violation:', violations[0]);
        }
        if (alerts.length > 0) {
            console.log('🚨 Sample alert:', alerts[0]);
        }

        // Initialize Overview Charts
        this.createSecurityTrendChart(posture);
        this.createRiskDistributionChart(violations, alerts);
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

        // Show all categories (including zeros for complete visualization)
        const allData = Object.entries(counts);
        const labels = allData.map(([category, _]) => category);
        const values = allData.map(([_, count]) => count);
        
        // Dynamic color mapping with enhanced gradients
        const dynamicColors = [
            { bg: 'rgba(248, 113, 113, 0.85)', border: 'rgb(220, 38, 38)', hover: 'rgba(248, 113, 113, 1)' },
            { bg: 'rgba(251, 146, 60, 0.85)', border: 'rgb(234, 88, 12)', hover: 'rgba(251, 146, 60, 1)' },
            { bg: 'rgba(250, 204, 21, 0.85)', border: 'rgb(234, 179, 8)', hover: 'rgba(250, 204, 21, 1)' },
            { bg: 'rgba(74, 222, 128, 0.85)', border: 'rgb(34, 197, 94)', hover: 'rgba(74, 222, 128, 1)' },
            { bg: 'rgba(96, 165, 250, 0.85)', border: 'rgb(59, 130, 246)', hover: 'rgba(96, 165, 250, 1)' },
            { bg: 'rgba(167, 139, 250, 0.85)', border: 'rgb(139, 92, 246)', hover: 'rgba(167, 139, 250, 1)' },
            { bg: 'rgba(244, 114, 182, 0.85)', border: 'rgb(236, 72, 153)', hover: 'rgba(244, 114, 182, 1)' }
        ];

        const backgroundColors = labels.map((_, index) => dynamicColors[index % dynamicColors.length].bg);
        const borderColors = labels.map((_, index) => dynamicColors[index % dynamicColors.length].border);
        const hoverBackgroundColors = labels.map((_, index) => dynamicColors[index % dynamicColors.length].hover);

        const totalCount = values.reduce((a, b) => a + b, 0);

        const config = {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: backgroundColors,
                    borderColor: 'transparent',
                    hoverBackgroundColor: hoverBackgroundColors,
                    borderWidth: 0,
                    hoverBorderWidth: 0,
                    hoverOffset: 10,
                    borderAlign: 'center'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'point'
                },
                plugins: {
                    legend: { 
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: 'rgb(148, 163, 184)',
                            font: { size: 11, family: 'Poppins', weight: '500' },
                            padding: 12,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            boxWidth: 10,
                            boxHeight: 10
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(148, 163, 184, 0.3)',
                        borderWidth: 1,
                        cornerRadius: 10,
                        displayColors: true,
                        titleFont: { size: 13, weight: 'bold', family: 'Poppins' },
                        bodyFont: { size: 12, family: 'Poppins' },
                        padding: 10,
                        callbacks: {
                            label: function(context) {
                                const percentage = totalCount > 0 ? ((context.parsed / totalCount) * 100).toFixed(1) : 0;
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '58%',
                rotation: -90,
                circumference: 360,
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 1200,
                    easing: 'easeOutQuart',
                    delay: (context) => context.dataIndex * 80
                },
                elements: {
                    arc: {
                        borderWidth: 0,
                        hoverBorderWidth: 0
                    }
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                }
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
                    point: { 
                        radius: 4, 
                        hoverRadius: 8,
                        backgroundColor: 'rgb(96, 165, 250)',
                        borderColor: '#ffffff',
                        borderWidth: 2,
                        hoverBorderWidth: 3
                    },
                    line: {
                        tension: 0.3
                    }
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                }
            }
        };

        window.securityChartInstances['security-trend-chart'] = new Chart(ctx, config);
    }

    createRiskDistributionChart(violations, alerts = []) {
        console.log('🍩 Creating enhanced risk distribution chart with violations:', violations);
        console.log('🚨 Including security alerts:', alerts);
        const canvas = document.getElementById('risk-donut-chart');
        if (!canvas) {
            console.warn('❌ Risk donut chart canvas not found!');
            return;
        }
        
        safeDestroySecurityChart('risk-donut-chart');

        const ctx = canvas.getContext('2d');

        // Combine violations and alerts for total risk calculation
        const allRiskItems = [...(violations || []), ...(alerts || [])];
        console.log('🔍 Combined risk items (violations + alerts):', allRiskItems.length);
        
        // Helper function to get severity level from an item
        const getSeverityLevel = (item) => {
            // Check multiple possible field names and formats
            const severityFields = [
                item.severity,
                item.risk_level, 
                item.level,
                item.priority,
                item.criticality
            ];
            
            for (let field of severityFields) {
                if (field) {
                    const severity = String(field).toLowerCase().trim();
                    // Map different severity variations
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
        
        // Ensure all risk levels are represented (even if zero)
        const riskCounts = {
            Critical: allRiskItems.filter(item => getSeverityLevel(item) === 'critical').length,
            High: allRiskItems.filter(item => getSeverityLevel(item) === 'high').length,
            Medium: allRiskItems.filter(item => getSeverityLevel(item) === 'medium').length,
            Low: allRiskItems.filter(item => getSeverityLevel(item) === 'low').length
        };

        console.log('📊 Enhanced risk counts calculated:', riskCounts);
        
        // Add detailed debugging for each item
        console.group('🔍 Detailed Risk Item Analysis');
        allRiskItems.forEach((item, index) => {
            const rawSeverity = item.severity || item.risk_level || item.level || 'unknown';
            const normalizedSeverity = getSeverityLevel(item);
            const title = item.title || item.policy_name || item.name || 'unnamed';
            console.log(`Item ${index + 1}: "${title}" - Raw: "${rawSeverity}" → Normalized: "${normalizedSeverity}"`);
        });
        console.groupEnd();
        
        // Count unknown/unmapped severity items
        const unknownSeverityItems = allRiskItems.filter(item => getSeverityLevel(item) === 'unknown');
        if (unknownSeverityItems.length > 0) {
            console.warn('⚠️ Items with unknown severity:', unknownSeverityItems.length);
            console.log('Unknown severity items:', unknownSeverityItems.map(item => ({
                title: item.title || item.policy_name || 'unnamed',
                severity: item.severity,
                risk_level: item.risk_level,
                level: item.level,
                priority: item.priority
            })));
        }
        
        // Handle empty data case with better UX
        const totalRisks = Object.values(riskCounts).reduce((a, b) => a + b, 0);
        console.log('🔢 Total risks calculated:', totalRisks, '(from', violations?.length || 0, 'violations +', alerts?.length || 0, 'alerts)');
        console.log('🎯 Individual counts:', Object.entries(riskCounts));
        
        // Debug missing high severity items specifically
        const highSeverityItems = allRiskItems.filter(item => getSeverityLevel(item) === 'high');
        console.log('🚨 High severity items found:', highSeverityItems.length);
        if (highSeverityItems.length > 0) {
            console.log('High severity details:', highSeverityItems.map(item => ({
                title: item.title || item.policy_name || 'unnamed',
                rawSeverity: item.severity || item.risk_level || item.level,
                normalizedSeverity: getSeverityLevel(item),
                source: item.hasOwnProperty('policy_name') ? 'violation' : 'alert'
            })));
        } else {
            console.warn('❌ No high severity items found! Check data structure.');
        }
        if (totalRisks === 0) {
            // Show a "no risks" visualization instead of hiding
            this.showNoRisksVisualization(canvas);
            return;
        }

        // Filter out zero values for better visualization  
        const filteredData = Object.entries(riskCounts)
            .map(([level, count]) => ({ level, count }))
            .filter(item => item.count > 0);
            
        if (filteredData.length === 0) {
            this.showNoRisksVisualization(canvas);
            return;
        }
        
        console.log(`🔧 Processing ${filteredData.length} risk categories:`, filteredData);
        
        // Clean static color palette for risk levels
        const colorMap = {
            'Critical': '#ef4444',    // Clean red
            'High': '#f97316',        // Clean orange  
            'Medium': '#eab308',      // Clean yellow
            'Low': '#22c55e'          // Clean green
        };

        // Generate static colors
        const chartColors = filteredData.map(item => colorMap[item.level]);
        const baseColors = filteredData.map(item => colorMap[item.level]);

        const config = {
            type: 'doughnut',
            plugins: [{
                beforeDraw: function(chart) {
                    const ctx = chart.ctx;
                    ctx.save();
                    // Add subtle shadow
                    ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
                    ctx.shadowBlur = 15;
                    ctx.shadowOffsetX = 3;
                    ctx.shadowOffsetY = 3;
                },
                afterDraw: function(chart) {
                    chart.ctx.restore();
                    
                    // Add center text with total risks
                    const ctx = chart.ctx;
                    ctx.save();
                    const centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
                    const centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;
                    
                    // Calculate visible risks (non-hidden segments)
                    const meta = chart.getDatasetMeta(0);
                    let visibleRisks = 0;
                    filteredData.forEach((item, i) => {
                        if (!meta.data[i].hidden) {
                            visibleRisks += item.count;
                        }
                    });
                    
                    // Draw risk count
                    ctx.font = 'bold 20px Arial';
                    ctx.fillStyle = visibleRisks > 0 ? '#ef4444' : '#22c55e';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(visibleRisks.toString(), centerX, centerY - 8);
                    
                    ctx.font = '13px Arial';
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                    ctx.fillText('Total Risks', centerX, centerY + 12);
                    
                    // Add risk level indicator icon
                    ctx.font = '25px Arial';
                    ctx.fillStyle = 'rgba(239, 68, 68, 0.3)';
                    const riskIcon = visibleRisks > 10 ? '⚠️' : visibleRisks > 5 ? '⚡' : visibleRisks > 0 ? '🔍' : '✅';
                    ctx.fillText(riskIcon, centerX, centerY - 35);
                    
                    ctx.restore();
                }
            }],
            data: {
                labels: filteredData.map(item => item.level),
                datasets: [{
                    data: filteredData.map(item => item.count),
                    backgroundColor: chartColors,
                    borderWidth: 2,
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    hoverOffset: 25,
                    hoverBorderWidth: 3,
                    hoverBorderColor: 'rgba(255, 255, 255, 0.8)',
                    spacing: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'point'
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: 'white',
                            padding: 10,
                            usePointStyle: true,
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            generateLabels: function(chart) {
                                const data = chart.data;
                                if (data.labels.length && data.datasets.length) {
                                    return data.labels.map((label, i) => {
                                        const meta = chart.getDatasetMeta(0);
                                        const value = data.datasets[0].data[i];
                                        const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                        const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                        const isHidden = meta.data[i] && meta.data[i].hidden;
                                        
                                        return {
                                            text: `${label}: ${value} (${percentage}%)`,
                                            fillStyle: isHidden ? 'rgba(150, 150, 150, 0.3)' : baseColors[i],
                                            fontColor: isHidden ? 'rgba(255, 255, 255, 0.3)' : 'white',
                                            textDecoration: isHidden ? 'line-through' : '',
                                            strokeStyle: isHidden ? 'rgba(255, 255, 255, 0.3)' : undefined,
                                            hidden: isHidden,
                                            index: i
                                        };
                                    });
                                }
                                return [];
                            }
                        },
                        onClick: function(e, legendItem, legend) {
                            const index = legendItem.index;
                            const chart = legend.chart;
                            const meta = chart.getDatasetMeta(0);
                            
                            meta.data[index].hidden = !meta.data[index].hidden;
                            chart.update('none');
                        }
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(239, 68, 68, 0.3)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                        displayColors: true,
                        filter: function(tooltipItem) {
                            const meta = tooltipItem.chart.getDatasetMeta(0);
                            return !meta.data[tooltipItem.dataIndex].hidden;
                        },
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${context.label}: ${value} risks (${percentage}%)`;
                            },
                            afterLabel: function(context) {
                                const value = context.parsed;
                                const level = context.label.toLowerCase();
                                if (level === 'critical' && value > 0) {
                                    return '🚨 Immediate attention required!';
                                } else if (level === 'high' && value > 0) {
                                    return '⚠️ High priority issue';
                                } else if (level === 'medium' && value > 2) {
                                    return '📋 Review recommended';
                                }
                                return '';
                            }
                        }
                    }
                },
                cutout: '55%',
                rotation: -90,
                circumference: 360,
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 2200,
                    easing: 'easeInOutCubic',
                    delay: (context) => {
                        return context.dataIndex * 150;
                    }
                },
                transitions: {
                    active: {
                        animation: {
                            duration: 300
                        }
                    },
                    hide: {
                        animation: {
                            duration: 0
                        }
                    },
                    show: {
                        animation: {
                            duration: 0
                        }
                    }
                },
                elements: {
                    arc: {
                        borderWidth: 0,
                        hoverBorderWidth: 0
                    }
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                }
            }
        };

        window.securityChartInstances['risk-donut-chart'] = new Chart(ctx, config);

        // Enhanced risk distribution summary
        this.updateRiskDistributionSummary(riskCounts, totalRisks);
        
        console.log('✅ Enhanced risk distribution chart created successfully with gradients and animations');
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

    // Helper function to add center text to donut charts
    addChartCenterText(chartId, value, label) {
        const chartContainer = document.getElementById(chartId);
        if (!chartContainer) return;

        const parentContainer = chartContainer.parentNode;
        if (!parentContainer) return;

        // Remove existing center text if present
        const existingOverlay = parentContainer.querySelector('.chart-center-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }

        // Create center text overlay
        const overlay = document.createElement('div');
        overlay.className = 'chart-center-overlay';
        overlay.innerHTML = `
            <div class="chart-center-value">${value}</div>
            <div class="chart-center-label">${label}</div>
        `;

        // Ensure parent container has relative positioning
        parentContainer.style.position = 'relative';
        parentContainer.appendChild(overlay);
    }
    
    updateRiskDistributionSummary(riskCounts, totalRisks) {
        const riskContainer = document.getElementById('risk-distribution');
        if (!riskContainer) return;

        // Calculate risk score (weighted)
        const riskScore = (
            (riskCounts.Critical * 10) + 
            (riskCounts.High * 7) + 
            (riskCounts.Medium * 4) + 
            (riskCounts.Low * 1)
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
                    // Show all levels, including zero counts for complete visualization
                    const percentage = totalRisks > 0 ? ((count / totalRisks) * 100).toFixed(1) : '0.0';
                    const colors = {
                        Critical: { text: 'text-red-400', bg: 'bg-red-500' },
                        High: { text: 'text-orange-400', bg: 'bg-orange-500' },
                        Medium: { text: 'text-yellow-400', bg: 'bg-yellow-500' },
                        Low: { text: 'text-green-400', bg: 'bg-green-500' }
                    };
                    const color = colors[level] || { text: 'text-slate-400', bg: 'bg-slate-500' };
                    
                    return `
                        <div class="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-slate-600 transition-colors">
                            <div class="flex items-center space-x-3">
                                <div class="w-3 h-3 ${color.bg} rounded-full"></div>
                                <span class="text-sm font-medium text-slate-200">${level}</span>
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

        // Enhanced dynamic color coding based on compliance scores with gradients
        const getColorForScore = (score) => {
            if (score >= 90) return {
                bg: 'rgba(34, 197, 94, 0.85)',
                border: 'rgb(34, 197, 94)',
                hover: 'rgba(34, 197, 94, 1)',
                gradient: 'linear-gradient(135deg, #22c55e, #16a34a)'
            };
            if (score >= 80) return {
                bg: 'rgba(59, 130, 246, 0.85)',
                border: 'rgb(59, 130, 246)',
                hover: 'rgba(59, 130, 246, 1)',
                gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)'
            };
            if (score >= 70) return {
                bg: 'rgba(251, 146, 60, 0.85)',
                border: 'rgb(251, 146, 60)',
                hover: 'rgba(251, 146, 60, 1)',
                gradient: 'linear-gradient(135deg, #fb923c, #f59e0b)'
            };
            if (score >= 60) return {
                bg: 'rgba(245, 101, 101, 0.85)',
                border: 'rgb(245, 101, 101)',
                hover: 'rgba(245, 101, 101, 1)',
                gradient: 'linear-gradient(135deg, #f56565, #ef4444)'
            };
            return {
                bg: 'rgba(239, 68, 68, 0.85)',
                border: 'rgb(239, 68, 68)',
                hover: 'rgba(239, 68, 68, 1)',
                gradient: 'linear-gradient(135deg, #ef4444, #dc2626)'
            };
        };

        const backgroundColors = scores.map(score => getColorForScore(score).bg);
        const borderColors = scores.map(score => getColorForScore(score).border);
        const hoverBackgroundColors = scores.map(score => getColorForScore(score).hover);

        // Enhanced framework labels with proper casing
        const enhancedLabels = frameworks.map(f => {
            const label = f.toUpperCase();
            return label.length > 8 ? label.substring(0, 8) + '...' : label;
        });

        // Create datasets for different compliance levels for better legend
        const excellentData = scores.map(score => score >= 90 ? score : null);
        const goodData = scores.map(score => score >= 80 && score < 90 ? score : null);
        const fairData = scores.map(score => score >= 70 && score < 80 ? score : null);
        const poorData = scores.map(score => score < 70 ? score : null);

        const config = {
            type: 'bar',
            data: {
                labels: enhancedLabels,
                datasets: [
                    {
                        label: 'Excellent (90-100%)',
                        data: excellentData,
                        backgroundColor: 'rgba(34, 197, 94, 0.85)',
                        borderColor: 'rgb(34, 197, 94)',
                        borderWidth: 2,
                        borderRadius: 6,
                        borderSkipped: false,
                        barThickness: 45,
                        maxBarThickness: 55,
                        hidden: false
                    },
                    {
                        label: 'Good (80-89%)',
                        data: goodData,
                        backgroundColor: 'rgba(59, 130, 246, 0.85)',
                        borderColor: 'rgb(59, 130, 246)',
                        borderWidth: 2,
                        borderRadius: 6,
                        borderSkipped: false,
                        barThickness: 45,
                        maxBarThickness: 55,
                        hidden: false
                    },
                    {
                        label: 'Fair (70-79%)',
                        data: fairData,
                        backgroundColor: 'rgba(251, 146, 60, 0.85)',
                        borderColor: 'rgb(251, 146, 60)',
                        borderWidth: 2,
                        borderRadius: 6,
                        borderSkipped: false,
                        barThickness: 45,
                        maxBarThickness: 55,
                        hidden: false
                    },
                    {
                        label: 'Needs Improvement (<70%)',
                        data: poorData,
                        backgroundColor: 'rgba(239, 68, 68, 0.85)',
                        borderColor: 'rgb(239, 68, 68)',
                        borderWidth: 2,
                        borderRadius: 6,
                        borderSkipped: false,
                        barThickness: 45,
                        maxBarThickness: 55,
                        hidden: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: { 
                        display: true,
                        position: 'top',
                        labels: {
                            color: 'rgb(148, 163, 184)',
                            font: { size: 11, family: 'Poppins', weight: '500' },
                            padding: 12,
                            usePointStyle: true,
                            pointStyle: 'rect',
                            boxWidth: 12,
                            boxHeight: 12,
                            filter: function(legendItem, chartData) {
                                // Only show legend items that have data
                                const dataset = chartData.datasets[legendItem.datasetIndex];
                                return dataset.data.some(value => value !== null && value !== undefined);
                            }
                        },
                        onClick: function(evt, legendItem, legend) {
                            // Enable legend click to toggle datasets
                            const index = legendItem.datasetIndex;
                            const chart = legend.chart;
                            const dataset = chart.data.datasets[index];
                            
                            dataset.hidden = !dataset.hidden;
                            chart.update();
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(148, 163, 184, 0.3)',
                        borderWidth: 1,
                        cornerRadius: 12,
                        displayColors: true,
                        titleFont: { size: 14, weight: 'bold', family: 'Poppins' },
                        bodyFont: { size: 13, family: 'Poppins' },
                        padding: 12,
                        boxPadding: 8,
                        callbacks: {
                            title: function(context) {
                                return `${frameworks[context[0].dataIndex]} Framework`;
                            },
                            label: function(context) {
                                const score = context.parsed.y;
                                if (score === null || score === undefined) return null;
                                
                                const grade = score >= 90 ? 'A+' : score >= 80 ? 'A' : score >= 70 ? 'B' : score >= 60 ? 'C' : 'F';
                                const status = score >= 90 ? 'Excellent' : score >= 80 ? 'Good' : score >= 70 ? 'Fair' : 'Needs Improvement';
                                return [
                                    `${context.dataset.label}`,
                                    `Compliance Score: ${score.toFixed(1)}%`,
                                    `Grade: ${grade} (${status})`,
                                    `Industry Standard: ${score >= 80 ? 'Met' : 'Below Standard'}`
                                ];
                            },
                            afterLabel: function(context) {
                                const score = context.parsed.y;
                                if (score === null || score === undefined) return '';
                                
                                const frameworkData = compliance[frameworks[context.dataIndex]];
                                if (frameworkData) {
                                    const passed = frameworkData.passed_controls || 0;
                                    const failed = frameworkData.failed_controls || 0;
                                    const total = passed + failed;
                                    const passRate = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;
                                    return [
                                        '',
                                        `Controls: ${passed} passed, ${failed} failed`,
                                        `Pass Rate: ${passRate}%`
                                    ];
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
                            drawBorder: false,
                            lineWidth: 1
                        },
                        ticks: { 
                            color: 'rgb(148, 163, 184)', 
                            font: { size: 11, family: 'Poppins', weight: '500' },
                            maxRotation: 45,
                            padding: 8
                        }
                    },
                    y: {
                        grid: { 
                            color: 'rgba(148, 163, 184, 0.1)', 
                            drawBorder: false,
                            lineWidth: 1
                        },
                        ticks: { 
                            color: 'rgb(148, 163, 184)', 
                            font: { size: 11, family: 'Poppins', weight: '500' },
                            padding: 8,
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        beginAtZero: true,
                        max: 100,
                        stepSize: 20
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutCubic',
                    delay: (context) => context.dataIndex * 150
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
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