; ------------------------------------------------------------------
; MOS-6510-Code aus vollständigem C64-RAM-Abbild
; Quelle: Dalek_Attack_ram.bin
; SHA-256: 6e5233f4b89231568e12ef9f97eb450bf9becf6dfc30fd6755bd6265edd25fdc
; Einsprung: $4100
;
; Kontrollflussbasiert: Nicht erreichbare Datenbytes werden nicht
; als vermeintliche Befehle ausgegeben.
; ------------------------------------------------------------------

; Dalek-Profil:
;   $4100 = Intro-Start
;   $46DC = Intro-Hauptschleife
;   $1D70 = FIRE-Ausgang
;   $0810/$0100 = nachgelagerter Spielentpacker

; ==================== INTRO-CODE ====================

.org $1021
music_play:
    LDX #$00                   ; $1021: A2 00
    DEC $1090                  ; $1023: CE 90 10
    BMI L1034                  ; $1026: 30 0C
    JSR L1226                  ; $1028: 20 26 12
    JSR L1225                  ; $102B: 20 25 12
    JMP L1225                  ; $102E: 4C 25 12

.org $1034
L1034:
    LDA #$03                   ; $1034: A9 03
    STA $1090                  ; $1036: 8D 90 10
    JSR L1040                  ; $1039: 20 40 10
    JSR L103F                  ; $103C: 20 3F 10
L103F:
    INX                        ; $103F: E8
L1040:
    DEC $108A,X                ; $1040: DE 8A 10
    BMI L1091                  ; $1043: 30 4C
    JMP L1226                  ; $1045: 4C 26 12
music_init:
    LDA #$1F                   ; $1048: A9 1F
    STA SID_VOLUME             ; $104A: 8D 18 D4
    LDA #$F0                   ; $104D: A9 F0
    STA SID_FILTER             ; $104F: 8D 17 D4
    AND #$0F                   ; $1052: 29 0F
    STA $1262                  ; $1054: 8D 62 12
    LDX #$0F                   ; $1057: A2 0F
L1059:
    STA $1081,X                ; $1059: 9D 81 10
    DEX                        ; $105C: CA
    BPL L1059                  ; $105D: 10 FA
    LDX #$02                   ; $105F: A2 02
L1061:
    LDA $14B9,X                ; $1061: BD B9 14
    STA $FA                    ; $1064: 85 FA
    LDA $14BC,X                ; $1066: BD BC 14
    STA $FB                    ; $1069: 85 FB
    LDY #$00                   ; $106B: A0 00
    LDA ($FA),Y                ; $106D: B1 FA
    STA $108D,X                ; $106F: 9D 8D 10
    INY                        ; $1072: C8
    LDA ($FA),Y                ; $1073: B1 FA
    STA $10E6,X                ; $1075: 9D E6 10
    AND #$0F                   ; $1078: 29 0F
    STA $10E9,X                ; $107A: 9D E9 10
    DEX                        ; $107D: CA
    BPL L1061                  ; $107E: 10 E1
    RTS                        ; $1080: 60

.org $1091
L1091:
    LDY $108D,X                ; $1091: BC 8D 10
    CPY #$FE                   ; $1094: C0 FE
    BNE L10A1                  ; $1096: D0 09
L1098:
    LDA $1084,X                ; $1098: BD 84 10
    AND #$FE                   ; $109B: 29 FE
    STA $1084,X                ; $109D: 9D 84 10
    RTS                        ; $10A0: 60
L10A1:
    LDA $1B50,Y                ; $10A1: B9 50 1B
    STA $FA                    ; $10A4: 85 FA
    LDA $1B31,Y                ; $10A6: B9 31 1B
    STA $FB                    ; $10A9: 85 FB
    LDY $1081,X                ; $10AB: BC 81 10
    LDA ($FA),Y                ; $10AE: B1 FA
    BMI L10D2                  ; $10B0: 30 20
    CMP #$60                   ; $10B2: C9 60
    BCC L10F9                  ; $10B4: 90 43
L10B6:
    AND #$1F                   ; $10B6: 29 1F
    STA $108A,X                ; $10B8: 9D 8A 10
    LDA #$FE                   ; $10BB: A9 FE
    STA $1031,X                ; $10BD: 9D 31 10
    JSR L1098                  ; $10C0: 20 98 10
L10C3:
    JMP L1187                  ; $10C3: 4C 87 11

.org $10D2
L10D2:
    CMP #$A0                   ; $10D2: C9 A0
    BCC L10EC                  ; $10D4: 90 16
    AND #$1F                   ; $10D6: 29 1F
    STA $108A,X                ; $10D8: 9D 8A 10
    BCS L10C3                  ; $10DB: B0 E6
    BRK                        ; $10DD: 00

.org $10EC
L10EC:
    ASL A                      ; $10EC: 0A
    ASL A                      ; $10ED: 0A
    ASL A                      ; $10EE: 0A
    STA $13D9,X                ; $10EF: 9D D9 13
    INY                        ; $10F2: C8
    LDA ($FA),Y                ; $10F3: B1 FA
    CMP #$60                   ; $10F5: C9 60
    BCS L10B6                  ; $10F7: B0 BD
L10F9:
    STA $FC                    ; $10F9: 85 FC
    INY                        ; $10FB: C8
    LDA $10E6,X                ; $10FC: BD E6 10
    LSR A                      ; $10FF: 4A
    LSR A                      ; $1100: 4A
    LSR A                      ; $1101: 4A
    LSR A                      ; $1102: 4A
    CLC                        ; $1103: 18
    ADC $FC                    ; $1104: 65 FC
    STA $10C9,X                ; $1106: 9D C9 10
    STY $FC                    ; $1109: 84 FC
    TAY                        ; $110B: A8
    LDA $1437,Y                ; $110C: B9 37 14
    STA $10CC,X                ; $110F: 9D CC 10
    STA $13E2,X                ; $1112: 9D E2 13
    LDA $11C5,Y                ; $1115: B9 C5 11
    STA $10CF,X                ; $1118: 9D CF 10
    STA $12B6,X                ; $111B: 9D B6 12
    LDY $FC                    ; $111E: A4 FC
    LDA ($FA),Y                ; $1120: B1 FA
    STA $1141,X                ; $1122: 9D 41 11
    AND #$1F                   ; $1125: 29 1F
    STA $108A,X                ; $1127: 9D 8A 10
    LDA ($FA),Y                ; $112A: B1 FA
    BMI L1150                  ; $112C: 30 22
    AND #$20                   ; $112E: 29 20
    BEQ L1177                  ; $1130: F0 45
    INY                        ; $1132: C8
    LDA ($FA),Y                ; $1133: B1 FA
    STA $1147,X                ; $1135: 9D 47 11
    INY                        ; $1138: C8
    LDA ($FA),Y                ; $1139: B1 FA
    STA $114A,X                ; $113B: 9D 4A 11
    JMP L1177                  ; $113E: 4C 77 11

.org $1150
L1150:
    STX $1262                  ; $1150: 8E 62 12
    INY                        ; $1153: C8
    LDA ($FA),Y                ; $1154: B1 FA
    STA $1266                  ; $1156: 8D 66 12
    AND #$0F                   ; $1159: 29 0F
    ASL A                      ; $115B: 0A
    SEC                        ; $115C: 38
    SBC #$10                   ; $115D: E9 10
    STA $12A0                  ; $115F: 8D A0 12
    INY                        ; $1162: C8
    LDA ($FA),Y                ; $1163: B1 FA
    BNE L116E                  ; $1165: D0 07
    LDA #$F0                   ; $1167: A9 F0
    STA SID_FILTER             ; $1169: 8D 17 D4
    BNE L1177                  ; $116C: D0 09
L116E:
    STA $126B                  ; $116E: 8D 6B 12
    LDA $12B3,X                ; $1171: BD B3 12
    STA SID_FILTER             ; $1174: 8D 17 D4
L1177:
    LDA #$FF                   ; $1177: A9 FF
    STA $1031,X                ; $1179: 9D 31 10
    STA $12B9,X                ; $117C: 9D B9 12
    LDA #$00                   ; $117F: A9 00
    STA $10DD,X                ; $1181: 9D DD 10
    STA $12BD,X                ; $1184: 9D BD 12
L1187:
    INY                        ; $1187: C8
    LDA ($FA),Y                ; $1188: B1 FA
    CMP #$FF                   ; $118A: C9 FF
    BNE L11C0                  ; $118C: D0 32
    DEC $10E9,X                ; $118E: DE E9 10
    BPL L11BE                  ; $1191: 10 2B
    LDA $14B9,X                ; $1193: BD B9 14
    STA $FA                    ; $1196: 85 FA
    LDA $14BC,X                ; $1198: BD BC 14
    STA $FB                    ; $119B: 85 FB
    LDY $1087,X                ; $119D: BC 87 10
    INY                        ; $11A0: C8
    INY                        ; $11A1: C8
    LDA ($FA),Y                ; $11A2: B1 FA
    CMP #$FF                   ; $11A4: C9 FF
    BNE L11AA                  ; $11A6: D0 02
    LDY #$00                   ; $11A8: A0 00
