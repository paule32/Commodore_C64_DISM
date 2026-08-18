# Stage 92 – dBase Formulardesigner Brush/Patterns

Stage 92 baut additiv auf Stage 91 auf.

## Resize-Vorschau

Der gestrichelte Vorschaurahmen während eines Resize-Vorgangs wird jetzt hellgrau (`#CDCDCD`) gezeichnet. Der eigentliche Fokus-/Selektionsrahmen bleibt davon unabhängig.

## Brush-Eigenschaften

Im Eigenschaftenbaum gibt es den neuen Root-Knoten `Brush` mit:

- `Background` – Hintergrundfarbe / Grundfläche.
- `Foreground` – Vordergrundfarbe des Patterns und zugleich Schriftfarbe eines Controls.
- `Style` – `Ohne Muster` oder eines von 12 Pattern-Mustern.

Die Farbreihen besitzen weiterhin einen editierbaren Hex-Wert und einen `...`-Button für den QColorDialog. Der Button zeigt zusätzlich die aktuelle Farbe als kleine Farbfläche.

## Pattern-Quelle

Die 12 Muster wurden aus der vom Benutzer gelieferten Referenzgrafik extrahiert. Die dicken schwarzen Außenrahmen der Musterkästchen wurden nicht übernommen. Jede Vorlage wird intern als 48×48-Schwarz/Weiß-Maske direkt in `d64_dism.py` gespeichert. Es besteht deshalb keine Laufzeitabhängigkeit von der hochgeladenen Bilddatei.

Masken-Semantik:

- Schwarz der Maske → `Foreground`
- Weiß der Maske → `Background`

Damit entspricht die Standarddarstellung der Vorlagen einem schwarzen Hintergrund mit weißem Muster. Änderungen an Background/Foreground färben die ComboBox-Vorschau und die Komponente dynamisch neu.

Die normalisierten Masken liegen zur Kontrolle zusätzlich unter `resources/form_brush_patterns/`. `FORM_BRUSH_PATTERNS_STAGE92.png` zeigt alle 12 Vorlagen ohne den ursprünglichen dicken Außenrand.

## Buttons

Für `QPushButton` wird die Farbe zusätzlich über ein lokales Stylesheet abgesichert, damit native Windows-/Qt-Styles die im Designer eingestellte Farbe nicht wieder mit einer Systemfarbe überschreiben.

- Style `Ohne Muster`: `Background` färbt die Buttonfläche; `Foreground` färbt die Schrift.
- Pattern-Style: Buttonfläche wird transparent, die Pattern-Brush wird darunter gezeichnet; `Foreground` bleibt gleichzeitig Schriftfarbe und Musterfarbe.

## Regression

- Stage-90/91/92-Fokustests: 22/22 OK
- Gesamte Testsuite: 837/837 OK
- Syntax: `compile(..., 'exec')` OK

PyQt5 ist in der Test-Containerumgebung nicht installiert; die native Qt5-GUI konnte dort daher nicht visuell gestartet werden.
