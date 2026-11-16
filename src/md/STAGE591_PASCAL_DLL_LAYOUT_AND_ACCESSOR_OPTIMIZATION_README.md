# Stage 591 – Pascal DLL: Raw-Layout, leeres DllMain und Feldbrücken

**Verbindliche Grundlage:** `d64_dism_stage590.zip`.

## 1. Nullbereiche und PE-FileAlignment

Die vom Windows-PE-Loader verwendete `FileAlignment`-Vorgabe (meist `0x200` =
512 Byte) erlaubt **nicht**, dass nach `.idata`, `.edata` oder am Sektionsende
beliebige Nullbytes entfernt werden. Auch die Datenverzeichnisse referenzieren
**RVAs**, die unverändert bleiben müssen.

Neu: `d64dbase/pe_dll_compact.py` implementiert eine **konservative
physische DLL-Layoutkompaktierung** für PE32 und PE32+:

- verschiebt nur komplette Raw-Sektionen auf korrekte Alignment-Grenzen;
- setzt, wenn dadurch tatsächlich Speicherplatz entfällt, `e_lfanew`
  auf `0x40`, ermittelt das minimale `SizeOfHeaders` und setzt
  `PointerToRawData` in allen Sektionsheadern neu;
- belässt `VirtualAddress`, `VirtualSize`, `SizeOfRawData`, EntryPoint,
  ImageBase, DLL-Export-/Import-/Relocation-Directory und **alle
  Sektionsdaten** unverändert;
- deaktiviert sich für signierte, gechecksumte, Debug-/COFF-Metadaten-
  oder Overlay-Images sowie inkonsistente PE-Strukturen;
- übernimmt ausschließlich ein **kleineres, revalidiertes** Image;
- lässt EXE-Dateien vollständig unangetastet.

**Grenze:** Bereits korrekt dicht gepackte DLLs bleiben unverändert. Ein
intrasektionaler Padding-Rest von 1–511 Bytes kann bei `FileAlignment=512`
nicht einzeln entfernt werden. Dies sind keine überflüssigen vier
unabhängigen Speicherblöcke.

Die DLL-Kompaktierung wird bei `link_coff32_objects()` und
`link_coff64_objects()` nur für DLLs durchgeführt, sowohl mit aktiviertem
D64Z/MSZIP-Flag als auch ohne Packing. Die vorhandene EXE-Packung bleibt
unverändert.

## 2. Leerer DLL-EntryPoint

Die PE32/PE64-Pascal-Generatoren erzeugen bei einer LIBRARY **ohne globale
Initializer und mit vollständig leerem BEGIN/END** unmittelbar:

PE32:
```asm
__d64_dll_entry:
    mov eax, 1
    ret 12
```

PE64:
```asm
__d64_dll_entry:
    mov eax, 1
    ret
```

Bei vorhandenen Initializern/Statements bleibt die Prüfung
`DLL_PROCESS_ATTACH` mit ihrem bisherigen Code bestehen. Kein Vergleich
wird unabhängig vom Programmzustand pauschal entfernt.

## 3. Klassen-Feldzugriff (`__d64_cls_*_get/set_*`)

4-Byte-Felder verwenden einen dword-Transfer statt vier byteweiser
Transfers. Beispiel PE32 `get_fwidth`:

```asm
__d64_cls_tform_get_fwidth:
    mov eax, dword ptr [esp+4]      ; Self
    mov edx, dword ptr [esp+8]      ; destination
    mov ecx, dword ptr [eax+20]
    mov dword ptr [edx+0], ecx
    ret
```

Der PE32-Frame (`push ebp`/`mov ebp,esp` und Epilog) entfällt bei diesen
reinen Feldbrücken, da kein lokaler Frame benötigt wird. Für PE64 erfolgt
entsprechend ein `mov r8d, dword ptr [...]` / `mov dword ptr [...], r8d`.

Bei Feldern mit anderen Größen bleibt die bisherige Byte-Kopierfolge
bestehen; lediglich der unnötige PE32-Frame entfällt. Exportsymbole,
ABI (cdecl/Win64), Feld-Offsets und die Parameterübergabe bleiben gleich.

## 4. Prüfungen und Einschränkungen

- 26 gezielte Tests aus `test_stage591`, `test_stage542` und `test_stage590` erfolgreich.
- Test für reale PE32- und PE64-Container und für eine künstlich
  eingefügte 512-Byte-Lücke: die Lücke wird entfernt, Exporte,
  Section-RVAs und Sektionsbytes bleiben identisch.
- Bereits korrekt dicht ausgerichtete DLLs werden byteidentisch belassen.
- Sicherheitstest: signierte DLLs werden nicht verändert.
- Compiler- und Optimierermodule bestehen die Python-Syntaxprüfung; der
  große Hauptcode hat Python-3.15-`lazy`-Imports und wurde per angepasster
  AST-Prüfung geprüft.
- Nativer Windows-`LoadLibrary`-/Export-Laufzeittest sowie realer MSZIP-
  Komprimierungs-/Dekomprimierungs-Roundtrip wurden hier nicht ausgeführt.
- Die mitgelieferten vorkompilierten DLLs sind Beispiel-/Runtime-Artefakte,
  keine neu gebauten Test-DLLs. Ein separater neuer Benutzer-DLL-Anhang wurde
  bei dieser Anfrage nicht bereitgestellt.
