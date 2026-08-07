; ---------------------------------------------------------------------------
; C64 BASIC Compiler output: basic_extended_demo.bas
; CBM-5-Byte-Fließkomma, Strings, Arrays, DATA/INPUT und KERNAL-I/O
; Ziel: MOS 6510 / Commodore 64
; ---------------------------------------------------------------------------
.org $080D
.entry __basic_start

__basic_start:
    tsx
    stx __basic_entry_sp
    lda #<__basic_data_start
    sta __basic_data_ptr
    lda #>__basic_data_start
    sta __basic_data_ptr+1
__basic_line_10:
__basic_line_20:
__basic_line_30:
    lda #<__basic_float_const_3
    ldy #>__basic_float_const_3
    jsr $BBA2
    ldx #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBD4
    lda #<__basic_float_const_4
    ldy #>__basic_float_const_4
    jsr $BBA2
    ldx #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBD4
    lda #<__basic_var_X
    ldy #>__basic_var_X
    jsr $BBA2
    ldx #<__basic_float_tmp_2
    ldy #>__basic_float_tmp_2
    jsr $BBD4
    lda #<__basic_var_Y
    ldy #>__basic_var_Y
    jsr $BBA2
    lda #<__basic_float_tmp_2
    ldy #>__basic_float_tmp_2
    jsr __basic_mul
    ldx #<__basic_float_tmp_1
    ldy #>__basic_float_tmp_1
    jsr $BBD4
    lda #<__basic_float_const_5
    ldy #>__basic_float_const_5
    jsr $BBA2
    lda #<__basic_float_tmp_1
    ldy #>__basic_float_tmp_1
    jsr __basic_add
    ldx #<__basic_var_Z
    ldy #>__basic_var_Z
    jsr $BBD4
__basic_line_40:
    lda #<__basic_var_Z
    ldy #>__basic_var_Z
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_1
    bne __basic_index_bad_2
    lda __basic_index
    cmp #$03
    bcc __basic_index_ok_1
    beq __basic_index_ok_1
__basic_index_bad_2:
    jsr __basic_bad_subscript
__basic_index_ok_1:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$05
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_F
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_F
    sta $FC
    lda #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBA2
    ldx $FB
    ldy $FC
    jsr $BBD4
    lda #<__basic_float_const_6
    ldy #>__basic_float_const_6
    jsr $BBA2
    ldx #<__basic_float_hold
    ldy #>__basic_float_hold
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_3
    bne __basic_index_bad_4
    lda __basic_index
    cmp #$02
    bcc __basic_index_ok_3
    beq __basic_index_ok_3
__basic_index_bad_4:
    jsr __basic_bad_subscript
__basic_index_ok_3:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$03
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_float_const_7
    ldy #>__basic_float_const_7
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_5
    bne __basic_index_bad_6
    lda __basic_index
    cmp #$02
    bcc __basic_index_ok_5
    beq __basic_index_ok_5
__basic_index_bad_6:
    jsr __basic_bad_subscript
__basic_index_ok_5:
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
    adc #<__basic_array_I_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_I_
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
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_7
    sta $FD
    lda #>__basic_string_7
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_8
    sta $FD
    lda #>__basic_string_8
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_9
    bne __basic_index_bad_10
    lda __basic_index
    cmp #$02
    bcc __basic_index_ok_9
    beq __basic_index_ok_9
__basic_index_bad_10:
    jsr __basic_bad_subscript
__basic_index_ok_9:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$00
    ldx #$01
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_S_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_S_
    sta $FC
    lda $FB
    sta __basic_dest_ptr
    lda $FC
    sta __basic_dest_ptr+1
    lda __basic_dest_ptr
    sta $FB
    lda __basic_dest_ptr+1
    sta $FC
    lda #<__basic_string_expr
    sta $FD
    lda #>__basic_string_expr
    sta $FE
    jsr __basic_string_copy
