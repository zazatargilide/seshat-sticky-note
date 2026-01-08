# widgets.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFontMetrics, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QPushButton, QSizeGrip, QSizePolicy, QVBoxLayout, QWidget


# --- КЛАСС 1: РУЧНОЙ ГРИП ---
class CyberGrip(QSizeGrip):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0.0, QColor(30, 30, 30, 0))
        gradient.setColorAt(0.6, QColor("#505050"))
        gradient.setColorAt(1.0, QColor("#b0b0b0"))

        pen = QPen(QBrush(gradient), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        painter.setOpacity(0.4)
        painter.drawLine(w - 12, h - 2, w - 2, h - 12)
        painter.setOpacity(0.7)
        painter.drawLine(w - 8, h - 2, w - 2, h - 8)
        painter.setOpacity(1.0)
        painter.drawLine(w - 4, h - 2, w - 2, h - 4)


# --- КЛАСС 2: ЗАГОЛОВОК С ОБРЕЗАНИЕМ ---
class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.TextElideMode.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)


# --- КЛАСС 3: ПЛАВАЮЩАЯ КНОПКА ---
class FloatingUnlockBtn(QWidget):
    def __init__(self, callback=None):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn = QPushButton("⚿")
        self.btn.setFixedSize(24, 24)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)

        if callback:
            self.btn.clicked.connect(callback)

        self.btn.setStyleSheet("""
            QPushButton { 
                background: transparent; border: none; color: #757575; font-size: 18px; 
            } 
            QPushButton:hover { color: #e0e0e0; }
        """)
        layout.addWidget(self.btn)
        self.setFixedSize(24, 24)

    def set_color(self, color_hex):
        self.btn.setStyleSheet(f"""
            QPushButton {{ 
                background: transparent; border: none; color: {color_hex}; font-size: 18px; 
            }} 
            QPushButton:hover {{ color: #e0e0e0; }}
        """)


class TitleLabel(QLabel):
    # Создаем сигнал, который будем испускать при дабл-клике
    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        # Проверяем, что это была именно левая кнопка мыши
        if event.button() == Qt.MouseButton.LeftButton:
            self.doubleClicked.emit()

        # Обязательно вызываем родительский метод, чтобы не сломать стандартное поведение
        super().mouseDoubleClickEvent(event)
