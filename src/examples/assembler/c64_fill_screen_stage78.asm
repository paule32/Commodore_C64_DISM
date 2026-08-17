; Stage 78 - C64 Textbildschirm mit einem Screen-Code fuellen.
; Bildschirm-RAM: $0400-$07E7 = exakt 1000 Bytes (40 x 25).
; A enthaelt jeweils den Screen-Code, nicht zwingend den PETSCII-Code.

.org $1000
.nostub

SCREEN      = $0400
FILLCHAR    = $02
PTRLO       = $FB
PTRHI       = $FC
LENLO       = $FD
LENHI       = $FE

; ---------------------------------------------------------------------------
; FillRange
;   A       = Screen-Code
;   PTRLO/HI= Startadresse
;   LENLO/HI= Anzahl Bytes
; ---------------------------------------------------------------------------
FillRange:
    STA FILLCHAR
    LDY #$00
FillRange_Loop:
    LDA LENLO
    ORA LENHI
    BEQ FillRange_Done
    LDA FILLCHAR
    STA (PTRLO),Y
    INC PTRLO
    BNE FillRange_NoCarry
    INC PTRHI
FillRange_NoCarry:
    DEC LENLO
    LDA LENLO
    CMP #$FF
    BNE FillRange_Loop
    DEC LENHI
    JMP FillRange_Loop
FillRange_Done:
    RTS

; ---------------------------------------------------------------------------
; FillLine
;   A = Screen-Code
;   X = Zeile 0..24
; ---------------------------------------------------------------------------
FillLine:
    STA FILLCHAR
    LDA ScreenLineLo,X
    STA PTRLO
    LDA ScreenLineHi,X
    STA PTRHI
    LDA #<40
    STA LENLO
    LDA #>40
    STA LENHI
    LDA FILLCHAR
    JSR FillRange
    RTS

; ---------------------------------------------------------------------------
; FillScreen
;   A = Screen-Code
;   Fuellt exakt $0400-$07E7. $07E8-$07FF bleiben unangetastet.
; ---------------------------------------------------------------------------
FillScreen:
    STA FILLCHAR
    LDA #<SCREEN
    STA PTRLO
    LDA #>SCREEN
    STA PTRHI
    LDA #<1000
    STA LENLO
    LDA #>1000
    STA LENHI
    LDA FILLCHAR
    JSR FillRange
    RTS

ScreenLineLo:
    .byte <(SCREEN+40*0), <(SCREEN+40*1), <(SCREEN+40*2), <(SCREEN+40*3), <(SCREEN+40*4)
    .byte <(SCREEN+40*5), <(SCREEN+40*6), <(SCREEN+40*7), <(SCREEN+40*8), <(SCREEN+40*9)
    .byte <(SCREEN+40*10), <(SCREEN+40*11), <(SCREEN+40*12), <(SCREEN+40*13), <(SCREEN+40*14)
    .byte <(SCREEN+40*15), <(SCREEN+40*16), <(SCREEN+40*17), <(SCREEN+40*18), <(SCREEN+40*19)
    .byte <(SCREEN+40*20), <(SCREEN+40*21), <(SCREEN+40*22), <(SCREEN+40*23), <(SCREEN+40*24)

ScreenLineHi:
    .byte >(SCREEN+40*0), >(SCREEN+40*1), >(SCREEN+40*2), >(SCREEN+40*3), >(SCREEN+40*4)
    .byte >(SCREEN+40*5), >(SCREEN+40*6), >(SCREEN+40*7), >(SCREEN+40*8), >(SCREEN+40*9)
    .byte >(SCREEN+40*10), >(SCREEN+40*11), >(SCREEN+40*12), >(SCREEN+40*13), >(SCREEN+40*14)
    .byte >(SCREEN+40*15), >(SCREEN+40*16), >(SCREEN+40*17), >(SCREEN+40*18), >(SCREEN+40*19)
    .byte >(SCREEN+40*20), >(SCREEN+40*21), >(SCREEN+40*22), >(SCREEN+40*23), >(SCREEN+40*24)
