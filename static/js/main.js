// Global chart instances tracker
let chartInstances = {};

// Form validation function
function validateAnalysisForm() {
    const resourceGroup = document.getElementById('resource_group').value.trim();
    const clusterName = document.getElementById('cluster_name').value.trim();
    
    // Clear any existing validation styles
    document.querySelectorAll('.form-control').forEach(input => {
        input.classList.remove('is-invalid', 'is-valid');
    });
    
    let isValid = true;
    
    // Validate Resource Group
    if (!resourceGroup) {
        document.getElementById('resource_group').classList.add('is-invalid');
        // showToast('❌ Please enter a Resource Group name', 'error');
        isValid = false;
    } else if (resourceGroup.length < 3) {
        document.getElementById('resource_group').classList.add('is-invalid');
        showToast('❌ Resource Group name must be at least 3 characters', 'error');
        isValid = false;
    } else {
        document.getElementById('resource_group').classList.add('is-valid');
    }
    
    // Validate Cluster Name
    if (!clusterName) {
        document.getElementById('cluster_name').classList.add('is-invalid');
        // showToast('❌ Please enter an AKS Cluster name', 'error');
        isValid = false;
    } else if (clusterName.length < 3) {
        document.getElementById('cluster_name').classList.add('is-invalid');
        showToast('❌ Cluster name must be at least 3 characters', 'error');
        isValid = false;
    } else {
        document.getElementById('cluster_name').classList.add('is-valid');
    }
    
    return isValid;
}


// ——— Consolidated DOMContentLoaded Handler ———


// ——— Form Submission Flow ———
// function handleAnalysisSubmit(e) {
//   e.preventDefault();
//   console.log('Form submitted');
//   const btn = document.getElementById('analyzeBtn');
//   const progress = document.getElementById('analysisProgress');
//   const fill = document.getElementById('progressFill');
//   const text = document.getElementById('progressText');
//   btn.classList.add('loading'); btn.disabled = true;
//   progress.classList.add('visible');

//   const steps = [
//     { pct:10, txt:'Connecting to Azure...' },
//     { pct:25, txt:'Fetching cost data...' },
//     { pct:45, txt:'Analyzing cluster metrics...' },
//     { pct:65, txt:'Calculating optimization opportunities...' },
//     { pct:85, txt:'Generating insights...' },
//     { pct:95, txt:'Finalizing analysis...' }
//   ];
//   let idx = 0;
//   (function advance() {
//     if (idx < steps.length) {
//       fill.style.width = steps[idx].pct + '%';
//       text.textContent = steps[idx].txt;
//       idx++;
//       setTimeout(advance, 800);
//     }
//   })();

//   fetch('/analyze', { method:'POST', body:new FormData(e.target) })
//     .then(r => { if(!r.ok) throw new Error(r.statusText); return r.text(); })
//     .then(() => {
//       fill.style.width = '100%';
//       text.textContent = 'Analysis completed successfully!';
//       setTimeout(() => {
//         showToast('🎉 Analysis completed! Found significant optimization opportunities.', 'success');
//         setTimeout(() => { switchToTab('#dashboard'); resetForm(); initializeCharts(); }, 1500);
//       }, 1000);
//     })
//     .catch(err => {
//       console.error(err);
//       showToast('❌ Analysis failed: ' + err.message, 'error');
//       resetForm();
//     });

//   function resetForm() {
//     btn.classList.remove('loading'); btn.disabled = false;
//     progress.classList.remove('visible');
//     fill.style.width = '0%'; text.textContent = 'Initializing analysis...';
//     idx = 0;
//   }
// }

// ——— Tab Switch Handler ———
function onTabSwitch(e) {
    const tgt = e.target.getAttribute('data-bs-target');
    console.log('Tab switched to:', tgt);
    
    // Hide all tab content first
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('show', 'active');
    });
    
    // Show the target tab
    const targetPane = document.querySelector(tgt);
    if (targetPane) {
        setTimeout(() => {
            targetPane.classList.add('show', 'active');
            
            if (tgt === '#dashboard') {
                initializeCharts();
            } else if (tgt === '#implementation') {
                // Always try to load implementation plan when tab is clicked
                loadImplementationPlan();
            } else if (tgt === '#alerts') {
                console.log('Alerts tab activated');
            }
        }, 100);
    }
}

// Also update the loadImplementationPlan function to check for cached data
function loadImplementationPlan() {
    const container = document.getElementById('implementation-plan-container');
    
    // Show loading state
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-muted">Analyzing your cluster to generate personalized implementation recommendations...</p>
        </div>
    `;

    fetch('/api/implementation-plan')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(planData => {
            // Mark that we've successfully loaded data
            if (planData && planData.phases && planData.phases.length > 0) {
                analysisCompleted = true;
            }
            displayImplementationPlan(planData);
            updateQuickStats(planData);
        })
        .catch(error => {
            console.error('Implementation plan loading error:', error);
            displayError(error.message);
        });
}

// ——— Main Chart Init ———
function initializeCharts() {
  console.log('🚀 Initializing charts...');
  fetch('/api/chart-data')
    .then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.statusText}`);
      return r.json();
    })
    .then(data => {
      console.log('📊 Chart data received:', data);
      if (data.status !== 'success') {
        throw new Error(data.message || 'Unexpected response');
      }
      // 1) Update metric cards & badges
      if (data.metrics) updateDashboardMetrics(data.metrics);
      // 2) Build all charts
      createAllCharts(data);
      console.log('✅ Charts initialized successfully');
    })
    .catch(err => {
      console.error('❌ Chart init error:', err);
      showChartError('Unable to load chart data: ' + err.message);
    });
}

// ——— Dashboard Metrics Updater ———
function updateDashboardMetrics(d) {
  console.log('📊 Updating metrics:', d);
  const updates = [
    { sel:['#current-cost'],       val:d.total_cost,        fmt:'currency' },
    { sel:['#potential-savings'],  val:d.total_savings,     fmt:'currency' },
    { sel:['#hpa-efficiency'],     val:d.hpa_reduction,     fmt:'percentage' },
    { sel:['#optimization-score'], val:calculateScore(d),   fmt:'number' },
    { sel:['#savings-percentage'], val:d.savings_percentage,fmt:'percentage' },
    { sel:['#annual-savings'],     val:d.annual_savings,    fmt:'currency' },
    { sel:['#monthly-savings'],    val:d.total_savings,     fmt:'currency' },
    { sel:['#action-savings'],     val:d.total_savings,     fmt:'currency-monthly' }
  ];
  updates.forEach((m,i) => animateMetric(m, i * 100));
  updateCostTrend(d);
  updateDataSourceIndicator(d);
}

function animateMetric(metric, delay) {
  let el = null;
  for (const s of metric.sel) {
    el = document.querySelector(s);
    if (el) break;
  }
  if (!el) return;

  setTimeout(() => {
    el.style.transition = 'all 0.3s'; el.style.opacity = '0.5'; el.style.transform = 'scale(0.9)';
    setTimeout(() => {
      const val = formatValue(metric.val, metric.fmt);
      if (el.closest('.metric-card')) el.textContent = val;
      else el.innerHTML = `<span class="metric-value-main">${val}</span><span class="metric-updated-indicator">●</span>`;
      el.classList.add('metric-updated');
      el.style.opacity='1'; el.style.transform='scale(1)';
      setTimeout(() => { el.style.background='rgba(40,167,69,0.1)'; setTimeout(()=>{ el.style.background=''; el.classList.remove('metric-updated'); },1000); },300);
    },300);
  }, delay);
}

function formatValue(v, fmt) {
    const n = parseFloat(v) || 0;
    switch(fmt) {
        case 'currency':         return '$' + n.toLocaleString(undefined,{minimumFractionDigits:0,maximumFractionDigits:0});
        case 'currency-monthly': return '$' + n.toLocaleString(undefined,{minimumFractionDigits:0,maximumFractionDigits:0}) + '/mo';
        case 'percentage':       return n.toFixed(1) + '%';
        case 'number':           return Math.round(n).toString();
        default:                 return n.toLocaleString();
    }
}

function calculateScore(d) {
  const s_pct = d.savings_percentage||0, h = d.hpa_reduction||0, cpu = d.cpu_gap||0, mem=d.memory_gap||0;
  const s_sc = Math.min(100, s_pct*2), e_sc = Math.min(100, h*1.5), u_sc = Math.max(0, 100 - (cpu+mem)/2);
  return Math.round(s_sc*0.4 + e_sc*0.3 + u_sc*0.3);
}

// ——— Cost Trend Indicator ———
function updateCostTrend(d) {
  document.querySelectorAll('#cost-trend').forEach(el => {
    const pct = d.savings_percentage||0;
    if (pct > 20) el.innerHTML = '<i class="fas fa-arrow-down text-success"></i> High Savings Potential';
    else if (pct > 10) el.innerHTML = '<i class="fas fa-arrow-down text-warning"></i> Moderate Savings';
    else el.innerHTML = '<i class="fas fa-minus text-info"></i> Limited Optimization';
  });
}

// ——— Data Source Badge ———
function updateDataSourceIndicator(d) {
  const isReal = !d.is_sample_data;
  let ind = document.querySelector('#data-source-indicator');
  if (!ind) {
    ind = document.createElement('div');
    ind.id = 'data-source-indicator';
    ind.className = 'data-source-indicator';
    (document.querySelector('#dashboard')||document.body).appendChild(ind);
  }
  ind.innerHTML = `
    <div class="data-source-badge ${isReal?'real-data':'sample-data'}">
      <i class="fas fa-${isReal?'cloud':'flask'}"></i>
      <span>${isReal?'Live Azure Data':'Demo Mode'}</span>
      <small>${d.data_source||''}</small>
    </div>
  `;
}

// ——— Unified Chart Builder ———
function createAllCharts(data) {
    console.log('🎨 Creating all charts...');
    try {
        destroyAllCharts();

        // detect real vs sample
        const md = data.metadata||{};
        const realFlag = md.is_real_data===true || md.force_real_data===true;
        const costNum = parseFloat(md.total_cost_verification?.replace(/[^0-9.]/g,'')||'0');
        const finalReal = realFlag || costNum > 100;

        console.log('Data type:', finalReal ? 'Real' : 'Sample');
        console.log('Creating charts with data:', data);

        if (data.costBreakdown?.values?.length) {
            console.log('Creating cost breakdown chart with data:', data.costBreakdown);
            createCostBreakdownChart(data.costBreakdown, finalReal);
        }
        if (data.hpaComparison) {
            console.log('Creating HPA comparison chart');
            createHPAComparisonChart(data.hpaComparison, finalReal);
        }
        if (data.nodeUtilization) {
            console.log('Creating node utilization chart');
            createNodeUtilizationChart(data.nodeUtilization, finalReal);
        }
        if (data.savingsBreakdown) {
            console.log('Creating savings breakdown chart');
            createSavingsBreakdownChart(data.savingsBreakdown, finalReal);
        }
        if (data.trendData) {
            console.log('Creating main trend chart');
            createMainTrendChart(data.trendData, finalReal);
        }
        if (data.insights) {
            updateInsights(data.insights);
        }
        // NEW: Pod cost charts
        if (data.podCostBreakdown) {
            console.log('Creating namespace cost chart');
            createNamespaceCostChart(data.podCostBreakdown);
            document.getElementById('pod-cost-section').style.display = 'block';
        }
        
        if (data.workloadCosts) {
            console.log('Creating workload cost chart');
            createWorkloadCostChart(data.workloadCosts);
        }
        
        if (data.namespaceDistribution || data.workloadCosts) {
            updatePodCostMetrics(data);
        }
        console.log('✅ All charts created');
    } catch (err) {
        console.error('❌ Error building charts', err);
        showChartError('Failed to render charts: ' + err.message);
    }
}

