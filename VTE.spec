# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Calculate repository / application root dynamically
try:
    APP_ROOT = os.path.abspath(SPECPATH)
except NameError:
    APP_ROOT = os.path.abspath(os.path.dirname(__file__)) if '__file__' in globals() else os.path.abspath('.')

# In case spec is executed from a subfolder such as build/VTE
if not os.path.exists(os.path.join(APP_ROOT, 'Tesseract-OCR')) and os.path.exists(os.path.join(APP_ROOT, '..', '..', 'Tesseract-OCR')):
    APP_ROOT = os.path.abspath(os.path.join(APP_ROOT, '..', '..'))

added_datas = [
    (os.path.join(APP_ROOT, 'app.ico'), '.'),
    (os.path.join(APP_ROOT, 'Tesseract-OCR'), 'Tesseract-OCR'),
]

a = Analysis(
    [os.path.join(APP_ROOT, 'VTE.py')],
    pathex=[APP_ROOT],
    binaries=[],
    datas=added_datas,
    hiddenimports=[
        'deep_translator',
        'googletrans',
        'pyttsx3',
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
        'pytesseract',
        'PIL',
        'PIL.ImageGrab',
        'PIL.ImageEnhance',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'mediapipe', 'opencv-python', 'opencv-contrib-python'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VTE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(APP_ROOT, 'app.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VTE',
)
