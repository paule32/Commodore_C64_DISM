from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


class LispCompilerError(Exception):
    def __init__(self, message: str, line: int = 0, column: int = 0, filename: str = "") -> None:
        self.message = str(message)
        self.line = int(line or 0)
        self.column = int(column or 0)
        self.filename = str(filename or "")
        super().__init__(self.__str__())

    def __str__(self) -> str:
        location = ""
        if self.filename:
            location += self.filename
        if self.line:
            location += (":" if location else "Zeile ") + str(self.line)
            if self.column:
                location += f":{self.column}"
        return f"{location}: {self.message}" if location else self.message


@dataclass(frozen=True)
class LispToken:
    kind: str
    text: str
    line: int
    column: int


@dataclass(frozen=True)
class LispNode:
    kind: str
    value: object = None
    children: Tuple["LispNode", ...] = ()
    line: int = 0
    column: int = 0


@dataclass
class LispCompileResult:
    assembly: str
    source_kind: str = "program"
    program_name: str = "lisp_program"
    warnings: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()
    linked_assembly_files: Tuple[str, ...] = ()
    linked_pe32_modules: Tuple[Tuple[str, str], ...] = ()
    functions: Tuple[str, ...] = ()
    globals: Tuple[str, ...] = ()


_SYMBOL_START = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_+-*/<>=!?")
_SYMBOL_CONT = _SYMBOL_START | set("0123456789")


def _tokenize(source: str, filename: str) -> List[LispToken]:
    text = str(source or "")
    result: List[LispToken] = []
    i = 0
    line = 1
    col = 1
    n = len(text)

    def advance_char(ch: str) -> None:
        nonlocal line, col
        if ch == "\n":
            line += 1
            col = 1
        else:
            col += 1

    while i < n:
        ch = text[i]
        if ch in " \t\r\n":
            advance_char(ch)
            i += 1
            continue
        if ch == ";":
            while i < n and text[i] not in "\r\n":
                advance_char(text[i])
                i += 1
            continue
        if ch == "(":
            result.append(LispToken("LPAREN", ch, line, col))
            advance_char(ch); i += 1; continue
        if ch == ")":
            result.append(LispToken("RPAREN", ch, line, col))
            advance_char(ch); i += 1; continue
        if ch == "'":
            result.append(LispToken("QUOTE", ch, line, col))
            advance_char(ch); i += 1; continue
        if ch == '"':
            start_line, start_col, start = line, col, i
            advance_char(ch); i += 1
            escaped = False
            while i < n:
                cur = text[i]
                if escaped:
                    escaped = False
                    advance_char(cur); i += 1
                    continue
                if cur == "\\":
                    escaped = True
                    advance_char(cur); i += 1
                    continue
                if cur == '"':
                    advance_char(cur); i += 1
                    raw = text[start:i]
                    result.append(LispToken("STRING", raw, start_line, start_col))
                    break
                if cur in "\r\n":
                    raise LispCompilerError(
                        "Zeichenkette wurde nicht geschlossen.",
                        start_line, start_col, filename,
                    )
                advance_char(cur); i += 1
            else:
                raise LispCompilerError(
                    "Zeichenkette wurde nicht geschlossen.",
                    start_line, start_col, filename,
                )
            continue

        # NUMBER folgt exakt der Grammar: '-'? [0-9]+. Ein einzelnes '-' ist SYMBOL.
        if ch.isdigit() or (ch == "-" and i + 1 < n and text[i + 1].isdigit()):
            start_line, start_col, start = line, col, i
            if ch == "-":
                advance_char(ch); i += 1
            while i < n and text[i].isdigit():
                advance_char(text[i]); i += 1
            result.append(LispToken("NUMBER", text[start:i], start_line, start_col))
            continue

        if ch in _SYMBOL_START:
            start_line, start_col, start = line, col, i
            while i < n and text[i] in _SYMBOL_CONT:
                advance_char(text[i]); i += 1
            result.append(LispToken("SYMBOL", text[start:i], start_line, start_col))
            continue

        raise LispCompilerError(
            f"Ungültiges LISP-Zeichen {ch!r}.", line, col, filename
        )

    result.append(LispToken("EOF", "", line, col))
    return result


class _Parser:
    def __init__(self, source: str, filename: str) -> None:
        self.filename = filename
        self.tokens = _tokenize(source, filename)
        self.index = 0

    @property
    def current(self) -> LispToken:
        return self.tokens[self.index]

    def take(self, kind: str) -> LispToken:
        token = self.current
        if token.kind != kind:
            raise LispCompilerError(
                f"{kind} erwartet, erhalten: {token.kind} ({token.text!r}).",
                token.line, token.column, self.filename,
            )
        self.index += 1
        return token

    def parse_program(self) -> Tuple[LispNode, ...]:
        forms = []
        while self.current.kind != "EOF":
            forms.append(self.parse_expression())
        return tuple(forms)

    def parse_expression(self) -> LispNode:
        token = self.current
        if token.kind == "LPAREN":
            return self.parse_list()
        if token.kind == "QUOTE":
            self.index += 1
            child = self.parse_expression()
            return LispNode("quote", children=(child,), line=token.line, column=token.column)
        if token.kind == "NUMBER":
            self.index += 1
            return LispNode("number", int(token.text, 10), line=token.line, column=token.column)
        if token.kind == "STRING":
            self.index += 1
            try:
                value = ast.literal_eval(token.text)
            except (SyntaxError, ValueError) as exc:
                raise LispCompilerError(
                    "Ungültige Zeichenkette.", token.line, token.column, self.filename
                ) from exc
            return LispNode("string", str(value), line=token.line, column=token.column)
        if token.kind == "SYMBOL":
            self.index += 1
            return LispNode("symbol", token.text, line=token.line, column=token.column)
        raise LispCompilerError(
            f"Ausdruck erwartet, erhalten: {token.kind}.",
            token.line, token.column, self.filename,
        )

    def parse_list(self) -> LispNode:
        open_token = self.take("LPAREN")
        children = []
        while self.current.kind not in {"RPAREN", "EOF"}:
            children.append(self.parse_expression())
        if self.current.kind == "EOF":
            raise LispCompilerError(
                "Liste wurde nicht mit ')' geschlossen.",
                open_token.line, open_token.column, self.filename,
            )
        self.take("RPAREN")
        return LispNode("list", children=tuple(children), line=open_token.line, column=open_token.column)


