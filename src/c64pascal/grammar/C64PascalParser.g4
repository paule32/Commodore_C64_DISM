parser grammar C64PascalParser;

options {
    tokenVocab = C64PascalLexer;
}

compilationUnit
    : programUnit EOF
    ;

programUnit
    : PROGRAM IDENTIFIER (LPAREN identifierList RPAREN)? SEMI block DOT
    ;

block
    : (declarationSection | methodImplementation)* compoundStatement
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

typeDefinition
    : IDENTIFIER EQ typeSpecification SEMI
    ;

typeSpecification
    : typeIdentifier
    | enumType
    | recordType
    | arrayType
    | setType
    | classType
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

setType
    : SET OF typeIdentifier
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

methodDeclaration
    : routineKind IDENTIFIER formalParameters? (COLON typeIdentifier)? SEMI methodDirective*
    ;

methodDirective
    : VIRTUAL SEMI
    | OVERRIDE SEMI
    ;

propertyDeclaration
    : PROPERTY IDENTIFIER COLON typeIdentifier propertyAccessor+ SEMI
    ;

propertyAccessor
    : READ IDENTIFIER
    | WRITE IDENTIFIER
    ;

methodImplementation
    : routineKind IDENTIFIER DOT IDENTIFIER formalParameters?
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
    | callStatement                        # callStatementNode
    | ifStatement                          # ifStatementNode
    | whileStatement                       # whileStatementNode
    | repeatStatement                      # repeatStatementNode
    | forStatement                         # forStatementNode
    | BREAK                                # breakStatementNode
    | CONTINUE                             # continueStatementNode
    | tryStatement                         # tryStatementNode
    | raiseStatement                       # raiseStatementNode
    ;

tryStatement
    : TRY tryBody (FINALLY finallyBody | EXCEPT exceptBody) END
    ;

tryBody
    : statementSequence?
    ;

finallyBody
    : statementSequence?
    ;

exceptBody
    : exceptionHandler+
    | statementSequence?
    ;

exceptionHandler
    : ON IDENTIFIER COLON typeIdentifier DO statement SEMI?
    ;

raiseStatement
    : RAISE expression?
    ;

assignmentStatement
    : designator ASSIGN expression
    ;

callStatement
    : designator (LPAREN argumentList? RPAREN)?
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
    : IDENTIFIER designatorSuffix*
    ;

designatorSuffix
    : DOT IDENTIFIER
    | LBRACK expression RBRACK
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
    : additiveExpression ((EQ | NE | LT | LE | GT | GE | IN) additiveExpression)?
    ;

additiveExpression
    : multiplicativeExpression ((PLUS | MINUS) multiplicativeExpression)*
    ;

multiplicativeExpression
    : unaryExpression ((STAR | SLASH | DIV | MOD) unaryExpression)*
    ;

unaryExpression
    : (PLUS | MINUS | NOT) unaryExpression
    | primaryExpression
    ;

primaryExpression
    : integerLiteral
    | setConstructor
    | STRING_LITERAL
    | TRUE
    | FALSE
    | NIL
    | designator LPAREN argumentList? RPAREN
    | designator
    | LPAREN expression RPAREN
    ;

setConstructor
    : LBRACK setElementList? RBRACK
    ;

setElementList
    : setElement (COMMA setElement)*
    ;

setElement
    : additiveExpression (DOTDOT additiveExpression)?
    ;

integerLiteral
    : HEX_INTEGER
    | BINARY_INTEGER
    | DECIMAL_INTEGER
    ;
