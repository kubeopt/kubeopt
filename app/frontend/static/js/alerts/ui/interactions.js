// frontend/static/js/alerts/ui/interactions.js

import { AlertsState, StateActions } from '../core/state.js';
import { displayAlerts } from './display.js';

/**
 * FIXED: Enhanced UI interaction functions with proper menu handling
 */

/**
 * FIXED: Enhanced filter alerts with proper state management
 */
export function filterAlerts(filter) {
    console.log(`🔍 Enhanced filtering alerts by: ${filter}`);
    
    // Update the current filter in state
    AlertsState.currentFilter = filter;
    
    // Update button states with animations
    const filterButtons = document.querySelectorAll('[onclick*="filterAlerts"], .filter-btn');
    filterButtons.forEach(btn => {
        btn.classList.remove('active', 'btn-primary');
        btn.classList.add('btn-outline-primary');
        btn.style.transform = 'scale(1)';
    });
    
    // Activate selected filter button with animation
    const activeBtn = document.querySelector(`[onclick="filterAlerts('${filter}')"]`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'btn-primary');
        activeBtn.classList.remove('btn-outline-primary');
        activeBtn.style.transform = 'scale(1.05)';
        setTimeout(() => {
            activeBtn.style.transform = 'scale(1)';
        }, 200);
    }
    
    // Enhanced filter with smooth animations
    const alertRows = document.querySelectorAll('.alert-row');
    let visibleCount = 0;
    
    alertRows.forEach((row, index) => {
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
            // Smooth show animation
            row.style.display = '';
            row.style.opacity = '0';
            row.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                row.style.transition = 'all 0.3s ease';
                row.style.opacity = '1';
                row.style.transform = 'translateY(0)';
            }, index * 50); // Stagger the animations
            
            visibleCount++;
        } else {
            // Smooth hide animation
            row.style.transition = 'all 0.2s ease';
            row.style.opacity = '0';
            row.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                row.style.display = 'none';
            }, 200);
        }
    });
    
    // Update filter counts with animation
    updateFilterCountsDisplay();
    
    console.log(`✅ Enhanced filter applied: ${filter}, showing ${visibleCount} alerts out of ${alertRows.length} total`);
}

/**
 * FIXED: Handle toggle switch for alert pause/resume
 */
export function handleToggleAlert(alertId, isChecked) {
    console.log(`🔄 Toggling alert ${alertId} to ${isChecked ? 'active' : 'paused'}`);
    
    const action = isChecked ? 'resume' : 'pause';
    const newStatus = action === 'pause' ? 'paused' : 'active';
    
    // Find the alert row and update immediately with animation
    const row = document.querySelector(`[data-alert-id="${alertId}"]`);
    if (row) {
        // Add subtle animation to indicate change
        row.style.transition = 'all 0.3s ease';
        row.style.transform = 'scale(1.02)';
        
        // Update the row's data attribute immediately
        row.dataset.status = newStatus;
        
        // Update the status badge immediately with animation
        const badge = row.querySelector('.badge');
        if (badge) {
            badge.style.transition = 'all 0.3s ease';
            badge.style.transform = 'scale(1.1)';
            
            if (isChecked) {
                badge.className = 'badge bg-success px-2 py-1';
                badge.textContent = 'Active';
            } else {
                badge.className = 'badge bg-secondary px-2 py-1';
                badge.textContent = 'Paused';
            }
            
            // Reset badge animation
            setTimeout(() => {
                badge.style.transform = 'scale(1)';
            }, 300);
        }
        
        // Reset row animation
        setTimeout(() => {
            row.style.transform = 'scale(1)';
        }, 300);
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
 * FIXED: Switch between alerts tabs with proper style preservation
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
    
    // Hide ALL possible tab contents with fade animation
    tabContentSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            element.style.transition = 'opacity 0.2s ease';
            element.style.opacity = '0';
            setTimeout(() => {
                element.style.display = 'none';
                element.classList.add('hidden');
            }, 200);
        });
    });
    
    // Remove active class from ALL possible tab buttons with animation
    tabButtonSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            element.style.transition = 'all 0.3s ease';
            element.classList.remove('active', 'border-blue-500', 'text-blue-600');
            element.classList.add('border-transparent', 'text-gray-500');
            element.style.transform = 'scale(1)';
        });
    });
    
    // Show the specific tab with fade-in animation
    setTimeout(() => {
        if (tabName === 'alerts') {
            // Show alerts content
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
                        element.style.opacity = '0';
                        setTimeout(() => {
                            element.style.opacity = '1';
                        }, 50);
                        alertsContentFound = true;
                        console.log(`✅ Showed alerts content using selector: ${selector}`);
                    }
                });
                if (alertsContentFound) break;
            }
            
            // Activate alerts tab button with scale animation
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
                        element.style.transform = 'scale(1.05)';
                        setTimeout(() => {
                            element.style.transform = 'scale(1)';
                        }, 200);
                        alertsButtonFound = true;
                        console.log(`✅ Activated alerts button using selector: ${selector}`);
                    }
                });
                if (alertsButtonFound) break;
            }
            
        } else if (tabName === 'notifications') {
            // Show notifications content
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
                        element.style.opacity = '0';
                        setTimeout(() => {
                            element.style.opacity = '1';
                        }, 50);
                        notificationsContentFound = true;
                        console.log(`✅ Showed notifications content using selector: ${selector}`);
                    }
                });
                if (notificationsContentFound) break;
            }
            
            // Activate notifications tab button with scale animation
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
                        element.style.transform = 'scale(1.05)';
                        setTimeout(() => {
                            element.style.transform = 'scale(1)';
                        }, 200);
                        notificationsButtonFound = true;
                        console.log(`✅ Activated notifications button using selector: ${selector}`);
                    }
                });
                if (notificationsButtonFound) break;
            }
        }
    }, 250);
    
    console.log(`✅ Successfully switched to ${tabName} tab`);
}

