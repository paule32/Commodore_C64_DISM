"""ANTLR-basierter Pascal-Compiler für C64 (6510) und Amiga (68000)."""

from .compiler import (
    C64PascalError,
    GeneratedAssembly,
    PascalPreprocessResult,
    PascalPreprocessorDiagnostic,
    compile_pascal_to_assembly,
    parse_pascal,
    preprocess_pascal_source,
    write_pascal_unit_interface,
)

__all__ = [
    "C64PascalError",
    "GeneratedAssembly",
    "PascalPreprocessResult",
    "PascalPreprocessorDiagnostic",
    "compile_pascal_to_assembly",
    "parse_pascal",
    "preprocess_pascal_source",
    "write_pascal_unit_interface",
]
