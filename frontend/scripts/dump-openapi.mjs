import { spawnSync } from 'node:child_process'
import { writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const backendRoot = resolve(frontendRoot, '..', 'backend')
const outputPath = resolve(frontendRoot, 'openapi.json')

const python = [
  'import json',
  'import sys',
  'from freestack.main import app',
  'json.dump(app.openapi(), sys.stdout)',
].join('\n')

const result = spawnSync('uv', ['run', 'python', '-c', python], {
  cwd: backendRoot,
  encoding: 'utf8',
})

if (result.error) {
  throw result.error
}
if (result.status !== 0) {
  throw new Error(result.stderr || `uv exited with status ${result.status}`)
}

const spec = JSON.parse(result.stdout)
writeFileSync(outputPath, `${JSON.stringify(spec, null, 2)}\n`)
