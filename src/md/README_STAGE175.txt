Stage 175 – Pascal CLASS virtual/override Parser-Synchronisierung
===============================================================

Ausgangsfehler
--------------
System.Objects.pas bricht bei

    destructor Destroy; virtual;

mit

    mismatched input ';' expecting ':'

ab. Bei der eingerückten Originalzeile liegt Spalte 36 am abschließenden
Semikolon hinter `virtual`. Ein alter Parser behandelt `virtual` dort wie einen
normalen Feldbezeichner und erwartet deshalb anschließend `:`.

Der Pascal-Quelltext wird NICHT verändert.

Repo-Befund
-----------
Der aktuelle dBase2Many-Stand besitzt bereits die richtige Grammatik:

    methodDirective
        : VIRTUAL
        | OVERRIDE
        ;

    methodDirectiveList
        : methodDirective SEMI
          (methodDirective SEMI)*
        ;

    constructorDeclaration
        : CONSTRUCTOR IDENT formalParamList?
          SEMI
          methodDirectiveList?
        ;

    destructorDeclaration
        : DESTRUCTOR IDENT formalParamList?
          SEMI
          methodDirectiveList?
        ;

Auch der aktuelle generierte `src/asmjit/parsers/pascal/PascalParser.py` wurde
mit ANTLR 4.13.2 erzeugt und ruft nach dem Destruktor-Semikolon bei VIRTUAL oder
OVERRIDE `methodDirectiveList()` auf.

Im Repository existiert außerdem bereits

    src/asmjit/x32/pascal/System/System.Objects.pui

mit:

    target         = win32
    object_format  = coff32
    machine        = i386
    pointer_size   = 4
    object.file    = System.Objects.o

und für TObject.Destroy:

    kind           = destructor
    is_virtual     = true
    vmt_offset     = 20

Damit ist nicht die Pascal-Syntax das Problem, sondern die zur Laufzeit von
`c64pascal` verwendete Parserkopie.

Stage-175-Korrektur
-------------------
Vor jedem Pascal-Build führt d64_dism jetzt aus:

  1. Ausgehend von der Pascal-Quelldatei nach `src/asmjit` suchen.
  2. `compiler/grammar/PascalParser.g4` prüfen.
  3. `parsers/pascal/PascalParser.py` auf folgende Fähigkeiten prüfen:
       * RULE_methodDirectiveList
       * VIRTUAL
       * OVERRIDE
       * constructorDeclaration
       * destructorDeclaration
       * methodDirectiveList()-Aufruf
  4. Das gefundene `src/asmjit` an Position 0 von sys.path setzen.
  5. eventuell geladene alte PascalLexer/Parser/Visitor/Listener-Module aus
     sys.modules entfernen.
  6. den Repo-lokalen Parser neu importieren.
  7. die Parser-/Lexer-Bindings im geladenen `c64pascal` und dessen bereits
     geladenen Generator-Modulen auf diese Repo-Version umstellen.

Wenn die Grammatik aktuell, der generierte Parser aber nachweislich alt ist,
wird einmalig ANTLR 4.13.2 mit genau dem bestehenden Repo-Schema aufgerufen:

    antlr4.exe -v 4.13.2 -Dlanguage=Python3 -Xexact-output-dir ^
        -o parsers\pascal compiler\grammar\PascalLexer.g4

    antlr4.exe -v 4.13.2 -Dlanguage=Python3 -Xexact-output-dir ^
        -o parsers\pascal -visitor -lib parsers\pascal ^
        compiler\grammar\PascalParser.g4

ANTLR wird nur zur Synchronisierung des Compiler-Parsers verwendet. Der
spätere Pascal->COFF32-Build bleibt der interne Compiler/Assembler/COFF-Pfad;
`mingw32-make`, GCC oder ein externer PE-Linker werden nicht aufgerufen.

Diagnose im Protokoll
---------------------
Bei erfolgreicher Synchronisierung schreibt die GUI beispielsweise:

    PASCAL FRONTEND: compiler=...\c64pascal...; parser=...\src\asmjit\parsers\pascal\PascalParser.py

Wenn ANTLR nachgeneriert wurde:

    ...; ANTLR regenerated

Damit ist sofort nachvollziehbar, welche Parserdatei wirklich ausgeführt wird.

System.Objects.pas -> COFF32
----------------------------
GUI:

  Pascal-Programme
    -> Windows PE32
       -> Units
          -> System.Objects.pas

Danach Unit bauen. Stage 171/174 erzeugt weiterhin das architekturspezifische
Objekt:

    System.Objects.coff32.o

CLI:

    py d64_dism.py --write-coff32 runtime\pascal\system\System.Objects.pas

Ohne explizites `-o` bleibt aus Kompatibilitätsgründen zusätzlich der bestehende
`.o`-Pfad erhalten.

Die lokalen `cdecl; external;` Routinen sind im aktuellen Generator ein eigener
COFF-External-Pfad. Für i386 wird ein nicht dekorierter Pascalname als C-Symbol
mit führendem Unterstrich registriert. Dadurch bleiben diese Referenzen im Unit-
Objekt als vom späteren Linker aufzulösende COFF-Symbole bestehen.

Zusätzliche Dateien
-------------------
System.Objects.pas
    Regressionstest aus der Vorgabe.

REGENERATE_PASCAL_PARSER_STAGE175.bat
    Manuelle Variante der ANTLR-4.13.2-Erzeugung. Optional; d64_dism versucht
    sie bei einer nachweislich alten generierten Parserdatei selbst.

BUILD_SYSTEM_OBJECTS_COFF32_STAGE175.bat
    CLI-Helfer für den COFF32-Unit-Build.

Testgrenze
----------
In der Linux-Testumgebung ist das externe `c64pascal`-Paket aus dem lokalen
Windows-Checkout nicht vorhanden und `antlr4` als Kommando fehlt. Daher konnte
der echte Pascal->COFF32-Lauf hier nicht ausgeführt werden. Geprüft wurden:

  * Python-Syntax von d64_dism.py
  * vollständige Stage-174-Quellerhaltung
  * 25 strukturelle Synchronisierungschecks
  * synthetischer Repo-vs.-stale-Parser-Test mit echtem Python-Import/Patching
  * Regression-Source mit allen kritischen Konstrukten

Quellerhaltung
---------------
Stage 174:
  2472709 Bytes / 56169 Zeilen
  SHA-256 098d3ea4a1cdc72dfb7ce9c8fb9cb0de3a36bc5ae62fe07e12641f4710c2faf7

Stage 175:
  2489747 Bytes / 56645 Zeilen
  SHA-256 f8a0589ec86df2210a5274718c93b92009f2e8859d912cba90640247aa072441

Unified Diff:
  +476
  -0
