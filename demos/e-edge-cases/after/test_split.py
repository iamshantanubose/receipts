from split import split_bill


def test_even_split():
    assert split_bill(1000, 4) == [250, 250, 250, 250]


def test_with_tip():
    assert split_bill(1000, 2, tip_percent=10) == [550, 550]


def test_single_person():
    assert split_bill(999, 1) == [999]


def test_sum_matches_for_even_case():
    assert sum(split_bill(60000, 3)) == 60000
