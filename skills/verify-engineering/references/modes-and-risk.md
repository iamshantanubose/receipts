# Modes, risk and budgets

## Risk score (pick the highest band that applies)

| Band | Signals in the change |
|---|---|
| **CRITICAL** | money or billing, auth/authz, crypto/secrets, personal or regulated data, data migrations and deletes, concurrency or locking, public API/contract, infra/IaC, rewriting a component (language/framework migration) |
| **HIGH** | core business rules, persistence/schema, caching, retries/timeouts, external integrations, dependency upgrades with major versions, changes to tests or CI gates |
| **MEDIUM** | ordinary feature logic, internal APIs, UI logic with state |
| **LOW** | copy/text, styling, comments, docs, logging, isolated pure functions with good tests |

Then adjust the band:
- **+1 band** if the change was AI-generated and has not been reviewed by a human, touches more than 10 files, or test files changed together with source.
- **+1 band** if there is no reliable test suite, or the suite cannot be run.
- **−1 band** (never below LOW) for a pure addition behind a feature flag that is off by default.

## Mode from risk

| Risk | Default mode |
|---|---|
| LOW | QUICK |
| MEDIUM | STANDARD |
| HIGH | STANDARD (DEEP for the risky files) |
| CRITICAL | DEEP |

The user may ask for a lower mode. Honour it, but list what that leaves NOT VERIFIED.

## What each mode does

| Activity | QUICK | STANDARD | DEEP |
|---|---|---|---|
| Requirements + change map | brief | full | full + must-not-change inventory |
| Independent challenge (stage 3) | cold read of risky hunks | fresh subagent / cold read | fresh subagent + second independent pass |
| Test-integrity scan | yes | yes + manual review | yes + manual review |
| Mutation probe | no | risky files (≤ 30 mutants) | every changed core file (≤ 60) |
| New probe tests | 1–3 targeted | per requirement + edge cases | + property-based / fuzz corpus |
| Differential old vs new | if it is a migration | if behaviour must not change | always for rewrites; corpus ≥ 500 records where feasible |
| Performance / security checks | only if touched | targeted | targeted + fault injection in sandbox |
| Report | short | full | full + residual-risk register |

## Default budgets (user may override)

| Budget | QUICK | STANDARD | DEEP |
|---|---|---|---|
| Fix attempts per defect (fix mode) | 2 | 3 | 3 |
| Total fix-loop iterations | 3 | 5 | 8 |
| Mutants | 0 | 30 | 60 |
| Wall-clock guideline | ~5 min | ~20 min | ~60 min |

When a budget runs out: stop, report what is known, mark the rest NOT VERIFIED, and escalate.
