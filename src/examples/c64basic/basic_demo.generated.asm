; ---------------------------------------------------------------------------
; C64 BASIC Compiler output: /mnt/data/d64_dism_c64_basic_project_fix/d64_dism_editor_compile_pipeline_fix/examples/c64basic/basic_demo.bas
; 16-Bit-Integer-Compiler, Ziel: MOS 6510 / C64
; ---------------------------------------------------------------------------
.org $080D
.entry __basic_start

__basic_start:
__basic_line_10:
__basic_line_20:
    lda #<__basic_string_1
    ldy #>__basic_string_1
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_30:
    lda #$02
    ldx #$00
    sta __basic_expr_tmp_1
    stx __basic_expr_tmp_1+1
    lda #$03
    ldx #$00
    sta __basic_expr_tmp_2
    stx __basic_expr_tmp_2+1
    lda #$04
    ldx #$00
    sta __basic_right
    stx __basic_right+1
    lda __basic_expr_tmp_2
    ldx __basic_expr_tmp_2+1
    sta __basic_left
    stx __basic_left+1
    jsr __basic_mul
    sta __basic_right
    stx __basic_right+1
    lda __basic_expr_tmp_1
    ldx __basic_expr_tmp_1+1
    sta __basic_left
    stx __basic_left+1
    jsr __basic_add
    sta __basic_var_A
    stx __basic_var_A+1
__basic_line_40:
    lda #<__basic_string_2
    ldy #>__basic_string_2
    jsr __basic_print_string
    lda __basic_var_A
    ldx __basic_var_A+1
    jsr __basic_print_int
    jsr __basic_newline
__basic_line_50:
    lda #$01
    ldx #$00
    sta __basic_var_I
    stx __basic_var_I+1
    lda #$05
    ldx #$00
    sta __basic_expr_tmp_3
    stx __basic_expr_tmp_3+1
    lda #$01
    ldx #$00
    sta __basic_expr_tmp_4
    stx __basic_expr_tmp_4+1
__basic_for_loop_3:
__basic_line_60:
    lda __basic_var_I
    ldx __basic_var_I+1
    jsr __basic_print_int
__basic_line_70:
    lda __basic_var_I
    ldx __basic_var_I+1
    sta __basic_left
    stx __basic_left+1
    lda __basic_expr_tmp_4
    ldx __basic_expr_tmp_4+1
    sta __basic_right
    stx __basic_right+1
    jsr __basic_add
    sta __basic_var_I
    stx __basic_var_I+1
    sta __basic_left
    stx __basic_left+1
    lda __basic_expr_tmp_3
    ldx __basic_expr_tmp_3+1
    sta __basic_right
    stx __basic_right+1
    lda __basic_expr_tmp_4
    ldx __basic_expr_tmp_4+1
    txa
    bpl __basic_for_positive_4
    jsr __basic_cmp_ge
    jmp __basic_for_done_5
__basic_for_positive_4:
    jsr __basic_cmp_le
__basic_for_done_5:
    cmp #$00
    bne __basic_for_loop_3
__basic_line_80:
    jsr __basic_newline
__basic_line_90:
    lda __basic_var_A
    ldx __basic_var_A+1
    sta __basic_expr_tmp_5
    stx __basic_expr_tmp_5+1
    lda #$0E
    ldx #$00
    sta __basic_right
    stx __basic_right+1
    lda __basic_expr_tmp_5
    ldx __basic_expr_tmp_5+1
    sta __basic_left
    stx __basic_left+1
    jsr __basic_cmp_eq
    cpx #$00
    bne __basic_if_true_high_7
    cmp #$00
    beq __basic_if_skip_6
__basic_if_true_high_7:
    jmp __basic_line_120
__basic_if_skip_6:
__basic_line_100:
    lda #<__basic_string_8
    ldy #>__basic_string_8
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_110:
    jmp __basic_line_130
__basic_line_120:
    lda #$20
    ldx #$D0
    sta $FB
    stx $FC
    lda #$06
    ldx #$00
    ldy #$00
    sta ($FB),y
