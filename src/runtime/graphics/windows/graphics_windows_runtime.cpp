#define WIN32_LEAN_AND_MEAN
#define D64_GRAPHICS_RUNTIME_EXPORTS 1
#include <windows.h>
#include <stdint.h>
#include <string.h>
#include "graphics_windows.h"

#if defined(__D64_GRAPHICS_DIRECT3D__)
# include <d3d9.h>
#else
# include <d2d1.h>
# include <dxgiformat.h>
#endif

static HWND g_hwnd = 0;
static uint32_t g_pixels[320 * 200];
static uint32_t g_logical_pixels[320 * 200];
static unsigned int g_present_divider = 0;
static unsigned int g_text_foreground = 1;
static unsigned int g_text_background = 0;

static const uint32_t g_c64_palette[16] = {
    0x000000,0xFFFFFF,0x883932,0x67B6BD,
    0x8B3F96,0x55A049,0x40318D,0xBFCE72,
    0x8B5429,0x574200,0xB86962,0x505050,
    0x787878,0x94E089,0x7869C4,0x9F9F9F
};

static uint32_t d64_color(unsigned int value)
{
    if (value < 16) value = g_c64_palette[value];
    return 0xFF000000u | (value & 0x00FFFFFFu);
}

static LRESULT CALLBACK d64_wndproc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    if (msg == WM_CLOSE) { DestroyWindow(hwnd); return 0; }
    if (msg == WM_DESTROY) { g_hwnd = 0; return 0; }
    return DefWindowProcA(hwnd, msg, wp, lp);
}

static void d64_pump_messages(void)
{
    MSG msg;
    while (PeekMessageA(&msg, 0, 0, 0, PM_REMOVE)) {
        TranslateMessage(&msg);
        DispatchMessageA(&msg);
    }
}

#if defined(__D64_GRAPHICS_DIRECT3D__)
static IDirect3D9 *g_d3d = 0;
static IDirect3DDevice9 *g_device = 0;

static int d64_create_renderer(void)
{
    D3DPRESENT_PARAMETERS pp;
    ZeroMemory(&pp, sizeof(pp));
    pp.Windowed = TRUE;
    pp.SwapEffect = D3DSWAPEFFECT_DISCARD;
    pp.hDeviceWindow = g_hwnd;
    pp.BackBufferWidth = 640;
    pp.BackBufferHeight = 400;
    pp.BackBufferFormat = D3DFMT_X8R8G8B8;
    pp.PresentationInterval = D3DPRESENT_INTERVAL_ONE;
    pp.Flags = D3DPRESENTFLAG_LOCKABLE_BACKBUFFER;

    g_d3d = Direct3DCreate9(D3D_SDK_VERSION);
    if (!g_d3d) return 0;
    if (FAILED(g_d3d->CreateDevice(
        D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, g_hwnd,
        D3DCREATE_SOFTWARE_VERTEXPROCESSING, &pp, &g_device))) {
        return 0;
    }
    return 1;
}

static void d64_present(void)
{
    if (!g_device || !g_hwnd) return;
    IDirect3DSurface9 *back = 0;
    if (FAILED(g_device->GetBackBuffer(0, 0, D3DBACKBUFFER_TYPE_MONO, &back))) return;
    D3DLOCKED_RECT lock;
    if (SUCCEEDED(back->LockRect(&lock, 0, 0))) {
        for (int y = 0; y < 400; ++y) {
            uint32_t *dst = (uint32_t *)((unsigned char *)lock.pBits + y * lock.Pitch);
            const uint32_t *src = &g_pixels[(y >> 1) * 320];
            for (int x = 0; x < 640; ++x) dst[x] = src[x >> 1];
        }
        back->UnlockRect();
    }
    back->Release();
    g_device->Present(0, 0, 0, 0);
    d64_pump_messages();
}

static void d64_destroy_renderer(void)
{
    if (g_device) { g_device->Release(); g_device = 0; }
    if (g_d3d) { g_d3d->Release(); g_d3d = 0; }
}
#else
static ID2D1Factory *g_factory = 0;
static ID2D1HwndRenderTarget *g_target = 0;
static ID2D1Bitmap *g_bitmap = 0;

