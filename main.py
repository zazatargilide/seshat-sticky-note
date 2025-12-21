#main.py
import sys
import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disk-cache-size=1"
from PyQt6.QtWidgets import QApplication
from app import StickyNote

if __name__ == "__main__":
    # Фиксы для экрана (High-DPI и Color Profile)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.screen=false" 
    
    app = QApplication(sys.argv)
    window = StickyNote()
    sys.exit(app.exec())