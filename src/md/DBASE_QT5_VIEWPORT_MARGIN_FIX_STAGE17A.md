# dBase Qt5 Stage 17A - MinGW32/Qt5 Build-Fix

Qt5 deklariert `QAbstractScrollArea::setViewportMargins(...)` als `protected`.
Die drei direkten Aufrufe auf `QPlainTextEdit` wurden daher entfernt.

Die gewuenschte 0-Pixel-Geometrie bleibt erhalten durch:

- `QPlainTextEdit::setContentsMargins(0, 0, 0, 0)`
- `QTextDocument::setDocumentMargin(0.0)`
- Stylesheet: `border: 0px; margin: 0px; padding: 0px;`
- Layout-Margins und Spacing der umgebenden Layouts bleiben 0.

Der 3-Pixel-Seitenrahmen, die Menueleiste und die Statusleiste aus Stage 17 bleiben unveraendert.
