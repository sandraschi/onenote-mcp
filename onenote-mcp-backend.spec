# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for onenote-mcp backend sidecar (fleet standard)."""

from PyInstaller.utils.hooks import copy_metadata

pkg_name = "onenote_mcp"

datas = [(f"src/onenote_mcp", "onenote_mcp")]
for pkg in (
    "fastmcp",
    "mcp",
    "uvicorn",
    "pydantic",
    "starlette",
    "httpx",
):
    datas += copy_metadata(pkg)

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "_strptime",
    "_datetime",
    "joserfc",
    "joserfc.jwk",
    "joserfc.jwt",
    # setuptools/pkg_resources runtime hook needs these; PyInstaller does not
    # auto-detect them (ModuleNotFoundError: No module named 'jaraco.text').
    "jaraco.text",
    "jaraco.context",
    "jaraco.functools",
]

a = Analysis(
    ["run_server.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pandas", "scipy", "torch", "tensorflow"],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="onenote-mcp-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
