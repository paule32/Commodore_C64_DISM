"""Stage 537: Pascal optimization configuration and codegen smoke tests.

ANTLR 4.13.2 parser is not needed for these AST-level checks; native PE32/PE64
Windows execution and full IDE GUI visual testing remain separate.
"""
import ast
import configparser
from pathlib import Path
import unittest

from pascal_optimizer import normalize_optimization_level, optimize_assembler
from test_stage532 import _compiler

ROOT = Path(__file__).resolve().parent
D64 = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage537Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = _compiler()
        cls.pos = cls.c.SourcePosition(1, 1)

    def _program(self):
        c, p = self.c, self.pos
        routine = c.GlobalRoutineImplementation(
            "function", "NextValue",
            (c.ParameterDeclaration(("Value",), "integer", "value", p),),
            "integer", (c.VarDeclaration(("Next",), "integer", None, p),),
            c.CompoundStatement(p, (
                c.AssignmentStatement(p, "Next", c.BinaryExpression(
                    p, c.NameExpression(p, "Value"), "+", c.LiteralExpression(p, 1))),
                c.IfStatement(p, c.BinaryExpression(
                    p, c.NameExpression(p, "Next"), ">", c.LiteralExpression(p, 5)),
                    c.AssignmentStatement(p, "Result", c.NameExpression(p, "Next")),
                    c.AssignmentStatement(p, "Result", c.BinaryExpression(
                        p, c.LiteralExpression(p, 3), "+", c.LiteralExpression(p, 4)))),
            )), p, "cdecl")
        return c.PascalProgram("Stage537", (), (), c.CompoundStatement(p, ()),
                               global_routines=(routine,))

    def test_normalize_levels(self):
        self.assertEqual([normalize_optimization_level(x) for x in
                          ("O0", "O1", "O2", "O3", "o3", "999", -5)],
                         [0, 1, 2, 3, 3, 0, 0])

    def test_peephole_safe_and_source_mapping(self):
        before = ["_start:", "    push eax", "    mov ecx, my_var",
                  "    pop eax", "    mov dword ptr [ecx], eax", "    ret",
                  "    jmp unreachable", "section .data", "x: dd 0"]
        mapped = {i+1: 10+i for i in range(len(before))}
        self.assertEqual(optimize_assembler(before, mapped, 0)[0], before)
        new, line_map = optimize_assembler(before, mapped, 1)
        self.assertNotIn("    push eax", new)
        self.assertNotIn("    pop eax", new)
        self.assertNotIn("    jmp unreachable", new)
        self.assertEqual(new[-2:], ["section .data", "x: dd 0"])
        self.assertEqual(len(line_map), len(new))

    def test_codegen_abi_locals_and_cookie_per_target_and_level(self):
        program = self._program()
        for target, cls, base in (
            ("pe32", self.c._PE32CodeGenerator, "ebp"),
            ("pe64", self.c._PE64CodeGenerator, "rbp")):
            for level in range(4):
                with self.subTest(target=target, level=level):
                    generated = cls(program, stack_protector=True,
                                    optimization_level=level).generate()
                    text = generated.assembly
                    self.assertIn("__pas_cookie_failure:", text)
                    self.assertIn("BCryptGenRandom", text)
                    self.assertIn("__pas_global_nextvalue:", text)
                    self.assertIn("section .data", text)
                    self.assertIn("section .bss", text)
                    in_bss = "__pas_local_global_nextvalue_next_" in text.split("section .bss", 1)[1]
                    self.assertEqual(in_bss, level < 2)
                    param_in_bss = "__pas_param_global_nextvalue_value_" in text.split("section .bss", 1)[1]
                    self.assertEqual(param_in_bss, level < 2)
                    if level >= 2:
                        self.assertIn("lea ecx, [ebp-" if base == "ebp"
                                      else "lea r11, [rbp-", text)
                        self.assertIn("lea ecx, [ebp+8]" if base == "ebp"
                                      else "lea r11, [rbp+16]", text)
                        self.assertRegex(text, r"j(?:le|be) __pas_if_else_\d+")
                    if target == "pe32":
                        self.assertIn("push ebx\n    push esi\n    push edi", text)
                        self.assertIn("mov ebx, dword ptr [ebp-8]", text)

    def test_O3_pure_constant_control_flow(self):
        c, p = self.c, self.pos
        inner = c.IfStatement(p, c.BinaryExpression(p, c.LiteralExpression(p, 1),
                    "=", c.LiteralExpression(p, 2)),
                c.CallStatement(p, "writeln", (c.LiteralExpression(p, 111),)),
                c.CallStatement(p, "writeln", (c.LiteralExpression(p, 222),)))
        program = c.PascalProgram("OptConst", (), (), c.CompoundStatement(p, (inner,)))
        ordinary = c._PE32CodeGenerator(program, optimization_level=0).generate().assembly
        optimized = c._PE32CodeGenerator(program, optimization_level=3).generate().assembly
        self.assertIn("mov eax, 111", ordinary)
        self.assertNotIn("mov eax, 111", optimized)
        self.assertIn("mov eax, 222", optimized)

    def test_independent_ini_sections(self):
        src = D64.replace("lazy from app_lang.deu import", "from app_lang.deu import")
        src = src.replace("lazy from app_lang.enu import", "from app_lang.enu import")
        tree = ast.parse(src)
        def run_loop(function_name, env):
            fn = next(f for f in tree.body if isinstance(f, ast.FunctionDef)
                      and f.name == function_name)
            node = next(n for n in fn.body if isinstance(n, ast.For) and
                        "Settings.Windows.{_suffix}.Compiler.Pascal.Optimierung"
                        in ast.get_source_segment(src, n))
            exec(compile(ast.fix_missing_locations(ast.Module(
                body=[node], type_ignores=[])), "<stage537>", "exec"), env)
        keys = {"pe32": "opt32", "pe64": "opt64"}
        def level(data):
            from pascal_optimizer import normalize_optimization_level
            return normalize_optimization_level(data.get("level", 0)
                  if isinstance(data, dict) else data)
        conf = configparser.ConfigParser(interpolation=None)
        conf.optionxform = str
        run_loop("format_project_ini", {"parser": conf,
                 "entries": {"opt32": [{"level": 1}], "opt64": [{"level": 3}]},
                 "PROJECT_WINDOWS_PASCAL_OPTIMIZATION_KEYS": keys,
                 "_stage537_optimizer_level": level,
                 "stage538_no_stack_frames": lambda row: bool(row.get("no_stack_frames", False)),
                 "_parse_project_bool": lambda value, default=False: str(value).lower() in ("true", "1", "yes")})
        self.assertEqual(conf.get("Settings.Windows.32Bit.Compiler.Pascal.Optimierung", "Level"), "O1")
        self.assertEqual(conf.get("Settings.Windows.64Bit.Compiler.Pascal.Optimierung", "Level"), "O3")
        restored = {}
        run_loop("parse_project_ini", {"parser": conf, "entries": restored,
                 "PROJECT_WINDOWS_PASCAL_OPTIMIZATION_KEYS": keys,
                 "_stage537_optimizer_level": level,
                 "stage538_no_stack_frames": lambda row: bool(row.get("no_stack_frames", False)),
                 "_parse_project_bool": lambda value, default=False: str(value).lower() in ("true", "1", "yes")})
        self.assertEqual(restored["opt32"], [{"level": 1, "no_stack_frames": False}])
        self.assertEqual(restored["opt64"], [{"level": 3, "no_stack_frames": False}])
        older = {}
        run_loop("parse_project_ini", {"parser": configparser.ConfigParser(),
                 "entries": older, "PROJECT_WINDOWS_PASCAL_OPTIMIZATION_KEYS": keys,
                 "_stage537_optimizer_level": level,
                 "stage538_no_stack_frames": lambda row: bool(row.get("no_stack_frames", False)),
                 "_parse_project_bool": lambda value, default=False: str(value).lower() in ("true", "1", "yes")})
        self.assertEqual(older["opt32"], [{"level": 0, "no_stack_frames": False}])
        self.assertEqual(older["opt64"], [{"level": 0, "no_stack_frames": False}])

    def test_gui_worker_dark_title_and_vcl_ownership(self):
        for expected in (
            'QGroupBox("Optimierung-Stufen: ", body)',
            '"compiler.pascal.optimization"',
            'self._pascal_optimization_pages',
            'panel.set_pascal_optimization_options',
            'compiler_kwargs["optimization_level"]',
            '"optimization_level": _stage537_optimizer_level(',
        ):
            self.assertIn(expected, D64)
        worker = (ROOT / "pascal_parallel_build.py").read_text(encoding="utf-8")
        self.assertIn('"optimization_level": job.get("optimization_level", 0)', worker)
        system = (ROOT / "system_information.py").read_text(encoding="utf-8")
        self.assertIn("DwmSetWindowAttribute", system)
        self.assertIn("showEvent(self, event)", system)
        vcl = (ROOT / "runtime/compiler/pascal/vcl/VCL.Windows.pas").read_text()
        self.assertNotIn("AppForm.Free;", vcl)


if __name__ == "__main__":
    unittest.main(verbosity=2)
