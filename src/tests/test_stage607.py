# -*- coding: utf-8 -*-
"""Stage 607: D64Z packing follows the project PE setting for dBASE runtime DLLs.

The PE payload tests use a zlib replacement ONLY for structural checks on a
non-Windows host. Windows builds continue to use Cabinet MSZIP algorithm 2.
"""
import ast
import re
import struct
import unittest
import zlib
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from d64dbase import pe_dll_payload
from d64dbase.console_runtime import DLL_NAME, EXPORTS, build_dll, deploy_runtime
from pascal_console_dependencies import inspect_pe
from test_stage605_link import _load_pe_linker

ROOT = Path(__file__).resolve().parent


def _parse_main():
    source = (ROOT / 'd64_dism.py').read_text('utf-8')
    return ast.parse(re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', source))


class Stage607Flags(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = _parse_main()

    @classmethod
    def _method(cls, name):
        for node in ast.walk(cls.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                return node
        raise AssertionError(name)

    def test_dll_pack_policy_tracks_both_target_specific_options(self):
        fn = self._method('_dbase_console_runtime_pack_enabled')
        import types
        namespace = {'PE_PACKING_DEFAULT': False}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), '<policy>', 'exec'), namespace)
        func = namespace[fn.name]
        state = types.SimpleNamespace(
            _project_windows_target_key=lambda t: str(t).lower(),
            project_windows_pe_packing_enabled={'pe32': True, 'pe64': False},
            project_windows_console_dll_pack={'pe32': False, 'pe64': True},
        )
        self.assertTrue(func(state, 'pe32'))   # global D64Z/PE packing alone
        self.assertTrue(func(state, 'pe64'))   # explicit runtime DLL packing alone
        state.project_windows_console_dll_pack['pe64'] = False
        self.assertFalse(func(state, 'pe64'))
        state.project_windows_pe_packing_enabled['pe32'] = False
        self.assertFalse(func(state, 'pe32'))
        state.project_windows_pe_packing_enabled['pe64'] = True
        self.assertTrue(func(state, 'pe64'))

    def test_both_manual_and_automatic_paths_use_same_policy(self):
        for method in ('create_dbase_runtime_dll', '_prepare_dbase_console_runtime'):
            node = self._method(method)
            calls = [call for call in ast.walk(node) if isinstance(call, ast.Call)
                     and isinstance(call.func, ast.Attribute)
                     and call.func.attr == '_dbase_console_runtime_pack_enabled']
            self.assertTrue(calls, method)
        source = (ROOT / 'd64_dism.py').read_text('utf-8')
        self.assertIn('D64Z/MSZIP-Status der Konsolen-DLL stimmt nicht', source)
        self.assertIn('Bei aktivem Linker-Packing wird die DLL automatisch gepackt.', source)


class Stage607RuntimePackaging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.link = _load_pe_linker()

    @classmethod
    def _kwargs(cls):
        return {
            'assemble32': cls.link['assemble_pe32_object_source'],
            'coff32': cls.link['write_coff32_object'],
            'link32': cls.link['link_coff32_objects'],
            'assemble64': cls.link['assemble_pe64_object_source'],
            'coff64': cls.link['write_coff64_object'],
            'link64': cls.link['link_coff64_objects'],
        }

    @staticmethod
    def _exports(path, machine):
        actual_machine, imports, exports = inspect_pe(path)
        if actual_machine != machine:
            raise ValueError('Architektur stimmt nicht überein')
        return exports

    def test_packed_pe32_pe64_dlls_keep_iat_exports_and_dll_entry(self):
        for target, machine in (('pe32', 0x14c), ('pe64', 0x8664)):
            with self.subTest(target=target), TemporaryDirectory() as temp:
                raw = Path(temp) / 'raw' / DLL_NAME
                packed = Path(temp) / 'packed' / DLL_NAME
                build_dll(target, raw, **self._kwargs())
                # zlib here is an intentional TEST stub: not valid Cabinet/MSZIP.
                build_dll(target, packed, **self._kwargs(), pack_dll=True,
                          compressor=lambda data: zlib.compress(data, 9))
                original = pe_dll_payload.parse_pe(raw.read_bytes())
                result = pe_dll_payload.parse_pe(packed.read_bytes())
                self.assertEqual(machine, result['machine'])
                self.assertNotEqual(original['entry'], result['entry'])
                self.assertFalse(pe_dll_payload.is_payload_packed(raw))
                self.assertTrue(pe_dll_payload.is_payload_packed(packed))
                stats = pe_dll_payload.packed_payload_info(packed)
                self.assertGreater(stats['original_bytes'], stats['compressed_bytes'])
                self.assertIsNone(pe_dll_payload.packed_payload_info(raw))
                self.assertIn(b'.loader', [s['name'] for s in result['secs']])
                self.assertIn(b'.ztext', [s['name'] for s in result['secs']])
                # The packed build adds Cabinet/VirtualProtect imports to the
                # *input* before linking; its .edata RVA can therefore differ
                # from a separately linked, unpacked build. Export names and
                # architecture must remain unchanged (verified below).
                self.assertTrue(set(EXPORTS).issubset(self._exports(packed, machine)))
                self.assertTrue(set(EXPORTS).issubset(self._exports(raw, machine)))
                _, imports, _ = inspect_pe(packed)
                self.assertIn('cabinet.dll', {s.lower() for s in imports})

    def test_pack_marker_alone_is_not_a_valid_payload(self):
        with TemporaryDirectory() as temp:
            packed = Path(temp) / DLL_NAME
            build_dll('pe32', packed, **self._kwargs(), pack_dll=True,
                      compressor=lambda raw: zlib.compress(raw, 9))
            self.assertTrue(pe_dll_payload.is_payload_packed(packed))
            pe = pe_dll_payload.parse_pe(packed.read_bytes())
            section = next(s for s in pe['secs'] if s['name'] == b'.ztext')
            data = bytearray(packed.read_bytes())
            data[section['rptr']:section['rptr']+4] = b'FAKE'
            packed.write_bytes(data)
            self.assertFalse(pe_dll_payload.is_payload_packed(packed))
            self.assertIsNone(pe_dll_payload.packed_payload_info(packed))

    def test_deployment_rebuilds_when_switching_packing_off(self):
        with TemporaryDirectory() as t:
            dest = Path(t) / 'test.exe'
            dest.write_bytes(b'MZ')
            fake_base = Path(t) / 'unshipped-source'
            fake_base.mkdir()
            for target in ('pe32', 'pe64'):
                # The installed DLL must follow project mode changes in both
                # directions, never silently retain a packed older image.
                with self.subTest(target=target), patch.object(
                        pe_dll_payload, 'mszip_compress',
                        side_effect=lambda raw: zlib.compress(raw, 9)):
                    d = deploy_runtime(dest, target, get_exports=self._exports,
                                       package_root=fake_base, pack_dll=True,
                                       **self._kwargs())
                    self.assertTrue(pe_dll_payload.is_payload_packed(d))
                    after = deploy_runtime(dest, target, get_exports=self._exports,
                                           package_root=fake_base, pack_dll=False,
                                           **self._kwargs())
                    self.assertEqual(d, after)
                    self.assertFalse(pe_dll_payload.is_payload_packed(after))
                    self.assertTrue(set(EXPORTS).issubset(self._exports(after, 0x14c if target=='pe32' else 0x8664)))


if __name__ == '__main__':
    unittest.main()
