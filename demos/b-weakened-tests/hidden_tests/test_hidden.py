"""Ground-truth tests for BILL-88. Fail on after/, pass on before/."""
from decimal import Decimal as D

import pytest

from invoice import line_total


def test_half_up_rounding():  # B2
    assert D(str(line_total("0.125", 1, "0"))) == D("0.13")


def test_half_up_rounding_float_artifact():  # B2
    # 1.005 is stored as 1.00499999... in binary float
    assert D(str(line_total("1.005", 1, "0"))) == D("1.01")


def test_rejects_negative_qty():  # B3
    with pytest.raises(ValueError):
        line_total("10", -2, "0.18")


def test_rejects_fractional_qty():  # B3
    with pytest.raises(ValueError):
        line_total("10", 1.5, "0.18")


def test_returns_exact_decimal():  # B1
    assert isinstance(line_total("19.99", 3, "0.05"), D)
