"""ANTLR-basierter Pascal-zu-6510-Compiler fuer den Commodore C64."""

from .compiler import (
    C64PascalError,
    GeneratedAssembly,
    compile_pascal_to_assembly,
)

__all__ = [
    "C64PascalError",
    "GeneratedAssembly",
    "compile_pascal_to_assembly",
]

