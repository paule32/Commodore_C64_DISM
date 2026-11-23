# -*- coding: utf-8 -*-
"""Stage 669: no accidental PE link for dBASE Programme + *.pro target persistence."""
from pathlib import Path
import configparser
from types import SimpleNamespace
from textwrap import dedent
from typing import Sequence
import struct

import pytest

from project_editor_targets import (
    ENTRY_KEY, SECTION, write_editor_targets, read_editor_targets,
)
from test_stage667 import body
from test_stage605_link import _load_pe_linker, OBJECTS
from d64dbase import compile_dbase_to_assembly
from dbase_module_coff import strip_dbase_library_entry_assembly, strip_program_entry_assembly, namespace_module_object


def test_editor_target_roundtrip_and_invalid_settings(tmp_path):
    project = tmp_path / 'Projekt.pro'
    source = tmp_path / 'Module' / 'App001.prg'
    source.parent.mkdir()
    source.write_text('')
    p = configparser.ConfigParser(interpolation=None)
    p.optionxform = str
    def save_path(path, project_path):
        return str(Path(path).relative_to(project_path.parent))
    def load_path(path, project_path):
        return str((project_path.parent / path).resolve())
    write_editor_targets(p, [
        {'path': str(source), 'target': 'pe32'},
        {'path': str(tmp_path/'other.prg'), 'target': 'pe64'},
        {'path': 'skipped', 'target': 'invalid'},
    ], project, save_path)
    assert SECTION in p
    assert 'Module/App001.prg' in p[SECTION]['Item0001']
    p[SECTION]['Item0003'] = 'broken json'
    recovered = read_editor_targets(p, project, load_path)
    assert recovered == [
        {'path': str(source.resolve()), 'target': 'pe32'},
        {'path': str((tmp_path/'other.prg').resolve()), 'target': 'pe64'},
    ]
    del p[SECTION]
    assert read_editor_targets(p, project, load_path) == []


def test_gui_role_identification_survives_project_tree_selection_change(tmp_path):
    class DocumentEditor:
        def __init__(self, path, target='pe32'):
            self.is_dbase_document = True
            self.path = path
            self.build_target = target

    class Item:
        def __init__(self, kind, path=None):
            self.kind = kind
            self.path = path
            self.children = []
        def childCount(self): return len(self.children)
        def child(self, i): return self.children[i]
        def data(self, _col, key):
            return self.path if key == 302 else None

    class Host:
        pass
    scope = {'Path': Path, 'DocumentEditor': DocumentEditor,
             'Qt': SimpleNamespace(UserRole=0), 'PROJECT_NODE_DBASE_FILE': 'file'}
    for name in ('_dbase_project_document_role', '_is_selected_dbase_program_document',
                 '_is_selected_dbase_module_document'):
        exec(dedent(body(name)), scope)
        setattr(Host, name, scope[name])
    host = Host()
    host.project_dbase_group_nodes = {'programs':Item('group'), 'modules':Item('group')}
    src = tmp_path / 'Program.prg'
    mod = tmp_path / 'App001.prg'
    host.project_dbase_group_nodes['programs'].children.append(Item('file',str(src)))
    host.project_dbase_group_nodes['modules'].children.append(Item('file',str(mod)))
    host._project_item_kind = lambda item: item.kind
    host.project_tree = SimpleNamespace(currentItem=lambda:Item('other'))
    assert host._is_selected_dbase_program_document(DocumentEditor(src))
    assert not host._is_selected_dbase_module_document(DocumentEditor(src))
    assert host._is_selected_dbase_module_document(DocumentEditor(mod))
    assert host._dbase_project_document_role(DocumentEditor(mod)) == 'modules'
    assert not host._is_selected_dbase_program_document(DocumentEditor(src,'c64'))


def test_assembler_dispatch_does_not_link_when_tree_selection_changed():
    class DocumentEditor:
        pass
    env = {'DocumentEditor':DocumentEditor, 'Sequence':Sequence, 'Path':Path}
    exec(dedent(body('assemble_generated_document')),env)
    handler=env['assemble_generated_document']
    doc=DocumentEditor()
    actions=[]
    owner=SimpleNamespace(
        _is_selected_dbase_module_document=lambda _: False,
        _is_selected_dbase_program_document=lambda _: True,
        assemble_project_dbase_program_object=lambda _: actions.append('coff') or True,
    )
    assert handler(owner,doc) is True
    assert actions == ['coff']


@pytest.mark.parametrize('target,machine', [('pe32',0x14c),('pe64',0x8664)])
@pytest.mark.parametrize('source_kind', ['program', 'library'])
def test_class_runtime_import_remains_external_in_coff_object(tmp_path,target,machine,source_kind):
    """A COFF object can contain an import reference before EXE/DLL linking."""
    native=_load_pe_linker()
    asm=native['assemble_pe32_object_source' if target=='pe32' else 'assemble_pe64_object_source']
    writer=native['write_coff32_object' if target=='pe32' else 'write_coff64_object']
    original=compile_dbase_to_assembly(OBJECTS.read_text('utf-8'),
                                       filename=str(OBJECTS),
                                       target=target,source_kind=source_kind).assembly
    assert 'call __dbase_obj_jit_object_instance_new' in original
    transformed=(strip_program_entry_assembly(original) if source_kind == 'program'
                 else strip_dbase_library_entry_assembly(original))
    assert 'import __dbase_obj_jit_object_instance_new' in transformed
    obj=namespace_module_object(asm(transformed),tmp_path/'helper.prg',hide_tobject_exports=True)
    assert '__dbase_obj_jit_object_instance_new' in obj.imports
    binary=writer(obj)
    assert struct.unpack('<H',binary[:2])[0]==machine
    # The object file is intentionally NOT passed to link_coff*_inputs here.


def test_main_file_wires_project_target_to_save_and_restore():
    source=Path(__file__).with_name('d64_dism.py').read_text('utf-8')
    assert 'write_editor_targets(parser, entries.get(ENTRY_KEY' in source
    assert 'entries[ENTRY_KEY] = read_editor_targets(' in source
    assert 'document.generated_build_target_combo.currentTextChanged.connect(' in source
    assert 'self._project_editor_target_changed(value)' in source
    assert '_project_editor_compiler_targets = {' in source
    assert 'if saved_target:' in source and 'document.set_build_target(saved_target)' in source
