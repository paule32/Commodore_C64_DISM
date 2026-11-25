import ast
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest
from windows_manifest import normalize_manifest_settings, manifest_xml

SOURCE = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf8')
class ResourceCompilerError(Exception): pass

def payload_function():
    start = SOURCE.index('def project_manifest_payload(')
    end = SOURCE.index('\ndef embed_project_manifest_resource(', start)
    ns = globals().copy()
    exec(SOURCE[start:end], ns)
    return ns['project_manifest_payload']

def config(**kw):
    return normalize_manifest_settings(dict(identity={'name':'Example.App'}, **kw))

def test_defaults():
    cfg = normalize_manifest_settings()
    assert not cfg['linkEnabled'] and not cfg['requireAdministrator'] and not cfg['dpiAware']
    assert payload_function()(cfg, '.') is None

@pytest.mark.parametrize('admin', [False, True])
def test_generated(admin):
    cfg = config(linkEnabled=True, requireAdministrator=admin, dpiAware=True, description='A & B')
    raw = payload_function()(cfg, '.')
    root = ET.fromstring(raw)
    level = root.find('.//{urn:schemas-microsoft-com:asm.v3}requestedExecutionLevel')
    assert level.attrib == {'level': 'requireAdministrator' if admin else 'asInvoker', 'uiAccess':'false'}
    assert root.find('{urn:schemas-microsoft-com:asm.v1}description').text == 'A & B'
    assert root.find('.//{http://schemas.microsoft.com/SMI/2016/WindowsSettings}dpiAwareness').text == 'PerMonitorV2, PerMonitor'

def test_external(tmp_path):
    path = tmp_path / 'app.manifest'
    path.write_text(manifest_xml(config()), encoding='utf8')
    cfg = config(linkEnabled=True, linkFile=path.name)
    assert payload_function()(cfg, tmp_path) == path.read_bytes()
    cfg['requireAdministrator'] = True
    with pytest.raises(ResourceCompilerError, match='requireAdministrator'):
        payload_function()(cfg, tmp_path)
    path.write_text(manifest_xml(cfg), encoding='utf8')
    assert payload_function()(cfg, tmp_path) == path.read_bytes()

def test_invalid_generated():
    with pytest.raises(ResourceCompilerError, match='Namen'):
        payload_function()({'linkEnabled': True}, '.')

def test_normalization_roundtrip():
    import json
    cfg = config(linkEnabled=True, requireAdministrator=True, description='Beschreibung', dpiAware=True)
    assert normalize_manifest_settings(json.loads(json.dumps(cfg))) == cfg

def test_minimize_visibility_handler():
    start = SOURCE.index('        def _project_settings_dock_visibility_changed(')
    end = SOURCE.index('\n        def ',start+16)
    import textwrap
    ns = {}; exec(textwrap.dedent(SOURCE[start:end]),ns)
    class Minimized:
        def isMinimized(self): return True
    ns['_project_settings_dock_visibility_changed'](Minimized(), False)

def test_deferred_hide():
    from types import SimpleNamespace
    import textwrap
    start = SOURCE.index('        def _finish_project_settings_hide(')
    end = SOURCE.index('\n        def ',start+16)
    ns={}; exec(textwrap.dedent(SOURCE[start:end]),ns)
    calls=[]
    obj=SimpleNamespace(isMinimized=lambda:False, project_settings_dock=SimpleNamespace(isHidden=lambda:False), _restore_project_settings_workspace=lambda:calls.append(True))
    ns['_finish_project_settings_hide'](obj)
    assert calls==[]
    obj.project_settings_dock.isHidden=lambda:True
    ns['_finish_project_settings_hide'](obj)
    assert calls==[True]
