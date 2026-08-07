import json
import tempfile
import unittest
from pathlib import Path

from c64c import C64CPreprocessor, C64PreprocessorError
from c64pascal import (
    C64PascalError,
    compile_pascal_to_assembly,
    preprocess_pascal_source,
)
from d64_dism import main as dism_main


class PascalPreprocessorTests(unittest.TestCase):
    def test_macro_expansion_comparisons_and_diagnostics(self):
        source = """program Conditions;
{$define BASE 2}
{$define VERSION BASE}
{$info VERSION selected}
{$if VERSION >= 2}
const Selected = 7;
{$else}
const Selected = 9;
{$endif}
{$if VERSION <= 2}
{$warn supported}
{$endif}
begin
  WriteLn(Selected);
end.
"""
        result = preprocess_pascal_source(source, filename="conditions.pas")
        self.assertIn("const Selected = 7;", result.source)
        self.assertNotIn("const Selected = 9;", result.source)
        self.assertEqual("BASE", result.macros["version"])
        self.assertIn("2 selected", str(result.notes[0]))
        self.assertIn("supported", str(result.warnings[0]))
        generated = compile_pascal_to_assembly(source, filename="conditions.pas")
        self.assertEqual(1, len(generated.notes))
        self.assertEqual(1, len(generated.warnings))

    def test_all_comparison_operators_and_inactive_error(self):
        operators = ("==", "!=", "<>", ">=", "<=", "<", ">")
        expressions = ("2 == 2", "2 != 3", "2 <> 3", "2 >= 2", "2 <= 2", "2 < 3", "3 > 2")
        directives = "\n".join(
            f"{{$if {expression}}}\n{{$else}}\n{{$error failed {operator}}}\n{{$endif}}"
            for operator, expression in zip(operators, expressions)
        )
        preprocess_pascal_source(directives, filename="operators.pas")

    def test_active_error_stops_compilation(self):
        with self.assertRaisesRegex(C64PascalError, "intentional"):
            preprocess_pascal_source("{$error intentional}", filename="broken.pas")


class CPreprocessorConditionTests(unittest.TestCase):
    def test_if_expands_macros_and_comparisons(self):
        source = """#define BASE 1
#define FOO BASE
#info FOO selected
#if FOO == 1
int selected = 7;
#else
#error wrong branch
#endif
#if FOO >= 1 && FOO <= 1 && FOO < 2 && FOO > 0 && FOO != 2
#warning supported
#endif
"""
        result = C64CPreprocessor().process(source, filename="conditions.c")
        self.assertIn("int selected = 7;", result.source)
        self.assertEqual(1, len(result.notes))
        self.assertEqual(1, len(result.warnings))
        self.assertIn("1 selected", str(result.notes[0]))

    def test_active_error_stops_preprocessing(self):
        with self.assertRaisesRegex(C64PreprocessorError, "intentional"):
            C64CPreprocessor().process("#if 2 > 1\n#error intentional\n#endif\n")

    def test_function_macro_token_paste_and_stringification(self):
        source = """#define PREFIX(param) FOO_ ## param
#define PAIR_NAME(param1, param2) \\
    PAIR_ ## param1 ## _ ## param2
#define STRINGIFY(param) #param
int PREFIX(VALUE) = 3;
int PAIR_NAME(LEFT, RIGHT) = 4;
const char *name = STRINGIFY(FOO_VALUE);
"""
        result = C64CPreprocessor().process(source, filename="paste.c")
        self.assertIn("int FOO_VALUE = 3;", result.source)
        self.assertIn("int PAIR_LEFT_RIGHT = 4;", result.source)
        self.assertIn('"FOO_VALUE"', result.source)

    def test_self_include_with_guard_is_inactive(self):
        with tempfile.TemporaryDirectory() as directory:
            header = Path(directory) / "guarded.h"
            header.write_text(
                "#ifndef GUARDED_H\n"
                "#define GUARDED_H\n"
                "#include \"guarded.h\"\n"
                "#define GUARDED_VALUE 7\n"
                "#endif\n",
                encoding="utf-8",
            )
            result = C64CPreprocessor(include_paths=[directory]).process(
                '#include "guarded.h"\nint value = GUARDED_VALUE;\n',
                filename=str(Path(directory) / "main.c"),
            )
            self.assertIn("int value = 7;", result.source)
            self.assertEqual((str(header.resolve()),), result.included_files)

    def test_self_include_without_guard_reports_cycle(self):
        with tempfile.TemporaryDirectory() as directory:
            header = Path(directory) / "unguarded.h"
            header.write_text('#include "unguarded.h"\n', encoding="utf-8")
            with self.assertRaisesRegex(C64PreprocessorError, "Zirkulaeres #include"):
                C64CPreprocessor(include_paths=[directory]).process(
                    '#include "unguarded.h"\n',
                    filename=str(Path(directory) / "main.c"),
                )


