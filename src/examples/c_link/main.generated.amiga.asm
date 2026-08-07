; Von C erzeugter Motorola-68000-Assembler
; Ziel: Commodore Amiga 500 / Standalone-Boot-ADF
; Runtime: direkte OCS-Register, keine Workbench-Libraries
; Programm: main
.bootable
section code,code
xdef _start
_start:
    move.l #$0007FFFC,sp
    bsr __c_screen_init
    bsr main
    bra __c_program_end

; C-Funktion main
xdef main
main:
    move.l a6,-(sp)
    move.l sp,a6
    suba.w #$0002,sp
    moveq #0,d0
    move.w d0,-(sp)
    lea -2(a6),a0
    move.w (sp)+,d0
    move.w d0,d1
    lsr.w #8,d1
    move.b d1,(a0)+
    move.b d0,(a0)
    move.w #$0014,d0
    move.w d0,-(sp)
    move.w #$001E,d0
    move.w d0,-(sp)
    bsr AddValues
    adda.w #$0004,sp
    move.w d0,-(sp)
    lea -2(a6),a0
    move.w (sp)+,d0
    move.w d0,d1
    lsr.w #8,d1
    move.b d1,(a0)+
    move.b d0,(a0)
    lea -2(a6),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    move.w d0,-(sp)
    move.w #$0000,d0
    move.w d0,-(sp)
    move.w #$0028,d0
    move.w d0,-(sp)
    bsr ClampValue
    adda.w #$0006,sp
    move.w d0,-(sp)
    lea -2(a6),a0
    move.w (sp)+,d0
    move.w d0,d1
    lsr.w #8,d1
    move.b d1,(a0)+
    move.b d0,(a0)
    bsr IncrementCounter
    bsr IncrementCounter
    lea __c_string_0(pc),a0
    bsr __c_print_string
    lea -2(a6),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    bsr __c_print_int16
    lea __c_string_1(pc),a0
    bsr __c_print_string
    bsr GetCounter
    bsr __c_print_int16
    lea __c_string_2(pc),a0
    bsr __c_print_string
    move.w #$0000,d0
    bra __c_return_main_1
    moveq #0,d0
__c_return_main_1:
    move.l a6,sp
    move.l (sp)+,a6
    rts

; Wartet auf den sicheren unteren Vertical-Blank-Bereich
__c_wait_safe_line:
    move.l #$00DFF000,a0
__c_wait_safe_line_loop:
    move.w $0006(a0),d0 ; VHPOSR
    andi.w #$FF00,d0
    cmpi.w #$F500,d0
    bcs __c_wait_safe_line_loop
    rts

; Copper-Liste bei $10000 lädt den Text-Bitplane-Zeiger in jedem Frame neu
__c_install_text_copper:
    move.l #$00010000,a1
    move.l #$008E2C81,(a1)+
    move.l #$0090F4C1,(a1)+
    move.l #$00920038,(a1)+
    move.l #$009400D0,(a1)+
    move.l #$01001200,(a1)+
    move.l #$01020000,(a1)+
    move.l #$01040000,(a1)+
    move.l #$01080000,(a1)+
    move.l #$010A0000,(a1)+
    move.l #$00E00001,(a1)+
    move.l #$00E28000,(a1)+
    move.l #$01800000,(a1)+
    move.l #$018200F0,(a1)+
    move.l #$FFFFFFFE,(a1)+
    rts

; Direkte OCS-Bildschirminitialisierung, 320x200, 1 Bitplane
__c_screen_init:
    bsr __c_wait_safe_line
    move.l #$00DFF000,a0
    move.w #$7FFF,$009A(a0) ; INTENA: Interrupts aus
    move.w #$7FFF,$0096(a0) ; DMACON: DMA aus
    bsr __c_clear_screen
    bsr __c_install_text_copper
    move.l #$00DFF000,a0
    move.l #$00010000,d0
    move.l d0,$0080(a0) ; COP1LCH/COP1LCL
    move.w #$0000,$0088(a0) ; COPJMP1
    move.w #$8380,$0096(a0) ; SET+DMAEN+BPLEN+COPEN
    rts
; Löscht 8000 Bytes Text-Bitplane-RAM und setzt den Cursor zurück
__c_clear_screen:
    move.l #$00018000,a0
    move.w #$07D0,d0