L11AA:
    TYA                        ; $11AA: 98
    STA $1087,X                ; $11AB: 9D 87 10
    LDA ($FA),Y                ; $11AE: B1 FA
    STA $108D,X                ; $11B0: 9D 8D 10
    INY                        ; $11B3: C8
    LDA ($FA),Y                ; $11B4: B1 FA
    STA $10E6,X                ; $11B6: 9D E6 10
    AND #$0F                   ; $11B9: 29 0F
    STA $10E9,X                ; $11BB: 9D E9 10
L11BE:
    LDY #$00                   ; $11BE: A0 00
L11C0:
    TYA                        ; $11C0: 98
    STA $1081,X                ; $11C1: 9D 81 10
    RTS                        ; $11C4: 60

.org $1225
L1225:
    INX                        ; $1225: E8
L1226:
    LDY $13D9,X                ; $1226: BC D9 13
    STY $FC                    ; $1229: 84 FC
    LDA $1141,X                ; $122B: BD 41 11
    AND #$40                   ; $122E: 29 40
    BNE L1290                  ; $1230: D0 5E
    STA $1144,X                ; $1232: 9D 44 11
    LDA $1559,Y                ; $1235: B9 59 15
    STA $FA                    ; $1238: 85 FA
    LDA $155A,Y                ; $123A: B9 5A 15
    LDY $10C6,X                ; $123D: BC C6 10
    STA $D406,Y                ; $1240: 99 06 D4
    LDA $FA                    ; $1243: A5 FA
    STA $D405,Y                ; $1245: 99 05 D4
    LDA $1084,X                ; $1248: BD 84 10
    AND #$FE                   ; $124B: 29 FE
    STA $D404,Y                ; $124D: 99 04 D4
    LDY $FC                    ; $1250: A4 FC
    LDA $155B,Y                ; $1252: B9 5B 15
    STA $1084,X                ; $1255: 9D 84 10
    LDA $155C,Y                ; $1258: B9 5C 15
    STA $13DC,X                ; $125B: 9D DC 13
    STA $13DF,X                ; $125E: 9D DF 13
    CPX #$00                   ; $1261: E0 00
    BNE L126F                  ; $1263: D0 0A
    LDA #$8F                   ; $1265: A9 8F
    STA $129E                  ; $1267: 8D 9E 12
    LDA #$8F                   ; $126A: A9 8F
    STA $1296                  ; $126C: 8D 96 12
L126F:
    LDA #$00                   ; $126F: A9 00
    STA $10E0,X                ; $1271: 9D E0 10
    STA $10E3,X                ; $1274: 9D E3 10
    LDA $155E,Y                ; $1277: B9 5E 15
    LSR A                      ; $127A: 4A
    LSR A                      ; $127B: 4A
    LSR A                      ; $127C: 4A
    STA $114D,X                ; $127D: 9D 4D 11
    LDA $1141,X                ; $1280: BD 41 11
    ORA #$40                   ; $1283: 09 40
    STA $1141,X                ; $1285: 9D 41 11
    LDA $1560,Y                ; $1288: B9 60 15
    STA $FD,X                  ; $128B: 95 FD
    JMP L1385                  ; $128D: 4C 85 13
L1290:
    CPX $1262                  ; $1290: EC 62 12
    BNE L12A7                  ; $1293: D0 12
    LDA #$8F                   ; $1295: A9 8F
    BEQ L12A7                  ; $1297: F0 0E
    DEC $1296                  ; $1299: CE 96 12
    CLC                        ; $129C: 18
    LDA #$8F                   ; $129D: A9 8F
    ADC #$0E                   ; $129F: 69 0E
    STA $129E                  ; $12A1: 8D 9E 12
    STA $D416                  ; $12A4: 8D 16 D4
L12A7:
    LDA $FD,X                  ; $12A7: B5 FD
    AND #$0F                   ; $12A9: 29 0F
    BEQ L12C7                  ; $12AB: F0 1A
    JSR L13E5                  ; $12AD: 20 E5 13
    JMP L1322                  ; $12B0: 4C 22 13

.org $12C7
L12C7:
    LDA $1141,X                ; $12C7: BD 41 11
    AND #$20                   ; $12CA: 29 20
    BNE L1322                  ; $12CC: D0 54
    LDA $FD,X                  ; $12CE: B5 FD
    AND #$10                   ; $12D0: 29 10
    BEQ L1322                  ; $12D2: F0 4E
    DEC $114D,X                ; $12D4: DE 4D 11
    BPL L1322                  ; $12D7: 10 49
    INC $114D,X                ; $12D9: FE 4D 11
    LDA $12BD,X                ; $12DC: BD BD 12
    AND #$03                   ; $12DF: 29 03
    TAY                        ; $12E1: A8
    LDA $12C3,Y                ; $12E2: B9 C3 12
    BNE L12FA                  ; $12E5: D0 13
    LDY $FC                    ; $12E7: A4 FC
    SEC                        ; $12E9: 38
    LDA $10CC,X                ; $12EA: BD CC 10
    SBC $155F,Y                ; $12ED: F9 5F 15
    STA $10CC,X                ; $12F0: 9D CC 10
    BCS L130D                  ; $12F3: B0 18
    DEC $10CF,X                ; $12F5: DE CF 10
    BNE L130D                  ; $12F8: D0 13
L12FA:
    LDY $FC                    ; $12FA: A4 FC
    CLC                        ; $12FC: 18
    LDA $10CC,X                ; $12FD: BD CC 10
    ADC $155F,Y                ; $1300: 79 5F 15
    STA $10CC,X                ; $1303: 9D CC 10
    BCC L130D                  ; $1306: 90 05
    INC $10CF,X                ; $1308: FE CF 10
    BCS L130D                  ; $130B: B0 00
L130D:
    INC $10DD,X                ; $130D: FE DD 10
    LDA $155E,Y                ; $1310: B9 5E 15
    AND #$0F                   ; $1313: 29 0F
    CMP $10DD,X                ; $1315: DD DD 10
    BNE L1322                  ; $1318: D0 08
    LDA #$00                   ; $131A: A9 00
    STA $10DD,X                ; $131C: 9D DD 10
    INC $12BD,X                ; $131F: FE BD 12
L1322:
    LDY $FC                    ; $1322: A4 FC
    LDA $155D,Y                ; $1324: B9 5D 15
    STA $FC                    ; $1327: 85 FC
    LDA $FD,X                  ; $1329: B5 FD
    AND #$40                   ; $132B: 29 40
    BEQ L1343                  ; $132D: F0 14
    CLC                        ; $132F: 18
    LDA $FC                    ; $1330: A5 FC
    ADC $13DC,X                ; $1332: 7D DC 13
    STA $13DC,X                ; $1335: 9D DC 13
    LDA $FC                    ; $1338: A5 FC
    ADC $13DF,X                ; $133A: 7D DF 13
    STA $13DF,X                ; $133D: 9D DF 13
    JMP L1385                  ; $1340: 4C 85 13
L1343:
    LDA $FD,X                  ; $1343: B5 FD
    AND #$20                   ; $1345: 29 20
    BEQ L1385                  ; $1347: F0 3C
    LDA $10E3,X                ; $1349: BD E3 10
    BEQ L135E                  ; $134C: F0 10
    CLC                        ; $134E: 18
    LDA $13DC,X                ; $134F: BD DC 13
    ADC $FC                    ; $1352: 65 FC
    STA $13DC,X                ; $1354: 9D DC 13
    BCC L136C                  ; $1357: 90 13
    INC $13DF,X                ; $1359: FE DF 13
    BCS L136C                  ; $135C: B0 0E
L135E:
    SEC                        ; $135E: 38
    LDA $13DC,X                ; $135F: BD DC 13
    SBC $FC                    ; $1362: E5 FC
    STA $13DC,X                ; $1364: 9D DC 13
    BCS L136C                  ; $1367: B0 03
    DEC $13DF,X                ; $1369: DE DF 13
L136C:
    INC $10E0,X                ; $136C: FE E0 10
    LDA $FC                    ; $136F: A5 FC
    AND #$0F                   ; $1371: 29 0F
    CMP $10E0,X                ; $1373: DD E0 10
    BNE L1385                  ; $1376: D0 0D
    LDA #$00                   ; $1378: A9 00
    STA $10E0,X                ; $137A: 9D E0 10
    LDA $10E3,X                ; $137D: BD E3 10
    EOR #$01                   ; $1380: 49 01
    STA $10E3,X                ; $1382: 9D E3 10
L1385:
    LDY $10C6,X                ; $1385: BC C6 10
    LDA $1084,X                ; $1388: BD 84 10
    STA $D404,Y                ; $138B: 99 04 D4
    LDA $13DF,X                ; $138E: BD DF 13
    STA $D403,Y                ; $1391: 99 03 D4
    LDA $13DC,X                ; $1394: BD DC 13
    STA $D402,Y                ; $1397: 99 02 D4
    LDA $1141,X                ; $139A: BD 41 11
    AND #$20                   ; $139D: 29 20
    BEQ L13CC                  ; $139F: F0 2B
    LDA $1147,X                ; $13A1: BD 47 11
    AND #$01                   ; $13A4: 29 01
    BEQ L13B2                  ; $13A6: F0 0A
    LDA $12B9,X                ; $13A8: BD B9 12
    EOR #$FF                   ; $13AB: 49 FF
    STA $12B9,X                ; $13AD: 9D B9 12
    BNE L13CC                  ; $13B0: D0 1A
