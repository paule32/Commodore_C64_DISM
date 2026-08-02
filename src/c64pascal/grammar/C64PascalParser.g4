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
    : constSection? varSection? compoundStatement
    ;

constSection
    : CONST constDefinition+
    ;

constDefinition
    : IDENTIFIER EQ expression SEMI
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
    ;

assignmentStatement
    : IDENTIFIER ASSIGN expression
    ;

callStatement
    : IDENTIFIER (LPAREN argumentList? RPAREN)?
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
    | primaryExpression
    ;

primaryExpression
    : integerLiteral
    | STRING_LITERAL
    | TRUE
    | FALSE
    | IDENTIFIER LPAREN argumentList? RPAREN
    | IDENTIFIER
    | LPAREN expression RPAREN
    ;

integerLiteral
    : HEX_INTEGER
    | BINARY_INTEGER
    | DECIMAL_INTEGER
    ;

