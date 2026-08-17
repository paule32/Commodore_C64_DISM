# PROLOG Wissen-Datenbank – Stage 71

Stage 71 baut auf Stage 70 auf. Als konkrete Darstellungsreferenz wurden der vom Benutzer hochgeladene Screenshot und das hochgeladene Archiv `d64_dism_prolog_knowledge_level_filter_stage62(1).zip` verwendet.

## Unverändert erhalten

- äußere Haupt-ScrollArea
- mehrere unabhängige innere Wissens-Abfrage-ScrollAreas
- Hinzufügen/Löschen pro Abfrage-Lane
- Fakten-/Arity-Filter links
- Parent-Pfad und eindeutige Alternativen
- grünes/rotes Label für verbleibende Alternativen
- Docking-/Theme-/F1-Property-Funktionen aus den neueren Stufen
- Consolas 9 pt, Fallback Courier New für Alternativen

## Sichtbare Alternativen

Beim Klick auf den ▼-Pfeil eines Level-Buttons wird ein lane-eigenes Auswahlpanel direkt unter der sichtbaren Button-Zeile eingeblendet:

    [ apfel ▼ ]
    [ gesund / essbar / obst ▼ ]
    [          Prüfen +          ]

Das Auswahlpanel ist kein Child des Custom-Flow-Hosts mehr, sondern ein Child des `QScrollArea.viewport()`. Die Zielposition wird aus der realen Position des Parent-Buttons berechnet:

    parent_button.mapTo(viewport, QPoint(0, row_h + 4))

Damit wird das Panel nicht mehr durch die Geometrie des FlowLayouts oder eines Level-Buttons abgeschnitten.

Der Stage-62-Referenzstand öffnete nach dem Pfeilklick unmittelbar die ComboBox-Liste. Dieses Verhalten ist wieder aktiv: `QTimer.singleShot(0, self.alternative_combo.showPopup)`.

## Prüfen +

Der lokale Button unter der Alternativen-ComboBox heißt `Prüfen +`.

Bei Erfolg:

1. gewählte Alternative wird über den bestehenden PROLOG-Prüfpfad geprüft,
2. ComboBox/Prüfen+-Panel wird ausgeblendet,
3. der neue Wert wird rechts als nächster Level-Button angefügt,
4. Alternativenstatus wird neu berechnet.

Beispiele:

    apfel -> gesund
    apfel -> essbar
    apfel -> obst

Bei Fehlschlag bleibt das Panel sichtbar und eine andere Alternative kann gewählt werden.

## Tests

- Stage-71-spezifisch: 8/8
- vollständige Regression: 712/712

PyQt5 ist in der Containerumgebung nicht installiert; eine native visuelle Windows-Ausführung wurde daher nicht behauptet.
