type LogLevel = 'debug' | 'info' | 'warn' | 'error'

const LEVELS: Record<LogLevel, number> = { debug: 0, info: 1, warn: 2, error: 3 }

const configuredLevel = (import.meta.env.VITE_LOG_LEVEL as LogLevel) || 'info'
const isProduction = import.meta.env.PROD
const threshold = LEVELS[configuredLevel] ?? 1

function shouldLog(level: LogLevel): boolean {
  if (isProduction && level !== 'error') return false
  return LEVELS[level] >= threshold
}

function formatMsg(level: LogLevel, msg: string): string {
  return `[${new Date().toISOString()}] [${level.toUpperCase()}] ${msg}`
}

export const logger = {
  debug(msg: string, ...args: unknown[]) {
    if (shouldLog('debug')) console.debug(formatMsg('debug', msg), ...args)
  },
  info(msg: string, ...args: unknown[]) {
    if (shouldLog('info')) console.info(formatMsg('info', msg), ...args)
  },
  warn(msg: string, ...args: unknown[]) {
    if (shouldLog('warn')) console.warn(formatMsg('warn', msg), ...args)
  },
  error(msg: string, ...args: unknown[]) {
    if (shouldLog('error')) console.error(formatMsg('error', msg), ...args)
  },

  /** Log an API response (debug level) */
  apiResponse(method: string, url: string, status: number, durationMs: number) {
    this.debug(`${method} ${url} → ${status} (${durationMs}ms)`)
  },

  /** Log a performance measurement (debug level) */
  perf(label: string, durationMs: number) {
    this.debug(`perf: ${label} took ${durationMs}ms`)
  },
}
