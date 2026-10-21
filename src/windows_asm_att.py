"""Stage 480: bidirectional GNU AT&T-style x86 source conversion.

The assembler/linker remains the built-in Intel/COFF backend.  Import/entry
metadata uses explicit .d64_* extensions; this is not a GNU as replacement.
Each input line translates into one output line for stable error locations.
"""
from __future__ import annotations

import re

_REGISTER_NAMES = frozenset(('al ah bl bh cl ch dl dh ax bx cx dx si di bp sp '
    'eax ebx ecx edx esi edi ebp esp rax rbx rcx rdx rsi rdi rbp rsp '
    'rip eip sil dil bpl spl st st0 st1 st2 st3 st4 st5 st6 st7').split()) | {
    'r%d%s' % (n, suffix) for n in range(8, 16) for suffix in ('', 'd', 'w', 'b')
} | {'xmm%d' % n for n in range(32)}
_REGISTER_RE = re.compile(r'\b(?:' + '|'.join(sorted(map(re.escape, _REGISTER_NAMES), key=len, reverse=True)) + r')\b', re.I)
_MEMORY_RE = re.compile(r'^\s*(?:(byte|word|dword|qword)\s+ptr\s+)?\[([^]]+)\]\s*$', re.I)
_SUFFIXABLE = set('mov movabs add sub adc sbb cmp test and or xor xchg push pop inc dec neg not lea shl sal shr sar imul mul div idiv'.split())
_NO_SWAP = set('call jmp je jne jz jnz jg jge jl jle ja jae jb jbe jc jnc jo jno js jns ret int'.split())
_SPECIAL_WIDTH = {'movzx': True, 'movsx': True, 'movsxd': True}
_DIRECTIVES_INTEL_TO_ATT = {
    'db': '.byte', 'dw': '.word', 'dd': '.long', 'dq': '.quad',
    'global': '.globl', 'globl': '.globl', 'extern': '.extern',
    'import': '.d64_import', 'entry': '.d64_entry', 'export': '.d64_export',
    'dllname': '.d64_dllname', 'bits': '.d64_bits',
    'resb': '.d64_resb', 'resw': '.d64_resw', 'resd': '.d64_resd', 'resq': '.d64_resq',
    'align': '.balign',
}
_DIRECTIVES_ATT_TO_INTEL = {
    '.byte': 'db', '.2byte': 'dw', '.short': 'dw', '.word': 'dw',
    '.4byte': 'dd', '.long': 'dd', '.int': 'dd', '.8byte': 'dq', '.quad': 'dq',
    '.globl': 'global', '.global': 'global', '.extern': 'extern',
    '.d64_import': 'import', '.d64_entry': 'entry', '.d64_export': 'export',
    '.d64_dllname': 'dllname', '.d64_bits': 'bits',
    '.d64_resb': 'resb', '.d64_resw': 'resw', '.d64_resd': 'resd',
    '.d64_resq': 'resq', '.balign': 'align', '.align': 'align',
}


def contains_att_syntax(source: str) -> bool:
    # Do not treat our %include/%define directives as GNU register syntax.
    return bool(re.search(
        r'(?m)^\s*(?:\.att_syntax|\.(?:p2align|asciz|zero|fill))\b'
        r'|%(?:' + '|'.join(sorted(_REGISTER_NAMES, key=len, reverse=True)) + r')\b',
        source, re.I,
    ))


def _split_operands(text: str) -> list[str]:
    result, depth, quote, start = [], 0, '', 0
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == '\\' and i + 1 < len(text):
                i += 2; continue
            if ch == quote:
                if i + 1 < len(text) and text[i+1] == quote:
                    i += 2; continue
                quote = ''
        elif ch in ('"', "'"):
            quote = ch
        elif ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        elif ch == ',' and depth == 0:
            result.append(text[start:i].strip()); start = i + 1
        i += 1
    result.append(text[start:].strip())
    return result


