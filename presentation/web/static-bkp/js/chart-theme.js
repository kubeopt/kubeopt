/**
 * ============================================================================
 * CHART THEME CONFIGURATION - Clean Minimal Design System
 * ============================================================================
 * Standardized chart styling that matches the clean-minimal.css theme
 * ============================================================================
 */

// Theme colors matching clean-minimal.css
export const ThemeColors = {
    primary: '#7FB069',         // --primary-green
    primaryLight: '#9CC584',    // --light-green
    primaryDark: '#5A8A4A',     // --dark-green
    
    backgrounds: {
        primary: '#f8f9fa',     // --bg-primary
        white: '#ffffff',       // --bg-white
        sidebar: '#7FB069'      // --bg-sidebar
    },
    
    text: {
        primary: '#2d3748',     // --text-primary
        secondary: '#4a5568',   // --text-secondary
        muted: '#718096',       // --text-muted
        light: '#a0aec0',       // --text-light
        white: '#ffffff'        // --text-white
    },
    
    borders: {
        default: '#e2e8f0',
        light: 'rgba(226, 232, 240, 0.5)'
    },
    
    shadows: {
        sm: '0 1px 3px rgba(0, 0, 0, 0.1)',
        md: '0 4px 6px rgba(0, 0, 0, 0.07)',
        lg: '0 10px 15px rgba(0, 0, 0, 0.1)'
    }
};

/**
 * Standard tooltip configuration that matches clean-minimal theme
 */
export function getThemeTooltipConfig(customCallbacks = {}) {
    return {
        enabled: true,
        backgroundColor: ThemeColors.backgrounds.white,
        titleColor: ThemeColors.text.primary,
        bodyColor: ThemeColors.text.secondary,
        footerColor: ThemeColors.text.muted,
        borderColor: ThemeColors.borders.default,
        borderWidth: 1,
        cornerRadius: 8,
        padding: 12,
        displayColors: true,
        boxPadding: 6,
        boxHeight: 12,
        boxWidth: 12,
        titleFont: {
            size: 14,
            weight: '600',
            family: 'system-ui, -apple-system, sans-serif'
        },
        bodyFont: {
            size: 13,
            weight: '500',
            family: 'system-ui, -apple-system, sans-serif'
        },
        footerFont: {
            size: 12,
            weight: '400',
            family: 'system-ui, -apple-system, sans-serif'
        },
        caretSize: 6,
        caretPadding: 8,
        ...customCallbacks
    };
}

/**
 * Standard legend configuration that matches clean-minimal theme
 */
export function getThemeLegendConfig(position = 'bottom') {
    return {
        display: true,
        position: position,
        align: 'center',
        labels: {
            color: ThemeColors.text.primary,
            font: {
                size: 12,
                weight: '500',
                family: 'system-ui, -apple-system, sans-serif'
            },
            padding: 16,
            usePointStyle: true,
            pointStyle: 'circle'
        },
        onHover: (event, legendItem) => {
            event.native.target.style.cursor = 'pointer';
        },
        onLeave: (event, legendItem) => {
            event.native.target.style.cursor = 'default';
        }
    };
}

/**
 * Standard chart options that match clean-minimal theme
 */
export function getThemeChartOptions(customOptions = {}) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            intersect: false,
            mode: 'index'
        },
        plugins: {
            legend: getThemeLegendConfig(),
            tooltip: getThemeTooltipConfig(),
        },
        scales: {
            x: {
                grid: {
                    display: true,
                    color: ThemeColors.borders.light,
                    lineWidth: 1
                },
                ticks: {
                    color: ThemeColors.text.secondary,
                    font: {
                        size: 11,
                        family: 'system-ui, -apple-system, sans-serif'
                    }
                },
                title: {
                    color: ThemeColors.text.primary,
                    font: {
                        size: 12,
                        weight: '600',
                        family: 'system-ui, -apple-system, sans-serif'
                    }
                }
            },
            y: {
                grid: {
                    display: true,
                    color: ThemeColors.borders.light,
                    lineWidth: 1
                },
                ticks: {
                    color: ThemeColors.text.secondary,
                    font: {
                        size: 11,
                        family: 'system-ui, -apple-system, sans-serif'
                    }
                },
                title: {
                    color: ThemeColors.text.primary,
                    font: {
                        size: 12,
                        weight: '600',
                        family: 'system-ui, -apple-system, sans-serif'
                    }
                }
            }
        },
        ...customOptions
    };
}

/**
 * Chart color palette that matches the theme
 */
export function getThemeChartColors() {
    return {
        primary: ThemeColors.primary,
        primaryLight: ThemeColors.primaryLight,
        primaryDark: ThemeColors.primaryDark,
        
        // Additional colors for multi-dataset charts
        secondary: '#6366f1',      // Indigo
        accent: '#f59e0b',         // Amber
        warning: '#ef4444',        // Red
        info: '#06b6d4',           // Cyan
        success: ThemeColors.primary,
        
        // Transparent variants
        primaryAlpha: 'rgba(127, 176, 105, 0.1)',
        secondaryAlpha: 'rgba(99, 102, 241, 0.1)',
        accentAlpha: 'rgba(245, 158, 11, 0.1)',
        warningAlpha: 'rgba(239, 68, 68, 0.1)',
        infoAlpha: 'rgba(6, 182, 212, 0.1)'
    };
}