#!/usr/bin/env python3
"""Build blinded benchmark cases from demos/ into OUT_DIR.

Each case is a small git repo: commit 1 = baseline, commit 2 = the change under review.
Answer keys, hidden tests and folder names that hint at the defect are left out.

  python3 benchmark/build_cases.py OUT_DIR
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEMOS = os.path.join(os.path.dirname(HERE), "demos")

# case id -> (demo, baseline source folder or None, change source folder)
CASES = {
    # batch "F": flawed changes
    "F1": ("d-refactor-security", "before", "after"),
    "F2": ("c-python-to-rust", "legacy", "rust_port"),
    "F3": ("e-edge-cases", None, "after"),
    "F4": ("b-weakened-tests", "before", "after"),
    "F5": ("a-business-rule", None, "after"),
    # batch "K": correct changes (negative controls)
    "K1": ("e-edge-cases", None, "control"),
    "K2": ("a-business-rule", None, "control"),
    "K3": ("c-python-to-rust", "legacy", "control_rust"),
}


def git(cwd, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="dev", GIT_AUTHOR_EMAIL="dev@example.com",
               GIT_COMMITTER_NAME="dev", GIT_COMMITTER_EMAIL="dev@example.com",
               GIT_AUTHOR_DATE="2026-11-20T10:00:00", GIT_COMMITTER_DATE="2026-11-20T10:00:00")
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=env)


def copy_files(src, dst):
    for name in os.listdir(src):
        if name in ("target", "__pycache__", ".pytest_cache"):
            continue
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=shutil.ignore_patterns("target", "__pycache__", ".pytest_cache"))
        else:
            shutil.copy2(s, d)


def build(case_id, out):
    demo, base, change = CASES[case_id]
    src = os.path.join(DEMOS, demo)
    repo = os.path.join(out, f"case-{case_id}")
    os.makedirs(repo)
    shutil.copy2(os.path.join(src, "REQUIREMENTS.md"), repo)
    git(repo, "init", "-q", "-b", "main")
    if demo == "c-python-to-rust":
        # baseline: legacy Python + conventional tests; change: adds the Rust port as rust_port/
        os.makedirs(os.path.join(repo, "legacy_python"))
        copy_files(os.path.join(src, "legacy_python"), os.path.join(repo, "legacy_python"))
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
    title = open(os.path.join(repo, "REQUIREMENTS.md"), encoding="utf-8").readline().strip("# \n")
    git(repo, "commit", "-qm", title)
    return repo


if __name__ == "__main__":
    out = os.path.abspath(sys.argv[1])
    os.makedirs(out, exist_ok=True)
    for cid in CASES:
        print(build(cid, out))
