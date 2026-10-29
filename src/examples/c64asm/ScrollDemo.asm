; -------------------------------------------------------------
; File  : ScrollDemo.asm
; Author: (c) 2026 by Blacky Cat - paule32
; -------------------------------------------------------------
; C64 HiRes 320x200 - BUNTER SINUS-TEXTSCROLLER
; Kein BASIC-Stub: Start bei $1000 per VICE "START".
;
; Bunte Zeichen werden als echte HiRes-Bitmap-Pixel gezeichnet.
; Bildschirmfarben stehen je 8x8-Zelle in $0400-$07E7.
; 8-Pixel-Glyphen mit 16-Pixel-Schritt vermeiden Farbkonflikte.
; Sinusform: y = 90 + 32 * sin(2*pi*(phase+5*index)/64)
; Kontinuierliche Bewegung: 2 Pixel pro Bildaufbau.
;
; Grafik: VIC Bank 0, Screen $0400, Bitmap $2000
; Quellcode komplett unter $2000.
; -------------------------------------------------------------
.org $1000
.nostub
.entry start

bmp_ptr   = $fb                ; 16bit Bitmapzeiger
col_ptr   = $fd                ; 16bit Farbattributzeiger

start:
    sei
    lda $dd00
    ora #$03                 ; VIC Bank 0
    sta $dd00
    lda #$18                 ; Screen $0400, Bitmap $2000
    sta $d018

    ; Schwarz fuer alle Bildschirmzellen, $10 = Weiss/Schwarz.
    lda #$10
    ldx #$00
init_colors:
    sta $0400,x
    sta $0500,x
    sta $0600,x
    sta $0700,x
    inx
    bne init_colors

    jsr clear_bitmap          ; Alle 8 KB nur beim Start loeschen

    lda #$00
    sta $d020                ; schwarzer Rahmen
    sta $d021                ; schwarzer Hintergrund
    lda $d016
    and #$ef                 ; HiRes (kein Multicolor)
    sta $d016
    lda $d011
    ora #$20                 ; Bitmap-Modus einschalten
    sta $d011

    lda #$40                 ; Anfang X=320 = $0140
    sta scroll_lo
    lda #$01
    sta scroll_hi
    lda #$00
    sta phase

frame_loop:
    jsr clear_band           ; Voriges Bild entfernen
    lda scroll_lo
    sta curr_lo
    lda scroll_hi
    sta curr_hi
    lda #$00
    sta msg_idx

char_loop:
    ldx msg_idx
    lda message,x
    cmp #$ff                 ; Text-Ende
    beq char_end

    ; Leerzeichen muessen nicht geplottet werden.
    cmp #$00
    beq next_char

    ; Nur X = -7..319 zeichnen (Teil-Clipping links/rechts).
    lda curr_hi
    beq char_visible
    cmp #$01
    beq check_right
    cmp #$ff
    bne next_char
    lda curr_lo
    cmp #$f9                 ; Negatives X: -7..-1
    bcs char_visible
    jmp next_char
check_right:
    lda curr_lo
    cmp #$40                 ; X<=319
    bcs next_char
char_visible:
    jsr draw_char

next_char:
    ; Nächstes Zeichen liegt 16 Pixel weiter rechts.
    clc
    lda curr_lo
    adc #16
    sta curr_lo
    lda curr_hi
    adc #0
    sta curr_hi
    inc msg_idx
    jmp char_loop

char_end:
    jsr wait_frame
    inc phase                ; Sinuswelle wandert

    ; Globale Textposition pro Bild um zwei Pixel nach links.
    sec
    lda scroll_lo
    sbc #2
    sta scroll_lo
    lda scroll_hi
    sbc #0
    sta scroll_hi

    ; Nach 30 Zeichen * 16 = 480 Pixeln neu von rechts.
    ; -480 = $fe20.
    lda scroll_hi
    cmp #$fe
    bne frame_loop
    lda scroll_lo
    cmp #$20
    bne frame_loop
    lda #$40
    sta scroll_lo
    lda #$01
    sta scroll_hi
    jmp frame_loop

