; Von C64 Pascal erzeugter MOS-6510-Assembler
; Programm: HelloC64
.org $080D
.entry __pascal_start
.basic

__pascal_start:
    lda #$93
    jsr $FFD2
    lda #<__pas_string_0
    ldx #>__pas_string_0
    jsr __pas_print_string
    lda #$0D
    jsr $FFD2
    lda #$00
    ldx #$00
    sta __pas_var_i_0
    stx __pas_var_i_0+1
    lda #$19
    ldx #$00
    sta __pas_tmp__for_limit_0_1_1
    stx __pas_tmp__for_limit_0_1_1+1
__pas_for_condition_1:
    lda __pas_var_i_0
    ldx __pas_var_i_0+1
    pha
    txa
    pha
    lda __pas_tmp__for_limit_0_1_1
    ldx __pas_tmp__for_limit_0_1_1+1
    sta $FD
    stx $FE
    pla
    tax
    pla
    sta $FB
    stx $FC
    txa
    eor $FE
    bpl __pas_cmp_order_9
    lda $FC
    bmi __pas_cmp_less_7
    jmp __pas_cmp_greater_8
__pas_cmp_order_9:
    ldx $FC
    cpx $FE
    bcc __pas_cmp_less_7
    bne __pas_cmp_greater_8
    lda $FB
    cmp $FD
    bcc __pas_cmp_less_7
    bne __pas_cmp_greater_8
    jmp __pas_cmp_true_4
__pas_cmp_less_7:
    jmp __pas_cmp_true_4
__pas_cmp_greater_8:
    jmp __pas_cmp_false_5
__pas_cmp_false_5:
    lda #$00
    ldx #$00
    jmp __pas_cmp_end_6
__pas_cmp_true_4:
    lda #$01
    ldx #$00
__pas_cmp_end_6:
    sta $FB
    txa
    ora $FB
    bne __pas_condition_true_10
    jmp __pas_for_end_3
__pas_condition_true_10:
    lda #$00
    ldx #$04
    pha
    txa
    pha
    lda __pas_var_i_0
    ldx __pas_var_i_0+1
    sta $FD
    stx $FE
    pla
    tax
    pla
    clc
    adc $FD
    sta $FB
    txa
    adc $FE
    tax
    lda $FB
    pha
    txa
    pha
    lda #$01
    ldx #$00
    pha
    txa
    pha
    lda __pas_var_i_0
    ldx __pas_var_i_0+1
    sta $FD
    stx $FE
    pla
    tax
    pla
    clc
    adc $FD
    sta $FB
    txa
    adc $FE
    tax
    lda $FB
    sta $FD
    pla
    sta $FC
    pla
    sta $FB
    lda $FD
    ldy #$00
    sta ($FB),y
    lda #$00
    ldx #$D8
    pha
    txa
    pha
    lda __pas_var_i_0
    ldx __pas_var_i_0+1
    sta $FD
    stx $FE
    pla
    tax
    pla
    clc
    adc $FD
    sta $FB
    txa
    adc $FE
    tax
    lda $FB
    pha
    txa
    pha
    lda #$01
    ldx #$00
    sta $FD
    pla
    sta $FC
    pla
    sta $FB
    lda $FD
    ldy #$00
    sta ($FB),y
__pas_for_step_2:
    lda __pas_var_i_0
    clc
    adc #$01
    sta __pas_var_i_0
    lda __pas_var_i_0+1
    adc #$00
    sta __pas_var_i_0+1
    jmp __pas_for_condition_1
__pas_for_end_3:
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

; Pascal-Variablen
__pas_var_i_0: .word 0 ; I
__pas_tmp__for_limit_0_1_1: .word 0 ; intern

; Nullterminierte PETSCII-Zeichenketten
__pas_string_0: .byte $43, $36, $34, $20, $50, $41, $53, $43, $41, $4C, $00
