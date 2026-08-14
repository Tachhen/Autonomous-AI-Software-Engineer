from calculator import multiply, subtract


def test_multiply():
    assert multiply(4, 5) == 20


def test_subtract():
    assert subtract(9, 4) == 5
