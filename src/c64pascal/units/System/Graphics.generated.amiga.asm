; System.Graphics Amiga 500 implementation
; Stack ABI: value parameters are pushed left-to-right as words; result D0.W
section code,code
xdef __pas_System_Graphics_SetTextColor
xdef __pas_System_Graphics_ClearScreen
xdef __pas_System_Graphics_InitGraphics
xdef __pas_System_Graphics_DoneGraphics
xdef __pas_System_Graphics_SetPixel
xdef __pas_System_Graphics_GetPixel
xdef __pas_System_Graphics_DrawLine
xdef __pas_System_Graphics_DrawRect
xdef __pas_System_Graphics_FillRect
xdef __pas_System_Graphics_DrawCircle
xdef __pas_System_Graphics_FillCircle
xdef __pas_System_Graphics_FloodFill
xdef __pas_System_Graphics_DrawTriangle
xdef __pas_System_Graphics_FillTriangle
xdef __pas_System_Graphics_DrawTriangleAngles
xdef SetTextColor
xdef ClearScreen
xdef InitGraphics
xdef DoneGraphics
xdef SetPixel
xdef GetPixel
xdef DrawLine
xdef DrawRect
xdef FillRect
xdef DrawCircle
xdef FillCircle
xdef FloodFill
xdef DrawTriangle
xdef FillTriangle
xdef DrawTriangleAngles

__gfx_wait_safe_line:
    move.l #$00DFF000,a0
__gfx_wait_safe_line_loop:
    move.w $0006(a0),d0
    andi.w #$FF00,d0
    cmpi.w #$F500,d0
    bcs __gfx_wait_safe_line_loop
    rts

; Copper list at $00010000. It reloads all bitplane pointers every frame.
__gfx_install_graphics_copper:
    move.l #$00010000,a1
    move.l #$008E2C81,(a1)+
    move.l #$0090F4C1,(a1)+
    move.l #$00920038,(a1)+
    move.l #$009400D0,(a1)+
    move.l #$01004200,(a1)+
    move.l #$01020000,(a1)+
    move.l #$01040000,(a1)+
    move.l #$01080000,(a1)+
    move.l #$010A0000,(a1)+
    move.l #$00E00002,(a1)+
    move.l #$00E20000,(a1)+
    move.l #$00E40002,(a1)+
    move.l #$00E62000,(a1)+
    move.l #$00E80002,(a1)+
    move.l #$00EA4000,(a1)+
    move.l #$00EC0002,(a1)+
    move.l #$00EE6000,(a1)+
    move.l #$01800000,(a1)+
    move.l #$01820FFF,(a1)+
    move.l #$01840F00,(a1)+
    move.l #$018600FF,(a1)+
    move.l #$01880F0F,(a1)+
    move.l #$018A00F0,(a1)+
    move.l #$018C000F,(a1)+
    move.l #$018E0FF0,(a1)+
    move.l #$01900F80,(a1)+
    move.l #$01920840,(a1)+
    move.l #$01940F66,(a1)+
    move.l #$01960444,(a1)+
    move.l #$01980888,(a1)+
    move.l #$019A08F8,(a1)+
    move.l #$019C088F,(a1)+
    move.l #$019E0CCC,(a1)+
    move.l #$FFFFFFFE,(a1)+
    rts

; Text copper layout intentionally matches the compiler runtime.
; COLOR00 value is at $0001002E, COLOR01 value at $00010032.
__gfx_install_text_copper:
    move.l #$00010000,a1
    move.l #$008E2C81,(a1)+
    move.l #$0090F4C1,(a1)+
    move.l #$00920038,(a1)+
    move.l #$009400D0,(a1)+
    move.l #$01001200,(a1)+
    move.l #$01020000,(a1)+
    move.l #$01040000,(a1)+
    move.l #$01080000,(a1)+
    move.l #$010A0000,(a1)+
    move.l #$00E00001,(a1)+
    move.l #$00E28000,(a1)+
    move.w #$0180,(a1)+
    lea __gfx_text_background(pc),a0
    move.w (a0),(a1)+
    move.w #$0182,(a1)+
    lea __gfx_text_foreground(pc),a0
    move.w (a0),(a1)+
    move.l #$FFFFFFFE,(a1)+
    rts

SetTextColor:
__pas_System_Graphics_SetTextColor:
    move.w 6(sp),d0
    andi.w #$000F,d0
    add.w d0,d0
    lea __gfx_palette(pc),a1
    adda.w d0,a1
    move.w (a1),d2
    move.w 4(sp),d0
    andi.w #$000F,d0
    add.w d0,d0
    lea __gfx_palette(pc),a1
    adda.w d0,a1
    move.w (a1),d1
    lea __gfx_text_foreground(pc),a1
    move.w d2,(a1)
    lea __gfx_text_background(pc),a1
    move.w d1,(a1)
    lea __gfx_graphics_active(pc),a1
    tst.b (a1)
    bne __gfx_set_text_color_done
    move.l #$00DFF000,a0
    move.w d1,$0180(a0)
    move.w d2,$0182(a0)
    move.l #$0001002E,a0
    move.w d1,(a0)
    move.l #$00010032,a0
    move.w d2,(a0)
__gfx_set_text_color_done:
    rts

__gfx_clear_text_plane:
    move.l #$00018000,a0
    move.w #$07D0,d0
__gfx_clear_text_loop:
    clr.l (a0)+
    subq.w #1,d0
    bne __gfx_clear_text_loop
    rts

__gfx_clear_graphics_planes:
    move.l #$00020000,a0
    move.w #$07D0,d0
__gfx_clear_plane_0_loop:
    clr.l (a0)+
    subq.w #1,d0
    bne __gfx_clear_plane_0_loop
    move.l #$00022000,a0
    move.w #$07D0,d0
__gfx_clear_plane_1_loop:
    clr.l (a0)+
    subq.w #1,d0
    bne __gfx_clear_plane_1_loop
    move.l #$00024000,a0
    move.w #$07D0,d0
__gfx_clear_plane_2_loop:
    clr.l (a0)+
    subq.w #1,d0
    bne __gfx_clear_plane_2_loop
    move.l #$00026000,a0
    move.w #$07D0,d0
__gfx_clear_plane_3_loop:
    clr.l (a0)+
    subq.w #1,d0
    bne __gfx_clear_plane_3_loop
    rts

ClearScreen:
__pas_System_Graphics_ClearScreen:
    lea __gfx_graphics_active(pc),a0
    tst.b (a0)
    beq __gfx_clear_current_text
    bsr __gfx_clear_graphics_planes
    rts
__gfx_clear_current_text:
    bsr __gfx_clear_text_plane
    rts

InitGraphics:
__pas_System_Graphics_InitGraphics:
    bsr __gfx_wait_safe_line
    move.l #$00DFF000,a0
    move.w #$7FFF,$009A(a0)
    move.w #$7FFF,$0096(a0)
    bsr __gfx_clear_graphics_planes
    bsr __gfx_install_graphics_copper
    move.l #$00DFF000,a0
    move.l #$00010000,d0
    move.l d0,$0080(a0)
    move.w #$0000,$0088(a0)
    lea __gfx_graphics_active(pc),a1
    move.b #$01,(a1)
    move.w #$8380,$0096(a0)
    rts

DoneGraphics:
__pas_System_Graphics_DoneGraphics:
    lea __gfx_text_mode(pc),a0
    move.b 5(sp),(a0)
    bsr __gfx_wait_safe_line
    move.l #$00DFF000,a0
    move.w #$7FFF,$0096(a0)
    bsr __gfx_clear_text_plane
    bsr __gfx_install_text_copper
    move.l #$00DFF000,a0
    move.l #$00010000,d0
    move.l d0,$0080(a0)
    move.w #$0000,$0088(a0)
    lea __gfx_graphics_active(pc),a1
    clr.b (a1)
    move.w #$8380,$0096(a0)
    rts

SetPixel:
__pas_System_Graphics_SetPixel:
    move.w 8(sp),d0
    move.w 6(sp),d1
    move.w 4(sp),d2
    bra __gfx_setpixel_fast