__basic_line_50:
__basic_line_60:
    jsr __basic_data_read_field
    jsr __basic_field_to_float
    ldx #<__basic_var_R
    ldy #>__basic_var_R
    jsr $BBD4
    jsr __basic_data_read_field
    lda #<__basic_str_T_
    sta $FB
    lda #>__basic_str_T_
    sta $FC
    lda #<__basic_field_buffer
    sta $FD
    lda #>__basic_field_buffer
    sta $FE
    jsr __basic_string_copy
    jsr __basic_data_read_field
    jsr __basic_field_to_float
    jsr __basic_fac_to_int
    sta __basic_var_J_
    stx __basic_var_J_+1
__basic_line_70:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_11
    sta $FD
    lda #>__basic_string_11
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    lda #<__basic_var_Z
    ldy #>__basic_var_Z
    jsr $BBA2
    jsr __basic_print_float
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_12
    sta $FD
    lda #>__basic_string_12
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_13
    bne __basic_index_bad_14
    lda __basic_index
    cmp #$03
    bcc __basic_index_ok_13
    beq __basic_index_ok_13
__basic_index_bad_14:
    jsr __basic_bad_subscript
__basic_index_ok_13:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$05
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_F
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_F
    sta $FC
    lda $FB
    ldy $FC
    jsr $BBA2
    jsr __basic_print_float
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_15
    bne __basic_index_bad_16
    lda __basic_index
    cmp #$02
    bcc __basic_index_ok_15
    beq __basic_index_ok_15
__basic_index_bad_16:
    jsr __basic_bad_subscript
__basic_index_ok_15:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$03
    ldx #$00
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda #<__basic_float_const_7
    ldy #>__basic_float_const_7
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_17
    bne __basic_index_bad_18
    lda __basic_index
    cmp #$02
    bcc __basic_index_ok_17
    beq __basic_index_ok_17
__basic_index_bad_18:
    jsr __basic_bad_subscript
__basic_index_ok_17:
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
    adc #<__basic_array_I_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_I_
    sta $FC
    ldy #$00
    lda ($FB),y
    sta __basic_int_hold
    iny
    lda ($FB),y
    tax
    lda __basic_int_hold
    jsr __basic_int_to_fac
    jsr __basic_print_float
    jsr __basic_newline
__basic_line_80:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_19
    sta $FD
    lda #>__basic_string_19
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_index
    stx __basic_index+1
    ldx __basic_index+1
    cpx #$00
    bcc __basic_index_ok_20
    bne __basic_index_bad_21
    lda __basic_index
    cmp #$02
    bcc __basic_index_ok_20
    beq __basic_index_ok_20
__basic_index_bad_21:
    jsr __basic_bad_subscript
__basic_index_ok_20:
    lda __basic_index
    ldx __basic_index+1
    sta __basic_linear_index
    stx __basic_linear_index+1
    lda __basic_linear_index
    ldx __basic_linear_index+1
    sta __basic_int_left
    stx __basic_int_left+1
    lda #$00
    ldx #$01
    sta __basic_int_right
    stx __basic_int_right+1
    jsr __basic_u16_mul
    sta __basic_linear_index
    stx __basic_linear_index+1
    clc
    lda __basic_linear_index
    adc #<__basic_array_S_
    sta $FB
    lda __basic_linear_index+1
    adc #>__basic_array_S_
    sta $FC
    lda $FB
    sta $FD
    lda $FC
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_22
    sta $FD
    lda #>__basic_string_22
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    lda #<__basic_var_R
    ldy #>__basic_var_R
    jsr $BBA2
    jsr __basic_print_float
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_str_T_
    sta $FD
    lda #>__basic_str_T_
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    ldy __basic_var_J_
    lda __basic_var_J_+1
    jsr $B391
    jsr __basic_print_float
    jsr __basic_newline
__basic_line_90:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_23
    sta $FD
    lda #>__basic_string_23
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    jsr __basic_read_line
    lda #$00
    sta __basic_field_position
    jsr __basic_input_next_field
    lda #<__basic_str_N_
    sta $FB
    lda #>__basic_str_N_
    sta $FC
    lda #<__basic_field_buffer
    sta $FD
    lda #>__basic_field_buffer
    sta $FE
    jsr __basic_string_copy
