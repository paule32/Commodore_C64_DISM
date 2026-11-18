"""Stage 611: typed native TObject NULL-compare codegen and PE smoke links.

The direct IF branch is enabled only if Registerbreite, Prozessorflags,
Stackzustand are all checked. A RETURN still materializes 0/1.
"""
from __future__ import annotations
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from d64dbase import compile_dbase_to_assembly
from pascal_console_dependencies import inspect_pe

ROOT = Path(__file__).parent
SOURCE = (ROOT / 'runtime/dbase/src/System.Objects.prg').read_text('utf8')
ALL = {'register_width': True, 'processor_flags': True, 'stack_state': True}


def method_body(asm: str, name: str) -> str:
    label=f'__dbase_cls_tobject_{name.lower()}:'
    rest=asm.split(label,1)[1]
    return rest.split(f'__dbase_cls_tobject_{name.lower()}_source_end:',1)[0]


class Stage611NullCodegen(unittest.TestCase):
    def compile(self, *, target='pe32', options=ALL, source=SOURCE):
        return compile_dbase_to_assembly(
            source, target=target, source_kind='library',
            peephole_options=options).assembly

    def test_default_unchanged_and_individual_controls(self):
        for target in ('pe32', 'pe64'):
            for opt in (None, {},
                        {'register_width': True, 'processor_flags': True},
                        {'register_width': True, 'stack_state': True},
                        {'processor_flags': True, 'stack_state': True}):
                with self.subTest(target=target, options=opt):
                    body=method_body(self.compile(target=target,options=opt),'free')
                    self.assertIn('    push eax\n' if target=='pe32' else '    push rax\n',body)
                    self.assertIn('    pop edx\n' if target=='pe32' else '    pop rdx\n',body)
                    self.assertIn('    cmp eax, edx\n' if target=='pe32' else '    cmp rax, rdx\n',body)

    def test_direct_branch_all_controls_pe32_and_pe64(self):
        for target,reg,load in (
            ('pe32','eax','    mov eax, dword ptr [ebp+8]'),
            ('pe64','rax','    mov rax, qword ptr [rbp-8]')):
            with self.subTest(target=target):
                asm=self.compile(target=target)
                for method in ('free','freeinstance'):
                    body=method_body(asm,method)
                    exact=(f'{load}\n'
                           f'    test {reg}, {reg}\n'
                           f'    jz __dbase_cls_tobject_{method}_else_1')
                    self.assertIn(exact,body)
                    self.assertNotIn('    cmp '+reg+', ',body)
                    self.assertNotIn('    setne al\n',body)
                    self.assertNotIn('    movzx eax, al\n',body)
                self.assertIn('call __dbase_ffi_jit_object_free',asm)
                self.assertIn('call __dbase_ffi_jit_object_instance_free',asm)

    def test_equality_and_operand_order(self):
        for old,new,op in (
            ('if Self <> NULL','if NULL <> Self','jz'),
            ('if Self <> NULL','if Self = NULL','jnz'),
            ('if Self <> NULL','if NULL = Self','jnz'),
            ('if Self <> NULL','if Self != 0','jz'),
        ):
            with self.subTest(statement=new):
                asm=self.compile(source=SOURCE.replace(old,new,1))
                body=method_body(asm,'free')
                self.assertIn('    test eax, eax\n    '+op+' __dbase_cls_tobject_free_else_1',body)
                self.assertNotIn('    setne al\n',body)
                self.assertNotIn('    pop edx\n',body)

    def test_nonzero_comparison_keeps_original_generic_path(self):
        modified=SOURCE.replace('if Self <> NULL','if Self <> 1',1)
        asm=self.compile(source=modified)
        body=method_body(asm,'free')
        self.assertIn('    push eax\n',body)
        self.assertIn('    cmp eax, edx\n',body)
        self.assertIn('    setne al\n',body)
        self.assertIn('    movzx eax, al\n',body)

    def test_return_boolean_still_normalizes_to_zero_or_one(self):
        for target,reg in (('pe32','eax'),('pe64','rax')):
            with self.subTest(target=target):
                asm=self.compile(target=target)
                body=method_body(asm,'inheritsfrom')
                self.assertIn(f'    test {reg}, {reg}\n    setne al\n    movzx eax, al\n',body)
                self.assertNotIn(f'    cmp {reg}, ',body)
                self.assertNotIn('    pop edx\n',body)
                self.assertNotIn('    pop rdx\n',body)

    def test_source_method_call_and_original_ffi_preserved(self):
        for target in ('pe32','pe64'):
            with self.subTest(target=target):
                old=self.compile(target=target,options=None)
                new=self.compile(target=target)
                old_calls=re.findall(r'^\s*call (__dbase_ffi_[A-Za-z0-9_]+)',old,re.M)
                new_calls=re.findall(r'^\s*call (__dbase_ffi_[A-Za-z0-9_]+)',new,re.M)
                self.assertEqual(old_calls,new_calls)
                self.assertIn('__dbase_vmt_tobject:',new)
                self.assertEqual(old.count('export "'),new.count('export "'))

    def test_real_pe32_pe64_dlls_link(self):
        from test_stage605_link import _load_pe_linker
        linker=_load_pe_linker()
        for target,machine in (('pe32',0x14c),('pe64',0x8664)):
            with self.subTest(target=target):
                assembly=self.compile(target=target)
                if target=='pe32':
                    obj=linker['assemble_pe32_object_source'](assembly)
                    coff=linker['write_coff32_object'](obj)
                    dll=linker['link_coff32_objects']((coff,),entry_symbol='__d64_dll_entry',dll=True,dll_name='RuntimeDB.dll')
                else:
                    obj=linker['assemble_pe64_object_source'](assembly)
                    coff=linker['write_coff64_object'](obj)
                    dll=linker['link_coff64_objects']((coff,),entry_symbol='__d64_dll_entry',dll=True,dll_name='RuntimeDB.dll')
                with TemporaryDirectory() as directory:
                    path=Path(directory)/'RuntimeDB.dll'
                    path.write_bytes(dll.executable)
                    actual_machine,imports,exports=inspect_pe(path)
                self.assertEqual(actual_machine,machine)
                self.assertIn('libd64_runtime.dll',{s.casefold() for s in imports})
                self.assertEqual(len(exports),12)
                self.assertIn('__dbase_cls_tobject_free',exports)

if __name__=='__main__':
    unittest.main()
