#!/usr/bin/env node
// Binary/ABI smoke only: no claim of WebGL rendering or interactive play.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const path = process.argv[2] ?? 'game/build.nosync/web/station-demo.wasm'
const module = new WebAssembly.Module(readFileSync(path))
const imports = WebAssembly.Module.imports(module)
const exports = WebAssembly.Module.exports(module)
for (const [name, kind] of [['memory', 'memory'], ['init', 'function'], ['frame', 'function'], ['event', 'function'], ['get_event_buffer', 'function'], ['status_bits', 'function']]) {
  assert.ok(exports.some(e => e.name === name && e.kind === kind), `missing browser ABI export: ${name}`)
}
assert.ok(imports.every(i => i.module === 'env' && i.kind === 'function'), 'unexpected runtime/server/Host import')
console.log(JSON.stringify({status: 'passed', imports, exports, bounds: 'Valid core WASM/browser ABI; WebGL gameplay remains a separate walkthrough.'}, null, 2))