; -------------------------------------------------------------
; Sichtbaren Glyph positionieren, Zeilen plotten und Farbe setzen
; -------------------------------------------------------------
draw_char:
    ; sin(phase + 5 * msg_idx) aus 64er Tabelle
    lda msg_idx
    asl a
    asl a
    clc
    adc msg_idx
    adc phase
    and #$3f
    tax
    lda sine_y,x
    sta glyph_y

    ; In 8x8-Bitmap-Zellen aufteilen.
    lda curr_lo
    and #$07
    sta xshift
    lda curr_lo
    and #$f8
    sta xbyte
    lda curr_lo
    lsr a
    lsr a
    lsr a
    sta cell_x
    lda #0
    sta high_add
    sta left_clip

    lda curr_hi
    beq x_prepared
    cmp #$ff
    beq x_negative
    ; X=256..319: Bitmap-Adresse um $0100 erhöhen.
    inc high_add
    lda cell_x
    clc
    adc #32
    sta cell_x
    jmp x_prepared
x_negative:
    ; X=-7..-1: nur rechter Teil des Glyphen in Spalte 0.
    lda #1
    sta left_clip
    lda #0
    sta xbyte
    sta cell_x
x_prepared:
    ; Farbwechsel je Zeichen + langsam laufender Farbbogen.
    lda phase
    lsr a
    lsr a
    lsr a
    clc
    adc msg_idx
    and #$07
    tax
    lda palette,x
    sta glyph_color

    ; Font-Offset = glyph_number * 8.
    ldx msg_idx
    lda message,x
    asl a
    asl a
    asl a
    sta font_base
    lda #0
    sta glyph_row
row_loop:
    ; 8 Pixel horizontale Schriftzeile holen.
    lda glyph_row
    clc
    adc font_base
    tax
    lda font_data,x
    sta row_left
    lda #0
    sta row_right

    ; Beliebige Pixel-X-Position: Fontreihe 0..7 Bit shiften.
    ldx xshift
    beq shifted
shift_loop:
    lsr row_left
    ror row_right
    dex
    bne shift_loop
shifted:
    lda row_left
    ora row_right
    beq row_next           ; Leere Schriftzeile überspringen

    ; Bitmap-Basis des Y-Pixels + X-Zellenoffset ($00,$08..$f8).
    lda glyph_y
    clc
    adc glyph_row
    sta pixel_y
    tay
    lda bitmap_lo,y
    clc
    adc xbyte
    sta bmp_ptr
    lda bitmap_hi,y
    adc high_add
    sta bmp_ptr+1

    ; Screen-Farbadresse: $0400 + (Y/8)*40 + (X/8)
    lda pixel_y
    lsr a
    lsr a
    lsr a
    tay
    lda screen_lo,y
    clc
    adc cell_x
    sta col_ptr
    lda screen_hi,y
    adc #0
    sta col_ptr+1

    ; Erster Glyphenteil (falls links nicht abgeschnitten).
    lda left_clip
    bne right_part
    ldy #0
    lda row_left
    beq right_part
    ora (bmp_ptr),y
    sta (bmp_ptr),y
    lda glyph_color
    sta (col_ptr),y

right_part:
    lda row_right
    beq row_next
    lda left_clip
    bne right_clipped_left
    lda cell_x
    cmp #39
    beq row_next          ; Am rechten Rand nicht hinausschreiben
    ldy #8
    jmp write_right
right_clipped_left:
    ldy #0                ; X=-7..-1, rechter Teil bei Spalte 0
write_right:
    lda row_right
    ora (bmp_ptr),y
    sta (bmp_ptr),y
    ldy #1
    lda left_clip
    bne color_left
    lda glyph_color
    sta (col_ptr),y
    jmp row_next
color_left:
    ldy #0
    lda glyph_color
    sta (col_ptr),y

row_next:
    inc glyph_row
    lda glyph_row
    cmp #8
    bne row_loop
    rts

