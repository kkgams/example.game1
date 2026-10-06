import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { localPluginPaths } from '../scripts/local-plugin-paths.mjs'

const root = resolve(import.meta.dirname, '..')
const config = JSON.parse(await readFile(resolve(root, 'gams.json'), 'utf8'))

test('CLI integration maps configured public sources to separately installed local plugins', () => {
  assert.deepEqual(localPluginPaths(root, config), ['fs', 'layout', 'lua', 'director-compiler', 'respack']
    .map(name => resolve(root, `plugins/${name}.comp.wasm`)))
})

test('CLI integration refuses unreviewed remote sources instead of resolving URLs as local paths', () => {
  assert.throws(() => localPluginPaths(root, { plugins: ['https://example.com/custom.wasm'] }), /not in release-lock.json/)
  assert.deepEqual(localPluginPaths(root, { plugins: ['plugins/custom.wasm'] }), [
    resolve(root, 'plugins/fs.comp.wasm'), resolve(root, 'plugins/custom.wasm'),
  ])
})
