"""Stage 501: pure-Python integration tests for Session designer roundtrips."""
import io
from pathlib import Path

from PIL import Image

from d64dbase.session_designer import (
    SESSION_EVENTS, SESSION_METHODS, session_icon_png_bytes,
    session_method_source,
)
from d64dbase.wfm import parse_dbase_wfm
from d64dbase.form_event_handlers import find_event_procedure_offset


def test_session_icon_exactly_36_by_36_transparent():
    raw = session_icon_png_bytes()
    image = Image.open(io.BytesIO(raw))
    assert image.size == (36, 36)
    assert image.mode == "RGBA"
    assert image.getpixel((0, 0))[3] == 0
    assert (Path(__file__).parent / "assets" / "dbase_session_36.png").read_bytes() == raw


def test_session_members_defined_with_exact_requested_spelling():
    assert SESSION_EVENTS == ("beforeRelease", "onPregress")
    assert SESSION_METHODS == (
        "access", "addAlias", "addPassword", "deleteAlias",
        "isAlias", "login", "user",
    )


def test_session_wrappers_provide_compilable_wfm_source_signatures():
    for method in SESSION_METHODS:
        source = session_method_source("Session1", method)
        assert source == [
            f"    function SESSION1_{method}(param)",
            f"        return SESSION::{method}(param)",
        ]


def test_session_wfm_parser_keeps_events_locks_and_wrappers():
    source = """** END HEADER -- do not remove this line
CLASS ParentForm OF FORM
    WITH (THIS)
        THIS.SESSION1 = NEW SESSION(THIS)
        WITH (THIS.SESSION1)
            Name = "SESSION1"
            lockRetryCount = 7
            lockRetryInterval = 250
            beforeRelease = CLASS::SESSION1_beforeRelease
            onPregress = CLASS::SESSION1_onPregress
        ENDWITH
    ENDWITH
""" + "\n".join(session_method_source("Session1", "addAlias")) + "\nENDCLASS\n"
    model = parse_dbase_wfm(source)
    assert len(model.controls) == 1
    session = model.controls[0]
    assert session.class_name == "SESSION"
    assert session.properties["lockRetryCount"] == 7
    assert session.properties["lockRetryInterval"] == 250
    assert session.events == {
        "beforeRelease": "CLASS::SESSION1_beforeRelease",
        "onPregress": "CLASS::SESSION1_onPregress",
    }
    assert len(model.methods) == 1
    assert model.methods[0].name == "SESSION1_addAlias"
    assert find_event_procedure_offset(source, "SESSION1_addAlias") is not None


def test_stage501_integrated_into_existing_designer_and_serialization():
    code = (Path(__file__).parent / "d64_dism.py").read_text(encoding="utf-8")
    assert 'self.session_identification_root = QTreeWidgetItem(' in code
    assert 'self.session_misc_root = QTreeWidgetItem(' in code
    assert 'self.session_parent_edit.doubleClicked.connect(self._navigate_to_session_parent)' in code
    assert 'self.method_grid.cellDoubleClicked.connect(self._session_method_double_clicked)' in code
    assert 'host._open_dbase_form_session_method(item, method.text())' in code
    assert 'lockRetryCount = {max(0,' in code
    assert 'lockRetryInterval = {max(0,' in code
    assert 'if item.component_type in ("Timer", "Session")' in code
