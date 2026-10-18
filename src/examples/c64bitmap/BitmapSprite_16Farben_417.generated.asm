; ---------------------------------------------------------------------------
; C64 BASIC Compiler output: /mnt/data/stage417_work/examples/c64bitmap/BitmapSprite_16Farben_417.bas
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
    ; LOAD SPRITE: Bitmap_16_Farben_417.bmsprite mit 2 Software-Sprites vorbereitet
__basic_line_20:
    jsr __basic_soft_screen_on
__basic_line_30:
__basic_line_40:
    ; Software-Sprite: 180 VIC-II-Bytes aktualisiert
    lda #$05
    sta $6CE8
    sta $6CE9
    sta $6CEA
    sta $6CEB
    sta $6CEC
    sta $6CED
    sta $6CEE
    sta $6CEF
    lda #$5A
    sta $6CF0
    sta $6CF1
    sta $6CF2
    sta $6CF3
    sta $6CF4
    sta $6CF5
    sta $6CF6
    sta $6CF7
    sta $6CF8
    sta $6CF9
    sta $6CFA
    sta $6CFB
    sta $6CFC
    sta $6CFD
    sta $6CFE
    sta $6CFF
    sta $6D00
    sta $6D01
    sta $6D02
    sta $6D03
    sta $6D04
    sta $6D05
    sta $6D06
    sta $6D07
    sta $6D08
    sta $6D09
    sta $6D0A
    sta $6D0B
    sta $6D0C
    sta $6D0D
    sta $6D0E
    sta $6D0F
    lda #$50
    sta $6D10
    sta $6D11
    sta $6D12
    sta $6D13
    sta $6D14
    sta $6D15
    sta $6D16
    sta $6D17
    lda #$05
    sta $6E20
    sta $6E21
    sta $6E22
    sta $6E23
    sta $6E24
    sta $6E25
    sta $6E26
    sta $6E27
    lda #$5A
    sta $6E28
    sta $6E29
    sta $6E2A
    sta $6E2B
    sta $6E2C
    sta $6E2D
    sta $6E2E
    sta $6E2F
    sta $6E30
    sta $6E31
    sta $6E32
    sta $6E33
    sta $6E34
    sta $6E35
    sta $6E36
    sta $6E37
    sta $6E38
    sta $6E39
    sta $6E3A
    sta $6E3B
    sta $6E3C
    sta $6E3D
    sta $6E3E
    sta $6E3F
    sta $6E40
    sta $6E41
    sta $6E42
    sta $6E43
    sta $6E44
    sta $6E45
    sta $6E46
    sta $6E47
    sta $6E48
    sta $6E49
    sta $6E4A
    sta $6E4B
    sta $6E4C
    sta $6E4D
    sta $6E4E
    sta $6E4F
    lda #$50
    sta $6E50
    sta $6E51
    sta $6E52
    sta $6E53
    sta $6E54
    sta $6E55
    sta $6E56
    sta $6E57
    lda #$05
    sta $6F60
    sta $6F61
    sta $6F62
    sta $6F63
    sta $6F64
    sta $6F65
    sta $6F66
    sta $6F67
    lda #$5A
    sta $6F68
    sta $6F69
    sta $6F6A
    sta $6F6B
    sta $6F6C
    sta $6F6D
    sta $6F6E
    sta $6F6F
    sta $6F70
    sta $6F71
    sta $6F72
    sta $6F73
    sta $6F74
    sta $6F75
    sta $6F76
    sta $6F77
    sta $6F78
    sta $6F79
    sta $6F7A
    sta $6F7B
    sta $6F7C
    sta $6F7D
    sta $6F7E
    sta $6F7F
    lda #$50
    sta $6F80
    sta $6F81
    sta $6F82
    sta $6F83
    sta $6F84
    sta $6F85
    sta $6F86
    sta $6F87
    lda #$05
    sta $6F88
    sta $6F89
    sta $6F8A
    sta $6F8B
    sta $6F8C
    sta $6F8D
    sta $6F8E
    sta $6F8F
    lda #$50
    sta $6F90
    sta $6F91
    sta $6F92
    sta $6F93
    sta $6F94
    sta $6F95
    sta $6F96
    sta $6F97
    lda #$10
    sta $459D
    lda #$12
    sta $459E
    lda #$23
    sta $459F
    lda #$34
    sta $45A0
    lda #$45
    sta $45A1
    lda #$50
    sta $45A2
    lda #$60
    sta $45C4
    lda #$67
    sta $45C5
    lda #$78
    sta $45C6
    lda #$89
    sta $45C7
    lda #$9A
    sta $45C8
    lda #$AB
    sta $45C9
    lda #$B0
    sta $45CA
    lda #$C0
    sta $45EC
    lda #$CD
    sta $45ED
    lda #$DE
    sta $45EE
    lda #$EF
    sta $45EF
    lda #$F0
    sta $45F0
    lda #$10
    sta $45F1
    sta $45F2
