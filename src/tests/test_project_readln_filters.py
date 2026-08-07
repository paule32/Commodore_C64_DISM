from pathlib import Path
import unittest

import d64_dism as mod

ROOT = Path(__file__).resolve().parents[1]
GUI_SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
PASCAL_SOURCE = (ROOT / "c64pascal" / "compiler.py").read_text(encoding="utf-8")


class ProjectMenuTests(unittest.TestCase):
    def test_project_is_first_new_menu_entry(self):
        start = GUI_SOURCE.index("def _populate_new_document_menu")
        end = GUI_SOURCE.index("def create_coff32_archive_dialog", start)
        block = GUI_SOURCE[start:end]
        self.assertLess(
            block.index("menu.addAction(self.new_project_action)"),
            block.index("menu.addAction(self.new_basic_action)"),
        )
        self.assertIn("def _save_project_before_new", GUI_SOURCE)
        self.assertIn("self.reset_project_tree()", GUI_SOURCE)


class WindowsModeTests(unittest.TestCase):
    def test_application_modes_and_macros(self):
        self.assertEqual(
            mod.WINDOWS_APPLICATION_MODES,
            ("Console", "GUI", "Direct2D", "Direct3D"),
        )
        self.assertIn("__D64_WINDOWS_CONSOLE__", mod.windows_application_predefined_macros("Console"))
        self.assertIn("__D64_WINDOWS_GUI__", mod.windows_application_predefined_macros("GUI"))
        self.assertIn("__D64_GRAPHICS_DIRECT2D__", mod.windows_application_predefined_macros("Direct2D"))
        self.assertIn("__D64_GRAPHICS_DIRECT3D__", mod.windows_application_predefined_macros("Direct3D"))

    def test_combo_has_separator_after_gui(self):
        self.assertIn('self.windows_graphics_combo.addItem("Console")', GUI_SOURCE)
        self.assertIn('self.windows_graphics_combo.addItem("GUI")', GUI_SOURCE)
        self.assertIn("self.windows_graphics_combo.insertSeparator(2)", GUI_SOURCE)
        self.assertIn('self.windows_graphics_combo.addItem("Direct2D")', GUI_SOURCE)
        self.assertIn('self.windows_graphics_combo.addItem("Direct3D")', GUI_SOURCE)


class FileFilterTests(unittest.TestCase):
    def test_only_three_platform_buttons_are_built(self):
        self.assertIn('for platform_name in ("C-64", "Amiga", "Windows"):', GUI_SOURCE)
        self.assertIn('source_menu = menu.addMenu("Quellcode")', GUI_SOURCE)
        self.assertIn('tools_menu = menu.addMenu("Tools")', GUI_SOURCE)
        self.assertIn('add_filter_action(menu, "Alle", "ALLE")', GUI_SOURCE)
        self.assertIn('add_filter_action(source_menu, "BASIC", "BASIC")', GUI_SOURCE)
        self.assertIn('add_filter_action(source_menu, "Pascal", "PAS")', GUI_SOURCE)
        self.assertIn('add_filter_action(source_menu, "C", "C")', GUI_SOURCE)
        self.assertIn('add_filter_action(source_menu, "Assembler", "ASM")', GUI_SOURCE)
        self.assertIn("self.directory_tree.setMinimumHeight(120)", GUI_SOURCE)


class ReadLnTests(unittest.TestCase):
    def test_readfile_is_internal_pe32_import(self):
        self.assertEqual(mod.PE32_DEFAULT_IMPORTS["readfile"], ("kernel32.dll", "ReadFile"))

    def test_pascal_backend_contains_readln_forms(self):
        self.assertIn('if name == "readln":', PASCAL_SOURCE)
        self.assertIn("def _compile_readln_call", PASCAL_SOURCE)
        self.assertIn("def _compile_readln_prompt", PASCAL_SOURCE)
        self.assertIn('self.runtime.add("readln")', PASCAL_SOURCE)
        self.assertIn('self.emitter.emit("    call ReadFile")', PASCAL_SOURCE)
        self.assertIn('if type_info == STRING_TYPE or type_info.kind == "class":', PASCAL_SOURCE)
        self.assertIn("return 4", PASCAL_SOURCE)


    def test_console_runtime_uses_real_console_devices(self):
        self.assertIn('self.emitter.emit("    call CreateFileA")', PASCAL_SOURCE)
        self.assertIn('_conin_name: db 67, 79, 78, 73, 78, 36, 0', PASCAL_SOURCE)
        self.assertIn('_conout_name: db 67, 79, 78, 79, 85, 84, 36, 0', PASCAL_SOURCE)
        self.assertEqual(
            mod.PE32_DEFAULT_IMPORTS["createfilea"],
            ("kernel32.dll", "CreateFileA"),
        )

    def test_console_launcher_does_not_redirect_stdio_to_devnull(self):
        start = GUI_SOURCE.index("def _launch_assembled_document")
        end = GUI_SOURCE.index("def _launch_amiga_document", start)
        block = GUI_SOURCE[start:end]
        self.assertIn('console_mode = (', block)
        self.assertIn('if not console_mode:', block)
        self.assertIn('"stdin": subprocess.DEVNULL', block)
        # Die DEVNULL-Zuweisung muss ausschließlich im Nicht-Console-Zweig liegen.
        console_pos = block.index('if not console_mode:')
        devnull_pos = block.index('"stdin": subprocess.DEVNULL')
        self.assertGreater(devnull_pos, console_pos)

    def test_internal_assembler_accepts_readln_runtime_addressing(self):
        source = '''
        bits 32
        global _start
        entry _start
        extern ReadFile
        _start:
            xor eax, eax
            mov ecx, 5
            mov byte ptr [eax+ecx], dl
        again:
            test ecx, ecx
            jz done
            dec ecx
            movzx edx, byte ptr [eax+ecx]
            cmp edx, 10
            je strip
            cmp edx, 13
            jne done
        strip:
            xor edx, edx
            mov byte ptr [eax+ecx], dl
            jmp again
        done:
            ; Eine echte Referenz erzeugen, damit der interne Linker
            ; ReadFile in die PE32-Importtabelle aufnimmt.
            call ReadFile
            ret
        '''
        raw = mod.assemble_pe32_coff_object(source, filename="readln-test.asm")
        linked = mod.link_coff32_objects((raw,), entry_symbol="_start", gui=True)
        self.assertTrue(linked.executable.startswith(b"MZ"))
        self.assertIn(b"ReadFile\0", linked.executable)


if __name__ == "__main__":
    unittest.main()
