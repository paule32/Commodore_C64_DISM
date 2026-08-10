from __future__ import annotations

import importlib.util
import struct
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from d64dbase import (
    DBaseSetDebugStatement,
    compile_dbase_to_assembly,
    dbase_uses_debug_output,
    parse_dbase_statements,
)


def load_d64_dism():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dism_dbase_embedded_console_stage4_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("d64_dism.py konnte nicht geladen werden")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseEmbeddedConsoleStage4Tests(unittest.TestCase):
    def test_set_debug_ast_and_output_routing(self):
        source = (
            "SET FORMAT TO CONSOLE\n"
            "SET DEBUG ON\n"
            "?? \"D=\"\n"
            "? 2 + 3\n"
            "SET DEBUG OFF\n"
            "? \"C\"\n"
        )
        statements = parse_dbase_statements(source)
        debug = [item for item in statements if isinstance(item, DBaseSetDebugStatement)]
        self.assertEqual([item.enabled for item in debug], [True, False])
        result = compile_dbase_to_assembly(source)
        self.assertEqual(result.debug_transcript, "D=5\r\n")
        self.assertEqual(result.transcript, "C\r\n")
        self.assertTrue(result.uses_debug_output)

    def test_debug_off_program_does_not_need_debug_tab(self):
        source = "SET FORMAT TO CONSOLE\nSET DEBUG OFF\n? \"nur Konsole\"\n"
        self.assertFalse(dbase_uses_debug_output(source))
        result = compile_dbase_to_assembly(source)
        self.assertFalse(result.uses_debug_output)
        self.assertNotIn("push -12", result.assembly)
        self.assertNotIn("mov ecx, -12", result.assembly)

    def test_no_external_console_or_command_processor_is_generated(self):
        source = "SET FORMAT TO CONSOLE\nSET DEBUG ON\n? \"debug\"\n"
        for target in ("pe32", "pe64"):
            asm = compile_dbase_to_assembly(source, target=target).assembly
            self.assertNotIn("AllocConsole", asm)
            self.assertNotIn("CreateProcessA", asm)
            self.assertNotIn("CreateNamedPipeA", asm)
            self.assertNotIn("cmd.exe", asm.casefold())
            self.assertNotIn("command.com", asm.casefold())
            self.assertNotIn("GetStdHandle", asm)
            self.assertNotIn("WriteFile", asm)
            self.assertIn("DBaseQtAppendConsole", asm)
            self.assertIn("DBaseQtAppendDebug", asm)

    def test_pe32_and_pe32plus_link_with_stdout_stderr_runtime(self):
        d64 = load_d64_dism()
        source = (
            "X = 2 + 3 * 4\n"
            "? \"X=\" + X\n"
            "SET FORMAT TO CONSOLE\n"
            "SET DEBUG ON\n"
            "? \"DX=\" + X\n"
            "SET DEBUG OFF\n"
            "?? \"done\"\n"
        )
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="stage4_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="stage4_64.asm", gui=True)
            )
            self.assertTrue(program.executable.startswith(b"MZ"))
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)

    def test_d64_gui_source_contains_embedded_console_process_wiring(self):
        text = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
        self.assertNotIn("def build_dbase_qt5_runtime_dll", text)
        self.assertNotIn("def ensure_dbase_qt5_runtime", text)
        self.assertIn("def _launch_dbase_qt5_gui", text)
        self.assertIn("d64qt5.dll", text)
        self.assertIn("subprocess.Popen([str(output_path)]", text)
        self.assertNotIn("process.readyReadStandardOutput.connect", text)
        self.assertNotIn("mingw32-make", text)
        self.assertNotIn("qmake.exe", text)


if __name__ == "__main__":
    unittest.main()
