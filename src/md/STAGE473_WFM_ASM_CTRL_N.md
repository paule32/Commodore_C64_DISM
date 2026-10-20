# Stage 473 – Strg+N im WFM-Assembler-TabWidget

**Verbindliche Basis:** `d64_dism_asm_472.zip`.

## Verhalten

- In beiden Assembler-Editorarten unter **Quellcode** (fester Haupt-Tab „Generierter Assembler“ und beliebige Include-/ASM-Tabs) erzeugt **Strg+N** einen neuen leeren Tab **`Unbenannt.asm`**.
- Der neue Tab besitzt rechts ein Schließen-Symbol und wird in `_dbase_form_asm_new` als **noch nicht gespeichert** markiert. Der Tooltip erläutert, dass beim ersten Speichern ein Dateiname gewählt werden muss.
- Der Fokus wird nach dem Öffnen auf den neuen Assembler-Editor gesetzt. Weitere `Strg+N`-Aufrufe erzeugen weitere unabhängige, ungespeicherte Tabs; gespeicherte Include-Dateien werden weiterhin über ihre Dateipfade gegen doppelte Tabs geprüft.
- **Strg+S** und **Datei → Speichern** benutzen weiterhin die Stage-472-Speicherlogik: neue Tabs öffnen beim ersten Speichern den Dateidialog; anschließend wird der tatsächliche Dateiname als Tabtitel gesetzt und die Neu-Kennzeichnung entfernt.
- Der **„Speichern unter“**-Dialog zeigt den vorgeschlagenen Dateinamen, zum Beispiel `Neue Assembler-Datei speichern unter – Unbenannt.asm`, in der Fenster-Titelleiste. Der standardmäßige Dateiauswahldialog erlaubt danach einen neuen Dateinamen.
- **Strg+N im WFM-Quelltext** wird von dieser Erweiterung **nicht** abgefangen. Der globale `Strg+N`-Shortcut der Hauptanwendung für „Neue Textdatei“ wird **innerhalb der ASM-Editoren** mit einem `QEvent.ShortcutOverride` abgefangen.
- Die registrierte Event-Filter-Instanz des permanenten ASM-Haupteditors wurde um dessen `QPlainTextEdit` ergänzt (bisher war nur das Viewport-Widget registriert); neue Include-Editoren besaßen die nötigen Event-Filter bereits.
- Die von Stage 472 vorhandene `%include`-Navigation, der vertikale Splitter, der unverschließbare generierte Haupt-Tab, die Speicheroptionen und das WFM-Dateihandling bleiben unverändert.

## Testnachweise

- `test_stage473_wfm_asm_ctrl_n.py`: 5 neue Tests, einschließlich simulierter Qt-Shortcut-Events ohne PyQt5.
- Zusammen mit `test_stage462...` bis `test_stage472...` (gezielte Stage-WFM-/Assembler-Tests): **107 Tests bestanden**.
- Python-Syntaxprüfung für die geänderte `d64_dism.py` erfolgreich.
- Eine zusätzliche, breiter gefasste historische Regression hat mehrere ältere Fehler angezeigt und wurde durch ein Zeitlimit beendet; dieser Lauf ist ausdrücklich **kein** vollständiger Erfolg.
- Die native Windows-/PyQt5-GUI wurde in der Linux-Testumgebung nicht interaktiv gestartet (PyQt5 hier nicht installiert).