__basic_line_100:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_24
    sta $FD
    lda #>__basic_string_24
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    jsr __basic_read_line
    lda #$00
    sta __basic_field_position
    jsr __basic_input_next_field
    jsr __basic_field_to_float
    ldx #<__basic_var_V
    ldy #>__basic_var_V
    jsr $BBD4
__basic_line_110:
    jsr $FFE4
    sta __basic_get_char
    lda __basic_get_char
    beq __basic_get_empty_25
    sta __basic_string_term+1
    lda #$01
    sta __basic_string_term
    jmp __basic_get_done_26
__basic_get_empty_25:
    lda #$00
    sta __basic_string_term
__basic_get_done_26:
    lda #<__basic_str_K_
    sta $FB
    lda #>__basic_str_K_
    sta $FC
    lda #<__basic_string_term
    sta $FD
    lda #>__basic_string_term
    sta $FE
    jsr __basic_string_copy
__basic_line_120:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_27
    sta $FD
    lda #>__basic_string_27
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_str_N_
    sta $FD
    lda #>__basic_str_N_
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #<__basic_var_V
    ldy #>__basic_var_V
    jsr $BBA2
    jsr __basic_print_float
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
    lda #$20
    jsr $FFD2
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
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    jsr __basic_newline
__basic_line_130:
    lda #<__basic_float_const_7
    ldy #>__basic_float_const_7
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_lfn
    lda #<__basic_float_const_8
    ldy #>__basic_float_const_8
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_device
    lda #<__basic_float_const_7
    ldy #>__basic_float_const_7
    jsr $BBA2
    jsr __basic_fac_to_int
    sta __basic_secondary
    lda __basic_lfn
    ldx __basic_device
    ldy __basic_secondary
    jsr $FFBA
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_28
    sta $FD
    lda #>__basic_string_28
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda __basic_string_expr
    ldx #<__basic_string_expr+1
    ldy #>__basic_string_expr+1
    jsr $FFBD
    jsr $FFC0
__basic_line_140:
    lda #<__basic_float_const_7
    ldy #>__basic_float_const_7
    jsr $BBA2
    jsr __basic_fac_to_int
    tax
    jsr $FFC9
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_str_N_
    sta $FD
    lda #>__basic_str_N_
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_29
    sta $FD
    lda #>__basic_string_29
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    lda #<__basic_var_V
    ldy #>__basic_var_V
    jsr $BBA2
    jsr __basic_print_float
    jsr __basic_newline
    jsr $FFCC
__basic_line_150:
    lda #<__basic_float_const_7
    ldy #>__basic_float_const_7
    jsr $BBA2
    jsr __basic_fac_to_int
    jsr $FFC3
__basic_line_160:
    lda #<__basic_data_line_50
    sta __basic_data_ptr
    lda #>__basic_data_line_50
    sta __basic_data_ptr+1
__basic_line_170:
    jsr __basic_data_read_field
    jsr __basic_field_to_float
    ldx #<__basic_var_R2
    ldy #>__basic_var_R2
    jsr $BBD4
__basic_line_180:
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_clear
    lda #<__basic_string_30
    sta $FD
    lda #>__basic_string_30
    sta $FE
    lda #<__basic_string_expr
    sta $FB
    lda #>__basic_string_expr
    sta $FC
    jsr __basic_string_append
    lda #<__basic_string_expr
    ldy #>__basic_string_expr
    jsr __basic_print_string
    lda #<__basic_var_R2
    ldy #>__basic_var_R2
    jsr $BBA2
    jsr __basic_print_float
    jsr __basic_newline
__basic_line_190:
    rts
__basic_program_end:
    jsr $FFCC
    rts

; ---- C64 BASIC Fließkomma-/String-/I/O-Runtime --------------------
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

