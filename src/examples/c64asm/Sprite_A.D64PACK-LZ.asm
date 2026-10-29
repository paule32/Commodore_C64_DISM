
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
    ; D64PACK: 6510-Binärarithmetik erzwingen. Beim Eintritt über
    ; BASIC SYS kann das Decimal-Flag gesetzt sein. Der LZ/RLE-
    ; Entpacker verwendet ADC; im BCD-Modus entstünden beschädigte
    ; Programmbytes und fehlerhafte Rücksprungadressen.
    ; Der ursprüngliche P-Status wurde vorab mit PHP gesichert und
    ; wird am Ende des Entpackens über PLP wiederhergestellt.
    cld
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
    lda #<$FAF2
    sta $F9
    lda #>$FAF2
    sta $FA
    lda #<$0508
    sta $FB
    lda #>$0508
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
    jmp $FAF2

; D64PACK v1 inspectable header (not needed by the decrunch loop itself).
__d64pack_header:
    .byte $44, $36, $34, $50
    .byte $01, $02, $02, $00
    .word $0801
    .word $04FA
    .word $080D
    .word $0428

__d64pack_bundle:
    .byte $A9, $68, $8D, $00, $C0, $A9, $85, $8D, $01, $C0, $A9, $01, $8D, $02, $C0, $A9
    .byte $68, $8D, $03, $C0, $A9, $A8, $8D, $04, $C0, $A9, $68, $8D, $05, $C0, $A9, $AA
    .byte $8D, $06, $C0, $A9, $68, $8D, $07, $C0, $A9, $28, $8D, $08, $C0, $A9, $4C, $8D
    .byte $09, $C0, $A9, $0D, $8D, $0A, $C0, $A9, $08, $8D, $0B, $C0, $A9, $F9, $85, $F7
    .byte $A9, $FF, $85, $F8, $A9, $FA, $85, $F9, $A9, $0C, $85, $FA, $A0, $00, $B1, $F7
    .byte $C9, $80, $F0, $53, $B0, $17, $AA, $E8, $20, $B7, $FB, $A0, $00, $B1, $F7, $91
    .byte $F9, $20, $B7, $FB, $20, $C0, $FB, $CA, $D0, $F1, $4C, $3E, $FB, $29, $7F, $18
    .byte $69, $02, $AA, $20, $B7, $FB, $A0, $00, $B1, $F7, $85, $FE, $20, $B7, $FB, $A0
    .byte $00, $B1, $F7, $85, $FD, $20, $B7, $FB, $18, $A5, $FD, $65, $F9, $85, $FD, $A5
    .byte $FE, $65, $FA, $85, $FE, $A0, $00, $B1, $FD, $91, $F9, $20, $C9, $FB, $20, $C0
    .byte $FB, $CA, $D0, $F1, $4C, $3E, $FB, $68, $85, $FF, $68, $85, $FE, $68, $85, $FD
    .byte $68, $85, $FC, $68, $85, $FB, $68, $85, $FA, $68, $85, $F9, $68, $85, $F8, $68
    .byte $85, $F7, $4C, $00, $C0, $A5, $F7, $D0, $02, $C6, $F8, $C6, $F7, $60, $A5, $F9
    .byte $D0, $02, $C6, $FA, $C6, $F9, $60, $A5, $FD, $D0, $02, $C6, $FE, $C6, $FD, $60
    .byte $80, $0B, $08, $0A, $00, $9E, $32, $30, $36, $31, $08, $71, $04, $81, $20, $3C
    .byte $09, $BA, $8E, $2B, $0D, $A9, $C3, $08, $28, $04, $81, $A9, $0C, $01, $2A, $04
    .byte $81, $A9, $FB, $01, $63, $00, $84, $0E, $00, $81, $63, $00, $81, $25, $00, $85
    .byte $A9, $00, $01, $2E, $00, $81, $CE, $09, $A5, $61, $03, $E0, $03, $81, $44, $08
    .byte $4C, $8F, $08, $A9, $85, $06, $0D, $00, $87, $29, $0D, $01, $D8, $00, $88, $8D
    .byte $2A, $0D, $AD, $B7, $0C, $A2, $B8, $A0, $0D, $20, $BD, $FF, $A9, $01, $AE, $29
    .byte $0D, $AC, $2A, $0D, $20, $BA, $FF, $17, $D1, $00, $81, $01, $A0, $08, $20, $D5
    .byte $FF, $90, $03, $4C, $4C, $0C, $0A, $A8, $00, $85, $A2, $FB, $01, $07, $00, $81
    .byte $D4, $BB, $A9, $8A, $03, $1C, $00, $8B, $8F, $00, $1C, $00, $8B, $94, $00, $1C
    .byte $00, $99, $9E, $00, $1C, $00, $8B, $99, $00, $1C, $00, $8B, $A3, $00, $1C, $00
    .byte $8B, $A8, $00, $1C, $00, $8B, $AD, $00, $1C, $00, $8B, $7B, $00, $1C, $00, $8A
    .byte $A9, $B2, $01, $0E, $00, $86, $85, $FB, $86, $FC, $A9, $80, $05, $24, $03, $81
    .byte $B1, $00, $81, $B7, $09, $A0, $02, $B8, $01, $83, $CC, $00, $59, $02, $81, $FB
    .byte $85, $FB, $A9, $0C, $85, $FC, $A9, $00, $A2, $06, $F0, $0C, $A0, $00, $0E, $10
    .byte $00, $82, $FB, $E6, $FC, $CA, $D0, $F4, $A0, $00, $C0, $31, $F0, $05, $91, $FB
    .byte $C8, $0E, $22, $00, $81, $A9, $0D, $4C, $D2, $FF, $04, $1D, $00, $86, $AA, $F0
    .byte $11, $02, $B0, $01, $83, $10, $00, $83, $12, $00, $81, $B7, $02, $81, $F7, $60
    .byte $85, $FB, $84, $04, $8E, $02, $83, $F0, $06, $20, $D2, $FF, $C8, $D0, $F6, $60
    .byte $08, $06, $00, $81, $4C, $84, $09, $20, $DD, $BD, $85, $FD, $84, $FE, $A2, $00
    .byte $0B, $8D, $01, $82, $F0, $09, $9D, $2D, $10, $E8, $C8, $E0, $FF, $D0, $F3, $8E
    .byte $2C, $10, $60, $20, $AA, $B1, $AA, $98, $60, $A8, $8A, $4C, $91, $B3, $4C, $67
    .byte $B8, $4C, $50, $B8, $4C, $28, $BA, $4C, $0F, $24, $13, $00, $82, $28, $00, $91
    .byte $3F, $00, $93, $15, $00, $93, $F0, $00, $15, $00, $91, $FF, $00, $15, $00, $8E
    .byte $20, $5B, $BC, $C9, $01, $04, $BD, $01, $88, $80, $00, $B6, $01, $83, $10, $00
    .byte $81, $2D, $00, $10, $00, $84, $2D, $00, $10, $00, $83, $11, $00, $81, $0D, $00
    .byte $11, $00, $84, $0D, $00, $11, $00, $83, $18, $00, $5B, $00, $81, $6D, $11, $0D
    .byte $48, $03, $4A, $00, $81, $6D, $12, $0D, $AA, $68, $04, $1F, $01, $81, $8D, $13
    .byte $01, $1D, $00, $82, $A0, $10, $4E, $12, $0D, $6E, $05, $41, $00, $81, $13, $18
    .byte $01, $1B, $00, $81, $6D, $0F, $0D, $8D, $13, $0D, $AD, $14, $0D, $6D, $10, $0D
    .byte $8D, $14, $0D, $0E, $0F, $0D, $2E, $10, $0D, $88, $D0, $DC, $AD, $13, $0D, $AE
    .byte $14, $0D, $60, $AD, $11, $0D, $0D, $12, $0D, $D0, $04, $A9, $00, $AA, $60, $2A
    .byte $1C, $00, $81, $CD, $12, $0D, $90, $20, $D0, $08, $06, $09, $00, $81, $CD, $11
    .byte $0D, $90, $16, $38, $05, $15, $00, $81, $ED, $11, $0D, $8D, $0F, $0D, $AD, $10
    .byte $0D, $ED, $12, $0D, $8D, $10, $0D, $4C, $BA, $0A, $AD, $0F, $0D, $AE, $10, $0D
    .byte $17, $75, $00, $81, $A9, $00, $01, $6E, $00, $81, $20, $E9, $0A, $4C, $F6, $0A
    .byte $A5, $FB, $8D, $1F, $09, $46, $01, $81, $8D, $20, $0D, $02, $5E, $00, $83, $22
    .byte $00, $5E, $00, $82, $23, $0D, $F0, $4F, $03, $29, $00, $84, $18, $A5, $FB, $6D
    .byte $22, $04, $35, $00, $81, $25, $01, $82, $85, $FC, $01, $1B, $00, $84, $A2, $00
    .byte $2E, $00, $82, $C9, $FF, $F0, $1B, $03, $2D, $00, $81, $FD, $91, $FB, $02, $39
    .byte $00, $84, $2D, $00, $84, $EE, $22, $0D, $E8, $EC, $23, $0D, $D0, $DE, $AD, $1F
    .byte $0A, $C0, $00, $82, $20, $00, $C0, $00, $83, $AD, $22, $0D, $91, $FB, $60, $05
    .byte $B8, $00, $82, $8D, $24, $0D, $B1, $FD, $8D, $25, $0D, $07, $BB, $00, $84, $E6
    .byte $FD, $01, $B5, $00, $81, $FE, $A0, $00, $CC, $24, $0D, $F0, $10, $07, $10, $00
    .byte $82, $13, $B1, $FB, $D1, $FD, $90, $0A, $D0, $0B, $C8, $D0, $EB, $CC, $25, $0D
    .byte $F0, $06, $A9, $FF, $60, $A9, $01, $60, $A9, $00, $60, $19, $BA, $00, $81, $CF
    .byte $FF, $C9, $0D, $F0, $0A, $E0, $FF, $F0, $06, $9D, $2D, $11, $E8, $D0, $EF, $8E
    .byte $2C, $11, $60, $AC, $26, $0D, $16, $11, $00, $82, $32, $00, $11, $00, $81, $27
    .byte $00, $81, $03, $C8, $D0, $F1, $A2, $00, $CC, $2C, $11, $F0, $0F, $B9, $2D, $11
    .byte $C9, $2C, $F0, $07, $9D, $2D, $12, $E8, $C8, $D0, $ED, $C8, $8C, $26, $0D, $1C
    .byte $50, $00, $81, $0D, $BD, $2C, $12, $C9, $20, $D0, $06, $CA, $4C, $DD, $0B, $A2
    .byte $00, $8E, $2C, $12, $60, $11, $14, $00, $81, $D0, $07, $A9, $7B, $A0, $0C, $4C
    .byte $A2, $BB, $A9, $2D, $85, $22, $A9, $13, $85, $23, $AD, $2C, $12, $4C, $B5, $B7
    .byte $AD, $1D, $0D, $85, $FB, $AD, $1E, $0D, $85, $1F, $15, $00, $81, $B1, $FB, $C9
    .byte $FF, $D0, $03, $4C, $6D, $0C, $AA, $8D, $2C, $12, $E6, $FB, $D0, $02, $E6, $FC
    .byte $A0, $00, $E0, $00, $F0, $09, $B1, $FB, $99, $2D, $12, $C8, $CA, $D0, $F3, $98
    .byte $18, $65, $FB, $8D, $1D, $0D, $A5, $FC, $69, $00, $8D, $1E, $0D, $60, $6C, $FB
    .byte $00, $48, $A9, $EE, $36, $16, $00, $83, $68, $A2, $00, $20, $BD, $09, $20, $95
    .byte $09, $20, $62, $0A, $0A, $00, $83, $C4, $00, $0A, $00, $83, $4C, $74, $0C, $A9
    .byte $DA, $A0, $0C, $20, $84, $09, $AE, $2B, $0D, $9A, $4C, $38, $09, $00, $11, $05
    .byte $00, $82, $81, $00, $05, $00, $82, $84, $00, $23, $00, $82, $8B, $7F, $01, $05
    .byte $00, $81, $88, $40, $01, $0A, $00, $83, $05, $00, $81, $87, $48, $01, $0F, $00
    .byte $83, $01, $00, $0A, $00, $82, $27, $00, $00, $82, $00, $00, $05, $05, $00, $82
    .byte $1C, $00, $00, $90, $50, $15, $00, $00, $0B, $08, $08, $00, $81, $69, $74, $65
    .byte $73, $2E, $73, $70, $72, $FF, $3F, $42, $0A, $2B, $00, $81, $53, $55, $42, $53
    .byte $43, $52, $49, $50, $54, $08, $14, $00, $87, $4F, $55, $54, $20, $4F, $46, $20
    .byte $44, $41, $54, $41, $0A, $0D, $00, $84, $0D, $00, $3F, $4C, $4F, $41, $44, $20
    .byte $45, $52, $52, $4F, $52, $20, $00, $0E

; ===========================================================================
; D64PACK Stage 52 - lesbare Decruncher-Quelle (NUR KOMMENTAR)
; Modus       : LZ
; Packsuche   : balanced
; Hochspeicher: $FAF2-$FFF9
; Der oben eingebettete __d64pack_bundle enthaelt genau diesen
; Decruncher bereits als Maschinencode plus den gepackten Stream.
; Die folgenden Zeilen sind deshalb ausnahmslos Kommentare und
; veraendern beim erneuten Assemblieren das PRG nicht.
; ===========================================================================
; .nostub
; .org $FAF2
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
;     lda #<$0CFA
;     sta $F9
;     lda #>$0CFA
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
