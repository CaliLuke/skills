#!/usr/bin/env node
/**
 * Development server wrapper that spawns the SQLite log server
 * alongside Vite when VITE_DEBUG_SQLITE=true is set.
 *
 * Usage:
 *   node scripts/dev.mjs [vite args]
 */
import { spawn } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const projectRoot = resolve(__dirname, '..')

const args = process.argv.slice(2)
const env = { ...process.env }

// Check if SQLite debug logging is enabled via .env.local
let sqliteLogEnabled = false
try {
  const envLocal = readFileSync(resolve(projectRoot, '.env.local'), 'utf-8')
  sqliteLogEnabled = envLocal.includes('VITE_DEBUG_SQLITE=true')
} catch {
  // .env.local doesn't exist, that's fine
}

// Start log server if SQLite logging is enabled
let logServer = null
if (sqliteLogEnabled) {
  logServer = spawn('bun', ['run', resolve(projectRoot, 'scripts/log-server.ts')], {
    stdio: ['ignore', 'pipe', 'pipe'],
    env,
  })

  // Only show log server startup message, suppress ongoing output
  let startupComplete = false
  logServer.stdout.on('data', (data) => {
    if (!startupComplete) {
      const output = data.toString()
      if (output.includes('Debug Log Server Running')) {
        console.log('\x1b[36m[log-server]\x1b[0m SQLite debug logging active on port 3847')
        startupComplete = true
      }
    }
  })

  logServer.stderr.on('data', (data) => {
    console.error('\x1b[31m[log-server]\x1b[0m', data.toString().trim())
  })
}

// Start Vite
const vite = spawn('vite', args, { stdio: 'inherit', env })

vite.on('exit', (code) => {
  if (logServer) logServer.kill()
  process.exit(code ?? 0)
})

// Clean up log server on signals
process.on('SIGINT', () => {
  if (logServer) logServer.kill()
  process.exit(0)
})
process.on('SIGTERM', () => {
  if (logServer) logServer.kill()
  process.exit(0)
})
