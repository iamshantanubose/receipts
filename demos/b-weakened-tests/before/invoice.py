from decimal import Decimal, ROUND_HALF_UP


def line_total(unit_price, qty, gst_rate):
    if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
        raise ValueError("qty must be a positive integer")
    amount = Decimal(str(unit_price)) * qty * (1 + Decimal(str(gst_rate)))
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
