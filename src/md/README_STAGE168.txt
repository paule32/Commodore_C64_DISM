Stage 168 – MSZIP direkt im d64_dism.py-Toolchainpfad
======================================================

F2/Build PE32:
  Sprache -> interner Compiler -> ASM -> interner IA-32-Assembler -> COFF32 ->
  interner COFF32-Linker -> Relocations/IAT -> MSZIP(.text) -> .loader/.ztext -> EXE

Direkte PE32-ASM-Dateien laufen ebenfalls über link_coff32_objects().
Kompilierte Pascal/C/LISP/PROLOG/dBase-Dateien laufen über
_write_pe32_generated_objects() -> link_coff32_inputs() -> link_coff32_objects().

Es wird kein externes Packprogramm, kein externer Assembler/Linker und kein
mingw32-make für diesen Vorgang verwendet.

Windows-Buildzeit:
  Cabinet.dll: CreateCompressor / Compress / CloseCompressor

EXE-Laufzeit (.loader):
  Cabinet.dll: CreateDecompressor / Decompress / CloseDecompressor
  kernel32.dll: VirtualProtect / FlushInstructionCache / ExitProcess

D64Z-v1 enthält Magic, Version, Algorithmus, Flags, originale .text-RVA,
Originalgröße, gepackte Größe, ursprünglichen EntryPoint und CRC32.

Die virtuelle .text-RVA und VirtualSize bleiben bestehen. Im gepackten Modus
hat .text keinen Raw-Dateiblock; der Windows-Loader reserviert den Bereich und
.loader stellt ihn vor dem Sprung zum ursprünglichen EntryPoint wieder her.
Andere Sektionen werden durch den Packschritt nicht umgeschrieben.

PE32-EXE-Kompression ist unter Windows standardmäßig aktiv. DLLs werden in
dieser ersten Stufe absichtlich nicht gepackt.
