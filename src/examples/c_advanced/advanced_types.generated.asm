; Von C64 C erzeugter MOS-6510-Assembler
; Programm: advanced_types
.org $080D
.entry __c_start
.basic

__c_start:
    lda #$0E
    jsr $FFD2
    jsr main
__c_program_end:
    rts

; C-Funktion main
main:
    lda __c_frame_pointer
    pha
    tsx
    stx __c_frame_pointer
    lda #$00
    pha
    pha
    pha
    pha
    pha
    pha
    pha
    pha
    pha
    pha
    pha
    pha
    pha
    lda #$00
    ldx #$00
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00FE,x
    lda $FA
    sta $00FF,x
    lda $F9
    ldx $FA
    lda #$00
    ldx #$00
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00FC,x
    lda $FA
    sta $00FD,x
    lda $F9
    ldx $FA
    lda #$00
    ldx #$00
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00FA,x
    lda $FA
    sta $00FB,x
    lda $F9
    ldx $FA
    lda #$00
    ldx #$00
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00F8,x
    lda $FA
    sta $00F9,x
    lda $F9
    ldx $FA
    lda #$00
    ldx #$00
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00F6,x
    lda $FA
    sta $00F7,x
    lda $F9
    ldx $FA
    lda #$00
    ldx #$00
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00F4,x
    lda $FA
    sta $00F5,x
    lda $F9
    ldx $FA
    lda #$03
    ldx #$00
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00FE,x
    lda $FA
    sta $00FF,x
    lda $F9
    ldx $FA
    lda #$03
    ldx #$00
    pha
    txa
    pha
    lda #$03
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
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00FC,x
    lda $FA
    sta $00FD,x
    lda $F9
    ldx $FA
    lda #$0A
    ldx #$00
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00FA,x
    lda $FA
    sta $00FB,x
    lda $F9
    ldx $FA
    jsr SetEmpty
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00F8,x
    lda $FA
    sta $00F9,x
    lda $F9
    ldx $FA
    ldx __c_frame_pointer
    lda $00F8,x
    sta $F9
    lda $00F9,x
    tax
    lda $F9
    sta $F9
    txa
    pha
    lda $F9
    pha
    lda #$01
    ldx #$00
    sta $F9
    txa
    pha
    lda $F9
    pha
    jsr SetAdd
    sta $F9
    stx $FA
    tsx
    txa
    clc
    adc #$04
    tax
    txs
    lda $F9
    ldx $FA
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00F8,x
    lda $FA
    sta $00F9,x
    lda $F9
    ldx $FA
    ldx __c_frame_pointer
    lda $00F8,x
    sta $F9
    lda $00F9,x
    tax
    lda $F9
    sta $F9
    txa
    pha
    lda $F9
    pha
    lda #$03
    ldx #$00
    sta $F9
    txa
    pha
    lda $F9
    pha
    jsr SetAdd
    sta $F9
    stx $FA
    tsx
    txa
    clc
    adc #$04
    tax
    txs
    lda $F9
    ldx $FA
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00F8,x
    lda $FA
    sta $00F9,x
    lda $F9
    ldx $FA
    ldx __c_frame_pointer
    lda $00FE,x
    sta $F9
    lda $00FF,x
    tax
    lda $F9
    pha
    txa
    pha
    ldx __c_frame_pointer
    lda $00FC,x
    sta $F9
    lda $00FD,x
    tax
    lda $F9
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
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00F4,x
    lda $FA
    sta $00F5,x
    lda $F9
    ldx $FA
    lda #<__c_string_0
    ldx #>__c_string_0
    jsr __c_print_string
    ldx __c_frame_pointer
    lda $00F4,x
    sta $F9
    lda $00F5,x
    tax
    lda $F9
    jsr __c_print_int16
    lda #<__c_string_1
    ldx #>__c_string_1
    jsr __c_print_string
    lda #$05
    ldx #$00
    sta $F9
    txa
    pha
    lda $F9
    pha
    jsr Factorial
    sta $F9
    stx $FA
    tsx
    txa
    clc
    adc #$02
    tax
    txs
    lda $F9
    ldx $FA
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00F6,x
    lda $FA
    sta $00F7,x
    lda $F9
    ldx $FA
    lda #<__c_string_2
    ldx #>__c_string_2
    jsr __c_print_string
    ldx __c_frame_pointer
    lda $00F6,x
    sta $F9
    lda $00F7,x
    tax
    lda $F9
    jsr __c_print_int16
    lda #<__c_string_1
    ldx #>__c_string_1
    jsr __c_print_string
    lda #<__c_string_3
    ldx #>__c_string_3
    jsr __c_print_string
    jsr PersistentCounter
    jsr __c_print_int16
    lda #<__c_string_4
    ldx #>__c_string_4
    jsr __c_print_string
    jsr PersistentCounter
    jsr __c_print_int16
    lda #<__c_string_1
    ldx #>__c_string_1
    jsr __c_print_string
    lda #<__c_string_5
    ldx #>__c_string_5
    jsr __c_print_string
    ldx __c_frame_pointer
    lda $00F8,x
    sta $F9
    lda $00F9,x
    tax
    lda $F9
    sta $F9
    txa
    pha
    lda $F9
    pha
    lda #$03
    ldx #$00
    sta $F9
    txa
    pha
    lda $F9
    pha
    jsr SetContains
    sta $F9
    stx $FA
    tsx
    txa
    clc
    adc #$04
    tax
    txs
    lda $F9
    ldx $FA
    jsr __c_print_int16
    lda #<__c_string_1
    ldx #>__c_string_1
    jsr __c_print_string
    lda #<__c_string_6
    ldx #>__c_string_6
    jsr __c_print_string
    ldx __c_frame_pointer
    lda $00FA,x
    sta $F9
    lda $00FB,x
    tax
    lda $F9
    jsr __c_print_int16
    lda #<__c_string_1
    ldx #>__c_string_1
    jsr __c_print_string
    lda #$00
    ldx #$00
    jmp __c_return_main_1
    lda #$00
    ldx #$00
