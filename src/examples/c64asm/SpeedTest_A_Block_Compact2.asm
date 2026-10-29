; ---------------------------------------------------------------------
; Datei : SpeedTest_A_Block_Compact2.asm
; Author: (c) 2026 Jens Kallup - paule32
; alle rechte vorbehalten.
; ---------------------------------------------------------------------
; Speicherbedarf: 38 Bytes (mit Lade-Adresse)
; ---------------------------------------------------------------------
.org $1000
.nostub
.entry START

START:
    LDA #$00
    STA $FB
    LDA #$04
    STA $FC

    LDX #20

ZEILE:
    LDY #19
    LDA #$01

SPALTE:
    STA ($FB),Y
    DEY
    BPL SPALTE

    CLC
    LDA $FB
    ADC #40
    STA $FB
    BCC WEITER
    INC $FC

WEITER:
    DEX
    BNE ZEILE

    JMP $A474
