Stage 178 - Pointer(Self) Pascal type cast
==============================================

Fehlerbild
----------
System.Objects.pas Zeile 52:

    jit_object_free(Pointer(Self));

ANTLR meldete:

    extraneous input 'Pointer' expecting {'TRUE', 'FALSE', 'NIL', 'NOT',
    '+', '-', '(', ')', HEX_INTEGER, BINARY_INTEGER, DECIMAL_INTEGER,
    STRING_LITERAL, IDENTIFIER}

Ursache
-------
`Pointer` wird im Stage-177-Lexer korrekt als `POINTER_TYPE` tokenisiert.
Die Ausdrucksregel akzeptierte Aufrufe aber nur ueber `designator`, dessen
Wurzel lediglich `IDENTIFIER | NIL` war. Deshalb konnte `Pointer(Self)` nicht
als Ausdruck beginnen.

Korrektur
---------
C64PascalParser.g4 besitzt jetzt:

    typeCastExpression
        : builtinCastType LPAREN expression RPAREN
        ;

    builtinCastType
        : INTEGER_TYPE
        | BYTE_TYPE
        | CHAR_TYPE
        | BOOLEAN_TYPE
        | POINTER_TYPE
        | STRING_TYPE
        | DOUBLE_TYPE
        ;

`primaryExpression` akzeptiert `typeCastExpression` vor normalen Designator-
Aufrufen.

compiler.py besitzt zusaetzlich `visitTypeCastExpression()`. Daraus entsteht
das bereits vom PE32-Codegenerator unterstuetzte AST:

    CallExpression(
        DesignatorExpression('Pointer'),
        [DesignatorExpression('Self')]
    )

Damit bleibt Pointer ein Pascal-Typ und wird NICHT zu einem normalen IDENTIFIER
zurueckgestuft.

Betroffene Stellen in System.Objects.pas
----------------------------------------
Pointer(Self) steht in den Zeilen:

    52, 58, 63, 69, 76, 88, 94

Alle sieben Stellen werden von derselben neuen Cast-Regel abgedeckt.

Nach dem Kopieren UNBEDINGT Parser neu erzeugen
----------------------------------------------
Die Dateien unter `generated/` im ZIP stammen weiterhin aus Stage 177, da sie
ANTLR-generierter Code sind und nicht manuell editiert werden sollen.

Auf deinem Windows-System deshalb nach dem Einspielen ausfuehren:

    compile_stage178.bat

oder deine eigene compile.bat mit ANTLR 4.13.2.

Danach `d64_dism.py` komplett beenden und neu starten. Ein bereits importierter
C64PascalParser in `sys.modules` wird sonst weiter benutzt.

Tests
-----
* compiler.py Python-Syntax: OK
* Parser-Grammatik: 60 Regeln, keine unbekannten Lexer-/Parserreferenzen
* System.Objects: 7 x Pointer(Self) gefunden
* Pointer(Self) -> CallExpression-Pointer-Cast AST: OK
* PE32-Codegen fuer Pointer(Self): OK
* extern _jit_object_free / call _jit_object_free: OK

Native ANTLR-Regeneration wurde in der Assistant-Umgebung nicht ausgefuehrt,
weil dort weiterhin kein ANTLR-4.13.2-Tool-JAR installiert ist.

SHA256 compiler.py
------------------
8e89c94775f6d2a8ce9c4d9700e3a07c5699484efe786409135c811f8abb20a4

SHA256 C64PascalParser.g4
-------------------------
9bffe64401f9aecd4bf162c8d283f7e09f371beb7a2154b339df2562fbe8d171
