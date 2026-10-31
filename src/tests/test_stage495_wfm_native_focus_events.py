"""Stage 495: Qt5 runtime delivery for WFM focus events on Windows/Linux.

The Qt5 development libraries aren't available here. These tests validate
Linux JSON generation, ELF linking, and native C++ event-dispatch contracts;
the actual GUI focus transition must be tested on the user's target systems.
"""
from pathlib import Path

import pytest

from d64dbase.linux_frontend import LinuxDBaseError, compile_linux_wfm
from test_stage490_linux_qt_terminal import decode_embedded_json

ROOT = Path(__file__).parent


def source(*, focus='OnGotFocus', lost=True, click=True, form_event=False):
    return ('CLASS Form1 OF FORM\n' +
            ('THIS.OnGotFocus = CLASS::Form1_onGotFocus\n' if form_event else '') +
            'THIS.PushButton1 = NEW BUTTON()\n' +
            f'THIS.PushButton1.{focus} = CLASS::PushButton1_onGotFocus\n' +
            ('THIS.PushButton1.OnLostFocus = CLASS::PushButton1_onLostFocus\n' if lost else '') +
            ('THIS.PushButton1.OnClick = CLASS::PushButton1_onClick\n' if click else '') +
            ('PROCEDURE Form1_onGotFocus(Sender)\n? "Formular im Fokus"\nRETURN\n' if form_event else '') +
            'PROCEDURE PushButton1_onGotFocus(Sender)\n? "Fokus bekommen"\nRETURN\n' +
            ('PROCEDURE PushButton1_onLostFocus(Sender)\n? "Fokus verloren"\nRETURN\n' if lost else '') +
            ('PROCEDURE PushButton1_onClick(Sender)\n? "Geklickt"\nRETURN\n' if click else '') +
            'ENDCLASS\n')


@pytest.mark.parametrize('bits', [32, 64])
def test_linux_wfm_focus_and_click_events_are_encoded_together(bits):
    result = compile_linux_wfm(source(form_event=True), bits=bits, filename='Form1.wfm')
    payload = decode_embedded_json(result.assembly, '__linux_wfm_json')
    assert payload['events'] == {'OnGotFocus': 'CLASS::Form1_onGotFocus'}
    assert payload['controls'][0]['events'] == {
        'OnGotFocus': 'CLASS::PushButton1_onGotFocus',
        'OnLostFocus': 'CLASS::PushButton1_onLostFocus',
        'OnClick': 'CLASS::PushButton1_onClick',
    }
    for name in ('form1_ongotfocus', 'pushbutton1_ongotfocus',
                 'pushbutton1_onlostfocus', 'pushbutton1_onclick'):
        assert payload['methods'][name]['parameters'] == ['Sender']
        assert payload['methods'][name]['actions'][0][0] == 'print'
    assert 'DBaseQtRunFormJson' in result.assembly


@pytest.mark.parametrize('bits', [32, 64])
def test_legacy_event_name_is_accepted(bits):
    payload = decode_embedded_json(
        compile_linux_wfm(source(focus='OnGetFocus', lost=False, click=False),
                          bits=bits, filename='OldForm.wfm').assembly,
        '__linux_wfm_json')
    assert 'OnGetFocus' in payload['controls'][0]['events']
    assert 'pushbutton1_ongotfocus' in payload['methods']


@pytest.mark.parametrize('event', ['OnGotFocus', 'OnLostFocus'])
def test_focus_has_at_most_one_sender_parameter(event):
    bad = source(focus=event, lost=False, click=False).replace(
        'PROCEDURE PushButton1_onGotFocus(Sender)',
        'PROCEDURE PushButton1_onGotFocus(Sender, Checked)')
    with pytest.raises(LinuxDBaseError, match=r'hoechstens einen Ereignisparameter'):
        compile_linux_wfm(bad, bits=64, filename='Form1.wfm')


def test_windows_runtime_handles_new_and_legacy_names_and_returns_sender():
    cpp = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')
    section = cpp.split('class DBaseQtWfmEventFilter final', 1)[1].split(
        'extern "C" D64QT5_API void *DBaseQtNonVisualCreate', 1)[0]
    assert 'QStringLiteral("ongotfocus")' in section
    assert 'QStringLiteral("ongetfocus")' in section
    assert 'QStringLiteral("onlostfocus")' in section
    assert 'QEvent::FocusIn' in section and 'QEvent::FocusOut' in section
    assert 'callback_(watched)' in section
    assert 'widget->setFocusPolicy(Qt::StrongFocus)' in section
    assert 'key == QStringLiteral("onclick")' in section


def test_linux_runtime_installs_true_qt_focus_filters_without_swallowing_events():
    cpp = (ROOT / 'd64qt5/d64qt5_linux_form.cpp').read_text(encoding='utf-8')
    assert 'class DBaseLinuxWfmFocusFilter final : public QObject' in cpp
    assert 'QEvent::FocusIn : QEvent::FocusOut' in cpp
    assert 'widget->installEventFilter(filter)' in cpp
    assert 'return QObject::eventFilter(watched, event);' in cpp
    assert 'nativeX11Id(widget)' in cpp
    assert 'widget->setFocusPolicy(Qt::StrongFocus)' in cpp
    assert 'QAbstractButton::clicked' in cpp
    assert 'if (!bindEvents(form.get()' in cpp


@pytest.mark.parametrize('bits', [32, 64])
def test_native_elf_focus_wfm_links(bits):
    from linux_elf import assemble_linux_elf
    from test_stage446_real_pe_link import linkers
    asm = linkers()
    result = compile_linux_wfm(source(), bits=bits, filename='Form1.wfm')
    obj, elf = assemble_linux_elf(
        result.assembly, bits=bits, filename=f'Form1.generated.linux{bits}.asm',
        assembler32=asm['assemble_pe32_object_source'],
        assembler64=asm['assemble_pe64_object_source'],
        shared_library='libd64_qt5.so', imported_symbols=('DBaseQtRunFormJson',))
    assert obj[:4] == elf[:4] == b'\x7fELF'
    assert b'DBaseQtRunFormJson' in elf
