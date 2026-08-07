; ---------------------------------------------------------------------------
; C64 multicolor bitmap target for the shared graphics.h API.
; The public routines use the dBase2Many C/Pascal 6510 stack ABI:
; every argument occupies two bytes, arguments are pushed left-to-right,
; and a function result is returned in A/X (low/high).
;
; VIC-II layout (bank 2):
;   $8800-$8BE7  palette-slot usage flags for each 4x8 multicolor cell
;   $8C00-$8FE7  multicolor screen matrix (palette slots 1 and 2)
;   $9000-$9FFF  intentionally unused by VIC-II (character-ROM shadow)
;   $A000-$BF3F  160x200 multicolor bitmap, displayed as 320x200
;
; The target code is placed at $4000.  The C64 build no longer links the large
; generated common-C primitive module, so the application remains below this
; address while the direct 6510 primitives have the complete $4000-$7FFF
; window.  VIC-II bank $8000-$BFFF remains reserved exclusively for graphics.
; ---------------------------------------------------------------------------

__d64_graphics_reserve_start = $8000
__d64_graphics_reserve_end   = $BFFF
__d64_graphics_runtime_start = $4000
__d64_graphics_runtime_limit = $8000

GFX_BITMAP_BASE = $A000
GFX_PALETTE_BASE = $8800
GFX_SCREEN_BASE = $8C00
GFX_TEXT_BASE   = $0400
GFX_COLOR_BASE   = $D800

GFX_BITMAP_LO = $F7
GFX_BITMAP_HI = $F8
GFX_SCREEN_LO = $F9
GFX_SCREEN_HI = $FA
GFX_PALETTE_LO = $FB
GFX_PALETTE_HI = $FC

.org $4000

; ---------------------------------------------------------------------------
; SetTextColor(foreground, background)
; ---------------------------------------------------------------------------
SetTextColor:
    tsx
    lda $0105,x
    and #$0F
    sta __gfx_text_color
    sta $0286
    lda $0103,x
    and #$0F
    sta __gfx_background
    sta $D020
    sta $D021
    rts

; ---------------------------------------------------------------------------
; ClearScreen()
; ---------------------------------------------------------------------------
ClearScreen:
    lda __gfx_active
    bne __gfx_clear_screen_graphics
    jmp __gfx_clear_text
__gfx_clear_screen_graphics:
    jmp __gfx_clear_graphics

; ---------------------------------------------------------------------------
; InitGraphics()
; Clear memory while display is blank, then enable a real 320x200 multicolor mode.
; ---------------------------------------------------------------------------
InitGraphics:
    php
    sei
    lda __gfx_active
    bne __gfx_init_saved
    lda $D011
    sta __gfx_saved_d011
    lda $D016
    sta __gfx_saved_d016
    lda $D018
    sta __gfx_saved_d018
    lda $DD00
    sta __gfx_saved_dd00
    lda $DD02
    sta __gfx_saved_dd02
    lda $01
    sta __gfx_saved_cpu_port
__gfx_init_saved:
    ; The bitmap occupies $A000-$BF3F.  With the normal C64 memory map the
    ; BASIC ROM is visible there for CPU reads, although writes still reach
    ; the underlying RAM.  Pixel read/modify/write operations would therefore
    ; mix BASIC-ROM bytes into the bitmap.  Keep KERNAL and I/O visible but
    ; clear LORAM for the complete graphics session.
    lda $01
    and #$FE
    sta $01

    lda $D011
    and #$EF
    sta $D011

    lda #$01
    sta __gfx_active
    jsr __gfx_clear_graphics

    lda $DD02
    ora #$03
    sta $DD02
    lda $DD00
    and #$FC
    ora #$01
    sta $DD00

    ; In VIC bank 2 the VIC-II always sees character ROM at $9000-$9FFF.
    ; Therefore the screen matrix must live outside that window.  $38 selects
    ; screen matrix $8C00 (offset $0C00) and bitmap $A000 (offset $2000).
    lda #$38
    sta $D018
    lda $D016
    and #$E7
    ora #$18
    sta $D016

    lda __gfx_background
    sta $D020
    sta $D021

    lda $D011
    and #$87
    ora #$38
    sta $D011
    plp
    rts

; ---------------------------------------------------------------------------
; DoneGraphics(mode)
; ---------------------------------------------------------------------------
DoneGraphics:
    tsx
    lda $0103,x
    sta __gfx_text_mode
    php
    sei

    lda $D011
    and #$EF
    sta $D011
    lda #$00
    sta __gfx_active

    lda $DD02
    ora #$03
    sta $DD02
    lda __gfx_saved_dd00
    and #$FC
    ora #$03
    sta $DD00

    lda __gfx_saved_d016
    and #$EF
    ora #$08
    sta $D016

    lda __gfx_text_mode
    beq __gfx_done_upper
    lda #$16
    bne __gfx_done_charset
__gfx_done_upper:
    lda #$14
__gfx_done_charset:
    sta $D018
    lda #$04
    sta $0288

    jsr __gfx_clear_text

    lda __gfx_background
    sta $D020
    sta $D021
    lda __gfx_saved_d011
    and #$DF
    ora #$18
    sta $D011

    ; Restore the CPU memory configuration that was active before graphics.
    ; In particular this maps the BASIC ROM back in when it was visible.
    lda __gfx_saved_cpu_port
    sta $01
    plp
    rts

; ---------------------------------------------------------------------------
; SetPixel(x, y, color)
; ---------------------------------------------------------------------------
SetPixel:
    tsx
    lda $0107,x
    sta __gfx_x_lo
    lda $0108,x
    sta __gfx_x_hi
    lda $0105,x
    sta __gfx_y_lo
    lda $0106,x
    sta __gfx_y_hi
    lda $0103,x
    and #$0F
    sta __gfx_color
    jmp __gfx_setpixel_core

; ---------------------------------------------------------------------------
; GetPixel(x, y) -> A/X
; ---------------------------------------------------------------------------
GetPixel:
    tsx
    lda $0105,x
    sta __gfx_x_lo
    lda $0106,x
    sta __gfx_x_hi
    lda $0103,x
    sta __gfx_y_lo
    lda $0104,x
    sta __gfx_y_hi
    jsr __gfx_getpixel_core
    ldx #$00
    rts

; ---------------------------------------------------------------------------
; __GraphicsHLine(x1, y, x2, color)
; Clipped horizontal span.  The inner pixel operation is pure assembler.
; ---------------------------------------------------------------------------
__GraphicsHLine:
    tsx
    lda $0109,x
    sta __gfx_line_x1_lo
    lda $010A,x
    sta __gfx_line_x1_hi
    lda $0107,x
    sta __gfx_y_lo
    lda $0108,x
    sta __gfx_y_hi
    lda $0105,x
    sta __gfx_line_x2_lo
    lda $0106,x
    sta __gfx_line_x2_hi
    lda $0103,x
    and #$0F
    sta __gfx_color

__gfx_hline_core:
    lda __gfx_y_hi
    beq __gfx_hline_y_high_ok
    rts
__gfx_hline_y_high_ok:
    lda __gfx_y_lo
    cmp #$C8
    bcc __gfx_hline_y_ok
    rts
__gfx_hline_y_ok:

    ; signed order: swap when x2 < x1
    lda __gfx_line_x1_hi
    eor #$80
    sta __gfx_temp
    lda __gfx_line_x2_hi
    eor #$80
    cmp __gfx_temp
    bcc __gfx_hline_swap
    bne __gfx_hline_ordered
    lda __gfx_line_x2_lo
    cmp __gfx_line_x1_lo
    bcc __gfx_hline_swap
    bcs __gfx_hline_ordered
__gfx_hline_swap:
    lda __gfx_line_x1_lo
    ldx __gfx_line_x2_lo
    stx __gfx_line_x1_lo
    sta __gfx_line_x2_lo
    lda __gfx_line_x1_hi
    ldx __gfx_line_x2_hi
    stx __gfx_line_x1_hi
    sta __gfx_line_x2_hi
__gfx_hline_ordered:
    lda __gfx_line_x2_hi
    bpl __gfx_hline_x2_nonnegative
    rts
__gfx_hline_x2_nonnegative:

    ; x1 < 0 -> 0
    lda __gfx_line_x1_hi
    bpl __gfx_hline_x1_nonnegative
    lda #$00
    sta __gfx_line_x1_lo
    sta __gfx_line_x1_hi
__gfx_hline_x1_nonnegative:
    ; x1 >= 320 -> outside
    lda __gfx_line_x1_hi
    cmp #$02
    bcc __gfx_hline_x1_hi_ok
    rts
__gfx_hline_x1_hi_ok:
    cmp #$01
    bne __gfx_hline_clip_x2
    lda __gfx_line_x1_lo
    cmp #$40
    bcc __gfx_hline_clip_x2
    rts

__gfx_hline_clip_x2:
    lda __gfx_line_x2_hi
    cmp #$02
    bcs __gfx_hline_set_319
    cmp #$01
    bne __gfx_hline_begin
    lda __gfx_line_x2_lo
    cmp #$40
    bcc __gfx_hline_begin
__gfx_hline_set_319:
    lda #$3F
    sta __gfx_line_x2_lo
    lda #$01
    sta __gfx_line_x2_hi

__gfx_hline_begin:
    lda __gfx_line_x1_lo
    sta __gfx_x_lo
    lda __gfx_line_x1_hi
    sta __gfx_x_hi
__gfx_hline_loop:
    jsr __gfx_setpixel_core
    lda __gfx_x_hi
    cmp __gfx_line_x2_hi
    bne __gfx_hline_next
    lda __gfx_x_lo
    cmp __gfx_line_x2_lo
    beq __gfx_hline_done
__gfx_hline_next:
    inc __gfx_x_lo
    bne __gfx_hline_loop
    inc __gfx_x_hi
    jmp __gfx_hline_loop
__gfx_hline_done:
    rts

; ---------------------------------------------------------------------------
; Direct C64 primitive implementations.
; These routines deliberately avoid the generated C64 C arithmetic/runtime.
; Public entries use the dBase2Many two-byte stack ABI; inner loops use the
; register/global-state pixel core above.
; ---------------------------------------------------------------------------

; ---------------------------------------------------------------------------
; DrawLine(x1, y1, x2, y2, color)
; ---------------------------------------------------------------------------
DrawLine:
    tsx
    lda $010B,x
    sta __gfx_p1_x_lo
    lda $010C,x
    sta __gfx_p1_x_hi
    lda $0109,x
    sta __gfx_p1_y_lo
    lda $010A,x
    sta __gfx_p1_y_hi
    lda $0107,x
    sta __gfx_p2_x_lo
    lda $0108,x
    sta __gfx_p2_x_hi
    lda $0105,x
    sta __gfx_p2_y_lo
    lda $0106,x
    sta __gfx_p2_y_hi
    lda $0103,x
    and #$0F
    sta __gfx_color
    jsr __gfx_drawline_core
    rts

__gfx_drawline_core:
    ; dx = abs(x2 - x1), sx = sign(x2 - x1)
    sec
    lda __gfx_p2_x_lo
    sbc __gfx_p1_x_lo
    sta __gfx_dx_lo
    lda __gfx_p2_x_hi
    sbc __gfx_p1_x_hi
    sta __gfx_dx_hi
    bpl __gfx_line_dx_positive
    lda __gfx_dx_lo
    eor #$FF
    clc
    adc #$01
    sta __gfx_dx_lo
    lda __gfx_dx_hi
    eor #$FF
    adc #$00
    sta __gfx_dx_hi
    lda #$FF
    bne __gfx_line_store_sx
__gfx_line_dx_positive:
    lda #$01
__gfx_line_store_sx:
    sta __gfx_step_x

    ; dy = abs(y2 - y1), sy = sign(y2 - y1)
    sec
    lda __gfx_p2_y_lo
    sbc __gfx_p1_y_lo
    sta __gfx_dy_lo
    lda __gfx_p2_y_hi
    sbc __gfx_p1_y_hi
    sta __gfx_dy_hi
    bpl __gfx_line_dy_positive
    lda __gfx_dy_lo
    eor #$FF
    clc
    adc #$01
    sta __gfx_dy_lo
    lda __gfx_dy_hi
    eor #$FF
    adc #$00
    sta __gfx_dy_hi
    lda #$FF
    bne __gfx_line_store_sy
__gfx_line_dy_positive:
    lda #$01
__gfx_line_store_sy:
    sta __gfx_step_y

    ; Select the major axis.
    lda __gfx_dx_hi
    cmp __gfx_dy_hi
    bcc __gfx_line_y_major
    bne __gfx_line_x_major
    lda __gfx_dx_lo
    cmp __gfx_dy_lo
    bcc __gfx_line_y_major

__gfx_line_x_major:
    lda __gfx_dx_hi
    lsr
    sta __gfx_error_hi
    lda __gfx_dx_lo
    ror
    sta __gfx_error_lo
__gfx_line_x_loop:
    jsr __gfx_plot_p1
    lda __gfx_p1_x_lo
    cmp __gfx_p2_x_lo
    bne __gfx_line_x_continue
    lda __gfx_p1_x_hi
    cmp __gfx_p2_x_hi
    bne __gfx_line_x_continue
    jmp __gfx_line_done
