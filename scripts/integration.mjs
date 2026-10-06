#!/usr/bin/env node
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { existsSync, readFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { localPluginPaths } from './local-plugin-paths.mjs'

const stationRoot = resolve(import.meta.dirname, '..')
const hostRoot = resolve(process.env.GAMS_HOST_ROOT ?? join(stationRoot, '../gams'))
const configPath = join(stationRoot, 'gams.json')
const config = JSON.parse(readFileSync(configPath, 'utf8'))

assert.ok(Array.isArray(config.plugins), 'gams.json plugins must be an array')
assert.ok(config.plugins.length > 0, 'gams.json must register at least one plugin')

const bridgePluginPaths = localPluginPaths(stationRoot, config)
for (const pluginPath of bridgePluginPaths) {
  assert.ok(existsSync(pluginPath), `missing CLI plugin: ${pluginPath}; run make setup-releases or make setup-local first`)
}
const pluginArgs = bridgePluginPaths.flatMap((path) => ['--plug', path])

const hostBin = process.env.GAMS_HOST_BIN
assert.ok(hostBin && existsSync(hostBin), 'GAMS_HOST_BIN must point at a built external Host binary')
const baseEnv = {
  ...process.env,
  GAMS_APP_CWD: stationRoot,
  GAMS_WASMTIME_CACHE_DIR: join(stationRoot, 'build.nosync/wasmtime-cache-integration'),
}
if (process.env.HOST_CC !== undefined) baseEnv.CC = process.env.HOST_CC
if (process.env.HOST_CXX !== undefined) baseEnv.CXX = process.env.HOST_CXX

function invoke(target, args) {
  const result = spawnSync(hostBin, [
    'run', ...pluginArgs,
    target, JSON.stringify(args),
  ], {
    cwd: hostRoot,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
    env: baseEnv,
  })

  assert.equal(
    result.status,
    0,
    `${target} failed\nconfigured plugins: ${bridgePluginPaths.join(', ')}\n${result.stderr}\n${result.stdout}`,
  )
  return JSON.parse(result.stdout)
}

const layoutRequest = {
  w: 1280,
  h: 720,
  config: {
    'max-areas': 16,
    'max-handles': 15,
    'min-panel-size': 120,
    'handle-half-size': 6,
  },
  'root-content-id': '46',
}
const layout = invoke('layout/layout::init-screen', [layoutRequest])
assert.equal(layout.err, undefined, 'layout init-screen returned an error result')
assert.equal(layout.ok.document['screen-w'], layoutRequest.w)
assert.equal(layout.ok.document['screen-h'], layoutRequest.h)
assert.equal(layout.ok.document.areas[0]['content-id'], layoutRequest['root-content-id'])

const luaRoundtrip = invoke('lua/lua::run', [`
function main()
  return json.encode({ answer = 42, ok = true, nullable = json.null })
end
`])
assert.equal(luaRoundtrip.err, undefined, `lua JSON roundtrip failed: ${luaRoundtrip.err}`)
assert.deepEqual(JSON.parse(luaRoundtrip.ok), { answer: 42, ok: true, nullable: null })

const luaFs = invoke('lua/lua::run', [`
function main()
  local text = fs.read_text('gams.json')
  local config = json.decode(text)
  return json.encode({ plugin_count = #config.plugins, has_ui = type(config.ui) == 'table' })
end
`])
assert.equal(luaFs.err, undefined, `lua fs bridge read failed: ${luaFs.err}`)
assert.deepEqual(JSON.parse(luaFs.ok), { plugin_count: config.plugins.length, has_ui: true })

const luaCaughtError = invoke('lua/lua::run', [`
function main()
  local ok, message = pcall(fs.read_text, 'missing.lua')
  return json.encode({ ok = ok, has_message = string.len(tostring(message)) > 0 })
end
`])
assert.equal(luaCaughtError.err, undefined, `lua pcall error handling failed: ${luaCaughtError.err}`)
assert.deepEqual(JSON.parse(luaCaughtError.ok), { ok: false, has_message: true })

const luaRuntimeError = invoke('lua/lua::run', [`
function main()
  local value = nil
  return value.missing
end
`])
assert.match(luaRuntimeError.err, /nil|attempt/i)

console.log('host integration smoke: configured station plugins -> layout init-screen ok')
console.log('host integration smoke: lua JSON, fs bridge, and error handling ok')
console.log('note: standalone Host integration does not run an independent Lua jco test; native component exception support is verified through the Host runtime path here.')
