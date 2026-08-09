parser grammar LispParser;

options {
    tokenVocab = LispLexer;
}

program
    : expression* EOF
    ;

expression
    : atom
    | list
    | quotedExpression
    ;

list
    : LPAREN expression* RPAREN
    ;

quotedExpression
    : QUOTE expression
    ;

atom
    : NUMBER
    | STRING
    | SYMBOL
    ;