__gfx_line_x_continue:
    sec
    lda __gfx_error_lo
    sbc __gfx_dy_lo
    sta __gfx_error_lo
    lda __gfx_error_hi
    sbc __gfx_dy_hi
    sta __gfx_error_hi
    bcs __gfx_line_x_no_minor
    clc
    lda __gfx_error_lo
    adc __gfx_dx_lo
    sta __gfx_error_lo
    lda __gfx_error_hi
    adc __gfx_dx_hi
    sta __gfx_error_hi
    jsr __gfx_step_p1_y
__gfx_line_x_no_minor:
    jsr __gfx_step_p1_x
    jmp __gfx_line_x_loop

__gfx_line_y_major:
    lda __gfx_dy_hi
    lsr
    sta __gfx_error_hi
    lda __gfx_dy_lo
    ror
    sta __gfx_error_lo
__gfx_line_y_loop:
    jsr __gfx_plot_p1
    lda __gfx_p1_y_lo
    cmp __gfx_p2_y_lo
    bne __gfx_line_y_continue
    lda __gfx_p1_y_hi
    cmp __gfx_p2_y_hi
    bne __gfx_line_y_continue
    jmp __gfx_line_done
__gfx_line_y_continue:
    sec
    lda __gfx_error_lo
    sbc __gfx_dx_lo
    sta __gfx_error_lo
    lda __gfx_error_hi
    sbc __gfx_dx_hi
    sta __gfx_error_hi
    bcs __gfx_line_y_no_minor
    clc
    lda __gfx_error_lo
    adc __gfx_dy_lo
    sta __gfx_error_lo
    lda __gfx_error_hi
    adc __gfx_dy_hi
    sta __gfx_error_hi
    jsr __gfx_step_p1_x
__gfx_line_y_no_minor:
    jsr __gfx_step_p1_y
    jmp __gfx_line_y_loop
__gfx_line_done:
    rts

__gfx_plot_p1:
    lda __gfx_p1_x_lo
    sta __gfx_x_lo
    lda __gfx_p1_x_hi
    sta __gfx_x_hi
    lda __gfx_p1_y_lo
    sta __gfx_y_lo
    lda __gfx_p1_y_hi
    sta __gfx_y_hi
    jsr __gfx_setpixel_core
    rts

__gfx_step_p1_x:
    lda __gfx_step_x
    bmi __gfx_step_p1_x_down
    inc __gfx_p1_x_lo
    bne __gfx_step_p1_x_done
    inc __gfx_p1_x_hi
__gfx_step_p1_x_done:
    rts
__gfx_step_p1_x_down:
    lda __gfx_p1_x_lo
    bne __gfx_step_p1_x_dec_low
    dec __gfx_p1_x_hi
__gfx_step_p1_x_dec_low:
    dec __gfx_p1_x_lo
    rts

__gfx_step_p1_y:
    lda __gfx_step_y
    bmi __gfx_step_p1_y_down
    inc __gfx_p1_y_lo
    bne __gfx_step_p1_y_done
    inc __gfx_p1_y_hi
__gfx_step_p1_y_done:
    rts
__gfx_step_p1_y_down:
    lda __gfx_p1_y_lo
    bne __gfx_step_p1_y_dec_low
    dec __gfx_p1_y_hi
__gfx_step_p1_y_dec_low:
    dec __gfx_p1_y_lo
    rts

; ---------------------------------------------------------------------------
; DrawRect(x1, y1, x2, y2, color)
; ---------------------------------------------------------------------------
DrawRect:
    tsx
    lda $010B,x
    sta __gfx_rect_left_lo
    lda $010C,x
    sta __gfx_rect_left_hi
    lda $0109,x
    sta __gfx_rect_top_lo
    lda $010A,x
    sta __gfx_rect_top_hi
    lda $0107,x
    sta __gfx_rect_right_lo
    lda $0108,x
    sta __gfx_rect_right_hi
    lda $0105,x
    sta __gfx_rect_bottom_lo
    lda $0106,x
    sta __gfx_rect_bottom_hi
    lda $0103,x
    and #$0F
    sta __gfx_color
    jsr __gfx_normalize_rect
    jsr __gfx_drawrect_core
    rts

__gfx_normalize_rect:
    ; Swap left/right when right-left is negative.
    sec
    lda __gfx_rect_right_lo
    sbc __gfx_rect_left_lo
    lda __gfx_rect_right_hi
    sbc __gfx_rect_left_hi
    bpl __gfx_rect_x_ordered
    lda __gfx_rect_left_lo
    ldx __gfx_rect_right_lo
    stx __gfx_rect_left_lo
    sta __gfx_rect_right_lo
    lda __gfx_rect_left_hi
    ldx __gfx_rect_right_hi
    stx __gfx_rect_left_hi
    sta __gfx_rect_right_hi
__gfx_rect_x_ordered:
    sec
    lda __gfx_rect_bottom_lo
    sbc __gfx_rect_top_lo
    lda __gfx_rect_bottom_hi
    sbc __gfx_rect_top_hi
    bpl __gfx_rect_y_ordered
    lda __gfx_rect_top_lo
    ldx __gfx_rect_bottom_lo
    stx __gfx_rect_top_lo
    sta __gfx_rect_bottom_lo
    lda __gfx_rect_top_hi
    ldx __gfx_rect_bottom_hi
    stx __gfx_rect_top_hi
    sta __gfx_rect_bottom_hi
__gfx_rect_y_ordered:
    rts

__gfx_drawrect_core:
    ; top horizontal
    lda __gfx_rect_left_lo
    sta __gfx_line_x1_lo
    lda __gfx_rect_left_hi
    sta __gfx_line_x1_hi
    lda __gfx_rect_right_lo
    sta __gfx_line_x2_lo
    lda __gfx_rect_right_hi
    sta __gfx_line_x2_hi
    lda __gfx_rect_top_lo
    sta __gfx_y_lo
    lda __gfx_rect_top_hi
    sta __gfx_y_hi
    jsr __gfx_hline_core

    ; bottom horizontal
    lda __gfx_rect_bottom_lo
    sta __gfx_y_lo
    lda __gfx_rect_bottom_hi
    sta __gfx_y_hi
    jsr __gfx_hline_core

    ; left vertical
    lda __gfx_rect_left_lo
    sta __gfx_p1_x_lo
    sta __gfx_p2_x_lo
    lda __gfx_rect_left_hi
    sta __gfx_p1_x_hi
    sta __gfx_p2_x_hi
    lda __gfx_rect_top_lo
    sta __gfx_p1_y_lo
    lda __gfx_rect_top_hi
    sta __gfx_p1_y_hi
    lda __gfx_rect_bottom_lo
    sta __gfx_p2_y_lo
    lda __gfx_rect_bottom_hi
    sta __gfx_p2_y_hi
    jsr __gfx_drawline_core

    ; right vertical
    lda __gfx_rect_right_lo
    sta __gfx_p1_x_lo
    sta __gfx_p2_x_lo
    lda __gfx_rect_right_hi
    sta __gfx_p1_x_hi
    sta __gfx_p2_x_hi
    lda __gfx_rect_top_lo
    sta __gfx_p1_y_lo
    lda __gfx_rect_top_hi
    sta __gfx_p1_y_hi
    lda __gfx_rect_bottom_lo
    sta __gfx_p2_y_lo
    lda __gfx_rect_bottom_hi
    sta __gfx_p2_y_hi
    jsr __gfx_drawline_core
    rts

; ---------------------------------------------------------------------------
; FillRect(x1,y1,x2,y2,fill,border,width)
; The border is assigned first, then the fill receives another local palette slot.
; ---------------------------------------------------------------------------
FillRect:
    tsx
    lda $010F,x
    sta __gfx_rect_left_lo
    lda $0110,x
    sta __gfx_rect_left_hi
    lda $010D,x
    sta __gfx_rect_top_lo
    lda $010E,x
    sta __gfx_rect_top_hi
    lda $010B,x
    sta __gfx_rect_right_lo
    lda $010C,x
    sta __gfx_rect_right_hi
    lda $0109,x
    sta __gfx_rect_bottom_lo
    lda $010A,x
    sta __gfx_rect_bottom_hi
    lda $0107,x
    and #$0F
    sta __gfx_fill_color
    lda $0105,x
    and #$0F
    sta __gfx_border_color
    lda $0103,x
    sta __gfx_border_count
    jsr __gfx_normalize_rect
    jsr __gfx_clip_rect
    bcs __gfx_fillrect_done

__gfx_fillrect_border_loop:
    lda __gfx_border_count
    beq __gfx_fillrect_fill
    lda __gfx_border_color
    sta __gfx_color
    jsr __gfx_drawrect_core
    jsr __gfx_inset_rect
    bcs __gfx_fillrect_done
    dec __gfx_border_count
    jmp __gfx_fillrect_border_loop

__gfx_fillrect_fill:
    lda __gfx_fill_color
    sta __gfx_color
    lda __gfx_rect_top_lo
    sta __gfx_fill_y_lo
    lda __gfx_rect_top_hi
    sta __gfx_fill_y_hi
__gfx_fillrect_row:
    lda __gfx_rect_left_lo
    sta __gfx_line_x1_lo
    lda __gfx_rect_left_hi
    sta __gfx_line_x1_hi
    lda __gfx_rect_right_lo
    sta __gfx_line_x2_lo
    lda __gfx_rect_right_hi
    sta __gfx_line_x2_hi
    lda __gfx_fill_y_lo
    sta __gfx_y_lo
    lda __gfx_fill_y_hi
    sta __gfx_y_hi
    jsr __gfx_hline_core
    lda __gfx_fill_y_lo
    cmp __gfx_rect_bottom_lo
    bne __gfx_fillrect_next_row
    lda __gfx_fill_y_hi
    cmp __gfx_rect_bottom_hi
    beq __gfx_fillrect_done
__gfx_fillrect_next_row:
    inc __gfx_fill_y_lo
    bne __gfx_fillrect_row
    inc __gfx_fill_y_hi
    jmp __gfx_fillrect_row
__gfx_fillrect_done:
    rts

__gfx_clip_rect:
    ; Entirely left or above?
    lda __gfx_rect_right_hi
    bmi __gfx_clip_rect_invalid
    lda __gfx_rect_bottom_hi
    bmi __gfx_clip_rect_invalid

    ; left < 0 -> 0
    lda __gfx_rect_left_hi
    bpl __gfx_clip_rect_left_ok
    lda #$00
    sta __gfx_rect_left_lo
    sta __gfx_rect_left_hi
__gfx_clip_rect_left_ok:
    ; top < 0 -> 0
    lda __gfx_rect_top_hi
    bpl __gfx_clip_rect_top_ok
    lda #$00
    sta __gfx_rect_top_lo
    sta __gfx_rect_top_hi
__gfx_clip_rect_top_ok:
    ; left >= 320 -> invalid
    lda __gfx_rect_left_hi
    cmp #$02
    bcs __gfx_clip_rect_invalid
    cmp #$01
    bne __gfx_clip_rect_right
    lda __gfx_rect_left_lo
    cmp #$40
    bcs __gfx_clip_rect_invalid

__gfx_clip_rect_right:
    lda __gfx_rect_right_hi
    cmp #$02
    bcs __gfx_clip_rect_set_right
    cmp #$01
    bne __gfx_clip_rect_top_bound
    lda __gfx_rect_right_lo
    cmp #$40
    bcc __gfx_clip_rect_top_bound
__gfx_clip_rect_set_right:
    lda #$3F
    sta __gfx_rect_right_lo
    lda #$01
    sta __gfx_rect_right_hi

__gfx_clip_rect_top_bound:
    lda __gfx_rect_top_hi
    bne __gfx_clip_rect_invalid
    lda __gfx_rect_top_lo
    cmp #$C8
    bcs __gfx_clip_rect_invalid
    lda __gfx_rect_bottom_hi
    bne __gfx_clip_rect_set_bottom
    lda __gfx_rect_bottom_lo
    cmp #$C8
    bcc __gfx_clip_rect_valid
__gfx_clip_rect_set_bottom:
    lda #$C7
    sta __gfx_rect_bottom_lo
    lda #$00
    sta __gfx_rect_bottom_hi
__gfx_clip_rect_valid:
    clc
    rts
__gfx_clip_rect_invalid:
    sec
    rts

__gfx_inset_rect:
    inc __gfx_rect_left_lo
    bne __gfx_inset_left_done
    inc __gfx_rect_left_hi
__gfx_inset_left_done:
    inc __gfx_rect_top_lo
    bne __gfx_inset_top_done
    inc __gfx_rect_top_hi
__gfx_inset_top_done:
    lda __gfx_rect_right_lo
    bne __gfx_inset_right_low
    dec __gfx_rect_right_hi
__gfx_inset_right_low:
    dec __gfx_rect_right_lo
    lda __gfx_rect_bottom_lo
    bne __gfx_inset_bottom_low
    dec __gfx_rect_bottom_hi
__gfx_inset_bottom_low:
    dec __gfx_rect_bottom_lo
    ; invalid when left > right or top > bottom
    lda __gfx_rect_left_hi
    cmp __gfx_rect_right_hi
    bcc __gfx_inset_check_y
    bne __gfx_inset_invalid
    lda __gfx_rect_left_lo
    cmp __gfx_rect_right_lo
    bcc __gfx_inset_check_y
    beq __gfx_inset_check_y
    bcs __gfx_inset_invalid
__gfx_inset_check_y:
    lda __gfx_rect_top_hi
    cmp __gfx_rect_bottom_hi
    bcc __gfx_inset_valid
    bne __gfx_inset_invalid
    lda __gfx_rect_top_lo
    cmp __gfx_rect_bottom_lo
    bcc __gfx_inset_valid
    beq __gfx_inset_valid
