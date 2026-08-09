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

from d64logo import LogoCompilerError, compile_logo_to_assembly


def load_d64_dism():
    # d64_dism imports the project's generated flags_rc module at top level.
    # The compiler/linker tests do not need resource constants, so a temporary
    # in-memory module is sufficient when the test is run standalone.
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dism_logo_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("d64_dism.py konnte nicht geladen werden")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class LogoCompilerTests(unittest.TestCase):
    def test_start_is_center_and_square_returns_to_start(self):
        result = compile_logo_to_assembly(
            "steps 60\nright 90\nsteps 40\nright 90\n"
            "steps 60\nright 90\nsteps 40\n",
            filename="square.logo",
            target="pe32",
            windows_application_mode="console",
        )
        self.assertEqual((result.final_x, result.final_y), (160, 100))
        self.assertEqual(result.final_heading, 270.0)
        self.assertEqual(len(result.segments), 4)

    def test_bilingual_absolute_directions(self):
        result = compile_logo_to_assembly(
            "rechts steps 10\nrunter steps 10\nlinks steps 10\nhoch steps 10\n",
            filename="de.logo",
            target="pe32",
            windows_application_mode="gui",
        )
        self.assertEqual((result.final_x, result.final_y), (160, 100))
        self.assertEqual(result.final_heading, 270.0)

    def test_go_direction_forms(self):
        result = compile_logo_to_assembly(
            "go east 20\ngo south steps 10\ngo west 20\ngo north steps 10\n",
            filename="go.logo",
            target="pe32",
        )
        self.assertEqual((result.final_x, result.final_y), (160, 100))

    def test_bad_command_reports_line(self):
        with self.assertRaises(LogoCompilerError) as caught:
            compile_logo_to_assembly(
                "steps 5\nwarp 20\n",
                filename="bad.logo",
                target="pe32",
            )
        self.assertEqual(caught.exception.line, 2)
        self.assertIn("warp", str(caught.exception))

    def test_console_and_gui_assembly_link_with_internal_pe32_toolchain(self):
        d64 = load_d64_dism()
        source = "east steps 20\nsouth steps 10\nwest steps 20\nnorth steps 10\n"
        for mode, gui in (("console", False), ("gui", True)):
            result = compile_logo_to_assembly(
                source,
                filename=f"native_{mode}.logo",
                target="pe32",
                windows_application_mode=mode,
            )
            program = d64.assemble_pe32_source(
                result.assembly,
                filename=f"native_{mode}.asm",
                gui=gui,
            )
            self.assertTrue(program.executable.startswith(b"MZ"))
            pe_offset = struct.unpack_from("<I", program.executable, 0x3C)[0]
            optional = pe_offset + 24
            subsystem = struct.unpack_from("<H", program.executable, optional + 68)[0]
            self.assertEqual(subsystem, 2 if gui else 3)

    def test_graphics_runtime_has_window_lifetime_api(self):
        d64 = load_d64_dism()
        self.assertIn("GraphicsWindowOpen", d64.WINDOWS_GRAPHICS_RUNTIME_HEADER)
        self.assertIn("InitGraphics320x200", d64.WINDOWS_GRAPHICS_RUNTIME_HEADER)
        self.assertIn("D64_GRAPHICS_API int GraphicsWindowOpen(void)", d64.WINDOWS_GRAPHICS_RUNTIME_CPP)
        self.assertIn("static uint32_t g_pixels[320 * 200]", d64.WINDOWS_GRAPHICS_RUNTIME_CPP)
        self.assertIn("d64_init_graphics_window(320u, 200u)", d64.WINDOWS_GRAPHICS_RUNTIME_CPP)


if __name__ == "__main__":
    unittest.main(verbosity=2)
