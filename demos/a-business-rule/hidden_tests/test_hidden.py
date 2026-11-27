"""Ground-truth tests. Fail on the flawed build, pass on the control."""
from decimal import Decimal as D

from pricing import checkout_total


def test_capped_discount_with_tax():  # A2
    # (10000 - 500 cap) * 1.18 = 11210.00
    assert checkout_total(D("10000"), D("0.18"), True) == D("11210.00")


def test_discount_capped_at_500():  # A2
    assert checkout_total(D("10000"), D("0"), True) == D("9500.00")


def test_coupon_and_loyalty_do_not_stack():  # A3
    # loyalty 200 vs coupon 50 -> best single discount is 200
    assert checkout_total(D("2000"), D("0"), True, coupon=D("50")) == D("1800.00")


def test_coupon_reduces_taxable_amount():  # A1
    assert checkout_total(D("500"), D("0.10"), False, coupon=D("100")) == D("440.00")
