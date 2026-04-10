import assert from 'node:assert/strict'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath, pathToFileURL } from 'node:url'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const bannerModuleUrl = pathToFileURL(
  path.join(repoRoot, 'packages', 'cli', 'dist', 'banner.js'),
).href

test('banner uses the new block wordmark instead of the old ASCII letters', async () => {
  const { renderNbcpBanner } = await import(bannerModuleUrl)
  const output = renderNbcpBanner()

  assert.match(output, /█{2,}/)
  assert.match(output, /Lotterymcp 中文命令行入口/)
  assert.match(output, /www\.neuxsbot\.com/)
  assert.doesNotMatch(output, /NN   NN EEEEEEE/)
})
