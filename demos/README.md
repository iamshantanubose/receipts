# Demo scenarios

Five deliberately flawed changes, each with a correct version to measure false alarms. In every flawed scenario
**the project's own tests pass**. That is the trap.

| Folder | Scenario | The change under review | Correct version (negative control) |
|---|---|---|---|
| `a-business-rule` | A: passes unit tests, breaks business rules | `after/` | `control/` |
| `b-weakened-tests` | B: agent weakened tests to get green | `after/` vs `before/` | `before/` |
| `c-python-to-rust` | C: migration with subtle behaviour differences | `rust_port/` vs `legacy_python/` | `control_rust/` |
| `d-refactor-security` | D: "pure refactor" loses atomicity + adds path traversal | `after/` vs `before/` | `before/` |
| `e-edge-cases` | E: fine for nice inputs, wrong at the edges | `after/` | `control/` |

Each folder has `REQUIREMENTS.md` (the ticket), the code, its existing tests, `ANSWER_KEY.md` (the hidden defects and expected
findings: **don't show this to the verifier**) and `hidden_tests/` (ground truth). Actual findings from real runs are
in `../benchmark/results/`, and a full example report is in `../examples/reports/`.

## Try it yourself (about 2 minutes)
From the repository root, with pytest installed:
```bash
cd demos/a-business-rule/after
python3 -m pytest -q                   # 4 passed: looks done
python3 -m pytest -q ../hidden_tests   # 4 failed: it isn't
```
Then, in your agent: `/verify-engineering` on that folder. Or, for the migration demo (needs cargo), again from the repository root:
```bash
cd demos/c-python-to-rust
(cd rust_port && cargo build --release -q)
python3 ../../skills/verify-engineering/scripts/diff_harness.py \
  --old "python3 legacy_python/normalize.py" --new rust_port/target/release/normalize \
  --inputs inputs/synthetic_traffic.tsv
# 600 records compared, 272 mismatched, in 13 groups (by the shape of the difference)
```

## Before / after
| Scenario | Project's tests | Hidden requirement tests on flawed build | On correct version |
|---|---|---|---|
| A | 4 passed | 4 failed | all passed |
| B | 3 passed, 1 skipped | 5 failed | all passed |
| C | 10/10 conventional match | 54.7% match on 600 records | 100% match (+ 5,000 fuzz) |
| D | 6 passed | 4 failed | all passed |
| E | 4 passed | 6 failed | all passed |

These numbers are checked automatically by `tests/test_demo_ground_truth.py`.
