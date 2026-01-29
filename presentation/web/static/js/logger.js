/**
 * Centralized Logging Utility for KubeOpt
 * ======================================
 * Respects LOG_LEVEL setting and provides consistent logging across all JS files
 */

class Logger {
    constructor() {
        // Get log level from meta tag or default to WARNING for production
        this.logLevel = this.getLogLevelFromMeta() || 'WARNING';
        this.logLevels = {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 2,
            'ERROR': 3,
            'CRITICAL': 4
        };
        this.currentLevel = this.logLevels[this.logLevel] || 2; // Default to WARNING
        
        // In production mode, suppress all console output except errors
        this.isProduction = this.getProductionModeFromMeta();
        if (this.isProduction) {
            this.currentLevel = Math.max(this.currentLevel, 3); // Minimum ERROR level in production
        }
    }

    getLogLevelFromMeta() {
        const metaTag = document.querySelector('meta[name="log-level"]');
        return metaTag ? metaTag.getAttribute('content').toUpperCase() : null;
    }

    getProductionModeFromMeta() {
        const metaTag = document.querySelector('meta[name="production-mode"]');
        return metaTag ? metaTag.getAttribute('content') === 'true' : false;
    }

    shouldLog(level) {
        return this.logLevels[level] >= this.currentLevel;
    }

    debug(message, ...args) {
        if (this.shouldLog('DEBUG')) {
            console.debug(`[DEBUG] ${message}`, ...args);
        }
    }

    info(message, ...args) {
        if (this.shouldLog('INFO')) {
            console.info(`[INFO] ${message}`, ...args);
        }
    }

    warning(message, ...args) {
        if (this.shouldLog('WARNING')) {
            console.warn(`[WARNING] ${message}`, ...args);
        }
    }

    warn(message, ...args) {
        this.warning(message, ...args);
    }

    error(message, ...args) {
        if (this.shouldLog('ERROR')) {
            console.error(`[ERROR] ${message}`, ...args);
        }
    }

    critical(message, ...args) {
        if (this.shouldLog('CRITICAL')) {
            console.error(`[CRITICAL] ${message}`, ...args);
        }
    }

    // Legacy support for existing console.log calls
    log(message, ...args) {
        // Treat generic log() calls as debug level
        this.debug(message, ...args);
    }

    // API response logging with level awareness
    logApiResponse(response, endpoint) {
        if (response.ok) {
            this.debug(`API Success: ${endpoint}`, response);
        } else {
            this.error(`API Error: ${endpoint}`, response);
        }
    }

    // Chart/UI event logging with level awareness
    logUserAction(action, details) {
        this.info(`User Action: ${action}`, details);
    }

    // Performance logging
    logPerformance(operation, duration) {
        if (duration > 1000) {
            this.warning(`Slow operation: ${operation} took ${duration}ms`);
        } else {
            this.debug(`Operation: ${operation} completed in ${duration}ms`);
        }
    }
}

// Create global logger instance
window.logger = new Logger();

// Override console methods in production to reduce noise
if (window.logger.isProduction) {
    // Save original console methods
    const originalConsole = {
        log: console.log,
        info: console.info,
        debug: console.debug,
        warn: console.warn,
        error: console.error
    };

    // Override console methods to use our logger
    console.log = (...args) => window.logger.log(...args);
    console.info = (...args) => window.logger.info(...args);
    console.debug = (...args) => window.logger.debug(...args);
    console.warn = (...args) => window.logger.warn(...args);
    // Keep console.error as-is for actual errors
}