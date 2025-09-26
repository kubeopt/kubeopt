/**
 * IMPLEMENTATION PLAN UTILS - Utilities and Helper Functions
 * Handles markdown conversion, copy functionality, notifications, and utility functions
 */

import { escapeHtml, getPriorityColor, getRiskColor } from '../utils.js';

/**
 * FIXED MARKDOWN CONVERSION FUNCTIONS - Clean and Proper Formatting
 */
export function convertToRichMarkdown(data, title = 'Configuration') {
    if (!data || typeof data !== 'object') {
        return `## ${title}\n\n*No configuration data available*`;
    }
    
    let markdown = `# ${title}\n\n`;
    
    // Helper function to format keys nicely
    function formatKey(key) {
        return key
            .replace(/([A-Z])/g, ' $1') // Add space before capital letters
            .replace(/_/g, ' ') // Replace underscores with spaces
            .toLowerCase()
            .replace(/\b\w/g, l => l.toUpperCase()) // Capitalize first letter of each word
            .trim();
    }
    
    // Enhanced value processing with cleaner output
    function processValue(value, depth = 0, maxDepth = 3) {
        const indent = '  '.repeat(depth);
        
        // Prevent infinite recursion
        if (depth > maxDepth) {
            return '*[Maximum depth reached]*';
        }
        
        if (value === null || value === undefined) {
            return '*Not configured*';
        }
        
        if (typeof value === 'boolean') {
            return value ? '✅ **Enabled**' : '❌ **Disabled**';
        }
        
        if (typeof value === 'number') {
            // Smart number formatting
            if (value > 1000000) {
                return `**$${(value / 1000000).toFixed(1)}M**`;
            } else if (value > 1000) {
                return `**$${(value / 1000).toFixed(1)}K**`;
            } else if (value < 1 && value > 0 && value <= 1) {
                return `**${(value * 100).toFixed(1)}%**`;
            } else {
                return `**${value.toLocaleString()}**`;
            }
        }
        
        if (typeof value === 'string') {
            // Clean string formatting - avoid over-processing
            if (value.length > 100) {
                return `${value.substring(0, 100)}...`;
            }
            return value;
        }
        
        if (Array.isArray(value)) {
            if (value.length === 0) return '*No items configured*';
            if (value.length > 10) {
                return `${value.slice(0, 10).map(item => `${indent}- ${processValue(item, depth + 1, maxDepth)}`).join('\n')}\n${indent}*... and ${value.length - 10} more items*`;
            }
            return value.map(item => `${indent}- ${processValue(item, depth + 1, maxDepth)}`).join('\n');
        }
        
        if (typeof value === 'object') {
            // Skip overly complex objects to keep markdown clean
            const entries = Object.entries(value);
            if (entries.length === 0) return '*No configuration data*';
            
            // Limit object depth and entries to keep output manageable
            const maxEntries = depth === 0 ? 15 : 8;
            const limitedEntries = entries.slice(0, maxEntries);
            
            let result = '';
            limitedEntries.forEach(([key, val]) => {
                const formattedKey = formatKey(key);
                const processedValue = processValue(val, depth + 1, maxDepth);
                
                // Only include if the value is meaningful
                if (processedValue !== '*Not configured*' && processedValue !== '*No configuration data*') {
                    result += `${indent}**${formattedKey}:** ${processedValue}\n`;
                }
            });
            
            if (entries.length > maxEntries) {
                result += `${indent}*... and ${entries.length - maxEntries} more configuration items*\n`;
            }
            
            return result.trim() || '*No meaningful configuration found*';
        }
        
        return String(value);
    }
    
    // Process only the most important sections to avoid clutter
    const importantKeys = Object.keys(data).filter(key => {
        const value = data[key];
        return value !== null && value !== undefined && 
               (typeof value !== 'object' || Object.keys(value).length > 0);
    });
    
    if (importantKeys.length === 0) {
        markdown += '*No configuration data available*\n\n';
        return markdown;
    }
    
    // Limit to most important sections
    const limitedKeys = importantKeys.slice(0, 10);
    
    limitedKeys.forEach(key => {
        const value = data[key];
        const sectionTitle = formatKey(key);
        const emoji = getEmojiForKey(key);
        
        markdown += `## ${emoji} ${sectionTitle}\n\n`;
        const processedContent = processValue(value, 0);
        
        if (processedContent && processedContent !== '*No meaningful configuration found*') {
            markdown += processedContent + '\n\n';
        } else {
            markdown += '*No configuration available for this section*\n\n';
        }
    });
    
    if (importantKeys.length > limitedKeys.length) {
        markdown += `---\n\n*Note: ${importantKeys.length - limitedKeys.length} additional configuration sections are available but not shown for brevity.*\n\n`;
    }
    
    return markdown;
}

