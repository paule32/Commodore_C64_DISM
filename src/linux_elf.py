"""Internal x86/x86-64 ELF object writer and static executable linker.

Stage 486. Pure Python, independent of host operating system, binutils and Qt.
Uses the dBase2Many assembler's encoded sections and COFF-style relocations.
This is a freestanding, syscall-oriented ELF backend, NOT glibc/dynamic linking.
"""
from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Iterable


class LinuxELFError(ValueError):
    pass


@dataclass(frozen=True)
class LinuxELFProgram:
    executable: bytes
    code: bytes
    entry_offset: int = 0
    instruction_count: int = 0


# Windows COFF relocation values emitted by the internal byte encoders.
_I386_ABS32, _I386_PC32 = 0x0006, 0x0014
_X64_ABS64, _X64_ABS32, _X64_PC32 = 0x0001, 0x0002, 0x0004
_R_386_32, _R_386_PC32 = 1, 2
_R_X64_64, _R_X64_PC32, _R_X64_32 = 1, 2, 10


def _align(value, alignment):
    return (value + alignment - 1) & -alignment


def _pack(fmt, *values):
    return struct.pack('<' + fmt, *values)


def _section_header(bits, name, typ, flags, addr, offset, size, link=0, info=0, alignment=1, entsize=0):
    if bits == 32:
        return _pack('IIIIIIIIII', name, typ, flags, addr, offset, size, link, info, alignment, entsize)
    return _pack('IIQQQQIIQQ', name, typ, flags, addr, offset, size, link, info, alignment, entsize)


def _elf_header(bits, elf_type, entry, phoff, shoff, phnum, shnum, shstrndx):
    ident = b'\x7fELF' + bytes((1 if bits == 32 else 2, 1, 1, 0, 0)) + bytes(7)
    if bits == 32:
        return ident + _pack('HHIIIIIHHHHHH', elf_type, 3, 1, entry, phoff, shoff, 0, 52, 32 if phnum else 0, phnum, 40, shnum, shstrndx)
    return ident + _pack('HHIQQQIHHHHHH', elf_type, 62, 1, entry, phoff, shoff, 0, 64, 56 if phnum else 0, phnum, 64, shnum, shstrndx)


def _relocation_type(bits, coff_type):
    if bits == 32:
        if coff_type == _I386_ABS32:
            return _R_386_32, 0
        if coff_type == _I386_PC32:
            return _R_386_PC32, -4
    else:
        if coff_type == _X64_ABS64:
            return _R_X64_64, 0
        if coff_type == _X64_ABS32:
            return _R_X64_32, 0
        if _X64_PC32 <= coff_type <= _X64_PC32 + 5:
            return _R_X64_PC32, -4 - (coff_type - _X64_PC32)
    raise LinuxELFError(f'COFF-Relocation 0x{coff_type:x} ist fuer ELF{bits} nicht implementiert')


def _add_cstring(data, value):
    offset = len(data)
    data.extend(str(value).encode('utf-8') + b'\0')
    return offset


