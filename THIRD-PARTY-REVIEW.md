# example.game1 redistribution review

## Decision and scope

**No identifiable permission blocker found in the reviewed game/source materials.**
The owner's standing Apache-2.0 grant and assertion of redistribution rights are
accepted for owner-controlled local code. Unknown earliest local authorship is
disclosed, not converted into a demand for another ownership approval. This is a
bounded source/build-path review, not perfect provenance certification, legal
advice, or an attestation that an existing binary came from these sources.

Only this `audit/` directory was written. No game rebuild, local-repository edit,
commit, tag, push or publication was performed. Host and sibling plugin/theme
release payloads are separate distributions, outside this review. `audit.json`
contains input SHA-256 inventories, upstream receipts and explicit proof bounds.

Reviewed inputs:

* `/Users/gook/Repos/kkgams-local/example.game1`, including the game sources,
  notices, dependency tree, root build scripts and flake pins;
* `examples/station-demo`, including generated Director/decoder/content data,
  game source and vendored Sokol source;
* `examples/demo/game`, earlier `plugins/game2` lineage and historical browser
  bridge snapshots;
* packaging template source/build pins, and the **actual standalone flake's**
  Odin/Zig environment. Root GAMS `flake.nix` does not itself list Odin or Zig,
  so it must not be substituted for the standalone environment.

## Build and linked-code map

| Material | Evidence and license | Distribution treatment |
| --- | --- | --- |
| Owner-controlled Project/game/content/build code | Standing Apache-2.0 instruction; local source and content inventory | Root `LICENSE` applies only to this code, not every dependency |
| Sokol Odin bindings | `sokol-odin` `9ea6ec125f002180d6cc6e7a009087ca0a019da4`, archive SHA-256 `0eebee1d50bb08f1bf44f5458d8c32d61e4c2069d73a2eddb9feeb7c04d185ba`; zlib/libpng, Andre Weissflog 2022 | Source dependency; imported gfx binding participates in game build |
| Embedded Sokol C gfx | Same verified archive, `sokol/c/sokol_gfx.c` includes `sokol_gfx.h`; `env.c` defines GLES3/implementation and includes that translation unit; header notice Andre Weissflog 2018 | Compiled into `env.o`, then referenced by Odin WASM foreign import; retain separate embedded header notice |
| Odin runtime/core | Actual `odin root` `/nix/store/708y97i6z1rq921qjrilyk6jjs9d3sy7-odin-dev-2026-05/share`; version `dev-2026-05`; upstream tag resolves to `ea5175d865c2034b033ebf5653d83638f10bba54`; **zlib**, not a presumed BSD standard-library license | Source-level runtime/core linkage is established by imports; compiler executable is a tool, not shipped game code |
| Odin emmalloc port | `base/runtime/wasm_allocator.odin`: explicitly modified port, Emscripten authors 2010–2014, full MIT notice | `host_wasm.odin` calls `runtime.default_wasm_allocator()`; actual identifiable external runtime, not merely speculative Emscripten tooling |
| Odin Unicode data | `core/strings` imports `core/unicode`; `generated.odin` full Unicode License V3 and Unicode, Inc. 1991–2026 notice | Retain for possible linked table/data use; exact retained table fragments are not attested |
| Odin math third-party portions | Imported `core:math`/fmt package contains Sun notice in `math_erf.odin`/`math_log1p.odin`, and Cephes/Moshier notice in `math_sincos.odin`; verbatim notices retained | Conservative package-level coverage. Station's direct math calls are `math.abs`, not evidence that erf/sincos survives linking; do not claim all package routines ship |
| Zig compiler runtime | Actual Zig `0.16.0`, Codeberg tag resolves to `44d9672fed001115e674fd5ddb32747ef43a7af4`; MIT; installed `compiler_rt` references LLVM ports and musl | **Conditional**, not confirmed linked here. Makefile uses `zig cc -c` for `env.o`, then Odin links. This alone does not prove a Zig runtime archive or every helper is linked |
| LLVM compiler-rt-derived Zig helpers | Installed add/mul/powi files cite upstream source revisions. Full official compiler-rt licenses retained at corresponding upstream revisions, including exceptions and legacy text | Conditional bounded coverage of ports; neither LLVM compiler executable nor entire LLVM tree is claimed to be embedded |
| musl-derived Zig math helpers | Installed Zig compiler_rt math source explicitly cites musl; exact distribution's `libc/musl/COPYRIGHT` retained | Conditional runtime-port attribution, **not** a claim that freestanding build links musl libc |
| Shader generator | `sokol-tools-bin` `11d0cf678105d614d675e6d9bd2aaf3eeff12f8c`, archive SHA-256 `c18bc3d9a52d63f385fcff9d04461e0f1c58f84102a0386acf59b6747655d17d`; MIT, Andre Weissflog 2019 | `sokol-shdc` is a build tool, not linked WASM. Output `room.glsl.odin` contains generated binding/shader strings, no separate identifiable external notice found in output |
| C compiler standard headers | Zig-supplied `<stddef.h>` and `<stdint.h>` are included for declarations/types | Inclusion of interface declarations is not evidence that host libc, libc++, Apple SDK or all LLVM code ships in WASM |

