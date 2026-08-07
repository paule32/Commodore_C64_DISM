; Von C64 Pascal erzeugter MOS-6510-Assembler
; Programm: UsesAndPreprocessor
.org $080D
.entry __pascal_start
.basic

__pascal_start:
    lda #$0E
    jsr $FFD2
    lda #<__pas_string_0
    ldx #>__pas_string_0
    jsr __pas_print_string
    lda #$0D
    jsr $FFD2
    lda #<__pas_string_1
    ldx #>__pas_string_1
    jsr __pas_print_string
    lda #$02
    ldx #$00
    jsr __pas_print_int16
    lda #$0D
    jsr $FFD2
    rts

; A/X = Adresse einer nullterminierten PETSCII-Zeichenkette
__pas_print_string:
    sta $FB
    stx $FC
__pas_print_string_loop:
    ldy #$00
    lda ($FB),y
    beq __pas_print_string_done
    jsr $FFD2
    inc $FB
    bne __pas_print_string_loop
    inc $FC
    jmp __pas_print_string_loop
__pas_print_string_done:
    rts

; unsigned 16-Bit DIV/MOD: $FB/$FC durch $FD/$FE
__pas_div16:
    lda #$00
    sta __pas_rt_mode
    jmp __pas_divmod16
__pas_mod16:
    lda #$01
    sta __pas_rt_mode
__pas_divmod16:
    lda $FD
    ora $FE
    bne __pas_divmod_nonzero
    lda #$00
    tax
    rts
__pas_divmod_nonzero:
    lda #$00
    sta __pas_rt_remainder
    sta __pas_rt_remainder+1
    ldx #$10
__pas_divmod_loop:
    asl $FB
    rol $FC
    rol __pas_rt_remainder
    rol __pas_rt_remainder+1
    lda __pas_rt_remainder+1
    cmp $FE
    bcc __pas_divmod_next
    bne __pas_divmod_subtract
    lda __pas_rt_remainder
    cmp $FD
    bcc __pas_divmod_next
__pas_divmod_subtract:
    sec
    lda __pas_rt_remainder
    sbc $FD
    sta __pas_rt_remainder
    lda __pas_rt_remainder+1
    sbc $FE
    sta __pas_rt_remainder+1
    inc $FB
__pas_divmod_next:
    dex
    bne __pas_divmod_loop
    lda __pas_rt_mode
    bne __pas_divmod_return_remainder
    lda $FB
    ldx $FC
    rts
__pas_divmod_return_remainder:
    lda __pas_rt_remainder
    ldx __pas_rt_remainder+1
    rts

; A/X = vorzeichenbehaftete 16-Bit-Zahl
__pas_print_int16:
    sta $FB
    stx $FC
    txa
    bpl __pas_print_int16_positive
    lda #$2D
    jsr $FFD2
    lda #$00
    sec
    sbc $FB
    sta __pas_rt_value
    lda #$00
    sbc $FC
    sta $FC
    lda __pas_rt_value
    sta $FB
__pas_print_int16_positive:
    lda $FB
    ora $FC
    bne __pas_print_int16_convert
    lda #$30
    jsr $FFD2
    rts
__pas_print_int16_convert:
    lda #$00
    sta __pas_rt_count
__pas_print_int16_divide:
    lda #$0A
    sta $FD
    lda #$00
    sta $FE
    jsr __pas_div16
    sta $FB
    stx $FC
    lda __pas_rt_remainder
    pha
    inc __pas_rt_count
    lda $FB
    ora $FC
    bne __pas_print_int16_divide
; Ziffern wurden auf dem Hardware-Stack abgelegt
__pas_print_int16_digits:
    pla
    clc
    adc #$30
    jsr $FFD2
    dec __pas_rt_count
    bne __pas_print_int16_digits
    rts

; Compiler-Laufzeitdaten
__pas_rt_value:      .word 0
__pas_rt_remainder:  .word 0
__pas_rt_count:      .byte 0
__pas_rt_mode:       .byte 0

; Nullterminierte PETSCII-Zeichenketten
__pas_string_0: .byte $D0, $D5, $C9, $20, $55, $4E, $44, $20, $CD, $41, $4B, $52, $4F, $53, $20, $41, $4B, $54, $49, $56, $00
__pas_string_1: .byte $D5, $4E, $49, $54, $2D, $D6, $45, $52, $53, $49, $4F, $4E, $20, $3D, $20, $00
