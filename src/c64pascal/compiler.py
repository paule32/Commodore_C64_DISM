# ----------------------------------------------------------------------------
# Kleiner ANTLR-basierter Pascal-zu-MOS-6510-Compiler.
# (c) 2026 by Jens Kallup - paule32
# alle Rechte vorbehalten.
#
# Der Compiler erzeugt lesbaren Assembler. Die zweite Stufe ist der
# in "d64_dism.py" enthaltene Mehrpass-Assembler, der daraus ein C64-PRG
# mit BASIC-SYS-Startzeile erstellt.
# ----------------------------------------------------------------------------
from __future__ import annotations

from dataclasses import dataclass, field
from typing      import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from antlr4                     import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from .generated.C64PascalLexer         import C64PascalLexer
from .generated.C64PascalParser        import C64PascalParser
from .generated.C64PascalParserVisitor import C64PascalParserVisitor

ScalarValue = Union[int, str, bool]

# ----------------------------------------------------------------------------
# Pascal-Fehler mit genauer Position im Quelltext.
# ----------------------------------------------------------------------------
class C64PascalError(Exception):
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
class CallExpression(Expression):
    name: str
    arguments: Tuple[Expression, ...]


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
    name: str
    expression: Expression


@dataclass(frozen=True)
class CallStatement(Statement):
    name: str
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
class ConstDeclaration:
    name: str
    expression: Expression
    position: SourcePosition


@dataclass(frozen=True)
class VarDeclaration:
    names: Tuple[str, ...]
    type_name: str
    initializer: Optional[Expression]
    position: SourcePosition


