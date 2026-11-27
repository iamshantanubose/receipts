# Ticket SHOP-214: Loyalty discount at checkout

Implement `checkout_total(subtotal, tax_rate, is_loyalty_member, coupon=0)` in `pricing.py`.
Amounts are in rupees as `Decimal`.

Acceptance criteria (signed off by Finance):

1. Loyalty members get **10% off the subtotal** when the subtotal is **₹1000 or more**.
2. The loyalty discount is **capped at ₹500**.
3. Tax is charged on the amount **after** discounts. The discount is never calculated on tax.
4. A coupon (a flat rupee amount) and the loyalty discount **do not stack**. The customer gets whichever is larger.
5. The total can never be negative.
6. Round the final total to 2 decimal places, half-up.

Behaviour that must not change: non-members with no coupon pay `subtotal * (1 + tax_rate)`.
