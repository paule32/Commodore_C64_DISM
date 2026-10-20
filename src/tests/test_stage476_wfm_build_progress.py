"""Stage 476: line-based WFM compile and Windows assembler/link progress."""
from pathlib import Path
import pytest

from windows_asm_macros import preprocess_windows_asm
from d64dbase.compiler import preprocess_dbase_source
from d64dbase.wfm import parse_dbase_wfm
from test_stage446_real_pe_link import linkers


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_assembler_reports_every_expanded_line_including_nested_includes(tmp_path, target):
    nested = tmp_path / 'nested'
    nested.mkdir()
    (nested / 'defs.inc').write_text('%define K 9\n__BREAK__\n', encoding='utf8')
    (tmp_path / 'outer.inc').write_text('%include "nested/defs.inc"\n', encoding='utf8')
    source = '%include "outer.inc"\nsection .text\nentry _start\n_start:\nmov eax, K\nret\n'
    asm_path = tmp_path / 'Form1.generated.asm'
    expanded = preprocess_windows_asm(source, filename=str(asm_path))
    visits = []
    coff = linkers()[f'assemble_{target}_coff_object'](
        source, filename=str(asm_path),
        progress_callback=lambda line, total: visits.append((line, total)),
    )
    assert coff
    assert [i for i, _ in visits] == list(range(1, len(expanded.locations) + 1))
    assert all(total == len(expanded.locations) for _, total in visits)
    assert any(str(nested / 'defs.inc') == name for name, _ in expanded.locations)


def test_error_stops_assembler_line_progress_at_error(tmp_path):
    asm_path = tmp_path / 'bad.asm'
    (tmp_path / 'broken.inc').write_text('mov eax, 2\ninvalid_op eax\n', encoding='utf8')
    source = '%include "broken.inc"\nsection .text\n_start:\nret\n'
    visits = []
    with pytest.raises(Exception):
        linkers()['assemble_pe32_coff_object'](
            source, filename=str(asm_path),
            progress_callback=lambda line, total: visits.append((line, total)),
        )
    assert visits
    assert visits[-1][0] <= visits[-1][1]


def test_wfm_parser_progress_follows_source_lines_and_includes(tmp_path):
    include = tmp_path / 'part.h'
    include.write_text('#define V 9\n', encoding='utf8')
    src = '#include "part.h"\nCLASS Form1 OF FORM\nTHIS.Width = V\nPROCEDURE OnClick()\nRETURN\nENDCLASS\n'
    front = preprocess_dbase_source(src, filename=str(tmp_path / 'Form1.wfm'))
    expanded = front.preprocessed_source
    visited = []
    model = parse_dbase_wfm(expanded, filename='Form1.wfm', progress_callback=visited.append)
    assert model.class_name == 'Form1'
    assert len(expanded.splitlines()) > len(src.splitlines())
    assert visited == sorted(visited)
    assert visited and max(visited) <= len(expanded.splitlines())


def test_gui_progress_is_attached_above_asm_tabs_and_reports_success_failure():
    code = (Path(__file__).parent / 'd64_dism.py').read_text(encoding='utf8')
    header = code.index('assembly_header = QWidget(assembly_host)')
    tabs = code.index('assembly_tabs = QTabWidget(assembly_host)', header)
    assert header < tabs
    assert 'dbase_form_asm_progress' in code[header:tabs]
    assert 'build_progress.setValue(1)' in code[header:tabs]
    for msg in ('Erfolgreich kompiliert !', 'Fehler beim kompilieren !',
                'Linkvorgang erfolgreich !', 'Fehler, Linken nicht möglich !'):
        assert msg in code
    assert 'progress_callback=self._dbase_form_progress_step' in code
    assert 'self._dbase_form_asm_progress_callback = self._dbase_form_progress_step' in code