static int d64_create_renderer(void)
{
    HRESULT hr = D2D1CreateFactory(D2D1_FACTORY_TYPE_SINGLE_THREADED, &g_factory);
    if (FAILED(hr)) return 0;
    D2D1_RENDER_TARGET_PROPERTIES props = D2D1::RenderTargetProperties();
    D2D1_HWND_RENDER_TARGET_PROPERTIES hwndProps =
        D2D1::HwndRenderTargetProperties(g_hwnd, D2D1::SizeU(640, 400));
    hr = g_factory->CreateHwndRenderTarget(props, hwndProps, &g_target);
    if (FAILED(hr)) return 0;
    D2D1_BITMAP_PROPERTIES bp = D2D1::BitmapProperties(
        D2D1::PixelFormat(DXGI_FORMAT_B8G8R8A8_UNORM, D2D1_ALPHA_MODE_IGNORE));
    hr = g_target->CreateBitmap(D2D1::SizeU(320, 200), 0, 0, &bp, &g_bitmap);
    return SUCCEEDED(hr);
}

static void d64_present(void)
{
    if (!g_target || !g_bitmap || !g_hwnd) return;
    g_bitmap->CopyFromMemory(0, g_pixels, 320 * 4);
    g_target->BeginDraw();
    g_target->Clear(D2D1::ColorF(D2D1::ColorF::Black));
    g_target->DrawBitmap(
        g_bitmap,
        D2D1::RectF(0.0f, 0.0f, 640.0f, 400.0f),
        1.0f,
        D2D1_BITMAP_INTERPOLATION_MODE_NEAREST_NEIGHBOR);
    g_target->EndDraw();
    d64_pump_messages();
}

static void d64_destroy_renderer(void)
{
    if (g_bitmap) { g_bitmap->Release(); g_bitmap = 0; }
    if (g_target) { g_target->Release(); g_target = 0; }
    if (g_factory) { g_factory->Release(); g_factory = 0; }
}
#endif

D64_GRAPHICS_API void SetTextColor(unsigned int foreground, unsigned int background)
{
    g_text_foreground = foreground;
    g_text_background = background;
}

D64_GRAPHICS_API void InitGraphics(void)
{
    WNDCLASSEXA wc;
    ZeroMemory(&wc, sizeof(wc));
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = d64_wndproc;
    wc.hInstance = GetModuleHandleA(0);
    wc.hCursor = LoadCursorA(0, IDC_ARROW);
    wc.lpszClassName = "dBase2ManyGraphicsWindow";
    RegisterClassExA(&wc);
    g_hwnd = CreateWindowExA(
        0, wc.lpszClassName, "dBase2Many - 320x200 Graphics",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT, 656, 439,
        0, 0, wc.hInstance, 0);
    memset(g_pixels, 0, sizeof(g_pixels));
    memset(g_logical_pixels, 0, sizeof(g_logical_pixels));
    d64_create_renderer();
    d64_present();
}

D64_GRAPHICS_API void DoneGraphics(TextMode mode)
{
    (void)mode;
    d64_present();
    d64_destroy_renderer();
    if (g_hwnd) { DestroyWindow(g_hwnd); g_hwnd = 0; }
}

D64_GRAPHICS_API void ClearScreen(void)
{
    const unsigned int color = 0;
    uint32_t value = d64_color(color);
    for (int i = 0; i < 320 * 200; ++i) {
        g_pixels[i] = value;
        g_logical_pixels[i] = color;
    }
    d64_present();
}

D64_GRAPHICS_API void SetPixel(int x, int y, GraphicsColor color)
{
    if ((unsigned)x >= 320u || (unsigned)y >= 200u) return;
    g_pixels[y * 320 + x] = d64_color(color);
    g_logical_pixels[y * 320 + x] = color;
    if ((++g_present_divider & 255u) == 0u) d64_present();
}

D64_GRAPHICS_API GraphicsColor GetPixel(int x, int y)
{
    if ((unsigned)x >= 320u || (unsigned)y >= 200u) return 0;
    return (GraphicsColor)(g_logical_pixels[y * 320 + x] & 0xFFu);
}

