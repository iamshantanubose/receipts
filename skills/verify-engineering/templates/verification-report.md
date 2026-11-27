# Engineering Verification Report

| | |
|---|---|
| **Verdict** | GO / CONDITIONAL GO / NO-GO |
| **Change** | [repo] · [base]...[head] · [N files, +A −D] |
| **Mode / permission** | [QUICK/STANDARD/DEEP] · [AUDIT ONLY / FIX AND VERIFY] |
| **Risk** | [LOW/MEDIUM/HIGH/CRITICAL]: [one-line reason] |
| **Date / verifier** | [YYYY-MM-DD] · [agent/model, independent subagent: yes/no] |

## 1. Executive summary
[≤ 5 lines: what changed, the verdict, the 1–3 findings that matter most, and what is still unknown.]

## 2. Scope
- In scope: [paths, commits, requirements]
- Out of scope / not examined: [...]

## 3. Requirements coverage
| # | Requirement / must-not-change | Status | Evidence |
|---|---|---|---|
| R1 | ... | PASS / FAIL / NOT VERIFIED | [test name / command / input → output] |

## 4. Findings (most severe first)
| ID | Severity | Status | Location | Finding | Evidence | Recommended fix |
|---|---|---|---|---|---|---|
| F1 | HIGH | FAIL | `file:line` | ... | ... | ... |

## 5. Test execution
| Command | Result | Notes |
|---|---|---|
| `...` | exit 0, 42 passed | pre-existing failures: none |

## 6. Test-integrity audit
- Scanner: `test_integrity_scan.py --base [base]`: [summary]
- Confirmed issues: [weakened / skipped / deleted / gates lowered / tautological / over-mocked]
- Mutation probe: [N mutants, K killed, S survived; survivors that matter]
- Requirement → test gaps: [...]

## 7. Behavioural discrepancies (differential / shadow)
- Corpus: [size, how it was built, synthetic/sanitised]
- Match rate: [x%] · groups: [n]
| Group (fingerprint) | Count | Root cause | Status |
|---|---|---|---|

## 8. Security and performance
[Findings, or "not in scope / NOT VERIFIED", with the reason.]

## 9. Unverified assumptions and NOT VERIFIED items
- [item]: [why it was not verified] · [what would verify it]

## 10. Commands executed
```
[every command actually run, in order, with exit codes; secrets redacted]
```

## 11. Remaining risks
[What could still go wrong after the recommended fixes, given what was not tested.]

## 12. Recommended actions
- [ ] [action] (blocks GO: yes/no)

---
GO means no blocking problems were found with the evidence listed. It is not a guarantee that the software
is free of defects. Merge and deployment decisions remain with a human.