__c_return_main_1:
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    txs
    pla
    sta __c_frame_pointer
    lda $F9
    ldx $FA
    rts

; A/X = Adresse einer nullterminierten PETSCII-Zeichenkette
__c_print_string:
    sta $FB
    stx $FC
__c_print_string_loop:
    ldy #$00
    lda ($FB),y
    beq __c_print_string_done
    jsr $FFD2
    inc $FB
    bne __c_print_string_loop
    inc $FC
    jmp __c_print_string_loop
__c_print_string_done:
    rts

; unsigned 16-Bit DIV/MOD: $FB/$FC durch $FD/$FE
__c_div16:
    lda #$00
    sta __c_rt_mode
    jmp __c_divmod16
__c_mod16:
    lda #$01
    sta __c_rt_mode
__c_divmod16:
    lda $FD
    ora $FE
    bne __c_divmod_nonzero
    lda #$00
    tax
    rts
__c_divmod_nonzero:
    lda #$00
    sta __c_rt_remainder
    sta __c_rt_remainder+1
    ldx #$10
__c_divmod_loop:
    asl $FB
    rol $FC
    rol __c_rt_remainder
    rol __c_rt_remainder+1
    lda __c_rt_remainder+1
    cmp $FE
    bcc __c_divmod_next
    bne __c_divmod_subtract
    lda __c_rt_remainder
    cmp $FD
    bcc __c_divmod_next
__c_divmod_subtract:
    sec
    lda __c_rt_remainder
    sbc $FD
    sta __c_rt_remainder
    lda __c_rt_remainder+1
    sbc $FE
    sta __c_rt_remainder+1
    inc $FB
__c_divmod_next:
    dex
    bne __c_divmod_loop
    lda __c_rt_mode
    bne __c_divmod_return_remainder
    lda $FB
    ldx $FC
    rts
__c_divmod_return_remainder:
    lda __c_rt_remainder
    ldx __c_rt_remainder+1
    rts

; A/X = vorzeichenbehaftete 16-Bit-Zahl
__c_print_int16:
    sta $FB
    stx $FC
    txa
    bpl __c_print_int16_positive
    lda #$2D
    jsr $FFD2
    lda #$00
    sec
    sbc $FB
    sta __c_rt_value
    lda #$00
    sbc $FC
    sta $FC
    lda __c_rt_value
    sta $FB
__c_print_int16_positive:
    lda $FB
    ora $FC
    bne __c_print_int16_convert
    lda #$30
    jsr $FFD2
    rts
__c_print_int16_convert:
    lda #$00
    sta __c_rt_count
