; Von C erzeugter Motorola-68000-Assembler
; Ziel: Commodore Amiga 500 / AmigaOS HUNK_CODE
; Programm: hello_c
section code,code
xdef _start
_start:
    move.l 4.w,a6
    lea __c_dos_name(pc),a1
    moveq #0,d0
    jsr -552(a6)
    lea __c_dos_base(pc),a0
    move.l d0,(a0)
    tst.l d0
    beq __c_program_end
    move.l d0,a6
    jsr -60(a6)
    lea __c_output_handle(pc),a0
    move.l d0,(a0)
    move.w #$0005,d0
    move.w d0,-(sp)
    lea __pas_var_counter_0(pc),a0
    move.w (sp)+,d0
    move.w d0,d1
    lsr.w #8,d1
    move.b d1,(a0)+
    move.b d0,(a0)
    lea __c_string_0(pc),a0
    bsr __c_print_string
    lea __pas_var_counter_0(pc),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    bsr __c_print_int16
    lea __c_string_1(pc),a0
    bsr __c_print_string
    bra __c_program_end
    bra __c_program_end

__c_print_int16:
    move.w d0,d4
    lea __c_int_buffer_end(pc),a0
    clr.b -(a0)
    moveq #0,d2
    move.w d0,d2
    bpl __c_print_int_positive
    neg.w d2
__c_print_int_positive:
    moveq #10,d3
__c_print_int_loop:
    divu.w d3,d2
    swap d2
    addi.b #$30,d2
    move.b d2,-(a0)
    swap d2
    tst.w d2
    bne __c_print_int_loop
    tst.w d4
    bpl __c_print_int_write
    move.b #$2D,-(a0)
__c_print_int_write:
    bsr __c_print_string
    rts

; A0 = nullterminierte Latin-1-Zeichenkette
__c_print_string:
    move.l a0,a1
__c_print_string_loop:
    tst.b (a1)+
    bne __c_print_string_loop
    suba.l a0,a1
    subq.l #1,a1
    move.l a1,d3
    move.l a0,d2
    lea __c_output_handle(pc),a1
    move.l (a1),d1
    lea __c_dos_base(pc),a1
    move.l (a1),a6
    jsr -48(a6)
    rts

__c_program_end:
    moveq #0,d0
    rts

    even
; AmigaDOS-Laufzeitdaten
__c_dos_base: dc.l 0
__c_output_handle: dc.l 0
__c_char_buffer: dc.b 0,0
__c_int_buffer: ds.b 8
__c_int_buffer_end:

; C-Variablen
    even
__pas_var_counter_0: ds.b 2 ; counter: integer

; Nullterminierte Amiga-Latin-1-Zeichenketten
__c_string_0: dc.b $43, $6F, $75, $6E, $74, $65, $72, $20, $3D, $20, $00
__c_string_1: dc.b $0A, $00
__c_dos_name: dc.b $64,$6F,$73,$2E,$6C,$69,$62,$72,$61,$72,$79,$00
end