; ---- Variablen, Arrays und Compiler-Temporärspeicher ---------------
__basic_var_J_: .word $0000
__basic_var_R: .fill 5, $00
__basic_var_R2: .fill 5, $00
__basic_var_V: .fill 5, $00
__basic_var_X: .fill 5, $00
__basic_var_Y: .fill 5, $00
__basic_var_Z: .fill 5, $00
__basic_str_K_: .fill 256, $00
__basic_str_N_: .fill 256, $00
__basic_str_T_: .fill 256, $00
__basic_array_F: .fill 20, $00
__basic_array_I_: .fill 18, $00
__basic_array_S_: .fill 768, $00
__basic_float_tmp_1: .fill 5, $00
__basic_float_tmp_2: .fill 5, $00
__basic_float_hold: .fill 5, $00
__basic_float_hold2: .fill 5, $00
__basic_int_left: .word $0000
__basic_int_right: .word $0000
__basic_int_result: .word $0000
__basic_int_hold: .word $0000
__basic_index: .word $0000
__basic_linear_index: .word $0000
__basic_dest_ptr: .word $0000
__basic_data_ptr: .word $0000
__basic_string_base_ptr: .word $0000
__basic_compare_result: .byte $00
__basic_string_dest_length: .byte $00
__basic_string_source_length: .byte $00
__basic_string_left_length: .byte $00
__basic_string_right_length: .byte $00
__basic_field_position: .byte $00
__basic_get_char: .byte $00
__basic_lfn: .byte $00
__basic_device: .byte $00
__basic_secondary: .byte $00
__basic_entry_sp: .byte $00
__basic_string_expr: .fill 256, $00
__basic_string_left: .fill 256, $00
__basic_string_right: .fill 256, $00
__basic_string_term: .fill 256, $00
__basic_input_buffer: .fill 256, $00
__basic_field_buffer: .fill 256, $00

; ---- Fließkommakonstanten im kompakten CBM-5-Byte-Format ----------
__basic_float_zero = __basic_float_const_1
__basic_float_one = __basic_float_const_2
__basic_float_const_1: .byte $00, $00, $00, $00, $00
__basic_float_const_2: .byte $81, $00, $00, $00, $00
__basic_float_const_3: .byte $81, $40, $00, $00, $00
__basic_float_const_4: .byte $82, $10, $00, $00, $00
__basic_float_const_5: .byte $80, $00, $00, $00, $00
__basic_float_const_6: .byte $86, $28, $00, $00, $00
__basic_float_const_7: .byte $82, $00, $00, $00, $00
__basic_float_const_8: .byte $84, $00, $00, $00, $00

; ---- Zeichenkettenliterale ------------------------------------------
__basic_string_7: .byte $05, $48, $45, $4C, $4C, $4F
__basic_string_8: .byte $04, $20, $43, $36, $34
__basic_string_11: .byte $06, $46, $4C, $4F, $41, $54, $3A
__basic_string_12: .byte $06, $41, $52, $52, $41, $59, $3A
__basic_string_19: .byte $07, $53, $54, $52, $49, $4E, $47, $3A
__basic_string_22: .byte $05, $44, $41, $54, $41, $3A
__basic_string_23: .byte $04, $4E, $41, $4D, $45
__basic_string_24: .byte $04, $57, $45, $52, $54
__basic_string_27: .byte $08, $45, $49, $4E, $47, $41, $42, $45, $3A
__basic_string_28: .byte $0D, $42, $41, $53, $49, $43, $44, $45, $4D, $4F, $2C, $53, $2C, $57
__basic_string_29: .byte $01, $2C
__basic_string_30: .byte $08, $52, $45, $53, $54, $4F, $52, $45, $3A

; ---- DATA-Tabelle: [Länge][Textbytes], $FF beendet -----------------
__basic_data_start:
__basic_data_line_50:
    .byte $04, $33, $2E, $31, $34
    .byte $09, $44, $41, $54, $41, $20, $54, $45, $58, $54
    .byte $01, $37
__basic_data_end: .byte $FF
__basic_error_bad_subscript: .byte "?BAD SUBSCRIPT ERROR", $0D, $00
__basic_error_out_of_data: .byte "?OUT OF DATA ERROR", $0D, $00
end