L13B2:
    CLC                        ; $13B2: 18
    LDA $13E2,X                ; $13B3: BD E2 13
    ADC $1147,X                ; $13B6: 7D 47 11
    STA $13E2,X                ; $13B9: 9D E2 13
    STA SID_BASE,Y             ; $13BC: 99 00 D4
    LDA $12B6,X                ; $13BF: BD B6 12
    ADC $114A,X                ; $13C2: 7D 4A 11
    STA $12B6,X                ; $13C5: 9D B6 12
    STA $D401,Y                ; $13C8: 99 01 D4
    RTS                        ; $13CB: 60
L13CC:
    LDA $10CC,X                ; $13CC: BD CC 10
    STA SID_BASE,Y             ; $13CF: 99 00 D4
    LDA $10CF,X                ; $13D2: BD CF 10
    STA $D401,Y                ; $13D5: 99 01 D4
    RTS                        ; $13D8: 60

.org $13E5
L13E5:
    TAY                        ; $13E5: A8
    LDA $1498,Y                ; $13E6: B9 98 14
    STA $FA                    ; $13E9: 85 FA
    LDA $14A8,Y                ; $13EB: B9 A8 14
    STA $FB                    ; $13EE: 85 FB
    LDY $1144,X                ; $13F0: BC 44 11
    LDA ($FA),Y                ; $13F3: B1 FA
    AND $1031,X                ; $13F5: 3D 31 10
    STA $1084,X                ; $13F8: 9D 84 10
    INY                        ; $13FB: C8
    LDA ($FA),Y                ; $13FC: B1 FA
    BMI L1404                  ; $13FE: 30 04
    CLC                        ; $1400: 18
    ADC $10C9,X                ; $1401: 7D C9 10
L1404:
    AND #$7F                   ; $1404: 29 7F
    STA $1429                  ; $1406: 8D 29 14
    INY                        ; $1409: C8
    LDA ($FA),Y                ; $140A: B1 FA
    BEQ L1411                  ; $140C: F0 03
    STA $129E                  ; $140E: 8D 9E 12
L1411:
    INY                        ; $1411: C8
    LDA ($FA),Y                ; $1412: B1 FA
    CMP #$FE                   ; $1414: C9 FE
    BCC L1424                  ; $1416: 90 0C
    BEQ L141E                  ; $1418: F0 04
    LDY #$00                   ; $141A: A0 00
    BEQ L1424                  ; $141C: F0 06
L141E:
    LDA $FD,X                  ; $141E: B5 FD
    AND #$F0                   ; $1420: 29 F0
    STA $FD,X                  ; $1422: 95 FD
L1424:
    TYA                        ; $1424: 98
    STA $1144,X                ; $1425: 9D 44 11
    LDY #$3F                   ; $1428: A0 3F
    LDA $1437,Y                ; $142A: B9 37 14
    STA $10CC,X                ; $142D: 9D CC 10
    LDA $11C5,Y                ; $1430: B9 C5 11
    STA $10CF,X                ; $1433: 9D CF 10
    RTS                        ; $1436: 60

.org $1D70
intro_fire_exit:
    SEI                        ; $1D70: 78
    LDX #$17                   ; $1D71: A2 17
L1D73:
    LDA $1000,X                ; $1D73: BD 00 10
    STA $01,X                  ; $1D76: 95 01
    DEX                        ; $1D78: CA
    BPL L1D73                  ; $1D79: 10 F8
    JSR $FDA3                  ; $1D7B: 20 A3 FD
    JSR $FF5B                  ; $1D7E: 20 5B FF
    LDA #$00                   ; $1D81: A9 00
    STA $C6                    ; $1D83: 85 C6
    STA $0286                  ; $1D85: 8D 86 02
    STA VIC_BORDER             ; $1D88: 8D 20 D0
    STA VIC_BACKGROUND0        ; $1D8B: 8D 21 D0
    JSR $E544                  ; $1D8E: 20 44 E5
    LDA #$00                   ; $1D91: A9 00
    LDX #$18                   ; $1D93: A2 18
    LDY #$15                   ; $1D95: A0 15
    STY VIC_MEMPTR             ; $1D97: 8C 18 D0
L1D9A:
    STA SID_BASE,X             ; $1D9A: 9D 00 D4
    DEX                        ; $1D9D: CA
    BPL L1D9A                  ; $1D9E: 10 FA
    LDX #$38                   ; $1DA0: A2 38
L1DA2:
    LDA $1DC3,X                ; $1DA2: BD C3 1D
    STA $0400,X                ; $1DA5: 9D 00 04
    LDA #$00                   ; $1DA8: A9 00
    STA $D800,X                ; $1DAA: 9D 00 D8
    DEX                        ; $1DAD: CA
    BPL L1DA2                  ; $1DAE: 10 F2
    LDX #$4F                   ; $1DB0: A2 4F
L1DB2:
    LDA #$03                   ; $1DB2: A9 03
    STA $D9B8,X                ; $1DB4: 9D B8 D9
    LDA $1E00,X                ; $1DB7: BD 00 1E
    STA $05B8,X                ; $1DBA: 9D B8 05
    DEX                        ; $1DBD: CA
    BPL L1DB2                  ; $1DBE: 10 F2
    JMP $0400                  ; $1DC0: 4C 00 04

.org $4100
intro_start:
    LDX #$17                   ; $4100: A2 17
L4102:
    LDA $01,X                  ; $4102: B5 01
    STA $1000,X                ; $4104: 9D 00 10
    DEX                        ; $4107: CA
    BPL L4102                  ; $4108: 10 F8
    LDA #$06                   ; $410A: A9 06
    LDX #$54                   ; $410C: A2 54
    LDY #$48                   ; $410E: A0 48
    STX $14                    ; $4110: 86 14
    STY $15                    ; $4112: 84 15
    JSR $E536                  ; $4114: 20 36 E5
    LDX #$00                   ; $4117: A2 00
L4119:
    LDY #$08                   ; $4119: A0 08
    LDA #$80                   ; $411B: A9 80
L411D:
    STA $1B70,X                ; $411D: 9D 70 1B
    LSR A                      ; $4120: 4A
    INX                        ; $4121: E8
    CPX #$80                   ; $4122: E0 80
    BEQ L412C                  ; $4124: F0 06
    DEY                        ; $4126: 88
    BEQ L4119                  ; $4127: F0 F0
    JMP L411D                  ; $4129: 4C 1D 41
L412C:
    LDX #$00                   ; $412C: A2 00
L412E:
    LDY #$08                   ; $412E: A0 08
    LDA #$00                   ; $4130: A9 00
L4132:
    STA $1BF0,X                ; $4132: 9D F0 1B
    INX                        ; $4135: E8
    CPX #$80                   ; $4136: E0 80
    BEQ L4148                  ; $4138: F0 0E
    DEY                        ; $413A: 88
    BNE L4132                  ; $413B: D0 F5
    LDA $4131                  ; $413D: AD 31 41
    EOR #$80                   ; $4140: 49 80
    STA $4131                  ; $4142: 8D 31 41
    JMP L412E                  ; $4145: 4C 2E 41
L4148:
    LDX #$00                   ; $4148: A2 00
L414A:
    LDY #$10                   ; $414A: A0 10
L414C:
    LDA #$20                   ; $414C: A9 20
    STA $1C70,X                ; $414E: 9D 70 1C
    LDA #$28                   ; $4151: A9 28
    STA $1CF0,X                ; $4153: 9D F0 1C
    INX                        ; $4156: E8
    CPX #$80                   ; $4157: E0 80
    BEQ L4167                  ; $4159: F0 0C
    DEY                        ; $415B: 88
    BNE L414C                  ; $415C: D0 EE
    INC $414D                  ; $415E: EE 4D 41
    INC $4152                  ; $4161: EE 52 41
    JMP L414A                  ; $4164: 4C 4A 41
L4167:
    LDX #$0F                   ; $4167: A2 0F
L4169:
    LDY #$00                   ; $4169: A0 00
    LDA #$33                   ; $416B: A9 33
L416D:
    STA $0428,X                ; $416D: 9D 28 04
    CLC                        ; $4170: 18
    ADC #$01                   ; $4171: 69 01
    STA $0450,X                ; $4173: 9D 50 04
    ADC #$01                   ; $4176: 69 01
    STA $0478,X                ; $4178: 9D 78 04
    ADC #$01                   ; $417B: 69 01
    STA $04A0,X                ; $417D: 9D A0 04
    ADC #$01                   ; $4180: 69 01
    STA $04C8,X                ; $4182: 9D C8 04
    ADC #$01                   ; $4185: 69 01
    STA $04F0,X                ; $4187: 9D F0 04
    ADC #$01                   ; $418A: 69 01
    STA $0518,X                ; $418C: 9D 18 05
    ADC #$01                   ; $418F: 69 01
    STA $0540,X                ; $4191: 9D 40 05
    ADC #$01                   ; $4194: 69 01
    STA $0568,X                ; $4196: 9D 68 05
    ADC #$01                   ; $4199: 69 01
    STA $0590,X                ; $419B: 9D 90 05
    ADC #$07                   ; $419E: 69 07
    INY                        ; $41A0: C8
    CPY #$0B                   ; $41A1: C0 0B
    BEQ L4169                  ; $41A3: F0 C4
    INX                        ; $41A5: E8
    CPX #$19                   ; $41A6: E0 19
    BNE L416D                  ; $41A8: D0 C3
    LDX #$00                   ; $41AA: A2 00
    LDA #$08                   ; $41AC: A9 08
