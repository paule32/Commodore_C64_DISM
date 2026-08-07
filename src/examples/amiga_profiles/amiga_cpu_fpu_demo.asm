; mk68060 + 68882 profile demonstration
section code,code
xdef _start
_start:
    movec vbr,d0
    movec pcr,d1
    link.l a6,#-16
    extb.l d0
    fmove fp0,fp1
    fadd fp1,fp2
    fmul fp2,fp3
    fcmp fp3,fp4
    ftst fp4
    fnop
    unlk a6
    rts
