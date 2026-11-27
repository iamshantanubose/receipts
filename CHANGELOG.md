# Changelog

## 1.0.0 (2026-11-27)
- First release of the `verify-engineering` skill: 7-stage verification workflow, QUICK / STANDARD / DEEP modes, AUDIT ONLY (default) and FIX AND VERIFY permissions.
- Scripts (Python standard library only): `test_integrity_scan.py`, `diff_harness.py`, `mutation_probe.py`.
- 5 deliberately flawed demo scenarios plus 3 correct controls, including a Python → Rust migration.
- Automated test suite (53 tests) and a reproducible benchmark.
- Hardened after an independent pre-release audit: the mutation probe can no longer touch files outside its temp copy; the scanner diffs from the merge-base, includes untracked files, validates refs and paths, has fewer false positives, and detects removed coverage gates; the differential harness compares bytes and reports empty corpora and run-level problems correctly.
