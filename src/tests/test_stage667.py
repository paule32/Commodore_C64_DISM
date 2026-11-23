# -*- coding: utf-8 -*-
"""Stage 667: split dBASE Module COFF Assemble / PE Link / Start.

Includes actual PE32/PE32+ internal linker tests on isolated objects, plus
project-UI wiring and missing/multiple main input checks. No Qt installed here.
"""
import ast
from pathlib import Path
import re
import functools
import textwrap
from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from dbase_module_coff import module_namespace, namespace_module_object, module_link_inputs

ROOT = Path(__file__).parent
MAIN = (ROOT / 'd64_dism.py').read_text('utf-8')


@functools.lru_cache(maxsize=1)
def source_tree():
    return ast.parse(re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', MAIN))


def method(name, klass='ExplorerWindow'):
    tree = source_tree()
    cls = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == klass)
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)


def body(name, klass='ExplorerWindow'):
    node = method(name, klass)
    return ast.get_source_segment(MAIN, node)


@pytest.mark.parametrize('target,machine', [('pe32', 0x14c), ('pe64', 0x8664)])
def test_real_coff_link_main_and_namespaced_module(tmp_path, target, machine):
    # Stage 668 reverses Stage 667's entry ownership: the Module is the main.
    from test_stage605_link import _load_pe_linker
    from pascal_console_dependencies import inspect_pe
    linker = _load_pe_linker()
    is64 = target == 'pe64'
    assembler = linker['assemble_pe64_object_source' if is64 else 'assemble_pe32_object_source']
    writer = linker['write_coff64_object' if is64 else 'write_coff32_object']
    actual_link = linker['link_coff64_inputs' if is64 else 'link_coff32_inputs']
    bits = 64 if is64 else 32
    programme_asm = (f'bits {bits}\nsection .text\n'
                     'helper:\n  nop\n  ret\nsection .data\nmydata: db 1\n')
    module_asm = (f'bits {bits}\nsection .text\nentry _start\n'
                  'global _start\n_start:\n  call helper\n  ret\n'
                  'helper:\n  nop\n  ret\nsection .data\nmydata: db 2\n')
    main = namespace_module_object(assembler(programme_asm), tmp_path / 'program.prg')
    mod = assembler(module_asm)
    assert '_start' not in main.symbols and '_start' in mod.symbols
    assert set(main.symbols).isdisjoint(mod.symbols)
    main_path, mod_path = tmp_path/'program.o',tmp_path/'module.o'
    main_path.write_bytes(writer(main))
    mod_path.write_bytes(writer(mod))
    assert module_link_inputs(mod_path, (tmp_path/'program.prg',), lambda _:main_path) == (mod_path,main_path)
    result = actual_link((mod_path,main_path), entry_symbol='_start')
    exe = tmp_path/'linked.exe'; exe.write_bytes(result.executable)
    assert inspect_pe(exe)[0] == (0x8664 if is64 else 0x14c)


def test_exported_module_symbols_keep_public_names(tmp_path):
    @dataclass(frozen=True)
    class Rel:
        offset: int
        symbol: str
        relocation_type: int = 6
        section: str = '.text'
    @dataclass(frozen=True)
    class Obj:
        symbols: dict
        relocations: tuple
        symbol_sections: dict
        entry_symbol: str
        exports: dict
    obj = Obj({'_start':0, 'private':1, 'PublicApi':2},
              (Rel(0,'private'), Rel(4,'PublicApi'), Rel(8,'Outside')),
              {'_start':'.text', 'private':'.data', 'PublicApi':'.text'},
              '_start', {'PublicApi':'PublicApi'})
    modified = namespace_module_object(obj, tmp_path / 'mod.prg')
    ns = module_namespace(tmp_path / 'mod.prg')
    assert modified.entry_symbol == ns + '_start'
    assert modified.symbols['PublicApi'] == 2
    assert modified.symbol_sections[ns + 'private'] == '.data'
    assert [rel.symbol for rel in modified.relocations] == [ns + 'private', 'PublicApi', 'Outside']
    assert modified.exports == obj.exports
    assert obj.symbols == {'_start':0, 'private':1, 'PublicApi':2}


