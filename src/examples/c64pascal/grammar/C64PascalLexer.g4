lexer grammar C64PascalLexer;

options {
    caseInsensitive = true;
}

PROGRAM      : 'PROGRAM';
UNIT         : 'UNIT';
INTERFACE    : 'INTERFACE';
IMPLEMENTATION : 'IMPLEMENTATION';
USES         : 'USES';
LIBRARY      : 'LIBRARY';

CONST        : 'CONST';
TYPE         : 'TYPE';
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
EXIT         : 'EXIT';
RAISE        : 'RAISE';
TRY          : 'TRY';
EXCEPT       : 'EXCEPT';
FINALLY      : 'FINALLY';

RECORD       : 'RECORD';
ARRAY        : 'ARRAY';
OF           : 'OF';
CLASS        : 'CLASS';
PRIVATE      : 'PRIVATE';
PROTECTED    : 'PROTECTED';
PUBLIC       : 'PUBLIC';
PUBLISHED    : 'PUBLISHED';
PROPERTY     : 'PROPERTY';
READ         : 'READ';
WRITE        : 'WRITE';
STORED       : 'STORED';
DEFAULT      : 'DEFAULT';
NODEFAULT    : 'NODEFAULT';
PROCEDURE    : 'PROCEDURE';
FUNCTION     : 'FUNCTION';
CONSTRUCTOR  : 'CONSTRUCTOR';
DESTRUCTOR   : 'DESTRUCTOR';

VIRTUAL      : 'VIRTUAL';
OVERRIDE     : 'OVERRIDE';
CDECL        : 'CDECL';
STDCALL      : 'STDCALL';
EXTERNAL     : 'EXTERNAL';
NAME         : 'NAME';
FORWARD      : 'FORWARD';
STATIC       : 'STATIC';
ABSTRACT     : 'ABSTRACT';
OVERLOAD     : 'OVERLOAD';
REINTRODUCE  : 'REINTRODUCE';
INLINE       : 'INLINE';
DYNAMIC      : 'DYNAMIC';
INHERITED    : 'INHERITED';

INTEGER_TYPE : 'INTEGER';
BYTE_TYPE    : 'BYTE';
CHAR_TYPE    : 'CHAR';
BOOLEAN_TYPE : 'BOOLEAN';
POINTER_TYPE : 'POINTER';
STRING_TYPE  : 'STRING';
DOUBLE_TYPE  : 'DOUBLE';

TRUE         : 'TRUE';
FALSE        : 'FALSE';
NIL          : 'NIL';
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
CARET        : '^';
AT           : '@';
LPAREN       : '(';
RPAREN       : ')';
LBRACK       : '[';
RBRACK       : ']';
COMMA        : ',';
COLON        : ':';
SEMI         : ';';
DOTDOT       : '..';
DOT          : '.';

HEX_INTEGER
    : '$' [0-9A-F]+
    ;

BINARY_INTEGER
    : '%' [01]+
    ;

// Stage 249: Require digits on both sides of the decimal point so 1..10 is
// still tokenized as DECIMAL_INTEGER DOTDOT DECIMAL_INTEGER.
REAL_LITERAL
    : [0-9]+ '.' [0-9]+ ([eE] [+-]? [0-9]+)?
    | [0-9]+ [eE] [+-]? [0-9]+
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
