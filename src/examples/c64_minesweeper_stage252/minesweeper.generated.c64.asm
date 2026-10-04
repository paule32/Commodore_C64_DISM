; ---------------------------------------------------------------------------
; C64 BASIC Compiler output: /mnt/data/d64_stage255_work/examples/c64_minesweeper_stage252/minesweeper.bas
; CBM-5-Byte-Fließkomma, Strings, Arrays, DATA/INPUT und KERNAL-I/O
; Ziel: MOS 6510 / Commodore 64
; ---------------------------------------------------------------------------
.org $080D
.entry __basic_start

__basic_start:
    jsr __basic_init_cbss
    tsx
    stx __basic_entry_sp
    lda #<__basic_data_start
    sta __basic_data_ptr
    lda #>__basic_data_start
    sta __basic_data_ptr+1
__basic_line_10:
__basic_line_20:
    lda #<__basic_float_const_3
    ldy #>__basic_float_const_3
    jsr $BBA2
    jsr __basic_fac_to_int
    sta $FB
    stx $FC
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    lda #<__basic_float_const_4
    ldy #>__basic_float_const_4
    jsr $BBA2
    jsr __basic_fac_to_int
    sta $FB
    stx $FC
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    lda #<__basic_float_const_5
    ldy #>__basic_float_const_5
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_string_term+1
    lda #$01
    sta __basic_string_term
    lda #<__basic_string_term
    ldy #>__basic_string_term
    jsr __basic_print_string
__basic_line_30:
    lda #<__basic_string_1
    ldy #>__basic_string_1
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_40:
    lda #<__basic_string_2
    ldy #>__basic_string_2
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_50:
    lda #<__basic_string_3
    ldy #>__basic_string_3
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_60:
    lda #<__basic_string_4
    ldy #>__basic_string_4
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_70:
    lda #<__basic_string_5
    ldy #>__basic_string_5
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_80:
    lda #<__basic_string_6
    ldy #>__basic_string_6
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_90:
    lda #<__basic_string_7
    ldy #>__basic_string_7
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_100:
    jsr $FFE4
    sta __basic_get_char
    lda __basic_get_char
    beq __basic_get_empty_8
    sta __basic_string_term+1
    lda #$01
    sta __basic_string_term
    jmp __basic_get_done_9
__basic_get_empty_8:
    lda #$00
    sta __basic_string_term
__basic_get_done_9:
    lda #<__basic_str_K_
    sta $FB
    lda #>__basic_str_K_
    sta $FC
    lda #<__basic_string_term
    sta $FD
    lda #>__basic_string_term
    sta $FE
    jsr __basic_string_copy
    lda #<__basic_string_left
    sta $FB
    lda #>__basic_string_left
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_str_K_
    sta $FD
    lda #>__basic_str_K_
    sta $FE
    lda #<__basic_string_left
    sta $FB
    lda #>__basic_string_left
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_right
    sta $FB
    lda #>__basic_string_right
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_12
    sta $FD
    lda #>__basic_string_12
    sta $FE
    lda #<__basic_string_right
    sta $FB
    lda #>__basic_string_right
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_left
    sta $FB
    lda #>__basic_string_left
    sta $FC
    lda #<__basic_string_right
    sta $FD
    lda #>__basic_string_right
    sta $FE
    jsr __basic_string_compare
    beq __basic_str_cmp_true_13
    lda #$00
    jmp __basic_str_cmp_done_14
__basic_str_cmp_true_13:
    lda #$01
__basic_str_cmp_done_14:
    cmp #$00
    bne __basic_if_then_10
    jmp __basic_if_skip_11
__basic_if_then_10:
    jmp __basic_line_100
__basic_if_skip_11:
__basic_line_105:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_str_K_
    sta $FD
    lda #>__basic_str_K_
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda __basic_string_expr
    beq __basic_asc_empty_15
    lda __basic_string_expr+1
    ldx #$00
    jmp __basic_asc_done_16
__basic_asc_empty_15:
    lda #$00
    tax
__basic_asc_done_16:
    jsr __basic_int_to_fac
    ldx #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBD4
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_2
    ldy #>__basic_float_tmp_2
    jsr $BBD4
    lda #<__basic_float_const_6
    ldy #>__basic_float_const_6
    jsr $BBA2
    lda #<__basic_float_tmp_2
    ldy #>__basic_float_tmp_2
    jsr __basic_cmp_lt
    ldx #<__basic_float_tmp_1
    ldy #>__basic_float_tmp_1
    jsr $BBD4
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_3
    ldy #>__basic_float_tmp_3
    jsr $BBD4
    lda #<__basic_float_const_7
    ldy #>__basic_float_const_7
    jsr $BBA2
    lda #<__basic_float_tmp_3
    ldy #>__basic_float_tmp_3
    jsr __basic_cmp_gt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_1
    ldy #>__basic_float_tmp_1
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_or
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_17
    jmp __basic_if_skip_18
__basic_if_then_17:
    jmp __basic_line_100
__basic_if_skip_18:
__basic_line_110:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_4
    ldy #>__basic_float_tmp_4
    jsr $BBD4
    lda #<__basic_float_const_6
    ldy #>__basic_float_const_6
    jsr $BBA2
    lda #<__basic_float_tmp_4
    ldy #>__basic_float_tmp_4
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_19
    jmp __basic_if_skip_20
__basic_if_then_19:
    lda #<__basic_float_const_8
    ldy #>__basic_float_const_8
    jsr $BBA2
    ldx #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBD4
__basic_if_skip_20:
__basic_line_120:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_5
    ldy #>__basic_float_tmp_5
    jsr $BBD4
    lda #<__basic_float_const_6
    ldy #>__basic_float_const_6
    jsr $BBA2
    lda #<__basic_float_tmp_5
    ldy #>__basic_float_tmp_5
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_21
    jmp __basic_if_skip_22
__basic_if_then_21:
    lda #<__basic_float_const_9
    ldy #>__basic_float_const_9
    jsr $BBA2
    ldx #<__basic_var_MC
    ldy #>__basic_var_MC
    jsr $BBD4
__basic_if_skip_22:
__basic_line_130:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_6
    ldy #>__basic_float_tmp_6
    jsr $BBD4
    lda #<__basic_float_const_6
    ldy #>__basic_float_const_6
    jsr $BBA2
    lda #<__basic_float_tmp_6
    ldy #>__basic_float_tmp_6
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_23
    jmp __basic_if_skip_24
__basic_if_then_23:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_var_SF
    ldy #>__basic_var_SF
    jsr $BBD4
__basic_if_skip_24:
__basic_line_140:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_7
    ldy #>__basic_float_tmp_7
    jsr $BBD4
    lda #<__basic_float_const_10
    ldy #>__basic_float_const_10
    jsr $BBA2
    lda #<__basic_float_tmp_7
    ldy #>__basic_float_tmp_7
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_25
    jmp __basic_if_skip_26
__basic_if_then_25:
    lda #<__basic_float_const_11
    ldy #>__basic_float_const_11
    jsr $BBA2
    ldx #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBD4
__basic_if_skip_26:
__basic_line_150:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_8
    ldy #>__basic_float_tmp_8
    jsr $BBD4
    lda #<__basic_float_const_10
    ldy #>__basic_float_const_10
    jsr $BBA2
    lda #<__basic_float_tmp_8
    ldy #>__basic_float_tmp_8
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_27
    jmp __basic_if_skip_28
__basic_if_then_27:
    lda #<__basic_float_const_12
    ldy #>__basic_float_const_12
    jsr $BBA2
    ldx #<__basic_var_MC
    ldy #>__basic_var_MC
    jsr $BBD4
__basic_if_skip_28:
__basic_line_160:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_9
    ldy #>__basic_float_tmp_9
    jsr $BBD4
    lda #<__basic_float_const_10
    ldy #>__basic_float_const_10
    jsr $BBA2
    lda #<__basic_float_tmp_9
    ldy #>__basic_float_tmp_9
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_29
    jmp __basic_if_skip_30
__basic_if_then_29:
    lda #<__basic_float_const_13
    ldy #>__basic_float_const_13
    jsr $BBA2
    ldx #<__basic_var_SF
    ldy #>__basic_var_SF
    jsr $BBD4
__basic_if_skip_30:
__basic_line_170:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_10
    ldy #>__basic_float_tmp_10
    jsr $BBD4
    lda #<__basic_float_const_14
    ldy #>__basic_float_const_14
    jsr $BBA2
    lda #<__basic_float_tmp_10
    ldy #>__basic_float_tmp_10
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_31
    jmp __basic_if_skip_32
__basic_if_then_31:
    lda #<__basic_float_const_15
    ldy #>__basic_float_const_15
    jsr $BBA2
    ldx #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBD4
__basic_if_skip_32:
__basic_line_180:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_11
    ldy #>__basic_float_tmp_11
    jsr $BBD4
    lda #<__basic_float_const_14
    ldy #>__basic_float_const_14
    jsr $BBA2
    lda #<__basic_float_tmp_11
    ldy #>__basic_float_tmp_11
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_33
    jmp __basic_if_skip_34
__basic_if_then_33:
    lda #<__basic_float_const_16
    ldy #>__basic_float_const_16
    jsr $BBA2
    ldx #<__basic_var_MC
    ldy #>__basic_var_MC
    jsr $BBD4
__basic_if_skip_34:
__basic_line_190:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_12
    ldy #>__basic_float_tmp_12
    jsr $BBD4
    lda #<__basic_float_const_14
    ldy #>__basic_float_const_14
    jsr $BBA2
    lda #<__basic_float_tmp_12
    ldy #>__basic_float_tmp_12
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_35
    jmp __basic_if_skip_36
__basic_if_then_35:
    lda #<__basic_float_const_17
    ldy #>__basic_float_const_17
    jsr $BBA2
    ldx #<__basic_var_SF
    ldy #>__basic_var_SF
    jsr $BBD4
__basic_if_skip_36:
__basic_line_200:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_13
    ldy #>__basic_float_tmp_13
    jsr $BBD4
    lda #<__basic_float_const_18
    ldy #>__basic_float_const_18
    jsr $BBA2
    lda #<__basic_float_tmp_13
    ldy #>__basic_float_tmp_13
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_37
    jmp __basic_if_skip_38
__basic_if_then_37:
    lda #<__basic_float_const_12
    ldy #>__basic_float_const_12
    jsr $BBA2
    ldx #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBD4
__basic_if_skip_38:
__basic_line_210:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_14
    ldy #>__basic_float_tmp_14
    jsr $BBD4
    lda #<__basic_float_const_18
    ldy #>__basic_float_const_18
    jsr $BBA2
    lda #<__basic_float_tmp_14
    ldy #>__basic_float_tmp_14
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_39
    jmp __basic_if_skip_40
__basic_if_then_39:
    lda #<__basic_float_const_19
    ldy #>__basic_float_const_19
    jsr $BBA2
    ldx #<__basic_var_MC
    ldy #>__basic_var_MC
    jsr $BBD4
__basic_if_skip_40:
__basic_line_220:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_15
    ldy #>__basic_float_tmp_15
    jsr $BBD4
    lda #<__basic_float_const_18
    ldy #>__basic_float_const_18
    jsr $BBA2
    lda #<__basic_float_tmp_15
    ldy #>__basic_float_tmp_15
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_41
    jmp __basic_if_skip_42
__basic_if_then_41:
    lda #<__basic_float_const_20
    ldy #>__basic_float_const_20
    jsr $BBA2
    ldx #<__basic_var_SF
    ldy #>__basic_var_SF
    jsr $BBD4
__basic_if_skip_42:
__basic_line_230:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_16
    ldy #>__basic_float_tmp_16
    jsr $BBD4
    lda #<__basic_float_const_7
    ldy #>__basic_float_const_7
    jsr $BBA2
    lda #<__basic_float_tmp_16
    ldy #>__basic_float_tmp_16
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_43
    jmp __basic_if_skip_44
__basic_if_then_43:
    lda #<__basic_float_const_21
    ldy #>__basic_float_const_21
    jsr $BBA2
    ldx #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBD4
__basic_if_skip_44:
__basic_line_240:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_17
    ldy #>__basic_float_tmp_17
    jsr $BBD4
    lda #<__basic_float_const_7
    ldy #>__basic_float_const_7
    jsr $BBA2
    lda #<__basic_float_tmp_17
    ldy #>__basic_float_tmp_17
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_45
    jmp __basic_if_skip_46
__basic_if_then_45:
    lda #<__basic_float_const_22
    ldy #>__basic_float_const_22
    jsr $BBA2
    ldx #<__basic_var_MC
    ldy #>__basic_var_MC
    jsr $BBD4
__basic_if_skip_46:
__basic_line_250:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_18
    ldy #>__basic_float_tmp_18
    jsr $BBD4
    lda #<__basic_float_const_7
    ldy #>__basic_float_const_7
    jsr $BBA2
    lda #<__basic_float_tmp_18
    ldy #>__basic_float_tmp_18
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_47
    jmp __basic_if_skip_48
__basic_if_then_47:
    lda #<__basic_float_const_23
    ldy #>__basic_float_const_23
    jsr $BBA2
    ldx #<__basic_var_SF
    ldy #>__basic_var_SF
    jsr $BBD4
__basic_if_skip_48:
__basic_line_260:
__basic_line_270:
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_SC
    ldy #>__basic_var_SC
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_FC
    ldy #>__basic_var_FC
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_DC
    ldy #>__basic_var_DC
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_OC
    ldy #>__basic_var_OC
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_GS
    ldy #>__basic_var_GS
    jsr $BBD4
__basic_line_280:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_VX
    ldy #>__basic_var_VX
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_VY
    ldy #>__basic_var_VY
    jsr $BBD4
    lda #<__basic_float_const_15
    ldy #>__basic_float_const_15
    jsr $BBA2
    ldx #<__basic_var_VW
    ldy #>__basic_var_VW
    jsr $BBD4
__basic_line_290:
    lda #<__basic_float_const_24
    ldy #>__basic_float_const_24
    jsr $BBA2
    jsr __basic_fac_to_int
    sta $FB
    stx $FC
    ldy #$00
    lda ($FB),y
    ldx #$00
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_21
    ldy #>__basic_float_tmp_21
    jsr $BBD4
    lda #<__basic_float_const_25
    ldy #>__basic_float_const_25
    jsr $BBA2
    lda #<__basic_float_tmp_21
    ldy #>__basic_float_tmp_21
    jsr __basic_mul
    ldx #<__basic_float_tmp_20
    ldy #>__basic_float_tmp_20
    jsr $BBD4
    lda #<__basic_float_const_26
    ldy #>__basic_float_const_26
    jsr $BBA2
    jsr __basic_fac_to_int
    sta $FB
    stx $FC
    ldy #$00
    lda ($FB),y
    ldx #$00
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_22
    ldy #>__basic_float_tmp_22
    jsr $BBD4
    lda #<__basic_float_const_27
    ldy #>__basic_float_const_27
    jsr $BBA2
    lda #<__basic_float_tmp_22
    ldy #>__basic_float_tmp_22
    jsr __basic_mul
    lda #<__basic_float_tmp_20
    ldy #>__basic_float_tmp_20
    jsr __basic_add
    ldx #<__basic_float_tmp_19
    ldy #>__basic_float_tmp_19
    jsr $BBD4
    lda #<__basic_float_const_28
    ldy #>__basic_float_const_28
    jsr $BBA2
    jsr __basic_fac_to_int
    sta $FB
    stx $FC
    ldy #$00
    lda ($FB),y
    ldx #$00
    jsr __basic_int_to_fac
    lda #<__basic_float_tmp_19
    ldy #>__basic_float_tmp_19
    jsr __basic_add
    lda $61
    beq __basic_neg_zero_49
    lda $66
    eor #$80
    sta $66
__basic_neg_zero_49:
    jsr $E097
    ldx #<__basic_var_R
    ldy #>__basic_var_R
    jsr $BBD4
__basic_line_300:
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_PL
    ldy #>__basic_var_PL
    jsr $BBD4
__basic_line_310:
    lda #<__basic_var_PL
    ldy #>__basic_var_PL
    jsr $BBA2
    ldx #<__basic_float_tmp_23
    ldy #>__basic_float_tmp_23
    jsr $BBD4
    lda #<__basic_var_MC
    ldy #>__basic_var_MC
    jsr $BBA2
    lda #<__basic_float_tmp_23
    ldy #>__basic_float_tmp_23
    jsr __basic_cmp_ge
    lda $61
    bne __basic_if_then_50
    jmp __basic_if_skip_51
__basic_if_then_50:
    jmp __basic_line_400
__basic_if_skip_51:
__basic_line_320:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    jsr $E097
    ldx #<__basic_float_tmp_25
    ldy #>__basic_float_tmp_25
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_25
    ldy #>__basic_float_tmp_25
    jsr __basic_mul
    jsr $BCCC
    ldx #<__basic_float_tmp_24
    ldy #>__basic_float_tmp_24
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_24
    ldy #>__basic_float_tmp_24
    jsr __basic_add
    ldx #<__basic_var_RX
    ldy #>__basic_var_RX
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    jsr $E097
    ldx #<__basic_float_tmp_27
    ldy #>__basic_float_tmp_27
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_27
    ldy #>__basic_float_tmp_27
    jsr __basic_mul
    jsr $BCCC
    ldx #<__basic_float_tmp_26
    ldy #>__basic_float_tmp_26
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_26
    ldy #>__basic_float_tmp_26
    jsr __basic_add
    ldx #<__basic_var_RY
    ldy #>__basic_var_RY
    jsr $BBD4
__basic_line_330:
    lda #<__basic_var_RY
    ldy #>__basic_var_RY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_54
    bne __basic_index_bad_55
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_54
    beq __basic_index_ok_54
__basic_index_bad_55:
    jsr __basic_bad_subscript
