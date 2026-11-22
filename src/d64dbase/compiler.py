from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_DOWN, localcontext
from datetime import datetime, date
from pathlib import Path
import ast
import os
import re
import struct
from typing import Dict, Mapping, Optional, Tuple, Union
from .procedure_files import DBaseProcedureFileManager


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
class DBaseSourceLocation:
    """Physical origin for one expanded line; never emits target instructions."""
    filename: str
    line: int
    # Filename + #include line of the parents, outermost first.
    include_chain: Tuple[Tuple[str, int], ...] = ()


class DBaseIncludeLineManager:
    """Python-only LIFO source manager for nested #include files."""
    def __init__(self, filename: str):
        self.stack: list[Tuple[str, int]] = [(str(filename), 0)]
        self.locations: list[DBaseSourceLocation] = []

    def push(self, filename: str, at_line: int):
        self.stack[-1] = (self.stack[-1][0], int(at_line))
        self.stack.append((str(filename), 0))

    def pop(self):
        if len(self.stack) <= 1:
            raise IndexError('Kein Include-Kontext vorhanden')
        self.stack.pop()

    def mark(self, line: int):
        self.locations.append(DBaseSourceLocation(
            self.stack[-1][0], int(line), tuple(self.stack[:-1])))


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
    ffi_prototypes: Tuple[object, ...] = ()
    source_locations: Tuple[DBaseSourceLocation, ...] = ()


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
class DBaseSetSpeechStatement:
    option: str
    value: Union[int, str]
    line: int
    column: int


@dataclass(frozen=True)
class DBaseSayStatement:
    expression: DBaseExpression
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
class DBaseSetBackgroundStatement:
    """SET BACKGROUND TO char / background, foreground, char (DOS 0..15/255)."""
    arguments: Tuple[DBaseExpression, ...]
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
class DBaseCondition(DBaseExpression):
    left: DBaseExpression
    operator: str
    right: DBaseExpression
    line: int
    column: int


@dataclass(frozen=True)
class DBaseIfBranch:
    condition: Optional[DBaseExpression]
    body: Tuple[object, ...]
    line: int
    column: int


@dataclass(frozen=True)
class DBaseIfStatement:
    branches: Tuple[DBaseIfBranch, ...]
    line: int
    column: int


@dataclass(frozen=True)
class DBaseCatchClause:
    """A typed, lexically scoped dBL exception handler."""
    class_name: str
    variable: str
    body: Tuple[object, ...]
    line: int
    column: int


@dataclass(frozen=True)
class DBaseThrowStatement:
    """THROW NEW Exception(text), THROW e, or THROW text."""
    class_name: str
    message: Optional[DBaseExpression]
    variable: str
    line: int
    column: int


@dataclass(frozen=True)
class DBaseTryStatement:
    """TRY / typed CATCH / optional FINALLY / ENDTRY."""
    try_body: Tuple[object, ...]
    catches: Tuple[DBaseCatchClause, ...]
    finally_body: Tuple[object, ...]
    line: int
    column: int


# Win32 errors are Win32 API status codes, NOT native SEH exception codes.
_WIN32_RAISE_BUILTINS = {"win32raise": "win32exception",
                         "win32fileraise": "win32fileexception"}


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
class DBaseClassDefinition:
    """Deklaration einer dBASE-Klasse mit optionalen nativen Methoden."""
    name: str
    parent: str
    custom: bool
    line: int
    column: int
    methods: Tuple[object, ...] = ()
    properties: Tuple[object, ...] = ()


@dataclass(frozen=True)
class DBaseNativeClassCallStatement:
    """Invoke a user CLASS method on a native JObject/JitVmt instance."""
    target: object
    declaring_class: str
    method_name: str
    argument: Optional[DBaseExpression]
    line: int
    column: int


@dataclass(frozen=True)
class DBaseNativeMethodStatement:
    """Single native VMT call: obj.Method(), STORE, assignment or ? output."""
    target: object
    method_name: str
    argument_name: str
    result_name: str
    print_result: bool
    line: int
    column: int


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


def _is_dbase_variadic_parameter_marker(text: str, index: int) -> bool:
    """True for the special first routine parameter marker ``**name``.

    dBase traditionally accepts ``**`` as a line-comment marker.  Stage 107
    additionally uses ``**name`` immediately after the opening parenthesis of
    PROCEDURE/FUNCTION as an explicit variadic-argument marker.  Only this
    syntactic position is exempt from comment scanning; ordinary ``**``
    comments keep their historic behaviour.
    """
    source = str(text or "")
    pos = int(index)
    if pos < 0 or not source.startswith("**", pos):
        return False
    after = pos + 2
    if after >= len(source) or not (source[after].isalpha() or source[after] == "_"):
        return False

    line_start = max(source.rfind("\n", 0, pos), source.rfind("\r", 0, pos)) + 1
    prefix = source[line_start:pos]
    return bool(re.search(
        r"(?i)\b(?:procedure|function)\s+[A-Za-z_]\w*\s*\(\s*$",
        prefix,
    ))


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
                and not (
                    candidate == "**"
                    and _is_dbase_variadic_parameter_marker(text, index)
                )
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


_DBASE_PREDEFINED_MACRO_NAMES = frozenset({
    "__file__", "__line__", "__date__", "__time__",
})


def _is_dbase_macro_defined(name: str, macros: Mapping[str, DBaseMacro]) -> bool:
    key = str(name or "").casefold()
    return key in macros or key in _DBASE_PREDEFINED_MACRO_NAMES


def _condition_to_python(
    expression: str,
    macros: Mapping[str, DBaseMacro],
    *,
    filename: str,
    line: int,
    compile_date: str,
    compile_time: str,
) -> str:
    """Uebersetzt einen C/C++-artigen Praeprozessor-Ausdruck nach Python.

    ``defined(NAME)`` und ``defined NAME`` liefern strikt 1/0. Danach werden
    Objekt- und Funktionsmakros expandiert. Noch unbekannte Bezeichner haben
    wie beim C-Praeprozessor den Wert 0.
    """
    text = re.sub(r"(?<![\w])#(?=__(?:FILE|LINE|DATE|TIME)__\b)", "", str(expression or ""), flags=re.I)

    def replace_defined(match: re.Match[str]) -> str:
        name = match.group(1) or match.group(2) or ""
        return "1" if _is_dbase_macro_defined(name, macros) else "0"

    text = re.sub(
        r"\bdefined\s*(?:\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)|([A-Za-z_][A-Za-z0-9_]*))",
        replace_defined,
        text,
        flags=re.IGNORECASE,
    )

    # Makros in Bedingungen genauso wie im normalen Quelltext expandieren.
    text, _ = _expand_dbase_macro_text(
        text,
        macros,
        filename=filename,
        line=line,
        compile_date=compile_date,
        compile_time=compile_time,
    )

    # Normalize operators and numeric literals outside quoted strings only.
    # Otherwise a #if "a=b" == "a==b" could compare equal by accident.
    segments = re.split(r'(\"(?:\"\"|[^\"])*\"|\'(?:\'\'|[^\'])*\')', text)
    for segment_index in range(0, len(segments), 2):
        chunk = segments[segment_index]
        chunk = re.sub(
            r"(?<![A-Za-z0-9_])\$([0-9A-Fa-f]+)",
            lambda m: str(int(m.group(1), 16)), chunk,
        )
        chunk = re.sub(
            r"(?<![A-Za-z0-9_])([0-9][0-9A-Fa-f]*)[hH]\b",
            lambda m: str(int(m.group(1), 16)), chunk,
        )
        chunk = chunk.replace("=>", ">=").replace("<>", "!=")
        chunk = re.sub(r"(?<![<>=!])=(?!=)", "==", chunk)
        chunk = chunk.replace("&&", " and ").replace("||", " or ")
        chunk = re.sub(r"!(?!=)", " not ", chunk)
        segments[segment_index] = chunk
    text = "".join(segments)

    # Identifikatoren ausserhalb von Strings: Python-Schluesselwoerter bzw.
    # boolesche Literale behalten, alles andere wird zu 0.
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

        # Kein Identifier-Match mitten in einer Zahl wie 0x10.
        if i > 0 and (text[i - 1].isalnum() or text[i - 1] == "_"):
            result.append(ch)
            i += 1
            continue

        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", text[i:])
        if m:
            word = m.group(0)
            low = word.casefold()
            if low in {"and", "or", "not"}:
                result.append(low)
            elif low == "true":
                result.append("True")
            elif low == "false":
                result.append("False")
            else:
                # Nach Makroexpansion noch unbekannte Namen entsprechen 0.
                result.append("0")
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
        # More useful than an opaque syntax error for mistyped comparison ops.
        unquoted = re.sub(r'(\"(?:\"\"|[^\"])*\"|\'(?:\'\'|[^\'])*\')', ' ', expression)
        unsupported = re.search(r"===|!==|><|=<|=~|~=|<=>", unquoted)
        if unsupported:
            raise DBaseCompilerError(
                f"Nicht unterstuetzter Vergleichsoperator '{unsupported.group(0)}'. "
                "Erlaubt sind <, <=, ==, !=, >=, => und >.",
                line=line, column=(unsupported.start() + 1), filename=filename,
            ) from None
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
                return Decimal(str(node.value)) if isinstance(node.value, float) else node.value
        if isinstance(node, ast.UnaryOp):
            value = ev(node.operand)
            if isinstance(node.op, ast.Not): return not bool(value)
            if isinstance(node.op, ast.UAdd): return +value
            if isinstance(node.op, ast.USub): return -value
            if isinstance(node.op, ast.Invert): return ~int(value)
        if isinstance(node, ast.BoolOp):
            # Short-circuit inactive operands (e.g. #if 0 && (1/0)).
            if isinstance(node.op, ast.And):
                return all(bool(ev(item)) for item in node.values)
            if isinstance(node.op, ast.Or):
                return any(bool(ev(item)) for item in node.values)
        if isinstance(node, ast.BinOp):
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div): return left / right
            if isinstance(node.op, ast.FloorDiv): return left // right
            if isinstance(node.op, ast.Mod): return left % right
            if isinstance(node.op, ast.BitAnd): return int(left) & int(right)
            if isinstance(node.op, ast.BitOr): return int(left) | int(right)
            if isinstance(node.op, ast.BitXor): return int(left) ^ int(right)
            if isinstance(node.op, ast.LShift): return int(left) << int(right)
            if isinstance(node.op, ast.RShift): return int(left) >> int(right)
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
    except TypeError:
        raise DBaseCompilerError(
            f"Inkompatible Datentypen im Makro-Ausdruck: {expression} (z. B. String und Zahl)",
            line=line, column=1, filename=filename,
        ) from None
    except (ValueError, ZeroDivisionError, OverflowError):
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
        if (
            text.startswith("//", i)
            or text.startswith("&&", i)
            or (
                text.startswith("**", i)
                and not _is_dbase_variadic_parameter_marker(text, i)
            )
        ):
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
    branch_taken: bool
    else_seen: bool = False


def _resolve_include_path(raw: str, *, filename: str, line: int, include_paths=(),
                          directive: str = "#include") -> Path:
    value = str(raw or "").strip()
    match = re.fullmatch(r'"([^"]+)"', value)
    if match is None:
        raise DBaseCompilerError(
            f'{directive} erwartet einen Pfad in doppelten Anfuehrungszeichen.',
            line=line,
            column=1,
            filename=filename,
        )
    include_name = os.path.expandvars(os.path.expanduser(match.group(1)))
    requested = Path(include_name)
    origin = Path(filename)
    roots = ([origin.parent] if filename and not str(filename).startswith("<") else [Path.cwd()])
    roots.extend(Path(entry).expanduser() for entry in (include_paths or ()) if str(entry).strip())
    candidates = [requested] if requested.is_absolute() else [root / requested for root in roots]
    # dBASE system units commonly omit the .prg extension in #include.
    if requested.suffix.casefold() not in ('.prg', '.dbase', '.h', '.inc'):
        candidates += [Path(str(candidate) + '.prg') for candidate in candidates]
    checked = []
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except (OSError, RuntimeError):
            resolved = candidate.absolute()
        checked.append(str(resolved))
        if resolved.is_file():
            return resolved
    raise DBaseCompilerError(
        f"{directive}-Datei nicht gefunden: " + include_name +
        "\nGepruefte Pfade: " + "; ".join(checked),
        line=line, column=1, filename=filename,
    )


def _read_dbase_include(path: Path, *, filename: str, line: int,
                        manager: Optional[DBaseProcedureFileManager] = None,
                        mode: str = 'include') -> str:
    directive = '#include' if mode == 'include' else 'SET PROCEDURE'
    try:
        data = manager.read(path, mode=mode) if manager is not None else path.read_bytes()
    except OSError as exc:
        raise DBaseCompilerError(
            f'{directive}-Datei konnte nicht gelesen werden: {path}: {exc}',
            line=line, column=1, filename=filename,
        ) from None
    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            return data.decode('cp1252')
        except UnicodeDecodeError as exc:
            raise DBaseCompilerError(
                f'{directive}-Datei ist weder UTF-8 noch Windows-1252: {path}',
                line=line, column=1, filename=filename,
            ) from exc


_SET_PROCEDURE_PREFIX = re.compile(r'^\s*SET\s+PROCEDURE\b', re.I)
_SET_PROCEDURE_LINE = re.compile(
    r'^\s*SET\s+PROCEDURE(?:\s+TO)?\s+("[^"\r\n]+")\s+(EXCLUSIVE|ADDITIVE)\s*$',
    re.I,
)


def _dbase_include_guard(source: str, *, filename: str) -> Optional[str]:
    """Find a conventional file-covering #ifndef NAME / #define NAME guard.

    Only a guard around the *entire* file is accepted. This permits a
    recursive include to be skipped when its guard is already defined, while
    genuinely unguarded include cycles still raise a useful diagnostic.
    """
    cleaned = strip_dbase_comments(source, filename=filename)
    logical = [(line.strip(), n) for n, line in enumerate(cleaned.splitlines(), 1)
               if line.strip()]
    if len(logical) < 3:
        return None
    first = re.fullmatch(r'#ifndef\s+([A-Za-z_]\w*)', logical[0][0], re.I)
    if not first or not re.fullmatch(r'#define\s+' + re.escape(first.group(1)) +
                                      r'(?:\s+[^\r\n]+)?', logical[1][0], re.I):
        return None
    depth = 0
    for index, (line, _) in enumerate(logical):
        directive = re.match(r'#\s*(if|ifdef|ifndef|endif)\b', line, re.I)
        if directive:
            if directive.group(1).casefold() == 'endif':
                depth -= 1
                if depth == 0 and index != len(logical) - 1:
                    return None
                if depth < 0:
                    return None
            else:
                depth += 1
    return first.group(1) if depth == 0 else None


def remap_dbase_source_error(error: DBaseCompilerError,
                             locations: Tuple[DBaseSourceLocation, ...]) -> DBaseCompilerError:
    """Translate flattened preprocessor lines back to physical include lines."""
    if not (error.line and 1 <= error.line <= len(locations)):
        return error
    origin = locations[error.line - 1]
    if origin.filename == error.filename and origin.line == error.line:
        return error
    chain = ' -> '.join(f'{name}:{at_line}' for name, at_line in origin.include_chain)
    suffix = f' (eingebunden ueber {chain})' if chain else ''
    return DBaseCompilerError(error.message + suffix, line=origin.line,
                              column=error.column, filename=origin.filename)


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


def _preprocess_dbase_macros(
    source: str,
    *,
    filename: str,
    _macros: Optional[Dict[str, DBaseMacro]] = None,
    _links: Optional[list[DBasePragmaLink]] = None,
    _warnings: Optional[list[str]] = None,
    _infos: Optional[list[str]] = None,
    _include_stack: Optional[Tuple[Path, ...]] = None,
    _source_locations: Optional[list[DBaseSourceLocation]] = None,
    _include_chain: Tuple[Tuple[str, int], ...] = (),
    _line_manager: Optional[DBaseIncludeLineManager] = None,
    _procedure_manager: Optional[DBaseProcedureFileManager] = None,
    _compile_date: str = "",
    _compile_time: str = "",
    target: str = "pe32",
    include_paths=(),
) -> Tuple[str, Tuple[DBaseMacro, ...], Tuple[DBasePragmaLink, ...], Tuple[str, ...], Tuple[str, ...]]:
    """C/C++-artiger dBase-Praeprozessor mit rekursiven Includes."""
    masked = strip_dbase_comments(source, filename=filename)
    original_lines = source.splitlines(keepends=True)
    masked_lines = masked.splitlines(keepends=True)

    macros = _macros if _macros is not None else {}
    if _macros is None:
        # Platform macros are a per-compilation state, shared with nested includes.
        # Explicit #undef/#define in user source remains possible.
        selected = str(target).casefold().strip()
        if selected.startswith(('linux', 'elf')):
            # Nur die aktive Plattform definieren: #ifdef prueft die
            # Existenz des Symbols, nicht dessen numerischen Wert.
            platform_macros = ('LINUX',)
        elif selected in {'pe32', 'pe64'}:
            # WIN32 ist wie _WIN32 bei MSVC auf PE32 und PE64 definiert.
            # Fuer die Bitness kann WIN64 separat geprueft werden.
            platform_macros = ('WINDOWS', 'WIN32') + (('WIN64',) if selected == 'pe64' else ())
        else:
            platform_macros = ()
        for platform_macro in platform_macros:
            macros[platform_macro.casefold()] = DBaseMacro(platform_macro, None, '1', 0, 0)
    links = _links if _links is not None else []
    warnings = _warnings if _warnings is not None else []
    infos = _infos if _infos is not None else []
    include_stack = tuple(_include_stack or ())
    procedure_manager = _procedure_manager

    if not _compile_date or not _compile_time:
        compile_now = datetime.now()
        compile_date = f"{compile_now:%b} {compile_now.day:2d} {compile_now:%Y}"
        compile_time = compile_now.strftime("%H:%M:%S")
    else:
        compile_date = _compile_date
        compile_time = _compile_time

    # Hauptdatei in den Include-Stack aufnehmen, damit direkte/indirekte
    # Selbst-Includes sauber erkannt werden.
    if not include_stack and filename and not str(filename).startswith("<"):
        try:
            root_path = Path(filename).resolve()
            include_stack = (root_path,)
        except OSError:
            pass

    stack: list[_DBaseConditionalFrame] = []
    output: list[str] = []
    locations = _source_locations if _source_locations is not None else []
    line_manager = _line_manager if _line_manager is not None else DBaseIncludeLineManager(filename)
    active = True
    block_state = False

    def evaluate_condition(expr: str, line_no: int) -> bool:
        return _safe_eval_macro_condition(
            expr,
            macros,
            filename=filename,
            line=line_no,
            compile_date=compile_date,
            compile_time=compile_time,
        )

    def _append_dbase_file_source(path: Path, *, mode: str, directive: str,
                                  line_no: int, orig_line: str):
        # Both directives use the same LIFO source map / macro namespace.
        # Source bytes are cached: guarded cycles never re-open an EXCLUSIVE
        # Windows handle, and repeated files use one consistent snapshot.
        if len(include_stack) >= 64:
            raise DBaseCompilerError(
                f'Maximale {directive}-Verschachtelung (64) ueberschritten.',
                line=line_no, column=1, filename=filename)
        # A previously loaded *guarded* file is a true no-op, even if the
        # caller selects a different Windows sharing mode this time.
        # In particular, do not try to re-open an EXCLUSIVE handle merely
        # to discover the guard that is already known to the compiler.
        if procedure_manager is not None and procedure_manager.has_snapshot(path):
            snapshot = _read_dbase_include(
                path, filename=filename, line=line_no,
                manager=procedure_manager, mode='include')
            old_guard = _dbase_include_guard(snapshot, filename=str(path))
            if old_guard and _is_dbase_macro_defined(old_guard, macros):
                output.append(_blank_directive_line(orig_line))
                locations.append(DBaseSourceLocation(filename, line_no, _include_chain))
                return
        child_source = _read_dbase_include(
            path, filename=filename, line=line_no,
            manager=procedure_manager, mode=mode)
        guard = _dbase_include_guard(child_source, filename=str(path))
        guarded = bool(guard and _is_dbase_macro_defined(guard, macros))
        if path in include_stack and not guarded:
            chain = ' -> '.join(str(p) for p in include_stack + (path,))
            raise DBaseCompilerError(
                f'Rekursives {directive} ohne wirksamen Include-Guard: {chain}',
                line=line_no, column=1, filename=filename)
        output.append(_blank_directive_line(orig_line))
        locations.append(DBaseSourceLocation(filename, line_no, _include_chain))
        if guarded:
            return
        child_locations: list[DBaseSourceLocation] = []
        line_manager.push(str(path), line_no)
        try:
            child_text, _, _, _, _ = _preprocess_dbase_macros(
                child_source, filename=str(path),
                _macros=macros, _links=links, _warnings=warnings, _infos=infos,
                _include_stack=include_stack + (path,),
                _source_locations=child_locations,
                _include_chain=_include_chain + ((filename, line_no),),
                _line_manager=line_manager,
                _procedure_manager=procedure_manager,
                _compile_date=compile_date, _compile_time=compile_time,
                target=target, include_paths=include_paths,
            )
        finally:
            line_manager.pop()
        output.append(child_text)
        locations.extend(child_locations)
        if child_text and not child_text.endswith(('\n', '\r')) and orig_line.endswith(('\n', '\r')):
            output.append('\n')

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
                condition = False
                if parent:
                    if keyword == "ifdef":
                        if not _IDENTIFIER_RE.fullmatch(rest):
                            raise DBaseCompilerError(
                                "#ifdef erwartet genau einen Makronamen.",
                                line=line_no, column=1, filename=filename,
                            )
                        condition = _is_dbase_macro_defined(rest, macros)
                    elif keyword == "ifndef":
                        if not _IDENTIFIER_RE.fullmatch(rest):
                            raise DBaseCompilerError(
                                "#ifndef erwartet genau einen Makronamen.",
                                line=line_no, column=1, filename=filename,
                            )
                        condition = not _is_dbase_macro_defined(rest, macros)
                    else:
                        condition = evaluate_condition(rest, line_no)
                stack.append(_DBaseConditionalFrame(parent, bool(condition)))
                active = parent and bool(condition)

            elif keyword == "elif":
                if not stack:
                    raise DBaseCompilerError(
                        "#elif ohne passendes #if/#ifdef/#ifndef.",
                        line=line_no, column=1, filename=filename,
                    )
                frame = stack[-1]
                if frame.else_seen:
                    raise DBaseCompilerError(
                        "#elif nach #else ist nicht erlaubt.",
                        line=line_no, column=1, filename=filename,
                    )
                condition = False
                if frame.parent_active and not frame.branch_taken:
                    condition = evaluate_condition(rest, line_no)
                active = frame.parent_active and (not frame.branch_taken) and bool(condition)
                if active:
                    frame.branch_taken = True

            elif keyword == "else":
                if not stack:
                    raise DBaseCompilerError(
                        "#else ohne passendes #if/#ifdef/#ifndef.",
                        line=line_no, column=1, filename=filename,
                    )
                frame = stack[-1]
                if frame.else_seen:
                    raise DBaseCompilerError(
                        "Mehrfaches #else im selben Praeprozessor-Block.",
                        line=line_no, column=1, filename=filename,
                    )
                frame.else_seen = True
                active = frame.parent_active and not frame.branch_taken
                if active:
                    frame.branch_taken = True

            elif keyword == "endif":
                if not stack:
                    raise DBaseCompilerError(
                        "#endif ohne passendes #if/#ifdef/#ifndef.",
                        line=line_no, column=1, filename=filename,
                    )
                frame = stack.pop()
                active = frame.parent_active

            # Alle weiteren Direktiven werden in einem inaktiven Zweig wie
            # beim C-Praeprozessor ignoriert. Damit kann #if 0 auch absichtlich
            # unkompilierbaren oder unvollstaendigen dBase-Code kapseln.
            elif not active:
                pass

            elif keyword == "define":
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

            elif keyword == "undef":
                if not _IDENTIFIER_RE.fullmatch(rest):
                    raise DBaseCompilerError(
                        "#undef erwartet genau einen Makronamen.",
                        line=line_no, column=1, filename=filename,
                    )
                macros.pop(rest.casefold(), None)

            elif keyword == "include":
                include_path = _resolve_include_path(
                    rest, filename=filename, line=line_no, include_paths=include_paths)
                _append_dbase_file_source(
                    include_path, mode='include', directive='#include',
                    line_no=line_no, orig_line=orig_line,
                )
                continue

            elif keyword in {"error", "warning", "warn", "info"}:
                message_text = rest.strip() or f"#{keyword}"
                message_text = re.sub(r"(?<![\w])#(?=__(?:FILE|LINE|DATE|TIME)__\b)", "", message_text, flags=re.I)
                expanded_message, _ = _expand_dbase_macro_text(
                    message_text,
                    macros,
                    filename=filename,
                    line=line_no,
                    compile_date=compile_date,
                    compile_time=compile_time,
                )
                # Diagnostic messages display the basename rather than a quoted
                # absolute __FILE__ path. Normal source expressions keep the
                # original full path and string quotation.
                expanded_message = expanded_message.replace(
                    _quote_dbase_predefined_string(str(filename)), Path(filename).name
                )
                expanded_message = " ".join(expanded_message.split())
                location = f"{filename}:{line_no}: #{keyword}: {expanded_message}"
                if keyword == "error":
                    raise DBaseCompilerError(
                        f"#error: {expanded_message}",
                        line=line_no, column=1, filename=filename,
                    )
                if keyword in {"warning", "warn"}:
                    warnings.append(location)
                else:
                    infos.append(location)

            elif keyword == "pragma":
                pm = re.match(r"link\b(.*)$", rest, flags=re.IGNORECASE)
                if pm is None:
                    raise DBaseCompilerError("Derzeit wird nur #pragma link unterstuetzt.", line=line_no, column=1, filename=filename)
                links.append(_resolve_pragma_link_path(pm.group(1).strip(), filename=filename, line=line_no))

            elif keyword:
                raise DBaseCompilerError(
                    f"Unbekannte Praeprozessor-Anweisung #{keyword}.",
                    line=line_no, column=1, filename=filename,
                )

            output.append(_blank_directive_line(orig_line))
            locations.append(DBaseSourceLocation(filename, line_no, _include_chain))
            continue

        if not active:
            output.append(_blank_directive_line(orig_line))
            locations.append(DBaseSourceLocation(filename, line_no, _include_chain))
            continue

        if _SET_PROCEDURE_PREFIX.match(masked_line):
            proc_match = _SET_PROCEDURE_LINE.fullmatch(masked_line.rstrip('\r\n'))
            if proc_match is None:
                raise DBaseCompilerError(
                    'SET PROCEDURE erwartet "Datei.prg" EXCLUSIVE oder ADDITIVE.',
                    line=line_no, column=1, filename=filename)
            proc_path = _resolve_include_path(
                proc_match.group(1), filename=filename, line=line_no,
                include_paths=include_paths, directive='SET PROCEDURE')
            mode = proc_match.group(2).casefold()
            _append_dbase_file_source(
                proc_path, mode=mode, directive='SET PROCEDURE',
                line_no=line_no, orig_line=orig_line)
            infos.append(f'{filename}:{line_no}: SET PROCEDURE {mode.upper()}: {proc_path}')
            continue

        active_line = re.sub(r"(?<![\w])#(?=__(?:FILE|LINE|DATE|TIME)__\b)", "", orig_line, flags=re.I)
        expanded, block_state = _expand_dbase_macro_text(
            active_line,
            macros,
            in_block_comment=block_state,
            filename=filename,
            line=line_no,
            compile_date=compile_date,
            compile_time=compile_time,
        )
        output.append(expanded)
        locations.append(DBaseSourceLocation(filename, line_no, _include_chain))

    if stack:
        raise DBaseCompilerError(
            "Fehlendes #endif am Dateiende.",
            line=len(original_lines) or 1,
            column=1,
            filename=filename,
        )
    return "".join(output), tuple(macros.values()), tuple(links), tuple(warnings), tuple(infos)


def preprocess_dbase_source(
    source: str,
    *,
    filename: str = "<dBase>",
    target: str = "pe32",
    include_paths=(),
) -> DBaseFrontendResult:
    text = str(source or "")
    normalized_target = normalize_dbase_target(target)
    comments = scan_dbase_comments(text, filename=filename)
    cleaned = strip_dbase_comments(text, filename=filename)
    source_locations: list[DBaseSourceLocation] = []
    with DBaseProcedureFileManager() as procedure_manager:
        preprocessed, macros, pragma_links, preprocessor_warnings, preprocessor_infos = _preprocess_dbase_macros(
            text, filename=filename, include_paths=include_paths, target=normalized_target,
            _source_locations=source_locations, _procedure_manager=procedure_manager,
        )
    from .ffi import extract_ffi_prototypes
    try:
        preprocessed, ffi_prototypes = extract_ffi_prototypes(preprocessed, filename=filename)
    except ValueError as exc:
        raise DBaseCompilerError(str(exc), filename=filename) from None
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
        ffi_prototypes=ffi_prototypes,
        source_locations=tuple(source_locations),
    )


def compile_dbase_frontend(
    source: str,
    *,
    filename: str = "<dBase>",
    target: str = "pe32",
    include_paths=(),
) -> DBaseFrontendResult:
    """Öffentlicher Einstieg der ersten dBase-Compilerstufe.

    Diese Stufe ist bewusst ausschließlich für Kommentare zuständig. Sie ist
    bereits auf PE32/PE32+ festgelegt, damit spätere Parser- und Codegen-Stufen
    dieselbe API weiterverwenden können.
    """
    return preprocess_dbase_source(source, filename=filename, target=target, include_paths=include_paths)


_NUMBER_RE = re.compile(
    r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
)
_HEX_0X_RE = re.compile(r"0[xX][0-9A-Fa-f]+")
_HEX_DOLLAR_RE = re.compile(r"\$[0-9A-Fa-f]+")
_HEX_SUFFIX_RE = re.compile(r"[0-9][0-9A-Fa-f]*[hH](?![A-Za-z0-9_])")
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")

_TYPE_NUMBER = 1
_TYPE_STRING = 2
_TYPE_CHAR = 3
_TYPE_LOGICAL = 4
_TYPE_DATE = 5
_STRING_KINDS = {"string", "char"}

# Stage 464: dBASE type information returned by TYPE()/VARTYPE().
# The PRG value slots store 1=number, 2=string, 3=char.
def _dbase_type_letter(kind: str) -> str:
    return {"number": "N", "string": "C", "char": "C", "logical": "L",
            "date": "D", "memo": "M", "object": "O"}.get(str(kind).casefold(), "U")


def _dbase_date_iso(raw: str, *, filename: str, line: int, column: int) -> str:
    """Validate dBASE {^YYYY-MM-DD} dates; store a canonical ISO calendar day."""
    try:
        return date.fromisoformat(str(raw)).isoformat()
    except ValueError as exc:
        raise DBaseCompilerError(
            f"Ungueltiges dBASE-Datum '{raw}' (erwartet {{^YYYY-MM-DD}}).",
            line=line, column=column, filename=filename,
        ) from exc