/**
 * FIXED Get appropriate emoji for configuration keys
 */
export function getEmojiForKey(key) {
    const emojiMap = {
        'budget': '💰', 'cost': '💰', 'pricing': '💰', 'billing': '💰', 'limits': '💰',
        'monitoring': '📊', 'metrics': '📈', 'alerts': '🚨', 'dashboard': '📋',
        'security': '🔒', 'authentication': '🔐', 'authorization': '🛡️',
        'storage': '💾', 'database': '🗄️', 'cache': '⚡',
        'network': '🌐', 'connectivity': '🔗', 'dns': '🌍',
        'backup': '💾', 'recovery': '🔄', 'disaster': '🆘', 'contingency': '🛡️',
        'performance': '⚡', 'optimization': '🚀', 'scaling': '📈',
        'compliance': '✅', 'governance': '⚖️', 'policy': '📜',
        'azure': '☁️', 'aws': '☁️', 'gcp': '☁️', 'cloud': '☁️',
        'kubernetes': '☸️', 'container': '📦', 'docker': '🐳',
        'service': '⚙️', 'application': '📱', 'api': '🔌',
        'configuration': '⚙️', 'settings': '🛠️', 'parameters': '📋',
        'success': '🎯', 'criteria': '🎯', 'timeline': '⏰', 'risk': '⚠️',
        'intelligence': '🧠', 'insights': '🧠', 'strategy': '📋'
    };
    
    const lowerKey = key.toLowerCase();
    for (const [keyword, emoji] of Object.entries(emojiMap)) {
        if (lowerKey.includes(keyword)) {
            return emoji;
        }
    }
    return '📋'; // default
}

/**
 * STANDALONE Render markdown with custom copy functionality (bypasses copy-functionality.js)
 */
