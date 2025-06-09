#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for creating macOS app bundle using py2app
"""

from setuptools import setup, find_packages
import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

APP = ['main.py']
DATA_FILES = [
    ('assets', ['assets']),
    ('configs', ['configs']),
]

OPTIONS = {
    'argv_emulation': False,  # 禁用argv_emulation避免Carbon框架问题
    'iconfile': None,  # 如果有.icns图标文件，在这里指定路径
    'plist': {
        'CFBundleName': '多开浏览器管理工具',
        'CFBundleDisplayName': '多开浏览器管理工具',
        'CFBundleGetInfoString': '多开浏览器管理工具 v1.0.0',
        'CFBundleIdentifier': 'com.chromeprofilemanager.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024 Chrome Profile Manager',
        'NSRequiresAquaSystemAppearance': False,
        'LSBackgroundOnly': False,
        'NSHighResolutionCapable': True,
    },
    'packages': ['gui', 'core'],
    'includes': [
        'gui',
        'gui.main_window',
        'gui.icon_helper', 
        'gui.icon_generator',
        'core',
        'core.browser_manager',
        'core.profile_manager',
        'core.config_manager',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'psutil',
        'requests',
    ],
    'excludes': [
        'matplotlib', 'numpy', 'scipy', 'tkinter', 'test', 'tests',
        'PyQt5.QtWebEngine', 'PyQt5.QtWebEngineWidgets', 'PyQt5.QtNetwork',
        'PyQt5.QtXml', 'PyQt5.QtXmlPatterns', 'PyQt5.QtSql', 'PyQt5.QtTest',
        'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets', 'PyQt5.QtOpenGL',
        'PyQt5.QtPrintSupport', 'PyQt5.QtQml', 'PyQt5.QtQuick',
    ],
    'optimize': 2,
    'strip': True,  # 减小应用体积
    'site_packages': True,  # 包含site-packages
    'qt_plugins': [
        'platforms/libqcocoa.dylib',
        'platforms/libqminimal.dylib',
        'platforms/libqoffscreen.dylib',
        'imageformats',
        'iconengines',
        'styles',
    ],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    packages=find_packages(),
    install_requires=[
        'PyQt5>=5.15.0',
        'psutil>=5.9.0',
        'requests>=2.28.0',
    ],
) 