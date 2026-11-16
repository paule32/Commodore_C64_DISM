# Stage 577 – Prolog-Widerspruchsprüfung für Agent 0002

**Verbindliche Ausgangsbasis:** `d64_dism_stage576.zip`.

## Erweiterungen

* `agent_0002_logic.py`: Satznahe Erkennung weniger deutscher geometrischer Adjektive inklusive einfacher Deklination (`quadratischen` → `quadratisch`). Die Eigenschaft wird nur zugeordnet, wenn sie direkt vor der Form oder in einem unterstützten Kopulasatz steht.
* `data/agent_0002_geometrie.pl`: editierbare Wissensbasis mit Eckenzahlen von Kreis, Dreieck und Quadrat und den Prolog-Prädikaten `widerspruch/2` und `vereinbar/2`. Die Regeln werden **durch den bestehenden d64prolog-Prolog-Resolver** ausgewertet, nicht per festkodierter Python-Widerspruchstabelle.
* `agent_0002_core.py`: nimmt das logische Ergebnis auf. Ein nachgewiesener Widerspruch, eine unbekannte Beweislage oder eine defekte Prolog-Wissensbasis blockieren bei erkannten Eigenschaft/Form-Paaren vorsorglich die Zeichnung. Ohne explizite Eigenschaft bleiben die bestehenden Kreis-/Dreieck-Funktionen erhalten.
* `agent_0002.py`: zeigt den logischen Prüfstatus und die Prolog-Begründung im rechten oberen Bereich an; die Zeichenfläche im unteren Bereich bleibt bei einem Widerspruch leer. Erkannte geometrische Adjektive erhalten die Wortart `Adjektiv (Geometrie)`.

## Prüffälle

| Satz | Ergebnis |
|---|---|
| `Zeige einen quadratischen Kreis` | Widerspruch – keine Zeichnung |
| `zeige quadratischen kreis` | Widerspruch – keine Zeichnung |
| `Zeige einen dreieckigen Kreis` | Widerspruch – keine Zeichnung |
| `Zeige einen runden Kreis` | Bezüglich der Eckenzahl vereinbar – Kreis |
| `Was ist ein Kreis?` | Kreis |
| `Zeige mir ein Dreieck` | Dreieck |

Prolog-Abfragen:

```prolog
?- widerspruch(quadratisch, kreis).  % true
?- vereinbar(rund, kreis).         % true
```

## Speicherort

Nach dem Entpacken:

```text
d64_dism.py
agent_0002.py
agent_0002_core.py
agent_0002_logic.py
d64prolog/
data/
  agent_0002_geometrie.pl
```

Für eine eingefrorene Windows-EXE wird die Wissensbasis aus `<EXE-Verzeichnis>/data/agent_0002_geometrie.pl` geladen. Bei normalem Quellstart wird das `data`-Verzeichnis neben den Python-Dateien verwendet. Eine vorhandene Datei wird nicht überschrieben.

## Grenzen

- Kein vollständiges Parsing freier deutscher Texte und keine allgemeine Prüfung logischer Wahrheit. Unterstützt werden nur wenige geometrische Eigenschaft/Form-Kombinationen.
- `vereinbar` bedeutet ausschließlich: Die hinterlegten Eckenzahlregeln widersprechen sich nicht. Andere mögliche Eigenschaften werden dadurch nicht bewiesen.
- Bei fehlenden oder fehlerhaften Prolog-Daten wird ein Fehler angezeigt und für bekannte Eigenschaft/Form-Paare vorsichtshalber keine Zeichnung erzeugt.
- Der Agent prüft die **Semantik** unabhängig von einer vollständigen grammatischen Validierung; so wird auch die artikellose Kurzform `zeige quadratischen kreis` semantisch geprüft, ohne sie als grammatisch korrekt zu deklarieren.
- Die native PyQt5-Oberfläche und der Windows-Theme-Wechsel müssen auf dem Zielsystem geprüft werden.

## Tests

`python -m pytest -q test_stage577.py test_stage576.py test_stage575.py`

Prolog-Fakten, Widerspruchs-/Vereinbarkeitsprüfung, Satzmuster, fehlende oder beschädigte Wissensbasis, Rückwärtskompatibilität und ursprüngliche Agent-0002-Importkollision werden abgedeckt.