D64_GRAPHICS_API void DrawLine(int x1,int y1,int x2,int y2,GraphicsColor c)
{
    int dx = x2 > x1 ? x2-x1 : x1-x2;
    int sx = x1 < x2 ? 1 : -1;
    int dy = -(y2 > y1 ? y2-y1 : y1-y2);
    int sy = y1 < y2 ? 1 : -1;
    int err = dx + dy;
    for (;;) {
        SetPixel(x1,y1,c);
        if (x1 == x2 && y1 == y2) break;
        int e2 = err << 1;
        if (e2 >= dy) { err += dy; x1 += sx; }
        if (e2 <= dx) { err += dx; y1 += sy; }
    }
    d64_present();
}

D64_GRAPHICS_API void DrawRect(int x1,int y1,int x2,int y2,GraphicsColor c)
{
    DrawLine(x1,y1,x2,y1,c); DrawLine(x2,y1,x2,y2,c);
    DrawLine(x2,y2,x1,y2,c); DrawLine(x1,y2,x1,y1,c);
}

D64_GRAPHICS_API void FillRect(int x1,int y1,int x2,int y2,GraphicsColor fill,
              GraphicsColor border,unsigned int bw)
{
    if (x1 > x2) { int t=x1; x1=x2; x2=t; }
    if (y1 > y2) { int t=y1; y1=y2; y2=t; }
    for (int y=y1;y<=y2;++y) for (int x=x1;x<=x2;++x) SetPixel(x,y,fill);
    for (int i=0;i<bw;++i) DrawRect(x1+i,y1+i,x2-i,y2-i,border);
    d64_present();
}

D64_GRAPHICS_API void DrawCircle(int cx,int cy,int r,GraphicsColor c)
{
    int x=r,y=0,d=1-r;
    while (x>=y) {
        SetPixel(cx+x,cy+y,c);SetPixel(cx-x,cy+y,c);
        SetPixel(cx+x,cy-y,c);SetPixel(cx-x,cy-y,c);
        SetPixel(cx+y,cy+x,c);SetPixel(cx-y,cy+x,c);
        SetPixel(cx+y,cy-x,c);SetPixel(cx-y,cy-x,c);
        ++y; if (d<0) d+=2*y+1; else { --x; d+=2*(y-x)+1; }
    }
    d64_present();
}

D64_GRAPHICS_API void FillCircle(int cx,int cy,int r,GraphicsColor fill,
                GraphicsColor border,unsigned int bw)
{
    for (int y=-r;y<=r;++y) {
        int xx=0; while ((xx+1)*(xx+1)+y*y<=r*r) ++xx;
        DrawLine(cx-xx,cy+y,cx+xx,cy+y,fill);
    }
    for (int i=0;i<bw;++i) DrawCircle(cx,cy,r-i,border);
    d64_present();
}

static void d64_hline(int x1, int y, int x2, GraphicsColor color)
{
    if (y < 0 || y >= GRAPHICS_HEIGHT) return;
    if (x1 > x2) { int t=x1; x1=x2; x2=t; }
    if (x1 < 0) x1 = 0;
    if (x2 >= GRAPHICS_WIDTH) x2 = GRAPHICS_WIDTH - 1;
    for (int x=x1; x<=x2; ++x) SetPixel(x,y,color);
}

D64_GRAPHICS_API void FloodFill(int x, int y, GraphicsColor fillColor)
{
    if ((unsigned)x >= GRAPHICS_WIDTH || (unsigned)y >= GRAPHICS_HEIGHT) return;
    GraphicsColor source = GetPixel(x,y);
    if (source == fillColor) return;

    enum { STACK_SIZE = GRAPHICS_WIDTH * GRAPHICS_HEIGHT };
    static int xs[STACK_SIZE];
    static int ys[STACK_SIZE];
    int top = 0;
    xs[top] = x; ys[top] = y; ++top;
    while (top > 0) {
        --top;
        int cx = xs[top], cy = ys[top];
        if ((unsigned)cx >= GRAPHICS_WIDTH || (unsigned)cy >= GRAPHICS_HEIGHT) continue;
        if (GetPixel(cx,cy) != source) continue;
        SetPixel(cx,cy,fillColor);
        if (top + 4 < STACK_SIZE) {
            xs[top]=cx-1; ys[top]=cy; ++top;
            xs[top]=cx+1; ys[top]=cy; ++top;
            xs[top]=cx; ys[top]=cy-1; ++top;
            xs[top]=cx; ys[top]=cy+1; ++top;
        }
    }
    d64_present();
}

