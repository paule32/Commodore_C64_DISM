from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
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
class DBaseFrontendResult:
    source: str
    comment_free_source: str
    comments: Tuple[DBaseComment, ...]
    target: str
    filename: str = "<dBase>"


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
class _DBaseAnalysis:
    expression_info: Mapping[DBaseExpression, _DBaseExpressionInfo]
    variables: Tuple[DBaseVariableInfo, ...]
    external_functions: Tuple[str, ...]
    console_transcript: str
    debug_transcript: str
    transcript_complete: bool
    uses_debug_output: bool


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
    return DBaseFrontendResult(
        source=text,
        comment_free_source=cleaned,
        comments=comments,
        target=normalized_target,
        filename=str(filename or "<dBase>"),
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
            "Erwartet wird '?' oder '??', eine Variablenzuweisung, SET FORMAT TO ... oder SET DEBUG ON/OFF.",
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


def parse_dbase_statements(
    source: str,
    *,
    filename: str = "<dBase>",
    target: str = "pe32",
) -> Tuple[object, ...]:
    """Parst ?/??, Variablenzuweisungen, SET FORMAT TO ... und SET DEBUG ON/OFF."""
    frontend = preprocess_dbase_source(source, filename=filename, target=target)
    cleaned = frontend.comment_free_source
    statements: list[object] = []

    for start, end in _logical_statement_ranges(frontend.source, frontend.comments):
        fragment = cleaned[start:end]
        if not fragment.strip():
            continue
        tokens = _tokenize_dbase_statement(
            fragment,
            filename=filename,
            base_offset=start,
            source=frontend.source,
        )
        parser = _DBaseExpressionParser(tokens, filename=filename)
        statements.append(parser.parse_statement())

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


def _analyze_expression(
    expression: DBaseExpression,
    *,
    symbols: Mapping[str, _DBaseSymbolState],
    expression_info: Dict[DBaseExpression, _DBaseExpressionInfo],
    external_functions: Dict[str, str],
    filename: str,
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
                f"Variable '{expression.name}' wurde vor ihrer Verwendung nicht zugewiesen.",
                line=expression.line,
                column=expression.column,
                filename=filename,
            )
        info = _DBaseExpressionInfo(
            kind=symbol.value_type,
            constant_value=symbol.constant_value,
            dynamic=symbol.dynamic,
            variable_label=symbol.label,
        )
    elif isinstance(expression, DBaseCallExpression):
        if expression.arguments:
            raise DBaseCompilerError(
                f"Funktionsaufruf '{expression.name}(...)': Parameter werden in dieser "
                "dBase-Stufe noch nicht unterstuetzt; no-arg Funktionen sind bereits linkbar.",
                line=expression.line,
                column=expression.column,
                filename=filename,
            )
        external_functions.setdefault(expression.name.casefold(), expression.name)
        info = _DBaseExpressionInfo(
            kind="number",
            constant_value=None,
            dynamic=True,
        )
    elif isinstance(expression, DBaseUnaryExpression):
        operand = _analyze_expression(
            expression.operand,
            symbols=symbols,
            expression_info=expression_info,
            external_functions=external_functions,
            filename=filename,
        )
        if operand.kind != "number":
            raise DBaseCompilerError(
                f"Unaerer Operator '{expression.operator}' erwartet eine Zahl.",
                line=expression.line,
                column=expression.column,
                filename=filename,
            )
        constant = None
        if operand.constant_value is not None:
            value = Decimal(operand.constant_value.value)
            constant = DBaseValue("number", value if expression.operator == "+" else -value)
        info = _DBaseExpressionInfo("number", constant, operand.dynamic)
    elif isinstance(expression, DBaseBinaryExpression):
        left = _analyze_expression(
            expression.left,
            symbols=symbols,
            expression_info=expression_info,
            external_functions=external_functions,
            filename=filename,
        )
        right = _analyze_expression(
            expression.right,
            symbols=symbols,
            expression_info=expression_info,
            external_functions=external_functions,
            filename=filename,
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
                    filename=filename,
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
                            filename=filename,
                        )
                    with localcontext() as context:
                        context.prec = 32
                        result = a / b
                else:
                    raise AssertionError(f"Unbekannter Operator: {operator}")
                constant = DBaseValue("number", result)
            info = _DBaseExpressionInfo(
                "number",
                constant,
                left.dynamic or right.dynamic,
            )
    else:
        raise AssertionError(f"Unbekannter dBase-Ausdrucksknoten: {type(expression)!r}")

    expression_info[expression] = info
    return info


def _preview_expression(
    expression: DBaseExpression,
    info_map: Mapping[DBaseExpression, _DBaseExpressionInfo],
) -> Optional[str]:
    info = info_map[expression]
    if info.constant_value is None:
        return None
    return _format_dbase_value(info.constant_value)


def _effective_output_target(format_target: str, debug_override: Optional[bool]) -> str:
    """Bestimmt den physischen Ausgabekanal fuer ?/??.

    CONSOLE schreibt standardmaessig nach stdout. SET DEBUG ON erzwingt stderr
    (IDE-DEBUG-Tab), SET DEBUG OFF erzwingt stdout. SCREEN bleibt als
    rueckwaertskompatibler Alias fuer DEBUG erhalten, solange kein explizites
    SET DEBUG OFF gesetzt wurde.
    """
    if debug_override is True:
        return "debug"
    if debug_override is False:
        return "console"
    return "debug" if str(format_target).casefold() == "screen" else "console"


def _analyze_program(
    statements: Tuple[object, ...],
    *,
    filename: str,
) -> _DBaseAnalysis:
    symbols: Dict[str, _DBaseSymbolState] = {}
    expression_info: Dict[DBaseExpression, _DBaseExpressionInfo] = {}
    external_functions: Dict[str, str] = {}
    console_chunks: list[str] = []
    debug_chunks: list[str] = []
    format_target = "console"
    debug_override: Optional[bool] = None
    transcript_complete = True
    uses_debug_output = False

    for statement in statements:
        if isinstance(statement, DBaseAssignmentStatement):
            info = _analyze_expression(
                statement.expression,
                symbols=symbols,
                expression_info=expression_info,
                external_functions=external_functions,
                filename=filename,
            )
            if info.kind in _STRING_KINDS and info.constant_value is None:
                raise DBaseCompilerError(
                    "Eine String-Zuweisung mit einem zur Laufzeit unbekannten Wert benoetigt "
                    "die spaetere dynamische String-Runtime. Konstante Strings und Variablen "
                    "sind bereits unterstuetzt.",
                    line=statement.line,
                    column=statement.column,
                    filename=filename,
                )
            key = statement.name.casefold()
            old = symbols.get(key)
            label = old.label if old is not None else _symbol_label(statement.name)
            symbols[key] = _DBaseSymbolState(
                name=statement.name,
                label=label,
                value_type=info.kind,
                constant_value=info.constant_value,
                dynamic=info.dynamic,
                last_line=statement.line,
                last_column=statement.column,
            )
            continue

        if isinstance(statement, DBaseSetFormatStatement):
            format_target = statement.target
            continue

        if isinstance(statement, DBaseSetDebugStatement):
            debug_override = bool(statement.enabled)
            continue

        if isinstance(statement, DBasePrintStatement):
            info = _analyze_expression(
                statement.expression,
                symbols=symbols,
                expression_info=expression_info,
                external_functions=external_functions,
                filename=filename,
            )
            output_target = _effective_output_target(format_target, debug_override)
            if output_target == "debug":
                uses_debug_output = True
            rendered = _preview_expression(statement.expression, expression_info)
            if rendered is None:
                transcript_complete = False
                continue
            chunks = debug_chunks if output_target == "debug" else console_chunks
            chunks.append(rendered)
            if statement.newline:
                chunks.append("\r\n")
            continue

        raise AssertionError(f"Unbekannte dBase-Anweisung: {type(statement)!r}")

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
        for symbol in symbols.values()
    )
    return _DBaseAnalysis(
        expression_info=dict(expression_info),
        variables=variables,
        external_functions=tuple(external_functions.values()),
        console_transcript="".join(console_chunks),
        debug_transcript="".join(debug_chunks),
        transcript_complete=transcript_complete,
        uses_debug_output=uses_debug_output,
    )


