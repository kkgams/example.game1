# Game third-party build inputs

| Dependency | Immutable revision | Archive SHA-256 |
| --- | --- | --- |
| sokol-odin | 9ea6ec125f002180d6cc6e7a009087ca0a019da4 | 0eebee1d50bb08f1bf44f5458d8c32d61e4c2069d73a2eddb9feeb7c04d185ba |
| sokol-tools-bin | 11d0cf678105d614d675e6d9bd2aaf3eeff12f8c | c18bc3d9a52d63f385fcff9d04461e0f1c58f84102a0386acf59b6747655d17d |

The Makefile validates each archive before extraction. Sokol Odin bindings and the
embedded C gfx implementation are zlib-licensed. Modified WASM foreign imports
carry explicit `GAMS station demo modification` markers for the ../../env.o path.
Shader tools are build-time only, MIT-licensed, and are not distributed binaries.

The locked standalone environment selects Odin dev-2026-05 and Zig 0.16.0.
Odin runtime/core use zlib terms; the actual WASM allocator preserves Emscripten
emmalloc MIT terms. Unicode and conservative Sun/Cephes math notices are retained.
Conditional Zig/LLVM compiler-rt/musl-derived helper terms are retained without a
claim that all those routines, musl libc, or compiler executables ship in the WASM.

Custom GLES headers and WebGL/host infrastructure have local demo lineage; earliest
original authorship is not independently established. Standing owner rights cover
local code absent an identified contrary restriction. A Khronos interface-header
notice is retained conservatively, not as proof of implementation copying.

Full terms: THIRD_PARTY_LICENSES/ and ../THIRD-PARTY-NOTICES.txt. See
../THIRD-PARTY-REVIEW.md for upstream URLs, exact license receipts and bounds.
Each release must record actual source/tool/build/output hashes; this source-level
review is not an attestation that old generated binaries match reviewed inputs.
