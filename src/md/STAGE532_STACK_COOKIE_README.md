# Stage 532 — Stack-Cookie-Instrumentierung (auf Stage 531)

## Bedienung

`Projekt-Einstellungen → Windows → 32-Bit → Compiler → Sicherheit → Stack: → Protector Cookie`

`Projekt-Einstellungen → Windows → 64-Bit → Compiler → Sicherheit → Stack: → Protector Cookie`

Die Checkboxen sind **unabhängig** und weiterhin standardmäßig **deaktiviert**.
Die schon in Stage 531 eingebauten INI-Sektionen bleiben unverändert:

```ini
[Settings.Windows.32Bit.Compiler.Security]
ProtectorCookie = true

[Settings.Windows.64Bit.Compiler.Security]
ProtectorCookie = false
```

## Integration

Dateien:
- `d64_dism.py`: gewählte architekturspezifische Option wird im Pascal-Compile-Worker an `compile_pascal_to_assembly(..., stack_protector=...)` übergeben; aktualisierter Tooltip.
- `c64pascal/compiler.py`: optionale Stack-Cookie-Instrumentierung in `_PE32CodeGenerator` und `_PE64CodeGenerator`, einschließlich eigenständiger Pascal-UNITs und LIBRARY-Quellen.
- `test_stage532.py`: Tests für Opt-in, x86/x64, normale Rückkehr, vorzeitiges EXIT und Projektweitergabe.

Bei **aktiviertem Schutz** erzeugt jede implementierte Pascal-Prozedur/-Funktion/-Methode:
1. Nach dem regulären Frame-Prolog einen Cookie-Slot auf dem nativen Stack (PE32: `[ebp-4]`, PE64: `[rbp-8]`; PE64-Methode: `[rbp-16]` im bereits vorhandenen Ausrichtungsslot).
2. Modulinterne einmalige CSPRNG-Initialisierung (`bcrypt.dll!BCryptGenRandom`) des Cookie-Geheimnisses. Bei parallelen Erstaufrufen wird der Gewinner mit `kernel32.dll!InterlockedCompareExchange` bzw. `InterlockedCompareExchange64` atomar ermittelt. Alle weiteren Aufrufe lesen das gleiche Geheimnis.
3. Ableitung des Frame-Wertes per XOR mit EBP/RBP und Ablage im Frame.
4. Prüfung gegen das Modulgeheimnis sowohl beim regulären Rücksprung als auch bei `Exit`-Anweisungen.
5. Bei Verletzung oder Fehlschlag der Zufallsinitialisierung: `RaiseFailFastException(NULL, NULL, 0)`; falls dieser Aufruf unerwartet zurückkehrt: `ExitProcess(0xC0000409)`.

PE64-Aufrufe an Windows-APIs verwenden die Windows-x64-Konvention (Register und 32 Byte Shadow Space). Der Generator überschreibt bei der Prüfung keine Integer-/Floating-Point-Rückgaberegister. Für `ProtectorCookie = false` werden keine neuen Imports, Stack-Slots oder Runtime-Routinen erzeugt.

Die Schutzfunktionen werden **direkt ins jeweilige PE32/PE32+-COFF-Modul** geschrieben. Weder `ces_runtime.h` noch eine Worker-DLL ist erforderlich. Die Windows-Systembibliotheken `bcrypt.dll` und `kernel32.dll` werden bei aktiviertem Schutz importiert. Der externe D64I-Packer/Loader bleibt unverändert: der Schutzcode befindet sich im kompilierten Image und wird mit diesem gepackt.

## Grenzen

- **Scope:** Diese Stage instrumentiert das native **Pascal-Frontend** für Windows PE32 und PE32+. C-, dBase-, PROLOG- oder direkt eingegebene ASM-Frontends erhalten durch diese Checkbox derzeit **keine** automatische Instrumentierung. Bereits vorkompilierte `.o`, `.a` und fremde DLLs werden ebenfalls nicht nachträglich geschützt.
- Der aktuelle Pascal-Codegenerator legt viele lokale Variablen und Arrays in statischen Modulbereichen statt auf dem Stack ab. Der Cookie erkennt nur eine Verfälschung des **Stack-Cookie-Slots** — nicht beliebige Out-of-bounds-Zugriffe auf diese statischen Daten. Array-Grenzprüfungen bleiben separat notwendig.
- Ein Stack-Cookie ist **keine** allgemeine Speichersicherheits- oder Control-Flow-Integrity-Garantie. Stapelüberschreibungen, die den Guard nicht erreichen, können unerkannt bleiben.
- Die Instrumentierung umfasst explizit generierte Pascal-Funktions- und Methodenrümpfe, nicht sämtliche compilerinternen Hilfsfunktionen, die Startfunktion `_start`, die Unit-Marker oder Fremdcode.
- PE32-Exceptions mit `longjmp` können geschützte Frames ohne regulären Epilog überspringen; die Integritätsprüfung ist derzeit auf **normale Returns und explizite `Exit`** begrenzt.
- Eine eigenständige Pascal-Unit muss mit derselben Option übersetzt werden, wenn auch ihre Funktionen geschützt sein sollen; bereits vorliegende Unit-Objekte werden nicht verändert.
- Testumgebung: das vorhandene ANTLR4-Paket ist 4.9.3, der mitgelieferte Pascal-Parser wurde mit ANTLR 4.13.2 generiert. Vollständige Pascal-Quelltextübersetzung ist in dieser Umgebung deshalb nicht möglich; die Tests bauen einen repräsentativen Pascal-AST direkt auf.
- Windows 10/11 muss die Funktionsimporte bereitstellen. Eine native Laufzeitprüfung inkl. absichtlich ausgelöster Stack-Korruption steht noch aus.

## Prüfungen

- `python test_stage532.py`: 4 von 4 Tests erfolgreich.
- Tatsächliche Generatorausgaben (`on/off`) für PE32 und PE64: 4 Varianten zu gültigen COFF-Objekten assembliert.
- UNIT- und LIBRARY-Generatorausgaben mit aktivem Cookie (`console_mode=False`) für PE32 und PE64: weitere 4 COFF-Objekte erfolgreich assembliert.
- PE32/PE64-Instruktionen des Runtime-Cookies separat mit den integrierten COFF-Assemblerroutinen geprüft.
- Stage-531-/530-Regressionstests: Assertions wurden erfolgreich ausgeführt (pytest-Prozess in dieser Umgebung beendet sich nach der Prüfungs-Ausgabe nicht verlässlich; deshalb kein vollständiger pytest-Abschluss gemeldet).
- **Nicht getestet**: Native PE32/PE64-Exe/DLL-Ausführung, konkrete Fail-Fast-Exception, VCL GUI und ein vollständiger End-to-End-Pascal-Parserlauf.

## Hinweise zur Sicherheit

Die Option ist ein zusätzliches Mitigation-Mittel für den durch Stage 531 auswählbaren Pascal-Zielcode. Für produktive Builds sind separate Speichergrenzenprüfungen und native Windows-Tests notwendig.
