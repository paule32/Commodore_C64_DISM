# dBase WFM / FORM OOP parser
# Stage 120 - structured nested property scopes

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


DBaseCompilerError = DBaseWfmError


@dataclass
class DBaseWfmFont:
    family: str = "Arial"
    size: int = 10
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikeout: bool = False
    alpha: int = 255
    background: str = "#FFFFFF"
    foreground: str = "#000000"

    def copy(self):
        return DBaseWfmFont(
            self.family, self.size, self.bold, self.italic,
            self.underline, self.strikeout, self.alpha,
            self.background, self.foreground,
        )


@dataclass
class DBaseWfmFontObject:
    path: str
    font: DBaseWfmFont = field(default_factory=DBaseWfmFont)
    order: int = 0


@dataclass
class DBaseWfmMethod:
    name: str
    kind: str = "procedure"
    parameters: Tuple[str, ...] = ()
    body: List[str] = field(default_factory=list)
    return_expr: str = ""
    order: int = 0
    # Stage 132: originaler PROCEDURE/FUNCTION-Block. Diese Zeilen werden
    # zusätzlich als UTF-8-Daten in die fertige WFM-EXE gelinkt.
    source_lines: List[str] = field(default_factory=list)
    source_start_line: int = 0


@dataclass
class DBaseWfmControl:
    path: str
    class_name: str
    parent_path: str
    properties: Dict[str, object] = field(default_factory=dict)
    events: Dict[str, str] = field(default_factory=dict)
    font: Optional[DBaseWfmFont] = None
    font_ref: str = ""
    constructor_args: Tuple[object, ...] = ()
    order: int = 0


@dataclass
class DBaseWfmForm:
    class_name: str
    properties: Dict[str, object] = field(default_factory=dict)
    declared_properties: Dict[str, object] = field(default_factory=dict)
    controls: List[DBaseWfmControl] = field(default_factory=list)
    font: Optional[DBaseWfmFont] = None
    font_ref: str = ""
    font_objects: Dict[str, DBaseWfmFontObject] = field(default_factory=dict)
    methods: List[DBaseWfmMethod] = field(default_factory=list)
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

    def font_object_by_path(self, path: str) -> Optional[DBaseWfmFontObject]:
        return self.font_objects.get(_wfm_normalize_path(path).casefold())

    def method_by_name(self, name: str) -> Optional[DBaseWfmMethod]:
        key = str(name).casefold()
        for method in self.methods:
            if method.name.casefold() == key:
                return method
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
                    current.append(text[i + 1])
                    i += 1
                else:
                    quote = ""
        else:
            if ch in {'"', "'"}:
                quote = ch
                current.append(ch)
            elif ch == '(':
                depth += 1
                current.append(ch)
            elif ch == ')':
                depth = max(0, depth - 1)
                current.append(ch)
            elif ch == ',' and depth == 0:
                result.append(''.join(current).strip())
                current = []
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
    bold = bool(args[2]) if len(args) > 2 else False
    italic = bool(args[3]) if len(args) > 3 else False
    # Stage 120: FONT(name,size,bold,cursive,stroke,underline).
    # Legacy five-argument files used the fifth argument as underline.
    if len(args) >= 6:
        strikeout = bool(args[4])
        underline = bool(args[5])
    else:
        strikeout = False
        underline = bool(args[4]) if len(args) > 4 else False
    return DBaseWfmFont(
        family=family,
        size=max(1, size),
        bold=bold,
        italic=italic,
        underline=underline,
        strikeout=strikeout,
    )


def _wfm_resolve_with(expr: str, stack: List[str]) -> str:
    target = _wfm_normalize_path(expr)
    if not stack:
        return target
    current = stack[-1]
    if current.casefold() == "this":
        return target
    if target.casefold() == "this":
        return current
    if target.casefold().startswith("this."):
        # Nested WITH(THIS.X) is relative to the active WITH scope.
        return current + target[4:]
    return current + "." + target