__basic_line_45:
    jsr __basic_soft_screen_wait
__basic_line_50:
    ; Software-Sprite: 188 VIC-II-Bytes aktualisiert
    lda #$55
    sta $6D08
    sta $6D09
    sta $6D0A
    sta $6D0B
    sta $6D0C
    sta $6D0D
    sta $6D0E
    sta $6D0F
    lda #$5A
    sta $6D10
    sta $6D11
    sta $6D12
    sta $6D13
    sta $6D14
    sta $6D15
    sta $6D16
    sta $6D17
    sta $6D18
    sta $6D19
    sta $6D1A
    sta $6D1B
    sta $6D1C
    sta $6D1D
    sta $6D1E
    sta $6D1F
    sta $6D20
    sta $6D21
    sta $6D22
    sta $6D23
    sta $6D24
    sta $6D25
    sta $6D26
    sta $6D27
    sta $6D28
    sta $6D29
    sta $6D2A
    sta $6D2B
    sta $6D2C
    sta $6D2D
    sta $6D2E
    sta $6D2F
    sta $6D30
    sta $6D31
    sta $6D32
    sta $6D33
    sta $6D34
    sta $6D35
    sta $6D36
    sta $6D37
    lda #$50
    sta $6D38
    sta $6D39
    sta $6D3A
    sta $6D3B
    sta $6D3C
    sta $6D3D
    sta $6D3E
    sta $6D3F
    lda #$55
    sta $6E48
    sta $6E49
    sta $6E4A
    sta $6E4B
    sta $6E4C
    sta $6E4D
    sta $6E4E
    sta $6E4F
    lda #$5A
    sta $6E50
    sta $6E51
    sta $6E52
    sta $6E53
    sta $6E54
    sta $6E55
    sta $6E56
    sta $6E57
    sta $6E58
    sta $6E59
    sta $6E5A
    sta $6E5B
    sta $6E5C
    sta $6E5D
    sta $6E5E
    sta $6E5F
    sta $6E60
    sta $6E61
    sta $6E62
    sta $6E63
    sta $6E64
    sta $6E65
    sta $6E66
    sta $6E67
    sta $6E68
    sta $6E69
    sta $6E6A
    sta $6E6B
    sta $6E6C
    sta $6E6D
    sta $6E6E
    sta $6E6F
    sta $6E70
    sta $6E71
    sta $6E72
    sta $6E73
    sta $6E74
    sta $6E75
    sta $6E76
    sta $6E77
    lda #$50
    sta $6E78
    sta $6E79
    sta $6E7A
    sta $6E7B
    sta $6E7C
    sta $6E7D
    sta $6E7E
    sta $6E7F
    lda #$00
    sta $6F88
    sta $6F89
    sta $6F8A
    sta $6F8B
    sta $6F8C
    sta $6F8D
    sta $6F8E
    sta $6F8F
    lda #$05
    sta $6F90
    sta $6F91
    sta $6F92
    sta $6F93
    sta $6F94
    sta $6F95
    sta $6F96
    sta $6F97
    lda #$5A
    sta $6F98
    sta $6F99
    sta $6F9A
    sta $6F9B
    sta $6F9C
    sta $6F9D
    sta $6F9E
    sta $6F9F
    sta $6FA0
    sta $6FA1
    sta $6FA2
    sta $6FA3
    sta $6FA4
    sta $6FA5
    sta $6FA6
    sta $6FA7
    sta $6FA8
    sta $6FA9
    sta $6FAA
    sta $6FAB
    sta $6FAC
    sta $6FAD
    sta $6FAE
    sta $6FAF
    sta $6FB0
    sta $6FB1
    sta $6FB2
    sta $6FB3
    sta $6FB4
    sta $6FB5
    sta $6FB6
    sta $6FB7
    lda #$50
    sta $6FB8
    sta $6FB9
    sta $6FBA
    sta $6FBB
    sta $6FBC
    sta $6FBD
    sta $6FBE
    sta $6FBF
    lda #$40
    sta $45A1
    lda #$45
    sta $45A2
    lda #$56
    sta $45A3
    lda #$67
    sta $45A4
    lda #$78
    sta $45A5
    lda #$89
    sta $45A6
    lda #$90
    sta $45A7
    lda #$A0
    sta $45C9
    lda #$AB
    sta $45CA
    lda #$BC
    sta $45CB
    lda #$CD
    sta $45CC
    lda #$DE
    sta $45CD
    lda #$EF
    sta $45CE
    lda #$F0
    sta $45CF
    lda #$00
    sta $45F1
    lda #$12
    sta $45F3
    lda #$23
    sta $45F4
    lda #$34
    sta $45F5
    lda #$45
    sta $45F6
    lda #$50
    sta $45F7
