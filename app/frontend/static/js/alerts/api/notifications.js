// frontend/static/js/alerts/api/notifications.js

import { API_ENDPOINTS } from '../core/config.js';

/**
 * API functions for notification management
 */

/**
 * Fetch in-app notifications
 */
export async function fetchInAppNotifications(clusterId = null, unreadOnly = false, limit = 50) {
    let apiUrl = `${API_ENDPOINTS.inAppNotifications}?unread_only=${unreadOnly}&limit=${limit}`;
    
    if (clusterId) {
        apiUrl += `&cluster_id=${encodeURIComponent(clusterId)}`;
    }
    
    const response = await fetch(apiUrl);
    
    if (!response.ok) {
        if (response.status === 404) {
            // Endpoint doesn't exist, return empty data
            return {
                status: 'success',
                notifications: [],
                unread_count: 0
            };
        }
        throw new Error(`Request failed: ${response.status}`);
    }
    
    return response.json();
}

/**
 * Update notification status (mark as read/dismiss)
 */
export async function updateNotifications(notificationIds, action) {
    try {
        const response = await fetch(API_ENDPOINTS.inAppNotifications, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                notification_ids: notificationIds,
                action: action
            })
        });
        
        if (response.status === 404) {
            // Endpoint doesn't exist, return success for local handling
            return { status: 'success', local_only: true };
        }
        
        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }
        
        return response.json();
    } catch (error) {
        // Return success for local handling if API call fails
        return { status: 'success', local_only: true, error: error.message };
    }
}

/**
 * Mark notification as read
 */
export async function markNotificationAsRead(notificationId) {
    return updateNotifications([notificationId], 'mark_read');
}

/**
 * Dismiss notification
 */
export async function dismissNotification(notificationId) {
    return updateNotifications([notificationId], 'dismiss');
}

/**
 * Mark all notifications as read
 */
export async function markAllNotificationsAsRead(notificationIds) {
    return updateNotifications(notificationIds, 'mark_read');
}

/**
 * Test Slack notification
 */
export async function testSlackNotification(title = 'Test Slack Integration', message = 'This is a test message from AKS Cost Intelligence alerts system.') {
    const response = await fetch(API_ENDPOINTS.slackTest, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title: title,
            message: message
        })
    });
    
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    
    return response.json();
}