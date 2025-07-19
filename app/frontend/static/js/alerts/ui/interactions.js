// frontend/static/js/alerts/ui/interactions.js

import { AlertsState, StateActions } from '../core/state.js';
import { displayAlerts } from './display.js';

/**
 * UI interaction functions for filtering, tabs, and menus
 */

/**
 * Filter alerts by status - COMPLETELY FIXED to show all alerts
 */
export function filterAlerts(filter) {
    console.log(`🔍 Filtering alerts by: ${filter}`);
    
    // Update the current filter in state
    AlertsState.currentFilter = filter;
    
    // Update button states
    const filterButtons = document.querySelectorAll('[onclick*="filterAlerts"], .filter-btn');
    filterButtons.forEach(btn => {
        btn.classList.remove('active', 'btn-primary');
        btn.classList.add('btn-outline-primary');
    });
    
    // Activate selected filter button
    const activeBtn = document.querySelector(`[onclick="filterAlerts('${filter}')"]`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'btn-primary');
        activeBtn.classList.remove('btn-outline-primary');
    }
    
    // Filter alert rows without corrupting the data
    const alertRows = document.querySelectorAll('.alert-row');
    let visibleCount = 0;
    
    alertRows.forEach(row => {
        const alertStatus = row.dataset.status || 'active';
        let shouldShow = false;
        
        switch (filter) {
            case 'all':
                shouldShow = true;
                break;
            case 'active':
                shouldShow = alertStatus === 'active';
                break;
            case 'paused':
                shouldShow = alertStatus === 'paused';
                break;
            default:
                shouldShow = true;
        }
        
        if (shouldShow) {
            row.style.display = '';
            row.style.opacity = '1';
            visibleCount++;
        } else {
            row.style.display = 'none';
            row.style.opacity = '0.5';
        }
    });
    
    // Update filter counts without corrupting state
    updateFilterCountsDisplay();
    
    console.log(`✅ Filter applied: ${filter}, showing ${visibleCount} alerts out of ${alertRows.length} total`);
}

/**
 * Handle toggle switch for alert pause/resume - FIXED to prevent state corruption
 */
export function handleToggleAlert(alertId, isChecked) {
    console.log(`🔄 Toggling alert ${alertId} to ${isChecked ? 'active' : 'paused'}`);
    
    const action = isChecked ? 'resume' : 'pause';
    const newStatus = action === 'pause' ? 'paused' : 'active';
    
    // Find the alert row and update immediately
    const row = document.querySelector(`[data-alert-id="${alertId}"]`);
    if (row) {
        // Update the row's data attribute immediately
        row.dataset.status = newStatus;
        
        // Update the status badge immediately
        const badge = row.querySelector('.badge');
        if (badge) {
            if (isChecked) {
                badge.className = 'badge bg-success px-2 py-1';
                badge.textContent = 'Active';
            } else {
                badge.className = 'badge bg-secondary px-2 py-1';
                badge.textContent = 'Paused';
            }
        }
    }
    
    // Update the state immediately to prevent issues
    const alertIndex = AlertsState.alerts.findIndex(a => a.id == alertId);
    if (alertIndex !== -1) {
        AlertsState.alerts[alertIndex].status = newStatus;
    }
    
    // Update counts immediately
    updateFilterCountsDisplay();
    
    // Make the API call asynchronously
    makeToggleAPICall(alertId, action, isChecked);
}

/**
 * Make API call for toggle alert
 */
async function makeToggleAPICall(alertId, action, isChecked) {
    try {
        const response = await fetch(`/api/alerts/${alertId}/pause`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            console.log(`✅ Alert ${alertId} ${action}d successfully`);
            // Show success toast
            if (window.createToast) {
                window.createToast('success', 'Success', `Alert ${action}d successfully`);
            }
        } else {
            // Revert if API call failed
            revertToggleState(alertId, !isChecked);
            if (window.createToast) {
                window.createToast('error', 'Error', `Failed to ${action} alert`);
            }
        }
    } catch (error) {
        console.error(`❌ Error ${action}ing alert:`, error);
        // Revert if API call failed
        revertToggleState(alertId, !isChecked);
        if (window.createToast) {
            window.createToast('error', 'Error', `Failed to ${action} alert: ${error.message}`);
        }
    }
}

/**
 * Revert toggle state if API call fails
 */
function revertToggleState(alertId, originalState) {
    const toggle = document.getElementById(`toggle-${alertId}`);
    if (toggle) {
        toggle.checked = originalState;
    }
    
    const row = document.querySelector(`[data-alert-id="${alertId}"]`);
    if (row) {
        const status = originalState ? 'active' : 'paused';
        row.dataset.status = status;
        
        // Revert the state in AlertsState
        const alertIndex = AlertsState.alerts.findIndex(a => a.id == alertId);
        if (alertIndex !== -1) {
            AlertsState.alerts[alertIndex].status = status;
        }
        
        const badge = row.querySelector('.badge');
        if (badge) {
            if (originalState) {
                badge.className = 'badge bg-success px-2 py-1';
                badge.textContent = 'Active';
            } else {
                badge.className = 'badge bg-secondary px-2 py-1';
                badge.textContent = 'Paused';
            }
        }
    }
    
    updateFilterCountsDisplay();
}

