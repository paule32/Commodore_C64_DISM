"""Stage 581: end-to-end CES OFF state reaches the PE32 writer, even if global ON.

Uses AST-isolated code: Python <=3.14 cannot import the application's Python
3.15 lazy import syntax, and a GUI is unnecessary for PE32-linker invariants.
"""
from __future__ import annotations

import ast
from configparser import ConfigParser
from pathlib import Path
import re
from typing import Optional

from debug_options import DebugOptions, read_options, update_project_file
from test_stage549 import _args, _ctx

ROOT = Path(__file__).parent
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
TREE = ast.parse(re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', SOURCE))


def top_functions(name):
    return [n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == name]


def install(ns, node):
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(module, '<stage581>', 'exec'), ns)
    return ns[node.name]


def test_explicit_off_flows_across_stage172_209_169_and_loader_rebuild():
    # Make global ON deliberately; the project OFF must take precedence.
    trace = []
    ns = {
        'Optional': Optional,
        'Dict': dict, 'Tuple': tuple, 'Sequence': tuple,
        'PE32_IMAGE_BASE': 0x400000,
        'PE32_PACK_COMPACTOR_DEFAULT': False,
        'PE32_MSZIP_LOADER_IMPORTS': {},
        'stage527_debug_options': lambda target='pe32': DebugOptions(ces=True),
        '_pe_packing_enabled': lambda target: True,
        '_pe_import_packer_settings': lambda target: {'enabled': False},
        '_pe_d64i_bootstrap_imports': lambda exact: {},
        'PE_IMPORT_PACKER_LAST_DECISION': {},
        'PE32_SECTION_RVA': 4096,
        '_build_pe32_image_with_imports_exports_stage167': lambda *a, **k: (b'MZ', b'\x90'),
    }
    def fake_loader_rebuild(image, text, imports, **kwargs):
        trace.append(kwargs['ces_enabled'])
        return (b'MZ_CES_ON' if kwargs['ces_enabled'] else b'MZ_CES_OFF'), text
    ns['_pe32_rebuild_with_mszip_loader'] = fake_loader_rebuild
    writers = top_functions('build_pe32_image_with_imports_exports')
    assert len(writers) == 4
    # True aliases as established in d64_dism.py at Stage 170/171.
    writer169 = install(ns, writers[1])
    ns['_build_pe32_image_with_imports_exports_stage169_layout'] = writer169
    writer209 = install(ns, writers[2])
    ns['_build_pe32_image_with_imports_exports_stage171'] = writer209
    writer172 = install(ns, writers[3])
    for ces in (False, True, False):
        image, _ = writer172(b'\x90', 0, {}, {},
                             ces_enabled=ces, compact_packed_image=False)
        assert image == (b'MZ_CES_ON' if ces else b'MZ_CES_OFF')
    assert trace == [False, True, False]
    # Legacy callers still use the original global default.
    image, _ = writer172(b'\x90', 0, {}, {}, compact_packed_image=False)
    assert image == b'MZ_CES_ON'


def test_real_loader_omits_ces_code_and_strings_when_off():
    ns = _ctx()  # global is CES=True!
    make = ns['_build_pe32_mszip_loader']
    enabled = make(**_args(), ces_enabled=True)
    disabled = make(**_args(), ces_enabled=False)
    assert b'CES: LoadLibraryA failed' in enabled
    assert b'CES: GetProcAddress failed' in enabled
    assert b'CES:' not in disabled
    assert b'MessageBoxA\0' not in disabled
    assert b'user32.dll\0' not in disabled
    assert len(disabled) < len(enabled)


def test_project_options_persist_pe32_off_separately_from_pe64_on(tmp_path):
    file = tmp_path / 'pascal.pro'
    file.write_text('[Project]\nName = Pascal\n[Settings.Debug]\nCheckEarlyStart = true\n')
    update_project_file(file, DebugOptions(ces=False), target='pe32')
    update_project_file(file, DebugOptions(ces=True), target='pe64')
    assert read_options(file, 'pe32').ces is False
    assert read_options(file, 'pe64').ces is True
    assert file.read_text().count('[Settings.Windows.32Bit.Debug]') == 1


def test_pe32_link_contract_carries_explicit_ces_argument():
    functions = {
        'link_coff32_inputs': top_functions('link_coff32_inputs')[-1],
        'link_coff32_objects': top_functions('link_coff32_objects')[-1],
        '_pe32_rebuild_with_mszip_loader': top_functions('_pe32_rebuild_with_mszip_loader')[-1],
    }
    for name, node in functions.items():
        assert 'ces_enabled' in [arg.arg for arg in node.args.kwonlyargs], name
    for name in ('link_coff32_inputs', 'link_coff32_objects'):
        node = functions[name]
        called = ('link_coff32_objects' if name == 'link_coff32_inputs'
                  else 'build_pe32_image_with_imports_exports')
        matches = [n for n in ast.walk(node) if isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Name) and n.func.id == called]
        assert any(any(k.arg == 'ces_enabled' and isinstance(k.value, ast.Name)
                       and k.value.id == 'ces_enabled' for k in n.keywords)
                   for n in matches), name
    writers = top_functions('build_pe32_image_with_imports_exports')
    assert len(writers)==4
    for writer in writers[1:]:
        assert 'ces_enabled' in [a.arg for a in writer.args.kwonlyargs]
    gui = next(node for node in ast.walk(TREE) if isinstance(node, ast.FunctionDef)
               and node.name == 'assemble_generated_document')
    gui_source = ast.get_source_segment(SOURCE, gui)
    assert 'ces_for_build = self._stage549_sync_debug_options_for_build(' in gui_source
    assert '**({"ces_enabled": bool(ces_for_build)} if not is64 else {})' in gui_source


def test_link_inputs_handoff_preserves_off():
    node = top_functions('link_coff32_inputs')[-1]
    ns = {'Sequence':tuple,'Path':Path,'Optional':Optional,'Dict':dict,'Tuple':tuple,
          'PE32Program':object,'PE32AssemblerError':ValueError,
          '_coff_link_input_objects':lambda paths, **kwargs:[b'test'],
          'link_coff32_objects':lambda objects, **kwargs:kwargs['ces_enabled']}
    link = install(ns,node)
    assert link([Path('main.o')],ces_enabled=False) is False
    assert link([Path('main.o')],ces_enabled=True) is True
