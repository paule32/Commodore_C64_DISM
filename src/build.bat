:: ----------------------------------------------------------------------
:: Datei: build.bat - VICE64 Disassembler
::
:: (c) 2026 by Jens Kallup - paule32
:: alle Rechte vorbehalten.
:: ----------------------------------------------------------------------
@echo off
set vice="T:\ViceC64\bin\x64sc.exe"
goto test2

:test1
:: einfacher Ablauf ohne VICE
python d64info.py Dalek_Attack.d64 ^
  --startup     ^
  --extract-prg ^
  --analyze-prg ^
  --disassemble

:test2
:: kompletter Ablauf mit VICE
python d64info.py "Dalek_Attack.d64" ^
  --image-ram ^
  --disassemble-code ^
  --vice %vice%
goto done

:test3
:: RAM Abbild Disassembler
python d64info.py "Dalek_Attack.d64" ^
  --disassemble-code ^
  --ram-input "dalek_ram.bin"
goto done

:test4
:: für Übergang vom Intro zum Spiel
python d64info.py "Dalek_Attack.d64" ^
  --disassemble-code      ^
  --ram-breakpoint 0x2100 ^
  --vice-no-warp          ^
  --vice-run-timeout 600  ^
  --vice %vice%
goto done

:done
echo fertig.
exit 0