__basic_index_ok_54:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_RX
    ldy #>__basic_var_RX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_56
    bne __basic_index_bad_57
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_56
    beq __basic_index_ok_56
__basic_index_bad_57:
    jsr __basic_bad_subscript
__basic_index_ok_56:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_M_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_M_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_28
    ldy #>__basic_float_tmp_28
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_28
    ldy #>__basic_float_tmp_28
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_52
    jmp __basic_if_skip_53
__basic_if_then_52:
    jmp __basic_line_320
__basic_if_skip_53:
__basic_line_340:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_var_RY
    ldy #>__basic_var_RY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_58
    bne __basic_index_bad_59
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_58
    beq __basic_index_ok_58
__basic_index_bad_59:
    jsr __basic_bad_subscript
__basic_index_ok_58:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_RX
    ldy #>__basic_var_RX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_60
    bne __basic_index_bad_61
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_60
    beq __basic_index_ok_60
__basic_index_bad_61:
    jsr __basic_bad_subscript
__basic_index_ok_60:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_M_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_M_
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    txa
    iny
    sta ($FB),y
    lda #<__basic_var_PL
    ldy #>__basic_var_PL
    jsr $BBA2
    ldx #<__basic_float_tmp_29
    ldy #>__basic_float_tmp_29
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_29
    ldy #>__basic_float_tmp_29
    jsr __basic_add
    ldx #<__basic_var_PL
    ldy #>__basic_var_PL
    jsr $BBD4
    jmp __basic_line_310
__basic_line_400:
    lda #<__basic_float_const_24
    ldy #>__basic_float_const_24
    jsr $BBA2
    jsr __basic_fac_to_int
    sta $FB
    stx $FC
    ldy #$00
    lda ($FB),y
    ldx #$00
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_32
    ldy #>__basic_float_tmp_32
    jsr $BBD4
    lda #<__basic_float_const_25
    ldy #>__basic_float_const_25
    jsr $BBA2
    lda #<__basic_float_tmp_32
    ldy #>__basic_float_tmp_32
    jsr __basic_mul
    ldx #<__basic_float_tmp_31
    ldy #>__basic_float_tmp_31
    jsr $BBD4
    lda #<__basic_float_const_26
    ldy #>__basic_float_const_26
    jsr $BBA2
    jsr __basic_fac_to_int
    sta $FB
    stx $FC
    ldy #$00
    lda ($FB),y
    ldx #$00
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_33
    ldy #>__basic_float_tmp_33
    jsr $BBD4
    lda #<__basic_float_const_27
    ldy #>__basic_float_const_27
    jsr $BBA2
    lda #<__basic_float_tmp_33
    ldy #>__basic_float_tmp_33
    jsr __basic_mul
    lda #<__basic_float_tmp_31
    ldy #>__basic_float_tmp_31
    jsr __basic_add
    ldx #<__basic_float_tmp_30
    ldy #>__basic_float_tmp_30
    jsr $BBD4
    lda #<__basic_float_const_28
    ldy #>__basic_float_const_28
    jsr $BBA2
    jsr __basic_fac_to_int
    sta $FB
    stx $FC
    ldy #$00
    lda ($FB),y
    ldx #$00
    jsr __basic_int_to_fac
    lda #<__basic_float_tmp_30
    ldy #>__basic_float_tmp_30
    jsr __basic_add
    ldx #<__basic_var_T0
    ldy #>__basic_var_T0
    jsr $BBD4
__basic_line_410:
    lda #<__basic_float_const_29
    ldy #>__basic_float_const_29
    jsr $BBA2
    ldx #<__basic_var_LT
    ldy #>__basic_var_LT
    jsr $BBD4
__basic_line_420:
    jsr __basic_line_1800
    jsr __basic_line_1900
    jsr __basic_line_2000
__basic_line_430:
    jmp __basic_line_1000
__basic_line_1000:
    jsr __basic_line_1900
__basic_line_1010:
    lda #<__basic_var_ET
    ldy #>__basic_var_ET
    jsr $BBA2
    ldx #<__basic_float_tmp_34
    ldy #>__basic_float_tmp_34
    jsr $BBD4
    lda #<__basic_var_LT
    ldy #>__basic_var_LT
    jsr $BBA2
    lda #<__basic_float_tmp_34
    ldy #>__basic_float_tmp_34
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_62
    jmp __basic_if_skip_63
__basic_if_then_62:
    jmp __basic_line_1040
__basic_if_skip_63:
__basic_line_1020:
    lda #<__basic_var_ET
    ldy #>__basic_var_ET
    jsr $BBA2
    ldx #<__basic_var_LT
    ldy #>__basic_var_LT
    jsr $BBD4
__basic_line_1030:
    jsr __basic_line_2000
__basic_line_1040:
    jsr $FFE4
    sta __basic_get_char
    lda __basic_get_char
    beq __basic_get_empty_64
    sta __basic_string_term+1
    lda #$01
    sta __basic_string_term
    jmp __basic_get_done_65
__basic_get_empty_64:
    lda #$00
    sta __basic_string_term
__basic_get_done_65:
    lda #<__basic_str_K_
    sta $FB
    lda #>__basic_str_K_
    sta $FC
    lda #<__basic_string_term
    sta $FD
    lda #>__basic_string_term
    sta $FE
    jsr __basic_string_copy
    lda #<__basic_string_left
    sta $FB
    lda #>__basic_string_left
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_str_K_
    sta $FD
    lda #>__basic_str_K_
    sta $FE
    lda #<__basic_string_left
    sta $FB
    lda #>__basic_string_left
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_right
    sta $FB
    lda #>__basic_string_right
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_12
    sta $FD
    lda #>__basic_string_12
    sta $FE
    lda #<__basic_string_right
    sta $FB
    lda #>__basic_string_right
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_left
    sta $FB
    lda #>__basic_string_left
    sta $FC
    lda #<__basic_string_right
    sta $FD
    lda #>__basic_string_right
    sta $FE
    jsr __basic_string_compare
    beq __basic_str_cmp_true_68
    lda #$00
    jmp __basic_str_cmp_done_69
__basic_str_cmp_true_68:
    lda #$01
__basic_str_cmp_done_69:
    cmp #$00
    bne __basic_if_then_66
    jmp __basic_if_skip_67
__basic_if_then_66:
    jmp __basic_line_1000
__basic_if_skip_67:
__basic_line_1045:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_str_K_
    sta $FD
    lda #>__basic_str_K_
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda __basic_string_expr
    beq __basic_asc_empty_70
    lda __basic_string_expr+1
    ldx #$00
    jmp __basic_asc_done_71
__basic_asc_empty_70:
    lda #$00
    tax
__basic_asc_done_71:
    jsr __basic_int_to_fac
    ldx #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBD4
__basic_line_1050:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_35
    ldy #>__basic_float_tmp_35
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_35
    ldy #>__basic_float_tmp_35
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_72
    jmp __basic_if_skip_73
__basic_if_then_72:
    jmp __basic_line_1000
__basic_if_skip_73:
__basic_line_1060:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_36
    ldy #>__basic_float_tmp_36
    jsr $BBD4
    lda #<__basic_float_const_30
    ldy #>__basic_float_const_30
    jsr $BBA2
    lda #<__basic_float_tmp_36
    ldy #>__basic_float_tmp_36
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_74
    jmp __basic_if_skip_75
__basic_if_then_74:
    jmp __basic_line_8900
__basic_if_skip_75:
__basic_line_1070:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_38
    ldy #>__basic_float_tmp_38
    jsr $BBD4
    lda #<__basic_float_const_31
    ldy #>__basic_float_const_31
    jsr $BBA2
    lda #<__basic_float_tmp_38
    ldy #>__basic_float_tmp_38
    jsr __basic_cmp_eq
    ldx #<__basic_float_tmp_37
    ldy #>__basic_float_tmp_37
    jsr $BBD4
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    ldx #<__basic_float_tmp_39
    ldy #>__basic_float_tmp_39
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_39
    ldy #>__basic_float_tmp_39
    jsr __basic_cmp_gt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_37
    ldy #>__basic_float_tmp_37
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_and
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_76
    jmp __basic_if_skip_77
__basic_if_then_76:
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    ldx #<__basic_float_tmp_40
    ldy #>__basic_float_tmp_40
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_40
    ldy #>__basic_float_tmp_40
    jsr __basic_sub
    ldx #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBD4
__basic_if_skip_77:
__basic_line_1080:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_42
    ldy #>__basic_float_tmp_42
    jsr $BBD4
    lda #<__basic_float_const_32
    ldy #>__basic_float_const_32
    jsr $BBA2
    lda #<__basic_float_tmp_42
    ldy #>__basic_float_tmp_42
    jsr __basic_cmp_eq
    ldx #<__basic_float_tmp_41
    ldy #>__basic_float_tmp_41
    jsr $BBD4
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    ldx #<__basic_float_tmp_43
    ldy #>__basic_float_tmp_43
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_43
    ldy #>__basic_float_tmp_43
    jsr __basic_cmp_lt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_41
    ldy #>__basic_float_tmp_41
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_and
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_78
    jmp __basic_if_skip_79
__basic_if_then_78:
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    ldx #<__basic_float_tmp_44
    ldy #>__basic_float_tmp_44
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_44
    ldy #>__basic_float_tmp_44
    jsr __basic_add
    ldx #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBD4
__basic_if_skip_79:
__basic_line_1090:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_46
    ldy #>__basic_float_tmp_46
    jsr $BBD4
    lda #<__basic_float_const_33
    ldy #>__basic_float_const_33
    jsr $BBA2
    lda #<__basic_float_tmp_46
    ldy #>__basic_float_tmp_46
    jsr __basic_cmp_eq
    ldx #<__basic_float_tmp_45
    ldy #>__basic_float_tmp_45
    jsr $BBD4
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    ldx #<__basic_float_tmp_47
    ldy #>__basic_float_tmp_47
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_47
    ldy #>__basic_float_tmp_47
    jsr __basic_cmp_gt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_45
    ldy #>__basic_float_tmp_45
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_and
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_80
    jmp __basic_if_skip_81
__basic_if_then_80:
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    ldx #<__basic_float_tmp_48
    ldy #>__basic_float_tmp_48
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_48
    ldy #>__basic_float_tmp_48
    jsr __basic_sub
    ldx #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBD4
__basic_if_skip_81:
__basic_line_1100:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_50
    ldy #>__basic_float_tmp_50
    jsr $BBD4
    lda #<__basic_float_const_34
    ldy #>__basic_float_const_34
    jsr $BBA2
    lda #<__basic_float_tmp_50
    ldy #>__basic_float_tmp_50
    jsr __basic_cmp_eq
    ldx #<__basic_float_tmp_49
    ldy #>__basic_float_tmp_49
    jsr $BBD4
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    ldx #<__basic_float_tmp_51
    ldy #>__basic_float_tmp_51
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_51
    ldy #>__basic_float_tmp_51
    jsr __basic_cmp_lt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_49
    ldy #>__basic_float_tmp_49
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_and
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_82
    jmp __basic_if_skip_83
__basic_if_then_82:
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    ldx #<__basic_float_tmp_52
    ldy #>__basic_float_tmp_52
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_52
    ldy #>__basic_float_tmp_52
    jsr __basic_add
    ldx #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBD4
__basic_if_skip_83:
__basic_line_1110:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_53
    ldy #>__basic_float_tmp_53
    jsr $BBD4
    lda #<__basic_float_const_35
    ldy #>__basic_float_const_35
    jsr $BBA2
    lda #<__basic_float_tmp_53
    ldy #>__basic_float_tmp_53
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_84
    jmp __basic_if_skip_85
__basic_if_then_84:
    jsr __basic_line_3500
__basic_if_skip_85:
__basic_line_1120:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_56
    ldy #>__basic_float_tmp_56
    jsr $BBD4
    lda #<__basic_float_const_36
    ldy #>__basic_float_const_36
    jsr $BBA2
    lda #<__basic_float_tmp_56
    ldy #>__basic_float_tmp_56
    jsr __basic_cmp_eq
    ldx #<__basic_float_tmp_55
    ldy #>__basic_float_tmp_55
    jsr $BBD4
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_57
    ldy #>__basic_float_tmp_57
    jsr $BBD4
    lda #<__basic_float_const_37
    ldy #>__basic_float_const_37
    jsr $BBA2
    lda #<__basic_float_tmp_57
    ldy #>__basic_float_tmp_57
    jsr __basic_cmp_eq
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_55
    ldy #>__basic_float_tmp_55
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_or
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_54
    ldy #>__basic_float_tmp_54
    jsr $BBD4
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_58
    ldy #>__basic_float_tmp_58
    jsr $BBD4
    lda #<__basic_float_const_38
    ldy #>__basic_float_const_38
    jsr $BBA2
    lda #<__basic_float_tmp_58
    ldy #>__basic_float_tmp_58
    jsr __basic_cmp_eq
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_54
    ldy #>__basic_float_tmp_54
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_or
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_86
    jmp __basic_if_skip_87
__basic_if_then_86:
    jsr __basic_line_4000
__basic_if_skip_87:
__basic_line_1130:
    jsr __basic_line_1800
__basic_line_1140:
    jsr __basic_line_1900
__basic_line_1150:
    jsr __basic_line_2000
__basic_line_1160:
    lda #<__basic_var_GS
    ldy #>__basic_var_GS
    jsr $BBA2
    ldx #<__basic_float_tmp_59
    ldy #>__basic_float_tmp_59
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_59
    ldy #>__basic_float_tmp_59
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_88
    jmp __basic_if_skip_89
__basic_if_then_88:
    jmp __basic_line_8000
__basic_if_skip_89:
__basic_line_1170:
    lda #<__basic_var_GS
    ldy #>__basic_var_GS
    jsr $BBA2
    ldx #<__basic_float_tmp_60
    ldy #>__basic_float_tmp_60
    jsr $BBD4
    lda #<__basic_float_const_13
    ldy #>__basic_float_const_13
    jsr $BBA2
    lda #<__basic_float_tmp_60
    ldy #>__basic_float_tmp_60
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_90
    jmp __basic_if_skip_91
__basic_if_then_90:
    jmp __basic_line_8500
__basic_if_skip_91:
__basic_line_1180:
    jmp __basic_line_1000
__basic_line_1800:
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    ldx #<__basic_float_tmp_61
    ldy #>__basic_float_tmp_61
    jsr $BBD4
    lda #<__basic_var_VX
    ldy #>__basic_var_VX
    jsr $BBA2
    lda #<__basic_float_tmp_61
    ldy #>__basic_float_tmp_61
    jsr __basic_cmp_le
    lda $61
    bne __basic_if_then_92
    jmp __basic_if_skip_93
__basic_if_then_92:
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    ldx #<__basic_float_tmp_62
    ldy #>__basic_float_tmp_62
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_62
    ldy #>__basic_float_tmp_62
    jsr __basic_sub
    ldx #<__basic_var_VX
    ldy #>__basic_var_VX
    jsr $BBD4
__basic_if_skip_93:
__basic_line_1810:
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    ldx #<__basic_float_tmp_63
    ldy #>__basic_float_tmp_63
    jsr $BBD4
    lda #<__basic_var_VX
    ldy #>__basic_var_VX
    jsr $BBA2
    ldx #<__basic_float_tmp_64
    ldy #>__basic_float_tmp_64
    jsr $BBD4
    lda #<__basic_var_VW
    ldy #>__basic_var_VW
    jsr $BBA2
    lda #<__basic_float_tmp_64
    ldy #>__basic_float_tmp_64
    jsr __basic_add
    lda #<__basic_float_tmp_63
    ldy #>__basic_float_tmp_63
    jsr __basic_cmp_gt
    lda $61
    bne __basic_if_then_94
    jmp __basic_if_skip_95
__basic_if_then_94:
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    ldx #<__basic_float_tmp_65
    ldy #>__basic_float_tmp_65
    jsr $BBD4
    lda #<__basic_var_VW
    ldy #>__basic_var_VW
    jsr $BBA2
    lda #<__basic_float_tmp_65
    ldy #>__basic_float_tmp_65
    jsr __basic_sub
    ldx #<__basic_var_VX
    ldy #>__basic_var_VX
    jsr $BBD4
__basic_if_skip_95:
__basic_line_1820:
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    ldx #<__basic_float_tmp_66
    ldy #>__basic_float_tmp_66
    jsr $BBD4
    lda #<__basic_var_VY
    ldy #>__basic_var_VY
    jsr $BBA2
    lda #<__basic_float_tmp_66
    ldy #>__basic_float_tmp_66
    jsr __basic_cmp_le
    lda $61
    bne __basic_if_then_96
    jmp __basic_if_skip_97
__basic_if_then_96:
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    ldx #<__basic_float_tmp_67
    ldy #>__basic_float_tmp_67
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_67
    ldy #>__basic_float_tmp_67
    jsr __basic_sub
    ldx #<__basic_var_VY
    ldy #>__basic_var_VY
    jsr $BBD4
__basic_if_skip_97:
__basic_line_1830:
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    ldx #<__basic_float_tmp_68
    ldy #>__basic_float_tmp_68
    jsr $BBD4
    lda #<__basic_var_VY
    ldy #>__basic_var_VY
    jsr $BBA2
    ldx #<__basic_float_tmp_69
    ldy #>__basic_float_tmp_69
    jsr $BBD4
    lda #<__basic_var_VW
    ldy #>__basic_var_VW
    jsr $BBA2
    lda #<__basic_float_tmp_69
    ldy #>__basic_float_tmp_69
    jsr __basic_add
    lda #<__basic_float_tmp_68
    ldy #>__basic_float_tmp_68
    jsr __basic_cmp_gt
    lda $61
    bne __basic_if_then_98
    jmp __basic_if_skip_99
