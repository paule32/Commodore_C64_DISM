[Deutsch](STAGE479_OUTPUT_DIRECTORIES_ASSEMBLER_SYNTAX.md) | [English](STAGE479_OUTPUT_DIRECTORIES_ASSEMBLER_SYNTAX.en.md)

# Stage 479 – Separate Windows Output Directories and Assembler Mode

Project Settings → Compiler → Output Directory now separates **assembler intermediates** (`.asm` and generated `.extern.inc`/`.payload.inc`) from **executable output** (`.o`/`.obj`, `.exe`, `.dll`) for PE32 and PE32+. Each has a directory chooser; the existing output path remains as a compatibility default. The **relative paths** option affects both and resolves them against the project at build time. A new Assembler → Assembler Mode option selects supported syntax behavior. Tests check independent architecture-specific paths, persistence, and build routing.
