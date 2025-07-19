// frontend/static/js/alerts/utils/validation.js

/**
 * Email validation
 */
export function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate alert form data
 */
export function validateAlertForm(formData) {
    const errors = [];
    
    if (!formData.name || !formData.name.trim()) {
        errors.push('Alert name is required');
    }
    
    if (!formData.email || !isValidEmail(formData.email)) {
        errors.push('Valid email address is required');
    }
    
    if (formData.threshold_amount <= 0 && formData.threshold_percentage <= 0) {
        errors.push('Either threshold amount or percentage must be greater than 0');
    }
    
    if (formData.threshold_percentage && (formData.threshold_percentage < 0 || formData.threshold_percentage > 100)) {
        errors.push('Threshold percentage must be between 0 and 100');
    }
    
    if (formData.max_notifications_per_day && formData.max_notifications_per_day < 1) {
        errors.push('Maximum notifications per day must be at least 1');
    }
    
    if (formData.cooldown_period_hours && formData.cooldown_period_hours < 0) {
        errors.push('Cooldown period cannot be negative');
    }
    
    return errors;
}

/**
 * Validate frequency configuration
 */
export function validateFrequencyConfig(frequency, atTime, maxPerDay, cooldown) {
    const errors = [];
    
    if (frequency === 'immediate' && (!cooldown || cooldown === 0)) {
        errors.push('Immediate alerts should have a cooldown period to prevent spam');
    }
    
    if (frequency === 'daily' && atTime && !isValidTime(atTime)) {
        errors.push('Invalid time format for daily notifications');
    }
    
    if (maxPerDay && maxPerDay > 100) {
        errors.push('Maximum notifications per day seems too high (>100)');
    }
    
    return errors;
}

/**
 * Validate time format (HH:MM)
 */
export function isValidTime(timeString) {
    const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
    return timeRegex.test(timeString);
}

// Note: escapeHtml moved to formatting.js

/**
 * Validate notification channels
 */
export function validateNotificationChannels(channels, availableChannels) {
    if (!Array.isArray(channels) || channels.length === 0) {
        return ['At least one notification channel must be selected'];
    }
    
    const invalidChannels = channels.filter(channel => !availableChannels[channel]);
    if (invalidChannels.length > 0) {
        return [`Invalid notification channels: ${invalidChannels.join(', ')}`];
    }
    
    return [];
}