L41AE:
    STA $D990,X                ; $41AE: 9D 90 D9
    STA $DA90,X                ; $41B1: 9D 90 DA
    STA $DB00,X                ; $41B4: 9D 00 DB
    INX                        ; $41B7: E8
    BNE L41AE                  ; $41B8: D0 F4
    SEI                        ; $41BA: 78
    LDA #$35                   ; $41BB: A9 35
    LDX #$01                   ; $41BD: A2 01
    LDY #$7F                   ; $41BF: A0 7F
    STA $01                    ; $41C1: 85 01
    STX VIC_IRQ_MASK           ; $41C3: 8E 1A D0
    STY CIA1_IRQ_CONTROL       ; $41C6: 8C 0D DC
    LDA #$00                   ; $41C9: A9 00
    JSR music_init             ; $41CB: 20 48 10
    LDX #$24                   ; $41CE: A2 24
    LDY #$42                   ; $41D0: A0 42
    STX NMI_VECTOR             ; $41D2: 8E FA FF
    STY $FFFB                  ; $41D5: 8C FB FF
    LDA #$EE                   ; $41D8: A9 EE
    LDX #$41                   ; $41DA: A2 41
    STA IRQ_VECTOR             ; $41DC: 8D FE FF
    STX $FFFF                  ; $41DF: 8E FF FF
    JSR vic_restore            ; $41E2: 20 DA 42
    LDA #$31                   ; $41E5: A9 31
    STA VIC_RASTER             ; $41E7: 8D 12 D0
    CLI                        ; $41EA: 58
    JMP intro_main             ; $41EB: 4C DC 46
intro_irq_dispatch:
    STA $11                    ; $41EE: 85 11
    STX $12                    ; $41F0: 86 12
    STY $13                    ; $41F2: 84 13
    LDX $42E3                  ; $41F4: AE E3 42
    CPX #$09                   ; $41F7: E0 09
    BNE L4200                  ; $41F9: D0 05
    LDX #$00                   ; $41FB: A2 00
    STX $42E3                  ; $41FD: 8E E3 42
L4200:
    LDA $4225,X                ; $4200: BD 25 42
    STA VIC_RASTER             ; $4203: 8D 12 D0
    LDA $4226,X                ; $4206: BD 26 42
    LDY $4227,X                ; $4209: BC 27 42
    STA $4219                  ; $420C: 8D 19 42
    STY $421A                  ; $420F: 8C 1A 42
    INX                        ; $4212: E8
    INX                        ; $4213: E8
    INX                        ; $4214: E8
    STX $42E3                  ; $4215: 8E E3 42
    JSR $FFFF                  ; $4218: 20 FF FF
    ROR VIC_IRQ_FLAGS          ; $421B: 6E 19 D0
    LDA $11                    ; $421E: A5 11
    LDX $12                    ; $4220: A6 12
    LDY $13                    ; $4222: A4 13
    RTI                        ; $4224: 40

.org $422E
irq_top:
    LDA #$00                   ; $422E: A9 00
    LDX #$C8                   ; $4230: A2 C8
    LDY #$19                   ; $4232: A0 19
    JSR set_border_background  ; $4234: 20 1B 48
    STX VIC_CTRL2              ; $4237: 8E 16 D0
    STY VIC_MEMPTR             ; $423A: 8C 18 D0
    RTS                        ; $423D: 60
fire_pressed:
    JMP intro_fire_exit        ; $423E: 4C 70 1D
irq_middle:
    LDX #$01                   ; $4241: A2 01
    JSR delay_short            ; $4243: 20 86 47
    NOP                        ; $4246: EA
    NOP                        ; $4247: EA
    LDA #$0E                   ; $4248: A9 0E
    LDX #$01                   ; $424A: A2 01
    JSR delay_short            ; $424C: 20 86 47
    JSR set_border_background  ; $424F: 20 1B 48
    LDA #$06                   ; $4252: A9 06
    JSR set_border_background  ; $4254: 20 1B 48
    JSR music_play             ; $4257: 20 21 10
    JSR color_scroll           ; $425A: 20 93 47
    LDA #$EF                   ; $425D: A9 EF
    CMP CIA1_PORT_B            ; $425F: CD 01 DC
    BEQ fire_pressed           ; $4262: F0 DA
    DEC $42E0                  ; $4264: CE E0 42
    LDA $42E0                  ; $4267: AD E0 42
    BNE L4280                  ; $426A: D0 14
    LDA #$02                   ; $426C: A9 02
    STA $42E0                  ; $426E: 8D E0 42
    LDA #$01                   ; $4271: A9 01
    STA $42E5                  ; $4273: 8D E5 42
    LDA $42E6                  ; $4276: AD E6 42
    BEQ L4280                  ; $4279: F0 05
    LDA #$01                   ; $427B: A9 01
    STA $42E7                  ; $427D: 8D E7 42
L4280:
    RTS                        ; $4280: 60
irq_bottom:
    LDX #$01                   ; $4281: A2 01
    JSR delay_short            ; $4283: 20 86 47
    NOP                        ; $4286: EA
    NOP                        ; $4287: EA
    LDA #$0B                   ; $4288: A9 0B
    LDX #$01                   ; $428A: A2 01
    JSR delay_short            ; $428C: 20 86 47
    JSR set_border_background  ; $428F: 20 1B 48
    LDA #$00                   ; $4292: A9 00
    JSR set_border_background  ; $4294: 20 1B 48
    LDA #$D8                   ; $4297: A9 D8
    LDX #$12                   ; $4299: A2 12
    STA VIC_CTRL2              ; $429B: 8D 16 D0
    STX VIC_MEMPTR             ; $429E: 8E 18 D0
    LDX #$01                   ; $42A1: A2 01
    LDY #$0C                   ; $42A3: A0 0C
    STX VIC_BACKGROUND1        ; $42A5: 8E 22 D0
    STY VIC_BACKGROUND2        ; $42A8: 8C 23 D0
    LDX #$02                   ; $42AB: A2 02
    JSR delay_long             ; $42AD: 20 8C 47
    LDA VIC_RASTER             ; $42B0: AD 12 D0
    CLC                        ; $42B3: 18
    ADC #$05                   ; $42B4: 69 05
L42B6:
    CMP VIC_RASTER             ; $42B6: CD 12 D0
    BNE L42B6                  ; $42B9: D0 FB
    LDX #$00                   ; $42BB: A2 00
    LDY VIC_RASTER             ; $42BD: AC 12 D0
L42C0:
    INY                        ; $42C0: C8
    LDA $4300,X                ; $42C1: BD 00 43
L42C4:
    CPY VIC_RASTER             ; $42C4: CC 12 D0
    BNE L42C4                  ; $42C7: D0 FB
    STA VIC_CTRL1              ; $42C9: 8D 11 D0
    INX                        ; $42CC: E8
    CPX #$60                   ; $42CD: E0 60
    BNE L42C0                  ; $42CF: D0 EF
    LDY VIC_RASTER             ; $42D1: AC 12 D0
    INY                        ; $42D4: C8
L42D5:
    CPY VIC_RASTER             ; $42D5: CC 12 D0
    BNE L42D5                  ; $42D8: D0 FB
vic_restore:
    LDA #$1B                   ; $42DA: A9 1B
    STA VIC_CTRL1              ; $42DC: 8D 11 D0
    RTS                        ; $42DF: 60

.org $44A8
L44A8:
    AND #$3F                   ; $44A8: 29 3F
    STA $426D                  ; $44AA: 8D 6D 42
    JSR L452D                  ; $44AD: 20 2D 45
    RTS                        ; $44B0: 60
L44B1:
    JSR L452D                  ; $44B1: 20 2D 45
    LDX #$00                   ; $44B4: A2 00
    LDY #$00                   ; $44B6: A0 00
L44B8:
    LDA ($14),Y                ; $44B8: B1 14
    BEQ L44C4                  ; $44BA: F0 08
    CMP #$1F                   ; $44BC: C9 1F
    BEQ L44C4                  ; $44BE: F0 04
    INY                        ; $44C0: C8
    INX                        ; $44C1: E8
    BNE L44B8                  ; $44C2: D0 F4
L44C4:
    TXA                        ; $44C4: 8A
    ASL A                      ; $44C5: 0A
    STA $42EE                  ; $44C6: 8D EE 42
    LDA #$28                   ; $44C9: A9 28
    SEC                        ; $44CB: 38
    SBC $42EE                  ; $44CC: ED EE 42
    LSR A                      ; $44CF: 4A
    STA $42E4                  ; $44D0: 8D E4 42
    RTS                        ; $44D3: 60
intro_routine_44d4:
    LDA $42E5                  ; $44D4: AD E5 42
    BEQ L4533                  ; $44D7: F0 5A
    LDA #$00                   ; $44D9: A9 00
    TAY                        ; $44DB: A8
    STA $42E5                  ; $44DC: 8D E5 42
    LDA ($14),Y                ; $44DF: B1 14
    CMP #$41                   ; $44E1: C9 41
    BMI L44E8                  ; $44E3: 30 03
    JMP L44A8                  ; $44E5: 4C A8 44
