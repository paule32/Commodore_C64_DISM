
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
    lda #<$FAD5
    sta $F9
    lda #>$FAD5
    sta $FA
    lda #<$0525
    sta $FB
    lda #>$0525
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
    jmp $FAD5

; D64PACK v1 inspectable header (not needed by the decrunch loop itself).
__d64pack_header:
    .byte $44, $36, $34, $50
    .byte $01, $02, $02, $00
    .word $0801
    .word $05A3
    .word $080D
    .word $0445

__d64pack_bundle:
    .byte $A9, $68, $8D, $00, $C0, $A9, $85, $8D, $01, $C0, $A9, $01, $8D, $02, $C0, $A9
    .byte $68, $8D, $03, $C0, $A9, $A8, $8D, $04, $C0, $A9, $68, $8D, $05, $C0, $A9, $AA
    .byte $8D, $06, $C0, $A9, $68, $8D, $07, $C0, $A9, $28, $8D, $08, $C0, $A9, $4C, $8D
    .byte $09, $C0, $A9, $0D, $8D, $0A, $C0, $A9, $08, $8D, $0B, $C0, $A9, $F9, $85, $F7
    .byte $A9, $FF, $85, $F8, $A9, $A3, $85, $F9, $A9, $0D, $85, $FA, $A0, $00, $B1, $F7
    .byte $C9, $80, $F0, $53, $B0, $17, $AA, $E8, $20, $9A, $FB, $A0, $00, $B1, $F7, $91
    .byte $F9, $20, $9A, $FB, $20, $A3, $FB, $CA, $D0, $F1, $4C, $21, $FB, $29, $7F, $18
    .byte $69, $02, $AA, $20, $9A, $FB, $A0, $00, $B1, $F7, $85, $FE, $20, $9A, $FB, $A0
    .byte $00, $B1, $F7, $85, $FD, $20, $9A, $FB, $18, $A5, $FD, $65, $F9, $85, $FD, $A5
    .byte $FE, $65, $FA, $85, $FE, $A0, $00, $B1, $FD, $91, $F9, $20, $AC, $FB, $20, $A3
    .byte $FB, $CA, $D0, $F1, $4C, $21, $FB, $68, $85, $FF, $68, $85, $FE, $68, $85, $FD
    .byte $68, $85, $FC, $68, $85, $FB, $68, $85, $FA, $68, $85, $F9, $68, $85, $F8, $68
    .byte $85, $F7, $4C, $00, $C0, $A5, $F7, $D0, $02, $C6, $F8, $C6, $F7, $60, $A5, $F9
    .byte $D0, $02, $C6, $FA, $C6, $F9, $60, $A5, $FD, $D0, $02, $C6, $FE, $C6, $FD, $60
    .byte $80, $0B, $08, $0A, $00, $9E, $32, $30, $36, $31, $08, $15, $05, $81, $20, $F7
    .byte $09, $BA, $8E, $DE, $0D, $A9, $79, $08, $E3, $04, $81, $A9, $0D, $01, $E5, $04
    .byte $81, $A9, $29, $01, $10, $01, $98, $02, $01, $85, $62, $00, $86, $2E, $00, $0E
    .byte $00, $84, $A9, $00, $0E, $00, $84, $24, $00, $0E, $00, $84, $AE, $00, $0E, $00
    .byte $84, $33, $00, $0E, $00, $83, $A2, $B3, $01, $38, $00, $8B, $B3, $00, $23, $00
    .byte $83, $61, $00, $86, $38, $00, $61, $00, $8A, $26, $00, $84, $0E, $00, $84, $7D
    .byte $0A, $A2, $02, $07, $00, $82, $D4, $BB, $A9, $A4, $03, $11, $00, $83, $A9, $A9
    .byte $A0, $0D, $03, $D4, $01, $81, $8D, $D4, $0D, $A9, $AE, $04, $1F, $00, $83, $A5
    .byte $66, $30, $0A, $03, $0A, $00, $81, $E9, $01, $81, $0D, $00, $0A, $00, $81, $AD
    .byte $D4, $01, $15, $03, $82, $03, $4C, $64, $08, $A9, $3D, $05, $1C, $00, $8B, $42
    .byte $00, $1C, $00, $8B, $47, $00, $1C, $00, $8B, $4C, $00, $1C, $00, $8B, $51, $00
    .byte $1C, $00, $8B, $56, $00, $1C, $00, $8B, $5B, $00, $38, $00, $99, $60, $00, $8C
    .byte $00, $98, $A9, $65, $01, $1C, $00, $99, $6A, $00, $1C, $00, $99, $6F, $00, $1C
    .byte $00, $99, $74, $00, $1C, $00, $8B, $1F, $00, $1C, $00, $8A, $A9, $29, $01, $0E
    .byte $00, $86, $85, $FB, $86, $FC, $A9, $24, $05, $23, $03, $81, $B1, $00, $81, $72
    .byte $0A, $A0, $02, $B8, $01, $83, $CC, $00, $59, $02, $81, $A4, $85, $FB, $A9, $03
    .byte $12, $02, $81, $A9, $00, $A2, $06, $F0, $0C, $A0, $00, $07, $10, $00, $82, $FB
    .byte $E6, $FC, $CA, $D0, $F4, $A0, $00, $C0, $3B, $F0, $05, $91, $FB, $C8, $0E, $22
    .byte $00, $81, $A9, $0D, $4C, $D2, $FF, $04, $1D, $00, $86, $AA, $F0, $11, $02, $B0
    .byte $01, $83, $10, $00, $83, $12, $00, $81, $B7, $02, $81, $F7, $60, $85, $FB, $84
    .byte $04, $8E, $02, $83, $F0, $06, $20, $D2, $FF, $C8, $D0, $F6, $60, $08, $06, $00
    .byte $81, $4C, $3F, $0A, $20, $DD, $BD, $85, $FD, $84, $FE, $A2, $00, $0B, $8D, $01
    .byte $82, $F0, $09, $9D, $E0, $10, $E8, $C8, $E0, $FF, $D0, $F3, $8E, $DF, $10, $60
    .byte $20, $AA, $B1, $AA, $98, $60, $A8, $8A, $4C, $91, $B3, $4C, $67, $B8, $4C, $50
    .byte $B8, $4C, $28, $BA, $4C, $0F, $24, $13, $00, $82, $28, $00, $91, $3F, $00, $93
    .byte $15, $00, $93, $F0, $00, $15, $00, $91, $FF, $00, $15, $00, $8E, $20, $5B, $BC
    .byte $C9, $01, $04, $BD, $01, $88, $24, $00, $B6, $01, $83, $10, $00, $81, $2D, $00
    .byte $10, $00, $84, $2D, $00, $10, $00, $83, $11, $00, $81, $0D, $00, $11, $00, $84
    .byte $0D, $00, $11, $00, $83, $18, $00, $5B, $00, $81, $6D, $C4, $0D, $48, $03, $4A
    .byte $00, $81, $6D, $C5, $0D, $AA, $68, $04, $1F, $01, $81, $8D, $C6, $01, $1D, $00
    .byte $82, $A0, $10, $4E, $C5, $0D, $6E, $05, $41, $00, $81, $13, $18, $01, $1B, $00
    .byte $81, $6D, $C2, $0D, $8D, $C6, $0D, $AD, $C7, $0D, $6D, $C3, $0D, $8D, $C7, $0D
    .byte $0E, $C2, $0D, $2E, $C3, $0D, $88, $D0, $DC, $AD, $C6, $0D, $AE, $C7, $0D, $60
    .byte $AD, $C4, $0D, $0D, $C5, $0D, $D0, $04, $A9, $00, $AA, $60, $2A, $1C, $00, $81
    .byte $CD, $C5, $0D, $90, $20, $D0, $08, $06, $09, $00, $81, $CD, $C4, $0D, $90, $16
    .byte $38, $05, $15, $00, $81, $ED, $C4, $0D, $8D, $C2, $0D, $AD, $C3, $0D, $ED, $C5
    .byte $0D, $8D, $C3, $0D, $4C, $75, $0B, $AD, $C2, $0D, $AE, $C3, $0D, $17, $75, $00
    .byte $81, $A9, $00, $01, $6E, $00, $81, $20, $A4, $0B, $4C, $B1, $0B, $A5, $FB, $8D
    .byte $D2, $09, $46, $01, $81, $8D, $D3, $0D, $02, $5E, $00, $83, $D5, $00, $5E, $00
    .byte $82, $D6, $0D, $F0, $4F, $03, $29, $00, $84, $18, $A5, $FB, $6D, $D5, $04, $35
    .byte $00, $81, $25, $01, $82, $85, $FC, $01, $1B, $00, $84, $A2, $00, $2E, $00, $82
    .byte $C9, $FF, $F0, $1B, $03, $2D, $00, $81, $FD, $91, $FB, $02, $39, $00, $84, $2D
    .byte $00, $84, $EE, $D5, $0D, $E8, $EC, $D6, $0D, $D0, $DE, $AD, $D2, $0A, $C0, $00
    .byte $82, $D3, $00, $C0, $00, $83, $AD, $D5, $0D, $91, $FB, $60, $05, $B8, $00, $82
    .byte $8D, $D7, $0D, $B1, $FD, $8D, $D8, $0D, $07, $BB, $00, $84, $E6, $FD, $01, $B5
    .byte $00, $81, $FE, $A0, $00, $CC, $D7, $0D, $F0, $10, $07, $10, $00, $82, $13, $B1
    .byte $FB, $D1, $FD, $90, $0A, $D0, $0B, $C8, $D0, $EB, $CC, $D8, $0D, $F0, $06, $A9
    .byte $FF, $60, $A9, $01, $60, $A9, $00, $60, $A2, $00, $20, $CF, $FF, $C9, $0D, $F0
    .byte $0A, $E0, $FF, $F0, $06, $9D, $E0, $11, $E8, $D0, $EF, $8E, $DF, $11, $60, $AC
    .byte $D9, $0D, $33, $11, $00, $82, $32, $00, $11, $00, $81, $27, $00, $81, $03, $C8
    .byte $D0, $F1, $A2, $00, $CC, $DF, $11, $F0, $0F, $B9, $E0, $11, $C9, $2C, $F0, $07
    .byte $9D, $E0, $12, $E8, $C8, $D0, $ED, $C8, $8C, $D9, $0D, $1C, $50, $00, $81, $0D
    .byte $BD, $DF, $12, $C9, $20, $D0, $06, $CA, $4C, $98, $0C, $A2, $00, $8E, $DF, $12
    .byte $60, $11, $14, $00, $81, $D0, $07, $A9, $1F, $A0, $0D, $4C, $A2, $BB, $A9, $E0
    .byte $85, $22, $A9, $13, $85, $23, $AD, $DF, $12, $4C, $B5, $B7, $AD, $D0, $0D, $85
    .byte $FB, $AD, $D1, $0D, $85, $1F, $15, $00, $81, $B1, $FB, $C9, $FF, $D0, $03, $4C
    .byte $11, $0D, $AA, $8D, $DF, $12, $E6, $FB, $D0, $02, $E6, $FC, $A0, $00, $E0, $00
    .byte $F0, $09, $B1, $FB, $99, $E0, $12, $C8, $CA, $D0, $F3, $98, $18, $65, $FB, $8D
    .byte $D0, $0D, $A5, $FC, $69, $00, $8D, $D1, $0D, $60, $6C, $FB, $00, $A9, $7A, $35
    .byte $0A, $00, $83, $4C, $18, $0D, $A9, $90, $A0, $0D, $20, $3F, $0A, $AE, $DE, $0D
    .byte $9A, $4C, $F3, $09, $00, $11, $05, $00, $82, $81, $00, $01, $1E, $00, $83, $15
    .byte $00, $00, $86, $78, $04, $05, $00, $81, $8E, $40, $01, $0A, $00, $82, $05, $00
    .byte $82, $8B, $7F, $01, $05, $00, $81, $88, $40, $01, $0A, $00, $83, $00, $00, $0A
    .byte $00, $81, $70, $00, $0A, $00, $83, $01, $00, $00, $87, $48, $00, $05, $05, $00
    .byte $82, $10, $00, $05, $00, $82, $27, $00, $05, $00, $82, $1C, $00, $05, $00, $82
    .byte $17, $00, $05, $00, $82, $1D, $00, $00, $90, $50, $1B, $00, $00, $FF, $3F, $42
    .byte $41, $44, $20, $53, $55, $42, $53, $43, $52, $49, $50, $54, $16, $14, $00, $86
    .byte $3F, $4F, $55, $54, $20, $4F, $46, $20, $44, $41, $54, $41, $20, $45, $52, $52
    .byte $4F, $52, $0D, $00, $13

; ===========================================================================
; D64PACK Stage 52 - lesbare Decruncher-Quelle (NUR KOMMENTAR)
; Modus       : LZ
; Packsuche   : balanced
; Hochspeicher: $FAD5-$FFF9
; Der oben eingebettete __d64pack_bundle enthaelt genau diesen
; Decruncher bereits als Maschinencode plus den gepackten Stream.
; Die folgenden Zeilen sind deshalb ausnahmslos Kommentare und
; veraendern beim erneuten Assemblieren das PRG nicht.
; ===========================================================================
; .nostub
; .org $FAD5
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
;     lda #<$0DA3
;     sta $F9
;     lda #>$0DA3
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
