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
class MethodDeclaration:
    kind: str
    name: str
    parameters: Tuple[ParameterDeclaration, ...]
    result_type_name: Optional[str]
    position: SourcePosition


@dataclass(frozen=True)
class ClassTypeSpecification(TypeSpecification):
    base_type_name: Optional[str]
    fields: Tuple[FieldDeclaration, ...]
    methods: Tuple[MethodDeclaration, ...]


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
            "classType",
        ):
            child = getattr(ctx, child_name)()
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

    def visitClassType(self, ctx):
        fields = []
        methods = []
        for member in ctx.classMember():
            if member.fieldDeclaration():
                fields.append(self.visit(member.fieldDeclaration()))
            elif member.methodDeclaration():
                methods.append(self.visit(member.methodDeclaration()))
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
        )

    def visitFieldDeclaration(self, ctx):
        return FieldDeclaration(
            tuple(token.getText() for token in ctx.identifierList().IDENTIFIER()),
            ctx.typeIdentifier().getText().casefold(),
            _position(ctx),
        )

    def visitMethodDeclaration(self, ctx):
        return MethodDeclaration(
            ctx.routineKind().getText().casefold(),
            ctx.IDENTIFIER().getText(),
            tuple(self.visit(ctx.formalParameters())) if ctx.formalParameters() else (),
            ctx.typeIdentifier().getText().casefold() if ctx.typeIdentifier() else None,
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
        if ctx.STRING_LITERAL():
            text = ctx.STRING_LITERAL().getText()[1:-1].replace("''", "'")
            return LiteralExpression(position, text)
        if ctx.TRUE():
            return LiteralExpression(position, True)
        if ctx.FALSE():
            return LiteralExpression(position, False)
        if ctx.designator():
            designator = self.visit(ctx.designator())
            if ctx.LPAREN():
                arguments = self.visit(ctx.argumentList()) if ctx.argumentList() else []
                return CallExpression(position, designator, tuple(arguments))
            return designator
        return self.visit(ctx.expression())

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


def _parse_pascal_program(source: str) -> PascalProgram:
    listener = _RaisingErrorListener()
    lexer = C64PascalLexer(InputStream(source))
    lexer.removeErrorListeners()
    lexer.addErrorListener(listener)
    parser = C64PascalParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(listener)
    tree = parser.compilationUnit()
    return _AstBuilder().visit(tree)


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

    def replace_routine(match: re.Match[str]) -> str:
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
    base_type: Optional["_PascalType"] = None

    @property
    def scalar(self) -> bool:
        return self.kind in {"scalar", "enum", "string"}

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
    implementation: Optional[MethodImplementation] = None
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



INTEGER_TYPE = _PascalType("integer", 2, True)
BYTE_TYPE = _PascalType("byte", 1, False)
CHAR_TYPE = _PascalType("char", 1, False)
BOOLEAN_TYPE = _PascalType("boolean", 1, False)
STRING_TYPE = _PascalType("string", 2, False)

_TYPES = {
    item.name: item
    for item in (INTEGER_TYPE, BYTE_TYPE, CHAR_TYPE, BOOLEAN_TYPE)
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
        self.current_method: Optional[_MethodInfo] = None
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
                size = element_count * element_type.size
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
                self.types[key] = type_info
                self._install_fields(type_info, specification.fields)
                if type_info.size == 0:
                    type_info.size = 1
                self._install_methods(type_info, specification.methods)
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
                )
                owner.size += field_type.size
                if owner.size > 256:
                    raise self._error(
                        f"{owner.name} ist größer als 256 Bytes.",
                        declaration.position,
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
            method = _MethodInfo(
                owner,
                declaration.kind,
                declaration.name,
                parameters,
                result_type,
                declaration.position,
                f"__pas_method_{self._safe_name(owner.name)}_{self._safe_name(declaration.name)}",
            )
            owner.methods[key] = method
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
            type_info = field_info.type_info
            offset = field_info.offset
            use_self = True
        else:
            raise self._error(f"Variable nicht gefunden: {designator.name}.", designator.position)

        dynamic = None
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
                offset += (index_value - type_info.lower_bound) * type_info.element_type.size
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
                    type_info.element_type.size,
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
        )

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

    def _expression_type(self, expression: Expression) -> _PascalType:
        if isinstance(expression, LiteralExpression):
            return self._constant_type(expression.value)
        if isinstance(expression, (NameExpression, DesignatorExpression)):
            key = self._key(expression.name)
            if not isinstance(expression, DesignatorExpression) or not expression.selectors:
                if key in self.constants:
                    return self.constant_types.get(key, self._constant_type(self.constants[key]))
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

        if dynamic is not None:
            self.emitter.emit("    add ecx, edx", line)
        if access.constant_offset:
            self.emitter.emit(f"    add ecx, {int(access.constant_offset)}", line)

    def _emit_load_access(self, access: _StorageAccess, line: int) -> None:
        if access.type_info.size not in {1, 2, 4}:
            raise self._error(
                "Das PE32-Backend kann derzeit skalare 8-, 16- und 32-Bit-Werte laden.",
                access.position,
            )
        self._emit_address(access, line)
        if access.type_info.size == 1:
            self.emitter.emit("    movzx eax, byte ptr [ecx]", line)
        elif access.type_info.size == 2:
            instruction = "movsx" if access.type_info.signed else "movzx"
            self.emitter.emit(f"    {instruction} eax, word ptr [ecx]", line)
        else:
            self.emitter.emit("    mov eax, dword ptr [ecx]", line)

    def _emit_store_access(self, access: _StorageAccess, line: int) -> None:
        if access.type_info.size not in {1, 2, 4}:
            raise self._error(
                "Das PE32-Backend kann derzeit skalare 8-, 16- und 32-Bit-Werte speichern.",
                access.position,
            )
        self.emitter.emit("    push eax", line)
        self._emit_address(access, line)
        self.emitter.emit("    pop eax", line)
        if access.type_info.size == 1:
            self.emitter.emit("    mov byte ptr [ecx], al", line)
        elif access.type_info.size == 2:
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
            if key in self.constants and not has_selectors:
                value = self.constants[key]
                if isinstance(value, str):
                    label = self._string_label(value, expression.position)
                    self.emitter.emit(f"    mov eax, {label}", line)
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
                        return self._compile_method_call(method, receiver, (), expression.position)
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
            if not argument_type.scalar or not parameter.type_info.scalar:
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
        self._emit_address(receiver, line)
        self.emitter.emit("    mov esi, ecx", line)

    def _compile_method_call(self, method, receiver, arguments, position):
        self._require_argument_count(method.name, arguments, len(method.parameters), position)
        line = position.line
        for argument, parameter, variable in zip(arguments, method.parameters, method.parameter_variables):
            argument_type = self._compile_expr(argument)
            if not argument_type.scalar or not parameter.type_info.scalar:
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

    def _compile_call_statement(self, statement: CallStatement) -> None:
        designator = self._as_designator(statement.designator, statement.position)
        name = self._key(designator.name) if not designator.selectors else ""
        line = statement.position.line
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
                    self.emitter.emit("    xor eax, eax", implementation.position.line)
                    self._store_variable(variable, implementation.position.line)
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
            self.emitter.emit("    push 1"); self.emitter.emit("    call ExitProcess"); self.emitter.emit("    ret")

    def _emit_data(self) -> None:
        self.emitter.emit(); self.emitter.emit("align 4")
        if self.console_mode:
            self.emitter.emit(f"{self.symbol_prefix}_stdout_handle: dd 0")
            self.emitter.emit(f"{self.symbol_prefix}_console_rect: dw 0, 0, 79, 24")
            self.emitter.emit(f"{self.symbol_prefix}_console_mode: dd 0")
            self.emitter.emit(f"{self.symbol_prefix}_written: dd 0")
            self.emitter.emit(f"{self.symbol_prefix}_format_buffer: db " + ", ".join(["0"] * 32))
            self.emitter.emit(f"{self.symbol_prefix}_char_buffer: db 0, 0")
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
                if variable.type_info.size == 1:
                    directive = "db"; value = int(initial_value or 0) & 0xFF
                elif variable.type_info.size == 2:
                    directive = "dw"; value = int(initial_value or 0) & 0xFFFF
                elif variable.type_info.size == 4:
                    directive = "dd"; value = int(initial_value or 0) & 0xFFFFFFFF
                else:
                    directive = "db"; value = None
                if value is None:
                    values = ", ".join("0" for _ in range(variable.type_info.size))
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
                "GetConsoleMode", "SetConsoleMode", "WriteFile", "lstrlenA",
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
                if result_type == STRING_TYPE:
                    raise self._error(
                        "String-Variablen werden im PE32-Backend noch nicht unterstützt.",
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
                raise self._error("String-Variablen werden im PE32-Backend noch nicht unterstuetzt.", initializer.position)
            if not variable.type_info.scalar:
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
    if normalized_target in {"pe32", "win32", "windows", "windows-pe32"}:
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
        if normalized_target not in {"pe32", "win32", "windows", "windows-pe32"}:
            raise C64PascalError(
                "Pascal LIBRARY wird derzeit ausschließlich für Windows PE32 unterstützt."
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
    elif normalized_target in {"pe32", "win32", "windows", "windows-pe32"}:
        uses_graphics = bool(re.search(r"\bInitGraphics\s*\(", source, re.IGNORECASE))
        generated = _PE32CodeGenerator(
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
    )
