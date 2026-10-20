# Stage 395 – C64 BASIC und MOS6510-Assembler: VICE-Kontextmenüs

**Verbindliche Basis:** `d64_dism_asm_394.zip`.

## Editor-Kontextmenü

Im C64-BASIC- und im C64-Assembler-Quelltexteditor erscheint derselbe VICE-Befehlsblock vor dem Qt-Standardmenü. Der ehemals inaktive fette Menüpunkt **Ausführen** ist jetzt anklickbar.

| Menüeintrag | C64 BASIC | C64 Assembler |
|---|---|---|
| Ausführen | `NEW`, BASIC-Zeilen, `RUN` per Keyboard Feed | Kompilierte PRG-Nutzbytes in VICE-RAM, PC auf Entry, EXIT |
| Zeile in VICE ausführen | Aktuelle BASIC-Zeile im Keyboard Feed | Code des vollständigen Quelltexts laden; eine Maschineninstruktion an der Zeilenadresse ausführen (VICE Step) |
| Auswahl in VICE ausführen | Bestehende BASIC-Auswahl-/Programmbehandlung | Code des vollständigen Quelltexts laden; Anzahl der markierten MOS6510-Instruktionen schrittweise ausführen |
| Programm an VICE übertragen | `NEW` + nummerierte BASIC-Zeilen | PRG in C64-RAM laden, **ohne** den PC zu verändern |
| Programm übertragen + RUN / START | BASIC: `RUN` | ASM: Set PC + EXIT |
| VICE BASIC zurücksetzen / VICE Monitor fortsetzen | `NEW` | Monitor verlassen; CPU fortsetzen |

Editieren, Kopieren, Ausschneiden, Einfügen und der vorhandene Operand-Rechner bleiben erhalten. Das Kontextmenü wird beim Assembler nur für **C64** angeboten (kein Amiga-/Windows-Assembler).

## VICE-Protokoll

- Verwendet bestehenden VICE Binary Remote Monitor API v2 auf `127.0.0.1:6502`, vorhandenen oder bei Bedarf gestarteten VICE-Prozess.
- `MEMORY_SET` (0x02) lädt **Bytes** aus dem erzeugten `.prg`, aber nicht den 2-Byte-PRG-Header. In Bytes 0..1 steht die Load-Adresse (Little Endian).
- `REGISTERS_AVAILABLE` (0x83) löst die PC-Register-ID dynamisch auf; `REGISTERS_SET` (0x32) setzt den PC. Antworttyp für Registeränderung: 0x31.
- `EXIT` (0xAA) setzt die Maschine nach **Ausführen** fort.
- `ADVANCE_INSTRUCTIONS` (0x71) führt beim Debuggen eine bzw. mehrere Maschineninstruktionen aus und hält danach im Monitor an. Die Schritte folgen dem **tatsächlichen CPU-Kontrollfluss**, der bei Sprüngen vom ausgewählten Zeilenbereich abweichen kann.
- Programmtransfer/Assemblerarbeit sind vom GUI-Thread getrennt. Fehler werden über die bereits vorhandenen Qt-Signale und Fehlerdialoge berichtet. Die IDE-Editorregisterkarte bleibt beim Ausführen aktiv.

## Sicherheit/Fehler

- PRG-Header, leerer PRG-Inhalt, Adressraumüberlauf und ungültiger PC werden abgefangen.
- Fehlt ein aktueller Assembler-Build, wird vor dem Senden der bestehende interne Assembler ausgeführt (inklusive Speichern-unter bei neuen Dateien).
- Für Zeile/Auswahl wird das *vollständige* Assemblerprogramm ohne Image-Packer assembliert, damit Symbole und Adressen korrekt bleiben. Eine Quellzeile ohne CPU-Instruktion erzeugt eine Fehlermeldung.
- Der normale `F2`-Build und der bisherige Start-Button bleiben unverändert.

## Tests

`python -m unittest -v test_stage395_vice_context.py test_stage394_c64_new_rename.py test_stage393_hex_refresh.py`

Diese tests sind PyQt-unabhängig. Ein Ende-zu-Ende-Test mit einer tatsächlichen VICE-Instanz unter Windows ist noch erforderlich.