__basic_line_55:
    jsr __basic_soft_screen_wait
__basic_line_60:
    ; Software-Sprite: 142 VIC-II-Bytes aktualisiert
    lda #$00
    sta $6CE8
    sta $6CE9
    sta $6CEA
    sta $6CEB
    sta $6CEC
    sta $6CED
    sta $6CEE
    sta $6CEF
    sta $6CF0
    sta $6CF1
    sta $6CF2
    sta $6CF3
    sta $6CF4
    sta $6CF5
    sta $6CF6
    sta $6CF7
    sta $6CF8
    sta $6CF9
    sta $6CFA
    sta $6CFB
    sta $6CFC
    sta $6CFD
    sta $6CFE
    sta $6CFF
    sta $6D00
    sta $6D01
    sta $6D02
    sta $6D03
    sta $6D04
    sta $6D05
    sta $6D06
    sta $6D07
    lda #$05
    sta $6D08
    sta $6D09
    sta $6D0A
    sta $6D0B
    sta $6D0C
    sta $6D0D
    sta $6D0E
    sta $6D0F
    lda #$00
    sta $6E20
    sta $6E21
    sta $6E22
    sta $6E23
    sta $6E24
    sta $6E25
    sta $6E26
    sta $6E27
    sta $6E28
    sta $6E29
    sta $6E2A
    sta $6E2B
    sta $6E2C
    sta $6E2D
    sta $6E2E
    sta $6E2F
    sta $6E30
    sta $6E31
    sta $6E32
    sta $6E33
    sta $6E34
    sta $6E35
    sta $6E36
    sta $6E37
    sta $6E38
    sta $6E39
    sta $6E3A
    sta $6E3B
    sta $6E3C
    sta $6E3D
    sta $6E3E
    sta $6E3F
    sta $6E40
    sta $6E41
    sta $6E42
    sta $6E43
    sta $6E44
    sta $6E45
    sta $6E46
    sta $6E47
    lda #$05
    sta $6E48
    sta $6E49
    sta $6E4A
    sta $6E4B
    sta $6E4C
    sta $6E4D
    sta $6E4E
    sta $6E4F
    lda #$00
    sta $6F60
    sta $6F61
    sta $6F62
    sta $6F63
    sta $6F64
    sta $6F65
    sta $6F66
    sta $6F67
    sta $6F68
    sta $6F69
    sta $6F6A
    sta $6F6B
    sta $6F6C
    sta $6F6D
    sta $6F6E
    sta $6F6F
    sta $6F70
    sta $6F71
    sta $6F72
    sta $6F73
    sta $6F74
    sta $6F75
    sta $6F76
    sta $6F77
    sta $6F78
    sta $6F79
    sta $6F7A
    sta $6F7B
    sta $6F7C
    sta $6F7D
    sta $6F7E
    sta $6F7F
    sta $6F80
    sta $6F81
    sta $6F82
    sta $6F83
    sta $6F84
    sta $6F85
    sta $6F86
    sta $6F87
    sta $459D
    sta $459E
    sta $459F
    sta $45A0
    sta $45C4
    sta $45C5
    sta $45C6
    sta $45C7
    sta $45C8
    sta $45EC
    sta $45ED
    sta $45EE
    sta $45EF
    sta $45F0
