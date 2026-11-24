# Stage 682 — O3: Unerreichbare Exception-Runtime und unbenutzte .bss entfernen

## Grundlage

Verbindlicher Ausgangsstand: `d64_dism_stage681.zip`.

## Problem

Der dBASE-Assembler erzeugt selbst für Programme ohne `THROW`/`CATCH` die
Exception-Status-Reservierungen `__dbase_exception_id`, `..._code`, die vier
gepackten Value-Slots (message, class, object, cstr) und ggf. weitere Labels.
Hinzu kommt ein generierter Fehlerausgabe-Block `__dbase_exception_unhandled_N`.

Die angefragten Felder stehen in `section .bss`: `resd`/`resq` belegen keinen
rohen Speicher im PE-Dateiimage, sondern nur reservierten Nullspeicher zur
Laufzeit. Eine naive Verlagerung in eine gemeinsam genutzte DLL-Variable würde
verschiedene Programmzustände/Threads miteinander vermischen. Ein vollständig
DLL-verwalteter Ausnahmezustand erfordert einen separaten Kontext pro Programm
oder Ausführung, Lebensdauerverwaltung und angepasste Lade-/Speicheroperationen
für sämtliche `__dbase_exception_*`-Adressen. Das ist in dieser Stage bewusst
**nicht** durch einen globalen DLL-Zeiger ersetzt worden.

## Implementierte O3-Optimierung

Neue Datei `dbase_exception_optimizer.py`. Nur bei `O3`:

1. Erkenne den Standardblock `__dbase_exception_unhandled_N` bis
   `__dbase_exception_continue_N`.
2. Entferne ihn nur dann, wenn weder sein Einstieg noch eines seiner internen
   Labels außerhalb dieses Blocks referenziert werden. Das vorgelagerte
   `jmp` auf den dann unmittelbar folgenden Fortsetzungspunkt wird ersetzt.
3. Entferne **alle** Exception-Statusreservierungen nur dann, wenn danach keine
   dieser Speicheradressen mehr referenziert wird. Die Value-Slots werden als
   unteilbare Gruppe behandelt: `lea reg, [slot_type]` kann die restlichen
   Felder indirekt über Offsets nutzen, auch ohne deren Label zu nennen.
4. Diese Prüfung läuft vor O2-Text-Compacting, um keine unbenutzten Runtime-
   Deskriptoren für den entfernten Ausnahme-Handler zu erzeugen.

O0/O1/O2 bleiben unverändert. O3 ist wiederholbar (idempotent).

Für Programme mit tatsächlichen Ausnahmezugriffen, z. B. `TRY ... THROW ...
CATCH ... ENDTRY`, bleibt die vollständige bisherige Exception-Verwaltung
bewusst erhalten. Das schützt die Semantik der existierenden Runtime.

## Dateien

- `dbase_exception_optimizer.py` — neue konservative Optimierung
- `dbase_size_optimizer.py` — O3-Anbindung vor O2-Text-Compacting
- `test_stage682.py` — sechs neue Tests

## Verifikation

- `test_stage682.py`: 6 bestanden (einschließlich COFF-Assemblierung und
  PE-Linking für PE32 und PE32+)
- `test_stage681.py`: 6 bestanden
- `test_stage680.py`: 3 bestanden

Ein nativer GUI-/DLL-/EXE-Laufzeittest unter Windows steht aus.

## Anwendung

Die Quelldateien mit O3 erneut kompilieren; alte `.asm`/`.o` werden nicht
nachträglich umgeschrieben. Für diese Verbesserung ist kein neuer DLL-Export
notwendig. Eine spätere vollständig DLL-basierte Exception-Context-API müsste
separat eingeführt und auf Mehrprogramm-/Mehrthread-Fähigkeit getestet werden.
