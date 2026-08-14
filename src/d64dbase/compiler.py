from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from datetime import datetime
from pathlib import Path
import ast
import os
import re
import struct
from typing import Dict, Mapping, Optional, Tuple, Union


class DBaseCompilerError(Exception):
    """Fehler des dBase-Frontends.

    Zeile und Spalte sind 1-basiert und beziehen sich immer auf den
    unveränderten Originalquelltext.
    """

    def __init__(
        self,
        message: str,
        line: int = 0,
        column: int = 0,
        filename: str = "<dBase>",
    ) -> None:
        self.message = str(message)
        self.line = int(line or 0)
        self.column = int(column or 0)
        self.filename = str(filename or "<dBase>")
        super().__init__(self.message)

    def __str__(self) -> str:
        location = self.filename
        if self.line:
            location += f":{self.line}"
            if self.column:
                location += f":{self.column}"
        return f"{location}: {self.message}"


@dataclass(frozen=True)
class DBaseComment:
    kind: str
    marker: str
    text: str
    start_offset: int
    end_offset: int
    start_line: int
    start_column: int
    end_line: int
    end_column: int


@dataclass(frozen=True)
class DBaseMacro:
    name: str
    parameters: Optional[Tuple[str, ...]]
    body: str
    line: int
    column: int

    @property
    def function_like(self) -> bool:
        return self.parameters is not None


@dataclass(frozen=True)
class DBasePragmaLink:
    path: str
    raw_path: str
    line: int
    column: int


@dataclass(frozen=True)
class DBaseFrontendResult:
    source: str
    comment_free_source: str
    comments: Tuple[DBaseComment, ...]
    target: str
    filename: str = "<dBase>"
    preprocessed_source: str = ""
    macros: Tuple[DBaseMacro, ...] = ()
    pragma_links: Tuple[DBasePragmaLink, ...] = ()
    preprocessor_warnings: Tuple[str, ...] = ()
    preprocessor_infos: Tuple[str, ...] = ()


@dataclass(frozen=True)
class DBaseCompileResult:
    assembly: str
    target: str
    windows_application_mode: str
    source_kind: str = "program"
    notes: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    linked_assembly_files: Tuple[str, ...] = ()
    linked_pe32_modules: Tuple[Tuple[str, str], ...] = ()
    linked_object_files: Tuple[str, ...] = ()
    frontend: Optional[DBaseFrontendResult] = None
    statements: Tuple[object, ...] = ()
    transcript: str = ""
    debug_transcript: str = ""
    uses_debug_output: bool = False
    variables: Tuple["DBaseVariableInfo", ...] = ()
    external_functions: Tuple[str, ...] = ()


@dataclass(frozen=True)
class DBaseToken:
    kind: str
    text: str
    value: object
    line: int
    column: int
    offset: int


@dataclass(frozen=True)
class DBaseExpression:
    line: int
    column: int


@dataclass(frozen=True)
class DBaseLiteralExpression(DBaseExpression):
    value_type: str
    value: object
    text: str


@dataclass(frozen=True)
class DBaseIdentifierExpression(DBaseExpression):
    name: str


@dataclass(frozen=True)
class DBaseCallExpression(DBaseExpression):
    name: str
    arguments: Tuple[DBaseExpression, ...]


@dataclass(frozen=True)
class DBaseUnaryExpression(DBaseExpression):
    operator: str
    operand: DBaseExpression


@dataclass(frozen=True)
class DBaseBinaryExpression(DBaseExpression):
    operator: str
    left: DBaseExpression
    right: DBaseExpression


@dataclass(frozen=True)
class DBasePrintStatement:
    expression: DBaseExpression
    newline: bool
    line: int
    column: int


@dataclass(frozen=True)
class DBaseAssignmentStatement:
    name: str
    expression: DBaseExpression
    line: int
    column: int


@dataclass(frozen=True)
class DBaseSetFormatStatement:
    target: str
    line: int
    column: int


@dataclass(frozen=True)
class DBaseSetDebugStatement:
    enabled: bool
    line: int
    column: int


@dataclass(frozen=True)
class DBaseSetColorStatement:
    spec: str
    line: int
    column: int


@dataclass(frozen=True)
class DBaseClearScreenStatement:
    expression: Optional[DBaseExpression]
    line: int
    column: int


@dataclass(frozen=True)
class DBaseSetBorderColorStatement:
    expression: DBaseExpression
    line: int
    column: int


@dataclass(frozen=True)
class DBaseReturnStatement:
    expression: Optional[DBaseExpression]
    line: int
    column: int


@dataclass(frozen=True)
class DBaseCallStatement:
    call: DBaseCallExpression
    line: int
    column: int


@dataclass(frozen=True)
class DBaseCondition:
    left: DBaseExpression
    operator: str
    right: DBaseExpression
    line: int
    column: int


@dataclass(frozen=True)
class DBaseIfBranch:
    condition: Optional[DBaseCondition]
    body: Tuple[object, ...]
    line: int
    column: int


@dataclass(frozen=True)
class DBaseIfStatement:
    branches: Tuple[DBaseIfBranch, ...]
    line: int
    column: int


@dataclass(frozen=True)
class DBaseRoutineDefinition:
    kind: str
    name: str
    parameters: Tuple[str, ...]
    body: Tuple[object, ...]
    line: int
    column: int

    @property
    def is_function(self) -> bool:
        return self.kind == "function"

    @property
    def is_procedure(self) -> bool:
        return self.kind == "procedure"


@dataclass(frozen=True)
class DBaseValue:
    kind: str
    value: object


@dataclass(frozen=True)
class DBaseVariableInfo:
    name: str
    label: str
    value_type: str
    constant_value: Optional[DBaseValue]
    dynamic: bool
    last_line: int
    last_column: int


@dataclass(frozen=True)
class _DBaseExpressionInfo:
    kind: str
    constant_value: Optional[DBaseValue]
    dynamic: bool
    variable_label: str = ""


@dataclass
class _DBaseSymbolState:
    name: str
    label: str
    value_type: str
    constant_value: Optional[DBaseValue]
    dynamic: bool
    last_line: int
    last_column: int


@dataclass(frozen=True)
class _DBaseCallBinding:
    kind: str
    target_label: str
    result_label: str
    argument_slots: Tuple[str, ...]
    parameter_slots: Tuple[str, ...]
    return_kind: str = ""


@dataclass
class _DBaseRoutineInstance:
    definition: DBaseRoutineDefinition
    signature: Tuple[str, ...]
    label: str
    parameter_symbols: Dict[str, _DBaseSymbolState]
    local_symbols: Dict[str, _DBaseSymbolState]
    expression_info: Dict[DBaseExpression, _DBaseExpressionInfo]
    call_bindings: Dict[DBaseCallExpression, _DBaseCallBinding]
    return_info: Optional[_DBaseExpressionInfo]
    result_label: str
    storage_slots: list[str]
    analyzing: bool = False


@dataclass(frozen=True)
class _DBaseAnalysis:
    expression_info: Mapping[DBaseExpression, _DBaseExpressionInfo]
    call_bindings: Mapping[DBaseCallExpression, _DBaseCallBinding]
    variables: Tuple[DBaseVariableInfo, ...]
    external_functions: Tuple[str, ...]
    console_transcript: str
    debug_transcript: str
    transcript_complete: bool
    uses_debug_output: bool
    routines: Mapping[str, DBaseRoutineDefinition]
    routine_instances: Tuple[_DBaseRoutineInstance, ...]
    storage_slots: Tuple[str, ...]


_LINE_MARKERS = ("//", "**", "&&")

_TARGET_ALIASES = {
    "pe32": "pe32",
    "win32": "pe32",
    "windows": "pe32",
    "windows32": "pe32",
    "windows-pe32": "pe32",
    "nt32": "pe32",
    "pe64": "pe64",
    "pe32+": "pe64",
    "win64": "pe64",
    "windows64": "pe64",
    "windows-pe64": "pe64",
    "windows-pe32+": "pe64",
    "amd64": "pe64",
    "x64": "pe64",
}


def normalize_dbase_target(value: str = "pe32") -> str:
    key = str(value or "pe32").strip().casefold()
    target = _TARGET_ALIASES.get(key)
    if target is None:
        raise DBaseCompilerError(
            "Der dBase-Compiler unterstützt ausschließlich Windows PE32 "
            "und Windows PE32+ (PE64/AMD64)."
        )
    return target


def normalize_dbase_windows_mode(value: str = "Console") -> str:
    key = str(value or "Console").strip().casefold()
    if key in {"console", "konsole", "cui"}:
        return "Console"
    if key in {"gui", "windows"}:
        return "GUI"
    raise DBaseCompilerError(
        "Unbekannter dBase-Windowsmodus. Erlaubt sind Console oder GUI."
    )


def _advance_position(fragment: str, line: int, column: int) -> tuple[int, int]:
    """Liefert die Position direkt hinter *fragment*.

    CRLF wird als ein logischer Zeilenumbruch behandelt. Einzelnes CR und LF
    funktionieren ebenfalls. Offsets bleiben trotzdem Python-String-Offets.
    """
    index = 0
    while index < len(fragment):
        char = fragment[index]
        if char == "\r":
            if index + 1 < len(fragment) and fragment[index + 1] == "\n":
                index += 1
            line += 1
            column = 1
        elif char == "\n":
            line += 1
            column = 1
        else:
            column += 1
        index += 1
    return line, column


def _blank_preserving_newlines(fragment: str) -> str:
    """Ersetzt Kommentarinhalt durch Leerzeichen, erhält CR/LF exakt."""
    return "".join(char if char in "\r\n" else " " for char in fragment)


def scan_dbase_comments(
    source: str,
    *,
    filename: str = "<dBase>",
) -> Tuple[DBaseComment, ...]:
    """Findet alle in Ausbaustufe 1 unterstützten dBase-Kommentare.

    Unterstützt werden exakt die gewünschten Formen::

        // Kommentar bis Zeilenende
        ** Kommentar bis Zeilenende
        && Kommentar bis Zeilenende
        /* Blockkommentar, auch über mehrere Zeilen */

    Ein Blockkommentar endet beim *ersten* folgenden ``*/``. Danach wird auf
    derselben Quellzeile sofort wieder normal lexikalisch weitergearbeitet.

    Kommentarstarter innerhalb von einfachen oder doppelten Stringliteralen
    werden nicht als Kommentar interpretiert. Verdoppelte Quotes (``''`` bzw.
    ``\"\"``) bleiben Bestandteil des Strings. Blockkommentare sind nicht
    verschachtelt.
    """
    text = str(source or "")
    comments: list[DBaseComment] = []
    length = len(text)
    index = 0
    line = 1
    column = 1
    quote: Optional[str] = None

    while index < length:
        char = text[index]

        # Stringmodus -----------------------------------------------------
        if quote is not None:
            if char == quote:
                # dBase/FoxPro-artige Verdopplung des Quote-Zeichens.
                if index + 1 < length and text[index + 1] == quote:
                    index += 2
                    column += 2
                    continue
                quote = None
                index += 1
                column += 1
                continue

            # Zusätzlich tolerant gegenüber C-artigen Escapes. Das bewahrt
            # spätere Dialekt-Erweiterungen davor, Kommentarzeichen in z.B.
            # "\\/*" fälschlich als Kommentar zu sehen.
            if (
                char == "\\"
                and index + 1 < length
                and text[index + 1] not in "\r\n"
            ):
                index += 2
                column += 2
                continue

            # Strings sind in dieser Vorstufe zeilenorientiert. Ein späterer
            # Parser darf einen fehlenden Abschluss separat diagnostizieren;
            # die Kommentarerkennung der nächsten Zeile darf dadurch nicht
            # verschluckt werden.
            if char == "\r":
                if index + 1 < length and text[index + 1] == "\n":
                    index += 2
                else:
                    index += 1
                line += 1
                column = 1
                quote = None
                continue
            if char == "\n":
                index += 1
                line += 1
                column = 1
                quote = None
                continue

            index += 1
            column += 1
            continue

        if char in {"'", '"'}:
            quote = char
            index += 1
            column += 1
            continue

        # Blockkommentar --------------------------------------------------
        if text.startswith("/*", index):
            start_offset = index
            start_line = line
            start_column = column
            close = text.find("*/", index + 2)
            if close < 0:
                raise DBaseCompilerError(
                    "Nicht abgeschlossener Blockkommentar; erwartet wird '*/'.",
                    line=start_line,
                    column=start_column,
                    filename=filename,
                )

            end_offset = close + 2
            fragment = text[start_offset:end_offset]
            end_line, end_column_after = _advance_position(
                fragment, start_line, start_column
            )
            comments.append(
                DBaseComment(
                    kind="block",
                    marker="/*",
                    text=fragment,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    start_line=start_line,
                    start_column=start_column,
                    end_line=end_line,
                    end_column=max(1, end_column_after - 1),
                )
            )
            line, column = end_line, end_column_after
            index = end_offset
            continue

        # Zeilenkommentar -------------------------------------------------
        marker = next(
            (
                candidate
                for candidate in _LINE_MARKERS
                if text.startswith(candidate, index)
            ),
            None,
        )
        if marker is not None:
            start_offset = index
            start_line = line
            start_column = column
            end_offset = index + len(marker)
            while end_offset < length and text[end_offset] not in "\r\n":
                end_offset += 1
            fragment = text[start_offset:end_offset]
            comments.append(
                DBaseComment(
                    kind="line",
                    marker=marker,
                    text=fragment,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    start_line=start_line,
                    start_column=start_column,
                    end_line=start_line,
                    end_column=start_column + max(0, len(fragment) - 1),
                )
            )
            # Der Zeilenumbruch selbst gehört nicht zum Kommentar und wird in
            # der nächsten Iteration normal verarbeitet.
            column += len(fragment)
            index = end_offset
            continue

        if char == "\r":
            if index + 1 < length and text[index + 1] == "\n":
                index += 2
            else:
                index += 1
            line += 1
            column = 1
            continue
        if char == "\n":
            index += 1
            line += 1
            column = 1
            continue

        index += 1
        column += 1

    return tuple(comments)


def strip_dbase_comments(
    source: str,
    *,
    filename: str = "<dBase>",
) -> str:
    """Entfernt Kommentare positionsstabil aus dBase-Quelltext.

    Jeder Nicht-Zeilenumbruch eines Kommentars wird durch genau ein Leerzeichen
    ersetzt. Dadurch bleiben Länge, Zeilennummern und Spalten aller folgenden
    Tokens exakt identisch zum Originalquelltext.
    """
    text = str(source or "")
    comments = scan_dbase_comments(text, filename=filename)
    if not comments:
        return text

    result: list[str] = []
    cursor = 0
    for comment in comments:
        result.append(text[cursor:comment.start_offset])
        result.append(
            _blank_preserving_newlines(
                text[comment.start_offset:comment.end_offset]
            )
        )
        cursor = comment.end_offset
    result.append(text[cursor:])
    cleaned = "".join(result)

    if len(cleaned) != len(text):
        raise AssertionError(
            "Interner Fehler: dBase-Kommentarpass änderte die Quelltextlänge."
        )
    return cleaned


def _blank_directive_line(text: str) -> str:
    return "".join(ch if ch in "\r\n" else " " for ch in text)


def _macro_number_text(text: str) -> Optional[str]:
    value = str(text or "").strip()
    if re.fullmatch(r"[+-]?\$[0-9A-Fa-f]+", value):
        sign = -1 if value.startswith("-") else 1
        payload = value.lstrip("+-")[1:]
        return str(sign * int(payload, 16))
    if re.fullmatch(r"[+-]?[0-9][0-9A-Fa-f]*[hH]", value):
        sign = -1 if value.startswith("-") else 1
        payload = value.lstrip("+-")[:-1]
        return str(sign * int(payload, 16))
    if re.fullmatch(r"[+-]?0[xX][0-9A-Fa-f]+", value):
        try:
            return str(int(value, 0))
        except ValueError:
            return None
    if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value):
        return value
    return None


def _macro_condition_scalar(name: str, macros: Mapping[str, DBaseMacro]) -> object:
    macro = macros.get(str(name).casefold())
    if macro is None:
        return 0
    if macro.function_like:
        return 1
    body = str(macro.body or "").strip()
    number = _macro_number_text(body)
    if number is not None:
        try:
            if any(ch in number for ch in ".eE"):
                return float(number)
            return int(number, 10)
        except ValueError:
            return 1
    if len(body) >= 2 and body[0] == body[-1] and body[0] in {"'", '"'}:
        # Python versteht die von dBase verwendeten einfachen/doppelten Quotes.
        try:
            return ast.literal_eval(body)
        except Exception:
            return body[1:-1]
    return 1


