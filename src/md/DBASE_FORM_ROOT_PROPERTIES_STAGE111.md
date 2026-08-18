# Stage 111 – FORM als Designer-Root

Stage 111 erweitert die in Stage 110 eingeführte visuelle WFM-Hauptform zu einem eigenständigen Designer-Objekt.

## Abstand

Die äußere Fensterkante liegt im Formular-Designer exakt 5 Pixel von der linken und oberen Arbeitsflächenkante entfernt. `Form.Left` und `Form.Top` bleiben davon unabhängig Runtime-Eigenschaften der WFM-Datei.

## Selektion und Eigenschaften

Ein Klick auf freie Clientfläche oder Titelbalken selektiert die Root-`FORM`. Der vorhandene Property-Editor wird auch für die Form verwendet. Verfügbar sind derselbe Positions-, Brush-, Font- und Border-Eigenschaftssatz wie bei Designer-Komponenten. `Width` und `Height` ändern die sichtbare Clientfläche; `Top` und `Left` ändern nur die späteren Runtime-Werte.

Die Form speichert und lädt Brush/Gradient/Pattern-Cut, Font, Fontfarben/Alpha, Border-Root, Shadow Color, alle vier Radien sowie die vier getrennten Border-Seiten mit Enabled/Style/Size/Color.

## Kontextmenü

Auf freier Formfläche steht dasselbe Menü wie bei Controls zur Verfügung: Hilfe, Kopieren, Einfügen, Ausschneiden und Entfernen. Die einzige Root-Form selbst wird nicht aus der Scene gelöscht; Ausschneiden/Entfernen leeren den Formularinhalt, damit die Designer-Arbeitsfläche bestehen bleibt.

## Resize-Fix

Control-Resize arbeitet jetzt vollständig im lokalen Koordinatenraum seines Parents. Controls direkt auf der Form arbeiten in Form-Koordinaten, Panel-Children in Panel-Koordinaten. Preview, Limits und Endgeometrie werden nicht mehr zwischen Scene- und Parent-Koordinaten gemischt. Die bestehenden Form-/Panel-/Border-Designerlimits bleiben erhalten.

## d64qt5

Die sechs Qt-Runtime-Quelldateien bleiben unverändert gegenüber Stage 110 und liegen ausschließlich im ZIP-Verzeichnis `d64qt5/`.
