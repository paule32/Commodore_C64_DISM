"""Stage 680: avoid reusing an old native Qt5 runtime archive after O3 changes."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
PRO = ROOT / 'd64qt5' / 'd64qt5_bridge.pro'
BUILD = ROOT / 'runtime' / 'build.qt5_embedded.win32.sh'


def test_native_archive_depends_on_each_compiled_source():
    pro = PRO.read_text(encoding='utf-8')
    build = BUILD.read_text(encoding='utf-8')
    modules = re.search(r'modules=\(([^)]+)\)', build)
    assert modules is not None
    for module in modules.group(1).split():
        rel = f'../runtime/{module}.cc'
        assert rel in pro, f'{rel} missing from archive dependencies'
        assert (PRO.parent / rel).is_file(), rel
    for rel in ('memory_nt32.asm', 'setjmp32.asm',
                'pascal/inttostr.asm', 'pascal/strtoint.asm',
                'pascal/cookie32.asm'):
        assert f'../runtime/{rel}' in pro
        assert (ROOT / 'runtime' / rel).is_file(), rel
    assert 'qt5_native_runtime.depends = $$QT5_NATIVE_DEPENDS' in pro
    assert 'QT5_NATIVE_DEPENDS = d64qt5_bridge.pro $$QT5_NATIVE_BUILD' in pro
    assert 'PRE_TARGETDEPS += $$QT5_NATIVE_ARCHIVE' in pro


def test_runtime_build_checks_coff_symbol_early():
    build = BUILD.read_text(encoding='utf-8')
    assert 'for tool in g++ nasm ar nm' in build
    assert 'nm -g --defined-only "$out/jitObject.o"' in build
    assert '_jit_default_tobject_vmt_abi$' in build
    assert 'rm -f win32/libd64_qt5_native.a' in build


def test_o3_export_and_implementation_remain_compatible():
    def_file = (ROOT / 'd64qt5' / 'd64qt5_bridge.def').read_text()
    source = (ROOT / 'runtime' / 'jitObject.cc').read_text()
    header = (ROOT / 'runtime' / 'jitObject.h').read_text()
    assert len(re.findall(r'^\s*jit_default_tobject_vmt_abi\s+@2085\s*$',
                          def_file, re.M)) == 1
    assert 'jit_default_tobject_vmt_abi(void) { return 1u; }' in source
    assert 'jit_default_tobject_vmt_abi(void)' in header
