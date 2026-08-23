start:
    jsr $E544       ; Bildschirm löschen

    lda #$01        ; Bildschirmcode für „A“
    sta $0400       ; linke obere Bildschirmposition

    lda #$01        ; Farbe Weiß
    sta $D800       ; Farbe der linken oberen Position

    rts             ; zurück zum BASIC