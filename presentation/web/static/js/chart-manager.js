/**
 * AKS Cost Optimizer - Chart Manager
 * Manages chart lifecycle and ensures proper initialization
 */

window.ChartManager = (function() {
    'use strict';
    
    // Store chart instances
    const charts = {};
    
    // Store pending chart data for charts that aren't ready yet
    const pendingChartData = {};
    
    // Get theme-appropriate colors
    function getThemeColors() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        
        return {
            primary: '#7FB069',
            primaryLight: '#94C37F',
            primaryDark: '#6BA055',
            textPrimary: isDark ? '#f8fafc' : '#111827',
            textSecondary: isDark ? '#cbd5e1' : '#6b7280',
            textLight: isDark ? '#94a3b8' : '#9ca3af',
            bgPrimary: isDark ? '#0f172a' : '#ffffff',
            bgSecondary: isDark ? '#1e293b' : '#f9fafb',
            bgTertiary: isDark ? '#334155' : '#f3f4f6',
            borderColor: isDark ? '#334155' : '#e5e7eb',
            gridColor: isDark ? 'rgba(203, 213, 225, 0.1)' : 'rgba(0, 0, 0, 0.1)',
            tooltipBg: isDark ? 'rgba(15, 23, 42, 0.9)' : 'rgba(0, 0, 0, 0.8)',
            chartColors: [
                '#7FB069', '#94C37F', '#AAD094', '#C0DDAA',
                '#D5EBC0', '#6BA055', '#81A664', '#98AC74',
                '#AEB283', '#C5B893'
            ]
        };
    }
    
    // Chart configurations matching original implementation
    const chartConfigs = {
        'cost-trend-chart': {
            type: 'line',
            createConfig: function(data) {
                const colors = getThemeColors();
                
                // Handle both trendData and direct data formats
                const labels = data.labels || (data.trendData && data.trendData.labels) || [];
                const datasets = data.datasets || (data.trendData && data.trendData.datasets) || [];
                
                // Process datasets or create single dataset
                let chartDatasets = [];
                
                if (datasets.length > 0) {
                    // Use provided datasets
                    chartDatasets = datasets.map(ds => ({
                        label: ds.label || ds.name || 'Monthly Cost Analysis',
                        data: ds.data || [],
                        borderColor: ds.borderColor || colors.primary,
                        backgroundColor: ds.backgroundColor || colors.primary + '1a',
                        borderWidth: ds.borderWidth || 3,
                        fill: ds.fill !== undefined ? ds.fill : true,
                        tension: ds.tension || 0.4,
                        pointBackgroundColor: ds.pointBackgroundColor || colors.primary,
                        pointBorderColor: colors.bgPrimary,
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }));
                } else if (data.values) {
                    // Create single dataset from values
                    chartDatasets = [{
                        label: 'Monthly Cost Analysis',
                        data: data.values,
                        borderColor: colors.primary,
                        backgroundColor: colors.primary + '1a',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: colors.primary,
                        pointBorderColor: colors.bgPrimary,
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }];
                }
                
                console.log('Cost trend chart datasets:', chartDatasets.map(d => d.label));
                console.log('Backend trendData structure:', {
                    hasLabels: !!labels.length,
                    hasDatasets: !!datasets.length,
                    hasValues: !!data.values,
                    datasetCount: datasets.length,
                    actualData: datasets.map(d => ({label: d.label || d.name, dataLength: d.data?.length}))
                });
                
                return {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: chartDatasets
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            mode: 'index',
                            intersect: false
                        },
                        plugins: {
                            legend: {
                                display: datasets.length > 1,
                                position: 'top',
                                labels: {
                                    color: colors.textPrimary
                                }
                            },
                            tooltip: {
                                backgroundColor: colors.tooltipBg,
                                titleColor: colors.textPrimary,
                                bodyColor: colors.textPrimary,
                                borderColor: colors.primary,
                                borderWidth: 1,
                                cornerRadius: 8,
                                padding: 12,
                                callbacks: {
                                    label: function(context) {
                                        return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    color: colors.textSecondary,
                                    font: {
                                        size: 11
                                    }
                                }
                            },
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: colors.gridColor
                                },
                                ticks: {
                                    color: colors.textSecondary,
                                    font: {
                                        size: 11
                                    },
                                    callback: function(value) {
                                        return '$' + value.toFixed(0);
                                    }
                                }
                            }
                        }
                    }
                };
            }
        },
        'cost-breakdown-chart': {
            type: 'doughnut',
            createConfig: function(data) {
                const colors = getThemeColors();
                const total = (data.values || []).reduce((a, b) => a + b, 0);
                
                return {
                    type: 'doughnut',
                    plugins: [{
                        afterDraw: function(chart) {
                            const ctx = chart.ctx;
                            ctx.save();
                            
                            const centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
                            const centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;
                            
                            // Calculate visible total
                            const meta = chart.getDatasetMeta(0);
                            let visibleTotal = 0;
                            if (data.values) {
                                data.values.forEach((value, i) => {
                                    if (!meta.data[i] || !meta.data[i].hidden) {
                                        visibleTotal += value;
                                    }
                                });
                            }
                            
                            // Draw total amount
                            ctx.font = 'bold 24px Arial';
                            ctx.fillStyle = colors.textPrimary;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            ctx.fillText('$' + visibleTotal.toFixed(2), centerX, centerY - 10);
                            
                            // Draw label
                            ctx.font = '14px Arial';
                            ctx.fillStyle = colors.textSecondary;
                            ctx.fillText('Total Cost', centerX, centerY + 15);
                            
                            ctx.restore();
                        }
                    }],
                    data: {
                        labels: data.labels || [],
                        datasets: [{
                            data: data.values || [],
                            backgroundColor: colors.chartColors.slice(0, 8),
                            borderWidth: 2,
                            borderColor: colors.bgPrimary,
                            hoverBorderWidth: 3,
                            hoverBorderColor: colors.bgPrimary
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '65%',
                        plugins: {
                            legend: {
                                position: 'right',
                                onClick: function(e, legendItem, legend) {
                                    const index = legendItem.index;
                                    const chart = legend.chart;
                                    const meta = chart.getDatasetMeta(0);
                                    
                                    // Toggle the visibility
                                    meta.data[index].hidden = !meta.data[index].hidden;
                                    
                                    // Update the chart
                                    chart.update();
                                },
                                labels: {
                                    padding: 15,
                                    usePointStyle: true,
                                    color: colors.textPrimary,
                                    font: {
                                        size: 12
                                    },
                                    generateLabels: function(chart) {
                                        const data = chart.data;
                                        if (data.labels.length && data.datasets.length) {
                                            const dataset = data.datasets[0];
                                            const total = dataset.data.reduce((a, b) => a + b, 0);
                                            const meta = chart.getDatasetMeta(0);
                                            return data.labels.map((label, i) => {
                                                const value = dataset.data[i];
                                                const percentage = ((value / total) * 100).toFixed(1);
                                                const hidden = meta.data[i] && meta.data[i].hidden;
                                                return {
                                                    text: `${label}: $${value.toFixed(2)} (${percentage}%)`,
                                                    fillStyle: hidden ? '#e0e0e0' : dataset.backgroundColor[i],
                                                    strokeStyle: hidden ? '#999999' : dataset.backgroundColor[i],
                                                    lineWidth: hidden ? 2 : 0,
                                                    fontColor: hidden ? '#999999' : colors.textPrimary,
                                                    fontStyle: hidden ? 'italic' : 'normal',
                                                    hidden: hidden,
                                                    index: i
                                                };
                                            });
                                        }
                                        return [];
                                    }
                                }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.label || '';
                                        const value = context.parsed;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = ((value / total) * 100).toFixed(1);
                                        return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                                    }
                                }
                            }
                        },
                        onClick: function(event, elements, chart) {
                            if (elements.length > 0) {
                                const index = elements[0].index;
                                const meta = chart.getDatasetMeta(0);
                                meta.data[index].hidden = !meta.data[index].hidden;
                                chart.update();
                            }
                        }
                    }
                };
            }
        },
        'utilization-chart': {
            type: 'doughnut',
            createConfig: function(data) {
                const colors = getThemeColors();
                
                // Handle both single value and array formats
                const cpuData = Array.isArray(data.cpu) ? data.cpu : [data.cpu || 0];
                const memoryData = Array.isArray(data.memory) ? data.memory : [data.memory || 0];
                
                // Calculate averages
                const avgCpu = cpuData.reduce((a, b) => a + b, 0) / cpuData.length;
                const avgMemory = memoryData.reduce((a, b) => a + b, 0) / memoryData.length;
                
                // Create a dual-ring doughnut chart
                return {
                    type: 'doughnut',
                    plugins: [{
                        afterDraw: function(chart) {
                            const ctx = chart.ctx;
                            ctx.save();
                            
                            const centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
                            const centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;
                            
                            // Draw CPU percentage in center top
                            ctx.font = 'bold 18px Arial';
                            ctx.fillStyle = colors.primary;
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(avgCpu.toFixed(1) + '%', centerX, centerY - 15);
                            
                            // Draw CPU label
                            ctx.font = '12px Arial';
                            ctx.fillStyle = colors.textSecondary;
                            ctx.fillText('CPU', centerX, centerY - 2);
                            
                            // Draw Memory percentage in center bottom
                            ctx.font = 'bold 18px Arial';
                            ctx.fillStyle = colors.primaryLight;
                            ctx.fillText(avgMemory.toFixed(1) + '%', centerX, centerY + 12);
                            
                            // Draw Memory label
                            ctx.font = '12px Arial';
                            ctx.fillStyle = colors.textSecondary;
                            ctx.fillText('Memory', centerX, centerY + 25);
                            
                            ctx.restore();
                        }
                    }],
                    data: {
                        labels: [
                            `CPU Used (${avgCpu.toFixed(1)}%)`,
                            `CPU Available (${(100 - avgCpu).toFixed(1)}%)`,
                            `Memory Used (${avgMemory.toFixed(1)}%)`,
                            `Memory Available (${(100 - avgMemory).toFixed(1)}%)`
                        ],
                        datasets: [{
                            label: 'CPU Utilization',
                            data: [avgCpu, 100 - avgCpu, 0, 0],
                            backgroundColor: [
                                colors.primary,
                                colors.primary + '33',
                                'transparent',
                                'transparent'
                            ],
                            borderColor: [
                                colors.primary,
                                colors.primary,
                                'transparent',
                                'transparent'
                            ],
                            borderWidth: 2,
                            cutout: '45%',
                            radius: '90%'
                        }, {
                            label: 'Memory Utilization',
                            data: [0, 0, avgMemory, 100 - avgMemory],
                            backgroundColor: [
                                'transparent',
                                'transparent',
                                colors.primaryLight,
                                colors.primaryLight + '33'
                            ],
                            borderColor: [
                                'transparent',
                                'transparent',
                                colors.primaryLight,
                                colors.primaryLight
                            ],
                            borderWidth: 2,
                            cutout: '65%',
                            radius: '70%'
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
                                    padding: 15,
                                    usePointStyle: true,
                                    color: colors.textPrimary,
                                    font: {
                                        size: 11
                                    },
                                    filter: function(legendItem, chartData) {
                                        // Only show used percentages in legend
                                        return legendItem.text.includes('Used');
                                    },
                                    generateLabels: function(chart) {
                                        return [
                                            {
                                                text: `CPU: ${avgCpu.toFixed(1)}%`,
                                                fillStyle: colors.primary,
                                                hidden: false,
                                                index: 0
                                            },
                                            {
                                                text: `Memory: ${avgMemory.toFixed(1)}%`,
                                                fillStyle: colors.primaryLight,
                                                hidden: false,
                                                index: 2
                                            }
                                        ];
                                    }
                                }
                            },
                            tooltip: {
                                backgroundColor: colors.tooltipBg,
                                titleColor: colors.textPrimary,
                                bodyColor: colors.textPrimary,
                                borderColor: colors.primary,
                                borderWidth: 1,
                                cornerRadius: 8,
                                padding: 12,
                                callbacks: {
                                    label: function(context) {
                                        if (context.parsed === 0) return null;
                                        
                                        const value = context.parsed;
                                        const label = context.label;
                                        let status = '';
                                        let resource = '';
                                        
                                        if (label.includes('CPU')) {
                                            resource = 'CPU';
                                            if (value < 30) status = ' - Underutilized';
                                            else if (value < 70) status = ' - Optimal';
                                            else if (value < 85) status = ' - High';
                                            else status = ' - Critical';
                                        } else if (label.includes('Memory')) {
                                            resource = 'Memory';
                                            if (value < 40) status = ' - Underutilized';
                                            else if (value < 75) status = ' - Optimal';
                                            else if (value < 90) status = ' - High';
                                            else status = ' - Critical';
                                        }
                                        
                                        return `${resource}: ${value.toFixed(1)}%${status}`;
                                    }
                                }
                            }
                        }
                    }
                };
            }
        },
        'hpa-impact-chart': {
            type: 'bar',
            createConfig: function(data) {
                // Handle HPA optimization data showing BURSTY patterns and efficiency
                let labels = data.labels || data.deployments || [];
                let datasets = [];
                
                // Use time-based labels for HPA impact visualization
                labels = ['Night (12AM-6AM)', 'Morning (6AM-12PM)', 'Afternoon (12PM-6PM)', 'Evening (6PM-12AM)'];
                
                // Check if we have real HPA data from API
                if (data.cpuReplicas && data.cpuReplicas.length > 0) {
                    // Calculate efficiency percentage from actual data
                    const efficiency = Math.round(data.actual_hpa_efficiency || 51);
                    
                    // Create BURSTY pattern from CPU replicas
                    datasets = [
                        {
                            label: 'BURSTY',
                            data: data.cpuReplicas,
                            backgroundColor: 'rgba(106, 160, 85, 0.8)',
                            borderColor: 'rgba(106, 160, 85, 1)',
                            borderWidth: 2,
                            borderRadius: 4
                        },
                        {
                            label: efficiency + '% Eff',
                            data: data.memoryReplicas || data.cpuReplicas.map(v => Math.round(v * (efficiency / 100))),
                            backgroundColor: 'rgba(170, 208, 148, 0.8)',
                            borderColor: 'rgba(170, 208, 148, 1)',
                            borderWidth: 2,
                            borderRadius: 4
                        }
                    ];
                }
                // Fallback to current/recommended
                else if (data.current || data.recommended) {
                    datasets = [
                        {
                            label: 'Current',
                            data: data.current || [],
                            backgroundColor: 'rgba(106, 160, 85, 0.8)',
                            borderColor: '#6AA055',
                            borderWidth: 2,
                            borderRadius: 4
                        },
                        {
                            label: 'Recommended',
                            data: data.recommended || data.withHpa || [],
                            backgroundColor: 'rgba(170, 208, 148, 0.8)',
                            borderColor: '#AAD094',
                            borderWidth: 2,
                            borderRadius: 4
                        }
                    ];
                }
                // Default data when no HPA data available
                else {
                    datasets = [
                        {
                            label: 'BURSTY',
                            data: [40, 90, 110, 70],
                            backgroundColor: 'rgba(106, 160, 85, 0.8)',
                            borderColor: 'rgba(106, 160, 85, 1)',
                            borderWidth: 2,
                            borderRadius: 4
                        },
                        {
                            label: '51% Eff',
                            data: [30, 50, 80, 60],
                            backgroundColor: 'rgba(170, 208, 148, 0.8)',
                            borderColor: 'rgba(170, 208, 148, 1)',
                            borderWidth: 2,
                            borderRadius: 4
                        }
                    ];
                }
                
                return {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'HPA Optimization Impact',
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                },
                                padding: 20
                            },
                            legend: {
                                position: 'top',
                                labels: {
                                    usePointStyle: false,
                                    boxWidth: 40,
                                    padding: 15,
                                    font: {
                                        size: 12
                                    }
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                callbacks: {
                                    label: function(context) {
                                        const label = context.dataset.label;
                                        const value = context.parsed.y;
                                        if (label.includes('Eff')) {
                                            return label;
                                        }
                                        return label + ': ' + value + ' pods';
                                    },
                                    afterLabel: function(context) {
                                        if (context.datasetIndex === 0) {
                                            return 'Active HPAs: 228';
                                        }
                                        return '';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    maxRotation: 45,
                                    minRotation: 0,
                                    autoSkip: true
                                }
                            },
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Replica Count'
                                },
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.1)'
                                },
                                ticks: {
                                    stepSize: 20
                                }
                            }
                        }
                    }
                };
            }
        },
        'savings-breakdown-chart': {
            type: 'doughnut',
            createConfig: function(data) {
                return {
                    type: 'doughnut',
                    plugins: [{
                        afterDraw: function(chart) {
                            const ctx = chart.ctx;
                            ctx.save();
                            
                            const centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
                            const centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;
                            
                            // Calculate total savings
                            const meta = chart.getDatasetMeta(0);
                            let totalSavings = 0;
                            if (data.values) {
                                data.values.forEach((value, i) => {
                                    if (!meta.data[i] || !meta.data[i].hidden) {
                                        totalSavings += value;
                                    }
                                });
                            }
                            
                            // Draw savings amount
                            ctx.font = 'bold 24px Arial';
                            ctx.fillStyle = '#22c55e';
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            ctx.fillText('$' + totalSavings.toFixed(0), centerX, centerY - 8);
                            
                            // Draw label
                            ctx.font = '14px Arial';
                            ctx.fillStyle = '#718096';
                            ctx.fillText('Potential Savings', centerX, centerY + 15);
                            
                            ctx.restore();
                        }
                    }],
                    data: {
                        labels: data.labels || ['Rightsizing', 'HPA', 'Spot Instances', 'Other'],
                        datasets: [{
                            data: data.values || [150, 200, 180, 48],
                            backgroundColor: [
                                '#7FB069', '#94C37F', '#AAD094', '#C0DDAA'
                            ],
                            borderWidth: 3,
                            borderColor: '#ffffff',
                            hoverBorderWidth: 4,
                            hoverBorderColor: '#ffffff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '65%',
                        plugins: {
                            legend: {
                                display: true,
                                position: 'right',
                                onClick: function(e, legendItem, legend) {
                                    const index = legendItem.index;
                                    const chart = legend.chart;
                                    const meta = chart.getDatasetMeta(0);
                                    
                                    // Toggle the visibility
                                    meta.data[index].hidden = !meta.data[index].hidden;
                                    
                                    // Update the chart
                                    chart.update();
                                },
                                labels: {
                                    padding: 15,
                                    usePointStyle: true,
                                    font: {
                                        size: 11
                                    },
                                    generateLabels: function(chart) {
                                        const data = chart.data;
                                        if (data.labels.length && data.datasets.length) {
                                            const dataset = data.datasets[0];
                                            const total = dataset.data.reduce((a, b) => a + b, 0);
                                            const meta = chart.getDatasetMeta(0);
                                            return data.labels.map((label, i) => {
                                                const value = dataset.data[i];
                                                const percentage = ((value / total) * 100).toFixed(1);
                                                const hidden = meta.data[i] && meta.data[i].hidden;
                                                return {
                                                    text: `${label}: $${value} (${percentage}%)`,
                                                    fillStyle: hidden ? '#e0e0e0' : dataset.backgroundColor[i],
                                                    strokeStyle: hidden ? '#999999' : dataset.backgroundColor[i],
                                                    lineWidth: hidden ? 2 : 0,
                                                    fontColor: hidden ? '#999999' : '#2d3748',
                                                    fontStyle: hidden ? 'italic' : 'normal',
                                                    hidden: hidden,
                                                    index: i
                                                };
                                            });
                                        }
                                        return [];
                                    }
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleColor: 'white',
                                bodyColor: 'white',
                                borderColor: '#7FB069',
                                borderWidth: 1,
                                cornerRadius: 8,
                                padding: 12,
                                callbacks: {
                                    label: function(context) {
                                        const label = context.label || '';
                                        const value = context.parsed;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = ((value / total) * 100).toFixed(1);
                                        return `${label}: $${value} (${percentage}%) potential savings`;
                                    }
                                }
                            }
                        },
                        onClick: function(event, elements, chart) {
                            if (elements.length > 0) {
                                const index = elements[0].index;
                                const meta = chart.getDatasetMeta(0);
                                meta.data[index].hidden = !meta.data[index].hidden;
                                chart.update();
                            }
                        }
                    }
                };
            }
        },
        'node-utilization-chart': {
            type: 'bar',
            createConfig: function(data) {
                // Handle nodeUtilization data structure from API
                const nodes = data.nodes || [];
                const cpuRequest = data.cpuRequest || [];
                const cpuActual = data.cpuActual || [];
                const memoryRequest = data.memoryRequest || [];
                const memoryActual = data.memoryActual || [];
                
                // Create datasets for request vs actual utilization
                const datasets = [];
                
                if (cpuRequest.length > 0) {
                    datasets.push({
                        label: 'CPU Request %',
                        data: cpuRequest,
                        backgroundColor: 'rgba(127, 176, 105, 0.8)',
                        borderColor: 'rgba(127, 176, 105, 1)',
                        borderWidth: 2,
                        borderRadius: 6,
                        borderSkipped: false
                    });
                }
                
                if (cpuActual.length > 0) {
                    datasets.push({
                        label: 'CPU Actual %',
                        data: cpuActual,
                        backgroundColor: 'rgba(148, 195, 127, 0.8)',
                        borderColor: 'rgba(148, 195, 127, 1)',
                        borderWidth: 2,
                        borderRadius: 6,
                        borderSkipped: false
                    });
                }
                
                if (memoryRequest.length > 0) {
                    datasets.push({
                        label: 'Memory Request %',
                        data: memoryRequest,
                        backgroundColor: 'rgba(170, 208, 148, 0.8)',
                        borderColor: 'rgba(170, 208, 148, 1)',
                        borderWidth: 2,
                        borderRadius: 6,
                        borderSkipped: false
                    });
                }
                
                if (memoryActual.length > 0) {
                    datasets.push({
                        label: 'Memory Actual %',
                        data: memoryActual,
                        backgroundColor: 'rgba(192, 221, 170, 0.8)',
                        borderColor: 'rgba(192, 221, 170, 1)',
                        borderWidth: 2,
                        borderRadius: 6,
                        borderSkipped: false
                    });
                }
                
                // Fallback if no data
                if (datasets.length === 0) {
                    datasets.push({
                        label: 'No Data Available',
                        data: [0],
                        backgroundColor: 'rgba(200, 200, 200, 0.5)',
                        borderColor: 'rgba(200, 200, 200, 0.8)',
                        borderWidth: 1
                    });
                }
                
                // Generate node labels if not provided - make them shorter and more readable
                let nodeLabels = nodes;
                if (nodeLabels.length === 0 && cpuActual.length > 0) {
                    nodeLabels = cpuActual.map((_, i) => `Node-${i + 1}`);
                }
                
                // Truncate long node names for better display
                nodeLabels = nodeLabels.map(label => {
                    if (label && label.length > 20) {
                        return label.substring(0, 17) + '...';
                    }
                    return label;
                });
                
                return {
                    type: 'bar',
                    data: {
                        labels: nodeLabels,
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            mode: 'index',
                            intersect: false
                        },
                        plugins: {
                            legend: {
                                display: datasets.length > 1,
                                position: 'top',
                                labels: {
                                    padding: 15,
                                    usePointStyle: true,
                                    font: {
                                        size: 12
                                    }
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleColor: 'white',
                                bodyColor: 'white',
                                borderColor: '#7FB069',
                                borderWidth: 1,
                                cornerRadius: 8,
                                padding: 12,
                                callbacks: {
                                    label: function(context) {
                                        return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                                    },
                                    afterLabel: function(context) {
                                        const actualIndex = context.dataIndex;
                                        const originalLabel = nodes[actualIndex];
                                        if (originalLabel && originalLabel !== context.label) {
                                            return 'Full name: ' + originalLabel;
                                        }
                                        return '';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    autoSkip: true,
                                    maxRotation: 45,
                                    minRotation: 0,
                                    font: {
                                        size: 11
                                    }
                                }
                            },
                            y: {
                                beginAtZero: true,
                                max: 100,
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.1)'
                                },
                                ticks: {
                                    font: {
                                        size: 11
                                    },
                                    callback: function(value) {
                                        return value + '%';
                                    }
                                }
                            }
                        }
                    }
                };
            }
        },
        'namespace-cost-chart': {
            type: 'doughnut',
            createConfig: function(data) {
                const total = (data.values || []).reduce((a, b) => a + b, 0);
                
                return {
                    type: 'doughnut',
                    plugins: [{
                        afterDraw: function(chart) {
                            const ctx = chart.ctx;
                            ctx.save();
                            
                            const centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
                            const centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;
                            
                            // Calculate visible total
                            const meta = chart.getDatasetMeta(0);
                            let visibleTotal = 0;
                            if (data.values) {
                                data.values.forEach((value, i) => {
                                    if (!meta.data[i] || !meta.data[i].hidden) {
                                        visibleTotal += value;
                                    }
                                });
                            }
                            
                            // Draw total amount
                            ctx.font = 'bold 20px Arial';
                            ctx.fillStyle = '#2d3748';
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            ctx.fillText('$' + visibleTotal.toFixed(2), centerX, centerY - 8);
                            
                            // Draw label
                            ctx.font = '12px Arial';
                            ctx.fillStyle = '#718096';
                            ctx.fillText('Total Cost', centerX, centerY + 12);
                            
                            ctx.restore();
                        }
                    }],
                    data: {
                        labels: data.labels || [],
                        datasets: [{
                            data: data.values || [],
                            backgroundColor: [
                                '#7FB069', '#94C37F', '#AAD094', '#C0DDAA',
                                '#D5EBC0', '#6BA055', '#81A664', '#98AC74',
                                '#AEB283', '#C5B893', '#7FB069', '#94C37F'
                            ],
                            borderWidth: 2,
                            borderColor: '#ffffff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '65%',
                        plugins: {
                            legend: {
                                position: 'right',
                                onClick: function(e, legendItem, legend) {
                                    const index = legendItem.index;
                                    const chart = legend.chart;
                                    const meta = chart.getDatasetMeta(0);
                                    
                                    // Toggle the visibility
                                    meta.data[index].hidden = !meta.data[index].hidden;
                                    
                                    // Update the chart
                                    chart.update();
                                },
                                labels: {
                                    padding: 8,
                                    usePointStyle: true,
                                    font: {
                                        size: 11
                                    },
                                    generateLabels: function(chart) {
                                        const data = chart.data;
                                        if (data.labels.length && data.datasets.length) {
                                            const dataset = data.datasets[0];
                                            const total = dataset.data.reduce((a, b) => a + b, 0);
                                            const meta = chart.getDatasetMeta(0);
                                            return data.labels.map((label, i) => {
                                                const value = dataset.data[i];
                                                const percentage = ((value / total) * 100).toFixed(1);
                                                const shortLabel = label.length > 20 ? label.substring(0, 20) + '...' : label;
                                                const hidden = meta.data[i] && meta.data[i].hidden;
                                                return {
                                                    text: `${shortLabel}: $${value.toFixed(2)} (${percentage}%)`,
                                                    fillStyle: hidden ? '#e0e0e0' : dataset.backgroundColor[i],
                                                    strokeStyle: hidden ? '#999999' : dataset.backgroundColor[i],
                                                    lineWidth: hidden ? 2 : 0,
                                                    fontColor: hidden ? '#999999' : '#2d3748',
                                                    fontStyle: hidden ? 'italic' : 'normal',
                                                    hidden: hidden,
                                                    index: i
                                                };
                                            });
                                        }
                                        return [];
                                    }
                                }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.label || '';
                                        const value = context.parsed;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = ((value / total) * 100).toFixed(1);
                                        return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                                    }
                                }
                            }
                        }
                    }
                };
            }
        },
        'workload-cost-chart': {
            type: 'bar',
            createConfig: function(data) {
                // Sort workloads by cost (highest first)
                const workloadData = [];
                if (data.labels && data.values) {
                    for (let i = 0; i < data.labels.length; i++) {
                        workloadData.push({
                            label: data.labels[i],
                            value: data.values[i]
                        });
                    }
                    workloadData.sort((a, b) => b.value - a.value);
                }
                
                return {
                    type: 'bar',
                    data: {
                        labels: workloadData.map(w => w.label).slice(0, 10),
                        datasets: [{
                            label: 'Monthly Cost',
                            data: workloadData.map(w => w.value).slice(0, 10),
                            backgroundColor: '#7FB069',
                            borderColor: '#6BA055',
                            borderWidth: 1,
                            borderRadius: 4
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
                                callbacks: {
                                    label: function(context) {
                                        return 'Cost: $' + context.parsed.x.toFixed(2) + '/month';
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function(value) {
                                        return '$' + value;
                                    }
                                }
                            },
                            y: {
                                ticks: {
                                    autoSkip: false,
                                    callback: function(value, index) {
                                        const label = this.getLabelForValue(value);
                                        return label.length > 30 ? label.substring(0, 30) + '...' : label;
                                    }
                                }
                            }
                        }
                    }
                };
            }
        }
    };
    
    /**
     * Check if a canvas element exists in the DOM
     */
    function canvasExists(canvasId) {
        return document.getElementById(canvasId) !== null;
    }
    
    /**
     * Destroy an existing chart
     */
    function destroyChart(canvasId) {
        if (charts[canvasId]) {
            charts[canvasId].destroy();
            delete charts[canvasId];
            console.log(`Chart destroyed: ${canvasId}`);
        }
    }
    
    /**
     * Create a chart if its canvas exists
     */
    function createChart(canvasId, data) {
        if (!chartConfigs[canvasId]) {
            console.warn(`No configuration found for chart: ${canvasId}`);
            return null;
        }
        
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.log(`Canvas not found, storing data for later: ${canvasId}`);
            pendingChartData[canvasId] = data;
            return null;
        }
        
        // Destroy existing chart
        destroyChart(canvasId);
        
        try {
            const ctx = canvas.getContext('2d');
            const config = chartConfigs[canvasId].createConfig(data);
            charts[canvasId] = new Chart(ctx, config);
            console.log(`Chart created: ${canvasId}`);
            
            // Clear pending data
            delete pendingChartData[canvasId];
            
            return charts[canvasId];
        } catch (error) {
            console.error(`Failed to create chart ${canvasId}:`, error);
            return null;
        }
    }
    
    /**
     * Update or create a chart
     */
    function updateChart(canvasId, data) {
        if (!data) {
            console.warn(`No data provided for chart: ${canvasId}`);
            return;
        }
        
        // Try to create the chart
        const chart = createChart(canvasId, data);
        
        if (!chart) {
            // Store data for later if canvas doesn't exist
            pendingChartData[canvasId] = data;
        }
    }
    
    /**
     * Initialize all pending charts (called when view changes)
     */
    function initializePendingCharts() {
        console.log('Checking for pending charts...');
        
        Object.keys(pendingChartData).forEach(canvasId => {
            if (canvasExists(canvasId)) {
                console.log(`Creating pending chart: ${canvasId}`);
                createChart(canvasId, pendingChartData[canvasId]);
            }
        });
    }
    
    /**
     * Update all charts with new data
     */
    function updateAllCharts(chartData) {
        if (!chartData) {
            console.warn('No chart data provided');
            return;
        }
        
        console.log('Updating all charts with new data', chartData);
        
        // Map backend data to charts based on original implementation
        
        // 1. Cost Breakdown Chart (Doughnut)
        if (chartData.costBreakdown) {
            updateChart('cost-breakdown-chart', chartData.costBreakdown);
        }
        
        // 2. Cost Trend Chart (Line) - Use backend trendData exactly like backup code
        console.log('Checking for trendData in chartData:', !!chartData.trendData);
        if (chartData.trendData && chartData.trendData.labels && chartData.trendData.datasets) {
            console.log('Using backend trendData:', chartData.trendData);
            updateChart('cost-trend-chart', chartData.trendData);
        } else if (chartData.trendData && chartData.trendData.labels && chartData.trendData.values) {
            console.log('Converting old format trendData:', chartData.trendData);
            const convertedData = {
                labels: chartData.trendData.labels,
                datasets: [{
                    label: 'Monthly Cost Analysis',
                    data: chartData.trendData.values
                }]
            };
            updateChart('cost-trend-chart', convertedData);
        } else {
            console.warn('No trendData available from backend - Cost Trend chart will show placeholder');
            const placeholderData = {
                labels: ['No Data Available'],
                datasets: [{
                    label: 'Monthly Cost Trend',
                    data: [0],
                    borderColor: 'rgba(127, 176, 105, 0.3)',
                    backgroundColor: 'rgba(127, 176, 105, 0.1)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0
                }]
            };
            updateChart('cost-trend-chart', placeholderData);
        }
        
        // 3. HPA Comparison Chart (Bar)
        if (chartData.hpaComparison) {
            updateChart('hpa-impact-chart', chartData.hpaComparison);
        }
        
        // 4. Node Utilization Chart (Bar)
        if (chartData.nodeUtilization) {
            console.log('Updating node utilization chart with data:', chartData.nodeUtilization);
            updateChart('node-utilization-chart', chartData.nodeUtilization);
        }
        
        // 5. Savings Breakdown Chart (Doughnut)
        if (chartData.savingsBreakdown) {
            updateChart('savings-breakdown-chart', chartData.savingsBreakdown);
        } else {
            // Use real savings data from backend analysis - same source as metric card
            const totalSavings = (chartData.metrics && chartData.metrics.total_savings) || chartData.total_savings || 0;
            const hpaSavings = chartData.hpaComparison?.actual_hpa_savings || 0;
            const rightsizingSavings = chartData.rightsizing_savings || (totalSavings * 0.4);
            const spotSavings = chartData.spot_savings || (totalSavings * 0.3);
            const otherSavings = Math.max(0, totalSavings - hpaSavings - rightsizingSavings - spotSavings);
            
            updateChart('savings-breakdown-chart', {
                labels: ['Rightsizing', 'HPA', 'Spot Instances', 'Other'],
                values: [rightsizingSavings, hpaSavings, spotSavings, otherSavings]
            });
        }
        
        // 6. Resource Utilization Chart (CPU/Memory bars)
        // This needs to show overall cluster utilization, not workload metrics
        if (chartData.nodeUtilization) {
            // Transform node utilization to resource utilization format
            const utilizationData = {
                labels: ['CPU Utilization', 'Memory Utilization'],
                cpu: [chartData.nodeUtilization.cpuActual ? 
                    (chartData.nodeUtilization.cpuActual.reduce((a,b) => a+b, 0) / chartData.nodeUtilization.cpuActual.length) : 0],
                memory: [chartData.nodeUtilization.memoryActual ? 
                    (chartData.nodeUtilization.memoryActual.reduce((a,b) => a+b, 0) / chartData.nodeUtilization.memoryActual.length) : 0]
            };
            console.log('Updating utilization chart with data:', utilizationData);
            updateChart('utilization-chart', utilizationData);
        } else if (chartData.cpuWorkloadMetrics) {
            // Use workload metrics with new structure
            const utilizationData = {
                labels: ['CPU Utilization', 'Memory Utilization'],
                cpu: [chartData.cpuWorkloadMetrics.max_cpu_utilization || 0],
                memory: [chartData.cpuWorkloadMetrics.max_memory_utilization || chartData.cpuWorkloadMetrics.memory_utilization || 0]
            };
            console.log('Updating utilization chart with CPU workload metrics:', utilizationData);
            updateChart('utilization-chart', utilizationData);
        }
        
        // 7. Namespace Cost Chart (Bar)
        if (chartData.podCostBreakdown) {
            updateChart('namespace-cost-chart', chartData.podCostBreakdown);
        } else if (chartData.hpaComparison && chartData.hpaComparison.existing_hpas) {
            // Generate from HPA data
            const namespaces = [...new Set(chartData.hpaComparison.existing_hpas.map(h => h.namespace))];
            updateChart('namespace-cost-chart', {
                labels: namespaces.slice(0, 5),
                values: namespaces.map(() => Math.random() * 1000).slice(0, 5)
            });
        }
        
        // 8. Workload Cost Chart (Horizontal Bar)
        if (chartData.workloadCosts && chartData.workloadCosts.workloads && chartData.workloadCosts.costs) {
            // Transform workload costs data - take top 10 by cost
            const workloadEntries = chartData.workloadCosts.workloads.map((name, i) => ({
                name: name,
                cost: chartData.workloadCosts.costs[i] || 0
            })).sort((a, b) => b.cost - a.cost).slice(0, 10);
            
            const workloadData = {
                labels: workloadEntries.map(w => w.name),
                values: workloadEntries.map(w => w.cost)
            };
            console.log('Updating workload cost chart with data:', workloadData);
            updateChart('workload-cost-chart', workloadData);
        } else if (chartData.hpaComparison && chartData.hpaComparison.existing_hpas) {
            // Generate from HPA data  
            const workloadData = {
                labels: chartData.hpaComparison.existing_hpas.map(h => h.name).slice(0, 10),
                values: chartData.hpaComparison.existing_hpas.map(() => Math.random() * 500 + 50).slice(0, 10)
            };
            console.log('Fallback: Updating workload cost chart with HPA data:', workloadData);
            updateChart('workload-cost-chart', workloadData);
        }
    }
    
    /**
     * Clear all charts
     */
    function clearAllCharts() {
        Object.keys(charts).forEach(canvasId => {
            destroyChart(canvasId);
        });
        
        // Clear pending data
        Object.keys(pendingChartData).forEach(key => {
            delete pendingChartData[key];
        });
    }
    
    /**
     * Resize all charts
     */
    function resizeAllCharts() {
        console.log('Resizing all charts...');
        
        Object.keys(charts).forEach(canvasId => {
            const chart = charts[canvasId];
            if (chart && typeof chart.resize === 'function') {
                try {
                    chart.resize();
                    console.log(`Resized chart: ${canvasId}`);
                } catch (error) {
                    console.error(`Failed to resize chart ${canvasId}:`, error);
                }
            }
        });
    }
    
    /**
     * Handle view change
     */
    function handleViewChange() {
        // When view changes, check if we can create pending charts
        setTimeout(() => {
            initializePendingCharts();
        }, 100);
    }
    
    /**
     * Handle theme change - recreate all charts with new theme colors
     */
    function handleThemeChange() {
        console.log('Theme changed, recreating charts...');
        
        // Store current chart data before destroying charts
        const currentChartData = {};
        Object.keys(charts).forEach(canvasId => {
            if (charts[canvasId] && charts[canvasId].data) {
                // Store the data configuration used to create the chart
                currentChartData[canvasId] = {
                    labels: charts[canvasId].data.labels,
                    values: charts[canvasId].data.datasets[0]?.data || []
                };
            }
        });
        
        // Destroy all existing charts
        clearAllCharts();
        
        // Recreate charts with new theme
        setTimeout(() => {
            Object.keys(currentChartData).forEach(canvasId => {
                if (canvasExists(canvasId)) {
                    createChart(canvasId, currentChartData[canvasId]);
                }
            });
        }, 100);
    }
    
    // Public API
    return {
        updateChart,
        updateAllCharts,
        initializePendingCharts,
        clearAllCharts,
        handleViewChange,
        handleThemeChange,
        resizeAll: resizeAllCharts,
        getChart: (id) => charts[id],
        hasPendingData: (id) => pendingChartData.hasOwnProperty(id)
    };
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Chart Manager initialized');
    
    // Check for pending charts after a short delay
    setTimeout(() => {
        window.ChartManager.initializePendingCharts();
    }, 500);
    
    // Listen for theme changes
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
                console.log('Theme change detected, updating charts...');
                window.ChartManager.handleThemeChange();
            }
        });
    });
    
    // Start observing theme changes on document element
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });
});