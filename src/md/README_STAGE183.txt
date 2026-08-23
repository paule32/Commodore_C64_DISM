Stage 183 - System.Strings, {$L}, free Unit routines
=====================================================

Reported diagnostics
--------------------

  PASCAL PREPROCESS: ... unbekannte Pascal-Direktive ignoriert: L inttostr.o
  PASCAL PREPROCESS: ... unbekannte Pascal-Direktive ignoriert: L strtoint.o
  Syntaxfehler: mismatched input '(' expecting '.'

Two independent causes were fixed.

1) d64_dism.py has an outer Pascal preprocessor. It previously consumed {$L}
   as an unknown directive before c64pascal/compiler.py could see it. Stage183
   recognizes {$L} and {$LINK}, resolves .o/.obj/.a/.lib relative to the Pascal
   source file, and forwards those paths as linked_object_files.

2) The Pascal grammar had no rule for a free Unit implementation such as:

     function IntToStr(AValue: Integer): String;
     begin
       ...
     end;

   Stage183 adds globalRoutineImplementation and separates plain Unit-interface
   prototypes into globalRoutinePrototype.

Expected PE32 unit symbols
--------------------------

  global __pas_System_Strings_IntToStr
  global __pas_System_Strings_StrToInt

The implementation calls the object symbols:

  call __IntToStr
  call __StrToInt

The double leading underscore is intentional for Win32 COFF cdecl when the
source-level routine name itself starts with an underscore:

  _IntToStr  -> __IntToStr
  _StrToInt  -> __StrToInt

The dynamic-string helper remains a PE import:

  import _jit_dynstring_from_cstr,
         "libruntime_mini.dll",
         "jit_dynstring_from_cstr"

{$L} flow
---------

  {$L inttostr.o}
  {$L strtoint.o}
       |
       v
  d64_dism Pascal preprocessor
       |
       +--> link_files
       |
       v
  compile_pascal_to_assembly(... linked_object_files=...)
       |
       +--> GeneratedAssembly.linked_object_files
       +--> PUI implementation.objects
       |
       v
  internal COFF32 linker

No external linker is required.

ANTLR
-----
C64PascalParser.g4 changed in Stage183. Run compile.bat with ANTLR 4.13.2 and
then completely exit/restart d64_dism.py. The Lexer grammar is byte-identical
to Stage182.
