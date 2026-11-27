# Benchmark: method

**Question:** does the `verify-engineering` skill find more real problems, with fewer false alarms, than simpler approaches?

**Short answer from the first run: not measurably.** See [`results/RESULTS.md`](results/RESULTS.md). This was one early,
author-scored run on small cases, and the skill showed no detection advantage. It is published so the method can be
repeated and improved, not as evidence that the skill is better.

## Approaches (same model, same tools, same cases, same output format)
| ID | Approach | Prompt |
|---|---|---|
| SELF | Self-review: "you implemented this commit; review your own work before handing off" | [`prompts/self-review.md`](prompts/self-review.md) |
| REVIEW | Generic code review: "act as a senior software engineer doing a thorough code review" | [`prompts/generic-review.md`](prompts/generic-review.md) |
| VERIFY | **verify-engineering** (this repo), read and followed, audit only | [`prompts/verify-engineering.md`](prompts/verify-engineering.md) |

- One model family, run as fresh agent sessions (no conversation history) with shell access. One agent reviewed one whole batch.
- Every agent got the **same answer format** ([`prompts/output-format.md`](prompts/output-format.md)), so the reports can be compared.
- Cases are **blinded**: `build_cases.py` builds each one as a small git repo (baseline commit + change commit). Cases contain no
  answer keys, no hidden tests, and no folder names that hint at a defect. Flawed changes and correct changes (negative controls)
  are in **separate** batches, reviewed by separate agents, so no agent could diff the two versions.
- Ground truth: each demo's `ANSWER_KEY.md` plus `hidden_tests/`. `tests/test_demo_ground_truth.py` checks that the planted
  defects are real (the hidden tests fail on the flawed build and pass on the control).
- The **scorer was not blinded**: the repo author scored every answer against the keys.

## Cases
| Case | Batch folder | Demo | Kind |
|---|---|---|---|
| F1 | `flawed/case-1` | d-refactor-security | flawed (atomicity loss + path traversal) |
| F2 | `flawed/case-2` | c-python-to-rust | flawed (Python → Rust port with 6 behaviour differences) |
| F3 | `flawed/case-3` | e-edge-cases | flawed (remainder loss, validation, rounding, precision) |
| F4 | `flawed/case-4` | b-weakened-tests | flawed (tests weakened, skipped and deleted; coverage gate lowered) |
| F5 | `flawed/case-5` | a-business-rule | flawed (3 broken business rules) |
| K1 | `controls/case-1` | e-edge-cases control | correct |
| K2 | `controls/case-2` | a-business-rule control | correct |
| K3 | `controls/case-3` | c-python-to-rust control | intended to be correct (the results show it was not, twice) |

## Reproduce
```bash
python3 benchmark/build_cases.py ~/verify-bench/run-1    # writes flawed/, controls/ and case-map.json
```
Then start one fresh agent session per approach and batch, give it the prompt from `prompts/` with the placeholders filled in,
and score its answer against `demos/*/ANSWER_KEY.md` using `case-map.json`. Never give `case-map.json` to an agent.

Scoring rubric: a planted defect counts as **found** if the root cause is identified. It counts as **proven** if the evidence given
is an executed input → wrong output that demonstrates it. A finding is **unsupported** when it is rated CRITICAL/HIGH but its own
evidence shows no wrong behaviour.
