
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
    lda #<$FB3D
    sta $F9
    lda #>$FB3D
    sta $FA
    lda #<$04BD
    sta $FB
    lda #>$04BD
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
    jmp $FB3D

; D64PACK v1 inspectable header (not needed by the decrunch loop itself).
__d64pack_header:
    .byte $44, $36, $34, $50
    .byte $01, $02, $02, $00
    .word $0801
    .word $048A
    .word $080D
    .word $03DD

__d64pack_bundle:
    .byte $A9, $68, $8D, $00, $C0, $A9, $85, $8D, $01, $C0, $A9, $01, $8D, $02, $C0, $A9
    .byte $68, $8D, $03, $C0, $A9, $A8, $8D, $04, $C0, $A9, $68, $8D, $05, $C0, $A9, $AA
    .byte $8D, $06, $C0, $A9, $68, $8D, $07, $C0, $A9, $28, $8D, $08, $C0, $A9, $4C, $8D
    .byte $09, $C0, $A9, $0D, $8D, $0A, $C0, $A9, $08, $8D, $0B, $C0, $A9, $F9, $85, $F7
    .byte $A9, $FF, $85, $F8, $A9, $8A, $85, $F9, $A9, $0C, $85, $FA, $A0, $00, $B1, $F7
    .byte $C9, $80, $F0, $53, $B0, $17, $AA, $E8, $20, $02, $FC, $A0, $00, $B1, $F7, $91
    .byte $F9, $20, $02, $FC, $20, $0B, $FC, $CA, $D0, $F1, $4C, $89, $FB, $29, $7F, $18
    .byte $69, $02, $AA, $20, $02, $FC, $A0, $00, $B1, $F7, $85, $FE, $20, $02, $FC, $A0
    .byte $00, $B1, $F7, $85, $FD, $20, $02, $FC, $18, $A5, $FD, $65, $F9, $85, $FD, $A5
    .byte $FE, $65, $FA, $85, $FE, $A0, $00, $B1, $FD, $91, $F9, $20, $14, $FC, $20, $0B
    .byte $FC, $CA, $D0, $F1, $4C, $89, $FB, $68, $85, $FF, $68, $85, $FE, $68, $85, $FD
    .byte $68, $85, $FC, $68, $85, $FB, $68, $85, $FA, $68, $85, $F9, $68, $85, $F8, $68
    .byte $85, $F7, $4C, $00, $C0, $A5, $F7, $D0, $02, $C6, $F8, $C6, $F7, $60, $A5, $F9
    .byte $D0, $02, $C6, $FA, $C6, $F9, $60, $A5, $FD, $D0, $02, $C6, $FE, $C6, $FD, $60
    .byte $80, $0B, $08, $0A, $00, $9E, $32, $30, $36, $31, $08, $3A, $04, $81, $20, $1C
    .byte $09, $BA, $8E, $CF, $0C, $A9, $60, $08, $08, $04, $81, $A9, $0C, $01, $0A, $04
    .byte $81, $A9, $53, $01, $AA, $00, $86, $1C, $00, $86, $8B, $00, $2A, $00, $8B, $95
    .byte $00, $0E, $00, $8B, $9A, $00, $1C, $00, $8A, $38, $00, $86, $4E, $00, $0E, $00
    .byte $84, $9F, $00, $0E, $00, $84, $49, $00, $15, $00, $83, $A2, $A4, $01, $1C, $00
    .byte $84, $5D, $00, $4C, $00, $83, $A9, $A4, $01, $15, $00, $84, $90, $00, $4F, $00
    .byte $84, $90, $00, $4F, $00, $84, $90, $00, $3A, $00, $84, $9F, $00, $4F, $00, $87
    .byte $A4, $00, $4F, $00, $8F, $7C, $00, $4F, $00, $87, $7C, $08, $A9, $5F, $03, $0A
    .byte $00, $81, $47, $09, $20, $42, $09, $04, $26, $00, $84, $0E, $00, $85, $09, $A2
    .byte $01, $07, $00, $82, $D4, $BB, $A9, $8B, $03, $11, $00, $83, $A9, $95, $A0, $0C
    .byte $03, $BC, $00, $81, $8D, $C5, $0C, $A9, $9A, $04, $34, $03, $81, $A2, $BB, $A5
    .byte $66, $30, $0A, $05, $0A, $00, $81, $D1, $00, $81, $0D, $00, $0A, $00, $81, $AD
    .byte $C5, $01, $FD, $01, $82, $03, $4C, $52, $08, $60, $20, $CC, $06, $59, $02, $81
    .byte $8B, $85, $FB, $A9, $03, $12, $02, $81, $A9, $00, $A2, $06, $F0, $04, $B6, $01
    .byte $81, $10, $00, $82, $FB, $E6, $FC, $CA, $D0, $F4, $A0, $00, $C0, $45, $F0, $05
    .byte $91, $FB, $C8, $0E, $22, $00, $81, $A9, $0D, $4C, $D2, $FF, $04, $1D, $00, $86
    .byte $AA, $F0, $01, $B3, $02, $84, $10, $00, $83, $12, $00, $81, $B7, $02, $81, $F7
    .byte $60, $85, $FB, $84, $04, $8E, $02, $83, $F0, $06, $20, $D2, $FF, $C8, $D0, $F6
    .byte $60, $08, $06, $00, $81, $4C, $64, $09, $20, $DD, $BD, $85, $FD, $84, $FE, $A2
    .byte $00, $0B, $8D, $01, $82, $F0, $09, $9D, $D1, $0F, $E8, $C8, $E0, $FF, $D0, $F3
    .byte $8E, $D0, $0F, $60, $20, $AA, $B1, $AA, $98, $60, $A8, $8A, $4C, $91, $B3, $4C
    .byte $67, $B8, $4C, $50, $B8, $4C, $28, $BA, $4C, $0F, $24, $13, $00, $82, $28, $00
    .byte $91, $3F, $00, $93, $15, $00, $93, $F0, $00, $15, $00, $91, $FF, $00, $15, $00
    .byte $8E, $20, $5B, $BC, $C9, $01, $04, $BD, $01, $88, $49, $00, $B6, $01, $83, $10
    .byte $00, $81, $2D, $00, $10, $00, $84, $2D, $00, $10, $00, $83, $11, $00, $81, $0D
    .byte $00, $11, $00, $84, $0D, $00, $11, $00, $83, $18, $00, $5B, $00, $81, $6D, $B5
    .byte $0C, $48, $03, $4A, $00, $81, $6D, $B6, $0C, $AA, $68, $04, $1F, $01, $81, $8D
    .byte $B7, $01, $1D, $00, $82, $A0, $10, $4E, $B6, $0C, $6E, $05, $41, $00, $81, $13
    .byte $18, $01, $1B, $00, $81, $6D, $B3, $0C, $8D, $B7, $0C, $AD, $B8, $0C, $6D, $B4
    .byte $0C, $8D, $B8, $0C, $0E, $B3, $0C, $2E, $B4, $0C, $88, $D0, $DC, $AD, $B7, $0C
    .byte $AE, $B8, $0C, $60, $AD, $B5, $0C, $0D, $B6, $0C, $D0, $04, $A9, $00, $AA, $60
    .byte $2A, $1C, $00, $81, $CD, $B6, $0C, $90, $20, $D0, $08, $06, $09, $00, $81, $CD
    .byte $B5, $0C, $90, $16, $38, $05, $15, $00, $81, $ED, $B5, $0C, $8D, $B3, $0C, $AD
    .byte $B4, $0C, $ED, $B6, $0C, $8D, $B4, $0C, $4C, $9A, $0A, $AD, $B3, $0C, $AE, $B4
    .byte $0C, $17, $75, $00, $81, $A9, $00, $01, $6E, $00, $81, $20, $C9, $0A, $4C, $D6
    .byte $0A, $A5, $FB, $8D, $C3, $09, $46, $01, $81, $8D, $C4, $0C, $02, $5E, $00, $83
    .byte $C6, $00, $5E, $00, $82, $C7, $0C, $F0, $4F, $03, $29, $00, $84, $18, $A5, $FB
    .byte $6D, $C6, $04, $35, $00, $81, $25, $01, $82, $85, $FC, $01, $1B, $00, $84, $A2
    .byte $00, $2E, $00, $82, $C9, $FF, $F0, $1B, $03, $2D, $00, $81, $FD, $91, $FB, $02
    .byte $39, $00, $84, $2D, $00, $84, $EE, $C6, $0C, $E8, $EC, $C7, $0C, $D0, $DE, $AD
    .byte $C3, $0A, $C0, $00, $82, $C4, $00, $C0, $00, $83, $AD, $C6, $0C, $91, $FB, $60
    .byte $05, $B8, $00, $82, $8D, $C8, $0C, $B1, $FD, $8D, $C9, $0C, $07, $BB, $00, $84
    .byte $E6, $FD, $01, $B5, $00, $81, $FE, $A0, $00, $CC, $C8, $0C, $F0, $10, $07, $10
    .byte $00, $82, $13, $B1, $FB, $D1, $FD, $90, $0A, $D0, $0B, $C8, $D0, $EB, $CC, $C9
    .byte $0C, $F0, $06, $A9, $FF, $60, $A9, $01, $60, $A9, $00, $60, $A2, $00, $20, $CF
    .byte $FF, $C9, $0D, $F0, $0A, $E0, $FF, $F0, $06, $9D, $D1, $10, $E8, $D0, $EF, $8E
    .byte $D0, $10, $60, $AC, $CA, $0C, $33, $11, $00, $82, $32, $00, $11, $00, $81, $27
    .byte $00, $81, $03, $C8, $D0, $F1, $A2, $00, $CC, $D0, $10, $F0, $0F, $B9, $D1, $10
    .byte $C9, $2C, $F0, $07, $9D, $D1, $11, $E8, $C8, $D0, $ED, $C8, $8C, $CA, $0C, $1C
    .byte $50, $00, $81, $0D, $BD, $D0, $11, $C9, $20, $D0, $06, $CA, $4C, $BD, $0B, $A2
    .byte $00, $8E, $D0, $11, $60, $11, $14, $00, $81, $D0, $07, $A9, $44, $A0, $0C, $4C
    .byte $A2, $BB, $A9, $D1, $85, $22, $A9, $12, $85, $23, $AD, $D0, $11, $4C, $B5, $B7
    .byte $AD, $C1, $0C, $85, $FB, $AD, $C2, $0C, $85, $1F, $15, $00, $81, $B1, $FB, $C9
    .byte $FF, $D0, $03, $4C, $36, $0C, $AA, $8D, $D0, $11, $E6, $FB, $D0, $02, $E6, $FC
    .byte $A0, $00, $E0, $00, $F0, $09, $B1, $FB, $99, $D1, $11, $C8, $CA, $D0, $F3, $98
    .byte $18, $65, $FB, $8D, $C1, $0C, $A5, $FC, $69, $00, $8D, $C2, $0C, $60, $6C, $FB
    .byte $00, $A9, $61, $35, $0A, $00, $83, $4C, $3D, $0C, $A9, $77, $A0, $0C, $20, $64
    .byte $09, $AE, $CF, $0C, $9A, $4C, $18, $09, $00, $11, $05, $00, $82, $81, $00, $01
    .byte $05, $00, $81, $85, $20, $00, $00, $00, $09, $48, $41, $4C, $4C, $4F, $20, $43
    .byte $36, $34, $01, $41, $00, $FF, $3F, $42, $41, $44, $20, $53, $55, $42, $53, $43
    .byte $52, $49, $50, $54, $20, $14, $00, $86, $3F, $4F, $55, $54, $20, $4F, $46, $20
    .byte $44, $41, $54, $41, $20, $45, $52, $52, $4F, $52, $0D, $00, $13

; ===========================================================================
; D64PACK Stage 52 - lesbare Decruncher-Quelle (NUR KOMMENTAR)
; Modus       : LZ
; Packsuche   : balanced
; Hochspeicher: $FB3D-$FFF9
; Der oben eingebettete __d64pack_bundle enthaelt genau diesen
; Decruncher bereits als Maschinencode plus den gepackten Stream.
; Die folgenden Zeilen sind deshalb ausnahmslos Kommentare und
; veraendern beim erneuten Assemblieren das PRG nicht.
; ===========================================================================
; .nostub
; .org $FB3D
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
;     lda #<$0C8A
;     sta $F9
;     lda #>$0C8A
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
