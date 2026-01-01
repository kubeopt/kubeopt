/**
 * Unified Dashboard JavaScript
 * Handles dashboard functionality including sidebar, charts, and navigation
 */

class UnifiedDashboard {
    constructor() {
        this.appState = null;
        this.clusterInfo = null;
        this.init();
    }

    init() {
        this.setupAppState();
        this.setupClusterInfo();
        this.bindEventListeners();
    }

    setupAppState() {
        // App state is set by the template
        this.appState = window.AppState || {};
    }

    setupClusterInfo() {
        // Cluster info is set by the template
        this.clusterInfo = window.clusterInfo || {};
    }

    bindEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.onDOMContentLoaded();
        });
    }

    onDOMContentLoaded() {
        this.setCurrentDate();
        this.restoreSidebarState();
        this.initializeDashboardModule();
    }

    // Sidebar Management
    toggleSidebar() {
        console.log('Toggle sidebar function called');
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('collapsed');
            
            // Save state
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
            
            // Update toggle button icon based on state
            const toggleBtn = document.querySelector('.sidebar-toggle i');
            if (toggleBtn) {
                toggleBtn.className = isCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left';
                // Add visual feedback
                toggleBtn.style.transform = isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)';
            }
            
            // Trigger chart resize after sidebar animation completes
            setTimeout(() => {
                this.triggerChartResize();
            }, 350); // Wait for sidebar transition to complete
            
            console.log('Sidebar collapsed state:', isCollapsed);
        } else {
            console.error('Sidebar element not found');
        }
    }

    restoreSidebarState() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            const savedState = localStorage.getItem('sidebarCollapsed');
            const isCollapsed = savedState === 'true';
            
            if (isCollapsed) {
                sidebar.classList.add('collapsed');
            }
            
            // Set correct icon based on state
            const toggleBtn = document.querySelector('.sidebar-toggle i');
            if (toggleBtn) {
                toggleBtn.className = isCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left';
                toggleBtn.style.transform = isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)';
            }
        }
    }

    // Chart Management
    triggerChartResize() {
        console.log('Triggering chart resize...');
        
        // Trigger window resize event to make charts responsive
        window.dispatchEvent(new Event('resize'));
        
        // If Chart.js is available, resize all charts
        if (window.Chart && window.Chart.instances) {
            Object.values(window.Chart.instances).forEach(chart => {
                if (chart && typeof chart.resize === 'function') {
                    chart.resize();
                }
            });
        }
        
        // Alternative method for Chart.js v3+
        if (window.Chart && window.Chart.registry) {
            Object.values(window.Chart.registry.controllers.items).forEach(controller => {
                if (controller.chart && typeof controller.chart.resize === 'function') {
                    controller.chart.resize();
                }
            });
        }
        
        // If using a global chart manager
        if (window.ChartManager && typeof window.ChartManager.resizeAll === 'function') {
            window.ChartManager.resizeAll();
        }
        
        console.log('Chart resize triggered');
    }

    // Utility Functions
    setCurrentDate() {
        const dateEl = document.getElementById('current-date');
        if (dateEl) {
            const today = new Date();
            const options = { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
            };
            dateEl.textContent = today.toLocaleDateString('en-US', options);
        }
    }

    initializeDashboardModule() {
        // Initialize Dashboard module
        if (window.Dashboard && typeof window.Dashboard.init === 'function') {
            console.log('Initializing Dashboard module...');
            window.Dashboard.init();
        } else {
            console.error('Dashboard module not available or missing init function');
        }
    }

    // Placeholder Functions
    generateNewPlan() {
        showToast('Generating new implementation plan...', 'info');
        // This will be implemented with actual API call
    }

    createAlert() {
        showToast('Alert creation modal would open here', 'info');
        // This will be implemented with actual modal
    }

    // Getters for external access
    getAppState() {
        return this.appState;
    }

    getClusterInfo() {
        return this.clusterInfo;
    }
}

// Initialize the dashboard when DOM is loaded
let unifiedDashboard;

document.addEventListener('DOMContentLoaded', function() {
    unifiedDashboard = new UnifiedDashboard();
});

// Global functions for template onclick handlers
function toggleSidebar() {
    unifiedDashboard?.toggleSidebar();
}

function generateNewPlan() {
    unifiedDashboard?.generateNewPlan();
}

function createAlert() {
    unifiedDashboard?.createAlert();
}

// Make functions globally available
window.generateNewPlan = generateNewPlan;
window.createAlert = createAlert;