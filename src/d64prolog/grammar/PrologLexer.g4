lexer grammar PrologLexer;

RULE      : ':-' ;
QUERY     : '?-' ;
NE        : '\\=' ;
STRICT_EQ : '==' ;
LE        : '=<' ;
GE        : '>=' ;
EQ        : '=' ;
LT        : '<' ;
GT        : '>' ;
LPAREN    : '(' ;
RPAREN    : ')' ;
LBRACK    : '[' ;
RBRACK    : ']' ;
BAR       : '|' ;
COMMA     : ',' ;
SEMI      : ';' ;
DOT       : '.' ;
CUT       : '!' ;
PLUS      : '+' ;
MINUS     : '-' ;
STAR      : '*' ;
SLASH     : '/' ;

FLOAT       : '-'? [0-9]+ '.' [0-9]+ ([eE] [+-]? [0-9]+)?
            | '-'? [0-9]+ [eE] [+-]? [0-9]+ ;
NUMBER      : '-'? [0-9]+ ;
VARIABLE    : [A-Z_] [A-Za-z0-9_]* ;
ATOM        : [a-z] [A-Za-z0-9_]* ;
QUOTED_ATOM : '\'' ( '\'\'' | ~['\r\n] )* '\'' ;
STRING      : '"' ( '\\' . | ~["\\\r\n] )* '"' ;

LINE_COMMENT  : '%' ~[\r\n]* -> skip ;
BLOCK_COMMENT : '/*' .*? '*/' -> skip ;
WS            : [ \t\r\n]+ -> skip ;