__c_print_int16_divide:
    lda #$0A
    sta $FD
    lda #$00
    sta $FE
    jsr __c_div16
    sta $FB
    stx $FC
    lda __c_rt_remainder
    pha
    inc __c_rt_count
    lda $FB
    ora $FC
    bne __c_print_int16_divide
; Ziffern wurden auf dem Hardware-Stack abgelegt
__c_print_int16_digits:
    pla
    clc
    adc #$30
    jsr $FFD2
    dec __c_rt_count
    bne __c_print_int16_digits
    rts

; Compiler-Laufzeitdaten
__c_rt_value:      .word 0
__c_rt_remainder:  .word 0
__c_rt_count:      .byte 0
__c_rt_mode:       .byte 0

; Nullterminierte PETSCII-Zeichenketten
__c_string_0: .byte $49, $4E, $4E, $45, $52, $3D, $00
__c_string_1: .byte $0D, $00
__c_string_2: .byte $46, $41, $43, $54, $4F, $52, $49, $41, $4C, $3D, $00
__c_string_3: .byte $53, $54, $41, $54, $49, $43, $3D, $00
__c_string_4: .byte $2C, $00
__c_string_5: .byte $53, $45, $54, $3D, $00
__c_string_6: .byte $53, $54, $52, $55, $43, $54, $3D, $00

; C-Stackframe-Zeiger
__c_frame_pointer: .byte 0

; --- separat kompiliertes C-Modul: set_runtime.c ---
; Separat kompiliertes C-Modul fuer MOS 6510
; Quelldatei: T:\GitHub\dBase2Many\src\asmjit\compiler\frontend\c64\c64c\runtime\set_runtime.c

; C-Funktion SetEmpty
SetEmpty:
    lda __cmod_set_runtime_0c6f687a_frame_pointer
    pha
    tsx
    stx __cmod_set_runtime_0c6f687a_frame_pointer
    lda #$00
    ldx #$00
    jmp __cmod_set_runtime_0c6f687a_return_setempty_1
    lda #$00
    ldx #$00
__cmod_set_runtime_0c6f687a_return_setempty_1:
    sta $F9
    stx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    txs
    pla
    sta __cmod_set_runtime_0c6f687a_frame_pointer
    lda $F9
    ldx $FA
    rts

; C-Funktion SetOf
SetOf:
    lda __cmod_set_runtime_0c6f687a_frame_pointer
    pha
    tsx
    stx __cmod_set_runtime_0c6f687a_frame_pointer
    lda #$00
    pha
    pha
    pha
    lda #$00
    ldx #$00
    sta $F9
    stx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $F9
    sta $00FE,x
    lda $FA
    sta $00FF,x
    lda $F9
    ldx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
    pha
    txa
    pha
    lda #$00
    ldx #$00
    sta $FD
    stx $FE
    pla
    tax
    pla
    sta $FB
    stx $FC
    txa
    eor $FE
    bpl __cmod_set_runtime_0c6f687a_cmp_order_16
    lda $FC
    bmi __cmod_set_runtime_0c6f687a_cmp_less_14
    jmp __cmod_set_runtime_0c6f687a_cmp_greater_15
__cmod_set_runtime_0c6f687a_cmp_order_16:
    ldx $FC
    cpx $FE
    bcc __cmod_set_runtime_0c6f687a_cmp_less_14
    bne __cmod_set_runtime_0c6f687a_cmp_greater_15
    lda $FB
    cmp $FD
    bcc __cmod_set_runtime_0c6f687a_cmp_less_14
    bne __cmod_set_runtime_0c6f687a_cmp_greater_15
    jmp __cmod_set_runtime_0c6f687a_cmp_false_12
__cmod_set_runtime_0c6f687a_cmp_less_14:
    jmp __cmod_set_runtime_0c6f687a_cmp_true_11
__cmod_set_runtime_0c6f687a_cmp_greater_15:
    jmp __cmod_set_runtime_0c6f687a_cmp_false_12
__cmod_set_runtime_0c6f687a_cmp_false_12:
    lda #$00
    ldx #$00
    jmp __cmod_set_runtime_0c6f687a_cmp_end_13
__cmod_set_runtime_0c6f687a_cmp_true_11:
    lda #$01
    ldx #$00
