# Reproduce → fix → re-verify loop

Runs **only in `fix` mode**, which the user must request explicitly. In `audit` mode, stop after step 3 and put
the proposed fix in the report.

```
for each confirmed defect (most severe first):
  1. Root cause    : explain WHY, with file:line. Not just "it fails".
  2. Reproduce     : write a test that fails now for exactly this reason. Run it and show the failure.
  3. Propose       : the smallest change that fixes the root cause. No drive-by refactors.
  4. Approve       : if the fix changes a public contract, data, security or anything outside the scope, ask first.
  5. Implement     : make the change.
  6. Re-run (a)    : the reproducing test now passes.
  7. Re-run (b)    : the affected regression tests plus the full suite, if it is affordable.
  8. Re-verify     : fresh subagent or cold read of the fix diff alone. Does it hold? Did it break anything?
  9. Record        : defect → test → fix → evidence, in the report.
```

## Budgets and stop conditions
- Use the per-mode budgets in `modes-and-risk.md` (QUICK 2 attempts / 3 iterations, STANDARD 3 / 5, DEEP 3 / 8), plus any time or token limit the user gives.
- After the last attempt on a defect, stop and escalate with what you learned.
- **Stop at once** if a fix needs: a dependency install, a schema or data migration, a change to production config,
  deleting files, or rewriting history. Ask first.
- **No blind retries.** Each attempt needs a new hypothesis, written down, before it runs.
- If the fix would make a test pass by changing the test, follow the hard rule in `test-integrity.md`.

## Hand-off when unresolved
Report: the defect, its reproduction, the hypotheses tried and why each failed, the current state of the
working tree (`git status`), and the recommended next step for the human.
