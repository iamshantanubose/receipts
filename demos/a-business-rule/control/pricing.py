from decimal import Decimal, ROUND_HALF_UP

LOYALTY_RATE = Decimal("0.10")
LOYALTY_MIN = Decimal("1000")
LOYALTY_CAP = Decimal("500")


def checkout_total(subtotal, tax_rate, is_loyalty_member, coupon=Decimal("0")):
    """Return the amount the customer pays, including tax."""
    loyalty = Decimal("0")
    if is_loyalty_member and subtotal >= LOYALTY_MIN:
        loyalty = min(subtotal * LOYALTY_RATE, LOYALTY_CAP)
    discount = max(loyalty, coupon)  # never stack: best single discount
    taxable = max(subtotal - discount, Decimal("0"))
    total = taxable * (1 + tax_rate)
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
