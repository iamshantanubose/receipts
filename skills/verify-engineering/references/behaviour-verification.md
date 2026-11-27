# Verifying actual behaviour

Pick the cheapest technique that can settle each open question. Record each command and its result.

| Technique | Use when | How (language-agnostic) |
|---|---|---|
| Targeted unit probe | One rule or one edge case | A small test in a scratch file that imports the unit and asserts the requirement's example |
| Regression run | Always | The project's own full test command. Note any pre-existing failures separately |
| Integration | Change crosses a module, DB, queue or filesystem boundary | Real components where they are safe locally (SQLite or a test container), fakes only at the outer edge |
| End-to-end | User-visible flow | Run the app locally and drive the flow (CLI, HTTP client, or browser automation) |
| Contract | API producers and consumers | Compare request/response shape, status codes, error codes and field types against the published contract or the previous version |
| Differential | Rewrite, port, optimisation, "no behaviour change" refactor | `scripts/diff_harness.py`: old and new on identical inputs |
| Property-based | Rules that must hold for all inputs (sum preserved, idempotent, round-trip) | Hypothesis / fast-check / proptest / QuickCheck. Without a library, a seeded random loop |
| Boundary | Ranges, limits, sizes | min−1, min, min+1, max−1, max, max+1, empty, huge |
| Performance | Speed or memory was a goal, or the hot path changed | Same input, same machine, several runs, report the median. Never claim a speedup from one run |
| Security | Untrusted input, auth, files, shell, SQL | Crafted inputs: traversal (`../`, absolute paths, symlinks), injection payloads, another user's IDs, oversized input |
| Fault injection | Recovery, atomicity, retries | Make a dependency fail in the middle of an operation (raise, timeout, disk full) **in a sandbox or temp copy**, then check the state |

## Differential testing and local shadow runs (migrations and rewrites)

The strongest evidence that a rewrite is equivalent: **the same inputs go into both versions, and the outputs are identical**.

1. **Pick the reference.** The old implementation is the oracle, even where it is "wrong". Differences are reported; intended differences need a requirement.
2. **Make both versions callable the same way.** CLI on stdin/stdout, an HTTP endpoint on two local ports, or a function wrapper. Normalise things that do not matter (timestamps, request IDs, key order) and *document* each normalisation.
3. **Build the corpus** (synthetic or sanitised, never raw production data without authorisation):
   - every existing test input;
   - the spec's examples;
   - the edge-case list from the challenge checklist, especially Unicode, number formats, whitespace, rounding ties, empty and missing fields, line endings;
   - **language-semantics classes** that a port silently changes: what the old runtime's parsers accept (Python `int()` takes `"٣"`, `"1_000"`, `" 5 "`, and has no integer overflow), string length units (bytes vs code points vs grapheme clusters), rounding mode (half-even vs half-away), float formatting, regex/Unicode tables, sort order and collation, integer division and modulo of negatives, `null` vs missing, default encodings, line-ending handling;
   - randomised combinations of valid and invalid values (seeded, so they can be reproduced). Write a small generator rather than a hand-picked list. A hand-picked list only contains what you already thought of.
4. **Run:** `python3 scripts/diff_harness.py --old "<old>" --new "<new>" --inputs corpus.txt [--mode lines|each|json] --report diff.json`
5. **Triage by fingerprint group, largest first.** Each group usually has one root cause. Reproduce one example as a failing test, fix it, rerun the **whole** corpus, and watch the match rate rise.
6. **In `fix` mode**, iterate within the fix-loop budgets (`fix-loop.md`) until the match is 100% or every remaining group is an approved intended difference. **In `audit` mode**, don't iterate: report every group with one reproducing example and its likely root cause.
7. **Report:** the match rate, groups and root causes, the corpus size and how it was built, the normalisations, and what the corpus does NOT cover (residual risk).

A **local shadow** setup sends the same recorded or synthetic request stream to both versions at the same time and compares the responses. It is the same idea at service level. **Never mirror production traffic, replay production writes, or touch production systems without explicit authorisation**, and even then only with read-only, side-effect-free requests.

## Evidence hygiene
- Write down the exact command, working directory, versions (language, toolchain), and the result (exit code and the key output lines).
- Separate **pre-existing** failures (they fail on the base too) from failures this change introduced. Check by running on the base.
- A flaky result counts as NOT VERIFIED until it reproduces consistently. Rerun it and note how many times.
