start:
    jsr $E544       ; Bildschirm löschen

    lda #$01        ; Bildschirmcode für "A"
    sta $0401       ; linke obere Bildschirmposition

    lda #$02        ; Farbe weis
    sta $D801       ; Farbe der linken oberen Position

    rts             ; zurück zum BASIC