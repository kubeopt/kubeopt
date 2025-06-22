/**
 * ============================================================================
 * AKS COST INTELLIGENCE - CSS INJECTION UTILITIES
 * ============================================================================
 * Dynamic CSS injection for enhanced styling and animations
 * ============================================================================
 */

/**
 * Injects necessary CSS for enhanced functionality
 */
export function injectEnhancedCSS() {
    if (document.getElementById('enhanced-dashboard-css')) return;
    
    const style = document.createElement('style');
    style.id = 'enhanced-dashboard-css';
    style.textContent = `
        .metric-updated { 
            position: relative; 
            transition: all 0.3s ease;
        }
        
        .metric-updated-indicator { 
            position: absolute; 
            top: -2px; 
            right: -2px; 
            animation: pulse 2s infinite; 
            color: #28a745;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* Better data source indicator positioning */
        .data-source-indicator { 
            position: fixed !important; 
            top: 140px !important; 
            right: 20px !important; 
            z-index: 999 !important;
            max-width: 200px !important;
        }
        
        .data-source-badge { 
            background: rgba(255,255,255,0.95) !important; 
            border-radius: 20px !important; 
            padding: 8px 16px !important; 
            display: flex !important; 
            align-items: center !important; 
            gap: 5px !important; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
            font-size: 0.875rem !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .data-source-badge.real-data { 
            border: 1px solid #28a745 !important; 
            color: #28a745 !important; 
        }
        
        .data-source-badge.sample-data { 
            border: 1px solid #ffc107 !important; 
            color: #856404 !important; 
            background: rgba(255,193,7,0.1) !important; 
        }
        
        [data-theme="dark"] .data-source-badge { 
            background: rgba(45,55,72,0.95) !important; 
            color: #f7fafc !important; 
        }
        
        .loading {
            position: relative;
            pointer-events: none;
        }
        
        .loading::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .analysis-progress {
            transition: all 0.3s ease;
            opacity: 0;
            transform: translateY(10px);
        }
        
        .analysis-progress.visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        /* Prevent modal backdrop from interfering with form inputs */
        .modal-backdrop {
            z-index: 1040 !important;
        }
        
        .modal {
            z-index: 1050 !important;
        }
        
        /* Ensure form inputs are accessible */
        .modal .form-control,
        .modal .form-select {
            position: relative !important;
            z-index: 1055 !important;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Add CSS for fixed data source indicator
 */
export function addFixedDataSourceCSS() {
    if (document.getElementById('fixed-data-source-css')) return;
    
    const style = document.createElement('style');
    style.id = 'fixed-data-source-css';
    style.textContent = `
        .data-source-indicator-fixed {
            position: fixed !important;
            top: 90px !important;
            right: 20px !important;
            z-index: 1100 !important;
            max-width: 200px !important;
            pointer-events: none !important;
        }
        
        .data-source-badge-fixed {
            background: rgba(255,255,255,0.95) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 20px !important;
            padding: 8px 16px !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important;
            font-size: 0.875rem !important;
            border: 1px solid rgba(0,0,0,0.1) !important;
        }
        
        .data-source-badge-fixed.real-data {
            border-color: #28a745 !important;
            color: #28a745 !important;
        }
        
        .data-source-badge-fixed.sample-data {
            border-color: #ffc107 !important;
            color: #856404 !important;
            background: rgba(255,193,7,0.1) !important;
        }
        
        .data-source-badge-fixed small {
            display: block;
            font-size: 0.75rem;
            opacity: 0.8;
            margin-top: 2px;
        }
        
        /* Modal input fixes */
        .modal .form-control,
        .modal .form-select {
            position: relative !important;
            z-index: 1060 !important;
            background: white !important;
            border: 1px solid #ced4da !important;
        }
        
        .modal .form-control:focus,
        .modal .form-select:focus {
            border-color: #007bff !important;
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
            z-index: 1061 !important;
        }
        
        /* Metric update animation */
        .metric-updated {
            position: relative;
        }
        
        .metric-updated::after {
            content: '✓';
            position: absolute;
            top: -5px;
            right: -5px;
            background: #28a745;
            color: white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            animation: checkmark-appear 0.5s ease-out;
        }
        
        @keyframes checkmark-appear {
            0% { opacity: 0; transform: scale(0); }
            50% { opacity: 1; transform: scale(1.2); }
            100% { opacity: 1; transform: scale(1); }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Add analysis progress CSS
 */
export function addAnalysisFixCSS() {
    if (document.getElementById('analysis-fix-css')) return;
    
    const style = document.createElement('style');
    style.id = 'analysis-fix-css';
    style.textContent = `
        /* Analysis progress fixes */
        .analysis-progress {
            transition: all 0.3s ease !important;
            opacity: 0;
            transform: translateY(10px);
        }
        
        .analysis-progress.visible {
            opacity: 1 !important;
            transform: translateY(0) !important;
            display: block !important;
        }
        
        /* Button loading state fixes */
        .btn.loading {
            pointer-events: none !important;
            opacity: 0.8;
        }
        
        .btn:not(.loading) {
            pointer-events: auto !important;
            opacity: 1;
        }
        
        /* Progress bar animation */
        .progress-fill {
            transition: width 0.5s ease, background 0.3s ease !important;
        }
        
        /* Tab switching fixes */
        .tab-pane {
            transition: opacity 0.3s ease !important;
        }
        
        .tab-pane.active {
            opacity: 1 !important;
        }
        
        .tab-pane:not(.active) {
            opacity: 0 !important;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Enhanced modal CSS fixes
 */
export function injectModalFixCSS() {
    if (document.getElementById('modal-fix-css')) return;
    
    const style = document.createElement('style');
    style.id = 'modal-fix-css';
    style.textContent = `
        /* Ensure modal z-index hierarchy */
        .modal-backdrop {
            z-index: 1040 !important;
        }
        
        .modal {
            z-index: 1050 !important;
        }
        
        /* Ensure form inputs are always accessible */
        .modal .form-control,
        .modal .form-select,
        .modal .form-check-input,
        .modal textarea {
            position: relative !important;
            z-index: 1055 !important;
            background: white !important;
            border: 1px solid #ced4da !important;
            pointer-events: auto !important;
        }
        
        .modal .form-control:focus,
        .modal .form-select:focus {
            border-color: #007bff !important;
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
            outline: none !important;
        }
        
        /* Ensure buttons work properly */
        .modal .btn {
            position: relative !important;
            z-index: 1055 !important;
            pointer-events: auto !important;
        }
        
        .modal .btn:disabled {
            pointer-events: none !important;
        }
        
        /* Ensure labels are clickable */
        .modal .form-label {
            position: relative !important;
            z-index: 1055 !important;
            pointer-events: auto !important;
            cursor: pointer !important;
        }
        
        /* Loading state for form submission */
        .modal .btn.loading {
            pointer-events: none !important;
        }
        
        /* Form validation styling */
        .modal .form-control.is-valid {
            border-color: #28a745 !important;
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3e%3cpath fill='%2328a745' d='m2.3 6.73.9.9 4.8-4.8-.9-.9-3.9 3.9-1.9-1.9-.9.9z'/%3e%3c/svg%3e") !important;
            background-repeat: no-repeat !important;
            background-position: right calc(0.375em + 0.1875rem) center !important;
            background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem) !important;
        }
        
        .modal .form-control.is-invalid {
            border-color: #dc3545 !important;
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12' width='12' height='12' fill='none' stroke='%23dc3545'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath d='m5.8 4.6 1.4 1.4M5.8 7.4l1.4-1.4'/%3e%3c/svg%3e") !important;
            background-repeat: no-repeat !important;
            background-position: right calc(0.375em + 0.1875rem) center !important;
            background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem) !important;
        }
        
        /* Dark theme modal fixes */
        [data-theme="dark"] .modal .form-control,
        [data-theme="dark"] .modal .form-select {
            background: #2d3748 !important;
            border-color: #4a5568 !important;
            color: #f7fafc !important;
        }
        
        [data-theme="dark"] .modal .form-control:focus,
        [data-theme="dark"] .modal .form-select:focus {
            background: #2d3748 !important;
            border-color: #4299e1 !important;
            color: #f7fafc !important;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Chart animation CSS
 */
export function addChartAnimationCSS() {
    if (document.getElementById('chart-animation-css')) return;
    
    const style = document.createElement('style');
    style.id = 'chart-animation-css';
    style.textContent = `
        /* Chart container animations */
        .chart-container {
            transition: all 0.3s ease;
        }
        
        .chart-container:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        /* Chart loading state */
        .chart-loading {
            position: relative;
            min-height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .chart-loading::before {
            content: '';
            position: absolute;
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Metric cards animation */
        .metric-card {
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
        }
        
        /* Smooth value transitions */
        .metric-value {
            transition: all 0.5s ease;
        }
        
        .metric-value.updating {
            transform: scale(1.05);
            color: #007bff;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Button and interaction CSS
 */
export function addInteractionCSS() {
    if (document.getElementById('interaction-css')) return;
    
    const style = document.createElement('style');
    style.id = 'interaction-css';
    style.textContent = `
        /* Enhanced button states */
        .btn {
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        /* Loading button state */
        .btn.loading {
            position: relative;
            pointer-events: none;
        }
        
        .btn.loading::after {
            content: '';
            position: absolute;
            width: 16px;
            height: 16px;
            margin: auto;
            border: 2px solid transparent;
            border-top-color: currentColor;
            border-radius: 50%;
            animation: button-loading-spinner 1s ease infinite;
        }
        
        @keyframes button-loading-spinner {
            from { transform: rotate(0turn); }
            to { transform: rotate(1turn); }
        }
        
        /* Card hover effects */
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }
        
        /* Form focus enhancements */
        .form-control:focus,
        .form-select:focus {
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
            border-color: #007bff;
        }
        
        /* Notification animations */
        .toast {
            animation: slideInRight 0.3s ease-out;
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        /* Ripple effect for buttons */
        .btn-ripple {
            position: relative;
            overflow: hidden;
        }
        
        .btn-ripple::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .btn-ripple:active::before {
            width: 300px;
            height: 300px;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Responsive design enhancements
 */
export function addResponsiveCSS() {
    if (document.getElementById('responsive-css')) return;
    
    const style = document.createElement('style');
    style.id = 'responsive-css';
    style.textContent = `
        /* Mobile optimizations */
        @media (max-width: 768px) {
            .card {
                margin-bottom: 1rem;
            }
            
            .btn {
                width: 100%;
                margin-bottom: 0.5rem;
            }
            
            .btn-group .btn {
                width: auto;
            }
            
            .table-responsive {
                border: none;
            }
            
            .modal .btn {
                width: 100%;
                margin-bottom: 0.5rem;
            }
            
            .data-source-indicator {
                top: 60px !important;
                right: 10px !important;
                max-width: 150px !important;
            }
            
            .chart-container {
                margin-bottom: 2rem;
            }
        }
        
        /* Tablet optimizations */
        @media (max-width: 992px) {
            .sidebar {
                position: fixed;
                z-index: 1030;
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }
            
            .sidebar.show {
                transform: translateX(0);
            }
        }
        
        /* Large screen optimizations */
        @media (min-width: 1200px) {
            .container-fluid {
                max-width: 1400px;
            }
            
            .chart-container {
                min-height: 400px;
            }
        }
        
        /* Print styles */
        @media print {
            .btn,
            .navbar,
            .sidebar,
            .data-source-indicator,
            .modal {
                display: none !important;
            }
            
            .card {
                break-inside: avoid;
                box-shadow: none;
                border: 1px solid #ddd;
            }
            
            .chart-container {
                break-inside: avoid;
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Dark theme support
 */
export function addDarkThemeCSS() {
    if (document.getElementById('dark-theme-css')) return;
    
    const style = document.createElement('style');
    style.id = 'dark-theme-css';
    style.textContent = `
        [data-theme="dark"] {
            --bs-body-bg: #1a202c;
            --bs-body-color: #f7fafc;
            --bs-card-bg: #2d3748;
            --bs-border-color: #4a5568;
        }
        
        [data-theme="dark"] .card {
            background: var(--bs-card-bg);
            border-color: var(--bs-border-color);
            color: var(--bs-body-color);
        }
        
        [data-theme="dark"] .table {
            color: var(--bs-body-color);
        }
        
        [data-theme="dark"] .table-striped > tbody > tr:nth-of-type(odd) > td {
            background-color: rgba(255, 255, 255, 0.05);
        }
        
        [data-theme="dark"] .modal-content {
            background: var(--bs-card-bg);
            color: var(--bs-body-color);
        }
        
        [data-theme="dark"] .form-control {
            background: #2d3748;
            border-color: #4a5568;
            color: #f7fafc;
        }
        
        [data-theme="dark"] .form-control:focus {
            background: #2d3748;
            border-color: #4299e1;
            color: #f7fafc;
        }
        
        [data-theme="dark"] .btn-outline-primary {
            color: #4299e1;
            border-color: #4299e1;
        }
        
        [data-theme="dark"] .btn-outline-primary:hover {
            background: #4299e1;
            color: #1a202c;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Initialize all CSS enhancements
 */
export function initializeAllCSS() {
    console.log('🎨 Initializing all CSS enhancements');
    
    injectEnhancedCSS();
    addFixedDataSourceCSS();
    addAnalysisFixCSS();
    injectModalFixCSS();
    addChartAnimationCSS();
    addInteractionCSS();
    addResponsiveCSS();
    addDarkThemeCSS();
    
    console.log('✅ All CSS enhancements loaded');
}

/**
 * Theme management
 */
export function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('preferred-theme', newTheme);
    
    // Update theme toggle button if it exists
    const themeToggle = document.querySelector('[data-theme-toggle]');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
}

/**
 * Initialize theme from localStorage
 */
export function initializeTheme() {
    const preferredTheme = localStorage.getItem('preferred-theme') || 'light';
    document.documentElement.setAttribute('data-theme', preferredTheme);
    
    // Setup theme toggle listener
    const themeToggle = document.querySelector('[data-theme-toggle]');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeAllCSS();
        initializeTheme();
    });
} else {
    initializeAllCSS();
    initializeTheme();
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.initializeAllCSS = initializeAllCSS;
    window.toggleTheme = toggleTheme;
    window.initializeTheme = initializeTheme;
}

console.log('✅ CSS injection utilities loaded successfully');