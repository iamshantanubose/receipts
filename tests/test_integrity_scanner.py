import json
import os
import subprocess

from conftest import DEMOS, run_script


def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(text)


def scan(before, after):
    r = run_script("test_integrity_scan.py", "--before", str(before), "--after", str(after), "--json")
    assert r.returncode in (0, 1), r.stderr
    return r.returncode, {f["rule"] for f in json.loads(r.stdout)["findings"]}, json.loads(r.stdout)["findings"]


BASE_TEST = """import pytest
from m import f

def test_exact():
    assert f(2) == 4

def test_raises():
    with pytest.raises(ValueError):
        f(-1)
"""


def test_scenario_b_catches_all_planted_tampering():
    code, rules, findings = scan(os.path.join(DEMOS, "b-weakened-tests", "before"),
                                 os.path.join(DEMOS, "b-weakened-tests", "after"))
    assert code == 1
    assert {"coverage-gate-lowered", "weakened-assertion", "skipped-test", "deleted-test"} <= rules
    weakened = [f for f in findings if f["rule"] == "weakened-assertion"]
    assert len(weakened) == 2  # approx(...) and abs(...) < 0.1


def test_clean_change_has_no_findings(tmp_path):
    """Negative control: adding a new honest test must not raise flags."""
    write(tmp_path / "a", "tests/test_m.py", BASE_TEST)
    write(tmp_path / "b", "tests/test_m.py", BASE_TEST + "\n\ndef test_zero():\n    assert f(0) == 0\n")
    code, rules, _ = scan(tmp_path / "a", tmp_path / "b")
    assert code == 0 and rules == set()


def test_js_skip_only_and_truthy(tmp_path):
    write(tmp_path / "a", "src/m.test.js", "it('adds', () => {\n  expect(add(1, 2)).toBe(3);\n});\n")
    write(tmp_path / "b", "src/m.test.js", "it.only('adds', () => {\n  expect(add(1, 2)).toBeTruthy();\n});\n")
    _, rules, _ = scan(tmp_path / "a", tmp_path / "b")
    assert {"skipped-test", "weakened-assertion"} <= rules


def test_rust_ignore_and_deleted_test_file(tmp_path):
    write(tmp_path / "a", "tests/core_test.rs", "#[test]\nfn adds() {\n    assert_eq!(add(1, 2), 3);\n}\n")
    write(tmp_path / "a", "tests/old_test.py", "def test_x():\n    assert 1 == 1\n")
    write(tmp_path / "b", "tests/core_test.rs", "#[test]\n#[ignore]\nfn adds() {\n    assert_eq!(add(1, 2), 3);\n}\n")
    _, rules, _ = scan(tmp_path / "a", tmp_path / "b")
    assert {"skipped-test", "deleted-test-file"} <= rules


def test_ci_ignores_failures_and_jest_threshold(tmp_path):
    write(tmp_path / "a", ".github/workflows/ci.yml", "steps:\n  - run: npm test\n")
    write(tmp_path / "b", ".github/workflows/ci.yml", "steps:\n  - run: npm test || true\n")
    write(tmp_path / "a", "jest.config.js", "module.exports = { coverageThreshold: { global: { lines: 90 } } };\n")
    write(tmp_path / "b", "jest.config.js", "module.exports = { coverageThreshold: { global: { lines: 50 } } };\n")
    _, rules, _ = scan(tmp_path / "a", tmp_path / "b")
    assert {"failures-ignored", "coverage-gate-lowered"} <= rules


def test_expected_value_change_and_swallowed_error(tmp_path):
    write(tmp_path / "a", "tests/test_m.py", BASE_TEST)
    changed = BASE_TEST.replace("f(2) == 4", "f(2) == 5").replace(
        "    with pytest.raises(ValueError):\n        f(-1)", "    try:\n        f(-1)\n    except Exception:\n        pass")
    write(tmp_path / "b", "tests/test_m.py", changed)
    _, rules, _ = scan(tmp_path / "a", tmp_path / "b")
    assert {"expected-value-changed", "swallowed-error"} <= rules