def test_missing_and_ambiguous_main_are_not_implicitly_built(tmp_path):
    module = tmp_path/'module.o'
    main = tmp_path/'main.o'
    with pytest.raises(ValueError, match='noch nicht assembliert'):
        module_link_inputs(module, [tmp_path/'main.prg'], lambda _:main)
    module.write_bytes(b'module')
    assert module_link_inputs(module,[],lambda _:main)==(module,)
    with pytest.raises(ValueError, match='COFF-Objekt des Programms fehlt'):
        module_link_inputs(module, [tmp_path/'main.prg'], lambda _:main)
    main.write_bytes(b'main')
    assert module_link_inputs(module,[tmp_path/'main.prg'],lambda _:main)==(module,main)
    with pytest.raises(ValueError,match='doppelte'):
        module_link_inputs(module,[tmp_path/'main.prg',tmp_path/'main2.prg'],lambda _:main)


def test_buttons_in_both_asm_panels_and_signal_wiring():
    assert 'link_assembled_button = QPushButton("Link", self.assembler_panel)' in MAIN
    assert 'link_generated_button = QPushButton("Link", self.generated_assembly_panel)' in MAIN
    assert MAIN.index('assembler_panel_layout.addWidget(self.assemble_button)') < MAIN.index('assembler_panel_layout.addWidget(self.link_assembled_button)') < MAIN.index('assembler_panel_layout.addWidget(self.start_assembled_button)')
    assert MAIN.index('self.assemble_generated_button\n            )') < MAIN.index('self.link_generated_button\n            )') < MAIN.index('self.start_generated_button\n            )')
    assert 'document.link_generated_requested.connect(\n                self.link_project_dbase_module_document' in MAIN
    assert 'self.start_generated_button.setVisible(not (active or object_only) or executable_ready)' in MAIN
    assert 'self.link_generated_button.setEnabled(coff_ready)' in MAIN


def test_module_selection_checks_tree_role_and_document_path():
    source = textwrap.dedent(body('_is_selected_dbase_module_document'))
    ns = {
        'DocumentEditor': type('DocumentEditor', (), {}),
        'PROJECT_NODE_DBASE_FILE': 'file',
        'Qt': SimpleNamespace(UserRole=1000),
        'Path': Path,
    }
    exec(source, ns)
    fn = ns['_is_selected_dbase_module_document']
    class Doc(ns['DocumentEditor']):
        is_dbase_document = True
        build_target = 'pe32'
        path = Path('/project/module.prg')
        _dbase_project_tree_item = None
    class Leaf:
        def __init__(self, role, path):
            self.role, self.path = role, path
        def data(self, column, role):
            if role == 1306: return self.role
            if role == 1302: return self.path
            return None
    owner = SimpleNamespace(project_tree=SimpleNamespace(currentItem=lambda: Leaf('modules', '/project/module.prg')),
                            _project_item_kind=lambda item: 'file')
    assert fn(owner, Doc()) is True
    owner.project_tree.currentItem = lambda: Leaf('programs', '/project/module.prg')
    assert fn(owner, Doc()) is False
    owner.project_tree.currentItem = lambda: Leaf('modules', '/project/other.prg')
    assert fn(owner, Doc()) is False
    owner.project_tree.currentItem = lambda: Leaf('modules', '/project/module.prg')
    d = Doc();d.build_target = 'linux64'
    assert fn(owner, d) is False


def test_assemble_has_no_link_and_link_requires_valid_coff():
    assembly = body('assemble_project_dbase_module_object')
    link = body('link_project_dbase_module_document')
    assert 'assembler(' in assembly
    assert 'namespace_module_object(' not in assembly
    assert 'writer(compiled)' in assembly
    assert 'link_coff32_inputs' not in assembly
    assert 'link_coff64_inputs' not in assembly
    assert 'module_link_inputs(' in link
    assert 'linker(' in link
    assert 'entry_symbol="__d64_dll_entry" if is_dll else "_start"' in link
    assert 'document._dbase_module_link_digest = document.generated_assembly_digest()' in link
    assert 'document.refresh_project_module_link_buttons()' in link
    assert '_coff_target_header_matches' in link


def test_other_build_types_keep_existing_link_pipeline():
    fn = body('assemble_generated_document')
    assert 'if self._is_selected_dbase_module_document(document):' in fn
    assert 'return self.assemble_project_dbase_module_object(document)' in fn
    assert 'object_writer(' in fn and 'linker(' in fn
    f2 = body('build_and_run_source_document')
    assert 'if self._is_selected_dbase_module_document(document):' in f2
    assert 'return self.assemble_project_dbase_module_object(document)' in f2
    assert 'return self._launch_assembled_document(document)' in f2
    asm = body('build_and_run_generated_assembly_document')
    assert 'if self._is_selected_dbase_module_document(document):' in asm
    assert 'return self.assemble_project_dbase_module_object(document)' in asm


