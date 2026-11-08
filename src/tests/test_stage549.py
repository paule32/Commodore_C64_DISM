"""Stage 549: CES is opt-in in the *final* PE32 loader, not just a GUI state.

The tests construct real stage-548 IA-32 loader bytes in isolation so they can
run without PyQt5 or Windows' cabinet.dll and without downgrading ANTLR files.
"""
from __future__ import annotations

import ast
import re
import struct
from pathlib import Path
from types import SimpleNamespace
import zlib

from test_stage539 import make_context, iats
from debug_options import DebugOptions

BASE = Path(__file__).parent
SOURCE = (BASE / "d64_dism.py").read_text(encoding="utf-8")
PARSEABLE = re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', SOURCE)
TREE = ast.parse(PARSEABLE)


def _ctx():
    ns = make_context()
    ns["PE_D64_LOADER_VERSION_PACKED"] = 1
    # Deliberately stale global state: the explicit argument MUST win.
    ns["stage527_debug_options"] = lambda target="pe32": DebugOptions(ces=True)
    return ns


def _args():
    return dict(image_base=0x400000, text_rva=0x1000,
                text_size=0x900, ztext_rva=0x7000, packed_size=200,
                original_entry_rva=0x1000, iat_rvas=iats(),
                d64i_rva=0x1900, loader_rva=0x3000)


def test_ces_disabled_absent_from_loader_even_with_stale_global():
    ns = _ctx()
    make = ns["_build_pe32_mszip_loader"]
    args = _args()
    enabled = make(**args, ces_enabled=True)
    disabled = make(**args, ces_enabled=False)
    assert b"CES: LoadLibraryA failed" in enabled
    assert b"CES: GetProcAddress failed" in enabled
    assert b"MessageBoxA\x00" in enabled
    assert b"CES:" not in disabled
    assert b"MessageBoxA\x00" not in disabled
    assert b"user32.dll\x00" not in disabled
    # The D64I resolver must still be able to resolve DLLs and symbols.
    assert disabled.startswith(b"\x55\x8B\xEC")
    assert b"D64L" in disabled
    assert len(disabled) < len(enabled)


def test_ces_enabled_only_with_d64i_and_disabled_survives_rebuild():
    ns = _ctx()
    make = ns["_build_pe32_mszip_loader"]
    args = _args()
    for rva in (0x3000, 0x3300, 0x3a00):
        assert b"CES:" not in make(**{**args,"loader_rva":rva},ces_enabled=False)
    assert b"CES:" not in make(**{**args,"d64i_rva":0},ces_enabled=True)


def test_compressed_second_stage_matches_ces_disabled_payload():
    ns = _ctx()
    make = ns["_build_pe32_mszip_loader"]
    args = _args()
    # The actual stage-539 packer uses Windows MSZIP; this isolated test
    # substitutes zlib only to exercise the rebase/fallback/restore contract.
    def rebuild(rva):
        return make(**{**args, "loader_rva": rva}, ces_enabled=False)
    original = rebuild(args["loader_rva"])
    packed, virt = ns["_pe_try_compress_second_stage_loader"](
        target="pe32", loader=original,
        loader_rva=args["loader_rva"], ztext_rva=args["ztext_rva"],
        iat_rvas=args["iat_rvas"], image_base=args["image_base"],
        file_alignment=512, rebuild_loader=rebuild)
    decision = ns["PE_LOADER_COMPRESSION_LAST_DECISION"]["pe32"]
    if decision.get("enabled"):
        offset = decision["bootstrap_size"]
        marker = ns["_d64l_info_block"]({})
        tail = len(marker) if packed.endswith(marker) else 0
        payload = packed[offset:-tail] if tail else packed[offset:]
        restored = zlib.decompress(payload)
        assert restored == rebuild(decision["destination_rva"])
    else:
        restored = packed
        assert restored == original
    assert b"CES:" not in restored
    assert b"MessageBoxA\x00" not in restored
    assert virt >= len(packed)


def test_all_pe32_loader_build_paths_pass_a_stable_ces_value():
    names = {
        "_pe32_rebuild_with_mszip_loader": 3,
        "link_coff32_objects": 1,
        "build_pe32_image_with_imports_exports": 3,  # Stage-209, not wrappers
    }
    for name, expected in names.items():
        matches = [node for node in TREE.body
                   if isinstance(node, ast.FunctionDef) and node.name == name]
        if name == "build_pe32_image_with_imports_exports":
            matches = [node for node in matches if node.lineno > 44200 and node.lineno < 44700]
        assert len(matches) == 1, (name, len(matches))
        count = sum(isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "_build_pe32_mszip_loader"
                    and any(k.arg == "ces_enabled" for k in node.keywords)
                    for node in ast.walk(matches[0]))
        assert count == expected, (name, count)


def test_architectures_keep_independent_ces_settings():
    from debug_options import DebugOptions
    ns = {"DebugOptions": DebugOptions,
          "PE_STAGE527_DEBUG_OPTIONS": {"pe32":DebugOptions(),"pe64":DebugOptions()}}
    for name in ("stage527_debug_options", "stage527_set_debug_options"):
        node = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == name)
        exec(compile(ast.Module(body=[node], type_ignores=[]), "<stage549>", "exec"),ns)
    ns["stage527_set_debug_options"](DebugOptions(ces=False),target="pe32")
    ns["stage527_set_debug_options"](DebugOptions(ces=True),target="pe64")
    assert not ns["stage527_debug_options"]("pe32").ces
    assert ns["stage527_debug_options"]("pe64").ces


def test_ide_reads_current_debug_page_and_invalidates_old_image():
    assert "panel.debug_options(target)" in SOURCE
    assert "CES-Einstellung geändert: neu assemblieren/linken" in SOURCE
    assert "self._stage549_sync_debug_options_for_build(document.build_target)" in SOURCE


if __name__ == '__main__':
    for name, val in sorted(globals().items()):
        if name.startswith('test_') and callable(val):
            val(); print('PASS',name)
