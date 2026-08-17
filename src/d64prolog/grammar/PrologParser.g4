parser grammar PrologParser;

options { tokenVocab=PrologLexer; }

program : statement* EOF ;

statement
    : QUERY goalList DOT
    | KNOWLEDGE EQ term DOT
    | callableTerm (RULE goalList)? DOT
    ;

goalList : goal (COMMA goal)* ;

goal
    : term ((EQ | NE | STRICT_EQ | LT | LE | GT | GE) term)?
    ;

callableTerm
    : ATOM (LPAREN term (COMMA term)* RPAREN)?
    | QUOTED_ATOM (LPAREN term (COMMA term)* RPAREN)?
    ;

term
    : KNOWLEDGE
    | VARIABLE
    | NUMBER
    | FLOAT
    | STRING
    | callableTerm
    | listTerm
    | CUT
    | PLUS
    | MINUS
    | STAR
    | SLASH
    | LPAREN term RPAREN
    ;

listTerm
    : LBRACK RBRACK
    | LBRACK term (COMMA term)* (BAR term)? RBRACK
    ;
