"""Stage 488: host-independent ELF32/ELF64 dynamic ET_EXEC linker.

Minimal SysV dynamic ABI: PT_INTERP, PT_DYNAMIC, DT_NEEDED, DT_RUNPATH,
.dynsym, .dynstr, .hash and R_*_32/64 symbol relocations. This is not a
replacement for the system's runtime loader; ld-linux resolves the shared
library's dependencies, relocations and constructors when the ELF starts.
"""
from __future__ import annotations

import struct
from typing import Iterable
from linux_elf import (_read_elf_object, _align, _pack, _elf_header, LinuxELFError,
                       _R_386_PC32, _R_386_32, _R_X64_PC32, _R_X64_32, _R_X64_64)


def link_elf_dynamic(objects: Iterable[bytes], *, bits: int, shared_library: str,
                     imported_symbols: Iterable[str], entry_symbol='_start',
                     runpath='$ORIGIN') -> bytes:
    """Link ET_REL inputs to a dynamically loaded ELF executable.

    Only absolute pointer imports are currently supported; unsupported PC32
    external relocations fail rather than emitting invalid PLT calls.
    """
    if bits not in (32, 64):
        raise LinuxELFError('ELF dynamisch: erwartet 32 oder 64 Bit')
    if not shared_library or '/' in shared_library or '\\' in shared_library or '\0' in shared_library:
        raise LinuxELFError('ELF DT_NEEDED erwartet einen sicheren .so-Dateinamen')
    objs = [_read_elf_object(bytes(item)) for item in objects]
    if not objs or any(obj.bits != bits for obj in objs):
        raise LinuxELFError('ELF-Objekte fehlen oder haben falsche Architektur')
    spelling = {str(x).casefold(): str(x) for x in imported_symbols}
    imported = tuple(spelling)
    if not imported:
        raise LinuxELFError('Dynamische ELF-Bindung benoetigt Importsymbole')
    code, data = bytearray(), bytearray()
    positions=[]; bss_size=0
    for obj in objs:
        pos={}
        for name, target in (('.text', code), ('.data', data)):
            target.extend(bytes(_align(len(target),16)-len(target)))
            pos[name]=len(target)
            target.extend(obj.sections.get(name,{}).get('data',b''))
        bss_size=_align(bss_size,16)
        pos['.bss']=bss_size
        bss_size+=obj.sections.get('.bss',{}).get('size',0)
        positions.append(pos)
    text_off=0x1000
    data_off=_align(text_off+len(code),0x1000)
    base=0x08048000 if bits==32 else 0x400000
    addresses={'.text':base+text_off,'.data':base+data_off,
               '.bss':base+data_off+_align(len(data),16)}
    symbols={}
    for obj,pos in zip(objs,positions):
        for name,(section,offset) in obj.symbols.items():
            if section is None: continue
            if section not in addresses or name in symbols:
                raise LinuxELFError(f'Unbekannte Sektion oder Doppeldefinition: {name}')
            symbols[name]=addresses[section]+pos[section]+offset
    entry=symbols.get(entry_symbol.casefold())
    if entry is None:
        raise LinuxELFError(f'ELF-Einstieg nicht definiert: {entry_symbol}')
    dynamic_patches=[]
    for obj,pos in zip(objs,positions):
        for section,offset,name,kind,addend in obj.relocations:
            if section not in ('.text','.data'):
                raise LinuxELFError(f'Dynamische ELF-Relocation in {section} nicht moeglich')
            buf=code if section=='.text' else data
            patch=pos[section]+offset
            location=addresses[section]+patch
            if name in imported and name not in symbols:
                if section!='.data' or kind != (_R_386_32 if bits==32 else _R_X64_64):
                    raise LinuxELFError(f'Dynamischer Import {name}: nur absolute Zeiger in .data erlaubt')
                if addend:
                    raise LinuxELFError(f'Dynamischer Import {name}: Addend nicht unterstuetzt')
                dynamic_patches.append((location,name))
                continue
            if name not in symbols:
                raise LinuxELFError(f'Ungeloestes ELF-Symbol: {name}')
            value=symbols[name]+addend
            if (bits==32 and kind==_R_386_PC32) or (bits==64 and kind==_R_X64_PC32):
                result=value-location
                if not -(1<<31)<=result<(1<<31):
                    raise LinuxELFError('ELF-PC-Relocation ueber 32-Bit-Grenze')
                struct.pack_into('<i',buf,patch,result)
            elif (bits==32 and kind==_R_386_32) or (bits==64 and kind==_R_X64_32):
                if not 0<=value<1<<32:
                    raise LinuxELFError('ELF-ABS32-Ueberlauf')
                struct.pack_into('<I',buf,patch,value)
            elif bits==64 and kind==_R_X64_64:
                struct.pack_into('<Q',buf,patch,value & ((1<<64)-1))
            else:
                raise LinuxELFError(f'Nicht unterstuetzte ELF-Relocation {kind}')
    if not dynamic_patches:
        raise LinuxELFError('Keine dynamischen ELF-Relocations gefunden')
    # ELF dynamic tables reside in the RW PT_LOAD after application data.
    dynstr=bytearray(b'\0')
    def append_string(value):
        offset=len(dynstr);dynstr.extend(value.encode('utf8')+b'\0');return offset
    needed_name=append_string(shared_library)
    runpath_name=append_string(runpath)
    sym_name={name:append_string(spelling[name]) for name in imported}
    symtab=bytearray(bytes(16 if bits==32 else 24))
    sym_index={}
    for idx,name in enumerate(imported,1):
        sym_index[name]=idx
        if bits==32:
            symtab+=_pack('IIIBBH',sym_name[name],0,0,0x12,0,0)
        else:
            symtab+=_pack('IBBHQQ',sym_name[name],0x12,0,0,0,0)
    # SysV hash table with a single bucket and chained symbols.
    nbucket=1; nchain=1+len(imported)
    hashes=_pack('II',nbucket,nchain)+_pack('I',1)
    hashes+=_pack('I',0)
    for i in range(1,nchain):
        hashes+=_pack('I',i+1 if i+1<nchain else 0)
    reloc=bytearray()
    for location,name in dynamic_patches:
        idx=sym_index[name]
        if bits==32:
            reloc+=_pack('II',location,(idx<<8)|_R_386_32)
        else:
            reloc+=_pack('QQq',location,(idx<<32)|_R_X64_64,0)
    metadata={}
    for name,payload,alignment in (
        ('dynstr',dynstr,1),('dynsym',symtab,8 if bits==64 else 4),
        ('hash',hashes,4),('reloc',reloc,8 if bits==64 else 4)):
        target=_align(len(data),alignment)
        data.extend(bytes(target-len(data)))
        metadata[name]=addresses['.data']+target
        data.extend(payload)
    dynamic_tags=[(1,needed_name),(5,metadata['dynstr']),(6,metadata['dynsym']),
                  (4,metadata['hash']),(10,len(dynstr)),(11,24 if bits==64 else 16),
                  (29,runpath_name),
                  (7 if bits==64 else 17,metadata['reloc']),
                  (8 if bits==64 else 18,len(reloc)),
                  (9 if bits==64 else 19,24 if bits==64 else 8),
                  (0,0)]
    dynamic_off=_align(len(data),8 if bits==64 else 4)
    data.extend(bytes(dynamic_off-len(data)))
    dyn_address=addresses['.data']+dynamic_off
    for tag,value in dynamic_tags:
        data.extend(_pack('QQ' if bits==64 else 'II',tag,value))
    dyn_size=len(data)-dynamic_off
    loader=b'/lib/ld-linux.so.2\0' if bits==32 else b'/lib64/ld-linux-x86-64.so.2\0'
    elf_size=52 if bits==32 else 64
    ph_size=32 if bits==32 else 56
    ph_num=4
    interp_off=_align(elf_size+ph_size*ph_num,16)
    if interp_off+len(loader)>text_off:
        raise LinuxELFError('ELF-Interpreter passt nicht in Programmheader')
    raw=bytearray(bytes(data_off+len(data)))
    raw[interp_off:interp_off+len(loader)]=loader
    raw[text_off:text_off+len(code)]=code
    raw[data_off:data_off+len(data)]=data
    if bits==32:
        headers=[_pack('IIIIIIII',3,interp_off,base+interp_off,base+interp_off,len(loader),len(loader),4,1),
                 _pack('IIIIIIII',1,0,base,base,text_off+len(code),text_off+len(code),5,0x1000),
                 _pack('IIIIIIII',1,data_off,base+data_off,base+data_off,len(data), (addresses['.bss']-addresses['.data'])+bss_size+(len(data)-len(data)),6,0x1000),
                 _pack('IIIIIIII',2,data_off+dynamic_off,dyn_address,dyn_address,dyn_size,dyn_size,6,4)]
    else:
        headers=[_pack('IIQQQQQQ',3,4,interp_off,base+interp_off,base+interp_off,len(loader),len(loader),1),
                 _pack('IIQQQQQQ',1,5,0,base,base,text_off+len(code),text_off+len(code),0x1000),
                 _pack('IIQQQQQQ',1,6,data_off,base+data_off,base+data_off,len(data), len(data),0x1000),
                 _pack('IIQQQQQQ',2,6,data_off+dynamic_off,dyn_address,dyn_address,dyn_size,dyn_size,8)]
    # .bss requires re-layout before the in-file dynamic metadata.
    if bss_size:
        raise LinuxELFError('Dynamischer ELF-Linker: .bss wird in Stage 488 noch nicht unterstuetzt')
    raw[:elf_size]=_elf_header(bits,2,entry,elf_size,0,ph_num,0,0)
    raw[elf_size:elf_size+ph_size*ph_num]=b''.join(headers)
    return bytes(raw)
