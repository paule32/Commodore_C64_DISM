Stage 170 – .text/.loader/.ztext/.idata + Import-by-Ordinal
==================================================================

Basis / Erhaltung
-----------------
Stage 169 d64_dism.py:
  2351788 Bytes (2296.67 KiB)
  52886 Zeilen
  SHA-256 7c068867a8c8255f2ddcbcc25482cf6667382038110bc09344d6e92db1f27322

Stage 170 d64_dism.py:
  2392516 Bytes (2336.44 KiB)
  54115 Zeilen
  SHA-256 669ace99813b07c35300e508b1bc05517deb5cfa0b16755ff251ab3add974d18

Alle 52886 Stage-169-Zeilen sind unverändert und in derselben
Reihenfolge vorhanden. Der Unified Diff enthält 1229 Ergänzungen und 0
entfernte Quellzeilen.

Bevorzugtes Section-Layout
--------------------------
Ja: Der PE-Loader benötigt .idata nicht vor .loader oder .ztext. Die Import-
Tabelle wird über IMAGE_DIRECTORY_ENTRY_IMPORT per RVA gefunden. Stage 170
verwendet im gepackten EXE-Pfad deshalb bewusst aufsteigende Section-RVAs:

  PE32 ohne weitere Datensektionen:
    .text -> .loader -> .ztext -> .idata

  PE32+ / AMD64:
    .text -> .loader -> .ztext -> .idata -> [.data] -> [.bss]

Die ersten vier Sections entsprechen damit immer dem gewünschten Layout.
.text behält seine ursprüngliche virtuelle Adresse und VirtualSize, besitzt im
gepackten Zustand aber keinen Raw-Dateiblock. AddressOfEntryPoint zeigt auf
.loader. .loader dekomprimiert .ztext nach .text und springt dann zum OEP.

PE32 Header-Verkleinerung
-------------------------
Der gepackte PE32-Pfad verwendet nun den minimal sinnvollen 64-Byte-DOS-Header
(e_lfanew=0x40). Bei einem kleinen 4-Section-Test sank SizeOfHeaders dadurch
von 0x400 auf 0x200 und das deterministische Testimage von 2560 auf 2048 Byte.
Das spart bei diesem Layout exakt 512 Byte.

Import-by-Ordinal
-----------------
Stage 170 unterstützt Name- und Ordinalimporte in PE32 und PE32+.

PE32:
  ILT/IAT-Wert = 0x80000000 | ordinal

PE32+:
  ILT/IAT-Wert = 0x8000000000000000 | ordinal

Für Ordinalimporte wird kein IMAGE_IMPORT_BY_NAME-Block mit Funktionsnamen
mehr in das EXE geschrieben. Der DLL-Name selbst bleibt weiterhin nötig, weil
der IMAGE_IMPORT_DESCRIPTOR ihn referenziert.

Explizite Assembler-Syntax:

  import Foo, "demo.dll", #123

Die bestehende Parser-Syntax musste dafür nicht entfernt oder umgebaut werden;
#123 wird im Stage-170-Importbuilder als Ordinal erkannt.

Automatische lokale Ordinale
----------------------------
Auf Windows ist für gepackte EXEs standardmäßig aktiviert:

  PE_PACK_IMPORTS_BY_LOCAL_ORDINAL_DEFAULT = True

Der Linker liest die Exporttabelle der zur Zielarchitektur passenden lokalen
DLL direkt als PE-Datei aus und ersetzt einen Namensimport nur dann, wenn der
Name dort eindeutig als Export mit Ordinal gefunden wurde.

PE32 sucht insbesondere die 32-Bit-DLL in SysWOW64, PE32+ die 64-Bit-DLL in
System32/Sysnative. Stimmt die Architektur nicht oder wird der Export nicht
gefunden, bleibt der normale Namensimport unverändert erhalten.

WICHTIG: Ordinalnummern von Windows-System-DLLs sind keine allgemein stabile,
dokumentierte ABI über alle Windows-Versionen hinweg. Der automatische Modus
optimiert daher für die lokale Ziel-Windows-Installation. Für portable EXEs
kann er abgeschaltet werden:

  PE_PACK_IMPORTS_BY_LOCAL_ORDINAL_DEFAULT = False

Für eigene DLLs mit festgelegten .DEF-Ordinalen ist ein explizites #Ordinal die
robustere Variante.

Gemessene Importgröße im Loader-Beispiel
----------------------------------------
Nur die sechs Stage-169-Loader-APIs, ohne weitere Programmimporte:

  PE32  Namensimporte: 261 Byte .idata logisch
  PE32  Ordinalimporte:149 Byte .idata logisch
  Einsparung:          112 Byte

  PE32+ Namensimporte: 325 Byte .idata logisch
  PE32+ Ordinalimporte:213 Byte .idata logisch
  Einsparung:          112 Byte

Wegen FileAlignment=0x200 wird die EXE-Datei erst dann um einen weiteren
512-Byte-Block kleiner, wenn die verkleinerte .idata dadurch eine
Alignment-Grenze unterschreitet.

PE32+ und ASLR
--------------
Im gepackten PE32+-EXE-Pfad wird ASLR bewusst abgeschaltet und
IMAGE_FILE_RELOCS_STRIPPED gesetzt. Grund: Windows kann Baserelocations im noch
nicht dekomprimierten .text nicht vor dem Stage-170-Loader sinnvoll patchen.
Der Packer verwendet deshalb die feste PE64_IMAGE_BASE und NX_COMPAT, aber
nicht DYNAMIC_BASE. Das ist korrekt für den aktuellen Self-Unpack-Pfad.

Ein späterer Loader könnte ASLR wieder erlauben, wenn er nach dem Entpacken
einen eigenen Relocation-Pass über .text ausführt.

Tests
-----
Siehe STAGE170_TEST_RESULTS.txt. Der native Cabinet.dll-Roundtrip konnte in der
Linux-Testumgebung nicht ausgeführt werden; die statischen PE-Layout-, Ordinal-
und Linkertests liefen deterministisch mit einem Fake-Kompressor. Auf Windows
nutzt der echte Build weiterhin Cabinet.dll / Compress und die Laufzeit
CreateDecompressor / Decompress.
