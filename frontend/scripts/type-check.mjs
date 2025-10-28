import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const isWindows = process.platform === 'win32'
const tscBin = join(
  __dirname,
  '..',
  'node_modules',
  '.bin',
  isWindows ? 'tsc.cmd' : 'tsc'
)

const child = spawn(tscBin, ['--noEmit'], {
  stdio: 'inherit',
  env: {
    ...process.env,
    NO_COLOR: process.env.NO_COLOR ?? '1'
  }
})

child.on('exit', (code) => {
  process.exit(code ?? 0)
})

child.on('error', (error) => {
  console.error('Failed to run tsc:', error)
  process.exit(1)
})
