# dBase Stage 22 – dynamischer `__dbase_format_buffer`

Stage 22 entfernt den statischen 96-Byte-Nullblock des dBase-Zahlformatpuffers.

## Vorher

Der generierte Datenabschnitt enthielt sinngemaess:

```asm
__dbase_format_buffer:
    db 0, 0, 0, ... ; insgesamt 96 Bytes
```

Der Symbolname war damit direkt die Adresse des Puffers.

## Jetzt

`__dbase_format_buffer` ist nur noch ein Pointer-Slot:

PE32:

```asm
__dbase_format_buffer:
    dd 0
```

PE32+:

```asm
__dbase_format_buffer:
    dd 0, 0
```

Der eigentliche Puffer wird einmal beim Programmstart angelegt.

### PE32

```asm
push 4             ; PAGE_READWRITE
push 12288         ; MEM_COMMIT | MEM_RESERVE
push 96            ; Pufferlaenge
push 0             ; lpAddress = NULL
call VirtualAlloc

test eax, eax
jne  allocation_ok
...
allocation_ok:
mov dword ptr [__dbase_format_buffer], eax
```

### PE32+

```asm
xor ecx, ecx       ; lpAddress = NULL
mov edx, 96
mov r8d, 12288     ; MEM_COMMIT | MEM_RESERVE
mov r9d, 4         ; PAGE_READWRITE
sub rsp, 40
call VirtualAlloc
add rsp, 40

test rax, rax
jne  allocation_ok
...
allocation_ok:
mov qword ptr [__dbase_format_buffer], rax
```

Bei einem Allokationsfehler wird die bereits initialisierte Qt-Runtime sauber mit
`DBaseQtShutdown` beendet und danach `ExitProcess(1)` aufgerufen.

## Verwendung

Alle Zahlformatierungsstellen laden jetzt den Pointer aus dem Slot.

Beispiele:

```asm
; PE32
push dword ptr [__dbase_format_buffer]
```

```asm
; PE32+
mov r8, qword ptr [__dbase_format_buffer]
```

Das betrifft insbesondere `_gcvt`, die Laengenbestimmung, `?`/`??` sowie
Zahl-zu-String-Konvertierungen fuer Konkatenationen.

## Freigabe

Nach `DBaseQtExec`/`DBaseQtShutdown` wird der Puffer freigegeben:

```text
VirtualFree(pointer, 0, MEM_RELEASE)
```

Danach wird der Pointer-Slot wieder auf Null gesetzt.

## Konstanten

- Pufferlaenge: 96 Bytes
- `MEM_COMMIT | MEM_RESERVE`: `0x3000` / `12288`
- `PAGE_READWRITE`: `0x04`
- `MEM_RELEASE`: `0x8000` / `32768`

## Kompatibilitaet

Die dBase-Syntax und die Qt5-Bridge-C-ABI bleiben unveraendert. Die Aenderung
betrifft ausschliesslich den erzeugten Windows-Assembler der dBase-Codegenerierung.