; Schneller interner Pixelpfad.
; Eingang: D0.W=X, D1.W=Y, D2.W=Farbe. Register duerfen zerstoert werden.
__gfx_setpixel_fast:
    tst.w d0
    bmi __gfx_setpixel_fast_done
    cmpi.w #$0140,d0
    bge __gfx_setpixel_fast_done
    tst.w d1
    bmi __gfx_setpixel_fast_done
    cmpi.w #$00C8,d1
    bge __gfx_setpixel_fast_done
    move.w d1,d3
    mulu.w #$0028,d3
    move.w d0,d4
    lsr.w #3,d4
    add.w d4,d3
    andi.w #$0007,d0
    lea __gfx_masks(pc),a1
    adda.w d0,a1
    moveq #0,d4
    move.b (a1),d4
    andi.w #$000F,d2

    move.l #$00020000,a0
    adda.w d3,a0
    moveq #0,d5
    move.b (a0),d5
    move.w d2,d6
    andi.w #$0001,d6
    beq __gfx_spf_clear_0
    or.b d4,d5
    bra __gfx_spf_store_0
__gfx_spf_clear_0:
    move.w d4,d6
    eori.b #$FF,d6
    and.b d6,d5
__gfx_spf_store_0:
    move.b d5,(a0)

    move.l #$00022000,a0
    adda.w d3,a0
    moveq #0,d5
    move.b (a0),d5
    move.w d2,d6
    andi.w #$0002,d6
    beq __gfx_spf_clear_1
    or.b d4,d5
    bra __gfx_spf_store_1
__gfx_spf_clear_1:
    move.w d4,d6
    eori.b #$FF,d6
    and.b d6,d5
__gfx_spf_store_1:
    move.b d5,(a0)

    move.l #$00024000,a0
    adda.w d3,a0
    moveq #0,d5
    move.b (a0),d5
    move.w d2,d6
    andi.w #$0004,d6
    beq __gfx_spf_clear_2
    or.b d4,d5
    bra __gfx_spf_store_2
__gfx_spf_clear_2:
    move.w d4,d6
    eori.b #$FF,d6
    and.b d6,d5
__gfx_spf_store_2:
    move.b d5,(a0)

    move.l #$00026000,a0
    adda.w d3,a0
    moveq #0,d5
    move.b (a0),d5
    move.w d2,d6
    andi.w #$0008,d6
    beq __gfx_spf_clear_3
    or.b d4,d5
    bra __gfx_spf_store_3
__gfx_spf_clear_3:
    move.w d4,d6
    eori.b #$FF,d6
    and.b d6,d5
__gfx_spf_store_3:
    move.b d5,(a0)
__gfx_setpixel_fast_done:
    rts

GetPixel:
__pas_System_Graphics_GetPixel:
    move.w 6(sp),d0
    move.w 4(sp),d1
    bra __gfx_getpixel_fast

; Schneller interner Lesepfad.
; Eingang: D0.W=X, D1.W=Y. Ergebnis: D0.W=Farbe.
__gfx_getpixel_fast:
    moveq #0,d5
    tst.w d0
    bmi __gfx_getpixel_fast_done
    cmpi.w #$0140,d0
    bge __gfx_getpixel_fast_done
    tst.w d1
    bmi __gfx_getpixel_fast_done
    cmpi.w #$00C8,d1
    bge __gfx_getpixel_fast_done
    move.w d1,d2
    mulu.w #$0028,d2
    move.w d0,d3
    lsr.w #3,d3
    add.w d3,d2
    andi.w #$0007,d0
    lea __gfx_masks(pc),a1
    adda.w d0,a1
    moveq #0,d3
    move.b (a1),d3

    move.l #$00020000,a0
    adda.w d2,a0
    moveq #0,d0
    move.b (a0),d0
    and.b d3,d0
    beq __gfx_gpf_next_0
    ori.w #$0001,d5
__gfx_gpf_next_0:
    move.l #$00022000,a0
    adda.w d2,a0
    moveq #0,d0
    move.b (a0),d0
    and.b d3,d0
    beq __gfx_gpf_next_1
    ori.w #$0002,d5
__gfx_gpf_next_1:
    move.l #$00024000,a0
    adda.w d2,a0
    moveq #0,d0
    move.b (a0),d0
    and.b d3,d0
    beq __gfx_gpf_next_2
    ori.w #$0004,d5
__gfx_gpf_next_2:
    move.l #$00026000,a0
    adda.w d2,a0
    moveq #0,d0
    move.b (a0),d0
    and.b d3,d0
    beq __gfx_gpf_next_3
    ori.w #$0008,d5
__gfx_gpf_next_3:
__gfx_getpixel_fast_done:
    move.w d5,d0
    rts

; Interne Primitive-Aufrufe vermeiden Parameter-Pushes pro Pixel.
__gfx_call_setpixel:
    bra __gfx_setpixel_fast
__gfx_call_getpixel:
    bra __gfx_getpixel_fast

; Schnelle horizontale Linie ohne erneute Multiplikation je Pixel.
; Eingang: D0.W=X1, D1.W=Y, D2.W=X2, D3.W=Farbe.
__gfx_hline_fast:
    tst.w d1
    bmi __gfx_hline_done
    cmpi.w #$00C8,d1
    bge __gfx_hline_done
    cmp.w d2,d0
    ble __gfx_hline_ordered
    move.w d0,d6
    move.w d2,d0
    move.w d6,d2
__gfx_hline_ordered:
    tst.w d2
    bmi __gfx_hline_done
    cmpi.w #$0140,d0
    bge __gfx_hline_done
    tst.w d0
    bpl __gfx_hline_left_ok
    moveq #0,d0
__gfx_hline_left_ok:
    cmpi.w #$013F,d2
    ble __gfx_hline_right_ok
    move.w #$013F,d2
__gfx_hline_right_ok:
    move.w d2,d5
    sub.w d0,d5
    addq.w #1,d5
    move.w d1,d6
    mulu.w #$0028,d6
    move.w d0,d1
    lsr.w #3,d1
    add.w d1,d6
    move.w d0,d1
    andi.w #$0007,d1
    lea __gfx_masks(pc),a4
    adda.w d1,a4
    moveq #0,d4
    move.b (a4),d4
    andi.w #$000F,d3
    move.w d3,d7
    move.l #$00020000,a0
    adda.w d6,a0
    move.l #$00022000,a1
    adda.w d6,a1
    move.l #$00024000,a2
    adda.w d6,a2
    move.l #$00026000,a3
    adda.w d6,a3
__gfx_hline_loop:
    moveq #0,d0
    move.b (a0),d0
    move.w d7,d2
    andi.w #$0001,d2
    beq __gfx_hline_clear_0
    or.b d4,d0
    bra __gfx_hline_store_0
__gfx_hline_clear_0:
    move.w d4,d6
    eori.b #$FF,d6
    and.b d6,d0
__gfx_hline_store_0:
    move.b d0,(a0)

    moveq #0,d0
    move.b (a1),d0
    move.w d7,d2
    andi.w #$0002,d2
    beq __gfx_hline_clear_1
    or.b d4,d0
    bra __gfx_hline_store_1
__gfx_hline_clear_1:
    move.w d4,d6
    eori.b #$FF,d6
    and.b d6,d0
__gfx_hline_store_1:
    move.b d0,(a1)

    moveq #0,d0
    move.b (a2),d0
    move.w d7,d2
    andi.w #$0004,d2
    beq __gfx_hline_clear_2
    or.b d4,d0
    bra __gfx_hline_store_2
__gfx_hline_clear_2:
    move.w d4,d6
    eori.b #$FF,d6
    and.b d6,d0
__gfx_hline_store_2:
    move.b d0,(a2)

    moveq #0,d0
    move.b (a3),d0
    move.w d7,d2
    andi.w #$0008,d2
    beq __gfx_hline_clear_3
    or.b d4,d0
    bra __gfx_hline_store_3
__gfx_hline_clear_3:
    move.w d4,d6
    eori.b #$FF,d6
    and.b d6,d0
