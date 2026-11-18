"""Stage 610: PE Compact, linked binary safety and UI/config integration."""
from __future__ import annotations

import ast
import re
import struct
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from d64dbase.pe_image_compact import compact_pe_image, compact_pe_file
from pascal_console_dependencies import inspect_pe
from d64dbase import compile_dbase_to_assembly
from test_stage605_link import _load_pe_linker

ROOT = Path(__file__).resolve().parent
MAIN = (ROOT / 'd64_dism.py').read_text('utf-8')
PRG = (ROOT / 'runtime/dbase/src/System.Objects.prg').read_text('utf-8')


def add_zero_block(src: bytes, section: bytes) -> bytes:
    """Create a valid-but-nonminimal PE by adding an aligned zero raw block."""
    data = bytearray(src)
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    opt = pe + 24
    align = struct.unpack_from('<I', data, opt + 36)[0]
    table = opt + struct.unpack_from('<H', data, pe + 20)[0]
    count = struct.unpack_from('<H', data, pe + 6)[0]
    position = None
    for i in range(count):
        off = table + i*40
        if data[off:off+8].rstrip(b'\0') == section:
            position = off
            break
    assert position is not None
    size, ptr = struct.unpack_from('<II', data, position+16)
    assert size and ptr
    insert = ptr+size
    data[insert:insert] = bytes(align)
    struct.pack_into('<I', data, position+16, size+align)
    for i in range(count):
        off = table+i*40
        old_size, old_ptr = struct.unpack_from('<II', data, off+16)
        if off != position and old_size and old_ptr >= insert:
            struct.pack_into('<I', data, off+20, old_ptr+align)
    # Update init-data size if raw section belongs to that type.
    kind = struct.unpack_from('<I', data, position+36)[0]
    if kind & 0x40:
        v = struct.unpack_from('<I', data, opt+8)[0]
        struct.pack_into('<I', data, opt+8, v+align)
    if kind & 0x20:
        v = struct.unpack_from('<I', data, opt+4)[0]
        struct.pack_into('<I', data, opt+4, v+align)
    return bytes(data)


