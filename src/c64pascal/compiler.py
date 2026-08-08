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

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

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
class TryFinallyStatement(Statement):
    try_statement: Statement
    finally_statement: Statement


@dataclass(frozen=True)
class ExceptHandler:
    variable_name: str
    type_name: str
    body: Statement
    position: SourcePosition


@dataclass(frozen=True)
class TryExceptStatement(Statement):
    try_statement: Statement
    except_statement: Optional[Statement]
    handlers: Tuple[ExceptHandler, ...] = ()


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
class EnumTypeSpecification(TypeSpecification):
    names: Tuple[str, ...]


@dataclass(frozen=True)
class FieldDeclaration:
    names: Tuple[str, ...]
    type_name: str
    position: SourcePosition
    visibility: str = "public"


@dataclass(frozen=True)
class RecordTypeSpecification(TypeSpecification):
    fields: Tuple[FieldDeclaration, ...]


@dataclass(frozen=True)
class ArrayTypeSpecification(TypeSpecification):
    lower_bound: Expression
    upper_bound: Expression
    element_type_name: str


@dataclass(frozen=True)
class SetTypeSpecification(TypeSpecification):
    element_type_name: str


@dataclass(frozen=True)
class ParameterDeclaration:
    names: Tuple[str, ...]
    type_name: str
    modifier: str
    position: SourcePosition


@dataclass(frozen=True)
class MethodDeclaration:
    kind: str
    name: str
    parameters: Tuple[ParameterDeclaration, ...]
    result_type_name: Optional[str]
    position: SourcePosition
    visibility: str = "public"
    is_virtual: bool = False
    is_override: bool = False


@dataclass(frozen=True)
class PropertyDeclaration:
    name: str
    type_name: str
    read_name: Optional[str]
    write_name: Optional[str]
    position: SourcePosition
    visibility: str = "public"


@dataclass(frozen=True)
class ClassTypeSpecification(TypeSpecification):
    base_type_name: Optional[str]
    fields: Tuple[FieldDeclaration, ...]
    methods: Tuple[MethodDeclaration, ...]
    properties: Tuple[PropertyDeclaration, ...] = ()


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