def parse_lisp(source: str, *, filename: str = "<LISP>") -> Tuple[LispNode, ...]:
    """Parst genau die mitgelieferte LispLexer/LispParser-Grammatik."""
    return _Parser(source, filename).parse_program()


@dataclass
class _FunctionInfo:
    name: str
    label: str
    parameters: Tuple[str, ...]
    body: Tuple[LispNode, ...]
    node: LispNode
    return_type: Optional[str] = None


class _AsmBuilder:
    def __init__(self) -> None:
        self.lines: List[str] = []

    def emit(self, text: str = "") -> None:
        self.lines.append(text)

    def label(self, name: str) -> None:
        self.lines.append(f"{name}:")

    def extend(self, lines: Iterable[str]) -> None:
        self.lines.extend(lines)

    def render(self) -> str:
        return "\n".join(self.lines).rstrip() + "\n"


class LispCompiler:
    """Kleiner nativer LISP->Intel-ASM-Compiler für d64_dism PE32/PE32+.

    Die Semantik orientiert sich an der mitgelieferten generator.py, verwendet
    aber keinerlei Writer/Emitter daraus. Ausgabe ist ausschließlich Text-ASM,
    den anschließend d64_dism selbst zu COFF32/COFF64 assembliert und linkt.
    """

    def __init__(
        self,
        source: str,
        *,
        filename: str,
        target: str,
        windows_application_mode: str = "Console",
    ) -> None:
        self.source = str(source or "")
        self.filename = str(filename or "<LISP>")
        self.target = str(target or "pe32").strip().casefold()
        if self.target not in {"pe32", "pe64"}:
            raise LispCompilerError(
                "Der LISP-Compiler unterstützt derzeit nur Windows PE32 und PE32+ (PE64).",
                filename=self.filename,
            )
        self.is64 = self.target == "pe64"
        mode = str(windows_application_mode or "Console").strip().casefold()
        if mode in {"console", "konsole"}:
            self.windows_application_mode = "Console"
        elif mode in {"gui", "windows"}:
            self.windows_application_mode = "GUI"
        else:
            raise LispCompilerError(
                "LISP unterstützt als Windows-Anwendungsmodus derzeit nur Console oder GUI.",
                filename=self.filename,
            )
        self.is_gui = self.windows_application_mode == "GUI"
        self.ptr_size = 8 if self.is64 else 4
        self.reg_a = "rax" if self.is64 else "eax"
        self.reg_b = "rcx" if self.is64 else "ecx"
        self.reg_bp = "rbp" if self.is64 else "ebp"
        self.reg_sp = "rsp" if self.is64 else "esp"
        self.forms = parse_lisp(self.source, filename=self.filename)
        stem = Path(self.filename).stem if self.filename not in {"", "<LISP>"} else "lisp"
        safe = re.sub(r"[^A-Za-z0-9_]+", "_", stem).strip("_").casefold() or "lisp"
        digest = hashlib.sha1(self.filename.encode("utf-8", errors="replace")).hexdigest()[:8]
        self.module_id = f"{safe}_{digest}"
        self.functions: Dict[str, _FunctionInfo] = {}
        self.function_order: List[_FunctionInfo] = []
        self.top_level_forms: List[LispNode] = []
        self.entry_function_name: Optional[str] = None
        self.globals: Dict[str, str] = {}
        self.strings: Dict[str, str] = {}
        self.string_values: Dict[str, str] = {}
        self.external_functions: Dict[str, int] = {}
        self.runtime_refs: set[str] = set()
        self.label_counter = 0
        self.current_function: Optional[_FunctionInfo] = None
        self.local_scopes: List[Dict[str, Tuple[str, int]]] = []
        self.break_stack: List[str] = []
        self.continue_stack: List[str] = []
        self.notes: List[str] = []
        self.warnings: List[str] = []
        self._register_program()

    def error(self, node: Optional[LispNode], message: str) -> LispCompilerError:
        return LispCompilerError(
            message,
            getattr(node, "line", 0) if node is not None else 0,
            getattr(node, "column", 0) if node is not None else 0,
            self.filename,
        )

    @staticmethod
    def _symbol(node: LispNode) -> str:
        return str(node.value).casefold() if node.kind == "symbol" else ""

    @staticmethod
    def _asm_symbol(name: str) -> str:
        """Macht beliebige Grammar-SYMBOL-Namen assembler-/COFF-sicher.

        LISP-Namen wie ``foo-bar`` oder ``empty?`` sind laut Grammar gueltig,
        waehrend die internen Intel-Assemblerlabels nur [A-Za-z0-9_.$?@]
        akzeptieren. Die Hexkodierung ist deterministisch und moduluebergreifend.
        """
        out = []
        for ch in str(name).casefold():
            if ch.isalnum() or ch == "_":
                out.append(ch)
            else:
                out.append(f"_x{ord(ch):02x}_")
        return "".join(out) or "anonymous"

    def _list_info(self, node: LispNode) -> Tuple[Optional[str], Tuple[LispNode, ...]]:
        if node.kind != "list" or not node.children:
            return None, ()
        head = node.children[0]
        if head.kind != "symbol":
            return None, tuple(node.children[1:])
        return self._symbol(head), tuple(node.children[1:])

    def _register_program(self) -> None:
        # Pass 1: DEFUN/START registrieren, damit Vorwärtsaufrufe möglich sind.
        for form in self.forms:
            operator, args = self._list_info(form)
            if operator == "defun":
                self._register_defun(form, args)
            elif operator == "start":
                self._register_start(form, args)
            else:
                self.top_level_forms.append(form)

        # Top-Level-SETQ vorab deklarieren, wie in der Referenzimplementierung.
        for form in self.top_level_forms:
            operator, args = self._list_info(form)
            if operator == "setq":
                if len(args) < 2 or len(args) % 2:
                    raise self.error(form, "SETQ erwartet Symbol/Wert-Paare.")
                for index in range(0, len(args), 2):
                    name_node, value_node = args[index], args[index + 1]
                    if name_node.kind != "symbol":
                        raise self.error(name_node, "SETQ erwartet links einen Symbolnamen.")
                    name = self._symbol(name_node)
                    if name not in self.globals:
                        inferred = self._infer_type(value_node)
                        self.globals[name] = "integer" if inferred == "nil" else inferred

        if self.entry_function_name is not None and self.entry_function_name not in self.functions:
            raise self.error(None, f"LISP-Startfunktion nicht gefunden: {self.entry_function_name}")

    def _register_start(self, node: LispNode, args: Sequence[LispNode]) -> None:
        if len(args) != 1 or args[0].kind != "symbol":
            raise self.error(node, "START erwartet genau einen Funktionsnamen.")
        if self.entry_function_name is not None:
            raise self.error(node, "START darf nur einmal angegeben werden.")
        self.entry_function_name = self._symbol(args[0])

    def _register_defun(self, node: LispNode, args: Sequence[LispNode]) -> None:
        if len(args) < 3:
            raise self.error(node, "DEFUN erwartet Name, Parameterliste und mindestens einen Rumpfausdruck.")
        if args[0].kind != "symbol":
            raise self.error(args[0], "DEFUN erwartet einen Funktionsnamen.")
        name = self._symbol(args[0])
        params_node = args[1]
        if params_node.kind != "list":
            raise self.error(params_node, "DEFUN erwartet eine Parameterliste in Klammern.")
        params: List[str] = []
        for param in params_node.children:
            if param.kind != "symbol":
                raise self.error(param, "Funktionsparameter muss ein Symbol sein.")
            p = self._symbol(param)
            if p in params:
                raise self.error(param, f"Parameter mehrfach definiert: {p}")
            params.append(p)
        if name in self.functions:
            raise self.error(node, f"Funktion mehrfach definiert: {name}")
        info = _FunctionInfo(name, f"lisp_func_{self._asm_symbol(name)}", tuple(params), tuple(args[2:]), node)
        self.functions[name] = info
        self.function_order.append(info)

    @property
    def is_main_program(self) -> bool:
        if self.entry_function_name is not None:
            return True
        if "main" in self.functions and not self.functions["main"].parameters:
            return True
        return bool(self.top_level_forms)

    def _new_label(self, prefix: str) -> str:
        self.label_counter += 1
        safe = re.sub(r"[^A-Za-z0-9_]+", "_", prefix)
        return f"__lisp_{self.module_id}_{safe}_{self.label_counter}"

    def _string_label(self, value: str) -> str:
        if value in self.strings:
            return self.strings[value]
        label = f"__lisp_{self.module_id}_str_{len(self.strings) + 1}"
        self.strings[value] = label
        self.string_values[label] = value
        return label

    def _global_label(self, name: str) -> str:
        # Globale LISP-Variablen sind absichtlich modulübergreifend sichtbar.
        return f"lisp_var_{self._asm_symbol(name)}"

    def _infer_type(self, node: LispNode) -> str:
        if node.kind == "number":
            return "integer"
        if node.kind == "string":
            return "string"
        if node.kind == "symbol":
            name = self._symbol(node)
            if name in {"true", "false", "t"}:
                return "boolean"
            if name == "nil":
                return "nil"
            if name in self.globals:
                return self.globals[name]
            for scope in reversed(self.local_scopes):
                if name in scope:
                    return scope[name][0]
            return "integer"
        if node.kind == "quote":
            child = node.children[0]
            if child.kind == "string":
                return "string"
            if child.kind == "number":
                return "integer"
            if child.kind == "symbol" and self._symbol(child) == "nil":
                return "nil"
            return "string"
        if node.kind == "list":
            op, args = self._list_info(node)
            if op in {"+", "-", "*", "/"}:
                return "integer"
            if op in {"=", "==", "/=", "!=", "<>", "<", "<=", ">", ">="}:
                return "boolean"
            if op == "if" and len(args) >= 2:
                return self._infer_type(args[1])
            if op == "setq" and len(args) >= 2:
                return self._infer_type(args[-1])
            if op == "read":
                return "string"
            if op in {"print", "println", "while", "break", "continue", "defun", "start"}:
                return "nil"
            if op in self.functions:
                return self.functions[op].return_type or "integer"
        return "integer"

    def _find_variable(self, name: str) -> Optional[Tuple[str, str, int]]:
        for scope in reversed(self.local_scopes):
            if name in scope:
                typ, offset = scope[name]
                return typ, "parameter", offset
        if name in self.globals:
            return self.globals[name], "global", 0
        return None

    def _emit_load_variable(self, out: _AsmBuilder, node: LispNode, name: str) -> str:
        found = self._find_variable(name)
        if found is None:
            raise self.error(node, f"Unbekanntes Symbol: {name}")
        typ, kind, offset = found
        if kind == "parameter":
            if typ == "string":
                out.emit(f"    mov {self.reg_a}, qword ptr [{self.reg_bp}+{offset}]" if self.is64 else f"    mov eax, dword ptr [ebp+{offset}]")
            else:
                out.emit(f"    mov eax, dword ptr [{self.reg_bp}+{offset}]")
        else:
            label = self._global_label(name)
            if typ == "string":
                out.emit(f"    mov {self.reg_a}, qword ptr [{label}]" if self.is64 else f"    mov eax, dword ptr [{label}]")
            else:
                out.emit(f"    mov eax, dword ptr [{label}]")
        return typ

    def _emit_store_variable(self, out: _AsmBuilder, node: LispNode, name: str, value_type: str) -> str:
        found = self._find_variable(name)
        if found is None:
            # NIL besitzt noch keinen eigenen Heap-/Objekttyp. Fuer Variablenslots
            # wird es wie der Nullwert eines Integers gespeichert, damit spaetere
            # SETQ-Zuweisungen eines Integers denselben Slot weiterverwenden koennen.
            storage_type = "integer" if value_type == "nil" else value_type
            self.globals[name] = storage_type
            found = (storage_type, "global", 0)
        expected, kind, offset = found
        compatible = expected == value_type or (expected == "integer" and value_type == "nil")
        if not compatible:
            raise self.error(node, f"SETQ-Typfehler für {name}: {value_type}, erwartet {expected}.")
        if kind == "parameter":
            if expected == "string":
                out.emit(f"    mov qword ptr [{self.reg_bp}+{offset}], {self.reg_a}" if self.is64 else f"    mov dword ptr [ebp+{offset}], eax")
            else:
                out.emit(f"    mov dword ptr [{self.reg_bp}+{offset}], eax")
        else:
            label = self._global_label(name)
            if expected == "string":
                out.emit(f"    mov qword ptr [{label}], {self.reg_a}" if self.is64 else f"    mov dword ptr [{label}], eax")
            else:
                out.emit(f"    mov dword ptr [{label}], eax")
        return expected

    def _push_result(self, out: _AsmBuilder) -> None:
        out.emit(f"    push {self.reg_a}")

    def _pop_temp(self, out: _AsmBuilder) -> None:
        out.emit(f"    pop {self.reg_b}")

    def _cleanup_args(self, out: _AsmBuilder, count: int) -> None:
        if count:
            out.emit(f"    add {self.reg_sp}, {count * self.ptr_size}")

    def _emit_expr(self, out: _AsmBuilder, node: LispNode) -> str:
        if node.kind == "number":
            out.emit(f"    mov eax, {int(node.value)}")
            return "integer"
        if node.kind == "string":
            label = self._string_label(str(node.value))
            out.emit(f"    mov {self.reg_a}, {label}")
            return "string"
        if node.kind == "quote":
            child = node.children[0]
            if child.kind == "number":
                out.emit(f"    mov eax, {int(child.value)}")
                return "integer"
            if child.kind == "string":
                label = self._string_label(str(child.value))
                out.emit(f"    mov {self.reg_a}, {label}")
                return "string"
            if child.kind == "symbol":
                symbol = self._symbol(child)
                if symbol == "nil":
                    out.emit("    xor eax, eax")
                    return "nil"
                # Noch keine echten Symbolobjekte: Quote-Symbol als lesbarer Text.
                label = self._string_label(symbol)
                out.emit(f"    mov {self.reg_a}, {label}")
                return "string"
            raise self.error(node, "Quoted Listen sind in dieser ersten nativen LISP-Stufe noch nicht materialisiert.")
        if node.kind == "symbol":
            name = self._symbol(node)
            if name == "nil":
                out.emit("    xor eax, eax")
                return "nil"
            if name == "false":
                out.emit("    xor eax, eax")
                return "boolean"
            if name in {"t", "true"}:
                out.emit("    mov eax, 1")
                return "boolean"
            return self._emit_load_variable(out, node, name)
        if node.kind != "list":
            raise self.error(node, "Unbekannter LISP-Ausdruck.")
        if not node.children:
            out.emit("    xor eax, eax")
            return "nil"
        op, args = self._list_info(node)
        if op is None:
            raise self.error(node, "Das erste Listenelement muss ein Operator-Symbol sein.")
        handlers = {
            "+": self._emit_add, "-": self._emit_sub, "*": self._emit_mul, "/": self._emit_div,
            "=": lambda o,n,a: self._emit_compare(o,n,a,"e"),
            "==": lambda o,n,a: self._emit_compare(o,n,a,"e"),
            "/=": lambda o,n,a: self._emit_compare(o,n,a,"ne"),
            "!=": lambda o,n,a: self._emit_compare(o,n,a,"ne"),
            "<>": lambda o,n,a: self._emit_compare(o,n,a,"ne"),
            "<": lambda o,n,a: self._emit_compare(o,n,a,"l"),
            "<=": lambda o,n,a: self._emit_compare(o,n,a,"le"),
            ">": lambda o,n,a: self._emit_compare(o,n,a,"g"),
            ">=": lambda o,n,a: self._emit_compare(o,n,a,"ge"),
            "setq": self._emit_setq,
            "if": self._emit_if,
            "while": self._emit_while,
            "break": self._emit_break,
            "continue": self._emit_continue,
            "print": lambda o,n,a: self._emit_print(o,n,a,False),
            "println": lambda o,n,a: self._emit_print(o,n,a,True),
            "read": self._emit_read,
        }
        handler = handlers.get(op)
        if handler is not None:
            return handler(out, node, args)
        if op in {"defun", "start"}:
            out.emit("    xor eax, eax")
            return "nil"
        return self._emit_call(out, node, op, args)

    def _require_int(self, node: LispNode, typ: str) -> None:
        if typ not in {"integer", "boolean", "nil"}:
            raise self.error(node, f"Integer-Ausdruck erwartet, erhalten: {typ}.")

    def _emit_add(self, out: _AsmBuilder, node: LispNode, args: Sequence[LispNode]) -> str:
        if len(args) < 2:
            raise self.error(node, "+ erwartet mindestens zwei Argumente.")
        typ = self._emit_expr(out, args[0]); self._require_int(args[0], typ)
        for arg in args[1:]:
            self._push_result(out)
            typ2 = self._emit_expr(out, arg); self._require_int(arg, typ2)
            self._pop_temp(out)
            out.emit("    add eax, ecx")
        return "integer"

    def _emit_sub(self, out: _AsmBuilder, node: LispNode, args: Sequence[LispNode]) -> str:
        if not args:
            raise self.error(node, "- erwartet mindestens ein Argument.")
        typ = self._emit_expr(out, args[0]); self._require_int(args[0], typ)
        if len(args) == 1:
            out.emit("    neg eax")
            return "integer"
        for arg in args[1:]:
            self._push_result(out)
            typ2 = self._emit_expr(out, arg); self._require_int(arg, typ2)
            self._pop_temp(out)
            out.emit("    sub ecx, eax")
            out.emit("    mov eax, ecx")
        return "integer"

    def _emit_mul(self, out: _AsmBuilder, node: LispNode, args: Sequence[LispNode]) -> str:
        if not args:
            out.emit("    mov eax, 1")
            return "integer"
        typ = self._emit_expr(out, args[0]); self._require_int(args[0], typ)
        for arg in args[1:]:
            self._push_result(out)
            typ2 = self._emit_expr(out, arg); self._require_int(arg, typ2)
            self._pop_temp(out)
            out.emit("    imul eax, ecx")
        return "integer"

    def _emit_div(self, out: _AsmBuilder, node: LispNode, args: Sequence[LispNode]) -> str:
        if len(args) < 2:
            raise self.error(node, "/ erwartet mindestens zwei Argumente.")
        typ = self._emit_expr(out, args[0]); self._require_int(args[0], typ)
        for arg in args[1:]:
            self._push_result(out)
            typ2 = self._emit_expr(out, arg); self._require_int(arg, typ2)
            out.emit("    mov ecx, eax")
            ok = self._new_label("div_ok")
            out.emit("    cmp ecx, 0")
            out.emit(f"    jne {ok}")
            self.runtime_refs.add("__lisp_div_zero")
            out.emit("    call __lisp_div_zero")
            out.label(ok)
            out.emit(f"    pop {self.reg_a}")
            out.emit("    cdq")
            out.emit("    idiv ecx")
        return "integer"

    def _emit_compare(self, out: _AsmBuilder, node: LispNode, args: Sequence[LispNode], condition: str) -> str:
        if len(args) != 2:
            raise self.error(node, "Vergleich erwartet genau zwei Argumente.")
        left = self._emit_expr(out, args[0]); self._require_int(args[0], left)
        self._push_result(out)
        right = self._emit_expr(out, args[1]); self._require_int(args[1], right)
        self._pop_temp(out)
        out.emit("    cmp ecx, eax")
        out.emit(f"    set{condition} al")
        out.emit("    and eax, 1")
        return "boolean"

    def _emit_setq(self, out: _AsmBuilder, node: LispNode, args: Sequence[LispNode]) -> str:
        if len(args) < 2 or len(args) % 2:
            raise self.error(node, "SETQ erwartet Symbol/Wert-Paare.")
        result = "nil"
        for index in range(0, len(args), 2):
            name_node, value_node = args[index], args[index + 1]
            if name_node.kind != "symbol":
                raise self.error(name_node, "SETQ erwartet links einen Symbolnamen.")
            result = self._emit_expr(out, value_node)
            self._emit_store_variable(out, name_node, self._symbol(name_node), result)
        return result

    def _emit_if(self, out: _AsmBuilder, node: LispNode, args: Sequence[LispNode]) -> str:
        if len(args) not in {2, 3}:
            raise self.error(node, "IF erwartet Bedingung, THEN-Ausdruck und optional ELSE-Ausdruck.")
        else_label = self._new_label("if_else")
        end_label = self._new_label("if_end")
        cond_type = self._emit_expr(out, args[0]); self._require_int(args[0], cond_type)
        out.emit("    cmp eax, 0")
        out.emit(f"    je {else_label}")
        then_type = self._emit_expr(out, args[1])
        out.emit(f"    jmp {end_label}")
        out.label(else_label)
        if len(args) == 3:
            else_type = self._emit_expr(out, args[2])
        else:
            out.emit("    xor eax, eax")
            else_type = "nil"
        out.label(end_label)
        if then_type == else_type:
            return then_type
        if then_type == "nil":
            return else_type
        if else_type == "nil":
            return then_type
        raise self.error(node, f"IF-Zweige besitzen unterschiedliche Typen: {then_type} / {else_type}.")

    def _emit_while(self, out: _AsmBuilder, node: LispNode, args: Sequence[LispNode]) -> str:
        if not args:
            raise self.error(node, "WHILE erwartet eine Bedingung.")
        condition = self._new_label("while_condition")
        end = self._new_label("while_end")
        self.break_stack.append(end); self.continue_stack.append(condition)
        try:
            out.label(condition)
            typ = self._emit_expr(out, args[0]); self._require_int(args[0], typ)
            out.emit("    cmp eax, 0")
            out.emit(f"    je {end}")
            for expression in args[1:]:
                self._emit_expr(out, expression)
            out.emit(f"    jmp {condition}")
            out.label(end)
        finally:
            self.continue_stack.pop(); self.break_stack.pop()
        out.emit("    xor eax, eax")
        return "nil"

    def _emit_break(self, out: _AsmBuilder, node: LispNode, args: Sequence[LispNode]) -> str:
        if args:
            raise self.error(node, "BREAK erwartet keine Argumente.")
        if not self.break_stack:
            raise self.error(node, "BREAK außerhalb einer WHILE-Schleife.")
        out.emit(f"    jmp {self.break_stack[-1]}")
        return "nil"

    def _emit_continue(self, out: _AsmBuilder, node: LispNode, args: Sequence[LispNode]) -> str:
        if args:
            raise self.error(node, "CONTINUE erwartet keine Argumente.")
        if not self.continue_stack:
            raise self.error(node, "CONTINUE außerhalb einer WHILE-Schleife.")
        out.emit(f"    jmp {self.continue_stack[-1]}")
        return "nil"

    def _emit_read(self, out: _AsmBuilder, node: LispNode, args: Sequence[LispNode]) -> str:
        """Liest eine komplette Konsolenzeile und liefert char* auf den Text.

        Der Runtime-Puffer wird einmalig mit VirtualAlloc reserviert. READ ist
        absichtlich eine Console-Funktion; GUI-Projekte besitzen keine
        Standardeingabekonsole.
        """
        if args:
            raise self.error(node, "READ erwartet keine Argumente.")
        if self.is_gui:
            raise self.error(
                node,
                "READ ist nur im Windows-Console-Modus verfügbar; GUI besitzt keine Konsoleneingabe.",
            )
        self.runtime_refs.add("__lisp_read_text")
        out.emit("    call __lisp_read_text")
        return "string"

    def _emit_print(self, out: _AsmBuilder, node: LispNode, args: Sequence[LispNode], newline: bool) -> str:
        for arg in args:
            typ = self._emit_expr(out, arg)
            if typ == "integer": helper = "__lisp_print_int"
            elif typ == "boolean": helper = "__lisp_print_bool"
            elif typ == "string": helper = "__lisp_print_text"
            elif typ == "nil": helper = "__lisp_print_nil"
            else: raise self.error(arg, f"Nicht druckbarer Typ: {typ}")
            self.runtime_refs.add(helper)
            out.emit(f"    push {self.reg_a}")
            out.emit(f"    call {helper}")
            self._cleanup_args(out, 1)
        if newline:
            self.runtime_refs.add("__lisp_print_newline")
            out.emit("    call __lisp_print_newline")
        out.emit("    xor eax, eax")
        return "nil"

    def _emit_call(self, out: _AsmBuilder, node: LispNode, name: str, args: Sequence[LispNode]) -> str:
        info = self.functions.get(name)
        if info is not None and len(args) != len(info.parameters):
            raise self.error(node, f"{name} erwartet {len(info.parameters)} Argument(e), erhalten: {len(args)}.")
        # Compilerinterne Funktionen erwarten Integerparameter wie die Referenz.
        for index in range(len(args) - 1, -1, -1):
            typ = self._emit_expr(out, args[index])
            if info is not None and typ not in {"integer", "boolean", "nil"}:
                raise self.error(args[index], f"Parameter {index + 1} von {name} erwartet Integer.")
            self._push_result(out)
        label = info.label if info is not None else f"lisp_func_{self._asm_symbol(name)}"
        if info is None:
            self.external_functions[label] = len(args)
        out.emit(f"    call {label}")
        self._cleanup_args(out, len(args))
        return (info.return_type or "integer") if info is not None else "integer"

    def _emit_function(self, out: _AsmBuilder, info: _FunctionInfo) -> None:
        out.label(info.label)
        out.emit(f"    push {self.reg_bp}")
        out.emit(f"    mov {self.reg_bp}, {self.reg_sp}")
        old = self.current_function
        self.current_function = info
        base = 16 if self.is64 else 8
        stride = 8 if self.is64 else 4
        scope = {name: ("integer", base + index * stride) for index, name in enumerate(info.parameters)}
        self.local_scopes.append(scope)
        try:
            result_type = "nil"
            for expression in info.body:
                result_type = self._emit_expr(out, expression)
            info.return_type = result_type
        finally:
            self.local_scopes.pop()
            self.current_function = old
        out.emit(f"    mov {self.reg_sp}, {self.reg_bp}")
        out.emit(f"    pop {self.reg_bp}")
        out.emit("    ret")
        out.emit()

    def _emit_main(self, out: _AsmBuilder) -> None:
        out.label("_main")
        out.emit(f"    push {self.reg_bp}")
        out.emit(f"    mov {self.reg_bp}, {self.reg_sp}")
        result_type = "nil"
        for expression in self.top_level_forms:
            result_type = self._emit_expr(out, expression)
        entry = self.entry_function_name
        if entry is None and "main" in self.functions:
            entry = "main"
        if entry is not None:
            info = self.functions[entry]
            if info.parameters:
                raise self.error(info.node, f"LISP-Startfunktion '{entry}' darf keine Parameter besitzen.")
            out.emit(f"    call {info.label}")
            result_type = info.return_type or "integer"
        elif not self.top_level_forms:
            out.emit("    xor eax, eax")
        out.emit(f"    mov {self.reg_sp}, {self.reg_bp}")
        out.emit(f"    pop {self.reg_bp}")
        out.emit("    ret")
        out.emit()

    def _emit_start_and_runtime(self, out: _AsmBuilder) -> None:
        # Die Runtime folgt bewusst der compilerinternen Stack-ABI. Unter PE64
        # erzeugt d64_dism für WinAPI-Imports automatisch Microsoft-x64-Adapter.
        out.label("_start")
        if not self.is_gui:
            out.emit("    call AllocConsole")
            out.emit("    push -11")
            out.emit("    call GetStdHandle")
            out.emit(
                "    mov qword ptr [__lisp_stdout], rax"
                if self.is64 else "    mov dword ptr [__lisp_stdout], eax"
            )
            out.emit("    push -10")
            out.emit("    call GetStdHandle")
            out.emit(
                "    mov qword ptr [__lisp_stdin], rax"
                if self.is64 else "    mov dword ptr [__lisp_stdin], eax"
            )
        out.emit("    call _main")
        out.emit("    push 0")
        out.emit("    call ExitProcess")
        out.emit()

        # READ: wartet mit ReadFile bis Konsolentext/ENTER verfügbar ist.
        # Der 4-KiB-Puffer wird lazy per VirtualAlloc angelegt und wiederverwendet.
        if not self.is_gui:
            out.label("__lisp_read_text")
            out.emit(f"    push {self.reg_bp}")
            out.emit(f"    mov {self.reg_bp}, {self.reg_sp}")
            out.emit(
                "    mov rax, qword ptr [__lisp_input_buffer]"
                if self.is64 else "    mov eax, dword ptr [__lisp_input_buffer]"
            )
            out.emit("    test rax, rax" if self.is64 else "    test eax, eax")
            buffer_ready = "__lisp_read_buffer_ready"
            alloc_ok = "__lisp_read_alloc_ok"
            trim_loop = "__lisp_read_trim_loop"
            trim_one = "__lisp_read_trim_one"
            terminate = "__lisp_read_terminate"
            finish = "__lisp_read_finish"
            out.emit(f"    jne {buffer_ready}")
            out.emit("    push 4")          # PAGE_READWRITE
            out.emit("    push 12288")      # MEM_COMMIT | MEM_RESERVE
            out.emit("    push 4096")
            out.emit("    push 0")
            out.emit("    call VirtualAlloc")
            out.emit("    test rax, rax" if self.is64 else "    test eax, eax")
            out.emit(f"    jne {alloc_ok}")
            out.emit(f"    mov {self.reg_a}, __lisp_empty_text")
            out.emit(f"    jmp {finish}")
            out.label(alloc_ok)
            out.emit(
                "    mov qword ptr [__lisp_input_buffer], rax"
                if self.is64 else "    mov dword ptr [__lisp_input_buffer], eax"
            )
            out.label(buffer_ready)
            out.emit("    mov dword ptr [__lisp_read_count], 0")
            out.emit("    push 0")
            out.emit("    push __lisp_read_count")
            out.emit("    push 4095")
            out.emit(
                "    push qword ptr [__lisp_input_buffer]"
                if self.is64 else "    push dword ptr [__lisp_input_buffer]"
            )
            out.emit(
                "    push qword ptr [__lisp_stdin]"
                if self.is64 else "    push dword ptr [__lisp_stdin]"
            )
            out.emit("    call ReadFile")
            out.emit("    mov edx, dword ptr [__lisp_read_count]")
            out.emit(
                "    mov rcx, qword ptr [__lisp_input_buffer]"
                if self.is64 else "    mov ecx, dword ptr [__lisp_input_buffer]"
            )
            out.label(trim_loop)
            out.emit("    cmp edx, 0")
            out.emit(f"    je {terminate}")
            out.emit(
                "    movzx eax, byte ptr [rcx+rdx-1]"
                if self.is64 else "    movzx eax, byte ptr [ecx+edx-1]"
            )
            out.emit("    cmp eax, 10")
            out.emit(f"    je {trim_one}")
            out.emit("    cmp eax, 13")
            out.emit(f"    jne {terminate}")
            out.label(trim_one)
            out.emit("    dec edx")
            out.emit(f"    jmp {trim_loop}")
            out.label(terminate)
            # Der PE32-Assembler kodiert Byte-Immediate-Speicherziele noch nicht
            # separat. AL=0 vermeidet dort ein versehentliches DWORD-Store.
            out.emit("    xor eax, eax")
            out.emit(
                "    mov byte ptr [rcx+rdx], al"
                if self.is64 else "    mov byte ptr [ecx+edx], al"
            )
            out.emit("    mov rax, rcx" if self.is64 else "    mov eax, ecx")
            out.label(finish)
            out.emit(f"    mov {self.reg_sp}, {self.reg_bp}")
            out.emit(f"    pop {self.reg_bp}")
            out.emit("    ret")
            out.emit()

        # Textausgabe: Argument = char* auf dem compilerinternen Stack.
        out.label("__lisp_print_text")
        out.emit(f"    push {self.reg_bp}")
        out.emit(f"    mov {self.reg_bp}, {self.reg_sp}")
        out.emit("    push rsi" if self.is64 else "    push esi")
        arg_off = 16 if self.is64 else 8
        out.emit(
            f"    mov rsi, qword ptr [rbp+{arg_off}]"
            if self.is64 else f"    mov esi, dword ptr [ebp+{arg_off}]"
        )

        if self.is_gui:
            # GUI-Programme besitzen absichtlich keine Konsole. PRINT/PRINTLN
            # zeigen den Wert daher über MessageBoxA an.
            out.emit("    push 0")
            out.emit("    push __lisp_gui_caption")
            out.emit("    push rsi" if self.is64 else "    push esi")
            out.emit("    push 0")
            out.emit("    call MessageBoxA")
        else:
            out.emit("    mov rcx, rsi" if self.is64 else "    mov ecx, esi")
            out.emit("    xor edx, edx")
            len_loop = "__lisp_runtime_strlen_loop"
            len_done = "__lisp_runtime_strlen_done"
            out.label(len_loop)
            out.emit("    movzx eax, byte ptr [rcx]" if self.is64 else "    movzx eax, byte ptr [ecx]")
            out.emit("    test eax, eax")
            out.emit(f"    je {len_done}")
            out.emit("    inc rcx" if self.is64 else "    inc ecx")
            out.emit("    inc edx")
            out.emit(f"    jmp {len_loop}")
            out.label(len_done)
            out.emit("    push 0")
            out.emit("    push __lisp_written")
            out.emit("    push rdx" if self.is64 else "    push edx")
            out.emit("    push rsi" if self.is64 else "    push esi")
            out.emit(
                "    push qword ptr [__lisp_stdout]"
                if self.is64 else "    push dword ptr [__lisp_stdout]"
            )
            out.emit("    call WriteFile")

        out.emit("    pop rsi" if self.is64 else "    pop esi")
        out.emit(f"    mov {self.reg_sp}, {self.reg_bp}")
        out.emit(f"    pop {self.reg_bp}")
        out.emit("    ret")
        out.emit()

        out.label("__lisp_print_int")
        out.emit(f"    push {self.reg_bp}")
        out.emit(f"    mov {self.reg_bp}, {self.reg_sp}")
        out.emit(f"    mov eax, dword ptr [{self.reg_bp}+{arg_off}]")
        out.emit("    push rax" if self.is64 else "    push eax")
        out.emit("    push __lisp_fmt_int")
        out.emit("    push __lisp_format_buffer")
        out.emit("    call wsprintfA")
        # wsprintfA ist cdecl; beim PE64-Adapter wird absichtlich nicht per RET n bereinigt.
        out.emit(f"    add {self.reg_sp}, {3 * self.ptr_size}")
        out.emit("    push __lisp_format_buffer")
        out.emit("    call __lisp_print_text")
        self._cleanup_args(out, 1)
        out.emit(f"    mov {self.reg_sp}, {self.reg_bp}")
        out.emit(f"    pop {self.reg_bp}")
        out.emit("    ret")
        out.emit()

        out.label("__lisp_print_bool")
        out.emit(f"    push {self.reg_bp}")
        out.emit(f"    mov {self.reg_bp}, {self.reg_sp}")
        out.emit(f"    mov eax, dword ptr [{self.reg_bp}+{arg_off}]")
        false_label = "__lisp_runtime_bool_false"
        done_label = "__lisp_runtime_bool_done"
        out.emit("    test eax, eax")
        out.emit(f"    je {false_label}")
        out.emit(f"    mov {self.reg_a}, __lisp_true_text")
        out.emit(f"    jmp {done_label}")
        out.label(false_label)
        out.emit(f"    mov {self.reg_a}, __lisp_false_text")
        out.label(done_label)
        out.emit(f"    push {self.reg_a}")
        out.emit("    call __lisp_print_text")
        self._cleanup_args(out, 1)
        out.emit(f"    mov {self.reg_sp}, {self.reg_bp}")
        out.emit(f"    pop {self.reg_bp}")
        out.emit("    ret")
        out.emit()

        out.label("__lisp_print_nil")
        out.emit(f"    mov {self.reg_a}, __lisp_nil_text")
        out.emit(f"    push {self.reg_a}")
        out.emit("    call __lisp_print_text")
        self._cleanup_args(out, 1)
        out.emit("    ret")
        out.emit()

        out.label("__lisp_print_newline")
        if self.is_gui:
            # MessageBoxA trennt Ausgaben bereits visuell; kein zweiter Dialog
            # nur für CR/LF.
            out.emit("    ret")
        else:
            out.emit(f"    mov {self.reg_a}, __lisp_newline")
            out.emit(f"    push {self.reg_a}")
            out.emit("    call __lisp_print_text")
            self._cleanup_args(out, 1)
            out.emit("    ret")
        out.emit()

        out.label("__lisp_div_zero")
        out.emit(f"    mov {self.reg_a}, __lisp_div_zero_text")
        out.emit(f"    push {self.reg_a}")
        out.emit("    call __lisp_print_text")
        self._cleanup_args(out, 1)
        if not self.is_gui:
            out.emit("    call __lisp_print_newline")
        out.emit("    push 1")
        out.emit("    call ExitProcess")
        out.emit("    ret")
        out.emit()

    @staticmethod
    def _db_line(label: str, value: str) -> str:
        raw = value.encode("utf-8") + b"\0"
        return f"{label}:\n    db " + ", ".join(str(b) for b in raw)

    def compile(self) -> LispCompileResult:
        code = _AsmBuilder()
        # Funktionen zuerst erzeugen, damit ihre Rueckgabetypen vor _main bekannt sind.
        for info in self.function_order:
            self._emit_function(code, info)
        if self.is_main_program:
            self._emit_main(code)

        # Erst nach der Codeerzeugung kennen wir alle externen Funktionsaufrufe.
        header = _AsmBuilder()
        header.emit("bits 64" if self.is64 else "bits 32")
        header.emit()
        if self.is_main_program:
            if self.is_gui:
                header.emit('import MessageBoxA, "user32.dll", "MessageBoxA"')
            else:
                header.emit('import AllocConsole, "kernel32.dll", "AllocConsole"')
                header.emit('import GetStdHandle, "kernel32.dll", "GetStdHandle"')
                header.emit('import WriteFile, "kernel32.dll", "WriteFile"')
                header.emit('import ReadFile, "kernel32.dll", "ReadFile"')
                header.emit('import VirtualAlloc, "kernel32.dll", "VirtualAlloc"')
            header.emit('import ExitProcess, "kernel32.dll", "ExitProcess"')
            header.emit('import wsprintfA, "user32.dll", "wsprintfA"')
            header.emit("global _start")
            header.emit("global _main")
        for info in self.function_order:
            header.emit(f"global {info.label}")
        for external in sorted(self.external_functions):
            if external not in {info.label for info in self.function_order}:
                header.emit(f"extern {external}")
        if not self.is_main_program:
            for runtime in sorted(self.runtime_refs):
                header.emit(f"extern {runtime}")
        header.emit("entry _start" if self.is_main_program else "entry _start")
        header.emit()
        header.emit("section .text")
        header.emit()

        final = _AsmBuilder()
        final.extend(header.lines)
        if self.is_main_program:
            self._emit_start_and_runtime(final)
        final.extend(code.lines)

        # Initialisierte Konstantdaten/Strings.
        final.emit("section .data")
        final.emit()
        if self.is_main_program:
            final.emit(self._db_line("__lisp_fmt_int", "%d"))
            final.emit(self._db_line("__lisp_true_text", "TRUE"))
            final.emit(self._db_line("__lisp_false_text", "FALSE"))
            final.emit(self._db_line("__lisp_nil_text", "NIL"))
            if not self.is_gui:
                final.emit(self._db_line("__lisp_empty_text", ""))
            if self.is_gui:
                final.emit(self._db_line("__lisp_gui_caption", "LISP"))
            else:
                final.emit("__lisp_newline:\n    db 13, 10, 0")
            final.emit(self._db_line("__lisp_div_zero_text", "LISP runtime error: division by zero"))
        for label, value in self.string_values.items():
            final.emit(self._db_line(label, value))

        if self.is64:
            final.emit()
            final.emit("section .bss")
            if self.is_main_program:
                if not self.is_gui:
                    final.emit("__lisp_stdout:\n    resq 1")
                    final.emit("__lisp_stdin:\n    resq 1")
                    final.emit("__lisp_written:\n    resd 1")
                    final.emit("__lisp_read_count:\n    resd 1")
                    final.emit("__lisp_input_buffer:\n    resq 1")
                final.emit("__lisp_format_buffer:\n    resb 64")
            for name, typ in sorted(self.globals.items()):
                unit = "resq 1" if typ == "string" else "resd 1"
                final.emit(f"{self._global_label(name)}:\n    {unit}")
        else:
            # Der vorhandene PE32-Assembler hat noch kein echtes .bss-Modell.
            # Kleine Runtime-/Globalwerte werden deshalb nullinitialisiert in .data abgelegt.
            if self.is_main_program:
                if not self.is_gui:
                    final.emit("__lisp_stdout:\n    dd 0")
                    final.emit("__lisp_stdin:\n    dd 0")
                    final.emit("__lisp_written:\n    dd 0")
                    final.emit("__lisp_read_count:\n    dd 0")
                    final.emit("__lisp_input_buffer:\n    dd 0")
                final.emit("__lisp_format_buffer:\n    db " + ", ".join("0" for _ in range(64)))
            for name, typ in sorted(self.globals.items()):
                final.emit(f"{self._global_label(name)}:\n    dd 0")

        source_kind = "program" if self.is_main_program else "unit"
        if source_kind == "unit":
            self.notes.append("Reines DEFUN-Modul: F2 erzeugt ein COFF-Objekt; kein eigenständiger _start-Einstieg.")
        else:
            if self.is_gui:
                self.notes.append("Windows-LISP-GUI-Hauptprogramm ohne Konsole; PRINT/PRINTLN verwenden MessageBoxA.")
            else:
                self.notes.append("Windows-LISP-Hauptprogramm mit internem Console-Startup und _start-Einstieg.")
        return LispCompileResult(
            assembly=final.render(),
            source_kind=source_kind,
            program_name=Path(self.filename).stem or "lisp_program",
            warnings=tuple(self.warnings),
            notes=tuple(self.notes),
            functions=tuple(info.name for info in self.function_order),
            globals=tuple(sorted(self.globals)),
        )


def compile_lisp_to_assembly(
    source: str,
    *,
    filename: str = "<LISP>",
    target: str = "pe32",
    windows_application_mode: str = "Console",
) -> LispCompileResult:
    return LispCompiler(
        source,
        filename=filename,
        target=target,
        windows_application_mode=windows_application_mode,
    ).compile()
