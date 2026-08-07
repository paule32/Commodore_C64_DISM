"""ANTLR-basierter C-Compiler für MOS 6510 und Motorola 68000.

Das C-Frontend baut einen kleinen, C-spezifischen AST auf. Danach wählen C64
und Amiga getrennte Codegeneratoren und getrennte Laufzeitroutinen: MOS 6510
für ein C64-PRG oder Motorola 68000 für ein eigenständig bootfähiges ADF.
"""

from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from c64pascal.compiler import (
    ArrayTypeSpecification,
    AssignmentStatement,
    BinaryExpression,
    BOOLEAN_TYPE,
    BreakStatement,
    CallExpression,
    CallStatement,
    CompoundStatement,
    ConstDeclaration,
    ContinueStatement,
    DesignatorExpression,
    Expression,
    ExternalRoutineDeclaration,
    ForStatement,
    IfStatement,
    IndexSelector,
    LiteralExpression,
    NameExpression,
    ParameterDeclaration,
    PascalProgram,
    RepeatStatement,
    STRING_TYPE,
    SourcePosition,
    Statement,
    TypeDeclaration,
    UnaryExpression,
    VarDeclaration,
    WhileStatement,
    _AmigaCodeGenerator,
    _PE32CodeGenerator,
    _CodeGenerator,
    _PascalType,
    _StorageAccess,
    _Variable,
)

from .generated.C64CLexer import C64CLexer
from .generated.C64CParser import C64CParser
from .generated.C64CParserVisitor import C64CParserVisitor
from .preprocessor import (
    C64PreprocessorError,
    PreprocessResult,
    PreprocessorDiagnostic,
    SourceLocation,
    preprocess_c_source,
)