__gfx_inset_invalid:
    sec
    rts
__gfx_inset_valid:
    clc
    rts

; ---------------------------------------------------------------------------
; DrawCircle / FillCircle
; ---------------------------------------------------------------------------
DrawCircle:
    tsx
    lda $0109,x
    sta __gfx_circle_cx_lo
    lda $010A,x
    sta __gfx_circle_cx_hi
    lda $0107,x
    sta __gfx_circle_cy_lo
    lda $0108,x
    sta __gfx_circle_cy_hi
    lda $0105,x
    sta __gfx_circle_radius_lo
    lda $0106,x
    sta __gfx_circle_radius_hi
    lda $0103,x
    and #$0F
    sta __gfx_color
    jsr __gfx_drawcircle_core
    rts

__gfx_drawcircle_core:
    lda __gfx_circle_radius_hi
    bmi __gfx_circle_done
    jsr __gfx_circle_init
__gfx_drawcircle_loop:
    jsr __gfx_circle_plot8
    jsr __gfx_circle_advance
    lda __gfx_circle_x_hi
    cmp __gfx_circle_y_hi
    bcc __gfx_circle_done
    bne __gfx_drawcircle_loop
    lda __gfx_circle_x_lo
    cmp __gfx_circle_y_lo
    bcs __gfx_drawcircle_loop
__gfx_circle_done:
    rts

FillCircle:
    tsx
    lda $010D,x
    sta __gfx_circle_cx_lo
    lda $010E,x
    sta __gfx_circle_cx_hi
    lda $010B,x
    sta __gfx_circle_cy_lo
    lda $010C,x
    sta __gfx_circle_cy_hi
    lda $0109,x
    sta __gfx_circle_radius_lo
    lda $010A,x
    sta __gfx_circle_radius_hi
    lda $0107,x
    and #$0F
    sta __gfx_fill_color
    lda $0105,x
    and #$0F
    sta __gfx_border_color
    lda $0103,x
    sta __gfx_border_count
    lda __gfx_circle_radius_lo
    sta __gfx_saved_radius_lo
    lda __gfx_circle_radius_hi
    sta __gfx_saved_radius_hi
    lda __gfx_border_count
    beq __gfx_fillcircle_after_border
__gfx_fillcircle_border_loop:
    lda __gfx_border_color
    sta __gfx_color
    jsr __gfx_drawcircle_core
    lda __gfx_circle_radius_lo
    bne __gfx_fillcircle_dec_radius
    lda __gfx_circle_radius_hi
    beq __gfx_fillcircle_no_interior
    dec __gfx_circle_radius_hi
__gfx_fillcircle_dec_radius:
    dec __gfx_circle_radius_lo
    dec __gfx_border_count
    bne __gfx_fillcircle_border_loop
    jmp __gfx_fillcircle_after_border
__gfx_fillcircle_no_interior:
    rts
__gfx_fillcircle_after_border:
    lda __gfx_fill_color
    sta __gfx_color
    lda __gfx_circle_radius_hi
    bmi __gfx_fillcircle_done
    jsr __gfx_circle_init
__gfx_fillcircle_loop:
    jsr __gfx_circle_fill4
    jsr __gfx_circle_advance
    lda __gfx_circle_x_hi
    cmp __gfx_circle_y_hi
    bcc __gfx_fillcircle_done
    bne __gfx_fillcircle_loop
    lda __gfx_circle_x_lo
    cmp __gfx_circle_y_lo
    bcs __gfx_fillcircle_loop
__gfx_fillcircle_done:
    rts

__gfx_circle_init:
    lda __gfx_circle_radius_lo
    sta __gfx_circle_x_lo
    lda __gfx_circle_radius_hi
    sta __gfx_circle_x_hi
    lda #$00
    sta __gfx_circle_y_lo
    sta __gfx_circle_y_hi
    sec
    lda #$01
    sbc __gfx_circle_radius_lo
    sta __gfx_circle_dec_lo
    lda #$00
    sbc __gfx_circle_radius_hi
    sta __gfx_circle_dec_hi
    rts

__gfx_circle_advance:
    inc __gfx_circle_y_lo
    bne __gfx_circle_y_inc_done
    inc __gfx_circle_y_hi
__gfx_circle_y_inc_done:
    lda __gfx_circle_dec_hi
    bmi __gfx_circle_dec_negative
    ; x--
    lda __gfx_circle_x_lo
    bne __gfx_circle_x_dec_low
    dec __gfx_circle_x_hi
__gfx_circle_x_dec_low:
    dec __gfx_circle_x_lo
    ; temp = 2*(y-x)+1
    sec
    lda __gfx_circle_y_lo
    sbc __gfx_circle_x_lo
    sta __gfx_temp16_lo
    lda __gfx_circle_y_hi
    sbc __gfx_circle_x_hi
    sta __gfx_temp16_hi
    asl __gfx_temp16_lo
    rol __gfx_temp16_hi
    inc __gfx_temp16_lo
    bne __gfx_circle_add_temp
    inc __gfx_temp16_hi
    jmp __gfx_circle_add_temp
__gfx_circle_dec_negative:
    ; temp = 2*y+1
    lda __gfx_circle_y_lo
    sta __gfx_temp16_lo
    lda __gfx_circle_y_hi
    sta __gfx_temp16_hi
    asl __gfx_temp16_lo
    rol __gfx_temp16_hi
    inc __gfx_temp16_lo
    bne __gfx_circle_add_temp
    inc __gfx_temp16_hi
__gfx_circle_add_temp:
    clc
    lda __gfx_circle_dec_lo
    adc __gfx_temp16_lo
    sta __gfx_circle_dec_lo
    lda __gfx_circle_dec_hi
    adc __gfx_temp16_hi
    sta __gfx_circle_dec_hi
    rts

__gfx_circle_plot8:
    ; (cx+x, cy+y)
    jsr __gfx_circle_point_xplus_yplus
    ; (cx-x, cy+y)
    jsr __gfx_circle_point_xminus_yplus
    ; (cx+x, cy-y)
    jsr __gfx_circle_point_xplus_yminus
    ; (cx-x, cy-y)
    jsr __gfx_circle_point_xminus_yminus
    ; swap x/y for remaining four octants
    jsr __gfx_circle_point_yplus_xplus
    jsr __gfx_circle_point_yminus_xplus
    jsr __gfx_circle_point_yplus_xminus
    jsr __gfx_circle_point_yminus_xminus
    rts

__gfx_circle_fill4:
    ; cx-x .. cx+x at cy+y
    jsr __gfx_circle_hline_x_at_yplus
    ; cx-x .. cx+x at cy-y
    jsr __gfx_circle_hline_x_at_yminus
    ; cx-y .. cx+y at cy+x
    jsr __gfx_circle_hline_y_at_xplus
    ; cx-y .. cx+y at cy-x
    jsr __gfx_circle_hline_y_at_xminus
    rts

; point helpers -------------------------------------------------------------
__gfx_circle_point_xplus_yplus:
    jsr __gfx_circle_set_x_plus_x
    jsr __gfx_circle_set_y_plus_y
    jmp __gfx_setpixel_core
__gfx_circle_point_xminus_yplus:
    jsr __gfx_circle_set_x_minus_x
    jsr __gfx_circle_set_y_plus_y
    jmp __gfx_setpixel_core
__gfx_circle_point_xplus_yminus:
    jsr __gfx_circle_set_x_plus_x
    jsr __gfx_circle_set_y_minus_y
    jmp __gfx_setpixel_core
__gfx_circle_point_xminus_yminus:
    jsr __gfx_circle_set_x_minus_x
    jsr __gfx_circle_set_y_minus_y
    jmp __gfx_setpixel_core
__gfx_circle_point_yplus_xplus:
    jsr __gfx_circle_set_x_plus_y
    jsr __gfx_circle_set_y_plus_x
    jmp __gfx_setpixel_core
__gfx_circle_point_yminus_xplus:
    jsr __gfx_circle_set_x_minus_y
    jsr __gfx_circle_set_y_plus_x
    jmp __gfx_setpixel_core
__gfx_circle_point_yplus_xminus:
    jsr __gfx_circle_set_x_plus_y
    jsr __gfx_circle_set_y_minus_x
    jmp __gfx_setpixel_core
__gfx_circle_point_yminus_xminus:
    jsr __gfx_circle_set_x_minus_y
    jsr __gfx_circle_set_y_minus_x
    jmp __gfx_setpixel_core

__gfx_circle_set_x_plus_x:
    clc
    lda __gfx_circle_cx_lo
    adc __gfx_circle_x_lo
    sta __gfx_x_lo
    lda __gfx_circle_cx_hi
    adc __gfx_circle_x_hi
    sta __gfx_x_hi
    rts
__gfx_circle_set_x_minus_x:
    sec
    lda __gfx_circle_cx_lo
    sbc __gfx_circle_x_lo
    sta __gfx_x_lo
    lda __gfx_circle_cx_hi
    sbc __gfx_circle_x_hi
    sta __gfx_x_hi
    rts
__gfx_circle_set_x_plus_y:
    clc
    lda __gfx_circle_cx_lo
    adc __gfx_circle_y_lo
    sta __gfx_x_lo
    lda __gfx_circle_cx_hi
    adc __gfx_circle_y_hi
    sta __gfx_x_hi
    rts
__gfx_circle_set_x_minus_y:
    sec
    lda __gfx_circle_cx_lo
    sbc __gfx_circle_y_lo
    sta __gfx_x_lo
    lda __gfx_circle_cx_hi
    sbc __gfx_circle_y_hi
    sta __gfx_x_hi
    rts
__gfx_circle_set_y_plus_y:
    clc
    lda __gfx_circle_cy_lo
    adc __gfx_circle_y_lo
    sta __gfx_y_lo
    lda __gfx_circle_cy_hi
    adc __gfx_circle_y_hi
    sta __gfx_y_hi
    rts
__gfx_circle_set_y_minus_y:
    sec
    lda __gfx_circle_cy_lo
    sbc __gfx_circle_y_lo
    sta __gfx_y_lo
    lda __gfx_circle_cy_hi
    sbc __gfx_circle_y_hi
    sta __gfx_y_hi
    rts
__gfx_circle_set_y_plus_x:
    clc
    lda __gfx_circle_cy_lo
    adc __gfx_circle_x_lo
    sta __gfx_y_lo
    lda __gfx_circle_cy_hi
    adc __gfx_circle_x_hi
    sta __gfx_y_hi
    rts
__gfx_circle_set_y_minus_x:
    sec
    lda __gfx_circle_cy_lo
    sbc __gfx_circle_x_lo
    sta __gfx_y_lo
    lda __gfx_circle_cy_hi
    sbc __gfx_circle_x_hi
    sta __gfx_y_hi
    rts

; span helpers --------------------------------------------------------------
__gfx_circle_hline_x_at_yplus:
    jsr __gfx_circle_span_x
    jsr __gfx_circle_set_y_plus_y
    jmp __gfx_hline_core
__gfx_circle_hline_x_at_yminus:
    jsr __gfx_circle_span_x
    jsr __gfx_circle_set_y_minus_y
    jmp __gfx_hline_core
__gfx_circle_hline_y_at_xplus:
    jsr __gfx_circle_span_y
    jsr __gfx_circle_set_y_plus_x
    jmp __gfx_hline_core
__gfx_circle_hline_y_at_xminus:
    jsr __gfx_circle_span_y
    jsr __gfx_circle_set_y_minus_x
    jmp __gfx_hline_core

__gfx_circle_span_x:
    sec
    lda __gfx_circle_cx_lo
    sbc __gfx_circle_x_lo
    sta __gfx_line_x1_lo
    lda __gfx_circle_cx_hi
    sbc __gfx_circle_x_hi
    sta __gfx_line_x1_hi
    clc
    lda __gfx_circle_cx_lo
    adc __gfx_circle_x_lo
    sta __gfx_line_x2_lo
    lda __gfx_circle_cx_hi
    adc __gfx_circle_x_hi
    sta __gfx_line_x2_hi
    rts
__gfx_circle_span_y:
    sec
    lda __gfx_circle_cx_lo
    sbc __gfx_circle_y_lo
    sta __gfx_line_x1_lo
    lda __gfx_circle_cx_hi
    sbc __gfx_circle_y_hi
    sta __gfx_line_x1_hi
    clc
    lda __gfx_circle_cx_lo
    adc __gfx_circle_y_lo
    sta __gfx_line_x2_lo
    lda __gfx_circle_cx_hi
    adc __gfx_circle_y_hi
    sta __gfx_line_x2_hi
    rts

; ---------------------------------------------------------------------------
; DrawTriangle and FillTriangle
; ---------------------------------------------------------------------------
DrawTriangle:
    tsx
    jsr __gfx_load_triangle_args
    lda $0103,x
    and #$0F
    sta __gfx_color
    jsr __gfx_drawtriangle_core
    rts

__gfx_load_triangle_args:
    lda $010F,x
    sta __gfx_tri_x1_lo
    lda $0110,x
    sta __gfx_tri_x1_hi
    lda $010D,x
    sta __gfx_tri_y1_lo
    lda $010E,x
    sta __gfx_tri_y1_hi
    lda $010B,x
    sta __gfx_tri_x2_lo
    lda $010C,x
    sta __gfx_tri_x2_hi
    lda $0109,x
    sta __gfx_tri_y2_lo
    lda $010A,x
    sta __gfx_tri_y2_hi
    lda $0107,x
    sta __gfx_tri_x3_lo
    lda $0108,x
    sta __gfx_tri_x3_hi
    lda $0105,x
    sta __gfx_tri_y3_lo
    lda $0106,x
    sta __gfx_tri_y3_hi
    rts

