import pytest
from calculator import Calculator


def test_add():
    calc = Calculator()
    assert calc.add(10, 5) == 15


def test_subtract():
    calc = Calculator()
    assert calc.subtract(10, 5) == 5


def test_multiply():
    calc = Calculator()
    assert calc.multiply(10, 5) == 50


def test_divide():
    calc = Calculator()
    assert calc.divide(10, 5) == 2


def test_divide_by_zero():
    calc = Calculator()

    with pytest.raises(ValueError):
        calc.divide(10, 0)


def test_percentage():
    calc = Calculator()
    assert calc.percentage(200, 10) == 20


def test_average():
    calc = Calculator()
    assert calc.average([10, 20, 30]) == 20