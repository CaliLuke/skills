---
name: SQLite Debug Logging
description: Token-efficient SQLite-based debug logging for frontend projects — local log server, structured logs, AI-friendly triage that persists across page refreshes. Use for "add debug logging", "set up SQLite logging", "AI-friendly logging", or frontend observability.
---

# SQLite Debug Logging for AI-Assisted Debugging

This skill teaches you how to leverage SQLite-based debug logging for efficient debugging. SQLite logs are far more token-efficient than raw console output or log files.

## Why SQLite for Debugging?

| Raw Logs Problem                         | SQLite Solution            |
| ---------------------------------------- | -------------------------- |
| Parsing thousands of lines wastes tokens | Query only what you need   |
| Lost on page refresh                     | Persists to disk           |
| No structure, hard to filter             | Indexed, queryable columns |
| Grep returns too much context            | SQL returns exact matches  |

## Debugging Strategy

### Step 1: Assess the Situation

Before querying, understand what you're looking for:

```bash
# Get an overview of what's in the logs
sqlite3 logs/debug.sqlite "SELECT level, COUNT(*) FROM logs GROUP BY level"

# Check the time range of available logs
sqlite3 logs/debug.sqlite "SELECT MIN(timestamp), MAX(timestamp) FROM logs"
```

### Step 2: Start Broad, Then Narrow

**Don't** start with complex queries. Layer filters progressively:

```bash
# 1. Recent errors (start here for most debugging)
sqlite3 logs/debug.sqlite "SELECT timestamp, event, message FROM logs WHERE level='error' ORDER BY timestamp DESC LIMIT 20"

# 2. If too many results, narrow by time
sqlite3 logs/debug.sqlite "SELECT * FROM logs WHERE level='error' AND timestamp > datetime('now', '-5 minutes')"

# 3. If still too broad, filter by component or route
sqlite3 logs/debug.sqlite "SELECT * FROM logs WHERE level='error' AND component='formName' ORDER BY timestamp DESC"
```

### Step 3: Follow the Trail

Once you find an error, trace backwards:

```bash
# Find what happened before an error (get context)
sqlite3 logs/debug.sqlite "SELECT timestamp, level, event, message FROM logs WHERE timestamp < '2024-01-15T10:30:00' ORDER BY timestamp DESC LIMIT 10"

# If there's a trace_id, follow the entire flow
sqlite3 logs/debug.sqlite "SELECT * FROM logs WHERE json_extract(data, '$.trace_id') = 'abc-123' ORDER BY timestamp"
```

## Query Patterns by Debugging Scenario

### "Something broke but I don't know what"

```bash
# Recent errors with full context
sqlite3 -column -header logs/debug.sqlite "
  SELECT timestamp, event, message,
         json_extract(data, '$.error') as error
  FROM logs
  WHERE level = 'error'
  ORDER BY timestamp DESC
  LIMIT 10
"
```

### "A specific feature isn't working"

```bash
# Filter by component (extracted from event prefix like 'auth.loginFailed' -> 'auth')
sqlite3 logs/debug.sqlite "SELECT * FROM logs WHERE component = 'auth' ORDER BY timestamp DESC LIMIT 20"

# Or by route if you know where the problem occurs
sqlite3 logs/debug.sqlite "SELECT * FROM logs WHERE route LIKE '/settings%' ORDER BY timestamp DESC"
```

### "Something is slow"

```bash
# Look for duration data in logs
sqlite3 logs/debug.sqlite "
  SELECT timestamp, event, json_extract(data, '$.duration_ms') as duration
  FROM logs
  WHERE json_extract(data, '$.duration_ms') > 1000
  ORDER BY timestamp DESC
"
```

### "User reports intermittent issue"

```bash
# Find patterns - which events fail most often
sqlite3 logs/debug.sqlite "
  SELECT event, COUNT(*) as count
  FROM logs
  WHERE level = 'error'
  GROUP BY event
  ORDER BY count DESC
"

# Check if errors cluster at certain times
sqlite3 logs/debug.sqlite "
  SELECT strftime('%H:%M', timestamp) as minute, COUNT(*)
  FROM logs
  WHERE level = 'error'
  GROUP BY minute
"
```

### "I need to see the full data payload"

