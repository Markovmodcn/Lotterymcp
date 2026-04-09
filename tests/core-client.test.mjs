import assert from 'node:assert/strict'
import { createServer } from 'node:http'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath, pathToFileURL } from 'node:url'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const coreEntryUrl = pathToFileURL(path.join(repoRoot, 'packages', 'core', 'dist', 'index.js')).href

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

test('core client requests the health endpoint and sends x-api-key', async () => {
  const requests = []
  const server = await startJsonServer((req, res) => {
    requests.push({ url: req.url, headers: req.headers })
    res.writeHead(200, { 'content-type': 'application/json; charset=utf-8' })
    res.end(JSON.stringify({ ok: true, service: 'nexusbot-lottery-api' }))
  })

  try {
    const { createLotteryMcpClient } = await import(coreEntryUrl)
    const client = createLotteryMcpClient({
      apiBaseUrl: server.origin,
      token: 'test-token-001',
      defaultPeriods: '100',
    })

    const result = await client.getHealth()

    assert.equal(result.ok, true)
    assert.equal(requests[0]?.url, '/api/v1/mcp/health')
    assert.equal(requests[0]?.headers['x-api-key'], 'test-token-001')
  } finally {
    await server.close()
  }
})

test('core client normalizes structured API errors from the website', async () => {
  const server = await startJsonServer((_req, res) => {
    res.writeHead(403, { 'content-type': 'application/json; charset=utf-8' })
    res.end(
      JSON.stringify({
        statusCode: 403,
        code: 'MCP_MEMBERSHIP_EXPIRED',
        message: '会员已过期，请升级后继续使用。',
        upgradeUrl: '/member/group-upgrade',
        displayMode: 'dialog_button',
        action: {
          type: 'open_url',
          label: '升级',
          url: 'https://www.neuxsbot.com/member/',
        },
      }),
    )
  })

  try {
    const { McpApiError, createLotteryMcpClient } = await import(coreEntryUrl)
    const client = createLotteryMcpClient({
      apiBaseUrl: server.origin,
      token: 'expired-token-001',
      defaultPeriods: '100',
    })

    await assert.rejects(
      () => client.getSummary({ lotteryType: 'fc3d' }),
      (error) => {
        assert.ok(error instanceof McpApiError)
        assert.equal(error.statusCode, 403)
        assert.equal(error.code, 'MCP_MEMBERSHIP_EXPIRED')
        assert.equal(error.upgradeUrl, '/member/group-upgrade')
        assert.equal(error.displayMode, 'dialog_button')
        assert.equal(error.action?.url, 'https://www.neuxsbot.com/member/')
        return true
      },
    )
  } finally {
    await server.close()
  }
})

test('core client retries a 429 response and succeeds on the next attempt', async () => {
  const { createLotteryMcpClient } = await import(coreEntryUrl)
  let attempts = 0
  const client = createLotteryMcpClient({
    apiBaseUrl: 'https://www.neuxsbot.com',
    token: 'retry-token-001',
    defaultPeriods: '100',
    fetchImpl: async () => {
      attempts += 1
      if (attempts === 1) {
        return new Response(JSON.stringify({ message: '请求过于频繁，请稍后重试。' }), {
          status: 429,
          headers: {
            'content-type': 'application/json; charset=utf-8',
            'retry-after': '0',
          },
        })
      }

      return new Response(JSON.stringify({ ok: true, service: 'nexusbot-lottery-api' }), {
        status: 200,
        headers: {
          'content-type': 'application/json; charset=utf-8',
        },
      })
    },
  })

  const result = await client.getHealth()

  assert.equal(result.ok, true)
  assert.equal(attempts, 2)
})
