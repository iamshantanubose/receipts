#!/usr/bin/env python3
"""Test-integrity scanner: finds changes that make a test suite *look* green without proving behaviour.

Detects, in a diff: deleted test files/functions, newly skipped/disabled/focused tests, dropped
assertion counts, weakened assertions (exact -> approximate/truthy/membership), edited expected
values, swallowed exceptions, lowered or removed coverage gates, CI steps told to ignore failures,
and mock-heavy additions. Best-effort patterns for Python, JS/TS, Rust, Go, Java/Kotlin, C# and Ruby.

It is a *heuristic triage tool*: every finding is a lead to confirm by reading the code, not a verdict.
A clean result does NOT prove the tests are adequate.

Usage:
  test_integrity_scan.py                       # working tree (incl. untracked files) vs HEAD
  test_integrity_scan.py --base main           # working tree vs merge-base(main, HEAD), i.e. "this branch"
  test_integrity_scan.py --base main --head HEAD   # committed branch changes only
  test_integrity_scan.py --before old_dir --after new_dir   # two folders, no git repo needed
  add --json for machine-readable output
Exit code: 0 = nothing HIGH, 1 = at least one HIGH finding, 2 = error (bad input, git failure).
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

TEST_PATH = re.compile(
    r"(^|/)(tests?|__tests__|spec|specs)/|(^|/)test_[^/]*$|_test\.[a-z]+$|\.(test|spec)\.[jt]sx?$|"
    r"(Test|Tests|Spec)\.(java|kt|cs|scala)$|_spec\.rb$|(^|/)conftest\.py$", re.I)
CONFIG_PATH = re.compile(
    r"(^|/)(pyproject\.toml|setup\.cfg|tox\.ini|pytest\.ini|\.coveragerc|jest\.config\.[cm]?[jt]s|vitest\.config\.[cm]?[jt]s|"
    r"package\.json|karma\.conf\.js|\.gitlab-ci\.yml|Makefile|Cargo\.toml|codecov\.ya?ml|\.nycrc(\.json)?|"
    r"phpunit\.xml|build\.gradle(\.kts)?|pom\.xml|\.github/workflows/[^/]+\.ya?ml)$", re.I)

# Test definitions (name captured). Kept deliberately narrow to avoid treating helpers as tests.
TEST_DEF = re.compile(
    r"^\s*(?:async\s+)?def\s+(test\w*)\s*\("                                # Python
    r"|^\s*(?:it|test|specify|describe|context)\s*\(?\s*['\"`](.+?)['\"`]"  # JS/TS, Ruby (it "x" do)
    r"|^\s*(?:pub\s+)?(?:async\s+)?fn\s+(test_\w+)\s*\("                    # Rust (test_ prefix)
    r"|^\s*func\s+(Test\w+)\s*\("                                           # Go
    r"|\bt\.Run\(\s*\"(.+?)\""                                              # Go subtests
    r"|^\s*(?:public\s+|internal\s+)?(?:async\s+)?(?:void|Task)\s+(test\w*)\s*\("  # Java/C# test-prefixed
    r"|^\s*fun\s+`(.+?)`\s*\(")                                             # Kotlin backtick names
TEST_MARKER = re.compile(r"^\s*(@Test\b|@ParameterizedTest\b|#\[test\]|#\[tokio::test|\[(Fact|Theory|Test|TestMethod|TestCase)\b)")
SKIP_HARD = re.compile(
    r"@pytest\.mark\.(skip|xfail)\b(?!if)|@unittest\.(skip|expectedFailure)\b(?!If|Unless)|\bpytest\.skip\(|self\.skipTest\(|"
    r"\b(it|test|describe|context|specify)\.(skip|todo|only)\s*\(|^\s*x(it|describe|test|specify)\s*[\(\s]|^\s*f(it|describe)\s*\(\s*['\"`]|"
    r"#\[ignore\]|\bt\.Skip(f|Now)?\(|@(Disabled|Ignore)\b|\[(Ignore|Skip)\b|\(\s*Skip\s*=|^\s*skip\s+['\"]|^\s*pending\s*[\(\s'\"]")
SKIP_COND = re.compile(r"@pytest\.mark\.skipif\b|@unittest\.skip(If|Unless)\b|@(EnabledIf|DisabledIf|EnabledOn|DisabledOn)\w*")
ASSERT = re.compile(
    r"\bassert\b|\bassert[A-Z]\w*\(|\bexpect\s*\(|\bassert_eq!|\bassert_ne!|\bassert!|\bt\.(Error|Fatal)f?\(|"
    r"\brequire\.\w+\(|\.should\b|\bverify\(|\bpytest\.raises\b|\bassertThat\(|\bAssert\.\w+\(|\bassertFailsWith\b")
EXACT = re.compile(r"==|assertEqual\(|assertEquals\(|toBe\(|toEqual\(|toStrictEqual\(|assert_eq!|\.Equal\(|"
                   r"assertIs\(|isEqualTo\(|\beq\(|toThrow\(|pytest\.raises|assertRaises|Assert\.(AreEqual|Equal|Throws)")
WEAK = re.compile(
    r"approx\(|assertAlmostEqual|toBeCloseTo|abs\(.*\)\s*[<]|math\.isclose|assertTrue\(|assert\s+True\b|"
    r"toBeTruthy\(|toBeDefined\(|not\.toBeNull\(|toBeGreaterThan(OrEqual)?\(|\bassert\s+\w+\s+in\b|"
    r"assertIn\(|toContain\(|assertIsNotNone\(|\.is_ok\(\)|\bassert!\(\s*true|expect\(true\)|assert\s+len\(|"
    r"Assert\.(True|NotNull)\(")
SWALLOW = re.compile(r"except(\s+[\w.]+(\s+as\s+\w+)?)?\s*:\s*(pass|\.\.\.)\s*$|catch\s*\([^)]*\)\s*\{\s*\}|"
                     r"catch\s*\{\s*\}|\.catch\(\s*\(\)\s*=>\s*\{\s*\}\s*\)|\|\|\s*true\b|_\s*=\s*err\b")
EXCEPT_OPEN = re.compile(r"^\s*(except(\s+[\w.]+(\s+as\s+\w+)?)?\s*:|(\}\s*)?catch\s*(\([^)]*\))?\s*\{|rescue\b.*)\s*$")
SWALLOW_BODY = re.compile(r"^\s*(pass|\.\.\.|\})\s*$")
MOCK = re.compile(r"mock\.patch|MagicMock|Mock\(|monkeypatch\.setattr|jest\.mock\(|jest\.fn\(|vi\.mock\(|"
                  r"sinon\.(stub|mock)|mockito|when\(.*\)\.thenReturn|gomock|mockall|patch\.object")
COVERAGE = re.compile(r"(fail_under|fail-under|cov-fail-under|coverageThreshold|minimum_coverage|min_coverage|"
                      r"\bbranches\b|\blines\b|\bfunctions\b|\bstatements\b|\bthreshold\b|jacoco\.minimum)\D{0,12}(\d+(\.\d+)?)", re.I)
GATE_KEYS = re.compile(r"fail_under|fail-under|cov-fail-under|coverageThreshold|minimum_coverage|min_coverage", re.I)
CI_IGNORE = re.compile(r"continue-on-error:\s*true|allow_failure:\s*true|--passWithNoTests|\|\|\s*(true|exit 0)\b|"
                       r"--deselect\b|--ignore[= ]\S*test|-k\s+['\"]?not\b|testPathIgnorePatterns|--exitzero|"
                       r"^\s*set \+e\b|--no-fail-on-empty", re.I)
LITERAL = re.compile(r"(['\"]).*?\1|\b\d+(\.\d+)?\b")

SEV_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}


def is_comment(t):
    t = t.strip()
    return (t.startswith("#") and not t.startswith("#[")) or t.startswith("//")


def lits(t):
    return [m.group(0) for m in LITERAL.finditer(t)]


def test_name(t):
    m = TEST_DEF.search(t)
    return next((g for g in m.groups() if g), None) if m else None


class ScanError(Exception):
    pass


def git(args, cwd=None, ok=(0,)):
    try:
        p = subprocess.run(["git", "-c", "core.quotePath=false"] + args, capture_output=True, cwd=cwd)
    except FileNotFoundError:
        raise ScanError("git is not installed")
    err = p.stderr.decode("utf-8", "replace").strip()
    if p.returncode not in ok or (p.returncode != 0 and err):
        raise ScanError(err.splitlines()[0] if err else f"git {' '.join(args[:2])} failed ({p.returncode})")
    return p.stdout.decode("utf-8", "replace")


def parse_diff(text):
    """Parse a unified diff. Returns [{file, old, status, lines: [(kind, old_ln, new_ln, text, hunk)]}]."""
    files, cur = [], None
    old_ln = new_ln = old_left = new_left = 0
    hunk = -1
    for line in text.splitlines():
        if cur is not None and (old_left > 0 or new_left > 0):  # inside a hunk: trust the counts
            tag, body = (line[:1], line[1:]) if line else (" ", "")
            if tag == "-":
                cur["lines"].append(("-", old_ln, None, body, hunk))
                old_ln += 1
                old_left -= 1
            elif tag == "+":
                cur["lines"].append(("+", None, new_ln, body, hunk))
                new_ln += 1
                new_left -= 1
            elif tag == "\\":
                pass  # "\ No newline at end of file"
            else:
                old_ln += 1
                new_ln += 1
                old_left -= 1
                new_left -= 1
            continue
        if line.startswith("diff --git"):
            cur = {"file": None, "old": None, "status": "modified", "lines": [], "binary": False}
            files.append(cur)
        elif cur is None:
            continue
        elif line.startswith("Binary files"):
            cur["binary"] = True
        elif line.startswith("--- "):
            p = line[4:].rstrip("\t")
            cur["old"] = None if p == "/dev/null" else re.sub(r"^a/", "", p)
        elif line.startswith("+++ "):
            p = line[4:].rstrip("\t")
            new = None if p == "/dev/null" else re.sub(r"^b/", "", p)
            cur["file"] = new or cur["old"]
            if new is None:
                cur["status"] = "deleted"
            elif cur["old"] is None:
                cur["status"] = "added"
        elif line.startswith("@@"):
            m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            old_ln, new_ln = int(m.group(1)), int(m.group(3))
            old_left = int(m.group(2)) if m.group(2) is not None else 1
            new_left = int(m.group(4)) if m.group(4) is not None else 1
            hunk += 1
    for fd in files:
        if fd["file"] is None:  # header-only entries (mode change, binary) -> take name from diff line
            fd["file"] = fd["old"] or ""
    return files


def strip_root(path, root):
    """Make a --no-index diff path relative to the folder it came from."""
    path = re.sub(r"^(\./)+", "", path.replace("\\", "/").lstrip("/"))
    for cand in (os.path.normpath(root), os.path.abspath(root), os.path.realpath(root)):
        cand = cand.replace("\\", "/").lstrip("/")
        if cand in ("", "."):
            continue
        if path.startswith(cand.rstrip("/") + "/"):
            return path[len(cand.rstrip("/")) + 1:]
    return path


def scan(files):
    findings = []

    def add(sev, rule, f, ln, msg, code=""):
        findings.append({"severity": sev, "rule": rule, "file": f, "line": ln or 0, "message": msg,
                         "code": code.strip()[:160]})

    for fd in files:
        f = fd["file"] or ""
        if fd.get("binary"):
            continue
        is_test = bool(TEST_PATH.search(f))
        is_cfg = bool(CONFIG_PATH.search(f))
        removed = [(o, t, h) for k, o, n, t, h in fd["lines"] if k == "-"]
        added = [(n, t, h) for k, o, n, t, h in fd["lines"] if k == "+"]

        if is_test and fd["status"] == "deleted":
            n = sum(1 for _, t, _ in removed if ASSERT.search(t))
            add("HIGH", "deleted-test-file", f, 0, f"Test file deleted ({n} assertions removed). Confirm the behaviour it covered is truly gone.")
            continue

        if is_test:
            rem_names = {}
            for ln, t, _ in removed:
                name = test_name(t)
                if name:
                    rem_names.setdefault(name, ln)
            add_names = {test_name(t) for _, t, _ in added} - {None}
            gone = [(n, ln) for n, ln in rem_names.items() if n not in add_names]
            new_names = add_names - set(rem_names)
            for name, ln in gone:
                if new_names:
                    add("MEDIUM", "test-removed-or-renamed", f, ln,
                        f"Test `{name}` is gone; new test names were added in the same file. Check it was renamed, not dropped.")
                else:
                    add("HIGH", "deleted-test", f, ln, f"Test `{name}` was removed and not re-added under the same name.")
            markers_lost = sum(1 for _, t, _ in removed if TEST_MARKER.search(t)) - sum(1 for _, t, _ in added if TEST_MARKER.search(t))
            if markers_lost > 0 and not gone:
                add("HIGH", "deleted-test", f, 0, f"{markers_lost} test annotation(s)/attribute(s) removed (@Test, [Fact], #[test], …).")
            for ln, t, _ in added:
                if is_comment(t):
                    continue
                if SKIP_HARD.search(t):
                    linked = re.search(r"(issue|ticket|bug|jira|#\d+|\b[A-Z]{2,}-\d+|https?://)", t, re.I)
                    add("MEDIUM" if linked else "HIGH", "skipped-test", f, ln,
                        "Test skipped/disabled/focused" + ("." if linked else " with no linked issue."), t)
                elif SKIP_COND.search(t):
                    add("LOW", "conditional-skip", f, ln, "Conditional skip added. Check the condition is legitimate (platform, optional dependency).", t)
            a_rem = sum(1 for _, t, _ in removed if ASSERT.search(t) and not is_comment(t))
            a_add = sum(1 for _, t, _ in added if ASSERT.search(t) and not is_comment(t))
            if a_rem > a_add:
                add("HIGH" if a_rem - a_add >= 2 else "MEDIUM", "assertions-dropped", f, 0,
                    f"Assertion count fell by {a_rem - a_add} ({a_rem} removed, {a_add} added).")
            # weakened / edited assertions: pair each removed exact assertion with the most similar added line in the same hunk
            used = set()
            for ln_r, t_r, h in removed:
                if not (ASSERT.search(t_r) and EXACT.search(t_r)) or is_comment(t_r):
                    continue
                cands = [(difflib.SequenceMatcher(None, t_r.strip(), t.strip()).ratio(), ln, t)
                         for ln, t, h2 in added if h2 == h and ln not in used and ASSERT.search(t)]
                if not cands:
                    continue
                ratio, ln_a, t_a = max(cands)
                if ratio < 0.5:
                    continue
                used.add(ln_a)
                if WEAK.search(t_a) and not WEAK.search(t_r):
                    add("HIGH", "weakened-assertion", f, ln_a,
                        f"Exact assertion replaced by a weaker form. Was: `{t_r.strip()[:90]}`", t_a)
                elif EXACT.search(t_a) and lits(t_r) != lits(t_a) and \
                        re.sub(LITERAL, "_", t_r).strip() == re.sub(LITERAL, "_", t_a).strip():
                    add("MEDIUM", "expected-value-changed", f, ln_a,
                        f"Expected value edited. Was: `{t_r.strip()[:90]}`. Check that the requirement changed, not just the output.", t_a)
            mocks = sum(1 for _, t, _ in added if MOCK.search(t)) - sum(1 for _, t, _ in removed if MOCK.search(t))
            if mocks >= 3:
                add("MEDIUM", "mock-heavy", f, 0, f"{mocks} new mocks/patches. Check the test still exercises real behaviour.")

        added_by_ln = {ln: t for ln, t, _ in added}
        for ln, t, _ in added:
            if is_comment(t):
                continue
            multi = EXCEPT_OPEN.match(t) and SWALLOW_BODY.match(added_by_ln.get(ln + 1, "x"))
            if SWALLOW.search(t) or multi:
                add("HIGH" if is_test else "MEDIUM", "swallowed-error", f, ln,
                    "Error swallowed or failure ignored." + (" In a test, this hides failures." if is_test else ""), t)

        if is_cfg:
            old_cov = {}
            for _, t, _ in removed:
                m = COVERAGE.search(t)
                if m:
                    old_cov[m.group(1).lower()] = float(m.group(2))
            new_keys = set()
            for ln, t, _ in added:
                m = COVERAGE.search(t)
                if m:
                    key = m.group(1).lower()
                    new_keys.add(key)
                    if key in old_cov and float(m.group(2)) < old_cov[key]:
                        add("HIGH", "coverage-gate-lowered", f, ln,
                            f"Coverage gate `{m.group(1)}` lowered {old_cov[key]:g} → {float(m.group(2)):g}.", t)
                if CI_IGNORE.search(t) and not is_comment(t):
                    add("HIGH", "failures-ignored", f, ln, "Config now ignores/deselects tests or failures.", t)
            for key, val in old_cov.items():
                if key not in new_keys and GATE_KEYS.search(key):
                    add("HIGH", "coverage-gate-removed", f, 0, f"Coverage gate `{key}` ({val:g}) was removed.")
    findings.sort(key=lambda x: (SEV_ORDER[x["severity"]], x["file"], x["line"]))
    return findings


def git_diff_worktree(repo, base):
    """Diff of `base` vs working tree, plus untracked (not ignored) files as additions."""
    text = git(["diff", "--unified=3", "--no-color", "-M", base, "--"], cwd=repo)
    untracked = git(["ls-files", "--others", "--exclude-standard", "-z"], cwd=repo).split("\0")
    for path in filter(None, untracked):
        text += "\n" + git(["diff", "--no-index", "--unified=3", "--no-color", "--", os.devnull, path], cwd=repo, ok=(0, 1))
    return text


def verify_ref(repo, ref):
    if ref.startswith("-"):
        raise ScanError(f"invalid ref {ref!r}")
    return git(["rev-parse", "--verify", "--quiet", "--end-of-options", ref + "^{commit}"], cwd=repo).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", help="branch/ref the change is based on (diffed from merge-base with HEAD). Default: HEAD")
    ap.add_argument("--head", help="ref for the new side (default: working tree incl. untracked files)")
    ap.add_argument("--before", help="folder with the old version (no-git mode)")
    ap.add_argument("--after", help="folder with the new version (no-git mode)")
    ap.add_argument("--repo", default=".", help="repository path (git mode)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        if a.before or a.after:
            if not (a.before and a.after):
                raise ScanError("--before and --after go together")
            for d in (a.before, a.after):
                if not os.path.isdir(d):
                    raise ScanError(f"not a folder: {d}")
            text = git(["diff", "--no-index", "--unified=3", "--no-color", "--", a.before, a.after], ok=(0, 1))
            files = parse_diff(text)
            for fd in files:
                fd["file"] = strip_root(strip_root(fd["file"] or "", a.after), a.before)
        else:
            if not os.path.isdir(a.repo):
                raise ScanError(f"not a folder: {a.repo}")
            if git(["rev-parse", "--is-inside-work-tree"], cwd=a.repo, ok=(0, 128)).strip() != "true":
                raise ScanError("not a git repository (use --repo, or --before/--after for plain folders)")
            if not git(["rev-list", "-n1", "--all"], cwd=a.repo).strip():
                raise ScanError("repository has no commits yet")
            head = verify_ref(a.repo, a.head) if a.head else None
            if a.base:
                base_sha = verify_ref(a.repo, a.base)
                base = git(["merge-base", base_sha, head or "HEAD"], cwd=a.repo).strip()
            else:
                base = verify_ref(a.repo, "HEAD")
            if head:
                text = git(["diff", "--unified=3", "--no-color", "-M", base, head, "--"], cwd=a.repo)
            else:
                text = git_diff_worktree(a.repo, base)
            files = parse_diff(text)
    except ScanError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    findings = scan(files)
    if a.json:
        print(json.dumps({"files_changed": len(files), "findings": findings}, indent=2))
    else:
        counts = defaultdict(int)
        for x in findings:
            counts[x["severity"]] += 1
        print(f"Test-integrity scan: {len(files)} files changed, {len(findings)} findings "
              f"({', '.join(f'{k} {counts[k]}' for k in SEV_ORDER if counts[k]) or 'none'})")
        for x in findings:
            loc = f"{x['file']}:{x['line']}" if x["line"] else x["file"]
            print(f"- [{x['severity']}] {x['rule']} @ {loc}: {x['message']}")
            if x["code"]:
                print(f"    > {x['code']}")
        if not findings:
            print("No test-integrity red flags found by pattern scan. This does NOT prove the tests are adequate.")
    return 1 if any(x["severity"] == "HIGH" for x in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
