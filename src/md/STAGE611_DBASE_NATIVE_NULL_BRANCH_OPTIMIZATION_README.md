# Stage 611 – native dBASE `IF ... NULL` direkt auswerten

**Verbindliche Basis:** `d64_dism_stage610.zip`.

## Ursache

In `d64dbase/object_abi.py` erzeugte `_NativeSourceEmitter._emit_expr`
für `IF Self <> NULL` zunächst einen vollständigen numerischen
Vergleich: `xor` für NULL, `push`, Laden von Self, `pop`, `cmp`, `setne`,
`movzx`, `test`, und schließlich einen bedingten Sprung. Das ist korrekt,
aber für eine IF-Abfrage unnötig groß.

## Optimierung

Für die nativen CLASS-Methoden werden folgende **bedingte** Muster mit
`test` und direktem bedingten Sprung umgesetzt:

- `IF x <> NULL` / `IF NULL <> x` / `IF x != 0`: `test x,x` + `jz` zur ELSE-Stelle.
- `IF x = NULL` / `IF NULL = x`: `test x,x` + `jnz` zur ELSE-Stelle.

Bei `RETURN x <> NULL` oder `RETURN x = NULL` muss das Ergebnis dagegen
`0` oder `1` sein. Der Compiler verwendet deshalb weiterhin `setne` /
`sete` und `movzx`, entfernt aber den unnötigen NULL-Stack-Umweg.

Die Quellausdrücke werden nur einmal ausgewertet; es werden nur Gleichheits-
und Ungleichheitsprüfungen mit einem Literal `NULL` oder `0` spezialisiert.
Allgemeine Vergleiche und Nicht-NULL-Operanden verwenden weiterhin den
vorhandenen Codepfad.

## Aktivierung

In den **Projekt-Einstellungen** unter **Compiler → dBASE → Optimierung →
Peephole Optimierung** alle drei Checkboxen aktivieren:

1. Registerbreite
2. Prozessorflags
3. Stackzustand

Die Optimierung des nativen CLASS-Quellcodes wird nur aktiviert, wenn alle
drei gesetzt sind. Dadurch bleibt das Verhalten bestehender Projekte mit
abgeschalteten Peephole-Optionen unverändert. Die Einstellungen sind wie
in Stage 609 pro Architektur getrennt und werden beim Kompilieren sowie
für die Link-Konsistenz verwendet.

## Beispiel PE32

Vorher:

```asm
xor eax, eax
push eax
mov eax, dword ptr [ebp+8]
pop edx
cmp eax, edx
setne al
movzx eax, al
test eax, eax
jz __dbase_cls_tobject_free_else_1
```

Nachher:

```asm
mov eax, dword ptr [ebp+8]
test eax, eax
jz __dbase_cls_tobject_free_else_1
```

## Messung mit `runtime/dbase/src/System.Objects.prg`

Intern ohne Packung mit den vorhandenen COFF-/PE-Linkern erzeugte DLLs:

| Ziel | .text VirtualSize ohne Peephole | .text VirtualSize mit allen 3 Optionen | Ersparnis | DLL-Dateigröße |
| --- | ---: | ---: | ---: | ---: |
| PE32 | 478 B | 446 B | 32 B | 3.072 B in beiden Fällen |
| PE64 | 870 B | 822 B | 48 B | 3.072 B in beiden Fällen |

Die ersparten Bytes beziehen sich auf den gesamten optimierten
`.text`-Code – einschließlich der bereits vorhandenen Stage-609-Regeln
für `mov eax,0/1` – und nicht nur auf die eine IF-Zeile. Die Dateigröße
bleibt wegen der PE-Dateiausrichtung gleich.

## Tests

`python -m unittest -q test_stage599 test_stage600 test_stage602 test_stage605 test_stage605_link test_stage609 test_stage609_link test_stage610 test_stage611`

**92 Tests erfolgreich**, davon 7 neue Stage-611-Tests einschließlich PE32/
PE64-COFF-DLL-Linklauf, Export- und Importkontrolle. Die Windows-API-
Laufzeit wurde nicht in Windows mittels `LoadLibrary` ausgeführt.

## Betroffene Dateien

- `d64dbase/object_abi.py` – IF-Branch und boolescher Vergleich mit NULL/0.
- `d64dbase/dll_backend.py` – optionale Optimierung an den nativen Emitter übergeben.
- `d64dbase/compiler.py` – Peephole-Einstellungen an den Klassen-DLL-Pfad durchreichen.
- `test_stage611.py` – neue Regressionstests.