__basic_line_65:
    jsr __basic_soft_screen_wait
__basic_line_70:
    jsr __basic_soft_screen_off
__basic_line_80:
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
    jsr $BC9B
    lda $65
    ldx $64
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
    lda #<(__basic_field_buffer+1)
    sta $22
    lda #>(__basic_field_buffer+1)
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


; Stage 417: echte VIC-II Multicolor-Bitmap Bank 1, $6000/$4400, Farben $D800
; Sichert Farb-RAM bei $4800-$4BE7 und stellt die VIC-Register wieder her.
__basic_soft_screen_on:
    lda __basic_soft_screen_active
    bne __basic_soft_screen_clear
    lda $DD00
    sta __basic_soft_old_bank
    lda $D011
    sta __basic_soft_old_d011
    lda $D016
    sta __basic_soft_old_d016
    lda $D018
    sta __basic_soft_old_d018
    lda $D021
    sta __basic_soft_old_d021
    ldx #$00
__basic_soft_save_colour:
    lda $D800,x
    sta $4800,x
    lda $D900,x
    sta $4900,x
    lda $DA00,x
    sta $4A00,x
    lda $DB00,x
    sta $4B00,x
    inx
    bne __basic_soft_save_colour
    lda #$01
    sta __basic_soft_screen_active
__basic_soft_screen_clear:
    lda $DD00
    and #$FC
    ora #$02
    sta $DD00
    lda #$18
    sta $D018
    lda $D011
    ora #$20
    sta $D011
    lda $D016
    ora #$10
    sta $D016
    lda #$00
    sta $D021
    ldx #$00
__basic_soft_zero_loop:
    lda #$00
    sta $6000,x
    sta $6100,x
    sta $6200,x
    sta $6300,x
    sta $6400,x
    sta $6500,x
    sta $6600,x
    sta $6700,x
    sta $6800,x
    sta $6900,x
    sta $6A00,x
    sta $6B00,x
    sta $6C00,x
    sta $6D00,x
    sta $6E00,x
    sta $6F00,x
    sta $7000,x
    sta $7100,x
    sta $7200,x
    sta $7300,x
    sta $7400,x
    sta $7500,x
    sta $7600,x
    sta $7700,x
    sta $7800,x
    sta $7900,x
    sta $7A00,x
    sta $7B00,x
    sta $7C00,x
    sta $7D00,x
    sta $7E00,x
    sta $7F00,x
    sta $4400,x
    sta $D800,x
    sta $4500,x
    sta $D900,x
    sta $4600,x
    sta $DA00,x
    sta $4700,x
    sta $DB00,x
    inx
    bne __basic_soft_zero_loop
    rts
__basic_soft_screen_wait:
    jsr $FFE4
    beq __basic_soft_screen_wait
    rts
__basic_soft_screen_off:
    lda __basic_soft_screen_active
    beq __basic_soft_screen_off_done
    ldx #$00
__basic_soft_restore_colour:
    lda $4800,x
    sta $D800,x
    lda $4900,x
    sta $D900,x
    lda $4A00,x
    sta $DA00,x
    lda $4B00,x
    sta $DB00,x
    inx
    bne __basic_soft_restore_colour
    lda __basic_soft_old_bank
    sta $DD00
    lda __basic_soft_old_d011
    sta $D011
    lda __basic_soft_old_d016
    sta $D016
    lda __basic_soft_old_d018
    sta $D018
    lda __basic_soft_old_d021
    sta $D021
    lda #$00
    sta __basic_soft_screen_active
__basic_soft_screen_off_done:
    rts
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
__basic_soft_screen_active: .cbss 1
__basic_soft_old_bank: .cbss 1
__basic_soft_old_d011: .cbss 1
__basic_soft_old_d016: .cbss 1
__basic_soft_old_d018: .cbss 1
__basic_soft_old_d021: .cbss 1
__basic_cbss_end:
end