class C64CError(Exception):
    """C-Fehler mit genauer Position im Quelltext."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        filename: Optional[str] = None,
        include_stack: Sequence[str] = (),
    ) -> None:
        self.message = str(message)
        self.line = int(line) if line else None
        self.column = int(column) + 1 if column is not None else None
        self.filename = str(filename) if filename else None
        self.include_stack = tuple(str(item) for item in include_stack)
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.line is None:
            return self.message
        prefix = f"{self.filename}:" if self.filename else "Zeile "
        if self.column is None:
            text = f"{prefix}{self.line}: {self.message}"
        elif self.filename:
            text = f"{prefix}{self.line}:{self.column}: {self.message}"
        else:
            text = f"Zeile {self.line}, Spalte {self.column}: {self.message}"
        if len(self.include_stack) > 1:
            text += "\nInclude-Kette: " + " -> ".join(self.include_stack)
        return text


@dataclass(frozen=True)
class GeneratedAssembly:
    program_name: str
    assembly: str
    source_map: Dict[int, int]
    variable_count: int
    string_count: int
    included_files: Tuple[str, ...] = ()
    macros: Tuple[str, ...] = ()
    notes: Tuple[PreprocessorDiagnostic, ...] = ()
    warnings: Tuple[PreprocessorDiagnostic, ...] = ()
    typedef_count: int = 0
    structure_count: int = 0
    prototype_count: int = 0
    enum_count: int = 0
    set_count: int = 0
    linked_assembly_files: Tuple[str, ...] = ()
    linked_c_files: Tuple[str, ...] = ()
    linked_pe32_modules: Tuple[Tuple[str, str], ...] = ()

    def c_line_for_assembly_line(self, assembly_line: int) -> int:
        line = int(assembly_line)
        while line > 0:
            source_line = self.source_map.get(line, 0)
            if source_line:
                return source_line
            line -= 1
        return 0

    def source_line_for_assembly_line(self, assembly_line: int) -> int:
        return self.c_line_for_assembly_line(assembly_line)


class _RaisingErrorListener(ErrorListener):
    def __init__(self, preprocessed: PreprocessResult) -> None:
        super().__init__()
        self.preprocessed = preprocessed

    def syntaxError(
        self,
        recognizer,
        offendingSymbol,
        line,
        column,
        msg,
        exc,
    ) -> None:
        del recognizer, offendingSymbol, exc
        location = self.preprocessed.location_for_line(line, column + 1)
        raise C64CError(
            f"Syntaxfehler: {msg}",
            location.line,
            location.column - 1,
            location.filename,
        )


@dataclass(frozen=True)
class _StructMember:
    name: str
    type_name: str
    pointer_depth: int
    location: SourceLocation


@dataclass(frozen=True)
class _CLocalVariable:
    name: str
    type_name: str
    position: SourcePosition
    is_static: bool = False
    initializer: Optional[Expression] = None


@dataclass(frozen=True)
class _CFunctionDefinition:
    name: str
    symbol: str
    return_type_name: Optional[str]
    parameters: Tuple[ParameterDeclaration, ...]
    local_variables: Tuple[_CLocalVariable, ...]
    body: CompoundStatement
    position: SourcePosition
    is_static: bool = False


@dataclass(frozen=True)
class _CArrayInfo:
    name: str
    dimensions: Tuple[int, ...]
    element_type_name: str
    pointer_depth: int
    position: SourcePosition
    is_local: bool = False
    is_static: bool = False


@dataclass(frozen=True)
class _CArrayAccessExpression(Expression):
    base_name: str
    indices: Tuple[Expression, ...]


@dataclass(frozen=True)
class _CArrayStoreStatement(Statement):
    base_name: str
    indices: Tuple[Expression, ...]
    operator: str
    expression: Expression


@dataclass(frozen=True)
class _CForStatement(Statement):
    """Allgemeine C-FOR-Schleife mit optionalen drei Kopfbestandteilen."""

    initializers: Tuple[Statement, ...]
    condition: Optional[Expression]
    update: Optional[Statement]
    body: Statement


@dataclass(frozen=True)
class _LoweredArrayDeclaration:
    name: str
    line: int
    dimensions: Tuple[str, ...]


@dataclass(frozen=True)
class _FrontendResult:
    program: PascalProgram
    preprocessed: PreprocessResult
    filename: str
    typedef_count: int
    structure_count: int
    prototype_count: int
    enum_count: int = 0
    set_count: int = 0
    functions: Tuple[_CFunctionDefinition, ...] = ()
    arrays: Tuple[_CArrayInfo, ...] = ()


@dataclass
class _CFunctionState:
    definition: _CFunctionDefinition
    return_type: object
    parameter_variables: Tuple[_Variable, ...]
    automatic_variables: Tuple[_Variable, ...]
    static_variables: Tuple[_Variable, ...]
    local_variables: Dict[str, _Variable]
    frame_size: int
    end_label: str


def _decode_c_literal(
    text: str,
    position: SourcePosition,
    filename: Optional[str] = None,
) -> str:
    try:
        value = ast.literal_eval(text)
    except (SyntaxError, ValueError) as exc:
        raise C64CError(
            "Ungueltiges C-Zeichen- oder Stringliteral.",
            position.line,
            position.column - 1,
            filename,
        ) from exc
    if not isinstance(value, str):
        raise C64CError(
            "Zeichenkette erwartet.",
            position.line,
            position.column - 1,
            filename,
        )
    return value


class _AstBuilder(C64CParserVisitor):
    """Wandelt den C-Parsebaum in die gemeinsame C64-Zwischenform um."""

    _BINARY_OPERATORS = {
        "||": "or",
        "&&": "and",
        "|": "or",
        "^": "xor",
        "&": "and",
        "==": "=",
        "!=": "<>",
        "<": "<",
        "<=": "<=",
        ">": ">",
        ">=": ">=",
        "+": "+",
        "-": "-",
        "*": "*",
        "/": "div",
        "%": "mod",
    }
    _ASSIGNMENT_OPERATORS = {
        "+=": "+",
        "-=": "-",
        "*=": "*",
        "/=": "div",
        "%=": "mod",
        "&=": "and",
        "|=": "or",
        "^=": "xor",
    }

    def __init__(
        self,
        filename: str,
        preprocessed: PreprocessResult,
        *,
        require_main: bool = True,
        array_declarations: Sequence[_LoweredArrayDeclaration] = (),
    ) -> None:
        super().__init__()
        self.filename = filename
        self.preprocessed = preprocessed
        self.require_main = bool(require_main)
        self.constants: List[ConstDeclaration] = []
        self.variables: List[VarDeclaration] = []
        self.type_declarations: List[TypeDeclaration] = []
        self.array_infos: List[_CArrayInfo] = []
        self._array_declarations: Dict[Tuple[int, str], List[_LoweredArrayDeclaration]] = {}
        for declaration in array_declarations:
            self._array_declarations.setdefault(
                (int(declaration.line), declaration.name),
                [],
            ).append(declaration)
        self.typedefs: Dict[str, str] = {}
        self.structures: Dict[str, Tuple[_StructMember, ...]] = {}
        self.prototypes: Dict[str, object] = {}
        self.external_routines: List[ExternalRoutineDeclaration] = []
        self.struct_variables: Dict[str, str] = {}
        self.function_definitions: List[_CFunctionDefinition] = []
        self._local_declaration_sink: Optional[List[_CLocalVariable]] = None
        self._scope_stack: List[Dict[str, str]] = []
        self._current_function_name: Optional[str] = None
        self._local_name_counter = 0

    def _location(self, context) -> SourceLocation:
        return self.preprocessed.location_for_line(
            context.start.line,
            context.start.column + 1,
        )

    def _position(self, context) -> SourcePosition:
        location = self._location(context)
        return SourcePosition(location.line, location.column)

    def _error(self, message: str, context) -> C64CError:
        location = self._location(context)
        return C64CError(
            message,
            location.line,
            location.column - 1,
            location.filename,
        )

    def _type_name(self, ctx) -> str:
        if ctx.VOID():
            return "void"
        if ctx.BOOL():
            return "boolean"
        if ctx.STRUCT():
            return f"struct:{ctx.IDENTIFIER().getText()}"
        if ctx.CHAR():
            return "byte" if ctx.UNSIGNED() else "char"
        if ctx.INT() or ctx.SIGNED() or ctx.UNSIGNED():
            return "integer"
        original = ctx.IDENTIFIER().getText()
        alias = self.typedefs.get(original)
        if alias is None:
            raise self._error(f"Unbekannter C-Typ: {original}.", ctx)
        seen = {original}
        while alias in self.typedefs and alias not in seen:
            seen.add(alias)
            alias = self.typedefs[alias]
        return alias

    @staticmethod
    def _has_qualifier(ctx, name: str) -> bool:
        return any(
            qualifier.getText().lower() == name.lower()
            for qualifier in ctx.declarationQualifier()
        )

    def _push_scope(self, initial: Optional[Mapping[str, str]] = None) -> None:
        self._scope_stack.append(dict(initial or {}))

    def _pop_scope(self) -> None:
        if not self._scope_stack:
            raise RuntimeError("C-Scope-Stack ist leer.")
        self._scope_stack.pop()

    def _declare_scoped_name(self, source_name: str, context) -> str:
        if not self._scope_stack:
            return source_name
        current = self._scope_stack[-1]
        if source_name in current:
            raise self._error(
                f"Lokaler Bezeichner mehrfach deklariert: {source_name}.",
                context,
            )
        self._local_name_counter += 1
        function_name = self._current_function_name or "scope"
        internal = (
            f"__c_local_{self._safe_identifier(function_name)}_"
            f"{self._local_name_counter}_{self._safe_identifier(source_name)}"
        )
        current[source_name] = internal
        return internal

    @staticmethod
    def _safe_identifier(name: str) -> str:
        return re.sub(r"[^A-Za-z0-9_]", "_", str(name)) or "value"

    def _resolve_scoped_name(self, source_name: str) -> str:
        for scope in reversed(self._scope_stack):
            internal = scope.get(source_name)
            if internal is not None:
                return internal
        return source_name

    def _static_initializer_value(
        self,
        expression: Optional[Expression],
        context,
    ) -> Optional[int]:
        if expression is None:
            return 0

        def evaluate(item: Expression) -> int:
            if isinstance(item, LiteralExpression) and not isinstance(item.value, str):
                return int(item.value)
            if isinstance(item, NameExpression):
                for declaration in self.constants:
                    if declaration.name == item.name:
                        return evaluate(declaration.expression)
                raise ValueError(item.name)
            if isinstance(item, UnaryExpression):
                value = evaluate(item.operand)
                if item.operator == "+":
                    return value
                if item.operator == "-":
                    return -value
                if item.operator == "not":
                    return int(not value)
                raise ValueError(item.operator)
            if isinstance(item, BinaryExpression):
                left = evaluate(item.left)
                right = evaluate(item.right)
                operations = {
                    "+": lambda: left + right,
                    "-": lambda: left - right,
                    "*": lambda: left * right,
                    "div": lambda: left // right,
                    "mod": lambda: left % right,
                    "and": lambda: left & right,
                    "or": lambda: left | right,
                    "xor": lambda: left ^ right,
                }
                operation = operations.get(item.operator)
                if operation is None:
                    raise ValueError(item.operator)
                return int(operation())
            raise ValueError(type(item).__name__)

        try:
            return evaluate(expression) & 0xFFFF
        except (ValueError, ZeroDivisionError) as exc:
            raise self._error(
                "Eine lokale static-Variable benoetigt einen konstanten "
                "Ganzzahl-Initialisierer.",
                context,
            ) from exc

    def _consume_struct_members(self, members) -> Tuple[_StructMember, ...]:
        result: List[_StructMember] = []
        names = set()
        for member in members:
            name = member.IDENTIFIER().getText()
            if name in names:
                raise self._error(f"Doppeltes struct-Feld: {name}.", member)
            names.add(name)
            result.append(
                _StructMember(
                    name,
                    self._type_name(member.typeSpecifier()),
                    len(member.STAR()),
                    self._location(member),
                )
            )
        return tuple(result)

    def _consume_typedef(self, ctx) -> None:
        if getattr(ctx, "aliasName", None) is not None:
            alias = ctx.aliasName.text
            tag_token = getattr(ctx, "tagName", None)
            canonical = tag_token.text if tag_token is not None else alias
            if canonical in self.structures:
                raise self._error(f"struct {canonical} wurde mehrfach definiert.", ctx)
            self.structures[canonical] = self._consume_struct_members(
                ctx.structMemberDeclaration()
            )
            self.typedefs[alias] = f"struct:{canonical}"
            return

        alias = ctx.IDENTIFIER().getText()
        if alias in self.typedefs:
            raise self._error(f"typedef {alias} wurde mehrfach definiert.", ctx)
        base = self._type_name(ctx.typeSpecifier())
        if ctx.STAR():
            base = f"pointer:{base}"
        self.typedefs[alias] = base

    def _consume_struct_declaration(self, ctx) -> None:
        tag = ctx.IDENTIFIER().getText()
        if tag in self.structures:
            raise self._error(f"struct {tag} wurde mehrfach definiert.", ctx)
        self.structures[tag] = self._consume_struct_members(
            ctx.structMemberDeclaration()
        )

    def _function_symbol(self, ctx, name: str) -> str:
        if not self._has_qualifier(ctx, "static"):
            return name
        source_path = Path(self.filename).expanduser().resolve()
        stem = source_path.stem
        safe_stem = re.sub(r"[^A-Za-z0-9_]", "_", stem) or "module"
        safe_name = re.sub(r"[^A-Za-z0-9_]", "_", name) or "function"
        digest = hashlib.sha1(str(source_path).encode("utf-8")).hexdigest()[:8]
        return f"__c_static_{safe_stem}_{digest}_{safe_name}"

    def _function_signature(
        self,
        ctx,
    ) -> Tuple[str, str, Tuple[ParameterDeclaration, ...], str, bool]:
        name = ctx.IDENTIFIER().getText()
        return_type = self._type_name(ctx.typeSpecifier())
        if ctx.STAR() or return_type.startswith("pointer:"):
            return_type = "integer"

        parameters: List[ParameterDeclaration] = []
        parameter_list = ctx.parameterList()
        if parameter_list is not None and not parameter_list.VOID():
            is_variadic = (
                getattr(parameter_list, "ELLIPSIS", lambda: None)()
                is not None
            )
            compound_getter = getattr(ctx, "compoundStatement", None)
            is_definition = (
                callable(compound_getter)
                and compound_getter() is not None
            )

            # Ein Prototyp wie
            #
            #     int printf(const char *format, ...);
            #
            # beschreibt lediglich die Aufrufschnittstelle und muss beim
            # Einlesen eines Headers erlaubt sein. Ein eigener variadischer
            # Funktionskoerper benoetigt dagegen va_list/va_start sowie eine
            # festgelegte Ziel-ABI und wird deshalb weiterhin abgewiesen.
            if is_variadic and is_definition:
                raise self._error(
                    "Variadische Funktionsdefinitionen werden nicht unterstuetzt.",
                    parameter_list,
                )

            for index, parameter in enumerate(parameter_list.parameterDeclaration()):
                type_name = self._type_name(parameter.typeSpecifier())
                if parameter.STAR() or type_name.startswith("pointer:"):
                    type_name = "integer"
                identifier = parameter.IDENTIFIER()
                parameter_name = (
                    identifier.getText()
                    if identifier is not None
                    else f"arg{index + 1}"
                )
                parameters.append(
                    ParameterDeclaration(
                        (parameter_name,),
                        type_name,
                        "value",
                        self._position(parameter),
                    )
                )

        is_static = self._has_qualifier(ctx, "static")
        symbol = self._function_symbol(ctx, name)
        return name, return_type, tuple(parameters), symbol, is_static

    def _consume_prototype(self, ctx) -> None:
        name, return_type, parameters, symbol, unused_static = (
            self._function_signature(ctx)
        )
        del unused_static

        previous = self.prototypes.get(name)
        if previous is not None:
            # Wiederholte Header-Prototypen und eine spätere Definition sind erlaubt.
            return

        self.prototypes[name] = ctx
        self.external_routines.append(
            ExternalRoutineDeclaration(
                "C",
                "procedure" if return_type == "void" else "function",
                name,
                parameters,
                None if return_type == "void" else return_type,
                symbol,
            )
        )

    def _parse_function_definition(self, ctx) -> _CFunctionDefinition:
        name, return_type, parameters, symbol, is_static = (
            self._function_signature(ctx)
        )
        local_variables: List[_CLocalVariable] = []
        previous_sink = self._local_declaration_sink
        previous_function = self._current_function_name
        previous_scopes = self._scope_stack
        self._local_declaration_sink = local_variables
        self._current_function_name = name
        self._scope_stack = []
        parameter_scope: Dict[str, str] = {}
        for parameter in parameters:
            parameter_name = parameter.names[0]
            if parameter_name in parameter_scope:
                raise self._error(
                    f"Parameter mehrfach deklariert: {parameter_name}.",
                    ctx,
                )
            parameter_scope[parameter_name] = parameter_name
        self._push_scope(parameter_scope)
        try:
            body = self._visit_compound_statement(
                ctx.compoundStatement(),
                push_scope=False,
            )
        finally:
            self._scope_stack = previous_scopes
            self._current_function_name = previous_function
            self._local_declaration_sink = previous_sink
        return _CFunctionDefinition(
            name=name,
            symbol=symbol,
            return_type_name=None if return_type == "void" else return_type,
            parameters=parameters,
            local_variables=tuple(local_variables),
            body=body,
            position=self._position(ctx),
            is_static=is_static,
        )

    def visitTranslationUnit(self, ctx):
        function_contexts = []
        main_function = None

        # Erste Phase: Typen, Deklarationen und alle Funktionssignaturen.
        # Auch main wird als normale Funktion erzeugt; damit besitzt main
        # denselben rekursionsfesten Stackframe wie jede andere C-Funktion.
        for external in ctx.externalDeclaration():
            if external.typedefDeclaration():
                self._consume_typedef(external.typedefDeclaration())
                continue
            if external.structDeclaration():
                self._consume_struct_declaration(external.structDeclaration())
                continue
            if external.functionPrototype():
                self._consume_prototype(external.functionPrototype())
                continue
            if external.declaration():
                self._consume_declaration(external.declaration(), local=False)
                continue
            function = external.functionDefinition()
            function_contexts.append(function)
            name = function.IDENTIFIER().getText()
            if name == "main":
                if main_function is not None:
                    raise self._error("main wurde mehrfach definiert.", function)
                main_function = function
            self._consume_prototype(function)

        if self.require_main and main_function is None:
            raise self._error("Die Funktion main fehlt.", ctx)
        if not self.require_main and main_function is not None:
            raise self._error(
                "Eine mit #pragma link eingebundene C-Datei darf keine main-Funktion enthalten.",
                main_function,
            )

        for function in function_contexts:
            name = function.IDENTIFIER().getText()
            if name == "main":
                return_type = self._type_name(function.typeSpecifier())
                if function.STAR():
                    return_type = "integer"
                if return_type not in {"integer", "void"}:
                    raise self._error(
                        "main muss int oder void zurueckgeben.",
                        function,
                    )
                parameters = function.parameterList()
                if parameters is not None and not parameters.VOID():
                    raise self._error(
                        "main unterstuetzt nur (void) oder ().",
                        parameters,
                    )
            self.function_definitions.append(
                self._parse_function_definition(function)
            )

        filename = Path(self.filename).name
        program_name = (
            Path(filename).stem
            if filename and not filename.startswith("<")
            else "main"
        )
        return PascalProgram(
            program_name,
            tuple(self.constants),
            tuple(self.variables),
            CompoundStatement(SourcePosition(1, 1), ()),
            types=tuple(self.type_declarations),
            external_routines=tuple(self.external_routines),
            unit_assembly_files=tuple(self.preprocessed.linked_assembly_files),
        )

    def _append_local_variable(
        self,
        name: str,
        type_name: str,
        position: SourcePosition,
        *,
        is_static: bool,
        initializer: Optional[Expression],
    ) -> None:
        if self._local_declaration_sink is None:
            raise RuntimeError("Lokale C-Deklaration ohne Funktionskontext.")
        self._local_declaration_sink.append(
            _CLocalVariable(
                name,
                type_name,
                position,
                is_static,
                initializer,
            )
        )

    def _declare_struct_fields(
        self,
        base_name: str,
        canonical: str,
        position: SourcePosition,
        context,
        *,
        local: bool,
        is_static: bool,
        seen: Optional[Set[str]] = None,
    ) -> None:
        members = self.structures.get(canonical)
        if members is None:
            raise self._error(f"struct {canonical} ist nicht definiert.", context)
        seen = set(seen or ())
        if canonical in seen:
            raise self._error(
                f"Rekursive eingebettete struct-Definition: {canonical}.",
                context,
            )
        seen.add(canonical)
        self.struct_variables[base_name] = canonical
        for member in members:
            field_name = f"{base_name}.{member.name}"
            member_type = member.type_name
            if member.pointer_depth or member_type.startswith("pointer:"):
                member_type = "integer"
            if member_type.startswith("struct:"):
                nested = member_type.split(":", 1)[1]
                self._declare_struct_fields(
                    field_name,
                    nested,
                    position,
                    context,
                    local=local,
                    is_static=is_static,
                    seen=seen,
                )
                continue
            if local:
                self._append_local_variable(
                    field_name,
                    member_type,
                    position,
                    is_static=is_static,
                    initializer=None,
                )
            else:
                self.variables.append(
                    VarDeclaration((field_name,), member_type, None, position)
                )

    @staticmethod
    def _evaluate_array_dimension(text: str, context) -> int:
        value_text = str(text).strip().rstrip("uUlL")
        if re.fullmatch(r"0[xX][0-9A-Fa-f]+", value_text):
            value = int(value_text, 16)
        elif re.fullmatch(r"0[bB][01]+", value_text):
            value = int(value_text[2:], 2)
        elif re.fullmatch(r"[0-9]+", value_text):
            value = int(value_text, 10)
        else:
            raise C64CError(
                "Arraygroessen muessen nach der Makroexpansion konstante "
                f"positive Ganzzahlen sein: {text!r}.",
                context.start.line,
                context.start.column,
            )
        if value <= 0:
            raise C64CError(
                f"Arraygroesse muss groesser als 0 sein: {value}.",
                context.start.line,
                context.start.column,
            )
        return value

    def _take_array_declaration(self, item, source_name: str):
        key = (int(item.start.line), source_name)
        declarations = self._array_declarations.get(key)
        if not declarations:
            return None
        declaration = declarations.pop(0)
        if not declarations:
            self._array_declarations.pop(key, None)
        return declaration

    def _make_array_type(
        self,
        source_name: str,
        internal_name: str,
        base_type_name: str,
        pointer_depth: int,
        dimensions: Tuple[int, ...],
        position: SourcePosition,
        *,
        local: bool,
        is_static: bool,
    ) -> str:
        total_count = 1
        for dimension in dimensions:
            total_count *= int(dimension)
            if total_count > 65535:
                raise C64CError(
                    f"Array {source_name} ist fuer dieses Compilerprofil zu gross.",
                    position.line,
                    position.column - 1,
                    self.filename,
                )

        element_type = "__c_pointer" if pointer_depth else base_type_name
        type_name = (
            f"__c_array_{self._safe_identifier(self._current_function_name or 'global')}_"
            f"{len(self.array_infos)}_{self._safe_identifier(source_name)}"
        )
        self.type_declarations.append(
            TypeDeclaration(
                type_name,
                ArrayTypeSpecification(
                    position,
                    LiteralExpression(position, 0),
                    LiteralExpression(position, total_count - 1),
                    element_type,
                ),
                position,
            )
        )
        self.array_infos.append(
            _CArrayInfo(
                internal_name,
                tuple(dimensions),
                base_type_name,
                int(pointer_depth),
                position,
                local,
                is_static,
            )
        )
        return type_name

    def _consume_declaration(self, ctx, *, local: bool) -> List[Statement]:
        type_name = self._type_name(ctx.typeSpecifier())
        if type_name == "void":
            raise self._error("Eine Variable kann nicht vom Typ void sein.", ctx)
        is_const = self._has_qualifier(ctx, "const")
        is_static = local and self._has_qualifier(ctx, "static")
        initializer_statements: List[Statement] = []

        for item in ctx.initDeclaratorList().initDeclarator():
            source_name = item.IDENTIFIER().getText()
            internal_name = (
                self._declare_scoped_name(source_name, item)
                if local
                else source_name
            )
            expression = self.visit(item.expression()) if item.expression() else None
            position = self._position(item)
            item_type = type_name
            pointer_depth = len(item.STAR())
            array_declaration = self._take_array_declaration(item, source_name)
            if array_declaration is not None:
                if expression is not None:
                    raise self._error(
                        "Array-Initialisierer in geschweiften Klammern folgen in "
                        "einer spaeteren Stufe.",
                        item,
                    )
                dimensions = tuple(
                    self._evaluate_array_dimension(value, item)
                    for value in array_declaration.dimensions
                )
                item_type = self._make_array_type(
                    source_name,
                    internal_name,
                    type_name,
                    pointer_depth,
                    dimensions,
                    position,
                    local=local,
                    is_static=is_static,
                )
            elif pointer_depth or item_type.startswith("pointer:"):
                item_type = "integer"

            if item_type.startswith("struct:"):
                if expression is not None:
                    raise self._error(
                        "struct-Initialisierer werden noch nicht unterstuetzt.",
                        item,
                    )
                canonical = item_type.split(":", 1)[1]
                self._declare_struct_fields(
                    internal_name,
                    canonical,
                    position,
                    item,
                    local=local,
                    is_static=is_static,
                )
                continue

            if is_const and not local:
                if expression is None:
                    raise self._error(
                        "Eine const-Deklaration benoetigt einen Initialwert.",
                        item,
                    )
                self.constants.append(
                    ConstDeclaration(source_name, expression, position)
                )
                continue

            if local:
                static_initializer = (
                    LiteralExpression(
                        position,
                        self._static_initializer_value(expression, item),
                    )
                    if is_static
                    else None
                )
                self._append_local_variable(
                    internal_name,
                    item_type,
                    position,
                    is_static=is_static,
                    initializer=static_initializer,
                )
                if not is_static and expression is not None:
                    initializer_statements.append(
                        AssignmentStatement(position, internal_name, expression)
                    )
                elif is_const and expression is None:
                    raise self._error(
                        "Eine lokale const-Deklaration benoetigt einen Initialwert.",
                        item,
                    )
                continue

            self.variables.append(
                VarDeclaration((source_name,), item_type, expression, position)
            )

        return initializer_statements

    def _visit_compound_statement(
        self,
        ctx,
        *,
        push_scope: bool,
    ) -> CompoundStatement:
        statements: List[Statement] = []
        if push_scope:
            self._push_scope()
        try:
            for item in ctx.blockItem():
                if item.declaration():
                    statements.extend(
                        self._consume_declaration(item.declaration(), local=True)
                    )
                else:
                    statements.append(self.visit(item.statement()))
        finally:
            if push_scope:
                self._pop_scope()
        return CompoundStatement(self._position(ctx), tuple(statements))

    def visitCompoundStatement(self, ctx):
        return self._visit_compound_statement(ctx, push_scope=True)

    def visitStatement(self, ctx):
        for name in (
            "compoundStatement",
            "ifStatement",
            "whileStatement",
            "doWhileStatement",
            "forStatement",
            "jumpStatement",
            "expressionStatement",
        ):
            child = getattr(ctx, name)()
            if child is not None:
                return self.visit(child)
        raise self._error("Nicht unterstuetzte C-Anweisung.", ctx)

    def visitExpressionStatement(self, ctx):
        if ctx.assignmentExpression():
            return self._assignment_statement(ctx.assignmentExpression())
        if ctx.callExpression():
            return self._call_statement(ctx.callExpression())
        return CompoundStatement(self._position(ctx), ())

    def visitIfStatement(self, ctx):
        statements = ctx.statement()
        return IfStatement(
            self._position(ctx),
            self.visit(ctx.expression()),
            self.visit(statements[0]),
            self.visit(statements[1]) if len(statements) > 1 else None,
        )

    def visitWhileStatement(self, ctx):
        return WhileStatement(
            self._position(ctx),
            self.visit(ctx.expression()),
            self.visit(ctx.statement()),
        )

    def visitDoWhileStatement(self, ctx):
        condition = self.visit(ctx.expression())
        repeat_condition = UnaryExpression(
            condition.position,
            "not",
            condition,
        )
        return RepeatStatement(
            self._position(ctx),
            (self.visit(ctx.statement()),),
            repeat_condition,
        )

    def visitForStatement(self, ctx):
        """Erzeugt eine allgemeine C-FOR-Schleife.

        C erlaubt jeden der drei Bestandteile auszulassen, insbesondere die
        verbreitete Endlosschleife ``for (;;)``.  Die alte Implementierung
        versuchte jede FOR-Schleife in die eingeschraenkte Pascal-FOR-Form
        umzuwandeln und verlangte deshalb Initialisierung, Vergleich und
        Inkrement.
        """
        self._push_scope()
        try:
            initializer = ctx.forInitializer()
            condition_ctx = ctx.expression()
            update_ctx = ctx.assignmentExpression()

            initializer_statements: List[Statement] = []
            if initializer is not None:
                if initializer.declaration() is not None:
                    initializer_statements.extend(
                        self._consume_declaration(
                            initializer.declaration(),
                            local=True,
                        )
                    )
                else:
                    initializer_statements.append(
                        self._assignment_statement(
                            initializer.assignmentExpression()
                        )
                    )

            condition = (
                self.visit(condition_ctx)
                if condition_ctx is not None
                else None
            )
            update = (
                self._assignment_statement(update_ctx)
                if update_ctx is not None
                else None
            )

            return _CForStatement(
                self._position(ctx),
                tuple(initializer_statements),
                condition,
                update,
                self.visit(ctx.statement()),
            )
        finally:
            self._pop_scope()

    def visitJumpStatement(self, ctx):
        if ctx.BREAK():
            return BreakStatement(self._position(ctx))
        if ctx.CONTINUE():
            return ContinueStatement(self._position(ctx))
        arguments = (self.visit(ctx.expression()),) if ctx.expression() else ()
        return CallStatement(self._position(ctx), "__c_return", arguments)

    def _lvalue_name(self, ctx) -> str:
        parts = [token.getText() for token in ctx.IDENTIFIER()]
        base = self._resolve_scoped_name(parts[0])
        if len(parts) == 1:
            return base

        current = base
        for member_name in parts[1:]:
            canonical = self.struct_variables.get(current)
            if canonical is None:
                raise self._error(f"{current} ist keine struct-Variable.", ctx)
            members = {
                member.name: member
                for member in self.structures.get(canonical, ())
            }
            member = members.get(member_name)
            if member is None:
                raise self._error(
                    f"struct {canonical} besitzt kein Feld {member_name}.",
                    ctx,
                )
            current = f"{current}.{member_name}"
        return current

    def _assignment_statement(self, ctx) -> AssignmentStatement:
        name = self._lvalue_name(ctx.lvalue())
        position = self._position(ctx)
        if ctx.assignmentOperator():
            operator = ctx.assignmentOperator().getText()
            right = self.visit(ctx.expression())
            if operator == "=":
                return AssignmentStatement(position, name, right)
            mapped = self._ASSIGNMENT_OPERATORS[operator]
            return AssignmentStatement(
                position,
                name,
                BinaryExpression(
                    position,
                    NameExpression(position, name),
                    mapped,
                    right,
                ),
            )
        operator = "+" if ctx.INC() else "-"
        return AssignmentStatement(
            position,
            name,
            BinaryExpression(
                position,
                NameExpression(position, name),
                operator,
                LiteralExpression(position, 1),
            ),
        )

    def _array_designator(
        self,
        base_name: str,
        indices: Tuple[Expression, ...],
        position: SourcePosition,
        context,
    ) -> DesignatorExpression:
        info = next(
            (item for item in reversed(self.array_infos) if item.name == base_name),
            None,
        )
        if info is None:
            raise self._error(f"Array nicht gefunden: {base_name}.", context)
        if len(indices) != len(info.dimensions):
            raise self._error(
                f"Array {base_name} erwartet {len(info.dimensions)} Indizes, "
                f"erhalten: {len(indices)}.",
                context,
            )

        # Die gemeinsame Pascal-Zwischenform kennt bereits feste Arrays. Fuer
        # C-Mehrdimensionalitaet wird der Row-Major-Index auf den bei der
        # Deklaration angelegten flachen Speicherbereich abgebildet:
        #
        #     a[i][j][k] -> ((i * dim1 + j) * dim2 + k)
        flat_index = indices[0]
        for dimension, index_expression in zip(info.dimensions[1:], indices[1:]):
            flat_index = BinaryExpression(
                position,
                BinaryExpression(
                    position,
                    flat_index,
                    "*",
                    LiteralExpression(position, int(dimension)),
                ),
                "+",
                index_expression,
            )

        return DesignatorExpression(
            position,
            base_name,
            (IndexSelector(position, flat_index),),
        )

    def _call_arguments(self, ctx) -> Tuple[Expression, ...]:
        argument_list = ctx.argumentList()
        if argument_list is None:
            return ()
        return tuple(self.visit(item) for item in argument_list.expression())

    def _call_expression(self, ctx) -> Expression:
        name = ctx.IDENTIFIER().getText()
        arguments = self._call_arguments(ctx)

        array_match = re.fullmatch(r"__d64_arr_get_(\d+)", name)
        if array_match is not None:
            index_count = int(array_match.group(1))
            if len(arguments) != index_count + 1:
                raise self._error("Interner Arrayzugriff besitzt falsche Argumentzahl.", ctx)
            base = arguments[0]
            if not isinstance(base, NameExpression):
                raise self._error("Arraybasis muss ein Bezeichner sein.", ctx)
            return self._array_designator(
                base.name,
                tuple(arguments[1:]),
                self._position(ctx),
                ctx,
            )

        if name in {"__d64_shl", "__d64_shr"}:
            if len(arguments) != 2:
                raise self._error("Shift-Operator erwartet zwei Operanden.", ctx)
            return BinaryExpression(
                self._position(ctx),
                arguments[0],
                "shl" if name == "__d64_shl" else "shr",
                arguments[1],
            )

        mapped = {
            "peek": "peek",
            "c64_peek": "peek",
            "chr": "chr",
            "c64_chr": "chr",
            "ord": "ord",
            "lo": "lo",
            "hi": "hi",
        }.get(name)
        if mapped is None:
            if name in self.prototypes:
                mapped = name
            else:
                raise self._error(f"Unbekannte C-Funktion: {name}.", ctx)
        return CallExpression(self._position(ctx), mapped, arguments)

    def _call_statement(self, ctx) -> Statement:
        name = ctx.IDENTIFIER().getText()
        arguments = self._call_arguments(ctx)
        position = self._position(ctx)

        array_match = re.fullmatch(
            r"__d64_arr_store_(set|or|and|xor|add|sub)_(\d+)",
            name,
        )
        if array_match is not None:
            index_count = int(array_match.group(2))
            if len(arguments) != index_count + 2:
                raise self._error("Interne Arrayzuweisung besitzt falsche Argumentzahl.", ctx)
            base = arguments[0]
            if not isinstance(base, NameExpression):
                raise self._error("Arraybasis muss ein Bezeichner sein.", ctx)
            designator = self._array_designator(
                base.name,
                tuple(arguments[1:1 + index_count]),
                position,
                ctx,
            )
            operation = array_match.group(1)
            value = arguments[-1]
            if operation != "set":
                value = BinaryExpression(
                    position,
                    designator,
                    {
                        "or": "or",
                        "and": "and",
                        "xor": "xor",
                        "add": "+",
                        "sub": "-",
                    }[operation],
                    value,
                )
            return AssignmentStatement(position, designator, value)

        if name == "printf":
            return self._printf_statement(arguments, position, ctx)
        if name == "puts":
            return CallStatement(position, "writeln", arguments)
        if name == "putchar":
            if len(arguments) != 1:
                raise self._error("putchar erwartet genau ein Argument.", ctx)
            character = CallExpression(position, "chr", (arguments[0],))
            return CallStatement(position, "write", (character,))
        mapped = {
            "c64_write": "write",
            "c64_writeln": "writeln",
            "c64_print_int": "write",
            "clrscr": "clrscr",
            "c64_clrscr": "clrscr",
            "amiga_set_text_color": "amiga_set_text_color",
            "poke": "poke",
            "c64_poke": "poke",
            "halt": "halt",
            "c64_halt": "halt",
        }.get(name)
        if mapped is None:
            if name in self.prototypes:
                mapped = name
            else:
                raise self._error(f"Unbekannte C-Funktion: {name}.", ctx)
        return CallStatement(position, mapped, arguments)

    def _printf_statement(
        self,
        arguments: Tuple[Expression, ...],
        position: SourcePosition,
        context,
    ) -> Statement:
        if not arguments or not isinstance(arguments[0], LiteralExpression) or not isinstance(arguments[0].value, str):
            raise self._error("printf erwartet ein konstantes Formatliteral.", context)
        format_text = arguments[0].value
        values = list(arguments[1:])
        value_index = 0
        statements: List[Statement] = []
        text_buffer: List[str] = []

        def flush_text() -> None:
            if text_buffer:
                statements.append(
                    CallStatement(
                        position,
                        "write",
                        (LiteralExpression(position, "".join(text_buffer)),),
                    )
                )
                text_buffer.clear()

        index = 0
        while index < len(format_text):
            character = format_text[index]
            if character != "%":
                text_buffer.append(character)
                index += 1
                continue
            if index + 1 >= len(format_text):
                raise self._error("Unvollstaendiger printf-Formatbezeichner.", context)
            specifier = format_text[index + 1]
            if specifier == "%":
                text_buffer.append("%")
                index += 2
                continue
            if specifier not in {"d", "i", "u", "c", "s"}:
                raise self._error(f"printf-Format %{specifier} wird nicht unterstuetzt.", context)
            if value_index >= len(values):
                raise self._error("printf hat zu wenige Argumente.", context)
            flush_text()
            value = values[value_index]
            value_index += 1
            if specifier == "c":
                value = CallExpression(position, "chr", (value,))
            statements.append(CallStatement(position, "write", (value,)))
            index += 2
        flush_text()
        if value_index != len(values):
            raise self._error("printf hat zu viele Argumente.", context)
        return CompoundStatement(position, tuple(statements))

    def _fold_binary(self, ctx):
        result = self.visit(ctx.getChild(0))
        for index in range(1, ctx.getChildCount(), 2):
            token = ctx.getChild(index).getText()
            result = BinaryExpression(
                result.position,
                result,
                self._BINARY_OPERATORS[token],
                self.visit(ctx.getChild(index + 1)),
            )
        return result

    def visitExpression(self, ctx):
        return self.visit(ctx.logicalOrExpression())

    def visitLogicalOrExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitLogicalAndExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitBitwiseOrExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitBitwiseXorExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitBitwiseAndExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitEqualityExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitRelationalExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitAdditiveExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitMultiplicativeExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitUnaryExpression(self, ctx):
        if ctx.primaryExpression():
            return self.visit(ctx.primaryExpression())
        operand = self.visit(ctx.unaryExpression())
        operator = ctx.getChild(0).getText()
        if operator == "!":
            return UnaryExpression(self._position(ctx), "not", operand)
        if operator == "~":
            return BinaryExpression(
                self._position(ctx),
                operand,
                "xor",
                LiteralExpression(self._position(ctx), 0xFFFF),
            )
        return UnaryExpression(self._position(ctx), operator, operand)

    def visitPrimaryExpression(self, ctx):
        position = self._position(ctx)
        if ctx.integerLiteral():
            return self.visit(ctx.integerLiteral())
        if ctx.CHAR_LITERAL():
            value = _decode_c_literal(
                ctx.CHAR_LITERAL().getText(),
                position,
                self._location(ctx).filename,
            )
            if len(value) != 1:
                raise self._error("Ein C-Zeichenliteral muss genau ein Zeichen enthalten.", ctx)
            return LiteralExpression(position, ord(value))
        if ctx.STRING_LITERAL():
            return LiteralExpression(
                position,
                _decode_c_literal(
                    ctx.STRING_LITERAL().getText(),
                    position,
                    self._location(ctx).filename,
                ),
            )
        if ctx.TRUE():
            return LiteralExpression(position, True)
        if ctx.FALSE():
            return LiteralExpression(position, False)
        if ctx.callExpression():
            return self._call_expression(ctx.callExpression())
        if ctx.lvalue():
            return NameExpression(position, self._lvalue_name(ctx.lvalue()))
        return self.visit(ctx.expression())

    def visitIntegerLiteral(self, ctx):
        text = ctx.getText().rstrip("uUlL")
        if text.lower().startswith("0b"):
            value = int(text[2:], 2)
        elif text.lower().startswith("0x"):
            value = int(text[2:], 16)
        else:
            value = int(text, 10)
        return LiteralExpression(self._position(ctx), value)




@dataclass(frozen=True)
class _LoweredCExtensions:
    preprocessed: PreprocessResult
    enum_count: int
    set_count: int
    array_declarations: Tuple[_LoweredArrayDeclaration, ...] = ()


def _replacement_with_same_lines(original: str, replacement: str) -> str:
    """Ersetzt einen Sprachzusatz, ohne die Quellzeilennummern zu verschieben."""
    newline_count = original.count("\n")
    compact = " ".join(replacement.splitlines()).strip()
    return compact + ("\n" * newline_count)


def _split_enum_items(body: str) -> List[str]:
    items: List[str] = []
    current: List[str] = []
    depth = 0
    quote: Optional[str] = None
    index = 0
    while index < len(body):
        char = body[index]
        if quote is not None:
            current.append(char)
            if char == "\\" and index + 1 < len(body):
                index += 1
                current.append(body[index])
            elif char == quote:
                quote = None
        elif char in {"'", '"'}:
            quote = char
            current.append(char)
        elif char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth = max(0, depth - 1)
            current.append(char)
        elif char == "," and depth == 0:
            value = "".join(current).strip()
            if value:
                items.append(value)
            current.clear()
        else:
            current.append(char)
        index += 1
    value = "".join(current).strip()
    if value:
        items.append(value)
    return items


def _enum_constants(body: str) -> List[Tuple[str, str]]:
    result: List[Tuple[str, str]] = []
    previous_name: Optional[str] = None
    for item in _split_enum_items(body):
        if "=" in item:
            name, expression = item.split("=", 1)
            name = name.strip()
            expression = expression.strip()
        else:
            name = item.strip()
            expression = "0" if previous_name is None else f"{previous_name} + 1"
        if re.fullmatch(r"[A-Za-z_]\w*", name) is None:
            raise C64CError(f"Ungueltiger Enum-Bezeichner: {name!r}.")
        result.append((name, expression))
        previous_name = name
    return result


def _source_line_number(source: str, offset: int) -> int:
    return source.count("\n", 0, max(0, int(offset))) + 1


def _array_dimensions(text: str) -> Tuple[str, ...]:
    return tuple(
        value.strip()
        for value in re.findall(r"\[\s*([^\]\r\n]+?)\s*\]", text)
    )


def _array_chain_parts(text: str) -> Tuple[str, Tuple[str, ...]]:
    match = re.match(r"\s*([A-Za-z_]\w*)", text)
    if match is None:
        raise ValueError(text)
    return match.group(1), _array_dimensions(text[match.end():])


def _mask_c_comments_and_literals(source: str) -> str:
    """Blendet Kommentare sowie String-/Zeichenliterale positionsstabil aus.

    Die Array-Syntaxsenkung arbeitet absichtlich vor dem ANTLR-Parser. Ihre
    regulären Ausdrücke dürfen deshalb ausschließlich echten C-Code sehen.
    Jedes ausgeblendete Zeichen wird durch ein Leerzeichen ersetzt; Zeilen-
    umbrüche bleiben erhalten, damit Quellpositionen und ``line_map`` stimmen.
    """
    result = list(source)
    state = "code"
    quote = ""
    index = 0

    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""

        if state == "code":
            if char == "/" and next_char == "/":
                result[index] = " "
                result[index + 1] = " "
                state = "line_comment"
                index += 2
                continue
            if char == "/" and next_char == "*":
                result[index] = " "
                result[index + 1] = " "
                state = "block_comment"
                index += 2
                continue
            if char in {"\"", "'"}:
                quote = char
                result[index] = " "
                state = "literal"
                index += 1
                continue
            index += 1
            continue

        if state == "line_comment":
            if char in {"\n", "\r"}:
                state = "code"
            else:
                result[index] = " "
            index += 1
            continue

        if state == "block_comment":
            if char == "*" and next_char == "/":
                result[index] = " "
                result[index + 1] = " "
                state = "code"
                index += 2
                continue
            if char not in {"\n", "\r"}:
                result[index] = " "
            index += 1
            continue

        # String- oder Zeichenliteral. Escapes werden zusammen übersprungen,
        # damit beispielsweise ``"\\""`` das Literal nicht vorzeitig beendet.
        if char == "\\" and next_char:
            result[index] = " "
            if next_char not in {"\n", "\r"}:
                result[index + 1] = " "
            index += 2
            continue
        if char == quote:
            result[index] = " "
            state = "code"
            quote = ""
            index += 1
            continue
        if char not in {"\n", "\r"}:
            result[index] = " "
        index += 1

    return "".join(result)


def _lower_c_array_syntax(
    preprocessed: PreprocessResult,
) -> Tuple[PreprocessResult, Tuple[_LoweredArrayDeclaration, ...]]:
    """Senkt feste C-Arrays auf interne Funktionsformen ab.

    Die ausgelieferten ANTLR-Dateien stammen aus einer Grammarstufe ohne
    eckige Klammern. Diese Quellsenkung hält die Zeilennummern stabil und
    erlaubt trotzdem reguläre Deklarationen und indizierte Zugriffe.
    """
    source = preprocessed.source
    declarations: List[_LoweredArrayDeclaration] = []

    # Benutzerdefinierte Typnamen sind erlaubt, C-Schlüsselwörter wie
    # ``return`` aber ausdrücklich nicht. Ohne diese Sperre wurde etwa
    #
    #     return GfxFloodXLow[index];
    #
    # als Arraydeklaration mit dem vermeintlichen Typ ``return`` erkannt.
    non_type_keywords = (
        "return|if|else|while|do|for|switch|case|default|break|continue|"
        "goto|sizeof"
    )
    declaration_pattern = re.compile(
        r"(?P<prefix>\b(?:const\s+|extern\s+|static\s+)*"
        r"(?:(?:unsigned|signed)\s+)?"
        rf"(?:char|int|bool|_Bool|(?!{non_type_keywords}\b)[A-Za-z_]\w*|"
        r"struct\s+[A-Za-z_]\w*)"
        r"\s+(?:\*\s*)*)"
        r"(?P<name>[A-Za-z_]\w*)\s*"
        r"(?P<dims>(?:\[\s*[^\]\r\n]+\s*\])+)",
        re.MULTILINE,
    )

    # Nur der positionsstabile Maskentext wird durchsucht. Die Ersetzungen
    # selbst erfolgen rückwärts im unveränderten Originaltext, damit weder
    # Kommentare/Literale noch die Offsets späterer Treffer beschädigt werden.
    declaration_mask = _mask_c_comments_and_literals(source)
    replacements: List[Tuple[int, int, str]] = []
    for match in declaration_pattern.finditer(declaration_mask):
        dimensions = _array_dimensions(match.group("dims"))
        if not dimensions:
            continue
        declarations.append(
            _LoweredArrayDeclaration(
                match.group("name"),
                _source_line_number(source, match.start("name")),
                dimensions,
            )
        )
        replacements.append(
            (
                match.start(),
                match.end(),
                match.group("prefix") + match.group("name"),
            )
        )

    for start, end, replacement_text in reversed(replacements):
        source = source[:start] + replacement_text + source[end:]

    # Skalare Casts sind in dieser 8/16-Bit-Stufe reine Wertkonvertierungen.
    # Diese Absenkung muss auch ohne Array-Deklarationen stattfinden. Zuvor
    # wurde bei array_names == leer zu frueh zurueckgekehrt; dadurch blieb
    # etwa `(GraphicsColor)(foreground & 15u)` im Parser-Eingang erhalten.
    cast_pattern = re.compile(
        r"\(\s*(?:(?:unsigned|signed)\s+)?"
        r"(?:char|int|bool|_Bool|GraphicsColor|TextMode|uint8_t|uint16_t)"
        r"\s*\)"
    )
    source = cast_pattern.sub("", source)

    # Die ausgelieferte Grammar besitzt keine Shift-Ebene. Einfache Shifts
    # werden ebenfalls unabhaengig von Array-Deklarationen abgesenkt.
    # Ein Shift-Operand darf neben einem einfachen Bezeichner auch ein bereits
    # noch nicht abgesenkter Arrayzugriff sein.  Die Array-Absenkung erfolgt
    # weiter unten und wandelt z. B.
    #
    #     values[index] << 8
    #
    # zuerst in ``__d64_shl(values[index], 8)`` und danach in
    # ``__d64_shl(__d64_arr_get_1(values, index), 8)`` um.
    identifier_atom = (
        r"\b[A-Za-z_]\w*"
        r"(?:\s*\[\s*[^\]\r\n]+\s*\])*"
    )
    numeric_atom = (
        r"(?:\b0[xX][0-9A-Fa-f]+[uUlL]*\b|"
        r"\b0[bB][01]+[uUlL]*\b|"
        r"\b[0-9]+[uUlL]*\b)"
    )
    atom = rf"(?:{identifier_atom}|{numeric_atom})"
    shift_pattern = re.compile(
        rf"(?P<left>{atom})\s*(?P<op><<|>>)\s*(?P<right>{atom})"
    )
    while True:
        changed = False

        def replace_shift(match: re.Match[str]) -> str:
            nonlocal changed
            changed = True
            name = "__d64_shl" if match.group("op") == "<<" else "__d64_shr"
            return f"{name}({match.group('left')}, {match.group('right')})"

        source = shift_pattern.sub(replace_shift, source)
        if not changed:
            break

    array_names = {item.name for item in declarations}
    if not array_names:
        lowered = PreprocessResult(
            source,
            preprocessed.line_map,
            preprocessed.macros,
            preprocessed.included_files,
            preprocessed.notes,
            preprocessed.warnings,
            preprocessed.linked_assembly_files,
            preprocessed.linked_c_files,
        )
        return lowered, ()

    names_pattern = "|".join(
        re.escape(name) for name in sorted(array_names, key=len, reverse=True)
    )
    chain = rf"(?P<chain>\b(?:{names_pattern})(?:\s*\[\s*[^\]\r\n]+\s*\])+ )"
    # Das Leerzeichen am Ende ist nur ein Regex-Baustein und wird entfernt.
    chain = chain[:-2] + ")"

    assignment_pattern = re.compile(
        chain
        + r"\s*(?P<op>\|=|&=|\^=|\+=|-=|=)\s*"
        + r"(?P<rhs>[^;\r\n]+);"
    )
    operator_names = {
        "=": "set",
        "|=": "or",
        "&=": "and",
        "^=": "xor",
        "+=": "add",
        "-=": "sub",
    }

    def replace_assignment(match: re.Match[str]) -> str:
        base, indices = _array_chain_parts(match.group("chain"))
        arguments = ", ".join((base, *indices, match.group("rhs").strip()))
        return (
            f"__d64_arr_store_{operator_names[match.group('op')]}_"
            f"{len(indices)}({arguments});"
        )

    source = assignment_pattern.sub(replace_assignment, source)

    access_pattern = re.compile(chain)

    def replace_access(match: re.Match[str]) -> str:
        base, indices = _array_chain_parts(match.group("chain"))
        arguments = ", ".join((base, *indices))
        return f"__d64_arr_get_{len(indices)}({arguments})"

    source = access_pattern.sub(replace_access, source)

    lowered = PreprocessResult(
        source,
        preprocessed.line_map,
        preprocessed.macros,
        preprocessed.included_files,
        preprocessed.notes,
        preprocessed.warnings,
        preprocessed.linked_assembly_files,
        preprocessed.linked_c_files,
    )
    return lowered, tuple(declarations)


def _lower_c_type_extensions(preprocessed: PreprocessResult) -> _LoweredCExtensions:
    """Senkt enum- und set-Deklarationen auf bereits vorhandene C-Konstrukte ab.

    Dadurch müssen die ausgelieferten ANTLR-Dateien nicht durch einen anderen
    Generator ersetzt werden. Die öffentliche C-Syntax bleibt dennoch direkt
    nutzbar.
    """
    source = preprocessed.source
    enum_count = 0
    set_count = 0
    enum_tags: Set[str] = set()

    typedef_enum = re.compile(
        r"\btypedef\s+enum(?:\s+([A-Za-z_]\w*))?\s*"
        r"\{([^{}]*)\}\s*([A-Za-z_]\w*)\s*;",
        re.IGNORECASE | re.DOTALL,
    )
    plain_enum = re.compile(
        r"\benum\s+([A-Za-z_]\w*)\s*\{([^{}]*)\}\s*;",
        re.IGNORECASE | re.DOTALL,
    )

    while True:
        match = typedef_enum.search(source)
        if match is None:
            break
        tag, body, alias = match.groups()
        declarations: List[str] = [f"typedef int {alias};"]
        if tag and tag != alias:
            declarations.append(f"typedef int {tag};")
            enum_tags.add(tag)
        enum_tags.add(alias)
        declarations.extend(
            f"const int {name} = {expression};"
            for name, expression in _enum_constants(body)
        )
        source = (
            source[:match.start()]
            + _replacement_with_same_lines(match.group(0), " ".join(declarations))
            + source[match.end():]
        )
        enum_count += 1

    while True:
        match = plain_enum.search(source)
        if match is None:
            break
        tag, body = match.groups()
        enum_tags.add(tag)
        declarations = [f"typedef int {tag};"]
        declarations.extend(
            f"const int {name} = {expression};"
            for name, expression in _enum_constants(body)
        )
        source = (
            source[:match.start()]
            + _replacement_with_same_lines(match.group(0), " ".join(declarations))
            + source[match.end():]
        )
        enum_count += 1

    set_patterns = (
        re.compile(
            r"\btypedef\s+set\s*<\s*([A-Za-z_]\w*)\s*>\s*"
            r"([A-Za-z_]\w*)\s*;",
            re.IGNORECASE,
        ),
        re.compile(
            r"\btypedef\s+set\s+([A-Za-z_]\w*)\s+"
            r"([A-Za-z_]\w*)\s*;",
            re.IGNORECASE,
        ),
    )
    for pattern in set_patterns:
        while True:
            match = pattern.search(source)
            if match is None:
                break
            unused_element_type, alias = match.groups()
            del unused_element_type
            source = (
                source[:match.start()]
                + _replacement_with_same_lines(
                    match.group(0),
                    f"typedef unsigned int {alias};",
                )
                + source[match.end():]
            )
            set_count += 1

    # Nach einer Definition darf der Standardname `enum Tag` weiterverwendet
    # werden. Intern ist Tag jetzt ein normaler typedef-Name.
    for tag in sorted(enum_tags, key=len, reverse=True):
        source = re.sub(
            rf"\benum\s+{re.escape(tag)}\b",
            tag,
            source,
            flags=re.IGNORECASE,
        )

    lowered = PreprocessResult(
        source,
        preprocessed.line_map,
        preprocessed.macros,
        preprocessed.included_files,
        preprocessed.notes,
        preprocessed.warnings,
        preprocessed.linked_assembly_files,
        preprocessed.linked_c_files,
    )
    lowered, array_declarations = _lower_c_array_syntax(lowered)
    return _LoweredCExtensions(
        lowered,
        enum_count,
        set_count,
        array_declarations,
    )


def _parse_c_frontend(
    source: str,
    *,
    filename: str = "<C-Editor>",
    include_paths: Iterable[Path | str] = (),
    predefined_macros: Optional[Mapping[str, str | int | bool]] = None,
    require_main: bool = True,
) -> _FrontendResult:
    try:
        preprocessed = preprocess_c_source(
            source,
            filename=filename,
            include_paths=include_paths,
            predefined_macros=predefined_macros,
        )
    except C64PreprocessorError as exc:
        raise C64CError(
            exc.message,
            exc.line,
            exc.column - 1,
            exc.filename,
            exc.include_stack,
        ) from exc

    lowered = _lower_c_type_extensions(preprocessed)
    preprocessed = lowered.preprocessed

    listener = _RaisingErrorListener(preprocessed)
    lexer = C64CLexer(InputStream(preprocessed.source))
    lexer.removeErrorListeners()
    lexer.addErrorListener(listener)
    parser = C64CParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(listener)
    tree = parser.translationUnit()
    builder = _AstBuilder(
        filename,
        preprocessed,
        require_main=require_main,
        array_declarations=lowered.array_declarations,
    )
    program = builder.visit(tree)
    return _FrontendResult(
        program,
        preprocessed,
        filename,
        len(builder.typedefs),
        len(builder.structures),
        len(builder.prototypes),
        lowered.enum_count,
        lowered.set_count,
        tuple(builder.function_definitions),
        tuple(builder.array_infos),
    )


def parse_c(
    source: str,
    *,
    filename: str = "<C-Editor>",
    include_paths: Iterable[Path | str] = (),
    predefined_macros: Optional[Mapping[str, str | int | bool]] = None,
) -> PascalProgram:
    """Praeprozessiert und parst C; nuetzlich fuer Frontend-Tests."""
    return _parse_c_frontend(
        source,
        filename=filename,
        include_paths=include_paths,
        predefined_macros=predefined_macros,
    ).program



class _CFunctionCodegenMixin:
    """Gemeinsame, rekursionsfeste Codeerzeugung fuer C-Funktionen.

    Parameter und automatische lokale Variablen liegen in einem echten
    Funktions-Stackframe. Nur explizit mit ``static`` deklarierte lokale
    Variablen erhalten dauerhaft reservierten globalen Speicher.
    """

    def _init_c_function_codegen(
        self,
        frontend: _FrontendResult,
        *,
        storage_prefix: str,
        module_mode: bool,
    ) -> None:
        self.c_function_definitions = tuple(frontend.functions)
        self.c_function_states: List[_CFunctionState] = []
        self.current_c_function: Optional[_CFunctionState] = None
        self.c_storage_prefix = storage_prefix
        self.c_module_mode = bool(module_mode)
        self.c_program_end_label: Optional[str] = None

    def _allocate_variable(self, *args, **kwargs):
        variable = super()._allocate_variable(*args, **kwargs)
        prefix = getattr(self, "c_storage_prefix", "")
        if prefix and variable.label.startswith("__pas"):
            variable.label = prefix + variable.label[len("__pas"):]
        return variable

    @staticmethod
    def _stack_variable(
        name: str,
        type_info,
        position: SourcePosition,
        offset: int,
    ) -> _Variable:
        variable = _Variable(
            name,
            f"@cframe:{offset}",
            type_info,
            position,
            True,
        )
        variable.c_stack_offset = int(offset)
        variable.c_storage_kind = "automatic"
        return variable

    @staticmethod
    def _c_stack_slot_size(type_info) -> int:
        # Ein Zwei-Byte-Slot vermeidet ungerade Wortzugriffe auf 68000 und
        # vereinfacht den 6510-Hardwarestack. Byte-Typen belegen ebenfalls 2.
        return max(2, int(type_info.size))

    def _prepare_c_functions(self) -> None:
        self.c_function_states = []
        for definition in self.c_function_definitions:
            routine = self.external_routines.get(self._key(definition.name))
            if routine is None:
                raise self._error(
                    f"Interne C-Funktionssignatur fehlt: {definition.name}.",
                    definition.position,
                )

            names: Set[str] = set()
            parameter_variables: List[_Variable] = []
            parameter_count = len(routine.parameters)
            for index, parameter in enumerate(routine.parameters):
                key = self._key(parameter.name)
                if key in names:
                    raise self._error(
                        f"Parameter mehrfach deklariert: {parameter.name}.",
                        parameter.position,
                    )
                names.add(key)
                parameter_variables.append(
                    self._stack_variable(
                        parameter.name,
                        parameter.type_info,
                        parameter.position,
                        self._c_parameter_offset(parameter_count, index),
                    )
                )

            automatic_variables: List[_Variable] = []
            static_variables: List[_Variable] = []
            local_variables: Dict[str, _Variable] = {}
            frame_size = 0

            for declaration in definition.local_variables:
                local_type = self._resolve_type(
                    declaration.type_name,
                    declaration.position,
                )
                key = self._key(declaration.name)
                if key in names:
                    raise self._error(
                        f"Lokaler Bezeichner mehrfach deklariert: {declaration.name}.",
                        declaration.position,
                    )
                names.add(key)

                if declaration.is_static:
                    variable = self._allocate_variable(
                        declaration.name,
                        local_type,
                        declaration.position,
                        internal=True,
                        label_prefix=f"static_{definition.name}",
                    )
                    initial_value = 0
                    if declaration.initializer is not None:
                        if not isinstance(declaration.initializer, LiteralExpression):
                            raise self._error(
                                "Interner Fehler beim static-Initialisierer.",
                                declaration.position,
                            )
                        initial_value = int(declaration.initializer.value) & 0xFFFF
                    variable.c_initial_value = initial_value
                    variable.c_storage_kind = "static"
                    static_variables.append(variable)
                else:
                    frame_size += self._c_stack_slot_size(local_type)
                    variable = self._stack_variable(
                        declaration.name,
                        local_type,
                        declaration.position,
                        -frame_size,
                    )
                    automatic_variables.append(variable)

                local_variables[key] = variable

            self.c_function_states.append(
                _CFunctionState(
                    definition=definition,
                    return_type=routine.result_type,
                    parameter_variables=tuple(parameter_variables),
                    automatic_variables=tuple(automatic_variables),
                    static_variables=tuple(static_variables),
                    local_variables=local_variables,
                    frame_size=frame_size,
                    end_label=self._new_label(
                        f"return_{self._safe_name(definition.name)}"
                    ),
                )
            )

    def _compile_expr(self, expression: Expression):
        # Die ausgelieferte ANTLR-Grammar besitzt noch keine eigene
        # Shift-Praezedenzebene.  _lower_c_array_syntax() senkt ``<<`` und
        # ``>>`` deshalb auf BinaryExpression("shl"/"shr") ab.  Die
        # eigentliche Maschinen-Codeerzeugung bleibt trotzdem regulaer und
        # zielabhaengig.
        if (
            isinstance(expression, BinaryExpression)
            and expression.operator in {"shl", "shr"}
        ):
            return self._compile_c_shift(expression)
        return super()._compile_expr(expression)

    def _compile_statement(self, statement: Statement) -> None:
        if isinstance(statement, _CForStatement):
            self._compile_c_for_statement(statement)
            return
        super()._compile_statement(statement)

    def _compile_c_for_statement(self, statement: _CForStatement) -> None:
        line = statement.position.line

        for initializer in statement.initializers:
            self._compile_statement(initializer)

        condition_label = self._new_label("c_for_condition")
        update_label = self._new_label("c_for_update")
        end_label = self._new_label("c_for_end")

        self.emitter.emit(f"{condition_label}:", line)
        if statement.condition is not None:
            self._compile_condition_jump_false(
                statement.condition,
                end_label,
            )

        self.break_targets.append(end_label)
        self.continue_targets.append(update_label)
        try:
            self._compile_statement(statement.body)
        finally:
            self.continue_targets.pop()
            self.break_targets.pop()

        self.emitter.emit(f"{update_label}:", line)
        if statement.update is not None:
            self._compile_statement(statement.update)
        self._emit_c_branch(condition_label, line)
        self.emitter.emit(f"{end_label}:", line)

    def _compile_c_return(self, statement: CallStatement) -> bool:
        if statement.name != "__c_return":
            return False

        state = self.current_c_function
        if state is None:
            raise self._error(
                "return ist ausserhalb einer C-Funktion nicht erlaubt.",
                statement.position,
            )

        if state.return_type is None:
            if statement.arguments:
                raise self._error(
                    f"void-Funktion {state.definition.name} darf keinen Wert zurueckgeben.",
                    statement.position,
                )
        else:
            if len(statement.arguments) != 1:
                raise self._error(
                    f"Funktion {state.definition.name} muss einen Wert zurueckgeben.",
                    statement.position,
                )
            result_type = self._compile_expr(statement.arguments[0])
            if not self._types_compatible(state.return_type, result_type):
                raise self._error(
                    f"Rueckgabetyp {result_type.name} passt nicht zu "
                    f"{state.return_type.name}.",
                    statement.position,
                )

        self._emit_c_branch(state.end_label, statement.position.line)
        return True

    def _compile_for(self, statement: ForStatement) -> None:
        variable = self._lookup_variable(statement.name)
        if variable is None:
            raise self._error(
                f"FOR-Variable nicht gefunden: {statement.name}.",
                statement.position,
            )
        line = statement.position.line
        self._compile_assignment(
            AssignmentStatement(
                statement.position,
                statement.name,
                statement.initial,
            )
        )
        condition_label = self._new_label("c_for_condition")
        increment_label = self._new_label("c_for_step")
        end_label = self._new_label("c_for_end")
        self.emitter.emit(f"{condition_label}:", line)
        comparison = BinaryExpression(
            statement.position,
            NameExpression(statement.position, statement.name),
            "<=" if statement.direction == "to" else ">=",
            statement.final,
        )
        self._compile_condition_jump_false(comparison, end_label)
        self.break_targets.append(end_label)
        self.continue_targets.append(increment_label)
        try:
            self._compile_statement(statement.body)
        finally:
            self.continue_targets.pop()
            self.break_targets.pop()
        self.emitter.emit(f"{increment_label}:", line)
        update = BinaryExpression(
            statement.position,
            NameExpression(statement.position, statement.name),
            "+" if statement.direction == "to" else "-",
            LiteralExpression(statement.position, 1),
        )
        self._compile_assignment(
            AssignmentStatement(
                statement.position,
                statement.name,
                update,
            )
        )
        self._emit_c_branch(condition_label, line)
        self.emitter.emit(f"{end_label}:", line)

    def _emit_c_functions(self) -> None:
        for state in self.c_function_states:
            definition = state.definition
            line = definition.position.line
            self.emitter.emit()
            self.emitter.emit(f"; C-Funktion {definition.name}", line)
            self._emit_c_public_symbol(definition)
            self.emitter.emit(f"{definition.symbol}:", line)

            previous_scope = self.scope_variables
            previous_function = self.current_c_function
            self.current_c_function = state
            self.scope_variables = {
                self._key(parameter.names[0]): variable
                for parameter, variable in zip(
                    definition.parameters,
                    state.parameter_variables,
                )
            }
            self.scope_variables.update(state.local_variables)

            try:
                self._emit_c_prologue(state, line)
                for variable in state.automatic_variables:
                    self._emit_c_zero_variable(variable, line)
                self._compile_statement(definition.body)
                if state.return_type is not None:
                    self._emit_c_zero_return(line)
                self.emitter.emit(f"{state.end_label}:", line)
                self._emit_c_epilogue(state, line)
            finally:
                self.scope_variables = previous_scope
                self.current_c_function = previous_function

    def _emit_c_public_symbol(self, definition: _CFunctionDefinition) -> None:
        del definition

    def _emit_c_branch(self, label: str, line: int) -> None:
        raise NotImplementedError

    def _c_parameter_offset(self, count: int, index: int) -> int:
        raise NotImplementedError

    def _emit_c_prologue(self, state: _CFunctionState, line: int) -> None:
        raise NotImplementedError

    def _emit_c_epilogue(self, state: _CFunctionState, line: int) -> None:
        raise NotImplementedError

    def _emit_c_zero_variable(self, variable: _Variable, line: int) -> None:
        raise NotImplementedError

    def _emit_c_zero_return(self, line: int) -> None:
        raise NotImplementedError

    def _compile_c_shift(self, expression: BinaryExpression):
        raise NotImplementedError


class _CCodeGenerator(_CFunctionCodegenMixin, _CodeGenerator):
    def __init__(
        self,
        frontend: _FrontendResult,
        *,
        module_mode: bool = False,
        module_prefix: str = "__c",
    ) -> None:
        super().__init__(frontend.program)
        self.frontend = frontend
        self.c_runtime_prefix = module_prefix
        self._init_c_function_codegen(
            frontend,
            storage_prefix=module_prefix,
            module_mode=module_mode,
        )

    @staticmethod
    def _key(name: str) -> str:
        return name

    def _error(self, message: str, position: SourcePosition) -> C64CError:
        return C64CError(
            message,
            position.line,
            position.column - 1,
            self.frontend.filename,
        )

    def _new_label(self, prefix: str) -> str:
        self.label_counter += 1
        return f"{self.c_runtime_prefix}_{prefix}_{self.label_counter}"

    def _emit_c_branch(self, label: str, line: int) -> None:
        self.emitter.emit(f"    jmp {label}", line)

    def _c_frame_pointer_label(self) -> str:
        return f"{self.c_runtime_prefix}_frame_pointer"

    def _c_parameter_offset(self, count: int, index: int) -> int:
        # +1 altes FP-Byte, +2/+3 Ruecksprungadresse, danach Argumente.
        return 4 + 2 * (count - 1 - index)

    def _emit_c_prologue(self, state: _CFunctionState, line: int) -> None:
        self.emitter.emit(f"    lda {self._c_frame_pointer_label()}", line)
        self.emitter.emit("    pha", line)
        self.emitter.emit("    tsx", line)
        self.emitter.emit(f"    stx {self._c_frame_pointer_label()}", line)
        if state.frame_size:
            self.emitter.emit("    lda #$00", line)
            # Schutzbyte: danach liegen 16-Bit-Slots bei FP-2, FP-4, ...
            self.emitter.emit("    pha", line)
            for _ in range(state.frame_size):
                self.emitter.emit("    pha", line)

    def _emit_c_epilogue(self, state: _CFunctionState, line: int) -> None:
        if state.return_type is not None:
            self.emitter.emit(f"    sta {self.ZP_VALUE_LO}", line)
            self.emitter.emit(f"    stx {self.ZP_VALUE_HI}", line)
        self.emitter.emit(f"    ldx {self._c_frame_pointer_label()}", line)
        self.emitter.emit("    txs", line)
        self.emitter.emit("    pla", line)
        self.emitter.emit(f"    sta {self._c_frame_pointer_label()}", line)
        if state.return_type is not None:
            self.emitter.emit(f"    lda {self.ZP_VALUE_LO}", line)
            self.emitter.emit(f"    ldx {self.ZP_VALUE_HI}", line)
        self.emitter.emit("    rts", line)

    @staticmethod
    def _c_access_offset(access: _StorageAccess) -> Optional[int]:
        label = access.base_label or ""
        if not label.startswith("@cframe:"):
            return None
        return int(label.split(":", 1)[1]) + int(access.constant_offset)

    def _emit_load_access(self, access: _StorageAccess, line: int) -> None:
        offset = self._c_access_offset(access)
        if offset is None:
            return super()._emit_load_access(access, line)
        if access.dynamic is not None or access.use_self:
            raise self._error(
                "Dynamischer Zugriff auf C-Stackvariablen wird nicht unterstuetzt.",
                access.position,
            )
        base = 0x0100 + offset
        self.emitter.emit(f"    ldx {self._c_frame_pointer_label()}", line)
        self.emitter.emit(f"    lda ${base & 0xFFFF:04X},x", line)
        if access.type_info.size == 2:
            self.emitter.emit(f"    sta {self.ZP_VALUE_LO}", line)
            self.emitter.emit(f"    lda ${(base + 1) & 0xFFFF:04X},x", line)
            self.emitter.emit("    tax", line)
            self.emitter.emit(f"    lda {self.ZP_VALUE_LO}", line)
        else:
            self.emitter.emit("    ldx #$00", line)

    def _emit_store_access(self, access: _StorageAccess, line: int) -> None:
        offset = self._c_access_offset(access)
        if offset is None:
            return super()._emit_store_access(access, line)
        if access.dynamic is not None or access.use_self:
            raise self._error(
                "Dynamischer Zugriff auf C-Stackvariablen wird nicht unterstuetzt.",
                access.position,
            )
        base = 0x0100 + offset
        self.emitter.emit(f"    sta {self.ZP_VALUE_LO}", line)
        self.emitter.emit(f"    stx {self.ZP_VALUE_HI}", line)
        self.emitter.emit(f"    ldx {self._c_frame_pointer_label()}", line)
        self.emitter.emit(f"    lda {self.ZP_VALUE_LO}", line)
        self.emitter.emit(f"    sta ${base & 0xFFFF:04X},x", line)
        if access.type_info.size == 2:
            self.emitter.emit(f"    lda {self.ZP_VALUE_HI}", line)
            self.emitter.emit(f"    sta ${(base + 1) & 0xFFFF:04X},x", line)
        self.emitter.emit(f"    lda {self.ZP_VALUE_LO}", line)
        if access.type_info.size == 2:
            self.emitter.emit(f"    ldx {self.ZP_VALUE_HI}", line)
        else:
            self.emitter.emit("    ldx #$00", line)

    def _store_variable(self, variable: _Variable, line: int) -> None:
        """Speichert globale und automatische C-Variablen einheitlich.

        Automatische Variablen tragen intern ein ``@cframe:<offset>``-Label.
        Dieses Label darf niemals in den erzeugten MOS-6510-Assembler
        gelangen, sondern muss ueber ``_emit_store_access`` in einen
        hardware-stackrelativen Zugriff umgesetzt werden.
        """
        self._emit_store_access(
            _StorageAccess(
                variable.type_info,
                variable.position,
                variable.label,
                False,
            ),
            line,
        )

    def _emit_c_zero_variable(self, variable: _Variable, line: int) -> None:
        self.emitter.emit("    lda #$00", line)
        self.emitter.emit("    ldx #$00", line)
        self._store_variable(variable, line)

    def _emit_c_zero_return(self, line: int) -> None:
        self.emitter.emit("    lda #$00", line)
        self.emitter.emit("    ldx #$00", line)

    def _compile_c_shift(self, expression: BinaryExpression):
        line = expression.position.line
        left_type = self._expression_type(expression.left)
        right_type = self._expression_type(expression.right)
        if not left_type.scalar or not right_type.scalar:
            raise self._error(
                "Shift-Operator erwartet skalare Operanden.",
                expression.position,
            )

        # Linken Operand ueber den Hardwarestack sichern, weil die Auswertung
        # des rechten Operanden die gemeinsamen Zero-Page-Arbeitszellen nutzt.
        self._compile_expr(expression.left)
        self.emitter.emit("    pha", line)
        self.emitter.emit("    txa", line)
        self.emitter.emit("    pha", line)
        self._compile_expr(expression.right)
        self.emitter.emit("    tay", line)
        self.emitter.emit("    pla", line)
        self.emitter.emit("    tax", line)
        self.emitter.emit("    pla", line)
        self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
        self.emitter.emit(f"    stx {self.ZP_LEFT_HI}", line)

        loop_label = self._new_label("shift_loop")
        positive_label = self._new_label("shift_positive")
        step_label = self._new_label("shift_step")
        end_label = self._new_label("shift_end")
        self.emitter.emit(f"{loop_label}:", line)
        self.emitter.emit("    cpy #$00", line)
        self.emitter.emit(f"    beq {end_label}", line)

        if expression.operator == "shl":
            self.emitter.emit(f"    asl {self.ZP_LEFT_LO}", line)
            self.emitter.emit(f"    rol {self.ZP_LEFT_HI}", line)
        elif left_type.signed:
            # Arithmetischer Rechtsshift: das Vorzeichenbit wird ueber SEC/ROR
            # wieder in Bit 15 eingeschoben.
            self.emitter.emit(f"    lda {self.ZP_LEFT_HI}", line)
            self.emitter.emit(f"    bpl {positive_label}", line)
            self.emitter.emit("    sec", line)
            self.emitter.emit(f"    ror {self.ZP_LEFT_HI}", line)
            self.emitter.emit(f"    ror {self.ZP_LEFT_LO}", line)
            self.emitter.emit(f"    jmp {step_label}", line)
            self.emitter.emit(f"{positive_label}:", line)
            self.emitter.emit(f"    lsr {self.ZP_LEFT_HI}", line)
            self.emitter.emit(f"    ror {self.ZP_LEFT_LO}", line)
        else:
            self.emitter.emit(f"    lsr {self.ZP_LEFT_HI}", line)
            self.emitter.emit(f"    ror {self.ZP_LEFT_LO}", line)

        self.emitter.emit(f"{step_label}:", line)
        self.emitter.emit("    dey", line)
        self.emitter.emit(f"    jmp {loop_label}", line)
        self.emitter.emit(f"{end_label}:", line)
        self.emitter.emit(f"    lda {self.ZP_LEFT_LO}", line)
        self.emitter.emit(f"    ldx {self.ZP_LEFT_HI}", line)
        return left_type

    def _emit_data(self) -> None:
        super()._emit_data()
        self.emitter.emit()
        self.emitter.emit("; C-Stackframe-Zeiger")
        self.emitter.emit(f"{self._c_frame_pointer_label()}: .byte 0")

    def _compile_external_call_6510(
        self,
        routine,
        arguments: Sequence[Expression],
        position: SourcePosition,
    ):
        self._require_argument_count(
            routine.name,
            arguments,
            len(routine.parameters),
            position,
        )
        line = position.line
        for argument, parameter in zip(arguments, routine.parameters):
            argument_type = self._compile_expr(argument)
            if not argument_type.scalar or not parameter.type_info.scalar:
                raise self._error(
                    "Aggregatparameter werden fuer externe C-Routinen noch nicht unterstuetzt.",
                    argument.position,
                )
            if not self._types_compatible(parameter.type_info, argument_type):
                raise self._error(
                    f"Argumenttyp {argument_type.name} passt nicht zu "
                    f"{parameter.type_info.name}.",
                    argument.position,
                )
            self.emitter.emit(f"    sta {self.ZP_VALUE_LO}", line)
            self.emitter.emit("    txa", line)
            self.emitter.emit("    pha", line)
            self.emitter.emit(f"    lda {self.ZP_VALUE_LO}", line)
            self.emitter.emit("    pha", line)

        self.emitter.emit(f"    jsr {routine.symbol}", line)
        stack_bytes = len(arguments) * 2
        if stack_bytes:
            # Rückgabewert sichern, bevor der Hardware-Stack bereinigt wird.
            self.emitter.emit(f"    sta {self.ZP_VALUE_LO}", line)
            self.emitter.emit(f"    stx {self.ZP_VALUE_HI}", line)
            self.emitter.emit("    tsx", line)
            self.emitter.emit("    txa", line)
            self.emitter.emit("    clc", line)
            self.emitter.emit(f"    adc #${stack_bytes:02X}", line)
            self.emitter.emit("    tax", line)
            self.emitter.emit("    txs", line)
            self.emitter.emit(f"    lda {self.ZP_VALUE_LO}", line)
            self.emitter.emit(f"    ldx {self.ZP_VALUE_HI}", line)
        return routine.result_type

    # Diese Namen werden vom MOS-6510-Backend selbst abgesenkt. Ihre
    # Deklarationen in den System-Headern sind Typinformationen und duerfen
    # nicht dazu fuehren, dass ein externes Symbol wie ``clrscr`` erzeugt wird.
    _C64_BUILTIN_FUNCTIONS = frozenset({
        "peek",
        "chr",
        "ord",
        "lo",
        "hi",
    })
    _C64_BUILTIN_PROCEDURES = frozenset({
        "write",
        "writeln",
        "clrscr",
        "poke",
        "inc",
        "dec",
        "halt",
        "settextcolor",
    })

    def _compile_function(self, expression: CallExpression):
        name = self._key(expression.name)

        # Builtins muessen vor den aus Header-Prototypen aufgebauten externen
        # Routinen behandelt werden. Sonst wird z. B. ``peek`` zu
        # ``jsr peek`` statt zum direkten Speicherzugriff.
        if name in self._C64_BUILTIN_FUNCTIONS:
            return super()._compile_function(expression)

        routine = self.external_routines.get(name)
        if routine is not None:
            if routine.result_type is None:
                raise self._error(
                    f"{routine.name} ist keine Funktion.",
                    expression.position,
                )
            return self._compile_external_call_6510(
                routine,
                expression.arguments,
                expression.position,
            )
        return super()._compile_function(expression)

    def _compile_call_statement(self, statement: CallStatement) -> None:
        if self._compile_c_return(statement):
            return

        name = self._key(statement.name)

        # Der alte Amiga-Headername bleibt bewusst plattformspezifisch.
        # Die gemeinsame API fuer beide Ziele lautet SetTextColor().
        if name == "amiga_set_text_color":
            raise self._error(
                "amiga_set_text_color ist eine Amiga-spezifische Anweisung.",
                statement.position,
            )

        # Systemfunktionen aus c64.h/stdio.h werden vom Backend direkt
        # umgesetzt. Der Prototyp dient nur der C-Typpruefung.
        if name in self._C64_BUILTIN_PROCEDURES:
            super()._compile_call_statement(statement)
            return

        routine = self.external_routines.get(name)
        if routine is not None:
            if routine.result_type is not None:
                raise self._error(
                    f"{routine.name} ist eine Funktion und muss in einem Ausdruck verwendet werden.",
                    statement.position,
                )
            self._compile_external_call_6510(
                routine,
                statement.arguments,
                statement.position,
            )
            return
        super()._compile_call_statement(statement)

    def generate(self) -> GeneratedAssembly:
        self._prepare_symbols()
        self._prepare_c_functions()
        source_line = self.program.body.position.line

        if self.c_module_mode:
            self.emitter.emit("; Separat kompiliertes C-Modul fuer MOS 6510")
            self.emitter.emit(f"; Quelldatei: {self.frontend.filename}")
            self._emit_c_functions()
            self._emit_runtime()
            self._emit_data()
            self.emitter.emit("end")
        else:
            self.c_program_end_label = "__c_program_end"
            self.emitter.emit("; Von C64 C erzeugter MOS-6510-Assembler")
            self.emitter.emit(f"; Programm: {self.program.name}")
            self.emitter.emit(".org $080D")
            self.emitter.emit(".entry __c_start")
            self.emitter.emit(".basic")
            self.emitter.emit()
            self.emitter.emit("__c_start:", source_line)
            self.emitter.emit("    lda #$0E", source_line)
            self.emitter.emit("    jsr $FFD2", source_line)
            for variable, initializer in self.initializers:
                result_type = self._compile_expr(initializer)
                if result_type == STRING_TYPE:
                    raise self._error(
                        "C-Stringvariablen folgen in einer spaeteren Stufe.",
                        initializer.position,
                    )
                self._store_variable(variable, initializer.position.line)
            main_state = next(
                state
                for state in self.c_function_states
                if state.definition.name == "main"
            )
            self.emitter.emit(f"    jsr {main_state.definition.symbol}", source_line)
            self.emitter.emit("__c_program_end:", source_line)
            graphics_runtime_linked = any(
                Path(filename).name.casefold() == "graphics_c64.asm"
                for filename in self.frontend.preprocessed.linked_assembly_files
            )
            if graphics_runtime_linked:
                # Ein C64-Grafikprogramm darf nach main nicht zu BASIC
                # zurueckkehren. Der KERNAL-Texteditor arbeitet sonst weiter
                # im Hintergrund, waehrend der VIC-II die Bitmap anzeigt.
                self.emitter.emit("    jmp __c_program_end", source_line)
            else:
                self.emitter.emit("    rts", source_line)
            self._emit_c_functions()
            self._emit_runtime()
            self._emit_data()

        assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
        assembly = assembly.replace("__pascal_start", f"{self.c_runtime_prefix}_start")
        assembly = assembly.replace("__pas", self.c_runtime_prefix)
        assembly = assembly.replace("Pascal-Variablen", "C-Variablen")
        if "@cframe:" in assembly:
            raise self._error(
                "Interne C-Stackframe-Markierung ist in den erzeugten "
                "Assembler gelangt.",
                self.program.body.position,
            )
        return GeneratedAssembly(
            program_name=self.program.name,
            assembly=assembly,
            source_map=dict(self.emitter.source_map),
            variable_count=sum(
                not variable.internal for variable in self.variable_order
            ),
            string_count=len(self.strings),
            included_files=self.frontend.preprocessed.included_files,
            macros=tuple(sorted(self.frontend.preprocessed.macros)),
            notes=self.frontend.preprocessed.notes,
            warnings=self.frontend.preprocessed.warnings,
            typedef_count=self.frontend.typedef_count,
            structure_count=self.frontend.structure_count,
            prototype_count=self.frontend.prototype_count,
            enum_count=self.frontend.enum_count,
            set_count=self.frontend.set_count,
            linked_assembly_files=(),
            linked_c_files=(),
        )


class _AmigaCCodeGenerator(_CFunctionCodegenMixin, _AmigaCodeGenerator):
    """C-Frontend fuer das eigenstaendige Motorola-68000-Backend."""

    def __init__(
        self,
        frontend: _FrontendResult,
        *,
        module_mode: bool = False,
        module_prefix: str = "__c",
    ) -> None:
        super().__init__(
            frontend.program,
            symbol_prefix=module_prefix,
            language_name="C",
        )
        self.frontend = frontend
        self._init_c_function_codegen(
            frontend,
            storage_prefix=module_prefix,
            module_mode=module_mode,
        )

    @staticmethod
    def _key(name: str) -> str:
        return name

    def _error(self, message: str, position: SourcePosition) -> C64CError:
        return C64CError(
            message,
            position.line,
            position.column - 1,
            self.frontend.filename,
        )

    def _new_label(self, prefix: str) -> str:
        self.label_counter += 1
        return f"{self.symbol_prefix}_{prefix}_{self.label_counter}"

    def _emit_c_public_symbol(self, definition: _CFunctionDefinition) -> None:
        if not definition.is_static:
            self.emitter.emit(f"xdef {definition.symbol}")

    def _emit_c_branch(self, label: str, line: int) -> None:
        self.emitter.emit(f"    bra {label}", line)

    def _c_parameter_offset(self, count: int, index: int) -> int:
        # 0(a6)=altes a6, 4(a6)=Ruecksprungadresse, danach Argumente.
        return 8 + 2 * (count - 1 - index)

    def _emit_c_prologue(self, state: _CFunctionState, line: int) -> None:
        self.emitter.emit("    move.l a6,-(sp)", line)
        self.emitter.emit("    move.l sp,a6", line)
        if state.frame_size:
            self.emitter.emit(
                f"    suba.w #${state.frame_size & 0xFFFF:04X},sp",
                line,
            )

    def _emit_c_epilogue(self, state: _CFunctionState, line: int) -> None:
        del state
        self.emitter.emit("    move.l a6,sp", line)
        self.emitter.emit("    move.l (sp)+,a6", line)
        self.emitter.emit("    rts", line)

    def _emit_address(self, access: _StorageAccess, line: int) -> None:
        label = access.base_label or ""
        if label.startswith("@cframe:"):
            if access.dynamic is not None or access.use_self:
                raise self._error(
                    "Dynamischer Zugriff auf C-Stackvariablen wird nicht unterstuetzt.",
                    access.position,
                )
            offset = (
                int(label.split(":", 1)[1])
                + int(access.constant_offset)
            )
            self.emitter.emit(f"    lea {offset}(a6),a0", line)
            return
        super()._emit_address(access, line)

    def _emit_c_zero_variable(self, variable: _Variable, line: int) -> None:
        self.emitter.emit("    moveq #0,d0", line)
        self._store_variable(variable, line)

    def _emit_c_zero_return(self, line: int) -> None:
        self.emitter.emit("    moveq #0,d0", line)

    def _compile_c_shift(self, expression: BinaryExpression):
        line = expression.position.line
        left_type = self._expression_type(expression.left)
        right_type = self._expression_type(expression.right)
        if not left_type.scalar or not right_type.scalar:
            raise self._error(
                "Shift-Operator erwartet skalare Operanden.",
                expression.position,
            )

        self._compile_expr(expression.left)
        self.emitter.emit("    move.w d0,-(sp)", line)
        self._compile_expr(expression.right)
        self.emitter.emit("    move.w d0,d1", line)
        self.emitter.emit("    move.w (sp)+,d0", line)

        if expression.operator == "shl":
            instruction = "lsl.w"
        elif left_type.signed:
            instruction = "asr.w"
        else:
            instruction = "lsr.w"
        self.emitter.emit(f"    {instruction} d1,d0", line)
        return left_type

    def _compile_call_statement(self, statement: CallStatement) -> None:
        if self._compile_c_return(statement):
            return
        super()._compile_call_statement(statement)

    def generate(self) -> GeneratedAssembly:
        self._prepare_symbols()
        self._prepare_c_functions()
        source_line = self.program.body.position.line

        if self.c_module_mode:
            self.emitter.emit("; Separat kompiliertes C-Modul fuer Motorola 68000")
            self.emitter.emit(f"; Quelldatei: {self.frontend.filename}")
            self.emitter.emit("section code,code")
            self._emit_c_functions()
            self._emit_runtime()
            self._emit_data()
            self.emitter.emit("end")
        else:
            self.c_program_end_label = f"{self.symbol_prefix}_program_end"
            self.emitter.emit("; Von C erzeugter Motorola-68000-Assembler")
            self.emitter.emit("; Ziel: Commodore Amiga 500 / Standalone-Boot-ADF")
            self.emitter.emit("; Runtime: direkte OCS-Register, keine Workbench-Libraries")
            self.emitter.emit(f"; Programm: {self.program.name}")
            self.emitter.emit(".bootable")
            self.emitter.emit("section code,code")
            self.emitter.emit("xdef _start")
            self.emitter.emit("_start:", source_line)
            self.emitter.emit("    move.l #$0007FFFC,sp", source_line)
            self.emitter.emit(
                f"    bsr {self.symbol_prefix}_screen_init",
                source_line,
            )

            for variable, initializer in self.initializers:
                result_type = self._compile_expr(initializer)
                if result_type == STRING_TYPE:
                    raise self._error(
                        "C-Stringvariablen werden noch nicht unterstuetzt.",
                        initializer.position,
                    )
                if not variable.type_info.scalar:
                    raise self._error(
                        "Aggregate koennen nicht direkt initialisiert werden.",
                        initializer.position,
                    )
                if not self._types_compatible(variable.type_info, result_type):
                    raise self._error(
                        f"Initialisierung von {variable.name} besitzt den falschen Typ.",
                        initializer.position,
                    )
                self._store_variable(variable, initializer.position.line)

            main_state = next(
                state
                for state in self.c_function_states
                if state.definition.name == "main"
            )
            self.emitter.emit(
                f"    bsr {main_state.definition.symbol}",
                source_line,
            )
            self.emitter.emit(
                f"    bra {self.c_program_end_label}",
                source_line,
            )
            self._emit_c_functions()
            self._emit_runtime()
            self.emitter.emit()
            self.emitter.emit(f"{self.c_program_end_label}:", source_line)
            self.emitter.emit(
                f"    bra {self.c_program_end_label}",
                source_line,
            )
            self._emit_data()
            self.emitter.emit("end")

        assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
        return GeneratedAssembly(
            program_name=self.program.name,
            assembly=assembly,
            source_map=dict(self.emitter.source_map),
            variable_count=sum(
                not variable.internal for variable in self.variable_order
            ),
            string_count=len(self.strings),
            included_files=self.frontend.preprocessed.included_files,
            macros=tuple(sorted(self.frontend.preprocessed.macros)),
            notes=self.frontend.preprocessed.notes,
            warnings=self.frontend.preprocessed.warnings,
            typedef_count=self.frontend.typedef_count,
            structure_count=self.frontend.structure_count,
            prototype_count=self.frontend.prototype_count,
            enum_count=self.frontend.enum_count,
            set_count=self.frontend.set_count,
            linked_assembly_files=(),
            linked_c_files=(),
        )


class _PE32CCodeGenerator(_CFunctionCodegenMixin, _PE32CodeGenerator):
    """C-Frontend fuer das integrierte IA-32-/Windows-PE32-Backend."""

    def __init__(self, frontend: _FrontendResult, *, module_mode: bool = False, module_prefix: str = "__c", graphics_backend: str = "Direct2D", console_mode: bool = True) -> None:
        super().__init__(frontend.program, symbol_prefix=module_prefix, language_name="C", graphics_backend=graphics_backend, console_mode=console_mode)
        self.frontend = frontend
        self._init_c_function_codegen(frontend, storage_prefix=module_prefix, module_mode=module_mode)

    @staticmethod
    def _key(name: str) -> str:
        return name

    def _error(self, message: str, position: SourcePosition) -> C64CError:
        return C64CError(message, position.line, position.column - 1, self.frontend.filename)

    def _new_label(self, prefix: str) -> str:
        self.label_counter += 1
        return f"{self.symbol_prefix}_{prefix}_{self.label_counter}"

    def _emit_c_public_symbol(self, definition: _CFunctionDefinition) -> None:
        if not definition.is_static:
            self.emitter.emit(f"global {definition.symbol}")

    def _emit_c_branch(self, label: str, line: int) -> None:
        self.emitter.emit(f"    jmp {label}", line)

    def _c_parameter_offset(self, count: int, index: int) -> int:
        del count
        return 8 + 4 * index

    @staticmethod
    def _c_stack_slot_size(type_info) -> int:
        return max(4, int(type_info.size))

    def _emit_c_prologue(self, state: _CFunctionState, line: int) -> None:
        self.emitter.emit("    push ebp", line)
        self.emitter.emit("    mov ebp, esp", line)
        if state.frame_size:
            self.emitter.emit(f"    sub esp, {state.frame_size}", line)

    def _emit_c_epilogue(self, state: _CFunctionState, line: int) -> None:
        del state
        self.emitter.emit("    mov esp, ebp", line)
        self.emitter.emit("    pop ebp", line)
        self.emitter.emit("    ret", line)

    def _emit_address(self, access: _StorageAccess, line: int) -> None:
        label = access.base_label or ""
        if label.startswith("@cframe:"):
            if access.dynamic is not None or access.use_self:
                raise self._error("Dynamischer Zugriff auf C-Stackvariablen wird noch nicht unterstuetzt.", access.position)
            offset = int(label.split(":", 1)[1]) + int(access.constant_offset)
            self.emitter.emit("    mov ecx, ebp", line)
            if offset:
                self.emitter.emit(f"    add ecx, {offset}", line)
            return
        super()._emit_address(access, line)

    def _emit_c_zero_variable(self, variable: _Variable, line: int) -> None:
        self.emitter.emit("    xor eax, eax", line)
        self._store_variable(variable, line)

    def _emit_c_zero_return(self, line: int) -> None:
        self.emitter.emit("    xor eax, eax", line)

    def _compile_c_shift(self, expression: BinaryExpression):
        line = expression.position.line
        left_type = self._expression_type(expression.left)
        right_type = self._expression_type(expression.right)
        if not left_type.scalar or not right_type.scalar:
            raise self._error("Shift-Operator erwartet skalare Operanden.", expression.position)
        self._compile_expr(expression.left)
        self.emitter.emit("    push eax", line)
        self._compile_expr(expression.right)
        self.emitter.emit("    mov ecx, eax", line)
        self.emitter.emit("    pop eax", line)
        instruction = "shl" if expression.operator == "shl" else ("sar" if left_type.signed else "shr")
        self.emitter.emit(f"    {instruction} eax, cl", line)
        return left_type

    def _compile_call_statement(self, statement: CallStatement) -> None:
        if self._compile_c_return(statement):
            return
        super()._compile_call_statement(statement)

    def generate(self) -> GeneratedAssembly:
        self._prepare_symbols(); self._prepare_c_functions()
        source_line = self.program.body.position.line
        if self.c_module_mode:
            self.emitter.emit("; Separat kompiliertes C-Modul fuer Windows PE32")
            self.emitter.emit(f"; Quelldatei: {self.frontend.filename}")
            self.emitter.emit("bits 32")
            self._emit_c_functions(); self._emit_runtime(); self._emit_data()
        else:
            self.emitter.emit("; Von C erzeugter IA-32-Assembler")
            self.emitter.emit("; Ziel: Windows PE32")
            self.emitter.emit(f"; Grafikbackend: {self.graphics_backend}")
            self.emitter.emit(f"; Programm: {self.program.name}")
            self.emitter.emit("bits 32"); self.emitter.emit("global _start"); self.emitter.emit("entry _start")
            for symbol in (
                "ExitProcess", "AllocConsole", "GetStdHandle",
                "SetConsoleScreenBufferSize", "SetConsoleWindowInfo",
                "GetConsoleMode", "SetConsoleMode", "WriteFile", "lstrlenA",
                "wsprintfA",
            ):
                self.emitter.emit(f"extern {symbol}")
            self.emitter.emit("_start:", source_line)
            if self.console_mode:
                self.emitter.emit(f"    call {self.symbol_prefix}_console_init", source_line)
            for variable, initializer in self.initializers:
                result_type = self._compile_expr(initializer)
                if result_type == STRING_TYPE:
                    raise self._error("C-Stringvariablen werden im PE32-Backend noch nicht unterstuetzt.", initializer.position)
                if not variable.type_info.scalar:
                    raise self._error("Aggregate koennen nicht direkt initialisiert werden.", initializer.position)
                if not self._types_compatible(variable.type_info, result_type):
                    raise self._error(f"Initialisierung von {variable.name} besitzt den falschen Typ.", initializer.position)
                self._store_variable(variable, initializer.position.line)
            main_state = next(state for state in self.c_function_states if state.definition.name == "main")
            self.emitter.emit(f"    call {main_state.definition.symbol}", source_line)
            self.emitter.emit("    push eax", source_line)
            self.emitter.emit("    call ExitProcess", source_line)
            self._emit_c_functions(); self._emit_runtime(); self._emit_data()
        assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
        return GeneratedAssembly(
            program_name=self.program.name,
            assembly=assembly,
            source_map=dict(self.emitter.source_map),
            variable_count=sum(not variable.internal for variable in self.variable_order),
            string_count=len(self.strings),
            included_files=self.frontend.preprocessed.included_files,
            macros=tuple(sorted(self.frontend.preprocessed.macros)),
            notes=self.frontend.preprocessed.notes,
            warnings=self.frontend.preprocessed.warnings,
            typedef_count=self.frontend.typedef_count,
            structure_count=self.frontend.structure_count,
            prototype_count=self.frontend.prototype_count,
            enum_count=self.frontend.enum_count,
            set_count=self.frontend.set_count,
            linked_assembly_files=(),
            linked_c_files=(),
        )


def _link_c_assembly_modules(
    generated: GeneratedAssembly,
    assembly_files: Sequence[str],
) -> GeneratedAssembly:
    if not assembly_files:
        return generated

    if "Windows PE32" in generated.assembly or "C-Modul fuer Windows PE32" in generated.assembly:
        linked = []
        for filename in assembly_files:
            path = Path(filename).expanduser().resolve()
            if not path.is_file():
                raise C64CError(f"C-Assembler-Modul nicht gefunden: {path}")
            linked.append(str(path))
        return GeneratedAssembly(
            program_name=generated.program_name,
            assembly=generated.assembly,
            source_map=generated.source_map,
            variable_count=generated.variable_count,
            string_count=generated.string_count,
            included_files=generated.included_files,
            macros=generated.macros,
            notes=generated.notes,
            warnings=generated.warnings,
            typedef_count=generated.typedef_count,
            structure_count=generated.structure_count,
            prototype_count=generated.prototype_count,
            enum_count=generated.enum_count,
            set_count=generated.set_count,
            linked_assembly_files=tuple(linked),
            linked_c_files=generated.linked_c_files,
            linked_pe32_modules=generated.linked_pe32_modules,
        )

    main_lines = generated.assembly.rstrip().splitlines()
    if main_lines and main_lines[-1].strip().casefold() == "end":
        main_lines.pop()
    output = ["\n".join(main_lines).rstrip()]
    linked: List[str] = []

    for filename in assembly_files:
        path = Path(filename).expanduser().resolve()
        try:
            module_source = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            raise C64CError(
                f"C-Assembler-Modul kann nicht gelesen werden: {path}: {exc}"
            ) from exc
        module_lines = module_source.rstrip().splitlines()
        if module_lines and module_lines[-1].strip().casefold() == "end":
            module_lines.pop()
        output.append(
            f"; --- statisch gelinktes C-Modul: {path.name} ---\n"
            + "\n".join(module_lines).rstrip()
        )
        linked.append(str(path))

    if "Ziel: Windows PE32" not in generated.assembly and "C-Modul fuer Windows PE32" not in generated.assembly:
        output.append("end")
    return GeneratedAssembly(
        program_name=generated.program_name,
        assembly="\n\n".join(output).rstrip() + "\n",
        source_map=generated.source_map,
        variable_count=generated.variable_count,
        string_count=generated.string_count,
        included_files=generated.included_files,
        macros=generated.macros,
        notes=generated.notes,
        warnings=generated.warnings,
        typedef_count=generated.typedef_count,
        structure_count=generated.structure_count,
        prototype_count=generated.prototype_count,
        enum_count=generated.enum_count,
        set_count=generated.set_count,
        linked_assembly_files=tuple(linked),
        linked_c_files=generated.linked_c_files,
        linked_pe32_modules=generated.linked_pe32_modules,
    )



def _c_module_prefix(path: Path) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", path.stem) or "module"
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:8]
    return f"__cmod_{safe}_{digest}"


def _compile_linked_c_modules(
    filenames: Sequence[str],
    *,
    include_paths: Iterable[Path | str],
    predefined_macros: Mapping[str, str | int | bool],
    normalized_target: str,
    initially_defined_symbols: Iterable[str] = (),
) -> Tuple[List[Tuple[str, str]], List[str]]:
    modules: List[Tuple[str, str]] = []
    assembly_files: List[str] = []
    completed: Set[Path] = set()
    visiting: List[Path] = []
    public_symbols: Dict[str, Path] = {
        str(name): Path("<main>") for name in initially_defined_symbols
    }

    def visit(filename: str, parent: Optional[Path] = None) -> None:
        path = Path(filename).expanduser().resolve()
        if parent is not None and path == parent:
            # Typischer Fall: modul.c inkludiert seinen Header, und der Header
            # enthält erneut #pragma link "modul.c".
            return
        if path in completed:
            return
        if path in visiting:
            cycle = " -> ".join(str(item) for item in visiting + [path])
            raise C64CError(f"Zyklischer #pragma-link: {cycle}")
        if not path.is_file():
            raise C64CError(f"Verlinkte C-Datei nicht gefunden: {path}")

        visiting.append(path)
        try:
            try:
                module_source = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError) as exc:
                raise C64CError(
                    f"Verlinkte C-Datei kann nicht gelesen werden: {path}: {exc}"
                ) from exc

            frontend = _parse_c_frontend(
                module_source,
                filename=str(path),
                include_paths=include_paths,
                predefined_macros=predefined_macros,
                require_main=False,
            )

            for dependency in frontend.preprocessed.linked_c_files:
                visit(dependency, path)

            for definition in frontend.functions:
                if definition.is_static:
                    continue
                previous = public_symbols.get(definition.symbol)
                if previous is not None:
                    raise C64CError(
                        f"C-Linkersymbol mehrfach definiert: {definition.symbol} "
                        f"in {previous} und {path}."
                    )
                public_symbols[definition.symbol] = path

            prefix = _c_module_prefix(path)
            if normalized_target in {"c64", "c-64", "6510"}:
                generated = _CCodeGenerator(
                    frontend,
                    module_mode=True,
                    module_prefix=prefix,
                ).generate()
            elif normalized_target in {"amiga", "amiga500", "a500", "m68k", "68000"}:
                generated = _AmigaCCodeGenerator(
                    frontend,
                    module_mode=True,
                    module_prefix=prefix,
                ).generate()
            elif normalized_target in {"pe32", "win32", "windows", "windows-pe32"}:
                generated = _PE32CCodeGenerator(
                    frontend,
                    module_mode=True,
                    module_prefix=prefix,
                    console_mode=False,
                ).generate()
            else:
                raise C64CError(f"Unbekanntes Compilerziel: {normalized_target}.")

            modules.append((str(path), generated.assembly))
            for asm_file in frontend.preprocessed.linked_assembly_files:
                if asm_file not in assembly_files:
                    assembly_files.append(asm_file)
            completed.add(path)
        finally:
            visiting.pop()

    for filename in filenames:
        visit(filename)
    return modules, assembly_files


def _link_c_source_modules(
    generated: GeneratedAssembly,
    modules: Sequence[Tuple[str, str]],
) -> GeneratedAssembly:
    if not modules:
        return generated

    if "Windows PE32" in generated.assembly:
        # PE32-Translation-Units bleiben getrennt. d64_dism.py assembliert
        # Hauptdatei und jedes #pragma-link-Modul einzeln zu COFF32.
        return GeneratedAssembly(
            program_name=generated.program_name,
            assembly=generated.assembly,
            source_map=generated.source_map,
            variable_count=generated.variable_count,
            string_count=generated.string_count,
            included_files=generated.included_files,
            macros=generated.macros,
            notes=generated.notes,
            warnings=generated.warnings,
            typedef_count=generated.typedef_count,
            structure_count=generated.structure_count,
            prototype_count=generated.prototype_count,
            enum_count=generated.enum_count,
            set_count=generated.set_count,
            linked_assembly_files=generated.linked_assembly_files,
            linked_c_files=tuple(str(Path(name).resolve()) for name, _asm in modules),
            linked_pe32_modules=tuple((str(name), str(asm)) for name, asm in modules),
        )

    main_lines = generated.assembly.rstrip().splitlines()
    if main_lines and main_lines[-1].strip().casefold() == "end":
        main_lines.pop()
    output = ["\n".join(main_lines).rstrip()]
    linked: List[str] = []

    for filename, module_source in modules:
        module_lines = module_source.rstrip().splitlines()
        if module_lines and module_lines[-1].strip().casefold() == "end":
            module_lines.pop()
        output.append(
            f"; --- separat kompiliertes C-Modul: {Path(filename).name} ---\n"
            + "\n".join(module_lines).rstrip()
        )
        linked.append(str(Path(filename).resolve()))

    if "Ziel: Windows PE32" not in generated.assembly and "C-Modul fuer Windows PE32" not in generated.assembly:
        output.append("end")
    return GeneratedAssembly(
        program_name=generated.program_name,
        assembly="\n\n".join(output).rstrip() + "\n",
        source_map=generated.source_map,
        variable_count=generated.variable_count,
        string_count=generated.string_count,
        included_files=generated.included_files,
        macros=generated.macros,
        notes=generated.notes,
        warnings=generated.warnings,
        typedef_count=generated.typedef_count,
        structure_count=generated.structure_count,
        prototype_count=generated.prototype_count,
        enum_count=generated.enum_count,
        set_count=generated.set_count,
        linked_assembly_files=generated.linked_assembly_files,
        linked_c_files=tuple(linked),
        linked_pe32_modules=generated.linked_pe32_modules,
    )


def compile_c_module_to_assembly(
    source: str,
    *,
    filename: str = "<C-Modul>",
    include_paths: Iterable[Path | str] = (),
    predefined_macros: Optional[Mapping[str, str | int | bool]] = None,
    target: str = "c64",
    module_prefix: Optional[str] = None,
    cpu_model: str = "mk68000",
    fpu_model: str = "FPU: None",
    graphics_backend: str = "Direct2D",
    windows_application_mode: str | None = None,
) -> GeneratedAssembly:
    """Kompiliert eine C-Translation-Unit ohne erforderliche main()-Funktion.

    Die Funktion wird vom Pascal-Unit-Linker verwendet, um getrennte
    Zielimplementierungen wie ``System.Graphics.c64.c`` regulär mit dem
    C-Frontend zu übersetzen. Auch deren ``#pragma link``-Abhängigkeiten
    werden als eigenständige C-Module kompiliert und statisch angefügt.
    """
    normalized_target = str(target).strip().casefold()
    del cpu_model, fpu_model
    target_macros = dict(predefined_macros or {})
    if normalized_target in {"c64", "c-64", "6510"}:
        target_macros.setdefault("__D64_TARGET_C64__", 1)
    elif normalized_target in {"amiga", "amiga500", "a500", "m68k", "68000"}:
        target_macros.setdefault("__D64_TARGET_AMIGA__", 1)
    elif normalized_target in {"pe32", "win32", "windows", "windows-pe32"}:
        target_macros.setdefault("__D64_TARGET_PE32__", 1)
        selected_mode = str(windows_application_mode or "").strip().casefold()
        if not selected_mode:
            if "__D64_WINDOWS_CONSOLE__" in target_macros:
                selected_mode = "console"
            elif "__D64_WINDOWS_GUI__" in target_macros:
                selected_mode = "gui"
        if selected_mode in {"console", "konsole"}:
            target_macros.setdefault("__D64_WINDOWS_CONSOLE__", 1)
        elif selected_mode:
            target_macros.setdefault("__D64_WINDOWS_GUI__", 1)
        if selected_mode in {"direct3d", "d3d", "d3d9"}:
            graphics_backend = "Direct3D"
        elif selected_mode in {"direct2d", "d2d"}:
            graphics_backend = "Direct2D"
        if selected_mode in {"direct2d", "d2d", "direct3d", "d3d", "d3d9"} or windows_application_mode is None:
            target_macros.setdefault("__D64_GRAPHICS_WINDOWS__", 1)
            target_macros.setdefault(
                "__D64_GRAPHICS_DIRECT3D__"
                if str(graphics_backend).casefold().startswith("direct3")
                else "__D64_GRAPHICS_DIRECT2D__",
                1,
            )
    else:
        raise C64CError(
            f"Unbekanntes Compilerziel: {target}.",
            filename=filename,
        )

    frontend = _parse_c_frontend(
        source,
        filename=filename,
        include_paths=include_paths,
        predefined_macros=target_macros,
        require_main=False,
    )
    prefix = module_prefix or _c_module_prefix(Path(filename))

    try:
        if normalized_target in {"c64", "c-64", "6510"}:
            generated = _CCodeGenerator(frontend, module_mode=True, module_prefix=prefix).generate()
        elif normalized_target in {"amiga", "amiga500", "a500", "m68k", "68000"}:
            generated = _AmigaCCodeGenerator(frontend, module_mode=True, module_prefix=prefix).generate()
        else:
            generated = _PE32CCodeGenerator(frontend, module_mode=True, module_prefix=prefix, graphics_backend=graphics_backend, console_mode=False).generate()

        public_symbols = (
            definition.symbol
            for definition in frontend.functions
            if not definition.is_static
        )
        c_modules, module_assembly_files = _compile_linked_c_modules(
            frontend.preprocessed.linked_c_files,
            include_paths=include_paths,
            predefined_macros=target_macros,
            normalized_target=normalized_target,
            initially_defined_symbols=public_symbols,
        )
        generated = _link_c_source_modules(generated, c_modules)

        assembly_files: List[str] = []
        for asm_file in (
            *frontend.preprocessed.linked_assembly_files,
            *module_assembly_files,
        ):
            if asm_file not in assembly_files:
                assembly_files.append(asm_file)
        return _link_c_assembly_modules(generated, assembly_files)
    except C64CError:
        raise
    except Exception as exc:
        line = getattr(exc, "line", None)
        column = getattr(exc, "column", None)
        message = getattr(exc, "message", str(exc))
        raise C64CError(
            message,
            line,
            (column - 1) if column else None,
            filename,
        ) from exc


def compile_c_to_assembly(
    source: str,
    *,
    filename: str = "<C-Editor>",
    include_paths: Iterable[Path | str] = (),
    predefined_macros: Optional[Mapping[str, str | int | bool]] = None,
    target: str = "c64",
    cpu_model: str = "mk68000",
    fpu_model: str = "FPU: None",
    graphics_backend: str = "Direct2D",
    windows_application_mode: str | None = None,
) -> GeneratedAssembly:
    """Praeprozessiert C und erzeugt 6510-, Motorola-680x0- oder IA-32-/PE32-Assembler."""
    normalized_target = str(target).strip().casefold()
    del cpu_model, fpu_model
    target_macros = dict(predefined_macros or {})
    if normalized_target in {"c64", "c-64", "6510"}:
        target_macros.setdefault("__D64_TARGET_C64__", 1)
    elif normalized_target in {"amiga", "amiga500", "a500", "m68k", "68000"}:
        target_macros.setdefault("__D64_TARGET_AMIGA__", 1)
    elif normalized_target in {"pe32", "win32", "windows", "windows-pe32"}:
        target_macros.setdefault("__D64_TARGET_PE32__", 1)
        selected_mode = str(windows_application_mode or "").strip().casefold()
        if not selected_mode:
            if "__D64_WINDOWS_CONSOLE__" in target_macros:
                selected_mode = "console"
            elif "__D64_WINDOWS_GUI__" in target_macros:
                selected_mode = "gui"
        if selected_mode in {"console", "konsole"}:
            target_macros.setdefault("__D64_WINDOWS_CONSOLE__", 1)
        elif selected_mode:
            target_macros.setdefault("__D64_WINDOWS_GUI__", 1)
        if selected_mode in {"direct3d", "d3d", "d3d9"}:
            graphics_backend = "Direct3D"
        elif selected_mode in {"direct2d", "d2d"}:
            graphics_backend = "Direct2D"
        if selected_mode in {"direct2d", "d2d", "direct3d", "d3d", "d3d9"} or windows_application_mode is None:
            target_macros.setdefault("__D64_GRAPHICS_WINDOWS__", 1)
            target_macros.setdefault(
                "__D64_GRAPHICS_DIRECT3D__"
                if str(graphics_backend).casefold().startswith("direct3")
                else "__D64_GRAPHICS_DIRECT2D__",
                1,
            )
    else:
        raise C64CError(f"Unbekanntes Compilerziel: {target}.", filename=filename)

    frontend = _parse_c_frontend(
        source,
        filename=filename,
        include_paths=include_paths,
        predefined_macros=target_macros,
    )
    try:
        if normalized_target in {"c64", "c-64", "6510"}:
            generated = _CCodeGenerator(frontend).generate()
        elif normalized_target in {"amiga", "amiga500", "a500", "m68k", "68000"}:
            generated = _AmigaCCodeGenerator(frontend).generate()
        elif normalized_target in {"pe32", "win32", "windows", "windows-pe32"}:
            if windows_application_mode is None:
                uses_graphics = bool(
                    re.search(r"\bInitGraphics\s*\(", source, re.IGNORECASE)
                )
                console_mode = not uses_graphics
            else:
                console_mode = str(windows_application_mode).strip().casefold() in {
                    "console", "konsole"
                }
            generated = _PE32CCodeGenerator(
                frontend,
                graphics_backend=graphics_backend,
                console_mode=console_mode,
            ).generate()
        else:
            raise C64CError(f"Unbekanntes Compilerziel: {target}.", filename=filename)

        main_symbols = (
            definition.symbol
            for definition in frontend.functions
            if not definition.is_static
        )
        c_modules, module_assembly_files = _compile_linked_c_modules(
            frontend.preprocessed.linked_c_files,
            include_paths=include_paths,
            predefined_macros=target_macros,
            normalized_target=normalized_target,
            initially_defined_symbols=main_symbols,
        )
        generated = _link_c_source_modules(generated, c_modules)

        assembly_files: List[str] = []
        for asm_file in (
            *frontend.preprocessed.linked_assembly_files,
            *module_assembly_files,
        ):
            if asm_file not in assembly_files:
                assembly_files.append(asm_file)
        return _link_c_assembly_modules(generated, assembly_files)
    except C64CError:
        raise
    except Exception as exc:
        line = getattr(exc, "line", None)
        column = getattr(exc, "column", None)
        message = getattr(exc, "message", str(exc))
        raise C64CError(
            message,
            line,
            (column - 1) if column else None,
            filename,
        ) from exc
