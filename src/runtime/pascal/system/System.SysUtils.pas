// ---------------------------------------------------------------------------
// File:   System.SysUtils.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
unit System.SysUtils;

interface

uses System.Objects;

type
    Exception = class(TObject)
    private
        FMessage: String;
    public
        constructor Create(const AMessage: String);
    published
        property Message: String read FMessage;
    end;

implementation

constructor Exception.Create(
    const AMessage: String
);
begin
    inherited Create;
    FMessage := AMessage;
end;

end.
