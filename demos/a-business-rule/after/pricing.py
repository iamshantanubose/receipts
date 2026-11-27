from decimal import Decimal, ROUND_HALF_UP

LOYALTY_RATE = Decimal("0.10")
LOYALTY_MIN = Decimal("1000")


def checkout_total(subtotal, tax_rate, is_loyalty_member, coupon=Decimal("0")):
    """Return the amount the customer pays, including tax."""
    gross = subtotal * (1 + tax_rate)
    discount = Decimal("0")
    if is_loyalty_member and subtotal >= LOYALTY_MIN:
        discount = gross * LOYALTY_RATE
    total = gross - discount - coupon
    if total < 0:
        total = Decimal("0")
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
