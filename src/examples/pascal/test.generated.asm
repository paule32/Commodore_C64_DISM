; Von C64 Pascal erzeugter MOS-6510-Assembler
; Programm: Unbenannt
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

; Compiler-Laufzeitdaten
__pas_rt_value:      .word 0
__pas_rt_remainder:  .word 0
__pas_rt_count:      .byte 0
__pas_rt_mode:       .byte 0

; Nullterminierte PETSCII-Zeichenketten
__pas_string_0: .byte $C8, $41, $4C, $4C, $4F, $00