def test_start_visibility_tracks_selected_link_and_file_staleness(tmp_path):
    script = textwrap.dedent(body('refresh_project_module_link_buttons','DocumentEditor'))
    ns = {'Path':Path}
    exec(script,ns)
    fn=ns['refresh_project_module_link_buttons']
    class Button:
        def __init__(self): self.visible=None;self.enabled=False
        def setVisible(self,v):self.visible=v
        def setEnabled(self,v):self.enabled=v
        def setText(self,v):pass
        def setToolTip(self,v):pass
    obj=SimpleNamespace(
        _dbase_module_selected=True,_dbase_program_selected=False,is_dbase_document=True,build_target='pe32',
        _dbase_module_coff_digest='digest', _dbase_module_coff_target='pe32',
        _dbase_module_link_digest='', _dbase_module_link_target='',
        _dbase_module_coff_path=None,_dbase_module_link_path=None,
        generated_assembly_digest=lambda: 'digest',
        link_assembled_button=Button(),link_generated_button=Button(),
        start_generated_button=Button(),start_assembled_button=Button(),
        assemble_generated_button=Button(),is_assembler_document=False,
    )
    fn(obj)
    assert obj.link_generated_button.visible is True
    assert obj.link_generated_button.enabled is False
    assert obj.start_generated_button.visible is False
    coff=tmp_path/'module.o';coff.write_bytes(b'bytes')
    obj._dbase_module_coff_path=coff
    fn(obj)
    assert obj.link_generated_button.enabled is True
    exe=tmp_path/'App.exe';exe.write_bytes(b'exe')
    obj._dbase_module_link_path=exe
    obj._dbase_module_link_digest='digest'
    obj._dbase_module_link_target='pe32'
    obj._dbase_module_link_inputs=((str(coff),coff.stat().st_mtime_ns,coff.stat().st_size),)
    fn(obj)
    assert obj.start_generated_button.visible is True
    assert obj.start_generated_button.enabled is True
    coff.write_bytes(b'different contents')
    fn(obj)
    assert obj.start_generated_button.visible is False
    assert obj.start_generated_button.enabled is False

@pytest.mark.parametrize('target,machine', [('pe32', 0x14c), ('pe64', 0x8664)])
def test_real_dbase_compiler_program_and_module_link(tmp_path, target, machine):
    from d64dbase import compile_dbase_to_assembly
    from dbase_module_coff import strip_program_entry_assembly
    from test_stage605_link import _load_pe_linker
    from pascal_console_dependencies import inspect_pe
    linker = _load_pe_linker()
    assembler = linker['assemble_pe64_object_source' if target == 'pe64' else 'assemble_pe32_object_source']
    writer = linker['write_coff64_object' if target == 'pe64' else 'write_coff32_object']
    link = linker['link_coff64_inputs' if target == 'pe64' else 'link_coff32_inputs']
    main_path = tmp_path/'Programme.prg'
    module_path = tmp_path/'Module.prg'
    main_path.write_text('? "Object"\n',encoding='utf-8')
    module_path.write_text('? "Executable"\n',encoding='utf-8')
    main_asm = strip_program_entry_assembly(compile_dbase_to_assembly(
        main_path.read_text(), filename=str(main_path),target=target).assembly)
    module_asm = compile_dbase_to_assembly(
        module_path.read_text(),filename=str(module_path),target=target).assembly
    main = namespace_module_object(assembler(main_asm),main_path)
    mod = assembler(module_asm)
    assert '_start' not in main.symbols and '_start' in mod.symbols
    main_o,mod_o=tmp_path/'Programme.o',tmp_path/'Module.o'
    main_o.write_bytes(writer(main));mod_o.write_bytes(writer(mod))
    inp=module_link_inputs(mod_o,(main_path,),lambda _:main_o)
    exe=tmp_path/'App.exe';exe.write_bytes(link(inp,entry_symbol='_start',gui=True).executable)
    assert inspect_pe(exe)[0]==machine