__gfx_drawtriangle_core:
    jsr __gfx_triangle_line_12
    jsr __gfx_triangle_line_23
    jsr __gfx_triangle_line_31
    rts

__gfx_triangle_line_12:
    lda __gfx_tri_x1_lo
    sta __gfx_p1_x_lo
    lda __gfx_tri_x1_hi
    sta __gfx_p1_x_hi
    lda __gfx_tri_y1_lo
    sta __gfx_p1_y_lo
    lda __gfx_tri_y1_hi
    sta __gfx_p1_y_hi
    lda __gfx_tri_x2_lo
    sta __gfx_p2_x_lo
    lda __gfx_tri_x2_hi
    sta __gfx_p2_x_hi
    lda __gfx_tri_y2_lo
    sta __gfx_p2_y_lo
    lda __gfx_tri_y2_hi
    sta __gfx_p2_y_hi
    jmp __gfx_drawline_core
__gfx_triangle_line_23:
    lda __gfx_tri_x2_lo
    sta __gfx_p1_x_lo
    lda __gfx_tri_x2_hi
    sta __gfx_p1_x_hi
    lda __gfx_tri_y2_lo
    sta __gfx_p1_y_lo
    lda __gfx_tri_y2_hi
    sta __gfx_p1_y_hi
    lda __gfx_tri_x3_lo
    sta __gfx_p2_x_lo
    lda __gfx_tri_x3_hi
    sta __gfx_p2_x_hi
    lda __gfx_tri_y3_lo
    sta __gfx_p2_y_lo
    lda __gfx_tri_y3_hi
    sta __gfx_p2_y_hi
    jmp __gfx_drawline_core
__gfx_triangle_line_31:
    lda __gfx_tri_x3_lo
    sta __gfx_p1_x_lo
    lda __gfx_tri_x3_hi
    sta __gfx_p1_x_hi
    lda __gfx_tri_y3_lo
    sta __gfx_p1_y_lo
    lda __gfx_tri_y3_hi
    sta __gfx_p1_y_hi
    lda __gfx_tri_x1_lo
    sta __gfx_p2_x_lo
    lda __gfx_tri_x1_hi
    sta __gfx_p2_x_hi
    lda __gfx_tri_y1_lo
    sta __gfx_p2_y_lo
    lda __gfx_tri_y1_hi
    sta __gfx_p2_y_hi
    jmp __gfx_drawline_core

FillTriangle:
    tsx
    ; Nine arguments: x1,y1,x2,y2,x3,y3,fill,border,width.
    lda $0113,x
    sta __gfx_tri_x1_lo
    lda $0114,x
    sta __gfx_tri_x1_hi
    lda $0111,x
    sta __gfx_tri_y1_lo
    lda $0112,x
    sta __gfx_tri_y1_hi
    lda $010F,x
    sta __gfx_tri_x2_lo
    lda $0110,x
    sta __gfx_tri_x2_hi
    lda $010D,x
    sta __gfx_tri_y2_lo
    lda $010E,x
    sta __gfx_tri_y2_hi
    lda $010B,x
    sta __gfx_tri_x3_lo
    lda $010C,x
    sta __gfx_tri_x3_hi
    lda $0109,x
    sta __gfx_tri_y3_lo
    lda $010A,x
    sta __gfx_tri_y3_hi
    lda $0107,x
    and #$0F
    sta __gfx_fill_color
    lda $0105,x
    and #$0F
    sta __gfx_border_color
    lda $0103,x
    sta __gfx_border_count

    ; Border first so its cell colour remains visible.
    lda __gfx_border_count
    beq __gfx_filltriangle_fan
    lda __gfx_border_color
    sta __gfx_color
    jsr __gfx_drawtriangle_core

__gfx_filltriangle_fan:
    lda __gfx_fill_color
    sta __gfx_color
    jsr __gfx_sort_triangle_by_y
    jsr __gfx_filltriangle_scanline
    rts

; Sort vertices so y1 <= y2 <= y3.
__gfx_sort_triangle_by_y:
    jsr __gfx_compare_y1_y2
    bcc __gfx_sort_12_ok
    beq __gfx_sort_12_ok
    jsr __gfx_swap_tri_12
__gfx_sort_12_ok:
    jsr __gfx_compare_y2_y3
    bcc __gfx_sort_23_ok
    beq __gfx_sort_23_ok
    jsr __gfx_swap_tri_23
__gfx_sort_23_ok:
    jsr __gfx_compare_y1_y2
    bcc __gfx_sort_done
    beq __gfx_sort_done
    jsr __gfx_swap_tri_12
__gfx_sort_done:
    rts

; Carry/zero are the unsigned 16-bit relation left >= right / equal.
; The clipped graphics coordinate range makes unsigned Y ordering sufficient.
__gfx_compare_y1_y2:
    lda __gfx_tri_y1_hi
    cmp __gfx_tri_y2_hi
    bne __gfx_compare_y12_done
    lda __gfx_tri_y1_lo
    cmp __gfx_tri_y2_lo
__gfx_compare_y12_done:
    rts
__gfx_compare_y2_y3:
    lda __gfx_tri_y2_hi
    cmp __gfx_tri_y3_hi
    bne __gfx_compare_y23_done
    lda __gfx_tri_y2_lo
    cmp __gfx_tri_y3_lo
__gfx_compare_y23_done:
    rts

__gfx_swap_tri_12:
    lda __gfx_tri_x1_lo
    ldx __gfx_tri_x2_lo
    stx __gfx_tri_x1_lo
    sta __gfx_tri_x2_lo
    lda __gfx_tri_x1_hi
    ldx __gfx_tri_x2_hi
    stx __gfx_tri_x1_hi
    sta __gfx_tri_x2_hi
    lda __gfx_tri_y1_lo
    ldx __gfx_tri_y2_lo
    stx __gfx_tri_y1_lo
    sta __gfx_tri_y2_lo
    lda __gfx_tri_y1_hi
    ldx __gfx_tri_y2_hi
    stx __gfx_tri_y1_hi
    sta __gfx_tri_y2_hi
    rts
__gfx_swap_tri_23:
    lda __gfx_tri_x2_lo
    ldx __gfx_tri_x3_lo
    stx __gfx_tri_x2_lo
    sta __gfx_tri_x3_lo
    lda __gfx_tri_x2_hi
    ldx __gfx_tri_x3_hi
    stx __gfx_tri_x2_hi
    sta __gfx_tri_x3_hi
    lda __gfx_tri_y2_lo
    ldx __gfx_tri_y3_lo
    stx __gfx_tri_y2_lo
    sta __gfx_tri_y3_lo
    lda __gfx_tri_y2_hi
    ldx __gfx_tri_y3_hi
    stx __gfx_tri_y2_hi
    sta __gfx_tri_y3_hi
    rts

__gfx_filltriangle_scanline:
    ; Degenerate horizontal triangle.
    lda __gfx_tri_y1_lo
    cmp __gfx_tri_y3_lo
    bne __gfx_filltri_nonflat
    lda __gfx_tri_y1_hi
    cmp __gfx_tri_y3_hi
    bne __gfx_filltri_nonflat
    lda __gfx_tri_x1_lo
    sta __gfx_line_x1_lo
    lda __gfx_tri_x1_hi
    sta __gfx_line_x1_hi
    lda __gfx_tri_x2_lo
    sta __gfx_line_x2_lo
    lda __gfx_tri_x2_hi
    sta __gfx_line_x2_hi
    jsr __gfx_expand_line_with_x3
    lda __gfx_tri_y1_lo
    sta __gfx_y_lo
    lda __gfx_tri_y1_hi
    sta __gfx_y_hi
    jsr __gfx_hline_core
    rts

__gfx_filltri_nonflat:
    ; Long edge A: vertex 1 -> vertex 3.
    lda __gfx_tri_x1_lo
    sta __gfx_edge_x_lo
    lda __gfx_tri_x1_hi
    sta __gfx_edge_x_hi
    lda __gfx_tri_x3_lo
    sta __gfx_edge_target_x_lo
    lda __gfx_tri_x3_hi
    sta __gfx_edge_target_x_hi
    lda __gfx_tri_y1_lo
    sta __gfx_edge_start_y_lo
    lda __gfx_tri_y1_hi
    sta __gfx_edge_start_y_hi
    lda __gfx_tri_y3_lo
    sta __gfx_edge_target_y_lo
    lda __gfx_tri_y3_hi
    sta __gfx_edge_target_y_hi
    jsr __gfx_edge_a_init_scan

    lda __gfx_tri_y1_lo
    sta __gfx_scan_y_lo
    lda __gfx_tri_y1_hi
    sta __gfx_scan_y_hi

    ; Top half is skipped for a flat-top triangle.
    lda __gfx_tri_y1_lo
    cmp __gfx_tri_y2_lo
    bne __gfx_filltri_top_begin
    lda __gfx_tri_y1_hi
    cmp __gfx_tri_y2_hi
    beq __gfx_filltri_bottom_init
__gfx_filltri_top_begin:
    lda __gfx_tri_x1_lo
    sta __gfx_edge_b_x_lo
    lda __gfx_tri_x1_hi
    sta __gfx_edge_b_x_hi
    lda __gfx_tri_x2_lo
    sta __gfx_edge_b_target_x_lo
    lda __gfx_tri_x2_hi
    sta __gfx_edge_b_target_x_hi
    lda __gfx_tri_y1_lo
    sta __gfx_edge_b_start_y_lo
    lda __gfx_tri_y1_hi
    sta __gfx_edge_b_start_y_hi
    lda __gfx_tri_y2_lo
    sta __gfx_edge_b_target_y_lo
    lda __gfx_tri_y2_hi
    sta __gfx_edge_b_target_y_hi
    jsr __gfx_edge_b_init_scan

__gfx_filltri_top_loop:
    ; Draw y1 .. y2-1.
    lda __gfx_scan_y_lo
    cmp __gfx_tri_y2_lo
    bne __gfx_filltri_top_draw
    lda __gfx_scan_y_hi
    cmp __gfx_tri_y2_hi
    beq __gfx_filltri_bottom_init
__gfx_filltri_top_draw:
    jsr __gfx_filltri_draw_current_span
    jsr __gfx_edge_a_advance_scan
    jsr __gfx_edge_b_advance_scan
    jsr __gfx_scan_y_inc
    jmp __gfx_filltri_top_loop

__gfx_filltri_bottom_init:
    ; Short edge B: vertex 2 -> vertex 3.
    lda __gfx_tri_x2_lo
    sta __gfx_edge_b_x_lo
    lda __gfx_tri_x2_hi
    sta __gfx_edge_b_x_hi
    lda __gfx_tri_x3_lo
    sta __gfx_edge_b_target_x_lo
    lda __gfx_tri_x3_hi
    sta __gfx_edge_b_target_x_hi
    lda __gfx_tri_y2_lo
    sta __gfx_edge_b_start_y_lo
    lda __gfx_tri_y2_hi
    sta __gfx_edge_b_start_y_hi
    lda __gfx_tri_y3_lo
    sta __gfx_edge_b_target_y_lo
    lda __gfx_tri_y3_hi
    sta __gfx_edge_b_target_y_hi
    jsr __gfx_edge_b_init_scan

__gfx_filltri_bottom_loop:
    jsr __gfx_filltri_draw_current_span
    lda __gfx_scan_y_lo
    cmp __gfx_tri_y3_lo
    bne __gfx_filltri_bottom_next
    lda __gfx_scan_y_hi
    cmp __gfx_tri_y3_hi
    beq __gfx_filltri_scan_done
__gfx_filltri_bottom_next:
    jsr __gfx_edge_a_advance_scan
    jsr __gfx_edge_b_advance_scan
    jsr __gfx_scan_y_inc
    jmp __gfx_filltri_bottom_loop
__gfx_filltri_scan_done:
    rts

__gfx_filltri_draw_current_span:
    lda __gfx_edge_x_lo
    sta __gfx_line_x1_lo
    lda __gfx_edge_x_hi
    sta __gfx_line_x1_hi
    lda __gfx_edge_b_x_lo
    sta __gfx_line_x2_lo
    lda __gfx_edge_b_x_hi
    sta __gfx_line_x2_hi
    lda __gfx_scan_y_lo
    sta __gfx_y_lo
    lda __gfx_scan_y_hi
    sta __gfx_y_hi
    jsr __gfx_hline_core
    rts

__gfx_scan_y_inc:
    inc __gfx_scan_y_lo
    bne __gfx_scan_y_inc_done
    inc __gfx_scan_y_hi
__gfx_scan_y_inc_done:
    rts

; Include x3 in a degenerate horizontal span.
__gfx_expand_line_with_x3:
    ; line_x1=min(x1,x2), line_x2=max(x1,x2) is normalised by HLine.
    ; Compare x3 with current pair and extend either side.
    sec
    lda __gfx_tri_x3_lo
    sbc __gfx_line_x1_lo
    lda __gfx_tri_x3_hi
    sbc __gfx_line_x1_hi
    bpl __gfx_expand_check_right
    lda __gfx_tri_x3_lo
    sta __gfx_line_x1_lo
    lda __gfx_tri_x3_hi
    sta __gfx_line_x1_hi
