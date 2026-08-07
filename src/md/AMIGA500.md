# Amiga-500-Ziel

Die RadioButton-Gruppe neben `Compile`/`Start` wählt das Ziel des aktuellen
Dokuments:

- `C-64`: MOS 6510, PETSCII/KERNAL-Laufzeit, PRG-Ausgabe und VICE
- `Amiga`: Motorola 68000, direkte OCS-Bildschirmlaufzeit, ADF-Ausgabe und
  WinUAE

Die beiden Zielsysteme besitzen getrennte Laufzeiten. Im C-64-Assembler wird
kein Amiga-Code eingebettet; im Amiga-Assembler befinden sich weder
MOS-6510-Befehle noch KERNAL-Aufrufe.

## Pascal und C nach Amiga-Assembler

Ein Pascal- oder C-Dokument mit Ziel `Amiga` erzeugt:

```text
programm.generated.amiga.asm
programm.adf
```

Der ASM-Tab zeigt den vollständigen Motorola-68000-Code einschließlich der
Amiga-Bildschirmlaufzeit und des 8x8-Bitmapfonts. Der Code arbeitet direkt mit
den Custom-Chip-Registern ab `$DFF000` und benötigt weder Workbench noch
`dos.library` oder `graphics.library`.

Pascal:

```pascal
program BitmapTextPascal;

begin
    SetTextColor($0F0, $000);
    WriteLn('Amiga 500 Bitmap-Text');
    WriteLn('Counter = ', 5);
end.
```

C:

```c
#include <stdio.h>
#include <amiga.h>

int main(void)
{
    amiga_set_text_color(AMIGA_GREEN, AMIGA_BLACK);
    printf("Amiga 500 Bitmap-Text\n");
    printf("Counter = %d\n", 5);
    return 0;
}
```

`SetTextColor` beziehungsweise `amiga_set_text_color` erwartet zwei
12-Bit-OCS-Farbwerte im Format `$RGB`/`0xRGB`. Bei der verwendeten einzelnen
Bitplane sind `COLOR01` und `COLOR00` globale Vorder- und Hintergrundfarbe;
eine Änderung färbt daher auch bereits gezeichneten Text um.

`ClrScr()` und `clrscr()` löschen die 320x200-Bitplane und setzen den
40x32-Zeichen-Cursor zurück. Nicht darstellbare Zeichen werden als `?`
ausgegeben. Die Fontdaten umfassen ASCII `$20..$7F` mit acht Bytes pro Glyphe.

## Standalone-ADF und Trackloader

Die Direktive `.bootable` kennzeichnet ein eigenständig bootfähiges Programm.
Der Bootblock lädt den Nutzcode über das beim Booten übergebene
`trackdisk.device`-I/O-Request aus den folgenden ADF-Sektoren nach `$00040000`
und springt dorthin. Die Text-Bitplane liegt bei `$00018000`, der Stack bei
`$0007FFFC`.

Damit ist der Nutzcode nicht mehr auf die 1012 freien Bootblock-Bytes begrenzt.
Der aktuelle Sicherheitsgrenzwert beträgt 258048 Bytes und hält Abstand zum
Stack. Das ADF besitzt die normale Größe von 901120 Bytes und eine gültige
Bootblock-Prüfsumme.

## WinUAE

Der Pfad zu `winuae64.exe` oder `winuae.exe` wird über `DISM > WinUAE`
gewählt. `Start` legt das erzeugte ADF direkt in DF0 ein. Eine passende
A500-Kickstart-ROM ist erforderlich; eine Workbench-Diskette, ein `DH0:` und
eine `startup-sequence` sind nicht erforderlich.

Das weiterhin enthaltene Beispiel `examples/amiga/blitter_green.m68k` zeigt
zusätzlich direkten Zugriff auf `COLOR00`, `DMACON`, `BLTCON0`, `BLTDPT` und
`BLTSIZE`.

## Copper-Korrektur gegen horizontale Streifen

Die Bitplane-Zeiger werden nun durch eine Copper-Liste bei `$00010000` in jedem Frame erneut geladen. Details stehen in `AMIGA_COPPER_ZEBRA_FIX.md`.
