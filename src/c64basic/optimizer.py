from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, DivisionByZero, InvalidOperation, localcontext
import re
from typing import Optional, Tuple

PRINT_STRATEGIES = ("direct", "inline_pointer", "string_thunk", "auto")


def normalize_print_strategy(value: str) -> str:
    text = str(value or "direct").strip().casefold().replace(" ", "_")
    aliases = {
        "inline": "inline_pointer",
        "inlinepointer": "inline_pointer",
        "inline-pointer": "inline_pointer",
        "thunk": "string_thunk",
        "stringthunk": "string_thunk",
        "string-thunk": "string_thunk",
    }
    text = aliases.get(text, text)
    return text if text in PRINT_STRATEGIES else "direct"


Node = Tuple


@dataclass
class C64BasicOptimizerStats:
    constant_folds: int = 0
    streamed_print_expressions: int = 0
    streamed_print_terms: int = 0
    avoided_string_materializations: int = 0
    direct_literal_prints: int = 0
    inline_pointer_prints: int = 0
    string_thunk_prints: int = 0


class C64BasicOptimizer:
    """Kleine, sichere Optimierungsstufe für den C64-BASIC-Codegenerator.

    Die Stufe arbeitet auf dem bereits geparsten Ausdrucksbaum bzw. auf der
    Struktur eines PRINT-Stringausdrucks. Sie verändert keine Variablen- oder
    Kontrollflusssemantik.
    """

    _COMPARISONS = {"=", "<>", "<", ">", "<=", ">="}
    _STRING_TERM_RE = re.compile(
        r"(?is)^\s*[A-Za-z_][A-Za-z0-9_]*\$(?:\s*\(.*\))?\s*$"
    )
    _STRING_FUNCTION_RE = re.compile(r"(?is)^\s*(?:CHR\$|STR\$)\s*\(.*\)\s*$")
    _STRING_LITERAL_RE = re.compile(r'(?s)^\s*"(?:""|[^"])*"\s*$')

    def __init__(self) -> None:
        self.stats = C64BasicOptimizerStats()

    def optimize_numeric_node(self, node: Node) -> Node:
        """Faltet reine numerische Konstantenausdrücke.

        Beispiel: 2 + 3 * 4 -> 14. Variablen, Funktionsaufrufe und die
        bitweisen BASIC-Operatoren bleiben unangetastet.
        """
        if not node:
            return node
        kind = node[0]
        if kind in {"number", "variable", "call"}:
            return node
        if kind == "unary":
            operator = str(node[1])
            child = self.optimize_numeric_node(node[2])
            if child[0] == "number" and operator in {"+", "-"}:
                value = Decimal(child[1])
                folded = value if operator == "+" else -value
                self.stats.constant_folds += 1
                return ("number", folded)
            return ("unary", operator, child)
        if kind != "binary":
            return node

        operator = str(node[1])
        left = self.optimize_numeric_node(node[2])
        right = self.optimize_numeric_node(node[3])
        if left[0] != "number" or right[0] != "number":
            return ("binary", operator, left, right)

        # AND/OR/MOD sind in der Runtime 16-Bit-Integeroperationen. Sie werden
        # hier absichtlich nicht gefaltet, damit deren genaue CBM-Semantik
        # unverändert bleibt.
        if operator in {"AND", "OR", "MOD"}:
            return ("binary", operator, left, right)

        a = Decimal(left[1])
        b = Decimal(right[1])
        try:
            with localcontext() as context:
                context.prec = 80
                if operator == "+":
                    result = a + b
                elif operator == "-":
                    result = a - b
                elif operator == "*":
                    result = a * b
                elif operator == "/":
                    # Division durch 0 bleibt eine Runtime-Angelegenheit.
                    if b == 0:
                        return ("binary", operator, left, right)
                    result = a / b
                elif operator in self._COMPARISONS:
                    truth = {
                        "=": a == b,
                        "<>": a != b,
                        "<": a < b,
                        ">": a > b,
                        "<=": a <= b,
                        ">=": a >= b,
                    }[operator]
                    # Der bestehende Compiler repräsentiert TRUE als 1.0.
                    result = Decimal(1 if truth else 0)
                else:
                    return ("binary", operator, left, right)
        except (DivisionByZero, InvalidOperation, OverflowError):
            return ("binary", operator, left, right)

        if not result.is_finite():
            return ("binary", operator, left, right)
        self.stats.constant_folds += 1
        return ("number", result)

    @staticmethod
    def _split_top_level_plus(text: str) -> Tuple[str, ...]:
        result = []
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
                elif char == "+" and depth == 0:
                    result.append(text[start:index].strip())
                    start = index + 1
            index += 1
        result.append(text[start:].strip())
        return tuple(result)

    def direct_print_terms(self, text: str) -> Optional[Tuple[str, ...]]:
        """Liefert Stringterme, die PRINT ohne Zwischenpuffer streamen kann.

        Unterstützt Literale, Stringvariablen/-arrays sowie CHR$/STR$ und
        deren '+'-Verkettung. Der Ausdruck wird dabei links-nach-rechts
        ausgegeben, sodass kein __basic_string_expr + append nötig ist.
        """
        terms = self._split_top_level_plus(text)
        if not terms or any(not term for term in terms):
            return None
        for term in terms:
            if self._STRING_LITERAL_RE.fullmatch(term):
                continue
            if self._STRING_FUNCTION_RE.fullmatch(term):
                continue
            if self._STRING_TERM_RE.fullmatch(term):
                continue
            return None
        return terms

    def record_streamed_print(self, term_count: int) -> None:
        self.stats.streamed_print_expressions += 1
        self.stats.streamed_print_terms += int(term_count)
        self.stats.avoided_string_materializations += 1
