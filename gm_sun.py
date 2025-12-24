#gm_sun.py

from PyQt6.QtWidgets import QGraphicsItem
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QColor, QPen, QBrush, QPainter, QFont, QRadialGradient, QLinearGradient

class SunItem(QGraphicsItem):
    def __init__(self, title, accent_color, progress_ratio, pin_callback):
        super().__init__()
        self.title = title
        self.accent = QColor(accent_color)
        self.progress = max(0.0, min(1.0, progress_ratio))
        self.pin_callback = pin_callback
        
        self.pinned = False
        self.is_hovered = False
        
        # Базовый размер, будет обновлен извне
        self.radius = 400
        self.update_geometry_rects()
        
        self.current_scale = 1.0
        self.target_scale = 1.0
        
        self.setAcceptHoverEvents(True)
        self.setZValue(-10) 

    def update_size(self, new_radius):
        """Динамическое изменение размера Солнца"""
        self.radius = new_radius
        self.update_geometry_rects()
        self.update()

    def update_geometry_rects(self):
        self.rect = QRectF(-self.radius, -self.radius, self.radius*2, self.radius*2)
        # Аура пропорциональна радиусу
        aura_gap = self.radius * 0.3
        self.aura_rect = self.rect.adjusted(-aura_gap, -aura_gap, aura_gap, aura_gap)

    def boundingRect(self):
        return self.aura_rect.adjusted(-200, -200, 200, 200)

    def set_progress(self, new_ratio):
        self.progress = max(0.0, min(1.0, new_ratio))
        self.update()

    def advance(self, phase):
        if not phase: return
        if abs(self.current_scale - self.target_scale) > 0.001:
            self.current_scale += (self.target_scale - self.current_scale) * 0.05
            self.setScale(self.current_scale)

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        if not self.pinned: self.target_scale = 1.05
        self.update()

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        if not self.pinned: self.target_scale = 1.0
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.pinned = not self.pinned
            self.pin_callback(self if self.pinned else None)
            self.set_pinned_visual(self.pinned)

    def set_pinned_visual(self, is_pinned):
        self.pinned = is_pinned
        self.target_scale = 1.2 if self.pinned else (1.05 if self.is_hovered else 1.0)
        self.update()

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = QPointF(0,0)
        
        # 1. АУРА
        extra_glow = 150 if self.pinned else (100 if self.is_hovered else 0)
        glow_radius = (self.radius * 1.5) + extra_glow
        
        glow = QRadialGradient(center, glow_radius)
        glow.setColorAt(0.4, QColor(0,0,0,0))
        
        glow_alpha = 120 if self.pinned else (100 if self.is_hovered else 80)
        glow_col = QColor(self.accent)
        glow_col.setAlpha(glow_alpha)
        
        glow.setColorAt(0.75, glow_col)
        glow.setColorAt(1.0, QColor(0,0,0,0))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(center, glow_radius, glow_radius)

        # 2. ПРОГРЕСС
        pen_width = self.radius * 0.08 # Толщина зависит от размера
        ring_rect = self.rect.adjusted(pen_width/2, pen_width/2, -pen_width/2, -pen_width/2)
        
        bg_grad = QLinearGradient(ring_rect.topLeft(), ring_rect.bottomRight())
        bg_grad.setColorAt(0, QColor(60, 60, 60, 100))
        bg_grad.setColorAt(1, QColor(30, 30, 30, 50))
        bg_pen = QPen(QBrush(bg_grad), pen_width); bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen); painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(ring_rect, 0, 360 * 16)
        
        if self.progress > 0:
            prog_grad = QLinearGradient(ring_rect.topLeft(), ring_rect.bottomRight())
            prog_grad.setColorAt(0, self.accent.lighter(120))
            prog_grad.setColorAt(1, self.accent.darker(110))
            prog_pen = QPen(QBrush(prog_grad), pen_width); prog_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(prog_pen)
            start_angle = 90 * 16
            span_angle = int(-self.progress * 360 * 16)
            painter.drawArc(ring_rect, start_angle, span_angle)

        # 3. ЯДРО
        core_rect = ring_rect.adjusted(pen_width/2 + 10, pen_width/2 + 10, -pen_width/2 - 10, -pen_width/2 - 10)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(core_rect)
        
        # 4. ТЕКСТ
        base_font_size = self.radius * 0.15
        font_size = base_font_size * 1.2 if self.pinned else base_font_size
        font = QFont("Arial", int(font_size), QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 110)
        painter.setFont(font); painter.setPen(QColor("#000000")) 
        painter.drawText(core_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, self.title)
        
        font_small = QFont("Arial", int(base_font_size * 0.6))
        painter.setFont(font_small)
        percent_rect = core_rect.adjusted(0, self.radius * 0.4, 0, 0)
        painter.drawText(percent_rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.progress*100)}%")