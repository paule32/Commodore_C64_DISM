[Deutsch](README.md) | [English](README.en.md)

# Commodore_C64_DISM
A Commodore C64 disassembler, disk-image information viewer, and unpacking tool.


### [Sponsor donation](https://www.paypal.com/ncp/payment/CUBXY9QPTPHRU)
### [Download a ZIP archive](https://kallup.net/downloads) containing a ready-to-run Windows 11 Pro 64-bit executable and the required DLL files.
---

[STAGES - Deutsch](docs/stages/STAGE393_C64_HEX_BUILD_PETSCII_JSON.md)<br>
[STAGES - English](docs/stages/STAGE393_C64_HEX_BUILD_PETSCII_JSON.en.md)


# d64_dism – Illustrated Project Atlas

**Integrated development environment, retro compilers, tools, and educational modules**  
**Status:** October 15, 2026

![Architecture of the d64_dism project](img/architektur.png)

## Project Concept

- A substantially extended Python/PyQt5 IDE with projects, dockable workspaces, and source-code and binary tools.
- Custom compiler, assembler, and linker components for the C64, Amiga, and Windows PE, alongside a separate dBase/WFM development branch.
- Specialized tools for C64 graphics, resources, documentation, server configuration, databases, mathematics, and learning.

---

## 01 Development Environment and Project Management

The shared foundation of the compiler, designer, and educational components.

### User Interface

Movable toolbars and resizable dock windows; a central tabbed document editor. Light and dark themes, status fields, favorites, and recently used files.

### Projects

Project/information tree and filesystem view with a working directory. `.pro` project files, platform- and compiler-specific project settings, and persistent file associations.

### Editors and Convenience Features

- Syntax highlighting, line numbers, zoom, search (Ctrl+F/F3), editing with undo/redo, and clipboard support.
- F2 / Compile / Assemble / Run workflows with target-specific behavior; source files and generated output in separate views.
- Hex viewer: eight bytes per line (4+4), PETSCII column, C64Pro font, and JSON mapping for 256 PETSCII codes.
- F1/CHM context-sensitive help, a log dock, and progress feedback during lengthy disassembly operations.
- New C64 BASIC and assembly files initially exist as unsaved templates; the files are created only when saved.

### Project Tree – Typical Areas

| Node / Workspace | Purpose |
|---|---|
| BASIC, ASM, Pascal, C, LISP, Prolog, LOGO, dBase | Source files, modules, and language-specific editors |
| C= 64 Sprites / Resources | Hardware sprites, bitmap sprites, character and screen resources |
| Tables / Forms / Reports | DBF data, WFM designer, SQL, report and label objects |
| Resources / Archives / Knowledge Bases | Windows resources, COFF objects, Prolog databases |

---

## 02 C64 Disks, Disassembler, and VICE

The original retro-computing functionality remains a development area in its own right.

### D64 and PRG Tools

- Open D64 images, inspect directories and the BAM, extract programs, inspect load addresses, and disassemble PRG files.
- Display MOS 6502/6510 code with operands and mnemonics, with optional live help and contextual information.
- Binary/RAM images, startup analysis, and hex views with PETSCII/character interpretation.
- Disassembly in a worker thread with byte-based progress and status reporting.

### Two Paths to Execution in VICE

![Two paths to execution in VICE](img/vice_ausfuehrungswege.png)

- **BASIC directly → VICE:** Transfer host data through the remote monitor; `LOAD SPRITE` loads into RAM at `$3000`.
- **BASIC → Compiler → VICE:** Sprite bytes embedded in the PRG; `SCREEN / DRAW / ERASE`.

### VICE Integration

- Direct transfer of BASIC lines/programs; ASM PRGs transferred byte by byte into C64 RAM.
- Binary Remote Monitor v2: set registers/PC, single-step instructions, and resume program execution.
- Generate D64 images with the 1541 BAM, directory, and PRG sector chains; mount the image on drive 8 and autostart the first PRG file.
- Configurable VICE settings (`vice.ini`), drive-8 directory, and project-local sprite-data preparation.

> **Note:** Configuring an already running VICE instance and assigning its drives may behave differently from restarting VICE. Many integration tests are based on source code or CPU behavior rather than full Windows emulator end-to-end tests.

---

## 03 C64 Character, Pixel, and Sprite Tools

Retro graphics designers and newer software-sprite functionality.

### The 16 C64 Color Indices

