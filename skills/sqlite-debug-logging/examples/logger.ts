/**
 * Frontend logger with SQLite debug logging support.
 *
 * When VITE_DEBUG_SQLITE=true, logs are sent to the local SQLite
 * log server for persistent, queryable storage.
 */

import { addLogEntry, downloadLogs as downloadLogBuffer, getLogsText as getBufferedLogsText } from './logBuffer'

// SQLite debug logging configuration
const SQLITE_LOG_ENABLED = import.meta.env.VITE_DEBUG_SQLITE === 'true'
const SQLITE_LOG_URL = 'http://localhost:3847/logs'

/** Available log levels. */
type Level = 'debug' | 'info' | 'warn' | 'error'

/**
 * Log entry structure following Elastic Common Schema (ECS).
 */
export type LogEntry = {
  '@timestamp': string
  'log.level': Level
  level: Level
  message: string
  'event.action': string
  event: { action: string }
  service: { name: string; environment: string }
  app: { component: string }
  labels: { log_origin: string }
} & Record<string, unknown>

/** Data passed to log function. */
type LogData = Record<string, unknown> & {
  message?: string
}

// Log level ordering for threshold checks
const LEVEL_ORDER: Record<Level, number> = { debug: 10, info: 20, warn: 30, error: 40 }

// Service configuration
const baseServiceName = (import.meta.env.VITE_SERVICE_NAME as string | undefined) ?? 'frontend'
const baseEnvironment = (import.meta.env.MODE as string | undefined) ?? 'development'
const envLogLevel = (import.meta.env.VITE_LOG_LEVEL as string | undefined)?.toLowerCase() as Level | undefined

/**
 * Gets the effective log threshold level.
 * Can be overridden at runtime via localStorage.
 */
function getThreshold(): Level {
  try {
    const override = typeof window !== 'undefined'
      ? (window.localStorage.getItem('log_level') || '').toLowerCase()
      : ''
    if (override && LEVEL_ORDER[override as Level]) return override as Level
  } catch {
    // Ignore storage errors
  }
  return envLogLevel && LEVEL_ORDER[envLogLevel] ? envLogLevel : 'info'
}

/** Checks if a log level should be logged. */
const shouldLog = (level: Level): boolean => LEVEL_ORDER[level] >= LEVEL_ORDER[getThreshold()]

/** Outputs log entry to browser console. */
function toConsole(entry: LogEntry) {
  if (import.meta.env.VITE_LOG_TO_CONSOLE === '0') return
  // Only output warn/error to reduce console noise
  if (entry.level === 'info' || entry.level === 'debug') return

  const { level, message, ...rest } = entry
  const cleaned = Object.fromEntries(
    Object.entries(rest).filter(([key]) =>
      !['@timestamp', 'event.action', 'event', 'service', 'app', 'level', 'message', 'log.level'].includes(key)
    )
  )
  const fn = level === 'error' ? console.error : console.warn
  if (Object.keys(cleaned).length > 0) {
    fn(`[${level}] ${message}`, cleaned)
  } else {
    fn(`[${level}] ${message}`)
  }
}

/** Gets the current browser route. */
function getCurrentRoute(): string {
  try {
    if (typeof window !== 'undefined' && window.location) {
      return window.location.pathname + window.location.search
    }
  } catch {
    // Ignore errors in non-browser environments
  }
  return 'unknown'
}

/**
 * Sends log entry to local SQLite debug server.
 * Fire-and-forget: errors are silently ignored.
 */
function toSqlite(entry: LogEntry) {
  if (!SQLITE_LOG_ENABLED) return

  const payload = {
    ...entry,
    route: getCurrentRoute(),
  }

  fetch(SQLITE_LOG_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).catch(() => {
    // Silently ignore - log server may not be running
  })
}

/**
 * Core logging function.
 */
export function log(level: Level, action: string, data: LogData = {}) {
  if (!shouldLog(level)) return

  const { message, ...rest } = data
  const entry: LogEntry = {
    '@timestamp': new Date().toISOString(),
    'log.level': level,
    level,
    message: message ?? action,
    'event.action': action,
    event: { action },
    service: { name: baseServiceName, environment: baseEnvironment },
    app: { component: 'frontend' },
    labels: { log_origin: 'frontend' },
    ...rest,
  }

  addLogEntry(entry)
  toConsole(entry)
  toSqlite(entry)
}

/** Logger convenience methods. */
export const logger = {
  debug: (action: string, data?: LogData) => log('debug', action, data),
  info: (action: string, data?: LogData) => log('info', action, data),
  warn: (action: string, data?: LogData) => log('warn', action, data),
  error: (action: string, data?: LogData) => log('error', action, data),
}

/** Get all buffered logs as JSONL text. */
export const getLogsText = () => getBufferedLogsText()

/** Download buffered logs as a file. */
export const downloadLogs = (filename?: string) => downloadLogBuffer(filename)
