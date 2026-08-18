# dBase WFM / FORM OOP parser
# Stage 108b - package-safe module

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import re


class DBaseWfmError(Exception):
    def __init__(self, message: str, *, line: int = 1, column: int = 1, filename: str = "<WFM>"):
        self.message = message
        self.line = int(line)
        self.column = int(column)
        self.filename = filename
        super().__init__(f"{filename}:{line}:{column}: {message}")


# Keep the parser standalone so it can live inside the existing d64dbase package.
DBaseCompilerError = DBaseWfmError

@dataclass
class DBaseWfmFont:
    family: str = "Arial"
    size: int = 10
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikeout: bool = False


@dataclass
class DBaseWfmControl:
    path: str
    class_name: str
    parent_path: str
    properties: Dict[str, object] = field(default_factory=dict)
    events: Dict[str, str] = field(default_factory=dict)
    font: Optional[DBaseWfmFont] = None
    order: int = 0


@dataclass
class DBaseWfmForm:
    class_name: str
    properties: Dict[str, object] = field(default_factory=dict)
    declared_properties: Dict[str, object] = field(default_factory=dict)
    controls: List[DBaseWfmControl] = field(default_factory=list)
    # Stage 111: die Root-FORM besitzt dieselben Font/Event-Metadaten wie Controls.
    font: Optional[DBaseWfmFont] = None
    events: Dict[str, str] = field(default_factory=dict)
    constructor_args: Tuple[object, ...] = ()
    init_args: Tuple[object, ...] = ()
    source: str = ""
    filename: str = "<WFM>"

    def control_by_path(self, path: str) -> Optional[DBaseWfmControl]:
        key = _wfm_normalize_path(path).casefold()
        for control in self.controls:
            if _wfm_normalize_path(control.path).casefold() == key:
                return control
        return None


def _wfm_normalize_path(path: str) -> str:
    value = re.sub(r"\s+", "", str(path or ""))
    if value.casefold() == "this":
        return "THIS"
    if value.casefold().startswith("this."):
        return "THIS." + value[5:]
    return value


def _wfm_split_args(text: str) -> List[str]:
    result: List[str] = []
    current: List[str] = []
    quote = ""
    depth = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            current.append(ch)
            if ch == quote:
                if i + 1 < len(text) and text[i + 1] == quote:
                    current.append(text[i + 1]); i += 1
                else:
                    quote = ""
        else:
            if ch in {'"', "'"}:
                quote = ch; current.append(ch)
            elif ch == '(':
                depth += 1; current.append(ch)
            elif ch == ')':
                depth = max(0, depth - 1); current.append(ch)
            elif ch == ',' and depth == 0:
                result.append(''.join(current).strip()); current = []
            else:
                current.append(ch)
        i += 1
    if current or text.strip():
        result.append(''.join(current).strip())
    return result


def _wfm_value(text: str) -> object:
    value = str(text).strip()
    low = value.casefold()
    if low in {".t.", "true"}:
        return True
    if low in {".f.", "false"}:
        return False
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        inner = value[1:-1]
        return inner.replace(value[0] * 2, value[0])
    try:
        if re.fullmatch(r"[+-]?\d+", value):
            return int(value)
        if re.fullmatch(r"[+-]?(?:\d+\.\d*|\d*\.\d+)", value):
            return float(value)
    except ValueError:
        pass
    return value


def _wfm_parse_font(expr: str) -> Optional[DBaseWfmFont]:
    m = re.fullmatch(r"(?is)NEW\s+FONT\s*\((.*)\)\s*", expr.strip())
    if not m:
        return None
    args = [_wfm_value(part) for part in _wfm_split_args(m.group(1))]
    family = str(args[0]) if args else "Arial"
    size = int(args[1]) if len(args) > 1 and isinstance(args[1], (int, float)) else 10
    # Template convention: NEW FONT(name,size,bold,italic,underline)
    bold = bool(args[2]) if len(args) > 2 else False
    italic = bool(args[3]) if len(args) > 3 else False
    underline = bool(args[4]) if len(args) > 4 else False
    return DBaseWfmFont(family, max(1, size), bold, italic, underline, False)


