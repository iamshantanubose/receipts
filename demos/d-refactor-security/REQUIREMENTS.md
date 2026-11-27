# Ticket WAL-57: Refactor wallet service (no behaviour change)

Clean up `wallet.py`: remove duplication, use clearer names, add type hints. **Pure refactor. Behaviour must not change.**

Invariants (from the security and finance reviews, still in force):
1. `transfer()` is all-or-nothing. If any step fails, neither balance changes.
2. A transfer of a non-positive amount, or more than the sender's balance, raises `ValueError`.
3. `read_statement(user_id, name)` only serves files inside that user's own statement folder.
4. Every transfer appends exactly one line to the audit log.

The change under review is `after/` compared with `before/`.
