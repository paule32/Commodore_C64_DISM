#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install an optional German offline Piper voice for d64_dism Stage 355.

This is a one-time *user action*, not part of compiling a dBase executable.
The voice model and external Piper runtime are not bundled with the project.
"""
from __future__ import annotations
import argparse
import hashlib
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

PIPER_WINDOWS_ZIP = (
    "https://github.com/rhasspy/piper/releases/download/"
    "2023.11.14-2/piper_windows_amd64.zip"
)
PIPER_VOICES = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
# The official Hugging Face model blob hash for the high-quality German voice.
THORSTEN_HIGH_SHA256 = "9df1c43c61149ef9b39e618e2b861fbe41e1fcea9390b2dac62e8761573ea4f1"


def voice_urls(quality: str) -> dict[str, str]:
    if quality not in {"low", "medium", "high"}:
        raise ValueError("quality must be low, medium or high")
    root = f"{PIPER_VOICES}/de/de_DE/thorsten/{quality}"
    filename = f"de_DE-thorsten-{quality}.onnx"
    return {
        "model": f"{root}/{filename}",
        "config": f"{root}/{filename}.json",
        "model_card": f"{root}/MODEL_CARD",
    }


def fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "d64-dism-piper-setup/1.0"})
    partial = dest.with_name(dest.name + ".part")
    if partial.exists():
        partial.unlink()
    try:
        with urllib.request.urlopen(request, timeout=120) as reader, partial.open("wb") as out:
            copied = 0
            while True:
                data = reader.read(1024 * 1024)
                if not data:
                    break
                out.write(data)
                copied += len(data)
                if copied and copied % (16 * 1024 * 1024) == 0:
                    print(f"  {dest.name}: {copied / (1024 * 1024):.0f} MiB ...")
        if not partial.stat().st_size:
            raise RuntimeError("Leere Download-Datei: " + url)
        partial.replace(dest)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


def verify_model_sha256(path: Path, expected: str) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for data in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(data)
    if digest.hexdigest().lower() != expected.lower():
        raise RuntimeError("Die SHA-256-Prüfung des Sprachmodells ist fehlgeschlagen: " + str(path))


def unpack_windows_cli(archive: Path, target: Path) -> None:
    """Unpack a trusted release archive, flattening its outer piper directory."""
    if not zipfile.is_zipfile(archive):
        raise ValueError(f"Keine gültige ZIP-Datei: {archive}")
    with tempfile.TemporaryDirectory(prefix="d64-piper-") as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(archive) as zf:
            for info in zf.infolist():
                # Guard against archive path traversal (third party ZIP).
                destination = (root / info.filename).resolve()
                if root.resolve() not in destination.parents and destination != root.resolve():
                    raise ValueError("Unsicherer Dateiname im ZIP: " + info.filename)
            zf.extractall(root)
        engines = list(root.rglob("piper.exe"))
        if not engines:
            raise ValueError("Das heruntergeladene Paket enthält keine piper.exe")
        source = min(engines, key=lambda p: len(p.parts)).parent
        target.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, dirs_exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deutsche Thorsten/Piper-Stimme für d64_dism installieren")
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="high")
    parser.add_argument("--directory", type=Path,
                        default=Path(__file__).resolve().parent / "piper")
    parser.add_argument("--engine-zip", type=Path,
                        help="lokale Piper-Windows-ZIP statt Netz-Download")
    parser.add_argument("--skip-engine", action="store_true",
                        help="Piper.exe und Bibliotheken sind schon vorhanden")
    parser.add_argument("--dry-run", action="store_true",
                        help="nur Download-Links anzeigen")
    args = parser.parse_args()
    urls = voice_urls(args.quality)
    directory = args.directory.resolve()
    print("Piper Windows:", PIPER_WINDOWS_ZIP)
    for key, value in urls.items():
        print(key + ":", value)
    print("Installationsordner:", directory)
    if args.dry_run:
        return 0
    directory.mkdir(parents=True, exist_ok=True)
    if not args.skip_engine and not (directory / "piper.exe").exists():
        if args.engine_zip:
            unpack_windows_cli(args.engine_zip, directory)
        else:
            with tempfile.TemporaryDirectory(prefix="d64-piper-zip-") as tmp:
                archive = Path(tmp) / "piper_windows_amd64.zip"
                print("Lade Windows-Piper herunter ...")
                fetch(PIPER_WINDOWS_ZIP, archive)
                unpack_windows_cli(archive, directory)
    if not (directory / "piper.exe").is_file():
        raise RuntimeError("piper.exe fehlt. Installiere erst das Windows-Piper-Paket.")
    for key, url in urls.items():
        filename = (f"de_DE-thorsten-{args.quality}.onnx" + (".json" if key == "config" else "")) if key != "model_card" else "MODEL_CARD"
        target = directory / filename
        if target.is_file() and target.stat().st_size:
            if key == "model" and args.quality == "high":
                verify_model_sha256(target, THORSTEN_HIGH_SHA256)
            print("Bereits vorhanden:", target.name)
            continue
        print("Lade herunter:", target.name)
        fetch(url, target)
        if key == "model" and args.quality == "high":
            try:
                verify_model_sha256(target, THORSTEN_HIGH_SHA256)
            except Exception:
                target.unlink(missing_ok=True)
                raise
    print("Bereit. Verwende in dBase: SET SPEECH MODE PIPER")
    print("Für eine fertige EXE die komplette piper-Unterstruktur neben die EXE kopieren.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
