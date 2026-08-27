# Optimierte Crypto-Routinen für dBase2Many

Ziel: i386 / Win32 COFF, NASM-Syntax, `cdecl`.

Die Quellen sind als kompakte One-Shot-Funktionen ausgeführt. Die separaten
Streaming-APIs (`init`, `update`, `final`) wurden absichtlich nicht übernommen,
damit die COFF-Objekte klein bleiben.

## Enthaltene NASM-Dateien

| Datei | Exportiertes Symbol | Hex-Ausgabe |
|---|---|---:|
| `blake2s_small.asm` | `_jit_blake2` | 64 Zeichen, klein |
| `crc16_small.asm` | `_jit_crc16` | 4 Zeichen, klein |
| `crc32_small.asm` | `_jit_crc32` | 8 Zeichen, klein |
| `crc32c_small.asm` | `_jit_crc32c` | 8 Zeichen, klein |
| `crc64_small.asm` | `_jit_crc64` | 16 Zeichen, groß |
| `md5_small.asm` | `_jit_md5` | 32 Zeichen, klein |
| `sha1_small.asm` | `_jit_sha1` | 40 Zeichen, klein |
| `sha224_small.asm` | `_jit_sha224` | 56 Zeichen, klein |
| `sha256_small.asm` | `_jit_sha256` | 64 Zeichen, klein |
| `sha3_256_small.asm` | `_jit_sha3` | 64 Zeichen, klein |
| `sha384_small.asm` | `_jit_sha384` | 96 Zeichen, klein |

SHA-512 ist nicht enthalten, weil bereits eine optimierte Fassung vorhanden ist.
BLAKE3 ist nicht enthalten: `blake3.cc` im bereitgestellten ZIP enthält noch
keine Implementierung.

## ABI

Alle öffentlichen Funktionen verwenden:

```c
char * __cdecl _jit_name(char *text, int length);
```

`CRC16`, `CRC32`, `CRC32C`, `CRC64`, `MD5`, `SHA1`, `SHA224`, `SHA256`,
`SHA3-256` und `SHA384` rufen `_jit_malloc` für den Ergebnisstring auf.

BLAKE2s verwendet wie die bereitgestellte C++-Fassung einen statischen
65-Byte-Ausgabepuffer. Dieser eine Wrapper ist deshalb nicht reentrant und nicht
thread-sicher.

## Bauen

PowerShell:

```powershell
./build_all.ps1
```

CMD:

```cmd
build_all.cmd
```

MSYS2/Bash:

```bash
./build_all.sh
```

Einzelne Datei:

```bash
nasm -Ox -f win32 asm/sha256_small.asm -o obj/sha256_small.o
```

Archiv:

```bash
i686-w64-mingw32-ar rcs libcrypto_small.a obj/*.o
```

## Referenzgrößen

Die folgenden Größen stammen von inhaltlich äquivalenten, assemblierbaren
COFF32-Referenzobjekten. NASM kann geringfügig andere Metadaten-Größen erzeugen.

| Objekt | Byte |
|---|---:|
| `crc16_small.o` | 630 |
| `crc32_small.o` | 626 |
| `crc32c_small.o` | 627 |
| `crc64_small.o` | 650 |
| `sha1_small.o` | 1197 |
| `md5_small.o` | 1477 |
| `sha224_small.o` | 1639 |
| `sha256_small.o` | 1639 |
| `sha3_256_small.o` | 1667 |
| `blake2s_small.o` | 2411 |
| `sha384_small.o` | 2660 |

## Wichtige Korrektur in SHA-384

Die hochgeladene C++-Fassung enthielt in der Kompressionsrunde:

```c
c = ROTR64(b, 2);
```

Die optimierte Fassung verwendet die korrekte SHA-384/SHA-512-Zustandsrotation:

```c
c = b;
```

## Getestete Vektoren

Siehe `TEST_VECTORS.txt`.
