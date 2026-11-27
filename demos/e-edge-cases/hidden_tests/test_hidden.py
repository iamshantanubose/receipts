"""Ground truth for SPLIT-9. Fail on after/, pass on control/."""
import pytest

from split import split_bill


def test_remainder_not_lost():  # E1
    assert split_bill(1000, 3) == [334, 333, 333]


def test_sum_always_exact():  # E1
    for total in (1, 7, 101, 99999):
        for n in (2, 3, 7):
            assert sum(split_bill(total, n)) == total


def test_zero_people_rejected():  # E2
    with pytest.raises(ValueError):
        split_bill(1000, 0)


def test_negative_inputs_rejected():  # E2
    with pytest.raises(ValueError):
        split_bill(-500, 2)
    with pytest.raises(ValueError):
        split_bill(500, 2, tip_percent=-10)


def test_fractional_people_rejected():  # E2
    with pytest.raises(ValueError):
        split_bill(1000, 2.5)


def test_returns_integers():  # E3
    assert all(isinstance(s, int) for s in split_bill(1001, 2, tip_percent=12.5))


def test_tip_half_up():  # E3
    # 15 * 10% = 1.5 paise -> half-up gives 2, so 17 in total
    assert sum(split_bill(15, 1, tip_percent=10)) == 17


def test_large_bill_precision():  # E4
    total = 10**9 + 7
    assert sum(split_bill(total, 3, tip_percent=7)) == total + round(total * 7 / 100 + 1e-9)
