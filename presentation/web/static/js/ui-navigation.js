/**
 * ============================================================================
 * AKS COST INTELLIGENCE - UI NAVIGATION AND TAB MANAGEMENT
 * ============================================================================
 * Tab switching, navigation, and UI state management
 * ============================================================================
 */

import { showNotification } from './notifications.js';
import { AppState } from './config.js';

/**
 * Switches to specified tab with enhanced navigation
 */
export function switchToTab(selector) {
    
    
    try {
        // Method 1: Find and click the tab button
        const tabButton = document.querySelector(`[data-bs-target="${selector}"]`);
        if (tabButton) {
            tabButton.click();
            
            updateAppState('smoothTransitions.currentTab', selector);
            return;
        }
        
        // Method 2: Manual tab switching for Bootstrap tabs
        if (selector === '#dashboard') {
            switchToDashboard();
            return;
        }
        
        if (selector === '#analysis') {
            switchToAnalysis();
            return;
        }
        
        if (selector === '#implementation') {
            switchToImplementation();
            return;
        }
        
        // Method 3: Generic tab switching
        const targetTab = document.querySelector(selector);
        if (targetTab) {
            // Hide all tabs
            document.querySelectorAll('.tab-pane').forEach(tab => {
                tab.classList.remove('show', 'active');
            });
            
            // Show target tab
            targetTab.classList.add('show', 'active');
            
            // Update navigation
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            
            const navLink = document.querySelector(`[data-bs-target="${selector}"]`);
            if (navLink) {
                navLink.classList.add('active');
            }
            
            
            updateAppState('smoothTransitions.currentTab', selector);
            return;
        }
        
        console.log('⚠️ Could not switch tab - target not found');
        
    } catch (error) {
        console.error('❌ Error switching tab:', error);
        showNotification('Failed to switch tab', 'error');
    }
}

/**
 * Switch to dashboard tab with specific handling
 */
function switchToDashboard() {
    const analysisTab = document.getElementById('analysis');
    const dashboardTab = document.getElementById('dashboard');
    const analysisTabBtn = document.getElementById('analysis-tab');
    const dashboardTabBtn = document.getElementById('dashboard-tab');
    
    if (analysisTab && dashboardTab) {
        // Hide analysis tab
        analysisTab.classList.remove('show', 'active');
        if (analysisTabBtn) analysisTabBtn.classList.remove('active');
        
        // Show dashboard tab
        dashboardTab.classList.add('show', 'active');
        if (dashboardTabBtn) dashboardTabBtn.classList.add('active');
        
        
        
        updateAppState('smoothTransitions.currentTab', '#dashboard');
    }
}

/**
 * Switch to analysis tab with specific handling
 */
function switchToAnalysis() {
    const analysisTab = document.getElementById('analysis');
    const dashboardTab = document.getElementById('dashboard');
    const analysisTabBtn = document.getElementById('analysis-tab');
    const dashboardTabBtn = document.getElementById('dashboard-tab');
    
    if (analysisTab && dashboardTab) {
        // Hide dashboard tab
        dashboardTab.classList.remove('show', 'active');
        if (dashboardTabBtn) dashboardTabBtn.classList.remove('active');
        
        // Show analysis tab
        analysisTab.classList.add('show', 'active');
        if (analysisTabBtn) analysisTabBtn.classList.add('active');
        
        
        updateAppState('smoothTransitions.currentTab', '#analysis');
    }
}

/**
 * Switch to implementation tab with specific handling
 */
function switchToImplementation() {
    const implementationTab = document.getElementById('implementation');
    if (implementationTab) {
        // Switch tab
        switchToTab('#implementation');
        
        
        updateAppState('smoothTransitions.currentTab', '#implementation');
        updateAppState('smoothTransitions.implementationLoaded', true);
    }
}

/**
 * Enhanced navigation with smooth transitions
 */
export function navigateToSection(sectionId, tabId) {
    return new Promise((resolve) => {
        // Set transition state
        updateAppState('smoothTransitions.isTransitioning', true);
        
        // Switch to tab first
        if (tabId) {
            switchToTab(tabId);
        }
        
        // Wait for tab transition
        setTimeout(() => {
            // Scroll to section
            const section = document.getElementById(sectionId);
            if (section) {
                section.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Highlight section briefly
                section.style.transition = 'all 0.3s ease';
                section.style.backgroundColor = 'rgba(0, 123, 255, 0.1)';
                section.style.borderRadius = '8px';
                
                setTimeout(() => {
                    section.style.backgroundColor = '';
                    section.style.borderRadius = '';
                }, 2000);
            }
            
            updateAppState('smoothTransitions.isTransitioning', false);
            resolve();
        }, 500);
    });
}

