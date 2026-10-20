# -*- coding: utf-8 -*-
"""Stage 455: PE32/PE32+ DLL-specific D64Z payload loader.

Unlike an EXE start stub, this DLL loader preserves DllMain's arguments, runs
only on DLL_PROCESS_ATTACH, relocates restored .text after MSZIP decompression,
and returns FALSE (not ExitProcess) on failure. The existing Windows Cabinet
MSZIP compressor is reused; NTFS compression is deliberately not involved.

The Windows loader still handles ordinary imports, .edata, .data and .reloc.
The original .text base relocations are re-applied after the code is restored.
"""
from __future__ import annotations

import ctypes
import os
import struct
from pathlib import Path

DLL_LOADER_IMPORTS = {
    '__d64_dll_CreateDecompressor': ('cabinet.dll', 'CreateDecompressor'),
    '__d64_dll_Decompress': ('cabinet.dll', 'Decompress'),
    '__d64_dll_CloseDecompressor': ('cabinet.dll', 'CloseDecompressor'),
    '__d64_dll_VirtualProtect': ('kernel32.dll', 'VirtualProtect'),
    '__d64_dll_FlushInstructionCache': ('kernel32.dll', 'FlushInstructionCache'),
}
D64Z = struct.Struct('<4sHHIIIIII')
_FILE_ALIGN_FALLBACK = 0x200


def _u16(b, off): return struct.unpack_from('<H', b, off)[0]
def _u32(b, off): return struct.unpack_from('<I', b, off)[0]
def _u64(b, off): return struct.unpack_from('<Q', b, off)[0]
def _round(x, a): return (x + a - 1) // a * a


