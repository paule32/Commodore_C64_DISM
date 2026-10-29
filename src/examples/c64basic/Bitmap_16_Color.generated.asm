; ---------------------------------------------------------------------------
; C64 BASIC Compiler output: T:\GitHub\dBase2Many\src\asmjit\compiler\frontend\c64\examples\c64basic\Bitmap_16_Color.bas
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
    ; LOAD SPRITE: Bitmap_16_Color.bmsprite mit 2 Software-Sprites vorbereitet
__basic_line_20:
    jsr __basic_soft_screen_on
__basic_line_30:
__basic_line_40:
    ; Software-Sprite: 180 VIC-II-Bytes aktualisiert
    ; STA reducer: 74 Tabellenbytes statt ca. 600 Codebytes
    lda #<__basic_sta_reducer_table_1
    ldy #>__basic_sta_reducer_table_1
    jsr __basic_sta_reducer_apply
__basic_line_45:
    jsr __basic_soft_screen_wait
__basic_line_50:
    ; Software-Sprite: 188 VIC-II-Bytes aktualisiert
    ; STA reducer: 73 Tabellenbytes statt ca. 624 Codebytes
    lda #<__basic_sta_reducer_table_2
    ldy #>__basic_sta_reducer_table_2
    jsr __basic_sta_reducer_apply
__basic_line_55:
    jsr __basic_soft_screen_wait
__basic_line_60:
    ; Software-Sprite: 142 VIC-II-Bytes aktualisiert
    ; STA reducer: 33 Tabellenbytes statt ca. 436 Codebytes
    lda #<__basic_sta_reducer_table_3
    ldy #>__basic_sta_reducer_table_3
    jsr __basic_sta_reducer_apply
__basic_line_65:
    jsr __basic_soft_screen_wait
__basic_line_70:
    jsr __basic_soft_screen_off
__basic_line_80:
    rts
__basic_program_end:
    jsr $FFCC
    rts
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
    jsr __basic_soft_zero_clear
    rts
__basic_soft_zero_clear:
    lda #$60
    ldy #$20
    jsr __basic_soft_zero_pages
    lda #$44
    ldy #$04
    jsr __basic_soft_zero_pages
    lda #$D8
    ldy #$04
    jsr __basic_soft_zero_pages
    rts
__basic_soft_zero_pages:
    sta __basic_soft_zero_store+2
__basic_soft_zero_page:
    ldx #$00
    lda #$00
__basic_soft_zero_loop:
__basic_soft_zero_store:
    sta $6000,x
    inx
    bne __basic_soft_zero_loop
    inc __basic_soft_zero_store+2
    dey
    bne __basic_soft_zero_page
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
__basic_sta_reducer_apply:
    sta $FB
    sty $FC
__basic_sta_reducer_next:
    ldy #$00
    lda ($FB),y
    beq __basic_sta_reducer_done
    tax
    jsr __basic_sta_reducer_inc_src
    lda ($FB),y
    sta $FD
    jsr __basic_sta_reducer_inc_src
    lda ($FB),y
    sta $FE
    jsr __basic_sta_reducer_inc_src
    txa
    bmi __basic_sta_reducer_fill
__basic_sta_reducer_literal:
    lda ($FB),y
    sta ($FD),y
    jsr __basic_sta_reducer_inc_src
    jsr __basic_sta_reducer_inc_dst
    dex
    bne __basic_sta_reducer_literal
    jmp __basic_sta_reducer_next
__basic_sta_reducer_fill:
    eor #$FF
    tax
    inx
    lda ($FB),y
    sta __basic_sta_reducer_value
    jsr __basic_sta_reducer_inc_src
__basic_sta_reducer_fill_loop:
    lda __basic_sta_reducer_value
    sta ($FD),y
    jsr __basic_sta_reducer_inc_dst
    dex
    bne __basic_sta_reducer_fill_loop
    jmp __basic_sta_reducer_next
__basic_sta_reducer_inc_src:
    inc $FB
    bne __basic_sta_reducer_src_ok
    inc $FC
__basic_sta_reducer_src_ok:
    rts
__basic_sta_reducer_inc_dst:
    inc $FD
    bne __basic_sta_reducer_dst_ok
    inc $FE
__basic_sta_reducer_dst_ok:
    rts
__basic_sta_reducer_done:
    rts

; ---- STA reducer: komprimierte Lookup-Tabellen -------------------
__basic_sta_reducer_table_1:
    .byte $F8, $E8, $6C, $05, $E0, $F0, $6C, $5A, $F8, $10, $6D, $50, $F8, $20, $6E, $05, $D8, $28, $6E, $5A
    .byte $F8, $50, $6E, $50, $F8, $60, $6F, $05, $E8, $68, $6F, $5A, $F8, $80, $6F, $50, $F8, $88, $6F, $05
    .byte $F8, $90, $6F, $50, $06, $9D, $45, $10, $12, $23, $34, $45, $50, $07, $C4, $45, $60, $67, $78, $89
    .byte $9A, $AB, $B0, $07, $EC, $45, $C0, $CD, $DE, $EF, $F0, $10, $10, $00
__basic_sta_reducer_table_2:
    .byte $F8, $08, $6D, $55, $D8, $10, $6D, $5A, $F8, $38, $6D, $50, $F8, $48, $6E, $55, $D8, $50, $6E, $5A
    .byte $F8, $78, $6E, $50, $F8, $88, $6F, $00, $F8, $90, $6F, $05, $E0, $98, $6F, $5A, $F8, $B8, $6F, $50
    .byte $07, $A1, $45, $40, $45, $56, $67, $78, $89, $90, $07, $C9, $45, $A0, $AB, $BC, $CD, $DE, $EF, $F0
    .byte $01, $F1, $45, $00, $05, $F3, $45, $12, $23, $34, $45, $50, $00
__basic_sta_reducer_table_3:
    .byte $E0, $E8, $6C, $00, $F8, $08, $6D, $05, $D8, $20, $6E, $00, $F8, $48, $6E, $05, $D8, $60, $6F, $00
    .byte $FC, $9D, $45, $00, $FB, $C4, $45, $00, $FB, $EC, $45, $00, $00

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
__basic_sta_reducer_value: .cbss 1
__basic_soft_screen_active: .cbss 1
__basic_soft_old_bank: .cbss 1
__basic_soft_old_d011: .cbss 1
__basic_soft_old_d016: .cbss 1
__basic_soft_old_d018: .cbss 1
__basic_soft_old_d021: .cbss 1
__basic_cbss_end:
end
