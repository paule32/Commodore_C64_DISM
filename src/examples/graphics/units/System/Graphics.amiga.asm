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
    move.l #$00DFF000,a0
    move.w d1,$0180(a0)
    move.w d2,$0182(a0)
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

__pas_System_Graphics_ClearScreen:
    lea __gfx_graphics_active(pc),a0
    tst.b (a0)
    beq __gfx_clear_current_text
    bsr __gfx_clear_graphics_planes
    rts
__gfx_clear_current_text:
    bsr __gfx_clear_text_plane
    rts

__pas_System_Graphics_InitGraphics:
    move.l #$00DFF000,a0
    move.w #$7FFF,$009A(a0)
    move.w #$7FFF,$0096(a0)
    move.w #$2C81,$008E(a0)
    move.w #$F4C1,$0090(a0)
    move.w #$0038,$0092(a0)
    move.w #$00D0,$0094(a0)
    move.w #$4200,$0100(a0)
    move.w #$0000,$0102(a0)
    move.w #$0000,$0104(a0)
    move.w #$0000,$0108(a0)
    move.w #$0000,$010A(a0)
    move.l #$00020000,d0
    move.l d0,$00E0(a0)
    move.l #$00022000,d0
    move.l d0,$00E4(a0)
    move.l #$00024000,d0
    move.l d0,$00E8(a0)
    move.l #$00026000,d0
    move.l d0,$00EC(a0)
    move.w __gfx_palette+0(pc),$0180(a0)
    move.w __gfx_palette+2(pc),$0182(a0)
    move.w __gfx_palette+4(pc),$0184(a0)
    move.w __gfx_palette+6(pc),$0186(a0)
    move.w __gfx_palette+8(pc),$0188(a0)
    move.w __gfx_palette+10(pc),$018A(a0)
    move.w __gfx_palette+12(pc),$018C(a0)
    move.w __gfx_palette+14(pc),$018E(a0)
    move.w __gfx_palette+16(pc),$0190(a0)
    move.w __gfx_palette+18(pc),$0192(a0)
    move.w __gfx_palette+20(pc),$0194(a0)
    move.w __gfx_palette+22(pc),$0196(a0)
    move.w __gfx_palette+24(pc),$0198(a0)
    move.w __gfx_palette+26(pc),$019A(a0)
    move.w __gfx_palette+28(pc),$019C(a0)
    move.w __gfx_palette+30(pc),$019E(a0)
    bsr __gfx_clear_graphics_planes
    lea __gfx_graphics_active(pc),a0
    move.b #$01,(a0)
    move.l #$00DFF000,a0
    move.w #$8300,$0096(a0)
    rts

__pas_System_Graphics_DoneGraphics:
    lea __gfx_text_mode(pc),a0
    move.b 5(sp),(a0)
    lea __gfx_graphics_active(pc),a0
    clr.b (a0)
    move.l #$00DFF000,a0
    move.w #$7FFF,$0096(a0)
    move.w #$1200,$0100(a0)
    move.l #$00018000,d0
    move.l d0,$00E0(a0)
    move.w #$0000,$0180(a0)
    move.w #$0FFF,$0182(a0)
    bsr __gfx_clear_text_plane
    move.l #$00DFF000,a0
    move.w #$8300,$0096(a0)
    rts

__pas_System_Graphics_SetPixel:
    move.w 8(sp),d0
    bmi __gfx_setpixel_done
    cmpi.w #$0140,d0
    bge __gfx_setpixel_done
    move.w 6(sp),d1
    bmi __gfx_setpixel_done
    cmpi.w #$00C8,d1
    bge __gfx_setpixel_done
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
    move.w 4(sp),d4
    andi.w #$000F,d4
    move.l #$00020000,a0
    adda.w d2,a0
    moveq #0,d1
    move.b (a0),d1
    move.w d4,d0
    andi.w #$0001,d0
    beq __gfx_sp_clear_0
    or.b d3,d1
    bra __gfx_sp_store_0
__gfx_sp_clear_0:
    move.w d3,d0
    eori.b #$FF,d0
    and.b d0,d1