Both pinned Sokol archives were fetched and their actual bytes checked against
Makefile digests before license extraction. The 46 present station Sokol source
files match that archive after reversing only the local Odin foreign-import
path alteration. This is a source-tree comparison, **not** a dependency-fetch
receipt for any pre-existing binary. The Sokol snapshot itself embeds the actual
C implementation: do not substitute the latest independent `floooh/sokol`
license/revision and pretend it is the source used here.

### Source marking defect, not missing redistribution permission

The standalone downloaded Odin files mark the `../../env.o` adjustment with
`GAMS station demo modification`. The current station-demo vendored Odin files
use the adjusted import but lack that adjacent marker. Their retained zlib
license requires altered source to be plainly marked. When redistributing those
station-demo dependency files, preserve the full original notice and add the
same explicit alteration marker (or distribute freshly fetched, appropriately
patched files). The standalone source already has the marker. This is a known
source-notice compliance follow-up, **not a demand to prove local authorship or
obtain a new upstream permission**. The existing THIRD_PARTY.md statement that
*each* altered station location is marked is not accurate for this local tree.
No source files outside the audit were changed to correct it.

## Custom GLES/JS/host lineage investigation

`web/wasm-include/GLES3/gl3.h` is a short custom type/constant subset, without
Khronos's generated-header preamble, full GLES declaration inventory or
platform-header include. `gl_funcs.h` supplies explicit WASM `env` imports using
Clang attributes. `env.c` selects Sokol and provides local sinf/cosf approximations.
`web/gl-bridge.js` implements a local `GLBridge` class and `createImportObject()`;
`index.html` imports this file directly. No `emcc` stage, generated Emscripten
loader, Emscripten runtime library import or external CDN script appears in this
game's web build path. This does **not** erase the Emscripten-derived allocator
notice found independently in Odin.

The custom files contain no identifiable copied external copyright/license
header. API function names/enumerant values and conventional WebGL marshalling
are not sufficient to identify an external implementation's author or copied
revision. Evidence/code-search comparisons used official Khronos
`api/GLES3/gl3.h`, pinned comparison commit
`1cdd228e34966dd6b95bd203e9f84faba0f371a1`, and Emscripten 4.0.10 comparison commit
`b7dc6e5747465580df5984e723b9d1f10d8e804b` (`src/lib/libwebgl.js` and its GLES3 header).
They establish relevant API/interface origins, not byte identity or provenance.
A full Khronos MIT header notice is retained conservatively from that immutable
Emscripten-vendored Khronos header. Khronos `gl.xml` has Apache-2.0 terms while
its generated GLES3 header is MIT: these must not be conflated. The XML notice
is reference evidence only, not a claim that XML was copied/shipped.

Local history:

* `9990f9814245d8bab6f1301572c14cd3078bfa88` (2026-05-22, Romāns Potašovs)
  moved game infrastructure into `examples/demo/game`; predecessor tree already
  had GLES headers under `plugins/game` and bridge/env under `plugins/game2`.
* `d6778f9d4603112d20ab6e01a85c5c8dd03be81a` (2026-03-05, Romāns Potašovs)
  already contains `cmd/browser/util/gl-bridge.js`; so May's move is not the
  bridge's first local existence.
