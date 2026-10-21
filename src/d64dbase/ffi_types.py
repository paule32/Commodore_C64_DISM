"""Win32 API integer, handle and string pointer types for the dBASE FFI.

Windows LLP64: LONG/DWORD/BOOL are always 32 bits, pointer-sized aliases
(HANDLE/SIZE_T/WPARAM/LPARAM/...) change from 32 to 64 bits for PE32+.

String input pointers are distinct from writable output pointers.  A writable
LPSTR/LPWSTR/LPDWORD/LPVOID must receive a valid native memory address; this
module does not pretend that a managed dBASE string is a mutable C buffer.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class WinAPIType:
    name: str
    category: str  # void, integer, pointer, ansi_string, wide_string
    size: int       # bit width, 0 means platform pointer width
    signed: bool = False

    def bits(self, target: str) -> int:
        return self.size or (64 if str(target).casefold() in ('pe64', 'pe32+', 'x64') else 32)

    @property
    def is_string_input(self) -> bool:
        return self.category in ('ansi_string', 'wide_string')

    @property
    def is_pointer(self) -> bool:
        return self.category in ('pointer', 'ansi_string', 'wide_string')


_TYPES: dict[str, WinAPIType] = {}


def _add(names: str, category: str, size: int, signed: bool = False) -> None:
    for name in names.split():
        _TYPES[name] = WinAPIType(name, category, size, signed)


_add('VOID CVOID', 'void', 0)
_add('BOOL BOOLEAN CBOOL', 'integer', 32, True)
_add('BYTE UCHAR', 'integer', 8)
_add('CHAR CCHAR', 'integer', 8, True)
_add('WCHAR', 'integer', 16)
_add('WORD USHORT', 'integer', 16)
_add('SHORT CSHORT', 'integer', 16, True)
_add('DWORD DWORD32 UINT UINT32 CUINT ULONG ULONG32 COLORREF LCID LCTYPE ACCESS_MASK REGSAM', 'integer', 32)
_add('INT CINT INT32 LONG LONG32 CLONG HRESULT NTSTATUS LSTATUS', 'integer', 32, True)
_add('DWORD64 DWORDLONG ULONGLONG ULONG64 UINT64 QWORD', 'integer', 64)
_add('LONGLONG LONG64 INT64', 'integer', 64, True)
_add('ATOM LANGID', 'integer', 16)
_add('HFILE', 'integer', 32, True)
_add('SIZE_T UINT_PTR ULONG_PTR DWORD_PTR WPARAM', 'integer', 0)
_add('SSIZE_T INT_PTR LONG_PTR LPARAM LRESULT', 'integer', 0, True)
_add('HANDLE HWND HINSTANCE HMODULE HDC HICON HCURSOR HMENU HKEY HBRUSH HBITMAP HFONT HPEN '
     'HGLOBAL HLOCAL HRSRC HGDIOBJ HMONITOR HACCEL HPALETTE HHOOK HWINSTA HDESK '
     'HFILE SC_HANDLE SERVICE_STATUS_HANDLE SOCKET FARPROC PROC '
     'PVOID LPVOID LPCVOID PCVOID PBYTE LPBYTE PWORD LPWORD PDWORD LPDWORD PBOOL LPBOOL '
     'PINT LPINT PUINT LPUINT PLONG LPLONG PHANDLE LPHANDLE PCHAR LPSTR PSTR '
     'PWCHAR LPWSTR PWSTR PULONG LPULONG PULONG_PTR LPULONG_PTR', 'pointer', 0)
_add('LPCSTR PCSTR LPCCH', 'ansi_string', 0)
_add('LPCWSTR PCWSTR LPCWCH', 'wide_string', 0)

FFI_TYPES = frozenset(_TYPES)


def ffi_type_info(name: str) -> WinAPIType:
    """Returns a typed ABI descriptor, or raises ValueError for unknown types."""
    value = str(name).strip().upper()
    try:
        return _TYPES[value]
    except KeyError:
        raise ValueError(f'Unbekannter Win32-API-Datentyp: {name}') from None


def ffi_return_instructions(type_name: str, *, is64: bool, storage: str = '__dbase_ffi_return') -> list[str]:
    """Normalize WinAPI integer/pointer return in (E/R)AX to a signed qword.

    The dBASE numeric runtime consumes this qword with FILD. Unsigned 64-bit
    values above INT64_MAX cannot be represented by the current numeric ABI.
    """
    typ = ffi_type_info(type_name)
    if typ.category == 'void':
        return []
    bits = typ.bits('pe64' if is64 else 'pe32')
    lines: list[str] = []
    if bits in (8, 16):
        # SHL/SAR/AND operate on EAX and are supported by both internal COFF
        # assemblers; MOVZX eax, ax is not accepted by the PE32 backend.
        shift = 32 - bits
        if typ.signed:
            lines.extend([f'    shl eax, {shift}', f'    sar eax, {shift}'])
        else:
            lines.append(f'    and eax, {(1 << bits) - 1}')
    if bits == 64:
        if not is64:
            return [f'    mov dword ptr [{storage}], eax',
                    f'    mov dword ptr [{storage}+4], edx']
        return [f'    mov qword ptr [{storage}], rax']
    if bits == 32 and is64 and typ.category != 'void':
        # Writing EAX clears the upper half of RAX. In particular the return
        # from DWORD (0xffffffff) must not become -1.
        lines.append('    mov eax, eax')
    lines.append(f'    mov dword ptr [{storage}], eax')
    if typ.signed:
        lines.extend(['    sar eax, 31', f'    mov dword ptr [{storage}+4], eax'])
    else:
        lines.append(f'    mov dword ptr [{storage}+4], 0')
    return lines
