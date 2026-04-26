# -*- mode: python -*-
# PyInstaller spec for building standalone backend executable
# Usage: pyinstaller pyinstaller.spec

import sys
from pathlib import Path

block_cipher = None

added_files = [
    ('templates/*', 'templates'),
    ('backend/engine/prompts/*.py', 'engine/prompts'),
]

a = Analysis(
    ['backend/main.py'],
    pathex=['backend'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'engine.prompts.gaoxin',
        'engine.prompts.xiaojuren',
        'engine.checklist',
        'engine.preview',
        'engine.composer',
        'engine.routes',
        'engine.reviewer',
        'engine.exporter',
        'templates.builtin',
        'services.company_info',
        'services.web_search',
        'documents.parser',
        'documents.vector_store',
        'llm.base',
        'llm.claude',
        'llm.openai_adapter',
        'llm.gemini',
        'llm.qwen',
        'llm.qianfan_adapter',
        'llm.deepseek',
        'llm.zhipu',
        'llm.moonshot',
        'llm.custom',
        'llm.custom_store',
        'llm.registry',
        'models.project',
        'models.document',
        'models.database',
        'projects.routes',
        'documents.routes',
        'templates.routes',
        'chromadb',
        'sqlalchemy',
        'aiosqlite',
        'bs4',
        'docx',
        'openpyxl',
        'PyPDF2',
        'httpx',
        'pydantic_settings',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
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
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
