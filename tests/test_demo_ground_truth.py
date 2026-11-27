"""Each demo's planted defects are real: hidden tests fail on the flawed build and pass on the control."""
import os
import shutil
import subprocess
import sys

import pytest

from conftest import DEMOS

PY_DEMOS = [("a-business-rule", "after", "control"), ("b-weakened-tests", "after", "before"),
            ("d-refactor-security", "after", "before"), ("e-edge-cases", "after", "control")]


def pytest_in(folder, *extra):
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", ".", *extra],
                          cwd=folder, capture_output=True, text=True)


@pytest.mark.parametrize("demo,flawed,control", PY_DEMOS)
def test_visible_tests_pass_on_flawed_build(demo, flawed, control):
    r = pytest_in(os.path.join(DEMOS, demo, flawed))
    assert r.returncode == 0, r.stdout  # the trap: CI is green


@pytest.mark.parametrize("demo,flawed,control", PY_DEMOS)
def test_hidden_tests_fail_on_flawed_build(demo, flawed, control):
    r = pytest_in(os.path.join(DEMOS, demo, flawed), "../hidden_tests")
    assert r.returncode == 1, r.stdout


@pytest.mark.parametrize("demo,flawed,control", PY_DEMOS)
def test_hidden_tests_pass_on_control(demo, flawed, control):
    r = pytest_in(os.path.join(DEMOS, demo, control), "../hidden_tests")
    assert r.returncode == 0, r.stdout


@pytest.mark.skipif(shutil.which("cargo") is None or shutil.which("bash") is None,
                    reason="needs the Rust toolchain and bash")
def test_rust_migration_differential_ground_truth():
    r = subprocess.run(["bash", os.path.join(DEMOS, "c-python-to-rust", "hidden_tests", "check.sh")],
                       capture_output=True, text=True, env=dict(os.environ, PYTHON=sys.executable))
    assert r.returncode == 0, r.stdout + r.stderr
