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

    // Sidebar Management - Two Panel System
    toggleSidebar() {
        window.logger.debug('Toggle sidebar function called - Two Panel System');
        const sidebarMenu = document.getElementById('sidebar-menu');
        if (sidebarMenu) {
            sidebarMenu.classList.toggle('expanded');
            
            // Save state
            const isExpanded = sidebarMenu.classList.contains('expanded');
            localStorage.setItem('sidebarExpanded', isExpanded);
            
            // Update toggle button icon based on state
            const toggleBtn = document.querySelector('.sidebar-toggle i');
            if (toggleBtn) {
                toggleBtn.className = isExpanded ? 'fas fa-times' : 'fas fa-bars';
            }
            
            // Trigger chart resize after sidebar animation completes
            setTimeout(() => {
                this.triggerChartResize();
            }, 350); // Wait for sidebar transition to complete
            
            window.logger.debug('Sidebar menu expanded state:', isExpanded);
        } else {
            window.logger.error('Sidebar menu element not found');
        }
    }

    restoreSidebarState() {
        const sidebarMenu = document.getElementById('sidebar-menu');
        if (sidebarMenu) {
            const savedState = localStorage.getItem('sidebarExpanded');
            const isExpanded = savedState === 'true';
            
            if (isExpanded) {
                sidebarMenu.classList.add('expanded');
            }
            
            // Set correct icon based on state
            const toggleBtn = document.querySelector('.sidebar-toggle i');
            if (toggleBtn) {
                toggleBtn.className = isExpanded ? 'fas fa-times' : 'fas fa-bars';
            }
        }
    }

    // Chart Management
    triggerChartResize() {
        window.logger.debug('Triggering chart resize...');
        
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
        
        window.logger.debug('Chart resize triggered');
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
            window.logger.debug('Initializing Dashboard module...');
            window.Dashboard.init();
        } else {
            window.logger.error('Dashboard module not available or missing init function');
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