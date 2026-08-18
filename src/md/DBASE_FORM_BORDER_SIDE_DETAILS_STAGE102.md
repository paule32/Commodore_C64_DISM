# Stage 102 – Border-Seiten mit Detail-Eigenschaften

Jede Border-Seite `Left`, `Top`, `Right`, `Bottom` ist weiterhin per Checkbox
aktivierbar und besitzt jetzt `Style`, `Size` und `Color` als Untereinträge.
Bei `Color` sitzt rechts ein separater `...`-Button für frei wählbare Farben.

Der Border-Root bleibt als Master: Änderungen an Master-Style/Size/Color setzen
alle vier Seiten zunächst auf denselben Wert. Anschließend kann jede Seite
separat angepasst werden. Die Änderungen wirken live und werden von
Kopieren/Ausschneiden/Einfügen mitgeführt.