__basic_if_then_98:
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    ldx #<__basic_float_tmp_70
    ldy #>__basic_float_tmp_70
    jsr $BBD4
    lda #<__basic_var_VW
    ldy #>__basic_var_VW
    jsr $BBA2
    lda #<__basic_float_tmp_70
    ldy #>__basic_float_tmp_70
    jsr __basic_sub
    ldx #<__basic_var_VY
    ldy #>__basic_var_VY
    jsr $BBD4
__basic_if_skip_99:
__basic_line_1840:
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    ldx #<__basic_float_tmp_71
    ldy #>__basic_float_tmp_71
    jsr $BBD4
    lda #<__basic_var_VW
    ldy #>__basic_var_VW
    jsr $BBA2
    lda #<__basic_float_tmp_71
    ldy #>__basic_float_tmp_71
    jsr __basic_sub
    ldx #<__basic_var_MX
    ldy #>__basic_var_MX
    jsr $BBD4
__basic_line_1850:
    lda #<__basic_var_MX
    ldy #>__basic_var_MX
    jsr $BBA2
    ldx #<__basic_float_tmp_72
    ldy #>__basic_float_tmp_72
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_72
    ldy #>__basic_float_tmp_72
    jsr __basic_cmp_lt
    lda $61
    bne __basic_if_then_100
    jmp __basic_if_skip_101
__basic_if_then_100:
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_MX
    ldy #>__basic_var_MX
    jsr $BBD4
__basic_if_skip_101:
__basic_line_1860:
    lda #<__basic_var_VX
    ldy #>__basic_var_VX
    jsr $BBA2
    ldx #<__basic_float_tmp_73
    ldy #>__basic_float_tmp_73
    jsr $BBD4
    lda #<__basic_var_MX
    ldy #>__basic_var_MX
    jsr $BBA2
    lda #<__basic_float_tmp_73
    ldy #>__basic_float_tmp_73
    jsr __basic_cmp_gt
    lda $61
    bne __basic_if_then_102
    jmp __basic_if_skip_103
__basic_if_then_102:
    lda #<__basic_var_MX
    ldy #>__basic_var_MX
    jsr $BBA2
    ldx #<__basic_var_VX
    ldy #>__basic_var_VX
    jsr $BBD4
__basic_if_skip_103:
__basic_line_1870:
    lda #<__basic_var_VY
    ldy #>__basic_var_VY
    jsr $BBA2
    ldx #<__basic_float_tmp_74
    ldy #>__basic_float_tmp_74
    jsr $BBD4
    lda #<__basic_var_MX
    ldy #>__basic_var_MX
    jsr $BBA2
    lda #<__basic_float_tmp_74
    ldy #>__basic_float_tmp_74
    jsr __basic_cmp_gt
    lda $61
    bne __basic_if_then_104
    jmp __basic_if_skip_105
__basic_if_then_104:
    lda #<__basic_var_MX
    ldy #>__basic_var_MX
    jsr $BBA2
    ldx #<__basic_var_VY
    ldy #>__basic_var_VY
    jsr $BBD4
__basic_if_skip_105:
__basic_line_1880:
    rts
__basic_line_1900:
    lda #<__basic_float_const_24
    ldy #>__basic_float_const_24
    jsr $BBA2
    jsr __basic_fac_to_int
    sta $FB
    stx $FC
    ldy #$00
    lda ($FB),y
    ldx #$00
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_77
    ldy #>__basic_float_tmp_77
    jsr $BBD4
    lda #<__basic_float_const_25
    ldy #>__basic_float_const_25
    jsr $BBA2
    lda #<__basic_float_tmp_77
    ldy #>__basic_float_tmp_77
    jsr __basic_mul
    ldx #<__basic_float_tmp_76
    ldy #>__basic_float_tmp_76
    jsr $BBD4
    lda #<__basic_float_const_26
    ldy #>__basic_float_const_26
    jsr $BBA2
    jsr __basic_fac_to_int
    sta $FB
    stx $FC
    ldy #$00
    lda ($FB),y
    ldx #$00
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_78
    ldy #>__basic_float_tmp_78
    jsr $BBD4
    lda #<__basic_float_const_27
    ldy #>__basic_float_const_27
    jsr $BBA2
    lda #<__basic_float_tmp_78
    ldy #>__basic_float_tmp_78
    jsr __basic_mul
    lda #<__basic_float_tmp_76
    ldy #>__basic_float_tmp_76
    jsr __basic_add
    ldx #<__basic_float_tmp_75
    ldy #>__basic_float_tmp_75
    jsr $BBD4
    lda #<__basic_float_const_28
    ldy #>__basic_float_const_28
    jsr $BBA2
    jsr __basic_fac_to_int
    sta $FB
    stx $FC
    ldy #$00
    lda ($FB),y
    ldx #$00
    jsr __basic_int_to_fac
    lda #<__basic_float_tmp_75
    ldy #>__basic_float_tmp_75
    jsr __basic_add
    ldx #<__basic_var_CT
    ldy #>__basic_var_CT
    jsr $BBD4
__basic_line_1910:
    lda #<__basic_var_CT
    ldy #>__basic_var_CT
    jsr $BBA2
    ldx #<__basic_float_tmp_79
    ldy #>__basic_float_tmp_79
    jsr $BBD4
    lda #<__basic_var_T0
    ldy #>__basic_var_T0
    jsr $BBA2
    lda #<__basic_float_tmp_79
    ldy #>__basic_float_tmp_79
    jsr __basic_sub
    ldx #<__basic_var_DT
    ldy #>__basic_var_DT
    jsr $BBD4
__basic_line_1920:
    lda #<__basic_var_DT
    ldy #>__basic_var_DT
    jsr $BBA2
    ldx #<__basic_float_tmp_80
    ldy #>__basic_float_tmp_80
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_80
    ldy #>__basic_float_tmp_80
    jsr __basic_cmp_ge
    lda $61
    bne __basic_if_then_106
    jmp __basic_if_skip_107
__basic_if_then_106:
    jmp __basic_line_1940
__basic_if_skip_107:
__basic_line_1930:
    lda #<__basic_var_DT
    ldy #>__basic_var_DT
    jsr $BBA2
    ldx #<__basic_float_tmp_81
    ldy #>__basic_float_tmp_81
    jsr $BBD4
    lda #<__basic_float_const_39
    ldy #>__basic_float_const_39
    jsr $BBA2
    lda #<__basic_float_tmp_81
    ldy #>__basic_float_tmp_81
    jsr __basic_add
    ldx #<__basic_var_DT
    ldy #>__basic_var_DT
    jsr $BBD4
__basic_line_1940:
    lda #<__basic_var_DT
    ldy #>__basic_var_DT
    jsr $BBA2
    ldx #<__basic_float_tmp_82
    ldy #>__basic_float_tmp_82
    jsr $BBD4
    lda #<__basic_float_const_40
    ldy #>__basic_float_const_40
    jsr $BBA2
    lda #<__basic_float_tmp_82
    ldy #>__basic_float_tmp_82
    jsr __basic_div
    jsr $BCCC
    ldx #<__basic_var_ET
    ldy #>__basic_var_ET
    jsr $BBD4
__basic_line_1950:
    rts
__basic_line_2000:
    lda #<__basic_float_const_5
    ldy #>__basic_float_const_5
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_string_term+1
    lda #$01
    sta __basic_string_term
    lda #<__basic_string_term
    ldy #>__basic_string_term
    jsr __basic_print_string
__basic_line_2010:
    lda #<__basic_string_108
    ldy #>__basic_string_108
    jsr __basic_print_string
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    jsr __basic_print_float
    lda #<__basic_string_109
    ldy #>__basic_string_109
    jsr __basic_print_string
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    jsr __basic_print_float
    lda #<__basic_string_110
    ldy #>__basic_string_110
    jsr __basic_print_string
    lda #<__basic_var_MC
    ldy #>__basic_var_MC
    jsr $BBA2
    jsr __basic_print_float
    jsr __basic_newline
__basic_line_2020:
    lda #<__basic_string_111
    ldy #>__basic_string_111
    jsr __basic_print_string
    lda #<__basic_var_ET
    ldy #>__basic_var_ET
    jsr $BBA2
    jsr __basic_print_float
    lda #<__basic_string_112
    ldy #>__basic_string_112
    jsr __basic_print_string
    lda #<__basic_var_SC
    ldy #>__basic_var_SC
    jsr $BBA2
    jsr __basic_print_float
    lda #<__basic_string_113
    ldy #>__basic_string_113
    jsr __basic_print_string
    lda #<__basic_var_FC
    ldy #>__basic_var_FC
    jsr $BBA2
    jsr __basic_print_float
    lda #<__basic_string_114
    ldy #>__basic_string_114
    jsr __basic_print_string
    lda #<__basic_var_DC
    ldy #>__basic_var_DC
    jsr $BBA2
    jsr __basic_print_float
    jsr __basic_newline
__basic_line_2030:
    lda #<__basic_string_115
    ldy #>__basic_string_115
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_2040:
    lda #<__basic_var_VX
    ldy #>__basic_var_VX
    jsr $BBA2
    ldx #<__basic_float_tmp_83
    ldy #>__basic_float_tmp_83
    jsr $BBD4
    lda #<__basic_var_VW
    ldy #>__basic_var_VW
    jsr $BBA2
    lda #<__basic_float_tmp_83
    ldy #>__basic_float_tmp_83
    jsr __basic_add
    ldx #<__basic_var_EX
    ldy #>__basic_var_EX
    jsr $BBD4
__basic_line_2050:
    lda #<__basic_var_EX
    ldy #>__basic_var_EX
    jsr $BBA2
    ldx #<__basic_float_tmp_84
    ldy #>__basic_float_tmp_84
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_84
    ldy #>__basic_float_tmp_84
    jsr __basic_cmp_gt
    lda $61
    bne __basic_if_then_116
    jmp __basic_if_skip_117
__basic_if_then_116:
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    ldx #<__basic_var_EX
    ldy #>__basic_var_EX
    jsr $BBD4
__basic_if_skip_117:
__basic_line_2060:
    lda #<__basic_var_VY
    ldy #>__basic_var_VY
    jsr $BBA2
    ldx #<__basic_float_tmp_85
    ldy #>__basic_float_tmp_85
    jsr $BBD4
    lda #<__basic_var_VW
    ldy #>__basic_var_VW
    jsr $BBA2
    lda #<__basic_float_tmp_85
    ldy #>__basic_float_tmp_85
    jsr __basic_add
    ldx #<__basic_var_EY
    ldy #>__basic_var_EY
    jsr $BBD4
__basic_line_2070:
    lda #<__basic_var_EY
    ldy #>__basic_var_EY
    jsr $BBA2
    ldx #<__basic_float_tmp_86
    ldy #>__basic_float_tmp_86
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_86
    ldy #>__basic_float_tmp_86
    jsr __basic_cmp_gt
    lda $61
    bne __basic_if_then_118
    jmp __basic_if_skip_119
__basic_if_then_118:
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    ldx #<__basic_var_EY
    ldy #>__basic_var_EY
    jsr $BBD4
__basic_if_skip_119:
__basic_line_2080:
    lda #<__basic_var_VY
    ldy #>__basic_var_VY
    jsr $BBA2
    ldx #<__basic_float_tmp_89
    ldy #>__basic_float_tmp_89
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_89
    ldy #>__basic_float_tmp_89
    jsr __basic_add
    ldx #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBD4
    lda #<__basic_var_EY
    ldy #>__basic_var_EY
    jsr $BBA2
    ldx #<__basic_float_tmp_87
    ldy #>__basic_float_tmp_87
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_88
    ldy #>__basic_float_tmp_88
    jsr $BBD4
__basic_for_loop_120:
__basic_line_2090:
    lda #<__basic_var_VX
    ldy #>__basic_var_VX
    jsr $BBA2
    ldx #<__basic_float_tmp_92
    ldy #>__basic_float_tmp_92
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_92
    ldy #>__basic_float_tmp_92
    jsr __basic_add
    ldx #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBD4
    lda #<__basic_var_EX
    ldy #>__basic_var_EX
    jsr $BBA2
    ldx #<__basic_float_tmp_90
    ldy #>__basic_float_tmp_90
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_91
    ldy #>__basic_float_tmp_91
    jsr $BBD4
__basic_for_loop_121:
__basic_line_2100:
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    ldx #<__basic_var_TX
    ldy #>__basic_var_TX
    jsr $BBD4
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    ldx #<__basic_var_TY
    ldy #>__basic_var_TY
    jsr $BBD4
    jsr __basic_line_2600
__basic_line_2110:
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    ldx #<__basic_float_tmp_94
    ldy #>__basic_float_tmp_94
    jsr $BBD4
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    lda #<__basic_float_tmp_94
    ldy #>__basic_float_tmp_94
    jsr __basic_cmp_eq
    ldx #<__basic_float_tmp_93
    ldy #>__basic_float_tmp_93
    jsr $BBD4
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    ldx #<__basic_float_tmp_95
    ldy #>__basic_float_tmp_95
    jsr $BBD4
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    lda #<__basic_float_tmp_95
    ldy #>__basic_float_tmp_95
    jsr __basic_cmp_eq
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_93
    ldy #>__basic_float_tmp_93
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_and
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_122
    jmp __basic_if_skip_123
__basic_if_then_122:
    lda #<__basic_float_const_41
    ldy #>__basic_float_const_41
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_string_term+1
    lda #$01
    sta __basic_string_term
    lda #<__basic_string_term
    ldy #>__basic_string_term
    jsr __basic_print_string
__basic_if_skip_123:
__basic_line_2120:
    lda #<__basic_str_C_
    ldy #>__basic_str_C_
    jsr __basic_print_string
__basic_line_2130:
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    ldx #<__basic_float_tmp_97
    ldy #>__basic_float_tmp_97
    jsr $BBD4
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    lda #<__basic_float_tmp_97
    ldy #>__basic_float_tmp_97
    jsr __basic_cmp_eq
    ldx #<__basic_float_tmp_96
    ldy #>__basic_float_tmp_96
    jsr $BBD4
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    ldx #<__basic_float_tmp_98
    ldy #>__basic_float_tmp_98
    jsr $BBD4
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    lda #<__basic_float_tmp_98
    ldy #>__basic_float_tmp_98
    jsr __basic_cmp_eq
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_96
    ldy #>__basic_float_tmp_96
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_and
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_124
    jmp __basic_if_skip_125
__basic_if_then_124:
    lda #<__basic_float_const_42
    ldy #>__basic_float_const_42
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_string_term+1
    lda #$01
    sta __basic_string_term
    lda #<__basic_string_term
    ldy #>__basic_string_term
    jsr __basic_print_string
__basic_if_skip_125:
__basic_line_2140:
    lda #<__basic_float_tmp_91
    ldy #>__basic_float_tmp_91
    jsr $BBA2
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr __basic_add
    ldx #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBD4
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    lda #<__basic_float_tmp_90
    ldy #>__basic_float_tmp_90
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_91
    ldy #>__basic_float_tmp_91
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_126
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_127
    jmp __basic_for_loop_121
__basic_for_negative_126:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_127
    jmp __basic_for_loop_121
__basic_for_done_127:
__basic_line_2150:
    jsr __basic_newline
__basic_line_2160:
    lda #<__basic_float_tmp_88
    ldy #>__basic_float_tmp_88
    jsr $BBA2
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr __basic_add
    ldx #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBD4
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    lda #<__basic_float_tmp_87
    ldy #>__basic_float_tmp_87
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_88
    ldy #>__basic_float_tmp_88
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_128
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_129
    jmp __basic_for_loop_120
__basic_for_negative_128:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_129
    jmp __basic_for_loop_120
__basic_for_done_129:
__basic_line_2170:
    rts
__basic_line_2600:
    lda #<__basic_var_GS
    ldy #>__basic_var_GS
    jsr $BBA2
    ldx #<__basic_float_tmp_99
    ldy #>__basic_float_tmp_99
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_99
    ldy #>__basic_float_tmp_99
    jsr __basic_cmp_ne
    lda $61
    bne __basic_if_then_130
    jmp __basic_if_skip_131
__basic_if_then_130:
    jmp __basic_line_2620
__basic_if_skip_131:
__basic_line_2610:
    lda #<__basic_var_TY
    ldy #>__basic_var_TY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_134
    bne __basic_index_bad_135
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_134
    beq __basic_index_ok_134
__basic_index_bad_135:
    jsr __basic_bad_subscript
__basic_index_ok_134:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_TX
    ldy #>__basic_var_TX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_136
    bne __basic_index_bad_137
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_136
    beq __basic_index_ok_136
__basic_index_bad_137:
    jsr __basic_bad_subscript
__basic_index_ok_136:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_M_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_M_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_100
    ldy #>__basic_float_tmp_100
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_100
    ldy #>__basic_float_tmp_100
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_132
    jmp __basic_if_skip_133
__basic_if_then_132:
    jmp __basic_line_2620
__basic_if_skip_133:
__basic_line_2615:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_138
    sta $FD
    lda #>__basic_string_138
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_str_C_
    sta $FB
    lda #>__basic_str_C_
    sta $FC
    lda #<__basic_string_expr
    sta $FD
    lda #>__basic_string_expr
    sta $FE
    jsr __basic_string_copy
    rts
__basic_line_2620:
    lda #<__basic_var_TY
    ldy #>__basic_var_TY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_141
    bne __basic_index_bad_142
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_141
    beq __basic_index_ok_141
__basic_index_bad_142:
    jsr __basic_bad_subscript
__basic_index_ok_141:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_TX
    ldy #>__basic_var_TX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_143
    bne __basic_index_bad_144
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_143
    beq __basic_index_ok_143
__basic_index_bad_144:
    jsr __basic_bad_subscript