def _condition_to_python(
    expression: str,
    macros: Mapping[str, DBaseMacro],
    *,
    filename: str,
    line: int,
    compile_date: str,
    compile_time: str,
) -> str:
    text = str(expression or "")

    def replace_defined(match: re.Match[str]) -> str:
        # Erweiterte dBase-Semantik: defined(foo) liefert bei einem numerischen
        # Objektmakro dessen Wert. Damit ist '#if defined(foo) >= 5' fuer
        # '#define foo 5' sinnvoll. Bei nichtnumerischen Makros ist der Wert 1,
        # bei nicht definierten Makros 0.
        value = _macro_condition_scalar(match.group(1), macros)
        return repr(value)

    text = re.sub(
        r"\bdefined\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)",
        replace_defined,
        text,
        flags=re.IGNORECASE,
    )
    text = text.replace("&&", " and ").replace("||", " or ")
    text = re.sub(r"!(?!=)", " not ", text)

    # Identifikatoren ausserhalb von Stringliteralen durch Makrowerte ersetzen.
    result: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in {"'", '"'}:
            quote = ch
            j = i + 1
            while j < len(text):
                if text[j] == quote:
                    if j + 1 < len(text) and text[j + 1] == quote:
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            result.append(text[i:j])
            i = j
            continue
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", text[i:])
        if m:
            word = m.group(0)
            low = word.casefold()
            if low in {"and", "or", "not", "true", "false"}:
                result.append({"true": "True", "false": "False"}.get(low, low))
            elif low == "__line__":
                result.append(repr(int(line)))
            elif low == "__file__":
                result.append(repr(str(filename)))
            elif low == "__date__":
                result.append(repr(str(compile_date)))
            elif low == "__time__":
                result.append(repr(str(compile_time)))
            else:
                result.append(repr(_macro_condition_scalar(word, macros)))
            i += len(word)
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def _safe_eval_macro_condition(
    expression: str,
    macros: Mapping[str, DBaseMacro],
    *,
    filename: str,
    line: int,
    compile_date: str,
    compile_time: str,
) -> bool:
    pyexpr = _condition_to_python(
        expression, macros, filename=filename, line=line,
        compile_date=compile_date, compile_time=compile_time,
    ).strip()
    if not pyexpr:
        raise DBaseCompilerError("Leerer Makro-Ausdruck.", line=line, column=1, filename=filename)
    try:
        tree = ast.parse(pyexpr, mode="eval")
    except SyntaxError as exc:
        raise DBaseCompilerError(
            f"Ungueltiger Makro-Ausdruck: {expression}",
            line=line,
            column=(exc.offset or 1),
            filename=filename,
        ) from None

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (bool, int, float, str)):
                return node.value
        if isinstance(node, ast.UnaryOp):
            value = ev(node.operand)
            if isinstance(node.op, ast.Not): return not bool(value)
            if isinstance(node.op, ast.UAdd): return +value
            if isinstance(node.op, ast.USub): return -value
        if isinstance(node, ast.BoolOp):
            values = [bool(ev(item)) for item in node.values]
            if isinstance(node.op, ast.And): return all(values)
            if isinstance(node.op, ast.Or): return any(values)
        if isinstance(node, ast.BinOp):
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div): return left / right
            if isinstance(node.op, ast.FloorDiv): return left // right
            if isinstance(node.op, ast.Mod): return left % right
        if isinstance(node, ast.Compare):
            left = ev(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = ev(comparator)
                if isinstance(op, ast.Eq): ok = left == right
                elif isinstance(op, ast.NotEq): ok = left != right
                elif isinstance(op, ast.Lt): ok = left < right
                elif isinstance(op, ast.LtE): ok = left <= right
                elif isinstance(op, ast.Gt): ok = left > right
                elif isinstance(op, ast.GtE): ok = left >= right
                else: raise ValueError
                if not ok: return False
                left = right
            return True
        raise ValueError

    try:
        return bool(ev(tree))
    except (ValueError, TypeError, ZeroDivisionError):
        raise DBaseCompilerError(
            f"Nicht unterstuetzter Makro-Ausdruck: {expression}",
            line=line,
            column=1,
            filename=filename,
        ) from None


def _parse_macro_call_arguments(text: str, open_index: int) -> Tuple[Tuple[str, ...], int]:
    depth = 0
    quote = ""
    args: list[str] = []
    start = open_index + 1
    i = open_index
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == quote:
                if i + 1 < len(text) and text[i + 1] == quote:
                    i += 2
                    continue
                quote = ""
            i += 1
            continue
        if ch in {"'", '"'}:
            quote = ch
            i += 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                payload = text[start:i]
                if payload.strip() or args:
                    args.append(payload)
                return tuple(args), i + 1
        elif ch == "," and depth == 1:
            args.append(text[start:i])
            start = i + 1
        i += 1
    return (), -1


def _quote_dbase_predefined_string(value: str) -> str:
    # Der dBase-Stringlexer kennt Backslash-Escapes. Fuer __FILE__ muessen
    # Windows-Pfade daher zuerst \ -> \\ maskiert werden; doppelte Quotes
    # werden wie bei normalen dBase-Stringliteralen verdoppelt.
    escaped = str(value).replace("\\", "\\\\").replace('"', '""')
    return '"' + escaped + '"'


def _predefined_macro_text(
    name: str,
    *,
    filename: str,
    line: int,
    compile_date: str,
    compile_time: str,
) -> Optional[str]:
    key = str(name).casefold()
    if key == "__line__":
        return str(int(line))
    if key == "__file__":
        return _quote_dbase_predefined_string(str(filename))
    if key == "__date__":
        return _quote_dbase_predefined_string(str(compile_date))
    if key == "__time__":
        return _quote_dbase_predefined_string(str(compile_time))
    return None


def _substitute_function_macro(
    macro: DBaseMacro,
    args: Tuple[str, ...],
    macros: Mapping[str, DBaseMacro],
    disabled: frozenset[str],
    depth: int,
    *,
    filename: str,
    line: int,
    compile_date: str,
    compile_time: str,
) -> str:
    params = macro.parameters or ()
    if len(args) != len(params):
        return macro.name + "(" + ",".join(args) + ")"
    mapping = {
        param.casefold(): _expand_dbase_macro_text(
            arg.strip(), macros, disabled=disabled, depth=depth + 1,
            filename=filename, line=line, compile_date=compile_date, compile_time=compile_time
        )[0]
        for param, arg in zip(params, args)
    }
    body = macro.body

    def repl(match: re.Match[str]) -> str:
        return mapping.get(match.group(0).casefold(), match.group(0))

    body = re.sub(r"[A-Za-z_][A-Za-z0-9_]*", repl, body)
    # C-artiges Token-Pasting / concatenate macro.
    while "##" in body:
        body = re.sub(r"\s*##\s*", "", body, count=1)
    return _expand_dbase_macro_text(
        body, macros, disabled=disabled, depth=depth + 1,
        filename=filename, line=line, compile_date=compile_date, compile_time=compile_time
    )[0]


def _expand_dbase_macro_text(
    text: str,
    macros: Mapping[str, DBaseMacro],
    *,
    disabled: frozenset[str] = frozenset(),
    depth: int = 0,
    in_block_comment: bool = False,
    filename: str = "<dBase>",
    line: int = 1,
    compile_date: str = "",
    compile_time: str = "",
) -> Tuple[str, bool]:
    if depth > 64:
        return text, in_block_comment
    out: list[str] = []
    i = 0
    while i < len(text):
        if in_block_comment:
            end = text.find("*/", i)
            if end < 0:
                out.append(text[i:])
                return "".join(out), True
            out.append(text[i:end + 2])
            i = end + 2
            in_block_comment = False
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                out.append(text[i:])
                return "".join(out), True
            out.append(text[i:end + 2])
            i = end + 2
            continue
        if text.startswith("//", i) or text.startswith("**", i) or text.startswith("&&", i):
            out.append(text[i:])
            break
        ch = text[i]
        if ch in {"'", '"'}:
            quote = ch
            j = i + 1
            while j < len(text):
                if text[j] == quote:
                    if j + 1 < len(text) and text[j + 1] == quote:
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            out.append(text[i:j])
            i = j
            continue
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", text[i:])
        if m:
            word = m.group(0)
            key = word.casefold()
            predefined = _predefined_macro_text(
                word, filename=filename, line=line,
                compile_date=compile_date, compile_time=compile_time,
            )
            if predefined is not None:
                out.append(predefined)
                i += len(word)
                continue
            macro = macros.get(key)
            if macro is None or key in disabled:
                out.append(word)
                i += len(word)
                continue
            if macro.function_like:
                j = i + len(word)
                while j < len(text) and text[j].isspace() and text[j] not in "\r\n":
                    j += 1
                if j >= len(text) or text[j] != "(":
                    out.append(word)
                    i += len(word)
                    continue
                args, after = _parse_macro_call_arguments(text, j)
                if after < 0:
                    out.append(word)
                    i += len(word)
                    continue
                replacement = _substitute_function_macro(
                    macro, args, macros, disabled | {key}, depth,
                    filename=filename, line=line,
                    compile_date=compile_date, compile_time=compile_time,
                )
                out.append(replacement)
                i = after
                continue
            replacement, _ = _expand_dbase_macro_text(
                macro.body, macros, disabled=disabled | {key}, depth=depth + 1,
                filename=filename, line=line,
                compile_date=compile_date, compile_time=compile_time,
            )
            out.append(replacement)
            i += len(word)
            continue
        out.append(ch)
        i += 1
    return "".join(out), in_block_comment


@dataclass
class _DBaseConditionalFrame:
    parent_active: bool
    condition_true: bool
    else_seen: bool
    macros_before: Dict[str, DBaseMacro]


def _resolve_pragma_link_path(raw: str, *, filename: str, line: int) -> DBasePragmaLink:
    value = str(raw or "").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    if not value:
        raise DBaseCompilerError("#pragma link erwartet einen Pfad.", line=line, column=1, filename=filename)
    value = os.path.expandvars(os.path.expanduser(value))
    path = Path(value)
    source_path = Path(filename)
    if not path.is_absolute():
        base = source_path.parent if filename and not str(filename).startswith("<") else Path.cwd()
        path = base / path
    path = path.resolve()
    if path.suffix.casefold() not in {".o", ".obj", ".a", ".lib"}:
        raise DBaseCompilerError(
            "#pragma link unterstuetzt .o, .obj, .a und .lib.",
            line=line, column=1, filename=filename,
        )
    return DBasePragmaLink(str(path), raw, line, 1)


def _preprocess_dbase_macros(source: str, *, filename: str) -> Tuple[str, Tuple[DBaseMacro, ...], Tuple[DBasePragmaLink, ...], Tuple[str, ...], Tuple[str, ...]]:
    # Kommentare werden nur fuer die Direktiverkennung positionsstabil maskiert;
    # der ausgegebene aktive Code behaelt Kommentare bei, damit die bestehende
    # dBase-Kommentarlogik inklusive mehrzeiliger Blockkommentare unveraendert bleibt.
    masked = strip_dbase_comments(source, filename=filename)
    original_lines = source.splitlines(keepends=True)
    masked_lines = masked.splitlines(keepends=True)
    macros: Dict[str, DBaseMacro] = {}
    links: list[DBasePragmaLink] = []
    warnings: list[str] = []
    infos: list[str] = []
    stack: list[_DBaseConditionalFrame] = []
    output: list[str] = []
    active = True
    block_state = False
    compile_now = datetime.now()
    compile_date = f"{compile_now:%b} {compile_now.day:2d} {compile_now:%Y}"
    compile_time = compile_now.strftime("%H:%M:%S")

    for line_no, (orig_line, masked_line) in enumerate(zip(original_lines, masked_lines), 1):
        body = masked_line.rstrip("\r\n")
        stripped = body.lstrip()
        directive = stripped.startswith("#")
        if directive:
            payload = stripped[1:].strip()
            m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\b(.*)$", payload)
            keyword = m.group(1).casefold() if m else ""
            rest = m.group(2).strip() if m else ""
            if keyword in {"if", "ifdef", "ifndef"}:
                parent = active
                if parent:
                    if keyword == "ifdef":
                        first = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", rest)
                        if first is None:
                            raise DBaseCompilerError("#ifdef erwartet ein Makro.", line=line_no, column=1, filename=filename)
                        key = first.group(1).casefold()
                        condition = key in macros
                        if condition and rest.strip().casefold() != key:
                            condition = _safe_eval_macro_condition(
                                rest, macros, filename=filename, line=line_no,
                                compile_date=compile_date, compile_time=compile_time,
                            )
                    elif keyword == "ifndef":
                        first = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", rest)
                        if first is None:
                            raise DBaseCompilerError("#ifndef erwartet ein Makro.", line=line_no, column=1, filename=filename)
                        key = first.group(1).casefold()
                        if rest.strip().casefold() == key:
                            condition = key not in macros
                        else:
                            condition = not _safe_eval_macro_condition(
                                rest, macros, filename=filename, line=line_no,
                                compile_date=compile_date, compile_time=compile_time,
                            )
                    else:
                        condition = _safe_eval_macro_condition(
                                rest, macros, filename=filename, line=line_no,
                                compile_date=compile_date, compile_time=compile_time,
                            )
                else:
                    condition = False
                stack.append(_DBaseConditionalFrame(parent, bool(condition), False, dict(macros)))
                active = parent and bool(condition)
            elif keyword == "else":
                if not stack:
                    raise DBaseCompilerError(f"#{keyword} ohne passendes #if/#ifdef/#ifndef.", line=line_no, column=1, filename=filename)
                frame = stack[-1]
                if frame.else_seen:
                    raise DBaseCompilerError("Mehrfaches #else im selben Makro-Scope.", line=line_no, column=1, filename=filename)
                frame.else_seen = True
                macros.clear(); macros.update(frame.macros_before)
                active = frame.parent_active and not frame.condition_true
            elif keyword == "endif":
                if not stack:
                    raise DBaseCompilerError("#endif ohne passendes #if/#ifdef/#ifndef.", line=line_no, column=1, filename=filename)
                frame = stack.pop()
                macros.clear(); macros.update(frame.macros_before)
                active = frame.parent_active
            elif keyword == "define":
                if active:
                    dm = re.match(r"([A-Za-z_][A-Za-z0-9_]*)(\(([^)]*)\))?(?:\s+(.*))?$", rest)
                    if dm is None:
                        raise DBaseCompilerError("Ungueltiges #define.", line=line_no, column=1, filename=filename)
                    name = dm.group(1)
                    params_text = dm.group(3)
                    value = dm.group(4) if dm.group(4) is not None else "1"
                    params: Optional[Tuple[str, ...]] = None
                    if dm.group(2) is not None:
                        params_list = [] if not params_text.strip() else [item.strip() for item in params_text.split(",")]
                        if any(not _IDENTIFIER_RE.fullmatch(item) for item in params_list):
                            raise DBaseCompilerError("Ungueltige Parameterliste in #define.", line=line_no, column=1, filename=filename)
                        if len({item.casefold() for item in params_list}) != len(params_list):
                            raise DBaseCompilerError("Doppelte Makroparameter sind nicht erlaubt.", line=line_no, column=1, filename=filename)
                        params = tuple(params_list)
                    macros[name.casefold()] = DBaseMacro(name, params, value, line_no, 1)
            elif keyword in {"error", "warning", "info"}:
                if active:
                    message_text = rest.strip()
                    if not message_text:
                        message_text = f"#{keyword}"
                    if keyword == "error":
                        raise DBaseCompilerError(
                            message_text, line=line_no, column=1, filename=filename
                        )
                    location = f"{filename}:{line_no}: {message_text}"
                    if keyword == "warning":
                        warnings.append(location)
                    else:
                        infos.append(location)
            elif keyword == "pragma":
                if active:
                    pm = re.match(r"link\b(.*)$", rest, flags=re.IGNORECASE)
                    if pm is None:
                        raise DBaseCompilerError("Derzeit wird nur #pragma link unterstuetzt.", line=line_no, column=1, filename=filename)
                    links.append(_resolve_pragma_link_path(pm.group(1).strip(), filename=filename, line=line_no))
            elif keyword:
                raise DBaseCompilerError(f"Unbekannte Praeprozessor-Anweisung #{keyword}.", line=line_no, column=1, filename=filename)
            output.append(_blank_directive_line(orig_line))
            continue

        if not active:
            output.append(_blank_directive_line(orig_line))
            continue
        expanded, block_state = _expand_dbase_macro_text(
            orig_line, macros, in_block_comment=block_state,
            filename=filename, line=line_no,
            compile_date=compile_date, compile_time=compile_time,
        )
        output.append(expanded)

    if stack:
        raise DBaseCompilerError("Fehlendes #endif am Dateiende.", line=len(original_lines) or 1, column=1, filename=filename)
    return "".join(output), tuple(macros.values()), tuple(links), tuple(warnings), tuple(infos)


def preprocess_dbase_source(
    source: str,
    *,
    filename: str = "<dBase>",
    target: str = "pe32",
) -> DBaseFrontendResult:
    text = str(source or "")
    normalized_target = normalize_dbase_target(target)
    comments = scan_dbase_comments(text, filename=filename)
    cleaned = strip_dbase_comments(text, filename=filename)
    preprocessed, macros, pragma_links, preprocessor_warnings, preprocessor_infos = _preprocess_dbase_macros(text, filename=filename)
    return DBaseFrontendResult(
        source=text,
        comment_free_source=cleaned,
        comments=comments,
        target=normalized_target,
        filename=str(filename or "<dBase>"),
        preprocessed_source=preprocessed,
        macros=macros,
        pragma_links=pragma_links,
        preprocessor_warnings=preprocessor_warnings,
        preprocessor_infos=preprocessor_infos,
    )


def compile_dbase_frontend(
    source: str,
    *,
    filename: str = "<dBase>",
    target: str = "pe32",
) -> DBaseFrontendResult:
    """Öffentlicher Einstieg der ersten dBase-Compilerstufe.

    Diese Stufe ist bewusst ausschließlich für Kommentare zuständig. Sie ist
    bereits auf PE32/PE32+ festgelegt, damit spätere Parser- und Codegen-Stufen
    dieselbe API weiterverwenden können.
    """
    return preprocess_dbase_source(source, filename=filename, target=target)


_NUMBER_RE = re.compile(
    r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
)
_HEX_0X_RE = re.compile(r"0[xX][0-9A-Fa-f]+")
_HEX_DOLLAR_RE = re.compile(r"\$[0-9A-Fa-f]+")
_HEX_SUFFIX_RE = re.compile(r"[0-9][0-9A-Fa-f]*[hH](?![A-Za-z0-9_])")
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

_TYPE_NUMBER = 1
_TYPE_STRING = 2
_TYPE_CHAR = 3
_STRING_KINDS = {"string", "char"}


def _position_at_offset(text: str, offset: int) -> tuple[int, int]:
    return _advance_position(text[:max(0, int(offset))], 1, 1)


def _logical_statement_ranges(
    source: str,
    comments: Tuple[DBaseComment, ...],
) -> Tuple[Tuple[int, int], ...]:
    """Teilt dBase-Quelltext an echten Zeilenenden in Statements.

    Zeilenumbrueche innerhalb eines /* ... */-Kommentars beenden das aktuelle
    Statement nicht. Zeilenkommentare //, ** und && enden weiterhin an CR/LF.
    """
    text = str(source or "")
    by_start = {comment.start_offset: comment for comment in comments}
    result: list[Tuple[int, int]] = []
    start = 0
    index = 0
    length = len(text)

    while index < length:
        comment = by_start.get(index)
        if comment is not None:
            index = comment.end_offset
            continue

        char = text[index]
        if char == "\r":
            result.append((start, index))
            if index + 1 < length and text[index + 1] == "\n":
                index += 2
            else:
                index += 1
            start = index
            continue
        if char == "\n":
            result.append((start, index))
            index += 1
            start = index
            continue
        index += 1

    if start < length:
        result.append((start, length))
    elif length == 0:
        return ()
    return tuple(result)


def _decode_dbase_string(
    text: str,
    start: int,
    *,
    line: int,
    column: int,
    filename: str,
) -> tuple[str, int]:
    quote = text[start]
    index = start + 1
    output: list[str] = []
    length = len(text)
    escapes = {
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "\\": "\\",
        "'": "'",
        '"': '"',
        "0": "\0",
    }

    while index < length:
        char = text[index]
        if char == quote:
            if index + 1 < length and text[index + 1] == quote:
                output.append(quote)
                index += 2
                continue
            return "".join(output), index + 1
        if char == "\\" and index + 1 < length:
            escaped = text[index + 1]
            output.append(escapes.get(escaped, escaped))
            index += 2
            continue
        if char in "\r\n":
            raise DBaseCompilerError(
                "Nicht abgeschlossenes Stringliteral.",
                line=line,
                column=column,
                filename=filename,
            )
        output.append(char)
        index += 1

    raise DBaseCompilerError(
        "Nicht abgeschlossenes Stringliteral.",
        line=line,
        column=column,
        filename=filename,
    )


def _tokenize_dbase_statement(
    text: str,
    *,
    filename: str,
    base_offset: int,
    source: str,
) -> Tuple[DBaseToken, ...]:
    """Tokenisiert ein bereits kommentar-maskiertes logisches Statement."""
    tokens: list[DBaseToken] = []
    index = 0
    length = len(text)
    line, column = _position_at_offset(source, base_offset)

    def advance(fragment: str) -> None:
        nonlocal line, column
        line, column = _advance_position(fragment, line, column)

    while index < length:
        char = text[index]
        if char.isspace():
            start = index
            while index < length and text[index].isspace():
                index += 1
            advance(text[start:index])
            continue

        token_line = line
        token_column = column
        token_offset = base_offset + index

        if text.startswith("??", index):
            tokens.append(DBaseToken("QMARK2", "??", None, token_line, token_column, token_offset))
            index += 2
            column += 2
            continue

        comparison_tokens = (
            ("<=", "LE"),
            (">=", "GE"),
            ("==", "EQEQ"),
            ("<>", "NEANGLE"),
        )
        matched_comparison = False
        for raw_cmp, cmp_kind in comparison_tokens:
            if text.startswith(raw_cmp, index):
                tokens.append(DBaseToken(cmp_kind, raw_cmp, raw_cmp, token_line, token_column, token_offset))
                index += len(raw_cmp)
                column += len(raw_cmp)
                matched_comparison = True
                break
        if matched_comparison:
            continue

        if char == "?":
            tokens.append(DBaseToken("QMARK", "?", None, token_line, token_column, token_offset))
            index += 1
            column += 1
            continue

        if char in {"'", '"'}:
            value, end = _decode_dbase_string(
                text,
                index,
                line=token_line,
                column=token_column,
                filename=filename,
            )
            raw = text[index:end]
            literal_kind = "char" if char == "'" and len(value) == 1 else "string"
            tokens.append(DBaseToken("STRING", raw, (literal_kind, value), token_line, token_column, token_offset))
            advance(raw)
            index = end
            continue

        hex_match = (
            _HEX_0X_RE.match(text, index)
            or _HEX_DOLLAR_RE.match(text, index)
            or _HEX_SUFFIX_RE.match(text, index)
        )
        if hex_match is not None:
            raw = hex_match.group(0)
            if raw.startswith(("0x", "0X")):
                digits = raw[2:]
            elif raw.startswith("$"):
                digits = raw[1:]
            else:
                digits = raw[:-1]
            value = Decimal(int(digits, 16))
            tokens.append(DBaseToken("NUMBER", raw, value, token_line, token_column, token_offset))
            index = hex_match.end()
            column += len(raw)
            continue

        match = _NUMBER_RE.match(text, index)
        if match is not None:
            raw = match.group(0)
            try:
                value = Decimal(raw)
            except InvalidOperation as exc:
                raise DBaseCompilerError(
                    f"Ungueltige Zahl: {raw}",
                    line=token_line,
                    column=token_column,
                    filename=filename,
                ) from exc
            tokens.append(DBaseToken("NUMBER", raw, value, token_line, token_column, token_offset))
            index = match.end()
            column += len(raw)
            continue

        match = _IDENTIFIER_RE.match(text, index)
        if match is not None:
            raw = match.group(0)
            tokens.append(DBaseToken("IDENT", raw, raw, token_line, token_column, token_offset))
            index = match.end()
            column += len(raw)
            continue

        punctuation = {
            "+": "PLUS",
            "-": "MINUS",
            "*": "STAR",
            "/": "SLASH",
            "(": "LPAREN",
            ")": "RPAREN",
            ",": "COMMA",
            "=": "EQUAL",
            "<": "LT",
            ">": "GT",
            "#": "NEHASH",
        }
        kind = punctuation.get(char)
        if kind is not None:
            tokens.append(DBaseToken(kind, char, char, token_line, token_column, token_offset))
            index += 1
            column += 1
            continue

        raise DBaseCompilerError(
            f"Unerwartetes Zeichen in dBase-Ausdruck: {char!r}",
            line=token_line,
            column=token_column,
            filename=filename,
        )

    tokens.append(DBaseToken("EOF", "", None, line, column, base_offset + length))
    return tuple(tokens)


class _DBaseExpressionParser:
    def __init__(
        self,
        tokens: Tuple[DBaseToken, ...],
        *,
        filename: str,
    ) -> None:
        self.tokens = tokens
        self.filename = filename
        self.index = 0

    @property
    def current(self) -> DBaseToken:
        return self.tokens[self.index]

    def peek(self, distance: int = 1) -> DBaseToken:
        return self.tokens[min(len(self.tokens) - 1, self.index + distance)]

    def take(self, kind: str) -> Optional[DBaseToken]:
        if self.current.kind != kind:
            return None
        token = self.current
        self.index += 1
        return token

    def expect(self, kind: str, message: str) -> DBaseToken:
        token = self.take(kind)
        if token is not None:
            return token
        current = self.current
        raise DBaseCompilerError(
            message,
            line=current.line,
            column=current.column,
            filename=self.filename,
        )

    def _expect_keyword(self, keyword: str, message: str) -> DBaseToken:
        token = self.current
        if token.kind == "IDENT" and str(token.value).casefold() == keyword.casefold():
            self.index += 1
            return token
        raise DBaseCompilerError(
            message,
            line=token.line,
            column=token.column,
            filename=self.filename,
        )

    def parse_statement(self) -> object:
        first = self.current

        if self.take("QMARK2") is not None:
            return self._parse_print(first, newline=False)
        if self.take("QMARK") is not None:
            return self._parse_print(first, newline=True)

        if first.kind == "IDENT" and str(first.value).casefold() == "return":
            self.index += 1
            expression = None
            if self.current.kind != "EOF":
                expression = self.parse_expression()
            self._expect_eof()
            return DBaseReturnStatement(
                expression=expression,
                line=first.line,
                column=first.column,
            )

        if first.kind == "IDENT" and self.peek().kind == "LPAREN":
            call = self.parse_expression()
            if not isinstance(call, DBaseCallExpression):
                raise AssertionError(type(call))
            self._expect_eof()
            return DBaseCallStatement(
                call=call,
                line=first.line,
                column=first.column,
            )

        if first.kind == "IDENT" and self.peek().kind == "EQUAL":
            self.index += 1
            self.index += 1
            if self.current.kind == "EOF":
                raise DBaseCompilerError(
                    f"Nach der Zuweisung an '{first.text}' wird ein Ausdruck erwartet.",
                    line=first.line,
                    column=first.column,
                    filename=self.filename,
                )
            expression = self.parse_expression()
            self._expect_eof()
            return DBaseAssignmentStatement(
                name=str(first.value),
                expression=expression,
                line=first.line,
                column=first.column,
            )

        if first.kind == "IDENT" and str(first.value).casefold() == "clear":
            self.index += 1
            target = self.current
            if target.kind != "IDENT" or str(target.value).casefold() != "screen":
                raise DBaseCompilerError(
                    "CLEAR erwartet SCREEN.",
                    line=target.line,
                    column=target.column,
                    filename=self.filename,
                )
            self.index += 1
            expression = None
            if self.current.kind != "EOF":
                expression = self.parse_expression()
            self._expect_eof()
            return DBaseClearScreenStatement(
                expression=expression,
                line=first.line,
                column=first.column,
            )

        if first.kind == "IDENT" and str(first.value).casefold() == "set":
            self.index += 1
            command = self.current
            if command.kind != "IDENT":
                raise DBaseCompilerError(
                    "Nach SET wird FORMAT, DEBUG, COLOR oder BORDERCOLOR erwartet.",
                    line=command.line,
                    column=command.column,
                    filename=self.filename,
                )
            keyword = str(command.value).casefold()
            self.index += 1
            if keyword == "format":
                self._expect_keyword("to", "Nach SET FORMAT wird TO erwartet.")
                target = self.current
                if target.kind != "IDENT" or str(target.value).casefold() not in {"screen", "console"}:
                    raise DBaseCompilerError(
                        "SET FORMAT TO erwartet SCREEN oder CONSOLE.",
                        line=target.line,
                        column=target.column,
                        filename=self.filename,
                    )
                self.index += 1
                self._expect_eof()
                return DBaseSetFormatStatement(
                    target=str(target.value).casefold(),
                    line=first.line,
                    column=first.column,
                )
            if keyword == "debug":
                state = self.current
                if state.kind != "IDENT" or str(state.value).casefold() not in {"on", "off"}:
                    raise DBaseCompilerError(
                        "SET DEBUG erwartet ON oder OFF.",
                        line=state.line,
                        column=state.column,
                        filename=self.filename,
                    )
                self.index += 1
                self._expect_eof()
                return DBaseSetDebugStatement(
                    enabled=str(state.value).casefold() == "on",
                    line=first.line,
                    column=first.column,
                )
            if keyword == "bordercolor":
                self._expect_keyword("to", "Nach SET BORDERCOLOR wird TO erwartet.")
                if self.current.kind == "EOF":
                    raise DBaseCompilerError(
                        "SET BORDERCOLOR TO erwartet einen Farbausdruck.",
                        line=command.line, column=command.column, filename=self.filename,
                    )
                expression = self.parse_expression()
                self._expect_eof()
                return DBaseSetBorderColorStatement(
                    expression=expression,
                    line=first.line,
                    column=first.column,
                )
            if keyword == "color":
                self._expect_keyword("to", "Nach SET COLOR wird TO erwartet.")
                value = self.current
                if value.kind != "STRING":
                    raise DBaseCompilerError(
                        'SET COLOR TO erwartet eine Farbangabe als String, z.B. "W/N".',
                        line=value.line,
                        column=value.column,
                        filename=self.filename,
                    )
                literal_kind, literal_value = value.value
                if literal_kind not in {"string", "char"}:
                    raise AssertionError(literal_kind)
                self.index += 1
                self._expect_eof()
                spec = str(literal_value).strip().upper()
                if not _validate_dbase_text_color_spec(spec):
                    raise DBaseCompilerError(
                        f"Ungueltige SET COLOR TO-Farbangabe '{literal_value}'.",
                        line=value.line,
                        column=value.column,
                        filename=self.filename,
                    )
                return DBaseSetColorStatement(
                    spec=spec,
                    line=first.line,
                    column=first.column,
                )
            raise DBaseCompilerError(
                "Nach SET wird FORMAT, DEBUG, COLOR oder BORDERCOLOR erwartet.",
                line=command.line,
                column=command.column,
                filename=self.filename,
            )

        raise DBaseCompilerError(
            "Erwartet wird '?' oder '??', eine Variablenzuweisung, ein Member-Aufruf, "
            "RETURN, CLEAR SCREEN, SET FORMAT TO ..., SET DEBUG ON/OFF, "
            "SET COLOR TO ... oder SET BORDERCOLOR TO ... .",
            line=first.line,
            column=first.column,
            filename=self.filename,
        )

    def _parse_print(self, first: DBaseToken, *, newline: bool) -> DBasePrintStatement:
        if self.current.kind == "EOF":
            raise DBaseCompilerError(
                "Nach '?' bzw. '??' wird ein Ausdruck erwartet.",
                line=first.line,
                column=first.column,
                filename=self.filename,
            )
        expression = self.parse_expression()
        self._expect_eof()
        return DBasePrintStatement(
            expression=expression,
            newline=newline,
            line=first.line,
            column=first.column,
        )

    def _expect_eof(self) -> None:
        if self.current.kind != "EOF":
            token = self.current
            raise DBaseCompilerError(
                f"Unerwartetes Token nach dem Ausdruck: {token.text!r}",
                line=token.line,
                column=token.column,
                filename=self.filename,
            )

    def parse_expression(self) -> DBaseExpression:
        return self.parse_additive()

    def parse_additive(self) -> DBaseExpression:
        expression = self.parse_multiplicative()
        while self.current.kind in {"PLUS", "MINUS"}:
            operator = self.current
            self.index += 1
            right = self.parse_multiplicative()
            expression = DBaseBinaryExpression(
                line=operator.line,
                column=operator.column,
                operator=operator.text,
                left=expression,
                right=right,
            )
        return expression

    def parse_multiplicative(self) -> DBaseExpression:
        expression = self.parse_unary()
        while self.current.kind in {"STAR", "SLASH"}:
            operator = self.current
            self.index += 1
            right = self.parse_unary()
            expression = DBaseBinaryExpression(
                line=operator.line,
                column=operator.column,
                operator=operator.text,
                left=expression,
                right=right,
            )
        return expression

    def parse_unary(self) -> DBaseExpression:
        if self.current.kind in {"PLUS", "MINUS"}:
            operator = self.current
            self.index += 1
            operand = self.parse_unary()
            return DBaseUnaryExpression(
                line=operator.line,
                column=operator.column,
                operator=operator.text,
                operand=operand,
            )
        return self.parse_primary()

    def parse_primary(self) -> DBaseExpression:
        token = self.current
        if self.take("NUMBER") is not None:
            return DBaseLiteralExpression(
                line=token.line,
                column=token.column,
                value_type="number",
                value=token.value,
                text=token.text,
            )
        if self.take("STRING") is not None:
            literal_kind, literal_value = token.value
            return DBaseLiteralExpression(
                line=token.line,
                column=token.column,
                value_type=str(literal_kind),
                value=literal_value,
                text=token.text,
            )
        if self.take("IDENT") is not None:
            name = str(token.value)
            if self.take("LPAREN") is not None:
                arguments: list[DBaseExpression] = []
                if self.current.kind != "RPAREN":
                    arguments.append(self.parse_expression())
                    while self.take("COMMA") is not None:
                        arguments.append(self.parse_expression())
                self.expect("RPAREN", "Fehlende schliessende Klammer ')' im Funktionsaufruf.")
                return DBaseCallExpression(
                    line=token.line,
                    column=token.column,
                    name=name,
                    arguments=tuple(arguments),
                )
            return DBaseIdentifierExpression(
                line=token.line,
                column=token.column,
                name=name,
            )
        if self.take("LPAREN") is not None:
            expression = self.parse_expression()
            self.expect("RPAREN", "Fehlende schliessende Klammer ')' im Ausdruck.")
            return expression

        raise DBaseCompilerError(
            "Ausdruck erwartet; erlaubt sind Zahlen, Hexzahlen, Strings, Klammern, "
            "Bezeichner oder Funktionsaufrufe.",
            line=token.line,
            column=token.column,
            filename=self.filename,
        )


def _parse_dbase_routine_header(
    tokens: Tuple[DBaseToken, ...],
    *,
    filename: str,
) -> tuple[str, str, Tuple[str, ...], int, int]:
    parser = _DBaseExpressionParser(tokens, filename=filename)
    first = parser.current
    if first.kind != "IDENT" or str(first.value).casefold() not in {"procedure", "function"}:
        raise DBaseCompilerError(
            "PROCEDURE oder FUNCTION erwartet.",
            line=first.line,
            column=first.column,
            filename=filename,
        )
    kind = str(first.value).casefold()
    parser.index += 1
    name_token = parser.current
    if name_token.kind != "IDENT":
        raise DBaseCompilerError(
            f"Nach {kind.upper()} wird ein Member-Name erwartet.",
            line=name_token.line,
            column=name_token.column,
            filename=filename,
        )
    name = str(name_token.value)
    parser.index += 1
    parameters: list[str] = []
    if parser.take("LPAREN") is not None:
        if parser.current.kind != "RPAREN":
            while True:
                token = parser.current
                if token.kind != "IDENT":
                    raise DBaseCompilerError(
                        "Parametername erwartet.",
                        line=token.line,
                        column=token.column,
                        filename=filename,
                    )
                parameter = str(token.value)
                if parameter.casefold() in {item.casefold() for item in parameters}:
                    raise DBaseCompilerError(
                        f"Parameter '{parameter}' ist mehrfach angegeben.",
                        line=token.line,
                        column=token.column,
                        filename=filename,
                    )
                parameters.append(parameter)
                parser.index += 1
                if parser.take("COMMA") is None:
                    break
        parser.expect("RPAREN", "Fehlende schliessende Klammer ')' in der Parameterliste.")
    parser._expect_eof()
    return kind, name, tuple(parameters), first.line, first.column


_REMOVED_ROUTINE_END_KEYWORDS = {
    "endproc", "endprocedure", "endfunc", "endfunction", "endunction",
}
_IF_STOP_KEYWORDS = {"elseif", "else", "endif"}
_COMPARISON_TOKEN_KINDS = {"LT", "LE", "EQEQ", "GT", "GE", "NEANGLE", "NEHASH"}
_COMPARISON_OPERATOR_MAP = {
    "LT": "<",
    "LE": "<=",
    "EQEQ": "==",
    "GT": ">",
    "GE": ">=",
    "NEANGLE": "!=",
    "NEHASH": "!=",
}


def _expression_from_token_slice(
    tokens: Tuple[DBaseToken, ...],
    *,
    filename: str,
    fallback: DBaseToken,
) -> DBaseExpression:
    body = tuple(token for token in tokens if token.kind != "EOF")
    if not body:
        raise DBaseCompilerError(
            "Ausdruck in IF-Bedingung erwartet.",
            line=fallback.line,
            column=fallback.column,
            filename=filename,
        )
    last = body[-1]
    eof = DBaseToken(
        "EOF", "", None,
        last.line,
        last.column + max(1, len(last.text)),
        last.offset + len(last.text),
    )
    parser = _DBaseExpressionParser(body + (eof,), filename=filename)
    expression = parser.parse_expression()
    parser._expect_eof()
    return expression


def _parse_dbase_condition(
    tokens: Tuple[DBaseToken, ...],
    *,
    filename: str,
    keyword: str,
) -> DBaseCondition:
    """Parst ``IF/ELSEIF <expr> <vergleich> <expr>`` ohne THEN."""
    first = tokens[0]
    body = tuple(token for token in tokens[1:] if token.kind != "EOF")
    if not body:
        raise DBaseCompilerError(
            f"Nach {keyword.upper()} wird eine Bedingung erwartet.",
            line=first.line,
            column=first.column,
            filename=filename,
        )

    depth = 0
    comparison_index = -1
    comparison_token: Optional[DBaseToken] = None
    for index, token in enumerate(body):
        if token.kind == "LPAREN":
            depth += 1
            continue
        if token.kind == "RPAREN":
            depth = max(0, depth - 1)
            continue
        if depth == 0 and token.kind in _COMPARISON_TOKEN_KINDS:
            if comparison_token is not None:
                raise DBaseCompilerError(
                    "Eine IF-Bedingung darf genau einen Vergleichsoperator enthalten.",
                    line=token.line,
                    column=token.column,
                    filename=filename,
                )
            comparison_index = index
            comparison_token = token

    if comparison_token is None:
        # Ein einzelnes '=' soll nicht stillschweigend als '==' gelten.
        equal = next((token for token in body if token.kind == "EQUAL"), None)
        if equal is not None:
            raise DBaseCompilerError(
                "In IF-Bedingungen ist '==' der Gleichheitsoperator; einzelnes '=' ist nur fuer Zuweisungen erlaubt.",
                line=equal.line,
                column=equal.column,
                filename=filename,
            )
        raise DBaseCompilerError(
            "IF/ELSEIF erwartet einen Vergleichsoperator: <, <=, ==, >, >=, <> oder #.",
            line=first.line,
            column=first.column,
            filename=filename,
        )

    left_tokens = body[:comparison_index]
    right_tokens = body[comparison_index + 1:]
    left = _expression_from_token_slice(left_tokens, filename=filename, fallback=comparison_token)
    right = _expression_from_token_slice(right_tokens, filename=filename, fallback=comparison_token)
    return DBaseCondition(
        left=left,
        operator=_COMPARISON_OPERATOR_MAP[comparison_token.kind],
        right=right,
        line=comparison_token.line,
        column=comparison_token.column,
    )


def parse_dbase_statements(
    source: str,
    *,
    filename: str = "<dBase>",
    target: str = "pe32",
) -> Tuple[object, ...]:
    """Parst dBase inklusive RETURN-beendeter Member und verschachtelter IF-Bloecke.

    Regeln dieser Stufe:
    - PROCEDURE endet ausschliesslich mit ``RETURN`` ohne Wert.
    - FUNCTION endet ausschliesslich mit ``RETURN <expr>``.
    - ENDPROC/ENDPROCEDURE/ENDFUNC/ENDFUNCTION sind nicht mehr gueltig.
    - IF/ELSEIF/ELSE/ENDIF darf beliebig verschachtelt werden.
    """
    frontend = preprocess_dbase_source(source, filename=filename, target=target)
    parse_source = frontend.preprocessed_source or frontend.source
    parse_comments = scan_dbase_comments(parse_source, filename=filename)
    cleaned = strip_dbase_comments(parse_source, filename=filename)

    records: list[Tuple[Tuple[DBaseToken, ...], str]] = []
    for start, end in _logical_statement_ranges(parse_source, parse_comments):
        fragment = cleaned[start:end]
        if not fragment.strip():
            continue
        tokens = _tokenize_dbase_statement(
            fragment,
            filename=filename,
            base_offset=start,
            source=parse_source,
        )
        first = tokens[0]
        keyword = str(first.value).casefold() if first.kind == "IDENT" else ""
        records.append((tokens, keyword))

    def reject_removed_end(tokens: Tuple[DBaseToken, ...], keyword: str) -> None:
        if keyword not in _REMOVED_ROUTINE_END_KEYWORDS:
            return
        first = tokens[0]
        raise DBaseCompilerError(
            f"{first.text.upper()} wird nicht mehr unterstuetzt. "
            "PROCEDURE endet mit RETURN; FUNCTION endet mit RETURN <expr>.",
            line=first.line,
            column=first.column,
            filename=filename,
        )

    def parse_simple(tokens: Tuple[DBaseToken, ...]) -> object:
        parser = _DBaseExpressionParser(tokens, filename=filename)
        return parser.parse_statement()

    def parse_block(
        index: int,
        *,
        stop_keywords: frozenset[str],
        routine_kind: str = "",
        routine_name: str = "",
    ) -> tuple[list[object], int]:
        result: list[object] = []
        while index < len(records):
            tokens, keyword = records[index]
            first = tokens[0]
            if keyword in stop_keywords:
                return result, index
            reject_removed_end(tokens, keyword)
            if keyword in {"procedure", "function"}:
                raise DBaseCompilerError(
                    "PROCEDURE/FUNCTION darf nicht innerhalb eines IF-Blocks definiert werden.",
                    line=first.line,
                    column=first.column,
                    filename=filename,
                )
            if keyword in _IF_STOP_KEYWORDS:
                raise DBaseCompilerError(
                    f"Unerwartetes {first.text.upper()} ohne passenden IF-Block.",
                    line=first.line,
                    column=first.column,
                    filename=filename,
                )
            if keyword == "if":
                statement, index = parse_if(
                    index,
                    routine_kind=routine_kind,
                    routine_name=routine_name,
                )
                result.append(statement)
                continue
            statement = parse_simple(tokens)
            if isinstance(statement, DBaseReturnStatement):
                if not routine_kind:
                    raise DBaseCompilerError(
                        "RETURN ist nur innerhalb einer PROCEDURE oder FUNCTION erlaubt.",
                        line=statement.line,
                        column=statement.column,
                        filename=filename,
                    )
                if routine_kind == "procedure" and statement.expression is not None:
                    raise DBaseCompilerError(
                        f"PROCEDURE '{routine_name}' darf mit RETURN keinen Wert zurueckgeben.",
                        line=statement.line,
                        column=statement.column,
                        filename=filename,
                    )
                if routine_kind == "function" and statement.expression is None:
                    raise DBaseCompilerError(
                        f"FUNCTION '{routine_name}' erwartet RETURN <expr>.",
                        line=statement.line,
                        column=statement.column,
                        filename=filename,
                    )
            result.append(statement)
            index += 1
        return result, index

    def parse_if(
        index: int,
        *,
        routine_kind: str = "",
        routine_name: str = "",
    ) -> tuple[DBaseIfStatement, int]:
        tokens, keyword = records[index]
        first = tokens[0]
        if keyword != "if":
            raise AssertionError(keyword)
        branches: list[DBaseIfBranch] = []
        condition = _parse_dbase_condition(tokens, filename=filename, keyword="if")
        body, index = parse_block(
            index + 1,
            stop_keywords=frozenset(_IF_STOP_KEYWORDS),
            routine_kind=routine_kind,
            routine_name=routine_name,
        )
        branches.append(DBaseIfBranch(condition, tuple(body), first.line, first.column))

        seen_else = False
        while index < len(records):
            branch_tokens, branch_keyword = records[index]
            branch_first = branch_tokens[0]
            if branch_keyword == "elseif":
                if seen_else:
                    raise DBaseCompilerError(
                        "ELSEIF darf nicht nach ELSE stehen.",
                        line=branch_first.line,
                        column=branch_first.column,
                        filename=filename,
                    )
                condition = _parse_dbase_condition(
                    branch_tokens,
                    filename=filename,
                    keyword="elseif",
                )
                branch_body, index = parse_block(
                    index + 1,
                    stop_keywords=frozenset(_IF_STOP_KEYWORDS),
                    routine_kind=routine_kind,
                    routine_name=routine_name,
                )
                branches.append(
                    DBaseIfBranch(condition, tuple(branch_body), branch_first.line, branch_first.column)
                )
                continue
            if branch_keyword == "else":
                if seen_else:
                    raise DBaseCompilerError(
                        "Ein IF-Block darf nur ein ELSE enthalten.",
                        line=branch_first.line,
                        column=branch_first.column,
                        filename=filename,
                    )
                parser = _DBaseExpressionParser(branch_tokens, filename=filename)
                parser.index += 1
                parser._expect_eof()
                seen_else = True
                branch_body, index = parse_block(
                    index + 1,
                    stop_keywords=frozenset({"endif"}),
                    routine_kind=routine_kind,
                    routine_name=routine_name,
                )
                branches.append(
                    DBaseIfBranch(None, tuple(branch_body), branch_first.line, branch_first.column)
                )
                continue
            if branch_keyword == "endif":
                parser = _DBaseExpressionParser(branch_tokens, filename=filename)
                parser.index += 1
                parser._expect_eof()
                return DBaseIfStatement(tuple(branches), first.line, first.column), index + 1
            break

        raise DBaseCompilerError(
            "IF-Block ist nicht mit ENDIF abgeschlossen.",
            line=first.line,
            column=first.column,
            filename=filename,
        )

    statements: list[object] = []
    index = 0
    while index < len(records):
        tokens, keyword = records[index]
        first = tokens[0]
        reject_removed_end(tokens, keyword)

        if keyword in _IF_STOP_KEYWORDS:
            raise DBaseCompilerError(
                f"Unerwartetes {first.text.upper()} ohne passenden IF-Block.",
                line=first.line,
                column=first.column,
                filename=filename,
            )

        if keyword == "if":
            statement, index = parse_if(index)
            statements.append(statement)
            continue

        if keyword in {"procedure", "function"}:
            kind, name, parameters, line, column = _parse_dbase_routine_header(
                tokens,
                filename=filename,
            )
            body: list[object] = []
            index += 1
            closed = False
            while index < len(records):
                body_tokens, body_keyword = records[index]
                body_first = body_tokens[0]
                reject_removed_end(body_tokens, body_keyword)
                if body_keyword in {"procedure", "function"}:
                    raise DBaseCompilerError(
                        f"{kind.upper()} '{name}' muss vor dem naechsten Member mit "
                        + ("RETURN <expr>." if kind == "function" else "RETURN.") ,
                        line=body_first.line,
                        column=body_first.column,
                        filename=filename,
                    )
                if body_keyword in _IF_STOP_KEYWORDS:
                    raise DBaseCompilerError(
                        f"Unerwartetes {body_first.text.upper()} ohne passenden IF-Block.",
                        line=body_first.line,
                        column=body_first.column,
                        filename=filename,
                    )
                if body_keyword == "if":
                    if_statement, index = parse_if(
                        index,
                        routine_kind=kind,
                        routine_name=name,
                    )
                    body.append(if_statement)
                    continue

                statement = parse_simple(body_tokens)
                if isinstance(statement, DBaseReturnStatement):
                    if kind == "procedure" and statement.expression is not None:
                        raise DBaseCompilerError(
                            f"PROCEDURE '{name}' darf mit RETURN keinen Wert zurueckgeben.",
                            line=statement.line,
                            column=statement.column,
                            filename=filename,
                        )
                    if kind == "function" and statement.expression is None:
                        raise DBaseCompilerError(
                            f"FUNCTION '{name}' erwartet RETURN <expr>.",
                            line=statement.line,
                            column=statement.column,
                            filename=filename,
                        )
                    body.append(statement)
                    index += 1
                    closed = True
                    break
                body.append(statement)
                index += 1

            if not closed:
                expected = "RETURN <expr>" if kind == "function" else "RETURN"
                raise DBaseCompilerError(
                    f"{kind.upper()} '{name}' muss mit {expected} enden.",
                    line=line,
                    column=column,
                    filename=filename,
                )
            statements.append(
                DBaseRoutineDefinition(
                    kind=kind,
                    name=name,
                    parameters=parameters,
                    body=tuple(body),
                    line=line,
                    column=column,
                )
            )
            continue

        statement = parse_simple(tokens)
        if isinstance(statement, DBaseReturnStatement):
            raise DBaseCompilerError(
                "RETURN ist nur innerhalb einer PROCEDURE oder FUNCTION erlaubt.",
                line=statement.line,
                column=statement.column,
                filename=filename,
            )
        statements.append(statement)
        index += 1

    seen: Dict[str, DBaseRoutineDefinition] = {}
    for statement in statements:
        if not isinstance(statement, DBaseRoutineDefinition):
            continue
        key = statement.name.casefold()
        old = seen.get(key)
        if old is not None:
            raise DBaseCompilerError(
                f"Member '{statement.name}' wurde bereits in Zeile {old.line} definiert.",
                line=statement.line,
                column=statement.column,
                filename=filename,
            )
        seen[key] = statement

    return tuple(statements)

DBASE_FOREGROUND_COLOR_CODES: Tuple[str, ...] = (
    "N", "B", "G", "GB", "BG", "R", "RB", "BR", "RG", "GR", "W",
    "N+", "B+", "G+", "GB+", "BG+", "R+", "RB+", "BR+", "RG+", "GR+", "W+",
)
DBASE_BACKGROUND_COLOR_CODES: Tuple[str, ...] = (
    "N", "B", "G", "GB", "BG", "R", "RB", "BR", "RG", "GR", "W",
    "N*", "B*", "G*", "GB*", "BG*", "R*", "RB*", "BR*", "RG*", "GR*", "W*",
)

def _validate_dbase_text_color_spec(spec: str) -> bool:
    value = str(spec).strip().upper()
    if value.count("/") != 1:
        return False
    # Vom Benutzer gewuenschte Reihenfolge: HINTERGRUND/VORDERGRUND.
    # Beispiel W/N = hellgrauer Hintergrund, schwarze Schrift.
    background, foreground = (part.strip() for part in value.split("/", 1))
    return (
        background in DBASE_BACKGROUND_COLOR_CODES
        and foreground in DBASE_FOREGROUND_COLOR_CODES
    )


def _format_dbase_number(value: Decimal) -> str:
    number = Decimal(value)
    if not number:
        return "0"
    if number == number.to_integral_value():
        return format(number.quantize(Decimal(1)), "f")
    text = format(number.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _format_dbase_value(value: DBaseValue) -> str:
    if value.kind in _STRING_KINDS:
        return str(value.value)
    if value.kind == "number":
        return _format_dbase_number(Decimal(value.value))
    raise AssertionError(f"Unbekannter dBase-Werttyp: {value.kind}")


def _symbol_label(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", str(name)).strip("_") or "var"
    return "__dbase_var_" + safe.casefold()


def _constant_concat_text(value: DBaseValue) -> str:
    return _format_dbase_value(value)


def _compare_dbase_values(
    left: DBaseValue,
    right: DBaseValue,
    operator: str,
    *,
    line: int,
    column: int,
    filename: str,
) -> bool:
    if left.kind == "number" and right.kind == "number":
        a = Decimal(left.value)
        b = Decimal(right.value)
    elif left.kind in _STRING_KINDS and right.kind in _STRING_KINDS:
        a = str(left.value)
        b = str(right.value)
    else:
        raise DBaseCompilerError(
            "IF-Vergleich erwartet zwei numerische Werte oder zwei Textwerte (String/Char).",
            line=line,
            column=column,
            filename=filename,
        )

    if operator == "<":
        return a < b
    if operator == "<=":
        return a <= b
    if operator == "==":
        return a == b
    if operator == ">":
        return a > b
    if operator == ">=":
        return a >= b
    if operator == "!=":
        return a != b
    raise AssertionError(operator)


def _preview_expression(
    expression: DBaseExpression,
    info_map: Mapping[DBaseExpression, _DBaseExpressionInfo],
) -> Optional[str]:
    info = info_map[expression]
    if info.constant_value is None:
        return None
    return _format_dbase_value(info.constant_value)


def _effective_output_target(format_target: str, debug_override: Optional[bool]) -> str:
    """Bestimmt den physischen Ausgabekanal fuer ?/??."""
    if debug_override is True:
        return "debug"
    if debug_override is False:
        return "console"
    return "debug" if str(format_target).casefold() == "screen" else "console"


def _safe_member_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", str(name)).strip("_").casefold() or "member"


def _routine_instance_label(definition: DBaseRoutineDefinition, signature: Tuple[str, ...]) -> str:
    signature_text = "_".join(signature) if signature else "void"
    return f"__dbase_{definition.kind}_{_safe_member_name(definition.name)}__{signature_text}"


class _DBaseProgramAnalyzer:
    def __init__(self, statements: Tuple[object, ...], *, filename: str) -> None:
        self.statements = statements
        self.filename = filename
        self.routines: Dict[str, DBaseRoutineDefinition] = {}
        self.global_symbols: Dict[str, _DBaseSymbolState] = {}
        # Alle jemals angelegten Top-Level-Variablen behalten einen stabilen
        # Speicherplatz, auch wenn eine Variable nur in einem IF-Zweig vorkommt.
        # Sichtbarkeit nach dem IF wird separat ueber global_symbols gemerged.
        self.global_labels: Dict[str, str] = {}
        self.all_global_states: Dict[str, _DBaseSymbolState] = {}
        self.expression_info: Dict[DBaseExpression, _DBaseExpressionInfo] = {}
        self.call_bindings: Dict[DBaseCallExpression, _DBaseCallBinding] = {}
        self.external_functions: Dict[str, str] = {}
        self.instances: Dict[Tuple[str, Tuple[str, ...]], _DBaseRoutineInstance] = {}
        self.storage_slots: list[str] = []
        self.call_counter = 0

        for statement in self.statements:
            if not isinstance(statement, DBaseRoutineDefinition):
                continue
            key = statement.name.casefold()
            if key in self.routines:
                old = self.routines[key]
                raise DBaseCompilerError(
                    f"Member '{statement.name}' wurde bereits in Zeile {old.line} definiert.",
                    line=statement.line,
                    column=statement.column,
                    filename=self.filename,
                )
            self.routines[key] = statement

    def _new_call_slots(self, count: int) -> Tuple[str, ...]:
        self.call_counter += 1
        prefix = f"__dbase_call_{self.call_counter}"
        slots = tuple(f"{prefix}_arg_{index}" for index in range(count))
        self.storage_slots.extend(slots)
        return slots

    @staticmethod
    def _merged_symbols(
        globals_: Mapping[str, _DBaseSymbolState],
        locals_: Mapping[str, _DBaseSymbolState],
    ) -> Dict[str, _DBaseSymbolState]:
        merged = dict(globals_)
        merged.update(locals_)
        return merged

    def analyze_expression(
        self,
        expression: DBaseExpression,
        *,
        symbols: Mapping[str, _DBaseSymbolState],
        expression_info: Dict[DBaseExpression, _DBaseExpressionInfo],
        call_bindings: Dict[DBaseCallExpression, _DBaseCallBinding],
        require_value: bool = True,
    ) -> _DBaseExpressionInfo:
        if expression in expression_info:
            return expression_info[expression]

        if isinstance(expression, DBaseLiteralExpression):
            info = _DBaseExpressionInfo(
                kind=expression.value_type,
                constant_value=DBaseValue(expression.value_type, expression.value),
                dynamic=False,
            )

        elif isinstance(expression, DBaseIdentifierExpression):
            symbol = symbols.get(expression.name.casefold())
            if symbol is None:
                raise DBaseCompilerError(
                    f"Variable '{expression.name}' oder gleichnamiger Parameter wurde vor seiner Verwendung nicht zugewiesen.",
                    line=expression.line,
                    column=expression.column,
                    filename=self.filename,
                )
            info = _DBaseExpressionInfo(
                kind=symbol.value_type,
                constant_value=symbol.constant_value,
                dynamic=symbol.dynamic,
                variable_label=symbol.label,
            )

        elif isinstance(expression, DBaseCallExpression):
            argument_info = tuple(
                self.analyze_expression(
                    argument,
                    symbols=symbols,
                    expression_info=expression_info,
                    call_bindings=call_bindings,
                )
                for argument in expression.arguments
            )
            definition = self.routines.get(expression.name.casefold())
            if definition is not None:
                if len(expression.arguments) != len(definition.parameters):
                    raise DBaseCompilerError(
                        f"Member '{expression.name}' erwartet {len(definition.parameters)} Parameter, "
                        f"erhalten wurden {len(expression.arguments)}.",
                        line=expression.line,
                        column=expression.column,
                        filename=self.filename,
                    )
                if definition.is_procedure and require_value:
                    raise DBaseCompilerError(
                        f"PROCEDURE '{definition.name}' liefert keinen Wert und darf nicht in einem Ausdruck stehen.",
                        line=expression.line,
                        column=expression.column,
                        filename=self.filename,
                    )
                signature = tuple(item.kind for item in argument_info)
                instance = self.instantiate_routine(definition, signature)
                argument_slots = self._new_call_slots(len(expression.arguments))
                parameter_slots = tuple(
                    instance.parameter_symbols[param.casefold()].label
                    for param in definition.parameters
                )
                binding = _DBaseCallBinding(
                    kind=definition.kind,
                    target_label=instance.label,
                    result_label=instance.result_label,
                    argument_slots=argument_slots,
                    parameter_slots=parameter_slots,
                    return_kind=(instance.return_info.kind if instance.return_info is not None else ""),
                )
                call_bindings[expression] = binding
                if definition.is_function:
                    if instance.return_info is None:
                        raise AssertionError("FUNCTION ohne analysierten Rueckgabewert")
                    info = _DBaseExpressionInfo(
                        kind=instance.return_info.kind,
                        constant_value=None,
                        dynamic=True,
                        variable_label=instance.result_label,
                    )
                else:
                    info = _DBaseExpressionInfo(
                        kind="void",
                        constant_value=None,
                        dynamic=True,
                    )
            else:
                if expression.arguments:
                    raise DBaseCompilerError(
                        f"Externer Funktionsaufruf '{expression.name}(...)' mit Parametern ist noch nicht deklariert. "
                        "Definiere ihn als dBase FUNCTION/PROCEDURE, damit beliebig viele Parameter verwendet werden koennen.",
                        line=expression.line,
                        column=expression.column,
                        filename=self.filename,
                    )
                self.external_functions.setdefault(expression.name.casefold(), expression.name)
                binding = _DBaseCallBinding(
                    kind="external",
                    target_label=expression.name,
                    result_label="",
                    argument_slots=(),
                    parameter_slots=(),
                    return_kind="number",
                )
                call_bindings[expression] = binding
                info = _DBaseExpressionInfo("number", None, True)

        elif isinstance(expression, DBaseUnaryExpression):
            operand = self.analyze_expression(
                expression.operand,
                symbols=symbols,
                expression_info=expression_info,
                call_bindings=call_bindings,
            )
            if operand.kind != "number":
                raise DBaseCompilerError(
                    f"Unaerer Operator '{expression.operator}' erwartet eine Zahl.",
                    line=expression.line,
                    column=expression.column,
                    filename=self.filename,
                )
            constant = None
            if operand.constant_value is not None:
                value = Decimal(operand.constant_value.value)
                constant = DBaseValue("number", value if expression.operator == "+" else -value)
            info = _DBaseExpressionInfo("number", constant, operand.dynamic)

        elif isinstance(expression, DBaseBinaryExpression):
            left = self.analyze_expression(
                expression.left,
                symbols=symbols,
                expression_info=expression_info,
                call_bindings=call_bindings,
            )
            right = self.analyze_expression(
                expression.right,
                symbols=symbols,
                expression_info=expression_info,
                call_bindings=call_bindings,
            )
            operator = expression.operator
            if operator == "+" and (left.kind in _STRING_KINDS or right.kind in _STRING_KINDS):
                constant = None
                if left.constant_value is not None and right.constant_value is not None:
                    constant = DBaseValue(
                        "string",
                        _constant_concat_text(left.constant_value)
                        + _constant_concat_text(right.constant_value),
                    )
                info = _DBaseExpressionInfo(
                    "string",
                    constant,
                    left.dynamic or right.dynamic,
                )
            else:
                if left.kind != "number" or right.kind != "number":
                    raise DBaseCompilerError(
                        f"Operator '{operator}' erwartet zwei Zahlen; '+' kann zusaetzlich "
                        "Strings/Chars mit automatisch formatierten Zahlen verketten.",
                        line=expression.line,
                        column=expression.column,
                        filename=self.filename,
                    )
                constant = None
                if left.constant_value is not None and right.constant_value is not None:
                    a = Decimal(left.constant_value.value)
                    b = Decimal(right.constant_value.value)
                    if operator == "+":
                        result = a + b
                    elif operator == "-":
                        result = a - b
                    elif operator == "*":
                        result = a * b
                    elif operator == "/":
                        if b == 0:
                            raise DBaseCompilerError(
                                "Division durch 0 im dBase-Ausdruck.",
                                line=expression.line,
                                column=expression.column,
                                filename=self.filename,
                            )
                        with localcontext() as context:
                            context.prec = 32
                            result = a / b
                    else:
                        raise AssertionError(operator)
                    constant = DBaseValue("number", result)
                info = _DBaseExpressionInfo("number", constant, left.dynamic or right.dynamic)
        else:
            raise AssertionError(f"Unbekannter dBase-Ausdrucksknoten: {type(expression)!r}")

        expression_info[expression] = info
        return info

    def _analyze_assignment(
        self,
        statement: DBaseAssignmentStatement,
        *,
        local_symbols: Dict[str, _DBaseSymbolState],
        expression_info: Dict[DBaseExpression, _DBaseExpressionInfo],
        call_bindings: Dict[DBaseCallExpression, _DBaseCallBinding],
        instance: Optional[_DBaseRoutineInstance],
        global_symbols: Optional[Dict[str, _DBaseSymbolState]] = None,
    ) -> None:
        if statement.name.casefold() == "loginsession":
            raise DBaseCompilerError(
                "LOGINSESSION ist ein schreibgeschuetzter globaler Laufzeitwert.",
                line=statement.line, column=statement.column, filename=self.filename,
            )
        globals_view = self.global_symbols if global_symbols is None else global_symbols
        symbols = self._merged_symbols(globals_view, local_symbols)
        info = self.analyze_expression(
            statement.expression,
            symbols=symbols,
            expression_info=expression_info,
            call_bindings=call_bindings,
        )
        key = statement.name.casefold()
        old = local_symbols.get(key)
        if old is not None:
            label = old.label
        elif instance is None:
            label = self.global_labels.setdefault(key, _symbol_label(statement.name))
        else:
            label = f"{instance.label}_local_{_safe_member_name(statement.name)}"
            if label not in instance.storage_slots:
                instance.storage_slots.append(label)
        state = _DBaseSymbolState(
            name=statement.name,
            label=label,
            value_type=info.kind,
            constant_value=info.constant_value,
            dynamic=info.dynamic,
            last_line=statement.line,
            last_column=statement.column,
        )
        if instance is None:
            globals_view[key] = state
            self.all_global_states[key] = state
        else:
            local_symbols[key] = state
            instance.local_symbols[key] = state

    @staticmethod
    def _merge_branch_symbols(
        paths: Tuple[Mapping[str, _DBaseSymbolState], ...],
    ) -> Dict[str, _DBaseSymbolState]:
        if not paths:
            return {}
        common = set(paths[0])
        for path in paths[1:]:
            common.intersection_update(path)
        merged: Dict[str, _DBaseSymbolState] = {}
        for key in common:
            states = [path[key] for path in paths]
            kinds = {state.value_type for state in states}
            if len(kinds) != 1:
                # Nach dem IF ist der Typ nicht eindeutig. Der Speicherplatz
                # bleibt vorhanden, aber der Name ist ausserhalb nicht sicher typisierbar.
                continue
            first = states[0]
            same_constant = all(
                state.constant_value == first.constant_value
                for state in states[1:]
            )
            merged[key] = _DBaseSymbolState(
                name=first.name,
                label=first.label,
                value_type=first.value_type,
                constant_value=first.constant_value if same_constant else None,
                dynamic=(not same_constant) or any(state.dynamic for state in states),
                last_line=max(state.last_line for state in states),
                last_column=states[-1].last_column,
            )
        return merged

    def analyze_condition(
        self,
        condition: DBaseCondition,
        *,
        symbols: Mapping[str, _DBaseSymbolState],
        expression_info: Dict[DBaseExpression, _DBaseExpressionInfo],
        call_bindings: Dict[DBaseCallExpression, _DBaseCallBinding],
    ) -> Optional[bool]:
        left = self.analyze_expression(
            condition.left, symbols=symbols, expression_info=expression_info,
            call_bindings=call_bindings,
        )
        right = self.analyze_expression(
            condition.right, symbols=symbols, expression_info=expression_info,
            call_bindings=call_bindings,
        )
        numeric = left.kind == "number" and right.kind == "number"
        textual = left.kind in _STRING_KINDS and right.kind in _STRING_KINDS
        if not numeric and not textual:
            raise DBaseCompilerError(
                "IF-Vergleich erwartet zwei numerische Werte oder zwei Textwerte (String/Char).",
                line=condition.line, column=condition.column, filename=self.filename,
            )
        if left.constant_value is None or right.constant_value is None:
            return None
        return _compare_dbase_values(
            left.constant_value, right.constant_value, condition.operator,
            line=condition.line, column=condition.column, filename=self.filename,
        )


    def _analyze_routine_sequence(
        self,
        sequence: Tuple[object, ...],
        *,
        definition: DBaseRoutineDefinition,
        instance: _DBaseRoutineInstance,
        local_symbols: Dict[str, _DBaseSymbolState],
    ) -> None:
        for statement in sequence:
            if isinstance(statement, DBaseAssignmentStatement):
                self._analyze_assignment(
                    statement,
                    local_symbols=local_symbols,
                    expression_info=instance.expression_info,
                    call_bindings=instance.call_bindings,
                    instance=instance,
                )
                continue
            if isinstance(statement, DBasePrintStatement):
                symbols = self._merged_symbols(self.global_symbols, local_symbols)
                self.analyze_expression(
                    statement.expression,
                    symbols=symbols,
                    expression_info=instance.expression_info,
                    call_bindings=instance.call_bindings,
                )
                continue
            if isinstance(statement, DBaseCallStatement):
                symbols = self._merged_symbols(self.global_symbols, local_symbols)
                self.analyze_expression(
                    statement.call,
                    symbols=symbols,
                    expression_info=instance.expression_info,
                    call_bindings=instance.call_bindings,
                    require_value=False,
                )
                continue
            if isinstance(statement, DBaseReturnStatement):
                if definition.is_procedure:
                    if statement.expression is not None:
                        raise DBaseCompilerError(
                            f"PROCEDURE '{definition.name}' darf keinen RETURN-Wert besitzen.",
                            line=statement.line,
                            column=statement.column,
                            filename=self.filename,
                        )
                    continue
                if statement.expression is None:
                    raise DBaseCompilerError(
                        f"FUNCTION '{definition.name}' erwartet RETURN <expr>.",
                        line=statement.line,
                        column=statement.column,
                        filename=self.filename,
                    )
                symbols = self._merged_symbols(self.global_symbols, local_symbols)
                info = self.analyze_expression(
                    statement.expression,
                    symbols=symbols,
                    expression_info=instance.expression_info,
                    call_bindings=instance.call_bindings,
                )
                if instance.return_info is not None and instance.return_info.kind != info.kind:
                    raise DBaseCompilerError(
                        f"FUNCTION '{definition.name}' verwendet unterschiedliche RETURN-Typen "
                        f"('{instance.return_info.kind}' und '{info.kind}') in derselben Spezialisierung.",
                        line=statement.line,
                        column=statement.column,
                        filename=self.filename,
                    )
                instance.return_info = info
                continue
            if isinstance(statement, DBaseIfStatement):
                base = dict(local_symbols)
                path_states: list[Mapping[str, _DBaseSymbolState]] = []
                has_else = False
                symbols_for_condition = self._merged_symbols(self.global_symbols, base)
                for branch in statement.branches:
                    if branch.condition is None:
                        has_else = True
                    else:
                        self.analyze_condition(
                            branch.condition,
                            symbols=symbols_for_condition,
                            expression_info=instance.expression_info,
                            call_bindings=instance.call_bindings,
                        )
                    branch_locals = dict(base)
                    self._analyze_routine_sequence(
                        branch.body,
                        definition=definition,
                        instance=instance,
                        local_symbols=branch_locals,
                    )
                    path_states.append(branch_locals)
                if not has_else:
                    path_states.append(base)
                merged = self._merge_branch_symbols(tuple(path_states))
                local_symbols.clear()
                local_symbols.update(merged)
                continue
            if isinstance(statement, DBaseSetBorderColorStatement):
                expression = statement.expression
                if isinstance(expression, DBaseCallExpression) and expression.name.casefold() != "rgb":
                    definition_ref = self.routines.get(expression.name.casefold())
                    if definition_ref is None or definition_ref.line >= statement.line:
                        raise DBaseCompilerError(
                            f"Funktion '{expression.name}' fuer SET BORDERCOLOR muss vor ihrer Verwendung definiert sein.",
                            line=expression.line, column=expression.column, filename=self.filename,
                        )
                symbols = self._merged_symbols(self.global_symbols, local_symbols)
                info = self.analyze_expression(
                    expression, symbols=symbols,
                    expression_info=instance.expression_info,
                    call_bindings=instance.call_bindings,
                )
                if info.kind not in _STRING_KINDS:
                    raise DBaseCompilerError(
                        "SET BORDERCOLOR TO erwartet einen Stringfarbnamen, eine String-Variable/Funktion oder RGB(...).",
                        line=expression.line, column=expression.column, filename=self.filename,
                    )
                if info.constant_value is not None:
                    value = str(info.constant_value.value)
                    valid_system = value.casefold() in _DBASE_SYSTEM_COLOR_LOOKUP
                    valid_rgb = bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", value))
                    if not valid_system and not valid_rgb:
                        raise DBaseCompilerError(
                            f"Ungueltiger Farbwert '{value}' fuer SET BORDERCOLOR.",
                            line=expression.line, column=expression.column, filename=self.filename,
                        )
                continue
            if isinstance(statement, DBaseClearScreenStatement):
                if statement.expression is not None:
                    expression = statement.expression
                    symbols = self._merged_symbols(self.global_symbols, local_symbols)
                    info = self.analyze_expression(
                        expression, symbols=symbols,
                        expression_info=instance.expression_info,
                        call_bindings=instance.call_bindings,
                    )
                    self._validate_clear_screen_expression(expression, info)
                continue
            if isinstance(statement, (DBaseSetFormatStatement, DBaseSetDebugStatement, DBaseSetColorStatement)):
                continue
            if isinstance(statement, DBaseRoutineDefinition):
                continue
            raise AssertionError(type(statement))

    def _validate_clear_screen_expression(
        self, expression: DBaseExpression, info: _DBaseExpressionInfo
    ) -> None:
        if info.kind == "number":
            if info.constant_value is not None:
                value = Decimal(info.constant_value.value)
                if value != value.to_integral_value() or value < 0 or value > 255:
                    raise DBaseCompilerError(
                        "CLEAR SCREEN als Zeichenmuster erwartet einen ganzzahligen Terminal-Code von 0x00 bis 0xFF.",
                        line=expression.line, column=expression.column, filename=self.filename,
                    )
            return
        if info.kind in _STRING_KINDS:
            if info.constant_value is not None:
                value = str(info.constant_value.value)
                if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
                    raise DBaseCompilerError(
                        "CLEAR SCREEN als Farbwert erwartet '#RRGGBB' oder RGB(rr,gg,bb).",
                        line=expression.line, column=expression.column, filename=self.filename,
                    )
            return
        raise DBaseCompilerError(
            "CLEAR SCREEN <Ausdruck> erwartet einen numerischen Terminal-Code oder einen Farbwert '#RRGGBB'/RGB(...).",
            line=expression.line, column=expression.column, filename=self.filename,
        )

    def instantiate_routine(
        self,
        definition: DBaseRoutineDefinition,
        signature: Tuple[str, ...],
    ) -> _DBaseRoutineInstance:
        key = (definition.name.casefold(), tuple(signature))
        existing = self.instances.get(key)
        if existing is not None:
            if existing.analyzing:
                raise DBaseCompilerError(
                    f"Rekursiver Aufruf von '{definition.name}' wird in dieser Ausbaustufe noch nicht unterstuetzt.",
                    line=definition.line,
                    column=definition.column,
                    filename=self.filename,
                )
            return existing

        if len(signature) != len(definition.parameters):
            raise AssertionError("Signatur/Parameter-Anzahl stimmt nicht")

        label = _routine_instance_label(definition, signature)
        parameter_symbols: Dict[str, _DBaseSymbolState] = {}
        storage_slots: list[str] = []
        for index, (parameter, kind) in enumerate(zip(definition.parameters, signature)):
            slot = f"{label}_param_{index}_{_safe_member_name(parameter)}"
            storage_slots.append(slot)
            parameter_symbols[parameter.casefold()] = _DBaseSymbolState(
                name=parameter,
                label=slot,
                value_type=kind,
                constant_value=None,
                dynamic=True,
                last_line=definition.line,
                last_column=definition.column,
            )

        result_label = f"{label}_result" if definition.is_function else ""
        if result_label:
            storage_slots.append(result_label)
        instance = _DBaseRoutineInstance(
            definition=definition,
            signature=tuple(signature),
            label=label,
            parameter_symbols=parameter_symbols,
            local_symbols=dict(parameter_symbols),
            expression_info={},
            call_bindings={},
            return_info=None,
            result_label=result_label,
            storage_slots=storage_slots,
            analyzing=True,
        )
        self.instances[key] = instance

        locals_ = dict(parameter_symbols)
        self._analyze_routine_sequence(
            definition.body,
            definition=definition,
            instance=instance,
            local_symbols=locals_,
        )

        if definition.is_function and instance.return_info is None:
            raise DBaseCompilerError(
                f"FUNCTION '{definition.name}' benoetigt RETURN <expr>.",
                line=definition.line,
                column=definition.column,
                filename=self.filename,
            )
        instance.local_symbols.update(locals_)
        instance.analyzing = False
        self.storage_slots.extend(instance.storage_slots)
        return instance

    def _analyze_top_sequence(
        self,
        sequence: Tuple[object, ...],
        globals_work: Dict[str, _DBaseSymbolState],
    ) -> None:
        for statement in sequence:
            if isinstance(statement, DBaseRoutineDefinition):
                continue
            if isinstance(statement, DBaseAssignmentStatement):
                self._analyze_assignment(
                    statement,
                    local_symbols={},
                    expression_info=self.expression_info,
                    call_bindings=self.call_bindings,
                    instance=None,
                    global_symbols=globals_work,
                )
                continue
            if isinstance(statement, DBasePrintStatement):
                self.analyze_expression(
                    statement.expression,
                    symbols=globals_work,
                    expression_info=self.expression_info,
                    call_bindings=self.call_bindings,
                )
                continue
            if isinstance(statement, DBaseCallStatement):
                self.analyze_expression(
                    statement.call,
                    symbols=globals_work,
                    expression_info=self.expression_info,
                    call_bindings=self.call_bindings,
                    require_value=False,
                )
                continue
            if isinstance(statement, DBaseIfStatement):
                base = dict(globals_work)
                paths: list[Mapping[str, _DBaseSymbolState]] = []
                has_else = False
                for branch in statement.branches:
                    if branch.condition is None:
                        has_else = True
                    else:
                        self.analyze_condition(
                            branch.condition,
                            symbols=base,
                            expression_info=self.expression_info,
                            call_bindings=self.call_bindings,
                        )
                    branch_globals = dict(base)
                    self._analyze_top_sequence(branch.body, branch_globals)
                    paths.append(branch_globals)
                if not has_else:
                    paths.append(base)
                merged = self._merge_branch_symbols(tuple(paths))
                globals_work.clear()
                globals_work.update(merged)
                continue
            if isinstance(statement, DBaseReturnStatement):
                raise DBaseCompilerError(
                    "RETURN ist auf Top-Level nicht erlaubt.",
                    line=statement.line,
                    column=statement.column,
                    filename=self.filename,
                )
            if isinstance(statement, DBaseSetBorderColorStatement):
                expression = statement.expression
                if isinstance(expression, DBaseCallExpression) and expression.name.casefold() != "rgb":
                    definition_ref = self.routines.get(expression.name.casefold())
                    if definition_ref is None or definition_ref.line >= statement.line:
                        raise DBaseCompilerError(
                            f"Funktion '{expression.name}' fuer SET BORDERCOLOR muss vor ihrer Verwendung definiert sein.",
                            line=expression.line, column=expression.column, filename=self.filename,
                        )
                info = self.analyze_expression(
                    expression, symbols=globals_work,
                    expression_info=self.expression_info, call_bindings=self.call_bindings,
                )
                if info.kind not in _STRING_KINDS:
                    raise DBaseCompilerError(
                        "SET BORDERCOLOR TO erwartet einen Stringfarbnamen, eine String-Variable/Funktion oder RGB(...).",
                        line=expression.line, column=expression.column, filename=self.filename,
                    )
                if info.constant_value is not None:
                    value = str(info.constant_value.value)
                    valid_system = value.casefold() in _DBASE_SYSTEM_COLOR_LOOKUP
                    valid_rgb = bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", value))
                    if not valid_system and not valid_rgb:
                        raise DBaseCompilerError(
                            f"Ungueltiger Farbwert '{value}' fuer SET BORDERCOLOR.",
                            line=expression.line, column=expression.column, filename=self.filename,
                        )
                continue
            if isinstance(statement, DBaseClearScreenStatement):
                if statement.expression is not None:
                    expression = statement.expression
                    info = self.analyze_expression(
                        expression, symbols=globals_work,
                        expression_info=self.expression_info,
                        call_bindings=self.call_bindings,
                    )
                    self._validate_clear_screen_expression(expression, info)
                continue
            if isinstance(statement, (DBaseSetFormatStatement, DBaseSetDebugStatement, DBaseSetColorStatement)):
                continue
            raise AssertionError(type(statement))

    def _condition_constant(self, condition: DBaseCondition) -> Optional[bool]:
        left = self.expression_info.get(condition.left)
        right = self.expression_info.get(condition.right)
        if left is None or right is None or left.constant_value is None or right.constant_value is None:
            return None
        return _compare_dbase_values(
            left.constant_value,
            right.constant_value,
            condition.operator,
            line=condition.line,
            column=condition.column,
            filename=self.filename,
        )

    def _preview_top_sequence(
        self,
        sequence: Tuple[object, ...],
        *,
        format_target: str,
        debug_override: Optional[bool],
        console_chunks: list[str],
        debug_chunks: list[str],
    ) -> tuple[str, Optional[bool], bool, bool]:
        complete = True
        uses_debug = False
        for statement in sequence:
            if isinstance(statement, DBaseRoutineDefinition):
                continue
            if isinstance(statement, DBaseSetFormatStatement):
                format_target = statement.target
                continue
            if isinstance(statement, DBaseSetDebugStatement):
                debug_override = bool(statement.enabled)
                continue
            if isinstance(statement, DBaseSetColorStatement):
                continue
            if isinstance(statement, DBaseClearScreenStatement):
                # CLEAR SCREEN betrifft nur die Konsolen-Textkomponente. Auch
                # die Compile-Vorschau bildet deshalb den danach sichtbaren
                # Konsoleninhalt ab.
                console_chunks.clear()
                continue
            if isinstance(statement, DBaseSetBorderColorStatement):
                continue
            if isinstance(statement, DBaseAssignmentStatement):
                continue
            if isinstance(statement, DBaseCallStatement):
                complete = False
                continue
            if isinstance(statement, DBasePrintStatement):
                target = _effective_output_target(format_target, debug_override)
                uses_debug = uses_debug or target == "debug"
                rendered = _preview_expression(statement.expression, self.expression_info)
                if rendered is None:
                    complete = False
                    continue
                chunks = debug_chunks if target == "debug" else console_chunks
                chunks.append(rendered)
                if statement.newline:
                    chunks.append("\r\n")
                continue
            if isinstance(statement, DBaseIfStatement):
                selected: Optional[DBaseIfBranch] = None
                dynamic = False
                for branch in statement.branches:
                    if branch.condition is None:
                        selected = branch
                        break
                    value = self._condition_constant(branch.condition)
                    if value is None:
                        dynamic = True
                        break
                    if value:
                        selected = branch
                        break
                if dynamic:
                    complete = False
                    continue
                if selected is not None:
                    format_target, debug_override, branch_complete, branch_debug = self._preview_top_sequence(
                        selected.body,
                        format_target=format_target,
                        debug_override=debug_override,
                        console_chunks=console_chunks,
                        debug_chunks=debug_chunks,
                    )
                    complete = complete and branch_complete
                    uses_debug = uses_debug or branch_debug
                continue
            if isinstance(statement, DBaseReturnStatement):
                raise AssertionError("RETURN in Top-Level-Vorschau")
            raise AssertionError(type(statement))
        return format_target, debug_override, complete, uses_debug

    def run(self) -> _DBaseAnalysis:
        self._analyze_top_sequence(self.statements, self.global_symbols)

        console_chunks: list[str] = []
        debug_chunks: list[str] = []
        _, _, transcript_complete, uses_debug_output = self._preview_top_sequence(
            self.statements,
            format_target="console",
            debug_override=None,
            console_chunks=console_chunks,
            debug_chunks=debug_chunks,
        )

        variables_list: list[DBaseVariableInfo] = []
        for key, label in self.global_labels.items():
            state = self.global_symbols.get(key) or self.all_global_states[key]
            visible = self.global_symbols.get(key)
            variables_list.append(
                DBaseVariableInfo(
                    name=state.name,
                    label=label,
                    value_type=state.value_type,
                    constant_value=(visible.constant_value if visible is not None else None),
                    dynamic=(visible.dynamic if visible is not None else True),
                    last_line=state.last_line,
                    last_column=state.last_column,
                )
            )

        return _DBaseAnalysis(
            expression_info=dict(self.expression_info),
            call_bindings=dict(self.call_bindings),
            variables=tuple(variables_list),
            external_functions=tuple(self.external_functions.values()),
            console_transcript="".join(console_chunks),
            debug_transcript="".join(debug_chunks),
            transcript_complete=transcript_complete,
            uses_debug_output=uses_debug_output,
            routines=dict(self.routines),
            routine_instances=tuple(self.instances.values()),
            storage_slots=tuple(dict.fromkeys(self.storage_slots)),
        )


def _analyze_program(
    statements: Tuple[object, ...],
    *,
    filename: str,
) -> _DBaseAnalysis:
    return _DBaseProgramAnalyzer(statements, filename=filename).run()

def _evaluate_dbase_expression(
    expression: DBaseExpression,
    *,
    filename: str,
    variables: Optional[Mapping[str, DBaseValue]] = None,
    call_resolver=None,
) -> DBaseValue:
    """Kompatible Konstant-Auswertung fuer Tests und Hilfsfunktionen."""
    env = {str(key).casefold(): value for key, value in (variables or {}).items()}
    if isinstance(expression, DBaseLiteralExpression):
        return DBaseValue(expression.value_type, expression.value)
    if isinstance(expression, DBaseIdentifierExpression):
        value = env.get(expression.name.casefold())
        if value is None:
            raise DBaseCompilerError(
                f"Variable '{expression.name}' wurde vor ihrer Verwendung nicht zugewiesen.",
                line=expression.line,
                column=expression.column,
                filename=filename,
            )
        return value
    if isinstance(expression, DBaseCallExpression):
        if call_resolver is not None:
            return call_resolver(expression, env)
        raise DBaseCompilerError(
            f"Funktionsaufruf '{expression.name}(...)' ist ein Laufzeitwert und kann "
            "ohne Member-Kontext nicht ausgewertet werden.",
            line=expression.line,
            column=expression.column,
            filename=filename,
        )
    if isinstance(expression, DBaseUnaryExpression):
        operand = _evaluate_dbase_expression(
            expression.operand, filename=filename, variables=env, call_resolver=call_resolver
        )
        if operand.kind != "number":
            raise DBaseCompilerError(
                f"Unaerer Operator '{expression.operator}' erwartet eine Zahl.",
                line=expression.line,
                column=expression.column,
                filename=filename,
            )
        value = Decimal(operand.value)
        return DBaseValue("number", value if expression.operator == "+" else -value)
    if isinstance(expression, DBaseBinaryExpression):
        left = _evaluate_dbase_expression(
            expression.left, filename=filename, variables=env, call_resolver=call_resolver
        )
        right = _evaluate_dbase_expression(
            expression.right, filename=filename, variables=env, call_resolver=call_resolver
        )
        operator = expression.operator
        if operator == "+" and (left.kind in _STRING_KINDS or right.kind in _STRING_KINDS):
            return DBaseValue("string", _format_dbase_value(left) + _format_dbase_value(right))
        if left.kind != "number" or right.kind != "number":
            raise DBaseCompilerError(
                f"Operator '{operator}' erwartet zwei Zahlen.",
                line=expression.line,
                column=expression.column,
                filename=filename,
            )
        a = Decimal(left.value)
        b = Decimal(right.value)
        if operator == "+": result = a + b
        elif operator == "-": result = a - b
        elif operator == "*": result = a * b
        elif operator == "/":
            if b == 0:
                raise DBaseCompilerError(
                    "Division durch 0 im dBase-Ausdruck.",
                    line=expression.line,
                    column=expression.column,
                    filename=filename,
                )
            with localcontext() as context:
                context.prec = 32
                result = a / b
        else:
            raise AssertionError(operator)
        return DBaseValue("number", result)
    raise AssertionError(type(expression))


class _DBaseReturnSignal(Exception):
    def __init__(self, value: Optional[DBaseValue]) -> None:
        self.value = value
        super().__init__("dBase return")


class _DBaseEvaluator:
    def __init__(self, statements: Tuple[object, ...], *, filename: str) -> None:
        self.filename = filename
        self.statements = statements
        self.routines = {
            statement.name.casefold(): statement
            for statement in statements
            if isinstance(statement, DBaseRoutineDefinition)
        }
        self.globals: Dict[str, DBaseValue] = {}
        self.output: list[str] = []
        self.depth = 0

    def _eval_expr(self, expression: DBaseExpression, scope: Mapping[str, DBaseValue]) -> DBaseValue:
        merged = dict(self.globals)
        merged.update(scope)
        return _evaluate_dbase_expression(
            expression,
            filename=self.filename,
            variables=merged,
            call_resolver=self._resolve_call,
        )

    def _eval_condition(self, condition: DBaseCondition, scope: Mapping[str, DBaseValue]) -> bool:
        left = self._eval_expr(condition.left, scope)
        right = self._eval_expr(condition.right, scope)
        return _compare_dbase_values(
            left, right, condition.operator,
            line=condition.line, column=condition.column, filename=self.filename,
        )

    def _resolve_call(self, call: DBaseCallExpression, env: Mapping[str, DBaseValue]) -> DBaseValue:
        definition = self.routines.get(call.name.casefold())
        if definition is None:
            raise DBaseCompilerError(
                f"Externe Funktion '{call.name}' kann in der Python-Vorschau nicht ausgefuehrt werden.",
                line=call.line,
                column=call.column,
                filename=self.filename,
            )
        if definition.is_procedure:
            raise DBaseCompilerError(
                f"PROCEDURE '{definition.name}' liefert keinen Wert.",
                line=call.line,
                column=call.column,
                filename=self.filename,
            )
        return self._invoke(definition, call.arguments, env, expect_value=True)

    def _invoke(
        self,
        definition: DBaseRoutineDefinition,
        arguments: Tuple[DBaseExpression, ...],
        caller_scope: Mapping[str, DBaseValue],
        *,
        expect_value: bool,
    ) -> Optional[DBaseValue]:
        if len(arguments) != len(definition.parameters):
            raise DBaseCompilerError(
                f"Member '{definition.name}' erwartet {len(definition.parameters)} Parameter, "
                f"erhalten wurden {len(arguments)}.",
                line=definition.line,
                column=definition.column,
                filename=self.filename,
            )
        if self.depth >= 128:
            raise DBaseCompilerError(
                "Maximale Member-Aufruftiefe der Vorschau ueberschritten.",
                line=definition.line,
                column=definition.column,
                filename=self.filename,
            )
        caller_merged = dict(self.globals)
        caller_merged.update(caller_scope)
        values = [self._eval_expr(argument, caller_merged) for argument in arguments]
        local: Dict[str, DBaseValue] = {
            parameter.casefold(): value
            for parameter, value in zip(definition.parameters, values)
        }
        self.depth += 1
        try:
            try:
                self._execute_sequence(definition.body, local, in_routine=definition)
            except _DBaseReturnSignal as signal:
                if definition.is_function:
                    if signal.value is None:
                        raise DBaseCompilerError(
                            f"FUNCTION '{definition.name}' hat keinen Rueckgabewert.",
                            line=definition.line,
                            column=definition.column,
                            filename=self.filename,
                        )
                    return signal.value
                if signal.value is not None:
                    raise DBaseCompilerError(
                        f"PROCEDURE '{definition.name}' darf keinen Wert zurueckgeben.",
                        line=definition.line,
                        column=definition.column,
                        filename=self.filename,
                    )
                return None
            if definition.is_function:
                raise DBaseCompilerError(
                    f"FUNCTION '{definition.name}' wurde ohne RETURN <expr> beendet.",
                    line=definition.line,
                    column=definition.column,
                    filename=self.filename,
                )
            return None
        finally:
            self.depth -= 1

    def _execute_sequence(
        self,
        sequence: Tuple[object, ...],
        scope: Dict[str, DBaseValue],
        *,
        in_routine: Optional[DBaseRoutineDefinition],
    ) -> None:
        for statement in sequence:
            if isinstance(statement, DBaseRoutineDefinition):
                continue
            if isinstance(statement, DBaseAssignmentStatement):
                value = self._eval_expr(statement.expression, scope)
                if in_routine is None:
                    self.globals[statement.name.casefold()] = value
                else:
                    scope[statement.name.casefold()] = value
                continue
            if isinstance(statement, DBasePrintStatement):
                value = self._eval_expr(statement.expression, scope)
                self.output.append(_format_dbase_value(value))
                if statement.newline:
                    self.output.append("\r\n")
                continue
            if isinstance(statement, DBaseCallStatement):
                definition = self.routines.get(statement.call.name.casefold())
                if definition is None:
                    raise DBaseCompilerError(
                        f"Externer Member '{statement.call.name}' kann in der Python-Vorschau nicht ausgefuehrt werden.",
                        line=statement.line,
                        column=statement.column,
                        filename=self.filename,
                    )
                self._invoke(
                    definition,
                    statement.call.arguments,
                    scope,
                    expect_value=False,
                )
                continue
            if isinstance(statement, DBaseIfStatement):
                for branch in statement.branches:
                    if branch.condition is None or self._eval_condition(branch.condition, scope):
                        self._execute_sequence(branch.body, scope, in_routine=in_routine)
                        break
                continue
            if isinstance(statement, DBaseReturnStatement):
                value = None if statement.expression is None else self._eval_expr(statement.expression, scope)
                raise _DBaseReturnSignal(value)
            if isinstance(statement, DBaseClearScreenStatement):
                self.output.clear()
                continue
            if isinstance(statement, (DBaseSetFormatStatement, DBaseSetDebugStatement, DBaseSetColorStatement, DBaseSetBorderColorStatement)):
                continue
            raise AssertionError(type(statement))

    def run(self) -> str:
        top_level = tuple(
            statement for statement in self.statements
            if not isinstance(statement, DBaseRoutineDefinition)
        )
        self._execute_sequence(top_level, {}, in_routine=None)
        return "".join(self.output)


def evaluate_dbase_statements(
    statements: Tuple[object, ...],
    *,
    filename: str = "<dBase>",
) -> str:
    return _DBaseEvaluator(statements, filename=filename).run()

def _db_lines(label: str, payload: bytes, *, nul_terminate: bool = False) -> list[str]:
    data = bytes(payload) + (b"\0" if nul_terminate else b"")
    lines = [f"{label}:"]
    if not data:
        lines.append("    db 0")
        return lines
    for start in range(0, len(data), 24):
        chunk = data[start:start + 24]
        lines.append("    db " + ", ".join(str(byte) for byte in chunk))
    return lines


class _DBaseCodeGenerator:
    def __init__(
        self,
        statements: Tuple[object, ...],
        analysis: _DBaseAnalysis,
        *,
        target: str,
        filename: str,
    ) -> None:
        self.statements = statements
        self.analysis = analysis
        self.target = target
        self.filename = filename
        self.is64 = target == "pe64"
        self.lines: list[str] = []
        self.data_lines: list[str] = []
        self.string_literals: Dict[bytes, str] = {}
        self.double_literals: Dict[bytes, str] = {}
        self.label_counter = 0
        self.output_target = "console"
        self.current_expression_info: Mapping[DBaseExpression, _DBaseExpressionInfo] = analysis.expression_info
        self.current_call_bindings: Mapping[DBaseCallExpression, _DBaseCallBinding] = analysis.call_bindings
        self.current_instance: Optional[_DBaseRoutineInstance] = None
        self.extra_storage_slots: list[str] = []
        # Stage 29: Top-Level-Abbruchziel, wenn die Qt-Runtime durch das
        # Schliessen des Hauptfensters einen Shutdown anfordert.
        self.program_cleanup_label = ""
        self.global_variable_labels = {
            variable.name.casefold(): variable.label
            for variable in analysis.variables
        }

    @property
    def ptr_size(self) -> int:
        return 8 if self.is64 else 4

    @property
    def sp(self) -> str:
        return "rsp" if self.is64 else "esp"

    def emit(self, line: str = "") -> None:
        self.lines.append(line)

    def new_label(self, prefix: str) -> str:
        self.label_counter += 1
        return f"__dbase_{prefix}_{self.label_counter}"

    def new_storage_slot(self, prefix: str) -> str:
        label = self.new_label(prefix)
        self.extra_storage_slots.append(label)
        return label

    def text_literal(self, value: str) -> tuple[str, int]:
        payload = str(value).encode("cp1252", errors="replace")
        label = self.string_literals.get(payload)
        if label is None:
            label = f"__dbase_text_{len(self.string_literals)}"
            self.string_literals[payload] = label
        return label, len(payload)

    def double_literal(self, value: Decimal) -> str:
        raw = struct.pack("<d", float(Decimal(value)))
        label = self.double_literals.get(raw)
        if label is None:
            label = f"__dbase_num_{len(self.double_literals)}"
            self.double_literals[raw] = label
        return label

    def _binding(self, expression: DBaseCallExpression) -> _DBaseCallBinding:
        binding = self.current_call_bindings.get(expression)
        if binding is None:
            raise AssertionError(f"Keine Call-Bindung fuer {expression.name}")
        return binding

    def emit_copy_slot(self, source: str, destination: str) -> None:
        self.emit(f"    mov eax, dword ptr [{source}_type]")
        self.emit(f"    mov dword ptr [{destination}_type], eax")
        self.emit(f"    mov eax, dword ptr [{source}_num]")
        self.emit(f"    mov dword ptr [{destination}_num], eax")
        self.emit(f"    mov eax, dword ptr [{source}_num+4]")
        self.emit(f"    mov dword ptr [{destination}_num+4], eax")
        if self.is64:
            self.emit(f"    mov rax, qword ptr [{source}_ptr]")
            self.emit(f"    mov qword ptr [{destination}_ptr], rax")
        else:
            self.emit(f"    mov eax, dword ptr [{source}_ptr]")
            self.emit(f"    mov dword ptr [{destination}_ptr], eax")
        self.emit(f"    mov eax, dword ptr [{source}_len]")
        self.emit(f"    mov dword ptr [{destination}_len], eax")

    def emit_static_text_to_slot(self, value: str, kind: str, destination: str) -> None:
        label, length = self.text_literal(value)
        if self.is64:
            self.emit(f"    mov rax, {label}")
            self.emit(f"    mov qword ptr [{destination}_ptr], rax")
        else:
            self.emit(f"    mov eax, {label}")
            self.emit(f"    mov dword ptr [{destination}_ptr], eax")
        self.emit(f"    mov dword ptr [{destination}_len], {length}")
        self.emit(
            f"    mov dword ptr [{destination}_type], "
            f"{_TYPE_CHAR if kind == 'char' else _TYPE_STRING}"
        )

    def emit_internal_call(self, label: str) -> None:
        # Der interne dBase-ABI uebergibt Parameter ueber Value-Slots. Auf
        # AMD64 sorgen zusaetzliche 8 Byte dafuer, dass der Member selbst
        # wieder mit RSP=8 mod 16 startet und externe Windows-x64-Aufrufe
        # korrekt ausrichten kann.
        if self.is64:
            self.emit("    sub rsp, 8")
            self.emit(f"    call {label}")
            self.emit("    add rsp, 8")
        else:
            self.emit(f"    call {label}")

    def emit_user_call(self, expression: DBaseCallExpression) -> _DBaseCallBinding:
        binding = self._binding(expression)
        if binding.kind == "external":
            if self.is64:
                self.emit("    sub rsp, 40")
                self.emit(f"    call {binding.target_label}")
                self.emit("    add rsp, 40")
            else:
                self.emit(f"    call {binding.target_label}")
            return binding

        # Zuerst alle Argumente in call-site-eigene Slots schreiben. Erst
        # danach werden sie in die Parameter-Slots kopiert. Dadurch bleibt
        # foo(1, foo(2,3)) korrekt, obwohl beide Aufrufe dieselbe Spezialisierung
        # verwenden.
        for argument, slot in zip(expression.arguments, binding.argument_slots):
            self.emit_store_expression_to_slot(argument, slot)
        for source, destination in zip(binding.argument_slots, binding.parameter_slots):
            self.emit_copy_slot(source, destination)
        self.emit_internal_call(binding.target_label)
        return binding

    def emit_numeric_expression(self, expression: DBaseExpression) -> None:
        info = self.current_expression_info[expression]

        if isinstance(expression, DBaseLiteralExpression):
            label = self.double_literal(Decimal(expression.value))
            self.emit(f"    fld qword ptr [{label}]")
            return

        if isinstance(expression, DBaseIdentifierExpression):
            if info.kind != "number":
                raise AssertionError("Stringvariable in numerischem Codepfad")
            self.emit(f"    fld qword ptr [{info.variable_label}_num]")
            return

        if isinstance(expression, DBaseCallExpression):
            binding = self.emit_user_call(expression)
            if binding.kind == "external":
                if self.is64:
                    self.emit("    movsd qword ptr [__dbase_call_number], xmm0")
                    self.emit("    fld qword ptr [__dbase_call_number]")
                # PE32/C-double ABI liefert den externen Wert bereits in ST0.
            else:
                self.emit(f"    fld qword ptr [{binding.result_label}_num]")
            return

        if isinstance(expression, DBaseUnaryExpression):
            self.emit_numeric_expression(expression.operand)
            if expression.operator == "-":
                self.emit("    fchs")
            return

        if isinstance(expression, DBaseBinaryExpression):
            self.emit_numeric_expression(expression.left)
            self.emit_numeric_expression(expression.right)
            op = {
                "+": "faddp",
                "-": "fsubp",
                "*": "fmulp",
                "/": "fdivp",
            }.get(expression.operator)
            if op is None:
                raise AssertionError(expression.operator)
            self.emit(f"    {op}")
            return

        raise AssertionError(type(expression))

    def _qt_writer_name(self, target: str) -> str:
        return "DBaseQtAppendDebug" if target in {"screen", "debug"} else "DBaseQtAppendConsole"

    def emit_qt_call0(self, function: str) -> None:
        if self.is64:
            self.emit("    sub rsp, 40")
            self.emit(f"    call {function}")
            self.emit("    add rsp, 40")
        else:
            self.emit(f"    call {function}")

    def emit_qt_call1_int(self, function: str, value: int) -> None:
        if self.is64:
            self.emit(f"    mov ecx, {int(value)}")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {function}")
            self.emit("    add rsp, 40")
        else:
            self.emit(f"    push {int(value)}")
            self.emit(f"    call {function}")
            self.emit("    add esp, 4")

    def emit_shutdown_guard(self, routine_end_label: str = "") -> None:
        # Ein Shutdown des Hauptfensters soll die Top-Level-Ausfuehrung
        # unverzueglich in den gemeinsamen Cleanup-Pfad schicken. Innerhalb
        # spezialisierter Routinen wird nicht direkt dorthin gesprungen, weil
        # sonst deren Return-Adresse den Stack fuer externe ABI-Aufrufe
        # verschieben wuerde. Der aufrufende Top-Level-Statement-Guard
        # uebernimmt die Weiterleitung nach der Rueckkehr.
        if routine_end_label or not self.program_cleanup_label:
            return
        self.emit_qt_call0("DBaseQtShutdownRequested")
        self.emit("    test eax, eax")
        self.emit(f"    jne {self.program_cleanup_label}")

    def emit_write_static(self, label: str, length: int, target: str) -> None:
        if length <= 0:
            return
        function = self._qt_writer_name(target)
        if self.is64:
            self.emit(f"    mov rcx, {label}")
            self.emit(f"    mov edx, {int(length)}")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {function}")
            self.emit("    add rsp, 40")
        else:
            self.emit(f"    push {int(length)}")
            self.emit(f"    push {label}")
            self.emit(f"    call {function}")
            self.emit("    add esp, 8")

    def emit_write_variable_text(self, var_label: str, target: str) -> None:
        function = self._qt_writer_name(target)
        if self.is64:
            self.emit(f"    mov rcx, qword ptr [{var_label}_ptr]")
            self.emit(f"    mov edx, dword ptr [{var_label}_len]")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {function}")
            self.emit("    add rsp, 40")
        else:
            self.emit(f"    push dword ptr [{var_label}_len]")
            self.emit(f"    push dword ptr [{var_label}_ptr]")
            self.emit(f"    call {function}")
            self.emit("    add esp, 8")

    def emit_format_number_from_st0(self) -> None:
        """Formatiert ST0 nach __dbase_format_buffer und laesst die Laenge in EDX."""
        self.emit("    fstp qword ptr [__dbase_temp_number]")
        if self.is64:
            self.emit("    movsd xmm0, qword ptr [__dbase_temp_number]")
            self.emit("    mov edx, 15")
            self.emit("    mov r8, qword ptr [__dbase_format_buffer]")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_gcvt")
            self.emit("    add rsp, 40")
        else:
            self.emit("    push dword ptr [__dbase_format_buffer]")
            self.emit("    push 15")
            self.emit("    push dword ptr [__dbase_temp_number_hi]")
            self.emit("    push dword ptr [__dbase_temp_number]")
            self.emit("    call __dbase_gcvt")
            self.emit("    add esp, 16")

        length_loop = self.new_label("strlen_loop")
        length_done = self.new_label("strlen_done")
        if self.is64:
            self.emit("    mov rcx, qword ptr [__dbase_format_buffer]")
        else:
            self.emit("    mov ecx, dword ptr [__dbase_format_buffer]")
        self.emit("    xor edx, edx")
        self.emit(f"{length_loop}:")
        self.emit("    movzx eax, byte ptr [rcx]" if self.is64 else "    movzx eax, byte ptr [ecx]")
        self.emit("    test eax, eax")
        self.emit(f"    je {length_done}")
        self.emit("    inc rcx" if self.is64 else "    inc ecx")
        self.emit("    inc edx")
        self.emit(f"    jmp {length_loop}")
        self.emit(f"{length_done}:")

    def emit_write_number_from_st0(self, target: str) -> None:
        self.emit_format_number_from_st0()
        function = self._qt_writer_name(target)
        if self.is64:
            self.emit("    mov rcx, qword ptr [__dbase_format_buffer]")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {function}")
            self.emit("    add rsp, 40")
        else:
            self.emit("    push edx")
            self.emit("    push dword ptr [__dbase_format_buffer]")
            self.emit(f"    call {function}")
            self.emit("    add esp, 8")

    def emit_heap_copy_buffer_to_slot(self, buffer_label: str, destination: str) -> None:
        # EDX enthaelt die Nutzlaenge.
        self.emit(f"    mov dword ptr [{destination}_len], edx")
        self.emit("    mov eax, edx")
        self.emit("    inc eax")
        if self.is64:
            self.emit("    mov ecx, eax")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_malloc")
            self.emit("    add rsp, 40")
            self.emit(f"    mov qword ptr [{destination}_ptr], rax")
            self.emit("    mov rcx, rax")
            self.emit(f"    mov rdx, qword ptr [{buffer_label}]")
            self.emit(f"    mov r8d, dword ptr [{destination}_len]")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_memcpy")
            self.emit("    add rsp, 40")
            self.emit(f"    mov rax, qword ptr [{destination}_ptr]")
            self.emit(f"    mov edx, dword ptr [{destination}_len]")
            self.emit("    add rax, rdx")
            self.emit("    mov byte ptr [rax], 0")
        else:
            self.emit("    push eax")
            self.emit("    call __dbase_malloc")
            self.emit("    add esp, 4")
            self.emit(f"    mov dword ptr [{destination}_ptr], eax")
            self.emit(f"    push dword ptr [{destination}_len]")
            self.emit(f"    push dword ptr [{buffer_label}]")
            self.emit(f"    push dword ptr [{destination}_ptr]")
            self.emit("    call __dbase_memcpy")
            self.emit("    add esp, 12")
            self.emit(f"    mov eax, dword ptr [{destination}_ptr]")
            self.emit(f"    add eax, dword ptr [{destination}_len]")
            self.emit("    mov byte ptr [eax], 0")
        self.emit(f"    mov dword ptr [{destination}_type], {_TYPE_STRING}")

    def emit_number_as_text_slot(self, expression: DBaseExpression, destination: str) -> None:
        self.emit_numeric_expression(expression)
        self.emit_format_number_from_st0()
        self.emit_heap_copy_buffer_to_slot("__dbase_format_buffer", destination)

    def emit_concat_slots(self, left: str, right: str, destination: str) -> None:
        self.emit(f"    mov eax, dword ptr [{left}_len]")
        self.emit(f"    add eax, dword ptr [{right}_len]")
        self.emit(f"    mov dword ptr [{destination}_len], eax")
        self.emit("    inc eax")
        if self.is64:
            self.emit("    mov ecx, eax")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_malloc")
            self.emit("    add rsp, 40")
            self.emit(f"    mov qword ptr [{destination}_ptr], rax")
            self.emit("    mov rcx, rax")
            self.emit(f"    mov rdx, qword ptr [{left}_ptr]")
            self.emit(f"    mov r8d, dword ptr [{left}_len]")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_memcpy")
            self.emit("    add rsp, 40")
            self.emit(f"    mov rcx, qword ptr [{destination}_ptr]")
            self.emit(f"    mov eax, dword ptr [{left}_len]")
            self.emit("    add rcx, rax")
            self.emit(f"    mov rdx, qword ptr [{right}_ptr]")
            self.emit(f"    mov r8d, dword ptr [{right}_len]")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_memcpy")
            self.emit("    add rsp, 40")
            self.emit(f"    mov rax, qword ptr [{destination}_ptr]")
            self.emit(f"    mov edx, dword ptr [{destination}_len]")
            self.emit("    add rax, rdx")
            self.emit("    mov byte ptr [rax], 0")
        else:
            self.emit("    push eax")
            self.emit("    call __dbase_malloc")
            self.emit("    add esp, 4")
            self.emit(f"    mov dword ptr [{destination}_ptr], eax")
            self.emit(f"    push dword ptr [{left}_len]")
            self.emit(f"    push dword ptr [{left}_ptr]")
            self.emit(f"    push dword ptr [{destination}_ptr]")
            self.emit("    call __dbase_memcpy")
            self.emit("    add esp, 12")
            self.emit(f"    mov eax, dword ptr [{destination}_ptr]")
            self.emit(f"    add eax, dword ptr [{left}_len]")
            self.emit(f"    push dword ptr [{right}_len]")
            self.emit(f"    push dword ptr [{right}_ptr]")
            self.emit("    push eax")
            self.emit("    call __dbase_memcpy")
            self.emit("    add esp, 12")
            self.emit(f"    mov eax, dword ptr [{destination}_ptr]")
            self.emit(f"    add eax, dword ptr [{destination}_len]")
            self.emit("    mov byte ptr [eax], 0")
        self.emit(f"    mov dword ptr [{destination}_type], {_TYPE_STRING}")

    def emit_store_expression_as_text_slot(self, expression: DBaseExpression, destination: str) -> None:
        info = self.current_expression_info[expression]
        if info.kind == "number":
            self.emit_number_as_text_slot(expression, destination)
        else:
            self.emit_store_expression_to_slot(expression, destination)

    def emit_store_expression_to_slot(self, expression: DBaseExpression, destination: str) -> None:
        info = self.current_expression_info[expression]
        if info.kind == "number":
            self.emit_numeric_expression(expression)
            self.emit(f"    fstp qword ptr [{destination}_num]")
            self.emit(f"    mov dword ptr [{destination}_type], {_TYPE_NUMBER}")
            return

        if isinstance(expression, DBaseLiteralExpression):
            self.emit_static_text_to_slot(str(expression.value), expression.value_type, destination)
            return

        if isinstance(expression, DBaseIdentifierExpression):
            self.emit_copy_slot(info.variable_label, destination)
            return

        if isinstance(expression, DBaseCallExpression):
            binding = self.emit_user_call(expression)
            if binding.kind == "external":
                raise AssertionError("Externe Calls sind derzeit numerisch")
            self.emit_copy_slot(binding.result_label, destination)
            return

        if isinstance(expression, DBaseBinaryExpression) and expression.operator == "+":
            if info.constant_value is not None:
                self.emit_static_text_to_slot(
                    _format_dbase_value(info.constant_value),
                    "string",
                    destination,
                )
                return
            left_slot = self.new_storage_slot("concat_left")
            right_slot = self.new_storage_slot("concat_right")
            self.emit_store_expression_as_text_slot(expression.left, left_slot)
            self.emit_store_expression_as_text_slot(expression.right, right_slot)
            self.emit_concat_slots(left_slot, right_slot, destination)
            return

        if info.constant_value is not None:
            self.emit_static_text_to_slot(_format_dbase_value(info.constant_value), info.kind, destination)
            return

        raise DBaseCompilerError(
            "Dieser dynamische String-Ausdruck kann noch nicht in einen Value-Slot geschrieben werden.",
            line=expression.line,
            column=expression.column,
            filename=self.filename,
        )

    def emit_print_expression(self, expression: DBaseExpression, target: str) -> None:
        info = self.current_expression_info[expression]
        if info.kind == "number":
            self.emit_numeric_expression(expression)
            self.emit_write_number_from_st0(target)
            return

        if isinstance(expression, DBaseLiteralExpression):
            label, length = self.text_literal(str(expression.value))
            self.emit_write_static(label, length, target)
            return

        if isinstance(expression, DBaseIdentifierExpression):
            self.emit_write_variable_text(info.variable_label, target)
            return

        if isinstance(expression, DBaseCallExpression):
            binding = self.emit_user_call(expression)
            if binding.kind == "external":
                raise AssertionError("Externe Stringfunktion nicht deklariert")
            self.emit_write_variable_text(binding.result_label, target)
            return

        if isinstance(expression, DBaseBinaryExpression) and expression.operator == "+":
            # Fuer ?/?? kann direkt gestreamt werden; dadurch ist keine temporaere
            # Allokation notwendig und Zahl+String bleibt effizient.
            self.emit_print_expression(expression.left, target)
            self.emit_print_expression(expression.right, target)
            return

        if info.constant_value is not None:
            label, length = self.text_literal(_format_dbase_value(info.constant_value))
            self.emit_write_static(label, length, target)
            return

        temp = self.new_storage_slot("print_text")
        self.emit_store_expression_to_slot(expression, temp)
        self.emit_write_variable_text(temp, target)

    def _assignment_label(self, statement: DBaseAssignmentStatement) -> str:
        key = statement.name.casefold()
        if self.current_instance is not None:
            symbol = self.current_instance.local_symbols.get(key)
            if symbol is not None:
                return symbol.label
        label = self.global_variable_labels.get(key)
        if label is None:
            raise AssertionError(f"Kein Speicher fuer Variable {statement.name}")
        return label

    def emit_assignment(self, statement: DBaseAssignmentStatement) -> None:
        self.emit_store_expression_to_slot(statement.expression, self._assignment_label(statement))

    def emit_call_statement(self, statement: DBaseCallStatement) -> None:
        self.emit_user_call(statement.call)

    def emit_condition_jump_false(self, condition: DBaseCondition, false_label: str) -> None:
        left_info = self.current_expression_info[condition.left]
        right_info = self.current_expression_info[condition.right]
        numeric = left_info.kind == "number" and right_info.kind == "number"

        if numeric:
            # Nach den beiden FLD-Auswertungen gilt ST0=right, ST1=left.
            # FUCOMIP vergleicht daher right gegen left. Die Sprungabbildung
            # unten ist entsprechend invertiert und springt bei FALSE.
            self.emit_numeric_expression(condition.left)
            self.emit_numeric_expression(condition.right)
            self.emit("    fucomip st0, st1")
            self.emit("    fstp st0")
            false_jump = {
                "<": "jbe",     # right <= left
                "<=": "jb",     # right <  left
                "==": "jne",
                ">": "jae",     # right >= left
                ">=": "ja",     # right >  left
                "!=": "je",
            }[condition.operator]
            self.emit(f"    {false_jump} {false_label}")
            return

        left_slot = self.new_storage_slot("if_left_text")
        right_slot = self.new_storage_slot("if_right_text")
        self.emit_store_expression_to_slot(condition.left, left_slot)
        self.emit_store_expression_to_slot(condition.right, right_slot)

        min_ready = self.new_label("if_text_min_ready")
        result_ready = self.new_label("if_text_result_ready")
        self.emit(f"    mov eax, dword ptr [{left_slot}_len]")
        self.emit(f"    mov ecx, dword ptr [{right_slot}_len]")
        self.emit("    cmp eax, ecx")
        self.emit(f"    jbe {min_ready}")
        self.emit("    mov eax, ecx")
        self.emit(f"{min_ready}:")
        if self.is64:
            self.emit("    mov r8d, eax")
            self.emit(f"    mov rcx, qword ptr [{left_slot}_ptr]")
            self.emit(f"    mov rdx, qword ptr [{right_slot}_ptr]")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_memcmp")
            self.emit("    add rsp, 40")
        else:
            self.emit("    push eax")
            self.emit(f"    push dword ptr [{right_slot}_ptr]")
            self.emit(f"    push dword ptr [{left_slot}_ptr]")
            self.emit("    call __dbase_memcmp")
            self.emit("    add esp, 12")
        self.emit("    cmp eax, 0")
        self.emit(f"    jne {result_ready}")
        # Gleicher Prefix: die Laenge entscheidet die lexikographische Ordnung.
        self.emit(f"    mov eax, dword ptr [{left_slot}_len]")
        self.emit(f"    sub eax, dword ptr [{right_slot}_len]")
        self.emit(f"{result_ready}:")
        self.emit("    cmp eax, 0")
        false_jump = {
            "<": "jge",
            "<=": "jg",
            "==": "jne",
            ">": "jle",
            ">=": "jl",
            "!=": "je",
        }[condition.operator]
        self.emit(f"    {false_jump} {false_label}")

    def emit_if_statement(
        self,
        statement: DBaseIfStatement,
        *,
        routine_end_label: str,
        routine_result_label: str,
        format_target: str,
        debug_override: Optional[bool],
        debug_visible: bool,
    ) -> None:
        end_label = self.new_label("if_end")
        for branch in statement.branches:
            next_label = self.new_label("if_next") if branch.condition is not None else ""
            if branch.condition is not None:
                self.emit_condition_jump_false(branch.condition, next_label)
            self._emit_statement_sequence(
                branch.body,
                routine_end_label=routine_end_label,
                routine_result_label=routine_result_label,
                format_target=format_target,
                debug_override=debug_override,
                debug_visible=debug_visible,
            )
            self.emit(f"    jmp {end_label}")
            if next_label:
                self.emit(f"{next_label}:")
        self.emit(f"{end_label}:")

    def emit_clear_screen(self, statement: DBaseClearScreenStatement) -> None:
        expression = statement.expression
        if expression is None:
            self.emit_qt_call0("DBaseQtClearScreen")
            return

        info = self.current_expression_info[expression]
        if info.kind == "number":
            self.emit_numeric_expression(expression)
            self.emit("    fstp qword ptr [__dbase_temp_number]")
            if self.is64:
                self.emit("    movsd xmm0, qword ptr [__dbase_temp_number]")
                self.emit("    sub rsp, 40")
                self.emit("    call DBaseQtClearScreenChar")
                self.emit("    add rsp, 40")
            else:
                self.emit("    push dword ptr [__dbase_temp_number_hi]")
                self.emit("    push dword ptr [__dbase_temp_number]")
                self.emit("    call DBaseQtClearScreenChar")
                self.emit("    add esp, 8")
            return

        if info.kind in _STRING_KINDS:
            if info.constant_value is not None:
                value = str(info.constant_value.value)
                label, length = self.text_literal(value)
                if self.is64:
                    self.emit(f"    mov rcx, {label}")
                    self.emit(f"    mov edx, {length}")
                    self.emit("    sub rsp, 40")
                    self.emit("    call DBaseQtClearScreenColor")
                    self.emit("    add rsp, 40")
                else:
                    self.emit(f"    push {length}")
                    self.emit(f"    push {label}")
                    self.emit("    call DBaseQtClearScreenColor")
                    self.emit("    add esp, 8")
                return

            slot = self.new_storage_slot("clear_screen_color")
            self.emit_store_expression_to_slot(expression, slot)
            if self.is64:
                self.emit(f"    mov rcx, qword ptr [{slot}_ptr]")
                self.emit(f"    mov edx, dword ptr [{slot}_len]")
                self.emit("    sub rsp, 40")
                self.emit("    call DBaseQtClearScreenColor")
                self.emit("    add rsp, 40")
            else:
                self.emit(f"    push dword ptr [{slot}_len]")
                self.emit(f"    push dword ptr [{slot}_ptr]")
                self.emit("    call DBaseQtClearScreenColor")
                self.emit("    add esp, 8")
            return

        raise AssertionError(info.kind)

    def emit_border_color(self, statement: DBaseSetBorderColorStatement) -> None:
        expression = statement.expression
        info = self.current_expression_info[expression]
        if info.constant_value is not None:
            value = str(info.constant_value.value)
            value = _DBASE_SYSTEM_COLOR_LOOKUP.get(value.casefold(), value)
            label, length = self.text_literal(value)
            if self.is64:
                self.emit(f"    mov rcx, {label}")
                self.emit(f"    mov edx, {length}")
                self.emit("    sub rsp, 40")
                self.emit("    call DBaseQtSetBorderColor")
                self.emit("    add rsp, 40")
            else:
                self.emit(f"    push {length}")
                self.emit(f"    push {label}")
                self.emit("    call DBaseQtSetBorderColor")
                self.emit("    add esp, 8")
            return
        slot = self.new_storage_slot("border_color")
        self.emit_store_expression_to_slot(expression, slot)
        if self.is64:
            self.emit(f"    mov rcx, qword ptr [{slot}_ptr]")
            self.emit(f"    mov edx, dword ptr [{slot}_len]")
            self.emit("    sub rsp, 40")
            self.emit("    call DBaseQtSetBorderColor")
            self.emit("    add rsp, 40")
        else:
            self.emit(f"    push dword ptr [{slot}_len]")
            self.emit(f"    push dword ptr [{slot}_ptr]")
            self.emit("    call DBaseQtSetBorderColor")
            self.emit("    add esp, 8")

    def _emit_statement_sequence(
        self,
        sequence: Tuple[object, ...],
        *,
        routine_end_label: str = "",
        routine_result_label: str = "",
        format_target: str = "console",
        debug_override: Optional[bool] = None,
        debug_visible: bool = False,
    ) -> tuple[str, Optional[bool], bool]:
        for statement in sequence:
            if isinstance(statement, DBaseRoutineDefinition):
                continue
            if isinstance(statement, DBaseAssignmentStatement):
                self.emit_assignment(statement)
            elif isinstance(statement, DBaseSetFormatStatement):
                format_target = statement.target
            elif isinstance(statement, DBaseSetDebugStatement):
                debug_override = bool(statement.enabled)
                debug_visible = bool(statement.enabled)
                self.emit_qt_call1_int("DBaseQtSetDebugVisible", 1 if debug_visible else 0)
            elif isinstance(statement, DBaseSetColorStatement):
                label, length = self.text_literal(statement.spec)
                if self.is64:
                    self.emit(f"    mov rcx, {label}")
                    self.emit(f"    mov edx, {length}")
                    self.emit("    sub rsp, 40")
                    self.emit("    call DBaseQtSetOutputColor")
                    self.emit("    add rsp, 40")
                else:
                    self.emit(f"    push {length}")
                    self.emit(f"    push {label}")
                    self.emit("    call DBaseQtSetOutputColor")
                    self.emit("    add esp, 8")
            elif isinstance(statement, DBaseClearScreenStatement):
                self.emit_clear_screen(statement)
            elif isinstance(statement, DBaseSetBorderColorStatement):
                self.emit_border_color(statement)
            elif isinstance(statement, DBaseCallStatement):
                self.emit_call_statement(statement)
            elif isinstance(statement, DBaseIfStatement):
                self.emit_if_statement(
                    statement,
                    routine_end_label=routine_end_label,
                    routine_result_label=routine_result_label,
                    format_target=format_target,
                    debug_override=debug_override,
                    debug_visible=debug_visible,
                )
            elif isinstance(statement, DBasePrintStatement):
                output_target = _effective_output_target(format_target, debug_override)
                if output_target == "debug" and not debug_visible:
                    self.emit_qt_call1_int("DBaseQtSetDebugVisible", 1)
                    debug_visible = True
                self.emit_print_expression(statement.expression, output_target)
                if statement.newline:
                    newline_label, newline_len = self.text_literal("\r\n")
                    self.emit_write_static(newline_label, newline_len, output_target)
                self.emit_qt_call0("DBaseQtProcessEvents")
            elif isinstance(statement, DBaseReturnStatement):
                if not routine_end_label:
                    raise AssertionError("RETURN ausserhalb Routine im Codegen")
                if statement.expression is not None:
                    if not routine_result_label:
                        raise AssertionError("PROCEDURE mit Rueckgabewert")
                    self.emit_store_expression_to_slot(statement.expression, routine_result_label)
                self.emit(f"    jmp {routine_end_label}")
            else:
                raise AssertionError(type(statement))

            if not isinstance(statement, DBaseReturnStatement):
                self.emit_shutdown_guard(routine_end_label)
        return format_target, debug_override, debug_visible

    def emit_routine_instance(self, instance: _DBaseRoutineInstance) -> None:
        previous_info = self.current_expression_info
        previous_calls = self.current_call_bindings
        previous_instance = self.current_instance
        self.current_expression_info = instance.expression_info
        self.current_call_bindings = instance.call_bindings
        self.current_instance = instance
        try:
            self.emit()
            self.emit(f"{instance.label}:")
            end_label = f"{instance.label}_end"
            self._emit_statement_sequence(
                instance.definition.body,
                routine_end_label=end_label,
                routine_result_label=instance.result_label,
            )
            self.emit(f"{end_label}:")
            self.emit("    ret")
        finally:
            self.current_expression_info = previous_info
            self.current_call_bindings = previous_calls
            self.current_instance = previous_instance

    def _emit_value_slot_data(self, label: str) -> None:
        self.data_lines.extend([
            f"{label}_type:",
            "    dd 0",
            f"{label}_num:",
            "    dd 0, 0",
            f"{label}_ptr:",
            "    dd 0, 0" if self.is64 else "    dd 0",
            f"{label}_len:",
            "    dd 0",
        ])

    def build(self) -> str:
        self.emit("bits 64" if self.is64 else "bits 32")
        self.emit()
        for symbol in (
            "DBaseQtInitialize",
            "DBaseQtShowWindow",
            "DBaseQtProcessEvents",
            "DBaseQtSetDebugVisible",
            "DBaseQtAppendConsole",
            "DBaseQtAppendDebug",
            "DBaseQtSetOutputColor",
            "DBaseQtClearScreen",
            "DBaseQtClearScreenChar",
            "DBaseQtClearScreenColor",
            "DBaseQtSetBorderColor",
            "DBaseQtMarkProgramFinished",
            "DBaseQtExec",
            "DBaseQtShutdownRequested",
            "DBaseQtShutdown",
        ):
            self.emit(f'import {symbol}, "d64qt5.dll", "{symbol}"')
        # Die Runtime-Helfer werden absichtlich immer importiert. Damit koennen
        # spezialisierte FUNCTION-Instanzen auch Zahl->Text und dynamische
        # String-Konkatenation verwenden, selbst wenn im Hauptprogramm kein ?
        # vorkommt.
        self.emit('import __dbase_gcvt, "msvcrt.dll", "_gcvt"')
        self.emit('import __dbase_malloc, "msvcrt.dll", "malloc"')
        self.emit('import __dbase_memcpy, "msvcrt.dll", "memcpy"')
        self.emit('import __dbase_memcmp, "msvcrt.dll", "memcmp"')
        self.emit('import ExitProcess, "kernel32.dll", "ExitProcess"')
        self.emit('import VirtualAlloc, "kernel32.dll", "VirtualAlloc"')
        self.emit('import VirtualFree, "kernel32.dll", "VirtualFree"')
        for function in self.analysis.external_functions:
            self.emit(f"extern {function}")
        self.emit("global _start")
        self.emit("entry _start")
        self.emit()
        self.emit("section .text")
        self.emit()
        self.emit("_start:")

        self.program_cleanup_label = self.new_label("program_cleanup")
        title_label, _ = self.text_literal("dBase Qt5 Console / DEBUG")
        if self.is64:
            self.emit(f"    mov rcx, {title_label}")
            self.emit("    sub rsp, 40")
            self.emit("    call DBaseQtInitialize")
            self.emit("    add rsp, 40")
        else:
            self.emit(f"    push {title_label}")
            self.emit("    call DBaseQtInitialize")
            self.emit("    add esp, 4")
        self.emit("    test eax, eax")
        init_ok = self.new_label("qt_init_ok")
        self.emit(f"    jne {init_ok}")
        if self.is64:
            self.emit("    mov ecx, 1")
            self.emit("    sub rsp, 40")
            self.emit("    call ExitProcess")
        else:
            self.emit("    push 1")
            self.emit("    call ExitProcess")
        self.emit(f"{init_ok}:")

        # Der Zahlformat-Puffer wird nicht mehr als langer Nullblock in .data
        # abgelegt. Stattdessen enthaelt __dbase_format_buffer nur einen
        # Pointer-Slot; die 96 Nutzbytes kommen zur Laufzeit von VirtualAlloc.
        format_alloc_ok = self.new_label("format_buffer_alloc_ok")
        if self.is64:
            self.emit("    xor ecx, ecx")
            self.emit("    mov edx, 96")
            self.emit("    mov r8d, 12288")      # MEM_COMMIT | MEM_RESERVE
            self.emit("    mov r9d, 4")          # PAGE_READWRITE
            self.emit("    sub rsp, 40")
            self.emit("    call VirtualAlloc")
            self.emit("    add rsp, 40")
            self.emit("    test rax, rax")
            self.emit(f"    jne {format_alloc_ok}")
        else:
            self.emit("    push 4")               # PAGE_READWRITE
            self.emit("    push 12288")           # MEM_COMMIT | MEM_RESERVE
            self.emit("    push 96")
            self.emit("    push 0")
            self.emit("    call VirtualAlloc")
            self.emit("    test eax, eax")
            self.emit(f"    jne {format_alloc_ok}")

        # Qt wurde bereits initialisiert; bei einem Allokationsfehler sauber
        # herunterfahren und mit Fehlercode 1 beenden.
        self.emit_qt_call0("DBaseQtShutdown")
        if self.is64:
            self.emit("    mov ecx, 1")
            self.emit("    sub rsp, 40")
            self.emit("    call ExitProcess")
        else:
            self.emit("    push 1")
            self.emit("    call ExitProcess")

        self.emit(f"{format_alloc_ok}:")
        if self.is64:
            self.emit("    mov qword ptr [__dbase_format_buffer], rax")
        else:
            self.emit("    mov dword ptr [__dbase_format_buffer], eax")

        # Vor dem ersten Show/Paint wird der definierte Startzustand hergestellt:
        # Konsole sichtbar, DEBUG aus. Die Bridge garantiert dabei, dass DEBUG OFF
        # niemals den Konsolen-Tab entfernt.
        self.emit_qt_call1_int("DBaseQtSetDebugVisible", 0)
        self.emit_qt_call0("DBaseQtShowWindow")
        self.emit_qt_call0("DBaseQtProcessEvents")
        self.emit_shutdown_guard()

        self._emit_statement_sequence(self.statements)

        self.emit_qt_call0("DBaseQtMarkProgramFinished")
        self.emit_qt_call0("DBaseQtExec")
        self.emit("    mov dword ptr [__dbase_exit_code], eax")

        # Sowohl der normale Eventloop-Rueckweg als auch ein Close waehrend
        # eines Dialogs/ProcessEvents landen hier. Dadurch werden Qt-Runtime
        # und der VirtualAlloc-Puffer garantiert ueber denselben Pfad abgebaut.
        self.emit(f"{self.program_cleanup_label}:")
        self.emit_qt_call0("DBaseQtShutdown")

        # Den per VirtualAlloc reservierten Formatpuffer wieder freigeben.
        if self.is64:
            self.emit("    mov rcx, qword ptr [__dbase_format_buffer]")
            self.emit("    test rcx, rcx")
            format_free_done = self.new_label("format_buffer_free_done")
            self.emit(f"    je {format_free_done}")
            self.emit("    xor edx, edx")          # dwSize = 0 bei MEM_RELEASE
            self.emit("    mov r8d, 32768")        # MEM_RELEASE
            self.emit("    sub rsp, 40")
            self.emit("    call VirtualFree")
            self.emit("    add rsp, 40")
            self.emit(f"{format_free_done}:")
            self.emit("    mov qword ptr [__dbase_format_buffer], 0")
        else:
            self.emit("    mov eax, dword ptr [__dbase_format_buffer]")
            self.emit("    test eax, eax")
            format_free_done = self.new_label("format_buffer_free_done")
            self.emit(f"    je {format_free_done}")
            self.emit("    push 32768")             # MEM_RELEASE
            self.emit("    push 0")
            self.emit("    push eax")
            self.emit("    call VirtualFree")
            self.emit(f"{format_free_done}:")
            self.emit("    mov dword ptr [__dbase_format_buffer], 0")

        if self.is64:
            self.emit("    mov ecx, dword ptr [__dbase_exit_code]")
            self.emit("    sub rsp, 40")
            self.emit("    call ExitProcess")
        else:
            self.emit("    push dword ptr [__dbase_exit_code]")
            self.emit("    call ExitProcess")

        # Spezialisierte dBase-Member liegen im selben .text-Abschnitt. Die
        # Labels duerfen nach _start folgen, da der interne Assembler Forward-
        # Referenzen aufloest.
        for instance in self.analysis.routine_instances:
            self.emit_routine_instance(instance)

        self.data_lines = ["", "section .data", ""]
        for raw, label in self.double_literals.items():
            low, high = struct.unpack("<II", raw)
            self.data_lines.extend([f"{label}:", f"    dd {low}, {high}"])
        for payload, label in self.string_literals.items():
            nul = label == title_label
            self.data_lines.extend(_db_lines(label, payload, nul_terminate=nul))
        self.data_lines.extend([
            "__dbase_temp_number:",
            "    dd 0",
            "__dbase_temp_number_hi:",
            "    dd 0",
            "__dbase_call_number:",
            "    dd 0, 0",
            "__dbase_format_buffer:",
            "    dd 0, 0" if self.is64 else "    dd 0",
            "__dbase_exit_code:",
            "    dd 0",
        ])

        all_slots: list[str] = []
        all_slots.extend(variable.label for variable in self.analysis.variables)
        all_slots.extend(self.analysis.storage_slots)
        all_slots.extend(self.extra_storage_slots)
        for label in dict.fromkeys(all_slots):
            self._emit_value_slot_data(label)

        return "\n".join(self.lines + self.data_lines).rstrip() + "\n"

def _emit_dbase_output_program(
    target: str,
    transcript: str,
) -> str:
    """Kompatibilitaetshelfer fuer ein reines statisches ?/??-Programm."""
    source = "?? " + repr(str(transcript)) if transcript else ""
    if not source:
        statements: Tuple[object, ...] = ()
    else:
        # Kein externer Aufrufer sollte diesen privaten Helfer fuer komplexe
        # Strings verwenden; compile_dbase_to_assembly ist der echte Einstieg.
        statements = (
            DBasePrintStatement(
                DBaseLiteralExpression(1, 1, "string", str(transcript), repr(str(transcript))),
                False,
                1,
                1,
            ),
        )
    analysis = _analyze_program(statements, filename="<dBase>")
    return _DBaseCodeGenerator(statements, analysis, target=target, filename="<dBase>").build()


def _first_non_whitespace_position(text: str) -> tuple[int, int]:
    line = 1
    column = 1
    index = 0
    while index < len(text):
        char = text[index]
        if not char.isspace():
            return line, column
        if char == "\r":
            if index + 1 < len(text) and text[index + 1] == "\n":
                index += 1
            line += 1
            column = 1
        elif char == "\n":
            line += 1
            column = 1
        else:
            column += 1
        index += 1
    return 0, 0


def _emit_empty_program(target: str) -> str:
    analysis = _analyze_program((), filename="<dBase>")
    return _DBaseCodeGenerator((), analysis, target=target, filename="<dBase>").build()


def compile_dbase_to_assembly(
    source: str,
    *,
    filename: str = "<dBase>",
    target: str = "pe32",
    windows_application_mode: str = "Console",
) -> DBaseCompileResult:
    """Kompiliert dBase mit Qt5-GUI, Membern und verschachtelten Bedingungen.

    Implementiert:
    - //, **, && und /* ... */ Kommentare
    - ? <expr> und ?? <expr>
    - Variablenzuweisung ``Name = Ausdruck``
    - Zahl-, Hex-, Char- und Stringliterale
    - arithmetische + - * / Ausdruecke und String-Konkatenation
    - PROCEDURE/FUNCTION mit beliebig vielen Parametern und nativen Member-Aufrufen
    - PROCEDURE endet ausschliesslich mit RETURN; FUNCTION mit RETURN <expr>
    - verschachtelte IF/ELSEIF/ELSE/ENDIF-Bloecke mit < <= == > >= <> und #
    - polymorphe FUNCTION-Spezialisierung nach Parameter-Typen (Zahl/String/Char)
    - no-arg Funktionsaufrufe als externe numerische Symbole
    - C-artige Makros: #define/#if/#ifdef/#ifndef/#else/#endif, ## und #pragma link
    - #error/#warning/#info sowie __FILE__/__LINE__/__DATE__/__TIME__
    - Qt5-GUI mit Tabs "Konsole" und "DEBUG" ueber d64qt5.dll
    - SET FORMAT TO SCREEN als kompatibler Debug-Ausgabekanal
    - SET DEBUG ON/OFF blendet den DEBUG-Tab ein/aus und routet ?/??
    """
    frontend = preprocess_dbase_source(
        source,
        filename=filename,
        target=target,
    )
    requested_mode = normalize_dbase_windows_mode(windows_application_mode)
    # dBase verwendet ab dieser Stufe immer die eigene Qt5-GUI-Runtime.
    # Der Parameter bleibt fuer API-Kompatibilitaet erhalten.
    mode = "GUI"
    statements = parse_dbase_statements(
        frontend.preprocessed_source or frontend.source,
        filename=filename,
        target=frontend.target,
    )
    analysis = _analyze_program(statements, filename=filename)
    assembly = _DBaseCodeGenerator(
        statements,
        analysis,
        target=frontend.target,
        filename=filename,
    ).build()
    target_label = (
        "Windows PE32+ (AMD64)"
        if frontend.target == "pe64"
        else "Windows PE32 (IA-32)"
    )
    warnings: list[str] = list(frontend.preprocessor_warnings)
    if requested_mode != "GUI":
        warnings.append(
            "dBase verwendet ab Qt5-GUI-Stufe immer das Windows-GUI-Subsystem; "
            "der angeforderte Console-Modus wird aus Kompatibilitaetsgruenden ignoriert."
        )
    if not analysis.transcript_complete:
        warnings.append(
            "Die Vorschau 'transcript' ist unvollstaendig, weil mindestens ein "
            "Funktionsaufruf erst zur Laufzeit ausgewertet wird."
        )
    if analysis.external_functions:
        warnings.append(
            "Externe dBase-Funktionen muessen beim Linken als Objekt/Modul bereitgestellt "
            "werden. Numerischer Rueckgabewert: ST0 (PE32), XMM0 (PE32+)."
        )
    return DBaseCompileResult(
        assembly=assembly,
        target=frontend.target,
        windows_application_mode=mode,
        notes=(
            f"dBase-Ausbaustufe 10: verschachtelte Bedingungen fuer {target_label}.",
            "#define unterstuetzt Objekt- und Funktionsmakros; ## verkettet Tokens.",
            "#if/#ifdef/#ifndef sind verschachtelbar und scoped; ausschliesslich #else ist gueltig.",
            "#if 0 ... #endif kann beliebig grosse dBase-Codebereiche vom Compile ausschliessen.",
            "#error bricht den Compiler ab; #warning und #info erscheinen in den Diagnosen.",
            "Vordefiniert: __FILE__, __LINE__, __DATE__ und __TIME__.",
            "#pragma link bindet .o/.obj/.a/.lib beim finalen PE-Linkschritt ein.",
            "Variablen koennen Zahl/Hex, Char und String aufnehmen; Zuweisungen erzeugen echte Speicher-Slots.",
            "PROCEDURE endet ausschliesslich mit RETURN ohne Wert; FUNCTION ausschliesslich mit RETURN <expr>.",
            "ENDPROC/ENDPROCEDURE/ENDFUNC/ENDFUNCTION sind nicht mehr Bestandteil der dBase-Syntax.",
            "IF/ELSEIF/ELSE/ENDIF ist beliebig verschachtelbar; Operatoren: <, <=, ==, >, >=, <> und # (ungleich).",
            "Numerische/Hex/Float-Werte werden numerisch, String/Char-Werte lexikographisch verglichen.",
            "Member-Parameterlisten sind nicht kuenstlich begrenzt; Aufrufe werden in Value-Slots uebergeben.",
            "FUNCTION-Instanzen werden anhand der verwendeten Parameter-Typen spezialisiert und koennen Zahl, String oder Char liefern.",
            "? fuegt CR/LF an; ?? schreibt ohne NewLine.",
            "Bei String/Char + Zahl wird die Zahl automatisch fuer die Textausgabe formatiert.",
            "Die erzeugte EXE baut ueber d64qt5.dll eine native Qt5-GUI mit Konsole- und DEBUG-Tab auf.",
            "Die beiden Ausgabeflaechen sind QPlainTextEdit; im DEBUG-Tab sitzt zusaetzlich eine QLineEdit-Eingabezeile.",
            "SET FORMAT TO CONSOLE + SET DEBUG ON leitet ?/?? in DEBUG; SET DEBUG OFF blendet DEBUG aus und schreibt wieder in Konsole.",
            "Nach der Programmausfuehrung bleibt die Qt-Ereignisschleife aktiv, bis das GUI-Fenster geschlossen wird.",
            "Hexliterale: 0xFF, $FF und 0FFh; die interne Rechenform ist numerisch.",
        ) + tuple(frontend.preprocessor_infos),
        warnings=tuple(warnings),
        linked_object_files=tuple(item.path for item in frontend.pragma_links),
        frontend=frontend,
        statements=statements,
        transcript=analysis.console_transcript,
        debug_transcript=analysis.debug_transcript,
        uses_debug_output=analysis.uses_debug_output,
        variables=analysis.variables,
        external_functions=analysis.external_functions,
    )



def dbase_uses_debug_output(
    source: str,
    *,
    filename: str = "<dBase>",
    target: str = "pe32",
) -> bool:
    """True, wenn mindestens eine ?/??-Ausgabe in den DEBUG-Kanal geht."""
    statements = parse_dbase_statements(source, filename=filename, target=target)
    return bool(_analyze_program(statements, filename=filename).uses_debug_output)

def preprocess_dbase_file(
    path: str | Path,
    *,
    target: str = "pe32",
) -> DBaseFrontendResult:
    source_path = Path(path)
    text = source_path.read_text(encoding="utf-8")
    return preprocess_dbase_source(
        text,
        filename=str(source_path),
        target=target,
    )


__all__ = [
    "DBaseComment",
    "DBaseMacro",
    "DBasePragmaLink",
    "DBaseCompilerError",
    "DBaseFrontendResult",
    "DBaseCompileResult",
    "DBaseToken",
    "DBaseExpression",
    "DBaseLiteralExpression",
    "DBaseIdentifierExpression",
    "DBaseCallExpression",
    "DBaseUnaryExpression",
    "DBaseBinaryExpression",
    "DBasePrintStatement",
    "DBaseAssignmentStatement",
    "DBaseSetFormatStatement",
    "DBaseSetDebugStatement",
    "DBaseSetColorStatement",
    "DBaseClearScreenStatement",
    "DBaseSetBorderColorStatement",
    "DBaseReturnStatement",
    "DBaseCallStatement",
    "DBaseCondition",
    "DBaseIfBranch",
    "DBaseIfStatement",
    "DBaseRoutineDefinition",
    "DBaseVariableInfo",
    "DBaseValue",
    "normalize_dbase_target",
    "normalize_dbase_windows_mode",
    "scan_dbase_comments",
    "strip_dbase_comments",
    "preprocess_dbase_source",
    "preprocess_dbase_file",
    "compile_dbase_frontend",
    "parse_dbase_statements",
    "evaluate_dbase_statements",
    "dbase_uses_debug_output",
    "compile_dbase_to_assembly",
]

# ---------------------------------------------------------------------------
# dBase Stage 13: erstes Klassen-/Objektmodell + native MENU-Objekte
# ---------------------------------------------------------------------------
# Diese Erweiterung bleibt absichtlich additiv. Die bestehende Ausdrucks-,
# Member-, IF- und Makrologik aus Stage 12 wird weiterverwendet.

_stage12_parse_dbase_statements = parse_dbase_statements
_Stage12ProgramAnalyzer = _DBaseProgramAnalyzer
_Stage12CodeGenerator = _DBaseCodeGenerator


@dataclass(frozen=True)
class DBaseObjectPath:
    parts: Tuple[str, ...]
    line: int
    column: int

    @property
    def canonical_parts(self) -> Tuple[str, ...]:
        if not self.parts:
            return ()
        head = self.parts[0].casefold()
        if head in {"_app", "this"}:
            return ("_app",) + tuple(self.parts[1:])
        return tuple(self.parts)

    @property
    def dotted(self) -> str:
        return ".".join(self.canonical_parts)


@dataclass(frozen=True)
class DBaseNewObjectStatement:
    target: DBaseObjectPath
    class_name: str
    owner: DBaseObjectPath
    line: int
    column: int


@dataclass(frozen=True)
class DBaseSessionLoginStatement:
    result_name: str
    target: DBaseObjectPath
    username: DBaseExpression
    password: DBaseExpression
    group: DBaseExpression
    line: int
    column: int


@dataclass(frozen=True)
class DBaseLocalObjectDeclaration:
    name: str
    class_name: str
    line: int
    column: int


@dataclass(frozen=True)
class DBaseObjectPropertyStatement:
    target: DBaseObjectPath
    property_name: str
    expression: Optional[DBaseExpression]
    object_value: Optional[DBaseObjectPath]
    line: int
    column: int


@dataclass(frozen=True)
class DBaseObjectMethodStatement:
    target: DBaseObjectPath
    method_name: str
    line: int
    column: int


@dataclass(frozen=True)
class DBaseMenuFileStatement:
    expression: DBaseExpression
    resolved_path: str
    line: int
    column: int

    @property
    def path(self) -> str:
        # Rueckwaertskompatible Lesehilfe fuer bestehende Tests/Tools.
        return self.resolved_path

    @property
    def configured(self) -> bool:
        return bool(self.resolved_path.strip())


@dataclass(frozen=True)
class DBaseAppColorStatement:
    property_name: str
    expression: DBaseExpression
    line: int
    column: int

    @property
    def color_name(self) -> str:
        # Rueckwaertskompatible Lesehilfe fuer direkte Stringliterale.
        if isinstance(self.expression, DBaseLiteralExpression) and self.expression.value_type in _STRING_KINDS:
            return str(self.expression.value)
        return ""


DBASE_SYSTEM_COLOR_NAMES: Tuple[str, ...] = (
    "ActiveBorder",
    "ActiveCaption",
    "AppWorkspace",
    "Background",
    "BtnFace",
    "BtnHighlight",
    "BtnShadow",
    "BtnText",
    "CaptionText",
    "GrayText",
    "Highlight",
    "HighlightText",
    "InactiveBorder",
    "InactiveCaption",
    "InactiveCaptionText",
    "InfoText",
    "InfoBk",
    "Menu",
    "MenuText",
    "Scrollbar",
    "Window",
    "WindowFrame",
    "WindowText",
)
_DBASE_SYSTEM_COLOR_LOOKUP = {name.casefold(): name for name in DBASE_SYSTEM_COLOR_NAMES}


@dataclass(frozen=True)
class DBaseMenuProperty:
    name: str
    value_kind: str
    value: object
    line: int
    column: int


@dataclass(frozen=True)
class DBaseWithStatement:
    target: DBaseObjectPath
    properties: Tuple[DBaseMenuProperty, ...]
    line: int
    column: int


_DBASE_OBJECT_PATH_TEXT = r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
_DBASE_OBJECT_PATH_RE = re.compile(rf"(?i)^{_DBASE_OBJECT_PATH_TEXT}$")
_DBASE_NEW_MENU_RE = re.compile(
    rf"(?i)^\s*({_DBASE_OBJECT_PATH_TEXT})\s*=\s*"
    rf"new\s+MENU\s*\(\s*({_DBASE_OBJECT_PATH_TEXT})\s*\)\s*$"
)
_DBASE_NEW_SESSION_RE = re.compile(
    rf"(?i)^\s*({_DBASE_OBJECT_PATH_TEXT})\s*=\s*new\s+SESSION\s*\(\s*\)\s*$"
)
_DBASE_SESSION_LOGIN_RE = re.compile(
    rf"(?i)^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*({_DBASE_OBJECT_PATH_TEXT})\.LOGIN\s*\((.*)\)\s*$"
)
_DBASE_LOCAL_DATABASE_RE = re.compile(
    r"(?i)^\s*local\s+([A-Za-z_][A-Za-z0-9_]*)\s+as\s+DATABASE\s*$"
)
_DBASE_NEW_DATABASE_RE = re.compile(
    rf"(?i)^\s*({_DBASE_OBJECT_PATH_TEXT})\s*=\s*new\s+DATABASE\s*\(\s*\)\s*$"
)
_DBASE_DATABASE_PROPERTY_RE = re.compile(
    rf"(?i)^\s*({_DBASE_OBJECT_PATH_TEXT})\.(path|databaseName|userName|password|active|alias|session)\s*=\s*(.*?)\s*$"
)
_DBASE_DATABASE_METHOD_RE = re.compile(
    rf"(?i)^\s*({_DBASE_OBJECT_PATH_TEXT})\.(open|close|commit)\s*\(\s*\)\s*$"
)
_DBASE_MENUFILE_RE = re.compile(
    r"(?i)^\s*((?:_app|this)\.menuFile)\s*=\s*(.*?)\s*$"
)
_DBASE_COLOR_NORMAL_RE = re.compile(
    r"(?i)^\s*((?:_app|this)\.colorNormal)\s*=\s*(.*?)\s*$"
)
_DBASE_WITH_RE = re.compile(
    rf"(?i)^\s*with\s*\(\s*({_DBASE_OBJECT_PATH_TEXT})\s*\)\s*$"
)
_DBASE_ENDWITH_RE = re.compile(r"(?i)^\s*endwith\s*$")


def _dbase_object_path(text: str, line: int, column: int = 1) -> DBaseObjectPath:
    value = str(text).strip()
    if not _DBASE_OBJECT_PATH_RE.fullmatch(value):
        raise DBaseCompilerError(
            f"Ungueltiger Objektpfad: {value}", line=line, column=column
        )
    return DBaseObjectPath(tuple(value.split(".")), line, column)


def _dbase_parent_path(target: DBaseObjectPath) -> DBaseObjectPath:
    parts = target.canonical_parts
    if len(parts) <= 1:
        return DBaseObjectPath(("_app",), target.line, target.column)
    return DBaseObjectPath(tuple(parts[:-1]), target.line, target.column)


def _dbase_parse_session_login_arguments(
    raw_arguments: str,
    *,
    raw_line: str,
    parse_source: str,
    line_start_offset: int,
    filename: str,
) -> Tuple[DBaseExpression, DBaseExpression, DBaseExpression]:
    login_pos = raw_line.casefold().find("login")
    synthetic = "Login(" + raw_arguments + ")"
    tokens = _tokenize_dbase_statement(
        synthetic,
        filename=filename,
        base_offset=line_start_offset + max(0, login_pos),
        source=parse_source,
    )
    parser = _DBaseExpressionParser(tokens, filename=filename)
    expression = parser.parse_expression()
    parser._expect_eof()
    if not isinstance(expression, DBaseCallExpression) or expression.name.casefold() != "login":
        raise DBaseCompilerError(
            "SESSION.Login konnte nicht geparst werden.",
            line=1,
            column=1,
            filename=filename,
        )
    if len(expression.arguments) != 3:
        raise DBaseCompilerError(
            "SESSION.Login(username, password, group) erwartet genau drei Parameter.",
            line=expression.line,
            column=expression.column,
            filename=filename,
        )
    return expression.arguments[0], expression.arguments[1], expression.arguments[2]


def _dbase_decode_property_string(text: str, *, filename: str, line: int, column: int) -> str:
    raw = str(text).strip()
    if len(raw) < 2 or raw[0] not in {'\"', "'"}:
        raise DBaseCompilerError(
            "Stringliteral erwartet.", line=line, column=column, filename=filename
        )
    value, end = _decode_dbase_string(raw, 0, line=line, column=column, filename=filename)
    if raw[end:].strip():
        raise DBaseCompilerError(
            "Unerwarteter Text nach dem Stringliteral.",
            line=line, column=column + end, filename=filename,
        )
    return value


def _dbase_parse_menu_property(text: str, *, filename: str, line: int) -> DBaseMenuProperty:
    match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$", text)
    if not match:
        raise DBaseCompilerError(
            "WITH erwartet eine Property-Zuweisung NAME = WERT.",
            line=line, column=1, filename=filename,
        )
    name, rhs = match.group(1), match.group(2)
    key = name.casefold()
    column = max(1, text.find(name) + 1)
    if key in {"text", "shortcut"}:
        return DBaseMenuProperty(
            name, "string",
            _dbase_decode_property_string(rhs, filename=filename, line=line, column=column),
            line, column,
        )
    if key == "separator":
        state = rhs.casefold()
        if state not in {"true", "false"}:
            raise DBaseCompilerError(
                "separator erwartet TRUE oder FALSE.",
                line=line, column=column, filename=filename,
            )
        return DBaseMenuProperty(name, "bool", state == "true", line, column)
    if key == "onclick":
        callback = re.fullmatch(r"(?i)class\s*::\s*([A-Za-z_][A-Za-z0-9_]*)", rhs)
        if callback:
            return DBaseMenuProperty(name, "callback", callback.group(1), line, column)
        block = re.fullmatch(r"\{(.*)\}", rhs, flags=re.S)
        if block:
            return DBaseMenuProperty(name, "codeblock", block.group(1), line, column)
        raise DBaseCompilerError(
            "onClick erwartet class::MEMBER oder einen Codeblock {...}.",
            line=line, column=column, filename=filename,
        )
    raise DBaseCompilerError(
        f"Unbekannte MENU-Property '{name}'. Erlaubt: text, onClick, shortCut, separator.",
        line=line, column=column, filename=filename,
    )


def _dbase_parse_property_expression(
    rhs: str,
    *,
    raw_line: str,
    parse_source: str,
    line_start_offset: int,
    line: int,
    filename: str,
) -> DBaseExpression:
    value = str(rhs).strip()
    if value.startswith("<"):
        raise DBaseCompilerError(
            "Die alte _app.menuFile = <menu.mnu>-Schreibweise wird nicht mehr unterstuetzt. "
            "Verwende _app.menuFile = \"menu.mnu\" oder einen String-Ausdruck.",
            line=line,
            column=max(1, raw_line.find(value) + 1),
            filename=filename,
        )
    rhs_column = raw_line.find(rhs) + 1
    rhs_offset = line_start_offset + max(0, rhs_column - 1)
    tokens = _tokenize_dbase_statement(
        rhs, filename=filename, base_offset=rhs_offset, source=parse_source
    )
    parser = _DBaseExpressionParser(tokens, filename=filename)
    expression = parser.parse_expression()
    parser._expect_eof()
    return expression


def _dbase_constant_condition_value(
    condition: DBaseCondition,
    *,
    env: Mapping[str, DBaseValue],
    routines: Mapping[str, DBaseRoutineDefinition],
    filename: str,
    call_stack: Tuple[str, ...],
) -> bool:
    left = _dbase_constant_expression_value(
        condition.left, env=env, routines=routines, filename=filename, call_stack=call_stack
    )
    right = _dbase_constant_expression_value(
        condition.right, env=env, routines=routines, filename=filename, call_stack=call_stack
    )
    return _compare_dbase_values(
        left, right, condition.operator,
        line=condition.line, column=condition.column, filename=filename,
    )


def _dbase_constant_function_value(
    definition: DBaseRoutineDefinition,
    arguments: Tuple[DBaseValue, ...],
    *,
    env: Mapping[str, DBaseValue],
    routines: Mapping[str, DBaseRoutineDefinition],
    filename: str,
    call_stack: Tuple[str, ...],
) -> DBaseValue:
    key = definition.name.casefold()
    if key in call_stack:
        raise DBaseCompilerError(
            f"Rekursiver Aufruf von '{definition.name}' kann fuer _app.menuFile nicht zur Compile-Zeit ausgewertet werden.",
            line=definition.line, column=definition.column, filename=filename,
        )
    if not definition.is_function:
        raise DBaseCompilerError(
            f"_app.menuFile erwartet einen Stringwert; PROCEDURE '{definition.name}' liefert keinen Wert.",
            line=definition.line, column=definition.column, filename=filename,
        )
    if len(arguments) != len(definition.parameters):
        raise DBaseCompilerError(
            f"FUNCTION '{definition.name}' erwartet {len(definition.parameters)} Parameter.",
            line=definition.line, column=definition.column, filename=filename,
        )

    local_env = {str(k).casefold(): v for k, v in env.items()}
    for parameter, value in zip(definition.parameters, arguments):
        local_env[parameter.casefold()] = value

    def run_sequence(sequence: Tuple[object, ...]) -> Optional[DBaseValue]:
        for statement in sequence:
            if isinstance(statement, DBaseAssignmentStatement):
                local_env[statement.name.casefold()] = _dbase_constant_expression_value(
                    statement.expression,
                    env=local_env,
                    routines=routines,
                    filename=filename,
                    call_stack=call_stack + (key,),
                )
                continue
            if isinstance(statement, DBaseReturnStatement):
                if statement.expression is None:
                    raise DBaseCompilerError(
                        f"FUNCTION '{definition.name}' muss fuer _app.menuFile einen Wert liefern.",
                        line=statement.line, column=statement.column, filename=filename,
                    )
                return _dbase_constant_expression_value(
                    statement.expression,
                    env=local_env,
                    routines=routines,
                    filename=filename,
                    call_stack=call_stack + (key,),
                )
            if isinstance(statement, DBaseIfStatement):
                branch_taken = False
                for branch in statement.branches:
                    if branch.condition is None or _dbase_constant_condition_value(
                        branch.condition,
                        env=local_env,
                        routines=routines,
                        filename=filename,
                        call_stack=call_stack + (key,),
                    ):
                        branch_taken = True
                        result = run_sequence(branch.body)
                        if result is not None:
                            return result
                        break
                if not branch_taken:
                    continue
                continue
            # Ausgaben, SET-Anweisungen und reine Aufrufe sind keine sichere
            # Compile-Time-Grundlage fuer einen Dateipfad.
            if isinstance(statement, (DBasePrintStatement, DBaseSetFormatStatement,
                                      DBaseSetDebugStatement, DBaseSetColorStatement,
                                      DBaseClearScreenStatement, DBaseSetBorderColorStatement,
                                      DBaseCallStatement)):
                raise DBaseCompilerError(
                    f"FUNCTION '{definition.name}' enthaelt Laufzeitlogik und kann fuer _app.menuFile "
                    "nicht zur Compile-Zeit ausgewertet werden.",
                    line=getattr(statement, 'line', definition.line),
                    column=getattr(statement, 'column', definition.column),
                    filename=filename,
                )
        return None

    result = run_sequence(definition.body)
    if result is None:
        raise DBaseCompilerError(
            f"FUNCTION '{definition.name}' liefert keinen zur Compile-Zeit bestimmbaren Wert fuer _app.menuFile.",
            line=definition.line, column=definition.column, filename=filename,
        )
    return result


def _dbase_constant_expression_value(
    expression: DBaseExpression,
    *,
    env: Mapping[str, DBaseValue],
    routines: Mapping[str, DBaseRoutineDefinition],
    filename: str,
    call_stack: Tuple[str, ...] = (),
) -> DBaseValue:
    if isinstance(expression, DBaseLiteralExpression):
        return DBaseValue(expression.value_type, expression.value)
    if isinstance(expression, DBaseIdentifierExpression):
        value = env.get(expression.name.casefold())
        if value is None:
            raise DBaseCompilerError(
                f"_app.menuFile: Variable '{expression.name}' ist an dieser Stelle nicht als Konstante bekannt.",
                line=expression.line, column=expression.column, filename=filename,
            )
        return value
    if isinstance(expression, DBaseCallExpression):
        definition = routines.get(expression.name.casefold())
        if definition is None:
            raise DBaseCompilerError(
                f"_app.menuFile: Funktion '{expression.name}' ist nicht als dBase FUNCTION definiert.",
                line=expression.line, column=expression.column, filename=filename,
            )
        args = tuple(
            _dbase_constant_expression_value(
                argument, env=env, routines=routines, filename=filename, call_stack=call_stack
            )
            for argument in expression.arguments
        )
        return _dbase_constant_function_value(
            definition, args, env=env, routines=routines, filename=filename, call_stack=call_stack
        )
    if isinstance(expression, DBaseUnaryExpression):
        operand = _dbase_constant_expression_value(
            expression.operand, env=env, routines=routines, filename=filename, call_stack=call_stack
        )
        if operand.kind != "number":
            raise DBaseCompilerError(
                f"_app.menuFile: unaerer Operator '{expression.operator}' erwartet eine Zahl.",
                line=expression.line, column=expression.column, filename=filename,
            )
        value = Decimal(operand.value)
        return DBaseValue("number", value if expression.operator == "+" else -value)
    if isinstance(expression, DBaseBinaryExpression):
        left = _dbase_constant_expression_value(
            expression.left, env=env, routines=routines, filename=filename, call_stack=call_stack
        )
        right = _dbase_constant_expression_value(
            expression.right, env=env, routines=routines, filename=filename, call_stack=call_stack
        )
        if expression.operator == "+" and (left.kind in _STRING_KINDS or right.kind in _STRING_KINDS):
            return DBaseValue(
                "string", _constant_concat_text(left) + _constant_concat_text(right)
            )
        if left.kind != "number" or right.kind != "number":
            raise DBaseCompilerError(
                f"_app.menuFile: Operator '{expression.operator}' ist fuer diesen String-Ausdruck ungueltig.",
                line=expression.line, column=expression.column, filename=filename,
            )
        a = Decimal(left.value)
        b = Decimal(right.value)
        if expression.operator == "+":
            result = a + b
        elif expression.operator == "-":
            result = a - b
        elif expression.operator == "*":
            result = a * b
        elif expression.operator == "/":
            if b == 0:
                raise DBaseCompilerError(
                    "Division durch 0 in _app.menuFile-Ausdruck.",
                    line=expression.line, column=expression.column, filename=filename,
                )
            with localcontext() as context:
                context.prec = 32
                result = a / b
        else:
            raise AssertionError(expression.operator)
        return DBaseValue("number", result)
    raise DBaseCompilerError(
        "_app.menuFile enthaelt keinen zur Compile-Zeit auswertbaren String-Ausdruck.",
        line=expression.line, column=expression.column, filename=filename,
    )


def _dbase_resolve_menu_file_expression(
    expression: DBaseExpression,
    *,
    before_line: int,
    base_statements: Tuple[object, ...],
    filename: str,
) -> str:
    routines = {
        statement.name.casefold(): statement
        for statement in base_statements
        if isinstance(statement, DBaseRoutineDefinition)
    }
    env: Dict[str, DBaseValue] = {}
    for statement in sorted(base_statements, key=lambda item: getattr(item, "line", 10**9)):
        if getattr(statement, "line", 10**9) >= before_line:
            continue
        if not isinstance(statement, DBaseAssignmentStatement):
            continue
        try:
            env[statement.name.casefold()] = _dbase_constant_expression_value(
                statement.expression,
                env=env,
                routines=routines,
                filename=filename,
            )
        except DBaseCompilerError:
            # Eine dynamische Zwischenvariable darf existieren; sie ist nur dann
            # unzulaessig, wenn menuFile tatsaechlich von ihr abhaengt.
            env.pop(statement.name.casefold(), None)

    value = _dbase_constant_expression_value(
        expression, env=env, routines=routines, filename=filename
    )
    if value.kind not in _STRING_KINDS:
        raise DBaseCompilerError(
            "_app.menuFile erwartet einen String-Ausdruck.",
            line=expression.line, column=expression.column, filename=filename,
        )
    return str(value.value).strip()

def _dbase_validate_direct_color_literal(
    expression: DBaseExpression, *, filename: str
) -> DBaseExpression:
    if not isinstance(expression, DBaseLiteralExpression):
        return expression
    if expression.value_type not in _STRING_KINDS:
        raise DBaseCompilerError(
            "_app.colorNormal erwartet einen Farbnamen als String, eine String-Variable/Funktion oder RGB(...).",
            line=expression.line, column=expression.column, filename=filename,
        )
    value = str(expression.value)
    canonical = _DBASE_SYSTEM_COLOR_LOOKUP.get(value.casefold())
    if canonical is None:
        raise DBaseCompilerError(
            f"Unbekannte Windows-Systemfarbe '{value}'. Verwende einen gueltigen Namen in Anfuehrungszeichen oder RGB(...).",
            line=expression.line, column=expression.column, filename=filename,
        )
    return DBaseLiteralExpression(
        line=expression.line, column=expression.column, value_type="string",
        value=canonical, text=expression.text,
    )


def _dbase_mask_line(line_text: str) -> str:
    return "".join("\t" if ch == "\t" else " " for ch in line_text)


def parse_dbase_statements(
    source: str,
    *,
    filename: str = "<dBase>",
    target: str = "pe32",
    _menu_include_stack: Tuple[str, ...] = (),
) -> Tuple[object, ...]:
    """Stage-12-Syntax plus globales _app-/MENU-Objektmodell.

    Stage 13 implementiert zunaechst die eingebauten Klassen APPLICATION (_app)
    und MENU. ``this`` ist auf Top-Level ein Alias fuer ``_app``. ``class::X``
    referenziert eine parameterlose PROCEDURE X als nativen Qt-onClick-Callback.
    """
    # Präprozessor zuerst, damit auch Makros in Menuedateien funktionieren.
    frontend = preprocess_dbase_source(source, filename=filename, target=target)
    parse_source = frontend.preprocessed_source or frontend.source
    lines = parse_source.splitlines(keepends=True)
    masked = list(lines)
    events: list[tuple[int, int, object, Tuple[object, ...]]] = []
    event_serial = 0

    i = 0
    while i < len(lines):
        raw_with_nl = lines[i]
        raw = raw_with_nl.rstrip("\r\n")
        line_no = i + 1

        color_normal = _DBASE_COLOR_NORMAL_RE.fullmatch(raw)
        if color_normal:
            rhs = color_normal.group(2)
            rhs_column = raw.find(rhs) + 1
            # Tokenpositionen auf die echte physische Quelldatei beziehen.
            line_start_offset = sum(len(item) for item in lines[:i])
            rhs_offset = line_start_offset + max(0, rhs_column - 1)
            tokens = _tokenize_dbase_statement(
                rhs, filename=filename, base_offset=rhs_offset, source=parse_source
            )
            parser = _DBaseExpressionParser(tokens, filename=filename)
            expression = parser.parse_expression()
            parser._expect_eof()
            expression = _dbase_validate_direct_color_literal(expression, filename=filename)
            statement = DBaseAppColorStatement(
                property_name="colorNormal",
                expression=expression,
                line=line_no,
                column=max(1, raw.lower().find("colornormal") + 1),
            )
            masked[i] = _dbase_mask_line(raw) + raw_with_nl[len(raw):]
            events.append((line_no, event_serial, statement, ()))
            event_serial += 1
            i += 1
            continue

        local_database = _DBASE_LOCAL_DATABASE_RE.fullmatch(raw)
        if local_database:
            statement = DBaseLocalObjectDeclaration(
                name=local_database.group(1),
                class_name="DATABASE",
                line=line_no,
                column=max(1, raw.lower().find("local") + 1),
            )
            masked[i] = _dbase_mask_line(raw) + raw_with_nl[len(raw):]
            events.append((line_no, event_serial, statement, ()))
            event_serial += 1
            i += 1
            continue

        new_database = _DBASE_NEW_DATABASE_RE.fullmatch(raw)
        if new_database:
            target_path = _dbase_object_path(
                new_database.group(1), line_no, max(1, raw.find(new_database.group(1)) + 1)
            )
            owner_path = _dbase_parent_path(target_path)
            statement = DBaseNewObjectStatement(
                target=target_path, class_name="DATABASE", owner=owner_path,
                line=line_no, column=max(1, raw.find(new_database.group(1)) + 1),
            )
            masked[i] = _dbase_mask_line(raw) + raw_with_nl[len(raw):]
            events.append((line_no, event_serial, statement, ()))
            event_serial += 1
            i += 1
            continue

        database_property = _DBASE_DATABASE_PROPERTY_RE.fullmatch(raw)
        if database_property:
            target_text = database_property.group(1)
            property_name = database_property.group(2)
            rhs = database_property.group(3)
            target_path = _dbase_object_path(
                target_text, line_no, max(1, raw.find(target_text) + 1)
            )
            object_value = None
            expression = None
            if property_name.casefold() == "session":
                object_value = _dbase_object_path(
                    rhs, line_no, max(1, raw.find(rhs) + 1)
                )
            elif property_name.casefold() == "active" and rhs.strip().casefold() in {"true", "false"}:
                flag = Decimal(1 if rhs.strip().casefold() == "true" else 0)
                expression = DBaseLiteralExpression(
                    line=line_no, column=max(1, raw.find(rhs) + 1),
                    value_type="number", value=flag, text=rhs.strip(),
                )
            else:
                line_start_offset = sum(len(item) for item in lines[:i])
                expression = _dbase_parse_property_expression(
                    rhs, raw_line=raw, parse_source=parse_source,
                    line_start_offset=line_start_offset, line=line_no, filename=filename,
                )
            statement = DBaseObjectPropertyStatement(
                target=target_path, property_name=property_name,
                expression=expression, object_value=object_value,
                line=line_no, column=max(1, raw.find(property_name) + 1),
            )
            masked[i] = _dbase_mask_line(raw) + raw_with_nl[len(raw):]
            events.append((line_no, event_serial, statement, ()))
            event_serial += 1
            i += 1
            continue

        database_method = _DBASE_DATABASE_METHOD_RE.fullmatch(raw)
        if database_method:
            target_text = database_method.group(1)
            statement = DBaseObjectMethodStatement(
                target=_dbase_object_path(
                    target_text, line_no, max(1, raw.find(target_text) + 1)
                ),
                method_name=database_method.group(2),
                line=line_no,
                column=max(1, raw.find(database_method.group(2)) + 1),
            )
            masked[i] = _dbase_mask_line(raw) + raw_with_nl[len(raw):]
            events.append((line_no, event_serial, statement, ()))
            event_serial += 1
            i += 1
            continue

        new_session = _DBASE_NEW_SESSION_RE.fullmatch(raw)
        if new_session:
            target_path = _dbase_object_path(
                new_session.group(1), line_no, max(1, raw.find(new_session.group(1)) + 1)
            )
            owner_path = _dbase_parent_path(target_path)
            statement = DBaseNewObjectStatement(
                target=target_path, class_name="SESSION", owner=owner_path,
                line=line_no, column=max(1, raw.find(new_session.group(1)) + 1),
            )
            masked[i] = _dbase_mask_line(raw) + raw_with_nl[len(raw):]
            events.append((line_no, event_serial, statement, ()))
            event_serial += 1
            i += 1
            continue

        session_login = _DBASE_SESSION_LOGIN_RE.fullmatch(raw)
        if session_login:
            result_name = session_login.group(1)
            target_text = session_login.group(2)
            target_path = _dbase_object_path(
                target_text, line_no, max(1, raw.find(target_text) + 1)
            )
            line_start_offset = sum(len(item) for item in lines[:i])
            username, password, group = _dbase_parse_session_login_arguments(
                session_login.group(3),
                raw_line=raw,
                parse_source=parse_source,
                line_start_offset=line_start_offset,
                filename=filename,
            )
            statement = DBaseSessionLoginStatement(
                result_name=result_name,
                target=target_path,
                username=username,
                password=password,
                group=group,
                line=line_no,
                column=max(1, raw.find(result_name) + 1),
            )
            masked[i] = _dbase_mask_line(raw) + raw_with_nl[len(raw):]
            events.append((line_no, event_serial, statement, ()))
            event_serial += 1
            i += 1
            continue

        menu_file = _DBASE_MENUFILE_RE.fullmatch(raw)
        if menu_file:
            rhs = menu_file.group(2)
            line_start_offset = sum(len(item) for item in lines[:i])
            expression = _dbase_parse_property_expression(
                rhs,
                raw_line=raw,
                parse_source=parse_source,
                line_start_offset=line_start_offset,
                line=line_no,
                filename=filename,
            )
            statement = DBaseMenuFileStatement(
                expression=expression,
                resolved_path="",
                line=line_no,
                column=max(1, raw.find(menu_file.group(1)) + 1),
            )
            masked[i] = _dbase_mask_line(raw) + raw_with_nl[len(raw):]
            events.append((line_no, event_serial, statement, ()))
            event_serial += 1
            i += 1
            continue

        new_menu = _DBASE_NEW_MENU_RE.fullmatch(raw)
        if new_menu:
            target_path = _dbase_object_path(new_menu.group(1), line_no)
            owner_path = _dbase_object_path(new_menu.group(2), line_no)
            statement = DBaseNewObjectStatement(
                target=target_path, class_name="MENU", owner=owner_path,
                line=line_no, column=max(1, raw.find(new_menu.group(1)) + 1),
            )
            masked[i] = _dbase_mask_line(raw) + raw_with_nl[len(raw):]
            events.append((line_no, event_serial, statement, ()))
            event_serial += 1
            i += 1
            continue

        with_match = _DBASE_WITH_RE.fullmatch(raw)
        if with_match:
            start_line = line_no
            target_path = _dbase_object_path(with_match.group(1), line_no)
            properties: list[DBaseMenuProperty] = []
            masked[i] = _dbase_mask_line(raw) + raw_with_nl[len(raw):]
            i += 1
            while i < len(lines):
                body_with_nl = lines[i]
                body = body_with_nl.rstrip("\r\n")
                body_line = i + 1
                masked[i] = _dbase_mask_line(body) + body_with_nl[len(body):]
                if _DBASE_ENDWITH_RE.fullmatch(body):
                    break
                if body.strip():
                    properties.append(
                        _dbase_parse_menu_property(body, filename=filename, line=body_line)
                    )
                i += 1
            if i >= len(lines):
                raise DBaseCompilerError(
                    "WITH-Block ist nicht mit ENDWITH abgeschlossen.",
                    line=start_line, column=1, filename=filename,
                )
            statement = DBaseWithStatement(
                target=target_path, properties=tuple(properties),
                line=start_line, column=max(1, raw.lower().find("with") + 1),
            )
            events.append((start_line, event_serial, statement, ()))
            event_serial += 1
            i += 1
            continue

        if _DBASE_ENDWITH_RE.fullmatch(raw):
            raise DBaseCompilerError(
                "Unerwartetes ENDWITH ohne passenden WITH-Block.",
                line=line_no, column=1, filename=filename,
            )
        i += 1

    base_source = "".join(masked)
    base_statements = _stage12_parse_dbase_statements(
        base_source, filename=filename, target=target
    )

    # Stage 24: menuFile ist ein normaler String-Ausdruck. Da die .mnu-Datei
    # Quellcode enthaelt, muss der Ausdruck beim Kompilieren bestimmbar sein.
    # Makros sind bereits expandiert; konstante Variablen und dBase-FUNCTIONs
    # werden hier ebenfalls ausgewertet. Ein leerer String bedeutet: Standardmenue.
    resolved_events: list[tuple[int, int, object, Tuple[object, ...]]] = []
    for event_line, event_serial_value, event, included in events:
        if not isinstance(event, DBaseMenuFileStatement):
            resolved_events.append((event_line, event_serial_value, event, included))
            continue

        path_value = _dbase_resolve_menu_file_expression(
            event.expression,
            before_line=event.line,
            base_statements=tuple(base_statements),
            filename=filename,
        )
        event = DBaseMenuFileStatement(
            expression=event.expression,
            resolved_path=path_value,
            line=event.line,
            column=event.column,
        )
        if not path_value:
            resolved_events.append((event_line, event_serial_value, event, ()))
            continue

        base = Path(filename).resolve().parent if filename and not str(filename).startswith("<") else Path.cwd()
        menu_path = Path(path_value)
        if not menu_path.is_absolute():
            menu_path = (base / menu_path).resolve()
        key = str(menu_path).casefold()
        if key in {item.casefold() for item in _menu_include_stack}:
            raise DBaseCompilerError(
                f"Zyklische _app.menuFile-Einbindung: {menu_path}",
                line=event.line, column=event.column, filename=filename,
            )
        if not menu_path.is_file():
            raise DBaseCompilerError(
                f"Menuedatei nicht gefunden: {menu_path}",
                line=event.line, column=event.column, filename=filename,
            )
        included_statements = parse_dbase_statements(
            menu_path.read_text(encoding="utf-8"),
            filename=str(menu_path), target=target,
            _menu_include_stack=_menu_include_stack + (str(menu_path),),
        )
        resolved_events.append((event_line, event_serial_value, event, included_statements))
    events = resolved_events

    # Hauptquelldatei nach physischer Zeile mergen. Eingebundene .mnu-Dateien
    # bleiben geschlossen an der menuFile-Zuweisung und behalten intern ihre
    # eigene Reihenfolge.
    base_items = sorted(
        ((getattr(statement, "line", 10**9), index, statement)
         for index, statement in enumerate(base_statements)),
        key=lambda item: (item[0], item[1]),
    )
    event_items = sorted(events, key=lambda item: (item[0], item[1]))
    result: list[object] = []
    bi = ei = 0
    while bi < len(base_items) or ei < len(event_items):
        if ei < len(event_items) and (
            bi >= len(base_items) or event_items[ei][0] <= base_items[bi][0]
        ):
            _line, _serial, event, included = event_items[ei]
            result.append(event)
            result.extend(included)
            ei += 1
        else:
            result.append(base_items[bi][2])
            bi += 1
    return tuple(result)


class _DBaseProgramAnalyzer(_Stage12ProgramAnalyzer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object_classes: Dict[Tuple[str, ...], str] = {}
        self.declared_object_classes: Dict[str, str] = {}
        # Stage 25: globaler, read-only Loginstatus. Der Wert wird bei jeder
        # Verwendung zur Laufzeit aus der Qt5-Bridge gelesen und besitzt
        # deshalb absichtlich keinen statischen Datenslot.
        self.global_symbols["loginsession"] = _DBaseSymbolState(
            name="LOGINSESSION",
            label="__dbase_builtin_loginsession",
            value_type="number",
            constant_value=None,
            dynamic=True,
            last_line=0,
            last_column=0,
        )

    @staticmethod
    def _object_key(path: DBaseObjectPath) -> Tuple[str, ...]:
        return tuple(part.casefold() for part in path.canonical_parts)

    def _require_object_class(self, path: DBaseObjectPath, expected: str, *, line: int, column: int) -> None:
        class_name = self.object_classes.get(self._object_key(path))
        if class_name != expected.upper():
            raise DBaseCompilerError(
                f"Objekt '{path.dotted}' ist nicht als {expected.upper()} erzeugt worden.",
                line=line, column=column, filename=self.filename,
            )

    def _analyze_database_property(
        self, statement: DBaseObjectPropertyStatement, globals_work: Dict[str, _DBaseSymbolState]
    ) -> None:
        self._require_object_class(
            statement.target, "DATABASE", line=statement.line, column=statement.column
        )
        key = statement.property_name.casefold()
        if key == "session":
            if statement.object_value is None:
                raise DBaseCompilerError(
                    "DATABASE.session erwartet eine SESSION-Objektreferenz.",
                    line=statement.line, column=statement.column, filename=self.filename,
                )
            self._require_object_class(
                statement.object_value, "SESSION", line=statement.line, column=statement.column
            )
            return

        if statement.expression is None:
            raise AssertionError(statement.property_name)
        info = self.analyze_expression(
            statement.expression, symbols=globals_work, expression_info=self.expression_info,
            call_bindings=self.call_bindings,
        )
        if key in {"path", "databasename", "username", "password", "alias"}:
            if info.kind not in _STRING_KINDS:
                raise DBaseCompilerError(
                    f"DATABASE.{statement.property_name} erwartet String/Char.",
                    line=statement.expression.line, column=statement.expression.column, filename=self.filename,
                )
            return
        if key == "active":
            if info.kind != "number":
                raise DBaseCompilerError(
                    "DATABASE.active erwartet TRUE/FALSE oder 0/1.",
                    line=statement.expression.line, column=statement.expression.column, filename=self.filename,
                )
            if info.constant_value is not None:
                value = Decimal(info.constant_value.value)
                if value not in {Decimal(0), Decimal(1)}:
                    raise DBaseCompilerError(
                        "DATABASE.active erwartet TRUE/FALSE oder 0/1.",
                        line=statement.expression.line, column=statement.expression.column, filename=self.filename,
                    )
            return
        raise DBaseCompilerError(
            f"Unbekannte DATABASE-Eigenschaft '{statement.property_name}'.",
            line=statement.line, column=statement.column, filename=self.filename,
        )

    def _analyze_database_method(self, statement: DBaseObjectMethodStatement) -> None:
        self._require_object_class(
            statement.target, "DATABASE", line=statement.line, column=statement.column
        )
        if statement.method_name.casefold() not in {"open", "close", "commit"}:
            raise DBaseCompilerError(
                f"Unbekannte DATABASE-Methode '{statement.method_name}'.",
                line=statement.line, column=statement.column, filename=self.filename,
            )

    def _analyze_session_login(
        self,
        statement: DBaseSessionLoginStatement,
        globals_work: Dict[str, _DBaseSymbolState],
    ) -> None:
        object_key = self._object_key(statement.target)
        class_name = self.object_classes.get(object_key)
        if class_name != "SESSION":
            raise DBaseCompilerError(
                f"Objekt '{statement.target.dotted}' ist vor Login() nicht als SESSION erzeugt worden.",
                line=statement.line, column=statement.column, filename=self.filename,
            )

        for label, expression in (
            ("Benutzername", statement.username),
            ("Passwort", statement.password),
            ("Gruppe", statement.group),
        ):
            info = self.analyze_expression(
                expression,
                symbols=globals_work,
                expression_info=self.expression_info,
                call_bindings=self.call_bindings,
            )
            if info.kind not in _STRING_KINDS:
                raise DBaseCompilerError(
                    f"SESSION.Login: {label} muss String/Char sein.",
                    line=expression.line, column=expression.column, filename=self.filename,
                )

        key = statement.result_name.casefold()
        old = globals_work.get(key)
        label = old.label if old is not None else self.global_labels.setdefault(
            key, _symbol_label(statement.result_name)
        )
        state = _DBaseSymbolState(
            name=statement.result_name,
            label=label,
            value_type="number",
            constant_value=None,
            dynamic=True,
            last_line=statement.line,
            last_column=statement.column,
        )
        globals_work[key] = state
        self.all_global_states[key] = state

    def analyze_expression(
        self,
        expression: DBaseExpression,
        *,
        symbols: Mapping[str, _DBaseSymbolState],
        expression_info: Dict[DBaseExpression, _DBaseExpressionInfo],
        call_bindings: Dict[DBaseCallExpression, _DBaseCallBinding],
        require_value: bool = True,
    ) -> _DBaseExpressionInfo:
        # RGB(rr,gg,bb) ist ein Compiler-Builtin. Die drei Kanaele muessen in
        # dieser Stufe konstante Ganzzahlen 0..255 (00h..FFh) ergeben. Das
        # Resultat ist ein normaler Stringwert "#RRGGBB" und kann deshalb
        # auch Variablen oder FUNCTION-Rueckgaben durchlaufen.
        if isinstance(expression, DBaseCallExpression) and expression.name.casefold() == "rgb":
            cached = expression_info.get(expression)
            if cached is not None:
                return cached
            if len(expression.arguments) != 3:
                raise DBaseCompilerError(
                    "RGB(rr,gg,bb) erwartet genau drei Farbkomponenten.",
                    line=expression.line, column=expression.column, filename=self.filename,
                )
            values: list[int] = []
            for argument in expression.arguments:
                # Komfortsyntax speziell fuer RGB: genau zwei Hexdigits werden
                # als Hexkanal gelesen, also RGB(FF,00,80) = #FF0080.
                raw_hex = None
                if isinstance(argument, DBaseIdentifierExpression):
                    match = re.fullmatch(r"([0-9A-Fa-f]{2})(?:[hH])?", argument.name)
                    if match:
                        raw_hex = int(match.group(1), 16)
                elif isinstance(argument, DBaseLiteralExpression):
                    raw = str(argument.text).strip()
                    if re.fullmatch(r"[0-9A-Fa-f]{2}", raw):
                        raw_hex = int(raw, 16)
                if raw_hex is not None:
                    values.append(raw_hex)
                    continue

                arg_info = self.analyze_expression(
                    argument, symbols=symbols, expression_info=expression_info,
                    call_bindings=call_bindings,
                )
                if arg_info.kind != "number" or arg_info.constant_value is None:
                    raise DBaseCompilerError(
                        "RGB(rr,gg,bb) erwartet konstante numerische Komponenten im Bereich 00h..FFh.",
                        line=argument.line, column=argument.column, filename=self.filename,
                    )
                number = Decimal(arg_info.constant_value.value)
                if number != number.to_integral_value() or number < 0 or number > 255:
                    raise DBaseCompilerError(
                        "RGB-Komponenten muessen Ganzzahlen von 0 bis 255 (00h..FFh) sein.",
                        line=argument.line, column=argument.column, filename=self.filename,
                    )
                values.append(int(number))
            text = "#%02X%02X%02X" % tuple(values)
            info = _DBaseExpressionInfo(
                kind="string", constant_value=DBaseValue("string", text), dynamic=False
            )
            expression_info[expression] = info
            return info
        return super().analyze_expression(
            expression, symbols=symbols, expression_info=expression_info,
            call_bindings=call_bindings, require_value=require_value,
        )

    def _analyze_app_color(
        self, statement: DBaseAppColorStatement, globals_work: Dict[str, _DBaseSymbolState]
    ) -> None:
        expression = statement.expression
        # Ein Funktionsname ohne dBase-Definition darf hier nicht als externer
        # C-Call durchrutschen. Genau das unterscheidet ActiveBorder() von einer
        # vorher definierten FUNCTION ActiveBorder().
        if isinstance(expression, DBaseCallExpression) and expression.name.casefold() != "rgb":
            definition = self.routines.get(expression.name.casefold())
            if definition is None or definition.line >= statement.line:
                raise DBaseCompilerError(
                    f"Funktion '{expression.name}' fuer _app.colorNormal muss vor ihrer Verwendung definiert sein.",
                    line=expression.line, column=expression.column, filename=self.filename,
                )
        info = self.analyze_expression(
            expression, symbols=globals_work, expression_info=self.expression_info,
            call_bindings=self.call_bindings,
        )
        if info.kind not in _STRING_KINDS:
            raise DBaseCompilerError(
                "_app.colorNormal erwartet einen Stringfarbnamen, eine String-Variable/Funktion oder RGB(...).",
                line=expression.line, column=expression.column, filename=self.filename,
            )
        if info.constant_value is not None:
            value = str(info.constant_value.value)
            valid_system = value.casefold() in _DBASE_SYSTEM_COLOR_LOOKUP
            valid_rgb = bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", value))
            if not valid_system and not valid_rgb:
                raise DBaseCompilerError(
                    f"Ungueltiger Farbwert '{value}' fuer _app.colorNormal.",
                    line=expression.line, column=expression.column, filename=self.filename,
                )

    def _validate_menu_statements(self, sequence: Tuple[object, ...]) -> None:
        for statement in sequence:
            if not isinstance(statement, DBaseWithStatement):
                continue
            for prop in statement.properties:
                if prop.value_kind != "callback":
                    continue
                definition = self.routines.get(str(prop.value).casefold())
                if definition is None:
                    raise DBaseCompilerError(
                        f"onClick-Member '{prop.value}' ist nicht definiert.",
                        line=prop.line, column=prop.column, filename=self.filename,
                    )
                if not definition.is_procedure or definition.parameters:
                    raise DBaseCompilerError(
                        f"onClick-Member '{definition.name}' muss eine parameterlose PROCEDURE sein.",
                        line=prop.line, column=prop.column, filename=self.filename,
                    )
                self.instantiate_routine(definition, ())

    @staticmethod
    def _without_menu(sequence: Tuple[object, ...]) -> Tuple[object, ...]:
        return tuple(
            statement for statement in sequence
            if not isinstance(statement, (DBaseLocalObjectDeclaration, DBaseNewObjectStatement, DBaseSessionLoginStatement, DBaseObjectPropertyStatement, DBaseObjectMethodStatement, DBaseWithStatement, DBaseMenuFileStatement, DBaseAppColorStatement))
        )

    def _analyze_top_sequence(self, sequence, globals_work):
        seq = tuple(sequence)
        self._validate_menu_statements(seq)
        for statement in seq:
            if isinstance(statement, DBaseLocalObjectDeclaration):
                key = statement.name.casefold()
                existing = self.declared_object_classes.get(key)
                if existing is not None and existing != statement.class_name.upper():
                    raise DBaseCompilerError(
                        f"Lokaler Objektalias '{statement.name}' wurde bereits als {existing} deklariert.",
                        line=statement.line, column=statement.column, filename=self.filename,
                    )
                self.declared_object_classes[key] = statement.class_name.upper()
                continue
            if isinstance(statement, DBaseAppColorStatement):
                self._analyze_app_color(statement, globals_work)
                continue
            if isinstance(statement, DBaseNewObjectStatement):
                class_name = statement.class_name.upper()
                if len(statement.target.canonical_parts) == 1:
                    declared = self.declared_object_classes.get(statement.target.canonical_parts[0].casefold())
                    if declared is not None and declared != class_name:
                        raise DBaseCompilerError(
                            f"Objekt '{statement.target.dotted}' ist als {declared} deklariert, nicht als {class_name}.",
                            line=statement.line, column=statement.column, filename=self.filename,
                        )
                self.object_classes[self._object_key(statement.target)] = class_name
                continue
            if isinstance(statement, DBaseObjectPropertyStatement):
                self._analyze_database_property(statement, globals_work)
                continue
            if isinstance(statement, DBaseObjectMethodStatement):
                self._analyze_database_method(statement)
                continue
            if isinstance(statement, DBaseSessionLoginStatement):
                self._analyze_session_login(statement, globals_work)
                continue
            if isinstance(statement, (DBaseWithStatement, DBaseMenuFileStatement)):
                continue
            # Jeweils genau ein Basestatement analysieren. Bei IF ruft die
            # Stage-12-Logik rekursiv wieder self._analyze_top_sequence auf.
            _Stage12ProgramAnalyzer._analyze_top_sequence(self, (statement,), globals_work)
        return None

    def _preview_top_sequence(self, sequence, **kwargs):
        return super()._preview_top_sequence(self._without_menu(tuple(sequence)), **kwargs)


def _analyze_program(statements: Tuple[object, ...], *, filename: str) -> _DBaseAnalysis:
    return _DBaseProgramAnalyzer(statements, filename=filename).run()


class _DBaseCodeGenerator(_Stage12CodeGenerator):
    MENU_IMPORTS = (
        "DBaseQtMenuCreate",
        "DBaseQtMenuSetText",
        "DBaseQtMenuSetSeparator",
        "DBaseQtMenuSetShortcut",
        "DBaseQtMenuSetOnClick",
        "DBaseQtEnsureDefaultMenu",
        "DBaseQtSetColorNormal",
    )
    SESSION_IMPORTS = (
        "DBaseQtSessionCreate",
        "DBaseQtGetLoginSession",
        "DBaseQtSessionLogin",
    )
    DATABASE_IMPORTS = (
        "DBaseQtDatabaseCreate",
        "DBaseQtDatabaseSetPath",
        "DBaseQtDatabaseSetDatabaseName",
        "DBaseQtDatabaseSetUserName",
        "DBaseQtDatabaseSetPassword",
        "DBaseQtDatabaseSetAlias",
        "DBaseQtDatabaseSetSession",
        "DBaseQtDatabaseSetActive",
        "DBaseQtDatabaseOpen",
        "DBaseQtDatabaseClose",
        "DBaseQtDatabaseCommit",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object_slots: Dict[Tuple[str, ...], str] = {}

    def _object_slot(self, path: DBaseObjectPath) -> str:
        parts = path.canonical_parts
        if parts == ("_app",):
            return ""
        key = tuple(part.casefold() for part in parts)
        label = self.object_slots.get(key)
        if label is None:
            label = "__dbase_object_" + "_".join(_safe_member_name(part) for part in parts)
            self.object_slots[key] = label
        return label

    def _load_object_handle(self, path: DBaseObjectPath) -> None:
        slot = self._object_slot(path)
        if not slot:
            self.emit("    xor rax, rax" if self.is64 else "    xor eax, eax")
        elif self.is64:
            self.emit(f"    mov rax, qword ptr [{slot}]")
        else:
            self.emit(f"    mov eax, dword ptr [{slot}]")

    def _callback_label(self, callback_name: str) -> str:
        definition = self.analysis.routines.get(callback_name.casefold())
        if definition is None:
            raise AssertionError(callback_name)
        for instance in self.analysis.routine_instances:
            if instance.definition is definition and not instance.signature:
                return instance.label
        raise AssertionError(f"Callback-Instanz fehlt: {callback_name}")

    def emit_numeric_expression(self, expression: DBaseExpression) -> None:
        if isinstance(expression, DBaseIdentifierExpression):
            info = self.current_expression_info[expression]
            if info.variable_label == "__dbase_builtin_loginsession":
                if self.is64:
                    self.emit("    sub rsp, 40")
                    self.emit("    call DBaseQtGetLoginSession")
                    self.emit("    add rsp, 40")
                else:
                    self.emit("    call DBaseQtGetLoginSession")
                self.emit("    mov dword ptr [__dbase_temp_number], eax")
                self.emit("    fild dword ptr [__dbase_temp_number]")
                return
        return super().emit_numeric_expression(expression)

    def emit_store_expression_to_slot(self, expression: DBaseExpression, destination: str) -> None:
        if isinstance(expression, DBaseCallExpression) and expression.name.casefold() == "rgb":
            info = self.current_expression_info[expression]
            if info.constant_value is None:
                raise AssertionError("RGB muss in Stage 15 konstant sein")
            self.emit_static_text_to_slot(str(info.constant_value.value), "string", destination)
            return
        return super().emit_store_expression_to_slot(expression, destination)

    def emit_print_expression(self, expression: DBaseExpression, target: str) -> None:
        if isinstance(expression, DBaseCallExpression) and expression.name.casefold() == "rgb":
            info = self.current_expression_info[expression]
            if info.constant_value is None:
                raise AssertionError("RGB muss in Stage 15 konstant sein")
            label, length = self.text_literal(str(info.constant_value.value))
            self.emit_write_static(label, length, target)
            return
        return super().emit_print_expression(expression, target)

    def emit_app_color(self, statement: DBaseAppColorStatement) -> None:
        expression = statement.expression
        info = self.current_expression_info[expression]

        if info.constant_value is not None:
            value = str(info.constant_value.value)
            # Systemnamen werden kanonisch geschrieben; RGB liefert bereits
            # #RRGGBB.
            value = _DBASE_SYSTEM_COLOR_LOOKUP.get(value.casefold(), value)
            label, length = self.text_literal(value)
            if self.is64:
                self.emit(f"    mov rcx, {label}")
                self.emit(f"    mov edx, {length}")
                self.emit("    sub rsp, 40")
                self.emit("    call DBaseQtSetColorNormal")
                self.emit("    add rsp, 40")
            else:
                self.emit(f"    push {length}")
                self.emit(f"    push {label}")
                self.emit("    call DBaseQtSetColorNormal")
                self.emit("    add esp, 8")
            return

        # Dynamischer String aus Variable oder dBase-FUNCTION: zuerst in einen
        # Value-Slot materialisieren und Pointer/Laenge an die C-ABI uebergeben.
        slot = self.new_storage_slot("app_color")
        self.emit_store_expression_to_slot(expression, slot)
        if self.is64:
            self.emit(f"    mov rcx, qword ptr [{slot}_ptr]")
            self.emit(f"    mov edx, dword ptr [{slot}_len]")
            self.emit("    sub rsp, 40")
            self.emit("    call DBaseQtSetColorNormal")
            self.emit("    add rsp, 40")
        else:
            self.emit(f"    push dword ptr [{slot}_len]")
            self.emit(f"    push dword ptr [{slot}_ptr]")
            self.emit("    call DBaseQtSetColorNormal")
            self.emit("    add esp, 8")

    def emit_new_object(self, statement: DBaseNewObjectStatement) -> None:
        target_slot = self._object_slot(statement.target)
        self._load_object_handle(statement.owner)
        class_name = statement.class_name.upper()
        if class_name == "MENU":
            create_symbol = "DBaseQtMenuCreate"
        elif class_name == "SESSION":
            create_symbol = "DBaseQtSessionCreate"
        elif class_name == "DATABASE":
            create_symbol = "DBaseQtDatabaseCreate"
        else:
            raise DBaseCompilerError(
                f"Unbekannte eingebaute Klasse '{statement.class_name}'.",
                line=statement.line, column=statement.column, filename=self.filename,
            )
        if self.is64:
            self.emit("    mov rcx, rax")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {create_symbol}")
            self.emit("    add rsp, 40")
            self.emit(f"    mov qword ptr [{target_slot}], rax")
        else:
            self.emit("    push eax")
            self.emit(f"    call {create_symbol}")
            self.emit("    add esp, 4")
            self.emit(f"    mov dword ptr [{target_slot}], eax")

    def emit_session_login(self, statement: DBaseSessionLoginStatement) -> None:
        session_slot = self._object_slot(statement.target)
        user_slot = self.new_storage_slot("session_user")
        pass_slot = self.new_storage_slot("session_pass")
        group_slot = self.new_storage_slot("session_group")
        self.emit_store_expression_to_slot(statement.username, user_slot)
        self.emit_store_expression_to_slot(statement.password, pass_slot)
        self.emit_store_expression_to_slot(statement.group, group_slot)

        if self.is64:
            self.emit(f"    mov rcx, qword ptr [{session_slot}]")
            self.emit(f"    mov rdx, qword ptr [{user_slot}_ptr]")
            self.emit(f"    mov r8d, dword ptr [{user_slot}_len]")
            self.emit(f"    mov r9, qword ptr [{pass_slot}_ptr]")
            self.emit("    sub rsp, 56")
            self.emit(f"    mov eax, dword ptr [{pass_slot}_len]")
            self.emit("    mov qword ptr [rsp+32], rax")
            self.emit(f"    mov rax, qword ptr [{group_slot}_ptr]")
            self.emit("    mov qword ptr [rsp+40], rax")
            self.emit(f"    mov eax, dword ptr [{group_slot}_len]")
            self.emit("    mov qword ptr [rsp+48], rax")
            self.emit("    call DBaseQtSessionLogin")
            self.emit("    add rsp, 56")
        else:
            self.emit(f"    push dword ptr [{group_slot}_len]")
            self.emit(f"    push dword ptr [{group_slot}_ptr]")
            self.emit(f"    push dword ptr [{pass_slot}_len]")
            self.emit(f"    push dword ptr [{pass_slot}_ptr]")
            self.emit(f"    push dword ptr [{user_slot}_len]")
            self.emit(f"    push dword ptr [{user_slot}_ptr]")
            self.emit(f"    push dword ptr [{session_slot}]")
            self.emit("    call DBaseQtSessionLogin")
            self.emit("    add esp, 28")

        result_label = self.global_variable_labels.get(statement.result_name.casefold())
        if result_label is None:
            raise AssertionError(f"Kein Speicher fuer SESSION.Login-Ergebnis {statement.result_name}")
        self.emit(f"    mov dword ptr [{result_label}_num], eax")
        self.emit(f"    fild dword ptr [{result_label}_num]")
        self.emit(f"    fstp qword ptr [{result_label}_num]")
        self.emit(f"    mov dword ptr [{result_label}_type], {_TYPE_NUMBER}")

    def _emit_database_string_property(self, statement: DBaseObjectPropertyStatement, function: str) -> None:
        if statement.expression is None:
            raise AssertionError(statement.property_name)
        database_slot = self._object_slot(statement.target)
        value_slot = self.new_storage_slot("database_property")
        self.emit_store_expression_to_slot(statement.expression, value_slot)
        if self.is64:
            self.emit(f"    mov rcx, qword ptr [{database_slot}]")
            self.emit(f"    mov rdx, qword ptr [{value_slot}_ptr]")
            self.emit(f"    mov r8d, dword ptr [{value_slot}_len]")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {function}")
            self.emit("    add rsp, 40")
        else:
            self.emit(f"    push dword ptr [{value_slot}_len]")
            self.emit(f"    push dword ptr [{value_slot}_ptr]")
            self.emit(f"    push dword ptr [{database_slot}]")
            self.emit(f"    call {function}")
            self.emit("    add esp, 12")

    def emit_database_property(self, statement: DBaseObjectPropertyStatement) -> None:
        key = statement.property_name.casefold()
        string_calls = {
            "path": "DBaseQtDatabaseSetPath",
            "databasename": "DBaseQtDatabaseSetDatabaseName",
            "username": "DBaseQtDatabaseSetUserName",
            "password": "DBaseQtDatabaseSetPassword",
            "alias": "DBaseQtDatabaseSetAlias",
        }
        if key in string_calls:
            self._emit_database_string_property(statement, string_calls[key])
            return

        database_slot = self._object_slot(statement.target)
        if key == "session":
            if statement.object_value is None:
                raise AssertionError("DATABASE.session ohne Objekt")
            session_slot = self._object_slot(statement.object_value)
            if self.is64:
                self.emit(f"    mov rcx, qword ptr [{database_slot}]")
                self.emit(f"    mov rdx, qword ptr [{session_slot}]")
                self.emit("    sub rsp, 40")
                self.emit("    call DBaseQtDatabaseSetSession")
                self.emit("    add rsp, 40")
            else:
                self.emit(f"    push dword ptr [{session_slot}]")
                self.emit(f"    push dword ptr [{database_slot}]")
                self.emit("    call DBaseQtDatabaseSetSession")
                self.emit("    add esp, 8")
            return

        if key == "active":
            if statement.expression is None:
                raise AssertionError("DATABASE.active ohne Ausdruck")
            info = self.current_expression_info[statement.expression]
            if info.constant_value is not None:
                value = 1 if Decimal(info.constant_value.value) != 0 else 0
                if self.is64:
                    self.emit(f"    mov rcx, qword ptr [{database_slot}]")
                    self.emit(f"    mov edx, {value}")
                    self.emit("    sub rsp, 40")
                    self.emit("    call DBaseQtDatabaseSetActive")
                    self.emit("    add rsp, 40")
                else:
                    self.emit(f"    push {value}")
                    self.emit(f"    push dword ptr [{database_slot}]")
                    self.emit("    call DBaseQtDatabaseSetActive")
                    self.emit("    add esp, 8")
            else:
                self.emit_numeric_expression(statement.expression)
                self.emit("    fistp dword ptr [__dbase_temp_number]")
                if self.is64:
                    self.emit(f"    mov rcx, qword ptr [{database_slot}]")
                    self.emit("    mov edx, dword ptr [__dbase_temp_number]")
                    self.emit("    sub rsp, 40")
                    self.emit("    call DBaseQtDatabaseSetActive")
                    self.emit("    add rsp, 40")
                else:
                    self.emit("    push dword ptr [__dbase_temp_number]")
                    self.emit(f"    push dword ptr [{database_slot}]")
                    self.emit("    call DBaseQtDatabaseSetActive")
                    self.emit("    add esp, 8")
            return
        raise AssertionError(statement.property_name)

    def emit_database_method(self, statement: DBaseObjectMethodStatement) -> None:
        database_slot = self._object_slot(statement.target)
        function = {
            "open": "DBaseQtDatabaseOpen",
            "close": "DBaseQtDatabaseClose",
            "commit": "DBaseQtDatabaseCommit",
        }[statement.method_name.casefold()]
        if self.is64:
            self.emit(f"    mov rcx, qword ptr [{database_slot}]")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {function}")
            self.emit("    add rsp, 40")
        else:
            self.emit(f"    push dword ptr [{database_slot}]")
            self.emit(f"    call {function}")
            self.emit("    add esp, 4")

    def _emit_menu_string(self, function: str, slot: str, value: str) -> None:
        label, length = self.text_literal(value)
        if self.is64:
            self.emit(f"    mov rcx, qword ptr [{slot}]")
            self.emit(f"    mov rdx, {label}")
            self.emit(f"    mov r8d, {length}")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {function}")
            self.emit("    add rsp, 40")
        else:
            self.emit(f"    push {length}")
            self.emit(f"    push {label}")
            self.emit(f"    push dword ptr [{slot}]")
            self.emit(f"    call {function}")
            self.emit("    add esp, 12")

    def emit_with_statement(self, statement: DBaseWithStatement) -> None:
        slot = self._object_slot(statement.target)
        for prop in statement.properties:
            key = prop.name.casefold()
            if key == "text":
                self._emit_menu_string("DBaseQtMenuSetText", slot, str(prop.value))
            elif key == "shortcut":
                self._emit_menu_string("DBaseQtMenuSetShortcut", slot, str(prop.value))
            elif key == "separator":
                value = 1 if prop.value else 0
                if self.is64:
                    self.emit(f"    mov rcx, qword ptr [{slot}]")
                    self.emit(f"    mov edx, {value}")
                    self.emit("    sub rsp, 40")
                    self.emit("    call DBaseQtMenuSetSeparator")
                    self.emit("    add rsp, 40")
                else:
                    self.emit(f"    push {value}")
                    self.emit(f"    push dword ptr [{slot}]")
                    self.emit("    call DBaseQtMenuSetSeparator")
                    self.emit("    add esp, 8")
            elif key == "onclick":
                callback = "0"
                if prop.value_kind == "callback":
                    callback = self._callback_label(str(prop.value))
                # Ein {...}-Codeblock ist in dieser ersten Klassenstufe ein
                # valider Callback-Platzhalter. Ein leerer/Kommentarblock wird
                # deshalb als NULL registriert und fuehrt sicher keine Aktion aus.
                if self.is64:
                    self.emit(f"    mov rcx, qword ptr [{slot}]")
                    self.emit(f"    mov rdx, {callback}")
                    self.emit("    sub rsp, 40")
                    self.emit("    call DBaseQtMenuSetOnClick")
                    self.emit("    add rsp, 40")
                else:
                    self.emit(f"    push {callback}")
                    self.emit(f"    push dword ptr [{slot}]")
                    self.emit("    call DBaseQtMenuSetOnClick")
                    self.emit("    add esp, 8")
            else:
                raise AssertionError(key)

    def _emit_statement_sequence(self, sequence, **kwargs):
        format_target = kwargs.get("format_target", "console")
        debug_override = kwargs.get("debug_override", None)
        debug_visible = kwargs.get("debug_visible", False)
        routine_end_label = kwargs.get("routine_end_label", "")
        routine_result_label = kwargs.get("routine_result_label", "")
        chunk: list[object] = []

        def flush():
            nonlocal format_target, debug_override, debug_visible, chunk
            if not chunk:
                return
            format_target, debug_override, debug_visible = super(_DBaseCodeGenerator, self)._emit_statement_sequence(
                tuple(chunk),
                routine_end_label=routine_end_label,
                routine_result_label=routine_result_label,
                format_target=format_target,
                debug_override=debug_override,
                debug_visible=debug_visible,
            )
            chunk = []

        for statement in sequence:
            if isinstance(statement, DBaseLocalObjectDeclaration):
                flush()
                self.emit_shutdown_guard(routine_end_label)
            elif isinstance(statement, DBaseObjectPropertyStatement):
                flush()
                self.emit_database_property(statement)
                self.emit_shutdown_guard(routine_end_label)
            elif isinstance(statement, DBaseObjectMethodStatement):
                flush()
                self.emit_database_method(statement)
                self.emit_shutdown_guard(routine_end_label)
            elif isinstance(statement, DBaseAppColorStatement):
                flush()
                self.emit_app_color(statement)
                self.emit_shutdown_guard(routine_end_label)
            elif isinstance(statement, DBaseNewObjectStatement):
                flush()
                self.emit_new_object(statement)
                self.emit_shutdown_guard(routine_end_label)
            elif isinstance(statement, DBaseSessionLoginStatement):
                flush()
                self.emit_session_login(statement)
                self.emit_shutdown_guard(routine_end_label)
            elif isinstance(statement, DBaseWithStatement):
                flush()
                self.emit_with_statement(statement)
                self.emit_shutdown_guard(routine_end_label)
            elif isinstance(statement, DBaseMenuFileStatement):
                flush()
                self.emit_shutdown_guard(routine_end_label)
            else:
                chunk.append(statement)
        flush()
        return format_target, debug_override, debug_visible

    def build(self) -> str:
        assembly = super().build()
        marker = 'import DBaseQtShutdown, "d64qt5.dll", "DBaseQtShutdown"\n'
        extra = "".join(
            f'import {symbol}, "d64qt5.dll", "{symbol}"\n'
            for symbol in self.MENU_IMPORTS + self.SESSION_IMPORTS + self.DATABASE_IMPORTS
        )
        if marker in assembly and extra not in assembly:
            assembly = assembly.replace(marker, marker + extra, 1)

        menu_file_statements = [
            statement for statement in self.statements
            if isinstance(statement, DBaseMenuFileStatement)
        ]
        has_menu_file = bool(menu_file_statements and menu_file_statements[-1].configured)
        if not has_menu_file:
            show_marker = "    call DBaseQtShowWindow\n"
            default_call = "    call DBaseQtEnsureDefaultMenu\n"
            if show_marker in assembly and default_call not in assembly:
                assembly = assembly.replace(show_marker, default_call + show_marker, 1)

        if self.object_slots:
            object_data = []
            for label in dict.fromkeys(self.object_slots.values()):
                object_data.append(f"{label}:")
                object_data.append("    dd 0, 0" if self.is64 else "    dd 0")
            assembly = assembly.rstrip() + "\n" + "\n".join(object_data) + "\n"
        return assembly


# Öffentliche Exportliste der additiven Stage-13-Klassen.
for _name in (
    "DBaseObjectPath", "DBaseNewObjectStatement", "DBaseSessionLoginStatement",
    "DBaseLocalObjectDeclaration", "DBaseObjectPropertyStatement", "DBaseObjectMethodStatement", "DBaseMenuFileStatement",
    "DBaseAppColorStatement", "DBASE_SYSTEM_COLOR_NAMES",
    "DBaseSetColorStatement", "DBaseClearScreenStatement", "DBaseSetBorderColorStatement",
    "DBASE_FOREGROUND_COLOR_CODES", "DBASE_BACKGROUND_COLOR_CODES",
    "DBaseMenuProperty", "DBaseWithStatement",
):
    if _name not in __all__:
        __all__.append(_name)

# Stage 13: die semantische Test-Auswertung ignoriert reine GUI-Objektaufbauten.
_stage12_evaluate_dbase_statements = evaluate_dbase_statements

def evaluate_dbase_statements(
    statements: Tuple[object, ...],
    *,
    filename: str = "<dBase>",
) -> str:
    filtered = tuple(
        statement for statement in statements
        if not isinstance(statement, (DBaseLocalObjectDeclaration, DBaseNewObjectStatement, DBaseSessionLoginStatement, DBaseObjectPropertyStatement, DBaseObjectMethodStatement, DBaseWithStatement, DBaseMenuFileStatement, DBaseAppColorStatement))
    )
    return _stage12_evaluate_dbase_statements(filtered, filename=filename)

_stage12_compile_dbase_to_assembly = compile_dbase_to_assembly

def compile_dbase_to_assembly(
    source: str,
    *,
    filename: str = "<dBase>",
    target: str = "pe32",
    windows_application_mode: str = "Console",
) -> DBaseCompileResult:
    result = _stage12_compile_dbase_to_assembly(
        source,
        filename=filename,
        target=target,
        windows_application_mode=windows_application_mode,
    )
    stage13_notes = (
        "dBase-Ausbaustufe 13: globales APPLICATION-Objekt _app und eingebaute MENU-Klasse.",
        "this ist auf Top-Level ein Alias fuer _app; Memberpfade werden als native Objekt-Handles gespeichert.",
        "WITH/ENDWITH setzt MENU-Properties text, onClick, shortCut und separator.",
        "class::MEMBER bindet eine parameterlose PROCEDURE als nativen Qt-onClick-Callback.",
        '_app.menuFile = "menu.mnu" bindet eine externe Menuequelldatei relativ zur dBase-Quelldatei ein; Makros sowie zur Compile-Zeit bestimmbare Variablen/Funktionen sind erlaubt.',
        "Das Qt-Hauptmenue liegt als QMenuBar in der ersten Zeile des Konsolen-Tabs.",
        "_app.colorNormal akzeptiert direkte Windows-Systemfarben nur als Stringliteral; Variablen/Funktionen und RGB(rr,gg,bb) sind ebenfalls moeglich.",
        "dBase-Ausbaustufe 16: CLEAR SCREEN leert die Konsole mit der aktuellen SET-COLOR-Hintergrundfarbe, ohne den Editorrahmen zu entfernen.",
        "SET BORDERCOLOR TO <expr> setzt die Rahmenfarbe der Konsolen-Textkomponente per Windows-Systemfarbe oder RGB(rr,gg,bb).",
        "dBase-Ausbaustufe 21: SESSION ist ein nativer Benutzer-/Sicherheitskontext; SESSION.Login(user,password,group) authentifiziert gegen Windows und liefert 0/1.",
        "dBase-Ausbaustufe 22: __dbase_format_buffer ist nur noch ein Pointer-Slot; 96 Bytes werden per VirtualAlloc reserviert und per VirtualFree freigegeben.",
        "dBase-Ausbaustufe 23: CLEAR SCREEN <expr> fuellt bei 0..255 die 80x25-Konsole mit einem CP437-Terminalzeichen; '#RRGGBB'/RGB(...) setzt beim Loeschen die Hintergrundfarbe.",
        "dBase-Ausbaustufe 24: Konsolen-Scrollbars und reservierte Leerzeile entfallen; menuFile verwendet String-Ausdruecke und bei leerem menuFile wird ein Standard-Dateimenue erzeugt.",
        "dBase-Ausbaustufe 25: new SESSION() oeffnet den rastergebundenen Windows-Login-Dialog; LOGINSESSION liefert den globalen 0/1-Status und bis zum Login bleiben nur Login/Beenden aktiv.",
        "dBase-Ausbaustufe 30: DATABASE-Objekte mit LOCAL ... AS DATABASE, Session-Bindung, Pfad/Name/Anmeldedaten/Alias sowie OPEN/CLOSE/COMMIT und ACTIVE-Lifecycle.",
        "dBase-Ausbaustufe 29: Schliessen des Hauptfensters beendet alle Dialog-Eventloops und fuehrt den generierten Code ueber einen gemeinsamen Shutdown-/VirtualFree-Cleanup-Pfad.",
    )
    return DBaseCompileResult(
        assembly=result.assembly,
        target=result.target,
        windows_application_mode=result.windows_application_mode,
        source_kind=result.source_kind,
        notes=stage13_notes + tuple(result.notes),
        warnings=result.warnings,
        linked_assembly_files=result.linked_assembly_files,
        linked_pe32_modules=result.linked_pe32_modules,
        linked_object_files=result.linked_object_files,
        frontend=result.frontend,
        statements=result.statements,
        transcript=result.transcript,
        debug_transcript=result.debug_transcript,
        uses_debug_output=result.uses_debug_output,
        variables=result.variables,
        external_functions=result.external_functions,
    )
