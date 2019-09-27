#!/usr/bin/env python3
# coding=utf-8

import json
from copy import copy, deepcopy

import pytest

from config.containers import PathDict, PathTuple, PathList
from config.path import Path


def assert_value(d, k, v):
    """ Assert that d contains key k with value v.

    Checks both item and attribute access.
    """
    assert k in d
    assert d[k] == v

    if isinstance(k, str):
        assert hasattr(d, k)
        assert getattr(d, k) == v
        assert getattr(d, k) is d[k]


def assert_not_in(d, k):
    assert k not in d

    with pytest.raises(KeyError):
        _ = d[k]

    if isinstance(k, str):
        with pytest.raises(AttributeError):
            _ = getattr(d, k)


def test_initialized_empty():
    ad = PathDict()
    assert len(ad) == 0

    assert_not_in(ad, "a")
    assert_not_in(ad, 1)
    assert_not_in(ad, True)
    assert_not_in(ad, (17, "b"))

    assert list(ad.keys()) == []
    assert list(ad.values()) == []
    assert list(ad.items()) == []

    for k in ad:
        assert not k and k

    assert repr(ad) == "PathDict({})"
    assert not ad
    assert not bool(ad)


def test_dict_access():
    cfg = PathDict()
    cfg[7] = 8
    cfg["foo"] = "bar"
    cfg[True] = False
    cfg[0.5] = 1.5

    assert_value(cfg, 7, 8)
    assert_value(cfg, "foo", "bar")
    assert_value(cfg, True, False)
    assert_value(cfg, 0.5, 1.5)

    assert set(cfg.keys()) == {7, True, "foo", 0.5}
    assert set(cfg.values()) == {8, "bar", False, 1.5}
    assert set(cfg.items()) == {(7, 8), ("foo", "bar"), (True, False), (0.5, 1.5)}


def test_empty_path():
    cfg = PathDict({"a": 1, "b.c": 10, "d": {"e": 10}, True: False, 2: 3})
    empty = Path()
    assert cfg[empty] is cfg
    assert empty in cfg



def test_get_item():
    """Attribute dict should have normal item access"""
    cfg = PathDict({"a": 1, "b.c": 10, "d": {"e": 10}, True: False, 2: 3})
    assert cfg["a"] == 1
    assert cfg["d"] == {"e": 10}
    assert cfg[True] is False
    assert cfg[2] == 3
    assert cfg["b.c"] == 10

    with pytest.raises(KeyError):
        _ = cfg["b"]

    with pytest.raises(KeyError):
        _ = cfg["d.e"]


def test_setitems():
    cfg = PathDict()
    cfg["a"] = 12
    cfg["b"] = "foo"
    cfg["a"] += 1
    cfg.b *= 2

    assert_value(cfg, "a", 13)
    assert_value(cfg, "b", "foofoo")


def test_attr_access():
    cfg = PathDict()
    cfg.a = 12
    cfg["b"] = "foo"

    assert_value(cfg, "a", 12)
    assert_value(cfg, "b", "foo")

    assert set(cfg.keys()) == {"a", "b"}
    assert set(cfg.values()) == {12, "foo"}
    assert set(cfg.items()) == {("a", 12), ("b", "foo")}


def test_init_from_dict():
    cfg = PathDict({"a": 12, "b": "foo"})

    assert_value(cfg, "a", 12)
    assert_value(cfg, "b", "foo")

    assert set(cfg.keys()) == {"a", "b"}
    assert set(cfg.values()) == {12, "foo"}
    assert set(cfg.items()) == {("a", 12), ("b", "foo")}


def test_init_from_dotteddict():
    cfg = PathDict({"a.b": 12, "a.c": "foo"})
    assert_value(cfg, "a.b", 12)
    assert_value(cfg, "a.c", "foo")


def test_init_from_path_dict():
    cfg = PathDict({Path("a", "b"): 12, Path("a", 2): "foo"})
    assert_value(cfg, "a", PathDict({"b": 12, 2: "foo"}))


