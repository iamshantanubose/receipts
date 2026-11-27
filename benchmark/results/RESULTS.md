# Benchmark results (run of 2026-11-27)

**Summary: one early run, scored by the repo author, with no measurable detection advantage for the skill.** On these small
cases every approach found 24 of 25 planted problems, and the skill backed the fewest of them with an executed example.
Treat this as a baseline for a better benchmark, not as evidence that the skill outperforms simpler prompts.

Verdicts and findings come from 9 agent runs: 3 approaches × 3 batches (flawed, controls, and a rerun of K3 after it was fixed).
Each run was one fresh agent session reviewing a whole batch. Nothing is estimated. `raw-findings.md` holds a condensed
transcription of every run's final answer. The verbatim text is in `raw/` only for the run that saved it to a file; the other
answers were transcribed from the session output.

## 1. Flawed changes (F1–F5): 25 planted problems in total
Per scenario: A (business rule) 3, B (weakened tests) 6, C (Rust port) 7, D (refactor) 4, E (edge cases) 5.

| | SELF | REVIEW | VERIFY |
|---|---|---|---|
| Verdict correct (NO-GO) on all 5 | 5/5 | 5/5 | 5/5 |
| Planted problems **found** | 24/25 | 24/25 | 24/25 |
| …of which **proven** with an executed example | 22 | 22 | 21 |
| Missed by every approach | C6 (CRLF + empty temperature) | C6 | C6 |
| Unsupported CRITICAL/HIGH claims | 1 | 1 | 1 |
| Weakened/skipped/deleted tests + lowered gate (F4) | all found | all found | all found |
| Extra *real* defects beyond the key (F2: Unicode digits rejected) | 0 | 0 | 1 |
| Per run, all five cases: agent tokens | 97.6k | 99.3k | 102.7k |
| Per run, all five cases: tool calls | 8 | 11 | 8 |
| Per run, all five cases: wall time | 63 s | 71 s | 67 s |

The last three rows describe one agent session reviewing all five cases. Eight to eleven tool calls for five cases is shallow,
which is part of why the cases did not separate the approaches.

## 2. Correct changes (negative controls)

| | SELF | REVIEW | VERIFY |
|---|---|---|---|
| K1 (correct split) verdict | GO | CONDITIONAL GO | GO |
| K2 (correct pricing) verdict | GO | GO | CONDITIONAL GO |
| False HIGH/CRITICAL findings on K1+K2 | 0 | 0 | 0 |
| Ran executed checks on K2 (vs code reading only) | no | yes | **no** |
| K1: depth of evidence | spot checks | spot checks | **20,000-case property test** |

## 3. The control that wasn't (K3: the "correct" Rust port)

The author's own differential corpus (600 records) showed the K3 port matching the Python reference 100%. **Every approach still
returned NO-GO, and every approach was right.**

| Real divergence in K3 v1 | SELF | REVIEW | VERIFY |
|---|---|---|---|
| Unicode digits (`٣`, `５`) accepted by Python `int()`/`float()` | ✔ | ✔ | ✔ |
| Integers beyond i64 → wrong error code | ✔ | ✔ | ✔ |
| PEP 515 underscore rules in floats | ✔ | ✔ | ✘ (reported as matching) |
| `\x1c` stripped by Rust but not by Python `float()` | ✔ | ✘ | ✘ |

The port was fixed (v2) and K3 was rerun with every approach. **All three found one more real divergence**: CPython refuses
`int()` strings longer than 4,300 digits, and all three said NO-GO. The port was fixed again (v3), and the reference now pins
that limit explicitly. v3 matches on the hidden corpus plus 5,000 seeded adversarial records, checked by
`tests/test_demo_ground_truth.py` (run locally on Python 3.9 and 3.13).

## What this says, without spin

1. **On these 8 cases, `verify-engineering` did not detect more problems than the simpler approaches.** With a capable model,
   explicit written requirements and a "be thorough" prompt, every approach found 24 of 25 planted problems. The benchmark has a
   **ceiling effect**: the cases are too easy to separate the approaches.
2. **Its evidence discipline was not better in this run.** The skill told the agent to prove findings, but twice it reported
   "code read only" results (a HIGH finding in F5, and the whole of K2), and once it wrongly marked an underscore class as
   matching. `SKILL.md` was tightened afterwards ("run it, don't just read it"; "code read only = NOT VERIFIED"). **That revision
   has not been re-benchmarked.**
3. **The most useful result was the hidden-bug discovery.** Verifiers that did not write the code found 5 real defects in a port
   its author had checked with a 600-record differential corpus. That is the core idea of the skill: an author's test corpus
   only contains what the author thought of.
4. The bundled scripts did not, by themselves, change agent outcomes here. They were reviewed and fixed after the run (including a
   mutation-probe path that could write to real files, and scanner false positives and false negatives). **The run used the
   earlier scripts and the earlier `SKILL.md`.**

## Limitations of this run
- 1 run per approach per batch (no repeated trials, no variance estimate). A single model family. Small, single-file cases with
  unusually explicit requirements.
- Scored by the repo author, not by a blinded third party.
- One agent reviewed a whole batch, so cases within a batch were not independent of each other.

## Next benchmark (needed before making any claim)
Larger multi-file repos, vague or partly missing requirements, weaker or cheaper models, repeated trials, one case per agent,
a blinded scorer, and the current `SKILL.md` and scripts.
