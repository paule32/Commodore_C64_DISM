"""Beschreibungen für erkannte x86-Funktionsprologe und -epiloge.

Diese Logik ist bewusst unabhängig von Qt und vom Compiler: Der ASM-Editor
bietet die Erklärung nur für tatsächlich benachbarte Befehlsfolgen an.
"""

from dataclasses import dataclass
import re
from typing import Optional, Sequence


@dataclass(frozen=True)
class StackFrameTooltip:
    """Kontext zur Anzeige im vorhandenen ASM-Hilfefenster."""

    title: str
    instructions: str
    description: str


# Ein optionales Label vor dem Befehl und abschließende Semikolon-Kommentare
# werden toleriert. Kommentarzeilen und beliebige Textfragmente zählen nicht.
_INSTRUCTION = re.compile(
    r"^\s*(?:[A-Za-z_.$][A-Za-z0-9_.$]*\s*:\s*)?"
    r"(?P<mnemonic>push|pop|mov)\s+"
    r"(?P<operands>[A-Za-z]+(?:\s*,\s*[A-Za-z]+)?)\s*$",
    re.IGNORECASE,
)


def _decode_instruction(line: str):
    code = str(line).split(";", 1)[0].strip()
    match = _INSTRUCTION.fullmatch(code)
    if match is None:
        return None
    mnemonic = match.group("mnemonic").casefold()
    operands = tuple(
        part.strip().casefold() for part in match.group("operands").split(",")
    )
    return mnemonic, operands


# Reservierung eines lokalen Stackbereichs nach dem klassischen Funktionsprolog.
# Nur unmittelbare positive Byteanzahlen sind erlaubt; Register-/Symboloperanden
# und Text in Kommentaren dürfen keinen Kontext-Tipp auslösen.
_STACK_RESERVE = re.compile(
    r"^\s*(?:[A-Za-z_.$][A-Za-z0-9_.$]*\s*:\s*)?"
    r"sub\s+(?P<stack>esp|rsp)\s*,\s*(?P<size>0[xX][0-9a-fA-F]+|[0-9]+)\s*$",
    re.IGNORECASE,
)


def stack_frame_allocation_tooltip(
    first: str, second: str, third: str, target: str = "pe32"
) -> Optional[StackFrameTooltip]:
    """Erklärt SUB ESP/RSP, N nur nach passendem PUSH/MOV-Funktionsprolog."""
    target = str(target).casefold()
    if target not in ("pe32", "pe64"):
        return None
    bp, sp, slot = (("ebp", "esp", 4) if target == "pe32"
                    else ("rbp", "rsp", 8))
    if (_decode_instruction(first) != ("push", (bp,))
            or _decode_instruction(second) != ("mov", (bp, sp))):
        return None
    code = str(third).split(";", 1)[0].strip()
    match = _STACK_RESERVE.fullmatch(code)
    if match is None or match.group("stack").casefold() != sp:
        return None
    raw_size = match.group("size")
    amount = int(raw_size, 16 if raw_size.lower().startswith("0x") else 10)
    if amount <= 0:
        return None

    if amount == slot:
        usage = (
            f"Damit entsteht Platz für einen lokalen {slot * 8}-Bit-Wert "
            f"(z. B. eine Variable). Er kann anschließend etwa über "
            f"[{bp}-{amount}] beschrieben werden."
        )
    else:
        usage = (
            f"Der reservierte Bereich kann lokale Variablen und temporäre "
            f"Werte aufnehmen (insgesamt {amount} Byte)."
        )
    return StackFrameTooltip(
        title="Funktionsprolog – lokalen Stack-Speicher reservieren",
        instructions=(
            f"PUSH {bp.upper()}  /  MOV {bp.upper()}, {sp.upper()}"
            f"  /  SUB {sp.upper()}, {amount}"
        ),
        description=(
            f"push {bp}: Sichert den bisherigen Frame-Pointer auf dem Stack; "
            f"{sp.upper()} sinkt um {slot} Byte.\n"
            f"mov {bp}, {sp}: Legt den Frame-Pointer für den neuen "
            f"Funktions-Stackframe fest.\n"
            f"sub {sp}, {amount}: Verringert {sp.upper()} um {amount} Byte "
            "und reserviert dadurch zusätzlichen Platz auf dem nach unten "
            "wachsenden Stack.\n\n"
            + usage + " Die Reservierung allein speichert oder initialisiert "
            "noch keinen Variablenwert.\n\n"
            f"Zusammen bilden diese drei Befehle den Funktionsprolog: "
            f"Der alte {bp.upper()} wird gesichert, ein neuer Stackframe "
            "eingerichtet und lokaler Speicher bereitgestellt. "
            "Die Reservierung wird beim Funktionsepilog, etwa mit "
            f"'mov {sp}, {bp}' und 'pop {bp}', wieder freigegeben."
        ),
    )


