# Stage 54 – Markdown-Ansicht im Texteditor

## Ziel

Markdown-Dateien (`.md`, `.markdown`) besitzen zwei gekoppelte Ansichten:

- **Rohdaten**: editierbarer Quelltext mit Zeilennummern-Gutter, Breakpoints/Bookmarks und Mini-Map.
- **MarkDown**: read-only Vorschau auf Basis von `QPlainTextEdit`.

Die Vorschau wird aus dem aktuellen Rohtext aufgebaut. Änderungen im Rohdaten-Editor werden nach 35 ms Entprellung neu gerendert.

## Darstellung

Es wird bewusst kein QWebEngine/QTextBrowser als Renderer verwendet. `MarkdownPreviewEdit` ist ein `QPlainTextEdit`, dessen `QTextDocument` über `QTextCursor`, `QTextCharFormat` und `QTextBlockFormat` formatiert wird.

Unterstützte GitHub-ähnliche Konstrukte:

- `#` bis `######` Überschriften
- **fett** und *kursiv*
- `Inline-Code`
- fenced Codeblöcke mit ``` oder ~~~
- Links `[Text](URL)`; Klick öffnet die URL
- Bilder werden ohne Pixel-Renderer als `[Bild: Alttext]` dargestellt
- Blockquotes
- ungeordnete und nummerierte Listen
- Task-Listen `[ ]` / `[x]`
- `~~durchgestrichen~~`
- horizontale Trennlinien
- GitHub-Flavoured Markdown Tabellen

## Theme

Markdown-Rohdaten und Vorschau folgen dem globalen Modus:

### Dark

- Hintergrund: `#0D1117`
- Text: `#C9D1D9`
- Gutter: `#161B22`
- Links/Headings: GitHub-nahe Blautöne

### Light

- Hintergrund: `#FFFFFF`
- Text: `#24292F`
- Gutter: `#F6F8FA`

Die Mini-Map übernimmt ihre Farben weiterhin direkt aus der Palette des Rohdaten-Editors.

## Rohdaten-Syntaxhighlighting

`AssemblerSyntaxHighlighter` besitzt ab Stage 54 zusätzlich einen Markdown-Modus. Hervorgehoben werden u. a.:

- Überschriften
- Listenmarker
- Blockquotes
- Links
- fett/kursiv/durchgestrichen
- Inline-Code
- fenced Codeblöcke

## Live-Kopplung

`raw_editor.textChanged` ruft `_markdown_source_changed()` auf. Für Markdown-Dateien wird der aktuelle Inhalt an `MarkdownPreviewEdit.set_markdown_source()` übergeben. Ein Single-Shot-QTimer verhindert unnötiges komplettes Rendern bei jedem unmittelbar aufeinanderfolgenden Tastendruck.

## Bestehende Editorfunktionen

Der Rohdaten-Editor bleibt `SourceTextEdit` innerhalb von `SourceEditorWithMiniMap`. Dadurch bleiben erhalten:

- Zeilennummern-Gutter
- Breakpoints
- Bookmarks/Favoriten
- Mini-Map
- bidirektionale Mini-Map-Scrollkopplung aus Stage 48/49

## Beispiel

`examples/markdown/markdown_demo.md`

## Tests

Neue Stage-54-Tests: 10.
Gesamter Projektstand: 565/565 Tests erfolgreich.

Hinweis: In der Container-Umgebung ist PyQt5 nicht installiert. Deshalb konnte die Qt5-GUI hier nicht nativ gestartet werden. Die Python-Syntaxprüfung (`py_compile`) und die vollständigen vorhandenen Regressionstests sind erfolgreich.
