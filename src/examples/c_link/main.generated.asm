; Von C64 C erzeugter MOS-6510-Assembler
; Programm: main
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
    lda #$14
    ldx #$00
    sta $F9
    txa
    pha
    lda $F9
    pha
    lda #$1E
    ldx #$00
    sta $F9
    txa
    pha
    lda $F9
    pha
    jsr AddValues
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
    sta $00FE,x
    lda $FA
    sta $00FF,x
    lda $F9
    ldx $FA
    ldx __c_frame_pointer
    lda $00FE,x
    sta $F9
    lda $00FF,x
    tax
    lda $F9
    sta $F9
    txa
    pha
    lda $F9
    pha
    lda #$00
    ldx #$00
    sta $F9
    txa
    pha
    lda $F9
    pha
    lda #$28
    ldx #$00
    sta $F9
    txa
    pha
    lda $F9
    pha
    jsr ClampValue
    sta $F9
    stx $FA
    tsx
    txa
    clc
    adc #$06
    tax
    txs
    lda $F9
    ldx $FA
    sta $F9
    stx $FA
    ldx __c_frame_pointer
    lda $F9
    sta $00FE,x
    lda $FA
    sta $00FF,x
    lda $F9
    ldx $FA
    jsr IncrementCounter
    jsr IncrementCounter
    lda #<__c_string_0
    ldx #>__c_string_0
    jsr __c_print_string
    ldx __c_frame_pointer
    lda $00FE,x
    sta $F9
    lda $00FF,x
    tax
    lda $F9
    jsr __c_print_int16
    lda #<__c_string_1
    ldx #>__c_string_1
    jsr __c_print_string
    jsr GetCounter
    jsr __c_print_int16
    lda #<__c_string_2
    ldx #>__c_string_2
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
__c_string_0: .byte $56, $41, $4C, $55, $45, $3D, $00
__c_string_1: .byte $20, $43, $4F, $55, $4E, $54, $45, $52, $3D, $00
__c_string_2: .byte $0D, $00

; C-Stackframe-Zeiger
__c_frame_pointer: .byte 0

; --- separat kompiliertes C-Modul: math_module.c ---
; Separat kompiliertes C-Modul fuer MOS 6510
; Quelldatei: T:\GitHub\dBase2Many\src\asmjit\compiler\frontend\c64\examples\c_link\math_module.c

; C-Funktion AddValues
AddValues:
    lda __cmod_math_module_f3ba77a5_frame_pointer
    pha
    tsx
    stx __cmod_math_module_f3ba77a5_frame_pointer
    ldx __cmod_math_module_f3ba77a5_frame_pointer
    lda $0106,x
    sta $F9
    lda $0107,x
    tax
    lda $F9
    pha
    txa
    pha
    ldx __cmod_math_module_f3ba77a5_frame_pointer
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
    clc
    adc $FD
    sta $FB
    txa
    adc $FE
    tax
    lda $FB
    jmp __cmod_math_module_f3ba77a5_return_addvalues_1
    lda #$00
    ldx #$00
__cmod_math_module_f3ba77a5_return_addvalues_1:
    sta $F9
    stx $FA
    ldx __cmod_math_module_f3ba77a5_frame_pointer
    txs
    pla
    sta __cmod_math_module_f3ba77a5_frame_pointer
    lda $F9
    ldx $FA
    rts

; C-Funktion ClampValue
ClampValue:
    lda __cmod_math_module_f3ba77a5_frame_pointer
    pha
    tsx
    stx __cmod_math_module_f3ba77a5_frame_pointer
    ldx __cmod_math_module_f3ba77a5_frame_pointer
    lda $0108,x
    sta $F9
    lda $0109,x
    tax
    lda $F9
    pha
    txa
    pha
    ldx __cmod_math_module_f3ba77a5_frame_pointer
    lda $0106,x
    sta $F9
    lda $0107,x
    tax
    lda $F9
    sta $FD
    stx $FE
    pla
    tax
    pla
    sta $FB
    stx $FC
    txa
    eor $FE
    bpl __cmod_math_module_f3ba77a5_cmp_order_12
    lda $FC
    bmi __cmod_math_module_f3ba77a5_cmp_less_10
    jmp __cmod_math_module_f3ba77a5_cmp_greater_11
__cmod_math_module_f3ba77a5_cmp_order_12:
    ldx $FC
    cpx $FE
    bcc __cmod_math_module_f3ba77a5_cmp_less_10
    bne __cmod_math_module_f3ba77a5_cmp_greater_11
    lda $FB
    cmp $FD
    bcc __cmod_math_module_f3ba77a5_cmp_less_10
    bne __cmod_math_module_f3ba77a5_cmp_greater_11
    jmp __cmod_math_module_f3ba77a5_cmp_false_8
__cmod_math_module_f3ba77a5_cmp_less_10:
    jmp __cmod_math_module_f3ba77a5_cmp_true_7
__cmod_math_module_f3ba77a5_cmp_greater_11:
    jmp __cmod_math_module_f3ba77a5_cmp_false_8
__cmod_math_module_f3ba77a5_cmp_false_8:
    lda #$00
    ldx #$00
    jmp __cmod_math_module_f3ba77a5_cmp_end_9
__cmod_math_module_f3ba77a5_cmp_true_7:
    lda #$01
    ldx #$00
__cmod_math_module_f3ba77a5_cmp_end_9:
    sta $FB
    txa
    ora $FB
    bne __cmod_math_module_f3ba77a5_condition_true_13
    jmp __cmod_math_module_f3ba77a5_if_else_5