; -------------------------------------------------------------
; Nur $2800..$37ff ausnullen: komplette Sinus-Zeichenregion.
; Die Schrift liegt zwischen Y=58 und Y=129 (max 8 Pixel).
; -------------------------------------------------------------
clear_bitmap:
    lda #$00
    sta bmp_ptr
    lda #$20
    sta bmp_ptr+1
    ldx #32
    jmp clear_pages

clear_band:
    lda #$00
    sta bmp_ptr
    lda #$28
    sta bmp_ptr+1
    ldx #16
clear_pages:
    lda #$00
clear_page:
    ldy #$00
clear_byte:
    sta (bmp_ptr),y
    iny
    bne clear_byte
    inc bmp_ptr+1
    dex
    bne clear_page
    rts

wait_frame:
not_250:
    lda $d012
    cmp #250
    beq not_250
find_250:
    lda $d012
    cmp #250
    bne find_250
    rts

; -------------------------------------------------------------
; Font 8x8; Schrift "C64  HIRES  SINUS  SCROLLER!  "
; Fontindex: 0 Leerzeichen, 1 C, 2 6, 3 4, 4 H, 5 I, 6 R,
;            7 E, 8 S, 9 N, 10 U, 11 O, 12 L, 13 !
; -------------------------------------------------------------
message:
    .byte $01,$02,$03,$00,$00,$04,$05,$06,$07,$08,$00,$00
    .byte $08,$05,$09,$0a,$08,$00,$00,$08,$01,$06,$0b,$0c
    .byte $0c,$07,$06,$0d,$00,$00,$ff

palette:
    .byte $10,$70,$30,$50,$d0,$e0,$80,$40

font_data:
    .byte $00,$00,$00,$00,$00,$00,$00,$00
    .byte $78,$cc,$80,$80,$80,$cc,$78,$00
    .byte $3c,$60,$c0,$f8,$cc,$cc,$78,$00
    .byte $1c,$3c,$6c,$cc,$fe,$0c,$0c,$00
    .byte $cc,$cc,$cc,$fc,$cc,$cc,$cc,$00
    .byte $fc,$30,$30,$30,$30,$30,$fc,$00
    .byte $f8,$cc,$cc,$f8,$d8,$cc,$cc,$00
    .byte $fc,$c0,$c0,$f8,$c0,$c0,$fc,$00
    .byte $7c,$c0,$c0,$78,$0c,$0c,$f8,$00
    .byte $cc,$ec,$fc,$dc,$cc,$cc,$cc,$00
    .byte $cc,$cc,$cc,$cc,$cc,$cc,$78,$00
    .byte $78,$cc,$cc,$cc,$cc,$cc,$78,$00
    .byte $c0,$c0,$c0,$c0,$c0,$c0,$fc,$00
    .byte $30,$30,$30,$30,$30,$00,$30,$00

sine_y:
    .byte $5a,$5d,$60,$63,$66,$69,$6c,$6e,$71,$73,$75,$76,$78,$79,$79,$7a
    .byte $7a,$7a,$79,$79,$78,$76,$75,$73,$71,$6e,$6c,$69,$66,$63,$60,$5d
    .byte $5a,$57,$54,$51,$4e,$4b,$48,$46,$43,$41,$3f,$3e,$3c,$3b,$3b,$3a
    .byte $3a,$3a,$3b,$3b,$3c,$3e,$3f,$41,$43,$46,$48,$4b,$4e,$51,$54,$57

