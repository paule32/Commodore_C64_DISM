from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
import math
import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .optimizer import C64BasicOptimizer, normalize_print_strategy


class C64BasicError(Exception):
    """Fehler im C64-BASIC-Quelltext mit optionaler BASIC-Zeilennummer."""

    def __init__(self, message: str, line: Optional[int] = None):
        self.message = str(message)
        self.line = int(line) if line is not None else None
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.line is None:
            return self.message
        return f"BASIC-Zeile {self.line}: {self.message}"


@dataclass(frozen=True)
class C64BasicCompileResult:
    assembly: str
    warnings: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()
    source_kind: str = "program"


@dataclass(frozen=True)
class _ArrayInfo:
    name: str
    symbol: str
    dimensions: Tuple[int, ...]
    kind: str                 # float, integer, string
    element_size: int

    @property
    def element_count(self) -> int:
        count = 1
        for upper_bound in self.dimensions:
            count *= upper_bound + 1
        return count

    @property
    def byte_size(self) -> int:
        return self.element_count * self.element_size


Token = Tuple[str, object]
Node = Tuple

_FLOAT_FUNCTIONS = {"ABS", "INT", "SGN", "PEEK", "LEN", "VAL", "ASC"}
_STRING_FUNCTIONS = {"CHR$", "STR$"}
_COMPARISON_OPERATORS = ("<=", ">=", "<>", "=", "<", ">")


def _split_outside_quotes(text: str, delimiter: str = ":") -> List[str]:
    result: List[str] = []
    start = 0
    quoted = False
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            if quoted and index + 1 < len(text) and text[index + 1] == '"':
                index += 2
                continue
            quoted = not quoted
        elif char == delimiter and not quoted:
            result.append(text[start:index].strip())
            start = index + 1
        index += 1
    result.append(text[start:].strip())
    return result


def _split_top_level(text: str, delimiter: str = ",") -> List[str]:
    """Teilt außerhalb von Zeichenketten und Klammern."""
    result: List[str] = []
    start = 0
    quoted = False
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            if quoted and index + 1 < len(text) and text[index + 1] == '"':
                index += 2
                continue
            quoted = not quoted
        elif not quoted:
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(0, depth - 1)
            elif char == delimiter and depth == 0:
                result.append(text[start:index].strip())
                start = index + 1
        index += 1
    result.append(text[start:].strip())
    return result


def _split_basic_statements(text: str) -> List[str]:
    """Teilt eine BASIC-Zeile; hinter REM/Apostroph bleibt ':' Kommentartext."""
    result: List[str] = []
    remaining = text
    while remaining:
        stripped = remaining.lstrip()
        if stripped.startswith("'") or re.match(r"(?i)^REM(?:\s|$)", stripped):
            result.append(stripped)
            break
        quoted = False
        split_at = -1
        for index, char in enumerate(remaining):
            if char == '"':
                if quoted and index + 1 < len(remaining) and remaining[index + 1] == '"':
                    continue
                quoted = not quoted
            elif char == ":" and not quoted:
                split_at = index
                break
        if split_at < 0:
            result.append(remaining.strip())
            break
        result.append(remaining[:split_at].strip())
        remaining = remaining[split_at + 1:]
    return [item for item in result if item]


def _split_print_items(text: str) -> Tuple[List[Tuple[str, str]], str]:
    items: List[Tuple[str, str]] = []
    start = 0
    quoted = False
    depth = 0
    separator = ""
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            if quoted and index + 1 < len(text) and text[index + 1] == '"':
                index += 2
                continue
            quoted = not quoted
        elif not quoted:
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(0, depth - 1)
            elif depth == 0 and char in ";,":
                items.append((text[start:index].strip(), char))
                separator = char
                start = index + 1
        index += 1
    tail = text[start:].strip()
    if tail:
        items.append((tail, ""))
        separator = ""
    elif text.rstrip().endswith((";", ",")):
        separator = text.rstrip()[-1]
    return items, separator


def _find_top_level_comparison(text: str) -> Optional[Tuple[str, str, str]]:
    quoted = False
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            if quoted and index + 1 < len(text) and text[index + 1] == '"':
                index += 2
                continue
            quoted = not quoted
            index += 1
            continue
        if not quoted:
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(0, depth - 1)
            elif depth == 0:
                for operator in _COMPARISON_OPERATORS:
                    if text.startswith(operator, index):
                        return (
                            text[:index].strip(),
                            operator,
                            text[index + len(operator):].strip(),
                        )
        index += 1
    return None


def _tokenize_expression(text: str, line: int) -> List[Token]:
    tokens: List[Token] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char == "$":
            end = index + 1
            while end < length and text[end] in "0123456789abcdefABCDEF":
                end += 1
            if end == index + 1:
                raise C64BasicError("Ungültige Hexadezimalzahl.", line)
            tokens.append(("number", Decimal(int(text[index + 1:end], 16))))
            index = end
            continue
        if char == "%":
            end = index + 1
            while end < length and text[end] in "01":
                end += 1
            if end == index + 1:
                raise C64BasicError("Ungültige Binärzahl.", line)
            tokens.append(("number", Decimal(int(text[index + 1:end], 2))))
            index = end
            continue
        if char.isdigit() or (char == "." and index + 1 < length and text[index + 1].isdigit()):
            match = re.match(
                r"(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?",
                text[index:],
            )
            if match is None:
                raise C64BasicError("Ungültige Fließkommazahl.", line)
            literal = match.group(0)
            try:
                value = Decimal(literal)
            except InvalidOperation as exc:
                raise C64BasicError("Ungültige Fließkommazahl.", line) from exc
            tokens.append(("number", value))
            index += len(literal)
            continue
        if char.isalpha() or char == "_":
            end = index + 1
            while end < length and (text[end].isalnum() or text[end] in "_$%#!"):
                end += 1
            value = text[index:end].upper()
            if value in {"MOD", "AND", "OR"}:
                tokens.append(("op", value))
            else:
                tokens.append(("identifier", value))
            index = end
            continue
        pair = text[index:index + 2]
        if pair in {"<=", ">=", "<>"}:
            tokens.append(("op", pair))
            index += 2
            continue
        if char in "+-*/(),=<>":
            tokens.append(("comma" if char == "," else "op", char))
            index += 1
            continue
        raise C64BasicError(f"Ungültiges Zeichen im Ausdruck: {char!r}", line)
    tokens.append(("eof", ""))
    return tokens


class _ExpressionParser:
    PRECEDENCE = {
        "OR": 1,
        "AND": 2,
        "=": 3,
        "<>": 3,
        "<": 3,
        ">": 3,
        "<=": 3,
        ">=": 3,
        "+": 4,
        "-": 4,
        "*": 5,
        "/": 5,
        "MOD": 5,
    }

    def __init__(self, text: str, line: int):
        self.tokens = _tokenize_expression(text, line)
        self.index = 0
        self.line = line

    def current(self) -> Token:
        return self.tokens[self.index]

    def consume(self) -> Token:
        token = self.current()
        self.index += 1
        return token

    def parse(self) -> Node:
        node = self.parse_binary(0)
        if self.current()[0] != "eof":
            raise C64BasicError("Unerwarteter Rest im Ausdruck.", self.line)
        return node

    def parse_binary(self, minimum: int) -> Node:
        node = self.parse_unary()
        while True:
            kind, value = self.current()
            if kind != "op" or value not in self.PRECEDENCE:
                break
            precedence = self.PRECEDENCE[str(value)]
            if precedence < minimum:
                break
            self.consume()
            right = self.parse_binary(precedence + 1)
            node = ("binary", str(value), node, right)
        return node

    def parse_unary(self) -> Node:
        kind, value = self.current()
        if kind == "op" and value in {"+", "-"}:
            self.consume()
            return ("unary", str(value), self.parse_unary())
        if kind == "number":
            self.consume()
            return ("number", value)
        if kind == "identifier":
            self.consume()
            name = str(value)
            if self.current() == ("op", "("):
                self.consume()
                arguments: List[Node] = []
                if self.current() != ("op", ")"):
                    while True:
                        arguments.append(self.parse_binary(0))
                        if self.current()[0] != "comma":
                            break
                        self.consume()
                if self.current() != ("op", ")"):
                    raise C64BasicError("Schließende Klammer fehlt.", self.line)
                self.consume()
                return ("call", name, tuple(arguments))
            return ("variable", name)
        if kind == "op" and value == "(":
            self.consume()
            node = self.parse_binary(0)
            if self.current() != ("op", ")"):
                raise C64BasicError("Schließende Klammer fehlt.", self.line)
            self.consume()
            return node
        raise C64BasicError("Ausdruck erwartet.", self.line)


def _parse_expression(text: str, line: int) -> Node:
    if not text.strip():
        raise C64BasicError("Ausdruck erwartet.", line)
    return _ExpressionParser(text, line).parse()


def _safe_symbol(name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_]", "_", name.upper())
    if not normalized or normalized[0].isdigit():
        normalized = "V_" + normalized
    return normalized


def _petscii_bytes(text: str) -> bytes:
    """Kodiert BASIC-Stringtext in PETSCII-Bytes.

    Stage ASM 62 führt für die C64Pro-Mono-Grafikpalette eine verlustfreie
    Direct-PETSCII-Darstellung ein: U+E000..U+E0FF entspricht exakt $00..$FF.
    Normales historisches Latin-1-Verhalten bleibt für bestehende Quellen
    erhalten. Nicht darstellbare Unicode-Zeichen werden weiterhin zu ``?``.
    """
    normalized = text.replace('""', '"')
    payload = bytearray()
    for character in normalized:
        codepoint = ord(character)
        if 0xE000 <= codepoint <= 0xE0FF:
            payload.append(codepoint - 0xE000)
        elif codepoint <= 0xFF:
            payload.append(codepoint)
        else:
            payload.append(ord('?'))
        if len(payload) >= 255:
            break
    return bytes(payload)


def _encode_cbm_float(value: Decimal) -> bytes:
    """Kodiert einen Python-Decimalwert in das kompakte 5-Byte-CBM-Format."""
    if not value.is_finite():
        raise C64BasicError("NaN und unendliche Werte werden nicht unterstützt.")
    if value == 0:
        return b"\x00\x00\x00\x00\x00"
    sign = 0x80 if value < 0 else 0
    absolute = abs(value)
    # Decimal.logb ist nicht überall gleich implementiert; die grobe
    # Binärexponent-Schätzung wird über float ermittelt und anschließend mit
    # Decimal korrigiert.
    try:
        exponent2 = math.floor(math.log2(float(absolute)))
    except (OverflowError, ValueError) as exc:
        raise C64BasicError(f"Fließkommazahl liegt außerhalb des C64-Bereichs: {value}") from exc
    with localcontext() as context:
        context.prec = 80
        two = Decimal(2)
        power = two ** exponent2
        while absolute < power:
            exponent2 -= 1
            power /= two
        while absolute >= power * two:
            exponent2 += 1
            power *= two
        exponent = exponent2 + 129
        if not 1 <= exponent <= 255:
            raise C64BasicError(f"Fließkommazahl liegt außerhalb des C64-Bereichs: {value}")
        normalized = absolute / power
        fraction = normalized - Decimal(1)
        mantissa = int((fraction * (1 << 31)).to_integral_value(rounding="ROUND_HALF_EVEN"))
        if mantissa >= (1 << 31):
            mantissa = 0
            exponent += 1
            if exponent > 255:
                raise C64BasicError(f"Fließkommazahl ist zu groß: {value}")
    return bytes(
        (
            exponent,
            sign | ((mantissa >> 24) & 0x7F),
            (mantissa >> 16) & 0xFF,
            (mantissa >> 8) & 0xFF,
            mantissa & 0xFF,
        )
    )


