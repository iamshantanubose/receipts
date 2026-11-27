# Answer key: Scenario A (keep this file away from the verifier during benchmarks)

Story: an AI agent built SHOP-214. All 4 of its unit tests pass. The code still breaks 3 of the 6 signed-off rules.

| ID | Severity | Defect | Requirement |
|---|---|---|---|
| A1 | HIGH | The coupon is subtracted **after** tax, so tax is charged on the pre-coupon amount. A non-member's ₹500 order with a ₹100 coupon at 10% tax pays ₹450 instead of ₹440. | #3 |
| A2 | HIGH | The ₹500 cap is missing. A ₹10,000 order gets ₹1,000 off. | #2 |
| A3 | HIGH | The coupon and the loyalty discount stack. Both are subtracted. | #4 |

Why the tests miss them: every discount test uses `tax_rate=0`, the only coupon test is the negative-total clamp, no subtotal goes above ₹5,000, and no test combines a coupon with loyalty.

Expected verdict: **NO-GO**.
Control (`control/`): correct. Expected verdict GO, or CONDITIONAL GO if the only gaps are coverage. Any HIGH finding on the control counts as a false positive.

Note: a percentage loyalty discount taken on the gross amount happens to give the same result as one taken on the subtotal, until the ₹500 cap applies. A reviewer who flags "discount computed on gross" without showing a wrong output has found a code smell, not a proven defect.
