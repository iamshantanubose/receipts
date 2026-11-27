#!/usr/bin/env python3
"""Differential (shadow) test harness: run OLD and NEW on identical inputs, compare, group mismatches.

Standard library only. It runs exactly the two commands you give it, locally, without a shell,
feeding the inputs on stdin. It adds no network access of its own, but those commands can do anything
your user account can, so only compare programs you are willing to run.

Mismatches are grouped by the *shape* of the difference, not by literal values: which `key=value`
fields differ, or which positions differ and how (a category word such as an error code is kept,
numbers become <num>, other text becomes <text>). One root cause therefore tends to form one group.
This works best when outputs are `key=value` tokens, tab/space-separated fields, or JSON.

Pipes, `&&`, `;` and redirects are refused: wrap a pipeline in a script and pass the script.

Modes:
  lines  : feed the whole input file to each command once; compare output line N to line N.
  each   : run each command once per input record (one line = one record); compare full stdout.
  json   : like `each`, but parse stdout as JSON and diff structurally (key paths).

Examples:
  diff_harness.py --old "python3 legacy.py" --new "./target/release/port" --inputs corpus.tsv
  diff_harness.py --old "node old.js" --new "node new.js" --inputs reqs.jsonl --mode json
Exit code: 0 = no mismatches, 1 = mismatches found, 2 = harness error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from collections import OrderedDict


SHELL_OPS = {"|", "||", "&", "&&", ";", ">", ">>", "<", "2>", "2>&1", "&>"}
CATEGORY = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]{0,39}")


def split_cmd(cmd: str) -> list[str]:
    """Split a command line into argv. Raises ValueError for shell syntax, which is not supported."""
    argv = shlex.split(cmd, posix=(os.name != "nt"))
    ops = [t for t in argv if t in SHELL_OPS]
    if ops:
        raise ValueError(f"shell operator {ops[0]!r} in {cmd!r}: commands run without a shell. "
                         "Put the pipeline in a script and pass the script instead.")
    if not argv:
        raise ValueError("empty command")
    return argv


def run(cmd: str, data: bytes, timeout: float) -> tuple[int, bytes, str]:
    """Returns (exit code, stdout bytes, stderr text). Outputs are compared as BYTES; text is only for display."""
    p = subprocess.run(split_cmd(cmd), input=data, capture_output=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr.decode("utf-8", "replace")


def show(b: bytes) -> str:
    """Bytes for display: invalid UTF-8 is shown as backslash escapes."""
    return b.decode("utf-8", "backslashreplace")


def tokens(s: str) -> OrderedDict:
    """Split an output line into a key->value view. key=value pairs keep their key; others use position."""
    out = OrderedDict()
    for i, tok in enumerate(s.replace("\t", " ").split()):
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
        else:
            out[f"#{i}"] = tok
    return out


def shape(v: str | None) -> str:
    """Collapse a value to its kind: ∅ (missing), <num>, a short category word (kept), or <text>."""
    if v is None or v == "":
        return "∅"
    try:
        float(v)
        return "<num>"
    except ValueError:
        pass
    return v if CATEGORY.fullmatch(v) else "<text>"


def line_fingerprint(old: str, new: str) -> str:
    """Group key for one mismatching output line. Literal numbers and free text never split groups."""
    a, b = tokens(old), tokens(new)
    keys = [k for k in OrderedDict.fromkeys(list(a) + list(b)) if a.get(k) != b.get(k)]
    head_a, head_b = shape(a.get("#0")), shape(b.get("#0"))
    if a.get("#0") != b.get("#0") and head_a != head_b:  # different outcome class (e.g. OK vs ERR)
        detail = f" ({shape(a.get('#1'))} → {shape(b.get('#1'))})" if ("#1" in a or "#1" in b) else ""
        return f"outcome {head_a} → {head_b}{detail}"
    named = [k for k in keys if not k.startswith("#")]
    if named:
        return "fields differ: " + ", ".join(named)
    return "values differ: " + ", ".join(f"{k}: {shape(a.get(k))} → {shape(b.get(k))}" for k in keys)


def json_paths(a, b, prefix: str = "") -> list[str]:
    """Structural differences between two JSON values as key paths (list indexes collapse to [])."""
    if type(a) is not type(b):
        return [f"{prefix or '$'}: type {type(a).__name__} → {type(b).__name__}"]
    if isinstance(a, dict):
        paths = []
        for k in sorted(set(a) | set(b)):
            p = f"{prefix}.{k}"
            if k not in a:
                paths.append(f"{p}: added")
            elif k not in b:
                paths.append(f"{p}: removed")
            else:
                paths += json_paths(a[k], b[k], p)
        return paths
    if isinstance(a, list):
        if len(a) != len(b):
            return [f"{prefix or '$'}: length {len(a)} → {len(b)}"]
        paths = []
        for i, (x, y) in enumerate(zip(a, b)):
            paths += json_paths(x, y, f"{prefix}[]")
        return paths
    return [] if a == b else [f"{prefix or '$'}: value"]


def non_negative_int(v: str) -> int:
    n = int(v)
    if n < 0:
        raise argparse.ArgumentTypeError(f"must be 0 or more, got {v}")
    return n


def positive_float(v: str) -> float:
    x = float(v)
    if x <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive number, got {v}")
    return x


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", required=True, help="command for the reference (trusted) implementation")
    ap.add_argument("--new", required=True, help="command for the implementation under test")
    ap.add_argument("--inputs", required=True, help="input file, one record per line")
    ap.add_argument("--mode", choices=["lines", "each", "json"], default="lines")
    ap.add_argument("--timeout", type=positive_float, default=30.0, help="seconds per command run")
    ap.add_argument("--max-examples", type=non_negative_int, default=3, help="examples kept per mismatch group")
    ap.add_argument("--report", help="write a JSON report here")
    args = ap.parse_args()

    for name in ("old", "new"):
        try:
            split_cmd(getattr(args, name))
        except ValueError as e:
            print(f"HARNESS ERROR: --{name}: {e}", file=sys.stderr)
            return 2
    try:
        with open(args.inputs, "rb") as f:
            raw = f.read()
    except OSError as e:
        print(f"HARNESS ERROR: cannot read --inputs {args.inputs!r}: {e.strerror}", file=sys.stderr)
        return 2
    records = raw.split(b"\n")
    if records and records[-1] == b"":
        records.pop()

    if not records:
        print("HARNESS ERROR: the input file has no records; nothing was compared.", file=sys.stderr)
        return 2

    groups = OrderedDict()    # per-record mismatches
    structural = OrderedDict()  # whole-run problems (exit code, line count)
    compared = 0

    def add(fp, rec, o, n, target=groups):
        g = target.setdefault(fp, {"count": 0, "examples": []})
        g["count"] += 1
        if len(g["examples"]) < args.max_examples:
            g["examples"].append({"input": rec, "old": o, "new": n})

    try:
        if args.mode == "lines":
            rc_o, out_o, err_o = run(args.old, raw, args.timeout)
            rc_n, out_n, err_n = run(args.new, raw, args.timeout)
            if rc_o != rc_n:
                add(f"exit code {rc_o} → {rc_n}", "<whole file>", err_o[-300:], err_n[-300:], structural)
            lo, ln = out_o.split(b"\n"), out_n.split(b"\n")
            for lst in (lo, ln):
                if lst and lst[-1] == b"":
                    lst.pop()
            if len(lo) != len(ln) or len(lo) != len(records):
                add(f"output line count old={len(lo)} new={len(ln)} for {len(records)} input records",
                    "<whole file>", "", "", structural)
            for i, rec in enumerate(records):
                compared += 1
                o = lo[i] if i < len(lo) else b"<missing>"
                n = ln[i] if i < len(ln) else b"<missing>"
                if o != n:
                    add(line_fingerprint(show(o), show(n)), show(rec), show(o), show(n))
        else:
            for rec in records:
                compared += 1
                rc_o, o, _ = run(args.old, rec + b"\n", args.timeout)
                rc_n, n, _ = run(args.new, rec + b"\n", args.timeout)
                text = show(rec)
                if rc_o != rc_n:
                    add(f"exit code {rc_o} → {rc_n}", text, show(o).strip(), show(n).strip())
                    continue
                if args.mode == "json":
                    try:
                        diffs = json_paths(json.loads(o), json.loads(n))
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        add(f"unparseable JSON ({type(e).__name__})", text, show(o).strip(), show(n).strip())
                        continue
                    if diffs:
                        add("; ".join(sorted(set(diffs))), text, show(o).strip(), show(n).strip())
                elif o != n:
                    add(line_fingerprint(show(o).strip(), show(n).strip()), text, show(o).strip(), show(n).strip())
    except subprocess.TimeoutExpired as e:
        print(f"HARNESS ERROR: timeout running {e.cmd}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as e:
        print(f"HARNESS ERROR: could not run a command: {e}", file=sys.stderr)
        return 2

    mismatched = sum(g["count"] for g in groups.values())
    print(f"Differential test: {compared} records compared, {mismatched} mismatched records, "
          f"{len(groups)} distinct group{'' if len(groups) == 1 else 's'}")
    print(f"Match rate: {100 * (compared - mismatched) / compared:.1f}%")
    for fp, g in structural.items():
        print(f"\n[RUN-LEVEL] {fp}")
        for ex in g["examples"]:
            if ex["old"] or ex["new"]:
                print(f"     old: {ex['old']!r}\n     new: {ex['new']!r}")
    for fp, g in sorted(groups.items(), key=lambda kv: -kv[1]["count"]):
        print(f"\n[{g['count']}x] {fp}")
        for ex in g["examples"]:
            print(f"   input: {ex['input']!r}\n     old: {ex['old']!r}\n     new: {ex['new']!r}")
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump({"compared": compared, "mismatches": mismatched, "groups": groups, "run_level": structural},
                      f, indent=2, ensure_ascii=False)
    return 1 if (mismatched or structural) else 0


if __name__ == "__main__":
    sys.exit(main())
