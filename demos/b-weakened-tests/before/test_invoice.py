from decimal import Decimal as D

import pytest

from invoice import line_total


def test_simple_line():
    assert line_total("100.00", 2, "0.18") == D("236.00")


def test_half_up_rounding():
    # 0.125 * 1 * 1.0 -> 0.13 (half-up), not 0.12
    assert line_total("0.125", 1, "0") == D("0.13")


def test_paisa_exact():
    assert line_total("19.99", 3, "0.05") == D("62.97")


def test_rejects_zero_qty():
    with pytest.raises(ValueError):
        line_total("10", 0, "0.18")


def test_rejects_negative_qty():
    with pytest.raises(ValueError):
        line_total("10", -2, "0.18")