__c_clear_screen_loop:
    clr.l (a0)+
    subq.w #1,d0
    bne __c_clear_screen_loop
    lea __c_cursor_x(pc),a0
    clr.b (a0)
    lea __c_cursor_y(pc),a0
    clr.b (a0)
    rts

; D0.B = ASCII-Zeichen, Ausgabe als 8x8-Bitmaske
__c_print_char:
    cmpi.w #$000A,d0
    beq __c_print_char_newline
    cmpi.w #$000D,d0
    beq __c_print_char_newline
    cmpi.w #$0019,d0
    bcs __c_print_char_substitute
    cmpi.w #$007F,d0
    bcs __c_print_char_glyph
__c_print_char_substitute:
    move.w #$003F,d0
__c_print_char_glyph:
    subi.w #$0020,d0
    mulu.w #$0008,d0
    lea __c_font_8x8(pc),a2
    adda.w d0,a2
    lea __c_cursor_y(pc),a1
    moveq #0,d1
    move.b (a1),d1
    mulu.w #$0140,d1
    move.l #$00018000,a1
    adda.l d1,a1
    lea __c_cursor_x(pc),a0
    moveq #0,d1
    move.b (a0),d1
    adda.w d1,a1
    move.b (a2)+,(a1)
    adda.w #$0028,a1
    move.b (a2)+,(a1)
    adda.w #$0028,a1
    move.b (a2)+,(a1)
    adda.w #$0028,a1
    move.b (a2)+,(a1)
    adda.w #$0028,a1
    move.b (a2)+,(a1)
    adda.w #$0028,a1
    move.b (a2)+,(a1)
    adda.w #$0028,a1
    move.b (a2)+,(a1)
    adda.w #$0028,a1
    move.b (a2)+,(a1)
    adda.w #$0028,a1
    lea __c_cursor_x(pc),a0
    addq.b #1,(a0)
    moveq #0,d0
    move.b (a0),d0
    cmpi.w #$0028,d0
    bcs __c_print_char_done
__c_print_char_newline:
    lea __c_cursor_x(pc),a0
    clr.b (a0)
    lea __c_cursor_y(pc),a0
    addq.b #1,(a0)
    moveq #0,d0
    move.b (a0),d0
    cmpi.w #$0019,d0
    bcs __c_print_char_done
    bsr __c_clear_screen
__c_print_char_done:
    rts

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
    move.l a0,a3
__c_print_string_loop:
    moveq #0,d0
    move.b (a3)+,d0
    beq __c_print_string_done
    bsr __c_print_char
    bra __c_print_string_loop
__c_print_string_done:
    rts

__c_program_end:
    bra __c_program_end

    even
; Direkte Amiga-Bildschirmlaufzeitdaten
__c_cursor_x: dc.b 0
__c_cursor_y: dc.b 0
__c_int_buffer: ds.b 8
__c_int_buffer_end:

; Nullterminierte Amiga-Latin-1-Zeichenketten
__c_string_0: dc.b $76, $61, $6C, $75, $65, $3D, $00
__c_string_1: dc.b $20, $63, $6F, $75, $6E, $74, $65, $72, $3D, $00
__c_string_2: dc.b $0A, $00

