> **Hinweis:** Stage 15 ersetzt die damalige unquoted-Farbnamensyntax. Direkte Systemfarbnamen muessen ab Stage 15 in Anfuehrungszeichen stehen; unquoted Namen sind nur noch echte Symbole.

# dBase Stage 14 - `_app.colorNormal` und Windows-Systemfarben

Stage 14 erweitert das globale `APPLICATION`-Objekt `_app` um die Property
`colorNormal`. Sie setzt den Hintergrund des Qt5-`QPlainTextEdit` im Tab
`Konsole`. Der DEBUG-Editor, die Schriftfarbe und die Zoom-Einstellungen werden
nicht veraendert.

## Syntax

Beide Formen sind gueltig:

```dbase
_app.colorNormal = ActiveBorder
_app.colorNormal = "ActiveBorder"
```

`this.colorNormal` ist auf Top-Level wie bisher ein Alias fuer
`_app.colorNormal`.

## Unterstuetzte Namen

| dBase-Name | Windows-Systemfarbe |
|---|---|
| ActiveBorder | `COLOR_ACTIVEBORDER` |
| ActiveCaption | `COLOR_ACTIVECAPTION` |
| AppWorkspace | `COLOR_APPWORKSPACE` |
| Background | `COLOR_BACKGROUND` |
| BtnFace | `COLOR_BTNFACE` |
| BtnHighlight | `COLOR_BTNHIGHLIGHT` |
| BtnShadow | `COLOR_BTNSHADOW` |
| BtnText | `COLOR_BTNTEXT` |
| CaptionText | `COLOR_CAPTIONTEXT` |
| GrayText | `COLOR_GRAYTEXT` |
| Highlight | `COLOR_HIGHLIGHT` |
| HighlightText | `COLOR_HIGHLIGHTTEXT` |
| InactiveBorder | `COLOR_INACTIVEBORDER` |
| InactiveCaption | `COLOR_INACTIVECAPTION` |
| InactiveCaptionText | `COLOR_INACTIVECAPTIONTEXT` |
| InfoText | `COLOR_INFOTEXT` |
| InfoBk | `COLOR_INFOBK` |
| Menu | `COLOR_MENU` |
| MenuText | `COLOR_MENUTEXT` |
| Scrollbar | `COLOR_SCROLLBAR` |
| Window | `COLOR_WINDOW` |
| WindowFrame | `COLOR_WINDOWFRAME` |
| WindowText | `COLOR_WINDOWTEXT` |

Die DLL liest die aktuelle Farbe unter Windows ueber `GetSysColor()`. Damit
werden keine festen RGB-Werte in die dBase-EXE eingebrannt.

## C-ABI der Bridge

Neu exportiert `d64qt5.dll`:

```cpp
int DBaseQtSetColorNormal(const char *name, int length);
```

Rueckgabe `1` bedeutet erfolgreich gesetzt, `0` unbekannter/ungueltiger Name.
Der Compiler validiert die Namen bereits vorher, sodass ein normal erzeugtes
Programm nur gueltige Werte uebergibt.

## PE32

Sinngemaess:

```asm
push 12
push __dbase_text_activeborder
call DBaseQtSetColorNormal
add esp, 8
```

## PE32+

Sinngemaess:

```asm
mov rcx, __dbase_text_activeborder
mov edx, 12
sub rsp, 40
call DBaseQtSetColorNormal
add rsp, 40
```

Die Qt5-Bridge muss wie bisher passend zur Zielarchitektur gebaut sein: 32 Bit
fuer PE32 und 64 Bit fuer PE32+.
