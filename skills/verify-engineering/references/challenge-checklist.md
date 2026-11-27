# Independent challenge checklist

Pick the sections that match the risk signals. For each question, answer **with evidence**
(a test you ran, an input → output, a file:line) or mark it SUSPECTED / NOT VERIFIED.

## Assumptions and business logic
- Which requirement does each changed hunk implement? Is any requirement left with no code?
- What did the author assume about inputs, units, currency, time zones, encoding, ordering, or nulls? Is it written down anywhere?
- Re-compute 2–3 acceptance examples by hand, *independently of the code*, then run them.
- Are any rules interacting (discount × tax, retry × idempotency, cache × permissions)? Test the combinations, not only each rule alone.

## Edge cases and boundaries
- Empty / zero / one / many; min, max, max+1; negative; very large; fractional where only integers make sense.
- Unicode (non-ASCII, combining marks, emoji, RTL), whitespace variants, CRLF line endings, case differences.
- Rounding ties (x.5), float representation (0.1 + 0.2), integer overflow, division by zero.
- Dates: leap day, DST change, month end, time zones, epoch, far-future dates.

## Error handling and recovery
- Every new failure path: is the error raised, typed, logged and surfaced? Or swallowed?
- After a partial failure, is the state consistent (all-or-nothing)? Are retries idempotent?
- Timeouts, cancellation and cleanup (files, sockets, locks, temp dirs) on error paths.

## Security
- Inputs reaching paths, shell, SQL, templates, deserialisers, redirects or URLs. Is anything injectable or open to traversal?
- Authorisation on every new or changed endpoint or operation. Can a user act on another user's data (IDOR)?
- Secrets in code, logs, error messages or test fixtures. Is validation or sanitisation weaker than before?
- New dependencies: are they known, maintained and pinned? Any install scripts?

## Data integrity
- Transactions: is the transaction boundary unchanged? Autocommit introduced? Multi-step writes atomic?
- Migrations: reversible? Data loss? Default values? Do old readers still work with new data?
- Money and quantities: exact types (decimal or integer minor units), no float.

## Concurrency
- Shared mutable state, check-then-act races, lock ordering, async functions without await, unbounded parallelism.
- Can two requests update the same record and lose an update?

## Compatibility and contracts
- Public function signatures, return types (for example `Decimal` → `float`), error codes, response shapes, field names, defaults.
- Wire formats and serialisation (key order, number formats, null vs missing).
- Config and env vars: renamed or removed? Feature-flag defaults?

## Performance and resources
- New N+1 queries, loops inside loops over large data, unbounded memory, missing pagination.
- Hot paths: measure before and after with the same input if performance was a goal.

## Integration
- Calls to other services: are timeouts, retries and error mapping unchanged? Is a contract test available?
- Downstream callers of changed symbols: grep for them and check each one still holds.
