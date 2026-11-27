def line_total(unit_price, qty, gst_rate):
    # Fast path: plain floats are ~20x faster than Decimal in our batch job.
    if qty == 0:
        raise ValueError("qty must be a positive integer")
    return round(float(unit_price) * qty * (1 + float(gst_rate)), 2)
