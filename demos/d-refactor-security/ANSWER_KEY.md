# Answer key: Scenario D (keep this file away from the verifier during benchmarks)

Story: a "pure refactor" for readability. All 6 existing tests still pass. The refactor removed two safety properties.

| ID | Severity | Defect |
|---|---|---|
| D1 | CRITICAL (data integrity) | Atomicity is lost. `isolation_level=None` (autocommit) plus removing `with db:` means a transfer to an unknown account debits the sender, then raises `KeyError`, and the money is gone. This breaks invariant 1. |
| D2 | CRITICAL (security) | Path traversal. The `realpath` + `commonpath` check was replaced with a `".." in name.split("/")` check. An absolute `name` (`/etc/passwd`) passes, because `os.path.join` throws away the base. Symlinks that escape the folder are followed, and backslash or encoded variants are not handled. This breaks invariant 3. |
| D3 | HIGH (security) | `user_id` is no longer checked at all. `user_id="alice/../bob"` reads Bob's statements. |
| T1 | MEDIUM (test integrity) | Tests only cover the happy path and the `..` case in `name`. Nothing tests failure in the middle of a transfer, absolute paths, symlinks, or a malicious `user_id`. |

Expected verdict: **NO-GO**. The CRITICAL items must block a GO.
Control: `before/` is correct for these invariants and passes `hidden_tests/`.
