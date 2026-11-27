import sys

from conftest import run_script

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


# ---- regression tests from the independent pre-release audit ----
import os


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