__basic_line_130:
    rts
__basic_program_end:
    rts

; ---- C64 BASIC Integer-Runtime ------------------------------------
__basic_newline:
    lda #$0D
    jmp $FFD2

__basic_print_string:
    sta $FB
    sty $FC
    ldy #$00
__basic_print_string_9:
    lda ($FB),y
    beq __basic_print_string_done_10
    jsr $FFD2
    iny
    bne __basic_print_string_9
__basic_print_string_done_10:
    rts

__basic_print_int:
    sta __basic_print_value
    stx __basic_print_value+1
    txa
    bpl __basic_print_positive_11
    lda #$2D
    jsr $FFD2
    lda __basic_print_value
    eor #$FF
    clc
    adc #$01
    sta __basic_print_value
    lda __basic_print_value+1
    eor #$FF
    adc #$00
    sta __basic_print_value+1
__basic_print_positive_11:
    lda #$00
    sta __basic_print_started
    ldy #$00
__basic_print_digit_4_12:
    lda __basic_print_value+1
    cmp #$27
    bcc __basic_print_emit_4_13
    bne __basic_print_greater_4_15
    lda __basic_print_value
    cmp #$10
    bcc __basic_print_emit_4_13
__basic_print_greater_4_15:
    sec
    lda __basic_print_value
    sbc #$10
    sta __basic_print_value
    lda __basic_print_value+1
    sbc #$27
    sta __basic_print_value+1
    iny
    jmp __basic_print_digit_4_12
__basic_print_emit_4_13:
    tya
    bne __basic_print_skip_4_14
    lda __basic_print_started
    beq __basic_print_skip_4_14_done
__basic_print_skip_4_14:
    tya
    ora #$30
    jsr $FFD2
    lda #$01
    sta __basic_print_started
__basic_print_skip_4_14_done:
    ldy #$00
__basic_print_digit_3_16:
    lda __basic_print_value+1
    cmp #$03
    bcc __basic_print_emit_3_17
    bne __basic_print_greater_3_19
    lda __basic_print_value
    cmp #$E8
    bcc __basic_print_emit_3_17
__basic_print_greater_3_19:
    sec
    lda __basic_print_value
    sbc #$E8
    sta __basic_print_value
    lda __basic_print_value+1
    sbc #$03
    sta __basic_print_value+1
    iny
    jmp __basic_print_digit_3_16
__basic_print_emit_3_17:
    tya
    bne __basic_print_skip_3_18
    lda __basic_print_started
    beq __basic_print_skip_3_18_done
__basic_print_skip_3_18:
    tya
    ora #$30
    jsr $FFD2
    lda #$01
    sta __basic_print_started
__basic_print_skip_3_18_done:
    ldy #$00
__basic_print_digit_2_20:
    lda __basic_print_value+1
    cmp #$00
    bne __basic_print_emit_2_21
    lda __basic_print_value
    cmp #$64
    bcc __basic_print_emit_2_21
    sec
    lda __basic_print_value
    sbc #$64
    sta __basic_print_value
    lda __basic_print_value+1
    sbc #$00
    sta __basic_print_value+1
    iny
    jmp __basic_print_digit_2_20
__basic_print_emit_2_21:
    tya
    bne __basic_print_skip_2_22
    lda __basic_print_started
    beq __basic_print_skip_2_22_done
__basic_print_skip_2_22:
    tya
    ora #$30
    jsr $FFD2
    lda #$01
    sta __basic_print_started
__basic_print_skip_2_22_done:
    ldy #$00
__basic_print_digit_1_23:
    lda __basic_print_value+1
    cmp #$00
    bne __basic_print_emit_1_24
    lda __basic_print_value
    cmp #$0A
    bcc __basic_print_emit_1_24
    sec
    lda __basic_print_value
    sbc #$0A
    sta __basic_print_value
    lda __basic_print_value+1
    sbc #$00
    sta __basic_print_value+1
    iny
    jmp __basic_print_digit_1_23
__basic_print_emit_1_24:
    tya
    bne __basic_print_skip_1_25
    lda __basic_print_started
    beq __basic_print_skip_1_25_done