/**
 * Breadcrumb navigation management
 */
export function updateBreadcrumb(items) {
    const breadcrumbContainer = document.querySelector('.breadcrumb');
    if (!breadcrumbContainer) return;
    
    const breadcrumbHTML = items.map((item, index) => {
        const isLast = index === items.length - 1;
        
        if (isLast) {
            return `<li class="breadcrumb-item active" aria-current="page">${item.text}</li>`;
        } else {
            return `<li class="breadcrumb-item">
                ${item.href ? `<a href="${item.href}">${item.text}</a>` : item.text}
            </li>`;
        }
    }).join('');
    
    breadcrumbContainer.innerHTML = breadcrumbHTML;
}

/**
 * Page title management
 */
export function updatePageTitle(title, subtitle = '') {
    // Update document title
    document.title = title + (subtitle ? ` - ${subtitle}` : '') + ' | AKS Cost Intelligence';
    
    // Update page header if it exists
    const pageHeader = document.querySelector('.page-header h1, .page-title');
    if (pageHeader) {
        pageHeader.textContent = title;
    }
    
    const pageSubtitle = document.querySelector('.page-subtitle');
    if (pageSubtitle && subtitle) {
        pageSubtitle.textContent = subtitle;
    }
}

/**
 * Navigation state management
 */
export function setActiveNavigation(activeItem) {
    // Remove active class from all nav items
    document.querySelectorAll('.nav-link, .navbar-nav .nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Add active class to specified item
    const activeNav = document.querySelector(`[data-nav="${activeItem}"], [href*="${activeItem}"]`);
    if (activeNav) {
        activeNav.classList.add('active');
    }
    
    // Update sidebar navigation if it exists
    const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
    sidebarLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === activeItem || link.getAttribute('data-target') === activeItem) {
            link.classList.add('active');
        }
    });
}

/**
 * Responsive navigation handling
 */
export function handleResponsiveNavigation() {
    const navbar = document.querySelector('.navbar-collapse');
    const navToggler = document.querySelector('.navbar-toggler');
    
    if (!navbar || !navToggler) return;
    
    // Close mobile menu when clicking nav links
    navbar.addEventListener('click', (event) => {
        if (event.target.classList.contains('nav-link')) {
            // Close mobile menu
            if (navbar.classList.contains('show')) {
                navToggler.click();
            }
        }
    });
    
    // Handle window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            // Auto-close mobile menu on desktop
            if (window.innerWidth >= 992 && navbar.classList.contains('show')) {
                navToggler.click();
            }
        }, 250);
    });
}

/**
 * Tab navigation with history support
 */
export function initializeTabNavigation() {
    
    
    // Handle browser back/forward buttons
    window.addEventListener('popstate', (event) => {
        if (event.state && event.state.tab) {
            switchToTab(event.state.tab);
        }
    });
    
    // Track tab changes in browser history
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('shown.bs.tab', (event) => {
            const tabTarget = event.target.getAttribute('data-bs-target');
            const tabName = tabTarget.replace('#', '');
            
            // Update URL without page reload
            const currentUrl = new URL(window.location);
            currentUrl.searchParams.set('tab', tabName);
            
            // Push to browser history
            history.pushState({ tab: tabTarget }, '', currentUrl.toString());
            
            // Update page title based on active tab
            updatePageTitleForTab(tabName);
            
            console.log(`📑 Tab changed to: ${tabName}`);
        });
    });
    
    // Initialize based on URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    if (tabParam) {
        const tabSelector = `#${tabParam}`;
        setTimeout(() => switchToTab(tabSelector), 100);
    }
}

/**
 * Update page title based on active tab
 */
function updatePageTitleForTab(tabName) {
    const tabTitles = {
        'dashboard': 'Cost Dashboard',
        'analysis': 'Cost Analysis', 
        'implementation': 'Implementation Plan',
        'optimization': 'Optimization Recommendations',
        'reports': 'Reports & Analytics'
    };
    
    const title = tabTitles[tabName] || 'Dashboard';
    updatePageTitle(title);
}

/**
 * Keyboard navigation support
 */
export function initializeKeyboardNavigation() {
    console.log('⌨️ Initializing keyboard navigation');
    
    document.addEventListener('keydown', (event) => {
        // Only handle if no input is focused
        if (document.activeElement.tagName === 'INPUT' || 
            document.activeElement.tagName === 'TEXTAREA') {
            return;
        }
        
        // Tab navigation with Ctrl+Number
        if (event.ctrlKey && event.key >= '1' && event.key <= '9') {
            event.preventDefault();
            const tabIndex = parseInt(event.key) - 1;
            const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
            
            if (tabButtons[tabIndex]) {
                tabButtons[tabIndex].click();
                showNotification(`Switched to ${tabButtons[tabIndex].textContent.trim()}`, 'info', 1500);
            }
        }
        
        // Navigation with arrow keys (when holding Ctrl)
        if (event.ctrlKey && (event.key === 'ArrowLeft' || event.key === 'ArrowRight')) {
            event.preventDefault();
            navigateTabDirection(event.key === 'ArrowLeft' ? -1 : 1);
        }
    });
}

