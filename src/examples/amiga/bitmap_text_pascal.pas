// ---------------------------------------------------------------------------
// Standalone-Amiga-500: WriteLn über einen 8x8-Bitmapzeichensatz
// ---------------------------------------------------------------------------
program BitmapTextPascal;

begin
    SetTextColor($0F0, $000);
    WriteLn('Amiga 500 Bitmap-Text');
    WriteLn('Pascal WriteLn: Counter = ', 5);
    WriteLn('Farbe: gruen auf schwarz');
end.
