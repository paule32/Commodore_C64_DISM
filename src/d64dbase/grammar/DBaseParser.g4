parser grammar DBaseParser;

options { tokenVocab=DBaseLexer; }

sourceFile
    : (routineDefinition | topLevelItem NEWLINE* | NEWLINE)* EOF
    ;

topLevelItem
    : statement
    | ifStatement
    | menuObjectStatement
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
    | CLEAR SCREEN
    ;

setStatement
    : SET FORMAT TO (SCREEN | CONSOLE)
    | SET DEBUG (ON | OFF)
    | SET COLOR TO (STRING_DOUBLE | STRING_SINGLE)
    | SET BORDERCOLOR TO expression
    ;

// Erste native Klassenstufe: _app und this sind APPLICATION-Objekte.
menuObjectStatement
    : objectPath EQUAL NEW MENU LPAREN objectPath RPAREN
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