__basic_index_ok_143:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_D_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_D_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_101
    ldy #>__basic_float_tmp_101
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_101
    ldy #>__basic_float_tmp_101
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_139
    jmp __basic_if_skip_140
__basic_if_then_139:
    jmp __basic_line_2640
__basic_if_skip_140:
__basic_line_2630:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_145
    sta $FD
    lda #>__basic_string_145
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_str_C_
    sta $FB
    lda #>__basic_str_C_
    sta $FC
    lda #<__basic_string_expr
    sta $FD
    lda #>__basic_string_expr
    sta $FE
    jsr __basic_string_copy
    rts
__basic_line_2640:
    lda #<__basic_var_TY
    ldy #>__basic_var_TY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_148
    bne __basic_index_bad_149
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_148
    beq __basic_index_ok_148
__basic_index_bad_149:
    jsr __basic_bad_subscript
__basic_index_ok_148:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_TX
    ldy #>__basic_var_TX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_150
    bne __basic_index_bad_151
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_150
    beq __basic_index_ok_150
__basic_index_bad_151:
    jsr __basic_bad_subscript
__basic_index_ok_150:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_O_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_O_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_102
    ldy #>__basic_float_tmp_102
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_102
    ldy #>__basic_float_tmp_102
    jsr __basic_cmp_ne
    lda $61
    bne __basic_if_then_146
    jmp __basic_if_skip_147
__basic_if_then_146:
    jmp __basic_line_2660
__basic_if_skip_147:
__basic_line_2650:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_152
    sta $FD
    lda #>__basic_string_152
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_str_C_
    sta $FB
    lda #>__basic_str_C_
    sta $FC
    lda #<__basic_string_expr
    sta $FD
    lda #>__basic_string_expr
    sta $FE
    jsr __basic_string_copy
    rts
__basic_line_2660:
    lda #<__basic_var_TY
    ldy #>__basic_var_TY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_155
    bne __basic_index_bad_156
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_155
    beq __basic_index_ok_155
__basic_index_bad_156:
    jsr __basic_bad_subscript
__basic_index_ok_155:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_TX
    ldy #>__basic_var_TX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_157
    bne __basic_index_bad_158
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_157
    beq __basic_index_ok_157
__basic_index_bad_158:
    jsr __basic_bad_subscript
__basic_index_ok_157:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_O_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_O_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_103
    ldy #>__basic_float_tmp_103
    jsr $BBD4
    lda #<__basic_float_const_13
    ldy #>__basic_float_const_13
    jsr $BBA2
    lda #<__basic_float_tmp_103
    ldy #>__basic_float_tmp_103
    jsr __basic_cmp_ne
    lda $61
    bne __basic_if_then_153
    jmp __basic_if_skip_154
__basic_if_then_153:
    jmp __basic_line_2680
__basic_if_skip_154:
__basic_line_2670:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_159
    sta $FD
    lda #>__basic_string_159
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_str_C_
    sta $FB
    lda #>__basic_str_C_
    sta $FC
    lda #<__basic_string_expr
    sta $FD
    lda #>__basic_string_expr
    sta $FE
    jsr __basic_string_copy
    rts
__basic_line_2680:
    jsr __basic_line_5000
__basic_line_2690:
    lda #<__basic_var_NN
    ldy #>__basic_var_NN
    jsr $BBA2
    ldx #<__basic_float_tmp_104
    ldy #>__basic_float_tmp_104
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_104
    ldy #>__basic_float_tmp_104
    jsr __basic_cmp_ne
    lda $61
    bne __basic_if_then_160
    jmp __basic_if_skip_161
__basic_if_then_160:
    jmp __basic_line_2710
__basic_if_skip_161:
__basic_line_2700:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_162
    sta $FD
    lda #>__basic_string_162
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_str_C_
    sta $FB
    lda #>__basic_str_C_
    sta $FC
    lda #<__basic_string_expr
    sta $FD
    lda #>__basic_string_expr
    sta $FE
    jsr __basic_string_copy
    rts
__basic_line_2710:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_var_NN
    ldy #>__basic_var_NN
    jsr $BBA2
    jsr __basic_float_to_string_term
    lda #<__basic_string_term
    sta $FD
    lda #>__basic_string_term
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_str_C_
    sta $FB
    lda #>__basic_str_C_
    sta $FC
    lda #<__basic_string_expr
    sta $FD
    lda #>__basic_string_expr
    sta $FE
    jsr __basic_string_copy
__basic_line_2720:
    rts
__basic_line_3500:
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_165
    bne __basic_index_bad_166
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_165
    beq __basic_index_ok_165
__basic_index_bad_166:
    jsr __basic_bad_subscript
__basic_index_ok_165:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_167
    bne __basic_index_bad_168
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_167
    beq __basic_index_ok_167
__basic_index_bad_168:
    jsr __basic_bad_subscript
__basic_index_ok_167:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_D_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_D_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_105
    ldy #>__basic_float_tmp_105
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_105
    ldy #>__basic_float_tmp_105
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_163
    jmp __basic_if_skip_164
__basic_if_then_163:
    rts
__basic_if_skip_164:
__basic_line_3510:
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_171
    bne __basic_index_bad_172
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_171
    beq __basic_index_ok_171
__basic_index_bad_172:
    jsr __basic_bad_subscript
__basic_index_ok_171:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_173
    bne __basic_index_bad_174
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_173
    beq __basic_index_ok_173
__basic_index_bad_174:
    jsr __basic_bad_subscript
__basic_index_ok_173:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_O_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_O_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_106
    ldy #>__basic_float_tmp_106
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_106
    ldy #>__basic_float_tmp_106
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_169
    jmp __basic_if_skip_170
__basic_if_then_169:
    rts
__basic_if_skip_170:
__basic_line_3520:
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_177
    bne __basic_index_bad_178
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_177
    beq __basic_index_ok_177
__basic_index_bad_178:
    jsr __basic_bad_subscript
__basic_index_ok_177:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_179
    bne __basic_index_bad_180
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_179
    beq __basic_index_ok_179
__basic_index_bad_180:
    jsr __basic_bad_subscript
__basic_index_ok_179:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_O_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_O_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_107
    ldy #>__basic_float_tmp_107
    jsr $BBD4
    lda #<__basic_float_const_13
    ldy #>__basic_float_const_13
    jsr $BBA2
    lda #<__basic_float_tmp_107
    ldy #>__basic_float_tmp_107
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_175
    jmp __basic_if_skip_176
__basic_if_then_175:
    jmp __basic_line_3560
__basic_if_skip_176:
__basic_line_3530:
    lda #<__basic_var_FC
    ldy #>__basic_var_FC
    jsr $BBA2
    ldx #<__basic_float_tmp_108
    ldy #>__basic_float_tmp_108
    jsr $BBD4
    lda #<__basic_var_MC
    ldy #>__basic_var_MC
    jsr $BBA2
    lda #<__basic_float_tmp_108
    ldy #>__basic_float_tmp_108
    jsr __basic_cmp_ge
    lda $61
    bne __basic_if_then_181
    jmp __basic_if_skip_182
__basic_if_then_181:
    rts
__basic_if_skip_182:
__basic_line_3540:
    lda #<__basic_float_const_13
    ldy #>__basic_float_const_13
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_183
    bne __basic_index_bad_184
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_183
    beq __basic_index_ok_183
__basic_index_bad_184:
    jsr __basic_bad_subscript
__basic_index_ok_183:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_185
    bne __basic_index_bad_186
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_185
    beq __basic_index_ok_185
__basic_index_bad_186:
    jsr __basic_bad_subscript
__basic_index_ok_185:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_O_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_O_
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    txa
    iny
    sta ($FB),y
    lda #<__basic_var_FC
    ldy #>__basic_var_FC
    jsr $BBA2
    ldx #<__basic_float_tmp_109
    ldy #>__basic_float_tmp_109
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_109
    ldy #>__basic_float_tmp_109
    jsr __basic_add
    ldx #<__basic_var_FC
    ldy #>__basic_var_FC
    jsr $BBD4
__basic_line_3550:
    rts
__basic_line_3560:
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_187
    bne __basic_index_bad_188
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_187
    beq __basic_index_ok_187
__basic_index_bad_188:
    jsr __basic_bad_subscript
__basic_index_ok_187:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_189
    bne __basic_index_bad_190
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_189
    beq __basic_index_ok_189
__basic_index_bad_190:
    jsr __basic_bad_subscript
__basic_index_ok_189:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_O_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_O_
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    txa
    iny
    sta ($FB),y
    lda #<__basic_var_FC
    ldy #>__basic_var_FC
    jsr $BBA2
    ldx #<__basic_float_tmp_110
    ldy #>__basic_float_tmp_110
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_110
    ldy #>__basic_float_tmp_110
    jsr __basic_sub
    ldx #<__basic_var_FC
    ldy #>__basic_var_FC
    jsr $BBD4
__basic_line_3570:
    rts
__basic_line_4000:
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_193
    bne __basic_index_bad_194
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_193
    beq __basic_index_ok_193
__basic_index_bad_194:
    jsr __basic_bad_subscript
__basic_index_ok_193:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_195
    bne __basic_index_bad_196
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_195
    beq __basic_index_ok_195
__basic_index_bad_196:
    jsr __basic_bad_subscript
__basic_index_ok_195:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_D_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_D_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_111
    ldy #>__basic_float_tmp_111
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_111
    ldy #>__basic_float_tmp_111
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_191
    jmp __basic_if_skip_192
__basic_if_then_191:
    rts
__basic_if_skip_192:
__basic_line_4010:
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_199
    bne __basic_index_bad_200
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_199
    beq __basic_index_ok_199
__basic_index_bad_200:
    jsr __basic_bad_subscript
__basic_index_ok_199:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_201
    bne __basic_index_bad_202
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_201
    beq __basic_index_ok_201
__basic_index_bad_202:
    jsr __basic_bad_subscript
__basic_index_ok_201:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_O_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_O_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_112
    ldy #>__basic_float_tmp_112
    jsr $BBD4
    lda #<__basic_float_const_13
    ldy #>__basic_float_const_13
    jsr $BBA2
    lda #<__basic_float_tmp_112
    ldy #>__basic_float_tmp_112
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_197
    jmp __basic_if_skip_198
__basic_if_then_197:
    rts
__basic_if_skip_198:
__basic_line_4020:
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_205
    bne __basic_index_bad_206
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_205
    beq __basic_index_ok_205
__basic_index_bad_206:
    jsr __basic_bad_subscript
__basic_index_ok_205:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_207
    bne __basic_index_bad_208
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_207
    beq __basic_index_ok_207
__basic_index_bad_208:
    jsr __basic_bad_subscript
__basic_index_ok_207:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_M_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_M_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_113
    ldy #>__basic_float_tmp_113
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_113
    ldy #>__basic_float_tmp_113
    jsr __basic_cmp_ne
    lda $61
    bne __basic_if_then_203
    jmp __basic_if_skip_204
__basic_if_then_203:
    jmp __basic_line_4050
__basic_if_skip_204:
__basic_line_4030:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_var_GS
    ldy #>__basic_var_GS
    jsr $BBD4
__basic_line_4040:
    rts
__basic_line_4050:
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_QH
    ldy #>__basic_var_QH
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_QT
    ldy #>__basic_var_QT
    jsr $BBD4
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$03
    bcc __basic_index_ok_209
    bne __basic_index_bad_210
    lda __basic_index
    cmp #$83
    bcc __basic_index_ok_209
    beq __basic_index_ok_209
__basic_index_bad_210:
    jsr __basic_bad_subscript
__basic_index_ok_209:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_QX_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_QX_
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    txa
    iny
    sta ($FB),y
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$03
    bcc __basic_index_ok_211
    bne __basic_index_bad_212
    lda __basic_index
    cmp #$83
    bcc __basic_index_ok_211
    beq __basic_index_ok_211
__basic_index_bad_212:
    jsr __basic_bad_subscript
__basic_index_ok_211:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_QY_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_QY_
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    txa
    iny
    sta ($FB),y
    lda #<__basic_float_const_17
    ldy #>__basic_float_const_17
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_var_CY
    ldy #>__basic_var_CY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_213
    bne __basic_index_bad_214
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_213
    beq __basic_index_ok_213
__basic_index_bad_214:
    jsr __basic_bad_subscript
__basic_index_ok_213:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_CX
    ldy #>__basic_var_CX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_215
    bne __basic_index_bad_216
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_215
    beq __basic_index_ok_215
__basic_index_bad_216:
    jsr __basic_bad_subscript
__basic_index_ok_215:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_O_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_O_
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    txa
    iny
    sta ($FB),y
__basic_line_4060:
    lda #<__basic_var_QH
    ldy #>__basic_var_QH
    jsr $BBA2
    ldx #<__basic_float_tmp_114
    ldy #>__basic_float_tmp_114
    jsr $BBD4
    lda #<__basic_var_QT
    ldy #>__basic_var_QT
    jsr $BBA2
    lda #<__basic_float_tmp_114
    ldy #>__basic_float_tmp_114
    jsr __basic_cmp_gt
    lda $61
    bne __basic_if_then_217
    jmp __basic_if_skip_218
__basic_if_then_217:
    jmp __basic_line_4300
__basic_if_skip_218:
__basic_line_4070:
    lda #<__basic_var_QH
    ldy #>__basic_var_QH
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$03
    bcc __basic_index_ok_219
    bne __basic_index_bad_220
    lda __basic_index
    cmp #$83
    bcc __basic_index_ok_219
    beq __basic_index_ok_219
__basic_index_bad_220:
    jsr __basic_bad_subscript
__basic_index_ok_219:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_QX_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_QX_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_var_TX
    ldy #>__basic_var_TX
    jsr $BBD4
    lda #<__basic_var_QH
    ldy #>__basic_var_QH
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$03
    bcc __basic_index_ok_221
    bne __basic_index_bad_222
    lda __basic_index
    cmp #$83
    bcc __basic_index_ok_221
    beq __basic_index_ok_221
__basic_index_bad_222:
    jsr __basic_bad_subscript
__basic_index_ok_221:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_QY_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_QY_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_var_TY
    ldy #>__basic_var_TY
    jsr $BBD4
    lda #<__basic_var_QH
    ldy #>__basic_var_QH
    jsr $BBA2
    ldx #<__basic_float_tmp_115
    ldy #>__basic_float_tmp_115
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_115
    ldy #>__basic_float_tmp_115
    jsr __basic_add
    ldx #<__basic_var_QH
    ldy #>__basic_var_QH
    jsr $BBD4
__basic_line_4080:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_var_TY
    ldy #>__basic_var_TY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_223
    bne __basic_index_bad_224
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_223
    beq __basic_index_ok_223
__basic_index_bad_224:
    jsr __basic_bad_subscript
__basic_index_ok_223:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_TX
    ldy #>__basic_var_TX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_225
    bne __basic_index_bad_226
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_225
    beq __basic_index_ok_225
__basic_index_bad_226:
    jsr __basic_bad_subscript
__basic_index_ok_225:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_O_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_O_
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    txa
    iny
    sta ($FB),y
    lda #<__basic_var_OC
    ldy #>__basic_var_OC
    jsr $BBA2
    ldx #<__basic_float_tmp_116
    ldy #>__basic_float_tmp_116
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_116
    ldy #>__basic_float_tmp_116
    jsr __basic_add
    ldx #<__basic_var_OC
    ldy #>__basic_var_OC
    jsr $BBD4
    lda #<__basic_var_SC
    ldy #>__basic_var_SC
    jsr $BBA2
    ldx #<__basic_float_tmp_117
    ldy #>__basic_float_tmp_117
    jsr $BBD4
    lda #<__basic_float_const_9
    ldy #>__basic_float_const_9
    jsr $BBA2
    ldx #<__basic_float_tmp_118
    ldy #>__basic_float_tmp_118
    jsr $BBD4
    lda #<__basic_var_SF
    ldy #>__basic_var_SF
    jsr $BBA2
    lda #<__basic_float_tmp_118
    ldy #>__basic_float_tmp_118
    jsr __basic_mul
    lda #<__basic_float_tmp_117
    ldy #>__basic_float_tmp_117
    jsr __basic_add
    ldx #<__basic_var_SC
    ldy #>__basic_var_SC
    jsr $BBD4
__basic_line_4090:
    jsr __basic_line_5000
__basic_line_4100:
    lda #<__basic_var_NN
    ldy #>__basic_var_NN
    jsr $BBA2
    ldx #<__basic_float_tmp_119
    ldy #>__basic_float_tmp_119
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_119
    ldy #>__basic_float_tmp_119
    jsr __basic_cmp_gt
    lda $61
    bne __basic_if_then_227
    jmp __basic_if_skip_228
__basic_if_then_227:
    jmp __basic_line_4060
__basic_if_skip_228:
__basic_line_4110:
    lda #<__basic_float_const_29
    ldy #>__basic_float_const_29
    jsr $BBA2
    ldx #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_120
    ldy #>__basic_float_tmp_120
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_121
    ldy #>__basic_float_tmp_121
    jsr $BBD4
__basic_for_loop_229:
__basic_line_4120:
    lda #<__basic_float_const_29
    ldy #>__basic_float_const_29
    jsr $BBA2
    ldx #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_122
    ldy #>__basic_float_tmp_122
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_123
    ldy #>__basic_float_tmp_123
    jsr $BBD4
__basic_for_loop_230:
__basic_line_4130:
    lda #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBA2
    ldx #<__basic_float_tmp_125
    ldy #>__basic_float_tmp_125
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_125
    ldy #>__basic_float_tmp_125
    jsr __basic_cmp_eq
    ldx #<__basic_float_tmp_124
    ldy #>__basic_float_tmp_124
    jsr $BBD4
    lda #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBA2
    ldx #<__basic_float_tmp_126
    ldy #>__basic_float_tmp_126
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_126
    ldy #>__basic_float_tmp_126
    jsr __basic_cmp_eq
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_124
    ldy #>__basic_float_tmp_124
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_and
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_231
    jmp __basic_if_skip_232
