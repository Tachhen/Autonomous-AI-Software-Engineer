from app import welcome


def test_welcome():
    assert welcome("Tenzing") == "HELLO, TENZING!"


def test_empty_name():
    assert welcome("") == "HELLO, !"
