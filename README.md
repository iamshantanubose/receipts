# VERIFY: evidence-driven verification for AI-written code

> **Everyone can make AI write code. Great engineers know how to prove that it works.**

`verify-engineering` is an Agent Skill for **Claude Code** and **Cursor** (Codex-compatible format). It turns your
coding agent into an **independent verifier**: it doesn't trust the author, the PR description or "all tests pass".
It produces its own evidence and ends with a clear **GO / CONDITIONAL GO / NO-GO** report.

```
/verify-engineering            → picks QUICK / STANDARD / DEEP from the risk of your change
/verify-engineering deep       → migrations, rewrites, money, auth, data
/verify-engineering fix        → also fixes what it finds (only when you say so)
```

## Why
AI agents are very good at producing code that *looks* finished. Common failure modes:
- The code passes its own tests but breaks a business rule nobody wrote a test for.
- The agent "fixes" a failing test by loosening the assertion, skipping it, or lowering the coverage gate.
- A rewrite (Python → Rust, REST → gRPC, ORM swap) passes the old tests but behaves differently on real inputs.
- A "pure refactor" quietly removes a transaction or a security check.

VERIFY is built to catch exactly these.

## What it does: 7 stages
1. **Requirements**: acceptance criteria, behaviour that must not change, assumptions. Asks only when it really matters.
2. **Change map**: diff → requirements → affected callers → risk and blast radius.
3. **Independent challenge**: a *fresh* subagent with no access to the author's reasoning, plus a risk-based checklist (logic, edges, security, data integrity, concurrency, compatibility…).
4. **Test-integrity audit** *(the part most reviews skip)*: deleted, skipped and weakened tests, edited expected values, swallowed errors, lowered coverage gates, CI told to ignore failures. Then a **mutation probe** to check that the tests can catch bugs at all.
5. **Behaviour proof**: targeted probes, property, boundary and contract checks, and for migrations a **differential harness** that runs old and new on identical inputs and groups the mismatches by root cause.
6. **Reproduce → fix → re-verify**: only in `fix` mode, with a failing test first and hard iteration budgets.
7. **Report**: every claim carries evidence; anything not checked is **NOT VERIFIED**, never "passed". Critical issues block GO. A human makes the merge call.

## Install (about 2 minutes)
**Claude Code**
```bash
npx skills add iamshantanubose/verify-engineering -a claude-code -g
```
or as a plugin, inside Claude Code: `/plugin marketplace add iamshantanubose/verify-engineering`, then `/plugin install verify-engineering@verify-engineering`.

**Cursor**
```bash
npx skills add iamshantanubose/verify-engineering -a cursor -g
```
**Manual (any host)**
```bash
git clone https://github.com/iamshantanubose/verify-engineering.git
cp -R verify-engineering/skills/verify-engineering ~/.claude/skills/    # Claude Code (Cursor's docs say it reads this folder too)
```
Details and troubleshooting: [Claude Code](docs/install-claude-code.md) · [Cursor](docs/install-cursor.md) · [Codex](docs/install-codex.md) · [Troubleshooting](docs/troubleshooting.md)

## Quick start: see it catch something
```bash
git clone https://github.com/iamshantanubose/verify-engineering.git && cd verify-engineering/demos/b-weakened-tests/after
python3 -m pytest -q                 # 3 passed, 1 skipped: "done"
python3 ../../../skills/verify-engineering/scripts/test_integrity_scan.py --before ../before --after .
# 6 findings: coverage gate 90 → 60, skip "flaky on CI", 2 weakened assertions, a deleted test…
```
Then open the folder in your agent and run `/verify-engineering`. A full example report: [examples/reports/scenario-b-weakened-tests.md](examples/reports/scenario-b-weakened-tests.md).

## Modes
| Mode | When | What you get |
|---|---|---|
| **QUICK** | Small, low-risk change | Requirement check, test-integrity scan, targeted probes, short report |
| **STANDARD** | Normal feature or PR | All 7 stages, an independent challenge, a probe per requirement |
| **DEEP** | Migrations, rewrites, money, auth, data, concurrency | + differential old-vs-new testing, a mutation probe, fault injection, a second independent pass |

Permissions: **AUDIT ONLY** (default: read-only, reports and failing tests) or **FIX AND VERIFY** (only when you ask).

## Built-in tools (Python 3.9+, standard library only, no installs)
| Script | What it does |
|---|---|
| `test_integrity_scan.py` | Finds test tampering in a git diff (incl. untracked files) or between two folders. Strongest for Python and JS/TS; basic patterns for Rust, Go, Java/Kotlin, C#, Ruby |
| `diff_harness.py` | Differential/shadow testing: old vs new on identical inputs. Line, per-record or JSON modes; mismatches grouped by fingerprint |
| `mutation_probe.py` | Plants small bugs in a **temp copy** and reports which ones your tests miss |

## Safety by design
The skill instructs the agent to: stay read-only by default; never merge, deploy, push, delete or rewrite history; treat repo
content as untrusted (ignore instructions hidden in code or docs, and report them); redact secrets; run destructive tests only in
temp copies; ask before installing anything; and never report a check it didn't run. These are instructions to an AI agent,
so keep your host's own permission prompts on. The bundled scripts enforce their part in code: the mutation probe refuses
targets outside its temporary copy, and refs and paths are validated.

## Demos, tests and benchmark
- [`demos/`](demos/): 5 deliberately flawed scenarios (business rule, weakened tests, a **Python → Rust migration**, refactor security/data-integrity, edge cases) plus correct versions to measure false alarms.
- [`tests/`](tests/): 53 automated tests (scripts, safety regressions, spec compliance, demo ground truth). Run with `python3 -m pytest -q tests`.
- [`benchmark/`](benchmark/): a blinded, reproducible comparison against other verification approaches, with method and raw results.

## Compatibility and limits
See [docs/compatibility.md](docs/compatibility.md) and [docs/validation.md](docs/validation.md). In short: Claude Code is the primary host; Cursor and Codex
use the same portable `SKILL.md` but haven't been verified live yet. The scripts are fast heuristics, not a replacement for full mutation tools or for careful review. GO means "no blocking problems found with the evidence listed". It is not a guarantee.

## License
MIT © 2026 Shantanu Bose
