; Von C64 Pascal erzeugter MOS-6510-Assembler
; Programm: AdvancedTypes
.org $080D
.entry __pascal_start
.basic

__pascal_start:
    lda #$0E
    jsr $FFD2
    lda #$0A
    ldx #$00
    sta __pas_var_point_0
    stx __pas_var_point_0+1
    lda #$14
    ldx #$00
    sta __pas_var_point_0+2
    stx __pas_var_point_0+3
    lda #$01
    ldx #$00
    sta __pas_var_point_0+4
    lda __pas_var_point_0
    ldx __pas_var_point_0+1
    sta __pas_var_points_1
    stx __pas_var_points_1+1
    lda __pas_var_point_0+2
    ldx __pas_var_point_0+3
    sta __pas_var_points_1+2
    stx __pas_var_points_1+3
    lda __pas_var_point_0+4
    ldx #$00
    sta __pas_var_points_1+4
    lda #$02
    ldx #$00
    sta __pas_var_index_3
    stx __pas_var_index_3+1
    lda #$1E
    ldx #$00
    sta $F9
    stx $FA
    lda __pas_var_index_3
    ldx __pas_var_index_3+1
    sec
    sbc #$01
    sta $FB
    txa
    sbc #$00
    tax
    lda $FB
    cpx #$00
    beq __pas_index_high_ok_1
    jmp __pas_range_error
__pas_index_high_ok_1:
    cmp #$03
    bcc __pas_index_range_ok_2
    jmp __pas_range_error
__pas_index_range_ok_2:
    sta $FB
    stx $FC
    lda #$05
    sta $FD
    lda #$00
    sta $FE
    jsr __pas_mul16
    cpx #$00
    beq __pas_index_offset_ok_3
    jmp __pas_range_error
__pas_index_offset_ok_3:
    tay
    lda $F9
    sta __pas_var_points_1,y
    iny
    lda $FA
    sta __pas_var_points_1,y
    lda #$28
    ldx #$00
    sta $F9
    stx $FA
    lda __pas_var_index_3
    ldx __pas_var_index_3+1
    sec
    sbc #$01
    sta $FB
    txa
    sbc #$00
    tax
    lda $FB
    cpx #$00
    beq __pas_index_high_ok_4
    jmp __pas_range_error
__pas_index_high_ok_4:
    cmp #$03
    bcc __pas_index_range_ok_5
    jmp __pas_range_error
__pas_index_range_ok_5:
    sta $FB
    stx $FC
    lda #$05
    sta $FD
    lda #$00
    sta $FE
    jsr __pas_mul16
    clc
    adc #$02
    sta $FB
    txa
    adc #$00
    tax
    lda $FB
    cpx #$00
    beq __pas_index_offset_ok_6
    jmp __pas_range_error
__pas_index_offset_ok_6:
    tay
    lda $F9
    sta __pas_var_points_1,y
    iny
    lda $FA
    sta __pas_var_points_1,y
    lda #$02
    ldx #$00
    sta $F9
    stx $FA
    lda __pas_var_index_3
    ldx __pas_var_index_3+1
    sec
    sbc #$01
    sta $FB
    txa
    sbc #$00
    tax
    lda $FB
    cpx #$00
    beq __pas_index_high_ok_7
    jmp __pas_range_error
__pas_index_high_ok_7:
    cmp #$03
    bcc __pas_index_range_ok_8
    jmp __pas_range_error
__pas_index_range_ok_8:
    sta $FB
    stx $FC
    lda #$05
    sta $FD
    lda #$00
    sta $FE
    jsr __pas_mul16
    clc
    adc #$04
    sta $FB
    txa
    adc #$00
    tax
    lda $FB
    cpx #$00
    beq __pas_index_offset_ok_9
    jmp __pas_range_error
