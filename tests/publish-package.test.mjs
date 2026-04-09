import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

const readJson = (relativePath) =>
  JSON.parse(readFileSync(path.join(repoRoot, relativePath), 'utf8'))

test('cli package does not depend on unpublished local file dependencies', () => {
  const cliPackage = readJson(path.join('packages', 'cli', 'package.json'))
  const dependencyEntries = Object.entries(cliPackage.dependencies || {})

  assert.ok(dependencyEntries.length > 0)

  for (const [name, version] of dependencyEntries) {
    assert.doesNotMatch(
      String(version),
      /^file:/,
      `CLI package dependency ${name} must not use a local file reference in a publishable package`,
    )
  }
})

test('publishable packages expose registry metadata and cli package includes a README', () => {
  const corePackage = readJson(path.join('packages', 'core', 'package.json'))
  const serverPackage = readJson(path.join('packages', 'mcp-server', 'package.json'))
  const cliReadmePath = path.join(repoRoot, 'packages', 'cli', 'README.md')

  assert.equal(corePackage.private, false)
  assert.equal(serverPackage.private, false)
  assert.equal(corePackage.publishConfig?.access, 'public')
  assert.equal(serverPackage.publishConfig?.access, 'public')
  assert.equal(existsSync(cliReadmePath), true)
})
