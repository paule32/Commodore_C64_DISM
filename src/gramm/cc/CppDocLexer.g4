lexer grammar CppDocLexer;

CLASS       : 'class';
STRUCT      : 'struct';
PUBLIC      : 'public';
PRIVATE     : 'private';
PROTECTED   : 'protected';
VIRTUAL     : 'virtual';
STATIC      : 'static';
CONST       : 'const';
INLINE      : 'inline';

IDENT       : [a-zA-Z_][a-zA-Z0-9_]*;

LINE_COMMENT
    : '//' ~[\r\n]* -> channel(HIDDEN)
    ;

BLOCK_COMMENT
    : '/*' .*? '*/' -> channel(HIDDEN)
    ;

WS
    : [ \t\r\n]+ -> channel(HIDDEN)
    ;

LBRACE      : '{';
RBRACE      : '}';
LPAREN      : '(';
RPAREN      : ')';
SEMI        : ';';
COLON       : ':';
COMMA       : ',';
STAR        : '*';
AMP         : '&';
LT          : '<';
GT          : '>';
EQ          : '=';
TILDE       : '~';

OTHER       : . ;