def _parse_lvalue(text: str, line: int) -> Tuple[str, Tuple[str, ...]]:
    match = re.fullmatch(
        r"\s*([A-Za-z_][A-Za-z0-9_$%#!]*)\s*(?:\((.*)\))?\s*",
        text,
        flags=re.S,
    )
    if match is None:
        raise C64BasicError("Variable oder Arrayelement erwartet.", line)
    indices: Tuple[str, ...] = ()
    if match.group(2) is not None:
        parts = _split_top_level(match.group(2), ",")
        if not parts or any(not part for part in parts):
            raise C64BasicError("Ungültiger Arrayindex.", line)
        indices = tuple(parts)
    return match.group(1).upper(), indices


def _is_string_name(name: str) -> bool:
    return name.upper().endswith("$")


def _is_integer_name(name: str) -> bool:
    return name.upper().endswith("%")


def _looks_like_string_expression(text: str) -> bool:
    stripped = text.strip()
    upper = stripped.upper()
    if stripped.startswith('"'):
        return True
    if any(upper.startswith(name + "(") for name in _STRING_FUNCTIONS):
        return True
    # LEN/VAL/ASC liefern Zahlen, obwohl ihre Argumente Strings enthalten.
    if any(upper.startswith(name + "(") for name in {"LEN", "VAL", "ASC"}):
        return False
    return bool(re.search(r"[A-Za-z_][A-Za-z0-9_]*\$", stripped))