L44E8:
    CMP #$1C                   ; $44E8: C9 1C
    BEQ L44B1                  ; $44EA: F0 C5
    CMP #$1F                   ; $44EC: C9 1F
    BEQ L4548                  ; $44EE: F0 58
    CMP #$00                   ; $44F0: C9 00
    BEQ L4534                  ; $44F2: F0 40
    LDY $42E4                  ; $44F4: AC E4 42
    PHA                        ; $44F7: 48
    TYA                        ; $44F8: 98
    PHA                        ; $44F9: 48
    LDX $42E8                  ; $44FA: AE E8 42
    LDA $449C,X                ; $44FD: BD 9C 44
    LDY $449D,X                ; $4500: BC 9D 44
    STA $16                    ; $4503: 85 16
    STY $17                    ; $4505: 84 17
    PLA                        ; $4507: 68
    TAY                        ; $4508: A8
    PLA                        ; $4509: 68
    STA ($16),Y                ; $450A: 91 16
    CLC                        ; $450C: 18
    ADC #$40                   ; $450D: 69 40
    INY                        ; $450F: C8
    STA ($16),Y                ; $4510: 91 16
    PHA                        ; $4512: 48
    LDA $16                    ; $4513: A5 16
    ADC #$28                   ; $4515: 69 28
    STA $16                    ; $4517: 85 16
    BCC L451D                  ; $4519: 90 02
    INC $17                    ; $451B: E6 17
L451D:
    PLA                        ; $451D: 68
    CLC                        ; $451E: 18
    ADC #$40                   ; $451F: 69 40
    DEY                        ; $4521: 88
    STA ($16),Y                ; $4522: 91 16
    ADC #$40                   ; $4524: 69 40
    INY                        ; $4526: C8
    STA ($16),Y                ; $4527: 91 16
    INY                        ; $4529: C8
    STY $42E4                  ; $452A: 8C E4 42
L452D:
    INC $14                    ; $452D: E6 14
    BNE L4533                  ; $452F: D0 02
    INC $15                    ; $4531: E6 15
L4533:
    RTS                        ; $4533: 60
L4534:
    LDA #$54                   ; $4534: A9 54
    LDX #$48                   ; $4536: A2 48
    LDY #$00                   ; $4538: A0 00
    STA $14                    ; $453A: 85 14
    STX $15                    ; $453C: 86 15
    STY $42E4                  ; $453E: 8C E4 42
    STY $42E8                  ; $4541: 8C E8 42
    JSR L4579                  ; $4544: 20 79 45
    RTS                        ; $4547: 60
L4548:
    LDA #$00                   ; $4548: A9 00
    STA $42E4                  ; $454A: 8D E4 42
    LDX $42E8                  ; $454D: AE E8 42
    INX                        ; $4550: E8
    INX                        ; $4551: E8
    CPX #$0C                   ; $4552: E0 0C
    BEQ L4567                  ; $4554: F0 11
    STX $42E8                  ; $4556: 8E E8 42
    LDA $449C,X                ; $4559: BD 9C 44
    LDY $449D,X                ; $455C: BC 9D 44
    STA $16                    ; $455F: 85 16
    STY $17                    ; $4561: 84 17
    JSR L452D                  ; $4563: 20 2D 45
    RTS                        ; $4566: 60
L4567:
    LDX #$00                   ; $4567: A2 00
    LDA $449C,X                ; $4569: BD 9C 44
    LDY $449D,X                ; $456C: BC 9D 44
    STA $16                    ; $456F: 85 16
    STY $17                    ; $4571: 84 17
    STX $42E8                  ; $4573: 8E E8 42
    JSR L452D                  ; $4576: 20 2D 45
L4579:
    LDA $42E0                  ; $4579: AD E0 42
    LDX #$A0                   ; $457C: A2 A0
    LDY #$01                   ; $457E: A0 01
    STA $42EF                  ; $4580: 8D EF 42
    STX $42E0                  ; $4583: 8E E0 42
    STY $42E6                  ; $4586: 8C E6 42
    RTS                        ; $4589: 60
intro_routine_458a:
    LDX #$00                   ; $458A: A2 00
    LDA #$20                   ; $458C: A9 20
L458E:
    STA $0608,X                ; $458E: 9D 08 06
    INX                        ; $4591: E8
    BNE L458E                  ; $4592: D0 FA
L4594:
    STA $0708,X                ; $4594: 9D 08 07
    INX                        ; $4597: E8
    CPX #$EF                   ; $4598: E0 EF
    BNE L4594                  ; $459A: D0 F8
    RTS                        ; $459C: 60
intro_routine_459d:
    LDA #$00                   ; $459D: A9 00
    STA $0E                    ; $459F: 85 0E
    STA $0F                    ; $45A1: 85 0F
    LDA $08                    ; $45A3: A5 08
    SEC                        ; $45A5: 38
    SBC $06                    ; $45A6: E5 06
    BCC L45B7                  ; $45A8: 90 0D
    STA $0A                    ; $45AA: 85 0A
    LDA #$E8                   ; $45AC: A9 E8
    STA $4636                  ; $45AE: 8D 36 46
    STA $4617                  ; $45B1: 8D 17 46
    JMP L45C5                  ; $45B4: 4C C5 45
L45B7:
    EOR #$FF                   ; $45B7: 49 FF
    ADC #$01                   ; $45B9: 69 01
    STA $0A                    ; $45BB: 85 0A
    LDA #$CA                   ; $45BD: A9 CA
    STA $4636                  ; $45BF: 8D 36 46
    STA $4617                  ; $45C2: 8D 17 46
L45C5:
    LDA $09                    ; $45C5: A5 09
    SEC                        ; $45C7: 38
    SBC $07                    ; $45C8: E5 07
    BCC L45D9                  ; $45CA: 90 0D
    STA $0B                    ; $45CC: 85 0B
    LDA #$C8                   ; $45CE: A9 C8
    STA $4646                  ; $45D0: 8D 46 46
    STA $4607                  ; $45D3: 8D 07 46
    JMP L45E7                  ; $45D6: 4C E7 45
L45D9:
    EOR #$FF                   ; $45D9: 49 FF
    ADC #$01                   ; $45DB: 69 01
    STA $0B                    ; $45DD: 85 0B
    LDA #$88                   ; $45DF: A9 88
    STA $4646                  ; $45E1: 8D 46 46
    STA $4607                  ; $45E4: 8D 07 46
L45E7:
    LDA $0B                    ; $45E7: A5 0B
    CMP $0A                    ; $45E9: C5 0A
    BCC L461D                  ; $45EB: 90 30
    SEC                        ; $45ED: 38
    SBC #$01                   ; $45EE: E9 01
    STA $0D                    ; $45F0: 85 0D
    LDX $06                    ; $45F2: A6 06
    LDY $07                    ; $45F4: A4 07
L45F6:
    LDA $1BF0,X                ; $45F6: BD F0 1B
    STA $02                    ; $45F9: 85 02
    LDA $1C70,X                ; $45FB: BD 70 1C
    STA $03                    ; $45FE: 85 03
    LDA $1B70,X                ; $4600: BD 70 1B
    ORA ($02),Y                ; $4603: 11 02
    STA ($02),Y                ; $4605: 91 02
    INY                        ; $4607: C8
    LDA $0E                    ; $4608: A5 0E
    CLC                        ; $460A: 18
    ADC $0A                    ; $460B: 65 0A
    STA $0E                    ; $460D: 85 0E
    CMP $0B                    ; $460F: C5 0B
    BCC L4618                  ; $4611: 90 05
    SBC $0B                    ; $4613: E5 0B
    STA $0E                    ; $4615: 85 0E
    INX                        ; $4617: E8
L4618:
    DEC $0D                    ; $4618: C6 0D
    BPL L45F6                  ; $461A: 10 DA
    RTS                        ; $461C: 60
L461D:
    LDA $0A                    ; $461D: A5 0A
    STA $0D                    ; $461F: 85 0D
    LDX $06                    ; $4621: A6 06
    LDY $07                    ; $4623: A4 07
L4625:
    LDA $1BF0,X                ; $4625: BD F0 1B
    STA $02                    ; $4628: 85 02
    LDA $1C70,X                ; $462A: BD 70 1C
    STA $03                    ; $462D: 85 03
    LDA $1B70,X                ; $462F: BD 70 1B
    ORA ($02),Y                ; $4632: 11 02
    STA ($02),Y                ; $4634: 91 02
    INX                        ; $4636: E8
    LDA $0F                    ; $4637: A5 0F
    CLC                        ; $4639: 18
    ADC $0B                    ; $463A: 65 0B
    STA $0F                    ; $463C: 85 0F
    CMP $0A                    ; $463E: C5 0A
    BCC L4647                  ; $4640: 90 05
    SBC $0A                    ; $4642: E5 0A
    STA $0F                    ; $4644: 85 0F
    INY                        ; $4646: C8
L4647:
    DEC $0D                    ; $4647: C6 0D
    BNE L4625                  ; $4649: D0 DA
    RTS                        ; $464B: 60
