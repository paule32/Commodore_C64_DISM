# Stage 642 – FNINIT in den internen PE32-/PE64-Assemblern

**Verbindliche Grundlage:** `d64_dism_stage641.zip`.

## Fehler

Der native dBL-Compiler erzeugt bei der Weitergabe einer verwalteten Exception das x87-Kommando `fninit`, um den x87-Status einschließlich eventuell verbliebener Registerwerte zu initialisieren. Der interne PE32-Assembler aus Stage 641 kannte dieses Kommando weder in seiner ersten Phase (Befehlslänge) noch im eigentlichen Encoder:

```
PE32-Assemblerbefehl nicht unterstützt: fninit
```

Die Stage-641-Testdatei umging die Lücke noch fälschlich mit `.replace('    fninit', '    nop')`. Ein `NOP` ist **kein** semantisch korrekter Ersatz für `FNINIT`.

## Änderung

- `d64_dism.py`: PE32-Assembler, **Pass 1** – `FNINIT` ohne Operanden hat eine Länge von **2 Bytes**; **Pass 2** – Kodierung `DB E3`.
- `d64_dism.py`: PE64-Assembler – Kodierung `DB E3` für dieselbe Anweisung.
- Jede Verwendung mit Operanden (etwa `fninit eax`) wird weiterhin abgelehnt.
- `test_stage641.py`: Das zuvor eingesetzte `FNINIT`-zu-`NOP`-Ersetzen wurde entfernt. Der reale erzeugte Assemblercode läuft nun durch die tatsächlich mitgelieferten internen Assembler und COFF-/PE-Linker.
- `test_stage642.py`: Drei zusätzliche Testfälle für Maschinenbytes, Label-Offsets, gemischte Schreibweisen, ungültige Operanden und das erzeugte Klassen-Exception-Programm unter PE32 und PE64.

## Verwendung

Das neue vollständige Projektarchiv entpacken und `d64_dism.py` aus **Stage 642** verwenden. Das zuvor fehlgeschlagene dBASE-Projekt mit dem eingebauten **PE32-/PE64-Assembler** erneut assemblieren und linken. Die dBASE-Quellen können unverändert bleiben. Die Qt5-DLL muss hierfür nicht neu gebaut werden.

## Automatisierte Tests

```
python -m unittest -q test_stage600 test_stage602 test_stage612 test_stage615 test_stage638 test_stage639 test_stage640 test_stage641 test_stage642
--------------------------------------------------------------------
Ran 134 tests
OK (skipped=1)
```

Die Tests belegen die Codegenerierung und den internen COFF-/PE-Linkpfad, nicht die tatsächliche Ausführung der erzeugten Windows-EXE. Das native Ausnahmeverhalten und die übrigen in Stage 641 dokumentierten Einschränkungen bleiben unverändert.
