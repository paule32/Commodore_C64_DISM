lexer grammar C64CLexer;

CONST        : 'const';
TYPEDEF      : 'typedef';
STRUCT       : 'struct';
EXTERN       : 'extern';
STATIC       : 'static';
UNSIGNED     : 'unsigned';
SIGNED       : 'signed';
INT          : 'int';
CHAR         : 'char';
BOOL         : 'bool' | '_Bool';
VOID         : 'void';
IF           : 'if';
ELSE         : 'else';
WHILE        : 'while';
DO           : 'do';
FOR          : 'for';
BREAK        : 'break';
CONTINUE     : 'continue';
RETURN       : 'return';
TRUE         : 'true';
FALSE        : 'false';

INC          : '++';
DEC          : '--';
ADD_ASSIGN   : '+=';
SUB_ASSIGN   : '-=';
MUL_ASSIGN   : '*=';
DIV_ASSIGN   : '/=';
MOD_ASSIGN   : '%=';
AND_ASSIGN   : '&=';
OR_ASSIGN    : '|=';
XOR_ASSIGN   : '^=';
LOGICAL_AND  : '&&';
LOGICAL_OR   : '||';
LE           : '<=';
GE           : '>=';
EQ           : '==';
NE           : '!=';
ASSIGN       : '=';
LT           : '<';
GT           : '>';
PLUS         : '+';
MINUS        : '-';
STAR         : '*';
SLASH        : '/';
PERCENT      : '%';
AMP          : '&';
PIPE         : '|';
CARET        : '^';
BANG         : '!';
TILDE        : '~';
LPAREN       : '(';
RPAREN       : ')';
LBRACE       : '{';
RBRACE       : '}';
COMMA        : ',';
SEMI         : ';';
DOT          : '.';
ELLIPSIS     : '...';

HEX_INTEGER
    : '0' [xX] [0-9a-fA-F]+ [uUlL]*
    ;

BINARY_INTEGER
    : '0' [bB] [01]+ [uUlL]*
    ;

DECIMAL_INTEGER
    : [0-9]+ [uUlL]*
    ;

CHAR_LITERAL
    : '\'' (ESCAPE_SEQUENCE | ~['\\\r\n]) '\''
    ;

STRING_LITERAL
    : '"' (ESCAPE_SEQUENCE | ~["\\\r\n])* '"'
    ;

fragment ESCAPE_SEQUENCE
    : '\\' (['"?\\abfnrtv] | 'x' [0-9a-fA-F]+ | [0-7] [0-7]? [0-7]?)
    ;

IDENTIFIER
    : [a-zA-Z_] [a-zA-Z0-9_]*
    ;

BLOCK_COMMENT
    : '/*' .*? '*/' -> skip
    ;

LINE_COMMENT
    : '//' ~[\r\n]* -> skip
    ;

WS
    : [ \t\r\n\f]+ -> skip
    ;
