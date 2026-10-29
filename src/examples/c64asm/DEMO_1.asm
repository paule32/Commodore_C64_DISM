; -------------------------------------------------------------------
; File  : Demo1.asm
; Author: (c) 2026 by Blacky Cat - paule32
;
; Commodore 64: WEISSE ZICKZACK-SCHWEISSNAHT + FALL + DEMO
; MOS 6510, HiRes 320x200, schwarz / weiss.
; Speichern als c64_schweissnaht_demo.asm; in d64_dism nach VICE
; senden.
; Quellcode und Daten liegen unter $2000, Bitmap $2000-$3fff.
;
; Ablauf:
;   1. Weiss gezackten Umriss von der Mitte nach aussen zeichnen.
;   2. Umriss um 42 Pixel nach unten bewegen.
;   3. Innenflaeche zeilenweise weiss fuellen.
;   4. DEMO schwarz in die weisse Flaeche zeichnen.
; -------------------------------------------------------------------
.org $1000
.nostub
.entry start

; Zeiger auf eine Bitmap-Spalte; $fd-$ff: Plot-Parameter
ptr       = $fb               ; $fb/$fc 16-Bit Bitmap-Zeiger
px        = $fd               ; Pixel-X (0..255)
py        = $fe               ; Pixel-Y (0..199)
pen       = $ff               ; 0=weiss setzen, 1=schwarz loeschen

start:
    sei                   ; Keine KERNAL-IRQ-Eingriffe in den Grafikscreen
    ; VIC-Bank 0, Screen $0400, Bitmap $2000
    lda $dd00
    ora #$03
    sta $dd00
    lda #$18
    sta $d018

    ; Screen-Farbattribute: $10 = Weiss auf Schwarz
    lda #$10
    ldx #$00
color_loop:
    sta $0400,x
    sta $0500,x
    sta $0600,x
    sta $0700,x
    inx
    bne color_loop

    ; 8000 Bitmap-Bytes auf Null setzen (kein Streifenmuster)
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

    ; Schwarzer Rahmen / Hintergrund, HiRes aktivieren
    lda #$00
    sta $d020
    sta $d021
    lda $d016
    and #$ef
    sta $d016
    lda $d011
    ora #$20
    sta $d011

    ; Umriss Mittelpunkt (160,100), Breite 84, Hoehe 42
    lda #79
    sta top_y
    lda #$00
    sta pen              ; weisse Pixel
    lda #$01
    sta animate          ; mit Einzelpixel-Animation
    jsr draw_outline

    ; Ganzen Umriss langsam nach unten bewegen
    lda #$00
    sta animate
    lda #42
    sta fall_count
fall_loop:
    lda #$01
    sta pen              ; alte Pixel loeschen
    jsr draw_outline
    inc top_y
    lda #$00
    sta pen              ; neuen Umriss zeichnen
    jsr draw_outline
    jsr wait_frame
    dec fall_count
    bne fall_loop

    ; Endposition: Umriss ungefaehr X=118..202, Y=121..165
    ; Innenbereich X=119..201, Y=123..162 weiss ausfuellen
    lda #123
    sta fill_y
    lda #$00
    sta pen
fill_line:
    lda #119
    sta fill_x
fill_pixel:
    lda fill_x
    sta px
    lda fill_y
    sta py
    jsr plot_pixel
    inc fill_x
    lda fill_x
    cmp #202
    bne fill_pixel
    jsr wait_frame
    inc fill_y
    lda fill_y
    cmp #163
    bne fill_line

    ; Schwarzer 2x2-Font in weisser Flaeche
    lda #$01
    sta pen
    lda #137
    sta char_x
    lda #0
    sta char_no
    jsr draw_demo

finished:
    jmp finished

; -------------------------------------------------------------
; Gezackter Umriss, 3 Phasen: oben, Seiten, unten
; Alle vier Koordinaten werden in 8-Bit-Variablen gehalten.
; -------------------------------------------------------------
draw_outline:
    lda #0
    sta step_no

top_loop:
    lda step_no
    and #$03
    tax
    lda zigzag,x
    clc
    adc top_y
    sta py

    lda #160
    sec
    sbc step_no
    sta px
    jsr plot_pixel
    lda #160
    clc
    adc step_no
    sta px
    jsr plot_pixel
    jsr maybe_frame
    inc step_no
    lda step_no
    cmp #43
    bne top_loop

    lda #0
    sta step_no
sides_loop:
    lda top_y
    clc
    adc step_no
    sta py

    lda step_no
    and #$03
    tax
    lda zigzag,x
    clc
    adc #118
    sta px
    jsr plot_pixel

    lda step_no
    and #$03
    tax
    lda #202
    sec
    sbc zigzag,x
    sta px
    jsr plot_pixel
    jsr maybe_frame
    inc step_no
    lda step_no
    cmp #43
    bne sides_loop

    lda #0
    sta step_no
