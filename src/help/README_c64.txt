C64-Hilfe fuer d64_dism.py
==========================

Lege die Commodore-C64-Hilfedatei unter genau diesem Namen ab:

    help/c64.chm

F1 im C64-Disassembler und im Hex-Viewer eines PRG/BIN-Dokuments
oeffnet diese CHM-Datei direkt. Die allgemeine Einstellung chm/last_file
wird dadurch nicht veraendert.

Stage ASM 1 - Context-ID + Topic-Fallback
=========================================

Im Python-Code ist beispielhaft definiert:

    help_py = {
        "test": 21,
    }

Wichtig: {"test", 21} waere in Python ein set und KEIN Dictionary.

Der integrierte CHM-Viewer versucht bei einem Overlay-Link zuerst die
numerische Context-ID. Dafuer kann das CHM-Projekt z.B. enthalten:

    [MAP]
    #define IDH_TEST 21

    [ALIAS]
    IDH_TEST=test.html

Wenn MAP/ALIAS-Metadaten in der extrahierten CHM nicht verfuegbar sind,
sucht der Viewer automatisch nach dem Dictionary-Key "test" im Keyword-
Index und danach im Themenbaum. Dadurch funktionieren sowohl klassische
CHM-Context-IDs als auch lesbare Topic-Namen.

Stage ASM 7 - Relocation-/Bootstrap-Overlay
===========================================

Das QPainter-Overlay fuer die Schleife ab $081C besitzt einen eigenen
klickbaren Hilfe-Link. Verwendet wird:

    help_py = {
        "test": 21,
        "relocation_bootstrap": 22,
    }

Fuer eine direkte CHM-Context-Aufloesung kann das CHM-Projekt z.B. enthalten:

    [MAP]
    #define IDH_RELOCATION_BOOTSTRAP 22

    [ALIAS]
    IDH_RELOCATION_BOOTSTRAP=relocation_bootstrap.html

Fehlt diese numerische Zuordnung, sucht der integrierte Viewer automatisch
nach dem Text "relocation_bootstrap" im CHM-Keyword-Index bzw. Themenbaum.

Stage ASM 79 - C64 BASIC F1-Hilfe
=================================

Im C64 BASIC Editor wird beim Druecken von F1 das BASIC-V2-Token unter dem
Cursor bestimmt. Die numerische Hilfe-ID entspricht dem originalen Tokenbyte.
Beispiele:

    FOR    = $81 = 129
    GOTO   = $89 = 137
    PRINT  = $99 = 153
    SYS    = $9E = 158
    PEEK   = $C2 = 194
    CHR$   = $C7 = 199

Auf stdout wird die ermittelte ID mit Python print() ausgegeben, z.B.:

    C64 BASIC Hilfe-ID: 153

Eine CHM kann die ID direkt so zuordnen:

    [MAP]
    #define IDH_BASIC_PRINT 153
    #define IDH_BASIC_FOR   129
    #define IDH_BASIC_CHR   199

    [ALIAS]
    IDH_BASIC_PRINT=basic/PRINT.html
    IDH_BASIC_FOR=basic/FOR.html
    IDH_BASIC_CHR=basic/CHR$.html

Fehlt die numerische MAP/ALIAS-Zuordnung, bleibt der bestehende Topic-/Keyword-
Fallback ueber das BASIC-Wort unter dem Cursor aktiv.
