# Stage 480 – GNU AT&T und Hauptmenü „Erstellen“

Grundlage: Stage 479.

## Menüfolge

Unmittelbar rechts von „Projekt“: „Erstellen“ mit Einträgen in dieser Reihenfolge:

1. **Kompilieren + Linken** (erster Eintrag): Compiler → Assembler → COFF/Linker, ohne automatischen Programmstart.
2. **Kompilieren**: nur ASM erzeugen.
3. Separator.
4. Exklusive Zielauswahl: Windows PE 32-Bit, Windows PE 64-Bit.
5. Separator.
6. Commodore C= 64, AMIGA 500.

Nicht unterstützte Ziel-/Sprachkombinationen werden zurückgewiesen; bestehende Zielarchitektur bleibt erhalten.

## AT&T-Modus

Die Einstellung „AT & T (GNU kompatibel)“ erzeugt AT&T-Assembler-Quellcode auch für compilererzeugte Dateien. Der intern verwendete COFF-Assembler übersetzt AT&T-Quellcode wieder in seine Intel-Operationen. Der Präprozessor bleibt vor der Übersetzung aktiv; vorhandene `%include`-Dateien werden berücksichtigt.

Neu in der GNU-Teilmenge: `.att_syntax`, `.intel_syntax`, `.text/.data/.bss`, `.section`, `.global/.globl`, `.d64_entry`, `.byte/.word/.long/.quad`, `.zero`, `.fill`, `.align`/`.p2align` (mit Grenzen), `.asciz/.ascii`, GNU-Register/Immediate/Adressierung und zahlreiche Mnemonics.

Der Modus ist **keine vollständige GNU-as-Emulation**. Nicht unterstützte GNU-Konstruktionen führen zu Fehlern, statt unverändert als fehlerhafter Intel-Code übergeben zu werden. Die Linkphase benutzt weiterhin den internen Windows-COFF-Linker, keinen externen GNU-as oder ld.

## Tests

Syntaxprüfung (`py_compile`), AT&T/Intel-Roundtrip, PE32/PE64-COFF und Linken, GNU-Includes, sowie Menüreihenfolge in `test_stage480_gnu_att_build_menu.py`.
