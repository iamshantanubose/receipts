# Benchmark results (run of 2026-11-27)

Verdicts and findings come from 12 actual agent runs (4 approaches × 3 batches), one fresh Sonnet subagent each. Nothing is estimated.
Scoring was done by the author of this repo against the answer keys, so read it with that in mind. `raw-findings.md` holds a condensed transcription of every run's final answer; verbatim text is in `raw/` for the runs that could save it (the sandbox blocked most agents from writing outside their case folder).

## 1. Flawed changes (F1–F5): 25 planted problems in total (A 3, B 6, C 7, D 4, E 5)

| | A Self-review | B Generic review | C Existing skill | D verify-engineering |
|---|---|---|---|---|
| Verdict correct (NO-GO) on all 5 | 5/5 | 5/5 | 5/5 | 5/5 |
| Planted problems **found** | 24/25 | 24/25 | 24/25 | 24/25 |
| …of which **proven** with an executed example | 22 | 22 | **24** | 21 |
| Missed by everyone | C6 (CRLF + empty temperature) | C6 | C6 | C6 |
| Unsupported CRITICAL/HIGH claims | 1 | 1 | 0 | 1 |
| Weakened/skipped/deleted tests + lowered gate (F4) | all found | all found | all found | all found |
| Extra *real* defects beyond the key (F2: Unicode digits rejected) | 0 | 0 | 1 | 1 |
| Subagent tokens | 97.6k | 99.3k | 102.4k | 102.7k |
| Wall time | 63 s | 71 s | 75 s | 67 s |

## 2. Correct changes (negative controls)

| | A | B | C | D |
|---|---|---|---|---|
| K1 (correct split) verdict | GO | CONDITIONAL GO | CONDITIONAL GO | GO |
| K2 (correct pricing) verdict | GO | GO | GO | CONDITIONAL GO |
| False HIGH/CRITICAL findings on K1+K2 | 0 | 0 | 0 | 0 |
| Ran executed checks on K2 (vs code reading only) | no | yes | yes | **no** |
| K1: depth of evidence | spot checks | spot checks | spot checks | **20,000-case property test** |

## 3. The control that wasn't (K3: our "correct" Rust port)

Our own differential corpus (600 records) showed the K3 port matching the Python reference 100%. **Every approach still returned NO-GO, and every approach was right.**

| Real divergence in K3 v1 | A | B | C | D |
|---|---|---|---|---|
| Unicode digits (`٣`, `５`) accepted by Python `int()`/`float()` | ✔ | ✔ | ✔ | ✔ |
| Integers beyond i64 → wrong error code | ✔ | ✔ | ✔ | ✔ |
| PEP 515 underscore rules in floats | ✔ | ✔ | ✔ | ✘ (reported as matching) |
| `\x1c` stripped by Rust but not by Python `float()` | ✔ | ✘ | ✘ | ✘ |

We fixed the port (v2) and reran K3 with all four. **All four found one more real divergence**: CPython refuses `int()` strings longer than 4,300 digits. A, B and D said NO-GO; C said CONDITIONAL GO. We fixed that as well (v3). It now matches on the hidden corpus plus seeded fuzz in CI.

## What this says, without spin

1. **On these 8 cases, `verify-engineering` did not detect more problems than the simpler approaches.** With a capable model, explicit written requirements and a "be thorough" prompt, all four approaches found 24 of 25 planted problems. The benchmark has a **ceiling effect**: the cases are too easy to separate the approaches.
2. **Its evidence discipline was not better in this run.** The skill told the agent to prove findings, but in two places it reported "code read only" results (a HIGH finding in F5, and the whole of K2), and once it wrongly marked an underscore class as matching. We tightened `SKILL.md` afterwards ("run it, don't just read it"; "code read only = NOT VERIFIED"). **That revision has not been re-benchmarked.**
3. **The most valuable result was the hidden-bug discovery.** Independent verifiers found 5 real defects in code that its author (us) had verified with a 600-record differential corpus. This is the core idea of the skill: the author's test corpus only contains what the author thought of.
4. The deterministic tools (`test_integrity_scan.py`, `diff_harness.py`, `mutation_probe.py`) did not, by themselves, change agent outcomes here. An independent pre-release audit *after* the benchmark found bugs in them (including a mutation-probe path that could write to real files, and scanner false positives). These were fixed, with regression tests, in the released version. **The benchmark ran on the pre-audit scripts and the pre-revision SKILL.md.**

## Limitations of this benchmark
- 1 run per approach per case (no repeated trials, no variance estimate). A single model family (Sonnet). Small, single-file cases with unusually explicit requirements.
- Scored by the repo author, not by a blinded third party.
- Approach C was used exactly as published, and its scope is narrower (verifying claims before completion), so it is not a like-for-like product comparison.

## Next benchmark (needed before making claims)
Larger multi-file repos, vague or partly missing requirements, weaker or cheaper models, repeated trials, a blinded scorer, and the revised SKILL.md.
