
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
    lda #<$FBE1
    sta $F9
    lda #>$FBE1
    sta $FA
    lda #<$0419
    sta $FB
    lda #>$0419
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
    jmp $FBE1

; D64PACK v1 inspectable header (not needed by the decrunch loop itself).
__d64pack_header:
    .byte $44, $36, $34, $50
    .byte $01, $02, $02, $00
    .word $0801
    .word $0393
    .word $080D
    .word $0339

__d64pack_bundle:
    .byte $A9, $68, $8D, $00, $C0, $A9, $85, $8D, $01, $C0, $A9, $01, $8D, $02, $C0, $A9
    .byte $68, $8D, $03, $C0, $A9, $A8, $8D, $04, $C0, $A9, $68, $8D, $05, $C0, $A9, $AA
    .byte $8D, $06, $C0, $A9, $68, $8D, $07, $C0, $A9, $28, $8D, $08, $C0, $A9, $4C, $8D
    .byte $09, $C0, $A9, $0D, $8D, $0A, $C0, $A9, $08, $8D, $0B, $C0, $A9, $F9, $85, $F7
    .byte $A9, $FF, $85, $F8, $A9, $93, $85, $F9, $A9, $0B, $85, $FA, $A0, $00, $B1, $F7
    .byte $C9, $80, $F0, $53, $B0, $17, $AA, $E8, $20, $A6, $FC, $A0, $00, $B1, $F7, $91
    .byte $F9, $20, $A6, $FC, $20, $AF, $FC, $CA, $D0, $F1, $4C, $2D, $FC, $29, $7F, $18
    .byte $69, $02, $AA, $20, $A6, $FC, $A0, $00, $B1, $F7, $85, $FE, $20, $A6, $FC, $A0
    .byte $00, $B1, $F7, $85, $FD, $20, $A6, $FC, $18, $A5, $FD, $65, $F9, $85, $FD, $A5
    .byte $FE, $65, $FA, $85, $FE, $A0, $00, $B1, $FD, $91, $F9, $20, $B8, $FC, $20, $AF
    .byte $FC, $CA, $D0, $F1, $4C, $2D, $FC, $68, $85, $FF, $68, $85, $FE, $68, $85, $FD
    .byte $68, $85, $FC, $68, $85, $FB, $68, $85, $FA, $68, $85, $F9, $68, $85, $F8, $68
    .byte $85, $F7, $4C, $00, $C0, $A5, $F7, $D0, $02, $C6, $F8, $C6, $F7, $60, $A5, $F9
    .byte $D0, $02, $C6, $FA, $C6, $F9, $60, $A5, $FD, $D0, $02, $C6, $FE, $C6, $FD, $60
    .byte $80, $0B, $08, $0A, $00, $9E, $32, $30, $36, $31, $08, $4B, $03, $81, $20, $2D
    .byte $08, $BA, $8E, $BA, $0B, $A9, $69, $08, $19, $03, $81, $A9, $0B, $01, $1B, $03
    .byte $81, $A9, $5F, $01, $1F, $03, $81, $58, $08, $20, $53, $08, $60, $20, $CC, $07
    .byte $59, $02, $81, $94, $85, $FB, $A9, $03, $12, $02, $81, $A9, $00, $A2, $06, $F0
    .byte $0C, $A0, $00, $07, $10, $00, $82, $FB, $E6, $FC, $CA, $D0, $F4, $A0, $00, $C0
    .byte $27, $F0, $05, $91, $FB, $C8, $0E, $22, $00, $81, $A9, $0D, $4C, $D2, $FF, $04
    .byte $1D, $00, $86, $AA, $F0, $11, $02, $B0, $01, $83, $10, $00, $83, $12, $00, $81
    .byte $B7, $02, $81, $F7, $60, $85, $FB, $84, $04, $8E, $02, $83, $F0, $06, $20, $D2
    .byte $FF, $C8, $D0, $F6, $60, $08, $06, $00, $81, $4C, $75, $08, $20, $DD, $BD, $85
    .byte $FD, $84, $FE, $A2, $00, $0B, $8D, $01, $82, $F0, $09, $9D, $BC, $0E, $E8, $C8
    .byte $E0, $FF, $D0, $F3, $8E, $BB, $0E, $60, $20, $AA, $B1, $AA, $98, $60, $A8, $8A
    .byte $4C, $91, $B3, $4C, $67, $B8, $4C, $50, $B8, $4C, $28, $BA, $4C, $0F, $24, $13
    .byte $00, $82, $28, $00, $91, $3F, $00, $93, $15, $00, $93, $F0, $00, $15, $00, $91
    .byte $FF, $00, $15, $00, $8E, $20, $5B, $BC, $C9, $01, $04, $BD, $01, $88, $5A, $00
    .byte $B6, $01, $83, $10, $00, $81, $2D, $00, $10, $00, $84, $2D, $00, $10, $00, $83
    .byte $11, $00, $81, $0D, $00, $11, $00, $84, $0D, $00, $11, $00, $83, $18, $00, $5B
    .byte $00, $81, $6D, $A0, $0B, $48, $03, $4A, $00, $81, $6D, $A1, $0B, $AA, $68, $04
    .byte $1F, $01, $81, $8D, $A2, $01, $1D, $00, $82, $A0, $10, $4E, $A1, $0B, $6E, $05
    .byte $41, $00, $81, $13, $18, $01, $1B, $00, $81, $6D, $9E, $0B, $8D, $A2, $0B, $AD
    .byte $A3, $0B, $6D, $9F, $0B, $8D, $A3, $0B, $0E, $9E, $0B, $2E, $9F, $0B, $88, $D0
    .byte $DC, $AD, $A2, $0B, $AE, $A3, $0B, $60, $AD, $A0, $0B, $0D, $A1, $0B, $D0, $04
    .byte $A9, $00, $AA, $60, $2A, $1C, $00, $81, $CD, $A1, $0B, $90, $20, $D0, $08, $06
    .byte $09, $00, $81, $CD, $A0, $0B, $90, $16, $38, $05, $15, $00, $81, $ED, $A0, $0B
    .byte $8D, $9E, $0B, $AD, $9F, $0B, $ED, $A1, $0B, $8D, $9F, $0B, $4C, $AB, $09, $AD
    .byte $9E, $0B, $AE, $9F, $0B, $17, $75, $00, $81, $A9, $00, $01, $6E, $00, $81, $20
    .byte $DA, $09, $4C, $E7, $09, $A5, $FB, $8D, $AE, $09, $46, $01, $81, $8D, $AF, $0B
    .byte $02, $5E, $00, $83, $B1, $00, $5E, $00, $82, $B2, $0B, $F0, $4F, $03, $29, $00
    .byte $84, $18, $A5, $FB, $6D, $B1, $04, $35, $00, $81, $25, $01, $82, $85, $FC, $01
    .byte $1B, $00, $84, $A2, $00, $2E, $00, $82, $C9, $FF, $F0, $1B, $03, $2D, $00, $81
    .byte $FD, $91, $FB, $02, $39, $00, $84, $2D, $00, $84, $EE, $B1, $0B, $E8, $EC, $B2
    .byte $0B, $D0, $DE, $AD, $AE, $0A, $C0, $00, $82, $AF, $00, $C0, $00, $83, $AD, $B1
    .byte $0B, $91, $FB, $60, $05, $B8, $00, $82, $8D, $B3, $0B, $B1, $FD, $8D, $B4, $0B
    .byte $07, $BB, $00, $84, $E6, $FD, $01, $B5, $00, $81, $FE, $A0, $00, $CC, $B3, $0B
    .byte $F0, $10, $07, $10, $00, $82, $13, $B1, $FB, $D1, $FD, $90, $0A, $D0, $0B, $C8
    .byte $D0, $EB, $CC, $B4, $0B, $F0, $06, $A9, $FF, $60, $A9, $01, $60, $A9, $00, $60
    .byte $A2, $00, $20, $CF, $FF, $C9, $0D, $F0, $0A, $E0, $FF, $F0, $06, $9D, $BC, $0F
    .byte $E8, $D0, $EF, $8E, $BB, $0F, $60, $AC, $B5, $0B, $33, $11, $00, $82, $32, $00
    .byte $11, $00, $81, $27, $00, $81, $03, $C8, $D0, $F1, $A2, $00, $CC, $BB, $0F, $F0
    .byte $0F, $B9, $BC, $0F, $C9, $2C, $F0, $07, $9D, $BC, $10, $E8, $C8, $D0, $ED, $C8
    .byte $8C, $B5, $0B, $1C, $50, $00, $81, $0D, $BD, $BB, $10, $C9, $20, $D0, $06, $CA
    .byte $4C, $CE, $0A, $A2, $00, $8E, $BB, $10, $60, $11, $14, $00, $81, $D0, $07, $A9
    .byte $55, $A0, $0B, $4C, $A2, $BB, $A9, $BC, $85, $22, $A9, $11, $85, $23, $AD, $BB
    .byte $10, $4C, $B5, $B7, $AD, $AC, $0B, $85, $FB, $AD, $AD, $0B, $85, $1F, $15, $00
    .byte $81, $B1, $FB, $C9, $FF, $D0, $03, $4C, $47, $0B, $AA, $8D, $BB, $10, $E6, $FB
    .byte $D0, $02, $E6, $FC, $A0, $00, $E0, $00, $F0, $09, $B1, $FB, $99, $BC, $10, $C8
    .byte $CA, $D0, $F3, $98, $18, $65, $FB, $8D, $AC, $0B, $A5, $FC, $69, $00, $8D, $AD
    .byte $0B, $60, $6C, $FB, $00, $A9, $6A, $35, $0A, $00, $83, $4C, $4E, $0B, $A9, $80
    .byte $A0, $0B, $20, $75, $08, $AE, $BA, $0B, $9A, $4C, $29, $08, $00, $11, $05, $00
    .byte $82, $81, $00, $01, $00, $81, $00, $09, $48, $41, $4C, $4C, $4F, $20, $43, $36
    .byte $34, $FF, $3F, $42, $41, $44, $20, $53, $55, $42, $53, $43, $52, $49, $50, $54
    .byte $19, $14, $00, $86, $3F, $4F, $55, $54, $20, $4F, $46, $20, $44, $41, $54, $41
    .byte $20, $45, $52, $52, $4F, $52, $0D, $00, $13