; 96 Glyphen, ASCII $20..$7F, je 8 Bytes
__c_font_8x8:
    dc.b $00, $00, $00, $00, $00, $00, $00, $00, $18, $18, $18, $18, $00, $00, $18, $00
    dc.b $66, $66, $66, $00, $00, $00, $00, $00, $66, $66, $FF, $66, $FF, $66, $66, $00
    dc.b $18, $3E, $60, $3C, $06, $7C, $18, $00, $62, $66, $0C, $18, $30, $66, $46, $00
    dc.b $3C, $66, $3C, $38, $67, $66, $3F, $00, $06, $0C, $18, $00, $00, $00, $00, $00
    dc.b $0C, $18, $30, $30, $30, $18, $0C, $00, $30, $18, $0C, $0C, $0C, $18, $30, $00
    dc.b $00, $66, $3C, $FF, $3C, $66, $00, $00, $00, $18, $18, $7E, $18, $18, $00, $00
    dc.b $00, $00, $00, $00, $00, $18, $18, $30, $00, $00, $00, $7E, $00, $00, $00, $00
    dc.b $00, $00, $00, $00, $00, $18, $18, $00, $00, $03, $06, $0C, $18, $30, $60, $00
    dc.b $3C, $66, $6E, $76, $66, $66, $3C, $00, $18, $18, $38, $18, $18, $18, $7E, $00
    dc.b $3C, $66, $06, $0C, $30, $60, $7E, $00, $3C, $66, $06, $1C, $06, $66, $3C, $00
    dc.b $06, $0E, $1E, $66, $7F, $06, $06, $00, $7E, $60, $7C, $06, $06, $66, $3C, $00
    dc.b $3C, $66, $60, $7C, $66, $66, $3C, $00, $7E, $66, $0C, $18, $18, $18, $18, $00
    dc.b $3C, $66, $66, $3C, $66, $66, $3C, $00, $3C, $66, $66, $3E, $06, $66, $3C, $00
    dc.b $00, $00, $18, $00, $00, $18, $00, $00, $00, $00, $18, $00, $00, $18, $18, $30
    dc.b $0E, $18, $30, $60, $30, $18, $0E, $00, $00, $00, $7E, $00, $7E, $00, $00, $00
    dc.b $70, $18, $0C, $06, $0C, $18, $70, $00, $3C, $66, $06, $0C, $18, $00, $18, $00
    dc.b $3C, $66, $6E, $6E, $60, $62, $3C, $00, $18, $3C, $66, $7E, $66, $66, $66, $00
    dc.b $7C, $66, $66, $7C, $66, $66, $7C, $00, $3C, $66, $60, $60, $60, $66, $3C, $00
    dc.b $78, $6C, $66, $66, $66, $6C, $78, $00, $7E, $60, $60, $78, $60, $60, $7E, $00
    dc.b $7E, $60, $60, $78, $60, $60, $60, $00, $3C, $66, $60, $6E, $66, $66, $3C, $00
    dc.b $66, $66, $66, $7E, $66, $66, $66, $00, $3C, $18, $18, $18, $18, $18, $3C, $00
    dc.b $1E, $0C, $0C, $0C, $0C, $6C, $38, $00, $66, $6C, $78, $70, $78, $6C, $66, $00
    dc.b $60, $60, $60, $60, $60, $60, $7E, $00, $63, $77, $7F, $6B, $63, $63, $63, $00
    dc.b $66, $76, $7E, $7E, $6E, $66, $66, $00, $3C, $66, $66, $66, $66, $66, $3C, $00
    dc.b $7C, $66, $66, $7C, $60, $60, $60, $00, $3C, $66, $66, $66, $66, $3C, $0E, $00
    dc.b $7C, $66, $66, $7C, $78, $6C, $66, $00, $3C, $66, $60, $3C, $06, $66, $3C, $00
    dc.b $7E, $18, $18, $18, $18, $18, $18, $00, $66, $66, $66, $66, $66, $66, $3C, $00
    dc.b $66, $66, $66, $66, $66, $3C, $18, $00, $63, $63, $63, $6B, $7F, $77, $63, $00
    dc.b $66, $66, $3C, $18, $3C, $66, $66, $00, $66, $66, $66, $3C, $18, $18, $18, $00
    dc.b $7E, $06, $0C, $18, $30, $60, $7E, $00, $3C, $30, $30, $30, $30, $30, $3C, $00
    dc.b $00, $60, $30, $18, $0C, $06, $03, $00, $3C, $0C, $0C, $0C, $0C, $0C, $3C, $00
    dc.b $08, $1C, $36, $63, $41, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $FF
    dc.b $20, $10, $08, $00, $00, $00, $00, $00, $00, $00, $3C, $06, $3E, $66, $3E, $00
    dc.b $00, $60, $60, $7C, $66, $66, $7C, $00, $00, $00, $3C, $60, $60, $60, $3C, $00
    dc.b $00, $06, $06, $3E, $66, $66, $3E, $00, $00, $00, $3C, $66, $7E, $60, $3C, $00
    dc.b $00, $0E, $18, $3E, $18, $18, $18, $00, $00, $00, $3E, $66, $66, $3E, $06, $7C
    dc.b $00, $60, $60, $7C, $66, $66, $66, $00, $00, $18, $00, $38, $18, $18, $3C, $00
    dc.b $00, $06, $00, $06, $06, $06, $06, $3C, $00, $60, $60, $6C, $78, $6C, $66, $00
    dc.b $00, $38, $18, $18, $18, $18, $3C, $00, $00, $00, $66, $7F, $7F, $6B, $63, $00
    dc.b $00, $00, $7C, $66, $66, $66, $66, $00, $00, $00, $3C, $66, $66, $66, $3C, $00
    dc.b $00, $00, $7C, $66, $66, $7C, $60, $60, $00, $00, $3E, $66, $66, $3E, $06, $06
    dc.b $00, $00, $7C, $66, $60, $60, $60, $00, $00, $00, $3E, $60, $3C, $06, $7C, $00
    dc.b $00, $18, $7E, $18, $18, $18, $0E, $00, $00, $00, $66, $66, $66, $66, $3E, $00
    dc.b $00, $00, $66, $66, $66, $3C, $18, $00, $00, $00, $63, $6B, $7F, $3E, $36, $00
    dc.b $00, $00, $66, $3C, $18, $3C, $66, $00, $00, $00, $66, $66, $66, $3E, $0C, $78
    dc.b $00, $00, $7E, $0C, $18, $30, $7E, $00, $0C, $18, $18, $30, $18, $18, $0C, $00
    dc.b $18, $18, $18, $18, $18, $18, $18, $18, $30, $18, $18, $0C, $18, $18, $30, $00
    dc.b $00, $00, $00, $39, $4E, $00, $00, $00, $00, $7E, $42, $42, $42, $42, $7E, $00