def write_elf_object(obj, *, bits: int) -> bytes:
    """Write a real ET_REL file with .symtab and .rel/.rela relocations."""
    if bits not in (32, 64):
        raise LinuxELFError('Nur ELF32 und ELF64 werden unterstuetzt.')
    if obj.imports or obj.exports or obj.dll_name:
        raise LinuxELFError('Windows-IMPORT/EXPORT/DLLNAME ist in einem Linux-ELF-Objekt nicht moeglich.')
    section_data = {'.text': bytes(obj.code), '.data': bytes(obj.data), '.bss': b''}
    section_size = {'.text': len(obj.code), '.data': len(obj.data), '.bss': int(obj.bss_size)}
    names = ['.text']
    if section_size['.data'] or '.data' in obj.symbol_sections.values() or any(r.section == '.data' for r in obj.relocations):
        names.append('.data')
    if section_size['.bss'] or '.bss' in obj.symbol_sections.values():
        names.append('.bss')
    section_index = {n: i + 1 for i, n in enumerate(names)}
    strtab = bytearray(b'\0')
    syms = []
    for name in obj.symbols:
        sym_section = obj.symbol_sections.get(name, '.text')
        if sym_section not in section_index:
            raise LinuxELFError(f'Symbol {name} in unbekannter Sektion {sym_section}')
        syms.append((name, sym_section, int(obj.symbols[name])))
    undefined = set(str(n).casefold() for n in obj.externals)
    undefined.update(r.symbol.casefold() for r in obj.relocations)
    undefined.difference_update(str(n).casefold() for n in obj.symbols)
    for name in sorted(undefined):
        syms.append((name, None, 0))
    sym_indices = {}
    symtab = bytearray(b'\0' * (16 if bits == 32 else 24))
    for index, (name, section, value) in enumerate(syms, 1):
        sym_indices[name.casefold()] = index
        nameoff = _add_cstring(strtab, name)
        section_no = section_index[section] if section else 0
        if bits == 32:
            symtab.extend(_pack('IIIBBH', nameoff, value, 0, 0x10, 0, section_no))
        else:
            symtab.extend(_pack('IBBHQQ', nameoff, 0x10, 0, section_no, value, 0))
    rel_by_section = {}
    for rel in obj.relocations:
        if rel.section not in section_index or rel.section == '.bss':
            raise LinuxELFError(f'Ungueltige ELF-Relocation in {rel.section}')
        if rel.offset < 0 or rel.offset >= len(section_data[rel.section]):
            raise LinuxELFError('ELF-Relocation ausserhalb der Quelldaten')
        kind, addend = _relocation_type(bits, rel.relocation_type)
        idx = sym_indices.get(rel.symbol.casefold())
        if idx is None:
            raise LinuxELFError(f'Unbekanntes Symbol: {rel.symbol}')
        blob = rel_by_section.setdefault(rel.section, bytearray())
        if bits == 32:
            # ELF32 REL has implicit addends. In the internal COFF buffer the
            # displacement placeholder is zero; PC32 needs an implicit -4.
            blob.extend(_pack('II', rel.offset, idx << 8 | kind))
        else:
            blob.extend(_pack('QQq', rel.offset, idx << 32 | kind, addend))
    # Apply i386 REL implicit addends without altering the original object.
    for rel in obj.relocations:
        if bits == 32 and rel.relocation_type == _I386_PC32:
            buf = bytearray(section_data[rel.section]); struct.pack_into('<i', buf, rel.offset, -4)
            section_data[rel.section] = bytes(buf)
    sections = []
    for name in names:
        sections.append(dict(name=name, typ=8 if name == '.bss' else 1,
                             flags=6 if name == '.text' else 3, data=section_data[name],
                             size=section_size[name], align=16))
    for sec_name, payload in rel_by_section.items():
        sections.append(dict(name=('.rel' if bits == 32 else '.rela') + sec_name,
                             typ=9 if bits == 32 else 4, flags=0, data=bytes(payload),
                             size=len(payload), align=4 if bits == 32 else 8,
                             target=sec_name, entsize=8 if bits == 32 else 24))
    sections.append(dict(name='.symtab', typ=2, flags=0, data=bytes(symtab), size=len(symtab), align=4 if bits == 32 else 8, entsize=16 if bits == 32 else 24))
    sections.append(dict(name='.strtab', typ=3, flags=0, data=bytes(strtab), size=len(strtab), align=1))
    shnames = bytearray(b'\0')
    for item in sections:
        item['nameoffset'] = _add_cstring(shnames, item['name'])
    shstrname = _add_cstring(shnames, '.shstrtab')
    sections.append(dict(name='.shstrtab', nameoffset=shstrname, typ=3, flags=0, data=bytes(shnames), size=len(shnames), align=1))
    idx = {sec['name']: number for number, sec in enumerate(sections, 1)}
    head_size = 52 if bits == 32 else 64
    buf = bytearray(bytes(head_size))
    for sec in sections:
        if sec['typ'] == 8:
            sec['offset'] = _align(len(buf), sec['align'])
            continue
        aligned = _align(len(buf), sec['align'])
        buf.extend(bytes(aligned - len(buf)))
        sec['offset'] = len(buf)
        buf.extend(sec['data'])
    shoff = _align(len(buf), 8 if bits == 64 else 4)
    buf.extend(bytes(shoff - len(buf)))
    buf.extend(bytes(40 if bits == 32 else 64))
    for sec in sections:
        buf.extend(_section_header(bits, sec['nameoffset'], sec['typ'], sec['flags'], 0,
                                   sec['offset'], sec['size'],
                                   idx['.symtab'] if sec.get('target') else idx['.strtab'] if sec['name'] == '.symtab' else 0,
                                   idx[sec['target']] if sec.get('target') else 1 if sec['name'] == '.symtab' else 0,
                                   sec['align'], sec.get('entsize', 0)))
    buf[:head_size] = _elf_header(bits, 1, 0, 0, shoff, 0, len(sections) + 1, idx['.shstrtab'])
    return bytes(buf)


@dataclass
class _ParsedObject:
    bits: int
    sections: dict
    symbols: dict
    relocations: list


