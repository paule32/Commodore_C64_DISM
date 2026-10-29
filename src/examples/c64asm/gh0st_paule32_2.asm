; -------------------------------------------------------------
; File  : gh0st_paule32_2.asm
; Author: (c) 2026 by Blacky Cat - paule32
; -------------------------------------------------------------
; C64 MULTICOLOR 160x200 (320 physische Bildschirm-Pixel)
; SINUS-WANDERLICHT MIT 8 OPTISCHEN BLAUSTUFEN + VIER TEXTZEILEN
; Ausgehend von der HiRes Sinus-Wanderlicht-Demo (Stage 500).
;
; Balken: X 0..319 physisch, Y 84..115 (32 Pixel hoch).
;   Nur die Farben/Helligkeiten wandern; Balken selbst bleibt fest.
;   Peak: 2 Pixel hoch, Sinus +/- 4 Pixel, 5 kleine Wellen.
;   Blau-Schweif bleicht nach und nach bis Schwarz aus.
;
; Multicolor-Bitmap: reale Aufloesung 160x200 Farbpixel
;   00 = $d021 schwarz (0)
;   01 = Screen high nibble blau (6)
;   10 = Screen low nibble hellblau (14)
;   11 = Color RAM cyan (3), in diesem Demo nicht benoetigt.
; Die 8 Blaustufen (+ Schwarz) sind Dither-Abstufungen, keine acht
; verschiedenen C64-Hardware-Blautone.
;
; URL oben: https://crazy-midi.de, Y=24..39, zentriert, gruen.
; Oberer Text: gh0st  &  paule32, Y=56..71, zentriert, weiss.
; Unterer Text: Commodore C= 64, Y=152..167, zentriert, gelb.
; URL unten: https://kallup.net, Y=176..191, zentriert, gruen.
; Alle Texte verwenden eigene Screen-RAM-Kacheln: Code 01 = Vordergrund,
; Code 00 = Schwarz. URLs: gruen (C64-Farbe 5).
; Text und 8 Blaustufen bleiben voneinander unabhaengig.
; Start: .org $1000, SYS 4096, VICE "Programm uebertragen + START"
; -------------------------------------------------------------
.org $1000
.nostub
.entry start

ptr        = $fb            ; Zeiger auf die aktuelle Bitmapzelle
step       = $fd            ; Nummer der Doppelzeile 0..15
peak       = $fe            ; Position des weissen Streifens 0..15
direction  = $ff            ; 0 = abwaerts, 1 = aufwaerts
pixel_a    = $f9            ; Dither-Maske fuer erste Pixelzeile
pixel_b    = $fa            ; Dither-Maske fuer zweite Pixelzeile
column     = $f5            ; 8-Pixel-Block X=0..39
waveval    = $f6            ; Sinusverschiebung fuer aktuellen Block
phase      = $f7            ; seitliche Wanderphase der Sinuswellen
tick       = $f8            ; bremst die seitliche Sinusphase

top_ptr    = $e0            ; obere Bitmapzeile Y=152
bottom_ptr = $e2            ; untere Bitmapzeile Y=160
font_ptr   = $e4            ; Glyphendaten (je 8 Zeilen)
draw_ptr   = $e6            ; aktive Bitmapzeile
text_col   = $e8            ; Bildschirm-Spalte 5..34
font_byte  = $e9            ; aktuelles Glyphenbyte
row_offset = $ea            ; lokaler 2-Pixel-Zeilenoffset

start:
    sei
    ; VIC-Bank 0, Screen $0400, Bitmap $2000.
    lda $dd00
    ora #$03
    sta $dd00
    lda #$18
    sta $d018

    ; 2-Bit-Pixelfarben: 00 Schwarz, 01 Blau, 10 Hellblau, 11 Cyan.
    ; Screen-RAM High Nibble = 6 (Blau), Low Nibble = 14 (Hellblau).
    lda #$6e
    ldx #$00
