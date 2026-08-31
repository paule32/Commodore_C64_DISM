// ---------------------------------------------------------------------------
// File:   Windows.User.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
unit Windows.User;

interface
uses System, Windows.Types;

const DLL_USER32 = 'user32.dll';

function GetWindowLongA(
    hWnd:   HWND;
    nIndex: Integer
    ): LongInt; stdcall; external
    DLL_USER32 name 'GetWindowLongA';

function SetWindowLongA(
    hWnd:      HWND;
    nIndex:    Integer;
    dwNewLong: LongInt
    ): LongInt; stdcall; external
    DLL_USER32 name 'SetWindowLongA';
    
function LoadIconA(
    hInstance:  HINSTANCE;
    lpIconName: Integer
    ):  HICON; stdcall; external
    DLL_USER32 name 'LoadIconA';

function LoadCursorA(
    hInstance:    HINSTANCE;
    lpCursorName: Integer
    ): HCURSOR; stdcall; external
    DLL_USER32 name 'LoadCursorA';

function RegisterClassA(
    var WndClass: TWndClassA
    ): Integer; stdcall; external
    DLL_USER32 name 'RegisterClassA';

function CreateWindowExA(
    dwExStyle:    DWORD;
    lpClassName:  PAnsiChar;
    lpWindowName: PAnsiChar;
    dwStyle:      DWORD;
    x:            Integer;
    y:            Integer;
    nWidth:       Integer;
    nHeight:      Integer;
    hWndParent:   HWND;
    hMenu:        HMENU;
    hInstance:    HINSTANCE;
    lpParam:      Pointer
    ): HWND; stdcall; external
    DLL_USER32 name 'CreateWindowExA';

function ShowWindow(
    hWnd:     HWND;
    nCmdShow: Integer
    ): BOOL; stdcall; external
    DLL_USER32 name 'ShowWindow';

function UpdateWindow(
    hWnd: HWND
    ): BOOL; stdcall; external
    DLL_USER32 name 'UpdateWindow';

function IsWindow(
    hWnd: HWND
    ): BOOL; stdcall; external
    DLL_USER32 name 'IsWindow';

function EnableWindow(
    hWnd: HWND;
    bEnable: BOOL
    ): BOOL; stdcall; external
    DLL_USER32 name 'EnableWindow';

function MoveWindow(
    hWnd: HWND;
    X: Integer;
    Y: Integer;
    nWidth: Integer;
    nHeight: Integer;
    bRepaint: BOOL
    ): BOOL; stdcall; external
    DLL_USER32 name 'MoveWindow';

function SetWindowTextA(
    hWnd: HWND;
    lpString: String
    ): BOOL; stdcall; external
    DLL_USER32 name 'SetWindowTextA';

function DestroyWindow(
    hWnd: HWND
    ): BOOL; stdcall; external
    DLL_USER32 name 'DestroyWindow';

function GetMessageA(
    var Msg:     TMsg;
    hWnd:        HWND;
    wMsgMin:     UINT;
    wMsgMax:     UINT
    ): BOOL; stdcall; external
    DLL_USER32 name 'GetMessageA';

function TranslateMessage(
    var Msg: TMsg
    ): BOOL; stdcall; external
    DLL_USER32 name 'TranslateMessage';

function DispatchMessageA(
    var Msg: TMsg
    ): LRESULT; stdcall; external
    DLL_USER32 name 'DispatchMessageA';

function DefWindowProcA(
    hWnd:   HWND;
    uMsg:   UINT;
    wParam: WPARAM;
    lParam: LPARAM
    ): LRESULT; stdcall; external
    DLL_USER32 name 'DefWindowProcA';

procedure PostQuitMessage(
    nExitCode: Integer
    ); stdcall; external
    DLL_USER32 name 'PostQuitMessage';

function MessageBoxA(
    hWnd:      HWND;
    lpText:    PAnsiChar;
    lpCaption: PAnsiChar;
    uType:     UINT
    ): Integer; stdcall; external
    DLL_USER32 name 'MessageBoxA';

implementation

end.