intro_routine_464c:
    LDA $0C                    ; $464C: A5 0C
    BNE L4670                  ; $464E: D0 20
    LDA #$19                   ; $4650: A9 19
    STA $4233                  ; $4652: 8D 33 42
    STA VIC_MEMPTR             ; $4655: 8D 18 D0
    LDA #$01                   ; $4658: A9 01
    STA $0C                    ; $465A: 85 0C
    JSR L46B6                  ; $465C: 20 B6 46
    LDA #$F0                   ; $465F: A9 F0
    STA $462B                  ; $4661: 8D 2B 46
    STA $45FC                  ; $4664: 8D FC 45
    LDA #$1C                   ; $4667: A9 1C
    STA $462C                  ; $4669: 8D 2C 46
    STA $45FD                  ; $466C: 8D FD 45
    RTS                        ; $466F: 60
L4670:
    LDA #$1B                   ; $4670: A9 1B
    STA $4233                  ; $4672: 8D 33 42
    STA VIC_MEMPTR             ; $4675: 8D 18 D0
    LDA #$00                   ; $4678: A9 00
    STA $0C                    ; $467A: 85 0C
    JSR L4690                  ; $467C: 20 90 46
    LDA #$70                   ; $467F: A9 70
    STA $462B                  ; $4681: 8D 2B 46
    STA $45FC                  ; $4684: 8D FC 45
    LDA #$1C                   ; $4687: A9 1C
    STA $462C                  ; $4689: 8D 2C 46
    STA $45FD                  ; $468C: 8D FD 45
    RTS                        ; $468F: 60
L4690:
    LDX #$50                   ; $4690: A2 50
    LDA #$00                   ; $4692: A9 00
L4694:
    STA $2198,X                ; $4694: 9D 98 21
    STA $2218,X                ; $4697: 9D 18 22
    STA $2298,X                ; $469A: 9D 98 22
    STA $2318,X                ; $469D: 9D 18 23
    STA $2398,X                ; $46A0: 9D 98 23
    STA $2418,X                ; $46A3: 9D 18 24
    STA $2498,X                ; $46A6: 9D 98 24
    STA $2518,X                ; $46A9: 9D 18 25
    STA $2598,X                ; $46AC: 9D 98 25
    STA $2618,X                ; $46AF: 9D 18 26
    DEX                        ; $46B2: CA
    BPL L4694                  ; $46B3: 10 DF
    RTS                        ; $46B5: 60
L46B6:
    LDX #$50                   ; $46B6: A2 50
    LDA #$00                   ; $46B8: A9 00
L46BA:
    STA $2998,X                ; $46BA: 9D 98 29
    STA $2A18,X                ; $46BD: 9D 18 2A
    STA $2A98,X                ; $46C0: 9D 98 2A
    STA $2B18,X                ; $46C3: 9D 18 2B
    STA $2B98,X                ; $46C6: 9D 98 2B
    STA $2C18,X                ; $46C9: 9D 18 2C
    STA $2C98,X                ; $46CC: 9D 98 2C
    STA $2D18,X                ; $46CF: 9D 18 2D
    STA $2D98,X                ; $46D2: 9D 98 2D
    STA $2E18,X                ; $46D5: 9D 18 2E
    DEX                        ; $46D8: CA
    BPL L46BA                  ; $46D9: 10 DF
    RTS                        ; $46DB: 60
intro_main:
    LDA #$00                   ; $46DC: A9 00
    STA $4700                  ; $46DE: 8D 00 47
    JSR intro_routine_464c     ; $46E1: 20 4C 46
    JSR intro_routine_464c     ; $46E4: 20 4C 46
    LDA #$0F                   ; $46E7: A9 0F
    STA $10                    ; $46E9: 85 10
    LDA $42E2                  ; $46EB: AD E2 42
    STA $46F8                  ; $46EE: 8D F8 46
    LDA $42E1                  ; $46F1: AD E1 42
    STA $46FC                  ; $46F4: 8D FC 46
L46F7:
    LDA #$00                   ; $46F7: A9 00
    STA $04                    ; $46F9: 85 04
    LDA #$30                   ; $46FB: A9 30
    STA $05                    ; $46FD: 85 05
L46FF:
    LDY #$01                   ; $46FF: A0 01
    BNE intro_main             ; $4701: D0 D9
    LDA ($04),Y                ; $4703: B1 04
    BMI L46F7                  ; $4705: 30 F0
    STA $06                    ; $4707: 85 06
    INY                        ; $4709: C8
    LDA ($04),Y                ; $470A: B1 04
    STA $07                    ; $470C: 85 07
    INY                        ; $470E: C8
    LDA ($04),Y                ; $470F: B1 04
    STA $08                    ; $4711: 85 08
    INY                        ; $4713: C8
    LDA ($04),Y                ; $4714: B1 04
    STA $09                    ; $4716: 85 09
    LDA $04                    ; $4718: A5 04
    CLC                        ; $471A: 18
    ADC #$04                   ; $471B: 69 04
    STA $04                    ; $471D: 85 04
    BCC L4723                  ; $471F: 90 02
    INC $05                    ; $4721: E6 05
L4723:
    LDA $42E7                  ; $4723: AD E7 42
    BEQ L4772                  ; $4726: F0 4A
    JSR scroll_divider         ; $4728: 20 22 48
    LDY #$00                   ; $472B: A0 00
    LDX $42E9                  ; $472D: AE E9 42
    LDA $4360,X                ; $4730: BD 60 43
    STA $435F                  ; $4733: 8D 5F 43
L4736:
    LDA $4301,Y                ; $4736: B9 01 43
    STA $4300,Y                ; $4739: 99 00 43
    INY                        ; $473C: C8
    CPY #$5F                   ; $473D: C0 5F
    BNE L4736                  ; $473F: D0 F5
    INC $42E9                  ; $4741: EE E9 42
    LDA $42E9                  ; $4744: AD E9 42
    CMP #$C7                   ; $4747: C9 C7
    BNE L4775                  ; $4749: D0 2A
    JSR intro_routine_458a     ; $474B: 20 8A 45
    LDY $42EA                  ; $474E: AC EA 42
    LDA $4490,Y                ; $4751: B9 90 44
    LDX $4496,Y                ; $4754: BE 96 44
    STA $42A2                  ; $4757: 8D A2 42
    STX $42A4                  ; $475A: 8E A4 42
    INC $42EA                  ; $475D: EE EA 42
    LDA $42EA                  ; $4760: AD EA 42
    CMP #$06                   ; $4763: C9 06
    BNE L476C                  ; $4765: D0 05
    LDA #$00                   ; $4767: A9 00
    STA $42EA                  ; $4769: 8D EA 42
L476C:
    JSR reset_raster_table     ; $476C: 20 35 48
    JSR reset_intro_state      ; $476F: 20 42 48
L4772:
    JSR intro_routine_44d4     ; $4772: 20 D4 44
L4775:
    JSR intro_routine_459d     ; $4775: 20 9D 45
    DEC $10                    ; $4778: C6 10
    BNE L46FF                  ; $477A: D0 83
    JSR intro_routine_464c     ; $477C: 20 4C 46
    LDA #$0F                   ; $477F: A9 0F
    STA $10                    ; $4781: 85 10
    JMP L46FF                  ; $4783: 4C FF 46
delay_short:
    DEX                        ; $4786: CA
    NOP                        ; $4787: EA
    BNE delay_short            ; $4788: D0 FC
    NOP                        ; $478A: EA
    RTS                        ; $478B: 60
delay_long:
    DEX                        ; $478C: CA
    NOP                        ; $478D: EA
    BNE delay_long             ; $478E: D0 FC
    BIT $24                    ; $4790: 24 24
    RTS                        ; $4792: 60
color_scroll:
    INC $42ED                  ; $4793: EE ED 42
    LDA $42ED                  ; $4796: AD ED 42
    CMP #$02                   ; $4799: C9 02
    BEQ L479E                  ; $479B: F0 01
    RTS                        ; $479D: 60
L479E:
    LDA #$00                   ; $479E: A9 00
    STA $42ED                  ; $47A0: 8D ED 42
    LDA $42EC                  ; $47A3: AD EC 42
    CLC                        ; $47A6: 18
    ADC #$01                   ; $47A7: 69 01
    STA $42EC                  ; $47A9: 8D EC 42
    CMP #$67                   ; $47AC: C9 67
    BNE L47B5                  ; $47AE: D0 05
    LDX #$00                   ; $47B0: A2 00
    STX $42EC                  ; $47B2: 8E EC 42
L47B5:
    TAY                        ; $47B5: A8
    LDA $4428,Y                ; $47B6: B9 28 44
    STA $D841                  ; $47B9: 8D 41 D8
    STA $D86A                  ; $47BC: 8D 6A D8
    STA $D893                  ; $47BF: 8D 93 D8
    STA $D8BC                  ; $47C2: 8D BC D8
    STA $D8E5                  ; $47C5: 8D E5 D8
    STA $D90E                  ; $47C8: 8D 0E D9
    STA $D937                  ; $47CB: 8D 37 D9
    STA $D960                  ; $47CE: 8D 60 D9
    STA $D989                  ; $47D1: 8D 89 D9
    STA $D9B2                  ; $47D4: 8D B2 D9
    LDX #$0F                   ; $47D7: A2 0F
