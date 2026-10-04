# ---------------------------------------------------------------------------
# \file  : mcp.py
# \author: (c) 2024, 2025, 2026 Jens Kallup - paule32
# \note  : All rights reserved
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request

from pathlib import Path

from mcp.server import MCPServer


# ------------------------------------------------------------
# Konfiguration
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
HELP_META_FILE = BASE_DIR / "helpmeta.json"

IC_API_BASE = os.environ.get(
    "DBASE2MANY_IC_API",
    "https://servera/api/ic.php"
)

# ------------------------------------------------------------
# MCP Server
# ------------------------------------------------------------

mcp = MCPServer("dBase2Many")


# ------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------

def load_help_meta() -> dict:
    if not HELP_META_FILE.is_file():
        return {}

    with HELP_META_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def normalize_language(value: str) -> str:
    return str(value or "").strip().casefold()


def normalize_topic(value: str) -> str:
    return str(value or "").strip().upper()


# ------------------------------------------------------------
# Tool: IC als SVG
# ------------------------------------------------------------

@mcp.tool()
def get_ic_svg(
    id: str,
    rotation: int = 0
) -> dict:
    """
    Liefert die SVG-Grafik eines ICs.

    id:
        IC-Bezeichnung, z.B. 74ls00.

    rotation:
        Drehung: 0, 90, 180 oder 270 Grad.
    """

    ic_id = str(id).strip()

    if not re.fullmatch(
        r"[A-Za-z0-9_-]+",
        ic_id
    ):
        raise ValueError(
            "Ungültige IC-ID."
        )

    if rotation not in (
        0,
        90,
        180,
        270
    ):
        raise ValueError(
            "rotation muss 0, 90, 180 oder 270 sein."
        )

    query = urllib.parse.urlencode({
        "id": ic_id,
        "rotation": rotation
    })

    url = f"{IC_API_BASE}?{query}"

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "dBase2Many-MCP/1.0",
            "Accept": "image/svg+xml"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=15
    ) as response:

        data = response.read()

        content_type = response.headers.get(
            "Content-Type",
            ""
        )

    svg = data.decode(
        "utf-8",
        errors="replace"
    )

    if "<svg" not in svg.casefold():
        raise RuntimeError(
            "Der Server hat keine SVG-Grafik geliefert."
        )

    return {
        "id": ic_id,
        "rotation": rotation,
        "url": url,
        "content_type": content_type,
        "svg": svg
    }

# ------------------------------------------------------------
# Tool: Hilfe nach Topic
# ------------------------------------------------------------
@mcp.tool()
def get_help_topic(
    topic: str,
    language: str = ""
) -> dict:
    """
    Sucht ein Hilfethema anhand seines Namens.

    Beispiel:
        topic = PRINT
        language = basic
    """

    data = load_help_meta()

    wanted_topic    = normalize_topic(topic)
    wanted_language = normalize_language(language)

    languages = []

    if wanted_language:
        languages.append(wanted_language)
    else:
        languages.extend(
            data.keys()
        )
    for language_name in languages:
        topics = data.get(
            language_name,
            {}
        )
        for name, meta in topics.items():
            if normalize_topic(name) == wanted_topic:
                return {
                    "found": True,
                    "language": language_name,
                    "topic": name,
                    "context_id": int(
                        meta.get(
                            "context_id",
                            0
                        )
                    ),
                    "local": str(
                        meta.get(
                            "local",
                            ""
                        )
                    )
                }
    return {
        "found": False,
        "topic": wanted_topic,
        "language": wanted_language
    }

# ------------------------------------------------------------
# Tool: Hilfe nach Context-ID
# ------------------------------------------------------------
@mcp.tool()
def get_help_context(
    context_id: int
) -> dict:
    """
    Sucht ein Hilfethema anhand einer numerischen Context-ID.
    """
    data   = load_help_meta()
    wanted = int(context_id)

    for language, topics in data.items():
        for topic,  meta in topics.items():
            current_id = int(
                meta.get(
                    "context_id",
                    0
                )
            )
            if current_id == wanted:
                return {
                    "found": True,
                    "context_id": wanted,
                    "language": language,
                    "topic": topic,
                    "local": str(
                        meta.get(
                            "local",
                            ""
                        )
                    )
                }
    return {
        "found": False,
        "context_id": wanted
    }

# ------------------------------------------------------------
# Start
# ------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="servera",
        port=8000
    )
