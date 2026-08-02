"""Kleiner ANTLR-basierter Pascal-zu-MOS-6510-Compiler.

Der Compiler erzeugt absichtlich lesbaren Assembler. Die zweite Stufe ist der
in ``d64_dism(5).py`` enthaltene Mehrpass-Assembler, der daraus ein C64-PRG
mit BASIC-SYS-Startzeile erstellt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from .generated.C64PascalLexer import C64PascalLexer
from .generated.C64PascalParser import C64PascalParser
from .generated.C64PascalParserVisitor import C64PascalParserVisitor


ScalarValue = Union[int, str, bool]


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
class PascalProgram:
    name: str
    constants: Tuple[ConstDeclaration, ...]
    variables: Tuple[VarDeclaration, ...]
    body: CompoundStatement
    types: Tuple[TypeDeclaration, ...] = ()
    methods: Tuple[MethodImplementation, ...] = ()


@dataclass(frozen=True)
class GeneratedAssembly:
    program_name: str
    assembly: str
    source_map: Dict[int, int]
    variable_count: int
    string_count: int

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


def parse_pascal(source: str, *, filename: str = "<Pascal-Editor>") -> PascalProgram:
    del filename
    listener = _RaisingErrorListener()
    lexer = C64PascalLexer(InputStream(source))
    lexer.removeErrorListeners()
    lexer.addErrorListener(listener)
    parser = C64PascalParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(listener)
    tree = parser.compilationUnit()
    return _AstBuilder().visit(tree)


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

        self._prepare_method_implementations()

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
            try:
                index_value = self._evaluate_constant(selector.expression)
            except C64PascalError:
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
            self._require_argument_count(designator.name, statement.arguments, 0, statement.position)
            self.emitter.emit("    lda #$93", line)
            self.emitter.emit("    jsr $FFD2", line)
            return
        if name == "poke":
            self._require_argument_count(designator.name, statement.arguments, 2, statement.position)
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
            self._require_argument_count(designator.name, statement.arguments, 1, statement.position)
            argument = statement.arguments[0]
            if not isinstance(argument, (NameExpression, DesignatorExpression)):
                raise self._error(f"{designator.name} erwartet eine Variable.", statement.position)
            target = self._as_designator(argument)
            target_type = self._resolve_storage(target).type_info
            if target_type not in {INTEGER_TYPE, BYTE_TYPE, CHAR_TYPE} and target_type.kind != "enum":
                raise self._error(f"{designator.name} erwartet einen ordinalen Wert.", argument.position)
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
            self._require_argument_count(designator.name, statement.arguments, 0, statement.position)
            label = self._new_label("halt")
            self.emitter.emit(f"{label}:", line)
            self.emitter.emit(f"    jmp {label}", line)
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
                if variable.type_info.size == 2:
                    directive = ".word 0"
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


def compile_pascal_to_assembly(
    source: str,
    *,
    filename: str = "<Pascal-Editor>",
) -> GeneratedAssembly:
    """Parst Pascal mit ANTLR und erzeugt MOS-6510-Assembler."""
    program = parse_pascal(source, filename=filename)
    return _CodeGenerator(program).generate()
