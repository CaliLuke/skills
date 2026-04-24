/**
 * In-memory log buffer for downloadLogs() functionality.
 *
 * Keeps recent logs in memory for export, independent of SQLite storage.
 * Useful for sharing logs or when SQLite is not enabled.
 */

import type { LogEntry } from './logger'

const MAX_ENTRIES = 2000
const MAX_AGE_MS = 2 * 60 * 60 * 1000 // 2 hours

let buffer: LogEntry[] = []

/** Adds a log entry to the buffer. */
export function addLogEntry(entry: LogEntry) {
  buffer.push(entry)
  trimBuffer()
}

/** Gets all buffered logs as newline-separated JSON. */
export function getLogsText(): string {
  return buffer.map((entry) => JSON.stringify(entry)).join('\n')
}

/** Downloads buffered logs as a file. */
export function downloadLogs(filename = `logs-${Date.now()}.jsonl`) {
  try {
    const txt = getLogsText()
    const blob = new Blob([txt], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    document.body.removeChild(anchor)
    URL.revokeObjectURL(url)
  } catch {
    // Ignore download errors
  }
}

/** Trims buffer to maintain size and age limits. */
const trimBuffer = () => {
  // Enforce max entries
  if (buffer.length > MAX_ENTRIES) {
    buffer = buffer.slice(-MAX_ENTRIES)
  }

  // Remove entries older than MAX_AGE_MS
  const now = Date.now()
  buffer = buffer.filter((entry) => {
    const ts = Date.parse(entry['@timestamp'])
    return Number.isFinite(ts) ? now - ts <= MAX_AGE_MS : true
  })
}