__basic_print_skip_1_25:
    tya
    ora #$30
    jsr $FFD2
    lda #$01
    sta __basic_print_started
__basic_print_skip_1_25_done:
    lda __basic_print_value
    ora #$30
    jmp $FFD2

__basic_add:
    clc
    lda __basic_left
    adc __basic_right
    pha
    lda __basic_left+1
    adc __basic_right+1
    tax
    pla
    rts
__basic_sub:
    sec
    lda __basic_left
    sbc __basic_right
    pha
    lda __basic_left+1
    sbc __basic_right+1
    tax
    pla
    rts
__basic_and:
    lda __basic_left
    and __basic_right
    pha
    lda __basic_left+1
    and __basic_right+1
    tax
    pla
    rts
__basic_or:
    lda __basic_left
    ora __basic_right
    pha
    lda __basic_left+1
    ora __basic_right+1
    tax
    pla
    rts

__basic_mul:
    lda #$00
    sta __basic_result
    sta __basic_result+1
    ldy #$10
__basic_mul_loop_26:
    lsr __basic_right+1
    ror __basic_right
    bcc __basic_mul_skip_27
    clc
    lda __basic_result
    adc __basic_left
    sta __basic_result
    lda __basic_result+1
    adc __basic_left+1
    sta __basic_result+1
__basic_mul_skip_27:
    asl __basic_left
    rol __basic_left+1
    dey
    bne __basic_mul_loop_26
    lda __basic_result
    ldx __basic_result+1
    rts

__basic_div:
    jsr __basic_divmod
    lda __basic_result
    ldx __basic_result+1
    rts
__basic_mod:
    jsr __basic_divmod
    lda __basic_left
    ldx __basic_left+1
    rts
__basic_divmod:
    lda __basic_right
    ora __basic_right+1
    bne __basic_divisor_ok_28
    lda #$00
    tax
    sta __basic_result
    sta __basic_result+1
    rts
__basic_divisor_ok_28:
    lda #$00
    sta __basic_result
    sta __basic_result+1
__basic_div_loop_29:
    jsr __basic_cmp_left_right_unsigned
    cmp #$00
    beq __basic_div_done_30
    sec
    lda __basic_left
    sbc __basic_right
    sta __basic_left
    lda __basic_left+1
    sbc __basic_right+1
    sta __basic_left+1
    inc __basic_result
    bne __basic_div_no_carry_31
    inc __basic_result+1
__basic_div_no_carry_31:
    jmp __basic_div_loop_29
__basic_div_done_30:
    rts

__basic_cmp_left_right_unsigned:
    lda __basic_left+1
    cmp __basic_right+1
    bcc __basic_cmp_u_false_32
    bne __basic_cmp_u_true_33
    lda __basic_left
    cmp __basic_right
    bcc __basic_cmp_u_false_32
__basic_cmp_u_true_33:
    lda #$01
    rts
__basic_cmp_u_false_32:
    lda #$00
    rts

__basic_cmp_prepare:
    lda __basic_left+1
    eor #$80
    sta __basic_cmp_left_high
    lda __basic_right+1
    eor #$80
    sta __basic_cmp_right_high
    rts
__basic_cmp_eq:
    lda __basic_left+1
    cmp __basic_right+1
    bne __basic___basic_cmp_eq_false_34
    lda __basic_left
    cmp __basic_right
    beq __basic___basic_cmp_eq_true_35
    jmp __basic___basic_cmp_eq_false_34
__basic___basic_cmp_eq_true_35:
    lda #$01
    jmp __basic___basic_cmp_eq_done_36
__basic___basic_cmp_eq_false_34:
    lda #$00
__basic___basic_cmp_eq_done_36:
    ldx #$00
    rts
__basic_cmp_ne:
    lda __basic_left+1
    cmp __basic_right+1
    bne __basic___basic_cmp_ne_true_38
    lda __basic_left
    cmp __basic_right
    bne __basic___basic_cmp_ne_true_38
    jmp __basic___basic_cmp_ne_false_37