__gfx_expand_check_right:
    sec
    lda __gfx_line_x2_lo
    sbc __gfx_tri_x3_lo
    lda __gfx_line_x2_hi
    sbc __gfx_tri_x3_hi
    bpl __gfx_expand_done
    lda __gfx_tri_x3_lo
    sta __gfx_line_x2_lo
    lda __gfx_tri_x3_hi
    sta __gfx_line_x2_hi
__gfx_expand_done:
    rts

; Initialise edge A from current/target globals.
__gfx_edge_a_init_scan:
    sec
    lda __gfx_edge_target_x_lo
    sbc __gfx_edge_x_lo
    sta __gfx_edge_dx_lo
    lda __gfx_edge_target_x_hi
    sbc __gfx_edge_x_hi
    sta __gfx_edge_dx_hi
    bpl __gfx_edge_a_dx_pos
    lda __gfx_edge_dx_lo
    eor #$FF
    clc
    adc #$01
    sta __gfx_edge_dx_lo
    lda __gfx_edge_dx_hi
    eor #$FF
    adc #$00
    sta __gfx_edge_dx_hi
    lda #$FF
    bne __gfx_edge_a_store_sx
__gfx_edge_a_dx_pos:
    lda #$01
__gfx_edge_a_store_sx:
    sta __gfx_edge_sx
    sec
    lda __gfx_edge_target_y_lo
    sbc __gfx_edge_start_y_lo
    sta __gfx_edge_dy_lo
    lda __gfx_edge_target_y_hi
    sbc __gfx_edge_start_y_hi
    sta __gfx_edge_dy_hi
    lda #$00
    sta __gfx_edge_err_lo
    sta __gfx_edge_err_hi
    rts

__gfx_edge_b_init_scan:
    sec
    lda __gfx_edge_b_target_x_lo
    sbc __gfx_edge_b_x_lo
    sta __gfx_edge_b_dx_lo
    lda __gfx_edge_b_target_x_hi
    sbc __gfx_edge_b_x_hi
    sta __gfx_edge_b_dx_hi
    bpl __gfx_edge_b_dx_pos
    lda __gfx_edge_b_dx_lo
    eor #$FF
    clc
    adc #$01
    sta __gfx_edge_b_dx_lo
    lda __gfx_edge_b_dx_hi
    eor #$FF
    adc #$00
    sta __gfx_edge_b_dx_hi
    lda #$FF
    bne __gfx_edge_b_store_sx
__gfx_edge_b_dx_pos:
    lda #$01
__gfx_edge_b_store_sx:
    sta __gfx_edge_b_sx
    sec
    lda __gfx_edge_b_target_y_lo
    sbc __gfx_edge_b_start_y_lo
    sta __gfx_edge_b_dy_lo
    lda __gfx_edge_b_target_y_hi
    sbc __gfx_edge_b_start_y_hi
    sta __gfx_edge_b_dy_hi
    lda #$00
    sta __gfx_edge_b_err_lo
    sta __gfx_edge_b_err_hi
    rts

__gfx_edge_a_advance_scan:
    clc
    lda __gfx_edge_err_lo
    adc __gfx_edge_dx_lo
    sta __gfx_edge_err_lo
    lda __gfx_edge_err_hi
    adc __gfx_edge_dx_hi
    sta __gfx_edge_err_hi
__gfx_edge_a_advance_loop:
    lda __gfx_edge_err_hi
    cmp __gfx_edge_dy_hi
    bcc __gfx_edge_a_advance_done
    bne __gfx_edge_a_take_x
    lda __gfx_edge_err_lo
    cmp __gfx_edge_dy_lo
    bcc __gfx_edge_a_advance_done
__gfx_edge_a_take_x:
    sec
    lda __gfx_edge_err_lo
    sbc __gfx_edge_dy_lo
    sta __gfx_edge_err_lo
    lda __gfx_edge_err_hi
    sbc __gfx_edge_dy_hi
    sta __gfx_edge_err_hi
    lda __gfx_edge_sx
    bmi __gfx_edge_a_x_down
    inc __gfx_edge_x_lo
    bne __gfx_edge_a_advance_loop
    inc __gfx_edge_x_hi
    jmp __gfx_edge_a_advance_loop
__gfx_edge_a_x_down:
    lda __gfx_edge_x_lo
    bne __gfx_edge_a_x_dec
    dec __gfx_edge_x_hi
__gfx_edge_a_x_dec:
    dec __gfx_edge_x_lo
    jmp __gfx_edge_a_advance_loop
__gfx_edge_a_advance_done:
    rts

__gfx_edge_b_advance_scan:
    clc
    lda __gfx_edge_b_err_lo
    adc __gfx_edge_b_dx_lo
    sta __gfx_edge_b_err_lo
    lda __gfx_edge_b_err_hi
    adc __gfx_edge_b_dx_hi
    sta __gfx_edge_b_err_hi
__gfx_edge_b_advance_loop:
    lda __gfx_edge_b_err_hi
    cmp __gfx_edge_b_dy_hi
    bcc __gfx_edge_b_advance_done
    bne __gfx_edge_b_take_x
    lda __gfx_edge_b_err_lo
    cmp __gfx_edge_b_dy_lo
    bcc __gfx_edge_b_advance_done
__gfx_edge_b_take_x:
    sec
    lda __gfx_edge_b_err_lo
    sbc __gfx_edge_b_dy_lo
    sta __gfx_edge_b_err_lo
    lda __gfx_edge_b_err_hi
    sbc __gfx_edge_b_dy_hi
    sta __gfx_edge_b_err_hi
    lda __gfx_edge_b_sx
    bmi __gfx_edge_b_x_down
    inc __gfx_edge_b_x_lo
    bne __gfx_edge_b_advance_loop
    inc __gfx_edge_b_x_hi
    jmp __gfx_edge_b_advance_loop
__gfx_edge_b_x_down:
    lda __gfx_edge_b_x_lo
    bne __gfx_edge_b_x_dec
    dec __gfx_edge_b_x_hi
__gfx_edge_b_x_dec:
    dec __gfx_edge_b_x_lo
    jmp __gfx_edge_b_advance_loop
__gfx_edge_b_advance_done:
    rts

__gfx_edge_init:
    sec
    lda __gfx_tri_x3_lo
    sbc __gfx_edge_x_lo
    sta __gfx_edge_dx_lo
    lda __gfx_tri_x3_hi
    sbc __gfx_edge_x_hi
    sta __gfx_edge_dx_hi
    bpl __gfx_edge_dx_positive
    lda __gfx_edge_dx_lo
    eor #$FF
    clc
    adc #$01
    sta __gfx_edge_dx_lo
    lda __gfx_edge_dx_hi
    eor #$FF
    adc #$00
    sta __gfx_edge_dx_hi
    lda #$FF
    bne __gfx_edge_store_sx
__gfx_edge_dx_positive:
    lda #$01
__gfx_edge_store_sx:
    sta __gfx_edge_sx

    sec
    lda __gfx_tri_y3_lo
    sbc __gfx_edge_y_lo
    sta __gfx_edge_dy_lo
    lda __gfx_tri_y3_hi
    sbc __gfx_edge_y_hi
    sta __gfx_edge_dy_hi
    bpl __gfx_edge_dy_positive
    lda __gfx_edge_dy_lo
    eor #$FF
    clc
    adc #$01
    sta __gfx_edge_dy_lo
    lda __gfx_edge_dy_hi
    eor #$FF
    adc #$00
    sta __gfx_edge_dy_hi
    lda #$FF
    bne __gfx_edge_store_sy
__gfx_edge_dy_positive:
    lda #$01
__gfx_edge_store_sy:
    sta __gfx_edge_sy

    lda __gfx_edge_dx_hi
    cmp __gfx_edge_dy_hi
    bcc __gfx_edge_y_major
    bne __gfx_edge_x_major
    lda __gfx_edge_dx_lo
    cmp __gfx_edge_dy_lo
    bcc __gfx_edge_y_major
__gfx_edge_x_major:
    lda #$00
    sta __gfx_edge_major
    lda __gfx_edge_dx_hi
    lsr
    sta __gfx_edge_err_hi
    lda __gfx_edge_dx_lo
    ror
    sta __gfx_edge_err_lo
    rts
__gfx_edge_y_major:
    lda #$01
    sta __gfx_edge_major
    lda __gfx_edge_dy_hi
    lsr
    sta __gfx_edge_err_hi
    lda __gfx_edge_dy_lo
    ror
    sta __gfx_edge_err_lo
    rts

__gfx_edge_step:
    lda __gfx_edge_major
    bne __gfx_edge_step_y_major
    sec
    lda __gfx_edge_err_lo
    sbc __gfx_edge_dy_lo
    sta __gfx_edge_err_lo
    lda __gfx_edge_err_hi
    sbc __gfx_edge_dy_hi
    sta __gfx_edge_err_hi
    bcs __gfx_edge_x_no_y
    clc
    lda __gfx_edge_err_lo
    adc __gfx_edge_dx_lo
    sta __gfx_edge_err_lo
    lda __gfx_edge_err_hi
    adc __gfx_edge_dx_hi
    sta __gfx_edge_err_hi
    jsr __gfx_step_edge_y
__gfx_edge_x_no_y:
    jsr __gfx_step_edge_x
    rts
__gfx_edge_step_y_major:
    sec
    lda __gfx_edge_err_lo
    sbc __gfx_edge_dx_lo
    sta __gfx_edge_err_lo
    lda __gfx_edge_err_hi
    sbc __gfx_edge_dx_hi
    sta __gfx_edge_err_hi
    bcs __gfx_edge_y_no_x
    clc
    lda __gfx_edge_err_lo
    adc __gfx_edge_dy_lo
    sta __gfx_edge_err_lo
    lda __gfx_edge_err_hi
    adc __gfx_edge_dy_hi
    sta __gfx_edge_err_hi
    jsr __gfx_step_edge_x
__gfx_edge_y_no_x:
    jsr __gfx_step_edge_y
    rts

__gfx_step_edge_x:
    lda __gfx_edge_sx
    bmi __gfx_step_edge_x_down
    inc __gfx_edge_x_lo
    bne __gfx_step_edge_x_done
    inc __gfx_edge_x_hi
__gfx_step_edge_x_done:
    rts
__gfx_step_edge_x_down:
    lda __gfx_edge_x_lo
    bne __gfx_step_edge_x_dec
    dec __gfx_edge_x_hi
__gfx_step_edge_x_dec:
    dec __gfx_edge_x_lo
    rts
__gfx_step_edge_y:
    lda __gfx_edge_sy
    bmi __gfx_step_edge_y_down
    inc __gfx_edge_y_lo
    bne __gfx_step_edge_y_done
    inc __gfx_edge_y_hi
__gfx_step_edge_y_done:
    rts
__gfx_step_edge_y_down:
    lda __gfx_edge_y_lo
    bne __gfx_step_edge_y_dec
    dec __gfx_edge_y_hi
__gfx_step_edge_y_dec:
    dec __gfx_edge_y_lo
    rts

; ---------------------------------------------------------------------------
; DrawTriangleAngles
; Angles are quantised to five-degree sine table entries, matching the common
; implementation but without relying on generated multiply/divide code.
; ---------------------------------------------------------------------------
DrawTriangleAngles:
    tsx
    lda $0113,x
    sta __gfx_center_x_lo
    lda $0114,x
    sta __gfx_center_x_hi
    lda $0111,x
    sta __gfx_center_y_lo
    lda $0112,x
    sta __gfx_center_y_hi
    lda $010F,x
    sta __gfx_radius1_lo
    lda $0110,x
    sta __gfx_radius1_hi
    lda $010D,x
    sta __gfx_radius2_lo
    lda $010E,x
    sta __gfx_radius2_hi
    lda $010B,x
    sta __gfx_radius3_lo
    lda $010C,x
    sta __gfx_radius3_hi
    lda $0109,x
    sta __gfx_angle1_lo
    lda $010A,x
    sta __gfx_angle1_hi
    lda $0107,x
    sta __gfx_angle2_lo
    lda $0108,x
    sta __gfx_angle2_hi
    lda $0105,x
    sta __gfx_angle3_lo
    lda $0106,x
    sta __gfx_angle3_hi
    lda $0103,x
    and #$0F
    sta __gfx_color

    ; Vertex 1
    lda __gfx_radius1_lo
    sta __gfx_mul_radius_lo
    lda __gfx_radius1_hi
    sta __gfx_mul_radius_hi
    lda __gfx_angle1_lo
    sta __gfx_trig_angle_lo
    lda __gfx_angle1_hi
    sta __gfx_trig_angle_hi
    jsr __gfx_make_vertex_1

    ; Vertex 2
    lda __gfx_radius2_lo
    sta __gfx_mul_radius_lo
    lda __gfx_radius2_hi
    sta __gfx_mul_radius_hi
    lda __gfx_angle2_lo
    sta __gfx_trig_angle_lo
    lda __gfx_angle2_hi
    sta __gfx_trig_angle_hi
    jsr __gfx_make_vertex_2

    ; Vertex 3
    lda __gfx_radius3_lo
    sta __gfx_mul_radius_lo
    lda __gfx_radius3_hi
    sta __gfx_mul_radius_hi
    lda __gfx_angle3_lo
    sta __gfx_trig_angle_lo
    lda __gfx_angle3_hi
    sta __gfx_trig_angle_hi
    jsr __gfx_make_vertex_3

    jsr __gfx_drawtriangle_core
    rts