__basic_if_then_231:
    jmp __basic_line_4220
__basic_if_skip_232:
__basic_line_4140:
    lda #<__basic_var_TX
    ldy #>__basic_var_TX
    jsr $BBA2
    ldx #<__basic_float_tmp_127
    ldy #>__basic_float_tmp_127
    jsr $BBD4
    lda #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBA2
    lda #<__basic_float_tmp_127
    ldy #>__basic_float_tmp_127
    jsr __basic_add
    ldx #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBD4
    lda #<__basic_var_TY
    ldy #>__basic_var_TY
    jsr $BBA2
    ldx #<__basic_float_tmp_128
    ldy #>__basic_float_tmp_128
    jsr $BBD4
    lda #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBA2
    lda #<__basic_float_tmp_128
    ldy #>__basic_float_tmp_128
    jsr __basic_add
    ldx #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBD4
__basic_line_4150:
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    ldx #<__basic_float_tmp_132
    ldy #>__basic_float_tmp_132
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_132
    ldy #>__basic_float_tmp_132
    jsr __basic_cmp_lt
    ldx #<__basic_float_tmp_131
    ldy #>__basic_float_tmp_131
    jsr $BBD4
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    ldx #<__basic_float_tmp_133
    ldy #>__basic_float_tmp_133
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_133
    ldy #>__basic_float_tmp_133
    jsr __basic_cmp_gt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_131
    ldy #>__basic_float_tmp_131
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_or
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_130
    ldy #>__basic_float_tmp_130
    jsr $BBD4
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    ldx #<__basic_float_tmp_134
    ldy #>__basic_float_tmp_134
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_134
    ldy #>__basic_float_tmp_134
    jsr __basic_cmp_lt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_130
    ldy #>__basic_float_tmp_130
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_or
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_129
    ldy #>__basic_float_tmp_129
    jsr $BBD4
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    ldx #<__basic_float_tmp_135
    ldy #>__basic_float_tmp_135
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_135
    ldy #>__basic_float_tmp_135
    jsr __basic_cmp_gt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_129
    ldy #>__basic_float_tmp_129
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_or
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_233
    jmp __basic_if_skip_234
__basic_if_then_233:
    jmp __basic_line_4220
__basic_if_skip_234:
__basic_line_4160:
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_237
    bne __basic_index_bad_238
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_237
    beq __basic_index_ok_237
__basic_index_bad_238:
    jsr __basic_bad_subscript
__basic_index_ok_237:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_239
    bne __basic_index_bad_240
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_239
    beq __basic_index_ok_239
__basic_index_bad_240:
    jsr __basic_bad_subscript
__basic_index_ok_239:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_M_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_M_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_136
    ldy #>__basic_float_tmp_136
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_136
    ldy #>__basic_float_tmp_136
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_235
    jmp __basic_if_skip_236
__basic_if_then_235:
    jmp __basic_line_4220
__basic_if_skip_236:
__basic_line_4170:
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_243
    bne __basic_index_bad_244
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_243
    beq __basic_index_ok_243
__basic_index_bad_244:
    jsr __basic_bad_subscript
__basic_index_ok_243:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_245
    bne __basic_index_bad_246
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_245
    beq __basic_index_ok_245
__basic_index_bad_246:
    jsr __basic_bad_subscript
__basic_index_ok_245:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_O_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_O_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_137
    ldy #>__basic_float_tmp_137
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_137
    ldy #>__basic_float_tmp_137
    jsr __basic_cmp_ne
    lda $61
    bne __basic_if_then_241
    jmp __basic_if_skip_242
__basic_if_then_241:
    jmp __basic_line_4220
__basic_if_skip_242:
__basic_line_4180:
    lda #<__basic_var_QT
    ldy #>__basic_var_QT
    jsr $BBA2
    ldx #<__basic_float_tmp_138
    ldy #>__basic_float_tmp_138
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_138
    ldy #>__basic_float_tmp_138
    jsr __basic_add
    ldx #<__basic_var_QT
    ldy #>__basic_var_QT
    jsr $BBD4
__basic_line_4190:
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_var_QT
    ldy #>__basic_var_QT
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$03
    bcc __basic_index_ok_247
    bne __basic_index_bad_248
    lda __basic_index
    cmp #$83
    bcc __basic_index_ok_247
    beq __basic_index_ok_247
__basic_index_bad_248:
    jsr __basic_bad_subscript
__basic_index_ok_247:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_QX_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_QX_
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    txa
    iny
    sta ($FB),y
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_var_QT
    ldy #>__basic_var_QT
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$03
    bcc __basic_index_ok_249
    bne __basic_index_bad_250
    lda __basic_index
    cmp #$83
    bcc __basic_index_ok_249
    beq __basic_index_ok_249
__basic_index_bad_250:
    jsr __basic_bad_subscript
__basic_index_ok_249:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_QY_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_QY_
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    txa
    iny
    sta ($FB),y
    lda #<__basic_float_const_17
    ldy #>__basic_float_const_17
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_251
    bne __basic_index_bad_252
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_251
    beq __basic_index_ok_251
__basic_index_bad_252:
    jsr __basic_bad_subscript
__basic_index_ok_251:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_253
    bne __basic_index_bad_254
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_253
    beq __basic_index_ok_253
__basic_index_bad_254:
    jsr __basic_bad_subscript
__basic_index_ok_253:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_O_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_O_
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    txa
    iny
    sta ($FB),y
__basic_line_4220:
    lda #<__basic_float_tmp_123
    ldy #>__basic_float_tmp_123
    jsr $BBA2
    lda #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr __basic_add
    ldx #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBD4
    lda #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBA2
    lda #<__basic_float_tmp_122
    ldy #>__basic_float_tmp_122
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_123
    ldy #>__basic_float_tmp_123
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_255
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_256
    jmp __basic_for_loop_230
__basic_for_negative_255:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_256
    jmp __basic_for_loop_230
__basic_for_done_256:
__basic_line_4230:
    lda #<__basic_float_tmp_121
    ldy #>__basic_float_tmp_121
    jsr $BBA2
    lda #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr __basic_add
    ldx #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBD4
    lda #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBA2
    lda #<__basic_float_tmp_120
    ldy #>__basic_float_tmp_120
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_121
    ldy #>__basic_float_tmp_121
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_257
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_258
    jmp __basic_for_loop_229
__basic_for_negative_257:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_258
    jmp __basic_for_loop_229
__basic_for_done_258:
__basic_line_4240:
    jmp __basic_line_4060
__basic_line_4300:
    jsr __basic_line_6000
__basic_line_4310:
    lda #<__basic_var_OC
    ldy #>__basic_var_OC
    jsr $BBA2
    ldx #<__basic_float_tmp_139
    ldy #>__basic_float_tmp_139
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    ldx #<__basic_float_tmp_141
    ldy #>__basic_float_tmp_141
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_141
    ldy #>__basic_float_tmp_141
    jsr __basic_mul
    ldx #<__basic_float_tmp_140
    ldy #>__basic_float_tmp_140
    jsr $BBD4
    lda #<__basic_var_MC
    ldy #>__basic_var_MC
    jsr $BBA2
    lda #<__basic_float_tmp_140
    ldy #>__basic_float_tmp_140
    jsr __basic_sub
    lda #<__basic_float_tmp_139
    ldy #>__basic_float_tmp_139
    jsr __basic_cmp_lt
    lda $61
    bne __basic_if_then_259
    jmp __basic_if_skip_260
__basic_if_then_259:
    rts
__basic_if_skip_260:
__basic_line_4320:
    lda #<__basic_float_const_13
    ldy #>__basic_float_const_13
    jsr $BBA2
    ldx #<__basic_var_GS
    ldy #>__basic_var_GS
    jsr $BBD4
__basic_line_4330:
    rts
__basic_line_5000:
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_NN
    ldy #>__basic_var_NN
    jsr $BBD4
__basic_line_5010:
    lda #<__basic_float_const_29
    ldy #>__basic_float_const_29
    jsr $BBA2
    ldx #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_142
    ldy #>__basic_float_tmp_142
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_143
    ldy #>__basic_float_tmp_143
    jsr $BBD4
__basic_for_loop_261:
__basic_line_5020:
    lda #<__basic_float_const_29
    ldy #>__basic_float_const_29
    jsr $BBA2
    ldx #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_144
    ldy #>__basic_float_tmp_144
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_145
    ldy #>__basic_float_tmp_145
    jsr $BBD4
__basic_for_loop_262:
__basic_line_5030:
    lda #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBA2
    ldx #<__basic_float_tmp_147
    ldy #>__basic_float_tmp_147
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_147
    ldy #>__basic_float_tmp_147
    jsr __basic_cmp_eq
    ldx #<__basic_float_tmp_146
    ldy #>__basic_float_tmp_146
    jsr $BBD4
    lda #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBA2
    ldx #<__basic_float_tmp_148
    ldy #>__basic_float_tmp_148
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_148
    ldy #>__basic_float_tmp_148
    jsr __basic_cmp_eq
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_146
    ldy #>__basic_float_tmp_146
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_and
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_263
    jmp __basic_if_skip_264
__basic_if_then_263:
    jmp __basic_line_5080
__basic_if_skip_264:
__basic_line_5040:
    lda #<__basic_var_TX
    ldy #>__basic_var_TX
    jsr $BBA2
    ldx #<__basic_float_tmp_149
    ldy #>__basic_float_tmp_149
    jsr $BBD4
    lda #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBA2
    lda #<__basic_float_tmp_149
    ldy #>__basic_float_tmp_149
    jsr __basic_add
    ldx #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBD4
    lda #<__basic_var_TY
    ldy #>__basic_var_TY
    jsr $BBA2
    ldx #<__basic_float_tmp_150
    ldy #>__basic_float_tmp_150
    jsr $BBD4
    lda #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBA2
    lda #<__basic_float_tmp_150
    ldy #>__basic_float_tmp_150
    jsr __basic_add
    ldx #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBD4
__basic_line_5050:
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    ldx #<__basic_float_tmp_154
    ldy #>__basic_float_tmp_154
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_154
    ldy #>__basic_float_tmp_154
    jsr __basic_cmp_lt
    ldx #<__basic_float_tmp_153
    ldy #>__basic_float_tmp_153
    jsr $BBD4
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    ldx #<__basic_float_tmp_155
    ldy #>__basic_float_tmp_155
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_155
    ldy #>__basic_float_tmp_155
    jsr __basic_cmp_gt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_153
    ldy #>__basic_float_tmp_153
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_or
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_152
    ldy #>__basic_float_tmp_152
    jsr $BBD4
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    ldx #<__basic_float_tmp_156
    ldy #>__basic_float_tmp_156
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_156
    ldy #>__basic_float_tmp_156
    jsr __basic_cmp_lt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_152
    ldy #>__basic_float_tmp_152
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_or
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_151
    ldy #>__basic_float_tmp_151
    jsr $BBD4
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    ldx #<__basic_float_tmp_157
    ldy #>__basic_float_tmp_157
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_157
    ldy #>__basic_float_tmp_157
    jsr __basic_cmp_gt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_151
    ldy #>__basic_float_tmp_151
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_or
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_265
    jmp __basic_if_skip_266
__basic_if_then_265:
    jmp __basic_line_5080
__basic_if_skip_266:
__basic_line_5060:
    lda #<__basic_var_NN
    ldy #>__basic_var_NN
    jsr $BBA2
    ldx #<__basic_float_tmp_158
    ldy #>__basic_float_tmp_158
    jsr $BBD4
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_267
    bne __basic_index_bad_268
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_267
    beq __basic_index_ok_267
__basic_index_bad_268:
    jsr __basic_bad_subscript
__basic_index_ok_267:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_269
    bne __basic_index_bad_270
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_269
    beq __basic_index_ok_269
__basic_index_bad_270:
    jsr __basic_bad_subscript
__basic_index_ok_269:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_M_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_M_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    lda #<__basic_float_tmp_158
    ldy #>__basic_float_tmp_158
    jsr __basic_add
    ldx #<__basic_var_NN
    ldy #>__basic_var_NN
    jsr $BBD4
__basic_line_5080:
    lda #<__basic_float_tmp_145
    ldy #>__basic_float_tmp_145
    jsr $BBA2
    lda #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr __basic_add
    ldx #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBD4
    lda #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBA2
    lda #<__basic_float_tmp_144
    ldy #>__basic_float_tmp_144
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_145
    ldy #>__basic_float_tmp_145
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_271
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_272
    jmp __basic_for_loop_262
__basic_for_negative_271:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_272
    jmp __basic_for_loop_262
__basic_for_done_272:
__basic_line_5090:
    lda #<__basic_float_tmp_143
    ldy #>__basic_float_tmp_143
    jsr $BBA2
    lda #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr __basic_add
    ldx #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBD4
    lda #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBA2
    lda #<__basic_float_tmp_142
    ldy #>__basic_float_tmp_142
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_143
    ldy #>__basic_float_tmp_143
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_273
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_274
    jmp __basic_for_loop_261
__basic_for_negative_273:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_274
    jmp __basic_for_loop_261
__basic_for_done_274:
__basic_line_5100:
    rts
__basic_line_6000:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    ldx #<__basic_float_tmp_159
    ldy #>__basic_float_tmp_159
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_160
    ldy #>__basic_float_tmp_160
    jsr $BBD4
__basic_for_loop_275:
__basic_line_6010:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    ldx #<__basic_float_tmp_161
    ldy #>__basic_float_tmp_161
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_162
    ldy #>__basic_float_tmp_162
    jsr $BBD4
__basic_for_loop_276:
__basic_line_6020:
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_279
    bne __basic_index_bad_280
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_279
    beq __basic_index_ok_279
__basic_index_bad_280:
    jsr __basic_bad_subscript
__basic_index_ok_279:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_281
    bne __basic_index_bad_282
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_281
    beq __basic_index_ok_281
__basic_index_bad_282:
    jsr __basic_bad_subscript
__basic_index_ok_281:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_M_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_M_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_163
    ldy #>__basic_float_tmp_163
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_163
    ldy #>__basic_float_tmp_163
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_277
    jmp __basic_if_skip_278
__basic_if_then_277:
    jmp __basic_line_6200
__basic_if_skip_278:
__basic_line_6030:
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_285
    bne __basic_index_bad_286
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_285
    beq __basic_index_ok_285
__basic_index_bad_286:
    jsr __basic_bad_subscript
__basic_index_ok_285:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_287
    bne __basic_index_bad_288
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_287
    beq __basic_index_ok_287
__basic_index_bad_288:
    jsr __basic_bad_subscript
__basic_index_ok_287:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_D_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_D_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_164
    ldy #>__basic_float_tmp_164
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_164
    ldy #>__basic_float_tmp_164
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_283
    jmp __basic_if_skip_284
__basic_if_then_283:
    jmp __basic_line_6200
__basic_if_skip_284:
__basic_line_6040:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_var_OK
    ldy #>__basic_var_OK
    jsr $BBD4
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    ldx #<__basic_var_TY
    ldy #>__basic_var_TY
    jsr $BBD4
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    ldx #<__basic_var_TX
    ldy #>__basic_var_TX
    jsr $BBD4
__basic_line_6050:
    lda #<__basic_float_const_29
    ldy #>__basic_float_const_29
    jsr $BBA2
    ldx #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_165
    ldy #>__basic_float_tmp_165
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_166
    ldy #>__basic_float_tmp_166
    jsr $BBD4
__basic_for_loop_289:
__basic_line_6060:
    lda #<__basic_float_const_29
    ldy #>__basic_float_const_29
    jsr $BBA2
    ldx #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_167
    ldy #>__basic_float_tmp_167
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_168
    ldy #>__basic_float_tmp_168
    jsr $BBD4
__basic_for_loop_290:
__basic_line_6070:
    lda #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBA2
    ldx #<__basic_float_tmp_170
    ldy #>__basic_float_tmp_170
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_170
    ldy #>__basic_float_tmp_170
    jsr __basic_cmp_eq
    ldx #<__basic_float_tmp_169
    ldy #>__basic_float_tmp_169
    jsr $BBD4
    lda #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBA2
    ldx #<__basic_float_tmp_171
    ldy #>__basic_float_tmp_171
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_171
    ldy #>__basic_float_tmp_171
    jsr __basic_cmp_eq
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_169
    ldy #>__basic_float_tmp_169
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_and
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_291
    jmp __basic_if_skip_292
__basic_if_then_291:
    jmp __basic_line_6150
__basic_if_skip_292:
__basic_line_6080:
    lda #<__basic_var_TX
    ldy #>__basic_var_TX
    jsr $BBA2
    ldx #<__basic_float_tmp_172
    ldy #>__basic_float_tmp_172
    jsr $BBD4
    lda #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBA2
    lda #<__basic_float_tmp_172
    ldy #>__basic_float_tmp_172
    jsr __basic_add
    ldx #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBD4
    lda #<__basic_var_TY
    ldy #>__basic_var_TY
    jsr $BBA2
    ldx #<__basic_float_tmp_173
    ldy #>__basic_float_tmp_173
    jsr $BBD4
    lda #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBA2
    lda #<__basic_float_tmp_173
    ldy #>__basic_float_tmp_173
    jsr __basic_add
    ldx #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBD4