def mszip_compress(data: bytes) -> bytes:
    """The same Windows Cabinet Compression API/MSZIP format as the EXE packer."""
    if os.name != 'nt':
        raise OSError('D64Z/MSZIP-DLL-Packing erfordert die Windows Cabinet Compression API.')
    from ctypes import wintypes
    cab = ctypes.WinDLL('cabinet.dll', use_last_error=True)
    cab.CreateCompressor.argtypes = (wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
    cab.CreateCompressor.restype = wintypes.BOOL
    cab.Compress.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                             ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t))
    cab.Compress.restype = wintypes.BOOL
    cab.CloseCompressor.argtypes = (ctypes.c_void_p,)
    cab.CloseCompressor.restype = wintypes.BOOL
    h = ctypes.c_void_p()
    if not cab.CreateCompressor(2, None, ctypes.byref(h)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        inp = ctypes.create_string_buffer(data, len(data))
        need = ctypes.c_size_t()
        if not cab.Compress(h, inp, len(data), None, 0, ctypes.byref(need)):
            err = ctypes.get_last_error()
            if err != 122 or not need.value:
                raise ctypes.WinError(err)
        if not need.value:
            raise OSError('MSZIP returned an empty output size')
        out = ctypes.create_string_buffer(need.value)
        written = ctypes.c_size_t()
        if not cab.Compress(h, inp, len(data), out, need.value, ctypes.byref(written)):
            raise ctypes.WinError(ctypes.get_last_error())
        return out.raw[:written.value]
    finally:
        cab.CloseCompressor(h)


class _Asm:
    """Small relative-branch and RIP-target patcher for DLL entry stubs."""
    def __init__(self, rva=0):
        self.rva = rva
        self.buf = bytearray()
        self.labels = {}
        self.patch = []
    def emit(self, bs): self.buf.extend(bs)
    def u32(self, v): self.emit(struct.pack('<I', v & 0xffffffff))
    def u64(self, v): self.emit(struct.pack('<Q', v & 0xffffffffffffffff))
    def label(self, name): self.labels[name] = len(self.buf)
    def jump(self, name, cond=None):
        self.emit(b'\xE9' if cond is None else b'\x0F'+bytes((cond,)))
        at = len(self.buf)
        self.u32(0)
        self.patch.append((at, 'label', name))
    def rip(self, insn, target):
        self.emit(insn)
        at = len(self.buf)
        self.u32(0)
        self.patch.append((at, 'rva', target))
    def rva_label(self, name):
        at = len(self.buf)
        self.u32(0)
        self.patch.append((at, 'label_rva', name))
    def rip_label(self, insn, name):
        self.emit(insn)
        at = len(self.buf)
        self.u32(0)
        self.patch.append((at, 'label', name))
    def done(self):
        for at, kind, value in self.patch:
            if kind == 'label_rva':
                struct.pack_into('<I', self.buf, at, self.rva + self.labels[value])
                continue
            target = self.labels[value] if kind == 'label' else value - self.rva
            disp = target - (at + 4)
            if not -(1<<31) <= disp < (1<<31):
                raise ValueError('DLL loader rel32 outside range')
            struct.pack_into('<i', self.buf, at, disp)
        return bytes(self.buf)


def _x86_stub(loader_rva, text_rva, size, packed_rva, packed_size,
              reloc_rva, reloc_count, entry_rva, base, api):
    """PIC x86 entry: module base is original DllMain HINSTANCE argument."""
    b = _Asm(loader_rva)
    # Only process attach (reason=1); thread attach/detach must not unpack again.
    b.emit(b'\x83\x7C\x24\x08\x01')
    b.jump('non_attach', 0x85)
    b.jump('process_attach')
    b.label('non_attach')
    # Unloading a DLL after failed PROCESS_ATTACH must not call its empty .text.
    b.emit(b'\x8B\x44\x24\x04\x80\xB8')
    b.rva_label('loaded_flag')
    b.emit(b'\x01')
    b.jump('uninitialized', 0x85)
    b.jump('original')
    b.label('process_attach')
    b.emit(b'\x55\x8B\xEC\x83\xEC\x28\x53\x56\x57')
    # Local variables: [ebp-4]=compressor, -8=written, -12=oldprot, -16=temp.
    b.emit(b'\x8B\x5D\x08')  # mov ebx, hInstance = loaded image base
    # CreateDecompressor(2, NULL, &handle)
    b.emit(b'\x8D\x45\xFC\x50\x6A\x00\x6A\x02')
    b.emit(b'\xFF\x93'); b.u32(api['CreateDecompressor'])
    b.emit(b'\x85\xC0'); b.jump('failed', 0x84)
    # VirtualProtect(base+text_rva, size, 0x40, &oldProtect)
    b.emit(b'\x8D\x45\xF4\x50\x6A\x40\x68'); b.u32(size)
    b.emit(b'\x8D\x83'); b.u32(text_rva); b.emit(b'\x50')
    b.emit(b'\xFF\x93'); b.u32(api['VirtualProtect'])
    b.emit(b'\x85\xC0'); b.jump('failed', 0x84)
    # Decompress(handle, payload, compressedSize, text, originalSize, &written)
    b.emit(b'\x8D\x45\xF8\x50\x68'); b.u32(size)
    b.emit(b'\x8D\x83'); b.u32(text_rva); b.emit(b'\x50')
    b.emit(b'\x68'); b.u32(packed_size)
    b.emit(b'\x8D\x83'); b.u32(packed_rva); b.emit(b'\x50')
    b.emit(b'\xFF\x75\xFC\xFF\x93'); b.u32(api['Decompress'])
    b.emit(b'\x85\xC0'); b.jump('failed', 0x84)
    b.emit(b'\x81\x7D\xF8'); b.u32(size)
    b.jump('failed', 0x85)
    b.emit(b'\xFF\x75\xFC\xFF\x93'); b.u32(api['CloseDecompressor'])
    # ImageBase delta: apply exactly those HIGHLOW fixups belonging to .text.
    b.emit(b'\x89\xDE\x81\xEE'); b.u32(base)  # esi=actualBase-preferredBase
    b.emit(b'\xBF'); b.u32(reloc_count)       # edi=count
    b.emit(b'\x8D\x93'); b.u32(reloc_rva)  # edx=relocation RVA vector
    b.label('relocs')
    b.emit(b'\x85\xFF'); b.jump('relocs_done', 0x84)
    b.emit(b'\x8B\x0A\x83\xC2\x04\x01\xD9')  # ecx=[edx++], ecx+=ebx
    b.emit(b'\x01\x31')                         # add DWORD [ecx], esi
    b.emit(b'\x4F'); b.jump('relocs')
    b.label('relocs_done')
    # FlushInstructionCache(-1, restored text, size)
    b.emit(b'\x68'); b.u32(size)
    b.emit(b'\x8D\x83'); b.u32(text_rva); b.emit(b'\x50\x6A\xFF')
    b.emit(b'\xFF\x93'); b.u32(api['FlushInstructionCache'])
    # Restore original page access rights.
    b.emit(b'\x8D\x45\xF0\x50\xFF\x75\xF4\x68'); b.u32(size)
    b.emit(b'\x8D\x83'); b.u32(text_rva); b.emit(b'\x50')
    b.emit(b'\xFF\x93'); b.u32(api['VirtualProtect'])
    b.emit(b'\xC6\x83'); b.rva_label('loaded_flag'); b.emit(b'\x01')
    b.emit(b'\x5F\x5E\x5B\x89\xEC\x5D')
    b.label('original')
    b.emit(b'\x8B\x44\x24\x04\x05'); b.u32(entry_rva)
    b.emit(b'\xFF\xE0')  # tail-jump: retain original DllMain arguments
    b.label('failed')
    b.emit(b'\x5F\x5E\x5B\x89\xEC\x5D\x31\xC0\xC2\x0C\x00')
    b.label('uninitialized')
    b.emit(b'\xB8\x01\x00\x00\x00\xC2\x0C\x00')
    b.label('loaded_flag')
    b.emit(b'\x00')
    return b.done()


def _x64_stub(loader_rva, text_rva, size, packed_rva, packed_size,
              reloc_rva, reloc_count, entry_rva, base, api):
    """Win64 ABI: save DllMain arguments and 32-byte call shadow space."""
    b = _Asm(loader_rva)
    b.emit(b'\x83\xFA\x01')  # cmp edx, DLL_PROCESS_ATTACH
    b.jump('non_attach', 0x85)
    b.jump('process_attach')
    b.label('non_attach')
    b.rip_label(b'\x80\x3D', 'loaded_flag')
    b.emit(b'\x01')
    b.jump('uninitialized', 0x85)
    b.jump('original')
    b.label('process_attach')
    # Entry RSP % 16 = 8. push rbp + frame 0xA0 => aligned for API calls.
    b.emit(b'\x55\x48\x89\xE5\x48\x81\xEC'); b.u32(0xA0)
    b.emit(b'\x48\x89\x5D\xF8\x48\x89\x75\xF0\x48\x89\x7D\xE8')
    b.emit(b'\x48\x89\x4D\xC0\x89\x55\xB8\x4C\x89\x45\xB0')
    # locals handle rbp-0x10? overlaps RSI saved -0x10! use -0x30,-0x38,-0x40,-0x48
    # original args: rcx -0x40 overlaps oldprot -0x40! move saved params down.
    # fixed locals: handle -0x28, written -0x30, oldprot -0x34, temp -0x38
    # arg hInst at -0x40; reason -0x48; reserved -0x50
    # CreateDecompressor(2, NULL, &handle)
    b.emit(b'\xB9\x02\x00\x00\x00\x31\xD2\x4C\x8D\x45\xD8')
    b.rip(b'\xFF\x15', api['CreateDecompressor'])
    b.emit(b'\x85\xC0'); b.jump('failed', 0x84)
    # VirtualProtect(..., &oldProtect) last arg r9.
    b.rip(b'\x48\x8D\x0D', text_rva)
    b.emit(b'\xBA'); b.u32(size)
    b.emit(b'\x41\xB8\x40\x00\x00\x00\x4C\x8D\x4D\xCC')
    b.rip(b'\xFF\x15', api['VirtualProtect'])
    b.emit(b'\x85\xC0'); b.jump('failed', 0x84)
    # Decompress(handle, payload, packedSize, text, textSize, &written)
    b.emit(b'\x48\x8B\x4D\xD8')
    b.rip(b'\x48\x8D\x15', packed_rva)
    b.emit(b'\x41\xB8'); b.u32(packed_size)
    b.rip(b'\x4C\x8D\x0D', text_rva)
    b.emit(b'\x48\xC7\x44\x24\x20'); b.u32(size)
    b.emit(b'\x48\x8D\x45\xD0\x48\x89\x44\x24\x28')
    b.rip(b'\xFF\x15', api['Decompress'])
    b.emit(b'\x85\xC0'); b.jump('failed', 0x84)
    b.emit(b'\x81\x7D\xD0'); b.u32(size)
    b.jump('failed', 0x85)
    b.emit(b'\x48\x8B\x4D\xD8')
    b.rip(b'\xFF\x15', api['CloseDecompressor'])
    # Relocations list DWORD RVA; repair 64-bit pointers in restored .text.
    b.emit(b'\x48\x8B\x5D\xC0\x48\x89\xDE\x48\xB8'); b.u64(base)
    b.emit(b'\x48\x29\xC6')
    b.rip(b'\x48\x8D\x3D', reloc_rva)
    b.emit(b'\xB9'); b.u32(reloc_count)
    b.label('relocs')
    b.emit(b'\x85\xC9'); b.jump('relocs_done', 0x84)
    b.emit(b'\x8B\x07\x48\x83\xC7\x04\x48\x8D\x14\x03\x48\x01\x32')
    b.emit(b'\xFF\xC9'); b.jump('relocs')
    b.label('relocs_done')
    # FlushInstructionCache((HANDLE)-1, text, textSize)
    b.emit(b'\x48\xC7\xC1\xFF\xFF\xFF\xFF')
    b.rip(b'\x48\x8D\x15', text_rva)
    b.emit(b'\x41\xB8'); b.u32(size)
    b.rip(b'\xFF\x15', api['FlushInstructionCache'])
    # Restore page protection
    b.rip(b'\x48\x8D\x0D', text_rva)
    b.emit(b'\xBA'); b.u32(size)
    b.emit(b'\x44\x8B\x45\xCC\x4C\x8D\x4D\xC8')
    b.rip(b'\xFF\x15', api['VirtualProtect'])
    # Mark the runtime initialized only after successful decompression.
    b.rip_label(b'\xC6\x05', 'loaded_flag')
    b.emit(b'\x01')
    # Restore original DllMain args and nonvolatile registers
    b.emit(b'\x48\x8B\x4D\xC0\x8B\x55\xB8\x4C\x8B\x45\xB0')
    b.emit(b'\x48\x8B\x5D\xF8\x48\x8B\x75\xF0\x48\x8B\x7D\xE8')
    b.emit(b'\x48\x89\xEC\x5D')
    b.label('original')
    b.rip(b'\xE9', entry_rva)
    b.label('failed')
    b.emit(b'\x48\x8B\x5D\xF8\x48\x8B\x75\xF0\x48\x8B\x7D\xE8')
    b.emit(b'\x48\x89\xEC\x5D\x31\xC0\xC3')
    b.label('uninitialized')
    b.emit(b'\xB8\x01\x00\x00\x00\xC3')
    b.label('loaded_flag')
    b.emit(b'\x00')
    return b.done()


def parse_pe(image: bytes):
    """Minimal strict PE descriptor; all exported/reloc/import RVAs stay stable."""
    blob = bytes(image)
    if len(blob) < 256 or blob[:2] != b'MZ': raise ValueError('Keine Windows PE DLL')
    pe = _u32(blob, 0x3c)
    if pe + 24 > len(blob) or blob[pe:pe+4] != b'PE\0\0':
        raise ValueError('Ungültiger PE Header')
    machine = _u16(blob, pe+4)
    count = _u16(blob, pe+6)
    ch = _u16(blob, pe+22)
    opt = pe+24
    magic = _u16(blob, opt)
    if (machine,magic) not in ((0x014c,0x10b),(0x8664,0x20b)):
        raise ValueError('Nur PE32 oder PE32+ DLL unterstützt')
    if not ch & 0x2000: raise ValueError('Das Eingabeimage ist keine DLL')
    optsize = _u16(blob,pe+20)
    sht = opt + optsize
    if sht + count*40 > len(blob): raise ValueError('Section-Tabelle abgeschnitten')
    secs=[]
    for i in range(count):
        h=sht+i*40
        size,rva,rawsz,rawptr=struct.unpack_from('<IIII',blob,h+8)
        if rawsz and (rawptr==0 or rawptr+rawsz>len(blob)):
            raise ValueError('PE-Sektion liegt außerhalb der Datei')
        secs.append(dict(name=blob[h:h+8].split(b'\0')[0],vsize=size,rva=rva,
                         rsize=rawsz,rptr=rawptr,chars=_u32(blob,h+36),
                         data=blob[rawptr:rawptr+rawsz] if rawsz else b''))
    dd=opt+(0x70 if magic==0x20b else 0x60)
    if dd+16*8>len(blob): raise ValueError('PE-Datenverzeichnisse abgeschnitten')
    base=_u64(blob,opt+24) if magic==0x20b else _u32(blob,opt+28)
    return dict(blob=blob,pe=pe,opt=opt,magic=magic,machine=machine,secs=secs,
                sht=sht,dd=dd,entry=_u32(blob,opt+16),base=base,
                f_align=_u32(blob,opt+36),s_align=_u32(blob,opt+32))


def rva_offset(pe, rva):
    for s in pe['secs']:
        if s['rva'] <= rva < s['rva']+s['rsize']:
            return s['rptr'] + rva - s['rva']
    raise ValueError(f'Kein Datei-Offset für RVA 0x{rva:X}')


def import_iats(pe):
    b=pe['blob']; rva,size=struct.unpack_from('<II',b,pe['dd']+8)
    if not rva or not size: raise ValueError('DLL benötigt echte Importtabelle')
    ptrsize=8 if pe['magic']==0x20b else 4
    out={}
    off=rva_offset(pe,rva)
    while True:
        if off+20>len(b): raise ValueError('Import Descriptor abgeschnitten')
        ilt,_,_,name,iat=struct.unpack_from('<IIIII',b,off)
        if not any((ilt,name,iat)): break
        dll=b[rva_offset(pe,name):].split(b'\0',1)[0].decode('ascii').lower()
        source=ilt or iat
        i=0
        while True:
            trva=source+i*ptrsize
            t_off=rva_offset(pe,trva)
            val=_u64(b,t_off) if ptrsize==8 else _u32(b,t_off)
            if not val: break
            if not (val & (1 << (ptrsize*8-1))):
                imp=b[rva_offset(pe,val)+2:].split(b'\0',1)[0].decode('ascii')
                out[(dll,imp)] = iat+i*ptrsize
            i+=1
        off+=20
    return out


def text_relocations(pe, text):
    b=pe['blob'];rva,size=struct.unpack_from('<II',b,pe['dd']+5*8)
    if not rva or not size:
        raise ValueError('DLL ohne Base-Relocations kann nicht ASLR-sicher gepackt werden')
    typ=10 if pe['magic']==0x20b else 3
    result=[];at=rva_offset(pe,rva);end=at+size
    while at < end:
        if at+8>end:raise ValueError('Reloc Block abgeschnitten')
        page,block=_u32(b,at),_u32(b,at+4)
        if block<8 or block%2 or at+block>end:raise ValueError('Ungültiger Reloc Block')
        for pos in range(at+8,at+block,2):
            word=_u16(b,pos);t=word>>12;fix=page+(word&0xfff)
            if t == 0:
                continue  # IMAGE_REL_BASED_ABSOLUTE padding
            if text['rva'] <= fix < text['rva']+text['vsize']:
                if t != typ: raise ValueError('Nicht unterstützter .text Reloc-Typ')
                if fix+ (8 if typ==10 else 4) > text['rva']+text['vsize']:
                    raise ValueError('Relocation außerhalb von .text')
                result.append(fix)
        at+=block
    return sorted(set(result))


def pack_pe_dll(image: bytes, *, compressor=None) -> bytes:
    """Embed compressed D64Z payload and a DLL_PROCESS_ATTACH unpacking stub."""
    pe=parse_pe(image)
    if any(s['name']==b'.ztext' for s in pe['secs']):
        return bytes(image)  # already packed
    text=next((s for s in pe['secs'] if s['name']==b'.text'),None)
    if text is None or text['vsize']<=0 or text['vsize']>len(text['data']):
        raise ValueError('Keine packbare .text-Sektion')
    imports=import_iats(pe)
    symbols={}
    for _name,(dll,api) in DLL_LOADER_IMPORTS.items():
        lookup=(dll,api)
        if lookup not in imports: raise ValueError('DLL-Packer-Import fehlt: '+dll+'!'+api)
        symbols[api]=imports[lookup]
    relocs=text_relocations(pe,text)
    original=text['data'][:text['vsize']]
    payload=(mszip_compress if compressor is None else compressor)(original)
    if not payload: raise ValueError('Leerer MSZIP-Payload')
    encoded=D64Z.pack(b'D64Z',1,2,1,text['rva'],len(original),len(payload),pe['entry'],
                      __import__('zlib').crc32(original)&0xffffffff)
    payload_block=encoded+payload+b''.join(struct.pack('<I',r) for r in relocs)
    fa=pe['f_align'] or _FILE_ALIGN_FALLBACK; sa=pe['s_align'] or 0x1000
    if fa&(fa-1) or sa&(sa-1):raise ValueError('Ungültige Section-Ausrichtung')
    last=max(_round(s['rva']+max(1,s['vsize']),sa) for s in pe['secs'])
    loader_rva=last
    probe=(_x86_stub if pe['machine']==0x14c else _x64_stub)(
        loader_rva,text['rva'],len(original),0,len(payload),0,len(relocs),
        pe['entry'],pe['base'],symbols)
    data_rva=_round(loader_rva+len(probe),sa)
    packed_rva=data_rva+D64Z.size
    reloc_rva=packed_rva+len(payload)
    loader=(_x86_stub if pe['machine']==0x14c else _x64_stub)(
        loader_rva,text['rva'],len(original),packed_rva,len(payload),reloc_rva,
        len(relocs),pe['entry'],pe['base'],symbols)
    if len(loader)!=len(probe):raise ValueError('Loadergröße instabil')
    parts=[]
    for s in pe['secs']:
        if s is text:
            s=dict(s,data=b'',rsize=0,rptr=0)
        parts.append(s)
    parts.extend([
        dict(name=b'.loader',vsize=len(loader),rva=loader_rva,rsize=0,rptr=0,
             chars=0xE0000020,data=loader),
        dict(name=b'.ztext',vsize=len(payload_block),rva=data_rva,rsize=0,rptr=0,
             chars=0x40000040,data=payload_block),
    ])
    newh=_round(pe['sht']+len(parts)*40,fa)
    cursor=newh
    for s in parts:
        if s['data']:
            s['rptr']=cursor;s['rsize']=_round(len(s['data']),fa);cursor+=s['rsize']
        else:s['rptr']=0;s['rsize']=0
    result=bytearray(cursor)
    result[:pe['sht']]=image[:pe['sht']]
    struct.pack_into('<H',result,pe['pe']+6,len(parts))
    struct.pack_into('<I',result,pe['opt']+16,loader_rva)
    struct.pack_into('<I',result,pe['opt']+56,_round(data_rva+len(payload_block),sa))
    struct.pack_into('<I',result,pe['opt']+60,newh)
    sizecode=sum(s['rsize'] for s in parts if s['chars'] & 0x20)
    sizedata=sum(s['rsize'] for s in parts if s['chars'] & 0x40)
    struct.pack_into('<II',result,pe['opt']+4,sizecode,sizedata)
    for i,s in enumerate(parts):
        off=pe['sht']+40*i
        result[off:off+8]=s['name'][:8].ljust(8,b'\0')
        struct.pack_into('<IIII',result,off+8,s['vsize'],s['rva'],s['rsize'],s['rptr'])
        # preserve original characteristics, and reflow line number/reloc data to zero
        struct.pack_into('<IIII',result,off+24,0,0,0,s['chars'])
        if s['rsize']:
            result[s['rptr']:s['rptr']+len(s['data'])]=s['data']
    candidate=bytes(result)
    parsed=parse_pe(candidate)
    if parsed['entry']!=loader_rva:raise ValueError('DLL entry point not replaced')
    if struct.unpack_from('<II',candidate,parsed['dd']) != struct.unpack_from('<II',image,pe['dd']):
        raise ValueError('DLL export directory changed')
    if text_relocations(parsed,parsed['secs'][next(i for i,s in enumerate(parsed['secs']) if s['name']==b'.text')]) != relocs:
        raise ValueError('Base relocations changed')
    return candidate


def is_payload_packed(path: Path) -> bool:
    try:
        return any(s['name']==b'.ztext' for s in parse_pe(Path(path).read_bytes())['secs'])
    except (OSError,ValueError,struct.error):
        return False