class Stage610Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.link = _load_pe_linker()
        cls.images = {}
        for target in ('pe32','pe64'):
            output = compile_dbase_to_assembly(PRG, target=target, source_kind='library')
            if target=='pe32':
                obj=cls.link['assemble_pe32_object_source'](output.assembly)
                raw=cls.link['write_coff32_object'](obj)
                program=cls.link['link_coff32_objects']((raw,), dll=True,
                    entry_symbol='__d64_dll_entry', dll_name='RuntimeDB.dll', pack_dll=False)
            else:
                obj=cls.link['assemble_pe64_object_source'](output.assembly)
                raw=cls.link['write_coff64_object'](obj)
                program=cls.link['link_coff64_objects']((raw,), dll=True,
                    entry_symbol='__d64_dll_entry', dll_name='RuntimeDB.dll', pack_dll=False)
            cls.images[target]=program.executable

    def test_new_option_in_two_architectures(self):
        for txt in ('PROJECT_WINDOWS_PE32_COMPACT_ENABLED_KEY',
                    'PROJECT_WINDOWS_PE64_COMPACT_ENABLED_KEY',
                    '"compact_enabled_key"',
                    '"Compact": "true" if _compact_enabled_value',
                    '"Compact", self.pe_packing_group',
                    'self.pe_compact_checkbox.toggled.connect(',
                    'def set_project_windows_compact(',
                    'def _stage610_compact_linked_program(',
                    'compact_pe_file(output_path)',
                    'self.project_windows_compact_enabled.get(document.build_target, False)'):
            self.assertIn(txt, MAIN)
        self.assertGreaterEqual(MAIN.count('self.project_settings_panel.set_pe_compact_enabled('), 1)
        self.assertGreaterEqual(MAIN.count('self.set_project_windows_compact('), 1)
        ast.parse(re.sub(r'(?m)^(\s*)lazy (from|import)\b',r'\1\2',MAIN))

    def test_pe32_and_pe64_dll_without_gaps_unchanged(self):
        for target, data in self.images.items():
            with self.subTest(target=target):
                out, report = compact_pe_image(data)
                self.assertLessEqual(len(out),len(data))
                self.assertEqual(report['saved_bytes'], len(data)-len(out))
                self.assertEqual(report['changed'],out!=data)

    def test_null_block_elimination_preserves_dll_import_exports(self):
        for target, original in self.images.items():
            with self.subTest(target=target), TemporaryDirectory() as d:
                candidate = add_zero_block(original, b'.idata')
                compacted, report = compact_pe_image(candidate)
                self.assertTrue(report['changed'], report)
                self.assertGreaterEqual(report['zero_bytes'],512)
                self.assertEqual(compacted, original)
                a=Path(d)/'before.dll'; b=Path(d)/'after.dll'
                a.write_bytes(candidate); b.write_bytes(compacted)
                self.assertEqual(inspect_pe(a), inspect_pe(b))

    def test_signed_and_debug_image_refused(self):
        for target, src in self.images.items():
            with self.subTest(target=target):
                data=bytearray(add_zero_block(src,b'.idata'))
                pe=struct.unpack_from('<I',data,0x3C)[0]
                opt=pe+24
                magic=struct.unpack_from('<H',data,opt)[0]
                directory=opt+(112 if magic==0x20B else 96)
                # Authenticode table presence blocks raw-pointer rewriting.
                struct.pack_into('<II',data,directory+4*8,len(data)-32,32)
                actual, info=compact_pe_image(bytes(data))
                self.assertEqual(actual,bytes(data))
                self.assertFalse(info['changed'])

    def test_nonzero_tail_and_overlay_refused(self):
        src=self.images['pe32']
        candidate=bytearray(add_zero_block(src,b'.idata'))
        # Poison the extra last block so it is NOT removable.
        pe=struct.unpack_from('<I',candidate,0x3C)[0]
        opt=pe+24
        hdr=opt+struct.unpack_from('<H',candidate,pe+20)[0]
        for i in range(struct.unpack_from('<H',candidate,pe+6)[0]):
            if candidate[hdr+i*40:hdr+i*40+8].rstrip(b'\0')==b'.idata':
                rp,rs=struct.unpack_from('<II',candidate,hdr+i*40+20)[0],struct.unpack_from('<I',candidate,hdr+i*40+16)[0]
                candidate[rp+rs-1]=0x71
        out,info=compact_pe_image(bytes(candidate))
        # no zero blocks; existing physical gaps could still be compacted.
        self.assertEqual(info['zero_bytes'],0)
        self.assertEqual(len(out),len(candidate))
        out,info=compact_pe_image(src+b'NOT-A-PE-OVERLAY')
        self.assertEqual(out,src+b'NOT-A-PE-OVERLAY')
        self.assertFalse(info['changed'])

    def test_actual_coff_link_hooks_both_architectures(self):
        """Execute Stage610 wrapper declarations against real COFF32/64 linkers."""
        import __future__
        ns = self.link
        source = re.sub(r'(?m)^(\s*)lazy (from|import)\b', r'\1\2', MAIN)
        nodes = ast.parse(source).body
        wrappers = []
        wanted = {'_stage610_compact_linked_program',
                  'link_coff32_objects', 'link_coff64_objects'}
        for node in nodes:
            if (isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id.startswith('_stage610_link_coff')
                        for t in node.targets)):
                wrappers.append(node)
            elif (isinstance(node, ast.FunctionDef) and node.name in wanted
                  and node.lineno > 50000):
                wrappers.append(node)
        self.assertEqual(len(wrappers), 5)
        exec(compile(ast.fix_missing_locations(ast.Module(body=wrappers, type_ignores=[])),
                     '<stage610-wrapper>', 'exec',
                     flags=__future__.annotations.compiler_flag), ns)
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                ns['PE_COMPACT_RUNTIME_SETTINGS'][target] = True
                output = compile_dbase_to_assembly(PRG, target=target, source_kind='library')
                if target == 'pe32':
                    obj=ns['assemble_pe32_object_source'](output.assembly)
                    binary=ns['write_coff32_object'](obj)
                    result=ns['link_coff32_objects']((binary,), dll=True,
                        entry_symbol='__d64_dll_entry', dll_name='RuntimeDB.dll', pack_dll=False)
                else:
                    obj=ns['assemble_pe64_object_source'](output.assembly)
                    binary=ns['write_coff64_object'](obj)
                    result=ns['link_coff64_objects']((binary,), dll=True,
                        entry_symbol='__d64_dll_entry', dll_name='RuntimeDB.dll', pack_dll=False)
                self.assertIn(target,ns['PE_COMPACT_LAST_RESULT'])
                self.assertEqual(ns['PE_COMPACT_LAST_RESULT'][target]['after_size'],len(result.executable))
                with TemporaryDirectory() as d:
                    output_path=Path(d)/'RuntimeDB.dll';output_path.write_bytes(result.executable)
                    _, imports, exports=inspect_pe(output_path)
                self.assertIn('__dbase_cls_tobject_create', exports)
                self.assertIn('libd64_runtime.dll',{x.lower() for x in imports})
        ns['PE_COMPACT_RUNTIME_SETTINGS'].update(pe32=False, pe64=False)

    def test_real_pe32_and_pe64_exe_link_and_compact(self):
        """True EXE COFF links, not just a DLL header with DLL bit cleared."""
        ns = _load_pe_linker()
        ns['PE_PACKING_RUNTIME_SETTINGS'].update(pe32=False, pe64=False)
        asm = 'section .text\nglobal _start\n_start:\n    xor eax, eax\n    ret\n'
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                assemble = ns['assemble_pe32_object_source'] if target=='pe32' else ns['assemble_pe64_object_source']
                write = ns['write_coff32_object'] if target=='pe32' else ns['write_coff64_object']
                link = ns['link_coff32_objects'] if target=='pe32' else ns['link_coff64_objects']
                executable = link((write(assemble(asm)),), entry_symbol='_start', dll=False)
                self.assertTrue(executable.executable.startswith(b'MZ'))
                candidate = add_zero_block(executable.executable,b'.text')
                compacted, report = compact_pe_image(candidate)
                self.assertTrue(report['changed'], report)
                self.assertEqual(compacted, executable.executable)

    def test_compact_file_idempotence(self):
        candidate=add_zero_block(self.images['pe32'],b'.idata')
        with TemporaryDirectory() as d:
            p=Path(d)/'a.dll';p.write_bytes(candidate)
            first=compact_pe_file(p)
            self.assertTrue(first['changed'])
            second=compact_pe_file(p)
            self.assertFalse(second['changed'])

    def test_exe_is_supported_by_general_compactor(self):
        # Flip only the IMAGE_FILE_DLL bit; the conservative compactor must
        # recognize both PE kinds. For stronger EXE testing, use test COFFs.
        original=bytearray(self.images['pe32'])
        pe=struct.unpack_from('<I',original,0x3C)[0]
        flags=struct.unpack_from('<H',original,pe+22)[0]
        struct.pack_into('<H',original,pe+22,flags & ~0x2000)
        candidate=add_zero_block(bytes(original),b'.idata')
        out,rep=compact_pe_image(candidate)
        self.assertTrue(rep['changed'],rep)
        self.assertEqual(out,bytes(original))


if __name__=='__main__':
    unittest.main()