def _split_comment(line: str):
    """Separate Intel ';' comments without touching quoted strings."""
    quote = ''
    i=0
    while i < len(line):
        ch=line[i]
        if quote:
            if ch == '\\' and i + 1 < len(line):
                i += 2; continue
            if ch == quote:
                if i + 1 < len(line) and line[i+1] == quote:
                    i += 2; continue
                quote = ''
        elif ch in ('"', "'"):
            quote=ch
        elif ch == ';':
            return line[:i], line[i+1:]
        i += 1
    return line, None


def _register_word(word):
    return word.casefold() in _REGISTER_NAMES


def _intel_mem_to_att(inside):
    s=inside.strip().replace(' ', '')
    # The internal COFF backend cannot represent arbitrary symbol+register
    # relocations. Preserve that limitation on either side of conversion.
    terms=re.findall(r'[+-]?[^+-]+',s)
    base=index=None; scale='1'; disp=[]
    for term in terms:
        sign=''
        if term[0] in '+-': sign,term=term[0],term[1:]
        if _register_word(term):
            if sign=='-': raise ValueError('Negatives Basisregister im Speicheroperand')
            if base is None: base=term.casefold()
            elif index is None: index=term.casefold()
            else: raise ValueError('Zu viele Register im Speicheroperand')
        elif '*' in term:
            reg,k=term.split('*',1)
            if not _register_word(reg) or k not in ('1','2','4','8') or index is not None or sign=='-':
                raise ValueError('Ungueltiges Indexregister / Skalenfaktor')
            index,scale=reg.casefold(),k
        else:
            disp.append((sign if disp else ('-' if sign=='-' else ''))+term)
    displacement=''.join(disp)
    if base or index:
        args=('%'+base if base else '')
        if index: args+=',%'+index+(','+scale if scale!='1' else '')
        return displacement+'('+args+')'
    return displacement or '0'


def _intel_operand_to_att(operand, mnemonic, position):
    op=operand.strip()
    mem=_MEMORY_RE.fullmatch(op)
    if mem:
        return _intel_mem_to_att(mem.group(2)), (mem.group(1) or '').casefold()
    if _register_word(op):
        return '%'+op.casefold(), ''
    if op.casefold().startswith('st('):
        return '%'+op, ''
    if re.fullmatch(r'[+-]?(?:\d+|0x[0-9a-f]+|\$[0-9a-f]+)',op,re.I):
        return ('$'+op if mnemonic not in _NO_SWAP else op), ''
    if re.fullmatch(r'[A-Za-z_.$?@][\w.$?@]*',op) or re.fullmatch(r'[+-]?\d+',op):
        return ('$'+op if mnemonic not in _NO_SWAP and mnemonic not in ('fld','fstp','fldcw','fnstcw','fild','fistp') else op), ''
    return op, ''


def _reg_size(reg):
    x=reg.lstrip('%').lower()
    if x.startswith('xmm'):return ''
    if x in ('al','ah','bl','bh','cl','ch','dl','dh','sil','dil','spl','bpl') or (x.startswith('r') and x.endswith('b')):return 'b'
    if x in ('ax','bx','cx','dx','si','di','bp','sp') or (x.startswith('r') and x.endswith('w')):return 'w'
    if x in ('eax','ebx','ecx','edx','esi','edi','ebp','esp') or (x.startswith('r') and x.endswith('d')):return 'l'
    if x in ('rax','rbx','rcx','rdx','rsi','rdi','rbp','rsp','rip') or re.fullmatch(r'r(?:[8-9]|1[0-5])',x):return 'q'
    return ''


