#!/usr/bin/env python3
"""Mutation probe: do the tests notice when the code is wrong?

Copies the project to a throwaway temp folder, plants one small bug at a time in the target file(s)
(flip a comparison, change a boundary, swap and/or, drop a `not`, change +/-, return a constant),
runs your test command, and reports which bugs the tests did NOT catch ("survivors").
Your real working tree is never modified.

Language-agnostic (regex-based), so treat it as a fast probe. For deep work use a real mutation
tool (mutmut, cargo-mutants, Stryker, PIT).

Safety: targets must be relative paths inside --root and must not be (or sit under) symlinks, so a
mutation can only ever touch the throwaway copy. The copy isolates *files*, not side effects: if your
tests talk to real databases, services or the network, they will do so for every mutant. Ask first.

Usage:
  mutation_probe.py --target src/pricing.py --test "python3 -m pytest -q -x" [--root .] [--max 40]
  [--exclude node_modules --exclude target]   # skip big folders the tests don't need (default: .git, caches)
Exit code: 0 = no survivors, 1 = survivors found, 2 = error (for example, tests fail before mutation).
"""
import argparse
import os
import random
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

MUTATORS = [
    ("<= → <", r"(?<=\s)<=(?=\s)", "<"), (">= → >", r"(?<=\s)>=(?=\s)", ">"),
    ("< → <=", r"(?<=\s)<(?=\s)", "<="), ("> → >=", r"(?<=\s)>(?=\s)", ">="), ("== → !=", r"==", "!="), ("!= → ==", r"!=", "=="),
    ("and → or", r"\band\b", "or"), ("or → and", r"\bor\b", "and"), ("&& → ||", r"&&", "||"),
    ("|| → &&", r"\|\|", "&&"), ("drop not", r"\bnot\s+", ""), ("drop !", r"(?<![\w!])!(?=[A-Za-z_(])", ""),
    ("+ → -", r"(?<=[\w)\]\s])\+(?=[\s\w(])", "-"), ("- → +", r"(?<=[\w)\]\s])-(?=[\s\w(])", "+"),
    ("* → /", r"(?<=[\w)\s])\*(?=[\s\w(])", "/"), ("min → max", r"\bmin\(", "max("),
    ("max → min", r"\bmax\(", "min("), ("True → False", r"\bTrue\b", "False"),
    ("true → false", r"\btrue\b", "false"), ("0 → 1", r"(?<![\w.])0(?![\w.])", "1"),
    ("1 → 0", r"(?<![\w.])1(?![\w.])", "0"),
]
SKIP_LINE = re.compile(r"^\s*(#|//|/\*|\*|import |from \S+ import|use |package |@|\"\"\"|''')")


def candidates(lines):
    out = []
    in_block = None  # inside a triple-quoted string or /* */ comment
    for i, line in enumerate(lines):
        stripped = line.strip()
        if in_block:
            if in_block in line:
                in_block = None
            continue
        for opener, closer in (('"""', '"""'), ("'''", "'''"), ("/*", "*/")):
            if stripped.startswith(opener) or (opener != "/*" and re.search(r"=\s*" + re.escape(opener), line)):
                rest = line.split(opener, 1)[1]
                if closer not in rest:
                    in_block = closer
                break
        if in_block or SKIP_LINE.match(line) or not stripped:
            continue
        if re.search(r"\b\w+!\s*\(", line) or stripped.startswith(("assert", "debug_assert")):
            continue  # macros / assertions: mutating them tests nothing useful
        code = re.sub(r"(['\"]).*?\1", lambda m: " " * len(m.group(0)), line)  # don't mutate inside strings
        code = re.split(r"\s#\s|//", code)[0]
        for name, pat, rep in MUTATORS:
            for m in re.finditer(pat, code):
                out.append((i, m.start(), m.end(), rep, name))
    return out


def split_cmd(cmd):
    return shlex.split(cmd, posix=(os.name != "nt"))


