# Condensed findings per run

Each agent returned its findings in the same format: severity, one line, then evidence. Below, every finding is shortened to its
headline. Evidence is quoted only where it matters for scoring. SELF = self-review, REVIEW = generic code review,
VERIFY = verify-engineering.

## F1: wallet refactor (all three: NO-GO)
- **SELF**: CRITICAL atomicity lost (alice 100 → 70 after a failed transfer); CRITICAL path containment (absolute `name` read a file outside the folder; `..` user_id unchecked); HIGH tests miss failure paths.
- **REVIEW**: CRITICAL atomicity (100 → 70); CRITICAL traversal (absolute path returned another user's file; user_id `..`, `/` and symlinks not rejected); HIGH behaviour changed despite "no change"; LOW audit ordering.
- **VERIFY**: CRITICAL atomicity (a 100 → 50 on HEAD, 100 on HEAD~1); CRITICAL containment (`read_statement('../statements/u2','s.txt')` returned SECRET2; absolute name; symlinks); MEDIUM tests.

## F2: Python → Rust port (all three: NO-GO)
- **SELF**: HIGH rounding (0.25 → 0.2 vs 0.3); HIGH bytes vs chars; HIGH f64 truncation (10.9, 1e2, 4096.9 accepted) + `1_0` rejected; MEDIUM temp whitespace; LOW conventional tests too narrow.
- **REVIEW**: HIGH f64 truncation; HIGH bytes vs chars; HIGH rounding; HIGH temp parsing (whitespace, nan); MEDIUM `1_0`; panic on invalid UTF-8; LOW tests narrow.
- **VERIFY**: HIGH f64 truncation + `1_0` + **Unicode digit `٣`**; HIGH rounding; HIGH bytes vs chars; MEDIUM temp whitespace/nan/underscore; LOW tests narrow.
- Not found by anyone: C6 (`hi\t10\t\r`, an empty temperature field followed by CR).

## F3: split bill (all three: NO-GO)
- **SELF**: CRITICAL remainder (1000/3 → 999); HIGH float tip and rounding (no proving example); HIGH validation (people=0 → ZeroDivisionError, negatives, tip 150); MEDIUM tests only even.
- **REVIEW**: CRITICAL remainder; HIGH float/banker's (no proving example); HIGH validation; MEDIUM tests.
- **VERIFY**: CRITICAL remainder (also 1001/3 → 1002, a paisa invented); HIGH validation; MEDIUM tip/precision (evidence shown was really the remainder bug); MEDIUM tests.

## F4: invoice speed-up with weakened tests (all three: NO-GO)
- All three: float vs Decimal (0.125 → 0.12); qty validation gutted (-2, 1.5, True accepted); coverage gate 90 → 60; skip "flaky on CI"; approx / ±0.1 tolerance; deleted negative-qty test. REVIEW and VERIFY also flagged the unproven "20x" claim.

## F5: checkout pricing (all three: NO-GO)
- **SELF**: cap missing (10000 → 10620 vs 11210); stacking + coupon after tax (proven: non-member 500/18%/100 → 490 vs 472); tests. Its "discount on gross" finding uses the cap example (cause misattributed).
- **REVIEW**: cap; stacking + coupon after tax (1000/18%/300 → 762 vs 826); "discount on gross" CRITICAL with no wrong output (**unsupported**); MEDIUM negative coupon; tests.
- **VERIFY**: "discount on gross" CRITICAL whose own evidence shows equal outputs (**unsupported**); cap (proven); stacking (proven); coupon-after-tax HIGH "**code read only**"; tests.

## K1: correct split (no false HIGH from anyone)
- SELF GO · REVIEW CONDITIONAL GO · VERIFY GO. All three noted LOW: a string tip raises TypeError, not ValueError; thin tests. VERIFY ran a 20,000-case randomised property check.

## K2: correct pricing (no false HIGH from anyone)
- SELF GO (code read only) · REVIEW GO (ran cap/coupon/boundary checks) · VERIFY CONDITIONAL GO (code read only).

## K3 v1: "correct" Rust port (all three: NO-GO, correctly)
- **SELF**: Unicode digits; i64 overflow error code; float underscores; `\x1c` float whitespace.
- **REVIEW**: Unicode digits; float underscores; i64 overflow; LOW invalid UTF-8 (not run).
- **VERIFY**: Unicode digits; overflow (29,013-input corpus); LOW invalid UTF-8. **Wrongly reported underscores as matching.**

## K3 v2: fixed port, rerun
- SELF NO-GO, REVIEW NO-GO, VERIFY NO-GO. All three found the >4,300-digit `int()` limit difference. SELF also noted invalid-UTF-8 lossy decoding (out of scope). VERIFY's verbatim answer: [`raw/verify-control-v2.txt`](raw/verify-control-v2.txt).
