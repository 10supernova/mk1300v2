# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for MK1300 Windows CLI installer.
Build on a Windows machine with:
    pyinstaller mk1300-win.spec
"""

block_cipher = None

a = Analysis(
    ["mk1300-win.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # Embed the whole mk1300 package
        ("mk1300/effects.py",        "mk1300"),
        ("mk1300/extra_effects.py",  "mk1300"),
        ("mk1300/categories.py",     "mk1300"),
        ("mk1300/driver.py",         "mk1300"),
        ("mk1300/layout.py",         "mk1300"),
        ("mk1300/keycodes.py",       "mk1300"),
        ("mk1300/cli.py",            "mk1300"),
        ("mk1300/config.py",         "mk1300"),
        ("mk1300/theme.py",          "mk1300"),
        ("mk1300/__init__.py",       "mk1300"),
        # Embed resources
        ("resources/antrgb.svg",     "resources"),
        ("LICENSE",                  "."),
        ("NOTICE",                   "."),
        ("README.md",                "."),
    ],
    hiddenimports=["hid", "hidapi"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude Linux-only / GTK4 UI modules to keep the exe small
        "gi",
        "cairo",
        "gi.repository",
        "gi.repository.Gtk",
        "gi.repository.Adw",
        "gi.repository.Gdk",
        "gi.repository.GLib",
        "gi.repository.GObject",
        "mk1300.ui",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="mk1300-win",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,          # CLI app — keep console window open
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,             # Add .ico here if you have one: icon="resources/antrgb.ico"
)
