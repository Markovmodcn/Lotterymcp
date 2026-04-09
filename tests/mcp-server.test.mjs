import assert from 'node:assert/strict'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath, pathToFileURL } from 'node:url'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const serverEntryUrl = pathToFileURL(path.join(repoRoot, 'packages', 'mcp-server', 'dist', 'index.js')).href

test('mcp server exposes the four lottery tools through the public tool catalog', async () => {
  const { createLotteryToolCatalog } = await import(serverEntryUrl)

  const catalog = createLotteryToolCatalog({
    getLatest: async () => ({ data: null, meta: { plan: 'member', apiKeyUsed: true, requestLimit: null, generatedAt: new Date().toISOString() } }),
    getHistory: async () => ({ data: [], meta: { plan: 'member', apiKeyUsed: true, requestLimit: 20, generatedAt: new Date().toISOString() } }),
    getPeriods: async () => ({ data: [], meta: { plan: 'member', apiKeyUsed: true, requestLimit: 20, generatedAt: new Date().toISOString() } }),
    getSummary: async () => ({ data: null, meta: { plan: 'member', apiKeyUsed: true, requestLimit: null, generatedAt: new Date().toISOString() } }),
  })

  assert.deepEqual(
    catalog.map((item) => item.name),
    ['lottery.latest', 'lottery.history', 'lottery.periods', 'lottery.summary'],
  )
})

test('latest tool delegates to the client and returns text content', async () => {
  const { createLotteryToolCatalog } = await import(serverEntryUrl)
  const calls = []
  const catalog = createLotteryToolCatalog({
    getLatest: async (input) => {
      calls.push(input)
      return {
        data: {
          lotteryType: 'fc3d',
          period: '2026048',
          numbers: '1 2 3',
          drawDate: '2026-04-08',
        },
        meta: {
          plan: 'member',
          apiKeyUsed: true,
          requestLimit: null,
          generatedAt: '2026-04-08T00:00:00.000Z',
        },
      }
    },
    getHistory: async () => ({ data: [], meta: { plan: 'member', apiKeyUsed: true, requestLimit: 20, generatedAt: new Date().toISOString() } }),
    getPeriods: async () => ({ data: [], meta: { plan: 'member', apiKeyUsed: true, requestLimit: 20, generatedAt: new Date().toISOString() } }),
    getSummary: async () => ({ data: null, meta: { plan: 'member', apiKeyUsed: true, requestLimit: null, generatedAt: new Date().toISOString() } }),
  })

  const latestTool = catalog.find((item) => item.name === 'lottery.latest')
  const result = await latestTool.handler({ lotteryType: 'fc3d' })

  assert.deepEqual(calls, [{ lotteryType: 'fc3d' }])
  assert.equal(result.isError, false)
  assert.equal(result.content[0].type, 'text')
  assert.match(result.content[0].text, /fc3d/)
  assert.match(result.content[0].text, /2026048/)
})
