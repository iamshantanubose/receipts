#!/usr/bin/env python3
"""Build the release zip: dist/receipts-verify-engineering-<version>.zip

The zip holds one folder, verify-engineering/, with the skill and a copy of LICENSE, ready to unzip into a
skills folder. The version comes from .claude-plugin/plugin.json. File order and timestamps are fixed, so the
same commit always gives the same bytes.

  python3 tools/build_release.py
"""
from __future__ import annotations

import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "verify-engineering")
SKIP_DIRS = {"__pycache__", ".pytest_cache"}
STAMP = (2026, 1, 1, 0, 0, 0)


def add(z: zipfile.ZipFile, src: str, arc: str) -> None:
    info = zipfile.ZipInfo(arc, STAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (0o755 if os.access(src, os.X_OK) else 0o644) << 16
    with open(src, "rb") as f:
        z.writestr(info, f.read())


def main() -> int:
    with open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        version = json.load(f)["version"]
    out = os.path.join(ROOT, "dist", f"receipts-verify-engineering-{version}.zip")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    files = []
    for d, dirs, names in os.walk(SKILL):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        files += [os.path.join(d, n) for n in names if not n.endswith(".pyc") and n != ".DS_Store"]
    with zipfile.ZipFile(out, "w") as z:
        for src in sorted(files):
            add(z, src, "verify-engineering/" + os.path.relpath(src, SKILL).replace(os.sep, "/"))
        add(z, os.path.join(ROOT, "LICENSE"), "verify-engineering/LICENSE")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