L47D9:
    LDA $D829,X                ; $47D9: BD 29 D8
    STA $D828,X                ; $47DC: 9D 28 D8
    LDA $D851,X                ; $47DF: BD 51 D8
    STA $D850,X                ; $47E2: 9D 50 D8
    LDA $D879,X                ; $47E5: BD 79 D8
    STA $D878,X                ; $47E8: 9D 78 D8
    LDA $D8A1,X                ; $47EB: BD A1 D8
    STA $D8A0,X                ; $47EE: 9D A0 D8
    LDA $D8C9,X                ; $47F1: BD C9 D8
    STA $D8C8,X                ; $47F4: 9D C8 D8
    LDA $D8F1,X                ; $47F7: BD F1 D8
    STA $D8F0,X                ; $47FA: 9D F0 D8
    LDA $D919,X                ; $47FD: BD 19 D9
    STA $D918,X                ; $4800: 9D 18 D9
    LDA $D941,X                ; $4803: BD 41 D9
    STA $D940,X                ; $4806: 9D 40 D9
    LDA $D969,X                ; $4809: BD 69 D9
    STA $D968,X                ; $480C: 9D 68 D9
    LDA $D991,X                ; $480F: BD 91 D9
    STA $D990,X                ; $4812: 9D 90 D9
    INX                        ; $4815: E8
    CPX #$22                   ; $4816: E0 22
    BNE L47D9                  ; $4818: D0 BF
    RTS                        ; $481A: 60
set_border_background:
    STA VIC_BORDER             ; $481B: 8D 20 D0
    STA VIC_BACKGROUND0        ; $481E: 8D 21 D0
    RTS                        ; $4821: 60
scroll_divider:
    INC $42EB                  ; $4822: EE EB 42
    LDA $42EB                  ; $4825: AD EB 42
    CMP #$03                   ; $4828: C9 03
    BNE L4832                  ; $482A: D0 06
    LDA #$00                   ; $482C: A9 00
    STA $42EB                  ; $482E: 8D EB 42
    RTS                        ; $4831: 60
L4832:
    JMP L4775                  ; $4832: 4C 75 47
reset_raster_table:
    LDX #$00                   ; $4835: A2 00
    LDA #$1B                   ; $4837: A9 1B
L4839:
    STA $4300,X                ; $4839: 9D 00 43
    INX                        ; $483C: E8
    CPX #$60                   ; $483D: E0 60
    BNE L4839                  ; $483F: D0 F8
    RTS                        ; $4841: 60
reset_intro_state:
    LDA #$00                   ; $4842: A9 00
    STA $42E6                  ; $4844: 8D E6 42
    STA $42E7                  ; $4847: 8D E7 42
    STA $42E9                  ; $484A: 8D E9 42
    LDA $42EF                  ; $484D: AD EF 42
    STA $42E0                  ; $4850: 8D E0 42
    RTS                        ; $4853: 60

; ==================== IRQ-TABELLE ====================

.org $4225
intro_irq_table:
    .byte $31, <$422E, >$422E ; Raster $31 -> irq_top
    .byte $91, <$4241, >$4241 ; Raster $91 -> irq_middle
    .byte $0D, <$4281, >$4281 ; Raster $0D -> irq_bottom

; ==================== INTRO-TEXT ====================

; C
; DEARLY BELOVED WE
; ARE GATHERED HERE
; TODAY TO PRESENT:
; E
; DALEK ATTACK
; C
; BASED ON THE
; FAMOUS DR. WHO
; CHARACTER.
; CRACKED BY
; L E G E N D
; AND RELEASED BY
; T . S . M
; ON THE 5TH OF
; DECEMBER 1992
; C
; THERE WAS SOME
; LAME CODING IN THE
; GAME THAT WOULD
; THROW THE C-128
; INTO 2 MHZ MODE BUT
; THAT HAS BEEN TAKEN
; CARE OF IN THIS
; RELEASE, SO IF YOU
; BUY THE ORIGINAL
; YOU'LL HAVE A
; BUGGED GAME.
; D
; SANTA SENDS OUT SOME
; EARLY HO HO HO'S TO
; C
; THE FOLLOWING GOOD
; BOYS AND GIRLYMEN.
; A<<1B> L E G E N D <1D>>
; ARCADE * CHROMANCE
; DOMINATORS * ENIGMA
; F4CG * NEI
; RED SECTOR INC.
; SUCCESS * TALENT
; A
; FOR THE LATEST AND
; GREATEST CALL THE
; TSM & LEGEND WHQ
; J
; (402) 734-3634

.org $4854
intro_screen_code_text:
    .byte $43, $1F, $1C, $04, $05, $01, $12, $0C, $19, $20, $02, $05, $0C, $0F, $16, $05  ; $4854
    .byte $04, $20, $17, $05, $1F, $1F, $1C, $01, $12, $05, $20, $07, $01, $14, $08, $05  ; $4864
    .byte $12, $05, $04, $20, $08, $05, $12, $05, $1F, $1F, $1C, $14, $0F, $04, $01, $19  ; $4874
    .byte $20, $14, $0F, $20, $10, $12, $05, $13, $05, $0E, $14, $3A, $1F, $45, $1F, $1C  ; $4884
    .byte $04, $01, $0C, $05, $0B, $20, $01, $14, $14, $01, $03, $0B, $1F, $43, $1F, $1C  ; $4894
    .byte $02, $01, $13, $05, $04, $20, $0F, $0E, $20, $14, $08, $05, $1F, $1C, $06, $01  ; $48A4
    .byte $0D, $0F, $15, $13, $20, $04, $12, $2E, $20, $17, $08, $0F, $1F, $1C, $03, $08  ; $48B4
    .byte $01, $12, $01, $03, $14, $05, $12, $2E, $1F, $1C, $03, $12, $01, $03, $0B, $05  ; $48C4
    .byte $04, $20, $02, $19, $1F, $1C, $0C, $20, $05, $20, $07, $20, $05, $20, $0E, $20  ; $48D4
    .byte $04, $1F, $1C, $01, $0E, $04, $20, $12, $05, $0C, $05, $01, $13, $05, $04, $20  ; $48E4
    .byte $02, $19, $1F, $1C, $14, $20, $2E, $20, $13, $20, $2E, $20, $0D, $1F, $1C, $0F  ; $48F4
    .byte $0E, $20, $14, $08, $05, $20, $35, $14, $08, $20, $0F, $06, $1F, $1C, $04, $05  ; $4904
    .byte $03, $05, $0D, $02, $05, $12, $20, $31, $39, $39, $32, $1F, $43, $1C, $14, $08  ; $4914
    .byte $05, $12, $05, $20, $17, $01, $13, $20, $13, $0F, $0D, $05, $1F, $1C, $0C, $01  ; $4924
    .byte $0D, $05, $20, $03, $0F, $04, $09, $0E, $07, $20, $09, $0E, $20, $14, $08, $05  ; $4934
    .byte $1F, $1C, $07, $01, $0D, $05, $20, $14, $08, $01, $14, $20, $17, $0F, $15, $0C  ; $4944
    .byte $04, $1F, $1C, $14, $08, $12, $0F, $17, $20, $14, $08, $05, $20, $03, $2D, $31  ; $4954
    .byte $32, $38, $1F, $1C, $09, $0E, $14, $0F, $20, $32, $20, $0D, $08, $1A, $20, $0D  ; $4964
    .byte $0F, $04, $05, $20, $02, $15, $14, $1F, $1C, $14, $08, $01, $14, $20, $08, $01  ; $4974
    .byte $13, $20, $02, $05, $05, $0E, $20, $14, $01, $0B, $05, $0E, $1F, $1C, $03, $01  ; $4984
    .byte $12, $05, $20, $0F, $06, $20, $09, $0E, $20, $14, $08, $09, $13, $1F, $1C, $12  ; $4994
    .byte $05, $0C, $05, $01, $13, $05, $2C, $20, $13, $0F, $20, $09, $06, $20, $19, $0F  ; $49A4
    .byte $15, $1F, $1C, $02, $15, $19, $20, $14, $08, $05, $20, $0F, $12, $09, $07, $09  ; $49B4
    .byte $0E, $01, $0C, $1F, $1C, $19, $0F, $15, $27, $0C, $0C, $20, $08, $01, $16, $05  ; $49C4
    .byte $20, $01, $1F, $1C, $02, $15, $07, $07, $05, $04, $20, $07, $01, $0D, $05, $2E  ; $49D4
    .byte $1F, $1F, $44, $1F, $1C, $13, $01, $0E, $14, $01, $20, $13, $05, $0E, $04, $13  ; $49E4
    .byte $20, $0F, $15, $14, $20, $13, $0F, $0D, $05, $1F, $1C, $05, $01, $12, $0C, $19  ; $49F4
    .byte $20, $08, $0F, $20, $08, $0F, $20, $08, $0F, $27, $13, $20, $14, $0F, $1F, $43  ; $4A04
    .byte $1C, $14, $08, $05, $20, $06, $0F, $0C, $0C, $0F, $17, $09, $0E, $07, $20, $07  ; $4A14
    .byte $0F, $0F, $04, $1F, $1C, $02, $0F, $19, $13, $20, $01, $0E, $04, $20, $07, $09  ; $4A24
    .byte $12, $0C, $19, $0D, $05, $0E, $2E, $1F, $1F, $41, $3C, $1B, $20, $0C, $20, $05  ; $4A34
    .byte $20, $07, $20, $05, $20, $0E, $20, $04, $20, $1D, $3E, $1F, $1C, $01, $12, $03  ; $4A44
    .byte $01, $04, $05, $20, $2A, $20, $03, $08, $12, $0F, $0D, $01, $0E, $03, $05, $1F  ; $4A54
    .byte $1C, $04, $0F, $0D, $09, $0E, $01, $14, $0F, $12, $13, $20, $2A, $20, $05, $0E  ; $4A64
    .byte $09, $07, $0D, $01, $1F, $1C, $06, $34, $03, $07, $20, $2A, $20, $0E, $05, $09  ; $4A74
    .byte $1F, $1C, $12, $05, $04, $20, $13, $05, $03, $14, $0F, $12, $20, $09, $0E, $03  ; $4A84
    .byte $2E, $1F, $1C, $13, $15, $03, $03, $05, $13, $13, $20, $2A, $20, $14, $01, $0C  ; $4A94
    .byte $05, $0E, $14, $1F, $41, $1C, $06, $0F, $12, $20, $14, $08, $05, $20, $0C, $01  ; $4AA4
    .byte $14, $05, $13, $14, $20, $01, $0E, $04, $1F, $1C, $07, $12, $05, $01, $14, $05  ; $4AB4
    .byte $13, $14, $20, $03, $01, $0C, $0C, $20, $14, $08, $05, $1F, $1F, $1C, $14, $13  ; $4AC4
    .byte $0D, $20, $26, $20, $0C, $05, $07, $05, $0E, $04, $20, $17, $08, $11, $1F, $1F  ; $4AD4
    .byte $4A, $1C, $28, $34, $30, $32, $29, $20, $37, $33, $34, $2D, $33, $36, $33, $34  ; $4AE4
    .byte $1F                                                                             ; $4AF4