__gfx_hline_store_3:
    move.b d0,(a3)

    subq.w #1,d5
    beq __gfx_hline_done
    lsr.w #1,d4
    bne __gfx_hline_loop
    move.w #$0080,d4
    adda.w #1,a0
    adda.w #1,a1
    adda.w #1,a2
    adda.w #1,a3
    bra __gfx_hline_loop
__gfx_hline_done:
    rts

__gfx_call_drawline:
    move.w d0,-(sp)
    move.w d1,-(sp)
    move.w d2,-(sp)
    move.w d3,-(sp)
    move.w d4,-(sp)
    bsr __pas_System_Graphics_DrawLine
    adda.w #$000A,sp
    rts
__gfx_call_drawrect:
    move.w d0,-(sp)
    move.w d1,-(sp)
    move.w d2,-(sp)
    move.w d3,-(sp)
    move.w d4,-(sp)
    bsr __pas_System_Graphics_DrawRect
    adda.w #$000A,sp
    rts
__gfx_call_drawcircle:
    move.w d0,-(sp)
    move.w d1,-(sp)
    move.w d2,-(sp)
    move.w d3,-(sp)
    bsr __pas_System_Graphics_DrawCircle
    adda.w #$0008,sp
    rts
__gfx_call_flood:
    move.w d0,-(sp)
    move.w d1,-(sp)
    move.w d2,-(sp)
    bsr __pas_System_Graphics_FloodFill
    adda.w #$0006,sp
    rts

DrawLine:
__pas_System_Graphics_DrawLine:
    move.w 12(sp),d0
    lea __gfx_line_x(pc),a0
    move.w d0,(a0)
    move.w 10(sp),d0
    lea __gfx_line_y(pc),a0
    move.w d0,(a0)
    move.w 8(sp),d0
    lea __gfx_line_x2(pc),a0
    move.w d0,(a0)
    move.w 6(sp),d0
    lea __gfx_line_y2(pc),a0
    move.w d0,(a0)
    move.w 4(sp),d0
    lea __gfx_line_color(pc),a0
    move.w d0,(a0)
    lea __gfx_line_x2(pc),a0
    move.w (a0),d0
    lea __gfx_line_x(pc),a0
    move.w (a0),d1
    sub.w d1,d0
    bpl __gfx_line_dx_ok
    neg.w d0