def _dbase_type_query_name(expression) -> str | None:
    """Classic TYPE('variable'): deliberately require a constant variable name."""
    if isinstance(expression, DBaseLiteralExpression) and expression.value_type in _STRING_KINDS:
        name = str(expression.value).strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            return name.casefold()
    return None



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
            ("!=", "NEBANG"),
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

        # Stage 465: Boolean values must precede dot operators and numbers.
        logical_match = re.match(r"\.(T|F)\.(?![A-Za-z0-9_])", text[index:], re.I)
        if logical_match is not None:
            raw = logical_match.group(0)
            tokens.append(DBaseToken("LOGICAL", raw, raw[1].upper() == "T",
                                     token_line, token_column, token_offset))
            index += len(raw)
            column += len(raw)
            continue

        # Date literals are unambiguous: {^2026-10-19} or {2026-10-19}.
        if char == "{":
            date_match = re.match(r"\{\^?(\d{4}-\d{2}-\d{2})\}", text[index:])
            if date_match is None:
                raise DBaseCompilerError(
                    "Datumliteral erwartet {^YYYY-MM-DD}.",
                    line=token_line, column=token_column, filename=filename)
            raw = date_match.group(0)
            iso = _dbase_date_iso(date_match.group(1), filename=filename,
                                  line=token_line, column=token_column)
            tokens.append(DBaseToken("DATE_LITERAL", raw, iso, token_line,
                                     token_column, token_offset))
            index += len(raw)
            column += len(raw)
            continue

        # dBase dot-delimited logical operators; case-insensitive and atomic.
        # Test before NUMBER: '.not.' must never be scanned as a fractional number.
        dot_operator = re.match(r"\.(AND|OR|NOT|XOR)\.", text[index:], re.I)
        if dot_operator is not None:
            raw = dot_operator.group(0)
            tokens.append(DBaseToken("LOGIC_" + dot_operator.group(1).upper(),
                                     raw, raw.casefold(), token_line, token_column, token_offset))
            index += len(raw)
            column += len(raw)
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
            # 0.AND. / 1.OR. without whitespace: the final dot is the
            # beginning of an operator, not the decimal separator.
            if raw.endswith(".") and re.match(
                r"\.(?:AND|OR|XOR|NOT)\.", text[index + len(raw) - 1:], re.I
            ):
                raw = raw[:-1]
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
            index += len(raw)
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
            ".": "DOT",  # Stage 647: super().FIELD after a call
            "#": "NEHASH",
            "!": "BANG",
            "$": "DOLLAR",
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

        # dBase STORE <Ausdruck> TO <SpeicherVariable>. Intern wird STORE auf
        # denselben Zuweisungsknoten wie ``name = expression`` abgebildet.
        # Damit bleiben Typanalyse, Speicherverwaltung, IF-Sichtbarkeit und
        # Codeerzeugung an genau einer Stelle implementiert.
        if first.kind == "IDENT" and str(first.value).casefold() == "store":
            self.index += 1
            if self.current.kind == "EOF":
                raise DBaseCompilerError(
                    "Nach STORE wird ein Ausdruck erwartet.",
                    line=first.line,
                    column=first.column,
                    filename=self.filename,
                )
            expression = self.parse_expression()
            self._expect_keyword("to", "Nach STORE <Ausdruck> wird TO erwartet.")
            target = self.current
            if target.kind != "IDENT":
                raise DBaseCompilerError(
                    "Nach STORE <Ausdruck> TO wird ein Variablenname erwartet.",
                    line=target.line,
                    column=target.column,
                    filename=self.filename,
                )
            target_name = str(target.value)
            if target_name.casefold() in {
                "and", "case", "class", "do", "else", "endcase",
                "endclass", "endif", "endproc", "endprocedure", "exit",
                "false", "for", "function", "if", "local", "not", "null",
                "off", "on", "or", "parameters", "private", "procedure",
                "public", "return", "set", "store", "this", "to", "true",
                "while",
            }:
                raise DBaseCompilerError(
                    "Reserviertes dBase-Schluesselwort ist als "
                    f"STORE-Ziel nicht erlaubt: {target_name}",
                    line=target.line,
                    column=target.column,
                    filename=self.filename,
                )
            if (
                isinstance(expression, DBaseIdentifierExpression)
                and expression.name.casefold() == target_name.casefold()
            ):
                raise DBaseCompilerError(
                    "Identische/zirkulaere STORE-Zuweisung ist nicht erlaubt: "
                    f"{target_name} TO {target_name}",
                    line=first.line,
                    column=first.column,
                    filename=self.filename,
                )
            self.index += 1
            self._expect_eof()
            return DBaseAssignmentStatement(
                name=target_name,
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

        # Stage 342: SAY accepts a dBase string expression.
        if first.kind == "IDENT" and str(first.value).casefold() == "say":
            self.index += 1
            if self.current.kind == "EOF":
                raise DBaseCompilerError(
                    'SAY erwartet einen String-Ausdruck.',
                    line=first.line, column=first.column, filename=self.filename,
                )
            expression = self.parse_expression()
            self._expect_eof()
            return DBaseSayStatement(expression, first.line, first.column)

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
                    "Nach SET wird FORMAT, DEBUG, SPEECH, COLOR, BACKGROUND oder BORDERCOLOR erwartet.",
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
            if keyword == "speech":
                action = self.current
                if action.kind != "IDENT":
                    raise DBaseCompilerError(
                        "SET SPEECH erwartet ON, OFF, MODE, MIX, PITCH, SPEED, FLUENCY, EXPRESSION oder ARTICULATION.",
                        line=action.line, column=action.column, filename=self.filename,
                    )
                option = str(action.value).casefold()
                self.index += 1
                if option in {"on", "off"}:
                    self._expect_eof()
                    return DBaseSetSpeechStatement("state", option, first.line, first.column)
                if option == "mode":
                    mode = self.current
                    if mode.kind != "IDENT" or str(mode.value).casefold() not in {"hybrid", "c64", "amiga", "piper", "samples"}:
                        raise DBaseCompilerError(
                            "SET SPEECH MODE erwartet HYBRID, C64, AMIGA, PIPER oder SAMPLES.",
                            line=mode.line, column=mode.column, filename=self.filename,
                        )
                    self.index += 1
                    self._expect_eof()
                    return DBaseSetSpeechStatement("mode", str(mode.value).casefold(), first.line, first.column)
                limits = {"mix": (0, 100), "pitch": (70, 260), "speed": (50, 200),
                          "fluency": (0, 100), "expression": (0, 100),
                          "articulation": (0, 100)}
                if option not in limits:
                    raise DBaseCompilerError(
                        "SET SPEECH erwartet ON, OFF, MODE, MIX, PITCH, SPEED, FLUENCY, EXPRESSION oder ARTICULATION.",
                        line=action.line, column=action.column, filename=self.filename,
                    )
                value = self.current
                if value.kind != "NUMBER":
                    raise DBaseCompilerError(
                        f"SET SPEECH {option.upper()} erwartet eine ganze Zahl.",
                        line=value.line, column=value.column, filename=self.filename,
                    )
                try:
                    parsed = Decimal(str(value.value))
                    if parsed != parsed.to_integral_value():
                        raise ValueError
                    number = int(parsed)
                except (ValueError, TypeError, InvalidOperation):
                    raise DBaseCompilerError(
                        f"SET SPEECH {option.upper()} erwartet eine ganze Zahl.",
                        line=value.line, column=value.column, filename=self.filename,
                    )
                self.index += 1
                self._expect_eof()
                low, high = limits[option]
                if not low <= number <= high:
                    raise DBaseCompilerError(
                        f"SET SPEECH {option.upper()} erwartet {low} bis {high}.",
                        line=value.line, column=value.column, filename=self.filename,
                    )
                return DBaseSetSpeechStatement(option, number, first.line, first.column)
            if keyword == "background":
                self._expect_keyword("to", "Nach SET BACKGROUND wird TO erwartet.")
                arguments = [self.parse_expression()]
                while self.take("COMMA") is not None:
                    arguments.append(self.parse_expression())
                if len(arguments) not in (1, 3):
                    raise DBaseCompilerError(
                        "SET BACKGROUND TO erwartet genau 1 oder 3 numerische Ausdruecke.",
                        line=first.line, column=first.column, filename=self.filename,
                    )
                self._expect_eof()
                return DBaseSetBackgroundStatement(tuple(arguments), first.line, first.column)
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
                "Nach SET wird FORMAT, DEBUG, SPEECH, COLOR, BACKGROUND oder BORDERCOLOR erwartet.",
                line=command.line,
                column=command.column,
                filename=self.filename,
            )

        raise DBaseCompilerError(
            "Erwartet wird '?' oder '??', eine Variablenzuweisung, ein Member-Aufruf, "
            "RETURN, CLEAR SCREEN, SAY <text>, SET SPEECH ..., SET FORMAT TO ..., SET DEBUG ON/OFF, "
            "SET COLOR TO ..., SET BACKGROUND TO ... oder SET BORDERCOLOR TO ... .",
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
        return self.parse_logical_or()

    def _parse_logical_chain(self, operand_parser, kind: str) -> DBaseExpression:
        expression = operand_parser()
        while self.current.kind == kind:
            operator = self.current
            self.index += 1
            right = operand_parser()
            expression = DBaseBinaryExpression(
                line=operator.line, column=operator.column,
                operator=operator.text.casefold(), left=expression, right=right,
            )
        return expression

    def parse_logical_or(self) -> DBaseExpression:
        return self._parse_logical_chain(self.parse_logical_xor, "LOGIC_OR")

    def parse_logical_xor(self) -> DBaseExpression:
        return self._parse_logical_chain(self.parse_logical_and, "LOGIC_XOR")

    def parse_logical_and(self) -> DBaseExpression:
        return self._parse_logical_chain(self.parse_logical_not, "LOGIC_AND")

    def parse_logical_not(self) -> DBaseExpression:
        if self.current.kind == "LOGIC_NOT":
            token = self.current
            self.index += 1
            return DBaseUnaryExpression(line=token.line, column=token.column,
                operator=".not.", operand=self.parse_logical_not())
        return self.parse_comparison()

    def parse_comparison(self) -> DBaseExpression:
        left = self.parse_additive()
        if self.current.kind not in _COMPARISON_TOKEN_KINDS:
            return left
        token = self.current
        self.index += 1
        right = self.parse_additive()
        return DBaseCondition(line=token.line, column=token.column, left=left,
                              operator=_COMPARISON_OPERATOR_MAP[token.kind], right=right)

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
        if self.take("DOLLAR") is not None:
            self.expect("LPAREN", "$(...) erwartet eine oeffnende Klammer.")
            arguments = [self.parse_expression()]
            self.expect("COMMA", "$(...) erwartet String und Anfangsposition.")
            arguments.append(self.parse_expression())
            if self.take("COMMA") is not None:
                arguments.append(self.parse_expression())
            self.expect("RPAREN", "$(...) erwartet zwei oder drei Parameter.")
            return DBaseCallExpression(line=token.line, column=token.column,
                                       name="$", arguments=tuple(arguments))
        if self.take("BANG") is not None:
            self.expect("LPAREN", "!(...) erwartet eine oeffnende Klammer.")
            argument = self.parse_expression()
            self.expect("RPAREN", "!(...) erwartet genau einen String und eine schliessende Klammer.")
            return DBaseCallExpression(line=token.line, column=token.column,
                                       name="!", arguments=(argument,))
        if self.take("LOGICAL") is not None:
            return DBaseLiteralExpression(
                line=token.line, column=token.column, value_type="logical",
                value=bool(token.value), text=token.text)
        if self.take("DATE_LITERAL") is not None:
            return DBaseLiteralExpression(
                line=token.line, column=token.column, value_type="date",
                value=str(token.value), text=token.text)
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
            # Stage 602: dBASE NULL is the zero/null pointer literal. NIL is
            # intentionally *not* a synonym (it belongs to Pascal).
            if name.casefold() == "null":
                return DBaseLiteralExpression(
                    line=token.line, column=token.column, value_type="number",
                    value=Decimal(0), text=token.text)
            if self.take("LPAREN") is not None:
                arguments: list[DBaseExpression] = []
                if self.current.kind != "RPAREN":
                    arguments.append(self.parse_expression())
                    while self.take("COMMA") is not None:
                        arguments.append(self.parse_expression())
                self.expect("RPAREN", "Fehlende schliessende Klammer ')' im Funktionsaufruf.")
                # Stage 647: SUPER is a lexical parent selector, not an
                # instantiable receiver. Only SUPER().<inherited-field> is
                # lowered to a qualified identifier for the native emitter.
                if name.casefold() == "super" and self.take("DOT") is not None:
                    member = self.expect("IDENT", "SUPER(). erwartet einen geerbten Feldnamen.")
                    if "." in str(member.value):
                        raise DBaseCompilerError(
                            "SUPER(). erwartet genau einen Feldnamen.",
                            line=member.line, column=member.column, filename=self.filename)
                    return DBaseIdentifierExpression(
                        line=token.line, column=token.column,
                        name="super." + str(member.value))
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
_EXCEPTION_STOP_KEYWORDS = {"catch", "finally", "endtry", "end"}

_COMPARISON_TOKEN_KINDS = {
    "LT", "LE", "EQUAL", "EQEQ", "GT", "GE", "NEANGLE", "NEHASH", "NEBANG"
}
_COMPARISON_OPERATOR_MAP = {
    "LT": "<",
    "LE": "<=",
    "EQUAL": "==",
    "EQEQ": "==",
    "GT": ">",
    "GE": ">=",
    "NEANGLE": "!=",
    "NEHASH": "!=",
    "NEBANG": "!=",
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
    tokens: Tuple[DBaseToken, ...], *, filename: str, keyword: str,
) -> DBaseExpression:
    """Parse a complete boolean IF/ELSEIF expression with normal precedence."""
    first = tokens[0]
    body = tuple(token for token in tokens[1:] if token.kind != "EOF")
    if not body:
        raise DBaseCompilerError(
            f"Nach {keyword.upper()} wird eine Bedingung erwartet.",
            line=first.line, column=first.column, filename=filename,
        )
    return _expression_from_token_slice(body, filename=filename, fallback=first)


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
        first = parser.current
        if first.kind == "IDENT" and str(first.value).casefold() == "throw":
            parser.index += 1
            if parser.current.kind == "EOF":
                return DBaseThrowStatement("", None, "", first.line, first.column)
            if (parser.current.kind == "IDENT" and
                    str(parser.current.value).casefold() == "new"):
                parser.index += 1
                class_token = parser.expect("IDENT", "Nach THROW NEW wird eine Exception-Klasse erwartet.")
                parser.expect("LPAREN", "THROW NEW Class(...) erwartet '('.")
                message = None
                if parser.current.kind != "RPAREN":
                    message = parser.parse_expression()
                parser.expect("RPAREN", "THROW NEW Class(...) erwartet ')'.")
                parser._expect_eof()
                return DBaseThrowStatement(str(class_token.value), message, "", first.line, first.column)
            if (parser.current.kind == "IDENT" and parser.peek().kind == "EOF"):
                variable = str(parser.current.value)
                parser.index += 1
                return DBaseThrowStatement("", None, variable, first.line, first.column)
            message = parser.parse_expression()
            parser._expect_eof()
            return DBaseThrowStatement("Exception", message, "", first.line, first.column)
        return parser.parse_statement()

    def parse_block(
        index: int,
        *,
        stop_keywords: frozenset[str],
        routine_kind: str = "",
        routine_name: str = "",
        catch_variables: frozenset[str] = frozenset(),
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
            if keyword in _IF_STOP_KEYWORDS | _EXCEPTION_STOP_KEYWORDS:
                raise DBaseCompilerError(
                    f"Unerwartetes {first.text.upper()} ohne passenden IF-/TRY-Block.",
                    line=first.line,
                    column=first.column,
                    filename=filename,
                )
            if keyword == "if":
                statement, index = parse_if(
                    index, routine_kind=routine_kind, routine_name=routine_name,
                    catch_variables=catch_variables,
                )
                result.append(statement)
                continue
            if keyword == "try":
                statement, index = parse_try(index, routine_kind=routine_kind,
                                             routine_name=routine_name,
                                             catch_variables=catch_variables)
                result.append(statement)
                continue
            statement = parse_simple(tokens)
            if isinstance(statement, DBaseThrowStatement) and statement.variable:
                if statement.variable.casefold() not in catch_variables:
                    raise DBaseCompilerError(
                        f"THROW {statement.variable} erwartet eine sichtbare CATCH-Variable.",
                        first.line, first.column, filename)
            if isinstance(statement, DBaseThrowStatement) and not (
                    statement.variable or statement.class_name):
                if not catch_variables:
                    raise DBaseCompilerError("THROW ohne Wert ist nur innerhalb CATCH erlaubt.",
                                             first.line, first.column, filename)
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

    def parse_try(
        index: int,
        *,
        routine_kind: str = "",
        routine_name: str = "",
        catch_variables: frozenset[str] = frozenset(),
    ) -> tuple[DBaseTryStatement, int]:
        tokens, _ = records[index]
        first = tokens[0]
        if len(tokens) != 2:
            raise DBaseCompilerError("TRY darf keine Parameter enthalten.",
                                     first.line, first.column, filename)
        try_body, at = parse_block(
            index + 1, stop_keywords=frozenset({"catch", "finally", "endtry", "end"}),
            routine_kind=routine_kind, routine_name=routine_name,
            catch_variables=catch_variables)
        catches: list[DBaseCatchClause] = []
        while at < len(records) and records[at][1] == "catch":
            catch_tokens, _ = records[at]
            cp = _DBaseExpressionParser(catch_tokens, filename=filename)
            cp.index += 1
            cp.expect("LPAREN", "CATCH erwartet (ExceptionClass variable).")
            type_token = cp.expect("IDENT", "CATCH erwartet eine Exception-Klasse.")
            var_token = cp.expect("IDENT", "CATCH erwartet einen Variablennamen.")
            cp.expect("RPAREN", "CATCH erwartet eine schliessende Klammer.")
            cp._expect_eof()
            variable = str(var_token.value)
            body, at = parse_block(
                at + 1, stop_keywords=frozenset({"catch", "finally", "endtry", "end"}),
                routine_kind=routine_kind, routine_name=routine_name,
                catch_variables=catch_variables | {variable.casefold()})
            catches.append(DBaseCatchClause(
                str(type_token.value), variable, tuple(body),
                catch_tokens[0].line, catch_tokens[0].column))
        finally_body: list[object] = []
        seen_finally = at < len(records) and records[at][1] == "finally"
        if seen_finally:
            finally_tokens, _ = records[at]
            if len(finally_tokens) != 2:
                raise DBaseCompilerError("FINALLY darf keine Parameter enthalten.",
                                         finally_tokens[0].line, finally_tokens[0].column, filename)
            finally_body, at = parse_block(
                at + 1, stop_keywords=frozenset({"endtry", "end", "finally", "catch"}),
                routine_kind=routine_kind, routine_name=routine_name,
                catch_variables=catch_variables)
        if at >= len(records) or records[at][1] != "endtry":
            raise DBaseCompilerError(
                "TRY erwartet ENDTRY (TRY ... FINALLY ... END ist entfernt).",
                first.line, first.column, filename)
        end_tokens, _ = records[at]
        if len(end_tokens) != 2:
            raise DBaseCompilerError("ENDTRY darf keine Parameter enthalten.",
                                     end_tokens[0].line, end_tokens[0].column, filename)
        if not catches and not seen_finally:
            raise DBaseCompilerError("TRY benoetigt mindestens CATCH oder FINALLY.",
                                     first.line, first.column, filename)
        return DBaseTryStatement(
            tuple(try_body), tuple(catches), tuple(finally_body),
            first.line, first.column), at + 1

    def parse_if(
        index: int,
        *,
        routine_kind: str = "",
        routine_name: str = "",
        catch_variables: frozenset[str] = frozenset(),
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
            catch_variables=catch_variables,
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
                    catch_variables=catch_variables,
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
                    catch_variables=catch_variables,
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

        if keyword in _IF_STOP_KEYWORDS | _EXCEPTION_STOP_KEYWORDS:
            raise DBaseCompilerError(
                f"Unerwartetes {first.text.upper()} ohne passenden IF-/TRY-Block.",
                line=first.line,
                column=first.column,
                filename=filename,
            )

        if keyword == "if":
            statement, index = parse_if(index)
            statements.append(statement)
            continue
        if keyword == "try":
            statement, index = parse_try(index)
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
                if body_keyword in _IF_STOP_KEYWORDS | _EXCEPTION_STOP_KEYWORDS:
                    raise DBaseCompilerError(
                        f"Unerwartetes {body_first.text.upper()} ohne passenden IF-/TRY-Block.",
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
                if body_keyword == "try":
                    try_statement, index = parse_try(index, routine_kind=kind,
                                                     routine_name=name)
                    body.append(try_statement)
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
    if value.kind == "logical":
        return ".T." if bool(value.value) else ".F."
    if value.kind == "date":
        return str(value.value)
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
    elif left.kind == right.kind == "logical":
        a, b = bool(left.value), bool(right.value)
    elif left.kind == right.kind == "date":
        a, b = str(left.value), str(right.value)
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



def _dbase_exception_hierarchy(statements: Tuple[object, ...]) -> dict[str, tuple[str, str, int]]:
    """Runtime type registry; native class declarations remain the source of ancestry."""
    known: dict[str, tuple[str, str]] = {
        "exception": ("Exception", "TObject"),
        "dbexception": ("DbException", "Exception"),
        "win32exception": ("Win32Exception", "Exception"),
        "win32fileexception": ("Win32FileException", "Win32Exception"),
    }
    for definition in statements:
        if isinstance(definition, DBaseClassDefinition):
            known[definition.name.casefold()] = (definition.name, definition.parent)
    # Only subclasses of Exception qualify for managed dBL THROW/CATCH.
    valid: dict[str, tuple[str, str, int]] = {}
    for key, (name, parent) in known.items():
        seen: set[str] = set()
        current = key
        while current != "exception" and current not in seen:
            seen.add(current)
            current = known.get(current, ("", ""))[1].casefold()
        if current == "exception":
            valid[key] = (name, parent, 0)
    for idx, key in enumerate(sorted(valid), 1):
        name, parent, _ = valid[key]
        valid[key] = (name, parent, idx)
    return valid


def _dbase_catch_prefix(clause: DBaseCatchClause) -> str:
    return f"__dbase_caught_{clause.line}_{clause.column}"

class _DBaseProgramAnalyzer:
    def __init__(self, statements: Tuple[object, ...], *, filename: str, ffi_prototypes=()) -> None:
        self.ffi_prototypes = {item.name.casefold(): item for item in ffi_prototypes}
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
        self.exception_types: dict[str, tuple[str, str, int]] = _dbase_exception_hierarchy(statements)
        self._catch_bindings: list[dict[str, str]] = []

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
            # Stage 464: TYPE("name") resolves a variable by its NAME;
            # VARTYPE(value) evaluates the argument itself.  A missing name
            # yields U instead of a spurious external-function import.
            if expression.name.casefold() in {"type", "vartype"}:
                function = expression.name.upper()
                if len(expression.arguments) != 1:
                    raise DBaseCompilerError(
                        f"{function}(...) erwartet genau einen Parameter.",
                        line=expression.line, column=expression.column,
                        filename=self.filename)
                arg = expression.arguments[0]
                symbol = None
                const_letter = None
                if expression.name.casefold() == "type":
                    name = _dbase_type_query_name(arg)
                    if name is None:
                        raise DBaseCompilerError(
                            'TYPE(...) erwartet einen konstanten Variablennamen, z.B. TYPE("xyz").',
                            line=arg.line, column=arg.column, filename=self.filename)
                    symbol = symbols.get(name) or self.all_global_states.get(name)
                elif (isinstance(arg, DBaseIdentifierExpression) and
                      arg.name.casefold() not in symbols and
                      arg.name.casefold() not in self.all_global_states):
                    const_letter = "U"
                else:
                    operand = (None if isinstance(arg, DBaseIdentifierExpression)
                               and arg.name.casefold() not in symbols
                               else self.analyze_expression(
                                   arg, symbols=symbols, expression_info=expression_info,
                                   call_bindings=call_bindings))
                    if isinstance(arg, DBaseIdentifierExpression):
                        symbol = (symbols.get(arg.name.casefold()) or
                                  self.all_global_states.get(arg.name.casefold()))
                    else:
                        const_letter = _dbase_type_letter(operand.kind)
                if symbol is None and const_letter is None:
                    const_letter = "U"
                info = _DBaseExpressionInfo(
                    kind="string",
                    constant_value=(DBaseValue("string", const_letter)
                                    if const_letter is not None else None),
                    dynamic=symbol is not None,
                    variable_label=symbol.label if symbol is not None else "",
                )
                expression_info[expression] = info
                return info
            # Stage 441: Stringlaenge und drei dynamische Trim-Builtins.
            # Diese Namen sind absichtlich case-insensitive und werden NICHT
            # als externe Qt/DLL-Funktionen oder User-FUNCTION behandelt.
            if expression.name.casefold() in {"len", "ltrim", "rtrim", "trim"}:
                name = expression.name.casefold()
                if len(expression.arguments) != 1:
                    raise DBaseCompilerError(
                        f"{name.upper()}(...) erwartet genau einen String-Ausdruck.",
                        line=expression.line, column=expression.column,
                        filename=self.filename,
                    )
                argument = expression.arguments[0]
                operand = self.analyze_expression(
                    argument, symbols=symbols, expression_info=expression_info,
                    call_bindings=call_bindings,
                )
                if operand.kind not in _STRING_KINDS:
                    raise DBaseCompilerError(
                        f"{name.upper()}(...) erwartet einen String/Char, keinen numerischen Wert.",
                        line=argument.line, column=argument.column,
                        filename=self.filename,
                    )
                from .string_length_trim import string_length, trim_string
                result_kind = "number" if name == "len" else "string"
                constant = None
                if operand.constant_value is not None:
                    text = str(operand.constant_value.value)
                    constant = DBaseValue(result_kind,
                        string_length(text) if name == "len" else trim_string(name, text))
                info = _DBaseExpressionInfo(result_kind, constant, operand.dynamic)
                expression_info[expression] = info
                return info
            # Stage 326: Einzelzeichen-Pruefung; numerischer Boolwert 0 oder 1.
            # Char und einzeichenlange Strings sind erlaubt. Dynamische Strings
            # mit einer anderen Laenge ergeben zur Laufzeit FALSE.
            if expression.name.casefold() in {"isupper", "islower"}:
                function = expression.name.upper()
                if len(expression.arguments) != 1:
                    raise DBaseCompilerError(
                        f"{function}(...) erwartet genau ein Zeichen.",
                        line=expression.line, column=expression.column,
                        filename=self.filename,
                    )
                argument = expression.arguments[0]
                operand = self.analyze_expression(
                    argument, symbols=symbols, expression_info=expression_info,
                    call_bindings=call_bindings,
                )
                if operand.kind not in _STRING_KINDS:
                    raise DBaseCompilerError(
                        f"{function}(...) erwartet ein Zeichen (Char/String), keinen numerischen Wert.",
                        line=argument.line, column=argument.column,
                        filename=self.filename,
                    )
                from .char_case import is_char_case
                constant = (None if operand.constant_value is None else DBaseValue(
                    "number", Decimal(int(is_char_case(
                        str(operand.constant_value.value),
                        upper=(expression.name.casefold() == "isupper"),
                    )))
                ))
                info = _DBaseExpressionInfo(
                    kind="number", constant_value=constant, dynamic=operand.dynamic,
                )
                expression_info[expression] = info
                return info
            # Stage 309: ISMOUSE() ist ein dynamischer Windows-Systemaufruf.
            # Nie konstant falten oder als benutzerdefiniertes externes Symbol behandeln.
            if expression.name.casefold() == "ismouse":
                if expression.arguments:
                    raise DBaseCompilerError(
                        "ISMOUSE() erwartet keine Parameter.",
                        line=expression.line, column=expression.column,
                        filename=self.filename,
                    )
                info = _DBaseExpressionInfo(kind="number", constant_value=None, dynamic=True)
                expression_info[expression] = info
                return info
            if expression.name.casefold() == "iskeyboard":
                if expression.arguments:
                    raise DBaseCompilerError(
                        "ISKEYBOARD() erwartet keine Parameter.",
                        line=expression.line, column=expression.column,
                        filename=self.filename,
                    )
                info = _DBaseExpressionInfo(kind="number", constant_value=None, dynamic=True)
                expression_info[expression] = info
                return info
            if expression.name == "$":
                operands = [self.analyze_expression(arg, symbols=symbols,
                    expression_info=expression_info, call_bindings=call_bindings)
                    for arg in expression.arguments]
                if operands[0].kind not in {"string", "char"} or any(
                        arg.kind != "number" for arg in operands[1:]):
                    raise DBaseCompilerError("$(...) erwartet einen String und numerische Position/Laenge.",
                        line=expression.line, column=expression.column, filename=self.filename)
                from .string_substring import substring
                constant = None
                if all(arg.constant_value is not None for arg in operands):
                    constant = DBaseValue("string", substring(
                        *[arg.constant_value.value for arg in operands]))
                info = _DBaseExpressionInfo(kind="string", constant_value=constant,
                    dynamic=any(arg.dynamic for arg in operands))
                expression_info[expression] = info
                return info
            if expression.name == "!":
                operand = self.analyze_expression(expression.arguments[0], symbols=symbols,
                    expression_info=expression_info, call_bindings=call_bindings)
                if operand.kind not in {"string", "char"}:
                    raise DBaseCompilerError("!(...) erwartet einen String.",
                        line=expression.line, column=expression.column, filename=self.filename)
                from .string_upper import upper_string
                constant = None if operand.constant_value is None else DBaseValue(
                    "string", upper_string(str(operand.constant_value.value)))
                info = _DBaseExpressionInfo(kind="string", constant_value=constant,
                                            dynamic=operand.dynamic)
                expression_info[expression] = info
                return info
            # INT(<numeric>) ist ein eingebauter dBase-Ausdruck. Er entfernt
            # den Nachkommateil (Abrunden Richtung 0), liefert aber weiterhin
            # einen numerischen dBase-Wert. Beispiele: INT(101.42)=101 und
            # INT(-101.42)=-101.
            if expression.name.casefold() == "int":
                if len(expression.arguments) != 1:
                    raise DBaseCompilerError(
                        "INT(...) erwartet genau einen numerischen Ausdruck.",
                        line=expression.line,
                        column=expression.column,
                        filename=self.filename,
                    )
                operand = self.analyze_expression(
                    expression.arguments[0],
                    symbols=symbols,
                    expression_info=expression_info,
                    call_bindings=call_bindings,
                )
                if operand.kind != "number":
                    raise DBaseCompilerError(
                        "INT(...) erwartet einen numerischen Wert.",
                        line=expression.arguments[0].line,
                        column=expression.arguments[0].column,
                        filename=self.filename,
                    )
                constant = None
                if operand.constant_value is not None:
                    number = Decimal(operand.constant_value.value)
                    constant = DBaseValue(
                        "number",
                        number.to_integral_value(rounding=ROUND_DOWN),
                    )
                info = _DBaseExpressionInfo(
                    kind="number",
                    constant_value=constant,
                    dynamic=operand.dynamic,
                )
                expression_info[expression] = info
                return info

            argument_info = tuple(
                self.analyze_expression(
                    argument,
                    symbols=symbols,
                    expression_info=expression_info,
                    call_bindings=call_bindings,
                )
                for argument in expression.arguments
            )
            ffi = self.ffi_prototypes.get(expression.name.casefold())
            if ffi is not None:
                if len(expression.arguments) != len(ffi.argument_types):
                    raise DBaseCompilerError(
                        f"DLL-Funktion {ffi.name} erwartet {len(ffi.argument_types)} Parameter, erhalten: {len(expression.arguments)}.",
                        line=expression.line, column=expression.column, filename=self.filename)
                from .ffi_types import ffi_type_info
                for parameter_type, actual in zip(ffi.argument_types, argument_info):
                    typ = ffi_type_info(parameter_type)
                    if typ.is_string_input:
                        null_pointer = (actual.kind == 'number' and actual.constant_value is not None
                                        and Decimal(actual.constant_value.value) == 0)
                        if typ.category == 'wide_string' and actual.kind in {'string', 'char'} and actual.constant_value is None:
                            raise DBaseCompilerError(
                                f"DLL-Funktion {ffi.name}: {parameter_type} braucht ein UTF-16-Literal "
                                "oder NULL (0); dynamische Texte benoetigen einen UTF-16-Puffer.",
                                line=expression.line, column=expression.column, filename=self.filename)
                        if actual.kind not in {'string', 'char'} and not null_pointer:
                            raise DBaseCompilerError(
                                f"DLL-Funktion {ffi.name}: {parameter_type} erwartet Text oder NULL (0).",
                                line=expression.line, column=expression.column, filename=self.filename)
                    elif actual.kind not in {'number', 'logical'}:
                        raise DBaseCompilerError(
                            f"DLL-Funktion {ffi.name}: {parameter_type} erwartet eine Zahl oder "
                            "native Speicheradresse (kein dBASE-String).",
                            line=expression.line, column=expression.column, filename=self.filename)
                if ffi.return_type == 'CVOID' and require_value:
                    raise DBaseCompilerError(
                        f"DLL-Funktion {ffi.name} liefert CVOID und kann nicht als Wert verwendet werden.",
                        line=expression.line, column=expression.column, filename=self.filename)
                slots = self._new_call_slots(len(expression.arguments))
                ffi_result_kind = ('void' if ffi.return_type == 'CVOID' else
                                   'string' if ffi_type_info(ffi.return_type).is_ansi_string_result
                                   else 'number')
                ffi_result = ''
                if ffi_result_kind == 'string':
                    ffi_result = f'__dbase_call_{self.call_counter}_ffi_result'
                    self.storage_slots.append(ffi_result)
                call_bindings[expression] = _DBaseCallBinding(
                    kind='ffi', target_label=ffi.label, result_label=ffi_result,
                    argument_slots=slots, parameter_slots=(), return_kind=ffi_result_kind)
                info = _DBaseExpressionInfo(ffi_result_kind, None, True)
                expression_info[expression] = info
                return info
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
            if (operand.kind not in {"number", "logical"} if expression.operator == ".not."
                    else operand.kind != "number"):
                raise DBaseCompilerError(
                    f"Unaerer Operator '{expression.operator}' erwartet eine Zahl.",
                    line=expression.line,
                    column=expression.column,
                    filename=self.filename,
                )
            constant = None
            if operand.constant_value is not None:
                value = Decimal(int(operand.constant_value.value)) if operand.kind == "logical" else Decimal(operand.constant_value.value)
                kind = "logical" if expression.operator == ".not." and operand.kind == "logical" else "number"
                result = (Decimal(0 if value else 1) if expression.operator == ".not."
                          else value if expression.operator == "+" else -value)
                constant = DBaseValue(kind, bool(result) if kind == "logical" else result)
            info = _DBaseExpressionInfo(
                "logical" if expression.operator == ".not." and operand.kind == "logical" else "number",
                constant, operand.dynamic)

        elif isinstance(expression, DBaseCondition):
            left = self.analyze_expression(expression.left, symbols=symbols,
                                           expression_info=expression_info, call_bindings=call_bindings)
            right = self.analyze_expression(expression.right, symbols=symbols,
                                            expression_info=expression_info, call_bindings=call_bindings)
            if not ((left.kind == right.kind and left.kind in {"number", "logical", "date"}) or
                    (left.kind in _STRING_KINDS and right.kind in _STRING_KINDS)):
                raise DBaseCompilerError(
                    "IF-Vergleich erwartet zwei numerische Werte oder zwei Textwerte (String/Char).",
                    line=expression.line, column=expression.column, filename=self.filename,
                )
            constant = None
            if left.constant_value is not None and right.constant_value is not None:
                truth = _compare_dbase_values(left.constant_value, right.constant_value,
                     expression.operator, line=expression.line, column=expression.column,
                     filename=self.filename)
                constant = DBaseValue("number", Decimal(int(truth)))
            info = _DBaseExpressionInfo("number", constant, left.dynamic or right.dynamic)

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
            if operator in {".and.", ".or.", ".xor."}:
                if left.kind not in {"number", "logical"} or right.kind not in {"number", "logical"}:
                    raise DBaseCompilerError(
                        f"Logischer Operator '{operator}' erwartet zwei numerische/Boolesche Werte.",
                        line=expression.line, column=expression.column, filename=self.filename)
                constant = None
                if left.constant_value is not None and right.constant_value is not None:
                    a = bool(left.constant_value.value)
                    b = bool(right.constant_value.value)
                    result = ((a and b) if operator == ".and."
                              else (a or b) if operator == ".or." else a != b)
                    result_kind = "logical" if left.kind == right.kind == "logical" else "number"
                    constant = DBaseValue(result_kind, result if result_kind == "logical" else Decimal(int(result)))
                elif left.constant_value is not None:
                    # Preserve short-circuit constant information.
                    a = bool(left.constant_value.value)
                    if (operator == ".and." and not a) or (operator == ".or." and a):
                        result_kind = "logical" if left.kind == right.kind == "logical" else "number"
                        constant = DBaseValue(result_kind, a if result_kind == "logical" else Decimal(int(a)))
                info = _DBaseExpressionInfo(
                    "logical" if left.kind == right.kind == "logical" else "number",
                    constant, left.dynamic or right.dynamic)
            elif operator == "+" and (left.kind in _STRING_KINDS or right.kind in _STRING_KINDS):
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
        self, condition: DBaseExpression, *, symbols: Mapping[str, _DBaseSymbolState],
        expression_info: Dict[DBaseExpression, _DBaseExpressionInfo],
        call_bindings: Dict[DBaseCallExpression, _DBaseCallBinding],
    ) -> Optional[bool]:
        info = self.analyze_expression(condition, symbols=symbols,
             expression_info=expression_info, call_bindings=call_bindings)
        if info.kind not in {"number", "logical"}:
            raise DBaseCompilerError(
                "IF/ELSEIF erwartet einen booleschen oder numerischen Ausdruck.",
                line=condition.line, column=condition.column, filename=self.filename)
        if info.constant_value is None:
            return None
        return (bool(info.constant_value.value) if info.kind == "logical"
                else bool(Decimal(info.constant_value.value)))


    def _analyze_exitprocess(self, statement: DBaseCallStatement, *,
                             symbols, expression_info, call_bindings) -> bool:
        if statement.call.name.casefold() != "exitprocess":
            return False
        args = statement.call.arguments
        if len(args) != 1:
            raise DBaseCompilerError(
                "ExitProcess erwartet genau einen numerischen Exit-Code.",
                statement.line, statement.column, self.filename)
        info = self.analyze_expression(args[0], symbols=symbols,
                                       expression_info=expression_info,
                                       call_bindings=call_bindings)
        if info.kind != "number":
            raise DBaseCompilerError("ExitProcess erwartet eine Zahl.",
                                     statement.line, statement.column, self.filename)
        return True

    def _analyze_win32_check_file(self, statement: DBaseCallStatement, *, symbols,
                                  expression_info, call_bindings) -> bool:
        if statement.call.name.casefold() != "win32checkfile":
            return False
        arguments = statement.call.arguments
        if len(arguments) != 1:
            raise DBaseCompilerError("Win32CheckFile erwartet genau einen VFS-Dateipfad.",
                                     statement.line, statement.column, self.filename)
        info = self.analyze_expression(arguments[0], symbols=symbols,
                                       expression_info=expression_info,
                                       call_bindings=call_bindings)
        if info.kind not in _STRING_KINDS:
            raise DBaseCompilerError("Win32CheckFile erwartet einen Textpfad.",
                                     statement.line, statement.column, self.filename)
        return True

    def _analyze_win32_raise(self, statement: DBaseCallStatement, *, symbols,
                             expression_info, call_bindings) -> bool:
        key = statement.call.name.casefold()
        if key not in _WIN32_RAISE_BUILTINS:
            return False
        arguments = statement.call.arguments
        if len(arguments) != 1:
            raise DBaseCompilerError(
                f"{statement.call.name} erwartet genau einen Win32-Fehlercode.",
                statement.line, statement.column, self.filename)
        info = self.analyze_expression(arguments[0], symbols=symbols,
                                       expression_info=expression_info,
                                       call_bindings=call_bindings)
        if info.kind != "number":
            raise DBaseCompilerError(
                f"{statement.call.name} erwartet einen numerischen Fehlercode.",
                statement.line, statement.column, self.filename)
        return True

    def _analyze_throw(self, statement: DBaseThrowStatement, *, symbols,
                       expression_info, call_bindings) -> None:
        if statement.variable or not statement.class_name:
            name = statement.variable.casefold() if statement.variable else ""
            if not self._catch_bindings or (name and not any(
                    name in context for context in reversed(self._catch_bindings))):
                raise DBaseCompilerError("THROW erwartet eine sichtbare CATCH-Variable.",
                                         statement.line, statement.column, self.filename)
            return
        if statement.class_name.casefold() not in self.exception_types:
            raise DBaseCompilerError(
                f"'{statement.class_name}' ist keine bekannte Exception-Klasse.",
                statement.line, statement.column, self.filename)
        if statement.message is not None:
            info = self.analyze_expression(
                statement.message, symbols=symbols,
                expression_info=expression_info, call_bindings=call_bindings)
            if info.kind not in _STRING_KINDS:
                raise DBaseCompilerError("THROW erwartet eine Textmeldung.",
                                         statement.line, statement.column, self.filename)

    def _analyze_catch(self, clause: DBaseCatchClause, body_callback, symbols):
        key = clause.class_name.casefold()
        if key not in self.exception_types:
            raise DBaseCompilerError(
                f"CATCH-Klasse '{clause.class_name}' ist keine Exception-Unterklasse.",
                clause.line, clause.column, self.filename)
        prefix = _dbase_catch_prefix(clause)
        self.storage_slots.extend((prefix + "_message", prefix + "_class", prefix + "_id",
                                   prefix + "_object", prefix + "_code"))
        additions = {}
        for prop, slot in (("message", "message"), ("error", "message"),
                           ("classname", "class"), ("code", "code")):
            name = clause.variable + "." + prop
            additions[name.casefold()] = _DBaseSymbolState(
                name, prefix + "_" + slot,
                "number" if prop == "code" else "string", None, True,
                clause.line, clause.column)
        prior = {name: symbols.get(name) for name in additions}
        symbols.update(additions)
        self._catch_bindings.append({clause.variable.casefold(): prefix})
        try:
            body_callback()
        finally:
            self._catch_bindings.pop()
            for name, old in prior.items():
                if old is None:
                    symbols.pop(name, None)
                else:
                    symbols[name] = old

    def _validate_catch_order(self, catches):
        def is_subclass(child: str, ancestor: str):
            current = child.casefold()
            while current in self.exception_types:
                if current == ancestor.casefold():
                    return True
                current = self.exception_types[current][1].casefold()
            return False
        for i, clause in enumerate(catches):
            for earlier in catches[:i]:
                if is_subclass(clause.class_name, earlier.class_name):
                    raise DBaseCompilerError(
                        f"CATCH ({clause.class_name}) wird bereits durch "
                        f"CATCH ({earlier.class_name}) abgefangen.",
                        clause.line, clause.column, self.filename)

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
            if isinstance(statement, DBaseSayStatement):
                symbols = self._merged_symbols(self.global_symbols, local_symbols)
                info = self.analyze_expression(
                    statement.expression, symbols=symbols,
                    expression_info=instance.expression_info,
                    call_bindings=instance.call_bindings,
                )
                if info.kind not in {"string", "char"}:
                    raise DBaseCompilerError(
                        "SAY erwartet einen String oder Char.",
                        line=statement.line, column=statement.column, filename=self.filename,
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
                if self._analyze_win32_check_file(
                        statement, symbols=symbols,
                        expression_info=instance.expression_info,
                        call_bindings=instance.call_bindings):
                    continue
                if self._analyze_win32_raise(
                        statement, symbols=symbols,
                        expression_info=instance.expression_info,
                        call_bindings=instance.call_bindings):
                    continue
                if self._analyze_exitprocess(
                        statement, symbols=symbols,
                        expression_info=instance.expression_info,
                        call_bindings=instance.call_bindings):
                    continue
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
            if isinstance(statement, DBaseThrowStatement):
                symbols = self._merged_symbols(self.global_symbols, local_symbols)
                self._analyze_throw(statement, symbols=symbols,
                                    expression_info=instance.expression_info,
                                    call_bindings=instance.call_bindings)
                continue
            if isinstance(statement, DBaseTryStatement):
                self._validate_catch_order(statement.catches)
                self._analyze_routine_sequence(
                    statement.try_body, definition=definition,
                    instance=instance, local_symbols=local_symbols)
                for clause in statement.catches:
                    self._analyze_catch(clause, lambda clause=clause: self._analyze_routine_sequence(
                        clause.body, definition=definition, instance=instance,
                        local_symbols=local_symbols), local_symbols)
                self._analyze_routine_sequence(
                    statement.finally_body, definition=definition,
                    instance=instance, local_symbols=local_symbols)
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
            if isinstance(statement, DBaseSetBackgroundStatement):
                symbols = self._merged_symbols(self.global_symbols, local_symbols)
                for index, expression in enumerate(statement.arguments):
                    info = self.analyze_expression(
                        expression, symbols=symbols,
                        expression_info=instance.expression_info,
                        call_bindings=instance.call_bindings,
                    )
                    self._validate_background_argument(info, expression, index, len(statement.arguments))
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
            if isinstance(statement, (DBaseSetFormatStatement, DBaseSetDebugStatement, DBaseSetColorStatement, DBaseSetSpeechStatement)):
                continue
            if isinstance(statement, DBaseRoutineDefinition):
                continue
            raise AssertionError(type(statement))

    def _validate_background_argument(self, info, expression, index, count):
        if info.kind != "number":
            raise DBaseCompilerError(
                "SET BACKGROUND TO erwartet numerische Werte fuer Farben und Zeichen.",
                line=expression.line, column=expression.column, filename=self.filename,
            )
        maximum = 255 if count == 1 or index == 2 else 15
        if info.constant_value is not None:
            value = Decimal(info.constant_value.value)
            if not value.is_finite() or value != value.to_integral_value() or not 0 <= value <= maximum:
                raise DBaseCompilerError(
                    f"SET BACKGROUND TO: Parameter {index + 1} muss eine ganze Zahl von 0 bis {maximum} sein.",
                    line=expression.line, column=expression.column, filename=self.filename,
                )

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
            if isinstance(statement, DBaseSayStatement):
                info = self.analyze_expression(
                    statement.expression, symbols=globals_work,
                    expression_info=self.expression_info, call_bindings=self.call_bindings,
                )
                if info.kind not in {"string", "char"}:
                    raise DBaseCompilerError(
                        "SAY erwartet einen String oder Char.",
                        line=statement.line, column=statement.column, filename=self.filename,
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
                if self._analyze_win32_check_file(
                        statement, symbols=globals_work,
                        expression_info=self.expression_info,
                        call_bindings=self.call_bindings):
                    continue
                if self._analyze_win32_raise(
                        statement, symbols=globals_work,
                        expression_info=self.expression_info,
                        call_bindings=self.call_bindings):
                    continue
                if self._analyze_exitprocess(
                        statement, symbols=globals_work,
                        expression_info=self.expression_info,
                        call_bindings=self.call_bindings):
                    continue
                self.analyze_expression(
                    statement.call,
                    symbols=globals_work,
                    expression_info=self.expression_info,
                    call_bindings=self.call_bindings,
                    require_value=False,
                )
                continue
            if isinstance(statement, DBaseThrowStatement):
                self._analyze_throw(statement, symbols=globals_work,
                                    expression_info=self.expression_info,
                                    call_bindings=self.call_bindings)
                continue
            if isinstance(statement, DBaseTryStatement):
                self._validate_catch_order(statement.catches)
                self._analyze_top_sequence(statement.try_body, globals_work)
                for clause in statement.catches:
                    self._analyze_catch(clause, lambda clause=clause: self._analyze_top_sequence(
                        clause.body, globals_work), globals_work)
                self._analyze_top_sequence(statement.finally_body, globals_work)
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
            if isinstance(statement, DBaseSetBackgroundStatement):
                for index, expression in enumerate(statement.arguments):
                    info = self.analyze_expression(
                        expression, symbols=globals_work,
                        expression_info=self.expression_info, call_bindings=self.call_bindings,
                    )
                    self._validate_background_argument(info, expression, index, len(statement.arguments))
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
            if isinstance(statement, (DBaseSetFormatStatement, DBaseSetDebugStatement, DBaseSetColorStatement, DBaseSetSpeechStatement)):
                continue
            raise AssertionError(type(statement))

    def _condition_constant(self, condition: DBaseExpression) -> Optional[bool]:
        info = self.expression_info.get(condition)
        if info is None or info.constant_value is None:
            return None
        return (bool(info.constant_value.value) if info.kind == "logical"
                else bool(Decimal(info.constant_value.value)))


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
            if isinstance(statement, DBaseSetSpeechStatement):
                continue
            if isinstance(statement, DBaseSayStatement):
                # Audio wird erst zur Laufzeit erzeugt, nicht im Text-Transcript.
                continue
            if isinstance(statement, DBaseSetColorStatement):
                continue
            if isinstance(statement, DBaseClearScreenStatement):
                # CLEAR SCREEN betrifft nur die Konsolen-Textkomponente. Auch
                # die Compile-Vorschau bildet deshalb den danach sichtbaren
                # Konsoleninhalt ab.
                console_chunks.clear()
                continue
            if isinstance(statement, DBaseSetBackgroundStatement):
                # Fills the visible terminal area; the compile transcript is
                # not a snapshot of GUI geometry and intentionally ignores it.
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
            if isinstance(statement, DBaseThrowStatement):
                complete = False
                continue
            if isinstance(statement, DBaseTryStatement):
                # A dynamic THROW/CATCH path cannot be predicted in the
                # compile-time transcript. FINALLY is shown for fallthrough.
                may_throw = any(isinstance(item, (DBaseThrowStatement, DBaseCallStatement))
                                for item in statement.try_body)
                if may_throw:
                    complete = False
                format_target, debug_override, inner_complete, inner_debug = self._preview_top_sequence(
                    statement.try_body, format_target=format_target,
                    debug_override=debug_override, console_chunks=console_chunks,
                    debug_chunks=debug_chunks)
                complete = complete and inner_complete
                uses_debug = uses_debug or inner_debug
                format_target, debug_override, inner_complete, inner_debug = self._preview_top_sequence(
                    statement.finally_body, format_target=format_target,
                    debug_override=debug_override, console_chunks=console_chunks,
                    debug_chunks=debug_chunks)
                complete = complete and inner_complete
                uses_debug = uses_debug or inner_debug
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
        # Stage 619: Wie Pascal WriteLn beginnt ?/?? im DEBUG-Kanal.
        # SET FORMAT TO CONSOLE und SET DEBUG OFF bleiben explizite Opt-outs.
        _, _, transcript_complete, uses_debug_output = self._preview_top_sequence(
            self.statements,
            format_target="screen",
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
    ffi_prototypes=(),
) -> _DBaseAnalysis:
    return _DBaseProgramAnalyzer(statements, filename=filename, ffi_prototypes=ffi_prototypes).run()

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
        if expression.name.casefold() in {"type", "vartype"}:
            function = expression.name.upper()
            if len(expression.arguments) != 1:
                raise DBaseCompilerError(
                    f"{function}(...) erwartet genau einen Parameter.",
                    line=expression.line, column=expression.column, filename=filename)
            arg = expression.arguments[0]
            if expression.name.casefold() == "type":
                name = _dbase_type_query_name(arg)
                if name is None:
                    raise DBaseCompilerError(
                        'TYPE(...) erwartet einen Variablennamen als String.',
                        line=arg.line, column=arg.column, filename=filename)
                value = env.get(name)
                return DBaseValue("string", _dbase_type_letter(value.kind) if value else "U")
            if isinstance(arg, DBaseIdentifierExpression) and arg.name.casefold() not in env:
                return DBaseValue("string", "U")
            value = _evaluate_dbase_expression(
                arg, filename=filename, variables=env, call_resolver=call_resolver)
            return DBaseValue("string", _dbase_type_letter(value.kind))
        if expression.name.casefold() in {"len", "ltrim", "rtrim", "trim"}:
            name = expression.name.casefold()
            if len(expression.arguments) != 1:
                raise DBaseCompilerError(
                    f"{name.upper()}(...) erwartet genau einen String-Ausdruck.",
                    line=expression.line, column=expression.column, filename=filename,
                )
            operand = _evaluate_dbase_expression(
                expression.arguments[0], filename=filename,
                variables=env, call_resolver=call_resolver,
            )
            if operand.kind not in _STRING_KINDS:
                raise DBaseCompilerError(
                    f"{name.upper()}(...) erwartet einen String/Char.",
                    line=expression.line, column=expression.column, filename=filename,
                )
            from .string_length_trim import string_length, trim_string
            text = str(operand.value)
            return (DBaseValue("number", string_length(text)) if name == "len"
                    else DBaseValue("string", trim_string(name, text)))
        if expression.name.casefold() in {"isupper", "islower"}:
            function = expression.name.upper()
            if len(expression.arguments) != 1:
                raise DBaseCompilerError(
                    f"{function}(...) erwartet genau ein Zeichen.",
                    line=expression.line, column=expression.column, filename=filename,
                )
            operand = _evaluate_dbase_expression(
                expression.arguments[0], filename=filename,
                variables=env, call_resolver=call_resolver,
            )
            if operand.kind not in _STRING_KINDS:
                raise DBaseCompilerError(
                    f"{function}(...) erwartet ein Zeichen (Char/String), keinen numerischen Wert.",
                    line=expression.line, column=expression.column, filename=filename,
                )
            from .char_case import is_char_case
            return DBaseValue("number", Decimal(int(is_char_case(
                str(operand.value), upper=(expression.name.casefold() == "isupper")
            ))))
        if expression.name.casefold() == "ismouse":
            if expression.arguments:
                raise DBaseCompilerError("ISMOUSE() erwartet keine Parameter.",
                    line=expression.line, column=expression.column, filename=filename)
            # Zur Laufzeit abfragen: die Python-/Kompilationsvorschau darf
            # niemals den Mausstatus des Build-Rechners einfrieren.
            raise DBaseCompilerError(
                "ISMOUSE() wird erst in der erzeugten Windows-EXE ausgewertet.",
                line=expression.line, column=expression.column, filename=filename)
        if expression.name.casefold() == "iskeyboard":
            if expression.arguments:
                raise DBaseCompilerError("ISKEYBOARD() erwartet keine Parameter.",
                    line=expression.line, column=expression.column, filename=filename)
            raise DBaseCompilerError(
                "ISKEYBOARD() wird erst in der erzeugten Windows-EXE ausgewertet.",
                line=expression.line, column=expression.column, filename=filename)
        if expression.name == "$":
            operands = [_evaluate_dbase_expression(arg, filename=filename,
                variables=env, call_resolver=call_resolver) for arg in expression.arguments]
            if operands[0].kind not in {"string", "char"} or any(
                    arg.kind != "number" for arg in operands[1:]):
                raise DBaseCompilerError("$(...) erwartet einen String und numerische Position/Laenge.",
                    line=expression.line, column=expression.column, filename=filename)
            from .string_substring import substring
            return DBaseValue("string", substring(*[arg.value for arg in operands]))
        if expression.name == "!":
            operand = _evaluate_dbase_expression(expression.arguments[0], filename=filename,
                variables=env, call_resolver=call_resolver)
            if operand.kind not in {"string", "char"}:
                raise DBaseCompilerError("!(...) erwartet einen String.",
                    line=expression.line, column=expression.column, filename=filename)
            from .string_upper import upper_string
            return DBaseValue("string", upper_string(str(operand.value)))
        if expression.name.casefold() == "int":
            if len(expression.arguments) != 1:
                raise DBaseCompilerError(
                    "INT(...) erwartet genau einen numerischen Ausdruck.",
                    line=expression.line,
                    column=expression.column,
                    filename=filename,
                )
            operand = _evaluate_dbase_expression(
                expression.arguments[0],
                filename=filename,
                variables=env,
                call_resolver=call_resolver,
            )
            if operand.kind != "number":
                raise DBaseCompilerError(
                    "INT(...) erwartet einen numerischen Wert.",
                    line=expression.arguments[0].line,
                    column=expression.arguments[0].column,
                    filename=filename,
                )
            return DBaseValue(
                "number",
                Decimal(operand.value).to_integral_value(rounding=ROUND_DOWN),
            )
        if call_resolver is not None:
            return call_resolver(expression, env)
        raise DBaseCompilerError(
            f"Funktionsaufruf '{expression.name}(...)' ist ein Laufzeitwert und kann "
            "ohne Member-Kontext nicht ausgewertet werden.",
            line=expression.line,
            column=expression.column,
            filename=filename,
        )
    if isinstance(expression, DBaseCondition):
        left = _evaluate_dbase_expression(expression.left, filename=filename,
                        variables=env, call_resolver=call_resolver)
        right = _evaluate_dbase_expression(expression.right, filename=filename,
                        variables=env, call_resolver=call_resolver)
        return DBaseValue("number", Decimal(int(_compare_dbase_values(left, right,
               expression.operator, line=expression.line, column=expression.column,
               filename=filename))))
    if isinstance(expression, DBaseUnaryExpression):
        operand = _evaluate_dbase_expression(
            expression.operand, filename=filename, variables=env, call_resolver=call_resolver
        )
        if (operand.kind not in {"number", "logical"} if expression.operator == ".not."
                else operand.kind != "number"):
            raise DBaseCompilerError(
                f"Unaerer Operator '{expression.operator}' erwartet eine Zahl.",
                line=expression.line,
                column=expression.column,
                filename=filename,
            )
        value = Decimal(int(operand.value)) if operand.kind == "logical" else Decimal(operand.value)
        kind = "logical" if expression.operator == ".not." and operand.kind == "logical" else "number"
        result = (Decimal(int(not bool(value))) if expression.operator == ".not."
                  else value if expression.operator == "+" else -value)
        return DBaseValue(kind, bool(result) if kind == "logical" else result)
    if isinstance(expression, DBaseBinaryExpression):
        if expression.operator in {".and.", ".or.", ".xor."}:
            left = _evaluate_dbase_expression(expression.left, filename=filename,
                       variables=env, call_resolver=call_resolver)
            if left.kind not in {"number", "logical"}:
                raise DBaseCompilerError("Logischer Operator erwartet eine Zahl.",
                       line=expression.line, column=expression.column, filename=filename)
            a = bool(left.value)
            result_kind = "logical" if left.kind == "logical" else "number"
            if (expression.operator == ".and." and not a) or (expression.operator == ".or." and a):
                return DBaseValue(result_kind, a if result_kind == "logical" else Decimal(int(a)))
            right = _evaluate_dbase_expression(expression.right, filename=filename,
                        variables=env, call_resolver=call_resolver)
            if right.kind not in {"number", "logical"}:
                raise DBaseCompilerError("Logischer Operator erwartet eine Zahl.",
                       line=expression.line, column=expression.column, filename=filename)
            b = bool(right.value)
            result_kind = "logical" if left.kind == right.kind == "logical" else "number"
            result = (a != b if expression.operator == ".xor."
                      else a and b if expression.operator == ".and." else a or b)
            return DBaseValue(result_kind, result if result_kind == "logical" else Decimal(int(result)))
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


@dataclass
class _DBaseExceptionObject:
    """Preview counterpart of a native JitVmt Exception instance."""
    class_name: str
    properties: Dict[str, object]

    @property
    def message(self) -> str:
        return self.properties.get("message", "Error.")


class _DBaseRaisedException(Exception):
    def __init__(self, class_name: str, message: str,
                 obj: Optional[_DBaseExceptionObject] = None) -> None:
        self.obj = obj if obj is not None else _DBaseExceptionObject(
            class_name, {"message": message})
        self.class_name = self.obj.class_name
        super().__init__(f"{class_name}: {message}")

    @property
    def message(self) -> str:
        return self.obj.message


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
        self.exception_types = _dbase_exception_hierarchy(statements)
        self.exception_class_definitions = {
            item.name.casefold(): item
            for item in statements if isinstance(item, DBaseClassDefinition)
        }
        self._caught_exceptions: list[tuple[str, _DBaseRaisedException]] = []

    def _new_exception_object(self, class_name: str, message: str) -> _DBaseExceptionObject:
        """Interpret native Message defaults and its __ini__ body in preview.

        This is an interpreter for the existing string-property subset, not a
        replacement for the compiled native TObject constructor.
        """
        key = class_name.casefold()
        lineage = []
        seen = set()
        while key in self.exception_types and key not in seen:
            seen.add(key)
            definition = self.exception_class_definitions.get(key)
            if definition is not None:
                lineage.append(definition)
            key = self.exception_types[key][1].casefold()
        fields = {"message": "Error.", "code": 0}
        from .derived_class_abi import property_default
        for definition in reversed(lineage):
            for prop in definition.properties:
                kind, value = property_default(prop)
                if kind == "string":
                    fields[prop.name.casefold()] = str(value)
        obj = _DBaseExceptionObject(class_name, fields)
        ctor = None
        for definition in lineage:
            ctor = next((m for m in definition.methods
                         if m.name.casefold() == "__ini__"), None)
            if ctor is not None:
                break
        if ctor is None:
            obj.properties["message"] = message
            return obj
        env = {"message": DBaseValue("string", obj.message)}
        if ctor.parameters:
            env[ctor.parameters[0].casefold()] = DBaseValue("string", message)
        for lineno, raw in ctor.body:
            action = raw.strip()
            if not re.match(r"^message\s*=", action, re.I):
                continue
            rhs = action.split("=", 1)[1].strip()
            tokens = _tokenize_dbase_statement(
                rhs, filename=self.filename,
                base_offset=0, source=rhs)
            parser = _DBaseExpressionParser(tokens, filename=self.filename)
            expression = parser.parse_expression()
            parser._expect_eof()
            result = _evaluate_dbase_expression(expression, filename=self.filename,
                                                variables=env)
            env["message"] = DBaseValue("string", str(result.value))
        obj.properties["message"] = str(env["message"].value)
        return obj

    def _eval_expr(self, expression: DBaseExpression, scope: Mapping[str, DBaseValue]) -> DBaseValue:
        merged = dict(self.globals)
        merged.update(scope)
        return _evaluate_dbase_expression(
            expression,
            filename=self.filename,
            variables=merged,
            call_resolver=self._resolve_call,
        )

    def _eval_condition(self, condition: DBaseExpression, scope: Mapping[str, DBaseValue]) -> bool:
        value = self._eval_expr(condition, scope)
        return bool(Decimal(value.value))


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
                if "." in statement.name:
                    variable, member = statement.name.casefold().split(".", 1)
                    active = next((error for name, error in reversed(self._caught_exceptions)
                                   if name == variable), None)
                    if active is not None:
                        if member not in {"message", "error"}:
                            raise DBaseCompilerError(
                                "Exception-Property ist schreibgeschuetzt: " + member,
                                statement.line, statement.column, self.filename)
                        if value.kind not in _STRING_KINDS:
                            raise DBaseCompilerError("Exception.Message erwartet Text.",
                                                     statement.line, statement.column, self.filename)
                        active.obj.properties["message"] = str(value.value)
                        scope[variable + ".message"] = DBaseValue("string", active.message)
                        scope[variable + ".error"] = DBaseValue("string", active.message)
                        continue
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
                if statement.call.name.casefold() == "win32checkfile":
                    # The app VFS is private to the actual Windows process.
                    # Never probe the compiler host filesystem in preview.
                    raise DBaseCompilerError(
                        "Win32CheckFile kann nur in der Windows-EXE ausgefuehrt werden.",
                        statement.line, statement.column, self.filename)
                native_key = _WIN32_RAISE_BUILTINS.get(statement.call.name.casefold())
                if native_key is not None:
                    from .win32_errors import win32_message
                    code_value = self._eval_expr(statement.call.arguments[0], scope)
                    code = int(code_value.value)
                    if code != 0:
                        cls = self.exception_types[native_key][0]
                        obj = self._new_exception_object(cls, win32_message(code))
                        obj.properties["code"] = code
                        raise _DBaseRaisedException(cls, obj.message, obj)
                    continue
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
            if isinstance(statement, DBaseThrowStatement):
                if statement.variable or not statement.class_name:
                    name = statement.variable.casefold() if statement.variable else ""
                    caught = next((error for label, error in reversed(self._caught_exceptions)
                                   if not name or name == label), None)
                    if caught is None:
                        raise DBaseCompilerError("THROW ohne passende CATCH-Variable.",
                                                 statement.line, statement.column, self.filename)
                    raise caught
                message = ("Error." if statement.message is None else
                           str(self._eval_expr(statement.message, scope).value))
                obj = self._new_exception_object(statement.class_name, message)
                raise _DBaseRaisedException(statement.class_name, obj.message, obj)
            if isinstance(statement, DBaseTryStatement):
                pending = None
                try:
                    try:
                        self._execute_sequence(statement.try_body, scope, in_routine=in_routine)
                    except _DBaseRaisedException as error:
                        def inherits(name, base):
                            current = name.casefold()
                            while current in self.exception_types:
                                if current == base.casefold():
                                    return True
                                current = self.exception_types[current][1].casefold()
                            return False
                        for clause in statement.catches:
                            if inherits(error.class_name, clause.class_name):
                                variable = clause.variable.casefold()
                                properties = {variable + ".message": DBaseValue("string", error.message),
                                              variable + ".error": DBaseValue("string", error.message),
                                              variable + ".classname": DBaseValue("string", error.class_name),
                                              variable + ".code": DBaseValue("number", Decimal(error.obj.properties.get("code", 0)))}
                                previous = {name: scope.get(name) for name in properties}
                                scope.update(properties)
                                self._caught_exceptions.append((variable, error))
                                try:
                                    self._execute_sequence(clause.body, scope, in_routine=in_routine)
                                finally:
                                    self._caught_exceptions.pop()
                                    for name, old in previous.items():
                                        if old is None:
                                            scope.pop(name, None)
                                        else:
                                            scope[name] = old
                                break
                        else:
                            raise
                finally:
                    self._execute_sequence(statement.finally_body, scope, in_routine=in_routine)
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
            if isinstance(statement, DBaseSetBackgroundStatement):
                continue
            if isinstance(statement, DBaseClearScreenStatement):
                self.output.clear()
                continue
            if isinstance(statement, (DBaseSetFormatStatement, DBaseSetDebugStatement, DBaseSetColorStatement, DBaseSetBorderColorStatement, DBaseSetSpeechStatement, DBaseSayStatement)):
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
        workstation_mode: bool = False,
        debug_theme: str = "default",
        ffi_prototypes=(),
    ) -> None:
        self.ffi_prototypes = {p.name.casefold(): p for p in ffi_prototypes}
        self.statements = statements
        def has_speech(seq):
            return any(isinstance(item, (DBaseSetSpeechStatement, DBaseSayStatement))
                       or isinstance(item, DBaseRoutineDefinition) and has_speech(item.body)
                       or isinstance(item, DBaseIfStatement) and any(has_speech(branch.body) for branch in item.branches)
                       for item in seq)
        self.uses_speech = has_speech(statements)
        self.speech_utf8_literals: Dict[bytes, str] = {}
        self.ffi_string_literals: Dict[bytes, str] = {}
        self.analysis = analysis
        self.target = target
        self.filename = filename
        self.workstation_mode = bool(workstation_mode)
        _debug_theme = str(debug_theme or "default").strip().casefold()
        self.debug_theme = _debug_theme if _debug_theme in {"default", "light", "dark"} else "default"
        self.is64 = target == "pe64"
        self.lines: list[str] = []
        self.data_lines: list[str] = []
        self.string_literals: Dict[bytes, str] = {}
        self.double_literals: Dict[bytes, str] = {}
        self.label_counter = 0
        self.output_target = "console"
        self.current_expression_info: Mapping[DBaseExpression, _DBaseExpressionInfo] = analysis.expression_info
        self.current_call_bindings: Mapping[DBaseCallExpression, _DBaseCallBinding] = analysis.call_bindings
        # Stage 208/209: nur Programme mit !() benoetigen den DLL-Upper-Export.
        self.uses_upper_runtime = any(
            isinstance(expression, DBaseCallExpression) and expression.name == "!"
            for expression in self.current_expression_info
        )
        self.current_instance: Optional[_DBaseRoutineInstance] = None
        self.exception_types = _dbase_exception_hierarchy(statements)
        self._exception_targets: tuple[str, ...] = ()
        self._exception_fallback: str = ""
        self._dbase_finalizers: tuple[tuple[Tuple[object, ...], int], ...] = ()
        self._caught_bindings: list[dict[str, str]] = []
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

    def emit_copy_exception_pair(self, source_message: str, destination_message: str) -> None:
        """Copy adjacent Message/Class value slots (Stage 648).

        _emit_value_slot_data emits each slot as type (4), number (8),
        pointer (4/8), length (4), without padding. The analyzer allocates
        caught Message and Class consecutively; the emitter likewise
        allocates the active exception Message and Class consecutively.
        Thus the two slots form one 40-byte / 48-byte contiguous range.

        REP MOVSD requires DF=0 (guaranteed by the Windows x86/x64 ABI).
        ESI/EDI or RSI/RDI are nonvolatile and must be saved. ECX is volatile.
        No calls happen between the saves and restores.
        """
        addr = "r" if self.is64 else "e"
        count = 12 if self.is64 else 10
        self.emit(f"    push {addr}si")
        self.emit(f"    push {addr}di")
        self.emit(f"    lea {addr}si, [{source_message}_type]")
        self.emit(f"    lea {addr}di, [{destination_message}_type]")
        self.emit(f"    mov ecx, {count}")
        self.emit("    rep movsd")
        self.emit(f"    pop {addr}di")
        self.emit(f"    pop {addr}si")

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
        # A managed THROW in a called dBASE routine travels to its caller.
        # Never execute further statements or consume a stale return value.
        self.emit_exception_check()
        return binding

    def emit_numeric_expression(self, expression: DBaseExpression) -> None:
        info = self.current_expression_info[expression]

        if (isinstance(expression, DBaseCondition) or
            (isinstance(expression, DBaseUnaryExpression) and expression.operator == ".not.") or
            (isinstance(expression, DBaseBinaryExpression) and
             expression.operator in {".and.", ".or.", ".xor."})):
            false_label = self.new_label("logic_false")
            end_label = self.new_label("logic_end")
            self.emit_condition_jump_false(expression, false_label)
            self.emit(f"    fld qword ptr [{self.double_literal(Decimal(1))}]")
            self.emit(f"    jmp {end_label}")
            self.emit(f"{false_label}:")
            self.emit("    fldz")
            self.emit(f"{end_label}:")
            return

        if isinstance(expression, DBaseLiteralExpression):
            number = (Decimal(int(bool(expression.value))) if expression.value_type == "logical"
                      else Decimal(expression.value))
            label = self.double_literal(number)
            self.emit(f"    fld qword ptr [{label}]")
            return

        if isinstance(expression, DBaseIdentifierExpression):
            if info.kind not in {"number", "logical"}:
                raise AssertionError("Nichtnumerische Variable in numerischem Codepfad")
            self.emit(f"    fld qword ptr [{info.variable_label}_num]")
            return

        if isinstance(expression, DBaseCallExpression):
            if expression.name.casefold() == "len":
                if info.constant_value is not None:
                    self.emit(f"    fld qword ptr [{self.double_literal(Decimal(info.constant_value.value))}]")
                else:
                    source = self.new_storage_slot("len_source")
                    self.emit_store_expression_to_slot(expression.arguments[0], source)
                    # Der dBASE-Stringslot speichert seine Byte-Laenge in
                    # CP1252; dort entspricht ein Byte einem Zeichen.
                    self.emit(f"    mov eax, dword ptr [{source}_len]")
                    self.emit("    mov dword ptr [__dbase_temp_number], eax")
                    self.emit("    fild dword ptr [__dbase_temp_number]")
                return
            if expression.name.casefold() in {"isupper", "islower"}:
                # Statische Literale sind bereits bei der Analyse gefaltet.
                # Fuer Variable/FUNCTION werden Ptr und Laenge des Werts
                # zur Laufzeit geprueft und dann das Codepage-Zeichen getestet.
                from .char_case import emit_char_case_check
                if info.constant_value is not None:
                    self.emit(f"    fld qword ptr [{self.double_literal(Decimal(info.constant_value.value))}]")
                else:
                    source = self.new_storage_slot("char_case")
                    self.emit_store_expression_to_slot(expression.arguments[0], source)
                    for instruction in emit_char_case_check(
                        source, is64=self.is64,
                        label_prefix=self.new_label(expression.name.casefold()),
                        upper=(expression.name.casefold() == "isupper"),
                    ):
                        self.emit(instruction)
                return
            if expression.name.casefold() == "iskeyboard":
                from .keyboard_detection import emit_keyboard_probe
                for instruction in emit_keyboard_probe(
                    is64=self.is64,
                    label_prefix=self.new_label("iskeyboard"),
                    has_shadow_space=False,
                ):
                    self.emit(instruction)
                self.emit("    mov dword ptr [__dbase_temp_number], eax")
                self.emit("    fild dword ptr [__dbase_temp_number]")
                return
            if expression.name.casefold() == "ismouse":
                # GetSystemMetrics(SM_MOUSEPRESENT=19) liefert BOOL in EAX.
                # Windows PE32: __stdcall (callee bereinigt den Stack).
                # Windows PE64: Microsoft-x64-ABI mit Shadow Space.
                if self.is64:
                    self.emit("    mov ecx, 19")
                    self.emit("    sub rsp, 40")
                    self.emit("    call GetSystemMetrics")
                    self.emit("    add rsp, 40")
                else:
                    self.emit("    push 19")
                    self.emit("    call GetSystemMetrics")
                self.emit("    test eax, eax")
                self.emit("    setne al")
                self.emit("    movzx eax, al")
                self.emit("    mov dword ptr [__dbase_temp_number], eax")
                self.emit("    fild dword ptr [__dbase_temp_number]")
                return
            if expression.name.casefold() == "int":
                # Operand nach ST0 laden und mit temporaer gesetztem x87-RC
                # (11b = truncate toward zero) runden. Danach den ursprueng-
                # lichen Control-Word-Zustand wiederherstellen. FRNDINT laesst
                # das Ergebnis als Double in ST0, sodass INT nahtlos in allen
                # numerischen Ausdruecken weiterverwendet werden kann.
                self.emit_numeric_expression(expression.arguments[0])
                self.emit("    fnstcw word ptr [__dbase_int_cw]")
                self.emit("    movzx eax, word ptr [__dbase_int_cw]")
                self.emit("    or eax, 3072")
                self.emit("    mov word ptr [__dbase_int_cw_trunc], ax")
                self.emit("    fldcw word ptr [__dbase_int_cw_trunc]")
                self.emit("    frndint")
                self.emit("    fldcw word ptr [__dbase_int_cw]")
                return
            binding = self.emit_user_call(expression)
            if binding.kind == 'ffi':
                self.emit('    fild qword ptr [__dbase_ffi_return]')
            elif binding.kind == "external":
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

    def emit_native_console_write(self, pointer: str, length: str | int, *, pointer_is_memory: bool = False) -> None:
        """Schreibt einen Bytepuffer in das lazy erzeugte Win32-Konsolenfenster.

        ``__dbase_console_write`` ruft beim ersten Zugriff selbst
        ``AllocConsole`` auf. Dadurch erscheint die Konsole erst dann, wenn
        ein ausgefuehrtes ?/??-Statement den CONSOLE-Kanal wirklich benutzt.
        """
        if self.is64:
            if pointer_is_memory:
                self.emit(f"    mov rcx, qword ptr [{pointer}]")
            else:
                self.emit(f"    mov rcx, {pointer}")
            if isinstance(length, int):
                self.emit(f"    mov edx, {int(length)}")
            else:
                self.emit(f"    mov edx, dword ptr [{length}]")
            self.emit_qt_call0("DBaseConsoleWrite")
        else:
            if isinstance(length, int):
                self.emit(f"    push {int(length)}")
            else:
                self.emit(f"    push dword ptr [{length}]")
            if pointer_is_memory:
                self.emit(f"    push dword ptr [{pointer}]")
            else:
                self.emit(f"    push {pointer}")
            self.emit("    call DBaseConsoleWrite")
            self.emit("    add esp, 8")

    def _emit_runtime_output_choice(self, writer) -> None:
        """Decide the ?/?? channel at execution time (shared across routines).

        An explicit SET DEBUG ON/OFF overrides SET FORMAT TO SCREEN/CONSOLE.
        With no override, SET FORMAT determines the channel.  The visibility
        flag prevents every print fragment from re-showing the QDialog.
        """
        override_ready = self.new_label("output_override_ready")
        console_label = self.new_label("output_console")
        show_done = self.new_label("output_show_done")
        end_label = self.new_label("output_done")

        self.emit("    cmp dword ptr [__dbase_output_debug_override], -1")
        self.emit(f"    jne {override_ready}")
        self.emit("    cmp dword ptr [__dbase_output_format_screen], 0")
        self.emit(f"    je {console_label}")
        self.emit(f"    jmp {show_done}")
        self.emit(f"{override_ready}:")
        self.emit("    cmp dword ptr [__dbase_output_debug_override], 0")
        self.emit(f"    je {console_label}")

        self.emit(f"{show_done}:")
        already_visible = self.new_label("output_already_visible")
        self.emit("    cmp dword ptr [__dbase_output_debug_visible], 0")
        self.emit(f"    jne {already_visible}")
        self.emit("    mov dword ptr [__dbase_output_debug_visible], 1")
        self.emit_qt_call1_int("DBaseQtSetDebugVisible", 1)
        self.emit(f"{already_visible}:")
        writer("debug")
        self.emit(f"    jmp {end_label}")
        self.emit(f"{console_label}:")
        writer("console")
        self.emit(f"{end_label}:")

    def emit_write_static(self, label: str, length: int, target: str) -> None:
        if target == "runtime":
            self._emit_runtime_output_choice(
                lambda chosen: self.emit_write_static(label, length, chosen)
            )
            return
        if target == "console":
            # Auch eine leere ??-Ausgabe muss die lazy Console erzeugen.
            self.emit_native_console_write(label, int(length))
            return
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
        if target == "runtime":
            self._emit_runtime_output_choice(
                lambda chosen: self.emit_write_variable_text(var_label, chosen)
            )
            return
        if target == "console":
            self.emit_native_console_write(
                f"{var_label}_ptr", f"{var_label}_len", pointer_is_memory=True
            )
            return
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
        if target == "runtime":
            # Die x87-Zahl wird exakt einmal formatiert, bevor ein eventuell
            # in einer FUNCTION veraenderter Debugzustand ausgewertet wird.
            self.emit("    mov dword ptr [__dbase_console_number_len], edx")
            self._emit_runtime_output_choice(
                lambda chosen: self._emit_runtime_formatted_number(chosen)
            )
            return
        if target == "console":
            # EDX enthaelt nach emit_format_number_from_st0 die Textlaenge.
            # In einen Slot sichern, weil emit_native_console_write eine
            # Speicherquelle fuer dynamische Laengen erwartet.
            self.emit("    mov dword ptr [__dbase_console_number_len], edx")
            self.emit_native_console_write(
                "__dbase_format_buffer",
                "__dbase_console_number_len",
                pointer_is_memory=True,
            )
            return
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

    def _emit_runtime_formatted_number(self, target: str) -> None:
        if target == "console":
            self.emit_native_console_write(
                "__dbase_format_buffer", "__dbase_console_number_len",
                pointer_is_memory=True,
            )
        else:
            if self.is64:
                self.emit("    mov rcx, qword ptr [__dbase_format_buffer]")
                self.emit("    mov edx, dword ptr [__dbase_console_number_len]")
                self.emit("    sub rsp, 40")
                self.emit("    call DBaseQtAppendDebug")
                self.emit("    add rsp, 40")
            else:
                self.emit("    push dword ptr [__dbase_console_number_len]")
                self.emit("    push dword ptr [__dbase_format_buffer]")
                self.emit("    call DBaseQtAppendDebug")
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

    def emit_type_query_to_slot(self, expression: DBaseCallExpression, destination: str) -> None:
        """Produce the current type code, not the inferred/static variable type."""
        info = self.current_expression_info[expression]
        if not info.variable_label:
            letter = str(info.constant_value.value) if info.constant_value is not None else "U"
            self.emit_static_text_to_slot(letter, "string", destination)
            return
        source = info.variable_label
        n_label, _ = self.text_literal("N")
        c_label, _ = self.text_literal("C")
        u_label, _ = self.text_literal("U")
        done = self.new_label("type_done")
        numeric = self.new_label("type_number")
        textual = self.new_label("type_text")
        self.emit(f"    mov eax, dword ptr [{source}_type]")
        self.emit(f"    cmp eax, {_TYPE_NUMBER}")
        self.emit(f"    je {numeric}")
        self.emit(f"    cmp eax, {_TYPE_STRING}")
        self.emit(f"    je {textual}")
        self.emit(f"    cmp eax, {_TYPE_CHAR}")
        self.emit(f"    je {textual}")
        logical = self.new_label("type_logical")
        dated = self.new_label("type_date")
        l_label, _ = self.text_literal("L")
        d_label, _ = self.text_literal("D")
        self.emit(f"    cmp eax, {_TYPE_LOGICAL}")
        self.emit(f"    je {logical}")
        self.emit(f"    cmp eax, {_TYPE_DATE}")
        self.emit(f"    je {dated}")
        self.emit(f"    mov {'rax' if self.is64 else 'eax'}, {u_label}")
        self.emit(f"    jmp {done}")
        self.emit(f"{numeric}:")
        self.emit(f"    mov {'rax' if self.is64 else 'eax'}, {n_label}")
        self.emit(f"    jmp {done}")
        self.emit(f"{textual}:")
        self.emit(f"    mov {'rax' if self.is64 else 'eax'}, {c_label}")
        self.emit(f"    jmp {done}")
        self.emit(f"{logical}:")
        self.emit(f"    mov {'rax' if self.is64 else 'eax'}, {l_label}")
        self.emit(f"    jmp {done}")
        self.emit(f"{dated}:")
        self.emit(f"    mov {'rax' if self.is64 else 'eax'}, {d_label}")
        self.emit(f"{done}:")
        self.emit(f"    mov {'qword' if self.is64 else 'dword'} ptr [{destination}_ptr], {'rax' if self.is64 else 'eax'}")
        self.emit(f"    mov dword ptr [{destination}_len], 1")
        self.emit(f"    mov dword ptr [{destination}_type], {_TYPE_STRING}")

    def emit_store_expression_to_slot(self, expression: DBaseExpression, destination: str) -> None:
        info = self.current_expression_info[expression]
        if (isinstance(expression, DBaseCallExpression) and
                expression.name.casefold() in {"type", "vartype"}):
            self.emit_type_query_to_slot(expression, destination)
            return
        if info.kind in {"number", "logical"}:
            self.emit_numeric_expression(expression)
            self.emit(f"    fstp qword ptr [{destination}_num]")
            self.emit(f"    mov dword ptr [{destination}_type], "
                      f"{_TYPE_LOGICAL if info.kind == 'logical' else _TYPE_NUMBER}")
            if info.kind == "logical":
                # Keep a text view for existing print/output paths.
                yes, _ = self.text_literal(".T.")
                no, _ = self.text_literal(".F.")
                if isinstance(expression, DBaseLiteralExpression):
                    self.emit(f"    mov {'rax' if self.is64 else 'eax'}, {yes if expression.value else no}")
                else:
                    self.emit(f"    mov {'rax' if self.is64 else 'eax'}, {yes}")
                    # Update pointer conditionally from numeric slot, without touching its type.
                    end = self.new_label('logical_view')
                    self.emit(f"    mov eax, dword ptr [{destination}_num]")
                    self.emit(f"    or eax, dword ptr [{destination}_num+4]")
                    self.emit(f"    mov {'rax' if self.is64 else 'eax'}, {yes}")
                    self.emit(f"    jne {end}")
                    self.emit(f"    mov {'rax' if self.is64 else 'eax'}, {no}")
                    self.emit(f"{end}:")
                self.emit(f"    mov {'qword' if self.is64 else 'dword'} ptr [{destination}_ptr], {'rax' if self.is64 else 'eax'}")
                self.emit(f"    mov dword ptr [{destination}_len], 3")
            return

        if isinstance(expression, DBaseLiteralExpression):
            if expression.value_type == "date":
                self.emit_static_text_to_slot(str(expression.value), "string", destination)
                self.emit(f"    mov dword ptr [{destination}_type], {_TYPE_DATE}")
            else:
                self.emit_static_text_to_slot(str(expression.value), expression.value_type, destination)
            return

        if isinstance(expression, DBaseIdentifierExpression):
            self.emit_copy_slot(info.variable_label, destination)
            return

        if isinstance(expression, DBaseCallExpression):
            if expression.name.casefold() in {"ltrim", "rtrim", "trim"}:
                from .string_length_trim import emit_trim_operation
                if info.constant_value is not None:
                    self.emit_static_text_to_slot(str(info.constant_value.value),
                                                  "string", destination)
                    return
                source = self.new_storage_slot("trim_source")
                self.emit_store_expression_to_slot(expression.arguments[0], source)
                for instruction in emit_trim_operation(
                    source, destination, kind=expression.name.casefold(),
                    is64=self.is64, prefix=self.new_label("trim"),
                    string_type=_TYPE_STRING,
                ):
                    self.emit(instruction)
                return
            if expression.name == "$":
                from .string_substring import emit_substring_copy
                slots = []
                for arg in expression.arguments:
                    slot = self.new_storage_slot("substring_arg")
                    self.emit_store_expression_to_slot(arg, slot)
                    slots.append(slot)
                for line in emit_substring_copy(slots[0], slots[1],
                        slots[2] if len(slots) == 3 else None, destination,
                        self.is64, self.new_label("substring"), _TYPE_STRING):
                    self.emit(line)
                return
            if expression.name == "!":
                from .string_upper import emit_upper_copy
                source = self.new_storage_slot("upper_source")
                self.emit_store_expression_to_slot(expression.arguments[0], source)
                for line in emit_upper_copy(
                    source, destination, self.is64,
                    self.new_label("upper"), _TYPE_STRING
                ):
                    self.emit(line)
                return
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
            label, length = self.text_literal(_format_dbase_value(DBaseValue(expression.value_type, expression.value)))
            self.emit_write_static(label, length, target)
            return

        if isinstance(expression, DBaseIdentifierExpression):
            self.emit_write_variable_text(info.variable_label, target)
            return

        if isinstance(expression, DBaseCallExpression):
            if expression.name.casefold() in {"type", "vartype"}:
                slot = self.new_storage_slot("type_print")
                self.emit_type_query_to_slot(expression, slot)
                self.emit_write_variable_text(slot, target)
                return
            if expression.name in {"!", "$"} or expression.name.casefold() in {"ltrim", "rtrim", "trim"}:
                slot = self.new_storage_slot("string_builtin_print")
                self.emit_store_expression_to_slot(expression, slot)
                self.emit_write_variable_text(slot, target)
                return
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

    def emit_condition_jump_true(self, condition: DBaseExpression, true_label: str) -> None:
        skip_label = self.new_label("logic_not_true")
        self.emit_condition_jump_false(condition, skip_label)
        self.emit(f"    jmp {true_label}")
        self.emit(f"{skip_label}:")

    def emit_condition_jump_false(self, condition: DBaseExpression, false_label: str) -> None:
        if isinstance(condition, DBaseUnaryExpression) and condition.operator == ".not.":
            self.emit_condition_jump_true(condition.operand, false_label)
            return
        if isinstance(condition, DBaseBinaryExpression):
            op = condition.operator
            if op == ".and.":
                self.emit_condition_jump_false(condition.left, false_label)
                self.emit_condition_jump_false(condition.right, false_label)
                return
            if op == ".or.":
                success = self.new_label("logic_or_true")
                self.emit_condition_jump_true(condition.left, success)
                self.emit_condition_jump_false(condition.right, false_label)
                self.emit(f"{success}:")
                return
            if op == ".xor.":
                left_false = self.new_label("logic_xor_left_false")
                done = self.new_label("logic_xor_done")
                self.emit_condition_jump_false(condition.left, left_false)
                self.emit_condition_jump_true(condition.right, false_label)
                self.emit(f"    jmp {done}")
                self.emit(f"{left_false}:")
                self.emit_condition_jump_false(condition.right, false_label)
                self.emit(f"{done}:")
                return
        if not isinstance(condition, DBaseCondition):
            # Nonzero numeric expression is logically true.
            self.emit_numeric_expression(condition)
            self.emit("    fldz")
            self.emit("    fucomip st0, st1")
            self.emit("    fstp st0")
            self.emit(f"    je {false_label}")
            return
        left_info = self.current_expression_info[condition.left]
        right_info = self.current_expression_info[condition.right]
        numeric = (left_info.kind == right_info.kind and
                   left_info.kind in {"number", "logical"})

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

    def emit_set_background(self, statement: DBaseSetBackgroundStatement) -> None:
        """Runtime ABI DBaseQtFillBackground(bg, fg, ch), 32-bit cdecl.

        The single-argument form passes -1/-1 to retain the current
        background/foreground palette; expressions are evaluated at runtime.
        """
        # Store each operand in its own slot to preserve the order and to
        # prevent subsequent FUNCTION calls from clobbering earlier results.
        slots = []
        for expression in statement.arguments:
            slot = self.new_storage_slot("background_arg")
            self.emit_numeric_expression(expression)
            self.emit(f"    fistp dword ptr [{slot}_num]")
            slots.append(slot)
        if len(slots) == 1:
            bg, fg, char = None, None, slots[0]
        else:
            bg, fg, char = slots
        if self.is64:
            self.emit(f"    mov ecx, dword ptr [{bg}_num]" if bg else "    mov ecx, -1")
            self.emit(f"    mov edx, dword ptr [{fg}_num]" if fg else "    mov edx, -1")
            self.emit(f"    mov r8d, dword ptr [{char}_num]")
            self.emit("    sub rsp, 40")
            self.emit("    call DBaseQtFillBackground")
            self.emit("    add rsp, 40")
        else:
            self.emit(f"    push dword ptr [{char}_num]")
            self.emit(f"    push dword ptr [{fg}_num]" if fg else "    push -1")
            self.emit(f"    push dword ptr [{bg}_num]" if bg else "    push -1")
            self.emit("    call DBaseQtFillBackground")
            self.emit("    add esp, 12")

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

    # Stage 342: speech is imported only for programs actually using it.
    def emit_speech_apply(self) -> None:
        self.emit("    push dword ptr [__dbase_speech_backend]")
        self.emit("    call SpeechSetBackend")
        for fn, var in (("SpeechSetMix", "mix"), ("SpeechSetPitch", "pitch"),
                        ("SpeechSetSpeed", "speed"), ("SpeechSetExpression", "expression"),
                        ("SpeechSetArticulation", "articulation"), ("SpeechSetFluency", "fluency")):
            self.emit(f"    push dword ptr [__dbase_speech_{var}]")
            self.emit(f"    call {fn}")     # Win32 __stdcall: DLL cleans 4 bytes.

    def emit_set_speech(self, statement: DBaseSetSpeechStatement) -> None:
        if statement.option == "state":
            if statement.value == "on":
                done = self.new_label("speech_on_done")
                self.emit("    cmp dword ptr [__dbase_speech_ready], 0")
                self.emit(f"    jne {done}")
                self.emit("    push 22050")
                self.emit("    call SpeechInitialize")
                self.emit("    mov dword ptr [__dbase_speech_ready], eax")
                self.emit("    test eax, eax")
                self.emit(f"    je {done}")
                self.emit_speech_apply()
                self.emit(f"{done}:")
            else:
                self.emit_speech_shutdown()
            return
        if statement.option == "mode":
            # Piper synthesizes complete sentences; SAMPLES reads prepared SPC WAV samples.
            backend = 1 if str(statement.value) == "piper" else 2 if str(statement.value) == "samples" else 0
            self.emit(f"    mov dword ptr [__dbase_speech_backend], {backend}")
            skip = self.new_label("speech_backend_skip")
            self.emit("    cmp dword ptr [__dbase_speech_ready], 0")
            self.emit(f"    je {skip}")
            self.emit(f"    push {backend}")
            self.emit("    call SpeechSetBackend")
            self.emit(f"{skip}:")
            if backend in (1, 2):
                return
            # Keep the same preset values as speech/retro_speech_demo.c.
            profiles = {"c64": (15, 130, 105, 38, 90, 25),
                        "hybrid": (55, 125, 100, 65, 60, 75),
                        "amiga": (85, 125, 100, 80, 35, 100)}
            mix, pitch, speed, expression, articulation, fluency = profiles[str(statement.value)]
            values = (("mix", mix, "SpeechSetMix"),
                      ("pitch", pitch, "SpeechSetPitch"),
                      ("speed", speed, "SpeechSetSpeed"),
                      ("expression", expression, "SpeechSetExpression"),
                      ("articulation", articulation, "SpeechSetArticulation"),
                      ("fluency", fluency, "SpeechSetFluency"))
        else:
            values = ((statement.option, int(statement.value),
                       {"mix":"SpeechSetMix", "pitch":"SpeechSetPitch", "speed":"SpeechSetSpeed",
                        "fluency":"SpeechSetFluency", "expression":"SpeechSetExpression",
                        "articulation":"SpeechSetArticulation"}[statement.option]),)
        for key, value, fn in values:
            self.emit(f"    mov dword ptr [__dbase_speech_{key}], {value}")
            skip = self.new_label("speech_setting_skip")
            self.emit("    cmp dword ptr [__dbase_speech_ready], 0")
            self.emit(f"    je {skip}")
            self.emit(f"    push {value}")
            self.emit(f"    call {fn}")
            self.emit(f"{skip}:")

    def emit_speech_shutdown(self) -> None:
        done = self.new_label("speech_shutdown_done")
        self.emit("    cmp dword ptr [__dbase_speech_ready], 0")
        self.emit(f"    je {done}")
        self.emit("    call SpeechShutdown")
        self.emit("    mov dword ptr [__dbase_speech_ready], 0")
        self.emit(f"{done}:")

    def emit_say(self, statement: DBaseSayStatement) -> None:
        info = self.current_expression_info[statement.expression]
        if info.kind not in {"string", "char"}:
            raise DBaseCompilerError("SAY erwartet einen String oder Char.",
                                     statement.line, statement.column, self.filename)
        done = self.new_label("speech_say_done")
        self.emit("    cmp dword ptr [__dbase_speech_ready], 0")
        self.emit(f"    je {done}")
        if info.constant_value is not None:
            payload = str(info.constant_value.value).encode("utf-8")
            label = self.speech_utf8_literals.get(payload)
            if label is None:
                label = self.new_label("speech_utf8")
                self.speech_utf8_literals[payload] = label
            self.emit(f"    push {label}")
            self.emit("    call SpeechSpeak")
        else:
            # dBase string slots hold CP1252 bytes with a length. The DLL
            # helper performs a bounded CP1252 -> UTF-8 conversion.
            slot = self.new_storage_slot("speech_text")
            self.emit_store_expression_to_slot(statement.expression, slot)
            self.emit(f"    push dword ptr [{slot}_len]")
            self.emit(f"    push dword ptr [{slot}_ptr]")
            self.emit("    call SpeechSpeakCP1252")
        self.emit(f"{done}:")

    def emit_win32_raise(self, statement: DBaseCallStatement) -> None:
        """Promote an explicitly supplied Win32 error number to TObject."""
        kind = _WIN32_RAISE_BUILTINS[statement.call.name.casefold()]
        self.emit_numeric_expression(statement.call.arguments[0])
        self.emit("    fistp dword ptr [__dbase_exception_code]")
        self.emit_win32_raise_code(kind)

    def emit_win32_check_file(self, statement: DBaseCallStatement) -> None:
        """Probe a user-private VFS file via Qt/Win32 and promote its error.

        One atomic bridge call does the actual CreateFileW and captures
        GetLastError BEFORE returning; arbitrary host paths are rejected by
        the same virtual mount mapping as the editor's Open dialog.
        """
        self.emit_store_expression_to_slot(statement.call.arguments[0],
                                           "__dbase_win32_file_path")
        if self.is64:
            self.emit("    mov rcx, qword ptr [__dbase_win32_file_path_ptr]")
            self.emit("    mov edx, dword ptr [__dbase_win32_file_path_len]")
            self.emit("    sub rsp, 40")
            self.emit("    call DBaseQtVfsCheckOpenRead")
            self.emit("    add rsp, 40")
        else:
            self.emit("    push dword ptr [__dbase_win32_file_path_len]")
            self.emit("    push dword ptr [__dbase_win32_file_path_ptr]")
            self.emit("    call DBaseQtVfsCheckOpenRead")
            self.emit("    add esp, 8")
        self.emit("    mov dword ptr [__dbase_exception_code], eax")
        self.emit_win32_raise_code("win32fileexception")

    def emit_win32_raise_code(self, kind: str) -> None:
        """Common conversion of an OS DWORD into managed exception + native Code."""
        done = self.new_label("win32_no_error")
        self.emit("    cmp dword ptr [__dbase_exception_code], 0")
        self.emit(f"    je {done}")
        self.emit_win32_message()
        class_name, _parent, type_id = self.exception_types[kind]
        self.emit_static_text_to_slot(class_name, "string", "__dbase_exception_class")
        self.emit(f"    mov dword ptr [__dbase_exception_id], {type_id}")
        # Stage 647: the Win32 DWORD must exist before Win32Exception.__ini__
        # formats super().Code; the default factory called __ini__ first.
        self.emit_build_exception_object(kind, preinit_code=True)
        # Native numeric PROPERTY inherited from Exception, not just BSS.
        from .object_abi import method_label
        skip = self.new_label("win32_missing_object")
        if self.is64:
            self.emit("    mov rcx, qword ptr [__dbase_exception_object_ptr]")
            self.emit("    test rcx, rcx")
            self.emit(f"    jz {skip}")
            self.emit("    mov edx, dword ptr [__dbase_exception_code]")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {method_label('Exception', 'set_Code')}")
            self.emit("    add rsp, 40")
        else:
            self.emit("    cmp dword ptr [__dbase_exception_object_ptr], 0")
            self.emit(f"    je {skip}")
            self.emit("    push dword ptr [__dbase_exception_code]")
            self.emit("    push dword ptr [__dbase_exception_object_ptr]")
            self.emit(f"    call {method_label('Exception', 'set_Code')}")
            self.emit("    add esp, 8")
        self.emit(f"{skip}:")
        self.emit(f"    jmp {self._exception_destination()}")
        self.emit(f"{done}:")

    def emit_win32_message(self) -> None:
        """FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS.

        Uses a buffer private to the executable.  __ini__ copies it to the
        native object's owned Message property before the next API call.
        """
        message_ok = self.new_label("win32_message_ok")
        message_done = self.new_label("win32_message_done")
        if self.is64:
            self.emit("    mov ecx, 4608")  # 0x1200 flags
            self.emit("    xor edx, edx")
            self.emit("    mov r8d, dword ptr [__dbase_exception_code]")
            self.emit("    xor r9d, r9d")  # system UI locale
            self.emit("    sub rsp, 72")
            self.emit("    mov rax, __dbase_win32_message_buffer")
            self.emit("    mov qword ptr [rsp+32], rax")
            self.emit("    mov qword ptr [rsp+40], 1024")
            self.emit("    mov qword ptr [rsp+48], 0")
            self.emit("    call FormatMessageA")
            self.emit("    add rsp, 72")
            self.emit("    test eax, eax")
            self.emit(f"    jnz {message_ok}")
        else:
            for arg in ("0", "1024", "__dbase_win32_message_buffer", "0",
                        "dword ptr [__dbase_exception_code]", "0", "4608"):
                self.emit(f"    push {arg}")
            self.emit("    call FormatMessageA")
            self.emit("    test eax, eax")
            self.emit(f"    jnz {message_ok}")
        self.emit_static_text_to_slot("Windows-Systemfehler", "string", "__dbase_exception_message")
        self.emit(f"    jmp {message_done}")
        self.emit(f"{message_ok}:")
        self.emit("    mov dword ptr [__dbase_exception_message_len], eax")
        if self.is64:
            self.emit("    mov rax, __dbase_win32_message_buffer")
            self.emit("    mov qword ptr [__dbase_exception_message_ptr], rax")
        else:
            self.emit("    mov dword ptr [__dbase_exception_message_ptr], __dbase_win32_message_buffer")
        self.emit(f"    mov dword ptr [__dbase_exception_message_type], {_TYPE_STRING}")
        self.emit(f"{message_done}:")

    def emit_exitprocess(self, statement: DBaseCallStatement) -> None:
        """Explicit Win32 exit; the caller owns cleanup and exit code."""
        argument = statement.call.arguments[0]
        self.emit_numeric_expression(argument)
        self.emit("    fistp dword ptr [__dbase_temp_number]")
        if self.is64:
            self.emit("    mov ecx, dword ptr [__dbase_temp_number]")
            self.emit("    sub rsp, 40")
            self.emit("    call ExitProcess")
            self.emit("    add rsp, 40")
        else:
            self.emit("    push dword ptr [__dbase_temp_number]")
            self.emit("    call ExitProcess")

    def _exception_destination(self) -> str:
        return self._exception_targets[-1] if self._exception_targets else self._exception_fallback

    def emit_exception_check(self) -> None:
        destination = self._exception_destination()
        if not destination:
            return
        self.emit("    cmp dword ptr [__dbase_exception_id], 0")
        no_error = self.new_label("exception_clear")
        self.emit(f"    je {no_error}")
        # Discard any pending x87 temporaries when a nested FUNCTION throws.
        self.emit("    fninit")
        self.emit(f"    jmp {destination}")
        self.emit(f"{no_error}:")

    def emit_build_exception_object(self, class_key: str, *, preinit_code=False) -> None:
        # A derived backend may instantiate a real native object here.
        # The final _DBaseCodeGenerator supplies that implementation.
        self.emit("    mov dword ptr [__dbase_exception_object_ptr], 0")

    def emit_throw(self, statement: DBaseThrowStatement) -> None:
        if statement.variable or not statement.class_name:
            name = statement.variable.casefold() if statement.variable else ""
            prefix = next((binding[name] for binding in reversed(self._caught_bindings)
                           if name in binding), "") if name else (
                next(iter(self._caught_bindings[-1].values()))
                if self._caught_bindings else "")
            if not prefix:
                raise AssertionError("THROW ohne sichtbare CATCH-Variable")
            self.emit_copy_exception_pair(prefix + "_message", "__dbase_exception_message")
            self.emit(f"    mov eax, dword ptr [{prefix}_id_num]")
            self.emit("    mov dword ptr [__dbase_exception_id], eax")
            self.emit(f"    fld qword ptr [{prefix}_code_num]")
            self.emit("    fistp dword ptr [__dbase_exception_code]")
            if self.is64:
                self.emit(f"    mov rax, qword ptr [{prefix}_object_ptr]")
                self.emit("    mov qword ptr [__dbase_exception_object_ptr], rax")
            else:
                self.emit(f"    mov eax, dword ptr [{prefix}_object_ptr]")
                self.emit("    mov dword ptr [__dbase_exception_object_ptr], eax")
        else:
            key = statement.class_name.casefold()
            name, _parent, class_id = self.exception_types[key]
            if statement.message is not None:
                self.emit_store_expression_to_slot(statement.message, "__dbase_exception_message")
            else:
                self.emit_static_text_to_slot("Error.", "string", "__dbase_exception_message")
            self.emit_static_text_to_slot(name, "string", "__dbase_exception_class")
            self.emit(f"    mov dword ptr [__dbase_exception_id], {class_id}")
            self.emit("    mov dword ptr [__dbase_exception_code], 0")
            # Stage 640: real JitVmt/TObject instance, not class/message-only
            # metadata.  The concrete generator chooses the native factory.
            self.emit_build_exception_object(key)
        destination = self._exception_destination()
        if not destination:
            raise AssertionError("Exception-Fallback fehlt")
        self.emit(f"    jmp {destination}")

    def emit_try_statement(
        self, statement: DBaseTryStatement, *,
        routine_end_label: str, routine_result_label: str,
        format_target: str, debug_override: Optional[bool], debug_visible: bool,
    ) -> None:
        """Typed dispatch and lexical cleanup, with routine-call propagation."""
        outer_targets = self._exception_targets
        outer_finalizers = self._dbase_finalizers
        dispatch = self.new_label("catch_dispatch")
        finally_label = self.new_label("exception_finally")
        after_label = self.new_label("exception_after")
        self._exception_targets = outer_targets + (dispatch,)
        if statement.finally_body:
            self._dbase_finalizers = outer_finalizers + (
                (statement.finally_body, len(outer_targets)),)
        try:
            self._emit_statement_sequence(
                statement.try_body, routine_end_label=routine_end_label,
                routine_result_label=routine_result_label,
                format_target=format_target, debug_override=debug_override,
                debug_visible=debug_visible)
        finally:
            self._exception_targets = outer_targets
            self._dbase_finalizers = outer_finalizers
        self.emit(f"    jmp {finally_label}")
        self.emit(f"{dispatch}:")
        for clause in statement.catches:
            handler = self.new_label("catch_handler")
            candidates = []
            for key, (_name, _parent, class_id) in self.exception_types.items():
                ancestor = key
                while ancestor in self.exception_types:
                    if ancestor == clause.class_name.casefold():
                        candidates.append(class_id)
                        break
                    ancestor = self.exception_types[ancestor][1].casefold()
            for class_id in candidates:
                self.emit(f"    cmp dword ptr [__dbase_exception_id], {class_id}")
                self.emit(f"    je {handler}")
            # Dispatch falls through to the next typed handler on mismatch.
            next_catch = self.new_label("catch_next")
            self.emit(f"    jmp {next_catch}")
            prefix = _dbase_catch_prefix(clause)
            self.emit(f"{handler}:")
            self.emit_copy_exception_pair("__dbase_exception_message", prefix + "_message")
            if self.is64:
                self.emit("    mov rax, qword ptr [__dbase_exception_object_ptr]")
                self.emit(f"    mov qword ptr [{prefix}_object_ptr], rax")
                self.emit("    mov qword ptr [__dbase_exception_object_ptr], 0")
            else:
                self.emit("    mov eax, dword ptr [__dbase_exception_object_ptr]")
                self.emit(f"    mov dword ptr [{prefix}_object_ptr], eax")
                self.emit("    mov dword ptr [__dbase_exception_object_ptr], 0")
            self.emit("    mov eax, dword ptr [__dbase_exception_id]")
            self.emit(f"    mov dword ptr [{prefix}_id_num], eax")
            self.emit("    fild dword ptr [__dbase_exception_code]")
            self.emit(f"    fstp qword ptr [{prefix}_code_num]")
            self.emit(f"    mov dword ptr [{prefix}_code_type], {_TYPE_NUMBER}")
            self.emit("    mov dword ptr [__dbase_exception_id], 0")
            self._caught_bindings.append({clause.variable.casefold(): prefix})
            self._exception_targets = outer_targets + (finally_label,)
            if statement.finally_body:
                self._dbase_finalizers = outer_finalizers + (
                    (statement.finally_body, len(outer_targets)),)
            try:
                self._emit_statement_sequence(
                    clause.body, routine_end_label=routine_end_label,
                    routine_result_label=routine_result_label,
                    format_target=format_target, debug_override=debug_override,
                    debug_visible=debug_visible)
            finally:
                self._caught_bindings.pop()
                self._exception_targets = outer_targets
                self._dbase_finalizers = outer_finalizers
            self.emit(f"    jmp {finally_label}")
            self.emit(f"{next_catch}:")
        self.emit(f"{finally_label}:")
        self._emit_statement_sequence(
            statement.finally_body, routine_end_label=routine_end_label,
            routine_result_label=routine_result_label,
            format_target=format_target, debug_override=debug_override,
            debug_visible=debug_visible)
        self.emit_exception_check()  # unhandled / thrown from CATCH / FINALLY
        self.emit(f"{after_label}:")

    def emit_pending_finalizers(
        self, *, routine_end_label: str, routine_result_label: str,
        format_target: str, debug_override: Optional[bool], debug_visible: bool,
    ) -> None:
        stack = self._dbase_finalizers
        targets = self._exception_targets
        try:
            for depth in range(len(stack) - 1, -1, -1):
                body, target_depth = stack[depth]
                self._dbase_finalizers = stack[:depth]
                self._exception_targets = targets[:target_depth]
                self._emit_statement_sequence(
                    body, routine_end_label=routine_end_label,
                    routine_result_label=routine_result_label,
                    format_target=format_target, debug_override=debug_override,
                    debug_visible=debug_visible)
        finally:
            self._dbase_finalizers = stack
            self._exception_targets = targets

    def _emit_statement_sequence(
        self,
        sequence: Tuple[object, ...],
        *,
        routine_end_label: str = "",
        routine_result_label: str = "",
        format_target: str = "screen",
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
                self.emit(
                    "    mov dword ptr [__dbase_output_format_screen], "
                    + ("1" if statement.target == "screen" else "0")
                )
            elif isinstance(statement, DBaseSetDebugStatement):
                debug_override = bool(statement.enabled)
                debug_visible = bool(statement.enabled)
                self.emit(
                    "    mov dword ptr [__dbase_output_debug_override], "
                    + ("1" if statement.enabled else "0")
                )
                self.emit(
                    "    mov dword ptr [__dbase_output_debug_visible], "
                    + ("1" if statement.enabled else "0")
                )
                self.emit_qt_call1_int("DBaseQtSetDebugVisible", 1 if debug_visible else 0)
            elif isinstance(statement, DBaseSetSpeechStatement):
                self.emit_set_speech(statement)
            elif isinstance(statement, DBaseSayStatement):
                self.emit_say(statement)
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
            elif isinstance(statement, DBaseSetBackgroundStatement):
                self.emit_set_background(statement)
            elif isinstance(statement, DBaseClearScreenStatement):
                self.emit_clear_screen(statement)
            elif isinstance(statement, DBaseSetBorderColorStatement):
                self.emit_border_color(statement)
            elif isinstance(statement, DBaseCallStatement):
                if statement.call.name.casefold() == "win32checkfile":
                    self.emit_win32_check_file(statement)
                elif statement.call.name.casefold() in _WIN32_RAISE_BUILTINS:
                    self.emit_win32_raise(statement)
                elif statement.call.name.casefold() == "exitprocess":
                    self.emit_exitprocess(statement)
                else:
                    self.emit_call_statement(statement)
            elif isinstance(statement, DBaseThrowStatement):
                self.emit_throw(statement)
            elif isinstance(statement, DBaseTryStatement):
                self.emit_try_statement(
                    statement, routine_end_label=routine_end_label,
                    routine_result_label=routine_result_label,
                    format_target=format_target, debug_override=debug_override,
                    debug_visible=debug_visible)
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
                # Runtimezustand statt Compilerzustand: SET DEBUG in einer
                # FUNCTION/PROCEDURE oder class::Callback gilt anschliessend
                # genauso fuer das aufrufende Hauptprogramm und .prg-Dateien.
                self.emit_print_expression(statement.expression, "runtime")
                if statement.newline:
                    newline_label, newline_len = self.text_literal("\r\n")
                    self.emit_write_static(newline_label, newline_len, "runtime")
                self.emit_qt_call0("DBaseQtProcessEvents")
            elif isinstance(statement, DBaseReturnStatement):
                if not routine_end_label:
                    raise AssertionError("RETURN ausserhalb Routine im Codegen")
                if statement.expression is not None:
                    if not routine_result_label:
                        raise AssertionError("PROCEDURE mit Rueckgabewert")
                    self.emit_store_expression_to_slot(statement.expression, routine_result_label)
                self.emit_pending_finalizers(
                    routine_end_label=routine_end_label,
                    routine_result_label=routine_result_label,
                    format_target=format_target, debug_override=debug_override,
                    debug_visible=debug_visible)
                self.emit(f"    jmp {routine_end_label}")
            else:
                raise AssertionError(type(statement))

            if not isinstance(statement, (DBaseReturnStatement, DBaseThrowStatement)):
                self.emit_shutdown_guard(routine_end_label)
        return format_target, debug_override, debug_visible

    def emit_routine_instance(self, instance: _DBaseRoutineInstance) -> None:
        previous_info = self.current_expression_info
        previous_calls = self.current_call_bindings
        previous_instance = self.current_instance
        previous_fallback = self._exception_fallback
        self.current_expression_info = instance.expression_info
        self.current_call_bindings = instance.call_bindings
        self.current_instance = instance
        try:
            self.emit()
            self.emit(f"{instance.label}:")
            end_label = f"{instance.label}_end"
            self._exception_fallback = end_label
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
            self._exception_fallback = previous_fallback

    def _emit_value_slot_data(self, label: str) -> None:
        # Stage 223: zero-initialized runtime slots belong to .bss.  The PE
        # loader provides them as zero-filled virtual memory, so they consume
        # no bytes in the executable image.
        self.bss_lines.extend([
            f"{label}_type:",
            "    resd 1",
            f"{label}_num:",
            "    resq 1",
            f"{label}_ptr:",
            "    resq 1" if self.is64 else "    resd 1",
            f"{label}_len:",
            "    resd 1",
        ])

    def emit_native_console_runtime(self, title_label: str) -> None:
        """Emittiert die lazy AllocConsole-/WriteFile-Laufzeit.

        Der Screen-Buffer wird auf 500 Zeilen gesetzt. Die aktuelle Breite
        bleibt erhalten, damit das Console-Host-Fenster keine unnoetige
        horizontale Scrollbar bekommt. Die normale Windows-Konsole liefert
        damit Scroll-Back per Mausrad und scrollt bei fortlaufender Ausgabe
        automatisch am unteren Rand weiter.
        """
        self.emit()
        self.emit("; Stage 109: lazy Win32 console for dBase ? / ??")
        self.emit("__dbase_console_ensure:")
        self.emit("    cmp dword ptr [__dbase_console_ready], 0")
        self.emit("    jne __dbase_console_ensure_done")

        # Stage 114: Vor AllocConsole wird bewusst NICHT mehr FreeConsole()
        # aufgerufen. Auf dem privaten D64Workstation-Desktop kann ein
        # vorschnelles Abtrennen die vom Console Host gerade aufgebaute
        # Zuordnung unguenstig beeinflussen. Falls bereits eine Console
        # existiert, darf AllocConsole() fehlschlagen; CONOUT$ wird danach
        # trotzdem explizit geoeffnet und verwendet.
        if self.is64:
            self.emit("    sub rsp, 40")
            self.emit("    call AllocConsole")
            self.emit("    add rsp, 40")

            # CreateFileA("CONOUT$", GENERIC_READ|GENERIC_WRITE,
            #             FILE_SHARE_READ|FILE_SHARE_WRITE, NULL,
            #             OPEN_EXISTING, 0, NULL)
            self.emit("    sub rsp, 56")
            self.emit("    mov rcx, __dbase_console_out_name")
            self.emit("    mov edx, 3221225472")
            self.emit("    mov r8d, 3")
            self.emit("    xor r9d, r9d")
            self.emit("    mov qword ptr [rsp+32], 3")
            self.emit("    mov qword ptr [rsp+40], 0")
            self.emit("    mov qword ptr [rsp+48], 0")
            self.emit("    call CreateFileA")
            self.emit("    add rsp, 56")
            self.emit("    test rax, rax")
            self.emit("    je __dbase_console_handle_fallback")
            self.emit("    cmp rax, -1")
            self.emit("    je __dbase_console_handle_fallback")
            self.emit("    mov qword ptr [__dbase_console_handle], rax")
            self.emit("    jmp __dbase_console_handle_ready")
            self.emit("__dbase_console_handle_fallback:")
            self.emit("    mov ecx, -11")          # STD_OUTPUT_HANDLE
            self.emit("    sub rsp, 40")
            self.emit("    call GetStdHandle")
            self.emit("    add rsp, 40")
            self.emit("    test rax, rax")
            self.emit("    je __dbase_console_ensure_done")
            self.emit("    cmp rax, -1")
            self.emit("    je __dbase_console_ensure_done")
            self.emit("    mov qword ptr [__dbase_console_handle], rax")
            self.emit("__dbase_console_handle_ready:")

            self.emit("    mov ecx, 1252")
            self.emit("    sub rsp, 40")
            self.emit("    call SetConsoleOutputCP")
            self.emit("    add rsp, 40")

            self.emit("    mov rcx, qword ptr [__dbase_console_handle]")
            self.emit("    mov rdx, __dbase_console_info")
            self.emit("    sub rsp, 40")
            self.emit("    call GetConsoleScreenBufferInfo")
            self.emit("    add rsp, 40")
            self.emit("    test eax, eax")
            self.emit("    je __dbase_console_buffer_fallback")
            self.emit("    mov edx, dword ptr [__dbase_console_info]")
            self.emit("    and edx, 65535")
            self.emit("    or edx, 32768000")      # Y=500, X=current width
            self.emit("    jmp __dbase_console_buffer_ready")
            self.emit("__dbase_console_buffer_fallback:")
            self.emit("    mov edx, 32768080")     # COORD(80, 500)
            self.emit("__dbase_console_buffer_ready:")
            self.emit("    mov rcx, qword ptr [__dbase_console_handle]")
            self.emit("    sub rsp, 40")
            self.emit("    call SetConsoleScreenBufferSize")
            self.emit("    add rsp, 40")

            self.emit(f"    mov rcx, {title_label}")
            self.emit("    sub rsp, 40")
            self.emit("    call SetConsoleTitleA")
            self.emit("    add rsp, 40")

            # Stage 113: Auf D64Workstation wird die GUI auf einem eigenen
            # Desktop gestartet. Eine lazy AllocConsole-Konsole kann dort
            # hinter dem Formular erzeugt werden. GetConsoleWindow +
            # ShowWindow/SetWindowPos macht sie explizit sichtbar und holt
            # sie einmal nach vorn, ohne sie dauerhaft TOPMOST zu machen.
            self.emit("    sub rsp, 40")
            self.emit("    call GetConsoleWindow")
            self.emit("    add rsp, 40")
            self.emit("    test rax, rax")
            self.emit("    je __dbase_console_window_ready")
            self.emit("    mov qword ptr [__dbase_console_window], rax")
            self.emit("    mov rcx, rax")
            self.emit("    mov edx, 5")             # SW_SHOW
            self.emit("    sub rsp, 40")
            self.emit("    call ShowWindow")
            self.emit("    add rsp, 40")
            self.emit("    mov rcx, qword ptr [__dbase_console_window]")
            # Stage 115 TEST: Console effektiv modal/TOPMOST halten.
            self.emit("    mov rdx, -1")            # HWND_TOPMOST
            self.emit("    xor r8d, r8d")
            self.emit("    xor r9d, r9d")
            self.emit("    sub rsp, 56")
            self.emit("    mov qword ptr [rsp+32], 0")
            self.emit("    mov qword ptr [rsp+40], 0")
            self.emit("    mov dword ptr [rsp+48], 67")  # SWP_NOSIZE|NOMOVE|SHOWWINDOW
            self.emit("    call SetWindowPos")
            self.emit("    add rsp, 56")
            self.emit("    mov rcx, qword ptr [__dbase_console_window]")
            self.emit("    sub rsp, 40")
            self.emit("    call SetForegroundWindow")
            self.emit("    add rsp, 40")
            self.emit("__dbase_console_window_ready:")
        else:
            self.emit("    call AllocConsole")

            # Explizites CONOUT$ verhindert unsichtbare Ausgabe auf NUL,
            # wenn STARTF_USESTDHANDLES beim Prozessstart gesetzt war.
            self.emit("    push 0")
            self.emit("    push 0")
            self.emit("    push 3")                 # OPEN_EXISTING
            self.emit("    push 0")
            self.emit("    push 3")                 # FILE_SHARE_READ|WRITE
            self.emit("    push 3221225472")        # GENERIC_READ|WRITE
            self.emit("    push __dbase_console_out_name")
            self.emit("    call CreateFileA")
            self.emit("    test eax, eax")
            self.emit("    je __dbase_console_handle_fallback")
            self.emit("    cmp eax, -1")
            self.emit("    je __dbase_console_handle_fallback")
            self.emit("    mov dword ptr [__dbase_console_handle], eax")
            self.emit("    jmp __dbase_console_handle_ready")
            self.emit("__dbase_console_handle_fallback:")
            self.emit("    push -11")              # STD_OUTPUT_HANDLE
            self.emit("    call GetStdHandle")
            self.emit("    test eax, eax")
            self.emit("    je __dbase_console_ensure_done")
            self.emit("    cmp eax, -1")
            self.emit("    je __dbase_console_ensure_done")
            self.emit("    mov dword ptr [__dbase_console_handle], eax")
            self.emit("__dbase_console_handle_ready:")

            self.emit("    push 1252")
            self.emit("    call SetConsoleOutputCP")

            self.emit("    push __dbase_console_info")
            self.emit("    push dword ptr [__dbase_console_handle]")
            self.emit("    call GetConsoleScreenBufferInfo")
            self.emit("    test eax, eax")
            self.emit("    je __dbase_console_buffer_fallback")
            self.emit("    mov edx, dword ptr [__dbase_console_info]")
            self.emit("    and edx, 65535")
            self.emit("    or edx, 32768000")
            self.emit("    jmp __dbase_console_buffer_ready")
            self.emit("__dbase_console_buffer_fallback:")
            self.emit("    mov edx, 32768080")
            self.emit("__dbase_console_buffer_ready:")
            self.emit("    push edx")
            self.emit("    push dword ptr [__dbase_console_handle]")
            self.emit("    call SetConsoleScreenBufferSize")

            self.emit(f"    push {title_label}")
            self.emit("    call SetConsoleTitleA")

            # Stage 113: Console-Fenster auf dem Workstation-Desktop
            # explizit sichtbar machen und einmal nach vorn holen.
            self.emit("    call GetConsoleWindow")
            self.emit("    test eax, eax")
            self.emit("    je __dbase_console_window_ready")
            self.emit("    mov dword ptr [__dbase_console_window], eax")
            self.emit("    push 5")                 # SW_SHOW
            self.emit("    push eax")
            self.emit("    call ShowWindow")
            self.emit("    push 67")                # SWP_NOSIZE|NOMOVE|SHOWWINDOW
            self.emit("    push 0")                 # cy
            self.emit("    push 0")                 # cx
            self.emit("    push 0")                 # y
            self.emit("    push 0")                 # x
            # Stage 115 TEST: Console effektiv modal/TOPMOST halten.
            self.emit("    push -1")                # HWND_TOPMOST
            self.emit("    push dword ptr [__dbase_console_window]")
            self.emit("    call SetWindowPos")
            self.emit("    push dword ptr [__dbase_console_window]")
            self.emit("    call SetForegroundWindow")
            self.emit("__dbase_console_window_ready:")

        self.emit("    mov dword ptr [__dbase_console_ready], 1")
        self.emit("__dbase_console_ensure_done:")
        self.emit("    ret")

        self.emit()
        self.emit("__dbase_console_write:")
        if self.is64:
            # Entry: RCX=buffer, EDX=length. 56 bytes halten Shadow Space,
            # den 5. WriteFile-Parameter und unsere beiden lokalen Werte.
            self.emit("    sub rsp, 56")
            self.emit("    mov qword ptr [rsp+40], rcx")
            self.emit("    mov dword ptr [rsp+48], edx")
            self.emit("    call __dbase_console_ensure")
            self.emit("    cmp dword ptr [__dbase_console_ready], 0")
            self.emit("    je __dbase_console_write_done")
            self.emit("    cmp dword ptr [rsp+48], 0")
            self.emit("    je __dbase_console_write_done")
            self.emit("    mov rcx, qword ptr [__dbase_console_handle]")
            self.emit("    mov rdx, qword ptr [rsp+40]")
            self.emit("    mov r8d, dword ptr [rsp+48]")
            self.emit("    mov r9, __dbase_console_written")
            self.emit("    mov qword ptr [rsp+32], 0")
            self.emit("    call WriteFile")
            self.emit("__dbase_console_write_done:")
            self.emit("    add rsp, 56")
            self.emit("    ret")
        else:
            self.emit("    push ebp")
            self.emit("    mov ebp, esp")
            self.emit("    call __dbase_console_ensure")
            self.emit("    cmp dword ptr [__dbase_console_ready], 0")
            self.emit("    je __dbase_console_write_done")
            self.emit("    cmp dword ptr [ebp+12], 0")
            self.emit("    je __dbase_console_write_done")
            self.emit("    push 0")
            self.emit("    push __dbase_console_written")
            self.emit("    push dword ptr [ebp+12]")
            self.emit("    push dword ptr [ebp+8]")
            self.emit("    push dword ptr [__dbase_console_handle]")
            self.emit("    call WriteFile")
            self.emit("__dbase_console_write_done:")
            self.emit("    mov esp, ebp")
            self.emit("    pop ebp")
            self.emit("    ret")

        self.emit()
        self.emit("__dbase_console_shutdown:")
        self.emit("    cmp dword ptr [__dbase_console_ready], 0")
        self.emit("    je __dbase_console_shutdown_done")
        if self.is64:
            self.emit("    sub rsp, 40")
            self.emit("    call FreeConsole")
            self.emit("    add rsp, 40")
            self.emit("    mov qword ptr [__dbase_console_handle], 0")
        else:
            self.emit("    call FreeConsole")
            self.emit("    mov dword ptr [__dbase_console_handle], 0")
        if self.is64:
            self.emit("    mov qword ptr [__dbase_console_window], 0")
        else:
            self.emit("    mov dword ptr [__dbase_console_window], 0")
        self.emit("    mov dword ptr [__dbase_console_ready], 0")
        self.emit("__dbase_console_shutdown_done:")
        self.emit("    ret")

    def build(self) -> str:
        self.emit("bits 64" if self.is64 else "bits 32")
        self.emit()
        for symbol in (
            "DBaseQtSetWorkstationMode",
            "DBaseQtSetDebugTheme",
            "DBaseQtRuntimeStartup",
            "DBaseQtRuntimeShutdown",
            "DBaseQtShowWindow",
            "DBaseQtProcessEvents",
            "DBaseQtSetDebugVisible",
            "DBaseQtAppendConsole",
            "DBaseQtAppendDebug",
            "DBaseQtSetOutputColor",
            "DBaseQtFillBackground",
            "DBaseQtClearScreen",
            "DBaseQtClearScreenChar",
            "DBaseQtClearScreenColor",
            "DBaseQtSetBorderColor",
            "DBaseQtMarkProgramFinished",
            "DBaseQtExec",
            "DBaseQtShutdownRequested",
            "DBaseQtShutdown",
        ):
            self.emit(f'import {symbol}, "libd64_qt5.dll", "{symbol}"')
        if self.uses_speech:
            for symbol in ("SpeechInitialize", "SpeechSetBackend", "SpeechSetMix", "SpeechSetPitch",
                           "SpeechSetSpeed", "SpeechSetExpression", "SpeechSetArticulation",
                           "SpeechSetFluency", "SpeechSpeak", "SpeechSpeakCP1252", "SpeechShutdown"):
                self.emit(f'import {symbol}, "retro_speech.dll", "{symbol}"')
        # Die Runtime-Helfer werden absichtlich immer importiert. Damit koennen
        # spezialisierte FUNCTION-Instanzen auch Zahl->Text und dynamische
        # String-Konkatenation verwenden, selbst wenn im Hauptprogramm kein ?
        # vorkommt.
        self.emit('import __dbase_gcvt, "msvcrt.dll", "_gcvt"')
        self.emit('import __dbase_malloc, "msvcrt.dll", "malloc"')
        # Stage 208/209: !() fuehrt die Unicode-Konvertierung in der Runtime-DLL aus.
        if self.uses_upper_runtime:
            self.emit('import __dbase_upper_buffer, "libd64_qt5.dll", "DBaseUpperBuffer"')
        self.emit('import __dbase_memcpy, "msvcrt.dll", "memcpy"')
        self.emit('import __dbase_memcmp, "msvcrt.dll", "memcmp"')
        self.emit('import ExitProcess, "kernel32.dll", "ExitProcess"')
        if self._uses_win32_errors:
            self.emit('import FormatMessageA, "kernel32.dll", "FormatMessageA"')
        if self._uses_win32_file_check:
            self.emit('import DBaseQtVfsCheckOpenRead, "libd64_qt5.dll", "DBaseQtVfsCheckOpenRead"')
        # Stage 446: Native dBASE console management is provided by the
        # architecture-matched c64_dbase_runtime.dll (no embedded Win32 API).
        from .char_case_runtime import CASE_EXPORTS
        from .wfm_format_runtime import EXPORTS as WFM_EXPORTS
        for exported in ("DBaseConsoleEnsure", "DBaseConsoleWrite",
                         "DBaseConsoleShutdown", "DBaseConsoleSetTitle") + CASE_EXPORTS + WFM_EXPORTS:
            self.emit(f'import {exported}, "c64_dbase_runtime.dll", "{exported}"')
        if any(isinstance(expr, DBaseCallExpression)
               and expr.name.casefold() == "ismouse"
               for expr in self.analysis.expression_info):
            self.emit('import GetSystemMetrics, "user32.dll", "GetSystemMetrics"')
        if any(isinstance(expr, DBaseCallExpression)
               and expr.name.casefold() == "iskeyboard"
               for expr in self.analysis.expression_info):
            self.emit('import GetRawInputDeviceList, "user32.dll", "GetRawInputDeviceList"')
            # ISKEYBOARD allocates a temporary device list independently of
            # the shared Stage-462 format buffer.
            self.emit('import VirtualAlloc, "kernel32.dll", "VirtualAlloc"')
            self.emit('import VirtualFree, "kernel32.dll", "VirtualFree"')
        for function in self.analysis.external_functions:
            self.emit(f"extern {function}")
        for ffi in self.ffi_prototypes.values():
            self.emit(ffi.import_line)
        # Only typed ANSI string returns need lstrlenA. The existing C-CRT
        # malloc/memcpy imports above provide independent dBASE-owned storage.
        from .ffi_string_result import returns_ansi_string
        if any(returns_ansi_string(ffi.return_type)
               for ffi in self.ffi_prototypes.values()):
            self.emit('import __dbase_ffi_lstrlenA, "kernel32.dll", "lstrlenA"')
        self.emit("; __d64_dbase_startup_begin__")
        self.emit("global _start")
        self.emit("entry _start")
        self.emit()
        self.emit("section .text")
        self.emit()
        self.emit("_start:")

        self.program_cleanup_label = self.new_label("program_cleanup")
        title_label, _ = self.text_literal("dBase Qt5 Console / DEBUG")
        # Stage 462: gemeinsame Qt5-Initialisierung inklusive Formatpuffer.
        # Der Buffer-Slot bleibt in der EXE, die 96 Bytes besitzt die Runtime.
        theme_value = 0 if self.debug_theme == "default" else 1 if self.debug_theme == "light" else 2
        if self.is64:
            self.emit(f"    mov rcx, {title_label}")
            self.emit(f"    mov edx, {1 if self.workstation_mode else 0}")
            self.emit(f"    mov r8d, {theme_value}")
            self.emit("    xor r9d, r9d")  # console
            self.emit("    mov rax, __dbase_format_buffer")
            self.emit("    sub rsp, 40")
            self.emit("    mov qword ptr [rsp+32], rax")
            self.emit("    call DBaseQtRuntimeStartup")
            self.emit("    add rsp, 40")
        else:
            self.emit("    push __dbase_format_buffer")
            self.emit("    push 0")           # console
            self.emit(f"    push {theme_value}")
            self.emit(f"    push {1 if self.workstation_mode else 0}")
            self.emit(f"    push {title_label}")
            self.emit("    call DBaseQtRuntimeStartup")
            self.emit("    add esp, 20")
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

        # Vor dem ersten Show/Paint wird der definierte Startzustand hergestellt:
        # Konsole sichtbar, DEBUG aus. Die Bridge garantiert dabei, dass DEBUG OFF
        # niemals den Konsolen-Tab entfernt.
        self.emit_qt_call1_int("DBaseQtSetDebugVisible", 0)
        self.emit_qt_call0("DBaseQtShowWindow")
        self.emit_qt_call0("DBaseQtProcessEvents")
        self.emit_shutdown_guard()

        unhandled_label = self.new_label("exception_unhandled")
        continue_label = self.new_label("exception_continue")
        self._exception_fallback = unhandled_label
        self._emit_statement_sequence(self.statements)
        self.emit(f"    jmp {continue_label}")
        self.emit(f"{unhandled_label}:")
        label, count = self.text_literal("Unbehandelte Exception: ")
        self.emit_write_static(label, count, "runtime")
        self.emit_write_variable_text("__dbase_exception_class", "runtime")
        label, count = self.text_literal(": ")
        self.emit_write_static(label, count, "runtime")
        self.emit_write_variable_text("__dbase_exception_message", "runtime")
        label, count = self.text_literal("\r\n")
        self.emit_write_static(label, count, "runtime")
        self.emit_qt_call0("DBaseQtProcessEvents")
        self.emit(f"{continue_label}:")

        self.emit_qt_call0("DBaseQtMarkProgramFinished")
        self.emit_qt_call0("DBaseQtExec")
        self.emit("    mov dword ptr [__dbase_exit_code], eax")

        # Stage 462: Externe Ressourcen VOR DBaseQtShutdown abbauen.
        # Im Direktstart darf DBaseQtShutdown den Prozess selbst beenden.
        self.emit(f"{self.program_cleanup_label}:")
        if self.uses_speech:
            self.emit_speech_shutdown()
        self.emit_qt_call0("DBaseConsoleShutdown")
        if self.is64:
            self.emit("    mov rcx, __dbase_format_buffer")
            self.emit("    sub rsp, 40")
            self.emit("    call DBaseQtRuntimeShutdown")
            self.emit("    add rsp, 40")
        else:
            self.emit("    push __dbase_format_buffer")
            self.emit("    call DBaseQtRuntimeShutdown")
            self.emit("    add esp, 4")

        if self.is64:
            self.emit("    mov ecx, dword ptr [__dbase_exit_code]")
            self.emit("    sub rsp, 40")
            self.emit("    call ExitProcess")
        else:
            self.emit("    push dword ptr [__dbase_exit_code]")
            self.emit("    call ExitProcess")

        self.emit("; __d64_dbase_startup_end__")

        # Spezialisierte dBase-Member liegen im selben .text-Abschnitt. Die
        # Labels duerfen nach _start folgen, da der interne Assembler Forward-
        # Referenzen aufloest.
        for instance in self.analysis.routine_instances:
            self.emit_routine_instance(instance)

        # Stage 446: all console routines and their state reside in the DLL.

        self.data_lines = ["", "section .data", ""]
        for payload, label in self.speech_utf8_literals.items():
            self.data_lines.extend(_db_lines(label, payload, nul_terminate=True))
        for payload, label in self.ffi_string_literals.items():
            self.data_lines.extend(_db_lines(label, payload))
        if self.uses_speech:
            for key, default in (("backend", 0), ("mix", 55), ("pitch", 125), ("speed", 100),
                                 ("expression", 60), ("articulation", 65), ("fluency", 75)):
                self.data_lines.extend((f"__dbase_speech_{key}:", f"    dd {default}"))
        for raw, label in self.double_literals.items():
            low, high = struct.unpack("<II", raw)
            self.data_lines.extend([f"{label}:", f"    dd {low}, {high}"])
        empty_string_bss: list[str] = []
        for payload, label in self.string_literals.items():
            # Stage 223: an empty string only needs one zero byte in memory.
            # Put that byte into .bss instead of spending a raw DATA byte.
            if not payload:
                empty_string_bss.append(label)
                continue
            nul = label == title_label
            self.data_lines.extend(_db_lines(label, payload, nul_terminate=nul))
        self.data_lines.extend([
            # Stage 619: START DEFAULT = SCREEN (DEBUG), nicht CONSOLE.
            # Diese Initialisierung muss im PE .data stehen: .bss ist Null.
            "__dbase_output_format_screen:", "    dd 1",
            # -1 = noch keine explizite SET DEBUG-Anweisung; in diesem Fall
            # wirkt SET FORMAT TO SCREEN/CONSOLE weiter wie bisher.
            "__dbase_output_debug_override:", "    dd -1",
            # Stage 114: Der Workstation-Runner erkennt damit native dBase-
            # GUI-Programme, fuer die er vor dem Resume eine versteckte
            # Console auf dem D64Workstation-Desktop vorreservieren soll.
            "__dbase_workstation_lazy_console_marker:",
            "    db 68, 54, 52, 68, 66, 65, 83, 69, 95, 76, 65, 90, 89, 95, 67, 79, 78, 83, 79, 76, 69, 95, 86, 49, 0",
        ])

        # Stage 223: initialized-zero runtime storage is emitted as .bss so it
        # contributes VirtualSize but no SizeOfRawData to the PE image.
        self.bss_lines = [
            "", "section .bss", "",
            "__dbase_ffi_return:", "    resq 1",
            "__dbase_temp_number:", "    resd 1",
            "__dbase_temp_number_hi:", "    resd 1",
            "__dbase_int_cw:", "    resw 1",
            "__dbase_int_cw_trunc:", "    resw 1",
            "__dbase_call_number:", "    resq 1",
            "__dbase_format_buffer:", "    resq 1" if self.is64 else "    resd 1",
            "__dbase_exit_code:", "    resd 1",
            "__dbase_output_debug_visible:", "    resd 1",
            "__dbase_console_number_len:", "    resd 1",
            "__dbase_exception_id:", "    resd 1",
            "__dbase_exception_code:", "    resd 1",
        ]
        self.extra_storage_slots.extend(("__dbase_exception_message", "__dbase_exception_class",
                                         "__dbase_exception_object", "__dbase_exception_cstr"))
        if self._uses_win32_errors:
            self.bss_lines.extend(("__dbase_win32_message_buffer:", "    resb 1024"))
        if self._uses_win32_file_check:
            self.extra_storage_slots.append("__dbase_win32_file_path")
        if self.uses_speech:
            self.bss_lines.extend(("__dbase_speech_ready:", "    resd 1"))
        for label in empty_string_bss:
            self.bss_lines.extend([f"{label}:", "    resb 1"])

        all_slots: list[str] = []
        all_slots.extend(variable.label for variable in self.analysis.variables)
        all_slots.extend(self.analysis.storage_slots)
        all_slots.extend(self.extra_storage_slots)
        for label in dict.fromkeys(all_slots):
            self._emit_value_slot_data(label)

        return "\n".join(self.lines + self.data_lines + self.bss_lines).rstrip() + "\n"

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
    workstation_mode: bool = False,
    debug_theme: str = "default",
    include_paths=(),
) -> DBaseCompileResult:
    """Kompiliert dBase mit Qt5-GUI, Membern und verschachtelten Bedingungen.

    Implementiert:
    - //, **, && und /* ... */ Kommentare
    - ? <expr> und ?? <expr>; CONSOLE wird lazy per AllocConsole geoeffnet
    - Variablenzuweisung ``Name = Ausdruck``
    - Zahl-, Hex-, Char- und Stringliterale
    - arithmetische + - * / Ausdruecke und String-Konkatenation
    - PROCEDURE/FUNCTION mit beliebig vielen Parametern und nativen Member-Aufrufen
    - PROCEDURE endet ausschliesslich mit RETURN; FUNCTION mit RETURN <expr>
    - verschachtelte IF/ELSEIF/ELSE/ENDIF-Bloecke mit < <= = == > >= <> # und !=
    - TRY/CATCH/FINALLY/ENDTRY, THROW und typisierte dBL-Exceptions
    - ExitProcess(<code>) als expliziter Win32-Systemaufruf (sofortige Prozessbeendigung)
    - polymorphe FUNCTION-Spezialisierung nach Parameter-Typen (Zahl/String/Char)
    - no-arg Funktionsaufrufe als externe numerische Symbole
    - C-artige Makros: #define/#undef/#if/#ifdef/#ifndef/#elif/#else/#endif/#include, ## und #pragma link
    - #error/#warning/#info sowie __FILE__/__LINE__/__DATE__/__TIME__
    - Qt5-GUI mit Tabs "Konsole" und "DEBUG" ueber d64qt5.dll
    - SET FORMAT TO SCREEN als kompatibler Debug-Ausgabekanal
    - SET DEBUG ON/OFF blendet den DEBUG-Tab ein/aus und routet ?/??
    """
    frontend = preprocess_dbase_source(
        source,
        filename=filename,
        target=target,
        include_paths=include_paths,
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
    def speech_used(seq):
        return any(isinstance(item, (DBaseSetSpeechStatement, DBaseSayStatement))
                   or isinstance(item, DBaseRoutineDefinition) and speech_used(item.body)
                   or isinstance(item, DBaseIfStatement) and any(speech_used(branch.body) for branch in item.branches)
                   or isinstance(item, DBaseTryStatement) and (speech_used(item.try_body) or speech_used(item.finally_body) or any(speech_used(c.body) for c in item.catches))
                   for item in seq)
    if frontend.target == "pe64" and speech_used(statements):
        raise DBaseCompilerError(
            "SET SPEECH und SAY benoetigen derzeit PE32: retro_speech.dll ist eine 32-Bit-DLL.",
            filename=filename,
        )
    analysis = _analyze_program(statements, filename=filename, ffi_prototypes=frontend.ffi_prototypes)
    assembly = _DBaseCodeGenerator(
        statements,
        analysis,
        target=frontend.target,
        filename=filename,
        workstation_mode=workstation_mode,
        debug_theme=debug_theme,
        ffi_prototypes=frontend.ffi_prototypes,
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
            f"dBase-Ausbaustufe 12: dBase-Makros, Includes und Bedingungen fuer {target_label}.",
            "#define unterstuetzt Objekt- und Funktionsmakros; ## verkettet Tokens.",
            "#if/#ifdef/#ifndef/#elif/#else/#endif sind C/C++-artig verschachtelbar; defined(NAME) und defined NAME werden unterstuetzt.",
            "#include \"path/to/file\" bindet dBase-Quelltext relativ zur aktuellen Quelldatei ein; Include-Guards funktionieren ueber #define/#ifndef.",
            "#if 0 ... #endif kann beliebig grosse dBase-Codebereiche vom Compile ausschliessen.",
            "#error bricht den Compiler ab; #warning und #info erscheinen in den Diagnosen.",
            "Vordefiniert: __FILE__, __LINE__, __DATE__ und __TIME__.",
            "#pragma link bindet .o/.obj/.a/.lib beim finalen PE-Linkschritt ein.",
            "Variablen koennen Zahl/Hex, Char und String aufnehmen; Zuweisungen erzeugen echte Speicher-Slots.",
            "PROCEDURE endet ausschliesslich mit RETURN ohne Wert; FUNCTION ausschliesslich mit RETURN <expr>.",
            "ENDPROC/ENDPROCEDURE/ENDFUNC/ENDFUNCTION sind nicht mehr Bestandteil der dBase-Syntax.",
            "IF/ELSEIF/ELSE/ENDIF ist beliebig verschachtelbar; Operatoren: <, <=, =, ==, >, >=, <>, # und !=.",
            "Stage 639: TRY/CATCH/FINALLY/ENDTRY und THROW; alter Abschluss END wird abgewiesen.",
            "Stage 638: ExitProcess(code) ist ein expliziter sofortiger Win32-Prozessabbruch; er ist kein Exception-Handler und beendet auch die Qt5-Konsole.",
            "Innerhalb einer IF-Bedingung bedeutet '=' Gleichheit; ausserhalb bleibt '=' der Zuweisungsoperator.",
            "Numerische/Hex/Float-Werte werden numerisch, String/Char-Werte lexikographisch verglichen.",
            "Member-Parameterlisten sind nicht kuenstlich begrenzt; Aufrufe werden in Value-Slots uebergeben.",
            "FUNCTION-Instanzen werden anhand der verwendeten Parameter-Typen spezialisiert und koennen Zahl, String oder Char liefern.",
            "? fuegt CR/LF an; ?? schreibt ohne NewLine.",
            "Stage 619: ?/?? schreiben standardmaessig in den DEBUG-QDialog (wie Pascal WriteLn). SET FORMAT TO CONSOLE oder SET DEBUG OFF aktivieren die native Konsole.",
            "Stage 109: Beim ersten ausgefuehrten ?/?? im expliziten CONSOLE-Kanal wird per AllocConsole ein nicht modales Windows-Konsolenfenster erzeugt.",
            "Stage 109: Der Console-Screen-Buffer umfasst 500 Zeilen Scroll-Back; das Windows-Console-Host-Fenster unterstuetzt Mausrad-Scrollen und automatisches Weiterscrollen am Pufferende.",
            "Stage 109: Beim GUI-Shutdown wird die native Konsole per FreeConsole wieder geschlossen; DEBUG-Ausgabe bleibt im Qt-DEBUG-Kanal.",
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
    "DBaseSourceLocation",
    "DBaseIncludeLineManager",
    "remap_dbase_source_error",
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
    "DBaseSetSpeechStatement",
    "DBaseSayStatement",
    "DBaseSetColorStatement",
    "DBaseSetBackgroundStatement",
    "DBaseClearScreenStatement",
    "DBaseSetBorderColorStatement",
    "DBaseReturnStatement",
    "DBaseCallStatement",
    "DBaseCondition",
    "DBaseIfBranch",
    "DBaseIfStatement",
    "DBaseTryStatement", "DBaseCatchClause", "DBaseThrowStatement",
    "DBaseRoutineDefinition",
    "DBaseClassDefinition",
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
    constructor_arguments: Tuple[DBaseExpression, ...] = ()


@dataclass(frozen=True)
class DBaseNativePropertyStatement:
    target: DBaseObjectPath
    property_name: str
    declaring_class: str
    value_type: str
    expression: Optional[DBaseExpression]
    print_result: bool
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
# Stage 600: native classes reuse the real runtime/jitObject.h VMT layout.
_DBASE_NEW_CLASS_RE = re.compile(
    rf"(?i)^\s*({_DBASE_OBJECT_PATH_TEXT})\s*=\s*new\s+([A-Za-z_]\w*)\s*\(\s*(.*?)\s*\)\s*$"
)
_DBASE_LOCAL_CLASS_RE = re.compile(
    r"(?i)^\s*LOCAL\s+([A-Za-z_]\w*)\s+AS\s+([A-Za-z_]\w*)\s*$"
)
_DBASE_NATIVE_METHOD_RE = re.compile(
    rf"(?i)^\s*(?:(\?)\s*|STORE\s+)?"
    rf"({_DBASE_OBJECT_PATH_TEXT})\.([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)?\s*\)"
    rf"\s*(?:TO\s+([A-Za-z_]\w*))?\s*$"
)
_DBASE_NATIVE_USER_METHOD_RE = re.compile(
    rf"(?i)^\s*({_DBASE_OBJECT_PATH_TEXT})\.([A-Za-z_]\w*)\s*\((.*)\)\s*$"
)
_DBASE_NATIVE_ASSIGN_RE = re.compile(
    rf"(?i)^\s*([A-Za-z_]\w*)\s*=\s*({_DBASE_OBJECT_PATH_TEXT})\."
    rf"([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)?\s*\)\s*$"
)

_DBASE_NATIVE_PROPERTY_READ_RE = re.compile(
    rf"(?i)^\s*\?\s*({_DBASE_OBJECT_PATH_TEXT})\.([A-Za-z_]\w*)\s*$"
)
_DBASE_NATIVE_PROPERTY_WRITE_RE = re.compile(
    rf"(?i)^\s*({_DBASE_OBJECT_PATH_TEXT})\.([A-Za-z_]\w*)\s*=\s*(.*?)\s*$"
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
    condition: DBaseExpression, *, env: Mapping[str, DBaseValue],
    routines: Mapping[str, DBaseRoutineDefinition], filename: str,
    call_stack: Tuple[str, ...],
) -> bool:
    value = _dbase_constant_expression_value(condition, env=env, routines=routines,
                                             filename=filename, call_stack=call_stack)
    return bool(Decimal(value.value))


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
            if isinstance(statement, (DBaseTryStatement, DBaseThrowStatement)):
                raise DBaseCompilerError(
                    "_app.menuFile kann TRY/CATCH/THROW nicht statisch auswerten.",
                    line=statement.line, column=statement.column, filename=filename)
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
                                      DBaseSetDebugStatement, DBaseSetColorStatement, DBaseSetSpeechStatement, DBaseSayStatement,
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
    if isinstance(expression, DBaseCondition):
        left = _dbase_constant_expression_value(expression.left, env=env, routines=routines,
                                                filename=filename, call_stack=call_stack)
        right = _dbase_constant_expression_value(expression.right, env=env, routines=routines,
                                                 filename=filename, call_stack=call_stack)
        return DBaseValue("number", Decimal(int(_compare_dbase_values(left, right,
              expression.operator, line=expression.line, column=expression.column,
              filename=filename))))
    if isinstance(expression, DBaseUnaryExpression):
        operand = _dbase_constant_expression_value(
            expression.operand, env=env, routines=routines, filename=filename, call_stack=call_stack
        )
        if operand.kind != "number":
            raise DBaseCompilerError(
                f"_app.menuFile: unaerer Operator '{expression.operator}' erwartet eine Zahl.",
                line=expression.line, column=expression.column, filename=filename,
            )
        value = Decimal(int(operand.value)) if operand.kind == "logical" else Decimal(operand.value)
        kind = "logical" if expression.operator == ".not." and operand.kind == "logical" else "number"
        result = (Decimal(int(not bool(value))) if expression.operator == ".not."
                  else value if expression.operator == "+" else -value)
        return DBaseValue(kind, bool(result) if kind == "logical" else result)
    if isinstance(expression, DBaseBinaryExpression):
        if expression.operator in {".and.", ".or.", ".xor."}:
            left = _dbase_constant_expression_value(expression.left, env=env, routines=routines,
                                                     filename=filename, call_stack=call_stack)
            if left.kind != "number":
                raise DBaseCompilerError("Logischer Operator erwartet numerischen Wert.",
                                         line=expression.line, column=expression.column, filename=filename)
            a = bool(left.value)
            result_kind = "logical" if left.kind == "logical" else "number"
            if (expression.operator == ".and." and not a) or (expression.operator == ".or." and a):
                return DBaseValue(result_kind, a if result_kind == "logical" else Decimal(int(a)))
            right = _dbase_constant_expression_value(expression.right, env=env, routines=routines,
                                                      filename=filename, call_stack=call_stack)
            if right.kind != "number":
                raise DBaseCompilerError("Logischer Operator erwartet numerischen Wert.",
                                         line=expression.line, column=expression.column, filename=filename)
            b = bool(right.value)
            result_kind = "logical" if left.kind == right.kind == "logical" else "number"
            result = (a != b if expression.operator == ".xor."
                      else a and b if expression.operator == ".and." else a or b)
            return DBaseValue(result_kind, result if result_kind == "logical" else Decimal(int(result)))
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


# Stage 602: Deklarationen und ausfuehrbare Methoden aus dem PRG-Quellstrom
# extrahieren; Zeilenpositionen, Funktionskoerper und Klassen-VMT beibehalten.
# Die native Methoden-Codegenerierung steht in d64dbase/object_abi.py.
_DBASE_CLASS_HEAD = re.compile(
    r"^\s*CLASS\s+([A-Za-z_]\w*)(?:\s+OF\s+([A-Za-z_]\w*))?"
    r"\s*(ENDCLASS)?\s*$", re.I
)
_DBASE_CLASS_END = re.compile(r"^\s*ENDCLASS\s*$", re.I)
_DBASE_CLASS_COMMENT = re.compile(r"^\s*(?://|&&|\*\*)")


def _extract_dbase_class_definitions(source: str, *, filename: str):
    """Extract CLASS members, including executable dBASE method bodies.

    Methods terminate at their top-level RETURN; IF/ELSE/ENDIF may appear
    before it. The source is masked only after its original positions have
    been retained. FFI prototypes are checked during native code generation.
    """
    from .class_model import DBaseClassError, DBaseClassRegistry
    from .object_abi import NativeClassMethod, NativeClassProperty, validate_methods
    from dataclasses import replace

    cleaned_source = strip_dbase_comments(source, filename=filename)
    lines = source.splitlines(keepends=True)
    cleaned_lines = cleaned_source.splitlines(keepends=True)
    masked = list(lines)
    classes = []
    registry = DBaseClassRegistry()
    current = None
    active = None
    signatures = re.compile(
        r"^\s*(procedure|function)\s+([A-Za-z_]\w*)"
        r"(?:\s*\(\s*([A-Za-z_]\w*)?\s*\))?\s*$", re.I)
    legacy_type = re.compile(r"^\s*RETURN\s+(PVOID|LPCSTR|CINT|BOOL|CBOOL|VOID)\s*$", re.I)
    for index, raw in enumerate(lines):
        lineno = index + 1
        code = cleaned_lines[index].rstrip("\r\n").strip()
        if current is None:
            if not re.match(r"^(?:CLASS|ENDCLASS)\b", code, re.I):
                continue
            if _DBASE_CLASS_END.fullmatch(code):
                raise DBaseCompilerError("ENDCLASS ohne passende CLASS-Deklaration.", line=lineno, column=1, filename=filename)
            header = _DBASE_CLASS_HEAD.fullmatch(code)
            if header is None:
                raise DBaseCompilerError("Erwartet: CLASS <Name> [OF <Basisklasse>|OF CUSTOM] [ENDCLASS].", line=lineno, column=1, filename=filename)
            name, parent = header.group(1), header.group(2) or "TObject"
            custom = parent.casefold() == "custom"
            try:
                info = registry.register(name, parent, custom=custom)
            except DBaseClassError as exc:
                raise DBaseCompilerError(str(exc), line=lineno, column=1, filename=filename) from exc
            classes.append(DBaseClassDefinition(info.name, info.parent, custom, lineno, 1))
            if not header.group(3):
                current = {'name': name, 'line': lineno, 'methods': [],
                           'properties': [], 'visibility': 'public'}
        elif _DBASE_CLASS_END.fullmatch(code):
            if active is not None:
                raise DBaseCompilerError(f"RETURN fehlt in {current['name']}.{active['name']}.", line=lineno, column=1, filename=filename)
            try:
                validate_methods(current['name'], tuple(current['methods']))
            except ValueError as exc:
                raise DBaseCompilerError(str(exc), line=lineno, column=1, filename=filename) from exc
            classes[-1] = replace(classes[-1], methods=tuple(current['methods']),
                                  properties=tuple(current['properties']))
            current = None
        elif not code:
            pass
        elif re.match(r"^CLASS\b", code, re.I):
            raise DBaseCompilerError("CLASS darf nicht verschachtelt werden.", line=lineno, column=1, filename=filename)
        elif active is None:
            visibility_line = re.fullmatch(r'(PUBLIC|PRIVATE)\s*', code, re.I)
            if visibility_line:
                current['visibility'] = visibility_line.group(1).casefold()
            else:
                property_line = re.fullmatch(
                    r'(?:(PUBLIC|PRIVATE)\s+)?(?:PROPERTY\s+)?'
                    r'([A-Za-z_]\w*)\s*(?:=\s*(.+))?', code, re.I)
                signature = signatures.fullmatch(code)
                if signature is not None:
                    kind, name, param = signature.groups()
                    active = {'kind': kind.casefold(), 'name': name,
                              'parameters': (param,) if param else (), 'line': lineno,
                              'body': [], 'if_depth': 0, 'try_depth': 0, 'pending': '', 'pending_line': lineno}
                elif property_line is not None and (
                    '=' in code or re.match(r'^(?:PUBLIC|PRIVATE|PROPERTY)\b', code, re.I)
                ):
                    declared_visibility, prop_name, prop_value = property_line.groups()
                    visibility = (declared_visibility or current['visibility']).casefold()
                    if any(prop.name.casefold() == prop_name.casefold() for prop in current['properties']):
                        raise DBaseCompilerError('Klassen-Property mehrfach deklariert: ' + prop_name,
                                                 line=lineno, column=1, filename=filename)
                    current['properties'].append(NativeClassProperty(
                        prop_name, visibility, (prop_value or '').strip(), lineno))
                else:
                    raise DBaseCompilerError(
                        'Klassenmember: PUBLIC/PRIVATE, PROPERTY, PROCEDURE oder FUNCTION erwartet.',
                        line=lineno, column=1, filename=filename)
        else:
            # Stage 647: an operator at the beginning of a physical line
            # continues the previous complete native-class expression.
            # Preserve its first source line in the diagnostic and do not
            # turn '+ ...' into an independent method statement.
            if code.startswith('+') and not active['pending'] and active['body']:
                previous_line, previous_stmt = active['body'][-1]
                active['body'][-1] = (previous_line, previous_stmt + ' ' + code)
                eol = raw[len(raw.rstrip("\r\n")):]
                masked[index] = _dbase_mask_line(raw.rstrip("\r\n")) + eol
                continue
            # Continuations of nested FFI calls, including multiline arguments.
            if active['pending']:
                active['pending'] += ' ' + code
            else:
                active['pending'] = code
                active['pending_line'] = lineno
            pending = active['pending']
            if pending.count('(') > pending.count(')'):
                pass
            elif pending.count('(') < pending.count(')'):
                raise DBaseCompilerError("Ueberzaehlige schliessende Klammer in Klassenmethode.",
                                         line=lineno, column=1, filename=filename)
            else:
                line_start = active['pending_line']
                active['pending'] = ''
                keyword = pending.split(None, 1)[0].casefold()
                if keyword == 'if':
                    active['if_depth'] += 1
                elif keyword == 'endif':
                    active['if_depth'] -= 1
                    if active['if_depth'] < 0:
                        raise DBaseCompilerError("ENDIF ohne IF in Klassenmethode.", line=lineno, column=1, filename=filename)
                elif keyword == 'else' and active['if_depth'] <= 0:
                    raise DBaseCompilerError("ELSE ohne IF in Klassenmethode.", line=lineno, column=1, filename=filename)
                elif keyword == 'try':
                    active['try_depth'] += 1
                elif keyword == 'endtry':
                    active['try_depth'] -= 1
                    if active['try_depth'] < 0:
                        raise DBaseCompilerError("ENDTRY ohne TRY in Klassenmethode.", line=lineno, column=1, filename=filename)
                elif keyword in ('catch', 'finally') and active['try_depth'] == 0:
                    raise DBaseCompilerError(f"{keyword.upper()} ohne TRY in Klassenmethode.", line=lineno, column=1, filename=filename)
                elif keyword in ('procedure', 'function') and signatures.fullmatch(pending):
                    raise DBaseCompilerError(f"RETURN fehlt in {current['name']}.{active['name']}.", line=lineno, column=1, filename=filename)
                active['body'].append((line_start, pending))
                if keyword == 'return' and active['if_depth'] == 0 and active['try_depth'] == 0:
                    content = tuple(active['body'])
                    type_hint = ''
                    # Backward compatibility: Stage 600 used RETURN PVOID as
                    # a signature-only placeholder, not a real expression.
                    if len(content) == 1 and (legacy := legacy_type.fullmatch(pending)):
                        type_hint = legacy.group(1).upper()
                        content = ()
                    elif len(content) == 1 and pending.casefold() == 'return' and active['kind'] == 'procedure':
                        # Legacy stubs without code retain their Stage-600 ABI.
                        content = ()
                    method = NativeClassMethod(active['kind'], active['name'],
                        active['parameters'], type_hint, active['line'], content)
                    current['methods'].append(method)
                    active = None
        if current is not None or re.match(r"^(?:CLASS|ENDCLASS)\b", code, re.I):
            eol = raw[len(raw.rstrip("\r\n")):]
            masked[index] = _dbase_mask_line(raw.rstrip("\r\n")) + eol
    if current is not None:
        raise DBaseCompilerError(f"ENDCLASS fehlt fuer CLASS {current['name']}.", line=current['line'], column=1, filename=filename)
    try:
        registry.validate()
    except DBaseClassError as exc:
        raise DBaseCompilerError(str(exc), filename=filename) from exc
    return "".join(masked), tuple(classes)


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
    parse_source, class_definitions = _extract_dbase_class_definitions(parse_source, filename=filename)
    lines = parse_source.splitlines(keepends=True)
    masked = list(lines)
    events: list[tuple[int, int, object, Tuple[object, ...]]] = []
    event_serial = 0
    native_object_type_map = {}
    user_native_calls: dict[int, DBaseNativeClassCallStatement] = {}
    inline_native_statements: dict[int, object] = {}
    for declaration in class_definitions:
        events.append((declaration.line, event_serial, declaration, ()))
        event_serial += 1

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

        from .object_abi import native_class_definitions
        native_classes = {obj.name.casefold(): obj.name for obj in native_class_definitions(class_definitions)}
        # A class referenced by NEW must exist as an explicit declaration;
        # built-in MENU/SESSION/DATABASE retain their independent paths.
        local_class = _DBASE_LOCAL_CLASS_RE.fullmatch(raw)
        if local_class and local_class.group(2).casefold() in native_classes:
            statement = DBaseLocalObjectDeclaration(local_class.group(1),
                native_classes[local_class.group(2).casefold()], line_no,
                max(1, raw.lower().find('local') + 1))
            masked[i] = _dbase_mask_line(raw) + raw_with_nl[len(raw):]
            events.append((line_no, event_serial, statement, ()))
            native_object_type_map[(local_class.group(1).casefold(),)] = native_classes[local_class.group(2).casefold()]
            event_serial += 1
            i += 1
            continue

        new_class = _DBASE_NEW_CLASS_RE.fullmatch(raw)
        if new_class and new_class.group(2).casefold() in native_classes:
            target_path = _dbase_object_path(new_class.group(1), line_no)
            raw_args = new_class.group(3).strip()
            constructor_args = ()
            if raw_args:
                # One typed dBASE expression, e.g. new Exception("file not found")
                expr = _dbase_parse_property_expression(
                    raw_args, raw_line=raw, parse_source=parse_source,
                    line_start_offset=sum(len(piece) for piece in lines[:i]),
                    line=line_no, filename=filename)
                constructor_args = (expr,)
            statement = DBaseNewObjectStatement(
                target_path, native_classes[new_class.group(2).casefold()],
                _dbase_parent_path(target_path), line_no, 1, constructor_args)
            native_object_type_map[target_path.canonical_parts] = statement.class_name
            # A harmless placeholder keeps NEW in its lexical TRY/IF body.
            # The AST rewrite below swaps it for the real native statement.
            inline_native_statements[line_no] = statement
            eol = raw_with_nl[len(raw):]
            masked[i] = f'? "__DBASE_NATIVE_OBJECT_{line_no}__"' + eol
            i += 1
            continue

        native_method = _DBASE_NATIVE_METHOD_RE.fullmatch(raw)
        native_assign = _DBASE_NATIVE_ASSIGN_RE.fullmatch(raw)
        if native_method or native_assign:
            if native_assign:
                result_name, object_name, method_name, argument_name = native_assign.groups()
                printable = False
            else:
                printable, object_name, method_name, argument_name, result_name = native_method.groups()
                printable = bool(printable)
            from .object_abi import METHOD_BY_NAME
            if method_name.casefold() in METHOD_BY_NAME:
                statement = DBaseNativeMethodStatement(
                    _dbase_object_path(object_name, line_no), method_name,
                    argument_name or '', result_name or '', printable, line_no, 1)
                # Keep the built-in native method at its lexical location too.
                inline_native_statements[line_no] = statement
                masked[i] = f'? "__DBASE_NATIVE_OBJECT_{line_no}__"' + raw_with_nl[len(raw):]
                i += 1
                continue

        # Stage 641: user-defined native CLASS methods must also be callable
        # from .prg code (and therefore propagate THROW back into TRY/CATCH).
        user_method = _DBASE_NATIVE_USER_METHOD_RE.fullmatch(raw)
        if user_method:
            path = _dbase_object_path(user_method.group(1), line_no)
            owner_class = native_object_type_map.get(path.canonical_parts)
            if owner_class:
                class_index = {item.name.casefold(): item for item in class_definitions}
                visited = set()
                current = class_index.get(owner_class.casefold())
                found = None
                declaring_class = ''
                while current is not None and current.name.casefold() not in visited:
                    visited.add(current.name.casefold())
                    found = next((method for method in current.methods
                                  if method.name.casefold() == user_method.group(2).casefold()), None)
                    if found is not None:
                        declaring_class = current.name
                        break
                    current = class_index.get(current.parent.casefold())
                if found is not None:
                    arg_raw = user_method.group(3).strip()
                    argument = (_dbase_parse_property_expression(
                        arg_raw, raw_line=raw, parse_source=parse_source,
                        line_start_offset=sum(len(piece) for piece in lines[:i]),
                        line=line_no, filename=filename) if arg_raw else None)
                    statement = DBaseNativeClassCallStatement(
                        path, declaring_class, found.name, argument, line_no, 1)
                    # Keep the original token in the Stage-12 parser so the
                    # call is placed *inside* its lexical TRY/IF/routine.
                    # Replace its parsed DBaseCallStatement recursively below.
                    user_native_calls[line_no] = statement
                    i += 1
                    continue

        read_property = _DBASE_NATIVE_PROPERTY_READ_RE.fullmatch(raw)
        write_property = _DBASE_NATIVE_PROPERTY_WRITE_RE.fullmatch(raw)
        match_property = read_property or write_property
        if match_property:
            object_path = _dbase_object_path(match_property.group(1), line_no)
            class_name = native_object_type_map.get(object_path.canonical_parts)
            if class_name:
                from .derived_class_abi import field_layout
                from types import SimpleNamespace
                known_classes = {item.name.casefold(): item for item in class_definitions}
                known_classes.setdefault('tobject', SimpleNamespace(
                    name='TObject', parent='', properties=()))
                try:
                    slots = field_layout(class_name, known_classes, 8 if target == 'pe64' else 4)
                except ValueError as exc:
                    raise DBaseCompilerError(str(exc), line=line_no, filename=filename) from None
                prop_entry = next(((p, owner, typ) for p, owner, _offset, typ in slots
                                   if p.name.casefold() == match_property.group(2).casefold()), None)
                if prop_entry is None:
                    raise DBaseCompilerError('Unbekannte Klassen-Property: ' + match_property.group(2),
                                             line=line_no, filename=filename)
                prop, owner, typ = prop_entry
                if prop.visibility == 'private':
                    raise DBaseCompilerError('PRIVATE PROPERTY darf nicht von ausserhalb gelesen/geschrieben werden: '
                                             + owner + '.' + prop.name,
                                             line=line_no, filename=filename)
                expression = None
                if write_property:
                    expression = _dbase_parse_property_expression(
                        write_property.group(3), raw_line=raw, parse_source=parse_source,
                        line_start_offset=sum(len(piece) for piece in lines[:i]),
                        line=line_no, filename=filename)
                statement = DBaseNativePropertyStatement(
                    object_path, prop.name, owner, typ, expression,
                    bool(read_property), line_no, 1)
                # Keep property reads/writes in enclosing TRY/IF blocks.
                inline_native_statements[line_no] = statement
                masked[i] = f'? "__DBASE_NATIVE_OBJECT_{line_no}__"' + raw_with_nl[len(raw):]
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
    if user_native_calls or inline_native_statements:
        from dataclasses import replace
        def replace_native_calls(items):
            converted = []
            for item in items:
                if isinstance(item, DBasePrintStatement) and item.line in inline_native_statements:
                    converted.append(inline_native_statements[item.line])
                    continue
                if isinstance(item, DBaseCallStatement) and item.line in user_native_calls:
                    call = user_native_calls[item.line]
                    if item.call.name.casefold() == (call.target.dotted + '.' + call.method_name).casefold():
                        converted.append(call)
                        continue
                if isinstance(item, DBaseTryStatement):
                    converted.append(replace(item,
                        try_body=replace_native_calls(item.try_body),
                        catches=tuple(replace(c, body=replace_native_calls(c.body)) for c in item.catches),
                        finally_body=replace_native_calls(item.finally_body)))
                elif isinstance(item, DBaseIfStatement):
                    converted.append(replace(item, branches=tuple(
                        replace(branch, body=replace_native_calls(branch.body))
                        for branch in item.branches)))
                elif isinstance(item, DBaseRoutineDefinition):
                    converted.append(replace(item, body=replace_native_calls(item.body)))
                else:
                    converted.append(item)
            return tuple(converted)
        return replace_native_calls(result)
    return tuple(result)


class _DBaseProgramAnalyzer(_Stage12ProgramAnalyzer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object_classes: Dict[Tuple[str, ...], str] = {}
        self.native_pointer_results: set[str] = set()
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
            if not isinstance(statement, (DBaseClassDefinition, DBaseNativeClassCallStatement, DBaseNativeMethodStatement, DBaseLocalObjectDeclaration, DBaseNewObjectStatement, DBaseSessionLoginStatement, DBaseNativePropertyStatement, DBaseObjectPropertyStatement, DBaseObjectMethodStatement, DBaseWithStatement, DBaseMenuFileStatement, DBaseAppColorStatement))
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
                for arg in statement.constructor_arguments:
                    info = self.analyze_expression(
                        arg, symbols=globals_work,
                        expression_info=self.expression_info,
                        call_bindings=self.call_bindings,
                    )
                    if info.kind not in _STRING_KINDS:
                        raise DBaseCompilerError(
                            'Nativer Klassenkonstruktor erwartet einen String.',
                            line=statement.line, filename=self.filename)
                expected_args = self.native_class_constructor_arity.get(class_name.casefold(), 0)
                if len(statement.constructor_arguments) != expected_args:
                    raise DBaseCompilerError(
                        f'Konstruktor {statement.class_name} erwartet {expected_args} Parameter.',
                        line=statement.line, filename=self.filename)
                if len(statement.target.canonical_parts) == 1:
                    declared = self.declared_object_classes.get(statement.target.canonical_parts[0].casefold())
                    if declared is not None and declared != class_name:
                        raise DBaseCompilerError(
                            f"Objekt '{statement.target.dotted}' ist als {declared} deklariert, nicht als {class_name}.",
                            line=statement.line, column=statement.column, filename=self.filename,
                        )
                self.object_classes[self._object_key(statement.target)] = class_name
                continue
            if isinstance(statement, DBaseNativePropertyStatement):
                if statement.expression is not None:
                    info = self.analyze_expression(
                        statement.expression, symbols=globals_work,
                        expression_info=self.expression_info,
                        call_bindings=self.call_bindings,
                    )
                    if statement.value_type == 'string' and info.kind not in _STRING_KINDS:
                        raise DBaseCompilerError('String-PROPERTY erwartet String/Char.',
                                                 line=statement.line, filename=self.filename)
                    if statement.value_type == 'number' and info.kind not in ('number', 'logical'):
                        raise DBaseCompilerError('Numerische PROPERTY erwartet Zahl.',
                                                 line=statement.line, filename=self.filename)
                continue
            if isinstance(statement, DBaseNativeClassCallStatement):
                object_key = self._object_key(statement.target)
                if object_key not in self.object_classes:
                    raise DBaseCompilerError(
                        f"Objekt '{statement.target.dotted}' wurde vor Methodenaufruf nicht erzeugt.",
                        line=statement.line, filename=self.filename)
                known = self.native_class_names
                if self.object_classes[object_key].casefold() not in known:
                    raise DBaseCompilerError("Benutzer-Methode erwartet native CLASS-Instanz.",
                                             line=statement.line, filename=self.filename)
                if statement.argument is not None:
                    info = self.analyze_expression(
                        statement.argument, symbols=globals_work,
                        expression_info=self.expression_info,
                        call_bindings=self.call_bindings)
                    if info.kind not in _STRING_KINDS | {"number"}:
                        raise DBaseCompilerError(
                            "Klassenmethode erwartet einen String oder numerischen Parameter.",
                            line=statement.line, filename=self.filename)
                continue
            if isinstance(statement, DBaseNativeMethodStatement):
                from .object_abi import METHOD_BY_NAME
                key = self._object_key(statement.target)
                if key not in self.object_classes or self.object_classes[key] in {'MENU', 'SESSION', 'DATABASE'}:
                    raise DBaseCompilerError(
                        f"Objekt '{statement.target.dotted}' wurde nicht als native Klasse erzeugt.",
                        line=statement.line, column=1, filename=self.filename)
                _, kind, params, result = METHOD_BY_NAME[statement.method_name.casefold()]
                if len(params) != bool(statement.argument_name):
                    raise DBaseCompilerError(
                        f"Methode {statement.method_name} erwartet {len(params)} Parameter.",
                        line=statement.line, column=1, filename=self.filename)
                if kind == 'procedure' and (statement.result_name or statement.print_result):
                    raise DBaseCompilerError('PROCEDURE hat keinen Rueckgabewert.',
                        line=statement.line, column=1, filename=self.filename)
                if statement.print_result and result == 'PVOID':
                    raise DBaseCompilerError('Rohzeiger kann nicht als dBASE-Text ausgegeben werden.',
                        line=statement.line, column=1, filename=self.filename)
                if statement.argument_name:
                    allowed_classes = self.native_class_names
                    if statement.argument_name.casefold() not in allowed_classes and statement.argument_name.casefold() not in self.native_pointer_results:
                        raise DBaseCompilerError('InheritsFrom erwartet einen Klassennamen oder TClass-Zeiger.',
                            line=statement.line, column=1, filename=self.filename)
                if statement.result_name:
                    result_key = statement.result_name.casefold()
                    if result == 'PVOID':
                        self.native_pointer_results.add(result_key)
                    else:
                        kind_value = 'string' if result == 'LPCSTR' else 'number'
                        old = globals_work.get(result_key)
                        label = old.label if old else self.global_labels.setdefault(result_key, _symbol_label(statement.result_name))
                        state = _DBaseSymbolState(statement.result_name, label, kind_value,
                            None, True, statement.line, statement.column)
                        globals_work[result_key] = state
                        self.all_global_states[result_key] = state
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


def _analyze_program(statements: Tuple[object, ...], *, filename: str, ffi_prototypes=()) -> _DBaseAnalysis:
    runtime_statements = tuple(s for s in statements if not isinstance(s, DBaseClassDefinition))
    analyzer = _DBaseProgramAnalyzer(runtime_statements, filename=filename, ffi_prototypes=ffi_prototypes)
    analyzer.exception_types = _dbase_exception_hierarchy(statements)
    from .object_abi import native_class_definitions
    native_definitions = native_class_definitions(
        tuple(s for s in statements if isinstance(s, DBaseClassDefinition)))
    analyzer.native_class_names = {s.name.casefold() for s in native_definitions}
    analyzer.native_class_constructor_arity = {
        s.name.casefold(): next((len(m.parameters) for m in s.methods
                                if m.name.casefold() == '__ini__'), 0)
        for s in native_definitions
    }
    return analyzer.run()


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

    def __init__(self, statements, analysis, **kwargs):
        # Klassen-Metadaten bleiben verfuegbar fuer die VMT-Ausgabe nach der
        # normalen Programmgenerierung; nur Top-Level-Code wird gefiltert.
        from .object_abi import native_class_definitions
        explicit_classes = tuple(s for s in statements if isinstance(s, DBaseClassDefinition))
        self.native_class_definitions = native_class_definitions(explicit_classes)
        def contains_exceptions(sequence):
            for item in sequence:
                if isinstance(item, (DBaseTryStatement, DBaseThrowStatement)):
                    return True
                if isinstance(item, DBaseCallStatement) and item.call.name.casefold() in (*_WIN32_RAISE_BUILTINS, "win32checkfile"):
                    return True
                if isinstance(item, DBaseClassDefinition) and any(
                        any(re.match(r'(?i)^\s*(?:try|throw)\b', raw)
                            for _line, raw in method.body)
                        for method in item.methods):
                    return True
                if isinstance(item, DBaseRoutineDefinition) and contains_exceptions(item.body):
                    return True
                if isinstance(item, DBaseIfStatement) and any(
                        contains_exceptions(branch.body) for branch in item.branches):
                    return True
            return False
        self._has_managed_exceptions = contains_exceptions(statements)
        def uses_win32_errors(sequence):
            for item in sequence:
                if isinstance(item, DBaseCallStatement) and item.call.name.casefold() in (*_WIN32_RAISE_BUILTINS, "win32checkfile"):
                    return True
                if isinstance(item, DBaseRoutineDefinition) and uses_win32_errors(item.body):
                    return True
                if isinstance(item, DBaseTryStatement) and (uses_win32_errors(item.try_body) or
                        any(uses_win32_errors(c.body) for c in item.catches) or
                        uses_win32_errors(item.finally_body)):
                    return True
                if isinstance(item, DBaseIfStatement) and any(uses_win32_errors(b.body) for b in item.branches):
                    return True
            return False
        self._uses_win32_errors = uses_win32_errors(statements)
        def uses_win32_file_check(sequence):
            for item in sequence:
                if isinstance(item, DBaseCallStatement) and item.call.name.casefold() == "win32checkfile":
                    return True
                if isinstance(item, DBaseRoutineDefinition) and uses_win32_file_check(item.body):
                    return True
                if isinstance(item, DBaseTryStatement) and (uses_win32_file_check(item.try_body) or
                        any(uses_win32_file_check(c.body) for c in item.catches) or
                        uses_win32_file_check(item.finally_body)):
                    return True
                if isinstance(item, DBaseIfStatement) and any(uses_win32_file_check(b.body) for b in item.branches):
                    return True
            return False
        self._uses_win32_file_check = uses_win32_file_check(statements)
        if self._has_managed_exceptions:
            from .object_abi import NativeClassProperty
            native_by_name = {c.name.casefold(): c for c in self.native_class_definitions}
            # For a standalone .prg without #include System.SysUtils, make the
            # same real TObject-compatible VMT available for base exceptions.
            synthetic = []
            if 'exception' not in native_by_name:
                synthetic.append(DBaseClassDefinition(
                    'Exception', 'TObject', False, 0, 0,
                    properties=(NativeClassProperty('Message', 'public', '"Error."'),
                                NativeClassProperty('Code', 'public', '0'))))
            if 'dbexception' not in native_by_name:
                synthetic.append(DBaseClassDefinition('DbException', 'Exception', False, 0, 0))
            if 'win32exception' not in native_by_name:
                synthetic.append(DBaseClassDefinition('Win32Exception', 'Exception', False, 0, 0))
            if 'win32fileexception' not in native_by_name:
                synthetic.append(DBaseClassDefinition('Win32FileException', 'Win32Exception', False, 0, 0))
            self.native_class_definitions += tuple(synthetic)
        self.native_class_names = {s.name.casefold() for s in self.native_class_definitions}
        runtime_statements = tuple(s for s in statements if not isinstance(s, DBaseClassDefinition))
        super().__init__(runtime_statements, analysis, **kwargs)
        self.exception_types = _dbase_exception_hierarchy(tuple(statements))
        self.object_slots: Dict[Tuple[str, ...], str] = {}

    def _native_method_raise_helpers(self) -> tuple[str, str]:
        """C-ABI bridge from native CLASS methods to Stage-640 TObject throws.

        The message argument is an ANSI NUL-terminated string.  Reuse the
        existing exception-object builder so ownership, Message, and cleanup
        stay identical to a PRG-level THROW NEW statement.
        """
        reg = "rax" if self.is64 else "eax"
        ptr = "qword ptr" if self.is64 else "dword ptr"
        start = len(self.lines)
        emit = lambda *lines: self.lines.extend(lines)
        data = []
        class_keys = {cls.name.casefold() for cls in self.native_class_definitions}
        for key, (class_name, _parent, type_id) in self.exception_types.items():
            if key not in class_keys:
                continue
            class_label = f"__dbase_native_throw_class_{key}"
            literal = class_name.encode("cp1252")
            data.extend((f"{class_label}:",
                         "    db " + ", ".join(str(byte) for byte in literal + b"\0")))
            begin = f"__dbase_raise_{key}"
            emit(f"{begin}:", "    push rbp" if self.is64 else "    push ebp",
                      "    mov rbp, rsp" if self.is64 else "    mov ebp, esp")
            if self.is64:
                emit("    sub rsp, 72", "    mov qword ptr [rbp-8], rcx",
                          "    mov rax, qword ptr [rbp-8]")
            else:
                emit("    mov eax, dword ptr [ebp+8]")
            is_valid = self.new_label("method_throw_text")
            emit(f"    test {reg}, {reg}", f"    jnz {is_valid}",
                      f"    mov {reg}, __dbase_cls_empty", f"{is_valid}:")
            emit(f"    mov {ptr} [__dbase_exception_message_ptr], {reg}")
            if self.is64:
                emit("    mov rcx, rax", "    sub rsp, 40",
                          "    call __dbase_exc_strlenA", "    add rsp, 40")
            else:
                emit("    push eax", "    call __dbase_exc_strlenA", "    add esp, 4")
            emit("    mov dword ptr [__dbase_exception_message_len], eax")
            if self.is64:
                emit(f"    mov rax, {class_label}",
                     "    mov qword ptr [__dbase_exception_class_ptr], rax")
            else:
                emit(f"    mov dword ptr [__dbase_exception_class_ptr], {class_label}")
            emit(f"    mov dword ptr [__dbase_exception_class_len], {len(literal)}",
                 f"    mov dword ptr [__dbase_exception_id], {type_id}",
                 "    mov dword ptr [__dbase_exception_code], 0",
                 f"    mov {ptr} [__dbase_exception_object_ptr], 0")
            self.emit_build_exception_object(key)
            emit("    mov rsp, rbp" if self.is64 else "    mov esp, ebp",
                      "    pop rbp" if self.is64 else "    pop ebp", "    ret")
        generated = tuple(self.lines[start:])
        del self.lines[start:]
        return "\n".join(generated), "\n".join(data)

    def _emit_exception_cstr(self, source_slot="__dbase_exception_message") -> None:
        """Create a zero-terminated temporary copy for the native constructor.

        dBL string value slots are not NUL-terminated; passing them directly to
        the JitVmt string constructor would read past their bounds.
        """
        if self.is64:
            self.emit(f"    mov ecx, dword ptr [{source_slot}_len]")
            self.emit("    inc rcx")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_malloc")
            self.emit("    add rsp, 40")
            self.emit("    mov qword ptr [__dbase_exception_cstr_ptr], rax")
            skip = self.new_label("exception_oom")
            self.emit("    test rax, rax")
            self.emit(f"    je {skip}")
            self.emit("    mov rcx, rax")
            self.emit(f"    mov rdx, qword ptr [{source_slot}_ptr]")
            self.emit(f"    mov r8d, dword ptr [{source_slot}_len]")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_memcpy")
            self.emit("    add rsp, 40")
            self.emit("    mov r11, qword ptr [__dbase_exception_cstr_ptr]")
            self.emit(f"    mov eax, dword ptr [{source_slot}_len]")
            self.emit("    mov byte ptr [r11+rax], 0")
            self.emit(f"{skip}:")
        else:
            self.emit(f"    mov ecx, dword ptr [{source_slot}_len]")
            self.emit("    inc ecx")
            self.emit("    push ecx")
            self.emit("    call __dbase_malloc")
            self.emit("    add esp, 4")
            self.emit("    mov dword ptr [__dbase_exception_cstr_ptr], eax")
            skip = self.new_label("exception_oom")
            self.emit("    test eax, eax")
            self.emit(f"    je {skip}")
            self.emit(f"    push dword ptr [{source_slot}_len]")
            self.emit(f"    push dword ptr [{source_slot}_ptr]")
            self.emit("    push eax")
            self.emit("    call __dbase_memcpy")
            self.emit("    add esp, 12")
            self.emit("    mov edx, dword ptr [__dbase_exception_cstr_ptr]")
            self.emit(f"    mov eax, dword ptr [{source_slot}_len]")
            self.emit("    mov byte ptr [edx+eax], 0")
            self.emit(f"{skip}:")

    def _exception_native_constructor(self, class_key: str):
        """Nearest inherited __ini__ signature used by the native factory."""
        definitions = {c.name.casefold(): c for c in self.native_class_definitions}
        current = definitions.get(class_key)
        visited = set()
        while current and current.name.casefold() not in visited:
            visited.add(current.name.casefold())
            for method in getattr(current, 'methods', ()):
                if method.name.casefold() == '__ini__':
                    return method
            current = definitions.get(current.parent.casefold())
        return None

    def emit_build_exception_object(self, class_key: str, *, preinit_code=False) -> None:
        """Build a JitVmt instance using the real native class factory.

        THROW e moves exactly this pointer back into the pending slot; object
        identity therefore survives catch/rethrow and typed subclass dispatch.
        """
        from .object_abi import method_label
        native = {c.name.casefold(): c for c in self.native_class_definitions}
        if class_key not in native:
            raise AssertionError(f"Missing exception class factory: {class_key}")
        ctor = self._exception_native_constructor(class_key)
        has_arg = ctor is not None and len(ctor.parameters) == 1
        if ctor is not None and len(ctor.parameters) > 1:
            raise DBaseCompilerError("Exception.__ini__ unterstuetzt maximal eine Meldung.",
                                     filename=self.filename)
        self._emit_exception_cstr()
        # Synthetic built-in Win32 exception classes can have no __ini__.
        # They use the default factory followed by the ordinary Code setter.
        preinit_code = bool(preinit_code and has_arg and class_key in
                             {'win32exception', 'win32fileexception'})
        factory = method_label(native[class_key].name,
            'create_with_code' if preinit_code else 'create')
        if self.is64:
            if has_arg:
                self.emit("    mov rcx, qword ptr [__dbase_exception_cstr_ptr]")
            if preinit_code:
                self.emit("    mov edx, dword ptr [__dbase_exception_code]")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {factory}")
            self.emit("    add rsp, 40")
            self.emit("    mov qword ptr [__dbase_exception_object_ptr], rax")
        else:
            if preinit_code:
                self.emit("    push dword ptr [__dbase_exception_code]")
            if has_arg:
                self.emit("    push dword ptr [__dbase_exception_cstr_ptr]")
            self.emit(f"    call {factory}")
            if has_arg or preinit_code:
                self.emit(f"    add esp, {4 * (int(has_arg) + int(preinit_code))}")
            self.emit("    mov dword ptr [__dbase_exception_object_ptr], eax")
        if not has_arg:
            # If no constructor is declared, still initialize Message through
            # the real inherited native setter (which creates an owned copy).
            if self.is64:
                self.emit("    mov rcx, qword ptr [__dbase_exception_object_ptr]")
                skip = self.new_label("exception_no_object")
                self.emit("    test rcx, rcx")
                self.emit(f"    jz {skip}")
                self.emit("    mov rdx, qword ptr [__dbase_exception_cstr_ptr]")
                self.emit("    sub rsp, 40")
                self.emit(f"    call {method_label('Exception', 'set_Message')}")
                self.emit("    add rsp, 40")
                self.emit(f"{skip}:")
            else:
                skip = self.new_label("exception_no_object")
                self.emit("    cmp dword ptr [__dbase_exception_object_ptr], 0")
                self.emit(f"    je {skip}")
                self.emit("    push dword ptr [__dbase_exception_cstr_ptr]")
                self.emit("    push dword ptr [__dbase_exception_object_ptr]")
                self.emit(f"    call {method_label('Exception', 'set_Message')}")
                self.emit("    add esp, 8")
                self.emit(f"{skip}:")
        # Sync the managed text view with the native Message property. If the
        # user-provided __ini__ decorates the message, CATCH sees that result.
        # Fallback keeps the original text if allocation failed.
        end = self.new_label("exception_message_ready")
        if self.is64:
            self.emit("    mov rcx, qword ptr [__dbase_exception_object_ptr]")
            self.emit("    test rcx, rcx")
            self.emit(f"    jz {end}")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {method_label('Exception', 'get_Message')}")
            self.emit("    add rsp, 40")
            self.emit("    test rax, rax")
            self.emit(f"    jz {end}")
            self.emit("    mov qword ptr [__dbase_exception_message_ptr], rax")
            self.emit("    mov rcx, rax")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_exc_strlenA")
            self.emit("    add rsp, 40")
            self.emit("    mov dword ptr [__dbase_exception_message_len], eax")
        else:
            self.emit("    cmp dword ptr [__dbase_exception_object_ptr], 0")
            self.emit(f"    je {end}")
            self.emit("    push dword ptr [__dbase_exception_object_ptr]")
            self.emit(f"    call {method_label('Exception', 'get_Message')}")
            self.emit("    add esp, 4")
            self.emit("    test eax, eax")
            self.emit(f"    jz {end}")
            self.emit("    mov dword ptr [__dbase_exception_message_ptr], eax")
            self.emit("    push eax")
            self.emit("    call __dbase_exc_strlenA")
            self.emit("    add esp, 4")
            self.emit("    mov dword ptr [__dbase_exception_message_len], eax")
        self.emit(f"{end}:")
        # Register the instance for deterministic destruction at program
        # cleanup. CATCH can rethrow the very same pointer, so releasing it on
        # handler exit would invalidate nested exceptions.
        self._emit_track_exception_object()
        # Free only the temporary argument buffer. The exception object owns
        # its own string and is intentionally retained while CATCH is active.
        if self.is64:
            self.emit("    mov rcx, qword ptr [__dbase_exception_cstr_ptr]")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_exc_free")
            self.emit("    add rsp, 40")
            self.emit("    mov qword ptr [__dbase_exception_cstr_ptr], 0")
        else:
            self.emit("    push dword ptr [__dbase_exception_cstr_ptr]")
            self.emit("    call __dbase_exc_free")
            self.emit("    add esp, 4")
            self.emit("    mov dword ptr [__dbase_exception_cstr_ptr], 0")

    def _emit_track_exception_object(self) -> None:
        skip = self.new_label("exception_track_done")
        if self.is64:
            self.emit("    cmp qword ptr [__dbase_exception_object_ptr], 0")
            self.emit(f"    je {skip}")
            self.emit("    mov ecx, 16")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_malloc")
            self.emit("    add rsp, 40")
            self.emit("    test rax, rax")
            self.emit(f"    jz {skip}")
            self.emit("    mov r11, qword ptr [__dbase_exception_object_ptr]")
            self.emit("    mov qword ptr [rax], r11")
            self.emit("    mov r11, qword ptr [__dbase_exception_objects_head]")
            self.emit("    mov qword ptr [rax+8], r11")
            self.emit("    mov qword ptr [__dbase_exception_objects_head], rax")
        else:
            self.emit("    cmp dword ptr [__dbase_exception_object_ptr], 0")
            self.emit(f"    je {skip}")
            self.emit("    push 8")
            self.emit("    call __dbase_malloc")
            self.emit("    add esp, 4")
            self.emit("    test eax, eax")
            self.emit(f"    jz {skip}")
            self.emit("    mov ecx, dword ptr [__dbase_exception_object_ptr]")
            self.emit("    mov dword ptr [eax], ecx")
            self.emit("    mov ecx, dword ptr [__dbase_exception_objects_head]")
            self.emit("    mov dword ptr [eax+4], ecx")
            self.emit("    mov dword ptr [__dbase_exception_objects_head], eax")
        self.emit(f"{skip}:")

    @staticmethod
    def _exception_cleanup_asm(is64: bool) -> str:
        if is64:
            return "\n".join((
                "__dbase_exception_cleanup_all:",
                "    push rbp", "    mov rbp, rsp", "    sub rsp, 64",
                "__dbase_exception_cleanup_next:",
                "    mov rax, qword ptr [__dbase_exception_objects_head]",
                "    test rax, rax", "    jz __dbase_exception_cleanup_done",
                "    mov qword ptr [rbp-8], rax",
                "    mov rdx, qword ptr [rax+8]",
                "    mov qword ptr [__dbase_exception_objects_head], rdx",
                "    mov rcx, qword ptr [rax]",
                "    test rcx, rcx", "    jz __dbase_exception_cleanup_node",
                "    call __dbase_exc_object_free",
                "__dbase_exception_cleanup_node:",
                "    mov rcx, qword ptr [rbp-8]", "    call __dbase_exc_free",
                "    jmp __dbase_exception_cleanup_next",
                "__dbase_exception_cleanup_done:",
                "    mov rsp, rbp", "    pop rbp", "    ret",
            ))
        return "\n".join((
            "__dbase_exception_cleanup_all:",
            "    push ebp", "    mov ebp, esp", "    push ebx",
            "__dbase_exception_cleanup_next:",
            "    mov ebx, dword ptr [__dbase_exception_objects_head]",
            "    test ebx, ebx", "    jz __dbase_exception_cleanup_done",
            "    mov eax, dword ptr [ebx+4]",
            "    mov dword ptr [__dbase_exception_objects_head], eax",
            "    mov eax, dword ptr [ebx]",
            "    test eax, eax", "    jz __dbase_exception_cleanup_node",
            "    push eax", "    call __dbase_exc_object_free", "    add esp, 4",
            "__dbase_exception_cleanup_node:",
            "    push ebx", "    call __dbase_exc_free", "    add esp, 4",
            "    jmp __dbase_exception_cleanup_next",
            "__dbase_exception_cleanup_done:",
            "    pop ebx", "    mov esp, ebp", "    pop ebp", "    ret",
        ))

    def emit_assignment(self, statement: DBaseAssignmentStatement) -> None:
        super().emit_assignment(statement)
        # A caught variable is a real exception object, not only a snapshot
        # of its Message property. Keep the native TObject field in sync when
        # assigning e.Message/e.error from dBL source.
        name = statement.name.casefold()
        if "." not in name:
            return
        variable, member = name.split(".", 1)
        if member not in {"message", "error"}:
            return
        prefix = next((context[variable] for context in reversed(self._caught_bindings)
                       if variable in context), None)
        if prefix is None:
            return
        self._emit_exception_cstr(prefix + "_message")
        skip = self.new_label("exception_set_skip")
        from .object_abi import method_label
        if self.is64:
            self.emit(f"    mov rcx, qword ptr [{prefix}_object_ptr]")
            self.emit("    test rcx, rcx")
            self.emit(f"    jz {skip}")
            self.emit("    mov rdx, qword ptr [__dbase_exception_cstr_ptr]")
            self.emit("    sub rsp, 40")
            self.emit(f"    call {method_label('Exception', 'set_Message')}")
            self.emit("    add rsp, 40")
            self.emit(f"{skip}:")
            self.emit("    mov rcx, qword ptr [__dbase_exception_cstr_ptr]")
            self.emit("    sub rsp, 40")
            self.emit("    call __dbase_exc_free")
            self.emit("    add rsp, 40")
            self.emit("    mov qword ptr [__dbase_exception_cstr_ptr], 0")
        else:
            self.emit(f"    cmp dword ptr [{prefix}_object_ptr], 0")
            self.emit(f"    je {skip}")
            self.emit("    push dword ptr [__dbase_exception_cstr_ptr]")
            self.emit(f"    push dword ptr [{prefix}_object_ptr]")
            self.emit(f"    call {method_label('Exception', 'set_Message')}")
            self.emit("    add esp, 8")
            self.emit(f"{skip}:")
            self.emit("    push dword ptr [__dbase_exception_cstr_ptr]")
            self.emit("    call __dbase_exc_free")
            self.emit("    add esp, 4")
            self.emit("    mov dword ptr [__dbase_exception_cstr_ptr], 0")

    def emit_user_call(self, expression: DBaseCallExpression) -> _DBaseCallBinding:
        binding = self._binding(expression)
        if binding.kind != 'ffi':
            return super().emit_user_call(expression)
        ffi = self.ffi_prototypes[expression.name.casefold()]
        # Materialize all arguments before touching the Win64 shadow space;
        # nested FUNCTION calls then preserve the normal stack alignment.
        from .ffi_types import ffi_type_info, ffi_return_instructions
        # Materialize arguments before modifying the Win64 shadow space.
        # String literals get their own zero-terminated native encoding; the
        # dBASE string storage is length-based and NOT necessarily C-terminated.
        native_string_labels = {}
        for index, (arg, slot, type_name) in enumerate(zip(expression.arguments, binding.argument_slots, ffi.argument_types)):
            typ = ffi_type_info(type_name)
            info = self.current_expression_info[arg]
            if typ.is_string_input and info.kind in ('string', 'char') and info.constant_value is not None:
                value = str(info.constant_value.value)
                data = (value.encode('utf-16-le') + b'\0\0') if typ.category == 'wide_string' else (value.encode('cp1252', errors='replace') + b'\0')
                label = self.ffi_string_literals.get(data)
                if label is None:
                    label = f'__dbase_ffi_text_{len(self.ffi_string_literals)}'
                    self.ffi_string_literals[data] = label
                native_string_labels[index] = label
            else:
                self.emit_store_expression_to_slot(arg, slot)
        if self.is64:
            count = len(binding.argument_slots)
            allocated = max(4, count) * 8
            allocated += 8 if allocated % 16 == 0 else 0
            self.emit(f'    sub rsp, {allocated}')
            for index, (arg_type, slot) in enumerate(zip(ffi.argument_types, binding.argument_slots)):
                register = ('rcx', 'rdx', 'r8', 'r9')[index] if index < 4 else 'rax'
                typ = ffi_type_info(arg_type)
                info = self.current_expression_info[expression.arguments[index]]
                if index in native_string_labels:
                    self.emit(f'    mov {register}, {native_string_labels[index]}')
                elif typ.is_string_input:
                    if info.kind == 'number':
                        self.emit(f'    xor {register}, {register}')
                    else:
                        self.emit(f'    mov {register}, qword ptr [{slot}_ptr]')
                else:
                    self.emit(f'    fld qword ptr [{slot}_num]')
                    self.emit('    fistp qword ptr [__dbase_ffi_return]')
                    # UINT/DWORD on Win64 must not sign-extend bit 31. Using
                    # a 32-bit destination automatically clears upper bits.
                    if typ.bits('pe64') == 32 and not typ.signed:
                        dest32 = ('ecx', 'edx', 'r8d', 'r9d')[index] if index < 4 else 'eax'
                        self.emit(f'    mov {dest32}, dword ptr [__dbase_ffi_return]')
                    else:
                        self.emit(f'    mov {register}, qword ptr [__dbase_ffi_return]')
                if index >= 4:
                    self.emit(f'    mov qword ptr [rsp+{index * 8}], rax')
            self.emit(f'    call {ffi.label}')
            self.emit(f'    add rsp, {allocated}')
        else:
            for index in range(len(binding.argument_slots) - 1, -1, -1):
                arg_type, slot = ffi.argument_types[index], binding.argument_slots[index]
                typ = ffi_type_info(arg_type)
                info = self.current_expression_info[expression.arguments[index]]
                if index in native_string_labels:
                    self.emit(f'    push {native_string_labels[index]}')
                elif typ.is_string_input:
                    if info.kind == 'number':
                        self.emit('    push 0')
                    else:
                        self.emit(f'    push dword ptr [{slot}_ptr]')
                else:
                    self.emit(f'    fld qword ptr [{slot}_num]')
                    if typ.bits('pe32') == 64:
                        # On x86 WINAPI an explicit int64 argument occupies
                        # two stack slots, pushed high DWORD before low DWORD.
                        self.emit('    fistp qword ptr [__dbase_ffi_return]')
                        self.emit('    push dword ptr [__dbase_ffi_return+4]')
                        self.emit('    push dword ptr [__dbase_ffi_return]')
                    else:
                        self.emit('    fistp dword ptr [__dbase_temp_number]')
                        self.emit('    push dword ptr [__dbase_temp_number]')
            self.emit(f'    call {ffi.label}')
            if ffi.calling_convention == 'cdecl':
                from .ffi import ffi_stack_argument_bytes
                cleanup = ffi_stack_argument_bytes(ffi.argument_types, target='pe32')
                if cleanup:
                    self.emit(f'    add esp, {cleanup}')
            # For stdcall the callee performs stack cleanup (ret N).
        if binding.return_kind == 'string':
            from .ffi_string_result import prg_ansi_result
            for instruction in prg_ansi_result(
                    binding.result_label, is64=self.is64,
                    prefix=self.new_label('ffi_ansi_result')):
                self.emit(instruction)
        else:
            for instruction in ffi_return_instructions(ffi.return_type, is64=self.is64):
                self.emit(instruction)
        return binding

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

    def emit_native_class_call(self, statement: DBaseNativeClassCallStatement) -> None:
        """Call user CLASS method with Self and forward pending managed exceptions."""
        from .object_abi import method_label
        object_slot = self._object_slot(statement.target)
        native = {cls.name.casefold(): cls for cls in self.native_class_definitions}
        owner = native[statement.declaring_class.casefold()]
        method = next(m for m in owner.methods
                      if m.name.casefold() == statement.method_name.casefold())
        if bool(method.parameters) != (statement.argument is not None):
            raise DBaseCompilerError(
                f"Methode {method.name} erwartet {len(method.parameters)} Parameter.",
                line=statement.line, filename=self.filename)
        text_arg, value_slot, pointer_slot = False, '', ''
        if statement.argument is not None:
            info = self.current_expression_info[statement.argument]
            value_slot = self.new_storage_slot('class_call_arg')
            self.emit_store_expression_to_slot(statement.argument, value_slot)
            if info.kind in _STRING_KINDS:
                # Methods use NUL-terminated ANSI strings, whereas the PRG
                # evaluator stores counted strings.  Save the owned temporary
                # in an independent slot: a nested THROW may reuse the global
                # exception cstr scratch variable.
                text_arg = True
                pointer_slot = self.new_storage_slot('class_call_cstr')
                self._emit_exception_cstr(value_slot)
                if self.is64:
                    self.emit('    mov rax, qword ptr [__dbase_exception_cstr_ptr]')
                    self.emit(f'    mov qword ptr [{pointer_slot}_ptr], rax')
                else:
                    self.emit('    mov eax, dword ptr [__dbase_exception_cstr_ptr]')
                    self.emit(f'    mov dword ptr [{pointer_slot}_ptr], eax')
            else:
                self.emit(f'    fld qword ptr [{value_slot}_num]')
                self.emit('    fistp dword ptr [__dbase_temp_number]')
        skipped = self.new_label('native_class_no_object')
        finished = self.new_label('native_class_return')
        if self.is64:
            self.emit(f'    mov rcx, qword ptr [{object_slot}]')
            self.emit('    test rcx, rcx')
            self.emit(f'    jz {skipped}')
            if statement.argument is not None:
                if text_arg:
                    self.emit(f'    mov rdx, qword ptr [{pointer_slot}_ptr]')
                else:
                    self.emit('    movsxd rdx, dword ptr [__dbase_temp_number]')
            self.emit('    sub rsp, 40')
            self.emit(f'    call {method_label(owner.name, method.name)}')
            self.emit('    add rsp, 40')
        else:
            self.emit(f'    cmp dword ptr [{object_slot}], 0')
            self.emit(f'    je {skipped}')
            if statement.argument is not None:
                if text_arg:
                    self.emit(f'    push dword ptr [{pointer_slot}_ptr]')
                else:
                    self.emit('    push dword ptr [__dbase_temp_number]')
            self.emit(f'    push dword ptr [{object_slot}]')
            self.emit(f'    call {method_label(owner.name, method.name)}')
            self.emit(f'    add esp, {8 if statement.argument is not None else 4}')
        self.emit(f'{skipped}:')
        if text_arg:
            if self.is64:
                self.emit(f'    mov rcx, qword ptr [{pointer_slot}_ptr]')
                self.emit('    sub rsp, 40')
                self.emit('    call __dbase_exc_free')
                self.emit('    add rsp, 40')
            else:
                self.emit(f'    push dword ptr [{pointer_slot}_ptr]')
                self.emit('    call __dbase_exc_free')
                self.emit('    add esp, 4')
        if self._has_managed_exceptions:
            self.emit_exception_check()
        self.emit(f'{finished}:')

    def emit_native_method(self, statement: DBaseNativeMethodStatement) -> None:
        """Dispatch via VMT on the real runtime object pointer (Self)."""
        from .object_abi import METHOD_BY_NAME, vmt_label
        from .ffi_string_result import prg_ansi_result
        index, kind, params, result_kind = METHOD_BY_NAME[statement.method_name.casefold()]
        object_slot = self._object_slot(statement.target)
        # A NULL/freed handle must never become CALL 0; the lookup can also
        # fail (invalid VMT).  Return zero/empty string on that path.
        null_label = self.new_label('native_method_null')
        done_label = self.new_label('native_method_done')
        if self.is64:
            self.emit(f'    mov rcx, qword ptr [{object_slot}]')
            self.emit('    test rcx, rcx')
            self.emit(f'    jz {null_label}')
            self.emit(f'    mov edx, {index}')
            self.emit('    sub rsp, 40')
            self.emit('    call __dbase_obj_jit_get_virtual_object')
            self.emit('    add rsp, 40')
            self.emit('    test rax, rax')
            self.emit(f'    jz {null_label}')
            self.emit('    mov r11, rax')
            self.emit(f'    mov rcx, qword ptr [{object_slot}]')
            if statement.argument_name:
                arg = statement.argument_name
                if arg.casefold() in self.native_class_names:
                    self.emit(f'    mov rdx, {vmt_label(arg)}')
                else:
                    self.emit(f'    mov rdx, qword ptr [{self._object_slot(_dbase_object_path(arg, statement.line))}]')
            self.emit('    sub rsp, 40')
            self.emit('    call r11')
            self.emit('    add rsp, 40')
        else:
            self.emit(f'    cmp dword ptr [{object_slot}], 0')
            self.emit(f'    je {null_label}')
            self.emit(f'    push {index}')
            self.emit(f'    push dword ptr [{object_slot}]')
            self.emit('    call __dbase_obj_jit_get_virtual_object')
            self.emit('    add esp, 8')
            self.emit('    test eax, eax')
            self.emit(f'    jz {null_label}')
            self.emit('    mov edx, eax')
            if statement.argument_name:
                arg = statement.argument_name
                if arg.casefold() in self.native_class_names:
                    self.emit(f'    push {vmt_label(arg)}')
                else:
                    self.emit(f'    push dword ptr [{self._object_slot(_dbase_object_path(arg, statement.line))}]')
            self.emit(f'    push dword ptr [{object_slot}]')
            self.emit('    call edx')
            self.emit('    add esp, 8' if statement.argument_name else '    add esp, 4')
        self.emit(f'    jmp {done_label}')
        self.emit(f'{null_label}:')
        self.emit('    xor rax, rax' if self.is64 else '    xor eax, eax')
        self.emit(f'{done_label}:')
        if statement.method_name.casefold() in {'free', 'freeinstance'}:
            self.emit(f'    mov {"qword" if self.is64 else "dword"} ptr [{object_slot}], 0')
        if result_kind == 'PVOID' and statement.result_name:
            result_slot = self._object_slot(_dbase_object_path(statement.result_name, statement.line))
            self.emit(f'    mov {"qword" if self.is64 else "dword"} ptr [{result_slot}], {"rax" if self.is64 else "eax"}')
        elif result_kind in ('CINT', 'BOOL') and (statement.result_name or statement.print_result):
            result_slot = (self.global_variable_labels[statement.result_name.casefold()]
                           if statement.result_name else self.new_storage_slot('native_number'))
            self.emit(f'    mov dword ptr [{result_slot}_num], eax')
            self.emit(f'    fild dword ptr [{result_slot}_num]')
            self.emit(f'    fstp qword ptr [{result_slot}_num]')
            self.emit(f'    mov dword ptr [{result_slot}_type], {_TYPE_NUMBER}')
            if statement.print_result:
                self.emit('    fld qword ptr [' + result_slot + '_num]')
                self.emit_write_number_from_st0('console')
        elif result_kind == 'LPCSTR' and (statement.result_name or statement.print_result):
            result_slot = (self.global_variable_labels[statement.result_name.casefold()]
                           if statement.result_name else self.new_storage_slot('native_text'))
            for instruction in prg_ansi_result(result_slot, is64=self.is64,
                                               prefix=self.new_label('class_cstr')):
                self.emit(instruction)
            if statement.print_result:
                self.emit_write_variable_text(result_slot, 'console')
        if statement.print_result:
            label, length = self.text_literal('\r\n')
            self.emit_write_static(label, length, 'console')
        if self._has_managed_exceptions:
            self.emit_exception_check()

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
        elif class_name.casefold() in self.native_class_names:
            from .object_abi import method_label
            factory = method_label(statement.class_name, 'create')
            if statement.constructor_arguments:
                argument_slot = self.new_storage_slot('ctor_arg')
                self.emit_store_expression_to_slot(statement.constructor_arguments[0], argument_slot)
                if self.is64:
                    self.emit(f'    mov rcx, qword ptr [{argument_slot}_ptr]')
                    self.emit('    sub rsp, 40')
                    self.emit(f'    call {factory}')
                    self.emit('    add rsp, 40')
                    self.emit(f'    mov qword ptr [{target_slot}], rax')
                else:
                    self.emit(f'    push dword ptr [{argument_slot}_ptr]')
                    self.emit(f'    call {factory}')
                    self.emit('    add esp, 4')
                    self.emit(f'    mov dword ptr [{target_slot}], eax')
            else:
                self.emit('    sub rsp, 40' if self.is64 else f'    call {factory}')
                if self.is64:
                    self.emit(f'    call {factory}')
                    self.emit('    add rsp, 40')
                    self.emit(f'    mov qword ptr [{target_slot}], rax')
                else:
                    self.emit(f'    mov dword ptr [{target_slot}], eax')
            if self._has_managed_exceptions:
                self.emit_exception_check()
            return
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

    def emit_native_property(self, statement: DBaseNativePropertyStatement) -> None:
        """Read/write public native CLASS fields through compiled ABI accessors."""
        def emit_many(*items):
            for item in items:
                self.emit(item)
        from .object_abi import method_label
        from .ffi_string_result import prg_ansi_result
        object_slot = self._object_slot(statement.target)
        is_string = statement.value_type == 'string'
        name = ('get_' if statement.print_result else 'set_') + statement.property_name
        label = method_label(statement.declaring_class, name)
        if statement.expression is not None:
            value_slot = self.new_storage_slot('native_property_value')
            self.emit_store_expression_to_slot(statement.expression, value_slot)
            if not is_string:
                emit_many(f'    fld qword ptr [{value_slot}_num]')
                emit_many('    fistp dword ptr [__dbase_temp_number]')
        skip = self.new_label('native_property_skip')
        if self.is64:
            emit_many(f'    mov rcx, qword ptr [{object_slot}]',
                      '    test rcx, rcx', f'    jz {skip}')
            if statement.expression is not None:
                if is_string:
                    emit_many(f'    mov rdx, qword ptr [{value_slot}_ptr]')
                else:
                    emit_many('    mov edx, dword ptr [__dbase_temp_number]')
            emit_many('    sub rsp, 40', f'    call {label}', '    add rsp, 40')
        else:
            emit_many(f'    cmp dword ptr [{object_slot}], 0', f'    je {skip}')
            if statement.expression is not None:
                if is_string:
                    emit_many(f'    push dword ptr [{value_slot}_ptr]')
                else:
                    emit_many('    push dword ptr [__dbase_temp_number]')
            emit_many(f'    push dword ptr [{object_slot}]', f'    call {label}',
                      f'    add esp, {8 if statement.expression is not None else 4}')
        if statement.print_result:
            done = self.new_label('native_property_done')
            emit_many(f'    jmp {done}', f'{skip}:',
                      '    xor rax, rax' if self.is64 else '    xor eax, eax',
                      f'{done}:')
        else:
            emit_many(f'{skip}:')
        if statement.print_result:
            if is_string:
                value = self.new_storage_slot('native_property_text')
                for instruction in prg_ansi_result(value, is64=self.is64,
                                                   prefix=self.new_label('native_prop_ansi')):
                    emit_many(instruction)
                self.emit_write_variable_text(value, 'console')
            else:
                emit_many('    mov dword ptr [__dbase_temp_number], eax',
                          '    fild dword ptr [__dbase_temp_number]')
                self.emit_write_number_from_st0('console')
            label_crlf, length = self.text_literal('\r\n')
            self.emit_write_static(label_crlf, length, 'console')

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
            elif isinstance(statement, DBaseNativePropertyStatement):
                flush()
                self.emit_native_property(statement)
                self.emit_shutdown_guard(routine_end_label)
            elif isinstance(statement, DBaseNativeClassCallStatement):
                flush()
                self.emit_native_class_call(statement)
                self.emit_shutdown_guard(routine_end_label)
            elif isinstance(statement, DBaseNativeMethodStatement):
                flush()
                self.emit_native_method(statement)
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
        if self.native_class_definitions and any(
                any(any(re.match(r'(?i)^\s*throw\b', text) for _ln, text in method.body)
                    for method in cls.methods)
                for cls in self.native_class_definitions):
            native_text, native_data = self._native_method_raise_helpers()
            if native_text:
                assembly = assembly.replace('section .data\n',
                                            native_text + '\nsection .data\n' + native_data + '\n', 1)
        marker = 'import DBaseQtShutdown, "libd64_qt5.dll", "DBaseQtShutdown"\n'
        extra = "".join(
            f'import {symbol}, "libd64_qt5.dll", "{symbol}"\n'
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

        if self.native_class_definitions and any(
            name in self.native_class_names for name in ('exception',)):
            marker = 'import __dbase_malloc, "msvcrt.dll", "malloc"\n'
            imports = ('import __dbase_exc_free, "msvcrt.dll", "free"\n'
                       'import __dbase_exc_strlenA, "kernel32.dll", "lstrlenA"\n'
                       'import __dbase_exc_object_free, "libd64_runtime.dll", "jit_object_free"\n')
            # The factory and setter use the C ABI, not the packed dBL slots.
            assembly = assembly.replace(marker, marker + imports, 1)
            # Emit the cleanup before the VMT-injection pass so object symbols
            # are in .text and the head pointer is a zero-filled .bss slot.
            assembly = assembly.replace('section .data\n',
                        self._exception_cleanup_asm(self.is64) + '\nsection .data\n', 1)
            assembly = assembly.rstrip() + ('\n__dbase_exception_objects_head:\n'
                                          '    resq 1\n' if self.is64 else
                                          '\n__dbase_exception_objects_head:\n    resd 1\n')
            # This is reached once, after DBaseQtExec and before DLL shutdown.
            assembly = assembly.replace('    call DBaseConsoleShutdown\n',
                                        '    call __dbase_exception_cleanup_all\n'
                                        '    call DBaseConsoleShutdown\n', 1)
        if self.native_class_definitions:
            from .object_abi import inject_class_assembly
            assembly = inject_class_assembly(assembly, self.native_class_definitions, target=self.target, ffi_prototypes=self.ffi_prototypes, filename=self.filename)
        if self.object_slots:
            object_data = []
            for label in dict.fromkeys(self.object_slots.values()):
                object_data.append(f"{label}:")
                # Object handles reside in .bss; initialized DD data is not
                # valid there and was rejected by the PE32/PE64 assembler.
                object_data.append("    resq 1" if self.is64 else "    resd 1")
            assembly = assembly.rstrip() + "\n" + "\n".join(object_data) + "\n"
        return assembly


# Öffentliche Exportliste der additiven Stage-13-Klassen.
for _name in (
    "DBaseObjectPath", "DBaseNewObjectStatement", "DBaseNativeClassCallStatement", "DBaseNativePropertyStatement", "DBaseSessionLoginStatement",
    "DBaseLocalObjectDeclaration", "DBaseObjectPropertyStatement", "DBaseObjectMethodStatement", "DBaseMenuFileStatement",
    "DBaseAppColorStatement", "DBASE_SYSTEM_COLOR_NAMES",
    "DBaseSetColorStatement", "DBaseSetBackgroundStatement", "DBaseClearScreenStatement", "DBaseSetBorderColorStatement",
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
        if not isinstance(statement, (DBaseClassDefinition, DBaseNativeClassCallStatement, DBaseNativeMethodStatement, DBaseLocalObjectDeclaration, DBaseNewObjectStatement, DBaseSessionLoginStatement, DBaseNativePropertyStatement, DBaseObjectPropertyStatement, DBaseObjectMethodStatement, DBaseWithStatement, DBaseMenuFileStatement, DBaseAppColorStatement))
    )
    evaluator = _DBaseEvaluator(filtered, filename=filename)
    evaluator.exception_types = _dbase_exception_hierarchy(statements)
    evaluator.exception_class_definitions = {
        item.name.casefold(): item for item in statements
        if isinstance(item, DBaseClassDefinition)
    }
    return evaluator.run()

_stage12_compile_dbase_to_assembly = compile_dbase_to_assembly


def _stage609_dbase_peephole(result: DBaseCompileResult, target: str, options):
    from dataclasses import replace
    from windows_peephole import optimize_windows_assembly
    optimized = optimize_windows_assembly(
        result.assembly, target=target, options=options)
    return replace(result, assembly=optimized.assembly)


def compile_dbase_to_assembly(
    source: str,
    *,
    filename: str = "<dBase>",
    target: str = "pe32",
    windows_application_mode: str = "Console",
    workstation_mode: bool = False,
    debug_theme: str = "default",
    include_paths=(),
    source_kind: str = "program",
    peephole_options=None,
) -> DBaseCompileResult:
    if str(source_kind).casefold() == "library":
        from .dll_backend import compile_dbase_class_library
        library_result = compile_dbase_class_library(
            source, filename=filename, target=target,
            include_paths=include_paths, peephole_options=peephole_options,
        )
        return _stage609_dbase_peephole(library_result, target, peephole_options)
    if str(source_kind).casefold() != "program":
        raise DBaseCompilerError(
            f"Unbekannte dBASE-Quellart: {source_kind}", filename=filename,
        )
    result = _stage12_compile_dbase_to_assembly(
        source,
        filename=filename,
        target=target,
        windows_application_mode=windows_application_mode,
        workstation_mode=workstation_mode,
        debug_theme=debug_theme,
        include_paths=include_paths,
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
        "Stage 306: dBase .NOT., .AND., .XOR. und .OR. in IF/ELSEIF und numerischen Ausdruecken; Klammern, short-circuit fuer AND/OR und 0/1-Boolwerte.",
        "dBase-Ausbaustufe 29: Schliessen des Hauptfensters beendet alle Dialog-Eventloops und fuehrt den generierten Code ueber einen gemeinsamen Shutdown-/VirtualFree-Cleanup-Pfad.",
    )
    return DBaseCompileResult(
        assembly=_stage609_dbase_peephole(result, target, peephole_options).assembly,
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