__basic___basic_cmp_ne_true_38:
    lda #$01
    jmp __basic___basic_cmp_ne_done_39
__basic___basic_cmp_ne_false_37:
    lda #$00
__basic___basic_cmp_ne_done_39:
    ldx #$00
    rts
__basic_cmp_lt:
    jsr __basic_cmp_prepare
    lda __basic_cmp_left_high
    cmp __basic_cmp_right_high
    bcc __basic___basic_cmp_lt_true_41
    bne __basic___basic_cmp_lt_false_40
    lda __basic_left
    cmp __basic_right
    bcc __basic___basic_cmp_lt_true_41
    jmp __basic___basic_cmp_lt_false_40
__basic___basic_cmp_lt_true_41:
    lda #$01
    jmp __basic___basic_cmp_lt_done_42
__basic___basic_cmp_lt_false_40:
    lda #$00
__basic___basic_cmp_lt_done_42:
    ldx #$00
    rts
__basic_cmp_le:
    jsr __basic_cmp_prepare
    lda __basic_cmp_left_high
    cmp __basic_cmp_right_high
    bcc __basic___basic_cmp_le_true_44
    bne __basic___basic_cmp_le_false_43
    lda __basic_left
    cmp __basic_right
    bcc __basic___basic_cmp_le_true_44
    beq __basic___basic_cmp_le_true_44
    jmp __basic___basic_cmp_le_false_43
__basic___basic_cmp_le_true_44:
    lda #$01
    jmp __basic___basic_cmp_le_done_45
__basic___basic_cmp_le_false_43:
    lda #$00
__basic___basic_cmp_le_done_45:
    ldx #$00
    rts
__basic_cmp_gt:
    jsr __basic_cmp_prepare
    lda __basic_cmp_left_high
    cmp __basic_cmp_right_high
    bcc __basic___basic_cmp_gt_false_46
    bne __basic___basic_cmp_gt_true_47
    lda __basic_left
    cmp __basic_right
    bcc __basic___basic_cmp_gt_false_46
    beq __basic___basic_cmp_gt_false_46
    jmp __basic___basic_cmp_gt_true_47
__basic___basic_cmp_gt_true_47:
    lda #$01
    jmp __basic___basic_cmp_gt_done_48
__basic___basic_cmp_gt_false_46:
    lda #$00
__basic___basic_cmp_gt_done_48:
    ldx #$00
    rts
__basic_cmp_ge:
    jsr __basic_cmp_prepare
    lda __basic_cmp_left_high
    cmp __basic_cmp_right_high
    bcc __basic___basic_cmp_ge_false_49
    bne __basic___basic_cmp_ge_true_50
    lda __basic_left
    cmp __basic_right
    bcc __basic___basic_cmp_ge_false_49
    jmp __basic___basic_cmp_ge_true_50
__basic___basic_cmp_ge_true_50:
    lda #$01
    jmp __basic___basic_cmp_ge_done_51
__basic___basic_cmp_ge_false_49:
    lda #$00
__basic___basic_cmp_ge_done_51:
    ldx #$00
    rts

; ---- Variablen und Compiler-Temporärspeicher -----------------------
__basic_var_A: .word $0000
__basic_var_I: .word $0000
__basic_expr_tmp_1: .word $0000
__basic_expr_tmp_2: .word $0000
__basic_expr_tmp_3: .word $0000
__basic_expr_tmp_4: .word $0000
__basic_expr_tmp_5: .word $0000
__basic_left: .word $0000
__basic_right: .word $0000
__basic_result: .word $0000
__basic_print_value: .word $0000
__basic_print_started: .byte $00
__basic_cmp_left_high: .byte $00
__basic_cmp_right_high: .byte $00

; ---- Zeichenketten --------------------------------------------------
__basic_string_1: .byte $43, $36, $34, $20, $42, $41, $53, $49, $43, $20, $43, $4F, $4D, $50, $49, $4C, $45, $52, $00
__basic_string_2: .byte $41, $3D, $00
__basic_string_8: .byte $46, $45, $48, $4C, $45, $52, $00
end