; Pixelbasis HiRes: $2000 + (Y/8)*320 + Y%8
bitmap_lo:
    .byte $00,$01,$02,$03,$04,$05,$06,$07,$40,$41,$42,$43,$44,$45,$46,$47
    .byte $80,$81,$82,$83,$84,$85,$86,$87,$c0,$c1,$c2,$c3,$c4,$c5,$c6,$c7
    .byte $00,$01,$02,$03,$04,$05,$06,$07,$40,$41,$42,$43,$44,$45,$46,$47
    .byte $80,$81,$82,$83,$84,$85,$86,$87,$c0,$c1,$c2,$c3,$c4,$c5,$c6,$c7
    .byte $00,$01,$02,$03,$04,$05,$06,$07,$40,$41,$42,$43,$44,$45,$46,$47
    .byte $80,$81,$82,$83,$84,$85,$86,$87,$c0,$c1,$c2,$c3,$c4,$c5,$c6,$c7
    .byte $00,$01,$02,$03,$04,$05,$06,$07,$40,$41,$42,$43,$44,$45,$46,$47
    .byte $80,$81,$82,$83,$84,$85,$86,$87,$c0,$c1,$c2,$c3,$c4,$c5,$c6,$c7
    .byte $00,$01,$02,$03,$04,$05,$06,$07,$40,$41,$42,$43,$44,$45,$46,$47
    .byte $80,$81,$82,$83,$84,$85,$86,$87,$c0,$c1,$c2,$c3,$c4,$c5,$c6,$c7
    .byte $00,$01,$02,$03,$04,$05,$06,$07,$40,$41,$42,$43,$44,$45,$46,$47
    .byte $80,$81,$82,$83,$84,$85,$86,$87,$c0,$c1,$c2,$c3,$c4,$c5,$c6,$c7
    .byte $00,$01,$02,$03,$04,$05,$06,$07
bitmap_hi:
    .byte $20,$20,$20,$20,$20,$20,$20,$20,$21,$21,$21,$21,$21,$21,$21,$21
    .byte $22,$22,$22,$22,$22,$22,$22,$22,$23,$23,$23,$23,$23,$23,$23,$23
    .byte $25,$25,$25,$25,$25,$25,$25,$25,$26,$26,$26,$26,$26,$26,$26,$26
    .byte $27,$27,$27,$27,$27,$27,$27,$27,$28,$28,$28,$28,$28,$28,$28,$28
    .byte $2a,$2a,$2a,$2a,$2a,$2a,$2a,$2a,$2b,$2b,$2b,$2b,$2b,$2b,$2b,$2b
    .byte $2c,$2c,$2c,$2c,$2c,$2c,$2c,$2c,$2d,$2d,$2d,$2d,$2d,$2d,$2d,$2d
    .byte $2f,$2f,$2f,$2f,$2f,$2f,$2f,$2f,$30,$30,$30,$30,$30,$30,$30,$30
    .byte $31,$31,$31,$31,$31,$31,$31,$31,$32,$32,$32,$32,$32,$32,$32,$32
    .byte $34,$34,$34,$34,$34,$34,$34,$34,$35,$35,$35,$35,$35,$35,$35,$35
    .byte $36,$36,$36,$36,$36,$36,$36,$36,$37,$37,$37,$37,$37,$37,$37,$37
    .byte $39,$39,$39,$39,$39,$39,$39,$39,$3a,$3a,$3a,$3a,$3a,$3a,$3a,$3a
    .byte $3b,$3b,$3b,$3b,$3b,$3b,$3b,$3b,$3c,$3c,$3c,$3c,$3c,$3c,$3c,$3c
    .byte $3e,$3e,$3e,$3e,$3e,$3e,$3e,$3e

; Screenfarbe: $0400 + 40*(Y/8)
screen_lo:
    .byte $00,$28,$50,$78,$a0,$c8,$f0,$18,$40,$68,$90,$b8,$e0,$08,$30,$58
    .byte $80,$a8,$d0,$f8,$20,$48,$70,$98,$c0
screen_hi:
    .byte $04,$04,$04,$04,$04,$04,$04,$05,$05,$05,$05,$05,$05,$06,$06,$06
    .byte $06,$06,$06,$06,$07,$07,$07,$07,$07

; Arbeitsvariablen:
scroll_lo:    .byte 0
scroll_hi:    .byte 0
curr_lo:      .byte 0
curr_hi:      .byte 0
phase:        .byte 0
msg_idx:      .byte 0
glyph_y:      .byte 0
glyph_row:    .byte 0
font_base:    .byte 0
xshift:       .byte 0
xbyte:        .byte 0
cell_x:       .byte 0
high_add:     .byte 0
left_clip:    .byte 0
row_left:     .byte 0
row_right:    .byte 0
pixel_y:      .byte 0
glyph_color:  .byte 0
