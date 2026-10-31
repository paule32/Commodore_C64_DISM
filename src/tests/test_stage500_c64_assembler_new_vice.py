"""Stage 500: neue ungespeicherte Assembler-Datei, Speichern und VICE-Reset.

Qt/VICE-unabhaengige Regressionstests gegen den echten Quellcode (AST-Isolation).
"""
import ast
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

from test_stage394_c64_new_rename import FakeDocument, FakeItem, FakeStatus
from test_stage399_c64_basic_context import Menu, Item

SRC = Path(__file__).with_name('d64_dism.py')
TEXT = SRC.read_text(encoding='utf-8')
TREE = ast.parse(TEXT)


def isolate(name, **extra):
    matches = [n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(matches) == 1, (name, len(matches))
    ns = {'Optional': Optional, 'Path': Path, 'DocumentEditor': FakeDocument,
          'QTreeWidgetItem': FakeItem}
    ns.update(extra)
    exec(compile(ast.fix_missing_locations(ast.Module(body=matches, type_ignores=[])),
                 str(SRC), 'exec'), ns)
    return ns[name]


class Tests(unittest.TestCase):
    def test_c64_assembler_project_target_new_first_and_existing_actions(self):
        owner_calls = []
        root = Item(titles=['Commodore C= 64'])
        root.setData(0, 1305, 'assembler')
        factory = isolate('_show_project_c64_menu',
            Qt=SimpleNamespace(UserRole=1000), QMenu=Menu,
            PROJECT_NODE_C64_TARGET='c64_target',
            PROJECT_NODE_C64_RESOURCE_ROOT='c64_resource_root',
            PROJECT_NODE_C64_RESOURCE_FILE='c64_resource_file',
            PROJECT_NODE_C64_SOURCE_FILE='c64_source_file')
        class Main:
            project_tree = SimpleNamespace(viewport=lambda: SimpleNamespace(mapToGlobal=lambda p:p))
            def _project_item_kind(self, _): return 'c64_target'
            def _new_unsaved_c64_source_document(self, *args, **kwargs):
                owner_calls.append((args, kwargs))
            def add_project_c64_files(self, language): owner_calls.append(('add', language))
        Menu.requested_label = 'Neu: Assembler-Programm'
        factory(Main(), root, (0,0))
        self.assertEqual(Menu.history, [
            'Neu: Assembler-Programm', 'C64-Quellprogramm hinzufügen …', 'Knoten schließen'])
        self.assertEqual(owner_calls, [(('assembler',), {
            'use_template': True, 'under_c64_target': True})])

    def test_new_asm_is_unsaved_and_attached_under_assembler_c64(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = FakeItem(None, ['Commodore C= 64'])
            class Main:
                project_c64_target_nodes={'assembler': root}
                project_root_items={}
                project_tree=SimpleNamespace(setCurrentItem=lambda item:None)
                def _ensure_project_for_new_document(self): pass
                def _project_existing_names(self): return []
                def _project_new_file_directory(self): return Path(tmp)
                def new_document(self, *, text, display_name):
                    obj = FakeDocument(display_name)
                    obj.text = text
                    return obj
                def set_project_modified(self, flag): pass
                def _update_document_tab(self, document): pass
                def statusBar(self): return FakeStatus()
                def show_error(self, *args): raise AssertionError(args)
            create = isolate('_new_unsaved_c64_source_document',
                DocumentEditor=FakeDocument, QTreeWidgetItem=FakeItem,
                Qt=SimpleNamespace(UserRole=1000),
                PROJECT_NODE_C64_SOURCE_FILE='c64_source_file')
            doc = create(Main(), 'assembler', under_c64_target=True)
            self.assertIs(doc._c64_project_tree_item.parent(), root)
            self.assertTrue(doc._is_new_c64_project_file)
            self.assertTrue(doc._c64_project_tree_item.data(0,1307))
            self.assertIsNone(doc.path)
            self.assertEqual(doc.target, 'c64')
            self.assertEqual(Path(doc.custom_display_name).suffix, '.asm')
            self.assertIn('.entry start', doc.text)
            self.assertFalse(list(Path(tmp).glob('*.asm')))

    def test_first_save_presents_asm_filter_and_appends_asm(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]
            class Dialog:
                @staticmethod
                def getSaveFileName(_parent, title, initial, filters):
                    calls.append((title, initial, filters))
                    return str(Path(tmp) / 'MyFirstAssembly'), filters
            choose = isolate('_choose_document_filename', QFileDialog=Dialog)
            class Main:
                current_directory=Path(tmp)
                def _project_new_file_directory(self): return Path(tmp)
                def show_error(self, *args): raise AssertionError(args)
            doc = SimpleNamespace(path=None, display_name='Unbenannt_1.asm',
                binary_disassembly_mode=False, _is_new_c64_project_file=True)
            chosen = choose(Main(), doc)
            self.assertEqual(chosen, Path(tmp) / 'MyFirstAssembly.asm')
            self.assertIn('C64 Assembler-Dateien (*.asm *.s *.a65)', calls[0][2])
            self.assertEqual(Path(calls[0][1]).suffix, '.asm')

    def test_saving_asm_registers_tree_file_and_clears_unsaved_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / 'Assembly.asm'
            leaf = FakeItem(None, ['Unbenannt_1.asm'])
            leaf.setData(0, 1307, True)
            leaf.setData(0, 1303, 'c64_source_file')
            class Document(FakeDocument):
                @property
                def display_name(self): return self.custom_display_name or self.path.name
                def __init__(self):
                    super().__init__('Unbenannt_1.asm')
                    self.binary_disassembly_mode=False
                    self._is_new_c64_project_file=True
                    self._c64_project_tree_item=leaf
                def data_for_saving(self, suffix):
                    assert suffix=='.asm'
                    return b'.org $1000\nstart:\n rts\n'
                def source_language(self): return 'assembler'
                def invalidate_assembly_result(self, reason): pass
                def mark_saved(self): self.saved=True
                def update_syntax_highlighting(self): pass
                is_prolog_document=False
            class Main:
                current_project_path=None
                current_directory=Path(tmp)/'different'
                icon_provider=SimpleNamespace(icon=lambda file:'icon')
                document_tabs=SimpleNamespace(setCurrentWidget=lambda document: None)
                def _choose_document_filename(self, doc): return dst
                def _find_open_document(self, path): return None
                def set_project_modified(self, value): pass
                def _apply_document_theme(self, doc): pass
                def _update_document_tab(self, doc): pass
                def _update_editor_status_panels(self): pass
                def _refresh_favorites_menu(self): pass
                def _remember_recent_file(self, path): pass
                def _sync_document_marker_to_project(self, *args, **kwargs): return False
                def log(self, message): pass
                def statusBar(self): return FakeStatus()
                def show_error(self,*args): raise AssertionError(args)
            save = isolate('_save_document', os=os, tempfile=tempfile,
                Qt=SimpleNamespace(UserRole=1000), QFileInfo=lambda p:p,
                DocumentEditor=Document)
            doc=Document()
            self.assertTrue(save(Main(), doc, save_as=False))
            self.assertEqual(dst.read_bytes(), b'.org $1000\nstart:\n rts\n')
            self.assertEqual(doc.path, dst)
            self.assertEqual(leaf.data(0,1302), str(dst))
            self.assertFalse(leaf.data(0,1307))
            self.assertFalse(doc._is_new_c64_project_file)
            self.assertTrue(doc.saved)

    def test_vice_reset_command_has_correct_binary_protocol(self):
        client_class = next(n for n in TREE.body
            if isinstance(n, ast.ClassDef) and n.name=='ViceBinaryMonitorClient')
        reset_func = next(n for n in client_class.body
            if isinstance(n, ast.FunctionDef) and n.name=='reset_system')
        class FakeClient:
            def __init__(self): self.calls=[]
            def command(self, code, data): self.calls.append((code, data))
        ns={'VICE_BINARY_MONITOR_RESET':0xCC}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[reset_func], type_ignores=[])),
                     str(SRC), 'exec'), ns)
        client=FakeClient()
        ns['reset_system'](client)
        ns['reset_system'](client, power_cycle=True)
        self.assertEqual(client.calls, [(0xCC,b'\x00'),(0xCC,b'\x01')])

    def test_vice_worker_reset_is_distinct_from_resume_and_never_assembles(self):
        calls=[]
        class Document: is_assembler_document=True; build_target='c64'
        class Monitor:
            def __init__(self, *a, **kw): pass
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def reset_system(self): calls.append('reset_system')
            def resume(self): calls.append('resume')
            def write_memory(self, *args): raise AssertionError('Must not upload on reset')
        class ImmediateThread:
            def __init__(self, *, target, name, daemon): self.target=target
            def is_alive(self): return False
            def start(self): self.target()
        class Main:
            _vice_debug_threads=[]
            def __init__(self):
                self.vice_debug_finished=SimpleNamespace(emit=lambda *args:calls.append(args[1:3]))
            def _vice_binary_monitor_probe(self): return True
            def _capture_vice_host_window_size(self): return None
            def _schedule_vice_host_window_size_restore(self, snap): pass
            def statusBar(self): return FakeStatus()
            def log(self, message): pass
            def show_error(self, *args): raise AssertionError(args)
        import hashlib, threading, time, subprocess
        run = isolate('_handle_assembler_vice_debug_request',
            DocumentEditor=Document, ViceBinaryMonitorClient=Monitor,
            ViceBinaryMonitorError=RuntimeError, AssemblerError=ValueError,
            threading=SimpleNamespace(Thread=ImmediateThread),
            hashlib=hashlib, time=time, subprocess=subprocess)
        run(Main(), Document(), 'reset_system')
        self.assertEqual(calls[0:2], ['reset_system','resume'])
        self.assertEqual(calls[2][0], True)
        self.assertIn('zurückgesetzt', calls[2][1])

    def test_editor_context_contains_edit_commands_and_vice_reset(self):
        # Native Qt Standardaktionen kommen weiterhin aus createStandardContextMenu.
        self.assertIn('standard_menu = self.createStandardContextMenu()', TEXT)
        self.assertIn('_translate_source_editor_context_menu(standard_menu)', TEXT)
        for label in ('Ausschneiden', 'Einfügen', 'Kopieren', 'Rückgängig',
                      'Wiederherstellen', 'Löschen', 'Alles markieren'):
            self.assertIn(label, TEXT)
        self.assertIn('"VICE zurücksetzen" if is_asm', TEXT)
        self.assertIn('"reset_system" if is_asm else "reset"', TEXT)
        self.assertIn('"VICE Monitor fortsetzen"', TEXT)
        self.assertIn('client.reset_system()', TEXT)

if __name__=='__main__': unittest.main()
