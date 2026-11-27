# Report and verdict rules

## Status words (use exactly these)
- **PASS**: checked, and evidence is attached (command + result, or input → output).
- **FAIL**: checked, evidence shows the requirement or invariant is broken.
- **NOT VERIFIED**: not checked, could not run, or the evidence is inconclusive. Give the reason.
- **SUSPECTED**: a plausible defect without proof yet. Never counted as PASS, and never alone blocks GO unless CRITICAL.

## Severity
| Severity | Meaning | Examples |
|---|---|---|
| CRITICAL | Security breach, data loss or corruption, money wrong at scale, outage | path traversal, non-atomic transfer, auth bypass |
| HIGH | A requirement or must-not-change behaviour is broken for realistic inputs; tests bent to pass | wrong business rule, migration mismatch, weakened assertions |
| MEDIUM | Wrong for rarer inputs, missing validation, test gaps that hide risk | rounding ties, CRLF, no negative tests |
| LOW | Minor or cosmetic issues, maintainability | naming, small inefficiency |

## Verdict
| Verdict | Only if |
|---|---|
| **NO-GO** | Any unresolved CRITICAL or HIGH finding, any broken must-not-change behaviour, or test-integrity tampering that hides failures |
| **CONDITIONAL GO** | No unresolved CRITICAL/HIGH, but there are open MEDIUM findings, any NOT VERIFIED requirement, or assumptions to confirm. List each condition as a checkbox |
| **GO** | Every requirement PASS with executed evidence, no unresolved test-audit finding, and no open MEDIUM or higher issue. NOT VERIFIED items may remain only outside the requirements (for example a performance claim nobody asked for), and they are listed |

Always include this line: *"GO means no blocking problems were found with the evidence listed. It is not a guarantee that the software is free of defects. Merge and deployment decisions remain with a human."*

## Report quality bar
- An executive summary of ≤ 5 lines a manager can read.
- Every finding: ID, severity, status, location (file:line), evidence, impact, recommended fix.
- Commands section: every command actually run, with its result. Nothing listed that was not run.
- Redact secrets and personal data in the outputs you quote.
