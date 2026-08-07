# Kompakte Zielauswahl oberhalb des Editors

Die bisher sichtbaren Ziel-RadioButtons wurden durch eine kompakte ComboBox ersetzt.

Einträge:

- `C= 64`
- `Amiga`
- `Windows PE32`

Die Zielauswahl ist im Quelltext-Panel und im erzeugten ASM-Panel vorhanden und wird synchron gehalten.

## Sichtbarkeit der Zusatzfelder

### C= 64

Nur die Ziel-ComboBox ist sichtbar. CPU-, FPU- und Windows-Modus-Felder sind ausgeblendet.

### Amiga

Rechts neben der Ziel-ComboBox erscheinen:

1. Amiga-CPU (`mk68000` ... `mk68060`)
2. Amiga-FPU (`FPU: None`, `FPU: 68881`, `FPU: 68882`)

Die Windows-Modus-ComboBox ist ausgeblendet.

### Windows PE32

Rechts neben der Ziel-ComboBox erscheint die bestehende Windows-Modus-ComboBox mit:

- Console
- GUI
- Trennlinie
- Direct2D
- Direct3D

Amiga-CPU und Amiga-FPU sind ausgeblendet.

## BASIC

BASIC bleibt wie bisher auf C64 beschränkt. In der Ziel-ComboBox werden Amiga und Windows PE32 für BASIC-Dokumente deaktiviert.
