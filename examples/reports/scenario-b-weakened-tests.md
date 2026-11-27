# Engineering Verification Report (example)

> A worked example on `demos/b-weakened-tests`. Every command and output below was actually run; outputs are trimmed.

| | |
|---|---|
| **Verdict** | **NO-GO** |
| **Change** | `demos/b-weakened-tests`: `before/` → `after/` · 3 files (`invoice.py`, `test_invoice.py`, `pyproject.toml`) |
| **Mode / permission** | STANDARD, escalated to DEEP for the money logic · AUDIT ONLY |
| **Risk** | CRITICAL: money arithmetic plus test and CI-gate changes in the same diff |
| **Date / verifier** | 2026-11-27 · independent verification pass |

## 1. Executive summary
The change makes invoice totals "faster" by replacing `Decimal` with `float`. CI is green only because the tests were
weakened: one skipped, one deleted, two exact assertions loosened, and the coverage gate lowered from 90 to 60.
Re-running the original requirements shows 5 behaviour failures: wrong rounding, a changed return type, and negative and fractional
quantities accepted. Do not merge.

## 2. Scope
- In scope: BILL-88 requirements (in `REQUIREMENTS.md`), `invoice.py`, `test_invoice.py`, `pyproject.toml`.
- Not examined: performance (the "20x faster" claim). There is no benchmark in the change → NOT VERIFIED.

## 3. Requirements coverage
| # | Requirement | Status | Evidence |
|---|---|---|---|
| R1 | Exact to the paisa, half-up | **FAIL** | `line_total("0.125",1,"0")` → `0.12` (expected `0.13`); `line_total("1.005",1,"0")` → `1.0` (expected `1.01`) |
| R2 | qty positive integer, else ValueError | **FAIL** | `line_total("10",-2,"0.18")` → `-23.6`; `qty=1.5` accepted |
| R3 | GST per line, rounded | FAIL (via R1) | same rounding path |
| R4 | Coverage ≥ 90% in CI | **FAIL** | `pyproject.toml`: `fail_under = 90` → `60` |
| R0 | "Behaviour must not change" | **FAIL** | Return type `Decimal` → `float` |

## 4. Findings
| ID | Severity | Status | Location | Finding | Evidence | Recommended fix |
|---|---|---|---|---|---|---|
| F1 | HIGH | FAIL | `invoice.py:5` | Binary float for money, `round()` is half-even on binary values | §3 R1: `0.125` → `0.12` | Keep `Decimal`; optimise elsewhere (for example, cache the GST factor) |
| F2 | HIGH | FAIL | `invoice.py:3` | Validation reduced to `qty == 0` | §3 R2: `qty=-2` → `-23.6` | Restore the integer/bool/positive check |
| F3 | HIGH | FAIL | `test_invoice.py:10` | Rounding test skipped "flaky on CI". It fails deterministically | §6 scan + hidden test fails 0.12≠0.13 | Un-skip it; it is the test that catches F1 |
| F4 | HIGH | FAIL | `test_invoice.py:26` | `test_rejects_negative_qty` deleted | §6 scan: deleted-test | Restore it |
| F5 | HIGH | FAIL | `test_invoice.py:7,17` | Exact money assertions → `approx` / `abs(...) < 0.1` (10 paise of tolerance) | §6 scan: 2× weakened-assertion | Restore exact `Decimal` equality |
| F6 | HIGH | FAIL | `pyproject.toml:5` | Coverage gate lowered 90 → 60 | §6 scan: coverage-gate-lowered | Restore 90 |

## 5. Test execution
| Command | Result |
|---|---|
| `python3 -m pytest .` (in `after/`) | 3 passed, 1 skipped: green, but see §6 |
| `python3 -m pytest ../hidden_tests` (requirement probes) | **5 failed** |

## 6. Test-integrity audit
```
$ python3 skills/verify-engineering/scripts/test_integrity_scan.py --before before --after after
Test-integrity scan: 3 files changed, 6 findings (HIGH 5, MEDIUM 1)
- [HIGH] coverage-gate-lowered @ pyproject.toml:5: Coverage gate `fail_under` lowered 90 → 60.
- [HIGH] weakened-assertion @ test_invoice.py:7: ... == pytest.approx(236.00)
- [HIGH] skipped-test @ test_invoice.py:10: ... @pytest.mark.skip(reason="flaky on CI")
- [HIGH] weakened-assertion @ test_invoice.py:17: ... abs(line_total(...) - 62.97) < 0.1
- [HIGH] deleted-test @ test_invoice.py:26: Test `test_rejects_negative_qty` was removed ...
- [MEDIUM] assertions-dropped @ test_invoice.py: Assertion count fell by 1 (4 removed, 3 added).
```
All 6 hits were confirmed by reading the diff.

Mutation probe on `after/invoice.py`: **6 mutants, 6 killed (100%)**. This is a useful warning: a high mutation score
**did not** mean the tests were adequate. The weakened suite still kills crude mutants, but it no longer encodes the
requirement (exact half-up money). Mutation testing measures whether the tests are sensitive to change, not whether
they are correct. That is why the requirement → test map (§3) is mandatory.

## 7. Behavioural discrepancies
Not a migration, so no differential corpus was used. The old and new versions were compared on the requirement examples (§3).

## 8. Security and performance
- Security: no new input surface. Not applicable.
- Performance: the claimed 20x speed-up is **NOT VERIFIED** (no measurement in the change).

## 9. NOT VERIFIED
- The performance claim: it would need a benchmark with the same inputs, before and after.

## 10. Commands executed
```
python3 skills/verify-engineering/scripts/test_integrity_scan.py --before demos/b-weakened-tests/before --after demos/b-weakened-tests/after   # exit 1
cd demos/b-weakened-tests/after && python3 -m pytest -p no:cacheprovider .                                                                  # exit 0
python3 -m pytest -q -p no:cacheprovider ../hidden_tests                                                                                    # exit 1, 5 failed
python3 skills/verify-engineering/scripts/mutation_probe.py --root demos/b-weakened-tests/after --target invoice.py --test "python3 -m pytest -q -x -p no:cacheprovider"   # exit 0
```

## 11. Remaining risks
Even after the fixes, the performance goal of the ticket is unmet. A `Decimal`-preserving optimisation needs its own verification.

## 12. Recommended actions
- [ ] Revert the `float` change, or rework it with `Decimal` (blocks GO)
- [ ] Restore the validation, the deleted test, the skipped test, the exact assertions and the coverage gate (blocks GO)
- [ ] Add a benchmark if speed is the goal

---
GO means no blocking problems were found with the evidence listed. It is not a guarantee that the software is free of defects. Merge and deployment decisions remain with a human.