/**
 * FIXED: Enhanced toggle simple alert menu dropdown with better positioning
 */
export function toggleSimpleMenu(alertId) {
    console.log('🔧 Enhanced menu toggle for alert:', alertId);
    
    // Close all other menus first
    document.querySelectorAll('[id^="simple-menu-"]').forEach(menu => {
        if (menu.id !== `simple-menu-${alertId}`) {
            menu.style.display = 'none';
            menu.classList.remove('show');
        }
    });
    
    // Toggle current menu
    const menu = document.getElementById(`simple-menu-${alertId}`);
    const button = document.getElementById(`dropdown-${alertId}`);
    
    if (menu && button) {
        const isHidden = menu.style.display === 'none' || menu.style.display === '';
        
        if (isHidden) {
            // Calculate optimal position
            const buttonRect = button.getBoundingClientRect();
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            const menuWidth = 180; // Approximate menu width
            const menuHeight = 200; // Approximate menu height
            
            // Show menu initially to measure
            menu.style.display = 'block';
            menu.classList.add('show');
            menu.style.position = 'absolute';
            menu.style.zIndex = '1050';
            menu.style.minWidth = `${menuWidth}px`;
            menu.style.backgroundColor = '#fff';
            menu.style.border = '1px solid #dee2e6';
            menu.style.borderRadius = '0.375rem';
            menu.style.boxShadow = '0 0.5rem 1rem rgba(0, 0, 0, 0.15)';
            menu.style.padding = '0.5rem 0';
            menu.style.transition = 'all 0.2s ease';
            menu.style.transform = 'scale(0.95)';
            menu.style.opacity = '0';
            
            // Calculate position
            let top = '100%';
            let right = '0';
            let left = 'auto';
            
            // Check if menu would go off-screen to the right
            if (buttonRect.right - menuWidth < 0) {
                right = 'auto';
                left = '0';
            }
            
            // Check if menu would go off-screen at the bottom
            if (buttonRect.bottom + menuHeight > viewportHeight) {
                top = 'auto';
                menu.style.bottom = '100%';
            }
            
            menu.style.top = top;
            menu.style.right = right;
            menu.style.left = left;
            
            // Animate in
            setTimeout(() => {
                menu.style.transform = 'scale(1)';
                menu.style.opacity = '1';
            }, 50);
            
            console.log('✅ Enhanced menu opened for alert:', alertId);
        } else {
            menu.style.transform = 'scale(0.95)';
            menu.style.opacity = '0';
            setTimeout(() => {
                menu.style.display = 'none';
                menu.classList.remove('show');
            }, 200);
            console.log('✅ Enhanced menu closed for alert:', alertId);
        }
    } else {
        console.error('❌ Menu or button not found for alert:', alertId);
    }
}

/**
 * Close specific menu
 */
