import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'

export type PythonProgram = {
  id: string
  label: string
  scriptRelativePath: string
  aliases: readonly string[]
}

export type RunCommandOptions = {
  cwd?: string
  env?: NodeJS.ProcessEnv
  inheritStdio?: boolean
}

export type RunCommandResult = {
  code: number
  stdout: string
  stderr: string
}

export type PythonRuntimeDeps = {
  platform: NodeJS.Platform
  env: NodeJS.ProcessEnv
  existsSync: (targetPath: string) => boolean
  mkdir: (targetPath: string, options?: { recursive?: boolean }) => Promise<void>
  readFile: (targetPath: string, encoding: BufferEncoding) => Promise<string>
  writeFile: (targetPath: string, content: string, encoding: BufferEncoding) => Promise<void>
  runCommand: (command: string, args: string[], options?: RunCommandOptions) => Promise<RunCommandResult>
}

export type PythonProgramRunOptions = {
  apiBaseUrl: string
  token?: string
  periods: string
  repoRoot: string
  pythonEnvDir?: string
  outputPath?: string
  onStatus?: (message: string) => void
}

export type PythonProgramRunResult = {
  exitCode: number
  pythonPath: string
  program: PythonProgram
}

type PythonCommand = {
  command: string
  argsPrefix: string[]
}

export const PYTHON_PROGRAMS: readonly PythonProgram[] = [
  {
    id: 'fc3d',
    label: '福彩3D 分析程序',
    scriptRelativePath: path.join('examples', 'python', 'fc3d_markov', 'main.py'),
    aliases: ['3d', 'fc3d_markov'],
  },
  {
    id: 'pl3',
    label: '排列3 分析程序',
    scriptRelativePath: path.join('examples', 'python', 'pl3_markov', 'main.py'),
    aliases: ['p3', 'pl3_markov'],
  },
  {
    id: 'ssq',
    label: '双色球 分析程序',
    scriptRelativePath: path.join('examples', 'python', 'ssq_quantum', 'main.py'),
    aliases: ['ssq_quantum'],
  },
  {
    id: 'dlt',
    label: '大乐透 分析程序',
    scriptRelativePath: path.join('examples', 'python', 'dlt_hybrid', 'main.py'),
    aliases: ['dlt_hybrid'],
  },
  {
    id: 'pl5',
    label: '排列5 分析程序',
    scriptRelativePath: path.join('examples', 'python', 'pailie5_positional', 'main.py'),
    aliases: ['p5', 'pailie5_positional'],
  },
  {
    id: 'qxc',
    label: '七星彩 分析程序',
    scriptRelativePath: path.join('examples', 'python', 'select7_positional', 'main.py'),
    aliases: ['select7', 'select7_positional'],
  },
  {
    id: 'kl8',
    label: '快乐8 分析程序',
    scriptRelativePath: path.join('examples', 'python', 'kl8_frequency', 'main.py'),
    aliases: ['k8', 'kl8_frequency'],
  },
] as const

export const getDefaultPythonRuntimeDeps = (): PythonRuntimeDeps => ({
  platform: process.platform,
  env: process.env,
  existsSync,
  mkdir: async (targetPath, options) => {
    await mkdir(targetPath, { recursive: options?.recursive })
  },
  readFile: async (targetPath, encoding) => readFile(targetPath, encoding),
  writeFile: async (targetPath, content, encoding) => {
    await writeFile(targetPath, content, encoding)
  },
  runCommand: (command, args, options = {}) =>
    new Promise((resolve) => {
      let child
      try {
        child = spawn(command, args, {
          cwd: options.cwd,
          env: {
            ...process.env,
            ...(options.env || {}),
          },
          stdio: options.inheritStdio ? 'inherit' : ['ignore', 'pipe', 'pipe'],
          shell: false,
          windowsHide: true,
        })
      } catch (error) {
        resolve({
          code: 1,
          stdout: '',
          stderr: `${command}: ${error instanceof Error ? error.message : String(error)}`,
        })
        return
      }

      let stdout = ''
      let stderr = ''

      if (!options.inheritStdio) {
        child.stdout?.setEncoding('utf8')
        child.stderr?.setEncoding('utf8')
        child.stdout?.on('data', (chunk) => {
          stdout += chunk
        })
        child.stderr?.on('data', (chunk) => {
          stderr += chunk
        })
      }

      child.on('error', (error) => {
        resolve({
          code: 1,
          stdout,
          stderr: error.message || stderr,
        })
      })

      child.on('close', (code) => {
        resolve({
          code: code ?? 1,
          stdout,
          stderr,
        })
      })
    }),
})