```bash
# Pretty-print JSON data for a specific log entry
sqlite3 -json logs/debug.sqlite "SELECT * FROM logs WHERE id = 123"

# Extract nested JSON fields
sqlite3 logs/debug.sqlite "
  SELECT timestamp,
         json_extract(data, '$.request.url') as url,
         json_extract(data, '$.response.status') as status
  FROM logs
  WHERE event LIKE 'api.%'
"
```

## Output Formats

Choose the right format for your needs:

```bash
# Default: pipe-separated (good for quick scans)
sqlite3 logs/debug.sqlite "SELECT timestamp, level, event FROM logs LIMIT 5"

# Column mode: aligned columns with headers (best for reading)
sqlite3 -column -header logs/debug.sqlite "SELECT timestamp, level, event FROM logs LIMIT 5"

# JSON: structured output (good for further processing)
sqlite3 -json logs/debug.sqlite "SELECT * FROM logs LIMIT 5"

# Line mode: one field per line (good for long values)
sqlite3 -line logs/debug.sqlite "SELECT * FROM logs WHERE id = 1"
```

## Common Schema

Most SQLite debug logging implementations use this schema:

| Column      | Type    | Description                                   |
| ----------- | ------- | --------------------------------------------- |
| `id`        | INTEGER | Auto-incrementing primary key                 |
| `timestamp` | TEXT    | ISO 8601 timestamp                            |
| `level`     | TEXT    | `debug`, `info`, `warn`, `error`              |
| `event`     | TEXT    | Action identifier (e.g., `form.submitFailed`) |
| `message`   | TEXT    | Human-readable description                    |
| `data`      | TEXT    | JSON-encoded additional context               |
| `component` | TEXT    | Extracted from event prefix                   |
| `route`     | TEXT    | Browser route when logged                     |

Always check the actual schema if queries fail:

```bash
sqlite3 logs/debug.sqlite ".schema logs"
```

## Efficiency Tips

1. **Use indexes**: Filter on `timestamp`, `level`, `event`, `component`, `route` first - these are typically indexed
2. **Avoid `LIKE '%pattern%'`**: Full-text search is slow. Use `event LIKE 'prefix.%'` instead
3. **Limit results**: Always use `LIMIT` when exploring. Start with 10-20 rows
4. **Use `json_extract` sparingly**: It's slower than column access. Filter by indexed columns first

## Verifying the System is Working

```bash
# Check if server is running
curl http://localhost:3847/health

# Check log statistics
curl http://localhost:3847/stats

# Verify database exists and has data
sqlite3 logs/debug.sqlite "SELECT COUNT(*) FROM logs"
```

## When NOT to Use SQLite Logs

- **Production debugging**: These are for local development only
- **Real-time streaming**: Use `tail -f` on file-based logs instead
- **Distributed tracing**: Use proper observability tools (Jaeger, etc.)

---

## Setting Up SQLite Debug Logging

### Architecture Overview

```text
┌─────────────────────┐     POST /logs      ┌──────────────────┐
│   Frontend Logger   │  ─────────────────► │   Log Server     │
│   (fire-and-forget) │                     │   (port 3847)    │
└─────────────────────┘                     └────────┬─────────┘
                                                     │
                                                     ▼
                                            ┌────────────────┐
                                            │ debug.sqlite   │
                                            │ auto-cleanup   │
                                            └────────────────┘
```

The system has three parts:

1. **Log server**: A lightweight HTTP server that writes logs to SQLite
2. **Frontend logger**: Sends structured log entries via fire-and-forget fetch
3. **Dev script**: Starts both the log server and your dev server together

## Step 1: Create the Log Server

Create a file like `scripts/log-server.ts` (or `.js`):

**Key requirements:**

- Listen on a dedicated port (e.g., 3847)
- Accept POST `/logs` with JSON body (single entry or array)
- Extract `component` from event string (e.g., `auth.loginFailed` → `auth`)
- Store arbitrary fields in a `data` JSON column
- Run periodic cleanup (e.g., delete entries older than 24 hours)
- Enable CORS for local development

**Minimal schema:**

```sql
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  level TEXT NOT NULL,
  event TEXT NOT NULL,
  message TEXT,
  data TEXT,
  component TEXT,
  route TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_event ON logs(event);
CREATE INDEX IF NOT EXISTS idx_logs_component ON logs(component);
CREATE INDEX IF NOT EXISTS idx_logs_route ON logs(route);
```

See `examples/log-server.ts` for a complete Bun implementation.

