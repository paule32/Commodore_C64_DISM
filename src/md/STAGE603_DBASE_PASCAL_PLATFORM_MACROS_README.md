# Stage 603 – Plattform-Makros für dBASE und Pascal

**Ausgangsbasis:** `d64_dism_stage602.zip` (verbindliche Stage 602).

## Neue automatische Makros

Die Makros beziehen sich auf das **gewählte Compilerziel**, nicht auf das Host-Betriebssystem.

| Ziel | Definierte Plattformmakros (`= 1`) | Nicht definiert |
|---|---|---|
| Windows PE32 | `WINDOWS`, `WIN32` | `WIN64`, `LINUX` |
| Windows PE32+ / PE64 | `WINDOWS`, `WIN32`, `WIN64` | `LINUX` |
| Linux/ELF (Präprozessor) | `LINUX` | `WINDOWS`, `WIN32`, `WIN64` |
| C64 / Amiga (Pascal) | keine dieser Makros | alle obigen |

`WIN32` ist analog zum Windows-C-API-Symbol `_WIN32` auch unter Windows-x64 gesetzt. Für eine 64-Bit-Spezialbehandlung kann `WIN64` getestet werden.

**Wichtig zu `#ifdef`/`{$IFDEF}`:** Ein Makro mit Wert `0` gilt als **definiert**. Deshalb wird zum Beispiel **nicht** automatisch `#define LINUX 0` bei Windows gesetzt – sonst würde `#ifdef LINUX` fälschlich den Linux-Zweig aktivieren. Inaktive Plattformmakros fehlen ganz; `#if LINUX == 0` funktioniert im dBASE-Präprozessor trotzdem, weil unbekannte Symbole dort den Zahlenwert 0 haben.

## dBASE

```dbase
#ifdef WIN32
    ? "Windows (PE32 oder PE64)"
#endif
#ifdef WINDOWS
    ? "Windows"
#endif
#ifdef WIN64
    ? "Windows 64 Bit"
#endif
#ifdef LINUX
    ? "Linux"
#endif
#if LINUX == 0
    ? "Nicht Linux"
#endif
```

Der bisherige dBASE-Präprozessor kannte `WINDOWS` beziehungsweise `LINUX` bereits; Stage 603 ergänzt `WIN32` und die 64-Bit-Unterscheidung `WIN64`. Der sichtbare Compiler akzeptiert aktuell nur **Windows PE32 und PE64** als dBASE-Ziel. `LINUX` ist im internen Präprozessor für ein zukünftiges Linux-/ELF-Ziel vorbereitet; die Änderung ist **kein Linux-Backend**.

## Pascal

```pascal
{$IFDEF WINDOWS}
  WriteLn('Windows');
{$ENDIF}
{$IFDEF WIN32}
  WriteLn('Windows API');
{$ENDIF}
{$IFDEF WIN64}
  WriteLn('Windows 64 Bit');
{$ENDIF}
{$IFDEF LINUX}
  WriteLn('Linux');
{$ENDIF}
```

In Pascal arbeiten `{$IFDEF}` und `{$IFNDEF}` mit der bloßen **Existenz** der Symbole. Die neuen vordefinierten Makros werden sowohl im Pascal-Compiler (`c64pascal/compiler.py`) als auch im IDE-Präprozessor (`d64_dism.py`) gesetzt und bei parallelen Pascal-Unit-Builds zielabhängig übergeben (`pascal_parallel_build.py`). Die bestehenden internen Makros `__D64_TARGET_PE32__` und `__D64_TARGET_PE64__` bleiben erhalten.

`c64pascal.preprocess_pascal_source` nimmt jetzt optional ein `target=` entgegen. Ohne `target` bleibt das Verhalten der bisherigen öffentlichen Hilfsfunktion unverändert. Für `target='linux'` wird der Linux-Zweig bei der Präprozessorauswertung ausgewählt. Das allein stellt **keinen vollständigen Linux-Assembler/Linker** bereit.

## Geänderte Dateien

- `d64dbase/compiler.py` – Zielmakros `WINDOWS`, `WIN32`, `WIN64`, `LINUX` im dBASE-Präprozessor.
- `c64pascal/compiler.py` – Einheitliche Pascal-Zielmakros für Windows-/Linux-Ziel, optionales `target` in `preprocess_pascal_source`.
- `d64_dism.py` – Gleiche Pascal-IDE-Zielmakros für GUI und CLI; zielabhängiger Preprocess bei paralleler Projektplanung.
- `pascal_parallel_build.py` – Übergibt `target` an Pascal-Preprocess im Parallel-Worker.
- `test_stage603.py` – 13 Regressionstests (mit Zielkombinationen und IDE-Präprozessorprüfung).
- `examples/platform_macros/platform_dbase.prg` und `platform_pascal.pas` – Beispiele.

## Prüfungen

- Stage-603-Tests: **13/13 erfolgreich**.
- Gesonderte Regressionstests Stage 592–602 (ausgenommen Stage 591, dessen Test im Archiv Abhängigkeiten außerhalb dieser Tests hat): **131** erfolgreich (12 + 6 + 10 + 12 + 11 + 8 + 9 + 14 + 21 + 7 + 21 = 131).
- Python-AST-Syntax der geänderten Dateien erfolgreich. `d64_dism.py` enthält Python-3.15-`lazy`-Imports und wurde im Python-3.13-Test ausschließlich für die Syntaxanalyse **im Speicher** auf normale `import`-Schreibweise normalisiert; die Datei im ZIP bleibt unangetastet.
- Pascal-Präprozessor-Tests verwenden die echten Funktionen aus `c64pascal/compiler.py` isoliert. Grund: Die gebündelten ANTLR-Dateien wurden mit 4.13.2 generiert, lokal ist jedoch ANTLR-Runtime 4.9.3 installiert. Daher **kein vollständiger nativer Pascal-Codegenerierungs-/Linux-Laufzeittest**.
- Der dBASE-Codegenerator wurde für PE32 und PE64 zusätzlich mit einem Plattform-`#ifdef`-Beispiel durchlaufen.