def test_git_mode(tmp_path):
    g = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    g("init", "-q")
    g("config", "user.email", "t@example.com")
    g("config", "user.name", "t")
    write(tmp_path, "test_m.py", BASE_TEST)
    g("add", ".")
    g("commit", "-qm", "base")
    write(tmp_path, "test_m.py", BASE_TEST.replace("def test_exact", "@pytest.mark.skip\ndef test_exact"))
    r = run_script("test_integrity_scan.py", "--repo", str(tmp_path))
    assert r.returncode == 1 and "skipped-test" in r.stdout


# ---- regression tests from the independent pre-release audit ----

def git_repo(tmp_path):
    g = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    g("init", "-q", "-b", "main")
    g("config", "user.email", "t@example.com")
    g("config", "user.name", "t")
    return g


def test_missing_folders_are_an_error_not_clean(tmp_path):
    r = run_script("test_integrity_scan.py", "--before", str(tmp_path / "nope1"), "--after", str(tmp_path / "nope2"))
    assert r.returncode == 2 and "not a folder" in r.stderr


def test_not_a_git_repo_is_an_error(tmp_path):
    r = run_script("test_integrity_scan.py", "--repo", str(tmp_path))
    assert r.returncode == 2 and r.stdout == ""


def test_base_uses_merge_base_not_tip(tmp_path):
    g = git_repo(tmp_path)
    write(tmp_path, "app.py", "x = 1\n")
    g("add", ".")
    g("commit", "-qm", "base")
    g("checkout", "-qb", "feature")
    write(tmp_path, "app.py", "x = 2\n")
    g("commit", "-qam", "feature work")
    g("checkout", "-q", "main")
    write(tmp_path, "tests/test_main.py", "def test_new():\n    assert 1 == 1\n")
    g("add", ".")
    g("commit", "-qm", "main moves on")
    g("checkout", "-q", "feature")
    r = run_script("test_integrity_scan.py", "--repo", str(tmp_path), "--base", "main")
    assert r.returncode == 0 and "deleted-test" not in r.stdout, r.stdout


def test_untracked_test_files_are_scanned(tmp_path):
    g = git_repo(tmp_path)
    write(tmp_path, "app.py", "x = 1\n")
    g("add", ".")
    g("commit", "-qm", "base")
    write(tmp_path, "tests/test_new.py", "import pytest\n\n@pytest.mark.skip\ndef test_a():\n    assert 1 == 1\n")
    r = run_script("test_integrity_scan.py", "--repo", str(tmp_path))
    assert r.returncode == 1 and "skipped-test" in r.stdout


def test_ref_injection_rejected(tmp_path):
    g = git_repo(tmp_path)
    write(tmp_path, "a.py", "x = 1\n")
    g("add", ".")
    g("commit", "-qm", "base")
    r = run_script("test_integrity_scan.py", "--repo", str(tmp_path), "--base=--output=INJECTED.txt")
    assert r.returncode == 2 and not (tmp_path / "INJECTED.txt").exists()


def test_honest_code_is_not_flagged_as_skip_or_gate(tmp_path):
    honest = ("import sys\nimport pytest\n\n"
              "@pytest.mark.skipif(sys.platform == 'win32', reason='posix only')\n"
              "def test_status():\n    order = make()\n    assert order.status == 'pending'\n"
              "    model.fit(X, y)\n    lines = read(path, 3)\n    threshold = 0.5\n")
    write(tmp_path / "a", "tests/test_m.py", "import pytest\n\ndef test_status():\n    lines = read(path, 5)\n    threshold = 0.9\n")
    write(tmp_path / "b", "tests/test_m.py", honest)
    code, rules, findings = scan(tmp_path / "a", tmp_path / "b")
    assert code == 0, findings
    assert not ({"skipped-test", "coverage-gate-lowered"} & rules)