def parse_dbase_wfm(source: str, *, filename: str = "<WFM>") -> DBaseWfmForm:
    """Parse the dBase CLASS ... OF FORM subset used by *.wfm files.

    Supported OOP constructs: PARAMETER/LOCAL bootstrap, NEW FormClass(...),
    CLASS name OF FORM, PROPERTY, THIS member paths, NEW PUSHBUTTON/CONTAINER,
    WITH/ENDWITH, direct member assignments and NEW FONT(...). Stage 111
    parses Font/Event properties on the root FORM as well.
    """
    text = str(source).replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = text.split("\n")
    class_start = None
    class_name = None
    class_end = None
    for idx, raw in enumerate(raw_lines):
        code = raw.strip()
        if code.startswith("//") or code.startswith("**") or not code:
            continue
        m = re.match(r"(?i)^CLASS\s+([A-Za-z_]\w*)\s+OF\s+FORM\s*$", code)
        if m:
            class_start = idx; class_name = m.group(1); break
    if class_start is None or not class_name:
        raise DBaseCompilerError(
            "WFM erwartet 'CLASS <Name> OF FORM'.", line=1, column=1, filename=filename
        )
    for idx in range(class_start + 1, len(raw_lines)):
        if re.match(r"(?i)^\s*ENDCLASS\s*$", raw_lines[idx]):
            class_end = idx; break
    if class_end is None:
        raise DBaseCompilerError(
            f"CLASS {class_name} OF FORM besitzt kein ENDCLASS.",
            line=class_start + 1, column=1, filename=filename,
        )

    model = DBaseWfmForm(class_name=class_name, source=text, filename=filename)
    # Bootstrap arguments: B = NEW ParentForm(...), B.Init(...)
    for raw in raw_lines[:class_start]:
        code = raw.split("//", 1)[0].strip()
        m = re.match(rf"(?i)^\w+\s*=\s*NEW\s+{re.escape(class_name)}\s*\((.*)\)\s*$", code)
        if m:
            model.constructor_args = tuple(_wfm_value(x) for x in _wfm_split_args(m.group(1)))
        m = re.match(r"(?i)^\w+\.Init\s*\((.*)\)\s*$", code)
        if m:
            model.init_args = tuple(_wfm_value(x) for x in _wfm_split_args(m.group(1)))

    controls: Dict[str, DBaseWfmControl] = {}
    order = 0
    with_target: Optional[str] = None

    def get_control(path: str) -> Optional[DBaseWfmControl]:
        return controls.get(_wfm_normalize_path(path).casefold())

    def set_assignment(target_path: str, prop_name: str, rhs: str, line_no: int) -> None:
        target_path = _wfm_normalize_path(target_path)
        prop = str(prop_name).strip()
        if target_path.casefold() == "this":
            if prop.casefold().startswith("on"):
                model.events[prop] = rhs.strip()
                return
            if prop.casefold() == "font":
                font = _wfm_parse_font(rhs)
                if font is not None:
                    model.font = font
                    return
            model.properties[prop] = _wfm_value(rhs)
            return
        if target_path.casefold() == "this.font":
            if model.font is None:
                model.font = DBaseWfmFont()
            key = prop.casefold()
            val = _wfm_value(rhs)
            if key == "bold": model.font.bold = bool(val)
            elif key == "italic": model.font.italic = bool(val)
            elif key == "underline": model.font.underline = bool(val)
            elif key in {"strikeout", "stroke"}: model.font.strikeout = bool(val)
            return
        control = get_control(target_path)
        if control is None:
            # A nested Font member such as THIS.PushButton2.Font.bold.
            fm = re.match(r"(?i)^(THIS(?:\.\w+)+)\.Font$", target_path)
            if fm:
                control = get_control(fm.group(1))
                if control is not None:
                    if control.font is None:
                        control.font = DBaseWfmFont()
                    key = prop.casefold()
                    val = _wfm_value(rhs)
                    if key == "bold": control.font.bold = bool(val)
                    elif key == "italic": control.font.italic = bool(val)
                    elif key == "underline": control.font.underline = bool(val)
                    elif key in {"strikeout", "stroke"}: control.font.strikeout = bool(val)
                    return
            return
        if prop.casefold().startswith("on"):
            control.events[prop] = rhs.strip()
            return
        if prop.casefold() == "font":
            font = _wfm_parse_font(rhs)
            if font is not None:
                control.font = font
                return
        control.properties[prop] = _wfm_value(rhs)

    idx = class_start + 1
    while idx < class_end:
        raw = raw_lines[idx]
        code = raw.split("//", 1)[0].strip()
        line_no = idx + 1
        idx += 1
        if not code or code.startswith("**"):
            continue
        m = re.match(r"(?i)^PROPERTY\s+([A-Za-z_]\w*)\s*=\s*(.+)$", code)
        if m:
            model.declared_properties[m.group(1)] = _wfm_value(m.group(2)); continue
        m = re.match(r"(?i)^WITH\s*\(\s*(THIS(?:\.\w+)*)\s*\)\s*$", code)
        if m:
            with_target = _wfm_normalize_path(m.group(1)); continue
        if re.match(r"(?i)^ENDWITH\s*$", code):
            with_target = None; continue
        m = re.match(
            r"(?i)^(THIS(?:\.\w+)+)\s*=\s*NEW\s+([A-Za-z_]\w*)\s*\(\s*(THIS(?:\.\w+)*)\s*\)\s*$",
            code,
        )
        if m:
            path = _wfm_normalize_path(m.group(1)); cls = m.group(2).upper(); parent = _wfm_normalize_path(m.group(3))
            order += 1
            control = DBaseWfmControl(path=path, class_name=cls, parent_path=parent, order=order)
            controls[path.casefold()] = control; model.controls.append(control); continue
        # Direct THIS.Path.Property = value. Greedy path split at final dot.
        m = re.match(r"(?i)^(THIS(?:\.\w+)+)\.([A-Za-z_]\w*)\s*=\s*(.+)$", code)
        if m:
            set_assignment(m.group(1), m.group(2), m.group(3), line_no); continue
        # Assignment inside WITH target.
        m = re.match(r"(?i)^([A-Za-z_]\w*)\s*=\s*(.+)$", code)
        if m and with_target:
            set_assignment(with_target, m.group(1), m.group(2), line_no); continue
        # Font.bold = .F. inside WITH(THIS.Control)
        m = re.match(r"(?i)^Font\.([A-Za-z_]\w*)\s*=\s*(.+)$", code)
        if m and with_target:
            set_assignment(with_target + ".Font", m.group(1), m.group(2), line_no); continue
        # Unknown method/event implementation lines are deliberately retained by
        # the source but do not prevent the first Form/OOP stage from loading.

    return model



__all__ = [
    "DBaseWfmError",
    "DBaseWfmFont",
    "DBaseWfmControl",
    "DBaseWfmForm",
    "parse_dbase_wfm",
]
