from decimal import Decimal as D

from pricing import checkout_total


def test_non_member_pays_subtotal_plus_tax():
    assert checkout_total(D("500"), D("0.18"), False) == D("590.00")


def test_member_below_threshold_gets_no_discount():
    assert checkout_total(D("999"), D("0"), True) == D("999.00")


def test_member_gets_ten_percent_with_zero_tax():
    assert checkout_total(D("2000"), D("0"), True) == D("1800.00")


def test_total_never_negative():
    assert checkout_total(D("100"), D("0"), False, coupon=D("500")) == D("0.00")
