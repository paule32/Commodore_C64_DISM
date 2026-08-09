from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple


class PrologCompilerError(Exception):
    def __init__(self, message: str, line: int = 0, column: int = 0, filename: str = "") -> None:
        self.message = str(message)
        self.line = int(line or 0)
        self.column = int(column or 0)
        self.filename = str(filename or "")
        super().__init__(self.__str__())

    def __str__(self) -> str:
        location = ""
        if self.filename:
            location = self.filename
        if self.line:
            location += (":" if location else "Zeile ") + str(self.line)
            if self.column:
                location += f":{self.column}"
        return f"{location}: {self.message}" if location else self.message


@dataclass(frozen=True)
class PrologToken:
    kind: str
    text: str
    line: int
    column: int


@dataclass(frozen=True)
class PrologTerm:
    kind: str
    value: object = None
    args: Tuple["PrologTerm", ...] = ()
    line: int = 0
    column: int = 0

    @property
    def arity(self) -> int:
        return len(self.args)


@dataclass(frozen=True)
class PrologClause:
    head: PrologTerm
    body: Tuple[PrologTerm, ...] = ()
    line: int = 0


@dataclass(frozen=True)
class PrologQuery:
    goals: Tuple[PrologTerm, ...]
    line: int = 0


@dataclass
class PrologCompileResult:
    assembly: str
    source_kind: str = "program"
    program_name: str = "prolog_program"
    warnings: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()
    linked_assembly_files: Tuple[str, ...] = ()
    linked_pe32_modules: Tuple[Tuple[str, str], ...] = ()
    predicates: Tuple[str, ...] = ()
    query_count: int = 0
    verbose: bool = False


# ---------------------------------------------------------------------------
# Lexer / parser
# ---------------------------------------------------------------------------
_SYMBOLIC_ATOMS = {"!", "+", "-", "*", "/", "<", ">", "=<", ">="}


def _tokenize(source: str, filename: str) -> List[PrologToken]:
    text = str(source or "")
    result: List[PrologToken] = []
    i = 0
    line = 1
    col = 1
    n = len(text)

    def advance(ch: str) -> None:
        nonlocal line, col
        if ch == "\n":
            line += 1
            col = 1
        else:
            col += 1

    while i < n:
        ch = text[i]
        if ch in " \t\r\n":
            advance(ch)
            i += 1
            continue
        if ch == "%":
            while i < n and text[i] not in "\r\n":
                advance(text[i]); i += 1
            continue
        if text.startswith("/*", i):
            start_line, start_col = line, col
            advance("/"); advance("*"); i += 2
            while i < n and not text.startswith("*/", i):
                advance(text[i]); i += 1
            if i >= n:
                raise PrologCompilerError("Blockkommentar wurde nicht geschlossen.", start_line, start_col, filename)
            advance("*"); advance("/"); i += 2
            continue

        start_line, start_col = line, col
        multi = None
        for candidate, kind in (
            (":-", "RULE"), ("?-", "QUERY"), ("\\=", "NE"),
            ("=<", "LE"), (">=", "GE"), ("==", "STRICT_EQ"),
        ):
            if text.startswith(candidate, i):
                multi = (candidate, kind)
                break
        if multi:
            token_text, kind = multi
            result.append(PrologToken(kind, token_text, start_line, start_col))
            for c in token_text:
                advance(c)
            i += len(token_text)
            continue

        singles = {
            "(": "LPAREN", ")": "RPAREN", "[": "LBRACK", "]": "RBRACK",
            "|": "BAR", ",": "COMMA", ".": "DOT", ";": "SEMI",
            "=": "EQ", "!": "CUT", "+": "PLUS", "-": "MINUS",
            "*": "STAR", "/": "SLASH", "<": "LT", ">": "GT",
        }
        if ch in singles:
            # Minus vor einer Ziffer ist Bestandteil der Zahl.
            if ch == "-" and i + 1 < n and text[i + 1].isdigit():
                pass
            else:
                result.append(PrologToken(singles[ch], ch, start_line, start_col))
                advance(ch); i += 1
                continue

        if ch == "'":
            i += 1; advance(ch)
            chars: List[str] = []
            while i < n:
                cur = text[i]
                if cur == "'":
                    if i + 1 < n and text[i + 1] == "'":
                        chars.append("'")
                        advance("'"); advance("'"); i += 2
                        continue
                    advance(cur); i += 1
                    break
                if cur in "\r\n":
                    raise PrologCompilerError("Quoted Atom wurde nicht geschlossen.", start_line, start_col, filename)
                if cur == "\\" and i + 1 < n:
                    advance(cur); i += 1
                    cur = text[i]
                    escapes = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", "'": "'"}
                    chars.append(escapes.get(cur, cur))
                    advance(cur); i += 1
                    continue
                chars.append(cur); advance(cur); i += 1
            else:
                raise PrologCompilerError("Quoted Atom wurde nicht geschlossen.", start_line, start_col, filename)
            result.append(PrologToken("ATOM", "".join(chars), start_line, start_col))
            continue

        if ch == '"':
            i += 1; advance(ch)
            chars: List[str] = []
            while i < n:
                cur = text[i]
                if cur == '"':
                    advance(cur); i += 1
                    break
                if cur in "\r\n":
                    raise PrologCompilerError("String wurde nicht geschlossen.", start_line, start_col, filename)
                if cur == "\\" and i + 1 < n:
                    advance(cur); i += 1
                    cur = text[i]
                    escapes = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", '"': '"'}
                    chars.append(escapes.get(cur, cur))
                    advance(cur); i += 1
                    continue
                chars.append(cur); advance(cur); i += 1
            else:
                raise PrologCompilerError("String wurde nicht geschlossen.", start_line, start_col, filename)
            result.append(PrologToken("STRING", "".join(chars), start_line, start_col))
            continue

        if ch.isdigit() or (ch == "-" and i + 1 < n and text[i + 1].isdigit()):
            start = i
            if ch == "-":
                advance(ch); i += 1
            while i < n and text[i].isdigit():
                advance(text[i]); i += 1
            kind = "NUMBER"
            # The final program terminator in ``1.`` must stay a DOT token.
            # A decimal point is part of a literal only when a digit follows.
            if i + 1 < n and text[i] == "." and text[i + 1].isdigit():
                kind = "FLOAT"
                advance(text[i]); i += 1
                while i < n and text[i].isdigit():
                    advance(text[i]); i += 1
            # Scientific notation, e.g. 1.25e-3 or 2e6.
            if i < n and text[i] in "eE":
                j = i + 1
                if j < n and text[j] in "+-":
                    j += 1
                if j < n and text[j].isdigit():
                    kind = "FLOAT"
                    while i < j:
                        advance(text[i]); i += 1
                    while i < n and text[i].isdigit():
                        advance(text[i]); i += 1
            result.append(PrologToken(kind, text[start:i], start_line, start_col))
            continue

        if ch.isalpha() or ch == "_":
            start = i
            while i < n and (text[i].isalnum() or text[i] == "_"):
                advance(text[i]); i += 1
            word = text[start:i]
            kind = "VAR" if word[0].isupper() or word[0] == "_" else "ATOM"
            result.append(PrologToken(kind, word, start_line, start_col))
            continue

        raise PrologCompilerError(f"Ungültiges PROLOG-Zeichen {ch!r}.", line, col, filename)

    result.append(PrologToken("EOF", "", line, col))
    return result