Schematic palette; exact color rendering depends on the hardware or emulator.

![The 16 C64 color indices](img/c64_farbpalette.png)

### Hardware Sprite Editor

24×21 HiRes or 12×21 multicolor, with transparent pixels. VIC-II color registers, shared multicolor values, and 2× scaling. `.spr`/`.sprite`/`.bin` store actual 63-/64-byte raw sprite data; project-local storage is supported.

### Bitmap Sprite Editor

Stage 416: a freely colorable pixel grid with 16 C64 color indices and per-pixel transparency. Standard 24×21, up to 128×128; multiple sprites, duplication, and deletion. `.bmsprite`/`.bmspr` use a binary format with a `C64BMSP1` header, not JSON.

### Other C64 Designers

- Character editor: up to 255 editable 8×8 characters.
- Palette editor: edit the 16 VIC-II colors and export source code.
- Text-screen editor: 40×25 characters with individual cell colors.
- Pixel-screen editor: 320×200 pixels with 16-color tools.
- BASIC editor: C64 font, on-screen keyboard, PETSCII, line numbering, and a custom row/column display.

> **Note:** A 16-color bitmap sprite cannot display all 16 colors independently in every cell on real VIC-II hardware: the multicolor bitmap mode permits four colors per 8×8 cell, including the global background color.

---

## 04 C64 BASIC – Screen and Software Sprites

Stages 413–417 extend BASIC V2 with custom sprite and graphics syntax.

| Command | Effect |
|---|---|
| `LOAD "name.spr",8,1` | Load a PRG from D64 drive 8 via KERNAL LOAD |
| `LOAD SPRITE "name.spr"` | Sprite from the Windows host, transferred directly through the monitor or embedded at compile time |
| `LOAD SPRITE "name.bmsprite"` | 16-color bitmap sprites as a compiler resource |
| `SCREEN ON` / `SCREEN OFF` | Enable multicolor bitmap / restore the previous VIC state |
| `SPRITE SOFTWARE ON` / `OFF` | Enable / disable software drawing commands |
| `SPRITE DRAW N,X,Y` | Draw a software sprite with transparency |
| `SPRITE ERASE N` | Remove a sprite and rebuild the remaining scene |
| `SCREEN WAIT` | Pause the bitmap display until a key is pressed |

### Example – Compiling C64 BASIC to Machine Code

```basic
10 LOAD SPRITE "figuren.bmsprite"
20 SCREEN ON
30 SPRITE SOFTWARE ON
40 SPRITE DRAW 0,100,80
50 SCREEN WAIT
60 SPRITE DRAW 1,140,80
70 SPRITE ERASE 0
80 SCREEN OFF
```

> **Note:** In Stage 417, the bitmap drawing scene is prepared at compile time. Sprite numbers and coordinates are initially constants; X must be even in multicolor mode. Direct VICE BASIC debug transfers do not yet support SCREEN/DRAW/ERASE.

---

## 05 Compiler Languages and Target Platforms

`d64_dism` combines multiple frontends. Supported language features vary considerably by language and platform.

| Frontend | Codebase / Features | Targets According to Project Code |
|---|---|---|
| BASIC | BASIC V2, C64 graphics/file/sprite extensions, internal 6510 assembler | C64 PRG; BASIC interpreter transfer to VICE |
| Pascal | ANTLR frontend, units/PUI, records, arrays, static classes | C64, Amiga, and Windows PE development branch |
| C | ANTLR frontend, preprocessor/macros, control flow, types | C64 and Amiga; Windows PE tools |
| dBase | DBF/SQL/WFM, string functions, console/GUI runtime | Windows PE32/PE32+ |
| PROLOG | Unification, lists, choice points, trail, assert/retract, knowledge browser | Windows PE32/PE32+ |
| LISP / LOGO / ELAN | Custom frontend/generator paths and sample programs | Varying, partly limited target support |

### Integrated Compilation Components

- MOS 6510 assembler with branch-range handling; Motorola 68k assembler and Amiga Hunk/ADF output.
- COFF32/COFF64 object generation, internal Windows PE linkers, import/export support, and runtime libraries.
- ANTLR lexers and parsers for C and Pascal; compilers produce human-readable assembly for further editing.
- Project profiles for Windows 32/64-bit and Commodore/Amiga targets; Compile / Assemble / Run.

