# Stage 673 – O1-Ausgabe-Routing in die native Qt5-Runtime-DLL verschoben

Verbindliche Grundlage: `d64_dism_stage672.zip`.

## Änderung

In Stage 672 erzeugte die O1-Optimierung pro EXE eine lokale `__dbase_o1_output_write`-Routine, die die Auswahl zwischen Debug-Ausgabe und nativer Windows-Konsole vornahm. Stage 673 verschiebt diese Logik in die Qt5-Runtime (`d64qt5/d64qt5_bridge.cpp`) und exportiert dafür:

```c
void DBaseQtRuntimeWrite(const char *text, int length,
                         int debugOverride, int formatScreen,
                         int *debugVisible);
```

- DLL: `libd64_qt5.dll`
- Export: `DBaseQtRuntimeWrite` (Ordinal 1019, Auflösung **per Namen**)
- 32-Bit: `cdecl`; 64-Bit: Microsoft x64 Calling Convention
- `debugOverride = -1`: `SET FORMAT` bestimmt den Kanal
- `debugOverride = 0`: immer Win32-Konsole
- `debugOverride != -1, != 0`: Debug-Ausgabe
- `formatScreen = 0`: Win32-Konsole; sonst Debug-Ausgabe (wenn kein Override)
- `debugVisible`: Zeiger auf den Sichtbarkeits-Slot in der EXE; wird vor `DBaseQtSetDebugVisible(1)` auf 1 gesetzt

Die native Konsole verbleibt in `c64_dbase_runtime.dll`. Die Qt5-DLL ruft den vorhandenen `DBaseConsoleWrite`-Export per `GetModuleHandleA`/`GetProcAddress` auf, statt den möglicherweise andersartigen `DBaseQtAppendConsole`-Kanal zu verwenden. Auch ein Aufruf mit `length=0` erzeugt die lazy Win32-Konsole. Nur wenn die separate Runtime-DLL fehlt, wird `DBaseQtAppendConsole` als Fallback benutzt.

## Compiler / Optimierung

`dbase_output_compactor.py` erzeugt bei `O1` für unterstützte **statische** Textausgaben einen direkten DLL-Aufruf; die lokale Assembler-Hilfsroutine entfällt. Bei PE32 werden 5 Parameter auf dem Stack übergeben; bei PE32+ liegen die ersten 4 Parameter in RCX/RDX/R8/R9 und der fünfte Parameter auf dem Stack mit reserviertem Shadow Space. Die Importdirektive wird an das Ende der ASM-Datei angefügt, sodass die bisherigen ASM-Zeilennummern erhalten bleiben.

`O0` bleibt bitgenau unverändert. Nicht unterstützte dynamische Texte, Zahlen, Property- und Exception-Abläufe bleiben unangetastet. Statische Texte werden nur dann umgeschrieben, wenn der vorhandene O1-Mustererkenner ein passendes, in sich abgeschlossenes Ausgabeschema findet.

### Aufrufbeispiel, PE32

```asm
    push __dbase_output_debug_visible
    push dword ptr [__dbase_output_format_screen]
    push dword ptr [__dbase_output_debug_override]
    push 5
    push __dbase_text_1
    call DBaseQtRuntimeWrite
    add esp, 20
```

## Kompatibilität

Die ursprüngliche 64-Export-ABI-Prüfsumme (`02c94324...`) bleibt unverändert. Alle alten Ordinals bleiben gleich. Die neue Funktion wird namentlich importiert; in `generate_runtime_abi.py` wurde ausdrücklich festgelegt, dass nur die ursprünglichen Ordinals 1–64 in den alten ABI-Hash eingehen.

**Wichtig: Die native `libd64_qt5.dll` muss aus den Stage-673-Quellen für die passende Windows-Architektur neu gebaut und ausgeliefert werden.** Eine ältere DLL ohne `DBaseQtRuntimeWrite` kann keine mit Stage 673 in O1 erzeugte EXE laden. O0 bleibt rückwärtskompatibel und benötigt diesen Export nicht. Die separate `c64_dbase_runtime.dll` braucht wegen Stage 673 keinen Quellcodeumbau. Mit der vorhandenen Windows-/Qt5-Buildumgebung: `d64qt5/build_d64qt5_mingw32.bat` beziehungsweise die bestehende Qt5-Buildroutine der gewählten Architektur.

## Nachweise

- Sechs neue Stage-673-Tests: O0/O1 unter PE32 und PE32+, ABI-Hash, nativer Funktionsaufruf mit simulierten Win32-Exports, reales Assemblieren und Linken.
- Zwanzig angepasste Stage-671/672-Regressionstests waren erfolgreich.
- Hochgeladenes `App001.generated.pe32.asm` mit `App001.generated.pe32.extern.inc`: O0 `.text` = 3711 Bytes, O1 `.text` = 2661 Bytes; PE32-EXE: 6144 bzw. 5120 Bytes. O1 importiert zusätzlich `DBaseQtRuntimeWrite`.
- Die bisherige Stage-672-O1-Version erzeugte für App001 `.text` = 2626 Bytes; die 35 Byte Mehrbedarf von Stage 673 entstehen durch das Übergeben der Runtime-Zustandsargumente. Die Routing-Routine selbst liegt dafür nur noch in der DLL.
- PE32-/PE32+-COFF-Objekte mit dem neuen Import ließen sich erfolgreich linken.
- Ein echter Windows-/Qt5-Runtime-DLL-Neubau und ein GUI-Laufzeittest wurden mangels installierter Qt5-/MinGW-Buildumgebung **nicht** durchgeführt. Getestet wurde die aus dem echten C++-Quelltext extrahierte Funktion mit einem nativen C++-Mock für die Windows-Exports.

## Geänderte Dateien

`dbase_output_compactor.py`, `d64qt5/d64qt5_bridge.cpp`, `d64qt5/d64qt5_bridge.h`, `d64qt5/d64qt5_bridge.def`, `d64qt5/generate_runtime_abi.py`, `test_stage671.py`, `test_stage672.py`. Neu: `test_stage673.py` und `examples/dbase/App001.generated.pe32.O1.stage673.asm`.
