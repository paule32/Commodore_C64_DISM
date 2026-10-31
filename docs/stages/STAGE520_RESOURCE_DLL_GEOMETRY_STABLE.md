[Deutsch](STAGE520_RESOURCE_DLL_GEOMETRY_STABLE.md) | [English](STAGE520_RESOURCE_DLL_GEOMETRY_STABLE.en.md)

# Stage 520 – Geometrie beim DLL-Build unverändert

**Verbindliche Basis:** Stage 519 (`d64_dism_asm_519.zip`).

## Fehlerbild

Beim Anklicken von `win32 DLL` konnte das Hauptfenster bzw. der Docking-Bereich des Ressourcen-Editors seine Breite oder Splitteraufteilung verändern. Der DLL-Build aktualisierte zuvor die gesamte Ressourcenansicht und schrieb eine ungekürzte Statusmeldung inklusive langem Ausgabepfad in das unten im Dock befindliche QLabel. Qt konnte daraus eine größere Mindestbreite für das Widget ableiten. Außerdem änderte der Build das angezeigte Compilerziel.

## Änderungen

* `WindowsResourceEditorWidget._resource_dll_source_entries()` kompiliert `.rc`-Dateien bzw. lädt `.res`-Einträge für den **Build**, ohne `_populate_tree()` und ohne Neuanordnung der TreeList, Eigenschaften oder Hex-Ansicht. Ungespeicherter RC-Text wird wie bisher gespeichert. Die Darstellung selbst wird nur über die bestehenden Vorschau-/Aktualisieren-Wege neu eingelesen.
* `compile_to_resource_dll()` übergibt ausschließlich die temporär für den Build ermittelten Einträge an `build_resource_dll_files()`; es wird **kein** `set_target()` ausgeführt. Der Klick auf win32 bzw. win64 bestimmt das Dateiformat, aber nicht die sichtbare Editor-Konfiguration.
* Status- und Dateipfad-Labels erhalten `QSizePolicy.Ignored` für die horizontale Größenanforderung und `minimumWidth=0`. Der Status wird mit `Qt.ElideMiddle` innerhalb der vorhandenen Breite angezeigt; der vollständige Text bleibt im Tooltip sowie im Statussignal für die Haupt-Statusleiste erhalten.
* Bestehende separat eingebundene Ressourcen-Editoren können die alten Methoden weiter verwenden (kompatibler Fallback).
* Das Layout der oberen Schaltflächen inklusive 14-Pixel-Abstand bleibt unverändert.

## Prüfung

* `test_stage520_resource_dll_geometry.py`: vier Tests für beide Build-Buttons, unveränderte Hauptfenster-/Dock-/Splitter-Modellzustände und UI-freien Kompiliervorgang.
* Aktualisierte Alt-Assertions der Stages 512/513: Ein DLL-Build darf das angezeigte Editorziel **nicht** mehr wechseln.
* 4 + 25 + 55 + 90 = **174 gezielte Tests** in getrennten Läufen bestanden.
* `python -m py_compile d64_dism.py` erfolgreich.

## Offener Integrationstest

Auf diesem Build-Host ist PyQt5 nicht installiert. Die Geometrieprüfungen verwenden bewusst simulierte Qt-Zustände und strukturelle Quelltextprüfungen, keinen ausgeführten Windows-Qt-Desktop. Unter Windows zusätzlich verifizieren: Hauptfenster-Rechteck, Dock-Rechteck, Floating-Zustand und Splitterpositionen vor/nach Klick auf `win32 DLL` bzw. `win64 DLL` einschließlich langer Datei-/Ausgabepfade und aktivierter Komprimierung.
