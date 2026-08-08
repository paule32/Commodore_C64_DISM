# PE64: kompakte Header und echte .bss-Sektion

## Headerlayout

Der PE64-Writer verwendet weiterhin den standardmaessigen PE32+-Optional-Header
mit 0xF0 Bytes und 16 Data Directories. Der DOS-Bereich wurde jedoch auf den
notwendigen 64-Byte-IMAGE_DOS_HEADER reduziert (`e_lfanew = 0x40`).

Import-, Export- und Base-Relocation-Payload werden in einer gemeinsamen
Linker-Datensektion gespeichert. Dadurch besitzt ein normales PE64-Image
hoechstens vier Sektionen:

- `.text`  - Code, READ + EXECUTE
- `.data`  - initialisierte Daten, READ + WRITE
- `.bss`   - uninitialisierte Daten, READ + WRITE, keine Raw-Bytes
- `.idata`/`.edata`/`.reloc` - kombinierte Linker-Daten

Damit passen DOS-, PE-, COFF-, Optional- und Section-Header in einen einzigen
0x200-Byte-FileAlignment-Block. Die erste Raw-Sektion `.text` beginnt somit bei
Dateioffset 0x200.

## .bss

Der interne AMD64-Assembler unterstuetzt:

```asm
section .bss
buffer: resb 4096
counter: resd 1
pointer: resq 1
```

Unterstuetzte Reservierungsdirektiven:

- `resb` / `rb`
- `resw` / `rw`
- `resd` / `rd`
- `resq` / `rq`

COFF64 und PE32+ schreiben fuer `.bss` keine Nutzdaten in die Datei:

- `VirtualSize` = reservierte Groesse
- `SizeOfRawData` = 0
- `PointerToRawData` = 0
- Characteristics = uninitialized data + READ + WRITE, nicht EXECUTE

Windows stellt diesen Speicher beim Laden automatisch mit Null initialisiert zur
Verfuegung.

Der PE64-Pascal/C-Backend legt Null-initialisierte globale Variablen sowie
mutable Runtime-Daten (Console-Handles, Exception-State, Formatbuffer usw.) in
`.bss`. Der per `VirtualAlloc` angelegte ReadLn-Payload bleibt dynamisch; in
`.bss` liegt nur noch dessen 8-Byte-Zeiger.

## Groessenbeispiel

Ein Test mit 10.000 Nullbytes ergibt beim direkten PE64-Writer:

- als initialisierte `.data`: 11.264 Byte EXE
- als `.bss`: 1.024 Byte EXE
- Ersparnis: 10.240 Byte

Die genaue Groesse haengt von Imports, Relocations und FileAlignment ab.
