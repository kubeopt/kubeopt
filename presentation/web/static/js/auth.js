/*
 * Authentication JavaScript
 * ========================
 * Handles login page functionality and interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-focus on username field
    const usernameField = document.getElementById('username');
    if (usernameField) {
        usernameField.focus();
    }
    
    // Enter key handling for form submission
    document.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const form = document.querySelector('form');
            if (form) {
                form.submit();
            }
        }
    });
    
    // Add loading state to login button
    const loginForm = document.querySelector('form');
    const loginBtn = document.querySelector('.login-btn');
    
    if (loginForm && loginBtn) {
        loginForm.addEventListener('submit', function() {
            loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';
            loginBtn.disabled = true;
        });
    }
    
    // Smooth animations for form elements
    const formInputs = document.querySelectorAll('.form-input');
    formInputs.forEach(function(input) {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
});