__gfx_line_dx_ok:
    lea __gfx_line_dx(pc),a0
    move.w d0,(a0)
    lea __gfx_line_x(pc),a0
    move.w (a0),d0
    lea __gfx_line_x2(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    blt __gfx_line_sx_pos
    move.w #$FFFF,d0
    bra __gfx_line_sx_done
__gfx_line_sx_pos:
    moveq #1,d0
__gfx_line_sx_done:
    lea __gfx_line_sx(pc),a0
    move.w d0,(a0)
    lea __gfx_line_y2(pc),a0
    move.w (a0),d0
    lea __gfx_line_y(pc),a0
    move.w (a0),d1
    sub.w d1,d0
    bpl __gfx_line_dy_abs
    neg.w d0
__gfx_line_dy_abs:
    neg.w d0
    lea __gfx_line_dy(pc),a0
    move.w d0,(a0)
    lea __gfx_line_y(pc),a0
    move.w (a0),d0
    lea __gfx_line_y2(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    blt __gfx_line_sy_pos
    move.w #$FFFF,d0
    bra __gfx_line_sy_done
__gfx_line_sy_pos:
    moveq #1,d0
__gfx_line_sy_done:
    lea __gfx_line_sy(pc),a0
    move.w d0,(a0)
    lea __gfx_line_dx(pc),a0
    move.w (a0),d0
    lea __gfx_line_dy(pc),a0
    move.w (a0),d1
    add.w d1,d0
    lea __gfx_line_err(pc),a0
    move.w d0,(a0)
__gfx_line_loop:
    lea __gfx_line_x(pc),a0
    move.w (a0),d0
    lea __gfx_line_y(pc),a0
    move.w (a0),d1
    lea __gfx_line_color(pc),a0
    move.w (a0),d2
    bsr __gfx_call_setpixel
    lea __gfx_line_x(pc),a0
    move.w (a0),d0
    lea __gfx_line_x2(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    bne __gfx_line_step
    lea __gfx_line_y(pc),a0
    move.w (a0),d0
    lea __gfx_line_y2(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    beq __gfx_line_return
__gfx_line_step:
    lea __gfx_line_err(pc),a0
    move.w (a0),d0
    add.w d0,d0
    lea __gfx_line_e2(pc),a0
    move.w d0,(a0)
    lea __gfx_line_dy(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    blt __gfx_line_no_x
    lea __gfx_line_err(pc),a0
    move.w (a0),d0
    lea __gfx_line_dy(pc),a0
    move.w (a0),d1
    add.w d1,d0
    lea __gfx_line_err(pc),a0
    move.w d0,(a0)
    lea __gfx_line_x(pc),a0
    move.w (a0),d0
    lea __gfx_line_sx(pc),a0
    move.w (a0),d1
    add.w d1,d0
    lea __gfx_line_x(pc),a0
    move.w d0,(a0)
__gfx_line_no_x:
    lea __gfx_line_e2(pc),a0
    move.w (a0),d0
    lea __gfx_line_dx(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    bgt __gfx_line_no_y
    lea __gfx_line_err(pc),a0
    move.w (a0),d0
    lea __gfx_line_dx(pc),a0
    move.w (a0),d1
    add.w d1,d0
    lea __gfx_line_err(pc),a0
    move.w d0,(a0)
    lea __gfx_line_y(pc),a0
    move.w (a0),d0
    lea __gfx_line_sy(pc),a0
    move.w (a0),d1
    add.w d1,d0
    lea __gfx_line_y(pc),a0
    move.w d0,(a0)
__gfx_line_no_y:
    bra __gfx_line_loop
__gfx_line_return:
    rts

DrawRect:
__pas_System_Graphics_DrawRect:
    move.w 12(sp),d0
    lea __gfx_rect_x1(pc),a0
    move.w d0,(a0)
    move.w 10(sp),d0
    lea __gfx_rect_y1(pc),a0
    move.w d0,(a0)
    move.w 8(sp),d0
    lea __gfx_rect_x2(pc),a0
    move.w d0,(a0)
    move.w 6(sp),d0
    lea __gfx_rect_y2(pc),a0
    move.w d0,(a0)
    move.w 4(sp),d0
    lea __gfx_rect_color(pc),a0
    move.w d0,(a0)

    ; obere horizontale Kante
    lea __gfx_rect_x1(pc),a0
    move.w (a0),d0
    lea __gfx_rect_y1(pc),a0
    move.w (a0),d1
    lea __gfx_rect_x2(pc),a0
    move.w (a0),d2
    lea __gfx_rect_color(pc),a0
    move.w (a0),d3
    bsr __gfx_hline_fast

    ; untere horizontale Kante
    lea __gfx_rect_x1(pc),a0
    move.w (a0),d0
    lea __gfx_rect_y2(pc),a0
    move.w (a0),d1
    lea __gfx_rect_x2(pc),a0
    move.w (a0),d2
    lea __gfx_rect_color(pc),a0
    move.w (a0),d3
    bsr __gfx_hline_fast

    ; linke vertikale Kante
    lea __gfx_rect_x1(pc),a0
    move.w (a0),d0
    lea __gfx_rect_y1(pc),a0
    move.w (a0),d1
    lea __gfx_rect_x1(pc),a0
    move.w (a0),d2
    lea __gfx_rect_y2(pc),a0
    move.w (a0),d3
    lea __gfx_rect_color(pc),a0
    move.w (a0),d4
    bsr __gfx_call_drawline

    ; rechte vertikale Kante
    lea __gfx_rect_x2(pc),a0
    move.w (a0),d0
    lea __gfx_rect_y1(pc),a0
    move.w (a0),d1
    lea __gfx_rect_x2(pc),a0
    move.w (a0),d2
    lea __gfx_rect_y2(pc),a0
    move.w (a0),d3
    lea __gfx_rect_color(pc),a0
    move.w (a0),d4
    bsr __gfx_call_drawline
    rts

FillRect:
__pas_System_Graphics_FillRect:
    move.w 16(sp),d0
    lea __gfx_fr_x1(pc),a0
    move.w d0,(a0)
    move.w 14(sp),d0
    lea __gfx_fr_y1(pc),a0
    move.w d0,(a0)
    move.w 12(sp),d0
    lea __gfx_fr_x2(pc),a0
    move.w d0,(a0)
    move.w 10(sp),d0
    lea __gfx_fr_y2(pc),a0
    move.w d0,(a0)
    move.w 8(sp),d0
    lea __gfx_fr_fill(pc),a0
    move.w d0,(a0)
    move.w 6(sp),d0
    lea __gfx_fr_border(pc),a0
    move.w d0,(a0)
    move.w 4(sp),d0
    lea __gfx_fr_width(pc),a0
    move.w d0,(a0)

    ; Koordinaten normalisieren.
    lea __gfx_fr_x1(pc),a0
    move.w (a0),d0
    lea __gfx_fr_x2(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    ble __gfx_fr_fast_x_ok
    lea __gfx_fr_x1(pc),a0
    move.w d1,(a0)
    lea __gfx_fr_x2(pc),a0
    move.w d0,(a0)
__gfx_fr_fast_x_ok:
    lea __gfx_fr_y1(pc),a0
    move.w (a0),d0
    lea __gfx_fr_y2(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    ble __gfx_fr_fast_y_ok
    lea __gfx_fr_y1(pc),a0
    move.w d1,(a0)
    lea __gfx_fr_y2(pc),a0
    move.w d0,(a0)
__gfx_fr_fast_y_ok:

    ; Fruehes Clipping verhindert Schleifen ausserhalb des Bildschirms.
    lea __gfx_fr_x2(pc),a0
    move.w (a0),d0
    tst.w d0
    bmi __gfx_fr_fast_done
    lea __gfx_fr_x1(pc),a0
    move.w (a0),d0
    cmpi.w #$0140,d0
    bge __gfx_fr_fast_done
    lea __gfx_fr_y2(pc),a0
    move.w (a0),d0
    tst.w d0
    bmi __gfx_fr_fast_done
    lea __gfx_fr_y1(pc),a0
    move.w (a0),d0
    cmpi.w #$00C8,d0
    bge __gfx_fr_fast_done

    lea __gfx_fr_y1(pc),a0
    move.w (a0),d0
    bpl __gfx_fr_fast_y1_ok
    moveq #0,d0
    move.w d0,(a0)
__gfx_fr_fast_y1_ok:
    lea __gfx_fr_y2(pc),a0
    move.w (a0),d0
    cmpi.w #$00C7,d0
    ble __gfx_fr_fast_y2_ok
    move.w #$00C7,d0
    move.w d0,(a0)
__gfx_fr_fast_y2_ok:

    lea __gfx_fr_y1(pc),a0
    move.w (a0),d0
    lea __gfx_fr_y(pc),a0
    move.w d0,(a0)
__gfx_fr_fast_y_loop:
    lea __gfx_fr_x1(pc),a0
    move.w (a0),d0
    lea __gfx_fr_y(pc),a0
    move.w (a0),d1
    lea __gfx_fr_x2(pc),a0
    move.w (a0),d2
    lea __gfx_fr_fill(pc),a0
    move.w (a0),d3
    bsr __gfx_hline_fast
    lea __gfx_fr_y(pc),a0
    move.w (a0),d0
    addq.w #1,d0
    move.w d0,(a0)
    lea __gfx_fr_y2(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    ble __gfx_fr_fast_y_loop

    moveq #0,d0
    lea __gfx_fr_i(pc),a0
    move.w d0,(a0)
__gfx_fr_fast_border_loop:
    lea __gfx_fr_i(pc),a0
    move.w (a0),d5
    lea __gfx_fr_width(pc),a0
    move.w (a0),d6
    cmp.w d6,d5
    bge __gfx_fr_fast_done
    lea __gfx_fr_x1(pc),a0
    move.w (a0),d0
    add.w d5,d0
    lea __gfx_fr_y1(pc),a0
    move.w (a0),d1
    add.w d5,d1
    lea __gfx_fr_x2(pc),a0
    move.w (a0),d2
    sub.w d5,d2
    lea __gfx_fr_y2(pc),a0
    move.w (a0),d3
    sub.w d5,d3
    lea __gfx_fr_border(pc),a0
    move.w (a0),d4
    bsr __gfx_call_drawrect
    lea __gfx_fr_i(pc),a0
    move.w (a0),d0
    addq.w #1,d0
    move.w d0,(a0)
    bra __gfx_fr_fast_border_loop
__gfx_fr_fast_done:
    rts

__gfx_circle_plot8:
    lea __gfx_circle_cx(pc),a0
    move.w (a0),d0
    lea __gfx_circle_x(pc),a0
    move.w (a0),d3
    add.w d3,d0
    lea __gfx_circle_cy(pc),a0
    move.w (a0),d1
    lea __gfx_circle_y(pc),a0
    move.w (a0),d3
    add.w d3,d1
    lea __gfx_circle_color(pc),a0
    move.w (a0),d2
    bsr __gfx_call_setpixel
    lea __gfx_circle_cx(pc),a0
    move.w (a0),d0
    lea __gfx_circle_x(pc),a0
    move.w (a0),d3
    sub.w d3,d0
    lea __gfx_circle_cy(pc),a0
    move.w (a0),d1
    lea __gfx_circle_y(pc),a0
    move.w (a0),d3
    add.w d3,d1
    lea __gfx_circle_color(pc),a0
    move.w (a0),d2
    bsr __gfx_call_setpixel
    lea __gfx_circle_cx(pc),a0
    move.w (a0),d0
    lea __gfx_circle_x(pc),a0
    move.w (a0),d3
    add.w d3,d0
    lea __gfx_circle_cy(pc),a0
    move.w (a0),d1
    lea __gfx_circle_y(pc),a0
    move.w (a0),d3
    sub.w d3,d1
    lea __gfx_circle_color(pc),a0
    move.w (a0),d2
    bsr __gfx_call_setpixel
    lea __gfx_circle_cx(pc),a0
    move.w (a0),d0
    lea __gfx_circle_x(pc),a0
    move.w (a0),d3
    sub.w d3,d0
    lea __gfx_circle_cy(pc),a0
    move.w (a0),d1
    lea __gfx_circle_y(pc),a0
    move.w (a0),d3
    sub.w d3,d1
    lea __gfx_circle_color(pc),a0
    move.w (a0),d2
    bsr __gfx_call_setpixel
    lea __gfx_circle_cx(pc),a0
    move.w (a0),d0
    lea __gfx_circle_y(pc),a0
    move.w (a0),d3
    add.w d3,d0
    lea __gfx_circle_cy(pc),a0
    move.w (a0),d1
    lea __gfx_circle_x(pc),a0
    move.w (a0),d3
    add.w d3,d1
    lea __gfx_circle_color(pc),a0
    move.w (a0),d2
    bsr __gfx_call_setpixel
    lea __gfx_circle_cx(pc),a0
    move.w (a0),d0
    lea __gfx_circle_y(pc),a0
    move.w (a0),d3
    sub.w d3,d0
    lea __gfx_circle_cy(pc),a0
    move.w (a0),d1
    lea __gfx_circle_x(pc),a0
    move.w (a0),d3
    add.w d3,d1
    lea __gfx_circle_color(pc),a0
    move.w (a0),d2
    bsr __gfx_call_setpixel
    lea __gfx_circle_cx(pc),a0
    move.w (a0),d0
    lea __gfx_circle_y(pc),a0
    move.w (a0),d3
    add.w d3,d0
    lea __gfx_circle_cy(pc),a0
    move.w (a0),d1
    lea __gfx_circle_x(pc),a0
    move.w (a0),d3
    sub.w d3,d1
    lea __gfx_circle_color(pc),a0
    move.w (a0),d2
    bsr __gfx_call_setpixel
    lea __gfx_circle_cx(pc),a0
    move.w (a0),d0
    lea __gfx_circle_y(pc),a0
    move.w (a0),d3
    sub.w d3,d0
    lea __gfx_circle_cy(pc),a0
    move.w (a0),d1
    lea __gfx_circle_x(pc),a0
    move.w (a0),d3
    sub.w d3,d1
    lea __gfx_circle_color(pc),a0
    move.w (a0),d2
    bsr __gfx_call_setpixel
    rts
DrawCircle:
__pas_System_Graphics_DrawCircle:
    move.w 10(sp),d0
    lea __gfx_circle_cx(pc),a0
    move.w d0,(a0)
    move.w 8(sp),d0
    lea __gfx_circle_cy(pc),a0
    move.w d0,(a0)
    move.w 6(sp),d0
    lea __gfx_circle_radius(pc),a0
    move.w d0,(a0)
    move.w 4(sp),d0
    lea __gfx_circle_color(pc),a0
    move.w d0,(a0)
    lea __gfx_circle_radius(pc),a0
    move.w (a0),d0
    bmi __gfx_circle_done
    lea __gfx_circle_x(pc),a0
    move.w d0,(a0)
    moveq #0,d1
    lea __gfx_circle_y(pc),a0
    move.w d1,(a0)
    moveq #1,d1
    sub.w d0,d1
    lea __gfx_circle_dec(pc),a0
    move.w d1,(a0)
__gfx_circle_loop:
    lea __gfx_circle_x(pc),a0
    move.w (a0),d0
    lea __gfx_circle_y(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    blt __gfx_circle_done
    bsr __gfx_circle_plot8
    lea __gfx_circle_y(pc),a0
    move.w (a0),d1
    addq.w #1,d1
    lea __gfx_circle_y(pc),a0
    move.w d1,(a0)
    lea __gfx_circle_dec(pc),a0
    move.w (a0),d0
    bge __gfx_circle_dec_ge
    add.w d1,d1
    addq.w #1,d1
    add.w d1,d0
    lea __gfx_circle_dec(pc),a0
    move.w d0,(a0)
    bra __gfx_circle_loop
__gfx_circle_dec_ge:
    lea __gfx_circle_x(pc),a0
    move.w (a0),d2
    subq.w #1,d2
    lea __gfx_circle_x(pc),a0
    move.w d2,(a0)
    lea __gfx_circle_y(pc),a0
    move.w (a0),d1
    sub.w d2,d1
    add.w d1,d1
    addq.w #1,d1
    lea __gfx_circle_dec(pc),a0
    move.w (a0),d0
    add.w d1,d0
    lea __gfx_circle_dec(pc),a0
    move.w d0,(a0)
    bra __gfx_circle_loop
__gfx_circle_done:
    rts

FillCircle:
__pas_System_Graphics_FillCircle:
    move.w 14(sp),d0
    lea __gfx_fc_cx(pc),a0
    move.w d0,(a0)
    move.w 12(sp),d0
    lea __gfx_fc_cy(pc),a0
    move.w d0,(a0)
    move.w 10(sp),d0
    lea __gfx_fc_radius(pc),a0
    move.w d0,(a0)
    move.w 8(sp),d0
    lea __gfx_fc_fill(pc),a0
    move.w d0,(a0)
    move.w 6(sp),d0
    lea __gfx_fc_border(pc),a0
    move.w d0,(a0)
    move.w 4(sp),d0
    lea __gfx_fc_width(pc),a0
    move.w d0,(a0)

    lea __gfx_fc_radius(pc),a0
    move.w (a0),d0
    bmi __gfx_fc_fast_done
    lea __gfx_circle_x(pc),a0
    move.w d0,(a0)
    moveq #0,d1
    lea __gfx_circle_y(pc),a0
    move.w d1,(a0)
    moveq #1,d1
    sub.w d0,d1
    lea __gfx_circle_dec(pc),a0
    move.w d1,(a0)

__gfx_fc_fast_fill_loop:
    lea __gfx_circle_x(pc),a0
    move.w (a0),d6
    lea __gfx_circle_y(pc),a0
    move.w (a0),d7
    cmp.w d7,d6
    blt __gfx_fc_fast_border_start

    ; cx-x .. cx+x bei cy+y
    lea __gfx_fc_cx(pc),a0
    move.w (a0),d0
    sub.w d6,d0
    lea __gfx_fc_cy(pc),a0
    move.w (a0),d1
    add.w d7,d1
    lea __gfx_fc_cx(pc),a0
    move.w (a0),d2
    add.w d6,d2
    lea __gfx_fc_fill(pc),a0
    move.w (a0),d3
    bsr __gfx_hline_fast

    ; cx-x .. cx+x bei cy-y
    lea __gfx_circle_x(pc),a0
    move.w (a0),d6
    lea __gfx_circle_y(pc),a0
    move.w (a0),d7
    lea __gfx_fc_cx(pc),a0
    move.w (a0),d0
    sub.w d6,d0
    lea __gfx_fc_cy(pc),a0
    move.w (a0),d1
    sub.w d7,d1
    lea __gfx_fc_cx(pc),a0
    move.w (a0),d2
    add.w d6,d2
    lea __gfx_fc_fill(pc),a0
    move.w (a0),d3
    bsr __gfx_hline_fast

    ; cx-y .. cx+y bei cy+x
    lea __gfx_circle_x(pc),a0
    move.w (a0),d6
    lea __gfx_circle_y(pc),a0
    move.w (a0),d7
    lea __gfx_fc_cx(pc),a0
    move.w (a0),d0
    sub.w d7,d0
    lea __gfx_fc_cy(pc),a0
    move.w (a0),d1
    add.w d6,d1
    lea __gfx_fc_cx(pc),a0
    move.w (a0),d2
    add.w d7,d2
    lea __gfx_fc_fill(pc),a0
    move.w (a0),d3
    bsr __gfx_hline_fast

    ; cx-y .. cx+y bei cy-x
    lea __gfx_circle_x(pc),a0
    move.w (a0),d6
    lea __gfx_circle_y(pc),a0
    move.w (a0),d7
    lea __gfx_fc_cx(pc),a0
    move.w (a0),d0
    sub.w d7,d0
    lea __gfx_fc_cy(pc),a0
    move.w (a0),d1
    sub.w d6,d1
    lea __gfx_fc_cx(pc),a0
    move.w (a0),d2
    add.w d7,d2
    lea __gfx_fc_fill(pc),a0
    move.w (a0),d3
    bsr __gfx_hline_fast

    ; Midpoint-Schritt.
    lea __gfx_circle_y(pc),a0
    move.w (a0),d1
    addq.w #1,d1
    move.w d1,(a0)
    lea __gfx_circle_dec(pc),a0
    move.w (a0),d0
    bge __gfx_fc_fast_dec_ge
    add.w d1,d1
    addq.w #1,d1
    add.w d1,d0
    move.w d0,(a0)
    bra __gfx_fc_fast_fill_loop
__gfx_fc_fast_dec_ge:
    lea __gfx_circle_x(pc),a0
    move.w (a0),d2
    subq.w #1,d2
    move.w d2,(a0)
    lea __gfx_circle_y(pc),a0
    move.w (a0),d1
    sub.w d2,d1
    add.w d1,d1
    addq.w #1,d1
    lea __gfx_circle_dec(pc),a0
    move.w (a0),d0
    add.w d1,d0
    move.w d0,(a0)
    bra __gfx_fc_fast_fill_loop

__gfx_fc_fast_border_start:
    moveq #0,d0
    lea __gfx_fc_i(pc),a0
    move.w d0,(a0)
__gfx_fc_fast_border_loop:
    lea __gfx_fc_i(pc),a0
    move.w (a0),d4
    lea __gfx_fc_width(pc),a0
    move.w (a0),d5
    cmp.w d5,d4
    bge __gfx_fc_fast_done
    lea __gfx_fc_radius(pc),a0
    move.w (a0),d2
    sub.w d4,d2
    bmi __gfx_fc_fast_done
    lea __gfx_fc_cx(pc),a0
    move.w (a0),d0
    lea __gfx_fc_cy(pc),a0
    move.w (a0),d1
    lea __gfx_fc_border(pc),a0
    move.w (a0),d3
    bsr __gfx_call_drawcircle
    lea __gfx_fc_i(pc),a0
    move.w (a0),d0
    addq.w #1,d0
    move.w d0,(a0)
    bra __gfx_fc_fast_border_loop
__gfx_fc_fast_done:
    rts

__gfx_flood_push:
    lea __gfx_flood_top(pc),a0
    move.w (a0),d2
    cmpi.w #$0800,d2
    bge __gfx_flood_push_done
    move.w d2,d3
    lsl.w #2,d3
    lea __gfx_flood_stack(pc),a0
    adda.w d3,a0
    move.w d0,(a0)
    move.w d1,2(a0)
    addq.w #1,d2
    lea __gfx_flood_top(pc),a0
    move.w d2,(a0)
__gfx_flood_push_done:
    rts
FloodFill:
__pas_System_Graphics_FloodFill:
    move.w 8(sp),d0
    lea __gfx_flood_sx(pc),a0
    move.w d0,(a0)
    move.w 6(sp),d0
    lea __gfx_flood_sy(pc),a0
    move.w d0,(a0)
    move.w 4(sp),d0
    lea __gfx_flood_fill(pc),a0
    move.w d0,(a0)
    lea __gfx_flood_sx(pc),a0
    move.w (a0),d0
    lea __gfx_flood_sy(pc),a0
    move.w (a0),d1
    bsr __gfx_call_getpixel
    lea __gfx_flood_source(pc),a0
    move.w d0,(a0)
    lea __gfx_flood_fill(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    beq __gfx_flood_done
    moveq #0,d0
    lea __gfx_flood_top(pc),a0
    move.w d0,(a0)
    lea __gfx_flood_sx(pc),a0
    move.w (a0),d0
    lea __gfx_flood_sy(pc),a0
    move.w (a0),d1
    bsr __gfx_flood_push
__gfx_flood_loop:
    lea __gfx_flood_top(pc),a0
    move.w (a0),d2
    beq __gfx_flood_done
    subq.w #1,d2
    lea __gfx_flood_top(pc),a0
    move.w d2,(a0)
    move.w d2,d3
    lsl.w #2,d3
    lea __gfx_flood_stack(pc),a0
    adda.w d3,a0
    move.w (a0),d0
    move.w 2(a0),d1
    lea __gfx_flood_x(pc),a0
    move.w d0,(a0)
    lea __gfx_flood_y(pc),a0
    move.w d1,(a0)
    tst.w d0
    bmi __gfx_flood_loop
    cmpi.w #$0140,d0
    bge __gfx_flood_loop
    tst.w d1
    bmi __gfx_flood_loop
    cmpi.w #$00C8,d1
    bge __gfx_flood_loop
    bsr __gfx_call_getpixel
    lea __gfx_flood_source(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    bne __gfx_flood_loop
    lea __gfx_flood_x(pc),a0
    move.w (a0),d0
    lea __gfx_flood_y(pc),a0
    move.w (a0),d1
    lea __gfx_flood_fill(pc),a0
    move.w (a0),d2
    bsr __gfx_call_setpixel
    lea __gfx_flood_x(pc),a0
    move.w (a0),d0
    addq.w #1,d0
    lea __gfx_flood_y(pc),a0
    move.w (a0),d1
    bsr __gfx_flood_push
    lea __gfx_flood_x(pc),a0
    move.w (a0),d0
    subq.w #1,d0
    lea __gfx_flood_y(pc),a0
    move.w (a0),d1
    bsr __gfx_flood_push
    lea __gfx_flood_x(pc),a0
    move.w (a0),d0
    lea __gfx_flood_y(pc),a0
    move.w (a0),d1
    addq.w #1,d1
    bsr __gfx_flood_push
    lea __gfx_flood_x(pc),a0
    move.w (a0),d0
    lea __gfx_flood_y(pc),a0
    move.w (a0),d1
    subq.w #1,d1
    bsr __gfx_flood_push
    bra __gfx_flood_loop
__gfx_flood_done:
    rts

DrawTriangle:
__pas_System_Graphics_DrawTriangle:
    move.w 16(sp),d0
    lea __gfx_tri_x1(pc),a0
    move.w d0,(a0)
    move.w 14(sp),d0
    lea __gfx_tri_y1(pc),a0
    move.w d0,(a0)
    move.w 12(sp),d0
    lea __gfx_tri_x2(pc),a0
    move.w d0,(a0)
    move.w 10(sp),d0
    lea __gfx_tri_y2(pc),a0
    move.w d0,(a0)
    move.w 8(sp),d0
    lea __gfx_tri_x3(pc),a0
    move.w d0,(a0)
    move.w 6(sp),d0
    lea __gfx_tri_y3(pc),a0
    move.w d0,(a0)
    move.w 4(sp),d0
    lea __gfx_tri_color(pc),a0
    move.w d0,(a0)
    lea __gfx_tri_x1(pc),a0
    move.w (a0),d0
    lea __gfx_tri_y1(pc),a0
    move.w (a0),d1
    lea __gfx_tri_x2(pc),a0
    move.w (a0),d2
    lea __gfx_tri_y2(pc),a0
    move.w (a0),d3
    lea __gfx_tri_color(pc),a0
    move.w (a0),d4
    bsr __gfx_call_drawline
    lea __gfx_tri_x2(pc),a0
    move.w (a0),d0
    lea __gfx_tri_y2(pc),a0
    move.w (a0),d1
    lea __gfx_tri_x3(pc),a0
    move.w (a0),d2
    lea __gfx_tri_y3(pc),a0
    move.w (a0),d3
    lea __gfx_tri_color(pc),a0
    move.w (a0),d4
    bsr __gfx_call_drawline
    lea __gfx_tri_x3(pc),a0
    move.w (a0),d0
    lea __gfx_tri_y3(pc),a0
    move.w (a0),d1
    lea __gfx_tri_x1(pc),a0
    move.w (a0),d2
    lea __gfx_tri_y1(pc),a0
    move.w (a0),d3
    lea __gfx_tri_color(pc),a0
    move.w (a0),d4
    bsr __gfx_call_drawline
    rts

FillTriangle:
__pas_System_Graphics_FillTriangle:
    move.w 20(sp),d0
    lea __gfx_ft_x1(pc),a0
    move.w d0,(a0)
    move.w 18(sp),d0
    lea __gfx_ft_y1(pc),a0
    move.w d0,(a0)
    move.w 16(sp),d0
    lea __gfx_ft_x2(pc),a0
    move.w d0,(a0)
    move.w 14(sp),d0
    lea __gfx_ft_y2(pc),a0
    move.w d0,(a0)
    move.w 12(sp),d0
    lea __gfx_ft_x3(pc),a0
    move.w d0,(a0)
    move.w 10(sp),d0
    lea __gfx_ft_y3(pc),a0
    move.w d0,(a0)
    move.w 8(sp),d0
    lea __gfx_ft_fill(pc),a0
    move.w d0,(a0)
    move.w 6(sp),d0
    lea __gfx_ft_border(pc),a0
    move.w d0,(a0)
    move.w 4(sp),d0
    lea __gfx_ft_width(pc),a0
    move.w d0,(a0)
    lea __gfx_ft_width(pc),a0
    move.w (a0),d0
    beq __gfx_ft_use_fill
    lea __gfx_ft_border(pc),a0
    move.w (a0),d4
    bra __gfx_ft_color_ready
__gfx_ft_use_fill:
    lea __gfx_ft_fill(pc),a0
    move.w (a0),d4
__gfx_ft_color_ready:
    lea __gfx_ft_x1(pc),a0
    move.w (a0),d0
    lea __gfx_ft_y1(pc),a0
    move.w (a0),d1
    lea __gfx_ft_x2(pc),a0
    move.w (a0),d2
    lea __gfx_ft_y2(pc),a0
    move.w (a0),d3
    bsr __gfx_call_drawline
    lea __gfx_ft_x2(pc),a0
    move.w (a0),d0
    lea __gfx_ft_y2(pc),a0
    move.w (a0),d1
    lea __gfx_ft_x3(pc),a0
    move.w (a0),d2
    lea __gfx_ft_y3(pc),a0
    move.w (a0),d3
    bsr __gfx_call_drawline
    lea __gfx_ft_x3(pc),a0
    move.w (a0),d0
    lea __gfx_ft_y3(pc),a0
    move.w (a0),d1
    lea __gfx_ft_x1(pc),a0
    move.w (a0),d2
    lea __gfx_ft_y1(pc),a0
    move.w (a0),d3
    bsr __gfx_call_drawline
    lea __gfx_ft_x1(pc),a0
    move.w (a0),d0
    lea __gfx_ft_x2(pc),a0
    move.w (a0),d1
    add.w d1,d0
    lea __gfx_ft_x3(pc),a0
    move.w (a0),d1
    add.w d1,d0
    ext.l d0
    divs.w #$0003,d0
    move.w d0,d6
    lea __gfx_ft_y1(pc),a0
    move.w (a0),d0
    lea __gfx_ft_y2(pc),a0
    move.w (a0),d1
    add.w d1,d0
    lea __gfx_ft_y3(pc),a0
    move.w (a0),d1
    add.w d1,d0
    ext.l d0
    divs.w #$0003,d0
    move.w d0,d7
    lea __gfx_ft_fill(pc),a0
    move.w (a0),d2
    move.w d6,d0
    move.w d7,d1
    bsr __gfx_call_flood
    lea __gfx_ft_width(pc),a0
    move.w (a0),d0
    beq __gfx_ft_done
    lea __gfx_ft_x1(pc),a0
    move.w (a0),d0
    lea __gfx_ft_y1(pc),a0
    move.w (a0),d1
    lea __gfx_ft_x2(pc),a0
    move.w (a0),d2
    lea __gfx_ft_y2(pc),a0
    move.w (a0),d3
    lea __gfx_ft_border(pc),a0
    move.w (a0),d4
    bsr __gfx_call_drawline
    lea __gfx_ft_x2(pc),a0
    move.w (a0),d0
    lea __gfx_ft_y2(pc),a0
    move.w (a0),d1
    lea __gfx_ft_x3(pc),a0
    move.w (a0),d2
    lea __gfx_ft_y3(pc),a0
    move.w (a0),d3
    lea __gfx_ft_border(pc),a0
    move.w (a0),d4
    bsr __gfx_call_drawline
    lea __gfx_ft_x3(pc),a0
    move.w (a0),d0
    lea __gfx_ft_y3(pc),a0
    move.w (a0),d1
    lea __gfx_ft_x1(pc),a0
    move.w (a0),d2
    lea __gfx_ft_y1(pc),a0
    move.w (a0),d3
    lea __gfx_ft_border(pc),a0
    move.w (a0),d4
    bsr __gfx_call_drawline
__gfx_ft_done:
    rts

__gfx_normalize_angle:
__gfx_norm_low:
    tst.w d3
    bpl __gfx_norm_high
    addi.w #$0168,d3
    bra __gfx_norm_low
__gfx_norm_high:
    cmpi.w #$0168,d3
    blt __gfx_norm_done
    subi.w #$0168,d3
    bra __gfx_norm_high
__gfx_norm_done:
    rts
__gfx_angle_point:
    move.w d0,d6
    move.w d1,d7
    bsr __gfx_normalize_angle
    move.w d3,d5
    move.w d3,d4
    add.w d4,d4
    lea __gfx_sine(pc),a0
    adda.w d4,a0
    move.w (a0),d4
    muls.w d2,d4
    divs.w #$0100,d4
    add.w d7,d4
    lea __gfx_angle_y(pc),a0
    move.w d4,(a0)
    move.w d5,d3
    addi.w #$005A,d3
    bsr __gfx_normalize_angle
    move.w d3,d4
    add.w d4,d4
    lea __gfx_sine(pc),a0
    adda.w d4,a0
    move.w (a0),d4
    muls.w d2,d4
    divs.w #$0100,d4
    add.w d6,d4
    move.w d4,d0
    lea __gfx_angle_y(pc),a0
    move.w (a0),d1
    rts

DrawTriangleAngles:
__pas_System_Graphics_DrawTriangleAngles:
    move.w 20(sp),d0
    lea __gfx_ta_cx(pc),a0
    move.w d0,(a0)
    move.w 18(sp),d0
    lea __gfx_ta_cy(pc),a0
    move.w d0,(a0)
    move.w 16(sp),d0
    lea __gfx_ta_r1(pc),a0
    move.w d0,(a0)
    move.w 14(sp),d0
    lea __gfx_ta_r2(pc),a0
    move.w d0,(a0)
    move.w 12(sp),d0
    lea __gfx_ta_r3(pc),a0
    move.w d0,(a0)
    move.w 10(sp),d0
    lea __gfx_ta_a1(pc),a0
    move.w d0,(a0)
    move.w 8(sp),d0
    lea __gfx_ta_a2(pc),a0
    move.w d0,(a0)
    move.w 6(sp),d0
    lea __gfx_ta_a3(pc),a0
    move.w d0,(a0)
    move.w 4(sp),d0
    lea __gfx_ta_color(pc),a0
    move.w d0,(a0)
    lea __gfx_ta_cx(pc),a0
    move.w (a0),d0
    lea __gfx_ta_cy(pc),a0
    move.w (a0),d1
    lea __gfx_ta_r1(pc),a0
    move.w (a0),d2
    lea __gfx_ta_a1(pc),a0
    move.w (a0),d3
    bsr __gfx_angle_point
    lea __gfx_ta_x1(pc),a0
    move.w d0,(a0)
    lea __gfx_ta_y1(pc),a0
    move.w d1,(a0)
    lea __gfx_ta_cx(pc),a0
    move.w (a0),d0
    lea __gfx_ta_cy(pc),a0
    move.w (a0),d1
    lea __gfx_ta_r2(pc),a0
    move.w (a0),d2
    lea __gfx_ta_a2(pc),a0
    move.w (a0),d3
    bsr __gfx_angle_point
    lea __gfx_ta_x2(pc),a0
    move.w d0,(a0)
    lea __gfx_ta_y2(pc),a0
    move.w d1,(a0)
    lea __gfx_ta_cx(pc),a0
    move.w (a0),d0
    lea __gfx_ta_cy(pc),a0
    move.w (a0),d1
    lea __gfx_ta_r3(pc),a0
    move.w (a0),d2
    lea __gfx_ta_a3(pc),a0
    move.w (a0),d3
    bsr __gfx_angle_point
    lea __gfx_ta_x3(pc),a0
    move.w d0,(a0)
    lea __gfx_ta_y3(pc),a0
    move.w d1,(a0)
    lea __gfx_ta_x1(pc),a0
    move.w (a0),d0
    lea __gfx_ta_y1(pc),a0
    move.w (a0),d1
    lea __gfx_ta_x2(pc),a0
    move.w (a0),d2
    lea __gfx_ta_y2(pc),a0
    move.w (a0),d3
    lea __gfx_ta_x3(pc),a0
    move.w (a0),d4
    lea __gfx_ta_y3(pc),a0
    move.w (a0),d5
    lea __gfx_ta_color(pc),a0
    move.w (a0),d6
    move.w d0,-(sp)
    move.w d1,-(sp)
    move.w d2,-(sp)
    move.w d3,-(sp)
    move.w d4,-(sp)
    move.w d5,-(sp)
    move.w d6,-(sp)
    bsr __pas_System_Graphics_DrawTriangle
    adda.w #$000E,sp
    rts

    even
__gfx_graphics_active: dc.b 0
__gfx_text_mode: dc.b 1
    even
__gfx_text_background: dc.w $0000
__gfx_text_foreground: dc.w $0FFF
__gfx_masks: dc.b $80,$40,$20,$10,$08,$04,$02,$01
    even
__gfx_palette: dc.w $000,$FFF,$F00,$0FF,$F0F,$0F0,$00F,$FF0,$F80,$840,$F66,$444,$888,$8F8,$88F,$CCC
__gfx_line_x: dc.w 0
__gfx_line_y: dc.w 0
__gfx_line_x2: dc.w 0
__gfx_line_y2: dc.w 0
__gfx_line_color: dc.w 0
__gfx_line_dx: dc.w 0
__gfx_line_dy: dc.w 0
__gfx_line_sx: dc.w 0
__gfx_line_sy: dc.w 0
__gfx_line_err: dc.w 0
__gfx_line_e2: dc.w 0
__gfx_rect_x1: dc.w 0
__gfx_rect_y1: dc.w 0
__gfx_rect_x2: dc.w 0
__gfx_rect_y2: dc.w 0
__gfx_rect_color: dc.w 0
__gfx_fr_x1: dc.w 0
__gfx_fr_y1: dc.w 0
__gfx_fr_x2: dc.w 0
__gfx_fr_y2: dc.w 0
__gfx_fr_fill: dc.w 0
__gfx_fr_border: dc.w 0
__gfx_fr_width: dc.w 0
__gfx_fr_x: dc.w 0
__gfx_fr_y: dc.w 0
__gfx_fr_i: dc.w 0
__gfx_circle_cx: dc.w 0
__gfx_circle_cy: dc.w 0
__gfx_circle_radius: dc.w 0
__gfx_circle_color: dc.w 0
__gfx_circle_x: dc.w 0
__gfx_circle_y: dc.w 0
__gfx_circle_dec: dc.w 0
__gfx_fc_cx: dc.w 0
__gfx_fc_cy: dc.w 0
__gfx_fc_radius: dc.w 0
__gfx_fc_fill: dc.w 0
__gfx_fc_border: dc.w 0
__gfx_fc_width: dc.w 0
__gfx_fc_r: dc.w 0
__gfx_fc_i: dc.w 0
__gfx_flood_sx: dc.w 0
__gfx_flood_sy: dc.w 0
__gfx_flood_fill: dc.w 0
__gfx_flood_source: dc.w 0
__gfx_flood_top: dc.w 0
__gfx_flood_x: dc.w 0
__gfx_flood_y: dc.w 0
__gfx_tri_x1: dc.w 0
__gfx_tri_y1: dc.w 0
__gfx_tri_x2: dc.w 0
__gfx_tri_y2: dc.w 0
__gfx_tri_x3: dc.w 0
__gfx_tri_y3: dc.w 0
__gfx_tri_color: dc.w 0
__gfx_ft_x1: dc.w 0
__gfx_ft_y1: dc.w 0
__gfx_ft_x2: dc.w 0
__gfx_ft_y2: dc.w 0
__gfx_ft_x3: dc.w 0
__gfx_ft_y3: dc.w 0
__gfx_ft_fill: dc.w 0
__gfx_ft_border: dc.w 0
__gfx_ft_width: dc.w 0
__gfx_angle_y: dc.w 0
__gfx_ta_cx: dc.w 0
__gfx_ta_cy: dc.w 0
__gfx_ta_r1: dc.w 0
__gfx_ta_r2: dc.w 0
__gfx_ta_r3: dc.w 0
__gfx_ta_a1: dc.w 0
__gfx_ta_a2: dc.w 0
__gfx_ta_a3: dc.w 0
__gfx_ta_color: dc.w 0
__gfx_ta_x1: dc.w 0
__gfx_ta_y1: dc.w 0
__gfx_ta_x2: dc.w 0
__gfx_ta_y2: dc.w 0
__gfx_ta_x3: dc.w 0
__gfx_ta_y3: dc.w 0
__gfx_flood_stack: ds.w 4096
__gfx_sine:
    dc.w $0000,$0004,$0009,$000D,$0012,$0016,$001B,$001F,$0024,$0028,$002C,$0031
    dc.w $0035,$003A,$003E,$0042,$0047,$004B,$004F,$0053,$0058,$005C,$0060,$0064
    dc.w $0068,$006C,$0070,$0074,$0078,$007C,$0080,$0084,$0088,$008B,$008F,$0093
    dc.w $0096,$009A,$009E,$00A1,$00A5,$00A8,$00AB,$00AF,$00B2,$00B5,$00B8,$00BB
    dc.w $00BE,$00C1,$00C4,$00C7,$00CA,$00CC,$00CF,$00D2,$00D4,$00D7,$00D9,$00DB
    dc.w $00DE,$00E0,$00E2,$00E4,$00E6,$00E8,$00EA,$00EC,$00ED,$00EF,$00F1,$00F2
    dc.w $00F3,$00F5,$00F6,$00F7,$00F8,$00F9,$00FA,$00FB,$00FC,$00FD,$00FE,$00FE
    dc.w $00FF,$00FF,$00FF,$0100,$0100,$0100,$0100,$0100,$0100,$0100,$00FF,$00FF
    dc.w $00FF,$00FE,$00FE,$00FD,$00FC,$00FB,$00FA,$00F9,$00F8,$00F7,$00F6,$00F5
    dc.w $00F3,$00F2,$00F1,$00EF,$00ED,$00EC,$00EA,$00E8,$00E6,$00E4,$00E2,$00E0
    dc.w $00DE,$00DB,$00D9,$00D7,$00D4,$00D2,$00CF,$00CC,$00CA,$00C7,$00C4,$00C1
    dc.w $00BE,$00BB,$00B8,$00B5,$00B2,$00AF,$00AB,$00A8,$00A5,$00A1,$009E,$009A
    dc.w $0096,$0093,$008F,$008B,$0088,$0084,$0080,$007C,$0078,$0074,$0070,$006C
    dc.w $0068,$0064,$0060,$005C,$0058,$0053,$004F,$004B,$0047,$0042,$003E,$003A
    dc.w $0035,$0031,$002C,$0028,$0024,$001F,$001B,$0016,$0012,$000D,$0009,$0004
    dc.w $0000,$FFFC,$FFF7,$FFF3,$FFEE,$FFEA,$FFE5,$FFE1,$FFDC,$FFD8,$FFD4,$FFCF
    dc.w $FFCB,$FFC6,$FFC2,$FFBE,$FFB9,$FFB5,$FFB1,$FFAD,$FFA8,$FFA4,$FFA0,$FF9C
    dc.w $FF98,$FF94,$FF90,$FF8C,$FF88,$FF84,$FF80,$FF7C,$FF78,$FF75,$FF71,$FF6D
    dc.w $FF6A,$FF66,$FF62,$FF5F,$FF5B,$FF58,$FF55,$FF51,$FF4E,$FF4B,$FF48,$FF45
    dc.w $FF42,$FF3F,$FF3C,$FF39,$FF36,$FF34,$FF31,$FF2E,$FF2C,$FF29,$FF27,$FF25
    dc.w $FF22,$FF20,$FF1E,$FF1C,$FF1A,$FF18,$FF16,$FF14,$FF13,$FF11,$FF0F,$FF0E
    dc.w $FF0D,$FF0B,$FF0A,$FF09,$FF08,$FF07,$FF06,$FF05,$FF04,$FF03,$FF02,$FF02
    dc.w $FF01,$FF01,$FF01,$FF00,$FF00,$FF00,$FF00,$FF00,$FF00,$FF00,$FF01,$FF01
    dc.w $FF01,$FF02,$FF02,$FF03,$FF04,$FF05,$FF06,$FF07,$FF08,$FF09,$FF0A,$FF0B
    dc.w $FF0D,$FF0E,$FF0F,$FF11,$FF13,$FF14,$FF16,$FF18,$FF1A,$FF1C,$FF1E,$FF20
    dc.w $FF22,$FF25,$FF27,$FF29,$FF2C,$FF2E,$FF31,$FF34,$FF36,$FF39,$FF3C,$FF3F
    dc.w $FF42,$FF45,$FF48,$FF4B,$FF4E,$FF51,$FF55,$FF58,$FF5B,$FF5F,$FF62,$FF66
    dc.w $FF6A,$FF6D,$FF71,$FF75,$FF78,$FF7C,$FF80,$FF84,$FF88,$FF8C,$FF90,$FF94
    dc.w $FF98,$FF9C,$FFA0,$FFA4,$FFA8,$FFAD,$FFB1,$FFB5,$FFB9,$FFBE,$FFC2,$FFC6
    dc.w $FFCB,$FFCF,$FFD4,$FFD8,$FFDC,$FFE1,$FFE5,$FFEA,$FFEE,$FFF3,$FFF7,$FFFC
end
