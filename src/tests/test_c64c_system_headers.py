from __future__ import annotations

import unittest
from pathlib import Path

from c64c import compile_c_to_assembly, preprocess_c_source


SOURCE = r"""
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

int main(void)
{
    size_t count = 5;
    ptrdiff_t difference = -2;
    uint8_t byte_value = UINT8_C(7);
    int8_t signed_byte = -1;
    uint16_t word_value = UINT16_C(1024);
    int16_t signed_word = INT16_C(-3);
    bool enabled = true;

    if (enabled) {
        count += byte_value;
    }
    return 0;
}
"""


class CSystemHeaderTests(unittest.TestCase):
    def test_builtin_headers_are_resolved_without_include_path(self) -> None:
        result = preprocess_c_source(SOURCE, filename="header_test.c")
        included = {Path(name).name for name in result.included_files}

        self.assertEqual(
            included,
            {"stddef.h", "stdint.h", "stdbool.h"},
        )
        self.assertIn("typedef unsigned int size_t;", result.source)
        self.assertIn("bool enabled = true;", result.source)

    def test_headers_compile_for_c64_and_amiga(self) -> None:
        c64 = compile_c_to_assembly(SOURCE, filename="header_test.c", target="c64")
        amiga = compile_c_to_assembly(SOURCE, filename="header_test.c", target="amiga")

        self.assertIn("MOS-6510", c64.assembly)
        self.assertIn("Motorola-68000", amiga.assembly)
        self.assertEqual(len(c64.included_files), 3)
        self.assertEqual(len(amiga.included_files), 3)


    def test_variadic_stdio_prototype_is_allowed(self) -> None:
        source = r"""
#include <stdio.h>

int main(void)
{
    printf("value=%d\n", 42);
    return 0;
}
"""
        generated = compile_c_to_assembly(
            source,
            filename="printf_header_test.c",
            target="c64",
        )

        self.assertIn("MOS-6510", generated.assembly)
        self.assertGreaterEqual(generated.prototype_count, 1)

    def test_c64_builtins_win_over_header_prototypes(self) -> None:
        source = r"""
#include <c64.h>

int main(void)
{
    unsigned char value;

    clrscr();
    poke(C64_SCREEN, 1);
    value = peek(C64_SCREEN);
    return lo(value) + hi(C64_SCREEN);
}
"""
        generated = compile_c_to_assembly(
            source,
            filename="c64_builtin_header_test.c",
            target="c64",
        )
        assembly = generated.assembly

        # Die Prototypen in c64.h dienen der Typpruefung. Die bekannten
        # C64-Routinen werden direkt vom Backend abgesenkt und duerfen nicht
        # als unaufgeloeste externe Symbole im Assembler erscheinen.
        self.assertNotIn("jsr clrscr", assembly)
        self.assertNotIn("jsr poke", assembly)
        self.assertNotIn("jsr peek", assembly)
        self.assertNotIn("jsr lo", assembly)
        self.assertNotIn("jsr hi", assembly)
        self.assertIn("lda #$93", assembly)
        self.assertIn("jsr $FFD2", assembly)
        self.assertIn("sta ($FB),y", assembly)
        self.assertIn("lda ($FB),y", assembly)

    def test_c64_builtin_aliases_are_lowered_too(self) -> None:
        source = r"""
#include <c64.h>

int main(void)
{
    c64_clrscr();
    c64_poke(C64_SCREEN, 2);
    return c64_peek(C64_SCREEN);
}
"""
        generated = compile_c_to_assembly(
            source,
            filename="c64_builtin_alias_test.c",
            target="c64",
        )
        assembly = generated.assembly

        self.assertNotIn("jsr c64_clrscr", assembly)
        self.assertNotIn("jsr c64_poke", assembly)
        self.assertNotIn("jsr c64_peek", assembly)
        self.assertNotIn("jsr clrscr", assembly)
        self.assertNotIn("jsr poke", assembly)
        self.assertNotIn("jsr peek", assembly)
        self.assertIn("lda #$93", assembly)

    def test_variadic_function_definition_remains_rejected(self) -> None:
        source = r"""
int custom_printf(const char *format, ...)
{
    return 0;
}

int main(void)
{
    return custom_printf("x");
}
"""
        with self.assertRaisesRegex(
            Exception,
            "Variadische Funktionsdefinitionen",
        ):
            compile_c_to_assembly(
                source,
                filename="variadic_definition_test.c",
                target="c64",
            )


if __name__ == "__main__":
    unittest.main()