def test_converts_subdicts():
    cfg = PathDict()
    cfg["a"] = {"b": {"c": 4}}
    assert set(cfg.keys()) == {"a"}
    assert isinstance(cfg.a, PathDict)
    assert set(cfg.a.keys()) == {"b"}
    assert isinstance(cfg.a.b, PathDict)
    assert set(cfg.a.b.items()) == {("c", 4)}
    assert cfg.a.b.c == 4


def test_converts_subdicts_in_init():
    cfg = PathDict({"a": {"b": {"c": 4}}})
    assert set(cfg.keys()) == {"a"}
    assert isinstance(cfg.a, PathDict)
    assert set(cfg.a.keys()) == {"b"}
    assert isinstance(cfg.a.b, PathDict)
    assert set(cfg.a.b.items()) == {("c", 4)}
    assert cfg.a.b.c == 4


def test_pathcontainer_conversion():
    cfg = PathDict()
    cfg["a"] = (1, [2, 3], {"four": (5, 8)})
    assert isinstance(cfg.a, PathTuple)
    assert isinstance(cfg.a[1], PathList)
    assert isinstance(cfg.a[2], PathDict)
    assert isinstance(cfg.a[2].four, PathTuple)
    assert cfg[Path("a", 1, 0)] == 2
    assert cfg[Path("a", 2, "four", 1)] == 8


def test_supports_path_access():
    cfg = PathDict({"a": {"b": {"c": 4}}})
    assert cfg[Path("a")] is cfg.a
    assert cfg[Path.from_str("a.b")] is cfg.a.b
    assert cfg[Path.from_str("a.b.c")] is cfg.a.b.c
    assert cfg[Path.from_str("a.b.c")] == 4

    cfg[Path.from_str("a.b.c")] = 6
    assert cfg[Path.from_str("a.b.c")] == 6
    cfg[Path.from_str("a.b.d")] = 8
    assert cfg[Path.from_str("a.b.d")] == 8

    cfg[Path.from_str("a.b")] = {"e": 9}
    assert set(cfg.a.b.keys()) == {"e"}
    assert cfg[Path.from_str("a.b.e")] == 9


def test_contains():
    b = PathDict({"ponies": "are pretty!"})
    assert "ponies" in b
    assert ("foo" in b) is False

    b["foo"] = 42
    assert "foo" in b

    b.hello = "hai"
    assert "hello" in b

    b[None] = 123
    assert None in b

    b[False] = 456
    assert False in b


def test_contains_path():
    b = PathDict({"ponies": {"are": "pretty!"}})
    assert Path.from_str("ponies") in b
    assert ("foo" in b) is False
    assert Path.from_str("ponies.are") in b
    assert Path.from_str("ponies.foo") not in b

    b["foo"] = 42
    assert Path.from_str("foo") in b
    assert Path.from_str("ponies.foo") not in b

    b.ponies.foo = "hai"
    assert Path.from_str("ponies.foo") in b


def test_delattr():
    b = PathDict({"lol": 42})
    del b.lol

    with pytest.raises(KeyError):
        _ = b["lol"]

    with pytest.raises(AttributeError):
        _ = b.lol


def test_dotted_delattr():
    b = PathDict({"lol": {"rofl": 42}})
    del b.lol.rofl

    assert_value(b, "lol", {})

    with pytest.raises(KeyError):
        _ = b["lol.rofl"]

    with pytest.raises(AttributeError):
        _ = b.lol.rofl


def test_delitem():
    cfg = PathDict({"lol": 42})
    del cfg["lol"]

    with pytest.raises(KeyError):
        _ = cfg["lol"]

    with pytest.raises(AttributeError):
        _ = cfg.lol