> **Note:** Having a frontend does not imply complete compliance with a language standard or a verified executable output for every target combination. The module READMEs describe the subsets actually supported.

---

## 06 Windows Compiler, Resources, and Runtime

Independent PE/COFF tooling alongside the C64 features.

### PE Toolchain

Integrated IA-32/PE32 assembler and COFF32 writer. PE32/PE32+ linker, COFF archives, DLL imports/exports, Windows launch programs, MSZIP image packer, and workstation runner.

### Resources and GUI

RC script compiler producing `.res` files and COFF resource objects. Resource editor with syntax highlighting, line numbers, and a minimap. Windows manifest project options; dBase WFM form designer and Qt5 C-ABI bridge.

### Development and Runtime

- Workstation mode with separate PE32/PE32+ launch paths and a session host.
- Win32 launcher with watchdog, console logging, and a fallback error dialog.
- Debug window with project-specific presentation options and light/dark themes.
- Windows graphics targets and Direct2D/Direct3D runtime tools in the Tools menu.

### Build Limitations

The internal compilers and assemblers are major project goals. Individual bridges and runtimes still require suitable Qt/MinGW build environments and are not necessarily built automatically when the IDE starts.

---

## 07 dBase, Databases, and Form Design

A substantial second focus of the application, not merely another language frontend.

### Database Layer

- Read and write DBF files; table designer, data grid, field types, and multi-table workspace.
- SQL builder with design/view areas, table relationships, sorting, and data navigation.
- ODBC login and DSN/DBQ configuration, including a 32-/64-bit helper path.
- Report builder with data fields and PDF/printing; label designer with templates and print-ready layouts.

### Forms and WFM System

- Visual form designer, property inspector, component controls, and border/shadow settings.
- Light/dark mode, controls, event/timer properties, and project-associated WFM files.
- Qt5 bridge `d64qt5.dll` for native dBase applications with console/DEBUG output.
- dBase compiler with support for strings, classes, and preprocessors.

### Data Development Tools

| SQL + DBF | Reports + Labels |
|---|---|
| Select sources, draw relationships, test queries, view SQL results, and use them in a report. | Visualize layouts, place database fields, export PDFs, and save/load project-specific designs. |

---

## 08 Education, Electronics, Documentation, and Servers

Additional integrated tools outside the traditional compiler workflow.

### Mathematics and Knowledge

Unit circle, sine/cosine, formula designer, number walls, Fibonacci numbers, Pascal's triangle, prime numbers, geometry, and interest calculations. Minesweeper, Memory, and other educational games.

### Geography and Natural Sciences

Maps of Germany, England, and France with river overlays. Periodic table with a detailed view and chemistry construction kit. Electronics construction kit with components, schematics, and initial simulation functionality.

### Music, Speech, and Media

Musical keyboard/piano with a musical notation area. Retro speech runtime and speech synthesis modules. WYSIWYG HTML editor and localization tools.

### Documentation and Servers

CHM help and a Doxygen documentation interface for Pascal/C++. BIND9/DynDNS, OpenSSL, and Apache dock panels. Qt themes, translations, resources, and help dialogs.

> **Note:** Some specialized modules were added across many development stages. Their presence in the source code confirms their integration, but their functional scope and runtime quality depend on external programs, assets, and operating systems.

---

## 09 Optimization – Making Programs Significantly Smaller

The latest stages focus on reducing generated MOS 6510 program code.

| Switch | Purpose |
|---|---|
| STA reducer – Stage 418 | Compress repeated STA sequences into literal/RLE tables plus a decoder. |
| Bitmap Clear – Stage 419 | Replace 40 STA page writes with a self-modifying page-clearing routine. |
| CALL reducer – Stage 420 | Remove unreachable C64 BASIC runtime code following control-flow and reference analysis. |

### Example Measurement: C64 Bitmap Sprite Program

![Size comparison with reducers](img/optimierung_groessenvergleich.png)

| Optimization | PRG Size |
|---|---:|
| Without reducers | 2,359 B |
| CALL only | 1,587 B |
| STA only | 1,889 B |
| STA + CALL | **1,117 B** |

**Stage 420 comparison:** Both reducers lower the PRG size from 2,359 to 1,117 bytes (approximately 53%).

### Selected Development Milestones

![Development milestones from Stage 393 to Stage 420](img/stage_zeitstrahl.png)

