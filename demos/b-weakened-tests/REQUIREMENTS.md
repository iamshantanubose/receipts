# Ticket BILL-88: Speed up invoice line totals

`line_total(unit_price, qty, gst_rate)` in `invoice.py` is too slow in batch jobs. Make it faster.
**The behaviour must not change.**

Existing rules (from BILL-12, still in force):
1. Money is exact to the paisa. Round half-up to 2 decimals.
2. `qty` must be a positive integer. Otherwise raise `ValueError`.
3. GST is applied per line: `round(unit_price * qty * (1 + gst_rate), 2)`.
4. The project keeps line coverage at or above 90% in CI.

The change under review is the most recent commit (`after/`) on top of the baseline (`before/`).
