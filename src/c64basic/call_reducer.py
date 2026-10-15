"""Stage 420: konservativer Dead-Code-Reducer fuer generierten MOS6510-Runtimecode.

Es werden ausschliesslich Instruktionen im vom Compiler bezeichneten Runtime-
Bereich entfernt. BASIC-Programmtext, Konstanten, Sprite-/Screen-Ressourcen und
CBSS bleiben adressstabil relativ zu ihren eigenen Layout-Regeln. Kontrollfluss
wird ueber JSR/JMP/bedingte Spruenge plus Fallthrough verfolgt. Unbekannte
Maschinenanweisungen werden nicht als Endpunkt betrachtet (konservativ).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import re
from typing import Sequence

_LABEL = re.compile(r'^\s*([A-Za-z_][\w]*):(?:\s*(.*))?$')
_SYMBOL = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', re.IGNORECASE)
_BRANCH = {'bcc', 'bcs', 'beq', 'bmi', 'bne', 'bpl', 'bvc', 'bvs', 'bra'}
_EXIT = {'rts', 'rti', 'brk'}


@dataclass(frozen=True)
class CallReduction:
    lines: tuple[str, ...]
    removed_instructions: int
    removed_labels: int
    skipped: bool = False


def reduce_runtime_calls(source: Sequence[str], start: int, end: int) -> CallReduction:
    """Entfernt nicht erreichbaren ASM-Runtimecode zwischen [start, end).

    Sicherheitsregeln:
    - Die Region muss Runtime-only sein; unbekannte Direktiven oder dynamische
      Codezeiger in .word/.byte fuehren zum unveraenderten Original.
    - Referenzen auf Runtime-Labels ausserhalb werden als Wurzeln betrachtet.
    - Jeder benutzte nicht-Kontrollfluss-Symboloperand im erreichbaren Code wird
      als Adresse genommen und vorsichtshalber ebenfalls als Wurzel behandelt.
    """
    original = list(source)
    if not 0 <= start < end <= len(original):
        return CallReduction(tuple(original), 0, 0, True)
    region = original[start:end]
    label_to_idx: dict[str, int] = {}
    parsed: list[str] = []
    for i, line in enumerate(region):
        code = line.split(';', 1)[0].strip()
        match = _LABEL.match(code)
        if match:
            label = match.group(1).lower()
            if label in label_to_idx:
                return CallReduction(tuple(original), 0, 0, True)
            label_to_idx[label] = i
            code = (match.group(2) or '').strip()
        if code.startswith('.') and not code.lower().startswith(('.byte', '.word')):
            return CallReduction(tuple(original), 0, 0, True)
        if '=' in code and not code.startswith(('#', 'lda ', 'ldx ', 'ldy ')):
            # Falls in Zukunft ein komplexes ASM-Konstrukt dazukommt,
            # keinen aggressiven automatischen Reducer anwenden.
            return CallReduction(tuple(original), 0, 0, True)
        parsed.append(code)
    if not label_to_idx:
        return CallReduction(tuple(original), 0, 0, True)

    # ASM mit .byte oder .word innerhalb der Runtime koennte inline Code oder
    # adressierte Daten enthalten, deren Reachability nicht aus JSR folgt.
    if any(c.lower().startswith(('.byte', '.word')) for c in parsed):
        return CallReduction(tuple(original), 0, 0, True)

    roots: set[int] = set()
    for line in original[:start] + original[end:]:
        stripped = line.split(';', 1)[0].strip()
        match = _LABEL.match(stripped)
        if match:
            stripped = (match.group(2) or '').strip()
        for ref in _SYMBOL.findall(stripped):
            target = label_to_idx.get(ref.lower())
            if target is not None:
                roots.add(target)

    visited: set[int] = set()
    pending = deque(roots)
    while pending:
        i = pending.popleft()
        if i in visited or not 0 <= i < len(region):
            continue
        visited.add(i)
        code = parsed[i]
        if not code:
            pending.append(i+1)
            continue
        parts = code.split(None, 1)
        opcode = parts[0].lower()
        operand = parts[1].strip() if len(parts) == 2 else ''
        refs = _SYMBOL.findall(operand)
        if opcode in _BRANCH or opcode in {'jmp', 'jsr'}:
            if refs:
                target = label_to_idx.get(refs[0].lower())
                if target is not None:
                    pending.append(target)
            if opcode in _BRANCH - {'bra'} or opcode == 'jsr':
                pending.append(i+1)
            elif opcode == 'bra' or opcode == 'jmp':
                pass
        else:
            # Referenz auf Code-Symbol ausserhalb eines Sprungbefehls kann
            # ein indirekter Aufruf oder ein selbstmodifizierender Operand sein.
            for ref in refs:
                target = label_to_idx.get(ref.lower())
                if target is not None:
                    pending.append(target)
            if opcode not in _EXIT:
                pending.append(i+1)

    # Nur entfernte Instruktionen und Labels wegwerfen; blank/comment-Zeilen
    # aus nicht erreichbaren Bloecken ebenfalls entfernen, damit die ASM-Datei
    # ohne verwaiste Ueberschriften lesbar bleibt.
    kept = [region[i] for i in range(len(region)) if i in visited]
    removed_instructions = sum(bool(c and not _LABEL.match(region[i].split(';', 1)[0].strip()))
                               for i, c in enumerate(parsed) if i not in visited)
    removed_labels = sum(1 for name, i in label_to_idx.items() if i not in visited)
    return CallReduction(tuple(original[:start] + kept + original[end:]),
                         removed_instructions, removed_labels)