@dataclass(frozen=True)
class PascalProgram:
    name: str
    constants: Tuple[ConstDeclaration, ...]
    variables: Tuple[VarDeclaration, ...]
    body: CompoundStatement
    types: Tuple[TypeDeclaration, ...] = ()
    methods: Tuple[MethodImplementation, ...] = ()
    external_routines: Tuple[ExternalRoutineDeclaration, ...] = ()
    unit_assembly_files: Tuple[str, ...] = ()


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
    """Wandelt den ANTLR-Parsebaum in einen kleinen, typfreien AST um."""

    def visitCompilationUnit(self, ctx):
        return self.visit(ctx.programUnit())

    def visitProgramUnit(self, ctx):
        constants, types, variables, methods, body = self.visit(ctx.block())
        return PascalProgram(
            name=ctx.IDENTIFIER().getText(),
            constants=tuple(constants),
            variables=tuple(variables),
            body=body,
            types=tuple(types),
            methods=tuple(methods),
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
        return (
            constants,
            types,
            variables,
            methods,
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
        return TypeDeclaration(
            ctx.IDENTIFIER().getText(),
            self.visit(ctx.typeSpecification()),
            _position(ctx),
        )

    def visitTypeSpecification(self, ctx):
        for child_name in (
            "typeIdentifier",
            "enumType",
            "recordType",
            "arrayType",
            "setType",
            "classType",
        ):
            getter = getattr(ctx, child_name, None)
            if getter is None:
                continue
            child = getter()
            if child is not None:
                if child_name == "typeIdentifier":
                    return NamedTypeSpecification(
                        _position(ctx),
                        child.getText().casefold(),
                    )
                return self.visit(child)
        raise C64PascalError("Interner Fehler: leere Typdefinition.")

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

    def visitSetType(self, ctx):
        return SetTypeSpecification(
            _position(ctx),
            ctx.typeIdentifier().getText().casefold(),
        )

    def visitClassType(self, ctx):
        fields = []
        methods = []
        properties = []
        current_visibility = "public"
        for member in ctx.classMember():
            if member.visibilitySpecifier():
                current_visibility = member.visibilitySpecifier().getText().casefold()
            elif member.fieldDeclaration():
                fields.append(
                    replace(
                        self.visit(member.fieldDeclaration()),
                        visibility=current_visibility,
                    )
                )
            elif member.methodDeclaration():
                methods.append(
                    replace(
                        self.visit(member.methodDeclaration()),
                        visibility=current_visibility,
                    )
                )
            elif hasattr(member, "propertyDeclaration") and member.propertyDeclaration():
                properties.append(
                    replace(
                        self.visit(member.propertyDeclaration()),
                        visibility=current_visibility,
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

    def visitFieldDeclaration(self, ctx):
        return FieldDeclaration(
            tuple(token.getText() for token in ctx.identifierList().IDENTIFIER()),
            ctx.typeIdentifier().getText().casefold(),
            _position(ctx),
        )

    def visitMethodDeclaration(self, ctx):
        directives = []
        if hasattr(ctx, "methodDirective"):
            directives = [item.getText().casefold() for item in ctx.methodDirective()]
        return MethodDeclaration(
            ctx.routineKind().getText().casefold(),
            ctx.IDENTIFIER().getText(),
            tuple(self.visit(ctx.formalParameters())) if ctx.formalParameters() else (),
            ctx.typeIdentifier().getText().casefold() if ctx.typeIdentifier() else None,
            _position(ctx),
            is_virtual=("virtual;" in directives or "override;" in directives),
            is_override=("override;" in directives),
        )

    def visitPropertyDeclaration(self, ctx):
        read_name = None
        write_name = None
        for accessor in ctx.propertyAccessor():
            text = accessor.getText()
            identifier = accessor.IDENTIFIER().getText()
            if text.casefold().startswith("read"):
                read_name = identifier
            elif text.casefold().startswith("write"):
                write_name = identifier
        return PropertyDeclaration(
            ctx.IDENTIFIER().getText(),
            ctx.typeIdentifier().getText().casefold(),
            read_name,
            write_name,
            _position(ctx),
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

    @staticmethod
    def _try_marker(statement):
        if not isinstance(statement, CallStatement) or statement.arguments:
            return None
        designator = statement.designator
        if isinstance(designator, DesignatorExpression):
            if designator.selectors:
                return None
            name = designator.name
        else:
            name = str(designator)
        match = re.fullmatch(
            r"__pas_try_(begin|finally|except|end)_(\d+)",
            name,
            re.IGNORECASE,
        )
        if match is None:
            return None
        return match.group(1).casefold(), int(match.group(2))

    @staticmethod
    def _except_on_marker(statement):
        if not isinstance(statement, CallStatement):
            return None
        designator = statement.designator
        if not isinstance(designator, DesignatorExpression):
            return None
        if designator.selectors or designator.name.casefold() != "__pas_except_on":
            return None
        if len(statement.arguments) != 2:
            return None
        var_expr, type_expr = statement.arguments
        if not isinstance(var_expr, LiteralExpression) or not isinstance(var_expr.value, str):
            return None
        if not isinstance(type_expr, LiteralExpression) or not isinstance(type_expr.value, str):
            return None
        return var_expr.value, type_expr.value

    def _build_except_statement(self, position, try_body, branch_body):
        statements = list(branch_body.statements) if isinstance(branch_body, CompoundStatement) else [branch_body]
        if not statements:
            return TryExceptStatement(position, try_body, branch_body)
        if self._except_on_marker(statements[0]) is None:
            return TryExceptStatement(position, try_body, branch_body)

        handlers = []
        index = 0
        while index < len(statements):
            marker = self._except_on_marker(statements[index])
            if marker is None:
                raise C64PascalError(
                    "Nach typisierten EXCEPT-Handlern wird derzeit nur ein weiterer ON-Handler erwartet.",
                    statements[index].position.line,
                    statements[index].position.column - 1,
                )
            if index + 1 >= len(statements):
                raise C64PascalError(
                    "ON-Handler benoetigt eine Anweisung nach DO.",
                    statements[index].position.line,
                    statements[index].position.column - 1,
                )
            variable_name, type_name = marker
            body = statements[index + 1]
            handlers.append(ExceptHandler(variable_name, type_name, body, statements[index].position))
            index += 2
        return TryExceptStatement(position, try_body, None, tuple(handlers))

    def _collapse_compat_try_compound(self, position, statements):
        if len(statements) < 3:
            return None
        start = self._try_marker(statements[0])
        finish = self._try_marker(statements[-1])
        if start is None or finish is None:
            return None
        if start[0] != "begin" or finish != ("end", start[1]):
            return None
        branch_index = None
        branch_kind = None
        for index, statement in enumerate(statements[1:-1], 1):
            marker = self._try_marker(statement)
            if marker is not None and marker[1] == start[1] and marker[0] in {"finally", "except"}:
                branch_index = index
                branch_kind = marker[0]
                break
        if branch_index is None:
            raise C64PascalError(
                "TRY benötigt FINALLY oder EXCEPT.",
                position.line,
                position.column - 1,
            )
        try_body = CompoundStatement(
            statements[0].position,
            tuple(statements[1:branch_index]),
        )
        branch_body = CompoundStatement(
            statements[branch_index].position,
            tuple(statements[branch_index + 1:-1]),
        )
        if branch_kind == "finally":
            return TryFinallyStatement(position, try_body, branch_body)
        return self._build_except_statement(position, try_body, branch_body)

    def visitCompoundStatement(self, ctx):
        statements = self.visit(ctx.statementSequence()) if ctx.statementSequence() else []
        collapsed = self._collapse_compat_try_compound(_position(ctx), statements)
        if collapsed is not None:
            return collapsed
        return CompoundStatement(_position(ctx), tuple(statements))

    def visitStatementSequence(self, ctx):
        return [self.visit(item) for item in ctx.statement()]

    # Diese beiden Visitor werden verwendet, sobald die .g4-Dateien neu mit
    # ANTLR 4.13.2 erzeugt wurden. Bis dahin übernimmt die Marker-
    # Kompatibilitätsschicht dieselbe AST-Struktur.
    def visitTryStatementNode(self, ctx):
        return self.visit(ctx.tryStatement())

    def visitTryStatement(self, ctx):
        try_body = self.visit(ctx.tryBody())
        if ctx.FINALLY():
            return TryFinallyStatement(
                _position(ctx),
                try_body,
                self.visit(ctx.finallyBody()),
            )
        except_body = self.visit(ctx.exceptBody())
        if isinstance(except_body, tuple) and all(isinstance(item, ExceptHandler) for item in except_body):
            return TryExceptStatement(_position(ctx), try_body, None, except_body)
        return TryExceptStatement(_position(ctx), try_body, except_body)

    def visitTryBody(self, ctx):
        statements = self.visit(ctx.statementSequence()) if ctx.statementSequence() else []
        return CompoundStatement(_position(ctx), tuple(statements))

    def visitFinallyBody(self, ctx):
        statements = self.visit(ctx.statementSequence()) if ctx.statementSequence() else []
        return CompoundStatement(_position(ctx), tuple(statements))

    def visitExceptBody(self, ctx):
        if hasattr(ctx, "exceptionHandler") and ctx.exceptionHandler():
            return tuple(self.visit(item) for item in ctx.exceptionHandler())
        statements = self.visit(ctx.statementSequence()) if ctx.statementSequence() else []
        return CompoundStatement(_position(ctx), tuple(statements))

    def visitExceptionHandler(self, ctx):
        return ExceptHandler(
            ctx.IDENTIFIER().getText(),
            ctx.typeIdentifier().getText(),
            self.visit(ctx.statement()),
            _position(ctx),
        )

    def visitCompoundStatementNode(self, ctx):
        return self.visit(ctx.compoundStatement())

    def visitAssignmentStatementNode(self, ctx):
        return self.visit(ctx.assignmentStatement())

    def visitCallStatementNode(self, ctx):
        return self.visit(ctx.callStatement())

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

    # Wird aktiv, sobald die aktualisierten .g4-Dateien neu generiert werden.
    # Die ausgelieferten aelteren Parser erhalten dieselbe Semantik ueber
    # _rewrite_raise_syntax_compat().
    def visitRaiseStatementNode(self, ctx):
        return self.visit(ctx.raiseStatement())

    def visitRaiseStatement(self, ctx):
        position = _position(ctx)
        if ctx.expression() is None:
            return CallStatement(position, DesignatorExpression(position, "__pas_reraise", ()), ())
        expression = self.visit(ctx.expression())
        if (
            isinstance(expression, CallExpression)
            and isinstance(expression.designator, DesignatorExpression)
            and len(expression.designator.selectors) == 1
            and isinstance(expression.designator.selectors[0], FieldSelector)
            and expression.designator.selectors[0].name.casefold() == "create"
            and len(expression.arguments) == 1
        ):
            class_name = expression.designator.name
            return CallStatement(
                position,
                DesignatorExpression(position, "__pas_raise_class", ()),
                (LiteralExpression(position, class_name), expression.arguments[0]),
            )
        return CallStatement(
            position,
            DesignatorExpression(position, "__pas_raise", ()),
            (expression,),
        )

    def visitAssignmentStatement(self, ctx):
        return AssignmentStatement(
            _position(ctx),
            self.visit(ctx.designator()),
            self.visit(ctx.expression()),
        )

    def visitCallStatement(self, ctx):
        arguments = self.visit(ctx.argumentList()) if ctx.argumentList() else []
        return CallStatement(
            _position(ctx),
            self.visit(ctx.designator()),
            tuple(arguments),
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
            if suffix.DOT():
                selectors.append(
                    FieldSelector(_position(suffix), suffix.IDENTIFIER().getText())
                )
            else:
                selectors.append(
                    IndexSelector(_position(suffix), self.visit(suffix.expression()))
                )
        return DesignatorExpression(
            _position(ctx),
            ctx.IDENTIFIER().getText(),
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
        if hasattr(ctx, "IN") and ctx.IN():
            operands = ctx.additiveExpression()
            return CallExpression(
                _position(ctx),
                "SetContains",
                (self.visit(operands[1]), self.visit(operands[0])),
            )
        return self._fold_binary(ctx)

    def visitAdditiveExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitMultiplicativeExpression(self, ctx):
        return self._fold_binary(ctx)

    def visitUnaryExpression(self, ctx):
        if ctx.primaryExpression():
            return self.visit(ctx.primaryExpression())
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
        if hasattr(ctx, "setConstructor") and ctx.setConstructor():
            return self.visit(ctx.setConstructor())
        if ctx.STRING_LITERAL():
            text = ctx.STRING_LITERAL().getText()[1:-1].replace("''", "'")
            return LiteralExpression(position, text)
        if ctx.TRUE():
            return LiteralExpression(position, True)
        if ctx.FALSE():
            return LiteralExpression(position, False)
        if hasattr(ctx, "NIL") and ctx.NIL():
            return DesignatorExpression(position, "nil", ())
        if ctx.designator():
            designator = self.visit(ctx.designator())
            if ctx.LPAREN():
                arguments = self.visit(ctx.argumentList()) if ctx.argumentList() else []
                return CallExpression(position, designator, tuple(arguments))
            return designator
        return self.visit(ctx.expression())


    def visitSetConstructor(self, ctx):
        position = _position(ctx)
        if ctx.setElementList() is None:
            return CallExpression(position, "EmptySet", ())
        terms = [self.visit(item) for item in ctx.setElementList().setElement()]
        if len(terms) == 1:
            return terms[0]
        return CallExpression(position, "SetUnion", tuple(terms))

    def visitSetElement(self, ctx):
        expressions = ctx.additiveExpression()
        if len(expressions) == 1:
            return CallExpression(
                _position(ctx),
                "SetOf",
                (self.visit(expressions[0]),),
            )
        return CallExpression(
            _position(ctx),
            "SetRange",
            (self.visit(expressions[0]), self.visit(expressions[1])),
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
    ) -> None:
        self.macros: Dict[str, str] = {}
        self.notes: List[PascalPreprocessorDiagnostic] = []
        self.warnings: List[PascalPreprocessorDiagnostic] = []
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



def _rewrite_except_on_syntax_compat(source: str) -> str:
    """Uebersetzt ``on E: EType do`` fuer alte generierte ANTLR-Dateien.

    Der Marker bleibt eine normale Pascal-Anweisung und wird spaeter vom
    AstBuilder in einen ExceptHandler umgewandelt. Dadurch bleiben Variable,
    Typ und Handler-Body getrennte semantische Elemente.
    """
    if hasattr(C64PascalLexer, "ON"):
        return source
    mask = _pascal_code_mask(source)
    pattern = re.compile(
        r"\bon\s+(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*"
        r"(?P<type>[A-Za-z_][A-Za-z0-9_]*)\s+do\b",
        re.IGNORECASE,
    )
    replacements = []
    for match in pattern.finditer(mask):
        variable_name = source[match.start("var"):match.end("var")]
        type_name = source[match.start("type"):match.end("type")]
        replacement = f"__pas_except_on('{variable_name}', '{type_name}');"
        replacements.append((match.start(), match.end(), replacement))
    for start, end, replacement in reversed(replacements):
        source = source[:start] + replacement + source[end:]
    return source


def _rewrite_try_syntax_compat(source: str) -> str:
    """Schreibt TRY..FINALLY/EXCEPT fuer alte generierte Parser in Marker-Bloecke um.

    Die Transformation behaelt alle Zeilen bei. Der AstBuilder erkennt die
    Marker wieder und erzeugt echte TryFinallyStatement/TryExceptStatement-
    Knoten. Strings und Kommentare werden ueber _pascal_code_mask ignoriert.
    """
    if hasattr(C64PascalLexer, "TRY"):
        return source

    mask = _pascal_code_mask(source)
    token_pattern = re.compile(
        r"\b(begin|record|class|case|try|finally|except|end)\b",
        re.IGNORECASE,
    )
    stack = []
    replacements = []
    try_counter = 0

    for match in token_pattern.finditer(mask):
        word = match.group(1).casefold()
        if word in {"begin", "record", "class", "case"}:
            stack.append((word, None))
            continue
        if word == "try":
            try_counter += 1
            stack.append(("try", try_counter))
            replacements.append(
                (match.start(), match.end(), f"begin __pas_try_begin_{try_counter};")
            )
            continue
        if word in {"finally", "except"}:
            if not stack or stack[-1][0] != "try":
                continue
            try_id = stack[-1][1]
            replacements.append(
                (match.start(), match.end(), f"__pas_try_{word}_{try_id};")
            )
            continue
        if word == "end" and stack:
            kind, try_id = stack.pop()
            if kind == "try":
                replacements.append(
                    (match.start(), match.end(), f"__pas_try_end_{try_id}; end")
                )

    for start, end, replacement in reversed(replacements):
        source = source[:start] + replacement + source[end:]
    return source



def _rewrite_raise_syntax_compat(source: str) -> str:
    """Uebersetzt Pascal RAISE fuer die ausgelieferten alten ANTLR-Dateien.

    Unterstuetzt werden zunaechst die fuer die Runtime wichtigen Formen::

        raise Exception.Create('message');
        raise 'message';
        raise;                    { re-raise }

    Der echte Lexer/Parser besitzt parallel dazu eine RAISE-Regel. Bis die
    generierten Dateien aktualisiert sind, werden interne Builtins verwendet.
    Strings und Kommentare werden mit _pascal_code_mask geschuetzt.
    """
    if hasattr(C64PascalLexer, "RAISE"):
        return source
    mask = _pascal_code_mask(source)
    pattern = re.compile(r"\braise\b(?P<body>[^;]*);", re.IGNORECASE)
    replacements = []
    for match in pattern.finditer(mask):
        raw_body = source[match.start("body"):match.end("body")].strip()
        if not raw_body:
            replacement = "__pas_reraise;"
        else:
            create = re.fullmatch(
                r"(?P<class>[A-Za-z_][A-Za-z0-9_]*)\s*\.\s*Create\s*\((?P<message>.*)\)\s*",
                raw_body,
                re.IGNORECASE | re.DOTALL,
            )
            if create is not None:
                class_name = create.group("class")
                message = create.group("message").strip()
                replacement = f"__pas_raise_class('{class_name}', {message});"
            else:
                replacement = f"__pas_raise({raw_body});"
        replacements.append((match.start(), match.end(), replacement))
    for start, end, replacement in reversed(replacements):
        source = source[:start] + replacement + source[end:]
    return source


def _normalize_late_global_declarations(source: str) -> str:
    """Erlaubt globale CONST/TYPE/VAR-Abschnitte nach Methodenimplementierungen.

    Die ausgelieferten generierten Parser erwarten alle globalen Abschnitte vor
    der ersten ``TClass.Method``-Implementierung. Nur fuer diesen alten Parser
    werden spaete globale Abschnitte im Parsertext nach vorn verschoben. Lokale
    VAR-Abschnitte einer Methode bleiben dabei an ihrer Stelle.
    """
    mask = _pascal_code_mask(source)
    word_pattern = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
    opener_words = {"begin", "record", "class", "case", "try"}
    section_words = {"const", "type", "var"}

    # Alle Woerter, die unmittelbar auf Programmebene liegen. BEGIN-Woerter
    # von Methoden sind hier ebenfalls enthalten; der letzte Top-Level-BEGIN
    # ist bei der unterstuetzten PROGRAM-Grammatik der eigentliche Hauptblock.
    stack = []
    top_words = []
    for match in word_pattern.finditer(mask):
        word = match.group(0).casefold()
        if word == "end":
            if stack:
                stack.pop()
            continue
        if not stack:
            top_words.append((match.start(), match.end(), word))
        if word in opener_words:
            stack.append(word)

    body_candidates = [item for item in top_words if item[2] == "begin"]
    if not body_candidates:
        return source
    main_begin = body_candidates[-1][0]

    method_pattern = re.compile(
        r"\b(?:procedure|function|constructor|destructor)\s+"
        r"[A-Za-z_][A-Za-z0-9_]*\s*\.\s*"
        r"[A-Za-z_][A-Za-z0-9_]*\b",
        re.IGNORECASE,
    )
    method_starts = [m.start() for m in method_pattern.finditer(mask[:main_begin])]
    if not method_starts:
        return source
    first_method_start = min(method_starts)

    # Ermittelt komplette Implementierungsbereiche, damit z.B.
    #   procedure T.Foo; var x: Integer; begin ... end;
    # keinen scheinbar globalen VAR-Abschnitt erzeugt.
    method_ranges = []
    block_token = re.compile(r"\b(begin|end)\b", re.IGNORECASE)
    for method_start in method_starts:
        body_match = re.search(r"\bbegin\b", mask[method_start:main_begin], re.IGNORECASE)
        if body_match is None:
            continue
        body_start = method_start + body_match.start()
        depth = 0
        method_end = main_begin
        for token in block_token.finditer(mask, body_start, main_begin):
            if token.group(1).casefold() == "begin":
                depth += 1
            else:
                depth -= 1
                if depth == 0:
                    method_end = token.end()
                    semi = mask.find(";", method_end, min(main_begin, method_end + 8))
                    if semi >= 0:
                        method_end = semi + 1
                    break
        method_ranges.append((method_start, method_end))

    def inside_method(offset: int) -> bool:
        return any(start <= offset < end for start, end in method_ranges)

    # Nur echte Top-Level-Abschnittswoerter nach der ersten Methode sammeln.
    section_starts = [
        start
        for start, unused_end, word in top_words
        if first_method_start < start < main_begin
        and word in section_words
        and not inside_method(start)
    ]
    if not section_starts:
        return source

    # Grenzen: naechster globaler Abschnitt, naechste Methode oder Haupt-BEGIN.
    boundaries = sorted(
        set(section_starts + [x for x in method_starts if x > first_method_start] + [main_begin])
    )
    spans = []
    for section_start in section_starts:
        end = next((value for value in boundaries if value > section_start), main_begin)
        spans.append((section_start, end))

    # Ueberlappende/duplizierte Spannen zusammenfassen.
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    moved = "".join(source[start:end] for start, end in merged)
    characters = list(source)
    for start, end in merged:
        characters[start:end] = list(_blank_preserving_lines(source[start:end]))
    blanked = "".join(characters)
    return blanked[:first_method_start] + moved + blanked[first_method_start:]


@dataclass
class _PascalSyntaxExtensions:
    set_types: Dict[str, Tuple[str, SourcePosition]] = field(default_factory=dict)
    properties: Dict[str, List[PropertyDeclaration]] = field(default_factory=dict)
    method_flags: Dict[Tuple[str, str], Tuple[bool, bool]] = field(default_factory=dict)


def _source_position_from_offset(source: str, offset: int) -> SourcePosition:
    line = source.count("\n", 0, offset) + 1
    previous_newline = source.rfind("\n", 0, offset)
    column = offset + 1 if previous_newline < 0 else offset - previous_newline
    return SourcePosition(line, column)


def _blank_preserving_lines(text: str) -> str:
    return "".join("\n" if character == "\n" else " " for character in text)


def _split_pascal_list(text: str) -> List[str]:
    result: List[str] = []
    start = 0
    depth = 0
    in_string = False
    index = 0
    while index < len(text):
        character = text[index]
        if character == "'":
            if in_string and index + 1 < len(text) and text[index + 1] == "'":
                index += 2
                continue
            in_string = not in_string
        elif not in_string:
            if character == "(":
                depth += 1
            elif character == ")" and depth:
                depth -= 1
            elif character == "," and depth == 0:
                result.append(text[start:index].strip())
                start = index + 1
        index += 1
    result.append(text[start:].strip())
    return [item for item in result if item]


def _rewrite_set_literals(source: str) -> str:
    """Schreibt Pascal-Set-Konstruktoren in interne Builtin-Aufrufe um.

    Die vorhandenen generierten ANTLR-Dateien kennen ``[A, B]`` nur als
    Arrayindex-Syntax. Die Umschreibung erfolgt deshalb ausschließlich an
    Stellen, an denen die eckige Klammer nicht direkt auf einen Designator
    folgt. Zeilennummern bleiben unverändert.
    """
    mask = _pascal_code_mask(source)
    replacements: List[Tuple[int, int, str]] = []
    index = 0
    while index < len(mask):
        if mask[index] != "[":
            index += 1
            continue
        previous = index - 1
        while previous >= 0 and mask[previous].isspace():
            previous -= 1
        if previous >= 0 and (mask[previous].isalnum() or mask[previous] in "_)]"):
            index += 1
            continue
        depth = 1
        end = index + 1
        while end < len(mask) and depth:
            if mask[end] == "[":
                depth += 1
            elif mask[end] == "]":
                depth -= 1
            end += 1
        if depth:
            index += 1
            continue
        content = source[index + 1:end - 1].strip()
        if not content:
            replacement = "EmptySet()"
        else:
            terms: List[str] = []
            for item in _split_pascal_list(content):
                range_parts = item.split("..", 1)
                if len(range_parts) == 2:
                    terms.append(
                        f"SetRange({range_parts[0].strip()}, {range_parts[1].strip()})"
                    )
                else:
                    terms.append(f"SetOf({item})")
            replacement = terms[0] if len(terms) == 1 else f"SetUnion({', '.join(terms)})"
        replacements.append((index, end, replacement))
        index = end
    for start, end, replacement in reversed(replacements):
        source = source[:start] + replacement + source[end:]
    return source


def _rewrite_set_membership(source: str) -> str:
    """Unterstützt die übliche einfache Pascal-Form ``Value in SetVar``."""
    pattern = re.compile(
        r"(?P<left>\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)"
        r"\s+in\s+"
        r"(?P<right>(?:[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*|\[[^\]\r\n]*\]))",
        re.IGNORECASE,
    )
    # Nur Codebereiche ersetzen. Kommentare/Strings werden über den Maskencheck
    # ausgeschlossen. Mehrere Membership-Ausdrücke werden von rechts nach links
    # ersetzt, damit Offsets stabil bleiben.
    while True:
        mask = _pascal_code_mask(source)
        matches = [match for match in pattern.finditer(mask)]
        if not matches:
            return source
        changed = False
        for match in reversed(matches):
            original = source[match.start():match.end()]
            visible = _pascal_code_mask(original)
            local = pattern.fullmatch(visible)
            if local is None:
                continue
            left = source[match.start("left"):match.end("left")]
            right = source[match.start("right"):match.end("right")]
            source = source[:match.start()] + f"SetContains({right}, {left})" + source[match.end():]
            changed = True
        if not changed:
            return source


def _normalize_pascal_oop_extensions(
    source: str,
) -> Tuple[str, _PascalSyntaxExtensions]:
    extensions = _PascalSyntaxExtensions()
    original = source
    mask = _pascal_code_mask(source)
    characters = list(source)

    # SET OF wird semantisch als eigener Typ zurückgespeichert. Für den alten
    # Parser steht währenddessen ein gleichzeiliger Integer-Alias im Text.
    set_pattern = re.compile(
        r"\b(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
        r"set\s+of\s+(?P<element>[A-Za-z_][A-Za-z0-9_]*)\s*;",
        re.IGNORECASE,
    )
    for match in set_pattern.finditer(mask):
        name = original[match.start("name"):match.end("name")]
        element = original[match.start("element"):match.end("element")]
        extensions.set_types[name.casefold()] = (
            element,
            _source_position_from_offset(original, match.start()),
        )
        start = match.start("element")
        prefix_start = mask.rfind("set", match.start(), start)
        if prefix_start < 0:
            continue
        replacement = "integer"
        span_end = match.end("element")
        span = span_end - prefix_start
        text = replacement + " " * max(0, span - len(replacement))
        characters[prefix_start:span_end] = list(text[:span])

    # Klassenblöcke: Property-Zeilen entfernen und Direktiven hinter Methoden
    # erfassen. PRIVATE/PROTECTED/PUBLIC/PUBLISHED bleiben im Parsertext und
    # werden vom AstBuilder verarbeitet.
    class_pattern = re.compile(
        r"\b(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*class\b"
        r"(?:\s*\([^)]*\))?(?P<body>.*?)\bend\s*;",
        re.IGNORECASE | re.DOTALL,
    )
    for class_match in class_pattern.finditer(mask):
        class_name = original[class_match.start("name"):class_match.end("name")]
        body_start, body_end = class_match.span("body")
        body_mask = mask[body_start:body_end]

        def visibility_at(local_offset: int) -> str:
            visibility = "public"
            for item in re.finditer(
                r"\b(private|protected|public|published)\b",
                body_mask[:local_offset],
                re.IGNORECASE,
            ):
                visibility = item.group(1).casefold()
            return visibility

        property_pattern = re.compile(
            r"\bproperty\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*"
            r"(?P<type>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<accessors>[^;]*);",
            re.IGNORECASE,
        )
        for prop_match in property_pattern.finditer(body_mask):
            absolute_start = body_start + prop_match.start()
            prop_name = original[
                body_start + prop_match.start("name"):
                body_start + prop_match.end("name")
            ]
            type_name = original[
                body_start + prop_match.start("type"):
                body_start + prop_match.end("type")
            ]
            accessor_text = original[
                body_start + prop_match.start("accessors"):
                body_start + prop_match.end("accessors")
            ]
            read_match = re.search(
                r"\bread\s+([A-Za-z_][A-Za-z0-9_]*)",
                accessor_text,
                re.IGNORECASE,
            )
            write_match = re.search(
                r"\bwrite\s+([A-Za-z_][A-Za-z0-9_]*)",
                accessor_text,
                re.IGNORECASE,
            )
            if read_match is None and write_match is None:
                raise C64PascalError(
                    f"Property {class_name}.{prop_name} benötigt READ und/oder WRITE.",
                    _source_position_from_offset(original, absolute_start).line,
                    _source_position_from_offset(original, absolute_start).column - 1,
                )
            extensions.properties.setdefault(class_name.casefold(), []).append(
                PropertyDeclaration(
                    prop_name,
                    type_name.casefold(),
                    read_match.group(1) if read_match else None,
                    write_match.group(1) if write_match else None,
                    _source_position_from_offset(original, absolute_start),
                    visibility_at(prop_match.start()),
                )
            )
            absolute_end = body_start + prop_match.end()
            blank = _blank_preserving_lines(original[absolute_start:absolute_end])
            characters[absolute_start:absolute_end] = list(blank)

        method_pattern = re.compile(
            r"\b(?:procedure|function|constructor|destructor)\s+"
            r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*"
            r"(?:\([^)]*\))?\s*(?::\s*[A-Za-z_][A-Za-z0-9_]*)?\s*;"
            r"(?P<directives>(?:\s*(?:virtual|override)\s*;)+)",
            re.IGNORECASE,
        )
        for method_match in method_pattern.finditer(body_mask):
            method_name = original[
                body_start + method_match.start("name"):
                body_start + method_match.end("name")
            ]
            directives_start = body_start + method_match.start("directives")
            directives_end = body_start + method_match.end("directives")
            directives = original[directives_start:directives_end].casefold()
            is_virtual = bool(re.search(r"\bvirtual\b", directives))
            is_override = bool(re.search(r"\boverride\b", directives))
            extensions.method_flags[(class_name.casefold(), method_name.casefold())] = (
                is_virtual,
                is_override,
            )
            blank = _blank_preserving_lines(original[directives_start:directives_end])
            characters[directives_start:directives_end] = list(blank)

    normalized = "".join(characters)
    # Membership wird zuerst umgeschrieben, damit auch typische Ausdrücke wie
    # ``Red in [Red, Blue]`` in einen SetContains-Aufruf überführt werden.
    # Anschließend wandelt der Literal-Pass die verbliebenen []-Konstruktoren um.
    normalized = _rewrite_set_membership(normalized)
    normalized = _rewrite_set_literals(normalized)
    return normalized, extensions


def _apply_pascal_syntax_extensions(
    program: PascalProgram,
    extensions: _PascalSyntaxExtensions,
) -> PascalProgram:
    declarations: List[TypeDeclaration] = []
    for declaration in program.types:
        key = declaration.name.casefold()
        specification = declaration.specification
        set_info = extensions.set_types.get(key)
        if set_info is not None:
            element_name, position = set_info
            specification = SetTypeSpecification(position, element_name.casefold())
        elif isinstance(specification, ClassTypeSpecification):
            methods = []
            for method in specification.methods:
                flags = extensions.method_flags.get(
                    (key, method.name.casefold()),
                    (False, False),
                )
                methods.append(
                    replace(
                        method,
                        is_virtual=bool(flags[0] or flags[1]),
                        is_override=bool(flags[1]),
                    )
                )
            specification = replace(
                specification,
                methods=tuple(methods),
                properties=tuple(extensions.properties.get(key, ())),
            )
        declarations.append(replace(declaration, specification=specification))
    return replace(program, types=tuple(declarations))


def _parse_pascal_program(source: str) -> PascalProgram:
    parser_source, extensions = _normalize_pascal_oop_extensions(source)
    parser_source = _rewrite_except_on_syntax_compat(parser_source)
    parser_source = _rewrite_try_syntax_compat(parser_source)
    parser_source = _rewrite_raise_syntax_compat(parser_source)
    parser_source = _normalize_late_global_declarations(parser_source)
    listener = _RaisingErrorListener()
    lexer = C64PascalLexer(InputStream(parser_source))
    lexer.removeErrorListeners()
    lexer.addErrorListener(listener)
    parser = C64PascalParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(listener)
    tree = parser.compilationUnit()
    return _apply_pascal_syntax_extensions(_AstBuilder().visit(tree), extensions)


def _find_unit_file(unit_name: str, search_paths: Sequence[Path]) -> Optional[Path]:
    return _find_unit_artifact(unit_name, search_paths, (".pas", ".pp"))


def _find_unit_artifact(
    unit_name: str,
    search_paths: Sequence[Path],
    suffixes: Sequence[str],
) -> Optional[Path]:
    relative_names = []
    dotted = unit_name.replace(".", "/")
    for stem in (dotted, unit_name, unit_name.split(".")[-1]):
        for suffix in suffixes:
            candidate = f"{stem}{suffix}"
            if candidate not in relative_names:
                relative_names.append(candidate)

    for directory in search_paths:
        for relative_name in relative_names:
            candidate = (directory / relative_name).resolve()
            if candidate.is_file():
                return candidate

    wanted = {
        Path(name).name.casefold()
        for name in relative_names
        if "/" not in name
    }
    for directory in search_paths:
        try:
            for candidate in directory.iterdir():
                if candidate.is_file() and candidate.name.casefold() in wanted:
                    return candidate.resolve()
        except OSError:
            continue
    return None


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
    transformed = (
        f"program __unit_{safe_name};\n"
        + cleaned_interface
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


_PUI_FORMAT = "d64pascal-pui"
_PUI_VERSION = 2


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
    r"(?ims)^\s*(procedure|function)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*"
    r"(?:\((.*?)\))?\s*"
    r"(?:\:\s*([A-Za-z_][A-Za-z0-9_.]*))?\s*;"
)


def _pui_parameter_information(text: str) -> List[Dict[str, object]]:
    result: List[Dict[str, object]] = []
    for group in filter(None, (item.strip() for item in text.split(';'))):
        match = re.fullmatch(
            r"(?is)(?:(const|var)\s+)?"
            r"([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)"
            r"\s*:\s*([A-Za-z_][A-Za-z0-9_.]*)",
            group,
        )
        if match is None:
            raise C64PascalError(f"Ungültige PUI-Parameterdeklaration: {group}.")
        modifier = (match.group(1) or 'value').casefold()
        type_name = match.group(3)
        for name in match.group(2).split(','):
            result.append({
                'name': name.strip(),
                'type': type_name,
                'modifier': modifier,
            })
    return result


def _pui_routine_information(
    unit_name: str,
    interface_source: str,
) -> Tuple[str, List[Dict[str, object]]]:
    routines: List[Dict[str, object]] = []
    safe_unit = re.sub(r"[^A-Za-z0-9_]", "_", unit_name)

    # Globale Unit-Routinen muessen fuer den kleinen PROGRAM-Parser weiterhin
    # ausgeblendet werden. Methoden innerhalb einer CLASS-Deklaration duerfen
    # dabei aber nicht als globale PUI-Routinen missverstanden werden.
    code_mask = _pascal_code_mask(interface_source)
    class_ranges = [
        match.span()
        for match in re.finditer(
            r"\b[A-Za-z_][A-Za-z0-9_]*\s*=\s*class\b"
            r"(?:\s*\([^)]*\))?.*?\bend\s*;",
            code_mask,
            re.IGNORECASE | re.DOTALL,
        )
    ]

    def inside_class(offset: int) -> bool:
        return any(start <= offset < end for start, end in class_ranges)

    def replace_routine(match: re.Match[str]) -> str:
        if inside_class(match.start()):
            return match.group(0)
        kind = match.group(1).casefold()
        name = match.group(2)
        parameters = _pui_parameter_information(match.group(3) or '')
        result_type = match.group(4) if kind == 'function' else None
        routines.append({
            'kind': kind,
            'name': name,
            'parameters': parameters,
            'result_type': result_type,
            'symbol': f"__pas_{safe_unit}_{name}",
        })
        # Die aktuelle ANTLR-Grammatik kennt noch keine globalen
        # Routinedeklarationen. Für die Typ-/Konstantenanalyse wird die
        # Deklaration deshalb durch Leerzeilen ersetzt; die vollständige
        # Signatur bleibt strukturiert in der PUI erhalten.
        return ''.join('\n' if char == '\n' else ' ' for char in match.group(0))

    parser_source = _PUI_ROUTINE_RE.sub(replace_routine, interface_source)
    return parser_source, routines


def _pui_symbol_information(
    program: PascalProgram,
    routines: Sequence[Dict[str, object]] = (),
) -> Dict[str, object]:
    return {
        "constants": [item.name for item in program.constants],
        "types": [item.name for item in program.types],
        "variables": [name for item in program.variables for name in item.names],
        "methods": [item.class_name + "." + item.name for item in program.methods],
        "routines": [str(item["name"]) for item in routines],
    }


def _unit_implementation_information(
    source_path: Optional[Path],
) -> Dict[str, str]:
    """Findet getrennt assemblierbare Zielmodule neben einer Pascal-Unit."""
    if source_path is None:
        return {}
    result: Dict[str, str] = {}
    for target, suffix in (("c64", ".c64.asm"), ("amiga", ".amiga.asm")):
        candidate = source_path.with_name(source_path.stem + suffix)
        if candidate.is_file():
            result[target] = candidate.name
    return result


def _unit_c_implementation_information(
    source_path: Optional[Path],
) -> Dict[str, str]:
    """Findet getrennt kompilierbare C-Zielmodule neben einer Pascal-Unit."""
    if source_path is None:
        return {}
    result: Dict[str, str] = {}
    for target, suffix in (("c64", ".c64.c"), ("amiga", ".amiga.c")):
        candidate = source_path.with_name(source_path.stem + suffix)
        if candidate.is_file():
            result[target] = candidate.name
    return result


def _pui_document(
    *,
    unit_name: str,
    interface_source: str,
    interface_units: Sequence[str],
    source_path: Optional[Path],
    guard: Optional[str] = None,
) -> Dict[str, object]:
    safe_name = re.sub(r"[^A-Za-z0-9_]", "_", unit_name)
    parser_source, routines = _pui_routine_information(unit_name, interface_source)
    interface_program = _parse_pascal_program(
        f"program __pui_{safe_name};\n{parser_source}\nbegin\nend.\n"
    )
    source_hash = None
    if source_path is not None and source_path.is_file():
        source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    return {
        "format": _PUI_FORMAT,
        "version": _PUI_VERSION,
        "unit": unit_name,
        "guard": guard,
        "interface": {
            "source": parser_source,
            "declaration_source": interface_source,
            "uses": list(interface_units),
            "symbols": _pui_symbol_information(interface_program, routines),
            "routines": routines,
        },
        "source": {
            "file": source_path.name if source_path is not None else None,
            "sha256": source_hash,
        },
        "implementation": {
            "assembly": _unit_implementation_information(source_path),
            "c": _unit_c_implementation_information(source_path),
        },
    }


def _write_pui_document(path: Path, document: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    except (OSError, TypeError, ValueError) as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise C64PascalError(f"PUI kann nicht geschrieben werden: {path}: {exc}") from exc


def _read_pui_document(path: Path, expected_unit: str) -> Dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise C64PascalError(f"PUI kann nicht gelesen werden: {path}: {exc}") from exc
    if not isinstance(document, dict) or document.get("format") != _PUI_FORMAT:
        raise C64PascalError(f"Ungültiges PUI-Format: {path}.")
    if document.get("version") != _PUI_VERSION:
        raise C64PascalError(f"Nicht unterstützte PUI-Version in {path}.")
    declared = str(document.get("unit", ""))
    if declared.casefold() != expected_unit.casefold():
        raise C64PascalError(
            f"PUI-Unit {declared or '<leer>'} passt nicht zu USES {expected_unit} ({path})."
        )
    interface = document.get("interface")
    if not isinstance(interface, dict) or not isinstance(interface.get("source"), str):
        raise C64PascalError(f"PUI enthält keinen gültigen Interface-Teil: {path}.")
    uses = interface.get("uses", [])
    if not isinstance(uses, list) or not all(isinstance(item, str) for item in uses):
        raise C64PascalError(f"PUI enthält eine ungültige USES-Liste: {path}.")
    return document


def _pui_external_routines(
    document: Dict[str, object],
) -> Tuple[ExternalRoutineDeclaration, ...]:
    interface = document.get("interface")
    if not isinstance(interface, dict):
        return ()
    raw_routines = interface.get("routines", [])
    if not isinstance(raw_routines, list):
        return ()
    unit_name = str(document.get("unit", ""))
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
        raw_parameters = raw.get("parameters", [])
        if isinstance(raw_parameters, list):
            for item in raw_parameters:
                if not isinstance(item, dict):
                    continue
                parameter_name = str(item.get("name", ""))
                type_name = str(item.get("type", "integer")).casefold()
                modifier = str(item.get("modifier", "value")).casefold()
                if parameter_name:
                    parameters.append(
                        ParameterDeclaration(
                            (parameter_name,),
                            type_name,
                            modifier,
                            position,
                        )
                    )
        result_name = raw.get("result_type")
        result.append(
            ExternalRoutineDeclaration(
                unit_name,
                kind,
                name,
                tuple(parameters),
                str(result_name).casefold() if result_name else None,
                symbol,
            )
        )
    return tuple(result)


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
) -> Path:
    source_path = Path(unit_path).expanduser().resolve()
    try:
        source = source_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise C64PascalError(f"Unit kann nicht gelesen werden: {source_path}: {exc}") from exc
    processed = PascalPreprocessor(predefined_macros).process(
        source,
        filename=str(source_path),
    )
    (
        unused_transformed,
        unit_name,
        interface_units,
        unused_implementation_units,
        interface_source,
        unused_implementation_source,
    ) = _unit_program_source(processed.source, filename=str(source_path))
    destination = (
        Path(pui_path).expanduser().resolve()
        if pui_path is not None
        else source_path.with_suffix(".pui")
    )
    _write_pui_document(
        destination,
        _pui_document(
            unit_name=unit_name,
            interface_source=interface_source,
            interface_units=interface_units,
            source_path=source_path,
            guard=_pascal_guard_macro(source),
        ),
    )
    return destination


class _PascalUnitResolver:
    def __init__(
        self,
        *,
        filename: str,
        include_paths: Iterable[Path | str],
        preprocessor: PascalPreprocessor,
        target: str = "c64",
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
        builtin_units = (Path(__file__).resolve().parent / "units").resolve()
        if builtin_units not in self.search_paths:
            self.search_paths.append(builtin_units)
        current = Path.cwd().resolve()
        if current not in self.search_paths:
            self.search_paths.append(current)
        self.programs: List[PascalProgram] = []
        self.external_routines: List[ExternalRoutineDeclaration] = []
        self.assembly_files: List[str] = []
        self.resolved: Dict[str, Path] = {}
        self.stack: List[str] = []
        self.preprocessor = preprocessor
        self.target = str(target)

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
                guard = document.get("guard")
                if (
                    isinstance(guard, str)
                    and guard.casefold() in self.preprocessor.macros
                ):
                    return
            chain = " -> ".join(self.stack + [key])
            raise C64PascalError(f"Zirkuläre USES-Abhängigkeit: {chain}.")
        pui_path = _find_unit_artifact(unit_name, self.search_paths, (".pui",))
        source_path = _find_unit_file(unit_name, self.search_paths)
        if pui_path is None and source_path is None:
            paths = "\n".join(f"  {path}" for path in self.search_paths)
            raise C64PascalError(
                f"Unit nicht gefunden: {unit_name}.\nDurchsuchte Pfade:\n{paths}"
            )
        self.stack.append(key)
        try:
            source_interface = ""
            source_implementation = ""
            source_interface_units: Tuple[str, ...] = ()
            implementation_units: Tuple[str, ...] = ()
            declared_name = unit_name
            if source_path is not None:
                try:
                    source = source_path.read_text(encoding="utf-8-sig")
                except (OSError, UnicodeError) as exc:
                    raise C64PascalError(
                        f"Unit kann nicht gelesen werden: {source_path}: {exc}"
                    ) from exc
                processed = self.preprocessor.process(source, filename=str(source_path))
                (
                    unused_transformed,
                    declared_name,
                    source_interface_units,
                    implementation_units,
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
                pui_interface = pui_document["interface"]
                interface_source = str(pui_interface["source"])
                interface_units = tuple(str(item) for item in pui_interface["uses"])
            else:
                interface_source = source_interface
                interface_units = source_interface_units
                pui_path = source_path.with_suffix(".pui")
                pui_document = _pui_document(
                    unit_name=declared_name,
                    interface_source=interface_source,
                    interface_units=interface_units,
                    source_path=source_path,
                    guard=_pascal_guard_macro(source),
                )
                _write_pui_document(pui_path, pui_document)

            self.external_routines.extend(_pui_external_routines(pui_document))
            implementation_base = (pui_path or source_path).parent
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
            safe_name = re.sub(r"[^A-Za-z0-9_]", "_", declared_name)
            transformed = (
                f"program __unit_{safe_name};\n"
                + interface_source
                + "\n"
                + source_implementation
                + "\nbegin\nend.\n"
            )
            dependencies = interface_units + implementation_units
            for dependency in dependencies:
                self.resolve(dependency)
            try:
                program = _parse_pascal_program(transformed)
            except C64PascalError as exc:
                raise C64PascalError(f"{pui_path or source_path}: {exc}") from exc
            self.programs.append(program)
            self.resolved[key] = pui_path or source_path
        finally:
            self.stack.pop()


def _parse_pascal_frontend(
    source: str,
    *,
    filename: str = "<Pascal-Editor>",
    include_paths: Iterable[Path | str] = (),
    predefined_macros: Optional[Dict[str, Union[str, int, bool]]] = None,
    target: str = "c64",
) -> Tuple[PascalProgram, PascalPreprocessResult]:
    preprocessor = PascalPreprocessor(predefined_macros)
    root_processed = preprocessor.process(source, filename=filename)
    cleaned_source, unit_names = _extract_program_uses(
        root_processed.source,
        filename=filename,
    )
    main_program = _parse_pascal_program(cleaned_source)
    if not unit_names:
        return main_program, PascalPreprocessResult(
            root_processed.source,
            dict(preprocessor.macros),
            tuple(preprocessor.notes),
            tuple(preprocessor.warnings),
        )

    resolver = _PascalUnitResolver(
        filename=filename,
        include_paths=include_paths,
        preprocessor=preprocessor,
        target=target,
    )
    for unit_name in unit_names:
        resolver.resolve(unit_name)

    constants = []
    types = []
    variables = []
    methods = []
    for unit_program in resolver.programs:
        constants.extend(unit_program.constants)
        types.extend(unit_program.types)
        variables.extend(unit_program.variables)
        methods.extend(unit_program.methods)
    constants.extend(main_program.constants)
    types.extend(main_program.types)
    variables.extend(main_program.variables)
    methods.extend(main_program.methods)
    program = PascalProgram(
        name=main_program.name,
        constants=tuple(constants),
        variables=tuple(variables),
        body=main_program.body,
        types=tuple(types),
        methods=tuple(methods),
        external_routines=tuple(resolver.external_routines),
        unit_assembly_files=tuple(resolver.assembly_files),
    )
    return program, PascalPreprocessResult(
        root_processed.source,
        dict(preprocessor.macros),
        tuple(preprocessor.notes),
        tuple(preprocessor.warnings),
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
    element_type: Optional["_PascalType"] = None
    lower_bound: int = 0
    upper_bound: int = -1
    methods: Dict[str, "_MethodInfo"] = field(default_factory=dict)
    properties: Dict[str, "_PropertyInfo"] = field(default_factory=dict)
    base_type: Optional["_PascalType"] = None
    vmt_methods: List["_MethodInfo"] = field(default_factory=list)
    vmt_label: Optional[str] = None

    @property
    def scalar(self) -> bool:
        return self.kind in {"scalar", "enum", "string", "set"}

    @property
    def aggregate(self) -> bool:
        return self.kind in {"record", "array", "class"}


@dataclass(frozen=True)
class _FieldInfo:
    name: str
    type_info: _PascalType
    offset: int
    position: SourcePosition
    owner: Optional[_PascalType] = None
    visibility: str = "public"


@dataclass(frozen=True)
class _ParameterInfo:
    name: str
    type_info: _PascalType
    modifier: str
    position: SourcePosition


@dataclass(eq=False)
class _MethodInfo:
    owner: _PascalType
    kind: str
    name: str
    parameters: Tuple[_ParameterInfo, ...]
    result_type: Optional[_PascalType]
    position: SourcePosition
    label: str
    visibility: str = "public"
    virtual: bool = False
    override: bool = False
    vmt_slot: Optional[int] = None
    implementation: Optional[MethodImplementation] = None
    parameter_variables: Tuple["_Variable", ...] = ()
    local_variables: Dict[str, "_Variable"] = field(default_factory=dict)
    local_initializers: List[Tuple["_Variable", Expression]] = field(default_factory=list)
    result_variable: Optional["_Variable"] = None


@dataclass(frozen=True)
class _PropertyInfo:
    owner: _PascalType
    name: str
    type_info: _PascalType
    read_name: Optional[str]
    write_name: Optional[str]
    visibility: str
    position: SourcePosition


@dataclass(frozen=True)
class _ExternalRoutineInfo:
    unit_name: str
    kind: str
    name: str
    parameters: Tuple[_ParameterInfo, ...]
    result_type: Optional[_PascalType]
    symbol: str



INTEGER_TYPE = _PascalType("integer", 2, True)
BYTE_TYPE = _PascalType("byte", 1, False)
CHAR_TYPE = _PascalType("char", 1, False)
BOOLEAN_TYPE = _PascalType("boolean", 1, False)
STRING_TYPE = _PascalType("string", 2, False)
UNTYPED_SET_TYPE = _PascalType("$setliteral", 2, False, "set", lower_bound=0, upper_bound=15)
NIL_TYPE = _PascalType("$nil", 4, False, "nil")

_TYPES = {
    item.name: item
    for item in (INTEGER_TYPE, BYTE_TYPE, CHAR_TYPE, BOOLEAN_TYPE, STRING_TYPE)
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
    # PE32 benutzt Klassenvariablen als echte Referenzen. Sobald ein Feld
    # ueber eine Klassenreferenz adressiert wird, muss zuerst der in der
    # Variablen gespeicherte Objektzeiger dereferenziert werden. C64/Amiga
    # ignorieren dieses Flag weiterhin und behalten ihr bisheriges Modell.
    class_deref: bool = False


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
        self.class_types: List[_PascalType] = []
        self.external_routines: Dict[str, _ExternalRoutineInfo] = {}
        self.current_method: Optional[_MethodInfo] = None
        self.scope_variables: Dict[str, _Variable] = {}
        self.strings: Dict[bytes, str] = {}
        self.runtime: set[str] = set()
        self.label_counter = 0
        self.break_targets: List[str] = []
        self.continue_targets: List[str] = []
        self.finally_stack: List[Statement] = []

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

    def _error(self, message: str, position: SourcePosition) -> C64PascalError:
        return C64PascalError(message, position.line, position.column - 1)

    def _class_pointer_size(self) -> int:
        return 2

    def _aggregate_size_limit(self) -> int:
        return 256

    def _target_storage_size(self, type_info: "_PascalType") -> int:
        return int(type_info.size)

    @staticmethod
    def _is_descendant(candidate: Optional["_PascalType"], owner: Optional["_PascalType"]) -> bool:
        current = candidate
        while current is not None:
            if current is owner:
                return True
            current = current.base_type
        return False

    def _member_accessible(self, owner: Optional["_PascalType"], visibility: str) -> bool:
        visibility = str(visibility or "public").casefold()
        if visibility in {"public", "published"}:
            return True
        if self.current_method is None:
            return False
        current_owner = self.current_method.owner
        if visibility == "private":
            return current_owner is owner
        if visibility == "protected":
            return self._is_descendant(current_owner, owner)
        return True

    def _require_member_access(
        self,
        owner: Optional["_PascalType"],
        visibility: str,
        display_name: str,
        position: SourcePosition,
    ) -> None:
        if not self._member_accessible(owner, visibility):
            raise self._error(
                f"{visibility.upper()}-Member ist hier nicht sichtbar: {display_name}.",
                position,
            )

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
            elif isinstance(specification, EnumTypeSpecification):
                if not specification.names:
                    raise self._error("Ein Aufzählungstyp benötigt mindestens einen Wert.", specification.position)
                if len(specification.names) > 256:
                    raise self._error("Ein Aufzählungstyp ist derzeit auf 256 Werte begrenzt.", specification.position)
                type_info = _PascalType(
                    declaration.name,
                    1,
                    False,
                    "enum",
                    lower_bound=0,
                    upper_bound=len(specification.names) - 1,
                )
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
                size = element_count * self._target_storage_size(element_type)
                if size > self._aggregate_size_limit():
                    raise self._error(
                        f"Statisches Array ist mit {size} Bytes größer als das Ziel-Limit "
                        f"von {self._aggregate_size_limit()} Bytes.",
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
            elif isinstance(specification, SetTypeSpecification):
                element_type = self._resolve_type(
                    specification.element_type_name,
                    specification.position,
                )
                if element_type == BOOLEAN_TYPE:
                    lower, upper = 0, 1
                elif element_type.kind == "enum":
                    lower, upper = element_type.lower_bound, element_type.upper_bound
                else:
                    raise self._error(
                        "SET OF unterstützt derzeit Boolean oder Aufzählungstypen.",
                        specification.position,
                    )
                if lower < 0 or upper > 15:
                    raise self._error(
                        f"SET OF {element_type.name} benötigt {upper - lower + 1} Bits; "
                        "der aktuelle plattformübergreifende Set-Typ unterstützt maximal 16 Werte.",
                        specification.position,
                    )
                type_info = _PascalType(
                    declaration.name,
                    2,
                    False,
                    "set",
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
                    base_type.size if base_type is not None else self._class_pointer_size(),
                    False,
                    "class",
                    base_type=base_type,
                    vmt_label=f"__pas_vmt_{self._safe_name(declaration.name)}",
                )
                if base_type is not None:
                    type_info.fields.update(base_type.fields)
                    type_info.methods.update(base_type.methods)
                    type_info.properties.update(base_type.properties)
                    type_info.vmt_methods.extend(base_type.vmt_methods)
                self.types[key] = type_info
                self.class_types.append(type_info)
                self._install_fields(type_info, specification.fields)
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
                owner.fields[key] = _FieldInfo(
                    field_name,
                    field_type,
                    owner.size,
                    declaration.position,
                    owner,
                    declaration.visibility,
                )
                owner.size += self._target_storage_size(field_type)
                if owner.size > self._aggregate_size_limit():
                    raise self._error(
                        f"{owner.name} ist größer als das Ziel-Limit von "
                        f"{self._aggregate_size_limit()} Bytes.",
                        declaration.position,
                    )

    @staticmethod
    def _method_signature_matches(
        inherited: _MethodInfo,
        kind: str,
        parameters: Tuple[_ParameterInfo, ...],
        result_type: Optional[_PascalType],
    ) -> bool:
        if inherited.kind != kind or inherited.result_type is not result_type:
            return False
        if len(inherited.parameters) != len(parameters):
            return False
        return all(
            left.type_info is right.type_info and left.modifier == right.modifier
            for left, right in zip(inherited.parameters, parameters)
        )

    def _install_methods(
        self,
        owner: _PascalType,
        declarations: Sequence[MethodDeclaration],
    ) -> None:
        for declaration in declarations:
            key = self._key(declaration.name)
            if key in owner.fields and owner.fields[key].owner is owner:
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
            inherited = owner.methods.get(key)
            if inherited is not None and inherited.owner is owner:
                raise self._error(
                    f"Methode mehrfach deklariert: {declaration.name}.",
                    declaration.position,
                )

            vmt_slot: Optional[int] = None
            is_virtual = bool(declaration.is_virtual or declaration.is_override)
            if declaration.is_override:
                if inherited is None or not inherited.virtual or inherited.vmt_slot is None:
                    raise self._error(
                        f"OVERRIDE benötigt eine geerbte virtuelle Methode: {owner.name}.{declaration.name}.",
                        declaration.position,
                    )
                if not self._method_signature_matches(
                    inherited, declaration.kind, parameters, result_type
                ):
                    raise self._error(
                        f"OVERRIDE-Signatur stimmt nicht mit {inherited.owner.name}.{inherited.name} überein.",
                        declaration.position,
                    )
                vmt_slot = inherited.vmt_slot
            elif declaration.is_virtual:
                vmt_slot = len(owner.vmt_methods)

            method = _MethodInfo(
                owner,
                declaration.kind,
                declaration.name,
                parameters,
                result_type,
                declaration.position,
                f"__pas_method_{self._safe_name(owner.name)}_{self._safe_name(declaration.name)}",
                declaration.visibility,
                is_virtual,
                declaration.is_override,
                vmt_slot,
            )
            owner.methods[key] = method
            if vmt_slot is not None:
                if declaration.is_override:
                    owner.vmt_methods[vmt_slot] = method
                else:
                    owner.vmt_methods.append(method)
            self.methods.append(method)

    def _install_properties(
        self,
        owner: _PascalType,
        declarations: Sequence[PropertyDeclaration],
    ) -> None:
        for declaration in declarations:
            key = self._key(declaration.name)
            if key in owner.fields and owner.fields[key].owner is owner:
                raise self._error(
                    f"Property kollidiert mit Feld: {owner.name}.{declaration.name}.",
                    declaration.position,
                )
            if key in owner.properties and owner.properties[key].owner is owner:
                raise self._error(
                    f"Property mehrfach deklariert: {owner.name}.{declaration.name}.",
                    declaration.position,
                )
            type_info = self._resolve_type(declaration.type_name, declaration.position)
            prop = _PropertyInfo(
                owner,
                declaration.name,
                type_info,
                declaration.read_name,
                declaration.write_name,
                declaration.visibility,
                declaration.position,
            )
            # Accessoren werden bereits beim Typaufbau validiert. READ darf ein
            # Feld gleichen Typs oder eine parameterlose Funktion sein. WRITE
            # darf ein Feld oder eine Prozedur mit genau einem Wertparameter sein.
            if prop.read_name:
                read_key = self._key(prop.read_name)
                field_info = owner.fields.get(read_key)
                method_info = owner.methods.get(read_key)
                if field_info is not None:
                    if field_info.type_info is not type_info:
                        raise self._error(
                            f"READ-Feld {prop.read_name} besitzt nicht den Property-Typ {type_info.name}.",
                            declaration.position,
                        )
                elif method_info is not None:
                    if method_info.result_type is not type_info or method_info.parameters:
                        raise self._error(
                            f"READ-Methode {prop.read_name} muss parameterlos {type_info.name} liefern.",
                            declaration.position,
                        )
                else:
                    raise self._error(
                        f"READ-Accessor nicht gefunden: {owner.name}.{prop.read_name}.",
                        declaration.position,
                    )
            if prop.write_name:
                write_key = self._key(prop.write_name)
                field_info = owner.fields.get(write_key)
                method_info = owner.methods.get(write_key)
                if field_info is not None:
                    if field_info.type_info is not type_info:
                        raise self._error(
                            f"WRITE-Feld {prop.write_name} besitzt nicht den Property-Typ {type_info.name}.",
                            declaration.position,
                        )
                elif method_info is not None:
                    if (
                        method_info.result_type is not None
                        or len(method_info.parameters) != 1
                        or method_info.parameters[0].type_info is not type_info
                    ):
                        raise self._error(
                            f"WRITE-Methode {prop.write_name} muss genau einen {type_info.name}-Parameter besitzen.",
                            declaration.position,
                        )
                else:
                    raise self._error(
                        f"WRITE-Accessor nicht gefunden: {owner.name}.{prop.write_name}.",
                        declaration.position,
                    )
            owner.properties[key] = prop

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
            if key in self.types or key in self.type_declarations:
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
            if isinstance(value, int) and not -32768 <= value <= 65535:
                raise self._error(
                    f"Konstante liegt außerhalb -32768..65535: {value}.",
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
        self._prepare_method_implementations()

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
                if item.modifier != "value":
                    raise self._error(
                        f"Externe Routine {declaration.name}: nur Wertparameter "
                        "werden derzeit unterstützt.",
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
                self._resolve_type(
                    declaration.result_type_name,
                    SourcePosition(1, 1),
                )
                if declaration.result_type_name
                else None
            )
            self.external_routines[key] = _ExternalRoutineInfo(
                declaration.unit_name,
                declaration.kind,
                declaration.name,
                tuple(parameters),
                result_type,
                declaration.symbol,
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

        if variable is not None:
            type_info = variable.type_info
            base_label = variable.label
        elif self.current_method is not None and key == "self":
            type_info = self.current_method.owner
            use_self = True
        elif self.current_method is not None and (
            key == "result" or key == self._key(self.current_method.name)
        ) and self.current_method.result_variable is not None:
            type_info = self.current_method.result_variable.type_info
            base_label = self.current_method.result_variable.label
        elif self.current_method is not None and key in self.current_method.owner.fields:
            field_info = self.current_method.owner.fields[key]
            self._require_member_access(
                field_info.owner,
                field_info.visibility,
                f"{field_info.owner.name if field_info.owner else self.current_method.owner.name}.{field_info.name}",
                designator.position,
            )
            type_info = field_info.type_info
            offset = field_info.offset
            use_self = True
        else:
            raise self._error(f"Variable nicht gefunden: {designator.name}.", designator.position)

        dynamic = None
        class_deref = False
        for selector in designator.selectors:
            if isinstance(selector, FieldSelector):
                if type_info.kind not in {"record", "class"}:
                    raise self._error(
                        f"{type_info.name} besitzt keine Felder.",
                        selector.position,
                    )
                field_info = type_info.fields.get(self._key(selector.name))
                if field_info is None:
                    raise self._error(
                        f"Feld nicht gefunden: {type_info.name}.{selector.name}.",
                        selector.position,
                    )
                if type_info.kind == "class":
                    class_deref = True
                    self._require_member_access(
                        field_info.owner,
                        field_info.visibility,
                        f"{field_info.owner.name if field_info.owner else type_info.name}.{field_info.name}",
                        selector.position,
                    )
                offset += field_info.offset
                type_info = field_info.type_info
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
                offset += (index_value - type_info.lower_bound) * self._target_storage_size(type_info.element_type)
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
                    self._target_storage_size(type_info.element_type),
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
            class_deref,
        )

    def _resolve_property_access(
        self,
        designator: DesignatorExpression,
    ) -> Optional[Tuple[_PropertyInfo, _StorageAccess]]:
        if designator.selectors and isinstance(designator.selectors[-1], FieldSelector):
            selector = designator.selectors[-1]
            receiver_designator = DesignatorExpression(
                designator.position,
                designator.name,
                designator.selectors[:-1],
            )
            try:
                receiver = self._resolve_storage(receiver_designator)
            except C64PascalError:
                return None
            if receiver.type_info.kind != "class":
                return None
            prop = receiver.type_info.properties.get(self._key(selector.name))
            if prop is None:
                return None
            self._require_member_access(
                prop.owner,
                prop.visibility,
                f"{prop.owner.name}.{prop.name}",
                selector.position,
            )
            return prop, receiver

        if not designator.selectors and self.current_method is not None:
            prop = self.current_method.owner.properties.get(self._key(designator.name))
            if prop is not None:
                self._require_member_access(
                    prop.owner,
                    prop.visibility,
                    f"{prop.owner.name}.{prop.name}",
                    designator.position,
                )
                return prop, _StorageAccess(
                    self.current_method.owner,
                    designator.position,
                    None,
                    True,
                )
        return None

    @staticmethod
    def _member_storage_from_receiver(
        receiver: _StorageAccess,
        field_info: _FieldInfo,
    ) -> _StorageAccess:
        return _StorageAccess(
            field_info.type_info,
            receiver.position,
            receiver.base_label,
            receiver.use_self,
            receiver.constant_offset + field_info.offset,
            receiver.dynamic,
            receiver.class_deref or (receiver.type_info.kind == "class" and not receiver.use_self),
        )

    def _compile_property_read(
        self,
        designator: DesignatorExpression,
    ) -> Optional[_PascalType]:
        resolved = self._resolve_property_access(designator)
        if resolved is None:
            return None
        prop, receiver = resolved
        if not prop.read_name:
            raise self._error(
                f"Property ist nicht lesbar: {prop.owner.name}.{prop.name}.",
                designator.position,
            )
        key = self._key(prop.read_name)
        field_info = receiver.type_info.fields.get(key)
        if field_info is not None:
            self._emit_load_access(
                self._member_storage_from_receiver(receiver, field_info),
                designator.position.line,
            )
            return prop.type_info
        method = receiver.type_info.methods.get(key)
        if method is None:
            raise self._error(
                f"READ-Accessor nicht gefunden: {prop.read_name}.",
                designator.position,
            )
        return self._compile_method_call(method, receiver, (), designator.position)

    def _compile_property_write(
        self,
        designator: DesignatorExpression,
        expression: Expression,
    ) -> bool:
        resolved = self._resolve_property_access(designator)
        if resolved is None:
            return False
        prop, receiver = resolved
        if not prop.write_name:
            raise self._error(
                f"Property ist schreibgeschützt: {prop.owner.name}.{prop.name}.",
                designator.position,
            )
        key = self._key(prop.write_name)
        field_info = receiver.type_info.fields.get(key)
        if field_info is not None:
            result_type = self._compile_expr(expression)
            if not self._types_compatible(prop.type_info, result_type):
                raise self._error(
                    f"Zuweisung von {result_type.name} an Property {prop.name}:{prop.type_info.name} ist nicht zulässig.",
                    expression.position,
                )
            self._emit_store_access(
                self._member_storage_from_receiver(receiver, field_info),
                designator.position.line,
            )
            return True
        method = receiver.type_info.methods.get(key)
        if method is None:
            raise self._error(
                f"WRITE-Accessor nicht gefunden: {prop.write_name}.",
                designator.position,
            )
        self._compile_method_call(method, receiver, (expression,), designator.position)
        return True

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
            self._require_member_access(
                method.owner,
                method.visibility,
                f"{method.owner.name}.{method.name}",
                method_selector.position,
            )
            return method, receiver

        if self.current_method is not None:
            method = self.current_method.owner.methods.get(self._key(designator.name))
            if method is not None:
                self._require_member_access(
                    method.owner,
                    method.visibility,
                    f"{method.owner.name}.{method.name}",
                    designator.position,
                )
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

    def _expression_type(self, expression: Expression) -> _PascalType:
        if isinstance(expression, LiteralExpression):
            return self._constant_type(expression.value)
        if isinstance(expression, (NameExpression, DesignatorExpression)):
            key = self._key(expression.name)
            if key == "nil" and (not isinstance(expression, DesignatorExpression) or not expression.selectors):
                return NIL_TYPE
            if not isinstance(expression, DesignatorExpression) or not expression.selectors:
                if key in self.constants:
                    return self.constant_types.get(key, self._constant_type(self.constants[key]))
            if isinstance(expression, DesignatorExpression):
                property_access = self._resolve_property_access(expression)
                if property_access is not None:
                    return property_access[0].type_info
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
        if isinstance(expression, CallExpression):
            designator = self._as_designator(expression.designator, expression.position)
            if not designator.selectors:
                name = self._key(designator.name)
                if name == "peek":
                    return BYTE_TYPE
                if name == "chr":
                    return CHAR_TYPE
                if name in {"ord", "lo", "hi"}:
                    return INTEGER_TYPE
                if name == "readln":
                    return STRING_TYPE
                if name == "exceptionmessage":
                    return STRING_TYPE
                if name == "exceptioncode":
                    return INTEGER_TYPE
                if name in {"emptyset", "setof", "setrange", "setunion"}:
                    return UNTYPED_SET_TYPE
                if name == "setcontains":
                    return BOOLEAN_TYPE

                # Globale Routinen aus C-Prototypen, #pragma-link-Modulen und
                # Pascal-PUI-Dateien muessen bereits bei der reinen
                # Typbestimmung beruecksichtigt werden. Andernfalls wird ein
                # Ausdruck wie
                #
                #     value | SetOf(element)
                #
                # faelschlich an die Klassenmethoden-Aufloesung weitergereicht
                # und endet mit "Methode nicht gefunden: SetOf".
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
            left = self._expression_type(expression.left)
            right = self._expression_type(expression.right)
            if left.kind == "set" or right.kind == "set":
                if left.kind != "set" or right.kind != "set":
                    raise self._error("Set-Operator erwartet auf beiden Seiten einen Set-Wert.", expression.position)
                if (
                    left is not UNTYPED_SET_TYPE
                    and right is not UNTYPED_SET_TYPE
                    and left.element_type is not right.element_type
                ):
                    raise self._error(
                        f"Inkompatible Set-Typen: {left.name} und {right.name}.",
                        expression.position,
                    )
                if expression.operator in {"=", "<>"}:
                    return BOOLEAN_TYPE
                if expression.operator in {"+", "-", "*"}:
                    return left if left is not UNTYPED_SET_TYPE else right
                raise self._error(
                    f"Operator {expression.operator} ist für Sets nicht zulässig.",
                    expression.position,
                )
            if expression.operator in {"=", "<>", "<", "<=", ">", ">="}:
                return BOOLEAN_TYPE
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
                property_type = self._compile_property_read(expression)
                if property_type is not None:
                    return property_type
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
            if left_type.kind == "set" and right_type.kind == "set":
                result_type = left_type if left_type is not UNTYPED_SET_TYPE else right_type
                if operator == "+":
                    self._emit_simple_binary("or", line)
                    return result_type
                if operator == "*":
                    self._emit_simple_binary("and", line)
                    return result_type
                if operator == "-":
                    self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
                    self.emitter.emit(f"    stx {self.ZP_LEFT_HI}", line)
                    self.emitter.emit(f"    lda {self.ZP_RIGHT_LO}", line)
                    self.emitter.emit("    eor #$FF", line)
                    self.emitter.emit(f"    sta {self.ZP_RIGHT_LO}", line)
                    self.emitter.emit(f"    lda {self.ZP_RIGHT_HI}", line)
                    self.emitter.emit("    eor #$FF", line)
                    self.emitter.emit(f"    sta {self.ZP_RIGHT_HI}", line)
                    self.emitter.emit(f"    lda {self.ZP_LEFT_LO}", line)
                    self.emitter.emit(f"    ldx {self.ZP_LEFT_HI}", line)
                    self._emit_simple_binary("and", line)
                    return result_type
                if operator in {"=", "<>"}:
                    self._emit_comparison(operator, False, line)
                    return BOOLEAN_TYPE
                raise self._error(f"Operator {operator} ist für Sets nicht zulässig.", expression.position)
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

    def _evaluate_set_mask(self, expression: Expression) -> int:
        if not isinstance(expression, CallExpression):
            raise self._error("Set-Konstruktor muss konstant sein.", expression.position)
        designator = self._as_designator(expression.designator, expression.position)
        if designator.selectors:
            raise self._error("Ungültiger Set-Konstruktor.", expression.position)
        name = self._key(designator.name)
        if name == "emptyset":
            self._require_argument_count(designator.name, expression.arguments, 0, expression.position)
            return 0
        if name == "setof":
            mask = 0
            if not expression.arguments:
                return 0
            for argument in expression.arguments:
                value = self._evaluate_constant(argument)
                if isinstance(value, (str, bool)):
                    value = int(value) if isinstance(value, bool) else -1
                value = int(value)
                if not 0 <= value <= 15:
                    raise self._error(
                        f"Set-Element {value} liegt außerhalb 0..15.",
                        argument.position,
                    )
                mask |= 1 << value
            return mask
        if name == "setrange":
            self._require_argument_count(designator.name, expression.arguments, 2, expression.position)
            lower = int(self._evaluate_constant(expression.arguments[0]))
            upper = int(self._evaluate_constant(expression.arguments[1]))
            if not (0 <= lower <= upper <= 15):
                raise self._error(
                    f"Set-Bereich {lower}..{upper} liegt außerhalb 0..15.",
                    expression.position,
                )
            mask = 0
            for value in range(lower, upper + 1):
                mask |= 1 << value
            return mask
        if name == "setunion":
            mask = 0
            for argument in expression.arguments:
                mask |= self._evaluate_set_mask(argument)
            return mask
        raise self._error(f"Unbekannter Set-Konstruktor: {designator.name}.", expression.position)

    def _compile_set_builtin(self, expression: CallExpression) -> Optional[_PascalType]:
        designator = self._as_designator(expression.designator, expression.position)
        if designator.selectors:
            return None
        name = self._key(designator.name)
        if name in {"emptyset", "setof", "setrange", "setunion"}:
            self._emit_load_literal(self._evaluate_set_mask(expression), expression.position.line)
            return UNTYPED_SET_TYPE
        if name != "setcontains":
            return None
        self._require_argument_count(designator.name, expression.arguments, 2, expression.position)
        set_type = self._expression_type(expression.arguments[0])
        if set_type.kind != "set":
            raise self._error("SetContains erwartet als erstes Argument einen Set-Wert.", expression.arguments[0].position)
        value = self._evaluate_constant(expression.arguments[1])
        if isinstance(value, (str, bool)):
            value = int(value) if isinstance(value, bool) else -1
        value = int(value)
        if not 0 <= value <= 15:
            raise self._error(f"Set-Element {value} liegt außerhalb 0..15.", expression.arguments[1].position)
        self._compile_expr(expression.arguments[0])
        mask = 1 << value
        line = expression.position.line
        if mask <= 0xFF:
            self.emitter.emit(f"    and #${mask:02X}", line)
        else:
            self.emitter.emit("    txa", line)
            self.emitter.emit(f"    and #${(mask >> 8) & 0xFF:02X}", line)
        false_label = self._new_label("set_contains_false")
        end_label = self._new_label("set_contains_end")
        self.emitter.emit(f"    beq {false_label}", line)
        self._emit_load_literal(1, line)
        self.emitter.emit(f"    jmp {end_label}", line)
        self.emitter.emit(f"{false_label}:", line)
        self._emit_load_literal(0, line)
        self.emitter.emit(f"{end_label}:", line)
        return BOOLEAN_TYPE

    def _compile_function(self, expression: CallExpression) -> _PascalType:
        designator = self._as_designator(expression.designator, expression.position)
        name = self._key(designator.name) if not designator.selectors else ""
        line = expression.position.line
        set_result = self._compile_set_builtin(expression)
        if set_result is not None:
            return set_result
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
        # Klassen sind Referenztypen. Eine Referenz auf eine abgeleitete
        # Instanz darf einer Variablen einer Basisklasse zugewiesen werden.
        if target.kind == "class" and source.kind == "nil":
            return True
        if target.kind == "class" and source.kind == "class":
            return self._is_descendant(source, target)
        if target.kind == "set" or source.kind == "set":
            if target.kind != "set" or source.kind != "set":
                return False
            if target is UNTYPED_SET_TYPE or source is UNTYPED_SET_TYPE:
                return True
            return target.element_type is source.element_type
        if target == BOOLEAN_TYPE or source == BOOLEAN_TYPE:
            return False
        numeric = {INTEGER_TYPE, BYTE_TYPE, CHAR_TYPE}
        return target in numeric and (source in numeric or source.kind == "enum")

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
        if method.virtual:
            if method.vmt_slot is None:
                raise self._error("Interner Fehler: virtuelle Methode ohne VMT-Slot.", position)
            slot_offset = method.vmt_slot * 2
            self.emitter.emit("    ldy #$00", line)
            self.emitter.emit(f"    lda ({self.ZP_SELF_LO}),y", line)
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
            self.emitter.emit("    iny", line)
            self.emitter.emit(f"    lda ({self.ZP_SELF_LO}),y", line)
            self.emitter.emit(f"    sta {self.ZP_LEFT_HI}", line)
            self.emitter.emit(f"    ldy #${slot_offset & 0xFF:02X}", line)
            self.emitter.emit(f"    lda ({self.ZP_LEFT_LO}),y", line)
            self.emitter.emit(f"    sta {self.ZP_RIGHT_LO}", line)
            self.emitter.emit("    iny", line)
            self.emitter.emit(f"    lda ({self.ZP_LEFT_LO}),y", line)
            self.emitter.emit(f"    sta {self.ZP_RIGHT_HI}", line)
            self.runtime.add("virtual_call")
            self.emitter.emit("    jsr __pas_virtual_call", line)
        else:
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

    def _compile_constructor_assignment(self, statement: AssignmentStatement) -> bool:
        expression = statement.expression
        if isinstance(expression, CallExpression):
            call_designator = self._as_designator(expression.designator, expression.position)
            arguments = expression.arguments
        elif isinstance(expression, DesignatorExpression):
            # Pascal erlaubt parameterlose Konstruktoren ohne Klammern:
            #     obj := TObject.Create;
            call_designator = expression
            arguments = ()
        else:
            return False
        if len(call_designator.selectors) != 1 or not isinstance(call_designator.selectors[0], FieldSelector):
            return False
        class_type = self.types.get(self._key(call_designator.name))
        if class_type is None or class_type.kind != "class":
            return False
        method = class_type.methods.get(self._key(call_designator.selectors[0].name))
        if method is None or method.kind != "constructor":
            return False
        self._require_member_access(
            method.owner,
            method.visibility,
            f"{method.owner.name}.{method.name}",
            expression.position,
        )

        target = self._resolve_storage(self._as_designator(statement.designator, statement.position))
        if target.type_info.kind != "class":
            raise self._error(
                f"Constructor {class_type.name}.{method.name} kann nur einer Klassenvariable zugewiesen werden.",
                statement.position,
            )
        # Das aktuelle OOP-Modell speichert Objekte statisch. Damit ein
        # Konstruktor-Ausdruck trotzdem Delphi-artig geschrieben werden kann,
        # konstruiert die Zuweisung direkt in den Speicher der Zielvariable.
        # Abgeleitete Instanzen in kleineren Basisklassen-Speichern werden erst
        # mit dem spaeteren Heap-/Referenzmodell zugelassen.
        if target.type_info is not class_type:
            raise self._error(
                f"Constructor {class_type.name}.{method.name} benötigt derzeit eine Zielvariable exakt vom Typ {class_type.name}.",
                statement.position,
            )
        self._compile_method_call(method, target, arguments, expression.position)
        return True

    def _compile_implicit_free(self, statement: CallStatement) -> bool:
        designator = self._as_designator(statement.designator, statement.position)
        if not designator.selectors or not isinstance(designator.selectors[-1], FieldSelector):
            return False
        if self._key(designator.selectors[-1].name) != "free":
            return False
        receiver_designator = DesignatorExpression(
            designator.position,
            designator.name,
            designator.selectors[:-1],
        )
        receiver = self._resolve_storage(receiver_designator)
        if receiver.type_info.kind != "class":
            return False
        # Eine explizit deklarierte Free-Methode hat Vorrang.
        explicit = receiver.type_info.methods.get("free")
        if explicit is not None:
            return False
        if statement.arguments:
            raise self._error("Free erwartet keine Argumente.", statement.position)
        destructor = receiver.type_info.methods.get("destroy")
        if destructor is None:
            # Delphi-kompatibles Free auf einem Objekt ohne expliziten
            # Destruktor ist im statischen Modell ein No-op.
            return True
        if destructor.kind != "destructor":
            raise self._error(
                f"{receiver.type_info.name}.Destroy ist kein Destruktor.",
                statement.position,
            )
        self._compile_method_call(destructor, receiver, (), statement.position)
        return True

    def _compile_assignment(self, statement: AssignmentStatement) -> None:
        if self._compile_constructor_assignment(statement):
            return
        designator = self._as_designator(statement.designator, statement.position)
        if self._compile_property_write(designator, statement.expression):
            return
        access = self._resolve_storage(designator)
        if not access.type_info.scalar:
            raise self._error(
                "Ganze Arrays, Records oder Klassen können nicht direkt zugewiesen werden.",
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

    def _compile_statement(self, statement: Statement) -> None:
        line = statement.position.line
        if isinstance(statement, CompoundStatement):
            for child in statement.statements:
                self._compile_statement(child)
            return
        if isinstance(statement, AssignmentStatement):
            self._compile_assignment(statement)
            return
        if isinstance(statement, CallStatement):
            self._compile_call_statement(statement)
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
        if isinstance(statement, TryFinallyStatement):
            self.finally_stack.append(statement.finally_statement)
            try:
                self._compile_statement(statement.try_statement)
            finally:
                self.finally_stack.pop()
            self._compile_statement(statement.finally_statement)
            return
        if isinstance(statement, TryExceptStatement):
            # Der Handler wird bereits als eigener Codeblock erzeugt. Solange
            # noch kein RAISE-/Exception-Transport aktiv ist, springt der
            # normale Ausführungspfad darüber hinweg. Eine spätere Runtime
            # kann den except_label direkt als Handlerziel verwenden.
            except_label = self._new_label("try_except_handler")
            end_label = self._new_label("try_except_end")
            self._compile_statement(statement.try_statement)
            self.emitter.emit(f"    jmp {end_label}", line)
            self.emitter.emit(f"{except_label}:", line)
            self._compile_statement(statement.except_statement)
            self.emitter.emit(f"{end_label}:", line)
            return
        if isinstance(statement, BreakStatement):
            if not self.break_targets:
                raise self._error("BREAK ist nur innerhalb einer Schleife erlaubt.", statement.position)
            self._compile_pending_finally()
            self.emitter.emit(f"    jmp {self.break_targets[-1]}", line)
            return
        if isinstance(statement, ContinueStatement):
            if not self.continue_targets:
                raise self._error("CONTINUE ist nur innerhalb einer Schleife erlaubt.", statement.position)
            self._compile_pending_finally()
            self.emitter.emit(f"    jmp {self.continue_targets[-1]}", line)
            return
        raise self._error("Anweisung wird nicht unterstützt.", statement.position)

    def _compile_pending_finally(self) -> None:
        if not self.finally_stack:
            return
        pending = list(reversed(self.finally_stack))
        saved = self.finally_stack
        self.finally_stack = []
        try:
            for finalizer in pending:
                self._compile_statement(finalizer)
        finally:
            self.finally_stack = saved

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

    def _compile_set_mutation(self, statement: CallStatement, include: bool) -> None:
        self._require_argument_count(
            "Include" if include else "Exclude",
            statement.arguments,
            2,
            statement.position,
        )
        target_expression = statement.arguments[0]
        if not isinstance(target_expression, (NameExpression, DesignatorExpression)):
            raise self._error("Include/Exclude erwartet als erstes Argument eine Set-Variable.", target_expression.position)
        target = self._as_designator(target_expression)
        access = self._resolve_storage(target)
        if access.type_info.kind != "set":
            raise self._error("Include/Exclude erwartet als erstes Argument einen Set-Typ.", target_expression.position)
        set_element = CallExpression(
            statement.position,
            "SetOf",
            (statement.arguments[1],),
        )
        expression = BinaryExpression(
            statement.position,
            target_expression,
            "+" if include else "-",
            set_element,
        )
        self._compile_assignment(
            AssignmentStatement(statement.position, target, expression)
        )

    def _compile_call_statement(self, statement: CallStatement) -> None:
        designator = self._as_designator(statement.designator, statement.position)
        name = self._key(designator.name) if not designator.selectors else ""
        line = statement.position.line
        if name in {"__pas_raise", "__pas_raise_class", "__pas_reraise"}:
            raise self._error(
                "Exception-Transport mit RAISE ist derzeit nur fuer Windows PE32 implementiert.",
                statement.position,
            )
        if name in {"include", "exclude"}:
            self._compile_set_mutation(statement, name == "include")
            return
        if self._compile_implicit_free(statement):
            return

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
            if routine.result_type is not None:
                raise self._error(
                    f"{routine.name} ist eine Funktion und muss in einem Ausdruck verwendet werden.",
                    statement.position,
                )
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
                    if variable.type_info.kind == "class":
                        assert variable.type_info.vmt_label is not None
                        self.emitter.emit(
                            f"    lda #<{variable.type_info.vmt_label}",
                            implementation.position.line,
                        )
                        self.emitter.emit(
                            f"    sta {variable.label}",
                            implementation.position.line,
                        )
                        self.emitter.emit(
                            f"    lda #>{variable.type_info.vmt_label}",
                            implementation.position.line,
                        )
                        self.emitter.emit(
                            f"    sta {variable.label}+1",
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
        if "virtual_call" in self.runtime:
            self.emitter.emit()
            self.emitter.emit("; Indirekter VMT-Aufruf; Zieladresse liegt in $FD/$FE")
            self.emitter.emit("__pas_virtual_call:")
            self.emitter.emit(f"    jmp ({self.ZP_RIGHT_LO})")
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

        if self.class_types:
            self.emitter.emit()
            self.emitter.emit("; Virtuelle Methodentabellen (VMT)")
            for class_type in self.class_types:
                assert class_type.vmt_label is not None
                self.emitter.emit(f"{class_type.vmt_label}:")
                if class_type.vmt_methods:
                    for method in class_type.vmt_methods:
                        self.emitter.emit(f"    .word {method.label}")
                else:
                    self.emitter.emit("    .word 0")

        if self.variable_order:
            self.emitter.emit()
            self.emitter.emit("; Pascal-Variablen")
            for variable in self.variable_order:
                initial_value = getattr(variable, "c_initial_value", None)
                comment = "intern" if variable.internal else variable.name
                if variable.type_info.kind == "class":
                    assert variable.type_info.vmt_label is not None
                    self.emitter.emit(
                        f"{variable.label}: .word {variable.type_info.vmt_label} "
                        f"; {comment}: {variable.type_info.name}, VMT"
                    )
                    remaining = variable.type_info.size - self._class_pointer_size()
                    if remaining > 0:
                        self.emitter.emit(
                            "    .byte " + ", ".join("$00" for _ in range(remaining))
                        )
                    continue
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
    ) -> None:
        super().__init__(program)
        self.symbol_prefix = symbol_prefix
        self.language_name = language_name
        self.graphics_backend = str(graphics_backend or "Direct2D")
        self.console_mode = bool(console_mode)
        self.library_name = str(library_name) if library_name else None
        self.library_exports = dict(library_exports or {})
        self._install_builtin_exception_class()

    def _install_builtin_exception_class(self) -> None:
        position = SourcePosition(1, 1)
        exception_type = _PascalType(
            "Exception",
            8,
            False,
            "class",
            vmt_label=f"{self.symbol_prefix}_vmt_exception",
        )
        message_field = _FieldInfo(
            "FMessage", STRING_TYPE, 4, position, exception_type, "private"
        )
        exception_type.fields["fmessage"] = message_field
        exception_type.properties["message"] = _PropertyInfo(
            exception_type, "Message", STRING_TYPE, "FMessage", None, "public", position
        )
        self.types["exception"] = exception_type
        self.class_types.append(exception_type)
        self.exception_base_type = exception_type

    def _class_pointer_size(self) -> int:
        return 4

    def _aggregate_size_limit(self) -> int:
        return 16 * 1024 * 1024

    def _target_storage_size(self, type_info: "_PascalType") -> int:
        return self._pe32_storage_size(type_info)

    def _compile_set_builtin(self, expression: CallExpression) -> Optional[_PascalType]:
        designator = self._as_designator(expression.designator, expression.position)
        if designator.selectors:
            return None
        name = self._key(designator.name)
        if name in {"emptyset", "setof", "setrange", "setunion"}:
            self._emit_load_literal(self._evaluate_set_mask(expression), expression.position.line)
            return UNTYPED_SET_TYPE
        if name != "setcontains":
            return None
        self._require_argument_count(designator.name, expression.arguments, 2, expression.position)
        if self._expression_type(expression.arguments[0]).kind != "set":
            raise self._error("SetContains erwartet als erstes Argument einen Set-Wert.", expression.arguments[0].position)
        value = int(self._evaluate_constant(expression.arguments[1]))
        if not 0 <= value <= 15:
            raise self._error(f"Set-Element {value} liegt außerhalb 0..15.", expression.arguments[1].position)
        self._compile_expr(expression.arguments[0])
        self.emitter.emit(f"    test eax, {1 << value}", expression.position.line)
        self.emitter.emit("    setne al", expression.position.line)
        self.emitter.emit("    movzx eax, al", expression.position.line)
        return BOOLEAN_TYPE

    def _new_label(self, prefix: str) -> str:
        self.label_counter += 1
        return f"{self.symbol_prefix}_{prefix}_{self.label_counter}"

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

    @staticmethod
    def _pe32_storage_size(type_info: _PascalType) -> int:
        # Strings und Klassen sind unter PE32 Referenztypen. Der Typ selbst
        # behaelt bei Klassen die Instanzgroesse (VMT + Felder), waehrend eine
        # Variable nur den 32-Bit-Objektzeiger speichert.
        if type_info == STRING_TYPE or type_info.kind == "class":
            return 4
        return int(type_info.size)


    def _compile_constructor_assignment(self, statement: AssignmentStatement) -> bool:
        expression = statement.expression
        if isinstance(expression, CallExpression):
            call_designator = self._as_designator(expression.designator, expression.position)
            arguments = expression.arguments
        elif isinstance(expression, DesignatorExpression):
            call_designator = expression
            arguments = ()
        else:
            return False
        if len(call_designator.selectors) != 1 or not isinstance(call_designator.selectors[0], FieldSelector):
            return False
        class_type = self.types.get(self._key(call_designator.name))
        if class_type is None or class_type.kind != "class":
            return False
        method = class_type.methods.get(self._key(call_designator.selectors[0].name))
        if method is None or method.kind != "constructor":
            return False
        self._require_member_access(
            method.owner,
            method.visibility,
            f"{method.owner.name}.{method.name}",
            expression.position,
        )
        target = self._resolve_storage(self._as_designator(statement.designator, statement.position))
        if target.type_info.kind != "class":
            raise self._error(
                f"Constructor {class_type.name}.{method.name} kann nur einer Klassenreferenz zugewiesen werden.",
                statement.position,
            )
        if not self._types_compatible(target.type_info, class_type):
            raise self._error(
                f"{class_type.name} kann nicht an {target.type_info.name} zugewiesen werden.",
                statement.position,
            )

        # Echte PE32-Heap-Instanz: EAX=Instanzgroesse, EDX=VMT.
        self.runtime.update({"heap", "exception"})
        self.emitter.emit(f"    mov eax, {int(class_type.size)}", statement.position.line)
        self.emitter.emit(f"    mov edx, {class_type.vmt_label}", statement.position.line)
        self.emitter.emit(f"    call {self.symbol_prefix}_new_object", statement.position.line)
        self._emit_store_access(target, statement.position.line)

        # Delphi-artige Constructor-Sicherheit: wir legen um den eigentlichen
        # Konstruktor einen versteckten Exception-Frame. Schlaegt Create fehl,
        # wird die teilweise erzeugte Instanz zerstoert/freigegeben, die
        # Zielreferenz auf NIL gesetzt und danach zur aeusseren Ebene erneut
        # geworfen.
        ctor_fail = self._new_label("constructor_unwind")
        ctor_done = self._new_label("constructor_done")
        self._emit_exception_frame_push(ctor_fail, statement.position.line)
        self._compile_method_call(method, target, arguments, expression.position)
        self._emit_exception_frame_pop(statement.position.line)
        self.emitter.emit(f"    jmp {ctor_done}", statement.position.line)
        self.emitter.emit(f"{ctor_fail}:", statement.position.line)
        destructor = class_type.methods.get("destroy")
        if destructor is not None and destructor.kind == "destructor":
            self._compile_method_call(destructor, target, (), expression.position)
        self._emit_load_access(target, statement.position.line)
        self.emitter.emit(f"    call {self.symbol_prefix}_free_object", statement.position.line)
        self.emitter.emit("    xor eax, eax", statement.position.line)
        self._emit_store_access(target, statement.position.line)
        self.emitter.emit(f"    jmp {self.symbol_prefix}_reraise", statement.position.line)
        self.emitter.emit(f"{ctor_done}:", statement.position.line)
        return True

    def _compile_implicit_free(self, statement: CallStatement) -> bool:
        designator = self._as_designator(statement.designator, statement.position)
        if not designator.selectors or not isinstance(designator.selectors[-1], FieldSelector):
            return False
        if self._key(designator.selectors[-1].name) != "free":
            return False
        receiver_designator = DesignatorExpression(
            designator.position,
            designator.name,
            designator.selectors[:-1],
        )
        receiver = self._resolve_storage(receiver_designator)
        if receiver.type_info.kind != "class":
            return False
        explicit = receiver.type_info.methods.get("free")
        if explicit is not None:
            return False
        if statement.arguments:
            raise self._error("Free erwartet keine Argumente.", statement.position)

        line = statement.position.line
        # Free(nil) ist ein No-op. Zuerst Referenz laden, dann optional den
        # (virtuellen) Destruktor aufrufen, anschließend HeapFree und NIL setzen.
        self._emit_load_access(receiver, line)
        done = self._new_label("free_done")
        self.emitter.emit("    test eax, eax", line)
        self.emitter.emit(f"    jz {done}", line)
        destructor = receiver.type_info.methods.get("destroy")
        if destructor is not None:
            if destructor.kind != "destructor":
                raise self._error(
                    f"{receiver.type_info.name}.Destroy ist kein Destruktor.",
                    statement.position,
                )
            self._compile_method_call(destructor, receiver, (), statement.position)

        self._emit_load_access(receiver, line)
        self.runtime.add("heap")
        self.emitter.emit(f"    call {self.symbol_prefix}_free_object", line)
        self.emitter.emit("    xor eax, eax", line)
        self._emit_store_access(receiver, line)
        self.emitter.emit(f"{done}:", line)
        return True

    def _compile_assignment(self, statement: AssignmentStatement) -> None:
        if self._compile_constructor_assignment(statement):
            return
        designator = self._as_designator(statement.designator, statement.position)
        if self._compile_property_write(designator, statement.expression):
            return
        access = self._resolve_storage(designator)
        if not access.type_info.scalar and access.type_info.kind != "class":
            raise self._error(
                "Ganze Arrays und Records können nicht direkt zugewiesen werden.",
                statement.position,
            )
        result_type = self._compile_expr(statement.expression)
        if not self._types_compatible(access.type_info, result_type):
            raise self._error(
                f"Zuweisung von {result_type.name} an {access.type_info.name} ist nicht zulässig.",
                statement.position,
            )
        self._emit_store_access(access, statement.position.line)

    def _readln_variable_access(self, expression: Expression) -> Optional[_StorageAccess]:
        if not isinstance(expression, (NameExpression, DesignatorExpression)):
            return None
        try:
            access = self._resolve_storage(expression)
        except C64PascalError:
            return None
        if access.type_info != STRING_TYPE:
            raise self._error(
                "ReadLn erwartet für die Eingabevariable derzeit den Typ String.",
                expression.position,
            )
        return access

    def _compile_readln_prompt(self, expression: Expression) -> None:
        prompt_type = self._compile_expr(expression)
        if prompt_type != STRING_TYPE:
            raise self._error(
                "Der ReadLn-Eingabetext muss vom Typ String sein.",
                expression.position,
            )
        self.runtime.add("print_string")
        self.emitter.emit(
            f"    call {self.symbol_prefix}_print_string",
            expression.position.line,
        )

    def _compile_readln_call(self, position: SourcePosition) -> None:
        if not self.console_mode:
            raise self._error(
                "ReadLn ist im Windows-PE32-Modus nur für 'Console' verfügbar.",
                position,
            )
        self.runtime.add("readln")
        self.emitter.emit(
            f"    call {self.symbol_prefix}_readln",
            position.line,
        )

    def _emit_nil_reference_check(self, register: str, line: int) -> None:
        self.runtime.add("exception")
        ok = self._new_label("class_ref_ok")
        self.emitter.emit(f"    test {register}, {register}", line)
        self.emitter.emit(f"    jnz {ok}", line)
        self.emitter.emit(f"    mov eax, {self.symbol_prefix}_nil_message", line)
        self.emitter.emit(f"    call {self.symbol_prefix}_raise", line)
        self.emitter.emit(f"{ok}:", line)

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
            if access.class_deref:
                self.emitter.emit(f"    mov ecx, dword ptr [{access.base_label}]", line)
                self._emit_nil_reference_check("ecx", line)
            else:
                self.emitter.emit(f"    mov ecx, {access.base_label}", line)

        if dynamic is not None:
            self.emitter.emit("    add ecx, edx", line)
        if access.constant_offset:
            self.emitter.emit(f"    add ecx, {int(access.constant_offset)}", line)

    def _emit_load_access(self, access: _StorageAccess, line: int) -> None:
        size = self._pe32_storage_size(access.type_info)
        if size not in {1, 2, 4}:
            raise self._error(
                "Das PE32-Backend kann derzeit skalare 8-, 16- und 32-Bit-Werte laden.",
                access.position,
            )
        self._emit_address(access, line)
        if size == 1:
            self.emitter.emit("    movzx eax, byte ptr [ecx]", line)
        elif size == 2:
            instruction = "movsx" if access.type_info.signed else "movzx"
            self.emitter.emit(f"    {instruction} eax, word ptr [ecx]", line)
        else:
            self.emitter.emit("    mov eax, dword ptr [ecx]", line)

    def _emit_store_access(self, access: _StorageAccess, line: int) -> None:
        size = self._pe32_storage_size(access.type_info)
        if size not in {1, 2, 4}:
            raise self._error(
                "Das PE32-Backend kann derzeit skalare 8-, 16- und 32-Bit-Werte speichern.",
                access.position,
            )
        self.emitter.emit("    push eax", line)
        self._emit_address(access, line)
        self.emitter.emit("    pop eax", line)
        if size == 1:
            self.emitter.emit("    mov byte ptr [ecx], al", line)
        elif size == 2:
            self.emitter.emit("    mov word ptr [ecx], ax", line)
        else:
            self.emitter.emit("    mov dword ptr [ecx], eax", line)

    def _store_variable(self, variable: _Variable, line: int) -> None:
        self._emit_store_access(
            _StorageAccess(variable.type_info, variable.position, variable.label, False),
            line,
        )

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
        if isinstance(expression, LiteralExpression):
            if isinstance(expression.value, str):
                label = self._string_label(expression.value, expression.position)
                self.emitter.emit(f"    mov eax, {label}", line)
                return STRING_TYPE
            self._emit_load_literal(int(expression.value), line)
            return self._constant_type(expression.value)

        if isinstance(expression, (NameExpression, DesignatorExpression)):
            key = self._key(expression.name)
            has_selectors = isinstance(expression, DesignatorExpression) and bool(expression.selectors)
            if key == "nil" and not has_selectors:
                self.emitter.emit("    xor eax, eax", line)
                return NIL_TYPE
            if key in self.constants and not has_selectors:
                value = self.constants[key]
                if isinstance(value, str):
                    label = self._string_label(value, expression.position)
                    self.emitter.emit(f"    mov eax, {label}", line)
                    return STRING_TYPE
                self._emit_load_literal(int(value), line)
                return self.constant_types.get(key, self._constant_type(value))
            if isinstance(expression, DesignatorExpression):
                property_type = self._compile_property_read(expression)
                if property_type is not None:
                    return property_type
            try:
                access = self._resolve_storage(expression)
            except C64PascalError:
                if isinstance(expression, DesignatorExpression):
                    resolved = self._resolve_parameterless_function(expression)
                    if resolved is not None:
                        method, receiver = resolved
                        return self._compile_method_call(method, receiver, (), expression.position)
                raise
            if not access.type_info.scalar and access.type_info.kind != "class":
                raise self._error(
                    f"{access.type_info.name} kann nicht als skalarer Ausdruck geladen werden.",
                    expression.position,
                )
            self._emit_load_access(access, line)
            return access.type_info

        if isinstance(expression, CallExpression):
            return self._compile_function(expression)

        if isinstance(expression, UnaryExpression):
            operand_type = self._compile_expr(expression.operand)
            if operand_type == STRING_TYPE:
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
            if left_type == STRING_TYPE or right_type == STRING_TYPE:
                raise self._error("String-Vergleiche und String-Arithmetik werden nicht unterstuetzt.", expression.position)
            self._compile_expr(expression.left)
            self.emitter.emit("    push eax", line)
            self._compile_expr(expression.right)
            self.emitter.emit("    mov edx, eax", line)
            self.emitter.emit("    pop eax", line)
            operator = expression.operator
            if left_type.kind == "set" and right_type.kind == "set":
                result_type = left_type if left_type is not UNTYPED_SET_TYPE else right_type
                if operator == "+":
                    self.emitter.emit("    or eax, edx", line)
                    return result_type
                if operator == "*":
                    self.emitter.emit("    and eax, edx", line)
                    return result_type
                if operator == "-":
                    self.emitter.emit("    not edx", line)
                    self.emitter.emit("    and eax, edx", line)
                    self.emitter.emit("    and eax, 65535", line)
                    return result_type
                if operator in {"=", "<>"}:
                    self._emit_comparison(operator, False, line)
                    return BOOLEAN_TYPE
                raise self._error(f"Operator {operator} ist für Sets nicht zulässig.", expression.position)
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

    def _compile_external_call(self, routine, arguments, position):
        self._require_argument_count(routine.name, arguments, len(routine.parameters), position)
        for argument, parameter in zip(arguments, routine.parameters):
            argument_type = self._expression_type(argument)
            if (
                (not argument_type.scalar and argument_type.kind != "class")
                or (not parameter.type_info.scalar and parameter.type_info.kind != "class")
            ):
                raise self._error("Aggregatparameter werden fuer externe Routinen noch nicht unterstuetzt.", argument.position)
            if not self._types_compatible(parameter.type_info, argument_type):
                raise self._error(f"Argumenttyp {argument_type.name} passt nicht zu {parameter.type_info.name}.", argument.position)
        line = position.line
        for argument in reversed(arguments):
            self._compile_expr(argument)
            self.emitter.emit("    push eax", line)
        self.emitter.emit(f"    call {routine.symbol}", line)
        if arguments:
            self.emitter.emit(f"    add esp, {len(arguments) * 4}", line)
        return routine.result_type if routine.result_type is not None else BYTE_TYPE

    def _compile_function(self, expression: CallExpression) -> _PascalType:
        designator = self._as_designator(expression.designator, expression.position)
        name = self._key(designator.name) if not designator.selectors else ""
        line = expression.position.line
        set_result = self._compile_set_builtin(expression)
        if set_result is not None:
            return set_result
        if name == "exceptionmessage":
            self._require_argument_count(designator.name, expression.arguments, 0, expression.position)
            self.runtime.add("exception")
            self.emitter.emit(f"    mov eax, dword ptr [{self.symbol_prefix}_exception_message]", line)
            return STRING_TYPE
        if name == "exceptioncode":
            self._require_argument_count(designator.name, expression.arguments, 0, expression.position)
            self.runtime.add("exception")
            self.emitter.emit(f"    mov eax, dword ptr [{self.symbol_prefix}_exception_code]", line)
            return INTEGER_TYPE
        if name == "readln":
            if len(expression.arguments) > 1:
                raise self._error(
                    "ReadLn als Funktion erwartet keinen oder einen Eingabetext.",
                    expression.position,
                )
            if expression.arguments:
                self._compile_readln_prompt(expression.arguments[0])
            self._compile_readln_call(expression.position)
            return STRING_TYPE
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
        routine = self.external_routines.get(name)
        if routine is not None:
            if routine.result_type is None:
                raise self._error(f"{routine.name} ist keine Funktion.", expression.position)
            return self._compile_external_call(routine, expression.arguments, expression.position)
        method, receiver = self._resolve_method_call(designator)
        if method.result_type is None:
            raise self._error(f"{method.owner.name}.{method.name} ist keine Funktion.", expression.position)
        return self._compile_method_call(method, receiver, expression.arguments, expression.position)

    def _emit_set_self_address(self, receiver: _StorageAccess, line: int) -> None:
        # SELF ist bereits der Objektzeiger. Bei einer Klassenvariablen liegt
        # dagegen an der Speicheradresse nur die 32-Bit-Referenz.
        if receiver.use_self and receiver.constant_offset == 0 and receiver.dynamic is None:
            self._emit_nil_reference_check("esi", line)
            return
        self._emit_address(receiver, line)
        if receiver.type_info.kind == "class":
            self.emitter.emit("    mov esi, dword ptr [ecx]", line)
        else:
            self.emitter.emit("    mov esi, ecx", line)
        self._emit_nil_reference_check("esi", line)

    def _compile_method_call(self, method, receiver, arguments, position):
        self._require_argument_count(method.name, arguments, len(method.parameters), position)
        line = position.line
        for argument, parameter, variable in zip(arguments, method.parameters, method.parameter_variables):
            argument_type = self._compile_expr(argument)
            if (not argument_type.scalar and argument_type.kind != "class") or (
                not parameter.type_info.scalar and parameter.type_info.kind != "class"
            ):
                raise self._error("Record-/Array-Parameter werden noch nicht unterstuetzt.", argument.position)
            if not self._types_compatible(parameter.type_info, argument_type):
                raise self._error(f"Argumenttyp {argument_type.name} passt nicht zu {parameter.type_info.name}.", argument.position)
            self._store_variable(variable, line)
        restore_self = self.current_method is not None
        if restore_self:
            self.emitter.emit("    push esi", line)
        self._emit_set_self_address(receiver, line)
        if method.virtual:
            if method.vmt_slot is None:
                raise self._error("Interner Fehler: virtuelle Methode ohne VMT-Slot.", position)
            self.emitter.emit("    mov ecx, dword ptr [esi]", line)
            self.emitter.emit(
                f"    call dword ptr [ecx+{method.vmt_slot * 4}]",
                line,
            )
        else:
            self.emitter.emit(f"    call {method.label}", line)
        if restore_self:
            self.emitter.emit("    pop esi", line)
        return method.result_type if method.result_type is not None else BYTE_TYPE

    _EXCEPTION_FRAME_SIZE = 24

    def _emit_exception_frame_push(self, handler_label: str, line: int) -> None:
        self.runtime.update({"exception", "heap"})
        self.emitter.emit(f"    sub esp, {self._EXCEPTION_FRAME_SIZE}", line)
        self.emitter.emit(f"    mov eax, dword ptr [{self.symbol_prefix}_exception_top]", line)
        self.emitter.emit("    mov dword ptr [esp], eax", line)
        self.emitter.emit(f"    mov eax, {handler_label}", line)
        self.emitter.emit("    mov dword ptr [esp+4], eax", line)
        self.emitter.emit("    mov dword ptr [esp+8], ebp", line)
        self.emitter.emit("    mov dword ptr [esp+12], esi", line)
        self.emitter.emit("    mov dword ptr [esp+16], ebx", line)
        self.emitter.emit("    mov dword ptr [esp+20], edi", line)
        self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_top], esp", line)

    def _emit_exception_frame_pop(self, line: int) -> None:
        self.emitter.emit("    mov eax, dword ptr [esp]", line)
        self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_top], eax", line)
        self.emitter.emit(f"    add esp, {self._EXCEPTION_FRAME_SIZE}", line)

    def _compile_try_body_with_control_cleanup(
        self,
        statement: Statement,
    ) -> Tuple[Optional[Tuple[str, str]], Optional[Tuple[str, str]]]:
        """Compile a protected body without leaking its runtime frame.

        BREAK/CONTINUE may target a loop outside the current TRY.  The base
        generator knows how to run pending FINALLY blocks, but it cannot know
        about the PE32 exception frame stored on ESP.  Temporarily replacing
        only the *currently active* loop target creates a cleanup trampoline.
        Loops declared inside the TRY push their own targets afterwards and
        therefore remain inside the protected scope.  Nested TRY blocks chain
        these trampolines naturally from inner to outer frame.
        """
        break_cleanup = None
        continue_cleanup = None
        if self.break_targets:
            original = self.break_targets[-1]
            cleanup = self._new_label("try_break_cleanup")
            self.break_targets[-1] = cleanup
            break_cleanup = (cleanup, original)
        if self.continue_targets:
            original = self.continue_targets[-1]
            cleanup = self._new_label("try_continue_cleanup")
            self.continue_targets[-1] = cleanup
            continue_cleanup = (cleanup, original)
        try:
            super()._compile_statement(statement)
        finally:
            if break_cleanup is not None:
                self.break_targets[-1] = break_cleanup[1]
            if continue_cleanup is not None:
                self.continue_targets[-1] = continue_cleanup[1]
        return break_cleanup, continue_cleanup

    def _emit_try_control_cleanup(
        self,
        cleanup: Optional[Tuple[str, str]],
        line: int,
    ) -> None:
        if cleanup is None:
            return
        cleanup_label, target_label = cleanup
        self.emitter.emit(f"{cleanup_label}:", line)
        self._emit_exception_frame_pop(line)
        self.emitter.emit(f"    jmp {target_label}", line)

    def _compile_statement(self, statement: Statement) -> None:
        line = statement.position.line
        if isinstance(statement, TryFinallyStatement):
            handler_label = self._new_label("try_finally_unwind")
            end_label = self._new_label("try_finally_end")
            self._emit_exception_frame_push(handler_label, line)
            self.finally_stack.append(statement.finally_statement)
            try:
                break_cleanup, continue_cleanup = self._compile_try_body_with_control_cleanup(
                    statement.try_statement
                )
            finally:
                self.finally_stack.pop()
            self._emit_exception_frame_pop(line)
            super()._compile_statement(statement.finally_statement)
            self.emitter.emit(f"    jmp {end_label}", line)

            # BREAK/CONTINUE have already executed the pending FINALLY code in
            # the base generator.  The trampoline only removes this TRY frame.
            self._emit_try_control_cleanup(break_cleanup, line)
            self._emit_try_control_cleanup(continue_cleanup, line)

            self.emitter.emit(f"{handler_label}:", line)
            # Das Runtime-Unwinding hat das aktuelle Frame bereits entfernt.
            # Der FINALLY-Code laeuft deshalb mit dem aeusseren Handler als Top.
            super()._compile_statement(statement.finally_statement)
            self.emitter.emit(f"    jmp {self.symbol_prefix}_reraise", line)
            self.emitter.emit(f"{end_label}:", line)
            return
        if isinstance(statement, TryExceptStatement):
            handler_label = self._new_label("try_except_handler")
            end_label = self._new_label("try_except_end")
            self._emit_exception_frame_push(handler_label, line)
            break_cleanup, continue_cleanup = self._compile_try_body_with_control_cleanup(
                statement.try_statement
            )
            self._emit_exception_frame_pop(line)
            self.emitter.emit(f"    jmp {end_label}", line)

            self._emit_try_control_cleanup(break_cleanup, line)
            self._emit_try_control_cleanup(continue_cleanup, line)

            self.emitter.emit(f"{handler_label}:", line)
            if statement.handlers:
                for index, handler in enumerate(statement.handlers):
                    exception_type = self._resolve_exception_class(handler.type_name, handler.position)
                    next_label = self._new_label(f"except_next_{index}")
                    handler_variable = self._allocate_variable(
                        handler.variable_name,
                        exception_type,
                        handler.position,
                        internal=True,
                        label_prefix=f"except_{handler.variable_name}",
                    )
                    self.emitter.emit(
                        f"    mov eax, dword ptr [{self.symbol_prefix}_exception_object]", line
                    )
                    self.emitter.emit(f"    mov edx, {exception_type.vmt_label}", line)
                    self.emitter.emit(f"    call {self.symbol_prefix}_exception_is_a", line)
                    self.emitter.emit("    test eax, eax", line)
                    self.emitter.emit(f"    jz {next_label}", line)
                    self.emitter.emit(
                        f"    mov eax, dword ptr [{self.symbol_prefix}_exception_object]", line
                    )
                    self._store_variable(handler_variable, line)
                    previous_scope = self.scope_variables
                    self.scope_variables = dict(previous_scope)
                    self.scope_variables[self._key(handler.variable_name)] = handler_variable
                    try:
                        super()._compile_statement(handler.body)
                    finally:
                        self.scope_variables = previous_scope
                    self.emitter.emit(f"    call {self.symbol_prefix}_exception_release", line)
                    self.emitter.emit(f"    jmp {end_label}", line)
                    self.emitter.emit(f"{next_label}:", line)
                # Kein ON-Typ passt: dieselbe Exception an den aeusseren Frame.
                self.emitter.emit(f"    jmp {self.symbol_prefix}_reraise", line)
            else:
                if statement.except_statement is not None:
                    super()._compile_statement(statement.except_statement)
                self.emitter.emit(f"    call {self.symbol_prefix}_exception_release", line)
            self.emitter.emit(f"{end_label}:", line)
            return
        super()._compile_statement(statement)

    def _compile_condition_jump_false(self, expression: Expression, target: str) -> None:
        result_type = self._compile_expr(expression)
        if result_type == STRING_TYPE:
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

    def _resolve_exception_class(self, class_name: str, position: SourcePosition) -> _PascalType:
        class_type = self._resolve_type(class_name, position)
        if class_type.kind != "class" or not self._is_descendant(class_type, self.exception_base_type):
            raise self._error(
                f"{class_name} ist keine von Exception abgeleitete Exception-Klasse.",
                position,
            )
        return class_type

    def _emit_raise_exception_class(
        self,
        class_type: _PascalType,
        message_expression: Expression,
        position: SourcePosition,
    ) -> None:
        line = position.line
        message_type = self._compile_expr(message_expression)
        if message_type != STRING_TYPE:
            raise self._error("Exception.Create erwartet eine String-Nachricht.", position)
        self.runtime.update({"heap", "exception"})

        message_temp = self._allocate_variable(
            f"$exception_message_{self.label_counter}_{len(self.variable_order)}",
            STRING_TYPE,
            position,
            internal=True,
            label_prefix="raised_exception_message",
        )
        self._store_variable(message_temp, line)

        object_temp = self._allocate_variable(
            f"$exception_object_{self.label_counter}_{len(self.variable_order)}",
            class_type,
            position,
            internal=True,
            label_prefix="raised_exception",
        )
        self.emitter.emit(f"    mov eax, {int(class_type.size)}", line)
        self.emitter.emit(f"    mov edx, {class_type.vmt_label}", line)
        self.emitter.emit(f"    call {self.symbol_prefix}_new_object", line)
        self._store_variable(object_temp, line)

        message_field = class_type.fields.get("fmessage")
        if message_field is None:
            raise self._error("Interner Fehler: Exception-Klasse ohne FMessage.", position)
        self._emit_load_access(
            _StorageAccess(STRING_TYPE, position, message_temp.label, False), line
        )
        self.emitter.emit("    mov edx, eax", line)
        self._emit_load_access(
            _StorageAccess(class_type, position, object_temp.label, False), line
        )
        self.emitter.emit(f"    mov dword ptr [eax+{message_field.offset}], edx", line)

        # Eine eigene Create(String)-Implementierung der konkreten
        # Exception-Klasse darf zusaetzliche Felder initialisieren. Die
        # Message-Basisinitialisierung ist bereits erfolgt und das Argument
        # wird nicht doppelt ausgewertet.
        constructor = class_type.methods.get("create")
        if constructor is not None and constructor.kind == "constructor":
            if len(constructor.parameters) != 1 or constructor.parameters[0].type_info != STRING_TYPE:
                raise self._error(
                    f"{class_type.name}.Create muss fuer RAISE genau einen String-Parameter besitzen.",
                    position,
                )
            self._compile_method_call(
                constructor,
                _StorageAccess(class_type, position, object_temp.label, False),
                (DesignatorExpression(position, message_temp.name),),
                position,
            )

        self._emit_load_access(
            _StorageAccess(class_type, position, object_temp.label, False), line
        )
        self.emitter.emit(f"    call {self.symbol_prefix}_raise_object", line)

    def _compile_call_statement(self, statement: CallStatement) -> None:
        designator = self._as_designator(statement.designator, statement.position)
        name = self._key(designator.name) if not designator.selectors else ""
        line = statement.position.line
        if name == "__pas_raise_class":
            self._require_argument_count("raise", statement.arguments, 2, statement.position)
            try:
                class_name = self._evaluate_constant(statement.arguments[0])
            except C64PascalError:
                class_name = None
            if not isinstance(class_name, str):
                raise self._error("RAISE erwartet einen statischen Exception-Klassennamen.", statement.position)
            class_type = self._resolve_exception_class(class_name, statement.position)
            self._emit_raise_exception_class(class_type, statement.arguments[1], statement.position)
            return
        if name == "__pas_raise":
            self._require_argument_count("raise", statement.arguments, 1, statement.position)
            self._emit_raise_exception_class(self.exception_base_type, statement.arguments[0], statement.position)
            return
        if name == "__pas_reraise":
            self._require_argument_count("raise", statement.arguments, 0, statement.position)
            self.runtime.add("exception")
            self.emitter.emit(f"    call {self.symbol_prefix}_reraise", line)
            return
        if name in {"include", "exclude"}:
            self._compile_set_mutation(statement, name == "include")
            return
        if self._compile_implicit_free(statement):
            return
        if name == "readln":
            if len(statement.arguments) > 2:
                raise self._error(
                    "ReadLn erwartet höchstens eine String-Variable und einen Eingabetext.",
                    statement.position,
                )
            target = None
            prompt = None
            if len(statement.arguments) == 1:
                target = self._readln_variable_access(statement.arguments[0])
                if target is None:
                    prompt = statement.arguments[0]
            elif len(statement.arguments) == 2:
                target = self._readln_variable_access(statement.arguments[0])
                if target is None:
                    raise self._error(
                        "ReadLn(variable, 'Text') erwartet als erstes Argument eine String-Variable.",
                        statement.arguments[0].position,
                    )
                prompt = statement.arguments[1]
            if prompt is not None:
                self._compile_readln_prompt(prompt)
            self._compile_readln_call(statement.position)
            if target is not None:
                self._emit_store_access(target, line)
            return
        if name in {"write", "writeln"}:
            for argument in statement.arguments:
                type_info = self._compile_expr(argument)
                if type_info == STRING_TYPE:
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
        if name == "clrscr":
            self._require_argument_count(designator.name, statement.arguments, 0, statement.position)
            self.runtime.add("clear_screen")
            self.emitter.emit(f"    call {self.symbol_prefix}_clear_screen", line)
            return
        routine = self.external_routines.get(name)
        if routine is not None:
            if routine.result_type is not None:
                raise self._error(f"{routine.name} ist eine Funktion und muss in einem Ausdruck verwendet werden.", statement.position)
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

    def _emit_methods(self) -> None:
        for method in self.methods:
            implementation = method.implementation
            if implementation is None:
                continue
            self.emitter.emit()
            self.emitter.emit(f"; {method.kind} {method.owner.name}.{method.name}", implementation.position.line)
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
                    line = implementation.position.line
                    self.emitter.emit("    xor eax, eax", line)
                    storage_size = self._pe32_storage_size(variable.type_info)
                    if variable.type_info.aggregate and variable.type_info.kind != "class":
                        self.emitter.emit(f"    mov ecx, {variable.label}", line)
                        for offset in range(storage_size):
                            operand = "byte ptr [ecx]" if offset == 0 else f"byte ptr [ecx+{offset}]"
                            self.emitter.emit(f"    mov {operand}, al", line)
                    else:
                        # Klassenvariablen sind Referenzen und beginnen mit NIL.
                        self._store_variable(variable, line)
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
                storage_size = self._pe32_storage_size(variable.type_info)
                if storage_size == 1:
                    self.emitter.emit(f"    mov byte ptr [{variable.label}], al")
                elif storage_size == 2:
                    self.emitter.emit(f"    mov word ptr [{variable.label}], ax")
                elif storage_size == 4:
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
        if "exception" in self.runtime:
            self.emitter.emit()
            self.emitter.emit("; Pascal Exception-Transport / Stack-Unwinding")
            self.emitter.emit(f"{self.symbol_prefix}_raise_object:")
            # Wird innerhalb eines EXCEPT-Handlers eine neue Exception
            # geworfen, gehoert die vorherige Exception nicht mehr zum
            # aktiven Transport. Nur Heap-Exception-Objekte werden freigegeben;
            # Runtime-Fallbacks benutzen ein statisches Exception-Objekt.
            replace_done = f"{self.symbol_prefix}_raise_object_replace_done"
            self.emitter.emit("    push eax")
            self.emitter.emit(f"    mov ecx, dword ptr [{self.symbol_prefix}_exception_object]")
            self.emitter.emit("    test ecx, ecx")
            self.emitter.emit(f"    jz {replace_done}")
            self.emitter.emit("    cmp ecx, eax")
            self.emitter.emit(f"    je {replace_done}")
            self.emitter.emit(f"    cmp dword ptr [{self.symbol_prefix}_exception_owned], 0")
            self.emitter.emit(f"    je {replace_done}")
            self.emitter.emit("    mov eax, ecx")
            self.emitter.emit(f"    call {self.symbol_prefix}_free_object")
            self.emitter.emit(f"{replace_done}:")
            self.emitter.emit("    pop eax")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_object], eax")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_owned], 1")
            self.emitter.emit("    test eax, eax")
            no_object_message = f"{self.symbol_prefix}_raise_object_no_message"
            self.emitter.emit(f"    jz {no_object_message}")
            self.emitter.emit("    mov edx, dword ptr [eax+4]")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_message], edx")
            self.emitter.emit(f"{no_object_message}:")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_code], 1")
            self.emitter.emit(f"    jmp {self.symbol_prefix}_exception_unwind")
            # Allocation-unabhaengiger Runtime-Fallback: ein statisches
            # Exception-Objekt mit gueltiger VMT und Message. Das ist auch bei
            # Out-of-memory sicher und kann von ``on E: Exception`` benutzt werden.
            self.emitter.emit(f"{self.symbol_prefix}_raise:")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_message], eax")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_raw_exception_object+4], eax")
            self.emitter.emit(f"    mov eax, {self.symbol_prefix}_raw_exception_object")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_object], eax")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_owned], 0")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_code], 1")
            self.emitter.emit(f"    jmp {self.symbol_prefix}_exception_unwind")
            self.emitter.emit(f"{self.symbol_prefix}_reraise:")
            self.emitter.emit(f"    cmp dword ptr [{self.symbol_prefix}_exception_message], 0")
            reraised = f"{self.symbol_prefix}_reraise_has_message"
            self.emitter.emit(f"    jne {reraised}")
            self.emitter.emit(f"    mov eax, {self.symbol_prefix}_generic_exception_message")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_message], eax")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_code], 1")
            self.emitter.emit(f"{reraised}:")
            self.emitter.emit(f"{self.symbol_prefix}_exception_unwind:")
            self.emitter.emit(f"    mov ecx, dword ptr [{self.symbol_prefix}_exception_top]")
            self.emitter.emit("    test ecx, ecx")
            unhandled = f"{self.symbol_prefix}_exception_unhandled"
            self.emitter.emit(f"    jz {unhandled}")
            self.emitter.emit("    mov edx, dword ptr [ecx+4]")
            self.emitter.emit("    mov eax, dword ptr [ecx]")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_top], eax")
            self.emitter.emit("    mov ebp, dword ptr [ecx+8]")
            self.emitter.emit("    mov esi, dword ptr [ecx+12]")
            self.emitter.emit("    mov ebx, dword ptr [ecx+16]")
            self.emitter.emit("    mov edi, dword ptr [ecx+20]")
            self.emitter.emit(f"    lea esp, [ecx+{self._EXCEPTION_FRAME_SIZE}]")
            self.emitter.emit("    jmp edx")
            self.emitter.emit(f"{unhandled}:")
            if self.console_mode:
                self.emitter.emit(f"    mov eax, {self.symbol_prefix}_unhandled_prefix")
                self.emitter.emit(f"    call {self.symbol_prefix}_write_cstring")
                no_message = f"{self.symbol_prefix}_exception_no_message"
                self.emitter.emit(f"    mov eax, dword ptr [{self.symbol_prefix}_exception_message]")
                self.emitter.emit("    test eax, eax")
                self.emitter.emit(f"    jz {no_message}")
                self.emitter.emit(f"    call {self.symbol_prefix}_write_cstring")
                self.emitter.emit(f"{no_message}:")
                self.emitter.emit(f"    mov eax, {self.symbol_prefix}_newline")
                self.emitter.emit(f"    call {self.symbol_prefix}_write_cstring")
            self.emitter.emit("    push 1")
            self.emitter.emit("    call ExitProcess")
            self.emitter.emit("    ret")

            self.emitter.emit(f"{self.symbol_prefix}_exception_is_a:")
            # EAX=Exception object (or NIL for raw runtime exception), EDX=expected VMT.
            raw_exception = f"{self.symbol_prefix}_exception_is_a_raw"
            match_loop = f"{self.symbol_prefix}_exception_is_a_loop"
            matched = f"{self.symbol_prefix}_exception_is_a_match"
            no_match = f"{self.symbol_prefix}_exception_is_a_no_match"
            self.emitter.emit("    test eax, eax")
            self.emitter.emit(f"    jz {raw_exception}")
            self.emitter.emit("    mov ecx, dword ptr [eax]")
            self.emitter.emit(f"{match_loop}:")
            self.emitter.emit("    test ecx, ecx")
            self.emitter.emit(f"    jz {no_match}")
            self.emitter.emit("    cmp ecx, edx")
            self.emitter.emit(f"    je {matched}")
            self.emitter.emit("    mov ecx, dword ptr [ecx-4]")
            self.emitter.emit(f"    jmp {match_loop}")
            self.emitter.emit(f"{raw_exception}:")
            self.emitter.emit(f"    mov ecx, {self.exception_base_type.vmt_label}")
            self.emitter.emit("    cmp edx, ecx")
            self.emitter.emit(f"    je {matched}")
            self.emitter.emit(f"{no_match}:")
            self.emitter.emit("    xor eax, eax")
            self.emitter.emit("    ret")
            self.emitter.emit(f"{matched}:")
            self.emitter.emit("    mov eax, 1")
            self.emitter.emit("    ret")
            self.emitter.emit(f"{self.symbol_prefix}_exception_release:")
            self.emitter.emit(f"    mov eax, dword ptr [{self.symbol_prefix}_exception_object]")
            release_clear = f"{self.symbol_prefix}_exception_release_clear"
            self.emitter.emit("    test eax, eax")
            self.emitter.emit(f"    jz {release_clear}")
            self.emitter.emit(f"    cmp dword ptr [{self.symbol_prefix}_exception_owned], 0")
            self.emitter.emit(f"    je {release_clear}")
            self.emitter.emit(f"    call {self.symbol_prefix}_free_object")
            self.emitter.emit(f"{release_clear}:")
            self.emitter.emit("    xor eax, eax")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_object], eax")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_owned], eax")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_message], eax")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_exception_code], eax")
            self.emitter.emit("    ret")

        if "heap" in self.runtime:
            self.emitter.emit()
            self.emitter.emit("; Pascal Class-Reference Heap Runtime")
            self.emitter.emit(f"{self.symbol_prefix}_new_object:")
            self.emitter.emit("    push ebx")
            self.emitter.emit("    push esi")
            self.emitter.emit("    mov ebx, eax")
            self.emitter.emit("    mov esi, edx")
            self.emitter.emit("    call GetProcessHeap")
            self.emitter.emit("    push ebx")
            self.emitter.emit("    push 8")
            self.emitter.emit("    push eax")
            self.emitter.emit("    call HeapAlloc")
            alloc_ok = f"{self.symbol_prefix}_heap_alloc_ok"
            self.emitter.emit("    test eax, eax")
            self.emitter.emit(f"    jnz {alloc_ok}")
            self.emitter.emit(f"    mov eax, {self.symbol_prefix}_oom_message")
            self.emitter.emit(f"    jmp {self.symbol_prefix}_raise")
            self.emitter.emit(f"{alloc_ok}:")
            self.emitter.emit("    mov dword ptr [eax], esi")
            self.emitter.emit("    pop esi")
            self.emitter.emit("    pop ebx")
            self.emitter.emit("    ret")
            self.emitter.emit(f"{self.symbol_prefix}_free_object:")
            free_done = f"{self.symbol_prefix}_heap_free_done"
            self.emitter.emit("    test eax, eax")
            self.emitter.emit(f"    jz {free_done}")
            self.emitter.emit("    push ebx")
            self.emitter.emit("    mov ebx, eax")
            self.emitter.emit("    call GetProcessHeap")
            self.emitter.emit("    push ebx")
            self.emitter.emit("    push 0")
            self.emitter.emit("    push eax")
            self.emitter.emit("    call HeapFree")
            self.emitter.emit("    pop ebx")
            self.emitter.emit(f"{free_done}:")
            self.emitter.emit("    ret")

        if self.console_mode:
            self.emitter.emit()
            self.emitter.emit(f"{self.symbol_prefix}_console_init:")
            self.emitter.emit("    call AllocConsole")
            # Nicht nur GetStdHandle verwenden: Wird das Programm von einem
            # GUI-Prozess mit umgeleiteten Standard-Handles gestartet, koennen
            # diese weiterhin auf NUL zeigen. CONIN$/CONOUT$ adressieren die
            # eben geoeffnete Windows-Konsole direkt und machen ReadLn/WriteLn
            # unabhaengig von der Startumgebung.
            self.emitter.emit("    push 0")
            self.emitter.emit("    push 0")
            self.emitter.emit("    push 3")  # OPEN_EXISTING
            self.emitter.emit("    push 0")
            self.emitter.emit("    push 3")  # FILE_SHARE_READ | FILE_SHARE_WRITE
            self.emitter.emit("    push 3221225472")  # GENERIC_READ | GENERIC_WRITE
            self.emitter.emit(f"    push {self.symbol_prefix}_conin_name")
            self.emitter.emit("    call CreateFileA")
            input_ok = f"{self.symbol_prefix}_console_input_ok"
            self.emitter.emit("    cmp eax, -1")
            self.emitter.emit(f"    jne {input_ok}")
            self.emitter.emit("    push -10")
            self.emitter.emit("    call GetStdHandle")
            self.emitter.emit(f"{input_ok}:")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_stdin_handle], eax")
            self.emitter.emit("    push 0")
            self.emitter.emit("    push 0")
            self.emitter.emit("    push 3")  # OPEN_EXISTING
            self.emitter.emit("    push 0")
            self.emitter.emit("    push 3")  # FILE_SHARE_READ | FILE_SHARE_WRITE
            self.emitter.emit("    push 3221225472")  # GENERIC_READ | GENERIC_WRITE
            self.emitter.emit(f"    push {self.symbol_prefix}_conout_name")
            self.emitter.emit("    call CreateFileA")
            output_ok = f"{self.symbol_prefix}_console_output_ok"
            self.emitter.emit("    cmp eax, -1")
            self.emitter.emit(f"    jne {output_ok}")
            self.emitter.emit("    push -11")
            self.emitter.emit("    call GetStdHandle")
            self.emitter.emit(f"{output_ok}:")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_stdout_handle], eax")
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

        if "readln" in self.runtime:
            self.emitter.emit(); self.emitter.emit(f"{self.symbol_prefix}_readln:")
            # ReadFile schreibt die Anzahl gelesener Bytes. Vor jedem Aufruf
            # auf 0 setzen, damit bei einem fehlgeschlagenen/abgebrochenen
            # ReadFile kein alter Wert aus einem vorherigen ReadLn uebrig bleibt.
            self.emitter.emit("    xor eax, eax")
            self.emitter.emit(f"    mov dword ptr [{self.symbol_prefix}_read_count], eax")
            self.emitter.emit("    push 0")
            self.emitter.emit(f"    push {self.symbol_prefix}_read_count")
            self.emitter.emit("    push 1023")
            self.emitter.emit(f"    push {self.symbol_prefix}_input_buffer")
            self.emitter.emit(f"    push dword ptr [{self.symbol_prefix}_stdin_handle]")
            self.emitter.emit("    call ReadFile")
            self.emitter.emit(f"    mov ecx, dword ptr [{self.symbol_prefix}_read_count]")
            self.emitter.emit(f"    mov eax, {self.symbol_prefix}_input_buffer")
            self.emitter.emit("    xor edx, edx")
            self.emitter.emit("    mov byte ptr [eax+ecx], dl")
            strip_loop = f"{self.symbol_prefix}_readln_strip"
            strip_done = f"{self.symbol_prefix}_readln_done"
            strip_char = f"{self.symbol_prefix}_readln_strip_char"
            self.emitter.emit(f"{strip_loop}:")
            self.emitter.emit("    test ecx, ecx")
            self.emitter.emit(f"    jz {strip_done}")
            self.emitter.emit("    dec ecx")
            self.emitter.emit("    movzx edx, byte ptr [eax+ecx]")
            self.emitter.emit("    cmp edx, 10")
            self.emitter.emit(f"    je {strip_char}")
            self.emitter.emit("    cmp edx, 13")
            self.emitter.emit(f"    jne {strip_done}")
            self.emitter.emit(f"{strip_char}:")
            self.emitter.emit("    xor edx, edx")
            self.emitter.emit("    mov byte ptr [eax+ecx], dl")
            self.emitter.emit(f"    jmp {strip_loop}")
            self.emitter.emit(f"{strip_done}:")
            self.emitter.emit(f"    mov eax, {self.symbol_prefix}_input_buffer")
            self.emitter.emit("    ret")

        if (
            self.runtime.intersection({"print_string", "print_int", "print_char", "print_newline", "clear_screen", "range_error"})
            or (self.console_mode and "exception" in self.runtime)
        ):
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
            self.emitter.emit("    push 1"); self.emitter.emit("    call ExitProcess"); self.emitter.emit("    ret")

    def _emit_data(self) -> None:
        self.emitter.emit(); self.emitter.emit("align 4")
        if self.class_types:
            self.emitter.emit("; Virtuelle Methodentabellen (VMT)")
            for class_type in self.class_types:
                assert class_type.vmt_label is not None
                base_vmt = class_type.base_type.vmt_label if class_type.base_type is not None else "0"
                self.emitter.emit(f"{class_type.vmt_label}__parent: dd {base_vmt}")
                self.emitter.emit(f"{class_type.vmt_label}:")
                if class_type.vmt_methods:
                    for method in class_type.vmt_methods:
                        self.emitter.emit(f"    dd {method.label}")
                else:
                    self.emitter.emit("    dd 0")
            self.emitter.emit("align 4")
        if "exception" in self.runtime:
            self.emitter.emit(f"{self.symbol_prefix}_exception_top: dd 0")
            self.emitter.emit(f"{self.symbol_prefix}_exception_object: dd 0")
            self.emitter.emit(f"{self.symbol_prefix}_exception_owned: dd 0")
            self.emitter.emit(f"{self.symbol_prefix}_exception_message: dd 0")
            self.emitter.emit(f"{self.symbol_prefix}_exception_code: dd 0")
            self.emitter.emit(f"{self.symbol_prefix}_raw_exception_object: dd {self.exception_base_type.vmt_label}, 0")
            self.emitter.emit(f"{self.symbol_prefix}_generic_exception_message: db 69, 120, 99, 101, 112, 116, 105, 111, 110, 0")
            self.emitter.emit(f"{self.symbol_prefix}_unhandled_prefix: db 85, 110, 104, 97, 110, 100, 108, 101, 100, 32, 101, 120, 99, 101, 112, 116, 105, 111, 110, 58, 32, 0")
            self.emitter.emit(f"{self.symbol_prefix}_nil_message: db 78, 105, 108, 32, 99, 108, 97, 115, 115, 32, 114, 101, 102, 101, 114, 101, 110, 99, 101, 0")
            self.emitter.emit(f"{self.symbol_prefix}_oom_message: db 79, 117, 116, 32, 111, 102, 32, 109, 101, 109, 111, 114, 121, 0")
        if self.console_mode:
            self.emitter.emit(f"{self.symbol_prefix}_stdin_handle: dd 0")
            self.emitter.emit(f"{self.symbol_prefix}_stdout_handle: dd 0")
            self.emitter.emit(f"{self.symbol_prefix}_conin_name: db 67, 79, 78, 73, 78, 36, 0")
            self.emitter.emit(f"{self.symbol_prefix}_conout_name: db 67, 79, 78, 79, 85, 84, 36, 0")
            self.emitter.emit(f"{self.symbol_prefix}_console_rect: dw 0, 0, 79, 24")
            self.emitter.emit(f"{self.symbol_prefix}_console_mode: dd 0")
            self.emitter.emit(f"{self.symbol_prefix}_written: dd 0")
            self.emitter.emit(f"{self.symbol_prefix}_format_buffer: db " + ", ".join(["0"] * 32))
            self.emitter.emit(f"{self.symbol_prefix}_char_buffer: db 0, 0")
            if "readln" in self.runtime:
                self.emitter.emit(f"{self.symbol_prefix}_read_count: dd 0")
                self.emitter.emit(
                    f"{self.symbol_prefix}_input_buffer: db "
                    + ", ".join(["0"] * 1024)
                )
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
                storage_size = self._pe32_storage_size(variable.type_info)
                if variable.type_info.kind == "class":
                    self.emitter.emit(
                        f"{variable.label}: dd 0 ; {comment}: {variable.type_info.name}, class reference (NIL)"
                    )
                    continue
                if storage_size == 1:
                    directive = "db"; value = int(initial_value or 0) & 0xFF
                elif storage_size == 2:
                    directive = "dw"; value = int(initial_value or 0) & 0xFFFF
                elif storage_size == 4:
                    directive = "dd"; value = int(initial_value or 0) & 0xFFFFFFFF
                else:
                    directive = "db"; value = None
                if value is None:
                    values = ", ".join("0" for _ in range(storage_size))
                    self.emitter.emit(f"{variable.label}: db {values} ; {comment}: {variable.type_info.name}")
                else:
                    self.emitter.emit(f"{variable.label}: {directive} {value} ; {comment}: {variable.type_info.name}")
        if self.strings:
            self.emitter.emit(); self.emitter.emit("; Nullterminierte Windows-Latin-1-Zeichenketten")
            for data, label in self.strings.items():
                values = ", ".join(str(value) for value in data + b"\x00")
                self.emitter.emit(f"{label}: db {values}")

    def generate(self) -> GeneratedAssembly:
        self._prepare_symbols()
        source_line = self.program.body.position.line

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
                "GetConsoleMode", "SetConsoleMode", "WriteFile", "ReadFile", "CreateFileA", "lstrlenA",
                "GetProcessHeap", "HeapAlloc", "HeapFree", "VirtualAlloc", "VirtualFree",
                "wsprintfA",
            ):
                self.emitter.emit(f"extern {symbol}")
            self.emitter.emit("__d64_dll_entry:", source_line)
            self.emitter.emit("    push ebp", source_line)
            self.emitter.emit("    mov ebp, esp", source_line)
            attach_done = self._new_label("dll_attach_done")
            self.emitter.emit("    cmp dword ptr [ebp+12], 1", source_line)
            self.emitter.emit(f"    jne {attach_done}", source_line)
            for variable, initializer in self.initializers:
                result_type = self._compile_expr(initializer)
                if not variable.type_info.scalar and variable.type_info.kind != "class":
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
            "GetConsoleMode", "SetConsoleMode", "WriteFile", "ReadFile", "CreateFileA", "lstrlenA",
            "GetProcessHeap", "HeapAlloc", "HeapFree", "VirtualAlloc", "VirtualFree",
            "wsprintfA",
        ):
            self.emitter.emit(f"extern {symbol}")
        self.emitter.emit("_start:", source_line)
        if self.console_mode:
            self.emitter.emit(f"    call {self.symbol_prefix}_console_init", source_line)
        for variable, initializer in self.initializers:
            result_type = self._compile_expr(initializer)
            if not variable.type_info.scalar and variable.type_info.kind != "class":
                raise self._error("Aggregate koennen nicht direkt initialisiert werden.", initializer.position)
            if not self._types_compatible(variable.type_info, result_type):
                raise self._error(f"Initialisierung von {variable.name} besitzt den falschen Typ.", initializer.position)
            self._store_variable(variable, initializer.position.line)
        self._compile_statement(self.program.body)
        self.emitter.emit("    push 0", source_line)
        self.emitter.emit("    call ExitProcess", source_line)
        self._emit_methods(); self._emit_runtime(); self._emit_data()
        assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
        return GeneratedAssembly(
            self.program.name,
            assembly,
            dict(self.emitter.source_map),
            sum(not variable.internal for variable in self.variable_order),
            len(self.strings),
        )




