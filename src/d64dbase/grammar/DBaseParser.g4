parser grammar DBaseParser;

options { tokenVocab=DBaseLexer; }

sourceFile
    : (routineDefinition | statement NEWLINE* | NEWLINE)* EOF
    ;

routineDefinition
    : procedureDefinition
    | functionDefinition
    ;

procedureDefinition
    : PROCEDURE IDENTIFIER parameterClause? NEWLINE*
      routineStatement*
      (RETURN NEWLINE* (ENDPROC | ENDPROCEDURE)?
      | (ENDPROC | ENDPROCEDURE))
    ;

functionDefinition
    : FUNCTION IDENTIFIER parameterClause? NEWLINE*
      routineStatement*
      RETURN expression NEWLINE* (ENDFUNC | ENDFUNCTION)?
    ;

parameterClause
    : LPAREN (IDENTIFIER (COMMA IDENTIFIER)*)? RPAREN
    ;

routineStatement
    : statement NEWLINE+
    ;

statement
    : (QUESTION | QUESTION2) expression
    | IDENTIFIER EQUAL expression
    | callExpression
    | setStatement
    ;

setStatement
    : IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER   // SET FORMAT TO CONSOLE/SCREEN
    | IDENTIFIER IDENTIFIER IDENTIFIER              // SET DEBUG ON/OFF
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
