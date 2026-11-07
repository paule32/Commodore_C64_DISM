"""Stage 530: independent PE32/PE64 debug state and nested DWARF group."""
from __future__ import annotations

import ast
import configparser
from pathlib import Path
import re
import tempfile

from debug_options import (
    ARCH_SECTIONS, DebugOptions, read_options, update_project_file,
)

BASE = Path(__file__).parent
SOURCE = (BASE / 'd64_dism.py').read_text(encoding='utf-8')
SOURCE_AST = ast.parse(re.sub(r'(?m)^(\s*)lazy (from|import) ',r'\1\2 ',SOURCE))
PAGE_SOURCE = (BASE/'debug_options.py').read_text('utf-8')


def get_class(name):
    nodes=[node for node in ast.walk(SOURCE_AST)
           if isinstance(node, ast.ClassDef) and node.name == name]
    assert len(nodes)==1, (name,len(nodes))
    return nodes[0]


def get_method(name, cls=None):
    nodes = cls.body if cls is not None else SOURCE_AST.body
    matches=[n for n in nodes if isinstance(n, ast.FunctionDef) and n.name==name]
    assert len(matches)==1, (name,len(matches))
    return matches[0]


def panel_instance():
    panel=get_class('ProjectSettingsPanel')
    methods=[get_method(name,panel) for name in (
        '_debug_page_controls', '_set_debug_page_options',
        '_debug_options_changed','set_debug_options','debug_options', '_target_key')]
    cls=ast.ClassDef(name='DebugPanelUnderTest',bases=[],keywords=[],body=methods,decorator_list=[])
    mod=ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[]))
    state={}
    context={'DebugOptions':DebugOptions,'stage530_default_debug_options':
             lambda:{'pe32':DebugOptions(),'pe64':DebugOptions()},
             'stage527_set_debug_options':lambda opt, target='pe32':state.__setitem__(target,opt)}
    exec(compile(mod,'<stage530 debug panel>','exec'), context)
    class FakeControl:
        def __init__(self): self.blocked=False
        def blockSignals(self,enabled):
            old=self.blocked; self.blocked=enabled; return old
    class FakePage:
        def __init__(self):
            for a in ('enable_debug','ces','dwarf_enabled','dwarf_v2','dwarf_v3'):
                setattr(self,a,FakeControl())
            self.current=DebugOptions()
        def options(self): return self.current
        def set_options(self, options):
            assert all(getattr(self,a).blocked for a in
                       ('enable_debug','ces','dwarf_enabled','dwarf_v2','dwarf_v3'))
            self.current=options
    class Owner:
        def __init__(self): self.changes=[]; self.project_debug_options={}
        def set_project_modified(self,dirty): self.changes.append(dirty)
    obj=object.__new__(context['DebugPanelUnderTest'])
    page32,page64=FakePage(),FakePage()
    obj.windows_pe32_page=type('Win32',(),{'debug_page':page32})()
    obj.windows_pe64_page=type('Win64',(),{'debug_page':page64})()
    obj._debug_pages={'pe32':page32,'pe64':page64}
    obj.owner=Owner()
    return obj,page32,page64,state


def test_syntax_and_navigation():
    # full program parses with legacy Python syntax conversion (PEP 810 lazy).
    assert SOURCE_AST
    panel=get_class('ProjectSettingsPanel')
    ctor=ast.get_source_segment(SOURCE,get_method('__init__',panel))
    assert 'self.tabs.addTab(self.debug_tab' not in ctor
    assert '"pe32": self.windows_pe32_page.debug_page' in ctor
    assert '"pe64": self.windows_pe64_page.debug_page' in ctor
    assert 'for _debug_page in self._debug_pages.values()' in ctor
    win=get_class('WindowsCompilerDirectorySettingsPage')
    init=ast.get_source_segment(SOURCE,get_method('__init__',win))
    assert '("Umgebung", "Compiler", "Assembler", "Linker", "Debug")' in init
    assert 'self.stack.addWidget(self.debug_page)' in init


def test_dwarf_group_is_nested():
    assert "QGroupBox('DWARF: ', debug_group)" in PAGE_SOURCE
    assert 'debug_layout.addWidget(dwarf_group)' in PAGE_SOURCE
    assert '\n        layout.addWidget(dwarf_group)' not in PAGE_SOURCE


def test_independent_pages_no_sync():
    panel,p32,p64,state=panel_instance()
    v32=DebugOptions(True,True,True,2)
    v64=DebugOptions(True,False,False,3)
    panel.set_debug_options({'pe32':v32,'pe64':v64})
    assert p32.options()==v32 and p64.options()==v64
    assert panel.debug_options('pe32')==v32
    assert panel.debug_options('pe64')==v64
    assert state=={'pe32':v32,'pe64':v64}
    assert panel.owner.changes==[]
    changed32=DebugOptions(False,False,True,3)
    p32.current=changed32
    panel._debug_options_changed(p32)
    assert p64.options()==v64 and state['pe64']==v64
    assert state['pe32']==changed32
    assert panel.owner.project_debug_options=={'pe32':changed32,'pe64':v64}
    changed64=DebugOptions(True,True,False,2)
    p64.current=changed64
    panel._debug_options_changed(p64)
    assert p32.options()==changed32 and state['pe32']==changed32
    assert panel.owner.project_debug_options['pe64']==changed64
    assert panel.owner.changes==[True,True]
    assert all(not w.blocked for page in (p32,p64)
               for w in (page.enable_debug,page.ces,page.dwarf_enabled,
                         page.dwarf_v2,page.dwarf_v3))