def stack_frame_pair_tooltip(
    first: str, second: str, target: str = "pe32"
) -> Optional[StackFrameTooltip]:
    """Erkennt nur zusammengehörige aufeinanderfolgende Prolog/Epilog-Paare.

    Leer-/Kommentarzeilen zwischen den beiden Befehlen werden vom Editor
    übersprungen; diese Funktion erhält die eigentlichen Befehlszeilen.
    """
    target = str(target).casefold()
    if target not in ("pe32", "pe64"):
        return None
    bp, sp, width = (("ebp", "esp", 4) if target == "pe32"
                     else ("rbp", "rsp", 8))
    a, b = _decode_instruction(first), _decode_instruction(second)

    if a == ("push", (bp,)) and b == ("mov", (bp, sp)):
        return StackFrameTooltip(
            title="Funktionsprolog – Stackframe sichern und einrichten",
            instructions=f"PUSH {bp.upper()}  /  MOV {bp.upper()}, {sp.upper()}",
            description=(
                f"push {bp}: Speichert den bisherigen Frame-Pointer {bp.upper()} "
                f"auf dem Stack; {sp.upper()} wird um {width} Byte verringert.\n"
                f"mov {bp}, {sp}: Übernimmt den aktuellen Stackpointer "
                f"{sp.upper()} als Basis des neuen Stackframes.\n\n"
                "Zusammen sichern diese Befehle den bisherigen Frame-Pointer "
                "und richten den Stackframe der Funktion ein. "
                "Es wird nicht der gesamte Stackinhalt kopiert."
            ),
        )

    if a == ("mov", (sp, bp)) and b == ("pop", (bp,)):
        return StackFrameTooltip(
            title="Funktionsepilog – Stackframe wiederherstellen",
            instructions=f"MOV {sp.upper()}, {bp.upper()}  /  POP {bp.upper()}",
            description=(
                f"mov {sp}, {bp}: Setzt den Stackpointer {sp.upper()} "
                "auf den Beginn des aktuellen Stackframes zurück; "
                "dessen lokale Stack-Reservierungen werden freigegeben.\n"
                f"pop {bp}: Lädt den vorher gesicherten Frame-Pointer "
                f"vom Stack zurück nach {bp.upper()}; "
                f"{sp.upper()} wird um {width} Byte erhöht.\n\n"
                f"Gemeinsam stellen diese Befehle den Stackframe-Zustand wieder her, "
                f"der zuvor mit 'push {bp}' und 'mov {bp}, {sp}' "
                "gesichert und eingerichtet wurde. "
                "Dabei wird nicht der gesamte Stackinhalt wiederhergestellt."
            ),
        )

    return None


# Stage 589: lokale Stack-Slots und wiederhergestellte Register. Die
# negativen EBP-Offsets sind KEINE Funktionsparameter. Bei klassischem
# 32-Bit-cdecl beginnen die Argumente oberhalb von EBP (ab [EBP+8]).
_DWORD_EBP_STORE = re.compile(
    r"^\s*mov\s+dword\s+ptr\s*\[\s*ebp\s*-\s*(?P<offset>\d+)\s*\]"
    r"\s*,\s*(?P<register>e(?:ax|bx|cx|dx|si|di))\s*$",
    re.IGNORECASE,
)
_SAVED_REGISTER_RESTORE = re.compile(
    r"^\s*mov\s+(?P<register>ebx|esi|edi)\s*,\s*dword\s+ptr"
    r"\s*\[\s*ebp\s*-\s*(?P<offset>\d+)\s*\]\s*$",
    re.IGNORECASE,
)
_STACK_SUBTRACT = re.compile(
    r"^\s*sub\s+esp\s*,\s*(?P<size>0[xX][0-9a-fA-F]+|\d+)\s*$",
    re.IGNORECASE,
)
_STACK_BARRIER = re.compile(r"^\s*(?:ret(?:n|f)?\b|leave\b|endp\b)", re.I)