def _read_elf_object(data: bytes) -> _ParsedObject:
    if data[:4] != b'\x7fELF' or data[5] != 1 or data[4] not in (1, 2):
        raise LinuxELFError('Keine little-endian ELF32-/ELF64-Datei.')
    bits = 32 if data[4] == 1 else 64
    if bits == 32:
        vals = struct.unpack_from('<HHIIIIIHHHHHH', data, 16)
        shoff, size, count, shstr_index = vals[5], vals[10], vals[11], vals[12]
        secfmt = '<IIIIIIIIII'; symfmt = '<IIIBBH'; symbytes = 16
    else:
        vals = struct.unpack_from('<HHIQQQIHHHHHH', data, 16)
        shoff, size, count, shstr_index = vals[5], vals[10], vals[11], vals[12]
        secfmt = '<IIQQQQIIQQ'; symfmt = '<IBBHQQ'; symbytes = 24
    if vals[0] != 1 or size != (40 if bits == 32 else 64) or not count or shoff + size * count > len(data):
        raise LinuxELFError('Ungueltiger oder nicht relocierbarer ELF-Objektkopf.')
    headers = [struct.unpack_from(secfmt, data, shoff + j * size) for j in range(count)]
    shstr = headers[shstr_index]
    names = data[shstr[4]:shstr[4] + shstr[5]]
    def getname(offset):
        return names[offset:names.find(b'\0', offset)].decode('utf-8')
    by_index = {i: getname(h[0]) for i, h in enumerate(headers) if i}
    sections = {}
    for i, h in enumerate(headers):
        if i and h[1] in (1, 8) and by_index[i] in ('.text', '.data', '.bss'):
            sections[by_index[i]] = {'data': b'' if h[1] == 8 else data[h[4]:h[4]+h[5]], 'size': h[5]}
    symh = next((h for h in headers if h[1] == 2), None)
    if symh is None:
        raise LinuxELFError('ELF-Objekt besitzt keine Symboltabelle')
    namesh = headers[symh[6]]
    string_bytes = data[namesh[4]:namesh[4] + namesh[5]]
    symbols = {}; indexes = []
    for off in range(symh[4], symh[4] + symh[5], symbytes):
        symbol = struct.unpack_from(symfmt, data, off)
        if bits == 32:
            st_name, value, _, _, _, shndx = symbol
        else:
            st_name, _, _, shndx, value, _ = symbol
        name = string_bytes[st_name:string_bytes.find(b'\0', st_name)].decode('utf-8').casefold()
        indexes.append(name)
        if name:
            symbols[name] = (by_index.get(shndx) if shndx else None, value)
    relocs = []
    for h in headers:
        if h[1] not in (4, 9):
            continue
        section = by_index[h[7]]
        entry_size = 8 if bits == 32 else 24
        for off in range(h[4], h[4] + h[5], entry_size):
            if bits == 32:
                offset, r_info = struct.unpack_from('<II', data, off)
                sym_idx, kind = r_info >> 8, r_info & 255
                width = 4
                if section not in sections or offset + width > len(sections[section]['data']):
                    raise LinuxELFError('Relocation ausserhalb der Sektion')
                initial = struct.unpack_from('<i' if kind == _R_386_PC32 else '<I', sections[section]['data'], offset)[0]
                addend = initial
            else:
                offset, r_info, addend = struct.unpack_from('<QQq', data, off)
                sym_idx, kind = r_info >> 32, r_info & 0xffffffff
            if sym_idx >= len(indexes):
                raise LinuxELFError('Ungueltiger ELF-Symbolindex')
            relocs.append((section, offset, indexes[sym_idx], kind, addend))
    return _ParsedObject(bits, sections, symbols, relocs)


