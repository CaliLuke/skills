---
name: log-hunt
description: Hunt for frontend issues in SQLite debug logs. Use for "hunt for issues", "check logs", "log hunt", "find bugs in logs", "debug session", triaging errors/warnings from the SQLite debug DB, or wiping the log database.
---

# Log Hunt — SQLite Debug Triage

Systematic process for finding and triaging frontend issues using the SQLite debug log database.

## Prerequisites

- The app must be running (container or `bun run dev`)
- The log server must be running on port 3847 (`curl http://localhost:3847/stats`)
- `VITE_DEBUG_SQLITE=true` must be set

## Phase 1: Prepare a Clean Session

Wipe the database to start fresh. **NEVER delete the file** — the log server holds an open handle and will crash.

```bash
sqlite3 logs/debug.sqlite "DELETE FROM logs; VACUUM;"
```

Then tell the user to use the app and come back when ready.

## Phase 2: Scan for Issues

Run these queries in order:

### Overview

```bash
sqlite3 -column -header logs/debug.sqlite "SELECT level, COUNT(*) as count FROM logs GROUP BY level ORDER BY count DESC"
```

### All Errors and Warnings

```bash
sqlite3 -column -header logs/debug.sqlite "SELECT timestamp, level, event, substr(message,1,100) as message FROM logs WHERE level IN ('error','warn') ORDER BY timestamp DESC"
```

### Full Error/Warning Data (for root cause analysis)

```bash
sqlite3 -json logs/debug.sqlite "SELECT timestamp, event, data FROM logs WHERE level IN ('error','warn') ORDER BY timestamp DESC"
```

### Most Frequent Error Events (pattern detection)

```bash
sqlite3 -column -header logs/debug.sqlite "SELECT event, COUNT(*) as count FROM logs WHERE level='error' GROUP BY event ORDER BY count DESC LIMIT 10"
```

## Phase 3: Triage and Report

For each issue found, classify it and present a report. **Do NOT jump to implementing fixes.** Present the issue to the user with options so they can decide the approach.

### Classification

1. **Backend issue** — The frontend is behaving correctly but the backend returns errors, wrong data, or missing fields.
2. **Frontend issue** — The frontend has a bug in its own logic, error handling, or state management.
3. **Data issue** — Truncation, missing pagination, or stale cache causing incorrect data display.

### Report Format

For each issue, present:

```markdown
### Issue: <short title>

**Classification**: Backend / Frontend / Data
**Severity**: Error / Warning / Info
**Event**: `<event name from logs>`
**Frequency**: <how many times it appeared>

**What's happening**: <1-2 sentence description of the symptom>

**Root cause**: <what the logs reveal about why this is happening>

**Evidence**: <relevant log data, API responses, or code references>
```

Then provide options:

#### For backend issues

Provide an **actionable bug report** the user can hand to the backend team. Include:

- Endpoint and method
- What was sent vs what was received
- Expected behavior
- Impact on the frontend

**Do NOT work around backend issues in the frontend.** The fix belongs in the backend.

#### For frontend issues

Present **1 to 3 realistic fix options** with trade-offs so the user can pick the approach. If the fix is obvious, just present one option — don't invent alternatives to hit a number:

```markdown
**Option A**: <approach> (Recommended)

- Pros: ...
- Cons: ...
- Files: ...

**Option B**: <approach>

- Pros: ...
- Cons: ...
- Files: ...
```

**Do NOT implement any fix** until the user selects an option.

#### For data issues

Identify whether the root cause is backend (missing pagination/sorting) or frontend (not handling limits), then follow the appropriate path above.

## Important Rules

1. **Never implement fixes without user approval** — present the report, wait for a decision.
2. **Never work around backend bugs** — if the backend is returning wrong data, report it. Don't add frontend hacks to compensate.
3. **Always provide options for frontend fixes** — the user decides the approach, not the agent.
4. **Time-filter queries** — always use `WHERE timestamp > datetime('now', '-N minutes')` when re-checking after user actions.
5. **Never delete `logs/debug.sqlite`** — always use `DELETE FROM logs; VACUUM;` to wipe.
6. **Check the log server is running** before querying — `curl -s http://localhost:3847/stats | head -3`. If it's down, tell the user.
