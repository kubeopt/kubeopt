/*
 * User Menu JavaScript
 * ===================
 * Handles user dropdown menu functionality across all pages
 */

// Global function - needed for inline onclick handlers
window.toggleUserMenu = function() {
    console.log('🔹 toggleUserMenu called!');
    const menu = document.getElementById('userDropdownMenu');
    console.log('🔹 Menu element found:', !!menu);
    
    if (!menu) {
        console.error('❌ User dropdown menu not found!');
        return;
    }

    // Pure Tailwind implementation - toggle hidden class
    const isVisible = !menu.classList.contains('hidden');
    console.log('🔹 Menu currently visible:', isVisible);
    
    if (isVisible) {
        // Hide menu
        menu.classList.add('hidden');
        console.log('✅ Hiding menu');
    } else {
        // Show menu
        menu.classList.remove('hidden');
        console.log('✅ Showing menu');
    }
};

// Test that the function is available
console.log('🔹 User menu script loaded, toggleUserMenu available:', typeof window.toggleUserMenu);

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing user menu...');
    initializeUserMenu();
});

// Also try to initialize on window load as backup
window.addEventListener('load', function() {
    console.log('Window loaded, re-initializing user menu...');
    setTimeout(initializeUserMenu, 100);
});

function initializeUserMenu() {
    try {
        console.log('Setting up user menu handlers...');
        setupOutsideClickClose();
        setupKeyboardNavigation();
        
        // Test if menu exists
        const menu = document.getElementById('userDropdownMenu');
        console.log('User dropdown menu found:', !!menu);
        
        if (menu) {
            console.log('Menu classes:', menu.className);
            console.log('Menu style:', menu.style.cssText);
        }
        
        // Find user buttons
        const allButtons = document.querySelectorAll('div[onclick*="toggleUserMenu"], .user-menu-trigger, [class*="bg-blue-600"]');
        console.log('Found potential user buttons:', allButtons.length);
        
        allButtons.forEach((btn, i) => {
            console.log(`Button ${i}:`, btn.tagName, btn.className);
        });
        
        console.log('User menu initialization completed');
    } catch (error) {
        console.error('Error initializing user menu:', error);
    }
}


function setupOutsideClickClose() {
    // Close user menu when clicking outside
    document.addEventListener('click', function(event) {
        const userMenu = document.getElementById('userDropdownMenu');
        if (!userMenu) return;
        
        // Check if click was on user button or menu
        const userButton = document.querySelector('.user-menu-trigger') || 
                          document.querySelector('.w-10.h-10.bg-gradient-to-r') ||
                          document.querySelector('[onclick*="toggleUserMenu"]');
        
        if (userButton && (userButton.contains(event.target) || userMenu.contains(event.target))) {
            return; // Don't close if clicking on button or menu
        }
        
        // Close menu
        if (userMenu.classList.contains('dropdown-menu')) {
            // Bootstrap
            userMenu.classList.add('d-none');
            userMenu.style.display = 'none';
        } else {
            // Tailwind
            userMenu.classList.add('hidden');
        }
    });
}

function setupKeyboardNavigation() {
    // Close user menu when pressing Escape
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const userMenu = document.getElementById('userDropdownMenu');
            if (userMenu) {
                if (userMenu.classList.contains('dropdown-menu')) {
                    // Bootstrap
                    userMenu.classList.add('d-none');
                    userMenu.style.display = 'none';
                } else {
                    // Tailwind
                    userMenu.classList.add('hidden');
                }
            }
        }
    });
}

