"""ANTLR-basierter C-zu-MOS-6510-Compiler fuer den Commodore C64.

Das C-Frontend baut einen kleinen, C-spezifischen AST auf und uebersetzt ihn
in die bereits bewaehrte 16-Bit-Zwischendarstellung des C64-Pascal-Backends.
Die erzeugte Assemblersprache wird anschliessend vom in ``d64_dism(5).py``
enthaltenen Mehrpass-Assembler in ein PRG umgewandelt.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from c64pascal.compiler import (
    AssignmentStatement,
    BinaryExpression,
    BOOLEAN_TYPE,
    BreakStatement,
    CallExpression,
    CallStatement,
    CompoundStatement,
    ConstDeclaration,
    ContinueStatement,
    Expression,
    ForStatement,
    IfStatement,
    LiteralExpression,
    NameExpression,
    PascalProgram,
    RepeatStatement,
    STRING_TYPE,
    SourcePosition,
    Statement,
    UnaryExpression,
    VarDeclaration,
    WhileStatement,
    _CodeGenerator,
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
class _FrontendResult:
    program: PascalProgram
    preprocessed: PreprocessResult
    filename: str
    typedef_count: int
    structure_count: int
    prototype_count: int


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

    def __init__(self, filename: str, preprocessed: PreprocessResult) -> None:
        super().__init__()
        self.filename = filename
        self.preprocessed = preprocessed
        self.constants: List[ConstDeclaration] = []
        self.variables: List[VarDeclaration] = []
        self.typedefs: Dict[str, str] = {}
        self.structures: Dict[str, Tuple[_StructMember, ...]] = {}
        self.prototypes: Dict[str, object] = {}
        self.struct_variables: Dict[str, str] = {}

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

    def _consume_prototype(self, ctx) -> None:
        name = ctx.IDENTIFIER().getText()
        # Typen werden hier bewusst aufgeloest: Ein Tippfehler in einem Header
        # soll nicht erst bei einem spaeteren Funktionsaufruf auffallen.
        self._type_name(ctx.typeSpecifier())
        parameters = ctx.parameterList()
        if parameters is not None:
            for parameter in parameters.parameterDeclaration():
                self._type_name(parameter.typeSpecifier())
        self.prototypes[name] = ctx

    def visitTranslationUnit(self, ctx):
        main_function = None
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
            name = function.IDENTIFIER().getText()
            if name != "main":
                raise self._error(
                    "In dieser ersten Stufe ist nur die Funktion main erlaubt.",
                    function,
                )
            if main_function is not None:
                raise self._error("main wurde mehrfach definiert.", function)
            main_function = function

        if main_function is None:
            raise self._error("Die Funktion main fehlt.", ctx)

        return_type = self._type_name(main_function.typeSpecifier())
        if main_function.STAR():
            return_type = "pointer"
        if return_type not in {"integer", "void"}:
            raise self._error("main muss int oder void zurueckgeben.", main_function)
        parameters = main_function.parameterList()
        if parameters is not None and not parameters.VOID():
            raise self._error("main unterstuetzt nur (void) oder ().", parameters)

        body = self.visit(main_function.compoundStatement())
        filename = Path(self.filename).name
        program_name = Path(filename).stem if filename and not filename.startswith("<") else "main"
        return PascalProgram(
            program_name,
            tuple(self.constants),
            tuple(self.variables),
            body,
        )

    def _consume_declaration(self, ctx, *, local: bool) -> List[Statement]:
        type_name = self._type_name(ctx.typeSpecifier())
        if type_name == "void":
            raise self._error("Eine Variable kann nicht vom Typ void sein.", ctx)
        is_const = self._has_qualifier(ctx, "const")
        initializer_statements: List[Statement] = []
        for item in ctx.initDeclaratorList().initDeclarator():
            name = item.IDENTIFIER().getText()
            expression = self.visit(item.expression()) if item.expression() else None
            position = self._position(item)
            item_type = type_name
            if item.STAR() or item_type.startswith("pointer:"):
                item_type = "integer"
            if item_type.startswith("struct:"):
                if expression is not None:
                    raise self._error(
                        "struct-Initialisierer werden noch nicht unterstuetzt.",
                        item,
                    )
                canonical = item_type.split(":", 1)[1]
                members = self.structures.get(canonical)
                if members is None:
                    raise self._error(f"struct {canonical} ist nicht definiert.", item)
                self.struct_variables[name] = canonical
                for member in members:
                    member_type = member.type_name
                    if member.pointer_depth or member_type.startswith("pointer:"):
                        member_type = "integer"
                    if member_type.startswith("struct:"):
                        raise self._error(
                            "Verschachtelte struct-Felder folgen in einer spaeteren Stufe.",
                            item,
                        )
                    self.variables.append(
                        VarDeclaration(
                            (f"{name}.{member.name}",),
                            member_type,
                            None,
                            position,
                        )
                    )
                continue
            if is_const:
                if expression is None:
                    raise self._error("Eine const-Deklaration benoetigt einen Initialwert.", item)
                self.constants.append(ConstDeclaration(name, expression, position))
                continue
            self.variables.append(
                VarDeclaration(
                    (name,),
                    item_type,
                    None if local else expression,
                    position,
                )
            )
            if local and expression is not None:
                initializer_statements.append(
                    AssignmentStatement(position, name, expression)
                )
        return initializer_statements

    def visitCompoundStatement(self, ctx):
        statements: List[Statement] = []
        for item in ctx.blockItem():
            if item.declaration():
                statements.extend(
                    self._consume_declaration(item.declaration(), local=True)
                )
            else:
                statements.append(self.visit(item.statement()))
        return CompoundStatement(self._position(ctx), tuple(statements))

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
        initializer = ctx.forInitializer()
        condition_ctx = ctx.expression()
        update_ctx = ctx.assignmentExpression()
        if initializer is None or condition_ctx is None or update_ctx is None:
            raise self._error(
                "FOR erwartet Initialisierung, Vergleich und ++/-- Schritt.",
                ctx,
            )

        if initializer.declaration():
            declaration = initializer.declaration()
            if self._has_qualifier(declaration, "const") or len(declaration.initDeclaratorList().initDeclarator()) != 1:
                raise self._error("FOR erwartet genau eine Laufvariable.", initializer)
            item = declaration.initDeclaratorList().initDeclarator(0)
            if item.expression() is None:
                raise self._error("FOR-Laufvariable benoetigt einen Initialwert.", item)
            self._consume_declaration(declaration, local=True)
            initial = AssignmentStatement(
                self._position(item),
                item.IDENTIFIER().getText(),
                self.visit(item.expression()),
            )
        else:
            initial = self._assignment_statement(initializer.assignmentExpression())

        if not isinstance(initial, AssignmentStatement):
            raise self._error("Ungueltige FOR-Initialisierung.", initializer)

        condition = self.visit(condition_ctx)
        if (
            not isinstance(condition, BinaryExpression)
            or not isinstance(condition.left, NameExpression)
            or condition.left.name != initial.name
            or condition.operator not in {"<", "<=", ">", ">="}
        ):
            raise self._error(
                "FOR-Vergleich muss die Laufvariable mit einer Grenze vergleichen.",
                condition_ctx,
            )

        update = self._assignment_statement(update_ctx)
        if (
            not isinstance(update, AssignmentStatement)
            or update.name != initial.name
            or not isinstance(update.expression, BinaryExpression)
            or not isinstance(update.expression.left, NameExpression)
            or not isinstance(update.expression.right, LiteralExpression)
            or int(update.expression.right.value) != 1
            or update.expression.operator not in {"+", "-"}
        ):
            raise self._error("FOR-Schritt muss ++, --, += 1 oder -= 1 sein.", update_ctx)

        direction = "to" if update.expression.operator == "+" else "downto"
        allowed = {"<", "<="} if direction == "to" else {">", ">="}
        if condition.operator not in allowed:
            raise self._error("FOR-Vergleich und Schritt haben verschiedene Richtungen.", ctx)

        final = condition.right
        if condition.operator == "<":
            final = BinaryExpression(final.position, final, "-", LiteralExpression(final.position, 1))
        elif condition.operator == ">":
            final = BinaryExpression(final.position, final, "+", LiteralExpression(final.position, 1))

        return ForStatement(
            self._position(ctx),
            initial.name,
            initial.expression,
            direction,
            final,
            self.visit(ctx.statement()),
        )

    def visitJumpStatement(self, ctx):
        if ctx.BREAK():
            return BreakStatement(self._position(ctx))
        if ctx.CONTINUE():
            return ContinueStatement(self._position(ctx))
        return CallStatement(self._position(ctx), "__c_return", ())

    def _lvalue_name(self, ctx) -> str:
        parts = [token.getText() for token in ctx.IDENTIFIER()]
        if len(parts) == 1:
            return parts[0]
        if len(parts) != 2:
            raise self._error(
                "Verschachtelter struct-Zugriff folgt in einer spaeteren Stufe.",
                ctx,
            )
        variable, member_name = parts
        canonical = self.struct_variables.get(variable)
        if canonical is None:
            raise self._error(f"{variable} ist keine struct-Variable.", ctx)
        member_names = {
            member.name for member in self.structures.get(canonical, ())
        }
        if member_name not in member_names:
            raise self._error(
                f"struct {canonical} besitzt kein Feld {member_name}.",
                ctx,
            )
        return f"{variable}.{member_name}"

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

    def _call_arguments(self, ctx) -> Tuple[Expression, ...]:
        argument_list = ctx.argumentList()
        if argument_list is None:
            return ()
        return tuple(self.visit(item) for item in argument_list.expression())

    def _call_expression(self, ctx) -> CallExpression:
        name = ctx.IDENTIFIER().getText()
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
                raise self._error(
                    f"Der Prototyp von {name} ist bekannt; die Codeerzeugung "
                    "fuer benutzerdefinierte Funktionen folgt in einer spaeteren Stufe.",
                    ctx,
                )
            raise self._error(f"Unbekannte C-Funktion: {name}.", ctx)
        return CallExpression(self._position(ctx), mapped, self._call_arguments(ctx))

    def _call_statement(self, ctx) -> Statement:
        name = ctx.IDENTIFIER().getText()
        arguments = self._call_arguments(ctx)
        position = self._position(ctx)
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
            "poke": "poke",
            "c64_poke": "poke",
            "halt": "halt",
            "c64_halt": "halt",
        }.get(name)
        if mapped is None:
            if name in self.prototypes:
                raise self._error(
                    f"Der Prototyp von {name} ist bekannt; die Codeerzeugung "
                    "fuer benutzerdefinierte Funktionen folgt in einer spaeteren Stufe.",
                    ctx,
                )
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


def _parse_c_frontend(
    source: str,
    *,
    filename: str = "<C-Editor>",
    include_paths: Iterable[Path | str] = (),
    predefined_macros: Optional[Mapping[str, str | int | bool]] = None,
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

    listener = _RaisingErrorListener(preprocessed)
    lexer = C64CLexer(InputStream(preprocessed.source))
    lexer.removeErrorListeners()
    lexer.addErrorListener(listener)
    parser = C64CParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(listener)
    tree = parser.translationUnit()
    builder = _AstBuilder(filename, preprocessed)
    program = builder.visit(tree)
    return _FrontendResult(
        program,
        preprocessed,
        filename,
        len(builder.typedefs),
        len(builder.structures),
        len(builder.prototypes),
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


class _CCodeGenerator(_CodeGenerator):
    def __init__(self, frontend: _FrontendResult) -> None:
        super().__init__(frontend.program)
        self.frontend = frontend

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
        return f"__c_{prefix}_{self.label_counter}"

    def _compile_call_statement(self, statement: CallStatement) -> None:
        if statement.name == "__c_return":
            self.emitter.emit("    jmp __c_program_end", statement.position.line)
            return
        super()._compile_call_statement(statement)

    def generate(self) -> GeneratedAssembly:
        self._prepare_symbols()
        source_line = self.program.body.position.line
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
        self._compile_statement(self.program.body)
        self.emitter.emit("__c_program_end:", source_line)
        self.emitter.emit("    rts", source_line)
        self._emit_runtime()
        self._emit_data()
        assembly = "\n".join(self.emitter.lines).rstrip() + "\n"
        assembly = assembly.replace("__pascal_start", "__c_start")
        assembly = assembly.replace("__pas", "__c")
        assembly = assembly.replace("Pascal-Variablen", "C-Variablen")
        return GeneratedAssembly(
            self.program.name,
            assembly,
            dict(self.emitter.source_map),
            sum(not variable.internal for variable in self.variable_order),
            len(self.strings),
            self.frontend.preprocessed.included_files,
            tuple(sorted(self.frontend.preprocessed.macros)),
            self.frontend.preprocessed.notes,
            self.frontend.preprocessed.warnings,
            self.frontend.typedef_count,
            self.frontend.structure_count,
            self.frontend.prototype_count,
        )


def compile_c_to_assembly(
    source: str,
    *,
    filename: str = "<C-Editor>",
    include_paths: Iterable[Path | str] = (),
    predefined_macros: Optional[Mapping[str, str | int | bool]] = None,
) -> GeneratedAssembly:
    """Praeprozessiert C, parst mit ANTLR und erzeugt MOS-6510-Assembler."""
    frontend = _parse_c_frontend(
        source,
        filename=filename,
        include_paths=include_paths,
        predefined_macros=predefined_macros,
    )
    try:
        return _CCodeGenerator(frontend).generate()
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
