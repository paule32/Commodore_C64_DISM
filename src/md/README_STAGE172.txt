Stage 172 – PE32 Packed Image Compactor
=========================================

Basis / Quellerhaltung
----------------------
Stage 171 d64_dism.py:
  2402830 Bytes (2346.51 KiB)
  54388 Zeilen
  SHA-256 162c17eb046b0d289c652d20e88c61d81d229e5aa276afa08706f2ea7b51c770

Stage 172 d64_dism.py:
  2426290 Bytes (2369.42 KiB)
  55033 Zeilen
  SHA-256 971708059b01eb6428c0b036b0bc00171484e912c08aa405702751f2f605ab22

Alle Stage-171-Zeilen bleiben unverändert und in derselben Reihenfolge
vorhanden. Unified Diff: +645 / -0 Quellzeilen.

Analyse der hochgeladenen test.exe
----------------------------------
Dateigröße: 2048 Byte
PE32/i386, FileAlignment=0x200, SectionAlignment=0x1000

Vorher:
  .text    RVA=0x1000  VS=0x0156  RawSize=0x000  RawPtr=0x000
  .loader  RVA=0x2000  VS=0x00B8  RawSize=0x200  RawPtr=0x200
  .ztext   RVA=0x3000  VS=0x2000  RawSize=0x200  RawPtr=0x400
  .idata   RVA=0x5000  VS=0x00D5  RawSize=0x200  RawPtr=0x600

Wichtig: Zwischen den Raw-Blöcken lag bereits kein physisches Dateiloch.
Der sichtbare Abstand war hauptsächlich der virtuelle 0x1000-RVA-Section-
Alignmentbereich.

Der reale Dateiverschnitt steckte in den 512-Byte-Raw-Blöcken:
  .loader: 184 Byte Code + 328 Byte Padding
  .ztext : 260 Byte D64Z/MSZIP + 252 Byte Padding

184 + 260 = 444 Byte. Das passt gemeinsam in einen einzigen 512-Byte-Block.

Compactor-Ablauf
----------------
compact_packed_pe32_image() erkennt ausschließlich das bekannte Stage-170/171
D64Z-PE32-Layout. Danach:

  1. PE32/MZ/Section-Tabelle validieren
  2. .loader und unmittelbar folgende .ztext suchen
  3. D64Z-v1/MSZIP-Header prüfen
  4. tatsächliche .ztext-Länge aus PackedSize bestimmen
  5. D64Z direkt hinter den Loadercode legen
  6. die x86-Loader-PackedVA exakt an der bekannten `push imm32`-Signatur patchen
  7. separate .ztext-Section entfernen
  8. folgende Raw-Sections lückenlos nach links packen
  9. NumberOfSections, SizeOfCode, SizeOfInitializedData, BaseOfData und
     PointerToRawData aktualisieren
 10. alle späteren RVAs, insbesondere .idata, unverändert lassen

Dadurch müssen IAT-Adressen und der bereits komprimierte .text nicht verändert
oder erneut komprimiert werden.

Nachher bei test.exe:
  .text    RVA=0x1000  VS=0x0156  RawSize=0x000  RawPtr=0x000
  .loader  RVA=0x2000  VS=0x01BC  RawSize=0x200  RawPtr=0x200
            D64Z eingebettet bei Loader+0x00B8 = RVA 0x20B8
  .idata   RVA=0x5000  VS=0x00D5  RawSize=0x200  RawPtr=0x400

Dateigröße:
  vorher 2048 Byte
  nachher 1536 Byte
  gespart  512 Byte = 25.0 %

Die logischen 260 D64Z-Bytes sind byte-identisch übernommen. Im Loader wurden
nur zwei Bytes des 32-Bit-PackedVA-Immediate geändert; die Adresse zeigt jetzt
von 0x00403020 auf 0x004020D8.

Warum .idata RVA 0x5000 bleibt
------------------------------
Ein Verschieben von .idata im virtuellen Adressraum würde bereits in .text
komprimierte IAT-Adressen verändern. Dafür müsste der Compactor .text zuerst
mit der Windows Compression API dekomprimieren, alle IAT-Referenzen neu
patchen und anschließend erneut MSZIP-komprimieren. Das bringt für die
physische EXE-Größe keinen zusätzlichen Vorteil, weil das RVA-Loch keine
Dateibytes belegt. Stage 172 verändert deshalb nur physische Blöcke, die echte
Bytes sparen.

Sicherheit
----------
Automatischer Compactor:
  PE32_PACK_COMPACTOR_DEFAULT = True

Der Compactor verändert nur:
  * IMAGE_FILE_MACHINE_I386 / PE32 Magic 0x10B
  * bekannte .loader + .ztext Reihenfolge
  * D64Z v1 mit MSZIP
  * eindeutige x86 `push old_packed_va` Loader-Signatur

Er verändert NICHT:
  * PE32+ / AMD64
  * signierte PE-Dateien / Certificate Directory
  * Bilder mit Debug Directory / PointerToRawData
  * ungepackte Images
  * bereits kompaktierte Images ohne separate .ztext

Wenn die Zusammenlegung bei einem größeren Payload keine FileAlignment-
Grenze spart, bleibt das Image byte-identisch.

Automatische Build-Integration
------------------------------
Der vollständige Stage-171-PE32-Writer bleibt erhalten. Stage 172 hält eine
Referenz darauf und legt einen additiven Wrapper darüber:

  Stage171 build_pe32_image_with_imports_exports()
      -> fertiges PE32
      -> compact_packed_pe32_image()
      -> kompakteres PE32, falls sicher möglich

CLI für vorhandene EXE
----------------------
  py d64_dism.py --compact-pe32 test.exe

Standardausgabe:
  test.compact.exe

Explizites Ziel:
  py d64_dism.py --compact-pe32 test.exe -o test_small.exe

Testumgebung
------------
Die echte Windows-Ausführung der erzeugten EXE konnte in dieser Linux-
Testumgebung nicht gestartet werden. Die PE-Struktur, RVA/Raw-Zuordnung,
D64Z-Datenintegrität, Loader-Pointerpatch und Import/IAT-Directories wurden
statisch geprüft. Der native Loader selbst ist unverändert bis auf die neue
PackedVA.