function destroyAllCharts() {
  const chartIds = [
        'mainTrendChart', 'costBreakdownChart', 'hpaComparisonChart', 
        'nodeUtilizationChart', 'savingsBreakdownChart', 'savingsProjectionChart',
        'namespaceCostChart', 'workloadCostChart'
    ];
  chartIds.forEach(id => {
    const canvas = document.getElementById(id);
    if (canvas && chartInstances[id]) {
      chartInstances[id].destroy();
      delete chartInstances[id];
      console.log(`Destroyed chart: ${id}`);
    }
  });
}

// ——— CHART FUNCTIONS ———

function createCostBreakdownChart(data, isRealData) {
    console.log('📊 Creating cost breakdown chart with data:', data);
    const canvas = document.getElementById('costBreakdownChart');
    if (!canvas) {
        console.warn('Cost breakdown canvas not found');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    // Ensure we have valid data
    const labels = data.labels || [];
    const values = data.values || [];
    
    console.log('Cost breakdown labels:', labels);
    console.log('Cost breakdown values:', values);

    // Filter out zero values and corresponding labels
    const filteredData = labels.map((label, index) => ({
        label: label,
        value: values[index] || 0
    })).filter(item => item.value > 0);

    if (filteredData.length === 0) {
        console.warn('No valid cost data to display');
        canvas.parentElement.innerHTML = '<div class="text-center text-muted p-4">No cost data available</div>';
        return;
    }

    const config = {
        type: 'doughnut',
        data: {
            labels: filteredData.map(item => item.label),
            datasets: [{
                data: filteredData.map(item => item.value),
                backgroundColor: [
                    '#3498db', '#e74c3c', '#f39c12', '#2ecc71',
                    '#9b59b6', '#1abc9c', '#95a5a6'
                ],
                borderWidth: 2,
                borderColor: colors.backgroundColor,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: colors.textColor,
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            // FIXED: Proper number conversion and method call
                            const percentage = total > 0 ? parseFloat(((value / total) * 100).toFixed(1)) : 0;
                            return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };

    chartInstances['costBreakdownChart'] = new Chart(ctx, config);
    console.log('✅ Cost breakdown chart created');
}

function createMainTrendChart(data, isRealData) {
  console.log('📈 Creating main trend chart');
  const canvas = document.getElementById('mainTrendChart');
  if (!canvas) {
    console.warn('Main trend canvas not found');
    return;
  }

  const ctx = canvas.getContext('2d');
  const colors = getChartColors();

  const datasets = (data.datasets || []).map((dataset, index) => ({
    label: dataset.name,
    data: dataset.data,
    borderColor: index === 0 ? '#e74c3c' : '#2ecc71',
    backgroundColor: index === 0 ? 'rgba(231, 76, 60, 0.1)' : 'rgba(46, 204, 113, 0.1)',
    borderWidth: 3,
    fill: true,
    tension: 0.4
  }));

  const config = {
    type: 'line',
    data: {
      labels: data.labels || [],
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: colors.textColor }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`;
            }
          }
        }
      },
      scales: {
        x: {
          ticks: { color: colors.textColor },
          grid: { color: colors.gridColor }
        },
        y: {
          ticks: {
            color: colors.textColor,
            callback: function(value) {
              return '$' + value.toLocaleString();
            }
          },
          grid: { color: colors.gridColor }
        }
      }
    }
  };

  chartInstances['mainTrendChart'] = new Chart(ctx, config);
  console.log('✅ Main trend chart created');
}

function createHPAComparisonChart(data, isRealData) {
  console.log('📊 Creating HPA comparison chart');
  const canvas = document.getElementById('hpaComparisonChart');
  if (!canvas) {
    console.warn('HPA comparison canvas not found');
    return;
  }

  const ctx = canvas.getContext('2d');
  const colors = getChartColors();

  const config = {
    type: 'bar',
    data: {
      labels: data.timePoints || [],
      datasets: [
        {
          label: 'CPU-based HPA',
          data: data.cpuReplicas || [],
          backgroundColor: 'rgba(231, 76, 60, 0.7)',
          borderColor: '#e74c3c',
          borderWidth: 2
        },
        {
          label: 'Memory-based HPA',
          data: data.memoryReplicas || [],
          backgroundColor: 'rgba(46, 204, 113, 0.7)',
          borderColor: '#2ecc71',
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: colors.textColor }
        }
      },
      scales: {
        x: {
          ticks: { color: colors.textColor },
          grid: { color: colors.gridColor }
        },
        y: {
          ticks: { color: colors.textColor },
          grid: { color: colors.gridColor },
          beginAtZero: true,
          title: {
            display: true,
            text: 'Replica Count',
            color: colors.textColor
          }
        }
      }
    }
  };

  chartInstances['hpaComparisonChart'] = new Chart(ctx, config);
  console.log('✅ HPA comparison chart created');
}

function createNodeUtilizationChart(data, isRealData) {
  console.log('🖥️ Creating node utilization chart');
  const canvas = document.getElementById('nodeUtilizationChart');
  if (!canvas) {
    console.warn('Node utilization canvas not found');
    return;
  }

  const ctx = canvas.getContext('2d');
  const colors = getChartColors();

  const config = {
    type: 'bar',
    data: {
      labels: data.nodes || [],
      datasets: [
        {
          label: 'CPU Request',
          data: data.cpuRequest || [],
          backgroundColor: 'rgba(52, 152, 219, 0.3)',
          borderColor: '#3498db',
          borderWidth: 2
        },
        {
          label: 'CPU Actual',
          data: data.cpuActual || [],
          backgroundColor: 'rgba(231, 76, 60, 0.7)',
          borderColor: '#e74c3c',
          borderWidth: 2
        },
        {
          label: 'Memory Request',
          data: data.memoryRequest || [],
          backgroundColor: 'rgba(155, 89, 182, 0.3)',
          borderColor: '#9b59b6',
          borderWidth: 2
        },
        {
          label: 'Memory Actual',
          data: data.memoryActual || [],
          backgroundColor: 'rgba(46, 204, 113, 0.7)',
          borderColor: '#2ecc71',
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: colors.textColor }
        }
      },
      scales: {
        x: {
          ticks: { color: colors.textColor },
          grid: { color: colors.gridColor }
        },
        y: {
          ticks: {
            color: colors.textColor,
            callback: function(value) {
              return value + '%';
            }
          },
          grid: { color: colors.gridColor },
          max: 100,
          title: {
            display: true,
            text: 'Utilization %',
            color: colors.textColor
          }
        }
      }
    }
  };

  chartInstances['nodeUtilizationChart'] = new Chart(ctx, config);
  console.log('✅ Node utilization chart created');
}

function createSavingsBreakdownChart(data, isRealData) {
  console.log('💰 Creating savings breakdown chart');
  const canvas = document.getElementById('savingsBreakdownChart');
  if (!canvas) {
    console.warn('Savings breakdown canvas not found');
    return;
  }

  const ctx = canvas.getContext('2d');
  const colors = getChartColors();

  const config = {
    type: 'pie',
    data: {
      labels: data.categories || [],
      datasets: [{
        data: data.values || [],
        backgroundColor: ['#3498db', '#e74c3c', '#2ecc71'],
        borderWidth: 2,
        borderColor: colors.backgroundColor
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: colors.textColor,
            padding: 10,
            usePointStyle: true
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.label}: $${context.parsed.toLocaleString()}`;
            }
          }
        }
      }
    }
  };

  chartInstances['savingsBreakdownChart'] = new Chart(ctx, config);
  console.log('✅ Savings breakdown chart created');
}

// ——— Insights Updater ———
function updateInsights(ins) {
  console.log('💡 Updating insights');
  const out = [];
  for (const [k,v] of Object.entries(ins)) {
    const title = k.replace(/_/g,' ').replace(/\b\w/g,l=>l.toUpperCase());
    out.push(`<div class="insight-item mb-3"><h6>${title}</h6><p>${v}</p></div>`);
  }
  const container = document.querySelector('#insights-container');
  if (container) {
    container.innerHTML = out.join('');
  }
}

// ——— Error & Toast Utilities ———
function showChartError(msg) {
  console.error('Chart error:', msg);
  ['costBreakdownChart','hpaComparisonChart','nodeUtilizationChart','savingsBreakdownChart','savingsProjectionChart']
    .forEach(id => {
      const c = document.getElementById(id);
      if (!c) return;
      c.parentElement.innerHTML = `
        <div class="text-center text-muted p-4">
          <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
          <p>${msg}</p>
          <button class="btn btn-outline-primary btn-sm" onclick="initializeCharts()">
            <i class="fas fa-redo me-1"></i>Retry
          </button>
        </div>
      `;
    });
}

// function showToast(msg, type) {
//   const t = document.createElement('div');
//   t.className = `toast toast-${type}`;
//   t.innerHTML = `<div class="toast-content">${msg}</div>`;
//   t.style.cssText = `
//     position: ; top: 20px; right: 20px; z-index: 10000;
//     padding: 15px 25px; border-radius: 10px; color: white;
//     font-weight: 600; max-width: 400px; animation: slideIn 0.3s ease;
//     background: ${type === 'success' ? 'linear-gradient(135deg, #11998e, #38ef7d)' : 'linear-gradient(135deg, #ff416c, #ff4757)'};
//   `;
//   document.body.appendChild(t);
//   setTimeout(()=>t.remove(),5000);
// }

// ——— Utility Functions ———
function switchToTab(sel) {
  const btn = document.querySelector(`[data-bs-target="${sel}"]`);
  if (btn) btn.click();
}

function getChartColors() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  return {
    textColor: isDark ? '#f7fafc' : '#2d3748',
    gridColor: isDark ? '#4a5568' : '#e2e8f0',
    backgroundColor: isDark ? '#2d3748' : '#ffffff'
  };
}

// ——— Action Functions ———
function refreshCharts() {
  showToast('Refreshing charts...', 'success');
  initializeCharts();
}

function exportReport() {
  showToast('Export feature coming soon!', 'success');
}

function deployOptimizations() {
  showToast('Deploy feature coming soon!', 'success');
}

function scheduleOptimization() {
  showToast('Schedule feature coming soon!', 'success');
}