def _stack_code(line: str) -> str:
    """Ausschließlich ausführbaren Befehlsteil verwenden."""
    code = str(line).split(";", 1)[0].strip()
    # Label vor einer Anweisung, nicht ein einzelnes Label
    return re.sub(r"^[A-Za-z_.$][A-Za-z0-9_.$]*\s*:\s*(?=\S)", "", code)


def _stack_nonempty(lines: Sequence[str]):
    result = []
    for i, line in enumerate(lines):
        code = _stack_code(line)
        if code and not code.endswith(":"):
            result.append((i, code))
    return result


def _local_frame_allocation(code_lines, prolog_index: int):
    """Anfängliche lokale Reservierung vor dem eigentlichen Funktionskörper."""
    # Entscheidend: die SUB-Anweisung steht nach PUSH EBP / MOV EBP, ESP.
    # Ein Stack-Cookie kann in diesem lokalen Slot liegen.
    for _, code in code_lines[prolog_index + 2:prolog_index + 7]:
        match = _STACK_SUBTRACT.fullmatch(code)
        if match:
            amount = int(match.group('size'), 0) if match.group('size').lower().startswith('0x') else int(match.group('size'))
            return amount if amount > 0 and amount % 4 == 0 else 0
        if re.match(r"(?:push|pop|call|ret|leave|jmp|mov\s+esp)\b", code, re.I):
            break
    return 0