; ===========================================================================
; D64PACK Stage 52 - lesbare Decruncher-Quelle (NUR KOMMENTAR)
; Modus       : LZ
; Packsuche   : balanced
; Hochspeicher: $FBE1-$FFF9
; Der oben eingebettete __d64pack_bundle enthaelt genau diesen
; Decruncher bereits als Maschinencode plus den gepackten Stream.
; Die folgenden Zeilen sind deshalb ausnahmslos Kommentare und
; veraendern beim erneuten Assemblieren das PRG nicht.
; ===========================================================================
; .nostub
; .org $FBE1
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
;     lda #<$0B93
;     sta $F9
;     lda #>$0B93
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
;     sta $FE
;     jsr __d64pack_dec_src
;     ldy #$00
;     lda ($F7),y
;     sta $FD
;     jsr __d64pack_dec_src
;     clc
;     lda $FD
;     adc $F9
;     sta $FD
;     lda $FE
;     adc $FA
;     sta $FE
; __d64pack_match_loop:
;     ldy #$00
;     lda ($FD),y
;     sta ($F9),y
;     jsr __d64pack_dec_match
;     jsr __d64pack_dec_dst
;     dex
;     bne __d64pack_match_loop
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
;
; __d64pack_dec_match:
;     lda $FD
;     bne __d64pack_dec_match_low
;     dec $FE
; __d64pack_dec_match_low:
;     dec $FD
;     rts