__cmod_set_runtime_0c6f687a_cmp_end_13:
    pha
    txa
    pha
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
    pha
    txa
    pha
    lda #$0F
    ldx #$00
    sta $FD
    stx $FE
    pla
    tax
    pla
    sta $FB
    stx $FC
    txa
    eor $FE
    bpl __cmod_set_runtime_0c6f687a_cmp_order_22
    lda $FC
    bmi __cmod_set_runtime_0c6f687a_cmp_less_20
    jmp __cmod_set_runtime_0c6f687a_cmp_greater_21
__cmod_set_runtime_0c6f687a_cmp_order_22:
    ldx $FC
    cpx $FE
    bcc __cmod_set_runtime_0c6f687a_cmp_less_20
    bne __cmod_set_runtime_0c6f687a_cmp_greater_21
    lda $FB
    cmp $FD
    bcc __cmod_set_runtime_0c6f687a_cmp_less_20
    bne __cmod_set_runtime_0c6f687a_cmp_greater_21
    jmp __cmod_set_runtime_0c6f687a_cmp_false_18
__cmod_set_runtime_0c6f687a_cmp_less_20:
    jmp __cmod_set_runtime_0c6f687a_cmp_false_18
__cmod_set_runtime_0c6f687a_cmp_greater_21:
    jmp __cmod_set_runtime_0c6f687a_cmp_true_17
__cmod_set_runtime_0c6f687a_cmp_false_18:
    lda #$00
    ldx #$00
    jmp __cmod_set_runtime_0c6f687a_cmp_end_19
__cmod_set_runtime_0c6f687a_cmp_true_17:
    lda #$01
    ldx #$00
__cmod_set_runtime_0c6f687a_cmp_end_19:
    sta $FD
    stx $FE
    pla
    tax
    pla
    ora $FD
    sta $FB
    txa
    ora $FE
    tax
    lda $FB
    sta $FB
    txa
    ora $FB
    bne __cmod_set_runtime_0c6f687a_condition_true_23
    jmp __cmod_set_runtime_0c6f687a_if_else_9
__cmod_set_runtime_0c6f687a_condition_true_23:
    lda #$00
    ldx #$00
    jmp __cmod_set_runtime_0c6f687a_return_setof_2
    jmp __cmod_set_runtime_0c6f687a_if_end_10
__cmod_set_runtime_0c6f687a_if_else_9:
__cmod_set_runtime_0c6f687a_if_end_10:
    lda #$01
    ldx #$00
    sta $F9
    stx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $F9
    sta $00FE,x
    lda $FA
    sta $00FF,x
    lda $F9
    ldx $FA
__cmod_set_runtime_0c6f687a_while_condition_24:
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
    pha
    txa
    pha
    lda #$00
    ldx #$00
    sta $FD
    stx $FE
    pla
    tax
    pla
    sta $FB
    stx $FC
    txa
    eor $FE
    bpl __cmod_set_runtime_0c6f687a_cmp_order_31
    lda $FC
    bmi __cmod_set_runtime_0c6f687a_cmp_less_29
    jmp __cmod_set_runtime_0c6f687a_cmp_greater_30
__cmod_set_runtime_0c6f687a_cmp_order_31:
    ldx $FC
    cpx $FE
    bcc __cmod_set_runtime_0c6f687a_cmp_less_29
    bne __cmod_set_runtime_0c6f687a_cmp_greater_30
    lda $FB
    cmp $FD
    bcc __cmod_set_runtime_0c6f687a_cmp_less_29
    bne __cmod_set_runtime_0c6f687a_cmp_greater_30
    jmp __cmod_set_runtime_0c6f687a_cmp_false_27
__cmod_set_runtime_0c6f687a_cmp_less_29:
    jmp __cmod_set_runtime_0c6f687a_cmp_false_27
__cmod_set_runtime_0c6f687a_cmp_greater_30:
    jmp __cmod_set_runtime_0c6f687a_cmp_true_26
__cmod_set_runtime_0c6f687a_cmp_false_27:
    lda #$00
    ldx #$00
    jmp __cmod_set_runtime_0c6f687a_cmp_end_28
__cmod_set_runtime_0c6f687a_cmp_true_26:
    lda #$01
    ldx #$00
__cmod_set_runtime_0c6f687a_cmp_end_28:
    sta $FB
    txa
    ora $FB
    bne __cmod_set_runtime_0c6f687a_condition_true_32
    jmp __cmod_set_runtime_0c6f687a_while_end_25