## Step 2: Add the Frontend Logger Integration

Add a function that sends logs to SQLite alongside your existing logging:

```typescript
const SQLITE_LOG_ENABLED = import.meta.env.VITE_DEBUG_SQLITE === "true";
const SQLITE_LOG_URL = "http://localhost:3847/logs";

function toSqlite(entry: LogEntry) {
  if (!SQLITE_LOG_ENABLED) return;

  fetch(SQLITE_LOG_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...entry,
      route: window.location.pathname,
    }),
  }).catch(() => {}); // Fire-and-forget, silent failure
}
```

**Critical design decisions:**

- **Fire-and-forget**: Never await, never retry, catch and ignore errors
- **Environment gated**: Only enable in development via env var
- **Non-blocking**: Must not affect app performance or behavior
- **Silent failure**: If log server is down, app continues normally

## Step 3: Create a Dev Script

Create a script that starts the log server alongside your dev server:

```javascript
// scripts/dev.mjs
import { spawn } from "child_process";

const logServer = spawn("bun", ["run", "scripts/log-server.ts"], {
  stdio: "inherit",
});

const devServer = spawn("bun", ["run", "vite"], {
  stdio: "inherit",
});

process.on("SIGINT", () => {
  logServer.kill();
  devServer.kill();
  process.exit();
});
```

Update `package.json`:

```json
{
  "scripts": {
    "dev": "node scripts/dev.mjs"
  }
}
```

## Step 4: Configure Environment

```bash
# .env.local
VITE_DEBUG_SQLITE=true
```

Add to `.gitignore`:

```text
logs/
```

## Structured Event Naming

Use consistent event naming for better queryability:

```text
{component}.{action}[.{result}]
```

Examples:

- `auth.login.success`
- `auth.login.failed`
- `form.submit.validationError`
- `api.request.timeout`
- `cart.checkout.completed`

This allows queries like:

```sql
-- All auth events
SELECT * FROM logs WHERE component = 'auth'

-- All failures across components
SELECT * FROM logs WHERE event LIKE '%.failed'

-- All API requests
SELECT * FROM logs WHERE event LIKE 'api.request.%'
```

## Logging Best Practices

### Always include context

```typescript
// Bad: no context
logger.error("form.submit.failed", { message: "Form failed" });

// Good: actionable context
logger.error("form.submit.failed", {
  message: "Form validation failed",
  formName: "checkout",
  validationErrors: errors,
  fieldValues: sanitizedValues, // never log passwords/tokens
});
```

### Use trace IDs for request flows

```typescript
const traceId = crypto.randomUUID();

logger.info("checkout.started", { trace_id: traceId, cartId });
// ... later
logger.info("checkout.paymentProcessed", { trace_id: traceId, amount });
// ... later
logger.info("checkout.completed", { trace_id: traceId, orderId });
```

Query the entire flow:

```sql
SELECT * FROM logs WHERE json_extract(data, '$.trace_id') = 'abc-123' ORDER BY timestamp
```

### Serialize errors properly

```typescript
function serializeError(error: unknown) {
  if (error instanceof Error) {
    return {
      error_message: error.message,
      error_class: error.name,
      error_stack: error.stack?.slice(0, 2000),
    };
  }
  return { error_message: String(error) };
}

// Usage
logger.error("operation.failed", {
  message: "Operation failed",
  ...serializeError(error),
});
```

## Adapting to Different Stacks

The pattern works with any stack. Adapt these pieces:

| Stack          | Log Server                            | Dev Script           | Env Var                    |
| -------------- | ------------------------------------- | -------------------- | -------------------------- |
| Vite + Bun     | `bun run scripts/log-server.ts`       | Spawn both processes | `VITE_DEBUG_SQLITE`        |
| Next.js        | Same server, different port           | Use `concurrently`   | `NEXT_PUBLIC_DEBUG_SQLITE` |
| Node + Express | Express middleware or separate server | npm-run-all          | `DEBUG_SQLITE`             |
| Plain HTML/JS  | Same server                           | Just start server    | Check at runtime           |

## Implementation Reference

For complete working code:

- `examples/log-server.ts` - Full Bun server with CORS, cleanup, stats
- `examples/dev.mjs` - Dev wrapper script
- `examples/logger.ts` - Frontend logger with toSqlite integration
- `references/implementation-guide.md` - Advanced patterns and customization