; ==================== NACH DEM INTRO ====================
; $4B00-$FEFF wird nach $0810-$BC0F kopiert.
; $0848-$0947 wird danach als Entpacker nach $0100 kopiert.
; Die folgenden Adressen sind die tatsächlichen Laufzeitadressen.

.org $0100
game_depacker:
    LDA ($2F),Y                ; $0100: B1 2F
    ROL A                      ; $0102: 2A
    ROL A                      ; $0103: 2A
    ROL A                      ; $0104: 2A
    ROL A                      ; $0105: 2A
    AND #$07                   ; $0106: 29 07
    TAX                        ; $0108: AA
    LDA $011A,X                ; $0109: BD 1A 01
    STA $0118                  ; $010C: 8D 18 01
    LDA ($2F),Y                ; $010F: B1 2F
    AND #$1F                   ; $0111: 29 1F
    TAX                        ; $0113: AA
    JSR L0122                  ; $0114: 20 22 01
    JMP $01FF                  ; $0117: 4C FF 01

.org $0122
L0122:
    INC $2F                    ; $0122: E6 2F
    BNE L0128                  ; $0124: D0 02
    INC $30                    ; $0126: E6 30
L0128:
    RTS                        ; $0128: 60
    LDA ($2F),Y                ; $0129: B1 2F
    JSR L0122                  ; $012B: 20 22 01
L012E:
    STA ($2D),Y                ; $012E: 91 2D
    INC $2D                    ; $0130: E6 2D
    BNE L0136                  ; $0132: D0 02
    INC $2E                    ; $0134: E6 2E
L0136:
    DEX                        ; $0136: CA
    BNE L012E                  ; $0137: D0 F5
    BEQ game_depacker          ; $0139: F0 C5
    LDA #$00                   ; $013B: A9 00
    BEQ L012E                  ; $013D: F0 EF
    LDA #$FF                   ; $013F: A9 FF
    BNE L012E                  ; $0141: D0 EB
L0143:
    LDA ($2F),Y                ; $0143: B1 2F
    STA ($2D),Y                ; $0145: 91 2D
    INC $2F                    ; $0147: E6 2F
    BNE L014D                  ; $0149: D0 02
    INC $30                    ; $014B: E6 30
L014D:
    INC $2D                    ; $014D: E6 2D
    BNE L0153                  ; $014F: D0 02
    INC $2E                    ; $0151: E6 2E
L0153:
    DEX                        ; $0153: CA
    BNE L0143                  ; $0154: D0 ED
    BEQ game_depacker          ; $0156: F0 A8
    JSR L0171                  ; $0158: 20 71 01
    LDA ($2F),Y                ; $015B: B1 2F
    JSR L0122                  ; $015D: 20 22 01
L0160:
    STA ($2D),Y                ; $0160: 91 2D
    INC $2D                    ; $0162: E6 2D
    BNE L0168                  ; $0164: D0 02
    INC $2E                    ; $0166: E6 2E
L0168:
    DEX                        ; $0168: CA
    BNE L0160                  ; $0169: D0 F5
    DEC $39                    ; $016B: C6 39
    BPL L0160                  ; $016D: 10 F1
    BMI game_depacker          ; $016F: 30 8F
L0171:
    STX $39                    ; $0171: 86 39
    LDA ($2F),Y                ; $0173: B1 2F
    TAX                        ; $0175: AA
    JMP L0122                  ; $0176: 4C 22 01
    JSR L0171                  ; $0179: 20 71 01
L017C:
    LDA ($2F),Y                ; $017C: B1 2F
    STA ($2D),Y                ; $017E: 91 2D
    INC $2F                    ; $0180: E6 2F
    BNE L0186                  ; $0182: D0 02
    INC $30                    ; $0184: E6 30
L0186:
    INC $2D                    ; $0186: E6 2D
    BNE L018C                  ; $0188: D0 02
    INC $2E                    ; $018A: E6 2E
L018C:
    DEX                        ; $018C: CA
    BNE L017C                  ; $018D: D0 ED
    DEC $39                    ; $018F: C6 39
    BPL L017C                  ; $0191: 10 E9
    JMP game_depacker          ; $0193: 4C 00 01
game_depacker_done:
    BIT L01DA                  ; $0196: 2C DA 01
    LDA #$37                   ; $0199: A9 37
    STA $01                    ; $019B: 85 01
    CLI                        ; $019D: 58
    JSR $2100                  ; $019E: 20 00 21
    JMP $A7AE                  ; $01A1: 4C AE A7
    CPX #$00                   ; $01A4: E0 00
    BEQ game_depacker_done     ; $01A6: F0 EE
    LDA #$04                   ; $01A8: A9 04
    BIT $08A9                  ; $01AA: 2C A9 08
    STA $FF                    ; $01AD: 85 FF
L01AF:
    LDA ($2F),Y                ; $01AF: B1 2F
    STA ($2D),Y                ; $01B1: 91 2D
    INY                        ; $01B3: C8
    CPY $FF                    ; $01B4: C4 FF
    BNE L01AF                  ; $01B6: D0 F7
    CLC                        ; $01B8: 18
    LDA $2D                    ; $01B9: A5 2D
    ADC $FF                    ; $01BB: 65 FF
    STA $2D                    ; $01BD: 85 2D
    LDA $2E                    ; $01BF: A5 2E
    ADC #$00                   ; $01C1: 69 00
    STA $2E                    ; $01C3: 85 2E
    LDY #$00                   ; $01C5: A0 00
    DEX                        ; $01C7: CA
    BNE L01AF                  ; $01C8: D0 E5
    CLC                        ; $01CA: 18
    LDA $2F                    ; $01CB: A5 2F
    ADC $FF                    ; $01CD: 65 FF
    STA $2F                    ; $01CF: 85 2F
    LDA $30                    ; $01D1: A5 30
    ADC #$00                   ; $01D3: 69 00
    STA $30                    ; $01D5: 85 30
    JMP game_depacker          ; $01D7: 4C 00 01
L01DA:
    LDA $EF00,Y                ; $01DA: B9 00 EF
    STA $FF00,Y                ; $01DD: 99 00 FF
    INY                        ; $01E0: C8
    BNE L01DA                  ; $01E1: D0 F7
    DEC $01DC                  ; $01E3: CE DC 01
    DEC $01DF                  ; $01E6: CE DF 01
    LDA $01DF                  ; $01E9: AD DF 01
    CMP #$DF                   ; $01EC: C9 DF
    BNE L01DA                  ; $01EE: D0 EA
    RTS                        ; $01F0: 60

.org $0810
game_stage2_entry:
    SEI                        ; $0810: 78
    LDA #$34                   ; $0811: A9 34
    STA $01                    ; $0813: 85 01
    LDX #$05                   ; $0815: A2 05
L0817:
    LDA $0842,X                ; $0817: BD 42 08
    STA $002D,X                ; $081A: 9D 2D 00
    DEX                        ; $081D: CA
    BPL L0817                  ; $081E: 10 F7
    TXS                        ; $0820: 9A
    LDY #$00                   ; $0821: A0 00
L0823:
    DEC $32                    ; $0823: C6 32
    DEC $082C                  ; $0825: CE 2C 08
L0828:
    LDA ($31),Y                ; $0828: B1 31
    STA $0000,Y                ; $082A: 99 00 00
    INY                        ; $082D: C8
    BNE L0828                  ; $082E: D0 F8
    LDA $32                    ; $0830: A5 32
    CMP #$08                   ; $0832: C9 08
    BNE L0823                  ; $0834: D0 ED
L0836:
    LDA $0848,Y                ; $0836: B9 48 08
    STA game_depacker,Y        ; $0839: 99 00 01
    INY                        ; $083C: C8
    BNE L0836                  ; $083D: D0 F7
    JMP game_depacker          ; $083F: 4C 00 01