__cmod_set_runtime_0c6f687a_condition_true_32:
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $00FE,x
    sta $F9
    lda $00FF,x
    tax
    lda $F9
    pha
    txa
    pha
    lda #$02
    ldx #$00
    sta $FD
    stx $FE
    pla
    tax
    pla
    sta $FB
    stx $FC
    jsr __cmod_set_runtime_0c6f687a_mul16
    sta $F9
    stx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $F9
    sta $00FE,x
    lda $FA
    sta $00FF,x
    lda $F9
    ldx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
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
    sec
    sbc $FD
    sta $FB
    txa
    sbc $FE
    tax
    lda $FB
    sta $F9
    stx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $F9
    sta $0104,x
    lda $FA
    sta $0105,x
    lda $F9
    ldx $FA
    jmp __cmod_set_runtime_0c6f687a_while_condition_24
__cmod_set_runtime_0c6f687a_while_end_25:
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $00FE,x
    sta $F9
    lda $00FF,x
    tax
    lda $F9
    jmp __cmod_set_runtime_0c6f687a_return_setof_2
    lda #$00
    ldx #$00
__cmod_set_runtime_0c6f687a_return_setof_2:
    sta $F9
    stx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    txs
    pla
    sta __cmod_set_runtime_0c6f687a_frame_pointer
    lda $F9
    ldx $FA
    rts

; C-Funktion SetAdd
SetAdd:
    lda __cmod_set_runtime_0c6f687a_frame_pointer
    pha
    tsx
    stx __cmod_set_runtime_0c6f687a_frame_pointer
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0106,x
    sta $F9
    lda $0107,x
    tax
    lda $F9
    pha
    txa
    pha
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
    sta $F9
    txa
    pha
    lda $F9
    pha
    jsr SetOf
    sta $F9
    stx $FA
    tsx
    txa
    clc
    adc #$02
    tax
    txs
    lda $F9
    ldx $FA
    sta $FD
    stx $FE
    pla
    tax
    pla
    ora $FD
    sta $FB
    txa
    ora $FE
    tax
    lda $FB
    jmp __cmod_set_runtime_0c6f687a_return_setadd_3
    lda #$00
    ldx #$00
__cmod_set_runtime_0c6f687a_return_setadd_3:
    sta $F9
    stx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    txs
    pla
    sta __cmod_set_runtime_0c6f687a_frame_pointer
    lda $F9
    ldx $FA
    rts

; C-Funktion SetRemove
SetRemove:
    lda __cmod_set_runtime_0c6f687a_frame_pointer
    pha
    tsx
    stx __cmod_set_runtime_0c6f687a_frame_pointer
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0106,x
    sta $F9
    lda $0107,x
    tax
    lda $F9
    pha
    txa
    pha
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
    sta $F9
    txa
    pha
    lda $F9
    pha
    jsr SetOf
    sta $F9
    stx $FA
    tsx
    txa
    clc
    adc #$02
    tax
    txs
    lda $F9
    ldx $FA
    pha
    txa
    pha
    lda #$FF
    ldx #$FF
    sta $FD
    stx $FE
    pla
    tax
    pla
    eor $FD
    sta $FB
    txa
    eor $FE
    tax
    lda $FB
    sta $FD
    stx $FE
    pla
    tax
    pla
    and $FD
    sta $FB
    txa
    and $FE
    tax
    lda $FB
    jmp __cmod_set_runtime_0c6f687a_return_setremove_4
    lda #$00
    ldx #$00
__cmod_set_runtime_0c6f687a_return_setremove_4:
    sta $F9
    stx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    txs
    pla
    sta __cmod_set_runtime_0c6f687a_frame_pointer
    lda $F9
    ldx $FA
    rts

; C-Funktion SetUnion
SetUnion:
    lda __cmod_set_runtime_0c6f687a_frame_pointer
    pha
    tsx
    stx __cmod_set_runtime_0c6f687a_frame_pointer
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0106,x
    sta $F9
    lda $0107,x
    tax
    lda $F9
    pha
    txa
    pha
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
    sta $FD
    stx $FE
    pla
    tax
    pla
    ora $FD
    sta $FB
    txa
    ora $FE
    tax
    lda $FB
    jmp __cmod_set_runtime_0c6f687a_return_setunion_5
    lda #$00
    ldx #$00
