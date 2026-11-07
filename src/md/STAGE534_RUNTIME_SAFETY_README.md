# Stage 534 – Pascal runtime safety (Basis: Stage 533)

## 1. PE32 globale Pascal-Routinen
- Aufrufer und Empfänger verwenden nun **durchgehend die Stack-ABI** für
  globale Pascal-Routinen (auch ohne explizites `cdecl`).
- Parameter werden rechts-nach-links gepusht; `cdecl` räumt der Aufrufer auf,
  `stdcall` der Empfänger. `VAR`-Argumente werden als Adressen übergeben.
- Größere Wertparameter (>4 Byte) werden explizit abgelehnt, statt stillschweigend
  als 32-Bit-Wert falsch übergeben zu werden.
- Betroffen: `c64pascal/compiler.py`, insbesondere `IntToStr`-artige Aufrufe.
- **Grenze:** Statische Speicherplätze für die *lokalen Parameterkopien* und
  Methoden-Parameter bleiben eine separate Reentranz-Aufgabe.

## 2. CRT-Importauflösung thread-sicher
- Die **tatsächlich aktive** NASM-Implementierung ist `runtime/compiler/memory_nt32.asm`
  (gespiegelt nach `runtime/memory_nt32.asm`).
- Atomarer Initialisierungsstatus mit `lock cmpxchg` (0 / 1 / 2 / 3).
  Bis zur vollständigen Initialisierung dürfen keine CRT-Pointer benutzt werden.
- C++-Alternative `memory.cc` verwendet ebenfalls atomare Einmalinitialisierung;
  der bisher mehrfach zurückgesetzte `ok`-Status entfällt.
- `free_fn` hat nun die korrekte Signatur `void (*)(void*)`.

## 3. Objektlebensdauer / Free-Diagnose
- Der Objekt-Allocator registriert live Pointer in einer begrenzten, nicht dynamisch
  allozierten Tabelle (8.192 Einträge).
- `jit_object_free` verweigert einen zweiten/concurrent Free, **bevor** die VMT
  dereferenziert wird. `jit_object_instance_free` markiert Objekte für den
  Finalizer und beendet die Lebensdauer nach dessen Rückkehr.
- Diagnoseausgabe optional beim Bauen des Runtime-Moduls mit
  `-DD64_OBJECT_LIFETIME_TRACE`: Allocation/Free/Fehler, Objektadresse,
  Windows-Prozess-ID und Thread-ID.
- Dies ist ein Guard für über die JIT-Runtime erzeugte Objekte, kein universeller
  Heap-Debugger und kein Ersatz für PageHeap/ASan/WinDbg.

## 4. TRY/EXCEPT/FINALLY-Frames
- `exception.cc`: Die prozessglobale aktive Frame-Zeigerkette wurde durch Windows
  `TlsAlloc`/`TlsGetValue`/`TlsSetValue` ersetzt; der Index wird bei
  `DLL_PROCESS_DETACH` via `TlsFree` freigegeben.
- PE32-Pascal-Codegenerator: Buffer (24 Byte) und Frame (268 Byte) werden **pro
  TRY-Aufruf auf dem jeweiligen Thread-Stack** reserviert. Das behebt die
  vorherige globale BSS-Frame-Wiederverwendung bei verschachtelten/reentranten
  Aufrufen. `EXIT` entfernt aktive Exception-Frames.
- `_jit_raise` kopiert jetzt die Nachricht in den Frame; eine erneute Raise-
  Weitergabe aus FINALLY verwendet die gespeicherte Nachricht.
- **Grenzen:** `Exit` *innerhalb* `try/finally` räumt den Exception-Frame ab,
  aber führt die `finally`-Anweisungen bei diesem speziellen Kontrollfluss
  noch nicht automatisch aus. PE64 `TRY` ist weiterhin nicht implementiert.

## Build / Betrieb unter Windows
**WICHTIG:** Die in dieser Stage im ZIP vorhandenen älteren EXE-/DLL-Dateien sind
Altbestände von Stage 533 und enthalten **nicht** die neuen Runtime-Korrekturen!
Die DLL muss neu gebaut und dann am **tatsächlichen Startort** der EXE ersetzt
werden. Zum Bauen der PE32-Runtime aus `runtime/compiler` in einer MSYS2-MINGW32-
Shell (`g++`, `gcc`, `nasm`) ausführen:

```bash
cd runtime/compiler
bash build.win32.sh
```

Ausgabe des vorhandenen Build-Skripts: `runtime/compiler/win32/libd64_runtime.dll`.
Danach die 32-Bit-DLL in das Verzeichnis der `test_raise.exe` übernehmen und
`test_raise.pas` mit Stage-534-Compiler neu übersetzen/linken. Die DLL muss
zum PE32-Ziel passen. `libd64_qt5.dll` bleibt bei dieser Korrektur unverändert.

Optional für Objekt-Diagnose: beim Übersetzen von `jitObject.cc` das Define
`-DD64_OBJECT_LIFETIME_TRACE` setzen und die Runtime neu linken.

## Tests
- `python test_stage534.py` (6 gezielte Checks)
- `python test_stage531.py`, `python test_stage532.py`, `python test_stage533.py`
- Auf Windows nach dem **Neuaufbau**:
  `py -3 test_stage534_live.py runtime/pascal/test/pe32/test_raise.exe -n 100`
  (füttert `ReadLn` mit einem Zeilenende, prüft stdout-Reihenfolge und Exitcode).

Hier getestet: Python-Codegenerierung, Syntax aller modifizierten Runtime-C++-
Module und COFF32-Objekt-Erzeugung per Clang. **Nicht getestet:** NASM-Assemblierung,
Neu-Link der vollständigen Runtime-DLL, native Ausführung unter Windows und
100-facher Laufzeittest. Diese müssen am Windows-System bestätigt werden.
