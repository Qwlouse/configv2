from dataclasses import dataclass, replace
from typing import Any, Optional, List, Dict, DefaultDict
import collections
from enum import Flag, auto

from config.path import Path
from config.containers import PathDict


class Node(Flag):
    LEAF = auto()
    DICT = auto()
    LIST = auto()
    ANY = LEAF | DICT | LIST
    LIST_OR_DICT = LIST | DICT


def get_value_and_type(value):
    if isinstance(value, dict):
        return {}, Node.DICT
    elif isinstance(value, list):
        return [], Node.LIST
    else:
        return value, Node.LEAF


@dataclass(frozen=True)
class Entry:
    path: Path
    priority: int
    value: Any
    type: Node = Node.ANY
    implicit: bool = False

    @property
    def explicit_priority(self):
        return 0 if self.implicit else self.priority

    def __post_init__(self):
        value, node_type = get_value_and_type(self.value)
        if self.type == Node.ANY:
            object.__setattr__(self, "type", node_type)

    def get_implicit_entries(self):
        # one implicit entries for each prefix of self.path
        for i in range(1, len(self.path)):
            prefix, part = self.path[:i], self.path[i]
            implicit_entry = replace(self, path=prefix, implicit=True)
            # implicit entries are dictionaries with the same priority as the
            # explicit entry except when the following path key is a slice or int
            # because in that case it might be either a dictionary or a list
            if isinstance(part, int):
                yield replace(implicit_entry, value={}, type=Node.LIST_OR_DICT)
            elif isinstance(part, slice):
                yield replace(implicit_entry, value=[], type=Node.LIST)
            else:
                yield replace(implicit_entry, value={}, type=Node.DICT)

        yield self

    def merge(self, other: "Entry"):
        assert self.path == other.path
        value = (
            self.value
            if self.explicit_priority >= other.explicit_priority
            else other.value
        )
        return Entry(
            path=self.path,
            priority=max(self.priority, other.priority),
            value=value,
            type=self.type & other.type,
            implicit=self.implicit and other.implicit,
        )


DEFAULT_PRIORITY = 10

PRIORITIES: Dict[str, int] = {
    "implicit": 1,
    "config": 2,
    "internal": 3,
    "named_config": 4,
    "run_arguments": 5,
    "commandline": 6,
    "forced": 7,
}


class Configuration:
    def __init__(self):
        self.entries_by_path: DefaultDict[Path, List[Entry]] = collections.defaultdict(
            list
        )
        self.active_priority = PRIORITIES["forced"]

    def add_entry(self, path: Path, value: Any, priority: Optional[int] = None):
        priority = priority or self.active_priority
        assert priority <= self.active_priority

        entry = Entry(path=path, value=value, priority=priority)

        # TODO: maybe merge entries of same priority
        for implicit_entry in entry.get_implicit_entries():
            self.entries_by_path[implicit_entry.path].append(implicit_entry)

    def get_value(self, path: Path):
        return self.to_dict(restrict=path)[path]

    def get_entry_for_priority(self, path: Path, priority=0):
        entries = [e for e in self.entries_by_path[path] if e.priority >= priority]
        sorted_entries = sorted(entries, key=lambda entry: entry.priority)
        result = sorted_entries.pop()
        while sorted_entries and result.implicit:
            result = result.merge(sorted_entries.pop())

        if not result.type:
            raise TypeError(f"No viable type found for '{path}'.")

        return result

    def check_write_access(self, path, priority):
        for p in [path[:i] for i in range(1, len(path))]:
            explicit_priority = [e.explicit_priority for e in self.entries_by_path[p]]
            if priority < max(explicit_priority, default=0):
                return False
        return True

    def to_dict(self, restrict=Path(), priority=0):
        compatible_paths = [
            k for k in self.entries_by_path.keys() if restrict.is_compatible_with(k)
        ]
        d = PathDict()
        for path in sorted(compatible_paths, key=lambda p: len(p)):
            entry = self.get_entry_for_priority(path, priority=priority)
            if self.check_write_access(path, entry.priority):
                d[path] = entry.value
        return d
