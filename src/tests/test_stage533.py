"""Stage 533 regression: memory-free wrapper must never call itself."""
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parent

class TestRuntimeFree(unittest.TestCase):
    def test_both_memory_implementations_use_resolved_free(self):
        for path in ("runtime/memory.cc", "runtime/compiler/memory.cc"):
            with self.subTest(path=path):
                text=(ROOT/path).read_text(encoding="utf-8")
                start=text.index("_jit_free(void *ptr) {")
                end=text.index("\n}",start)
                body=text[start:end]
                self.assertRegex(body, r"p_free\s*\(")
                self.assertNotRegex(body, r"(?m)^\s*_jit_free\s*\(ptr\)\s*;")

    def test_pe32_runtime_thunk_redirect(self):
        b=(ROOT/"runtime/win32/libd64_runtime.dll").read_bytes()
        pe=struct.unpack_from("<I",b,0x3c)[0]
        self.assertEqual(b[pe:pe+4],b"PE\0\0")
        sec=pe+24+struct.unpack_from("<H",b,pe+20)[0]
        info=next((struct.unpack_from("<IIII",b,sec+i*40+8)
                   for i in range(struct.unpack_from("<H",b,pe+6)[0])
                   if b[sec+i*40:sec+i*40+8].startswith(b".text")),None)
        self.assertIsNotNone(info)
        _,va,_,fileoff=info
        offset=fileoff+(0x23d4-va)
        self.assertEqual(b[offset],0xe8)
        disp=struct.unpack_from("<i",b,offset+1)[0]
        self.assertEqual(0x23d4+5+disp,0x2217)

if __name__=="__main__":
    unittest.main()
