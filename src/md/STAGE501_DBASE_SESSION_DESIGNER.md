# Stage 501 – dBASE-Formulardesigner: SESSION-Komponente

**Basis:** `d64_dism_asm_500(1).zip` – kein anderer Entwicklungszweig.

## Darstellung

- Ein transparentes **36 × 36 Pixel** großes `assets/dbase_session_36.png` stellt eine Datenbank mit Benutzer-Symbol dar.
- Das PNG wird über `d64dbase.session_designer.session_icon_png_bytes()` eingebettet; seine Pixmap erscheint zentriert in der vorhandenen nicht-visuellen **42 × 42** großen Session-Komponente.
- Dieselbe Pixmap erscheint in der Datenbank-Komponentenpalette.
- Alle anderen Komponenten behalten ihre Darstellung und Größe.

## Session-Inspector

Nur bei Selektion einer Session erscheinen zusätzliche Gruppen:

- **Identifikation**
  - `baseClassName`: schreibgeschützt, `SESSION`
  - `className`: schreibgeschützt, die WFM-Klasse (standardmäßig `SESSION`)
  - `name`: editierbar
  - `parent`: schreibgeschützt; Doppelklick selektiert das Parent-Item und zeigt dessen Eigenschaften.
- **Verschiedenes**
  - `lockRetryCount`: `QSpinBox`, Standardwert 3, Minimum 0
  - `lockRetryInterval`: `QSpinBox`, Standardwert 1000, Minimum 0

Beide Retry-Werte werden im WFM mit ihrem Namen gespeichert und beim Laden wieder eingelesen; sie bleiben beim Kopieren/Einfügen erhalten. Die beiden Standardwerte sind Designer-Vorgaben.

## Ereignisse

Für Session gibt es `beforeRelease` und `onPregress` (genau diese Schreibweise). Event-Prozeduren können über die bestehende Eventnavigation angelegt und bearbeitet werden. Der WFM-Parser erkennt jetzt auch `beforeRelease` als Event statt als normale Eigenschaft; die Eventbindungen von nicht-visuellen Komponenten werden beim Laden übernommen.

## Methoden

Der bisher leere Tab **Methoden** besitzt für Session eine Tabelle mit Doppelklick:

| Methode | Wert |
| --- | --- |
| access | SESSION::ACCESS |
| addAlias | SESSION::ADDALIAS |
| addPassword | SESSION::ADDPASSWORD |
| deleteAlias | SESSION::DELETEALIAS |
| isAlias | SESSION::ISALIAS |
| login | SESSION::LOGIN |
| user | SESSION::USER |

Ein Doppelklick auf einen Eintrag öffnet den vorhandenen WFM-Quellcodeeditor und fügt die passende Funktion ein, falls sie noch nicht existiert, z. B.:

```dbase
    function SESSION1_addAlias(param)
        return SESSION::addAlias(param)
```

Bei erneutem Doppelklick wird zur vorhandenen Methode navigiert, ohne sie erneut anzulegen. Ein unvollständig editierter WFM-Quelltext wird nicht durch den Designer überschrieben.

## Prüfung

- Original-Stage-500-Projekt bleibt enthalten.
- `test_stage501_session_designer.py`: PNG, Methodennamen, Codevorlage und WFM-Parsing inklusive `beforeRelease`/`onPregress`.
- Gemeinsam mit bestehenden Formular-/Editor-Regressionstests: **38 Tests erfolgreich**.
- Python-AST-Syntaxprüfung der vollständigen `d64_dism.py` erfolgreich.
- **Offen:** nativer PyQt5-Fenstertest unter Windows/Linux und die tatsächliche Backend-/Runtime-Implementierung der SESSION-Methoden. Der neue Tab generiert die gewünschten Quelltext-Wrapper, keine zusätzlichen Runtime-Exports.
