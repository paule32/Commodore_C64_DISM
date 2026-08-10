parser grammar DBaseParser;

options { tokenVocab=DBaseLexer; }

sourceFile
    : (statement NEWLINE* | NEWLINE)* EOF
    ;

statement
    : (QUESTION | QUESTION2) expression
    | IDENTIFIER EQUAL expression
    | setStatement
    ;

setStatement
    : IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER   // SET FORMAT TO CONSOLE/SCREEN
    | IDENTIFIER IDENTIFIER IDENTIFIER              // SET DEBUG ON/OFF
    ;

expression
    : additiveExpression
    ;

additiveExpression
    : multiplicativeExpression ((PLUS | MINUS) multiplicativeExpression)*
    ;

multiplicativeExpression
    : unaryExpression ((STAR | SLASH) unaryExpression)*
    ;

unaryExpression
    : (PLUS | MINUS) unaryExpression
    | primaryExpression
    ;

primaryExpression
    : NUMBER
    | HEX_NUMBER
    | STRING_DOUBLE
    | STRING_SINGLE
    | IDENTIFIER (LPAREN argumentList? RPAREN)?
    | LPAREN expression RPAREN
    ;

argumentList
    : expression (COMMA expression)*
    ;