export function closeMenu(alertId) {
    const menu = document.getElementById(`simple-menu-${alertId}`);
    if (menu) {
        menu.style.transform = 'scale(0.95)';
        menu.style.opacity = '0';
        setTimeout(() => {
            menu.style.display = 'none';
            menu.classList.remove('show');
        }, 200);
    }
}

/**
 * FIXED: Enhanced filter counts update with animations
 */
function updateFilterCountsDisplay() {
    const alerts = AlertsState.alerts;
    const allCount = alerts.length;
    const activeCount = alerts.filter(a => (a.status || 'active') === 'active').length;
    const pausedCount = alerts.filter(a => a.status === 'paused').length;
    
    // Update count displays with animations
    const elements = {
        'all-count': allCount,
        'active-count': activeCount,
        'paused-count': pausedCount,
        'total-alerts-count': allCount
    };
    
    Object.entries(elements).forEach(([id, count]) => {
        const element = document.getElementById(id);
        if (element) {
            // Animate count change
            element.style.transition = 'all 0.3s ease';
            element.style.transform = 'scale(1.2)';
            element.style.color = '#22c55e';
            element.textContent = count;
            
            setTimeout(() => {
                element.style.transform = 'scale(1)';
                element.style.color = '';
            }, 300);
        }
    });
    
    console.log('📊 Enhanced counts updated:', { allCount, activeCount, pausedCount });
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
    document.querySelectorAll('[id^="simple-menu-"]').forEach(menu => {
        menu.style.display = 'none';
        menu.classList.remove('show');
    });
    
    console.log('📄 Viewing alert details:', alert);
    
    // Enhanced alert display with better formatting
    const details = `Alert Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Name: ${alert.name}
💰 Budget: $${alert.threshold_amount || 'N/A'}
📧 Email: ${alert.email || 'Not set'}
🔄 Status: ${alert.status || 'active'}
🖥️ Cluster: ${alert.cluster_name || 'All clusters'}`;
    
    alert(details);
}

/**
 * FIXED: Enhanced outside click handler
 */
export function setupEnhancedClickHandlers() {
    document.addEventListener('click', function(event) {
        // Enhanced menu closing logic with proper event handling
        if (!event.target.closest('.dropdown') && 
            !event.target.closest('[id^="simple-menu-"]') &&
            !event.target.closest('button[onclick*="toggleSimpleMenu"]') &&
            !event.target.closest('[id^="dropdown-"]')) {
            
            document.querySelectorAll('[id^="simple-menu-"]').forEach(menu => {
                menu.style.transform = 'scale(0.95)';
                menu.style.opacity = '0';
                setTimeout(() => {
                    menu.style.display = 'none';
                    menu.classList.remove('show');
                }, 200);
            });
        }
        
        // Handle dropdown item clicks with smooth animations
        if (event.target.closest('.dropdown-item')) {
            event.preventDefault();
            
            // Add click animation
            const item = event.target.closest('.dropdown-item');
            item.style.transition = 'transform 0.1s ease';
            item.style.transform = 'scale(0.95)';
            setTimeout(() => {
                item.style.transform = 'scale(1)';
            }, 100);
            
            // Close the menu after clicking an item with delay for animation
            const menu = event.target.closest('[id^="simple-menu-"]');
            if (menu) {
                setTimeout(() => {
                    menu.style.transform = 'scale(0.95)';
                    menu.style.opacity = '0';
                    setTimeout(() => {
                        menu.style.display = 'none';
                        menu.classList.remove('show');
                    }, 200);
                }, 150);
            }
        }
    });
    
    console.log('✅ Enhanced click handlers setup');
}

/**
 * Initialize enhanced UI interactions
 */
export function initializeUIInteractions() {
    setupEnhancedClickHandlers();
    
    console.log('✅ Enhanced UI interactions initialized with animations and improved UX');
}

// Keep the legacy toggleAlertMenu function for backward compatibility
export const toggleAlertMenu = toggleSimpleMenu;

// Export for global use
window.filterAlerts = filterAlerts;
window.switchAlertsTab = switchAlertsTab;
window.toggleSimpleMenu = toggleSimpleMenu;
window.closeMenu = closeMenu;
window.handleToggleAlert = handleToggleAlert;
window.viewAlert = viewAlert;
window.setupEnhancedClickHandlers = setupEnhancedClickHandlers;