__cmod_set_runtime_0c6f687a_return_setunion_5:
    sta $F9
    stx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    txs
    pla
    sta __cmod_set_runtime_0c6f687a_frame_pointer
    lda $F9
    ldx $FA
    rts

; C-Funktion SetIntersection
SetIntersection:
    lda __cmod_set_runtime_0c6f687a_frame_pointer
    pha
    tsx
    stx __cmod_set_runtime_0c6f687a_frame_pointer
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0106,x
    sta $F9
    lda $0107,x
    tax
    lda $F9
    pha
    txa
    pha
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
    sta $FD
    stx $FE
    pla
    tax
    pla
    and $FD
    sta $FB
    txa
    and $FE
    tax
    lda $FB
    jmp __cmod_set_runtime_0c6f687a_return_setintersection_6
    lda #$00
    ldx #$00
__cmod_set_runtime_0c6f687a_return_setintersection_6:
    sta $F9
    stx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    txs
    pla
    sta __cmod_set_runtime_0c6f687a_frame_pointer
    lda $F9
    ldx $FA
    rts

; C-Funktion SetDifference
SetDifference:
    lda __cmod_set_runtime_0c6f687a_frame_pointer
    pha
    tsx
    stx __cmod_set_runtime_0c6f687a_frame_pointer
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0106,x
    sta $F9
    lda $0107,x
    tax
    lda $F9
    pha
    txa
    pha
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
    pha
    txa
    pha
    lda #$FF
    ldx #$FF
    sta $FD
    stx $FE
    pla
    tax
    pla
    eor $FD
    sta $FB
    txa
    eor $FE
    tax
    lda $FB
    sta $FD
    stx $FE
    pla
    tax
    pla
    and $FD
    sta $FB
    txa
    and $FE
    tax
    lda $FB
    jmp __cmod_set_runtime_0c6f687a_return_setdifference_7
    lda #$00
    ldx #$00
__cmod_set_runtime_0c6f687a_return_setdifference_7:
    sta $F9
    stx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    txs
    pla
    sta __cmod_set_runtime_0c6f687a_frame_pointer
    lda $F9
    ldx $FA
    rts

; C-Funktion SetContains
SetContains:
    lda __cmod_set_runtime_0c6f687a_frame_pointer
    pha
    tsx
    stx __cmod_set_runtime_0c6f687a_frame_pointer
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0106,x
    sta $F9
    lda $0107,x
    tax
    lda $F9
    pha
    txa
    pha
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
    sta $F9
    txa
    pha
    lda $F9
    pha
    jsr SetOf
    sta $F9
    stx $FA
    tsx
    txa
    clc
    adc #$02
    tax
    txs
    lda $F9
    ldx $FA
    sta $FD
    stx $FE
    pla
    tax
    pla
    and $FD
    sta $FB
    txa
    and $FE
    tax
    lda $FB
    pha
    txa
    pha
    lda #$00
    ldx #$00
    sta $FD
    stx $FE
    pla
    tax
    pla
    sta $FB
    stx $FC
    cmp $FD
    bne __cmod_set_runtime_0c6f687a_cmp_true_33
    cpx $FE
    beq __cmod_set_runtime_0c6f687a_cmp_false_34
    jmp __cmod_set_runtime_0c6f687a_cmp_true_33
__cmod_set_runtime_0c6f687a_cmp_false_34:
    lda #$00
    ldx #$00
    jmp __cmod_set_runtime_0c6f687a_cmp_end_35
__cmod_set_runtime_0c6f687a_cmp_true_33:
    lda #$01
    ldx #$00
__cmod_set_runtime_0c6f687a_cmp_end_35:
    jmp __cmod_set_runtime_0c6f687a_return_setcontains_8
    lda #$00
    ldx #$00
__cmod_set_runtime_0c6f687a_return_setcontains_8:
    sta $F9
    stx $FA
    ldx __cmod_set_runtime_0c6f687a_frame_pointer
    txs
    pla
    sta __cmod_set_runtime_0c6f687a_frame_pointer
    lda $F9
    ldx $FA
    rts

; $FB/$FC * $FD/$FE, Ergebnis in A/X
__cmod_set_runtime_0c6f687a_mul16:
    lda #$00
    sta __cmod_set_runtime_0c6f687a_rt_value
    sta __cmod_set_runtime_0c6f687a_rt_value+1
    ldy #$10