__pas_index_offset_ok_9:
    tay
    lda $F9
    sta __pas_var_points_1,y
    lda #$04
    ldx #$00
    sta __pas_param_tcounter_create_avalue_4
    stx __pas_param_tcounter_create_avalue_4+1
    ldy #$00
    tya
    clc
    adc #<__pas_var_counter_2
    sta $F7
    lda #>__pas_var_counter_2
    adc #$00
    sta $F8
    jsr __pas_method_tcounter_create
    ldy #$00
    tya
    clc
    adc #<__pas_var_counter_2
    sta $F7
    lda #>__pas_var_counter_2
    adc #$00
    sta $F8
    jsr __pas_method_tcounter_inc
    lda #<__pas_string_0
    ldx #>__pas_string_0
    jsr __pas_print_string
    ldy #$00
    tya
    clc
    adc #<__pas_var_counter_2
    sta $F7
    lda #>__pas_var_counter_2
    adc #$00
    sta $F8
    jsr __pas_method_tcounter_getvalue
    sta $F9
    stx $FA
    lda $F9
    ldx $FA
    jsr __pas_print_int16
    lda #$0D
    jsr $FFD2
    rts

; constructor TCounter.Create
__pas_method_tcounter_create:
    lda __pas_param_tcounter_create_avalue_4
    ldx __pas_param_tcounter_create_avalue_4+1
    ldy #$00
    sta ($F7),y
    iny
    txa
    sta ($F7),y
    rts

; procedure TCounter.Inc
__pas_method_tcounter_inc:
    ldy #$00
    lda ($F7),y
    pha
    iny
    lda ($F7),y
    tax
    pla
    pha
    txa
    pha
    lda #$01
    ldx #$00
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
    ldy #$00
    sta ($F7),y
    iny
    txa
    sta ($F7),y
    rts

; function TCounter.GetValue
__pas_method_tcounter_getvalue:
    lda #$00
    sta __pas_result_tcounter_getvalue_result_5
    sta __pas_result_tcounter_getvalue_result_5+1
    ldy #$00
    lda ($F7),y
    pha
    iny
    lda ($F7),y
    tax
    pla
    sta __pas_result_tcounter_getvalue_result_5
    stx __pas_result_tcounter_getvalue_result_5+1
    lda __pas_result_tcounter_getvalue_result_5
    ldx __pas_result_tcounter_getvalue_result_5+1
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

; Laufzeitfehler bei variablem Arrayindex
__pas_range_error:
    lda #<__pas_range_error_text
    ldx #>__pas_range_error_text
    jsr __pas_print_string
__pas_range_error_halt:
    jmp __pas_range_error_halt

; $FB/$FC * $FD/$FE, Ergebnis in A/X
__pas_mul16:
    lda #$00
    sta __pas_rt_value
    sta __pas_rt_value+1
    ldy #$10
__pas_mul16_loop:
    lsr $FE
    ror $FD
    bcc __pas_mul16_no_add
    clc
    lda __pas_rt_value
    adc $FB
    sta __pas_rt_value
    lda __pas_rt_value+1
    adc $FC
    sta __pas_rt_value+1
__pas_mul16_no_add:
    asl $FB
    rol $FC
    dey
    bne __pas_mul16_loop
    lda __pas_rt_value
    ldx __pas_rt_value+1
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

; Pascal-Variablen
__pas_var_point_0: .byte $00, $00, $00, $00, $00 ; Point: TPoint
__pas_var_points_1: .byte $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00 ; Points: TPoints
__pas_var_counter_2: .word 0 ; Counter: TCounter
__pas_var_index_3: .word 0 ; Index: integer
__pas_param_tcounter_create_avalue_4: .word 0 ; intern: integer
__pas_result_tcounter_getvalue_result_5: .word 0 ; intern: integer

__pas_range_error_text: .byte $49, $6E, $64, $65, $78, $20, $6F, $75, $74, $20, $6F, $66, $20, $72, $61, $6E, $67, $65, $0D, $00

; Nullterminierte PETSCII-Zeichenketten
__pas_string_0: .byte $C3, $4F, $55, $4E, $54, $45, $52, $20, $3D, $20, $00
