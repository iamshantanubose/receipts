# Answer key: Scenario E (keep this file away from the verifier during benchmarks)

Story: the function works for the "nice" numbers in the tests: even splits and round tips.

| ID | Severity | Defect |
|---|---|---|
| E1 | HIGH | The remainder is lost. `split_bill(1000, 3)` returns `[333, 333, 333]` and 1 paisa vanishes. It can also invent paise, since `round(1001/2)` gives `[500, 500]`, a paisa short, and 1003/2 can round up. This breaks rules 1 and 2. |
| E2 | HIGH | There is no input validation. `people=0` raises `ZeroDivisionError` instead of `ValueError`. Negative totals and tips, and fractional `people`, are silently accepted (`[share] * 2.5` raises `TypeError`). This breaks rule 4. |
| E3 | MEDIUM | Tip rounding. The tip is folded into a float and rounded with Python's half-to-even `round()`, not half-up. `split_bill(15, 1, 10)` gives 16 where the rule says 17. |
| E4 | MEDIUM | Precision. Large bills go through float division. The current output is still correct at 10^9 only by luck; the rule asks for guaranteed exactness. Exactness is the real check, so E4 counts as found if the verifier flags float use for money at scale. |
| T1 | MEDIUM (test integrity) | Every test input divides evenly. `test_sum_matches_for_even_case` checks the sum only where it can't fail. |

Expected verdict: **NO-GO**.
Control (`control/`): correct. Expected GO or CONDITIONAL GO.
