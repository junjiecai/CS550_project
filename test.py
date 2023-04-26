from backend.core import _get_local_neighbours


def test_1():
    results = set(_get_local_neighbours(0, 0, check_range=True, x_range=[-1, 1], y_range=[-1, 1]))

    answer = set([
        (-1, -1),
        (0, -1),
        (1, -1),
        (-1, 0),
        (1, 0),
        (-1, 1),
        (0, 1),
        (1, 1)
    ])

    assert results == answer


def test_2():
    results = set(_get_local_neighbours(-1, -1, check_range=True, x_range=[-1, 1], y_range=[-1, 1]))

    answer = set([
        (0, -1),
        (0, 0),
        (-1, 0)
    ])

    assert results == answer


def test_3():
    results = set(_get_local_neighbours(0, 1, check_range=True, x_range=[-1, 1], y_range=[-1, 1]))

    answer = set([
        (-1, 0),
        (0, 0),
        (1, 0),
        (1, 1),
        (-1, 1)
    ])

    assert results == answer
