# Stage 590 – Pascal LIBRARY mit D64Z/MSZIP und ESP-Stackslot-Tooltips

Verbindliche Basis: **d64_dism_stage589.zip**.

## 1. D64Z/MSZIP-Packing auch für Pascal-LIBRARY

In `d64_dism.py` sind die `link_coff32_objects`-, `link_coff64_objects`-
und zugehörigen `*_inputs`-Verzweigungen für DLL-Ziele um `pack_dll`
erweitert. Damit erreicht das Projektattribut
`Linker -> Optionen -> D64Z/MSZIP PE-Packung aktivieren` den DLL-Linker.

Bei `LIBRARY foo;` und aktivierter Projektoption:

- Der interne PE32- oder PE32+-Linker baut zunächst ein normales DLL-Image
  mit Exportverzeichnis, Imports und Base-Relocations.
- Zusätzlich benötigte Windows-API-Imports für den DLL-Entpacker werden vor
  dem endgültigen PE-Image-Build eingebunden.
- `d64dbase/pe_dll_payload.py` erstellt anschließend einen separaten
  D64Z/MSZIP-Entpacker für DLLs; `.text` liegt komprimiert in `.ztext`.
- Der neue DLL-Einstiegspunkt verarbeitet `DLL_PROCESS_ATTACH`, stellt
  `.text` wieder her, führt notwendige Relocations aus und springt zum
  ursprünglichen DLL-Einstiegspunkt weiter. Die Export-RVAs ändern sich nicht.
- Ohne aktiviertes Packing bleibt der normale DLL-Linkpfad bestehen.

**EXE-Ausgabe bleibt unverändert:** Das bereits bestehende EXE-Packing samt
EXE-Loader wird weder entfernt noch durch den DLL-Startstub ersetzt.

**Windows-Abhängigkeit:** Der echte MSZIP-Kompressor benötigt die Windows
Cabinet Compression API (`cabinet.dll`). Ein tatsächlicher DLL-LoadLibrary-
und Export-Aufruftest unter Windows war hier nicht verfügbar.

## 2. Fünf MOV-Tooltips für ESP-Stackplätze

Der vorhandene Tooltip im `SourceTextEdit` unterstützt nun jeweils einzeln
und als zusammenhängende Folge:

```asm
mov dword ptr [esp+0],  ebx
mov dword ptr [esp+4],  esi
mov dword ptr [esp+8],  edi
mov dword ptr [esp+12], ebp
mov dword ptr [esp+16], esp
```

Beim Hover auf ein `MOV`-Mnemonic werden Registerquelle, Stack-Adresse und
32-Bit-Breite erläutert. Bei erkannter Fünferfolge enthält der Tooltip
zusätzlich den Zusammenhang: fünf Slots = 20 Byte.

Wichtige Unterscheidungen:

- `MOV [ESP+offset], REG` schreibt **einen Wert** in bereits gültigen Speicher;
  es ist kein `PUSH` und verändert `ESP` nicht.
- Der Slot muss durch einen umgebenden gültigen Stackbereich gedeckt sein.
- `[ESP+16], ESP` speichert **den aktuellen Pointerwert**, nicht den Stack.
- Die Slots sind **nicht automatisch Pascal-Parameter**; ihre Rolle ergibt
  sich erst aus der jeweiligen Aufrufkonvention und dem Prolog.
- PE32/x86 wird unterstützt; das PE64-Registerpaar RSP/RBP und die
  bisherigen EBP-Stackframe-Tooltips bleiben unverändert.

Betroffene Dateien: `asm_stack_frame_tooltips.py`, `d64_dism.py`.

## 3. Prüfungen

- `python -m unittest test_stage590` – 10 neue gezielte Tests erfolgreich.
- `test_stage586`, `test_stage588`, `test_stage589` – 22 vorhandene
  Tooltip-/Editor-Regressionstests erfolgreich.
- Zusätzliche PE32-/PE64-DLL-Strukturtests mit komprimiertem Testpayload
  (zlib nur als Testersatz für Windows MSZIP) durchgeführt: Header,
  Exportverzeichnis, Entpacker- und Payload-Sektionen.
- Syntax der geänderten Python-Module geprüft; `d64_dism.py` enthält
  Python-3.15-Lazy-Import-Syntax und wurde dafür im AST-Test entsprechend
  normalisiert (nicht zur Laufzeit verändert).

**Grenze der Tests:** Die echten Windows-Cabinet-Komprimierung, das native
Laden beider DLL-Architekturen, Aufruf exportierter Funktionen und GUI-Hover
wurden in dieser Linux-Testumgebung nicht ausgeführt. Bitte den Windows-
Laufzeittest nachziehen, bevor die DLL-Packer-Änderung produktiv verwendet wird.