__gfx_sp_store_0:
    move.b d1,(a0)
    lsr.w #1,d4
    move.l #$00022000,a0
    adda.w d2,a0
    moveq #0,d1
    move.b (a0),d1
    move.w d4,d0
    andi.w #$0001,d0
    beq __gfx_sp_clear_1
    or.b d3,d1
    bra __gfx_sp_store_1
__gfx_sp_clear_1:
    move.w d3,d0
    eori.b #$FF,d0
    and.b d0,d1
__gfx_sp_store_1:
    move.b d1,(a0)
    lsr.w #1,d4
    move.l #$00024000,a0
    adda.w d2,a0
    moveq #0,d1
    move.b (a0),d1
    move.w d4,d0
    andi.w #$0001,d0
    beq __gfx_sp_clear_2
    or.b d3,d1
    bra __gfx_sp_store_2
__gfx_sp_clear_2:
    move.w d3,d0
    eori.b #$FF,d0
    and.b d0,d1
__gfx_sp_store_2:
    move.b d1,(a0)
    lsr.w #1,d4
    move.l #$00026000,a0
    adda.w d2,a0
    moveq #0,d1
    move.b (a0),d1
    move.w d4,d0
    andi.w #$0001,d0
    beq __gfx_sp_clear_3
    or.b d3,d1
    bra __gfx_sp_store_3
__gfx_sp_clear_3:
    move.w d3,d0
    eori.b #$FF,d0
    and.b d0,d1
__gfx_sp_store_3:
    move.b d1,(a0)
__gfx_setpixel_done:
    rts

__pas_System_Graphics_GetPixel:
    moveq #0,d5
    move.w 6(sp),d0
    bmi __gfx_getpixel_done
    cmpi.w #$0140,d0
    bge __gfx_getpixel_done
    move.w 4(sp),d1
    bmi __gfx_getpixel_done
    cmpi.w #$00C8,d1
    bge __gfx_getpixel_done
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
    beq __gfx_gp_next_0
    ori.w #$0001,d5
__gfx_gp_next_0:
    move.l #$00022000,a0
    adda.w d2,a0
    moveq #0,d0
    move.b (a0),d0
    and.b d3,d0
    beq __gfx_gp_next_1
    ori.w #$0002,d5
__gfx_gp_next_1:
    move.l #$00024000,a0
    adda.w d2,a0
    moveq #0,d0
    move.b (a0),d0
    and.b d3,d0
    beq __gfx_gp_next_2
    ori.w #$0004,d5
__gfx_gp_next_2:
    move.l #$00026000,a0
    adda.w d2,a0
    moveq #0,d0
    move.b (a0),d0
    and.b d3,d0
    beq __gfx_gp_next_3
    ori.w #$0008,d5
__gfx_gp_next_3:
__gfx_getpixel_done:
    move.w d5,d0
    rts

__gfx_call_setpixel:
    move.w d0,-(sp)
    move.w d1,-(sp)
    move.w d2,-(sp)
    bsr __pas_System_Graphics_SetPixel
    adda.w #$0006,sp
    rts