def intel_to_att(source: str, *, target: str = 'pe32') -> str:
    """Emit actual AT&T operand syntax from internal Intel assembly source.

    The %macro family remains unchanged.  Private COFF import/entry directives
    use .d64_* spellings so the internal linker can round-trip their metadata.
    """
    result=['.att_syntax\n']
    for no,raw in enumerate(source.splitlines(keepends=True),1):
        newline='\r\n' if raw.endswith('\r\n') else ('\n' if raw.endswith('\n') else '')
        line=raw.rstrip('\r\n')
        if not line.strip(): result.append(raw);continue
        if line.lstrip().startswith('%'): result.append(raw);continue
        body,comment=_split_comment(line)
        if not body.strip():
            result.append('#'+(comment or '')+newline);continue
        m=re.match(r'^(\s*)([^\s:]+)(?::\s*(.*))?$',body)
        if m and ':' in body and re.match(r'^\s*[.$?@A-Za-z_][\w.$?@]*:',body):
            label_match=re.match(r'^(\s*[.$?@A-Za-z_][\w.$?@]*:)(.*)$',body)
            if label_match and not label_match.group(2).strip():
                result.append(body+(' #'+comment if comment else '')+newline);continue
        inst=re.match(r'^(\s*)([A-Za-z_.][\w.]*)((?:\s+.*)?)$',body)
        if not inst:
            raise ValueError(f'Intel->AT&T Zeile {no}: nicht unterstuetzte Syntax: {line.strip()}')
        indent,mnemonic,rest=inst.groups();name=mnemonic.casefold();args=rest.strip()
        if name=='bits' and args.strip() in ('32','64'):
            out='.code'+args.strip()
        elif name in ('section', 'segment', '.section', '.segment'):
            # Internal dBase/WFM output uses BOTH 'section .text' and
            # '.section .text'.  The latter must be a GNU section directive,
            # never an AT&T instruction with an immediate '$.text' operand.
            dest=args.split(',', 1)[0].strip().strip('"')
            if dest.startswith('$'):
                # Also tolerate listings emitted by the old Stage 480 bug.
                dest = dest[1:]
            if not dest:
                raise ValueError(f'Intel->AT&T Zeile {no}: leere COFF-Sektion')
            if dest.casefold() in ('.text', '.data', '.bss'):
                out=dest.lower()
            else:
                out='.section '+dest
        elif name in _DIRECTIVES_INTEL_TO_ATT:
            out=_DIRECTIVES_INTEL_TO_ATT[name]+(' '+args if args else '')
        elif name in ('db','dw','dd','dq'):
            out=_DIRECTIVES_INTEL_TO_ATT[name]+' '+args
        elif name in ('text','data','bss') and not args:
            out='.'+name
        elif name in ('cpu','model','public'):
            out='.d64_'+name+(' '+args if args else '')
        elif name in ('times',):
            # Keep NASM-like expression under a private directive.
            out='.d64_times '+args
        elif name in ('resb','resw','resd','resq'):
            out='.d64_'+name+' '+args
        else:
            original=_split_operands(args) if args else []
            converted=[];sizes=[]
            for k,op in enumerate(original):
                c,size=_intel_operand_to_att(op,name,k)
                converted.append(c);sizes.append(size)
            if len(converted)==2 and name not in _NO_SWAP:
                converted.reverse();sizes.reverse()
            elif len(converted)==3 and name=='imul':
                converted=[converted[2],converted[1],converted[0]]
            suffix=''
            if name in ('movzx','movsx') and len(converted)==2:
                # GNU sizes for source and destination are separate.
                src_sz={'byte':'b','word':'w','dword':'l','qword':'q'}.get(sizes[0], '') or _reg_size(converted[0]);dst_sz=_reg_size(converted[1])
                if src_sz and dst_sz:
                    op_prefix='movz' if name=='movzx' else 'movs'
                    gnu_name=op_prefix+src_sz+dst_sz
                else:
                    gnu_name=name
            elif name=='movsxd':
                gnu_name='movslq'
            else:
                gnu_name=name
                if name in _SUFFIXABLE:
                    suffix=next(({'byte':'b','word':'w','dword':'l','qword':'q'}[sizes[i]] for i in range(len(sizes)) if sizes[i]),'')
                    if not suffix:
                        suffix=next((_reg_size(arg) for arg in reversed(converted) if arg.startswith('%')),'')
                    if suffix:gnu_name+=suffix
            if name in ('fld','fstp','fild','fistp') and sizes:
                float_width={'word':'s','dword':'s','qword':'l'}.get(sizes[0], '')
                if float_width:out_name = name + float_width
                else:out_name = gnu_name
                gnu_name = out_name
            if name in ('call','jmp') and converted and converted[0].startswith(('%','(')):
                converted[0]='*'+converted[0]
            out=gnu_name+(' '+', '.join(converted) if converted else '')
        result.append(indent+out+(' #'+comment if comment else '')+newline)
    return ''.join(result)


