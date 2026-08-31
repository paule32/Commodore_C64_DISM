// ---------------------------------------------------------------------------
// File:   Windows.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
unit Windows.Types;
interface
uses System.Types;

const
    // Window messages
    WM_NCCREATE         = $0081;
    WM_NCDESTROY        = $0082;
    
    WM_CREATE           = $0001;
    WM_DESTROY          = $0002;
    WM_COMMAND          = $0111;
    
    GWL_USERDATA        = -21;

    // Window class styles
    CS_REDRAW           = $0003;        // CS_VREDRAW or CS_HREDRAW

    // Window/control styles
    WS_OVERLAPPEDWINDOW = $00CF0000;
    
    WS_TABSTOP          = $00010000;
    WS_CLIPSIBLINGS     = $04000000;
    WS_DISABLED         = $08000000;
    WS_VISIBLE          = $10000000;
    WS_CHILD            = $40000000;
    WS_BUTTON           = $50010000;    // WS_CHILD | WS_VISIBLE | WS_TABSTOP

    // CreateWindow defaults
    CW_USEDEFAULT       = $0; //-2147483648;

    // Stock resources
    IDI_APPLICATION     = 32512;
    IDC_ARROW           = 32512;
    COLOR_WINDOW        = 5;

    // ShowWindow
    SW_HIDE             =  0;
    SW_SHOW             =  5;
    SW_SHOWDEFAULT      = 10;

    // MessageBox
    MB_OK               = $00000000;
    MB_ICONERROR        = $00000010;
    MB_ICONINFORMATION  = $00000040;

    // PushButton style
    BS_PUSHBUTTON       = $00000000;
    
type
    BOOL      = Integer;
    UINT      = Integer;
    DWORD     = Integer;
    LONG      = Integer;
    WPARAM    = Integer;
    LPARAM    = Integer;
    LRESULT   = Integer;

    HANDLE    = Integer;
    HINSTANCE = Integer;
    HMODULE   = Integer;
    HWND      = Integer;
    HICON     = Integer;
    HCURSOR   = Integer;
    HBRUSH    = Integer;
    HMENU     = Integer;

    TPoint = record
        x: LONG;
        y: LONG;
    end;

    TMsg = record
        hwnd:    HWND;
        message: UINT;
        wParam:  WPARAM;
        lParam:  LPARAM;
        time:    DWORD;
        pt:      TPoint;
    end;

    PCREATESTRUCTA  = ^TCREATESTRUCTA;
    LPCREATESTRUCTA = PCREATESTRUCTA;

    TCREATESTRUCTA = record
        lpCreateParams: Pointer;
        hInstance:      HINSTANCE;
        hMenu:          HMENU;
        hwndParent:     HWND;
        cy:             Integer;
        cx:             Integer;
        y:              Integer;
        x:              Integer;
        style:          LongInt;
        lpszName:       PAnsiChar;
        lpszClass:      PAnsiChar;
        dwExStyle:      LongWord;
    end;

    TWndClassA = record
        style:         UINT;
        lpfnWndProc:   Pointer;
        cbClsExtra:    Integer;
        cbWndExtra:    Integer;
        hInstance:     HINSTANCE;
        hIcon:         HICON;
        hCursor:       HCURSOR;
        hbrBackground: HBRUSH;
        lpszMenuName:  PAnsiChar;
        lpszClassName: PAnsiChar;
    end;

implementation
end.