@dataclass(frozen=True)
class PascalProgram:
    name: str
    constants: Tuple[ConstDeclaration, ...]
    variables: Tuple[VarDeclaration, ...]
    body: CompoundStatement


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
        constants, variables, body = self.visit(ctx.block())
        return PascalProgram(
            ctx.IDENTIFIER().getText(),
            tuple(constants),
            tuple(variables),
            body,
        )

    def visitBlock(self, ctx):
        constants = self.visit(ctx.constSection()) if ctx.constSection() else []
        variables = self.visit(ctx.varSection()) if ctx.varSection() else []
        return constants, variables, self.visit(ctx.compoundStatement())

    def visitConstSection(self, ctx):
        return [self.visit(item) for item in ctx.constDefinition()]

    def visitConstDefinition(self, ctx):
        return ConstDeclaration(
            ctx.IDENTIFIER().getText(),
            self.visit(ctx.expression()),
            _position(ctx),
        )

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
            ctx.IDENTIFIER().getText(),
            self.visit(ctx.expression()),
        )

    def visitCallStatement(self, ctx):
        arguments = self.visit(ctx.argumentList()) if ctx.argumentList() else []
        return CallStatement(
            _position(ctx),
            ctx.IDENTIFIER().getText(),
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
        if ctx.IDENTIFIER():
            name = ctx.IDENTIFIER().getText()
            if ctx.LPAREN():
                arguments = self.visit(ctx.argumentList()) if ctx.argumentList() else []
                return CallExpression(position, name, tuple(arguments))
            return NameExpression(position, name)
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


@dataclass(frozen=True)
class _PascalType:
    name: str
    size: int
    signed: bool = False


INTEGER_TYPE = _PascalType("integer", 2, True )
BYTE_TYPE    = _PascalType("byte"   , 1, False)
CHAR_TYPE    = _PascalType("char"   , 1, False)
BOOLEAN_TYPE = _PascalType("boolean", 1, False)
STRING_TYPE  = _PascalType("string" , 2, False)

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


@dataclass
class _Emitter:
    lines: List[str] = field(default_factory=list)
    source_map: Dict[int, int] = field(default_factory=dict)

    def emit(self, text: str = "", source_line: int = 0) -> None:
        self.lines.append(text)
        if source_line:
            self.source_map[len(self.lines)] = int(source_line)


class _CodeGenerator:
    ZP_LEFT_LO = "$FB"
    ZP_LEFT_HI = "$FC"
    ZP_RIGHT_LO = "$FD"
    ZP_RIGHT_HI = "$FE"

    def __init__(self, program: PascalProgram) -> None:
        self.program = program
        self.emitter = _Emitter()
        self.constants: Dict[str, ScalarValue] = {}
        self.variables: Dict[str, _Variable] = {}
        self.variable_order: List[_Variable] = []
        self.initializers: List[Tuple[_Variable, Expression]] = []
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
        if key in self.variables or key in self.constants:
            raise self._error(f"Bezeichner mehrfach deklariert: {name}.", position)
        label_prefix = "tmp" if internal else "var"
        variable = _Variable(
            name,
            f"__pas_{label_prefix}_{self._safe_name(name)}_{len(self.variable_order)}",
            type_info,
            position,
            internal,
        )
        self.variables[key] = variable
        self.variable_order.append(variable)
        return variable

    def _evaluate_constant(self, expression: Expression) -> ScalarValue:
        if isinstance(expression, LiteralExpression):
            return expression.value
        if isinstance(expression, NameExpression):
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

    def _prepare_symbols(self) -> None:
        for declaration in self.program.constants:
            key = self._key(declaration.name)
            if key in self.constants or key in self.variables:
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

        for declaration in self.program.variables:
            type_info = _TYPES.get(declaration.type_name)
            if type_info is None:
                raise self._error(
                    f"Nicht unterstützter C64-Datentyp: {declaration.type_name}.",
                    declaration.position,
                )
            for name in declaration.names:
                variable = self._declare_variable(
                    name,
                    type_info,
                    declaration.position,
                )
                if declaration.initializer is not None:
                    self.initializers.append((variable, declaration.initializer))

    def _constant_type(self, value: ScalarValue) -> _PascalType:
        if isinstance(value, str):
            return STRING_TYPE
        if isinstance(value, bool):
            return BOOLEAN_TYPE
        if 0 <= int(value) <= 255:
            return BYTE_TYPE
        return INTEGER_TYPE

    def _expression_type(self, expression: Expression) -> _PascalType:
        if isinstance(expression, LiteralExpression):
            return self._constant_type(expression.value)
        if isinstance(expression, NameExpression):
            key = self._key(expression.name)
            if key in self.variables:
                return self.variables[key].type_info
            if key in self.constants:
                return self._constant_type(self.constants[key])
            raise self._error(f"Bezeichner nicht gefunden: {expression.name}.", expression.position)
        if isinstance(expression, CallExpression):
            name = self._key(expression.name)
            if name == "peek":
                return BYTE_TYPE
            if name == "chr":
                return CHAR_TYPE
            if name in {"ord", "lo", "hi"}:
                return INTEGER_TYPE
            raise self._error(f"Unbekannte Funktion: {expression.name}.", expression.position)
        if isinstance(expression, UnaryExpression):
            return BOOLEAN_TYPE if expression.operator == "not" else self._expression_type(expression.operand)
        if isinstance(expression, BinaryExpression):
            if expression.operator in {"=", "<>", "<", "<=", ">", ">="}:
                return BOOLEAN_TYPE
            left = self._expression_type(expression.left)
            right = self._expression_type(expression.right)
            if left == STRING_TYPE or right == STRING_TYPE:
                raise self._error("Zeichenkettenarithmetik wird noch nicht unterstützt.", expression.position)
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
            code = ord(character)
            if code == 0 or code > 255:
                raise C64PascalError(
                    f"Zeichen U+{code:04X} kann nicht direkt als PETSCII ausgegeben werden.",
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

        if isinstance(expression, NameExpression):
            key = self._key(expression.name)
            if key in self.constants:
                value = self.constants[key]
                if isinstance(value, str):
                    label = self._string_label(value, expression.position)
                    self.emitter.emit(f"    lda #<{label}", line)
                    self.emitter.emit(f"    ldx #>{label}", line)
                    return STRING_TYPE
                self._emit_load_literal(int(value), line)
                return self._constant_type(value)
            variable = self.variables.get(key)
            if variable is None:
                raise self._error(f"Bezeichner nicht gefunden: {expression.name}.", expression.position)
            self.emitter.emit(f"    lda {variable.label}", line)
            if variable.type_info.size == 2:
                self.emitter.emit(f"    ldx {variable.label}+1", line)
            else:
                self.emitter.emit("    ldx #$00", line)
            return variable.type_info

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
        name = self._key(expression.name)
        line = expression.position.line
        if name == "peek":
            self._require_argument_count(expression.name, expression.arguments, 1, expression.position)
            self._compile_expr(expression.arguments[0])
            self.emitter.emit(f"    sta {self.ZP_LEFT_LO}", line)
            self.emitter.emit(f"    stx {self.ZP_LEFT_HI}", line)
            self.emitter.emit("    ldy #$00", line)
            self.emitter.emit(f"    lda ({self.ZP_LEFT_LO}),y", line)
            self.emitter.emit("    ldx #$00", line)
            return BYTE_TYPE
        if name in {"chr", "ord", "lo", "hi"}:
            self._require_argument_count(expression.name, expression.arguments, 1, expression.position)
            self._compile_expr(expression.arguments[0])
            if name in {"chr", "lo"}:
                self.emitter.emit("    ldx #$00", line)
            elif name == "hi":
                self.emitter.emit("    txa", line)
                self.emitter.emit("    ldx #$00", line)
            return CHAR_TYPE if name == "chr" else INTEGER_TYPE
        raise self._error(f"Unbekannte Funktion: {expression.name}.", expression.position)

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
        variable = self.variables.get(self._key(statement.name))
        if variable is None or variable.internal:
            raise self._error(f"Variable nicht gefunden: {statement.name}.", statement.position)
        result_type = self._compile_expr(statement.expression)
        if result_type == STRING_TYPE:
            raise self._error("String-Variablen folgen in einer späteren Stufe.", statement.position)
        if variable.type_info == BOOLEAN_TYPE and result_type != BOOLEAN_TYPE:
            raise self._error("Boolean-Zuweisung erwartet einen Boolean-Ausdruck.", statement.position)
        self._store_variable(variable, statement.position.line)

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
        variable = self.variables.get(self._key(statement.name))
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
            NameExpression(statement.position, statement.name),
            "<=" if statement.direction == "to" else ">=",
            NameExpression(statement.position, hidden_name),
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
        name = self._key(statement.name)
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
            self._require_argument_count(statement.name, statement.arguments, 0, statement.position)
            self.emitter.emit("    lda #$93", line)
            self.emitter.emit("    jsr $FFD2", line)
            return
        if name == "poke":
            self._require_argument_count(statement.name, statement.arguments, 2, statement.position)
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
            self._require_argument_count(statement.name, statement.arguments, 1, statement.position)
            argument = statement.arguments[0]
            if not isinstance(argument, NameExpression):
                raise self._error(f"{statement.name} erwartet eine Variable.", statement.position)
            variable = self.variables.get(self._key(argument.name))
            if variable is None or variable.internal:
                raise self._error(f"Variable nicht gefunden: {argument.name}.", argument.position)
            operation = "+" if name == "inc" else "-"
            self._compile_assignment(
                AssignmentStatement(
                    statement.position,
                    argument.name,
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
            self._require_argument_count(statement.name, statement.arguments, 0, statement.position)
            label = self._new_label("halt")
            self.emitter.emit(f"{label}:", line)
            self.emitter.emit(f"    jmp {label}", line)
            return
        raise self._error(f"Unbekannte Prozedur: {statement.name}.", statement.position)

    def _emit_runtime(self) -> None:
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
                directive = ".word 0" if variable.type_info.size == 2 else ".byte 0"
                comment = "intern" if variable.internal else variable.name
                self.emitter.emit(f"{variable.label}: {directive} ; {comment}")

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
        self.emitter.emit("; (c) 2026 by Jens Kallup - paule32")
        self.emitter.emit("; alle Rechte vorbehalten.")
        self.emitter.emit(";")
        self.emitter.emit(f"; Programm: {self.program.name}")
        self.emitter.emit(".org $080D")
        self.emitter.emit(".entry __pascal_start")
        self.emitter.emit(".basic")
        self.emitter.emit()
        self.emitter.emit("__pascal_start:", source_line)
        for variable, initializer in self.initializers:
            result_type = self._compile_expr(initializer)
            if result_type == STRING_TYPE:
                raise self._error("String-Variablen folgen in einer späteren Stufe.", initializer.position)
            self._store_variable(variable, initializer.position.line)
        self._compile_statement(self.program.body)
        self.emitter.emit("    rts", source_line)
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

# ----------------------------------------------------------------------------
# Parst Pascal mit ANTLR und erzeugt MOS-6510-Assembler.
# ----------------------------------------------------------------------------
def compile_pascal_to_assembly(
    source: str,
    *,
    filename: str = "<Pascal-Editor>",
) -> GeneratedAssembly:
    program = parse_pascal(source, filename=filename)
    return _CodeGenerator(program).generate()