__cmod_set_runtime_0c6f687a_mul16_loop:
    lsr $FE
    ror $FD
    bcc __cmod_set_runtime_0c6f687a_mul16_no_add
    clc
    lda __cmod_set_runtime_0c6f687a_rt_value
    adc $FB
    sta __cmod_set_runtime_0c6f687a_rt_value
    lda __cmod_set_runtime_0c6f687a_rt_value+1
    adc $FC
    sta __cmod_set_runtime_0c6f687a_rt_value+1
__cmod_set_runtime_0c6f687a_mul16_no_add:
    asl $FB
    rol $FC
    dey
    bne __cmod_set_runtime_0c6f687a_mul16_loop
    lda __cmod_set_runtime_0c6f687a_rt_value
    ldx __cmod_set_runtime_0c6f687a_rt_value+1
    rts

; Compiler-Laufzeitdaten
__cmod_set_runtime_0c6f687a_rt_value:      .word 0
__cmod_set_runtime_0c6f687a_rt_remainder:  .word 0
__cmod_set_runtime_0c6f687a_rt_count:      .byte 0
__cmod_set_runtime_0c6f687a_rt_mode:       .byte 0

; C-Stackframe-Zeiger
__cmod_set_runtime_0c6f687a_frame_pointer: .byte 0

; --- separat kompiliertes C-Modul: recursive_module.c ---
; Separat kompiliertes C-Modul fuer MOS 6510
; Quelldatei: T:\GitHub\dBase2Many\src\asmjit\compiler\frontend\c64\examples\c_advanced\recursive_module.c

; C-Funktion Factorial
Factorial:
    lda __cmod_recursive_module_9379dde2_frame_pointer
    pha
    tsx
    stx __cmod_recursive_module_9379dde2_frame_pointer
    lda #$00
    pha
    pha
    pha
    lda #$00
    ldx #$00
    sta $F9
    stx $FA
    ldx __cmod_recursive_module_9379dde2_frame_pointer
    lda $F9
    sta $00FE,x
    lda $FA
    sta $00FF,x
    lda $F9
    ldx $FA
    ldx __cmod_recursive_module_9379dde2_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
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
    sta $FB
    stx $FC
    txa
    eor $FE
    bpl __cmod_recursive_module_9379dde2_cmp_order_10
    lda $FC
    bmi __cmod_recursive_module_9379dde2_cmp_less_8
    jmp __cmod_recursive_module_9379dde2_cmp_greater_9
__cmod_recursive_module_9379dde2_cmp_order_10:
    ldx $FC
    cpx $FE
    bcc __cmod_recursive_module_9379dde2_cmp_less_8
    bne __cmod_recursive_module_9379dde2_cmp_greater_9
    lda $FB
    cmp $FD
    bcc __cmod_recursive_module_9379dde2_cmp_less_8
    bne __cmod_recursive_module_9379dde2_cmp_greater_9
    jmp __cmod_recursive_module_9379dde2_cmp_true_5
__cmod_recursive_module_9379dde2_cmp_less_8:
    jmp __cmod_recursive_module_9379dde2_cmp_true_5
__cmod_recursive_module_9379dde2_cmp_greater_9:
    jmp __cmod_recursive_module_9379dde2_cmp_false_6
__cmod_recursive_module_9379dde2_cmp_false_6:
    lda #$00
    ldx #$00
    jmp __cmod_recursive_module_9379dde2_cmp_end_7
__cmod_recursive_module_9379dde2_cmp_true_5:
    lda #$01
    ldx #$00
__cmod_recursive_module_9379dde2_cmp_end_7:
    sta $FB
    txa
    ora $FB
    bne __cmod_recursive_module_9379dde2_condition_true_11
    jmp __cmod_recursive_module_9379dde2_if_else_3
__cmod_recursive_module_9379dde2_condition_true_11:
    lda #$01
    ldx #$00
    jmp __cmod_recursive_module_9379dde2_return_factorial_1
    jmp __cmod_recursive_module_9379dde2_if_end_4
