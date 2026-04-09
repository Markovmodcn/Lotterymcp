#!/usr/bin/env node

import path from 'node:path'
import { readFileSync } from 'node:fs'
import { createInterface } from 'node:readline/promises'
import { fileURLToPath } from 'node:url'
import { McpApiError, createLotteryMcpClient, formatMcpApiError } from 'lotterymcp-core'
import { MCP_SERVER_TOOLS, MCP_SERVER_TRANSPORT, startNbcpStdioServer } from 'lotterymcp-server'
import {
  DEFAULT_API_BASE_URL,
  DEFAULT_PERIODS,
  maskToken,
  renderMcpConfigSnippet,
  resolveConfig,
  saveLocalConfig,
  validateConfig,
  type NbcpConfig,
} from './config.js'
import { renderNbcpBanner, shouldShowBanner } from './banner.js'
import { PYTHON_PROGRAMS, getPythonProgramById, runPythonAnalysisProgram } from './python-runtime.js'

const WEBSITE_URL = 'https://www.neuxsbot.com'
const MEMBER_CENTER_URL = 'https://www.neuxsbot.com/member'
const TOKEN_PAGE_URL = 'https://www.neuxsbot.com/member/api-keys'
const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..')

const MENU_TEXT = `请选择操作：
  1. 注册/登录并获取 Token
  2. 配置接口地址、Token、默认期数
  3. 生成 MCP 配置片段
  4. 检查当前配置和网站连通性
  5. 启动 MCP 服务
  6. 直接运行本地分析程序
  0. 退出`

const HELP_TEXT = `临时打开菜单:
  npx --yes lotterymcp@latest

全局安装:
  npm i -g lotterymcp

使用方法:
  1. 先注册/登录官网并获取 Token
  2. 再配置 API_BASE_URL / TOKEN / DEFAULT_PERIODS
  3. 复制 MCP 配置片段到支持 MCP 的 AI 工具
  4. 在 AI 对话里动态选择彩种和期数
  5. 如需本地直接分析，可运行 Python 分析程序

可用命令:
  serve            启动 MCP stdio 服务
  init             生成本地配置文件
  doctor           检查当前配置和网站连通性
  login            打开官网账号页并获取 Token
  analyze          直接运行 Python 分析程序

说明:
  analyze 命令会自动准备本地 Python 运行环境。
  如果当前系统没有 Python，Windows 下会尝试自动安装并初始化依赖。

当前版本:
  官网: www.neuxsbot.com
  传输方式: ${MCP_SERVER_TRANSPORT}
  彩种: 由 AI 对话动态传入，不写死在本地配置
  工具列表: ${MCP_SERVER_TOOLS.join(', ')}
`

const TOKEN_TEXT = `注册/登录并获取 Token:
  官网首页: ${WEBSITE_URL}
  官网账号页: ${MEMBER_CENTER_URL}
  密钥页: ${TOKEN_PAGE_URL}

说明:
  1. 登录后进入官网账号页，直接复制 MCP Token。
  2. Token 用于识别会员权限、调用次数、升级状态。
  3. 彩种不在本地写死，由 AI 对话触发工具时动态传入。
`

const renderConfigSummary = (config: Partial<NbcpConfig>) => `当前配置:
  API_BASE_URL: ${config.apiBaseUrl || '(未设置)'}
  TOKEN: ${maskToken(config.token || '')}
  DEFAULT_PERIODS: ${config.defaultPeriods || '(未设置)'}
`

const renderPythonProgramMenu = () => {
  const rows = PYTHON_PROGRAMS.map((program, index) => `  ${index + 1}. ${program.label} (${program.id})`)
  return `请选择本地分析程序：
${rows.join('\n')}
  0. 返回上级`
}

const renderAnalyzeUsage = () => {
  const rows = PYTHON_PROGRAMS.map((program) => `  ${program.id.padEnd(4, ' ')} ${program.label}`)
  return `可用分析程序:
${rows.join('\n')}

示例:
  npx --yes lotterymcp@latest analyze fc3d --periods 120
  npx --yes lotterymcp@latest analyze ssq --periods 150
`
}

const isPositiveInteger = (value: string) => /^\d+$/.test(value.trim())

const buildNextConfig = (
  currentConfig: Partial<NbcpConfig>,
  input: {
    apiBaseUrl?: string
    token?: string
    defaultPeriods?: string
  },
): NbcpConfig => ({
  apiBaseUrl: input.apiBaseUrl?.trim() || currentConfig.apiBaseUrl || DEFAULT_API_BASE_URL,
  token: input.token?.trim() || currentConfig.token || '',
  defaultPeriods: input.defaultPeriods?.trim() || currentConfig.defaultPeriods || DEFAULT_PERIODS,
})

const toResolvedConfig = (config: Partial<NbcpConfig>): NbcpConfig => ({
  apiBaseUrl: String(config.apiBaseUrl || '').trim(),
  token: String(config.token || '').trim(),
  defaultPeriods: String(config.defaultPeriods || '').trim(),
})

