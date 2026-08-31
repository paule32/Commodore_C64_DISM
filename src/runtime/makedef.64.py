# ---------------------------------------------------------------------------
# File:   makedef.64.py
# Author: (c) 2024, 2025, 2026 Jens Kallup - paule32
# All rights reserved
# ---------------------------------------------------------------------------
from pathlib import Path

imports_files = {
    "libdbase2many.64.dll": [
        "arrays",
        "crypto",
        "diskio",
        "strings",
        "console",
        "runtime",
        "memory",
        "exception",
        "debug",
        "error",
    ]
}

def write_merged_def_file(output_file, base_dir="."):
    base_dir = Path(base_dir)
    output_file = Path(output_file)
    written = set()

    with output_file.open("w", encoding="ascii", newline="\n") as out:
        for dll_name, def_names in imports_files.items():
            out.write(f'LIBRARY "{dll_name}"\n')
            out.write("EXPORTS\n")

            for def_name in def_names:
                def_file = base_dir / f"{def_name}.def"

                if not def_file.is_file():
                    raise FileNotFoundError(f"DEF-Datei nicht gefunden: {def_file}")

                for line in def_file.read_text(encoding="ascii").splitlines():
                    line = line.strip()

                    if not line:
                        continue

                    if line.upper().startswith("LIBRARY"):
                        continue

                    if line.upper() == "EXPORTS":
                        continue

                    symbol = line.split()[0].lower()
                                        
                    if symbol in written:
                        continue
                                                                                        
                    written.add(symbol)
                    out.write(f"    {line}\n")

            out.write("\n")

if __name__ == "__main__":
    write_merged_def_file(
        "libdbase2many.64.def",
        base_dir = "exports"
    )
