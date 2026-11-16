"""Stage 584 regression: freestanding PE32 runtime link avoids GCC 16 pseudo relocator.

Only source/driver command-line checks here; a real MSYS2 MINGW32 toolchain and
Windows host are required to verify the produced DLL on Windows.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
BUILD_SCRIPTS = (
    ROOT / 'runtime/build.win32.sh',
    ROOT / 'runtime/compiler/build.win32.sh',
)


class Stage584LinkerTests(unittest.TestCase):
    def test_both_pe32_runtime_builds_disable_auto_data_import_and_pseudo_relocations(self):
        for script in BUILD_SCRIPTS:
            with self.subTest(script=script):
                source = script.read_text(encoding='utf-8')
                self.assertRegex(source, r'(?m)^\s*if ! gcc -m32 -fPIC -shared -nostdlib \\$')
                self.assertIn('-Wl,--disable-auto-import,--disable-runtime-pseudo-reloc', source)
                self.assertIn('win32/obj/pas_cookie32.o', source)
                self.assertIn('-lbcrypt -lkernel32', source)
                self.assertIn('-Wl,--out-implib,win32/libd64_runtime.dll.a', source)

    def test_stale_dll_removed_before_link_not_after(self):
        for script in BUILD_SCRIPTS:
            with self.subTest(script=script):
                source = script.read_text(encoding='utf-8')
                remove_at = source.index('rm -f win32/libd64_runtime.dll win32/libd64_runtime.dll.a')
                link_at = source.index('if ! gcc -m32 -fPIC -shared -nostdlib')
                self.assertLess(remove_at, link_at)
                self.assertRegex(source[link_at:], r'if ! gcc .*?\n(?:.*\n)*?\s*echo "relocation link error\."',
                                 'The link failure must still abort the build')

    def test_custom_dll_entrypoint_stays_instead_of_crt_replacement(self):
        main = (ROOT / 'runtime/dllmain.cc').read_text(encoding='utf-8')
        self.assertIn('DllMainCRTStartup(', main)
        for script in BUILD_SCRIPTS:
            source = script.read_text(encoding='utf-8')
            self.assertIn('win32/obj/dllmain.o', source)
            self.assertIn('-nostdlib', source)
            self.assertNotIn(' -lmingw32', source)
            self.assertNotIn(' -lmsvcrt', source)

    def test_pe64_build_scripts_unchanged_by_new_options(self):
        for directory in ('runtime', 'runtime/compiler'):
            script = (ROOT / directory / 'build.win64.sh').read_text(encoding='utf-8')
            self.assertNotIn('--disable-runtime-pseudo-reloc', script)


if __name__ == '__main__':
    unittest.main()