class _Parser:
    def __init__(self, source: str, filename: str) -> None:
        self.filename = filename
        self.tokens = _tokenize(source, filename)
        self.index = 0
        self._anonymous_counter = 0

    @property
    def current(self) -> PrologToken:
        return self.tokens[self.index]

    def take(self, kind: str) -> PrologToken:
        token = self.current
        if token.kind != kind:
            raise PrologCompilerError(
                f"{kind} erwartet, erhalten: {token.kind} ({token.text!r}).",
                token.line, token.column, self.filename,
            )
        self.index += 1
        return token

    def parse(self) -> Tuple[Tuple[PrologClause, ...], Tuple[PrologQuery, ...]]:
        clauses: List[PrologClause] = []
        queries: List[PrologQuery] = []
        while self.current.kind != "EOF":
            if self.current.kind == "QUERY":
                token = self.take("QUERY")
                goals = self.parse_goal_list()
                self.take("DOT")
                queries.append(PrologQuery(tuple(goals), token.line))
                continue
            head = self.parse_callable_term()
            body: Tuple[PrologTerm, ...] = ()
            if self.current.kind == "RULE":
                self.take("RULE")
                body = tuple(self.parse_goal_list())
            self.take("DOT")
            clauses.append(PrologClause(head, body, head.line))
        return tuple(clauses), tuple(queries)

    @staticmethod
    def _flatten_conjunction(term: PrologTerm) -> List[PrologTerm]:
        if term.kind == "compound" and str(term.value) == "," and len(term.args) == 2:
            return _Parser._flatten_conjunction(term.args[0]) + _Parser._flatten_conjunction(term.args[1])
        return [term]

    def parse_goal_list(self) -> List[PrologTerm]:
        # ISO-like operator precedence for clause bodies and queries:
        #   :-  (only inside parenthesized assert/retract terms)
        #   ;
        #   ,
        #   = \= == is < =< > >=
        #   + -
        #   * / mod
        expr = self.parse_disjunction()
        return self._flatten_conjunction(expr)

    def parse_disjunction(self) -> PrologTerm:
        left = self.parse_conjunction()
        while self.current.kind == "SEMI":
            token = self.take("SEMI")
            right = self.parse_conjunction()
            left = PrologTerm("compound", ";", (left, right), token.line, token.column)
        return left

    def parse_conjunction(self) -> PrologTerm:
        left = self.parse_relation()
        while self.current.kind == "COMMA":
            token = self.take("COMMA")
            right = self.parse_relation()
            left = PrologTerm("compound", ",", (left, right), token.line, token.column)
        return left

    def parse_relation(self) -> PrologTerm:
        left = self.parse_arith_add()
        infix_map = {
            "EQ": "=", "NE": "\\=", "STRICT_EQ": "==",
            "LT": "<", "LE": "=<", "GT": ">", "GE": ">=",
        }
        token = self.current
        operator = infix_map.get(token.kind)
        if operator is None and token.kind == "ATOM" and token.text.casefold() == "is":
            operator = "is"
        if operator is not None:
            self.index += 1
            right = self.parse_arith_add()
            return PrologTerm("compound", operator, (left, right), token.line, token.column)
        return left

    def parse_arith_add(self) -> PrologTerm:
        left = self.parse_arith_mul()
        while self.current.kind in {"PLUS", "MINUS"}:
            token = self.current
            self.index += 1
            right = self.parse_arith_mul()
            left = PrologTerm("compound", token.text, (left, right), token.line, token.column)
        return left

    def parse_fraction_operand(self) -> PrologTerm:
        """Parse one numeric fraction operand before multiplicative operators.

        d64 PROLOG intentionally treats ``number / number`` as one fraction
        operand.  This gives the user-facing arithmetic convention:

            1/2 / 1/2  ->  (1/2) / (1/2)

        instead of ISO Prolog's purely left-associative ``/`` chain.  The
        special grouping is deliberately limited to numeric literals, so
        general expressions such as ``A / B / C`` keep the normal operator
        behaviour unless parentheses make another grouping explicit.
        """
        left = self.parse_unary()
        if left.kind not in {"number", "float"}:
            return left
        if self.current.kind != "SLASH":
            return left
        if self.index + 1 >= len(self.tokens):
            return left
        next_token = self.tokens[self.index + 1]
        if next_token.kind not in {"NUMBER", "FLOAT"}:
            return left
        token = self.current
        self.index += 1
        right = self.parse_unary()
        if right.kind not in {"number", "float"}:
            # Defensive fallback; the token lookahead above should guarantee
            # this, but keep the parser deterministic if token rules evolve.
            raise PrologCompilerError(
                "Numerischer Nenner nach '/' erwartet.",
                token.line, token.column, self.filename,
            )
        return PrologTerm("compound", "/", (left, right), token.line, token.column)

    def parse_arith_mul(self) -> PrologTerm:
        left = self.parse_fraction_operand()
        while True:
            token = self.current
            if token.kind in {"STAR", "SLASH"}:
                self.index += 1
                operator = token.text
            elif token.kind == "ATOM" and token.text.casefold() == "mod":
                self.index += 1
                operator = "mod"
            else:
                break
            right = self.parse_fraction_operand()
            left = PrologTerm("compound", operator, (left, right), token.line, token.column)
        return left

    def parse_unary(self) -> PrologTerm:
        token = self.current
        if token.kind in {"PLUS", "MINUS"}:
            self.index += 1
            value = self.parse_unary()
            return PrologTerm("compound", token.text, (value,), token.line, token.column)
        return self.parse_term()

    def parse_nested_rule_term(self) -> PrologTerm:
        # Used for terms such as assert((head(X) :- body(X), more(X))).
        left = self.parse_disjunction()
        if self.current.kind == "RULE":
            token = self.take("RULE")
            right = self.parse_disjunction()
            return PrologTerm("compound", ":-", (left, right), token.line, token.column)
        return left

    def parse_goal(self) -> PrologTerm:
        return self.parse_relation()

    def parse_callable_term(self) -> PrologTerm:
        term = self.parse_term()
        if term.kind not in {"atom", "compound"}:
            raise PrologCompilerError(
                "Prädikatkopf muss ein Atom oder zusammengesetzter Term sein.",
                term.line, term.column, self.filename,
            )
        return term

    def parse_term(self) -> PrologTerm:
        token = self.current
        if token.kind == "VAR":
            self.index += 1
            name = token.text
            if name == "_":
                self._anonymous_counter += 1
                name = f"__anon_{self._anonymous_counter}"
            return PrologTerm("var", name, line=token.line, column=token.column)
        if token.kind == "NUMBER":
            self.index += 1
            return PrologTerm("number", int(token.text, 10), line=token.line, column=token.column)
        if token.kind == "FLOAT":
            self.index += 1
            return PrologTerm("float", float(token.text), line=token.line, column=token.column)
        if token.kind == "STRING":
            self.index += 1
            return PrologTerm("string", token.text, line=token.line, column=token.column)
        if token.kind == "CUT":
            self.index += 1
            return PrologTerm("atom", "!", line=token.line, column=token.column)
        if token.kind == "ATOM":
            self.index += 1
            atom = PrologTerm("atom", token.text, line=token.line, column=token.column)
            if self.current.kind != "LPAREN":
                return atom
            self.take("LPAREN")
            args: List[PrologTerm] = []
            if self.current.kind != "RPAREN":
                # A comma at this level separates arguments.  A parenthesized
                # argument may itself contain conjunction/disjunction/rules.
                args.append(self.parse_relation())
                while self.current.kind == "COMMA":
                    self.take("COMMA")
                    args.append(self.parse_relation())
            self.take("RPAREN")
            return PrologTerm("compound", token.text, tuple(args), token.line, token.column)
        if token.kind == "LBRACK":
            return self.parse_list_term()
        if token.kind == "LPAREN":
            self.take("LPAREN")
            term = self.parse_nested_rule_term()
            self.take("RPAREN")
            return term
        raise PrologCompilerError(
            f"Term erwartet, erhalten: {token.kind} ({token.text!r}).",
            token.line, token.column, self.filename,
        )

    def parse_list_term(self) -> PrologTerm:
        token = self.take("LBRACK")
        if self.current.kind == "RBRACK":
            self.take("RBRACK")
            return PrologTerm("atom", "[]", line=token.line, column=token.column)

        items: List[PrologTerm] = [self.parse_relation()]
        tail = PrologTerm("atom", "[]", line=token.line, column=token.column)
        while self.current.kind == "COMMA":
            self.take("COMMA")
            items.append(self.parse_relation())
        if self.current.kind == "BAR":
            self.take("BAR")
            tail = self.parse_relation()
        self.take("RBRACK")
        for item in reversed(items):
            tail = PrologTerm("compound", ".", (item, tail), token.line, token.column)
        return tail