; --- separat kompiliertes C-Modul: math_module.c ---
; Separat kompiliertes C-Modul fuer Motorola 68000
; Quelldatei: T:\GitHub\dBase2Many\src\asmjit\compiler\frontend\c64\examples\c_link\math_module.c
section code,code

; C-Funktion AddValues
xdef AddValues
AddValues:
    move.l a6,-(sp)
    move.l sp,a6
    lea 10(a6),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    move.w d0,-(sp)
    lea 8(a6),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    move.w d0,d1
    move.w (sp)+,d0
    add.w d1,d0
    bra __cmod_math_module_f3ba77a5_return_addvalues_1
    moveq #0,d0
__cmod_math_module_f3ba77a5_return_addvalues_1:
    move.l a6,sp
    move.l (sp)+,a6
    rts

; C-Funktion ClampValue
xdef ClampValue
ClampValue:
    move.l a6,-(sp)
    move.l sp,a6
    lea 12(a6),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    move.w d0,-(sp)
    lea 10(a6),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    move.w d0,d1
    move.w (sp)+,d0
    cmp.w d1,d0
    blt __cmod_math_module_f3ba77a5_cmp_true_7
    moveq #0,d0
    bra __cmod_math_module_f3ba77a5_cmp_end_8
__cmod_math_module_f3ba77a5_cmp_true_7:
    moveq #1,d0
__cmod_math_module_f3ba77a5_cmp_end_8:
    tst.w d0
    beq __cmod_math_module_f3ba77a5_if_else_5
    lea 10(a6),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    bra __cmod_math_module_f3ba77a5_return_clampvalue_2
    jmp __cmod_math_module_f3ba77a5_if_end_6
__cmod_math_module_f3ba77a5_if_else_5:
__cmod_math_module_f3ba77a5_if_end_6:
    lea 12(a6),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    move.w d0,-(sp)
    lea 8(a6),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    move.w d0,d1
    move.w (sp)+,d0
    cmp.w d1,d0
    bgt __cmod_math_module_f3ba77a5_cmp_true_11
    moveq #0,d0
    bra __cmod_math_module_f3ba77a5_cmp_end_12
__cmod_math_module_f3ba77a5_cmp_true_11:
    moveq #1,d0
__cmod_math_module_f3ba77a5_cmp_end_12:
    tst.w d0
    beq __cmod_math_module_f3ba77a5_if_else_9
    lea 8(a6),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    bra __cmod_math_module_f3ba77a5_return_clampvalue_2
    jmp __cmod_math_module_f3ba77a5_if_end_10
__cmod_math_module_f3ba77a5_if_else_9:
__cmod_math_module_f3ba77a5_if_end_10:
    lea 12(a6),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    bra __cmod_math_module_f3ba77a5_return_clampvalue_2
    moveq #0,d0
__cmod_math_module_f3ba77a5_return_clampvalue_2:
    move.l a6,sp
    move.l (sp)+,a6
    rts

