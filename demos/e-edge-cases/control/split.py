def split_bill(total_paise, people, tip_percent=0):
    """Split a bill (in paise) evenly, including tip. Integer maths only."""
    if isinstance(people, bool) or not isinstance(people, int) or people < 1:
        raise ValueError("people must be an integer >= 1")
    if isinstance(total_paise, bool) or not isinstance(total_paise, int) or total_paise < 0:
        raise ValueError("total_paise must be an integer >= 0")
    if not 0 <= tip_percent <= 100:
        raise ValueError("tip_percent must be between 0 and 100")
    from fractions import Fraction
    tip_exact = Fraction(total_paise) * Fraction(str(tip_percent)) / 100
    tip = int(tip_exact + Fraction(1, 2))  # half-up for non-negative values
    grand = total_paise + tip
    base, extra = divmod(grand, people)
    return [base + 1 if i < extra else base for i in range(people)]
