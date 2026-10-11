#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""speechConvert.py – WAV-Stille entfernen, IMA-ADPCM erzeugen, Sprachcontainer verwalten.

Einzeldatei:
  python speechConvert.py du.wav -s --keep-ms 5 -ow du_adpcm.wav
  python speechConvert.py du.wav -s -oc deutsch.spc -a DU
  python speechConvert.py -oc deutsch.spc -d DU
  python speechConvert.py -oc deutsch.spc --list
  python speechConvert.py @stapel.txt -oc deutsch.spc
  python speechConvert.py -m deutsch.spc englisch.spc --verify
  python speechConvert.py --text "Hello!" -l en_US -ow hello.wav
  python speechConvert.py --text "Guten Morgen" --piper-backend python -l de_DE -ow morgen.wav
  python speechConvert.py -oc deutsch.spc --test GUTENMORGEN
  python speechConvert.py du.wav -c mp3 --vlc "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"

Batchzeilen (relative Pfade beziehen sich auf den Batchdatei-Ordner):
  "du.wav" S A
  "nicht_mehr.wav" D
  "hallo welt.wav" A

A = zum Container hinzufuegen/ersetzen, D = Eintrag entfernen,
S = Endstille entfernen. Ohne S bleibt die Laenge unveraendert.

Der SPC1-Container verwendet einen indexierten Payload-Bereich (optional gzip je Eintrag);
die einzelnen Payloads sind WAV PCM, WAV IMA-ADPCM, MP3 oder Ogg/Vorbis.
IMA-ADPCM ist der Standard und wird ohne VLC nativ kodiert.

