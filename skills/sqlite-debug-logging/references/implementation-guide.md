# SQLite Debug Logging - Implementation Guide

This guide provides detailed implementation notes and advanced patterns for the SQLite debug logging system.

## How It Works

### Request Flow

1. **Frontend calls `logger.info('action', { data })`**
2. **Logger creates ECS-formatted LogEntry**
3. **`toSqlite()` sends fire-and-forget POST to localhost:3847**
4. **Log server inserts into SQLite with extracted component/route**
5. **1% chance: cleanup entries older than 24 hours**

### Fire-and-Forget Pattern

The `toSqlite()` function is designed to never block or fail visibly:

```typescript
function toSqlite(entry: LogEntry) {
  if (!SQLITE_LOG_ENABLED) return

  fetch(SQLITE_LOG_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...entry, route: getCurrentRoute() }),
  }).catch(() => {})  // Silent failure
}
```

This ensures:
- No UI blocking on slow network
- No errors if log server isn't running
- No retry logic complexity

### Component Extraction

The log server automatically extracts component names from event actions:

```typescript
function extractComponent(event: string): string {
  const parts = event.split(".");
  return parts.length > 1 ? parts[0] : "unknown";
}
```

Examples:
- `authForm.submitFailed` → component: `authForm`
- `api.request.error` → component: `api`
- `error` → component: `unknown`

### Route Capture

The frontend automatically captures the browser route:

```typescript
function getCurrentRoute(): string {
  try {
    if (typeof window !== 'undefined' && window.location) {
      return window.location.pathname + window.location.search
    }
  } catch {
    return 'unknown'
  }
  return 'unknown'
}
```

This enables queries like:
```sql
SELECT * FROM logs WHERE route LIKE '/settings%'
```

## Log Entry Structure (ECS)

The system uses Elastic Common Schema (ECS) for compatibility with observability tools:

```typescript
type LogEntry = {
  '@timestamp': string           // ISO 8601: "2024-01-15T10:30:00.000Z"
  'log.level': Level             // ECS field
  level: Level                   // Convenience field
  message: string                // Human-readable message
  'event.action': string         // Action identifier
  event: { action: string }      // ECS nested format
  service: {
    name: string                 // e.g., "my-frontend"
    environment: string          // e.g., "development"
  }
  app: { component: string }     // Application component
  labels: { log_origin: string } // Origin marker
} & Record<string, unknown>      // Additional fields
```

## Advanced Patterns

### Structured Event Logging

Create domain-specific log events:

```typescript
// events.ts
export const logFormSubmit = (formName: string, success: boolean, data?: object) => {
  logger.info(`${formName}.submit${success ? 'Success' : 'Failed'}`, {
    message: `Form ${formName} submission ${success ? 'succeeded' : 'failed'}`,
    formName,
    success,
    ...data,
  })
}

// Usage
logFormSubmit('loginForm', false, { error: 'Invalid credentials' })
```

### Trace IDs for Request Correlation

Add trace IDs to correlate related logs:

```typescript
const traceId = crypto.randomUUID()

logger.info('api.request.start', {
  message: 'Starting API request',
  trace_id: traceId,
  url: '/api/users',
})

// Later...
logger.info('api.request.complete', {
  message: 'API request completed',
  trace_id: traceId,
  duration_ms: 150,
})
```

Query correlated logs:
```sql
SELECT * FROM logs WHERE trace_id = 'abc-123' ORDER BY timestamp
```

### Error Serialization

Serialize errors properly for logging:

```typescript
function serializeError(error: unknown): Record<string, unknown> {
  if (error instanceof Error) {
    return {
      'error.message': error.message,
      'error.class': error.name,
      'error.stack_trace': error.stack?.slice(0, 2000),
    }
  }
  return { 'error.message': String(error) }
}

// Usage
try {
  await riskyOperation()
} catch (error) {
  logger.error('operation.failed', {
    message: 'Risky operation failed',
    ...serializeError(error),
  })
}
```

### React Console Interception

Capture React warnings automatically:

```typescript
const originalWarn = console.warn
const originalError = console.error

console.warn = (...args) => {
  const message = args.join(' ')
  if (message.includes('Warning:')) {
    logger.warn('react.warning', { message, raw: args })
  }
  originalWarn.apply(console, args)
}

console.error = (...args) => {
  const message = args.join(' ')
  if (message.includes('Error:') || message.includes('Warning:')) {
    logger.error('react.error', { message, raw: args })
  }
  originalError.apply(console, args)
}
```

