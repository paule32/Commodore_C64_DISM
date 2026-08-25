parser grammar C64PascalParser;

options {
    tokenVocab = C64PascalLexer;
}

compilationUnit
    : (programUnit | unitUnit) EOF
    ;

programUnit
    : PROGRAM IDENTIFIER (LPAREN identifierList RPAREN)? SEMI block DOT
    ;

// Native UNIT syntax. compiler.py still keeps its existing source-splitting
// path for PUI generation, but regenerated parsers can now parse units too.
unitUnit
    : UNIT qualifiedIdentifier SEMI
      INTERFACE
      usesClause?
      declarationSection*
      globalRoutinePrototype*
      IMPLEMENTATION
      usesClause?
      declarationSection*
      (globalRoutineDeclaration | globalRoutineImplementation | methodImplementation)*
      (compoundStatement DOT | END DOT)
    ;

usesClause
    : USES qualifiedIdentifier (COMMA qualifiedIdentifier)* SEMI
    ;

qualifiedIdentifier
    : IDENTIFIER (DOT IDENTIFIER)*
    ;

block
    : declarationSection*
      (globalRoutineDeclaration | globalRoutineImplementation | methodImplementation)*
      compoundStatement
    ;

declarationSection
    : constSection
    | typeSection
    | varSection
    ;

constSection
    : CONST constDefinition+
    ;

constDefinition
    : IDENTIFIER EQ expression SEMI
    ;

typeSection
    : TYPE typeDefinition+
    ;

// Built-in type tokens are legal on the left side as well. This is required
// for bootstrap units such as System.Types.pas (Boolean = 0..1, Byte = ...).
typeDefinition
    : typeName EQ typeSpecification SEMI
    ;

typeName
    : IDENTIFIER
    | INTEGER_TYPE
    | BYTE_TYPE
    | CHAR_TYPE
    | BOOLEAN_TYPE
    | POINTER_TYPE
    | STRING_TYPE
    | DOUBLE_TYPE
    ;

typeSpecification
    : typeIdentifier
    | subrangeType
    | pointerType
    | enumType
    | recordType
    | arrayType
    | classType
    ;

subrangeType
    : signedIntegerLiteral DOTDOT signedIntegerLiteral
    ;

pointerType
    : CARET typeIdentifier
    ;

signedIntegerLiteral
    : (PLUS | MINUS)? integerLiteral
    ;

enumType
    : LPAREN identifierList RPAREN
    ;

recordType
    : RECORD fieldDeclaration* END
    ;

arrayType
    : ARRAY LBRACK expression DOTDOT expression RBRACK OF typeIdentifier
    ;

classType
    : CLASS (LPAREN typeIdentifier RPAREN)? classMember* END
    ;

classMember
    : visibilitySpecifier
    | fieldDeclaration
    | methodDeclaration
    | propertyDeclaration
    ;

visibilitySpecifier
    : PRIVATE
    | PROTECTED
    | PUBLIC
    | PUBLISHED
    ;

fieldDeclaration
    : identifierList COLON typeIdentifier SEMI
    ;

// Delphi/Object-Pascal style class property.  System units commonly use
// declarations such as:
//     property Message: String read FMessage write FMessage;
propertyDeclaration
    : PROPERTY IDENTIFIER propertyIndexParameters? COLON typeIdentifier
      propertySpecifier* SEMI
    ;

propertyIndexParameters
    : LBRACK formalParameterList? RBRACK
    ;

propertySpecifier
    : READ propertyAccessor
    | WRITE propertyAccessor
    | STORED (TRUE | FALSE | IDENTIFIER)
    | DEFAULT expression
    | NODEFAULT
    ;

propertyAccessor
    : IDENTIFIER (DOT IDENTIFIER)*
    ;

methodDeclaration
    : CLASS? routineKind IDENTIFIER formalParameters? (COLON typeIdentifier)? SEMI
      methodDirective*
    ;

methodDirective
    : (
        VIRTUAL
        | OVERRIDE
        | CDECL
        | STDCALL
        | FORWARD
        | STATIC
        | ABSTRACT
        | OVERLOAD
        | REINTRODUCE
        | INLINE
        | DYNAMIC
      ) SEMI
    ;

// Example accepted:
// function jit_object_class_type(AObject: Pointer): Pointer; cdecl; external;
// Plain Unit-interface prototype. A calling convention belongs to the
// public ABI and is therefore legal directly after the signature.
globalRoutinePrototype
    : (PROCEDURE | FUNCTION) IDENTIFIER formalParameters?
      (COLON typeIdentifier)? SEMI globalRoutineCallingConvention?
    ;

// External/forward declarations must contain EXTERNAL or FORWARD. Keeping
// CDECL separate makes `function Foo(...); cdecl; begin ... end;` unambiguously
// an implementation rather than a declaration.
globalRoutineDeclaration
    : (PROCEDURE | FUNCTION) IDENTIFIER formalParameters?
      (COLON typeIdentifier)? SEMI globalRoutineCallingConvention?
      (EXTERNAL externalImportSpecification? | FORWARD) SEMI
    ;

externalImportSpecification
    : (IDENTIFIER | STRING_LITERAL) (NAME STRING_LITERAL)?
    ;

// Free routine implementation in a PROGRAM/UNIT implementation section.
globalRoutineImplementation
    : (PROCEDURE | FUNCTION) IDENTIFIER formalParameters?
      (COLON typeIdentifier)? SEMI globalRoutineCallingConvention?
      routineBlock SEMI
    ;

