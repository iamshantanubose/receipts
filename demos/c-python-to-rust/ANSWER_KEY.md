# Answer key: Scenario C (keep this file away from the verifier during benchmarks)

Story: an AI agent ported the Python normalizer to Rust in one pass. All 10 conventional tests pass on both versions.
On 600 synthetic traffic-like records, only **54.7%** of outputs match.

| ID | Severity | Root cause in `rust_port/src/main.rs` | Example input → legacy vs port |
|---|---|---|---|
| C1 | HIGH | `prompt.len()` counts **UTF-8 bytes**, but Python `len()` counts **code points**. Every non-ASCII prompt (Hindi, accents, emoji) gets the wrong `chars`, and some are wrongly rejected as `prompt_too_long`. | `café au lait` → chars=12 vs chars=13 |
| C2 | HIGH | `max_tokens` is parsed as `f64` and **truncated**, so `10.7` → 10 and `1e3` → 1000 are accepted where the legacy code returns `bad_max_tokens`. | `hi\t10.7\t0.5` → ERR vs OK |
| C3 | HIGH | `max_tokens` with an underscore, such as `1_000`, is valid in Python `int()` but rejected by Rust. | `1_000` → OK vs ERR bad_max_tokens |
| C4 | MEDIUM | Temperature rounding: `(t*10).round()/10` rounds halves away from zero. Python rounds the exact binary value half-to-even. | `0.15` → 0.1 vs 0.2; `0.95` → 0.9 vs 1.0 |
| C5 | MEDIUM | Temperature with surrounding whitespace (` 0.5`) is accepted by Python `float()` but rejected by Rust `parse`. | ERR bad_temperature only in the port |
| C6 | LOW | CRLF input: `lines()` strips `\r`, so an empty temperature field gets defaulted, while legacy returns `bad_temperature`. | `hi\t10\t\r` |
| T1 | MEDIUM (test integrity) | The conventional suite is ASCII-only, uses integers only, has no rounding ties and no whitespace variants. It cannot tell the port apart from the reference. | — |

Expected verdict: **NO-GO** for the port, with C1–C5 found through differential testing on identical inputs.
Control: `control_rust/` mirrors Python's `int()`/`float()`/`str.strip()` rules, including Unicode digits, PEP 515 underscores, numeric whitespace and integers beyond i64. It matches the reference 100% on the hidden corpus plus 5,000 seeded adversarial records (`hidden_tests/check.sh`), and on 20,000 more in additional local runs. A verifier should report GO, or CONDITIONAL GO with residual risk outside the tested input domain (for example invalid UTF-8, which the Python reference rejects with a crash).

**Benchmark history (kept on purpose).** Version 1 of this control was *not* equivalent. It missed Unicode digits, PEP 515 underscore rules, integers beyond i64, and the fact that `float()` does not strip `\x1c`–`\x1f` while `str.strip()` does. The first 600-record corpus didn't catch that, and **every verification approach in the benchmark did.** The control was fixed and added those inputs to the corpus. On the rerun, every approach found one more real difference: Python's `int()` refuses strings longer than 4,300 digits (CPython's `int_max_str_digits` limit), and the control saturated them instead. Version 3 fixes that too, and the reference now pins the limit explicitly (`INT_MAX_STR_DIGITS` in `legacy_python/normalize.py`), so its behaviour no longer depends on the Python version. Invalid UTF-8 input remains **out of scope** (the Python reference does not define behaviour for it). This is exactly the failure the skill warns about: a corpus that only covers what the author thought of.
