"""Configurações gerais"""
import os
import sys

if sys.platform == 'win32':
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass

os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'

DATABASE_NAME = 'equip_control.db'
DEFAULT_THEME = "light"