__cmod_recursive_module_9379dde2_if_else_3:
__cmod_recursive_module_9379dde2_if_end_4:
    ldx __cmod_recursive_module_9379dde2_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
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
    sec
    sbc $FD
    sta $FB
    txa
    sbc $FE
    tax
    lda $FB
    sta $F9
    txa
    pha
    lda $F9
    pha
    jsr Factorial
    sta $F9
    stx $FA
    tsx
    txa
    clc
    adc #$02
    tax
    txs
    lda $F9
    ldx $FA
    sta $F9
    stx $FA
    ldx __cmod_recursive_module_9379dde2_frame_pointer
    lda $F9
    sta $00FE,x
    lda $FA
    sta $00FF,x
    lda $F9
    ldx $FA
    ldx __cmod_recursive_module_9379dde2_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
    pha
    txa
    pha
    ldx __cmod_recursive_module_9379dde2_frame_pointer
    lda $00FE,x
    sta $F9
    lda $00FF,x
    tax
    lda $F9
    sta $FD
    stx $FE
    pla
    tax
    pla
    sta $FB
    stx $FC
    jsr __cmod_recursive_module_9379dde2_mul16
    jmp __cmod_recursive_module_9379dde2_return_factorial_1
    lda #$00
    ldx #$00
__cmod_recursive_module_9379dde2_return_factorial_1:
    sta $F9
    stx $FA
    ldx __cmod_recursive_module_9379dde2_frame_pointer
    txs
    pla
    sta __cmod_recursive_module_9379dde2_frame_pointer
    lda $F9
    ldx $FA
    rts

; C-Funktion PersistentCounter
PersistentCounter:
    lda __cmod_recursive_module_9379dde2_frame_pointer
    pha
    tsx
    stx __cmod_recursive_module_9379dde2_frame_pointer
    lda __cmod_recursive_module_9379dde2_static_persistentcounter___c_local_persistentcounter_2_counter_0
    ldx __cmod_recursive_module_9379dde2_static_persistentcounter___c_local_persistentcounter_2_counter_0+1
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
    sta __cmod_recursive_module_9379dde2_static_persistentcounter___c_local_persistentcounter_2_counter_0
    stx __cmod_recursive_module_9379dde2_static_persistentcounter___c_local_persistentcounter_2_counter_0+1
    lda __cmod_recursive_module_9379dde2_static_persistentcounter___c_local_persistentcounter_2_counter_0
    ldx __cmod_recursive_module_9379dde2_static_persistentcounter___c_local_persistentcounter_2_counter_0+1
    jmp __cmod_recursive_module_9379dde2_return_persistentcounter_2
    lda #$00
    ldx #$00
__cmod_recursive_module_9379dde2_return_persistentcounter_2:
    sta $F9
    stx $FA
    ldx __cmod_recursive_module_9379dde2_frame_pointer
    txs
    pla
    sta __cmod_recursive_module_9379dde2_frame_pointer
    lda $F9
    ldx $FA
    rts

; $FB/$FC * $FD/$FE, Ergebnis in A/X
__cmod_recursive_module_9379dde2_mul16:
    lda #$00
    sta __cmod_recursive_module_9379dde2_rt_value
    sta __cmod_recursive_module_9379dde2_rt_value+1
    ldy #$10
__cmod_recursive_module_9379dde2_mul16_loop:
    lsr $FE
    ror $FD
    bcc __cmod_recursive_module_9379dde2_mul16_no_add
    clc
    lda __cmod_recursive_module_9379dde2_rt_value
    adc $FB
    sta __cmod_recursive_module_9379dde2_rt_value
    lda __cmod_recursive_module_9379dde2_rt_value+1
    adc $FC
    sta __cmod_recursive_module_9379dde2_rt_value+1
__cmod_recursive_module_9379dde2_mul16_no_add:
    asl $FB
    rol $FC
    dey
    bne __cmod_recursive_module_9379dde2_mul16_loop
    lda __cmod_recursive_module_9379dde2_rt_value
    ldx __cmod_recursive_module_9379dde2_rt_value+1
    rts

; Compiler-Laufzeitdaten
__cmod_recursive_module_9379dde2_rt_value:      .word 0
__cmod_recursive_module_9379dde2_rt_remainder:  .word 0
__cmod_recursive_module_9379dde2_rt_count:      .byte 0
__cmod_recursive_module_9379dde2_rt_mode:       .byte 0

; C-Variablen
__cmod_recursive_module_9379dde2_static_persistentcounter___c_local_persistentcounter_2_counter_0: .word $0028 ; intern: integer

; C-Stackframe-Zeiger
__cmod_recursive_module_9379dde2_frame_pointer: .byte 0

