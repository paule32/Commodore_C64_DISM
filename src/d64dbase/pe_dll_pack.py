# -*- coding: utf-8 -*-
"""Stage 452: Windows-native, loader-transparent compression for runtime DLLs.

This is NTFS filesystem compression, NOT an executable PE unpacking stub and
NOT a portable UPX-style packer.  The MZ/PE bytes and exported entry points
stay intact, so Windows can map the file with its ordinary DLL loader.
NTFS compression metadata may be lost when copying to another filesystem.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import shutil
from pathlib import Path

FILE_ATTRIBUTE_COMPRESSED = 0x00000800
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
FSCTL_SET_COMPRESSION = 0x0009C040
COMPRESSION_FORMAT_NONE = 0
COMPRESSION_FORMAT_DEFAULT = 1


def _windows_api():
    """Resolve kernel32 lazily: importing the module works on non-Windows OSes."""
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetFileAttributesW.restype = wintypes.DWORD
    kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                     ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                                     wintypes.HANDLE]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.DeviceIoControl.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                          ctypes.c_void_p, wintypes.DWORD,
                                          ctypes.c_void_p, wintypes.DWORD,
                                          ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    kernel32.DeviceIoControl.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    return ctypes, wintypes, kernel32


def is_ntfs_compressed(path: Path) -> bool:
    """Whether Windows marks the file as compressed; False on non-Windows."""
    if os.name != 'nt':
        return False
    ctypes, _wintypes, api = _windows_api()
    attributes = api.GetFileAttributesW(str(Path(path).resolve()))
    if attributes == INVALID_FILE_ATTRIBUTES:
        raise ctypes.WinError(ctypes.get_last_error())
    return bool(attributes & FILE_ATTRIBUTE_COMPRESSED)


def _set_ntfs_compression_native(path: Path, enabled: bool = True) -> Path:
    """Apply filesystem compression without changing a DLL's in-memory PE image.

    Always fail explicitly on an unsupported filesystem/platform.  Never
    replace the PE with a compressed blob which LoadLibrary cannot load.
    """
    destination = Path(path)
    if not destination.is_file():
        raise FileNotFoundError(str(destination))
    if os.name != 'nt':
        if enabled:
            raise OSError('"pack dll" benötigt Windows und ein NTFS-Laufwerk; '
                          'PE-DLLs dürfen nicht als zlib-Container gespeichert werden.')
        return destination

    if is_ntfs_compressed(destination) == bool(enabled):
        return destination

    ctypes, wintypes, api = _windows_api()
    # GENERIC_READ|GENERIC_WRITE is needed on some NTFS versions for
    # FSCTL_SET_COMPRESSION; FILE_WRITE_DATA alone can produce ERROR_ACCESS_DENIED.
    # Keep sharing enabled so antivirus/file-indexing readers do not block us.
    handle = api.CreateFileW(str(destination.resolve()), 0xC0000000, 0x00000007,
                             None, 3, 0x00000080, None)
    if handle is None or int(handle) == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        fmt = ctypes.c_ushort(COMPRESSION_FORMAT_DEFAULT if enabled
                              else COMPRESSION_FORMAT_NONE)
        written = wintypes.DWORD(0)
        if not api.DeviceIoControl(handle, FSCTL_SET_COMPRESSION,
                                   ctypes.byref(fmt), ctypes.sizeof(fmt),
                                   None, 0, ctypes.byref(written), None):
            error = ctypes.get_last_error()
            raise OSError(error, 'NTFS-Komprimierung fehlgeschlagen (Dateisystem '
                          'oder Berechtigungen prüfen): ' + str(ctypes.WinError(error)))
    finally:
        api.CloseHandle(handle)
    if is_ntfs_compressed(destination) != bool(enabled):
        raise OSError('Windows hat den angeforderten NTFS-Komprimierungsstatus '
                      'der DLL nicht übernommen.')
    return destination


def _volume_compression_diagnostic(path: Path) -> str:
    """Describe the target filesystem without assuming WinError 1 means FAT.

    SMB, mapped/substituted drives and filesystem drivers may reject FSCTLs
    even when the physical backing store uses NTFS.  Diagnostic failures must
    never replace the original packaging error.
    """
    if os.name != 'nt':
        return ''
    try:
        ctypes, wintypes, kernel32 = _windows_api()
        kernel32.GetVolumePathNameW.argtypes = [wintypes.LPCWSTR,
                                                 wintypes.LPWSTR, wintypes.DWORD]
        kernel32.GetVolumePathNameW.restype = wintypes.BOOL
        kernel32.GetVolumeInformationW.argtypes = [
            wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR, wintypes.DWORD,
        ]
        kernel32.GetVolumeInformationW.restype = wintypes.BOOL
        root = ctypes.create_unicode_buffer(32768)
        if not kernel32.GetVolumePathNameW(str(Path(path).resolve()), root, len(root)):
            return ''
        filesystem = ctypes.create_unicode_buffer(256)
        flags = wintypes.DWORD(0)
        if not kernel32.GetVolumeInformationW(root.value, None, 0, None,
                                              None, ctypes.byref(flags),
                                              filesystem, len(filesystem)):
            return ''
        # FILE_FILE_COMPRESSION = 0x00000010 (GetVolumeInformationW).
        supported = bool(flags.value & 0x00000010)
        return (f'Ziellaufwerk: {root.value}; Dateisystem: {filesystem.value}; '
                f'Dateikomprimierung: {"unterstützt" if supported else "nicht unterstützt"}. ')
    except (OSError, ValueError, AttributeError, TypeError):
        return ''


def _find_windows_compact_exe() -> str | None:
    """Prefer the system tool even when an IDE has a reduced PATH."""
    for env_var in ('SystemRoot', 'windir'):
        system_root = os.environ.get(env_var)
        if system_root:
            candidate = Path(system_root) / 'System32' / 'compact.exe'
            if candidate.is_file():
                return str(candidate)
    return shutil.which('compact.exe') or shutil.which('compact')


def _compact_windows_fallback(path: Path, enabled: bool) -> Path:
    """Second Windows-native NTFS compression path for access-denied FSCTL.

    compact.exe ships with Windows.  This is filesystem compression only:
    the DLL stays an ordinary unmodified PE image and can use LoadLibrary.
    """
    destination = Path(path)
    compact_exe = _find_windows_compact_exe()
    if not compact_exe:
        raise FileNotFoundError('Windows compact.exe wurde nicht gefunden')
    args = [compact_exe, '/C' if enabled else '/U', '/I', '/Q', str(destination.resolve())]
    result = subprocess.run(args, capture_output=True, text=True, errors='replace',
                            timeout=60, check=False)
    if result.returncode != 0 or is_ntfs_compressed(destination) != bool(enabled):
        details = (result.stderr or result.stdout or '').strip()
        raise OSError('Windows compact.exe konnte die DLL nicht komprimieren '
                      f'(Exitcode {result.returncode}): {details[:400]}')
    return destination


# These errors may come from redirectors, non-NTFS volumes, security filters,
# or an unsupported FSCTL.  The alternate Windows command is worth trying,
# but its success MUST be checked against the file attributes.
_RETRYABLE_WIN32_ERRORS = frozenset((1, 5, 32, 50, 87))
_RETRYABLE_ERRNOS = frozenset((1, 5, 13, 32, 50, 87))


def set_ntfs_compression(path: Path, enabled: bool = True) -> Path:
    """Try FSCTL, then compact.exe for unavailable/denied filesystem IOCTLs.

    Never claim success unless Windows reports the requested file attribute.
    For WinError 1 / 50, where neither path works, include the target volume's
    filesystem and explicit advice instead of an opaque 'Unzulässige Funktion'.
    """
    try:
        return _set_ntfs_compression_native(path, enabled)
    except OSError as primary:
        if os.name != 'nt' or not enabled:
            raise
        winerror = getattr(primary, 'winerror', None)
        errno = getattr(primary, 'errno', None)
        if (winerror not in _RETRYABLE_WIN32_ERRORS
                and errno not in _RETRYABLE_ERRNOS):
            raise
        try:
            return _compact_windows_fallback(path, enabled)
        except (OSError, subprocess.TimeoutExpired) as fallback:
            filesystem = _volume_compression_diagnostic(path)
            if winerror in (1, 50) or errno in (1, 50):
                reason = ('Windows unterstützt den Komprimierungsbefehl für '
                          'dieses Ziel nicht (WinError 1/50). ')
            else:
                reason = ('Windows hat die NTFS-Komprimierung verweigert. ')
            raise OSError(
                reason + filesystem
                + 'Auch compact.exe konnte die Datei nicht komprimieren. '
                  'Bitte ein lokales NTFS-Ausgabeverzeichnis mit Schreibrechten '
                  'wählen oder die Checkbox "pack dll" deaktivieren. '
                  'Die DLL bleibt auch ungepackt normal ladbar. '
                + f'FSCTL: {primary}; compact.exe: {fallback}'
            ) from fallback


def pack_loadable_dll(path: Path, *, compressor=None) -> Path:
    """Validate loader-visible bytes before and after transparent compression.

    The optional compressor is intended for isolated non-Windows tests.
    """
    destination = Path(path)
    raw = destination.read_bytes()
    if len(raw) < 0x40 or raw[:2] != b'MZ':
        raise ValueError('"pack dll": Keine gültige Windows-PE-Datei (MZ fehlt).')
    pe_offset = int.from_bytes(raw[0x3c:0x40], 'little')
    if pe_offset + 24 > len(raw) or raw[pe_offset:pe_offset + 4] != b'PE\0\0':
        raise ValueError('"pack dll": Ungültiger Windows-PE-Header.')
    before = hashlib.sha256(raw).digest()
    (compressor or set_ntfs_compression)(destination, True)
    if hashlib.sha256(destination.read_bytes()).digest() != before:
        raise ValueError('"pack dll": Der PE-Dateiinhalt wurde verändert; '
                         'die DLL darf nicht ausgeliefert werden.')
    return destination


# Stage 453: NTFS compression changes file allocation, not logical PE size.
def compression_report(path: Path) -> dict:
    """Report the real final DLL status, including allocated NTFS bytes.

    GetCompressedFileSizeW returns the physical allocation (not the unchanged
    MZ/PE file length). It may be equal to the file length on tiny images.
    """
    dll = Path(path)
    logical = dll.stat().st_size
    if os.name != 'nt':
        return {"compressed": False, "logical_bytes": logical,
                "allocated_bytes": None}
    ctypes, wintypes, api = _windows_api()
    api.GetCompressedFileSizeW.argtypes = [wintypes.LPCWSTR,
                                            ctypes.POINTER(wintypes.DWORD)]
    api.GetCompressedFileSizeW.restype = wintypes.DWORD
    upper = wintypes.DWORD(0)
    ctypes.set_last_error(0)
    lower = api.GetCompressedFileSizeW(str(dll.resolve()), ctypes.byref(upper))
    if lower == 0xFFFFFFFF and ctypes.get_last_error():
        raise ctypes.WinError(ctypes.get_last_error())
    allocated = (int(upper.value) << 32) | int(lower)
    return {"compressed": is_ntfs_compressed(dll),
            "logical_bytes": logical, "allocated_bytes": allocated}


def replace_verified_runtime(candidate: Path, destination: Path, *,
                             pack_dll: bool = False, check=None, repack=None) -> Path:
    """Install a staged DLL, checking compression on the FINAL destination.

    A same-volume backup restores the previous file if rename or a last-chance
    compression fails. Optional check/repack are used by Windows-attribute
    regression tests; they do not change the production code path.
    """
    source, dest = Path(candidate), Path(destination)
    checker = check or is_ntfs_compressed
    repacker = repack or pack_loadable_dll
    verify = bool(pack_dll and (os.name == 'nt' or check is not None))
    backup = source.parent / (".__dbase_runtime_backup_" + dest.name)
    if backup.exists():
        raise FileExistsError(f"Temporäre DLL-Sicherung existiert bereits: {backup}")
    had_old = dest.is_file()
    if had_old:
        os.replace(dest, backup)
    try:
        os.replace(source, dest)
        if verify and not checker(dest):
            # A successful check on the temporary file is NOT sufficient:
            # reapply after moving if the destination lost its NTFS attribute.
            repacker(dest)
        if verify and not checker(dest):
            raise OSError('"pack dll": Die fertige DLL ist am Ausgabeort '
                          'nicht NTFS-komprimiert. Eine vorhandene DLL wurde '
                          'wiederhergestellt.')
    except BaseException:
        if had_old and backup.is_file():
            os.replace(backup, dest)
        elif not had_old and dest.exists():
            dest.unlink()
        raise
    if backup.is_file():
        backup.unlink()
    return dest
