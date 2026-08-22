Stage 161 – Formdesigner Quellcode/Assembler ohne interne Buildleisten

Problem
-------
Der eingebettete DocumentEditor konnte im Quellcode-Tab seine interne
Leiste erneut sichtbar machen:

    [Compile / Assemble] [Windows PE32 / PE32+] [GUI]

Der bisherige hide()-Aufruf war nicht dauerhaft ausreichend, weil
DocumentEditor.update_syntax_highlighting() sein assembler_panel später
wieder sichtbar schalten kann.

Korrektur
---------
Die internen DocumentEditor-Leisten werden jetzt vollständig aus den
sichtbaren WFM-Seitenlayouts entfernt.

Quellcode:
    source_layout.removeWidget(build_document.assembler_panel)

Assembler:
    assembly_layout.removeWidget(build_document.generated_assembly_panel)

Beide Panels werden anschließend an den unsichtbaren Hilfs-DocumentEditor
zurückgehängt. Dadurch können spätere setVisible(True)-Aufrufe sie nicht
mehr im Formdesigner anzeigen.

Sichtbare Formdesigner-Tabs:
    Formular-Designer
    Assembler      (nach erfolgreichem Compile)
    Quellcode

Die zentrale Formdesigner-Buildleiste oberhalb des TabWidgets bleibt
unverändert erhalten und funktional:

    Compile
    Windows PE32 / Windows PE32+
    Assemble
    Start

Source-Outline Dark Mode
------------------------
Die TreeList links neben dem Quellcode wurde separat gestylt.

Dark:
    Hintergrund  #181818
    Header       #252525
    Schrift      #FFFFFF
    Auswahl      #294764

Light:
    Hintergrund  #F5F5F5
    Schrift      #111111
    Auswahl      #CFE4F7

Der Stil wird beim Erzeugen sowie bei jedem Dark-/Light-Wechsel aktualisiert.

Unverändert:
- Source-Outline Navigation zu Prozeduren/Funktionen/Variablen
- F2 im ASM-Editor -> Assemble + interner Link
- Timer 42x42 / OnTimer
- Session/Database/Query/DataSource 42x42
- d64qt5 bleibt im Unterverzeichnis d64qt5/

py_compile d64_dism.py: OK
Native Windows/PyQt5-GUI-Laufzeitprüfung ist hier nicht verfügbar.
