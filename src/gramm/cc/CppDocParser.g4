parser grammar CppDocParser;

options {
    tokenVocab = CppDocLexer;
}

translationUnit
    : declaration* EOF
    ;

declaration
    : classDeclaration
    | otherToken
    ;

classDeclaration
    : classKind IDENT inheritance? LBRACE classBody RBRACE SEMI?
    ;

classKind
    : CLASS
    | STRUCT
    ;

inheritance
    : COLON inheritanceItem (COMMA inheritanceItem)*
    ;

inheritanceItem
    : accessSpecifier? typeName
    ;

classBody
    : classMember*
    ;

classMember
    : accessSection
    | methodDeclaration
    | fieldDeclaration
    | classDeclaration
    | otherToken
    ;

accessSection
    : accessSpecifier COLON
    ;

accessSpecifier
    : PUBLIC
    | PRIVATE
    | PROTECTED
    ;

methodDeclaration
    : modifier* typeName? destructorOrName LPAREN parameterList? RPAREN CONST? SEMI
    ;

fieldDeclaration
    : typeName IDENT SEMI
    ;

parameterList
    : parameter (COMMA parameter)*
    ;

parameter
    : typeName IDENT?
    ;

modifier
    : VIRTUAL
    | STATIC
    | INLINE
    ;

destructorOrName
    : IDENT
    | TILDE IDENT
    ;

typeName
    : IDENT typeSuffix*
    ;

typeSuffix
    : STAR
    | AMP
    | LT typeName (COMMA typeName)* GT
    ;

otherToken
    : OTHER
    | IDENT
    | SEMI
    | COLON
    | COMMA
    | LPAREN
    | RPAREN
    | LBRACE
    | RBRACE
    | STAR
    | AMP
    | LT
    | GT
    | EQ
    | TILDE
    ;
