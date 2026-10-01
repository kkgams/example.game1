#!/usr/bin/env python3
"""Record actual pinned-shell game build inputs/tools/outputs; no linking claims."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def collect(root):
    odin_version, zig_version = command('odin', 'version'), command('zig', 'version')
    if 'dev-2026-05' not in odin_version or zig_version != '0.16.0':
        raise ValueError('build tools differ from the reviewed locked environment')
    odin_root = Path(command('odin', 'root'))
    files = ['flake.lock', 'game/Makefile', 'game/env.c', 'game/env.o',
             'game/room.glsl', 'game/room.glsl.odin', 'game/station.rspk',
             'game/sokol/c/sokol_gfx.c', 'game/sokol/c/sokol_gfx.h']
    files += [p.relative_to(root).as_posix() for p in (root / 'game').rglob('*.odin')
              if 'build.nosync' not in p.parts]
    files += [p.relative_to(root).as_posix() for p in (root / 'game/web/wasm-include').rglob('*.h')]
    inputs = {p: digest(root / p) for p in sorted(set(files))}
    outputs = {name: digest(root / 'game/build.nosync/web' / name)
               for name in ('index.html', 'gl-bridge.js', 'station-demo.wasm', 'station.rspk')}
    core = {p: digest(odin_root / p) for p in
            ('base/runtime/wasm_allocator.odin', 'core/unicode/generated.odin',
             'core/math/math_erf.odin', 'core/math/math_log1p.odin', 'core/math/math_sincos.odin')}
    tools = {}
    for tool in ('odin', 'zig'):
        path = Path(shutil.which(tool))
        tools[tool] = {'path': str(path), 'sha256': digest(path)}
    return {'schema': 1, 'odin_version': odin_version, 'zig_version': zig_version,
            'flake_lock_sha256': digest(root / 'flake.lock'), 'tools': tools,
            'odin_root': str(odin_root), 'odin_source_sha256': core,
            'build_inputs_sha256': inputs, 'outputs_sha256': outputs,
            'bounds': 'Actual source/tool/output receipt; not an exact retained-symbol attribution or legal certification.'}


if __name__ == '__main__':
    output = Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(collect(ROOT), indent=2, sort_keys=True) + '\n')
