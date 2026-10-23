# Stage 489 – Menü »Erstellen«: alle sechs Compilerziele auswählbar

Verbindliche Grundlage: `d64_dism_asm_488.zip`.

## Ursache
Die Stage-488-Methode `_build_menu_select_target()` hat eine Wahl bereits *beim
Anklicken* zurückgewiesen, wenn für die aktuelle Quelldateisprache kein
Compiler-Backend existierte. `_build_menu_sync_target()` hat danach die
Markierung erneut aus `document.build_target` (oft PE32) gesetzt. Dadurch
ließ sich die alternative Wahl nicht dauerhaft markieren.

## Korrektur
- Genau eine exklusive Auswahlgruppe mit sechs checkbaren Aktionen:
  `pe32`, `pe64`, `linux32`, `linux64`, `c64`, `amiga`.
- Jede Aktion ist wählbar, auch bevor ein Quelldokument geöffnet ist.
- Zur deutlichen Sichtbarkeit zeigt die ausgewählte Aktion sowohl die normale
  Qt-Radio-Markierung (`setChecked(True)`) als auch ein `✓` vor ihrem Namen.
  Die Eigenschaft `compiler_target_selected` kennzeichnet die Auswahl auch
  programmatisch.
- Pro offenem Dokument wird die Benutzerwahl über
  `document.build_menu_requested_target` festgehalten. Dadurch bleibt ein
  Wunschziel auch dann sichtbar, wenn für die Sprache kein Backend existiert.
- Der WFM-Designer bietet seine bisherigen PE32, PE64, Linux32, Linux64 und
  neu zusätzlich Amiga 500 und Commodore C=64 an. Eine Auswahl im Menü wird
  in die ComboBox übernommen; eine Auswahl in der ComboBox wird zurück ins
  Menü synchronisiert.
- Vor jedem Menü-Build wird die *gewählte* Zielplattform geprüft. Eine nicht
  implementierte Kombination führt zu einer ausdrücklichen Meldung, die
  Zielmarkierung bleibt aber aktiv. Insbesondere .prg und .wfm werden
  nicht mehr stillschweigend nach PE32 umgeschaltet.
- Erfolgreiches Kompilieren und Starten bleibt an die tatsächlichen
  verfügbaren Backends und den bestehenden Build-Erfolgsstatus gebunden.

## Implementierungsgrenze
Diese Stage implementiert **keinen neuen dBASE-/WFM-Codegenerator** für
Amiga 500 oder C64. Die Menüwahl ist möglich und wird vermerkt;
»Kompilieren«/»Kompilieren + Linken« melden bei fehlendem Backend
»Compilerziel nicht verfügbar«.

## Prüfung
- `test_stage489_all_build_targets.py`: sechs Auswahlmöglichkeiten,
  WFM-ComboBox, exklusive Markierung, auswählbar ohne Dokument,
  kein Zurückspringen auf PE32, Meldung beim Build.
- Bestehende Stage-480/481-Menütests für Build und Start.
- Python-Syntaxprüfung von `d64_dism.py`; ZIP-Integritätsprüfung.
- Native Windows-/Linux-GUI-Interaktion bleibt ausstehend (PyQt5 in dieser
  Testumgebung nicht installiert).
