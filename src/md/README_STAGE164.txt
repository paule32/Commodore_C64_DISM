Stage 164 – DBF öffnen / NonVisual-Komponenten / TAB-Navigation / 4-Space-Indent

Datei -> Öffnen
- *.dbf ist im Erweiterungsfilter enthalten.
- DBF-Dateien werden nicht als Texteditor geöffnet.
- Öffnen einer DBF aktiviert den Tabellen-Designer und fokussiert den inneren Tab Daten.
- Bereits im Tabellen-Designer geöffnete DBFs werden wiederverwendet.

Formdesigner Nicht-visuelle Komponenten
- Timer, Session, Database, SQL, Query (Legacy), DataSource und Table sind fest 42x42.
- Resize-Rahmen/Knubbel bleiben sichtbar.
- Eigenschaften: Position (Left, Top editierbar; Width, Height sichtbar aber gesperrt), Name, Active / Enabled.
- Timer zusätzlich: Intervall, OnTimer. (WFM-Schlüssel bleibt kompatibel: Interval)
- Brush/Font/Border/HWND werden für diese Komponenten nicht angezeigt.
- Left/Top/Width/Height/Active werden im WFM gespeichert und beim Laden wieder übernommen.
- Timer speichert zusätzlich Interval/OnTimer.
- Datenbank-Palette: Session, Database, SQL, DataSource, Table. Query bleibt intern nur zum Laden älterer WFM-Dateien kompatibel.

TAB im Formdesigner
- TAB springt in geometrischer Reihenfolge zur nächsten Komponente.
- Shift+TAB/Backtab springt zurück.
- Vorherige Selektion/Fokus wird entfernt, damit nur der aktuelle Resize-Rahmen sichtbar bleibt.
- Property/Event-Ansicht folgt über selectionChanged automatisch.

TAB im Quellcode-Editor
- TAB ohne Auswahl: vier Leerzeichen.
- TAB mit Auswahl: alle betroffenen Zeilen +4 Leerzeichen.
- Shift+TAB/Backtab: bis zu vier führende Leerzeichen entfernen.
- ALT+TAB wird ebenfalls als Outdent behandelt, falls Windows das Ereignis an Qt weiterreicht. Unter Windows ist ALT+TAB normalerweise ein systemweiter Fensterschalter; deshalb ist Shift+TAB die zuverlässige In-App-Variante.
- Ein vorhandener führender #9-Tab wird beim Outdent als eine Einrückungsstufe entfernt.

py_compile: OK