def stack_frame_memory_tooltip(
    lines: Sequence[str], hover_index: int, target: str = 'pe32'
) -> Optional[StackFrameTooltip]:
    """Erklärt EBP-Schreibzugriffe und Wiederherstellung gesicherter Register.

    Die Funktion wird ausschließlich auf den aktuellen PE32-Assembler-Text
    angewendet. Aussagen zu gesicherten Registern erfolgen nur nach Erkennung
    von PUSH EBX/ESI/EDI an den dazugehörigen Stackpositionen.
    """
    if str(target).casefold() != 'pe32' or not 0 <= hover_index < len(lines):
        return None

    entries = _stack_nonempty(lines)
    indexed = {raw_index: item_index for item_index, (raw_index, _) in enumerate(entries)}
    if hover_index not in indexed:
        return None
    current = indexed[hover_index]
    instruction = entries[current][1]
    store = _DWORD_EBP_STORE.fullmatch(instruction)
    restore = _SAVED_REGISTER_RESTORE.fullmatch(instruction)
    if store is None and restore is None:
        return None

    # Letzten passenden Prolog verwenden; nicht über das Ende einer anderen
    # Funktion hinaus interpretieren. Unterschiedliche Labels innerhalb einer
    # Funktion sind erlaubt.
    prolog_index = None
    for pos in range(current - 1, -1, -1):
        if (_decode_instruction(entries[pos][1]) == ('push', ('ebp',))
                and _decode_instruction(entries[pos + 1][1]) == ('mov', ('ebp', 'esp'))):
            prolog_index = pos
            break
        if _STACK_BARRIER.match(entries[pos][1]):
            return None
    if prolog_index is None:
        return None

    local_bytes = _local_frame_allocation(entries, prolog_index)
    if store is not None:
        offset = int(store.group('offset'))
        reg = store.group('register').upper()
        if offset != 4 or local_bytes < 4:
            return None
        return StackFrameTooltip(
            title='Stackframe – ersten lokalen 32-Bit-Slot beschreiben',
            instructions=f'MOV DWORD PTR [EBP-4], {reg}',
            description=(
                f'mov dword ptr [ebp-4], {reg.lower()}: Kopiert den '
                f'32-Bit-Wert aus {reg} an die Speicheradresse EBP-4. '
                'Hier liegen die ersten vier Bytes des im Funktionsprolog '
                'reservierten lokalen Stackbereichs (etwa eine lokale '
                'Variable, ein temporärer Wert oder ein Stack-Cookie).\n\n'
                'Die Anweisung schreibt den Wert wirklich in den Speicher; '
                'SUB ESP, 4 hatte zuvor lediglich Platz dafür reserviert.\n\n'
                'Wichtig: [EBP-4] ist kein erster Funktionsparameter. '
                'Bei der üblichen 32-Bit-Aufrufkonvention beginnt der '
                'erste Stackparameter bei [EBP+8] (nach gespeichertem EBP '
                'und Rücksprungadresse).'
            ),
        )

    # Für die drei MOVs die tatsächliche SAVE-Triplettfolge im Prolog
    # verlangen. Ein beliebiger Zugriff auf [EBP-8] darf niemals als
    # Rückladen von EBX fehlinterpretiert werden.
    saved = (('push', ('ebx',)), ('push', ('esi',)), ('push', ('edi',)))
    saved_at = None
    for i in range(prolog_index + 2, min(current - 2, prolog_index + 40)):
        if tuple(_decode_instruction(code) for _, code in entries[i:i+3]) == saved:
            saved_at = i
            break
    if saved_at is None:
        return None

    # Die EBP-Offsets aus der TATSÄCHLICHEN Stackhöhe ableiten: Ein
    # zusätzliches PUSH oder SUB vor dem Register-Sichern ändert die Slots.
    # CALL selbst ist bei der Rückkehr stackneutral; dynamische Änderungen
    # an ESP werden nicht als sicher klassifiziert.
    depth = 0
    for _, code in entries[prolog_index + 2:saved_at]:
        push = re.fullmatch(r'push\s+.+', code, re.I)
        pop = re.fullmatch(r'pop\s+.+', code, re.I)
        delta = re.fullmatch(
            r'(sub|add)\s+esp\s*,\s*(0[xX][0-9a-fA-F]+|\d+)', code, re.I
        )
        if push:
            depth += 4
        elif pop:
            depth -= 4
        elif delta:
            amount = int(delta.group(2), 16 if delta.group(2).lower().startswith('0x') else 10)
            depth += amount if delta.group(1).lower() == 'sub' else -amount
        elif re.match(r'(?:mov|lea|and|xor|xchg)\s+esp\b', code, re.I):
            return None
        if depth < 0:
            return None

    wanted = (('ebx', depth + 4), ('esi', depth + 8), ('edi', depth + 12))

    # Das MOV-Triplett liegt in der Reihenfolge EBX, ESI, EDI; jedes
    # einzelne Mnemonic erhält denselben inhaltlichen Kontext-Tipp.
    for start in range(max(prolog_index + 2, current - 2), current + 1):
        if start + 2 >= len(entries) or not start <= current <= start + 2:
            continue
        triple = entries[start:start+3]
        parsed = [_SAVED_REGISTER_RESTORE.fullmatch(code) for _, code in triple]
        if all(parsed) and tuple((m.group('register').casefold(), int(m.group('offset'))) for m in parsed) == wanted:
            slot1, slot2, slot3 = (offset for _, offset in wanted)
            return StackFrameTooltip(
                title='Funktionsausgang – gesicherte Register wiederherstellen',
                instructions=(
                    f'MOV EBX, DWORD PTR [EBP-{slot1}]  /  '
                    f'MOV ESI, DWORD PTR [EBP-{slot2}]  /  '
                    f'MOV EDI, DWORD PTR [EBP-{slot3}]'
                ),
                description=(
                    f'mov ebx, dword ptr [ebp-{slot1}]: Lädt den ursprünglich '
                    'mit PUSH EBX gesicherten EBX-Wert zurück.\n'
                    f'mov esi, dword ptr [ebp-{slot2}]: Lädt den ursprünglich '
                    'mit PUSH ESI gesicherten ESI-Wert zurück.\n'
                    f'mov edi, dword ptr [ebp-{slot3}]: Lädt den ursprünglich '
                    'mit PUSH EDI gesicherten EDI-Wert zurück.\n\n'
                    'Die Stackplätze folgen auf die lokale Reservierung. '
                    'EBX, ESI und EDI müssen in der üblichen x86-Aufrufkonvention '
                    'über den Funktionsaufruf hinweg erhalten bleiben.\n\n'
                    'Diese Speicherstellen sind keine zweiten, dritten oder '
                    'vierten Funktionsparameter. Parameter beginnen bei '
                    '[EBP+8], [EBP+12], [EBP+16] usw.; negative EBP-Offsets '
                    'gehören hier zum lokalen Stackframe.'
                ),
            )
    return None


# Stage 590: Schreiben in ESP-relative 32-Bit-Stackplätze. Anders als
# PUSH wird bei MOV der Stackpointer NICHT verändert. Diese Speicherstellen
# können lokale Sicherungsslots, temporäre Daten oder zuvor reservierte
# Argument-Slots sein. Ihre Bedeutung hängt vom umgebenden Code ab.
_ESP_DWORD_STORE = re.compile(
    r"^mov\s+dword\s+ptr\s*\[\s*esp\s*(?:\+\s*(?P<offset>0[xX][0-9a-fA-F]+|\d+))?\s*\]"
    r"\s*,\s*(?P<reg>eax|ebx|ecx|edx|esi|edi|ebp|esp)\s*$",
    re.IGNORECASE,
)
_ESP_REGISTER_SAVE_SEQUENCE = ((0, 'ebx'), (4, 'esi'), (8, 'edi'),
                               (12, 'ebp'), (16, 'esp'))


