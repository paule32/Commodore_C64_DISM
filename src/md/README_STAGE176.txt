Stage 176 – System.Types.pas / Pascal-Kommentare + Direktiven
==============================================================

Ziel
----
Der folgende Pascal-Stil wird vor dem bestehenden ANTLR/c64pascal-Compiler
sauber lexikalisch vorverarbeitet und anschließend weiterhin über den internen
Pascal -> ASM -> COFF32/COFF64-Pfad gebaut.

Unterstützte Kommentararten
---------------------------
1. Mehrzeilig:

   (* Kommentar
      über mehrere Zeilen *)

2. Einzeilig:

   // Kommentar bis Zeilenende

3. Mehrzeilig:

   { Kommentar
      über mehrere Zeilen }

Wichtig: `{$...}` wird VOR dem normalen {...}-Kommentar erkannt. Damit ist

   {$define VERSION 1}

keinesfalls ein Kommentar.

Unterstützte Pascal-Direktiven / Makros
---------------------------------------
Stage 176 verarbeitet:

   {$define NAME}
   {$define NAME value}
   {$undef NAME}

   {$ifdef NAME}
   {$ifndef NAME}
   {$if expression}
   {$elseif expression}
   {$elif expression}
   {$else}
   {$endif}
   {$ifend}

   {$error text}
   {$warning text}
   {$info text}

Für `{$if ...}` werden unterstützt:

   defined(NAME)
   not
   and
   or
   xor
   =  <>  <  >  <=  >=
   Dezimalzahlen
   $HEX
   Pascal-Strings 'text'
   Klammern

Beispiele:

   {$define FOO 1}

   {$ifdef FOO}
      X := 1;
   {$else}
      X := 2;
   {$endif}

   {$if defined(FOO) and FOO = 1}
      X := 3;
   {$endif}

Makroersetzung
---------------
Ein Define mit explizitem Wert wird außerhalb von Strings/Kommentaren
tokenweise ersetzt:

   {$define VERSION 1}
   X := VERSION;

wird für den Parser zu:

   X := 1;

Ebenso:

   {$define VERSION_TEXT '1.0.0'}
   S := VERSION_TEXT;

zu:

   S := '1.0.0';

Ein reines Symboldefine `{$define FOO}` dient als Conditional-Symbol und wird
nicht automatisch als Identifiertext ersetzt.

Zusätzlich stehen bereit:

   __LINE__
   __FILE__
   __DATE__
   __TIME__

Zeilentreue
-----------
Direktiven, Kommentare und inaktive Conditional-Blöcke werden durch Leerzeichen
ersetzt; ihre Zeilenumbrüche bleiben erhalten. Dadurch stimmen spätere ANTLR-
Fehlerzeilen weiterhin mit dem Editor und der Originaldatei überein.

System.Types.pas Regression
---------------------------
Die exakt bereitgestellte Unit wurde durch den Stage-176-Preprocessor geschickt.
Ergebnis:

   Defines erkannt : 4
   Kommentare       : 7
   Originalzeilen   : 70
   Ausgabezeilen    : 70

Erkannte Defines:

   VERSION      = 1
   VERSION_TEXT = '1.0.0'
   VERSION_NAME = 'Community'
   PRODUCT_NAME = 'dBase2Many'

Folgende Pascal-Typdeklarationen bleiben unverändert im Parsertext:

   Boolean     = 0..1;
   Byte        = 0..255;
   Char        = 0..255;
   Word        = 0..65535;
   DWord       = 0..4294967295;
   ShortInt    = -128..127;
   SmallInt    = -32768..32767;
   Int32       = -2147483648..2147483647;

   PChar       = ^Char;
   PAnsiChar   = ^AnsiChar;
   PAnsiString = ^AnsiString;
   PByte       = ^Byte;

Es gibt also absichtlich KEINE Umformung von `..` oder `^`.

GUI-Build
---------
Der bestehende Pascal-GUI-Pfad macht jetzt:

   Editor-Text
      -> prepare_pascal_frontend_for_compile()       [Stage175]
      -> preprocess_pascal_source()                  [Stage176]
      -> compile_pascal_to_assembly()
      -> interner IA-32-/AMD64-Assembler
      -> COFF32 / COFF64

Im Protokoll erscheint z.B.:

   PASCAL PREPROCESS: Kommentare=7; Direktiven=4; Defines=4; Zeilen=70

CLI / COFF32
------------

   py d64_dism.py --write-coff32 System.Types.pas

Für eine Pascal-UNIT bleibt der Stage-171-Pfad aktiv und erzeugt zusätzlich die
architekturspezifische Ausgabe:

   System.Types.coff32.o

PE32+ entsprechend:

   py d64_dism.py --write-coff64 System.Types.pas

   System.Types.coff64.o

Include-Hinweis
---------------
`{$include ...}` / `{$I ...}` wird in Stage 176 noch NICHT expandiert. Die
Direktive wird derzeit mit einer Diagnose ignoriert. Dieser Punkt ist bewusst
nicht als fertig markiert. Die vom Benutzer geforderte define/ifdef/endif-
Familie ist implementiert.

Testgrenze
----------
Das externe lokale `c64pascal`-Paket des Windows-Checkouts ist in der Assistant-
Linuxumgebung nicht vorhanden. Daher konnte der vollständige ANTLR/Pascal->
COFF32-Lauf hier nicht nativ ausgeführt werden. Die Stage-176-Vorverarbeitung,
Integration in GUI/CLI und der exakte System.Types-Regressionstext wurden
programmgesteuert geprüft.

Quellerhaltung
---------------
Stage 175:
  2489747 Bytes / 56645 Zeilen
  SHA-256 f8a0589ec86df2210a5274718c93b92009f2e8859d912cba90640247aa072441

Stage 176:
  2510898 Bytes / 57260 Zeilen
  SHA-256 95defaf9474be5d83fcb4e4c2a29abeda04a17b26a4482f823e1b9c1d316850e

Unified Diff:
  +615
  -0
