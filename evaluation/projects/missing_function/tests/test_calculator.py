from calculator import square, cube


def test_square():
    assert square(4) == 16


def test_cube():
    assert cube(3) == 27


def test_cube_negative():
    assert cube(-2) == -8
