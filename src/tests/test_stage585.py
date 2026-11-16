"""Stage 585: PE32 stack-cookie avoids missing InterlockedCompareExchange@12 import.

Source and ABI regression checks. A native NASM/MinGW32 link + Windows run
must be performed with the user's toolchain.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
ASM = ROOT / 'runtime/pascal/cookie32.asm'


class Stage585CookieAtomicTests(unittest.TestCase):
    def test_nasm_uses_atomic_x86_instruction_without_missing_windows_symbol(self):
        source = ASM.read_text(encoding='utf-8')
        self.assertNotIn('extern _InterlockedCompareExchange@12', source)
        self.assertNotIn('call _InterlockedCompareExchange@12', source)
        self.assertIn('lock cmpxchg dword [ecx], edx', source)
        self.assertIn('xor eax, eax', source)
        self.assertIn('or edx, 1', source)
        # ECX is volatile across BCryptGenRandom; the destination is reloaded.
        self.assertLess(source.index('call _BCryptGenRandom@16'),
                        source.index('mov ecx, [ebp+8]            ; reload guard pointer'))
        self.assertLess(source.index('mov ecx, [ebp+8]            ; reload guard pointer'),
                        source.index('lock cmpxchg dword [ecx], edx'))
        self.assertLess(source.index('xor eax, eax'),
                        source.index('lock cmpxchg dword [ecx], edx'))

    def test_error_handling_and_cdecl_exports_unchanged(self):
        source = ASM.read_text(encoding='utf-8')
        for symbol in ('_jit_pas_cookie_initialize32', '_jit_pas_cookie_failure32'):
            self.assertIn(f'global {symbol}', source)
            self.assertIn(f'{symbol}:', source)
        for symbol in ('_BCryptGenRandom@16', '_RaiseFailFastException@12', '_ExitProcess@4'):
            self.assertIn(f'extern {symbol}', source)
            self.assertIn(f'call {symbol}', source)
        self.assertIn('push 0xC0000409', source)
        self.assertIn('ud2', source)

    def test_both_runtime_build_paths_assemble_same_source(self):
        for directory, source_path in (
            ('runtime', 'pascal/cookie32.asm'),
            ('runtime/compiler', '../pascal/cookie32.asm'),
        ):
            with self.subTest(directory=directory):
                script = (ROOT / directory / 'build.win32.sh').read_text('utf-8')
                self.assertIn('win32/obj/pas_cookie32.o', script)
                self.assertIn(source_path, script)
                self.assertIn('-lbcrypt -lkernel32', script)
                self.assertIn('--disable-runtime-pseudo-reloc', script)

    def test_pascal_backend_still_imports_runtime_cookie_apis(self):
        backend = (ROOT / 'c64pascal/compiler.py').read_text('utf-8')
        self.assertIn('jit_pas_cookie_initialize32', backend)
        self.assertIn('jit_pas_cookie_failure32', backend)
        self.assertNotIn('InterlockedCompareExchange@12', ASM.read_text('utf-8'))
        for directory in ('runtime', 'runtime/compiler'):
            defs = (ROOT / directory / 'win32/libd64_runtime.def').read_text('utf-8')
            self.assertIn('jit_pas_cookie_initialize32', defs)
            self.assertIn('jit_pas_cookie_failure32', defs)


if __name__ == '__main__':
    unittest.main()