__gfx_make_vertex_1:
    jsr __gfx_compute_vertex_xy
    lda __gfx_vertex_x_lo
    sta __gfx_tri_x1_lo
    lda __gfx_vertex_x_hi
    sta __gfx_tri_x1_hi
    lda __gfx_vertex_y_lo
    sta __gfx_tri_y1_lo
    lda __gfx_vertex_y_hi
    sta __gfx_tri_y1_hi
    rts
__gfx_make_vertex_2:
    jsr __gfx_compute_vertex_xy
    lda __gfx_vertex_x_lo
    sta __gfx_tri_x2_lo
    lda __gfx_vertex_x_hi
    sta __gfx_tri_x2_hi
    lda __gfx_vertex_y_lo
    sta __gfx_tri_y2_lo
    lda __gfx_vertex_y_hi
    sta __gfx_tri_y2_hi
    rts
__gfx_make_vertex_3:
    jsr __gfx_compute_vertex_xy
    lda __gfx_vertex_x_lo
    sta __gfx_tri_x3_lo
    lda __gfx_vertex_x_hi
    sta __gfx_tri_x3_hi
    lda __gfx_vertex_y_lo
    sta __gfx_tri_y3_lo
    lda __gfx_vertex_y_hi
    sta __gfx_tri_y3_hi
    rts

__gfx_compute_vertex_xy:
    ; Preserve original angle.
    lda __gfx_trig_angle_lo
    sta __gfx_saved_angle_lo
    lda __gfx_trig_angle_hi
    sta __gfx_saved_angle_hi
    ; cos(a) = sin(a + 90)
    clc
    lda __gfx_trig_angle_lo
    adc #$5A
    sta __gfx_trig_angle_lo
    lda __gfx_trig_angle_hi
    adc #$00
    sta __gfx_trig_angle_hi
    jsr __gfx_sin_scaled
    jsr __gfx_mul_scaled
    clc
    lda __gfx_center_x_lo
    adc __gfx_scaled_lo
    sta __gfx_vertex_x_lo
    lda __gfx_center_x_hi
    adc __gfx_scaled_hi
    sta __gfx_vertex_x_hi
    ; sin(a)
    lda __gfx_saved_angle_lo
    sta __gfx_trig_angle_lo
    lda __gfx_saved_angle_hi
    sta __gfx_trig_angle_hi
    jsr __gfx_sin_scaled
    jsr __gfx_mul_scaled
    clc
    lda __gfx_center_y_lo
    adc __gfx_scaled_lo
    sta __gfx_vertex_y_lo
    lda __gfx_center_y_hi
    adc __gfx_scaled_hi
    sta __gfx_vertex_y_hi
    ; Restore input angle for caller diagnostics/reuse.
    lda __gfx_saved_angle_lo
    sta __gfx_trig_angle_lo
    lda __gfx_saved_angle_hi
    sta __gfx_trig_angle_hi
    rts

__gfx_sin_scaled:
    ; Normalise signed angle into 0..359.
__gfx_sin_normalize_negative:
    lda __gfx_trig_angle_hi
    bpl __gfx_sin_normalize_high
    clc
    lda __gfx_trig_angle_lo
    adc #$68
    sta __gfx_trig_angle_lo
    lda __gfx_trig_angle_hi
    adc #$01
    sta __gfx_trig_angle_hi
    jmp __gfx_sin_normalize_negative
__gfx_sin_normalize_high:
    lda __gfx_trig_angle_hi
    cmp #$01
    bcc __gfx_sin_quadrant
    bne __gfx_sin_sub_360
    lda __gfx_trig_angle_lo
    cmp #$68
    bcc __gfx_sin_quadrant
__gfx_sin_sub_360:
    sec
    lda __gfx_trig_angle_lo
    sbc #$68
    sta __gfx_trig_angle_lo
    lda __gfx_trig_angle_hi
    sbc #$01
    sta __gfx_trig_angle_hi
    jmp __gfx_sin_normalize_high

__gfx_sin_quadrant:
    lda #$00
    sta __gfx_quadrant
    lda __gfx_trig_angle_hi
    bne __gfx_sin_high_256

    ; 0..255: distinguish all three represented quadrants explicitly.
    lda __gfx_trig_angle_lo
    cmp #$5A
    bcc __gfx_sin_remainder_ready
    cmp #$B4
    bcc __gfx_sin_q1_low
    ; quadrant 2, 180..255
    sec
    sbc #$B4
    sta __gfx_remainder
    lda #$02
    sta __gfx_quadrant
    jmp __gfx_sin_index
__gfx_sin_q1_low:
    sec
    sbc #$5A
    sta __gfx_remainder
    lda #$01
    sta __gfx_quadrant
    jmp __gfx_sin_reflect

__gfx_sin_high_256:
    ; 256..359: low byte $00-$0D is quadrant 2, $0E-$67 quadrant 3.
    lda __gfx_trig_angle_lo
    cmp #$0E
    bcc __gfx_sin_q2_high
    sec
    sbc #$0E
    sta __gfx_remainder
    lda #$03
    sta __gfx_quadrant
    jmp __gfx_sin_reflect
__gfx_sin_q2_high:
    clc
    lda __gfx_trig_angle_lo
    adc #$4C
    sta __gfx_remainder
    lda #$02
    sta __gfx_quadrant
    jmp __gfx_sin_index
__gfx_sin_remainder_ready:
    sta __gfx_remainder
    jmp __gfx_sin_index
__gfx_sin_reflect:
    sec
    lda #$5A
    sbc __gfx_remainder
    sta __gfx_remainder

__gfx_sin_index:
    clc
    lda __gfx_remainder
    adc #$02
    sta __gfx_div_value
    lda #$00
    sta __gfx_sine_index
__gfx_sin_div5_loop:
    lda __gfx_div_value
    cmp #$05
    bcc __gfx_sin_lookup
    sec
    sbc #$05
    sta __gfx_div_value
    inc __gfx_sine_index
    jmp __gfx_sin_div5_loop
__gfx_sin_lookup:
    ldy __gfx_sine_index
    lda __gfx_sine_table_lo,y
    sta __gfx_trig_value_lo
    lda __gfx_sine_table_hi,y
    sta __gfx_trig_value_hi
    lda __gfx_quadrant
    cmp #$02
    bcc __gfx_sin_done
    lda __gfx_trig_value_lo
    eor #$FF
    clc
    adc #$01
    sta __gfx_trig_value_lo
    lda __gfx_trig_value_hi
    eor #$FF
    adc #$00
    sta __gfx_trig_value_hi
__gfx_sin_done:
    rts

__gfx_mul_scaled:
    ; signed(trig) * signed(radius), then divide by 256.
    lda #$00
    sta __gfx_mul_sign
    lda __gfx_trig_value_hi
    bpl __gfx_mul_trig_positive
    inc __gfx_mul_sign
    lda __gfx_trig_value_lo
    eor #$FF
    clc
    adc #$01
    sta __gfx_mul_value_lo
    lda __gfx_trig_value_hi
    eor #$FF
    adc #$00
    sta __gfx_mul_value_hi
    jmp __gfx_mul_radius_sign
__gfx_mul_trig_positive:
    lda __gfx_trig_value_lo
    sta __gfx_mul_value_lo
    lda __gfx_trig_value_hi
    sta __gfx_mul_value_hi
__gfx_mul_radius_sign:
    lda __gfx_mul_radius_hi
    bpl __gfx_mul_radius_positive
    lda __gfx_mul_sign
    eor #$01
    sta __gfx_mul_sign
    lda __gfx_mul_radius_lo
    eor #$FF
    clc
    adc #$01
    sta __gfx_mul_count_lo
    lda __gfx_mul_radius_hi
    eor #$FF
    adc #$00
    sta __gfx_mul_count_hi
    jmp __gfx_mul_begin
__gfx_mul_radius_positive:
    lda __gfx_mul_radius_lo
    sta __gfx_mul_count_lo
    lda __gfx_mul_radius_hi
    sta __gfx_mul_count_hi
__gfx_mul_begin:
    lda #$00
    sta __gfx_product_lo
    sta __gfx_product_mid
    sta __gfx_product_hi
__gfx_mul_loop:
    lda __gfx_mul_count_lo
    ora __gfx_mul_count_hi
    beq __gfx_mul_finish
    clc
    lda __gfx_product_lo
    adc __gfx_mul_value_lo
    sta __gfx_product_lo
    lda __gfx_product_mid
    adc __gfx_mul_value_hi
    sta __gfx_product_mid
    lda __gfx_product_hi
    adc #$00
    sta __gfx_product_hi
    lda __gfx_mul_count_lo
    bne __gfx_mul_dec_low
    dec __gfx_mul_count_hi
__gfx_mul_dec_low:
    dec __gfx_mul_count_lo
    jmp __gfx_mul_loop
__gfx_mul_finish:
    lda __gfx_product_mid
    sta __gfx_scaled_lo
    lda __gfx_product_hi
    sta __gfx_scaled_hi
    lda __gfx_mul_sign
    beq __gfx_mul_done
    lda __gfx_scaled_lo
    eor #$FF
    clc
    adc #$01
    sta __gfx_scaled_lo
    lda __gfx_scaled_hi
    eor #$FF
    adc #$00
    sta __gfx_scaled_hi
__gfx_mul_done:
    rts

; ---------------------------------------------------------------------------
; FloodFill(x,y,fill)
; 256-entry bounded stack in RAM hidden from VIC-II by the bank-2 char shadow.
; ---------------------------------------------------------------------------
FloodFill:
    tsx
    lda $0107,x
    sta __gfx_flood_x_lo
    lda $0108,x
    sta __gfx_flood_x_hi
    lda $0105,x
    sta __gfx_flood_y
    lda $0103,x
    and #$0F
    sta __gfx_fill_color
    lda __gfx_flood_x_lo
    sta __gfx_x_lo
    lda __gfx_flood_x_hi
    sta __gfx_x_hi
    lda __gfx_flood_y
    sta __gfx_y_lo
    lda #$00
    sta __gfx_y_hi
    jsr __gfx_getpixel_core
    sta __gfx_flood_source
    cmp __gfx_fill_color
    bne __gfx_flood_start
    jmp __gfx_flood_done
__gfx_flood_start:
    lda #$00
    sta __gfx_flood_top
    jsr __gfx_flood_push_current
__gfx_flood_loop:
    lda __gfx_flood_top
    bne __gfx_flood_have_item
    jmp __gfx_flood_done
__gfx_flood_have_item:
    dec __gfx_flood_top
    ldy __gfx_flood_top
    lda $9000,y
    sta __gfx_flood_x_lo
    lda $9100,y
    sta __gfx_flood_x_hi
    lda $9200,y
    sta __gfx_flood_y
    lda __gfx_flood_x_lo
    sta __gfx_x_lo
    lda __gfx_flood_x_hi
    sta __gfx_x_hi
    lda __gfx_flood_y
    sta __gfx_y_lo
    lda #$00
    sta __gfx_y_hi
    jsr __gfx_getpixel_core
    cmp __gfx_flood_source
    bne __gfx_flood_loop
    lda __gfx_fill_color
    sta __gfx_color
    jsr __gfx_setpixel_core

    ; left
    lda __gfx_flood_x_lo
    ora __gfx_flood_x_hi
    beq __gfx_flood_no_left
    jsr __gfx_flood_x_dec
    jsr __gfx_flood_push_current
    jsr __gfx_flood_x_inc
__gfx_flood_no_left:
    ; right if x < 319
    lda __gfx_flood_x_hi
    cmp #$01
    bcc __gfx_flood_add_right
    bne __gfx_flood_no_right
    lda __gfx_flood_x_lo
    cmp #$3F
    bcs __gfx_flood_no_right
__gfx_flood_add_right:
    jsr __gfx_flood_x_inc
    jsr __gfx_flood_push_current
    jsr __gfx_flood_x_dec
__gfx_flood_no_right:
    lda __gfx_flood_y
    beq __gfx_flood_no_up
    dec __gfx_flood_y
    jsr __gfx_flood_push_current
    inc __gfx_flood_y
__gfx_flood_no_up:
    lda __gfx_flood_y
    cmp #$C7
    bcc __gfx_flood_add_down
    jmp __gfx_flood_loop
__gfx_flood_add_down:
    inc __gfx_flood_y
    jsr __gfx_flood_push_current
    dec __gfx_flood_y
    jmp __gfx_flood_loop
__gfx_flood_done:
    rts

__gfx_flood_push_current:
    lda __gfx_flood_top
    cmp #$FF
    beq __gfx_flood_push_done
    tay
    lda __gfx_flood_x_lo
    sta $9000,y
    lda __gfx_flood_x_hi
    sta $9100,y
    lda __gfx_flood_y
    sta $9200,y
    inc __gfx_flood_top
__gfx_flood_push_done:
    rts
__gfx_flood_x_inc:
    inc __gfx_flood_x_lo
    bne __gfx_flood_x_inc_done
    inc __gfx_flood_x_hi
__gfx_flood_x_inc_done:
    rts
__gfx_flood_x_dec:
    lda __gfx_flood_x_lo
    bne __gfx_flood_x_dec_low
    dec __gfx_flood_x_hi
__gfx_flood_x_dec_low:
    dec __gfx_flood_x_lo
    rts

