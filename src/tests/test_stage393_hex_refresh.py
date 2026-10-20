"""Stage 393: Qt-unabhaengige Regressionstests fuer Hex/Build/PETSCII.

Ausfuehren: python -m unittest -v test_stage393_hex_refresh.py
"""
import ast
import json
from pathlib import Path
from typing import Optional
from tempfile import TemporaryDirectory
import unittest

BASE = Path(__file__).resolve().parent
SOURCE = BASE / 'd64_dism.py'
TREE = ast.parse(SOURCE.read_text(encoding='utf-8'))


def find_node(name, node=TREE):
    for descendant in ast.walk(node):
        if isinstance(descendant, (ast.FunctionDef, ast.ClassDef)) and descendant.name == name:
            return descendant
    raise KeyError(name)


def load_functions(*names):
    nodes = [find_node(name) for name in names]
    module = ast.Module(body=nodes, type_ignores=[])
    namespace = {'Dict': dict, 'Optional': Optional, 'Path': Path, 'json': json,
                 '__file__': str(SOURCE)}
    exec(compile(ast.fix_missing_locations(module), str(SOURCE), 'exec'), namespace)
    return namespace


class Stage393PetsciiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = load_functions(
            '_build_c64_petscii_to_c64pro_codepoint',
            '_parse_c64_petscii_map_byte',
            '_parse_c64_petscii_unicode',
            'load_c64_petscii_unicode_map',
        )
        cls.ns['C64_PETSCII_MAP_FILENAME'] = 'C64Pro.petscii.json'
        cls.legacy = cls.ns['_build_c64_petscii_to_c64pro_codepoint']()

    def test_full_json_round_trip_same_as_stage392(self):
        actual = self.ns['load_c64_petscii_unicode_map'](BASE / 'C64Pro.petscii.json')
        self.assertEqual(len(actual), 256)
        self.assertEqual(actual, self.legacy)
        self.assertEqual(actual[0x41], 0x41)
        self.assertEqual(actual[0x5C], 0xA3)
        self.assertEqual(actual[0xC0], actual[0x60])

    def test_custom_json_overrides_one_character(self):
        document = json.loads((BASE / 'C64Pro.petscii.json').read_text('utf-8'))
        document['petscii_to_unicode']['0x41'] = 'U+2605'
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'custom.json'
            path.write_text(json.dumps(document), encoding='utf-8')
            actual = self.ns['load_c64_petscii_unicode_map'](path)
        self.assertEqual(actual[0x41], 0x2605)
        self.assertEqual(actual[0x42], self.legacy[0x42])

    def test_missing_or_partial_json_falls_back(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'wrong.json'
            self.assertEqual(self.ns['load_c64_petscii_unicode_map'](path), self.legacy)
            path.write_text('{"petscii_to_unicode":{"0x41":"U+2605"}}')
            self.assertEqual(self.ns['load_c64_petscii_unicode_map'](path), self.legacy)

    def test_bad_keys_and_invalid_unicode_rejected(self):
        self.assertEqual(self.ns['_parse_c64_petscii_map_byte']('$FF'), 255)
        self.assertEqual(self.ns['_parse_c64_petscii_map_byte']('0x00'), 0)
        self.assertEqual(self.ns['_parse_c64_petscii_unicode']('U+F137'), 0xF137)
        for byte in ('256', '-1', '0x100', 'nope'):
            with self.subTest(byte=byte):
                with self.assertRaises(ValueError):
                    self.ns['_parse_c64_petscii_map_byte'](byte)
        for codepoint in ('U+D800', 'U+110000', 'abc'):
            with self.subTest(codepoint=codepoint):
                with self.assertRaises(ValueError):
                    self.ns['_parse_c64_petscii_unicode'](codepoint)


class _FakeScrollBar:
    def __init__(self): self.value = None
    def setValue(self, value): self.value = value


class _FakeViewport:
    def __init__(self): self.repainted = False
    def update(self): self.repainted = True


class _FakeHex:
    def __init__(self):
        self.buffer = b''
        self.read_only = False
        self.v = _FakeScrollBar()
        self.h = _FakeScrollBar()
        self.vp = _FakeViewport()
    def set_data(self, data, *, modified=False):
        assert not modified
        self.buffer = bytes(data)
    def data(self): return self.buffer
    def set_read_only(self, value): self.read_only = bool(value)
    def verticalScrollBar(self): return self.v
    def horizontalScrollBar(self): return self.h
    def viewport(self): return self.vp
    def setToolTip(self, value): self.tooltip = value


class _FakeTabs:
    def __init__(self): self.current = None
    def indexOf(self, hexedit): return 2
    def setTabVisible(self, index, visible): self.visible = (index, visible)
    def setCurrentIndex(self, index): self.current = index


class _FakeDoc:
    def __init__(self):
        self.hex_editor = _FakeHex()
        self.views = _FakeTabs()
        self._syncing_views = False
        self._hex_build_preview_path = None
        self._hex_build_input_bytes = None
        self.binary_disassembly_mode = False
        self._data_source = 'text'
        self.source_text = b'10 PRINT "HALLO"\n'
    def text_for_saving(self, suffix=None): return self.source_text.decode('utf-8')
    encoding = 'utf-8'


class Stage393HexRefreshTests(unittest.TestCase):
    def test_snapshot_keeps_assembler_focus_and_keeps_source(self):
        func = find_node('show_assembled_hex_bytes')
        namespace = {'Path': Path, 'C64_PETSCII_MAP_FILENAME': 'C64Pro.petscii.json'}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[func], type_ignores=[])),
                     str(SOURCE), 'exec'), namespace)
        doc = _FakeDoc()
        sample = b'\x01\x08\xA9\x01\x60'
        namespace['show_assembled_hex_bytes'](doc, sample, BASE/'test.prg')
        self.assertEqual(doc.hex_editor.buffer, sample)
        self.assertTrue(doc.hex_editor.read_only)
        self.assertIsNone(doc.views.current)  # Stage 394: kein erzwungener Tabwechsel
        self.assertEqual(doc.views.visible, (2, True))
        self.assertFalse(doc._syncing_views)
        self.assertEqual(doc._data_source, 'text')
        self.assertEqual(doc.source_text, b'10 PRINT "HALLO"\n')
        self.assertEqual(doc.hex_editor.v.value, 0)
        self.assertEqual(doc.hex_editor.h.value, 0)

    def test_rebuilt_binary_preview_never_becomes_source(self):
        func = find_node('show_assembled_hex_bytes')
        namespace = {'Path': Path, 'C64_PETSCII_MAP_FILENAME': 'C64Pro.petscii.json'}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[func], type_ignores=[])),
                     str(SOURCE), 'exec'), namespace)
        doc = _FakeDoc()
        doc.binary_disassembly_mode = True
        doc._data_source = 'hex'
        input_image = b'\x01\x08\xa9\x00\x60'
        doc.hex_editor.set_data(input_image)
        namespace['show_assembled_hex_bytes'](doc, b'\x01\x08\xa9\x01\x60', BASE/'output.prg')
        self.assertEqual(doc._hex_build_input_bytes, input_image)
        self.assertEqual(doc.hex_editor.buffer, b'\x01\x08\xa9\x01\x60')
        namespace['show_assembled_hex_bytes'](doc, b'\x01\x08\xa9\x02\x60', BASE/'output.prg')
        self.assertEqual(doc._hex_build_input_bytes, input_image)
        # Ctrl+S for the binary input must still use its original buffer.
        source_data = find_node('data_for_saving')
        extract = {'Optional': Optional}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[source_data], type_ignores=[])),
                     str(SOURCE), 'exec'), extract)
        self.assertEqual(extract['data_for_saving'](doc), input_image)

    def test_readonly_hex_guards_exist(self):
        for name in ('cut_selection', 'paste_bytes', '_replace_byte', '_replace_nibble'):
            method = find_node(name)
            source = ast.get_source_segment(SOURCE.read_text(encoding='utf-8'), method)
            self.assertIn('if self._read_only:', source)

    def test_refresh_reads_final_file_and_not_source(self):
        node = find_node('_refresh_assembled_hex_view')
        class Doc(_FakeDoc):
            def show_assembled_hex_bytes(self, image, path):
                self.image = image
                self.file = path
        namespace = {'DocumentEditor': Doc, 'Path': Path}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                     str(SOURCE), 'exec'), namespace)
        with TemporaryDirectory() as directory:
            path = Path(directory)/'output.prg'
            path.write_bytes(b'\x01\x08\xA9\x01\x60')
            class Window:
                def __init__(self): self.logs = [];self.updated = False
                def log(self, text): self.logs.append(text)
                def _update_editor_status_panels(self): self.updated = True
            window, doc = Window(), Doc()
            namespace['_refresh_assembled_hex_view'](window, doc, path)
            self.assertEqual(doc.image, path.read_bytes())
            self.assertEqual(doc.file, path)
            self.assertTrue(window.updated)
            self.assertTrue(any('HEX REFRESH:' in line for line in window.logs))
            path.unlink()
            namespace['_refresh_assembled_hex_view'](window, doc, path)
            self.assertEqual(doc.image, b'\x01\x08\xA9\x01\x60')

    def test_both_success_paths_integrated(self):
        for method in ('assemble_document', 'assemble_generated_document'):
            src = ast.get_source_segment(SOURCE.read_text(encoding='utf-8'), find_node(method))
            self.assertIn('self._refresh_assembled_hex_view(document, output_path)', src)
        doc = ast.get_source_segment(SOURCE.read_text(encoding='utf-8'), find_node('data_for_saving'))
        self.assertIn('_hex_build_preview_path', doc)
        self.assertIn('text_for_saving', doc)


if __name__ == '__main__': unittest.main()
