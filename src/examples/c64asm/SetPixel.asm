; -------------------------------------------------------------------
; File  : SetPixel.asm
; Author: (c) 2026 by Blacky Cat - paule32
;
; Desc  : Switch to the C64 320x200 HiRes Mode, set a yellow Pixel in
;         the screen center; endless loop at end.
; -------------------------------------------------------------------
.org $1000
.entry start

start:
    jsr $e544          ; Textbildschirm löschen

    ; Bitmap löschen ($2000-$3FFF)
    lda #$00
    sta $fb
    lda #$20
    sta $fc
    ldx #$20
    lda #$00           ; WICHTIG: Null schreiben !

clear_page:
    ldy #$00
clear_byte:
    sta ($fb),y
    iny
    bne clear_byte
    inc $fc
    dex
    bne clear_page

    lda $dd00          ; VIC-Bank 0
    ora #$03
    sta $dd00

    lda #$18           ; Screen $0400, Bitmap $2000
    sta $d018
    lda $d011
    ora #$20           ; Bitmap-Modus einschalten
    sta $d011
    lda $d016
    and #$ef           ; HiRes statt Multicolor
    sta $d016

    lda #$00
    sta $d020          ; Rahmen schwarz
    sta $d021          ; Hintergrund schwarz

    lda #$70           ; Gelb auf Schwarz
    sta $05f4          ; Farbattribut bei (160,100)

    lda #$80           ; Ein Pixel setzen
    sta $2fa4          ; Bitmap-Adresse (160,100)

ende:
    jmp ende
