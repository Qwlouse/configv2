from typing import Union, Any
from collections.abc import Mapping, Iterable
from config.path import Path
from copy import copy


##############################################################################
#                               conversion                                   #
##############################################################################


def recursive_path_conversion(value: Any) -> Any:
    if isinstance(value, (PathTuple, PathList, PathDict)):
        return value
    elif isinstance(value, tuple):
        return PathTuple(value)
    elif isinstance(value, list):
        return PathList(value)
    elif isinstance(value, dict):
        return PathDict(value)
    else:
        return value


def recursive_unconversion(value):
    if isinstance(value, (PathDict, dict)):
        return {k: recursive_unconversion(v) for k, v in value.items()}
    elif isinstance(value, (PathTuple, tuple)):
        return tuple([recursive_unconversion(v) for v in value])
    elif isinstance(value, (PathList, list)):
        return list([recursive_unconversion(v) for v in value])
    else:
        return value


# noinspection PyUnresolvedReferences,Mypy
class PathMixin:
    def __getitem__(self, key: Union[Path, int, slice]) -> Any:
        if not isinstance(key, Path):
            return super().__getitem__(key)

        if not key:   # empty path
            return self

        with key.track_errors():
            first, rest = key[0], key[1:]
            entry = super().__getitem__(first)
            return entry[rest] if rest else entry

    def __contains__(self, key):
        if not isinstance(key, Path):
            return super().__contains__(key)

        if not key:   # empty path
            return True

        with key.track_errors():
            first, rest = key[0], key[1:]
            try:
                sub_item = self[first]
                return sub_item.__contains__(rest) if rest else True
            except (IndexError, AttributeError):
                return False

    def __setitem__(self, key, value, default=None):
        value = recursive_path_conversion(value)

        if not isinstance(key, Path):
            return super().__setitem__(key, value)

        with key.track_errors():
            first, rest = key[0], key[1:]
            if rest:
                if default is None:
                    to_update = self[first]
                else:
                    to_update = self.setdefault(first, default())
                to_update[rest] = value
            else:
                super().__setitem__(first, value)

    def __delitem__(self, key):
        if not isinstance(key, Path):
            return super().__delitem__(key)

        with key.track_errors():
            first, rest = key[0], key[1:]
            if rest:
                return self[first].__delitem__(rest)
            else:
                return super().__delitem__(first)


##############################################################################
#                                 Tuple                                      #
##############################################################################


class PathTuple(PathMixin, tuple):
    """Behaves like normal tuple, but handles Paths and auto-converts items"""

    @staticmethod
    def __new__(cls, seq=()):
        # noinspection PyTypeChecker
        return super().__new__(cls, [recursive_path_conversion(x) for x in seq])

    __setitem__ = None
    __delitem__ = None


##############################################################################
#                                 List                                       #
##############################################################################


class PathList(PathMixin, list):
    """Behaves like normal list, but handles Paths and auto-converts items"""

    def __init__(self, iterable=()):
        super().__init__([recursive_path_conversion(x) for x in iterable])

    def append(self, obj):
        list.append(self, recursive_path_conversion(obj))

    def extend(self, iterable):
        list.extend(self, recursive_path_conversion(iterable))


##############################################################################
#                                 Dict                                       #
##############################################################################


class PathDict(PathMixin, dict):
    """ Subclass of dict that allows attribute access and path based item access.

    Based on bunch/munch packages.
    """

    def __init__(self, seq=None, **kwargs):
        """
        PathDict() -> new empty AttributeDict
        PathDict(mapping) -> new dictionary initialized from a mapping
            object's (key, value) pairs
        PathDict(iterable) -> new dictionary initialized as if via:
            d = {}
            for k, v in iterable:
                d[k] = v
        PathDict(**kwargs) -> new dictionary initialized with the
            name=value pairs in the keyword argument list.
            For example:  dict(one=1, two=2)
        """
        super().__init__()
        self.update(seq, **kwargs)

    # only called if k not found in normal places
    def __getattr__(self, key):
        try:
            # Throws exception if not in prototype chain
            return object.__getattribute__(self, key)
        except AttributeError:
            try:
                return self[key]
            except KeyError:
                raise AttributeError(key)

    def __setattr__(self, key, value):
        try:
            # Throws exception if not in prototype chain
            object.__getattribute__(self, key)
        except AttributeError:
            try:
                self[key] = value
            except KeyError:
                raise AttributeError(key)
        else:
            object.__setattr__(self, key, value)

    def __delattr__(self, key):
        try:
            # Throws exception if not in prototype chain
            object.__getattribute__(self, key)
        except AttributeError:
            try:
                del self[key]
            except KeyError:
                raise AttributeError(key)
        else:
            object.__delattr__(self, key)

    def __contains__(self, key):
        if not isinstance(key, Path):
            return super().__contains__(key)

        if not key:   # empty path
            return self

        with key.track_errors():
            first, rest = key[0], key[1:]
            if rest:
                return super().__contains__(first) and self[first].__contains__(rest)
            else:
                return super().__contains__(first)

    def update(self, m=None, **kwargs):
        items = []
        if isinstance(m, Mapping):
            items.extend(m.items())
        elif isinstance(m, Iterable):
            items.extend(m)
        elif m is not None:
            raise ValueError(
                "Invalid m: has to be mapping or iterable, but was {}".format(type(m))
            )

        if kwargs:
            items.extend(kwargs.items())

        default = PathDict
        for k, v in items:
            self.__setitem__(k, v, default)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.to_dict())

    def copy(self):
        return copy(self)

    def to_dict(self):
        return recursive_unconversion(self)

    def recursive_update(self, d=None, **kwargs):
        """
        Given a dictionaries d, update dict d recursively.

        E.g.:
        d = {'a': {'b' : 1}}
        u = {'c': 2, 'a': {'d': 3}}
        => {'a': {'b': 1, 'd': 3}, 'c': 2}
        """
        assert d or kwargs
        d = recursive_path_conversion(kwargs if d is None else d)
        for k, v in d.flat_items():
            self.__setitem__(k, v, PathDict)

    def flat_items(self):
        yield from iterate_flattened(self)


##############################################################################
#                                 Utils                                      #
##############################################################################


def _by_str_key(x):
    k, v = x
    return str(k)


def iterate_flattened(d, key=Path(), key_func=_by_str_key, include_nodes=False):
    """
    Recursively iterate over the entries of nested dicts, lists, and tuples.

    Provides a full Path for each leaf.
    """
    if isinstance(d, Mapping):
        if include_nodes:
            yield key, type(d)()
        for k, value in sorted(d.items(), key=key_func):
            yield from iterate_flattened(value, key + Path(k), key_func=key_func)
    elif isinstance(d, (list, tuple)):
        if include_nodes:
            yield key, type(d)()
        for i, value in enumerate(d):
            yield from iterate_flattened(value, key + Path(i), key_func=key_func)
    else:
        yield key, d
