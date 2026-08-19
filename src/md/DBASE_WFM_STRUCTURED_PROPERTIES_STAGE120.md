# Stage 120 - strukturierte WFM/OOP-Eigenschaften

Neue WFM-Dateien speichern Font, Brush und Border als verschachtelte WITH-Objekte. Der Parser akzeptiert weiterhin das alte flache Format.

Unterstützt werden:
- `WITH (THIS.Font)` mit Name, Size, Bold, Cursive, Stroke, Underline, Alpha, Background, Foreground.
- `NEW FONT(name,size,bold,cursive,stroke,underline)` sowie die alte 5-Argument-Form.
- `WITH (THIS.Brush)` und relativ darin `WITH (THIS.Style)`.
- `WITH (THIS.Border)` mit Shadow, Rounded und Left/Top/Right/Bottom.
- `Enabled` pro Border-Seite, damit die bisherigen Designer-Checkboxen verlustfrei gespeichert werden.
- benannte Font-Objekte (`THIS.FONT1 = NEW FONT(...)`) und `THIS.Font = THIS.FONT1`.
- Komponenten-Konstruktoren mit Standardparent THIS sowie optionalem Textargument.
- `procedure __init__`, `procedure __del__`, `function __main__` werden geparst und gespeichert.

Hinweis: Stage 120 macht diese Lifecycle-Methoden zum WFM-Modellbestandteil und bewahrt ihren Quelltext. Der bestehende Stage-118-Form-Fallback-Compiler baut weiterhin die visuelle Form direkt aus dem geparsten Modell auf; freie dBase-Anweisungen innerhalb der drei Methoden werden noch nicht als eigener dBase-Methoden-Bytecode ausgeführt.

Runtime-Ergänzungen:
- `Text` der FORM setzt den nativen Fenstertitel.
- `Name` setzt `QObject::objectName`.
- `rgb(r,g,b,a)` wird für Qt-Styles zu `rgba(r,g,b,a)` normalisiert.
