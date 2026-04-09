#!/usr/bin/env node

import path from 'node:path'
import { spawn } from 'node:child_process'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const cliEntrypoint = require.resolve('neuxnbcp/dist/index.js')

const child = spawn(process.execPath, [cliEntrypoint, ...process.argv.slice(2)], {
  stdio: 'inherit',
  windowsHide: true,
})

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal)
    return
  }
  process.exit(code ?? 0)
})

child.on('error', (error) => {
  console.error(error instanceof Error ? error.message : String(error))
  process.exit(1)
})
