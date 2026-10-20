# Stage 437: Hilfe -> Über / Über Qt5

## Verbindliche Basis
`d64_dism_asm_436.zip`

## Umsetzung
- Beide Hilfe-Menüpunkte öffnen nun den gemeinsamen, modalen `D64AboutDialog`.
- Eigener frameless Qt5-Dialog mit einem 3 Pixel breiten umlaufenden Rahmen.
- Im Dark-Mode verläuft die mit QPainter gezeichnete Titelleiste von Schwarz (`#000000`) nach Grau (`#707070`).
- Ein oben rechts gezeichnetes X schließt den Dialog; die Titelzeile lässt sich ziehen. Zusätzlich gibt es eine `OK`-Schaltfläche.
- Im Light-Mode werden helle Hintergründe, eine helle Titelleiste und gut lesbare dunkle Schriften verwendet.
- **Über ...** zeigt genau:

  Gelb:
  ```text
  C= 64  Disassembler
  Version 0.0.1
  (c) 2026 bei Jens Kallup - paule32
  Alle Rechte vorbehalten.
  ```
  Weiß:
  ```text
  Lizenziert durch die MIT Lizenz
  ```
  Die Platzhalter `<gelbe Schriftfarbe>` und `<weiße Schriftfarbe>` werden nicht als Text ausgegeben.
- **Über Qt5 ...** zeigt die aktuellen Qt-/PyQt-Versionsnummern über `qVersion()` beziehungsweise `PYQT_VERSION_STR` sowie einen Hinweis auf Qt; die Standard-Qt-Meldungsbox wurde zugunsten der einheitlichen Gestaltung ersetzt.

## Dateien
- `d64_dism.py` – Import und beide Dialogaktionen
- `d64_about_dialog.py` – neue Widget- und Titelbarklassen
- `test_stage437_about_dialog_theme.py` – Tests der Texte, Menüs, Farben und Fensterbuttons

## Prüfungen
- Python-Syntax per `py_compile` und Stage-437-Strukturtests
- Windows-/PyQt5-Sichttest muss in der Zielumgebung noch durchgeführt werden.