WAV-Konvertierung akzeptiert PCM-WAV-Dateien (8/16/24/32 Bit).
Mit --text wird stattdessen Piper verwendet; --lang waehlt das ONNX-Modell.
Bei IMA-ADPCM werden Mehrkanal-Eingaben automatisch zu Mono gemischt.
"""

from __future__ import annotations

import argparse
import gzip
import json
import io
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import wave
import zlib
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

MAGIC = b"SPCHV1\x00\x00"
VERSION = 1
HEADER = struct.Struct("<8sHHIQQ")  # 32 bytes
ENTRY = struct.Struct("<HBBIQQQI")  # 36 bytes before UTF-8 name
CODECS = {"pcm": 1, "ima-adpcm": 2, "mp3": 3, "ogg": 4}
CODEC_NAMES = {v: k for k, v in CODECS.items()}
CODEC_GZIP_FLAG = 0x80  # Bit 7 of entry codec; low 7 bits are the original codec
EXTENSIONS = {"pcm": ".wav", "ima-adpcm": ".wav", "mp3": ".mp3", "ogg": ".ogg"}
FORMATS = {"adpcm": "ima-adpcm", "ima": "ima-adpcm", "ima-adpcm": "ima-adpcm",
           "pcm": "pcm", "pcm16": "pcm", "pcm-wav": "pcm", "wav": "pcm",
           "mp3": "mp3", "ogg": "ogg", "vorbis": "ogg"}

# IMA/DVI ADPCM step-size and index tables from the published specification.
STEPS = (7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31,
         34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118,
         130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371,
         408, 449, 494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166,
         1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024,
         3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845,
         8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500,
         20350, 22385, 24623, 26846, 32767)
INDEX_DELTA = (-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8)
ADPCM_BLOCK_ALIGN = 256
ADPCM_SAMPLES_PER_BLOCK = (ADPCM_BLOCK_ALIGN - 4) * 2 + 1


class SpeechError(Exception):
    """Verstaendliche CLI-Fehlermeldung."""


@dataclass
class PcmAudio:
    channels: int
    sample_width: int
    rate: int
    frames: int
    data: bytes


@dataclass
class Item:
    name: str
    codec: int
    channels: int
    rate: int
    frames: int
    size: int
    crc: int
    source: Optional[Path] = None  # interim payload file, otherwise existing container
    offset: int = 0


def parse_codec(value: str) -> str:
    normalized = value.lower().replace("_", "-")
    if normalized not in FORMATS:
        raise argparse.ArgumentTypeError("Format: ima-adpcm (Standard), pcm, mp3 oder ogg")
    return FORMATS[normalized]


def checked_name(value: str) -> str:
    name = value.strip()
    raw = name.encode("utf-8")
    if not raw or len(raw) > 255 or any(c in name for c in "/\\\x00\r\n"):
        raise SpeechError(f"Ungültiger Containereintrag: {value!r} (max. 255 UTF-8-Bytes)")
    return name


def load_pcm(path: Path) -> PcmAudio:
    try:
        with wave.open(str(path), "rb") as wav:
            if wav.getcomptype() != "NONE":
                raise SpeechError(f"Nur unkomprimiertes PCM-WAV als Eingabe: {path}")
            channels, width, rate, count = (
                wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes())
            if channels < 1 or channels > 8 or width not in (1, 2, 3, 4) or rate < 1:
                raise SpeechError("PCM-WAV benötigt 1–8 Kanäle und 8/16/24/32 Bit")
            raw = wav.readframes(count)
            if len(raw) != count * channels * width:
                raise SpeechError(f"WAV-Daten unvollständig: {path}")
            return PcmAudio(channels, width, rate, count, raw)
    except (wave.Error, EOFError) as ex:
        raise SpeechError(f"Keine unterstützte PCM-WAV-Datei: {path} ({ex})") from ex
    except OSError as ex:
        raise SpeechError(f"Kann WAV nicht öffnen: {path}: {ex}") from ex


def trim_end(audio: PcmAudio, keep_ms: float) -> tuple[PcmAudio, int]:
    """Nur exakt stille PCM-Frames entfernen; alle erhaltenen Bytes unveraendert."""
    if keep_ms < 0:
        raise SpeechError("--keep-ms darf nicht negativ sein")
    frame_bytes = audio.channels * audio.sample_width
    frame_silence = (b"\x80" if audio.sample_width == 1 else
                     b"\x00" * audio.sample_width) * audio.channels
    last = audio.frames
    raw = audio.data
    while last > 0 and raw[(last - 1) * frame_bytes:last * frame_bytes] == frame_silence:
        last -= 1
    zeros = audio.frames - last
    retained = min(zeros, round(audio.rate * keep_ms / 1000.0))
    result_count = last + retained
    return PcmAudio(audio.channels, audio.sample_width, audio.rate,
                    result_count, raw[:result_count * frame_bytes]), audio.frames - result_count


def pcm_wav_bytes(audio: PcmAudio) -> bytes:
    out = io.BytesIO()
    with wave.open(out, "wb") as wav:
        wav.setnchannels(audio.channels)
        wav.setsampwidth(audio.sample_width)
        wav.setframerate(audio.rate)
        wav.writeframes(audio.data)
    return out.getvalue()


def mono_samples_s16(audio: PcmAudio) -> list[int]:
    """16-bit signed mono; for stereo/multichannel, arithmetic average."""
    result: list[int] = []
    pos = 0
    width = audio.sample_width
    for _ in range(audio.frames):
        total = 0
        for _ in range(audio.channels):
            if width == 1:
                sample = (audio.data[pos] - 128) << 8
            elif width == 2:
                sample = int.from_bytes(audio.data[pos:pos + 2], "little", signed=True)
            elif width == 3:
                sample = int.from_bytes(audio.data[pos:pos + 3], "little", signed=True) >> 8
            else:
                sample = int.from_bytes(audio.data[pos:pos + 4], "little", signed=True) >> 16
            total += sample
            pos += width
        result.append(max(-32768, min(32767, round(total / audio.channels))))
    return result


def _ima_nibble(sample: int, predictor: int, index: int) -> tuple[int, int, int]:
    step = STEPS[index]
    difference = sample - predictor
    code = 8 if difference < 0 else 0
    difference = abs(difference)
    delta = 0
    if difference >= step:
        code |= 4
        difference -= step
    if difference >= step // 2:
        code |= 2
        difference -= step // 2
    if difference >= step // 4:
        code |= 1
    delta = step >> 3
    if code & 4:
        delta += step
    if code & 2:
        delta += step >> 1
    if code & 1:
        delta += step >> 2
    predictor = predictor - delta if code & 8 else predictor + delta
    predictor = max(-32768, min(32767, predictor))
    index = max(0, min(88, index + INDEX_DELTA[code]))
    return code, predictor, index


def ima_adpcm_wav_bytes(audio: PcmAudio) -> bytes:
    """Canonical Microsoft WAVE_FORMAT_DVI_ADPCM (0x0011), 256-byte mono blocks.

    Each block is a 4-byte predictor/index header followed by low-nibble-first
    ADPCM samples. Fact chunk records the exact original sample count.
    """
    samples = mono_samples_s16(audio)
    blocks = bytearray()
    index = 0
    for start in range(0, len(samples), ADPCM_SAMPLES_PER_BLOCK):
        chunk = samples[start:start + ADPCM_SAMPLES_PER_BLOCK]
        predictor = chunk[0]
        block = bytearray(struct.pack("<hBB", predictor, index, 0))
        nibbles = bytearray()
        for sample in chunk[1:]:
            code, predictor, index = _ima_nibble(sample, predictor, index)
            nibbles.append(code)
        # Die letzte Blockhaelfte mit codierter Stille statt Null-Nibbles
        # auffuellen: manche Decoder ignorieren bei ADPCM den fact-Samplecount
        # und spielen den letzten Block sonst mit einem Nachklang ab.
        for _ in range(ADPCM_SAMPLES_PER_BLOCK - len(chunk)):
            code, predictor, index = _ima_nibble(0, predictor, index)
            nibbles.append(code)
        for offset in range(0, len(nibbles), 2):
            lo = nibbles[offset]
            hi = nibbles[offset + 1] if offset + 1 < len(nibbles) else 0
            block.append(lo | (hi << 4))
        if len(block) < ADPCM_BLOCK_ALIGN:
            block.extend(b"\x00" * (ADPCM_BLOCK_ALIGN - len(block)))
        if len(block) != ADPCM_BLOCK_ALIGN:
            raise SpeechError("Interner ADPCM-Blockgrößenfehler")
        blocks.extend(block)
    # fmt chunk: WAVEFORMATEX (18 bytes) + WORD samplesPerBlock (2 bytes)
    average_bytes_sec = max(1, audio.rate * ADPCM_BLOCK_ALIGN // ADPCM_SAMPLES_PER_BLOCK)
    fmt = struct.pack("<HHIIHHHH", 0x0011, 1, audio.rate,
                      average_bytes_sec, ADPCM_BLOCK_ALIGN, 4, 2,
                      ADPCM_SAMPLES_PER_BLOCK)
    fact = struct.pack("<I", audio.frames)
    def chunk(kind: bytes, data: bytes) -> bytes:
        return kind + struct.pack("<I", len(data)) + data + (b"\x00" if len(data) & 1 else b"")
    contents = b"WAVE" + chunk(b"fmt ", fmt) + chunk(b"fact", fact) + chunk(b"data", blocks)
    return b"RIFF" + struct.pack("<I", len(contents)) + contents


def find_vlc(explicit: Optional[str]) -> Path:
    if explicit:
        p = Path(explicit).expanduser()
        if p.is_file():
            return p
        via_path = shutil.which(explicit)
        if via_path:
            return Path(via_path)
        raise SpeechError(f"VLC nicht gefunden: {explicit}")
    candidate = shutil.which("vlc.exe") or shutil.which("vlc")
    if candidate:
        return Path(candidate)
    for env in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(env)
        if base:
            candidate_path = Path(base) / "VideoLAN" / "VLC" / "vlc.exe"
            if candidate_path.is_file():
                return candidate_path
    raise SpeechError("VLC nicht gefunden. Mit --vlc den Pfad zur vlc.exe angeben.")


def vlc_encode(audio: PcmAudio, codec: str, vlc: Optional[str]) -> bytes:
    """VLC used for compressed MP3/Ogg. IMA-ADPCM is encoded internally."""
    vlc_bin = find_vlc(vlc)
    with tempfile.TemporaryDirectory(prefix="speechconvert_vlc_") as td:
        folder = Path(td)
        src = folder / "input.wav"
        dst = folder / ("output.mp3" if codec == "mp3" else "output.ogg")
        src.write_bytes(pcm_wav_bytes(audio))
        if codec == "mp3":
            transcode = "acodec=mp3,ab=48,channels=1,samplerate=16000"
            mux = "raw"
        elif codec == "ogg":
            transcode = "acodec=vorb,ab=48,channels=1,samplerate=16000"
            mux = "ogg"
        else:
            raise SpeechError("VLC-Encoding nur für mp3/ogg vorgesehen")
        sout = f"#transcode{{{transcode}}}:std{{access=file,mux={mux},dst={str(dst)}}}"
        command = [str(vlc_bin), "-I", "dummy", "--no-video", "--play-and-exit",
                   "--sout", sout, str(src), "vlc://quit"]
        try:
            proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=120, check=False)
        except subprocess.TimeoutExpired as exc:
            raise SpeechError("VLC hat das Zeitlimit von 120 Sekunden überschritten") from exc
        if proc.returncode != 0 or not dst.exists() or dst.stat().st_size == 0:
            errors = proc.stderr.decode("utf-8", "replace")[-1000:]
            raise SpeechError(f"VLC-Konvertierung gescheitert (Code {proc.returncode}). {errors}")
        return dst.read_bytes()


def encode(audio: PcmAudio, codec: str, vlc: Optional[str]) -> tuple[bytes, int]:
    if codec == "pcm":
        return pcm_wav_bytes(audio), audio.channels
    if codec == "ima-adpcm":
        return ima_adpcm_wav_bytes(audio), 1
    return vlc_encode(audio, codec, vlc), 1


def _validate_header(file, size: int) -> tuple[int, int, int]:
    if size < HEADER.size:
        raise SpeechError("Container zu kurz oder beschädigt")
    magic, version, flags, count, directory, directory_length = HEADER.unpack(file.read(HEADER.size))
    if magic != MAGIC or version != VERSION or flags != 0:
        raise SpeechError("Ungültiger Container (erwartet SPC1 Version 1)")
    if count > 1_000_000 or directory < HEADER.size or directory > size:
        raise SpeechError("Containerverzeichnis beschädigt")
    if directory_length > size - directory or directory + directory_length != size:
        raise SpeechError("Containerverzeichnis-Länge ungültig")
    return count, directory, directory_length


def read_container(path: Path) -> dict[str, Item]:
    if not path.exists():
        return {}
    items: dict[str, Item] = {}
    with path.open("rb") as file:
        size = path.stat().st_size
        count, directory, length = _validate_header(file, size)
        file.seek(directory)
        read_start = file.tell()
        for _ in range(count):
            packed = file.read(ENTRY.size)
            if len(packed) != ENTRY.size:
                raise SpeechError("Unvollständiger Containereintrag")
            name_len, codec, channels, rate, offset, length_item, frames, crc = ENTRY.unpack(packed)
            if not name_len or name_len > 255 or (codec & 0x7F) not in CODEC_NAMES or channels < 1 or rate < 1:
                raise SpeechError("Ungültiger Containereintrag")
            name_raw = file.read(name_len)
            if len(name_raw) != name_len:
                raise SpeechError("Abgeschnittener Eintragsname")
            try:
                name = checked_name(name_raw.decode("utf-8", "strict"))
            except UnicodeError as ex:
                raise SpeechError("Ungültiger UTF-8-Name") from ex
            if offset < HEADER.size or length_item > directory - offset:
                raise SpeechError(f"Eintrag {name!r} zeigt außerhalb des Datenbereichs")
            key = name.casefold()
            if key in items:
                raise SpeechError(f"Doppelter Containereintrag: {name}")
            items[key] = Item(name, codec, channels, rate, frames, length_item, crc, None, offset)
        if file.tell() - read_start != length:
            raise SpeechError("Containerverzeichnis hat unerwartete Zusatzdaten")
    return items


def _copy_exact(input_file, output_file, length: int) -> int:
    crc = 0
    while length:
        block = input_file.read(min(1024 * 1024, length))
        if not block:
            raise SpeechError("Containerdaten beim Kopieren unvollständig")
        output_file.write(block)
        crc = zlib.crc32(block, crc)
        length -= len(block)
    return crc & 0xffffffff


def write_container(path: Path, items: dict[str, Item]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Optional[Path] = None
    old_file = None
    try:
        if path.exists():
            old_file = path.open("rb")
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix="." + path.name + ".",
                                         suffix=".tmp", delete=False) as out:
            tmp_path = Path(out.name)
            out.write(b"\x00" * HEADER.size)
            updated: list[tuple[Item, int]] = []
            for item in sorted(items.values(), key=lambda r: r.name.casefold()):
                start = out.tell()
                if item.source is not None:
                    with item.source.open("rb") as src:
                        # Quell-SPC: Nutzdaten liegen nicht am Dateianfang.
                        # Bei frisch konvertierten Payload-Dateien ist offset=0.
                        src.seek(item.offset)
                        crc = _copy_exact(src, out, item.size)
                else:
                    if old_file is None:
                        raise SpeechError(f"Fehlende Quelldaten für Eintrag {item.name}")
                    old_file.seek(item.offset)
                    crc = _copy_exact(old_file, out, item.size)
                if crc != item.crc:
                    raise SpeechError(f"CRC-Fehler in Eintrag {item.name}: Container wird nicht geändert")
                updated.append((item, start))
            directory_offset = out.tell()
            for item, start in updated:
                name_raw = item.name.encode("utf-8")
                out.write(ENTRY.pack(len(name_raw), item.codec, item.channels, item.rate,
                                     start, item.size, item.frames, item.crc))
                out.write(name_raw)
            directory_size = out.tell() - directory_offset
            out.seek(0)
            out.write(HEADER.pack(MAGIC, VERSION, 0, len(items), directory_offset, directory_size))
            out.flush()
            os.fsync(out.fileno())
        if old_file:
            old_file.close()
            old_file = None
        os.replace(tmp_path, path)
        tmp_path = None
    finally:
        if old_file:
            old_file.close()
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


def verify_container(path: Path) -> int:
    items = read_container(path)
    with path.open("rb") as file:
        for item in items.values():
            file.seek(item.offset)
            crc = 0
            remaining = item.size
            gzip_decoder = zlib.decompressobj(wbits=31) if item.codec & CODEC_GZIP_FLAG else None
            inflated = 0
            while remaining:
                data = file.read(min(1024 * 1024, remaining))
                if not data:
                    raise SpeechError(f"Eintrag abgeschnitten: {item.name}")
                crc = zlib.crc32(data, crc)
                remaining -= len(data)
                if gzip_decoder is not None:
                    try:
                        block = gzip_decoder.decompress(data, 64 * 1024 * 1024 + 1 - inflated)
                    except zlib.error as exc:
                        raise SpeechError(f"GZIP-Fehler in {item.name}: {exc}") from exc
                    inflated += len(block)
                    if inflated > 64 * 1024 * 1024 or gzip_decoder.unconsumed_tail:
                        raise SpeechError(f"GZIP-Daten überschreiten 64 MiB: {item.name}")
            if (crc & 0xffffffff) != item.crc:
                raise SpeechError(f"CRC-Fehler: {item.name}")
            if gzip_decoder is not None and (not gzip_decoder.eof or gzip_decoder.unused_data):
                raise SpeechError(f"Ungültiger GZIP-Stream: {item.name}")
    return len(items)



# Stage 359: Container entry preview. A stored GZIP payload is CRC-checked,
# decompressed and (if IMA-ADPCM) decoded before Windows playback.
MAX_PREVIEW_PAYLOAD = 64 * 1024 * 1024


def read_sample_payload(path: Path, entry: Item) -> bytes:
    """Read precisely one SPC payload, validate CRC32 and optional gzip stream."""
    with path.open("rb") as source:
        source.seek(entry.offset)
        data = source.read(entry.size)
    if len(data) != entry.size:
        raise SpeechError(f"Audiodaten von {entry.name!r} sind unvollständig")
    if (zlib.crc32(data) & 0xffffffff) != entry.crc:
        raise SpeechError(f"CRC32-Fehler beim Containereintrag {entry.name!r}")
    if not (entry.codec & CODEC_GZIP_FLAG):
        if len(data) > MAX_PREVIEW_PAYLOAD:
            raise SpeechError("Audiodaten überschreiten das 64-MiB-Limit")
        return data
    decoder = zlib.decompressobj(wbits=31)
    try:
        result = decoder.decompress(data, MAX_PREVIEW_PAYLOAD + 1)
    except zlib.error as exc:
        raise SpeechError(f"GZIP-Fehler beim Eintrag {entry.name!r}: {exc}") from exc
    if (len(result) > MAX_PREVIEW_PAYLOAD or decoder.unconsumed_tail or
            not decoder.eof or decoder.unused_data):
        raise SpeechError(f"Ungültige oder zu große GZIP-Daten in {entry.name!r}")
    return result


def _wave_chunks(data: bytes) -> dict[bytes, bytes]:
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise SpeechError("Der SPC-Eintrag enthält keine gültige RIFF-WAV-Datei")
    wav_end = struct.unpack_from("<I", data, 4)[0] + 8
    if wav_end != len(data):
        raise SpeechError("Beschädigte RIFF-Länge im SPC-Eintrag")
    chunks: dict[bytes, bytes] = {}
    at = 12
    while at < wav_end:
        if at + 8 > wav_end:
            raise SpeechError("WAV-Chunk-Kopf ist abgeschnitten")
        kind, length = struct.unpack_from("<4sI", data, at)
        at += 8
        if length > wav_end - at:
            raise SpeechError("WAV-Chunk-Daten sind abgeschnitten")
        chunks.setdefault(kind, data[at:at + length])
        at += length + (length & 1)
    if at != wav_end:
        raise SpeechError("WAV-Chunk ist falsch ausgerichtet")
    return chunks


def decode_ima_adpcm(payload: bytes, entry: Item) -> PcmAudio:
    """Microsoft WAV IMA/DVI-ADPCM, mono, low nibble first, fact frame count."""
    chunks = _wave_chunks(payload)
    fmt = chunks.get(b"fmt ", b"")
    data = chunks.get(b"data")
    fact = chunks.get(b"fact", b"")
    if len(fmt) < 20 or data is None or len(fact) < 4:
        raise SpeechError("IMA-ADPCM-WAV benötigt fmt, fact und data")
    tag, channels, rate, _, alignment, bits = struct.unpack_from("<HHIIHH", fmt)
    per_block = struct.unpack_from("<H", fmt, 18)[0]
    actual_frames = struct.unpack_from("<I", fact)[0]
    if (tag != 0x11 or channels != 1 or entry.channels != 1 or
            rate != entry.rate or rate < 1 or bits != 4 or alignment < 8 or
            per_block != 1 + (alignment - 4) * 2 or
            actual_frames != entry.frames or len(data) % alignment != 0 or
            (len(data) // alignment) * per_block < actual_frames):
        raise SpeechError(f"Ungültige IMA-ADPCM-Formatdaten für {entry.name!r}")
    if actual_frames * 2 > MAX_PREVIEW_PAYLOAD:
        raise SpeechError("Dekodierte WAV-Daten überschreiten 64 MiB")
    output = bytearray()
    produced = 0
    for start in range(0, len(data), alignment):
        block = data[start:start + alignment]
        predictor, step_index, reserved = struct.unpack_from("<hBB", block)
        if step_index > 88 or reserved != 0:
            raise SpeechError(f"Ungültiger ADPCM-Blockkopf in {entry.name!r}")
        if produced < actual_frames:
            output.extend(struct.pack("<h", predictor))
            produced += 1
        for packed in block[4:]:
            for code in (packed & 0x0f, packed >> 4):
                if produced == actual_frames:
                    break
                step = STEPS[step_index]
                difference = (step >> 3)
                if code & 1:
                    difference += step >> 2
                if code & 2:
                    difference += step >> 1
                if code & 4:
                    difference += step
                predictor += -difference if code & 8 else difference
                predictor = max(-32768, min(32767, predictor))
                step_index = max(0, min(88, step_index + INDEX_DELTA[code]))
                output.extend(struct.pack("<h", predictor))
                produced += 1
            if produced == actual_frames:
                break
        if produced == actual_frames:
            break
    if produced != actual_frames:
        raise SpeechError(f"IMA-ADPCM-Dekodierung unvollständig: {entry.name!r}")
    return PcmAudio(1, 2, rate, produced, bytes(output))


def preview_pcm_wav(payload: bytes, entry: Item) -> bytes:
    """Return a standard 16-bit mono WAV for Windows winsound."""
    if (entry.codec & 0x7f) == CODECS["ima-adpcm"]:
        audio = decode_ima_adpcm(payload, entry)
    else:
        try:
            with wave.open(io.BytesIO(payload), "rb") as wav:
                if wav.getcomptype() != "NONE":
                    raise SpeechError("Der PCM-Eintrag enthält keine unkomprimierte WAV-Datei")
                audio = PcmAudio(wav.getnchannels(), wav.getsampwidth(),
                                 wav.getframerate(), wav.getnframes(),
                                 wav.readframes(wav.getnframes()))
        except (wave.Error, EOFError, struct.error) as exc:
            raise SpeechError(f"Ungültige PCM-WAV im Eintrag {entry.name!r}: {exc}") from exc
        if (audio.rate != entry.rate or audio.channels != entry.channels or
                audio.frames != entry.frames or audio.sample_width not in (1, 2, 3, 4)):
            raise SpeechError(f"PCM-WAV-Metadaten stimmen nicht mit {entry.name!r} überein")
        if audio.frames * 2 > MAX_PREVIEW_PAYLOAD:
            raise SpeechError("Dekodierte WAV-Daten überschreiten 64 MiB")
        if audio.channels == 1 and audio.sample_width == 2:
            return payload
        audio = PcmAudio(1, 2, audio.rate, audio.frames,
                         struct.pack("<" + "h" * audio.frames, *mono_samples_s16(audio)))
    return pcm_wav_bytes(audio)


def _play_wav_windows(wav_data: bytes) -> None:
    if sys.platform != "win32":
        raise SpeechError("WAV-Vorschau benötigt Windows; MP3/Ogg können mit VLC abgespielt werden")
    try:
        import winsound
        winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_SYNC)
    except (ImportError, RuntimeError, OSError) as exc:
        raise SpeechError(f"Windows-WAV-Wiedergabe fehlgeschlagen: {exc}") from exc


def _play_vlc_audio(payload: bytes, extension: str, vlc: Optional[str]) -> None:
    vlc_bin = find_vlc(vlc)
    with tempfile.TemporaryDirectory(prefix="speechconvert_preview_") as tmpdir:
        target = Path(tmpdir) / ("sample" + extension)
        target.write_bytes(payload)
        command = [str(vlc_bin), "-I", "dummy", "--no-video", "--play-and-exit",
                   str(target), "vlc://quit"]
        try:
            run = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 timeout=120, check=False)
        except subprocess.TimeoutExpired as exc:
            raise SpeechError("VLC-Wiedergabe nach 120 Sekunden abgebrochen") from exc
        if run.returncode:
            raise SpeechError("VLC-Wiedergabe fehlgeschlagen (Code " + str(run.returncode) +
                              "): " + run.stderr.decode("utf-8", "replace")[-500:])


def test_container_entry(path: Path, name: str, vlc: Optional[str] = None) -> None:
    """Look up, validate, decode and play a single named SPC entry."""
    if not path.is_file():
        raise SpeechError(f"SPC-Container nicht gefunden: {path}")
    items = read_container(path)
    key = checked_name(name).casefold()
    if key not in items:
        raise SpeechError(f"Eintrag {name!r} nicht gefunden in {path} (mit --list anzeigen)")
    entry = items[key]
    payload = read_sample_payload(path, entry)
    codec = entry.codec & 0x7f
    seconds = entry.frames / entry.rate
    print(f"TEST: {entry.name} | {CODEC_NAMES[codec]} | {entry.rate} Hz | {seconds:.2f} s" +
          (" | gzip" if entry.codec & CODEC_GZIP_FLAG else ""), flush=True)
    if codec in (CODECS["pcm"], CODECS["ima-adpcm"]):
        wav_data = preview_pcm_wav(payload, entry)
        _play_wav_windows(wav_data)
    else:
        _play_vlc_audio(payload, EXTENSIONS[CODEC_NAMES[codec]], vlc)
    print("WIEDERGABE BEENDET")

# Offizieller Voice-Katalog (Namen dienen auch als Suchvorschlaege).
# Das Sprachmodell bestimmt die Piper-Sprache; piper.exe besitzt keinen
# unabhaengigen --lang-Schalter fuer ein bereits geladenes ONNX-Modell.
VOICE_CATALOG = {
    "de_DE": ("thorsten-high", "thorsten-medium", "thorsten-low",
              "kerstin-low", "ramona-low", "thorsten_emotional-medium"),
    "en_US": ("amy-medium", "amy-low", "joe-medium", "lessac-medium", "lessac-high"),
}
DEFAULT_VOICE = {"de_DE": ("thorsten", "high"), "en_US": ("amy", "medium")}


def normalize_language(value: str) -> str:
    value = value.replace("-", "_").strip()
    parts = value.split("_")
    if len(parts) != 2 or len(parts[0]) not in (2, 3) or len(parts[1]) != 2:
        raise argparse.ArgumentTypeError("Sprache im Format de_DE oder en_US angeben")
    if not (parts[0].isalpha() and parts[1].isalpha()):
        raise argparse.ArgumentTypeError("Ungültiger Sprachcode")
    return parts[0].lower() + "_" + parts[1].upper()


def list_voice_catalog(lang: Optional[str] = None) -> None:
    languages = (lang,) if lang else tuple(VOICE_CATALOG)
    for code in languages:
        print(code + ":")
        voices = VOICE_CATALOG.get(code, ())
        if not voices:
            print("  Keine vorinstallierte Empfehlung; anderes .onnx-Modell explizit angeben")
        for voice in voices:
            base = f"{code}-{voice}.onnx"
            print(f"  {base}   +   {base}.json")


def piper_model_path(args: argparse.Namespace) -> Path:
    lang = args.lang
    if args.model:
        model = Path(args.model).expanduser().resolve()
        if not model.is_file():
            raise SpeechError(f"Piper-Modell nicht gefunden: {model}")
        if not model.with_name(model.name + ".json").is_file():
            raise SpeechError(f"Piper-Modellkonfiguration fehlt: {model.name}.json")
        if not model.name.lower().startswith(lang.lower() + "-"):
            raise SpeechError(f"Modell {model.name} passt nicht zu --lang {lang}")
        return model
    default_name, default_quality = DEFAULT_VOICE.get(lang, (None, None))
    if args.voice:
        voice = args.voice
    elif default_name:
        voice = default_name
    else:
        raise SpeechError(f"Für {lang} bitte --voice oder --model angeben")
    quality = args.quality or default_quality or "medium"
    basename = f"{lang}-{voice}-{quality}.onnx"
    base = Path(__file__).resolve().parent
    locations = (
        [Path(args.model_dir).expanduser().resolve()] if args.model_dir else
        [base / "speech" / "piper", base / "piper", Path.cwd() / "speech" / "piper", Path.cwd() / "piper"]
    )
    for folder in locations:
        candidate = folder / basename
        if candidate.is_file() and candidate.with_name(candidate.name + ".json").is_file():
            return candidate
    raise SpeechError(
        f"Piper-Stimme nicht gefunden: {basename} (plus .json). "
        "Modelle nach speech/piper legen oder --model-dir/--model verwenden."
    )


def find_piper(executable: Optional[str], model: Path) -> Path:
    if executable:
        path = Path(executable).expanduser()
        if path.is_file():
            return path.resolve()
        found = shutil.which(executable)
        if found:
            return Path(found).resolve()
        raise SpeechError(f"Piper-Programm nicht gefunden: {executable}")
    for candidate in (model.parent / "piper.exe", model.parent / "piper",
                      Path(__file__).resolve().parent / "speech" / "piper" / "piper.exe"):
        if candidate.is_file():
            return candidate.resolve()
    found = shutil.which("piper.exe") or shutil.which("piper")
    if found:
        return Path(found).resolve()
    raise SpeechError("piper.exe nicht gefunden. Mit --piper die ausführbare Datei angeben.")


# Windows NTSTATUS 0xC0000409: Fail Fast. Das ist nicht zwangslaeufig
# ein tatsaechlicher Pufferueberlauf. Bei Piper 1.2.0/Windows wurde der
# Absturz waehrend der ONNX-Modellinitialisierung beobachtet.
PIPER_WINDOWS_FAIL_FAST = 0xC0000409


def _piper_exit_code(returncode: int) -> str:
    """Auch negative, von subprocess gemeldete NTSTATUS-Werte darstellen."""
    return f"{returncode & 0xffffffff} (0x{returncode & 0xffffffff:08X})"


def _piper_python_command(args: argparse.Namespace, model: Path, wav: Path) -> list[str]:
    """Piper-Python-CLI (alte und neue piper-tts-Versionen: stdin, --output_file)."""
    command = args.piper_python or sys.executable
    if not command:
        raise SpeechError("Kein Python-Interpreter fuer Piper gefunden")
    if Path(command).is_file():
        python_bin = str(Path(command).expanduser().resolve())
    else:
        python_bin = shutil.which(command)
        if not python_bin:
            raise SpeechError(f"Python-Interpreter nicht gefunden: {command}")
    return [python_bin, "-m", "piper", "--model", str(model), "--output_file", str(wav)]


def _run_piper(command: list[str], cwd: Path, text: str, wav: Path, label: str) -> PcmAudio:
    try:
        process = subprocess.run(
            command,
            input=(text.rstrip() + "\n").encode("utf-8"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(cwd), timeout=180, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise SpeechError(f"{label} hat das Zeitlimit von 180 Sekunden ueberschritten") from exc
    except OSError as exc:
        raise SpeechError(f"{label} konnte nicht gestartet werden: {exc}") from exc

    if process.returncode == 0 and wav.is_file() and wav.stat().st_size:
        try:
            return load_pcm(wav)
        except (SpeechError, OSError, ValueError, wave.Error) as exc:
            raise SpeechError(f"{label} lieferte keine gueltige PCM-WAV: {exc}") from exc

    outputs = ((process.stderr or b"") + b"\n" + (process.stdout or b"")).decode("utf-8", "replace").strip()
    suffix = f"\nAusgabe: {outputs[-2000:]}" if outputs else "\nPiper gab keine Fehlermeldung aus."
    if (process.returncode & 0xffffffff) == PIPER_WINDOWS_FAIL_FAST:
        suffix += ("\nWindows-Fail-Fast 0xC0000409: Piper/ONNX-Runtime ist abgestuerzt "
                   "(bekannt fuer manche Windows-Versionen mit Piper 1.2.0). "
                   "Nicht durch --gzip oder SPC verursacht.\n"
                   "Pruefung: piper.exe unmittelbar mit --model und --output_file testen. "
                   "Alternative: python -m pip install --upgrade piper-tts und "
                   "speechConvert.py mit --piper-backend python starten.")
    raise SpeechError(f"{label} hat keine WAV-Datei erzeugt (Exit {_piper_exit_code(process.returncode)}).{suffix}")


def synthesize_piper(text: str, args: argparse.Namespace) -> PcmAudio:
    if not text.strip():
        raise SpeechError("--text darf nicht leer sein")
    model = piper_model_path(args)
    backend = getattr(args, "piper_backend", "auto")
    with tempfile.TemporaryDirectory(prefix="speechconvert_piper_") as tmp:
        wav = Path(tmp) / "synth.wav"
        exe_failure = None
        if backend in ("auto", "exe"):
            try:
                program = find_piper(args.piper, model)
                command = [str(program), "--model", str(model), "--output_file", str(wav)]
                return _run_piper(command, program.parent, text, wav, "piper.exe")
            except SpeechError as exc:
                exe_failure = str(exc)
                # Ausschliesslich bei fehlender EXE oder einem bekannten Windows-
                # Fail-Fast-Absturz auf das Python-Paket ausweichen.
                can_fallback = ("nicht gefunden" in exe_failure.lower() or
                                "0xC0000409" in exe_failure)
                if backend == "exe" or not can_fallback:
                    raise
                print("HINWEIS: Piper-EXE nicht verfuegbar oder abgestuerzt; "
                      "versuche Python-Paket piper-tts.", file=sys.stderr)
        # Dem Python-Backend die Dateipfade absolut uebergeben, aber die
        # Piper-Arbeitsumgebung vom Modellordner aus starten.
        wav.unlink(missing_ok=True)
        command = _piper_python_command(args, model, wav)
        try:
            return _run_piper(command, model.parent, text, wav, "Piper-Python")
        except SpeechError as exc:
            details = str(exc)
            if "No module named piper" in details:
                details += ("\nInstallation des Python-Backends: "
                            "python -m pip install --upgrade piper-tts")
            if exe_failure:
                details = ("EXE-Versuch: " + exe_failure + "\n"
                           "Python-Fallback: " + details)
            raise SpeechError(details) from exc


def merge_containers(first: Path, second: Path, output: Path, conflict: str) -> tuple[int, int]:
    """File2 in File1; bei -oc in separate Datei. Keine Audiorekodierung."""
    first = first.expanduser().resolve()
    second = second.expanduser().resolve()
    output = output.expanduser().resolve()
    if first == second:
        raise SpeechError("--merge benötigt zwei verschiedene Quellcontainer")
    for source in (first, second):
        if not source.is_file():
            raise SpeechError(f"SPC-Datei nicht gefunden: {source}")
    originals = read_container(first)
    additions = read_container(second)
    merged = {
        key: replace(item, source=(first if output != first else None))
        for key, item in originals.items()
    }
    inserted = 0
    collisions = 0
    for key, item in additions.items():
        if key in merged:
            collisions += 1
            if conflict == "error":
                raise SpeechError(f"Doppelter Eintragsname {item.name!r}; --on-conflict keep|replace angeben")
            if conflict == "keep":
                continue
        merged[key] = replace(item, source=second)
        inserted += 1
    # Schreibt atomar. Der Originalcontainer und Datei2 bleiben im Fehlerfall erhalten.
    write_container(output, merged)
    return inserted, collisions


def batch_commands(filename: Path) -> list[tuple[str, Path, str, bool]]:
    """(operation, wav_path, entry_name, strip) tuples."""
    result = []
    try:
        text = filename.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise SpeechError(f"Batchdatei kann nicht gelesen werden: {filename} ({exc})") from exc
    for line_no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        try:
            parts = shlex.split(line, posix=False)
        except ValueError as exc:
            raise SpeechError(f"Batchzeile {line_no}: {exc}") from exc
        parts = [x[1:-1] if len(x) >= 2 and x[0] == x[-1] and x[0] in "\"'" else x for x in parts]
        if len(parts) not in (2, 3):
            raise SpeechError(f"Batchzeile {line_no}: erwartet <WAV> [S] <A|D>")
        marker = parts[-1].upper()
        modifiers = [v.upper() for v in parts[1:-1]]
        if marker not in ("A", "D") or modifiers not in ([], ["S"]):
            raise SpeechError(f"Batchzeile {line_no}: erwartet <WAV> [S] <A|D>")
        path = Path(parts[0]).expanduser()
        if not path.is_absolute():
            path = filename.parent / path
        result.append((marker, path, checked_name(path.stem), "S" in modifiers))
    return result


def _arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                 allow_abbrev=False)
    ap.add_argument("eingaben", nargs="*", metavar="WAV|@BATCH",
                    help="PCM-WAV-Datei oder @Datei mit Batchanweisungen")
    ap.add_argument("--keep-ms", type=float, default=0.0, metavar="MS",
                    help="Bei --strip so viele ms Endstille behalten (Standard 0)")
    ap.add_argument("--output-wav", "-ow", type=Path, metavar="DATEI",
                    help="Ergebnis-WAV schreiben (PCM oder IMA-ADPCM)")
    ap.add_argument("--output-container", "-oc", type=Path, metavar="DATEI",
                    help="Sprachcontainer .spc anlegen/ändern")
    ap.add_argument("--del", "-d", action="append", default=[], dest="delete", metavar="EINTRAG",
                    help="Eintrag im Container löschen (mehrfach zulässig)")
    ap.add_argument("--add", "-a", metavar="EINTRAG",
                    help="Eingabe als angegebenen Eintrag zum Container hinzufügen/ersetzen")
    ap.add_argument("--gzip", "-gz", action="store_true",
                    help="Nur im Container: Payload nach dem Kodieren zusätzlich mit gzip komprimieren")
    ap.add_argument("--strip", "-s", action="store_true",
                    help="Exakt stille Frames am WAV-Ende entfernen")
    ap.add_argument("--convert", "-c", type=parse_codec, default="ima-adpcm", metavar="FORMAT",
                    help="Ausgabe: ima-adpcm (Standard), pcm, mp3, ogg")
    ap.add_argument("--lang", "-l", type=normalize_language, default="de_DE", metavar="SPRACHE",
                    help="Piper-Stimmensprache, z. B. de_DE oder en_US (wirkt nur mit --text)")
    ap.add_argument("--text", metavar="TEXT", help="Text mit Piper in PCM-WAV umwandeln; --lang wählt das Sprachmodell")
    ap.add_argument("--piper", metavar="PFAD", help="Pfad zu piper.exe")
    ap.add_argument("--piper-backend", choices=("auto", "exe", "python"), default="auto",
                    help="Piper-Backend: auto (EXE, bei 0xC0000409 Python-Fallback), exe oder python")
    ap.add_argument("--piper-python", metavar="PYTHON",
                    help="Python-Interpreter mit installiertem piper-tts (Standard: aktueller Interpreter)")
    ap.add_argument("--model", type=Path, metavar="ONNX", help="Piper-Modell .onnx (mit gleichnamiger .onnx.json)")
    ap.add_argument("--model-dir", type=Path, metavar="ORDNER", help="Ordner mit installierten Piper-Stimmen")
    ap.add_argument("--voice", metavar="SPRECHER", help="Sprecher, z. B. thorsten, kerstin, amy, joe")
    ap.add_argument("--quality", choices=("x_low", "low", "medium", "high"),
                    help="Piper-Modellqualität (Standard: de_DE=high, en_US=medium)")
    ap.add_argument("--list-voices", action="store_true", help="Beispiele offiziell verfügbarer Piper-Stimmen anzeigen")
    ap.add_argument("--merge", "-m", nargs=2, type=Path, metavar=("DATEI1", "DATEI2"),
                    help="DATEI2 in DATEI1 zusammenführen; ohne -oc wird DATEI1 aktualisiert")
    ap.add_argument("--on-conflict", choices=("keep", "replace", "error"), default="keep",
                    help="Namenskonflikte bei --merge: keep (Standard), replace oder error")
    ap.add_argument("--vlc", metavar="PFAD", help="Optionaler Pfad zu vlc.exe für MP3/Ogg-Encoding")
    ap.add_argument("--test", metavar="EINTRAG",
                    help="SPC-Eintrag anhören: PCM/IMA-ADPCM direkt unter Windows, MP3/Ogg über VLC")
    ap.add_argument("--list", action="store_true", help="Einträge im Container auflisten")
    ap.add_argument("--verify", action="store_true", help="CRC aller Containereinträge prüfen")
    return ap


def main(argv: Optional[list[str]] = None) -> int:
    ap = _arg_parser()
    args = ap.parse_args(argv)
    if args.test is not None:
        if (not args.output_container or args.merge or args.eingaben or
                args.text is not None or args.add or args.delete or args.strip or
                args.gzip or args.output_wav or args.list_voices):
            ap.error("--test EINTRAG benötigt ausschließlich -oc CONTAINER.spc (optional --vlc)")
        if args.convert != "ima-adpcm":
            ap.error("--convert wird bei --test nicht verwendet")
        if args.verify:
            print(f"CRC OK: {verify_container(args.output_container)} Einträge")
        if args.list:
            for entry in read_container(args.output_container).values():
                print("  " + entry.name)
        test_container_entry(args.output_container, args.test, args.vlc)
        return 0
    if args.piper_backend == "python" and args.piper:
        ap.error("--piper ist nur mit --piper-backend exe/auto sinnvoll; --piper-python fuer Python verwenden")
    if args.list_voices:
        if args.merge or args.eingaben or args.text or args.delete or args.add or args.list or args.verify:
            ap.error("--list-voices nicht mit Dateioperationen kombinieren")
        list_voice_catalog(args.lang if args.lang != "de_DE" else None)
        return 0
    if args.merge:
        if args.eingaben or args.text is not None or args.add or args.delete or args.output_wav or args.strip:
            ap.error("--merge kann nicht mit WAV-, --text-, --add-, --del- oder --strip-Operationen kombiniert werden")
        output = args.output_container or args.merge[0]
        if args.gzip:
            ap.error("--gzip wirkt nur beim Hinzufügen neuer Samples; bei --merge bleiben Payloads unverändert")
        if args.convert != "ima-adpcm":
            ap.error("--convert wirkt nicht beim verlustfreien Zusammenführen")
        added, duplicates = merge_containers(args.merge[0], args.merge[1], output, args.on_conflict)
        print(f"MERGE: {args.merge[1]} -> {output} (übernommen/ersetzt: {added}, Namenskonflikte: {duplicates})")
        if args.list:
            for item in read_container(output).values():
                print(f"  {item.name} ({CODEC_NAMES[item.codec & 0x7f]}{' +gzip' if item.codec & CODEC_GZIP_FLAG else ''})")
        if args.verify:
            print(f"CRC OK: {verify_container(output)} Einträge")
        return 0
    if args.text is not None and args.eingaben:
        ap.error("--text und WAV-Dateien nicht gleichzeitig angeben")
    if args.text is not None and args.output_container and not args.add:
        ap.error("--text mit -oc benötigt -a EINTRAG")
    if args.text is not None and not args.output_container and not args.output_wav:
        ap.error("--text benötigt -ow oder -oc mit -a EINTRAG")
    if args.keep_ms < 0:
        ap.error("--keep-ms muss >= 0 sein")
    if args.gzip and not args.output_container:
        ap.error("--gzip/-gz ist nur mit --output-container/-oc erlaubt")
    if args.output_wav and args.convert not in ("pcm", "ima-adpcm"):
        ap.error("--output-wav kann nur PCM- oder IMA-ADPCM-WAV schreiben. Für MP3/Ogg: -oc oder automatische Ausgabedatei verwenden.")
    if (args.add or args.delete or args.list or args.verify) and not args.output_container:
        ap.error("--add/--del/--list/--verify benötigt --output-container")
    batch_files = [x[1:] for x in args.eingaben if x.startswith("@")]
    single_files = [x for x in args.eingaben if not x.startswith("@")]
    if args.add and (len(single_files) != 1 and args.text is None or batch_files):
        ap.error("--add erwartet genau eine WAV-Eingabe oder --text")
    if args.output_wav and (len(single_files) != 1 and args.text is None or batch_files):
        ap.error("--output-wav erwartet genau eine WAV-Eingabe oder --text")
    if len(batch_files) > 1:
        ap.error("Es wird eine Batchdatei je Aufruf unterstützt")
    if batch_files and not args.output_container:
        ap.error("@BATCH benötigt --output-container")
    if not args.eingaben and args.text is None and not args.delete and not args.list and not args.verify:
        ap.error("Eingabe, --text, @BATCH, --del, --list oder --verify fehlt")
    operations = []
    for name in args.delete:
        operations.append(("D", None, checked_name(name), False))
    for path_string in single_files:
        path = Path(path_string).expanduser()
        operations.append(("A", path, checked_name(args.add or path.stem), args.strip))
    if args.text is not None:
        operations.append(("T", None, checked_name(args.add or "speech"), args.strip))
    if batch_files:
        operations.extend(batch_commands(Path(batch_files[0]).expanduser()))
    writes = bool(operations)
    if args.output_container and writes and any(op[0] == "A" for op in operations):
        pass  # Additions are explicit with -a or implicit from positional WAV files.
    # If no container is specified, only one input is supported per command.
    if not args.output_container and len(operations) != 1:
        ap.error("Ohne --output-container genau eine WAV-Eingabe angeben")
    if not args.output_container and operations and operations[0][0] not in ("A", "T"):
        ap.error("--del benötigt --output-container")

    with tempfile.TemporaryDirectory(prefix="speechconvert_") as workdir:
        staged = Path(workdir)
        items: dict[str, Item] = (read_container(args.output_container) if args.output_container else {})
        for index, (op, source, name, batch_strip) in enumerate(operations):
            if op == "D":
                removed = items.pop(name.casefold(), None)
                print(f"ENTFERNT: {name}" if removed else f"NICHT VORHANDEN: {name}")
                continue
            if op == "T":
                audio = synthesize_piper(args.text, args)
            else:
                assert source is not None
                audio = load_pcm(source)
            original_frames = audio.frames
            if args.strip or batch_strip:
                audio, removed = trim_end(audio, args.keep_ms)
            else:
                removed = 0
            payload, channels = encode(audio, args.convert, args.vlc)
            is_batch = bool(batch_files)
            if args.output_container:
                payload_path = staged / f"audio_{index:06d}.bin"
                stored_payload = gzip.compress(payload, compresslevel=9, mtime=0) if args.gzip else payload
                payload_path.write_bytes(stored_payload)
                crc = zlib.crc32(stored_payload) & 0xffffffff
                entry = Item(name, CODECS[args.convert] | (CODEC_GZIP_FLAG if args.gzip else 0),
                             channels, audio.rate, audio.frames,
                             len(stored_payload), crc, payload_path)
                items[name.casefold()] = entry
                pack_info = f", gzip {len(stored_payload)} B (vorher {len(payload)} B)" if args.gzip else ""
                print(f"ADD: {name} <- {source or 'Piper:'+args.lang} ({args.convert}{pack_info}, -{removed} Frames)")
            if not args.output_container or args.output_wav:
                if args.output_wav:
                    target = args.output_wav
                else:
                    suff = "_ohne_stille" if removed else ""
                    assert source is not None
                    target = source.with_name(source.stem + suff +
                                              "_" + args.convert.replace("-", "_") + EXTENSIONS[args.convert])
                if source is not None and source.resolve() == target.resolve():
                    raise SpeechError("Eingabe und Ausgabe dürfen nicht identisch sein")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
                print(f"DATEI: {target} ({len(payload)} Bytes, {original_frames} -> {audio.frames} Frames)")
        if args.output_container and writes:
            write_container(args.output_container, items)
            print(f"CONTAINER: {args.output_container} ({len(items)} Einträge)")
    if args.output_container and args.list:
        print(f"Inhalt: {args.output_container}")
        for item in read_container(args.output_container).values():
            duration = item.frames * 1000 / item.rate
            codec_label = CODEC_NAMES[item.codec & 0x7F] + ("+gzip" if item.codec & CODEC_GZIP_FLAG else "")
            print(f"  {item.name:30} {codec_label:15} {item.size:9} B "
                  f"{duration:8.1f} ms")
    if args.output_container and args.verify:
        count = verify_container(args.output_container)
        print(f"CRC OK: {count} Einträge")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SpeechError, OSError, ValueError, struct.error) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        raise SystemExit(1)