export const getPythonProgramById = (value: string) => {
  const normalized = String(value || '').trim().toLowerCase()
  return PYTHON_PROGRAMS.find(
    (program) => program.id === normalized || program.aliases.some((alias) => alias.toLowerCase() === normalized),
  )
}

export const getPythonEnvDir = () => process.env.NBCP_PYTHON_ENV_DIR || path.join(os.homedir(), '.neuxsbot', 'python-env')

export const getVenvPythonPath = (
  pythonEnvDir: string,
  platform: NodeJS.Platform = process.platform,
) => (platform === 'win32' ? path.join(pythonEnvDir, 'Scripts', 'python.exe') : path.join(pythonEnvDir, 'bin', 'python'))

export const getRequirementsStampPath = (pythonEnvDir: string) => path.join(pythonEnvDir, '.requirements.stamp')

const getRequirementsPath = (repoRoot: string) => path.join(repoRoot, 'examples', 'python', 'requirements.txt')

const getPythonCandidates = async (deps: PythonRuntimeDeps): Promise<PythonCommand[]> => {
  const { platform, env } = deps
  const customPython = env.NBCP_PYTHON_BIN?.trim()
  const candidates: PythonCommand[] = []

  if (customPython) {
    candidates.push({ command: customPython, argsPrefix: [] })
  }

  if (platform === 'win32') {
    const resolvedPythonPath = await resolveWindowsCommandPath('python', deps)
    if (resolvedPythonPath) {
      candidates.push({ command: resolvedPythonPath, argsPrefix: [] })
    }
  }

  if (platform === 'win32') {
    candidates.push(
      { command: 'py', argsPrefix: ['-3'] },
      { command: 'python', argsPrefix: [] },
      { command: 'python3', argsPrefix: [] },
    )
  } else {
    candidates.push(
      { command: 'python3', argsPrefix: [] },
      { command: 'python', argsPrefix: [] },
    )
  }

  const seen = new Set<string>()
  return candidates.filter((candidate) => {
    const key = `${candidate.command}::${candidate.argsPrefix.join(' ')}`
    if (seen.has(key)) {
      return false
    }
    seen.add(key)
    return true
  })
}

const resolveWindowsCommandPath = async (commandName: string, deps: PythonRuntimeDeps) => {
  if (deps.platform !== 'win32') {
    return null
  }

  const probeScript = [
    `$command = Get-Command ${commandName} -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source`,
    'if (-not $command) { exit 1 }',
    'Write-Output $command',
  ].join('; ')
  const result = await deps.runCommand('powershell.exe', ['-NoProfile', '-Command', probeScript])
  const resolvedPath = result.stdout.trim()
  return result.code === 0 && resolvedPath ? resolvedPath : null
}

const resolvePythonCommand = async (
  deps: PythonRuntimeDeps,
): Promise<PythonCommand | null> => {
  for (const candidate of await getPythonCandidates(deps)) {
    const result = await deps.runCommand(candidate.command, [...candidate.argsPrefix, '--version'])
    if (result.code === 0) {
      return candidate
    }
  }

  return null
}

const ensureSystemPython = async (
  deps: PythonRuntimeDeps,
  onStatus: (message: string) => void,
): Promise<PythonCommand> => {
  const resolved = await resolvePythonCommand(deps)
  if (resolved) {
    return resolved
  }

  if (deps.platform !== 'win32') {
    throw new Error('未检测到可用的 Python，请先安装 Python 3 后再运行本地分析程序。')
  }

  onStatus('未检测到 Python，正在尝试自动安装 Windows Python 环境...')
  const wingetCommand =
    deps.env.NBCP_WINGET_BIN?.trim() || (await resolveWindowsCommandPath('winget', deps)) || 'winget'
  const installResult = await deps.runCommand(
    wingetCommand,
    ['install', '-e', '--id', 'Python.Python.3.12', '--accept-package-agreements', '--accept-source-agreements'],
    { inheritStdio: true },
  )

  if (installResult.code !== 0) {
    throw new Error('自动安装 Python 失败，请确认系统已安装 winget，或手动安装 Python 3 后重试。')
  }

  const resolvedAfterInstall = await resolvePythonCommand(deps)
  if (!resolvedAfterInstall) {
    throw new Error('Python 已尝试自动安装，但当前仍未检测到可用解释器，请重新打开终端后重试。')
  }

  return resolvedAfterInstall
}

