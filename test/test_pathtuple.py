#!/usr/bin/env python3
# coding=utf-8

from collections.abc import Iterable, Sequence

import pytest

from config.containers import PathTuple
from config.path import Path


def test_is_tuple():
    pt = PathTuple()
    assert isinstance(pt, tuple)
    assert isinstance(pt, Iterable)
    assert isinstance(pt, Sequence)


def test_initialized_empty():
    pt = PathTuple()
    assert len(pt) == 0
    assert pt == ()
    assert "a" not in pt
    assert pt.count("") == 0

    with pytest.raises(ValueError):
        pt.index(None)

    with pytest.raises(IndexError):
        _ = pt[1]

    for x in pt:
        assert False


def test_tuple_access():
    pt = PathTuple([1, 2, 3])
    assert 1 in pt
    assert 3 in pt
    assert pt == (1, 2, 3)
    assert pt[0] == 1
    assert pt[2] == 3
    assert pt.count(1) == 1
    assert pt[:2] == (1, 2)
    assert pt[1:] == (2, 3)
    assert pt[:] == (1, 2, 3)
    assert pt[1:2] == (2,)
    assert pt[::2] == (1, 3)
    assert pt[-1] == 3
    assert pt[-2:] == (2, 3)


def test_recursive_attrlist_conversion():
    pt = PathTuple([1, (2, 3)])
    assert isinstance(pt[1], PathTuple)


def test_path_access():
    pt = PathTuple([1, (2, 3)])
    assert pt[Path(0)] == 1
    assert pt[Path(1)] == (2, 3)
    assert pt[Path(1, 1)] == 3
    assert Path(1, 1) in pt
    assert Path(0, 1) not in pt


@pytest.mark.parametrize(
    "path, expected_exc, error_path",
    [
        (Path(1, 4), IndexError, Path(1, 4)),
        (Path(1, 4, 0, 0), IndexError, Path(1, 4)),
        (Path(4, 1, 0, 0), IndexError, Path(4)),
        (Path("a", "b"), TypeError, Path("a")),
        (Path(0, 1), TypeError, Path(0)),
    ],
)
def test_path_error(path, expected_exc, error_path):
    pt = PathTuple((1, (2, 3, (4, 5))))
    with pytest.raises(expected_exc) as exc_info:
        _ = pt[path]
    assert exc_info.value.args[1] == error_path


def test_nested_eq():
    assert PathTuple((1, 2, (3, 4))) == (1, 2, (3, 4))
