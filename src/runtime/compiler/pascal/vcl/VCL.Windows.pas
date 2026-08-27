// ---------------------------------------------------------------------------
// File:   VCL.Windows.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
unit VCL.Windows;

interface
uses System,
     Windows.Types,
     Windows.Kernel,
     Windows.User;

type
    TWindow = class(TObject)
    private
        FWinRegisteredName: PAnsiChar;
        FWinInstance: HINSTANCE;
        FWinHandle: HWND;
        FWinTitle: PAnsiChar;
    public
        constructor Create;
        destructor Destroy; override;
        
        function GetHandle: HWND;
        function DispatchMessage(
            winhWnd: HWND;
            Msg: UINT;
            wParam: WPARAM;
            lParam: LPARAM
        ):  LRESULT;
        
    end;

type
    TForm = class(TWindow)
    private
        FWidth: Integer;
        FHeight: Integer;
        FLeft: Integer;
        FTop: Integer;
        FCaption: String;
    public
        constructor Create;
        destructor Destroy; override;
    published
        property Height: Integer read FHeight write FHeight;
        property Width: Integer read FWidth write FWidth;
        property Top: Integer read FTop write FTop;
        property Left: Integer read FLeft write FLeft;
        property Caption: String read FCaption write FCaption;
    end;

implementation

{ TWindow }

function GlobalWindowProc(
    winHwnd: HWND;
    uMsg:    UINT;
    wParam:  WPARAM;
    lParam:  LPARAM
):  LRESULT; stdcall;
var
    AppForm: TForm;
    CreateStruct: PCREATESTRUCTA;
    ButtonWindow: HWND;
begin
    if uMsg = WM_NCCREATE then
    begin
        CreateStruct := PCREATESTRUCTA(lParam);
        AppForm := TForm(CreateStruct^.lpCreateParams);
        
        if Assigned(AppForm) then
        begin
            AppForm.FWinHandle := winHwnd;
            SetWindowLongA(
                winhwnd,
                GWL_USERDATA,
                LongInt(AppForm)
            );
        end;
    end else
    begin
        AppForm := TForm(
            GetWindowLongA(
                winhwnd,
                GWL_USERDATA
            )
        );
    end;
    
    if Assigned(AppForm) then
    begin
        result := AppForm.DispatchMessage(
            winhwnd,
            uMsg,
            wParam,
            lParam
        );

        if uMsg = WM_NCDESTROY then
        begin
            SetWindowLongA(
                winhwnd,
                GWL_USERDATA,
                0
            );
            AppForm.FWinHandle := 0;
            AppForm.Free;
            Exit;
        end;
        
        if uMsg = WM_DESTROY then
        begin
            PostQuitMessage(0);
            Result := 0;
            Exit;
        end;

        Exit;
    end;
(*
    if uMsg = WM_CREATE then
    begin
        ButtonWindow := CreateWindowExA(
            0,
            PAnsiChar('BUTTON'),
            PAnsiChar('Information'),
            WS_BUTTON,
            16,
            16,
            140,
            32,
            hWnd,
            ID_BUTTON_INFO,
            AppInstance,
            nil
        );
        Result := 0;
        Exit;
    end;

    if uMsg = WM_COMMAND then
    begin
        if wParam = ID_BUTTON_INFO then
        begin
            MessageBoxA(
                hWnd,
                PAnsiChar('Die Win32-GUI funktioniert.'),
                PAnsiChar('dBase2Many Pascal'),
                MB_OK + MB_ICONINFORMATION
            );
        end;

        Result := 0;
        Exit;
    end;
*)
    if uMsg = WM_DESTROY then
    begin
        PostQuitMessage(0);
        Result := 0;
        Exit;
    end;

    Result := DefWindowProcA(
        winhWnd,
        uMsg,
        wParam,
        lParam
    );
end;

constructor TWindow.Create;
var
    RegisterResult: Integer;
    WinClass: TWndClassA;
begin
    inherited Create;
    WriteLn('TWindow: Create');
    
    FWinRegisteredName      := PAnsiChar('Win32Gui.Window');
    FWinInstance            := GetModuleHandleA(nil);
    
    WinClass.style         := CS_REDRAW;
    WinClass.lpfnWndProc   := @GlobalWindowProc;
    WinClass.cbClsExtra    := 0;
    WinClass.cbWndExtra    := 0;
    WinClass.hInstance     := FWinInstance;
    WinClass.hIcon         := LoadIconA(0, IDI_APPLICATION);
    WinClass.hCursor       := LoadCursorA(0, IDC_ARROW);
    WinClass.hbrBackground := HBRUSH(COLOR_WINDOW + 1);
    WinClass.lpszMenuName  := nil;
    WinClass.lpszClassName := FWinRegisteredName;
    
    RegisterResult := RegisterClassA(WinClass);
    if RegisterResult = 0 then
    begin
        MessageBoxA(
            0,
            PAnsiChar('Die Fensterklasse konnte nicht registriert werden.'),
            PAnsiChar('Win32-Fehler'),
            MB_OK + MB_ICONERROR
        );
        ExitProcess(3);
    end;
    WriteLn('Register ok');
    FWinHandle := CreateWindowExA(
        0,                    { dwExStyle         }
        FWinRegisteredName,   { lpClassName       }
        FWinTitle,            { lpWindowName      }
        WS_OVERLAPPEDWINDOW,  { dwStyle           }
        CW_USEDEFAULT,        { X                 }
        CW_USEDEFAULT,        { Y                 }
        640,                  { nWidth            }
        480,                  { nHeight           }
        0,                    { hWndParent        }
        0,                    { hMenu             }
        FWinInstance,         { hInstance         }
        self                  { lpParam -> Objekt }
    );
    WriteLn('WinCreate ok');
    if FWinHandle = 0 then
    begin
        WriteLn('Handle error');
        MessageBoxA(
            0,
            PAnsiChar('Das Hauptfenster konnte nicht erzeugt werden.'),
            PAnsiChar('Win32-Fehler'),
            MB_OK + MB_ICONERROR
        );
        ExitProcess(2);
    end;
    
    WriteLn('TWindow: win handle ok');
end;
destructor TWindow.Destroy;
begin
    inherited Destroy;
end;

function TWindow.DispatchMessage(
    winhWnd: HWND;
    Msg: UINT;
    wParam: WPARAM;
    lParam: LPARAM
):  LRESULT;
begin
    result := DefWindowProcA(
        winhWnd,
        Msg,
        wParam,
        lParam
    );
end;

function TWindow.GetHandle: HWND;
begin
    result := FWinHandle;
end;


{ TForm }

constructor TForm.Create;
begin
    inherited Create;
    
    WriteLn('TForm: Create');
    
    FCaption := 'TForm';
end;

destructor TForm.Destroy;
begin
    inherited Destroy;
end;

end.
