# Stage 584 – MinGW32 GCC 16.1 PE32-Runtime-DLL-Linkfehler

**Verbindliche Basis:** `d64_dism_stage583.zip`.

## Gemeldeter Linkerfehler

```
ld.exe: libd64_runtime_dll_ertr000001.o:(.rdata+0x0):
  undefined reference to `_pei386_runtime_relocator'
collect2.exe: error: ld returned 1 exit status
relocation link error.
```

Die beiden vorhandenen Skripte (`runtime/build.win32.sh` und
`runtime/compiler/build.win32.sh`) erzeugen die PE32-Runtime absichtlich
mit `-shared -nostdlib`. Die DLL implementiert ihren eigenen
`DllMainCRTStartup` in `runtime/dllmain.cc`. Bei impliziten Datenimports
kann GNU ld Runtime-Pseudo-Relocations anlegen, für deren Abarbeitung der
MinGW-CRT-Helfer `_pei386_runtime_relocator` benötigt würde. Wegen
`-nostdlib` ist er nicht verfügbar. Das Linker-eigene `ertr000001.o` ist
keine Quelldatei im Projekt und soll nicht händisch ersetzt werden.

## Korrektur

Beide PE32-Buildskripte übergeben dem Linker jetzt:

```
-Wl,--disable-auto-import,--disable-runtime-pseudo-reloc
```

Dadurch werden automatische DLL-Datenimporte und zur Laufzeit auszuführende
Pseudo-Relocations unterbunden. Ein bislang erforderlicher impliziter
Datenimport führt jetzt zu einer **konkreten Linkerfehlermeldung**; solche
Referenzen müssten dann explizit über `__imp_...`/`dllimport` oder einen
Funktionszugriff angepasst werden. Die Prüfung wird also nicht umgangen.

Die bisherigen Optionen `-nostdlib`, `-lbcrypt -lkernel32`, die eigenen
DLL-Einstiegspunkte und die Stage-583-NASM-Objekte bleiben erhalten.
Alte `libd64_runtime.dll`- und `.dll.a`-Dateien im jeweiligen Buildordner
werden unmittelbar vor dem Linken entfernt, sodass nach einem fehlgeschlagenen
Build keine veraltete DLL als neu gebaute DLL interpretiert werden kann.

PE64-Skripte und Pascal-Codegenerierung bleiben unverändert.

## MSYS2-Build (MINGW32-Shell)

Aus dem Projektstamm:

```bash
cd runtime
bash build.win32.sh
```

Oder, falls der zweite Buildbaum verwendet wird:

```bash
cd runtime/compiler
bash build.win32.sh
```

Anschließend aus dem Projektstamm den neuen PE32-DLL-Exportzustand prüfen:

```bash
python runtime/pascal/verify_cookie_runtime.py runtime/win32/libd64_runtime.dll
```

Bei Verwendung des zweiten Buildbaums entsprechend
`runtime/compiler/win32/libd64_runtime.dll` einsetzen. Die erfolgreiche DLL
muss neben die erzeugte PE32-EXE kopiert werden. Im Stage-583/584-Archiv
vorhandene ältere Binär-DLLs sind **keine** Bestätigung, dass die neuen
Stack-Cookie-Exporte bereits gebaut sind.

## Prüfungen

- Neue Regressionen in `test_stage584.py`: 4 bestanden.
- Stage-583-Lauf: 4 bestanden.
- Stage-532-Lauf: 4 bestanden.
- Stage-578-Lauf: 6 bestanden.
- Beide betroffenen Shellskripte: `bash -n` bestanden.
- GNU-ld-PE-Optionen sind dokumentiert und auf dem verfügbaren binutils-ld
  als unterstützte Optionen vorhanden.

**Nicht bestätigt:** ein nativer Linklauf mit MSYS2 MINGW32 GCC 16.1.0,
NASM und ein Windows-Laufzeittest; diese Werkzeuge sind hier nicht vorhanden.
Die Korrektur adressiert den konkreten `ertr000001.o`-Pseudo-Relocation-Fehler,
ein späterer anderer Linkfehler kann weitere Ursachen haben.
