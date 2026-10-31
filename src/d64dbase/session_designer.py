"""Session designer metadata, icon and default method wrappers (Stage 501)."""
from __future__ import annotations
import base64
import re

SESSION_EVENTS = ("beforeRelease", "onPregress")
SESSION_METHODS = ("access", "addAlias", "addPassword", "deleteAlias", "isAlias", "login", "user")
DEFAULT_LOCK_RETRY_COUNT = 3
DEFAULT_LOCK_RETRY_INTERVAL = 1000
_SESSION_ICON_BASE64 = "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"

def session_icon_png_bytes():
    """The exact, 36 x 36 RGBA PNG shared by the palette and form item."""
    return base64.b64decode(_SESSION_ICON_BASE64)

def session_method_source(component_name: str, method_name: str) -> list[str]:
    """Generate a WFM function which forwards one parameter to SESSION."""
    if method_name not in SESSION_METHODS:
        raise ValueError("Unbekannte Session-Methode: " + str(method_name))
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", str(component_name)):
        raise ValueError("Ungueltiger Session-Komponentenname")
    return [
        f"    function {component_name.upper()}_{method_name}(param)",
        f"        return SESSION::{method_name}(param)",
    ]


def session_method_binding(component_name: str, method_name: str) -> tuple[str, str]:
    """Return the WFM property and CLASS:: handler for a SESSION method.

    The property keeps the dBASE method's spelling; the handler identifier
    uses the uppercase CLASS:: convention independently of the function's
    mixed-case display name.
    """
    session_method_source(component_name, method_name)  # validate both names
    return method_name, f"CLASS::{component_name.upper()}_{method_name.upper()}"


def session_method_assignments(events) -> list[tuple[str, str]]:
    """Return bound SESSION methods, in their canonical declaration order."""
    values = {str(key).casefold(): str(value) for key, value in dict(events or {}).items()}
    return [
        (method, values[method.casefold()])
        for method in SESSION_METHODS if method.casefold() in values
    ]


def bind_session_method(events: dict, component_name: str, method_name: str) -> bool:
    """Bind the wrapper once, removing differently cased duplicate keys.

    Updates the designer's existing event/binding mapping in-place. True
    means a change was made to that mapping.
    """
    key, reference = session_method_binding(component_name, method_name)
    matches = [old for old in events if str(old).casefold() == key.casefold()]
    if len(matches) == 1 and matches[0] == key and events[key] == reference:
        return False
    for old in matches:
        events.pop(old)
    events[key] = reference
    return True


# Stage 503: SESSION::... is a native object method call, not a numeric
# expression. Keep the syntactic recognition deliberately narrow so an
# invalid or unsupported method cannot accidentally compile to a no-op.
_SESSION_RETURN_CALL = re.compile(
    r"(?is)^SESSION\s*::\s*([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*\)$"
)


def parse_session_return_call(expression: str):
    """Return (canonical method name, argument identifier) or None.

    Invalid SESSION:: syntax raises ValueError instead of falling through to
    the unrelated dBase arithmetic expression parser.
    """
    value = str(expression or "").strip()
    if not re.match(r"(?i)^SESSION\s*::", value):
        return None
    match = _SESSION_RETURN_CALL.fullmatch(value)
    if not match:
        raise ValueError("SESSION:: erwartet METHODENNAME(parameter), z.B. SESSION::deleteAlias(param).")
    method_name = next((name for name in SESSION_METHODS
                        if name.casefold() == match.group(1).casefold()), None)
    if method_name is None:
        raise ValueError("Unbekannte SESSION-Methode: " + match.group(1))
    return method_name, match.group(2)