init_colors:
    sta $0400,x
    sta $0500,x
    sta $0600,x
    sta $0700,x
    inx
    bne init_colors

    ; Color-RAM ist die 4. Farbe des Multicolor-Bitmap-Modus:
    ; hier Cyan (#3) als vorbereitete Reserve fuer Code 11.
    lda #$03
    ldx #$00
init_color_ram:
    sta $d800,x
    sta $d900,x
    sta $da00,x
    sta $db00,x
    inx
    bne init_color_ram

    ; Gesamte 8-KB-Bitmap gegen alte Pixel / Streifen loeschen.
    lda #$00
    sta ptr
    lda #$20
    sta ptr+1
    ldx #$20
    lda #$00
clear_page:
    ldy #$00
clear_byte:
    sta (ptr),y
    iny
    bne clear_byte
    inc ptr+1
    dex
    bne clear_page

    ; Anfangswerte und Helligkeiten aller Zeilen loeschen.
    lda #$00
    sta peak                ; Kopf zunaechst bei Y=84..85
    sta direction           ; Bewegung nach unten
    sta phase               ; Sinus startet mit Phase 0
    sta tick
    ldx #$00
init_levels:
    sta levels,x
    inx
    cpx #16
    bne init_levels

    lda #$00
    sta $d020              ; Rahmen schwarz
    sta $d021              ; Hintergrund schwarz
    lda $d016
    ora #$10               ; MultiColor Bitmap (Bit 4 setzen)
    sta $d016
    lda $d011
    ora #$20               ; Bitmap-Modus
    sta $d011

    ; Der Gesamtbildschirm wurde oben auf Schwarz gesetzt.
    ; Alle vier Textzeilen NUR EINMAL zeichnen: Die Animationsroutine
    ; aendert ausschliesslich die Bitmap-Zeilen Y=84..115.
    jsr draw_urls
    jsr draw_upper_title
    jsr draw_caption

animation:
    ; Maximales Hellblau (8) im Wanderzentrum.
    ldx peak
    lda #8
    sta levels,x

    lda #0
    sta step
render_rows:
    ; Start des aktuellen 2-Zeilen-Bitmapstreifens.
    ldx step
    lda line_addr_lo,x
    sta ptr
    lda line_addr_hi,x
    sta ptr+1
    lda #0
    sta column

next_cell:
    ; Fuer jeden 8-Pixel-Bereich gibt die Sinustabelle eine
    ; Verschiebung von -2 bis +2 Doppelzeilen vor (+/-4 Pixel).
    ; Gleiches Profil fuer Weiss und seinen verblassenden Schweif:
    ; beide bilden gemeinsam eine mitbewegte Sinuskurve.
    lda column
    clc
    adc phase
    and #$0f
    tax
    lda sine_offsets,x      ; 0..4, 2 entspricht 0 Pixel
    sta waveval

    ; Helligkeit aus der um den Sinus verschobenen Doppelzeile.
    ; Ausserhalb des 32-Pixel-Balkens: Schwarz.
    lda step
    clc
    adc #2
    sec
    sbc waveval
    bcc dark_cell
    cmp #16
    bcs dark_cell
    tax
    lda levels,x
    tax
    lda level_even,x
    sta pixel_a
    lda level_odd,x
    sta pixel_b
    jmp draw_cell

dark_cell:
    lda #$00
    sta pixel_a
    sta pixel_b

draw_cell:
    ldy #0
    lda pixel_a
    sta (ptr),y
    iny
    lda pixel_b
    sta (ptr),y
    clc
    lda ptr
    adc #8
    sta ptr
    bcc no_page
    inc ptr+1
no_page:
    inc column
    lda column
    cmp #40
    bne next_cell

    inc step
    lda step
    cmp #16
    bne render_rows

    ; Balken steht still. Nur Licht, Wellen und Schweif wandern.
    jsr wait_frame

    ; Sinuswelle seitlich weiterlaufen lassen (alle zwei Bilder).
    inc tick
    lda tick
    and #1
    bne keep_phase
    inc phase
keep_phase:

    ; Nach jedem Bild verliert jede weisse Doppelzeile genau
    ; eine Helligkeitsstufe, bis sie schwarz ist.
    ; Auch beim Wenden bleibt der alte Schweif vorerst erhalten.
    ldx #0
fade_loop:
    lda levels,x
    beq fade_next
    sec
    sbc #1
    sta levels,x
fade_next:
    inx
    cpx #16
    bne fade_loop

    ; Wanderposition zwischen 0 (oben) und 15 (unten) pendeln.
    lda direction
    bne move_up
move_down:
    lda peak
    cmp #15
    bne continue_down
    lda #1
    sta direction
    dec peak
    jmp animation
continue_down:
    inc peak
    jmp animation

move_up:
    lda peak
    bne continue_up
    lda #0
    sta direction
    inc peak
    jmp animation
continue_up:
    dec peak
    jmp animation

; Auf Rasterzeile $f8 warten (PAL und NTSC).
wait_frame:
wait_not_f8:
    lda $d012
    cmp #$f8
    beq wait_not_f8
wait_is_f8:
    lda $d012
    cmp #$f8
    bne wait_is_f8
    rts


; ---------------------------------------------------------------
; Zwei GRUENE URLs, vorgerendert als echte C64-Multicolor-Bitmap.
; Jedes Zeichen: 5x8 Pixel plus eine Leerspalte, zweifach vertikal.
; Zeichenbreite physisch 12, Hoehe 16 Pixel, zentriert.
;
; URL oben:  X=34..285, Y=24..39  -> VIC-Zellen 4..35
; URL unten: X=52..267, Y=176..191 -> VIC-Zellen 6..33
; Codes 00=Schwarz, 01=Gruen (C64-Farbe 5), via Screen-RAM $50.
; Wegen des 2-Bit-Multicolor-Modus bleiben alle Bytes innerhalb
; der jeweiligen 8x8-Bitmapzellen; keine Video-RAM-Ueberlappung.
; ---------------------------------------------------------------
draw_urls:
    ; Bitmap: oben erste 8 Scanlines in Zeile 3 ($23e0),
    ; zweite 8 Scanlines in Zeile 4 ($2520): je 32 * 8 = 256 Bytes.
    ldx #$00
url_top_copy:
    lda url_top_bitmap,x
    sta $23e0,x
    lda url_top_bitmap+256,x
    sta $2520,x
    inx
    bne url_top_copy

    ; Bitmap: unten je 28 * 8 = 224 Bytes.
    ldx #$00
url_bottom_copy:
    lda url_bottom_bitmap,x
    sta $3bb0,x
    lda url_bottom_bitmap+224,x
    sta $3cf0,x
    inx
    cpx #224
    bne url_bottom_copy

    ; Beide oberen Textzeilen gruene C64-Farbe Nr. 5,
    ; nullgesetzte Pixel bleiben schwarz.
    ldx #$00
url_top_color:
    lda #$50
    sta $047c,x
    sta $04a4,x
    inx
    cpx #32
    bne url_top_color

    ; Beide unteren Textzeilen gruene C64-Farbe Nr. 5.
    ldx #$00
url_bottom_color:
    lda #$50
    sta $0776,x
    sta $079e,x
    inx
    cpx #28
    bne url_bottom_color
    rts

; ---------------------------------------------------------------
; Statische weisse Titelzeile oberhalb des Sinus-Effekts:
; 17 Zeichen * 2 Bildschirmzellen = 34 Zellen = 272 phys. Pixel.
; Zentriert: X=24..295, Y=56..71 (16 phys. Pixel hoch).
; Die 2-Bit-Codes "01" (Weiss) und "00" (Schwarz) werden in der
; Bitmap gesetzt. Gilt nur fuer Textzellen mit Screen-RAM $10.
; ---------------------------------------------------------------
draw_upper_title:
    lda #$d8                  ; $28d8 = Y 56, Spalte 3
    sta top_ptr
    lda #$28
    sta top_ptr+1
    lda #$18                  ; $2a18 = Y 64, Spalte 3
    sta bottom_ptr
    lda #$2a
    sta bottom_ptr+1
    lda #<title_font_data
    sta font_ptr
    lda #>title_font_data
    sta font_ptr+1
    lda #3
    sta text_col

upper_char:
    ; Beide 8-Pixel-hohen Screen-Zeilen mit Weiss ($1) auf Schwarz ($0).
    ldx text_col
    lda #$10
    sta $0518,x              ; Y=56, erste Zelle
    sta $0519,x              ; Y=56, zweite Zelle
    sta $0540,x              ; Y=64, erste Zelle
    sta $0541,x              ; Y=64, zweite Zelle

    lda top_ptr
    sta draw_ptr
    lda top_ptr+1
    sta draw_ptr+1
    ldy #0
upper_top:
    jsr draw_font_row
    iny
    cpy #4
    bne upper_top

    lda bottom_ptr
    sta draw_ptr
    lda bottom_ptr+1
    sta draw_ptr+1
upper_bottom:
    jsr draw_font_row
    iny
    cpy #8
    bne upper_bottom

    ; Naechstes der 17 Zeichen: Font +8, zwei Zellen +16.
    clc
    lda font_ptr
    adc #8
    sta font_ptr
    bcc upper_font_ptr_ok
    inc font_ptr+1
upper_font_ptr_ok:
    clc
    lda top_ptr
    adc #16
    sta top_ptr
    bcc upper_top_ptr_ok
    inc top_ptr+1
upper_top_ptr_ok:
    clc
    lda bottom_ptr
    adc #16
    sta bottom_ptr
    bcc upper_bottom_ptr_ok
    inc bottom_ptr+1
upper_bottom_ptr_ok:
    inc text_col
    inc text_col
    lda text_col
    cmp #37                  ; die Zellen 3..36 sind fertig
    bne upper_char
    rts

; ---------------------------------------------------------------
; Statische zweifarbige Schrift hoeher im Multicolor-Bitmap:
; 15 Zeichen * 2 Bildschirmzellen = 30 Zellen = 240 phys. Pixel.
; Zentriert: X=40..279, Y=152..167 (16 phys. Pixel hoch).
; Die 2-Bit-Codes "01" (Gelb) und "00" (Schwarz) werden in der
; Bitmap gesetzt. Gilt nur fuer Textzellen mit Screen-RAM $70.
; ---------------------------------------------------------------
draw_caption:
    lda #$e8                  ; $37e8 = Y 152, Spalte 5
    sta top_ptr
    lda #$37
    sta top_ptr+1
    lda #$28                  ; $3928 = Y 160, Spalte 5
    sta bottom_ptr
    lda #$39
    sta bottom_ptr+1
    lda #<font_data
    sta font_ptr
    lda #>font_data
    sta font_ptr+1
    lda #5
    sta text_col

caption_char:
    ; Beide 8-Pixel-hohen Screen-Zeilen mit Gelb ($7) auf
    ; Schwarz ($0) faerben, alle anderen Farben unveraendert.
    ldx text_col
    lda #$70
    sta $06f8,x              ; Y=152, erste Zelle
    sta $06f9,x              ; Y=152, zweite Zelle
    sta $0720,x              ; Y=160, erste Zelle
    sta $0721,x              ; Y=160, zweite Zelle

    lda top_ptr
    sta draw_ptr
    lda top_ptr+1
    sta draw_ptr+1
    ldy #0
caption_top:
    jsr draw_font_row
    iny
    cpy #4
    bne caption_top

    lda bottom_ptr
    sta draw_ptr
    lda bottom_ptr+1
    sta draw_ptr+1
caption_bottom:
    jsr draw_font_row
    iny
    cpy #8
    bne caption_bottom

    ; Naechstes der 15 Zeichen: Font +8, zwei Zellen +16.
    clc
    lda font_ptr
    adc #8
    sta font_ptr
    bcc font_ptr_ok
    inc font_ptr+1
font_ptr_ok:
    clc
    lda top_ptr
    adc #16
    sta top_ptr
    bcc top_ptr_ok
    inc top_ptr+1
top_ptr_ok:
    clc
    lda bottom_ptr
    adc #16
    sta bottom_ptr
    bcc bottom_ptr_ok
    inc bottom_ptr+1
bottom_ptr_ok:
    inc text_col
    inc text_col
    lda text_col
    cmp #35                  ; die Zellen 5..34 sind fertig
    bne caption_char
    rts

; Achte darauf: Das C64-Multicolor-Bitmap kodiert Farben pro
; Doppelpixel: 00=Schwarz, 01=gelb (aus High Nibble von $70).
; Fontdaten sind 8x8 monochrom, auf 2 Zellen (16 px) verteilt.
; Jede Glyphenzeile wird zweimal ausgegeben, so 16 Pixel hoch.
; Aufruf: Y=0..7; bleibt als Fontzeilenindex erhalten.
draw_font_row:
    lda (font_ptr),y
    sta font_byte
    tya
    pha                     ; Original-Y sichern
    and #3
    asl                     ; Zielzeile = (Y modulo 4)*2
    sta row_offset
    tay

    ; linke Glyphen-Haelfte (4 Doppel-Pixel)
    lda font_byte
    lsr
    lsr
    lsr
    lsr
    tax
    lda bits_to_yellow,x
    sta (draw_ptr),y
    iny
    sta (draw_ptr),y

    ; rechte Glyphen-Haelfte in naechster 8-Byte-Zelle
    lda row_offset
    clc
    adc #8
    tay
    lda font_byte
    and #$0f
    tax
    lda bits_to_yellow,x
    sta (draw_ptr),y
    iny
    sta (draw_ptr),y

    pla
    tay
    rts

; Abbildung 4 Monochrom-Bits -> vier 2-Bit-Multicolor-Pixel.
; 0 -> 00 (Hintergrund), 1 -> 01 (Gelb), keine Farbe 10/11.
bits_to_yellow:
    .byte $00,$01,$04,$05,$10,$11,$14,$15
    .byte $40,$41,$44,$45,$50,$51,$54,$55

; Zeichensatz fuer die 17 Zeichen "gh0st  &  paule32".
; 17 * 8 = 136 Byte. Kleine Schrift fuer den weissen Titel.
title_font_data:
    .byte $00,$00,$38,$44,$44,$3c,$04,$38     ; 'g'
    .byte $40,$40,$58,$64,$44,$44,$44,$00     ; 'h'
    .byte $38,$44,$4c,$54,$64,$44,$38,$00     ; '0'
    .byte $00,$00,$38,$40,$38,$04,$78,$00     ; 's'
    .byte $20,$20,$78,$20,$20,$24,$18,$00     ; 't'
    .byte $00,$00,$00,$00,$00,$00,$00,$00     ; ' '
    .byte $00,$00,$00,$00,$00,$00,$00,$00     ; ' '
    .byte $30,$48,$30,$4a,$44,$46,$3a,$00     ; '&'
    .byte $00,$00,$00,$00,$00,$00,$00,$00     ; ' '
    .byte $00,$00,$00,$00,$00,$00,$00,$00     ; ' '
    .byte $00,$00,$58,$64,$44,$78,$40,$40     ; 'p'
    .byte $00,$00,$38,$04,$3c,$44,$3c,$00     ; 'a'
    .byte $00,$00,$44,$44,$44,$4c,$34,$00     ; 'u'
    .byte $30,$10,$10,$10,$10,$10,$38,$00     ; 'l'
    .byte $00,$00,$38,$44,$7c,$40,$38,$00     ; 'e'
    .byte $38,$44,$08,$18,$08,$44,$38,$00     ; '3'
    .byte $38,$44,$04,$18,$20,$40,$7c,$00     ; '2'

; Zeichensatz fuer die 15 Zeichen "Commodore C= 64".
; 15 * 8 = 120 Byte. Normale Groess-/Kleinschreibung.
font_data:
    .byte $38,$44,$40,$40,$40,$44,$38,$00     ; 'C'
    .byte $00,$00,$38,$44,$44,$44,$38,$00     ; 'o'
    .byte $00,$00,$68,$54,$54,$54,$54,$00     ; 'm'
    .byte $00,$00,$68,$54,$54,$54,$54,$00     ; 'm'
    .byte $00,$00,$38,$44,$44,$44,$38,$00     ; 'o'
    .byte $04,$04,$34,$4c,$44,$4c,$34,$00     ; 'd'
    .byte $00,$00,$38,$44,$44,$44,$38,$00     ; 'o'
    .byte $00,$00,$58,$64,$40,$40,$40,$00     ; 'r'
    .byte $00,$00,$38,$44,$7c,$40,$38,$00     ; 'e'
    .byte $00,$00,$00,$00,$00,$00,$00,$00     ; ' '
    .byte $38,$44,$40,$40,$40,$44,$38,$00     ; 'C'
    .byte $00,$00,$7c,$00,$7c,$00,$00,$00     ; '='
    .byte $00,$00,$00,$00,$00,$00,$00,$00     ; ' '
    .byte $18,$20,$40,$78,$44,$44,$38,$00     ; '6'
    .byte $08,$18,$28,$48,$7c,$08,$08,$00     ; '4'

; 16-Sample-Sinustabelle, 2 kleine Wellen pro 16 Zellen.
; Werte 0..4 -> Verschiebung -4,-2,0,+2,+4 Pixel.
; 40 Zellen = 5 kleine Wellen ueber die ganze Balkenbreite.
sine_offsets:
    .byte 2,3,4,3,2,1,0,1
    .byte 2,3,4,3,2,1,0,1

; Acht BLAUE Abstufungen 1..8, dazu 0 = Schwarz.
; Multicolor-Codes 00 Schwarz, 01 Blau, 10 Hellblau.
; Pro Bitmap-Byte 4 Doppelbreit-Farbpixel, jeweils zwei Zeilen.
level_even:
    .byte $00,$40,$44,$44,$44,$99,$99,$aa,$aa
level_odd:
    .byte $00,$00,$00,$40,$44,$44,$99,$99,$aa

; 16 Werte fuer 16 Doppelzeilen, zu Beginn alle Schwarz.
levels:
    .byte 0,0,0,0,0,0,0,0
    .byte 0,0,0,0,0,0,0,0

; Bitmap-Startadressen fuer Y=84,86,...114.
line_addr_lo:
    .byte $84,$86,$c0,$c2,$c4,$c6,$00,$02
    .byte $04,$06,$40,$42,$44,$46,$80,$82
line_addr_hi:
    .byte $2c,$2c,$2d,$2d,$2d,$2d,$2f,$2f
    .byte $2f,$2f,$30,$30,$30,$30,$31,$31

; ---------------------------------------------------------------
; Statische Bitmapdaten fuer gruenen Text (00 schwarz, 01 gruen).
; Um den Text zu aendern, build.py aus dem ZIP verwenden.
url_top_bitmap:
    .byte $10,$10,$10,$10,$11,$11,$14,$14,$00,$00,$00,$00,$41,$41,$10,$10
    .byte $40,$40,$40,$40,$50,$50,$40,$40,$04,$04,$04,$04,$15,$15,$04,$04
    .byte $00,$00,$00,$00,$01,$01,$01,$01,$00,$00,$00,$00,$54,$54,$01,$01
    .byte $00,$00,$00,$00,$05,$05,$10,$10,$00,$00,$00,$00,$50,$50,$00,$00
    .byte $00,$00,$10,$10,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$01,$01
    .byte $10,$10,$10,$10,$40,$40,$00,$00,$01,$01,$01,$01,$04,$04,$10,$10
    .byte $00,$00,$00,$00,$05,$05,$10,$10,$00,$00,$00,$00,$51,$51,$01,$01
    .byte $00,$00,$00,$00,$14,$14,$41,$41,$00,$00,$00,$00,$05,$05,$00,$00
    .byte $00,$00,$00,$00,$41,$41,$10,$10,$00,$00,$00,$00,$55,$55,$04,$04
    .byte $00,$00,$00,$00,$10,$10,$10,$10,$00,$00,$00,$00,$10,$10,$11,$11
    .byte $00,$00,$00,$00,$00,$00,$55,$55,$00,$00,$00,$00,$14,$14,$11,$11
    .byte $00,$00,$00,$00,$40,$40,$10,$10,$10,$10,$00,$00,$50,$50,$10,$10
    .byte $00,$00,$00,$00,$05,$05,$10,$10,$10,$10,$10,$10,$10,$10,$50,$50
    .byte $10,$10,$00,$00,$50,$50,$10,$10,$00,$00,$00,$00,$00,$00,$00,$00
    .byte $00,$00,$00,$00,$00,$00,$01,$01,$01,$01,$01,$01,$51,$51,$05,$05
    .byte $00,$00,$00,$00,$05,$05,$10,$10,$00,$00,$00,$00,$40,$40,$10,$10
    .byte $10,$10,$10,$10,$10,$10,$00,$00,$10,$10,$10,$10,$10,$10,$00,$00
    .byte $40,$40,$41,$41,$14,$14,$00,$00,$04,$04,$04,$04,$01,$01,$00,$00
    .byte $01,$01,$11,$11,$41,$41,$00,$00,$54,$54,$00,$00,$00,$00,$00,$00
    .byte $05,$05,$00,$00,$15,$15,$00,$00,$40,$40,$10,$10,$40,$40,$00,$00
    .byte $10,$10,$00,$00,$00,$00,$00,$00,$04,$04,$10,$10,$10,$10,$00,$00
    .byte $00,$00,$01,$01,$01,$01,$00,$00,$40,$40,$00,$00,$00,$00,$00,$00
    .byte $10,$10,$10,$10,$05,$05,$00,$00,$01,$01,$01,$01,$51,$51,$00,$00
    .byte $00,$00,$00,$00,$00,$00,$00,$00,$05,$05,$10,$10,$05,$05,$00,$00
    .byte $50,$50,$10,$10,$51,$51,$00,$00,$10,$10,$40,$40,$55,$55,$00,$00
    .byte $05,$05,$00,$00,$15,$15,$00,$00,$50,$50,$10,$10,$40,$40,$00,$00
    .byte $00,$00,$00,$00,$00,$00,$00,$00,$11,$11,$11,$11,$11,$11,$00,$00
    .byte $10,$10,$10,$10,$10,$10,$00,$00,$10,$10,$10,$10,$54,$54,$00,$00
    .byte $10,$10,$10,$10,$05,$05,$00,$00,$10,$10,$50,$50,$10,$10,$00,$00
    .byte $10,$10,$10,$10,$54,$54,$00,$00,$00,$00,$05,$05,$05,$05,$00,$00
    .byte $01,$01,$01,$01,$00,$00,$00,$00,$01,$01,$05,$05,$51,$51,$00,$00
    .byte $15,$15,$10,$10,$05,$05,$00,$00,$50,$50,$00,$00,$50,$50,$00,$00

url_bottom_bitmap:
    .byte $04,$04,$04,$04,$04,$04,$05,$05,$00,$00,$00,$00,$50,$50,$04,$04
    .byte $10,$10,$10,$10,$54,$54,$10,$10,$01,$01,$01,$01,$05,$05,$01,$01
    .byte $00,$00,$00,$00,$40,$40,$00,$00,$00,$00,$00,$00,$55,$55,$40,$40
    .byte $00,$00,$00,$00,$01,$01,$44,$44,$00,$00,$00,$00,$54,$54,$00,$00
    .byte $00,$00,$04,$04,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .byte $04,$04,$04,$04,$10,$10,$40,$40,$00,$00,$00,$00,$01,$01,$04,$04
    .byte $44,$44,$44,$44,$04,$04,$04,$04,$00,$00,$00,$00,$10,$10,$40,$40
    .byte $00,$00,$00,$00,$15,$15,$00,$00,$01,$01,$00,$00,$00,$00,$40,$40
    .byte $40,$40,$40,$40,$40,$40,$40,$40,$14,$14,$04,$04,$04,$04,$04,$04
    .byte $00,$00,$00,$00,$04,$04,$04,$04,$00,$00,$00,$00,$04,$04,$04,$04
    .byte $00,$00,$00,$00,$55,$55,$40,$40,$00,$00,$00,$00,$00,$00,$40,$40
    .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$45,$45,$50,$50
    .byte $00,$00,$00,$00,$01,$01,$44,$44,$00,$00,$00,$00,$50,$50,$04,$04
    .byte $10,$10,$10,$10,$54,$54,$10,$10,$00,$00,$00,$00,$00,$00,$00,$00
    .byte $04,$04,$04,$04,$04,$04,$00,$00,$04,$04,$04,$04,$04,$04,$00,$00
    .byte $10,$10,$10,$10,$05,$05,$00,$00,$01,$01,$41,$41,$00,$00,$00,$00
    .byte $00,$00,$04,$04,$50,$50,$00,$00,$55,$55,$40,$40,$40,$40,$00,$00
    .byte $01,$01,$00,$00,$05,$05,$00,$00,$50,$50,$04,$04,$50,$50,$00,$00
    .byte $04,$04,$00,$00,$00,$00,$00,$00,$01,$01,$04,$04,$04,$04,$00,$00
    .byte $00,$00,$00,$00,$00,$00,$00,$00,$10,$10,$40,$40,$40,$40,$00,$00
    .byte $05,$05,$04,$04,$04,$04,$00,$00,$00,$00,$40,$40,$10,$10,$00,$00
    .byte $15,$15,$40,$40,$15,$15,$00,$00,$40,$40,$40,$40,$41,$41,$00,$00
    .byte $40,$40,$40,$40,$50,$50,$00,$00,$04,$04,$04,$04,$15,$15,$00,$00
    .byte $04,$04,$04,$04,$01,$01,$00,$00,$04,$04,$14,$14,$44,$44,$00,$00
    .byte $55,$55,$40,$40,$40,$40,$00,$00,$00,$00,$01,$01,$01,$01,$00,$00
    .byte $00,$00,$40,$40,$40,$40,$00,$00,$40,$40,$40,$40,$40,$40,$00,$00
    .byte $45,$45,$44,$44,$41,$41,$00,$00,$54,$54,$00,$00,$54,$54,$00,$00
    .byte $10,$10,$10,$10,$05,$05,$00,$00,$00,$00,$40,$40,$00,$00,$00,$00
