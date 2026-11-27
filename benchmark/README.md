# Benchmark: method

**Question:** does the `verify-engineering` skill find more real problems, with fewer false alarms, than simpler approaches?

## Approaches (same model, same tools, same cases, same output format)
| ID | Approach | Prompt framing |
|---|---|---|
| A | Self-review | "You implemented this commit. Review your own work before handing off." |
| B | Generic code review | "Act as a senior engineer doing a thorough code review." |
| C | Existing verification skill | A popular open-source "verify before claiming completion" agent skill (MIT licensed), read and followed |
| D | **verify-engineering** (this repo) | The skill in `skills/verify-engineering/`, read and followed, AUDIT ONLY |

- Model: Claude Sonnet, run as independent subagents (fresh context, no conversation history), with shell access, inside Claude Code.
- Every agent got the **same 4-line output format** (case / verdict / findings with evidence), so the reports can be compared.
- Cases are **blinded**: built by `build_cases.py` as small git repos (baseline commit + change commit). They contain no answer keys, no hidden tests, and no folder names that hint at a defect. Flawed changes and correct changes (negative controls) went to **separate** agents, so no agent could diff the two versions.
- Ground truth: each demo's `ANSWER_KEY.md` plus `hidden_tests/`. `tests/test_demo_ground_truth.py` checks that the planted defects are real (the hidden tests fail on the flawed build and pass on the control).

## Cases
| Case | Demo | Kind |
|---|---|---|
| F1 | d-refactor-security | flawed (atomicity loss + path traversal) |
| F2 | c-python-to-rust | flawed (Python → Rust port with 6 behaviour differences) |
| F3 | e-edge-cases | flawed (remainder loss, validation, rounding, precision) |
| F4 | b-weakened-tests | flawed (tests weakened, skipped and deleted; coverage gate lowered) |
| F5 | a-business-rule | flawed (3 broken business rules) |
| K1 | e-edge-cases control | correct |
| K2 | a-business-rule control | correct |
| K3 | c-python-to-rust control | intended to be correct (see results: it was not, twice) |

## Reproduce
```bash
python3 benchmark/build_cases.py /tmp/verify-bench/run-1   # build blinded cases
# then give each approach's prompt + the case folder to a fresh agent session, and score against demos/*/ANSWER_KEY.md
```
Scoring rubric: a planted defect counts as **found** if the root cause is identified. It counts as **proven** if the evidence given is an executed input → wrong output that demonstrates it. A finding is **unsupported** when it is rated CRITICAL/HIGH but its own evidence shows no wrong behaviour.
