
; ---------------------------------------------------------------------------
; D64PACK v1 self-extracting C64 PRG
; Stage 52: bootstrap -> high-RAM decruncher -> banking-safe return trampoline
; ---------------------------------------------------------------------------
.org $080D
.entry __d64pack_boot
__d64pack_boot:
    ; Preserve the machine state seen by the original SYS entry.
    php
    pha
    txa
    pha
    tya
    pha
    sei
    lda $01
    pha
    lda $F7
    pha
    lda $F8
    pha
    lda $F9
    pha
    lda $FA
    pha
    lda $FB
    pha
    lda $FC
    pha
    lda $FD
    pha
    lda $FE
    pha
    lda $FF
    pha
    lda #$34
    sta $01

    lda #<__d64pack_bundle
    sta $F7
    lda #>__d64pack_bundle
    sta $F8
    lda #<$FAB1
    sta $F9
    lda #>$FAB1
    sta $FA
    lda #<$0549
    sta $FB
    lda #>$0549
    sta $FC

__d64pack_copy_loop:
    lda $FB
    ora $FC
    beq __d64pack_copy_done
    ldy #$00
    lda ($F7),y
    sta ($F9),y
    inc $F7
    bne __d64pack_src_inc_done
    inc $F8
__d64pack_src_inc_done:
    inc $F9
    bne __d64pack_dst_inc_done
    inc $FA
__d64pack_dst_inc_done:
    lda $FB
    bne __d64pack_count_low
    dec $FC
__d64pack_count_low:
    dec $FB
    jmp __d64pack_copy_loop

__d64pack_copy_done:
    jmp $FAB1

; D64PACK v1 inspectable header (not needed by the decrunch loop itself).
__d64pack_header:
    .byte $44, $36, $34, $50
    .byte $01, $01, $02, $00
    .word $0801
    .word $0484
    .word $080D
    .word $048B

