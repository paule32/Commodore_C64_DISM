# PE64 ReadLn input buffer via VirtualAlloc

The Windows PE64 Pascal runtime no longer emits the ReadLn input buffer as a large
initialized zero-byte array in `.data`.

Old layout:

```asm
__pas_read_count:   dd 0
__pas_input_buffer: db 0, 0, 0, ...
```

New layout:

```asm
__pas_read_count:   dd 0
__pas_input_buffer: dq 0
```

On the first `ReadLn` call the runtime performs the equivalent of:

```c
VirtualAlloc(NULL, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
```

The resulting address is stored in `__pas_input_buffer` and reused by later
`ReadLn` calls. `ReadFile` reads at most 4095 bytes so the final byte remains
available for the zero terminator.

The memory is process-owned and Windows releases it automatically when the PE64
process exits. The buffer is deliberately kept alive between calls because
`ReadLn` returns its address to Pascal code.

The internal PE64 linker recognizes `VirtualAlloc` as a `kernel32.dll` import and
uses the existing stack-to-Microsoft-x64 ABI adapter with four arguments.

## Size effect

In a minimal internal PE64 comparison, replacing a 4096-byte initialized `.data`
buffer with the 8-byte pointer plus `VirtualAlloc` reduced the resulting image from
5632 bytes to 2048 bytes. The exact saving in a real program depends on PE file
alignment and the rest of `.data`.