def parse_dbase_wfm(source: str, *, filename: str = "<WFM>") -> DBaseWfmForm:
    """Parse dBase CLASS ... OF FORM including Stage-120 structured properties.

    Nested scopes are normalized to the legacy flat designer property names so
    old and new WFM files share one designer/compiler/runtime path.
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
            class_start = idx
            class_name = m.group(1)
            break
    if class_start is None or not class_name:
        raise DBaseCompilerError("WFM erwartet 'CLASS <Name> OF FORM'.", line=1, column=1, filename=filename)
    for idx in range(class_start + 1, len(raw_lines)):
        if re.match(r"(?i)^\s*ENDCLASS\s*$", raw_lines[idx]):
            class_end = idx
            break
    if class_end is None:
        raise DBaseCompilerError(
            f"CLASS {class_name} OF FORM besitzt kein ENDCLASS.",
            line=class_start + 1, column=1, filename=filename,
        )

    model = DBaseWfmForm(class_name=class_name, source=text, filename=filename)
    for raw in raw_lines[:class_start]:
        code = raw.split("//", 1)[0].strip()
        m = re.match(rf"(?i)^\w+\s*=\s*NEW\s+{re.escape(class_name)}\s*\((.*)\)\s*$", code)
        if m:
            model.constructor_args = tuple(_wfm_value(x) for x in _wfm_split_args(m.group(1)))
        m = re.match(r"(?i)^\w+\.Init\s*\((.*)\)\s*$", code)
        if m:
            model.init_args = tuple(_wfm_value(x) for x in _wfm_split_args(m.group(1)))

    controls: Dict[str, DBaseWfmControl] = {}
    font_objects: Dict[str, DBaseWfmFontObject] = {}
    with_stack: List[str] = []
    order = 0
    method_order = 0
    current_method: Optional[DBaseWfmMethod] = None

    def get_control(path: str) -> Optional[DBaseWfmControl]:
        return controls.get(_wfm_normalize_path(path).casefold())

    def get_font_object(path: str) -> Optional[DBaseWfmFontObject]:
        return font_objects.get(_wfm_normalize_path(path).casefold())

    def find_control_base(path: str):
        norm = _wfm_normalize_path(path)
        parts = norm.split('.')
        for end in range(len(parts), 1, -1):
            candidate = '.'.join(parts[:end])
            control = get_control(candidate)
            if control is not None:
                suffix = '.'.join(parts[end:])
                return control, suffix
        return None, ""

    def ensure_font(owner):
        if getattr(owner, "font", None) is None:
            owner.font = DBaseWfmFont()
        return owner.font

    def set_font_value(owner, props: Dict[str, object], prop: str, rhs: str):
        font = ensure_font(owner)
        key = prop.casefold()
        val = _wfm_value(rhs)
        if key in {"name", "family"}:
            font.family = str(val)
        elif key == "size":
            font.size = max(1, int(round(float(val))))
        elif key == "bold":
            font.bold = bool(val)
        elif key in {"cursive", "italic"}:
            font.italic = bool(val)
        elif key in {"stroke", "strikeout"}:
            font.strikeout = bool(val)
        elif key == "underline":
            font.underline = bool(val)
        elif key == "alpha":
            font.alpha = max(0, min(255, int(round(float(val)))))
            props["FontAlpha"] = font.alpha
        elif key == "background":
            font.background = str(val)
            props["FontBackground"] = val
        elif key == "foreground":
            font.foreground = str(val)
            props["FontForeground"] = val

    def nested_property_name(subpath: str, prop: str):
        sub = subpath.casefold().strip('.')
        key = prop.casefold()
        if sub == "brush":
            return {
                "background": "BackColor",
                "foreground": "ForeColor",
                "gradient": "BrushGradient",
            }.get(key)
        if sub in {"brush.style", "style"}:
            return {
                "pattern": "BrushStyle",
                "cutwidth": "BrushCutWidth",
                "cutheight": "BrushCutHeight",
            }.get(key)
        if sub == "border":
            return {"style": "BorderStyle", "size": "BorderWidth", "color": "BorderColor"}.get(key)
        if sub in {"border.shadow", "shadow"}:
            return "ShadowColor" if key == "color" else None
        if sub in {"border.rounded", "rounded"}:
            return {
                "topleft": "BorderRoundedTL", "topright": "BorderRoundedTR",
                "bottomleft": "BorderRoundedBL", "bottomright": "BorderRoundedBR",
            }.get(key)
        for side in ("left", "top", "right", "bottom"):
            if sub in {f"border.{side}", side}:
                label = side.capitalize()
                return {
                    "enabled": f"Border{label}",
                    "style": f"Border{label}Style",
                    "size": f"Border{label}Size",
                    "color": f"Border{label}Color",
                }.get(key)
        return None

    def assign_to_owner(owner, props: Dict[str, object], events: Dict[str, str], subpath: str, prop: str, rhs: str):
        sub = subpath.casefold().strip('.')
        key = prop.casefold()
        if sub == "font":
            set_font_value(owner, props, prop, rhs)
            return True
        mapped = nested_property_name(subpath, prop)
        if mapped:
            props[mapped] = _wfm_value(rhs)
            return True
        if not sub:
            if key.startswith("on"):
                event_value = rhs.strip()
                legacy_event = re.match(
                    r"(?i)^CLASS\*?::\s*([A-Za-z_]\w*)$",
                    event_value,
                )
                if legacy_event:
                    event_value = "CLASS::" + legacy_event.group(1)
                events[prop] = event_value
                return True
            if key == "font":
                font = _wfm_parse_font(rhs)
                if font is not None:
                    owner.font = font
                    return True
                ref = _wfm_normalize_path(rhs)
                if ref.casefold().startswith("this."):
                    owner.font_ref = ref
                    return True
            props[prop] = _wfm_value(rhs)
            return True
        return False

    def set_assignment(target_path: str, prop_name: str, rhs: str, line_no: int) -> None:
        target_path = _wfm_normalize_path(target_path)
        prop = str(prop_name).strip()
        if target_path.casefold() == "this":
            assign_to_owner(model, model.properties, model.events, "", prop, rhs)
            return
        if target_path.casefold().startswith("this."):
            # Named FONT object first.
            fobj = get_font_object(target_path)
            if fobj is not None:
                set_font_value(fobj, {}, prop, rhs)
                return
            # Root nested properties.
            root_suffix = target_path[5:]
            root_first = root_suffix.split('.', 1)[0].casefold()
            if root_first in {"font", "brush", "border", "style", "shadow", "rounded", "left", "top", "right", "bottom"}:
                assign_to_owner(model, model.properties, model.events, root_suffix, prop, rhs)
                return
        control, suffix = find_control_base(target_path)
        if control is not None:
            assign_to_owner(control, control.properties, control.events, suffix, prop, rhs)
            return

    idx = class_start + 1
    while idx < class_end:
        raw = raw_lines[idx]
        code = raw.split("//", 1)[0].strip()
        line_no = idx + 1
        idx += 1
        if not code or code.startswith("**"):
            continue

        # Method body: ends implicitly at next procedure/function or ENDCLASS.
        method_match = re.match(
            r"(?i)^(procedure|function)\s+([A-Za-z_]\w*)"
            r"\s*(?:\(([^)]*)\))?\s*$",
            code,
        )
        if method_match:
            method_order += 1
            params = tuple(
                p.strip()
                for p in (method_match.group(3) or "").split(",")
                if p.strip()
            )
            current_method = DBaseWfmMethod(
                name=method_match.group(2),
                kind=method_match.group(1).lower(),
                parameters=params,
                order=method_order,
                source_lines=[raw.rstrip()],
                source_start_line=line_no,
            )
            model.methods.append(current_method)
            with_stack.clear()
            continue
        if current_method is not None:
            current_method.source_lines.append(raw.rstrip())
            mret = re.match(r"(?i)^return(?:\s+(.+))?$", code)
            if mret:
                current_method.return_expr = (mret.group(1) or "").strip()
                current_method.body.append(code)
                current_method = None
                continue
            current_method.body.append(raw.rstrip())
            continue

        m = re.match(r"(?i)^PROPERTY\s+([A-Za-z_]\w*)\s*=\s*(.+)$", code)
        if m:
            model.declared_properties[m.group(1)] = _wfm_value(m.group(2))
            continue

        m = re.match(r"(?i)^WITH\s*\(\s*(THIS(?:\.\w+)*)\s*\)\s*$", code)
        if m:
            with_stack.append(_wfm_resolve_with(m.group(1), with_stack))
            continue
        if re.match(r"(?i)^ENDWIT(?:H)?\s*$", code):
            if with_stack:
                with_stack.pop()
            continue

        # Named FONT resource: THIS.FONT1 = NEW FONT(...)
        m = re.match(r"(?i)^(THIS(?:\.\w+)+)\s*=\s*(NEW\s+FONT\s*\(.*\))\s*$", code)
        if m:
            lhs = _wfm_normalize_path(m.group(1))
            if with_stack and with_stack[-1].casefold() != "this" and lhs.count('.') == 1:
                lhs = with_stack[-1] + lhs[4:]
            font = _wfm_parse_font(m.group(2)) or DBaseWfmFont()
            order += 1
            obj = DBaseWfmFontObject(path=lhs, font=font, order=order)
            font_objects[lhs.casefold()] = obj
            model.font_objects[lhs.casefold()] = obj
            continue

        # Component construction supports parent default THIS and optional text.
        m = re.match(r"(?i)^(THIS(?:\.\w+)+)\s*=\s*NEW\s+([A-Za-z_]\w*)\s*\((.*)\)\s*$", code)
        if m and m.group(2).casefold() != "font":
            path = _wfm_normalize_path(m.group(1))
            cls = m.group(2).upper()
            arg_text = m.group(3).strip()
            raw_args = _wfm_split_args(arg_text) if arg_text else []
            args = tuple(_wfm_value(x) for x in raw_args)
            parent = "THIS"
            if raw_args and _wfm_normalize_path(raw_args[0]).casefold().startswith("this"):
                parent = _wfm_normalize_path(raw_args[0])
            order += 1
            control = DBaseWfmControl(
                path=path, class_name=cls, parent_path=parent,
                constructor_args=args, order=order,
            )
            if len(args) > 1 and isinstance(args[1], str):
                control.properties["Text"] = args[1]
            controls[path.casefold()] = control
            model.controls.append(control)
            continue

        # Generic assignment.
        m = re.match(r"(?i)^(.+?)\s*=\s*(.+)$", code)
        if m:
            lhs = m.group(1).strip()
            rhs = m.group(2).strip()
            scope = with_stack[-1] if with_stack else ""

            if re.match(r"(?i)^[A-Za-z_]\w*$", lhs) and scope:
                set_assignment(scope, lhs, rhs, line_no)
                continue

            if lhs.casefold().startswith("font.") and scope:
                set_assignment(scope + ".Font", lhs.split('.', 1)[1], rhs, line_no)
                continue

            if lhs.casefold().startswith("this."):
                # In a nested WITH, THIS.X denotes X below the active scope.
                resolved_lhs = _wfm_normalize_path(lhs)
                if scope and scope.casefold() != "this" and resolved_lhs.count('.') == 1:
                    resolved_lhs = scope + resolved_lhs[4:]
                if '.' in resolved_lhs:
                    target, prop = resolved_lhs.rsplit('.', 1)
                    set_assignment(target, prop, rhs, line_no)
                    continue

    # Resolve shared FONT references after all FONT objects are known.
    def resolve_font(owner, props):
        ref = _wfm_normalize_path(getattr(owner, "font_ref", ""))
        if not ref:
            return
        obj = get_font_object(ref)
        if obj is None:
            return
        owner.font = obj.font.copy()
        props["FontAlpha"] = owner.font.alpha
        props["FontBackground"] = owner.font.background
        props["FontForeground"] = owner.font.foreground

    resolve_font(model, model.properties)
    for control in model.controls:
        resolve_font(control, control.properties)

    return model


__all__ = [
    "DBaseWfmError",
    "DBaseWfmFont",
    "DBaseWfmFontObject",
    "DBaseWfmMethod",
    "DBaseWfmControl",
    "DBaseWfmForm",
    "parse_dbase_wfm",
]
