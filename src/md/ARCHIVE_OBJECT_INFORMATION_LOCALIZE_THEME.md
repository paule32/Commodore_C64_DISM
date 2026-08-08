# Archive-/Objektinformationen und LocalizeTool-MessageBox-Theme

Basis: d64_dism(10).py mit der zuvor additiv ergänzten C-Programme/Archive-Projektstruktur.

## Projekt-Archive

Ein Klick auf `C-Programme -> Archive -> <name>.a` öffnet im rechten Informationsbereich den Untertab `Archiv-Informationen`.

Angezeigt werden unter anderem:
- Name und Pfad
- Dateigröße
- erkannte Zielarchitektur (`Windows PE32 / COFF32` oder `Windows PE64 / COFF64`)
- Archivmitglieder
- Header- und Datenposition jedes Archivmitglieds
- Symbol-/Objektnamen
- Code/Funktion-, Data- und BSS-Klassifikation
- Sektion und Symboloffset
- absolute Symbolposition innerhalb der Archivdatei, soweit eine Raw-Position existiert

Existiert die `.a`-Datei noch nicht, wird stattdessen die im Projekt hinterlegte Objektliste mit Architektur und Größe angezeigt.

## COFF-Objektdateien

Ein Klick auf einen `.o`/`.obj`-Unterknoten öffnet `Objekt-Informationen`.

Angezeigt werden unter anderem:
- Name, Pfad und Größe
- COFF-Machine und PE32/PE64-Zuordnung
- Sektionen mit Raw-Dateiposition, Größe, Relocations und R/W/X-Rechten
- Symbole mit Name, Funktion/Data/BSS-Rolle, Sektion, Offset, Dateiposition und Storage Class

Die Analyse erfolgt direkt auf den COFF-Bytes und verwendet keine externe Toolchain.

## LocalizeTool

Alle MessageBoxen des LocalizeTools verwenden jetzt das vorhandene Theme des Hauptfensters.

Dark Mode:
- dunkler Hintergrund `#202630`
- weiße Beschriftung
- dunkle Buttons mit weißer Schrift

Light Mode:
- hellgrauer/weißer Hintergrund
- schwarze Beschriftung
- helle Buttons mit schwarzer Schrift
