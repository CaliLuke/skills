/**
 * Local SQLite debug log server for development.
 * Receives log entries from the frontend and stores them in SQLite.
 *
 * Usage:
 *   bun run scripts/log-server.ts
 *
 * Endpoints:
 *   POST /logs   - Ingest log entries (single or batch)
 *   GET  /stats  - View log statistics
 *   GET  /health - Health check
 *
 * Logs are stored in logs/debug.sqlite with 24-hour retention.
 */

import { Database } from "bun:sqlite";
import { mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const PORT = 3847;
const RETENTION_HOURS = 24;

// Resolve paths relative to project root
const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, "..");
const LOGS_DIR = join(PROJECT_ROOT, "logs");
const DB_PATH = join(LOGS_DIR, "debug.sqlite");

/** Ensures the logs directory exists. */
async function ensureLogsDir(): Promise<void> {
  if (!existsSync(LOGS_DIR)) {
    await mkdir(LOGS_DIR, { recursive: true });
    console.log(`Created logs directory: ${LOGS_DIR}`);
  }
}

/** Initializes the SQLite database with the logs table. */
function initDatabase(): Database {
  const db = new Database(DB_PATH, { create: true });

  // Create logs table
  db.run(`
    CREATE TABLE IF NOT EXISTS logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp TEXT NOT NULL,
      level TEXT NOT NULL,
      event TEXT NOT NULL,
      message TEXT,
      data TEXT,
      component TEXT,
      route TEXT,
      trace_id TEXT,
      created_at TEXT DEFAULT (datetime('now'))
    )
  `);

  // Create indexes for efficient querying
  db.run(`CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_logs_event ON logs(event)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_logs_component ON logs(component)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_logs_route ON logs(route)`);

  console.log(`Database initialized: ${DB_PATH}`);
  return db;
}

/** Cleans up log entries older than RETENTION_HOURS. */
function cleanupOldLogs(db: Database): number {
  const result = db.run(
    `DELETE FROM logs WHERE timestamp < datetime('now', '-${RETENTION_HOURS} hours')`
  );
  return result.changes;
}

/** Extracts component name from event string (e.g., "form.submit" -> "form") */
function extractComponent(event: string): string {
  const parts = event.split(".");
  return parts.length > 1 ? parts[0] : "unknown";
}

/** Log entry type matching frontend LogEntry structure. */
type LogEntryPayload = {
  "@timestamp": string;
  level: string;
  "event.action": string;
  message?: string;
  route?: string;
  trace_id?: string;
  [key: string]: unknown;
};

/** Inserts a log entry into the database. */
function insertLog(db: Database, entry: LogEntryPayload): void {
  const event = entry["event.action"] || "unknown";
  const component = extractComponent(event);

  // Extract known fields, put rest in data
  const {
    "@timestamp": timestamp,
    level,
    "event.action": _event,
    message,
    route,
    trace_id,
    // Exclude internal fields from data
    "log.level": _logLevel,
    event: _eventObj,
    service: _service,
    app: _app,
    labels: _labels,
    ...rest
  } = entry;

  const stmt = db.prepare(`
    INSERT INTO logs (timestamp, level, event, message, data, component, route, trace_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);

  stmt.run(
    timestamp,
    level,
    event,
    message || null,
    Object.keys(rest).length > 0 ? JSON.stringify(rest) : null,
    component,
    route || null,
    trace_id || null
  );
}

/** Main server setup. */
async function main(): Promise<void> {
  await ensureLogsDir();
  const db = initDatabase();

  // Initial cleanup
  const cleaned = cleanupOldLogs(db);
  if (cleaned > 0) {
    console.log(`Cleaned up ${cleaned} old log entries`);
  }

  const server = Bun.serve({
    port: PORT,
    async fetch(req) {
      const url = new URL(req.url);

      // CORS headers for local development
      const corsHeaders = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      };

      // Handle preflight
      if (req.method === "OPTIONS") {
        return new Response(null, { status: 204, headers: corsHeaders });
      }

      // Health check
      if (url.pathname === "/health") {
        return new Response("ok", { headers: corsHeaders });
      }

      // Log ingestion endpoint
      if (url.pathname === "/logs" && req.method === "POST") {
        try {
          const body = await req.json();

          // Handle batch or single entry
          const entries: LogEntryPayload[] = Array.isArray(body) ? body : [body];

          for (const entry of entries) {
            insertLog(db, entry);
          }

          // Cleanup old entries periodically (1% chance per request)
          if (Math.random() < 0.01) {
            const cleaned = cleanupOldLogs(db);
            if (cleaned > 0) {
              console.log(`Cleaned up ${cleaned} old log entries`);
            }
          }

          return new Response(JSON.stringify({ ok: true, count: entries.length }), {
            status: 200,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        } catch (error) {
          console.error("Failed to process log entry:", error);
          return new Response(JSON.stringify({ error: "Invalid request" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }
      }

      // Stats endpoint
      if (url.pathname === "/stats") {
        const stats = db.query(`
          SELECT
            COUNT(*) as total,
            SUM(CASE WHEN level = 'debug' THEN 1 ELSE 0 END) as debug_count,
            SUM(CASE WHEN level = 'info' THEN 1 ELSE 0 END) as info_count,
            SUM(CASE WHEN level = 'warn' THEN 1 ELSE 0 END) as warn_count,
            SUM(CASE WHEN level = 'error' THEN 1 ELSE 0 END) as error_count,
            MIN(timestamp) as oldest,
            MAX(timestamp) as newest
          FROM logs
        `).get();

        return new Response(JSON.stringify(stats, null, 2), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }

      return new Response("Not found", { status: 404, headers: corsHeaders });
    },
  });

  console.log(`
╔══════════════════════════════════════════════════════════════╗
║  Debug Log Server Running                                     ║
╠══════════════════════════════════════════════════════════════╣
║  Port:      ${PORT}                                            ║
║  Database:  logs/debug.sqlite                                 ║
║  Retention: ${RETENTION_HOURS} hours                                        ║
╠══════════════════════════════════════════════════════════════╣
║  Endpoints:                                                   ║
║    POST /logs   - Ingest log entries                         ║
║    GET  /stats  - View log statistics                        ║
║    GET  /health - Health check                               ║
╚══════════════════════════════════════════════════════════════╝

Query logs with:
  sqlite3 logs/debug.sqlite "SELECT * FROM logs ORDER BY timestamp DESC LIMIT 10"
`);
}

main().catch(console.error);
