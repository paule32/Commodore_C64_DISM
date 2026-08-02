; Von C64 C erzeugter MOS-6510-Assembler
; Programm: preprocessor
.org $080D
.entry __c_start
.basic

__c_start:
    lda #$00
    ldx #$00
    sta __c_var_cursor_x_0
    lda #$00
    ldx #$00
    sta __c_var_cursor_y_1
    lda #$00
    ldx #$04
    pha
    txa
    pha
    lda __c_var_cursor_x_0
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
    lda #$00
    ldx #$D8
    pha
    txa
    pha
    lda __c_var_cursor_x_0
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
    lda #<__c_string_0
    ldx #>__c_string_0
    jsr __c_print_string
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
__c_var_cursor_x_0: .byte 0 ; cursor.x
__c_var_cursor_y_1: .byte 0 ; cursor.y

; Nullterminierte PETSCII-Zeichenketten
__c_string_0: .byte $41, $00
