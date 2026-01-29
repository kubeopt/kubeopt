/**
 * AKS Cost Optimizer - UI Module
 * Handles general UI functionality and interactions
 */

window.UI = (function() {
    'use strict';
    
    /**
     * Initialize UI components
     */
    function init() {
        window.logger.debug('Initializing UI components...');
        
        initSidebar();
        initTheme();
        initTooltips();
        initDateDisplay();
        
        window.logger.debug('UI components initialized');
    }

    /**
     * Initialize sidebar functionality
     */
    function initSidebar() {
        // Sidebar toggle functionality removed
        
        // Auto-collapse on mobile
        if (window.innerWidth <= 768) {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.classList.add('collapsed');
            }
        }
        
        // Handle window resize
        window.addEventListener('resize', window.Utils.debounce(() => {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar && window.innerWidth <= 768) {
                sidebar.classList.add('collapsed');
            }
        }, 250));
    }


    /**
     * Initialize theme functionality
     */
    function initTheme() {
        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        setTheme(savedTheme);
        
        // Update theme toggle icon
        updateThemeIcon(savedTheme);
    }

    /**
     * Set theme
     */
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        updateThemeIcon(theme);
        
        // Recreate charts to update theme colors - this will be handled automatically by MutationObserver in chart-manager.js
    }

    /**
     * Toggle theme
     */
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
    }

    /**
     * Update theme toggle icon
     */
    function updateThemeIcon(theme) {
        const themeToggle = document.querySelector('.theme-toggle i');
        if (themeToggle) {
            themeToggle.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        }
    }

    /**
     * Show toast notification
     */
    function showToast(message, type = 'info', duration = 5000) {
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.toast');
        existingToasts.forEach(toast => toast.remove());
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} bounce-in`;
        toast.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" class="toast-close">&times;</button>
        `;
        
        // Add toast styles if not already present
        if (!document.querySelector('#toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 12px 16px;
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    font-weight: 500;
                    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                    z-index: 1000;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    max-width: 400px;
                }
                .toast-info { background: #3b82f6; }
                .toast-success { background: #10b981; }
                .toast-warning { background: #f59e0b; }
                .toast-error { background: #ef4444; }
                .toast-close {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 16px;
                    cursor: pointer;
                    padding: 0;
                    margin-left: auto;
                }
            `;
            document.head.appendChild(style);
        }
        
        // Add to page
        document.body.appendChild(toast);
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.classList.add('fade-out');
                    setTimeout(() => toast.remove(), 300);
                }
            }, duration);
        }
    }

    /**
     * Initialize tooltips
     */
    function initTooltips() {
        const elementsWithTooltips = document.querySelectorAll('[title]');
        elementsWithTooltips.forEach(element => {
            element.addEventListener('mouseenter', showTooltip);
            element.addEventListener('mouseleave', hideTooltip);
        });
    }

    /**
     * Show tooltip
     */
    function showTooltip(event) {
        const element = event.target;
        const title = element.getAttribute('title');
        
        if (!title) return;
        
        // Create tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = title;
        tooltip.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            white-space: nowrap;
            z-index: 1000;
            pointer-events: none;
        `;
        
        document.body.appendChild(tooltip);
        
        // Position tooltip
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
        
        // Store reference
        element._tooltip = tooltip;
        
        // Hide original title
        element.setAttribute('data-original-title', title);
        element.removeAttribute('title');
    }

    /**
     * Hide tooltip
     */
    function hideTooltip(event) {
        const element = event.target;
        
        if (element._tooltip) {
            element._tooltip.remove();
            element._tooltip = null;
        }
        
        // Restore original title
        const originalTitle = element.getAttribute('data-original-title');
        if (originalTitle) {
            element.setAttribute('title', originalTitle);
            element.removeAttribute('data-original-title');
        }
    }

    /**
     * Initialize date display
     */
    function initDateDisplay() {
        const dateEl = document.getElementById('current-date');
        if (dateEl) {
            updateDateDisplay();
            
            // Update every minute
            setInterval(updateDateDisplay, 60000);
        }
    }

    /**
     * Update date display
     */
    function updateDateDisplay() {
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

    /**
     * Show loading state for element
     */
    function showLoading(elementId, message = 'Loading...') {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="loading-state">
                    <div class="loading-spinner"></div>
                    <span>${message}</span>
                </div>
            `;
            element.classList.add('loading');
        }
    }

    /**
     * Hide loading state for element
     */
    function hideLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.remove('loading');
        }
    }

    /**
     * Show modal
     */
    function showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('fade-in');
            
            // Focus first input
            const firstInput = modal.querySelector('input, textarea, select');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        }
    }

    /**
     * Hide modal
     */
    function hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('fade-out');
            setTimeout(() => {
                modal.classList.add('hidden');
                modal.classList.remove('fade-in', 'fade-out');
            }, 300);
        }
    }

    /**
     * Handle global keyboard shortcuts
     */
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Escape key - close modals
            if (event.key === 'Escape') {
                const visibleModal = document.querySelector('.modal:not(.hidden)');
                if (visibleModal) {
                    hideModal(visibleModal.id);
                }
            }
            
            // Ctrl/Cmd + R - refresh dashboard
            if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
                event.preventDefault();
                if (window.Dashboard && window.Dashboard.refresh) {
                    window.Dashboard.refresh();
                }
            }
        });
    }

    // Public API
    return {
        init,
        toggleTheme,
        setTheme,
        showToast,
        showLoading,
        hideLoading,
        showModal,
        hideModal,
        initKeyboardShortcuts
    };
})();

// Make functions globally available for compatibility
window.showToast = window.UI.showToast;
window.toggleTheme = window.UI.toggleTheme;