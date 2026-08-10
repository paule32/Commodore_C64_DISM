lexer grammar DBaseLexer;

// ---------------------------------------------------------------------------
// dBase lexical layer, stage 7: comments, expressions, members.
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

PROCEDURE    : [Pp][Rr][Oo][Cc][Ee][Dd][Uu][Rr][Ee];
FUNCTION     : [Ff][Uu][Nn][Cc][Tt][Ii][Oo][Nn];
RETURN       : [Rr][Ee][Tt][Uu][Rr][Nn];
ENDPROC      : [Ee][Nn][Dd][Pp][Rr][Oo][Cc];
ENDPROCEDURE : [Ee][Nn][Dd][Pp][Rr][Oo][Cc][Ee][Dd][Uu][Rr][Ee];
ENDFUNC      : [Ee][Nn][Dd][Ff][Uu][Nn][Cc];
ENDFUNCTION  : [Ee][Nn][Dd][Ff][Uu][Nn][Cc][Tt][Ii][Oo][Nn];

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
