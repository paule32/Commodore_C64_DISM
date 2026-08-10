lexer grammar DBaseLexer;

// ---------------------------------------------------------------------------
// dBase lexical layer, stage 3.
// ---------------------------------------------------------------------------

STRING_DOUBLE
    : '"' ( '""' | '\\' . | ~["\r\n] )* '"'
    ;

STRING_SINGLE
    : '\'' ( '\'\'' | '\\' . | ~['\r\n] )* '\''
    ;

BLOCK_COMMENT
    : '/*' .*? '*/' -> channel(HIDDEN)
    ;

LINE_COMMENT_SLASH
    : '//' ~[\r\n]* -> channel(HIDDEN)
    ;

LINE_COMMENT_STAR
    : '**' ~[\r\n]* -> channel(HIDDEN)
    ;

LINE_COMMENT_AMP
    : '&&' ~[\r\n]* -> channel(HIDDEN)
    ;

QUESTION2 : '??';
QUESTION  : '?';
EQUAL     : '=';
PLUS      : '+';
MINUS     : '-';
STAR      : '*';
SLASH     : '/';
LPAREN    : '(';
RPAREN    : ')';
COMMA     : ',';

HEX_NUMBER
    : '0' [xX] HEX+
    | '$' HEX+
    | DIGIT HEX* [hH]
    ;

NUMBER
    : DIGIT+ ('.' DIGIT*)? EXPONENT?
    | '.' DIGIT+ EXPONENT?
    ;

IDENTIFIER
    : [A-Za-z_] [A-Za-z0-9_]*
    ;

NEWLINE
    : '\r'? '\n'
    | '\r'
    ;

WS
    : [ \t\f]+ -> channel(HIDDEN)
    ;

fragment DIGIT    : [0-9];
fragment HEX      : [0-9A-Fa-f];
fragment EXPONENT : [eE] [+-]? DIGIT+;
