# Stage 648 — kompakter CATCH-/THROW-Snapshot

**Verbindliche Ausgangsbasis:** `d64_dism_stage647.zip`. Keine weiteren
Projektmodule wurden geändert.

## Ursache

Der dBASE-Compiler kopierte beim Eintritt in `CATCH` die beiden benachbarten
Wertespeicher für `Message` und `Class` feldweise. Dabei erzeugte
`emit_copy_slot()` jeweils fünf 32-Bit-Lese-/Schreibpaare unter PE32. Bei
PE64 wurden für dieselben Felder zehn Speichertransfers je Wertespeicher
verwendet, darunter zwei Transfers mit 64-Bit-Zeigerbreite.

## Änderung im Generator

`d64dbase/compiler.py` enthält jetzt `emit_copy_exception_pair()`; sowohl
`emit_try_statement()` als auch der `THROW e`-Rethrow-Pfad verwenden diese
Funktion. Die Funktion kopiert **beide** aufeinanderfolgenden Wertespeicher
in einem Aufruf der x86-Stringinstruktion `rep movsd`:

* PE32: 2 × (4 Byte Typ + 8 Byte Zahl + 4 Byte Zeiger + 4 Byte Länge)
  = 40 Byte = 10 DWORDs.
* PE64: 2 × (4 Byte Typ + 8 Byte Zahl + 8 Byte Zeiger + 4 Byte Länge)
  = 48 Byte = 12 DWORDs.

Die BSS-Speicherbelegung in `_emit_value_slot_data()` erzeugt die Felder ohne
Padding; sowohl Catch-Message/-Class in `_analyze_catch()` als auch
Exception-Message/-Class im Emitter werden hintereinander reserviert.
Die lineare Blockkopie ist deshalb wohldefiniert. Die kopierten Bytes
sind mit denen des bisherigen Feld-für-Feld-Codes identisch.

`ESI/EDI` bzw. `RSI/RDI` werden **gesichert und wiederhergestellt**. Die
Windows-ABI verlangt `DF=0`, worauf sich `rep movsd` stützt. Der Compiler
setzt DF nicht selbst. `ECX` ist ein flüchtiges Register; der Code setzt es
nur unmittelbar vor der Blockkopie. Für den Exception-Objektzeiger bleibt
die bisherige Eigentumsübertragung mit Nullsetzen des Quellzeigers erhalten.
Die Fehlercodekonvertierung per `FILD`/`FSTP`, `Code_type`, `Exception_id`
und die Ausgabeauswahl bleiben unverändert.

## Interner Assembler

`d64_dism.py` versteht nun `rep movsd` (`F3 A5`) in PE32 und PE64.
Der PE32-Zweipassassembler kennt dieselbe Länge (zwei Bytes) in beiden
Durchläufen. Andere neue REP-Varianten werden nicht freigeschaltet.

## Beispiel: PE32

```asm
__dbase_catch_handler_38:
    push esi
    push edi
    lea esi, [__dbase_exception_message_type]
    lea edi, [__dbase_caught_13_5_message_type]
    mov ecx, 10
    rep movsd
    pop edi
    pop esi
    mov eax, dword ptr [__dbase_exception_object_ptr]
    mov dword ptr [__dbase_caught_13_5_object_ptr], eax
    mov dword ptr [__dbase_exception_object_ptr], 0
    mov eax, dword ptr [__dbase_exception_id]
    mov dword ptr [__dbase_caught_13_5_id_num], eax
    fild dword ptr [__dbase_exception_code]
    fstp qword ptr [__dbase_caught_13_5_code_num]
    mov dword ptr [__dbase_caught_13_5_code_type], 1
    mov dword ptr [__dbase_exception_id], 0
```

Der nachfolgende `SET DEBUG`/`SET FORMAT`-Auswahlblock wird bewusst nicht
verändert, weil er die bisherigen Laufzeitentscheidungen erhält.

## Messung und Tests

Identisches kleines Programm mit `THROW NEW DbException`, einem `CATCH`
und `? e.Message`, jeweils mit dem integrierten COFF-Assembler übersetzt:

| Vergleich | Stage 647 | Stage 648 | Differenz |
|---|---:|---:|---:|
| PE32 `.text`-Bytes | 2663 | 2566 | -97 |
| PE64 `.text`-Bytes | 3508 | 3409 | -99 |
| PE32 Assemblerzeilen | 968 | 956 | -12 |
| PE64 Assemblerzeilen | 1025 | 1013 | -12 |

- Bisherige Exception-Regression: **100 Tests bestanden, 79 Untertests**.
- Neue Stage-648-Tests: **6 Tests bestanden**.
- Native PE32-/PE64-COFF-Assemblerkodierung für `F3 A5` geprüft.
- Echte PE32- und PE64-Images mit dem internen COFF-Linker erstellt.
- Weiterhin kein Windows-Laufzeittest für das erzeugte EXE-Image.

**Geändert:** `d64dbase/compiler.py`, `d64_dism.py`

**Neu:** `test_stage648.py`, dieses Dokument.