__d64pack_bundle:
    .byte $A9, $68, $8D, $00, $C0, $A9, $85, $8D, $01, $C0, $A9, $01, $8D, $02, $C0, $A9
    .byte $68, $8D, $03, $C0, $A9, $A8, $8D, $04, $C0, $A9, $68, $8D, $05, $C0, $A9, $AA
    .byte $8D, $06, $C0, $A9, $68, $8D, $07, $C0, $A9, $28, $8D, $08, $C0, $A9, $4C, $8D
    .byte $09, $C0, $A9, $0D, $8D, $0A, $C0, $A9, $08, $8D, $0B, $C0, $A9, $F9, $85, $F7
    .byte $A9, $FF, $85, $F8, $A9, $84, $85, $F9, $A9, $0C, $85, $FA, $A0, $00, $B1, $F7
    .byte $C9, $80, $F0, $3A, $B0, $17, $AA, $E8, $20, $5D, $FB, $A0, $00, $B1, $F7, $91
    .byte $F9, $20, $5D, $FB, $20, $66, $FB, $CA, $D0, $F1, $4C, $FD, $FA, $29, $7F, $18
    .byte $69, $02, $AA, $20, $5D, $FB, $A0, $00, $B1, $F7, $85, $FF, $20, $5D, $FB, $A5
    .byte $FF, $A0, $00, $91, $F9, $20, $66, $FB, $CA, $D0, $F4, $4C, $FD, $FA, $68, $85
    .byte $FF, $68, $85, $FE, $68, $85, $FD, $68, $85, $FC, $68, $85, $FB, $68, $85, $FA
    .byte $68, $85, $F9, $68, $85, $F8, $68, $85, $F7, $4C, $00, $C0, $A5, $F7, $D0, $02
    .byte $C6, $F8, $C6, $F7, $60, $A5, $F9, $D0, $02, $C6, $FA, $C6, $F9, $60, $80, $0B
    .byte $08, $0A, $00, $9E, $32, $30, $36, $31, $08, $00, $81, $20, $EC, $08, $BA, $8E
    .byte $C4, $0C, $A9, $5A, $8D, $B6, $0C, $A9, $0C, $8D, $B7, $0C, $20, $14, $0C, $20
    .byte $12, $09, $A9, $33, $A0, $0C, $20, $1B, $A2, $BB, $A2, $85, $A0, $0C, $20, $D4
    .byte $BB, $20, $1B, $0C, $A9, $85, $A0, $0C, $20, $A2, $BB, $20, $45, $09, $20, $12
    .byte $09, $A9, $2E, $A0, $0C, $20, $A2, $BB, $A2, $8A, $A0, $0C, $20, $D4, $BB, $A9
    .byte $38, $A0, $0C, $20, $A2, $BB, $A2, $8F, $A0, $0C, $20, $D4, $BB, $A9, $2E, $A0
    .byte $0C, $20, $A2, $BB, $A2, $94, $A0, $0C, $20, $D4, $BB, $A9, $8A, $A0, $0C, $20
    .byte $A2, $BB, $20, $45, $09, $A9, $94, $A0, $0C, $20, $A2, $BB, $A9, $8A, $A0, $0C
    .byte $20, $72, $09, $A2, $8A, $A0, $0C, $20, $D4, $BB, $A9, $8A, $A0, $0C, $20, $A2
    .byte $BB, $A9, $8F, $A0, $0C, $20, $5B, $BC, $8D, $BA, $0C, $A9, $94, $A0, $0C, $20
    .byte $A2, $BB, $A5, $66, $30, $0A, $AD, $BA, $7F, $0C, $C9, $01, $F0, $0D, $4C, $6C
    .byte $08, $AD, $BA, $0C, $C9, $FF, $F0, $03, $4C, $6C, $08, $20, $12, $09, $A9, $85
    .byte $A0, $0C, $20, $A2, $BB, $A2, $99, $A0, $0C, $20, $D4, $BB, $A9, $33, $A0, $0C
    .byte $20, $A2, $BB, $A9, $99, $A0, $0C, $20, $7E, $09, $A5, $61, $F0, $03, $4C, $E7
    .byte $08, $20, $22, $0C, $20, $12, $09, $60, $20, $CC, $FF, $60, $A9, $85, $85, $FB
    .byte $A9, $0C, $85, $FC, $A9, $00, $A2, $06, $F0, $0C, $A0, $00, $91, $FB, $C8, $D0
    .byte $FB, $E6, $FC, $CA, $D0, $F4, $A0, $00, $C0, $40, $F0, $05, $91, $FB, $C8, $D0
    .byte $F7, $60, $A9, $0D, $4C, $D2, $FF, $85, $FB, $84, $FC, $A0, $00, $B1, $FB, $AA
    .byte $F0, $11, $E6, $FB, $D0, $02, $E6, $FC, $A0, $7F, $00, $B1, $FB, $20, $D2, $FF
    .byte $C8, $CA, $D0, $F7, $60, $85, $FB, $84, $FC, $A0, $00, $B1, $FB, $F0, $06, $20
    .byte $D2, $FF, $C8, $D0, $F6, $60, $20, $DD, $BD, $4C, $34, $09, $20, $DD, $BD, $85
    .byte $FD, $84, $FE, $A2, $00, $A0, $00, $B1, $FD, $F0, $09, $9D, $C6, $0F, $E8, $C8
    .byte $E0, $FF, $D0, $F3, $8E, $C5, $0F, $60, $20, $AA, $B1, $AA, $98, $60, $A8, $8A
    .byte $4C, $91, $B3, $4C, $67, $B8, $4C, $50, $B8, $4C, $28, $BA, $4C, $0F, $BB, $20
    .byte $5B, $BC, $F0, $07, $A9, $29, $A0, $0C, $4C, $A2, $BB, $A9, $2E, $A0, $0C, $4C
    .byte $A2, $BB, $20, $5B, $BC, $D0, $07, $A9, $29, $A0, $0C, $4C, $A2, $BB, $A9, $2E
    .byte $A0, $0C, $4C, $A2, $BB, $20, $5B, $BC, $C9, $01, $7F, $F0, $07, $A9, $29, $A0
    .byte $0C, $4C, $A2, $BB, $A9, $2E, $A0, $0C, $4C, $A2, $BB, $20, $5B, $BC, $C9, $FF
    .byte $F0, $07, $A9, $29, $A0, $0C, $4C, $A2, $BB, $A9, $2E, $A0, $0C, $4C, $A2, $BB
    .byte $20, $5B, $BC, $C9, $FF, $D0, $07, $A9, $29, $A0, $0C, $4C, $A2, $BB, $A9, $2E
    .byte $A0, $0C, $4C, $A2, $BB, $20, $5B, $BC, $C9, $01, $D0, $07, $A9, $29, $A0, $0C
    .byte $4C, $A2, $BB, $A9, $2E, $A0, $0C, $4C, $A2, $BB, $AD, $A8, $0C, $2D, $AA, $0C
    .byte $48, $AD, $A9, $0C, $2D, $AB, $0C, $AA, $68, $60, $AD, $A8, $0C, $0D, $AA, $0C
    .byte $48, $AD, $A9, $0C, $0D, $AB, $0C, $AA, $68, $60, $18, $AD, $A8, $0C, $6D, $AA
    .byte $0C, $48, $AD, $A9, $0C, $6D, $AB, $0C, $AA, $68, $60, $7F, $A9, $00, $8D, $AC
    .byte $0C, $8D, $AD, $0C, $A0, $10, $4E, $AB, $0C, $6E, $AA, $0C, $90, $13, $18, $AD
    .byte $AC, $0C, $6D, $A8, $0C, $8D, $AC, $0C, $AD, $AD, $0C, $6D, $A9, $0C, $8D, $AD
    .byte $0C, $0E, $A8, $0C, $2E, $A9, $0C, $88, $D0, $DC, $AD, $AC, $0C, $AE, $AD, $0C
    .byte $60, $AD, $AA, $0C, $0D, $AB, $0C, $D0, $04, $A9, $00, $AA, $60, $AD, $A9, $0C
    .byte $CD, $AB, $0C, $90, $20, $D0, $08, $AD, $A8, $0C, $CD, $AA, $0C, $90, $16, $38
    .byte $AD, $A8, $0C, $ED, $AA, $0C, $8D, $A8, $0C, $AD, $A9, $0C, $ED, $AB, $0C, $8D
    .byte $A9, $0C, $4C, $6A, $0A, $AD, $A8, $0C, $AE, $A9, $0C, $60, $A0, $00, $A9, $00
    .byte $91, $FB, $60, $20, $99, $0A, $4C, $A6, $0A, $A5, $FB, $8D, $7F, $B8, $0C, $A5
    .byte $FC, $8D, $B9, $0C, $A0, $00, $B1, $FB, $8D, $BB, $0C, $B1, $FD, $8D, $BC, $0C
    .byte $F0, $4F, $E6, $FD, $D0, $02, $E6, $FE, $18, $A5, $FB, $6D, $BB, $0C, $85, $FB
    .byte $A5, $FC, $69, $00, $85, $FC, $E6, $FB, $D0, $02, $E6, $FC, $A2, $00, $AD, $BB
    .byte $0C, $C9, $FF, $F0, $1B, $A0, $00, $B1, $FD, $91, $FB, $E6, $FD, $D0, $02, $E6
    .byte $FE, $E6, $FB, $D0, $02, $E6, $FC, $EE, $BB, $0C, $E8, $EC, $BC, $0C, $D0, $DE
    .byte $AD, $B8, $0C, $85, $FB, $AD, $B9, $0C, $85, $FC, $A0, $00, $AD, $BB, $0C, $91
    .byte $FB, $60, $A0, $00, $B1, $FB, $8D, $BD, $0C, $B1, $FD, $8D, $BE, $0C, $E6, $FB
    .byte $D0, $02, $E6, $FC, $E6, $FD, $D0, $02, $E6, $FE, $A0, $00, $CC, $7F, $BD, $0C
    .byte $F0, $10, $CC, $BE, $0C, $F0, $13, $B1, $FB, $D1, $FD, $90, $0A, $D0, $0B, $C8
    .byte $D0, $EB, $CC, $BE, $0C, $F0, $06, $A9, $FF, $60, $A9, $01, $60, $A9, $00, $60
    .byte $A2, $00, $20, $CF, $FF, $C9, $0D, $F0, $0A, $E0, $FF, $F0, $06, $9D, $C6, $10
    .byte $E8, $D0, $EF, $8E, $C5, $10, $60, $AC, $BF, $0C, $CC, $C5, $10, $F0, $32, $B9
    .byte $C6, $10, $C9, $20, $D0, $03, $C8, $D0, $F1, $A2, $00, $CC, $C5, $10, $F0, $0F
    .byte $B9, $C6, $10, $C9, $2C, $F0, $07, $9D, $C6, $11, $E8, $C8, $D0, $ED, $C8, $8C
    .byte $BF, $0C, $E0, $00, $F0, $0D, $BD, $C5, $11, $C9, $20, $D0, $06, $CA, $4C, $8D
    .byte $0B, $A2, $00, $8E, $C5, $11, $60, $AD, $C5, $11, $D0, $07, $A9, $29, $7F, $A0
    .byte $0C, $4C, $A2, $BB, $A9, $C6, $85, $22, $A9, $12, $85, $23, $AD, $C5, $11, $4C
    .byte $B5, $B7, $AD, $B6, $0C, $85, $FB, $AD, $B7, $0C, $85, $FC, $A0, $00, $B1, $FB
    .byte $C9, $FF, $D0, $03, $4C, $06, $0C, $AA, $8D, $C5, $11, $E6, $FB, $D0, $02, $E6
    .byte $FC, $A0, $00, $E0, $00, $F0, $09, $B1, $FB, $99, $C6, $11, $C8, $CA, $D0, $F3
    .byte $98, $18, $65, $FB, $8D, $B6, $0C, $A5, $FC, $69, $00, $8D, $B7, $0C, $60, $6C
    .byte $FB, $00, $A9, $5B, $A0, $0C, $20, $34, $09, $4C, $0D, $0C, $A9, $71, $A0, $0C
    .byte $20, $34, $09, $AE, $C4, $0C, $9A, $4C, $E8, $08, $A9, $3D, $A0, $0C, $4C, $17
    .byte $09, $A9, $50, $A0, $0C, $4C, $17, $09, $A9, $53, $A0, $0C, $4C, $17, $09, $7F
    .byte $00, $83, $81, $00, $00, $82, $84, $60, $01, $00, $81, $83, $20, $01, $00, $81
    .byte $12, $43, $36, $34, $20, $42, $41, $53, $49, $43, $20, $43, $4F, $4D, $50, $49
    .byte $4C, $45, $52, $02, $41, $3D, $06, $46, $45, $48, $4C, $45, $52, $FF, $3F, $42
    .byte $41, $44, $20, $53, $55, $42, $53, $43, $52, $49, $50, $54, $20, $45, $52, $52
    .byte $4F, $52, $0D, $00, $3F, $4F, $55, $54, $20, $4F, $46, $20, $44, $41, $54, $41
    .byte $20, $45, $52, $52, $4F, $52, $0D, $00, $47

