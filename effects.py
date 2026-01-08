# effects.py
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QColor


class RainbowManager(QObject):
    color_changed = pyqtSignal(str)

    def __init__(self, speed=20):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_color)
        self.timer.setInterval(speed)
        self.hue = 0

    def start(self):
        if not self.timer.isActive():
            self.timer.start()

    def stop(self):
        self.timer.stop()

    def _update_color(self):
        # 1. Скорость ргб флэша
        self.hue = (self.hue + 5) % 360

        # 2. Насыщенность перелива:
        # Saturation = 100 (было 200). Меньше - пастельное.
        # Value = 255 (макс).
        color = QColor.fromHsv(self.hue, 100, 255)

        self.color_changed.emit(color.name())