export function renderMarkdownData(markdownContent, containerTitle = 'Configuration Details') {
    // Convert markdown to HTML with styling
    const htmlContent = markdownContent
        .replace(/^# (.*$)/gm, '<h1 style="color: #e2e8f0; margin: 25px 0 20px 0; font-size: 24px; border-bottom: 3px solid #667eea; padding-bottom: 12px;">$1</h1>')
        .replace(/^## (.*$)/gm, '<h2 style="color: #e2e8f0; margin: 20px 0 15px 0; font-size: 18px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">$1</h2>')
        .replace(/^### (.*$)/gm, '<h3 style="color: #4a5568; margin: 15px 0 10px 0; font-size: 16px;">$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong style="color: #e2e8f0; font-weight: 600;">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em style="color: #718096; font-style: italic;">$1</em>')
        .replace(/`(.*?)`/g, '<code style="background: #edf2f7; padding: 2px 6px; border-radius: 4px; font-family: monospace; color: #e2e8f0; font-size: 13px;">$1</code>')
        .replace(/^- (.*$)/gm, '<li style="margin: 5px 0; color: #4a5568; line-height: 1.5;">$1</li>')
        .replace(/(<li.*?>[\s\S]*?<\/li>)/s, '<ul style="margin: 10px 0; padding-left: 20px; list-style-type: disc;">$1</ul>')
        .replace(/\n/g, '<br>');
    
    // Generate unique ID for this markdown container
    const buttonId = `markdown-copy-btn-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Store markdown content in a global variable for copy access
    if (!window.markdownStore) window.markdownStore = {};
    window.markdownStore[buttonId] = markdownContent;
    
    return `
        <div style="background: #f8fafc; border-radius: 16px; padding: 25px; margin-top: 30px; border: 1px solid #e2e8f0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;">
                <h3 style="margin: 0; color: #22543d; display: flex; align-items: center; gap: 10px;">
                    <span>📋</span> ${containerTitle}
                </h3>
                <button id="${buttonId}"
                        onclick="event.stopPropagation(); event.preventDefault(); copyMarkdownStandalone('${buttonId}');" 
                        style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.2s ease;"
                        onmouseover="this.style.background='#5a67d8'" 
                        onmouseout="this.style.background='#667eea'"
                        title="Copy markdown to clipboard"
                        data-custom-copy="true">
                    📋 Copy Markdown
                </button>
            </div>
            
            <div class="markdown-content" style="
                background: white; 
                border-radius: 12px; 
                padding: 20px; 
                border: 1px solid #e2e8f0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                max-height: 400px;
                overflow-y: auto;
            ">
                ${htmlContent}
            </div>
            
            <!-- Raw markdown source (hidden by default) -->
            <details style="margin-top: 15px;">
                <summary style="cursor: pointer; font-weight: 600; color: #667eea; font-size: 14px; transition: color 0.2s ease;" 
                         onmouseover="this.style.color='#5a67d8'" 
                         onmouseout="this.style.color='#667eea'">
                    View Markdown Source
                </summary>
                <pre style="background: #1a202c; color: #e2e8f0; padding: 15px; border-radius: 8px; font-size: 11px; overflow-x: auto; border: 1px solid #2d3748; margin-top: 10px; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; line-height: 1.4; white-space: pre-wrap;">${markdownContent.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
            </details>
        </div>
    `;
}

// NOTE: Standalone markdown copy functionality (bypasses copy-functionality.js)
// Uses existing notification system for user feedback

/**
 * Standalone copy function for markdown content (with interference protection)
 */
window.copyMarkdownStandalone = function(buttonId) {
    logDebug('📋 Standalone markdown copy for button:', buttonId);
    
    const markdownContent = window.markdownStore?.[buttonId];
    const button = document.getElementById(buttonId);
    
    if (!markdownContent) {
        console.error('❌ No markdown content found for button:', buttonId);
        if (window.showNotification) {
            window.showNotification('❌ No content found to copy', 'error', 3000);
        }
        return false; // Prevent any further event handling
    }
    
    // Remove any error classes that might be added by other systems
    if (button) {
        button.classList.remove('copy-error', 'copy-success');
        button.removeAttribute('data-copy-target'); // Ensure no interference
    }
    
    // Try modern clipboard API first
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(markdownContent).then(() => {
            logDebug('✅ Markdown copied via Clipboard API');
            
            // Use existing notification system if available
            if (window.showNotification) {
                window.showNotification('✅ Markdown configuration copied to clipboard!', 'success', 3000);
            }
            
            // Protected visual feedback on button
            if (button) {
                showCopySuccess(button);
            }
        }).catch(err => {
            console.error('❌ Clipboard API failed:', err);
            fallbackCopyMarkdown(markdownContent, button);
        });
    } else {
        logDebug('📋 Clipboard API not available, using fallback');
        fallbackCopyMarkdown(markdownContent, button);
    }
    
    return false; // Prevent event bubbling
};

/**
 * Protected visual feedback function
 */
function showCopySuccess(button) {
    // Store original values safely
    const originalData = {
        text: button.innerHTML,
        background: button.style.background || '#667eea',
        className: button.className
    };
    
    // Clear any conflicting classes
    button.classList.remove('copy-error', 'copy-success');
    
    // Apply success styling
    button.innerHTML = '✅ Copied!';
    button.style.background = '#38a169';
    button.style.transition = 'all 0.2s ease';
    
    // Restore after delay
    setTimeout(() => {
        if (button && button.id) { // Ensure button still exists
            button.innerHTML = originalData.text;
            button.style.background = originalData.background;
            button.className = originalData.className;
            
            // Remove any error classes that might have been added
            button.classList.remove('copy-error', 'copy-success');
        }
    }, 2000);
}

/**
 * Protected fallback copy method
 */
function fallbackCopyMarkdown(text, button) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    textArea.style.top = '-9999px';
    textArea.style.opacity = '0';
    textArea.style.zIndex = '-1';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    textArea.setSelectionRange(0, text.length);
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            logDebug('✅ Markdown copied via fallback method');
            
            // Use existing notification system if available
            if (window.showNotification) {
                window.showNotification('✅ Markdown configuration copied to clipboard!', 'success', 3000);
            }
            
            // Protected visual feedback
            if (button) {
                showCopySuccess(button);
            }
        } else {
            throw new Error('execCommand copy failed');
        }
    } catch (err) {
        console.error('❌ Fallback copy failed:', err);
        
        // Use existing notification system if available
        if (window.showNotification) {
            window.showNotification('❌ Failed to copy. Please copy manually from the source below.', 'error', 5000);
        }
        
        // Visual feedback for error
        if (button) {
            const originalText = button.innerHTML;
            const originalBg = button.style.background || '#667eea';
            button.innerHTML = '❌ Failed';
            button.style.background = '#e53e3e';
            setTimeout(() => {
                if (button && button.id) {
                    button.innerHTML = originalText;
                    button.style.background = originalBg;
                    button.classList.remove('copy-error', 'copy-success');
                }
            }, 3000);
        }
    } finally {
        document.body.removeChild(textArea);
    }
}

/**
 * Badge color helper function
 */
export function getBadgeColor(type) {
    const colors = {
        'security': '#e53e3e', 'compliance': '#ed8936', 'governance': '#38b2ac',
        'critical': '#9f7aea', 'setup': '#3182ce', 'implementation': '#48bb78',
        'optimization': '#0bc5ea', 'monitoring': '#718096', 'hpa': '#e53e3e',
        'rightsizing': '#ed8936', 'assessment': '#3182ce', 'storage': '#9f7aea'
    };
    return colors[type] || '#718096';
}

/**
 * Enhanced notification system
 */
export function showCopyNotification(message, type = 'success') {
    if (window.showNotification) {
        window.showNotification(message, type, 3000);
    } else {
        const notification = document.createElement('div');
        const bgColor = type === 'success' ? '#48bb78' : '#e53e3e';
        const icon = type === 'success' ? '✅' : '❌';
        
        notification.style.cssText = `
            position: fixed; 
            top: 20px; 
            right: 20px; 
            background: ${bgColor}; 
            color: white; 
            padding: 15px 20px; 
            border-radius: 12px; 
            z-index: 10000; 
            font-size: 14px; 
            font-weight: 500;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            gap: 8px;
            animation: slideIn 0.3s ease;
            max-width: 400px;
        `;
        
        notification.innerHTML = `${icon} ${message}`;
        document.body.appendChild(notification);
        
        // Add animation styles
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

/**
 * Color helper functions for UI consistency
 */
export function getStatusColor(status) {
    const statusColors = {
        'active': '#48bb78',
        'inactive': '#e53e3e',
        'pending': '#ed8936',
        'warning': '#ecc94b',
        'info': '#4299e1',
        'success': '#48bb78',
        'error': '#e53e3e'
    };
    return statusColors[status.toLowerCase()] || '#718096';
}

export function getPriorityColorUtil(priority) {
    const priorityColors = {
        'critical': '#e53e3e',
        'high': '#ed8936',
        'medium': '#ecc94b',
        'low': '#48bb78',
        'info': '#4299e1'
    };
    return priorityColors[priority.toLowerCase()] || '#718096';
}

export function getRiskColorUtil(risk) {
    const riskColors = {
        'high': '#e53e3e',
        'medium': '#ed8936',
        'low': '#48bb78',
        'none': '#38b2ac'
    };
    return riskColors[risk.toLowerCase()] || '#718096';
}

/**
 * Text formatting utilities
 */
export function truncateText(text, maxLength = 100) {
    if (typeof text !== 'string') return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
}

export function formatCurrency(amount, currency = 'USD') {
    if (typeof amount !== 'number') return '$0.00';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

export function formatPercentage(value, decimals = 1) {
    if (typeof value !== 'number') return '0%';
    return `${(value * 100).toFixed(decimals)}%`;
}

export function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

/**
 * Data validation utilities
 */
export function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

export function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

export function sanitizeHtml(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
}

/**
 * Array and object utilities
 */
export function groupBy(array, key) {
    return array.reduce((groups, item) => {
        const group = item[key];
        if (!groups[group]) {
            groups[group] = [];
        }
        groups[group].push(item);
        return groups;
    }, {});
}

export function sortBy(array, key, direction = 'asc') {
    return [...array].sort((a, b) => {
        const aVal = a[key];
        const bVal = b[key];
        
        if (direction === 'desc') {
            return bVal > aVal ? 1 : bVal < aVal ? -1 : 0;
        }
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
    });
}

export function uniqueBy(array, key) {
    const seen = new Set();
    return array.filter(item => {
        const value = item[key];
        if (seen.has(value)) {
            return false;
        }
        seen.add(value);
        return true;
    });
}

/**
 * Storage utilities (memory-based for artifacts compatibility)
 */
export function getFromStorage(key, defaultValue = null) {
    if (typeof window === 'undefined') return defaultValue;
    
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.warn('Failed to read from localStorage:', error);
        return defaultValue;
    }
}

export function setToStorage(key, value) {
    if (typeof window === 'undefined') return false;
    
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        console.warn('Failed to write to localStorage:', error);
        return false;
    }
}

export function removeFromStorage(key) {
    if (typeof window === 'undefined') return false;
    
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.warn('Failed to remove from localStorage:', error);
        return false;
    }
}

/**
 * Performance utilities
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

export function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * DOM utilities
 */
export function createElement(tag, attributes = {}, children = []) {
    const element = document.createElement(tag);
    
    Object.entries(attributes).forEach(([key, value]) => {
        if (key === 'style' && typeof value === 'object') {
            Object.assign(element.style, value);
        } else if (key.startsWith('on') && typeof value === 'function') {
            element.addEventListener(key.slice(2).toLowerCase(), value);
        } else {
            element.setAttribute(key, value);
        }
    });
    
    children.forEach(child => {
        if (typeof child === 'string') {
            element.appendChild(document.createTextNode(child));
        } else if (child instanceof Node) {
            element.appendChild(child);
        }
    });
    
    return element;
}

export function findAncestor(element, selector) {
    while (element && element !== document.body) {
        if (element.matches && element.matches(selector)) {
            return element;
        }
        element = element.parentElement;
    }
    return null;
}

// Global assignments for compatibility
if (typeof window !== 'undefined') {
    logDebug('✅ Implementation Plan Utils loaded');
    logDebug('📋 Markdown conversion and copy functionality ready');
    logDebug('🛠️ Helper utilities and formatters available');
}