## Database Optimization

### Index Usage

The default indexes cover common query patterns:

| Index | Optimizes |
|-------|-----------|
| `idx_logs_timestamp` | Time-range queries, cleanup |
| `idx_logs_level` | Filtering by severity |
| `idx_logs_event` | Finding specific events |
| `idx_logs_component` | Component-based filtering |
| `idx_logs_route` | Route-based filtering |

### Query Optimization Tips

```sql
-- Use indexes: filter on indexed columns first
SELECT * FROM logs
WHERE level = 'error'
  AND timestamp > datetime('now', '-1 hour')
ORDER BY timestamp DESC;

-- Avoid: full table scan
SELECT * FROM logs WHERE message LIKE '%error%';

-- Better: use event column
SELECT * FROM logs WHERE event LIKE '%.error';
```

### Batch Inserts

The log server accepts batch inserts for efficiency:

```typescript
// Frontend batching (optional optimization)
let pendingLogs: LogEntry[] = []
let flushTimeout: number | null = null

function queueLog(entry: LogEntry) {
  pendingLogs.push(entry)
  if (!flushTimeout) {
    flushTimeout = setTimeout(flushLogs, 100)
  }
}

function flushLogs() {
  if (pendingLogs.length > 0) {
    fetch(SQLITE_LOG_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pendingLogs),
    }).catch(() => {})
    pendingLogs = []
  }
  flushTimeout = null
}
```

## Extending the System

### Adding Custom Endpoints

Add new endpoints to log-server.ts:

```typescript
// Query endpoint
if (url.pathname === "/query" && req.method === "GET") {
  const level = url.searchParams.get('level')
  const limit = parseInt(url.searchParams.get('limit') || '100')

  let query = 'SELECT * FROM logs'
  if (level) query += ` WHERE level = '${level}'`
  query += ` ORDER BY timestamp DESC LIMIT ${limit}`

  const rows = db.query(query).all()
  return new Response(JSON.stringify(rows), {
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  })
}
```

### Custom Retention Policies

Implement per-level retention:

```typescript
function cleanupWithPolicy(db: Database) {
  // Keep errors for 7 days
  db.run(`DELETE FROM logs WHERE level = 'error' AND timestamp < datetime('now', '-7 days')`)

  // Keep warnings for 3 days
  db.run(`DELETE FROM logs WHERE level = 'warn' AND timestamp < datetime('now', '-3 days')`)

  // Keep info/debug for 24 hours
  db.run(`DELETE FROM logs WHERE level IN ('info', 'debug') AND timestamp < datetime('now', '-24 hours')`)
}
```

### Export to External Systems

Add periodic export to external logging:

```typescript
// Export to external system (e.g., hourly cron)
async function exportToExternal(db: Database) {
  const rows = db.query(`
    SELECT * FROM logs
    WHERE timestamp > datetime('now', '-1 hour')
    ORDER BY timestamp
  `).all()

  if (rows.length > 0) {
    await fetch('https://logs.example.com/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(rows),
    })
  }
}
```

## Debugging the Debug Logger

### Check if Logging is Working

```bash
# Check log server is running
curl http://localhost:3847/health

# Check stats
curl http://localhost:3847/stats | jq

# Watch logs in real-time
watch -n 1 'sqlite3 logs/debug.sqlite "SELECT timestamp, level, event FROM logs ORDER BY timestamp DESC LIMIT 5"'
```

### Common Issues

**Logs not appearing:**
1. Check `VITE_DEBUG_SQLITE=true` in `.env.local`
2. Restart dev server after changing env
3. Check browser network tab for failed requests to localhost:3847

**Database locked:**
```bash
# Find processes using the file
lsof logs/debug.sqlite

# Close all sqlite3 sessions before running dev server
```

**High disk usage:**
```bash
# Check database size
ls -lh logs/debug.sqlite

# Manual cleanup
sqlite3 logs/debug.sqlite "DELETE FROM logs WHERE timestamp < datetime('now', '-6 hours')"
sqlite3 logs/debug.sqlite "VACUUM"
```
