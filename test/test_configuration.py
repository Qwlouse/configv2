import pytest

from config.configuration import Configuration, Path

p = Path.from_str


@pytest.fixture
def cfg():
    return Configuration()


def test_simple(cfg):
    cfg.add_entry(p("a"), 1)
    cfg.add_entry(p("b"), "foo")

    assert cfg.get_value(p("a")) == 1
    assert cfg.get_value(p("b")) == "foo"
    assert cfg.get_value(p("")) == {"a": 1, "b": "foo"}


def test_nested(cfg):
    cfg.add_entry(p("a.b"), 1)
    cfg.add_entry(p("a.c"), 2)

    assert cfg.get_value(p("a.b")) == 1
    assert cfg.get_value(p("a.c")) == 2
    assert cfg.get_value(p("a")) == {"b": 1, "c": 2}
    assert cfg.get_value(p("")) == {"a": {"b": 1, "c": 2}}


def test_add_dict_entry(cfg):
    cfg.add_entry(p("a"), {"b": 1, "c": 2})
    assert cfg.get_value(p("a.b")) == 1
    assert cfg.get_value(p("a.c")) == 2
    assert cfg.get_value(p("a")) == {"b": 1, "c": 2}


def test_simple_override(cfg):
    cfg.add_entry(p("a"), {"b": 1, "c": 2}, priority=2)
    cfg.add_entry(p("a.b"), 9, priority=6)
    assert cfg.get_value(p("a.b")) == 9
    assert cfg.get_value(p("a.c")) == 2
    assert cfg.get_value(p("a")) == {"b": 9, "c": 2}


def test_simple_append(cfg):
    cfg.add_entry(p("a"), {"b": 1, "c": 2}, priority=2)
    cfg.add_entry(p("a.d"), 9, priority=6)
    assert cfg.get_value(p("a.b")) == 1
    assert cfg.get_value(p("a.c")) == 2
    assert cfg.get_value(p("a.d")) == 9
    assert cfg.get_value(p("a")) == {"b": 1, "c": 2, "d": 9}


def test_ignored_entry(cfg):
    cfg.add_entry(p("a"), {"b": 1, "c": 2}, priority=6)
    cfg.add_entry(p("a.b"), 9, priority=2)
    assert cfg.get_value(p("a.b")) == 1
    assert cfg.get_value(p("a.c")) == 2
    assert cfg.get_value(p("a")) == {"b": 1, "c": 2}


def test_closed_dict_override_entry(cfg):
    cfg.add_entry(p("a"), {"b": 1, "c": 2}, priority=2)
    cfg.add_entry(p("a"), {"d": 9}, priority=6)
    assert cfg.get_value(p("a.d")) == 9
    assert cfg.get_value(p("a")) == {"d": 9}


def test_case1(cfg):
    cfg.add_entry(p("a"), {"b": {"e": 1}, "c": 2}, priority=2)
    cfg.add_entry(p("a"), {"d": 9}, priority=4)
    cfg.add_entry(p("a.b.f"), 99, priority=6)
    assert cfg.get_value(p("a.d")) == 9
    assert cfg.get_value(p("a.b.f")) == 99
    assert cfg.get_value(p("a")) == {"d": 9, "b": {"f": 99}}


def test_int_key_implicit_dict(cfg):
    cfg.add_entry(p("a[1]"), "foo")
    assert cfg.to_dict() == {"a": {1: "foo"}}


def test_int_key_override_dict(cfg):
    cfg.add_entry(p("a.b"), True)
    cfg.add_entry(p("a[1]"), "foo")
    assert cfg.to_dict() == {"a": {"b": True, 1: "foo"}}


def test_int_key_override_list(cfg):
    cfg.add_entry(p("a"), [1, 2, 3], priority=2)
    cfg.add_entry(p("a[1]"), 22, priority=3)
    assert cfg.to_dict() == {"a": [1, 22, 3]}


def test_slice_key_implicit_list_error(cfg):
    cfg.add_entry(p("a"), [1, 2, 3, 4], priority=2)
    cfg.add_entry(p("a[:2]"), [9, 9], priority=4)
    assert cfg.to_dict() == {"a": [9, 9, 3, 4]}