def _esp_store_match(line: str):
    match = _ESP_DWORD_STORE.fullmatch(_stack_code(line))
    if match is None:
        return None
    raw = match.group('offset') or '0'
    offset = int(raw, 16 if raw.lower().startswith('0x') else 10)
    return offset, match.group('reg').casefold()


def esp_stack_slot_tooltip(
    lines: Sequence[str], hover_index: int, target: str = 'pe32'
) -> Optional[StackFrameTooltip]:
    """MOV [ESP+offset],reg: einzeln oder als zusammengehörige 5er-Folge.

    Ermittelt ausschließlich den Speichereffekt und behauptet nicht, dass
    der reservierte Bereich Parameter oder lokale Variablen sein müsse.
    """
    if str(target).casefold() != 'pe32' or not 0 <= hover_index < len(lines):
        return None
    parsed = _esp_store_match(lines[hover_index])
    if parsed is None:
        return None
    offset, reg = parsed
    entries = _stack_nonempty(lines)
    positions = {raw: idx for idx, (raw, _) in enumerate(entries)}
    active = positions.get(hover_index)
    if active is None:
        return None
    sequence = None
    for start in range(max(0, active - 4), min(active + 1, len(entries) - 4)):
        matches = tuple(_esp_store_match(code) for _, code in entries[start:start + 5])
        if matches == _ESP_REGISTER_SAVE_SEQUENCE:
            sequence = True
            break

    dest = f'[ESP+{offset}]'
    text = (
        f'mov dword ptr [esp+{offset}], {reg}: Schreibt den aktuellen '
        f'32-Bit-Inhalt von {reg.upper()} in den vier Byte breiten '
        f'Stack-Speicherplatz {dest}. '
        'Der Registerwert wird kopiert, nicht aus dem Register entfernt. '
        'ESP bleibt durch MOV unverändert.\n\n'
        f'Der Speicherbereich {dest} bis [ESP+{offset + 3}] muss vorher '
        'gültig bereitgestellt sein, beispielsweise durch SUB ESP, 20. '
        'Ohne entsprechenden Kontext lässt sich nicht entscheiden, ob '
        'dieser Platz für lokale Daten, Registersicherungen oder '
        'vorbereitete Aufrufargumente dient.'
    )
    if reg == 'esp':
        text += ('\n\nSpezialfall ESP: Es wird der aktuelle numerische '
                 'Wert des Stackpointers gespeichert, NICHT der gesamte '
                 'Stackinhalt. Die Schreiboperation selbst ändert ESP nicht.')

    if sequence:
        seq_text = ('\n'.join(
            f'mov dword ptr [esp+{off}], {name}: Speichert {name.upper()} '
            f'in den {off // 4 + 1}. 32-Bit-Slot.'
            for off, name in _ESP_REGISTER_SAVE_SEQUENCE
        ))
        return StackFrameTooltip(
            title='Register auf dem Stack sichern – fünf 32-Bit-Slots',
            instructions='MOV [ESP+0/4/8/12/16], EBX/ESI/EDI/EBP/ESP',
            description=(
                seq_text + '\n\n'
                'Die fünf Befehle schreiben zusammen 20 Byte in fünf '
                'aufeinanderfolgende, bereits verfügbare 32-Bit-Speicherplätze. '
                'Sie führen kein PUSH aus und verringern ESP nicht. '
                'Bei [ESP+16] wird der augenblickliche ESP-Wert abgelegt, '
                'nicht eine Kopie des Stacks.\n\n'
                'Diese Slots sind nicht automatisch die fünf Pascal-Parameter: '
                'Ihre Zuordnung hängt vom Funktionsprolog und von vorherigen '
                'Stackreservierungen ab.\n\n'
                'Aktueller Befehl: ' + text
            ),
        )
    return StackFrameTooltip(
        title='ESP-relativer Stack-Speicherzugriff – 32 Bit ablegen',
        instructions=f'MOV DWORD PTR {dest}, {reg.upper()}',
        description=text,
    )