def test_legacy_import_both():
    cfg=configparser.ConfigParser(interpolation=None)
    cfg.read_string('[Settings.Debug]\nEnableDebug = true\nCheckEarlyStart = true\nDwarfEnabled = true\nDwarfVersion = 2\n')
    old=DebugOptions(True,True,True,2)
    assert DebugOptions.from_parser(cfg,target='pe32')==old
    assert DebugOptions.from_parser(cfg,target='pe64')==old
    cfg[ARCH_SECTIONS['pe64']]={'EnableDebug':'false','DwarfVersion':'3'}
    assert DebugOptions.from_parser(cfg,target='pe32')==old
    assert DebugOptions.from_parser(cfg,target='pe64')==DebugOptions()


def test_project_file_two_sections():
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)/'abc.pro'
        p.write_bytes(b'\xef\xbb\xbf[Project]\r\nName = test\r\n\r\n[Other]\r\nData = safe\r\n')
        v32=DebugOptions(True,True,False,3)
        v64=DebugOptions(False,False,True,2)
        update_project_file(p,v32,target='pe32')
        update_project_file(p,v64,target='pe64')
        assert p.read_bytes().startswith(b'\xef\xbb\xbf')
        assert read_options(p,'pe32')==v32
        assert read_options(p,'pe64')==v64
        assert p.read_bytes().count(b'\r\n')>=6
        update_project_file(p,DebugOptions(False,True,True,2),target='pe32')
        assert read_options(p,'pe64')==v64
        assert 'Data = safe' in p.read_text(encoding='utf-8-sig')
        assert p.read_text(encoding='utf-8-sig').count('[Settings.Windows.32Bit.Debug]')==1


def test_runtime_state_by_architecture():
    # Compile the actual small functions from d64_dism.py, no PyQt needed.
    names=('stage530_default_debug_options','stage527_debug_options','stage527_set_debug_options')
    nodes=[get_method(name) for name in names]
    module=ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))
    ns={'DebugOptions':DebugOptions,'Dict':dict}
    exec(compile(module,'<debug runtime>','exec'),ns)
    ns['PE_STAGE527_DEBUG_OPTIONS']=ns['stage530_default_debug_options']()
    pe32=DebugOptions(True,True,False,3)
    pe64=DebugOptions(False,False,True,2)
    ns['stage527_set_debug_options'](pe32,target='pe32')
    ns['stage527_set_debug_options'](pe64,target='pe64')
    assert ns['stage527_debug_options']()==pe32  # Existing PE32 loader
    assert ns['stage527_debug_options']('pe64')==pe64
    assert ns['stage527_debug_options']('pe32').ces
    assert not ns['stage527_debug_options']('pe64').ces


def test_save_load_paths_present():
    # Verify both profiles are included in the normal .pro load/save path.
    fmt=ast.get_source_segment(SOURCE,get_method('format_project_ini'))
    parse=ast.get_source_segment(SOURCE,get_method('parse_project_ini'))
    collect=ast.get_source_segment(SOURCE,get_method('collect_project_entries',get_class('ExplorerWindow')))
    assert 'for _target, _suffix in (("pe32", "32Bit"), ("pe64", "64Bit")):' in fmt
    assert 'parser[f"Settings.Windows.{_suffix}.Debug"]' in fmt
    assert 'DebugOptions.from_parser(parser, target=_target)' in parse
    assert 'for target in ("pe32", "pe64"):' in collect
    assert '__stage530_debug_{target}__' in collect
    assert 'project_debug_options = {' in SOURCE
    assert 'stage527_set_debug_options(_options, target=_target)' in SOURCE


def test_legacy_api():
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)/'old.pro'
        p.write_text('[Project]\nFormat = dBase2Many Project\n',encoding='utf-8')
        legacy=DebugOptions(True,True,True,2)
        update_project_file(p,legacy)
        assert read_options(p)==legacy
        assert read_options(p,'pe32')==legacy
        assert read_options(p,'pe64')==legacy


if __name__ == '__main__':
    functions=[test_syntax_and_navigation,test_dwarf_group_is_nested,
               test_independent_pages_no_sync,test_legacy_import_both,
               test_project_file_two_sections,test_runtime_state_by_architecture,
               test_save_load_paths_present,test_legacy_api]
    for test in functions:
        test(); print('PASS',test.__name__)
    print(f'Stage 530 tests passed: {len(functions)}')
