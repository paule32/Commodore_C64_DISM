# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['d64_dism.py'],
    pathex      = [],
    binaries    = [
        ( "c64c/include"        , "c64c/include" ),
        ("examples"             , "examples"),
        ("runtime/graphics"     , "runtime/graphics"),
        ("runtime/pascal/test"  , "runtime/pascal/test"),
        ("C64Pro.ttf"           , "."),
        ("d64qt5.dll"           , "."),
        ("libgcc_s_dw2-1.dll"   , "."),
        ("libstdc++-6.dll"      , "."),
        ("libwinpthread-1.dll"  , "."),
    ],
    datas           = [],
    hiddenimports   = [],
    hookspath       = [],
    hooksconfig     = {},
    runtime_hooks   = [],
    excludes        = [],
    noarchive       = False,
    optimize        = 0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries            = True,
    name                        = 'd64_dism',
    debug                       = False,
    bootloader_ignore_signals   = False,
    strip                       = False,
    upx                         = True,
    console                     = True,
    disable_windowed_traceback  = False,
    argv_emulation              = False,
    target_arch                 = None,
    codesign_identity           = None,
    entitlements_file           = None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip           = False,
    upx             = True,
    upx_exclude     = [],
    name            = 'd64_dism',
)
