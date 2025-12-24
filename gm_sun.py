import math
from PyQt6.QtWidgets import QGraphicsItem
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (QColor, QPen, QBrush, QPainter, QFont, 
                         QRadialGradient, QLinearGradient, QPainterPath, QFontMetrics)

class SunItem(QGraphicsItem):
    def __init__(self, title, accent_color, progress_ratio, pin_callback):
        super().__init__()
        self.title = title
        self.accent = QColor(accent_color)
        self.progress = max(0.0, min(1.0, progress_ratio))
        self.pin_callback = pin_callback
        
        self.pinned = False
        self.is_hovered = False
        
        self.radius = 400
        self.update_geometry_rects()
        
        self.current_scale = 1.0
        self.target_scale = 1.0
        self.pulse_phase = 0.0
        
        self.setAcceptHoverEvents(True)
        self.setZValue(-10) 

    def update_size(self, new_radius):
        self.radius = new_radius
        self.update_geometry_rects()
        self.update()

    def update_geometry_rects(self):
        self.rect = QRectF(-self.radius, -self.radius, self.radius*2, self.radius*2)
        aura_gap = self.radius * 0.8
        self.aura_rect = self.rect.adjusted(-aura_gap, -aura_gap, aura_gap, aura_gap)

    def boundingRect(self):
        return self.aura_rect

    def set_progress(self, new_ratio):
        self.progress = max(0.0, min(1.0, new_ratio))
        self.update()

    def advance(self, phase):
        if not phase: return
        
        if abs(self.current_scale - self.target_scale) > 0.001:
            self.current_scale += (self.target_scale - self.current_scale) * 0.05
            self.setScale(self.current_scale)
            
        self.pulse_phase += 0.02
        self.update()

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
        
        base_glow_alpha = 100
        if self.is_hovered or self.pinned:
            base_glow_alpha = 160
            
        pulse = (math.sin(self.pulse_phase) + 1) / 2 
        
        # --- 1. СВЕЧЕНИЕ ---
        layers = [
            (1.8, 0.4, 0.05),
            (1.5, 0.7, 0.08),
            (1.2, 1.0, 0.10)
        ]
        
        painter.setPen(Qt.PenStyle.NoPen)
        for r_mult, a_mult, p_eff in layers:
            current_r = self.radius * (r_mult + pulse * p_eff)
            grad = QRadialGradient(QPointF(0,0), current_r)
            col = QColor(self.accent)
            alpha = int(base_glow_alpha * a_mult * (0.8 + pulse * 0.2))
            col.setAlpha(min(255, alpha))
            grad.setColorAt(self.radius / current_r, col) 
            grad.setColorAt(1.0, QColor(0,0,0,0)) 
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(QPointF(0,0), current_r, current_r)

        # --- 2. ПРОГРЕСС ---
        pen_width = self.radius * 0.08
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

        # --- 3. ЯДРО ---
        core_rect = ring_rect.adjusted(pen_width/2 + 10, pen_width/2 + 10, -pen_width/2 - 10, -pen_width/2 - 10)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(core_rect)
        
        # --- 4. АДАПТИВНЫЙ ТЕКСТ ---
        # Максимально доступная ширина (с отступами внутри круга)
        available_width = core_rect.width() * 0.85 
        
        # Начинаем с шрифта побольше
        font_size = self.radius * 0.3 
        font = QFont("Arial", int(font_size), QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 105)
        
        fm = QFontMetrics(font)
        
        # Уменьшаем шрифт, пока текст не влезет или не станет слишком мелким
        min_font_size = 12
        while (fm.horizontalAdvance(self.title) > available_width) and (font_size > min_font_size):
            font_size -= 1.0
            font.setPointSize(int(font_size))
            fm = QFontMetrics(font)
            
        # Если все равно не влазит - обрезаем (Elide)
        elided_title = fm.elidedText(self.title, Qt.TextElideMode.ElideRight, int(available_width))
        
        painter.setFont(font)
        painter.setPen(QColor("#000000")) 
        
        # Рисуем по центру
        painter.drawText(core_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, elided_title)
        
        # Проценты внизу
        font_small = QFont("Arial", int(max(10, font_size * 0.5)))
        painter.setFont(font_small)
        # Смещаем вниз относительно центра
        percent_rect = core_rect.adjusted(0, self.radius * 0.5, 0, 0)
        painter.drawText(percent_rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.progress*100)}%")