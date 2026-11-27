# Auditing the tests themselves

Goal: decide whether the test suite **could fail** if the code were wrong. "Green" is only evidence
when the tests are honest and relevant.

## Automated scan (triage)
`scripts/test_integrity_scan.py` flags these in the diff:

| Rule | What it catches | Default severity |
|---|---|---|
| deleted-test-file / deleted-test | test (or @Test / [Fact] / #[test] marker) removed and not re-added | HIGH |
| test-removed-or-renamed | a test name disappeared while new test names appeared in the same file | MEDIUM: confirm it was a rename |
| skipped-test | unconditional skip / xfail / ignore / disabled / `.only` focus added | HIGH without a linked issue, otherwise MEDIUM |
| conditional-skip | `skipif` / `skipUnless` / `@EnabledOn…` added | LOW: check the condition is legitimate |
| assertions-dropped | fewer assertions than before in a test file | MEDIUM, HIGH if 2 or more |
| weakened-assertion | exact check → approx / bare truthy (`assert x`) / `is not None` / ordering (`> 0`) / membership / `abs(...) < tol` | HIGH |
| expected-value-changed | same assertion, different expected literal | MEDIUM: confirm that a requirement changed |
| swallowed-error | `except: pass` (also `pass` added under an unchanged `except` line), empty `catch {}`, `|| true`, Go `_ = err`, Rust `let _ =` | HIGH in tests, MEDIUM in source |
| coverage-gate-lowered / -removed | `fail_under`, `coverageThreshold`, … decreased or deleted (config files only) | HIGH |
| failures-ignored | `continue-on-error`, `--deselect`, `-k "not …"`, `--passWithNoTests`, … | HIGH |
| mock-heavy | 3 or more new mocks/patches in one test file | MEDIUM |

The scanner is pattern-based and best-effort: strongest for Python and JS/TS, basic for Rust, Go, Java/Kotlin, C# and Ruby. It scans the working tree including untracked files, and with `--base` it diffs from the merge-base. **Confirm every hit by reading it**, and look for what it cannot see.

## Manual review (always in STANDARD/DEEP)
1. **Requirement → test map.** For each acceptance criterion, name the test that would fail if it broke. No test = gap.
2. **Tautological tests.** Does the test compute the expected value with the same logic as the code (`expected = price * 0.9` copied from the implementation)? That proves nothing.
3. **Expected values taken from the output.** Literals that look copied from a run (`62.970000000001`), or snapshot files regenerated in the same change.
4. **Mocks replacing the subject.** Is the thing under test itself mocked? Do mocks return the answer the test then asserts?
5. **Never-failing tests.** Asserting inside a loop that runs zero times, `assert` on a non-empty string, missing `await`, exceptions caught by the test itself, `pytest.raises(Exception)` that is too broad.
6. **Negative paths.** Invalid input, failures in the middle of an operation, permission denied, timeouts. Are any tested?
7. **Input diversity.** Are all inputs "nice" (ASCII, even numbers, integers, no ties)? Nice-only inputs hide defects.
8. **Config drift.** Test discovery patterns, markers, environment flags, CI conditions (`if:`) that stop tests from running.
9. **History.** For changed tests, compare with the previous version: `git log -p -- <test file>`. Was it changed *after* the code started failing it?

## Can the tests catch bugs? (mutation / fault injection)
`scripts/mutation_probe.py` plants small bugs in a **temporary copy** and runs the tests. Interpreting the score:
- Survivors on lines that implement a requirement are real gaps. Write a test that kills each one.
- Some survivors are *equivalent mutants*, where the behaviour really is unchanged. Explain them; don't chase them.
- For a fuller run, use the ecosystem tool: `mutmut` (Python), `cargo mutants` (Rust), Stryker (JS/TS), PIT (Java). Ask before installing anything.

## Hard rule
Never weaken, skip, delete or re-baseline a test to get a pass. If a test really is wrong, show the
requirement that proves it, and propose the correction in the report (or in fix mode, change it with
that justification written in the commit/report).
