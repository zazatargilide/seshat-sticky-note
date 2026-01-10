# main.py
import os
import sys
import ctypes

# Импортируем QIcon, чтобы программа не падала
from PyQt6.QtGui import QIcon 
from PyQt6.QtWidgets import QApplication

# Фикс кэша (твой старый код)
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disk-cache-size=1"

from app import StickyNote

if __name__ == "__main__":
    # --- 1. МАГИЯ ДЛЯ ИКОНКИ В ТАСКБАРЕ ---
    myappid = 'ata.seshat.stickynote.version.1.6.127' # Любая уникальная строка
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass

    # Фиксы для экрана
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.screen=false"

    app = QApplication(sys.argv)

    # --- 2. УСТАНОВКА ИКОНКИ ДЛЯ ВСЕГО ПРИЛОЖЕНИЯ ---
    # Вычисляем путь, чтобы иконка находилась железно
    basedir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(basedir, "icon.ico")
    
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = StickyNote()
    sys.exit(app.exec())