def _normalize_pe64_assembly_text(source: str) -> str:
    """Macht aus den wenigen geerbten IA-32-Stackaliasen sichtbaren AMD64-Code."""
    text = str(source)
    text = text.replace("bits 32", "bits 64")
    text = text.replace("IA-32-Assembler", "AMD64-Assembler")
    text = text.replace("Windows PE32 DLL / integrierter COFF32-Linker", "Windows PE64 DLL / integrierter COFF64-Linker")
    text = text.replace("Windows PE32 / integrierter COFF32-Linker", "Windows PE64 / integrierter COFF64-Linker")
    text = text.replace("Ziel: Windows PE32", "Ziel: Windows PE64")
    replacements = {
        "push ebp":"push rbp", "pop ebp":"pop rbp", "mov ebp, esp":"mov rbp, rsp",
        "mov esp, ebp":"mov rsp, rbp", "push esi":"push rsi", "pop esi":"pop rsi",
        "push edi":"push rdi", "pop edi":"pop rdi", "push ebx":"push rbx", "pop ebx":"pop rbx",
        "push eax":"push rax", "pop eax":"pop rax", "push ecx":"push rcx", "pop ecx":"pop rcx",
        "push edx":"push rdx", "pop edx":"pop rdx", "jmp edx":"jmp rdx", "jmp eax":"jmp rax",
    }
    lines=[]
    inserted_text_section = False
    for line in text.splitlines():
        stripped=line.strip().casefold()
        if stripped == "bits 64" and not inserted_text_section:
            lines.append(line)
            lines.append("section .text")
            inserted_text_section = True
            continue
        for old,new in replacements.items():
            if stripped == old:
                indent=line[:len(line)-len(line.lstrip())]; line=indent+new; stripped=new.casefold(); break
        # Der alte DLL-Einstieg las fdwReason aus [ebp+12]. Unter Win64 liegt
        # der zweite Parameter direkt in EDX.
        if re.fullmatch(r"\s*cmp\s+dword\s+ptr\s+\[ebp\+12\]\s*,\s*1\s*", line, re.I):
            line="    cmp edx, 1"
        if re.fullmatch(r"\s*ret\s+12\s*", line, re.I):
            line="    ret"
        # Der einzige geerbte cdecl-Cleanup in der PE64-Runtime ist wsprintfA:
        # drei 8-Byte-Pushes statt drei 4-Byte-Pushes.
        m=re.fullmatch(r"(\s*)add\s+esp\s*,\s*(\d+)\s*", line, re.I)
        if m:
            line=f"{m.group(1)}add rsp, {int(m.group(2))*2}"
        m=re.fullmatch(r"(\s*)sub\s+esp\s*,\s*(\d+)\s*", line, re.I)
        if m:
            line=f"{m.group(1)}sub rsp, {int(m.group(2))*2}"
        lines.append(line)
    return "\n".join(lines).rstrip()+"\n"