def _evaluate_dbase_expression(
    expression: DBaseExpression,
    *,
    filename: str,
    variables: Optional[Mapping[str, DBaseValue]] = None,
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
        raise DBaseCompilerError(
            f"Funktionsaufruf '{expression.name}(...)' ist ein Laufzeitwert und kann "
            "nicht konstant ausgewertet werden.",
            line=expression.line,
            column=expression.column,
            filename=filename,
        )
    if isinstance(expression, DBaseUnaryExpression):
        operand = _evaluate_dbase_expression(expression.operand, filename=filename, variables=env)
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
        left = _evaluate_dbase_expression(expression.left, filename=filename, variables=env)
        right = _evaluate_dbase_expression(expression.right, filename=filename, variables=env)
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


def evaluate_dbase_statements(
    statements: Tuple[object, ...],
    *,
    filename: str = "<dBase>",
) -> str:
    variables: Dict[str, DBaseValue] = {}
    chunks: list[str] = []
    for statement in statements:
        if isinstance(statement, DBaseAssignmentStatement):
            variables[statement.name.casefold()] = _evaluate_dbase_expression(
                statement.expression,
                filename=filename,
                variables=variables,
            )
        elif isinstance(statement, DBasePrintStatement):
            value = _evaluate_dbase_expression(
                statement.expression,
                filename=filename,
                variables=variables,
            )
            chunks.append(_format_dbase_value(value))
            if statement.newline:
                chunks.append("\r\n")
        elif isinstance(statement, (DBaseSetFormatStatement, DBaseSetDebugStatement)):
            continue
    return "".join(chunks)


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

    def emit_numeric_expression(self, expression: DBaseExpression) -> None:
        info = self.analysis.expression_info[expression]

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
            if self.is64:
                # Native Windows-x64 ABI: 32 Byte shadow space plus 8 Byte
                # Alignment, da _start vor dem CALL bei RSP=8 mod 16 liegt.
                self.emit("    sub rsp, 40")
                self.emit(f"    call {expression.name}")
                self.emit("    add rsp, 40")
                self.emit("    movsd qword ptr [__dbase_call_number], xmm0")
                self.emit("    fld qword ptr [__dbase_call_number]")
            else:
                self.emit(f"    call {expression.name}")
                # PE32/C-double ABI liefert den Wert bereits in ST0.
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

    def emit_write_number_from_st0(self, target: str) -> None:
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
        function = self._qt_writer_name(target)
        if self.is64:
            self.emit("    mov rcx, __dbase_format_buffer")
            # EDX enthaelt bereits die Zeichenanzahl.
            self.emit("    sub rsp, 40")
            self.emit(f"    call {function}")
            self.emit("    add rsp, 40")
        else:
            self.emit("    push edx")
            self.emit("    push __dbase_format_buffer")
            self.emit(f"    call {function}")
            self.emit("    add esp, 8")

    def emit_print_expression(self, expression: DBaseExpression, target: str) -> None:
        info = self.analysis.expression_info[expression]
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

        if isinstance(expression, DBaseBinaryExpression) and expression.operator == "+":
            self.emit_print_expression(expression.left, target)
            self.emit_print_expression(expression.right, target)
            return

        if info.constant_value is not None:
            label, length = self.text_literal(_format_dbase_value(info.constant_value))
            self.emit_write_static(label, length, target)
            return

        raise DBaseCompilerError(
            "Dynamischer String-Ausdruck kann in dieser Stufe nur direkt als '+'-Kette ausgegeben werden.",
            line=expression.line,
            column=expression.column,
            filename=self.filename,
        )

    def emit_assignment(self, statement: DBaseAssignmentStatement) -> None:
        info = self.analysis.expression_info[statement.expression]
        label = _symbol_label(statement.name)
        if info.kind == "number":
            self.emit_numeric_expression(statement.expression)
            self.emit(f"    fstp qword ptr [{label}_num]")
            self.emit(f"    mov dword ptr [{label}_type], {_TYPE_NUMBER}")
            return

        if info.constant_value is None:
            raise AssertionError("Nicht-konstante Stringzuweisung haette Analysefehler liefern muessen")
        text_value = _format_dbase_value(info.constant_value)
        text_label, length = self.text_literal(text_value)
        type_tag = _TYPE_CHAR if info.kind == "char" else _TYPE_STRING
        if self.is64:
            self.emit(f"    mov rax, {text_label}")
            self.emit(f"    mov qword ptr [{label}_ptr], rax")
        else:
            self.emit(f"    mov eax, {text_label}")
            self.emit(f"    mov dword ptr [{label}_ptr], eax")
        self.emit(f"    mov dword ptr [{label}_len], {length}")
        self.emit(f"    mov dword ptr [{label}_type], {type_tag}")

    def build(self) -> str:
        has_print = any(isinstance(s, DBasePrintStatement) for s in self.statements)

        self.emit("bits 64" if self.is64 else "bits 32")
        self.emit()
        # Stabile C-ABI-Bridge. d64qt5.dll bindet intern gegen Qt5Core,
        # Qt5Gui und Qt5Widgets; der generierte Assembler muss keine
        # compiler-/versionsabhaengigen C++-Mangled-Names importieren.
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
        if has_print:
            self.emit('import __dbase_gcvt, "msvcrt.dll", "_gcvt"')
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

        format_target = "console"
        debug_override: Optional[bool] = None
        debug_visible = False
        for statement in self.statements:
            if isinstance(statement, DBaseAssignmentStatement):
                self.emit_assignment(statement)
            elif isinstance(statement, DBaseSetFormatStatement):
                format_target = statement.target
            elif isinstance(statement, DBaseSetDebugStatement):
                debug_override = bool(statement.enabled)
                debug_visible = bool(statement.enabled)
                self.emit_qt_call1_int("DBaseQtSetDebugVisible", 1 if debug_visible else 0)
            elif isinstance(statement, DBasePrintStatement):
                output_target = _effective_output_target(format_target, debug_override)
                if output_target == "debug" and not debug_visible:
                    # SET FORMAT TO SCREEN bleibt kompatibel und nutzt den
                    # DEBUG-Tab, ohne irgendeine Textkonsole zu oeffnen.
                    self.emit_qt_call1_int("DBaseQtSetDebugVisible", 1)
                    debug_visible = True
                self.emit_print_expression(statement.expression, output_target)
                if statement.newline:
                    newline_label, newline_len = self.text_literal("\r\n")
                    self.emit_write_static(newline_label, newline_len, output_target)
                # Laengere Programme aktualisieren die Qt-Oberflaeche auch
                # waehrend der eigentlichen dBase-Ausfuehrung.
                self.emit_qt_call0("DBaseQtProcessEvents")
            else:
                raise AssertionError(type(statement))

        self.emit_qt_call0("DBaseQtMarkProgramFinished")
        self.emit_qt_call0("DBaseQtExec")
        if self.is64:
            self.emit("    mov dword ptr [__dbase_exit_code], eax")
        else:
            self.emit("    mov dword ptr [__dbase_exit_code], eax")
        self.emit_qt_call0("DBaseQtShutdown")
        if self.is64:
            self.emit("    mov ecx, dword ptr [__dbase_exit_code]")
            self.emit("    sub rsp, 40")
            self.emit("    call ExitProcess")
        else:
            self.emit("    push dword ptr [__dbase_exit_code]")
            self.emit("    call ExitProcess")

        self.data_lines = ["", "section .data", ""]
        for raw, label in self.double_literals.items():
            low, high = struct.unpack("<II", raw)
            self.data_lines.extend([f"{label}:", f"    dd {low}, {high}"])
        for payload, label in self.string_literals.items():
            # Qt bridge uses explicit length; only the window title needs NUL.
            nul = label == title_label
            self.data_lines.extend(_db_lines(label, payload, nul_terminate=nul))
        if has_print:
            self.data_lines.extend([
                "__dbase_temp_number:",
                "    dd 0",
                "__dbase_temp_number_hi:",
                "    dd 0",
                "__dbase_call_number:",
                "    dd 0, 0",
                "__dbase_format_buffer:",
                "    db " + ", ".join("0" for _ in range(96)),
            ])
        self.data_lines.extend([
            "__dbase_exit_code:",
            "    dd 0",
        ])

        for variable in self.analysis.variables:
            label = variable.label
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
    """Kompiliert dBase-Ausbaustufe 3 fuer Windows PE32 und PE32+.

    Implementiert:
    - //, **, && und /* ... */ Kommentare
    - ? <expr> und ?? <expr>
    - Variablenzuweisung ``Name = Ausdruck``
    - Zahl-, Hex-, Char- und Stringliterale
    - arithmetische + - * / Ausdruecke und String-Konkatenation
    - no-arg Funktionsaufrufe als externe numerische Symbole
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
        frontend.source,
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
    warnings: list[str] = []
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
            f"dBase-Ausbaustufe 3: Variablen und Runtime-Ausgabe fuer {target_label}.",
            "Variablen koennen Zahl/Hex, Char und String aufnehmen; Zuweisungen erzeugen echte Speicher-Slots.",
            "? fuegt CR/LF an; ?? schreibt ohne NewLine.",
            "Bei String/Char + Zahl wird die Zahl automatisch fuer die Textausgabe formatiert.",
            "Die erzeugte EXE baut ueber d64qt5.dll eine native Qt5-GUI mit Konsole- und DEBUG-Tab auf.",
            "Die beiden Ausgabeflaechen sind QPlainTextEdit; im DEBUG-Tab sitzt zusaetzlich eine QLineEdit-Eingabezeile.",
            "SET FORMAT TO CONSOLE + SET DEBUG ON leitet ?/?? in DEBUG; SET DEBUG OFF blendet DEBUG aus und schreibt wieder in Konsole.",
            "Nach der Programmausfuehrung bleibt die Qt-Ereignisschleife aktiv, bis das GUI-Fenster geschlossen wird.",
            "Hexliterale: 0xFF, $FF und 0FFh; die interne Rechenform ist numerisch.",
        ),
        warnings=tuple(warnings),
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
