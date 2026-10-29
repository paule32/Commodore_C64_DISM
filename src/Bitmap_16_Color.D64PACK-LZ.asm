
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
    lda #<$F9E3
    sta $F9
    lda #>$F9E3
    sta $FA
    lda #<$0617
    sta $FB
    lda #>$0617
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
    jmp $F9E3

; D64PACK v1 inspectable header (not needed by the decrunch loop itself).
__d64pack_header:
    .byte $44, $36, $34, $50
    .byte $01, $02, $02, $00
    .word $0801
    .word $0594
    .word $080D
    .word $0537

__d64pack_bundle:
    .byte $A9, $68, $8D, $00, $C0, $A9, $85, $8D, $01, $C0, $A9, $01, $8D, $02, $C0, $A9
    .byte $68, $8D, $03, $C0, $A9, $A8, $8D, $04, $C0, $A9, $68, $8D, $05, $C0, $A9, $AA
    .byte $8D, $06, $C0, $A9, $68, $8D, $07, $C0, $A9, $28, $8D, $08, $C0, $A9, $4C, $8D
    .byte $09, $C0, $A9, $0D, $8D, $0A, $C0, $A9, $08, $8D, $0B, $C0, $A9, $F9, $85, $F7
    .byte $A9, $FF, $85, $F8, $A9, $94, $85, $F9, $A9, $0D, $85, $FA, $A0, $00, $B1, $F7
    .byte $C9, $80, $F0, $53, $B0, $17, $AA, $E8, $20, $A8, $FA, $A0, $00, $B1, $F7, $91
    .byte $F9, $20, $A8, $FA, $20, $B1, $FA, $CA, $D0, $F1, $4C, $2F, $FA, $29, $7F, $18
    .byte $69, $02, $AA, $20, $A8, $FA, $A0, $00, $B1, $F7, $85, $FE, $20, $A8, $FA, $A0
    .byte $00, $B1, $F7, $85, $FD, $20, $A8, $FA, $18, $A5, $FD, $65, $F9, $85, $FD, $A5
    .byte $FE, $65, $FA, $85, $FE, $A0, $00, $B1, $FD, $91, $F9, $20, $BA, $FA, $20, $B1
    .byte $FA, $CA, $D0, $F1, $4C, $2F, $FA, $68, $85, $FF, $68, $85, $FE, $68, $85, $FD
    .byte $68, $85, $FC, $68, $85, $FB, $68, $85, $FA, $68, $85, $F9, $68, $85, $F8, $68
    .byte $85, $F7, $4C, $00, $C0, $A5, $F7, $D0, $02, $C6, $F8, $C6, $F7, $60, $A5, $F9
    .byte $D0, $02, $C6, $FA, $C6, $F9, $60, $A5, $FD, $D0, $02, $C6, $FE, $C6, $FD, $60
    .byte $80, $0B, $08, $0A, $00, $9E, $32, $30, $36, $31, $08, $54, $05, $81, $20, $47
    .byte $08, $BA, $8E, $BB, $0D, $A9, $6A, $08, $35, $03, $81, $A9, $0D, $01, $37, $03
    .byte $81, $20, $59, $0B, $A9, $AC, $04, $0A, $00, $87, $F6, $A0, $0C, $02, $0A, $00
    .byte $84, $A9, $3F, $01, $07, $04, $81, $54, $0C, $20, $F0, $0B, $20, $F6, $0B, $60
    .byte $20, $CC, $0A, $5B, $02, $81, $95, $85, $FB, $A9, $03, $14, $02, $81, $A9, $00
    .byte $A2, $06, $F0, $0C, $A0, $00, $07, $10, $00, $82, $FB, $E6, $FC, $CA, $D0, $F4
    .byte $A0, $00, $C0, $2E, $F0, $05, $91, $FB, $C8, $0E, $22, $00, $81, $A9, $0D, $4C
    .byte $D2, $FF, $04, $1D, $00, $86, $AA, $F0, $11, $02, $B2, $01, $83, $10, $00, $83
    .byte $12, $00, $81, $B9, $02, $81, $F7, $60, $01, $C5, $03, $87, $06, $20, $D2, $FF
    .byte $C8, $D0, $F6, $60, $07, $06, $00, $81, $4C, $8F, $08, $20, $DD, $BD, $85, $FD
    .byte $84, $FE, $A2, $00, $0B, $8F, $01, $82, $F0, $09, $9D, $BD, $10, $E8, $C8, $E0
    .byte $FF, $D0, $F3, $8E, $BC, $10, $60, $20, $9B, $BC, $A5, $65, $A6, $64, $60, $A8
    .byte $8A, $4C, $91, $B3, $4C, $67, $B8, $4C, $50, $B8, $4C, $28, $BA, $4C, $0F, $26
    .byte $13, $00, $82, $28, $00, $91, $3F, $00, $93, $15, $00, $93, $F0, $00, $15, $00
    .byte $91, $FF, $00, $15, $00, $8E, $20, $5B, $BC, $C9, $01, $04, $BD, $01, $88, $65
    .byte $00, $B6, $01, $83, $10, $00, $81, $2D, $00, $10, $00, $84, $2D, $00, $10, $00
    .byte $83, $11, $00, $81, $0D, $00, $11, $00, $84, $0D, $00, $11, $00, $83, $18, $00
    .byte $5B, $00, $81, $6D, $A1, $0D, $48, $03, $4A, $00, $81, $6D, $A2, $0D, $AA, $68
    .byte $60, $05, $37, $02, $81, $A3, $00, $1D, $00, $82, $A0, $10, $4E, $A2, $0D, $6E
    .byte $05, $41, $00, $81, $13, $18, $01, $1B, $00, $81, $6D, $9F, $0D, $8D, $A3, $0D
    .byte $AD, $A4, $0D, $6D, $A0, $0D, $8D, $A4, $0D, $0E, $9F, $0D, $2E, $A0, $0D, $88
    .byte $D0, $DC, $AD, $A3, $0D, $AE, $A4, $0D, $60, $AD, $A1, $0D, $0D, $A2, $0D, $D0
    .byte $04, $A9, $00, $AA, $60, $2A, $1C, $00, $81, $CD, $A2, $0D, $90, $20, $D0, $08
    .byte $06, $09, $00, $81, $CD, $A1, $0D, $90, $16, $38, $05, $15, $00, $81, $ED, $A1
    .byte $0D, $8D, $9F, $0D, $AD, $A0, $0D, $ED, $A2, $0D, $8D, $0C, $1C, $01, $81, $C7
    .byte $09, $AD, $9F, $0D, $AE, $A0, $0D, $60, $A0, $09, $E9, $01, $81, $6E, $00, $81
    .byte $20, $F6, $09, $4C, $03, $0A, $A5, $FB, $8D, $AF, $09, $46, $01, $81, $8D, $B0
    .byte $0D, $02, $5E, $00, $83, $B2, $00, $5E, $00, $82, $B3, $0D, $F0, $4F, $03, $29
    .byte $00, $84, $18, $A5, $FB, $6D, $B2, $04, $35, $00, $81, $25, $01, $82, $85, $FC
    .byte $01, $1B, $00, $84, $A2, $00, $2E, $00, $82, $C9, $FF, $F0, $1B, $03, $2D, $00
    .byte $81, $FD, $91, $FB, $02, $39, $00, $84, $2D, $00, $84, $EE, $B2, $0D, $E8, $EC
    .byte $B3, $0D, $D0, $DE, $AD, $AF, $0A, $C0, $00, $82, $B0, $00, $C0, $00, $83, $AD
    .byte $B2, $0D, $91, $FB, $60, $A0, $00, $07, $1A, $02, $81, $B4, $0D, $B1, $FD, $8D
    .byte $B5, $0D, $06, $BB, $00, $84, $27, $02, $84, $A0, $00, $CC, $B4, $0D, $F0, $10
    .byte $06, $10, $00, $82, $13, $B1, $FB, $D1, $FD, $90, $0A, $D0, $0B, $C8, $D0, $EB
    .byte $CC, $B5, $0D, $F0, $06, $A9, $FF, $60, $A9, $01, $60, $A9, $00, $60, $A2, $00
    .byte $20, $CF, $FF, $C9, $0D, $F0, $0A, $E0, $FF, $F0, $06, $9D, $BD, $11, $E8, $D0
    .byte $EF, $8E, $BC, $11, $60, $AC, $B6, $0D, $33, $11, $00, $82, $32, $00, $11, $00
    .byte $81, $27, $00, $81, $03, $C8, $D0, $F1, $A2, $00, $CC, $BC, $11, $F0, $0F, $B9
    .byte $BD, $11, $C9, $2C, $F0, $07, $9D, $BD, $12, $E8, $C8, $D0, $ED, $C8, $8C, $B6
    .byte $0D, $1C, $50, $00, $81, $0D, $BD, $BC, $12, $C9, $20, $D0, $06, $CA, $4C, $EA
    .byte $0A, $A2, $00, $8E, $BC, $12, $60, $11, $14, $00, $81, $D0, $07, $01, $C2, $00
    .byte $81, $0D, $4C, $A2, $BB, $A9, $BD, $85, $22, $A9, $12, $85, $23, $AD, $BC, $12
    .byte $4C, $B5, $B7, $AD, $AD, $0D, $85, $FB, $AD, $AE, $0D, $85, $1A, $35, $01, $83
    .byte $C9, $FF, $D0, $03, $4C, $46, $0C, $AA, $8D, $BC, $12, $0A, $6B, $01, $83, $20
    .byte $01, $81, $E0, $00, $F0, $09, $B1, $FB, $99, $BD, $12, $C8, $09, $39, $01, $81
    .byte $98, $18, $65, $FB, $8D, $AD, $0D, $A5, $FC, $69, $00, $8D, $AE, $0D, $60, $6C
    .byte $FB, $00, $11, $9D, $00, $81, $D0, $40, $01, $40, $00, $81, $8D, $BE, $13, $02
    .byte $49, $00, $81, $8D, $BF, $13, $02, $4B, $00, $81, $8D, $C0, $13, $AD, $18, $D0
    .byte $8D, $C1, $13, $AD, $21, $D0, $8D, $C2, $13, $0E, $7F, $00, $82, $D8, $9D, $00
    .byte $48, $BD, $00, $D9, $9D, $00, $49, $BD, $00, $DA, $9D, $00, $4A, $BD, $00, $DB
    .byte $9D, $00, $4B, $15, $7F, $00, $81, $A9, $01, $01, $9D, $00, $81, $AD, $00, $DD
    .byte $29, $FC, $09, $02, $06, $76, $00, $81, $A9, $18, $01, $83, $00, $82, $11, $D0
    .byte $09, $20, $03, $6F, $00, $82, $16, $D0, $09, $10, $8D, $16, $05, $79, $00, $81
    .byte $74, $00, $81, $20, $C6, $0B, $60, $A9, $60, $A0, $20, $07, $07, $00, $82, $44
    .byte $00, $07, $00, $83, $A9, $D8, $A0, $04, $20, $DC, $0B, $60, $8D, $E5, $0B, $A2
    .byte $00, $A9, $00, $9D, $00, $60, $E8, $D0, $FA, $EE, $E5, $0B, $88, $D0, $F0, $60
    .byte $20, $E4, $FF, $F0, $FB, $60, $AD, $BD, $13, $F0, $40, $A2, $00, $BD, $00, $48
    .byte $9D, $00, $D8, $BD, $00, $49, $9D, $00, $D9, $BD, $00, $4A, $9D, $00, $DA, $BD
    .byte $00, $4B, $9D, $00, $DB, $E8, $D0, $E5, $AD, $BE, $13, $8D, $00, $DD, $AD, $BF
    .byte $13, $8D, $11, $D0, $AD, $C0, $13, $8D, $16, $D0, $AD, $C1, $13, $8D, $18, $D0
    .byte $AD, $C2, $13, $8D, $21, $D0, $A9, $00, $8D, $BD, $13, $60, $A9, $6B, $69, $0A
    .byte $00, $83, $4C, $4D, $0C, $A9, $81, $A0, $0D, $20, $8F, $08, $AE, $BB, $0D, $9A
    .byte $4C, $43, $08, $85, $FB, $84, $FC, $A0, $00, $B1, $FB, $F0, $4D, $AA, $1B, $07
    .byte $00, $84, $11, $00, $82, $B1, $FB, $85, $FE, $03, $0A, $00, $81, $8A, $30, $10
    .byte $B1, $FB, $91, $FD, $06, $15, $00, $81, $1A, $00, $83, $F3, $00, $1A, $00, $81
    .byte $49, $FF, $AA, $E8, $B1, $FB, $8D, $BC, $13, $20, $9D, $0C, $AD, $BC, $13, $91
    .byte $FD, $20, $A4, $0C, $CA, $D0, $F5, $4C, $58, $0C, $E6, $FB, $1B, $07, $00, $81
    .byte $FC, $60, $E6, $FD, $D0, $02, $E6, $FE, $60, $60, $F8, $E8, $6C, $05, $E0, $F0
    .byte $6C, $5A, $F8, $10, $13, $4A, $00, $81, $20, $00, $93, $00, $81, $28, $00, $4A
    .byte $00, $81, $50, $00, $4A, $00, $81, $60, $6F, $05, $E8, $68, $04, $4E, $00, $81
    .byte $80, $6F, $01, $3E, $00, $82, $05, $00, $3E, $00, $81, $50, $06, $9D, $45, $10
    .byte $04, $5D, $00, $83, $07, $C4, $45, $60, $03, $3F, $00, $81, $9A, $AB, $B0, $07
    .byte $EC, $45, $C0, $06, $3F, $00, $82, $10, $10, $01, $4D, $00, $82, $55, $D8, $10
    .byte $6D, $5A, $F8, $38, $6D, $50, $08, $49, $00, $81, $55, $D8, $50, $6E, $5A, $F8
    .byte $78, $6E, $50, $F8, $88, $6F, $00, $F8, $90, $6F, $05, $E0, $98, $6F, $5A, $F8
    .byte $B8, $6F, $50, $07, $A1, $45, $40, $45, $56, $67, $78, $89, $90, $07, $C9, $45
    .byte $A0, $AB, $BC, $CD, $DE, $EF, $F0, $01, $F1, $45, $00, $05, $F3, $45, $12, $23
    .byte $34, $45, $50, $00, $E0, $E8, $6C, $00, $F8, $08, $6D, $05, $D8, $20, $6E, $00
    .byte $F8, $48, $6E, $05, $D8, $60, $6F, $00, $FC, $9D, $4F, $04, $00, $81, $C4, $45
    .byte $00, $FB, $EC, $45, $05, $01, $00, $84, $00, $81, $01, $01, $00, $81, $00, $FF
    .byte $3F, $42, $41, $44, $20, $53, $55, $42, $53, $43, $52, $49, $50, $54, $0F, $14
    .byte $00, $86, $3F, $4F, $55, $54, $20, $4F, $46, $20, $44, $41, $54, $41, $20, $45
    .byte $52, $52, $4F, $52, $0D, $00, $13

; ===========================================================================
; D64PACK Stage 52 - lesbare Decruncher-Quelle (NUR KOMMENTAR)
; Modus       : LZ
; Packsuche   : balanced
; Hochspeicher: $F9E3-$FFF9
; Der oben eingebettete __d64pack_bundle enthaelt genau diesen
; Decruncher bereits als Maschinencode plus den gepackten Stream.
; Die folgenden Zeilen sind deshalb ausnahmslos Kommentare und
; veraendern beim erneuten Assemblieren das PRG nicht.
; ===========================================================================
; .nostub
; .org $F9E3
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
;     lda #<$0D94
;     sta $F9
;     lda #>$0D94
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
