[Deutsch](STAGE419_C64_STA_REDUCER_BITMAP_CLEAR.md) | [English](STAGE419_C64_STA_REDUCER_BITMAP_CLEAR.en.md)

# Stage 419 – Compact Bitmap Screen Initialization with STA Reducer

**Basis:** `d64_dism_asm_418.zip` (see the German release notes for the exact baseline).

Stage 419 optimizes the bitmap clear sequence used by the C64 software-sprite runtime. With **STA reducer off**, the original loop with 40 direct `STA abs,X` operations remains. With the option enabled, repeated page writes are consolidated into a compact self-modifying clearing routine using one `STA abs,X` instruction and three memory ranges. All required writes still occur **at runtime**; this is an output-size optimization, not a removed initialization.

The existing Stage-418 literal/RLE tables for the other sprite write sequences remain. The documentation includes PRG-size measurements and regression tests. Behavior on real hardware must still respect VIC-II address ranges and reserved memory.
