def split_bill(total_paise, people, tip_percent=0):
    """Split a bill (in paise) evenly, including tip."""
    grand = total_paise * (1 + tip_percent / 100)
    share = round(grand / people)
    return [share] * people
