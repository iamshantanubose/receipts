# Changelog

## 1.0.1 (2026-11-27)
- Repository renamed to `receipts`. The skill is still `verify-engineering`; the Claude Code marketplace is now `receipts`
  (`/plugin install verify-engineering@receipts`).
- `test_integrity_scan.py`: now flags exact assertions replaced by a bare truthy `assert x`, `is not None` or an ordering
  comparison (`> 0`); `pass` added under an unchanged `except` line; and Rust `let _ =`. Unknown refs give a clear error.
- `mutation_probe.py`: Python `//` is treated as floor division, not as a comment, so those lines are mutated again. A run with
  zero mutation points exits 2 instead of reporting a pass. `--max` and `--timeout` must be positive; non-UTF-8 targets and
  shell operators in `--test` give clean errors. The default budget is 30 mutants, matching the docs.
- `diff_harness.py`: mismatches are grouped by the shape of the difference rather than by literal values, so one root cause
  forms one group. A missing inputs file, shell operators and invalid numeric options are reported without a traceback.
- Scenario C: the legacy reference pins the 4,300-digit `int()` limit, so the control matches on every Python version.
- Benchmark: exact prompts published in `benchmark/prompts/`; results reported for three approaches with a plain statement that
  the single author-scored run showed no measurable detection advantage.
- Verdict rules aligned between `SKILL.md` and the references; new guardrail for running untrusted contributors' code.
- Release zip renamed to `receipts-verify-engineering-<version>.zip`, built by `tools/build_release.py`, and now includes LICENSE.
- Test suite: 70 tests.

## 1.0.0 (2026-11-27)
- First release of the `verify-engineering` skill: 7-stage verification workflow, QUICK / STANDARD / DEEP modes, AUDIT ONLY (default) and FIX AND VERIFY permissions.
- Scripts (Python standard library only): `test_integrity_scan.py`, `diff_harness.py`, `mutation_probe.py`.
- 5 deliberately flawed demo scenarios, each with a correct version, including a Python → Rust migration.
- Automated test suite (53 tests) and a reproducible benchmark.
