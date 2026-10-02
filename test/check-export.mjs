#!/usr/bin/env node
// Development/native smoke against an explicitly selected external Host binary.
import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { existsSync, readFileSync, rmSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { join, resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const binary = process.env.GAMS_HOST_BIN
const hostRoot = process.env.GAMS_HOST_ROOT
assert.ok(binary && hostRoot && existsSync(binary), 'select the external released Host via GAMS_HOST_BIN/GAMS_HOST_ROOT')
const config = JSON.parse(readFileSync(join(root, 'gams.json'), 'utf8'))
const plugins = [join(root, 'plugins/fs.comp.wasm'), ...config.plugins.map(p => resolve(root, p))]
const source = readFileSync(join(root, 'ng/presets/export-station-web.lua'), 'utf8')
const sha = data => createHash('sha256').update(data).digest('hex')
const documents = ['LICENSE', 'NOTICE', 'THIRD-PARTY-NOTICES.txt']

function invoke(variant, output, body = source) {
  const pack = `content/generated/${variant}.rspk`
  const inputs = `{${readFileSync(join(root, pack)).length}, ${JSON.stringify(output)}, "game/build.nosync/web/index.html", "game/build.nosync/web/gl-bridge.js", "game/build.nosync/web/station-demo.wasm", ${JSON.stringify(pack)}}`
  const code = `function main()\nlocal inputs = ${inputs}\nlocal outputs = {}\n${body}\nreturn json.encode(outputs[1])\nend`
  const result = spawnSync(binary, ['run', ...plugins.flatMap(p => ['--plug', p]), 'lua/lua::run', JSON.stringify([code])], {
    cwd: hostRoot, encoding: 'utf8', env: {...process.env, GAMS_APP_CWD: root, GAMS_WASMTIME_CACHE_DIR: join(root, 'build.nosync/wasmtime-cache-integration')},
  })
  assert.equal(result.status, 0, `${result.stderr}\n${result.stdout}`)
  return JSON.parse(result.stdout)
}

const hashes = {}
for (const variant of ['power', 'key']) {
  const output = `build.nosync/export-proof/${variant}`
  const response = invoke(variant, output)
  assert.equal(response.err, undefined, response.err)
  const metadata = JSON.parse(response.ok)
  assert.equal(metadata.files.length, 8)
  const folder = join(root, output)
  for (const name of documents) assert.deepEqual(readFileSync(join(folder, name)), readFileSync(join(root, name)))
  assert.deepEqual(readFileSync(join(folder, 'README.md')), readFileSync(join(root, 'BROWSER-README.md')))
  assert.deepEqual(readFileSync(join(folder, 'station-demo.wasm')), readFileSync(join(root, 'game/build.nosync/web/station-demo.wasm')))
  assert.deepEqual(readFileSync(join(folder, 'station.rspk')), readFileSync(join(root, `content/generated/${variant}.rspk`)))
  hashes[variant] = {wasm: sha(readFileSync(join(folder, 'station-demo.wasm'))), pack: sha(readFileSync(join(folder, 'station.rspk')))}
}
assert.equal(hashes.power.wasm, hashes.key.wasm)
assert.notEqual(hashes.power.pack, hashes.key.pack)
const missing = 'build.nosync/export-proof/missing-notice'
rmSync(join(root, missing), {recursive: true, force: true})
const altered = source.replace('{"NOTICE", "NOTICE"}', '{"NOTICE", "missing-notice-for-test.txt"}')
assert.notEqual(altered, source)
const failed = invoke('power', missing, altered)
assert.ok(typeof failed.err === 'string' && failed.err.length > 0)
assert.equal(existsSync(join(root, missing)), false, 'missing required legal input must fail before output mutation')
console.log(JSON.stringify({status: 'passed', export_files: 8, hashes, missing_notice_failed_before_mutation: true}, null, 2))
