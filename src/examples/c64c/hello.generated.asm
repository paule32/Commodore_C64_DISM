; Von C64 C erzeugter MOS-6510-Assembler
; Programm: hello
.org $080D
.entry __c_start
.basic

__c_start:
    lda #$93
    jsr $FFD2
    lda #<__c_string_0
    ldx #>__c_string_0
    jsr __c_print_string
    lda #$00
    ldx #$00
    sta __c_var_i_0
    lda #$1A
    ldx #$00
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
    sta __c_tmp__for_limit_0_1_1
__c_for_condition_1:
    lda __c_var_i_0
    ldx #$00
    pha
    txa
    pha
    lda __c_tmp__for_limit_0_1_1
    ldx #$00
    sta $FD
    stx $FE
    pla
    tax
    pla
    sta $FB
    stx $FC
    ldx $FC
    cpx $FE
    bcc __c_cmp_less_7
    bne __c_cmp_greater_8
    lda $FB
    cmp $FD
    bcc __c_cmp_less_7
    bne __c_cmp_greater_8
    jmp __c_cmp_true_4
__c_cmp_less_7:
    jmp __c_cmp_true_4
__c_cmp_greater_8:
    jmp __c_cmp_false_5
__c_cmp_false_5:
    lda #$00
    ldx #$00
    jmp __c_cmp_end_6
__c_cmp_true_4:
    lda #$01
    ldx #$00
__c_cmp_end_6:
    sta $FB
    txa
    ora $FB
    bne __c_condition_true_10
    jmp __c_for_end_3
__c_condition_true_10:
    lda #$00
    ldx #$04
    pha
    txa
    pha
    lda __c_var_i_0
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
    pha
    txa
    pha
    lda #$01
    ldx #$00
    pha
    txa
    pha
    lda __c_var_i_0
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
    sta $FD
    pla
    sta $FC
    pla
    sta $FB
    lda $FD
    ldy #$00
    sta ($FB),y
    lda #$00
    ldx #$D8
    pha
    txa
    pha
    lda __c_var_i_0
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
    pha
    txa
    pha
    lda #$01
    ldx #$00
    sta $FD
    pla
    sta $FC
    pla
    sta $FB
    lda $FD
    ldy #$00
    sta ($FB),y
__c_for_step_2:
    lda __c_var_i_0
    clc
    adc #$01
    sta __c_var_i_0
    jmp __c_for_condition_1
__c_for_end_3:
    jmp __c_program_end
__c_program_end:
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

; Compiler-Laufzeitdaten
__c_rt_value:      .word 0
__c_rt_remainder:  .word 0
__c_rt_count:      .byte 0
__c_rt_mode:       .byte 0

; C-Variablen
__c_var_i_0: .byte 0 ; i
__c_tmp__for_limit_0_1_1: .byte 0 ; intern

; Nullterminierte PETSCII-Zeichenketten
__c_string_0: .byte $43, $36, $34, $20, $43, $0D, $00
