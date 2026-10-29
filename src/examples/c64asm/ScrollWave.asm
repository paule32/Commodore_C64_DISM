; ---------------------------------------------------------------
; File  : ScrollWave.asm
; Author: (c) 2026 by Blacky Cat - paule32
; ---------------------------------------------------------------
; C64 MULTICOLOR 160x200 (320 physische Bildschirm-Pixel)
; SINUS-WANDERLICHT MIT 8 OPTISCHEN BLAUSTUFEN
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
; Start: .org $1000, SYS 4096, VICE "Programm uebertragen + START"
; ---------------------------------------------------------------
.org $1000
.nostub
.entry start

ptr       = $fb             ; Zeiger auf die aktuelle Bitmapzelle
step      = $fd             ; Nummer der Doppelzeile 0..15
peak      = $fe             ; Position des weissen Streifens 0..15
direction = $ff             ; 0 = abwaerts, 1 = aufwaerts
pixel_a   = $f9             ; Dither-Maske fuer erste Pixelzeile
pixel_b   = $fa             ; Dither-Maske fuer zweite Pixelzeile
column    = $f5             ; 8-Pixel-Block X=0..39
waveval   = $f6             ; Sinusverschiebung fuer aktuellen Block
phase     = $f7             ; seitliche Wanderphase der Sinuswellen
tick      = $f8             ; bremst die seitliche Sinusphase

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