class _BasicCompiler:
    AUTO_PRINT_LITERAL_MARKER = ";@BASIC_AUTO_PRINT_LITERAL "

    def __init__(
        self,
        source: str,
        filename: str,
        *,
        optimizer_enabled: bool = True,
        optimizer_strategy: str = "direct",
    ):
        self.source = source
        self.filename = filename
        self.lines: List[str] = []
        self.numeric_variables: Dict[str, Tuple[str, str]] = {}
        self.string_variables: Dict[str, str] = {}
        self.arrays: Dict[str, _ArrayInfo] = {}
        self.float_temporaries: List[str] = []
        self.string_literals: List[Tuple[str, bytes]] = []
        self._string_literal_by_payload: Dict[bytes, str] = {}
        self._string_literal_print_uses: Dict[str, int] = {}
        self._string_literal_thunks: set[str] = set()
        self._inline_pointer_runtime_needed = False
        self.float_constants: Dict[str, Tuple[str, bytes]] = {}
        self.label_counter = 0
        self.temp_counter = 0
        self.for_stack: List[Dict[str, str]] = []
        self.defined_line_numbers: set[int] = set()
        self.referenced_line_numbers: List[Tuple[int, int]] = []
        self.warnings: List[str] = []
        self.data_by_line: List[Tuple[int, List[str]]] = []
        self.data_line_labels: Dict[int, str] = {}
        self.total_array_bytes = 0
        self.optimizer_enabled = bool(optimizer_enabled)
        self.optimizer_strategy = normalize_print_strategy(optimizer_strategy)
        self.optimizer = C64BasicOptimizer()

    def new_label(self, prefix: str) -> str:
        self.label_counter += 1
        return f"__basic_{prefix}_{self.label_counter}"

    def new_float_temp(self) -> str:
        self.temp_counter += 1
        name = f"__basic_float_tmp_{self.temp_counter}"
        self.float_temporaries.append(name)
        return name

    def emit(self, text: str = "") -> None:
        self.lines.append(text)

    def numeric_variable(self, name: str) -> Tuple[str, str]:
        key = name.upper()
        if _is_string_name(key):
            raise C64BasicError(f"Stringvariable {name} kann nicht numerisch verwendet werden.")
        if key not in self.numeric_variables:
            kind = "integer" if _is_integer_name(key) else "float"
            self.numeric_variables[key] = (
                f"__basic_var_{_safe_symbol(key)}",
                kind,
            )
        return self.numeric_variables[key]

    def string_variable(self, name: str) -> str:
        key = name.upper()
        if not _is_string_name(key):
            raise C64BasicError(f"Numerische Variable {name} kann nicht als String verwendet werden.")
        if key not in self.string_variables:
            self.string_variables[key] = f"__basic_str_{_safe_symbol(key)}"
        return self.string_variables[key]

    def add_string_literal(self, text: str) -> str:
        # Immutable Stringliterale können sicher zusammengelegt werden. Das ist
        # insbesondere für String-Thunks wichtig: mehrfach verwendeter Text
        # erhält ein gemeinsames Zielsymbol.
        payload = _petscii_bytes(text)
        existing = self._string_literal_by_payload.get(payload)
        if existing is not None:
            return existing
        symbol = self.new_label("string")
        self._string_literal_by_payload[payload] = symbol
        self.string_literals.append((symbol, payload))
        return symbol

    @staticmethod
    def _print_thunk_label(symbol: str) -> str:
        suffix = str(symbol).removeprefix("__basic_string_")
        return f"__basic_print_thunk_{suffix}"

    def _emit_direct_literal_print(self, symbol: str) -> None:
        self.emit(f"    lda #<{symbol}")
        self.emit(f"    ldy #>{symbol}")
        self.emit("    jsr __basic_print_string")
        self.optimizer.stats.direct_literal_prints += 1

    def _emit_inline_pointer_literal_print(self, symbol: str) -> None:
        self._inline_pointer_runtime_needed = True
        self.emit("    jsr __basic_print_literal_inline")
        self.emit(f"    .word {symbol}")
        self.optimizer.stats.inline_pointer_prints += 1

    def _emit_string_thunk_literal_print(self, symbol: str) -> None:
        self._string_literal_thunks.add(symbol)
        self.emit(f"    jsr {self._print_thunk_label(symbol)}")
        self.optimizer.stats.string_thunk_prints += 1

    def emit_print_literal(self, symbol: str) -> None:
        strategy = self.optimizer_strategy if self.optimizer_enabled else "direct"
        self._string_literal_print_uses[symbol] = (
            self._string_literal_print_uses.get(symbol, 0) + 1
        )
        if strategy == "direct":
            self._emit_direct_literal_print(symbol)
        elif strategy == "inline_pointer":
            self._emit_inline_pointer_literal_print(symbol)
        elif strategy == "string_thunk":
            self._emit_string_thunk_literal_print(symbol)
        elif strategy == "auto":
            # Die endgültige Entscheidung ist erst möglich, nachdem alle
            # PRINT-Stellen bekannt sind. Der Marker wird vor der Runtime-
            # Ausgabe in echte 6502-Instruktionen umgeschrieben.
            self.emit(self.AUTO_PRINT_LITERAL_MARKER + symbol)
        else:
            self._emit_direct_literal_print(symbol)

    def resolve_auto_print_literals(self) -> None:
        if not (self.optimizer_enabled and self.optimizer_strategy == "auto"):
            return
        resolved: List[str] = []
        marker = self.AUTO_PRINT_LITERAL_MARKER
        for line in self.lines:
            if not line.startswith(marker):
                resolved.append(line)
                continue
            symbol = line[len(marker):].strip()
            count = int(self._string_literal_print_uses.get(symbol, 0))
            if count >= 2:
                self._string_literal_thunks.add(symbol)
                resolved.append(f"    jsr {self._print_thunk_label(symbol)}")
                self.optimizer.stats.string_thunk_prints += 1
            else:
                self._inline_pointer_runtime_needed = True
                resolved.append("    jsr __basic_print_literal_inline")
                resolved.append(f"    .word {symbol}")
                self.optimizer.stats.inline_pointer_prints += 1
        self.lines = resolved

    def float_constant(self, value: Decimal) -> str:
        normalized = str(value.normalize()) if value != 0 else "0"
        if normalized not in self.float_constants:
            symbol = f"__basic_float_const_{len(self.float_constants) + 1}"
            self.float_constants[normalized] = (symbol, _encode_cbm_float(value))
        return self.float_constants[normalized][0]

    def emit_load_float(self, symbol: str) -> None:
        self.emit(f"    lda #<{symbol}")
        self.emit(f"    ldy #>{symbol}")
        self.emit("    jsr $BBA2")       # MOVFM: memory -> FAC

    def emit_store_float(self, symbol: str) -> None:
        self.emit(f"    ldx #<{symbol}")
        self.emit(f"    ldy #>{symbol}")
        self.emit("    jsr $BBD4")       # MOVMF: FAC -> memory

    def emit_pointer(self, low_symbol: str, high_symbol: str, symbol: str) -> None:
        self.emit(f"    lda #<{symbol}")
        self.emit(f"    sta {low_symbol}")
        self.emit(f"    lda #>{symbol}")
        self.emit(f"    sta {high_symbol}")

    def declare_array(self, name: str, dimensions: Sequence[int], line: int) -> _ArrayInfo:
        key = name.upper()
        if not 1 <= len(dimensions) <= 2:
            raise C64BasicError("Arrays unterstützen eine oder zwei Dimensionen.", line)
        bounds = tuple(int(value) for value in dimensions)
        if any(value < 0 or value > 32767 for value in bounds):
            raise C64BasicError("Arraygrenzen müssen zwischen 0 und 32767 liegen.", line)
        kind = "string" if _is_string_name(key) else ("integer" if _is_integer_name(key) else "float")
        element_size = {"string": 256, "integer": 2, "float": 5}[kind]
        existing = self.arrays.get(key)
        if existing is not None:
            if existing.dimensions != bounds:
                raise C64BasicError(f"Array {name} wurde mit anderen Grenzen erneut dimensioniert.", line)
            return existing
        info = _ArrayInfo(
            name=key,
            symbol=f"__basic_array_{_safe_symbol(key)}",
            dimensions=bounds,
            kind=kind,
            element_size=element_size,
        )
        if info.byte_size > 30000 or self.total_array_bytes + info.byte_size > 30000:
            raise C64BasicError(
                f"Array {name} benötigt {info.byte_size} Bytes; der statische Arraybereich wäre zu groß.",
                line,
            )
        self.arrays[key] = info
        self.total_array_bytes += info.byte_size
        return info

    def ensure_array(self, name: str, index_count: int, line: int) -> _ArrayInfo:
        key = name.upper()
        info = self.arrays.get(key)
        if info is None:
            # Commodore BASIC dimensioniert nicht deklarierte Arrays automatisch 0..10.
            info = self.declare_array(key, [10] * index_count, line)
            self.warnings.append(
                f"BASIC-Zeile {line}: Array {key} wurde automatisch mit Grenze 10 dimensioniert."
            )
        if len(info.dimensions) != index_count:
            raise C64BasicError(
                f"Array {name} erwartet {len(info.dimensions)} Indizes, erhalten: {index_count}.",
                line,
            )
        return info

    def compile_numeric_expression(self, node: Node, basic_line: int) -> None:
        if self.optimizer_enabled:
            node = self.optimizer.optimize_numeric_node(node)
        kind = node[0]
        if kind == "number":
            self.emit_load_float(self.float_constant(Decimal(node[1])))
            return
        if kind == "variable":
            name = str(node[1])
            symbol, value_kind = self.numeric_variable(name)
            if value_kind == "float":
                self.emit_load_float(symbol)
            else:
                self.emit(f"    ldy {symbol}")
                self.emit(f"    lda {symbol}+1")
                self.emit("    jsr $B391")       # GIVAYF: signed int AY -> FAC
            return
        if kind == "call":
            name = str(node[1]).upper()
            arguments = tuple(node[2])
            if name in _FLOAT_FUNCTIONS:
                self.compile_numeric_function(name, arguments, basic_line)
                return
            info = self.ensure_array(name, len(arguments), basic_line)
            if info.kind == "string":
                raise C64BasicError(f"Stringarray {name} kann nicht numerisch verwendet werden.", basic_line)
            self.compile_array_address(info, arguments, basic_line)
            if info.kind == "float":
                self.emit("    lda $FB")
                self.emit("    ldy $FC")
                self.emit("    jsr $BBA2")
            else:
                self.emit("    ldy #$00")
                self.emit("    lda ($FB),y")
                self.emit("    sta __basic_int_hold")
                self.emit("    iny")
                self.emit("    lda ($FB),y")
                self.emit("    tax")
                self.emit("    lda __basic_int_hold")
                self.emit("    jsr __basic_int_to_fac")
            return
        if kind == "unary":
            operator = node[1]
            self.compile_numeric_expression(node[2], basic_line)
            if operator == "-":
                zero = self.new_label("neg_zero")
                self.emit("    lda $61")
                self.emit(f"    beq {zero}")
                self.emit("    lda $66")
                self.emit("    eor #$80")
                self.emit("    sta $66")
                self.emit(f"{zero}:")
            return
        if kind != "binary":
            raise C64BasicError("Interner Ausdrucksfehler.", basic_line)

        operator, left, right = str(node[1]), node[2], node[3]
        temporary = self.new_float_temp()
        self.compile_numeric_expression(left, basic_line)
        self.emit_store_float(temporary)
        self.compile_numeric_expression(right, basic_line)

        if operator in {"+", "-", "*", "/"}:
            helper = {
                "+": "__basic_add",
                "-": "__basic_sub",
                "*": "__basic_mul",
                "/": "__basic_div",
            }[operator]
            self.emit(f"    lda #<{temporary}")
            self.emit(f"    ldy #>{temporary}")
            self.emit(f"    jsr {helper}")
            return
        if operator in {"AND", "OR", "MOD"}:
            self.emit("    jsr __basic_fac_to_int")
            self.emit("    sta __basic_int_right")
            self.emit("    stx __basic_int_right+1")
            self.emit_load_float(temporary)
            self.emit("    jsr __basic_fac_to_int")
            self.emit("    sta __basic_int_left")
            self.emit("    stx __basic_int_left+1")
            helper = {
                "AND": "__basic_int_and",
                "OR": "__basic_int_or",
                "MOD": "__basic_int_mod",
            }[operator]
            self.emit(f"    jsr {helper}")
            self.emit("    jsr __basic_int_to_fac")
            return
        if operator in _COMPARISON_OPERATORS:
            helper = {
                "=": "__basic_cmp_eq",
                "<>": "__basic_cmp_ne",
                "<": "__basic_cmp_lt",
                ">": "__basic_cmp_gt",
                "<=": "__basic_cmp_le",
                ">=": "__basic_cmp_ge",
            }[operator]
            self.emit(f"    lda #<{temporary}")
            self.emit(f"    ldy #>{temporary}")
            self.emit(f"    jsr {helper}")
            return
        raise C64BasicError(f"Operator {operator} wird nicht unterstützt.", basic_line)

    # Kompatibilitätsname für frühere Tests und externe Aufrufer.
    compile_expression = compile_numeric_expression

    def compile_numeric_function(self, name: str, arguments: Sequence[Node], line: int) -> None:
        expected = 1
        if len(arguments) != expected:
            raise C64BasicError(f"{name} erwartet genau ein Argument.", line)
        if name in {"LEN", "VAL", "ASC"}:
            raise C64BasicError(
                f"{name} benötigt einen Stringausdruck und muss direkt im Quelltext stehen.", line
            )
        self.compile_numeric_expression(arguments[0], line)
        if name == "ABS":
            self.emit("    jsr $BC58")
        elif name == "INT":
            self.emit("    jsr $BCCC")
        elif name == "SGN":
            # Die BASIC-ROM-Funktion legt -1, 0 oder 1 direkt wieder in FAC ab.
            self.emit("    jsr $BC39")
        elif name == "PEEK":
            self.emit("    jsr __basic_fac_to_int")
            self.emit("    sta $FB")
            self.emit("    stx $FC")
            self.emit("    ldy #$00")
            self.emit("    lda ($FB),y")
            self.emit("    ldx #$00")
            self.emit("    jsr __basic_int_to_fac")

    def compile_special_numeric_function(self, text: str, line: int) -> bool:
        match = re.fullmatch(r"(?is)\s*(LEN|VAL|ASC)\s*\((.*)\)\s*", text)
        if match is None:
            return False
        name = match.group(1).upper()
        argument = match.group(2)
        self.compile_string_expression_to(argument, "__basic_string_expr", line)
        if name == "LEN":
            self.emit("    lda __basic_string_expr")
            self.emit("    ldx #$00")
            self.emit("    jsr __basic_int_to_fac")
        elif name == "ASC":
            empty = self.new_label("asc_empty")
            done = self.new_label("asc_done")
            self.emit("    lda __basic_string_expr")
            self.emit(f"    beq {empty}")
            self.emit("    lda __basic_string_expr+1")
            self.emit("    ldx #$00")
            self.emit(f"    jmp {done}")
            self.emit(f"{empty}:")
            self.emit("    lda #$00")
            self.emit("    tax")
            self.emit(f"{done}:")
            self.emit("    jsr __basic_int_to_fac")
        else:
            self.emit_pointer("$22", "$23", "__basic_string_expr+1")
            self.emit("    lda __basic_string_expr")
            zero = self.new_label("val_zero")
            done = self.new_label("val_done")
            self.emit(f"    beq {zero}")
            self.emit("    jsr $B7B5")           # STRVAL
            self.emit(f"    jmp {done}")
            self.emit(f"{zero}:")
            self.emit_load_float(self.float_constant(Decimal(0)))
            self.emit(f"{done}:")
        return True

    def compile_numeric_text(self, text: str, line: int) -> None:
        if self.compile_special_numeric_function(text, line):
            return
        self.compile_numeric_expression(_parse_expression(text, line), line)

    def compile_array_address(self, info: _ArrayInfo, indices: Sequence[Node], line: int) -> None:
        if len(indices) != len(info.dimensions):
            raise C64BasicError(
                f"Array {info.name} erwartet {len(info.dimensions)} Indizes.", line
            )
        # Erster Index.
        self.compile_numeric_expression(indices[0], line)
        self.emit("    jsr __basic_fac_to_int")
        self.emit("    sta __basic_index")
        self.emit("    stx __basic_index+1")
        self.emit_array_bounds_check(info.dimensions[0], line)

        if len(indices) == 2:
            stride = info.dimensions[1] + 1
            self.emit("    lda __basic_index")
            self.emit("    ldx __basic_index+1")
            self.emit("    sta __basic_int_left")
            self.emit("    stx __basic_int_left+1")
            self.emit(f"    lda #${stride & 0xFF:02X}")
            self.emit(f"    ldx #${(stride >> 8) & 0xFF:02X}")
            self.emit("    sta __basic_int_right")
            self.emit("    stx __basic_int_right+1")
            self.emit("    jsr __basic_u16_mul")
            self.emit("    sta __basic_linear_index")
            self.emit("    stx __basic_linear_index+1")

            self.compile_numeric_expression(indices[1], line)
            self.emit("    jsr __basic_fac_to_int")
            self.emit("    sta __basic_index")
            self.emit("    stx __basic_index+1")
            self.emit_array_bounds_check(info.dimensions[1], line)
            self.emit("    lda __basic_linear_index")
            self.emit("    ldx __basic_linear_index+1")
            self.emit("    sta __basic_int_left")
            self.emit("    stx __basic_int_left+1")
            self.emit("    lda __basic_index")
            self.emit("    ldx __basic_index+1")
            self.emit("    sta __basic_int_right")
            self.emit("    stx __basic_int_right+1")
            self.emit("    jsr __basic_u16_add")
            self.emit("    sta __basic_linear_index")
            self.emit("    stx __basic_linear_index+1")
        else:
            self.emit("    lda __basic_index")
            self.emit("    ldx __basic_index+1")
            self.emit("    sta __basic_linear_index")
            self.emit("    stx __basic_linear_index+1")

        self.emit("    lda __basic_linear_index")
        self.emit("    ldx __basic_linear_index+1")
        self.emit("    sta __basic_int_left")
        self.emit("    stx __basic_int_left+1")
        self.emit(f"    lda #${info.element_size & 0xFF:02X}")
        self.emit(f"    ldx #${(info.element_size >> 8) & 0xFF:02X}")
        self.emit("    sta __basic_int_right")
        self.emit("    stx __basic_int_right+1")
        self.emit("    jsr __basic_u16_mul")
        self.emit("    sta __basic_linear_index")
        self.emit("    stx __basic_linear_index+1")
        self.emit("    clc")
        self.emit("    lda __basic_linear_index")
        self.emit(f"    adc #<{info.symbol}")
        self.emit("    sta $FB")
        self.emit("    lda __basic_linear_index+1")
        self.emit(f"    adc #>{info.symbol}")
        self.emit("    sta $FC")

    def emit_array_bounds_check(self, upper: int, line: int) -> None:
        okay = self.new_label("index_ok")
        bad = self.new_label("index_bad")
        self.emit("    ldx __basic_index+1")
        self.emit(f"    cpx #${(upper >> 8) & 0xFF:02X}")
        self.emit(f"    bcc {okay}")
        self.emit(f"    bne {bad}")
        self.emit("    lda __basic_index")
        self.emit(f"    cmp #${upper & 0xFF:02X}")
        self.emit(f"    bcc {okay}")
        self.emit(f"    beq {okay}")
        self.emit(f"{bad}:")
        self.emit("    jsr __basic_bad_subscript")
        self.emit(f"{okay}:")

    def string_term_source_pointer(self, term: str, line: int) -> None:
        stripped = term.strip()
        if len(stripped) >= 2 and stripped.startswith('"') and stripped.endswith('"'):
            symbol = self.add_string_literal(stripped[1:-1])
            self.emit_pointer("$FD", "$FE", symbol)
            return
        function_match = re.fullmatch(r"(?is)\s*(CHR\$|STR\$)\s*\((.*)\)\s*", stripped)
        if function_match is not None:
            name = function_match.group(1).upper()
            argument = function_match.group(2)
            self.compile_numeric_text(argument, line)
            if name == "CHR$":
                self.emit("    jsr __basic_fac_to_int")
                self.emit("    sta __basic_string_term+1")
                self.emit("    lda #$01")
                self.emit("    sta __basic_string_term")
            else:
                self.emit("    jsr __basic_float_to_string_term")
            self.emit_pointer("$FD", "$FE", "__basic_string_term")
            return
        name, index_texts = _parse_lvalue(stripped, line)
        if not _is_string_name(name):
            raise C64BasicError("Stringausdruck erwartet.", line)
        if index_texts:
            info = self.ensure_array(name, len(index_texts), line)
            if info.kind != "string":
                raise C64BasicError(f"Array {name} ist kein Stringarray.", line)
            nodes = tuple(_parse_expression(item, line) for item in index_texts)
            self.compile_array_address(info, nodes, line)
            self.emit("    lda $FB")
            self.emit("    sta $FD")
            self.emit("    lda $FC")
            self.emit("    sta $FE")
        else:
            self.emit_pointer("$FD", "$FE", self.string_variable(name))

    def compile_print_string_term(self, term: str, line: int) -> None:
        """Gibt genau einen Stringterm ohne __basic_string_expr aus."""
        stripped = term.strip()
        if len(stripped) >= 2 and stripped.startswith('"') and stripped.endswith('"'):
            symbol = self.add_string_literal(stripped[1:-1])
            self.emit_print_literal(symbol)
            return

        function_match = re.fullmatch(r"(?is)\s*(CHR\$|STR\$)\s*\((.*)\)\s*", stripped)
        if function_match is not None:
            name = function_match.group(1).upper()
            argument = function_match.group(2)
            self.compile_numeric_text(argument, line)
            if name == "CHR$":
                self.emit("    jsr __basic_fac_to_int")
                self.emit("    sta __basic_string_term+1")
                self.emit("    lda #$01")
                self.emit("    sta __basic_string_term")
            else:
                self.emit("    jsr __basic_float_to_string_term")
            self.emit("    lda #<__basic_string_term")
            self.emit("    ldy #>__basic_string_term")
            self.emit("    jsr __basic_print_string")
            return

        name, index_texts = _parse_lvalue(stripped, line)
        if not _is_string_name(name):
            raise C64BasicError("Stringausdruck erwartet.", line)
        if index_texts:
            info = self.ensure_array(name, len(index_texts), line)
            if info.kind != "string":
                raise C64BasicError(f"Array {name} ist kein Stringarray.", line)
            nodes = tuple(_parse_expression(item, line) for item in index_texts)
            self.compile_array_address(info, nodes, line)
            self.emit("    lda $FB")
            self.emit("    ldy $FC")
        else:
            symbol = self.string_variable(name)
            self.emit(f"    lda #<{symbol}")
            self.emit(f"    ldy #>{symbol}")
        self.emit("    jsr __basic_print_string")

    def compile_print_string_expression_direct(self, text: str, line: int) -> bool:
        """Streamt einen PRINT-Stringausdruck direkt, falls sicher darstellbar."""
        if not self.optimizer_enabled:
            return False
        terms = self.optimizer.direct_print_terms(text)
        if terms is None:
            return False
        for term in terms:
            self.compile_print_string_term(term, line)
        self.optimizer.record_streamed_print(len(terms))
        return True

    def compile_string_expression_to(self, text: str, destination: str, line: int) -> None:
        terms = _split_top_level(text, "+")
        if not terms or any(not term for term in terms):
            raise C64BasicError("Ungültiger Stringausdruck.", line)
        self.emit_pointer("$FB", "$FC", destination)
        self.emit("    jsr __basic_string_clear")
        for term in terms:
            self.string_term_source_pointer(term, line)
            self.emit_pointer("$FB", "$FC", destination)
            self.emit("    jsr __basic_string_append")

    def compile_string_compare(self, left: str, operator: str, right: str, line: int) -> None:
        self.compile_string_expression_to(left, "__basic_string_left", line)
        self.compile_string_expression_to(right, "__basic_string_right", line)
        self.emit_pointer("$FB", "$FC", "__basic_string_left")
        self.emit_pointer("$FD", "$FE", "__basic_string_right")
        self.emit("    jsr __basic_string_compare")
        # A: $FF left<right, 0 equal, 1 left>right.
        true_label = self.new_label("str_cmp_true")
        done_label = self.new_label("str_cmp_done")
        if operator == "=":
            self.emit(f"    beq {true_label}")
        elif operator == "<>":
            self.emit(f"    bne {true_label}")
        elif operator == "<":
            self.emit("    cmp #$FF")
            self.emit(f"    beq {true_label}")
        elif operator == ">":
            self.emit("    cmp #$01")
            self.emit(f"    beq {true_label}")
        elif operator == "<=":
            self.emit("    cmp #$01")
            self.emit(f"    bne {true_label}")
        elif operator == ">=":
            self.emit("    cmp #$FF")
            self.emit(f"    bne {true_label}")
        self.emit("    lda #$00")
        self.emit(f"    jmp {done_label}")
        self.emit(f"{true_label}:")
        self.emit("    lda #$01")
        self.emit(f"{done_label}:")

    def compile_print(self, tail: str, line: int) -> None:
        items, trailing = _split_print_items(tail)
        if not items and not tail.strip():
            self.emit("    jsr __basic_newline")
            return
        for value, separator in items:
            if not value:
                continue
            if _looks_like_string_expression(value):
                if not self.compile_print_string_expression_direct(value, line):
                    self.compile_string_expression_to(value, "__basic_string_expr", line)
                    self.emit("    lda #<__basic_string_expr")
                    self.emit("    ldy #>__basic_string_expr")
                    self.emit("    jsr __basic_print_string")
            else:
                self.compile_numeric_text(value, line)
                self.emit("    jsr __basic_print_float")
            if separator == ",":
                # Vereinfachte TAB-Zone: vier Leerzeichen.
                for _ in range(4):
                    self.emit("    lda #$20")
                    self.emit("    jsr $FFD2")
        if trailing not in {";", ","}:
            self.emit("    jsr __basic_newline")

    def compile_numeric_store(self, name: str, indices: Tuple[str, ...], line: int) -> None:
        if indices:
            info = self.ensure_array(name, len(indices), line)
            if info.kind == "string":
                raise C64BasicError(f"Stringarray {name} erwartet einen Stringwert.", line)
            self.emit_store_float("__basic_float_hold")
            nodes = tuple(_parse_expression(item, line) for item in indices)
            self.compile_array_address(info, nodes, line)
            self.emit_load_float("__basic_float_hold")
            if info.kind == "float":
                self.emit("    ldx $FB")
                self.emit("    ldy $FC")
                self.emit("    jsr $BBD4")
            else:
                self.emit("    jsr __basic_fac_to_int")
                self.emit("    ldy #$00")
                self.emit("    sta ($FB),y")
                self.emit("    txa")
                self.emit("    iny")
                self.emit("    sta ($FB),y")
            return
        symbol, kind = self.numeric_variable(name)
        if kind == "float":
            self.emit_store_float(symbol)
        else:
            self.emit("    jsr __basic_fac_to_int")
            self.emit(f"    sta {symbol}")
            self.emit(f"    stx {symbol}+1")

    def compile_string_store_from_buffer(
        self, name: str, indices: Tuple[str, ...], source_buffer: str, line: int
    ) -> None:
        if indices:
            info = self.ensure_array(name, len(indices), line)
            if info.kind != "string":
                raise C64BasicError(f"Array {name} ist kein Stringarray.", line)
            nodes = tuple(_parse_expression(item, line) for item in indices)
            self.compile_array_address(info, nodes, line)
            self.emit("    lda $FB")
            self.emit("    sta __basic_dest_ptr")
            self.emit("    lda $FC")
            self.emit("    sta __basic_dest_ptr+1")
            self.emit("    lda __basic_dest_ptr")
            self.emit("    sta $FB")
            self.emit("    lda __basic_dest_ptr+1")
            self.emit("    sta $FC")
        else:
            self.emit_pointer("$FB", "$FC", self.string_variable(name))
        self.emit_pointer("$FD", "$FE", source_buffer)
        self.emit("    jsr __basic_string_copy")

    def compile_assignment(self, text: str, line: int) -> None:
        comparison = _find_top_level_comparison(text)
        if comparison is None or comparison[1] != "=":
            raise C64BasicError("Zuweisung erwartet: VARIABLE = AUSDRUCK.", line)
        left, _operator, right = comparison
        name, indices = _parse_lvalue(left, line)
        if _is_string_name(name):
            self.compile_string_expression_to(right, "__basic_string_expr", line)
            self.compile_string_store_from_buffer(name, indices, "__basic_string_expr", line)
        else:
            self.compile_numeric_text(right, line)
            self.compile_numeric_store(name, indices, line)

    def compile_if(self, tail: str, line: int) -> None:
        match = re.match(r"(?is)^(.*?)\s+THEN\s+(.+)$", tail.strip())
        if match is None:
            raise C64BasicError("IF benötigt THEN.", line)
        condition_text = match.group(1).strip()
        action = match.group(2).strip()
        comparison = _find_top_level_comparison(condition_text)
        skip = self.new_label("if_skip")
        if comparison is not None and (
            _looks_like_string_expression(comparison[0])
            or _looks_like_string_expression(comparison[2])
        ):
            self.compile_string_compare(*comparison, line)
            self.emit("    cmp #$00")
            self.emit(f"    beq {skip}")
        else:
            self.compile_numeric_text(condition_text, line)
            self.emit("    lda $61")            # FAC exponent: 0 means numeric zero
            self.emit(f"    beq {skip}")
        if re.fullmatch(r"\d+", action):
            target = int(action)
            self.referenced_line_numbers.append((target, line))
            self.emit(f"    jmp __basic_line_{target}")
        else:
            self.compile_statement(action, line)
        self.emit(f"{skip}:")

    def compile_for(self, tail: str, line: int) -> None:
        match = re.match(
            r"(?is)^([A-Za-z_][A-Za-z0-9_%#!]*)\s*=\s*(.*?)\s+TO\s+(.*?)(?:\s+STEP\s+(.+))?$",
            tail.strip(),
        )
        if match is None:
            raise C64BasicError("FOR-Syntax: FOR V = START TO ENDE [STEP SCHRITT].", line)
        variable_name = match.group(1).upper()
        if _is_string_name(variable_name):
            raise C64BasicError("FOR benötigt eine numerische Variable.", line)
        end_symbol = self.new_float_temp()
        step_symbol = self.new_float_temp()
        self.compile_numeric_text(match.group(2), line)
        self.compile_numeric_store(variable_name, (), line)
        self.compile_numeric_text(match.group(3), line)
        self.emit_store_float(end_symbol)
        self.compile_numeric_text(match.group(4) or "1", line)
        self.emit_store_float(step_symbol)
        loop_label = self.new_label("for_loop")
        self.emit(f"{loop_label}:")
        self.for_stack.append(
            {
                "name": variable_name,
                "end": end_symbol,
                "step": step_symbol,
                "loop": loop_label,
                "line": str(line),
            }
        )

    def compile_next(self, tail: str, line: int) -> None:
        if not self.for_stack:
            raise C64BasicError("NEXT ohne zugehöriges FOR.", line)
        expected = tail.strip().upper()
        context = self.for_stack[-1]
        if expected and expected != context["name"]:
            raise C64BasicError(
                f"NEXT {expected} passt nicht zu FOR {context['name']}.", line
            )
        self.for_stack.pop()
        variable_name = context["name"]
        variable_symbol, variable_kind = self.numeric_variable(variable_name)
        # Schritt laden und Variable addieren.
        self.emit_load_float(context["step"])
        if variable_kind == "float":
            self.emit(f"    lda #<{variable_symbol}")
            self.emit(f"    ldy #>{variable_symbol}")
            self.emit("    jsr __basic_add")
        else:
            self.emit_store_float("__basic_float_hold")
            self.emit(f"    ldy {variable_symbol}")
            self.emit(f"    lda {variable_symbol}+1")
            self.emit("    jsr $B391")
            self.emit_store_float("__basic_float_hold2")
            self.emit_load_float("__basic_float_hold")
            self.emit("    lda #<__basic_float_hold2")
            self.emit("    ldy #>__basic_float_hold2")
            self.emit("    jsr __basic_add")
        self.compile_numeric_store(variable_name, (), line)
        # Aktuellen Wert erneut laden, mit Endwert vergleichen.
        symbol, kind = self.numeric_variable(variable_name)
        if kind == "float":
            self.emit_load_float(symbol)
        else:
            self.emit(f"    ldy {symbol}")
            self.emit(f"    lda {symbol}+1")
            self.emit("    jsr $B391")
        self.emit(f"    lda #<{context['end']}")
        self.emit(f"    ldy #>{context['end']}")
        self.emit("    jsr $BC5B")           # current FAC vs end memory
        self.emit("    sta __basic_compare_result")
        self.emit_load_float(context["step"])
        negative = self.new_label("for_negative")
        done = self.new_label("for_done")
        self.emit("    lda $66")
        self.emit(f"    bmi {negative}")
        # Positiv: current <= end => compare result != 1.
        self.emit("    lda __basic_compare_result")
        self.emit("    cmp #$01")
        self.emit(f"    beq {done}")
        self.emit(f"    jmp {context['loop']}")
        self.emit(f"{negative}:")
        # Negativ: current >= end => compare result != $FF.
        self.emit("    lda __basic_compare_result")
        self.emit("    cmp #$FF")
        self.emit(f"    beq {done}")
        self.emit(f"    jmp {context['loop']}")
        self.emit(f"{done}:")

    def compile_dim(self, tail: str, line: int) -> None:
        # DIM wurde bereits in prepare_program ausgewertet; zur Laufzeit no-op.
        if not tail.strip():
            raise C64BasicError("DIM erwartet mindestens ein Array.", line)

    def parse_dim_declaration(self, text: str, line: int) -> None:
        for declaration in _split_top_level(text, ","):
            match = re.fullmatch(
                r"\s*([A-Za-z_][A-Za-z0-9_$%#!]*)\s*\((.*)\)\s*",
                declaration,
                flags=re.S,
            )
            if match is None:
                raise C64BasicError("DIM-Syntax: DIM NAME(GRENZE[,GRENZE]).", line)
            dimensions: List[int] = []
            for bound_text in _split_top_level(match.group(2), ","):
                try:
                    value = Decimal(bound_text.strip())
                except InvalidOperation as exc:
                    raise C64BasicError("DIM-Grenzen müssen konstant sein.", line) from exc
                if value != value.to_integral_value():
                    raise C64BasicError("DIM-Grenzen müssen ganzzahlig sein.", line)
                dimensions.append(int(value))
            self.declare_array(match.group(1), dimensions, line)

    def compile_input(self, tail: str, line: int, *, channel: Optional[str] = None) -> None:
        rest = tail.strip()
        if channel is not None:
            self.compile_numeric_text(channel, line)
            self.emit("    jsr __basic_fac_to_int")
            self.emit("    tax")
            self.emit("    jsr $FFC6")          # CHKIN
        else:
            prompt_match = re.match(r'(?is)^\s*("(?:""|[^"])*")\s*([;,])\s*(.*)$', rest)
            if prompt_match is not None:
                if not self.compile_print_string_expression_direct(prompt_match.group(1), line):
                    self.compile_string_expression_to(prompt_match.group(1), "__basic_string_expr", line)
                    self.emit("    lda #<__basic_string_expr")
                    self.emit("    ldy #>__basic_string_expr")
                    self.emit("    jsr __basic_print_string")
                if prompt_match.group(2) == ",":
                    self.emit("    lda #$3F")
                    self.emit("    jsr $FFD2")
                    self.emit("    lda #$20")
                    self.emit("    jsr $FFD2")
                rest = prompt_match.group(3).strip()
            else:
                self.emit("    lda #$3F")
                self.emit("    jsr $FFD2")
                self.emit("    lda #$20")
                self.emit("    jsr $FFD2")
        variables = [part for part in _split_top_level(rest, ",") if part]
        if not variables:
            raise C64BasicError("INPUT erwartet mindestens eine Variable.", line)
        self.emit("    jsr __basic_read_line")
        self.emit("    lda #$00")
        self.emit("    sta __basic_field_position")
        for variable in variables:
            name, indices = _parse_lvalue(variable, line)
            self.emit("    jsr __basic_input_next_field")
            self.compile_assign_field(name, indices, line)
        if channel is not None:
            self.emit("    jsr $FFCC")          # CLRCHN

    def compile_assign_field(self, name: str, indices: Tuple[str, ...], line: int) -> None:
        if _is_string_name(name):
            self.compile_string_store_from_buffer(name, indices, "__basic_field_buffer", line)
        else:
            self.emit("    jsr __basic_field_to_float")
            self.compile_numeric_store(name, indices, line)

    def compile_read(self, tail: str, line: int) -> None:
        variables = [part for part in _split_top_level(tail, ",") if part]
        if not variables:
            raise C64BasicError("READ erwartet mindestens eine Variable.", line)
        for variable in variables:
            name, indices = _parse_lvalue(variable, line)
            self.emit("    jsr __basic_data_read_field")
            self.compile_assign_field(name, indices, line)

    def compile_restore(self, tail: str, line: int) -> None:
        target_symbol = "__basic_data_start"
        if tail.strip():
            if not re.fullmatch(r"\d+", tail.strip()):
                raise C64BasicError("RESTORE erwartet eine DATA-Zeilennummer.", line)
            requested = int(tail.strip())
            candidates = [number for number, _items in self.data_by_line if number >= requested]
            if not candidates:
                raise C64BasicError(f"Ab Zeile {requested} existieren keine DATA-Werte.", line)
            target_symbol = self.data_line_labels[min(candidates)]
        self.emit_pointer("__basic_data_ptr", "__basic_data_ptr+1", target_symbol)

    def compile_get(self, tail: str, line: int, *, channel: Optional[str] = None) -> None:
        variables = [part for part in _split_top_level(tail, ",") if part]
        if not variables:
            raise C64BasicError("GET erwartet mindestens eine Variable.", line)
        if channel is not None:
            self.compile_numeric_text(channel, line)
            self.emit("    jsr __basic_fac_to_int")
            self.emit("    tax")
            self.emit("    jsr $FFC6")
        for variable in variables:
            name, indices = _parse_lvalue(variable, line)
            self.emit("    jsr $FFCF" if channel is not None else "    jsr $FFE4")
            self.emit("    sta __basic_get_char")
            if _is_string_name(name):
                empty = self.new_label("get_empty")
                done = self.new_label("get_done")
                self.emit("    lda __basic_get_char")
                self.emit(f"    beq {empty}")
                self.emit("    sta __basic_string_term+1")
                self.emit("    lda #$01")
                self.emit("    sta __basic_string_term")
                self.emit(f"    jmp {done}")
                self.emit(f"{empty}:")
                self.emit("    lda #$00")
                self.emit("    sta __basic_string_term")
                self.emit(f"{done}:")
                self.compile_string_store_from_buffer(name, indices, "__basic_string_term", line)
            else:
                self.emit("    lda __basic_get_char")
                self.emit("    ldx #$00")
                self.emit("    jsr __basic_int_to_fac")
                self.compile_numeric_store(name, indices, line)
        if channel is not None:
            self.emit("    jsr $FFCC")

    def compile_open(self, tail: str, line: int) -> None:
        parts = _split_top_level(tail, ",")
        if not 2 <= len(parts) <= 4:
            raise C64BasicError("OPEN-Syntax: OPEN LOGISCH,GERÄT[,SEKUNDÄR[,DATEINAME]].", line)
        for expression, symbol in zip(parts[:3], ("__basic_lfn", "__basic_device", "__basic_secondary")):
            self.compile_numeric_text(expression, line)
            self.emit("    jsr __basic_fac_to_int")
            self.emit(f"    sta {symbol}")
        if len(parts) < 3:
            self.emit("    lda #$00")
            self.emit("    sta __basic_secondary")
        self.emit("    lda __basic_lfn")
        self.emit("    ldx __basic_device")
        self.emit("    ldy __basic_secondary")
        self.emit("    jsr $FFBA")             # SETLFS
        if len(parts) == 4:
            self.compile_string_expression_to(parts[3], "__basic_string_expr", line)
            self.emit("    lda __basic_string_expr")
            self.emit("    ldx #<__basic_string_expr+1")
            self.emit("    ldy #>__basic_string_expr+1")
        else:
            self.emit("    lda #$00")
            self.emit("    tax")
            self.emit("    tay")
        self.emit("    jsr $FFBD")             # SETNAM
        self.emit("    jsr $FFC0")             # OPEN

    def compile_close(self, tail: str, line: int) -> None:
        self.compile_numeric_text(tail, line)
        self.emit("    jsr __basic_fac_to_int")
        self.emit("    jsr $FFC3")

    def compile_print_channel(self, tail: str, line: int) -> None:
        parts = _split_top_level(tail, ",")
        if not parts or not parts[0]:
            raise C64BasicError("PRINT# erwartet eine logische Dateinummer.", line)
        channel = parts[0]
        body = tail[tail.find(",") + 1:] if "," in tail else ""
        self.compile_numeric_text(channel, line)
        self.emit("    jsr __basic_fac_to_int")
        self.emit("    tax")
        self.emit("    jsr $FFC9")             # CHKOUT
        self.compile_print(body, line)
        self.emit("    jsr $FFCC")

    def compile_cmd(self, tail: str, line: int) -> None:
        self.compile_numeric_text(tail, line)
        self.emit("    jsr __basic_fac_to_int")
        self.emit("    tax")
        self.emit("    jsr $FFC9")

    def compile_statement(self, statement: str, line: int) -> None:
        statement = statement.strip()
        if not statement:
            return
        upper = statement.upper()
        if upper.startswith("PRINT#"):
            self.compile_print_channel(statement[6:].lstrip(), line)
            return
        if upper.startswith("INPUT#"):
            tail = statement[6:].lstrip()
            parts = _split_top_level(tail, ",")
            if len(parts) < 2:
                raise C64BasicError("INPUT# erwartet Kanal und Variable.", line)
            self.compile_input(",".join(parts[1:]), line, channel=parts[0])
            return
        if upper.startswith("GET#"):
            tail = statement[4:].lstrip()
            parts = _split_top_level(tail, ",")
            if len(parts) < 2:
                raise C64BasicError("GET# erwartet Kanal und Variable.", line)
            self.compile_get(",".join(parts[1:]), line, channel=parts[0])
            return

        match = re.match(r"^([A-Za-z?]+)\b\s*(.*)$", statement, flags=re.S)
        keyword = ""
        tail = statement
        if statement.startswith("?"):
            keyword, tail = "PRINT", statement[1:].lstrip()
        elif match:
            keyword, tail = match.group(1).upper(), match.group(2).strip()

        if keyword == "REM" or statement.startswith("'"):
            return
        if keyword == "PRINT":
            self.compile_print(tail, line)
            return
        if keyword == "LET":
            self.compile_assignment(tail, line)
            return
        if keyword == "IF":
            self.compile_if(tail, line)
            return
        if keyword == "GOTO":
            if not re.fullmatch(r"\d+", tail):
                raise C64BasicError("GOTO erwartet eine Zeilennummer.", line)
            target = int(tail)
            self.referenced_line_numbers.append((target, line))
            self.emit(f"    jmp __basic_line_{target}")
            return
        if keyword == "GOSUB":
            if not re.fullmatch(r"\d+", tail):
                raise C64BasicError("GOSUB erwartet eine Zeilennummer.", line)
            target = int(tail)
            self.referenced_line_numbers.append((target, line))
            self.emit(f"    jsr __basic_line_{target}")
            return
        if keyword == "RETURN":
            self.emit("    rts")
            return
        if keyword == "FOR":
            self.compile_for(tail, line)
            return
        if keyword == "NEXT":
            self.compile_next(tail, line)
            return
        if keyword == "DIM":
            self.compile_dim(tail, line)
            return
        if keyword == "DATA":
            return
        if keyword == "READ":
            self.compile_read(tail, line)
            return
        if keyword == "RESTORE":
            self.compile_restore(tail, line)
            return
        if keyword == "INPUT":
            self.compile_input(tail, line)
            return
        if keyword == "GET":
            self.compile_get(tail, line)
            return
        if keyword == "OPEN":
            self.compile_open(tail, line)
            return
        if keyword == "CLOSE":
            self.compile_close(tail, line)
            return
        if keyword == "CMD":
            self.compile_cmd(tail, line)
            return
        if keyword == "POKE":
            parts = _split_top_level(tail, ",")
            if len(parts) != 2:
                raise C64BasicError("POKE erwartet Adresse und Wert.", line)
            self.compile_numeric_text(parts[0], line)
            self.emit("    jsr __basic_fac_to_int")
            self.emit("    sta $FB")
            self.emit("    stx $FC")
            self.compile_numeric_text(parts[1], line)
            self.emit("    jsr __basic_fac_to_int")
            self.emit("    ldy #$00")
            self.emit("    sta ($FB),y")
            return
        if keyword == "SYS":
            node = _parse_expression(tail, line)
            if node[0] == "number" and Decimal(node[1]) == Decimal(node[1]).to_integral_value():
                address = int(Decimal(node[1])) & 0xFFFF
                self.emit(f"    jsr ${address:04X}")
            else:
                self.compile_numeric_expression(node, line)
                self.emit("    jsr __basic_fac_to_int")
                self.emit("    sta $FB")
                self.emit("    stx $FC")
                self.emit("    jsr __basic_sys_indirect")
            return
        if keyword in {"END", "STOP"}:
            self.emit("    rts")
            return
        if _find_top_level_comparison(statement) is not None:
            self.compile_assignment(statement, line)
            return
        raise C64BasicError(f"BASIC-Anweisung wird nicht unterstützt: {keyword or statement}", line)

    def parse_source(self) -> List[Tuple[int, List[str]]]:
        parsed: List[Tuple[int, List[str]]] = []
        synthetic = 1
        previous = -1
        for physical, raw in enumerate(self.source.splitlines(), 1):
            stripped = raw.strip()
            if not stripped:
                continue
            match = re.match(r"^(\d+)\s*(.*)$", stripped)
            if match:
                number = int(match.group(1))
                rest = match.group(2)
                if number in self.defined_line_numbers:
                    raise C64BasicError("Zeilennummer ist doppelt vorhanden.", number)
                if number <= previous:
                    self.warnings.append(
                        f"BASIC-Zeile {number}: Zeilennummern sind nicht aufsteigend."
                    )
                previous = number
            else:
                number = 60000 + synthetic
                synthetic += 1
                rest = stripped
                self.warnings.append(
                    f"Physische Zeile {physical}: keine BASIC-Zeilennummer; intern {number} verwendet."
                )
            self.defined_line_numbers.add(number)
            parsed.append((number, _split_basic_statements(rest)))
        if not parsed:
            raise C64BasicError("Der BASIC-Quelltext ist leer.")
        return parsed

    def prepare_program(self, parsed: Sequence[Tuple[int, Sequence[str]]]) -> None:
        for number, statements in parsed:
            data_items: List[str] = []
            for statement in statements:
                match = re.match(r"(?is)^\s*([A-Za-z]+)\b\s*(.*)$", statement)
                if match is None:
                    continue
                keyword = match.group(1).upper()
                tail = match.group(2).strip()
                if keyword == "DIM":
                    self.parse_dim_declaration(tail, number)
                elif keyword == "DATA":
                    for item in _split_top_level(tail, ","):
                        stripped = item.strip()
                        if len(stripped) >= 2 and stripped.startswith('"') and stripped.endswith('"'):
                            stripped = stripped[1:-1].replace('""', '"')
                        data_items.append(stripped)
            if data_items:
                self.data_by_line.append((number, data_items))
                self.data_line_labels[number] = f"__basic_data_line_{number}"

    def emit_runtime(self) -> None:
        self.emit("")
        self.emit("; ---- C64 BASIC Fließkomma-/String-/I/O-Runtime --------------------")
        self.emit("; C64-CBSS: nicht im PRG gespeicherter, beim Start genullter RAM")
        self.emit("__basic_init_cbss:")
        self.emit("    lda #<__basic_cbss_start")
        self.emit("    sta $FB")
        self.emit("    lda #>__basic_cbss_start")
        self.emit("    sta $FC")
        self.emit("    lda #$00")
        self.emit("    ldx #>(__basic_cbss_end-__basic_cbss_start)")
        self.emit("    beq __basic_init_cbss_remainder")
        self.emit("__basic_init_cbss_page:")
        self.emit("    ldy #$00")
        self.emit("__basic_init_cbss_page_loop:")
        self.emit("    sta ($FB),y")
        self.emit("    iny")
        self.emit("    bne __basic_init_cbss_page_loop")
        self.emit("    inc $FC")
        self.emit("    dex")
        self.emit("    bne __basic_init_cbss_page")
        self.emit("__basic_init_cbss_remainder:")
        self.emit("    ldy #$00")
        self.emit("__basic_init_cbss_remainder_loop:")
        self.emit("    cpy #<(__basic_cbss_end-__basic_cbss_start)")
        self.emit("    beq __basic_init_cbss_done")
        self.emit("    sta ($FB),y")
        self.emit("    iny")
        self.emit("    bne __basic_init_cbss_remainder_loop")
        self.emit("__basic_init_cbss_done:")
        self.emit("    rts")
        self.emit("")
        self.emit("__basic_newline:")
        self.emit("    lda #$0D")
        self.emit("    jmp $FFD2")
        self.emit("")
        self.emit("__basic_print_string:")
        self.emit("    sta $FB")
        self.emit("    sty $FC")
        self.emit("    ldy #$00")
        self.emit("    lda ($FB),y")
        self.emit("    tax")
        self.emit("    beq __basic_print_string_done")
        self.emit("    inc $FB")
        self.emit("    bne __basic_print_string_ptr_ok")
        self.emit("    inc $FC")
        self.emit("__basic_print_string_ptr_ok:")
        self.emit("    ldy #$00")
        self.emit("__basic_print_string_loop:")
        self.emit("    lda ($FB),y")
        self.emit("    jsr $FFD2")
        self.emit("    iny")
        self.emit("    dex")
        self.emit("    bne __basic_print_string_loop")
        self.emit("__basic_print_string_done:")
        self.emit("    rts")
        self.emit("")
        if self._inline_pointer_runtime_needed:
            self.emit("; Inline-Pointer PRINT: JSR + .word Stringadresse")
            self.emit("__basic_print_literal_inline:")
            self.emit("    pla")
            self.emit("    sta $FB")
            self.emit("    pla")
            self.emit("    sta $FC")
            self.emit("    inc $FB")
            self.emit("    bne __basic_print_literal_ptr_ready")
            self.emit("    inc $FC")
            self.emit("__basic_print_literal_ptr_ready:")
            self.emit("    ldy #$00")
            self.emit("    lda ($FB),y")
            self.emit("    sta $FD")
            self.emit("    iny")
            self.emit("    lda ($FB),y")
            self.emit("    sta $FE")
            # Returnadresse ist aktuell die Adresse des ersten Inline-Bytes.
            # Für RTS muss Adresse_des_zweiten_Inline_Bytes auf dem Stack liegen,
            # damit das implizite +1 hinter das .word springt.
            self.emit("    inc $FB")
            self.emit("    bne __basic_print_literal_return_ready")
            self.emit("    inc $FC")
            self.emit("__basic_print_literal_return_ready:")
            self.emit("    lda $FC")
            self.emit("    pha")
            self.emit("    lda $FB")
            self.emit("    pha")
            self.emit("    lda $FD")
            self.emit("    ldy $FE")
            self.emit("    jmp __basic_print_string")
            self.emit("")
        self.emit("__basic_print_z:")
        self.emit("    sta $FB")
        self.emit("    sty $FC")
        self.emit("    ldy #$00")
        self.emit("__basic_print_z_loop:")
        self.emit("    lda ($FB),y")
        self.emit("    beq __basic_print_z_done")
        self.emit("    jsr $FFD2")
        self.emit("    iny")
        self.emit("    bne __basic_print_z_loop")
        self.emit("__basic_print_z_done:")
        self.emit("    rts")
        self.emit("")
        self.emit("__basic_print_float:")
        self.emit("    jsr $BDDD")              # FOUT: FAC -> zero-terminated string
        self.emit("    jmp __basic_print_z")
        self.emit("")
        self.emit("__basic_float_to_string_term:")
        self.emit("    jsr $BDDD")
        self.emit("    sta $FD")
        self.emit("    sty $FE")
        self.emit("    ldx #$00")
        self.emit("    ldy #$00")
        self.emit("__basic_float_to_string_loop:")
        self.emit("    lda ($FD),y")
        self.emit("    beq __basic_float_to_string_done")
        self.emit("    sta __basic_string_term+1,x")
        self.emit("    inx")
        self.emit("    iny")
        self.emit("    cpx #$FF")
        self.emit("    bne __basic_float_to_string_loop")
        self.emit("__basic_float_to_string_done:")
        self.emit("    stx __basic_string_term")
        self.emit("    rts")
        self.emit("")
        self.emit("; FAC-/Integer-Konvertierung")
        self.emit("__basic_fac_to_int:")
        self.emit("    jsr $B1AA")              # FACINX: Y=low, A=high
        self.emit("    tax")
        self.emit("    tya")
        self.emit("    rts")
        self.emit("__basic_int_to_fac:")
        self.emit("    tay")                    # input A=low, X=high
        self.emit("    txa")
        self.emit("    jmp $B391")              # GIVAYF
        self.emit("")
        self.emit("; Kompatible Arithmetik-Helfernamen; linker Operand liegt im Speicher A/Y")
        self.emit("__basic_add:")
        self.emit("    jmp $B867")
        self.emit("__basic_sub:")
        self.emit("    jmp $B850")
        self.emit("__basic_mul:")
        self.emit("    jmp $BA28")
        self.emit("__basic_div:")
        self.emit("    jmp $BB0F")
        self.emit("")
        self.emit("; Vergleich: FAC ist rechter Operand, Speicher A/Y ist linker Operand")
        for label, relation in (
            ("__basic_cmp_eq", "eq"),
            ("__basic_cmp_ne", "ne"),
            ("__basic_cmp_lt", "lt"),
            ("__basic_cmp_gt", "gt"),
            ("__basic_cmp_le", "le"),
            ("__basic_cmp_ge", "ge"),
        ):
            true_label = label + "_true"
            self.emit(f"{label}:")
            self.emit("    jsr $BC5B")
            if relation == "eq":
                self.emit(f"    beq {true_label}")
            elif relation == "ne":
                self.emit(f"    bne {true_label}")
            elif relation == "lt":
                self.emit("    cmp #$01")
                self.emit(f"    beq {true_label}")
            elif relation == "gt":
                self.emit("    cmp #$FF")
                self.emit(f"    beq {true_label}")
            elif relation == "le":
                self.emit("    cmp #$FF")
                self.emit(f"    bne {true_label}")
            else:
                self.emit("    cmp #$01")
                self.emit(f"    bne {true_label}")
            self.emit("    lda #<__basic_float_zero")
            self.emit("    ldy #>__basic_float_zero")
            self.emit("    jmp $BBA2")
            self.emit(f"{true_label}:")
            self.emit("    lda #<__basic_float_one")
            self.emit("    ldy #>__basic_float_one")
            self.emit("    jmp $BBA2")
        self.emit("")
        self.emit("__basic_int_and:")
        self.emit("    lda __basic_int_left")
        self.emit("    and __basic_int_right")
        self.emit("    pha")
        self.emit("    lda __basic_int_left+1")
        self.emit("    and __basic_int_right+1")
        self.emit("    tax")
        self.emit("    pla")
        self.emit("    rts")
        self.emit("__basic_int_or:")
        self.emit("    lda __basic_int_left")
        self.emit("    ora __basic_int_right")
        self.emit("    pha")
        self.emit("    lda __basic_int_left+1")
        self.emit("    ora __basic_int_right+1")
        self.emit("    tax")
        self.emit("    pla")
        self.emit("    rts")
        self.emit("")
        self.emit("__basic_u16_add:")
        self.emit("    clc")
        self.emit("    lda __basic_int_left")
        self.emit("    adc __basic_int_right")
        self.emit("    pha")
        self.emit("    lda __basic_int_left+1")
        self.emit("    adc __basic_int_right+1")
        self.emit("    tax")
        self.emit("    pla")
        self.emit("    rts")
        self.emit("__basic_u16_mul:")
        self.emit("    lda #$00")
        self.emit("    sta __basic_int_result")
        self.emit("    sta __basic_int_result+1")
        self.emit("    ldy #$10")
        self.emit("__basic_u16_mul_loop:")
        self.emit("    lsr __basic_int_right+1")
        self.emit("    ror __basic_int_right")
        self.emit("    bcc __basic_u16_mul_skip")
        self.emit("    clc")
        self.emit("    lda __basic_int_result")
        self.emit("    adc __basic_int_left")
        self.emit("    sta __basic_int_result")
        self.emit("    lda __basic_int_result+1")
        self.emit("    adc __basic_int_left+1")
        self.emit("    sta __basic_int_result+1")
        self.emit("__basic_u16_mul_skip:")
        self.emit("    asl __basic_int_left")
        self.emit("    rol __basic_int_left+1")
        self.emit("    dey")
        self.emit("    bne __basic_u16_mul_loop")
        self.emit("    lda __basic_int_result")
        self.emit("    ldx __basic_int_result+1")
        self.emit("    rts")
        self.emit("__basic_int_mod:")
        self.emit("    lda __basic_int_right")
        self.emit("    ora __basic_int_right+1")
        self.emit("    bne __basic_int_mod_nonzero")
        self.emit("    lda #$00")
        self.emit("    tax")
        self.emit("    rts")
        self.emit("__basic_int_mod_nonzero:")
        self.emit("__basic_int_mod_loop:")
        self.emit("    lda __basic_int_left+1")
        self.emit("    cmp __basic_int_right+1")
        self.emit("    bcc __basic_int_mod_done")
        self.emit("    bne __basic_int_mod_sub")
        self.emit("    lda __basic_int_left")
        self.emit("    cmp __basic_int_right")
        self.emit("    bcc __basic_int_mod_done")
        self.emit("__basic_int_mod_sub:")
        self.emit("    sec")
        self.emit("    lda __basic_int_left")
        self.emit("    sbc __basic_int_right")
        self.emit("    sta __basic_int_left")
        self.emit("    lda __basic_int_left+1")
        self.emit("    sbc __basic_int_right+1")
        self.emit("    sta __basic_int_left+1")
        self.emit("    jmp __basic_int_mod_loop")
        self.emit("__basic_int_mod_done:")
        self.emit("    lda __basic_int_left")
        self.emit("    ldx __basic_int_left+1")
        self.emit("    rts")
        self.emit("")
        self.emit("; Stringroutinen: [Länge][bis zu 255 Bytes]")
        self.emit("__basic_string_clear:")
        self.emit("    ldy #$00")
        self.emit("    lda #$00")
        self.emit("    sta ($FB),y")
        self.emit("    rts")
        self.emit("__basic_string_copy:")
        self.emit("    jsr __basic_string_clear")
        self.emit("    jmp __basic_string_append")
        self.emit("__basic_string_append:")
        # Der Zielpointer muss auch nach Seitenwechseln sicher erhalten bleiben.
        self.emit("    lda $FB")
        self.emit("    sta __basic_string_base_ptr")
        self.emit("    lda $FC")
        self.emit("    sta __basic_string_base_ptr+1")
        self.emit("    ldy #$00")
        self.emit("    lda ($FB),y")
        self.emit("    sta __basic_string_dest_length")
        self.emit("    lda ($FD),y")
        self.emit("    sta __basic_string_source_length")
        self.emit("    beq __basic_string_append_empty")
        # Pointer auf erstes Quellzeichen.
        self.emit("    inc $FD")
        self.emit("    bne __basic_string_src_ptr_ok")
        self.emit("    inc $FE")
        self.emit("__basic_string_src_ptr_ok:")
        # Zielpointer = Basis + 1 + bestehende Länge, vollständig 16-Bit-sicher.
        self.emit("    clc")
        self.emit("    lda $FB")
        self.emit("    adc __basic_string_dest_length")
        self.emit("    sta $FB")
        self.emit("    lda $FC")
        self.emit("    adc #$00")
        self.emit("    sta $FC")
        self.emit("    inc $FB")
        self.emit("    bne __basic_string_dst_ptr_ok")
        self.emit("    inc $FC")
        self.emit("__basic_string_dst_ptr_ok:")
        self.emit("    ldx #$00")
        self.emit("__basic_string_append_loop:")
        self.emit("    lda __basic_string_dest_length")
        self.emit("    cmp #$FF")
        self.emit("    beq __basic_string_append_done")
        self.emit("    ldy #$00")
        self.emit("    lda ($FD),y")
        self.emit("    sta ($FB),y")
        self.emit("    inc $FD")
        self.emit("    bne __basic_string_append_src_ok")
        self.emit("    inc $FE")
        self.emit("__basic_string_append_src_ok:")
        self.emit("    inc $FB")
        self.emit("    bne __basic_string_append_dst_ok")
        self.emit("    inc $FC")
        self.emit("__basic_string_append_dst_ok:")
        self.emit("    inc __basic_string_dest_length")
        self.emit("    inx")
        self.emit("    cpx __basic_string_source_length")
        self.emit("    bne __basic_string_append_loop")
        self.emit("__basic_string_append_done:")
        self.emit("    lda __basic_string_base_ptr")
        self.emit("    sta $FB")
        self.emit("    lda __basic_string_base_ptr+1")
        self.emit("    sta $FC")
        self.emit("    ldy #$00")
        self.emit("    lda __basic_string_dest_length")
        self.emit("    sta ($FB),y")
        self.emit("__basic_string_append_empty:")
        self.emit("    rts")
        self.emit("")
        self.emit("__basic_string_compare:")
        self.emit("    ldy #$00")
        self.emit("    lda ($FB),y")
        self.emit("    sta __basic_string_left_length")
        self.emit("    lda ($FD),y")
        self.emit("    sta __basic_string_right_length")
        self.emit("    inc $FB")
        self.emit("    bne __basic_string_cmp_lptr_ok")
        self.emit("    inc $FC")
        self.emit("__basic_string_cmp_lptr_ok:")
        self.emit("    inc $FD")
        self.emit("    bne __basic_string_cmp_rptr_ok")
        self.emit("    inc $FE")
        self.emit("__basic_string_cmp_rptr_ok:")
        self.emit("    ldy #$00")
        self.emit("__basic_string_cmp_loop:")
        self.emit("    cpy __basic_string_left_length")
        self.emit("    beq __basic_string_cmp_left_end")
        self.emit("    cpy __basic_string_right_length")
        self.emit("    beq __basic_string_cmp_right_shorter")
        self.emit("    lda ($FB),y")
        self.emit("    cmp ($FD),y")
        self.emit("    bcc __basic_string_cmp_less")
        self.emit("    bne __basic_string_cmp_greater")
        self.emit("    iny")
        self.emit("    bne __basic_string_cmp_loop")
        self.emit("__basic_string_cmp_left_end:")
        self.emit("    cpy __basic_string_right_length")
        self.emit("    beq __basic_string_cmp_equal")
        self.emit("__basic_string_cmp_less:")
        self.emit("    lda #$FF")
        self.emit("    rts")
        self.emit("__basic_string_cmp_right_shorter:")
        self.emit("__basic_string_cmp_greater:")
        self.emit("    lda #$01")
        self.emit("    rts")
        self.emit("__basic_string_cmp_equal:")
        self.emit("    lda #$00")
        self.emit("    rts")
        self.emit("")
        self.emit("; INPUT/INPUT#/READ-Feldpuffer")
        self.emit("__basic_read_line:")
        self.emit("    ldx #$00")
        self.emit("__basic_read_line_loop:")
        self.emit("    jsr $FFCF")
        self.emit("    cmp #$0D")
        self.emit("    beq __basic_read_line_done")
        self.emit("    cpx #$FF")
        self.emit("    beq __basic_read_line_done")
        self.emit("    sta __basic_input_buffer+1,x")
        self.emit("    inx")
        self.emit("    bne __basic_read_line_loop")
        self.emit("__basic_read_line_done:")
        self.emit("    stx __basic_input_buffer")
        self.emit("    rts")
        self.emit("__basic_input_next_field:")
        self.emit("    ldy __basic_field_position")
        self.emit("__basic_input_skip_spaces:")
        self.emit("    cpy __basic_input_buffer")
        self.emit("    beq __basic_input_field_empty")
        self.emit("    lda __basic_input_buffer+1,y")
        self.emit("    cmp #$20")
        self.emit("    bne __basic_input_copy_start")
        self.emit("    iny")
        self.emit("    bne __basic_input_skip_spaces")
        self.emit("__basic_input_copy_start:")
        self.emit("    ldx #$00")
        self.emit("__basic_input_copy_loop:")
        self.emit("    cpy __basic_input_buffer")
        self.emit("    beq __basic_input_copy_done")
        self.emit("    lda __basic_input_buffer+1,y")
        self.emit("    cmp #$2C")
        self.emit("    beq __basic_input_comma")
        self.emit("    sta __basic_field_buffer+1,x")
        self.emit("    inx")
        self.emit("    iny")
        self.emit("    bne __basic_input_copy_loop")
        self.emit("__basic_input_comma:")
        self.emit("    iny")
        self.emit("__basic_input_copy_done:")
        self.emit("    sty __basic_field_position")
        # Nachlaufende Leerzeichen entfernen.
        self.emit("__basic_input_trim:")
        self.emit("    cpx #$00")
        self.emit("    beq __basic_input_field_store")
        self.emit("    lda __basic_field_buffer,x")
        self.emit("    cmp #$20")
        self.emit("    bne __basic_input_field_store")
        self.emit("    dex")
        self.emit("    jmp __basic_input_trim")
        self.emit("__basic_input_field_empty:")
        self.emit("    ldx #$00")
        self.emit("__basic_input_field_store:")
        self.emit("    stx __basic_field_buffer")
        self.emit("    rts")
        self.emit("__basic_field_to_float:")
        self.emit("    lda __basic_field_buffer")
        self.emit("    bne __basic_field_to_float_nonempty")
        self.emit("    lda #<__basic_float_zero")
        self.emit("    ldy #>__basic_float_zero")
        self.emit("    jmp $BBA2")
        self.emit("__basic_field_to_float_nonempty:")
        self.emit("    lda #<__basic_field_buffer+1")
        self.emit("    sta $22")
        self.emit("    lda #>__basic_field_buffer+1")
        self.emit("    sta $23")
        self.emit("    lda __basic_field_buffer")
        self.emit("    jmp $B7B5")
        self.emit("")
        self.emit("__basic_data_read_field:")
        self.emit("    lda __basic_data_ptr")
        self.emit("    sta $FB")
        self.emit("    lda __basic_data_ptr+1")
        self.emit("    sta $FC")
        self.emit("    ldy #$00")
        self.emit("    lda ($FB),y")
        self.emit("    cmp #$FF")
        self.emit("    bne __basic_data_available")
        self.emit("    jmp __basic_out_of_data")
        self.emit("__basic_data_available:")
        self.emit("    tax")
        self.emit("    sta __basic_field_buffer")
        self.emit("    inc $FB")
        self.emit("    bne __basic_data_ptr_ok")
        self.emit("    inc $FC")
        self.emit("__basic_data_ptr_ok:")
        self.emit("    ldy #$00")
        self.emit("__basic_data_copy_loop:")
        self.emit("    cpx #$00")
        self.emit("    beq __basic_data_copy_done")
        self.emit("    lda ($FB),y")
        self.emit("    sta __basic_field_buffer+1,y")
        self.emit("    iny")
        self.emit("    dex")
        self.emit("    bne __basic_data_copy_loop")
        self.emit("__basic_data_copy_done:")
        self.emit("    tya")
        self.emit("    clc")
        self.emit("    adc $FB")
        self.emit("    sta __basic_data_ptr")
        self.emit("    lda $FC")
        self.emit("    adc #$00")
        self.emit("    sta __basic_data_ptr+1")
        self.emit("    rts")
        self.emit("")
        self.emit("__basic_sys_indirect:")
        self.emit("    jmp ($FB)")
        self.emit("")
        self.emit("__basic_bad_subscript:")
        self.emit("    lda #<__basic_error_bad_subscript")
        self.emit("    ldy #>__basic_error_bad_subscript")
        self.emit("    jsr __basic_print_z")
        self.emit("    jmp __basic_abort")
        self.emit("__basic_out_of_data:")
        self.emit("    lda #<__basic_error_out_of_data")
        self.emit("    ldy #>__basic_error_out_of_data")
        self.emit("    jsr __basic_print_z")
        self.emit("__basic_abort:")
        self.emit("    ldx __basic_entry_sp")
        self.emit("    txs")
        self.emit("    jmp __basic_program_end")

    def emit_print_literal_thunks(self) -> None:
        if not self._string_literal_thunks:
            return
        self.emit("")
        self.emit("; ---- Optimizer: String-Thunks --------------------------------------")
        for symbol in sorted(
            self._string_literal_thunks,
            key=lambda value: int(str(value).rsplit("_", 1)[-1])
            if str(value).rsplit("_", 1)[-1].isdigit() else str(value),
        ):
            self.emit(f"{self._print_thunk_label(symbol)}:")
            self.emit(f"    lda #<{symbol}")
            self.emit(f"    ldy #>{symbol}")
            self.emit("    jmp __basic_print_string")

    def emit_storage(self) -> None:
        # Geladene, unveränderliche/initialisierte Daten kommen zuerst. Alles
        # was beim BASIC-Programmstart den Wert 0 haben soll, wird danach in
        # einem C64-spezifischen .cbss-Bereich nur adressiert, nicht ins PRG
        # geschrieben. __basic_init_cbss löscht diesen RAM vor der ersten
        # BASIC-Zeile.
        self.emit("")
        self.emit("; ---- Fließkommakonstanten im kompakten CBM-5-Byte-Format ----------")
        # Stabile Aliasnamen für Runtime und Tests.
        zero_symbol = self.float_constant(Decimal(0))
        one_symbol = self.float_constant(Decimal(1))
        self.emit(f"__basic_float_zero = {zero_symbol}")
        self.emit(f"__basic_float_one = {one_symbol}")
        for _key, (symbol, payload) in self.float_constants.items():
            values = ", ".join(f"${byte:02X}" for byte in payload)
            self.emit(f"{symbol}: .byte {values}")

        if self.string_literals:
            self.emit("")
            self.emit("; ---- ShortString-Literale: [1 Byte Länge][0..255 Datenbytes] ------")
            for symbol, payload in self.string_literals:
                values = ", ".join(f"${byte:02X}" for byte in bytes((len(payload),)) + payload)
                self.emit(f"{symbol}: .byte {values}")

        self.emit("")
        self.emit("; ---- DATA-Tabelle: [Länge][Textbytes], $FF beendet -----------------")
        self.emit("__basic_data_start:")
        for number, items in self.data_by_line:
            self.emit(f"{self.data_line_labels[number]}:")
            for item in items:
                payload = _petscii_bytes(item)
                values = ", ".join(f"${byte:02X}" for byte in bytes((len(payload),)) + payload)
                self.emit(f"    .byte {values}")
        self.emit("__basic_data_end: .byte $FF")
        self.emit('__basic_error_bad_subscript: .byte "?BAD SUBSCRIPT ERROR", $0D, $00')
        self.emit('__basic_error_out_of_data: .byte "?OUT OF DATA ERROR", $0D, $00')

        self.emit("")
        self.emit("; ---- Ende des physisch im PRG gespeicherten Images ----------------")
        self.emit("__basic_image_end:")
        self.emit("")
        self.emit("; ---- C64 CBSS: nur RAM-Adressen, KEINE Bytes im PRG ----------------")
        self.emit("; Strings sind Pascal/Turbo-Pascal-artige ShortStrings:")
        self.emit(";   Byte 0 = Länge 0..255, Byte 1..255 = Zeichen")
        self.emit("__basic_cbss_start:")

        for _name, (symbol, kind) in sorted(self.numeric_variables.items()):
            size = 5 if kind == "float" else 2
            self.emit(f"{symbol}: .cbss {size}")
        for _name, symbol in sorted(self.string_variables.items()):
            self.emit(f"{symbol}: .cbss 256")
        for _name, info in sorted(self.arrays.items()):
            self.emit(f"{info.symbol}: .cbss {info.byte_size}")
        for symbol in self.float_temporaries:
            self.emit(f"{symbol}: .cbss 5")
        for symbol in ("__basic_float_hold", "__basic_float_hold2"):
            self.emit(f"{symbol}: .cbss 5")
        for symbol in (
            "__basic_int_left", "__basic_int_right", "__basic_int_result",
            "__basic_int_hold", "__basic_index", "__basic_linear_index",
            "__basic_dest_ptr", "__basic_data_ptr", "__basic_string_base_ptr",
        ):
            self.emit(f"{symbol}: .cbss 2")
        for symbol in (
            "__basic_compare_result", "__basic_string_dest_length",
            "__basic_string_source_length", "__basic_string_left_length",
            "__basic_string_right_length", "__basic_field_position",
            "__basic_get_char", "__basic_lfn", "__basic_device",
            "__basic_secondary", "__basic_entry_sp",
        ):
            self.emit(f"{symbol}: .cbss 1")
        for symbol in (
            "__basic_string_expr", "__basic_string_left", "__basic_string_right",
            "__basic_string_term", "__basic_input_buffer", "__basic_field_buffer",
        ):
            self.emit(f"{symbol}: .cbss 256")

        self.emit("__basic_cbss_end:")

    def compile(self) -> C64BasicCompileResult:
        parsed = self.parse_source()
        self.prepare_program(parsed)
        # Runtime benötigt diese Konstanten unabhängig vom Quelltext.
        self.float_constant(Decimal(0))
        self.float_constant(Decimal(1))

        self.emit("; ---------------------------------------------------------------------------")
        self.emit(f"; C64 BASIC Compiler output: {self.filename}")
        self.emit("; CBM-5-Byte-Fließkomma, Strings, Arrays, DATA/INPUT und KERNAL-I/O")
        self.emit("; Ziel: MOS 6510 / Commodore 64")
        self.emit("; ---------------------------------------------------------------------------")
        self.emit(".org $080D")
        self.emit(".entry __basic_start")
        self.emit("")
        self.emit("__basic_start:")
        self.emit("    jsr __basic_init_cbss")
        self.emit("    tsx")
        self.emit("    stx __basic_entry_sp")
        self.emit("    lda #<__basic_data_start")
        self.emit("    sta __basic_data_ptr")
        self.emit("    lda #>__basic_data_start")
        self.emit("    sta __basic_data_ptr+1")
        for number, statements in parsed:
            self.emit(f"__basic_line_{number}:")
            for statement in statements:
                self.compile_statement(statement, number)
        if self.for_stack:
            context = self.for_stack[-1]
            raise C64BasicError(
                f"FOR {context['name']} aus Zeile {context['line']} besitzt kein NEXT."
            )
        self.emit("__basic_program_end:")
        self.emit("    jsr $FFCC")             # Kanäle sicher auf Standard zurückstellen
        self.emit("    rts")

        missing = sorted(
            {target for target, _source in self.referenced_line_numbers}
            - self.defined_line_numbers
        )
        if missing:
            source_line = next(
                source for target, source in self.referenced_line_numbers
                if target == missing[0]
            )
            raise C64BasicError(
                f"Sprungziel {missing[0]} ist nicht vorhanden.", source_line
            )

        self.resolve_auto_print_literals()
        self.emit_runtime()
        self.emit_print_literal_thunks()
        self.emit_storage()
        self.emit("end")
        optimizer_stats = self.optimizer.stats
        notes = (
            "Numerische Standardvariablen verwenden das originale 5-Byte-CBM-Fließkommaformat.",
            "Variablen mit %-Suffix und Integerarrays verwenden 16-Bit-Ganzzahlen.",
            "Strings verwenden 256-Byte-ShortString-Slots: 1 Längenbyte (0..255) plus bis zu 255 Zeichen.",
            "Nullinitialisierte Variablen, Arrays und Runtime-Puffer liegen im C64-CBSS hinter dem PRG und werden beim Start per 6510-Schleife gelöscht.",
            "OPEN/CLOSE/CMD/PRINT#/INPUT#/GET# verwenden die C64-KERNAL-Sprungtabelle.",
            (
                "Optimizer: "
                + ("aktiv" if self.optimizer_enabled else "deaktiviert")
                + f"; Strategie={self.optimizer_strategy}; "
                f"{optimizer_stats.constant_folds} Konstantenfaltung(en), "
                f"{optimizer_stats.streamed_print_expressions} direkt gestreamte PRINT-Ausdrücke, "
                f"{optimizer_stats.avoided_string_materializations} vermiedene String-Zwischenpuffer; "
                f"Literal-PRINT direct={optimizer_stats.direct_literal_prints}, "
                f"inline={optimizer_stats.inline_pointer_prints}, "
                f"thunk={optimizer_stats.string_thunk_prints}."
            ),
            "Der erzeugte ASM-Code kann im ASM-Tab geprüft und anschließend assembliert werden.",
        )
        return C64BasicCompileResult(
            assembly="\n".join(self.lines) + "\n",
            warnings=tuple(self.warnings),
            notes=notes,
        )


def compile_basic_to_assembly(
    source: str,
    *,
    filename: str = "<memory>",
    target: str = "c64",
    optimizer_enabled: bool = True,
    optimizer_strategy: str = "direct",
) -> C64BasicCompileResult:
    if str(target).strip().casefold() not in {"c64", "c-64", "commodore64"}:
        raise C64BasicError(
            "Der BASIC-Compiler unterstützt derzeit ausschließlich das Ziel C-64."
        )
    return _BasicCompiler(
        str(source),
        str(filename),
        optimizer_enabled=bool(optimizer_enabled),
        optimizer_strategy=optimizer_strategy,
    ).compile()