const persistConfig = async (nextConfig: NbcpConfig) => {
  if (!nextConfig.token.trim()) {
    console.error('Token 不能为空。')
    return 1
  }

  if (!isPositiveInteger(nextConfig.defaultPeriods)) {
    console.error('默认期数必须是正整数。')
    return 1
  }

  await saveLocalConfig(nextConfig)
  console.log('\n配置已保存。')
  console.log(renderConfigSummary(nextConfig))
  return 0
}

const promptForConfig = async () => {
  const currentConfig = await resolveConfig()

  if (!process.stdin.isTTY) {
    const pipedInput = readFileSync(0, 'utf8').split(/\r?\n/)
    const nextConfig = buildNextConfig(currentConfig, {
      apiBaseUrl: pipedInput[0],
      token: pipedInput[1],
      defaultPeriods: pipedInput[2],
    })
    return persistConfig(nextConfig)
  }

  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
  })

  try {
    const apiBaseUrlInput = (
      await rl.question(`接口地址 [${currentConfig.apiBaseUrl || DEFAULT_API_BASE_URL}]: `)
    ).trim()
    const tokenInput = (
      await rl.question(`Token [${currentConfig.token ? maskToken(currentConfig.token) : '必填'}]: `)
    ).trim()
    const defaultPeriodsInput = (
      await rl.question(`默认期数 [${currentConfig.defaultPeriods || DEFAULT_PERIODS}]: `)
    ).trim()

    const nextConfig = buildNextConfig(currentConfig, {
      apiBaseUrl: apiBaseUrlInput,
      token: tokenInput,
      defaultPeriods: defaultPeriodsInput,
    })

    return persistConfig(nextConfig)
  } finally {
    rl.close()
  }
}

const canShowInteractiveMenu = (
  stdin: Pick<NodeJS.ReadStream, 'isTTY'> = process.stdin,
  stdout: Pick<NodeJS.WriteStream, 'isTTY'> = process.stdout,
) => process.env.NBCP_FORCE_MENU === '1' || (Boolean(stdin.isTTY) && Boolean(stdout.isTTY))

const printConfigSnippet = async () => {
  const config = await resolveConfig()
  const missing = validateConfig(config)

  if (missing.length > 0) {
    console.error(`未检测到完整配置，请先完成接入向导。缺少: ${missing.join(', ')}`)
    return 1
  }

  console.log('将下面这段 MCP 配置粘贴到支持 MCP 的 AI 工具中:\n')
  console.log(renderMcpConfigSnippet(config as NbcpConfig))
  return 0
}

const renderDoctorSummary = (health: any) => {
  const tools = Array.isArray(health?.tools) ? health.tools.join(', ') : '未返回'
  const authHeader = health?.auth?.header ? String(health.auth.header) : '未返回'

  return [
    '网站接口正常。',
    `  服务名称: ${health?.service || '未知'}`,
    `  传输方式: ${health?.transport || '未知'}`,
    `  鉴权头: ${authHeader}`,
    `  工具列表: ${tools}`,
  ].join('\n')
}

const runDoctor = async () => {
  const config = await resolveConfig()
  const missing = validateConfig(config)
  console.log(renderConfigSummary(config))

  if (missing.length > 0) {
    console.log(`缺少: ${missing.join(', ')}`)
    return 1
  }

  try {
    const client = createLotteryMcpClient(toResolvedConfig(config))
    const health = await client.getHealth()
    console.log(renderDoctorSummary(health))
    return 0
  } catch (error) {
    const message =
      error instanceof McpApiError
        ? formatMcpApiError(error)
        : error instanceof Error
          ? error.message
          : String(error)
    console.error(`网站接口异常: ${message}`)
    return 1
  }
}

const runServe = async () => {
  const config = await resolveConfig()
  const missing = validateConfig(config)

  if (missing.length > 0) {
    console.error(`未检测到完整配置，请先运行 init 或默认菜单完成接入。缺少: ${missing.join(', ')}`)
    return 1
  }

  try {
    await startNbcpStdioServer(toResolvedConfig(config))
    await new Promise(() => undefined)
    return 0
  } catch (error) {
    const message =
      error instanceof McpApiError
        ? formatMcpApiError(error)
        : error instanceof Error
          ? error.message
          : String(error)
    console.error(`MCP 服务启动失败: ${message}`)
    return 1
  }
}

