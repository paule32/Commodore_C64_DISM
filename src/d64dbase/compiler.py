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

        if first.kind == "IDENT" and str(first.value).casefold() == "set":
            self.index += 1
            command = self.current
            if command.kind != "IDENT":
                raise DBaseCompilerError(
                    "Nach SET wird FORMAT oder DEBUG erwartet.",
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
            raise DBaseCompilerError(
                "Nach SET wird FORMAT oder DEBUG erwartet.",
                line=command.line,
                column=command.column,
                filename=self.filename,
            )

        raise DBaseCompilerError(
            "Erwartet wird '?' oder '??', eine Variablenzuweisung, ein Member-Aufruf, "
            "RETURN, SET FORMAT TO ... oder SET DEBUG ON/OFF.",
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


def _routine_end_kind(keyword: str) -> str:
    key = str(keyword).casefold()
    if key in {"endproc", "endprocedure"}:
        return "procedure"
    if key in {"endfunc", "endfunction"}:
        return "function"
    return ""


def parse_dbase_statements(
    source: str,
    *,
    filename: str = "<dBase>",
    target: str = "pe32",
) -> Tuple[object, ...]:
    """Parst das dBase-Programm inklusive PROCEDURE/FUNCTION-Membern.

    Routinen stehen auf Top-Level. Eine PROCEDURE kann durch ein nacktes
    ``RETURN`` beendet werden; alternativ werden ENDPROC/ENDPROCEDURE
    akzeptiert. Eine FUNCTION wird durch ``RETURN <expr>`` beendet und darf
    optional noch ENDFUNC/ENDFUNCTION folgen. Parameterlisten sind nicht
    kuenstlich begrenzt.
    """
    frontend = preprocess_dbase_source(source, filename=filename, target=target)
    parse_source = frontend.preprocessed_source or frontend.source
    parse_comments = scan_dbase_comments(parse_source, filename=filename)
    cleaned = strip_dbase_comments(parse_source, filename=filename)
    statements: list[object] = []

    current_kind = ""
    current_name = ""
    current_parameters: Tuple[str, ...] = ()
    current_body: list[object] = []
    current_line = 0
    current_column = 0
    current_has_return = False
    just_closed_kind = ""

    def close_current(*, implicit: bool = False) -> None:
        nonlocal current_kind, current_name, current_parameters, current_body
        nonlocal current_line, current_column, current_has_return, just_closed_kind
        if not current_kind:
            return
        if current_kind == "function" and not current_has_return:
            raise DBaseCompilerError(
                f"FUNCTION '{current_name}' benoetigt RETURN <expr>.",
                line=current_line,
                column=current_column,
                filename=filename,
            )
        statements.append(
            DBaseRoutineDefinition(
                kind=current_kind,
                name=current_name,
                parameters=current_parameters,
                body=tuple(current_body),
                line=current_line,
                column=current_column,
            )
        )
        just_closed_kind = current_kind
        current_kind = ""
        current_name = ""
        current_parameters = ()
        current_body = []
        current_line = 0
        current_column = 0
        current_has_return = False

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

        if keyword in {"procedure", "function"}:
            if current_kind:
                # Eine PROCEDURE darf vor dem naechsten Member implizit enden.
                # Eine FUNCTION braucht dagegen immer einen Rueckgabewert.
                close_current(implicit=True)
            kind, name, parameters, line, column = _parse_dbase_routine_header(
                tokens,
                filename=filename,
            )
            current_kind = kind
            current_name = name
            current_parameters = parameters
            current_body = []
            current_line = line
            current_column = column
            current_has_return = False
            just_closed_kind = ""
            continue

        end_kind = _routine_end_kind(keyword)
        if end_kind:
            if current_kind:
                if current_kind != end_kind:
                    raise DBaseCompilerError(
                        f"{first.text.upper()} passt nicht zu {current_kind.upper()} '{current_name}'.",
                        line=first.line,
                        column=first.column,
                        filename=filename,
                    )
                close_current()
                continue
            if just_closed_kind == end_kind:
                # Optionales END... direkt nach dem RETURN akzeptieren.
                just_closed_kind = ""
                continue
            raise DBaseCompilerError(
                f"Unerwartetes {first.text.upper()} ohne offene Routine.",
                line=first.line,
                column=first.column,
                filename=filename,
            )

        parser = _DBaseExpressionParser(tokens, filename=filename)
        statement = parser.parse_statement()

        if current_kind:
            if isinstance(statement, DBaseReturnStatement):
                if current_kind == "procedure" and statement.expression is not None:
                    raise DBaseCompilerError(
                        f"PROCEDURE '{current_name}' darf mit RETURN keinen Wert zurueckgeben.",
                        line=statement.line,
                        column=statement.column,
                        filename=filename,
                    )
                if current_kind == "function" and statement.expression is None:
                    raise DBaseCompilerError(
                        f"FUNCTION '{current_name}' erwartet RETURN <expr>.",
                        line=statement.line,
                        column=statement.column,
                        filename=filename,
                    )
                current_body.append(statement)
                current_has_return = True
                close_current()
            else:
                current_body.append(statement)
            continue

        if isinstance(statement, DBaseReturnStatement):
            raise DBaseCompilerError(
                "RETURN ist nur innerhalb einer PROCEDURE oder FUNCTION erlaubt.",
                line=statement.line,
                column=statement.column,
                filename=filename,
            )
        statements.append(statement)
        just_closed_kind = ""

    if current_kind:
        close_current(implicit=True)

    # Doppelte Membernamen werden unabhaengig von Gross-/Kleinschreibung abgelehnt.
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
    ) -> None:
        symbols = self._merged_symbols(self.global_symbols, local_symbols)
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
            old_global = self.global_symbols.get(key)
            label = old_global.label if old_global is not None else _symbol_label(statement.name)
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
            self.global_symbols[key] = state
        else:
            local_symbols[key] = state
            instance.local_symbols[key] = state

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
        return_seen = False
        for statement in definition.body:
            if isinstance(statement, DBaseAssignmentStatement):
                self._analyze_assignment(
                    statement,
                    local_symbols=locals_,
                    expression_info=instance.expression_info,
                    call_bindings=instance.call_bindings,
                    instance=instance,
                )
                continue
            if isinstance(statement, DBasePrintStatement):
                symbols = self._merged_symbols(self.global_symbols, locals_)
                self.analyze_expression(
                    statement.expression,
                    symbols=symbols,
                    expression_info=instance.expression_info,
                    call_bindings=instance.call_bindings,
                )
                continue
            if isinstance(statement, DBaseCallStatement):
                symbols = self._merged_symbols(self.global_symbols, locals_)
                self.analyze_expression(
                    statement.call,
                    symbols=symbols,
                    expression_info=instance.expression_info,
                    call_bindings=instance.call_bindings,
                    require_value=False,
                )
                continue
            if isinstance(statement, DBaseReturnStatement):
                return_seen = True
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
                symbols = self._merged_symbols(self.global_symbols, locals_)
                instance.return_info = self.analyze_expression(
                    statement.expression,
                    symbols=symbols,
                    expression_info=instance.expression_info,
                    call_bindings=instance.call_bindings,
                )
                continue
            if isinstance(statement, (DBaseSetFormatStatement, DBaseSetDebugStatement)):
                continue
            raise AssertionError(type(statement))

        if definition.is_function and (not return_seen or instance.return_info is None):
            raise DBaseCompilerError(
                f"FUNCTION '{definition.name}' benoetigt RETURN <expr>.",
                line=definition.line,
                column=definition.column,
                filename=self.filename,
            )
        instance.local_symbols = locals_
        instance.analyzing = False
        self.storage_slots.extend(instance.storage_slots)
        return instance

    def run(self) -> _DBaseAnalysis:
        console_chunks: list[str] = []
        debug_chunks: list[str] = []
        format_target = "console"
        debug_override: Optional[bool] = None
        transcript_complete = True
        uses_debug_output = False

        for statement in self.statements:
            if isinstance(statement, DBaseRoutineDefinition):
                continue
            if isinstance(statement, DBaseAssignmentStatement):
                self._analyze_assignment(
                    statement,
                    local_symbols={},
                    expression_info=self.expression_info,
                    call_bindings=self.call_bindings,
                    instance=None,
                )
                continue
            if isinstance(statement, DBaseSetFormatStatement):
                format_target = statement.target
                continue
            if isinstance(statement, DBaseSetDebugStatement):
                debug_override = bool(statement.enabled)
                continue
            if isinstance(statement, DBaseCallStatement):
                self.analyze_expression(
                    statement.call,
                    symbols=self.global_symbols,
                    expression_info=self.expression_info,
                    call_bindings=self.call_bindings,
                    require_value=False,
                )
                transcript_complete = False
                continue
            if isinstance(statement, DBasePrintStatement):
                self.analyze_expression(
                    statement.expression,
                    symbols=self.global_symbols,
                    expression_info=self.expression_info,
                    call_bindings=self.call_bindings,
                )
                output_target = _effective_output_target(format_target, debug_override)
                if output_target == "debug":
                    uses_debug_output = True
                rendered = _preview_expression(statement.expression, self.expression_info)
                if rendered is None:
                    transcript_complete = False
                    continue
                chunks = debug_chunks if output_target == "debug" else console_chunks
                chunks.append(rendered)
                if statement.newline:
                    chunks.append("\r\n")
                continue
            if isinstance(statement, DBaseReturnStatement):
                raise DBaseCompilerError(
                    "RETURN ist auf Top-Level nicht erlaubt.",
                    line=statement.line,
                    column=statement.column,
                    filename=self.filename,
                )
            raise AssertionError(type(statement))

        variables = tuple(
            DBaseVariableInfo(
                name=symbol.name,
                label=symbol.label,
                value_type=symbol.value_type,
                constant_value=symbol.constant_value,
                dynamic=symbol.dynamic,
                last_line=symbol.last_line,
                last_column=symbol.last_column,
            )
            for symbol in self.global_symbols.values()
        )
        return _DBaseAnalysis(
            expression_info=dict(self.expression_info),
            call_bindings=dict(self.call_bindings),
            variables=variables,
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
            if isinstance(statement, DBaseReturnStatement):
                value = None if statement.expression is None else self._eval_expr(statement.expression, scope)
                raise _DBaseReturnSignal(value)
            if isinstance(statement, (DBaseSetFormatStatement, DBaseSetDebugStatement)):
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
            self.emit("    mov r8, __dbase_format_buffer")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_gcvt")
            self.emit("    add rsp, 40")
        else:
            self.emit("    push __dbase_format_buffer")
            self.emit("    push 15")
            self.emit("    push dword ptr [__dbase_temp_number_hi]")
            self.emit("    push dword ptr [__dbase_temp_number]")
            self.emit("    call __dbase_gcvt")
            self.emit("    add esp, 16")

        length_loop = self.new_label("strlen_loop")
        length_done = self.new_label("strlen_done")
        if self.is64:
            self.emit("    mov rcx, __dbase_format_buffer")
        else:
            self.emit("    mov ecx, __dbase_format_buffer")
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
            self.emit("    mov rcx, __dbase_format_buffer")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {function}")
            self.emit("    add rsp, 40")
        else:
            self.emit("    push edx")
            self.emit("    push __dbase_format_buffer")
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
            self.emit(f"    mov rdx, {buffer_label}")
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
            self.emit(f"    push {buffer_label}")
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

    def _emit_statement_sequence(
        self,
        sequence: Tuple[object, ...],
        *,
        routine_end_label: str = "",
        routine_result_label: str = "",
    ) -> None:
        format_target = "console"
        debug_override: Optional[bool] = None
        debug_visible = False
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
            elif isinstance(statement, DBaseCallStatement):
                self.emit_call_statement(statement)
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
            "DBaseQtMarkProgramFinished",
            "DBaseQtExec",
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
        self.emit('import ExitProcess, "kernel32.dll", "ExitProcess"')
        for function in self.analysis.external_functions:
            self.emit(f"extern {function}")
        self.emit("global _start")
        self.emit("entry _start")
        self.emit()
        self.emit("section .text")
        self.emit()
        self.emit("_start:")

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
        self.emit_qt_call0("DBaseQtShowWindow")
        self.emit_qt_call0("DBaseQtProcessEvents")
        self.emit_qt_call1_int("DBaseQtSetDebugVisible", 0)

        self._emit_statement_sequence(self.statements)

        self.emit_qt_call0("DBaseQtMarkProgramFinished")
        self.emit_qt_call0("DBaseQtExec")
        self.emit("    mov dword ptr [__dbase_exit_code], eax")
        self.emit_qt_call0("DBaseQtShutdown")
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
            "    db " + ", ".join("0" for _ in range(96)),
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
    """Kompiliert dBase mit Qt5-GUI, Variablen und PROCEDURE/FUNCTION-Membern.

    Implementiert:
    - //, **, && und /* ... */ Kommentare
    - ? <expr> und ?? <expr>
    - Variablenzuweisung ``Name = Ausdruck``
    - Zahl-, Hex-, Char- und Stringliterale
    - arithmetische + - * / Ausdruecke und String-Konkatenation
    - PROCEDURE/FUNCTION mit beliebig vielen Parametern und nativen Member-Aufrufen
    - RETURN ohne Wert fuer PROCEDURE; RETURN <expr> fuer FUNCTION
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
            f"dBase-Ausbaustufe 9: Praeprozessor/Startlogik fuer {target_label}.",
            "#define unterstuetzt Objekt- und Funktionsmakros; ## verkettet Tokens.",
            "#if/#ifdef/#ifndef sind verschachtelbar und scoped; ausschliesslich #else ist gueltig.",
            "#if 0 ... #endif kann beliebig grosse dBase-Codebereiche vom Compile ausschliessen.",
            "#error bricht den Compiler ab; #warning und #info erscheinen in den Diagnosen.",
            "Vordefiniert: __FILE__, __LINE__, __DATE__ und __TIME__.",
            "#pragma link bindet .o/.obj/.a/.lib beim finalen PE-Linkschritt ein.",
            "Variablen koennen Zahl/Hex, Char und String aufnehmen; Zuweisungen erzeugen echte Speicher-Slots.",
            "PROCEDURE darf nur RETURN ohne Wert verwenden; FUNCTION verwendet RETURN <expr>.",
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
    "DBaseReturnStatement",
    "DBaseCallStatement",
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
