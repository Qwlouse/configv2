import functools
import collections
from ast import literal_eval
from typing import Any, Tuple, List, Optional, overload
from contextlib import contextmanager

# noinspection Mypy
from lark import Transformer, Lark, Token


@functools.total_ordering
class Path(collections.abc.Sequence):
    """ Immutable config path object that holds a sequence of keys. """

    __slots__ = ("parts",)

    def __init__(self, *parts: Any):
        self.parts: Tuple[Any, ...] = parts

    def is_prefix_of(self, other: "Path") -> bool:
        """Return True if this path is a prefix of given path."""
        return self.parts == other.parts[: len(self)]

    def is_suffix_of(self, other: "Path") -> bool:
        """Return True if this path is a suffix of given path."""
        return self.parts == other.parts[-len(self) :]

    def is_compatible_with(self, other: "Path") -> bool:
        end = min(len(self), len(other))
        return self.parts[:end] == other.parts[:end]

    # Item access
    @overload
    def __getitem__(self, index: int) -> Any:
        ...  # pragma: no cover

    @overload
    def __getitem__(self, index: slice) -> "Path":
        ...  # pragma: no cover

    def __getitem__(self, index):
        if isinstance(index, slice):
            return Path(*self.parts[index])
        else:
            return self.parts[index]

    # Other Aux methods
    def __len__(self) -> int:
        return len(self.parts)

    def __hash__(self) -> int:
        hashable_parts = tuple(
            p if not isinstance(p, slice) else (slice, p.start, p.stop, p.step)
            for p in self.parts
        )
        return hash(hashable_parts)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Path):
            return self.parts == other.parts
        else:
            return False

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, Path):
            return self.parts > other.parts
        else:
            raise TypeError(f"unorderable types: Path < {type(other)}")

    def __repr__(self) -> str:
        r = "".join([self.format_part(part) for part in self.parts])
        r = r[1:] if r and r[0] == "." else r
        return r

    def __add__(self, other):
        if isinstance(other, Path):
            return Path(*(self.parts + other.parts))
        else:
            raise TypeError(
                "Can't convert '{}' object to Path implicitly.".format(type(other))
            )

    @contextmanager
    def track_errors(self):
        try:
            yield
        except (AttributeError, IndexError, KeyError, TypeError) as e:
            if not e.args or not isinstance(e.args[-1], Path):
                e.args += (self[:1],)
            else:
                e.args = e.args[:-1] + (self[:1] + e.args[-1],)
            raise

    @staticmethod
    def format_part(part: Any) -> str:
        if isinstance(part, str):
            if part.isidentifier():
                return "." + part
            else:
                return f"['{part}']"
        elif isinstance(part, slice):
            fm = [part.start, ":", part.stop]
            if part.step is not None:
                fm += [":", part.step]
            slice_str = "".join([str(f) for f in fm if f is not None])
            return f"[{slice_str}]"
        else:
            return "[" + str(part).replace(" ", "") + "]"

    @classmethod
    def from_str(cls, str_path: str) -> "Path":
        tree = path_parser.parse(str_path)
        return PathTransformer().transform(tree)


path_parser = Lark(
    start="path",
    grammar=r"""
// A path is a series of dot-separated identifiers and [] based item-access.
path: [identifier ("." identifier | "[" key "]")*]

?key: integer   // item-access keys can be any hashable python literal
    | slice_key
    | float_value
    | complex_value
    | boolean
    | none
    | string
    | other
    | tuple_key

tuple_key: "()"
         | "(" key ",)"
         | "(" key ("," key)+ [","] ")"

integer.3: DEC_NUMBER
         | HEX_NUMBER
         | BIN_NUMBER
         | OCT_NUMBER

complex_value.2: [FLOAT_NUMBER /[+-]/] IMAG_NUMBER

float_value.2: FLOAT_NUMBER

!slice_key.2: [integer] ":"i [integer] [":"i [integer]]

identifier: /\w+/

string: /".*?(?<!\\)(\\\\)*?"/ | /'.*?(?<!\\)(\\\\)*?'/

!none.2: "None"

!boolean.2: "True" | "False"

other.0: /[^"'.\]\s]+/

DEC_NUMBER: /0|-?[1-9]\d*/i
HEX_NUMBER: /-?0x[\da-f]*/i
OCT_NUMBER: /-?0o[0-7]*/i
BIN_NUMBER : /-?0b[0-1]*/i
FLOAT_NUMBER: /-?((\d+\.\d*|\.\d+|\d+)(e[-+]?\d+)?|\d+(e[-+]?\d+))/i
IMAG_NUMBER: /-?\d+j/i | FLOAT_NUMBER "j"i
""",
)


class PathTransformer(Transformer):
    @staticmethod
    def path(args: List[Any]) -> Path:
        return Path(*args)

    @staticmethod
    def identifier(args: List[Token]) -> str:
        return str(args[0])

    @staticmethod
    def slice_key(args: List[str]) -> slice:
        sargs: List[Optional[int]] = [None, None, None]
        i = 0
        for a in args:
            if a == ":":
                i += 1
            else:
                sargs[i] = int(a)
        return slice(*sargs)

    @staticmethod
    def integer(args: List[str]) -> int:
        return literal_eval(args[0])

    @staticmethod
    def complex_value(args: List[str]) -> complex:
        return complex("".join(args))

    @staticmethod
    def float_value(args: List[str]) -> float:
        return float(args[0])

    @staticmethod
    def none(_) -> None:
        return None

    @staticmethod
    def boolean(args: List[str]) -> bool:
        return {"True": True, "False": False}[args[0]]

    @staticmethod
    def string(args: List[str]) -> str:
        return args[0][1:-1]

    @staticmethod
    def other(args: List[str]) -> str:
        print("OTHER:", args)
        return str(args[0])

    @staticmethod
    def tuple_key(args: List[Any]) -> Tuple[Any, ...]:
        return tuple(args)
