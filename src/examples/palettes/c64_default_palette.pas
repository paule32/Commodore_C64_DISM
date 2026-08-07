{ 16 C64-Farben als RGB-Tripel. }
const
    C64CustomPalette: array[0..15, 0..2] of Byte = (
        ($00, $00, $00), { 00: Schwarz }
        ($FF, $FF, $FF), { 01: Weiß }
        ($88, $39, $32), { 02: Rot }
        ($67, $B6, $BD), { 03: Cyan }
        ($8B, $3F, $96), { 04: Violett }
        ($55, $A0, $49), { 05: Grün }
        ($40, $31, $8D), { 06: Blau }
        ($BF, $CE, $72), { 07: Gelb }
        ($8B, $54, $29), { 08: Orange }
        ($57, $42, $00), { 09: Braun }
        ($B8, $69, $62), { 10: Hellrot }
        ($50, $50, $50), { 11: Dunkelgrau }
        ($78, $78, $78), { 12: Grau }
        ($94, $E0, $89), { 13: Hellgrün }
        ($78, $69, $C4), { 14: Hellblau }
        ($9F, $9F, $9F) { 15: Hellgrau }
    );