__basic_line_6090:
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    ldx #<__basic_float_tmp_177
    ldy #>__basic_float_tmp_177
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_177
    ldy #>__basic_float_tmp_177
    jsr __basic_cmp_lt
    ldx #<__basic_float_tmp_176
    ldy #>__basic_float_tmp_176
    jsr $BBD4
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    ldx #<__basic_float_tmp_178
    ldy #>__basic_float_tmp_178
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_178
    ldy #>__basic_float_tmp_178
    jsr __basic_cmp_gt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_176
    ldy #>__basic_float_tmp_176
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_or
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_175
    ldy #>__basic_float_tmp_175
    jsr $BBD4
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    ldx #<__basic_float_tmp_179
    ldy #>__basic_float_tmp_179
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_179
    ldy #>__basic_float_tmp_179
    jsr __basic_cmp_lt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_175
    ldy #>__basic_float_tmp_175
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_or
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_174
    ldy #>__basic_float_tmp_174
    jsr $BBD4
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    ldx #<__basic_float_tmp_180
    ldy #>__basic_float_tmp_180
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_180
    ldy #>__basic_float_tmp_180
    jsr __basic_cmp_gt
    jsr __basic_fac_to_int
    sta __basic_int_right
    stx __basic_int_right+1
    lda #<__basic_float_tmp_174
    ldy #>__basic_float_tmp_174
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_int_left
    stx __basic_int_left+1
    jsr __basic_int_or
    jsr __basic_int_to_fac
    lda $61
    bne __basic_if_then_293
    jmp __basic_if_skip_294
__basic_if_then_293:
    jmp __basic_line_6150
__basic_if_skip_294:
__basic_line_6100:
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_297
    bne __basic_index_bad_298
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_297
    beq __basic_index_ok_297
__basic_index_bad_298:
    jsr __basic_bad_subscript
__basic_index_ok_297:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_299
    bne __basic_index_bad_300
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_299
    beq __basic_index_ok_299
__basic_index_bad_300:
    jsr __basic_bad_subscript
__basic_index_ok_299:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_M_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_M_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_181
    ldy #>__basic_float_tmp_181
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_181
    ldy #>__basic_float_tmp_181
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_295
    jmp __basic_if_skip_296
__basic_if_then_295:
    jmp __basic_line_6150
__basic_if_skip_296:
__basic_line_6110:
    lda #<__basic_var_NY
    ldy #>__basic_var_NY
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_303
    bne __basic_index_bad_304
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_303
    beq __basic_index_ok_303
__basic_index_bad_304:
    jsr __basic_bad_subscript
__basic_index_ok_303:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_NX
    ldy #>__basic_var_NX
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_305
    bne __basic_index_bad_306
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_305
    beq __basic_index_ok_305
__basic_index_bad_306:
    jsr __basic_bad_subscript
__basic_index_ok_305:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_O_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_O_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_182
    ldy #>__basic_float_tmp_182
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_182
    ldy #>__basic_float_tmp_182
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_301
    jmp __basic_if_skip_302
__basic_if_then_301:
    jmp __basic_line_6150
__basic_if_skip_302:
__basic_line_6120:
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_OK
    ldy #>__basic_var_OK
    jsr $BBD4
__basic_line_6150:
    lda #<__basic_float_tmp_168
    ldy #>__basic_float_tmp_168
    jsr $BBA2
    lda #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr __basic_add
    ldx #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBD4
    lda #<__basic_var_DX
    ldy #>__basic_var_DX
    jsr $BBA2
    lda #<__basic_float_tmp_167
    ldy #>__basic_float_tmp_167
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_168
    ldy #>__basic_float_tmp_168
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_307
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_308
    jmp __basic_for_loop_290
__basic_for_negative_307:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_308
    jmp __basic_for_loop_290
__basic_for_done_308:
__basic_line_6160:
    lda #<__basic_float_tmp_166
    ldy #>__basic_float_tmp_166
    jsr $BBA2
    lda #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr __basic_add
    ldx #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBD4
    lda #<__basic_var_DY
    ldy #>__basic_var_DY
    jsr $BBA2
    lda #<__basic_float_tmp_165
    ldy #>__basic_float_tmp_165
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_166
    ldy #>__basic_float_tmp_166
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_309
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_310
    jmp __basic_for_loop_289
__basic_for_negative_309:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_310
    jmp __basic_for_loop_289
__basic_for_done_310:
__basic_line_6170:
    lda #<__basic_var_OK
    ldy #>__basic_var_OK
    jsr $BBA2
    ldx #<__basic_float_tmp_183
    ldy #>__basic_float_tmp_183
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_183
    ldy #>__basic_float_tmp_183
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_311
    jmp __basic_if_skip_312
__basic_if_then_311:
    jmp __basic_line_6200
__basic_if_skip_312:
__basic_line_6180:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_313
    bne __basic_index_bad_314
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_313
    beq __basic_index_ok_313
__basic_index_bad_314:
    jsr __basic_bad_subscript
__basic_index_ok_313:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_315
    bne __basic_index_bad_316
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_315
    beq __basic_index_ok_315
__basic_index_bad_316:
    jsr __basic_bad_subscript
__basic_index_ok_315:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_D_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_D_
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    txa
    iny
    sta ($FB),y
    lda #<__basic_var_DC
    ldy #>__basic_var_DC
    jsr $BBA2
    ldx #<__basic_float_tmp_184
    ldy #>__basic_float_tmp_184
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_184
    ldy #>__basic_float_tmp_184
    jsr __basic_add
    ldx #<__basic_var_DC
    ldy #>__basic_var_DC
    jsr $BBD4
    lda #<__basic_var_SC
    ldy #>__basic_var_SC
    jsr $BBA2
    ldx #<__basic_float_tmp_185
    ldy #>__basic_float_tmp_185
    jsr $BBD4
    lda #<__basic_float_const_10
    ldy #>__basic_float_const_10
    jsr $BBA2
    ldx #<__basic_float_tmp_186
    ldy #>__basic_float_tmp_186
    jsr $BBD4
    lda #<__basic_var_SF
    ldy #>__basic_var_SF
    jsr $BBA2
    lda #<__basic_float_tmp_186
    ldy #>__basic_float_tmp_186
    jsr __basic_mul
    lda #<__basic_float_tmp_185
    ldy #>__basic_float_tmp_185
    jsr __basic_add
    ldx #<__basic_var_SC
    ldy #>__basic_var_SC
    jsr $BBD4
__basic_line_6200:
    lda #<__basic_float_tmp_162
    ldy #>__basic_float_tmp_162
    jsr $BBA2
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr __basic_add
    ldx #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBD4
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    lda #<__basic_float_tmp_161
    ldy #>__basic_float_tmp_161
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_162
    ldy #>__basic_float_tmp_162
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_317
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_318
    jmp __basic_for_loop_276
__basic_for_negative_317:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_318
    jmp __basic_for_loop_276
__basic_for_done_318:
__basic_line_6210:
    lda #<__basic_float_tmp_160
    ldy #>__basic_float_tmp_160
    jsr $BBA2
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr __basic_add
    ldx #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBD4
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    lda #<__basic_float_tmp_159
    ldy #>__basic_float_tmp_159
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_160
    ldy #>__basic_float_tmp_160
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_319
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_320
    jmp __basic_for_loop_275
__basic_for_negative_319:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_320
    jmp __basic_for_loop_275
__basic_for_done_320:
__basic_line_6220:
    rts
__basic_line_8000:
    jsr __basic_line_1900
    jsr __basic_line_2000
__basic_line_8010:
    jsr __basic_newline
__basic_line_8020:
    lda #<__basic_string_321
    ldy #>__basic_string_321
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_8030:
    lda #<__basic_string_111
    ldy #>__basic_string_111
    jsr __basic_print_string
    lda #<__basic_var_ET
    ldy #>__basic_var_ET
    jsr $BBA2
    jsr __basic_print_float
    lda #<__basic_string_322
    ldy #>__basic_string_322
    jsr __basic_print_string
    lda #<__basic_var_SC
    ldy #>__basic_var_SC
    jsr $BBA2
    jsr __basic_print_float
    jsr __basic_newline
__basic_line_8040:
    lda #<__basic_string_323
    ldy #>__basic_string_323
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_8050:
    jsr $FFE4
    sta __basic_get_char
    lda __basic_get_char
    beq __basic_get_empty_324
    sta __basic_string_term+1
    lda #$01
    sta __basic_string_term
    jmp __basic_get_done_325
__basic_get_empty_324:
    lda #$00
    sta __basic_string_term
__basic_get_done_325:
    lda #<__basic_str_K_
    sta $FB
    lda #>__basic_str_K_
    sta $FC
    lda #<__basic_string_term
    sta $FD
    lda #>__basic_string_term
    sta $FE
    jsr __basic_string_copy
    lda #<__basic_string_left
    sta $FB
    lda #>__basic_string_left
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_str_K_
    sta $FD
    lda #>__basic_str_K_
    sta $FE
    lda #<__basic_string_left
    sta $FB
    lda #>__basic_string_left
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_right
    sta $FB
    lda #>__basic_string_right
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_12
    sta $FD
    lda #>__basic_string_12
    sta $FE
    lda #<__basic_string_right
    sta $FB
    lda #>__basic_string_right
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_left
    sta $FB
    lda #>__basic_string_left
    sta $FC
    lda #<__basic_string_right
    sta $FD
    lda #>__basic_string_right
    sta $FE
    jsr __basic_string_compare
    beq __basic_str_cmp_true_328
    lda #$00
    jmp __basic_str_cmp_done_329
__basic_str_cmp_true_328:
    lda #$01
__basic_str_cmp_done_329:
    cmp #$00
    bne __basic_if_then_326
    jmp __basic_if_skip_327
__basic_if_then_326:
    jmp __basic_line_8050
__basic_if_skip_327:
__basic_line_8055:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_str_K_
    sta $FD
    lda #>__basic_str_K_
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda __basic_string_expr
    beq __basic_asc_empty_330
    lda __basic_string_expr+1
    ldx #$00
    jmp __basic_asc_done_331
__basic_asc_empty_330:
    lda #$00
    tax
__basic_asc_done_331:
    jsr __basic_int_to_fac
    ldx #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBD4
__basic_line_8060:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_187
    ldy #>__basic_float_tmp_187
    jsr $BBD4
    lda #<__basic_float_const_43
    ldy #>__basic_float_const_43
    jsr $BBA2
    lda #<__basic_float_tmp_187
    ldy #>__basic_float_tmp_187
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_332
    jmp __basic_if_skip_333
__basic_if_then_332:
    jmp __basic_line_20
__basic_if_skip_333:
__basic_line_8070:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_188
    ldy #>__basic_float_tmp_188
    jsr $BBD4
    lda #<__basic_float_const_30
    ldy #>__basic_float_const_30
    jsr $BBA2
    lda #<__basic_float_tmp_188
    ldy #>__basic_float_tmp_188
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_334
    jmp __basic_if_skip_335
__basic_if_then_334:
    jmp __basic_line_8900
__basic_if_skip_335:
__basic_line_8080:
    jmp __basic_line_8050
__basic_line_8500:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    ldx #<__basic_float_tmp_189
    ldy #>__basic_float_tmp_189
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_190
    ldy #>__basic_float_tmp_190
    jsr $BBD4
__basic_for_loop_336:
__basic_line_8510:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    ldx #<__basic_float_tmp_191
    ldy #>__basic_float_tmp_191
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_192
    ldy #>__basic_float_tmp_192
    jsr $BBD4
__basic_for_loop_337:
__basic_line_8520:
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_340
    bne __basic_index_bad_341
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_340
    beq __basic_index_ok_340
__basic_index_bad_341:
    jsr __basic_bad_subscript
__basic_index_ok_340:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_342
    bne __basic_index_bad_343
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_342
    beq __basic_index_ok_342
__basic_index_bad_343:
    jsr __basic_bad_subscript
__basic_index_ok_342:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_M_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_M_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    ldx #<__basic_float_tmp_193
    ldy #>__basic_float_tmp_193
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    lda #<__basic_float_tmp_193
    ldy #>__basic_float_tmp_193
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_338
    jmp __basic_if_skip_339
__basic_if_then_338:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_344
    bne __basic_index_bad_345
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_344
    beq __basic_index_ok_344
__basic_index_bad_345:
    jsr __basic_bad_subscript
__basic_index_ok_344:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$1F
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_346
    bne __basic_index_bad_347
    lda __basic_index
    cmp #$1E
    bcc __basic_index_ok_346
    beq __basic_index_ok_346
__basic_index_bad_347:
    jsr __basic_bad_subscript
__basic_index_ok_346:
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_add
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$02
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_D_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_D_
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    jsr __basic_fac_to_int
    ldy #$00
    sta ($FB),y
    txa
    iny
    sta ($FB),y
__basic_if_skip_339:
__basic_line_8530:
    lda #<__basic_float_tmp_192
    ldy #>__basic_float_tmp_192
    jsr $BBA2
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr __basic_add
    ldx #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBD4
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    lda #<__basic_float_tmp_191
    ldy #>__basic_float_tmp_191
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_192
    ldy #>__basic_float_tmp_192
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_348
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_349
    jmp __basic_for_loop_337
__basic_for_negative_348:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_349
    jmp __basic_for_loop_337
__basic_for_done_349:
__basic_line_8540:
    lda #<__basic_float_tmp_190
    ldy #>__basic_float_tmp_190
    jsr $BBA2
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr __basic_add
    ldx #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBD4
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    lda #<__basic_float_tmp_189
    ldy #>__basic_float_tmp_189
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_190
    ldy #>__basic_float_tmp_190
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_350
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_351
    jmp __basic_for_loop_336
__basic_for_negative_350:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_351
    jmp __basic_for_loop_336
__basic_for_done_351:
__basic_line_8550:
    lda #<__basic_var_SC
    ldy #>__basic_var_SC
    jsr $BBA2
    ldx #<__basic_float_tmp_195
    ldy #>__basic_float_tmp_195
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    ldx #<__basic_float_tmp_197
    ldy #>__basic_float_tmp_197
    jsr $BBD4
    lda #<__basic_var_SZ
    ldy #>__basic_var_SZ
    jsr $BBA2
    lda #<__basic_float_tmp_197
    ldy #>__basic_float_tmp_197
    jsr __basic_mul
    ldx #<__basic_float_tmp_196
    ldy #>__basic_float_tmp_196
    jsr $BBD4
    lda #<__basic_var_SF
    ldy #>__basic_var_SF
    jsr $BBA2
    lda #<__basic_float_tmp_196
    ldy #>__basic_float_tmp_196
    jsr __basic_mul
    lda #<__basic_float_tmp_195
    ldy #>__basic_float_tmp_195
    jsr __basic_add
    ldx #<__basic_float_tmp_194
    ldy #>__basic_float_tmp_194
    jsr $BBD4
    lda #<__basic_float_const_44
    ldy #>__basic_float_const_44
    jsr $BBA2
    ldx #<__basic_float_tmp_199
    ldy #>__basic_float_tmp_199
    jsr $BBD4
    lda #<__basic_var_ET
    ldy #>__basic_var_ET
    jsr $BBA2
    lda #<__basic_float_tmp_199
    ldy #>__basic_float_tmp_199
    jsr __basic_sub
    ldx #<__basic_float_tmp_198
    ldy #>__basic_float_tmp_198
    jsr $BBD4
    lda #<__basic_var_SF
    ldy #>__basic_var_SF
    jsr $BBA2
    lda #<__basic_float_tmp_198
    ldy #>__basic_float_tmp_198
    jsr __basic_mul
    jsr $BCCC
    lda #<__basic_float_tmp_194
    ldy #>__basic_float_tmp_194
    jsr __basic_add
    ldx #<__basic_var_SC
    ldy #>__basic_var_SC
    jsr $BBD4
__basic_line_8560:
    lda #<__basic_var_SC
    ldy #>__basic_var_SC
    jsr $BBA2
    ldx #<__basic_float_tmp_200
    ldy #>__basic_float_tmp_200
    jsr $BBD4
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    lda #<__basic_float_tmp_200
    ldy #>__basic_float_tmp_200
    jsr __basic_cmp_lt
    lda $61
    bne __basic_if_then_352
    jmp __basic_if_skip_353
__basic_if_then_352:
    lda #<__basic_float_const_1
    ldy #>__basic_float_const_1
    jsr $BBA2
    ldx #<__basic_var_SC
    ldy #>__basic_var_SC
    jsr $BBD4
__basic_if_skip_353:
__basic_line_8570:
    jsr __basic_line_2000
__basic_line_8580:
    jsr __basic_newline
__basic_line_8590:
    lda #<__basic_string_354
    ldy #>__basic_string_354
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_8600:
    lda #<__basic_string_111
    ldy #>__basic_string_111
    jsr __basic_print_string
    lda #<__basic_var_ET
    ldy #>__basic_var_ET
    jsr $BBA2
    jsr __basic_print_float
    lda #<__basic_string_322
    ldy #>__basic_string_322
    jsr __basic_print_string
    lda #<__basic_var_SC
    ldy #>__basic_var_SC
    jsr $BBA2
    jsr __basic_print_float
    jsr __basic_newline
__basic_line_8610:
    lda #<__basic_string_323
    ldy #>__basic_string_323
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_8620:
    jsr $FFE4
    sta __basic_get_char
    lda __basic_get_char
    beq __basic_get_empty_355
    sta __basic_string_term+1
    lda #$01
    sta __basic_string_term
    jmp __basic_get_done_356
__basic_get_empty_355:
    lda #$00
    sta __basic_string_term
__basic_get_done_356:
    lda #<__basic_str_K_
    sta $FB
    lda #>__basic_str_K_
    sta $FC
    lda #<__basic_string_term
    sta $FD
    lda #>__basic_string_term
    sta $FE
    jsr __basic_string_copy
    lda #<__basic_string_left
    sta $FB
    lda #>__basic_string_left
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_str_K_
    sta $FD
    lda #>__basic_str_K_
    sta $FE
    lda #<__basic_string_left
    sta $FB
    lda #>__basic_string_left
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_right
    sta $FB
    lda #>__basic_string_right
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_12
    sta $FD
    lda #>__basic_string_12
    sta $FE
    lda #<__basic_string_right
    sta $FB
    lda #>__basic_string_right
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_left
    sta $FB
    lda #>__basic_string_left
    sta $FC
    lda #<__basic_string_right
    sta $FD
    lda #>__basic_string_right
    sta $FE
    jsr __basic_string_compare
    beq __basic_str_cmp_true_359
    lda #$00
    jmp __basic_str_cmp_done_360
