parser grammar DBaseParser;

options { tokenVocab=DBaseLexer; }

sourceFile
    : (routineDefinition | topLevelItem NEWLINE* | NEWLINE)* EOF
    ;

topLevelItem
    : statement
    | ifStatement
    | menuObjectStatement
    | sessionObjectStatement
    | sessionLoginStatement
    | databaseLocalDeclaration
    | databaseObjectStatement
    | databasePropertyStatement
    | databaseMethodStatement
    | appPropertyStatement
    | withStatement
    ;

routineDefinition
    : procedureDefinition
    | functionDefinition
    ;

procedureDefinition
    : PROCEDURE IDENTIFIER parameterClause? NEWLINE+
      routineBodyItem*
      RETURN NEWLINE*
    ;

functionDefinition
    : FUNCTION IDENTIFIER parameterClause? NEWLINE+
      routineBodyItem*
      RETURN expression NEWLINE*
    ;

parameterClause
    : LPAREN (IDENTIFIER (COMMA IDENTIFIER)*)? RPAREN
    ;

routineBodyItem
    : statement NEWLINE+
    | ifStatement NEWLINE*
    ;

ifStatement
    : IF condition NEWLINE+
      ifBodyItem*
      (ELSEIF condition NEWLINE+ ifBodyItem*)*
      (ELSE NEWLINE+ ifBodyItem*)?
      ENDIF
    ;

ifBodyItem
    : statement NEWLINE+
    | returnStatement NEWLINE+
    | ifStatement NEWLINE*
    ;

returnStatement
    : RETURN expression?
    ;

condition
    : expression comparisonOperator expression
    ;

comparisonOperator
    : LT | LE | EQEQ | GT | GE | NEANGLE | HASH
    ;

statement
    : (QUESTION | QUESTION2) expression
    | IDENTIFIER EQUAL expression
    | callExpression
    | setStatement
    | CLEAR SCREEN expression?
    ;

setStatement
    : SET FORMAT TO (SCREEN | CONSOLE)
    | SET DEBUG (ON | OFF)
    | SET COLOR TO (STRING_DOUBLE | STRING_SINGLE)
    | SET BORDERCOLOR TO expression
    ;

// APPLICATION-Properties verwenden normale Ausdruecke. Fuer _app.menuFile
// ist Stage 24 die kanonische Form: _app.menuFile = "menu.mnu"; die alte
// Winkelklammer-Schreibweise ist nicht mehr Teil der Sprache.
// Erste native Klassenstufe: _app und this sind APPLICATION-Objekte.
menuObjectStatement
    : objectPath EQUAL NEW MENU LPAREN objectPath RPAREN
    ;

sessionObjectStatement
    : objectPath EQUAL NEW SESSION LPAREN RPAREN
    ;

sessionLoginStatement
    : IDENTIFIER EQUAL objectPath DOT LOGIN LPAREN expression COMMA expression COMMA expression RPAREN
    ;

databaseLocalDeclaration
    : LOCAL IDENTIFIER AS DATABASE
    ;

databaseObjectStatement
    : objectPath EQUAL NEW DATABASE LPAREN RPAREN
    ;

databasePropertyStatement
    : objectPath DOT (PATH | DATABASENAME | USERNAME | PASSWORD | ACTIVE | ALIAS | SESSION) EQUAL (expression | objectPath)
    ;

databaseMethodStatement
    : objectPath DOT (OPEN | CLOSE | COMMIT) LPAREN RPAREN
    ;

appPropertyStatement
    : objectPath EQUAL expression
    ;

withStatement
    : WITH LPAREN objectPath RPAREN NEWLINE+
      menuPropertyStatement*
      ENDWITH
    ;

menuPropertyStatement
    : IDENTIFIER EQUAL (STRING_DOUBLE | STRING_SINGLE | TRUE | FALSE | callbackReference) NEWLINE+
    ;

callbackReference
    : CLASS SCOPE IDENTIFIER
    ;

objectPath
    : IDENTIFIER (DOT IDENTIFIER)*
    ;

expression
    : additiveExpression
    ;

additiveExpression
    : multiplicativeExpression ((PLUS | MINUS) multiplicativeExpression)*
    ;

multiplicativeExpression
    : unaryExpression ((STAR | SLASH) unaryExpression)*
    ;

unaryExpression
    : (PLUS | MINUS) unaryExpression
    | primaryExpression
    ;

primaryExpression
    : NUMBER
    | HEX_NUMBER
    | STRING_DOUBLE
    | STRING_SINGLE
    | callExpression
    | IDENTIFIER
    | LPAREN expression RPAREN
    ;

callExpression
    : IDENTIFIER LPAREN argumentList? RPAREN
    ;

argumentList
    : expression (COMMA expression)*
    ;