class PascalUnitInterfaceTests(unittest.TestCase):
    def test_uses_creates_and_prefers_pui(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unit = root / "Values.pas"
            unit.write_text(
                "unit Values;\ninterface\nconst Answer = 42;\nimplementation\nend.\n",
                encoding="utf-8",
            )
            main = "program Main;\nuses Values;\nbegin\nWriteLn(Answer);\nend.\n"
            generated = compile_pascal_to_assembly(
                main,
                filename=str(root / "main.pas"),
                include_paths=[root],
            )
            self.assertIn("#$2A", generated.assembly)
            pui = root / "Values.pui"
            self.assertTrue(pui.is_file())
            document = json.loads(pui.read_text(encoding="utf-8"))
            self.assertEqual("d64pascal-pui", document["format"])
            self.assertIn("Answer", document["interface"]["symbols"]["constants"])

            unit.write_text(
                "unit Values;\ninterface\nconst Answer = 99;\nimplementation\nend.\n",
                encoding="utf-8",
            )
            preferred = compile_pascal_to_assembly(
                main,
                filename=str(root / "main.pas"),
                include_paths=[root],
            )
            self.assertIn("#$2A", preferred.assembly)
            self.assertNotIn("#$63", preferred.assembly)

            unit.unlink()
            pui_only = compile_pascal_to_assembly(
                main,
                filename=str(root / "main.pas"),
                include_paths=[root],
            )
            self.assertIn("#$2A", pui_only.assembly)

    def test_guarded_self_use_is_inactive_and_guard_is_stored_in_pui(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unit = root / "GuardedUnit.pas"
            unit.write_text(
                "{$ifndef __GUARDED_UNIT_PAS_}\n"
                "{$define __GUARDED_UNIT_PAS_}\n"
                "unit GuardedUnit;\n"
                "interface\n"
                "uses GuardedUnit;\n"
                "const GuardedValue = 6;\n"
                "implementation\n"
                "end.\n"
                "{$endif}\n",
                encoding="utf-8",
            )
            generated = compile_pascal_to_assembly(
                "program Main; uses GuardedUnit; begin WriteLn(GuardedValue); end.",
                filename=str(root / "main.pas"),
                include_paths=[root],
            )
            self.assertIn("#$06", generated.assembly)
            document = json.loads(
                unit.with_suffix(".pui").read_text(encoding="utf-8")
            )
            self.assertEqual("__GUARDED_UNIT_PAS_", document["guard"])


class CommandLineCompilerTests(unittest.TestCase):
    def test_write_c64_with_unit_include_path_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "CliValues.pas").write_text(
                "unit CliValues;\ninterface\nconst Value = 3;\nimplementation\nend.\n",
                encoding="utf-8",
            )
            source = root / "main.pas"
            source.write_text(
                "program Main;\nuses CliValues;\nbegin\nWriteLn(Value);\nend.\n",
                encoding="utf-8",
            )
            output = root / "custom.prg"
            result = dism_main(
                [
                    "--write-c64",
                    str(source),
                    "-Fi",
                    str(root),
                    "-o",
                    str(output),
                ]
            )
            self.assertEqual(0, result)
            self.assertTrue(output.is_file())
            self.assertTrue(source.with_suffix(".generated.asm").is_file())

    def test_write_amiga_c_uses_default_adf_name(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "hello.c"
            source.write_text(
                '#include <stdio.h>\nint main(void) { printf("Hello\\n"); return 0; }\n',
                encoding="utf-8",
            )
            self.assertEqual(0, dism_main(["--write-amiga", str(source)]))
            output = source.with_suffix(".adf")
            self.assertEqual(901120, output.stat().st_size)
            self.assertTrue(source.with_suffix(".generated.amiga.asm").is_file())


if __name__ == "__main__":
    unittest.main()

class PascalRoutinePuiTests(unittest.TestCase):
    def test_graphics_pui_contains_global_routines(self):
        root = Path(__file__).resolve().parents[1]
        unit = root / "c64pascal" / "units" / "System" / "Graphics.pas"
        from c64pascal import write_pascal_unit_interface
        pui = write_pascal_unit_interface(unit)
        document = json.loads(pui.read_text(encoding="utf-8"))
        routines = document["interface"]["routines"]
        names = {item["name"] for item in routines}
        self.assertIn("SetPixel", names)
        self.assertIn("GetPixel", names)
        get_pixel = next(item for item in routines if item["name"] == "GetPixel")
        self.assertEqual("TColor", get_pixel["result_type"])
        self.assertEqual(2, len(get_pixel["parameters"]))
