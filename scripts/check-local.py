#!/usr/bin/env python3
"""Fail fast unless sibling Project Units have been explicitly assembled."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    *(f"plugins/{name}.comp.wasm" for name in
      ("fs", "layout", "lua", "director-compiler", "respack")),
    *(f"ui-plugins/{name}.js" for name in
      ("context", "keys", "layout", "toast", "popup", "tooltip")),
    *(f"views/{name}.js" for name in
      ("view-files", "view-code", "view-ng", "view-ng-node", "files-rename", "files-default")),
    "themes/the98.css",
]
missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
if missing:
    raise SystemExit("local Project assembly is incomplete; run `make setup-local` first; missing:\n  "
                     + "\n  ".join(missing))
print("local Project assembly is complete")
