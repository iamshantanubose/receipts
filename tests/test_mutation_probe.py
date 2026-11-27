import importlib.util
import os
import sys

from conftest import SCRIPTS, run_script

CODE = "def grade(score):\n    if score >= 50:\n        return 'pass'\n    return 'fail'\n"
WEAK = "from m import grade\n\ndef test_pass():\n    assert grade(90) == 'pass'\n"
STRONG = WEAK + "\ndef test_boundary():\n    assert grade(50) == 'pass'\n    assert grade(49) == 'fail'\n"
CMD = f"{sys.executable} -m pytest -q -x -p no:cacheprovider"


def setup(tmp_path, tests):
    (tmp_path / "m.py").write_text(CODE)
    (tmp_path / "test_m.py").write_text(tests)


def test_weak_tests_leave_survivors_and_tree_untouched(tmp_path):
    setup(tmp_path, WEAK)
    r = run_script("mutation_probe.py", "--root", str(tmp_path), "--target", "m.py", "--test", CMD)
    assert r.returncode == 1 and "SURVIVED" in r.stdout and ">= → >" in r.stdout
    assert (tmp_path / "m.py").read_text() == CODE  # the user's tree is never modified


def test_strong_tests_kill_everything(tmp_path):
    setup(tmp_path, STRONG)
    r = run_script("mutation_probe.py", "--root", str(tmp_path), "--target", "m.py", "--test", CMD)
    assert r.returncode == 0, r.stdout


def test_failing_baseline_is_reported_not_scored(tmp_path):
    setup(tmp_path, WEAK.replace("'pass'", "'nope'"))
    r = run_script("mutation_probe.py", "--root", str(tmp_path), "--target", "m.py", "--test", CMD)
    assert r.returncode == 2 and "BEFORE any mutation" in r.stderr


# ---- safety and error-path regressions ----


def test_absolute_target_is_refused_and_real_file_untouched(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    (real / "m.py").write_text(CODE)
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "test_m.py").write_text(WEAK)
    r = run_script("mutation_probe.py", "--root", str(proj), "--target", str(real / "m.py"), "--test", CMD)
    assert r.returncode == 2 and (real / "m.py").read_text() == CODE


def test_symlinked_target_is_refused(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    (real / "m.py").write_text(CODE)
    proj = tmp_path / "proj"
    proj.mkdir()
    os.symlink(real / "m.py", proj / "m.py")
    (proj / "test_m.py").write_text(WEAK)
    r = run_script("mutation_probe.py", "--root", str(proj), "--target", "m.py", "--test", CMD)
    assert r.returncode == 2 and "symlink" in r.stderr and (real / "m.py").read_text() == CODE


def test_dotdot_and_missing_targets_are_errors(tmp_path):
    setup(tmp_path, WEAK)
    for t in ("../m.py", "nope.py"):
        r = run_script("mutation_probe.py", "--root", str(tmp_path), "--target", t, "--test", CMD)
        assert r.returncode == 2 and "Traceback" not in r.stderr


def test_docstrings_and_generics_are_not_mutated(tmp_path):
    code = ('def grade(score):\n    """Values below 0 or above 100 and <= weird are rejected."""\n'
            '    kinds = "List<int>"\n    if score >= 50:\n        return "pass"\n    return "fail"\n')
    (tmp_path / "m.py").write_text(code)
    (tmp_path / "test_m.py").write_text(STRONG)
    r = run_script("mutation_probe.py", "--root", str(tmp_path), "--target", "m.py", "--test", CMD)
    assert "SURVIVED m.py:2" not in r.stdout and r.returncode == 0, r.stdout


def test_unrunnable_test_command_is_error(tmp_path):
    setup(tmp_path, WEAK)
    r = run_script("mutation_probe.py", "--root", str(tmp_path), "--target", "m.py", "--test", "/no/such/python -m pytest")
    assert r.returncode == 2 and "Traceback" not in r.stderr


def test_python_floor_division_is_mutated_not_treated_as_comment(tmp_path):
    (tmp_path / "m.py").write_text("def half(x):\n    return x // 2 + 1\n")
    (tmp_path / "test_m.py").write_text("from m import half\n\ndef test_half():\n    assert half(4) == 3\n")
    r = run_script("mutation_probe.py", "--root", str(tmp_path), "--target", "m.py", "--test", CMD)
    assert r.returncode in (0, 1) and "Mutation probe: 2 mutants" in r.stdout, r.stdout + r.stderr


def test_comment_syntax_follows_the_language():
    spec = importlib.util.spec_from_file_location("mutation_probe", os.path.join(SCRIPTS, "mutation_probe.py"))
    mp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mp)
    js = mp.candidates(["const ok = a > b; // x < y"], hash_comments=False)
    assert [c[4] for c in js] == ["> → >="]
    py = mp.candidates(["y = a // b  # a < b"], hash_comments=True)
    assert py == []  # `//` is an operator here, and the comment is skipped; no mutator matches `//`
    py = mp.candidates(["y = a // b + 1  # a < b"], hash_comments=True)
    assert {c[4] for c in py} == {"+ → -", "1 → 0"}


def test_zero_mutants_is_an_error_not_a_pass(tmp_path):
    (tmp_path / "m.py").write_text('GREETING = "hello"\n')
    (tmp_path / "test_m.py").write_text("def test_ok():\n    assert True\n")
    r = run_script("mutation_probe.py", "--root", str(tmp_path), "--target", "m.py", "--test", CMD)
    assert r.returncode == 2 and "no mutation points" in r.stderr


def test_max_must_be_positive(tmp_path):
    setup(tmp_path, WEAK)
    for v in ("0", "-3"):
        r = run_script("mutation_probe.py", "--root", str(tmp_path), "--target", "m.py", "--test", CMD, "--max", v)
        assert r.returncode == 2 and "positive integer" in r.stderr


def test_non_utf8_target_is_a_clean_error(tmp_path):
    (tmp_path / "m.py").write_bytes(b"\xff\xfe x = 1 + 2\n")
    r = run_script("mutation_probe.py", "--root", str(tmp_path), "--target", "m.py", "--test", CMD)
    assert r.returncode == 2 and "not UTF-8" in r.stderr and "Traceback" not in r.stderr


def test_shell_operators_are_refused(tmp_path):
    setup(tmp_path, WEAK)
    r = run_script("mutation_probe.py", "--root", str(tmp_path), "--target", "m.py", "--test", f"cd . && {CMD}")
    assert r.returncode == 2 and "without a shell" in r.stderr
