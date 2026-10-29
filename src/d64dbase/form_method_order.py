"""Qt-independent ordering for the dBASE WFM source outline and new event methods.

The source outline is a *view*: it must not rearrange hand-written source.
Only an explicit addition of a designer-generated event handler is allowed to
reorder the event-handler portion of the serialized WFM method collection.
"""

from __future__ import annotations

import re
from typing import Iterable, List, TypeVar

_T = TypeVar("_T")
_EVENT_NAME = re.compile(r"^[A-Za-z_]\w*_on[A-Za-z_]\w*$", re.IGNORECASE)
_NATURAL_SPLIT = re.compile(r"(\d+)")


def _alphanumeric_key(name: str) -> tuple:
    """Natural, case-insensitive sorting: Button2 before Button10."""
    parts = _NATURAL_SPLIT.split(str(name).casefold())
    return tuple((1, int(part)) if part.isdigit() else (0, part)
                 for part in parts)


def source_outline_sort_key(name: str, kind: str) -> tuple:
    """Procedure: __init__, __del__, others; function: __main__, others."""
    folded = str(name).casefold()
    category = str(kind).casefold()
    if category == "procedure":
        if folded == "__init__":
            return (0, (), folded)
        if folded == "__del__":
            return (1, (), folded)
    elif category == "function" and folded == "__main__":
        return (0, (), folded)
    return (2, _alphanumeric_key(name), folded)


def insert_event_method_sorted(methods: Iterable[_T], new_method: _T,
                               *, bound_names: Iterable[str] = ()) -> List[_T]:
    """Insert a *new* WFM event method into the alphabetical event group.

    All existing non-event methods retain their relative order. Their source
    lines and bodies are never edited. A pre-existing event group is sorted
    only when the designer explicitly inserts a new handler. Custom event
    names are detected through WFM OnXxx bindings passed as bound_names.
    """
    result = list(methods)
    wanted = str(getattr(new_method, 'name', '')).casefold()
    if any(str(getattr(m, 'name', '')).casefold() == wanted for m in result):
        return result  # Case-insensitive duplicate guard
    bound = {str(name).casefold() for name in bound_names}
    bound.add(wanted)

    def is_handler(method):
        name = str(getattr(method, 'name', ''))
        return name.casefold() in bound or bool(_EVENT_NAME.fullmatch(name))

    event_positions = [i for i, method in enumerate(result) if is_handler(method)]
    if not event_positions:
        result.append(new_method)
        return result
    first = event_positions[0]
    handlers = [result[i] for i in event_positions] + [new_method]
    handlers.sort(key=lambda method: _alphanumeric_key(getattr(method, 'name', '')))
    remainder = [method for method in result if not is_handler(method)]
    remainder[first:first] = handlers
    return remainder