def parse_prolog(source: str, *, filename: str = "<PROLOG>") -> Tuple[Tuple[PrologClause, ...], Tuple[PrologQuery, ...]]:
    return _Parser(source, filename).parse()


# ---------------------------------------------------------------------------
# Kleine automatisch verfuegbare PROLOG-Standardbibliothek.  Diese Praedikate
# werden nicht in Python ausgewertet, sondern als normale Klauseln in die
# native Runtime aufgenommen. Dadurch verwenden sie exakt denselben Trail-,
# Choice-Point- und Unifikationspfad wie benutzerdefinierte Praedikate.
#
# Ein benutzerdefiniertes Praedikat mit derselben Signatur gewinnt: in diesem
# Fall wird die Standarddefinition nicht zusaetzlich eingebunden.
# ---------------------------------------------------------------------------
_PROLOG_STANDARD_LIBRARY_SOURCE = r"""
member(X, [X|_]).
member(X, [_|T]) :- member(X, T).
"""

_PROLOG_STANDARD_LIBRARY_CLAUSES, _PROLOG_STANDARD_LIBRARY_QUERIES = parse_prolog(
    _PROLOG_STANDARD_LIBRARY_SOURCE,
    filename="<PROLOG-Standardbibliothek>",
)


def _with_prolog_standard_library(clauses: Sequence[PrologClause]) -> Tuple[PrologClause, ...]:
    result = list(clauses)
    existing = {_predicate_key(clause.head) for clause in result}

    # Standardpraedikate bestehen haeufig aus mehreren Klauseln. Deshalb wird
    # immer die komplette Klauselgruppe eingefuegt oder gar keine davon.
    # Sonst wuerde z. B. member/2 nur seine Kopf-Klausel erhalten und beim
    # Backtracking niemals den Listentail untersuchen.
    grouped: Dict[Tuple[str, int], List[PrologClause]] = {}
    for clause in _PROLOG_STANDARD_LIBRARY_CLAUSES:
        grouped.setdefault(_predicate_key(clause.head), []).append(clause)

    for key, library_clauses in grouped.items():
        if key in existing:
            continue
        result.extend(library_clauses)
        existing.add(key)
    return tuple(result)


