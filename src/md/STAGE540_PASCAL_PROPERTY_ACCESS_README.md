# Stage 540 – Pascal-Property-Zugriff

Verbindliche Ausgangsbasis: `d64_dism_stage539.zip`.

## Behobener Fehler

Der Parser kennt `property OnTest1: String read FString write FString`,
aber `_CodeGenerator._resolve_storage()` suchte bisher bei `Foo.OnTest1`
ausschließlich nach einem echten Feld namens `OnTest1`. Das führte zur
Compilerfehlermeldung `Feld nicht gefunden: TFoo.OnTest1`.

## Änderungen

Datei `c64pascal/compiler.py`:

- Gemeinsame Auflösung einer Property in `_resolve_property_target()` inklusive
  Besitzklasse, geerbter Properties und richtungsabhängiger READ-/WRITE-Accessoren.
- Field-Accessor (`read FString`, `write FString`): Umleitung auf die vorhandene
  Objektfeldadresse und -offset, ohne zusätzliche Speicherplätze anzulegen.
- Methoden-Accessor (`read GetName`, `write SetName`): Getter/Setter werden über
  die bereits vorhandene Methodenaufruf-Codegenerierung aufgerufen.
- Zugriff auf `Foo.OnTest1`, `Self.OnTest1` und unqualifiziertes `OnTest1` aus
  einer Objektmethode.
- Schreibgeschützte, nur beschreibbare, nicht existente und inkompatible
  Accessoren erhalten spezifische Kompilierungsdiagnosen.
- Lokale Variablen/Parameter und echte Felder behalten ihre Namenspriorität.
- `_expression_type` erkennt den Rückgabetyp von Property-Gettern.
- Für Eingabeziele von `ReadLn` wird die Schreibbarkeit einer Property geprüft.
- Indizierte Properties werden weiterhin mit eindeutiger Fehlermeldung abgewiesen.

## Beispiel

```pascal
type
    TFoo = class(TObject)
    private
        FString: String;
        FDouble: Double;
    published
        property OnTest1: String read FString write FString;
        property OnTest2: Double read FDouble write FDouble;
    end;

// innerhalb einer Instanzmethode:
OnTest1 := 'Hello';
OnTest2 := 3.21;

// außerhalb:
WriteLn(Foo.OnTest1);
```

Beide Properties werden über ihre backing fields geladen beziehungsweise
beschrieben. Es wird keine neue Runtime-DLL benötigt.

## Prüfungen

- 4 neue Stage-540-Unittests einschließlich PE32, PE32+, O0/O2/O3 und
  aktivierter Stack-Cookie-Instrumentierung.
- 42 bestehende Tests aus Stages 531–539 sowie Stage 532 bestanden.
- `py_compile` für den geänderten Compiler bestanden.
- Die ANTLR-Python-Runtime dieser Umgebung ist 4.9.3; die generierten
  Parserdateien erwarten 4.13.2. Ein vollständiger Pascal-Quelltext-Parse
  und ein nativer Windows-EXE-Test sind deshalb noch nicht bestätigt.

Beim Prüfen unter Windows die Pascal-Dateien mit Stage 540 erneut kompilieren.
Eine Runtime-DLL muss wegen dieser reinen Compilerkorrektur nicht neu gebaut
werden.
