lexer grammar LispLexer;

LPAREN  : '(';
RPAREN  : ')';
QUOTE   : '\'';

NUMBER  : '-'? [0-9]+ ;
STRING  : '"' ( '\\' . | ~["\\] )* '"' ;

SYMBOL  : [a-zA-Z_+\-*/<>=!?] [a-zA-Z0-9_+\-*/<>=!?]* ;

WS      : [ \t\r\n]+   -> skip ;
COMMENT : ';' ~[\r\n]* -> skip ;
