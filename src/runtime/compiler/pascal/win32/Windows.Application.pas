// ---------------------------------------------------------------------------
// File:   Windows.Application.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
unit Windows.Application;

interface
uses System,
    Windows.Types,
    Windows.kernel,
    Windows.user,

    VCL.Windows;

const
    ID_BUTTON_INFO = 1001;

type
    TApplication = class(TObject)
    private
        FAppForm    : TForm;
    protected
        //procedure RunMessageLoop;
    public
        constructor Create;
        destructor Destroy; override;
    end;

implementation

{ TApplication }

procedure RunMessageLoop;
var
    msg: TMsg;
    status: Integer;
begin
    status := GetMessageA(msg, 0, 0, 0);

    while status > 0 do
    begin
        TranslateMessage(msg);
        DispatchMessageA(msg);
        status := GetMessageA(msg, 0, 0, 0);
    end;
end;

constructor TApplication.Create;
begin
    inherited Create;
    writeln('TApp: Create');
    FAppForm := TForm.Create;
    
    ShowWindow(FAppForm.FWinHandle, SW_SHOWDEFAULT);
    UpdateWindow(FAppForm.FWinHandle);
    RunMessageLoop;
end;

destructor TApplication.Destroy;
begin
    FAppForm.Free;
    
    inherited Destroy;
end;

end.
