import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "verify-engineering")
SCRIPTS = os.path.join(SKILL, "scripts")
DEMOS = os.path.join(ROOT, "demos")


def run_script(name, *args, cwd=None):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          capture_output=True, text=True, cwd=cwd)