* Preserved historical snapshots and SHA-256s show local lineage. A committer
  name is neither an original-author certificate nor an external license grant.
  Earlier absolute provenance remains unknown and disclosed. Standing owner
  rights cover local inheritance absent an identifiable contrary third-party
  restriction. No invented external "game upstream" is assigned.

## Full notice payload

Copy `NOTICE.txt` to the new repository root as `NOTICE`; retain its existing
complete Apache `LICENSE`. Copy **all** `licenses/*.txt` verbatim into
`game/THIRD_PARTY_LICENSES/`. These are raw upstream files or byte-for-byte
complete embedded-notice slices (comment syntax/indentation deliberately kept);
SHA-256, source URL/path, revision and extraction description are in `audit.json`.
Do not replace them with hand-retyped SPDX summaries or discard author clauses.

The complete compiler-rt license files include upstream legacy terms and
exceptions verbatim. Retaining those full files does not assert that every
component mentioned by an upstream licensing file is part of this game.
`evidence/emscripten-LICENSE`, `AUTHORS` and libwebgl are **comparison evidence**,
not the claimed license of the local bridge; the actually applicable allocator
MIT text is `licenses/odin-emmalloc.txt`. `sokol-tools-bin.txt` covers the
identified build dependency; this review does not authorize redistribution of
an SDK/toolchain bundle or certify every library inside the tool executable.

For a standalone visitor web ZIP, include root `NOTICE`, `LICENSE`, this review,
and `THIRD_PARTY_LICENSES/` alongside `index.html`, JS, WASM and content. The
notice deliberately describes conservative/conditional compiler runtime
coverage. Do not describe this source-level pack as a certification of an
unreviewed artifact's precise retained routines.

## Bind the notices to the build/release inputs

Recommended integration (not performed outside this directory):

1. Template/new-repository root `NOTICE`, `LICENSING.md`, and
   `game/THIRD_PARTY.md` should use this bounded conclusion instead of the old
   blanket "unknown authorship requires owner approval" publication gate.
2. Track the full notice pack and this review in the source archive. Do not ship
   downloaded tools, caches or prebuilt `env.o` as if they were original source.
3. Make `web`/web-export/release-copy explicitly copy `NOTICE`, `LICENSE`, review
   and full licenses into the web output. Include the notice files as declared
   prerequisites, so packaging cannot silently omit or retain stale notices.
   `deps` currently copies just two Sokol licenses: it does not assemble runtime
   notices or web-distribution notices automatically.
4. Record SHA-256s of root/game Makefiles, flake.nix/flake.lock, dependency pins,
   imported source files, generated `room.glsl.odin`, `env.c`, both GLES headers,
   JS/HTML, content pack and notice files in the release build receipt. Hashes in
   this audit are a reference inventory, not a release receipt for fresh bytes.
5. Capture tool versions/root **under the unchanged lock**, e.g. from the
   standalone repository `nix develop --no-write-lock-file --command odin root`
   and `... odin version`, plus Zig version/root and source/compiler hashes.
   `ODIN`/`ZIG` Makefile overrides and PATH can change actual tools despite a
   lock; fail receipt validation on unreviewed substitution rather than
   silently claiming the old notice/tool binding.
6. For the fresh parent build, retain actual compile/link command output and
   final WASM/source/notice hashes. If claiming exact Zig runtime inclusion or
   pruning conditional notices, inspect the link inputs/map and symbol origins;
   otherwise keep the conservative conditional notices. Nix host compiler
   libraries are not automatically shipped visitor-game dependencies.
7. Source/template/newrepo insertion paths are explicit, but this audit changes
   neither the template nor standalone. A fresh-build/packaging agent must apply
   those integration edits in its own authorized scope and verify archive
   contents. Notice omission or the station alteration-marker defect are
   actionable packaging/source-compliance defects, not discovered missing
   third-party permission.

Existing `game/build.nosync/web` files (and source export copies) are hashed only
as observed inventory. They were not rebuilt, matched to link receipts or
certified as emitted by the reviewed environment. The review does not cover
future changed source/dependencies, native builds, plugin binary releases,
trademarks, or non-code rights beyond the supplied owner-rights assumption.