__gfx_getpixel_core:
    jsr __gfx_validate_xy
    bcs __gfx_getpixel_core_invalid
    jsr __gfx_build_addresses
    jsr __gfx_decode_pixel_code
    lda __gfx_pixel_code
    beq __gfx_getpixel_core_background
    cmp #$01
    beq __gfx_getpixel_core_slot1
    cmp #$02
    beq __gfx_getpixel_core_slot2
    ; Slot 3 is stored in colour RAM at $D800 + cell index.
    jsr __gfx_read_color_slot3
    rts
__gfx_getpixel_core_slot1:
    ldy #$00
    lda (GFX_SCREEN_LO),y
    lsr
    lsr
    lsr
    lsr
    and #$0F
    rts
__gfx_getpixel_core_slot2:
    ldy #$00
    lda (GFX_SCREEN_LO),y
    and #$0F
    rts
__gfx_getpixel_core_background:
    lda __gfx_background
    and #$0F
    rts
__gfx_getpixel_core_invalid:
    lda #$00
    rts


; ---------------------------------------------------------------------------
; Internal multicolor pixel core
; ---------------------------------------------------------------------------
; The public API keeps 320 horizontal coordinates.  VIC-II multicolor bitmap
; pixels are two hardware pixels wide, therefore x and x^1 address the same
; two-bit bitmap field.  Screen positions and object sizes remain identical.
__gfx_setpixel_core:
    jsr __gfx_validate_xy
    bcs __gfx_setpixel_done
    jsr __gfx_build_addresses
    jsr __gfx_select_pixel_code
    jsr __gfx_write_pixel_code
__gfx_setpixel_done:
    rts

; Select or allocate one of the three local cell colours.  Code 0 is the
; global background, codes 1/2 are the screen-RAM nibbles, and code 3 is
; colour RAM.  A cell can therefore hold background plus three object colours.
__gfx_select_pixel_code:
    lda __gfx_color
    and #$0F
    sta __gfx_color
    cmp __gfx_background
    bne __gfx_select_nonbackground
    lda #$00
    sta __gfx_pixel_code
    rts

__gfx_select_nonbackground:
    ldy #$00
    lda (GFX_PALETTE_LO),y
    and #$07
    sta __gfx_palette_used
    lda (GFX_SCREEN_LO),y
    sta __gfx_screen_value

    ; Existing slot 1?
    lda __gfx_palette_used
    and #$01
    beq __gfx_select_check_slot2
    lda __gfx_screen_value
    lsr
    lsr
    lsr
    lsr
    and #$0F
    cmp __gfx_color
    beq __gfx_select_code1

__gfx_select_check_slot2:
    lda __gfx_palette_used
    and #$02
    beq __gfx_select_check_slot3
    lda __gfx_screen_value
    and #$0F
    cmp __gfx_color
    beq __gfx_select_code2

__gfx_select_check_slot3:
    lda __gfx_palette_used
    and #$04
    beq __gfx_select_allocate
    jsr __gfx_read_color_slot3
    cmp __gfx_color
    beq __gfx_select_code3

__gfx_select_allocate:
    lda __gfx_palette_used
    and #$01
    beq __gfx_allocate_slot1
    lda __gfx_palette_used
    and #$02
    beq __gfx_allocate_slot2
    lda __gfx_palette_used
    and #$04
    beq __gfx_allocate_slot3

    ; Four non-background colours in one 4x8 cell are impossible on a VIC-II.
    ; Keep the existing palette stable and use slot 3 for the new pixel rather
    ; than recolouring an already drawn block.  The counter helps diagnostics.
    inc __gfx_palette_overflow
    lda #$03
    sta __gfx_pixel_code
    rts

__gfx_allocate_slot1:
    lda __gfx_screen_value
    and #$0F
    sta __gfx_temp
    lda __gfx_color
    asl
    asl
    asl
    asl
    ora __gfx_temp
    ldy #$00
    sta (GFX_SCREEN_LO),y
    lda __gfx_palette_used
    ora #$01
    sta (GFX_PALETTE_LO),y
__gfx_select_code1:
    lda #$01
    sta __gfx_pixel_code
    rts

__gfx_allocate_slot2:
    lda __gfx_screen_value
    and #$F0
    ora __gfx_color
    ldy #$00
    sta (GFX_SCREEN_LO),y
    lda __gfx_palette_used
    ora #$02
    sta (GFX_PALETTE_LO),y
__gfx_select_code2:
    lda #$02
    sta __gfx_pixel_code
    rts

__gfx_allocate_slot3:
    lda __gfx_color
    jsr __gfx_write_color_slot3
    ldy #$00
    lda __gfx_palette_used
    ora #$04
    sta (GFX_PALETTE_LO),y
__gfx_select_code3:
    lda #$03
    sta __gfx_pixel_code
    rts

; GFX_PALETTE_BASE and colour RAM have the same low byte; their high bytes
; differ by $50.  Temporarily retarget the zero-page pointer and restore it.
__gfx_read_color_slot3:
    lda GFX_PALETTE_HI
    clc
    adc #$50
    sta GFX_PALETTE_HI
    ldy #$00
    lda (GFX_PALETTE_LO),y
    and #$0F
    sta __gfx_color_slot3
    lda GFX_PALETTE_HI
    sec
    sbc #$50
    sta GFX_PALETTE_HI
    lda __gfx_color_slot3
    rts

; A contains the colour to write.
__gfx_write_color_slot3:
    and #$0F
    sta __gfx_color_slot3
    lda GFX_PALETTE_HI
    clc
    adc #$50
    sta GFX_PALETTE_HI
    ldy #$00
    lda __gfx_color_slot3
    sta (GFX_PALETTE_LO),y
    lda GFX_PALETTE_HI
    sec
    sbc #$50
    sta GFX_PALETTE_HI
    rts

__gfx_write_pixel_code:
    ldy __gfx_pair_index
    lda __gfx_clear_masks,y
    sta __gfx_temp
    ldy #$00
    lda (GFX_BITMAP_LO),y
    and __gfx_temp
    sta __gfx_temp

    lda __gfx_pixel_code
    asl
    asl
    asl
    clc
    adc __gfx_pair_index
    tay
    lda __gfx_code_patterns,y
    ora __gfx_temp
    ldy #$00
    sta (GFX_BITMAP_LO),y
    rts

__gfx_decode_pixel_code:
    ldy #$00
    lda (GFX_BITMAP_LO),y
    and __gfx_mask
    sta __gfx_temp
    ldy __gfx_pair_index
    lda __gfx_pair_shifts,y
    tax
    lda __gfx_temp
__gfx_decode_shift_loop:
    cpx #$00
    beq __gfx_decode_shift_done
    lsr
    dex
    jmp __gfx_decode_shift_loop
__gfx_decode_shift_done:
    and #$03
    sta __gfx_pixel_code
    rts

__gfx_validate_xy:
    lda __gfx_x_hi
    bmi __gfx_xy_invalid
    cmp #$02
    bcs __gfx_xy_invalid
    cmp #$01
    bne __gfx_xy_x_ok
    lda __gfx_x_lo
    cmp #$40
    bcs __gfx_xy_invalid
__gfx_xy_x_ok:
    lda __gfx_y_hi
    bne __gfx_xy_invalid
    lda __gfx_y_lo
    cmp #$C8
    bcs __gfx_xy_invalid
    clc
    rts
__gfx_xy_invalid:
    sec
    rts

__gfx_build_addresses:
    ldy __gfx_y_lo
    lda __gfx_bitmap_y_lo,y
    sta GFX_BITMAP_LO
    lda __gfx_bitmap_y_hi,y
    sta GFX_BITMAP_HI

    lda __gfx_x_lo
    and #$F8
    clc
    adc GFX_BITMAP_LO
    sta GFX_BITMAP_LO
    lda __gfx_x_hi
    adc GFX_BITMAP_HI
    sta GFX_BITMAP_HI

    ldy __gfx_y_lo
    lda __gfx_screen_y_lo,y
    sta GFX_SCREEN_LO
    lda __gfx_screen_y_hi,y
    sta GFX_SCREEN_HI

    lda __gfx_x_hi
    beq __gfx_cell_x_low
    lda #$20
    bne __gfx_cell_x_store
__gfx_cell_x_low:
    lda #$00
__gfx_cell_x_store:
    sta __gfx_cell_x
    lda __gfx_x_lo
    lsr
    lsr
    lsr
    ora __gfx_cell_x
    clc
    adc GFX_SCREEN_LO
    sta GFX_SCREEN_LO
    bcc __gfx_screen_no_carry
    inc GFX_SCREEN_HI
__gfx_screen_no_carry:
    lda GFX_SCREEN_LO
    sta GFX_PALETTE_LO
    lda GFX_SCREEN_HI
    sec
    sbc #$04
    sta GFX_PALETTE_HI

    lda __gfx_x_lo
    and #$07
    sta __gfx_pair_index
    tay
    lda __gfx_masks,y
    sta __gfx_mask
    rts

; ---------------------------------------------------------------------------
; Fast clears
; ---------------------------------------------------------------------------
__gfx_clear_graphics:
    lda #$00
    sta __gfx_palette_overflow
    lda #$00
    ldx #$00
__gfx_clear_bitmap_pages:
    sta $A000,x
    sta $A100,x
    sta $A200,x
    sta $A300,x
    sta $A400,x
    sta $A500,x
    sta $A600,x
    sta $A700,x
    sta $A800,x
    sta $A900,x
    sta $AA00,x
    sta $AB00,x
    sta $AC00,x
    sta $AD00,x
    sta $AE00,x
    sta $AF00,x
    sta $B000,x
    sta $B100,x
    sta $B200,x
    sta $B300,x
    sta $B400,x
    sta $B500,x
    sta $B600,x
    sta $B700,x
    sta $B800,x
    sta $B900,x
    sta $BA00,x
    sta $BB00,x
    sta $BC00,x
    sta $BD00,x
    sta $BE00,x
    inx
    bne __gfx_clear_bitmap_pages
    ldx #$3F
__gfx_clear_bitmap_tail:
    sta $BF00,x
    dex
    bpl __gfx_clear_bitmap_tail

    ; Palette-slot usage table: no local colours allocated yet.
    lda #$00
    ldx #$00
__gfx_clear_palette_pages:
    sta $8800,x
    sta $8900,x
    sta $8A00,x
    inx
    bne __gfx_clear_palette_pages
    ldx #$00
__gfx_clear_palette_tail:
    sta $8B00,x
    inx
    cpx #$E8
    bne __gfx_clear_palette_tail

    ; Screen nibbles and colour RAM contain palette slots 1, 2 and 3.
    lda #$00
    ldx #$00
__gfx_clear_screen_pages:
    sta $8C00,x
    sta $8D00,x
    sta $8E00,x
    sta $D800,x
    sta $D900,x
    sta $DA00,x
    inx
    bne __gfx_clear_screen_pages
    ldx #$00
__gfx_clear_screen_tail:
    sta $8F00,x
    sta $DB00,x
    inx
    cpx #$E8
    bne __gfx_clear_screen_tail

    lda __gfx_background
    and #$0F
    sta $D020
    sta $D021
    rts

__gfx_clear_text:
    lda #$20
    ldx #$00
__gfx_clear_text_pages:
    sta $0400,x
    sta $0500,x
    sta $0600,x
    inx
    bne __gfx_clear_text_pages
    ldx #$00
__gfx_clear_text_tail:
    sta $0700,x
    inx
    cpx #$E8
    bne __gfx_clear_text_tail

    lda __gfx_text_color
    ldx #$00
__gfx_clear_color_pages:
    sta $D800,x
    sta $D900,x
    sta $DA00,x
    inx
    bne __gfx_clear_color_pages
    ldx #$00
__gfx_clear_color_tail:
    sta $DB00,x
    inx
    cpx #$E8
    bne __gfx_clear_color_tail
    rts

; ---------------------------------------------------------------------------
; State and tables
; ---------------------------------------------------------------------------
__gfx_active:        .byte $00
__gfx_text_color:    .byte $01
__gfx_background:    .byte $00
__gfx_text_mode:     .byte $00
__gfx_saved_d011:    .byte $1B
__gfx_saved_d016:    .byte $C8
__gfx_saved_d018:    .byte $14
__gfx_saved_dd00:    .byte $03
__gfx_saved_dd02:    .byte $3F
__gfx_saved_cpu_port:.byte $37
__gfx_x_lo:          .byte $00
__gfx_x_hi:          .byte $00
__gfx_y_lo:          .byte $00
__gfx_y_hi:          .byte $00
__gfx_color:         .byte $00
__gfx_mask:          .byte $C0
__gfx_pair_index:    .byte $00
__gfx_pixel_code:    .byte $00
__gfx_palette_used:  .byte $00
__gfx_screen_value:  .byte $00
__gfx_color_slot3:   .byte $00
__gfx_palette_overflow:.byte $00
__gfx_temp:          .byte $00
__gfx_cell_x:        .byte $00
__gfx_line_x1_lo:    .byte $00
__gfx_line_x1_hi:    .byte $00
__gfx_line_x2_lo:    .byte $00
__gfx_line_x2_hi:    .byte $00

; Direct primitive working state ------------------------------------------------
__gfx_p1_x_lo:        .byte $00
__gfx_p1_x_hi:        .byte $00
__gfx_p1_y_lo:        .byte $00
__gfx_p1_y_hi:        .byte $00
__gfx_p2_x_lo:        .byte $00
__gfx_p2_x_hi:        .byte $00
__gfx_p2_y_lo:        .byte $00
__gfx_p2_y_hi:        .byte $00
__gfx_dx_lo:          .byte $00
__gfx_dx_hi:          .byte $00
__gfx_dy_lo:          .byte $00
__gfx_dy_hi:          .byte $00
__gfx_error_lo:       .byte $00
__gfx_error_hi:       .byte $00
__gfx_step_x:         .byte $01
__gfx_step_y:         .byte $01
__gfx_temp16_lo:      .byte $00
__gfx_temp16_hi:      .byte $00

