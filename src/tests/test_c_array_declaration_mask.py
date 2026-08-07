from pathlib import Path
import unittest

from c64c.compiler import _lower_c_type_extensions
from c64c.preprocessor import preprocess_c_source


ROOT = Path(__file__).resolve().parents[1]


class CArrayDeclarationMaskTests(unittest.TestCase):
    @staticmethod
    def _lower(source: str):
        preprocessed = preprocess_c_source(
            source,
            filename="array_declaration_mask.c",
            include_paths=[ROOT / "c64c" / "include"],
            predefined_macros={"__D64_TARGET_C64__": 1},
        )
        return _lower_c_type_extensions(preprocessed)

    def test_return_array_access_is_not_mistaken_for_declaration(self):
        lowered = self._lower(
            """
static unsigned char values[256];

int load_value(unsigned int index)
{
    return values[index];
}
"""
        )
        text = lowered.preprocessed.source
        self.assertIn("static unsigned char values;", text)
        self.assertIn("return __d64_arr_get_1(values, index);", text)
        self.assertEqual(
            [(item.name, item.dimensions) for item in lowered.array_declarations],
            [("values", ("256",))],
        )

    def test_array_examples_in_comments_and_literals_are_ignored(self):
        lowered = self._lower(
            r'''
/* unsigned int CommentArray[256]; */
static unsigned char values[16];
const char *text = "FakeArray[12]";

int load_value(unsigned int index)
{
    // return CommentArray[index];
    return values[index];
}
'''
        )
        self.assertEqual(
            [(item.name, item.dimensions) for item in lowered.array_declarations],
            [("values", ("16",))],
        )
        self.assertIn("/* unsigned int CommentArray[256]; */", lowered.preprocessed.source)
        self.assertIn('"FakeArray[12]"', lowered.preprocessed.source)

    def test_graphics_flood_load_keeps_both_array_indices(self):
        source_path = ROOT / "runtime" / "graphics" / "common" / "graphics_api.c"
        preprocessed = preprocess_c_source(
            source_path.read_text(encoding="utf-8"),
            filename=str(source_path),
            include_paths=[ROOT / "c64c" / "include", ROOT / "runtime" / "graphics" / "include"],
            predefined_macros={"__D64_TARGET_C64__": 1},
        )
        lowered = _lower_c_type_extensions(preprocessed)
        lines = lowered.preprocessed.source.splitlines()
        flood_function = "\n".join(lines[305:320])
        self.assertIn("__d64_arr_get_1(GfxFloodXLow, index)", flood_function)
        self.assertIn("__d64_arr_get_1(GfxFloodXHigh, index)", flood_function)
        names = [item.name for item in lowered.array_declarations]
        self.assertEqual(names.count("GfxFloodXLow"), 1)
        self.assertNotIn("GfxFloodX", names)


if __name__ == "__main__":
    unittest.main()
