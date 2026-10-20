# Stage 474 – WFM Assembler-Tabs: Stil, Kontextmenü, rotes Schließen, Counter

**Verbindliche Grundlage:** `d64_dism_asm_473.zip`

## Implementierung (`d64_dism.py`)

- Zusätzliche Assembler-Editoren übernehmen jetzt `QPalette` des generierten
  Haupt-Assembler-Editors (navyblauer Codehintergrund und gelbe Standard-Schrift),
  einschließlich Viewport. Der Gutter verwendet `set_gutter_dark_mode(True)`.
- `AssemblerSyntaxHighlighter` bleibt für jeden Tab aktiviert; vorhandene
  Editorfunktionen (MiniMap, Editor-Hilfe, Suchen, F2) bleiben bestehen.
- Bei Live-Theme-Wechsel werden alle WFM-Assembler-Editoren erneut auf das
  Stilprofil des Haupt-Assembler-Editors synchronisiert.
- Das `SourceTextEdit`-Kontextmenü wird für die WFM-ASM-Editoren um den **ersten**
  Menüpunkt `Neu Assembler` erweitert, gefolgt von einem Separator und den
  bisherigen Menüpunkten. Beim Klick auf einen `%include`-Dateinamen folgen
  `In neuen Tab öffnen` / Separator / `Hilfe` vor den normalen Editieraktionen.
  Das frühere Eventfilter-Spezialmenü wird nicht mehr vorgeschaltet.
- Zusätzliche Tabs erhalten rechts ein 12x12 Pixel großes rotes X-Symbol
  (eigener transparenter QPixmap/QIcon), das erste generierte Tab bleibt fest.
- Alle Wege zum Erstellen neuer ASM-Tabs (Strg+N, Datei > Neu > Assembler >
  Programm, Kontextmenü) verwenden einen gemeinsamen laufenden Zähler ab 1:
  `Unbenannt_1.asm`, `Unbenannt_2.asm`, usw.
- Beim Schließen des Formular-Designers bzw. des gesamten Formular-Workspaces
  wird der Zähler auf 1 zurückgesetzt. Sind durch das bloße Schließen/Hiding
  noch ältere Tabs vorhanden, wird der nächste freie Name gewählt statt einer
  Namenskollision.
- Neu angelegte Tabs bleiben weiterhin in `_dbase_form_asm_new` markiert:
  das erste Speichern öffnet weiterhin `Speichern unter` mit dem jeweiligen
  neuen Namen im Fenstertitel, danach wird die Neu-Markierung entfernt.

## Tests

- `test_stage474_wfm_asm_styles_context_counter.py`: fünf neue Prüfungen zu
  Nummerierung, Reset/Namenskollision, Farbpalette und Gutter,
  Kontextmenü-/Include-Kompatibilität und rotem Close-Icon.
- Relevante Stages 467, 469, 470, 471, 472, 473, 474:
  **46 bestanden**.
- Im größeren historischen Testbereich bestehen alte, sachlich unabhängige
  Fehler in Stage-450/452/453-Tests zu D64Z/MSZIP/NTFS-Kompression; die
  betreffenden Packer-/Runtime-Dateien wurden nicht verändert.
- PyQt5 ist in dieser Linux-Testumgebung nicht installiert. Echtes
  Windows-Rendering, Klick- und Menübedienung wurden nicht nativ getestet.