def link_elf_objects(objects: Iterable[bytes], *, bits: int, entry_symbol='_start') -> bytes:
    """Statically link ET_REL inputs into a freestanding ELF32/ELF64 ET_EXEC.

    Supports .text, .data, .bss, global symbol definitions and absolute / PC
    relocations. Undefined symbols are errors; no libc or dynamic loader.
    """
    objects = [_read_elf_object(bytes(item)) for item in objects]
    if not objects:
        raise LinuxELFError('Keine ELF-Objektdateien zum Linken.')
    if bits not in (32, 64) or any(item.bits != bits for item in objects):
        raise LinuxELFError('ELF32 und ELF64 koennen nicht gemeinsam gelinkt werden.')
    positions = []
    section_contents = {'.text': bytearray(), '.data': bytearray()}
    bss_size = 0
    for obj in objects:
        pos = {}
        for section in ('.text', '.data'):
            chunk = obj.sections.get(section, {}).get('data', b'')
            content = section_contents[section]
            content.extend(bytes(_align(len(content), 16) - len(content)))
            pos[section] = len(content)
            content.extend(chunk)
        bss_size = _align(bss_size, 16)
        pos['.bss'] = bss_size
        bss_size += obj.sections.get('.bss', {}).get('size', 0)
        positions.append(pos)
    ehsize = 52 if bits == 32 else 64
    phsize = 32 if bits == 32 else 56
    data_needed = bool(section_contents['.data'] or bss_size)
    phnum = 2 if data_needed else 1
    text_off = 0x1000
    data_off = _align(text_off + len(section_contents['.text']), 0x1000)
    base = 0x08048000 if bits == 32 else 0x400000
    addrs = {'.text': base + text_off, '.data': base + data_off, '.bss': base + data_off + _align(len(section_contents['.data']), 16)}
    # .bss follows .data inside the writable PT_LOAD.
    defined = {}
    for obj, pos in zip(objects, positions):
        for name, (sec, offset) in obj.symbols.items():
            if sec is None:
                continue
            if sec not in addrs:
                raise LinuxELFError(f'Unbekannte Sektion {sec} fuer Symbol {name}')
            if name in defined:
                raise LinuxELFError(f'Symbol mehrfach definiert: {name}')
            defined[name] = addrs[sec] + pos[sec] + int(offset)
    entry = defined.get(str(entry_symbol).casefold())
    if entry is None:
        raise LinuxELFError(f'Linux-Einstiegssymbol nicht gefunden: {entry_symbol}')
    for obj, pos in zip(objects, positions):
        for section, offset, symbol, kind, addend in obj.relocations:
            if symbol not in defined:
                raise LinuxELFError(f'Ungeloestes Linux-Symbol: {symbol} (kein ELF-Import vorhanden)')
            if section not in section_contents:
                raise LinuxELFError(f'Relocation in {section} nicht unterstuetzt')
            target = defined[symbol]
            patch = pos[section] + offset
            patch_address = addrs[section] + patch
            content = section_contents[section]
            if (bits == 32 and kind == _R_386_PC32) or (bits == 64 and kind == _R_X64_PC32):
                value = target + addend - patch_address
                if not -(1 << 31) <= value < (1 << 31):
                    raise LinuxELFError('PC-relative ELF-Relocation ausserhalb von 32 Bit')
                struct.pack_into('<i', content, patch, value)
            elif (bits == 32 and kind == _R_386_32) or (bits == 64 and kind == _R_X64_32):
                value = target + addend
                if not 0 <= value < (1 << 32):
                    raise LinuxELFError('ELF-Adress-Relocation passt nicht in 32 Bit')
                struct.pack_into('<I', content, patch, value)
            elif bits == 64 and kind == _R_X64_64:
                struct.pack_into('<Q', content, patch, (target + addend) & ((1 << 64) - 1))
            else:
                raise LinuxELFError(f'ELF{bits}-Relocationtyp {kind} unbekannt')
    file_data_end = data_off + len(section_contents['.data']) if data_needed else text_off + len(section_contents['.text'])
    exe = bytearray(bytes(file_data_end))
    exe[text_off:text_off + len(section_contents['.text'])] = section_contents['.text']
    if data_needed:
        exe[data_off:data_off + len(section_contents['.data'])] = section_contents['.data']
    if bits == 32:
        phdr = _pack('IIIIIIII', 1, 0, base, base, text_off + len(section_contents['.text']), text_off + len(section_contents['.text']), 5, 0x1000)
        if data_needed:
            phdr += _pack('IIIIIIII', 1, data_off, base + data_off, base + data_off,
                          len(section_contents['.data']), (addrs['.bss'] - addrs['.data']) + bss_size, 6, 0x1000)
    else:
        phdr = _pack('IIQQQQQQ', 1, 5, 0, base, base, text_off + len(section_contents['.text']), text_off + len(section_contents['.text']), 0x1000)
        if data_needed:
            phdr += _pack('IIQQQQQQ', 1, 6, data_off, base + data_off, base + data_off,
                          len(section_contents['.data']), (addrs['.bss'] - addrs['.data']) + bss_size, 0x1000)
    exe[:ehsize] = _elf_header(bits, 2, entry, ehsize, 0, phnum, 0, 0)
    exe[ehsize:ehsize + len(phdr)] = phdr
    return bytes(exe)


def assemble_linux_elf(source: str, *, bits: int, filename: str, assembler32, assembler64,
                       include_dirs=(), progress_callback=None, shared_library=None, imported_symbols=()):
    """Host-independent ASM -> ET_REL + ET_EXEC, static or dynamic .so."""
    if bits == 32:
        obj = assembler32(source, filename=filename, include_dirs=include_dirs,
                          progress_callback=progress_callback)
    elif bits == 64:
        obj = assembler64(source, filename=filename, include_dirs=include_dirs,
                          progress_callback=progress_callback)
    else:
        raise LinuxELFError('Linux erwartet 32 oder 64 Bit')
    output = write_elf_object(obj, bits=bits)
    if shared_library:
        from linux_elf_dynamic import link_elf_dynamic
        program = link_elf_dynamic((output,), bits=bits,
                                   shared_library=shared_library,
                                   imported_symbols=imported_symbols,
                                   entry_symbol=obj.entry_symbol or '_start')
    else:
        program = link_elf_objects((output,), bits=bits,
                                   entry_symbol=obj.entry_symbol or '_start')
    return output, program
