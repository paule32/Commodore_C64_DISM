; ---------------------------------------------------------------------
; Datei : SpeedTest_A_Block.asm
; Author: (c) 2026 Jens Kallup - paule32
; alle rechte vorbehalten.
; ---------------------------------------------------------------------
; Erklärung
; Der C64-Bildschirm besitzt 40 Spalten und 25 Zeilen.
; Die Zeichen beginnen im normalen Bildschirmmodus bei Adresse $0400.
; ---------------------------------------------------------------------
; Programm-Datei vorher: 61 Bytes - SpeedTest_A_Block.asm
; Programm-Datei nacher: 50 Bytes - SpeedTest_A_Block_Compact.asm
; ---------------------------------------------------------------------
.org $1000
.nostub
.entry START

START:
    ; Bildschirmadresse $0400
    LDA #$00
    STA $FB
    LDA #$04
    STA $FC

    ; Farbspeicher $D800
    LDA #$00
    STA $FD
    LDA #$D8
    STA $FE

    ; 20 Zeilen
    LDX #20

ZEILE:
    LDY #0

SPALTE:
    LDA #$01
    STA ($FB),Y
    STA ($FD),Y

    INY
    CPY #20
    BNE SPALTE

    ; Naechste Bildschirmzeile: +40
    CLC
    LDA $FB
    ADC #40
    STA $FB
    BCC SCREEN_OK
    INC $FC

SCREEN_OK:
    ; Naechste Farbzeile: +40
    CLC
    LDA $FD
    ADC #40
    STA $FD
    BCC COLOR_OK
    INC $FE

COLOR_OK:
    DEX
    BNE ZEILE

    ; Zurueck zum C64-BASIC
    JMP $A474

;    rts