def test_weakening_in_later_hunk_is_found(tmp_path):
    base = "def test_a():\n    assert f(2) == 4\n" + "".join(f"\ndef test_x{i}():\n    assert g({i}) == {i}\n" for i in range(20))
    base += "\ndef test_money():\n    assert total() == 236\n"
    new = base.replace("def test_a():\n", "def test_a():\n" + "    x = 1\n" * 15)
    new = new.replace("assert total() == 236", "assert total() == pytest.approx(236)")
    write(tmp_path / "a", "tests/test_m.py", base)
    write(tmp_path / "b", "tests/test_m.py", new)
    _, rules, _ = scan(tmp_path / "a", tmp_path / "b")
    assert "weakened-assertion" in rules


def test_removed_coverage_gate(tmp_path):
    write(tmp_path / "a", "pyproject.toml", "[tool.coverage.report]\nfail_under = 90\n")
    write(tmp_path / "b", "pyproject.toml", "[tool.coverage.report]\n")
    _, rules, _ = scan(tmp_path / "a", tmp_path / "b")
    assert "coverage-gate-removed" in rules


def test_non_utf8_file_does_not_crash(tmp_path):
    (tmp_path / "a" / "tests").mkdir(parents=True)
    (tmp_path / "b" / "tests").mkdir(parents=True)
    (tmp_path / "a" / "tests" / "test_l.py").write_bytes(b"# caf\xe9\ndef test_a():\n    assert 1 == 1\n")
    (tmp_path / "b" / "tests" / "test_l.py").write_bytes(b"# caf\xe9\n")
    r = run_script("test_integrity_scan.py", "--before", str(tmp_path / "a"), "--after", str(tmp_path / "b"))
    assert r.returncode == 1 and "deleted-test" in r.stdout and "Traceback" not in r.stderr


def test_ruby_csharp_kotlin_deletions(tmp_path):
    write(tmp_path / "a", "spec/m_spec.rb", 'describe "M" do\n  it "adds" do\n    expect(add(1, 2)).to eq(3)\n  end\nend\n')
    write(tmp_path / "b", "spec/m_spec.rb", 'describe "M" do\nend\n')
    write(tmp_path / "a", "tests/MTests.cs", "[Fact]\npublic async Task Adds()\n{\n    Assert.Equal(3, Add(1, 2));\n}\n")
    write(tmp_path / "b", "tests/MTests.cs", "\n")
    write(tmp_path / "a", "src/test/MTest.kt", "@Test\nfun `adds numbers`() {\n    assertEquals(3, add(1, 2))\n}\n")
    write(tmp_path / "b", "src/test/MTest.kt", "\n")
    _, _, findings = scan(tmp_path / "a", tmp_path / "b")
    flagged = {f["file"] for f in findings if f["rule"] == "deleted-test"}
    assert flagged == {"spec/m_spec.rb", "tests/MTests.cs", "src/test/MTest.kt"}, findings


def test_rust_helper_removal_is_not_a_deleted_test(tmp_path):
    write(tmp_path / "a", "tests/core_test.rs", "fn helper() -> u32 {\n    3\n}\n\n#[test]\nfn test_adds() {\n    assert_eq!(helper(), 3);\n}\n")
    write(tmp_path / "b", "tests/core_test.rs", "#[test]\nfn test_adds() {\n    assert_eq!(3, 3);\n}\n")
    _, rules, _ = scan(tmp_path / "a", tmp_path / "b")
    assert "deleted-test" not in rules


def test_rename_is_medium_not_high(tmp_path):
    write(tmp_path / "a", "tests/test_m.py", "def test_old_name():\n    assert f(2) == 4\n")
    write(tmp_path / "b", "tests/test_m.py", "def test_new_name():\n    assert f(2) == 4\n")
    code, rules, _ = scan(tmp_path / "a", tmp_path / "b")
    assert code == 0 and "test-removed-or-renamed" in rules
