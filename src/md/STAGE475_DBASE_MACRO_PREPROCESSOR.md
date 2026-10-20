# Stage 475 – dBASE-Präprozessor für .prg und .wfm

Verbindliche Basis: `d64_dism_asm_474.zip`.

## Neue und vervollständigte Funktionalität

Der bereits in `d64dbase/compiler.py` vorhandene Präprozessor ist jetzt auch im
WFM-Formularcompiler aktiv. Der unmodifizierte Editorquelltext bleibt bestehen;
präprozessiert wird ausschließlich eine temporäre Kompilierversion.

- `#include "datei.h"`: rekursiv, Include-Guards, zirkuläre Includes erkannt,
  Dateisuche relativ zur aktuell einbindenden Datei und anschließend in den
  Projekteinstellungen `Windows → PE32/PE64 → Compiler → Eingabe-Verzeichnis`.
- `#define`, `#undef`, `#ifdef`, `#ifndef`, `#if`, `#elif`, `#else`, `#endif`;
  auch verschachtelt.
- Vergleichsoperatoren `<`, `<=`, `==`, `!=`, `>=`, `=>`, `>`; die bisherige
  Kompatibilität mit `=` und `<>` wird beibehalten.
- Arithmetik, Klammern, String-Konkatenation und Dezimalzahlen im Ausdruck.
  Operatorprioritäten stammen aus einem auf erlaubte AST-Knoten eingeschränkten
  Evaluator; es wird **kein** Python-`eval` auf Quelltext ausgeführt. Dezimalzahlen
  werden als `Decimal` ausgewertet.
- Fehler bei inkompatiblen Operanden (beispielsweise `"Text" + 42`),
  fehlerhaften Operatoren und fehlenden Includes mit Dateiname/Zeilennummer.
- `__FILE__`, `__LINE__`, `__DATE__`, `__TIME__` und die Schreibweise mit
  vorangestelltem `#` in aktiven Ausdrücken sowie in Meldungstexten.
- `#info`, `#warn`, `#warning` werden im Haupt-Protokoll und in den
  Compilerdiagnosen angezeigt; `#error` bricht ab und wird als Compilerfehler
  einschließlich Meldungstext im Protokoll angezeigt.

`__FILE__` liefert in normalen Ausdrücken einen Quellpfad als String. In
`#info`/`#warn`/`#error` wird stattdessen für übersichtliche Meldungen der
Dateiname ohne überflüssige Anführungszeichen ausgegeben.

## Beispiel

```dbase
#define MAKRO 2
#include "gemeinsam.h"

#if MAKRO => 2 && (2 + 3 * 4) == 14
    ? "aktiv"
#elif MAKRO == 1
    ? "alternativ"
#else
    #error Keine gueltige Einstellung
#endif

#if "String1" + "String2" == "String1String2"
    ? "Strings verknuepft"
#endif

#info Dies ist Infotext aus der Datei: #__FILE__
#warn Beispielwarnung in Zeile __LINE__
```

## Dateien

- `d64dbase/compiler.py`: Präprozessor, Dateisuche, Ausdrucksparser,
  Fehlermeldungen und öffentliche optionale `include_paths`-Parameter.
- `d64_dism.py`: gemeinsamer Präprozessor für dBASE und WFM, Übernahme der
  Projekteingabeverzeichnisse, Protokollierung von `#error`-Abbrüchen.
- `test_stage475_dbase_macros_wfm.py`: 21 automatisierte Tests für Bedingungen,
  Typfehler, Fehlermeldungen, Include-Verschachtelung, WFM und beide PE-Ziele.

## Testnachweis

Gezielte gemeinsame Regression Stage 464–475: **106 passed**.
PE32- und PE32+-WFM-Objekt-/EXE-Verlinkung im Testsuite-Lauf erfolgreich.
Eine native Qt5-Interaktion mit dem Windows-Protokollfenster konnte hier nicht
interaktiv durchgeführt werden.