/**
 * Switch between alerts tabs - COMPLETELY FIXED to prevent conflicts
 */
export function switchAlertsTab(tabName) {
    console.log(`📑 Switching to tab: ${tabName}`);
    
    // Define all possible tab content selectors
    const tabContentSelectors = [
        '#alerts-tab-content',
        '#notifications-tab-content', 
        '.alerts-content',
        '.notifications-content',
        '.tab-content',
        '.alerts-tab-content',
        '.notifications-tab-content',
        '[data-tab="alerts"]',
        '[data-tab="notifications"]'
    ];
    
    // Define all possible tab button selectors
    const tabButtonSelectors = [
        '#alerts-tab-btn',
        '#notifications-tab-btn',
        '.alerts-tab-button',
        '.notifications-tab-button',
        '.tab-button',
        '.nav-link',
        '[onclick*="alerts"]',
        '[onclick*="notifications"]',
        '[data-tab="alerts"]',
        '[data-tab="notifications"]'
    ];
    
    // Hide ALL possible tab contents
    tabContentSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            element.style.display = 'none';
            element.classList.add('hidden');
        });
    });
    
    // Remove active class from ALL possible tab buttons
    tabButtonSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            element.classList.remove('active', 'border-blue-500', 'text-blue-600');
            element.classList.add('border-transparent', 'text-gray-500');
        });
    });
    
    // Now show the specific tab
    if (tabName === 'alerts') {
        // Show alerts content - try multiple selectors
        const alertsContentSelectors = [
            '#alerts-tab-content',
            '.alerts-content',
            '[data-tab="alerts"]'
        ];
        
        let alertsContentFound = false;
        for (const selector of alertsContentSelectors) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                if (!alertsContentFound) {
                    element.style.display = 'block';
                    element.classList.remove('hidden');
                    alertsContentFound = true;
                    console.log(`✅ Showed alerts content using selector: ${selector}`);
                }
            });
            if (alertsContentFound) break;
        }
        
        // Activate alerts tab button - try multiple selectors
        const alertsButtonSelectors = [
            '#alerts-tab-btn',
            '[onclick*="switchAlertsTab(\'alerts\')"]',
            '[data-tab="alerts"]',
            '.alerts-tab-button'
        ];
        
        let alertsButtonFound = false;
        for (const selector of alertsButtonSelectors) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                if (!alertsButtonFound) {
                    element.classList.add('active', 'border-blue-500', 'text-blue-600');
                    element.classList.remove('border-transparent', 'text-gray-500');
                    alertsButtonFound = true;
                    console.log(`✅ Activated alerts button using selector: ${selector}`);
                }
            });
            if (alertsButtonFound) break;
        }
        
    } else if (tabName === 'notifications') {
        // Show notifications content - try multiple selectors
        const notificationsContentSelectors = [
            '#notifications-tab-content',
            '.notifications-content',
            '[data-tab="notifications"]'
        ];
        
        let notificationsContentFound = false;
        for (const selector of notificationsContentSelectors) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                if (!notificationsContentFound) {
                    element.style.display = 'block';
                    element.classList.remove('hidden');
                    notificationsContentFound = true;
                    console.log(`✅ Showed notifications content using selector: ${selector}`);
                }
            });
            if (notificationsContentFound) break;
        }
        
        // Activate notifications tab button - try multiple selectors
        const notificationsButtonSelectors = [
            '#notifications-tab-btn',
            '[onclick*="switchAlertsTab(\'notifications\')"]',
            '[data-tab="notifications"]',
            '.notifications-tab-button'
        ];
        
        let notificationsButtonFound = false;
        for (const selector of notificationsButtonSelectors) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                if (!notificationsButtonFound) {
                    element.classList.add('active', 'border-blue-500', 'text-blue-600');
                    element.classList.remove('border-transparent', 'text-gray-500');
                    notificationsButtonFound = true;
                    console.log(`✅ Activated notifications button using selector: ${selector}`);
                }
            });
            if (notificationsButtonFound) break;
        }
    }
    
    console.log(`✅ Successfully switched to ${tabName} tab`);
}

/**
 * Toggle simple alert menu dropdown - FIXED positioning
 */
