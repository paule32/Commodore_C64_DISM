from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from c64c.compiler import compile_c_to_assembly
from c64c.preprocessor import preprocess_c_source


ADVANCED_SOURCE = r"""
#include <stdio.h>
#include <set.h>

#define BASE_VALUE 3
#define DOUBLE(value) ((value) + (value))

typedef enum TColor
{
    colorBlack,
    colorRed,
    colorGreen,
    colorBlue
} TColor;

typedef set<TColor> TColorSet;

typedef struct TPoint
{
    int x;
    int y;
} TPoint;

struct TCounter
{
    int value;
};

int Factorial(int value)
{
    int partial;

    if (value <= 1)
        return 1;

    partial = Factorial(value - 1);
    return value * partial;
}

int PersistentCounter(void)
{
    static int counter = 40;
    counter++;
    return counter;
}

int main(void)
{
    TPoint point;
    struct TCounter counter;
    TColorSet colors;
    int result;

    point.x = BASE_VALUE;
    point.y = DOUBLE(BASE_VALUE);
    counter.value = 10;
    colors = SET_ADD(SET_EMPTY(), colorBlue);

    {
        int result;
        result = point.x + point.y;
        printf("inner=%d\n", result);
    }

    result = Factorial(5);
    result = result + PersistentCounter();
    return result + counter.value + SET_HAS(colors, colorBlue);
}
"""


class CAdvancedFeatureTests(unittest.TestCase):
    def test_preprocessor_supports_elif_and_function_macros(self) -> None:
        source = r"""
#define VALUE 4
#define DOUBLE(x) ((x) + (x))
#if VALUE == 1
int selected = 1;
#elif VALUE == 4
int selected = DOUBLE(VALUE);
#else
int selected = 0;
#endif
"""
        result = preprocess_c_source(source, filename="macros.c")
        self.assertIn("int selected = ((4) + (4));", result.source)
        self.assertNotIn("selected = 1", result.source)

    def test_amiga_uses_stackframes_static_data_enum_set_and_structs(self) -> None:
        generated = compile_c_to_assembly(
            ADVANCED_SOURCE,
            filename="advanced.c",
            target="amiga",
        )
        assembly = generated.assembly

        self.assertIn("Factorial:", assembly)
        self.assertIn("bsr Factorial", assembly)
        self.assertIn("move.l a6,-(sp)", assembly)
        self.assertIn("move.l sp,a6", assembly)
        self.assertRegex(assembly, r"lea -[0-9]+\(a6\),a0")
        self.assertIn("__c_static_persistentcounter_", assembly)
        self.assertIn("dc.w $0028", assembly)
        self.assertGreaterEqual(generated.enum_count, 1)
        self.assertGreaterEqual(generated.set_count, 1)
        self.assertGreaterEqual(generated.structure_count, 2)

    def test_c64_saves_recursive_frame_pointer(self) -> None:
        generated = compile_c_to_assembly(
            ADVANCED_SOURCE,
            filename="advanced.c",
            target="c64",
        )
        assembly = generated.assembly

        self.assertIn("Factorial:", assembly)
        self.assertIn("jsr Factorial", assembly)
        self.assertIn("frame_pointer", assembly)
        self.assertIn("tsx", assembly)
        self.assertIn("txs", assembly)
        self.assertIn("__c_static_persistentcounter_", assembly)

    def test_pragma_link_module_can_be_recursive_and_keep_static_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module = root / "recursive.c"
            module.write_text(
                "int Factorial(int value) {\n"
                "  int partial;\n"
                "  if (value <= 1) return 1;\n"
                "  partial = Factorial(value - 1);\n"
                "  return value * partial;\n"
                "}\n"
                "int Counter(void) {\n"
                "  static int value = 7;\n"
                "  value++;\n"
                "  return value;\n"
                "}\n",
                encoding="utf-8",
            )
            main = root / "main.c"
            main.write_text(
                '#pragma link "recursive.c"\n'
                "int Factorial(int value);\n"
                "int Counter(void);\n"
                "int main(void) {\n"
                "  int result;\n"
                "  result = Factorial(5);\n"
                "  return result + Counter();\n"
                "}\n",
                encoding="utf-8",
            )

            generated = compile_c_to_assembly(
                main.read_text(encoding="utf-8"),
                filename=str(main),
                target="amiga",
            )

            self.assertEqual(len(generated.linked_c_files), 1)
            self.assertIn("Factorial:", generated.assembly)
            self.assertIn("Counter:", generated.assembly)
            self.assertIn("bsr Factorial", generated.assembly)
            self.assertIn("bsr Counter", generated.assembly)


if __name__ == "__main__":
    unittest.main()