__basic_str_cmp_true_359:
    lda #$01
__basic_str_cmp_done_360:
    cmp #$00
    bne __basic_if_then_357
    jmp __basic_if_skip_358
__basic_if_then_357:
    jmp __basic_line_8620
__basic_if_skip_358:
__basic_line_8625:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_str_K_
    sta $FD
    lda #>__basic_str_K_
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda __basic_string_expr
    beq __basic_asc_empty_361
    lda __basic_string_expr+1
    ldx #$00
    jmp __basic_asc_done_362
__basic_asc_empty_361:
    lda #$00
    tax
__basic_asc_done_362:
    jsr __basic_int_to_fac
    ldx #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBD4
__basic_line_8630:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_201
    ldy #>__basic_float_tmp_201
    jsr $BBD4
    lda #<__basic_float_const_43
    ldy #>__basic_float_const_43
    jsr $BBA2
    lda #<__basic_float_tmp_201
    ldy #>__basic_float_tmp_201
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_363
    jmp __basic_if_skip_364
__basic_if_then_363:
    jmp __basic_line_20
__basic_if_skip_364:
__basic_line_8640:
    lda #<__basic_var_KC
    ldy #>__basic_var_KC
    jsr $BBA2
    ldx #<__basic_float_tmp_202
    ldy #>__basic_float_tmp_202
    jsr $BBD4
    lda #<__basic_float_const_30
    ldy #>__basic_float_const_30
    jsr $BBA2
    lda #<__basic_float_tmp_202
    ldy #>__basic_float_tmp_202
    jsr __basic_cmp_eq
    lda $61
    bne __basic_if_then_365
    jmp __basic_if_skip_366
__basic_if_then_365:
    jmp __basic_line_8900
__basic_if_skip_366:
__basic_line_8650:
    jmp __basic_line_8620
__basic_line_8900:
    lda #<__basic_float_const_5
    ldy #>__basic_float_const_5
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_string_term+1
    lda #$01
    sta __basic_string_term
    lda #<__basic_string_term
    ldy #>__basic_string_term
    jsr __basic_print_string
    lda #<__basic_string_367
    ldy #>__basic_string_367
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_8910:
    rts
__basic_program_end:
    jsr $FFCC
    rts

; ---- C64 BASIC Fließkomma-/String-/I/O-Runtime --------------------
; C64-CBSS: nicht im PRG gespeicherter, beim Start genullter RAM
__basic_init_cbss:
    lda #<__basic_cbss_start
    sta $FB
    lda #>__basic_cbss_start
    sta $FC
    lda #$00
    ldx #>(__basic_cbss_end-__basic_cbss_start)
    beq __basic_init_cbss_remainder
__basic_init_cbss_page:
    ldy #$00
__basic_init_cbss_page_loop:
    sta ($FB),y
    iny
    bne __basic_init_cbss_page_loop
    inc $FC
    dex
    bne __basic_init_cbss_page
__basic_init_cbss_remainder:
    ldy #$00
__basic_init_cbss_remainder_loop:
    cpy #<(__basic_cbss_end-__basic_cbss_start)
    beq __basic_init_cbss_done
    sta ($FB),y
    iny
    bne __basic_init_cbss_remainder_loop
__basic_init_cbss_done:
    rts

__basic_newline:
    lda #$0D
    jmp $FFD2

__basic_print_string:
    sta $FB
    sty $FC
    ldy #$00
    lda ($FB),y
    tax
    beq __basic_print_string_done
    inc $FB
    bne __basic_print_string_ptr_ok
    inc $FC
__basic_print_string_ptr_ok:
    ldy #$00
__basic_print_string_loop:
    lda ($FB),y
    jsr $FFD2
    iny
    dex
    bne __basic_print_string_loop
__basic_print_string_done:
    rts

__basic_print_z:
    sta $FB
    sty $FC
    ldy #$00
__basic_print_z_loop:
    lda ($FB),y
    beq __basic_print_z_done
    jsr $FFD2
    iny
    bne __basic_print_z_loop
__basic_print_z_done:
    rts

__basic_print_float:
    jsr $BDDD
    jmp __basic_print_z

__basic_float_to_string_term:
    jsr $BDDD
    sta $FD
    sty $FE
    ldx #$00
    ldy #$00
__basic_float_to_string_loop:
    lda ($FD),y
    beq __basic_float_to_string_done
    sta __basic_string_term+1,x
    inx
    iny
    cpx #$FF
    bne __basic_float_to_string_loop
__basic_float_to_string_done:
    stx __basic_string_term
    rts

; FAC-/Integer-Konvertierung
__basic_fac_to_int:
    jsr $B1AA
    tax
    tya
    rts
__basic_int_to_fac:
    tay
    txa
    jmp $B391

; Kompatible Arithmetik-Helfernamen; linker Operand liegt im Speicher A/Y
__basic_add:
    jmp $B867
__basic_sub:
    jmp $B850
__basic_mul:
    jmp $BA28
__basic_div:
    jmp $BB0F

; Vergleich: FAC ist rechter Operand, Speicher A/Y ist linker Operand
__basic_cmp_eq:
    jsr $BC5B
    beq __basic_cmp_eq_true
    lda #<__basic_float_zero
    ldy #>__basic_float_zero
    jmp $BBA2
__basic_cmp_eq_true:
    lda #<__basic_float_one
    ldy #>__basic_float_one
    jmp $BBA2
__basic_cmp_ne:
    jsr $BC5B
    bne __basic_cmp_ne_true
    lda #<__basic_float_zero
    ldy #>__basic_float_zero
    jmp $BBA2
__basic_cmp_ne_true:
    lda #<__basic_float_one
    ldy #>__basic_float_one
    jmp $BBA2
__basic_cmp_lt:
    jsr $BC5B
    cmp #$01
    beq __basic_cmp_lt_true
    lda #<__basic_float_zero
    ldy #>__basic_float_zero
    jmp $BBA2
__basic_cmp_lt_true:
    lda #<__basic_float_one
    ldy #>__basic_float_one
    jmp $BBA2
__basic_cmp_gt:
    jsr $BC5B
    cmp #$FF
    beq __basic_cmp_gt_true
    lda #<__basic_float_zero
    ldy #>__basic_float_zero
    jmp $BBA2
__basic_cmp_gt_true:
    lda #<__basic_float_one
    ldy #>__basic_float_one
    jmp $BBA2
__basic_cmp_le:
    jsr $BC5B
    cmp #$FF
    bne __basic_cmp_le_true
    lda #<__basic_float_zero
    ldy #>__basic_float_zero
    jmp $BBA2
__basic_cmp_le_true:
    lda #<__basic_float_one
    ldy #>__basic_float_one
    jmp $BBA2
__basic_cmp_ge:
    jsr $BC5B
    cmp #$01
    bne __basic_cmp_ge_true
    lda #<__basic_float_zero
    ldy #>__basic_float_zero
    jmp $BBA2
__basic_cmp_ge_true:
    lda #<__basic_float_one
    ldy #>__basic_float_one
    jmp $BBA2

__basic_int_and:
    lda __basic_int_left
    and __basic_int_right
    pha
    lda __basic_int_left+1
    and __basic_int_right+1
    tax
    pla
    rts
__basic_int_or:
    lda __basic_int_left
    ora __basic_int_right
    pha
    lda __basic_int_left+1
    ora __basic_int_right+1
    tax
    pla
    rts

__basic_u16_add:
    clc
    lda __basic_int_left
    adc __basic_int_right
    pha
    lda __basic_int_left+1
    adc __basic_int_right+1
    tax
    pla
    rts
__basic_u16_mul:
    lda #$00
    sta __basic_int_result
    sta __basic_int_result+1
    ldy #$10
__basic_u16_mul_loop:
    lsr __basic_int_right+1
    ror __basic_int_right
    bcc __basic_u16_mul_skip
    clc
    lda __basic_int_result
    adc __basic_int_left
    sta __basic_int_result
    lda __basic_int_result+1
    adc __basic_int_left+1
    sta __basic_int_result+1
__basic_u16_mul_skip:
    asl __basic_int_left
    rol __basic_int_left+1
    dey
    bne __basic_u16_mul_loop
    lda __basic_int_result
    ldx __basic_int_result+1
    rts
__basic_int_mod:
    lda __basic_int_right
    ora __basic_int_right+1
    bne __basic_int_mod_nonzero
    lda #$00
    tax
    rts
__basic_int_mod_nonzero:
__basic_int_mod_loop:
    lda __basic_int_left+1
    cmp __basic_int_right+1
    bcc __basic_int_mod_done
    bne __basic_int_mod_sub
    lda __basic_int_left
    cmp __basic_int_right
    bcc __basic_int_mod_done
__basic_int_mod_sub:
    sec
    lda __basic_int_left
    sbc __basic_int_right
    sta __basic_int_left
    lda __basic_int_left+1
    sbc __basic_int_right+1
    sta __basic_int_left+1
    jmp __basic_int_mod_loop
__basic_int_mod_done:
    lda __basic_int_left
    ldx __basic_int_left+1
    rts

; Stringroutinen: [Länge][bis zu 255 Bytes]
__basic_string_clear:
    ldy #$00
    lda #$00
    sta ($FB),y
    rts
__basic_string_copy:
    jsr __basic_string_clear
    jmp __basic_string_append
__basic_string_append:
    lda $FB
    sta __basic_string_base_ptr
    lda $FC
    sta __basic_string_base_ptr+1
    ldy #$00
    lda ($FB),y
    sta __basic_string_dest_length
    lda ($FD),y
    sta __basic_string_source_length
    beq __basic_string_append_empty
    inc $FD
    bne __basic_string_src_ptr_ok
    inc $FE
__basic_string_src_ptr_ok:
    clc
    lda $FB
    adc __basic_string_dest_length
    sta $FB
    lda $FC
    adc #$00
    sta $FC
    inc $FB
    bne __basic_string_dst_ptr_ok
    inc $FC
__basic_string_dst_ptr_ok:
    ldx #$00
__basic_string_append_loop:
    lda __basic_string_dest_length
    cmp #$FF
    beq __basic_string_append_done
    ldy #$00
    lda ($FD),y
    sta ($FB),y
    inc $FD
    bne __basic_string_append_src_ok
    inc $FE
__basic_string_append_src_ok:
    inc $FB
    bne __basic_string_append_dst_ok
    inc $FC
__basic_string_append_dst_ok:
    inc __basic_string_dest_length
    inx
    cpx __basic_string_source_length
    bne __basic_string_append_loop
__basic_string_append_done:
    lda __basic_string_base_ptr
    sta $FB
    lda __basic_string_base_ptr+1
    sta $FC
    ldy #$00
    lda __basic_string_dest_length
    sta ($FB),y
__basic_string_append_empty:
    rts

__basic_string_compare:
    ldy #$00
    lda ($FB),y
    sta __basic_string_left_length
    lda ($FD),y
    sta __basic_string_right_length
    inc $FB
    bne __basic_string_cmp_lptr_ok
    inc $FC
__basic_string_cmp_lptr_ok:
    inc $FD
    bne __basic_string_cmp_rptr_ok
    inc $FE
__basic_string_cmp_rptr_ok:
    ldy #$00
__basic_string_cmp_loop:
    cpy __basic_string_left_length
    beq __basic_string_cmp_left_end
    cpy __basic_string_right_length
    beq __basic_string_cmp_right_shorter
    lda ($FB),y
    cmp ($FD),y
    bcc __basic_string_cmp_less
    bne __basic_string_cmp_greater
    iny
    bne __basic_string_cmp_loop
__basic_string_cmp_left_end:
    cpy __basic_string_right_length
    beq __basic_string_cmp_equal
__basic_string_cmp_less:
    lda #$FF
    rts
__basic_string_cmp_right_shorter:
__basic_string_cmp_greater:
    lda #$01
    rts
__basic_string_cmp_equal:
    lda #$00
    rts

; INPUT/INPUT#/READ-Feldpuffer
__basic_read_line:
    ldx #$00
__basic_read_line_loop:
    jsr $FFCF
    cmp #$0D
    beq __basic_read_line_done
    cpx #$FF
    beq __basic_read_line_done
    sta __basic_input_buffer+1,x
    inx
    bne __basic_read_line_loop
__basic_read_line_done:
    stx __basic_input_buffer
    rts
__basic_input_next_field:
    ldy __basic_field_position
__basic_input_skip_spaces:
    cpy __basic_input_buffer
    beq __basic_input_field_empty
    lda __basic_input_buffer+1,y
    cmp #$20
    bne __basic_input_copy_start
    iny
    bne __basic_input_skip_spaces
__basic_input_copy_start:
    ldx #$00
__basic_input_copy_loop:
    cpy __basic_input_buffer
    beq __basic_input_copy_done
    lda __basic_input_buffer+1,y
    cmp #$2C
    beq __basic_input_comma
    sta __basic_field_buffer+1,x
    inx
    iny
    bne __basic_input_copy_loop
__basic_input_comma:
    iny
__basic_input_copy_done:
    sty __basic_field_position
__basic_input_trim:
    cpx #$00
    beq __basic_input_field_store
    lda __basic_field_buffer,x
    cmp #$20
    bne __basic_input_field_store
    dex
    jmp __basic_input_trim
__basic_input_field_empty:
    ldx #$00
__basic_input_field_store:
    stx __basic_field_buffer
    rts
__basic_field_to_float:
    lda __basic_field_buffer
    bne __basic_field_to_float_nonempty
    lda #<__basic_float_zero
    ldy #>__basic_float_zero
    jmp $BBA2
__basic_field_to_float_nonempty:
    lda #<__basic_field_buffer+1
    sta $22
    lda #>__basic_field_buffer+1
    sta $23
    lda __basic_field_buffer
    jmp $B7B5

__basic_data_read_field:
    lda __basic_data_ptr
    sta $FB
    lda __basic_data_ptr+1
    sta $FC
    ldy #$00
    lda ($FB),y
    cmp #$FF
    bne __basic_data_available
    jmp __basic_out_of_data
__basic_data_available:
    tax
    sta __basic_field_buffer
    inc $FB
    bne __basic_data_ptr_ok
    inc $FC
__basic_data_ptr_ok:
    ldy #$00
__basic_data_copy_loop:
    cpx #$00
    beq __basic_data_copy_done
    lda ($FB),y
    sta __basic_field_buffer+1,y
    iny
    dex
    bne __basic_data_copy_loop
__basic_data_copy_done:
    tya
    clc
    adc $FB
    sta __basic_data_ptr
    lda $FC
    adc #$00
    sta __basic_data_ptr+1
    rts

__basic_sys_indirect:
    jmp ($FB)

__basic_bad_subscript:
    lda #<__basic_error_bad_subscript
    ldy #>__basic_error_bad_subscript
    jsr __basic_print_z
    jmp __basic_abort
__basic_out_of_data:
    lda #<__basic_error_out_of_data
    ldy #>__basic_error_out_of_data
    jsr __basic_print_z
__basic_abort:
    ldx __basic_entry_sp
    txs
    jmp __basic_program_end

; ---- Fließkommakonstanten im kompakten CBM-5-Byte-Format ----------
__basic_float_zero = __basic_float_const_1
__basic_float_one = __basic_float_const_2
__basic_float_const_1: .byte $00, $00, $00, $00, $00
__basic_float_const_2: .byte $81, $00, $00, $00, $00
__basic_float_const_3: .byte $90, $50, $20, $00, $00
__basic_float_const_4: .byte $90, $50, $21, $00, $00
__basic_float_const_5: .byte $88, $13, $00, $00, $00
__basic_float_const_6: .byte $86, $44, $00, $00, $00
__basic_float_const_7: .byte $86, $54, $00, $00, $00
__basic_float_const_8: .byte $84, $10, $00, $00, $00
__basic_float_const_9: .byte $84, $20, $00, $00, $00
__basic_float_const_10: .byte $86, $48, $00, $00, $00
__basic_float_const_11: .byte $84, $40, $00, $00, $00
__basic_float_const_12: .byte $85, $30, $00, $00, $00
__basic_float_const_13: .byte $82, $00, $00, $00, $00
__basic_float_const_14: .byte $86, $4C, $00, $00, $00
__basic_float_const_15: .byte $85, $00, $00, $00, $00
__basic_float_const_16: .byte $86, $20, $00, $00, $00
__basic_float_const_17: .byte $82, $40, $00, $00, $00
__basic_float_const_18: .byte $86, $50, $00, $00, $00
__basic_float_const_19: .byte $87, $34, $00, $00, $00
__basic_float_const_20: .byte $83, $00, $00, $00, $00
__basic_float_const_21: .byte $85, $70, $00, $00, $00
__basic_float_const_22: .byte $88, $34, $00, $00, $00
__basic_float_const_23: .byte $83, $20, $00, $00, $00
__basic_float_const_24: .byte $88, $20, $00, $00, $00
__basic_float_const_25: .byte $91, $00, $00, $00, $00
__basic_float_const_26: .byte $88, $21, $00, $00, $00
__basic_float_const_27: .byte $89, $00, $00, $00, $00
__basic_float_const_28: .byte $88, $22, $00, $00, $00
__basic_float_const_29: .byte $81, $80, $00, $00, $00
__basic_float_const_30: .byte $87, $22, $00, $00, $00
__basic_float_const_31: .byte $87, $02, $00, $00, $00
__basic_float_const_32: .byte $87, $08, $00, $00, $00
__basic_float_const_33: .byte $87, $2E, $00, $00, $00
__basic_float_const_34: .byte $87, $26, $00, $00, $00
__basic_float_const_35: .byte $87, $0C, $00, $00, $00
__basic_float_const_36: .byte $87, $1E, $00, $00, $00
__basic_float_const_37: .byte $86, $00, $00, $00, $00
__basic_float_const_38: .byte $84, $50, $00, $00, $00
__basic_float_const_39: .byte $99, $00, $00, $00, $00
__basic_float_const_40: .byte $86, $70, $00, $00, $00
__basic_float_const_41: .byte $85, $10, $00, $00, $00
__basic_float_const_42: .byte $88, $12, $00, $00, $00
__basic_float_const_43: .byte $87, $1C, $00, $00, $00
__basic_float_const_44: .byte $89, $16, $00, $00, $00

