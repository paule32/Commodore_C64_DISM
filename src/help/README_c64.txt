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
