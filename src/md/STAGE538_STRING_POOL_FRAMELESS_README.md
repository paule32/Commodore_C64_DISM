# Stage 538 – Pascal-Strings und bedingt rahmenlose Routinen

**Basis:** `d64_dism_stage537.zip`.

## Pascal-Zeichenketten und Klassenmetadaten

Die Pascal-Codegeneratoren PE32 und PE32+ teilen ab O1 **vollständig identische,
nullterminierte Zeichenketten** zwischen Klassenmetadaten und Pascal-Literalen.
Beispiel: `__pas_string_25:` und `__pas_classname_tfoo:` können unmittelbar
aufeinander folgen und zeigen dann auf exakt denselben Speicherblock `TFoo\0`.
Die bereits bestehende Deduplikation identischer Pascal-Stringliterale bleibt
aktiv. Das Dateiformat und die Verwendung der Zeiger bleiben unverändert.

**Nicht zusammengelegt werden nur gemeinsame Präfixe:** `TFoo Destroy`,
`TFoo Show` und `TFoo` müssen für die vorhandene, nullterminierte String-ABI
jeweils als zusammenhängende Bytefolge adressierbar bleiben. Eine echte
Präfix-Kompression würde Laufzeit-Rekonstruktion oder einen anderen
String-Datentyp voraussetzen. Dasselbe gilt für `TFaz`, `Win32` und `TFoo`/
`TForm`. Gemeinsame Suffixe sind davon zu unterscheiden und werden in dieser
Stage nicht automatisch überlappend gespeichert.

## Projekt-Einstellungen

Links: `Windows -> 32-Bit/64-Bit -> Compiler -> Pascal -> Optimierung`.
Rechts: Die vorhandene GroupBox `Optimierung-Stufen:` bleibt bestehen;
darunter befindet sich eine neue GroupBox `Stack: ` mit der Checkbox
`No Stack Frames` (Standard: **aus**).

Die Einstellung ist pro Windows-Ziel getrennt und wird gespeichert als:

```ini
[Settings.Windows.32Bit.Compiler.Pascal.Optimierung]
Level = O1
NoStackFrames = true

[Settings.Windows.64Bit.Compiler.Pascal.Optimierung]
Level = O2
NoStackFrames = false
```

Dieselbe Auswahl geht an die normale Pascal-Kompilierung und die getrennten
Compiler-Worker der parallelen Unit-Erzeugung. Ältere Projektdateien ohne
`NoStackFrames` erhalten den Standard `false`.

## Tatsächliche Codeerzeugung

Die Checkbox ist **unabhängig von O0 bis O3**. Die Umsetzung ist bewusst
konservativ: Nur Routinen ohne funktionsrelevante Framezugriffe und ohne
Stack-Cookie sind Kandidaten. PE32-Leaf-Routinen behalten die erforderlichen
Sicherungen der nichtflüchtigen Register `EBX`, `ESI`, `EDI`; sie verwenden
statt EBP-basierter Wiederherstellung symmetrische PUSH/POP-Paare.
Für PE64 erfolgt Frame-Omission nur bei echten Leaf-Routinen ohne Call,
Stackframezugriff oder nichtflüchtige Registeränderungen. Insbesondere
PE64-Methoden, die `RSI` sichern, bleiben unverändert, solange der
Compiler keine passenden Windows-x64-Unwind-Daten emittiert.

Bei Stack-Cookies, Stack-Lokalvariablen, verwendeten Stackparametern,
Exception-/TRY-Kontexten, x64-Calls mit Shadow Space oder
unbekannter Stackbewegung wird der bisherige Prolog/Epilog beibehalten.
Der Compiler nimmt keine pauschale Löschung von `push ebp`, `mov ebp,esp`
oder `mov esp,ebp`, `pop ebp` vor, da dies ungültigen Code erzeugen würde.

## Dateien

- `c64pascal/compiler.py`: neue Codegeneratoroption und Daten-Deduplikation
- `pascal_optimizer.py`: konservative Frame-Sicherheitsanalyse und Umschreibung
- `d64_dism.py`: GUI, `.pro`-Speicherung, Compiler-Aufrufparameter
- `pascal_parallel_build.py`: Weitergabe an parallele Compilerprozesse
- `test_stage538.py`: zusätzliche Architektur-, Cookie-, ABI-, String- und Projektdateitests
- `test_stage537.py`: ältere Test-Erwartungen an das erweiterte Optimierungsprofil angepasst

## Prüfungen

- Stage 538: **9/9 Tests erfolgreich**.
- Stage 537/535/534 plus Stage 538: **22 Tests erfolgreich**, dazu
  **20 parametrische Subtests**.
- Stage 536: 8 Prüfungen erfolgreich, anschließend durch Testzeitlimit
  beendet; dieser komplette Lauf gilt ausdrücklich nicht als bestanden.
- Statische Python-Syntaxprüfung der geänderten Compiler- und Workerdateien
  erfolgreich; `d64_dism.py` enthält bereits aus Stage 537 stammende
  Python-3.15-`lazy`-Importsyntax und kann in der hier vorhandenen Python-3.13-
  Umgebung nicht direkt ausgeführt werden.

Native Windows-10/11-Ausführung und ein vollständiger, mit passender ANTLR-
Runtime erzeugter Pascal-EXE-Build stehen noch aus. Insbesondere die
Windows-x64-Unwind- und Exceptionpfade sollten auf dem Zielsystem überprüft
werden, bevor die Option großflächig genutzt wird.
