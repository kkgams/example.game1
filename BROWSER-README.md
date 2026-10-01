# Station — browser game

This prebuilt export runs independently of GAMS. Keep its runtime files together
with LICENSE, NOTICE, THIRD-PARTY-NOTICES.txt and every other document from the ZIP.
The release ZIP includes UPSTREAM-NOTICES/; the Project's content-only export
retains the same full upstream terms in THIRD-PARTY-NOTICES.txt.

Serve this directory with an ordinary static HTTP server, for example:

```sh
python3 -m http.server 8814
```

Open http://localhost:8814/ in a WebGL2-capable browser. Direct file:// opening is
not supported. Move with WASD/arrows, interact with E, restart with R. The default
puzzle requires restoring power before the exit unlocks. Pick up the key too.

To edit the door rule and export the key variant, download the separate Project
ZIP and open it with the released GAMS 2.0.3 Apple Silicon app. Its prebuilt game
and installed Project Units allow content-only exports without Odin, Zig or Nix.
See that Project's README for the walkthrough. No Host binary is bundled here.
