; ---------------------------------------------------------------------
; Datei : SpeedTest_A_Block_Compact.asm
; Author: (c) 2026 Jens Kallup - paule32
; alle rechte vorbehalten.
; ---------------------------------------------------------------------
; Erklärung
; Der C64-Bildschirm besitzt 40 Spalten und 25 Zeilen.
; Die Zeichen beginnen im normalen Bildschirmmodus bei Adresse $0400.
; ---------------------------------------------------------------------
; Programm-Datei vorher: 61 Bytes - SpeedTest_A_Block.asm
; Programm-Datei nacher: 50 Bytes - SpeedTest_A_Block_Compact.asm
; Ersparnis            : 19 %
;
; Zeichen              : 400
; Bildschirmbereich    : 20 x 20
;
; Der entscheidende Trick ist:
;   CLC
;   LDA $FB
;   ADC #40
;   STA $FB
;   STA $FD
;   BCC WEITER
;   INC $FC
;   INC $FE
;
; Da Bildschirm- und Farbspeicher dieselbe Byteanordnung besitzen,
; können wir ihre unteren Adressbytes gemeinsam aktualisieren.
; Auch der Übertrag in das obere Byte erfolgt bei beiden gleichzeitig.
;
; Mit LDY #19 und BPL SPALTE sparen wir außerdem einen zusätzlichen
; Vergleichsbefehl.
;
; Noch ein Hinweis:
; Wenn Dir die Zeichenfarbe egal ist, lässt sich das Programm weiter
; verkleinern, indem wir den Farbspeicher vollständig weglassen.
; Dann verwenden die Buchstaben die bereits im C64-Farbspeicher
; vorhandenen Farben.
; Dies erfolgt im Assembler-Programm: SpeedTest_A_Block_Compact2.asm
; ---------------------------------------------------------------------
.org $1000
.nostub
.entry START

START:
    LDA #0
    STA $FB
    STA $FD

    LDA #$04
    STA $FC
    LDA #$D8
    STA $FE

    LDX #20

ZEILE:
    LDY #19
    LDA #1

SPALTE:
    STA ($FB),Y
    STA ($FD),Y
    DEY
    BPL SPALTE

    CLC
    LDA $FB
    ADC #40
    STA $FB
    STA $FD
    BCC WEITER
    INC $FC
    INC $FE

WEITER:
    DEX
    BNE ZEILE

    JMP $A474
