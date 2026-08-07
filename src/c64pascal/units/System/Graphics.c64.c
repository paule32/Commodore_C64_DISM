/*
 * Getrennt kompilierte C64-Implementierung der Pascal-Unit System.Graphics.
 * Alle C64-Primitiven liegen direkt in MOS-6510-Assembler. Dadurch bleibt
 * die Pascal- und C-API identisch, ohne die komplexen Algorithmen durch den
 * allgemeinen C64-C-Codegenerator laufen zu lassen.
 */
#pragma d64_link_asm "../../../runtime/graphics/c64/graphics_c64.asm"
