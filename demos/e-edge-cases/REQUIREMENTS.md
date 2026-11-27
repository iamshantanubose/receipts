# Ticket SPLIT-9: Split a bill between friends

`split_bill(total_paise, people, tip_percent=0)` in `split.py` returns a list with each person's share in paise (integers).

Acceptance criteria:
1. The shares must add up **exactly** to the total plus tip. No paisa is lost or invented.
2. Shares differ by at most 1 paisa. The extra paise go to the first people in the list.
3. The tip is `round_half_up(total_paise * tip_percent / 100)` paise.
4. `people` must be an integer ≥ 1, `total_paise` an integer ≥ 0, and `tip_percent` between 0 and 100. Otherwise raise `ValueError`.
5. Works for large bills (up to ₹10 crore = 10^9 paise) without precision loss.
