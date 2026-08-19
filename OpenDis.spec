# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo,
    FixedFileInfo,
    StringFileInfo,
    StringTable,
    StringStruct,
    VarFileInfo,
    VarStruct,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

APP_NAME = "OpenDis"
VERSION = "1.0.0"
COMPANY = "MagnataTile"

BASE_DIR = Path.cwd()


# ============================================================
# CUSTOMTKINTER
# ============================================================

datas, binaries, hiddenimports = collect_all(
    "customtkinter"
)


# ============================================================
# INFORMAÇÕES DO EXECUTÁVEL WINDOWS
# ============================================================

version_info = VSVersionInfo(

    ffi=FixedFileInfo(
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),

    kids=[

        StringFileInfo(
            [
                # =================================================
                # PORTUGUÊS (BRASIL)
                # 0416 = Portuguese (Brazil)
                # 04B0 = Unicode
                # =================================================

                StringTable(
                    "041604B0",

                    [

                        StringStruct(
                            "CompanyName",
                            "MagnataTile"
                        ),

                        StringStruct(
                            "FileDescription",
                            "OpenVPN <+> Discord"
                        ),

                        StringStruct(
                            "FileVersion",
                            "1.0.0.0"
                        ),

                        StringStruct(
                            "InternalName",
                            "OpenDis"
                        ),

                        StringStruct(
                            "LegalCopyright",
                            "Copyright (C) 2026 MagnataTile"
                        ),

                        StringStruct(
                            "OriginalFilename",
                            "OpenDis.exe"
                        ),

                        StringStruct(
                            "ProductName",
                            "OpenDis"
                        ),

                        StringStruct(
                            "ProductVersion",
                            "1.0.0.0"
                        ),

                        StringStruct(
                            "Comments",
                            "OpenVPN Community + Discord"
                        ),

                    ],
                )
            ]
        ),

        # ========================================================
        # PORTUGUÊS - BRASIL
        # ========================================================

        VarFileInfo(
            [
                VarStruct(
                    "Translation",
                    [1046, 1200]
                )
            ]
        ),

    ],
)


# ============================================================
# ANALYSIS
# ============================================================

a = Analysis(
    [
        str(BASE_DIR / "opendis.py")
    ],

    pathex=[
        str(BASE_DIR)
    ],

    binaries=binaries,

    datas=datas,

    hiddenimports=hiddenimports,

    hookspath=[],

    hooksconfig={},

    runtime_hooks=[],

    excludes=[],

    noarchive=False,

    optimize=0,
)


# ============================================================
# PYZ
# ============================================================

pyz = PYZ(
    a.pure
)


# ============================================================
# EXECUTÁVEL
# ============================================================

exe = EXE(

    pyz,

    a.scripts,

    a.binaries,

    a.datas,

    [],

    # ========================================================
    # NOME
    # ========================================================

    name="OpenDis_",

    # ========================================================
    # DEBUG
    # ========================================================

    debug=False,

    bootloader_ignore_signals=False,

    # ========================================================
    # OTIMIZAÇÃO
    # ========================================================

    strip=False,

    upx=True,

    upx_exclude=[],

    # ========================================================
    # RUNTIME
    # ========================================================

    runtime_tmpdir=None,

    # ========================================================
    # JANELA
    # ========================================================

    console=False,

    disable_windowed_traceback=False,

    argv_emulation=False,

    # ========================================================
    # PLATAFORMA
    # ========================================================

    target_arch=None,

    # ========================================================
    # ASSINATURA
    # ========================================================

    codesign_identity=None,

    entitlements_file=None,

    # ========================================================
    # ÍCONE
    # ========================================================

    icon=str(BASE_DIR / "OpenDis.ico"),

    # ========================================================
    # METADADOS
    # ========================================================

    version=version_info,
)