def run(cmd, cwd, timeout):
    t = time.time()
    try:
        p = subprocess.run(split_cmd(cmd), cwd=cwd, capture_output=True, timeout=timeout)
        return p.returncode, time.time() - t
    except subprocess.TimeoutExpired:
        return "timeout", time.time() - t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", required=True, action="append", help="file to mutate (repeatable), relative to --root")
    ap.add_argument("--test", required=True, help="test command run from the project root")
    ap.add_argument("--root", default=".")
    ap.add_argument("--max", type=int, default=40, help="max mutants to try (budget)")
    ap.add_argument("--timeout", type=float, default=120.0, help="seconds per test run")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--exclude", action="append", default=[], help="folder/file name to leave out of the copy (repeatable)")
    a = ap.parse_args()

    root = os.path.realpath(a.root)
    if not os.path.isdir(root):
        print(f"ERROR: --root is not a folder: {a.root}", file=sys.stderr)
        return 2
    for t in a.target:  # targets must resolve to a real file inside root, reached without symlinks
        if os.path.isabs(t) or ".." in t.replace("\\", "/").split("/"):
            print(f"ERROR: --target must be a relative path inside --root without '..': {t}", file=sys.stderr)
            return 2
        real = os.path.join(root, t)
        if not os.path.isfile(real):
            print(f"ERROR: target not found: {t}", file=sys.stderr)
            return 2
        if os.path.realpath(real) != os.path.normpath(real):
            print(f"ERROR: target is a symlink or under a symlinked folder: {t}", file=sys.stderr)
            return 2
    work = tempfile.mkdtemp(prefix="mutation-probe-")
    proj = os.path.join(work, "p")
    ignore = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", *a.exclude)
    shutil.copytree(root, proj, symlinks=True, ignore=ignore)
    for t in a.target:  # belt and braces: the path we will write must be a regular file inside the copy
        path = os.path.join(proj, t)
        if os.path.islink(path) or not os.path.realpath(path).startswith(os.path.realpath(proj) + os.sep):
            print(f"ERROR: refusing to mutate {t}: it does not resolve inside the temporary copy", file=sys.stderr)
            shutil.rmtree(work, ignore_errors=True)
            return 2
    try:
        try:
            rc, secs = run(a.test, proj, a.timeout)
        except OSError as e:
            print(f"ERROR: could not run the test command: {e}", file=sys.stderr)
            return 2
        if rc != 0:
            print(f"ERROR: the test command fails BEFORE any mutation (exit {rc}) when run in the temporary copy. "
                  "Fix or report that first. If it passes in your real folder, the copy may be missing something "
                  "(check --exclude) or the tests depend on absolute paths.", file=sys.stderr)
            return 2
        timeout = max(10.0, secs * 5)
        pool = []
        for t in a.target:
            path = os.path.join(proj, t)
            with open(path, encoding="utf-8") as f:
                lines = f.read().split("\n")
            pool += [(t, c) for c in candidates(lines)]
        random.Random(a.seed).shuffle(pool)
        pool = pool[: a.max]
        killed, survived, timeouts = 0, [], 0
        for t, (i, s, e, rep, name) in pool:
            path = os.path.join(proj, t)
            with open(path, encoding="utf-8") as f:
                original = f.read()
            lines = original.split("\n")
            mutated_line = lines[i][:s] + rep + lines[i][e:]
            lines[i] = mutated_line
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            rc, _ = run(a.test, proj, timeout)
            with open(path, "w", encoding="utf-8") as f:
                f.write(original)
            if rc == "timeout":
                timeouts += 1
                killed += 1
            elif rc != 0:
                killed += 1
            else:
                survived.append((t, i + 1, name, mutated_line.strip()))
        total = len(pool)
        print(f"Mutation probe: {total} mutants, {killed} killed, {len(survived)} survived"
              + (f", {timeouts} timed out (counted as killed)" if timeouts else ""))
        if total:
            print(f"Mutation score: {100 * killed / total:.0f}%")
        for t, ln, name, code in survived:
            print(f"- SURVIVED {t}:{ln} [{name}]  {code}")
        if survived:
            print("Each survivor is a bug the current tests would let through. Add a test that kills it, or explain why it is equivalent.")
        return 1 if survived else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)  # only our own temp copy


if __name__ == "__main__":
    sys.exit(main())
