"""Kleiner ANTLR-basierter Pascal-Compiler für MOS 6510 und M68000.

Der Compiler erzeugt absichtlich lesbaren Assembler. Die zweite Stufe ist der
in ``d64_dism.py`` enthaltene Mehrpass-Assembler, der daraus ein C64-PRG mit
BASIC-SYS-Startzeile erstellt. Alternativ erzeugt das Amiga-Backend
Motorola-68000-Code für ein eigenständig bootfähiges ADF.
"""

from __future__ import annotations

import ast
import base64
import hashlib
import json
import re

from dataclasses import dataclass, field, fields, is_dataclass, replace
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from .generated.C64PascalLexer import C64PascalLexer
from .generated.C64PascalParser import C64PascalParser
from .generated.C64PascalParserVisitor import C64PascalParserVisitor


ScalarValue = Union[int, str, bool]


# Fest eingebetteter 8x8-Bitmapzeichensatz für ASCII $20..$7F. Die Glyphen
# werden vom Amiga-Backend als 1-Bit-Masken in das erzeugte 68000-ASM
# geschrieben. Dadurch benötigt das Standalone-Programm keine Fontdatei und
# keine graphics.library.
_AMIGA_FONT_8X8 = base64.b64decode(
    "AAAAAAAAAAAYGBgYAAAYAGZmZgAAAAAAZmb/Zv9mZgAYPmA8BnwYAGJmDBgwZkYAPGY8OGdmPwAGDBgA"
    "AAAAAAwYMDAwGAwAMBgMDAwYMAAAZjz/PGYAAAAYGH4YGAAAAAAAAAAYGDAAAAB+AAAAAAAAAAAAGBgA"
    "AAMGDBgwYAA8Zm52ZmY8ABgYOBgYGH4APGYGDDBgfgA8ZgYcBmY8AAYOHmZ/BgYAfmB8BgZmPAA8ZmB8"
    "ZmY8AH5mDBgYGBgAPGZmPGZmPAA8ZmY+BmY8AAAAGAAAGAAAAAAYAAAYGDAOGDBgMBgOAAAAfgB+AAAA"
    "cBgMBgwYcAA8ZgYMGAAYADxmbm5gYjwAGDxmfmZmZgB8ZmZ8ZmZ8ADxmYGBgZjwAeGxmZmZseAB+YGB4"
    "YGB+AH5gYHhgYGAAPGZgbmZmPABmZmZ+ZmZmADwYGBgYGDwAHgwMDAxsOABmbHhweGxmAGBgYGBgYH4A"
    "Y3d/a2NjYwBmdn5+bmZmADxmZmZmZjwAfGZmfGBgYAA8ZmZmZjwOAHxmZnx4bGYAPGZgPAZmPAB+GBgY"
    "GBgYAGZmZmZmZjwAZmZmZmY8GABjY2Nrf3djAGZmPBg8ZmYAZmZmPBgYGAB+BgwYMGB+ADwwMDAwMDwA"
    "AGAwGAwGAwA8DAwMDAw8AAgcNmNBAAAAAAAAAAAAAP8gEAgAAAAAAAAAPAY+Zj4AAGBgfGZmfAAAADxg"
    "YGA8AAAGBj5mZj4AAAA8Zn5gPAAADhg+GBgYAAAAPmZmPgZ8AGBgfGZmZgAAGAA4GBg8AAAGAAYGBgY8"
    "AGBgbHhsZgAAOBgYGBg8AAAAZn9/a2MAAAB8ZmZmZgAAADxmZmY8AAAAfGZmfGBgAAA+ZmY+BgYAAHxm"
    "YGBgAAAAPmA8BnwAABh+GBgYDgAAAGZmZmY+AAAAZmZmPBgAAABja38+NgAAAGY8GDxmAAAAZmZmPgx4"
    "AAB+DBgwfgAMGBgwGBgMABgYGBgYGBgYMBgYDBgYMAAAAAA5TgAAAAB+QkJCQn4A"
)


class C64PascalError(Exception):
    """Pascal-Fehler mit genauer Position im Quelltext."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
    ) -> None:
        self.message = str(message)
        self.line = int(line) if line else None
        self.column = int(column) + 1 if column is not None else None
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.line is None:
            return self.message
        if self.column is None:
            return f"Zeile {self.line}: {self.message}"
        return f"Zeile {self.line}, Spalte {self.column}: {self.message}"


@dataclass(frozen=True)
class SourcePosition:
    line: int
    column: int


@dataclass(frozen=True)
class Expression:
    position: SourcePosition


@dataclass(frozen=True)
class LiteralExpression(Expression):
    value: ScalarValue


@dataclass(frozen=True)
class NameExpression(Expression):
    name: str


@dataclass(frozen=True)
class DesignatorSelector:
    position: SourcePosition


@dataclass(frozen=True)
class FieldSelector(DesignatorSelector):
    name: str


@dataclass(frozen=True)
class IndexSelector(DesignatorSelector):
    expression: Expression


@dataclass(frozen=True)
class DereferenceSelector(DesignatorSelector):
    """Typed-pointer dereference (Object Pascal postfix ^)."""
    pass


@dataclass(frozen=True)
class DesignatorExpression(Expression):
    name: str
    selectors: Tuple[DesignatorSelector, ...] = ()


@dataclass(frozen=True)
class CallExpression(Expression):
    designator: Union[str, DesignatorExpression]
    arguments: Tuple[Expression, ...]

    @property
    def name(self) -> str:
        if isinstance(self.designator, DesignatorExpression):
            return self.designator.name
        return str(self.designator)


@dataclass(frozen=True)
class InheritedCallExpression(Expression):
    """Direct base-class method/function call used as an expression."""
    method_name: Optional[str]
    arguments: Tuple[Expression, ...]


@dataclass(frozen=True)
class AddressOfExpression(Expression):
    """Object-Pascal routine address expression, e.g. @WindowProc."""
    target: DesignatorExpression


@dataclass(frozen=True)
class UnaryExpression(Expression):
    operator: str
    operand: Expression


@dataclass(frozen=True)
class BinaryExpression(Expression):
    left: Expression
    operator: str
    right: Expression


@dataclass(frozen=True)
class Statement:
    position: SourcePosition


@dataclass(frozen=True)
class CompoundStatement(Statement):
    statements: Tuple[Statement, ...]


@dataclass(frozen=True)
class AssignmentStatement(Statement):
    designator: Union[str, DesignatorExpression]
    expression: Expression

    @property
    def name(self) -> str:
        if isinstance(self.designator, DesignatorExpression):
            return self.designator.name
        return str(self.designator)


@dataclass(frozen=True)
class CallStatement(Statement):
    designator: Union[str, DesignatorExpression]
    arguments: Tuple[Expression, ...]

    @property
    def name(self) -> str:
        if isinstance(self.designator, DesignatorExpression):
            return self.designator.name
        return str(self.designator)


@dataclass(frozen=True)
class InheritedCallStatement(Statement):
    method_name: Optional[str]
    arguments: Tuple[Expression, ...]


@dataclass(frozen=True)
class IfStatement(Statement):
    condition: Expression
    then_statement: Statement
    else_statement: Optional[Statement]


@dataclass(frozen=True)
class WhileStatement(Statement):
    condition: Expression
    body: Statement


@dataclass(frozen=True)
class RepeatStatement(Statement):
    statements: Tuple[Statement, ...]
    condition: Expression


@dataclass(frozen=True)
class ForStatement(Statement):
    name: str
    initial: Expression
    direction: str
    final: Expression
    body: Statement


@dataclass(frozen=True)
class BreakStatement(Statement):
    pass


@dataclass(frozen=True)
class ContinueStatement(Statement):
    pass


@dataclass(frozen=True)
class ExitStatement(Statement):
    """Leave the current Pascal routine/method immediately."""
    pass


@dataclass(frozen=True)
class RaiseStatement(Statement):
    """Object-Pascal RAISE statement.

    Stage 207 keeps the exception expression in the AST.  The Windows
    backends currently lower Exception.Create(message) to the established
    _jit_raise runtime contract; a bare re-raise is reserved for the later
    TRY/EXCEPT unwinding stage.
    """
    expression: Optional[Expression] = None


@dataclass(frozen=True)
class TryStatement(Statement):
    """Object-Pascal TRY/EXCEPT or TRY/FINALLY block."""
    try_statements: Tuple[Statement, ...]
    handler_kind: str
    handler_statements: Tuple[Statement, ...]


@dataclass(frozen=True)
class ConstDeclaration:
    name: str
    expression: Expression
    position: SourcePosition


@dataclass(frozen=True)
class TypeSpecification:
    position: SourcePosition


@dataclass(frozen=True)
class NamedTypeSpecification(TypeSpecification):
    name: str


@dataclass(frozen=True)
class SubrangeTypeSpecification(TypeSpecification):
    lower_bound: Expression
    upper_bound: Expression


@dataclass(frozen=True)
class PointerTypeSpecification(TypeSpecification):
    target_type_name: str


@dataclass(frozen=True)
class EnumTypeSpecification(TypeSpecification):
    names: Tuple[str, ...]


@dataclass(frozen=True)
class FieldDeclaration:
    names: Tuple[str, ...]
    type_name: str
    position: SourcePosition
    visibility: str = "public"
    offset: Optional[int] = None


@dataclass(frozen=True)
class RecordTypeSpecification(TypeSpecification):
    fields: Tuple[FieldDeclaration, ...]


@dataclass(frozen=True)
class ArrayTypeSpecification(TypeSpecification):
    lower_bound: Expression
    upper_bound: Expression
    element_type_name: str


@dataclass(frozen=True)
class ParameterDeclaration:
    names: Tuple[str, ...]
    type_name: str
    modifier: str
    position: SourcePosition


@dataclass(frozen=True)
class PropertyDeclaration:
    name: str
    type_name: str
    read_accessor: Optional[str]
    write_accessor: Optional[str]
    position: SourcePosition
    index_parameters: Tuple[ParameterDeclaration, ...] = ()
    visibility: str = "public"


@dataclass(frozen=True)
class MethodDeclaration:
    kind: str
    name: str
    parameters: Tuple[ParameterDeclaration, ...]
    result_type_name: Optional[str]
    position: SourcePosition
    directives: Tuple[str, ...] = ()
    is_class_method: bool = False
    visibility: str = "public"
    external_symbol: Optional[str] = None


@dataclass(frozen=True)
class ClassTypeSpecification(TypeSpecification):
    base_type_name: Optional[str]
    fields: Tuple[FieldDeclaration, ...]
    methods: Tuple[MethodDeclaration, ...]
    properties: Tuple[PropertyDeclaration, ...] = ()
    abi_size: Optional[int] = None


@dataclass(frozen=True)
class TypeDeclaration:
    name: str
    specification: TypeSpecification
    position: SourcePosition


@dataclass(frozen=True)
class VarDeclaration:
    names: Tuple[str, ...]
    type_name: str
    initializer: Optional[Expression]
    position: SourcePosition


@dataclass(frozen=True)
class GlobalRoutineImplementation:
    kind: str
    name: str
    parameters: Tuple[ParameterDeclaration, ...]
    result_type_name: Optional[str]
    local_variables: Tuple[VarDeclaration, ...]
    body: CompoundStatement
    position: SourcePosition
    calling_convention: Optional[str] = None


@dataclass(frozen=True)
class MethodImplementation:
    kind: str
    class_name: str
    name: str
    parameters: Tuple[ParameterDeclaration, ...]
    result_type_name: Optional[str]
    local_variables: Tuple[VarDeclaration, ...]
    body: CompoundStatement
    position: SourcePosition


@dataclass(frozen=True)
class ExternalRoutineDeclaration:
    unit_name: str
    kind: str
    name: str
    parameters: Tuple[ParameterDeclaration, ...]
    result_type_name: Optional[str]
    symbol: str
    calling_convention: Optional[str] = None
    library_reference: Optional[str] = None
    import_name: Optional[str] = None


@dataclass(frozen=True)
class PascalProgram:
    name: str
    constants: Tuple[ConstDeclaration, ...]
    variables: Tuple[VarDeclaration, ...]
    body: CompoundStatement
    types: Tuple[TypeDeclaration, ...] = ()
    methods: Tuple[MethodImplementation, ...] = ()
    external_routines: Tuple[ExternalRoutineDeclaration, ...] = ()
    global_routines: Tuple[GlobalRoutineImplementation, ...] = ()
    unit_assembly_files: Tuple[str, ...] = ()
    unit_object_files: Tuple[str, ...] = ()




def _pascal_metadata_signature(value):
    """Position-independent signature for compiler-generated Pascal metadata.

    This is used only to collapse identical declarations arriving from legacy
    parser bridges or PUI/dependency merges. User-written conflicting duplicate
    declarations remain errors.
    """
    if isinstance(value, SourcePosition):
        return None
    if is_dataclass(value):
        return (
            type(value).__name__,
            tuple(
                (item.name, _pascal_metadata_signature(getattr(value, item.name)))
                for item in fields(value)
                if item.name != "position"
            ),
        )
    if isinstance(value, tuple):
        return tuple(_pascal_metadata_signature(item) for item in value)
    if isinstance(value, list):
        return tuple(_pascal_metadata_signature(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted(
            (str(key).casefold(), _pascal_metadata_signature(item))
            for key, item in value.items()
        ))
    if isinstance(value, str):
        return value.casefold()
    return value


def _type_declarations_equivalent(
    left: TypeDeclaration,
    right: TypeDeclaration,
) -> bool:
    return (
        left.name.casefold() == right.name.casefold()
        and _pascal_metadata_signature(left.specification)
        == _pascal_metadata_signature(right.specification)
    )


def _merge_pascal_type_declarations(
    *groups: Sequence[TypeDeclaration],
) -> Tuple[TypeDeclaration, ...]:
    """Merge PUI/bridge type groups while preserving first-occurrence order.

    Identical declarations are one ABI type and are kept once. Incompatible
    same-name declarations are retained so the normal semantic duplicate check
    still reports them.
    """
    result: List[TypeDeclaration] = []
    by_name: Dict[str, TypeDeclaration] = {}
    for group in groups:
        for declaration in group:
            key = declaration.name.casefold()
            previous = by_name.get(key)
            if previous is not None and _type_declarations_equivalent(
                previous, declaration
            ):
                continue
            if previous is None:
                by_name[key] = declaration
            result.append(declaration)
    return tuple(result)


def _merge_pascal_type_scopes(
    imported_groups: Sequence[Sequence[TypeDeclaration]],
    local_group: Sequence[TypeDeclaration],
) -> Tuple[TypeDeclaration, ...]:
    """Merge Pascal type scopes with USES precedence.

    A declaration in the current module always shadows imported identifiers.
    For imported Units Pascal/Delphi name lookup gives the later visible USES
    scope precedence over an earlier one.  This matters for the Windows Units:
    for example ``System.Types.DWord`` and ``Windows.Types.DWORD`` may describe
    the same API name with intentionally different source-level aliases.

    Stage 192's duplicate guard is deliberately preserved *inside one scope*:
    two conflicting declarations in the same Unit are retained so the semantic
    pass still raises ``Datentyp mehrfach deklariert``.  Only declarations from
    an earlier, different scope are hidden by a later scope.
    """
    local = tuple(local_group)
    shadowed = {declaration.name.casefold() for declaration in local}

    # Resolver.programs is emitted in Pascal visibility order.  Walk backwards
    # so a later USES scope wins, then prepend accepted groups again to preserve
    # the original declaration order for all non-conflicting identifiers.
    visible_groups: List[Tuple[TypeDeclaration, ...]] = []
    for group in reversed(tuple(imported_groups)):
        current = tuple(group)
        accepted = tuple(
            declaration
            for declaration in current
            if declaration.name.casefold() not in shadowed
        )
        if accepted:
            visible_groups.append(accepted)

        # Add names only *after* filtering the complete group.  Consequently a
        # duplicate inside the same Unit is not hidden from the semantic check.
        shadowed.update(declaration.name.casefold() for declaration in current)

    imported: List[TypeDeclaration] = []
    for group in reversed(visible_groups):
        imported.extend(group)

    return tuple(imported) + local


@dataclass(frozen=True)
class GeneratedAssembly:
    program_name: str
    assembly: str
    source_map: Dict[int, int]
    variable_count: int
    string_count: int
    notes: Tuple["PascalPreprocessorDiagnostic", ...] = ()
    warnings: Tuple["PascalPreprocessorDiagnostic", ...] = ()
    source_kind: str = "program"
    unit_name: Optional[str] = None
    pui_path: Optional[str] = None
    linked_assembly_files: Tuple[str, ...] = ()
    linked_object_files: Tuple[str, ...] = ()

    def pascal_line_for_assembly_line(self, assembly_line: int) -> int:
        line = int(assembly_line)
        while line > 0:
            source_line = self.source_map.get(line, 0)
            if source_line:
                return source_line
            line -= 1
        return 0


class _RaisingErrorListener(ErrorListener):
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
        raise C64PascalError(f"Syntaxfehler: {msg}", line, column)


def _position(context) -> SourcePosition:
    return SourcePosition(context.start.line, context.start.column + 1)


class _AstBuilder(C64PascalParserVisitor):
    """Wandelt den ANTLR-Parsebaum in einen kleinen, typfreien AST um.

    Stage 198: Ein optionaler Progress-Callback meldet die aktuell vom
    ANTLR-Visitor bearbeitete Pascal-Quellzeile. Der Callback wird bewusst
    innerhalb des Compiler-Threads aufgerufen; die Qt-GUI bekommt die Werte
    anschließend ausschließlich über Signals des PascalCompileWorker.
    """

    def __init__(
        self,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        progress_filename: str = "<Pascal-Editor>",
    ) -> None:
        super().__init__()
        self._progress_callback = progress_callback
        self._progress_filename = str(progress_filename)
        self._progress_last_line = 0

    def _report_progress(self, ctx) -> None:
        callback = self._progress_callback
        if callback is None or ctx is None:
            return
        start = getattr(ctx, "start", None)
        line = int(getattr(start, "line", 0) or 0)
        if line <= 0 or line == self._progress_last_line:
            return
        self._progress_last_line = line
        callback(self._progress_filename, line)

    def visit(self, tree):
        self._report_progress(tree)
        return super().visit(tree)

    def visitCompilationUnit(self, ctx):
        if ctx.programUnit() is not None:
            return self.visit(ctx.programUnit())
        unit_accessor = getattr(ctx, "unitUnit", None)
        if unit_accessor is not None and unit_accessor() is not None:
            return self.visit(unit_accessor())
        raise C64PascalError("Interner Fehler: leere Pascal-CompilationUnit.")

    def visitProgramUnit(self, ctx):
        (
            constants,
            types,
            variables,
            methods,
            externals,
            global_routines,
            body,
        ) = self.visit(ctx.block())
        return PascalProgram(
            name=ctx.IDENTIFIER().getText(),
            constants=tuple(constants),
            variables=tuple(variables),
            body=body,
            types=tuple(types),
            methods=tuple(methods),
            external_routines=tuple(externals),
            global_routines=tuple(global_routines),
        )

    def visitUnitUnit(self, ctx):
        constants = []
        types = []
        variables = []
        for section in ctx.declarationSection():
            if section.constSection():
                constants.extend(self.visit(section.constSection()))
            elif section.typeSection():
                types.extend(self.visit(section.typeSection()))
            elif section.varSection():
                variables.extend(self.visit(section.varSection()))
        methods = [self.visit(item) for item in ctx.methodImplementation()]
        global_routines = [
            self.visit(item) for item in ctx.globalRoutineImplementation()
        ] if hasattr(ctx, "globalRoutineImplementation") else []
        externals = []
        for item in ctx.globalRoutineDeclaration():
            declaration = self.visit(item)
            if declaration is not None:
                externals.append(declaration)
        body_ctx = ctx.compoundStatement()
        body = (
            self.visit(body_ctx)
            if body_ctx is not None
            else CompoundStatement(_position(ctx), ())
        )
        return PascalProgram(
            name=ctx.qualifiedIdentifier().getText(),
            constants=tuple(constants),
            variables=tuple(variables),
            body=body,
            types=tuple(types),
            methods=tuple(methods),
            external_routines=tuple(externals),
            global_routines=tuple(global_routines),
        )

    def visitBlock(self, ctx):
        constants = []
        types = []
        variables = []
        for section in ctx.declarationSection():
            if section.constSection():
                constants.extend(self.visit(section.constSection()))
            elif section.typeSection():
                types.extend(self.visit(section.typeSection()))
            elif section.varSection():
                variables.extend(self.visit(section.varSection()))
        methods = [self.visit(item) for item in ctx.methodImplementation()]
        global_routines = [
            self.visit(item) for item in ctx.globalRoutineImplementation()
        ] if hasattr(ctx, "globalRoutineImplementation") else []
        external_contexts = (
            ctx.globalRoutineDeclaration()
            if hasattr(ctx, "globalRoutineDeclaration")
            else []
        )
        externals = []
        for item in external_contexts:
            declaration = self.visit(item)
            if declaration is not None:
                externals.append(declaration)
        return (
            constants,
            types,
            variables,
            methods,
            externals,
            global_routines,
            self.visit(ctx.compoundStatement()),
        )

    def visitConstSection(self, ctx):
        return [self.visit(item) for item in ctx.constDefinition()]

    def visitConstDefinition(self, ctx):
        return ConstDeclaration(
            ctx.IDENTIFIER().getText(),
            self.visit(ctx.expression()),
            _position(ctx),
        )

    def visitTypeSection(self, ctx):
        return [self.visit(item) for item in ctx.typeDefinition()]

    def visitTypeDefinition(self, ctx):
        if hasattr(ctx, "typeName") and ctx.typeName() is not None:
            name = ctx.typeName().getText()
        else:
            name = ctx.IDENTIFIER().getText()
        return TypeDeclaration(
            name,
            self.visit(ctx.typeSpecification()),
            _position(ctx),
        )

    def visitTypeSpecification(self, ctx):
        for child_name in (
            "typeIdentifier",
            "subrangeType",
            "pointerType",
            "enumType",
            "recordType",
            "arrayType",
            "classType",
        ):
            accessor = getattr(ctx, child_name, None)
            child = accessor() if accessor is not None else None
            if child is not None:
                if child_name == "typeIdentifier":
                    return NamedTypeSpecification(
                        _position(ctx),
                        child.getText().casefold(),
                    )
                return self.visit(child)
        raise C64PascalError("Interner Fehler: leere Typdefinition.")

    def visitSubrangeType(self, ctx):
        values = ctx.signedIntegerLiteral()
        return SubrangeTypeSpecification(
            _position(ctx),
            self.visit(values[0]),
            self.visit(values[1]),
        )

    def visitPointerType(self, ctx):
        return PointerTypeSpecification(
            _position(ctx),
            ctx.typeIdentifier().getText().casefold(),
        )

    def visitSignedIntegerLiteral(self, ctx):
        literal = self.visit(ctx.integerLiteral())
        value = int(literal.value)
        if ctx.MINUS():
            value = -value
        return LiteralExpression(_position(ctx), value)

    def visitEnumType(self, ctx):
        names = tuple(token.getText() for token in ctx.identifierList().IDENTIFIER())
        return EnumTypeSpecification(_position(ctx), names)

    def visitRecordType(self, ctx):
        return RecordTypeSpecification(
            _position(ctx),
            tuple(self.visit(item) for item in ctx.fieldDeclaration()),
        )

    def visitArrayType(self, ctx):
        expressions = ctx.expression()
        return ArrayTypeSpecification(
            _position(ctx),
            self.visit(expressions[0]),
            self.visit(expressions[1]),
            ctx.typeIdentifier().getText().casefold(),
        )

    def visitClassType(self, ctx):
        fields = []
        methods = []
        properties = []
        visibility = "public"
        for member in ctx.classMember():
            visibility_accessor = getattr(member, "visibilitySpecifier", None)
            visibility_ctx = (
                visibility_accessor()
                if visibility_accessor is not None
                else None
            )
            if visibility_ctx is not None:
                visibility = visibility_ctx.getText().casefold()
                continue
            if member.fieldDeclaration():
                fields.append(
                    replace(
                        self.visit(member.fieldDeclaration()),
                        visibility=visibility,
                    )
                )
            elif member.methodDeclaration():
                methods.append(
                    replace(
                        self.visit(member.methodDeclaration()),
                        visibility=visibility,
                    )
                )
            else:
                property_accessor = getattr(member, "propertyDeclaration", None)
                if property_accessor is not None and property_accessor() is not None:
                    properties.append(
                        replace(
                            self.visit(property_accessor()),
                            visibility=visibility,
                        )
                    )
        base_type_name = (
            ctx.typeIdentifier().getText().casefold()
            if ctx.typeIdentifier()
            else None
        )
        return ClassTypeSpecification(
            _position(ctx),
            base_type_name,
            tuple(fields),
            tuple(methods),
            tuple(properties),
        )

    def visitPropertyDeclaration(self, ctx):
        read_accessor = None
        write_accessor = None
        for specifier in ctx.propertySpecifier():
            accessor = (
                specifier.propertyAccessor()
                if hasattr(specifier, "propertyAccessor")
                else None
            )
            if specifier.READ():
                read_accessor = accessor.getText() if accessor is not None else None
            elif specifier.WRITE():
                write_accessor = accessor.getText() if accessor is not None else None
        index_parameters = ()
        index_ctx = ctx.propertyIndexParameters()
        if index_ctx is not None and index_ctx.formalParameterList() is not None:
            index_parameters = tuple(self.visit(index_ctx.formalParameterList()))
        return PropertyDeclaration(
            ctx.IDENTIFIER().getText(),
            ctx.typeIdentifier().getText().casefold(),
            read_accessor,
            write_accessor,
            _position(ctx),
            index_parameters,
        )

    def visitFieldDeclaration(self, ctx):
        return FieldDeclaration(
            tuple(token.getText() for token in ctx.identifierList().IDENTIFIER()),
            ctx.typeIdentifier().getText().casefold(),
            _position(ctx),
        )

    def visitMethodDeclaration(self, ctx):
        directive_contexts = (
            ctx.methodDirective() if hasattr(ctx, "methodDirective") else []
        )
        directives = tuple(
            item.getText().rstrip(";").casefold()
            for item in directive_contexts
        )
        return MethodDeclaration(
            ctx.routineKind().getText().casefold(),
            ctx.IDENTIFIER().getText(),
            tuple(self.visit(ctx.formalParameters())) if ctx.formalParameters() else (),
            ctx.typeIdentifier().getText().casefold() if ctx.typeIdentifier() else None,
            _position(ctx),
            directives,
            bool(ctx.CLASS()) if hasattr(ctx, "CLASS") else False,
        )

    def visitGlobalRoutineDeclaration(self, ctx):
        kind = "function" if ctx.FUNCTION() else "procedure"
        # FORWARD only declares a later implementation; EXTERNAL produces a
        # real linker-visible external routine.
        external_token = getattr(ctx, "EXTERNAL", lambda: None)()
        if external_token is None:
            return None
        parameters = (
            tuple(self.visit(ctx.formalParameters()))
            if ctx.formalParameters()
            else ()
        )
        name = ctx.IDENTIFIER().getText()
        convention_ctx = getattr(ctx, "globalRoutineCallingConvention", lambda: None)()
        calling_convention = (
            convention_ctx.getText().split(";", 1)[0].strip().casefold()
            if convention_ctx is not None
            else None
        )
        library_reference = None
        import_name = None
        import_ctx = getattr(ctx, "externalImportSpecification", lambda: None)()
        if import_ctx is not None:
            raw_import = import_ctx.getText()
            import_match = re.fullmatch(
                r"(?is)(?P<library>'(?:''|[^'])*'|[A-Za-z_][A-Za-z0-9_]*)"
                r"(?:name(?P<member>'(?:''|[^'])*'))?",
                raw_import,
            )
            if import_match is not None:
                raw_library = import_match.group("library")
                if raw_library.startswith("'"):
                    library_reference = raw_library[1:-1].replace("''", "'")
                else:
                    library_reference = raw_library
                raw_member = import_match.group("member")
                if raw_member:
                    import_name = raw_member[1:-1].replace("''", "'")
        symbol = "_" + name if calling_convention == "cdecl" else name
        return ExternalRoutineDeclaration(
            "",
            kind,
            name,
            parameters,
            ctx.typeIdentifier().getText().casefold() if ctx.typeIdentifier() else None,
            symbol,
            calling_convention,
            library_reference,
            import_name,
        )

    def visitGlobalRoutineImplementation(self, ctx):
        local_variables, body = self.visit(ctx.routineBlock())
        convention_ctx = getattr(ctx, "globalRoutineCallingConvention", lambda: None)()
        return GlobalRoutineImplementation(
            "function" if ctx.FUNCTION() else "procedure",
            ctx.IDENTIFIER().getText(),
            tuple(self.visit(ctx.formalParameters())) if ctx.formalParameters() else (),
            ctx.typeIdentifier().getText().casefold() if ctx.typeIdentifier() else None,
            tuple(local_variables),
            body,
            _position(ctx),
            (
                convention_ctx.getText().split(";", 1)[0].strip().casefold()
                if convention_ctx is not None
                else None
            ),
        )

    def visitFormalParameters(self, ctx):
        if ctx.formalParameterList() is None:
            return []
        return self.visit(ctx.formalParameterList())

    def visitFormalParameterList(self, ctx):
        result = []
        for group in ctx.formalParameterGroup():
            result.extend(self.visit(group))
        return result

    def visitFormalParameterGroup(self, ctx):
        modifier = "const" if ctx.CONST() else "var" if ctx.VAR() else "value"
        position = _position(ctx)
        type_name = ctx.typeIdentifier().getText().casefold()
        return [
            ParameterDeclaration((token.getText(),), type_name, modifier, position)
            for token in ctx.identifierList().IDENTIFIER()
        ]

    def visitMethodImplementation(self, ctx):
        local_variables, body = self.visit(ctx.routineBlock())
        identifiers = ctx.IDENTIFIER()
        return MethodImplementation(
            ctx.routineKind().getText().casefold(),
            identifiers[0].getText(),
            identifiers[1].getText(),
            tuple(self.visit(ctx.formalParameters())) if ctx.formalParameters() else (),
            ctx.typeIdentifier().getText().casefold() if ctx.typeIdentifier() else None,
            tuple(local_variables),
            body,
            _position(ctx),
        )

    def visitRoutineBlock(self, ctx):
        variables = self.visit(ctx.varSection()) if ctx.varSection() else []
        return variables, self.visit(ctx.compoundStatement())

    def visitVarSection(self, ctx):
        return [self.visit(item) for item in ctx.varDeclaration()]

    def visitVarDeclaration(self, ctx):
        names = tuple(token.getText() for token in ctx.identifierList().IDENTIFIER())
        initializer = self.visit(ctx.expression()) if ctx.expression() else None
        return VarDeclaration(
            names,
            ctx.typeIdentifier().getText().casefold(),
            initializer,
            _position(ctx),
        )

    def visitCompoundStatement(self, ctx):
        statements = self.visit(ctx.statementSequence()) if ctx.statementSequence() else []
        return CompoundStatement(_position(ctx), tuple(statements))

    def visitStatementSequence(self, ctx):
        return [self.visit(item) for item in ctx.statement()]

    def visitCompoundStatementNode(self, ctx):
        return self.visit(ctx.compoundStatement())

    def visitAssignmentStatementNode(self, ctx):
        return self.visit(ctx.assignmentStatement())

    def visitCallStatementNode(self, ctx):
        return self.visit(ctx.callStatement())

    def visitInheritedStatementNode(self, ctx):
        return self.visit(ctx.inheritedStatement())

    def visitInheritedStatement(self, ctx):
        identifier = ctx.IDENTIFIER()
        arguments = self.visit(ctx.argumentList()) if ctx.argumentList() else []
        return InheritedCallStatement(
            _position(ctx),
            identifier.getText() if identifier is not None else None,
            tuple(arguments),
        )

    def visitIfStatementNode(self, ctx):
        return self.visit(ctx.ifStatement())

    def visitWhileStatementNode(self, ctx):
        return self.visit(ctx.whileStatement())

    def visitRepeatStatementNode(self, ctx):
        return self.visit(ctx.repeatStatement())

    def visitForStatementNode(self, ctx):
        return self.visit(ctx.forStatement())

    def visitBreakStatementNode(self, ctx):
        return BreakStatement(_position(ctx))

    def visitContinueStatementNode(self, ctx):
        return ContinueStatement(_position(ctx))

    def visitExitStatementNode(self, ctx):
        return ExitStatement(_position(ctx))

    def visitAssignmentStatement(self, ctx):
        return AssignmentStatement(
            _position(ctx),
            self.visit(ctx.designator()),
            self.visit(ctx.expression()),
        )

    def visitCallStatement(self, ctx):
        arguments = self.visit(ctx.argumentList()) if ctx.argumentList() else []
        designator = self.visit(ctx.designator())

        # Stage 211 compatibility: generated parsers from earlier stages lex
        # EXIT as IDENTIFIER, so a bare ``Exit;`` arrives as CallStatement.
        # Convert it to the language statement before method/routine lookup.
        if (
            isinstance(designator, DesignatorExpression)
            and not designator.selectors
            and designator.name.casefold() == "exit"
            and not arguments
        ):
            return ExitStatement(_position(ctx))

        if (
            isinstance(designator, DesignatorExpression)
            and not designator.selectors
            and designator.name.casefold() in {"__d64_raise", "__d64_reraise"}
        ):
            if designator.name.casefold() == "__d64_reraise":
                if arguments:
                    raise C64PascalError(
                        "Internes RERAISE erwartet keine Argumente.",
                        ctx.start.line,
                        ctx.start.column,
                    )
                return RaiseStatement(_position(ctx), None)
            if len(arguments) != 1:
                raise C64PascalError(
                    "RAISE erwartet genau einen Exception-Ausdruck.",
                    ctx.start.line,
                    ctx.start.column,
                )
            return RaiseStatement(_position(ctx), arguments[0])
        return CallStatement(
            _position(ctx),
            designator,
            tuple(arguments),
        )

    def visitRaiseStatementNode(self, ctx):
        return self.visit(ctx.raiseStatement())

    def visitRaiseStatement(self, ctx):
        expression = ctx.expression() if hasattr(ctx, "expression") else None
        return RaiseStatement(
            _position(ctx),
            self.visit(expression) if expression is not None else None,
        )

    def visitTryStatementNode(self, ctx):
        return self.visit(ctx.tryStatement())

    def visitTryStatement(self, ctx):
        sequences = list(ctx.statementSequence()) if hasattr(ctx, "statementSequence") else []
        try_statements = (
            tuple(self.visit(sequences[0])) if sequences else ()
        )
        handler_statements = (
            tuple(self.visit(sequences[1])) if len(sequences) > 1 else ()
        )
        handler_kind = "except" if getattr(ctx, "EXCEPT", lambda: None)() is not None else "finally"
        return TryStatement(
            _position(ctx),
            try_statements,
            handler_kind,
            handler_statements,
        )

    def visitIfStatement(self, ctx):
        statements = ctx.statement()
        return IfStatement(
            _position(ctx),
            self.visit(ctx.expression()),
            self.visit(statements[0]),
            self.visit(statements[1]) if len(statements) > 1 else None,
        )

    def visitWhileStatement(self, ctx):
        return WhileStatement(
            _position(ctx),
            self.visit(ctx.expression()),
            self.visit(ctx.statement()),
        )

    def visitRepeatStatement(self, ctx):
        statements = self.visit(ctx.statementSequence()) if ctx.statementSequence() else []
        return RepeatStatement(
            _position(ctx),
            tuple(statements),
            self.visit(ctx.expression()),
        )

    def visitForStatement(self, ctx):
        direction = "to" if ctx.TO() else "downto"
        expressions = ctx.expression()
        return ForStatement(
            _position(ctx),
            ctx.IDENTIFIER().getText(),
            self.visit(expressions[0]),
            direction,
            self.visit(expressions[1]),
            self.visit(ctx.statement()),
        )

    def visitArgumentList(self, ctx):
        return [self.visit(item) for item in ctx.expression()]

    def visitDesignator(self, ctx):
        selectors = []
        for suffix in ctx.designatorSuffix():
            caret = getattr(suffix, "CARET", None)
            if callable(caret) and caret() is not None:
                selectors.append(DereferenceSelector(_position(suffix)))
            elif suffix.DOT():
                name = suffix.IDENTIFIER().getText()
                if name.casefold() == "__d64_deref":
                    selectors.append(DereferenceSelector(_position(suffix)))
                else:
                    selectors.append(FieldSelector(_position(suffix), name))
            else:
                selectors.append(
                    IndexSelector(_position(suffix), self.visit(suffix.expression()))
                )
        identifier = ctx.IDENTIFIER()
        name = (
            identifier.getText()
            if identifier is not None
            else "nil"
        )
        return DesignatorExpression(
            _position(ctx),
            name,
            tuple(selectors),
        )

    def _fold_binary(self, ctx):
        result = self.visit(ctx.getChild(0))
        for index in range(1, ctx.getChildCount(), 2):
            result = BinaryExpression(
                result.position,
                result,
                ctx.getChild(index).getText().casefold(),
                self.visit(ctx.getChild(index + 1)),
            )
        return result

    def visitExpression(self, ctx):
        return self.visit(ctx.orExpression())

    def visitOrExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitAndExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitComparisonExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitAdditiveExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitMultiplicativeExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitUnaryExpression(self, ctx):
        if ctx.primaryExpression():
            return self.visit(ctx.primaryExpression())
        at_accessor = getattr(ctx, "AT", None)
        designator_accessor = getattr(ctx, "designator", None)
        if (
            callable(at_accessor)
            and at_accessor() is not None
            and callable(designator_accessor)
            and designator_accessor() is not None
        ):
            target = self.visit(designator_accessor())
            if not isinstance(target, DesignatorExpression):
                raise C64PascalError(
                    "Adressoperator @ erwartet einen Routinenbezeichner.",
                    ctx.start.line,
                    ctx.start.column,
                )
            return AddressOfExpression(_position(ctx), target)
        operand = self.visit(ctx.unaryExpression())
        return UnaryExpression(
            _position(ctx),
            ctx.getChild(0).getText().casefold(),
            operand,
        )

    def visitPrimaryExpression(self, ctx):
        position = _position(ctx)
        if ctx.integerLiteral():
            return self.visit(ctx.integerLiteral())
        if ctx.STRING_LITERAL():
            text = ctx.STRING_LITERAL().getText()[1:-1].replace("''", "'")
            return LiteralExpression(position, text)
        if ctx.TRUE():
            return LiteralExpression(position, True)
        if ctx.FALSE():
            return LiteralExpression(position, False)
        if hasattr(ctx, "NIL") and ctx.NIL():
            return NameExpression(position, "nil")
        cast_accessor = getattr(ctx, "typeCastExpression", None)
        if cast_accessor is not None and cast_accessor() is not None:
            return self.visit(cast_accessor())

        # Stage 209: a freshly regenerated parser exposes INHERITED as its own
        # primary-expression alternative.  Stage 208 implemented the visitor
        # method itself, but forgot to dispatch to it from this generic primary
        # visitor.  In that case ctx.expression() is None and the old fallback
        # eventually called visit(None).
        inherited_accessor = getattr(ctx, "inheritedExpression", None)
        if callable(inherited_accessor):
            inherited_ctx = inherited_accessor()
            if inherited_ctx is not None:
                return self.visit(inherited_ctx)

        if ctx.designator():
            designator = self.visit(ctx.designator())
            if ctx.LPAREN():
                arguments = self.visit(ctx.argumentList()) if ctx.argumentList() else []
                if (
                    isinstance(designator, DesignatorExpression)
                    and not designator.selectors
                    and designator.name.casefold() == "__d64_addressof"
                ):
                    if len(arguments) != 1 or not isinstance(
                        arguments[0], DesignatorExpression
                    ):
                        raise C64PascalError(
                            "Adressoperator @ erwartet genau einen Routinenbezeichner.",
                            position.line,
                            position.column - 1,
                        )
                    return AddressOfExpression(position, arguments[0])
                return CallExpression(position, designator, tuple(arguments))
            return designator
        return self.visit(ctx.expression())

    def visitInheritedExpression(self, ctx):
        position = _position(ctx)
        identifier = ctx.IDENTIFIER()
        arguments = self.visit(ctx.argumentList()) if ctx.argumentList() else []
        return InheritedCallExpression(
            position,
            identifier.getText() if identifier is not None else None,
            tuple(arguments),
        )

    def visitTypeCastExpression(self, ctx):
        position = _position(ctx)
        type_name = ctx.builtinCastType().getText()
        designator = DesignatorExpression(position, type_name, ())
        return CallExpression(
            position,
            designator,
            (self.visit(ctx.expression()),),
        )

    def visitIntegerLiteral(self, ctx):
        text = ctx.getText()
        if text.startswith("$"):
            value = int(text[1:], 16)
        elif text.startswith("%"):
            value = int(text[1:], 2)
        else:
            value = int(text, 10)
        return LiteralExpression(_position(ctx), value)


def _pascal_code_mask(source: str) -> str:
    """Maskiert Strings und Kommentare, behält aber Positionen und Zeilen."""
    text = str(source)
    output = list(text)
    index = 0
    state = "code"
    while index < len(text):
        character = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""
        if state == "code":
            if character == "'":
                output[index] = " "
                state = "string"
            elif character == "{":
                output[index] = " "
                state = "brace_comment"
            elif character == "(" and following == "*":
                output[index] = output[index + 1] = " "
                index += 1
                state = "paren_comment"
            elif character == "/" and following == "/":
                output[index] = output[index + 1] = " "
                index += 1
                state = "line_comment"
        elif state == "string":
            if character != "\n":
                output[index] = " "
            if character == "'":
                if following == "'":
                    output[index + 1] = " "
                    index += 1
                else:
                    state = "code"
        elif state == "brace_comment":
            if character != "\n":
                output[index] = " "
            if character == "}":
                state = "code"
        elif state == "paren_comment":
            if character != "\n":
                output[index] = " "
            if character == "*" and following == ")":
                output[index + 1] = " "
                index += 1
                state = "code"
        else:
            if character != "\n":
                output[index] = " "
            if character == "\n":
                state = "code"
        index += 1
    return "".join(output)


@dataclass(frozen=True)
class PascalPreprocessResult:
    source: str
    macros: Dict[str, str]
    notes: Tuple["PascalPreprocessorDiagnostic", ...] = ()
    warnings: Tuple["PascalPreprocessorDiagnostic", ...] = ()
    link_files: Tuple[str, ...] = ()


@dataclass(frozen=True)
class PascalPreprocessorDiagnostic:
    kind: str
    message: str
    filename: str
    line: int

    def __str__(self) -> str:
        return f"{self.filename}:{self.line}: {self.kind}: {self.message}"


def _expand_pascal_macros(
    source: str,
    macros: Dict[str, str],
    expansion_stack: Tuple[str, ...] = (),
) -> str:
    if not macros or not source:
        return source
    mask = _pascal_code_mask(source)
    output = []
    cursor = 0
    for match in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", mask):
        output.append(source[cursor:match.start()])
        name = match.group(0)
        key = name.casefold()
        if key not in macros:
            output.append(source[match.start():match.end()])
        elif key in expansion_stack:
            chain = " -> ".join(expansion_stack + (key,))
            raise C64PascalError(f"Rekursive Pascal-Makrodefinition: {chain}.")
        else:
            output.append(
                _expand_pascal_macros(
                    macros[key],
                    macros,
                    expansion_stack + (key,),
                )
            )
        cursor = match.end()
    output.append(source[cursor:])
    return "".join(output)


def _condition_identifiers(
    expression: str,
    macros: Dict[str, str],
    stack: Tuple[str, ...] = (),
) -> str:
    mask = _pascal_code_mask(expression)
    output = []
    cursor = 0
    mappings = {
        "true": "True",
        "false": "False",
        "and": "and",
        "or": "or",
        "not": "not",
        "div": "//",
        "mod": "%",
        "xor": "^",
    }
    for match in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", mask):
        output.append(expression[cursor:match.start()])
        name = match.group(0)
        key = name.casefold()
        if key in mappings:
            output.append(mappings[key])
        elif key in macros:
            if key in stack:
                chain = " -> ".join(stack + (key,))
                raise C64PascalError(
                    f"Rekursive Pascal-Makrobedingung: {chain}."
                )
            output.append(
                "("
                + _condition_identifiers(
                    macros[key],
                    macros,
                    stack + (key,),
                )
                + ")"
            )
        else:
            output.append("0")
        cursor = match.end()
    output.append(expression[cursor:])
    return "".join(output)


def _evaluate_preprocessor_ast(node: ast.AST):
    if isinstance(node, ast.Expression):
        return _evaluate_preprocessor_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(
        node.value,
        (bool, int, str),
    ):
        return node.value
    if isinstance(node, ast.UnaryOp):
        value = _evaluate_preprocessor_ast(node.operand)
        if isinstance(node.op, ast.Not):
            return not bool(value)
        if isinstance(node.op, ast.USub):
            return -int(value)
        if isinstance(node.op, ast.UAdd):
            return +int(value)
    if isinstance(node, ast.BoolOp):
        values = [_evaluate_preprocessor_ast(item) for item in node.values]
        if isinstance(node.op, ast.And):
            return all(bool(item) for item in values)
        if isinstance(node.op, ast.Or):
            return any(bool(item) for item in values)
    if isinstance(node, ast.BinOp):
        left = _evaluate_preprocessor_ast(node.left)
        right = _evaluate_preprocessor_ast(node.right)
        operations = {
            ast.Add: lambda: left + right,
            ast.Sub: lambda: int(left) - int(right),
            ast.Mult: lambda: int(left) * int(right),
            ast.FloorDiv: lambda: int(left) // int(right),
            ast.Mod: lambda: int(left) % int(right),
            ast.BitAnd: lambda: int(left) & int(right),
            ast.BitOr: lambda: int(left) | int(right),
            ast.BitXor: lambda: int(left) ^ int(right),
        }
        operation = operations.get(type(node.op))
        if operation is not None:
            return operation()
    if isinstance(node, ast.Compare):
        left = _evaluate_preprocessor_ast(node.left)
        for operator, comparator in zip(node.ops, node.comparators):
            right = _evaluate_preprocessor_ast(comparator)
            comparisons = {
                ast.Eq: left == right,
                ast.NotEq: left != right,
                ast.Lt: left < right,
                ast.LtE: left <= right,
                ast.Gt: left > right,
                ast.GtE: left >= right,
            }
            if type(operator) not in comparisons or not comparisons[type(operator)]:
                return False
            left = right
        return True
    raise C64PascalError("Nicht unterstützter Ausdruck in {$if ...}.")


def _evaluate_pascal_condition(
    expression: str,
    macros: Dict[str, str],
) -> bool:
    text = re.sub(
        r"\bdefined\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)",
        lambda match: "True"
        if match.group(1).casefold() in macros
        else "False",
        expression,
        flags=re.IGNORECASE,
    )
    text = _condition_identifiers(text, macros)
    text = re.sub(r"(?<![A-Za-z0-9_])\$([0-9A-Fa-f]+)", r"0x\1", text)
    text = re.sub(r"(?<![A-Za-z0-9_])%([01]+)", r"0b\1", text)
    text = text.replace("<>", "!=")
    text = re.sub(r"(?<![<>=!])=(?!=)", "==", text)
    try:
        tree = ast.parse(text, mode="eval")
        return bool(_evaluate_preprocessor_ast(tree))
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise C64PascalError(
            f"Ungültiger Ausdruck in {{$if {expression}}}: {exc}."
        ) from exc


class PascalPreprocessor:
    """Bedingte Pascal-Direktiven und objektartige Makros."""

    def __init__(
        self,
        predefined_macros: Optional[Dict[str, Union[str, int, bool]]] = None,
        *,
        link_search_paths: Iterable[Path | str] = (),
    ) -> None:
        self.macros: Dict[str, str] = {}
        self.notes: List[PascalPreprocessorDiagnostic] = []
        self.warnings: List[PascalPreprocessorDiagnostic] = []
        # {$L file.o} / {$LINK file.o}: echte Linker-Eingaben fuer den
        # integrierten COFF32/COFF64-Linker. Die Liste bleibt ueber rekursiv
        # verarbeitete USES-Units erhalten und wird am Ende dedupliziert.
        self.link_files: List[str] = []
        self.link_search_paths: List[Path] = []
        for item in link_search_paths or ():
            try:
                path = Path(item).expanduser().resolve()
            except (OSError, RuntimeError, ValueError):
                path = Path(item).expanduser().absolute()
            if path not in self.link_search_paths:
                self.link_search_paths.append(path)
        for name, value in (predefined_macros or {}).items():
            key = str(name).casefold()
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(name)):
                raise C64PascalError(f"Ungültiger Pascal-Makroname: {name}.")
            self.macros[key] = (
                "1" if value is True else "0" if value is False else str(value)
            )

    @staticmethod
    def _blank(text: str) -> str:
        return "".join("\n" if character == "\n" else " " for character in text)

    def process(
        self,
        source: str,
        *,
        filename: str = "<Pascal-Editor>",
    ) -> PascalPreprocessResult:
        text = str(source)
        output: List[str] = []
        process_link_files: List[str] = []
        frames: List[Dict[str, bool]] = []
        segment_start = 0
        index = 0
        state = "code"

        def active() -> bool:
            return frames[-1]["active"] if frames else True

        def flush(end: int) -> None:
            segment = text[segment_start:end]
            output.append(
                _expand_pascal_macros(segment, self.macros)
                if active()
                else self._blank(segment)
            )

        while index < len(text):
            character = text[index]
            following = text[index + 1] if index + 1 < len(text) else ""
            if state == "code":
                if character == "'":
                    state = "string"
                elif character == "{" and following == "$":
                    flush(index)
                    end = text.find("}", index + 2)
                    line = text.count("\n", 0, index) + 1
                    if end < 0:
                        raise C64PascalError(
                            f"Nicht abgeschlossene Präprozessor-Direktive ({filename}).",
                            line,
                            0,
                        )
                    raw = text[index + 2:end].strip()
                    parts = raw.split(None, 1)
                    command = parts[0].casefold() if parts else ""
                    argument = parts[1].strip() if len(parts) > 1 else ""
                    was_active = active()
                    if command in {"ifdef", "ifndef", "if"}:
                        parent_active = was_active
                        if command == "if":
                            condition = (
                                _evaluate_pascal_condition(argument, self.macros)
                                if parent_active
                                else False
                            )
                        else:
                            if not re.fullmatch(
                                r"[A-Za-z_][A-Za-z0-9_]*",
                                argument,
                            ):
                                raise C64PascalError(
                                    f"{{$${command}}} erwartet einen Makronamen.",
                                    line,
                                    0,
                                )
                            defined = argument.casefold() in self.macros
                            condition = defined if command == "ifdef" else not defined
                        frames.append(
                            {
                                "parent": parent_active,
                                "condition": bool(condition),
                                "active": parent_active and bool(condition),
                                "else_seen": False,
                            }
                        )
                    elif command == "else":
                        if not frames:
                            raise C64PascalError(
                                f"{{$else}} ohne Bedingung ({filename}).",
                                line,
                                0,
                            )
                        frame = frames[-1]
                        if frame["else_seen"]:
                            raise C64PascalError(
                                f"Mehrfaches {{$else}} ({filename}).",
                                line,
                                0,
                            )
                        frame["else_seen"] = True
                        frame["active"] = frame["parent"] and not frame["condition"]
                    elif command == "endif":
                        if not frames:
                            raise C64PascalError(
                                f"{{$endif}} ohne Bedingung ({filename}).",
                                line,
                                0,
                            )
                        frames.pop()
                    elif command in {"define", "undef"}:
                        if was_active:
                            define_match = re.fullmatch(
                                r"([A-Za-z_][A-Za-z0-9_]*)(?:\s*(?::=|=)?\s*(.*))?",
                                argument,
                            )
                            if define_match is None:
                                raise C64PascalError(
                                    f"Ungültiges {{$%s}} (%s)." % (command, filename),
                                    line,
                                    0,
                                )
                            key = define_match.group(1).casefold()
                            if command == "undef":
                                self.macros.pop(key, None)
                            else:
                                value = (define_match.group(2) or "1").strip()
                                if "\n" in value or "\r" in value:
                                    raise C64PascalError(
                                        "Pascal-Makrowerte dürfen keine Zeilenumbrüche enthalten.",
                                        line,
                                        0,
                                    )
                                self.macros[key] = value or "1"
                    elif command in {"l", "link", "linklib"}:
                        if was_active:
                            link_name = _expand_pascal_macros(
                                argument, self.macros
                            ).strip()
                            if (
                                len(link_name) >= 2
                                and link_name[0] == link_name[-1]
                                and link_name[0] in {"'", '"'}
                            ):
                                link_name = link_name[1:-1]
                            if not link_name:
                                raise C64PascalError(
                                    "{$L}/{$LINK}/{$LINKLIB} erwartet eine Datei.",
                                    line,
                                    0,
                                )
                            allowed = (
                                {".a", ".lib"}
                                if command == "linklib"
                                else {".o", ".obj", ".a", ".lib"}
                            )
                            source_candidate = Path(link_name).expanduser()
                            if source_candidate.suffix.casefold() not in allowed:
                                raise C64PascalError(
                                    (
                                        "{$LINKLIB} erwartet .a/.lib: "
                                        if command == "linklib"
                                        else "{$L}/{$LINK} erwartet .o/.obj/.a/.lib: "
                                    )
                                    + link_name
                                    + ".",
                                    line,
                                    0,
                                )
                            candidates: List[Path] = []
                            if source_candidate.is_absolute():
                                candidates.append(source_candidate)
                            else:
                                try:
                                    source_path = Path(filename).expanduser()
                                    base_dir = (
                                        source_path.resolve().parent
                                        if not str(filename).startswith("<")
                                        else Path.cwd()
                                    )
                                except (OSError, RuntimeError, ValueError):
                                    base_dir = Path.cwd()
                                candidates.append(base_dir / source_candidate)
                                candidates.extend(
                                    directory / source_candidate
                                    for directory in self.link_search_paths
                                )
                            chosen = next(
                                (path for path in candidates if path.is_file()),
                                candidates[0],
                            )
                            try:
                                link_path = chosen.resolve()
                            except (OSError, RuntimeError):
                                link_path = chosen.absolute()
                            key = str(link_path).casefold()
                            if all(str(Path(item)).casefold() != key for item in self.link_files):
                                self.link_files.append(str(link_path))
                            if all(str(Path(item)).casefold() != key for item in process_link_files):
                                process_link_files.append(str(link_path))
                    elif command in {"info", "warn", "warning", "error"}:
                        if was_active:
                            message = _expand_pascal_macros(
                                argument,
                                self.macros,
                            ).strip()
                            if len(message) >= 2 and message[0] == message[-1] == "'":
                                message = message[1:-1].replace("''", "'")
                            message = message or f"{{$%s}}" % command
                            if command == "error":
                                raise C64PascalError(
                                    f"{filename}: {message}",
                                    line,
                                    0,
                                )
                            diagnostic = PascalPreprocessorDiagnostic(
                                "info" if command == "info" else "warning",
                                message,
                                filename,
                                line,
                            )
                            if command == "info":
                                self.notes.append(diagnostic)
                            else:
                                self.warnings.append(diagnostic)
                    else:
                        raise C64PascalError(
                            f"Unbekannte Pascal-Direktive {{$%s}} (%s)." % (raw, filename),
                            line,
                            0,
                        )
                    output.append(self._blank(text[index:end + 1]))
                    index = end
                    segment_start = end + 1
                elif character == "{":
                    state = "brace_comment"
                elif character == "(" and following == "*":
                    state = "paren_comment"
                    index += 1
                elif character == "/" and following == "/":
                    state = "line_comment"
                    index += 1
            elif state == "string":
                if character == "'":
                    if following == "'":
                        index += 1
                    else:
                        state = "code"
            elif state == "brace_comment":
                if character == "}":
                    state = "code"
            elif state == "paren_comment":
                if character == "*" and following == ")":
                    state = "code"
                    index += 1
            elif character == "\n":
                state = "code"
            index += 1

        flush(len(text))
        if frames:
            raise C64PascalError(
                f"Fehlendes {{$endif}} am Dateiende ({filename})."
            )
        return PascalPreprocessResult(
            source="".join(output),
            macros=dict(self.macros),
            notes=tuple(self.notes),
            warnings=tuple(self.warnings),
            link_files=tuple(process_link_files),
        )


def preprocess_pascal_source(
    source: str,
    *,
    filename: str = "<Pascal-Editor>",
    predefined_macros: Optional[Dict[str, Union[str, int, bool]]] = None,
) -> PascalPreprocessResult:
    return PascalPreprocessor(predefined_macros).process(
        source,
        filename=filename,
    )


def _blank_pascal_segment(source: str, start: int, end: int) -> str:
    return (
        source[:start]
        + "".join("\n" if character == "\n" else " " for character in source[start:end])
        + source[end:]
    )


def _unit_names(text: str, *, filename: str, line: int) -> Tuple[str, ...]:
    names = []
    for item in text.split(","):
        name = item.strip()
        if not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*",
            name,
        ):
            raise C64PascalError(
                f"Ungültiger Unit-Name in USES: {name or item!r} ({filename}).",
                line,
                0,
            )
        names.append(name)
    return tuple(names)


def _extract_uses_after(
    source: str,
    start: int,
    *,
    filename: str,
) -> Tuple[str, Tuple[str, ...], int]:
    mask = _pascal_code_mask(source)
    cursor = int(start)
    while cursor < len(mask) and mask[cursor].isspace():
        cursor += 1
    match = re.match(r"uses\b", mask[cursor:], re.IGNORECASE)
    if match is None:
        return source, (), start
    uses_start = cursor
    semicolon = mask.find(";", cursor + match.end())
    if semicolon < 0:
        line = source.count("\n", 0, uses_start) + 1
        raise C64PascalError(
            f"USES-Klausel ohne abschließendes Semikolon ({filename}).",
            line,
            0,
        )
    names_text = source[cursor + match.end():semicolon]
    line = source.count("\n", 0, uses_start) + 1
    names = _unit_names(names_text, filename=filename, line=line)
    return (
        _blank_pascal_segment(source, uses_start, semicolon + 1),
        names,
        semicolon + 1,
    )


def _pascal_source_kind(source: str) -> str:
    """Ermittelt den Typ der obersten Pascal-Quelldatei."""
    mask = _pascal_code_mask(source)
    match = re.match(
        r"\s*(program|unit|library)\b",
        mask,
        re.IGNORECASE,
    )
    return match.group(1).casefold() if match is not None else "program"


def _extract_program_uses(
    source: str,
    *,
    filename: str,
) -> Tuple[str, Tuple[str, ...]]:
    mask = _pascal_code_mask(source)
    header = re.search(r"\bprogram\b", mask, re.IGNORECASE)
    if header is None:
        return source, ()
    semicolon = mask.find(";", header.end())
    if semicolon < 0:
        return source, ()
    cleaned, names, unused_end = _extract_uses_after(
        source,
        semicolon + 1,
        filename=filename,
    )
    return cleaned, names


def _generated_parser_supports_rule(rule_name: str) -> bool:
    return hasattr(C64PascalParser, f"RULE_{str(rule_name)}")


def _generated_lexer_supports_token(token_name: str) -> bool:
    return hasattr(C64PascalLexer, str(token_name))


def _legacy_generated_parser_requires_bridge(rule_name: str = "subrangeType") -> bool:
    """Return True when the loaded generated ANTLR files lack one feature.

    Older stages used only RULE_subrangeType as a global version probe.  That is
    insufficient after incremental grammar extensions: a generated parser can
    know subranges while still predating PROPERTY or INHERITED.  Stage 182
    therefore probes every feature independently.
    """
    return not _generated_parser_supports_rule(rule_name)


def _blank_pascal_span(source: str, start: int, end: int) -> str:
    fragment = source[start:end]
    replacement = "".join(
        "\n" if ch == "\n" else "\r" if ch == "\r" else " "
        for ch in fragment
    )
    return source[:start] + replacement + source[end:]


def _legacy_integer_value(text: str) -> int:
    value = str(text).strip()
    sign = 1
    if value.startswith("+"):
        value = value[1:].strip()
    elif value.startswith("-"):
        sign = -1
        value = value[1:].strip()
    if value.startswith("$"):
        return sign * int(value[1:], 16)
    if value.startswith("%"):
        return sign * int(value[1:], 2)
    return sign * int(value, 10)



def _rewrite_raise_statements(source: str) -> Tuple[str, bool]:
    """Lower Object-Pascal ``raise`` before legacy ANTLR files see it.

    Some generated C64PascalLexer/Parser copies predate the RAISE token/rule.
    The rewrite is deliberately syntax-preserving at the semantic level:

        raise Exception.Create('text');

    becomes

        __d64_raise(Exception.Create('text'));

    and is converted straight back into :class:`RaiseStatement` by
    ``_AstBuilder``. Strings and comments are protected by ``_pascal_code_mask``
    and physical line numbers are preserved.
    """
    working = str(source)
    mask = _pascal_code_mask(working)
    matches = list(re.finditer(r"\braise\b", mask, re.IGNORECASE))
    if not matches:
        return working, False

    spans = []
    for match in matches:
        cursor = match.end()
        paren_depth = 0
        bracket_depth = 0
        while cursor < len(mask):
            ch = mask[cursor]
            if ch == "(":
                paren_depth += 1
            elif ch == ")":
                if paren_depth > 0:
                    paren_depth -= 1
            elif ch == "[":
                bracket_depth += 1
            elif ch == "]":
                if bracket_depth > 0:
                    bracket_depth -= 1
            elif ch == ";" and paren_depth == 0 and bracket_depth == 0:
                break
            cursor += 1
        if cursor >= len(mask):
            line = mask.count("\n", 0, match.start()) + 1
            raise C64PascalError(
                "RAISE-Anweisung ohne abschließendes Semikolon.",
                line,
                0,
            )
        expression = working[match.end():cursor].strip()
        replacement = (
            "__d64_raise(" + expression + ")"
            if expression
            else "__d64_reraise()"
        )
        spans.append((match.start(), cursor, replacement))

    for start, end, replacement in reversed(spans):
        # Keep the original semicolon at ``end``.
        working = working[:start] + replacement + working[end:]
    return working, True


def _rewrite_try_statements(source: str) -> Tuple[str, bool]:
    """Lower TRY/EXCEPT and TRY/FINALLY for generated parsers that predate them.

    The replacement is line-neutral.  Each TRY becomes a synthetic compound
    statement with marker calls.  After ANTLR has built the ordinary AST,
    :func:`_restore_legacy_try_statement` turns those markers back into a real
    :class:`TryStatement`.
    """
    working = str(source)
    mask = _pascal_code_mask(working)
    token_re = re.compile(
        r"\b(begin|case|record|class|try|except|finally|end)\b",
        re.IGNORECASE,
    )
    stack = []
    completed = []
    next_id = 1

    for match in token_re.finditer(mask):
        word = match.group(1).casefold()
        if word in {"begin", "case", "record", "class"}:
            stack.append({"kind": word, "start": match.start()})
            continue
        if word == "try":
            item = {
                "kind": "try",
                "start": match.start(),
                "id": next_id,
                "split_kind": None,
                "split": None,
            }
            next_id += 1
            stack.append(item)
            continue
        if word in {"except", "finally"}:
            if not stack or stack[-1].get("kind") != "try":
                continue
            item = stack[-1]
            if item.get("split_kind") is not None:
                line = mask.count("\n", 0, match.start()) + 1
                raise C64PascalError(
                    "TRY darf entweder EXCEPT oder FINALLY besitzen, nicht beides.",
                    line,
                    0,
                )
            item["split_kind"] = word
            item["split"] = match.start()
            continue
        if word == "end" and stack:
            item = stack.pop()
            if item.get("kind") != "try":
                continue
            if item.get("split_kind") is None:
                line = mask.count("\n", 0, item["start"]) + 1
                raise C64PascalError(
                    "TRY erwartet EXCEPT oder FINALLY.",
                    line,
                    0,
                )
            item["end"] = match.start()
            completed.append(item)

    if not completed:
        return working, False

    replacements = []
    for item in completed:
        ident = int(item["id"])
        replacements.extend((
            (item["start"], item["start"] + 3,
             f"begin __d64_try_begin({ident});"),
            (item["split"], item["split"] + len(item["split_kind"]),
             f"__d64_try_{item['split_kind']}({ident});"),
            (item["end"], item["end"] + 3,
             f"__d64_try_end({ident}); end"),
        ))
    for start, end, text in sorted(replacements, reverse=True):
        working = working[:start] + text + working[end:]
    return working, True


def _legacy_try_marker(statement: Statement) -> Optional[Tuple[str, int]]:
    if not isinstance(statement, CallStatement):
        return None
    designator = statement.designator
    if not isinstance(designator, DesignatorExpression) or designator.selectors:
        return None
    name = designator.name.casefold()
    prefix = "__d64_try_"
    if not name.startswith(prefix) or len(statement.arguments) != 1:
        return None
    argument = statement.arguments[0]
    if not isinstance(argument, LiteralExpression) or not isinstance(argument.value, int):
        return None
    return name[len(prefix):], int(argument.value)


def _restore_legacy_try_statement(statement: Statement) -> Statement:
    """Restore synthetic TRY marker compounds recursively."""
    if isinstance(statement, CompoundStatement):
        children = tuple(_restore_legacy_try_statement(item) for item in statement.statements)
        if len(children) >= 3:
            first = _legacy_try_marker(children[0])
            last = _legacy_try_marker(children[-1])
            if first is not None and first[0] == "begin" and last == ("end", first[1]):
                split_index = None
                split_kind = None
                for index, child in enumerate(children[1:-1], 1):
                    marker = _legacy_try_marker(child)
                    if marker in {("except", first[1]), ("finally", first[1])}:
                        split_index = index
                        split_kind = marker[0]
                        break
                if split_index is not None:
                    return TryStatement(
                        statement.position,
                        tuple(children[1:split_index]),
                        str(split_kind),
                        tuple(children[split_index + 1:-1]),
                    )
        return replace(statement, statements=children)
    if isinstance(statement, IfStatement):
        return replace(
            statement,
            then_statement=_restore_legacy_try_statement(statement.then_statement),
            else_statement=(
                _restore_legacy_try_statement(statement.else_statement)
                if statement.else_statement is not None else None
            ),
        )
    if isinstance(statement, WhileStatement):
        return replace(statement, body=_restore_legacy_try_statement(statement.body))
    if isinstance(statement, RepeatStatement):
        return replace(
            statement,
            statements=tuple(_restore_legacy_try_statement(item) for item in statement.statements),
        )
    if isinstance(statement, ForStatement):
        return replace(statement, body=_restore_legacy_try_statement(statement.body))
    return statement


def _restore_legacy_try_program(program: PascalProgram) -> PascalProgram:
    return replace(
        program,
        body=_restore_legacy_try_statement(program.body),
        methods=tuple(
            replace(method, body=_restore_legacy_try_statement(method.body))
            for method in program.methods
        ),
        global_routines=tuple(
            replace(routine, body=_restore_legacy_try_statement(routine.body))
            for routine in program.global_routines
        ),
    )


def _rewrite_address_of_uses(source: str) -> Tuple[str, bool]:
    """Lower Object-Pascal ``@Routine`` before the legacy lexer sees ``@``.

    The Stage-202 bundled C64PascalLexer predates the AT token even though the
    repository PascalLexer grammar already knows it.  Only code regions are
    rewritten; strings and all supported comment forms are masked first.

    ``@GlobalWindowProc`` becomes
    ``__d64_addressof(GlobalWindowProc)``.  _AstBuilder immediately converts
    that internal call into AddressOfExpression, so it remains a routine address
    and is never compiled as an ordinary function invocation.
    """
    working = str(source)
    mask = _pascal_code_mask(working)
    pattern = re.compile(
        r"@\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\s*\.\s*[A-Za-z_][A-Za-z0-9_]*)*)"
    )
    matches = list(pattern.finditer(mask))
    if not matches:
        return working, False
    for match in reversed(matches):
        raw_name = working[match.start("name"):match.end("name")]
        compact_name = re.sub(r"\s+", "", raw_name)
        replacement = "__d64_addressof(" + compact_name + ")"
        working = working[:match.start()] + replacement + working[match.end():]
    return working, True


def _rewrite_pointer_dereference_uses(source: str) -> Tuple[str, bool]:
    """Lower ``Pointer^.Field`` / ``Pointer^[Index]`` for legacy ANTLR files.

    The checked-in C64 parser predates postfix pointer dereference in a designator.
    We replace only a caret that is immediately followed by a selector (dot or
    bracket), leaving typed-pointer declarations such as ``PRec = ^TRec`` and
    Stage-201 ``TRec^`` declaration syntax untouched.  Strings/comments are
    protected by ``_pascal_code_mask``.

    ``P^.X`` becomes ``P.__d64_deref.X``.  _AstBuilder translates that internal
    selector back into DereferenceSelector, so no semantic information is lost.
    """
    working = str(source)
    mask = _pascal_code_mask(working)
    matches = list(re.finditer(r"\^(?=\s*[.\[])", mask))
    if not matches:
        return working, False
    for match in reversed(matches):
        working = (
            working[:match.start()]
            + ".__d64_deref"
            + working[match.end():]
        )
    return working, True


def _anonymous_pointer_alias(target_type_name: str) -> str:
    """Return a deterministic internal name for an anonymous typed pointer."""
    target = str(target_type_name or "").strip()
    safe = re.sub(r"[^A-Za-z0-9_]", "_", target)
    return "__d64_ptr_" + (safe or "anonymous")


def _anonymous_pointer_type_text(type_text: str) -> Tuple[str, Optional[str]]:
    """Normalize ``TFoo^`` / ``^TFoo`` and return (type_name, pointer_target)."""
    text = str(type_text or "").strip()
    prefix = re.fullmatch(r"\^\s*([A-Za-z_][A-Za-z0-9_.]*)", text)
    if prefix is not None:
        target = prefix.group(1)
        return _anonymous_pointer_alias(target), target.casefold()
    postfix = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_.]*)\s*\^", text)
    if postfix is not None:
        target = postfix.group(1)
        return _anonymous_pointer_alias(target), target.casefold()
    return text, None


def _rewrite_anonymous_pointer_type_uses(
    source: str,
) -> Tuple[str, Tuple[TypeDeclaration, ...]]:
    """Lower anonymous typed pointers in declaration type positions before ANTLR.

    Accepted compact spellings are ``TFoo^`` and ``^TFoo``.  They are replaced
    with deterministic internal aliases and accompanied by real
    ``PointerTypeSpecification`` nodes, so the semantic layer keeps the target
    type instead of degrading the declaration to an untyped Pointer.
    """
    working = str(source)
    code_mask = _pascal_code_mask(working)
    pattern = re.compile(
        r"(?P<leader>:\s*)"
        r"(?:"
        r"\^\s*(?P<prefix>[A-Za-z_][A-Za-z0-9_.]*)"
        r"|"
        r"(?P<postfix>[A-Za-z_][A-Za-z0-9_.]*)\s*\^"
        r")",
        re.IGNORECASE,
    )
    matches = list(pattern.finditer(code_mask))
    if not matches:
        return working, ()

    declarations_by_key = {}
    for match in matches:
        target = match.group("prefix") or match.group("postfix")
        if not target:
            continue
        alias = _anonymous_pointer_alias(target)
        key = alias.casefold()
        if key not in declarations_by_key:
            line = code_mask.count("\n", 0, match.start()) + 1
            last_newline = code_mask.rfind("\n", 0, match.start())
            column = match.start() - last_newline
            position = SourcePosition(line, max(1, column))
            declarations_by_key[key] = TypeDeclaration(
                alias,
                PointerTypeSpecification(position, target.casefold()),
                position,
            )

    for match in reversed(matches):
        target = match.group("prefix") or match.group("postfix")
        if not target:
            continue
        alias = _anonymous_pointer_alias(target)
        replacement = match.group("leader") + alias
        working = working[:match.start()] + replacement + working[match.end():]

    return working, tuple(declarations_by_key.values())


def _legacy_parameter_declarations(
    text: str,
    *,
    position: SourcePosition,
) -> Tuple[ParameterDeclaration, ...]:
    result: List[ParameterDeclaration] = []
    if not str(text or "").strip():
        return ()
    for group in filter(None, (item.strip() for item in str(text).split(";"))):
        match = re.fullmatch(
            r"(?is)(?:(const|var)\s+)?"
            r"([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)"
            r"\s*:\s*(\^\s*[A-Za-z_][A-Za-z0-9_.]*|[A-Za-z_][A-Za-z0-9_.]*\s*\^?)",
            group,
        )
        if match is None:
            raise C64PascalError(
                f"Ungültige Parameterdeklaration: {group}.",
                position.line,
                position.column - 1,
            )
        modifier = (match.group(1) or "value").casefold()
        normalized_type, pointer_target = _anonymous_pointer_type_text(match.group(3))
        type_name = ("pointer" if pointer_target is not None else normalized_type).casefold()
        for raw_name in match.group(2).split(","):
            result.append(
                ParameterDeclaration(
                    (raw_name.strip(),),
                    type_name,
                    modifier,
                    position,
                )
            )
    return tuple(result)


def _legacy_pascal_extension_bridge(
    source: str,
) -> Tuple[
    str,
    Tuple[TypeDeclaration, ...],
    Tuple[ExternalRoutineDeclaration, ...],
    Tuple[Tuple[str, PropertyDeclaration], ...],
    Tuple[Tuple[int, Optional[str]], ...],
    Tuple[Tuple[str, str, int, Optional[str]], ...],
]:
    """Adapt current Object-Pascal syntax to older generated ANTLR files.

    Capability checks are feature-specific.  This lets a Stage-178 generated
    parser (for example) use Stage-182 compiler.py even though it has subranges
    and Pointer(Self) but does not yet know PROPERTY or INHERITED.
    """
    needs_bootstrap = _legacy_generated_parser_requires_bridge("subrangeType")
    needs_property = (
        _legacy_generated_parser_requires_bridge("propertyDeclaration")
        or not _generated_lexer_supports_token("PROPERTY")
    )
    needs_inherited = (
        _legacy_generated_parser_requires_bridge("inheritedStatement")
        or not _generated_lexer_supports_token("INHERITED")
    )
    # Stage 208: some generated parser copies already know INHERITED as a
    # statement but still reject it in expression position, e.g.
    # `Result := inherited GetWindowStyle or WS_TABSTOP;`.  Probe that rule
    # independently and lower named inherited calls when required.
    needs_inherited_expression = (
        _legacy_generated_parser_requires_bridge("inheritedExpression")
    )
    needs_global_routine = (
        _legacy_generated_parser_requires_bridge("globalRoutineImplementation")
        or _legacy_generated_parser_requires_bridge("globalRoutineCallingConvention")
        or not _generated_lexer_supports_token("CDECL")
        or not _generated_lexer_supports_token("STDCALL")
    )
    needs_external_routine = (
        _legacy_generated_parser_requires_bridge("globalRoutineDeclaration")
        or _legacy_generated_parser_requires_bridge("externalImportSpecification")
        or not _generated_lexer_supports_token("CDECL")
        or not _generated_lexer_supports_token("STDCALL")
        or not _generated_lexer_supports_token("EXTERNAL")
        or not _generated_lexer_supports_token("NAME")
    )

    # Stage 226: generated parser copies before TRY/EXCEPT/FINALLY see TRY as
    # an ordinary identifier. Lower it to a synthetic compound before ANTLR.
    needs_try_bridge = (
        _legacy_generated_parser_requires_bridge("tryStatement")
        or not _generated_lexer_supports_token("TRY")
        or not _generated_lexer_supports_token("EXCEPT")
        or not _generated_lexer_supports_token("FINALLY")
    )
    working = str(source)
    if needs_try_bridge:
        working, unused_try_rewritten = _rewrite_try_statements(working)

    # Stage 207: lower RAISE before old generated lexer/parser copies see it.
    working, needs_raise = _rewrite_raise_statements(working)

    # Stage 201: formal parameters, fields, properties and local variables can
    # use compact anonymous typed pointers (TFoo^ / ^TFoo). The checked-in
    # generated parser only accepts an identifier at these declaration sites.
    working, anonymous_pointer_types = _rewrite_anonymous_pointer_type_uses(working)
    needs_anonymous_pointer = bool(anonymous_pointer_types)

    # Stage 202: expression designators such as CreateStruct^.lpCreateParams
    # need a real pointer-dereference selector even with the legacy parser.
    working, needs_pointer_dereference = _rewrite_pointer_dereference_uses(working)

    # Stage 203: the bundled legacy lexer does not recognize '@'. Lower it
    # before tokenization and reconstruct a real AddressOfExpression in AST.
    working, needs_address_of = _rewrite_address_of_uses(working)

    if not (
        needs_bootstrap
        or needs_property
        or needs_inherited
        or needs_inherited_expression
        or needs_global_routine
        or needs_external_routine
        or needs_anonymous_pointer
        or needs_pointer_dereference
        or needs_address_of
        or needs_raise
    ):
        return source, (), (), (), (), ()

    extracted_types: List[TypeDeclaration] = list(anonymous_pointer_types)
    extracted_externals: List[ExternalRoutineDeclaration] = []
    extracted_properties: List[Tuple[str, PropertyDeclaration]] = []
    inherited_markers: List[Tuple[int, Optional[str]]] = []
    global_routine_markers: List[Tuple[str, str, int, Optional[str]]] = []
    spans: List[Tuple[int, int]] = []

    # 1) Subrange and pointer type definitions. They are safe to identify by
    # their distinctive RHS syntax even without a full TYPE-section parser.
    if needs_bootstrap:
        type_pattern = re.compile(
            r"(?im)^[ \t]*"
            r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
            r"(?P<rhs>"
            r"[+-]?(?:\$[0-9A-Fa-f]+|%[01]+|[0-9]+)\s*\.\.\s*"
            r"[+-]?(?:\$[0-9A-Fa-f]+|%[01]+|[0-9]+)"
            r"|\^[ \t]*[A-Za-z_][A-Za-z0-9_.]*"
            r")\s*;"
        )
        for match in type_pattern.finditer(working):
            name = match.group("name")
            rhs = match.group("rhs").strip()
            line = working.count("\n", 0, match.start()) + 1
            position = SourcePosition(line, 1)
            if rhs.startswith("^"):
                target_name = rhs[1:].strip().casefold()
                specification: TypeSpecification = PointerTypeSpecification(
                    position,
                    target_name,
                )
            else:
                left_text, right_text = re.split(r"\s*\.\.\s*", rhs, maxsplit=1)
                specification = SubrangeTypeSpecification(
                    position,
                    LiteralExpression(position, _legacy_integer_value(left_text)),
                    LiteralExpression(position, _legacy_integer_value(right_text)),
                )
            extracted_types.append(TypeDeclaration(name, specification, position))
            spans.append((match.start(), match.end()))

    # 2) Global EXTERNAL declarations. This is feature-specific: a generated
    # parser may already know subranges/pointers while still predating the
    # CDECL/EXTERNAL global-routine grammar.
    if needs_external_routine:
        routine_pattern = re.compile(
            r"(?ims)^[ \t]*(?P<kind>procedure|function)\s+"
            r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*"
            r"(?:\((?P<params>[^)]*)\))?\s*"
            r"(?:\:\s*(?P<result>[A-Za-z_][A-Za-z0-9_.]*))?\s*;"
            r"(?P<calling>[ \t]*(?:cdecl|stdcall)\s*;[ \t]*(?:\r?\n)?)?"
            r"(?P<tail>"
            r"[ \t]*external\b"
            r"(?:\s+(?P<library>'(?:''|[^'])*'|[A-Za-z_][A-Za-z0-9_]*))?"
            r"(?:\s+name\s+(?P<member>'(?:''|[^'])*'))?"
            r"\s*;"
            r"|[ \t]*forward[ \t]*;"
            r")"
        )
        for match in routine_pattern.finditer(working):
            tail = match.group("tail") or ""
            if not re.match(r"(?is)\s*external\b", tail):
                continue
            line = working.count("\n", 0, match.start()) + 1
            position = SourcePosition(line, 1)
            name = match.group("name")
            calling_match = re.search(
                r"\b(cdecl|stdcall)\b",
                match.group("calling") or "",
                re.IGNORECASE,
            )
            calling_convention = (
                calling_match.group(1).casefold() if calling_match else None
            )
            raw_library = match.group("library")
            if raw_library and raw_library.startswith("'"):
                library_reference = raw_library[1:-1].replace("''", "'")
            else:
                library_reference = raw_library
            raw_member = match.group("member")
            import_name = (
                raw_member[1:-1].replace("''", "'")
                if raw_member
                else None
            )
            extracted_externals.append(
                ExternalRoutineDeclaration(
                    "",
                    match.group("kind").casefold(),
                    name,
                    _legacy_parameter_declarations(
                        match.group("params") or "",
                        position=position,
                    ),
                    match.group("result").casefold()
                    if match.group("result")
                    else None,
                    "_" + name if calling_convention == "cdecl" else name,
                    calling_convention,
                    library_reference,
                    import_name,
                )
            )
            spans.append((match.start(), match.end()))


        # Old parser reads method directives as field identifiers.
        directive_pattern = re.compile(
            r"(?im)\b(?:virtual|override)\s*;"
        )
        spans.extend((m.start(), m.end()) for m in directive_pattern.finditer(working))

    # 4) PROPERTY declarations for generated parsers predating Stage 179.
    if needs_property:
        mask = _pascal_code_mask(working)
        class_pattern = re.compile(
            r"(?is)\b(?P<class>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
            r"class(?:\s*\([^)]*\))?(?P<body>.*?)\bend\s*;"
        )
        property_pattern = re.compile(
            r"(?is)\bproperty\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
            r"(?:\s*\[(?P<params>[^]]*)\])?\s*:\s*"
            r"(?P<type>[A-Za-z_][A-Za-z0-9_.]*)"
            r"(?P<specs>[^;]*)\s*;"
        )
        for class_match in class_pattern.finditer(mask):
            body_start = class_match.start("body")
            body_text = class_match.group("body")
            class_name = class_match.group("class")
            for prop_match in property_pattern.finditer(body_text):
                start = body_start + prop_match.start()
                end = body_start + prop_match.end()
                line = working.count("\n", 0, start) + 1
                column = start - working.rfind("\n", 0, start)
                position = SourcePosition(line, column)
                specs = prop_match.group("specs") or ""
                read_match = re.search(
                    r"(?i)\bread\s+([A-Za-z_][A-Za-z0-9_.]*)", specs
                )
                write_match = re.search(
                    r"(?i)\bwrite\s+([A-Za-z_][A-Za-z0-9_.]*)", specs
                )
                index_parameters = _legacy_parameter_declarations(
                    prop_match.group("params") or "",
                    position=position,
                )
                extracted_properties.append((
                    class_name,
                    PropertyDeclaration(
                        prop_match.group("name"),
                        prop_match.group("type").casefold(),
                        read_match.group(1) if read_match else None,
                        write_match.group(1) if write_match else None,
                        position,
                        index_parameters,
                    ),
                ))
                spans.append((start, end))

    # 5) INHERITED compatibility bridge.  Stage 208 distinguishes statement
    # support from expression support.  A parser can already accept
    # `inherited Create;` while still rejecting
    # `Result := inherited GetWindowStyle or ...`.  Named inherited calls are
    # therefore lowered whenever either grammar form is missing; AST rewriting
    # restores direct-base dispatch after parsing.
    if needs_inherited or needs_inherited_expression:
        mask = _pascal_code_mask(working)
        inherited_pattern = re.compile(
            r"(?im)\binherited\b(?:[ \t]+(?P<name>[A-Za-z_][A-Za-z0-9_]*))?"
        )
        for match in inherited_pattern.finditer(mask):
            line = working.count("\n", 0, match.start()) + 1
            name = match.group("name")
            if name:
                inherited_markers.append((line, name))
                keyword_end = match.start() + len("inherited")
                spans.append((match.start(), keyword_end))
            elif needs_inherited:
                # Bare `inherited;`: replace the keyword with an equally long
                # identifier understood by every older statement grammar.
                inherited_markers.append((line, None))
                replacement = "_d64inh__"
                assert len(replacement) == len("inherited")
                working = (
                    working[:match.start()]
                    + replacement
                    + working[match.start() + len("inherited"):]
                )

    # Apply every position-based blanking operation before inserting any text
    # whose length differs from the original source. Stage187 inserted the
    # synthetic ``__D64GlobalRoutines.`` prefix first; that shifted all saved
    # EXTERNAL spans and could leave a stray ``cdecl``/``external`` token in
    # the old generated parser input.
    for start, end in sorted(set(spans), reverse=True):
        working = _blank_pascal_span(working, start, end)

    # 6) Free global PROCEDURE/FUNCTION implementations for generated parsers
    # predating Stage 183/189. The old grammar only knows ClassName.MethodName
    # implementations and cannot accept `cdecl;` between the routine signature
    # and BEGIN. Preserve that convention as AST metadata while blanking it from
    # the legacy parser stream.
    if needs_global_routine:
        mask = _pascal_code_mask(working)
        routine_re = re.compile(
            r"(?im)\b(?P<kind>procedure|function)\s+"
            r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b"
        )
        replacements: List[Tuple[int, int, str]] = []
        implementation_directive_spans: List[Tuple[int, int]] = []
        pending_markers: List[Tuple[str, str, int, Optional[str]]] = []
        for match in routine_re.finditer(mask):
            after_name = match.end("name")
            # Already a class-qualified implementation.
            if mask[after_name:].lstrip().startswith("."):
                continue
            header_end = _library_routine_header_end(mask, match.end())
            if header_end < 0:
                continue
            if not _looks_like_library_routine_implementation(mask, header_end):
                continue

            calling_convention: Optional[str] = None
            directive_match = re.match(
                r"(?is)\s*(?P<calling>(?:cdecl|stdcall)\s*;)",
                mask[header_end + 1:],
            )
            if directive_match is not None:
                calling_text = directive_match.group("calling")
                calling_convention = calling_text.split(";", 1)[0].strip().casefold()
                directive_start = header_end + 1 + directive_match.start("calling")
                directive_end = header_end + 1 + directive_match.end("calling")
                implementation_directive_spans.append((directive_start, directive_end))

            name = match.group("name")
            kind = match.group("kind").casefold()
            line = working.count("\n", 0, match.start()) + 1
            pending_markers.append((kind, name, line, calling_convention))
            replacements.append(
                (
                    match.start("name"),
                    match.end("name"),
                    "__D64GlobalRoutines." + name,
                )
            )

        # Blanking is length-preserving and therefore must happen before the
        # synthetic ClassName. prefix changes source offsets.
        for start, end in sorted(set(implementation_directive_spans), reverse=True):
            working = _blank_pascal_span(working, start, end)
        global_routine_markers.extend(pending_markers)
        for start, end, replacement in sorted(
            replacements, key=lambda item: item[0], reverse=True
        ):
            working = working[:start] + replacement + working[end:]

    return (
        working,
        tuple(extracted_types),
        tuple(extracted_externals),
        tuple(extracted_properties),
        tuple(inherited_markers),
        tuple(global_routine_markers),
    )


def _rewrite_legacy_inherited_expression(
    expression: Expression,
    markers: Dict[int, Optional[str]],
) -> Expression:
    """Restore direct-base dispatch after the legacy parser bridge.

    Named INHERITED expressions are blanked to an ordinary designator/call
    before tokenization.  Match only the marked source line and method name,
    then recurse through compound expressions so binary expressions such as
    `inherited GetWindowStyle or WS_TABSTOP` are reconstructed correctly.
    """
    marker = markers.get(expression.position.line, "__missing__")

    if isinstance(expression, CallExpression):
        designator = (
            expression.designator
            if isinstance(expression.designator, DesignatorExpression)
            else DesignatorExpression(expression.position, str(expression.designator), ())
        )
        if marker != "__missing__" and marker is not None:
            if (
                not designator.selectors
                and designator.name.casefold() == str(marker).casefold()
            ):
                return InheritedCallExpression(
                    expression.position,
                    marker,
                    tuple(
                        _rewrite_legacy_inherited_expression(arg, markers)
                        for arg in expression.arguments
                    ),
                )
        return replace(
            expression,
            arguments=tuple(
                _rewrite_legacy_inherited_expression(arg, markers)
                for arg in expression.arguments
            ),
        )

    if isinstance(expression, DesignatorExpression):
        if marker != "__missing__" and marker is not None:
            if (
                not expression.selectors
                and expression.name.casefold() == str(marker).casefold()
            ):
                return InheritedCallExpression(
                    expression.position, marker, ()
                )
        rewritten_selectors: List[DesignatorSelector] = []
        changed = False
        for selector in expression.selectors:
            if isinstance(selector, IndexSelector):
                rewritten = _rewrite_legacy_inherited_expression(
                    selector.expression, markers
                )
                if rewritten is not selector.expression:
                    changed = True
                    selector = replace(selector, expression=rewritten)
            rewritten_selectors.append(selector)
        return (
            replace(expression, selectors=tuple(rewritten_selectors))
            if changed
            else expression
        )

    if isinstance(expression, UnaryExpression):
        return replace(
            expression,
            operand=_rewrite_legacy_inherited_expression(
                expression.operand, markers
            ),
        )

    if isinstance(expression, BinaryExpression):
        return replace(
            expression,
            left=_rewrite_legacy_inherited_expression(expression.left, markers),
            right=_rewrite_legacy_inherited_expression(expression.right, markers),
        )

    if isinstance(expression, AddressOfExpression):
        return expression

    return expression


def _rewrite_legacy_inherited_statement(
    statement: Statement,
    markers: Dict[int, Optional[str]],
) -> Statement:
    if isinstance(statement, AssignmentStatement):
        return replace(
            statement,
            expression=_rewrite_legacy_inherited_expression(
                statement.expression, markers
            ),
        )
    if isinstance(statement, CallStatement):
        marker = markers.get(statement.position.line, "__missing__")
        designator = (
            statement.designator
            if isinstance(statement.designator, DesignatorExpression)
            else DesignatorExpression(statement.position, str(statement.designator), ())
        )
        if marker != "__missing__":
            expected = marker or "_d64inh__"
            if (
                not designator.selectors
                and designator.name.casefold() == str(expected).casefold()
            ):
                return InheritedCallStatement(
                    statement.position,
                    marker,
                    tuple(statement.arguments),
                )
        return replace(
            statement,
            arguments=tuple(
                _rewrite_legacy_inherited_expression(arg, markers)
                for arg in statement.arguments
            ),
        )
    if isinstance(statement, CompoundStatement):
        return replace(
            statement,
            statements=tuple(
                _rewrite_legacy_inherited_statement(item, markers)
                for item in statement.statements
            ),
        )
    if isinstance(statement, IfStatement):
        return replace(
            statement,
            condition=_rewrite_legacy_inherited_expression(
                statement.condition, markers
            ),
            then_statement=_rewrite_legacy_inherited_statement(
                statement.then_statement, markers
            ),
            else_statement=(
                _rewrite_legacy_inherited_statement(statement.else_statement, markers)
                if statement.else_statement is not None
                else None
            ),
        )
    if isinstance(statement, WhileStatement):
        return replace(
            statement,
            condition=_rewrite_legacy_inherited_expression(
                statement.condition, markers
            ),
            body=_rewrite_legacy_inherited_statement(statement.body, markers),
        )
    if isinstance(statement, RepeatStatement):
        return replace(
            statement,
            statements=tuple(
                _rewrite_legacy_inherited_statement(item, markers)
                for item in statement.statements
            ),
            condition=_rewrite_legacy_inherited_expression(
                statement.condition, markers
            ),
        )
    if isinstance(statement, ForStatement):
        return replace(
            statement,
            initial=_rewrite_legacy_inherited_expression(
                statement.initial, markers
            ),
            final=_rewrite_legacy_inherited_expression(
                statement.final, markers
            ),
            body=_rewrite_legacy_inherited_statement(statement.body, markers),
        )
    if isinstance(statement, RaiseStatement):
        return replace(
            statement,
            expression=(
                _rewrite_legacy_inherited_expression(statement.expression, markers)
                if statement.expression is not None
                else None
            ),
        )
    if isinstance(statement, TryStatement):
        return replace(
            statement,
            try_statements=tuple(
                _rewrite_legacy_inherited_statement(item, markers)
                for item in statement.try_statements
            ),
            handler_statements=tuple(
                _rewrite_legacy_inherited_statement(item, markers)
                for item in statement.handler_statements
            ),
        )

    return statement


def _parse_pascal_program(
    source: str,
    *,
    progress_callback: Optional[Callable[[str, int], None]] = None,
    progress_filename: str = "<Pascal-Editor>",
) -> PascalProgram:
    (
        parser_source,
        extra_types,
        extra_externals,
        extra_properties,
        inherited_markers,
        global_routine_markers,
    ) = _legacy_pascal_extension_bridge(source)
    listener = _RaisingErrorListener()
    lexer = C64PascalLexer(InputStream(parser_source))
    lexer.removeErrorListeners()
    lexer.addErrorListener(listener)
    parser = C64PascalParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(listener)
    tree = parser.compilationUnit()
    program = _AstBuilder(
        progress_callback=progress_callback,
        progress_filename=progress_filename,
    ).visit(tree)
    program = _restore_legacy_try_program(program)

    if global_routine_markers:
        marker_conventions = {
            (kind.casefold(), name.casefold(), int(line)): convention
            for kind, name, line, convention in global_routine_markers
        }
        marker_keys = set(marker_conventions)
        retained_methods: List[MethodImplementation] = []
        converted_globals: List[GlobalRoutineImplementation] = list(
            program.global_routines
        )
        for method in program.methods:
            key = (
                method.kind.casefold(),
                method.name.casefold(),
                int(method.position.line),
            )
            if (
                method.class_name.casefold() == "__d64globalroutines"
                and key in marker_keys
            ):
                converted_globals.append(
                    GlobalRoutineImplementation(
                        method.kind,
                        method.name,
                        method.parameters,
                        method.result_type_name,
                        method.local_variables,
                        method.body,
                        method.position,
                        marker_conventions.get(key),
                    )
                )
            else:
                retained_methods.append(method)
        program = replace(
            program,
            methods=tuple(retained_methods),
            global_routines=tuple(converted_globals),
        )

    if extra_properties:
        by_class: Dict[str, List[PropertyDeclaration]] = {}
        for class_name, declaration in extra_properties:
            by_class.setdefault(class_name.casefold(), []).append(declaration)
        rewritten_types: List[TypeDeclaration] = []
        for declaration in program.types:
            additions = by_class.get(declaration.name.casefold(), ())
            specification = declaration.specification
            if additions and isinstance(specification, ClassTypeSpecification):
                specification = replace(
                    specification,
                    properties=tuple(specification.properties) + tuple(additions),
                )
                declaration = replace(declaration, specification=specification)
            rewritten_types.append(declaration)
        program = replace(program, types=tuple(rewritten_types))

    if inherited_markers:
        markers = {line: name for line, name in inherited_markers}
        program = replace(
            program,
            body=_rewrite_legacy_inherited_statement(program.body, markers),
            methods=tuple(
                replace(
                    method,
                    body=_rewrite_legacy_inherited_statement(method.body, markers),
                )
                for method in program.methods
            ),
            global_routines=tuple(
                replace(
                    routine,
                    body=_rewrite_legacy_inherited_statement(routine.body, markers),
                )
                for routine in program.global_routines
            ),
        )

    if extra_types or extra_externals:
        program = replace(
            program,
            # Stage 192: a bootstrap type may arrive both from a partially
            # regenerated parser and from the legacy extraction bridge.
            types=_merge_pascal_type_declarations(program.types, extra_types),
            external_routines=(
                tuple(program.external_routines) + tuple(extra_externals)
            ),
        )
    return program


def _parse_pascal_program_with_progress(
    source: str,
    progress_callback: Optional[Callable[[str, int], None]],
    progress_filename: str,
) -> PascalProgram:
    """Kompatibilitätswrapper für Stage 198.

    Ohne Callback wird absichtlich die historische Ein-Argument-Signatur
    verwendet. Dadurch bleiben Stage-197-Tests und externe Monkeypatches, die
    ``_parse_pascal_program = lambda source: ...`` einsetzen, unverändert gültig.
    """
    if progress_callback is None:
        return _parse_pascal_program(source)
    return _parse_pascal_program(
        source,
        progress_callback=progress_callback,
        progress_filename=progress_filename,
    )


def _unit_source_declared_name(path: Path) -> Optional[str]:
    """Read only enough source metadata to verify a USES candidate identity.

    Stage 221: qualified units such as ``VCL.Windows`` must never silently bind
    to an unrelated basename-only ``Windows.pas`` from an earlier search root.
    The full parser is intentionally not involved here; this is only a cheap
    source-header identity check used by unit discovery.
    """
    try:
        source = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return None
    mask = _pascal_code_mask(source)
    match = re.search(
        r"\bunit\s+([A-Za-z_][A-Za-z0-9_.]*)\s*;",
        mask,
        re.IGNORECASE,
    )
    return match.group(1) if match else None


def _find_unit_file(unit_name: str, search_paths: Sequence[Path]) -> Optional[Path]:
    # Stage 221: inspect every source candidate in specificity order and accept
    # only a file whose declared UNIT name actually matches the USES name.
    # This keeps a legacy basename fallback possible (e.g. Windows.pas that
    # really declares VCL.Windows), while rejecting an unrelated ``unit Windows``.
    wanted = unit_name.casefold()
    for candidate in _find_unit_artifacts(
        unit_name, search_paths, (".pas", ".pp")
    ):
        declared = _unit_source_declared_name(candidate)
        if declared is None or declared.casefold() == wanted:
            return candidate
    return None


def _find_unit_artifacts(
    unit_name: str,
    search_paths: Sequence[Path],
    suffixes: Sequence[str],
) -> Tuple[Path, ...]:
    """Return matching artifacts with qualified-name specificity first.

    Stage 221 keeps search-path ordering *within* a specificity tier, but for a
    qualified USES name all exact qualified spellings are searched across every
    root before the basename fallback.  Therefore ``VCL.Windows`` prefers
    ``VCL/Windows.pas`` / ``VCL.Windows.pas`` over an earlier unrelated
    ``Windows.pas``.
    """
    dotted = unit_name.replace(".", "/")
    basename = unit_name.split(".")[-1]

    exact_names: List[str] = []
    fallback_names: List[str] = []
    for stem in (dotted, unit_name):
        for suffix in suffixes:
            candidate = f"{stem}{suffix}"
            if candidate not in exact_names:
                exact_names.append(candidate)
    for suffix in suffixes:
        candidate = f"{basename}{suffix}"
        if candidate not in exact_names and candidate not in fallback_names:
            fallback_names.append(candidate)

    result: List[Path] = []
    seen = set()

    def append_direct(relative_names: Sequence[str]) -> None:
        for directory in search_paths:
            if directory is None:
                continue
            for relative_name in relative_names:
                candidate = (Path(directory) / relative_name).resolve()
                key = str(candidate).casefold()
                if candidate.is_file() and key not in seen:
                    seen.add(key)
                    result.append(candidate)

    def append_casefolded(relative_names: Sequence[str]) -> None:
        wanted = {
            Path(name).name.casefold()
            for name in relative_names
            if "/" not in name
        }
        if not wanted:
            return
        for directory in search_paths:
            if directory is None:
                continue
            try:
                for candidate in Path(directory).iterdir():
                    resolved = candidate.resolve()
                    key = str(resolved).casefold()
                    if (
                        candidate.is_file()
                        and candidate.name.casefold() in wanted
                        and key not in seen
                    ):
                        seen.add(key)
                        result.append(resolved)
            except OSError:
                continue

    # Qualified paths/names first across all roots, basename only afterwards.
    append_direct(exact_names)
    append_casefolded(exact_names)
    append_direct(fallback_names)
    append_casefolded(fallback_names)
    return tuple(result)


def _find_unit_artifact(
    unit_name: str,
    search_paths: Sequence[Path],
    suffixes: Sequence[str],
) -> Optional[Path]:
    matches = _find_unit_artifacts(unit_name, search_paths, suffixes)
    return matches[0] if matches else None


def _unit_program_source(
    source: str,
    *,
    filename: str,
) -> Tuple[str, str, Tuple[str, ...], Tuple[str, ...], str, str]:
    mask = _pascal_code_mask(source)
    header = re.search(
        r"\bunit\s+([A-Za-z_][A-Za-z0-9_.]*)\s*;",
        mask,
        re.IGNORECASE,
    )
    if header is None:
        raise C64PascalError(f"Keine UNIT-Deklaration in {filename}.")
    unit_name = header.group(1)
    interface = re.search(
        r"\binterface\b",
        mask[header.end():],
        re.IGNORECASE,
    )
    if interface is None:
        raise C64PascalError(f"INTERFACE-Abschnitt fehlt in Unit {unit_name}.")
    interface_start = header.end() + interface.end()
    implementation = re.search(
        r"\bimplementation\b",
        mask[interface_start:],
        re.IGNORECASE,
    )
    if implementation is None:
        implementation_start = len(source)
        interface_end = len(source)
    else:
        interface_end = interface_start + implementation.start()
        implementation_start = interface_start + implementation.end()

    interface_source = source[interface_start:interface_end]
    cleaned_interface, interface_units, unused_end = _extract_uses_after(
        interface_source,
        0,
        filename=filename,
    )

    implementation_source = source[implementation_start:]
    implementation_mask = _pascal_code_mask(implementation_source)
    final_end = re.search(
        r"\bend\s*\.\s*\Z",
        implementation_mask,
        re.IGNORECASE,
    )
    if final_end is None:
        raise C64PascalError(f"Abschließendes END. fehlt in Unit {unit_name}.")
    implementation_source = implementation_source[:final_end.start()]
    cleaned_implementation, implementation_units, unused_end = _extract_uses_after(
        implementation_source,
        0,
        filename=filename,
    )
    # Bootstrap-Units wie System.Types.pas verwenden einen leeren
    # IMPLEMENTATION/BEGIN/END.-Block. Da END. oben bereits als Unit-Abschluss
    # entfernt wurde, bleibt hier nur BEGIN übrig; für das synthetische PROGRAM
    # wird dieser leere Initialisierungsblock vollständig ausgeblendet.
    if re.fullmatch(
        r"\s*begin\s*",
        _pascal_code_mask(cleaned_implementation),
        re.IGNORECASE,
    ):
        cleaned_implementation = _blank_pascal_segment(
            cleaned_implementation, 0, len(cleaned_implementation)
        )
    unsupported = re.search(
        r"\b(initialization|finalization)\b",
        _pascal_code_mask(cleaned_implementation),
        re.IGNORECASE,
    )
    if unsupported is not None:
        raise C64PascalError(
            f"{unsupported.group(1).upper()} wird in Unit {unit_name} noch nicht unterstützt."
        )

    safe_name = re.sub(r"[^A-Za-z0-9_]", "_", unit_name)
    # Interface-Prototypen bleiben fuer die PUI erhalten, werden aber im
    # synthetischen PROGRAM-Parse ausgeblendet. So ist eine freie
    # Implementierung eindeutig von ihrem Interface-Prototyp getrennt.
    parser_interface, unused_interface_routines = _pui_routine_information(
        unit_name, cleaned_interface
    )
    del unused_interface_routines
    transformed = (
        f"program __unit_{safe_name};\n"
        + parser_interface
        + "\n"
        + cleaned_implementation
        + "\nbegin\nend.\n"
    )
    return (
        transformed,
        unit_name,
        interface_units,
        implementation_units,
        cleaned_interface,
        cleaned_implementation,
    )


_PUI_FORMAT = "dBase2Many Pascal Unit Interface"
_PUI_VERSION = 1
_PUI_LEGACY_FORMAT = "d64pascal-pui"
_PUI_LEGACY_VERSION = 2


def _pascal_guard_macro(source: str) -> Optional[str]:
    opening = re.match(
        r"\s*\{\$ifndef\s+([A-Za-z_][A-Za-z0-9_]*)\s*\}",
        source,
        re.IGNORECASE,
    )
    if opening is None:
        return None
    name = opening.group(1)
    definition = re.match(
        rf"\s*\{{\$define\s+{re.escape(name)}(?:\s+(?:1|true))?\s*\}}",
        source[opening.end():],
        re.IGNORECASE,
    )
    if definition is None:
        return None
    if re.search(r"\{\$endif\s*\}\s*\Z", source, re.IGNORECASE) is None:
        return None
    return name



_PUI_ROUTINE_RE = re.compile(
    r"(?ims)^[ \t]*(?P<kind>procedure|function)\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*"
    r"(?:\((?P<params>.*?)\))?\s*"
    r"(?:\:\s*(?P<result>[A-Za-z_][A-Za-z0-9_.]*))?\s*;"
    r"(?P<calling>[ \t]*(?:cdecl|stdcall)\s*;[ \t]*(?:\r?\n)?)?"
    r"(?P<external>"
    r"[ \t]*external\b"
    r"(?:\s+(?P<library>'(?:''|[^'])*'|[A-Za-z_][A-Za-z0-9_]*))?"
    r"(?:\s+name\s+(?P<member>'(?:''|[^'])*'))?"
    r"\s*;"
    r")?"
    r"(?P<forward>[ \t]*forward[ \t]*;)?"
)



def _pui_parameter_information(text: str) -> List[Dict[str, object]]:
    result: List[Dict[str, object]] = []
    for group in filter(None, (item.strip() for item in text.split(';'))):
        match = re.fullmatch(
            r"(?is)(?:(const|var)\s+)?"
            r"([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)"
            r"\s*:\s*(\^\s*[A-Za-z_][A-Za-z0-9_.]*|[A-Za-z_][A-Za-z0-9_.]*\s*\^?)",
            group,
        )
        if match is None:
            raise C64PascalError(f"Ungültige PUI-Parameterdeklaration: {group}.")
        modifier = (match.group(1) or 'value').casefold()
        normalized_type, pointer_target = _anonymous_pointer_type_text(match.group(3))
        type_name = 'Pointer' if pointer_target is not None else normalized_type
        for name in match.group(2).split(','):
            result.append({
                'name': name.strip(),
                'type': type_name,
                'modifier': modifier,
            })
    return result


def _pui_class_spans(source: str) -> Tuple[Tuple[int, int], ...]:
    """Return CLASS..END spans in an interface section.

    Class method declarations are not global PUI routines. The former regex-only
    implementation accidentally stripped methods such as TObject.ClassType from
    System.Objects. This lightweight scanner works on the comment/string mask,
    so keywords inside comments or literals do not affect nesting.
    """
    mask = _pascal_code_mask(source)
    token_re = re.compile(r"\b(class|end)\b", re.IGNORECASE)
    stack: List[int] = []
    result: List[Tuple[int, int]] = []
    for match in token_re.finditer(mask):
        token = match.group(1).casefold()
        if token == "class":
            stack.append(match.start())
        elif stack:
            start = stack.pop()
            if not stack:
                result.append((start, match.end()))
    return tuple(result)


def _pui_routine_information(
    unit_name: str,
    interface_source: str,
) -> Tuple[str, List[Dict[str, object]]]:
    routines: List[Dict[str, object]] = []
    safe_unit = re.sub(r"[^A-Za-z0-9_]", "_", unit_name)
    class_spans = _pui_class_spans(interface_source)

    def inside_class(position: int) -> bool:
        return any(start <= position < end for start, end in class_spans)

    def replace_routine(match: re.Match[str]) -> str:
        if inside_class(match.start()):
            return match.group(0)
        kind = match.group("kind").casefold()
        name = match.group("name")
        parameters = _pui_parameter_information(match.group("params") or '')
        result_type = match.group("result") if kind == 'function' else None
        calling_match = re.search(
            r"\b(cdecl|stdcall)\b",
            match.group("calling") or "",
            re.IGNORECASE,
        )
        calling_convention = (
            calling_match.group(1).casefold() if calling_match else None
        )
        is_external = bool(match.group("external"))
        is_forward = bool(match.group("forward"))
        raw_library = match.group("library")
        if raw_library and raw_library.startswith("'"):
            library_reference = raw_library[1:-1].replace("''", "'")
        else:
            library_reference = raw_library
        raw_member = match.group("member")
        import_name = (
            raw_member[1:-1].replace("''", "'")
            if raw_member
            else None
        )
        directives = tuple(
            item
            for item in (
                calling_convention,
                "external" if is_external else None,
                "forward" if is_forward else None,
            )
            if item
        )
        routines.append({
            'kind': kind,
            'name': name,
            'parameters': parameters,
            'result_type': result_type,
            'symbol': f"__pas_{safe_unit}_{name}",
            'directives': directives,
            'calling_convention': calling_convention,
            'is_external': is_external,
            'library_reference': library_reference,
            'import_name': import_name,
        })
        return ''.join('\n' if char == '\n' else ' ' for char in match.group(0))

    parser_source = _PUI_ROUTINE_RE.sub(replace_routine, interface_source)
    return parser_source, routines


def _pui_interface_external_declarations(
    unit_name: str,
    routines: Sequence[Dict[str, object]],
) -> Tuple[ExternalRoutineDeclaration, ...]:
    """Convert metadata-only interface scans into semantic EXTERNAL declarations.

    Interface routine prototypes are intentionally blanked before the synthetic
    PROGRAM parser runs.  EXTERNAL imports still have to enter the code generator
    and linker, so they are reconstructed from the already parsed metadata rather
    than by synthesizing Pascal source.
    """
    result: List[ExternalRoutineDeclaration] = []
    position = SourcePosition(1, 1)
    for routine in routines:
        if not bool(routine.get("is_external")):
            continue
        parameters: List[ParameterDeclaration] = []
        for item in routine.get("parameters", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            type_name = str(item.get("type", "integer")).strip().casefold()
            modifier = str(item.get("modifier", "value")).strip().casefold() or "value"
            if name:
                parameters.append(
                    ParameterDeclaration((name,), type_name, modifier, position)
                )
        calling_convention = str(
            routine.get("calling_convention") or ""
        ).casefold() or None
        name = str(routine.get("name", ""))
        symbol = "_" + name if calling_convention == "cdecl" else name
        result.append(
            ExternalRoutineDeclaration(
                unit_name,
                str(routine.get("kind", "procedure")).casefold(),
                name,
                tuple(parameters),
                (
                    str(routine.get("result_type")).casefold()
                    if routine.get("result_type")
                    else None
                ),
                symbol,
                calling_convention,
                (
                    str(routine.get("library_reference"))
                    if routine.get("library_reference")
                    else None
                ),
                (
                    str(routine.get("import_name"))
                    if routine.get("import_name")
                    else None
                ),
            )
        )
    return tuple(result)


def _pui_resolve_library_reference(
    reference: Optional[str],
    semantic: Optional["_CodeGenerator"],
) -> Optional[str]:
    if not reference:
        return None
    text = str(reference).strip()
    if semantic is not None and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text):
        value = semantic.constants.get(text.casefold())
        if value is not None:
            if not isinstance(value, str):
                raise C64PascalError(
                    f"EXTERNAL-DLL-Konstante {text} muss eine Zeichenkette sein."
                )
            return value
    return text


def _pui_parameter_stack_bytes(
    routine: Dict[str, object],
    semantic: Optional["_CodeGenerator"],
) -> int:
    total = 0
    for item in routine.get("parameters", []):
        size = 4
        modifier = "value"
        type_info = None
        if isinstance(item, dict):
            modifier = str(item.get("modifier", "value") or "value").casefold()
            if semantic is not None:
                type_name = str(item.get("type", "integer")).casefold()
                try:
                    type_info = semantic._resolve_type(type_name, SourcePosition(1, 1))
                except C64PascalError:
                    type_info = None
                if type_info is not None:
                    size = 4 if type_info.kind == "class" else max(1, int(type_info.size))

        # Win32 VAR parameters carry the address of the caller's storage.
        # CONST records/arrays are likewise passed by address; using the record
        # byte size here would generate a wrong STDCALL decoration such as
        # _RegisterClassA@40 instead of _RegisterClassA@4.
        by_reference = modifier == "var" or (
            modifier == "const"
            and type_info is not None
            and type_info.kind in {"record", "array"}
        )
        if by_reference:
            size = 4

        total += max(4, (size + 3) & ~3)
    return total


def _pui_routine_link_symbol(
    unit_name: str,
    routine: Dict[str, object],
    *,
    target: str,
    semantic: Optional["_CodeGenerator"],
) -> str:
    name = str(routine.get("name", ""))
    if not bool(routine.get("is_external")):
        return f"__pas_{_pui_safe_unit_name(unit_name)}_{name}"
    target_info = _pui_target_information(target)
    if target_info.get("compiler_target") == "pe64":
        return name
    convention = str(routine.get("calling_convention") or "").casefold()
    if convention == "stdcall":
        return f"_{name}@{_pui_parameter_stack_bytes(routine, semantic)}"
    if convention == "cdecl":
        return "_" + name
    return name


def _pui_safe_unit_name(unit_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", str(unit_name))


def _pui_normalized_unit_name(unit_name: str) -> str:
    return _pui_safe_unit_name(unit_name).casefold()


def _pui_method_symbol(class_name: str, method_name: str) -> str:
    def safe(value: str) -> str:
        text = "".join(
            character.lower() if character.isalnum() else "_"
            for character in str(value)
        )
        return text or "value"
    return f"__pas_method_{safe(class_name)}_{safe(method_name)}"


def _pui_target_information(target: str) -> Dict[str, object]:
    normalized = str(target or "pe32").strip().casefold()
    if normalized in {"pe32", "win32", "windows", "windows-pe32"}:
        return {
            "target": "win32",
            "object_format": "coff32",
            "machine": "i386",
            "pointer_size": 4,
            "calling_convention": "cdecl",
            "compiler_target": "pe32",
        }
    if normalized in {"pe64", "win64", "windows64", "windows-pe64", "windows-pe32+"}:
        return {
            "target": "win64",
            "object_format": "coff64",
            "machine": "amd64",
            "pointer_size": 8,
            "calling_convention": "win64",
            "compiler_target": "pe64",
        }
    if normalized in {"amiga", "amiga500", "a500", "m68k", "68000"}:
        return {
            "target": "amiga",
            "object_format": "m68k-object",
            "machine": "m68000",
            "pointer_size": 4,
            "calling_convention": "register",
            "compiler_target": "amiga",
        }
    return {
        "target": "c64",
        "object_format": "mos6510-object",
        "machine": "mos6510",
        "pointer_size": 2,
        "calling_convention": "pascal",
        "compiler_target": "c64",
    }


def _pui_unit_object_filename(source_path: Optional[Path], target: str) -> Optional[str]:
    if source_path is None:
        return None
    info = _pui_target_information(target)
    compiler_target = str(info["compiler_target"])
    if compiler_target == "pe32":
        return source_path.stem + ".coff32.o"
    if compiler_target == "pe64":
        return source_path.stem + ".coff64.o"
    # C64/Amiga unit objects are not a stable standalone ABI in this compiler
    # stage; do not claim a binary artifact that is not actually emitted.
    return None


def _pui_parameter_metadata(parameter: ParameterDeclaration) -> Dict[str, object]:
    modifier = str(parameter.modifier or "value").casefold()
    return {
        "name": parameter.names[0] if parameter.names else "",
        "type": str(parameter.type_name).casefold(),
        "modifier": modifier,
        "is_var": modifier == "var",
        "is_const": modifier == "const",
    }


def _pui_property_metadata(property_declaration: PropertyDeclaration) -> Dict[str, object]:
    return {
        "name": property_declaration.name,
        "type": str(property_declaration.type_name).casefold(),
        "read": property_declaration.read_accessor,
        "write": property_declaration.write_accessor,
        "visibility": property_declaration.visibility,
        "index_params": [
            _pui_parameter_metadata(parameter)
            for parameter in property_declaration.index_parameters
        ],
    }


def _pui_externalize_class_methods(
    program: PascalProgram,
) -> PascalProgram:
    """Return a metadata-layout program whose class methods are ABI externals.

    PUI generation needs the compiler's real type-layout rules but must not
    require implementations for interface-declared methods. Marking those
    methods with their real COFF label lets _prepare_symbols resolve classes and
    sizes without generating method bodies.
    """
    declarations: List[TypeDeclaration] = []
    for declaration in program.types:
        specification = declaration.specification
        if isinstance(specification, ClassTypeSpecification):
            specification = replace(
                specification,
                methods=tuple(
                    replace(
                        method,
                        external_symbol=(
                            method.external_symbol
                            or _pui_method_symbol(declaration.name, method.name)
                        ),
                    )
                    for method in specification.methods
                ),
            )
            declaration = replace(declaration, specification=specification)
        declarations.append(declaration)
    return replace(
        program,
        types=tuple(declarations),
        methods=(),
        global_routines=(),
        external_routines=(),
    )


def _pui_semantic_layout(
    interface_program: PascalProgram,
    *,
    target: str,
    dependency_programs: Sequence[PascalProgram] = (),
) -> Optional["_CodeGenerator"]:
    """Resolve ABI sizes/offsets without embedding or retaining source text."""
    constants: List[ConstDeclaration] = []
    type_groups: List[Sequence[TypeDeclaration]] = []
    for dependency in dependency_programs:
        constants.extend(dependency.constants)
        type_groups.append(dependency.types)
    constants.extend(interface_program.constants)
    type_groups.append(interface_program.types)
    layout_program = PascalProgram(
        name="__pui_layout",
        constants=tuple(constants),
        variables=(),
        body=CompoundStatement(SourcePosition(1, 1), ()),
        types=_merge_pascal_type_scopes(
            tuple(type_groups[:-1]),
            tuple(type_groups[-1]) if type_groups else (),
        ),
    )
    layout_program = _pui_externalize_class_methods(layout_program)
    normalized = str(target or "pe32").strip().casefold()
    try:
        if normalized in {"pe32", "win32", "windows", "windows-pe32"}:
            generator: _CodeGenerator = _PE32CodeGenerator(
                layout_program,
                console_mode=False,
            )
        elif normalized in {
            "pe64", "win64", "windows64", "windows-pe64", "windows-pe32+"
        }:
            generator = _PE64CodeGenerator(layout_program, console_mode=False)
        else:
            generator = _CodeGenerator(layout_program)
        generator._prepare_symbols()
        return generator
    except C64PascalError:
        # Metadata creation must still work for a standalone interface whose
        # dependency PUI is not available yet. In that case sizes may be null,
        # but no source code is leaked as a fallback.
        return None


def _pui_constant_value(
    declaration: ConstDeclaration,
    semantic: Optional["_CodeGenerator"],
) -> object:
    if semantic is not None:
        key = declaration.name.casefold()
        if key in semantic.constants:
            return semantic.constants[key]
    expression = declaration.expression
    if isinstance(expression, LiteralExpression):
        return expression.value
    return None


def _pui_type_metadata(
    interface_program: PascalProgram,
    *,
    semantic: Optional["_CodeGenerator"],
    calling_convention: str,
) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    aliases: List[Dict[str, object]] = []
    subranges: List[Dict[str, object]] = []
    records: List[Dict[str, object]] = []
    enums: List[Dict[str, object]] = []
    arrays: List[Dict[str, object]] = []
    pointers: List[Dict[str, object]] = []
    classes: List[Dict[str, object]] = []

    for declaration in interface_program.types:
        specification = declaration.specification
        semantic_type = (
            semantic.types.get(declaration.name.casefold())
            if semantic is not None
            else None
        )
        if isinstance(specification, NamedTypeSpecification):
            aliases.append({
                "kind": "alias",
                "name": declaration.name,
                "target_type": specification.name,
            })
            continue
        if isinstance(specification, PointerTypeSpecification):
            pointers.append({
                "kind": "pointer",
                "name": declaration.name,
                "target_type": specification.target_type_name,
                "size": semantic_type.size if semantic_type is not None else None,
            })
            continue
        if isinstance(specification, SubrangeTypeSpecification):
            lower = semantic_type.lower_bound if semantic_type is not None else None
            upper = semantic_type.upper_bound if semantic_type is not None else None
            subranges.append({
                "kind": "subrange",
                "name": declaration.name,
                "lower": lower,
                "upper": upper,
                "size": semantic_type.size if semantic_type is not None else None,
                "signed": semantic_type.signed if semantic_type is not None else None,
            })
            continue
        if isinstance(specification, EnumTypeSpecification):
            enums.append({
                "kind": "enum",
                "name": declaration.name,
                "values": list(specification.names),
                "size": semantic_type.size if semantic_type is not None else None,
            })
            continue
        if isinstance(specification, ArrayTypeSpecification):
            arrays.append({
                "kind": "array",
                "name": declaration.name,
                "lower": semantic_type.lower_bound if semantic_type is not None else None,
                "upper": semantic_type.upper_bound if semantic_type is not None else None,
                "element_type": specification.element_type_name,
                "size": semantic_type.size if semantic_type is not None else None,
            })
            continue
        if isinstance(specification, RecordTypeSpecification):
            record_fields: List[Dict[str, object]] = []
            for field_declaration in specification.fields:
                for field_name in field_declaration.names:
                    field_info = (
                        semantic_type.fields.get(field_name.casefold())
                        if semantic_type is not None
                        else None
                    )
                    record_fields.append({
                        "name": field_name,
                        "type": field_declaration.type_name,
                        "offset": field_info.offset if field_info is not None else None,
                    })
            records.append({
                "kind": "record",
                "name": declaration.name,
                "size": semantic_type.size if semantic_type is not None else None,
                "fields": record_fields,
            })
            continue
        if not isinstance(specification, ClassTypeSpecification):
            continue

        # Private member names are intentionally not serialized. The aggregate
        # class size remains part of the ABI so derived-class layout still works.
        class_fields: List[Dict[str, object]] = []
        for field_declaration in specification.fields:
            if field_declaration.visibility == "private":
                continue
            for field_name in field_declaration.names:
                field_info = (
                    semantic_type.fields.get(field_name.casefold())
                    if semantic_type is not None
                    else None
                )
                class_fields.append({
                    "name": field_name,
                    "type": field_declaration.type_name,
                    "offset": field_info.offset if field_info is not None else field_declaration.offset,
                    "visibility": field_declaration.visibility,
                })

        class_methods: List[Dict[str, object]] = []
        for method in specification.methods:
            if method.visibility == "private":
                continue
            directives = {item.casefold() for item in method.directives}
            class_methods.append({
                "name": method.name,
                "kind": method.kind,
                "symbol": method.external_symbol or _pui_method_symbol(
                    declaration.name, method.name
                ),
                "params": [
                    _pui_parameter_metadata(parameter)
                    for parameter in method.parameters
                ],
                "return_type": method.result_type_name,
                "visibility": method.visibility,
                "calling_convention": calling_convention,
                "is_virtual": "virtual" in directives,
                "is_override": "override" in directives,
                "is_class_method": bool(method.is_class_method),
                # The current backend emits direct calls, not a physical VMT
                # table, so inventing an offset here would make the PUI lie.
                "vmt_offset": None,
            })

        class_properties = [
            _pui_property_metadata(property_declaration)
            for property_declaration in specification.properties
            if property_declaration.visibility != "private"
        ]
        parent = (
            semantic_type.base_type.name
            if semantic_type is not None and semantic_type.base_type is not None
            else specification.base_type_name
        )
        classes.append({
            "name": declaration.name,
            "parent": parent,
            "size": semantic_type.size if semantic_type is not None else specification.abi_size,
            "vmt_symbol": None,
            "class_name_symbol": None,
            "fields": class_fields,
            "methods": class_methods,
            "properties": class_properties,
        })

    return ({
        "aliases": aliases,
        "subranges": subranges,
        "records": records,
        "enums": enums,
        "arrays": arrays,
        "pointers": pointers,
    }, classes)


def _pui_import_metadata(
    full_program: Optional[PascalProgram],
    *,
    target: str = "pe32",
) -> Dict[str, object]:
    if full_program is None:
        return {}
    target_info = _pui_target_information(target)
    is_pe64 = target_info.get("compiler_target") == "pe64"
    result: Dict[str, object] = {}
    for routine in full_program.external_routines:
        # Public interface DLL imports are serialized from the interface scan
        # below, where DLL constants can be resolved against semantic metadata.
        # Avoid a second unresolved entry such as library="DLL_KERNEL32".
        if routine.unit_name and routine.library_reference:
            continue
        convention = str(routine.calling_convention or "").casefold() or None
        symbol = routine.symbol
        if is_pe64 and (
            convention in {"cdecl", "stdcall", "win64"}
            or symbol == "_" + routine.name
        ):
            symbol = routine.name
        member = PASCAL_MINIRUNTIME_IMPORTS.get(routine.name.casefold())
        if routine.library_reference:
            result[symbol] = {
                "kind": "dll",
                "library": routine.library_reference,
                "name": routine.import_name or routine.name,
                "pascal_name": routine.name,
                "calling_convention": "win64" if is_pe64 else (convention or "cdecl"),
            }
        elif member is not None:
            result[symbol] = {
                "kind": "dll",
                "library": PASCAL_MINIRUNTIME_DLL,
                "name": member,
                "pascal_name": routine.name,
                "calling_convention": "win64" if is_pe64 else (convention or "cdecl"),
            }
        else:
            result[symbol] = {
                "kind": "external",
                "name": routine.name,
                "calling_convention": "win64" if is_pe64 else (convention or "cdecl"),
            }
    return result


def _pui_portable_link_name(path_value: str) -> str:
    # Never serialize an absolute build-machine path into the interface. The
    # PUI directory and Stage185 project link-search paths are the resolution
    # contract.
    return Path(path_value).name


def _pui_document(
    *,
    unit_name: str,
    interface_source: str,
    interface_units: Sequence[str],
    implementation_units: Sequence[str] = (),
    source_path: Optional[Path],
    target: str = "pe32",
    full_program: Optional[PascalProgram] = None,
    dependency_programs: Sequence[PascalProgram] = (),
    link_files: Sequence[str] = (),
    macros: Optional[Dict[str, str]] = None,
) -> Dict[str, object]:
    """Create a metadata-only PUI.

    `interface_source` is parsed transiently and is never written to the JSON.
    This is deliberate information hiding: consumers receive the public ABI,
    type layout and link contract, not recoverable Pascal declarations.
    """
    safe_name = _pui_safe_unit_name(unit_name)
    parser_source, routines = _pui_routine_information(unit_name, interface_source)
    interface_program = _parse_pascal_program(
        f"program __pui_{safe_name};\n{parser_source}\nbegin\nend.\n"
    )
    semantic = _pui_semantic_layout(
        interface_program,
        target=target,
        dependency_programs=dependency_programs,
    )
    target_info = _pui_target_information(target)
    types, classes = _pui_type_metadata(
        interface_program,
        semantic=semantic,
        calling_convention=str(target_info["calling_convention"]),
    )

    functions: List[Dict[str, object]] = []
    procedures: List[Dict[str, object]] = []
    interface_imports: Dict[str, object] = {}
    for routine in routines:
        symbol = _pui_routine_link_symbol(
            unit_name, routine, target=target, semantic=semantic
        )
        effective_convention = (
            "win64"
            if target_info.get("compiler_target") == "pe64"
            else (
                str(routine.get("calling_convention") or "").casefold()
                or str(target_info["calling_convention"])
            )
        )
        entry = {
            "name": routine["name"],
            "kind": routine["kind"],
            "symbol": symbol,
            "params": [
                {
                    "name": item.get("name", ""),
                    "type": str(item.get("type", "integer")).casefold(),
                    "modifier": str(item.get("modifier", "value")).casefold(),
                    "is_var": str(item.get("modifier", "value")).casefold() == "var",
                    "is_const": str(item.get("modifier", "value")).casefold() == "const",
                }
                for item in routine.get("parameters", [])
                if isinstance(item, dict)
            ],
            "return_type": routine.get("result_type"),
            "calling_convention": effective_convention,
        }
        if bool(routine.get("is_external")):
            library = _pui_resolve_library_reference(
                routine.get("library_reference"), semantic
            )
            member = str(routine.get("import_name") or routine["name"])
            if library:
                interface_imports[symbol] = {
                    "kind": "dll",
                    "library": library,
                    "name": member,
                    "pascal_name": routine["name"],
                    "calling_convention": effective_convention,
                }
        (functions if routine["kind"] == "function" else procedures).append(entry)

    constants = []
    for declaration in interface_program.constants:
        value = _pui_constant_value(declaration, semantic)
        constants.append({
            "name": declaration.name,
            "value": value,
        })

    variables = [
        {
            "name": name,
            "type": declaration.type_name,
            "symbol": None,
        }
        for declaration in interface_program.variables
        for name in declaration.names
    ]

    object_name = _pui_unit_object_filename(source_path, target)
    object_info: Dict[str, object] = {
        "file": object_name,
        "format": target_info["object_format"],
        "machine": target_info["machine"],
    }

    link_objects: List[str] = []
    link_archives: List[str] = []
    for item in link_files:
        portable = _pui_portable_link_name(str(item))
        if Path(portable).suffix.casefold() in {".a", ".lib"}:
            if portable not in link_archives:
                link_archives.append(portable)
        elif portable not in link_objects:
            link_objects.append(portable)

    # Do not persist general compiler macro state. Only explicitly supplied
    # interface metadata should cross a unit boundary; currently there is no
    # exported-macro syntax, so the correct metadata set is empty.
    del macros
    return {
        "format": _PUI_FORMAT,
        "version": _PUI_VERSION,
        "unit": {
            "name": unit_name,
            "normalized_name": _pui_normalized_unit_name(unit_name),
        },
        # Stage206: keep the source fingerprint separate from any field named
        # ``source``.  Stage186 deliberately reserves source-bearing keys for
        # information-hiding checks; a SHA-256 is ABI/cache metadata, not source
        # text, but keeping it under a neutral block avoids schema ambiguity.
        "fingerprint": {
            "source_sha256": (
                _pui_source_sha256(source_path)
                if source_path is not None
                else None
            ),
        },
        "target": {
            "target": target_info["target"],
            "object_format": target_info["object_format"],
            "machine": target_info["machine"],
            "pointer_size": target_info["pointer_size"],
            "calling_convention": target_info["calling_convention"],
        },
        "object": object_info,
        "uses": {
            "interface": list(interface_units),
            "implementation": list(implementation_units),
        },
        "imports": {
            **_pui_import_metadata(full_program, target=target),
            **interface_imports,
        },
        "initialization": {
            "symbol": f"__unit_{safe_name}",
        },
        "finalization": {
            "symbol": None,
        },
        "constants": constants,
        "types": types,
        "symbols": {
            "functions": functions,
            "procedures": procedures,
            "classes": classes,
            "variables": variables,
        },
        "link": {
            "objects": link_objects,
            "archives": link_archives,
            "resources": [],
            "embedded_objects": [],
            "base_directory": "pui",
        },
        "macros": {},
    }


def _write_pui_document(path: Path, document: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(
            json.dumps(document, ensure_ascii=False, indent=4) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    except (OSError, TypeError, ValueError) as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise C64PascalError(f"PUI kann nicht geschrieben werden: {path}: {exc}") from exc


def _pui_is_legacy(document: Dict[str, object]) -> bool:
    return (
        document.get("format") == _PUI_LEGACY_FORMAT
        and document.get("version") == _PUI_LEGACY_VERSION
    )


def _pui_unit_name(document: Dict[str, object]) -> str:
    unit = document.get("unit")
    if isinstance(unit, dict):
        return str(unit.get("name", ""))
    return str(unit or "")


def _pui_uses(document: Dict[str, object]) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    if _pui_is_legacy(document):
        interface = document.get("interface")
        uses = interface.get("uses", []) if isinstance(interface, dict) else []
        return tuple(str(item) for item in uses), ()
    uses = document.get("uses")
    if not isinstance(uses, dict):
        return (), ()
    interface = uses.get("interface", [])
    implementation = uses.get("implementation", [])
    return (
        tuple(str(item) for item in interface if isinstance(item, str)),
        tuple(str(item) for item in implementation if isinstance(item, str)),
    )


def _pui_safe_stage205_source_fingerprint(value: object) -> bool:
    """Return True only for Stage205's source={sha256: ...} cache metadata.

    Stage205 introduced a source fingerprint but accidentally stored it below a
    key named ``source``.  Stage186 reserves that key because older PUIs used it
    for recoverable Pascal text.  Accept exactly the Stage205 fingerprint shape
    as a read-only migration input; no path, declaration or source text is
    permitted here.
    """
    if not isinstance(value, dict) or set(value) != {"sha256"}:
        return False
    digest = value.get("sha256")
    if digest is None:
        return True
    text = str(digest).strip()
    return bool(re.fullmatch(r"[0-9A-Fa-f]{64}", text))


def _pui_contains_source_payload(value: object) -> bool:
    forbidden = {
        "source",
        "interface_source",
        "declaration_source",
        "parser_source",
        "source_text",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = str(key).casefold()
            if normalized_key == "source" and _pui_safe_stage205_source_fingerprint(child):
                # Stage206 migration exception: SHA-256 only, never source text.
                continue
            if normalized_key in forbidden:
                return True
            if _pui_contains_source_payload(child):
                return True
    elif isinstance(value, list):
        return any(_pui_contains_source_payload(item) for item in value)
    return False


def _read_pui_document(path: Path, expected_unit: str) -> Dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise C64PascalError(f"PUI kann nicht gelesen werden: {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise C64PascalError(f"Ungültiges PUI-Format: {path}.")
    if _pui_is_legacy(document):
        # Read-only migration path. Regenerating this PUI writes Stage186's
        # metadata-only format and removes the embedded source permanently.
        declared = _pui_unit_name(document)
        if declared.casefold() != expected_unit.casefold():
            raise C64PascalError(
                f"PUI-Unit {declared or '<leer>'} passt nicht zu USES {expected_unit} ({path})."
            )
        return document
    if document.get("format") != _PUI_FORMAT or document.get("version") != _PUI_VERSION:
        raise C64PascalError(f"Nicht unterstütztes PUI-Format in {path}.")
    if _pui_contains_source_payload(document):
        raise C64PascalError(
            f"PUI {path} verletzt Information Hiding: Quelltextfeld gefunden."
        )
    declared = _pui_unit_name(document)
    if declared.casefold() != expected_unit.casefold():
        raise C64PascalError(
            f"PUI-Unit {declared or '<leer>'} passt nicht zu USES {expected_unit} ({path})."
        )
    interface_uses, implementation_uses = _pui_uses(document)
    del interface_uses, implementation_uses
    symbols = document.get("symbols")
    if not isinstance(symbols, dict):
        raise C64PascalError(f"PUI enthält keine gültigen Symbolmetadaten: {path}.")
    return document


def _pui_external_routines(
    document: Dict[str, object],
) -> Tuple[ExternalRoutineDeclaration, ...]:
    if _pui_is_legacy(document):
        interface = document.get("interface")
        raw_routines = interface.get("routines", []) if isinstance(interface, dict) else []
        unit_name = _pui_unit_name(document)
    else:
        symbols = document.get("symbols")
        if not isinstance(symbols, dict):
            return ()
        raw_routines = []
        for kind_key in ("functions", "procedures"):
            values = symbols.get(kind_key, [])
            if isinstance(values, list):
                raw_routines.extend(item for item in values if isinstance(item, dict))
        unit_name = _pui_unit_name(document)
    result: List[ExternalRoutineDeclaration] = []
    position = SourcePosition(1, 1)
    for raw in raw_routines:
        if not isinstance(raw, dict):
            continue
        kind = str(raw.get("kind", "procedure")).casefold()
        name = str(raw.get("name", ""))
        symbol = str(raw.get("symbol", ""))
        if not name or not symbol or kind not in {"procedure", "function"}:
            continue
        parameters: List[ParameterDeclaration] = []
        raw_parameters = raw.get("params", raw.get("parameters", []))
        if isinstance(raw_parameters, list):
            for item in raw_parameters:
                if not isinstance(item, dict):
                    continue
                parameter_name = str(item.get("name", ""))
                type_name = str(item.get("type", "integer")).casefold()
                modifier = str(item.get("modifier", "value")).casefold()
                if item.get("is_var") is True:
                    modifier = "var"
                elif item.get("is_const") is True:
                    modifier = "const"
                if parameter_name:
                    parameters.append(
                        ParameterDeclaration(
                            (parameter_name,),
                            type_name,
                            modifier,
                            position,
                        )
                    )
        result_name = raw.get("return_type", raw.get("result_type"))
        calling_convention = str(raw.get("calling_convention") or "").casefold() or None
        library_reference = None
        import_name = None
        imports = document.get("imports") if isinstance(document, dict) else None
        if isinstance(imports, dict):
            import_spec = imports.get(symbol)
            if import_spec is None:
                import_spec = next(
                    (value for key, value in imports.items() if str(key).casefold() == symbol.casefold()),
                    None,
                )
            if isinstance(import_spec, dict) and str(import_spec.get("kind", "")).casefold() == "dll":
                library_reference = str(import_spec.get("library") or "") or None
                import_name = str(import_spec.get("name") or name)
                calling_convention = (
                    str(import_spec.get("calling_convention") or calling_convention or "").casefold()
                    or None
                )
        result.append(
            ExternalRoutineDeclaration(
                unit_name,
                kind,
                name,
                tuple(parameters),
                str(result_name).casefold() if result_name else None,
                symbol,
                calling_convention,
                library_reference,
                import_name,
            )
        )
    return tuple(result)


def _pui_program_from_metadata(document: Dict[str, object]) -> PascalProgram:
    """Reconstruct only semantic declarations required by a consumer.

    No Pascal source is synthesized or parsed for Stage186 PUI files.
    """
    if _pui_is_legacy(document):
        interface = document.get("interface")
        source = interface.get("source", "") if isinstance(interface, dict) else ""
        safe = _pui_safe_unit_name(_pui_unit_name(document))
        return _parse_pascal_program(
            f"program __legacy_pui_{safe};\n{source}\nbegin\nend.\n"
        )

    position = SourcePosition(1, 1)
    type_declarations: List[TypeDeclaration] = []
    types = document.get("types")
    if isinstance(types, dict):
        for item in types.get("aliases", []) if isinstance(types.get("aliases", []), list) else []:
            if isinstance(item, dict) and item.get("name") and item.get("target_type"):
                type_declarations.append(TypeDeclaration(
                    str(item["name"]),
                    NamedTypeSpecification(position, str(item["target_type"]).casefold()),
                    position,
                ))
        for item in types.get("pointers", []) if isinstance(types.get("pointers", []), list) else []:
            if isinstance(item, dict) and item.get("name") and item.get("target_type"):
                type_declarations.append(TypeDeclaration(
                    str(item["name"]),
                    PointerTypeSpecification(position, str(item["target_type"]).casefold()),
                    position,
                ))
        for item in types.get("subranges", []) if isinstance(types.get("subranges", []), list) else []:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            lower = item.get("lower")
            upper = item.get("upper")
            if not isinstance(lower, int) or not isinstance(upper, int):
                continue
            type_declarations.append(TypeDeclaration(
                str(item["name"]),
                SubrangeTypeSpecification(
                    position,
                    LiteralExpression(position, lower),
                    LiteralExpression(position, upper),
                ),
                position,
            ))
        for item in types.get("enums", []) if isinstance(types.get("enums", []), list) else []:
            if isinstance(item, dict) and item.get("name"):
                values = item.get("values", [])
                type_declarations.append(TypeDeclaration(
                    str(item["name"]),
                    EnumTypeSpecification(
                        position,
                        tuple(str(value) for value in values if isinstance(value, str)),
                    ),
                    position,
                ))
        for item in types.get("records", []) if isinstance(types.get("records", []), list) else []:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            fields: List[FieldDeclaration] = []
            for raw in item.get("fields", []) if isinstance(item.get("fields", []), list) else []:
                if isinstance(raw, dict) and raw.get("name") and raw.get("type"):
                    fields.append(FieldDeclaration(
                        (str(raw["name"]),),
                        str(raw["type"]).casefold(),
                        position,
                        "public",
                        int(raw["offset"]) if isinstance(raw.get("offset"), int) else None,
                    ))
            type_declarations.append(TypeDeclaration(
                str(item["name"]),
                RecordTypeSpecification(position, tuple(fields)),
                position,
            ))
        for item in types.get("arrays", []) if isinstance(types.get("arrays", []), list) else []:
            if not isinstance(item, dict) or not item.get("name") or not item.get("element_type"):
                continue
            lower = item.get("lower")
            upper = item.get("upper")
            if not isinstance(lower, int) or not isinstance(upper, int):
                continue
            type_declarations.append(TypeDeclaration(
                str(item["name"]),
                ArrayTypeSpecification(
                    position,
                    LiteralExpression(position, lower),
                    LiteralExpression(position, upper),
                    str(item["element_type"]).casefold(),
                ),
                position,
            ))

    symbols = document.get("symbols")
    raw_classes = symbols.get("classes", []) if isinstance(symbols, dict) else []
    if isinstance(raw_classes, list):
        for raw_class in raw_classes:
            if not isinstance(raw_class, dict) or not raw_class.get("name"):
                continue
            fields: List[FieldDeclaration] = []
            for raw in raw_class.get("fields", []) if isinstance(raw_class.get("fields", []), list) else []:
                if isinstance(raw, dict) and raw.get("name") and raw.get("type"):
                    fields.append(FieldDeclaration(
                        (str(raw["name"]),),
                        str(raw["type"]).casefold(),
                        position,
                        str(raw.get("visibility", "public")).casefold(),
                        int(raw["offset"]) if isinstance(raw.get("offset"), int) else None,
                    ))
            methods: List[MethodDeclaration] = []
            for raw in raw_class.get("methods", []) if isinstance(raw_class.get("methods", []), list) else []:
                if not isinstance(raw, dict) or not raw.get("name") or not raw.get("symbol"):
                    continue
                parameters: List[ParameterDeclaration] = []
                for param in raw.get("params", []) if isinstance(raw.get("params", []), list) else []:
                    if not isinstance(param, dict) or not param.get("name"):
                        continue
                    modifier = str(param.get("modifier", "value")).casefold()
                    if param.get("is_var") is True:
                        modifier = "var"
                    elif param.get("is_const") is True:
                        modifier = "const"
                    parameters.append(ParameterDeclaration(
                        (str(param["name"]),),
                        str(param.get("type", "integer")).casefold(),
                        modifier,
                        position,
                    ))
                directives: List[str] = []
                if raw.get("is_virtual"):
                    directives.append("virtual")
                if raw.get("is_override"):
                    directives.append("override")
                methods.append(MethodDeclaration(
                    str(raw.get("kind", "procedure")).casefold(),
                    str(raw["name"]),
                    tuple(parameters),
                    str(raw["return_type"]).casefold() if raw.get("return_type") else None,
                    position,
                    tuple(directives),
                    bool(raw.get("is_class_method", False)),
                    str(raw.get("visibility", "public")).casefold(),
                    str(raw["symbol"]),
                ))
            properties: List[PropertyDeclaration] = []
            for raw in raw_class.get("properties", []) if isinstance(raw_class.get("properties", []), list) else []:
                if not isinstance(raw, dict) or not raw.get("name") or not raw.get("type"):
                    continue
                index_parameters: List[ParameterDeclaration] = []
                for param in raw.get("index_params", []) if isinstance(raw.get("index_params", []), list) else []:
                    if isinstance(param, dict) and param.get("name"):
                        index_parameters.append(ParameterDeclaration(
                            (str(param["name"]),),
                            str(param.get("type", "integer")).casefold(),
                            str(param.get("modifier", "value")).casefold(),
                            position,
                        ))
                properties.append(PropertyDeclaration(
                    str(raw["name"]),
                    str(raw["type"]).casefold(),
                    str(raw["read"]) if raw.get("read") else None,
                    str(raw["write"]) if raw.get("write") else None,
                    position,
                    tuple(index_parameters),
                    str(raw.get("visibility", "public")).casefold(),
                ))
            type_declarations.append(TypeDeclaration(
                str(raw_class["name"]),
                ClassTypeSpecification(
                    position,
                    str(raw_class["parent"]).casefold() if raw_class.get("parent") else None,
                    tuple(fields),
                    tuple(methods),
                    tuple(properties),
                    int(raw_class["size"]) if isinstance(raw_class.get("size"), int) else None,
                ),
                position,
            ))

    constants: List[ConstDeclaration] = []
    raw_constants = document.get("constants")
    if isinstance(raw_constants, list):
        for raw in raw_constants:
            if not isinstance(raw, dict) or not raw.get("name"):
                continue
            value = raw.get("value")
            if isinstance(value, (str, int, bool)):
                constants.append(ConstDeclaration(
                    str(raw["name"]),
                    LiteralExpression(position, value),
                    position,
                ))

    return PascalProgram(
        name=f"__pui_{_pui_normalized_unit_name(_pui_unit_name(document))}",
        constants=tuple(constants),
        variables=(),
        body=CompoundStatement(position, ()),
        types=tuple(type_declarations),
    )


def _pui_target_assembly(
    document: Dict[str, object],
    *,
    target: str,
    base_directory: Path,
) -> Optional[Path]:
    implementation = document.get("implementation")
    if not isinstance(implementation, dict):
        return None
    assembly = implementation.get("assembly")
    if not isinstance(assembly, dict):
        return None
    normalized = str(target).strip().casefold()
    key = (
        "amiga" if normalized in {"amiga", "amiga500", "a500", "m68k", "68000"}
        else "pe32" if normalized in {"pe32", "win32", "windows", "windows-pe32"}
        else "c64"
    )
    filename = assembly.get(key)
    if not isinstance(filename, str) or not filename.strip():
        return None
    candidate = (base_directory / filename).resolve()
    if not candidate.is_file():
        raise C64PascalError(
            f"Implementierungsmodul der Unit fehlt: {candidate}."
        )
    return candidate


def _pui_target_c_source(
    document: Dict[str, object],
    *,
    target: str,
    base_directory: Path,
) -> Optional[Path]:
    implementation = document.get("implementation")
    if not isinstance(implementation, dict):
        return None
    sources = implementation.get("c")
    if not isinstance(sources, dict):
        return None
    normalized = str(target).strip().casefold()
    key = (
        "amiga" if normalized in {"amiga", "amiga500", "a500", "m68k", "68000"}
        else "pe32" if normalized in {"pe32", "win32", "windows", "windows-pe32"}
        else "c64"
    )
    filename = sources.get(key)
    if not isinstance(filename, str) or not filename.strip():
        return None
    candidate = (base_directory / filename).resolve()
    if not candidate.is_file():
        raise C64PascalError(
            f"C-Implementierungsmodul der Unit fehlt: {candidate}."
        )
    return candidate


def _pui_validate_target(document: Dict[str, object], target: str) -> None:
    if _pui_is_legacy(document):
        return
    actual = document.get("target")
    if not isinstance(actual, dict):
        raise C64PascalError("PUI besitzt keine Target-Metadaten.")
    expected = _pui_target_information(target)
    actual_format = str(actual.get("object_format", "")).casefold()
    actual_machine = str(actual.get("machine", "")).casefold()
    try:
        actual_pointer_size = int(actual.get("pointer_size"))
    except (TypeError, ValueError):
        actual_pointer_size = -1
    actual_calling = str(actual.get("calling_convention", "")).casefold()
    expected_format = str(expected["object_format"]).casefold()
    expected_machine = str(expected["machine"]).casefold()
    expected_pointer_size = int(expected["pointer_size"])
    expected_calling = str(expected["calling_convention"]).casefold()
    if (
        actual_format != expected_format
        or actual_machine != expected_machine
        or actual_pointer_size != expected_pointer_size
        or actual_calling != expected_calling
    ):
        raise C64PascalError(
            "PUI-Target passt nicht zum Compilerziel: "
            f"PUI={actual_format}/{actual_machine}/ptr{actual_pointer_size}/{actual_calling}, "
            f"Compiler={expected_format}/{expected_machine}/ptr{expected_pointer_size}/{expected_calling}."
        )


def _pui_source_sha256(path: Path) -> Optional[str]:
    """Return a stable fingerprint for a Pascal Unit source without storing source text."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def _pui_source_matches(document: Dict[str, object], source_path: Path) -> bool:
    # Stage206 schema.
    fingerprint = document.get("fingerprint")
    recorded = ""
    if isinstance(fingerprint, dict):
        recorded = str(fingerprint.get("source_sha256", "")).strip().casefold()

    # Stage205 migration input.  Accept only the exact safe SHA-256 shape; this
    # does not re-open the legacy source-text PUI format.
    if not recorded:
        source = document.get("source")
        if _pui_safe_stage205_source_fingerprint(source):
            recorded = str(source.get("sha256", "")).strip().casefold()

    current = _pui_source_sha256(source_path)
    return bool(recorded and current and recorded == current.casefold())


def _pui_object_is_fresh_for_source(object_path: Optional[Path], source_path: Optional[Path]) -> bool:
    if object_path is None or not object_path.is_file():
        return False
    if source_path is None or not source_path.is_file():
        return True
    try:
        return object_path.stat().st_mtime_ns >= source_path.stat().st_mtime_ns
    except OSError:
        return False


def _pui_resolve_link_name(
    name: str,
    *,
    base_directory: Path,
    search_paths: Sequence[Path | str] = (),
) -> Path:
    raw = Path(name).expanduser()
    if raw.is_absolute():
        candidates = [raw]
    else:
        candidates = [Path(base_directory).expanduser() / raw]
        candidates.extend(Path(item).expanduser() / raw for item in search_paths or ())
    selected = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    try:
        return selected.resolve()
    except (OSError, RuntimeError):
        return selected.absolute()


def _pui_primary_object_file(
    document: Dict[str, object],
    *,
    base_directory: Path,
    search_paths: Sequence[Path | str] = (),
) -> Optional[Path]:
    if _pui_is_legacy(document):
        return None
    object_info = document.get("object")
    if not isinstance(object_info, dict):
        return None
    filename = object_info.get("file")
    if not isinstance(filename, str) or not filename.strip():
        return None
    return _pui_resolve_link_name(
        filename,
        base_directory=base_directory,
        search_paths=search_paths,
    )


def _pui_link_object_files(
    document: Dict[str, object],
    *,
    base_directory: Path,
    search_paths: Sequence[Path | str] = (),
) -> Tuple[str, ...]:
    if _pui_is_legacy(document):
        implementation = document.get("implementation")
        raw_items = (
            implementation.get("objects", [])
            if isinstance(implementation, dict)
            else []
        )
    else:
        raw_items: List[str] = []
        object_info = document.get("object")
        if isinstance(object_info, dict):
            filename = object_info.get("file")
            if isinstance(filename, str) and filename.strip():
                raw_items.append(filename)
        link = document.get("link")
        if isinstance(link, dict):
            for key in ("objects", "archives"):
                values = link.get(key, [])
                if isinstance(values, list):
                    raw_items.extend(
                        str(item) for item in values
                        if isinstance(item, str) and item.strip()
                    )
    if not isinstance(raw_items, list):
        return ()
    directories: List[Path] = [Path(base_directory).expanduser()]
    for value in search_paths or ():
        path = Path(value).expanduser()
        if path not in directories:
            directories.append(path)
    result: List[str] = []
    seen = set()
    for item in raw_items:
        if not isinstance(item, str) or not item.strip():
            continue
        raw_path = Path(item).expanduser()
        candidates = [raw_path] if raw_path.is_absolute() else [
            directory / raw_path for directory in directories
        ]
        selected = next((candidate for candidate in candidates if candidate.is_file()), None)
        if selected is None:
            selected = candidates[0]
        try:
            selected = selected.resolve()
        except (OSError, RuntimeError):
            selected = selected.absolute()
        key = str(selected).casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(str(selected))
    return tuple(result)


def _append_pascal_c_aliases(
    assembly: str,
    document: Dict[str, object],
    *,
    target: str,
) -> str:
    """Fuegt Pascal-PUI-Symbole als Wrapper vor C-Exports ein."""
    routines = _pui_external_routines(document)
    if not routines:
        return assembly
    lines = assembly.rstrip().splitlines()
    if lines and lines[-1].strip().casefold() == "end":
        lines.pop()
    normalized = str(target).strip().casefold()
    is_amiga = normalized in {"amiga", "amiga500", "a500", "m68k", "68000"}
    is_pe32 = normalized in {"pe32", "win32", "windows", "windows-pe32"}
    lines.append("")
    lines.append("; Pascal-PUI-Aliase fuer das getrennt kompilierte C-Modul")
    for routine in routines:
        if routine.symbol == routine.name:
            continue
        if is_pe32:
            lines.append(f"global {routine.symbol}")
        lines.append(f"{routine.symbol}:")
        lines.append(
            f"    bra {routine.name}" if is_amiga else f"    jmp {routine.name}"
        )
    if not is_pe32:
        lines.append("end")
    return "\n".join(lines).rstrip() + "\n"


def _compile_pui_c_implementation(
    document: Dict[str, object],
    *,
    source_path: Path,
    target: str,
    include_paths: Iterable[Path | str],
) -> Path:
    """Kompiliert ein C-Unitmodul und legt das erzeugte ASM daneben ab."""
    try:
        source = source_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise C64PascalError(
            f"C-Implementierungsmodul kann nicht gelesen werden: {source_path}: {exc}"
        ) from exc

    # Lazy import verhindert den Modulzyklus: c64c.compiler verwendet die
    # gemeinsamen Pascal-Datentypen aus dieser Datei.
    try:
        from c64c.compiler import C64CError, compile_c_module_to_assembly
    except Exception as exc:
        raise C64PascalError(
            f"C-Compiler fuer Unit-Implementierung kann nicht geladen werden: {exc}"
        ) from exc

    project_root = Path(__file__).resolve().parent.parent
    paths: List[Path] = []
    for item in (
        *include_paths,
        source_path.parent,
        project_root / "runtime" / "graphics" / "include",
        project_root / "c64c" / "include",
    ):
        path = Path(item).expanduser().resolve()
        if path not in paths:
            paths.append(path)

    try:
        generated = compile_c_module_to_assembly(
            source,
            filename=str(source_path),
            include_paths=paths,
            target=target,
            module_prefix="__pas_unit_c",
        )
    except C64CError as exc:
        raise C64PascalError(
            f"C-Implementierung der Pascal-Unit konnte nicht kompiliert werden: {exc}"
        ) from exc

    assembly = _append_pascal_c_aliases(
        generated.assembly,
        document,
        target=target,
    )
    normalized = str(target).strip().casefold()
    if normalized in {"amiga", "amiga500", "a500", "m68k", "68000"}:
        suffix = "amiga"
    elif normalized in {"pe32", "win32", "windows", "windows-pe32"}:
        suffix = "pe32"
    else:
        suffix = "c64"
    source_name = source_path.name
    target_suffix = f".{suffix}.c"
    unit_stem = (
        source_name[:-len(target_suffix)]
        if source_name.casefold().endswith(target_suffix)
        else source_path.stem
    )
    output = source_path.with_name(unit_stem + f".generated.{suffix}.asm")
    try:
        output.write_text(assembly, encoding="utf-8")
    except OSError as exc:
        raise C64PascalError(
            f"Erzeugtes Unit-C-Modul kann nicht geschrieben werden: {output}: {exc}"
        ) from exc
    return output


def write_pascal_unit_interface(
    unit_path: Path | str,
    pui_path: Optional[Path | str] = None,
    *,
    predefined_macros: Optional[Dict[str, Union[str, int, bool]]] = None,
    target: str = "pe32",
    include_paths: Iterable[Path | str] = (),
    link_search_paths: Iterable[Path | str] = (),
    output_directory: Optional[Path | str] = None,
) -> Path:
    """Write the public ABI metadata for a Pascal unit.

    Stage186 deliberately never stores source text in the PUI. The source is
    parsed once here to derive metadata and can then be removed from a binary
    distribution that contains only .pui + .o/.obj/.a/.lib.
    """
    source_path = Path(unit_path).expanduser().resolve()
    try:
        source = source_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise C64PascalError(f"Unit kann nicht gelesen werden: {source_path}: {exc}") from exc
    preprocessor = PascalPreprocessor(
        predefined_macros,
        link_search_paths=link_search_paths,
    )
    processed = preprocessor.process(source, filename=str(source_path))
    (
        transformed,
        unit_name,
        interface_units,
        implementation_units,
        interface_source,
        unused_implementation_source,
    ) = _unit_program_source(processed.source, filename=str(source_path))
    del unused_implementation_source

    resolver = _PascalUnitResolver(
        filename=str(source_path),
        include_paths=tuple(include_paths) + (source_path.parent,),
        preprocessor=preprocessor,
        target=target,
        output_directory=output_directory,
    )
    for dependency in interface_units + implementation_units:
        resolver.resolve(dependency)

    full_program = _parse_pascal_program(transformed)
    if pui_path is not None:
        destination = Path(pui_path).expanduser().resolve()
    elif output_directory:
        destination = (
            Path(output_directory).expanduser().resolve()
            / source_path.with_suffix(".pui").name
        )
    else:
        destination = source_path.with_suffix(".pui")
    document = _pui_document(
        unit_name=unit_name,
        interface_source=interface_source,
        interface_units=interface_units,
        implementation_units=implementation_units,
        source_path=source_path,
        target=target,
        full_program=full_program,
        dependency_programs=tuple(resolver.programs),
        link_files=processed.link_files,
        macros=processed.macros,
    )
    _write_pui_document(destination, document)
    return destination


class _PascalUnitResolver:
    def __init__(
        self,
        *,
        filename: str,
        include_paths: Iterable[Path | str],
        preprocessor: PascalPreprocessor,
        target: str = "c64",
        output_directory: Optional[Path | str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> None:
        self.search_paths: List[Path] = []
        try:
            root_file = Path(filename).expanduser().resolve()
        except (OSError, RuntimeError):
            root_file = None
        if root_file is not None and root_file.is_file():
            self.search_paths.append(root_file.parent)
        for item in include_paths:
            path = Path(item).expanduser().resolve()
            if path not in self.search_paths:
                self.search_paths.append(path)
        self.output_directory: Optional[Path] = None
        if output_directory:
            try:
                self.output_directory = Path(output_directory).expanduser().resolve()
            except (OSError, RuntimeError, ValueError):
                self.output_directory = Path(output_directory).expanduser().absolute()
            if self.output_directory not in self.search_paths:
                self.search_paths.append(self.output_directory)

        # Stage196: project InputDirectories are not only link-object search
        # paths. They are also architecture-specific PUI/Unit lookup roots.
        # Keep their QListWidget order exactly as provided by the IDE.
        for item in preprocessor.link_search_paths:
            try:
                path = Path(item).expanduser().resolve()
            except (OSError, RuntimeError, ValueError):
                path = Path(item).expanduser().absolute()
            if path not in self.search_paths:
                self.search_paths.append(path)

        builtin_units = (Path(__file__).resolve().parent / "units").resolve()
        if builtin_units not in self.search_paths:
            self.search_paths.append(builtin_units)
        current = Path.cwd().resolve()
        if current not in self.search_paths:
            self.search_paths.append(current)
        self.programs: List[PascalProgram] = []
        self.external_routines: List[ExternalRoutineDeclaration] = []
        self.assembly_files: List[str] = []
        self.object_files: List[str] = []
        self.resolved: Dict[str, Path] = {}
        self.stack: List[str] = []
        self.preprocessor = preprocessor
        self.target = str(target)
        self.progress_callback = progress_callback

    def resolve(self, unit_name: str) -> None:
        key = unit_name.casefold()
        if key in self.resolved:
            return
        if key in self.stack:
            guarded_source = _find_unit_file(unit_name, self.search_paths)
            if guarded_source is not None:
                try:
                    guarded_text = guarded_source.read_text(encoding="utf-8-sig")
                except (OSError, UnicodeError):
                    guarded_text = ""
                guard = _pascal_guard_macro(guarded_text)
                if guard is not None and guard.casefold() in self.preprocessor.macros:
                    self.preprocessor.process(
                        guarded_text,
                        filename=str(guarded_source),
                    )
                    return
            guarded_pui = _find_unit_artifact(
                unit_name,
                self.search_paths,
                (".pui",),
            )
            if guarded_pui is not None:
                document = _read_pui_document(guarded_pui, unit_name)
                if _pui_is_legacy(document):
                    guard = document.get("guard")
                    if (
                        isinstance(guard, str)
                        and guard.casefold() in self.preprocessor.macros
                    ):
                        return
            chain = " -> ".join(self.stack + [key])
            raise C64PascalError(f"Zirkuläre USES-Abhängigkeit: {chain}.")

        # Stage196: PE32 and PE32+ may coexist. Do not stop at the first
        # same-named PUI if its ABI belongs to the other architecture. Search
        # every configured directory in order. If source exists but only a
        # wrong-target PUI is present, treat the PUI as stale and rebuild it
        # into the active target's output_directory.
        pui_candidates: List[Path] = []
        if self.output_directory is not None:
            pui_candidates.extend(
                _find_unit_artifacts(
                    unit_name, (self.output_directory,), (".pui",)
                )
            )
        for candidate in _find_unit_artifacts(
            unit_name, self.search_paths, (".pui",)
        ):
            if candidate not in pui_candidates:
                pui_candidates.append(candidate)

        # Resolve the Pascal source before validating PUI candidates.  A
        # source-bearing experimental/legacy PUI must never be consumed as ABI
        # metadata, but when the authoritative .pas file exists we can safely
        # discard that stale cache and rebuild a source-free PUI instead of
        # aborting the whole USES resolution.
        source_path = _find_unit_file(unit_name, self.search_paths)

        pui_path: Optional[Path] = None
        pui_target_mismatches: List[str] = []
        for candidate in pui_candidates:
            try:
                candidate_document = _read_pui_document(candidate, unit_name)
            except C64PascalError as exc:
                if (
                    source_path is not None
                    and "verletzt Information Hiding" in str(exc)
                ):
                    pui_target_mismatches.append(
                        f"  {candidate}: source-tragende PUI wird aus "
                        f"{source_path.name} neu erzeugt."
                    )
                    continue
                raise
            try:
                _pui_validate_target(candidate_document, self.target)
            except C64PascalError as exc:
                pui_target_mismatches.append(f"  {candidate}: {exc}")
                continue
            pui_path = candidate
            break
        if pui_path is None and source_path is None:
            paths = "\n".join(f"  {path}" for path in self.search_paths)
            if pui_target_mismatches:
                mismatches = "\n".join(pui_target_mismatches)
                raise C64PascalError(
                    f"Keine PUI fuer das aktive Compilerziel gefunden: {unit_name}.\n"
                    f"Nicht passende PUIs:\n{mismatches}\n"
                    f"Durchsuchte Pfade:\n{paths}"
                )
            raise C64PascalError(
                f"Unit nicht gefunden: {unit_name}.\nDurchsuchte Pfade:\n{paths}"
            )

        self.stack.append(key)
        try:
            source_interface = ""
            source_implementation = ""
            source_interface_units: Tuple[str, ...] = ()
            source_implementation_units: Tuple[str, ...] = ()
            transformed_source = ""
            declared_name = unit_name
            source_text = ""
            processed: Optional[PascalPreprocessResult] = None
            source_full_program: Optional[PascalProgram] = None

            if source_path is not None:
                try:
                    source_text = source_path.read_text(encoding="utf-8-sig")
                except (OSError, UnicodeError) as exc:
                    raise C64PascalError(
                        f"Unit kann nicht gelesen werden: {source_path}: {exc}"
                    ) from exc
                processed = self.preprocessor.process(
                    source_text,
                    filename=str(source_path),
                )
                (
                    transformed_source,
                    declared_name,
                    source_interface_units,
                    source_implementation_units,
                    source_interface,
                    source_implementation,
                ) = _unit_program_source(processed.source, filename=str(source_path))

            if declared_name.casefold() != key:
                raise C64PascalError(
                    f"Unit-Name {declared_name} passt nicht zu USES {unit_name} "
                    f"({source_path})."
                )

            if pui_path is not None:
                pui_document = _read_pui_document(pui_path, unit_name)
                if (
                    _pui_is_legacy(pui_document)
                    and source_path is not None
                    and processed is not None
                ):
                    # Automatic privacy migration: as soon as the original Unit
                    # source is available, replace Stage177-185's source-bearing
                    # PUI with the Stage186 metadata-only contract.
                    for dependency in (
                        source_interface_units + source_implementation_units
                    ):
                        self.resolve(dependency)
                    source_full_program = _parse_pascal_program_with_progress(
                        transformed_source,
                        self.progress_callback,
                        str(source_path),
                    )
                    full_program = source_full_program
                    pui_document = _pui_document(
                        unit_name=declared_name,
                        interface_source=source_interface,
                        interface_units=source_interface_units,
                        implementation_units=source_implementation_units,
                        source_path=source_path,
                        target=self.target,
                        full_program=full_program,
                        dependency_programs=tuple(self.programs),
                        link_files=processed.link_files,
                        macros=processed.macros,
                    )
                    if self.output_directory is not None:
                        pui_path = self.output_directory / pui_path.name
                    _write_pui_document(pui_path, pui_document)
                _pui_validate_target(pui_document, self.target)
                if source_path is not None and processed is not None:
                    # Stage205: when the Pascal source is available it is the
                    # authoritative visibility contract.  A PUI is a cache/link
                    # contract and must never reintroduce stale USES metadata.
                    interface_units = source_interface_units
                    implementation_units = source_implementation_units
                else:
                    interface_units, implementation_units = _pui_uses(pui_document)
            else:
                # Resolve interface dependencies before deriving layout metadata;
                # this lets a class such as Exception(TObject) record the real
                # base size without serializing TObject's source declaration.
                for dependency in (
                    source_interface_units + source_implementation_units
                ):
                    self.resolve(dependency)
                if source_path is None or processed is None:
                    raise C64PascalError(
                        f"PUI kann ohne Unit-Quelle nicht erzeugt werden: {unit_name}."
                    )
                source_full_program = _parse_pascal_program_with_progress(
                        transformed_source,
                        self.progress_callback,
                        str(source_path),
                    )
                full_program = source_full_program
                pui_path = (
                    self.output_directory / source_path.with_suffix(".pui").name
                    if self.output_directory is not None
                    else source_path.with_suffix(".pui")
                )
                pui_document = _pui_document(
                    unit_name=declared_name,
                    interface_source=source_interface,
                    interface_units=source_interface_units,
                    implementation_units=source_implementation_units,
                    source_path=source_path,
                    target=self.target,
                    full_program=full_program,
                    dependency_programs=tuple(self.programs),
                    link_files=processed.link_files,
                    macros=processed.macros,
                )
                _write_pui_document(pui_path, pui_document)
                interface_units = source_interface_units
                implementation_units = source_implementation_units

            dependencies = interface_units + implementation_units
            for dependency in dependencies:
                self.resolve(dependency)

            if source_path is not None and processed is not None:
                # Stage205: source wins over a same-target but stale PUI.
                # Rebuild only metadata; no Pascal source text is serialized.
                # This is especially important for ABI aliases such as UINT,
                # DWORD, HWND and HMODULE whose PE32 width must stay 4 bytes.
                if source_full_program is None:
                    source_full_program = _parse_pascal_program_with_progress(
                        transformed_source,
                        self.progress_callback,
                        str(source_path),
                    )
                fresh_document = _pui_document(
                    unit_name=declared_name,
                    interface_source=source_interface,
                    interface_units=source_interface_units,
                    implementation_units=source_implementation_units,
                    source_path=source_path,
                    target=self.target,
                    full_program=source_full_program,
                    dependency_programs=tuple(self.programs),
                    link_files=processed.link_files,
                    macros=processed.macros,
                )
                if pui_path is None:
                    pui_path = (
                        self.output_directory / source_path.with_suffix(".pui").name
                        if self.output_directory is not None
                        else source_path.with_suffix(".pui")
                    )
                if (
                    not _pui_source_matches(pui_document, source_path)
                    or pui_document != fresh_document
                ):
                    _write_pui_document(pui_path, fresh_document)
                pui_document = fresh_document

            self.external_routines.extend(_pui_external_routines(pui_document))
            implementation_base = (pui_path or source_path).parent
            link_search_paths = tuple(self.preprocessor.link_search_paths)
            primary_object = _pui_primary_object_file(
                pui_document,
                base_directory=implementation_base,
                search_paths=link_search_paths,
            )
            link_inputs = _pui_link_object_files(
                pui_document,
                base_directory=implementation_base,
                search_paths=link_search_paths,
            )

            # Prefer the PUI + compiled object contract. During an incremental
            # source build the companion object may not exist yet; in that one
            # case source is used transiently as a compatibility fallback, but
            # it is never copied into the PUI.
            use_metadata_program = (
                not _pui_is_legacy(pui_document)
                and (
                    source_path is None
                    or _pui_object_is_fresh_for_source(primary_object, source_path)
                )
            )

            if use_metadata_program:
                if primary_object is not None and not primary_object.is_file():
                    raise C64PascalError(
                        f"PUI-Objektdatei fehlt: {primary_object}."
                    )
                for object_name in link_inputs:
                    if object_name not in self.object_files:
                        self.object_files.append(object_name)
                program = _pui_program_from_metadata(pui_document)
            else:
                # Do not add the unit's own object while compiling its source
                # inline; doing so would define the same methods twice. Extra
                # {$L}/{$linklib} dependencies remain valid linker inputs.
                primary_key = (
                    str(primary_object).casefold()
                    if primary_object is not None
                    else None
                )
                for object_name in link_inputs:
                    if primary_key is not None and str(object_name).casefold() == primary_key:
                        continue
                    if object_name not in self.object_files:
                        self.object_files.append(object_name)

                implementation_file = _pui_target_assembly(
                    pui_document,
                    target=self.target,
                    base_directory=implementation_base,
                )
                if implementation_file is None:
                    c_implementation = _pui_target_c_source(
                        pui_document,
                        target=self.target,
                        base_directory=implementation_base,
                    )
                    if c_implementation is not None:
                        implementation_file = _compile_pui_c_implementation(
                            pui_document,
                            source_path=c_implementation,
                            target=self.target,
                            include_paths=self.search_paths,
                        )
                if implementation_file is not None:
                    implementation_name = str(implementation_file)
                    if implementation_name not in self.assembly_files:
                        self.assembly_files.append(implementation_name)

                if source_path is not None and transformed_source:
                    try:
                        program = (
                            source_full_program
                            if source_full_program is not None
                            else _parse_pascal_program_with_progress(
                                transformed_source,
                                self.progress_callback,
                                str(source_path),
                            )
                        )
                    except C64PascalError as exc:
                        raise C64PascalError(f"{source_path}: {exc}") from exc
                elif _pui_is_legacy(pui_document):
                    program = _pui_program_from_metadata(pui_document)
                else:
                    raise C64PascalError(
                        f"PUI {pui_path} besitzt kein verwendbares Objekt und "
                        "die Unit-Quelle ist nicht verfügbar."
                    )

            self.programs.append(program)
            self.resolved[key] = pui_path or source_path
        finally:
            self.stack.pop()


def _merge_external_routines_for_link(
    resolver_routines: Sequence[ExternalRoutineDeclaration],
    unit_programs: Sequence[PascalProgram],
    main_program: PascalProgram,
) -> Tuple[ExternalRoutineDeclaration, ...]:
    """Keep public PUI imports and private source-level runtime imports.

    ``resolver_routines`` contains the public declarations reconstructed from
    PUI metadata.  When a Unit is compiled from its available Pascal source,
    its implementation can additionally contain private EXTERNAL declarations
    which deliberately do not belong in the public PUI.  The merged PE module
    still needs those symbols while emitting that Unit's method bodies.

    The main program's own EXTERNAL declarations must be retained as well when
    the program has a USES clause.  Duplicate compatible declarations are
    intentionally left to ``_prepare_external_routines()``, which already
    validates their linker symbols.
    """
    merged: List[ExternalRoutineDeclaration] = list(resolver_routines)
    for unit_program in unit_programs:
        merged.extend(unit_program.external_routines)
    merged.extend(main_program.external_routines)
    return tuple(merged)


def _parse_pascal_frontend(
    source: str,
    *,
    filename: str = "<Pascal-Editor>",
    include_paths: Iterable[Path | str] = (),
    predefined_macros: Optional[Dict[str, Union[str, int, bool]]] = None,
    target: str = "c64",
    link_search_paths: Iterable[Path | str] = (),
    output_directory: Optional[Path | str] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> Tuple[PascalProgram, PascalPreprocessResult]:
    preprocessor = PascalPreprocessor(
        predefined_macros, link_search_paths=link_search_paths
    )
    root_processed = preprocessor.process(source, filename=filename)
    cleaned_source, unit_names = _extract_program_uses(
        root_processed.source,
        filename=filename,
    )
    main_program = _parse_pascal_program_with_progress(
        cleaned_source,
        progress_callback,
        filename,
    )
    if not unit_names:
        return replace(
            main_program,
            unit_object_files=tuple(preprocessor.link_files),
        ), PascalPreprocessResult(
            root_processed.source,
            dict(preprocessor.macros),
            tuple(preprocessor.notes),
            tuple(preprocessor.warnings),
            tuple(preprocessor.link_files),
        )

    resolver = _PascalUnitResolver(
        filename=filename,
        include_paths=include_paths,
        preprocessor=preprocessor,
        target=target,
        output_directory=output_directory,
        progress_callback=progress_callback,
    )
    for unit_name in unit_names:
        resolver.resolve(unit_name)

    constants = []
    type_groups: List[Sequence[TypeDeclaration]] = []
    variables = []
    methods = []
    global_routines = []
    for unit_program in resolver.programs:
        constants.extend(unit_program.constants)
        type_groups.append(unit_program.types)
        variables.extend(unit_program.variables)
        methods.extend(unit_program.methods)
        global_routines.extend(unit_program.global_routines)
    constants.extend(main_program.constants)
    type_groups.append(main_program.types)
    variables.extend(main_program.variables)
    methods.extend(main_program.methods)
    global_routines.extend(main_program.global_routines)
    types = _merge_pascal_type_scopes(
        tuple(type_groups[:-1]),
        tuple(type_groups[-1]) if type_groups else (),
    )
    program = PascalProgram(
        name=main_program.name,
        constants=tuple(constants),
        variables=tuple(variables),
        body=main_program.body,
        types=tuple(types),
        methods=tuple(methods),
        external_routines=_merge_external_routines_for_link(
            resolver.external_routines,
            resolver.programs,
            main_program,
        ),
        global_routines=tuple(global_routines),
        unit_assembly_files=tuple(resolver.assembly_files),
        unit_object_files=tuple(
            dict.fromkeys(
                list(preprocessor.link_files) + list(resolver.object_files)
            )
        ),
    )
    return program, PascalPreprocessResult(
        root_processed.source,
        dict(preprocessor.macros),
        tuple(preprocessor.notes),
        tuple(preprocessor.warnings),
        tuple(preprocessor.link_files),
    )


def parse_pascal(
    source: str,
    *,
    filename: str = "<Pascal-Editor>",
    include_paths: Iterable[Path | str] = (),
    predefined_macros: Optional[Dict[str, Union[str, int, bool]]] = None,
) -> PascalProgram:
    return _parse_pascal_frontend(
        source,
        filename=filename,
        include_paths=include_paths,
        predefined_macros=predefined_macros,
    )[0]


@dataclass(eq=False)
class _PascalType:
    name: str
    size: int
    signed: bool = False
    kind: str = "scalar"
    fields: Dict[str, "_FieldInfo"] = field(default_factory=dict)
    properties: Dict[str, "_PropertyInfo"] = field(default_factory=dict)
    element_type: Optional["_PascalType"] = None
    lower_bound: int = 0
    upper_bound: int = -1
    methods: Dict[str, "_MethodInfo"] = field(default_factory=dict)
    base_type: Optional["_PascalType"] = None
    pointer_target: Optional["_PascalType"] = None

    @property
    def scalar(self) -> bool:
        return self.kind in {
            "scalar", "enum", "subrange", "pointer", "string", "double"
        }

    @property
    def aggregate(self) -> bool:
        return self.kind in {"record", "array", "class"}


@dataclass(frozen=True)
class _FieldInfo:
    name: str
    type_info: _PascalType
    offset: int
    position: SourcePosition


@dataclass(frozen=True)
class _PropertyInfo:
    name: str
    type_info: _PascalType
    read_accessor: Optional[str]
    write_accessor: Optional[str]
    position: SourcePosition
    index_parameters: Tuple[_ParameterInfo, ...] = ()


@dataclass(frozen=True)
class _ParameterInfo:
    name: str
    type_info: _PascalType
    modifier: str
    position: SourcePosition
    # Stage 215: preserve the source/PUI type spelling for ABI aliases such as
    # Win32 BOOL.  Semantic aliases still resolve to their storage type
    # (BOOL -> Integer), but external-call compatibility may need the public ABI
    # identity without weakening normal Pascal assignment rules.
    declared_type_name: Optional[str] = None


@dataclass(eq=False)
class _MethodInfo:
    owner: _PascalType
    kind: str
    name: str
    parameters: Tuple[_ParameterInfo, ...]
    result_type: Optional[_PascalType]
    position: SourcePosition
    label: str
    implementation: Optional[MethodImplementation] = None
    is_virtual: bool = False
    is_override: bool = False
    is_class_method: bool = False
    visibility: str = "public"
    is_external: bool = False
    parameter_variables: Tuple["_Variable", ...] = ()
    local_variables: Dict[str, "_Variable"] = field(default_factory=dict)
    local_initializers: List[Tuple["_Variable", Expression]] = field(default_factory=list)
    result_variable: Optional["_Variable"] = None


@dataclass(frozen=True)
class _ExternalRoutineInfo:
    unit_name: str
    kind: str
    name: str
    parameters: Tuple[_ParameterInfo, ...]
    result_type: Optional[_PascalType]
    symbol: str
    calling_convention: Optional[str] = None
    library: Optional[str] = None
    import_name: Optional[str] = None


@dataclass
class _GlobalRoutineInfo:
    kind: str
    name: str
    parameters: Tuple[_ParameterInfo, ...]
    result_type: Optional[_PascalType]
    position: SourcePosition
    label: str
    implementation: GlobalRoutineImplementation
    calling_convention: Optional[str] = None
    parameter_variables: Tuple["_Variable", ...] = ()
    local_variables: Dict[str, "_Variable"] = field(default_factory=dict)
    local_initializers: List[Tuple["_Variable", Expression]] = field(default_factory=list)
    result_variable: Optional["_Variable"] = None


INTEGER_TYPE = _PascalType("integer", 2, True)
BYTE_TYPE = _PascalType("byte", 1, False)
CHAR_TYPE = _PascalType("char", 1, False)
BOOLEAN_TYPE = _PascalType("boolean", 1, False)
STRING_TYPE = _PascalType("string", 2, False, "string")
POINTER_TYPE = _PascalType("pointer", 2, False, "pointer")
DOUBLE_TYPE = _PascalType("double", 8, True, "double")

# Windows PE32 uses native 32-bit Integer, Pointer and dynamic-string handles.
PE32_INTEGER_TYPE = _PascalType("integer", 4, True)
PE32_POINTER_TYPE = _PascalType("pointer", 4, False, "pointer")
PE32_STRING_TYPE = _PascalType("string", 4, False, "string")

# Windows PE32+ / AMD64 keeps Delphi-style Integer at 32 Bit while pointers
# and string handles are native 64-bit values.  These widths are also used by
# the source-free PUI layout pass so PE64 metadata never inherits C64 sizes.
PE64_INTEGER_TYPE = _PascalType("integer", 4, True)
PE64_POINTER_TYPE = _PascalType("pointer", 8, False, "pointer")
PE64_STRING_TYPE = _PascalType("string", 8, False, "string")

# Stage 181: Runtime-Funktionen aus System.Objects werden als echte PE-Imports
# an d64qt5.dll gebunden. Der erste Name ist der Pascal/DLL-Exportname;
# der lokale COFF32-cdecl-Symbolname wird weiterhin als _jit_* erzeugt.
PASCAL_MINIRUNTIME_DLL = "libd64_runtime.dll"
PASCAL_MINIRUNTIME_IMPORTS: Dict[str, str] = {
    "jit_object_instance_new"   : "jit_object_instance_new",
    "jit_object_instance_free"  : "jit_object_instance_free",
    "jit_object_free"           : "jit_object_free",
    "jit_object_class_type"     : "jit_object_class_type",
    "jit_class_parent"          : "jit_class_parent",
    "jit_class_name"            : "jit_class_name",
    "jit_class_instance_size"   : "jit_class_instance_size",
    "jit_inherits_from_class"   : "jit_inherits_from_class",
    "jit_inherits_from_object"  : "jit_inherits_from_object",
    "jit_dynstring_from_cstr"   : "jit_dynstring_from_cstr",
}

_TYPES = {
    item.name: item
    for item in (
        INTEGER_TYPE, BYTE_TYPE, CHAR_TYPE, BOOLEAN_TYPE,
        STRING_TYPE, POINTER_TYPE, DOUBLE_TYPE,
    )
}


@dataclass
class _Variable:
    name: str
    label: str
    type_info: _PascalType
    position: SourcePosition
    internal: bool = False


@dataclass(frozen=True)
class _DynamicAccess:
    expression: Expression
    lower_bound: int
    element_count: int
    stride: int
    position: SourcePosition


@dataclass(frozen=True)
class _StorageAccess:
    type_info: _PascalType
    position: SourcePosition
    base_label: Optional[str]
    use_self: bool
    constant_offset: int = 0
    dynamic: Optional[_DynamicAccess] = None
    # Offsets that must be applied before loading each pointer value.
    # Example: P^.Field => (0,), Record.Ptr^.Field => (PtrOffset,).
    dereference_offsets: Tuple[int, ...] = ()


@dataclass
class _Emitter:
    lines: List[str] = field(default_factory=list)
    source_map: Dict[int, int] = field(default_factory=dict)

    def emit(self, text: str = "", source_line: int = 0) -> None:
        self.lines.append(text)
        if source_line:
            self.source_map[len(self.lines)] = int(source_line)


class _CodeGenerator:
    ZP_SELF_LO = "$F7"
    ZP_SELF_HI = "$F8"
    ZP_VALUE_LO = "$F9"
    ZP_VALUE_HI = "$FA"
    ZP_LEFT_LO = "$FB"
    ZP_LEFT_HI = "$FC"
    ZP_RIGHT_LO = "$FD"
    ZP_RIGHT_HI = "$FE"

    def __init__(self, program: PascalProgram) -> None:
        self.program = program
        self.emitter = _Emitter()
        self.constants: Dict[str, ScalarValue] = {}
        self.constant_types: Dict[str, _PascalType] = {}
        self.types: Dict[str, _PascalType] = dict(_TYPES)
        self.type_declarations: Dict[str, TypeDeclaration] = {}
        self.resolving_types: set[str] = set()
        self.variables: Dict[str, _Variable] = {}
        self.variable_order: List[_Variable] = []
        self.initializers: List[Tuple[_Variable, Expression]] = []
        self.methods: List[_MethodInfo] = []
        self.external_routines: Dict[str, _ExternalRoutineInfo] = {}
        self.global_routines: Dict[str, _GlobalRoutineInfo] = {}
        self.imported_method_symbols: set[str] = set()
        self.current_method: Optional[_MethodInfo] = None
        self.current_global_routine: Optional[_GlobalRoutineInfo] = None
        self.scope_variables: Dict[str, _Variable] = {}
        self.strings: Dict[bytes, str] = {}
        self.runtime: set[str] = set()
        self.label_counter = 0
        self.break_targets: List[str] = []
        self.continue_targets: List[str] = []

    @staticmethod
    def _key(name: str) -> str:
        return name.casefold()

    @staticmethod
    def _safe_name(name: str) -> str:
        result = "".join(
            character.lower() if character.isalnum() else "_"
            for character in name
        )
        return result or "value"

    def _value_storage_size(self, type_info: _PascalType) -> int:
        """Bytes occupied by one Pascal value in a variable/field slot.

        The base compiler keeps the historic representation. Windows backends
        override this for class-reference values, whose instance layout is not
        the same thing as the size of a variable holding the object reference.
        """
        return max(1, int(type_info.size))

    def _value_is_scalar(self, type_info: _PascalType) -> bool:
        return bool(type_info.scalar)

    def _error(self, message: str, position: SourcePosition) -> C64PascalError:
        return C64PascalError(message, position.line, position.column - 1)

    def _new_label(self, prefix: str) -> str:
        self.label_counter += 1
        return f"__pas_{prefix}_{self.label_counter}"

    def _declare_variable(
        self,
        name: str,
        type_info: _PascalType,
        position: SourcePosition,
        *,
        internal: bool = False,
    ) -> _Variable:
        key = self._key(name)
        if key in self.variables or key in self.constants or key in self.types:
            raise self._error(f"Bezeichner mehrfach deklariert: {name}.", position)
        variable = self._allocate_variable(name, type_info, position, internal=internal)
        self.variables[key] = variable
        return variable

    def _allocate_variable(
        self,
        name: str,
        type_info: _PascalType,
        position: SourcePosition,
        *,
        internal: bool = False,
        label_prefix: Optional[str] = None,
    ) -> _Variable:
        label_prefix = self._safe_name(
            label_prefix if label_prefix is not None else "tmp" if internal else "var"
        )
        variable = _Variable(
            name,
            f"__pas_{label_prefix}_{self._safe_name(name)}_{len(self.variable_order)}",
            type_info,
            position,
            internal,
        )
        self.variable_order.append(variable)
        return variable

    def _is_constant_expression(self, expression: Expression) -> bool:
        """Prueft ohne Compilerfehler, ob ein Ausdruck konstant ist.

        Diese Vorpruefung ist insbesondere fuer Arrayindizes wichtig. Die
        Pascal- und C-Codegeneratoren verwenden unterschiedliche Fehlerklassen;
        eine Ausnahme als Steuerfluss wuerde deshalb einen gueltigen lokalen
        C-Index wie ``array[index]`` faelschlich als Compilerfehler melden.
        """
        if isinstance(expression, LiteralExpression):
            return True
        if isinstance(expression, (NameExpression, DesignatorExpression)):
            if isinstance(expression, DesignatorExpression) and expression.selectors:
                return False
            return self._key(expression.name) in self.constants
        if isinstance(expression, UnaryExpression):
            return self._is_constant_expression(expression.operand)
        if isinstance(expression, BinaryExpression):
            return (
                self._is_constant_expression(expression.left)
                and self._is_constant_expression(expression.right)
            )
        return False

    def _evaluate_constant(self, expression: Expression) -> ScalarValue:
        if isinstance(expression, LiteralExpression):
            return expression.value
        if isinstance(expression, (NameExpression, DesignatorExpression)):
            if isinstance(expression, DesignatorExpression) and expression.selectors:
                raise self._error("Ein Feld- oder Arrayzugriff ist hier nicht konstant.", expression.position)
            key = self._key(expression.name)
            if key not in self.constants:
                raise self._error(
                    f"Konstanter Bezeichner nicht gefunden: {expression.name}.",
                    expression.position,
                )
            return self.constants[key]
        if isinstance(expression, UnaryExpression):
            value = self._evaluate_constant(expression.operand)
            if expression.operator == "+" and isinstance(value, int):
                return +value
            if expression.operator == "-" and isinstance(value, int):
                return -value
            if expression.operator == "not":
                return not bool(value)
            raise self._error("Ungültiger Konstantenausdruck.", expression.position)
        if isinstance(expression, BinaryExpression):
            left = self._evaluate_constant(expression.left)
            right = self._evaluate_constant(expression.right)
            operator = expression.operator
            try:
                if operator == "+":
                    return left + right
                if operator == "-":
                    return int(left) - int(right)
                if operator == "*":
                    return int(left) * int(right)
                if operator == "div":
                    if int(right) == 0:
                        raise ZeroDivisionError
                    return int(left) // int(right)
                if operator == "/":
                    raise self._error(
                        "Der Real-Operator '/' wird nicht unterstützt; verwende DIV.",
                        expression.position,
                    )
                if operator == "mod":
                    if int(right) == 0:
                        raise ZeroDivisionError
                    return int(left) % int(right)
                if operator == "and":
                    if isinstance(left, bool) and isinstance(right, bool):
                        return left and right
                    return int(left) & int(right)
                if operator == "or":
                    if isinstance(left, bool) and isinstance(right, bool):
                        return left or right
                    return int(left) | int(right)
                if operator == "xor":
                    if isinstance(left, bool) and isinstance(right, bool):
                        return left != right
                    return int(left) ^ int(right)
                if operator == "=":
                    return left == right
                if operator == "<>":
                    return left != right
                if operator == "<":
                    return left < right
                if operator == "<=":
                    return left <= right
                if operator == ">":
                    return left > right
                if operator == ">=":
                    return left >= right
            except (TypeError, ValueError):
                pass
            except ZeroDivisionError:
                raise self._error("Division durch null im Konstantenausdruck.", expression.position)
        raise self._error("Ausdruck ist nicht konstant.", expression.position)

    def _resolve_type(self, name: str, position: SourcePosition) -> _PascalType:
        key = self._key(name)
        if key in self.resolving_types:
            declaration = self.type_declarations.get(key)
            display_name = declaration.name if declaration is not None else name
            raise self._error(f"Zyklische Typdefinition: {display_name}.", position)
        resolved = self.types.get(key)
        if resolved is not None:
            return resolved
        declaration = self.type_declarations.get(key)
        if declaration is None:
            raise self._error(f"Datentyp nicht gefunden: {name}.", position)

        self.resolving_types.add(key)
        try:
            specification = declaration.specification
            if isinstance(specification, NamedTypeSpecification):
                type_info = self._resolve_type(specification.name, specification.position)
            elif isinstance(specification, SubrangeTypeSpecification):
                lower = self._evaluate_constant(specification.lower_bound)
                upper = self._evaluate_constant(specification.upper_bound)
                if isinstance(lower, (str, bool)) or isinstance(upper, (str, bool)):
                    raise self._error(
                        "Subrange-Grenzen müssen ganzzahlig sein.",
                        specification.position,
                    )
                lower = int(lower); upper = int(upper)
                if upper < lower:
                    raise self._error(
                        f"Ungültiger Subrange {lower}..{upper}.",
                        specification.position,
                    )
                signed = lower < 0
                if signed:
                    if -128 <= lower and upper <= 127:
                        size = 1
                    elif -32768 <= lower and upper <= 32767:
                        size = 2
                    elif -0x80000000 <= lower and upper <= 0x7FFFFFFF:
                        size = 4
                    else:
                        raise self._error(
                            f"Subrange außerhalb des 32-Bit-Bereichs: {lower}..{upper}.",
                            specification.position,
                        )
                else:
                    if upper <= 0xFF:
                        size = 1
                    elif upper <= 0xFFFF:
                        size = 2
                    elif upper <= 0xFFFFFFFF:
                        size = 4
                    else:
                        raise self._error(
                            f"Subrange außerhalb des 32-Bit-Bereichs: {lower}..{upper}.",
                            specification.position,
                        )
                type_info = _PascalType(
                    declaration.name, size, signed, "subrange",
                    lower_bound=lower, upper_bound=upper,
                )
            elif isinstance(specification, PointerTypeSpecification):
                target_type = self._resolve_type(
                    specification.target_type_name,
                    specification.position,
                )
                native_pointer = self.types.get("pointer", POINTER_TYPE)
                type_info = _PascalType(
                    declaration.name,
                    native_pointer.size,
                    False,
                    "pointer",
                    pointer_target=target_type,
                )
            elif isinstance(specification, EnumTypeSpecification):
                if not specification.names:
                    raise self._error("Ein Aufzählungstyp benötigt mindestens einen Wert.", specification.position)
                if len(specification.names) > 256:
                    raise self._error("Ein C64-Aufzählungstyp ist auf 256 Werte begrenzt.", specification.position)
                type_info = _PascalType(declaration.name, 1, False, "enum")
                self.types[key] = type_info
                for value, enum_name in enumerate(specification.names):
                    enum_key = self._key(enum_name)
                    if enum_key in self.constants or enum_key in self.variables or enum_key in self.types:
                        raise self._error(f"Bezeichner mehrfach deklariert: {enum_name}.", specification.position)
                    self.constants[enum_key] = value
                    self.constant_types[enum_key] = type_info
            elif isinstance(specification, RecordTypeSpecification):
                type_info = _PascalType(declaration.name, 0, False, "record")
                self.types[key] = type_info
                self._install_fields(type_info, specification.fields)
                if type_info.size == 0:
                    type_info.size = 1
            elif isinstance(specification, ArrayTypeSpecification):
                lower = self._evaluate_constant(specification.lower_bound)
                upper = self._evaluate_constant(specification.upper_bound)
                if isinstance(lower, (str, bool)) or isinstance(upper, (str, bool)):
                    raise self._error("Arraygrenzen müssen ganzzahlig sein.", specification.position)
                lower = int(lower)
                upper = int(upper)
                if upper < lower:
                    raise self._error(
                        f"Ungültiger Arraybereich {lower}..{upper}.",
                        specification.position,
                    )
                element_type = self._resolve_type(
                    specification.element_type_name,
                    specification.position,
                )
                element_count = upper - lower + 1
                size = element_count * self._value_storage_size(element_type)
                if size > 256:
                    raise self._error(
                        f"Statisches C64-Array ist mit {size} Bytes größer als 256 Bytes.",
                        specification.position,
                    )
                type_info = _PascalType(
                    declaration.name,
                    size,
                    False,
                    "array",
                    element_type=element_type,
                    lower_bound=lower,
                    upper_bound=upper,
                )
            elif isinstance(specification, ClassTypeSpecification):
                base_type = None
                if specification.base_type_name:
                    base_type = self._resolve_type(
                        specification.base_type_name,
                        specification.position,
                    )
                    if base_type.kind != "class":
                        raise self._error("Eine Klasse kann nur von einer Klasse erben.", specification.position)
                type_info = _PascalType(
                    declaration.name,
                    base_type.size if base_type is not None else 0,
                    False,
                    "class",
                    base_type=base_type,
                )
                if base_type is not None:
                    type_info.fields.update(base_type.fields)
                    type_info.methods.update(base_type.methods)
                    type_info.properties.update(base_type.properties)
                self.types[key] = type_info
                self._install_fields(type_info, specification.fields)
                if specification.abi_size is not None:
                    type_info.size = max(type_info.size, int(specification.abi_size))
                if type_info.size == 0:
                    type_info.size = 1
                self._install_methods(type_info, specification.methods)
                self._install_properties(type_info, specification.properties)
            else:
                raise self._error("Nicht unterstützte Typdefinition.", declaration.position)
            self.types[key] = type_info
            return type_info
        finally:
            self.resolving_types.discard(key)

    def _install_fields(
        self,
        owner: _PascalType,
        declarations: Sequence[FieldDeclaration],
    ) -> None:
        for declaration in declarations:
            field_type = self._resolve_type(declaration.type_name, declaration.position)
            for field_name in declaration.names:
                key = self._key(field_name)
                if key in owner.fields:
                    raise self._error(f"Feld mehrfach deklariert: {field_name}.", declaration.position)
                field_offset = (
                    owner.size
                    if declaration.offset is None
                    else int(declaration.offset)
                )
                owner.fields[key] = _FieldInfo(
                    field_name,
                    field_type,
                    field_offset,
                    declaration.position,
                )
                owner.size = max(
                    owner.size,
                    field_offset + self._value_storage_size(field_type),
                )
                if owner.size > 256:
                    raise self._error(
                        f"{owner.name} ist größer als 256 Bytes.",
                        declaration.position,
                    )

    def _install_properties(
        self,
        owner: _PascalType,
        declarations: Sequence[PropertyDeclaration],
    ) -> None:
        for declaration in declarations:
            key = self._key(declaration.name)
            if key in owner.fields or (
                key in owner.methods and owner.methods[key].owner is owner
            ):
                raise self._error(
                    f"Klassenmitglied mehrfach deklariert: {declaration.name}.",
                    declaration.position,
                )
            if key in owner.properties and (
                owner.base_type is None
                or owner.properties[key] is not owner.base_type.properties.get(key)
            ):
                raise self._error(
                    f"Property mehrfach deklariert: {declaration.name}.",
                    declaration.position,
                )
            property_type = self._resolve_type(
                declaration.type_name, declaration.position
            )
            parameters = tuple(
                _ParameterInfo(
                    parameter.names[0],
                    self._resolve_type(parameter.type_name, parameter.position),
                    parameter.modifier,
                    parameter.position,
                )
                for parameter in declaration.index_parameters
            )
            owner.properties[key] = _PropertyInfo(
                declaration.name,
                property_type,
                declaration.read_accessor,
                declaration.write_accessor,
                declaration.position,
                parameters,
            )

    def _install_methods(
        self,
        owner: _PascalType,
        declarations: Sequence[MethodDeclaration],
    ) -> None:
        for declaration in declarations:
            key = self._key(declaration.name)
            if key in owner.fields:
                raise self._error(
                    f"Klassenmitglied mehrfach deklariert: {declaration.name}.",
                    declaration.position,
                )
            parameters = tuple(
                _ParameterInfo(
                    parameter.names[0],
                    self._resolve_type(parameter.type_name, parameter.position),
                    parameter.modifier,
                    parameter.position,
                )
                for parameter in declaration.parameters
            )
            result_type = (
                self._resolve_type(declaration.result_type_name, declaration.position)
                if declaration.result_type_name
                else None
            )
            if declaration.kind == "function" and result_type is None:
                raise self._error("FUNCTION benötigt einen Rückgabetyp.", declaration.position)
            if declaration.kind != "function" and result_type is not None:
                raise self._error(
                    f"{declaration.kind.upper()} darf keinen Rückgabetyp besitzen.",
                    declaration.position,
                )
            if key in owner.methods and owner.methods[key].owner is owner:
                raise self._error(f"Methode mehrfach deklariert: {declaration.name}.", declaration.position)
            method_label = (
                declaration.external_symbol
                if declaration.external_symbol
                else f"__pas_method_{self._safe_name(owner.name)}_{self._safe_name(declaration.name)}"
            )
            method = _MethodInfo(
                owner,
                declaration.kind,
                declaration.name,
                parameters,
                result_type,
                declaration.position,
                method_label,
                is_virtual=("virtual" in declaration.directives),
                is_override=("override" in declaration.directives),
                is_class_method=declaration.is_class_method,
                visibility=declaration.visibility,
                is_external=bool(declaration.external_symbol),
            )
            owner.methods[key] = method
            if method.is_external:
                self.imported_method_symbols.add(method.label)
            else:
                self.methods.append(method)

    def _constant_declaration_type(
        self,
        declaration: ConstDeclaration,
        value: ScalarValue,
    ) -> _PascalType:
        expression = declaration.expression
        if isinstance(expression, (NameExpression, DesignatorExpression)):
            return self.constant_types.get(self._key(expression.name), self._constant_type(value))
        return self._constant_type(value)

    def _prepare_symbols(self) -> None:
        for declaration in self.program.types:
            key = self._key(declaration.name)
            previous_declaration = self.type_declarations.get(key)
            if (
                previous_declaration is not None
                and _type_declarations_equivalent(previous_declaration, declaration)
            ):
                # Identical compiler-generated/PUI declaration: one ABI type.
                continue
            if key in self.types:
                # Bootstrap-Units dürfen die elementaren Pascal-Typen durch ihre
                # kanonischen Subranges dokumentieren. Der aktive Backend-Typ
                # bleibt dabei maßgeblich (z.B. Integer/Pointer unter PE32).
                if (
                    key in {"boolean", "byte", "char"}
                    and isinstance(declaration.specification, SubrangeTypeSpecification)
                ):
                    continue
                raise self._error(
                    f"Datentyp mehrfach deklariert: {declaration.name}.",
                    declaration.position,
                )
            if key in self.type_declarations:
                raise self._error(f"Datentyp mehrfach deklariert: {declaration.name}.", declaration.position)
            self.type_declarations[key] = declaration

        for declaration in self.program.types:
            if isinstance(declaration.specification, EnumTypeSpecification):
                self._resolve_type(declaration.name, declaration.position)

        for declaration in self.program.constants:
            key = self._key(declaration.name)
            if key in self.constants or key in self.variables or key in self.types:
                raise self._error(
                    f"Bezeichner mehrfach deklariert: {declaration.name}.",
                    declaration.position,
                )
            value = self._evaluate_constant(declaration.expression)
            if isinstance(value, int):
                minimum, maximum = self._integer_constant_bounds()
                if not minimum <= value <= maximum:
                    raise self._error(
                        f"Konstante liegt außerhalb {minimum}..{maximum}: {value}.",
                        declaration.position,
                    )
            self.constants[key] = value
            self.constant_types[key] = self._constant_declaration_type(declaration, value)

        for declaration in self.program.types:
            self._resolve_type(declaration.name, declaration.position)

        for declaration in self.program.variables:
            type_info = self._resolve_type(declaration.type_name, declaration.position)
            for name in declaration.names:
                variable = self._declare_variable(
                    name,
                    type_info,
                    declaration.position,
                )
                if declaration.initializer is not None:
                    self.initializers.append((variable, declaration.initializer))

        self._prepare_external_routines()
        self._prepare_global_routines()
        self._prepare_method_implementations()

    def _prepare_global_routines(self) -> None:
        for implementation in self.program.global_routines:
            key = self._key(implementation.name)
            if key in self.global_routines:
                raise self._error(
                    f"Globale Routine mehrfach implementiert: {implementation.name}.",
                    implementation.position,
                )
            if key in self.external_routines:
                # A PUI declaration of a source-available Unit routine describes
                # the same routine from the consumer side.  When the Unit source
                # is statically merged, its implementation wins and the PUI
                # external must disappear.  An explicit EXTERNAL in the same
                # source (unit_name empty) remains an error.
                previous_external = self.external_routines[key]
                if previous_external.unit_name:
                    self.external_routines.pop(key, None)
                else:
                    raise self._error(
                        f"Globale Routine zugleich EXTERNAL und implementiert: {implementation.name}.",
                        implementation.position,
                    )
            parameters: List[_ParameterInfo] = []
            for item in implementation.parameters:
                if item.modifier == "var":
                    raise self._error(
                        f"Globale Routine {implementation.name}: VAR-Parameter werden "
                        "in dieser Stufe noch nicht unterstützt.",
                        item.position,
                    )
                parameters.append(
                    _ParameterInfo(
                        item.names[0],
                        self._resolve_type(item.type_name, item.position),
                        item.modifier,
                        item.position,
                    )
                )
            result_type = (
                self._resolve_type(implementation.result_type_name, implementation.position)
                if implementation.result_type_name
                else None
            )
            if implementation.kind == "function" and result_type is None:
                raise self._error(
                    f"FUNCTION {implementation.name} benötigt einen Rückgabetyp.",
                    implementation.position,
                )
            if implementation.kind != "function" and result_type is not None:
                raise self._error(
                    f"PROCEDURE {implementation.name} darf keinen Rückgabetyp besitzen.",
                    implementation.position,
                )
            if getattr(self, "unit_name", None):
                safe_unit = re.sub(r"[^A-Za-z0-9_]", "_", str(self.unit_name))
                label = f"__pas_{safe_unit}_{implementation.name}"
            else:
                label = f"__pas_global_{self._safe_name(implementation.name)}"
            routine = _GlobalRoutineInfo(
                implementation.kind,
                implementation.name,
                tuple(parameters),
                result_type,
                implementation.position,
                label,
                implementation,
                implementation.calling_convention,
            )
            local_names = set()
            parameter_variables = []
            for parameter in routine.parameters:
                pkey = self._key(parameter.name)
                if pkey in local_names:
                    raise self._error(
                        f"Parameter mehrfach deklariert: {parameter.name}.",
                        parameter.position,
                    )
                local_names.add(pkey)
                parameter_variables.append(
                    self._allocate_variable(
                        parameter.name,
                        parameter.type_info,
                        parameter.position,
                        internal=True,
                        label_prefix=f"param_global_{implementation.name}",
                    )
                )
            routine.parameter_variables = tuple(parameter_variables)
            for declaration in implementation.local_variables:
                local_type = self._resolve_type(declaration.type_name, declaration.position)
                for name in declaration.names:
                    lkey = self._key(name)
                    if lkey in local_names:
                        raise self._error(
                            f"Lokaler Bezeichner mehrfach deklariert: {name}.",
                            declaration.position,
                        )
                    local_names.add(lkey)
                    variable = self._allocate_variable(
                        name,
                        local_type,
                        declaration.position,
                        internal=True,
                        label_prefix=f"local_global_{implementation.name}",
                    )
                    routine.local_variables[lkey] = variable
                    if declaration.initializer is not None:
                        routine.local_initializers.append((variable, declaration.initializer))
            if routine.result_type is not None:
                routine.result_variable = self._allocate_variable(
                    "Result",
                    routine.result_type,
                    implementation.position,
                    internal=True,
                    label_prefix=f"result_global_{implementation.name}",
                )
            self.global_routines[key] = routine

    @staticmethod
    def _external_parameter_by_reference(parameter: _ParameterInfo) -> bool:
        """Return True when an EXTERNAL ABI parameter carries an address.

        VAR is always a caller-storage reference.  CONST remains value-like for
        scalar/pointer/class handles in this compiler stage, but aggregate
        records/arrays are passed by address.  This is the form used by Win32
        APIs such as RegisterClassA(const WNDCLASSA).
        """
        modifier = str(parameter.modifier or "value").casefold()
        return modifier == "var" or (
            modifier == "const"
            and parameter.type_info.kind in {"record", "array"}
        )

    def _external_value_types_compatible(
        self,
        parameter: _ParameterInfo,
        source: _PascalType,
    ) -> bool:
        """Object-Pascal compatibility plus narrow external ABI bridges.

        Win32 BOOL is declared by the runtime as an Integer-sized alias, while
        Pascal True/False have Boolean type.  The public parameter spelling is
        preserved in ``declared_type_name`` so only BOOL/LongBool parameters
        accept Boolean values.  Ordinary Integer parameters and assignments stay
        strict.
        """
        if self._types_compatible(parameter.type_info, source):
            return True
        declared = self._key(parameter.declared_type_name or "")
        if (
            source == BOOLEAN_TYPE
            and declared in {"bool", "longbool"}
            and parameter.type_info.kind in {"scalar", "enum", "subrange"}
            and int(parameter.type_info.size) == 4
        ):
            return True
        return False

    def _validate_external_value_argument(
        self,
        parameter: _ParameterInfo,
        argument: Expression,
        *,
        aggregate_message: str,
    ) -> _PascalType:
        """Validate a by-value EXTERNAL argument without emitting code.

        Pascal class instances are reference values even though the compiler's
        storage model classifies the instance layout itself as an aggregate.
        A Win32/Win64 Pointer parameter may therefore receive a class-valued
        expression such as Self: the emitted expression is the object address.
        Records/arrays remain forbidden by-value.
        """
        argument_type = self._expression_type(argument)
        class_as_pointer = (
            parameter.type_info.kind == "pointer"
            and argument_type.kind == "class"
        )
        if not class_as_pointer and (
            not argument_type.scalar or not parameter.type_info.scalar
        ):
            raise self._error(aggregate_message, argument.position)
        if not self._external_value_types_compatible(parameter, argument_type):
            expected_name = parameter.declared_type_name or parameter.type_info.name
            raise self._error(
                f"Argumenttyp {argument_type.name} passt nicht zu "
                f"{expected_name}.",
                argument.position,
            )
        return argument_type

    def _resolve_external_reference_argument(
        self,
        routine: _ExternalRoutineInfo,
        argument: Expression,
        parameter: _ParameterInfo,
    ) -> _StorageAccess:
        if not isinstance(argument, (NameExpression, DesignatorExpression)):
            raise self._error(
                f"Externe Routine {routine.name}: {parameter.modifier.upper()}-Parameter "
                f"{parameter.name} erwartet eine Variable.",
                argument.position,
            )
        access = self._resolve_storage(argument)
        if not self._types_compatible(parameter.type_info, access.type_info):
            raise self._error(
                f"Argumenttyp {access.type_info.name} passt nicht zu "
                f"{parameter.type_info.name}.",
                argument.position,
            )
        return access

    def _prepare_external_routines(self) -> None:
        for declaration in self.program.external_routines:
            key = self._key(declaration.name)
            if key in self.external_routines:
                previous = self.external_routines[key]
                if previous.symbol != declaration.symbol:
                    raise self._error(
                        f"Globale Routine mehrfach deklariert: {declaration.name}.",
                        SourcePosition(1, 1),
                    )
                continue
            parameters: List[_ParameterInfo] = []
            for item in declaration.parameters:
                modifier = str(item.modifier or "value").casefold()
                if modifier not in {"value", "var", "const"}:
                    raise self._error(
                        f"Externe Routine {declaration.name}: unbekannter "
                        f"Parametermodifikator {item.modifier}.",
                        item.position,
                    )
                parameters.append(
                    _ParameterInfo(
                        item.names[0],
                        self._resolve_type(item.type_name, item.position),
                        modifier,
                        item.position,
                        item.type_name,
                    )
                )
            result_type = (
                self._resolve_type(
                    declaration.result_type_name,
                    SourcePosition(1, 1),
                )
                if declaration.result_type_name
                else None
            )
            library = None
            if declaration.library_reference:
                reference = str(declaration.library_reference).strip()
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", reference):
                    value = self.constants.get(self._key(reference))
                    if value is None:
                        raise self._error(
                            f"EXTERNAL-DLL-Konstante nicht gefunden: {reference}.",
                            SourcePosition(1, 1),
                        )
                    if not isinstance(value, str):
                        raise self._error(
                            f"EXTERNAL-DLL-Konstante {reference} muss eine Zeichenkette sein.",
                            SourcePosition(1, 1),
                        )
                    library = value
                else:
                    library = reference
            self.external_routines[key] = _ExternalRoutineInfo(
                declaration.unit_name,
                declaration.kind,
                declaration.name,
                tuple(parameters),
                result_type,
                declaration.symbol,
                declaration.calling_convention,
                library,
                declaration.import_name or (declaration.name if library else None),
            )

    def _prepare_method_implementations(self) -> None:
        for implementation in self.program.methods:
            class_type = self._resolve_type(implementation.class_name, implementation.position)
            if class_type.kind != "class":
                raise self._error(
                    f"{implementation.class_name} ist keine Klasse.",
                    implementation.position,
                )
            method = class_type.methods.get(self._key(implementation.name))
            if method is None or method.owner is not class_type:
                raise self._error(
                    f"Methode nicht in {class_type.name} deklariert: {implementation.name}.",
                    implementation.position,
                )
            if method.implementation is not None:
                raise self._error(
                    f"Methode mehrfach implementiert: {class_type.name}.{method.name}.",
                    implementation.position,
                )
            if method.kind != implementation.kind:
                raise self._error("Methodenart stimmt nicht mit der Deklaration überein.", implementation.position)
            if len(method.parameters) != len(implementation.parameters):
                raise self._error("Parameterzahl stimmt nicht mit der Deklaration überein.", implementation.position)
            for expected, actual in zip(method.parameters, implementation.parameters):
                actual_type = self._resolve_type(actual.type_name, actual.position)
                if expected.type_info is not actual_type or self._key(expected.name) != self._key(actual.names[0]):
                    raise self._error("Methodenparameter stimmt nicht mit der Deklaration überein.", actual.position)
            actual_result = (
                self._resolve_type(implementation.result_type_name, implementation.position)
                if implementation.result_type_name
                else None
            )
            if method.result_type is not actual_result:
                raise self._error("Rückgabetyp stimmt nicht mit der Deklaration überein.", implementation.position)
            method.implementation = implementation

            parameter_variables = []
            local_names = set()
            for parameter in method.parameters:
                key = self._key(parameter.name)
                if key in local_names:
                    raise self._error(f"Parameter mehrfach deklariert: {parameter.name}.", parameter.position)
                local_names.add(key)
                parameter_variables.append(
                    self._allocate_variable(
                        parameter.name,
                        parameter.type_info,
                        parameter.position,
                        internal=True,
                        label_prefix=f"param_{class_type.name}_{method.name}",
                    )
                )
            method.parameter_variables = tuple(parameter_variables)

            for declaration in implementation.local_variables:
                local_type = self._resolve_type(declaration.type_name, declaration.position)
                for name in declaration.names:
                    key = self._key(name)
                    if key in local_names:
                        raise self._error(f"Lokaler Bezeichner mehrfach deklariert: {name}.", declaration.position)
                    local_names.add(key)
                    variable = self._allocate_variable(
                        name,
                        local_type,
                        declaration.position,
                        internal=True,
                        label_prefix=f"local_{class_type.name}_{method.name}",
                    )
                    method.local_variables[key] = variable
                    if declaration.initializer is not None:
                        method.local_initializers.append((variable, declaration.initializer))

            if method.result_type is not None:
                method.result_variable = self._allocate_variable(
                    "Result",
                    method.result_type,
                    implementation.position,
                    internal=True,
                    label_prefix=f"result_{class_type.name}_{method.name}",
                )

        for method in self.methods:
            if method.implementation is None:
                raise self._error(
                    f"Implementierung fehlt: {method.owner.name}.{method.name}.",
                    method.position,
                )

    def _integer_constant_bounds(self) -> Tuple[int, int]:
        # Native C64/Amiga bootstrap range retained for the legacy backends.
        return (-32768, 65535)

    def _constant_type(self, value: ScalarValue) -> _PascalType:
        if isinstance(value, str):
            return STRING_TYPE
        if isinstance(value, bool):
            return BOOLEAN_TYPE
        if 0 <= int(value) <= 255:
            return BYTE_TYPE
        return INTEGER_TYPE

    def _lookup_variable(self, name: str) -> Optional[_Variable]:
        key = self._key(name)
        variable = self.scope_variables.get(key)
        if variable is not None:
            return variable
        return self.variables.get(key)

    @staticmethod
    def _as_designator(
        expression: Union[str, NameExpression, DesignatorExpression],
        position: Optional[SourcePosition] = None,
    ) -> DesignatorExpression:
        if isinstance(expression, DesignatorExpression):
            return expression
        if isinstance(expression, str):
            if position is None:
                position = SourcePosition(1, 1)
            return DesignatorExpression(position, expression, ())
        return DesignatorExpression(expression.position, expression.name, ())

    def _resolve_storage(
        self,
        expression: Union[NameExpression, DesignatorExpression],
    ) -> _StorageAccess:
        designator = self._as_designator(expression)
        key = self._key(designator.name)
        variable = self._lookup_variable(designator.name)
        use_self = False
        base_label = None
        offset = 0

        direct_class_instance = False
        if variable is not None:
            type_info = variable.type_info
            base_label = variable.label
        elif self.current_method is not None and key == "self":
            type_info = self.current_method.owner
            use_self = True
            direct_class_instance = True
        elif self.current_method is not None and (
            key == "result" or key == self._key(self.current_method.name)
        ) and self.current_method.result_variable is not None:
            type_info = self.current_method.result_variable.type_info
            base_label = self.current_method.result_variable.label
        elif self.current_method is not None and key in self.current_method.owner.fields:
            field_info = self.current_method.owner.fields[key]
            type_info = field_info.type_info
            offset = field_info.offset
            use_self = True
        else:
            raise self._error(f"Variable nicht gefunden: {designator.name}.", designator.position)

        dynamic = None
        dereference_offsets: List[int] = []
        for selector in designator.selectors:
            if isinstance(selector, DereferenceSelector):
                if type_info.kind != "pointer" or type_info.pointer_target is None:
                    raise self._error(
                        f"{type_info.name} ist kein typisierter Pointer.",
                        selector.position,
                    )
                if dynamic is not None:
                    raise self._error(
                        "Pointer-Dereferenzierung nach variablem Arrayindex wird derzeit nicht unterstützt.",
                        selector.position,
                    )
                dereference_offsets.append(offset)
                offset = 0
                type_info = type_info.pointer_target
                continue

            if isinstance(selector, FieldSelector):
                if type_info.kind not in {"record", "class"}:
                    raise self._error(
                        f"{type_info.name} besitzt keine Felder.",
                        selector.position,
                    )
                # A class variable stores an object reference.  SELF is already
                # the instance address, but AppForm.Field / FChild.Field must
                # first load the pointer value from the class-reference slot.
                if type_info.kind == "class" and not direct_class_instance:
                    if dynamic is not None:
                        raise self._error(
                            "Klassenfeldzugriff nach variablem Arrayindex wird "
                            "derzeit noch nicht unterstützt.",
                            selector.position,
                        )
                    dereference_offsets.append(offset)
                    offset = 0
                    direct_class_instance = True
                field_info = type_info.fields.get(self._key(selector.name))
                if field_info is None:
                    raise self._error(
                        f"Feld nicht gefunden: {type_info.name}.{selector.name}.",
                        selector.position,
                    )
                offset += field_info.offset
                type_info = field_info.type_info
                direct_class_instance = False
                continue

            if not isinstance(selector, IndexSelector) or type_info.kind != "array":
                raise self._error(
                    f"{type_info.name} ist kein Array.",
                    selector.position,
                )
            assert type_info.element_type is not None
            if self._is_constant_expression(selector.expression):
                index_value = self._evaluate_constant(selector.expression)
            else:
                index_value = None
            if index_value is not None:
                if isinstance(index_value, (str, bool)):
                    raise self._error("Arrayindex muss ganzzahlig sein.", selector.position)
                index_value = int(index_value)
                if not type_info.lower_bound <= index_value <= type_info.upper_bound:
                    raise self._error(
                        f"Arrayindex {index_value} liegt außerhalb "
                        f"{type_info.lower_bound}..{type_info.upper_bound}.",
                        selector.position,
                    )
                offset += (
                    index_value - type_info.lower_bound
                ) * self._value_storage_size(type_info.element_type)
            else:
                if dynamic is not None:
                    raise self._error(
                        "Pro Zugriff wird zunächst nur ein variabler Arrayindex unterstützt.",
                        selector.position,
                    )
                dynamic = _DynamicAccess(
                    selector.expression,
                    type_info.lower_bound,
                    type_info.upper_bound - type_info.lower_bound + 1,
                    self._value_storage_size(type_info.element_type),
                    selector.position,
                )
            type_info = type_info.element_type

        return _StorageAccess(
            type_info,
            designator.position,
            base_label,
            use_self,
            offset,
            dynamic,
            tuple(dereference_offsets),
        )

    def _resolve_inherited_method(
        self,
        method_name: Optional[str],
        position: SourcePosition,
    ) -> Tuple[_MethodInfo, _StorageAccess]:
        if self.current_method is None:
            raise self._error(
                "INHERITED ist nur innerhalb einer Methode erlaubt.", position
            )
        base_type = self.current_method.owner.base_type
        if base_type is None:
            raise self._error(
                f"{self.current_method.owner.name} besitzt keine Basisklasse.",
                position,
            )
        name = method_name or self.current_method.name
        method = base_type.methods.get(self._key(name))
        if method is None:
            raise self._error(
                f"Geerbte Methode nicht gefunden: {base_type.name}.{name}.",
                position,
            )
        return method, _StorageAccess(
            base_type,
            position,
            None,
            True,
        )

    def _compile_inherited_call(self, statement: InheritedCallStatement) -> None:
        method, receiver = self._resolve_inherited_method(
            statement.method_name, statement.position
        )
        self._compile_method_call(
            method, receiver, statement.arguments, statement.position
        )

    def _compile_inherited_expression(
        self, expression: InheritedCallExpression
    ) -> _PascalType:
        method, receiver = self._resolve_inherited_method(
            expression.method_name, expression.position
        )
        if method.result_type is None:
            raise self._error(
                f"{method.owner.name}.{method.name} ist keine Funktion.",
                expression.position,
            )
        return self._compile_method_call(
            method, receiver, expression.arguments, expression.position
        )

    def _resolve_class_constructor_designator(
        self,
        designator: DesignatorExpression,
    ) -> Optional[Tuple[_PascalType, _MethodInfo]]:
        """Resolve ``TClass.Create`` without treating ``TClass`` as storage.

        Object-Pascal class identifiers live in the type namespace.  A
        constructor designator therefore has a class type as its receiver, not
        a variable slot.  Keeping this separate from _resolve_method_call()
        prevents ``TForm.Create`` from falling into _resolve_storage(TForm) and
        producing "Variable nicht gefunden: TForm".
        """
        if len(designator.selectors) != 1:
            return None
        selector = designator.selectors[0]
        if not isinstance(selector, FieldSelector):
            return None
        class_type = self.types.get(self._key(designator.name))
        if class_type is None or class_type.kind != "class":
            return None
        method = class_type.methods.get(self._key(selector.name))
        if method is None or method.kind != "constructor":
            return None
        return class_type, method

    def _compile_class_constructor_call(
        self,
        class_type: _PascalType,
        method: _MethodInfo,
        arguments: Sequence[Expression],
        position: SourcePosition,
    ) -> _PascalType:
        raise self._error(
            "Klassen-Konstruktoraufrufe als Ausdruck sind derzeit nur für "
            "Windows PE32/PE64 implementiert.",
            position,
        )

    def _node_uses_class_constructor(self, node: object) -> bool:
        """Small AST walk used before emitting import declarations."""
        if node is None or isinstance(node, (str, bytes, int, float, bool)):
            return False
        if isinstance(node, DesignatorExpression):
            if self._resolve_class_constructor_designator(node) is not None:
                return True
        if isinstance(node, CallExpression):
            designator = self._as_designator(node.designator, node.position)
            if self._resolve_class_constructor_designator(designator) is not None:
                return True
        if isinstance(node, (tuple, list)):
            return any(self._node_uses_class_constructor(item) for item in node)
        values = getattr(node, "__dict__", None)
        if isinstance(values, dict):
            return any(self._node_uses_class_constructor(value) for value in values.values())
        return False

    def _resolve_method_call(
        self,
        designator: DesignatorExpression,
    ) -> Tuple[_MethodInfo, _StorageAccess]:
        if designator.selectors and isinstance(designator.selectors[-1], FieldSelector):
            method_selector = designator.selectors[-1]
            receiver_designator = DesignatorExpression(
                designator.position,
                designator.name,
                designator.selectors[:-1],
            )
            receiver = self._resolve_storage(receiver_designator)
            if receiver.type_info.kind != "class":
                raise self._error(
                    f"{receiver.type_info.name} ist keine Klasse.",
                    method_selector.position,
                )
            method = receiver.type_info.methods.get(self._key(method_selector.name))
            if method is None:
                raise self._error(
                    f"Methode nicht gefunden: {receiver.type_info.name}.{method_selector.name}.",
                    method_selector.position,
                )
            return method, receiver

        if self.current_method is not None:
            method = self.current_method.owner.methods.get(self._key(designator.name))
            if method is not None:
                return method, _StorageAccess(
                    self.current_method.owner,
                    designator.position,
                    None,
                    True,
                )
        raise self._error(f"Methode nicht gefunden: {designator.name}.", designator.position)

    def _resolve_parameterless_function(
        self,
        designator: DesignatorExpression,
    ) -> Optional[Tuple[_MethodInfo, _StorageAccess]]:
        looks_like_method = (
            bool(designator.selectors)
            and isinstance(designator.selectors[-1], FieldSelector)
        ) or (
            not designator.selectors
            and self.current_method is not None
            and self._key(designator.name) in self.current_method.owner.methods
        )
        if not looks_like_method:
            return None
        try:
            method, receiver = self._resolve_method_call(designator)
        except C64PascalError:
            return None
        if method.parameters or method.result_type is None:
            return None
        return method, receiver

    def _routine_address_label(self, expression: AddressOfExpression) -> str:
        target = expression.target
        if target.selectors:
            raise self._error(
                "Adressoperator @ für Methoden/qualifizierte Routinen wird derzeit noch nicht unterstützt.",
                expression.position,
            )
        key = self._key(target.name)
        routine = self.global_routines.get(key)
        if routine is not None:
            return str(routine.label)
        if key in self.external_routines:
            raise self._error(
                f"Adresse einer importierten EXTERNAL-Routine wird derzeit noch nicht unterstützt: {target.name}.",
                expression.position,
            )
        raise self._error(
            f"Routine für Adressoperator @ nicht gefunden: {target.name}.",
            expression.position,
        )

    def _expression_type(self, expression: Expression) -> _PascalType:
        if isinstance(expression, LiteralExpression):
            return self._constant_type(expression.value)
        if isinstance(expression, (NameExpression, DesignatorExpression)):
            key = self._key(expression.name)
            if key == "nil" and (
                not isinstance(expression, DesignatorExpression)
                or not expression.selectors
            ):
                return self.types.get("pointer", POINTER_TYPE)
            if not isinstance(expression, DesignatorExpression) or not expression.selectors:
                if key in self.constants:
                    return self.constant_types.get(key, self._constant_type(self.constants[key]))
            if isinstance(expression, DesignatorExpression):
                constructor = self._resolve_class_constructor_designator(expression)
                if constructor is not None:
                    class_type, method = constructor
                    if method.parameters:
                        raise self._error(
                            f"{class_type.name}.{method.name} erwartet "
                            f"{len(method.parameters)} Argument(e).",
                            expression.position,
                        )
                    return class_type
            try:
                return self._resolve_storage(expression).type_info
            except C64PascalError:
                if isinstance(expression, DesignatorExpression):
                    resolved = self._resolve_parameterless_function(expression)
                    if resolved is not None:
                        method, unused_receiver = resolved
                        del unused_receiver
                        assert method.result_type is not None
                        return method.result_type
                raise
        if isinstance(expression, InheritedCallExpression):
            method, unused_receiver = self._resolve_inherited_method(
                expression.method_name, expression.position
            )
            del unused_receiver
            if method.result_type is None:
                raise self._error(
                    f"{method.owner.name}.{method.name} ist keine Funktion.",
                    expression.position,
                )
            return method.result_type
        if isinstance(expression, AddressOfExpression):
            self._routine_address_label(expression)
            return self.types.get("pointer", POINTER_TYPE)
        if isinstance(expression, CallExpression):
            designator = self._as_designator(expression.designator, expression.position)
            constructor = self._resolve_class_constructor_designator(designator)
            if constructor is not None:
                class_type, method = constructor
                self._require_argument_count(
                    f"{class_type.name}.{method.name}",
                    expression.arguments,
                    len(method.parameters),
                    expression.position,
                )
                return class_type
            if not designator.selectors:
                name = self._key(designator.name)
                cast_type = self.types.get(name)
                if cast_type is not None and len(expression.arguments) == 1:
                    return cast_type
                if name == "peek":
                    return BYTE_TYPE
                if name == "chr":
                    return CHAR_TYPE
                if name in {"ord", "lo", "hi"}:
                    return INTEGER_TYPE
                if name == "assigned":
                    self._require_argument_count(
                        designator.name, expression.arguments, 1, expression.position
                    )
                    argument_type = self._expression_type(expression.arguments[0])
                    if argument_type.kind not in {"pointer", "class"}:
                        raise self._error(
                            "ASSIGNED erwartet einen Pointer oder eine Klassenreferenz.",
                            expression.arguments[0].position,
                        )
                    return BOOLEAN_TYPE
                if name == "readln":
                    if len(expression.arguments) > 1:
                        raise self._error(
                            "READLN als Ausdruck erwartet hoechstens einen String-Prompt.",
                            expression.position,
                        )
                    if expression.arguments:
                        prompt_type = self._expression_type(expression.arguments[0])
                        if prompt_type.kind != "string":
                            raise self._error(
                                "READLN(Prompt) erwartet einen String-Prompt.",
                                expression.arguments[0].position,
                            )
                    return self.types.get("string", STRING_TYPE)

                # Globale Routinen aus C-Prototypen, #pragma-link-Modulen und
                # Pascal-PUI-Dateien muessen bereits bei der reinen
                # Typbestimmung beruecksichtigt werden. Andernfalls wird ein
                # Ausdruck wie
                #
                #     value | SetOf(element)
                #
                # faelschlich an die Klassenmethoden-Aufloesung weitergereicht
                # und endet mit "Methode nicht gefunden: SetOf".
                global_routine = self.global_routines.get(name)
                if global_routine is not None:
                    if global_routine.result_type is None:
                        raise self._error(
                            f"{global_routine.name} ist keine Funktion.",
                            expression.position,
                        )
                    return global_routine.result_type
                routine = self.external_routines.get(name)
                if routine is not None:
                    if routine.result_type is None:
                        raise self._error(
                            f"{routine.name} ist keine Funktion.",
                            expression.position,
                        )
                    return routine.result_type

            method, unused_receiver = self._resolve_method_call(designator)
            del unused_receiver
            if method.result_type is None:
                raise self._error(
                    f"{method.owner.name}.{method.name} ist keine Funktion.",
                    expression.position,
                )
            return method.result_type
        if isinstance(expression, UnaryExpression):
            return BOOLEAN_TYPE if expression.operator == "not" else self._expression_type(expression.operand)
        if isinstance(expression, BinaryExpression):
            if expression.operator in {"=", "<>", "<", "<=", ">", ">="}:
                return BOOLEAN_TYPE
            left = self._expression_type(expression.left)
            right = self._expression_type(expression.right)
            if left == STRING_TYPE or right == STRING_TYPE:
                raise self._error("Zeichenkettenarithmetik wird noch nicht unterstützt.", expression.position)
            if not left.scalar or not right.scalar:
                raise self._error("Operator erwartet skalare Operanden.", expression.position)
            if left == INTEGER_TYPE or right == INTEGER_TYPE:
                return INTEGER_TYPE
            return BYTE_TYPE
        raise self._error("Unbekannter Ausdruck.", expression.position)

    def _emit_load_literal(self, value: int, source_line: int) -> None:
        if not -32768 <= value <= 65535:
            raise C64PascalError(
                f"Ganzzahl liegt außerhalb -32768..65535: {value}.",
                source_line,
            )
        value &= 0xFFFF
        self.emitter.emit(f"    lda #${value & 0xFF:02X}", source_line)
        self.emitter.emit(f"    ldx #${value >> 8:02X}", source_line)

    @staticmethod
    def _petscii_bytes(text: str, position: SourcePosition) -> bytes:
        result = bytearray()
        for character in text:
            if character == "\n":
                result.append(13)
                continue

            if "a" <= character <= "z":
                result.append(ord(character) - ord("a") + 0x41)
                continue

            if "A" <= character <= "Z":
                result.append(ord(character) - ord("A") + 0xC1)
                continue

            code = ord(character)
            if code == 0 or code > 255:
                raise C64PascalError(
                    f"Zeichen U+{code:04X} kann nicht als PETSCII ausgegeben werden.",
                    position.line,
                    position.column - 1,
                )
            result.append(code)
        return bytes(result)

    def _string_label(self, text: str, position: SourcePosition) -> str:
        data = self._petscii_bytes(text, position)
        label = self.strings.get(data)
        if label is None:
            label = f"__pas_string_{len(self.strings)}"
            self.strings[data] = label
        return label

    def _compile_expr(self, expression: Expression) -> _PascalType:
        line = expression.position.line
        if isinstance(expression, AddressOfExpression):
            self._routine_address_label(expression)
            raise self._error(
                "Adressoperator @ ist für das C64-Backend noch nicht aktiviert.",
                expression.position,
            )
        if isinstance(expression, LiteralExpression):
            if isinstance(expression.value, str):
                label = self._string_label(expression.value, expression.position)
                self.emitter.emit(f"    lda #<{label}", line)
                self.emitter.emit(f"    ldx #>{label}", line)
                return STRING_TYPE
            self._emit_load_literal(int(expression.value), line)
            return self._constant_type(expression.value)

        if isinstance(expression, (NameExpression, DesignatorExpression)):
            key = self._key(expression.name)
            has_selectors = (
                isinstance(expression, DesignatorExpression)
                and bool(expression.selectors)
            )
            if key in self.constants and not has_selectors:
                value = self.constants[key]
                if isinstance(value, str):
                    label = self._string_label(value, expression.position)
                    self.emitter.emit(f"    lda #<{label}", line)
                    self.emitter.emit(f"    ldx #>{label}", line)
                    return STRING_TYPE
                self._emit_load_literal(int(value), line)
                return self.constant_types.get(key, self._constant_type(value))
            if isinstance(expression, DesignatorExpression):
                constructor = self._resolve_class_constructor_designator(expression)
                if constructor is not None:
                    class_type, method = constructor
                    return self._compile_class_constructor_call(
                        class_type, method, (), expression.position
                    )
            try:
                access = self._resolve_storage(expression)
            except C64PascalError:
                if isinstance(expression, DesignatorExpression):
                    resolved = self._resolve_parameterless_function(expression)
                    if resolved is not None:
                        method, receiver = resolved
                        return self._compile_method_call(
                            method,
                            receiver,
                            (),
                            expression.position,
                        )
                raise
            if not access.type_info.scalar:
                raise self._error(
                    f"{access.type_info.name} kann nicht als skalarer Ausdruck geladen werden.",
                    expression.position,
                )
            self._emit_load_access(access, line)
            return access.type_info

        if isinstance(expression, InheritedCallExpression):
            return self._compile_inherited_expression(expression)

        if isinstance(expression, CallExpression):
            return self._compile_function(expression)

        if isinstance(expression, UnaryExpression):
            operand_type = self._compile_expr(expression.operand)
            if operand_type == STRING_TYPE:
                raise self._error("Ungültiger Operator für String.", expression.position)
            if expression.operator == "+":
                return operand_type
            if expression.operator == "-":
                self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
                self.emitter.emit(f"    stx {self.ZP_LEFT_HI}", line)
                self.emitter.emit("    lda #$00", line)
                self.emitter.emit("    sec", line)
                self.emitter.emit(f"    sbc {self.ZP_LEFT_LO}", line)
                self.emitter.emit(f"    sta {self.ZP_RIGHT_LO}", line)
                self.emitter.emit("    lda #$00", line)
                self.emitter.emit(f"    sbc {self.ZP_LEFT_HI}", line)
                self.emitter.emit("    tax", line)
                self.emitter.emit(f"    lda {self.ZP_RIGHT_LO}", line)
                return INTEGER_TYPE
            if expression.operator == "not":
                false_label = self._new_label("not_false")
                end_label = self._new_label("not_end")
                self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
                self.emitter.emit("    txa", line)
                self.emitter.emit(f"    ora {self.ZP_LEFT_LO}", line)
                self.emitter.emit(f"    bne {false_label}", line)
                self._emit_load_literal(1, line)
                self.emitter.emit(f"    jmp {end_label}", line)
                self.emitter.emit(f"{false_label}:", line)
                self._emit_load_literal(0, line)
                self.emitter.emit(f"{end_label}:", line)
                return BOOLEAN_TYPE
            raise self._error(f"Unbekannter unärer Operator: {expression.operator}.", expression.position)

        if isinstance(expression, BinaryExpression):
            left_type = self._expression_type(expression.left)
            right_type = self._expression_type(expression.right)
            if left_type == STRING_TYPE or right_type == STRING_TYPE:
                raise self._error("String-Vergleiche und String-Arithmetik folgen in einer späteren Stufe.", expression.position)
            self._compile_expr(expression.left)
            self.emitter.emit("    pha", line)
            self.emitter.emit("    txa", line)
            self.emitter.emit("    pha", line)
            self._compile_expr(expression.right)
            self.emitter.emit(f"    sta {self.ZP_RIGHT_LO}", line)
            self.emitter.emit(f"    stx {self.ZP_RIGHT_HI}", line)
            self.emitter.emit("    pla", line)
            self.emitter.emit("    tax", line)
            self.emitter.emit("    pla", line)
            operator = expression.operator
            if operator in {"+", "-", "and", "or", "xor"}:
                self._emit_simple_binary(operator, line)
                if operator in {"and", "or", "xor"} and left_type == BOOLEAN_TYPE and right_type == BOOLEAN_TYPE:
                    return BOOLEAN_TYPE
                return INTEGER_TYPE if INTEGER_TYPE in {left_type, right_type} else BYTE_TYPE
            if operator == "*":
                self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
                self.emitter.emit(f"    stx {self.ZP_LEFT_HI}", line)
                self.runtime.add("mul16")
                self.emitter.emit("    jsr __pas_mul16", line)
                return INTEGER_TYPE
            if operator in {"div", "mod"}:
                self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
                self.emitter.emit(f"    stx {self.ZP_LEFT_HI}", line)
                self.runtime.add("div16")
                routine = "__pas_mod16" if operator == "mod" else "__pas_div16"
                self.emitter.emit(f"    jsr {routine}", line)
                return INTEGER_TYPE
            if operator == "/":
                raise self._error("Der Real-Operator '/' wird nicht unterstützt; verwende DIV.", expression.position)
            if operator in {"=", "<>", "<", "<=", ">", ">="}:
                signed = left_type.signed or right_type.signed
                self._emit_comparison(operator, signed, line)
                return BOOLEAN_TYPE
            raise self._error(f"Unbekannter Operator: {operator}.", expression.position)

        raise self._error("Ausdruck kann nicht übersetzt werden.", expression.position)

    @staticmethod
    def _label_with_offset(label: str, offset: int) -> str:
        return label if offset == 0 else f"{label}+{offset}"

    def _emit_dynamic_offset(self, access: _StorageAccess, line: int) -> None:
        dynamic = access.dynamic
        if dynamic is None:
            self.emitter.emit(f"    ldy #${access.constant_offset & 0xFF:02X}", line)
            return

        self._compile_expr(dynamic.expression)
        lower = dynamic.lower_bound & 0xFFFF
        self.emitter.emit("    sec", line)
        self.emitter.emit(f"    sbc #${lower & 0xFF:02X}", line)
        self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
        self.emitter.emit("    txa", line)
        self.emitter.emit(f"    sbc #${lower >> 8:02X}", line)
        self.emitter.emit("    tax", line)
        self.emitter.emit(f"    lda {self.ZP_LEFT_LO}", line)

        high_ok = self._new_label("index_high_ok")
        self.emitter.emit("    cpx #$00", line)
        self.emitter.emit(f"    beq {high_ok}", line)
        self.runtime.add("range_error")
        self.emitter.emit("    jmp __pas_range_error", line)
        self.emitter.emit(f"{high_ok}:", line)
        if dynamic.element_count < 256:
            range_ok = self._new_label("index_range_ok")
            self.emitter.emit(f"    cmp #${dynamic.element_count:02X}", line)
            self.emitter.emit(f"    bcc {range_ok}", line)
            self.emitter.emit("    jmp __pas_range_error", line)
            self.emitter.emit(f"{range_ok}:", line)

        if dynamic.stride != 1:
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
            self.emitter.emit(f"    stx {self.ZP_LEFT_HI}", line)
            self.emitter.emit(f"    lda #${dynamic.stride & 0xFF:02X}", line)
            self.emitter.emit(f"    sta {self.ZP_RIGHT_LO}", line)
            self.emitter.emit(f"    lda #${dynamic.stride >> 8:02X}", line)
            self.emitter.emit(f"    sta {self.ZP_RIGHT_HI}", line)
            self.runtime.add("mul16")
            self.emitter.emit("    jsr __pas_mul16", line)

        if access.constant_offset:
            self.emitter.emit("    clc", line)
            self.emitter.emit(f"    adc #${access.constant_offset & 0xFF:02X}", line)
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
            self.emitter.emit("    txa", line)
            self.emitter.emit(f"    adc #${access.constant_offset >> 8:02X}", line)
            self.emitter.emit("    tax", line)
            self.emitter.emit(f"    lda {self.ZP_LEFT_LO}", line)

        offset_ok = self._new_label("index_offset_ok")
        self.emitter.emit("    cpx #$00", line)
        self.emitter.emit(f"    beq {offset_ok}", line)
        self.emitter.emit("    jmp __pas_range_error", line)
        self.emitter.emit(f"{offset_ok}:", line)
        self.emitter.emit("    tay", line)

    def _emit_load_access(self, access: _StorageAccess, line: int) -> None:
        if access.dereference_offsets:
            raise self._error(
                "Postfix-Pointer-Dereferenzierung ist für dieses Backend noch nicht aktiviert.",
                access.position,
            )
        if access.type_info.size not in {1, 2}:
            raise self._error("Nur skalare 8- und 16-Bit-Werte können geladen werden.", access.position)
        if access.dynamic is None and not access.use_self:
            assert access.base_label is not None
            operand = self._label_with_offset(access.base_label, access.constant_offset)
            self.emitter.emit(f"    lda {operand}", line)
            if access.type_info.size == 2:
                self.emitter.emit(f"    ldx {self._label_with_offset(access.base_label, access.constant_offset + 1)}", line)
            else:
                self.emitter.emit("    ldx #$00", line)
            return

        self._emit_dynamic_offset(access, line)
        operand = f"({self.ZP_SELF_LO}),y" if access.use_self else f"{access.base_label},y"
        self.emitter.emit(f"    lda {operand}", line)
        if access.type_info.size == 2:
            self.emitter.emit("    pha", line)
            self.emitter.emit("    iny", line)
            self.emitter.emit(f"    lda {operand}", line)
            self.emitter.emit("    tax", line)
            self.emitter.emit("    pla", line)
        else:
            self.emitter.emit("    ldx #$00", line)

    def _emit_store_access(self, access: _StorageAccess, line: int) -> None:
        if access.dereference_offsets:
            raise self._error(
                "Postfix-Pointer-Dereferenzierung ist für dieses Backend noch nicht aktiviert.",
                access.position,
            )
        if access.type_info.size not in {1, 2}:
            raise self._error("Nur skalare 8- und 16-Bit-Werte können gespeichert werden.", access.position)
        if access.dynamic is None and not access.use_self:
            assert access.base_label is not None
            self.emitter.emit(
                f"    sta {self._label_with_offset(access.base_label, access.constant_offset)}",
                line,
            )
            if access.type_info.size == 2:
                self.emitter.emit(
                    f"    stx {self._label_with_offset(access.base_label, access.constant_offset + 1)}",
                    line,
                )
            return

        if access.dynamic is not None:
            self.emitter.emit(f"    sta {self.ZP_VALUE_LO}", line)
            self.emitter.emit(f"    stx {self.ZP_VALUE_HI}", line)
            self._emit_dynamic_offset(access, line)
            operand = f"({self.ZP_SELF_LO}),y" if access.use_self else f"{access.base_label},y"
            self.emitter.emit(f"    lda {self.ZP_VALUE_LO}", line)
            self.emitter.emit(f"    sta {operand}", line)
            if access.type_info.size == 2:
                self.emitter.emit("    iny", line)
                self.emitter.emit(f"    lda {self.ZP_VALUE_HI}", line)
                self.emitter.emit(f"    sta {operand}", line)
            return

        self.emitter.emit(f"    ldy #${access.constant_offset & 0xFF:02X}", line)
        self.emitter.emit(f"    sta ({self.ZP_SELF_LO}),y", line)
        if access.type_info.size == 2:
            self.emitter.emit("    iny", line)
            self.emitter.emit("    txa", line)
            self.emitter.emit(f"    sta ({self.ZP_SELF_LO}),y", line)

    def _emit_simple_binary(self, operator: str, line: int) -> None:
        instruction = {"and": "and", "or": "ora", "xor": "eor"}.get(operator)
        if operator == "+":
            self.emitter.emit("    clc", line)
            self.emitter.emit(f"    adc {self.ZP_RIGHT_LO}", line)
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
            self.emitter.emit("    txa", line)
            self.emitter.emit(f"    adc {self.ZP_RIGHT_HI}", line)
        elif operator == "-":
            self.emitter.emit("    sec", line)
            self.emitter.emit(f"    sbc {self.ZP_RIGHT_LO}", line)
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
            self.emitter.emit("    txa", line)
            self.emitter.emit(f"    sbc {self.ZP_RIGHT_HI}", line)
        else:
            self.emitter.emit(f"    {instruction} {self.ZP_RIGHT_LO}", line)
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
            self.emitter.emit("    txa", line)
            self.emitter.emit(f"    {instruction} {self.ZP_RIGHT_HI}", line)
        self.emitter.emit("    tax", line)
        self.emitter.emit(f"    lda {self.ZP_LEFT_LO}", line)

    def _emit_comparison(self, operator: str, signed: bool, line: int) -> None:
        self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
        self.emitter.emit(f"    stx {self.ZP_LEFT_HI}", line)
        true_label = self._new_label("cmp_true")
        false_label = self._new_label("cmp_false")
        end_label = self._new_label("cmp_end")

        if operator in {"=", "<>"}:
            self.emitter.emit(f"    cmp {self.ZP_RIGHT_LO}", line)
            self.emitter.emit(f"    bne {false_label if operator == '=' else true_label}", line)
            self.emitter.emit(f"    cpx {self.ZP_RIGHT_HI}", line)
            self.emitter.emit(f"    beq {true_label if operator == '=' else false_label}", line)
            self.emitter.emit(f"    jmp {false_label if operator == '=' else true_label}", line)
        else:
            less_label = self._new_label("cmp_less")
            greater_label = self._new_label("cmp_greater")
            compare_label = self._new_label("cmp_order")
            if signed:
                self.emitter.emit("    txa", line)
                self.emitter.emit(f"    eor {self.ZP_RIGHT_HI}", line)
                self.emitter.emit(f"    bpl {compare_label}", line)
                self.emitter.emit(f"    lda {self.ZP_LEFT_HI}", line)
                self.emitter.emit(f"    bmi {less_label}", line)
                self.emitter.emit(f"    jmp {greater_label}", line)
                self.emitter.emit(f"{compare_label}:", line)
            self.emitter.emit(f"    ldx {self.ZP_LEFT_HI}", line)
            self.emitter.emit(f"    cpx {self.ZP_RIGHT_HI}", line)
            self.emitter.emit(f"    bcc {less_label}", line)
            self.emitter.emit(f"    bne {greater_label}", line)
            self.emitter.emit(f"    lda {self.ZP_LEFT_LO}", line)
            self.emitter.emit(f"    cmp {self.ZP_RIGHT_LO}", line)
            self.emitter.emit(f"    bcc {less_label}", line)
            self.emitter.emit(f"    bne {greater_label}", line)
            target_equal = true_label if operator in {"<=", ">="} else false_label
            self.emitter.emit(f"    jmp {target_equal}", line)
            self.emitter.emit(f"{less_label}:", line)
            self.emitter.emit(f"    jmp {true_label if operator in {'<', '<='} else false_label}", line)
            self.emitter.emit(f"{greater_label}:", line)
            self.emitter.emit(f"    jmp {true_label if operator in {'>', '>='} else false_label}", line)

        self.emitter.emit(f"{false_label}:", line)
        self._emit_load_literal(0, line)
        self.emitter.emit(f"    jmp {end_label}", line)
        self.emitter.emit(f"{true_label}:", line)
        self._emit_load_literal(1, line)
        self.emitter.emit(f"{end_label}:", line)

    def _compile_external_call(
        self,
        routine: _ExternalRoutineInfo,
        arguments: Sequence[Expression],
        position: SourcePosition,
    ) -> _PascalType:
        """Erzeugt einen normalen rekursionsfesten 6510-Unit-Aufruf.

        Die ABI entspricht der getrennt kompilierten C64-C-ABI: Jedes skalare
        Argument wird in Quellreihenfolge als High-/Low-Byte auf den
        Hardwarestack gelegt. Der letzte Parameter liegt damit unmittelbar
        oberhalb der Ruecksprungadresse. Ein 16-Bit-Ergebnis kommt in A/X
        zurueck.
        """
        self._require_argument_count(
            routine.name, arguments, len(routine.parameters), position
        )
        line = position.line
        for argument, parameter in zip(arguments, routine.parameters):
            argument_type = self._compile_expr(argument)
            if not argument_type.scalar or not parameter.type_info.scalar:
                raise self._error(
                    "Aggregatparameter werden fuer externe Routinen noch nicht unterstuetzt.",
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
            # Rueckgabewert sichern, bevor der Hardwarestack bereinigt wird.
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
        return routine.result_type if routine.result_type is not None else BYTE_TYPE

    def _compile_function(self, expression: CallExpression) -> _PascalType:
        designator = self._as_designator(expression.designator, expression.position)
        name = self._key(designator.name) if not designator.selectors else ""
        line = expression.position.line
        if name == "peek":
            self._require_argument_count(designator.name, expression.arguments, 1, expression.position)
            self._compile_expr(expression.arguments[0])
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
            self.emitter.emit(f"    stx {self.ZP_LEFT_HI}", line)
            self.emitter.emit("    ldy #$00", line)
            self.emitter.emit(f"    lda ({self.ZP_LEFT_LO}),y", line)
            self.emitter.emit("    ldx #$00", line)
            return BYTE_TYPE
        if name in {"chr", "ord", "lo", "hi"}:
            self._require_argument_count(designator.name, expression.arguments, 1, expression.position)
            self._compile_expr(expression.arguments[0])
            if name in {"chr", "lo"}:
                self.emitter.emit("    ldx #$00", line)
            elif name == "hi":
                self.emitter.emit("    txa", line)
                self.emitter.emit("    ldx #$00", line)
            return CHAR_TYPE if name == "chr" else INTEGER_TYPE
        routine = self.external_routines.get(name)
        if routine is not None:
            if routine.result_type is None:
                raise self._error(
                    f"{routine.name} ist keine Funktion.",
                    expression.position,
                )
            return self._compile_external_call(
                routine, expression.arguments, expression.position
            )
        method, receiver = self._resolve_method_call(designator)
        if method.result_type is None:
            raise self._error(
                f"{method.owner.name}.{method.name} ist keine Funktion.",
                expression.position,
            )
        return self._compile_method_call(
            method,
            receiver,
            expression.arguments,
            expression.position,
        )

    def _types_compatible(self, target: _PascalType, source: _PascalType) -> bool:
        if target is source:
            return True
        if target.kind == "pointer":
            return source.kind in {"pointer", "class"}
        if source.kind == "pointer":
            return target.kind == "pointer"
        if target.kind == "string" or source.kind == "string":
            return target.kind == source.kind
        if target == BOOLEAN_TYPE or source == BOOLEAN_TYPE:
            return False
        numeric_kinds = {"scalar", "enum", "subrange"}
        return target.kind in numeric_kinds and source.kind in numeric_kinds

    def _emit_set_self_address(self, receiver: _StorageAccess, line: int) -> None:
        if receiver.dynamic is None and receiver.use_self and receiver.constant_offset == 0:
            return

        self._emit_dynamic_offset(receiver, line)
        if receiver.use_self:
            self.emitter.emit("    tya", line)
            self.emitter.emit("    clc", line)
            self.emitter.emit(f"    adc {self.ZP_SELF_LO}", line)
            self.emitter.emit(f"    sta {self.ZP_VALUE_LO}", line)
            self.emitter.emit(f"    lda {self.ZP_SELF_HI}", line)
            self.emitter.emit("    adc #$00", line)
            self.emitter.emit(f"    sta {self.ZP_VALUE_HI}", line)
            self.emitter.emit(f"    lda {self.ZP_VALUE_LO}", line)
            self.emitter.emit(f"    sta {self.ZP_SELF_LO}", line)
            self.emitter.emit(f"    lda {self.ZP_VALUE_HI}", line)
            self.emitter.emit(f"    sta {self.ZP_SELF_HI}", line)
            return

        assert receiver.base_label is not None
        self.emitter.emit("    tya", line)
        self.emitter.emit("    clc", line)
        self.emitter.emit(f"    adc #<{receiver.base_label}", line)
        self.emitter.emit(f"    sta {self.ZP_SELF_LO}", line)
        self.emitter.emit(f"    lda #>{receiver.base_label}", line)
        self.emitter.emit("    adc #$00", line)
        self.emitter.emit(f"    sta {self.ZP_SELF_HI}", line)

    def _compile_method_call(
        self,
        method: _MethodInfo,
        receiver: _StorageAccess,
        arguments: Sequence[Expression],
        position: SourcePosition,
    ) -> _PascalType:
        self._require_argument_count(method.name, arguments, len(method.parameters), position)
        line = position.line
        for argument, parameter, variable in zip(
            arguments,
            method.parameters,
            method.parameter_variables,
        ):
            argument_type = self._compile_expr(argument)
            if not argument_type.scalar or not parameter.type_info.scalar:
                raise self._error("Aggregatparameter werden noch nicht unterstützt.", argument.position)
            if not self._types_compatible(parameter.type_info, argument_type):
                raise self._error(
                    f"Argumenttyp {argument_type.name} passt nicht zu {parameter.type_info.name}.",
                    argument.position,
                )
            self._store_variable(variable, line)

        restore_self = self.current_method is not None
        if restore_self:
            self.emitter.emit(f"    lda {self.ZP_SELF_LO}", line)
            self.emitter.emit("    pha", line)
            self.emitter.emit(f"    lda {self.ZP_SELF_HI}", line)
            self.emitter.emit("    pha", line)

        self._emit_set_self_address(receiver, line)
        self.emitter.emit(f"    jsr {method.label}", line)

        if method.result_type is not None:
            if not method.result_type.scalar:
                raise self._error("Klassenfunktionen können nur skalare Werte zurückgeben.", position)
            self.emitter.emit(f"    sta {self.ZP_VALUE_LO}", line)
            self.emitter.emit(f"    stx {self.ZP_VALUE_HI}", line)

        if restore_self:
            self.emitter.emit("    pla", line)
            self.emitter.emit(f"    sta {self.ZP_SELF_HI}", line)
            self.emitter.emit("    pla", line)
            self.emitter.emit(f"    sta {self.ZP_SELF_LO}", line)

        if method.result_type is not None:
            self.emitter.emit(f"    lda {self.ZP_VALUE_LO}", line)
            self.emitter.emit(f"    ldx {self.ZP_VALUE_HI}", line)
            return method.result_type
        return BYTE_TYPE

    def _require_argument_count(
        self,
        name: str,
        arguments: Sequence[Expression],
        expected: int,
        position: SourcePosition,
    ) -> None:
        if len(arguments) != expected:
            raise self._error(
                f"{name} erwartet {expected} Argument(e), erhalten: {len(arguments)}.",
                position,
            )

    def _store_variable(self, variable: _Variable, line: int) -> None:
        self.emitter.emit(f"    sta {variable.label}", line)
        if variable.type_info.size == 2:
            self.emitter.emit(f"    stx {variable.label}+1", line)

    def _compile_assignment(self, statement: AssignmentStatement) -> None:
        designator = self._as_designator(statement.designator, statement.position)
        access = self._resolve_storage(designator)
        if not self._value_is_scalar(access.type_info):
            raise self._error(
                "Ganze Arrays oder Records können nicht direkt zugewiesen werden.",
                statement.position,
            )
        result_type = self._compile_expr(statement.expression)
        if result_type == STRING_TYPE:
            raise self._error("String-Variablen folgen in einer späteren Stufe.", statement.position)
        if not self._types_compatible(access.type_info, result_type):
            raise self._error(
                f"Zuweisung von {result_type.name} an {access.type_info.name} ist nicht zulässig.",
                statement.position,
            )
        self._emit_store_access(access, statement.position.line)

    def _compile_condition_jump_false(self, expression: Expression, target: str) -> None:
        line = expression.position.line
        result_type = self._compile_expr(expression)
        if result_type == STRING_TYPE:
            raise self._error("String kann nicht als Bedingung verwendet werden.", expression.position)
        continue_label = self._new_label("condition_true")
        self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
        self.emitter.emit("    txa", line)
        self.emitter.emit(f"    ora {self.ZP_LEFT_LO}", line)
        self.emitter.emit(f"    bne {continue_label}", line)
        self.emitter.emit(f"    jmp {target}", line)
        self.emitter.emit(f"{continue_label}:", line)

    @staticmethod
    def _raise_exception_create_message(statement: RaiseStatement) -> Expression:
        """Return the message argument of Exception.Create(message)."""
        expression = statement.expression
        if expression is None:
            raise C64PascalError(
                "RAISE ohne Exception-Ausdruck (RERAISE) wird erst mit TRY/EXCEPT-Unwinding unterstützt.",
                statement.position.line,
                statement.position.column - 1,
            )
        if not isinstance(expression, CallExpression):
            raise C64PascalError(
                "RAISE erwartet derzeit Exception.Create(<String>).",
                statement.position.line,
                statement.position.column - 1,
            )
        designator = expression.designator
        if not isinstance(designator, DesignatorExpression):
            raise C64PascalError(
                "RAISE erwartet derzeit Exception.Create(<String>).",
                statement.position.line,
                statement.position.column - 1,
            )
        selectors = designator.selectors
        is_exception_create = (
            designator.name.casefold() == "exception"
            and len(selectors) == 1
            and isinstance(selectors[0], FieldSelector)
            and selectors[0].name.casefold() == "create"
        )
        if not is_exception_create or len(expression.arguments) != 1:
            raise C64PascalError(
                "RAISE erwartet derzeit Exception.Create(<String>).",
                statement.position.line,
                statement.position.column - 1,
            )
        return expression.arguments[0]

    def _active_result_variable(self) -> Optional[_Variable]:
        if self.current_method is not None:
            return self.current_method.result_variable
        if self.current_global_routine is not None:
            return self.current_global_routine.result_variable
        return None

    def _compile_exit_statement(self, statement: ExitStatement) -> None:
        # C64 and Amiga routine methods both use RTS and their respective
        # _emit_load_access implementation to place function results in the
        # backend return register(s).  Windows overrides this for its stack
        # frame epilogues.
        if self.current_method is None and self.current_global_routine is None:
            raise self._error(
                "EXIT ist derzeit nur innerhalb einer Routine/Methode erlaubt.",
                statement.position,
            )
        result_variable = self._active_result_variable()
        if result_variable is not None:
            self._emit_load_access(
                _StorageAccess(
                    result_variable.type_info,
                    statement.position,
                    result_variable.label,
                    False,
                ),
                statement.position.line,
            )
        self.emitter.emit("    rts", statement.position.line)

    def _compile_raise_statement(self, statement: RaiseStatement) -> None:
        raise self._error(
            "RAISE ist derzeit nur für Windows PE32/PE64 implementiert.",
            statement.position,
        )

    def _compile_try_statement(self, statement: TryStatement) -> None:
        raise self._error(
            "TRY/EXCEPT/FINALLY ist derzeit nur für Windows PE32 implementiert.",
            statement.position,
        )

    def _compile_statement(self, statement: Statement) -> None:
        line = statement.position.line
        if isinstance(statement, CompoundStatement):
            for child in statement.statements:
                self._compile_statement(child)
            return
        if isinstance(statement, AssignmentStatement):
            self._compile_assignment(statement)
            return
        if isinstance(statement, InheritedCallStatement):
            self._compile_inherited_call(statement)
            return
        if isinstance(statement, ExitStatement):
            self._compile_exit_statement(statement)
            return
        if isinstance(statement, CallStatement):
            # Defensive compatibility for ASTs produced by third-party or old
            # parsers: never resolve a bare EXIT as a method named ``Exit``.
            designator = self._as_designator(statement.designator, statement.position)
            if (
                not designator.selectors
                and designator.name.casefold() == "exit"
                and not statement.arguments
            ):
                self._compile_exit_statement(ExitStatement(statement.position))
                return
            self._compile_call_statement(statement)
            return
        if isinstance(statement, RaiseStatement):
            self._compile_raise_statement(statement)
            return
        if isinstance(statement, TryStatement):
            self._compile_try_statement(statement)
            return
        if isinstance(statement, IfStatement):
            else_label = self._new_label("if_else")
            end_label = self._new_label("if_end")
            self._compile_condition_jump_false(statement.condition, else_label)
            self._compile_statement(statement.then_statement)
            self.emitter.emit(f"    jmp {end_label}", line)
            self.emitter.emit(f"{else_label}:", line)
            if statement.else_statement is not None:
                self._compile_statement(statement.else_statement)
            self.emitter.emit(f"{end_label}:", line)
            return
        if isinstance(statement, WhileStatement):
            condition_label = self._new_label("while_condition")
            end_label = self._new_label("while_end")
            self.emitter.emit(f"{condition_label}:", line)
            self._compile_condition_jump_false(statement.condition, end_label)
            self.break_targets.append(end_label)
            self.continue_targets.append(condition_label)
            try:
                self._compile_statement(statement.body)
            finally:
                self.continue_targets.pop()
                self.break_targets.pop()
            self.emitter.emit(f"    jmp {condition_label}", line)
            self.emitter.emit(f"{end_label}:", line)
            return
        if isinstance(statement, RepeatStatement):
            start_label = self._new_label("repeat_start")
            condition_label = self._new_label("repeat_condition")
            end_label = self._new_label("repeat_end")
            self.emitter.emit(f"{start_label}:", line)
            self.break_targets.append(end_label)
            self.continue_targets.append(condition_label)
            try:
                for child in statement.statements:
                    self._compile_statement(child)
            finally:
                self.continue_targets.pop()
                self.break_targets.pop()
            self.emitter.emit(f"{condition_label}:", line)
            self._compile_condition_jump_false(statement.condition, start_label)
            self.emitter.emit(f"{end_label}:", line)
            return
        if isinstance(statement, ForStatement):
            self._compile_for(statement)
            return
        if isinstance(statement, BreakStatement):
            if not self.break_targets:
                raise self._error("BREAK ist nur innerhalb einer Schleife erlaubt.", statement.position)
            self.emitter.emit(f"    jmp {self.break_targets[-1]}", line)
            return
        if isinstance(statement, ContinueStatement):
            if not self.continue_targets:
                raise self._error("CONTINUE ist nur innerhalb einer Schleife erlaubt.", statement.position)
            self.emitter.emit(f"    jmp {self.continue_targets[-1]}", line)
            return
        raise self._error("Anweisung wird nicht unterstützt.", statement.position)

    def _compile_for(self, statement: ForStatement) -> None:
        variable = self._lookup_variable(statement.name)
        if variable is None or variable.internal:
            raise self._error(f"FOR-Variable nicht gefunden: {statement.name}.", statement.position)
        if variable.type_info not in {INTEGER_TYPE, BYTE_TYPE, CHAR_TYPE}:
            raise self._error("FOR erwartet Integer, Byte oder Char.", statement.position)
        line = statement.position.line
        self._compile_expr(statement.initial)
        self._store_variable(variable, line)
        hidden_name = f"$for_limit_{self.label_counter}_{len(self.variable_order)}"
        limit = self._declare_variable(hidden_name, variable.type_info, statement.position, internal=True)
        self._compile_expr(statement.final)
        self._store_variable(limit, line)

        condition_label = self._new_label("for_condition")
        increment_label = self._new_label("for_step")
        end_label = self._new_label("for_end")
        self.emitter.emit(f"{condition_label}:", line)
        comparison = BinaryExpression(
            statement.position,
            DesignatorExpression(statement.position, statement.name),
            "<=" if statement.direction == "to" else ">=",
            DesignatorExpression(statement.position, hidden_name),
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
        self.emitter.emit(f"    lda {variable.label}", line)
        if statement.direction == "to":
            self.emitter.emit("    clc", line)
            self.emitter.emit("    adc #$01", line)
        else:
            self.emitter.emit("    sec", line)
            self.emitter.emit("    sbc #$01", line)
        self.emitter.emit(f"    sta {variable.label}", line)
        if variable.type_info.size == 2:
            self.emitter.emit(f"    lda {variable.label}+1", line)
            self.emitter.emit(f"    adc #$00" if statement.direction == "to" else "    sbc #$00", line)
            self.emitter.emit(f"    sta {variable.label}+1", line)
        self.emitter.emit(f"    jmp {condition_label}", line)
        self.emitter.emit(f"{end_label}:", line)

    def _compile_call_statement(self, statement: CallStatement) -> None:
        designator = self._as_designator(statement.designator, statement.position)
        name = self._key(designator.name) if not designator.selectors else ""
        line = statement.position.line

        # Echte C64-/Sprach-Builtins muessen vor den aus Headern oder PUI-Dateien
        # importierten Routinen behandelt werden. Ein Prototyp wie
        # ``void poke(uint16_t, uint8_t);`` liefert nur Typinformationen und
        # darf niemals einen externen ``jsr poke``-Aufruf erzeugen.
        if name in {"write", "writeln"}:
            for argument in statement.arguments:
                type_info = self._compile_expr(argument)
                if type_info == STRING_TYPE:
                    self.runtime.add("print_string")
                    self.emitter.emit("    jsr __pas_print_string", line)
                elif type_info == CHAR_TYPE:
                    self.emitter.emit("    jsr $FFD2", line)
                else:
                    self.runtime.update({"print_int16", "div16"})
                    self.emitter.emit("    jsr __pas_print_int16", line)
            if name == "writeln":
                self.emitter.emit("    lda #$0D", line)
                self.emitter.emit("    jsr $FFD2", line)
            return

        if name == "clrscr":
            self._require_argument_count(
                designator.name,
                statement.arguments,
                0,
                statement.position,
            )
            self.emitter.emit("    lda #$93", line)
            self.emitter.emit("    jsr $FFD2", line)
            return

        if name == "poke":
            self._require_argument_count(
                designator.name,
                statement.arguments,
                2,
                statement.position,
            )
            self._compile_expr(statement.arguments[0])
            self.emitter.emit("    pha", line)
            self.emitter.emit("    txa", line)
            self.emitter.emit("    pha", line)
            self._compile_expr(statement.arguments[1])
            self.emitter.emit(f"    sta {self.ZP_RIGHT_LO}", line)
            self.emitter.emit("    pla", line)
            self.emitter.emit(f"    sta {self.ZP_LEFT_HI}", line)
            self.emitter.emit("    pla", line)
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
            self.emitter.emit(f"    lda {self.ZP_RIGHT_LO}", line)
            self.emitter.emit("    ldy #$00", line)
            self.emitter.emit(f"    sta ({self.ZP_LEFT_LO}),y", line)
            return

        if name in {"inc", "dec"}:
            self._require_argument_count(
                designator.name,
                statement.arguments,
                1,
                statement.position,
            )
            argument = statement.arguments[0]
            if not isinstance(argument, (NameExpression, DesignatorExpression)):
                raise self._error(
                    f"{designator.name} erwartet eine Variable.",
                    statement.position,
                )
            target = self._as_designator(argument)
            target_type = self._resolve_storage(target).type_info
            if (
                target_type not in {INTEGER_TYPE, BYTE_TYPE, CHAR_TYPE}
                and target_type.kind != "enum"
            ):
                raise self._error(
                    f"{designator.name} erwartet einen ordinalen Wert.",
                    argument.position,
                )
            operation = "+" if name == "inc" else "-"
            self._compile_assignment(
                AssignmentStatement(
                    statement.position,
                    target,
                    BinaryExpression(
                        statement.position,
                        argument,
                        operation,
                        LiteralExpression(statement.position, 1),
                    ),
                )
            )
            return

        if name == "halt":
            self._require_argument_count(
                designator.name,
                statement.arguments,
                0,
                statement.position,
            )
            label = self._new_label("halt")
            self.emitter.emit(f"{label}:", line)
            self.emitter.emit(f"    jmp {label}", line)
            return

        # Erst nachdem alle direkten C64-Builtins ausgeschlossen wurden,
        # darf eine echte externe Unit-/C-Routine aufgeloest werden.
        routine = self.external_routines.get(name)
        if routine is not None:
            # Object Pascal permits a function call as a statement.  In that
            # form the function is executed normally and its result register is
            # intentionally ignored (e.g. DestroyWindow(FHandle);).
            self._compile_external_call(
                routine,
                statement.arguments,
                statement.position,
            )
            return

        if name in {"settextcolor", "amiga_set_text_color"}:
            raise self._error(
                "SetTextColor ist nur ueber die Unit System.Graphics verfuegbar.",
                statement.position,
            )

        method, receiver = self._resolve_method_call(designator)
        self._compile_method_call(
            method,
            receiver,
            statement.arguments,
            statement.position,
        )

    def _emit_methods(self) -> None:
        for method in self.methods:
            implementation = method.implementation
            if implementation is None:
                continue
            self.emitter.emit()
            self.emitter.emit(
                f"; {method.kind} {method.owner.name}.{method.name}",
                implementation.position.line,
            )
            self.emitter.emit(f"{method.label}:", implementation.position.line)

            previous_method = self.current_method
            previous_scope = self.scope_variables
            self.current_method = method
            self.scope_variables = {
                self._key(parameter.name): variable
                for parameter, variable in zip(
                    method.parameters,
                    method.parameter_variables,
                )
            }
            self.scope_variables.update(method.local_variables)
            if method.result_variable is not None:
                self.scope_variables["result"] = method.result_variable
                self.scope_variables[self._key(method.name)] = method.result_variable

            try:
                for variable in method.local_variables.values():
                    self.emitter.emit("    lda #$00", implementation.position.line)
                    for offset in range(variable.type_info.size):
                        self.emitter.emit(
                            f"    sta {self._label_with_offset(variable.label, offset)}",
                            implementation.position.line,
                        )
                if method.result_variable is not None:
                    self.emitter.emit("    lda #$00", implementation.position.line)
                    for offset in range(method.result_variable.type_info.size):
                        self.emitter.emit(
                            f"    sta {self._label_with_offset(method.result_variable.label, offset)}",
                            implementation.position.line,
                        )
                for variable, initializer in method.local_initializers:
                    result_type = self._compile_expr(initializer)
                    if not self._types_compatible(variable.type_info, result_type):
                        raise self._error(
                            f"Initialisierung von {variable.name} besitzt den falschen Typ.",
                            initializer.position,
                        )
                    self._store_variable(variable, initializer.position.line)
                self._compile_statement(implementation.body)
                if method.result_variable is not None:
                    self._emit_load_access(
                        _StorageAccess(
                            method.result_variable.type_info,
                            implementation.position,
                            method.result_variable.label,
                            False,
                        ),
                        implementation.position.line,
                    )
                self.emitter.emit("    rts", implementation.position.line)
            finally:
                self.scope_variables = previous_scope
                self.current_method = previous_method

    def _emit_runtime(self) -> None:
        if "range_error" in self.runtime:
            self.runtime.add("print_string")

        if "print_string" in self.runtime:
            self.emitter.emit()
            self.emitter.emit("; A/X = Adresse einer nullterminierten PETSCII-Zeichenkette")
            self.emitter.emit("__pas_print_string:")
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}")
            self.emitter.emit(f"    stx {self.ZP_LEFT_HI}")
            self.emitter.emit("__pas_print_string_loop:")
            self.emitter.emit("    ldy #$00")
            self.emitter.emit(f"    lda ({self.ZP_LEFT_LO}),y")
            self.emitter.emit("    beq __pas_print_string_done")
            self.emitter.emit("    jsr $FFD2")
            self.emitter.emit(f"    inc {self.ZP_LEFT_LO}")
            self.emitter.emit("    bne __pas_print_string_loop")
            self.emitter.emit(f"    inc {self.ZP_LEFT_HI}")
            self.emitter.emit("    jmp __pas_print_string_loop")
            self.emitter.emit("__pas_print_string_done:")
            self.emitter.emit("    rts")

        if "range_error" in self.runtime:
            self.emitter.emit()
            self.emitter.emit("; Laufzeitfehler bei variablem Arrayindex")
            self.emitter.emit("__pas_range_error:")
            self.emitter.emit("    lda #<__pas_range_error_text")
            self.emitter.emit("    ldx #>__pas_range_error_text")
            self.emitter.emit("    jsr __pas_print_string")
            self.emitter.emit("__pas_range_error_halt:")
            self.emitter.emit("    jmp __pas_range_error_halt")

        if "mul16" in self.runtime:
            self.emitter.emit()
            self.emitter.emit("; $FB/$FC * $FD/$FE, Ergebnis in A/X")
            self.emitter.emit("__pas_mul16:")
            self.emitter.emit("    lda #$00")
            self.emitter.emit("    sta __pas_rt_value")
            self.emitter.emit("    sta __pas_rt_value+1")
            self.emitter.emit("    ldy #$10")
            self.emitter.emit("__pas_mul16_loop:")
            self.emitter.emit(f"    lsr {self.ZP_RIGHT_HI}")
            self.emitter.emit(f"    ror {self.ZP_RIGHT_LO}")
            self.emitter.emit("    bcc __pas_mul16_no_add")
            self.emitter.emit("    clc")
            self.emitter.emit("    lda __pas_rt_value")
            self.emitter.emit(f"    adc {self.ZP_LEFT_LO}")
            self.emitter.emit("    sta __pas_rt_value")
            self.emitter.emit("    lda __pas_rt_value+1")
            self.emitter.emit(f"    adc {self.ZP_LEFT_HI}")
            self.emitter.emit("    sta __pas_rt_value+1")
            self.emitter.emit("__pas_mul16_no_add:")
            self.emitter.emit(f"    asl {self.ZP_LEFT_LO}")
            self.emitter.emit(f"    rol {self.ZP_LEFT_HI}")
            self.emitter.emit("    dey")
            self.emitter.emit("    bne __pas_mul16_loop")
            self.emitter.emit("    lda __pas_rt_value")
            self.emitter.emit("    ldx __pas_rt_value+1")
            self.emitter.emit("    rts")

        if "div16" in self.runtime:
            self.emitter.emit()
            self.emitter.emit("; unsigned 16-Bit DIV/MOD: $FB/$FC durch $FD/$FE")
            self.emitter.emit("__pas_div16:")
            self.emitter.emit("    lda #$00")
            self.emitter.emit("    sta __pas_rt_mode")
            self.emitter.emit("    jmp __pas_divmod16")
            self.emitter.emit("__pas_mod16:")
            self.emitter.emit("    lda #$01")
            self.emitter.emit("    sta __pas_rt_mode")
            self.emitter.emit("__pas_divmod16:")
            self.emitter.emit(f"    lda {self.ZP_RIGHT_LO}")
            self.emitter.emit(f"    ora {self.ZP_RIGHT_HI}")
            self.emitter.emit("    bne __pas_divmod_nonzero")
            self.emitter.emit("    lda #$00")
            self.emitter.emit("    tax")
            self.emitter.emit("    rts")
            self.emitter.emit("__pas_divmod_nonzero:")
            self.emitter.emit("    lda #$00")
            self.emitter.emit("    sta __pas_rt_remainder")
            self.emitter.emit("    sta __pas_rt_remainder+1")
            self.emitter.emit("    ldx #$10")
            self.emitter.emit("__pas_divmod_loop:")
            self.emitter.emit(f"    asl {self.ZP_LEFT_LO}")
            self.emitter.emit(f"    rol {self.ZP_LEFT_HI}")
            self.emitter.emit("    rol __pas_rt_remainder")
            self.emitter.emit("    rol __pas_rt_remainder+1")
            self.emitter.emit("    lda __pas_rt_remainder+1")
            self.emitter.emit(f"    cmp {self.ZP_RIGHT_HI}")
            self.emitter.emit("    bcc __pas_divmod_next")
            self.emitter.emit("    bne __pas_divmod_subtract")
            self.emitter.emit("    lda __pas_rt_remainder")
            self.emitter.emit(f"    cmp {self.ZP_RIGHT_LO}")
            self.emitter.emit("    bcc __pas_divmod_next")
            self.emitter.emit("__pas_divmod_subtract:")
            self.emitter.emit("    sec")
            self.emitter.emit("    lda __pas_rt_remainder")
            self.emitter.emit(f"    sbc {self.ZP_RIGHT_LO}")
            self.emitter.emit("    sta __pas_rt_remainder")
            self.emitter.emit("    lda __pas_rt_remainder+1")
            self.emitter.emit(f"    sbc {self.ZP_RIGHT_HI}")
            self.emitter.emit("    sta __pas_rt_remainder+1")
            self.emitter.emit(f"    inc {self.ZP_LEFT_LO}")
            self.emitter.emit("__pas_divmod_next:")
            self.emitter.emit("    dex")
            self.emitter.emit("    bne __pas_divmod_loop")
            self.emitter.emit("    lda __pas_rt_mode")
            self.emitter.emit("    bne __pas_divmod_return_remainder")
            self.emitter.emit(f"    lda {self.ZP_LEFT_LO}")
            self.emitter.emit(f"    ldx {self.ZP_LEFT_HI}")
            self.emitter.emit("    rts")
            self.emitter.emit("__pas_divmod_return_remainder:")
            self.emitter.emit("    lda __pas_rt_remainder")
            self.emitter.emit("    ldx __pas_rt_remainder+1")
            self.emitter.emit("    rts")

        if "print_int16" in self.runtime:
            self.emitter.emit()
            self.emitter.emit("; A/X = vorzeichenbehaftete 16-Bit-Zahl")
            self.emitter.emit("__pas_print_int16:")
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}")
            self.emitter.emit(f"    stx {self.ZP_LEFT_HI}")
            self.emitter.emit("    txa")
            self.emitter.emit("    bpl __pas_print_int16_positive")
            self.emitter.emit("    lda #$2D")
            self.emitter.emit("    jsr $FFD2")
            self.emitter.emit("    lda #$00")
            self.emitter.emit("    sec")
            self.emitter.emit(f"    sbc {self.ZP_LEFT_LO}")
            self.emitter.emit("    sta __pas_rt_value")
            self.emitter.emit("    lda #$00")
            self.emitter.emit(f"    sbc {self.ZP_LEFT_HI}")
            self.emitter.emit(f"    sta {self.ZP_LEFT_HI}")
            self.emitter.emit("    lda __pas_rt_value")
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}")
            self.emitter.emit("__pas_print_int16_positive:")
            self.emitter.emit(f"    lda {self.ZP_LEFT_LO}")
            self.emitter.emit(f"    ora {self.ZP_LEFT_HI}")
            self.emitter.emit("    bne __pas_print_int16_convert")
            self.emitter.emit("    lda #$30")
            self.emitter.emit("    jsr $FFD2")
            self.emitter.emit("    rts")
            self.emitter.emit("__pas_print_int16_convert:")
            self.emitter.emit("    lda #$00")
            self.emitter.emit("    sta __pas_rt_count")
            self.emitter.emit("__pas_print_int16_divide:")
            self.emitter.emit("    lda #$0A")
            self.emitter.emit(f"    sta {self.ZP_RIGHT_LO}")
            self.emitter.emit("    lda #$00")
            self.emitter.emit(f"    sta {self.ZP_RIGHT_HI}")
            self.emitter.emit("    jsr __pas_div16")
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}")
            self.emitter.emit(f"    stx {self.ZP_LEFT_HI}")
            self.emitter.emit("    lda __pas_rt_remainder")
            self.emitter.emit("    pha")
            self.emitter.emit("    inc __pas_rt_count")
            self.emitter.emit(f"    lda {self.ZP_LEFT_LO}")
            self.emitter.emit(f"    ora {self.ZP_LEFT_HI}")
            self.emitter.emit("    bne __pas_print_int16_divide")
            self.emitter.emit("; Ziffern wurden auf dem Hardware-Stack abgelegt")
            self.emitter.emit("__pas_print_int16_digits:")
            self.emitter.emit("    pla")
            self.emitter.emit("    clc")
            self.emitter.emit("    adc #$30")
            self.emitter.emit("    jsr $FFD2")
            self.emitter.emit("    dec __pas_rt_count")
            self.emitter.emit("    bne __pas_print_int16_digits")
            self.emitter.emit("    rts")

    def _emit_data(self) -> None:
        self.emitter.emit()
        self.emitter.emit("; Compiler-Laufzeitdaten")
        self.emitter.emit("__pas_rt_value:      .word 0")
        self.emitter.emit("__pas_rt_remainder:  .word 0")
        self.emitter.emit("__pas_rt_count:      .byte 0")
        self.emitter.emit("__pas_rt_mode:       .byte 0")

        if self.variable_order:
            self.emitter.emit()
            self.emitter.emit("; Pascal-Variablen")
            for variable in self.variable_order:
                initial_value = getattr(variable, "c_initial_value", None)
                if variable.type_info.size == 2:
                    directive = (
                        f".word ${int(initial_value) & 0xFFFF:04X}"
                        if initial_value is not None
                        else ".word 0"
                    )
                elif initial_value is not None and variable.type_info.size == 1:
                    directive = f".byte ${int(initial_value) & 0xFF:02X}"
                else:
                    directive = ".byte " + ", ".join(
                        "$00" for unused_offset in range(variable.type_info.size)
                    )
                comment = "intern" if variable.internal else variable.name
                self.emitter.emit(
                    f"{variable.label}: {directive} ; {comment}: {variable.type_info.name}"
                )

        if "range_error" in self.runtime:
            self.emitter.emit()
            self.emitter.emit(
                "__pas_range_error_text: .byte "
                "$49, $6E, $64, $65, $78, $20, $6F, $75, $74, $20, "
                "$6F, $66, $20, $72, $61, $6E, $67, $65, $0D, $00"
            )

        if self.strings:
            self.emitter.emit()
            self.emitter.emit("; Nullterminierte PETSCII-Zeichenketten")
            for data, label in self.strings.items():
                values = ", ".join(f"${value:02X}" for value in data + b"\x00")
                self.emitter.emit(f"{label}: .byte {values}")

    def generate(self) -> GeneratedAssembly:
        self._prepare_symbols()
        source_line = self.program.body.position.line
        self.emitter.emit("; Von C64 Pascal erzeugter MOS-6510-Assembler")
        self.emitter.emit(f"; Programm: {self.program.name}")
        self.emitter.emit(".org $080D")
        self.emitter.emit(".entry __pascal_start")
        self.emitter.emit(".basic")
        self.emitter.emit()
        self.emitter.emit("__pascal_start:", source_line)
        self.emitter.emit("    lda #$0E", source_line)
        self.emitter.emit("    jsr $FFD2", source_line)
        for variable, initializer in self.initializers:
            result_type = self._compile_expr(initializer)
            if result_type == STRING_TYPE:
                raise self._error("String-Variablen folgen in einer späteren Stufe.", initializer.position)
            if not variable.type_info.scalar:
                raise self._error("Aggregate können nicht direkt initialisiert werden.", initializer.position)
            if not self._types_compatible(variable.type_info, result_type):
                raise self._error(
                    f"Initialisierung von {variable.name} besitzt den falschen Typ.",
                    initializer.position,
                )
            self._store_variable(variable, initializer.position.line)
        self._compile_statement(self.program.body)
        self.emitter.emit("    rts", source_line)
        self._emit_methods()
        self._emit_runtime()
        self._emit_data()
        assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
        return GeneratedAssembly(
            self.program.name,
            assembly,
            dict(self.emitter.source_map),
            sum(not variable.internal for variable in self.variable_order),
            len(self.strings),
        )



class _PE64LayoutGenerator(_CodeGenerator):
    """Semantic-only Windows PE32+/AMD64 layout resolver.

    Stage 191 deliberately separates ABI layout from machine-code emission.
    Pure interface Units such as System.Types need correct 64-bit pointer
    sizes in their PUI even though they emit only a tiny AMD64 unit anchor.
    """

    def __init__(self, program: PascalProgram) -> None:
        super().__init__(program)
        self.types["integer"] = PE64_INTEGER_TYPE
        self.types["pointer"] = PE64_POINTER_TYPE
        self.types["string"] = PE64_STRING_TYPE


def _statement_contains_raise(statement: Statement) -> bool:
    if isinstance(statement, RaiseStatement):
        return True
    if isinstance(statement, CompoundStatement):
        return any(_statement_contains_raise(item) for item in statement.statements)
    if isinstance(statement, IfStatement):
        return (
            _statement_contains_raise(statement.then_statement)
            or (
                statement.else_statement is not None
                and _statement_contains_raise(statement.else_statement)
            )
        )
    if isinstance(statement, WhileStatement):
        return _statement_contains_raise(statement.body)
    if isinstance(statement, RepeatStatement):
        return any(_statement_contains_raise(item) for item in statement.statements)
    if isinstance(statement, ForStatement):
        return _statement_contains_raise(statement.body)
    if isinstance(statement, TryStatement):
        return (
            any(_statement_contains_raise(item) for item in statement.try_statements)
            or any(_statement_contains_raise(item) for item in statement.handler_statements)
        )
    return False


def _statement_contains_try(statement: Statement) -> bool:
    if isinstance(statement, TryStatement):
        return True
    if isinstance(statement, CompoundStatement):
        return any(_statement_contains_try(item) for item in statement.statements)
    if isinstance(statement, IfStatement):
        return (
            _statement_contains_try(statement.then_statement)
            or (statement.else_statement is not None and _statement_contains_try(statement.else_statement))
        )
    if isinstance(statement, WhileStatement):
        return _statement_contains_try(statement.body)
    if isinstance(statement, RepeatStatement):
        return any(_statement_contains_try(item) for item in statement.statements)
    if isinstance(statement, ForStatement):
        return _statement_contains_try(statement.body)
    return False


def _ast_contains_unqualified_call(node, target_name: str) -> bool:
    """Return True when an AST node contains an unqualified call by name.

    Stage 228 uses this before code generation so PE import directives for
    compiler builtins such as ReadLn can be emitted before the first code
    instruction.  Qualified calls (for example Obj.ReadLn) deliberately do
    not count as language builtins.
    """
    target = str(target_name).casefold()
    if isinstance(node, (CallStatement, CallExpression)):
        designator = node.designator
        if isinstance(designator, str):
            if designator.casefold() == target:
                return True
        elif (
            isinstance(designator, DesignatorExpression)
            and not designator.selectors
            and designator.name.casefold() == target
        ):
            return True
    if isinstance(node, (tuple, list)):
        return any(_ast_contains_unqualified_call(item, target) for item in node)
    dataclass_fields = getattr(type(node), "__dataclass_fields__", None)
    if dataclass_fields:
        for field_name in dataclass_fields:
            if field_name == "position":
                continue
            if _ast_contains_unqualified_call(getattr(node, field_name), target):
                return True
    return False


def _program_contains_builtin_call(program: PascalProgram, name: str) -> bool:
    return _ast_contains_unqualified_call(program, name)


def _program_contains_try(program: PascalProgram) -> bool:
    if _statement_contains_try(program.body):
        return True
    if any(_statement_contains_try(method.body) for method in program.methods):
        return True
    return any(_statement_contains_try(routine.body) for routine in program.global_routines)


def _program_contains_raise(program: PascalProgram) -> bool:
    if _statement_contains_raise(program.body):
        return True
    if any(_statement_contains_raise(method.body) for method in program.methods):
        return True
    return any(_statement_contains_raise(routine.body) for routine in program.global_routines)


class _PE32CodeGenerator(_CodeGenerator):
    """Erzeugt IA-32-Assembler fuer den integrierten Windows-PE32-Linker."""

    def __init__(
        self,
        program: PascalProgram,
        *,
        symbol_prefix: str = "__pas",
        language_name: str = "Pascal",
        graphics_backend: str = "Direct2D",
        console_mode: bool = True,
        library_name: Optional[str] = None,
        library_exports: Optional[Dict[str, str]] = None,
        unit_name: Optional[str] = None,
    ) -> None:
        super().__init__(program)
        # Delphi/Win32-compatible native widths used by bootstrap units.
        self.types["integer"] = PE32_INTEGER_TYPE
        self.types["pointer"] = PE32_POINTER_TYPE
        self.types["string"] = PE32_STRING_TYPE
        self.symbol_prefix = symbol_prefix
        self.language_name = language_name
        self.graphics_backend = str(graphics_backend or "Direct2D")
        self.console_mode = bool(console_mode)
        self.library_name = str(library_name) if library_name else None
        self.library_exports = dict(library_exports or {})
        self.unit_name = str(unit_name) if unit_name else None

        # Stage 227: every PE32/PE64 Pascal UNIT is a separate COFF object.
        # The integrated linker currently exposes assembler labels from each
        # object in one symbol namespace, so module-internal helper/data names
        # such as ``__pas_fmt_s`` must not be repeated by every UNIT.
        # Keep the historic ``__pas_*`` namespace for the main PROGRAM and
        # derive a deterministic module-local prefix for UNITs.  An explicitly
        # supplied non-default prefix remains authoritative.
        if self.unit_name and self.symbol_prefix == "__pas":
            safe_unit = re.sub(r"[^A-Za-z0-9_]", "_", self.unit_name)
            self.symbol_prefix = f"__pas_unit_{safe_unit}"
        self.uses_raise = _program_contains_raise(program)
        self.uses_try = _program_contains_try(program)
        self.uses_readln = _program_contains_builtin_call(program, "readln")
        self.exception_frames: List[Tuple[str, str]] = []

    def _value_storage_size(self, type_info: _PascalType) -> int:
        if type_info.kind == "class":
            return max(1, int(self.types.get("pointer", PE32_POINTER_TYPE).size))
        return super()._value_storage_size(type_info)

    def _value_is_scalar(self, type_info: _PascalType) -> bool:
        # Object-Pascal class *values* are references even though type_info.size
        # deliberately remains the complete instance/VMT layout size.
        return type_info.kind == "class" or super()._value_is_scalar(type_info)

    @classmethod
    def _pe32_parameter_stack_bytes(cls, parameters: Sequence[_ParameterInfo]) -> int:
        total = 0
        for parameter in parameters:
            if cls._external_parameter_by_reference(parameter):
                size = 4
            else:
                size = 4 if parameter.type_info.kind == "class" else max(1, int(parameter.type_info.size))
            total += max(4, (size + 3) & ~3)
        return total

    def _external_symbol(self, routine: _ExternalRoutineInfo) -> str:
        convention = str(routine.calling_convention or "").casefold()
        if convention == "stdcall":
            return f"_{routine.name}@{self._pe32_parameter_stack_bytes(routine.parameters)}"
        return str(routine.symbol)

    def _new_label(self, prefix: str) -> str:
        self.label_counter += 1
        return f"{self.symbol_prefix}_{prefix}_{self.label_counter}"

    def _integer_constant_bounds(self) -> Tuple[int, int]:
        # Win32/Win64 API constants are commonly expressed as unsigned DWORD
        # bit patterns while negative signed 32-bit values are valid too.
        return (-0x80000000, 0xFFFFFFFF)

    def _constant_type(self, value: ScalarValue) -> _PascalType:
        if isinstance(value, str):
            return self.types["string"]
        if isinstance(value, bool):
            return BOOLEAN_TYPE
        if 0 <= int(value) <= 255:
            return BYTE_TYPE
        return self.types["integer"]

    def _emit_load_literal(self, value: int, source_line: int) -> None:
        if not -0x80000000 <= int(value) <= 0xFFFFFFFF:
            raise self._error(
                f"Ganzzahl liegt ausserhalb des IA-32-Bereichs: {value}.",
                SourcePosition(source_line, 1),
            )
        self.emitter.emit(f"    mov eax, {int(value)}", source_line)

    @staticmethod
    def _windows_string_bytes(text: str, position: SourcePosition) -> bytes:
        try:
            return text.replace("\r\n", "\n").replace("\r", "\n").encode("latin-1")
        except UnicodeEncodeError as exc:
            character = text[exc.start]
            raise C64PascalError(
                f"Zeichen U+{ord(character):04X} kann nicht in eine Windows-Latin-1-Zeichenkette uebernommen werden.",
                position.line,
                position.column - 1,
            ) from exc

    def _string_label(self, text: str, position: SourcePosition) -> str:
        data = self._windows_string_bytes(text, position)
        label = self.strings.get(data)
        if label is None:
            label = f"{self.symbol_prefix}_string_{len(self.strings)}"
            self.strings[data] = label
        return label

    def _emit_address(self, access: _StorageAccess, line: int) -> None:
        dynamic = access.dynamic
        if dynamic is not None:
            self._compile_expr(dynamic.expression)
            if dynamic.lower_bound:
                self.emitter.emit(f"    sub eax, {int(dynamic.lower_bound)}", line)
            range_ok = self._new_label("index_range_ok")
            self.emitter.emit(f"    cmp eax, {int(dynamic.element_count)}", line)
            self.emitter.emit(f"    jb {range_ok}", line)
            self.runtime.add("range_error")
            self.emitter.emit(f"    jmp {self.symbol_prefix}_range_error", line)
            self.emitter.emit(f"{range_ok}:", line)
            if dynamic.stride != 1:
                self.emitter.emit(f"    mov edx, {int(dynamic.stride)}", line)
                self.emitter.emit("    imul eax, edx", line)
            self.emitter.emit("    mov edx, eax", line)

        if access.use_self:
            self.emitter.emit("    mov ecx, esi", line)
        else:
            assert access.base_label is not None
            self.emitter.emit(f"    mov ecx, {access.base_label}", line)

        for deref_offset in access.dereference_offsets:
            if deref_offset:
                self.emitter.emit(f"    add ecx, {int(deref_offset)}", line)
            self.emitter.emit("    mov ecx, dword ptr [ecx]", line)

        if dynamic is not None:
            self.emitter.emit("    add ecx, edx", line)
        if access.constant_offset:
            self.emitter.emit(f"    add ecx, {int(access.constant_offset)}", line)

    def _emit_load_access(self, access: _StorageAccess, line: int) -> None:
        value_size = self._value_storage_size(access.type_info)
        if value_size not in {1, 2, 4}:
            raise self._error(
                "Das PE32-Backend kann derzeit skalare 8-, 16- und 32-Bit-Werte laden "
                f"(Typ {access.type_info.name}, Wertgroesse {value_size} Byte, "
                f"Instanzgroesse {access.type_info.size} Byte).",
                access.position,
            )
        self._emit_address(access, line)
        if value_size == 1:
            self.emitter.emit("    movzx eax, byte ptr [ecx]", line)
        elif value_size == 2:
            instruction = "movsx" if access.type_info.signed else "movzx"
            self.emitter.emit(f"    {instruction} eax, word ptr [ecx]", line)
        else:
            self.emitter.emit("    mov eax, dword ptr [ecx]", line)

    def _emit_store_access(self, access: _StorageAccess, line: int) -> None:
        value_size = self._value_storage_size(access.type_info)
        if value_size not in {1, 2, 4}:
            raise self._error(
                "Das PE32-Backend kann derzeit skalare 8-, 16- und 32-Bit-Werte speichern "
                f"(Typ {access.type_info.name}, Wertgroesse {value_size} Byte, "
                f"Instanzgroesse {access.type_info.size} Byte).",
                access.position,
            )
        self.emitter.emit("    push eax", line)
        self._emit_address(access, line)
        self.emitter.emit("    pop eax", line)
        if value_size == 1:
            self.emitter.emit("    mov byte ptr [ecx], al", line)
        elif value_size == 2:
            self.emitter.emit("    mov word ptr [ecx], ax", line)
        else:
            self.emitter.emit("    mov dword ptr [ecx], eax", line)

    def _store_variable(self, variable: _Variable, line: int) -> None:
        self._emit_store_access(
            _StorageAccess(variable.type_info, variable.position, variable.label, False),
            line,
        )

    def _zero_variable(self, variable: _Variable, line: int) -> None:
        """Zero-initialize one PE32 local variable.

        Scalar values keep the historic EAX/store path.  Real Pascal
        aggregates (records/arrays) occupy their complete value size and must
        be cleared in-place instead of being routed through _store_variable(),
        which intentionally only handles scalar-width stores.
        """
        value_size = self._value_storage_size(variable.type_info)
        if self._value_is_scalar(variable.type_info) and value_size in {1, 2, 4}:
            self.emitter.emit("    xor eax, eax", line)
            self._store_variable(variable, line)
            return

        if variable.type_info.kind not in {"record", "array"}:
            raise self._error(
                f"Lokale Variable {variable.name} vom Typ {variable.type_info.name} "
                f"({value_size} Byte) kann im PE32-Backend nicht nullinitialisiert werden.",
                variable.position,
            )

        access = _StorageAccess(
            variable.type_info, variable.position, variable.label, False
        )
        self._emit_address(access, line)
        offset = 0
        while value_size - offset >= 4:
            operand = "[ecx]" if offset == 0 else f"[ecx+{offset}]"
            self.emitter.emit(f"    mov dword ptr {operand}, 0", line)
            offset += 4
        if value_size - offset >= 2:
            operand = "[ecx]" if offset == 0 else f"[ecx+{offset}]"
            self.emitter.emit(f"    mov word ptr {operand}, 0", line)
            offset += 2
        if value_size - offset:
            operand = "[ecx]" if offset == 0 else f"[ecx+{offset}]"
            self.emitter.emit(f"    mov byte ptr {operand}, 0", line)

    def _emit_comparison(self, operator: str, signed: bool, line: int) -> None:
        if signed:
            instruction = {"=":"sete", "<>":"setne", "<":"setl", "<=":"setle", ">":"setg", ">=":"setge"}[operator]
        else:
            instruction = {"=":"sete", "<>":"setne", "<":"setb", "<=":"setbe", ">":"seta", ">=":"setae"}[operator]
        self.emitter.emit("    cmp eax, edx", line)
        self.emitter.emit(f"    {instruction} al", line)
        self.emitter.emit("    movzx eax, al", line)

    def _compile_expr(self, expression: Expression) -> _PascalType:
        line = expression.position.line
        if isinstance(expression, AddressOfExpression):
            label = self._routine_address_label(expression)
            self.emitter.emit(f"    mov eax, {label}", line)
            return self.types.get("pointer", PE32_POINTER_TYPE)

        if isinstance(expression, LiteralExpression):
            if isinstance(expression.value, str):
                label = self._string_label(expression.value, expression.position)
                self.emitter.emit(f"    mov eax, {label}", line)
                return self.types.get("string", PE32_STRING_TYPE)
            self._emit_load_literal(int(expression.value), line)
            return self._constant_type(expression.value)

        if isinstance(expression, (NameExpression, DesignatorExpression)):
            key = self._key(expression.name)
            has_selectors = isinstance(expression, DesignatorExpression) and bool(expression.selectors)
            if key == "nil" and not has_selectors:
                self.emitter.emit("    xor eax, eax", line)
                return self.types.get("pointer", PE32_POINTER_TYPE)
            if key in self.constants and not has_selectors:
                value = self.constants[key]
                if isinstance(value, str):
                    label = self._string_label(value, expression.position)
                    self.emitter.emit(f"    mov eax, {label}", line)
                    return self.types.get("string", PE32_STRING_TYPE)
                self._emit_load_literal(int(value), line)
                return self.constant_types.get(key, self._constant_type(value))
            if isinstance(expression, DesignatorExpression):
                constructor = self._resolve_class_constructor_designator(expression)
                if constructor is not None:
                    class_type, method = constructor
                    return self._compile_class_constructor_call(
                        class_type, method, (), expression.position
                    )
            try:
                access = self._resolve_storage(expression)
            except C64PascalError:
                if isinstance(expression, DesignatorExpression):
                    resolved = self._resolve_parameterless_function(expression)
                    if resolved is not None:
                        method, receiver = resolved
                        return self._compile_method_call(method, receiver, (), expression.position)
                raise
            if access.type_info.kind == "class":
                if key == "self" and not has_selectors:
                    self.emitter.emit("    mov eax, esi", line)
                else:
                    self._emit_load_access(access, line)
                return access.type_info
            if not access.type_info.scalar:
                raise self._error(
                    f"{access.type_info.name} kann nicht als skalarer Ausdruck geladen werden.",
                    expression.position,
                )
            self._emit_load_access(access, line)
            return access.type_info

        if isinstance(expression, InheritedCallExpression):
            return self._compile_inherited_expression(expression)

        if isinstance(expression, CallExpression):
            return self._compile_function(expression)

        if isinstance(expression, UnaryExpression):
            operand_type = self._compile_expr(expression.operand)
            if operand_type.kind == "string":
                raise self._error("Ungueltiger Operator fuer String.", expression.position)
            if expression.operator == "+":
                return operand_type
            if expression.operator == "-":
                self.emitter.emit("    neg eax", line)
                return INTEGER_TYPE
            if expression.operator == "not":
                self.emitter.emit("    cmp eax, 0", line)
                self.emitter.emit("    sete al", line)
                self.emitter.emit("    movzx eax, al", line)
                return BOOLEAN_TYPE
            raise self._error(f"Unbekannter unaerer Operator: {expression.operator}.", expression.position)

        if isinstance(expression, BinaryExpression):
            left_type = self._expression_type(expression.left)
            right_type = self._expression_type(expression.right)
            if left_type.kind == "string" or right_type.kind == "string":
                raise self._error("String-Vergleiche und String-Arithmetik werden nicht unterstuetzt.", expression.position)
            self._compile_expr(expression.left)
            self.emitter.emit("    push eax", line)
            self._compile_expr(expression.right)
            self.emitter.emit("    mov edx, eax", line)
            self.emitter.emit("    pop eax", line)
            operator = expression.operator
            if operator in {"+", "-", "and", "or", "xor"}:
                instruction = {"+":"add", "-":"sub", "and":"and", "or":"or", "xor":"xor"}[operator]
                self.emitter.emit(f"    {instruction} eax, edx", line)
                if operator in {"and", "or", "xor"} and left_type == BOOLEAN_TYPE and right_type == BOOLEAN_TYPE:
                    return BOOLEAN_TYPE
                return INTEGER_TYPE if INTEGER_TYPE in {left_type, right_type} else BYTE_TYPE
            if operator == "*":
                self.emitter.emit("    imul eax, edx", line)
                return INTEGER_TYPE
            if operator in {"div", "mod"}:
                self.emitter.emit("    mov ecx, edx", line)
                self.emitter.emit("    cdq", line)
                self.emitter.emit("    idiv ecx", line)
                if operator == "mod":
                    self.emitter.emit("    mov eax, edx", line)
                return INTEGER_TYPE
            if operator == "/":
                raise self._error("Der Real-Operator '/' wird nicht unterstuetzt; verwende DIV.", expression.position)
            if operator in {"=", "<>", "<", "<=", ">", ">="}:
                self._emit_comparison(operator, left_type.signed or right_type.signed, line)
                return BOOLEAN_TYPE
            raise self._error(f"Unbekannter Operator: {operator}.", expression.position)

        raise self._error("Ausdruck kann nicht uebersetzt werden.", expression.position)

    def _compile_exit_statement(self, statement: ExitStatement) -> None:
        if self.current_method is None and self.current_global_routine is None:
            raise self._error(
                "EXIT ist derzeit nur innerhalb einer Routine/Methode erlaubt.",
                statement.position,
            )
        line = statement.position.line
        result_variable = self._active_result_variable()
        if result_variable is not None:
            self._emit_load_access(
                _StorageAccess(
                    result_variable.type_info,
                    statement.position,
                    result_variable.label,
                    False,
                ),
                line,
            )
        self.emitter.emit("    mov esp, ebp", line)
        self.emitter.emit("    pop ebp", line)
        if self.current_global_routine is not None:
            convention = str(
                self.current_global_routine.calling_convention or "cdecl"
            ).casefold()
            if convention == "stdcall":
                cleanup = self._pe32_parameter_stack_bytes(
                    self.current_global_routine.parameters
                )
                self.emitter.emit(
                    f"    ret {cleanup}" if cleanup else "    ret", line
                )
                return
        self.emitter.emit("    ret", line)

    def _compile_raise_statement(self, statement: RaiseStatement) -> None:
        message = self._raise_exception_create_message(statement)
        message_type = self._compile_expr(message)
        if message_type.kind != "string":
            raise self._error(
                "Exception.Create in RAISE erwartet einen String als Nachricht.",
                message.position,
            )
        line = statement.position.line
        # Established NT32 runtime ABI:
        #   _jit_raise(JIT_USER_EXCEPTION=7, const char *message)
        # cdecl arguments are pushed right-to-left.
        self.emitter.emit("    push eax", line)
        self.emitter.emit("    push 7", line)
        self.emitter.emit("    call _jit_raise", line)
        self.emitter.emit("    add esp, 8", line)

    def _new_exception_frame(self) -> Tuple[str, str]:
        env_label = self._new_label("exc_env")
        frame_label = self._new_label("exc_frame")
        self.exception_frames.append((env_label, frame_label))
        return env_label, frame_label

    def _emit_exception_checkpoint(
        self,
        env_label: str,
        handler_label: str,
        line: int,
    ) -> None:
        """Store a native IA-32 longjmp target without a C wrapper frame.

        ``_jit_setjmp`` is exported through a normal C wrapper by the current
        PE32 runtime.  A later ``longjmp`` therefore resumes inside a wrapper
        invocation which has already returned.  Depending on the compiler
        prologue/epilogue used for the runtime DLL, that stale frame corrupts
        ESP before control reaches the Pascal EXCEPT block.

        The six dwords below are the established ``JitJumpBuffer`` ABI:
        EBX, ESI, EDI, EBP, ESP and EIP.  Saving the Pascal handler address
        directly makes the non-local jump independent of the runtime
        wrapper's private stack frame.
        """
        self.emitter.emit(f"    mov dword ptr [{env_label}+0], ebx", line)
        self.emitter.emit(f"    mov dword ptr [{env_label}+4], esi", line)
        self.emitter.emit(f"    mov dword ptr [{env_label}+8], edi", line)
        self.emitter.emit(f"    mov dword ptr [{env_label}+12], ebp", line)
        self.emitter.emit(f"    mov dword ptr [{env_label}+16], esp", line)
        self.emitter.emit(
            f"    mov dword ptr [{env_label}+20], {handler_label}", line
        )

    def _emit_exception_pop(self, line: int) -> None:
        self.emitter.emit("    call _jit_exception_pop", line)

    def _compile_try_statement(self, statement: TryStatement) -> None:
        line = statement.position.line
        env_label, frame_label = self._new_exception_frame()
        handler_label = self._new_label("try_handler")
        end_label = self._new_label("try_end")

        # JitExceptionFrame.env must point at its 24-byte IA-32 jump buffer
        # before _jit_exception_push initializes code/message/prev.
        self.emitter.emit(f"    mov dword ptr [{frame_label}], {env_label}", line)
        self.emitter.emit(f"    push {frame_label}", line)
        self.emitter.emit("    call _jit_exception_push", line)
        self.emitter.emit("    add esp, 4", line)
        self._emit_exception_checkpoint(env_label, handler_label, line)

        for child in statement.try_statements:
            self._compile_statement(child)

        self._emit_exception_pop(line)
        if statement.handler_kind == "except":
            self.emitter.emit(f"    jmp {end_label}", line)
            self.emitter.emit(f"{handler_label}:", line)
            # Pop before executing the handler so a RAISE inside EXCEPT is
            # handled by the surrounding exception frame instead of itself.
            self._emit_exception_pop(line)
            for child in statement.handler_statements:
                self._compile_statement(child)
            self.emitter.emit(f"{end_label}:", line)
            return

        if statement.handler_kind == "finally":
            for child in statement.handler_statements:
                self._compile_statement(child)
            self.emitter.emit(f"    jmp {end_label}", line)
            self.emitter.emit(f"{handler_label}:", line)
            self._emit_exception_pop(line)
            for child in statement.handler_statements:
                self._compile_statement(child)
            # Re-raise the captured exception code.  The current runtime does
            # not persist the message text in JitExceptionFrame yet, so pass
            # null for the rethrow message while preserving the exception code.
            self.emitter.emit(f"    mov eax, dword ptr [{frame_label}+4]", line)
            self.emitter.emit("    push 0", line)
            self.emitter.emit("    push eax", line)
            self.emitter.emit("    call _jit_raise", line)
            self.emitter.emit("    add esp, 8", line)
            self.emitter.emit(f"{end_label}:", line)
            return

        raise self._error("Unbekannte TRY-Handlerart.", statement.position)

    def _compile_external_call(self, routine, arguments, position):
        self._require_argument_count(
            routine.name, arguments, len(routine.parameters), position
        )

        # Validate all arguments before emitting the call.  VAR parameters and
        # aggregate CONST parameters are true by-reference ABI arguments.
        for argument, parameter in zip(arguments, routine.parameters):
            if self._external_parameter_by_reference(parameter):
                self._resolve_external_reference_argument(
                    routine, argument, parameter
                )
                continue
            self._validate_external_value_argument(
                parameter,
                argument,
                aggregate_message=(
                    "Aggregat-Wertparameter werden fuer externe Routinen noch "
                    "nicht unterstuetzt; verwende VAR/CONST fuer Records/Arrays."
                ),
            )

        line = position.line
        pairs = list(zip(arguments, routine.parameters))
        for argument, parameter in reversed(pairs):
            if self._external_parameter_by_reference(parameter):
                access = self._resolve_external_reference_argument(
                    routine, argument, parameter
                )
                self._emit_address(access, line)
                self.emitter.emit("    push ecx", line)
            else:
                self._compile_expr(argument)
                self.emitter.emit("    push eax", line)

        self.emitter.emit(f"    call {self._external_symbol(routine)}", line)
        if arguments and str(routine.calling_convention or "").casefold() != "stdcall":
            self.emitter.emit(f"    add esp, {len(arguments) * 4}", line)
        return routine.result_type if routine.result_type is not None else BYTE_TYPE

    def _compile_typecast(
        self,
        target_type: _PascalType,
        argument: Expression,
        position: SourcePosition,
    ) -> _PascalType:
        line = position.line
        source_type = self._compile_expr(argument)
        if target_type.kind == "class":
            if source_type.kind in {"pointer", "class"}:
                return target_type
            # Stage 219: On PE32 a class variable stores a 32-bit object
            # reference.  Win32 APIs such as GetWindowLongA therefore return
            # that reference through a 32-bit integer.  An explicit
            # TForm(LongIntValue) cast is a bit-preserving integer-to-object
            # reference conversion.  Keep this explicit-only; ordinary
            # class := integer assignments remain invalid.
            if source_type.kind in {"scalar", "enum", "subrange"}:
                source_size = self._value_storage_size(source_type)
                target_size = self._value_storage_size(target_type)
                if source_size == target_size == 4:
                    return target_type
            raise self._error(
                f"{source_type.name} kann nicht nach {target_type.name} konvertiert werden.",
                position,
            )
        if target_type.kind == "pointer":
            # Stage 210 Windows strings are already native C-string pointers.
            # An explicit PAnsiChar(String)/Pointer(String) cast therefore only
            # changes the Pascal type view; it does not copy the string.
            if source_type.kind not in {
                "pointer", "class", "scalar", "subrange", "string"
            }:
                raise self._error(
                    f"{source_type.name} kann nicht nach Pointer konvertiert werden.",
                    position,
                )
            return target_type
        # Stage 218: Object-Pascal class values are native references.  On
        # PE32 an explicit LongInt/Int32-style cast is therefore a bit-preserving
        # 32-bit reference-to-integer conversion, e.g. LongInt(AppForm) for
        # SetWindowLongA(..., GWL_USERDATA, ...).  Keep this explicit-only: normal
        # class/integer assignments remain type errors.
        if (
            source_type.kind in {"pointer", "class"}
            and target_type.kind in {"scalar", "enum", "subrange"}
        ):
            source_size = self._value_storage_size(source_type)
            target_size = self._value_storage_size(target_type)
            if source_size > 4 or target_size > 4:
                raise self._error(
                    f"Typkonvertierung {source_type.name} -> {target_type.name} "
                    "passt nicht in einen PE32-Registerwert.",
                    position,
                )
            if target_size == 1:
                self.emitter.emit("    and eax, 255", line)
            elif target_size == 2:
                self.emitter.emit("    and eax, 65535", line)
            return target_type
        if target_type.scalar and source_type.scalar:
            if target_type.size == 1:
                self.emitter.emit("    and eax, 255", line)
            elif target_type.size == 2:
                self.emitter.emit("    and eax, 65535", line)
            return target_type
        raise self._error(
            f"Typkonvertierung {source_type.name} -> {target_type.name} wird nicht unterstützt.",
            position,
        )

    def _compile_assigned_builtin(
        self, expression: CallExpression
    ) -> _PascalType:
        designator = self._as_designator(expression.designator, expression.position)
        self._require_argument_count(
            designator.name, expression.arguments, 1, expression.position
        )
        argument = expression.arguments[0]
        argument_type = self._expression_type(argument)
        if argument_type.kind not in {"pointer", "class"}:
            raise self._error(
                "ASSIGNED erwartet einen Pointer oder eine Klassenreferenz.",
                argument.position,
            )
        self._compile_expr(argument)
        line = expression.position.line
        self.emitter.emit("    test eax, eax", line)
        self.emitter.emit("    setne al", line)
        self.emitter.emit("    movzx eax, al", line)
        return BOOLEAN_TYPE

    def _emit_read_runtime_call(self, symbol: str, line: int) -> None:
        self.emitter.emit(f"    call {symbol}", line)

    def _emit_read_runtime_free(self, line: int) -> None:
        # _jit_read_string allocates through the runtime CRT allocator; free
        # through the same runtime DLL to avoid crossing allocator instances.
        self.emitter.emit("    push eax", line)
        self.emitter.emit("    call _jit_free", line)
        self.emitter.emit("    add esp, 4", line)

    def _emit_readln_discard_line(self, line: int) -> None:
        self._emit_read_runtime_call("_jit_read_string", line)
        self._emit_read_runtime_free(line)

    def _compile_readln_expression(self, expression: CallExpression) -> _PascalType:
        if len(expression.arguments) > 1:
            raise self._error(
                "READLN als Ausdruck erwartet hoechstens einen String-Prompt.",
                expression.position,
            )
        if expression.arguments:
            prompt = expression.arguments[0]
            prompt_type = self._expression_type(prompt)
            if prompt_type.kind != "string":
                raise self._error(
                    "READLN(Prompt) erwartet einen String-Prompt.",
                    prompt.position,
                )
            # Reuse the normal Write path so PE32 and PE64 keep their existing
            # console-output ABI.  No newline is emitted for a prompt.
            self._compile_call_statement(
                CallStatement(
                    expression.position,
                    DesignatorExpression(expression.position, "Write", ()),
                    (prompt,),
                )
            )
        self._emit_read_runtime_call("_jit_read_string", expression.position.line)
        return self.types.get("string", PE32_STRING_TYPE)

    def _compile_readln_statement(self, statement: CallStatement) -> None:
        line = statement.position.line
        if not statement.arguments:
            # Classic Pascal `ReadLn;` / `ReadLn()` pause: consume one complete
            # line and discard the temporary runtime buffer.
            self._emit_readln_discard_line(line)
            return

        consumed_line = False
        for index, argument in enumerate(statement.arguments):
            if not isinstance(argument, (NameExpression, DesignatorExpression)):
                raise self._error(
                    "READLN erwartet beschreibbare Variablen als Argumente.",
                    argument.position,
                )
            designator = self._as_designator(argument, argument.position)
            access = self._resolve_storage(designator)
            type_info = access.type_info
            is_last = index == len(statement.arguments) - 1

            if type_info.kind == "string":
                if not is_last:
                    raise self._error(
                        "Ein String-Argument von READLN muss das letzte Argument sein.",
                        argument.position,
                    )
                self._emit_read_runtime_call("_jit_read_string", line)
                self._emit_store_access(access, line)
                consumed_line = True
                continue

            if type_info == CHAR_TYPE:
                if not is_last:
                    raise self._error(
                        "Ein Char-Argument von READLN muss das letzte Argument sein.",
                        argument.position,
                    )
                self._emit_read_runtime_call("_jit_read_string", line)
                # Preserve the allocated line buffer while the selected Char
                # target computes its address and stores AL.
                self.emitter.emit("    push eax", line)
                self.emitter.emit("    movzx eax, byte ptr [eax]", line)
                self._emit_store_access(access, line)
                self.emitter.emit("    pop eax", line)
                self._emit_read_runtime_free(line)
                consumed_line = True
                continue

            if type_info.kind == "double" or self._value_storage_size(type_info) > 4:
                raise self._error(
                    f"READLN unter PE32 unterstuetzt {type_info.name} noch nicht.",
                    argument.position,
                )
            if type_info.kind not in {"scalar", "enum", "subrange"}:
                raise self._error(
                    f"READLN kann keinen Wert vom Typ {type_info.name} einlesen.",
                    argument.position,
                )

            self._emit_read_runtime_call("jit_read_int", line)
            if type_info == BOOLEAN_TYPE:
                self.emitter.emit("    test eax, eax", line)
                self.emitter.emit("    setne al", line)
                self.emitter.emit("    movzx eax, al", line)
            elif self._value_storage_size(type_info) == 1:
                self.emitter.emit("    and eax, 255", line)
            elif self._value_storage_size(type_info) == 2:
                self.emitter.emit("    and eax, 65535", line)
            self._emit_store_access(access, line)

        # `_jit_read_int` uses formatted extraction and leaves the terminating
        # newline in the stream.  Consume the remainder so READLN really ends
        # at the current line and a following ReadLn does not return instantly.
        if not consumed_line:
            self._emit_readln_discard_line(line)

    def _compile_function(self, expression: CallExpression) -> _PascalType:
        designator = self._as_designator(expression.designator, expression.position)
        constructor = self._resolve_class_constructor_designator(designator)
        if constructor is not None:
            class_type, method = constructor
            return self._compile_class_constructor_call(
                class_type, method, expression.arguments, expression.position
            )
        name = self._key(designator.name) if not designator.selectors else ""
        line = expression.position.line
        if name == "assigned":
            return self._compile_assigned_builtin(expression)
        if name == "readln":
            return self._compile_readln_expression(expression)
        cast_type = self.types.get(name) if name else None
        if cast_type is not None:
            self._require_argument_count(
                designator.name, expression.arguments, 1, expression.position
            )
            return self._compile_typecast(
                cast_type, expression.arguments[0], expression.position
            )
        if name == "peek":
            raise self._error("PEEK ist fuer Windows PE32 nicht verfuegbar.", expression.position)
        if name in {"chr", "ord", "lo", "hi"}:
            self._require_argument_count(designator.name, expression.arguments, 1, expression.position)
            self._compile_expr(expression.arguments[0])
            if name == "hi":
                self.emitter.emit("    shr eax, 8", line)
            elif name in {"chr", "lo"}:
                self.emitter.emit("    and eax, 255", line)
            return CHAR_TYPE if name == "chr" else INTEGER_TYPE
        global_routine = self.global_routines.get(name)
        if global_routine is not None:
            if global_routine.result_type is None:
                raise self._error(
                    f"{global_routine.name} ist keine Funktion.", expression.position
                )
            return self._compile_global_routine_call(
                global_routine, expression.arguments, expression.position
            )
        routine = self.external_routines.get(name)
        if routine is not None:
            if routine.result_type is None:
                raise self._error(f"{routine.name} ist keine Funktion.", expression.position)
            return self._compile_external_call(routine, expression.arguments, expression.position)
        method, receiver = self._resolve_method_call(designator)
        if method.result_type is None:
            raise self._error(f"{method.owner.name}.{method.name} ist keine Funktion.", expression.position)
        return self._compile_method_call(method, receiver, expression.arguments, expression.position)

    def _compile_global_routine_call(
        self,
        routine: _GlobalRoutineInfo,
        arguments: Sequence[Expression],
        position: SourcePosition,
    ) -> _PascalType:
        self._require_argument_count(
            routine.name, arguments, len(routine.parameters), position
        )
        line = position.line

        # A global routine declared CDECL is a real unit ABI entry point. Calls
        # from the defining unit must use the same stack contract as consumers
        # reconstructed from its source-free PUI.
        if routine.calling_convention == "cdecl":
            for argument, parameter in zip(arguments, routine.parameters):
                argument_type = self._expression_type(argument)
                if not self._value_is_scalar(argument_type) or not self._value_is_scalar(parameter.type_info):
                    raise self._error(
                        "Aggregatparameter werden noch nicht unterstützt.",
                        argument.position,
                    )
                if not self._types_compatible(parameter.type_info, argument_type):
                    raise self._error(
                        f"Argumenttyp {argument_type.name} passt nicht zu "
                        f"{parameter.type_info.name}.",
                        argument.position,
                    )
            for argument in reversed(arguments):
                self._compile_expr(argument)
                self.emitter.emit("    push eax", line)
            self.emitter.emit(f"    call {routine.label}", line)
            if arguments:
                self.emitter.emit(f"    add esp, {len(arguments) * 4}", line)
            return routine.result_type if routine.result_type is not None else BYTE_TYPE

        for argument, parameter, variable in zip(
            arguments, routine.parameters, routine.parameter_variables
        ):
            argument_type = self._compile_expr(argument)
            if not self._value_is_scalar(argument_type) or not self._value_is_scalar(parameter.type_info):
                raise self._error(
                    "Aggregatparameter werden noch nicht unterstützt.",
                    argument.position,
                )
            if not self._types_compatible(parameter.type_info, argument_type):
                raise self._error(
                    f"Argumenttyp {argument_type.name} passt nicht zu "
                    f"{parameter.type_info.name}.",
                    argument.position,
                )
            self._store_variable(variable, line)
        self.emitter.emit(f"    call {routine.label}", line)
        return routine.result_type if routine.result_type is not None else BYTE_TYPE

    def _emit_set_self_address(self, receiver: _StorageAccess, line: int) -> None:
        if (
            receiver.use_self
            and receiver.base_label is None
            and receiver.constant_offset == 0
            and receiver.dynamic is None
            and not receiver.dereference_offsets
        ):
            return
        self._emit_load_access(receiver, line)
        self.emitter.emit("    mov esi, eax", line)

    def _compile_method_call(self, method, receiver, arguments, position):
        self._require_argument_count(method.name, arguments, len(method.parameters), position)
        line = position.line
        for argument, parameter, variable in zip(arguments, method.parameters, method.parameter_variables):
            argument_type = self._compile_expr(argument)
            if not self._value_is_scalar(argument_type) or not self._value_is_scalar(parameter.type_info):
                raise self._error("Aggregatparameter werden noch nicht unterstuetzt.", argument.position)
            if not self._types_compatible(parameter.type_info, argument_type):
                raise self._error(f"Argumenttyp {argument_type.name} passt nicht zu {parameter.type_info.name}.", argument.position)
            self._store_variable(variable, line)
        restore_self = self.current_method is not None
        if restore_self:
            self.emitter.emit("    push esi", line)
        self._emit_set_self_address(receiver, line)
        self.emitter.emit(f"    call {method.label}", line)
        if restore_self:
            self.emitter.emit("    pop esi", line)
        return method.result_type if method.result_type is not None else BYTE_TYPE

    def _class_allocator_symbol(self) -> str:
        return "_calloc"

    def _compile_class_constructor_call(
        self,
        class_type: _PascalType,
        method: _MethodInfo,
        arguments: Sequence[Expression],
        position: SourcePosition,
    ) -> _PascalType:
        self._require_argument_count(
            f"{class_type.name}.{method.name}",
            arguments,
            len(method.parameters),
            position,
        )
        if method.is_external and method.parameters:
            raise self._error(
                "PE32: Konstruktoren importierter Klassen mit Parametern "
                "benötigen noch eine Unit-Methoden-ABI; parameterlose "
                "Konstruktoren sind bereits unterstützt.",
                position,
            )
        line = position.line
        temp = self._allocate_variable(
            f"$ctor_{class_type.name}_{self.label_counter}_{len(self.variable_order)}",
            class_type,
            position,
            internal=True,
            label_prefix="ctor_result",
        )
        # calloc(count=1, size=instance_size), cdecl/right-to-left.
        self.emitter.emit(f"    push {max(1, int(class_type.size))}", line)
        self.emitter.emit("    push 1", line)
        self.emitter.emit(f"    call {self._class_allocator_symbol()}", line)
        self.emitter.emit("    add esp, 8", line)
        self._store_variable(temp, line)
        receiver = _StorageAccess(
            class_type, position, temp.label, False
        )
        self._compile_method_call(method, receiver, arguments, position)
        # Constructors are procedures in the source ABI; the expression value
        # is the allocated object reference, not EAX left by the method body.
        self._emit_load_access(receiver, line)
        return class_type

    def _compile_condition_jump_false(self, expression: Expression, target: str) -> None:
        result_type = self._compile_expr(expression)
        if result_type.kind == "string":
            raise self._error("String kann nicht als Bedingung verwendet werden.", expression.position)
        self.emitter.emit("    test eax, eax", expression.position.line)
        self.emitter.emit(f"    jz {target}", expression.position.line)

    def _compile_for(self, statement: ForStatement) -> None:
        variable = self._lookup_variable(statement.name)
        if variable is None or variable.internal:
            raise self._error(f"FOR-Variable nicht gefunden: {statement.name}.", statement.position)
        if variable.type_info not in {INTEGER_TYPE, BYTE_TYPE, CHAR_TYPE}:
            raise self._error("FOR erwartet Integer, Byte oder Char.", statement.position)
        line = statement.position.line
        self._compile_expr(statement.initial)
        self._store_variable(variable, line)
        hidden_name = f"$for_limit_{self.label_counter}_{len(self.variable_order)}"
        limit = self._declare_variable(hidden_name, variable.type_info, statement.position, internal=True)
        self._compile_expr(statement.final)
        self._store_variable(limit, line)
        condition_label = self._new_label("for_condition")
        increment_label = self._new_label("for_step")
        end_label = self._new_label("for_end")
        self.emitter.emit(f"{condition_label}:", line)
        comparison = BinaryExpression(statement.position, DesignatorExpression(statement.position, statement.name), "<=" if statement.direction == "to" else ">=", DesignatorExpression(statement.position, hidden_name))
        self._compile_condition_jump_false(comparison, end_label)
        self.break_targets.append(end_label); self.continue_targets.append(increment_label)
        try:
            self._compile_statement(statement.body)
        finally:
            self.continue_targets.pop(); self.break_targets.pop()
        self.emitter.emit(f"{increment_label}:", line)
        self._emit_load_access(_StorageAccess(variable.type_info, variable.position, variable.label, False), line)
        self.emitter.emit("    add eax, 1" if statement.direction == "to" else "    sub eax, 1", line)
        self._store_variable(variable, line)
        self.emitter.emit(f"    jmp {condition_label}", line)
        self.emitter.emit(f"{end_label}:", line)

    def _compile_call_statement(self, statement: CallStatement) -> None:
        designator = self._as_designator(statement.designator, statement.position)
        name = self._key(designator.name) if not designator.selectors else ""
        line = statement.position.line
        if name in {"write", "writeln"}:
            for argument in statement.arguments:
                type_info = self._compile_expr(argument)
                if type_info.kind == "string":
                    self.runtime.add("print_string")
                    self.emitter.emit(f"    call {self.symbol_prefix}_print_string", line)
                elif type_info == CHAR_TYPE:
                    self.runtime.add("print_char")
                    self.emitter.emit(f"    call {self.symbol_prefix}_print_char", line)
                else:
                    self.runtime.add("print_int")
                    self.emitter.emit(f"    call {self.symbol_prefix}_print_int", line)
            if name == "writeln":
                self.runtime.add("print_newline")
                self.emitter.emit(f"    call {self.symbol_prefix}_print_newline", line)
            return
        if name == "readln":
            self._compile_readln_statement(statement)
            return
        if name == "clrscr":
            self._require_argument_count(designator.name, statement.arguments, 0, statement.position)
            self.runtime.add("clear_screen")
            self.emitter.emit(f"    call {self.symbol_prefix}_clear_screen", line)
            return
        global_routine = self.global_routines.get(name)
        if global_routine is not None:
            # A function result may intentionally be discarded in statement
            # context; _compile_global_routine_call still performs the normal
            # argument/ABI checks and leaves the unused value in EAX/RAX.
            self._compile_global_routine_call(
                global_routine, statement.arguments, statement.position
            )
            return
        routine = self.external_routines.get(name)
        if routine is not None:
            # Function calls are valid statements in Object Pascal; discard
            # the return value after the normal external call.
            self._compile_external_call(routine, statement.arguments, statement.position)
            return
        if name == "poke":
            raise self._error("POKE ist fuer Windows PE32 nicht verfuegbar.", statement.position)
        if name in {"inc", "dec"}:
            self._require_argument_count(designator.name, statement.arguments, 1, statement.position)
            argument = statement.arguments[0]
            if not isinstance(argument, (NameExpression, DesignatorExpression)):
                raise self._error(f"{designator.name} erwartet eine Variable.", statement.position)
            target = self._as_designator(argument)
            self._compile_assignment(AssignmentStatement(statement.position, target, BinaryExpression(statement.position, argument, "+" if name == "inc" else "-", LiteralExpression(statement.position, 1))))
            return
        if name == "halt":
            self._require_argument_count(designator.name, statement.arguments, 0, statement.position)
            self.emitter.emit("    push 0", line)
            self.emitter.emit("    call ExitProcess", line)
            return
        method, receiver = self._resolve_method_call(designator)
        self._compile_method_call(method, receiver, statement.arguments, statement.position)

    def _emit_global_routines(self) -> None:
        for routine in self.global_routines.values():
            implementation = routine.implementation
            self.emitter.emit()
            self.emitter.emit(
                f"; {routine.kind} {routine.name}", implementation.position.line
            )
            if self.unit_name:
                self.emitter.emit(
                    f"global {routine.label}", implementation.position.line
                )
            self.emitter.emit(f"{routine.label}:", implementation.position.line)
            previous_method = self.current_method
            previous_global = self.current_global_routine
            previous_scope = self.scope_variables
            self.current_method = None
            self.current_global_routine = routine
            self.scope_variables = {
                self._key(parameter.name): variable
                for parameter, variable in zip(
                    routine.parameters, routine.parameter_variables
                )
            }
            self.scope_variables.update(routine.local_variables)
            if routine.result_variable is not None:
                self.scope_variables["result"] = routine.result_variable
                self.scope_variables[self._key(routine.name)] = routine.result_variable
            try:
                self.emitter.emit("    push ebp", implementation.position.line)
                self.emitter.emit("    mov ebp, esp", implementation.position.line)

                # IA-32 CDECL and STDCALL both receive arguments on the stack.
                # STDCALL differs only in who removes them afterwards.  Materialize
                # both conventions so callbacks such as GlobalWindowProc can use
                # HWND/UINT/WPARAM/LPARAM through the normal variable resolver.
                convention = str(routine.calling_convention or "cdecl").casefold()
                if convention in {"cdecl", "stdcall"}:
                    stack_offset = 8
                    for parameter, variable in zip(
                        routine.parameters, routine.parameter_variables
                    ):
                        if self._external_parameter_by_reference(parameter):
                            slot_size = 4
                        else:
                            size = self._value_storage_size(parameter.type_info)
                            slot_size = max(4, (size + 3) & ~3)
                        self.emitter.emit(
                            f"    mov eax, dword ptr [ebp+{stack_offset}]",
                            implementation.position.line,
                        )
                        self._store_variable(variable, implementation.position.line)
                        stack_offset += slot_size

                for variable in routine.local_variables.values():
                    self._zero_variable(variable, implementation.position.line)
                if routine.result_variable is not None:
                    self.emitter.emit("    xor eax, eax", implementation.position.line)
                    self._store_variable(routine.result_variable, implementation.position.line)
                for variable, initializer in routine.local_initializers:
                    result_type = self._compile_expr(initializer)
                    if not self._types_compatible(variable.type_info, result_type):
                        raise self._error(
                            f"Initialisierung von {variable.name} besitzt den falschen Typ.",
                            initializer.position,
                        )
                    self._store_variable(variable, initializer.position.line)
                self._compile_statement(implementation.body)
                if routine.result_variable is not None:
                    self._emit_load_access(
                        _StorageAccess(
                            routine.result_variable.type_info,
                            implementation.position,
                            routine.result_variable.label,
                            False,
                        ),
                        implementation.position.line,
                    )
                self.emitter.emit("    mov esp, ebp", implementation.position.line)
                self.emitter.emit("    pop ebp", implementation.position.line)
                convention = str(routine.calling_convention or "cdecl").casefold()
                if convention == "stdcall":
                    cleanup = self._pe32_parameter_stack_bytes(routine.parameters)
                    self.emitter.emit(
                        f"    ret {cleanup}" if cleanup else "    ret",
                        implementation.position.line,
                    )
                else:
                    self.emitter.emit("    ret", implementation.position.line)
            finally:
                self.scope_variables = previous_scope
                self.current_global_routine = previous_global
                self.current_method = previous_method

    def _emit_methods(self) -> None:
        for method in self.methods:
            implementation = method.implementation
            if implementation is None:
                continue
            self.emitter.emit()
            self.emitter.emit(f"; {method.kind} {method.owner.name}.{method.name}", implementation.position.line)
            if self.unit_name:
                self.emitter.emit(f"global {method.label}", implementation.position.line)
            self.emitter.emit(f"{method.label}:", implementation.position.line)
            previous_method = self.current_method; previous_scope = self.scope_variables
            self.current_method = method
            self.scope_variables = {self._key(parameter.name): variable for parameter, variable in zip(method.parameters, method.parameter_variables)}
            self.scope_variables.update(method.local_variables)
            if method.result_variable is not None:
                self.scope_variables["result"] = method.result_variable
                self.scope_variables[self._key(method.name)] = method.result_variable
            try:
                self.emitter.emit("    push ebp", implementation.position.line)
                self.emitter.emit("    mov ebp, esp", implementation.position.line)
                for variable in method.local_variables.values():
                    self._zero_variable(variable, implementation.position.line)
                if method.result_variable is not None:
                    self.emitter.emit("    xor eax, eax", implementation.position.line)
                    self._store_variable(method.result_variable, implementation.position.line)
                for variable, initializer in method.local_initializers:
                    result_type = self._compile_expr(initializer)
                    if not self._types_compatible(variable.type_info, result_type):
                        raise self._error(f"Initialisierung von {variable.name} besitzt den falschen Typ.", initializer.position)
                    self._store_variable(variable, initializer.position.line)
                self._compile_statement(implementation.body)
                if method.result_variable is not None:
                    self._emit_load_access(_StorageAccess(method.result_variable.type_info, implementation.position, method.result_variable.label, False), implementation.position.line)
                self.emitter.emit("    mov esp, ebp", implementation.position.line)
                self.emitter.emit("    pop ebp", implementation.position.line)
                self.emitter.emit("    ret", implementation.position.line)
            finally:
                self.scope_variables = previous_scope; self.current_method = previous_method

    def _library_export_method(self, internal_name: str):
        matches = [
            method for method in self.methods
            if method.owner.name == "__D64LibraryExports"
            and method.name.casefold() == str(internal_name).casefold()
            and method.implementation is not None
        ]
        if len(matches) != 1:
            raise self._error(
                f"DLL-Export-Routine nicht eindeutig gefunden: {internal_name}.",
                SourcePosition(1, 1),
            )
        return matches[0]

    def _emit_library_exports(self) -> None:
        if not self.library_exports:
            return
        for public_name, internal_name in self.library_exports.items():
            method = self._library_export_method(internal_name)
            wrapper = "__d64_export_" + self._safe_name(public_name)
            self.emitter.emit()
            self.emitter.emit(f"global {wrapper}")
            self.emitter.emit(f'export "{public_name}", {wrapper}')
            self.emitter.emit(f"{wrapper}:")
            self.emitter.emit("    push ebp")
            self.emitter.emit("    mov ebp, esp")
            for index, variable in enumerate(method.parameter_variables):
                stack_offset = 8 + index * 4
                self.emitter.emit(f"    mov eax, dword ptr [ebp+{stack_offset}]")
                if variable.type_info.size == 1:
                    self.emitter.emit(f"    mov byte ptr [{variable.label}], al")
                elif variable.type_info.size == 2:
                    self.emitter.emit(f"    mov word ptr [{variable.label}], ax")
                elif variable.type_info.size == 4:
                    self.emitter.emit(f"    mov dword ptr [{variable.label}], eax")
                else:
                    raise self._error(
                        f"DLL-Export {public_name}: Parameter {variable.name} "
                        "ist größer als 32 Bit und wird noch nicht unterstützt.",
                        variable.position,
                    )
            self.emitter.emit("    xor esi, esi")
            self.emitter.emit(f"    call {method.label}")
            self.emitter.emit("    mov esp, ebp")
            self.emitter.emit("    pop ebp")
            # Exportierte Routinen verwenden cdecl; der Aufrufer räumt auf.
            self.emitter.emit("    ret")

    def _emit_runtime(self) -> None:
        if self.console_mode:
            self.emitter.emit()
            self.emitter.emit(f"{self.symbol_prefix}_console_init:")
            self.emitter.emit("    call AllocConsole")
            self.emitter.emit("    push -11")
            self.emitter.emit("    call GetStdHandle")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_stdout_handle], eax")
            self.emitter.emit(f"    push {self.symbol_prefix}_console_info")
            self.emitter.emit("    push eax")
            self.emitter.emit("    call GetConsoleScreenBufferInfo")
            self.emitter.emit(
                f"    mov dword ptr [{self.symbol_prefix}_console_state_valid], eax"
            )
            # Zuerst das sichtbare Fenster verkleinern, danach den Puffer exakt
            # auf 80x25 setzen. Umgekehrt kann SetConsoleScreenBufferSize bei
            # einem noch groesseren Fenster fehlschlagen.
            self.emitter.emit(f"    push {self.symbol_prefix}_console_rect")
            self.emitter.emit("    push 1")
            self.emitter.emit("    push eax")
            self.emitter.emit("    call SetConsoleWindowInfo")
            self.emitter.emit("    push 1638480")  # (25 << 16) | 80
            self.emitter.emit(f"    push dword ptr [{self.symbol_prefix}_stdout_handle]")
            self.emitter.emit("    call SetConsoleScreenBufferSize")
            # ANSI-Sequenzen fuer ClrScr freischalten.
            self.emitter.emit(f"    push {self.symbol_prefix}_console_mode")
            self.emitter.emit(f"    push dword ptr [{self.symbol_prefix}_stdout_handle]")
            self.emitter.emit("    call GetConsoleMode")
            self.emitter.emit(f"    mov eax, dword ptr [{self.symbol_prefix}_console_mode]")
            self.emitter.emit("    or eax, 4")
            self.emitter.emit("    push eax")
            self.emitter.emit(f"    push dword ptr [{self.symbol_prefix}_stdout_handle]")
            self.emitter.emit("    call SetConsoleMode")
            self.emitter.emit("    ret")

            self.emitter.emit()
            self.emitter.emit(f"{self.symbol_prefix}_console_restore:")
            restore_done = f"{self.symbol_prefix}_console_restore_done"
            self.emitter.emit(
                f"    cmp dword ptr [{self.symbol_prefix}_console_state_valid], 0"
            )
            self.emitter.emit(f"    je {restore_done}")
            self.emitter.emit(
                f"    push dword ptr [{self.symbol_prefix}_console_mode]"
            )
            self.emitter.emit(
                f"    push dword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit("    call SetConsoleMode")
            self.emitter.emit(f"    push {self.symbol_prefix}_console_restore_rect")
            self.emitter.emit("    push 1")
            self.emitter.emit(
                f"    push dword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit("    call SetConsoleWindowInfo")
            self.emitter.emit(
                f"    push dword ptr [{self.symbol_prefix}_console_info]"
            )
            self.emitter.emit(
                f"    push dword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit("    call SetConsoleScreenBufferSize")
            self.emitter.emit(f"    mov eax, {self.symbol_prefix}_console_info")
            self.emitter.emit("    add eax, 10")
            self.emitter.emit("    push eax")
            self.emitter.emit("    push 1")
            self.emitter.emit(
                f"    push dword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit("    call SetConsoleWindowInfo")
            self.emitter.emit(
                f"    push dword ptr [{self.symbol_prefix}_console_info+4]"
            )
            self.emitter.emit(
                f"    push dword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit("    call SetConsoleCursorPosition")
            self.emitter.emit(f"{restore_done}:")
            self.emitter.emit("    ret")

        if self.runtime.intersection({"print_string", "print_int", "print_char", "print_newline", "clear_screen", "range_error"}):
            self.emitter.emit(); self.emitter.emit(f"{self.symbol_prefix}_write_cstring:")
            self.emitter.emit("    push eax")
            self.emitter.emit("    push eax")
            self.emitter.emit("    call lstrlenA")
            self.emitter.emit("    mov edx, eax")
            self.emitter.emit("    pop eax")
            self.emitter.emit("    push 0")
            self.emitter.emit(f"    push {self.symbol_prefix}_written")
            self.emitter.emit("    push edx")
            self.emitter.emit("    push eax")
            self.emitter.emit(f"    push dword ptr [{self.symbol_prefix}_stdout_handle]")
            self.emitter.emit("    call WriteFile")
            self.emitter.emit("    ret")

        if "print_string" in self.runtime:
            self.emitter.emit(); self.emitter.emit(f"{self.symbol_prefix}_print_string:")
            self.emitter.emit(f"    call {self.symbol_prefix}_write_cstring"); self.emitter.emit("    ret")
        if "print_int" in self.runtime:
            self.emitter.emit(); self.emitter.emit(f"{self.symbol_prefix}_print_int:")
            self.emitter.emit("    push eax")
            self.emitter.emit(f"    push {self.symbol_prefix}_fmt_d")
            self.emitter.emit(f"    push {self.symbol_prefix}_format_buffer")
            self.emitter.emit("    call wsprintfA")
            self.emitter.emit("    add esp, 12")
            self.emitter.emit(f"    mov eax, {self.symbol_prefix}_format_buffer")
            self.emitter.emit(f"    call {self.symbol_prefix}_write_cstring"); self.emitter.emit("    ret")
        if "print_char" in self.runtime:
            self.emitter.emit(); self.emitter.emit(f"{self.symbol_prefix}_print_char:")
            self.emitter.emit(f"    mov byte ptr [{self.symbol_prefix}_char_buffer], al")
            self.emitter.emit(f"    mov eax, {self.symbol_prefix}_char_buffer")
            self.emitter.emit(f"    call {self.symbol_prefix}_write_cstring"); self.emitter.emit("    ret")
        if "print_newline" in self.runtime:
            self.emitter.emit(); self.emitter.emit(f"{self.symbol_prefix}_print_newline:")
            self.emitter.emit(f"    mov eax, {self.symbol_prefix}_newline")
            self.emitter.emit(f"    call {self.symbol_prefix}_write_cstring"); self.emitter.emit("    ret")
        if "clear_screen" in self.runtime:
            self.emitter.emit(); self.emitter.emit(f"{self.symbol_prefix}_clear_screen:")
            self.emitter.emit(f"    mov eax, {self.symbol_prefix}_clear_sequence")
            self.emitter.emit(f"    call {self.symbol_prefix}_write_cstring"); self.emitter.emit("    ret")
        if "range_error" in self.runtime:
            self.emitter.emit(); self.emitter.emit(f"{self.symbol_prefix}_range_error:")
            self.emitter.emit(f"    mov eax, {self.symbol_prefix}_range_message")
            self.emitter.emit(f"    call {self.symbol_prefix}_write_cstring")
            if self.console_mode:
                self.emitter.emit(f"    call {self.symbol_prefix}_console_restore")
            self.emitter.emit("    push 1"); self.emitter.emit("    call ExitProcess"); self.emitter.emit("    ret")

    def _emit_data(self) -> None:
        self.emitter.emit(); self.emitter.emit("align 4")
        if self.console_mode:
            self.emitter.emit(f"{self.symbol_prefix}_console_rect: dw 0, 0, 79, 24")
        self.emitter.emit(f"{self.symbol_prefix}_fmt_s: db 37, 115, 0")
        self.emitter.emit(f"{self.symbol_prefix}_fmt_d: db 37, 100, 0")
        self.emitter.emit(f"{self.symbol_prefix}_fmt_c: db 37, 99, 0")
        self.emitter.emit(f"{self.symbol_prefix}_newline: db 13, 10, 0")
        self.emitter.emit(f"{self.symbol_prefix}_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0")
        self.emitter.emit(f"{self.symbol_prefix}_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0")
        if self.variable_order:
            self.emitter.emit(); self.emitter.emit(f"; {self.language_name}-Variablen")
            for variable in self.variable_order:
                comment = "intern" if variable.internal else variable.name
                initial_value = getattr(variable, "c_initial_value", None)
                value_size = self._value_storage_size(variable.type_info)
                if value_size == 1:
                    directive = "db"; value = int(initial_value or 0) & 0xFF
                elif value_size == 2:
                    directive = "dw"; value = int(initial_value or 0) & 0xFFFF
                elif value_size == 4:
                    directive = "dd"; value = int(initial_value or 0) & 0xFFFFFFFF
                else:
                    directive = "db"; value = None
                if value is None:
                    values = ", ".join("0" for _ in range(value_size))
                    self.emitter.emit(f"{variable.label}: db {values} ; {comment}: {variable.type_info.name}")
                else:
                    self.emitter.emit(f"{variable.label}: {directive} {value} ; {comment}: {variable.type_info.name}")
        if self.strings:
            self.emitter.emit(); self.emitter.emit("; Nullterminierte Windows-Latin-1-Zeichenketten")
            for data, label in self.strings.items():
                values = ", ".join(str(value) for value in data + b"\x00")
                self.emitter.emit(f"{label}: db {values}")
        if self.console_mode or self.exception_frames:
            self.emitter.emit()
            self.emitter.emit("section .bss")
            self.emitter.emit("align 4")
        if self.console_mode:
            self.emitter.emit(f"{self.symbol_prefix}_stdout_handle: resd 1")
            self.emitter.emit(f"{self.symbol_prefix}_console_restore_rect: resw 4")
            self.emitter.emit(f"{self.symbol_prefix}_console_info: resb 22")
            self.emitter.emit(f"{self.symbol_prefix}_console_state_valid: resd 1")
            self.emitter.emit(f"{self.symbol_prefix}_console_mode: resd 1")
            self.emitter.emit(f"{self.symbol_prefix}_written: resd 1")
            self.emitter.emit(f"{self.symbol_prefix}_format_buffer: resb 32")
            self.emitter.emit(f"{self.symbol_prefix}_char_buffer: resb 2")
        if self.exception_frames:
            self.emitter.emit()
            self.emitter.emit("; Pascal TRY/EXCEPT exception frames (PE32, BSS)")
            for env_label, frame_label in self.exception_frames:
                self.emitter.emit(f"{env_label}: resb 24")
                self.emitter.emit(f"{frame_label}: resb 268")

    def _emit_external_declarations(self) -> None:
        emitted: set[str] = set()
        if self._node_uses_class_constructor(self.program):
            allocator_symbol = self._class_allocator_symbol()
            line = f'import {allocator_symbol}, "msvcrt.dll", "calloc"'
            self.emitter.emit(line)
            emitted.add(line)
        for routine in self.external_routines.values():
            symbol = self._external_symbol(routine)
            member = PASCAL_MINIRUNTIME_IMPORTS.get(routine.name.casefold())
            if routine.library:
                dll = str(routine.library).replace('"', '')
                import_name = str(routine.import_name or routine.name).replace('"', '')
                line = f'import {symbol}, "{dll}", "{import_name}"'
            elif member is not None:
                line = (
                    f'import {symbol}, "{PASCAL_MINIRUNTIME_DLL}", "{member}"'
                )
            else:
                line = f"extern {symbol}"
            if line not in emitted:
                self.emitter.emit(line)
                emitted.add(line)
        for symbol in sorted(self.imported_method_symbols, key=str.casefold):
            line = f"extern {symbol}"
            if line not in emitted:
                self.emitter.emit(line)
                emitted.add(line)
        if self.uses_raise:
            line = f'import _jit_raise, "{PASCAL_MINIRUNTIME_DLL}", "_jit_raise"'
            if line not in emitted:
                self.emitter.emit(line)
                emitted.add(line)
        if self.uses_try:
            for symbol in ("_jit_exception_push", "_jit_exception_pop"):
                line = f'import {symbol}, "{PASCAL_MINIRUNTIME_DLL}", "{symbol}"'
                if line not in emitted:
                    self.emitter.emit(line)
                    emitted.add(line)
        if self.uses_readln:
            for symbol in ("_jit_read_string", "_jit_read_int", "_jit_free"):
                line = f'import {symbol}, "{PASCAL_MINIRUNTIME_DLL}", "{symbol}"'
                if line not in emitted:
                    self.emitter.emit(line)
                    emitted.add(line)

    def generate(self) -> GeneratedAssembly:
        self._prepare_symbols()
        source_line = self.program.body.position.line

        if self.unit_name:
            safe_unit = re.sub(r"[^A-Za-z0-9_]", "_", self.unit_name)
            self.emitter.emit("; Von Pascal erzeugtes Windows-PE32-Unit-Modul")
            self.emitter.emit(f"; Unit: {self.unit_name}")
            self.emitter.emit("bits 32")
            self.emitter.emit(f"global __unit_{safe_unit}")
            self._emit_external_declarations()
            self.emitter.emit(f"__unit_{safe_unit}:")
            self.emitter.emit("    ret")
            self._emit_global_routines()
            self._emit_methods()
            self._emit_runtime()
            self._emit_data()
            assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
            return GeneratedAssembly(
                self.program.name,
                assembly,
                dict(self.emitter.source_map),
                sum(not variable.internal for variable in self.variable_order),
                len(self.strings),
                source_kind="unit",
                unit_name=self.unit_name,
            )

        if self.library_name:
            self.emitter.emit("; Von Pascal erzeugter IA-32-Assembler")
            self.emitter.emit("; Ziel: Windows PE32 DLL / integrierter COFF32-Linker")
            self.emitter.emit(f"; Library: {self.library_name}")
            self.emitter.emit("bits 32")
            self.emitter.emit(f'dllname "{self.library_name}.dll"')
            self.emitter.emit("global __d64_dll_entry")
            self.emitter.emit("entry __d64_dll_entry")
            for symbol in (
                "ExitProcess", "AllocConsole", "GetStdHandle",
                "SetConsoleScreenBufferSize", "SetConsoleWindowInfo",
                "GetConsoleScreenBufferInfo", "SetConsoleCursorPosition",
                "GetConsoleMode", "SetConsoleMode", "WriteFile", "lstrlenA",
                "wsprintfA",
            ):
                self.emitter.emit(f"extern {symbol}")
            self._emit_external_declarations()
            self.emitter.emit("__d64_dll_entry:", source_line)
            self.emitter.emit("    push ebp", source_line)
            self.emitter.emit("    mov ebp, esp", source_line)
            attach_done = self._new_label("dll_attach_done")
            self.emitter.emit("    cmp dword ptr [ebp+12], 1", source_line)
            self.emitter.emit(f"    jne {attach_done}", source_line)
            for variable, initializer in self.initializers:
                result_type = self._compile_expr(initializer)
                if result_type == STRING_TYPE:
                    raise self._error(
                        "String-Variablen werden im PE32-Backend noch nicht unterstützt.",
                        initializer.position,
                    )
                if not self._value_is_scalar(variable.type_info):
                    raise self._error(
                        "Aggregate können nicht direkt initialisiert werden.",
                        initializer.position,
                    )
                if not self._types_compatible(variable.type_info, result_type):
                    raise self._error(
                        f"Initialisierung von {variable.name} besitzt den falschen Typ.",
                        initializer.position,
                    )
                self._store_variable(variable, initializer.position.line)
            self._compile_statement(self.program.body)
            self.emitter.emit(f"{attach_done}:", source_line)
            self.emitter.emit("    mov eax, 1", source_line)
            self.emitter.emit("    mov esp, ebp", source_line)
            self.emitter.emit("    pop ebp", source_line)
            self.emitter.emit("    ret 12", source_line)
            self._emit_global_routines()
            self._emit_methods()
            self._emit_library_exports()
            self._emit_runtime()
            self._emit_data()
            assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
            return GeneratedAssembly(
                self.program.name,
                assembly,
                dict(self.emitter.source_map),
                sum(not variable.internal for variable in self.variable_order),
                len(self.strings),
                source_kind="library",
            )

        self.emitter.emit(f"; Von {self.language_name} erzeugter IA-32-Assembler")
        self.emitter.emit("; Ziel: Windows PE32 / integrierter COFF32-Linker")
        self.emitter.emit(f"; Grafikbackend: {self.graphics_backend}")
        self.emitter.emit(f"; Programm: {self.program.name}")
        self.emitter.emit("bits 32")
        self.emitter.emit("global _start")
        self.emitter.emit("entry _start")
        for symbol in (
            "ExitProcess", "AllocConsole", "GetStdHandle",
            "SetConsoleScreenBufferSize", "SetConsoleWindowInfo",
            "GetConsoleScreenBufferInfo", "SetConsoleCursorPosition",
            "GetConsoleMode", "SetConsoleMode", "WriteFile", "lstrlenA",
            "wsprintfA",
        ):
            self.emitter.emit(f"extern {symbol}")
        self._emit_external_declarations()
        self.emitter.emit("_start:", source_line)
        if self.console_mode:
            self.emitter.emit(f"    call {self.symbol_prefix}_console_init", source_line)
        for variable, initializer in self.initializers:
            result_type = self._compile_expr(initializer)
            if result_type == STRING_TYPE:
                raise self._error("String-Variablen werden im PE32-Backend noch nicht unterstuetzt.", initializer.position)
            if not self._value_is_scalar(variable.type_info):
                raise self._error("Aggregate koennen nicht direkt initialisiert werden.", initializer.position)
            if not self._types_compatible(variable.type_info, result_type):
                raise self._error(f"Initialisierung von {variable.name} besitzt den falschen Typ.", initializer.position)
            self._store_variable(variable, initializer.position.line)
        self._compile_statement(self.program.body)
        if self.console_mode:
            self.emitter.emit(f"    call {self.symbol_prefix}_console_restore", source_line)
        self.emitter.emit("    push 0", source_line)
        self.emitter.emit("    call ExitProcess", source_line)
        self._emit_global_routines(); self._emit_methods(); self._emit_runtime(); self._emit_data()
        assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
        return GeneratedAssembly(
            self.program.name,
            assembly,
            dict(self.emitter.source_map),
            sum(not variable.internal for variable in self.variable_order),
            len(self.strings),
        )


class _PE64CodeGenerator(_PE32CodeGenerator):
    """Native AMD64 assembler for the integrated Windows PE32+/COFF64 path.

    Integer remains 32 bit (Delphi/Win64 compatible), while pointers and
    dynamic-string handles are 64 bit.  Calls crossing module boundaries use
    the Microsoft x64 register convention RCX/RDX/R8/R9 plus the mandatory
    32-byte shadow space.
    """

    WIN64_ARGUMENT_REGISTERS = ("rcx", "rdx", "r8", "r9")

    def __init__(
        self,
        program: PascalProgram,
        *,
        symbol_prefix: str = "__pas",
        language_name: str = "Pascal",
        graphics_backend: str = "Direct2D",
        console_mode: bool = True,
        library_name: Optional[str] = None,
        library_exports: Optional[Dict[str, str]] = None,
        unit_name: Optional[str] = None,
    ) -> None:
        super().__init__(
            program,
            symbol_prefix=symbol_prefix,
            language_name=language_name,
            graphics_backend=graphics_backend,
            console_mode=console_mode,
            library_name=library_name,
            library_exports=library_exports,
            unit_name=unit_name,
        )
        self.types["integer"] = PE64_INTEGER_TYPE
        self.types["pointer"] = PE64_POINTER_TYPE
        self.types["string"] = PE64_STRING_TYPE
        self.call_temporaries: List[str] = []

    @staticmethod
    def _align16(value: int) -> int:
        value = int(value)
        return (value + 15) & ~15

    def _external_symbol(self, routine: _ExternalRoutineInfo) -> str:
        symbol = str(routine.symbol)
        # Windows x64 uses one unified ABI: CDECL/STDCALL decoration disappears.
        # Preserve a Pascal identifier that itself begins with '_' (for example
        # _jit_blake2) by returning the source name, not by stripping characters.
        if str(routine.calling_convention or "").casefold() in {"cdecl", "stdcall", "win64"}:
            return str(routine.name)
        if symbol == "_" + str(routine.name):
            return str(routine.name)
        return symbol

    def _new_call_temp(self) -> str:
        label = f"{self.symbol_prefix}_calltmp_{len(self.call_temporaries)}"
        self.call_temporaries.append(label)
        return label

    def _emit_internal_call(self, symbol: str, line: int) -> None:
        # The generated routines keep RSP 16-byte aligned outside CALLs.
        self.emitter.emit("    sub rsp, 32", line)
        self.emitter.emit(f"    call {symbol}", line)
        self.emitter.emit("    add rsp, 32", line)

    def _emit_read_runtime_call(self, symbol: str, line: int) -> None:
        self._emit_internal_call(symbol, line)

    def _emit_read_runtime_free(self, line: int) -> None:
        self.emitter.emit("    mov rcx, rax", line)
        self._emit_internal_call("_jit_free", line)

    def _emit_win64_call(
        self,
        symbol: str,
        arguments: Sequence[Expression],
        parameters: Sequence[_ParameterInfo],
        position: SourcePosition,
        *,
        receiver: Optional[_StorageAccess] = None,
        external_routine: Optional[_ExternalRoutineInfo] = None,
    ) -> None:
        if len(arguments) != len(parameters):
            self._require_argument_count(symbol, arguments, len(parameters), position)
        line = position.line
        external_abi = external_routine is not None
        temp_labels: List[str] = []

        if receiver is not None:
            if (
                receiver.use_self
                and receiver.base_label is None
                and receiver.constant_offset == 0
                and receiver.dynamic is None
                and not receiver.dereference_offsets
            ):
                self.emitter.emit("    mov rax, rsi", line)
            else:
                self._emit_load_access(receiver, line)
            temp = self._new_call_temp()
            self.emitter.emit(f"    mov qword ptr [{temp}], rax", line)
            temp_labels.append(temp)

        for argument, parameter in zip(arguments, parameters):
            if external_abi and self._external_parameter_by_reference(parameter):
                assert external_routine is not None
                access = self._resolve_external_reference_argument(
                    external_routine, argument, parameter
                )
                self._emit_address(access, line)
                temp = self._new_call_temp()
                self.emitter.emit(f"    mov qword ptr [{temp}], r11", line)
                temp_labels.append(temp)
                continue

            if external_abi:
                self._validate_external_value_argument(
                    parameter,
                    argument,
                    aggregate_message=(
                        "Aggregat-Wertparameter werden für externe Windows PE32+ "
                        "Routinen noch nicht unterstützt; verwende VAR/CONST."
                    ),
                )
            else:
                argument_type = self._expression_type(argument)
                if not self._value_is_scalar(argument_type) or not self._value_is_scalar(parameter.type_info):
                    raise self._error(
                        "Aggregatparameter werden für Windows PE32+ noch nicht unterstützt.",
                        argument.position,
                    )
                if not self._types_compatible(parameter.type_info, argument_type):
                    raise self._error(
                        f"Argumenttyp {argument_type.name} passt nicht zu {parameter.type_info.name}.",
                        argument.position,
                    )
            self._compile_expr(argument)
            temp = self._new_call_temp()
            self.emitter.emit(f"    mov qword ptr [{temp}], rax", line)
            temp_labels.append(temp)

        stack_arguments = max(0, len(temp_labels) - 4)
        frame_size = self._align16(32 + stack_arguments * 8)
        self.emitter.emit(f"    sub rsp, {frame_size}", line)
        for index, label in enumerate(temp_labels):
            if index < 4:
                self.emitter.emit(
                    f"    mov {self.WIN64_ARGUMENT_REGISTERS[index]}, qword ptr [{label}]",
                    line,
                )
            else:
                self.emitter.emit(f"    mov rax, qword ptr [{label}]", line)
                self.emitter.emit(
                    f"    mov qword ptr [rsp+{32 + (index - 4) * 8}], rax",
                    line,
                )
        self.emitter.emit(f"    call {symbol}", line)
        self.emitter.emit(f"    add rsp, {frame_size}", line)

    def _emit_load_literal(self, value: int, source_line: int) -> None:
        number = int(value)
        if not -(1 << 63) <= number <= (1 << 64) - 1:
            raise self._error(
                f"Ganzzahl liegt außerhalb des AMD64-Bereichs: {value}.",
                SourcePosition(source_line, 1),
            )
        if -0x80000000 <= number <= 0xFFFFFFFF:
            self.emitter.emit(f"    mov eax, {number}", source_line)
        else:
            self.emitter.emit(f"    mov rax, {number}", source_line)

    def _emit_address(self, access: _StorageAccess, line: int) -> None:
        dynamic = access.dynamic
        if dynamic is not None:
            self._compile_expr(dynamic.expression)
            if dynamic.lower_bound:
                self.emitter.emit(f"    sub eax, {int(dynamic.lower_bound)}", line)
            range_ok = self._new_label("index_range_ok")
            self.emitter.emit(f"    cmp eax, {int(dynamic.element_count)}", line)
            self.emitter.emit(f"    jb {range_ok}", line)
            self.runtime.add("range_error")
            self.emitter.emit(f"    jmp {self.symbol_prefix}_range_error", line)
            self.emitter.emit(f"{range_ok}:", line)
            if dynamic.stride != 1:
                self.emitter.emit(f"    mov r10d, {int(dynamic.stride)}", line)
                self.emitter.emit("    imul eax, r10d", line)
            self.emitter.emit("    mov r10d, eax", line)

        if access.use_self:
            self.emitter.emit("    mov r11, rsi", line)
        else:
            assert access.base_label is not None
            self.emitter.emit(f"    mov r11, {access.base_label}", line)

        for deref_offset in access.dereference_offsets:
            if deref_offset:
                self.emitter.emit(f"    add r11, {int(deref_offset)}", line)
            self.emitter.emit("    mov r11, qword ptr [r11]", line)

        if dynamic is not None:
            self.emitter.emit("    add r11, r10", line)
        if access.constant_offset:
            self.emitter.emit(f"    add r11, {int(access.constant_offset)}", line)

    def _emit_load_access(self, access: _StorageAccess, line: int) -> None:
        value_size = self._value_storage_size(access.type_info)
        if value_size not in {1, 2, 4, 8}:
            raise self._error(
                "Das PE64-Backend kann derzeit skalare 8-, 16-, 32- und 64-Bit-Werte laden.",
                access.position,
            )
        self._emit_address(access, line)
        if value_size == 1:
            self.emitter.emit("    movzx eax, byte ptr [r11]", line)
        elif value_size == 2:
            instruction = "movsx" if access.type_info.signed else "movzx"
            self.emitter.emit(f"    {instruction} eax, word ptr [r11]", line)
        elif value_size == 4:
            self.emitter.emit("    mov eax, dword ptr [r11]", line)
        else:
            self.emitter.emit("    mov rax, qword ptr [r11]", line)

    def _emit_store_access(self, access: _StorageAccess, line: int) -> None:
        value_size = self._value_storage_size(access.type_info)
        if value_size not in {1, 2, 4, 8}:
            raise self._error(
                "Das PE64-Backend kann derzeit skalare 8-, 16-, 32- und 64-Bit-Werte speichern.",
                access.position,
            )
        self.emitter.emit("    push rax", line)
        self._emit_address(access, line)
        self.emitter.emit("    pop rax", line)
        if value_size == 1:
            self.emitter.emit("    mov byte ptr [r11], al", line)
        elif value_size == 2:
            self.emitter.emit("    mov word ptr [r11], ax", line)
        elif value_size == 4:
            self.emitter.emit("    mov dword ptr [r11], eax", line)
        else:
            self.emitter.emit("    mov qword ptr [r11], rax", line)

    def _store_variable(self, variable: _Variable, line: int) -> None:
        self._emit_store_access(
            _StorageAccess(variable.type_info, variable.position, variable.label, False),
            line,
        )

    def _zero_variable(self, variable: _Variable, line: int) -> None:
        """Zero-initialize one PE64 local, including full aggregates."""
        value_size = self._value_storage_size(variable.type_info)
        if self._value_is_scalar(variable.type_info) and value_size in {1, 2, 4, 8}:
            self.emitter.emit("    xor rax, rax", line)
            self._store_variable(variable, line)
            return

        if variable.type_info.kind not in {"record", "array"}:
            raise self._error(
                f"Lokale Variable {variable.name} vom Typ {variable.type_info.name} "
                f"({value_size} Byte) kann im PE64-Backend nicht nullinitialisiert werden.",
                variable.position,
            )

        access = _StorageAccess(
            variable.type_info, variable.position, variable.label, False
        )
        self._emit_address(access, line)
        offset = 0
        while value_size - offset >= 8:
            operand = "[r11]" if offset == 0 else f"[r11+{offset}]"
            self.emitter.emit(f"    mov qword ptr {operand}, 0", line)
            offset += 8
        if value_size - offset >= 4:
            operand = "[r11]" if offset == 0 else f"[r11+{offset}]"
            self.emitter.emit(f"    mov dword ptr {operand}, 0", line)
            offset += 4
        if value_size - offset >= 2:
            operand = "[r11]" if offset == 0 else f"[r11+{offset}]"
            self.emitter.emit(f"    mov word ptr {operand}, 0", line)
            offset += 2
        if value_size - offset:
            operand = "[r11]" if offset == 0 else f"[r11+{offset}]"
            self.emitter.emit(f"    mov byte ptr {operand}, 0", line)

    def _emit_comparison(
        self, operator: str, signed: bool, line: int, *, width64: bool = False
    ) -> None:
        if signed:
            instruction = {
                "=": "sete", "<>": "setne", "<": "setl", "<=": "setle",
                ">": "setg", ">=": "setge",
            }[operator]
        else:
            instruction = {
                "=": "sete", "<>": "setne", "<": "setb", "<=": "setbe",
                ">": "seta", ">=": "setae",
            }[operator]
        self.emitter.emit("    cmp rax, rdx" if width64 else "    cmp eax, edx", line)
        self.emitter.emit(f"    {instruction} al", line)
        self.emitter.emit("    movzx eax, al", line)

    def _compile_expr(self, expression: Expression) -> _PascalType:
        line = expression.position.line
        if isinstance(expression, AddressOfExpression):
            label = self._routine_address_label(expression)
            self.emitter.emit(f"    mov rax, {label}", line)
            return self.types.get("pointer", PE64_POINTER_TYPE)

        if isinstance(expression, LiteralExpression):
            if isinstance(expression.value, str):
                label = self._string_label(expression.value, expression.position)
                self.emitter.emit(f"    mov rax, {label}", line)
                return self.types.get("string", PE64_STRING_TYPE)
            self._emit_load_literal(int(expression.value), line)
            return self._constant_type(expression.value)

        if isinstance(expression, (NameExpression, DesignatorExpression)):
            key = self._key(expression.name)
            has_selectors = isinstance(expression, DesignatorExpression) and bool(expression.selectors)
            if key == "nil" and not has_selectors:
                self.emitter.emit("    xor rax, rax", line)
                return self.types.get("pointer", PE64_POINTER_TYPE)
            if key in self.constants and not has_selectors:
                value = self.constants[key]
                if isinstance(value, str):
                    label = self._string_label(value, expression.position)
                    self.emitter.emit(f"    mov rax, {label}", line)
                    return self.types.get("string", PE64_STRING_TYPE)
                self._emit_load_literal(int(value), line)
                return self.constant_types.get(key, self._constant_type(value))
            if isinstance(expression, DesignatorExpression):
                constructor = self._resolve_class_constructor_designator(expression)
                if constructor is not None:
                    class_type, method = constructor
                    return self._compile_class_constructor_call(
                        class_type, method, (), expression.position
                    )
            try:
                access = self._resolve_storage(expression)
            except C64PascalError:
                if isinstance(expression, DesignatorExpression):
                    resolved = self._resolve_parameterless_function(expression)
                    if resolved is not None:
                        method, receiver = resolved
                        return self._compile_method_call(
                            method, receiver, (), expression.position
                        )
                raise
            if access.type_info.kind == "class":
                if key == "self" and not has_selectors:
                    self.emitter.emit("    mov rax, rsi", line)
                else:
                    self._emit_load_access(access, line)
                return access.type_info
            if not access.type_info.scalar:
                raise self._error(
                    f"{access.type_info.name} kann nicht als skalarer Ausdruck geladen werden.",
                    expression.position,
                )
            self._emit_load_access(access, line)
            return access.type_info

        if isinstance(expression, InheritedCallExpression):
            return self._compile_inherited_expression(expression)

        if isinstance(expression, CallExpression):
            return self._compile_function(expression)

        if isinstance(expression, UnaryExpression):
            operand_type = self._compile_expr(expression.operand)
            if operand_type.kind == "string":
                raise self._error("Ungültiger Operator für String.", expression.position)
            if expression.operator == "+":
                return operand_type
            if expression.operator == "-":
                self.emitter.emit("    neg eax", line)
                return self.types.get("integer", PE64_INTEGER_TYPE)
            if expression.operator == "not":
                self.emitter.emit("    cmp eax, 0", line)
                self.emitter.emit("    sete al", line)
                self.emitter.emit("    movzx eax, al", line)
                return BOOLEAN_TYPE
            raise self._error(
                f"Unbekannter unärer Operator: {expression.operator}.",
                expression.position,
            )

        if isinstance(expression, BinaryExpression):
            left_type = self._expression_type(expression.left)
            right_type = self._expression_type(expression.right)
            if left_type.kind == "string" or right_type.kind == "string":
                raise self._error(
                    "String-Vergleiche und String-Arithmetik werden noch nicht unterstützt.",
                    expression.position,
                )
            self._compile_expr(expression.left)
            self.emitter.emit("    push rax", line)
            self._compile_expr(expression.right)
            self.emitter.emit("    mov rdx, rax", line)
            self.emitter.emit("    pop rax", line)
            operator = expression.operator
            if operator in {"+", "-", "and", "or", "xor"}:
                instruction = {
                    "+": "add", "-": "sub", "and": "and", "or": "or", "xor": "xor"
                }[operator]
                self.emitter.emit(f"    {instruction} eax, edx", line)
                if operator in {"and", "or", "xor"} and left_type == BOOLEAN_TYPE and right_type == BOOLEAN_TYPE:
                    return BOOLEAN_TYPE
                return self.types.get("integer", PE64_INTEGER_TYPE)
            if operator == "*":
                self.emitter.emit("    imul eax, edx", line)
                return self.types.get("integer", PE64_INTEGER_TYPE)
            if operator in {"div", "mod"}:
                self.emitter.emit("    mov r10d, edx", line)
                self.emitter.emit("    cdq", line)
                self.emitter.emit("    idiv r10d", line)
                if operator == "mod":
                    self.emitter.emit("    mov eax, edx", line)
                return self.types.get("integer", PE64_INTEGER_TYPE)
            if operator == "/":
                raise self._error(
                    "Der Real-Operator '/' wird nicht unterstützt; verwende DIV.",
                    expression.position,
                )
            if operator in {"=", "<>", "<", "<=", ">", ">="}:
                width64 = (
                    left_type.kind in {"pointer", "class"}
                    or right_type.kind in {"pointer", "class"}
                    or left_type.size == 8
                    or right_type.size == 8
                )
                self._emit_comparison(
                    operator,
                    left_type.signed or right_type.signed,
                    line,
                    width64=width64,
                )
                return BOOLEAN_TYPE
            raise self._error(f"Unbekannter Operator: {operator}.", expression.position)

        raise self._error("Ausdruck kann nicht übersetzt werden.", expression.position)

    def _compile_assigned_builtin(
        self, expression: CallExpression
    ) -> _PascalType:
        designator = self._as_designator(expression.designator, expression.position)
        self._require_argument_count(
            designator.name, expression.arguments, 1, expression.position
        )
        argument = expression.arguments[0]
        argument_type = self._expression_type(argument)
        if argument_type.kind not in {"pointer", "class"}:
            raise self._error(
                "ASSIGNED erwartet einen Pointer oder eine Klassenreferenz.",
                argument.position,
            )
        self._compile_expr(argument)
        line = expression.position.line
        self.emitter.emit("    test rax, rax", line)
        self.emitter.emit("    setne al", line)
        self.emitter.emit("    movzx eax, al", line)
        return BOOLEAN_TYPE

    def _compile_typecast(
        self,
        target_type: _PascalType,
        argument: Expression,
        position: SourcePosition,
    ) -> _PascalType:
        line = position.line
        source_type = self._compile_expr(argument)
        if target_type.kind == "class":
            if source_type.kind in {"pointer", "class"}:
                return target_type
            if source_type.kind in {"scalar", "enum", "subrange"}:
                source_size = self._value_storage_size(source_type)
                target_size = self._value_storage_size(target_type)
                if source_size < target_size:
                    raise self._error(
                        f"PE64: Typkonvertierung {source_type.name} -> {target_type.name} "
                        "würde aus einem 32-Bit-Wert eine 64-Bit-Objektreferenz "
                        "rekonstruieren; verwende GetWindowLongPtrA und einen "
                        "pointer-großen Integer-Typ (NativeInt/LONG_PTR).",
                        position,
                    )
                if source_size == target_size:
                    return target_type
            raise self._error(
                f"{source_type.name} kann nicht nach {target_type.name} konvertiert werden.",
                position,
            )
        if target_type.kind == "pointer":
            # Native Windows String values are pointer-sized C-string handles.
            if source_type.kind not in {
                "pointer", "class", "scalar", "subrange", "string"
            }:
                raise self._error(
                    f"{source_type.name} kann nicht nach Pointer konvertiert werden.",
                    position,
                )
            if source_type.size <= 4:
                self.emitter.emit("    mov eax, eax", line)
            return target_type
        # Stage 218: A Win64 class/pointer value is eight bytes.  Do not
        # silently truncate it through LongInt/Int32.  Code storing an object
        # reference in window userdata must use SetWindowLongPtrA together with
        # a pointer-sized integer type (NativeInt/LONG_PTR).
        if (
            source_type.kind in {"pointer", "class"}
            and target_type.kind in {"scalar", "enum", "subrange"}
        ):
            source_size = self._value_storage_size(source_type)
            target_size = self._value_storage_size(target_type)
            if target_size < source_size:
                raise self._error(
                    f"PE64: Typkonvertierung {source_type.name} -> {target_type.name} "
                    "würde eine 64-Bit-Referenz abschneiden; verwende einen "
                    "pointer-großen Integer-Typ und SetWindowLongPtrA.",
                    position,
                )
            return target_type
        if target_type.scalar and source_type.scalar:
            if target_type.size == 1:
                self.emitter.emit("    and eax, 255", line)
            elif target_type.size == 2:
                self.emitter.emit("    and eax, 65535", line)
            return target_type
        raise self._error(
            f"Typkonvertierung {source_type.name} -> {target_type.name} wird nicht unterstützt.",
            position,
        )

    def _compile_exit_statement(self, statement: ExitStatement) -> None:
        if self.current_method is None and self.current_global_routine is None:
            raise self._error(
                "EXIT ist derzeit nur innerhalb einer Routine/Methode erlaubt.",
                statement.position,
            )
        line = statement.position.line
        result_variable = self._active_result_variable()
        if result_variable is not None:
            self._emit_load_access(
                _StorageAccess(
                    result_variable.type_info,
                    statement.position,
                    result_variable.label,
                    False,
                ),
                line,
            )
        if self.current_method is not None:
            # Matches _PE64CodeGenerator._emit_methods prologue:
            # push rbp / mov rbp,rsp / push rsi / sub rsp,8.
            self.emitter.emit("    add rsp, 8", line)
            self.emitter.emit("    pop rsi", line)
            self.emitter.emit("    pop rbp", line)
            self.emitter.emit("    ret", line)
            return
        # Global PE64 routines only establish an RBP frame.
        self.emitter.emit("    mov rsp, rbp", line)
        self.emitter.emit("    pop rbp", line)
        self.emitter.emit("    ret", line)

    def _compile_try_statement(self, statement: TryStatement) -> None:
        raise self._error(
            "TRY/EXCEPT/FINALLY benötigt unter PE64 noch einen nativen 64-Bit-setjmp/longjmp-Runtimepfad; PE32 ist implementiert.",
            statement.position,
        )

    def _compile_raise_statement(self, statement: RaiseStatement) -> None:
        message = self._raise_exception_create_message(statement)
        message_type = self._compile_expr(message)
        if message_type.kind != "string":
            raise self._error(
                "Exception.Create in RAISE erwartet einen String als Nachricht.",
                message.position,
            )
        line = statement.position.line
        # Microsoft x64 ABI: RCX=code, RDX=message, 32 bytes shadow space.
        self.emitter.emit("    mov rdx, rax", line)
        self.emitter.emit("    mov ecx, 7", line)
        self.emitter.emit("    sub rsp, 32", line)
        self.emitter.emit("    call _jit_raise", line)
        self.emitter.emit("    add rsp, 32", line)

    def _compile_external_call(self, routine, arguments, position):
        self._require_argument_count(
            routine.name, arguments, len(routine.parameters), position
        )
        self._emit_win64_call(
            self._external_symbol(routine),
            arguments,
            routine.parameters,
            position,
            external_routine=routine,
        )
        return routine.result_type if routine.result_type is not None else BYTE_TYPE

    def _compile_global_routine_call(
        self,
        routine: _GlobalRoutineInfo,
        arguments: Sequence[Expression],
        position: SourcePosition,
    ) -> _PascalType:
        self._require_argument_count(
            routine.name, arguments, len(routine.parameters), position
        )
        self._emit_win64_call(
            routine.label, arguments, routine.parameters, position
        )
        return routine.result_type if routine.result_type is not None else BYTE_TYPE

    def _emit_set_self_address(self, receiver: _StorageAccess, line: int) -> None:
        if (
            receiver.use_self
            and receiver.base_label is None
            and receiver.constant_offset == 0
            and receiver.dynamic is None
            and not receiver.dereference_offsets
        ):
            return
        self._emit_load_access(receiver, line)
        self.emitter.emit("    mov rsi, rax", line)

    def _compile_method_call(self, method, receiver, arguments, position):
        self._require_argument_count(
            method.name, arguments, len(method.parameters), position
        )
        self._emit_win64_call(
            method.label,
            arguments,
            method.parameters,
            position,
            receiver=receiver,
        )
        return method.result_type if method.result_type is not None else BYTE_TYPE

    def _class_allocator_symbol(self) -> str:
        return "calloc"

    def _compile_class_constructor_call(
        self,
        class_type: _PascalType,
        method: _MethodInfo,
        arguments: Sequence[Expression],
        position: SourcePosition,
    ) -> _PascalType:
        self._require_argument_count(
            f"{class_type.name}.{method.name}",
            arguments,
            len(method.parameters),
            position,
        )
        line = position.line
        temp = self._allocate_variable(
            f"$ctor_{class_type.name}_{self.label_counter}_{len(self.variable_order)}",
            class_type,
            position,
            internal=True,
            label_prefix="ctor_result",
        )
        self.emitter.emit("    mov ecx, 1", line)
        self.emitter.emit(f"    mov edx, {max(1, int(class_type.size))}", line)
        self.emitter.emit("    sub rsp, 32", line)
        self.emitter.emit(f"    call {self._class_allocator_symbol()}", line)
        self.emitter.emit("    add rsp, 32", line)
        self._store_variable(temp, line)
        receiver = _StorageAccess(
            class_type, position, temp.label, False
        )
        self._compile_method_call(method, receiver, arguments, position)
        self._emit_load_access(receiver, line)
        return class_type

    def _compile_condition_jump_false(self, expression: Expression, target: str) -> None:
        result_type = self._compile_expr(expression)
        if result_type.kind == "string":
            raise self._error(
                "String kann nicht als Bedingung verwendet werden.", expression.position
            )
        instruction = (
            "test rax, rax"
            if self._value_storage_size(result_type) == 8
            else "test eax, eax"
        )
        self.emitter.emit(f"    {instruction}", expression.position.line)
        self.emitter.emit(f"    jz {target}", expression.position.line)

    def _compile_call_statement(self, statement: CallStatement) -> None:
        designator = self._as_designator(statement.designator, statement.position)
        name = self._key(designator.name) if not designator.selectors else ""
        line = statement.position.line
        if name in {"write", "writeln"}:
            for argument in statement.arguments:
                type_info = self._compile_expr(argument)
                if type_info.kind == "string":
                    self.runtime.add("print_string")
                    self._emit_internal_call(f"{self.symbol_prefix}_print_string", line)
                elif type_info == CHAR_TYPE:
                    self.runtime.add("print_char")
                    self._emit_internal_call(f"{self.symbol_prefix}_print_char", line)
                else:
                    self.runtime.add("print_int")
                    self._emit_internal_call(f"{self.symbol_prefix}_print_int", line)
            if name == "writeln":
                self.runtime.add("print_newline")
                self._emit_internal_call(f"{self.symbol_prefix}_print_newline", line)
            return
        if name == "readln":
            self._compile_readln_statement(statement)
            return
        if name == "clrscr":
            self._require_argument_count(
                designator.name, statement.arguments, 0, statement.position
            )
            self.runtime.add("clear_screen")
            self._emit_internal_call(f"{self.symbol_prefix}_clear_screen", line)
            return
        global_routine = self.global_routines.get(name)
        if global_routine is not None:
            # Function calls are valid statements in Object Pascal; discard
            # the return value after the normal call.
            self._compile_global_routine_call(
                global_routine, statement.arguments, statement.position
            )
            return
        routine = self.external_routines.get(name)
        if routine is not None:
            # Function calls are valid statements in Object Pascal; discard
            # the return value after the normal external call.
            self._compile_external_call(routine, statement.arguments, statement.position)
            return
        if name == "poke":
            raise self._error("POKE ist für Windows PE32+ nicht verfügbar.", statement.position)
        if name in {"inc", "dec"}:
            self._require_argument_count(
                designator.name, statement.arguments, 1, statement.position
            )
            argument = statement.arguments[0]
            if not isinstance(argument, (NameExpression, DesignatorExpression)):
                raise self._error(
                    f"{designator.name} erwartet eine Variable.", statement.position
                )
            target = self._as_designator(argument)
            self._compile_assignment(
                AssignmentStatement(
                    statement.position,
                    target,
                    BinaryExpression(
                        statement.position,
                        argument,
                        "+" if name == "inc" else "-",
                        LiteralExpression(statement.position, 1),
                    ),
                )
            )
            return
        if name == "halt":
            self._require_argument_count(
                designator.name, statement.arguments, 0, statement.position
            )
            self.emitter.emit("    xor ecx, ecx", line)
            self.emitter.emit("    sub rsp, 32", line)
            self.emitter.emit("    call ExitProcess", line)
            self.emitter.emit("    add rsp, 32", line)
            return
        method, receiver = self._resolve_method_call(designator)
        self._compile_method_call(
            method, receiver, statement.arguments, statement.position
        )

    def _materialize_win64_parameter(
        self,
        variable: _Variable,
        overall_index: int,
        line: int,
    ) -> None:
        if overall_index < 4:
            reg = self.WIN64_ARGUMENT_REGISTERS[overall_index]
            self.emitter.emit(f"    mov rax, {reg}", line)
        else:
            # RBP points 8 bytes below the entry RSP after PUSH RBP.
            stack_offset = 48 + (overall_index - 4) * 8
            self.emitter.emit(
                f"    mov rax, qword ptr [rbp+{stack_offset}]", line
            )
        self._store_variable(variable, line)

    def _emit_global_routines(self) -> None:
        for routine in self.global_routines.values():
            implementation = routine.implementation
            line = implementation.position.line
            self.emitter.emit()
            self.emitter.emit(f"; {routine.kind} {routine.name}", line)
            if self.unit_name:
                self.emitter.emit(f"global {routine.label}", line)
            self.emitter.emit(f"{routine.label}:", line)
            previous_method = self.current_method
            previous_global = self.current_global_routine
            previous_scope = self.scope_variables
            self.current_method = None
            self.current_global_routine = routine
            self.scope_variables = {
                self._key(parameter.name): variable
                for parameter, variable in zip(
                    routine.parameters, routine.parameter_variables
                )
            }
            self.scope_variables.update(routine.local_variables)
            if routine.result_variable is not None:
                self.scope_variables["result"] = routine.result_variable
                self.scope_variables[self._key(routine.name)] = routine.result_variable
            try:
                self.emitter.emit("    push rbp", line)
                self.emitter.emit("    mov rbp, rsp", line)
                for index, variable in enumerate(routine.parameter_variables):
                    self._materialize_win64_parameter(variable, index, line)
                for variable in routine.local_variables.values():
                    self._zero_variable(variable, line)
                if routine.result_variable is not None:
                    self.emitter.emit("    xor rax, rax", line)
                    self._store_variable(routine.result_variable, line)
                for variable, initializer in routine.local_initializers:
                    result_type = self._compile_expr(initializer)
                    if not self._types_compatible(variable.type_info, result_type):
                        raise self._error(
                            f"Initialisierung von {variable.name} besitzt den falschen Typ.",
                            initializer.position,
                        )
                    self._store_variable(variable, initializer.position.line)
                self._compile_statement(implementation.body)
                if routine.result_variable is not None:
                    self._emit_load_access(
                        _StorageAccess(
                            routine.result_variable.type_info,
                            implementation.position,
                            routine.result_variable.label,
                            False,
                        ),
                        line,
                    )
                self.emitter.emit("    mov rsp, rbp", line)
                self.emitter.emit("    pop rbp", line)
                self.emitter.emit("    ret", line)
            finally:
                self.scope_variables = previous_scope
                self.current_global_routine = previous_global
                self.current_method = previous_method

    def _emit_methods(self) -> None:
        for method in self.methods:
            implementation = method.implementation
            if implementation is None:
                continue
            line = implementation.position.line
            self.emitter.emit()
            self.emitter.emit(
                f"; {method.kind} {method.owner.name}.{method.name}", line
            )
            if self.unit_name:
                self.emitter.emit(f"global {method.label}", line)
            self.emitter.emit(f"{method.label}:", line)
            previous_method = self.current_method
            previous_scope = self.scope_variables
            self.current_method = method
            self.scope_variables = {
                self._key(parameter.name): variable
                for parameter, variable in zip(
                    method.parameters, method.parameter_variables
                )
            }
            self.scope_variables.update(method.local_variables)
            if method.result_variable is not None:
                self.scope_variables["result"] = method.result_variable
                self.scope_variables[self._key(method.name)] = method.result_variable
            try:
                self.emitter.emit("    push rbp", line)
                self.emitter.emit("    mov rbp, rsp", line)
                self.emitter.emit("    push rsi", line)
                self.emitter.emit("    sub rsp, 8", line)
                self.emitter.emit("    mov rsi, rcx", line)
                for index, variable in enumerate(method.parameter_variables):
                    self._materialize_win64_parameter(variable, index + 1, line)
                for variable in method.local_variables.values():
                    self._zero_variable(variable, line)
                if method.result_variable is not None:
                    self.emitter.emit("    xor rax, rax", line)
                    self._store_variable(method.result_variable, line)
                for variable, initializer in method.local_initializers:
                    result_type = self._compile_expr(initializer)
                    if not self._types_compatible(variable.type_info, result_type):
                        raise self._error(
                            f"Initialisierung von {variable.name} besitzt den falschen Typ.",
                            initializer.position,
                        )
                    self._store_variable(variable, initializer.position.line)
                self._compile_statement(implementation.body)
                if method.result_variable is not None:
                    self._emit_load_access(
                        _StorageAccess(
                            method.result_variable.type_info,
                            implementation.position,
                            method.result_variable.label,
                            False,
                        ),
                        line,
                    )
                self.emitter.emit("    add rsp, 8", line)
                self.emitter.emit("    pop rsi", line)
                self.emitter.emit("    pop rbp", line)
                self.emitter.emit("    ret", line)
            finally:
                self.scope_variables = previous_scope
                self.current_method = previous_method

    def _emit_library_exports(self) -> None:
        if not self.library_exports:
            return
        for public_name, internal_name in self.library_exports.items():
            method = self._library_export_method(internal_name)
            if len(method.parameters) > 3:
                raise self._error(
                    f"PE64-DLL-Export {public_name}: derzeit höchstens 3 explizite Parameter.",
                    method.position,
                )
            wrapper = "__d64_export_" + self._safe_name(public_name)
            self.emitter.emit()
            self.emitter.emit(f"global {wrapper}")
            self.emitter.emit(f'export "{public_name}", {wrapper}')
            self.emitter.emit(f"{wrapper}:")
            if len(method.parameters) >= 3:
                self.emitter.emit("    mov r9, r8")
            if len(method.parameters) >= 2:
                self.emitter.emit("    mov r8, rdx")
            if len(method.parameters) >= 1:
                self.emitter.emit("    mov rdx, rcx")
            self.emitter.emit("    xor rcx, rcx")
            self.emitter.emit("    sub rsp, 40")
            self.emitter.emit(f"    call {method.label}")
            self.emitter.emit("    add rsp, 40")
            self.emitter.emit("    ret")

    def _emit_runtime_prologue(self, label: str) -> None:
        self.emitter.emit()
        self.emitter.emit(f"{label}:")
        self.emitter.emit("    push rbp")
        self.emitter.emit("    mov rbp, rsp")

    def _emit_runtime_epilogue(self) -> None:
        self.emitter.emit("    pop rbp")
        self.emitter.emit("    ret")

    def _emit_runtime(self) -> None:
        if self.console_mode:
            self._emit_runtime_prologue(f"{self.symbol_prefix}_console_init")
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call AllocConsole")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit("    mov rcx, -11")
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call GetStdHandle")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit(
                f"    mov qword ptr [{self.symbol_prefix}_stdout_handle], rax"
            )
            self.emitter.emit("    mov rcx, rax")
            self.emitter.emit(f"    mov rdx, {self.symbol_prefix}_console_info")
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call GetConsoleScreenBufferInfo")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit(
                f"    mov dword ptr [{self.symbol_prefix}_console_state_valid], eax"
            )
            self.emitter.emit(
                f"    mov rcx, qword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit("    mov edx, 1")
            self.emitter.emit(f"    mov r8, {self.symbol_prefix}_console_rect")
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call SetConsoleWindowInfo")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit(
                f"    mov rcx, qword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit("    mov edx, 1638480")
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call SetConsoleScreenBufferSize")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit(
                f"    mov rcx, qword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit(f"    mov rdx, {self.symbol_prefix}_console_mode")
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call GetConsoleMode")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit(
                f"    mov eax, dword ptr [{self.symbol_prefix}_console_mode]"
            )
            self.emitter.emit("    or eax, 4")
            self.emitter.emit("    mov edx, eax")
            self.emitter.emit(
                f"    mov rcx, qword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call SetConsoleMode")
            self.emitter.emit("    add rsp, 32")
            self._emit_runtime_epilogue()

            self._emit_runtime_prologue(
                f"{self.symbol_prefix}_console_restore"
            )
            restore_done = f"{self.symbol_prefix}_console_restore_done"
            self.emitter.emit(
                f"    cmp dword ptr [{self.symbol_prefix}_console_state_valid], 0"
            )
            self.emitter.emit(f"    je {restore_done}")
            self.emitter.emit(
                f"    mov rcx, qword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit(
                f"    mov edx, dword ptr [{self.symbol_prefix}_console_mode]"
            )
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call SetConsoleMode")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit(
                f"    mov rcx, qword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit("    mov edx, 1")
            self.emitter.emit(f"    mov r8, {self.symbol_prefix}_console_restore_rect")
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call SetConsoleWindowInfo")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit(
                f"    mov rcx, qword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit(
                f"    mov edx, dword ptr [{self.symbol_prefix}_console_info]"
            )
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call SetConsoleScreenBufferSize")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit(
                f"    mov rcx, qword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit("    mov edx, 1")
            self.emitter.emit(f"    mov r8, {self.symbol_prefix}_console_info")
            self.emitter.emit("    add r8, 10")
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call SetConsoleWindowInfo")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit(
                f"    mov rcx, qword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit(
                f"    mov edx, dword ptr [{self.symbol_prefix}_console_info+4]"
            )
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call SetConsoleCursorPosition")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit(f"{restore_done}:")
            self._emit_runtime_epilogue()

        if self.runtime.intersection(
            {"print_string", "print_int", "print_char", "print_newline", "clear_screen", "range_error"}
        ):
            self._emit_runtime_prologue(f"{self.symbol_prefix}_write_cstring")
            self.emitter.emit(
                f"    mov qword ptr [{self.symbol_prefix}_write_ptr], rax"
            )
            self.emitter.emit("    mov rcx, rax")
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call lstrlenA")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit("    mov r8d, eax")
            self.emitter.emit(
                f"    mov rdx, qword ptr [{self.symbol_prefix}_write_ptr]"
            )
            self.emitter.emit(
                f"    mov rcx, qword ptr [{self.symbol_prefix}_stdout_handle]"
            )
            self.emitter.emit(f"    mov r9, {self.symbol_prefix}_written")
            self.emitter.emit("    sub rsp, 48")
            self.emitter.emit("    mov qword ptr [rsp+32], 0")
            self.emitter.emit("    call WriteFile")
            self.emitter.emit("    add rsp, 48")
            self._emit_runtime_epilogue()

        if "print_string" in self.runtime:
            self._emit_runtime_prologue(f"{self.symbol_prefix}_print_string")
            self._emit_internal_call(f"{self.symbol_prefix}_write_cstring", 0)
            self._emit_runtime_epilogue()
        if "print_int" in self.runtime:
            self._emit_runtime_prologue(f"{self.symbol_prefix}_print_int")
            self.emitter.emit("    mov r8d, eax")
            self.emitter.emit(f"    mov rcx, {self.symbol_prefix}_format_buffer")
            self.emitter.emit(f"    mov rdx, {self.symbol_prefix}_fmt_d")
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call wsprintfA")
            self.emitter.emit("    add rsp, 32")
            self.emitter.emit(f"    mov rax, {self.symbol_prefix}_format_buffer")
            self._emit_internal_call(f"{self.symbol_prefix}_write_cstring", 0)
            self._emit_runtime_epilogue()
        if "print_char" in self.runtime:
            self._emit_runtime_prologue(f"{self.symbol_prefix}_print_char")
            self.emitter.emit(
                f"    mov byte ptr [{self.symbol_prefix}_char_buffer], al"
            )
            self.emitter.emit(f"    mov rax, {self.symbol_prefix}_char_buffer")
            self._emit_internal_call(f"{self.symbol_prefix}_write_cstring", 0)
            self._emit_runtime_epilogue()
        if "print_newline" in self.runtime:
            self._emit_runtime_prologue(f"{self.symbol_prefix}_print_newline")
            self.emitter.emit(f"    mov rax, {self.symbol_prefix}_newline")
            self._emit_internal_call(f"{self.symbol_prefix}_write_cstring", 0)
            self._emit_runtime_epilogue()
        if "clear_screen" in self.runtime:
            self._emit_runtime_prologue(f"{self.symbol_prefix}_clear_screen")
            self.emitter.emit(f"    mov rax, {self.symbol_prefix}_clear_sequence")
            self._emit_internal_call(f"{self.symbol_prefix}_write_cstring", 0)
            self._emit_runtime_epilogue()
        if "range_error" in self.runtime:
            self._emit_runtime_prologue(f"{self.symbol_prefix}_range_error")
            self.emitter.emit(f"    mov rax, {self.symbol_prefix}_range_message")
            self._emit_internal_call(f"{self.symbol_prefix}_write_cstring", 0)
            if self.console_mode:
                self._emit_internal_call(
                    f"{self.symbol_prefix}_console_restore", 0
                )
            self.emitter.emit("    mov ecx, 1")
            self.emitter.emit("    sub rsp, 32")
            self.emitter.emit("    call ExitProcess")
            self.emitter.emit("    add rsp, 32")
            self._emit_runtime_epilogue()

    def _emit_data(self) -> None:
        self.emitter.emit()
        self.emitter.emit("align 8")
        if self.console_mode:
            self.emitter.emit(f"{self.symbol_prefix}_console_rect: dw 0, 0, 79, 24")
        self.emitter.emit(f"{self.symbol_prefix}_fmt_s: db 37, 115, 0")
        self.emitter.emit(f"{self.symbol_prefix}_fmt_d: db 37, 100, 0")
        self.emitter.emit(f"{self.symbol_prefix}_fmt_c: db 37, 99, 0")
        self.emitter.emit(f"{self.symbol_prefix}_newline: db 13, 10, 0")
        self.emitter.emit(
            f"{self.symbol_prefix}_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0"
        )
        self.emitter.emit(
            f"{self.symbol_prefix}_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0"
        )
        if self.variable_order:
            self.emitter.emit()
            self.emitter.emit(f"; {self.language_name}-Variablen")
            for variable in self.variable_order:
                comment = "intern" if variable.internal else variable.name
                initial_value = getattr(variable, "c_initial_value", None)
                value_size = self._value_storage_size(variable.type_info)
                if value_size == 1:
                    directive = "db"; value = int(initial_value or 0) & 0xFF
                elif value_size == 2:
                    directive = "dw"; value = int(initial_value or 0) & 0xFFFF
                elif value_size == 4:
                    directive = "dd"; value = int(initial_value or 0) & 0xFFFFFFFF
                elif value_size == 8:
                    directive = "dq"; value = int(initial_value or 0) & 0xFFFFFFFFFFFFFFFF
                else:
                    directive = "db"; value = None
                if value is None:
                    values = ", ".join("0" for _ in range(value_size))
                    self.emitter.emit(
                        f"{variable.label}: db {values} ; {comment}: {variable.type_info.name}"
                    )
                else:
                    self.emitter.emit(
                        f"{variable.label}: {directive} {value} ; {comment}: {variable.type_info.name}"
                    )
        if self.strings:
            self.emitter.emit()
            self.emitter.emit("; Nullterminierte Windows-Latin-1-Zeichenketten")
            for data, label in self.strings.items():
                values = ", ".join(str(value) for value in data + b"\x00")
                self.emitter.emit(f"{label}: db {values}")
        if self.console_mode or self.call_temporaries:
            self.emitter.emit()
            self.emitter.emit("section .bss")
            self.emitter.emit("align 8")
        if self.console_mode:
            self.emitter.emit(f"{self.symbol_prefix}_stdout_handle: resq 1")
            self.emitter.emit(f"{self.symbol_prefix}_console_restore_rect: resw 4")
            self.emitter.emit(f"{self.symbol_prefix}_console_info: resb 22")
            self.emitter.emit(f"{self.symbol_prefix}_console_state_valid: resd 1")
            self.emitter.emit(f"{self.symbol_prefix}_console_mode: resd 1")
            self.emitter.emit(f"{self.symbol_prefix}_written: resd 1")
            self.emitter.emit(f"{self.symbol_prefix}_write_ptr: resq 1")
            self.emitter.emit(f"{self.symbol_prefix}_format_buffer: resb 32")
            self.emitter.emit(f"{self.symbol_prefix}_char_buffer: resb 2")
        if self.call_temporaries:
            self.emitter.emit()
            self.emitter.emit("; PE64 Win64-call temporaries (BSS)")
            for label in self.call_temporaries:
                self.emitter.emit(f"{label}: resq 1")

    def _emit_external_declarations(self) -> None:
        emitted: set[str] = set()
        if self._node_uses_class_constructor(self.program):
            allocator_symbol = self._class_allocator_symbol()
            line = f'import {allocator_symbol}, "msvcrt.dll", "calloc"'
            self.emitter.emit(line)
            emitted.add(line)
        for routine in self.external_routines.values():
            symbol = self._external_symbol(routine)
            member = PASCAL_MINIRUNTIME_IMPORTS.get(routine.name.casefold())
            if routine.library:
                dll = str(routine.library).replace('"', '')
                import_name = str(routine.import_name or routine.name).replace('"', '')
                line = f'import {symbol}, "{dll}", "{import_name}"'
            elif member is not None:
                line = f'import {symbol}, "{PASCAL_MINIRUNTIME_DLL}", "{member}"'
            else:
                line = f"extern {symbol}"
            if line not in emitted:
                self.emitter.emit(line)
                emitted.add(line)
        for symbol in sorted(self.imported_method_symbols, key=str.casefold):
            line = f"extern {symbol}"
            if line not in emitted:
                self.emitter.emit(line)
                emitted.add(line)
        if self.uses_raise:
            line = f'import _jit_raise, "{PASCAL_MINIRUNTIME_DLL}", "_jit_raise"'
            if line not in emitted:
                self.emitter.emit(line)
                emitted.add(line)
        if self.uses_readln:
            for symbol in ("_jit_read_string", "_jit_read_int", "_jit_free"):
                line = f'import {symbol}, "{PASCAL_MINIRUNTIME_DLL}", "{symbol}"'
                if line not in emitted:
                    self.emitter.emit(line)
                    emitted.add(line)

    def generate(self) -> GeneratedAssembly:
        self._prepare_symbols()
        source_line = self.program.body.position.line

        if self.unit_name:
            safe_unit = re.sub(r"[^A-Za-z0-9_]", "_", self.unit_name)
            self.emitter.emit("; Von Pascal erzeugtes Windows-PE32+-AMD64-Unit-Modul")
            self.emitter.emit(f"; Unit: {self.unit_name}")
            self.emitter.emit("; Architektur: AMD64 / x86-64 / COFF64")
            self.emitter.emit("bits 64")
            self.emitter.emit(f"global __unit_{safe_unit}")
            self._emit_external_declarations()
            self.emitter.emit(f"__unit_{safe_unit}:")
            self.emitter.emit("    ret")
            self._emit_global_routines()
            self._emit_methods()
            self._emit_runtime()
            self._emit_data()
            assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
            return GeneratedAssembly(
                self.program.name,
                assembly,
                dict(self.emitter.source_map),
                sum(not variable.internal for variable in self.variable_order),
                len(self.strings),
                source_kind="unit",
                unit_name=self.unit_name,
            )

        if self.library_name:
            self.emitter.emit("; Von Pascal erzeugter AMD64-Assembler")
            self.emitter.emit("; Ziel: Windows PE32+ DLL / integrierter COFF64-Linker")
            self.emitter.emit(f"; Library: {self.library_name}")
            self.emitter.emit("bits 64")
            self.emitter.emit(f'dllname "{self.library_name}.dll"')
            self.emitter.emit("global __d64_dll_entry")
            self.emitter.emit("entry __d64_dll_entry")
            self._emit_external_declarations()
            self.emitter.emit("__d64_dll_entry:", source_line)
            self.emitter.emit("    push rbp", source_line)
            self.emitter.emit("    mov rbp, rsp", source_line)
            attach_done = self._new_label("dll_attach_done")
            self.emitter.emit("    cmp edx, 1", source_line)
            self.emitter.emit(f"    jne {attach_done}", source_line)
            for variable, initializer in self.initializers:
                result_type = self._compile_expr(initializer)
                if not variable.type_info.scalar:
                    raise self._error(
                        "Aggregate können nicht direkt initialisiert werden.",
                        initializer.position,
                    )
                if not self._types_compatible(variable.type_info, result_type):
                    raise self._error(
                        f"Initialisierung von {variable.name} besitzt den falschen Typ.",
                        initializer.position,
                    )
                self._store_variable(variable, initializer.position.line)
            self._compile_statement(self.program.body)
            self.emitter.emit(f"{attach_done}:", source_line)
            self.emitter.emit("    mov eax, 1", source_line)
            self.emitter.emit("    pop rbp", source_line)
            self.emitter.emit("    ret", source_line)
            self._emit_global_routines()
            self._emit_methods()
            self._emit_library_exports()
            self._emit_runtime()
            self._emit_data()
            assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
            return GeneratedAssembly(
                self.program.name,
                assembly,
                dict(self.emitter.source_map),
                sum(not variable.internal for variable in self.variable_order),
                len(self.strings),
                source_kind="library",
            )

        self.emitter.emit(f"; Von {self.language_name} erzeugter AMD64-Assembler")
        self.emitter.emit("; Ziel: Windows PE32+ / integrierter COFF64-Linker")
        self.emitter.emit(f"; Grafikbackend: {self.graphics_backend}")
        self.emitter.emit(f"; Programm: {self.program.name}")
        self.emitter.emit("bits 64")
        self.emitter.emit("global _start")
        self.emitter.emit("entry _start")
        for symbol in (
            "ExitProcess", "AllocConsole", "GetStdHandle",
            "SetConsoleScreenBufferSize", "SetConsoleWindowInfo",
            "GetConsoleScreenBufferInfo", "SetConsoleCursorPosition",
            "GetConsoleMode", "SetConsoleMode", "WriteFile", "lstrlenA",
            "wsprintfA",
        ):
            self.emitter.emit(f"extern {symbol}")
        self._emit_external_declarations()
        self.emitter.emit("_start:", source_line)
        self.emitter.emit("    push rbp", source_line)
        self.emitter.emit("    mov rbp, rsp", source_line)
        if self.console_mode:
            self._emit_internal_call(f"{self.symbol_prefix}_console_init", source_line)
        for variable, initializer in self.initializers:
            result_type = self._compile_expr(initializer)
            if not variable.type_info.scalar:
                raise self._error(
                    "Aggregate können nicht direkt initialisiert werden.", initializer.position
                )
            if not self._types_compatible(variable.type_info, result_type):
                raise self._error(
                    f"Initialisierung von {variable.name} besitzt den falschen Typ.",
                    initializer.position,
                )
            self._store_variable(variable, initializer.position.line)
        self._compile_statement(self.program.body)
        if self.console_mode:
            self._emit_internal_call(
                f"{self.symbol_prefix}_console_restore", source_line
            )
        self.emitter.emit("    xor ecx, ecx", source_line)
        self.emitter.emit("    sub rsp, 32", source_line)
        self.emitter.emit("    call ExitProcess", source_line)
        self.emitter.emit("    add rsp, 32", source_line)
        self._emit_global_routines()
        self._emit_methods()
        self._emit_runtime()
        self._emit_data()
        assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
        return GeneratedAssembly(
            self.program.name,
            assembly,
            dict(self.emitter.source_map),
            sum(not variable.internal for variable in self.variable_order),
            len(self.strings),
        )


class _AmigaCodeGenerator(_CodeGenerator):
    """Erzeugt eigenständigen Motorola-68000-Assembler für den Amiga 500."""

    def __init__(
        self,
        program: PascalProgram,
        *,
        symbol_prefix: str = "__pas",
        language_name: str = "Pascal",
    ) -> None:
        super().__init__(program)
        self.symbol_prefix = symbol_prefix
        self.language_name = language_name

    def _new_label(self, prefix: str) -> str:
        self.label_counter += 1
        return f"{self.symbol_prefix}_{prefix}_{self.label_counter}"

    def _emit_load_literal(self, value: int, source_line: int) -> None:
        if not -32768 <= value <= 65535:
            raise self._error(
                f"Ganzzahl liegt außerhalb -32768..65535: {value}.",
                SourcePosition(source_line, 1),
            )
        self.emitter.emit(f"    move.w #${value & 0xFFFF:04X},d0", source_line)

    @staticmethod
    def _amiga_string_bytes(text: str, position: SourcePosition) -> bytes:
        try:
            return text.replace("\r\n", "\n").replace("\r", "\n").encode(
                "latin-1"
            )
        except UnicodeEncodeError as exc:
            character = text[exc.start]
            raise C64PascalError(
                f"Zeichen U+{ord(character):04X} kann nicht in eine "
                "Amiga-Latin-1-Zeichenkette übernommen werden.",
                position.line,
                position.column - 1,
            ) from exc

    def _string_label(self, text: str, position: SourcePosition) -> str:
        data = self._amiga_string_bytes(text, position)
        label = self.strings.get(data)
        if label is None:
            label = f"{self.symbol_prefix}_string_{len(self.strings)}"
            self.strings[data] = label
        return label

    def _emit_address(self, access: _StorageAccess, line: int) -> None:
        dynamic = access.dynamic
        if dynamic is not None:
            self._compile_expr(dynamic.expression)
            if dynamic.lower_bound:
                self.emitter.emit(
                    f"    subi.w #${dynamic.lower_bound & 0xFFFF:04X},d0",
                    line,
                )
            range_ok = self._new_label("index_range_ok")
            self.emitter.emit(
                f"    cmpi.w #${dynamic.element_count & 0xFFFF:04X},d0",
                line,
            )
            self.emitter.emit(f"    bcs {range_ok}", line)
            self.runtime.add("range_error")
            self.emitter.emit(f"    bra {self.symbol_prefix}_range_error", line)
            self.emitter.emit(f"{range_ok}:", line)
            if dynamic.stride != 1:
                self.emitter.emit(
                    f"    mulu.w #${dynamic.stride & 0xFFFF:04X},d0",
                    line,
                )
            self.emitter.emit("    move.w d0,d2", line)

        if access.use_self:
            self.emitter.emit("    move.l a5,a0", line)
        else:
            assert access.base_label is not None
            self.emitter.emit(f"    lea {access.base_label}(pc),a0", line)

        for deref_offset in access.dereference_offsets:
            if deref_offset:
                self.emitter.emit(
                    f"    adda.w #${deref_offset & 0xFFFF:04X},a0", line
                )
            self.emitter.emit("    move.l (a0),a0", line)

        if dynamic is not None:
            self.emitter.emit("    adda.w d2,a0", line)
        if access.constant_offset:
            self.emitter.emit(
                f"    adda.w #${access.constant_offset & 0xFFFF:04X},a0",
                line,
            )

    def _emit_load_access(self, access: _StorageAccess, line: int) -> None:
        if access.type_info.size not in {1, 2}:
            raise self._error(
                "Nur skalare 8- und 16-Bit-Werte können geladen werden.",
                access.position,
            )
        self._emit_address(access, line)
        self.emitter.emit("    moveq #0,d0", line)
        if access.type_info.size == 1:
            self.emitter.emit("    move.b (a0),d0", line)
        else:
            # Byteweises Laden verhindert Adressfehler bei gepackten Records.
            self.emitter.emit("    move.b (a0)+,d0", line)
            self.emitter.emit("    lsl.w #8,d0", line)
            self.emitter.emit("    move.b (a0),d0", line)

    def _emit_store_access(self, access: _StorageAccess, line: int) -> None:
        if access.type_info.size not in {1, 2}:
            raise self._error(
                "Nur skalare 8- und 16-Bit-Werte können gespeichert werden.",
                access.position,
            )
        self.emitter.emit("    move.w d0,-(sp)", line)
        self._emit_address(access, line)
        self.emitter.emit("    move.w (sp)+,d0", line)
        if access.type_info.size == 1:
            self.emitter.emit("    move.b d0,(a0)", line)
        else:
            # Gepackte Aggregate dürfen auch an ungeraden Adressen liegen.
            self.emitter.emit("    move.w d0,d1", line)
            self.emitter.emit("    lsr.w #8,d1", line)
            self.emitter.emit("    move.b d1,(a0)+", line)
            self.emitter.emit("    move.b d0,(a0)", line)

    def _store_variable(self, variable: _Variable, line: int) -> None:
        self._emit_store_access(
            _StorageAccess(
                variable.type_info,
                variable.position,
                variable.label,
                False,
            ),
            line,
        )

    def _emit_comparison(self, operator: str, signed: bool, line: int) -> None:
        del signed
        true_label = self._new_label("cmp_true")
        end_label = self._new_label("cmp_end")
        branch = {
            "=": "beq",
            "<>": "bne",
            "<": "blt",
            "<=": "ble",
            ">": "bgt",
            ">=": "bge",
        }[operator]
        self.emitter.emit("    cmp.w d1,d0", line)
        self.emitter.emit(f"    {branch} {true_label}", line)
        self.emitter.emit("    moveq #0,d0", line)
        self.emitter.emit(f"    bra {end_label}", line)
        self.emitter.emit(f"{true_label}:", line)
        self.emitter.emit("    moveq #1,d0", line)
        self.emitter.emit(f"{end_label}:", line)

    def _compile_expr(self, expression: Expression) -> _PascalType:
        line = expression.position.line
        if isinstance(expression, AddressOfExpression):
            self._routine_address_label(expression)
            raise self._error(
                "Adressoperator @ ist für das Amiga-Backend noch nicht aktiviert.",
                expression.position,
            )

        if isinstance(expression, LiteralExpression):
            if isinstance(expression.value, str):
                label = self._string_label(expression.value, expression.position)
                self.emitter.emit(f"    lea {label}(pc),a0", line)
                return STRING_TYPE
            self._emit_load_literal(int(expression.value), line)
            return self._constant_type(expression.value)

        if isinstance(expression, (NameExpression, DesignatorExpression)):
            key = self._key(expression.name)
            has_selectors = isinstance(expression, DesignatorExpression) and bool(
                expression.selectors
            )
            if key in self.constants and not has_selectors:
                value = self.constants[key]
                if isinstance(value, str):
                    label = self._string_label(value, expression.position)
                    self.emitter.emit(f"    lea {label}(pc),a0", line)
                    return STRING_TYPE
                self._emit_load_literal(int(value), line)
                return self.constant_types.get(key, self._constant_type(value))
            try:
                access = self._resolve_storage(expression)
            except C64PascalError:
                if isinstance(expression, DesignatorExpression):
                    resolved = self._resolve_parameterless_function(expression)
                    if resolved is not None:
                        method, receiver = resolved
                        return self._compile_method_call(
                            method,
                            receiver,
                            (),
                            expression.position,
                        )
                raise
            if not access.type_info.scalar:
                raise self._error(
                    f"{access.type_info.name} kann nicht als skalarer Ausdruck geladen werden.",
                    expression.position,
                )
            self._emit_load_access(access, line)
            return access.type_info

        if isinstance(expression, InheritedCallExpression):
            return self._compile_inherited_expression(expression)

        if isinstance(expression, CallExpression):
            return self._compile_function(expression)

        if isinstance(expression, UnaryExpression):
            operand_type = self._compile_expr(expression.operand)
            if operand_type == STRING_TYPE:
                raise self._error("Ungültiger Operator für String.", expression.position)
            if expression.operator == "+":
                return operand_type
            if expression.operator == "-":
                self.emitter.emit("    neg.w d0", line)
                return INTEGER_TYPE
            if expression.operator == "not":
                false_label = self._new_label("not_false")
                end_label = self._new_label("not_end")
                self.emitter.emit("    tst.w d0", line)
                self.emitter.emit(f"    bne {false_label}", line)
                self.emitter.emit("    moveq #1,d0", line)
                self.emitter.emit(f"    bra {end_label}", line)
                self.emitter.emit(f"{false_label}:", line)
                self.emitter.emit("    moveq #0,d0", line)
                self.emitter.emit(f"{end_label}:", line)
                return BOOLEAN_TYPE
            raise self._error(
                f"Unbekannter unärer Operator: {expression.operator}.",
                expression.position,
            )

        if isinstance(expression, BinaryExpression):
            left_type = self._expression_type(expression.left)
            right_type = self._expression_type(expression.right)
            if left_type == STRING_TYPE or right_type == STRING_TYPE:
                raise self._error(
                    "String-Vergleiche und String-Arithmetik werden nicht unterstützt.",
                    expression.position,
                )
            self._compile_expr(expression.left)
            self.emitter.emit("    move.w d0,-(sp)", line)
            self._compile_expr(expression.right)
            self.emitter.emit("    move.w d0,d1", line)
            self.emitter.emit("    move.w (sp)+,d0", line)
            operator = expression.operator
            if operator in {"+", "-", "and", "or", "xor"}:
                instruction = {
                    "+": "add.w",
                    "-": "sub.w",
                    "and": "and.w",
                    "or": "or.w",
                    "xor": "eor.w",
                }[operator]
                self.emitter.emit(f"    {instruction} d1,d0", line)
                if (
                    operator in {"and", "or", "xor"}
                    and left_type == BOOLEAN_TYPE
                    and right_type == BOOLEAN_TYPE
                ):
                    return BOOLEAN_TYPE
                return INTEGER_TYPE if INTEGER_TYPE in {left_type, right_type} else BYTE_TYPE
            if operator == "*":
                self.emitter.emit("    muls.w d1,d0", line)
                return INTEGER_TYPE
            if operator in {"div", "mod"}:
                self.emitter.emit("    ext.l d0", line)
                self.emitter.emit("    divs.w d1,d0", line)
                if operator == "mod":
                    self.emitter.emit("    swap d0", line)
                return INTEGER_TYPE
            if operator == "/":
                raise self._error(
                    "Der Real-Operator '/' wird nicht unterstützt; verwende DIV.",
                    expression.position,
                )
            if operator in {"=", "<>", "<", "<=", ">", ">="}:
                self._emit_comparison(
                    operator,
                    left_type.signed or right_type.signed,
                    line,
                )
                return BOOLEAN_TYPE
            raise self._error(f"Unbekannter Operator: {operator}.", expression.position)

        raise self._error("Ausdruck kann nicht übersetzt werden.", expression.position)

    def _compile_external_call(
        self,
        routine: _ExternalRoutineInfo,
        arguments: Sequence[Expression],
        position: SourcePosition,
    ) -> _PascalType:
        self._require_argument_count(
            routine.name, arguments, len(routine.parameters), position
        )
        line = position.line
        for argument, parameter in zip(arguments, routine.parameters):
            argument_type = self._compile_expr(argument)
            if not argument_type.scalar or not parameter.type_info.scalar:
                raise self._error(
                    "Aggregatparameter werden für externe Routinen noch nicht unterstützt.",
                    argument.position,
                )
            if not self._types_compatible(parameter.type_info, argument_type):
                raise self._error(
                    f"Argumenttyp {argument_type.name} passt nicht zu "
                    f"{parameter.type_info.name}.",
                    argument.position,
                )
            self.emitter.emit("    move.w d0,-(sp)", line)
        self.emitter.emit(f"    bsr {routine.symbol}", line)
        stack_bytes = len(arguments) * 2
        if stack_bytes:
            self.emitter.emit(f"    adda.w #${stack_bytes:04X},sp", line)
        return routine.result_type if routine.result_type is not None else BYTE_TYPE

    def _compile_function(self, expression: CallExpression) -> _PascalType:
        designator = self._as_designator(expression.designator, expression.position)
        name = self._key(designator.name) if not designator.selectors else ""
        line = expression.position.line
        if name == "peek":
            raise self._error(
                "PEEK ist ein C64-spezifischer Befehl und für Amiga nicht verfügbar.",
                expression.position,
            )
        if name in {"chr", "ord", "lo", "hi"}:
            self._require_argument_count(
                designator.name,
                expression.arguments,
                1,
                expression.position,
            )
            self._compile_expr(expression.arguments[0])
            if name == "hi":
                self.emitter.emit("    lsr.w #8,d0", line)
            elif name in {"chr", "lo"}:
                self.emitter.emit("    andi.w #$00FF,d0", line)
            return CHAR_TYPE if name == "chr" else INTEGER_TYPE
        routine = self.external_routines.get(name)
        if routine is not None:
            if routine.result_type is None:
                raise self._error(
                    f"{routine.name} ist keine Funktion.",
                    expression.position,
                )
            return self._compile_external_call(
                routine, expression.arguments, expression.position
            )
        method, receiver = self._resolve_method_call(designator)
        if method.result_type is None:
            raise self._error(
                f"{method.owner.name}.{method.name} ist keine Funktion.",
                expression.position,
            )
        return self._compile_method_call(
            method,
            receiver,
            expression.arguments,
            expression.position,
        )

    def _emit_set_self_address(self, receiver: _StorageAccess, line: int) -> None:
        self._emit_address(receiver, line)
        self.emitter.emit("    move.l a0,a5", line)

    def _compile_method_call(
        self,
        method: _MethodInfo,
        receiver: _StorageAccess,
        arguments: Sequence[Expression],
        position: SourcePosition,
    ) -> _PascalType:
        self._require_argument_count(
            method.name,
            arguments,
            len(method.parameters),
            position,
        )
        line = position.line
        for argument, parameter, variable in zip(
            arguments,
            method.parameters,
            method.parameter_variables,
        ):
            argument_type = self._compile_expr(argument)
            if not argument_type.scalar or not parameter.type_info.scalar:
                raise self._error(
                    "Aggregatparameter werden noch nicht unterstützt.",
                    argument.position,
                )
            if not self._types_compatible(parameter.type_info, argument_type):
                raise self._error(
                    f"Argumenttyp {argument_type.name} passt nicht zu "
                    f"{parameter.type_info.name}.",
                    argument.position,
                )
            self._store_variable(variable, line)

        restore_self = self.current_method is not None
        if restore_self:
            self.emitter.emit("    move.l a5,-(sp)", line)
        self._emit_set_self_address(receiver, line)
        self.emitter.emit(f"    bsr {method.label}", line)
        if restore_self:
            self.emitter.emit("    move.l (sp)+,a5", line)
        return method.result_type if method.result_type is not None else BYTE_TYPE

    def _compile_condition_jump_false(self, expression: Expression, target: str) -> None:
        result_type = self._compile_expr(expression)
        if result_type == STRING_TYPE:
            raise self._error(
                "String kann nicht als Bedingung verwendet werden.",
                expression.position,
            )
        self.emitter.emit("    tst.w d0", expression.position.line)
        self.emitter.emit(f"    beq {target}", expression.position.line)

    def _compile_for(self, statement: ForStatement) -> None:
        variable = self._lookup_variable(statement.name)
        if variable is None or variable.internal:
            raise self._error(
                f"FOR-Variable nicht gefunden: {statement.name}.",
                statement.position,
            )
        if variable.type_info not in {INTEGER_TYPE, BYTE_TYPE, CHAR_TYPE}:
            raise self._error(
                "FOR erwartet Integer, Byte oder Char.",
                statement.position,
            )
        line = statement.position.line
        self._compile_expr(statement.initial)
        self._store_variable(variable, line)
        hidden_name = f"$for_limit_{self.label_counter}_{len(self.variable_order)}"
        limit = self._declare_variable(
            hidden_name,
            variable.type_info,
            statement.position,
            internal=True,
        )
        self._compile_expr(statement.final)
        self._store_variable(limit, line)

        condition_label = self._new_label("for_condition")
        increment_label = self._new_label("for_step")
        end_label = self._new_label("for_end")
        self.emitter.emit(f"{condition_label}:", line)
        comparison = BinaryExpression(
            statement.position,
            DesignatorExpression(statement.position, statement.name),
            "<=" if statement.direction == "to" else ">=",
            DesignatorExpression(statement.position, hidden_name),
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
        self._emit_load_access(
            _StorageAccess(
                variable.type_info,
                variable.position,
                variable.label,
                False,
            ),
            line,
        )
        self.emitter.emit(
            "    addq.w #1,d0" if statement.direction == "to" else "    subq.w #1,d0",
            line,
        )
        self._store_variable(variable, line)
        self.emitter.emit(f"    bra {condition_label}", line)
        self.emitter.emit(f"{end_label}:", line)

    def _compile_call_statement(self, statement: CallStatement) -> None:
        designator = self._as_designator(statement.designator, statement.position)
        name = self._key(designator.name) if not designator.selectors else ""
        line = statement.position.line

        # Sprach-/Runtime-Builtins werden vor externen Deklarationen behandelt.
        # Das ist insbesondere fuer C-Systemheader wichtig, die Prototypen wie
        # ``void clrscr(void);`` bereitstellen.
        if name in {"write", "writeln"}:
            for argument in statement.arguments:
                type_info = self._compile_expr(argument)
                if type_info == STRING_TYPE:
                    self.runtime.add("print_string")
                    self.emitter.emit(f"    bsr {self.symbol_prefix}_print_string", line)
                elif type_info == CHAR_TYPE:
                    self.runtime.update({"print_string", "print_char"})
                    self.emitter.emit(f"    bsr {self.symbol_prefix}_print_char", line)
                else:
                    self.runtime.update({"print_string", "print_int16"})
                    self.emitter.emit(f"    bsr {self.symbol_prefix}_print_int16", line)
            if name == "writeln":
                self.runtime.add("print_string")
                label = self._string_label("\n", statement.position)
                self.emitter.emit(f"    lea {label}(pc),a0", line)
                self.emitter.emit(f"    bsr {self.symbol_prefix}_print_string", line)
            return
        if name == "clrscr":
            self._require_argument_count(
                designator.name,
                statement.arguments,
                0,
                statement.position,
            )
            self.runtime.add("clear_screen")
            self.emitter.emit(f"    bsr {self.symbol_prefix}_clear_screen", line)
            return
        if name in {"settextcolor", "amiga_set_text_color"}:
            self._require_argument_count(
                designator.name,
                statement.arguments,
                2,
                statement.position,
            )
            foreground_type = self._compile_expr(statement.arguments[0])
            if foreground_type == STRING_TYPE:
                raise self._error(
                    "SetTextColor erwartet zwei 12-Bit-RGB-Werte.",
                    statement.arguments[0].position,
                )
            self.emitter.emit("    move.w d0,-(sp)", line)
            background_type = self._compile_expr(statement.arguments[1])
            if background_type == STRING_TYPE:
                raise self._error(
                    "SetTextColor erwartet zwei 12-Bit-RGB-Werte.",
                    statement.arguments[1].position,
                )
            self.emitter.emit("    move.w d0,d1", line)
            self.emitter.emit("    move.w (sp)+,d0", line)
            self.runtime.add("set_text_color")
            self.emitter.emit(
                f"    bsr {self.symbol_prefix}_set_text_color",
                line,
            )
            return
        routine = self.external_routines.get(name)
        if routine is not None:
            # Object Pascal permits a function call as a statement; execute it
            # normally and intentionally ignore the value left in the result
            # register.
            self._compile_external_call(
                routine, statement.arguments, statement.position
            )
            return
        if name == "poke":
            raise self._error(
                "POKE ist ein C64-spezifischer Befehl und für Amiga nicht verfügbar.",
                statement.position,
            )
        if name in {"inc", "dec"}:
            self._require_argument_count(
                designator.name,
                statement.arguments,
                1,
                statement.position,
            )
            argument = statement.arguments[0]
            if not isinstance(argument, (NameExpression, DesignatorExpression)):
                raise self._error(
                    f"{designator.name} erwartet eine Variable.",
                    statement.position,
                )
            target = self._as_designator(argument)
            target_type = self._resolve_storage(target).type_info
            if (
                target_type not in {INTEGER_TYPE, BYTE_TYPE, CHAR_TYPE}
                and target_type.kind != "enum"
            ):
                raise self._error(
                    f"{designator.name} erwartet einen ordinalen Wert.",
                    argument.position,
                )
            self._compile_assignment(
                AssignmentStatement(
                    statement.position,
                    target,
                    BinaryExpression(
                        statement.position,
                        argument,
                        "+" if name == "inc" else "-",
                        LiteralExpression(statement.position, 1),
                    ),
                )
            )
            return
        if name == "halt":
            self._require_argument_count(
                designator.name,
                statement.arguments,
                0,
                statement.position,
            )
            label = self._new_label("halt")
            self.emitter.emit(f"{label}:", line)
            self.emitter.emit(f"    bra {label}", line)
            return
        method, receiver = self._resolve_method_call(designator)
        self._compile_method_call(
            method,
            receiver,
            statement.arguments,
            statement.position,
        )

    def _emit_methods(self) -> None:
        for method in self.methods:
            implementation = method.implementation
            if implementation is None:
                continue
            self.emitter.emit()
            self.emitter.emit(
                f"; {method.kind} {method.owner.name}.{method.name}",
                implementation.position.line,
            )
            self.emitter.emit(f"{method.label}:", implementation.position.line)

            previous_method = self.current_method
            previous_scope = self.scope_variables
            self.current_method = method
            self.scope_variables = {
                self._key(parameter.name): variable
                for parameter, variable in zip(
                    method.parameters,
                    method.parameter_variables,
                )
            }
            self.scope_variables.update(method.local_variables)
            if method.result_variable is not None:
                self.scope_variables["result"] = method.result_variable
                self.scope_variables[self._key(method.name)] = method.result_variable
            try:
                for variable in method.local_variables.values():
                    self.emitter.emit("    moveq #0,d0", implementation.position.line)
                    for offset in range(variable.type_info.size):
                        self.emitter.emit(
                            f"    lea {variable.label}(pc),a0",
                            implementation.position.line,
                        )
                        if offset:
                            self.emitter.emit(
                                f"    adda.w #${offset:04X},a0",
                                implementation.position.line,
                            )
                        self.emitter.emit("    move.b d0,(a0)", implementation.position.line)
                if method.result_variable is not None:
                    self.emitter.emit("    moveq #0,d0", implementation.position.line)
                    self._store_variable(method.result_variable, implementation.position.line)
                for variable, initializer in method.local_initializers:
                    result_type = self._compile_expr(initializer)
                    if not self._types_compatible(variable.type_info, result_type):
                        raise self._error(
                            f"Initialisierung von {variable.name} besitzt den falschen Typ.",
                            initializer.position,
                        )
                    self._store_variable(variable, initializer.position.line)
                self._compile_statement(implementation.body)
                if method.result_variable is not None:
                    self._emit_load_access(
                        _StorageAccess(
                            method.result_variable.type_info,
                            implementation.position,
                            method.result_variable.label,
                            False,
                        ),
                        implementation.position.line,
                    )
                self.emitter.emit("    rts", implementation.position.line)
            finally:
                self.scope_variables = previous_scope
                self.current_method = previous_method

    def _emit_runtime(self) -> None:
        self.emitter.emit()
        self.emitter.emit("; Wartet auf den sicheren unteren Vertical-Blank-Bereich")
        self.emitter.emit(f"{self.symbol_prefix}_wait_safe_line:")
        self.emitter.emit("    move.l #$00DFF000,a0")
        wait_loop = f"{self.symbol_prefix}_wait_safe_line_loop"
        self.emitter.emit(f"{wait_loop}:")
        self.emitter.emit("    move.w $0006(a0),d0 ; VHPOSR")
        self.emitter.emit("    andi.w #$FF00,d0")
        self.emitter.emit("    cmpi.w #$F500,d0")
        self.emitter.emit(f"    bcs {wait_loop}")
        self.emitter.emit("    rts")

        self.emitter.emit()
        self.emitter.emit("; Copper-Liste bei $10000 lädt den Text-Bitplane-Zeiger in jedem Frame neu")
        self.emitter.emit(f"{self.symbol_prefix}_install_text_copper:")
        self.emitter.emit("    move.l #$00010000,a1")
        self.emitter.emit("    move.l #$008E2C81,(a1)+")
        self.emitter.emit("    move.l #$0090F4C1,(a1)+")
        self.emitter.emit("    move.l #$00920038,(a1)+")
        self.emitter.emit("    move.l #$009400D0,(a1)+")
        self.emitter.emit("    move.l #$01001200,(a1)+")
        self.emitter.emit("    move.l #$01020000,(a1)+")
        self.emitter.emit("    move.l #$01040000,(a1)+")
        self.emitter.emit("    move.l #$01080000,(a1)+")
        self.emitter.emit("    move.l #$010A0000,(a1)+")
        self.emitter.emit("    move.l #$00E00001,(a1)+")
        self.emitter.emit("    move.l #$00E28000,(a1)+")
        self.emitter.emit("    move.l #$01800000,(a1)+")
        self.emitter.emit("    move.l #$018200F0,(a1)+")
        self.emitter.emit("    move.l #$FFFFFFFE,(a1)+")
        self.emitter.emit("    rts")

        self.emitter.emit()
        self.emitter.emit("; Direkte OCS-Bildschirminitialisierung, 320x200, 1 Bitplane")
        self.emitter.emit(f"{self.symbol_prefix}_screen_init:")
        self.emitter.emit(f"    bsr {self.symbol_prefix}_wait_safe_line")
        self.emitter.emit("    move.l #$00DFF000,a0")
        self.emitter.emit("    move.w #$7FFF,$009A(a0) ; INTENA: Interrupts aus")
        self.emitter.emit("    move.w #$7FFF,$0096(a0) ; DMACON: DMA aus")
        self.emitter.emit(f"    bsr {self.symbol_prefix}_clear_screen")
        self.emitter.emit(f"    bsr {self.symbol_prefix}_install_text_copper")
        self.emitter.emit("    move.l #$00DFF000,a0")
        self.emitter.emit("    move.l #$00010000,d0")
        self.emitter.emit("    move.l d0,$0080(a0) ; COP1LCH/COP1LCL")
        self.emitter.emit("    move.w #$0000,$0088(a0) ; COPJMP1")
        self.emitter.emit("    move.w #$8380,$0096(a0) ; SET+DMAEN+BPLEN+COPEN")
        self.emitter.emit("    rts")

        self.emitter.emit("; Löscht 8000 Bytes Text-Bitplane-RAM und setzt den Cursor zurück")
        self.emitter.emit(f"{self.symbol_prefix}_clear_screen:")
        self.emitter.emit("    move.l #$00018000,a0")
        self.emitter.emit("    move.w #$07D0,d0")
        clear_loop = f"{self.symbol_prefix}_clear_screen_loop"
        self.emitter.emit(f"{clear_loop}:")
        self.emitter.emit("    clr.l (a0)+")
        self.emitter.emit("    subq.w #1,d0")
        self.emitter.emit(f"    bne {clear_loop}")
        self.emitter.emit(f"    lea {self.symbol_prefix}_cursor_x(pc),a0")
        self.emitter.emit("    clr.b (a0)")
        self.emitter.emit(f"    lea {self.symbol_prefix}_cursor_y(pc),a0")
        self.emitter.emit("    clr.b (a0)")
        self.emitter.emit("    rts")

        if "set_text_color" in self.runtime:
            self.emitter.emit()
            self.emitter.emit("; D0.W = Vordergrund-$RGB, D1.W = Hintergrund-$RGB")
            self.emitter.emit(f"{self.symbol_prefix}_set_text_color:")
            self.emitter.emit("    andi.w #$0FFF,d0")
            self.emitter.emit("    andi.w #$0FFF,d1")
            self.emitter.emit("    move.l #$00DFF000,a0")
            self.emitter.emit("    move.w d1,$0180(a0)")
            self.emitter.emit("    move.w d0,$0182(a0)")
            self.emitter.emit("    move.l #$0001002E,a0 ; Copper COLOR00 value")
            self.emitter.emit("    move.w d1,(a0)")
            self.emitter.emit("    move.l #$00010032,a0 ; Copper COLOR01 value")
            self.emitter.emit("    move.w d0,(a0)")
            self.emitter.emit("    rts")

        if "range_error" in self.runtime:
            self.runtime.add("print_string")
            label = self._string_label(
                "Index out of range\n",
                SourcePosition(1, 1),
            )
            self.emitter.emit()
            self.emitter.emit(f"{self.symbol_prefix}_range_error:")
            self.emitter.emit(f"    lea {label}(pc),a0")
            self.emitter.emit(f"    bsr {self.symbol_prefix}_print_string")
            halt_label = f"{self.symbol_prefix}_range_error_halt"
            self.emitter.emit(f"{halt_label}:")
            self.emitter.emit(f"    bra {halt_label}")

        if "print_char" in self.runtime or "print_string" in self.runtime:
            self.emitter.emit()
            self.emitter.emit("; D0.B = ASCII-Zeichen, Ausgabe als 8x8-Bitmaske")
            self.emitter.emit(f"{self.symbol_prefix}_print_char:")
            newline = f"{self.symbol_prefix}_print_char_newline"
            substitute = f"{self.symbol_prefix}_print_char_substitute"
            glyph = f"{self.symbol_prefix}_print_char_glyph"
            done = f"{self.symbol_prefix}_print_char_done"
            self.emitter.emit("    cmpi.w #$000A,d0")
            self.emitter.emit(f"    beq {newline}")
            self.emitter.emit("    cmpi.w #$000D,d0")
            self.emitter.emit(f"    beq {newline}")
            self.emitter.emit("    cmpi.w #$0019,d0")
            self.emitter.emit(f"    bcs {substitute}")
            self.emitter.emit("    cmpi.w #$007F,d0")
            self.emitter.emit(f"    bcs {glyph}")
            self.emitter.emit(f"{substitute}:")
            self.emitter.emit("    move.w #$003F,d0")
            self.emitter.emit(f"{glyph}:")
            self.emitter.emit("    subi.w #$0020,d0")
            self.emitter.emit("    mulu.w #$0008,d0")
            self.emitter.emit(f"    lea {self.symbol_prefix}_font_8x8(pc),a2")
            self.emitter.emit("    adda.w d0,a2")
            self.emitter.emit(f"    lea {self.symbol_prefix}_cursor_y(pc),a1")
            self.emitter.emit("    moveq #0,d1")
            self.emitter.emit("    move.b (a1),d1")
            self.emitter.emit("    mulu.w #$0140,d1")
            self.emitter.emit("    move.l #$00018000,a1")
            self.emitter.emit("    adda.l d1,a1")
            self.emitter.emit(f"    lea {self.symbol_prefix}_cursor_x(pc),a0")
            self.emitter.emit("    moveq #0,d1")
            self.emitter.emit("    move.b (a0),d1")
            self.emitter.emit("    adda.w d1,a1")
            for unused_row in range(8):
                self.emitter.emit("    move.b (a2)+,(a1)")
                self.emitter.emit("    adda.w #$0028,a1")
            self.emitter.emit(f"    lea {self.symbol_prefix}_cursor_x(pc),a0")
            self.emitter.emit("    addq.b #1,(a0)")
            self.emitter.emit("    moveq #0,d0")
            self.emitter.emit("    move.b (a0),d0")
            self.emitter.emit("    cmpi.w #$0028,d0")
            self.emitter.emit(f"    bcs {done}")
            self.emitter.emit(f"{newline}:")
            self.emitter.emit(f"    lea {self.symbol_prefix}_cursor_x(pc),a0")
            self.emitter.emit("    clr.b (a0)")
            self.emitter.emit(f"    lea {self.symbol_prefix}_cursor_y(pc),a0")
            self.emitter.emit("    addq.b #1,(a0)")
            self.emitter.emit("    moveq #0,d0")
            self.emitter.emit("    move.b (a0),d0")
            self.emitter.emit("    cmpi.w #$0019,d0")
            self.emitter.emit(f"    bcs {done}")
            self.emitter.emit(f"    bsr {self.symbol_prefix}_clear_screen")
            self.emitter.emit(f"{done}:")
            self.emitter.emit("    rts")

        if "print_int16" in self.runtime:
            self.emitter.emit()
            self.emitter.emit(f"{self.symbol_prefix}_print_int16:")
            self.emitter.emit("    move.w d0,d4")
            self.emitter.emit(f"    lea {self.symbol_prefix}_int_buffer_end(pc),a0")
            self.emitter.emit("    clr.b -(a0)")
            self.emitter.emit("    moveq #0,d2")
            self.emitter.emit("    move.w d0,d2")
            positive = f"{self.symbol_prefix}_print_int_positive"
            loop = f"{self.symbol_prefix}_print_int_loop"
            write = f"{self.symbol_prefix}_print_int_write"
            self.emitter.emit(f"    bpl {positive}")
            self.emitter.emit("    neg.w d2")
            self.emitter.emit(f"{positive}:")
            self.emitter.emit("    moveq #10,d3")
            self.emitter.emit(f"{loop}:")
            self.emitter.emit("    divu.w d3,d2")
            self.emitter.emit("    swap d2")
            self.emitter.emit("    addi.b #$30,d2")
            self.emitter.emit("    move.b d2,-(a0)")
            self.emitter.emit("    swap d2")
            self.emitter.emit("    tst.w d2")
            self.emitter.emit(f"    bne {loop}")
            self.emitter.emit("    tst.w d4")
            self.emitter.emit(f"    bpl {write}")
            self.emitter.emit("    move.b #$2D,-(a0)")
            self.emitter.emit(f"{write}:")
            self.emitter.emit(f"    bsr {self.symbol_prefix}_print_string")
            self.emitter.emit("    rts")

        if "print_string" in self.runtime:
            self.emitter.emit()
            self.emitter.emit("; A0 = nullterminierte Latin-1-Zeichenkette")
            self.emitter.emit(f"{self.symbol_prefix}_print_string:")
            self.emitter.emit("    move.l a0,a3")
            loop = f"{self.symbol_prefix}_print_string_loop"
            done = f"{self.symbol_prefix}_print_string_done"
            self.emitter.emit(f"{loop}:")
            self.emitter.emit("    moveq #0,d0")
            self.emitter.emit("    move.b (a3)+,d0")
            self.emitter.emit(f"    beq {done}")
            self.emitter.emit(f"    bsr {self.symbol_prefix}_print_char")
            self.emitter.emit(f"    bra {loop}")
            self.emitter.emit(f"{done}:")
            self.emitter.emit("    rts")

    def _emit_data(self) -> None:
        self.emitter.emit()
        self.emitter.emit("    even")
        self.emitter.emit("; Direkte Amiga-Bildschirmlaufzeitdaten")
        self.emitter.emit(f"{self.symbol_prefix}_cursor_x: dc.b 0")
        self.emitter.emit(f"{self.symbol_prefix}_cursor_y: dc.b 0")
        self.emitter.emit(f"{self.symbol_prefix}_int_buffer: ds.b 8")
        self.emitter.emit(f"{self.symbol_prefix}_int_buffer_end:")

        if self.variable_order:
            self.emitter.emit()
            self.emitter.emit(f"; {self.language_name}-Variablen")
            for variable in self.variable_order:
                self.emitter.emit("    even")
                comment = "intern" if variable.internal else variable.name
                initial_value = getattr(variable, "c_initial_value", None)
                if initial_value is not None and variable.type_info.size == 2:
                    storage = f"dc.w ${int(initial_value) & 0xFFFF:04X}"
                elif initial_value is not None and variable.type_info.size == 1:
                    storage = f"dc.b ${int(initial_value) & 0xFF:02X}"
                else:
                    storage = f"ds.b {variable.type_info.size}"
                self.emitter.emit(
                    f"{variable.label}: {storage} "
                    f"; {comment}: {variable.type_info.name}"
                )

        if self.strings:
            self.emitter.emit()
            self.emitter.emit("; Nullterminierte Amiga-Latin-1-Zeichenketten")
            for data, label in self.strings.items():
                values = ", ".join(f"${value:02X}" for value in data + b"\x00")
                self.emitter.emit(f"{label}: dc.b {values}")

        if self.runtime.intersection({"print_char", "print_string", "print_int16"}):
            self.emitter.emit()
            self.emitter.emit("; 96 Glyphen, ASCII $20..$7F, je 8 Bytes")
            self.emitter.emit(f"{self.symbol_prefix}_font_8x8:")
            for offset in range(0, len(_AMIGA_FONT_8X8), 16):
                values = ", ".join(
                    f"${value:02X}"
                    for value in _AMIGA_FONT_8X8[offset:offset + 16]
                )
                self.emitter.emit(f"    dc.b {values}")

    def generate(self) -> GeneratedAssembly:
        self._prepare_symbols()
        source_line = self.program.body.position.line
        end_label = f"{self.symbol_prefix}_program_end"
        self.emitter.emit(
            f"; Von {self.language_name} erzeugter Motorola-68000-Assembler"
        )
        self.emitter.emit("; Ziel: Commodore Amiga 500 / Standalone-Boot-ADF")
        self.emitter.emit("; Runtime: direkte OCS-Register, keine Workbench-Libraries")
        self.emitter.emit(f"; Programm: {self.program.name}")
        self.emitter.emit(".bootable")
        self.emitter.emit("section code,code")
        self.emitter.emit("xdef _start")
        self.emitter.emit("_start:", source_line)
        self.emitter.emit("    move.l #$0007FFFC,sp", source_line)
        self.emitter.emit(f"    bsr {self.symbol_prefix}_screen_init", source_line)

        for variable, initializer in self.initializers:
            result_type = self._compile_expr(initializer)
            if result_type == STRING_TYPE:
                raise self._error(
                    "String-Variablen werden noch nicht unterstützt.",
                    initializer.position,
                )
            if not variable.type_info.scalar:
                raise self._error(
                    "Aggregate können nicht direkt initialisiert werden.",
                    initializer.position,
                )
            if not self._types_compatible(variable.type_info, result_type):
                raise self._error(
                    f"Initialisierung von {variable.name} besitzt den falschen Typ.",
                    initializer.position,
                )
            self._store_variable(variable, initializer.position.line)

        self._compile_statement(self.program.body)
        self.emitter.emit(f"    bra {end_label}", source_line)
        self._emit_methods()
        self._emit_runtime()
        self.emitter.emit()
        self.emitter.emit(f"{end_label}:", source_line)
        self.emitter.emit(f"    bra {end_label}", source_line)
        self._emit_data()
        self.emitter.emit("end")
        assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
        return GeneratedAssembly(
            self.program.name,
            assembly,
            dict(self.emitter.source_map),
            sum(not variable.internal for variable in self.variable_order),
            len(self.strings),
        )



def _unit_marker_assembly(unit_name: str, target: str) -> str:
    """Erzeugt den Anker eines separat kompilierten Pascal-Unit-Moduls.

    Zielabhängige Implementierungsdateien werden anschließend anhand der PUI
    statisch angefügt. Der Anker sorgt dafür, dass auch eine reine Interface-
    Unit ein eindeutig benanntes Modul besitzt.
    """
    safe_name = re.sub(r"[^A-Za-z0-9_]", "_", unit_name)
    normalized_target = str(target).strip().casefold()
    if normalized_target in {"pe32", "win32", "windows", "windows-pe32"}:
        return (
            "; Von Pascal erzeugtes Windows-PE32-Unit-Modul\n"
            f"; Unit: {unit_name}\n"
            "bits 32\n"
            f"global __unit_{safe_name}\n"
            f"__unit_{safe_name}:\n"
            "    ret\n"
        )
    if normalized_target in {
        "pe64", "win64", "windows64", "windows-pe64", "windows-pe32+"
    }:
        return (
            "; Von Pascal erzeugtes Windows-PE32+-AMD64-Unit-Modul\n"
            f"; Unit: {unit_name}\n"
            "; Architektur: AMD64 / x86-64 / COFF64\n"
            "bits 64\n"
            f"global __unit_{safe_name}\n"
            f"__unit_{safe_name}:\n"
            "    ret\n"
        )
    if normalized_target in {"amiga", "amiga500", "a500", "m68k", "68000"}:
        return (
            "; Von Pascal erzeugtes Amiga-Unit-Modul\n"
            f"; Unit: {unit_name}\n"
            "; Zielabhängige Routinen werden aus dem in der PUI genannten ASM-Modul gelinkt.\n"
            "section code,code\n"
            f"xdef __unit_{safe_name}\n"
            f"__unit_{safe_name}:\n"
            "    rts\n"
            "end\n"
        )
    return (
        "; Von Pascal erzeugtes C64-Unit-Modul\n"
        f"; Unit: {unit_name}\n"
        "; Zielabhängige Routinen werden aus dem in der PUI genannten ASM-Modul gelinkt.\n"
        f"__unit_{safe_name}:\n"
        "    rts\n"
    )


def _compile_pascal_unit_interface(
    source: str,
    *,
    filename: str,
    include_paths: Iterable[Path | str],
    predefined_macros: Optional[Dict[str, Union[str, int, bool]]],
    target: str,
    linked_object_files: Sequence[str] = (),
    link_search_paths: Iterable[Path | str] = (),
    output_directory: Optional[Path | str] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> GeneratedAssembly:
    """Kompiliert eine direkt geöffnete Pascal-Unit.

    Die Unit wird nicht als PROGRAM an den ANTLR-Parser übergeben. Stattdessen
    werden UNIT/INTERFACE/IMPLEMENTATION zuerst zerlegt, die PUI-Datei wird
    geschrieben und ein separates Unit-ASM-Modul erzeugt.
    """
    preprocessor = PascalPreprocessor(
        predefined_macros, link_search_paths=link_search_paths
    )
    processed = preprocessor.process(source, filename=filename)
    supplied_link_files = tuple(str(item) for item in linked_object_files)
    (
        transformed_source,
        unit_name,
        interface_units,
        implementation_units,
        interface_source,
        implementation_source,
    ) = _unit_program_source(processed.source, filename=filename)

    # PUI immer neben der gespeicherten Unit anlegen.
    source_path: Optional[Path]
    try:
        candidate = Path(filename).expanduser().resolve()
        source_path = candidate if candidate.is_file() else None
    except (OSError, RuntimeError, ValueError):
        source_path = None

    pui_path: Optional[Path] = None
    pui_document: Optional[Dict[str, object]] = None

    # Abhängigkeiten werden bereits beim Unit-Build geprüft und ihre PUI-Dateien
    # bei Bedarf erzeugt. Zielabhängige ASM-Module werden anschließend anhand
    # der PUI statisch mit dem erzeugten Unit-Modul zusammengeführt.
    resolver = _PascalUnitResolver(
        filename=filename,
        include_paths=include_paths,
        preprocessor=preprocessor,
        target=target,
        output_directory=output_directory,
        progress_callback=progress_callback,
    )
    for dependency in interface_units + implementation_units:
        resolver.resolve(dependency)

    # Parse the complete unit once for code generation/import metadata. The PUI
    # writer receives this AST but serializes metadata only, never source text.
    full_unit_program = _parse_pascal_program_with_progress(
        transformed_source,
        progress_callback,
        filename,
    )

    # Interface EXTERNAL declarations are intentionally blanked before the
    # synthetic PROGRAM parse. Re-attach their semantic metadata directly so
    # the Unit object and source-free PUI retain DLL/import/calling-convention
    # information without reintroducing interface source text.
    _unused_parser_interface, interface_routines = _pui_routine_information(
        unit_name, interface_source
    )
    del _unused_parser_interface
    interface_externals = _pui_interface_external_declarations(
        unit_name, interface_routines
    )
    if interface_externals:
        full_unit_program = replace(
            full_unit_program,
            external_routines=(
                tuple(full_unit_program.external_routines)
                + tuple(interface_externals)
            ),
        )
    if source_path is not None:
        pui_path = (
            Path(output_directory).expanduser().resolve()
            / source_path.with_suffix(".pui").name
            if output_directory
            else source_path.with_suffix(".pui")
        )
        pui_document = _pui_document(
            unit_name=unit_name,
            interface_source=interface_source,
            interface_units=interface_units,
            implementation_units=implementation_units,
            source_path=source_path,
            target=target,
            full_program=full_unit_program,
            dependency_programs=tuple(resolver.programs),
            link_files=tuple(
                dict.fromkeys(list(supplied_link_files) + list(processed.link_files))
            ),
            macros=processed.macros,
        )
        _write_pui_document(pui_path, pui_document)

    implementation_mask = _pascal_code_mask(implementation_source)
    has_pascal_routines = bool(re.search(
        r"\b(procedure|function|constructor|destructor)\b",
        implementation_mask,
        re.IGNORECASE,
    ))
    normalized_target = str(target).strip().casefold()

    if normalized_target in {"pe32", "win32", "windows", "windows-pe32"}:
        # Für Windows PE32 wird die vollständige Unit als echtes, relocierbares
        # Pascal-Modul übersetzt. Der vorhandene d64_dism-Assembler baut daraus
        # anschließend COFF32; es entsteht bewusst keine _start-Routine.
        unit_program = full_unit_program

        constants: List[ConstDeclaration] = []
        type_groups: List[Sequence[TypeDeclaration]] = []
        variables: List[VarDeclaration] = []
        methods: List[MethodImplementation] = []
        externals: List[ExternalRoutineDeclaration] = []
        global_routines: List[GlobalRoutineImplementation] = []

        # Stage212: public routines imported through dependency PUIs live in
        # resolver.external_routines.  Program compilation already consumes
        # this visibility list, but the PE32/PE64 Unit path previously merged
        # only resolver.programs.  That made declarations such as
        # Windows.User.CreateWindowExA invisible while compiling VCL.Controls
        # and the unqualified call incorrectly fell through to Self-method
        # lookup ("Methode nicht gefunden: CreateWindowExA").
        externals.extend(resolver.external_routines)

        for dependency_program in resolver.programs:
            constants.extend(dependency_program.constants)
            type_groups.append(dependency_program.types)
            variables.extend(dependency_program.variables)
            methods.extend(dependency_program.methods)
            externals.extend(dependency_program.external_routines)
            global_routines.extend(dependency_program.global_routines)
        constants.extend(unit_program.constants)
        type_groups.append(unit_program.types)
        variables.extend(unit_program.variables)
        methods.extend(unit_program.methods)
        externals.extend(unit_program.external_routines)
        global_routines.extend(unit_program.global_routines)
        types = _merge_pascal_type_scopes(
            tuple(type_groups[:-1]),
            tuple(type_groups[-1]) if type_groups else (),
        )

        merged_program = PascalProgram(
            name=unit_program.name,
            constants=tuple(constants),
            variables=tuple(variables),
            body=unit_program.body,
            types=tuple(types),
            methods=tuple(methods),
            external_routines=tuple(externals),
            global_routines=tuple(global_routines),
            unit_assembly_files=tuple(resolver.assembly_files),
            unit_object_files=tuple(
                dict.fromkeys(
                    list(supplied_link_files)
                    + list(preprocessor.link_files)
                    + list(resolver.object_files)
                )
            ),
        )
        generated = _PE32CodeGenerator(
            merged_program,
            console_mode=False,
            unit_name=unit_name,
        ).generate()
        generated = replace(
            generated,
            notes=tuple(preprocessor.notes),
            warnings=tuple(preprocessor.warnings),
            source_kind="unit",
            unit_name=unit_name,
            pui_path=str(pui_path) if pui_path is not None else None,
            linked_object_files=tuple(merged_program.unit_object_files),
        )
    elif normalized_target in {
        "pe64", "win64", "windows64", "windows-pe64", "windows-pe32+"
    }:
        # Stage 191: native AMD64 path.  PE32+ never enters the C64/Amiga
        # marker fallback; executable Unit routines are emitted as x86-64 too.
        unit_program = full_unit_program
        constants: List[ConstDeclaration] = []
        type_groups: List[Sequence[TypeDeclaration]] = []
        variables: List[VarDeclaration] = []
        methods: List[MethodImplementation] = []
        externals: List[ExternalRoutineDeclaration] = []
        global_routines: List[GlobalRoutineImplementation] = []

        # Stage212: public routines imported through dependency PUIs live in
        # resolver.external_routines.  Program compilation already consumes
        # this visibility list, but the PE32/PE64 Unit path previously merged
        # only resolver.programs.  That made declarations such as
        # Windows.User.CreateWindowExA invisible while compiling VCL.Controls
        # and the unqualified call incorrectly fell through to Self-method
        # lookup ("Methode nicht gefunden: CreateWindowExA").
        externals.extend(resolver.external_routines)

        for dependency_program in resolver.programs:
            constants.extend(dependency_program.constants)
            type_groups.append(dependency_program.types)
            variables.extend(dependency_program.variables)
            methods.extend(dependency_program.methods)
            externals.extend(dependency_program.external_routines)
            global_routines.extend(dependency_program.global_routines)
        constants.extend(unit_program.constants)
        type_groups.append(unit_program.types)
        variables.extend(unit_program.variables)
        methods.extend(unit_program.methods)
        externals.extend(unit_program.external_routines)
        global_routines.extend(unit_program.global_routines)
        types = _merge_pascal_type_scopes(
            tuple(type_groups[:-1]),
            tuple(type_groups[-1]) if type_groups else (),
        )
        merged_program = PascalProgram(
            name=unit_program.name,
            constants=tuple(constants),
            variables=tuple(variables),
            body=unit_program.body,
            types=tuple(types),
            methods=tuple(methods),
            external_routines=tuple(externals),
            global_routines=tuple(global_routines),
            unit_assembly_files=tuple(resolver.assembly_files),
            unit_object_files=tuple(
                dict.fromkeys(
                    list(supplied_link_files)
                    + list(preprocessor.link_files)
                    + list(resolver.object_files)
                )
            ),
        )
        generated = _PE64CodeGenerator(
            merged_program,
            console_mode=False,
            unit_name=unit_name,
        ).generate()
        generated = replace(
            generated,
            notes=tuple(preprocessor.notes),
            warnings=tuple(preprocessor.warnings),
            source_kind="unit",
            unit_name=unit_name,
            pui_path=str(pui_path) if pui_path is not None else None,
            linked_object_files=tuple(merged_program.unit_object_files),
        )
    else:
        # C64/Amiga behalten den bisherigen Interface-Unit-Pfad. Echte
        # Pascal-Implementierungen bleiben dort bis zu einem separaten
        # Mehrmodul-Backend explizit abgelehnt.
        if has_pascal_routines:
            raise C64PascalError(
                "Globale Pascal-Routinen im IMPLEMENTATION-Teil einer Unit werden "
                "für dieses Ziel noch nicht unterstützt. Verwende PE32 oder ein "
                "getrenntes C-/ASM-Implementierungsmodul."
            )
        generated = GeneratedAssembly(
            program_name=unit_name,
            assembly=_unit_marker_assembly(unit_name, target),
            source_map={},
            variable_count=0,
            string_count=0,
            notes=tuple(preprocessor.notes),
            warnings=tuple(preprocessor.warnings),
            source_kind="unit",
            unit_name=unit_name,
            pui_path=str(pui_path) if pui_path is not None else None,
        )
    if pui_document is not None and pui_path is not None:
        implementation_file = _pui_target_assembly(
            pui_document,
            target=target,
            base_directory=pui_path.parent,
        )
        if implementation_file is None:
            c_implementation = _pui_target_c_source(
                pui_document,
                target=target,
                base_directory=pui_path.parent,
            )
            if c_implementation is not None:
                implementation_file = _compile_pui_c_implementation(
                    pui_document,
                    source_path=c_implementation,
                    target=target,
                    include_paths=include_paths,
                )
        if implementation_file is not None:
            generated = _link_pascal_assembly_modules(
                generated, (str(implementation_file),), target=target
            )
    return generated

def _link_pascal_assembly_modules(
    generated: GeneratedAssembly,
    assembly_files: Sequence[str],
    *,
    target: str = "c64",
) -> GeneratedAssembly:
    if not assembly_files:
        return generated
    normalized_target = str(target).strip().casefold()
    if normalized_target in {
        "pe32", "win32", "windows", "windows-pe32",
        "pe64", "win64", "windows64", "windows-pe64", "windows-pe32+",
    }:
        linked: List[str] = []
        for filename in assembly_files:
            path = Path(filename).expanduser().resolve()
            if not path.is_file():
                raise C64PascalError(f"Unit-Assembler nicht gefunden: {path}")
            linked.append(str(path))
        # PE32 bleibt absichtlich in getrennten Modulen: d64_dism.py assembliert
        # jedes Modul zu COFF32 und übergibt alle .o an den internen Linker.
        return replace(generated, linked_assembly_files=tuple(linked))
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
            raise C64PascalError(
                f"Unit-Assembler kann nicht gelesen werden: {path}: {exc}"
            ) from exc
        module_lines = module_source.rstrip().splitlines()
        if module_lines and module_lines[-1].strip().casefold() == "end":
            module_lines.pop()
        output.append(
            f"; --- statisch gelinktes Unit-Modul: {path.name} ---\n"
            + "\n".join(module_lines).rstrip()
        )
        linked.append(str(path))
    if str(target).strip().casefold() not in {
        "pe32", "win32", "windows", "windows-pe32",
        "pe64", "win64", "windows64", "windows-pe64", "windows-pe32+",
    }:
        output.append("end")
    return replace(
        generated,
        assembly="\n\n".join(output).rstrip() + "\n",
        linked_assembly_files=tuple(linked),
    )


def _split_pascal_export_items(text: str) -> Tuple[str, ...]:
    items: List[str] = []
    current: List[str] = []
    quote: Optional[str] = None
    for character in str(text):
        if quote is not None:
            current.append(character)
            if character == quote:
                quote = None
            continue
        if character in {"'", '"'}:
            quote = character
            current.append(character)
            continue
        if character == ",":
            value = "".join(current).strip()
            if value:
                items.append(value)
            current = []
            continue
        current.append(character)
    value = "".join(current).strip()
    if value:
        items.append(value)
    return tuple(items)


def _library_routine_header_end(mask: str, start: int) -> int:
    depth = 0
    for index in range(start, len(mask)):
        character = mask[index]
        if character == "(":
            depth += 1
        elif character == ")" and depth:
            depth -= 1
        elif character == ";" and depth == 0:
            return index
    return -1


def _looks_like_library_routine_implementation(mask: str, header_end: int) -> bool:
    # Nach dem Header darf ein lokaler VAR-Teil folgen. Entscheidend ist, dass
    # BEGIN vor einer neuen Routine-/TYPE-/CONST-/END-Deklaration erscheint.
    scan = mask[header_end + 1:]
    token_re = re.compile(
        r"\b(begin|procedure|function|constructor|destructor|type|const|end|exports)\b",
        re.IGNORECASE,
    )
    for match in token_re.finditer(scan):
        token = match.group(1).casefold()
        if token == "begin":
            return True
        return False
    return False


def _pascal_library_to_program_source(
    source: str,
    *,
    filename: str,
) -> Tuple[str, str, Dict[str, str]]:
    """Übersetzt den unterstützten LIBRARY-Subset in das vorhandene AST-Modell.

    Freie PROCEDURE/FUNCTION-Implementierungen werden intern Methoden einer
    synthetischen Klasse. Für jeden EXPORT entsteht später ein cdecl-Wrapper,
    der über die PE32-Exporttabelle veröffentlicht wird.
    """
    mask = _pascal_code_mask(source)
    header = re.match(
        r"\s*library\s+([A-Za-z_][A-Za-z0-9_]*)\s*;",
        mask,
        re.IGNORECASE,
    )
    if header is None:
        raise C64PascalError(f"Ungültiger LIBRARY-Header in {filename}.")
    library_name = header.group(1)

    exports_match = re.search(r"\bexports\b", mask[header.end():], re.IGNORECASE)
    exports_region = None
    public_exports: Dict[str, str] = {}
    if exports_match is not None:
        export_start = header.end() + exports_match.start()
        export_keyword_end = header.end() + exports_match.end()
        export_end = mask.find(";", export_keyword_end)
        if export_end < 0:
            raise C64PascalError("EXPORTS-Abschnitt besitzt kein abschließendes Semikolon.")
        exports_region = (export_start, export_end + 1)
        raw_items = source[export_keyword_end:export_end]
        for item in _split_pascal_export_items(raw_items):
            match = re.match(
                r"^([A-Za-z_][A-Za-z0-9_]*)"
                r"(?:\s+name\s+(['\"])(.*?)\2)?$",
                item.strip(),
                re.IGNORECASE | re.DOTALL,
            )
            if match is None:
                raise C64PascalError(
                    "EXPORTS unterstützt derzeit 'Name' oder "
                    "\"Name name 'Alias'\". Fehlerhaft: " + item
                )
            internal_name = match.group(1)
            public_name = match.group(3) or internal_name
            if public_name in public_exports:
                raise C64PascalError(f"DLL-Export mehrfach angegeben: {public_name}.")
            public_exports[public_name] = internal_name

    # Alle freien globalen PROCEDURE/FUNCTION-Implementierungen ermitteln.
    routine_re = re.compile(
        r"\b(procedure|function)\s+([A-Za-z_][A-Za-z0-9_]*)\b",
        re.IGNORECASE,
    )
    routines: List[Tuple[int, int, str, str]] = []
    for match in routine_re.finditer(mask, header.end()):
        name = match.group(2)
        after_name = match.end(2)
        if mask[after_name:].lstrip().startswith("."):
            # Bereits eine Klassenmethode.
            continue
        header_end = _library_routine_header_end(mask, match.end())
        if header_end < 0:
            continue
        if not _looks_like_library_routine_implementation(mask, header_end):
            continue
        routines.append((match.start(), header_end, match.group(1), name))

    if public_exports and not routines:
        raise C64PascalError(
            "LIBRARY EXPORTS gefunden, aber keine globalen PROCEDURE/FUNCTION-Implementierungen."
        )

    routine_names = {name.casefold() for _start, _end, _kind, name in routines}
    for public_name, internal_name in public_exports.items():
        if internal_name.casefold() not in routine_names:
            raise C64PascalError(
                f"DLL-Export {public_name} verweist auf nicht implementierte Routine {internal_name}."
            )

    replacements: List[Tuple[int, int, str]] = []
    # LIBRARY -> PROGRAM, Position/Länge bleiben bis auf das Schlüsselwort stabil.
    library_keyword = re.search(r"\blibrary\b", mask[:header.end()], re.IGNORECASE)
    assert library_keyword is not None
    replacements.append((library_keyword.start(), library_keyword.end(), "program"))

    if exports_region is not None:
        start, end = exports_region
        blanked = "".join("\n" if ch == "\n" else " " for ch in source[start:end])
        replacements.append((start, end, blanked))

    declarations: List[str] = []
    for start, header_end, kind, name in routines:
        header_text = source[start:header_end + 1].strip()
        declarations.append("    " + header_text)
        name_match = re.search(
            rf"\b{re.escape(kind)}\s+({re.escape(name)})\b",
            source[start:header_end + 1],
            re.IGNORECASE,
        )
        if name_match is None:
            raise C64PascalError(f"Interner LIBRARY-Transformationsfehler bei {name}.")
        absolute_name_start = start + name_match.start(1)
        absolute_name_end = start + name_match.end(1)
        replacements.append(
            (
                absolute_name_start,
                absolute_name_end,
                f"__D64LibraryExports.{name}",
            )
        )

    if routines:
        first_routine_start = min(item[0] for item in routines)
        class_decl = (
            "type\n"
            "  __D64LibraryExports = class\n"
            "  public\n"
            + "\n".join(declarations)
            + "\n  end;\n\n"
        )
        replacements.append((first_routine_start, first_routine_start, class_decl))

    transformed = source
    for start, end, value in sorted(replacements, key=lambda item: item[0], reverse=True):
        transformed = transformed[:start] + value + transformed[end:]
    return transformed, library_name, public_exports


def compile_pascal_to_assembly(
    source: str,
    *,
    filename: str = "<Pascal-Editor>",
    include_paths: Iterable[Path | str] = (),
    predefined_macros: Optional[Dict[str, Union[str, int, bool]]] = None,
    target: str = "c64",
    cpu_model: str = "mk68000",
    fpu_model: str = "FPU: None",
    graphics_backend: str = "Direct2D",
    linked_object_files: Sequence[str] = (),
    link_search_paths: Iterable[Path | str] = (),
    output_directory: Optional[Path | str] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> GeneratedAssembly:
    """Parst PROGRAM-, UNIT- oder PE32-LIBRARY-Quellen und erzeugt Assembler.

    Stage 198: ``progress_callback(filename, line)`` meldet echte Pascal-
    Quellzeilen aus dem ANTLR-Visitor und aus aufgelösten USES-Units.
    """
    source_kind = _pascal_source_kind(source)
    normalized_target = str(target).strip().casefold()
    del cpu_model, fpu_model

    if progress_callback is not None:
        progress_callback(filename, 1)

    if source_kind == "unit":
        return _compile_pascal_unit_interface(
            source,
            filename=filename,
            include_paths=include_paths,
            predefined_macros=predefined_macros,
            target=target,
            linked_object_files=linked_object_files,
            link_search_paths=link_search_paths,
            output_directory=output_directory,
            progress_callback=progress_callback,
        )

    library_name: Optional[str] = None
    library_exports: Dict[str, str] = {}
    frontend_source = source
    if source_kind == "library":
        if normalized_target not in {
            "pe32", "win32", "windows", "windows-pe32",
            "pe64", "win64", "windows64", "windows-pe64", "windows-pe32+",
        }:
            raise C64PascalError(
                "Pascal LIBRARY wird nur für Windows PE32/PE32+ unterstützt."
            )
        frontend_source, library_name, library_exports = _pascal_library_to_program_source(
            source,
            filename=filename,
        )

    program, preprocessed = _parse_pascal_frontend(
        frontend_source,
        filename=filename,
        include_paths=include_paths,
        predefined_macros=predefined_macros,
        target=target,
        link_search_paths=link_search_paths,
        output_directory=output_directory,
        progress_callback=progress_callback,
    )
    if normalized_target in {"c64", "c-64", "6510"}:
        generated = _CodeGenerator(program).generate()
    elif normalized_target in {"amiga", "amiga500", "a500", "m68k", "68000"}:
        generated = _AmigaCodeGenerator(program).generate()
    elif normalized_target in {"pe32", "win32", "windows", "windows-pe32"}:
        uses_graphics = bool(re.search(r"\bInitGraphics\s*\(", source, re.IGNORECASE))
        generated = _PE32CodeGenerator(
            program,
            graphics_backend=graphics_backend,
            console_mode=(not uses_graphics and source_kind != "library"),
            library_name=library_name,
            library_exports=library_exports,
        ).generate()
    elif normalized_target in {
        "pe64", "win64", "windows64", "windows-pe64", "windows-pe32+"
    }:
        uses_graphics = bool(re.search(r"\bInitGraphics\s*\(", source, re.IGNORECASE))
        generated = _PE64CodeGenerator(
            program,
            graphics_backend=graphics_backend,
            console_mode=(not uses_graphics and source_kind != "library"),
            library_name=library_name,
            library_exports=library_exports,
        ).generate()
    else:
        raise C64PascalError(f"Unbekanntes Compilerziel: {target}.")
    generated = _link_pascal_assembly_modules(
        generated, program.unit_assembly_files, target=target
    )
    return replace(
        generated,
        notes=preprocessed.notes,
        warnings=preprocessed.warnings,
        source_kind=source_kind,
        linked_object_files=tuple(
            dict.fromkeys(
                list(linked_object_files) + list(program.unit_object_files)
            )
        ),
    )
