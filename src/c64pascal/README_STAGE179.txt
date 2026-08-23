Stage 179 - Pascal PROPERTY / Message
=====================================

Fehlerbild
----------

    Zeile 13, Spalte 18:
    extraneous input 'Message' expecting ':'

Typische Quellzeile:

    property Message: String read FMessage write FMessage;

Ursache
-------
Stage 178 kannte PROPERTY, READ und WRITE nicht als Lexer-Tokens. Deshalb wurde
`property` als normales IDENTIFIER und damit als vermeintlicher Feldname
interpretiert. `fieldDeclaration` erwartete danach ':'; beim folgenden
`Message` entstand exakt die genannte Diagnose.

Lexer Stage 179
---------------
Neu:

    PROPERTY
    READ
    WRITE
    STORED
    DEFAULT
    NODEFAULT

Parser Stage 179
----------------
Neu:

    propertyDeclaration
    propertyIndexParameters
    propertySpecifier
    propertyAccessor

Unterstuetzt werden u.a.:

    property Message: String read FMessage write FMessage;
    property Name: String read GetName;
    property Value: Integer write SetValue;
    property Flag: Boolean read FFlag stored True;
    property Count: Integer read FCount default 0;
    property Item[Index: Integer]: String read GetItem write SetItem;

Compiler-AST
------------
Neue PropertyDeclaration-Struktur mit:

    name
    type_name
    read_accessor
    write_accessor
    index_parameters

ClassTypeSpecification speichert Properties getrennt von Feldern und Methoden.
Die semantische _PascalType-Struktur besitzt ebenfalls eine Property-Tabelle.
Vererbte Properties werden an abgeleitete Klassen weitergereicht.

Wichtig
-------
Nach dem Austausch von Lexer/Parser-Grammatik MUSS ANTLR 4.13.2 neu ausgefuehrt
werden. Die im ZIP vorhandenen generated/*.py Dateien wurden nicht manuell
veraendert.

    compile_stage178.bat

funktioniert weiterhin, oder deine eigene compile.bat:

    antlr4.exe -v 4.13.2 -Dlanguage=Python3 -Xexact-output-dir       -o c64pascal\generated c64pascal\grammar\C64PascalLexer.g4

    antlr4.exe -v 4.13.2 -Dlanguage=Python3 -Xexact-output-dir       -visitor -no-listener -lib c64pascal\generated       -o c64pascal\generated c64pascal\grammar\C64PascalParser.g4

Danach d64_dism.py komplett beenden und neu starten.

Hinweis zur Semantik
--------------------
Stage 179 speichert Properties semantisch und validiert ihren Typ. Feld- und
Methoden-Accessoren werden als Namen erhalten. Vollstaendige Delphi-Property-
Dispatch-Semantik (automatischer Getter-/Setter-Aufruf bei jedem Property-
Ausdruck) ist noch nicht aktiviert; fuer System-Units, die Properties im
Interface deklarieren und intern direkt auf F-Felder zugreifen, reicht diese
Stufe zum Kompilieren der Deklaration.
