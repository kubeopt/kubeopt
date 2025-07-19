// frontend/static/js/alerts/utils/formatting.js

import { FREQUENCY_MAP, NOTIFICATION_TYPES, STATUS_BADGES, DEFAULTS } from '../core/config.js';

/**
 * Format date and time
 */
export function formatDateTime(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch {
        return dateString || 'Invalid date';
    }
}

/**
 * Format date only
 */
export function formatDate(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
        });
    } catch {
        return 'Invalid date';
    }
}

/**
 * Format time only
 */
export function formatTime(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true
        });
    } catch {
        return 'Invalid time';
    }
}

/**
 * Format currency
 */
export function formatCurrency(amount, currency = '$') {
    if (typeof amount !== 'number') return 'N/A';
    return `${currency}${amount.toLocaleString()}`;
}

/**
 * Get frequency information
 */
export function getFrequencyInfo(frequency) {
    // Ensure we never return undefined
    if (!frequency || frequency === 'undefined' || frequency === '') {
        frequency = DEFAULTS.frequency;
    }
    
    // Try to get from frequency map
    const fallback = FREQUENCY_MAP[frequency];
    if (fallback) {
        return fallback;
    }
    
    // Ultimate fallback
    return {
        display: 'Daily',
        description: 'Send notifications daily',
        icon: 'fa-calendar-day',
        color: 'primary'
    };
}

/**
 * Get status badge class
 */
export function getStatusBadgeClass(status) {
    return STATUS_BADGES[status] || 'bg-secondary';
}

/**
 * Get notification icon
 */
export function getNotificationIcon(type) {
    const config = NOTIFICATION_TYPES[type];
    return config ? config.icon : 'bell';
}

/**
 * Get notification color
 */
export function getNotificationColor(type) {
    const config = NOTIFICATION_TYPES[type];
    return config ? config.color : 'secondary';
}

/**
 * Get notification background color for UI
 */
export function getNotificationTypeColor(type) {
    const config = NOTIFICATION_TYPES[type];
    return config ? config.bgColor : 'blue';
}

/**
 * Get notification type icon
 */
export function getNotificationTypeIcon(type) {
    const config = NOTIFICATION_TYPES[type];
    return config ? config.icon : 'bell';
}

/**
 * Generate unique ID
 */
export function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Truncate text
 */
export function truncateText(text, maxLength = 50) {
    if (typeof text !== 'string') return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Format percentage
 */
export function formatPercentage(value) {
    if (typeof value !== 'number') return '0%';
    return `${Math.round(value)}%`;
}

/**
 * Format relative time
 */
export function formatRelativeTime(timestamp) {
    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return formatDate(timestamp);
    } catch {
        return 'Unknown';
    }
}

/**
 * Escape HTML for safe insertion
 */
export function escapeHtml(text) {
    if (typeof text !== 'string') return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}