# Condensed findings per run

Each agent returned its findings in the same format: severity, one line, then evidence. Below, every finding is shortened to its headline. Evidence is quoted only where it matters for scoring. A = self-review, B = generic review, C = existing verification skill, D = verify-engineering.

## F1: wallet refactor (all four: NO-GO)
- **A**: CRITICAL atomicity lost (alice 100 → 70 after a failed transfer); CRITICAL path containment (absolute `name` read a file outside the folder; `..` user_id unchecked); HIGH tests miss failure paths.
- **B**: CRITICAL atomicity (100 → 70); CRITICAL traversal (absolute path returned another user's file; user_id `..`, `/` and symlinks not rejected); HIGH behaviour changed despite "no change"; LOW audit ordering.
- **C**: CRITICAL atomicity; CRITICAL containment (absolute name → "SECRET"; user_id `..` not rejected; symlinks); MEDIUM tests; LOW ordering.
- **D**: CRITICAL atomicity (a 100 → 50 on HEAD, 100 on HEAD~1); CRITICAL containment (`read_statement('../statements/u2','s.txt')` returned SECRET2; absolute name; symlinks); MEDIUM tests.

## F2: Python → Rust port (all four: NO-GO)
- **A**: HIGH rounding (0.25 → 0.2 vs 0.3); HIGH bytes vs chars; HIGH f64 truncation (10.9, 1e2, 4096.9 accepted) + `1_0` rejected; MEDIUM temp whitespace; LOW conventional tests too narrow.
- **B**: HIGH f64 truncation; HIGH bytes vs chars; HIGH rounding; HIGH temp parsing (whitespace, nan); MEDIUM `1_0`; panic on invalid UTF-8; LOW tests narrow.
- **C**: HIGH bytes vs chars; HIGH f64 truncation; HIGH rounding; MEDIUM underscores/whitespace/**Unicode digits**; MEDIUM tests narrow; LOW "CRLF identical" (true for a non-empty field).
- **D**: HIGH f64 truncation + `1_0` + **Unicode digit `٣`**; HIGH rounding; HIGH bytes vs chars; MEDIUM temp whitespace/nan/underscore; LOW tests narrow.
- Not found by anyone: C6 (`hi\t10\t\r`, an empty temperature field followed by CR).

## F3: split bill (all four: NO-GO)
- **A**: CRITICAL remainder (1000/3 → 999); HIGH float tip and rounding (no proving example); HIGH validation (people=0 → ZeroDivisionError, negatives, tip 150); MEDIUM tests only even.
- **B**: CRITICAL remainder; HIGH float/banker's (no proving example); HIGH validation; MEDIUM tests.
- **C**: CRITICAL remainder; HIGH tip half-up **proven** (`split_bill(15,1,10)` → 16, expected 17); HIGH precision **proven** (10^17 case); HIGH validation; MEDIUM tests.
- **D**: CRITICAL remainder (also 1001/3 → 1002, a paisa invented); HIGH validation; MEDIUM tip/precision (evidence shown was really the remainder bug); MEDIUM tests.

## F4: invoice speed-up with weakened tests (all four: NO-GO)
- All four: float vs Decimal (0.125 → 0.12); qty validation gutted (-2, 1.5, True accepted); coverage gate 90 → 60; skip "flaky on CI"; approx / ±0.1 tolerance; deleted negative-qty test. B, C and D also flagged the unproven "20x" claim.

## F5: checkout pricing (all four: NO-GO)
- **A**: cap missing (10000 → 10620 vs 11210); stacking + coupon after tax (proven: non-member 500/18%/100 → 490 vs 472); tests. Its "discount on gross" finding uses the cap example (cause misattributed).
- **B**: cap; stacking + coupon after tax (1000/18%/300 → 762 vs 826); "discount on gross" CRITICAL with no wrong output (**unsupported**); MEDIUM negative coupon; tests.
- **C**: cap (9000 vs 9500); stacking (1500 vs 1700); coupon after tax **proven** (2000/18%/300 → 2060 vs 2006); tests.
- **D**: "discount on gross" CRITICAL whose own evidence shows equal outputs (**unsupported**); cap (proven); stacking (proven); coupon-after-tax HIGH "**code read only**"; tests.

## K1: correct split (no false HIGH from anyone)
- A GO · B CONDITIONAL GO · C CONDITIONAL GO · D GO. All four noted LOW: a string tip raises TypeError, not ValueError; thin tests. D ran a 20,000-case randomised property check.

## K2: correct pricing (no false HIGH from anyone)
- A GO (code read only) · B GO (ran cap/coupon/boundary checks) · C GO (ran checks) · D CONDITIONAL GO (code read only).

## K3 v1: "correct" Rust port (all four: NO-GO, correctly)
- **A**: Unicode digits; i64 overflow error code; float underscores; `\x1c` float whitespace.
- **B**: Unicode digits; float underscores; i64 overflow; LOW invalid UTF-8 (not run).
- **C**: Unicode digits + overflow; float underscores; LOW tests narrow.
- **D**: Unicode digits; overflow (29,013-input corpus); LOW invalid UTF-8. **Wrongly reported underscores as matching.**

## K3 v2: fixed port, rerun
- A NO-GO, B NO-GO, D NO-GO, C CONDITIONAL GO. All four found the >4,300-digit `int()` limit difference. A also noted invalid-UTF-8 lossy decoding (out of scope).