# ---------------------------------------------------------------------------
# Compile-time SLD resolver. This first backend compiles the deterministic
# result transcript into native PE32/PE32+ code. The logic frontend is kept
# separate so a later runtime/backtracking engine can reuse the same parser.
# ---------------------------------------------------------------------------
Env = Dict[str, PrologTerm]


def _predicate_key(term: PrologTerm) -> Tuple[str, int]:
    if term.kind == "atom":
        return str(term.value).casefold(), 0
    if term.kind == "compound":
        return str(term.value).casefold(), len(term.args)
    return "", -1


def _deref(term: PrologTerm, env: Env) -> PrologTerm:
    seen = set()
    current = term
    while current.kind == "var" and str(current.value) in env:
        name = str(current.value)
        if name in seen:
            break
        seen.add(name)
        current = env[name]
    return current


def _subst(term: PrologTerm, env: Env) -> PrologTerm:
    term = _deref(term, env)
    if term.kind == "compound":
        return PrologTerm(term.kind, term.value, tuple(_subst(arg, env) for arg in term.args), term.line, term.column)
    return term


def _unify(left: PrologTerm, right: PrologTerm, env: Env) -> Optional[Env]:
    result = dict(env)
    stack = [(left, right)]
    while stack:
        a, b = stack.pop()
        a = _deref(a, result)
        b = _deref(b, result)
        if a.kind == "var":
            if b.kind == "var" and a.value == b.value:
                continue
            result[str(a.value)] = b
            continue
        if b.kind == "var":
            result[str(b.value)] = a
            continue
        if a.kind != b.kind:
            return None
        if a.kind in {"atom", "number", "float", "string"}:
            if a.value != b.value:
                return None
            continue
        if a.kind == "compound":
            if str(a.value).casefold() != str(b.value).casefold() or len(a.args) != len(b.args):
                return None
            stack.extend(zip(a.args, b.args))
            continue
        return None
    return result