__cmod_math_module_f3ba77a5_condition_true_13:
    ldx __cmod_math_module_f3ba77a5_frame_pointer
    lda $0106,x
    sta $F9
    lda $0107,x
    tax
    lda $F9
    jmp __cmod_math_module_f3ba77a5_return_clampvalue_2
    jmp __cmod_math_module_f3ba77a5_if_end_6
__cmod_math_module_f3ba77a5_if_else_5:
__cmod_math_module_f3ba77a5_if_end_6:
    ldx __cmod_math_module_f3ba77a5_frame_pointer
    lda $0108,x
    sta $F9
    lda $0109,x
    tax
    lda $F9
    pha
    txa
    pha
    ldx __cmod_math_module_f3ba77a5_frame_pointer
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
    sta $FB
    stx $FC
    txa
    eor $FE
    bpl __cmod_math_module_f3ba77a5_cmp_order_21
    lda $FC
    bmi __cmod_math_module_f3ba77a5_cmp_less_19
    jmp __cmod_math_module_f3ba77a5_cmp_greater_20
__cmod_math_module_f3ba77a5_cmp_order_21:
    ldx $FC
    cpx $FE
    bcc __cmod_math_module_f3ba77a5_cmp_less_19
    bne __cmod_math_module_f3ba77a5_cmp_greater_20
    lda $FB
    cmp $FD
    bcc __cmod_math_module_f3ba77a5_cmp_less_19
    bne __cmod_math_module_f3ba77a5_cmp_greater_20
    jmp __cmod_math_module_f3ba77a5_cmp_false_17
__cmod_math_module_f3ba77a5_cmp_less_19:
    jmp __cmod_math_module_f3ba77a5_cmp_false_17
__cmod_math_module_f3ba77a5_cmp_greater_20:
    jmp __cmod_math_module_f3ba77a5_cmp_true_16
__cmod_math_module_f3ba77a5_cmp_false_17:
    lda #$00
    ldx #$00
    jmp __cmod_math_module_f3ba77a5_cmp_end_18
__cmod_math_module_f3ba77a5_cmp_true_16:
    lda #$01
    ldx #$00
__cmod_math_module_f3ba77a5_cmp_end_18:
    sta $FB
    txa
    ora $FB
    bne __cmod_math_module_f3ba77a5_condition_true_22
    jmp __cmod_math_module_f3ba77a5_if_else_14
__cmod_math_module_f3ba77a5_condition_true_22:
    ldx __cmod_math_module_f3ba77a5_frame_pointer
    lda $0104,x
    sta $F9
    lda $0105,x
    tax
    lda $F9
    jmp __cmod_math_module_f3ba77a5_return_clampvalue_2
    jmp __cmod_math_module_f3ba77a5_if_end_15
__cmod_math_module_f3ba77a5_if_else_14:
__cmod_math_module_f3ba77a5_if_end_15:
    ldx __cmod_math_module_f3ba77a5_frame_pointer
    lda $0108,x
    sta $F9
    lda $0109,x
    tax
    lda $F9
    jmp __cmod_math_module_f3ba77a5_return_clampvalue_2
    lda #$00
    ldx #$00
__cmod_math_module_f3ba77a5_return_clampvalue_2:
    sta $F9
    stx $FA
    ldx __cmod_math_module_f3ba77a5_frame_pointer
    txs
    pla
    sta __cmod_math_module_f3ba77a5_frame_pointer
    lda $F9
    ldx $FA
    rts

; C-Funktion IncrementCounter
IncrementCounter:
    lda __cmod_math_module_f3ba77a5_frame_pointer
    pha
    tsx
    stx __cmod_math_module_f3ba77a5_frame_pointer
    lda __cmod_math_module_f3ba77a5_var_module_counter_0
    ldx __cmod_math_module_f3ba77a5_var_module_counter_0+1
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
    sta __cmod_math_module_f3ba77a5_var_module_counter_0
    stx __cmod_math_module_f3ba77a5_var_module_counter_0+1
__cmod_math_module_f3ba77a5_return_incrementcounter_3:
    ldx __cmod_math_module_f3ba77a5_frame_pointer
    txs
    pla
    sta __cmod_math_module_f3ba77a5_frame_pointer
    rts

; C-Funktion GetCounter
GetCounter:
    lda __cmod_math_module_f3ba77a5_frame_pointer
    pha
    tsx
    stx __cmod_math_module_f3ba77a5_frame_pointer
    lda __cmod_math_module_f3ba77a5_var_module_counter_0
    ldx __cmod_math_module_f3ba77a5_var_module_counter_0+1
    jmp __cmod_math_module_f3ba77a5_return_getcounter_4
    lda #$00
    ldx #$00
__cmod_math_module_f3ba77a5_return_getcounter_4:
    sta $F9
    stx $FA
    ldx __cmod_math_module_f3ba77a5_frame_pointer
    txs
    pla
    sta __cmod_math_module_f3ba77a5_frame_pointer
    lda $F9
    ldx $FA
    rts

; Compiler-Laufzeitdaten
__cmod_math_module_f3ba77a5_rt_value:      .word 0
__cmod_math_module_f3ba77a5_rt_remainder:  .word 0
__cmod_math_module_f3ba77a5_rt_count:      .byte 0
__cmod_math_module_f3ba77a5_rt_mode:       .byte 0

; C-Variablen
__cmod_math_module_f3ba77a5_var_module_counter_0: .word 0 ; module_counter: integer

; C-Stackframe-Zeiger
__cmod_math_module_f3ba77a5_frame_pointer: .byte 0