def _att_mem_to_intel(op):
    m=re.fullmatch(r'([^()]*)\(\s*(%[A-Za-z0-9]*)?\s*(?:,\s*(%[A-Za-z0-9]+)\s*(?:,\s*(\d+)\s*)?)?\)',op)
    if not m:return None
    disp,base,index,scale=m.groups()
    terms=[]
    if base:terms.append(base[1:].lower())
    if index:terms.append(index[1:].lower()+('*'+scale if scale and scale!='1' else ''))
    if disp.strip():terms.append(disp.strip())
    if not terms:raise ValueError('Leerer GNU-Speicheroperand')
    return '['+'+'.join(terms).replace('+-','-')+']'


def _att_operand_to_intel(op, mnemonic, role, width):
    op=op.strip()
    indirect=op.startswith('*')
    if indirect:op=op[1:].strip()
    if op.startswith('$'):return op[1:]
    if op.startswith('%'):
        name=op[1:].lower()
        if re.fullmatch(r'st\([0-7]\)', name):
            return 'st'+name[3]
        if not _register_word(name):raise ValueError('Unbekanntes GNU-Register '+op)
        return name
    mem=_att_mem_to_intel(op)
    if mem is None and mnemonic not in _NO_SWAP:
        # In AT&T, only '$expr' is immediate; bare expression = memory.
        # The built-in COFF backend supports symbols and integer addresses.
        if re.fullmatch(r'[A-Za-z_.?$@][\w.$?@]*',op) or re.fullmatch(r'[+-]?(?:0x[0-9A-Fa-f]+|\d+)', op):
            mem='['+op+']'
    if mem is not None:
        return (dict(b='byte',w='word',l='dword',q='qword').get(width,'')+' ptr '+mem).strip() if width else mem
    return op


def _constant_unsigned(text: str, line: int, directive: str, *, limit: int = 65536) -> int:
    try:
        value = int(text.strip(), 0)
    except (ValueError, OverflowError):
        raise ValueError(f"AT&T-Zeile {line}: {directive} erwartet eine numerische Konstante") from None
    if value < 0 or value > limit:
        raise ValueError(
            f"AT&T-Zeile {line}: {directive} verlangt 0..{limit} Elemente"
        )
    return value


def _gnu_fill_directive(name: str, args: str, line: int, section: str) -> str:
    """Lower bounded GNU zero/space/fill to supported internal data directives.

    Never emit unsupported 'times COUNT db 0': the internal PE assembler has
    no NASM TIMES directive. Keep one logical source line for diagnostics.
    """
    parts = _split_operands(args)
    if name in ('.zero', '.space', '.skip'):
        if not 1 <= len(parts) <= 2:
            raise ValueError(f'AT&T-Zeile {line}: {name} erwartet Anzahl[, Füllbyte]')
        count = _constant_unsigned(parts[0], line, name)
        fill = int(parts[1], 0) if len(parts) == 2 else 0
        if not 0 <= fill <= 255:
            raise ValueError(f'AT&T-Zeile {line}: {name} Füllbyte außerhalb 0..255')
        if section == '.bss' and fill == 0:
            return 'resb ' + str(count)
        if section == '.bss':
            raise ValueError(f'AT&T-Zeile {line}: initialisierte Daten in .bss nicht erlaubt')
        return 'db ' + ', '.join([str(fill)] * count) if count else '; GNU 0 Bytes'
    if name == '.fill':
        if not 1 <= len(parts) <= 3:
            raise ValueError(f'AT&T-Zeile {line}: .fill erwartet Anzahl[, Größe[, Wert]]')
        count = _constant_unsigned(parts[0], line, '.fill')
        unit = _constant_unsigned(parts[1], line, '.fill', limit=8) if len(parts)>1 else 1
        if unit not in (1, 2, 4, 8):
            raise ValueError(f'AT&T-Zeile {line}: .fill unterstützt Größe 1,2,4,8')
        value = int(parts[2], 0) if len(parts)>2 else 0
        if section == '.bss':
            if value: raise ValueError(f'AT&T-Zeile {line}: .fill mit Füllwert in .bss')
            return 'resb ' + str(count*unit)
        directive = {1:'db', 2:'dw', 4:'dd', 8:'dq'}[unit]
        return directive + ' ' + ', '.join([str(value)] * count) if count else '; GNU 0 Bytes'
    raise ValueError(f'Unbekannte GNU-Fülldirektive {name}')