def test_delitem_path():
    cfg = PathDict({"lol": {"rofl": 42}})
    del cfg[Path.from_str("lol.rofl")]

    assert_value(cfg, "lol", {})

    with pytest.raises(KeyError):
        _ = cfg["lol.rofl"]

    with pytest.raises(AttributeError):
        _ = cfg.lol.rofl


def test_to_dict():
    d = {"foo": {"lol": True}, "hello": 42, "ponies": "are pretty!"}
    cfg = PathDict(d)
    assert cfg.to_dict() == d


# @pytest.mark.skip("Not sure if this is a good idea")
# def test_dict_property():
#     d = {'foo': {'lol': True}, 'hello': 42, 'ponies': 'are pretty!'}
#     cfg = AttributeDict(d)
#     assert cfg.__dict__ == d


def test_repr():
    d = {"foo": {"lol": True}, "hello": 42, "ponies": "are pretty!"}
    b = PathDict(d)
    assert repr(b).startswith("PathDict({")
    assert "'ponies': 'are pretty!'" in repr(b)
    assert "'hello': 42" in repr(b)
    assert "'foo': {'lol': True}" in repr(b)
    assert "'hello': 42" in repr(b)

    with_spaces = PathDict({1: 2, '"a b"': 9, "c": PathDict({"simple": 5})})
    assert repr(with_spaces).startswith("PathDict({")
    assert "'\"a b\"': 9" in repr(with_spaces)
    assert "1: 2" in repr(with_spaces)
    assert "'c': {'simple': 5}" in repr(with_spaces)

    assert with_spaces == eval(repr(with_spaces))


def test_shallow_copy():
    m = PathDict({"urmom": {"sez": {"what": "what"}}})
    c = copy(m)
    assert c is not m
    assert c.urmom is m.urmom
    assert c.urmom.sez is m.urmom.sez
    assert c.urmom.sez.what == "what"
    assert c == m


def test_deepcopy():
    m = PathDict({"urmom": {"sez": {"what": "what"}}})
    c = deepcopy(m)
    assert c is not m
    assert c.urmom is not m.urmom
    assert c.urmom.sez is not m.urmom.sez
    assert c.urmom.sez.what == "what"
    assert c == m


@pytest.mark.parametrize("attrname", dir(PathDict))
def test_reserved_attributes(attrname):
    # Make sure that the default attributes on the AttributeDict instance are
    # accessible.

    taken_munch = PathDict({attrname: "abc123"})

    # Make sure that the attribute is determined as in the filled collection...
    assert attrname in taken_munch

    # ...and that it is available using key access...
    assert taken_munch[attrname] == "abc123"

    # ...but that it is not available using attribute access.
    attr = getattr(taken_munch, attrname)
    assert attr != "abc123"

    empty_munch = PathDict()

    # Make sure that the attribute is not seen contained in the empty
    # collection...
    assert attrname not in empty_munch

    # ...and that the attr is of the correct original type.
    attr = getattr(empty_munch, attrname)
    if attrname == "__doc__":
        assert isinstance(attr, str)
    elif attrname in ("__hash__", "__weakref__"):
        assert attr is None
    elif attrname == "__module__":
        assert attr == "config.containers"
    elif attrname == "__dict__":
        assert set(attr.keys()) == set()
    else:
        assert callable(attr)


def test_update():
    d = {"foo": {"lol": True}, "hello": 42, "ponies": "are pretty!"}
    b = PathDict(d)

    b.update(a="b", hello=10, foo={"bar": 2})

    assert b.a == "b"
    assert b.hello == 10
    assert b.foo == {"bar": 2}


def test_recursive_update():
    d = {"foo": {"lol": True}, "ponies": "are pretty!"}
    b = PathDict(d)

    b.recursive_update(a="b", hello={"you": 10}, foo={"bar": 2})

    assert b.a == "b"
    assert isinstance(b.hello, PathDict)
    assert b.hello.you == 10
    assert isinstance(b.foo, PathDict)
    assert b.foo == {"bar": 2, "lol": True}
