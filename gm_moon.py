import random
import math
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QMenu
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (QColor, QPen, QBrush, QPainter, QPainterPath, 
                         QPolygonF, QRadialGradient, QFont, QTransform, QPainterPathStroker)

class SubTaskMoonItem(QGraphicsItem):
    def __init__(self, data, accent_color, orbit_radius, start_angle, speed, status_callback=None):
        super().__init__()
        self.data = data
        self.accent = QColor(accent_color)
        self.text = data.get("text", "Moon")
        self.status_callback = status_callback
        
        self.is_done = data.get("checked", False)
        self.is_cancelled = data.get("cancelled", False)
        
        self.orbit_radius = orbit_radius
        self.current_angle = start_angle
        
        speed_var = random.uniform(0.8, 1.2)
        self.speed = (speed * speed_var) / 10.0
        
        text_bonus = min(len(self.text), 20) * 0.8 
        chaos_bonus = random.uniform(-25, 50)
        base_r = 40 + text_bonus + chaos_bonus
        self.radius = max(25, base_r)
        
        self.rect = QRectF(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        
        self.is_hovered = False
        self.is_title_pinned = False
        
        self.title_item = QGraphicsTextItem(self.text, self)
        font = QFont("Arial", 12, QFont.Weight.Bold)
        self.title_item.setFont(font)
        self.title_item.setDefaultTextColor(QColor("#ffffff"))
        txt_rect = self.title_item.boundingRect()
        self.title_item.setPos(-txt_rect.width() / 2, self.radius + 10)
        self.title_item.setVisible(False)

        self.features = []
        self.broken_body = None; self.shards = []; self.dust = []
        
        self.refresh_geometry()
        self.setAcceptHoverEvents(True)

    def sync_with_data(self):
        real_done = self.data.get("checked", False)
        real_cancel = self.data.get("cancelled", False)
        
        if self.is_cancelled != real_cancel:
            self.is_cancelled = real_cancel
            self.refresh_geometry()
            
        if self.is_done != real_done:
            self.is_done = real_done
            self.update()

    def refresh_geometry(self):
        self.features = []
        self.broken_body = None; self.shards = []; self.dust = []
        if self.is_cancelled:
            self._generate_unique_break()
            self._generate_cosmic_dust()
        else:
            num = random.randint(3, 6)
            for _ in range(num): self.features.append(self._generate_jagged_feature())
        self.update()

    def set_status(self, done=None, cancelled=None, from_parent=False, silent=False):
        changed = False
        
        if cancelled is not None and self.is_cancelled != cancelled:
            self.is_cancelled = cancelled
            self.data['cancelled'] = cancelled
            self.refresh_geometry()
            changed = True
            
        if done is not None and self.is_done != done:
            self.is_done = done
            self.data['checked'] = done
            changed = True
            
        if changed:
            self.update()
            if not from_parent and self.parentItem() and hasattr(self.parentItem(), 'on_moon_changed'):
                self.parentItem().on_moon_changed()
            if not silent and self.status_callback:
                self.status_callback()

    def set_show_title(self, visible):
        if visible:
            self.title_item.setVisible(True)
        else:
            self.title_item.setVisible(self.is_hovered or self.is_title_pinned)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_title_pinned = not self.is_title_pinned
            self.title_item.setVisible(self.is_title_pinned or self.is_hovered)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #202020; color: white; border: 1px solid #555; } QMenu::item:selected { background-color: #404040; }")
        action_done = menu.addAction("✅ Выполнено" if not self.is_done else "Вернуть в работу")
        action_cancel = menu.addAction("❌ Зачеркнуть" if not self.is_cancelled else "✨ Восстановить")
        res = menu.exec(event.screenPos())
        if res == action_done: self.set_status(done=not self.is_done)
        elif res == action_cancel:
            new_cancel = not self.is_cancelled
            self.set_status(cancelled=new_cancel, done=False if new_cancel else self.is_done)

    def advance(self, phase):
        if not phase: return
        self.current_angle += self.speed
        rad = math.radians(self.current_angle)
        x = self.orbit_radius * math.cos(rad); y = self.orbit_radius * math.sin(rad)
        self.setPos(x, y)

    def hoverEnterEvent(self, event):
        self.is_hovered = True; self.title_item.setVisible(True); self.update()
    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        if not self.is_title_pinned: self.title_item.setVisible(False)
        self.update()

    def _generate_jagged_feature(self):
        path = QPainterPath(); cx = random.uniform(-self.radius/2, self.radius/2); cy = random.uniform(-self.radius/2, self.radius/2)
        points = []; num_points = random.randint(5, 8); base_radius = random.uniform(self.radius/4, self.radius/2)
        for i in range(num_points):
            angle = math.radians((360 / num_points) * i); r = base_radius + random.uniform(-5, 5)
            px = cx + math.cos(angle) * r; py = cy + math.sin(angle) * r; points.append(QPointF(px, py))
        polygon = QPolygonF(points); path.addPolygon(polygon); return path
    def _generate_unique_break(self):
        full_moon = QPainterPath(); full_moon.addEllipse(self.rect); angle = random.uniform(0, 360); r_outer = self.radius * 2
        cutter = QPainterPath(); p0 = QPointF(math.cos(math.radians(angle)) * r_outer, math.sin(math.radians(angle)) * r_outer); cutter.moveTo(p0)
        offset_x = random.uniform(-5, 5); offset_y = random.uniform(-5, 5)
        cutter.lineTo(offset_x + random.uniform(-5, 5), offset_y + random.uniform(-5, 5))
        cutter.lineTo(math.cos(math.radians(angle + 50)) * r_outer, math.sin(math.radians(angle + 50)) * r_outer)
        cutter.lineTo(math.cos(math.radians(angle - 50)) * r_outer, math.sin(math.radians(angle - 50)) * r_outer)
        cutter.closeSubpath(); stroker = QPainterPathStroker(); stroker.setWidth(random.uniform(5, 15)); stroker.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        cut_poly = stroker.createStroke(cutter); self.broken_body = full_moon.subtracted(cut_poly)
        debris_source = full_moon.intersected(cut_poly); num_shards = random.randint(3, 7)
        for _ in range(num_shards):
            sx = random.uniform(-self.radius, self.radius); sy = random.uniform(-self.radius, self.radius); shard_poly = QPolygonF()
            for _ in range(random.randint(3, 5)): shard_poly.append(QPointF(sx + random.uniform(-8,8), sy + random.uniform(-8,8)))
            shard_path = QPainterPath(); shard_path.addPolygon(shard_poly); final_shard = debris_source.intersected(shard_path)
            if not final_shard.isEmpty():
                move_dist = random.uniform(5, 20); move_angle = math.atan2(sy, sx); dx = math.cos(move_angle) * move_dist; dy = math.sin(move_angle) * move_dist; final_shard.translate(dx, dy); self.shards.append(final_shard)
    def _generate_cosmic_dust(self):
        dust_count = random.randint(10, 25)
        for _ in range(dust_count):
            dist = random.uniform(self.radius * 1.2, self.radius * 4.0); angle = random.uniform(0, 360)
            dx = math.cos(math.radians(angle)) * dist; dy = math.sin(math.radians(angle)) * dist
            size = random.uniform(1.0, 5.0); poly = QPolygonF()
            poly.append(QPointF(dx, dy)); poly.append(QPointF(dx + size, dy + size)); poly.append(QPointF(dx - size, dy + size/2)); self.dust.append(poly)
    def boundingRect(self): return self.rect.adjusted(-100, -100, 100, 100)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.is_cancelled:
            painter.setPen(QPen(QColor("#555555"), 1)); painter.setBrush(QBrush(QColor("#333333")))
            if self.broken_body: painter.drawPath(self.broken_body)
            painter.setBrush(QBrush(QColor("#444444")))
            for shard in self.shards: painter.drawPath(shard)
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QBrush(QColor("#777777")))
            for speck in self.dust: painter.drawPolygon(speck)
            return

        # --- СУПЕР КОНТРАСТНАЯ ЛОГИКА ДЛЯ ЛУН ---
        if self.is_done:
            # СВЕТЛЯЧОК: Яркий цвет, свечение
            base_color = self.accent
            feat_color = self.accent.lighter(130)
            border_color = QColor("#ffffff") # Белый ободок
            border_width = 2
            shadow_alpha = 50 # Почти нет тени, луна светится
        else:
            # КАМЕНЬ: Темно-серый, никакой жизни
            base_color = QColor("#303030") 
            feat_color = QColor("#404040")
            border_color = QColor("#555555") # Тусклый ободок
            border_width = 1
            shadow_alpha = 180

        if self.is_hovered: 
            border_color = border_color.lighter(150)
            if not self.is_done: base_color = QColor("#454545") # Чуть светлее при наведении, но всё равно серое

        painter.save(); moon_path = QPainterPath(); moon_path.addEllipse(self.rect); painter.setClipPath(moon_path)
        painter.fillPath(moon_path, QBrush(base_color))
        
        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QBrush(feat_color))
        for feat in self.features: painter.drawPath(feat)
        
        # Тень
        shadow_grad = QRadialGradient(QPointF(0, 0), self.radius)
        shadow_grad.setColorAt(0.6, QColor(0,0,0,0))
        shadow_grad.setColorAt(1.0, QColor(0,0,0,shadow_alpha))
        painter.fillPath(moon_path, QBrush(shadow_grad)); painter.restore()
        
        pen = QPen(border_color, border_width)
        painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush); painter.drawEllipse(self.rect)