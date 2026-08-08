# Windows PE64: eigene Konsole und echte .text/.data-Sektionen

## Ursache 1: PE64-Konsole wurde geerbt

d64_dism.py startete PE32/PE64 bislang nur mit CREATE_NEW_PROCESS_GROUP. Ein
Console-Target konnte dadurch die Konsole des aufrufenden Prozesses erben.
`AllocConsole` kann in diesem Fall keine zweite Konsole anlegen. Anschließende
Aufrufe von SetConsoleWindowInfo/SetConsoleScreenBufferSize verändern dann das
geerbte Konsolenfenster.

PE64/PE32-Console-Targets werden deshalb aus der IDE mit CREATE_NEW_CONSOLE
gestartet. CREATE_NEW_PROCESS_GROUP bleibt zusätzlich erhalten.

## Ursache 2: temporäres RWX-Sektionsmodell

Der erste PE64-Backendstand legte Code, VMTs, Strings, Handles und Variablen in
einem einzigen COFF64-.text-Block ab. Die finale PE32+-Datei musste diese
Sektion deshalb READ|WRITE|EXECUTE markieren.

PE64 verwendet nun echte Sektionen:

- `.text`: IMAGE_SCN_CNT_CODE | IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_MEM_READ
- `.data`: IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE

Der Pascal/C-PE64-Codegenerator erzeugt explizit `section .text` und vor den
Runtime-/Programmdaten `section .data`.

## COFF64/Linker

COFF64 speichert .text und .data separat. Symbole behalten ihre Section Number,
und Relocations tragen die Quellsektion. Der interne Linker löst REL32,
ADDR64 und ADDR32 auch über Sektionsgrenzen hinweg auf. DIR64-Basisrelokationen
werden mit der tatsächlichen RVA der Patchstelle erzeugt.

Maschinencode in einer expliziten `.data`-Sektion wird vom internen
PE64-Assembler als Fehler abgelehnt.
