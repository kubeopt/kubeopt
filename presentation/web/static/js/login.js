/**
 * Login Page JavaScript
 * Handles login form functionality, password toggle, and form validation
 */

class LoginPage {
    constructor() {
        this.loginForm = null;
        this.passwordInput = null;
        this.toggleButton = null;
        this.init();
    }

    init() {
        this.bindEventListeners();
    }

    bindEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.onDOMContentLoaded();
        });
    }

    onDOMContentLoaded() {
        this.loginForm = document.querySelector('.login-form');
        this.passwordInput = document.getElementById('password');
        this.toggleButton = document.querySelector('.toggle-password');

        this.setupFormSubmission();
        this.setupKeyboardNavigation();
        this.setupPasswordToggle();
        this.autoFocusUsername();
    }

    setupPasswordToggle() {
        if (this.toggleButton) {
            this.toggleButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.togglePassword();
            });
        }
    }

    // Password Visibility Toggle
    togglePassword() {
        if (!this.passwordInput) return;

        const toggleIcon = document.querySelector('.toggle-password i');
        
        if (this.passwordInput.type === 'password') {
            this.passwordInput.type = 'text';
            if (toggleIcon) {
                toggleIcon.className = 'fas fa-eye-slash';
            }
        } else {
            this.passwordInput.type = 'password';
            if (toggleIcon) {
                toggleIcon.className = 'fas fa-eye';
            }
        }
    }

    // Form Submission Handling
    setupFormSubmission() {
        if (!this.loginForm) return;

        this.loginForm.addEventListener('submit', (e) => {
            this.handleFormSubmission(e);
        });
    }

    handleFormSubmission(event) {
        const button = this.loginForm.querySelector('.login-button');
        
        if (button) {
            button.classList.add('loading');
            
            // Remove loading state if form submission fails
            setTimeout(() => {
                button.classList.remove('loading');
            }, 5000);
        }

        // Validate form before submission
        if (!this.validateForm()) {
            event.preventDefault();
            if (button) {
                button.classList.remove('loading');
            }
        }
    }

    // Form Validation
    validateForm() {
        const username = document.getElementById('username');
        const password = document.getElementById('password');
        
        let isValid = true;

        // Clear previous error states
        this.clearFormErrors();

        // Validate username
        if (!username || !username.value.trim()) {
            this.showFieldError(username, 'Username is required');
            isValid = false;
        }

        // Validate password
        if (!password || !password.value.trim()) {
            this.showFieldError(password, 'Password is required');
            isValid = false;
        } else if (password.value.length < 6) {
            this.showFieldError(password, 'Password must be at least 6 characters');
            isValid = false;
        }

        return isValid;
    }

    showFieldError(field, message) {
        if (!field) return;

        field.classList.add('error');
        
        // Create error message element if it doesn't exist
        const wrapper = field.closest('.input-wrapper') || field.closest('.form-group');
        if (wrapper && !wrapper.querySelector('.error-message')) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = message;
            wrapper.appendChild(errorDiv);
        }
    }

    clearFormErrors() {
        // Remove error classes
        document.querySelectorAll('.form-input.error').forEach(input => {
            input.classList.remove('error');
        });

        // Remove error messages
        document.querySelectorAll('.error-message').forEach(error => {
            error.remove();
        });
    }

    // Auto-focus and Keyboard Navigation
    autoFocusUsername() {
        const usernameField = document.getElementById('username');
        if (usernameField) {
            // Small delay to ensure the page is fully loaded
            setTimeout(() => {
                usernameField.focus();
            }, 100);
        }
    }

    setupKeyboardNavigation() {
        const formInputs = document.querySelectorAll('.form-input');
        
        formInputs.forEach(input => {
            input.addEventListener('keydown', (e) => {
                this.handleKeyNavigation(e);
            });
        });
    }

    handleKeyNavigation(event) {
        if (event.key === 'Enter') {
            const form = event.target.closest('form');
            const inputs = Array.from(form.querySelectorAll('.form-input'));
            const currentIndex = inputs.indexOf(event.target);
            
            if (currentIndex < inputs.length - 1) {
                // Focus next input
                event.preventDefault();
                inputs[currentIndex + 1].focus();
            } else {
                // Submit form
                form.submit();
            }
        }
    }

    // Utility Methods
    showMessage(message, type = 'info') {
        // Create a message element and show it
        const messageDiv = document.createElement('div');
        messageDiv.className = `login-message login-message-${type}`;
        messageDiv.textContent = message;

        const loginCard = document.querySelector('.login-card');
        if (loginCard) {
            loginCard.insertBefore(messageDiv, loginCard.firstChild);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }
    }

    // Loading state management
    setLoading(loading) {
        const button = document.querySelector('.login-button');
        if (button) {
            if (loading) {
                button.classList.add('loading');
                button.disabled = true;
            } else {
                button.classList.remove('loading');
                button.disabled = false;
            }
        }
    }

    // Form data collection
    getFormData() {
        return {
            username: document.getElementById('username')?.value.trim() || '',
            password: document.getElementById('password')?.value || '',
            remember: document.getElementById('remember')?.checked || false
        };
    }

    // Reset form
    resetForm() {
        if (this.loginForm) {
            this.loginForm.reset();
            this.clearFormErrors();
            this.autoFocusUsername();
        }
    }
}

// Initialize the login page when DOM is loaded
let loginPage;

document.addEventListener('DOMContentLoaded', function() {
    loginPage = new LoginPage();
});

// Global functions for template onclick handlers
function togglePassword() {
    loginPage?.togglePassword();
}