def _term_text(term: PrologTerm, env: Optional[Env] = None) -> str:
    if env is not None:
        term = _subst(term, env)
    if term.kind == "var":
        name = str(term.value)
        return "_" if name.startswith("__anon_") or name.startswith("__fresh_anon_") else name
    if term.kind == "number":
        return str(term.value)
    if term.kind == "float":
        return format(float(term.value), ".15g")
    if term.kind == "string":
        return str(term.value)
    if term.kind == "atom":
        value = str(term.value)
        if re.fullmatch(r"[a-z][A-Za-z0-9_]*", value):
            return value
        return "'" + value.replace("'", "''") + "'"
    if term.kind == "compound":
        return f"{term.value}(" + ", ".join(_term_text(arg, env) for arg in term.args) + ")"
    return str(term.value)


def _write_term_text(term: PrologTerm, env: Optional[Env] = None) -> str:
    if env is not None:
        term = _subst(term, env)
    if term.kind in {"atom", "string", "number"}:
        return str(term.value)
    if term.kind == "float":
        return format(float(term.value), ".15g")
    return _term_text(term, env)


def _eval_arith_term(term: PrologTerm, env: Env) -> Optional[PrologTerm]:
    term = _deref(term, env)
    if term.kind in {"number", "float"}:
        return term
    if term.kind != "compound":
        return None
    op = str(term.value).casefold()

    # Arithmetic function float/1.  This is deliberately handled here,
    # inside the arithmetic evaluator used by is/2 and numeric comparisons.
    # It is distinct from the ordinary predicate float/1 below, which only
    # tests whether an already bound term has the FLOAT type.
    if len(term.args) == 1 and op == "float":
        value = _eval_arith_term(term.args[0], env)
        if value is None:
            return None
        return PrologTerm(
            "float",
            float(value.value),
            line=term.line,
            column=term.column,
        )

    if len(term.args) == 1 and op in {"+", "-"}:
        value = _eval_arith_term(term.args[0], env)
        if value is None:
            return None
        if op == "+":
            return value
        if value.kind == "number":
            return PrologTerm("number", -int(value.value), line=term.line, column=term.column)
        return PrologTerm("float", -float(value.value), line=term.line, column=term.column)
    if len(term.args) != 2 or op not in {"+", "-", "*", "/", "mod"}:
        return None
    left = _eval_arith_term(term.args[0], env)
    right = _eval_arith_term(term.args[1], env)
    if left is None or right is None:
        return None
    if op == "mod":
        if left.kind != "number" or right.kind != "number" or int(right.value) == 0:
            return None
        return PrologTerm("number", int(left.value) % int(right.value), line=term.line, column=term.column)
    if op == "/":
        denominator = float(right.value)
        if denominator == 0.0:
            return None
        return PrologTerm("float", float(left.value) / denominator, line=term.line, column=term.column)
    both_int = left.kind == right.kind == "number"
    if op == "+": value = left.value + right.value
    elif op == "-": value = left.value - right.value
    else: value = left.value * right.value
    return PrologTerm("number" if both_int else "float", int(value) if both_int else float(value), line=term.line, column=term.column)


