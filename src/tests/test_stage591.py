"""Stage 591 regression: DLL physical layout, lean DllMain, field bridges."""
import struct
import unittest
from pathlib import Path
from d64dbase.pe_dll_payload import parse_pe
from d64dbase.pe_dll_compact import compact_pe_dll_layout
from test_stage532 import _compiler
from test_stage542 import unit_program

ROOT=Path(__file__).resolve().parent
c=_compiler()
p=c.SourcePosition(1,1)

class Stage591Tests(unittest.TestCase):
    def test_empty_dll_entry_omits_unnecessary_branch(self):
        prog=c.PascalProgram('foo', (), (), c.CompoundStatement(p, ()))
        for arch,backend,ret in [('pe32',c._PE32CodeGenerator,'    ret 12'),
                                 ('pe64',c._PE64CodeGenerator,'    ret')]:
            with self.subTest(arch=arch):
                generated=backend(prog,library_name='foo').generate().assembly
                entry=generated.split('__d64_dll_entry:',1)[1].split('\n',5)
                self.assertEqual(entry[1].strip(),'mov eax, 1')
                self.assertEqual(entry[2].strip(),ret.strip())
                self.assertNotIn('dll_attach_done',generated)

    def test_nonempty_dll_entry_still_checks_attach(self):
        body=c.CompoundStatement(p,(c.AssignmentStatement(p,'X',c.LiteralExpression(p,5)),))
        prog=c.PascalProgram('foo', (), (c.VarDeclaration(('X',),'integer',None,p),), body)
        for arch,backend in [('pe32',c._PE32CodeGenerator),('pe64',c._PE64CodeGenerator)]:
            with self.subTest(arch=arch):
                generated=backend(prog,library_name='foo').generate().assembly
                self.assertIn('dll_attach_done',generated)
                self.assertIn('    jne __pas_dll_attach_done_',generated)

    def test_field_bridges_export_names_and_scalar_transfer(self):
        for arch,backend in [('pe32',c._PE32CodeGenerator),('pe64',c._PE64CodeGenerator)]:
            with self.subTest(arch=arch):
                asm=backend(unit_program(),unit_name='VCL.Windows').generate().assembly
                get=asm.split('__d64_cls_tfoo_get_fvalue:',1)[1].split('    ret',1)[0]
                sett=asm.split('__d64_cls_tfoo_set_fvalue:',1)[1].split('    ret',1)[0]
                self.assertNotIn('push ebp',get)
                self.assertNotIn('mov cl, byte ptr',get)
                self.assertNotIn('mov r8b, byte ptr',get)
                self.assertIn('dword ptr',get)
                self.assertIn('dword ptr',sett)
                self.assertIn('global __d64_cls_tfoo_get_fvalue',asm)
                self.assertIn('global __d64_cls_tfoo_set_fvalue',asm)
                if arch=='pe32':
                    self.assertIn('mov eax, dword ptr [esp+4]',get)
                    self.assertIn('mov edx, dword ptr [esp+8]',get)
                    self.assertIn('mov ecx, dword ptr [eax+4]',get)
                    self.assertIn('mov dword ptr [edx+0], ecx',get)
                    self.assertIn('mov ecx, dword ptr [edx+0]',sett)
                else:
                    self.assertIn('mov r8d, dword ptr [rcx+4]',get)

    def test_compactor_retains_already_tight_images(self):
        paths=['examples/dbase/build/bin/pe32/d64_dbase_console.dll',
               'examples/dbase/build/bin/pe64/d64_dbase_console.dll']
        for filename in paths:
            with self.subTest(filename=filename):
                original=(ROOT/filename).read_bytes()
                after, info=compact_pe_dll_layout(original)
                self.assertEqual(after,original)
                self.assertFalse(info['changed'])

    def test_compactor_removes_whole_block_hole_without_rva_changes(self):
        sample=(ROOT/'examples/dbase/build/bin/pe32/d64_dbase_console.dll').read_bytes()
        pe=parse_pe(sample)
        fa=pe['f_align']; off=sorted(s['rptr'] for s in pe['secs'] if s['rsize'])[1]
        # Physically insert one FileAlignment hole before a raw section;
        # file data and virtual addresses stay unchanged.
        modified=bytearray(sample[:off]+b'\0'*fa+sample[off:])
        for i,sec in enumerate(pe['secs']):
            if sec['rptr']>=off and sec['rsize']:
                struct.pack_into('<I',modified,pe['sht']+i*40+20,sec['rptr']+fa)
        base=parse_pe(modified)
        optimized, info=compact_pe_dll_layout(modified)
        rebuilt=parse_pe(optimized)
        self.assertTrue(info['changed'],info)
        self.assertGreaterEqual(info['saved_bytes'],fa)
        self.assertEqual(base['entry'],rebuilt['entry'])
        self.assertEqual(base['blob'][base['dd']:base['dd']+128], optimized[rebuilt['dd']:rebuilt['dd']+128])
        for a,b in zip(base['secs'],rebuilt['secs']):
            self.assertEqual((a['name'],a['rva'],a['vsize'],a['chars'],a['data']),
                             (b['name'],b['rva'],b['vsize'],b['chars'],b['data']))
        second, extra=compact_pe_dll_layout(optimized)
        self.assertEqual(second,optimized)
        self.assertFalse(extra['changed'])

    def test_signed_dll_is_left_untouched(self):
        source=(ROOT/'examples/dbase/build/bin/pe32/d64_dbase_console.dll').read_bytes()
        pe=parse_pe(source)
        modified=bytearray(source)
        struct.pack_into('<II',modified,pe['dd']+4*8,0x1800,0x80)
        out,info=compact_pe_dll_layout(modified)
        self.assertEqual(out,bytes(modified))
        self.assertFalse(info['changed'])

if __name__=='__main__': unittest.main()