def att_to_intel(source: str) -> str:
    """Translate AT&T source to internal Intel, preserving source line numbers."""
    out=[]
    section='.text'
    intel_mode=False
    for no,raw in enumerate(source.splitlines(keepends=True),1):
        newline='\r\n' if raw.endswith('\r\n') else ('\n' if raw.endswith('\n') else '')
        line=raw.rstrip('\r\n'); stripped=line.strip()
        if not stripped or stripped.startswith(('%include','%define','%undef','%if','%elif','%else','%endif')):
            out.append(raw);continue
        if stripped.startswith(('#',';')):
            out.append('; '+stripped.lstrip('#;')+newline);continue
        if stripped.startswith('.att_syntax'):
            intel_mode=False
            out.append('; AT&T syntax'+newline);continue
        if stripped.startswith('.intel_syntax'):
            intel_mode=True
            out.append('; Intel syntax'+newline);continue
        if intel_mode:
            # GAS explicitly switched to Intel syntax; leave instruction and
            # operand order alone, instead of silently reversing it twice.
            out.append(raw)
            continue
        # GNU # comments (but not quoted strings) => Intel comments.
        quote='';cut=None;i=0
        while i<len(line):
            ch=line[i]
            if quote:
                if ch=='\\' and i+1<len(line):i+=2;continue
                if ch==quote:quote=''
            elif ch in ('"',"'"):quote=ch
            elif ch=='#':cut=i;break
            i+=1
        comment='' if cut is None else ' ;'+line[cut+1:]
        code=line if cut is None else line[:cut]
        if not code.strip():out.append(comment+newline);continue
        m=re.match(r'^(\s*[.$?@A-Za-z_][\w.$?@]*:)(.*)$',code)
        if m and not m.group(2).strip():out.append(m.group(1)+comment+newline);continue
        statement=re.match(r'^(\s*)([A-Za-z_.][\w.]*)((?:\s+.*)?)$',code)
        if not statement:
            raise ValueError(f'AT&T-Zeile {no}: nicht unterstützte Syntax: {stripped}')
        indent,mnemonic,rawarg=statement.groups();name=mnemonic.casefold();arg=rawarg.strip()
        if name in ('.text','.data','.bss','.rodata','.rdata') and not arg:
            section = '.data' if name in ('.rodata','.rdata') else name
            out.append('section '+section+comment+newline);continue
        if name=='.section':
            section=arg.split(',',1)[0].strip().strip('"')
            # Backward compatibility with Stage 480's accidental '$.text'.
            if section.startswith('$') and section[1:] in ('.text', '.data', '.bss', '.rodata', '.rdata'):
                section=section[1:]
            if section in ('.rodata', '.rdata'):
                section = '.data'  # Internal COFF backend has only text/data/bss.
            if section not in ('.text','.data','.bss'):
                raise ValueError(f'AT&T-Zeile {no}: COFF-Sektion nicht unterstützt: {section}')
            out.append('section '+section+comment+newline);continue
        if name in _DIRECTIVES_ATT_TO_INTEL:
            out.append(indent+_DIRECTIVES_ATT_TO_INTEL[name]+(' '+arg if arg else '')+comment+newline);continue
        # A .extern.inc emitted by Stage 470 can contain private COFF import
        # metadata. It is not a GNU instruction and must not be reversed.
        if name in ('import','export','dllname','entry','bits','section',
                    'resb','resw','resd','resq','db','dw','dd','dq','global','extern','align'):
            out.append(code+comment+newline);continue
        if name in ('.d64_cpu','.d64_model','.d64_public','.d64_times'):
            out.append(indent+name[5:]+(' '+arg if arg else '')+comment+newline);continue
        if name in ('.code32','.code64'):
            out.append('bits '+('64' if name=='.code64' else '32')+comment+newline);continue
        if name in ('.p2align',):
            try:
                power=int(arg.split(',')[0],0)
                if power<0 or power>30:raise ValueError
            except ValueError:
                raise ValueError(f'AT&T-Zeile {no}: .p2align benoetigt einen konstanten Exponenten') from None
            out.append(indent+'align '+str(1<<power)+comment+newline);continue
        if name in ('.zero','.space','.skip','.fill'):
            converted = _gnu_fill_directive(name, arg, no, section)
            out.append(indent + converted + comment + newline)
            continue
        if name in ('.asciz','.string','.ascii'):
            extra=', 0' if name!='.ascii' else ''
            out.append(indent+'db '+arg+extra+comment+newline);continue
        if name in ('.file','.ident','.type','.size','.def','.scl','.endef') or name.startswith('.cfi_'):
            # Metadata discarded intentionally; cannot change generated machine code.
            out.append('; GNU metadata: '+code.strip()+newline);continue
        if name.startswith('.'):
            raise ValueError(f'AT&T-Zeile {no}: GNU-Direktive {name} wird vom internen COFF-Assembler nicht unterstützt')
        # GNU toolchains emit these aliases in both x86 and AMD64 listings.
        # Normalize only those implemented by the internal COFF backend.
        if name in ('retq','retl','leaveq','leavel','nopq','nopl',
                    'callq','calll','jmpq','jmpl','movabsq','movabsl'):
            name = re.sub(r'(?:q|l)$', '', name)
            if name == 'movabs': name = 'mov'
        if name == 'cltd': name = 'cdq'
        if name == 'cqto': name = 'cqo'
        float_width=''
        if name in ('fldl','fstpl','flds','fstps','fildl','fistpl'):
            float_width='q' if name.endswith('l') else 'l'
            name=name[:-1]
        if name in {'movzbl','movzwl','movzbq','movzwq','movsbw','movsbl','movsbq','movswl','movswq','movslq'}:
            if name=='movslq': name='movsxd';width='l'
            else:width=name[4];name='movzx' if name.startswith('movz') else 'movsx'
        else:
            width=''
            if len(name)>2 and name[-1] in 'bwlq' and name[:-1] in _SUFFIXABLE:
                width=name[-1];name=name[:-1]
        args=_split_operands(arg) if arg else []
        if len(args)>3:raise ValueError(f'AT&T-Zeile {no}: zu viele Operanden: {mnemonic}')
        if len(args)==3 and name=='imul':
            raise ValueError(f'AT&T-Zeile {no}: Drei-Operand-IMUL benötigt eine noch nicht unterstützte Backend-Erweiterung')
        if len(args)==2 and name not in _NO_SWAP:
            args=[_att_operand_to_intel(args[1],name,1,width),_att_operand_to_intel(args[0],name,0,width)]
        elif len(args)==3 and name=='imul':
            args=[_att_operand_to_intel(args[2],name,2,width),_att_operand_to_intel(args[1],name,1,width),_att_operand_to_intel(args[0],name,0,width)]
        else:
            args=[_att_operand_to_intel(x,name,i,width) for i,x in enumerate(args)]
        # GNU operand size provides memory width.  Omit redundant prefixes
        # where the destination register determines width, but keep byte/word
        # memory widths for widening MOVZX and memory-only operations.
        if float_width and len(args)==1 and '[' in args[0] and ' ptr ' not in args[0]:
            args[0]=('qword' if float_width=='q' else 'dword')+' ptr '+args[0]
        if name in ('movzx','movsx') and len(args)==2:
            if args[1].startswith(('byte ptr','word ptr')):pass
            elif '[' in args[1]:args[1]='byte ptr '+args[1]
        if name in ('call','jmp') and args and args[0].startswith('*'):
            args[0]=args[0][1:]
        out.append(indent+name+(' '+', '.join(args) if args else '')+comment+newline)
    return ''.join(out)
