# -*- coding: utf-8 -*-
"""Stage 608 – dBASE RuntimeDB.dll packing, project policy and PE verification."""
from __future__ import annotations

import ast
import re
import types
import unittest
import zlib
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from d64dbase import compile_dbase_to_assembly, pe_dll_payload
from d64dbase.library_packing import DBaseLibraryPackingError, validate_library_packing
from test_stage605_link import _load_pe_linker

ROOT = Path(__file__).resolve().parent
OBJECTS = ROOT / 'runtime/dbase/src/System.Objects.prg'


def _main_tree():
    source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
    return ast.parse(re.sub(r'(?m)^(\s*)lazy (from|import)\b', r'\1\2', source))


class Stage608ProjectIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = _main_tree()
        cls.main_source = (ROOT / 'd64_dism.py').read_text('utf-8')

    def test_gui_build_checks_written_runtimedb_image(self):
        source = self.main_source
        start = source.index('        def assemble_generated_document(')
        end = source.index('        @staticmethod\n        def _c_source_has_main_definition', start)
        block = source[start:end]
        self.assertIn('self._dbase_class_library_packing_enabled(document.build_target)', block)
        self.assertIn('pack_dll=(\n                            _dbase_library_pack', block)
        self.assertIn('program.executable, document.build_target,', block)
        self.assertIn('output_path, document.build_target,', block)
        self.assertIn('DBASE DLL LINK (', block)
        self.assertIn('DBASE DLL DATEI (', block)
        self.assertIn('except (OSError, ResourceCompilerError, ValueError) as exc:', block)

    def test_visible_checkbox_controls_snapshot_for_each_architecture(self):
        method = next(node for node in ast.walk(self.tree) if isinstance(node, ast.FunctionDef)
                      and node.name == '_dbase_class_library_packing_enabled')
        ns = {'PE_PACKING_DEFAULT': False, '_set_pe_packing_enabled': lambda t, v: None}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                     '<policy>', 'exec'), ns)
        fn = ns['_dbase_class_library_packing_enabled']
        state = types.SimpleNamespace(
            _project_windows_target_key=lambda t: str(t).lower(),
            project_windows_pe_packing_enabled={'pe32': False, 'pe64': True},
            project_windows_console_dll_pack={'pe32': False, 'pe64': False},
            project_settings_panel=None,
        )
        self.assertFalse(fn(state, 'pe32'))
        self.assertTrue(fn(state, 'pe64'))
        live = {'pe32': True, 'pe64': False}
        page = lambda target: types.SimpleNamespace(
            pe_packing_enabled=lambda: live[target],
            console_runtime_pack_checkbox=types.SimpleNamespace(isChecked=lambda: False)
        )
        state.project_settings_panel = types.SimpleNamespace(page_for_target=page)
        self.assertTrue(fn(state, 'pe32'))
        self.assertFalse(fn(state, 'pe64'))
        self.assertEqual(state.project_windows_pe_packing_enabled,
                         {'pe32': True, 'pe64': False})
        # The separate Runtime "pack dll" toggle must also pack RuntimeDB.dll.
        state.project_settings_panel = None
        state.project_windows_console_dll_pack['pe64'] = True
        self.assertTrue(fn(state, 'pe64'))
        state.project_windows_console_dll_pack['pe64'] = False
        self.assertFalse(fn(state, 'pe64'))


class Stage608LinkerPacking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.link = _load_pe_linker()
        source = OBJECTS.read_text('utf-8')
        cls.coff = {}
        for target in ('pe32', 'pe64'):
            program = compile_dbase_to_assembly(
                source, target=target, filename=str(OBJECTS), source_kind='library')
            obj = cls.link[f'assemble_{target}_object_source'](program.assembly, filename=str(OBJECTS))
            cls.coff[target] = cls.link[f'write_coff{32 if target=="pe32" else 64}_object'](obj)

    def _link(self, target, enabled):
        func = self.link[f'link_coff{32 if target=="pe32" else 64}_objects']
        with patch.object(pe_dll_payload, 'mszip_compress',
                          side_effect=lambda data: zlib.compress(data, 9)):
            result = func((self.coff[target],), entry_symbol='__d64_dll_entry',
                          dll=True, dll_name='RuntimeDB.dll', pack_dll=enabled)
        return result.executable

    def test_both_architectures_link_real_class_dll_packed_and_unpacked(self):
        for target in ('pe32', 'pe64'):
            for packed in (False, True):
                with self.subTest(target=target, packed=packed):
                    binary = self._link(target, packed)
                    info = validate_library_packing(binary, target, requested=packed)
                    self.assertEqual(info['packed'], packed)
                    pe = pe_dll_payload.parse_pe(binary)
                    sections = {s['name'] for s in pe['secs']}
                    self.assertEqual(b'.ztext' in sections, packed)
                    if packed:
                        self.assertIn(b'.loader', sections)
                        self.assertGreater(info['original_bytes'], 0)
                        self.assertGreater(info['compressed_bytes'], 0)
                    with TemporaryDirectory() as temp:
                        path = Path(temp) / 'RuntimeDB.dll'
                        path.write_bytes(binary)
                        self.assertEqual(validate_library_packing(path, target,
                                        requested=packed), info)

    def test_packing_mismatch_is_an_error_not_silent_unpacked_output(self):
        for target in ('pe32', 'pe64'):
            raw = self._link(target, False)
            packed = self._link(target, True)
            with self.subTest(target=target, mode='expected-packed'):
                with self.assertRaisesRegex(DBaseLibraryPackingError, 'fehlen'):
                    validate_library_packing(raw, target, requested=True)
            with self.subTest(target=target, mode='expected-unpacked'):
                with self.assertRaisesRegex(DBaseLibraryPackingError, 'deaktiviert'):
                    validate_library_packing(packed, target, requested=False)

    def test_architecture_and_payload_header_are_validated(self):
        binary = self._link('pe32', True)
        with self.assertRaisesRegex(DBaseLibraryPackingError, 'Architektur'):
            validate_library_packing(binary, 'pe64', requested=True)
        pe = pe_dll_payload.parse_pe(binary)
        ztext = next(s for s in pe['secs'] if s['name'] == b'.ztext')
        changed = bytearray(binary)
        changed[ztext['rptr']:ztext['rptr'] + 4] = b'BAD!'
        with self.assertRaisesRegex(DBaseLibraryPackingError, 'Format'):
            validate_library_packing(changed, 'pe32', requested=True)


if __name__ == '__main__':
    unittest.main()
