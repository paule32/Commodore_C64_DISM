lexer grammar DBaseLexer;

// ---------------------------------------------------------------------------
// dBase lexical layer, stage 16: comments, expressions, members, IF blocks,
// _app/this object paths, NEW MENU and WITH/ENDWITH.
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

PROCEDURE : [Pp][Rr][Oo][Cc][Ee][Dd][Uu][Rr][Ee];
FUNCTION  : [Ff][Uu][Nn][Cc][Tt][Ii][Oo][Nn];
RETURN    : [Rr][Ee][Tt][Uu][Rr][Nn];
IF        : [Ii][Ff];
ELSEIF    : [Ee][Ll][Ss][Ee][Ii][Ff];
ELSE      : [Ee][Ll][Ss][Ee];
ENDIF     : [Ee][Nn][Dd][Ii][Ff];
WITH      : [Ww][Ii][Tt][Hh];
ENDWITH   : [Ee][Nn][Dd][Ww][Ii][Tt][Hh];
NEW       : [Nn][Ee][Ww];
MENU      : [Mm][Ee][Nn][Uu];
TRUE      : [Tt][Rr][Uu][Ee];
FALSE     : [Ff][Aa][Ll][Ss][Ee];
CLASS     : [Cc][Ll][Aa][Ss][Ss];
SET         : [Ss][Ee][Tt];
CLEAR       : [Cc][Ll][Ee][Aa][Rr];
COLOR       : [Cc][Oo][Ll][Oo][Rr];
BORDERCOLOR : [Bb][Oo][Rr][Dd][Ee][Rr][Cc][Oo][Ll][Oo][Rr];
TO        : [Tt][Oo];
DEBUG     : [Dd][Ee][Bb][Uu][Gg];
FORMAT    : [Ff][Oo][Rr][Mm][Aa][Tt];
ON        : [Oo][Nn];
OFF       : [Oo][Ff][Ff];
SCREEN    : [Ss][Cc][Rr][Ee][Ee][Nn];
CONSOLE   : [Cc][Oo][Nn][Ss][Oo][Ll][Ee];

QUESTION2 : '??';
QUESTION  : '?';
SCOPE     : '::';
LE        : '<=';
GE        : '>=';
EQEQ      : '==';
NEANGLE   : '<>';
LT        : '<';
GT        : '>';
HASH      : '#';
EQUAL     : '=';
PLUS      : '+';
MINUS     : '-';
STAR      : '*';
SLASH     : '/';
DOT       : '.';
LPAREN    : '(';
RPAREN    : ')';
COMMA     : ',';
LBRACE    : '{';
RBRACE    : '}';

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