; ---- ShortString-Literale: [1 Byte Länge][0..255 Datenbytes] ------
__basic_string_1: .byte $0F, $4D, $49, $4E, $45, $53, $57, $45, $45, $50, $45, $52, $20, $43, $36, $34
__basic_string_2: .byte $0E, $53, $43, $48, $57, $49, $45, $52, $49, $47, $4B, $45, $49, $54, $3A
__basic_string_3: .byte $1B, $31, $20, $41, $4E, $46, $41, $45, $4E, $47, $45, $52, $20, $20, $39, $58, $39, $20, $20, $20, $31, $30, $20, $4D, $49, $4E, $45, $4E
__basic_string_4: .byte $1B, $32, $20, $4C, $45, $49, $43, $48, $54, $20, $20, $20, $20, $31, $32, $58, $31, $32, $20, $20, $32, $32, $20, $4D, $49, $4E, $45, $4E
__basic_string_5: .byte $1B, $33, $20, $4D, $49, $54, $54, $45, $4C, $20, $20, $20, $20, $31, $36, $58, $31, $36, $20, $20, $34, $30, $20, $4D, $49, $4E, $45, $4E
__basic_string_6: .byte $1B, $34, $20, $53, $43, $48, $57, $45, $52, $20, $20, $20, $20, $32, $32, $58, $32, $32, $20, $20, $39, $30, $20, $4D, $49, $4E, $45, $4E
__basic_string_7: .byte $1B, $35, $20, $45, $58, $50, $45, $52, $54, $45, $20, $20, $20, $33, $30, $58, $33, $30, $20, $31, $38, $30, $20, $4D, $49, $4E, $45, $4E
__basic_string_12: .byte $00
__basic_string_108: .byte $0C, $4D, $49, $4E, $45, $53, $57, $45, $45, $50, $45, $52, $20
__basic_string_109: .byte $01, $58
__basic_string_110: .byte $08, $20, $20, $4D, $49, $4E, $45, $4E, $3A
__basic_string_111: .byte $05, $5A, $45, $49, $54, $3A
__basic_string_112: .byte $03, $20, $50, $3A
__basic_string_113: .byte $03, $20, $46, $3A
__basic_string_114: .byte $03, $20, $44, $3A
__basic_string_115: .byte $22, $57, $41, $53, $44, $3D, $57, $45, $47, $20, $4F, $2F, $53, $50, $41, $43, $45, $3D, $41, $55, $46, $20, $46, $3D, $46, $4C, $41, $47, $20, $51, $3D, $45, $4E, $44, $45
__basic_string_138: .byte $02, $2A, $20
__basic_string_145: .byte $02, $44, $20
__basic_string_152: .byte $02, $23, $20
__basic_string_159: .byte $02, $46, $20
__basic_string_162: .byte $02, $2E, $20
__basic_string_321: .byte $22, $42, $4F, $4F, $4D, $21, $20, $44, $55, $20, $48, $41, $53, $54, $20, $45, $49, $4E, $45, $20, $4D, $49, $4E, $45, $20, $47, $45, $54, $52, $4F, $46, $46, $45, $4E, $2E
__basic_string_322: .byte $12, $20, $53, $45, $4B, $55, $4E, $44, $45, $4E, $20, $20, $50, $55, $4E, $4B, $54, $45, $3A
__basic_string_323: .byte $15, $4E, $3D, $4E, $45, $55, $45, $53, $20, $53, $50, $49, $45, $4C, $20, $20, $51, $3D, $45, $4E, $44, $45
__basic_string_354: .byte $26, $47, $45, $57, $4F, $4E, $4E, $45, $4E, $21, $20, $41, $4C, $4C, $45, $20, $4D, $49, $4E, $45, $4E, $20, $53, $49, $4E, $44, $20, $45, $4E, $54, $53, $43, $48, $41, $45, $52, $46, $54, $2E
__basic_string_367: .byte $14, $4D, $49, $4E, $45, $53, $57, $45, $45, $50, $45, $52, $20, $42, $45, $45, $4E, $44, $45, $54, $2E

; ---- DATA-Tabelle: [Länge][Textbytes], $FF beendet -----------------
__basic_data_start:
__basic_data_end: .byte $FF
__basic_error_bad_subscript: .byte "?BAD SUBSCRIPT ERROR", $0D, $00
__basic_error_out_of_data: .byte "?OUT OF DATA ERROR", $0D, $00

; ---- Ende des physisch im PRG gespeicherten Images ----------------
__basic_image_end:

; ---- C64 CBSS: nur RAM-Adressen, KEINE Bytes im PRG ----------------
; Strings sind Pascal/Turbo-Pascal-artige ShortStrings:
;   Byte 0 = Länge 0..255, Byte 1..255 = Zeichen
__basic_cbss_start:
__basic_var_CT: .cbss 5
__basic_var_CX: .cbss 5
__basic_var_CY: .cbss 5
__basic_var_DC: .cbss 5
__basic_var_DT: .cbss 5
__basic_var_DX: .cbss 5
__basic_var_DY: .cbss 5
__basic_var_ET: .cbss 5
__basic_var_EX: .cbss 5
__basic_var_EY: .cbss 5
__basic_var_FC: .cbss 5
__basic_var_GS: .cbss 5
__basic_var_KC: .cbss 5
__basic_var_LT: .cbss 5
__basic_var_MC: .cbss 5
__basic_var_MX: .cbss 5
__basic_var_NN: .cbss 5
__basic_var_NX: .cbss 5
__basic_var_NY: .cbss 5
__basic_var_OC: .cbss 5
__basic_var_OK: .cbss 5
__basic_var_PL: .cbss 5
__basic_var_QH: .cbss 5
__basic_var_QT: .cbss 5
__basic_var_R: .cbss 5
__basic_var_RX: .cbss 5
__basic_var_RY: .cbss 5
__basic_var_SC: .cbss 5
__basic_var_SF: .cbss 5
__basic_var_SZ: .cbss 5
__basic_var_T0: .cbss 5
__basic_var_TX: .cbss 5
__basic_var_TY: .cbss 5
__basic_var_VW: .cbss 5
__basic_var_VX: .cbss 5
__basic_var_VY: .cbss 5
__basic_var_X: .cbss 5
__basic_var_Y: .cbss 5
__basic_str_C_: .cbss 256
__basic_str_K_: .cbss 256
__basic_array_D_: .cbss 1922
__basic_array_M_: .cbss 1922
__basic_array_O_: .cbss 1922
__basic_array_QX_: .cbss 1800
__basic_array_QY_: .cbss 1800
__basic_float_tmp_1: .cbss 5
__basic_float_tmp_2: .cbss 5
__basic_float_tmp_3: .cbss 5
__basic_float_tmp_4: .cbss 5
__basic_float_tmp_5: .cbss 5
__basic_float_tmp_6: .cbss 5
__basic_float_tmp_7: .cbss 5
__basic_float_tmp_8: .cbss 5
__basic_float_tmp_9: .cbss 5
__basic_float_tmp_10: .cbss 5
__basic_float_tmp_11: .cbss 5
__basic_float_tmp_12: .cbss 5
__basic_float_tmp_13: .cbss 5
__basic_float_tmp_14: .cbss 5
__basic_float_tmp_15: .cbss 5
__basic_float_tmp_16: .cbss 5
__basic_float_tmp_17: .cbss 5
__basic_float_tmp_18: .cbss 5
__basic_float_tmp_19: .cbss 5
__basic_float_tmp_20: .cbss 5
__basic_float_tmp_21: .cbss 5
__basic_float_tmp_22: .cbss 5
__basic_float_tmp_23: .cbss 5
__basic_float_tmp_24: .cbss 5
__basic_float_tmp_25: .cbss 5
__basic_float_tmp_26: .cbss 5
__basic_float_tmp_27: .cbss 5
__basic_float_tmp_28: .cbss 5
__basic_float_tmp_29: .cbss 5
__basic_float_tmp_30: .cbss 5
__basic_float_tmp_31: .cbss 5
__basic_float_tmp_32: .cbss 5
__basic_float_tmp_33: .cbss 5
__basic_float_tmp_34: .cbss 5
__basic_float_tmp_35: .cbss 5
__basic_float_tmp_36: .cbss 5
__basic_float_tmp_37: .cbss 5
__basic_float_tmp_38: .cbss 5
__basic_float_tmp_39: .cbss 5
__basic_float_tmp_40: .cbss 5
__basic_float_tmp_41: .cbss 5
__basic_float_tmp_42: .cbss 5
__basic_float_tmp_43: .cbss 5
__basic_float_tmp_44: .cbss 5
__basic_float_tmp_45: .cbss 5
__basic_float_tmp_46: .cbss 5
__basic_float_tmp_47: .cbss 5
__basic_float_tmp_48: .cbss 5
__basic_float_tmp_49: .cbss 5
__basic_float_tmp_50: .cbss 5
__basic_float_tmp_51: .cbss 5
__basic_float_tmp_52: .cbss 5
__basic_float_tmp_53: .cbss 5
__basic_float_tmp_54: .cbss 5
__basic_float_tmp_55: .cbss 5
__basic_float_tmp_56: .cbss 5
__basic_float_tmp_57: .cbss 5
__basic_float_tmp_58: .cbss 5
__basic_float_tmp_59: .cbss 5
__basic_float_tmp_60: .cbss 5
__basic_float_tmp_61: .cbss 5
__basic_float_tmp_62: .cbss 5
__basic_float_tmp_63: .cbss 5
__basic_float_tmp_64: .cbss 5
__basic_float_tmp_65: .cbss 5
__basic_float_tmp_66: .cbss 5
__basic_float_tmp_67: .cbss 5
__basic_float_tmp_68: .cbss 5
__basic_float_tmp_69: .cbss 5
__basic_float_tmp_70: .cbss 5
__basic_float_tmp_71: .cbss 5
__basic_float_tmp_72: .cbss 5
__basic_float_tmp_73: .cbss 5
__basic_float_tmp_74: .cbss 5
__basic_float_tmp_75: .cbss 5
__basic_float_tmp_76: .cbss 5
__basic_float_tmp_77: .cbss 5
__basic_float_tmp_78: .cbss 5
__basic_float_tmp_79: .cbss 5
__basic_float_tmp_80: .cbss 5
__basic_float_tmp_81: .cbss 5
__basic_float_tmp_82: .cbss 5
__basic_float_tmp_83: .cbss 5
__basic_float_tmp_84: .cbss 5
__basic_float_tmp_85: .cbss 5
__basic_float_tmp_86: .cbss 5
__basic_float_tmp_87: .cbss 5
__basic_float_tmp_88: .cbss 5
__basic_float_tmp_89: .cbss 5
__basic_float_tmp_90: .cbss 5
__basic_float_tmp_91: .cbss 5
__basic_float_tmp_92: .cbss 5
__basic_float_tmp_93: .cbss 5
__basic_float_tmp_94: .cbss 5
__basic_float_tmp_95: .cbss 5
__basic_float_tmp_96: .cbss 5
__basic_float_tmp_97: .cbss 5
__basic_float_tmp_98: .cbss 5
__basic_float_tmp_99: .cbss 5
__basic_float_tmp_100: .cbss 5
__basic_float_tmp_101: .cbss 5
__basic_float_tmp_102: .cbss 5
__basic_float_tmp_103: .cbss 5
__basic_float_tmp_104: .cbss 5
__basic_float_tmp_105: .cbss 5
__basic_float_tmp_106: .cbss 5
__basic_float_tmp_107: .cbss 5
__basic_float_tmp_108: .cbss 5
__basic_float_tmp_109: .cbss 5
__basic_float_tmp_110: .cbss 5
__basic_float_tmp_111: .cbss 5
__basic_float_tmp_112: .cbss 5
__basic_float_tmp_113: .cbss 5
__basic_float_tmp_114: .cbss 5
__basic_float_tmp_115: .cbss 5
__basic_float_tmp_116: .cbss 5
__basic_float_tmp_117: .cbss 5
__basic_float_tmp_118: .cbss 5
__basic_float_tmp_119: .cbss 5
__basic_float_tmp_120: .cbss 5
__basic_float_tmp_121: .cbss 5
__basic_float_tmp_122: .cbss 5
__basic_float_tmp_123: .cbss 5
__basic_float_tmp_124: .cbss 5
__basic_float_tmp_125: .cbss 5
__basic_float_tmp_126: .cbss 5
__basic_float_tmp_127: .cbss 5
__basic_float_tmp_128: .cbss 5
__basic_float_tmp_129: .cbss 5
__basic_float_tmp_130: .cbss 5
__basic_float_tmp_131: .cbss 5
__basic_float_tmp_132: .cbss 5
__basic_float_tmp_133: .cbss 5
__basic_float_tmp_134: .cbss 5
__basic_float_tmp_135: .cbss 5
__basic_float_tmp_136: .cbss 5
__basic_float_tmp_137: .cbss 5
__basic_float_tmp_138: .cbss 5
__basic_float_tmp_139: .cbss 5
__basic_float_tmp_140: .cbss 5
__basic_float_tmp_141: .cbss 5
__basic_float_tmp_142: .cbss 5
__basic_float_tmp_143: .cbss 5
__basic_float_tmp_144: .cbss 5
__basic_float_tmp_145: .cbss 5
__basic_float_tmp_146: .cbss 5
__basic_float_tmp_147: .cbss 5
__basic_float_tmp_148: .cbss 5
__basic_float_tmp_149: .cbss 5
__basic_float_tmp_150: .cbss 5
__basic_float_tmp_151: .cbss 5
__basic_float_tmp_152: .cbss 5
__basic_float_tmp_153: .cbss 5
__basic_float_tmp_154: .cbss 5
__basic_float_tmp_155: .cbss 5
__basic_float_tmp_156: .cbss 5
__basic_float_tmp_157: .cbss 5
__basic_float_tmp_158: .cbss 5
__basic_float_tmp_159: .cbss 5
__basic_float_tmp_160: .cbss 5
__basic_float_tmp_161: .cbss 5
__basic_float_tmp_162: .cbss 5
__basic_float_tmp_163: .cbss 5
__basic_float_tmp_164: .cbss 5
__basic_float_tmp_165: .cbss 5
__basic_float_tmp_166: .cbss 5
__basic_float_tmp_167: .cbss 5
__basic_float_tmp_168: .cbss 5
__basic_float_tmp_169: .cbss 5
__basic_float_tmp_170: .cbss 5
__basic_float_tmp_171: .cbss 5
__basic_float_tmp_172: .cbss 5
__basic_float_tmp_173: .cbss 5
__basic_float_tmp_174: .cbss 5
__basic_float_tmp_175: .cbss 5
__basic_float_tmp_176: .cbss 5
__basic_float_tmp_177: .cbss 5
__basic_float_tmp_178: .cbss 5
__basic_float_tmp_179: .cbss 5
__basic_float_tmp_180: .cbss 5
__basic_float_tmp_181: .cbss 5
__basic_float_tmp_182: .cbss 5
__basic_float_tmp_183: .cbss 5
__basic_float_tmp_184: .cbss 5
__basic_float_tmp_185: .cbss 5
__basic_float_tmp_186: .cbss 5
__basic_float_tmp_187: .cbss 5
__basic_float_tmp_188: .cbss 5
__basic_float_tmp_189: .cbss 5
__basic_float_tmp_190: .cbss 5
__basic_float_tmp_191: .cbss 5
__basic_float_tmp_192: .cbss 5
__basic_float_tmp_193: .cbss 5
__basic_float_tmp_194: .cbss 5
__basic_float_tmp_195: .cbss 5
__basic_float_tmp_196: .cbss 5
__basic_float_tmp_197: .cbss 5
__basic_float_tmp_198: .cbss 5
__basic_float_tmp_199: .cbss 5
__basic_float_tmp_200: .cbss 5
__basic_float_tmp_201: .cbss 5
__basic_float_tmp_202: .cbss 5
__basic_float_hold: .cbss 5
__basic_float_hold2: .cbss 5
__basic_int_left: .cbss 2
__basic_int_right: .cbss 2
__basic_int_result: .cbss 2
__basic_int_hold: .cbss 2
__basic_index: .cbss 2
__basic_linear_index: .cbss 2
__basic_dest_ptr: .cbss 2
__basic_data_ptr: .cbss 2
__basic_string_base_ptr: .cbss 2
__basic_compare_result: .cbss 1
__basic_string_dest_length: .cbss 1
__basic_string_source_length: .cbss 1
__basic_string_left_length: .cbss 1
__basic_string_right_length: .cbss 1
__basic_field_position: .cbss 1
__basic_get_char: .cbss 1
__basic_lfn: .cbss 1
__basic_device: .cbss 1
__basic_secondary: .cbss 1
__basic_entry_sp: .cbss 1
__basic_string_expr: .cbss 256
__basic_string_left: .cbss 256
__basic_string_right: .cbss 256
__basic_string_term: .cbss 256
__basic_input_buffer: .cbss 256
__basic_field_buffer: .cbss 256
__basic_cbss_end:
end