class _Resolver:
    def __init__(
        self,
        clauses: Sequence[PrologClause],
        *, filename: str,
        max_depth: int = 192,
        max_solutions: int = 512,
    ) -> None:
        self.filename = filename
        self.max_depth = max_depth
        self.max_solutions = max_solutions
        self.by_predicate: Dict[Tuple[str, int], List[PrologClause]] = {}
        for clause in clauses:
            key = _predicate_key(clause.head)
            if key[1] < 0:
                continue
            self.by_predicate.setdefault(key, []).append(clause)
        self._fresh_counter = 0
        self._solution_count = 0

    def _fresh_clause(self, clause: PrologClause) -> PrologClause:
        self._fresh_counter += 1
        suffix = self._fresh_counter
        mapping: Dict[str, str] = {}

        def clone(term: PrologTerm) -> PrologTerm:
            if term.kind == "var":
                original = str(term.value)
                if original.startswith("__anon_"):
                    fresh = f"__fresh_anon_{suffix}_{len(mapping)}"
                else:
                    fresh = mapping.setdefault(original, f"__fresh_{suffix}_{original}")
                return PrologTerm("var", fresh, line=term.line, column=term.column)
            if term.kind == "compound":
                return PrologTerm(term.kind, term.value, tuple(clone(arg) for arg in term.args), term.line, term.column)
            return term

        return PrologClause(clone(clause.head), tuple(clone(goal) for goal in clause.body), clause.line)

    def solve(self, goals: Sequence[PrologTerm]) -> Iterator[Tuple[Env, Tuple[str, ...]]]:
        self._solution_count = 0
        yield from self._solve(tuple(goals), {}, (), 0)

    def _solve(
        self,
        goals: Tuple[PrologTerm, ...],
        env: Env,
        output: Tuple[str, ...],
        depth: int,
    ) -> Iterator[Tuple[Env, Tuple[str, ...]]]:
        if self._solution_count >= self.max_solutions:
            return
        if depth > self.max_depth:
            raise PrologCompilerError(
                f"PROLOG-Auflösung überschreitet die Rekursionstiefe {self.max_depth}.",
                filename=self.filename,
            )
        if not goals:
            self._solution_count += 1
            yield env, output
            return

        goal = _subst(goals[0], env)
        rest = goals[1:]
        key = _predicate_key(goal)
        name, arity = key

        # Builtins ---------------------------------------------------------
        if name == "true" and arity == 0:
            yield from self._solve(rest, env, output, depth)
            return
        if name == "fail" and arity == 0:
            return
        if name == "!" and arity == 0:
            # Cut is accepted in the first compiler stage as a deterministic
            # success point. Full choice-point pruning belongs to the later
            # runtime backtracking engine.
            yield from self._solve(rest, env, output, depth)
            return
        if name == "is" and arity == 2:
            value = _eval_arith_term(goal.args[1], env)
            if value is None:
                return
            new_env = _unify(goal.args[0], value, env)
            if new_env is not None:
                yield from self._solve(rest, new_env, output, depth)
            return
        if name in {"=", "=="} and arity == 2:
            new_env = _unify(goal.args[0], goal.args[1], env)
            if new_env is not None:
                yield from self._solve(rest, new_env, output, depth)
            return
        if name == "\\=" and arity == 2:
            if _unify(goal.args[0], goal.args[1], env) is None:
                yield from self._solve(rest, env, output, depth)
            return
        if name in {"write", "writeln"} and arity == 1:
            rendered = _write_term_text(goal.args[0], env)
            suffix = "\r\n" if name == "writeln" else ""
            yield from self._solve(rest, env, output + (rendered + suffix,), depth)
            return
        if name == "nl" and arity == 0:
            yield from self._solve(rest, env, output + ("\r\n",), depth)
            return
        if name in {"var", "nonvar", "atom", "integer", "float", "number", "string"} and arity == 1:
            value = _deref(goal.args[0], env)
            ok = {
                "var": value.kind == "var",
                "nonvar": value.kind != "var",
                "atom": value.kind == "atom",
                "integer": value.kind == "number",
                "float": value.kind == "float",
                "number": value.kind in {"number", "float"},
                "string": value.kind == "string",
            }[name]
            if ok:
                yield from self._solve(rest, env, output, depth)
            return
        if name in {"<", "=<", ">", ">="} and arity == 2:
            a = _eval_arith_term(goal.args[0], env)
            b = _eval_arith_term(goal.args[1], env)
            if a is None or b is None:
                raise PrologCompilerError(
                    f"{name}/2 erwartet zwei gebundene Zahlen oder arithmetische Ausdrücke.",
                    goal.line, goal.column, self.filename,
                )
            ok = {
                "<": float(a.value) < float(b.value),
                "=<": float(a.value) <= float(b.value),
                ">": float(a.value) > float(b.value),
                ">=": float(a.value) >= float(b.value),
            }[name]
            if ok:
                yield from self._solve(rest, env, output, depth)
            return

        # User predicate ---------------------------------------------------
        clauses = self.by_predicate.get(key, ())
        for clause in clauses:
            fresh = self._fresh_clause(clause)
            new_env = _unify(goal, fresh.head, env)
            if new_env is None:
                continue
            yield from self._solve(tuple(fresh.body) + rest, new_env, output, depth + 1)
            if self._solution_count >= self.max_solutions:
                return


class _AsmBuilder:
    def __init__(self) -> None:
        self.lines: List[str] = []

    def emit(self, text: str = "") -> None:
        self.lines.append(str(text))

    def label(self, name: str) -> None:
        self.lines.append(f"{name}:")

    def render(self) -> str:
        return "\n".join(self.lines).rstrip() + "\n"