globalRoutineCallingConvention
    : (CDECL | STDCALL) SEMI
    ;

methodImplementation
    : CLASS? routineKind IDENTIFIER DOT IDENTIFIER formalParameters?
      (COLON typeIdentifier)? SEMI routineBlock SEMI
    ;

routineKind
    : PROCEDURE
    | FUNCTION
    | CONSTRUCTOR
    | DESTRUCTOR
    ;

formalParameters
    : LPAREN formalParameterList? RPAREN
    ;

formalParameterList
    : formalParameterGroup (SEMI formalParameterGroup)*
    ;

formalParameterGroup
    : (CONST | VAR)? identifierList COLON typeIdentifier
    ;

routineBlock
    : varSection? compoundStatement
    ;

varSection
    : VAR varDeclaration+
    ;

varDeclaration
    : identifierList COLON typeIdentifier (ASSIGN expression)? SEMI
    ;

identifierList
    : IDENTIFIER (COMMA IDENTIFIER)*
    ;

typeIdentifier
    : INTEGER_TYPE
    | BYTE_TYPE
    | CHAR_TYPE
    | BOOLEAN_TYPE
    | POINTER_TYPE
    | STRING_TYPE
    | DOUBLE_TYPE
    | IDENTIFIER
    ;

compoundStatement
    : BEGIN statementSequence? END
    ;

statementSequence
    : statement (SEMI statement)* SEMI?
    ;

statement
    : compoundStatement                    # compoundStatementNode
    | assignmentStatement                  # assignmentStatementNode
    | inheritedStatement                   # inheritedStatementNode
    | callStatement                        # callStatementNode
    | raiseStatement                       # raiseStatementNode
    | tryStatement                         # tryStatementNode
    | ifStatement                          # ifStatementNode
    | whileStatement                       # whileStatementNode
    | repeatStatement                      # repeatStatementNode
    | forStatement                         # forStatementNode
    | BREAK                                # breakStatementNode
    | CONTINUE                             # continueStatementNode
    | EXIT                                 # exitStatementNode
    ;

assignmentStatement
    : designator ASSIGN expression
    ;

callStatement
    : designator (LPAREN argumentList? RPAREN)?
    ;

raiseStatement
    : RAISE expression?
    ;

tryStatement
    : TRY statementSequence? EXCEPT statementSequence? END
    | TRY statementSequence? FINALLY statementSequence? END
    ;

// Object Pascal inherited call.  `inherited Create;` explicitly selects the
// implementation in the direct base class; bare `inherited;` reuses the
// current method name.
inheritedStatement
    : INHERITED (IDENTIFIER (LPAREN argumentList? RPAREN)?)?
    ;

ifStatement
    : IF expression THEN statement (ELSE statement)?
    ;

whileStatement
    : WHILE expression DO statement
    ;

repeatStatement
    : REPEAT statementSequence? UNTIL expression
    ;

forStatement
    : FOR IDENTIFIER ASSIGN expression (TO | DOWNTO) expression DO statement
    ;

designator
    : (IDENTIFIER | NIL) designatorSuffix*
    ;

designatorSuffix
    : DOT IDENTIFIER
    | LBRACK expression RBRACK
    | CARET
    ;

argumentList
    : expression (COMMA expression)*
    ;

expression
    : orExpression
    ;

orExpression
    : andExpression ((OR | XOR) andExpression)*
    ;

andExpression
    : comparisonExpression (AND comparisonExpression)*
    ;

comparisonExpression
    : additiveExpression ((EQ | NE | LT | LE | GT | GE) additiveExpression)?
    ;

additiveExpression
    : multiplicativeExpression ((PLUS | MINUS) multiplicativeExpression)*
    ;

multiplicativeExpression
    : unaryExpression ((STAR | SLASH | DIV | MOD) unaryExpression)*
    ;

unaryExpression
    : (PLUS | MINUS | NOT) unaryExpression
    | AT designator
    | primaryExpression
    ;

primaryExpression
    : integerLiteral
    | STRING_LITERAL
    | TRUE
    | FALSE
    | NIL
    | typeCastExpression
    | inheritedExpression
    | designator LPAREN argumentList? RPAREN
    | designator
    | LPAREN expression RPAREN
    ;

// Stage 208: INHERITED can also participate in an expression.  This is
// required by VCL code such as `Result := inherited GetWindowStyle or ...`.
inheritedExpression
    : INHERITED IDENTIFIER (LPAREN argumentList? RPAREN)?
    ;

// Built-in Pascal type casts are distinct from ordinary routine calls.
// POINTER_TYPE is a lexer keyword, therefore Pointer(Self) cannot be parsed
// through `designator`, whose root is IDENTIFIER. Keeping casts separate also
// avoids weakening the lexer by turning Pointer back into an IDENTIFIER.
typeCastExpression
    : builtinCastType LPAREN expression RPAREN
    ;

builtinCastType
    : INTEGER_TYPE
    | BYTE_TYPE
    | CHAR_TYPE
    | BOOLEAN_TYPE
    | POINTER_TYPE
    | STRING_TYPE
    | DOUBLE_TYPE
    ;

integerLiteral
    : HEX_INTEGER
    | BINARY_INTEGER
    | DECIMAL_INTEGER
    ;
