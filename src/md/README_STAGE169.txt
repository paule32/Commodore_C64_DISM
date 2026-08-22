Stage 169 – vollständige Stage-167-Basis + PE32/PE32+-MSZIP
=================================================================

Warum dieser Stand neu aufgebaut wurde
--------------------------------------
Die von dir genannte letzte Originalgröße von rund 2264 KiB passt exakt zur
Stage-167-Quelldatei. Deshalb wurde Stage 169 diesmal direkt aus genau dieser
vollständigen Datei aufgebaut und nicht aus einer verkürzten Zwischenfassung.

Verbindliche Basis:
  d64_dism.py = 2318827 Bytes = 2264.48 KiB
  Zeilen      = 51926
  SHA-256     = a83cb561458323deff22ddfddbd1f15969e2325462ec50b630c1a70d4514308f

Neue Stage 169:
  d64_dism.py = 2351788 Bytes = 2296.67 KiB
  Zeilen      = 52886
  SHA-256     = 7c068867a8c8255f2ddcbcc25482cf6667382038110bc09344d6e92db1f27322

Erhaltungsnachweis:
  alle 51926 Stage-167-Zeilen unverändert/in Originalreihenfolge vorhanden
  Unified-Diff: 960 hinzugefügt, 0 entfernt

Damit ist die Erweiterung tatsächlich additiv. Der ursprüngliche PE32- und
PE32+-Writer bleibt im Quelltext vollständig stehen. Die Pack-Unterstützung
wird über nachgeschaltete Wrapper ergänzt.

PE32-Packer
-----------
Ablauf:
  Stage-167 PE32-Writer vollständig ausführen
  -> COFF32-Relocations/IAT/Exporte/Baserelocations sind fertig
  -> finalen .text per Cabinet.dll/MSZIP komprimieren
  -> D64Z-v1-Header + komprimierte Daten in .ztext
  -> nativen x86-.loader ergänzen
  -> AddressOfEntryPoint auf .loader umstellen
  -> .text behält RVA/VirtualSize, RawSize wird 0

PE32+-Packer
------------
Ablauf analog für AMD64/PE32+:
  Stage-167 PE32+-Writer vollständig ausführen
  -> finalen .text packen
  -> nativen AMD64-.loader ergänzen
  -> .ztext ergänzen
  -> ursprünglichen OEP nach dem Entpacken anspringen

Der AMD64-Loader:
  * benutzt das Windows-x64-ABI mit 32 Byte Shadow Space,
  * übergibt Decompress-Argument 5/6 auf dem Stack,
  * adressiert IAT/.text/.ztext/OEP RIP-relativ,
  * erzeugt dadurch keine zusätzlichen absoluten DIR64-Fixups,
  * stellt den alten Seitenschutz wieder her,
  * ruft FlushInstructionCache vor dem OEP-Sprung auf.

Compression API
---------------
Buildzeit:
  Cabinet.dll -> CreateCompressor / Compress / CloseCompressor

Laufzeit:
  Cabinet.dll -> CreateDecompressor / Decompress / CloseDecompressor
  Kernel32.dll -> VirtualProtect / FlushInstructionCache / ExitProcess

Standardverhalten
-----------------
PE32-EXE:  auf Windows standardmäßig gepackt
PE32+-EXE: auf Windows standardmäßig gepackt
DLL:       weiterhin ungepackt
Nicht-Windows: Standard-Packing aus, da Cabinet Compression API fehlt

Es wird kein externes Packprogramm, kein externer Assembler/Linker und kein
mingw32-make für den Packvorgang gestartet.

Kompatibilität
--------------
Die Windows Compression API mit CreateDecompressor/Decompress setzt Windows 8
oder neuer voraus. Windows 11 ist geeignet.

ZIP-Hinweis
-----------
Damit die echte Quellgröße im Archiv sichtbar bleibt, wird d64_dism.py in der
Stage-169-ZIP absichtlich mit ZIP_STORED und damit unkomprimiert abgelegt.
