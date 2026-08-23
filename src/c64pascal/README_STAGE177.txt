Stage 177 - Pascal Parser/Lexer fuer System.Types + System.Objects
=====================================================================

Basis
-----
Verbindliche Grundlage ist das vom Benutzer hochgeladene `packed.zip`.
Es wurden nur diese bestehenden Quelldateien geaendert:

  compiler.py
  grammar/C64PascalLexer.g4
  grammar/C64PascalParser.g4

Alle 18 anderen bestehenden Dateien des Uploads sind byte-identisch erhalten.

Neue Lexer-Tokens
-----------------
UNIT, INTERFACE, IMPLEMENTATION, USES, LIBRARY
VIRTUAL, OVERRIDE, CDECL, EXTERNAL, FORWARD
POINTER_TYPE, STRING_TYPE, DOUBLE_TYPE
NIL, CARET (^)

Die drei Pascal-Kommentarformen bleiben erhalten:

  { ... }
  (* ... *)
  // ...

`{$...}`-Direktiven werden weiterhin vor ANTLR vom vorhandenen
PascalPreprocessor verarbeitet.

Neue Parser-Regeln
------------------
* native UNIT-CompilationUnit
* qualifizierte Unitnamen wie `System.Types`
* Subrange-Typen: `0..255`, `-2147483648..2147483647`
* Pointertypen: `^Char`, `^AnsiString`
* Builtin-Typnamen auch links von `=` fuer Bootstrap-Units
* Methodendirektiven: `virtual;`, `override;`, `cdecl;`, `forward;`
* globale externe Routinen: `function ...; cdecl; external;`
* NIL als Ausdruck
* Pointer/String/Double als echte Typbezeichner

System.Types.pas
----------------
Die exakte Vorgabe liegt im Paket unter:

  units/System/Types.pas

PE32-Typmodell:

  Boolean      1 Byte
  Byte         1 Byte
  Char         1 Byte
  Word         2 Byte unsigned
  DWord        4 Byte unsigned
  ShortInt     1 Byte signed
  SmallInt     2 Byte signed
  Int32        4 Byte signed
  Cardinal     4 Byte
  UInt32       4 Byte
  LongInt      4 Byte signed
  LongWord     4 Byte
  Integer      4 Byte (Win32-native)
  Pointer      4 Byte
  String       4 Byte Handle
  PChar        4 Byte Pointer
  PAnsiChar    4 Byte Pointer
  PAnsiString  4 Byte Pointer
  PByte        4 Byte Pointer
  Double       8 Byte
  Real         Alias von Double
  Extended     Alias von Double (vorlaeufig)

System.Objects.pas
------------------
Die exakte Vorgabe liegt unter:

  units/System/Objects.pas

Unterstuetzt werden fuer diese Unit:

  TClass = Pointer
  TObject = class
  destructor Destroy; virtual;
  Self <> nil
  Pointer(Self)
  parameterlose Methoden ohne ()
  String-Rueckgabewerte
  cdecl; external;

Die zehn Runtime-Routinen werden im PE32-Unit-ASM als ungelöste C/COFF-Symbole
mit Win32-cdecl-Unterstrich ausgegeben, z.B.:

  extern _jit_object_free
  extern _jit_object_class_type
  extern _jit_dynstring_from_cstr

Klassenmethoden der Unit werden global exportiert, z.B.:

  global __pas_method_tobject_destroy
  global __pas_method_tobject_classtype

Damit kann d64_dism.py das erzeugte IA-32-ASM mit seinem eingebauten Assembler
zu COFF32 assemblieren und spaeter mit den Runtime-Objekten linken.

UNIT-Codeerzeugung PE32
-----------------------
Eine Unit erzeugt keinen Programmstart `_start`.
Stattdessen entsteht z.B.:

  bits 32
  global __unit_System_Objects
  __unit_System_Objects:
      ret

gefolgt von den implementierten Unit-Methoden und externen COFF-Referenzen.

Kompatibilitaet mit dem hochgeladenen Generated-Parser
------------------------------------------------------
Der Upload enthaelt bereits generierte `generated/*.py` Dateien. Diese wurden
nicht blind manuell editiert. `compiler.py` besitzt stattdessen eine schmale
Kompatibilitaetsschicht fuer den alten Generated-Parser:

  * Subranges und ^Pointer werden strukturiert extrahiert.
  * virtual/override werden fuer den alten Parser zeilentreu ausgeblendet.
  * cdecl/external-Deklarationen werden als ExternalRoutineDeclaration erhalten.
  * Nach einer ANTLR-Neugenerierung deaktiviert sich diese Bridge automatisch,
    sobald `RULE_subrangeType` im neuen Parser vorhanden ist.

ANTLR 4.13.2 neu erzeugen
------------------------
Auf dem Windows-System:

  py -m pip install antlr4-python3-runtime==4.13.2

Danach:

  REGENERATE_PARSER_STAGE177.bat T:\Tools\antlr-4.13.2-complete.jar

oder direkt:

  py generate_parser.py T:\Tools\antlr-4.13.2-complete.jar

Wichtig: d64_dism.py danach neu starten, damit keine alte Parserklasse mehr in
`sys.modules` liegt.

Regressionstest nach Regeneration
---------------------------------
Vom Elternverzeichnis des Pakets (Ordnername `c64pascal`):

  py -m c64pascal.test_stage177_system_units

Der Test kompiliert beide echten Unit-Dateien mit `target="pe32"` und prueft
PUI, Unit-Marker, externe Runtime-Symbole und alle TObject-Methoden.

Testumgebung / Grenze
---------------------
In der Assistant-Umgebung ist nur `antlr4-python3-runtime 4.9.3` installiert,
der hochgeladene Generated-Parser verwendet dagegen Serialized-ATN-Version 4
(ANTLR 4.13.x). Ein ANTLR-4.13.2-JAR ist hier nicht installiert und konnte
wegen fehlender DNS-Verbindung nicht heruntergeladen werden. Daher wurde der
Generated-Parser hier nicht neu erzeugt und der native End-to-End-ANTLR-Lauf
nicht behauptet.

Geprueft wurden stattdessen:

  * Python-Syntax von compiler.py / generate_parser.py / Regressionstest
  * Lexer-/Parser-Regelreferenzen ohne fehlende Tokens/Rules
  * exakte System.Types/System.Objects Vorverarbeitung
  * Legacy-Bridge mit 12 Spezialtypen und 10 externen Routinen
  * PE32-Semantik fuer alle System.Types-Typbreiten
  * PE32-Codegen fuer alle System.Objects-Konstrukte
  * virtual-Flag im semantischen Methodenmodell
  * PUI-Klassenspannen: Klassenmethoden werden NICHT als globale Routinen entfernt

Hashes
------
compiler.py:
  3c2aaa931e131ad9b832ef2bd48f7d5eb7479590edbcfe34204fadf804bf0fb6

C64PascalLexer.g4:
  817f6d9dd81624ba3b7a0674197126df724b3e682425968e266d0beb1e2e18e1

C64PascalParser.g4:
  9c43b73ff7d3828676faa1738124f2a3b31e1bac164dcba3d7f755ad6f283645