bottom_loop:
    lda step_no
    and #$03
    tax
    lda zigzag,x
    clc
    adc top_y
    adc #42              ; top_y + 42 + zigzag
    sta py

    lda #118
    clc
    adc step_no
    sta px
    jsr plot_pixel
    lda #202
    sec
    sbc step_no
    sta px
    jsr plot_pixel
    jsr maybe_frame
    inc step_no
    lda step_no
    cmp #43
    bne bottom_loop
    rts

maybe_frame:
    lda animate
    beq no_frame
    jsr wait_frame
no_frame:
    rts

; Der VICE/C64-Raster erreicht 250 einmal pro Bild (PAL/NTSC).
wait_frame:
wait_not_250:
    lda $d012
    cmp #250
    beq wait_not_250
wait_for_250:
    lda $d012
    cmp #250
    bne wait_for_250
    rts

; -------------------------------------------------------------
; HiRes Pixel: $2000 + 320*(Y/8) + 8*(X/8) + (Y & 7)
; (ptr),Y greift auf die 8 aufeinanderfolgenden Bitmapzeilen
; innerhalb der 8x8-Zelle zu.
; -------------------------------------------------------------
plot_pixel:
    lda py
    lsr a
    lsr a
    lsr a                 ; tile = py / 8
    sta tile
    and #$03
    tax
    lda row_low,x         ; (tile * 64) & 255
    sta ptr

    lda tile
    lsr a
    lsr a                 ; tile / 4
    clc
    adc tile              ; tile + tile/4
    adc #$20              ; $2000 + tile*320
    sta ptr+1

    lda px
    and #$f8              ; 8*(px / 8)
    clc
    adc ptr
    sta ptr
    bcc pixel_no_carry
    inc ptr+1
pixel_no_carry:
    lda py
    and #$07
    tay
    lda px
    and #$07
    tax
    lda bit_mask,x
    ldx pen
    bne clear_dot
    ora (ptr),y
    sta (ptr),y
    rts
clear_dot:
    eor #$ff
    and (ptr),y
    sta (ptr),y
    rts

; -------------------------------------------------------------
; DEMO: Font mit 5x7 Pixeln, 2-fach vergroessert.
; Pixel werden gezielt SCHWARZ gesetzt, also gut sichtbar auf
; der weissen Flaeche.
; -------------------------------------------------------------
draw_demo:
    lda #0
    sta glyph_row
next_glyph_row:
    lda char_no
    asl a
    asl a
    asl a                 ; 8 Datenbytes pro Buchstabe
    clc
    adc glyph_row
    tax
    lda letters,x
    sta glyph_bits
    lda #0
    sta glyph_col
next_glyph_col:
    lda glyph_bits
    and #$10
    beq skip_black_dot

    lda glyph_col
    asl a
    clc
    adc char_x
    sta px
    lda glyph_row
    asl a
    clc
    adc #137
    sta py
    jsr plot_pixel
    inc px
    jsr plot_pixel
    inc py
    jsr plot_pixel
    dec px
    jsr plot_pixel

skip_black_dot:
    asl glyph_bits
    inc glyph_col
    lda glyph_col
    cmp #5
    bne next_glyph_col
    inc glyph_row
    lda glyph_row
    cmp #7
    bne next_glyph_row

    lda #0
    sta glyph_row
    lda char_x
    clc
    adc #12
    sta char_x
    inc char_no
    lda char_no
    cmp #4
    bne next_glyph_row
    rts

; Wellenform fuer die Zickzack-Schweissnaht
row_low:
    .byte $00,$40,$80,$c0
bit_mask:
    .byte $80,$40,$20,$10,$08,$04,$02,$01
zigzag:
    .byte 0,1,2,1

; 5x7-Zeichensatz D E M O (jeweils auf 8 Bytes gepolstert)
letters:
    .byte 14,17,17,17,17,17,14,0     ; D
    .byte 31,16,16,30,16,16,31,0     ; E
    .byte 17,27,21,21,17,17,17,0     ; M
    .byte 14,17,17,17,17,17,14,0     ; O

; Arbeitsvariablen im Programm-RAM (ausserhalb des Bildspeichers)
top_y:       .byte 79
step_no:     .byte 0
animate:     .byte 0
fall_count:  .byte 0
fill_x:      .byte 0
fill_y:      .byte 0
tile:        .byte 0
char_x:      .byte 0
char_no:     .byte 0
glyph_row:   .byte 0
glyph_col:   .byte 0
glyph_bits:  .byte 0