D64_GRAPHICS_API void DrawTriangle(int x1,int y1,int x2,int y2,int x3,int y3,GraphicsColor color)
{
    DrawLine(x1,y1,x2,y2,color);
    DrawLine(x2,y2,x3,y3,color);
    DrawLine(x3,y3,x1,y1,color);
    d64_present();
}

static void d64_thick_line(int x1,int y1,int x2,int y2,GraphicsColor color,unsigned int width)
{
    if (width <= 1u) { DrawLine(x1,y1,x2,y2,color); return; }
    int dx = x2>x1 ? x2-x1 : x1-x2;
    int dy = y2>y1 ? y2-y1 : y1-y2;
    int half = (int)(width/2u);
    if (dx >= dy) {
        for (int o=-half;o<=half;++o) DrawLine(x1,y1+o,x2,y2+o,color);
    } else {
        for (int o=-half;o<=half;++o) DrawLine(x1+o,y1,x2+o,y2,color);
    }
}

D64_GRAPHICS_API void FillTriangle(int x1,int y1,int x2,int y2,int x3,int y3,
                                   GraphicsColor fillColor,GraphicsColor borderColor,
                                   unsigned int borderWidth)
{
    int t;
    if (y1>y2) { t=y1;y1=y2;y2=t; t=x1;x1=x2;x2=t; }
    if (y2>y3) { t=y2;y2=y3;y3=t; t=x2;x2=x3;x3=t; }
    if (y1>y2) { t=y1;y1=y2;y2=t; t=x1;x1=x2;x2=t; }
    if (y1==y3) {
        int lo=x1, hi=x1;
        if (x2<lo) lo=x2; if (x3<lo) lo=x3;
        if (x2>hi) hi=x2; if (x3>hi) hi=x3;
        d64_hline(lo,y1,hi,fillColor);
    } else {
        for (int y=y1;y<=y3;++y) {
            int a, b;
            if (y<y2 && y2!=y1) a=x1+((x2-x1)*(y-y1))/(y2-y1);
            else if (y3!=y2) a=x2+((x3-x2)*(y-y2))/(y3-y2);
            else a=x2;
            b=x1+((x3-x1)*(y-y1))/(y3-y1);
            /* Draw span regardless of edge ordering. */
            if (a<=b) d64_hline(a,y,b,fillColor); else d64_hline(b,y,a,fillColor);
        }
    }
    if (borderWidth) {
        d64_thick_line(x1,y1,x2,y2,borderColor,borderWidth);
        d64_thick_line(x2,y2,x3,y3,borderColor,borderWidth);
        d64_thick_line(x3,y3,x1,y1,borderColor,borderWidth);
    }
    d64_present();
}

static int d64_sine_quarter(unsigned int index)
{
    static const int table[19] = {0,22,44,66,88,108,128,147,165,181,196,210,222,232,241,247,252,255,256};
    return table[index <= 18u ? index : 18u];
}

static int d64_sin_deg(int angle)
{
    while (angle < 0) angle += 360;
    while (angle >= 360) angle -= 360;
    unsigned int quadrant=(unsigned int)angle/90u;
    unsigned int remainder=(unsigned int)angle%90u;
    if (quadrant==1u || quadrant==3u) remainder=90u-remainder;
    unsigned int index=(remainder+2u)/5u;
    int value=d64_sine_quarter(index);
    if (quadrant>=2u) value=-value;
    return value;
}
static int d64_cos_deg(int angle) { return d64_sin_deg(angle+90); }

D64_GRAPHICS_API void DrawTriangleAngles(int centerX,int centerY,
                                         int radius1,int radius2,int radius3,
                                         int angle1,int angle2,int angle3,
                                         GraphicsColor color)
{
    int x1=centerX+(d64_cos_deg(angle1)*radius1)/256;
    int y1=centerY+(d64_sin_deg(angle1)*radius1)/256;
    int x2=centerX+(d64_cos_deg(angle2)*radius2)/256;
    int y2=centerY+(d64_sin_deg(angle2)*radius2)/256;
    int x3=centerX+(d64_cos_deg(angle3)*radius3)/256;
    int y3=centerY+(d64_sin_deg(angle3)*radius3)/256;
    DrawTriangle(x1,y1,x2,y2,x3,y3,color);
}

