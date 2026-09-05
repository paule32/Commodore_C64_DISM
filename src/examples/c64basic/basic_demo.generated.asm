; ---------------------------------------------------------------------------
; C64 BASIC Compiler output: T:\GitHub\dBase2Many\src\asmjit\compiler\frontend\c64\examples\c64basic\basic_demo.bas
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
    jsr __basic_print_thunk_1
    jsr __basic_newline
__basic_line_30:
    lda #<__basic_float_const_3
    ldy #>__basic_float_const_3
    jsr $BBA2
    ldx #<__basic_var_A
    ldy #>__basic_var_A
    jsr $BBD4
__basic_line_40:
    jsr __basic_print_thunk_2
    lda #<__basic_var_A
    ldy #>__basic_var_A
    jsr $BBA2
    jsr __basic_print_float
    jsr __basic_newline
__basic_line_50:
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_var_I
    ldy #>__basic_var_I
    jsr $BBD4
    lda #<__basic_float_const_4
    ldy #>__basic_float_const_4
    jsr $BBA2
    ldx #<__basic_float_tmp_1
    ldy #>__basic_float_tmp_1
    jsr $BBD4
    lda #<__basic_float_const_2
    ldy #>__basic_float_const_2
    jsr $BBA2
    ldx #<__basic_float_tmp_2
    ldy #>__basic_float_tmp_2
    jsr $BBD4
__basic_for_loop_3:
__basic_line_60:
    lda #<__basic_var_I
    ldy #>__basic_var_I
    jsr $BBA2
    jsr __basic_print_float
__basic_line_70:
    lda #<__basic_float_tmp_2
    ldy #>__basic_float_tmp_2
    jsr $BBA2
    lda #<__basic_var_I
    ldy #>__basic_var_I
    jsr __basic_add
    ldx #<__basic_var_I
    ldy #>__basic_var_I
    jsr $BBD4
    lda #<__basic_var_I
    ldy #>__basic_var_I
    jsr $BBA2
    lda #<__basic_float_tmp_1
    ldy #>__basic_float_tmp_1
    jsr $BC5B
    sta __basic_compare_result
    lda #<__basic_float_tmp_2
    ldy #>__basic_float_tmp_2
    jsr $BBA2
    lda $66
    bmi __basic_for_negative_4
    lda __basic_compare_result
    cmp #$01
    beq __basic_for_done_5
    jmp __basic_for_loop_3
__basic_for_negative_4:
    lda __basic_compare_result
    cmp #$FF
    beq __basic_for_done_5
    jmp __basic_for_loop_3
__basic_for_done_5:
__basic_line_80:
    jsr __basic_newline
__basic_line_90:
    lda #<__basic_var_A
    ldy #>__basic_var_A
    jsr $BBA2
    ldx #<__basic_float_tmp_3
    ldy #>__basic_float_tmp_3
    jsr $BBD4
    lda #<__basic_float_const_3
    ldy #>__basic_float_const_3
    jsr $BBA2
    lda #<__basic_float_tmp_3
    ldy #>__basic_float_tmp_3
    jsr __basic_cmp_eq
    lda $61
    beq __basic_if_skip_6
    jmp __basic_line_110
__basic_if_skip_6:
__basic_line_100:
    jsr __basic_print_thunk_7
    jsr __basic_newline
__basic_line_110:
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

; ---- Optimizer: String-Thunks --------------------------------------
__basic_print_thunk_1:
    lda #<__basic_string_1
    ldy #>__basic_string_1
    jmp __basic_print_string
__basic_print_thunk_2:
    lda #<__basic_string_2
    ldy #>__basic_string_2
    jmp __basic_print_string
__basic_print_thunk_7:
    lda #<__basic_string_7
    ldy #>__basic_string_7
    jmp __basic_print_string

; ---- Fließkommakonstanten im kompakten CBM-5-Byte-Format ----------
__basic_float_zero = __basic_float_const_1
__basic_float_one = __basic_float_const_2
__basic_float_const_1: .byte $00, $00, $00, $00, $00
__basic_float_const_2: .byte $81, $00, $00, $00, $00
__basic_float_const_3: .byte $84, $60, $00, $00, $00
__basic_float_const_4: .byte $83, $20, $00, $00, $00

; ---- ShortString-Literale: [1 Byte Länge][0..255 Datenbytes] ------
__basic_string_1: .byte $16, $43, $36, $34, $20, $42, $41, $53, $49, $43, $20, $43, $4F, $4D, $50, $49, $4C, $45, $52, $20, $21, $21, $21
__basic_string_2: .byte $02, $41, $3D
__basic_string_7: .byte $06, $46, $45, $48, $4C, $45, $52

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
__basic_var_A: .cbss 5
__basic_var_I: .cbss 5
__basic_float_tmp_1: .cbss 5
__basic_float_tmp_2: .cbss 5
__basic_float_tmp_3: .cbss 5
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
