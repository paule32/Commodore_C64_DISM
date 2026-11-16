program PlatformExample;
begin
  {$IFDEF WINDOWS}
  WriteLn('Windows-Ziel');
  {$ENDIF}
  {$IFDEF WIN32}
  WriteLn('Windows API');
  {$ENDIF}
  {$IFDEF WIN64}
  WriteLn('64-Bit Windows');
  {$ENDIF}
  {$IFDEF LINUX}
  WriteLn('Linux-Ziel');
  {$ENDIF}
end.
