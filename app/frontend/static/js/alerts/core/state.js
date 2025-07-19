// frontend/static/js/alerts/core/state.js

/**
 * Global alerts state management
 */
export const AlertsState = {
    alerts: [],
    loading: false,
    currentClusterId: null,
    emailConfigured: false,
    slackConfigured: false,
    systemAvailable: true,
    lastError: null,
    currentFilter: 'all',
    inAppNotifications: [],
    unreadNotificationsCount: 0,
    notificationChannels: {
        email: false,
        slack: false,
        inApp: true
    },
    frequencyConfigs: [],
    defaultFrequency: 'daily'
};

/**
 * State update functions
 */
export const StateActions = {
    setAlerts(alerts) {
        AlertsState.alerts = alerts;
    },

    setLoading(loading) {
        AlertsState.loading = loading;
    },

    setCurrentCluster(clusterId) {
        AlertsState.currentClusterId = clusterId;
    },

    setSystemAvailable(available) {
        AlertsState.systemAvailable = available;
    },

    setNotificationChannels(channels) {
        AlertsState.notificationChannels = { ...AlertsState.notificationChannels, ...channels };
    },

    setInAppNotifications(notifications) {
        AlertsState.inAppNotifications = notifications;
    },

    setUnreadCount(count) {
        AlertsState.unreadNotificationsCount = count;
    },

    setCurrentFilter(filter) {
        AlertsState.currentFilter = filter;
    },

    addAlert(alert) {
        AlertsState.alerts.push(alert);
    },

    removeAlert(alertId) {
        AlertsState.alerts = AlertsState.alerts.filter(a => a.id != alertId);
    },

    updateAlert(alertId, updates) {
        const alert = AlertsState.alerts.find(a => a.id == alertId);
        if (alert) {
            Object.assign(alert, updates);
        }
    },

    addNotification(notification) {
        AlertsState.inAppNotifications.unshift(notification);
        if (!notification.read) {
            AlertsState.unreadNotificationsCount += 1;
        }
    },

    markNotificationRead(notificationId) {
        const notification = AlertsState.inAppNotifications.find(n => n.id === notificationId);
        if (notification && !notification.read) {
            notification.read = true;
            AlertsState.unreadNotificationsCount = Math.max(0, AlertsState.unreadNotificationsCount - 1);
        }
    },

    removeNotification(notificationId) {
        const notification = AlertsState.inAppNotifications.find(n => n.id === notificationId);
        if (notification && !notification.read) {
            AlertsState.unreadNotificationsCount = Math.max(0, AlertsState.unreadNotificationsCount - 1);
        }
        AlertsState.inAppNotifications = AlertsState.inAppNotifications.filter(n => n.id !== notificationId);
    }
};