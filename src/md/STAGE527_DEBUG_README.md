# Stage 527 – Debug-Einstellungen und CES-Bootstrap (Teilumsetzung)

**Verbindliche Quelle:** `packed(8).zip` vom 6. November 2026. Der vollständige Inhalt ist erhalten; Änderungen an `d64_dism.py`, hinzugefügte `debug_options.py`, `runtime/debug/ces_runtime.h`, dieses Dokument und `test_stage527.py`.

## Benutzerschnittstelle

Projekt-Einstellungen → **Debug** (Haupteintrag neben Windows, AMIGA und C=64):

- GroupBox `Debug:`: `Enable Debug` (aus), `CES - Check Early Start` (aus)
- GroupBox `DWARF:`: `Enabled` (aus), `DWARF Version 2`, `DWARF Version 3` (vorgewählt)
- Änderungen der Optionen werden über den bisherigen `save_project()`-Weg unter `[Settings.Debug]` im `.pro`-Projekt abgelegt und beim Laden wiederhergestellt. Änderungen im geöffneten Panel aktualisieren die Laufzeit-Einstellungen für den nächsten Build.

## CES (konkret angeschlossen)

In `_build_pe32_mszip_loader` werden bei aktivierter CES-Option die Fehlerzweige des **D64I-Import-Resolvers** nach fehlgeschlagenem `LoadLibraryA` bzw. `GetProcAddress` in eine zusätzliche Diagnoseroutine geführt. Diese lädt im Fehlerfall `user32.dll` und `MessageBoxA` über die bereits vorhandenen Loader-Importe, zeigt den betroffenen DLL- bzw. Symbolnamen an und beendet anschließend mit dem vorhandenen Fehlercode `0xD6400001`.

Das Debug-Image wird dadurch größer. Bei ausgeschalteter CES-Option wird dieser Zusatzcode nicht emittiert. Das funktioniert bei komprimierten 32-Bit-Images mit D64I-Importresolver; der PE64-Loader, nicht komprimierte Bilder und weitere Frühstart-Fehlerpfade sind noch **nicht** angeschlossen. Es gibt noch keine numerische `GetLastError`-Ausgabe in diesem handemittierten Loader. Die Header-Version `ces_runtime.h` bietet sie für *separate native C/C++-Bootstrap-Projekte*.

## WICHTIG: Enable Debug / DWARF

Das Setzen/Speichern der Optionen ist implementiert, aber **es werden in dieser Stage noch keine echten DWARF-2-/DWARF-3-Sektionen bzw. allgemeinen Symboltabellen in den eigenen PE-/COFF-Writern erzeugt**. Allein das Einschalten der Checkboxen macht die resultierenden EXE/DLL/O-Dateien daher noch nicht DWARF-fähig. Diese Backend-Arbeiten und unabhängige Tests sind ein gesonderter Ausbauschritt. Es werden keine erfundenen `.debug_info`-Sektionen eingebaut.

## `ces_runtime.h` – Kompilieren und Linken

Ein `.h`-Header wird **nicht eigenständig kompiliert oder gelinkt**. Die Datei `runtime/debug/ces_runtime.h` enthält `static`-Funktionen. Für einen mit MinGW32 gebauten *nativen C/C++-Bootstrap* könnte eine Quelldatei beispielsweise schreiben:

```cpp
#include "debug/ces_runtime.h"

void example(void) {
    HMODULE module = d64_ces_load_library("libd64_runtime.dll");
    if (module) {
        d64_ces_get_proc(module, "libd64_runtime.dll", "jit_object_instance_new");
        FreeLibrary(module);
    }
}
```

Vom Verzeichnis `src/runtime` aus würde diese Quelldatei etwa so kompiliert:

```bash
g++ -m32 -std=c++17 -O0 -g -c ces_bootstrap.cc -o win32/obj/ces_bootstrap.o
```

`ces_bootstrap.o` müsste dann mit **dem tatsächlich aufrufenden C/C++-Bootstrap** zusammen gelinkt werden, z.B. unter Verwendung von `-lkernel32` (die Kernel32-Funktionen sind Win32-API-Imports). Wichtig: Der aktuell eingesetzte PE32-MSZIP-Loader in `d64_dism.py` erzeugt seine Maschinenbefehle *direkt in Python*. Er verlinkt keine externen `.o`-Dateien. Daher hat das bloße Erstellen einer `ces_bootstrap.o` **keinen Einfluss** auf den Loader des Projekts. Der tatsächlich angeschlossene PE32-CES-Code befindet sich unmittelbar in `_build_pe32_mszip_loader`.

## Tests

- `python test_stage527.py`: Syntaxanalyse der Datei mit lediglich für Python vor 3.15 temporär normalisierten `lazy`-Importzeilen; INI-Update/-Roundtrip; isolierte PE32-CES-Maschinencodegenerierung (aktiv/inaktiv).
- Kein nativer Windows-10-Laufzeittest, keine vollständige PyQt5-Darstellung möglich in der Prüf-Umgebung.
- Die hochgeladene `d64_dism.py` enthält bereits aktive `lazy from ... import`-Anweisungen. Damit benötigt der unveränderte Source in dieser Form einen Python-Interpreter, der PEP 810 unterstützt (Python 3.15). Für ältere Interpreter sind die Imports anzupassen.