/**
 * Navigate tabs in specified direction
 */
function navigateTabDirection(direction) {
    const tabButtons = Array.from(document.querySelectorAll('[data-bs-toggle="tab"]'));
    const activeTab = document.querySelector('[data-bs-toggle="tab"].active, [data-bs-toggle="tab"][aria-selected="true"]');
    
    if (!activeTab || tabButtons.length === 0) return;
    
    const currentIndex = tabButtons.indexOf(activeTab);
    let newIndex = currentIndex + direction;
    
    // Wrap around
    if (newIndex < 0) newIndex = tabButtons.length - 1;
    if (newIndex >= tabButtons.length) newIndex = 0;
    
    tabButtons[newIndex].click();
}

/**
 * Loading state management for navigation
 */
export function setNavigationLoadingState(isLoading, targetTab = null) {
    const navLinks = targetTab ? 
        document.querySelectorAll(`[data-bs-target="${targetTab}"]`) :
        document.querySelectorAll('.nav-link[data-bs-toggle="tab"]');
    
    navLinks.forEach(link => {
        if (isLoading) {
            link.classList.add('loading');
            link.style.pointerEvents = 'none';
            
            const originalText = link.innerHTML;
            link.setAttribute('data-original-text', originalText);
            link.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>' + link.textContent.trim();
        } else {
            link.classList.remove('loading');
            link.style.pointerEvents = '';
            
            const originalText = link.getAttribute('data-original-text');
            if (originalText) {
                link.innerHTML = originalText;
                link.removeAttribute('data-original-text');
            }
        }
    });
}

/**
 * Progressive enhancement for navigation
 */
export function enhanceNavigation() {
    // Add smooth scrolling to internal links
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', (event) => {
            const target = document.querySelector(link.getAttribute('href'));
            if (target) {
                event.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add loading states to external links
    document.querySelectorAll('a[href^="http"], a[href^="/"], a[target="_blank"]').forEach(link => {
        link.addEventListener('click', () => {
            link.style.opacity = '0.7';
            setTimeout(() => {
                link.style.opacity = '';
            }, 1000);
        });
    });
}

/**
 * Initialize all navigation features
 */
export function initializeNavigation() {
    console.log('🧭 Initializing comprehensive navigation system');
    
    try {
        initializeTabNavigation();
        initializeKeyboardNavigation();
        handleResponsiveNavigation();
        enhanceNavigation();
        
        // Set up navigation event listeners
        setupNavigationEvents();
        
        console.log('✅ Navigation system initialized successfully');
    } catch (error) {
        console.error('❌ Navigation initialization failed:', error);
    }
}

/**
 * Setup navigation event listeners
 */
function setupNavigationEvents() {

    if (window.smoothUIManager) {
        console.log('🔄 Skipping ui-navigation events - smooth.js is active');
        return;
    }
    // Track navigation timing
    const navigationStartTime = performance.now();
    
    document.addEventListener('DOMContentLoaded', () => {
        const loadTime = performance.now() - navigationStartTime;
        console.log(`🧭 Navigation ready in ${Math.round(loadTime)}ms`);
    });
    
    // Handle tab switching events
    document.addEventListener('show.bs.tab', (event) => {
        console.log('🔄 Tab switching:', event.target.getAttribute('data-bs-target'));
        setNavigationLoadingState(true, event.target.getAttribute('data-bs-target'));
    });
    
    document.addEventListener('shown.bs.tab', (event) => {
        console.log('✅ Tab switched:', event.target.getAttribute('data-bs-target'));
        setNavigationLoadingState(false, event.target.getAttribute('data-bs-target'));
    });
}

/**
 * Utility function to update app state
 */
function updateAppState(path, value) {
    const keys = path.split('.');
    let current = AppState;
    
    for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) {
            current[keys[i]] = {};
        }
        current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeNavigation);
} else {
    initializeNavigation();
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.switchToTab = switchToTab;
    window.navigateToSection = navigateToSection;
    window.updateBreadcrumb = updateBreadcrumb;
    window.updatePageTitle = updatePageTitle;
    window.setActiveNavigation = setActiveNavigation;
    window.setNavigationLoadingState = setNavigationLoadingState;
    window.initializeNavigation = initializeNavigation;
}

