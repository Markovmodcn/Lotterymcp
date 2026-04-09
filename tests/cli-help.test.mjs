import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import { mkdtempSync, readFileSync } from 'node:fs'
import { createServer } from 'node:http'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const cliEntry = path.join(repoRoot, 'packages', 'cli', 'dist', 'index.js')

const startJsonServer = async (handler) => {
  const server = createServer(handler)
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve))
  const address = server.address()
  const origin = `http://127.0.0.1:${address.port}`

  return {
    origin,
    close: async () => {
      await new Promise((resolve, reject) => server.close((error) => (error ? reject(error) : resolve())))
    },
  }
}

const runCli = (args, options = {}) =>
  new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [cliEntry, ...args], {
      cwd: repoRoot,
      env: {
        ...process.env,
        ...(options.env || {}),
      },
      stdio: ['pipe', 'pipe', 'pipe'],
    })

    let stdout = ''
    let stderr = ''

    child.stdout.setEncoding('utf8')
    child.stderr.setEncoding('utf8')
    child.stdout.on('data', (chunk) => {
      stdout += chunk
    })
    child.stderr.on('data', (chunk) => {
      stderr += chunk
    })
    child.on('error', reject)
    child.on('close', (code) => {
      resolve({
        status: code,
        stdout,
        stderr,
      })
    })

    if (options.input) {
      child.stdin.write(options.input)
    }
    child.stdin.end()
  })

test('cli --help exits successfully and shows readable Chinese help', () => {
  const result = spawnSync(process.execPath, [cliEntry, '--help'], {
    cwd: repoRoot,
    encoding: 'utf8',
  })

  assert.equal(result.status, 0)
  assert.match(result.stdout, /使用方法:/)
  assert.match(result.stdout, /启动 MCP stdio 服务/)
  assert.match(result.stdout, /先注册\/登录官网并获取 Token/)
  assert.match(result.stdout, /npx --yes neuxnbcp@latest/)
  assert.equal(result.stderr, '')
})

test('cli without args shows the startup menu in Chinese and can exit cleanly', () => {
  const result = spawnSync(process.execPath, [cliEntry], {
    cwd: repoRoot,
    encoding: 'utf8',
    input: '0\n',
    env: {
      ...process.env,
      NBCP_FORCE_BANNER: '1',
      NBCP_FORCE_MENU: '1',
    },
  })

  assert.equal(result.status, 0)
  assert.ok(result.stdout.includes('Lotterymcp'))
  assert.match(result.stdout, /请选择操作：/)
  assert.match(result.stdout, /1\.\s+注册\/登录并获取 Token/)
  assert.match(result.stdout, /2\.\s+配置接口地址、Token、默认期数/)
  assert.match(result.stdout, /3\.\s+生成 MCP 配置片段/)
  assert.match(result.stdout, /4\.\s+检查当前配置和网站连通性/)
  assert.match(result.stdout, /5\.\s+启动 MCP 服务/)
  assert.match(result.stdout, /0\.\s+退出/)
  assert.match(result.stdout, /请输入数字：/)
  assert.match(result.stdout, /已退出。/)
  assert.equal(result.stderr, '')
})

test('cli init saves API base URL, token, and default periods', () => {
  const tempDir = mkdtempSync(path.join(os.tmpdir(), 'nbcp-config-'))
  const configPath = path.join(tempDir, 'cp.config.json')
  const result = spawnSync(process.execPath, [cliEntry, 'init'], {
    cwd: repoRoot,
    encoding: 'utf8',
    input: 'https://api.example.com\nmy-token-123456\n188\n',
    env: {
      ...process.env,
      NBCP_CONFIG_PATH: configPath,
    },
  })

  assert.equal(result.status, 0)
  assert.match(result.stdout, /配置已保存。/)
  const savedConfig = JSON.parse(readFileSync(configPath, 'utf8'))
  assert.deepEqual(savedConfig, {
    apiBaseUrl: 'https://api.example.com',
    token: 'my-token-123456',
    defaultPeriods: '188',
  })
  assert.equal(result.stderr, '')
})

test('cli doctor performs a real health check and reports success in Chinese', async () => {
  const requests = []
  const server = await startJsonServer((req, res) => {
    requests.push({ url: req.url, headers: req.headers })
    res.writeHead(200, { 'content-type': 'application/json; charset=utf-8' })
    res.end(
      JSON.stringify({
        ok: true,
        service: 'nexusbot-lottery-api',
        transport: 'rest',
        auth: { header: 'x-api-key' },
        tools: ['lottery.latest', 'lottery.history', 'lottery.periods', 'lottery.summary'],
      }),
    )
  })

  try {
    const result = await runCli(['doctor'], {
      env: {
        NEUXSBOT_API_BASE_URL: server.origin,
        NEUXSBOT_TOKEN: 'doctor-token-001',
        NEUXSBOT_DEFAULT_PERIODS: '100',
      },
    })

    assert.equal(result.status, 0)
    assert.match(result.stdout, /当前配置:/)
    assert.match(result.stdout, /网站接口正常/)
    assert.match(result.stdout, /服务名称: nexusbot-lottery-api/)
    assert.doesNotMatch(result.stdout, /doctor-token-001/)
    assert.equal(requests[0]?.url, '/api/v1/mcp/health')
    assert.equal(requests[0]?.headers['x-api-key'], 'doctor-token-001')
    assert.equal(result.stderr, '')
  } finally {
    await server.close()
  }
})

test('cli doctor reports friendly guidance when the website rate limits requests', async () => {
  const server = await startJsonServer((_req, res) => {
    res.writeHead(429, {
      'content-type': 'application/json; charset=utf-8',
      'retry-after': '0',
    })
    res.end(
      JSON.stringify({
        statusCode: 429,
        code: 'MCP_RATE_LIMITED',
        message: '请求过于频繁，请稍后重试。',
      }),
    )
  })

  try {
    const result = await runCli(['doctor'], {
      env: {
        NEUXSBOT_API_BASE_URL: server.origin,
        NEUXSBOT_TOKEN: 'doctor-token-002',
        NEUXSBOT_DEFAULT_PERIODS: '100',
      },
    })

    assert.equal(result.status, 1)
    assert.match(result.stdout, /当前配置:/)
    assert.match(result.stderr, /请求过于频繁/)
    assert.match(result.stderr, /降低默认期数|调用频率/)
  } finally {
    await server.close()
  }
})

test('cli login points users to the account token page', () => {
  const result = spawnSync(process.execPath, [cliEntry, 'login'], {
    cwd: repoRoot,
    encoding: 'utf8',
  })

  assert.equal(result.status, 0)
  assert.match(result.stdout, /官网首页: https:\/\/www\.neuxsbot\.com/)
  assert.match(result.stdout, /官网账号页: https:\/\/www\.neuxsbot\.com\/member/)
  assert.equal(result.stderr, '')
})

test('cli serve stays silent on stdout when config is incomplete', () => {
  const result = spawnSync(process.execPath, [cliEntry, 'serve'], {
    cwd: repoRoot,
    encoding: 'utf8',
    env: {
      ...process.env,
      NBCP_FORCE_BANNER: '1',
      NEUXSBOT_API_BASE_URL: '',
      NEUXSBOT_TOKEN: '',
    },
  })

  assert.equal(result.status, 1)
  assert.equal(result.stdout, '')
  assert.match(result.stderr, /未检测到完整配置/)
})