const ensurePythonPackages = async (
  venvPythonPath: string,
  repoRoot: string,
  pythonEnvDir: string,
  deps: PythonRuntimeDeps,
  onStatus: (message: string) => void,
) => {
  const requirementsPath = getRequirementsPath(repoRoot)
  const requirementsText = await deps.readFile(requirementsPath, 'utf8')
  const stampPath = getRequirementsStampPath(pythonEnvDir)
  let installedStamp = ''

  if (deps.existsSync(stampPath)) {
    installedStamp = await deps.readFile(stampPath, 'utf8')
  }

  if (installedStamp === requirementsText) {
    return
  }

  onStatus('正在安装 Python 依赖，请稍候...')
  const upgradePipResult = await deps.runCommand(venvPythonPath, ['-m', 'pip', 'install', '--upgrade', 'pip'], {
    cwd: repoRoot,
    inheritStdio: true,
  })
  if (upgradePipResult.code !== 0) {
    throw new Error('升级 pip 失败，无法继续初始化本地分析环境。')
  }

  const installRequirementsResult = await deps.runCommand(
    venvPythonPath,
    ['-m', 'pip', 'install', '-r', requirementsPath],
    {
      cwd: repoRoot,
      inheritStdio: true,
    },
  )
  if (installRequirementsResult.code !== 0) {
    throw new Error('安装 Python 依赖失败，请检查网络或 pip 源后重试。')
  }

  await deps.writeFile(stampPath, requirementsText, 'utf8')
}

export const ensurePythonRuntime = async (
  repoRoot: string,
  pythonEnvDir: string,
  deps: PythonRuntimeDeps = getDefaultPythonRuntimeDeps(),
  onStatus: (message: string) => void = () => {},
) => {
  const systemPython = await ensureSystemPython(deps, onStatus)
  const venvPythonPath = getVenvPythonPath(pythonEnvDir, deps.platform)

  if (!deps.existsSync(venvPythonPath)) {
    onStatus('正在初始化 Python 虚拟环境...')
    await deps.mkdir(path.dirname(pythonEnvDir), { recursive: true })
    const createVenvResult = await deps.runCommand(
      systemPython.command,
      [...systemPython.argsPrefix, '-m', 'venv', pythonEnvDir],
      {
        cwd: repoRoot,
        inheritStdio: true,
      },
    )

    if (createVenvResult.code !== 0) {
      throw new Error('创建 Python 虚拟环境失败，请检查 Python 安装是否完整。')
    }
  }

  await ensurePythonPackages(venvPythonPath, repoRoot, pythonEnvDir, deps, onStatus)
  return venvPythonPath
}

export const runPythonAnalysisProgram = async (
  programId: string,
  options: PythonProgramRunOptions,
  deps: PythonRuntimeDeps = getDefaultPythonRuntimeDeps(),
): Promise<PythonProgramRunResult> => {
  const program = getPythonProgramById(programId)
  if (!program) {
    throw new Error(`未识别的分析程序: ${programId}`)
  }

  const onStatus = options.onStatus || (() => {})
  const pythonEnvDir = options.pythonEnvDir || getPythonEnvDir()
  const venvPythonPath = await ensurePythonRuntime(options.repoRoot, pythonEnvDir, deps, onStatus)
  const scriptPath = path.join(options.repoRoot, program.scriptRelativePath)
  const periods = String(options.periods || '').trim()
  const args = [scriptPath, '--api-base-url', options.apiBaseUrl, '--periods', periods]

  if (options.token?.trim()) {
    args.push('--token', options.token.trim())
  }

  if (options.outputPath?.trim()) {
    args.push('--output', options.outputPath.trim())
  }

  onStatus(`正在运行 ${program.label}...`)
  const runResult = await deps.runCommand(venvPythonPath, args, {
    cwd: options.repoRoot,
    env: {
      ...deps.env,
      NEUXSBOT_API_BASE_URL: options.apiBaseUrl,
      NEUXSBOT_TOKEN: options.token || '',
      NEUXSBOT_PERIODS: periods,
    },
    inheritStdio: true,
  })

  if (runResult.code !== 0) {
    throw new Error(`${program.label} 运行失败，请检查上面的输出信息。`)
  }

  return {
    exitCode: runResult.code,
    pythonPath: venvPythonPath,
    program,
  }
}