const runSelectedPythonProgram = async (
  programId: string,
  overrides: {
    periods?: string
    outputPath?: string
  } = {},
) => {
  const config = await resolveConfig()
  const resolvedConfig = buildNextConfig(config, {})
  const program = getPythonProgramById(programId)
  const periods = String(overrides.periods || resolvedConfig.defaultPeriods || DEFAULT_PERIODS).trim()

  if (!program) {
    console.error(`未识别的分析程序: ${programId}`)
    console.log(renderAnalyzeUsage())
    return 1
  }

  if (!isPositiveInteger(periods)) {
    console.error('分析期数必须是正整数。')
    return 1
  }

  console.log(`准备运行: ${program.label}`)
  console.log(`接口地址: ${resolvedConfig.apiBaseUrl}`)
  console.log(`分析期数: ${periods}`)
  if (!resolvedConfig.token.trim()) {
    console.log('当前未配置 Token，将按当前网站公开能力尝试访问数据。')
  }
  console.log('')

  try {
    await runPythonAnalysisProgram(program.id, {
      apiBaseUrl: resolvedConfig.apiBaseUrl,
      token: resolvedConfig.token,
      periods,
      outputPath: overrides.outputPath,
      repoRoot: REPO_ROOT,
      onStatus: (message) => console.log(message),
    })
    console.log(`\n${program.label} 运行完成。`)
    return 0
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    return 1
  }
}

const runPythonProgramMenu = async () => {
  console.log('本地分析程序会自动准备 Python 运行环境。')
  console.log('如果当前系统没有 Python，Windows 下会尝试自动安装并初始化依赖。\n')
  console.log(renderPythonProgramMenu())

  if (!canShowInteractiveMenu()) {
    console.log('\n当前为非交互环境，请使用 `lotterymcp analyze <programId> --periods 120`。')
    console.log(renderAnalyzeUsage())
    return 0
  }

  const currentConfig = await resolveConfig()
  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
  })

  try {
    const selection = (await rl.question('\n请输入数字：')).trim()
    console.log('')

    if (selection === '0') {
      console.log('已返回。')
      return 0
    }

    const program = /^\d+$/.test(selection) ? PYTHON_PROGRAMS[Number(selection) - 1] : undefined
    if (!program) {
      console.error(`无效选择: ${selection || '(空)'}`)
      return 1
    }

    const periodsInput = (
      await rl.question(`分析期数 [${currentConfig.defaultPeriods || DEFAULT_PERIODS}]: `)
    ).trim()

    return runSelectedPythonProgram(program.id, {
      periods: periodsInput || currentConfig.defaultPeriods || DEFAULT_PERIODS,
    })
  } finally {
    rl.close()
  }
}

const parseAnalyzeArgs = (argv: string[]) => {
  const parsed: {
    programId?: string
    periods?: string
    outputPath?: string
  } = {}

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]
    if (!arg) {
      continue
    }

    if (!arg.startsWith('--') && !parsed.programId) {
      parsed.programId = arg
      continue
    }

    if (arg === '--periods' || arg === '-p') {
      parsed.periods = argv[index + 1]
      index += 1
      continue
    }

    if (arg === '--output' || arg === '-o') {
      parsed.outputPath = argv[index + 1]
      index += 1
      continue
    }

    throw new Error(`未知参数: ${arg}`)
  }

  return parsed
}

const runAnalyzeCommand = async (argv: string[]) => {
  let parsed: ReturnType<typeof parseAnalyzeArgs>

  try {
    parsed = parseAnalyzeArgs(argv)
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    console.log(renderAnalyzeUsage())
    return 1
  }

  if (!parsed.programId) {
    if (canShowInteractiveMenu()) {
      return runPythonProgramMenu()
    }

    console.log(renderAnalyzeUsage())
    return 0
  }

  return runSelectedPythonProgram(parsed.programId, {
    periods: parsed.periods,
    outputPath: parsed.outputPath,
  })
}

const runStartupMenu = async () => {
  console.log(MENU_TEXT)

  if (!canShowInteractiveMenu()) {
    console.log('\n当前为非交互环境，请追加 --help 查看完整帮助。')
    return 0
  }

  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
  })

  try {
    const selection = (await rl.question('\n请输入数字：')).trim()
    console.log('')

    switch (selection) {
      case '1':
        console.log(TOKEN_TEXT)
        return 0
      case '2':
        return promptForConfig()
      case '3':
        return printConfigSnippet()
      case '4':
        return runDoctor()
      case '5':
        return runServe()
      case '6':
        return runPythonProgramMenu()
      case '0':
        console.log('已退出。')
        return 0
      default:
        console.error(`无效选择: ${selection || '(空)'}`)
        return 1
    }
  } finally {
    rl.close()
  }
}

const args = process.argv.slice(2)
const command = args[0]

const main = async () => {
  if (shouldShowBanner(command)) {
    process.stdout.write(renderNbcpBanner())
  }

  if (!command) {
    return runStartupMenu()
  }

  if (command === '--help' || command === '-h') {
    console.log(HELP_TEXT)
    return 0
  }

  if (command === 'serve') {
    return runServe()
  }

  if (command === 'init') {
    return promptForConfig()
  }

  if (command === 'doctor') {
    return runDoctor()
  }

  if (command === 'login') {
    console.log(TOKEN_TEXT)
    return 0
  }

  if (command === 'analyze') {
    return runAnalyzeCommand(args.slice(1))
  }

  console.error(`未知命令: ${command}`)
  console.log(HELP_TEXT)
  return 1
}

try {
  const exitCode = await main()
  process.exitCode = exitCode
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error))
  process.exitCode = 1
}

