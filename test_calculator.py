import pytest

import calculator


def test_add():
    assert calculator.add(2, 3) == 5


def test_divide():
    assert calculator.divide(10, 4) == 2.5


def test_divide_by_zero():
    with pytest.raises(ValueError):
        calculator.divide(1, 0)
