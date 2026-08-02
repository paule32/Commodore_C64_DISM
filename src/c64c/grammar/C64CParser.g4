parser grammar C64CParser;

options {
    tokenVocab = C64CLexer;
}

translationUnit
    : externalDeclaration* EOF
    ;

externalDeclaration
    : functionDefinition
    | functionPrototype SEMI
    | typedefDeclaration SEMI
    | structDeclaration SEMI
    | declaration SEMI
    ;

functionDefinition
    : declarationQualifier* typeSpecifier STAR* IDENTIFIER LPAREN parameterList? RPAREN compoundStatement
    ;

functionPrototype
    : declarationQualifier* typeSpecifier STAR* IDENTIFIER LPAREN parameterList? RPAREN
    ;

parameterList
    : VOID
    | parameterDeclaration (COMMA parameterDeclaration)* (COMMA ELLIPSIS)?
    ;

parameterDeclaration
    : CONST? typeSpecifier STAR* IDENTIFIER?
    ;

declaration
    : declarationQualifier* typeSpecifier initDeclaratorList
    ;

declarationQualifier
    : CONST
    | EXTERN
    | STATIC
    ;

typedefDeclaration
    : TYPEDEF typeSpecifier STAR* IDENTIFIER                                      # scalarTypedef
    | TYPEDEF STRUCT tagName=IDENTIFIER? LBRACE structMemberDeclaration* RBRACE aliasName=IDENTIFIER # structuredTypedef
    ;

structDeclaration
    : STRUCT IDENTIFIER LBRACE structMemberDeclaration* RBRACE
    ;

structMemberDeclaration
    : CONST? typeSpecifier STAR* IDENTIFIER SEMI
    ;

initDeclaratorList
    : initDeclarator (COMMA initDeclarator)*
    ;

initDeclarator
    : STAR* IDENTIFIER (ASSIGN expression)?
    ;

typeSpecifier
    : SIGNED? INT
    | UNSIGNED INT?
    | SIGNED? CHAR
    | UNSIGNED CHAR
    | BOOL
    | VOID
    | STRUCT IDENTIFIER
    | IDENTIFIER
    ;

compoundStatement
    : LBRACE blockItem* RBRACE
    ;

blockItem
    : declaration SEMI
    | statement
    ;

statement
    : compoundStatement
    | ifStatement
    | whileStatement
    | doWhileStatement
    | forStatement
    | jumpStatement
    | expressionStatement
    ;

expressionStatement
    : (assignmentExpression | callExpression)? SEMI
    ;

ifStatement
    : IF LPAREN expression RPAREN statement (ELSE statement)?
    ;

whileStatement
    : WHILE LPAREN expression RPAREN statement
    ;

doWhileStatement
    : DO statement WHILE LPAREN expression RPAREN SEMI
    ;

forStatement
    : FOR LPAREN forInitializer? SEMI expression? SEMI assignmentExpression? RPAREN statement
    ;

forInitializer
    : declaration
    | assignmentExpression
    ;

jumpStatement
    : BREAK SEMI
    | CONTINUE SEMI
    | RETURN expression? SEMI
    ;

assignmentExpression
    : lvalue assignmentOperator expression
    | lvalue (INC | DEC)
    | (INC | DEC) lvalue
    ;

lvalue
    : IDENTIFIER (DOT IDENTIFIER)*
    ;

assignmentOperator
    : ASSIGN
    | ADD_ASSIGN
    | SUB_ASSIGN
    | MUL_ASSIGN
    | DIV_ASSIGN
    | MOD_ASSIGN
    | AND_ASSIGN
    | OR_ASSIGN
    | XOR_ASSIGN
    ;

argumentList
    : expression (COMMA expression)*
    ;

expression
    : logicalOrExpression
    ;

logicalOrExpression
    : logicalAndExpression (LOGICAL_OR logicalAndExpression)*
    ;

logicalAndExpression
    : bitwiseOrExpression (LOGICAL_AND bitwiseOrExpression)*
    ;

bitwiseOrExpression
    : bitwiseXorExpression (PIPE bitwiseXorExpression)*
    ;

bitwiseXorExpression
    : bitwiseAndExpression (CARET bitwiseAndExpression)*
    ;

bitwiseAndExpression
    : equalityExpression (AMP equalityExpression)*
    ;

equalityExpression
    : relationalExpression ((EQ | NE) relationalExpression)*
    ;

relationalExpression
    : additiveExpression ((LT | LE | GT | GE) additiveExpression)*
    ;

additiveExpression
    : multiplicativeExpression ((PLUS | MINUS) multiplicativeExpression)*
    ;

multiplicativeExpression
    : unaryExpression ((STAR | SLASH | PERCENT) unaryExpression)*
    ;

unaryExpression
    : (PLUS | MINUS | BANG | TILDE) unaryExpression
    | primaryExpression
    ;

primaryExpression
    : integerLiteral
    | CHAR_LITERAL
    | STRING_LITERAL
    | TRUE
    | FALSE
    | callExpression
    | lvalue
    | LPAREN expression RPAREN
    ;

callExpression
    : IDENTIFIER LPAREN argumentList? RPAREN
    ;

integerLiteral
    : HEX_INTEGER
    | BINARY_INTEGER
    | DECIMAL_INTEGER
    ;