__gfx_call_getpixel:
    move.w d0,-(sp)
    move.w d1,-(sp)
    bsr __pas_System_Graphics_GetPixel
    adda.w #$0004,sp
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
    lea __gfx_rect_x1(pc),a0
    move.w (a0),d0
    lea __gfx_rect_y1(pc),a0
    move.w (a0),d1
    lea __gfx_rect_x2(pc),a0
    move.w (a0),d2
    lea __gfx_rect_y1(pc),a0
    move.w (a0),d3
    lea __gfx_rect_color(pc),a0
    move.w (a0),d4
    bsr __gfx_call_drawline
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
    lea __gfx_rect_x2(pc),a0
    move.w (a0),d0
    lea __gfx_rect_y2(pc),a0
    move.w (a0),d1
    lea __gfx_rect_x1(pc),a0
    move.w (a0),d2
    lea __gfx_rect_y2(pc),a0
    move.w (a0),d3
    lea __gfx_rect_color(pc),a0
    move.w (a0),d4
    bsr __gfx_call_drawline
    lea __gfx_rect_x1(pc),a0
    move.w (a0),d0
    lea __gfx_rect_y2(pc),a0
    move.w (a0),d1
    lea __gfx_rect_x1(pc),a0
    move.w (a0),d2
    lea __gfx_rect_y1(pc),a0
    move.w (a0),d3
    lea __gfx_rect_color(pc),a0
    move.w (a0),d4
    bsr __gfx_call_drawline
    rts

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
    lea __gfx_fr_x1(pc),a0
    move.w (a0),d0
    lea __gfx_fr_x2(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    ble __gfx_fr_x_ok
    lea __gfx_fr_x1(pc),a0
    move.w d1,(a0)
    lea __gfx_fr_x2(pc),a0
    move.w d0,(a0)
__gfx_fr_x_ok:
    lea __gfx_fr_y1(pc),a0
    move.w (a0),d0
    lea __gfx_fr_y2(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    ble __gfx_fr_y_ok
    lea __gfx_fr_y1(pc),a0
    move.w d1,(a0)
    lea __gfx_fr_y2(pc),a0
    move.w d0,(a0)
__gfx_fr_y_ok:
    lea __gfx_fr_y1(pc),a0
    move.w (a0),d0
    lea __gfx_fr_y(pc),a0
    move.w d0,(a0)
__gfx_fr_y_loop:
    lea __gfx_fr_x1(pc),a0
    move.w (a0),d0
    lea __gfx_fr_x(pc),a0
    move.w d0,(a0)
__gfx_fr_x_loop:
    lea __gfx_fr_x(pc),a0
    move.w (a0),d0
    lea __gfx_fr_y(pc),a0
    move.w (a0),d1
    lea __gfx_fr_fill(pc),a0
    move.w (a0),d2
    bsr __gfx_call_setpixel
    lea __gfx_fr_x(pc),a0
    move.w (a0),d0
    addq.w #1,d0
    lea __gfx_fr_x(pc),a0
    move.w d0,(a0)
    lea __gfx_fr_x2(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    ble __gfx_fr_x_loop
    lea __gfx_fr_y(pc),a0
    move.w (a0),d0
    addq.w #1,d0
    lea __gfx_fr_y(pc),a0
    move.w d0,(a0)
    lea __gfx_fr_y2(pc),a0
    move.w (a0),d1
    cmp.w d1,d0
    ble __gfx_fr_y_loop
    moveq #0,d0
    lea __gfx_fr_i(pc),a0
    move.w d0,(a0)
__gfx_fr_border_loop:
    lea __gfx_fr_i(pc),a0
    move.w (a0),d5
    lea __gfx_fr_width(pc),a0
    move.w (a0),d6
    cmp.w d6,d5
    bge __gfx_fr_done
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
    lea __gfx_fr_i(pc),a0
    move.w d0,(a0)
    bra __gfx_fr_border_loop
__gfx_fr_done:
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
    lea __gfx_fc_r(pc),a0
    move.w d0,(a0)
__gfx_fc_fill_loop:
    lea __gfx_fc_r(pc),a0
    move.w (a0),d2
    bmi __gfx_fc_border_start
    lea __gfx_fc_cx(pc),a0
    move.w (a0),d0
    lea __gfx_fc_cy(pc),a0
    move.w (a0),d1
    lea __gfx_fc_fill(pc),a0
    move.w (a0),d3
    bsr __gfx_call_drawcircle
    lea __gfx_fc_r(pc),a0
    move.w (a0),d0
    subq.w #1,d0
    lea __gfx_fc_r(pc),a0
    move.w d0,(a0)
    bra __gfx_fc_fill_loop
__gfx_fc_border_start:
    moveq #0,d0
    lea __gfx_fc_i(pc),a0
    move.w d0,(a0)
__gfx_fc_border_loop:
    lea __gfx_fc_i(pc),a0
    move.w (a0),d4
    lea __gfx_fc_width(pc),a0
    move.w (a0),d5
    cmp.w d5,d4
    bge __gfx_fc_done
    lea __gfx_fc_radius(pc),a0
    move.w (a0),d2
    sub.w d4,d2
    bmi __gfx_fc_done
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
    lea __gfx_fc_i(pc),a0
    move.w d0,(a0)
    bra __gfx_fc_border_loop
__gfx_fc_done:
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
