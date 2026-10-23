"""Stage 492: Linux Qt5 WFM onClick signature / RETURN regression."""
from pathlib import Path
import pytest
from d64dbase.linux_frontend import compile_linux_wfm, LinuxDBaseError
from test_stage490_linux_qt_terminal import decode_embedded_json

ROOT=Path(__file__).parent

def source(signature='PROCEDURE PushButton1_onClick(Sender, Checked)', body='? "Hallo"\n? Sender\nLOCAL X = Checked\n? X\nRETURN'):
    return ('''CLASS Form1 OF FORM
THIS.PushButton1=NEW BUTTON()
THIS.PushButton1.OnClick=CLASS::PushButton1_onClick
''' + signature + '\n' + body + '\nENDCLASS\n')

@pytest.mark.parametrize('bits', [32,64])
def test_onclick_parameters_are_bounded_into_native_qt_actions(bits):
    result=compile_linux_wfm(source(),bits=bits,filename='Form1.wfm')
    payload=decode_embedded_json(result.assembly,'__linux_wfm_json')
    method=payload['methods']['pushbutton1_onclick']
    assert method['parameters']==['Sender','Checked']
    assert method['kind']=='procedure'
    assert method['actions']==[
        ['print','Hallo',True],
        ['print_value',{'variable':'sender'},True],
        ['set_var','x',{'variable':'checked'}],
        ['print_value',{'variable':'x'},True],
    ]
    assert 'DBaseQtRunFormJson' in result.assembly

@pytest.mark.parametrize('bits',[32,64])
def test_parameterless_procedures_remain_backward_compatible(bits):
    result=compile_linux_wfm(source(signature='PROCEDURE PushButton1_onClick()',
                                   body='? "Alt"\nRETURN'),bits=bits,filename='Form1.wfm')
    method=decode_embedded_json(result.assembly,'__linux_wfm_json')['methods']['pushbutton1_onclick']
    assert method==[['print','Alt',True]]

@pytest.mark.parametrize('bits',[32,64])
def test_function_return_value_and_warning(bits):
    result=compile_linux_wfm(source(signature='FUNCTION PushButton1_onClick(Sender)',
                                    body='RETURN Sender'),bits=bits,filename='Form1.wfm')
    method=decode_embedded_json(result.assembly,'__linux_wfm_json')['methods']['pushbutton1_onclick']
    assert method['actions']==[['return',{'variable':'sender'}]]
    assert any('Rueckgabewert nicht aus' in x or 'Rueckgabewert' in x for x in result.warnings)

@pytest.mark.parametrize('signature,body,expected', [
    ('PROCEDURE PushButton1_onClick(a,b,c)','RETURN','hoechstens zwei'),
    ('PROCEDURE PushButton1_onClick()','RETURN 1','darf keinen RETURN-Wert'),
    ('FUNCTION PushButton1_onClick()','RETURN','erwartet RETURN'),
    ('FUNCTION PushButton1_onClick()','? "Hi"','muss RETURN'),
    ('PROCEDURE PushButton1_onClick(Sender)','DO WHILE .T.','noch nicht implementiert'),
])
def test_invalid_event_method_gives_specific_error(signature,body,expected):
    with pytest.raises(LinuxDBaseError,match=expected):
        compile_linux_wfm(source(signature,body),bits=64,filename='Form1.wfm')

@pytest.mark.parametrize('bits',[32,64])
def test_messagebox_accepts_sender_as_hwnd(bits):
    header='#define user32 "user32.so"\nextern CINT MessageBoxA(HWND,LPCSTR,LPCSTR,UINT) user32 from "MessageBoxA"\n'
    result=compile_linux_wfm(header+source(signature='PROCEDURE PushButton1_onClick(Sender)',
        body='MessageBoxA(Sender,"Hallo","Titel",0)\nRETURN'),bits=bits,filename='Form1.wfm')
    method=decode_embedded_json(result.assembly,'__linux_wfm_json')['methods']['pushbutton1_onclick']
    assert method['actions'][0]==['ffi_call','MessageBoxA',[{'variable':'sender'},'Hallo','Titel',0],'']


def test_function_can_return_native_messagebox_result():
    header='#define user32 "user32.so"\nextern CINT MessageBoxA(HWND,LPCSTR,LPCSTR,UINT) user32 from "MessageBoxA"\n'
    result=compile_linux_wfm(header+source(
        signature='FUNCTION PushButton1_onClick(Sender)',
        body='RETURN MessageBoxA(Sender,"Frage?","Titel",4)'),
        bits=64,filename='Form1.wfm')
    method=decode_embedded_json(result.assembly,'__linux_wfm_json')['methods']['pushbutton1_onclick']
    assert method['actions']==[['ffi_return','MessageBoxA',
                                [{'variable':'sender'},'Frage?','Titel',4]]]
    assert any('Rueckgabewert' in item for item in result.warnings)


def test_runtime_consumes_method_parameter_metadata():
    cpp=(ROOT/'d64qt5/d64qt5_linux_form.cpp').read_text(encoding='utf-8')
    assert 'initialVariables' in cpp
    assert 'parameters=specification.value(QStringLiteral("parameters")).toArray();' in cpp
    assert 'const QVariant sender=QVariant::fromValue(' in cpp
    assert 'nativeX11Id(button)' in cpp
    assert 'eventVariables.insert(parameters.at(1).toString().toLower(),checked);' in cpp
    assert 'QVariant runDBaseActions(' in cpp
    assert 'return args.size()>1 ? compatArgument(args.at(1),variables,form) : QVariant();' in cpp

@pytest.mark.parametrize('bits',[32,64])
def test_event_elf_links_with_native_qt_so(bits):
    from linux_elf import assemble_linux_elf
    from test_stage446_real_pe_link import linkers
    result=compile_linux_wfm(source(),bits=bits,filename='Form1.wfm')
    asm=linkers()
    obj,elf=assemble_linux_elf(result.assembly,bits=bits,filename='Form1.generated.asm',
        assembler32=asm['assemble_pe32_object_source'],
        assembler64=asm['assemble_pe64_object_source'],
        shared_library='libd64_qt5.so',imported_symbols=('DBaseQtRunFormJson',))
    assert obj[:4]==elf[:4]==b'\x7fELF'
    assert b'DBaseQtRunFormJson' in elf