// Implementation Plan
// function loadImplementationPlan() {
//   console.log('🚀 Loading dynamic implementation plan...');
//   const container = document.getElementById('recommendations-container');
//   if (!container) {
//     console.error('❌ recommendations-container not found!');
//     return;
//   }

//   // Show loading state
//   container.innerHTML = `
//     <div class="text-center mt-4 mb-4">
//       <div class="spinner-border text-primary" role="status">
//         <span class="visually-hidden">Loading...</span>
//       </div>
//       <p class="mt-3">Analyzing your cluster to generate personalized implementation recommendations...</p>
//     </div>
//   `;

//   // Fetch dynamic implementation plan from your existing API
//   fetch('/api/implementation-plan')
//     .then(response => {
//       console.log('📡 API Response status:', response.status);
//       if (!response.ok) {
//         throw new Error(`HTTP ${response.status}: ${response.statusText}`);
//       }
//       return response.json();
//     })
//     .then(data => {
//       console.log('📋 Implementation plan received:', data);

//       // Handle different response statuses from your API
//       if (data.status === 'no_analysis') {
//         console.log('⚠️ No analysis available');
//         showNoAnalysisMessage(container);
//         return;
//       }

//       if (data.status === 'error') {
//         console.log('❌ Implementation plan error:', data.summary?.message);
//         showImplementationError(container, data.summary?.message || 'Unknown error occurred');
//         return;
//       }

//       // Update the summary with real data from your API structure
//       console.log('📊 Updating summary with:', data.summary);
//       updateImplementationSummary(data.summary);

//       // Render the dynamic phases using your API structure
//       console.log('🏗️ Rendering phases:', data.phases);
//       renderImplementationPhases(container, data);

//       // Update monitoring plan if available
//       if (data.monitoring_plan) {
//         console.log('📈 Updating monitoring plan');
//         updateMonitoringPlan(data.monitoring_plan);
//       }

//       console.log('✅ Implementation plan rendered successfully');
//     })
//     .catch(error => {
//       console.error('❌ Error loading implementation plan:', error);
//       showImplementationError(container, error.message);
//     });
// }

// Enhanced Implementation Plan JavaScript Functions
// This replaces your existing loadImplementationPlan and displayImplementationPlan functions


// start
// function loadImplementationPlan() {
//     const container = document.getElementById('implementation-plan-container');
    
//     // Show loading state
//     container.innerHTML = `
//         <div class="text-center py-5">
//             <div class="spinner-border text-primary mb-3" role="status">
//                 <span class="visually-hidden">Loading...</span>
//             </div>
//             <p class="text-muted">Analyzing your cluster to generate personalized implementation recommendations...</p>
//         </div>
//     `;

//     fetch('/api/implementation-plan')
//         .then(response => {
//             if (!response.ok) {
//                 throw new Error(`HTTP ${response.status}: ${response.statusText}`);
//             }
//             return response.json();
//         })
//         .then(planData => {
//             displayImplementationPlan(planData);
//             updateQuickStats(planData);
//         })
//         .catch(error => {
//             console.error('Implementation plan loading error:', error);
//             displayError(error.message);
//         });
// }

function displayError(message) {
    const container = document.getElementById('implementation-plan-container');
    container.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <h4 class="alert-heading">
                <i class="fas fa-exclamation-triangle"></i> Error Loading Implementation Plan
            </h4>
            <p class="mb-3">${message}</p>
            <hr>
            <div class="d-flex gap-2">
                <button class="btn btn-outline-danger btn-sm" onclick="loadImplementationPlan()">
                    <i class="fas fa-redo"></i> Retry
                </button>
                <button class="btn btn-outline-secondary btn-sm" onclick="location.reload()">
                    <i class="fas fa-refresh"></i> Refresh Page
                </button>
            </div>
        </div>
    `;
}

function displayImplementationPlan(planData) {
    const container = document.getElementById('implementation-plan-container');
    
    if (!planData || !planData.phases || planData.phases.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-info-circle fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">No Implementation Plan Available</h4>
                <p class="text-muted">Run an analysis first to generate your implementation plan</p>
                <button class="btn btn-primary" onclick="window.location.href='#analysis'">
                    <i class="fas fa-chart-bar"></i> Run Analysis
                </button>
            </div>
        `;
        return;
    }

    const summary = planData.summary || {};
    
    // In displayImplementationPlan function, update the summary section
    let html = `
        <div class="card border-0 shadow-lg mb-4" style="background: var(--fresh-gradient);">
            <div class="card-body text-white">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h3 class="card-title mb-3">
                            <i class="fas fa-rocket me-2"></i>Implementation Plan Summary
                        </h3>
                        <div class="mb-3">
                            <strong>Cluster:</strong> ${summary.cluster_name || 'N/A'} 
                            <span class="mx-2">•</span>
                            <strong>Resource Group:</strong> ${summary.resource_group || 'N/A'}
                        </div>
                        <p class="mb-0 opacity-90">
                            This ${summary.total_weeks || 0}-week implementation plan will optimize your AKS cluster 
                            through ${summary.total_phases || 0} carefully planned phases.
                        </p>
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="badge fs-6 px-3 py-2" style="background: rgba(255,255,255,0.2);">
                            <i class="fas fa-shield-alt me-1"></i>
                            ${summary.risk_level || 'Unknown'} Risk
                        </div>
                    </div>
                </div>
                
                <div class="row g-3 mt-3">
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">$${(summary.monthly_savings || 0).toFixed(2)}</div>
                            <small class="opacity-90">Monthly Savings</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">$${(summary.annual_savings || 0).toFixed(2)}</div>
                            <small class="opacity-90">Annual Savings</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">${summary.total_weeks || 0}</div>
                            <small class="opacity-90">Total Weeks</small>
                        </div>
                    </div>
                    <div class="col-6 col-md-3">
                        <div class="text-center p-3 rounded" style="background: rgba(255,255,255,0.15);">
                            <div class="h4 mb-1 text-white">${(summary.complexity_score || 0).toFixed(1)}/10</div>
                            <small class="opacity-90">Complexity</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Render each phase
    planData.phases.forEach((phase, idx) => {
        html += renderPhaseCard(phase, idx + 1);
    });

    // Add additional sections
    if (planData.monitoring_plan) {
        html += renderMonitoringSection(planData.monitoring_plan);
    }

    if (planData.governance_plan) {
        html += renderGovernanceSection(planData.governance_plan);
    }

    if (planData.success_metrics) {
        html += renderSuccessMetricsSection(planData.success_metrics);
    }

    if (planData.contingency_plans) {
        html += renderContingencySection(planData.contingency_plans);
    }

    container.innerHTML = html;
}

// function renderPhaseCard(phase, phaseNumber) {
//     const riskColor = getRiskColor(phase.risk);
//     const phaseColors = [
//         'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
//         'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
//         'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
//         'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
//         'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)'
//     ];
    
//     return `
//         <div class="card border-0 shadow-sm mb-4">
//             <div class="card-header border-0 text-white position-relative" 
//                  style="background: ${phaseColors[(phaseNumber - 1) % phaseColors.length]};">
//                 <div class="position-absolute top-0 end-0 translate-middle">
//                     <div class="badge bg-white text-primary fs-5 rounded-circle p-2" 
//                          style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">
//                         ${phaseNumber}
//                     </div>
//                 </div>
//                 <h5 class="card-title mb-3">${phase.title || `Phase ${phaseNumber}`}</h5>
//                 <div class="d-flex flex-wrap gap-2">
//                     <span class="badge bg-white bg-opacity-25">
//                         <i class="fas fa-clock me-1"></i>${phase.weeks || (phase.duration ? phase.duration + ' weeks' : 'TBD')}
//                     </span>
//                     <span class="badge bg-white bg-opacity-25">
//                         <i class="fas fa-shield-alt me-1"></i>${phase.risk || 'Unknown'} Risk
//                     </span>
//                     <span class="badge bg-success">
//                         <i class="fas fa-dollar-sign me-1"></i>${(phase.savings || 0).to(2)}/month
//                     </span>
//                 </div>
//             </div>
            
//             <div class="card-body">
//                 ${phase.description ? `
//                     <div class="alert alert-light border-start border-4 border-info mb-4">
//                         <i class="fas fa-info-circle me-2 text-info"></i>
//                         ${phase.description}
//                     </div>
//                 ` : ''}
                
//                 ${renderTasksSection(phase.tasks)}
                
//                 <div class="row mt-4">
//                     ${phase.validation ? `
//                         <div class="col-md-6">
//                             ${renderValidationSection(phase.validation)}
//                         </div>
//                     ` : ''}
//                     ${phase.rollback_plan ? `
//                         <div class="col-md-6">
//                             ${renderRollbackSection(phase.rollback_plan)}
//                         </div>
//                     ` : ''}
//                 </div>
//             </div>
//         </div>
//     `;
// }

function renderTasksSection(tasks) {
    if (!tasks || tasks.length === 0) return '';
    
    let html = `
        <h6 class="mb-3"><i class="fas fa-list-check me-2"></i>Implementation Tasks</h6>
        <div class="accordion" id="tasks-accordion-${Date.now()}">
    `;
    
    tasks.forEach((task, idx) => {
        const accordionId = `task-${Date.now()}-${idx}`;
        
        if (typeof task === 'string') {
            html += `
                <div class="accordion-item border">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" 
                                data-bs-toggle="collapse" data-bs-target="#${accordionId}">
                            <i class="fas fa-cog me-2"></i>Task ${idx + 1}
                        </button>
                    </h2>
                    <div id="${accordionId}" class="accordion-collapse collapse">
                        <div class="accordion-body">
                            <p class="mb-0">${task}</p>
                        </div>
                    </div>
                </div>
            `;
        } else if (typeof task === 'object') {
            html += `
                <div class="accordion-item border">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" 
                                data-bs-toggle="collapse" data-bs-target="#${accordionId}">
                            <i class="fas fa-cog me-2"></i>${task.task || `Task ${idx + 1}`}
                        </button>
                    </h2>
                    <div id="${accordionId}" class="accordion-collapse collapse">
                        <div class="accordion-body">
                            ${task.description ? `<p class="text-muted mb-3">${task.description}</p>` : ''}
                            
                            ${task.command ? `
                                <div class="mb-3">
                                    <label class="form-label fw-bold">Command:</label>
                                    <div class="bg-dark text-light p-3 rounded font-monospace">
                                        <code>${task.command}</code>
                                        <button class="btn btn-sm btn-outline-primary position-absolute top-0 end-0 m-2" 
                                                onclick="copyToClipboard('${task.command.replace(/'/g, "\\'")}')">
                                            <i class="fas fa-copy"></i>
                                        </button>
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${task.template ? `
                                <div class="mb-3">
                                    <label class="form-label fw-bold">Template:</label>
                                    <div class="bg-light p-3 rounded">
                                        <pre class="mb-0 font-monospace small">${escapeHtml(task.template)}</pre>
                                        <button class="btn btn-sm btn-outline-primary position-absolute top-0 end-0 m-2" 
                                                onclick="copyToClipboard(\`${task.template.replace(/`/g, '\\`')}\`)">
                                            <i class="fas fa-copy"></i> Copy
                                        </button>
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${task.expected_outcome ? `
                                <div class="alert">
                                    <i class="fas fa-bullseye me-2"></i>
                                    <strong>Expected Outcome:</strong> ${task.expected_outcome}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }
    });
    
    html += `</div>`;
    return html;
}