def test_compile_invalidates_start_and_refreshes_after_asm_replacement():
    fn = body('_finish_compile_stage')
    assert 'document._dbase_module_coff_digest = ""' in fn
    assert 'document._dbase_module_link_digest = ""' in fn
    assert 'document.refresh_project_module_link_buttons()' in fn
    assert fn.index('document._dbase_module_link_digest = ""') < fn.index('document.refresh_project_module_link_buttons()')


def test_start_is_unsafe_until_module_link_completed():
    start_asm = body('start_generated_assembly_document')
    assert 'if self._is_selected_dbase_module_document(document):' in start_asm
    assert 'if not document.start_generated_button.isEnabled():' in start_asm
    assert 'return self._launch_assembled_document(document)' in start_asm
    start_source = body('start_assembled_document')
    assert 'if self._is_selected_dbase_module_document(document):' in start_source
    assert 'return self.start_generated_assembly_document(document)' in start_source

@pytest.mark.parametrize('target,machine', [('pe32', 0x14c), ('pe64', 0x8664)])
def test_actual_gui_module_assemble_method_produces_coff_only(tmp_path, target, machine):
    """Execute the real GUI method with native compiler/assembler dependencies."""
    from d64dbase import compile_dbase_to_assembly
    from test_stage605_link import _load_pe_linker
    from pascal_console_dependencies import inspect_pe
    import struct
    functions = _load_pe_linker()
    main_src = tmp_path / 'Unit.prg'
    main_src.write_text('? "Module test"\n', encoding='utf-8')
    asm = compile_dbase_to_assembly(main_src.read_text(encoding='utf-8'),
                                    filename=str(main_src), target=target).assembly
    env = dict(Path=Path, DocumentEditor=object,
               assemble_pe32_object_source=functions['assemble_pe32_object_source'],
               assemble_pe64_object_source=functions['assemble_pe64_object_source'],
               write_coff32_object=functions['write_coff32_object'],
               write_coff64_object=functions['write_coff64_object'],
               PE32AssemblerError=functions['PE32AssemblerError'],
               PE64AssemblerError=functions['PE64AssemblerError'])
    exec(textwrap.dedent(body('assemble_project_dbase_module_object')), env)
    method = env['assemble_project_dbase_module_object']
    doc = SimpleNamespace(
        path=main_src, build_target=target,
        _dbase_module_selected=False, _dbase_module_coff_digest='stale',
        _dbase_module_coff_path=None, _dbase_module_link_digest='old',
        _dbase_module_link_path=None, generated_assembly_editor=SimpleNamespace(toPlainText=lambda: asm),
        generated_assembly_path=tmp_path / 'Unit.asm',
        generated_assembly_digest=lambda: 'digest',
        refresh_project_module_link_buttons=lambda: None,
        show_generated_assembly_error=lambda *args, **kw: pytest.fail(str(args)),
        generated_assembly_status_label=SimpleNamespace(setText=lambda s: None),
        hints_editor=SimpleNamespace(setPlainText=lambda s: None),
    )
    logger=[]
    obj_path=tmp_path/'Unit.o'
    owner=SimpleNamespace(
        _is_selected_dbase_module_document=lambda doc: True,
        _project_generated_object_path=lambda *args, **kw: obj_path,
        _document_windows_pascal_unit_output_path=lambda doc: tmp_path,
        _project_windows_asm_include_paths=lambda *args: [],
        _dbase_assembly_output_path=lambda doc: doc.generated_assembly_path,
        _write_assembled_program=lambda path,data: Path(path).write_bytes(data),
        show_error=lambda title,error: pytest.fail(f'{title}: {error}'),
        log=lambda message: logger.append(message),
        statusBar=lambda: SimpleNamespace(showMessage=lambda s: None),
        current_directory=tmp_path,
        populate_file_list=lambda: None,
    )
    assert method(owner, doc) is True
    assert obj_path.read_bytes()[:2] == struct.pack('<H', machine)
    assert doc._dbase_module_coff_path == obj_path
    assert doc._dbase_module_coff_digest == 'digest'
    assert doc._dbase_module_link_path is None
    assert 'DBASE MODULE ASSEMBLE' in logger[-1]

def test_actual_gui_link_method_requires_profile_and_module_entry():
    source = body('link_project_dbase_module_document')
    assert 'scope_language != "dbase"' in source
    assert 'module_link_inputs(' in source
    assert 'expected_entry = "__d64_dll_entry" if scope_kind == "library" else "_start"' in source
    assert 'self._project_named_effective_assignment(leaf)' in source
    assert 'program_sources[0]' not in source
