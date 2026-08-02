lexer grammar C64PascalLexer;

options {
    caseInsensitive = true;
}

PROGRAM      : 'PROGRAM';
CONST        : 'CONST';
VAR          : 'VAR';
BEGIN        : 'BEGIN';
END          : 'END';
IF           : 'IF';
THEN         : 'THEN';
ELSE         : 'ELSE';
WHILE        : 'WHILE';
DO           : 'DO';
REPEAT       : 'REPEAT';
UNTIL        : 'UNTIL';
FOR          : 'FOR';
TO           : 'TO';
DOWNTO       : 'DOWNTO';
BREAK        : 'BREAK';
CONTINUE     : 'CONTINUE';

INTEGER_TYPE : 'INTEGER';
BYTE_TYPE    : 'BYTE';
CHAR_TYPE    : 'CHAR';
BOOLEAN_TYPE : 'BOOLEAN';

TRUE         : 'TRUE';
FALSE        : 'FALSE';
DIV          : 'DIV';
MOD          : 'MOD';
AND          : 'AND';
OR           : 'OR';
XOR          : 'XOR';
NOT          : 'NOT';

ASSIGN       : ':=';
LE           : '<=';
GE           : '>=';
NE           : '<>';
EQ           : '=';
LT           : '<';
GT           : '>';
PLUS         : '+';
MINUS        : '-';
STAR         : '*';
SLASH        : '/';
LPAREN       : '(';
RPAREN       : ')';
COMMA        : ',';
COLON        : ':';
SEMI         : ';';
DOT          : '.';

HEX_INTEGER
    : '$' [0-9A-F]+
    ;

BINARY_INTEGER
    : '%' [01]+
    ;

DECIMAL_INTEGER
    : [0-9]+
    ;

STRING_LITERAL
    : '\'' ('\'\'' | ~['\r\n])* '\''
    ;

IDENTIFIER
    : [A-Z_] [A-Z0-9_]*
    ;

BRACE_COMMENT
    : '{' .*? '}' -> skip
    ;

PAREN_COMMENT
    : '(*' .*? '*)' -> skip
    ;

LINE_COMMENT
    : '//' ~[\r\n]* -> skip
    ;

WS
    : [ \t\r\n\f]+ -> skip
    ;

