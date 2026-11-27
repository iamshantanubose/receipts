#!/usr/bin/env python3
"""Build blinded benchmark cases from demos/ into OUT_DIR.

Each case is a small git repo: commit 1 = baseline, commit 2 = the change under review.
Answer keys, hidden tests and folder names that hint at the defect are left out.

Layout (the same one the published run used):
  OUT_DIR/flawed/case-1 … case-5     F1 … F5   (one agent reviews this whole folder)
  OUT_DIR/controls/case-1 … case-3   K1 … K3   (a separate agent reviews this folder)
  OUT_DIR/case-map.json              which case is which; never give this file to an agent

  python3 benchmark/build_cases.py OUT_DIR
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEMOS = os.path.join(os.path.dirname(HERE), "demos")
SKIP = ("target", "__pycache__", ".pytest_cache")

# case id -> (batch folder, case folder, demo, baseline source folder or None, change source folder)
CASES = {
    "F1": ("flawed", "case-1", "d-refactor-security", "before", "after"),
    "F2": ("flawed", "case-2", "c-python-to-rust", "legacy_python", "rust_port"),
    "F3": ("flawed", "case-3", "e-edge-cases", None, "after"),
    "F4": ("flawed", "case-4", "b-weakened-tests", "before", "after"),
    "F5": ("flawed", "case-5", "a-business-rule", None, "after"),
    "K1": ("controls", "case-1", "e-edge-cases", None, "control"),
    "K2": ("controls", "case-2", "a-business-rule", None, "control"),
    "K3": ("controls", "case-3", "c-python-to-rust", "legacy_python", "control_rust"),
}


def git(cwd: str, *args: str) -> None:
    env = dict(os.environ, GIT_AUTHOR_NAME="dev", GIT_AUTHOR_EMAIL="dev@example.com",
               GIT_COMMITTER_NAME="dev", GIT_COMMITTER_EMAIL="dev@example.com",
               GIT_AUTHOR_DATE="2026-11-20T10:00:00", GIT_COMMITTER_DATE="2026-11-20T10:00:00")
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=env)


def copy_files(src: str, dst: str) -> None:
    for name in os.listdir(src):
        if name in SKIP:
            continue
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=shutil.ignore_patterns(*SKIP))
        else:
            shutil.copy2(s, d)


def build(case_id: str, out: str) -> str:
    batch, folder, demo, base, change = CASES[case_id]
    src = os.path.join(DEMOS, demo)
    repo = os.path.join(out, batch, folder)
    os.makedirs(repo)
    shutil.copy2(os.path.join(src, "REQUIREMENTS.md"), repo)
    git(repo, "init", "-q", "-b", "main")
    if demo == "c-python-to-rust":
        # baseline: legacy Python + conventional tests; change: adds the Rust port as rust_port/
        os.makedirs(os.path.join(repo, base))
        copy_files(os.path.join(src, base), os.path.join(repo, base))
        for f in ("tests_conventional.txt", "tests_conventional.expected"):
            shutil.copy2(os.path.join(src, f), repo)
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "Legacy Python normalizer")
        os.makedirs(os.path.join(repo, "rust_port"))
        copy_files(os.path.join(src, change), os.path.join(repo, "rust_port"))
        with open(os.path.join(repo, ".gitignore"), "w") as f:
            f.write("target/\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "API-301: port normalizer to Rust")
        return repo
    if base:
        copy_files(os.path.join(src, base), repo)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "Baseline")
    for name in os.listdir(repo):  # replace baseline code with the change
        if name not in (".git", "REQUIREMENTS.md"):
            p = os.path.join(repo, name)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    copy_files(os.path.join(src, change), repo)
    git(repo, "add", "-A")
    with open(os.path.join(repo, "REQUIREMENTS.md"), encoding="utf-8") as f:
        title = f.readline().strip("# \n")
    git(repo, "commit", "-qm", title)
    return repo


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out_dir", help="new or empty folder to build the cases in")
    out = os.path.abspath(ap.parse_args().out_dir)
    if os.path.exists(out) and os.listdir(out):
        print(f"ERROR: {out} is not empty. Pick a new folder.", file=sys.stderr)
        return 2
    os.makedirs(out, exist_ok=True)
    for cid in CASES:
        print(f"{cid}  {build(cid, out)}")
    with open(os.path.join(out, "case-map.json"), "w", encoding="utf-8") as f:
        json.dump({cid: f"{b}/{c}" for cid, (b, c, *_rest) in CASES.items()}, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
