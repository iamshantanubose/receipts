import json
import os
import sys

from conftest import run_script

PY = sys.executable


def prog(tmp_path, name, body):
    p = tmp_path / name
    p.write_text("import sys\nfor line in sys.stdin:\n    line = line.rstrip('\\n')\n" + body)
    return f"{PY} {p}"


def test_identical_programs_match(tmp_path):
    a = prog(tmp_path, "a.py", "    print('OK n=' + str(len(line)))\n")
    inp = tmp_path / "in.txt"
    inp.write_text("x\nhello\n\n")
    r = run_script("diff_harness.py", "--old", a, "--new", a, "--inputs", str(inp))
    assert r.returncode == 0 and "100.0%" in r.stdout


def test_mismatches_grouped_by_fingerprint(tmp_path):
    old = prog(tmp_path, "old.py", "    print('OK n=' + str(len(line)))\n")
    new = prog(tmp_path, "new.py", "    print('OK n=' + str(len(line.encode())))\n")  # bytes, not chars
    inp = tmp_path / "in.txt"
    inp.write_text("abc\ncafé\nनमस्ते\nplain\n", encoding="utf-8")
    rep = tmp_path / "r.json"
    r = run_script("diff_harness.py", "--old", old, "--new", new, "--inputs", str(inp), "--report", str(rep))
    assert r.returncode == 1
    data = json.loads(rep.read_text())
    assert data["compared"] == 4 and data["mismatches"] == 2
    assert list(data["groups"]) == ["fields differ: n"]


def test_json_mode_reports_paths(tmp_path):
    old = prog(tmp_path, "o.py", "    import json; print(json.dumps({'a': 1, 'b': [1, 2]}))\n")
    new = prog(tmp_path, "n.py", "    import json; print(json.dumps({'a': '1', 'b': [1, 2], 'c': 0}))\n")
    inp = tmp_path / "in.txt"
    inp.write_text("{}\n")
    r = run_script("diff_harness.py", "--old", old, "--new", new, "--inputs", str(inp), "--mode", "json")
    assert r.returncode == 1 and ".a: type int → str" in r.stdout and ".c: added" in r.stdout


def test_missing_command_is_harness_error(tmp_path):
    inp = tmp_path / "in.txt"
    inp.write_text("x\n")
    r = run_script("diff_harness.py", "--old", "definitely-not-a-command-xyz", "--new", "true", "--inputs", str(inp))
    assert r.returncode == 2


# ---- regression tests from the independent pre-release audit ----

def test_empty_corpus_is_an_error(tmp_path):
    inp = tmp_path / "in.txt"
    inp.write_text("")
    for mode in ("lines", "each"):
        r = run_script("diff_harness.py", "--old", "cat", "--new", "cat", "--inputs", str(inp), "--mode", mode)
        assert r.returncode == 2


def test_binary_outputs_compared_as_bytes(tmp_path):
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    a.write_text("import sys\nsys.stdin.read()\nsys.stdout.buffer.write(b'\\xff\\n')\n")
    b.write_text("import sys\nsys.stdin.read()\nsys.stdout.buffer.write(b'\\xfe\\n')\n")
    inp = tmp_path / "in.txt"
    inp.write_text("x\n")
    r = run_script("diff_harness.py", "--old", f"{PY} {a}", "--new", f"{PY} {b}", "--inputs", str(inp))
    assert r.returncode == 1 and "0.0%" in r.stdout


def test_extra_output_line_is_run_level_not_negative_rate(tmp_path):
    old = prog(tmp_path, "o.py", "    print(line)\n")
    new = prog(tmp_path, "n.py", "    print(line)\nprint('extra')\n")
    inp = tmp_path / "in.txt"
    inp.write_text("a\nb\n")
    r = run_script("diff_harness.py", "--old", old, "--new", new, "--inputs", str(inp))
    assert r.returncode == 1 and "Match rate: 100.0%" in r.stdout and "RUN-LEVEL" in r.stdout and "-" not in r.stdout.split("Match rate: ")[1][:2]


def test_non_executable_command_is_harness_error(tmp_path):
    f = tmp_path / "notexec.sh"
    f.write_text("echo hi\n")
    inp = tmp_path / "in.txt"
    inp.write_text("x\n")
    r = run_script("diff_harness.py", "--old", str(f), "--new", str(f), "--inputs", str(inp))
    assert r.returncode == 2 and "Traceback" not in r.stderr
