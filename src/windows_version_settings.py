"""Project VERSIONINFO settings and Windows certificate subject inspection."""
import json
import os
from pathlib import Path
import subprocess
from collections.abc import Mapping

VERSION_DEFAULTS = dict(enabled=False, CompanyName='', FileDescription='',
    FileVersion='1.0.0.0', ProductName='', ProductVersion='1.0.0.0',
    LegalCopyright='', LegalTrademarks='', OriginalFilename='', InternalName='', Comments='')


def normalize_version_settings(value=None):
    src = value if isinstance(value, Mapping) else {}
    return {key: bool(src.get(key, default)) if key == 'enabled' else
            str(src.get(key, default) or '') for key, default in VERSION_DEFAULTS.items()}


def version_numbers(value):
    parts = value.split('.')
    if len(parts) != 4 or any(not p.isascii() or not p.isdecimal() or len(p) > 5 or int(p) > 65535 for p in parts):
        raise ValueError('FileVersion und ProductVersion benötigen vier Zahlen von 0 bis 65535.')
    return tuple(map(int, parts))


def version_payload(settings, output_path, pack):
    cfg = normalize_version_settings(settings)
    if not cfg['enabled']:
        return None
    path = Path(output_path)
    fixed = {'FILEVERSION': version_numbers(cfg['FileVersion']),
             'PRODUCTVERSION': version_numbers(cfg['ProductVersion']),
             'FILETYPE': 2 if path.suffix.lower() == '.dll' else 1}
    cfg['OriginalFilename'] = cfg['OriginalFilename'] or path.name
    cfg['InternalName'] = cfg['InternalName'] or path.stem
    strings = [('VALUE', k, [v]) for k,v in cfg.items() if k != 'enabled']
    nodes = [('BLOCK', 'StringFileInfo', [('BLOCK', '040904B0', strings)]),
             ('BLOCK', 'VarFileInfo', [('VALUE', 'Translation', [0x0409, 1200])])]
    return pack(fixed, nodes)


def inspect_signing_certificate(cfg, password=''):
    """Read the certificate subject; this is not an Authenticode trust verdict."""
    if os.name != 'nt':
        raise RuntimeError('Zertifikatprüfung benötigt Windows PowerShell.')
    request = dict(source=cfg['certificate_source'], pfx=cfg['pfx_file'],
                   location=cfg['store_location'], store=cfg['store_name'],
                   thumbprint=cfg['thumbprint'], password=password)
    script = r'''
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$r = [Console]::In.ReadToEnd() | ConvertFrom-Json
if ($r.source -eq 'store') {
    $path = 'Cert:\' + $r.location + '\' + $r.store + '\' + $r.thumbprint
    $cert = Get-Item -LiteralPath $path
} else {
    $secure = New-Object System.Security.SecureString
    foreach ($ch in $r.password.ToCharArray()) { $secure.AppendChar($ch) }
    $data = Get-PfxData -FilePath $r.pfx -Password $secure
    $cert = @($data.EndEntityCertificates)[0]
}
if ($null -eq $cert) { throw 'Kein Endzertifikat gefunden.' }
$cert.GetNameInfo([System.Security.Cryptography.X509Certificates.X509NameType]::SimpleName, $false)
'''
    result = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],
        input=json.dumps(request, ensure_ascii=True), encoding='utf-8', errors='replace',
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode or not result.stdout.strip():
        raise RuntimeError('Zertifikat konnte nicht gelesen werden. Pfad, Speicher und Passwort prüfen.')
    return result.stdout.strip()


def inspect_signed_publisher(path):
    if os.name != 'nt':
        raise RuntimeError('Windows erforderlich.')
    script = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$p = [Console]::In.ReadToEnd() | ConvertFrom-Json
$cert = (Get-AuthenticodeSignature -LiteralPath $p).SignerCertificate
if ($null -eq $cert) { throw 'Kein Signaturzertifikat.' }
$cert.GetNameInfo([System.Security.Cryptography.X509Certificates.X509NameType]::SimpleName, $false)
'''
    result = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],
        input=json.dumps(str(Path(path).resolve()), ensure_ascii=True), encoding='utf-8', errors='replace',
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode or not result.stdout.strip():
        raise RuntimeError('Signaturzertifikat konnte nicht gelesen werden.')
    return result.stdout.strip()