| Stage | Development |
|---|---|
| 393 | Hex + PETSCII |
| 396 | Hardware sprites |
| 404 | Binary `.spr` |
| 409 | D64/VICE |
| 413 | `LOAD SPRITE` |
| 416 | Bitmap editor |
| 417 | Software sprites |
| 418–420 | Optimizers |

---

## 10 Development Status, Risks, and Next Milestones

This overview distinguishes features implemented in code from fully verified runtime behavior.

### Verifiable in the Archive

- `d64_dism.py` comprises approximately 140,000 lines; the Stage 420 ZIP contains roughly 400 project files, including modules and tests.
- Stages 393–420 have separate technical change documents; regression tests and actual assembler PRG comparisons are available for the CALL/STA reducers.
- The C64 BASIC, sprite, and VICE subsystems have repeatedly been corrected using specific user-supplied programs.

### Not Fully Verified

- End-to-end tests of all GUI modules on Windows, all VICE/WinUAE configurations, and all PE/Amiga targets.
- C64 bitmap software sprites with dynamic coordinates and animation; Stage 417 primarily works with constant scenes.
- General safety of the CALL reducer for arbitrary external and indirectly referenced assembly code.
- Unrestricted 16-colors-per-pixel rendering on real VIC-II hardware; cell-color limitations remain.

### Recommended Next Milestones

| Priority | Concrete Task |
|---|---|
| 1 | Windows GUI/VICE regression suite for `LOAD SPRITE`, `SCREEN/DRAW/ERASE`, and disk-image autostart. |
| 2 | Dynamic software sprites: motion/collision routines, RAM safety, and color-conflict strategies. |
| 3 | Compiler optimization with safe symbol/function roots, testable call-graph output, and size reports. |
| 4 | Automated builds and functional tests across C64, Amiga, PE32, and PE32+. |

### Sources for This Overview

`d64_dism.py`, modules, README files, Stage 393–420 documents, and development notes supplied to the project. Earlier development versions are mentioned only for context insofar as they are carried forward by the current Stage 420 code.

---

## Screenshots and Quick Start

### Preview

![Preview](img/screen0021.png)

### Step 1

![Preview](img/screen00A1.png)

After starting the application, select **Open** from the menu. A file-system dialog will appear. Navigate to the data you want to edit.

### Step 2

![Preview](img/screen00A2.png)

### Step 3

![Preview](img/screen00A3.png)

### Step 4

![Preview](img/screen00A4.png)

### Step 5

![Preview](img/screen00A5.png)

After compiling and assembling the form/application, navigate to `example/dbase`. The generated executable (`.exe`) should be there. You can then run the application.

Make sure **D64QT5.DLL** is accessible in the same directory as the executable.

If everything works, a new workstation window with a blank screen and the application should open.

Happy coding with dBASE!

### For FibuDev

![Preview](img/screen0013.png)

The screenshot shows `test.exe`, produced by compiling and assembling `examples/dbase/test.wfm`. The resulting file was approximately 3,500 bytes after compression using Win32 API packing functions. The unpacked file was approximately 7,200 bytes (a saving of roughly 3,000 bytes).

### A Note on Cybersecurity

The packed file uses a transparent format and can be decompressed again to examine the original contents for malware or other hidden components.

### Disclaimer – No Warranties

The software is provided without warranties concerning damage arising from packed code or third-party software. The author aims to avoid interfering with software protections or integrity mechanisms.

### Preview – New Source Code Editor Layout for the dBASE Compiler

![Preview](img/screen00A6.png)

### Preview – Resource Editor / Compiler

![Preview](img/screen0019.png)

### Preview – Prime Number Solver

![Preview](img/screen0020.png)

### Preview – Electronics Construction Kit

![Preview](img/screen0018.png)

### Preview – Report Designer

![Preview](img/screen0017.png)

### Additional Screenshots

![Preview](img/screen0015.png)

![Preview](img/screen0016.png)

![Preview](img/screen0012.png)

![Preview](img/screen0011.png)

![Preview](img/screen0010.png)

![Preview](img/screen0009.png)

![Preview](img/screen0008.png)

![Preview](img/screen0007.png)

![Preview](img/screen0006.png)

![Preview](img/screen0005.png)

![Preview](img/screen0004.png)

### Preview A

![Preview](img/screen0001.png)

![Preview](img/screen0002.png)

![Preview](img/screen0014.png)

![Preview](img/screen0022.png)

![Preview](img/screen0023.png)

![Preview](img/screen0024.png)
