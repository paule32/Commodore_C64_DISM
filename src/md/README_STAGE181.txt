Stage 181 - libruntime_mini.dll import for System.Objects
========================================================

Problem
-------
The COFF32 linker reported unresolved symbols:

    _jit_object_free
    _jit_object_instance_free
    _jit_object_class_type
    _jit_class_parent
    _jit_class_name
    _jit_dynstring_from_cstr
    _jit_class_instance_size
    _jit_inherits_from_object

Cause
-----
System.Objects declared its runtime functions as Pascal `cdecl; external;`.
Stage180 converted cdecl names to Win32 COFF symbols `_jit_*`, but the generated
unit assembly emitted only:

    extern _jit_object_free

That tells COFF that another object/archive must define the symbol. It does NOT
create a PE DLL import.

Stage181 solution
-----------------
System.Objects now emits real assembler import metadata:

    import _jit_object_free, "libruntime_mini.dll", "jit_object_free"

The three operands have distinct meanings:

    _jit_object_free       local COFF32 cdecl symbol used by CALL relocations
    libruntime_mini.dll    DLL written to the PE import descriptor
    jit_object_free        exported member name requested from the DLL

The same mapping is emitted for all 10 runtime functions in System.Objects.

The internal assembler writes this mapping into its COFF32 `.drectve` metadata.
The internal COFF32 linker reads that metadata, creates a JMP-[IAT] thunk and
builds `.idata`. No MinGW/ld/link.exe is involved.

Fallback for old .o files
-------------------------
Stage181 also adds the same 10 mappings to PE32_DEFAULT_IMPORTS. Therefore an
older System.Objects.coff32.o that contains only `_jit_*` external relocations
can still link successfully. `_resolve_pe32_default_import()` strips the leading
COFF cdecl underscore and maps the name to libruntime_mini.dll.

Runtime placement
-----------------
For a PE32 EXE use the 32-bit libruntime_mini.dll. Put it beside the generated
EXE (or in another Windows DLL search path). The integrated linker does not need
the DLL file to create a name import, but the Windows loader needs it when the
EXE starts.

Export names
------------
Stage181 expects these DLL export names WITHOUT the COFF leading underscore:

    jit_object_instance_new
    jit_object_instance_free
    jit_object_free
    jit_object_class_type
    jit_class_parent
    jit_class_name
    jit_class_instance_size
    jit_inherits_from_class
    jit_inherits_from_object
    jit_dynstring_from_cstr

If your DLL exports names with a different spelling, the third operand of the
`import` directive must be adjusted accordingly.

ANTLR
-----
Stage181 does not change Lexer.g4 or Parser.g4. If Stage180 grammar has already
been regenerated with ANTLR 4.13.2, no additional ANTLR regeneration is needed
for this import fix. The included c64pascal grammar remains the Stage180 grammar.