; C-Funktion IncrementCounter
xdef IncrementCounter
IncrementCounter:
    move.l a6,-(sp)
    move.l sp,a6
    lea __cmod_math_module_f3ba77a5_var_module_counter_0(pc),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    move.w d0,-(sp)
    move.w #$0001,d0
    move.w d0,d1
    move.w (sp)+,d0
    add.w d1,d0
    move.w d0,-(sp)
    lea __cmod_math_module_f3ba77a5_var_module_counter_0(pc),a0
    move.w (sp)+,d0
    move.w d0,d1
    lsr.w #8,d1
    move.b d1,(a0)+
    move.b d0,(a0)
__cmod_math_module_f3ba77a5_return_incrementcounter_3:
    move.l a6,sp
    move.l (sp)+,a6
    rts

; C-Funktion GetCounter
xdef GetCounter
GetCounter:
    move.l a6,-(sp)
    move.l sp,a6
    lea __cmod_math_module_f3ba77a5_var_module_counter_0(pc),a0
    moveq #0,d0
    move.b (a0)+,d0
    lsl.w #8,d0
    move.b (a0),d0
    bra __cmod_math_module_f3ba77a5_return_getcounter_4
    moveq #0,d0
__cmod_math_module_f3ba77a5_return_getcounter_4:
    move.l a6,sp
    move.l (sp)+,a6
    rts

; Wartet auf den sicheren unteren Vertical-Blank-Bereich
__cmod_math_module_f3ba77a5_wait_safe_line:
    move.l #$00DFF000,a0
__cmod_math_module_f3ba77a5_wait_safe_line_loop:
    move.w $0006(a0),d0 ; VHPOSR
    andi.w #$FF00,d0
    cmpi.w #$F500,d0
    bcs __cmod_math_module_f3ba77a5_wait_safe_line_loop
    rts

; Copper-Liste bei $10000 lädt den Text-Bitplane-Zeiger in jedem Frame neu
__cmod_math_module_f3ba77a5_install_text_copper:
    move.l #$00010000,a1
    move.l #$008E2C81,(a1)+
    move.l #$0090F4C1,(a1)+
    move.l #$00920038,(a1)+
    move.l #$009400D0,(a1)+
    move.l #$01001200,(a1)+
    move.l #$01020000,(a1)+
    move.l #$01040000,(a1)+
    move.l #$01080000,(a1)+
    move.l #$010A0000,(a1)+
    move.l #$00E00001,(a1)+
    move.l #$00E28000,(a1)+
    move.l #$01800000,(a1)+
    move.l #$018200F0,(a1)+
    move.l #$FFFFFFFE,(a1)+
    rts

; Direkte OCS-Bildschirminitialisierung, 320x200, 1 Bitplane
__cmod_math_module_f3ba77a5_screen_init:
    bsr __cmod_math_module_f3ba77a5_wait_safe_line
    move.l #$00DFF000,a0
    move.w #$7FFF,$009A(a0) ; INTENA: Interrupts aus
    move.w #$7FFF,$0096(a0) ; DMACON: DMA aus
    bsr __cmod_math_module_f3ba77a5_clear_screen
    bsr __cmod_math_module_f3ba77a5_install_text_copper
    move.l #$00DFF000,a0
    move.l #$00010000,d0
    move.l d0,$0080(a0) ; COP1LCH/COP1LCL
    move.w #$0000,$0088(a0) ; COPJMP1
    move.w #$8380,$0096(a0) ; SET+DMAEN+BPLEN+COPEN
    rts
; Löscht 8000 Bytes Text-Bitplane-RAM und setzt den Cursor zurück
__cmod_math_module_f3ba77a5_clear_screen:
    move.l #$00018000,a0
    move.w #$07D0,d0
__cmod_math_module_f3ba77a5_clear_screen_loop:
    clr.l (a0)+
    subq.w #1,d0
    bne __cmod_math_module_f3ba77a5_clear_screen_loop
    lea __cmod_math_module_f3ba77a5_cursor_x(pc),a0
    clr.b (a0)
    lea __cmod_math_module_f3ba77a5_cursor_y(pc),a0
    clr.b (a0)
    rts

    even
; Direkte Amiga-Bildschirmlaufzeitdaten
__cmod_math_module_f3ba77a5_cursor_x: dc.b 0
__cmod_math_module_f3ba77a5_cursor_y: dc.b 0
__cmod_math_module_f3ba77a5_int_buffer: ds.b 8
__cmod_math_module_f3ba77a5_int_buffer_end:

; C-Variablen
    even
__cmod_math_module_f3ba77a5_var_module_counter_0: ds.b 2 ; module_counter: integer

end
