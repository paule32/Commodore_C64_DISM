woerter.dbf – dBase2Many / Agent 0003
========================================

Geprüfte und ergänzte Wortformen: 1366 Datensätze
Verschiedene Zeichenfolgen: 1348
Kodierung: dBASE III+, CP1252, Codepage-Marker 0x03
Dateipfad im Projekt: data/woerter.dbf

Felder
------
ID            Nummer des DBF-Datensatzes
WORT          Deutsche Wortform, durchgehend kleingeschrieben
WORTART       Substantiv, Verb, Adjektiv, Artikel usw.
LEMMA         Grundform; Substantive ebenfalls kleingeschrieben
SUBSTANTIV    T nur für Nomen
VERB          T nur für Verben
SINGULAR      T wenn diese Form im Singular vorkommt
PLURAL        T wenn diese Form im Plural vorkommt
DER/DIE/DAS   GRAMMATISCHES Geschlecht des Nomen-Lemmas,
              nicht der Artikel einer konkreten Satzposition
MALE/FEMALE  wie DER / DIE; meint Genus maskulin / feminin,
              nicht das biologische Geschlecht
NEUTRUM       wie DAS; bei Neutra sind MALE und FEMALE beide F
NOMINATIV    T wenn diese Wortform in diesem Kasus vorkommt
GENITIV      T wenn diese Wortform in diesem Kasus vorkommt
DATIV        T wenn diese Wortform in diesem Kasus vorkommt
AKKUSATIV    T wenn diese Wortform in diesem Kasus vorkommt
KASUS        Zusammenfassung aller wahr markierten Kasusformen

Bei Homonymen sind mehrere Datensätze mit unterschiedlicher Wortart
oder Grundform zulässig: z. B. 'fragen' als Verb und als Nomenplural.
Bei Verbformen stehen KASUS-Felder auf F (nicht anwendbar). Adjektive
benötigen zur Kasusbestimmung zusätzlichen Satzkontext; hier wird daher
kein beliebiger Kasus behauptet. Auch bei adverbialen Formen wird
kein Kasus fingiert.

Prüfung
-------
- DBF-Schreib-/Leseroundtrip identisch
- alle logischen Felder echte T/F-Werte
- DER/DIE/DAS exakt konsistent mit MALE/FEMALE/NEUTRUM
- SUBSTANTIV und VERB konsistent zur Wortart
- Singular/Plural inklusive synkretischer Formen
- Kasus-Flags konsistent mit dem lesbaren KASUS-Feld
- Schreibweise mit ß (nicht fehlerhaftes casefold zu ss)

WICHTIG: Dies ist eine geprüfte, bewusst begrenzte lexikalische Basis,
keine vollständige 10.000-Wörter-Datenbank. Das frühere Ziel von 10.000
morphologisch zuverlässig annotierten Formen ist damit NOCH NICHT erreicht.
Es wurden keine ungeprüften Wörter zum Erreichen einer Zielzahl erfunden.
Eine vollständige morphologische Abdeckung und disambiguierte Grammatik
benötigt eine entsprechend lizenzierte Referenzdatenbank bzw. NLP-Analyse.
