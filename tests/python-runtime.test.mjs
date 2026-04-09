import assert from 'node:assert/strict'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath, pathToFileURL } from 'node:url'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const pythonRuntimeModuleUrl = pathToFileURL(
  path.join(repoRoot, 'packages', 'cli', 'dist', 'python-runtime.js'),
).href

const createDeps = ({
  platform = 'win32',
  existingPaths = [],
  requirementsText = 'numpy>=1.25\npandas>=2.2\n',
  onRun,
} = {}) => {
  const existing = new Set(existingPaths.map((value) => path.normalize(value)))
  const written = new Map()

  return {
    platform,
    env: {},
    existsSync: (targetPath) => existing.has(path.normalize(targetPath)),
    mkdir: async (targetPath) => {
      existing.add(path.normalize(targetPath))
    },
    readFile: async () => requirementsText,
    writeFile: async (targetPath, content) => {
      const normalized = path.normalize(targetPath)
      existing.add(normalized)
      written.set(normalized, String(content))
    },
    runCommand: async (command, args, options = {}) => {
      if (onRun) {
        return onRun({ command, args, options, existing, written })
      }

      return { code: 0, stdout: '', stderr: '' }
    },
  }
}

test('runPythonAnalysisProgram bootstraps Python on Windows and launches the selected script', async () => {
  const { getVenvPythonPath, runPythonAnalysisProgram } = await import(pythonRuntimeModuleUrl)

  const envDir = path.join(repoRoot, '.tmp-tests', 'python-env-bootstrap')
  const venvPython = getVenvPythonPath(envDir, 'win32')
  const calls = []
  let versionChecks = 0

  const deps = createDeps({
    existingPaths: [repoRoot],
    onRun: async ({ command, args, existing }) => {
      calls.push({ command, args })

      if (args.at(-1) === '--version') {
        versionChecks += 1
        if (versionChecks < 4) {
          return { code: 1, stdout: '', stderr: 'not found' }
        }
        return { code: 0, stdout: 'Python 3.12.0', stderr: '' }
      }

      if (command === 'winget') {
        return { code: 0, stdout: 'installed', stderr: '' }
      }

      if (args.includes('-m') && args.includes('venv')) {
        existing.add(path.normalize(venvPython))
        return { code: 0, stdout: 'venv ready', stderr: '' }
      }

      if (args.includes('pip') && args.includes('install')) {
        return { code: 0, stdout: 'pip ok', stderr: '' }
      }

      if (command === venvPython) {
        return { code: 0, stdout: 'analysis ok', stderr: '' }
      }

      return { code: 0, stdout: '', stderr: '' }
    },
  })

  const result = await runPythonAnalysisProgram(
    'fc3d',
    {
      apiBaseUrl: 'https://api.example.com',
      token: 'token-123',
      periods: '188',
      repoRoot,
      pythonEnvDir: envDir,
    },
    deps,
  )

  assert.equal(result.exitCode, 0)
  assert.ok(calls.some((entry) => entry.command === 'winget'))
  assert.ok(calls.some((entry) => entry.args.includes('venv')))
  assert.ok(calls.some((entry) => entry.command === venvPython && entry.args.includes('--periods')))
  const scriptRun = calls.find((entry) => entry.command === venvPython && entry.args.includes('--periods'))
  assert.ok(scriptRun)
  assert.equal(scriptRun.args[0], path.join(repoRoot, 'examples', 'python', 'fc3d_markov', 'main.py'))
  assert.ok(scriptRun.args.includes('--api-base-url'))
  assert.ok(scriptRun.args.includes('https://api.example.com'))
  assert.ok(scriptRun.args.includes('--token'))
  assert.ok(scriptRun.args.includes('token-123'))
  assert.ok(scriptRun.args.includes('188'))
})

test('runPythonAnalysisProgram reuses an existing virtual environment without reinstalling it', async () => {
  const { getRequirementsStampPath, getVenvPythonPath, runPythonAnalysisProgram } = await import(
    pythonRuntimeModuleUrl
  )

  const envDir = path.join(repoRoot, '.tmp-tests', 'python-env-reuse')
  const venvPython = getVenvPythonPath(envDir, process.platform)
  const stampPath = getRequirementsStampPath(envDir)
  const calls = []

  const deps = createDeps({
    platform: process.platform,
    existingPaths: [repoRoot, envDir, venvPython, stampPath],
    onRun: async ({ command, args }) => {
      calls.push({ command, args })
      if ((command === 'python3' || command === 'python' || command === 'py') && args.at(-1) === '--version') {
        return { code: 0, stdout: 'Python 3.11.9', stderr: '' }
      }
      if (command === venvPython) {
        return { code: 0, stdout: 'analysis ok', stderr: '' }
      }
      return { code: 0, stdout: '', stderr: '' }
    },
  })

  const result = await runPythonAnalysisProgram(
    'ssq',
    {
      apiBaseUrl: 'https://www.neuxsbot.com',
      token: '',
      periods: '120',
      repoRoot,
      pythonEnvDir: envDir,
    },
    deps,
  )

  assert.equal(result.exitCode, 0)
  assert.ok(calls.some((entry) => entry.command === venvPython))
  assert.ok(calls.every((entry) => !entry.args.includes('venv')))
  assert.ok(calls.every((entry) => !(entry.args.includes('pip') && entry.args.includes('install'))))
})