def _db_lines(label: str, data: bytes) -> List[str]:
    payload = bytes(data) + b"\0"
    lines = [f"{label}:"]
    for start in range(0, len(payload), 24):
        chunk = payload[start:start + 24]
        lines.append("    db " + ", ".join(str(value) for value in chunk))
    return lines


class PrologCompiler:
    """PROLOG -> Intel ASM frontend for d64_dism PE32/PE32+.

    The parser/resolver implements a useful first PROLOG subset and emits
    ordinary IA-32 or AMD64 assembly. d64_dism remains responsible for COFF
    object creation and final PE linking.
    """

    def __init__(
        self,
        source: str,
        *, filename: str,
        target: str,
        windows_application_mode: str = "Console",
        verbose: bool = False,
    ) -> None:
        self.source = str(source or "")
        self.filename = str(filename or "<PROLOG>")
        self.target = str(target or "pe32").strip().casefold()
        if self.target not in {"pe32", "pe64"}:
            raise PrologCompilerError(
                "Der PROLOG-Compiler unterstützt nur Windows PE32 und PE32+ (PE64).",
                filename=self.filename,
            )
        mode = str(windows_application_mode or "Console").strip().casefold()
        if mode in {"console", "konsole"}:
            self.windows_application_mode = "Console"
        elif mode in {"gui", "windows"}:
            self.windows_application_mode = "GUI"
        else:
            raise PrologCompilerError(
                "PROLOG unterstützt als Windows-Anwendungsmodus derzeit nur Console oder GUI.",
                filename=self.filename,
            )
        self.is64 = self.target == "pe64"
        self.is_gui = self.windows_application_mode == "GUI"
        self.verbose = bool(verbose)
        user_clauses, self.queries = parse_prolog(self.source, filename=self.filename)
        self.user_clauses = tuple(user_clauses)
        self.clauses = _with_prolog_standard_library(self.user_clauses)
        self.resolver = _Resolver(self.clauses, filename=self.filename)
        self.notes: List[str] = []
        self.warnings: List[str] = []

    def _query_variables(self, query: PrologQuery) -> List[Tuple[str, PrologTerm]]:
        found: Dict[str, PrologTerm] = {}

        def walk(term: PrologTerm) -> None:
            if term.kind == "var":
                name = str(term.value)
                if not name.startswith("__anon_"):
                    found.setdefault(name, term)
            elif term.kind == "compound":
                for arg in term.args:
                    walk(arg)

        for goal in query.goals:
            walk(goal)
        return list(found.items())

    def _evaluate_program(self) -> str:
        chunks: List[str] = []
        queries = list(self.queries)
        if not queries and ("main", 0) in self.resolver.by_predicate:
            main_goal = PrologTerm("atom", "main")
            queries.append(PrologQuery((main_goal,), 0))
            self.notes.append("Keine ?-Query vorhanden: main/0 wird als Einstieg verwendet.")
        elif not queries:
            self.notes.append("Keine ?-Query und kein main/0: das erzeugte Programm beendet sich ohne PROLOG-Ausgabe.")
            return ""

        for query_index, query in enumerate(queries, 1):
            variables = self._query_variables(query)
            solutions = list(self.resolver.solve(query.goals))
            if not solutions:
                chunks.append("false.\r\n")
                continue

            for env, effects in solutions:
                chunks.extend(effects)
                if variables:
                    assignments = []
                    for name, term in variables:
                        assignments.append(f"{name} = {_term_text(term, env)}")
                    chunks.append(", ".join(assignments) + ".\r\n")
                elif not effects:
                    chunks.append("true.\r\n")

        return "".join(chunks)

    def _emit_assembly(self, transcript: str) -> str:
        out = _AsmBuilder()
        out.emit("bits 64" if self.is64 else "bits 32")
        out.emit()
        if self.is_gui:
            out.emit('import MessageBoxA, "user32.dll", "MessageBoxA"')
        else:
            out.emit('import AllocConsole, "kernel32.dll", "AllocConsole"')
            out.emit('import GetStdHandle, "kernel32.dll", "GetStdHandle"')
            if transcript:
                out.emit('import WriteFile, "kernel32.dll", "WriteFile"')
        out.emit('import ExitProcess, "kernel32.dll", "ExitProcess"')
        out.emit("global _start")
        out.emit("entry _start")
        out.emit()
        out.emit("section .text")
        out.emit()
        out.label("_start")
        if self.is_gui:
            message = transcript or "PROLOG-Programm erfolgreich ausgeführt."
            out.emit("    push 0")
            out.emit("    push __prolog_caption")
            out.emit("    push __prolog_output")
            out.emit("    push 0")
            out.emit("    call MessageBoxA")
        else:
            out.emit("    call AllocConsole")
            out.emit("    push -11")
            out.emit("    call GetStdHandle")
            out.emit(
                "    mov qword ptr [__prolog_stdout], rax"
                if self.is64 else "    mov dword ptr [__prolog_stdout], eax"
            )
            if transcript:
                payload_len = len(transcript.encode("latin-1", errors="replace"))
                out.emit("    push 0")
                out.emit("    push __prolog_written")
                out.emit(f"    push {payload_len}")
                out.emit("    push __prolog_output")
                out.emit(
                    "    push qword ptr [__prolog_stdout]"
                    if self.is64 else "    push dword ptr [__prolog_stdout]"
                )
                out.emit("    call WriteFile")
        out.emit("    push 0")
        out.emit("    call ExitProcess")
        out.emit()
        out.emit("section .data")
        output_text = transcript if not self.is_gui else (transcript or "PROLOG-Programm erfolgreich ausgeführt.")
        for line in _db_lines("__prolog_output", output_text.encode("latin-1", errors="replace")):
            out.emit(line)
        for line in _db_lines("__prolog_caption", b"d64 PROLOG"):
            out.emit(line)
        if self.is64 and not self.is_gui:
            out.emit()
            out.emit("section .bss")
            out.emit("__prolog_stdout:")
            out.emit("    resq 1")
            out.emit("__prolog_written:")
            out.emit("    resd 1")
        elif not self.is_gui:
            # PE32's existing assembler has no real BSS model yet.
            out.emit("__prolog_stdout:")
            out.emit("    dd 0")
            out.emit("__prolog_written:")
            out.emit("    dd 0")
        return out.render()

    def compile(self) -> PrologCompileResult:
        # Runtime backend: clauses and queries are now executed by the native
        # PROLOG engine in the generated PE image. The previous compile-time
        # resolver remains in this module as a reference/test helper only.
        from .runtime import PrologRuntimeEmitter

        emitter = PrologRuntimeEmitter(
            self.clauses,
            self.queries,
            target=self.target,
            mode=self.windows_application_mode,
            filename=self.filename,
            verbose=self.verbose,
        )
        assembly = emitter.emit()
        predicate_names = sorted(
            f"{name}/{arity}"
            for name, arity in {
                _predicate_key(clause.head) for clause in self.clauses
            }
            if arity >= 0
        )
        self.notes.append(
            "Native PROLOG-Runtime aktiv: Term-Heap, Listen, Trail-Stack, "
            "Choice-Points und Unifikation laufen in der erzeugten EXE."
        )
        self.notes.append(
            "assert/1, asserta/1 und assertz/1 speichern zur Laufzeit Fakten und Regeln; "
            "asserta fuegt vorne, assertz hinten ein, retract/1 entfernt die erste passende Klausel."
        )
        self.notes.append(
            "Runtime-Stufe 2 aktiv: Occurs-Check, striktes ==/2, is/2 mit Arithmetik, "
            "Disjunktion (;), lexikalische Cut-Barrieren und kopierende Dynamic-Heap-GC."
        )
        self.notes.append(
            "Typprädikat string/1: erfolgreich nur für bereits gebundene String-Terme; "
            "ungebundene Variablen, Atome und Zahlen führen zu false und werden nicht gebunden."
        )
        self.notes.append(
            "Verbose-Modus: automatische Top-Level-Loesungsbindungen sind "
            + ("unterdrueckt; write/writeln bleiben sichtbar." if self.verbose else "sichtbar.")
        )
        self.notes.append(
            "PROLOG-Standardbibliothek: member/2 ist automatisch verfuegbar und "
            "arbeitet zur Laufzeit mit normalen Choice-Points und Backtracking."
        )
        if not self.is_gui:
            self.notes.append(
                "Interaktive Queries: repl/0 startet den Console-Top-Level; nach einer Loesung "
                "fordert ';' die naechste Alternative an, ENTER beendet die aktuelle Suche. "
                "Ohne ?-Query und ohne main/0 startet die EXE automatisch im REPL."
            )
        else:
            self.notes.append(
                "GUI-Ausgaben werden zur Laufzeit gesammelt und am Programmende in MessageBoxA angezeigt; "
                "repl/0 ist im GUI-Modus deaktiviert."
            )
        return PrologCompileResult(
            assembly=assembly,
            source_kind="program",
            program_name=Path(self.filename).stem or "prolog_program",
            warnings=tuple(self.warnings),
            notes=tuple(self.notes),
            predicates=tuple(predicate_names),
            query_count=len(self.queries),
            verbose=self.verbose,
        )


def compile_prolog_to_assembly(
    source: str,
    *, filename: str = "<PROLOG>",
    target: str = "pe32",
    windows_application_mode: str = "Console",
    verbose: bool = False,
) -> PrologCompileResult:
    return PrologCompiler(
        source,
        filename=filename,
        target=target,
        windows_application_mode=windows_application_mode,
        verbose=verbose,
    ).compile()