class _PE64CodeGenerator(_PE32CodeGenerator):
    """AMD64-/Windows-PE64-Backend auf Basis desselben Pascal-AST."""

    _EXCEPTION_FRAME_SIZE = 48

    def _install_builtin_exception_class(self) -> None:
        position = SourcePosition(1, 1)
        exception_type = _PascalType(
            "Exception", 16, False, "class",
            vmt_label=f"{self.symbol_prefix}_vmt_exception",
        )
        message_field = _FieldInfo(
            "FMessage", STRING_TYPE, 8, position, exception_type, "private"
        )
        exception_type.fields["fmessage"] = message_field
        exception_type.properties["message"] = _PropertyInfo(
            exception_type, "Message", STRING_TYPE, "FMessage", None,
            "public", position,
        )
        self.types["exception"] = exception_type
        self.class_types.append(exception_type)
        self.exception_base_type = exception_type

    def _class_pointer_size(self) -> int:
        return 8

    @staticmethod
    def _pe32_storage_size(type_info: _PascalType) -> int:
        if type_info == STRING_TYPE or type_info.kind == "class":
            return 8
        return int(type_info.size)

    def _target_storage_size(self, type_info: "_PascalType") -> int:
        return self._pe32_storage_size(type_info)

    def _compile_readln_call(self, position: SourcePosition) -> None:
        if not self.console_mode:
            raise self._error(
                "ReadLn ist im Windows-PE64-Modus nur für 'Console' verfügbar.",
                position,
            )
        self.runtime.add("readln")
        self.emitter.emit(f"    call {self.symbol_prefix}_readln", position.line)

    def _emit_address(self, access: _StorageAccess, line: int) -> None:
        dynamic = access.dynamic
        if dynamic is not None:
            self._compile_expr(dynamic.expression)
            if dynamic.lower_bound:
                self.emitter.emit(f"    sub eax, {int(dynamic.lower_bound)}", line)
            ok=self._new_label("index_range_ok")
            self.emitter.emit(f"    cmp eax, {int(dynamic.element_count)}", line)
            self.emitter.emit(f"    jb {ok}", line)
            self.runtime.add("range_error"); self.emitter.emit(f"    jmp {self.symbol_prefix}_range_error", line)
            self.emitter.emit(f"{ok}:", line)
            if dynamic.stride != 1:
                self.emitter.emit(f"    mov edx, {int(dynamic.stride)}", line)
                self.emitter.emit("    imul eax, edx", line)
            self.emitter.emit("    mov edx, eax", line)
        if access.use_self:
            self.emitter.emit("    mov rcx, rsi", line)
        else:
            assert access.base_label is not None
            if access.class_deref:
                self.emitter.emit(f"    mov rcx, qword ptr [{access.base_label}]", line)
                self._emit_nil_reference_check("rcx", line)
            else:
                self.emitter.emit(f"    mov rcx, {access.base_label}", line)
        if dynamic is not None:
            self.emitter.emit("    add rcx, rdx", line)
        if access.constant_offset:
            self.emitter.emit(f"    add rcx, {int(access.constant_offset)}", line)

    def _emit_load_access(self, access: _StorageAccess, line: int) -> None:
        size=self._pe32_storage_size(access.type_info); self._emit_address(access,line)
        if size==1: self.emitter.emit("    movzx eax, byte ptr [rcx]",line)
        elif size==2:
            ins="movsx" if access.type_info.signed else "movzx"; self.emitter.emit(f"    {ins} eax, word ptr [rcx]",line)
        elif size==4: self.emitter.emit("    mov eax, dword ptr [rcx]",line)
        elif size==8: self.emitter.emit("    mov rax, qword ptr [rcx]",line)
        else: raise self._error("Das PE64-Backend kann skalare 8-, 16-, 32- und 64-Bit-Werte laden.",access.position)

    def _emit_store_access(self, access: _StorageAccess, line: int) -> None:
        size=self._pe32_storage_size(access.type_info)
        self.emitter.emit("    push rax",line); self._emit_address(access,line); self.emitter.emit("    pop rax",line)
        if size==1: self.emitter.emit("    mov byte ptr [rcx], al",line)
        elif size==2: self.emitter.emit("    mov word ptr [rcx], ax",line)
        elif size==4: self.emitter.emit("    mov dword ptr [rcx], eax",line)
        elif size==8: self.emitter.emit("    mov qword ptr [rcx], rax",line)
        else: raise self._error("Das PE64-Backend kann skalare 8-, 16-, 32- und 64-Bit-Werte speichern.",access.position)

    def _emit_set_self_address(self, receiver: _StorageAccess, line: int) -> None:
        if receiver.use_self and receiver.constant_offset==0 and receiver.dynamic is None:
            self._emit_nil_reference_check("rsi",line); return
        self._emit_address(receiver,line)
        if receiver.type_info.kind=="class": self.emitter.emit("    mov rsi, qword ptr [rcx]",line)
        else: self.emitter.emit("    mov rsi, rcx",line)
        self._emit_nil_reference_check("rsi",line)

    def _compile_method_call(self, method, receiver, arguments, position):
        self._require_argument_count(method.name,arguments,len(method.parameters),position); line=position.line
        for argument,parameter,variable in zip(arguments,method.parameters,method.parameter_variables):
            at=self._compile_expr(argument)
            if (not at.scalar and at.kind!="class") or (not parameter.type_info.scalar and parameter.type_info.kind!="class"):
                raise self._error("Record-/Array-Parameter werden noch nicht unterstützt.",argument.position)
            if not self._types_compatible(parameter.type_info,at): raise self._error(f"Argumenttyp {at.name} passt nicht zu {parameter.type_info.name}.",argument.position)
            self._store_variable(variable,line)
        restore=self.current_method is not None
        if restore: self.emitter.emit("    push rsi",line)
        self._emit_set_self_address(receiver,line)
        if method.virtual:
            if method.vmt_slot is None: raise self._error("Interner Fehler: virtuelle Methode ohne VMT-Slot.",position)
            self.emitter.emit("    mov rcx, qword ptr [rsi]",line)
            self.emitter.emit(f"    call qword ptr [rcx+{method.vmt_slot*8}]",line)
        else: self.emitter.emit(f"    call {method.label}",line)
        if restore: self.emitter.emit("    pop rsi",line)
        return method.result_type if method.result_type is not None else BYTE_TYPE

    def _emit_exception_frame_push(self, handler_label: str, line: int) -> None:
        self.runtime.update({"exception","heap"})
        self.emitter.emit(f"    sub rsp, {self._EXCEPTION_FRAME_SIZE}",line)
        self.emitter.emit(f"    mov rax, qword ptr [{self.symbol_prefix}_exception_top]",line)
        self.emitter.emit("    mov qword ptr [rsp], rax",line)
        self.emitter.emit(f"    mov rax, {handler_label}",line)
        self.emitter.emit("    mov qword ptr [rsp+8], rax",line)
        self.emitter.emit("    mov qword ptr [rsp+16], rbp",line)
        self.emitter.emit("    mov qword ptr [rsp+24], rsi",line)
        self.emitter.emit("    mov qword ptr [rsp+32], rbx",line)
        self.emitter.emit("    mov qword ptr [rsp+40], rdi",line)
        self.emitter.emit(f"    mov qword ptr [{self.symbol_prefix}_exception_top], rsp",line)

    def _emit_exception_frame_pop(self, line: int) -> None:
        self.emitter.emit("    mov rax, qword ptr [rsp]",line)
        self.emitter.emit(f"    mov qword ptr [{self.symbol_prefix}_exception_top], rax",line)
        self.emitter.emit(f"    add rsp, {self._EXCEPTION_FRAME_SIZE}",line)

    def _compile_statement(self, statement: Statement) -> None:
        # Nur TRY..EXCEPT benoetigt direkte Breitenanpassung. TRY..FINALLY kann
        # den geerbten Kontrollfluss mit unseren Frame-Methoden wiederverwenden.
        if not isinstance(statement, TryExceptStatement):
            return super()._compile_statement(statement)
        line=statement.position.line; handler_label=self._new_label("try_except_handler"); end_label=self._new_label("try_except_end")
        self._emit_exception_frame_push(handler_label,line)
        break_cleanup,continue_cleanup=self._compile_try_body_with_control_cleanup(statement.try_statement)
        self._emit_exception_frame_pop(line); self.emitter.emit(f"    jmp {end_label}",line)
        self._emit_try_control_cleanup(break_cleanup,line); self._emit_try_control_cleanup(continue_cleanup,line)
        self.emitter.emit(f"{handler_label}:",line)
        if statement.handlers:
            for index,handler in enumerate(statement.handlers):
                et=self._resolve_exception_class(handler.type_name,handler.position); next_label=self._new_label(f"except_next_{index}")
                hv=self._allocate_variable(handler.variable_name,et,handler.position,internal=True,label_prefix=f"except_{handler.variable_name}")
                self.emitter.emit(f"    mov rax, qword ptr [{self.symbol_prefix}_exception_object]",line)
                self.emitter.emit(f"    mov rdx, {et.vmt_label}",line)
                self.emitter.emit(f"    call {self.symbol_prefix}_exception_is_a",line); self.emitter.emit("    test eax, eax",line); self.emitter.emit(f"    jz {next_label}",line)
                self.emitter.emit(f"    mov rax, qword ptr [{self.symbol_prefix}_exception_object]",line); self._store_variable(hv,line)
                previous=self.scope_variables; self.scope_variables=dict(previous); self.scope_variables[self._key(handler.variable_name)]=hv
                try: _CodeGenerator._compile_statement(self,handler.body)
                finally: self.scope_variables=previous
                self.emitter.emit(f"    call {self.symbol_prefix}_exception_release",line); self.emitter.emit(f"    jmp {end_label}",line); self.emitter.emit(f"{next_label}:",line)
            self.emitter.emit(f"    jmp {self.symbol_prefix}_reraise",line)
        else:
            if statement.except_statement is not None: _CodeGenerator._compile_statement(self,statement.except_statement)
            self.emitter.emit(f"    call {self.symbol_prefix}_exception_release",line)
        self.emitter.emit(f"{end_label}:",line)

    def _compile_function(self, expression: CallExpression) -> _PascalType:
        designator=self._as_designator(expression.designator,expression.position); name=self._key(designator.name) if not designator.selectors else ""
        if name=="exceptionmessage":
            self._require_argument_count(designator.name,expression.arguments,0,expression.position); self.runtime.add("exception"); self.emitter.emit(f"    mov rax, qword ptr [{self.symbol_prefix}_exception_message]",expression.position.line); return STRING_TYPE
        return super()._compile_function(expression)

    def _emit_raise_exception_class(self, class_type, message_expression, position):
        line=position.line; mt=self._compile_expr(message_expression)
        if mt!=STRING_TYPE: raise self._error("Exception.Create erwartet eine String-Nachricht.",position)
        self.runtime.update({"heap","exception"})
        msg=self._allocate_variable(f"$exception_message_{self.label_counter}_{len(self.variable_order)}",STRING_TYPE,position,internal=True,label_prefix="raised_exception_message"); self._store_variable(msg,line)
        obj=self._allocate_variable(f"$exception_object_{self.label_counter}_{len(self.variable_order)}",class_type,position,internal=True,label_prefix="raised_exception")
        self.emitter.emit(f"    mov eax, {int(class_type.size)}",line); self.emitter.emit(f"    mov rdx, {class_type.vmt_label}",line); self.emitter.emit(f"    call {self.symbol_prefix}_new_object",line); self._store_variable(obj,line)
        field=class_type.fields.get("fmessage")
        if field is None: raise self._error("Interner Fehler: Exception-Klasse ohne FMessage.",position)
        self._emit_load_access(_StorageAccess(STRING_TYPE,position,msg.label,False),line); self.emitter.emit("    mov rdx, rax",line); self._emit_load_access(_StorageAccess(class_type,position,obj.label,False),line); self.emitter.emit(f"    mov qword ptr [rax+{field.offset}], rdx",line)
        ctor=class_type.methods.get("create")
        if ctor is not None and ctor.kind=="constructor": self._compile_method_call(ctor,_StorageAccess(class_type,position,obj.label,False),(DesignatorExpression(position,msg.name),),position)
        self._emit_load_access(_StorageAccess(class_type,position,obj.label,False),line); self.emitter.emit(f"    call {self.symbol_prefix}_raise_object",line)

    def _emit_library_exports(self) -> None:
        if not self.library_exports: return
        arg_regs=("rcx","rdx","r8","r9")
        for public,internal in self.library_exports.items():
            method=self._library_export_method(internal); wrapper="__d64_export_"+self._safe_name(public)
            self.emitter.emit(); self.emitter.emit(f"global {wrapper}"); self.emitter.emit(f'export "{public}", {wrapper}'); self.emitter.emit(f"{wrapper}:")
            for index,var in enumerate(method.parameter_variables):
                size=self._pe32_storage_size(var.type_info)
                if index<4:
                    reg64=arg_regs[index]
                    reg32=("ecx","edx","r8d","r9d")[index]
                    reg16=("cx","dx","r8w","r9w")[index]
                    reg8=("cl","dl","r8b","r9b")[index]
                    if size==8: self.emitter.emit(f"    mov qword ptr [{var.label}], {reg64}")
                    elif size==4: self.emitter.emit(f"    mov dword ptr [{var.label}], {reg32}")
                    elif size==2: self.emitter.emit(f"    mov word ptr [{var.label}], {reg16}")
                    elif size==1: self.emitter.emit(f"    mov byte ptr [{var.label}], {reg8}")
                else:
                    off=40+(index-4)*8
                    self.emitter.emit(f"    mov rax, qword ptr [rsp+{off}]")
                    if size==8: self.emitter.emit(f"    mov qword ptr [{var.label}], rax")
                    elif size==4: self.emitter.emit(f"    mov dword ptr [{var.label}], eax")
                    elif size==2: self.emitter.emit(f"    mov word ptr [{var.label}], ax")
                    elif size==1: self.emitter.emit(f"    mov byte ptr [{var.label}], al")
            self.emitter.emit("    xor rsi, rsi"); self.emitter.emit(f"    call {method.label}"); self.emitter.emit("    ret")


    def _compile_external_call(self, routine, arguments, position):
        """PE64 external call via linker-generated Microsoft-x64 adapter."""
        self._require_argument_count(routine.name, arguments, len(routine.parameters), position)
        for argument, parameter in zip(arguments, routine.parameters):
            argument_type = self._expression_type(argument)
            if (
                (not argument_type.scalar and argument_type.kind != "class")
                or (not parameter.type_info.scalar and parameter.type_info.kind != "class")
            ):
                raise self._error("Aggregatparameter werden fuer externe Routinen noch nicht unterstuetzt.", argument.position)
            if not self._types_compatible(parameter.type_info, argument_type):
                raise self._error(
                    f"Argumenttyp {argument_type.name} passt nicht zu {parameter.type_info.name}.",
                    argument.position,
                )
        line = position.line
        # Compilerinternes PE64-ABI: ein 8-Byte-Slot pro Parameter. Der Linker
        # materialisiert aus dem Alias einen Adapter auf Microsoft x64 ABI.
        for argument in reversed(arguments):
            self._compile_expr(argument)
            self.emitter.emit("    push rax", line)
        adapter_symbol = f"__d64_argc{len(arguments)}__{routine.symbol}"
        self.emitter.emit(f"    call {adapter_symbol}", line)
        return routine.result_type if routine.result_type is not None else BYTE_TYPE

    def _compile_implicit_free(self, statement: CallStatement) -> bool:
        designator = self._as_designator(statement.designator, statement.position)
        if not designator.selectors or not isinstance(designator.selectors[-1], FieldSelector):
            return False
        if self._key(designator.selectors[-1].name) != "free":
            return False
        receiver_designator = DesignatorExpression(
            designator.position, designator.name, designator.selectors[:-1]
        )
        receiver = self._resolve_storage(receiver_designator)
        if receiver.type_info.kind != "class":
            return False
        if receiver.type_info.methods.get("free") is not None:
            return False
        if statement.arguments:
            raise self._error("Free erwartet keine Argumente.", statement.position)
        line = statement.position.line
        self._emit_load_access(receiver, line)
        done = self._new_label("free_done")
        self.emitter.emit("    test rax, rax", line)
        self.emitter.emit(f"    jz {done}", line)
        destructor = receiver.type_info.methods.get("destroy")
        if destructor is not None:
            if destructor.kind != "destructor":
                raise self._error(
                    f"{receiver.type_info.name}.Destroy ist kein Destruktor.", statement.position
                )
            self._compile_method_call(destructor, receiver, (), statement.position)
        self._emit_load_access(receiver, line)
        self.runtime.add("heap")
        self.emitter.emit(f"    call {self.symbol_prefix}_free_object", line)
        self.emitter.emit("    xor eax, eax", line)
        self._emit_store_access(receiver, line)
        self.emitter.emit(f"{done}:", line)
        return True

    def _emit_runtime(self) -> None:
        if "exception" in self.runtime:
            p=self.symbol_prefix; self.emitter.emit(); self.emitter.emit("; Pascal PE64 Exception-Transport / Stack-Unwinding")
            self.emitter.emit(f"{p}_raise_object:"); done=f"{p}_raise_object_replace_done"; self.emitter.emit("    push rax"); self.emitter.emit(f"    mov rcx, qword ptr [{p}_exception_object]"); self.emitter.emit("    test rcx, rcx"); self.emitter.emit(f"    jz {done}"); self.emitter.emit("    cmp rcx, rax"); self.emitter.emit(f"    je {done}"); self.emitter.emit(f"    cmp dword ptr [{p}_exception_owned], 0"); self.emitter.emit(f"    je {done}"); self.emitter.emit("    mov rax, rcx"); self.emitter.emit(f"    call {p}_free_object"); self.emitter.emit(f"{done}:"); self.emitter.emit("    pop rax"); self.emitter.emit(f"    mov qword ptr [{p}_exception_object], rax"); self.emitter.emit(f"    mov dword ptr [{p}_exception_owned], 1"); self.emitter.emit("    test rax, rax"); no=f"{p}_raise_object_no_message"; self.emitter.emit(f"    jz {no}"); self.emitter.emit("    mov rdx, qword ptr [rax+8]"); self.emitter.emit(f"    mov qword ptr [{p}_exception_message], rdx"); self.emitter.emit(f"{no}:"); self.emitter.emit(f"    mov dword ptr [{p}_exception_code], 1"); self.emitter.emit(f"    jmp {p}_exception_unwind")
            self.emitter.emit(f"{p}_raise:"); self.emitter.emit(f"    mov qword ptr [{p}_exception_message], rax"); self.emitter.emit(f"    mov qword ptr [{p}_raw_exception_object+8], rax"); self.emitter.emit(f"    mov rax, {p}_raw_exception_object"); self.emitter.emit(f"    mov qword ptr [{p}_exception_object], rax"); self.emitter.emit(f"    mov dword ptr [{p}_exception_owned], 0"); self.emitter.emit(f"    mov dword ptr [{p}_exception_code], 1"); self.emitter.emit(f"    jmp {p}_exception_unwind")
            self.emitter.emit(f"{p}_reraise:"); self.emitter.emit(f"    cmp qword ptr [{p}_exception_message], 0"); rer=f"{p}_reraise_has_message"; self.emitter.emit(f"    jne {rer}"); self.emitter.emit(f"    mov rax, {p}_generic_exception_message"); self.emitter.emit(f"    mov qword ptr [{p}_exception_message], rax"); self.emitter.emit(f"    mov dword ptr [{p}_exception_code], 1"); self.emitter.emit(f"{rer}:")
            self.emitter.emit(f"{p}_exception_unwind:"); self.emitter.emit(f"    mov rcx, qword ptr [{p}_exception_top]"); self.emitter.emit("    test rcx, rcx"); un=f"{p}_exception_unhandled"; self.emitter.emit(f"    jz {un}"); self.emitter.emit("    mov rdx, qword ptr [rcx+8]"); self.emitter.emit("    mov rax, qword ptr [rcx]"); self.emitter.emit(f"    mov qword ptr [{p}_exception_top], rax"); self.emitter.emit("    mov rbp, qword ptr [rcx+16]"); self.emitter.emit("    mov rsi, qword ptr [rcx+24]"); self.emitter.emit("    mov rbx, qword ptr [rcx+32]"); self.emitter.emit("    mov rdi, qword ptr [rcx+40]"); self.emitter.emit(f"    lea rsp, [rcx+{self._EXCEPTION_FRAME_SIZE}]"); self.emitter.emit("    jmp rdx"); self.emitter.emit(f"{un}:")
            if self.console_mode:
                self.emitter.emit(f"    mov rax, {p}_unhandled_prefix"); self.emitter.emit(f"    call {p}_write_cstring"); nm=f"{p}_exception_no_message"; self.emitter.emit(f"    mov rax, qword ptr [{p}_exception_message]"); self.emitter.emit("    test rax, rax"); self.emitter.emit(f"    jz {nm}"); self.emitter.emit(f"    call {p}_write_cstring"); self.emitter.emit(f"{nm}:"); self.emitter.emit(f"    mov rax, {p}_newline"); self.emitter.emit(f"    call {p}_write_cstring")
            self.emitter.emit("    push 1"); self.emitter.emit("    call ExitProcess"); self.emitter.emit("    ret")
            self.emitter.emit(f"{p}_exception_is_a:"); raw=f"{p}_exception_is_a_raw"; loop=f"{p}_exception_is_a_loop"; match=f"{p}_exception_is_a_match"; no_match=f"{p}_exception_is_a_no_match"; self.emitter.emit("    test rax, rax"); self.emitter.emit(f"    jz {raw}"); self.emitter.emit("    mov rcx, qword ptr [rax]"); self.emitter.emit(f"{loop}:"); self.emitter.emit("    test rcx, rcx"); self.emitter.emit(f"    jz {no_match}"); self.emitter.emit("    cmp rcx, rdx"); self.emitter.emit(f"    je {match}"); self.emitter.emit("    mov rcx, qword ptr [rcx-8]"); self.emitter.emit(f"    jmp {loop}"); self.emitter.emit(f"{raw}:"); self.emitter.emit(f"    mov rcx, {self.exception_base_type.vmt_label}"); self.emitter.emit("    cmp rdx, rcx"); self.emitter.emit(f"    je {match}"); self.emitter.emit(f"{no_match}:"); self.emitter.emit("    xor eax, eax"); self.emitter.emit("    ret"); self.emitter.emit(f"{match}:"); self.emitter.emit("    mov eax, 1"); self.emitter.emit("    ret")
            self.emitter.emit(f"{p}_exception_release:"); self.emitter.emit(f"    mov rax, qword ptr [{p}_exception_object]"); clear=f"{p}_exception_release_clear"; self.emitter.emit("    test rax, rax"); self.emitter.emit(f"    jz {clear}"); self.emitter.emit(f"    cmp dword ptr [{p}_exception_owned], 0"); self.emitter.emit(f"    je {clear}"); self.emitter.emit(f"    call {p}_free_object"); self.emitter.emit(f"{clear}:"); self.emitter.emit("    xor rax, rax"); self.emitter.emit(f"    mov qword ptr [{p}_exception_object], rax"); self.emitter.emit(f"    mov dword ptr [{p}_exception_owned], eax"); self.emitter.emit(f"    mov qword ptr [{p}_exception_message], rax"); self.emitter.emit(f"    mov dword ptr [{p}_exception_code], eax"); self.emitter.emit("    ret")
        if "heap" in self.runtime:
            p=self.symbol_prefix; self.emitter.emit(); self.emitter.emit("; Pascal PE64 Class-Reference Heap Runtime"); self.emitter.emit(f"{p}_new_object:"); self.emitter.emit("    push rbx"); self.emitter.emit("    push rsi"); self.emitter.emit("    mov ebx, eax"); self.emitter.emit("    mov rsi, rdx"); self.emitter.emit("    call GetProcessHeap"); self.emitter.emit("    push rbx"); self.emitter.emit("    push 8"); self.emitter.emit("    push rax"); self.emitter.emit("    call HeapAlloc"); ok=f"{p}_heap_alloc_ok"; self.emitter.emit("    test rax, rax"); self.emitter.emit(f"    jnz {ok}"); self.emitter.emit(f"    mov rax, {p}_oom_message"); self.emitter.emit(f"    jmp {p}_raise"); self.emitter.emit(f"{ok}:"); self.emitter.emit("    mov qword ptr [rax], rsi"); self.emitter.emit("    pop rsi"); self.emitter.emit("    pop rbx"); self.emitter.emit("    ret"); self.emitter.emit(f"{p}_free_object:"); fd=f"{p}_heap_free_done"; self.emitter.emit("    test rax, rax"); self.emitter.emit(f"    jz {fd}"); self.emitter.emit("    push rbx"); self.emitter.emit("    mov rbx, rax"); self.emitter.emit("    call GetProcessHeap"); self.emitter.emit("    push rbx"); self.emitter.emit("    push 0"); self.emitter.emit("    push rax"); self.emitter.emit("    call HeapFree"); self.emitter.emit("    pop rbx"); self.emitter.emit(f"{fd}:"); self.emitter.emit("    ret")
        if self.console_mode:
            p=self.symbol_prefix; self.emitter.emit(); self.emitter.emit(f"{p}_console_init:"); self.emitter.emit("    call AllocConsole")
            for label,handle,std in ((f"{p}_conin_name",f"{p}_stdin_handle",-10),(f"{p}_conout_name",f"{p}_stdout_handle",-11)):
                self.emitter.emit("    push 0"); self.emitter.emit("    push 0"); self.emitter.emit("    push 3"); self.emitter.emit("    push 0"); self.emitter.emit("    push 3"); self.emitter.emit("    push 3221225472"); self.emitter.emit(f"    push {label}"); self.emitter.emit("    call CreateFileA"); ok=self._new_label("console_handle_ok"); self.emitter.emit("    cmp rax, -1"); self.emitter.emit(f"    jne {ok}"); self.emitter.emit(f"    push {std}"); self.emitter.emit("    call GetStdHandle"); self.emitter.emit(f"{ok}:"); self.emitter.emit(f"    mov qword ptr [{handle}], rax")
            self.emitter.emit(f"    push {p}_console_rect"); self.emitter.emit("    push 1"); self.emitter.emit(f"    push qword ptr [{p}_stdout_handle]"); self.emitter.emit("    call SetConsoleWindowInfo"); self.emitter.emit("    push 1638480"); self.emitter.emit(f"    push qword ptr [{p}_stdout_handle]"); self.emitter.emit("    call SetConsoleScreenBufferSize"); self.emitter.emit(f"    push {p}_console_mode"); self.emitter.emit(f"    push qword ptr [{p}_stdout_handle]"); self.emitter.emit("    call GetConsoleMode"); self.emitter.emit(f"    mov eax, dword ptr [{p}_console_mode]"); self.emitter.emit("    or eax, 4"); self.emitter.emit("    push rax"); self.emitter.emit(f"    push qword ptr [{p}_stdout_handle]"); self.emitter.emit("    call SetConsoleMode"); self.emitter.emit("    ret")
        if "readln" in self.runtime:
            p = self.symbol_prefix
            self.emitter.emit()
            self.emitter.emit("; ReadLn: Eingabepuffer wird beim ersten Aufruf dynamisch angelegt")
            self.emitter.emit(f"{p}_readln:")

            # __pas_input_buffer enthaelt nur noch einen 64-Bit-Zeiger. Der
            # eigentliche Speicher wird erst beim ersten ReadLn reserviert.
            # VirtualAlloc(NULL, 4096, MEM_COMMIT|MEM_RESERVE, PAGE_READWRITE)
            # wird ueber den PE64 Stack->Microsoft-x64 Adapter aufgerufen.
            buffer_ready = f"{p}_readln_buffer_ready"
            alloc_ok = f"{p}_readln_buffer_alloc_ok"
            self.emitter.emit(f"    mov rax, qword ptr [{p}_input_buffer]")
            self.emitter.emit("    test rax, rax")
            self.emitter.emit(f"    jnz {buffer_ready}")
            self.emitter.emit("    push 4")       # PAGE_READWRITE
            self.emitter.emit("    push 12288")   # MEM_COMMIT | MEM_RESERVE
            self.emitter.emit("    push 4096")    # eine Windows-Speicherseite
            self.emitter.emit("    push 0")       # lpAddress = NULL
            self.emitter.emit("    call VirtualAlloc")
            self.emitter.emit("    test rax, rax")
            self.emitter.emit(f"    jnz {alloc_ok}")
            self.emitter.emit("    push 1")
            self.emitter.emit("    call ExitProcess")
            self.emitter.emit(f"{alloc_ok}:")
            self.emitter.emit(f"    mov qword ptr [{p}_input_buffer], rax")
            self.emitter.emit(f"{buffer_ready}:")

            # ReadFile darf maximal 4095 Bytes schreiben; Byte 4095 bleibt fuer
            # den abschliessenden NUL-Terminator reserviert.
            self.emitter.emit("    xor eax, eax")
            self.emitter.emit(f"    mov dword ptr [{p}_read_count], eax")
            self.emitter.emit("    push 0")
            self.emitter.emit(f"    push {p}_read_count")
            self.emitter.emit("    push 4095")
            self.emitter.emit(f"    push qword ptr [{p}_input_buffer]")
            self.emitter.emit(f"    push qword ptr [{p}_stdin_handle]")
            self.emitter.emit("    call ReadFile")
            self.emitter.emit(f"    mov ecx, dword ptr [{p}_read_count]")
            self.emitter.emit(f"    mov rax, qword ptr [{p}_input_buffer]")
            self.emitter.emit("    xor edx, edx")
            self.emitter.emit("    mov byte ptr [rax+rcx], dl")
            loop = f"{p}_readln_strip"
            done = f"{p}_readln_done"
            strip = f"{p}_readln_strip_char"
            self.emitter.emit(f"{loop}:")
            self.emitter.emit("    test ecx, ecx")
            self.emitter.emit(f"    jz {done}")
            self.emitter.emit("    dec ecx")
            self.emitter.emit("    movzx edx, byte ptr [rax+rcx]")
            self.emitter.emit("    cmp edx, 10")
            self.emitter.emit(f"    je {strip}")
            self.emitter.emit("    cmp edx, 13")
            self.emitter.emit(f"    jne {done}")
            self.emitter.emit(f"{strip}:")
            self.emitter.emit("    xor edx, edx")
            self.emitter.emit("    mov byte ptr [rax+rcx], dl")
            self.emitter.emit(f"    jmp {loop}")
            self.emitter.emit(f"{done}:")
            self.emitter.emit(f"    mov rax, qword ptr [{p}_input_buffer]")
            self.emitter.emit("    ret")
        if self.runtime.intersection({"print_string","print_int","print_char","print_newline","clear_screen","range_error"}) or (self.console_mode and "exception" in self.runtime):
            p=self.symbol_prefix; self.emitter.emit(); self.emitter.emit(f"{p}_write_cstring:"); self.emitter.emit("    push rax"); self.emitter.emit("    push rax"); self.emitter.emit("    call lstrlenA"); self.emitter.emit("    mov edx, eax"); self.emitter.emit("    pop rax"); self.emitter.emit("    push 0"); self.emitter.emit(f"    push {p}_written"); self.emitter.emit("    push rdx"); self.emitter.emit("    push rax"); self.emitter.emit(f"    push qword ptr [{p}_stdout_handle]"); self.emitter.emit("    call WriteFile"); self.emitter.emit("    ret")
        p=self.symbol_prefix
        if "print_string" in self.runtime: self.emitter.emit(); self.emitter.emit(f"{p}_print_string:"); self.emitter.emit(f"    call {p}_write_cstring"); self.emitter.emit("    ret")
        if "print_int" in self.runtime: self.emitter.emit(); self.emitter.emit(f"{p}_print_int:"); self.emitter.emit("    push rax"); self.emitter.emit(f"    push {p}_fmt_d"); self.emitter.emit(f"    push {p}_format_buffer"); self.emitter.emit("    call wsprintfA"); self.emitter.emit("    add rsp, 24"); self.emitter.emit(f"    mov rax, {p}_format_buffer"); self.emitter.emit(f"    call {p}_write_cstring"); self.emitter.emit("    ret")
        if "print_char" in self.runtime: self.emitter.emit(); self.emitter.emit(f"{p}_print_char:"); self.emitter.emit(f"    mov byte ptr [{p}_char_buffer], al"); self.emitter.emit(f"    mov rax, {p}_char_buffer"); self.emitter.emit(f"    call {p}_write_cstring"); self.emitter.emit("    ret")
        if "print_newline" in self.runtime: self.emitter.emit(); self.emitter.emit(f"{p}_print_newline:"); self.emitter.emit(f"    mov rax, {p}_newline"); self.emitter.emit(f"    call {p}_write_cstring"); self.emitter.emit("    ret")
        if "clear_screen" in self.runtime: self.emitter.emit(); self.emitter.emit(f"{p}_clear_screen:"); self.emitter.emit(f"    mov rax, {p}_clear_sequence"); self.emitter.emit(f"    call {p}_write_cstring"); self.emitter.emit("    ret")
        if "range_error" in self.runtime: self.emitter.emit(); self.emitter.emit(f"{p}_range_error:"); self.emitter.emit(f"    mov rax, {p}_range_message"); self.emitter.emit(f"    call {p}_write_cstring"); self.emitter.emit("    push 1"); self.emitter.emit("    call ExitProcess"); self.emitter.emit("    ret")

    def _emit_data(self) -> None:
        p = self.symbol_prefix
        initialized_vars = []
        bss_vars = []
        for var in self.variable_order:
            initial = getattr(var, "c_initial_value", None)
            if initial in (None, 0):
                bss_vars.append(var)
            else:
                initialized_vars.append(var)

        # Initialisierte Daten: VMTs, konstante Strings, Tabellen und explizit
        # mit einem Nicht-Nullwert initialisierte globale Variablen.
        self.emitter.emit()
        self.emitter.emit("section .data")
        self.emitter.emit("align 8")
        if self.class_types:
            self.emitter.emit("; Virtuelle Methodentabellen (VMT), 64 Bit")
            for ct in self.class_types:
                base = ct.base_type.vmt_label if ct.base_type is not None else "0"
                self.emitter.emit(f"{ct.vmt_label}__parent: dq {base}")
                self.emitter.emit(f"{ct.vmt_label}:")
                if ct.vmt_methods:
                    for method in ct.vmt_methods:
                        self.emitter.emit(f"    dq {method.label}")
                else:
                    self.emitter.emit("    dq 0")
            self.emitter.emit("align 8")
        if "exception" in self.runtime:
            # raw_exception_object contains a VMT relocation and therefore is
            # initialized data. The mutable exception state itself lives in BSS.
            self.emitter.emit(f"{p}_raw_exception_object: dq {self.exception_base_type.vmt_label}, 0")
            self.emitter.emit(f"{p}_generic_exception_message: db 69,120,99,101,112,116,105,111,110,0")
            self.emitter.emit(f"{p}_unhandled_prefix: db 85,110,104,97,110,100,108,101,100,32,101,120,99,101,112,116,105,111,110,58,32,0")
            self.emitter.emit(f"{p}_nil_message: db 78,105,108,32,99,108,97,115,115,32,114,101,102,101,114,101,110,99,101,0")
            self.emitter.emit(f"{p}_oom_message: db 79,117,116,32,111,102,32,109,101,109,111,114,121,0")
        if self.console_mode:
            self.emitter.emit(f"{p}_conin_name: db 67,79,78,73,78,36,0")
            self.emitter.emit(f"{p}_conout_name: db 67,79,78,79,85,84,36,0")
            self.emitter.emit(f"{p}_console_rect: dw 0,0,79,24")
        self.emitter.emit(f"{p}_fmt_s: db 37,115,0")
        self.emitter.emit(f"{p}_fmt_d: db 37,100,0")
        self.emitter.emit(f"{p}_fmt_c: db 37,99,0")
        self.emitter.emit(f"{p}_newline: db 13,10,0")
        self.emitter.emit(f"{p}_clear_sequence: db 27,91,50,74,27,91,72,0")
        self.emitter.emit(f"{p}_range_message: db 82,97,110,103,101,32,101,114,114,111,114,13,10,0")

        if initialized_vars:
            self.emitter.emit()
            self.emitter.emit(f"; {self.language_name}-Variablen mit explizitem Initialwert")
            for var in initialized_vars:
                comment = "intern" if var.internal else var.name
                initial = int(getattr(var, "c_initial_value", 0) or 0)
                size = self._pe32_storage_size(var.type_info)
                if size == 8:
                    self.emitter.emit(f"{var.label}: dq {initial & 0xFFFFFFFFFFFFFFFF} ; {comment}: {var.type_info.name}")
                elif size == 4:
                    self.emitter.emit(f"{var.label}: dd {initial & 0xFFFFFFFF} ; {comment}: {var.type_info.name}")
                elif size == 2:
                    self.emitter.emit(f"{var.label}: dw {initial & 0xFFFF} ; {comment}: {var.type_info.name}")
                elif size == 1:
                    self.emitter.emit(f"{var.label}: db {initial & 0xFF} ; {comment}: {var.type_info.name}")
                else:
                    # Aggregate initializers are not emitted by this backend yet.
                    self.emitter.emit(f"{var.label}: db " + ", ".join("0" for _ in range(size)) +
                                      f" ; {comment}: {var.type_info.name}")

        if self.strings:
            self.emitter.emit()
            self.emitter.emit("; Nullterminierte Windows-Latin-1-Zeichenketten")
            for data, label in self.strings.items():
                self.emitter.emit(f"{label}: db " + ", ".join(str(v) for v in data + b"\0"))

        # Uninitialisierte/Null-initialisierte Daten bekommen eine echte BSS-
        # Sektion. Der COFF64/PE32+-Writer reserviert dafür VirtualSize, schreibt
        # aber keinerlei Nullbytes in die .o/.exe/.dll-Datei. Windows liefert
        # die Seiten beim Laden automatisch mit Null initialisiert.
        need_bss = bool(bss_vars or "exception" in self.runtime or self.console_mode)
        if need_bss:
            self.emitter.emit()
            self.emitter.emit("section .bss")
            self.emitter.emit("align 8")
            if "exception" in self.runtime:
                self.emitter.emit(f"{p}_exception_top: resq 1")
                self.emitter.emit(f"{p}_exception_object: resq 1")
                self.emitter.emit(f"{p}_exception_owned: resd 1")
                self.emitter.emit("align 8")
                self.emitter.emit(f"{p}_exception_message: resq 1")
                self.emitter.emit(f"{p}_exception_code: resd 1")
            if self.console_mode:
                self.emitter.emit("align 8")
                self.emitter.emit(f"{p}_stdin_handle: resq 1")
                self.emitter.emit(f"{p}_stdout_handle: resq 1")
                self.emitter.emit(f"{p}_console_mode: resd 1")
                self.emitter.emit(f"{p}_written: resd 1")
                self.emitter.emit(f"{p}_format_buffer: resb 32")
                self.emitter.emit(f"{p}_char_buffer: resb 2")
                if "readln" in self.runtime:
                    self.emitter.emit(f"{p}_read_count: resd 1")
                    self.emitter.emit("align 8")
                    # The 4-KiB ReadLn payload remains VirtualAlloc-backed; BSS
                    # contains only the nullable pointer to that allocation.
                    self.emitter.emit(f"{p}_input_buffer: resq 1")
            if bss_vars:
                self.emitter.emit()
                self.emitter.emit(f"; {self.language_name}-Nullvariablen (.bss, keine Raw-Bytes)")
                for var in bss_vars:
                    comment = "intern" if var.internal else var.name
                    size = int(self._pe32_storage_size(var.type_info))
                    align = 8 if size >= 8 else (4 if size >= 4 else (2 if size >= 2 else 1))
                    if align > 1:
                        self.emitter.emit(f"align {align}")
                    self.emitter.emit(f"{var.label}: resb {size} ; {comment}: {var.type_info.name}")

    def generate(self) -> GeneratedAssembly:
        generated=super().generate()
        return replace(generated,assembly=_normalize_pe64_assembly_text(generated.assembly))


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

    def _class_pointer_size(self) -> int:
        return 4

    def _aggregate_size_limit(self) -> int:
        return 65535

    def _compile_set_builtin(self, expression: CallExpression) -> Optional[_PascalType]:
        designator = self._as_designator(expression.designator, expression.position)
        if designator.selectors:
            return None
        name = self._key(designator.name)
        if name in {"emptyset", "setof", "setrange", "setunion"}:
            self._emit_load_literal(self._evaluate_set_mask(expression), expression.position.line)
            return UNTYPED_SET_TYPE
        if name != "setcontains":
            return None
        self._require_argument_count(designator.name, expression.arguments, 2, expression.position)
        if self._expression_type(expression.arguments[0]).kind != "set":
            raise self._error("SetContains erwartet als erstes Argument einen Set-Wert.", expression.arguments[0].position)
        value = int(self._evaluate_constant(expression.arguments[1]))
        if not 0 <= value <= 15:
            raise self._error(f"Set-Element {value} liegt außerhalb 0..15.", expression.arguments[1].position)
        line = expression.position.line
        self._compile_expr(expression.arguments[0])
        self.emitter.emit(f"    andi.w #${1 << value:04X},d0", line)
        false_label = self._new_label("set_contains_false")
        end_label = self._new_label("set_contains_end")
        self.emitter.emit(f"    beq {false_label}", line)
        self.emitter.emit("    moveq #1,d0", line)
        self.emitter.emit(f"    bra {end_label}", line)
        self.emitter.emit(f"{false_label}:", line)
        self.emitter.emit("    moveq #0,d0", line)
        self.emitter.emit(f"{end_label}:", line)
        return BOOLEAN_TYPE

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
            if isinstance(expression, DesignatorExpression):
                property_type = self._compile_property_read(expression)
                if property_type is not None:
                    return property_type
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
            if left_type.kind == "set" and right_type.kind == "set":
                result_type = left_type if left_type is not UNTYPED_SET_TYPE else right_type
                if operator == "+":
                    self.emitter.emit("    or.w d1,d0", line)
                    return result_type
                if operator == "*":
                    self.emitter.emit("    and.w d1,d0", line)
                    return result_type
                if operator == "-":
                    self.emitter.emit("    eori.w #$FFFF,d1", line)
                    self.emitter.emit("    and.w d1,d0", line)
                    return result_type
                if operator in {"=", "<>"}:
                    self._emit_comparison(operator, False, line)
                    return BOOLEAN_TYPE
                raise self._error(f"Operator {operator} ist für Sets nicht zulässig.", expression.position)
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
        set_result = self._compile_set_builtin(expression)
        if set_result is not None:
            return set_result
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
        if method.virtual:
            if method.vmt_slot is None:
                raise self._error("Interner Fehler: virtuelle Methode ohne VMT-Slot.", position)
            self.emitter.emit("    move.l (a5),a0", line)
            offset = method.vmt_slot * 4
            if offset:
                self.emitter.emit(f"    move.l ${offset:04X}(a0),a0", line)
            else:
                self.emitter.emit("    move.l (a0),a0", line)
            self.emitter.emit("    jsr (a0)", line)
        else:
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
        if name in {"__pas_raise", "__pas_reraise"}:
            raise self._error(
                "Exception-Transport mit RAISE ist derzeit nur fuer Windows PE32 implementiert.",
                statement.position,
            )
        if name in {"include", "exclude"}:
            self._compile_set_mutation(statement, name == "include")
            return
        if self._compile_implicit_free(statement):
            return

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
            if routine.result_type is not None:
                raise self._error(
                    f"{routine.name} ist eine Funktion und muss in einem Ausdruck verwendet werden.",
                    statement.position,
                )
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
                    if variable.type_info.kind == "class":
                        assert variable.type_info.vmt_label is not None
                        self.emitter.emit(
                            f"    lea {variable.label}(pc),a0",
                            implementation.position.line,
                        )
                        self.emitter.emit(
                            f"    lea {variable.type_info.vmt_label}(pc),a1",
                            implementation.position.line,
                        )
                        self.emitter.emit("    move.l a1,(a0)", implementation.position.line)
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

        if self.class_types:
            self.emitter.emit()
            self.emitter.emit("; Virtuelle Methodentabellen (VMT)")
            for class_type in self.class_types:
                self.emitter.emit("    even")
                assert class_type.vmt_label is not None
                self.emitter.emit(f"{class_type.vmt_label}:")
                if class_type.vmt_methods:
                    for method in class_type.vmt_methods:
                        self.emitter.emit(f"    dc.l {method.label}")
                else:
                    self.emitter.emit("    dc.l 0")

        if self.variable_order:
            self.emitter.emit()
            self.emitter.emit(f"; {self.language_name}-Variablen")
            for variable in self.variable_order:
                self.emitter.emit("    even")
                comment = "intern" if variable.internal else variable.name
                initial_value = getattr(variable, "c_initial_value", None)
                if variable.type_info.kind == "class":
                    assert variable.type_info.vmt_label is not None
                    self.emitter.emit(
                        f"{variable.label}: dc.l {variable.type_info.vmt_label} "
                        f"; {comment}: {variable.type_info.name}, VMT"
                    )
                    remaining = variable.type_info.size - self._class_pointer_size()
                    if remaining > 0:
                        self.emitter.emit(f"    ds.b {remaining}")
                    continue
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
    if normalized_target in {"pe64", "win64", "windows64", "windows-pe64"}:
        return (
            "; Von Pascal erzeugtes Windows-PE64-Unit-Modul\n"
            f"; Unit: {unit_name}\n"
            "bits 64\n"
            f"global __unit_{safe_name}\n"
            f"__unit_{safe_name}:\n"
            "    ret\n"
        )
    if normalized_target in {"pe32", "win32", "windows", "windows-pe32"}:
        return (
            "; Von Pascal erzeugtes Windows-PE32-Unit-Modul\n"
            f"; Unit: {unit_name}\n"
            "bits 32\n"
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
) -> GeneratedAssembly:
    """Kompiliert eine direkt geöffnete Pascal-Unit.

    Die Unit wird nicht als PROGRAM an den ANTLR-Parser übergeben. Stattdessen
    werden UNIT/INTERFACE/IMPLEMENTATION zuerst zerlegt, die PUI-Datei wird
    geschrieben und ein separates Unit-ASM-Modul erzeugt.
    """
    preprocessor = PascalPreprocessor(predefined_macros)
    processed = preprocessor.process(source, filename=filename)
    (
        unused_transformed,
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
    if source_path is not None:
        pui_path = source_path.with_suffix(".pui")
        pui_document = _pui_document(
            unit_name=unit_name,
            interface_source=interface_source,
            interface_units=interface_units,
            source_path=source_path,
            guard=_pascal_guard_macro(source),
        )
        _write_pui_document(pui_path, pui_document)

    # Abhängigkeiten werden bereits beim Unit-Build geprüft und ihre PUI-Dateien
    # bei Bedarf erzeugt. Zielabhängige ASM-Module werden anschließend anhand
    # der PUI statisch mit dem erzeugten Unit-Modul zusammengeführt.
    resolver = _PascalUnitResolver(
        filename=filename,
        include_paths=include_paths,
        preprocessor=preprocessor,
        target=target,
    )
    for dependency in interface_units + implementation_units:
        resolver.resolve(dependency)

    # Eine Interface-Unit darf leer implementiert sein. Enthält sie bereits
    # echten Pascal-Code, muss dieser zukünftig als globales Unit-Modul durch
    # den Mehrdateien-Linker übersetzt werden; er darf hier nicht stillschweigend
    # verworfen werden.
    implementation_mask = _pascal_code_mask(implementation_source)
    if re.search(r"\b(procedure|function|constructor|destructor)\b", implementation_mask, re.IGNORECASE):
        raise C64PascalError(
            "Globale Pascal-Routinen im IMPLEMENTATION-Teil einer Unit werden "
            "vom separaten Unit-Linker noch nicht unterstützt. Die Unit-PUI "
            "wurde bereits erzeugt; implementiere die Routinen derzeit in den "
            "getrennten C-/ASM-Modulen."
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
    if normalized_target in {"pe32", "win32", "windows", "windows-pe32", "pe64", "win64", "windows64", "windows-pe64"}:
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
    if str(target).strip().casefold() not in {"pe32", "win32", "windows", "windows-pe32"}:
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



def _inject_console_breakpoints(
    program: PascalProgram,
    breakpoint_lines: Iterable[int],
) -> PascalProgram:
    """Fügt ReadLn-Haltepunkte vor AST-Anweisungen bestimmter Quellzeilen ein.

    Die Quelle selbst wird nicht verändert. Dadurch bleiben ANTLR-Positionen,
    Compilerfehler und die Zuordnung Gutter -> Pascal-Zeile stabil.
    """
    requested = {
        int(line) for line in breakpoint_lines
        if int(line) > 0
    }
    if not requested:
        return program

    consumed = set()

    def pause_statement(position: SourcePosition) -> CallStatement:
        return CallStatement(
            position,
            DesignatorExpression(position, "readln", ()),
            (),
        )

    def instrument(statement: Statement) -> Statement:
        line = int(statement.position.line)
        trigger_here = line in requested and line not in consumed
        if trigger_here:
            consumed.add(line)

        if isinstance(statement, CompoundStatement):
            transformed = replace(
                statement,
                statements=tuple(instrument(item) for item in statement.statements),
            )
        elif isinstance(statement, IfStatement):
            transformed = replace(
                statement,
                then_statement=instrument(statement.then_statement),
                else_statement=(
                    instrument(statement.else_statement)
                    if statement.else_statement is not None else None
                ),
            )
        elif isinstance(statement, WhileStatement):
            transformed = replace(statement, body=instrument(statement.body))
        elif isinstance(statement, RepeatStatement):
            transformed = replace(
                statement,
                statements=tuple(instrument(item) for item in statement.statements),
            )
        elif isinstance(statement, ForStatement):
            transformed = replace(statement, body=instrument(statement.body))
        elif isinstance(statement, TryFinallyStatement):
            transformed = replace(
                statement,
                try_statement=instrument(statement.try_statement),
                finally_statement=instrument(statement.finally_statement),
            )
        elif isinstance(statement, TryExceptStatement):
            transformed_handlers = tuple(
                replace(handler, body=instrument(handler.body))
                for handler in statement.handlers
            )
            transformed = replace(
                statement,
                try_statement=instrument(statement.try_statement),
                except_statement=(
                    instrument(statement.except_statement)
                    if statement.except_statement is not None else None
                ),
                handlers=transformed_handlers,
            )
        else:
            transformed = statement

        if not trigger_here:
            return transformed
        return CompoundStatement(
            statement.position,
            (pause_statement(statement.position), transformed),
        )

    methods = tuple(
        replace(method, body=instrument(method.body))
        for method in program.methods
    )
    return replace(
        program,
        body=instrument(program.body),
        methods=methods,
    )


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
    windows_application_mode: Optional[str] = None,
    breakpoint_lines: Iterable[int] = (),
) -> GeneratedAssembly:
    """Parst PROGRAM-, UNIT- oder PE32-LIBRARY-Quellen und erzeugt Assembler."""
    source_kind = _pascal_source_kind(source)
    normalized_target = str(target).strip().casefold()
    del cpu_model, fpu_model

    if source_kind == "unit":
        return _compile_pascal_unit_interface(
            source,
            filename=filename,
            include_paths=include_paths,
            predefined_macros=predefined_macros,
            target=target,
        )

    library_name: Optional[str] = None
    library_exports: Dict[str, str] = {}
    frontend_source = source
    if source_kind == "library":
        if normalized_target not in {"pe32", "win32", "windows", "windows-pe32", "pe64", "win64", "windows64", "windows-pe64"}:
            raise C64PascalError(
                "Pascal LIBRARY wird derzeit ausschließlich für Windows PE32/PE64 unterstützt."
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
    )
    if normalized_target in {"c64", "c-64", "6510"}:
        generated = _CodeGenerator(program).generate()
    elif normalized_target in {"amiga", "amiga500", "a500", "m68k", "68000"}:
        generated = _AmigaCodeGenerator(program).generate()
    elif normalized_target in {"pe32", "win32", "windows", "windows-pe32", "pe64", "win64", "windows64", "windows-pe64"}:
        if windows_application_mode is None:
            uses_graphics = bool(
                re.search(r"\bInitGraphics\s*\(", source, re.IGNORECASE)
            )
            selected_mode = graphics_backend if uses_graphics else "Console"
        else:
            selected_mode = str(windows_application_mode).strip() or "Console"
        mode_key = selected_mode.casefold()
        console_mode = mode_key in {"console", "konsole"}
        if console_mode and source_kind != "library":
            program = _inject_console_breakpoints(program, breakpoint_lines)
        if mode_key in {"direct3d", "d3d", "d3d9"}:
            graphics_backend = "Direct3D"
        elif mode_key in {"direct2d", "d2d"}:
            graphics_backend = "Direct2D"
        generator_class = _PE64CodeGenerator if normalized_target in {"pe64", "win64", "windows64", "windows-pe64"} else _PE32CodeGenerator
        generated = generator_class(
            program,
            graphics_backend=graphics_backend,
            console_mode=(console_mode and source_kind != "library"),
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
    )
