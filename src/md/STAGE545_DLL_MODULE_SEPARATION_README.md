# Stage 545 – Pascal-DLL/EXE-Modultrennung

Basis: `d64_dism_stage544.zip`. Geändert: `c64pascal/compiler.py`, `d64_dism.py`, `pascal_parallel_build.py` sowie gezielte Pascal-Runtime-Units. Neu: `pascal_library_contract.py`, `test_stage545.py`.

## Ziel

Beim Build einer Pascal-`library Runtime;` liegen die implementierten Klassen und öffentlichen Unit-Routinen in `Runtime.dll`. Ein Programm mit explizitem `{$L Runtime}` verwendet für diese Klassen und Routinen DLL-Imports, nicht dieselben Methoden-/Unit-Objekte erneut im EXE-Image. Die `.pui`-Dateien bleiben ausschließlich Schnittstellenmetadaten.

## Vorgehen

1. Die DLL **zuerst** aus `library Runtime; uses System, Windows; begin end.` für die gewünschte Architektur (PE32 oder PE32+) komplett neu erstellen. Nicht nur die Pascal-Quelltexte, auch die DLL und die PUI/COFF-Zwischenprodukte neu erzeugen.
2. Der Compiler erzeugt im Pascal-Unit-Ausgabeverzeichnis `Runtime.paslib.json`; die IDE legt diese JSON-Datei beim anschließenden echten DLL-Link auch neben die fertige DLL.
3. In das **Hauptprogramm** die Direktive `{$L Runtime}` aufnehmen, etwa:

   ```pascal
   program test_raise;
   {$L Runtime}
   uses System, Windows;
   var Application: TApplication;
   begin
       Application := TApplication.Create;
       Application.Free;
   end.
   ```

4. Sicherstellen, dass `Runtime.dll`, `Runtime.paslib.json` und die zur Architektur passenden `.pui`-Dateien über die festgelegten Such- beziehungsweise Ausgabeverzeichnisse auffindbar sind. Windows benötigt `Runtime.dll` bei Ausführung im DLL-Suchpfad, in der Regel im Verzeichnis der EXE.
5. Das Hauptprogramm neu kompilieren und linken. Alte `.o`/`.asm`/`.pui`-Produkte aus einem gemischten Build entfernen, damit sie nicht versehentlich mitgelinkt werden.

## Konkrete Implementierung

- `pascal_library_contract.py`: separates, versions- und zielarchitekturabhängiges DLL-Besitzverzeichnis ohne Pascal-Quelltext, Funktionszeiger oder Adressen. Die exportierten Symbole werden aus der tatsächlichen erzeugten DLL-Assemblerausgabe ermittelt. Der Vertrag enthält bereitgestellte Unit-Namen, Klassen sowie öffentlich erreichbare globale Routinen. Er wird atomar geschrieben.
- `_PascalUnitResolver`: Eine explizit mittels `{$L ...}` eingebundene DLL mit passendem Vertrag bewirkt bei ihren Units die **metadata-only**-Auflösung. Für diese Units werden weder die Original-COFF-Objekte noch Unit-ASM oder Implementierungsrümpfe in das Programm übernommen. Fehlt der Export einer verwendbaren Klasse, erfolgt ein eindeutiger Compilerfehler statt eines stillen statischen Fallbacks.
- Öffentliche Unit-Funktionen/Prozeduren werden als `D64_<Unit>_<Name>` exportiert, sofern sie tatsächlich implementiert sind. Ihr interner Pascal-Name muss nicht mit dem DLL-Exportsymbol identisch sein. Die EXE bekommt einen externen Aufruf mit dem in der `.pui` beschriebenen Pascal-Typvertrag.
- Exportierte Instanzmethoden und Konstruktorfabriken verwenden die bereits vorhandenen Stage-542-Brücken; die EXE kompiliert deren Rümpfe nicht erneut.
- Quellen `System.Objects.pas` (`TObject`), `System.SysUtils.pas` (`Exception`), `VCL.Windows.pas` (`TWindow`, `TForm`) und `Windows.Application.pas` (`TApplication`) sind in beiden gelieferten Runtime-Quellbäumen nun explizit für DLL-Exporte markiert. **Ein Bibliotheksneubau ist erforderlich.**
- Die IDE übergibt die bei der Vorverarbeitung entfernte `{$L Runtime}`-Angabe nun ausdrücklich über `linked_dll_files` an den Compiler, auch im parallelen Pascal-Worker. Damit geht die DLL-Bindung vor der eigentlichen Semantikanalyse nicht mehr verloren.
- Linker-Vorprüfung: DLL-Architektur, vorhandene PE-Exportnamen und der Sidecar-Vertrag werden gegengeprüft. Bei abweichenden DLLs wird nicht wieder auf lokalen Unit-Maschinencode zurückgefallen.
- `{$L inttostr.o}` oder ähnliche Abhängigkeiten **innerhalb einer aus DLL importierten Unit** gehören nur zur erzeugten DLL; sie werden nicht zusätzlich als Objektdateien der EXE übergeben. Explizite Objektlinks des Hauptprogramms bleiben erhalten.

## Grenzen

- Die DLL wird durch den Pascal-Compiler vorbereitet, ihr tatsächliches PE-Image muss aber wie bisher mit dem Windows-COFF-Linker erzeugt werden. Der `.paslib.json`-Vertrag alleine ist **keine** DLL und ersetzt nicht deren Exporttabelle.
- Es werden nur im Vertrag vorhandene, exportierte Schnittstellen DLL-basiert; nicht zugeordnete Units bleiben lokal. Die EXE enthält weiterhin ihren eigenen Programm-/Startcode und benötigte Runtime-Hilfen. Eine absolut duplikatfreie Gesamtlaufzeit ist nicht behauptet.
- Das Klassenexport-ABI ist noch eingeschränkt: keine vollständige Unterstützung für überladene Methoden und komplexe by-value-Parameter sowie lokale Klassen, die exportierte Klassen DLL-übergreifend ableiten. Klassenlayout, Ownership und Speicherfreigabe dürfen architekturübergreifend nicht vermischt werden.
- Bestehende lokale `.o`-Dateien dürfen nicht zusätzlich über `{$L foo.o}` eingebunden werden, wenn ihr Code bereits in der DLL liegt. Der Compiler schützt bei paketverwalteten Units vor automatisch vererbten Objektlinks, nicht vor absichtlich explizit angegebenen doppelten Dateien im Hauptprogramm.
- Funktionale Win32-/Win64-DLL-Erstellung und Start sowie Bildgrößenmessungen wurden in dieser Umgebung nicht nativ bestätigt. Bitte `Runtime.dll` und anschließend `test_raise.exe` unter Windows erneut bauen, bei 32/64 Bit getrennt, und die Importtabelle bzw. Assemblerlabels vergleichen.

## Prüfungen

`python -m unittest -v test_stage545`

6 Stage-545-Tests (sieben `subTest`-Architekturdurchläufe) plus 34 gezielt ausgeführte Alt-Tests erfolgreich, insgesamt 40 Python-Tests. Zusätzlich Syntaxprüfung des modifizierten `compiler.py`; `d64_dism.py` enthält bereits vor Stage 545 Python-3.15-`lazy`-Imports, daher wurde die Syntaxprüfung dieser Datei mit ausschließlich temporär neutralisierten `lazy`-Schlüsselwörtern unter Python 3.13 durchgeführt. Vollständiger nativer Windows-PE32-/PE32+-Build steht aus.
