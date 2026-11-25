import ast
import json
import re
import struct
from pathlib import Path
from typing import Optional, Sequence
import pytest
from windows_version_settings import normalize_version_settings, version_payload, version_numbers

SOURCE = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf8')

@pytest.fixture(scope='module')
def pack():
    ns = dict(struct=struct, Optional=Optional, Sequence=Sequence)
    for name in ('_align','_pad','_utf16z','_version_block','_pack_version_info'):
        start = SOURCE.index('def '+name+'(')
        end = SOURCE.index('\n\ndef ',start+4)
        exec(SOURCE[start:end],ns)
    return ns['_pack_version_info']

@pytest.mark.parametrize('name,kind', [('app.exe',1),('app.dll',2)])
def test_binary_version(pack,name,kind):
    payload=version_payload(dict(enabled=True, CompanyName='Müller & Co', FileVersion='1.2.3.4',ProductVersion='5.6.7.8'),name,pack)
    assert struct.unpack_from('<HHH',payload)==(len(payload),52,0)
    offset=payload.index(struct.pack('<I',0xFEEF04BD))
    fixed=struct.unpack_from('<13I',payload,offset)
    assert fixed[2:6]==(0x10002,0x30004,0x50006,0x70008)
    assert fixed[9]==kind
    for text in ('Müller & Co',name,'StringFileInfo','040904B0','Translation','CompanyName'):
        assert text.encode('utf-16le') in payload
    assert struct.pack('<HH',0x0409,1200) in payload

@pytest.mark.parametrize('bad',['1.2','1.2.3.65536','-1.0.0.0','1.2.3.x','1.2.3.'])
def test_invalid_version(bad):
    with pytest.raises(ValueError): version_numbers(bad)

def test_off_and_roundtrip(pack):
    assert version_payload(None,'app.exe',pack) is None
    a=normalize_version_settings(dict(enabled=True,CompanyName='32 Bit'))
    b=normalize_version_settings(dict(enabled=True,CompanyName='64 Bit'))
    assert json.loads(json.dumps([a,b]))==[a,b]
    assert a!=b

def test_wiring_and_order():
    for bits in (32,64):
        assert f'Settings.Windows.{bits}Bit.Linker.VersionInfo' in SOURCE
    assert SOURCE.count('self._embed_project_version(')==5
    assert SOURCE.count('self._embed_project_version(output_path, document.build_target)\n                    # Stage 610')==2
    assert 'tl.addWidget(self.signtool_button); tl.addWidget(self.signtool,1)' in SOURCE
    assert 'self.signtool_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))' in SOURCE
    assert 'entries[_settings["version_key"]] = [normalize_version_settings(self.project_windows_versions.get(_target))]' in SOURCE
    assert 'self.set_project_windows_version(_target, _version_entries[0] if _version_entries else None, mark_modified=False)' in SOURCE
    ast.parse(re.sub(r'(?m)^(\s*)lazy (?=(?:from|import) )',r'\1',SOURCE))