; ===========================================================================
; D64PACK Stage 52 - lesbare Decruncher-Quelle (NUR KOMMENTAR)
; Modus       : RLE
; Packsuche   : balanced
; Hochspeicher: $FAB1-$FFF9
; Der oben eingebettete __d64pack_bundle enthaelt genau diesen
; Decruncher bereits als Maschinencode plus den gepackten Stream.
; Die folgenden Zeilen sind deshalb ausnahmslos Kommentare und
; veraendern beim erneuten Assemblieren das PRG nicht.
; ===========================================================================
; .nostub
; .org $FAB1
; .entry __d64pack_high_start
; __d64pack_high_start:
;     ; Stage 52: install the final return trampoline in always-visible RAM.
;     lda #$68
;     sta $C000
;     lda #$85
;     sta $C001
;     lda #$01
;     sta $C002
;     lda #$68
;     sta $C003
;     lda #$A8
;     sta $C004
;     lda #$68
;     sta $C005
;     lda #$AA
;     sta $C006
;     lda #$68
;     sta $C007
;     lda #$28
;     sta $C008
;     lda #$4C
;     sta $C009
;     lda #$0D
;     sta $C00A
;     lda #$08
;     sta $C00B
;
;     lda #<$FFF9
;     sta $F7
;     lda #>$FFF9
;     sta $F8
;     lda #<$0C84
;     sta $F9
;     lda #>$0C84
;     sta $FA
; __d64pack_next:
;     ldy #$00
;     lda ($F7),y
;     cmp #$80
;     beq __d64pack_done
;     bcs __d64pack_encoded
;     tax
;     inx
;     jsr __d64pack_dec_src
; __d64pack_literal_loop:
;     ldy #$00
;     lda ($F7),y
;     sta ($F9),y
;     jsr __d64pack_dec_src
;     jsr __d64pack_dec_dst
;     dex
;     bne __d64pack_literal_loop
;     jmp __d64pack_next
; __d64pack_encoded:
;     and #$7F
;     clc
;     adc #$02
;     tax
;
;     jsr __d64pack_dec_src
;     ldy #$00
;     lda ($F7),y
;     sta $FF
;     jsr __d64pack_dec_src
; __d64pack_run_loop:
;     lda $FF
;     ldy #$00
;     sta ($F9),y
;     jsr __d64pack_dec_dst
;     dex
;     bne __d64pack_run_loop
;     jmp __d64pack_next
;
; __d64pack_done:
;     pla
;     sta $FF
;     pla
;     sta $FE
;     pla
;     sta $FD
;     pla
;     sta $FC
;     pla
;     sta $FB
;     pla
;     sta $FA
;     pla
;     sta $F9
;     pla
;     sta $F8
;     pla
;     sta $F7
;     jmp $C000
;
; __d64pack_dec_src:
;     lda $F7
;     bne __d64pack_dec_src_low
;     dec $F8
; __d64pack_dec_src_low:
;     dec $F7
;     rts
;
; __d64pack_dec_dst:
;     lda $F9
;     bne __d64pack_dec_dst_low
;     dec $FA
; __d64pack_dec_dst_low:
;     dec $F9
;     rts
