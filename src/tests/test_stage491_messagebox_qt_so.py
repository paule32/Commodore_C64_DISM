"""Stage 491: Win32 MessageBox aliases use native Linux Qt5 .so C ABI."""
import json
from pathlib import Path
import pytest
from d64dbase.compiler import _preprocess_dbase_macros
from d64dbase.linux_frontend import compile_linux_prg, compile_linux_wfm, LinuxDBaseError
from test_stage490_linux_qt_terminal import decode_embedded_json

ROOT=Path(__file__).parent
HEADER='''#ifdef WINDOWS
#define user32 "user32.dll"
#else
#define user32 "user32.so"
#endif
extern CINT MessageBoxA(HWND,LPCSTR,LPCSTR,UINT) user32 from "MessageBoxA"
'''
HEADER_W=HEADER.replace('MessageBoxA(HWND,LPCSTR,LPCSTR,UINT)',
                        'MessageBoxW(HWND,LPCWSTR,LPCWSTR,UINT)').replace('from "MessageBoxA"','from "MessageBoxW"')

@pytest.mark.parametrize('target,dll', [('pe32','user32.dll'),('pe64','user32.dll'),('linux32','user32.so'),('linux64','user32.so')])
def test_platform_specific_user32_macro(target,dll):
    generated,*_=_preprocess_dbase_macros(HEADER,filename='winapi.h',target=target)
    assert '"'+dll+'"' in generated

@pytest.mark.parametrize('bits', [32,64])
def test_messagebox_from_user32_so_in_prg(bits):
    src=HEADER+'LOCAL result\nresult = MessageBoxA(0, "Hallo", "Titel", 4)\n? result\n'
    out=compile_linux_prg(src,bits=bits,filename='dialog.prg',qt_terminal=True)
    payload=decode_embedded_json(out.assembly,'__linux_console_json')
    assert payload['actions'] == [
        ['ffi_call','MessageBoxA',[0,'Hallo','Titel',4],'result'],
        ['print_var','result',True],
    ]
    assert 'DBaseQtRunConsoleJson' in out.assembly

@pytest.mark.parametrize('bits', [32,64])
def test_messagebox_with_x11_hwnd_and_windows_flags_in_wfm(bits):
    src=(HEADER+'CLASS Form1 OF FORM\nTHIS.Button1=NEW BUTTON()\n'
         'THIS.Button1.OnClick=CLASS::Show\nPROCEDURE Show()\n'
         'MessageBoxA(THIS.HWND, "Wie geht es?", "Frage", 0x24)\nRETURN\nENDCLASS\n')
    generated=compile_linux_wfm(src,bits=bits,filename='Form1.wfm')
    payload=decode_embedded_json(generated.assembly,'__linux_wfm_json')
    assert payload['methods']['show'] == [
        ['ffi_call','MessageBoxA',[{'x11_window':True},'Wie geht es?','Frage',0x24],'']
    ]

@pytest.mark.parametrize('bits',[32,64])
def test_wide_message_box_import(bits):
    result=compile_linux_prg(HEADER_W+'MessageBoxW(0,"Grüße","Titel",0)\n',bits=bits,
                             filename='unicode.prg',qt_terminal=True)
    actions=decode_embedded_json(result.assembly,'__linux_console_json')['actions']
    assert actions == [['ffi_call','MessageBoxW',[0,'Grüße','Titel',0],'']]

@pytest.mark.parametrize('bad', [
    'MessageBoxA(0,"text","title")',
    'MessageBoxA(0,123,"title",0)',
    'MessageBoxA(123,"text","title",0)',
    'MessageBoxA(0,"text","title","flags")',
])
def test_messagebox_ffi_rejects_bad_call(bad):
    with pytest.raises(LinuxDBaseError):
        compile_linux_prg(HEADER+bad+'\n',bits=64,filename='bad.prg',qt_terminal=True)


def test_linux_shared_library_exports_messagebox_and_maps_result_codes():
    cpp=(ROOT/'d64qt5/d64qt5_linux_form.cpp').read_text(encoding='utf-8')
    header=(ROOT/'d64qt5/d64qt5_bridge.h').read_text(encoding='utf-8')
    script=(ROOT/'d64qt5/build_linux.sh').read_text(encoding='utf-8')
    assert 'D64QT5_API int MessageBoxA(' in cpp
    assert 'D64QT5_API int MessageBoxW(' in cpp
    assert 'D64QT5_API int MessageBoxA(' in header
    assert 'D64QT5_API int MessageBoxW(' in header
    assert '::MessageBoxA(hwnd,text.constData(),caption.constData(),flags)' in cpp
    assert 'QMessageBox box(icon,caption,message,buttons,windowForX11Id(hwnd))' in cpp
    for flag in ('0x01U','0x02U','0x03U','0x04U','0x05U'):
        assert flag in cpp
    for result in ('QMessageBox::Ok:', 'QMessageBox::Cancel:', 'QMessageBox::Yes:', 'QMessageBox::No:'):
        assert result in cpp
    assert 'ln -sfn libd64_qt5.so release/user32.so' in script
    assert 'ln -sfn libd64_qt5.so release/shell32.so' in script


def test_messagebox_export_is_available_through_shell32_so_alias():
    source=(
        '#define shell32 "shell32.so"\n'
        'extern CINT MessageBoxA(HWND,LPCSTR,LPCSTR,UINT) shell32 from "MessageBoxA"\n'
        'MessageBoxA(0,"Test","Alias",0)\n'
    )
    output=compile_linux_prg(source,bits=64,filename='alias.prg',qt_terminal=True)
    actions=decode_embedded_json(output.assembly,'__linux_console_json')['actions']
    assert actions == [['ffi_call','MessageBoxA',[0,'Test','Alias',0],'']]
