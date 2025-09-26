/*
 * User Menu JavaScript
 * ===================
 * Handles user dropdown menu functionality across all pages
 */

// Global function - needed for inline onclick handlers
window.toggleUserMenu = function(event) {
    logDebug('🔹 toggleUserMenu called!', event);
    
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    const menu = document.getElementById('userDropdownMenu');
    logDebug('🔹 Menu element found:', !!menu);
    
    if (!menu) {
        logError('❌ User dropdown menu not found!');
        return false;
    }

    // Pure Tailwind implementation - toggle hidden class
    const isVisible = !menu.classList.contains('hidden');
    logDebug('🔹 Menu currently visible:', isVisible);
    logDebug('🔹 Menu classes:', menu.className);
    
    if (isVisible) {
        // Hide menu
        menu.classList.add('hidden');
        logDebug('✅ Hiding menu');
    } else {
        // Show menu
        menu.classList.remove('hidden');
        logDebug('✅ Showing menu');
    }
    
    return false;
};

// Test that the function is available
logDebug('🔹 User menu script loaded, toggleUserMenu available:', typeof window.toggleUserMenu);

document.addEventListener('DOMContentLoaded', function() {
    logDebug('DOM loaded, initializing user menu...');
    initializeUserMenu();
});

// Also try to initialize on window load as backup
window.addEventListener('load', function() {
    logDebug('Window loaded, re-initializing user menu...');
    setTimeout(initializeUserMenu, 100);
});

function initializeUserMenu() {
    try {
        logDebug('Setting up user menu handlers...');
        setupOutsideClickClose();
        setupKeyboardNavigation();
        
        // Test if menu exists
        const menu = document.getElementById('userDropdownMenu');
        logDebug('User dropdown menu found:', !!menu);
        
        if (menu) {
            logDebug('Menu classes:', menu.className);
            logDebug('Menu style:', menu.style.cssText);
        }
        
        // Find user buttons and add event listeners as backup
        const allButtons = document.querySelectorAll('div[onclick*="toggleUserMenu"], .user-menu-trigger, [class*="bg-blue-600"], [class*="bg-gradient-to-r"]');
        logDebug('Found potential user buttons:', allButtons.length);
        
        allButtons.forEach((btn, i) => {
            logDebug(`Button ${i}:`, btn.tagName, btn.className);
            
            // Add click event listener as backup to onclick
            btn.addEventListener('click', function(event) {
                logDebug('Event listener triggered for button', i);
                window.toggleUserMenu(event);
            });
        });
        
        
        logDebug('User menu initialization completed');
    } catch (error) {
        logError('Error initializing user menu:', error);
    }
}


function setupOutsideClickClose() {
    // Close user menu when clicking outside
    document.addEventListener('click', function(event) {
        const userMenu = document.getElementById('userDropdownMenu');
        if (!userMenu) return;
        
        // Check if click was on user button or menu
        const userButton = document.querySelector('[onclick*="toggleUserMenu"]');
        
        if (userButton && (userButton.contains(event.target) || userMenu.contains(event.target))) {
            return; // Don't close if clicking on button or menu
        }
        
        // Close menu using Tailwind classes
        userMenu.classList.add('hidden');
    });
}

function setupKeyboardNavigation() {
    // Close user menu when pressing Escape
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const userMenu = document.getElementById('userDropdownMenu');
            if (userMenu) {
                // Close menu using Tailwind classes
                userMenu.classList.add('hidden');
            }
        }
    });
}


