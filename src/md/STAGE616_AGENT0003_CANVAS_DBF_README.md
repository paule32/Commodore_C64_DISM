# Stage 616 – Agent 0003: Qt-Canvas-Lebensdauer und kompakte Wörter-DBF

Basis: `d64_dism_stage615.zip`.

## Fehlerbehebung beim Öffnen von Agent 0003

Bei Stage 615 wird das untere Panel des `GermanAssociationWidget`
(Agent 0002) entfernt. Das darin liegende Qt-Widget `AssociationCanvas`
wird dabei von Qt gelöscht, aber `self.canvas` verweist noch auf den
ungültigen SIP/PyQt-Wrapper. `GermanAssociationWidget.set_dark_mode()`
ruft dann `self.canvas.set_dark_mode()` auf und wirft `RuntimeError`.

- `agent_0003.py`: Setzt `self.canvas = None` **vor** dem Herauslösen des
  alten Panels aus dem Splitter und plant die spätere Freigabe via
  `old.deleteLater()` ein.
- `agent_0002.py`: Ruft die Theme-Funktion des Canvas nur auf, wenn die
  Referenz nicht `None` ist. Agent 0002 bleibt unverändert nutzbar.
- Dark-/Light-Mode und restliche Panel-Anordnung bleiben erhalten.

## Kompakte `data/woerter.dbf`

Die bisherige DBF wurde auf 17 Felder umgestellt, darunter `ADJEKTIV`
als einbyteiges dBASE-III+-Logikfeld **direkt hinter `VERB`**.
Die redundanten Felder `WORTART`, `KASUS`, `LEMMA` wurden entfernt.
Die Fallmerkmale bleiben als Booleans `NOMINATIV`, `GENITIV`, `DATIV`,
`AKKUSATIV` erhalten.

Bestand: 1.366 ursprüngliche Datensätze mit 1.348 unterschiedlichen Wortformen; 18 doppelte Schreibweisen wurden unter Zusammenfassung ihrer Bool-Merkmale zusammengeführt. Anschließend 5.000 neue unterschiedliche Wortformen hinzugefügt = **6.348 Datensätze**.
Im Wortschatz wird pro Wortform nur eine Zeile gehalten; das Material
umfasst Substantive, Verben und Adjektive sowie mehrere Flexionsformen.
Die Kennzeichnungen neuer Flexionsformen sind regelbasiert und daher
keine vollständige morphologische Analyse des Deutschen.
Für bestimmte Wörter ist eine Validierung im Satzkontext nötig,
insbesondere bei mehrdeutigen Wortarten, Numeri und Kasus.

`agent_0003_language.py` liest den Worttyp nun ausschließlich aus den
Logikfeldern `SUBSTANTIV`, `VERB` und `ADJEKTIV`; die Bereitstellung der
Fallback-DBF verwendet dasselbe neue Schema.

Der Dateiname und Pfad bleiben `data/woerter.dbf`.

## Wortlisten – Quellen und Lizenz

Ein Teil der neuen Wortformen basiert auf den Wortlisten
`https://github.com/cpos/AlleDeutschenWoerter` (Substantive/Verben/Adjektive),
welche unter GNU General Public License v2.0 veröffentlicht sind.
Die abgeleiteten Wortdaten werden mit der zugehörigen Lizenzinformation
und dem vollständigen Lizenztext in `licenses/woerter_GPL-2.0.txt`
weitergegeben. Regelmäßige Verb- und Adjektivformen sind aus den
Grundformen abgeleitet worden. Die ursprünglichen Listen enthalten
nicht für jede Wortform explizite Kasus-/Numerus-Informationen.

## Tests

- Python-Syntax und Struktur-/Theme-Tests
- Datenbank-Roundtrip, Anzahl, Feldreihenfolge, logische T/F-Werte
- Agent-0003-Fragen inklusive Verben, Adjektiven und Nomen
- vorhandene Stage-615-Bildtests

GUI-Laufzeittest unter Windows / PyQt5 bleibt erforderlich, weil
PyQt5 in der Prüf-Umgebung nicht installiert ist.
