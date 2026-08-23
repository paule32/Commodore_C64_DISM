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

// Method/routine directives needed by System.Objects.pas.
VIRTUAL      : 'VIRTUAL';
OVERRIDE     : 'OVERRIDE';
CDECL        : 'CDECL';
EXTERNAL     : 'EXTERNAL';
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

DECIMAL_INTEGER
    : [0-9]+
    ;

STRING_LITERAL
    : '\'' ('\'\'' | ~['\r\n])* '\''
    ;

IDENTIFIER
    : [A-Z_] [A-Z0-9_]*
    ;

// IMPORTANT: compiler directives are handled by the Pascal preprocessor
// before ANTLR sees the source. Normal brace comments must therefore remain
// separate from {$...} processing.
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