__gfx_rect_left_lo:   .byte $00
__gfx_rect_left_hi:   .byte $00
__gfx_rect_top_lo:    .byte $00
__gfx_rect_top_hi:    .byte $00
__gfx_rect_right_lo:  .byte $00
__gfx_rect_right_hi:  .byte $00
__gfx_rect_bottom_lo: .byte $00
__gfx_rect_bottom_hi: .byte $00
__gfx_fill_y_lo:      .byte $00
__gfx_fill_y_hi:      .byte $00
__gfx_fill_color:     .byte $00
__gfx_border_color:   .byte $00
__gfx_border_count:   .byte $00

__gfx_circle_cx_lo:   .byte $00
__gfx_circle_cx_hi:   .byte $00
__gfx_circle_cy_lo:   .byte $00
__gfx_circle_cy_hi:   .byte $00
__gfx_circle_radius_lo:.byte $00
__gfx_circle_radius_hi:.byte $00
__gfx_saved_radius_lo:.byte $00
__gfx_saved_radius_hi:.byte $00
__gfx_circle_x_lo:    .byte $00
__gfx_circle_x_hi:    .byte $00
__gfx_circle_y_lo:    .byte $00
__gfx_circle_y_hi:    .byte $00
__gfx_circle_dec_lo:  .byte $00
__gfx_circle_dec_hi:  .byte $00

__gfx_tri_x1_lo:      .byte $00
__gfx_tri_x1_hi:      .byte $00
__gfx_tri_y1_lo:      .byte $00
__gfx_tri_y1_hi:      .byte $00
__gfx_tri_x2_lo:      .byte $00
__gfx_tri_x2_hi:      .byte $00
__gfx_tri_y2_lo:      .byte $00
__gfx_tri_y2_hi:      .byte $00
__gfx_tri_x3_lo:      .byte $00
__gfx_tri_x3_hi:      .byte $00
__gfx_tri_y3_lo:      .byte $00
__gfx_tri_y3_hi:      .byte $00

__gfx_edge_x_lo:      .byte $00
__gfx_edge_x_hi:      .byte $00
__gfx_edge_y_lo:      .byte $00
__gfx_edge_y_hi:      .byte $00
__gfx_edge_dx_lo:     .byte $00
__gfx_edge_dx_hi:     .byte $00
__gfx_edge_dy_lo:     .byte $00
__gfx_edge_dy_hi:     .byte $00
__gfx_edge_err_lo:    .byte $00
__gfx_edge_err_hi:    .byte $00
__gfx_edge_sx:        .byte $01
__gfx_edge_sy:        .byte $01
__gfx_edge_major:     .byte $00
__gfx_edge_target_x_lo:.byte $00
__gfx_edge_target_x_hi:.byte $00
__gfx_edge_start_y_lo: .byte $00
__gfx_edge_start_y_hi: .byte $00
__gfx_edge_target_y_lo:.byte $00
__gfx_edge_target_y_hi:.byte $00
__gfx_edge_b_x_lo:     .byte $00
__gfx_edge_b_x_hi:     .byte $00
__gfx_edge_b_target_x_lo:.byte $00
__gfx_edge_b_target_x_hi:.byte $00
__gfx_edge_b_start_y_lo:.byte $00
__gfx_edge_b_start_y_hi:.byte $00
__gfx_edge_b_target_y_lo:.byte $00
__gfx_edge_b_target_y_hi:.byte $00
__gfx_edge_b_dx_lo:    .byte $00
__gfx_edge_b_dx_hi:    .byte $00
__gfx_edge_b_dy_lo:    .byte $00
__gfx_edge_b_dy_hi:    .byte $00
__gfx_edge_b_err_lo:   .byte $00
__gfx_edge_b_err_hi:   .byte $00
__gfx_edge_b_sx:       .byte $01
__gfx_scan_y_lo:       .byte $00
__gfx_scan_y_hi:       .byte $00

__gfx_center_x_lo:    .byte $00
__gfx_center_x_hi:    .byte $00
__gfx_center_y_lo:    .byte $00
__gfx_center_y_hi:    .byte $00
__gfx_radius1_lo:     .byte $00
__gfx_radius1_hi:     .byte $00
__gfx_radius2_lo:     .byte $00
__gfx_radius2_hi:     .byte $00
__gfx_radius3_lo:     .byte $00
__gfx_radius3_hi:     .byte $00
__gfx_angle1_lo:      .byte $00
__gfx_angle1_hi:      .byte $00
__gfx_angle2_lo:      .byte $00
__gfx_angle2_hi:      .byte $00
__gfx_angle3_lo:      .byte $00
__gfx_angle3_hi:      .byte $00
__gfx_trig_angle_lo:  .byte $00
__gfx_trig_angle_hi:  .byte $00
__gfx_saved_angle_lo: .byte $00
__gfx_saved_angle_hi: .byte $00
__gfx_trig_value_lo:  .byte $00
__gfx_trig_value_hi:  .byte $00
__gfx_mul_radius_lo:  .byte $00
__gfx_mul_radius_hi:  .byte $00
__gfx_mul_value_lo:   .byte $00
__gfx_mul_value_hi:   .byte $00
__gfx_mul_count_lo:   .byte $00
__gfx_mul_count_hi:   .byte $00
__gfx_mul_sign:       .byte $00
__gfx_product_lo:     .byte $00
__gfx_product_mid:    .byte $00
__gfx_product_hi:     .byte $00
__gfx_scaled_lo:      .byte $00
__gfx_scaled_hi:      .byte $00
__gfx_vertex_x_lo:    .byte $00
__gfx_vertex_x_hi:    .byte $00
__gfx_vertex_y_lo:    .byte $00
__gfx_vertex_y_hi:    .byte $00
__gfx_quadrant:       .byte $00
__gfx_remainder:      .byte $00
__gfx_div_value:      .byte $00
__gfx_sine_index:     .byte $00

__gfx_flood_x_lo:     .byte $00
__gfx_flood_x_hi:     .byte $00
__gfx_flood_y:        .byte $00
__gfx_flood_source:   .byte $00
__gfx_flood_top:      .byte $00

__gfx_sine_table_lo:
    .byte $00,$16,$2C,$42,$58,$6C,$80,$93,$A5,$B5,$C4,$D2,$DE,$E8,$F1,$F7,$FC,$FF,$00
__gfx_sine_table_hi:
    .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$01

__gfx_masks:
    .byte $C0, $C0, $30, $30, $0C, $0C, $03, $03
__gfx_clear_masks:
    .byte $3F, $3F, $CF, $CF, $F3, $F3, $FC, $FC
__gfx_pair_shifts:
    .byte $06, $06, $04, $04, $02, $02, $00, $00
; Four groups of eight entries: bitmap bit patterns for colour codes 0..3.
__gfx_code_patterns:
    .byte $00,$00,$00,$00,$00,$00,$00,$00
    .byte $40,$40,$10,$10,$04,$04,$01,$01
    .byte $80,$80,$20,$20,$08,$08,$02,$02
    .byte $C0,$C0,$30,$30,$0C,$0C,$03,$03

__gfx_bitmap_y_lo:
    .byte $00, $01, $02, $03, $04, $05, $06, $07, $40, $41, $42, $43, $44, $45, $46, $47
    .byte $80, $81, $82, $83, $84, $85, $86, $87, $C0, $C1, $C2, $C3, $C4, $C5, $C6, $C7
    .byte $00, $01, $02, $03, $04, $05, $06, $07, $40, $41, $42, $43, $44, $45, $46, $47
    .byte $80, $81, $82, $83, $84, $85, $86, $87, $C0, $C1, $C2, $C3, $C4, $C5, $C6, $C7
    .byte $00, $01, $02, $03, $04, $05, $06, $07, $40, $41, $42, $43, $44, $45, $46, $47
    .byte $80, $81, $82, $83, $84, $85, $86, $87, $C0, $C1, $C2, $C3, $C4, $C5, $C6, $C7
    .byte $00, $01, $02, $03, $04, $05, $06, $07, $40, $41, $42, $43, $44, $45, $46, $47
    .byte $80, $81, $82, $83, $84, $85, $86, $87, $C0, $C1, $C2, $C3, $C4, $C5, $C6, $C7
    .byte $00, $01, $02, $03, $04, $05, $06, $07, $40, $41, $42, $43, $44, $45, $46, $47
    .byte $80, $81, $82, $83, $84, $85, $86, $87, $C0, $C1, $C2, $C3, $C4, $C5, $C6, $C7
    .byte $00, $01, $02, $03, $04, $05, $06, $07, $40, $41, $42, $43, $44, $45, $46, $47
    .byte $80, $81, $82, $83, $84, $85, $86, $87, $C0, $C1, $C2, $C3, $C4, $C5, $C6, $C7
    .byte $00, $01, $02, $03, $04, $05, $06, $07

__gfx_bitmap_y_hi:
    .byte $A0, $A0, $A0, $A0, $A0, $A0, $A0, $A0, $A1, $A1, $A1, $A1, $A1, $A1, $A1, $A1
    .byte $A2, $A2, $A2, $A2, $A2, $A2, $A2, $A2, $A3, $A3, $A3, $A3, $A3, $A3, $A3, $A3
    .byte $A5, $A5, $A5, $A5, $A5, $A5, $A5, $A5, $A6, $A6, $A6, $A6, $A6, $A6, $A6, $A6
    .byte $A7, $A7, $A7, $A7, $A7, $A7, $A7, $A7, $A8, $A8, $A8, $A8, $A8, $A8, $A8, $A8
    .byte $AA, $AA, $AA, $AA, $AA, $AA, $AA, $AA, $AB, $AB, $AB, $AB, $AB, $AB, $AB, $AB
    .byte $AC, $AC, $AC, $AC, $AC, $AC, $AC, $AC, $AD, $AD, $AD, $AD, $AD, $AD, $AD, $AD
    .byte $AF, $AF, $AF, $AF, $AF, $AF, $AF, $AF, $B0, $B0, $B0, $B0, $B0, $B0, $B0, $B0
    .byte $B1, $B1, $B1, $B1, $B1, $B1, $B1, $B1, $B2, $B2, $B2, $B2, $B2, $B2, $B2, $B2
    .byte $B4, $B4, $B4, $B4, $B4, $B4, $B4, $B4, $B5, $B5, $B5, $B5, $B5, $B5, $B5, $B5
    .byte $B6, $B6, $B6, $B6, $B6, $B6, $B6, $B6, $B7, $B7, $B7, $B7, $B7, $B7, $B7, $B7
    .byte $B9, $B9, $B9, $B9, $B9, $B9, $B9, $B9, $BA, $BA, $BA, $BA, $BA, $BA, $BA, $BA
    .byte $BB, $BB, $BB, $BB, $BB, $BB, $BB, $BB, $BC, $BC, $BC, $BC, $BC, $BC, $BC, $BC
    .byte $BE, $BE, $BE, $BE, $BE, $BE, $BE, $BE

__gfx_screen_y_lo:
    .byte $00, $00, $00, $00, $00, $00, $00, $00, $28, $28, $28, $28, $28, $28, $28, $28
    .byte $50, $50, $50, $50, $50, $50, $50, $50, $78, $78, $78, $78, $78, $78, $78, $78
    .byte $A0, $A0, $A0, $A0, $A0, $A0, $A0, $A0, $C8, $C8, $C8, $C8, $C8, $C8, $C8, $C8
    .byte $F0, $F0, $F0, $F0, $F0, $F0, $F0, $F0, $18, $18, $18, $18, $18, $18, $18, $18
    .byte $40, $40, $40, $40, $40, $40, $40, $40, $68, $68, $68, $68, $68, $68, $68, $68
    .byte $90, $90, $90, $90, $90, $90, $90, $90, $B8, $B8, $B8, $B8, $B8, $B8, $B8, $B8
    .byte $E0, $E0, $E0, $E0, $E0, $E0, $E0, $E0, $08, $08, $08, $08, $08, $08, $08, $08
    .byte $30, $30, $30, $30, $30, $30, $30, $30, $58, $58, $58, $58, $58, $58, $58, $58
    .byte $80, $80, $80, $80, $80, $80, $80, $80, $A8, $A8, $A8, $A8, $A8, $A8, $A8, $A8
    .byte $D0, $D0, $D0, $D0, $D0, $D0, $D0, $D0, $F8, $F8, $F8, $F8, $F8, $F8, $F8, $F8
    .byte $20, $20, $20, $20, $20, $20, $20, $20, $48, $48, $48, $48, $48, $48, $48, $48
    .byte $70, $70, $70, $70, $70, $70, $70, $70, $98, $98, $98, $98, $98, $98, $98, $98
    .byte $C0, $C0, $C0, $C0, $C0, $C0, $C0, $C0

__gfx_screen_y_hi:
    .byte $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C
    .byte $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C
    .byte $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C
    .byte $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8C, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D
    .byte $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D
    .byte $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D
    .byte $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8D, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E
    .byte $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E
    .byte $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E
    .byte $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E, $8E
    .byte $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F
    .byte $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F
    .byte $8F, $8F, $8F, $8F, $8F, $8F, $8F, $8F
end
