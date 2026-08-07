program UsesAndPreprocessor;

uses BuildInfo;

{$define REQUIRED_VERSION 2}
{$info Erzeuge Programm für Version REQUIRED_VERSION}

{$if REQUIRED_VERSION >= 2}
const FeatureText = 'PUI und Makros aktiv';
{$else}
{$error Die konfigurierte Version ist zu alt}
{$endif}

begin
  WriteLn(FeatureText);
  WriteLn('Unit-Version = ', BuildVersion);
end.
