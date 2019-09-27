import pytest
from config.path import Path
import pickle
from copy import copy, deepcopy


VALID_PATHS = {
    "": (),
    "foo": ("foo",),
    "a[10]": ("a", 10),
    "a[-13]": ("a", -13),
    "a.b": ("a", "b"),
    "a[False]": ("a", False),
    "a[1.7]": ("a", 1.7),
    "a[-3e-14]": ("a", -3e-14),
    "a[(1,2)]": ("a", (1, 2)),
    "a[(1,(2,()))]": ("a", (1, (2, ()))),
    "a[None]": ("a", None),
    "a['b c \" \\' ]=.']": ("a", "b c \" \\' ]=."),
    "a[:]": ("a", slice(None)),
    "a[1:7]": ("a", slice(1, 7)),
    "a[::2]": ("a", slice(None, None, 2)),
    "a[1:-1:3]": ("a", slice(1, -1, 3)),
    "α.β.é": ("α", "β", "é"),
    "_some.longer4.example[2]": ("_some", "longer4", "example", 2),
}
STR_PATHS, PARTS = zip(*sorted(VALID_PATHS.items()))

FANCY_NUMBERS = {
    "a[1+1j]": ("a", 1 + 1j),
    "a[1.7-3.2j]": ("a", 1.7 - 3.2j),
    "a[0b010]": ("a", 0b010),
    "a[0o17]": ("a", 0o17),
    "a[0xfa71]": ("a", 0xFA71),
}
STR_PATHS_FANCY, PARTS_FANCY = zip(*sorted(FANCY_NUMBERS.items()))


@pytest.mark.parametrize("parts", PARTS, ids=STR_PATHS)
def test_initialization(parts):
    p = Path(*parts)
    assert isinstance(p, Path)
    assert p.parts == parts


@pytest.mark.parametrize("parts", PARTS, ids=STR_PATHS)
def test_eq(parts):
    p1 = Path(*parts)
    p2 = Path(*parts)
    assert p1 == p2
    assert p1 != parts


def test_empty():
    assert not Path()


@pytest.mark.parametrize("parts", PARTS, ids=STR_PATHS)
def test_len(parts):
    assert len(Path(*parts)) == len(parts)


@pytest.mark.parametrize("parts", PARTS, ids=STR_PATHS)
def test_hash(parts):
    assert isinstance(hash(Path(*parts)), int)
    assert hash(Path(*parts)) == hash(Path(*parts))
    assert hash(Path(*parts)) != hash(Path(*parts) + Path("b"))


@pytest.mark.parametrize("parts", PARTS, ids=STR_PATHS)
def test_getitem(parts):
    p = Path(*parts)
    for i in range(len(parts)):
        assert p[i] == parts[i]


def test_ordering():
    p = Path("a", "b", 1, True)
    assert p < Path("a", "b", 2, False)
    assert p > Path("a", "b", 1, False)
    assert p < Path("z", "a", 0, False)
    assert p >= p
    assert p <= p


def test_ordering_failure():
    p = Path("a", 1)
    with pytest.raises(TypeError):
        fail = p > "a[1]"

    with pytest.raises(TypeError):
        fail = p > ("a", 1)


@pytest.mark.parametrize("parts", PARTS, ids=STR_PATHS)
def test_getitem_slice(parts):
    p = Path(*parts)
    for i in range(len(parts)):
        for j in range(i, len(parts)):
            assert p[i:j] == Path(*parts[i:j])


@pytest.mark.parametrize("str_path, parts", zip(STR_PATHS, PARTS), ids=STR_PATHS)
def test_repr(str_path, parts):
    assert repr(Path(*parts)) == str_path


@pytest.mark.parametrize("str_path, parts", zip(STR_PATHS, PARTS), ids=STR_PATHS)
def test_from_str(str_path, parts):
    ps = Path.from_str(str_path)
    pp = Path(*parts)
    assert ps == pp
    assert repr(ps) == str_path


@pytest.mark.parametrize(
    "str_path, parts", zip(STR_PATHS_FANCY, PARTS_FANCY), ids=STR_PATHS_FANCY
)
def test_from_str_fancy_numbers(str_path, parts):
    ps = Path.from_str(str_path)
    pp = Path(*parts)
    assert ps == pp


def test_from_str_fallback():
    p = Path.from_str("a[foobar]")
    assert p.parts == ("a", "foobar")


@pytest.mark.parametrize("parts", PARTS, ids=STR_PATHS)
def test_pickle(parts):
    p = Path(*parts)
    p2 = pickle.loads(pickle.dumps(p))
    assert p == p2


@pytest.mark.parametrize("parts", PARTS, ids=STR_PATHS)
def test_copy(parts):
    p = Path(*parts)
    assert copy(p) == p
    assert deepcopy(p) == p


def test_add():
    assert Path("foo") + Path("bar") == Path("foo", "bar")
    assert Path("foo") + Path(2) == Path("foo", 2)
    assert Path() + Path("foo", "bar") + Path() == Path("foo", "bar")
    p = Path()
    p += Path("a")
    p += Path("b")
    assert p == Path("a", "b")


def test_add_fail():
    p = Path("a", "b")
    with pytest.raises(TypeError):
        q = p + "c"
    with pytest.raises(TypeError):
        q = p + ("c",)


def test_is_prefix_of():
    p = Path.from_str("a.b[2].c[True].e.foo")
    for i in range(len(p)):
        assert p[:i].is_prefix_of(p)
        assert not p.is_prefix_of(p[:i])


def test_is_suffix_of():
    p = Path.from_str("a.b[2].c[True].e.foo")
    for i in range(1, len(p)):
        assert p[i:].is_suffix_of(p)
        assert not p.is_suffix_of(p[i:])
