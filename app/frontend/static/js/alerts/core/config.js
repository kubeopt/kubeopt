// frontend/static/js/alerts/core/config.js

/**
 * Frequency configuration mappings
 */
export const FREQUENCY_MAP = {
    'immediate': { 
        display: 'Immediate', 
        description: 'Send notification as soon as alert is triggered',
        icon: 'fa-bolt',
        color: 'danger'
    },
    'hourly': { 
        display: 'Hourly', 
        description: 'Send notifications once per hour',
        icon: 'fa-clock',
        color: 'warning'
    },
    'daily': { 
        display: 'Daily', 
        description: 'Send one notification per day at 9:00 AM',
        icon: 'fa-calendar-day',
        color: 'primary'
    },
    'weekly': { 
        display: 'Weekly', 
        description: 'Send notifications once per week',
        icon: 'fa-calendar-week',
        color: 'info'
    },
    'monthly': { 
        display: 'Monthly', 
        description: 'Send notifications once per month',
        icon: 'fa-calendar-alt',
        color: 'secondary'
    },
    'custom_4h': { 
        display: 'Every 4 Hours', 
        description: 'Send notifications every 4 hours',
        icon: 'fa-history',
        color: 'success'
    }
};

/**
 * Notification type configurations
 */
export const NOTIFICATION_TYPES = {
    'info': {
        icon: 'info-circle',
        color: 'info',
        bgColor: 'blue'
    },
    'success': {
        icon: 'check-circle',
        color: 'success',
        bgColor: 'green'
    },
    'warning': {
        icon: 'exclamation-triangle',
        color: 'warning',
        bgColor: 'yellow'
    },
    'error': {
        icon: 'times-circle',
        color: 'danger',
        bgColor: 'red'
    },
    'alert': {
        icon: 'bell',
        color: 'primary',
        bgColor: 'orange'
    }
};

/**
 * Status badge configurations
 */
export const STATUS_BADGES = {
    'active': 'bg-success',
    'paused': 'bg-warning text-dark',
    'triggered': 'bg-danger',
    'failed': 'bg-secondary'
};

/**
 * Channel configurations
 */
export const CHANNEL_ICONS = {
    'email': '<i class="fas fa-envelope text-primary"></i>',
    'slack': '<i class="fab fa-slack text-success"></i>',
    'inapp': '<i class="fas fa-bell text-info"></i>',
    'in_app': '<i class="fas fa-bell text-info"></i>'
};

/**
 * API endpoints
 */
export const API_ENDPOINTS = {
    alerts: '/api/alerts',
    systemStatus: '/api/alerts/system-status',
    emailConfig: '/api/alerts/email-config',
    frequencyConfigs: '/api/alerts/frequency-configs',
    inAppNotifications: '/api/notifications/in-app',
    slackTest: '/api/notifications/slack/test',
    alertTriggers: '/api/alerts/triggers'
};

/**
 * Default configurations
 */
export const DEFAULTS = {
    frequency: 'daily',
    notificationTime: '09:00',
    maxNotificationsPerDay: 3,
    cooldownHours: 4,
    toastDuration: 5000,
    errorToastDuration: 8000
};