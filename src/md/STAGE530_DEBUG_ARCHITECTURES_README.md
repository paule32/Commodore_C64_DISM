# Stage 530 – Debug-Einstellungen pro Windows-Architektur

**Basis:** `d64_dism_stage529.zip` (keine anderen Entwicklungszweige).

## Bedienung

- Projekt-Einstellungen → Windows → 32-Bit → Debug
- Projekt-Einstellungen → Windows → 64-Bit → Debug

Es gibt weiterhin **keinen** zusätzlichen Haupt-Tab „Debug“.
Beide TreeList-Seiten besitzen getrennte Werte für:

- Enable Debug
- CES – Check Early Start
- DWARF → Enabled
- DWARF Version 2 / 3

Die **DWARF-GroupBox ist nun physisch innerhalb der Debug-GroupBox** eingebaut.
Ein Wechsel zwischen 32-Bit- und 64-Bit-Tab verändert die jeweils andere Debug-Konfiguration nicht.

## Persistenz und Migration

Neue `.pro`-Projekte speichern die beiden unabhängigen Bereiche als:

```ini
[Settings.Windows.32Bit.Debug]
Title = Windows 32Bit Debug
EnableDebug = true
CheckEarlyStart = true
DwarfEnabled = true
DwarfVersion = 2

[Settings.Windows.64Bit.Debug]
Title = Windows 64Bit Debug
EnableDebug = false
CheckEarlyStart = false
DwarfEnabled = false
DwarfVersion = 3
```

Das Beispiel zeigt **verschiedene** Werte; die initialen Standardwerte sind alle deaktiviert, DWARF 3 ist vorausgewählt.
Bei bestehenden `.pro`-Projekten mit ausschließlich `[Settings.Debug]` wird der alte Konfigurationsstand **einmalig für beide Profile als Ausgangswert** benutzt. Beim erneuten Speichern werden separate 32-/64-Bit-Abschnitte geschrieben. Hat eine Architektur bereits einen eigenen Abschnitt, hat dieser Vorrang gegenüber dem alten gemeinsamen Abschnitt.

**Anbindung:** In der GUI werden nur die angeklickte Architektur und ihr Eintrag im Laufzeitstatus verändert. Projektöffnen, Projekterstellen, Projekt schließen und die Standard-Speicherwege berücksichtigen beide Profile. Die Hilfsfunktionen in `debug_options.py` unterstützen ein optionales `target='pe32'`/`target='pe64'` und weiterhin den Legacy-Aufruf ohne `target`.

## Backend-Status

Der von Stage 527 eingeführte CES-Diagnosecode in `_build_pe32_mszip_loader()` verwendet explizit die PE32-Optionen (Standardziel `pe32`). Die separat verwaltete PE64-CES-Option ist **noch keine Zusage**, dass dieselbe CES-Meldelogik im PE64-Loader implementiert ist; Stage 527 implementierte CES nur im PE32-Loader. DWARF 2/3 sind weiterhin Projektoptionen; das Schreiben vollständiger DWARF-Sektionen bleibt ausstehend.

## Betroffene Dateien

- `d64_dism.py` – Zustand, Navigation, Projektdatei-Laden und -Speichern
- `debug_options.py` – verschachtelte GroupBox, architekturspezifische INI-Abschnitte
- `test_stage530.py` – neue Prüfungen, inklusive Unabhängigkeit, Legacy-Migration, `.pro`-Dateien und Runtime-Zugriff
- `test_stage528.py`, `test_stage529.py` – historische TreeList-Prüfungen an den jetzt architekturgetrennten Zustand angepasst

## Prüfungen

- `test_stage527.py`: 3 bestanden
- `test_stage528.py`: 2 bestanden (an Stage 530 angepasst)
- `test_stage529.py`: 2 bestanden (an Stage 530 angepasst)
- `test_stage530.py`: 8 bestanden
- Gesamt: **15 / 15** automatisierte Prüfungen erfolgreich.

Die PyQt5-GUI wurde in dieser Laufzeitumgebung **nicht visuell** getestet, da PyQt5 nicht installiert ist. Ein nativer Windows-Test der PE32- und PE64-Builds wurde nicht durchgeführt. Die bestehenden, im Stage-529-ZIP enthaltenen Build-Artefakte wurden unverändert übernommen; sie wurden **nicht neu erzeugt**.