function renderValidationSection(validation) {
    if (!validation || validation.length === 0) return '';
    
    return `
        <div class="card border-success">
            <div class="card-header bg-success bg-opacity-10 border-success">
                <h6 class="mb-0 text-success">
                    <i class="fas fa-check-circle me-2"></i>Validation Steps
                </h6>
            </div>
            <div class="card-body">
                <ul class="list-group list-group-flush">
                    ${validation.map(step => `
                        <li class="list-group-item border-0 px-0 py-2">
                            <i class="fas fa-check text-success me-2"></i>${step}
                        </li>
                    `).join('')}
                </ul>
            </div>
        </div>
    `;
}

function renderRollbackSection(rollbackPlan) {
    if (!rollbackPlan || typeof rollbackPlan !== 'object') return '';
    
    return `
        <div class="card border-warning">
            <div class="card-header bg-warning bg-opacity-10 border-warning">
                <h6 class="mb-0 text-warning-emphasis">
                    <i class="fas fa-undo me-2"></i>Rollback Plan
                </h6>
            </div>
            <div class="card-body">
                ${rollbackPlan.trigger_conditions ? `
                    <div class="mb-3">
                        <strong class="text-danger">Trigger Conditions:</strong>
                        <ul class="mt-2">
                            ${rollbackPlan.trigger_conditions.map(condition => `
                                <li class="text-danger">${condition}</li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${rollbackPlan.rollback_steps ? `
                    <div class="mb-3">
                        <strong>Rollback Steps:</strong>
                        <ol class="mt-2">
                            ${rollbackPlan.rollback_steps.map(step => `<li>${step}</li>`).join('')}
                        </ol>
                    </div>
                ` : ''}
                
                ${rollbackPlan.recovery_time ? `
                    <div class="alert alert-info mb-0">
                        <i class="fas fa-clock me-2"></i>
                        <strong>Expected Recovery Time:</strong> ${rollbackPlan.recovery_time}
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

function renderMonitoringSection(monitoringPlan) {
    return `
        <div class="card border-0 shadow-sm mt-5">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0">
                    <i class="fas fa-chart-line me-2"></i>Ongoing Monitoring & Optimization
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-4">
                    ${monitoringPlan.daily_checks ? `
                        <div class="col-md-6">
                            <h6 class="text-success">
                                <i class="fas fa-calendar-day me-2"></i>Daily Monitoring
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${monitoringPlan.daily_checks.map(check => `
                                    <li class="list-group-item border-0 px-0">${check}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${monitoringPlan.weekly_reviews ? `
                        <div class="col-md-6">
                            <h6 class="text-primary">
                                <i class="fas fa-calendar-week me-2"></i>Weekly Reviews
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${monitoringPlan.weekly_reviews.map(review => `
                                    <li class="list-group-item border-0 px-0">${review}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${monitoringPlan.monthly_assessments ? `
                        <div class="col-md-6">
                            <h6 class="text-warning">
                                <i class="fas fa-calendar-alt me-2"></i>Monthly Assessments
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${monitoringPlan.monthly_assessments.map(assessment => `
                                    <li class="list-group-item border-0 px-0">${assessment}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${monitoringPlan.automated_alerts ? `
                        <div class="col-md-6">
                            <h6 class="text-danger">
                                <i class="fas fa-exclamation-triangle me-2"></i>Automated Alerts
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${monitoringPlan.automated_alerts.map(alert => `
                                    <li class="list-group-item border-0 px-0">${alert}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderGovernanceSection(governancePlan) {
    return `
        <div class="card border-0 shadow-sm mt-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                    <i class="fas fa-shield-alt me-2"></i>Governance & Control Framework
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-4">
                    ${governancePlan.resource_policies ? `
                        <div class="col-md-4">
                            <h6 class="text-primary">
                                <i class="fas fa-cogs me-2"></i>Resource Policies
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${governancePlan.resource_policies.map(policy => `
                                    <li class="list-group-item border-0 px-0">${policy}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${governancePlan.cost_controls ? `
                        <div class="col-md-4">
                            <h6 class="text-success">
                                <i class="fas fa-dollar-sign me-2"></i>Cost Controls
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${governancePlan.cost_controls.map(control => `
                                    <li class="list-group-item border-0 px-0">${control}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${governancePlan.operational_procedures ? `
                        <div class="col-md-4">
                            <h6 class="text-warning">
                                <i class="fas fa-clipboard-list me-2"></i>Operational Procedures
                            </h6>
                            <ul class="list-group list-group-flush">
                                ${governancePlan.operational_procedures.map(procedure => `
                                    <li class="list-group-item border-0 px-0">${procedure}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderSuccessMetricsSection(successMetrics) {
    return `
        <div class="card border-0 shadow-sm mt-4">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0">
                    <i class="fas fa-bullseye me-2"></i>Success Metrics & KPIs
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-3">
                    ${Object.entries(successMetrics).map(([categoryKey, categoryData]) => {
                        if (!categoryData || typeof categoryData !== 'object') return '';
                        return `
                        <div class="col-md-4">
                            <div class="metric-summary-card">
                                <h6 class="text-info mb-3">
                                    <i class="fas fa-${getCategoryIcon(categoryKey)} me-2"></i>
                                    ${formatCategoryName(categoryKey)}
                                </h6>
                                ${Object.entries(categoryData).slice(0, 3).map(([key, value]) => `
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <span class="small text-muted">${formatMetricName(key)}</span>
                                        <span class="fw-bold text-primary">${value}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        `;
                    }).join('')}
                </div>
            </div>
        </div>
    `;
}

// Add these helper functions
function getCategoryIcon(category) {
    const icons = {
        'cost_metrics': 'dollar-sign',
        'performance_metrics': 'tachometer-alt',
        'operational_metrics': 'cogs'
    };
    return icons[category] || 'chart-bar';
}

function formatCategoryName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatMetricName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function renderContingencySection(contingencyPlans) {
    return `
        <div class="card border-0 shadow-sm mt-4">
            <div class="card-header bg-warning text-dark">
                <h5 class="mb-0">
                    <i class="fas fa-exclamation-triangle me-2"></i>Contingency Plans
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-4">
                    ${Object.entries(contingencyPlans).map(([key, plan]) => `
                        <div class="col-md-4">
                            <div class="card h-100 border-warning">
                                <div class="card-header bg-warning bg-opacity-10">
                                    <h6 class="mb-0 text-capitalize">
                                        ${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                    </h6>
                                </div>
                                <div class="card-body">
                                    <p class="small text-muted mb-2">
                                        <strong>Scenario:</strong> ${plan.scenario}
                                    </p>
                                    <p class="small mb-2">
                                        <strong>Alternative:</strong> ${plan.alternative}
                                    </p>
                                    <div class="alert alert-warning alert-sm mb-0">
                                        <strong>Impact:</strong> ${plan.impact}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

function updateQuickStats(planData) {
    const summary = planData.summary || {};
    
    // Update quick stats if elements exist
    const elements = {
        'total-phases-stat': summary.total_phases || 0,
        'total-weeks-stat': summary.total_weeks || 0,
        'monthly-savings-stat': `${(summary.monthly_savings || 0).toFixed(2)}`,
        'risk-level-stat': summary.risk_level || 'Unknown',
        'annual-savings-impl': `${(summary.annual_savings || 0).toFixed(2)}`
    };

    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });

    // Show quick stats section
    const quickStatsSection = document.getElementById('implementation-quick-stats');
    if (quickStatsSection) {
        quickStatsSection.style.display = 'block';
    }

    // Show implementation tracker
    const tracker = document.getElementById('implementation-tracker');
    if (tracker) {
        tracker.style.display = 'block';
    }
}

// Utility functions
function getRiskColor(risk) {
    const riskColors = {
        'low': '#28a745',
        'medium': '#ffc107',
        'high': '#dc3545'
    };
    return riskColors[(risk || 'unknown').toLowerCase()] || '#6c757d';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

//remove once tested
// function copyToClipboard(text) {
//     navigator.clipboard.writeText(text).then(() => {
//         // Show success toast or notification
//         showToast('Copied to clipboard!', 'success');
//     }).catch(err => {
//         console.error('Failed to copy: ', err);
//         showToast('Failed to copy to clipboard', 'error');
//     });
// }

function showToast(message, type = 'info') {
    // Create and show bootstrap toast
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0" 
             role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check' : 'exclamation-triangle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1080';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
  console.log('Dashboard initializing…');

  // ——— Inject CSS ———
  injectMetricsCSS();

  // ——— Form Submission ———
  const form = document.getElementById('analysisForm');
  if (form) {
    form.addEventListener('submit', handleAnalysisSubmit);
  }

  // ——— Bootstrap Tab Switching ———
  document.querySelectorAll('[data-bs-toggle="tab"]').forEach(btn => {
    btn.addEventListener('shown.bs.tab', onTabSwitch);
  });

  // ——— Auto-init Charts if Dashboard Already Active ———
  if (document.querySelector('#dashboard')?.classList.contains('active')) {
    setTimeout(initializeCharts, 500);
  }

  // ——— Alerts Tab Fix ———
  const alertTab = document.getElementById('alerts-tab');
  if (alertTab) {
    alertTab.addEventListener('click', function(e) {
      console.log('Alert tab clicked');
      new bootstrap.Tab(alertTab).show();
    });
  }

  // ——— Implementation Tab Loader ———
  const implementationTab = document.getElementById('implementation-tab');
  if (implementationTab) {
    implementationTab.addEventListener('click', loadImplementationPlan);
  }
  // If the implementation pane is already active on load, fire it immediately
  if (document.getElementById('implementation')?.classList.contains('active')) {
    loadImplementationPlan();
  }

  //
  // Add input event listeners for real-time validation
    const resourceGroupInput = document.getElementById('resource_group');
    const clusterNameInput = document.getElementById('cluster_name');
    
    if (resourceGroupInput) {
        resourceGroupInput.addEventListener('input', function() {
            if (this.value.trim().length >= 3) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                if (this.value.trim().length > 0) {
                    this.classList.add('is-invalid');
                }
            }
        });
    }
    
    if (clusterNameInput) {
        clusterNameInput.addEventListener('input', function() {
            if (this.value.trim().length >= 3) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                if (this.value.trim().length > 0) {
                    this.classList.add('is-invalid');
                }
            }
        });
    }

    // NEW: Handle pod analysis checkbox
    const podAnalysisCheckbox = document.getElementById('enable_pod_analysis');
    if (podAnalysisCheckbox) {
        podAnalysisCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            console.log('Pod analysis checkbox changed:', isChecked);
            
            // Show/hide info about pod analysis
            const podInfo = document.querySelector('.pod-analysis-info');
            if (podInfo) {
                podInfo.style.display = isChecked ? 'block' : 'none';
            }
            
            // Update form hint
            const formHint = this.parentElement.querySelector('.form-hint');
            if (formHint) {
                if (isChecked) {
                    formHint.textContent = 'Analyze costs at namespace and workload level (adds 30-60 seconds)';
                    formHint.classList.add('text-info');
                } else {
                    formHint.textContent = 'Enable for detailed pod-level cost insights';
                    formHint.classList.remove('text-info');
                }
            }
        });
        
        // Trigger initial state
        podAnalysisCheckbox.dispatchEvent(new Event('change'));
    }
});

/////// END ////

let analysisCompleted = false;

// Update the handleAnalysisSubmit function
function handleAnalysisSubmit(e) {
  e.preventDefault();
  
  // Validate form first
  if (!validateAnalysisForm()) {
    return; // Stop submission if validation fails
  }
  console.log('Form submitted');
  const btn = document.getElementById('analyzeBtn');
  const progress = document.getElementById('analysisProgress');
  const fill = document.getElementById('progressFill');
  const text = document.getElementById('progressText');
  btn.classList.add('loading'); 
  btn.disabled = true;
  progress.classList.add('visible');

  const steps = [
    { pct:10, txt:'Connecting to Azure...' },
    { pct:25, txt:'Fetching cost data...' },
    { pct:45, txt:'Analyzing cluster metrics...' },
    { pct:65, txt:'Calculating optimization opportunities...' },
    { pct:85, txt:'Generating insights...' },
    { pct:95, txt:'Finalizing analysis...' }
  ];
  let idx = 0;
  (function advance() {
    if (idx < steps.length) {
      fill.style.width = steps[idx].pct + '%';
      text.textContent = steps[idx].txt;
      idx++;
      setTimeout(advance, 800);
    }
  })();

  fetch('/analyze', { method:'POST', body:new FormData(e.target) })
    .then(r => { if(!r.ok) throw new Error(r.statusText); return r.text(); })
    .then(() => {
      fill.style.width = '100%';
      text.textContent = 'Analysis completed successfully!';
      analysisCompleted = true; // Set analysis state
      setTimeout(() => {
        showToast('🎉 Analysis completed! Found significant optimization opportunities.', 'success');
        setTimeout(() => { 
          switchToTab('#dashboard'); 
          resetForm(); 
          initializeCharts(); 
        }, 1500);
      }, 1000);
    })
    .catch(err => {
      console.error(err);
      showToast('❌ Analysis failed: ' + err.message, 'error');
      resetForm();
    });

  function resetForm() {
    btn.classList.remove('loading'); 
    btn.disabled = false;
    progress.classList.remove('visible');
    fill.style.width = '0%'; 
    text.textContent = 'Initializing analysis...';
    idx = 0;
  }
}

function updateImplementationSummary(summary) {
  console.log('📊 Updating summary with data:', summary);

  // Update the annual savings in the summary box
  const annualSavingsElement = document.getElementById('annual-savings-impl');
  if (annualSavingsElement) {
    if (summary && summary.annual_savings) {
      annualSavingsElement.textContent = `$${summary.annual_savings.toLocaleString()}`;
      console.log('✅ Updated annual savings to:', summary.annual_savings);
    } else {
      console.log('⚠️ No annual_savings in summary:', summary);
    }
  } else {
    console.log('⚠️ annual-savings-impl element not found');
  }

  // Update quick stats if they exist
  const totalPhasesElement = document.getElementById('total-phases-stat');
  if (totalPhasesElement) {
    totalPhasesElement.textContent = summary?.total_phases || 0;
  }

  const totalWeeksElement = document.getElementById('total-weeks-stat');
  if (totalWeeksElement) {
    totalWeeksElement.textContent = `${summary?.total_weeks || 0} weeks`;
  }

  const monthlySavingsElement = document.getElementById('monthly-savings-stat');
  if (monthlySavingsElement) {
    monthlySavingsElement.textContent = `$${(summary?.monthly_savings || 0).toLocaleString()}`;
  }

  const riskLevelElement = document.getElementById('risk-level-stat');
  if (riskLevelElement) {
    riskLevelElement.textContent = summary?.risk_level || 'Unknown';
  }

  // Show the quick stats row if it exists
  const quickStatsRow = document.getElementById('implementation-quick-stats');
  if (quickStatsRow) {
    quickStatsRow.style.display = 'flex';
  }
}

// THE MISSING FUNCTION - This is what was causing the issue!
function renderImplementationPhases(container, data) {
  console.log('🏗️ Starting to render implementation phases');
  const { phases, summary, monitoring_plan, success_metrics } = data;

  if (!phases || phases.length === 0) {
    console.log('⚠️ No phases found, showing no optimization message');
    container.innerHTML = `
      <div class="text-center mt-4 mb-4">
        <div class="alert alert-info">
          <h5><i class="fas fa-info-circle me-2"></i>No Major Optimizations Needed</h5>
          <p>Your cluster is already well-optimized! Only minor improvements were identified.</p>
          <p><strong>Current Status:</strong> ${summary?.message || 'Analysis complete'}</p>
        </div>
      </div>
    `;
    return;
  }

  console.log(`🏗️ Rendering ${phases.length} phases`);

  let html = `
    <div class="row mb-4">
      <div class="col-12">
        <div class="card bg-primary text-white">
          <div class="card-body">
            <div class="row text-center">
              <div class="col-md-3">
                <h3 class="mb-1">${summary.total_phases}</h3>
                <small>Implementation Phases</small>
              </div>
              <div class="col-md-3">
                <h3 class="mb-1">${summary.total_weeks}</h3>
                <small>Total Weeks</small>
              </div>
              <div class="col-md-3">
                <h3 class="mb-1">$${summary.monthly_savings.toLocaleString()}</h3>
                <small>Monthly Savings</small>
              </div>
              <div class="col-md-3">
                <h3 class="mb-1">${summary.risk_level}</h3>
                <small>Overall Risk</small>
              </div>
            </div>
            ${summary.resource_group && summary.cluster_name ? `
            <div class="row mt-3">
              <div class="col-12 text-center">
                <small><i class="fas fa-server me-1"></i> ${summary.resource_group} / ${summary.cluster_name}</small>
                ${summary.success_probability ? `<span class="ms-3"><i class="fas fa-chart-line me-1"></i> ${summary.success_probability} Success Rate</span>` : ''}
              </div>
            </div>
            ` : ''}
          </div>
        </div>
      </div>
    </div>
  `;

  // Render each phase
  phases.forEach((phase, index) => {
    console.log(`🏗️ Rendering phase ${index + 1}:`, phase.title);
    html += renderPhaseCard(phase, index);
  });

  // Add success metrics if available
  if (success_metrics && Object.keys(success_metrics).length > 0) {
    console.log('🎯 Adding success metrics');
    html += renderSuccessMetrics(success_metrics);
  }

  console.log('🏗️ Setting innerHTML for container');
  container.innerHTML = html;
  console.log('✅ Implementation phases rendered successfully');
}

function renderPhaseCard(phase, index) {
  const riskColorClass = getRiskColorClass(phase.risk);
  const phaseNumber = phase.phase || (index + 1);

  let html = `
    <div class="row mb-4">
      <div class="col-12">
        <div class="card border-0 shadow">
          <div class="card-header ${riskColorClass} text-white">
            <div class="d-flex justify-content-between align-items-center flex-wrap">
              <h6 class="mb-0">
                <i class="fas fa-${getPhaseIcon(phase.title)} me-2"></i>
                Phase ${phaseNumber}: ${phase.title}
              </h6>
              <div class="d-flex gap-2 flex-wrap">
                <span class="badge bg-light text-dark">${phase.weeks}</span>
                <span class="badge bg-light text-dark">$${phase.savings.toLocaleString()}/month</span>
                <span class="badge bg-light text-dark">${phase.risk} Risk</span>
              </div>
            </div>
          </div>
          <div class="card-body">
            <p class="lead mb-4">${phase.description}</p>

            <div class="row">
              <div class="col-lg-8">
                <h6><i class="fas fa-tasks me-2"></i>Implementation Tasks</h6>
                <div class="accordion accordion-flush" id="phase${phaseNumber}Tasks">
  `;

  // Render tasks
  if (phase.tasks && phase.tasks.length > 0) {
    phase.tasks.forEach((task, taskIndex) => {
      const taskId = `task${phaseNumber}_${taskIndex}`;
      html += `
        <div class="accordion-item">
          <h2 class="accordion-header" id="heading_${taskId}">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_${taskId}" aria-expanded="false">
              <div class="w-100">
                <strong>${task.task}</strong>
                ${task.time_estimate ? `<small class="text-muted d-block">Estimated time: ${task.time_estimate}</small>` : ''}
              </div>
            </button>
          </h2>
          <div id="collapse_${taskId}" class="accordion-collapse collapse" data-bs-parent="#phase${phaseNumber}Tasks">
            <div class="accordion-body">
              <p><strong>Description:</strong> ${task.description}</p>
              ${task.command ? `
              <div class="mb-3">
                <strong>Command:</strong>
                <div class="bg-light text-light p-3 rounded mt-2 position-relative">
                  <code>${task.command}</code>
                  <button class="btn btn-sm btn-outline-primary position-absolute top-0 end-0 m-2" onclick="copyToClipboard('${task.command.replace(/'/g, "\\'")}')">
                    <i class="fas fa-copy"></i>
                  </button>
                </div>
              </div>
              ` : ''}
              ${task.template ? `
              <div class="mb-3">
                <strong>YAML Template:</strong>
                <div class="bg-light border rounded mt-2 position-relative" style="max-height: 300px; overflow-y: auto;">
                  <pre class="p-3 mb-0"><code>${task.template}</code></pre>
                  <button class="btn btn-sm btn-outline-primary position-absolute top-0 end-0 m-2" onclick="copyToClipboard(\`${task.template.replace(/`/g, '\\`')}\`)">
                    <i class="fas fa-copy"></i>
                  </button>
                </div>
              </div>
              ` : ''}
              <div class="alert">
                <strong>Expected Outcome:</strong> ${task.expected_outcome}
              </div>
            </div>
          </div>
        </div>
      `;
    });
  }

  html += `
                </div>
              </div>
              <div class="col-lg-4">
                <h6><i class="fas fa-check-circle me-2"></i>Validation Steps</h6>
                <ul class="list-group list-group-flush">
  `;

  // Render validation steps
  if (phase.validation && phase.validation.length > 0) {
    phase.validation.forEach(step => {
      html += `<li class="list-group-item px-0 border-0"><i class="fas fa-check text-success me-2"></i>${step}</li>`;
    });
  }

  html += `
                </ul>

                <div class="mt-4">
                  <h6><i class="fas fa-info-circle me-2"></i>Phase Summary</h6>
                  <div class="card bg-light">
                    <div class="card-body p-3">
                      <div class="row text-center">
                        <div class="col-6">
                          <strong class="text-success">$${phase.savings.toLocaleString()}</strong>
                          <small class="d-block text-muted">Monthly Savings</small>
                        </div>
                        <div class="col-6">
                          <strong class="text-primary">${phase.duration} weeks</strong>
                          <small class="d-block text-muted">Duration</small>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  return html;
}

function updateMonitoringPlan(monitoringPlan) {
  console.log('📈 Updating monitoring plan:', monitoringPlan);
  if (!monitoringPlan || Object.keys(monitoringPlan).length === 0) return;

  // Find the monitoring section and update it
  const monitoringSection = document.querySelector('#monitoring-section .card-body');
  if (monitoringSection) {
    let html = '<div class="row">';

    if (monitoringPlan.daily_checks && monitoringPlan.daily_checks.length > 0) {
      html += `
        <div class="col-md-6">
          <h6><i class="fas fa-calendar-day me-2"></i>Daily Monitoring</h6>
          <ul class="list-group list-group-flush">
      `;
      monitoringPlan.daily_checks.forEach(check => {
        html += `<li class="list-group-item px-0">${check}</li>`;
      });
      html += '</ul></div>';
    }

    if (monitoringPlan.weekly_reviews && monitoringPlan.weekly_reviews.length > 0) {
      html += `
        <div class="col-md-6">
          <h6><i class="fas fa-calendar-week me-2"></i>Weekly Reviews</h6>
          <ul class="list-group list-group-flush">
      `;
      monitoringPlan.weekly_reviews.forEach(review => {
        html += `<li class="list-group-item px-0">${review}</li>`;
      });
      html += '</ul></div>';
    }

    html += '</div>';
    monitoringSection.innerHTML = html;
    console.log('✅ Monitoring plan updated');
  } else {
    console.log('⚠️ Monitoring section not found');
  }
}

function showNoAnalysisMessage(container) {
  container.innerHTML = `
    <div class="text-center mt-4 mb-4">
      <div class="alert alert-warning">
        <h4><i class="fas fa-exclamation-triangle me-2"></i>No Analysis Available</h4>
        <p>Please run a cost analysis first to generate your personalized implementation plan.</p>
        <button class="btn btn-primary" onclick="switchToTab('#analysis')">
          <i class="fas fa-search me-2"></i>Run Analysis
        </button>
      </div>
    </div>
  `;
}

function showImplementationError(container, message) {
  container.innerHTML = `
    <div class="text-center mt-4 mb-4">
      <div class="alert alert-danger">
        <h4><i class="fas fa-exclamation-circle me-2"></i>Error Loading Implementation Plan</h4>
        <p>${message}</p>
        <button class="btn btn-outline-primary" onclick="loadImplementationPlan()">
          <i class="fas fa-redo me-2"></i>Retry
        </button>
      </div>
    </div>
  `;
}

// Helper functions
function getRiskColorClass(risk) {
  switch (risk?.toLowerCase()) {
    case 'high': return 'bg-danger';
    case 'medium': return 'bg-warning';
    case 'low': return 'bg-success';
    default: return 'bg-primary';
  }
}

function getPhaseIcon(title) {
  const titleLower = title.toLowerCase();
  if (titleLower.includes('resource') || titleLower.includes('right-sizing')) return 'cog';
  if (titleLower.includes('hpa') || titleLower.includes('scaling')) return 'expand-arrows-alt';
  if (titleLower.includes('storage')) return 'hdd';
  if (titleLower.includes('optimization')) return 'bullseye';
  return 'rocket';
}

function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast('Copied to clipboard!', 'success');
    }).catch(err => {
      console.error('Failed to copy:', err);
      showToast('Failed to copy to clipboard', 'error');
    });
  } else {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      showToast('Copied to clipboard!', 'success');
    } catch (err) {
      console.error('Failed to copy:', err);
      showToast('Failed to copy to clipboard', 'error');
    }
    document.body.removeChild(textArea);
  }
}

function createNamespaceCostChart(data) {
    console.log('📊 Creating namespace cost chart with data:', data);
    const canvas = document.getElementById('namespaceCostChart');
    if (!canvas || !data || !data.labels || data.labels.length === 0) {
        console.warn('Namespace cost chart data not available or empty');
        // Hide the pod cost section if no data
        const podSection = document.getElementById('pod-cost-section');
        if (podSection) {
            podSection.style.display = 'none';
        }
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    // Generate colors for namespaces
    const namespaceColors = [
        '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
        '#1abc9c', '#95a5a6', '#34495e', '#e67e22', '#16a085'
    ];

    const config = {
        type: 'doughnut',
        data: {
            labels: data.labels || [],
            datasets: [{
                data: data.values || [],
                backgroundColor: namespaceColors,
                borderWidth: 2,
                borderColor: colors.backgroundColor,
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: colors.textColor,
                        padding: 15,
                        usePointStyle: true,
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    // FIXED: Proper number conversion and method call
                                    const percentage = total > 0 ? parseFloat(((value / total) * 100).toFixed(1)) : 0;
                                    return {
                                        text: `${label}: $${value.toLocaleString()} (${percentage}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
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
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            // FIXED: Proper number conversion and method call
                            const percentage = total > 0 ? parseFloat(((value / total) * 100).toFixed(1)) : 0;
                            return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };

    chartInstances['namespaceCostChart'] = new Chart(ctx, config);
    
    // Update analysis badge
    const badge = document.getElementById('pod-analysis-badge');
    if (badge) {
        badge.textContent = `${data.analysis_method || 'Unknown'} - ${data.accuracy_level || 'Unknown'} Accuracy`;
        badge.className = `badge ${getAccuracyBadgeClass(data.accuracy_level)}`;
    }
    
    console.log('✅ Namespace cost chart created');
}

function createWorkloadCostChart(data) {
    console.log('📊 Creating workload cost chart with data:', data);
    const canvas = document.getElementById('workloadCostChart');
    if (!canvas || !data) {
        console.warn('Workload cost chart data not available');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    // Color code by workload type
    const typeColors = {
        'Deployment': '#3498db',
        'StatefulSet': '#e74c3c', 
        'DaemonSet': '#2ecc71',
        'ReplicaSet': '#f39c12',
        'Job': '#9b59b6',
        'CronJob': '#1abc9c'
    };

    const backgroundColors = data.types.map(type => typeColors[type] || '#95a5a6');

    const config = {
        type: 'bar', // CHANGED: from 'horizontalBar' to 'bar'
        data: {
            labels: data.workloads.map(w => w.split('/')[1] || w), // Show only workload name
            datasets: [{
                label: 'Monthly Cost',
                data: data.costs || [],
                backgroundColor: backgroundColors,
                borderColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y', // ADDED: This makes it horizontal in Chart.js v3+
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const index = context[0].dataIndex;
                            return `${data.types[index]}: ${data.workloads[index]}`;
                        },
                        label: function(context) {
                            const index = context.dataIndex;
                            return [
                                `Cost: $${context.parsed.x.toLocaleString()}/month`,
                                `Namespace: ${data.namespaces[index]}`,
                                `Replicas: ${data.replicas[index]}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: colors.textColor,
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: { color: colors.gridColor }
                },
                y: {
                    ticks: { 
                        color: colors.textColor,
                        maxTicksLimit: 15
                    },
                    grid: { color: colors.gridColor }
                }
            }
        }
    };

    chartInstances['workloadCostChart'] = new Chart(ctx, config);
    console.log('✅ Workload cost chart created');
}

function getAccuracyBadgeClass(accuracy) {
    switch (accuracy?.toLowerCase()) {
        case 'very high': return 'bg-success';
        case 'high': return 'bg-info';
        case 'good': return 'bg-warning';
        case 'basic': return 'bg-secondary';
        default: return 'bg-secondary';
    }
}

function updatePodCostMetrics(data) {
    console.log('📊 Updating pod cost metrics with data:', data);
    
    if (!data) {
        console.warn('No data provided to updatePodCostMetrics');
        return;
    }
    
    // Calculate top namespace cost
    let topNamespaceCost = 0;
    if (data.namespaceDistribution && data.namespaceDistribution.costs) {
        topNamespaceCost = Math.max(...data.namespaceDistribution.costs);
    } else if (data.podCostBreakdown && data.podCostBreakdown.values) {
        topNamespaceCost = Math.max(...data.podCostBreakdown.values);
    }
    
    // Get namespace count
    let namespaceCount = 0;
    if (data.namespaceDistribution && data.namespaceDistribution.namespaces) {
        namespaceCount = data.namespaceDistribution.namespaces.length;
    } else if (data.podCostBreakdown && data.podCostBreakdown.labels) {
        namespaceCount = data.podCostBreakdown.labels.length;
    }
    
    // Get workload count
    let workloadCount = 0;
    if (data.workloadCosts && data.workloadCosts.workloads) {
        workloadCount = data.workloadCosts.workloads.length;
    }
    
    // Get analysis accuracy
    let accuracy = 'Unknown';
    if (data.podCostBreakdown && data.podCostBreakdown.accuracy_level) {
        accuracy = data.podCostBreakdown.accuracy_level;
    }
    
    console.log(`Updating metrics: topCost=${topNamespaceCost}, namespaces=${namespaceCount}, workloads=${workloadCount}, accuracy=${accuracy}`);
    
    // Update the metrics
    const updates = [
        { sel: '#top-namespace-cost', val: topNamespaceCost, fmt: 'currency' },
        { sel: '#total-namespaces', val: namespaceCount, fmt: 'number' },
        { sel: '#total-workloads', val: workloadCount, fmt: 'number' },
        { sel: '#analysis-accuracy', val: accuracy, fmt: 'text' }
    ];
    
    updates.forEach(update => {
        const element = document.querySelector(update.sel);
        if (element) {
            let displayValue;
            if (update.fmt === 'currency') {
                displayValue = '$' + (update.val || 0).toLocaleString();
            } else if (update.fmt === 'number') {
                displayValue = (update.val || 0).toString();
            } else {
                displayValue = update.val || 'Unknown';
            }
            
            element.textContent = displayValue;
            console.log(`Updated ${update.sel} to: ${displayValue}`);
        } else {
            console.warn(`Element not found: ${update.sel}`);
        }
    });
    
    // Show the pod cost section if we have data
    if (topNamespaceCost > 0 || namespaceCount > 0) {
        const podSection = document.getElementById('pod-cost-section');
        if (podSection) {
            podSection.style.display = 'block';
            console.log('Pod cost section made visible');
        }
    }
}

// Debug
function testImplementationAPI() {
  console.log('🧪 Testing implementation API directly...');

  fetch('/api/implementation-plan')
    .then(response => response.json())
    .then(data => {
      console.log('🧪 Test result:', data);
      console.log('🧪 Phases:', data.phases);
      console.log('🧪 Summary:', data.summary);
    })
    .catch(error => {
      console.error('🧪 Test error:', error);
    });
}

// ——— CSS Injection ———
function injectMetricsCSS() {
  if (document.getElementById('metrics-update-css')) return;
  const s = document.createElement('style');
  s.id = 'metrics-update-css';
  s.textContent = `
    .metric-updated { position: relative; }
    .metric-updated-indicator { position: absolute; top:-2px; right:-2px; animation:pulse 2s infinite; }
    @keyframes pulse {0%,100%{opacity:1;}50%{opacity:0.5;}}
    @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    .data-source-indicator { position: fixed; top:90px; right:20px; z-index:1000; }
    .data-source-badge { background:rgba(255,255,255,0.95); border-radius:20px; padding:8px 16px; display:flex; align-items:center; gap:5px; box-shadow:0 2px 10px rgba(0,0,0,0.1); }
    .data-source-badge.real-data { border:1px solid #28a745; color:#28a745; }
    .data-source-badge.sample-data { border:1px solid #ffc107; color:#856404; background:rgba(255,193,7,0.1); }
    [data-theme="dark"] .data-source-badge { background:rgba(45,55,72,0.95); color:#f7fafc; }
  `;
  document.head.appendChild(s);
}

// alerts/schedule/deploy-fix


/**
 * AKS Cost Intelligence - Enhanced Frontend
 * Modern UI interactions, real alerts, and deployment functionality
 */

// Global state management
const AppState = {
    alerts: [],
    deployments: [],
    currentAnalysis: null,
    notifications: []
};

// Notification system
class NotificationManager {
    constructor() {
        this.container = this.createContainer();
    }
    
    createContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
        return container;
    }
    
    show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `
            notification-toast fade-in
            bg-white dark:bg-gray-800 
            border-l-4 ${this.getBorderColor(type)}
            rounded-lg shadow-lg p-4 max-w-sm
            transform transition-all duration-300
        `;
        
        notification.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <i class="fas fa-${this.getIcon(type)} text-${this.getTextColor(type)} text-xl"></i>
                </div>
                <div class="ml-3 flex-1">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                        ${message}
                    </p>
                </div>
                <div class="ml-4 flex-shrink-0">
                    <button class="inline-flex text-gray-400 hover:text-gray-600 focus:outline-none">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        // Add click to dismiss
        notification.querySelector('button').addEventListener('click', () => {
            this.remove(notification);
        });
        
        this.container.appendChild(notification);
        
        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => this.remove(notification), duration);
        }
        
        return notification;
    }
    
    remove(notification) {
        notification.classList.add('opacity-0', 'transform', 'translate-x-full');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
    
    getBorderColor(type) {
        const colors = {
            success: 'border-green-500',
            error: 'border-red-500',
            warning: 'border-yellow-500',
            info: 'border-blue-500'
        };
        return colors[type] || colors.info;
    }
    
    getTextColor(type) {
        const colors = {
            success: 'green-500',
            error: 'red-500',
            warning: 'yellow-500',
            info: 'blue-500'
        };
        return colors[type] || colors.info;
    }
    
    getIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    }
}

// Initialize notification manager
const notifications = new NotificationManager();

// Enhanced Alerts Management
class AlertsManager {
    constructor() {
        this.alerts = [];
        this.init();
    }
    
    async init() {
        await this.loadAlerts();
        this.bindEvents();
    }
    
    async loadAlerts() {
        try {
            const response = await fetch('/api/alerts');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.alerts = data.alerts;
                this.renderAlerts();
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Failed to load alerts:', error);
            notifications.show('Failed to load alerts', 'error');
        }
    }
    
    async createAlert(alertData) {
        try {
            const response = await fetch('/api/alerts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(alertData)
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                notifications.show('Alert created successfully!', 'success');
                await this.loadAlerts();
                return true;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Failed to create alert:', error);
            notifications.show('Failed to create alert: ' + error.message, 'error');
            return false;
        }
    }
    
    async updateAlert(alertId, updates) {
        try {
            const response = await fetch(`/api/alerts/${alertId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                notifications.show('Alert updated successfully!', 'success');
                await this.loadAlerts();
                return true;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Failed to update alert:', error);
            notifications.show('Failed to update alert: ' + error.message, 'error');
            return false;
        }
    }
    
    async deleteAlert(alertId) {
        if (!confirm('Are you sure you want to delete this alert?')) {
            return false;
        }
        
        try {
            const response = await fetch(`/api/alerts/${alertId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                notifications.show('Alert deleted successfully!', 'success');
                await this.loadAlerts();
                return true;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Failed to delete alert:', error);
            notifications.show('Failed to delete alert: ' + error.message, 'error');
            return false;
        }
    }
    
    async testAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/test`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                notifications.show('Test email sent successfully!', 'success');
                return true;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Failed to test alert:', error);
            notifications.show('Failed to send test email: ' + error.message, 'error');
            return false;
        }
    }
    
    renderAlerts() {
        const container = document.getElementById('existing-alerts');
        if (!container) return;
        
        if (this.alerts.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-bell-slash text-4xl text-gray-400 mb-4"></i>
                    <p class="text-gray-500">No alerts configured yet</p>
                    <p class="text-sm text-gray-400">Create your first alert to start monitoring costs</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.alerts.map(alert => this.renderAlertCard(alert)).join('');
    }
    
    renderAlertCard(alert) {
        const statusClass = alert.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800';
        const lastTriggered = alert.last_triggered ? 
            new Date(alert.last_triggered).toLocaleDateString() : 'Never';
        
        return `
            <div class="alert-card bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-all duration-300">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-3 mb-2">
                            <h4 class="text-lg font-semibold text-gray-900">${alert.name}</h4>
                            <span class="px-2 py-1 text-xs font-medium rounded-full ${statusClass}">
                                ${alert.status}
                            </span>
                        </div>
                        
                        <div class="grid grid-cols-2 gap-4 text-sm text-gray-600 mb-4">
                            <div>
                                <span class="font-medium">Threshold:</span> 
                                ${alert.threshold_amount > 0 ? 
                                    `$${alert.threshold_amount.toLocaleString()}` : 
                                    `${alert.threshold_percentage}%`}
                            </div>
                            <div>
                                <span class="font-medium">Email:</span> ${alert.email}
                            </div>
                            <div>
                                <span class="font-medium">Cluster:</span> ${alert.cluster_name || 'All'}
                            </div>
                            <div>
                                <span class="font-medium">Last Triggered:</span> ${lastTriggered}
                            </div>
                        </div>
                        
                        <div class="flex items-center gap-2 text-sm text-gray-500">
                            <i class="fas fa-chart-line"></i>
                            <span>Triggered ${alert.trigger_count} times</span>
                            <span class="mx-2">•</span>
                            <span>Frequency: ${alert.notification_frequency}</span>
                        </div>
                    </div>
                    
                    <div class="flex items-center gap-2 ml-4">
                        <button class="btn-icon-sm text-blue-600 hover:bg-blue-50" 
                                onclick="alertsManager.editAlert(${alert.id})"
                                title="Edit Alert">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon-sm text-green-600 hover:bg-green-50" 
                                onclick="alertsManager.testAlert(${alert.id})"
                                title="Test Alert">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                        <button class="btn-icon-sm text-red-600 hover:bg-red-50" 
                                onclick="alertsManager.deleteAlert(${alert.id})"
                                title="Delete Alert">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    editAlert(alertId) {
        const alert = this.alerts.find(a => a.id === alertId);
        if (!alert) return;
        
        // Populate form with alert data
        document.getElementById('budget-amount').value = alert.threshold_amount;
        document.getElementById('alert-email').value = alert.email;
        document.getElementById('alert-threshold').value = alert.threshold_percentage;
        
        // Scroll to form
        document.getElementById('budget-alert-form').scrollIntoView({ behavior: 'smooth' });
        
        // Show update button instead of create
        const submitBtn = document.querySelector('#budget-alert-form button[type="submit"]');
        submitBtn.innerHTML = `
            <i class="fas fa-save me-2"></i>Update Alert
        `;
        submitBtn.onclick = (e) => {
            e.preventDefault();
            this.handleFormSubmit(alertId);
        };
    }
    
    bindEvents() {
        const form = document.getElementById('budget-alert-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmit();
            });
        }
    }
    
    async handleFormSubmit(alertId = null) {
        const formData = {
            name: document.getElementById('budget-amount').value ? 
                `Budget Alert - $${document.getElementById('budget-amount').value}` : 
                'Cost Threshold Alert',
            alert_type: 'cost_threshold',
            threshold_amount: parseFloat(document.getElementById('budget-amount').value) || 0,
            threshold_percentage: parseFloat(document.getElementById('alert-threshold').value) || 80,
            email: document.getElementById('alert-email').value,
            resource_group: '', // Would be populated from current analysis
            cluster_name: '', // Would be populated from current analysis
            notification_frequency: 'immediate'
        };
        
        if (alertId) {
            await this.updateAlert(alertId, formData);
        } else {
            await this.createAlert(formData);
        }
        
        // Reset form
        document.getElementById('budget-alert-form').reset();
        const submitBtn = document.querySelector('#budget-alert-form button[type="submit"]');
        submitBtn.innerHTML = `
            <i class="fas fa-play me-2"></i>Setup Smart Alerts
        `;
        submitBtn.onclick = null;
    }
}

// Enhanced Deployment Management
class DeploymentManager {
    constructor() {
        this.deployments = [];
        this.init();
    }
    
    async init() {
        await this.loadDeployments();
        this.bindEvents();
    }
    
    async loadDeployments() {
        try {
            const response = await fetch('/api/deployments');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.deployments = data.tasks;
                this.renderDeployments();
            }
        } catch (error) {
            console.error('Failed to load deployments:', error);
        }
    }
    
    async deployOptimizations() {
        const analysisData = AppState.currentAnalysis;
        if (!analysisData) {
            notifications.show('Please run an analysis first', 'warning');
            return;
        }
        
        // Show deployment modal
        this.showDeploymentModal();
    }
    
    async scheduleOptimization() {
        const analysisData = AppState.currentAnalysis;
        if (!analysisData) {
            notifications.show('Please run an analysis first', 'warning');
            return;
        }
        
        // Show scheduling modal
        this.showSchedulingModal();
    }
    
    showDeploymentModal() {
        const modal = this.createDeploymentModal();
        document.body.appendChild(modal);
        
        // Show modal with animation
        setTimeout(() => {
            modal.classList.add('opacity-100');
            modal.querySelector('.modal-content').classList.add('scale-100');
        }, 10);
    }
    
    showSchedulingModal() {
        const modal = this.createSchedulingModal();
        document.body.appendChild(modal);
        
        // Show modal with animation
        setTimeout(() => {
            modal.classList.add('opacity-100');
            modal.querySelector('.modal-content').classList.add('scale-100');
        }, 10);
    }
    
    createDeploymentModal() {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 opacity-0 transition-opacity duration-300';
        
        modal.innerHTML = `
            <div class="modal-content bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 transform scale-95 transition-transform duration-300">
                <div class="px-6 py-4 border-b border-gray-200">
                    <div class="flex items-center justify-between">
                        <h3 class="text-lg font-semibold text-gray-900">Deploy Optimizations</h3>
                        <button class="text-gray-400 hover:text-gray-600" onclick="this.closest('.fixed').remove()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                
                <div class="px-6 py-4 max-h-96 overflow-y-auto">
                    <div class="space-y-4">
                        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <div class="flex items-center">
                                <i class="fas fa-info-circle text-blue-500 mr-3"></i>
                                <div>
                                    <h4 class="text-sm font-medium text-blue-900">Ready to Deploy</h4>
                                    <p class="text-sm text-blue-700">The following optimizations will be applied immediately:</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="space-y-3">
                            <div class="optimization-item border border-gray-200 rounded-lg p-4">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center">
                                        <input type="checkbox" id="hpa-opt" checked class="mr-3">
                                        <div>
                                            <h5 class="font-medium text-gray-900">Memory-based HPA</h5>
                                            <p class="text-sm text-gray-600">Enable memory-based horizontal pod autoscaling</p>
                                        </div>
                                    </div>
                                    <span class="text-green-600 font-medium">$324/mo savings</span>
                                </div>
                            </div>
                            
                            <div class="optimization-item border border-gray-200 rounded-lg p-4">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center">
                                        <input type="checkbox" id="resource-opt" checked class="mr-3">
                                        <div>
                                            <h5 class="font-medium text-gray-900">Resource Right-sizing</h5>
                                            <p class="text-sm text-gray-600">Optimize CPU and memory requests/limits</p>
                                        </div>
                                    </div>
                                    <span class="text-green-600 font-medium">$283/mo savings</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                            <div class="flex items-start">
                                <i class="fas fa-exclamation-triangle text-yellow-500 mr-3 mt-1"></i>
                                <div>
                                    <h4 class="text-sm font-medium text-yellow-900">Before You Deploy</h4>
                                    <ul class="text-sm text-yellow-700 mt-1 list-disc list-inside">
                                        <li>Ensure you have cluster admin permissions</li>
                                        <li>Backup current configurations (automatic rollback available)</li>
                                        <li>Monitor workloads after deployment</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                    <button class="btn-secondary" onclick="this.closest('.fixed').remove()">
                        Cancel
                    </button>
                    <button class="btn-primary" onclick="deploymentManager.confirmDeploy(this)">
                        <i class="fas fa-rocket mr-2"></i>
                        Deploy Now
                    </button>
                </div>
            </div>
        `;
        
        return modal;
    }
    
    createSchedulingModal() {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 opacity-0 transition-opacity duration-300';
        
        // Get current date for minimum scheduling
        const now = new Date();
        const minDateTime = new Date(now.getTime() + 60000); // Minimum 1 minute from now
        const minDateTimeString = minDateTime.toISOString().slice(0, 16);
        
        modal.innerHTML = `
            <div class="modal-content bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 transform scale-95 transition-transform duration-300">
                <div class="px-6 py-4 border-b border-gray-200">
                    <div class="flex items-center justify-between">
                        <h3 class="text-lg font-semibold text-gray-900">Schedule Deployment</h3>
                        <button class="text-gray-400 hover:text-gray-600" onclick="this.closest('.fixed').remove()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                
                <div class="px-6 py-4">
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                <i class="fas fa-calendar-alt mr-2"></i>
                                Deployment Date & Time
                            </label>
                            <input type="datetime-local" 
                                   id="schedule-datetime" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                   min="${minDateTimeString}"
                                   value="${minDateTimeString}">
                            <p class="text-xs text-gray-500 mt-1">Select when to deploy the optimizations</p>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                <i class="fas fa-bell mr-2"></i>
                                Notification Preferences
                            </label>
                            <div class="space-y-2">
                                <label class="flex items-center">
                                    <input type="checkbox" checked class="mr-2">
                                    <span class="text-sm">Email notification before deployment</span>
                                </label>
                                <label class="flex items-center">
                                    <input type="checkbox" checked class="mr-2">
                                    <span class="text-sm">Email notification after completion</span>
                                </label>
                            </div>
                        </div>
                        
                        <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                            <div class="flex items-start">
                                <i class="fas fa-dollar-sign text-green-500 mr-3 mt-1"></i>
                                <div>
                                    <h4 class="text-sm font-medium text-green-900">Estimated Monthly Savings</h4>
                                    <p class="text-lg font-bold text-green-700">$607.19</p>
                                    <p class="text-xs text-green-600">Based on current analysis</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                    <button class="btn-secondary" onclick="this.closest('.fixed').remove()">
                        Cancel
                    </button>
                    <button class="btn-primary" onclick="deploymentManager.confirmSchedule(this)">
                        <i class="fas fa-clock mr-2"></i>
                        Schedule Deployment
                    </button>
                </div>
            </div>
        `;
        
        return modal;
    }
    
    async confirmDeploy(button) {
        const modal = button.closest('.fixed');
        const selectedOptimizations = [];
        
        // Get selected optimizations
        if (document.getElementById('hpa-opt').checked) {
            selectedOptimizations.push({
                type: 'hpa_memory_based',
                name: 'Memory-based HPA',
                configuration: {
                    min_replicas: 1,
                    max_replicas: 10,
                    target_memory_utilization: 70
                }
            });
        }
        
        if (document.getElementById('resource-opt').checked) {
            selectedOptimizations.push({
                type: 'resource_limits',
                name: 'Resource Right-sizing',
                configuration: {
                    optimize_requests: true,
                    optimize_limits: true
                }
            });
        }
        
        // Show loading state
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Deploying...';
        
        try {
            for (const optimization of selectedOptimizations) {
                const response = await fetch('/api/deploy', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: optimization.name,
                        type: optimization.type,
                        resource_group: AppState.currentAnalysis?.resource_group || '',
                        cluster_name: AppState.currentAnalysis?.cluster_name || '',
                        configuration: optimization.configuration,
                        estimated_savings: 607.19 // From analysis
                    })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    notifications.show(`${optimization.name} deployment started!`, 'success');
                } else {
                    throw new Error(data.message);
                }
            }
            
            modal.remove();
            await this.loadDeployments();
            
        } catch (error) {
            console.error('Deployment failed:', error);
            notifications.show('Deployment failed: ' + error.message, 'error');
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-rocket mr-2"></i>Deploy Now';
        }
    }
    
    async confirmSchedule(button) {
        const modal = button.closest('.fixed');
        const scheduledTime = document.getElementById('schedule-datetime').value;
        
        if (!scheduledTime) {
            notifications.show('Please select a deployment time', 'warning');
            return;
        }
        
        // Show loading state
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Scheduling...';
        
        try {
            const response = await fetch('/api/schedule-deployment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: 'Scheduled Optimization',
                    type: 'hpa_memory_based',
                    resource_group: AppState.currentAnalysis?.resource_group || '',
                    cluster_name: AppState.currentAnalysis?.cluster_name || '',
                    configuration: {
                        min_replicas: 1,
                        max_replicas: 10,
                        target_memory_utilization: 70
                    },
                    estimated_savings: 607.19,
                    scheduled_time: new Date(scheduledTime).toISOString()
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                notifications.show('Deployment scheduled successfully!', 'success');
                modal.remove();
                await this.loadDeployments();
            } else {
                throw new Error(data.message);
            }
            
        } catch (error) {
            console.error('Scheduling failed:', error);
            notifications.show('Scheduling failed: ' + error.message, 'error');
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-clock mr-2"></i>Schedule Deployment';
        }
    }
    
    renderDeployments() {
        // This would render deployments in a dedicated section
        // For now, we'll show a status indicator
        this.updateDeploymentStatus();
    }
    
    updateDeploymentStatus() {
        const activeDeployments = this.deployments.filter(d => 
            ['pending', 'running', 'scheduled'].includes(d.status)
        );
        
        if (activeDeployments.length > 0) {
            this.showDeploymentStatus(activeDeployments);
        }
    }
    
    showDeploymentStatus(deployments) {
        // Remove existing status
        const existing = document.getElementById('deployment-status');
        if (existing) existing.remove();
        
        const statusContainer = document.createElement('div');
        statusContainer.id = 'deployment-status';
        statusContainer.className = 'fixed bottom-4 left-4 bg-white rounded-lg shadow-lg border border-gray-200 p-4 max-w-sm z-40';
        
        statusContainer.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <h4 class="font-medium text-gray-900">Active Deployments</h4>
                <button onclick="this.parentElement.parentElement.remove()" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="space-y-2">
                ${deployments.map(deployment => `
                    <div class="flex items-center justify-between text-sm">
                        <span class="text-gray-700">${deployment.name}</span>
                        <span class="status-indicator status-${deployment.status}">
                            ${deployment.status}
                        </span>
                    </div>
                `).join('')}
            </div>
        `;
        
        document.body.appendChild(statusContainer);
    }
    
    bindEvents() {
        // Bind deployment buttons if they exist in global scope
        window.deployOptimizations = () => this.deployOptimizations();
        window.scheduleOptimization = () => this.scheduleOptimization();
    }
}

// Enhanced UI Interactions
class UIEnhancer {
    constructor() {
        this.init();
    }
    
    init() {
        this.addLoadingStates();
        this.addHoverEffects();
        this.addAnimations();
        this.addKeyboardShortcuts();
    }
    
    addLoadingStates() {
        // Add loading states to buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-primary, .btn-success')) {
                this.addButtonLoading(e.target);
            }
        });
    }
    
    addButtonLoading(button) {
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Loading...';
        
        // Remove loading state after 3 seconds (adjust based on actual operation)
        setTimeout(() => {
            button.disabled = false;
            button.innerHTML = originalText;
        }, 3000);
    }
    
    addHoverEffects() {
        // Add hover effects to cards
        const style = document.createElement('style');
        style.textContent = `
            .card, .metric-card, .alert-card {
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            .card:hover, .metric-card:hover, .alert-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            }
            
            .btn-icon-sm {
                @apply w-8 h-8 rounded-full flex items-center justify-center transition-colors duration-200;
            }
        `;
        document.head.appendChild(style);
    }
    
    addAnimations() {
        // Add intersection observer for fade-in animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        });
        
        // Observe all cards and metric elements
        document.querySelectorAll('.card, .metric-card').forEach(el => {
            observer.observe(el);
        });
    }
    
    addKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R to refresh charts
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                if (typeof refreshCharts === 'function') {
                    refreshCharts();
                    notifications.show('Charts refreshed!', 'info');
                }
            }
            
            // Escape to close modals
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.fixed.inset-0');
                modals.forEach(modal => modal.remove());
            }
        });
    }
}

// Initialize enhanced functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize managers
    window.alertsManager = new AlertsManager();
    window.deploymentManager = new DeploymentManager();
    window.uiEnhancer = new UIEnhancer();
    
    // Add enhanced CSS classes
    const style = document.createElement('style');
    style.textContent = `
        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }
        
        .slide-up {
            animation: slideUp 0.6s ease-out;
        }
        
        .scale-in {
            animation: scaleIn 0.4s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes scaleIn {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
        
        .btn-secondary {
            @apply px-4 py-2 border border-gray-300 text-gray-700 bg-white rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200;
        }
        
        .notification-toast {
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }
    `;
    document.head.appendChild(style);
    
    console.log('Enhanced dashboard initialized successfully!');
});

// Export for global access
window.AppState = AppState;
window.notifications = notifications;