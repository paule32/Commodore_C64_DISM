# Stage 400 – C64: Compiler -> BASIC -> Dialekt

Verbindliche Ausgangsbasis: `d64_dism_asm_399.zip`.

## Benutzeroberfläche

Im Projekt-Einstellungen-Dock unter `C= 64` existieren für die Profile
`68000`, `68010`, `68020`, `68030` die Seiten `Compiler -> BASIC`.
Auf jeder Seite befindet sich rechts die GroupBox `Dialekt` mit zwei exklusiven
RadioButtons:

- `BASIC V2` (Default)
- `Simon BASIC`

Der Dialog verwendet die vorhandene Projektsettings-Theme-Steuerung für Dark/Light.
`68010` wurde analog zu den existierenden C64-Einstellungsprofilen ergänzt.
Es wird damit kein neues Compilerziel und kein neuer Prozessor-Backend eingeführt.

## Projektdatei

Die Projekteinstellung ist profilspezifisch und wird pro Profil im INI-Abschnitt
`Settings.C64.<Profil>.Compiler.BASIC` gespeichert. Beispiel:

```ini
[Settings.C64.68000.Compiler.BASIC]
Title = C=64 68000 BASIC Dialekt
Dialect = basic_v2

[Settings.C64.68010.Compiler.BASIC]
Title = C=64 68010 BASIC Dialekt
Dialect = simon_basic
```

Beim Einlesen alter Projekte oder ungültiger Werte gilt `basic_v2` als Default.
Die GUI aktualisiert bei Wechsel die Projektkonfiguration; geänderte Werte
markieren das Projekt als verändert und werden analog zu bestehenden
Projekteinstellungen persistiert.

## Abgrenzung

Die Auswahl `Simon BASIC` ist zunächst nur eine gespeicherte Projekteinstellung.
Es wurden keine Simon-BASIC-Tokens, kein Simon-BASIC-Lexer/Parser, keine
Codegenerierung und keine besondere VICE-Runtime ergänzt.

## Prüfungen

- `python -m py_compile d64_dism.py`
- 5 Stage-400-Tests: Profile, Defaults, INI-Roundtrip, GUI-Verkabelung,
  Schreibverhalten bei Profiländerung.
- 16 bestehende Stage-394-/395-/399-Regressionstests erfolgreich.
- ZIP-Integrität und Unverändertheit der übrigen Projektdateien geprüft.

Ein interaktiver Qt5-Windows-Laufzeittest steht noch aus.
