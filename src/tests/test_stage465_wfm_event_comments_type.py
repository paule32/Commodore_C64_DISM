# -*- coding: utf-8 -*-
"""Stage 465: TYPE/VARTYPE with inline dBASE comments IN event procedures."""
import pytest
from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized
from test_stage446_real_pe_link import linkers

EVENT_SOURCE = '''B = NEW Form1()
CLASS Form1 OF FORM
    PROCEDURE PushButton1_onClick()
        STORE 123.45 TO xyz
        ? TYPE("xyz")       && N
        ? VARTYPE(xyz)      && N
        IF TYPE("xyz") == "N"
            ? "xyz ist numerisch"
        ENDIF
        STORE "Hallo" TO xyz
        ? TYPE("xyz")       && C
        ? VARTYPE(xyz)      && C
        ? TYPE("unbekannt") && U
        RETURN
ENDCLASS
'''

COMMENT_SOURCE = '''B = NEW Form1()
CLASS Form1 OF FORM
    PROCEDURE PushButton1_onClick()
        /* zwei Zeilen mit Kommentaren
           ? TYPE("unknown")
        */
        STORE "A&&B" TO xyz && Schlusskommentar
        ? xyz       && String mit && bleibt intakt
        ? TYPE("xyz") /* Blockkommentar */ && C
        IF TYPE("xyz") == "C" && Nachtest
            ? "passed" // ignored
        ENDIF
        RETURN
ENDCLASS
'''

@pytest.mark.parametrize('target', ('pe32','pe64'))
@pytest.mark.parametrize('source', (EVENT_SOURCE, COMMENT_SOURCE))
def test_wfm_event_comment_procedure_assembles_links(target, source):
    assembly=compile_slot_optimized(target,False,False,source)
    assert '    call DBaseWfmFormatValue' in assembly
    assert '    cmp ecx, eax' in assembly
    if source == COMMENT_SOURCE:
        assert 'A&&B' in assembly
    tools=linkers()
    obj=tools[f'assemble_{target}_object_source'](assembly)
    bits=64 if target=='pe64' else 32
    coff=tools[f'write_coff{bits}_object'](obj)
    pe=tools[f'link_coff{bits}_objects']((coff,),entry_symbol='__d64_wfm_entry',gui=True)
    assert pe.executable.startswith(b'MZ')
