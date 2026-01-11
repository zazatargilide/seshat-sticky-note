# main.py

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app import StickyNote

# 1. Эта функция делает EXE автономным.
# Она ищет файлы внутри EXE, если программа упакована.
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS # Эта папка создается временно при запуске EXE
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disk-cache-size=1"

if __name__ == "__main__":
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)

    # 2. Устанавливаем иконку глобально для всего приложения сразу здесь
    # Используем нашу функцию, чтобы найти иконку внутри EXE
    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = StickyNote()
    # В ui_setup.py теперь можно вообще убрать установку иконки, 
    # так как мы задали её глобально для app выше.
    
    sys.exit(app.exec())