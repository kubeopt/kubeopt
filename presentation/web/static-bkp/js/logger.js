/**
 * AKS Cost Optimizer - Logging Utility
 * =====================================
 * 
 * Provides centralized logging with configurable levels to reduce console noise.
 * Respects LOG_LEVEL environment setting and production mode.
 * 
 * Developer: Srinivas Kondepudi
 * Organization: Nivaya Technologies & kubeopt
 */

(function() {
    'use strict';

    // Log levels (higher number = more verbose)
    const LOG_LEVELS = {
        ERROR: 1,
        WARN: 2,
        INFO: 3,
        DEBUG: 4
    };

    class Logger {
        constructor() {
            this.currentLevel = this.determineLogLevel();
            this.isProduction = this.isProductionMode();
            
            // In production, suppress all but errors unless explicitly configured
            if (this.isProduction && this.currentLevel > LOG_LEVELS.ERROR) {
                this.currentLevel = LOG_LEVELS.ERROR;
            }
        }

        determineLogLevel() {
            // Check if LOG_LEVEL is set via meta tag or global variable
            const metaLogLevel = document.querySelector('meta[name="log-level"]');
            if (metaLogLevel) {
                const level = metaLogLevel.getAttribute('content').toUpperCase();
                return LOG_LEVELS[level] || LOG_LEVELS.INFO;
            }

            // Check for global window variable
            if (window.LOG_LEVEL) {
                const level = window.LOG_LEVEL.toString().toUpperCase();
                return LOG_LEVELS[level] || LOG_LEVELS.INFO;
            }

            // Check URL parameter for debugging
            const urlParams = new URLSearchParams(window.location.search);
            const debugParam = urlParams.get('debug');
            if (debugParam === 'true' || debugParam === '1') {
                return LOG_LEVELS.DEBUG;
            }

            // Default to INFO level
            return LOG_LEVELS.INFO;
        }

        isProductionMode() {
            // Check if production mode is set
            const metaProduction = document.querySelector('meta[name="production-mode"]');
            if (metaProduction) {
                return metaProduction.getAttribute('content') === 'true';
            }

            // Check for global window variable
            if (window.PRODUCTION_MODE !== undefined) {
                return window.PRODUCTION_MODE === true || window.PRODUCTION_MODE === 'true';
            }

            // Check hostname for production indicators
            const hostname = window.location.hostname;
            return !hostname.includes('localhost') && 
                   !hostname.includes('127.0.0.1') && 
                   !hostname.includes('dev');
        }

        error(message, ...args) {
            if (this.currentLevel >= LOG_LEVELS.ERROR) {
                console.error(`[ERROR]`, message, ...args);
            }
        }

        warn(message, ...args) {
            if (this.currentLevel >= LOG_LEVELS.WARN) {
                console.warn(`[WARN]`, message, ...args);
            }
        }

        info(message, ...args) {
            if (this.currentLevel >= LOG_LEVELS.INFO) {
                console.info(`[INFO]`, message, ...args);
            }
        }

        debug(message, ...args) {
            if (this.currentLevel >= LOG_LEVELS.DEBUG) {
                logDebug(`[DEBUG]`, message, ...args);
            }
        }

        // Convenience methods for common logging patterns
        apiCall(method, url, data) {
            this.debug(`API ${method}:`, url, data ? data : '');
        }

        userAction(action, details) {
            this.info(`User Action: ${action}`, details || '');
        }

        featureAccess(feature, allowed) {
            this.debug(`Feature Access: ${feature} - ${allowed ? 'ALLOWED' : 'BLOCKED'}`);
        }

        performance(label, duration) {
            this.debug(`Performance: ${label} took ${duration}ms`);
        }

        // Analysis data logging - commonly used for debugging
        analysisData(label, data) {
            this.debug(`📊 Analysis Data - ${label}:`, data);
        }

        chartData(chartType, data) {
            this.debug(`📈 Chart Data - ${chartType}:`, data);
        }

        apiResponse(endpoint, status, data) {
            if (status >= 400) {
                this.error(`❌ API Error - ${endpoint} (${status}):`, data);
            } else {
                this.debug(`✅ API Success - ${endpoint} (${status}):`, data);
            }
        }

        clusterAction(clusterId, action, details) {
            this.info(`🏗️ Cluster ${clusterId} - ${action}:`, details || '');
        }

        // Method to temporarily enable debug logging
        enableDebug() {
            this.currentLevel = LOG_LEVELS.DEBUG;
            this.info('Debug logging enabled');
        }

        // Method to disable all logging except errors
        silent() {
            this.currentLevel = LOG_LEVELS.ERROR;
            console.warn('[WARN] Logging set to silent mode - only errors will be shown');
        }

        // Get current log level info
        getInfo() {
            const levelName = Object.keys(LOG_LEVELS).find(key => LOG_LEVELS[key] === this.currentLevel);
            return {
                level: this.currentLevel,
                levelName: levelName,
                isProduction: this.isProduction
            };
        }
    }

    // Create global logger instance
    window.Logger = new Logger();

    // Expose convenience functions to global scope for easy migration
    window.logError = (msg, ...args) => window.Logger.error(msg, ...args);
    window.logWarn = (msg, ...args) => window.Logger.warn(msg, ...args);
    window.logDebug = (msg, ...args) => window.Logger.info(msg, ...args);
    window.logDebug = (msg, ...args) => window.Logger.debug(msg, ...args);
    
    // Expose analysis-specific logging functions
    window.logAnalysisData = (label, data) => window.Logger.analysisData(label, data);
    window.logChartData = (chartType, data) => window.Logger.chartData(chartType, data);
    window.logApiResponse = (endpoint, status, data) => window.Logger.apiResponse(endpoint, status, data);
    window.logClusterAction = (clusterId, action, details) => window.Logger.clusterAction(clusterId, action, details);

    // Log initialization
    const logDebug = window.Logger.getInfo();
    console.info(`[INFO] Logger initialized - Level: ${logDebug.levelName} (${logDebug.level}), Production: ${logDebug.isProduction}`);

})();