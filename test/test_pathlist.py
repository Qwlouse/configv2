from collections.abc import Iterable, MutableSequence

import pytest

from config.containers import PathList
from config.path import Path


def test_is_list():
    pl = PathList()
    assert isinstance(pl, list)
    assert isinstance(pl, Iterable)
    assert isinstance(pl, MutableSequence)


def test_initialized_empty():
    pl = PathList()
    assert len(pl) == 0
    assert pl == []
    assert "a" not in pl
    assert pl.count("") == 0
    with pytest.raises(ValueError):
        pl.index(None)
    with pytest.raises(IndexError):
        _ = pl[1]

    for x in pl:
        assert False


def test_list_access():
    pl = PathList([1, 2, 3])
    assert 1 in pl
    assert 3 in pl
    assert pl == [1, 2, 3]
    assert pl[0] == 1
    assert pl[2] == 3
    assert pl.count(1) == 1
    assert pl[:2] == [1, 2]
    assert pl[1:] == [2, 3]
    assert pl[:] == [1, 2, 3]
    assert pl[1:2] == [2]
    assert pl[::2] == [1, 3]
    assert pl[-1] == 3
    assert pl[-2:] == [2, 3]


def test_append():
    pl = PathList([1, 2])
    pl.append(8)
    assert pl == [1, 2, 8]


def test_extend():
    pl = PathList([1, 2])
    pl.extend([4, 8])
    assert pl == [1, 2, 4, 8]


def test_pop():
    pl = PathList([1, 2, 3])
    assert pl.pop() == 3
    assert pl == [1, 2]
    assert pl.pop(0) == 1
    assert pl == [2]
    with pytest.raises(IndexError):
        assert pl.pop(1)
    assert pl.pop() == 2
    assert pl == []
    with pytest.raises(IndexError):
        assert pl.pop()


def test_recursive_attrlist_conversion():
    pl = PathList([1, [2, 3]])
    assert isinstance(pl[1], PathList)
    pl.append([4, 5])
    assert isinstance(pl[2], PathList)
    pl.extend([[7], 8])
    assert isinstance(pl[3], PathList)
    pl[0] = [0, 0, 0]
    assert isinstance(pl[0], PathList)


def test_path_access():
    pl = PathList([1, [2, 3]])
    assert pl[Path(0)] == 1
    assert pl[Path(1)] == [2, 3]
    assert pl[Path(1, 1)] == 3