export function toggleSimpleMenu(alertId) {
    console.log('🔧 Toggling menu for alert:', alertId);
    
    // Close all other menus first
    document.querySelectorAll('[id^="simple-menu-"]').forEach(menu => {
        if (menu.id !== `simple-menu-${alertId}`) {
            menu.style.display = 'none';
        }
    });
    
    // Toggle current menu
    const menu = document.getElementById(`simple-menu-${alertId}`);
    if (menu) {
        const isHidden = menu.style.display === 'none' || menu.style.display === '';
        
        if (isHidden) {
            // Position and show menu
            menu.style.display = 'block';
            menu.style.position = 'absolute';
            menu.style.top = '100%';
            menu.style.right = '0';
            menu.style.left = 'auto';
            menu.style.zIndex = '1050';
            menu.style.minWidth = '160px';
            menu.style.backgroundColor = '#fff';
            menu.style.border = '1px solid #dee2e6';
            menu.style.borderRadius = '0.375rem';
            menu.style.boxShadow = '0 0.5rem 1rem rgba(0, 0, 0, 0.15)';
            menu.style.padding = '0.5rem 0';
            console.log('✅ Menu opened for alert:', alertId);
        } else {
            menu.style.display = 'none';
            console.log('✅ Menu closed for alert:', alertId);
        }
    } else {
        console.error('❌ Menu not found for alert:', alertId);
    }
}

/**
 * Close specific menu
 */
export function closeMenu(alertId) {
    const menu = document.getElementById(`simple-menu-${alertId}`);
    if (menu) {
        menu.style.display = 'none';
    }
}

/**
 * Update filter button counts without affecting display
 */
function updateFilterCountsDisplay() {
    const alerts = AlertsState.alerts;
    const allCount = alerts.length;
    const activeCount = alerts.filter(a => (a.status || 'active') === 'active').length;
    const pausedCount = alerts.filter(a => a.status === 'paused').length;
    
    // Update count displays
    const elements = {
        'all-count': allCount,
        'active-count': activeCount,
        'paused-count': pausedCount,
        'total-alerts-count': allCount
    };
    
    Object.entries(elements).forEach(([id, count]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = count;
        }
    });
    
    console.log('📊 Filter counts updated:', { allCount, activeCount, pausedCount });
}

/**
 * View alert details in modal/panel
 */
export function viewAlert(alertId) {
    const alert = AlertsState.alerts.find(a => a.id == alertId);
    if (!alert) {
        console.warn('Alert not found:', alertId);
        return;
    }
    
    // Close any open menus
    document.querySelectorAll('[id^="menu-"]').forEach(menu => {
        menu.classList.add('hidden');
    });
    
    console.log('📄 Viewing alert details:', alert);
    
    // You can expand this to show a details modal
    // For now, just log the details
    alert('Alert Details:\n' + 
          `Name: ${alert.name}\n` +
          `Budget: $${alert.threshold_amount || 'N/A'}\n` +
          `Email: ${alert.email || 'Not set'}\n` +
          `Status: ${alert.status || 'active'}\n` +
          `Cluster: ${alert.cluster_name || 'All clusters'}`);
}

/**
 * Setup filter buttons if they don't exist
 */
export function setupFilterButtons() {
    const alertsContainer = document.getElementById('alerts-list-container');
    if (alertsContainer && !document.getElementById('alerts-filter-buttons')) {
        const filterButtonsHtml = `
            <div id="alerts-filter-buttons" class="mb-3">
                <div class="btn-group" role="group" aria-label="Alert filters">
                    <button type="button" class="btn btn-outline-primary active filter-btn" 
                            onclick="filterAlerts('all')">
                        <i class="fas fa-list me-1"></i>All (<span id="all-count">0</span>)
                    </button>
                    <button type="button" class="btn btn-outline-success filter-btn" 
                            onclick="filterAlerts('active')">
                        <i class="fas fa-play me-1"></i>Active (<span id="active-count">0</span>)
                    </button>
                    <button type="button" class="btn btn-outline-warning filter-btn" 
                            onclick="filterAlerts('paused')">
                        <i class="fas fa-pause me-1"></i>Paused (<span id="paused-count">0</span>)
                    </button>
                </div>
            </div>
        `;
        
        alertsContainer.insertAdjacentHTML('beforebegin', filterButtonsHtml);
    }
    
    // Initial count update
    updateFilterCountsDisplay();
}

/**
 * Initialize UI interactions with simple menu handling
 */
export function initializeUIInteractions() {
    setupFilterButtons();
    
    // Set up outside click handlers to close menus
    document.addEventListener('click', function(event) {
        // Close simple menus when clicking outside
        if (!event.target.closest('[id^="simple-menu-"]') && 
            !event.target.closest('button[onclick*="toggleSimpleMenu"]') &&
            !event.target.closest('.dropdown button')) {
            document.querySelectorAll('[id^="simple-menu-"]').forEach(menu => {
                menu.style.display = 'none';
            });
        }
        
        // Handle dropdown item clicks
        if (event.target.closest('.dropdown-item')) {
            event.preventDefault();
            
            // Close the menu after clicking an item
            const menu = event.target.closest('[id^="simple-menu-"]');
            if (menu) {
                menu.style.display = 'none';
            }
        }
    });
    
    console.log('✅ UI interactions initialized with tab conflict resolution');
}

// Keep the legacy toggleAlertMenu function for backward compatibility
export const toggleAlertMenu = toggleSimpleMenu;

// Export for global use
window.filterAlerts = filterAlerts;
window.switchAlertsTab = switchAlertsTab;
window.toggleSimpleMenu = toggleSimpleMenu;
window.closeMenu = closeMenu;
window.handleToggleAlert = handleToggleAlert;