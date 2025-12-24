#gm_planet.py

import math
import random
import os
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QMenu
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (QColor, QPen, QBrush, QPainter, QFont, 
                         QFontMetrics, QPolygonF, QRadialGradient, QPixmap, 
                         QPainterPath, QTransform, QPainterPathStroker)

from gm_moon import SubTaskMoonItem

class TaskPlanetItem(QGraphicsItem):
    STATE_NORMAL = 0
    STATE_HOVERED = 1
    STATE_PINNED = 2

    def __init__(self, task_data, accent_color, orbit_radius, start_angle, pin_callback, status_callback, calculated_radius):
        super().__init__()
        self.data = task_data
        self.text = task_data.get("text", "Task")
        self.children_data = task_data.get("children", [])
        self.accent = QColor(accent_color)
        self.pin_callback = pin_callback
        self.status_callback = status_callback
        
        self.is_done = task_data.get("checked", False)
        self.is_cancelled = task_data.get("cancelled", False)
        
        self.radius = calculated_radius
        self.rect = QRectF(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        
        self.orbit_radius = orbit_radius
        self.current_angle = start_angle
        
        # --- ФИЗИКА ---
        dist_factor = 1000 / (orbit_radius if orbit_radius > 0 else 1)
        kepler_speed = math.sqrt(dist_factor) * 0.05
        personality_speed = random.uniform(0.8, 1.5)
        direction = 1 if random.random() > 0.5 else -1
        self.speed = kepler_speed * personality_speed * direction
        
        self.dash_offset = 0.0
        
        self.state = self.STATE_NORMAL
        self.current_scale = 1.0
        self.target_scale = 1.0
        self.is_hovered = False
        
        # Базовый Z-уровень (будет переназначен в goal_map в зависимости от размера)
        self.base_z = 0 
        
        self.setAcceptHoverEvents(True)
        
        self.continents = []
        self.broken_body_path = None
        self.shards = []
        self.debris_field = []
        self.broken_pixmap = None
        
        self.refresh_geometry()
        self._spawn_moons()

    # --- ГЛАВНОЕ ИСПРАВЛЕНИЕ: ТОЧНАЯ ОБЛАСТЬ КЛИКА ---
    def shape(self):
        """
        Определяет физическую форму для столкновений мышкой.
        Возвращаем только круг планеты, игнорируя орбиты и луны (луны обрабатывают клики сами).
        """
        path = QPainterPath()
        path.addEllipse(self.rect)
        return path

    def get_system_radius(self):
        max_dist = self.radius
        for child in self.childItems():
            if isinstance(child, SubTaskMoonItem):
                dist = child.orbit_radius + child.radius + 20 
                if dist > max_dist:
                    max_dist = dist
        return max_dist

    def sync_with_data(self):
        real_done = self.data.get("checked", False)
        real_cancel = self.data.get("cancelled", False)
        
        need_update = False
        if self.is_cancelled != real_cancel:
            self.is_cancelled = real_cancel
            self.refresh_geometry()
            need_update = True
        
        if self.is_done != real_done:
            self.is_done = real_done
            need_update = True
            
        if need_update:
            self.update()

    def refresh_geometry(self):
        self.continents = []
        self.broken_body_path = None
        self.shards = []
        self.debris_field = []
        self.chaos_level = 0
        
        for child in self.children_data:
            if child.get("cancelled", False):
                self.chaos_level += 1
        
        if self.is_cancelled:
            self.chaos_level += 3 
            if self.chaos_level > 0:
                self._generate_diverse_debris()
            
            if os.path.exists("broken.png"):
                self.broken_pixmap = QPixmap("broken.png")
            else:
                self._generate_unique_shatter()
        else:
            if self.chaos_level > 0:
                self._generate_diverse_debris()
            
            base_count = int(self.radius / 15) 
            num_continents = random.randint(max(3, base_count), max(5, base_count + 5))
            
            for _ in range(num_continents):
                self.continents.append(self._generate_jagged_continent())
                
        self.update()

    def set_status(self, done=None, cancelled=None, silent=False):
        changed = False
        if cancelled is not None and self.is_cancelled != cancelled:
            self.is_cancelled = cancelled
            self.data['cancelled'] = cancelled
            for child in self.childItems():
                if isinstance(child, SubTaskMoonItem):
                    child.set_status(cancelled=cancelled, from_parent=True, silent=silent)
            self.refresh_geometry()
            changed = True

        if done is not None and self.is_done != done:
            self.is_done = done
            self.data['checked'] = done
            for child in self.childItems():
                if isinstance(child, SubTaskMoonItem):
                    child.set_status(done=done, from_parent=True, silent=silent)
            self.update()
            changed = True
            
        if changed and not silent and self.status_callback: 
            self.status_callback()

    def on_moon_changed(self):
        moons = [c for c in self.childItems() if isinstance(c, SubTaskMoonItem)]
        if not moons: return

        changed = False
        all_cancelled = all(m.is_cancelled for m in moons)
        if all_cancelled and not self.is_cancelled:
             self.set_status(cancelled=True)
             return

        any_alive = any(not m.is_cancelled for m in moons)
        if any_alive and self.is_cancelled:
            self.set_status(cancelled=False)
            return

        all_done = all(m.is_done for m in moons)
        if all_done and not self.is_done:
            self.is_done = True
            self.data['checked'] = True
            changed = True
        elif not all_done and self.is_done:
             self.is_done = False
             self.data['checked'] = False
             changed = True
        
        if changed: 
            self.update()
            if self.status_callback: self.status_callback()

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #202020; color: white; border: 1px solid #555; } QMenu::item:selected { background-color: #404040; }")
        
        action_done = menu.addAction("✅ Выполнено" if not self.is_done else "🔙 Вернуть в работу")
        action_cancel = menu.addAction("❌ Зачеркнуть" if not self.is_cancelled else "✨ Восстановить")
        menu.addSeparator()
        action_reroll = menu.addAction("🎲 Пересобрать ландшафт")
        
        res = menu.exec(event.screenPos())
        
        if res == action_done:
            self.set_status(done=not self.is_done)
        elif res == action_cancel:
            new_val = not self.is_cancelled
            self.set_status(cancelled=new_val, done=False if new_val else self.is_done)
        elif res == action_reroll:
            self.refresh_geometry()

    def advance(self, phase):
        if not phase: return
        
        self.dash_offset -= 0.5
        if self.dash_offset < -100: self.dash_offset = 0
        
        if self.state != self.STATE_PINNED:
            self.current_angle += self.speed
            rad = math.radians(self.current_angle)
            x = self.orbit_radius * math.cos(rad)
            y = self.orbit_radius * math.sin(rad)
            self.setPos(x, y)
            
        if abs(self.current_scale - self.target_scale) > 0.0001:
            self.current_scale += (self.target_scale - self.current_scale) * 0.05
            self.setScale(self.current_scale)
        
        if self.is_hovered or self.state == self.STATE_PINNED:
            self.update()

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        if self.state == self.STATE_NORMAL:
            self.state = self.STATE_HOVERED
            self.target_scale = 1.1
            # Поднимаем высоко, но не выше пина
            self.setZValue(500)
        self._update_links(True)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        if self.state == self.STATE_HOVERED:
            self.state = self.STATE_NORMAL
            self.target_scale = 1.0
            # Возвращаем на базовый уровень (сортировка по размеру)
            self.setZValue(self.base_z)
        self._update_links(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.state == self.STATE_PINNED:
                self.set_pinned(False)
                self.pin_callback(None)
            else:
                self.set_pinned(True)
                self.pin_callback(self)
        super().mousePressEvent(event)

    def set_pinned(self, pinned):
        if pinned:
            self.state = self.STATE_PINNED
            self.target_scale = 1.0 
            # Самый высокий приоритет
            self.setZValue(1000)
        else:
            self.state = self.STATE_NORMAL
            self.target_scale = 1.0
            self.setZValue(self.base_z)
            
        self._update_links(pinned)
        for child in self.childItems():
            if isinstance(child, SubTaskMoonItem):
                child.set_show_title(pinned)

    def _update_links(self, highlighted):
        for child in self.childItems():
             if isinstance(child, QGraphicsPathItem):
                 pen = child.pen()
                 color = QColor(self.accent)
                 color.setAlpha(150 if highlighted else 40)
                 pen.setColor(color)
                 child.setPen(pen)
        self.update()

    def _spawn_moons(self):
        if not self.children_data: return
        
        count = len(self.children_data)
        current_orbit_dist = self.radius + 60 
        
        for i, child_data in enumerate(self.children_data):
            start_angle = (360 / count) * i + random.uniform(0, 90)
            speed = random.uniform(0.5, 1.5) * (1 if random.random() > 0.5 else -1)
            
            moon = SubTaskMoonItem(child_data, self.accent, 0, start_angle, speed, self.status_callback)
            
            moon_space_needed = moon.radius + 15 
            current_orbit_dist += moon_space_needed
            
            moon.orbit_radius = current_orbit_dist
            moon.setParentItem(self)
            moon.advance(1) 
            
            orbit_path = QPainterPath()
            orbit_path.addEllipse(QPointF(0,0), current_orbit_dist, current_orbit_dist)
            
            orbit_item = QGraphicsPathItem(orbit_path, self)
            pen = QPen(self.accent, 2)
            d1 = random.randint(5, 25)
            d2 = random.randint(10, 30)
            pen.setDashPattern([d1, d2])
            
            color = QColor(self.accent)
            color.setAlpha(40)
            pen.setColor(color)
            
            orbit_item.setPen(pen)
            # Орбиты всегда ниже самой планеты
            orbit_item.setZValue(-1)
            
            current_orbit_dist += moon_space_needed + 10 

    def _generate_jagged_continent(self):
        path = QPainterPath()
        cx = random.uniform(-self.radius*0.8, self.radius*0.8)
        cy = random.uniform(-self.radius*0.8, self.radius*0.8)
        
        num_points = random.randint(10, 20)
        base_radius = random.uniform(self.radius * 0.15, self.radius * 0.35)
        points = []
        
        for i in range(num_points):
            angle = math.radians((360 / num_points) * i)
            noise = random.uniform(-base_radius * 0.3, base_radius * 0.3)
            r = base_radius + noise
            px = cx + math.cos(angle) * r
            py = cy + math.sin(angle) * r
            points.append(QPointF(px, py))
            
        polygon = QPolygonF(points)
        path.addPolygon(polygon)
        return path

    def _generate_diverse_debris(self):
        count = random.randint(10, 20) + (self.chaos_level * 8)
        for _ in range(count):
            dist = self.radius * random.triangular(1.1, 3.0, 1.4)
            angle = random.uniform(0, 360)
            dx = math.cos(math.radians(angle)) * dist
            dy = math.sin(math.radians(angle)) * dist
            
            size = random.uniform(2.0, 10.0)
            poly = QPolygonF()
            for _ in range(random.randint(3,5)):
                poly.append(QPointF(random.uniform(-size, size), random.uniform(-size, size)))
            
            rotation = random.uniform(0, 360)
            transform = QTransform().translate(dx, dy).rotate(rotation)
            final_poly = transform.map(poly)
            
            gray = random.randint(50, 120)
            alpha = random.randint(100, 255)
            color = QColor(gray, gray, gray, alpha)
            
            self.debris_field.append((final_poly, color))

    def _generate_unique_shatter(self):
        planet_shape = QPainterPath()
        planet_shape.addEllipse(self.rect)
        cuts = QPainterPath()
        
        for _ in range(random.randint(2, 3)):
            angle = random.uniform(0, 360)
            r_start = self.radius * 1.8
            p1 = QPointF(math.cos(math.radians(angle))*r_start, math.sin(math.radians(angle))*r_start)
            p2 = QPointF(math.cos(math.radians(angle+180))*r_start, math.sin(math.radians(angle+180))*r_start)
            
            path = QPainterPath()
            path.moveTo(p1)
            path.lineTo(p2)
            
            stroker = QPainterPathStroker()
            stroker.setWidth(random.uniform(10, 30))
            cuts.addPath(stroker.createStroke(path))
            
        self.broken_body_path = planet_shape.subtracted(cuts)

    def boundingRect(self):
        sys_r = self.get_system_radius() + 50
        return self.rect.adjusted(-sys_r, -sys_r, sys_r, sys_r)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.is_cancelled:
            if self.broken_pixmap:
                painter.drawPixmap(self.rect.toRect(), self.broken_pixmap)
            else:
                if self.debris_field:
                    painter.setPen(Qt.PenStyle.NoPen)
                    for poly, color in self.debris_field:
                        painter.setBrush(QBrush(color))
                        painter.drawPolygon(poly)
                        
                painter.setBrush(QBrush(QColor("#2b2b2b")))
                painter.setPen(Qt.PenStyle.NoPen)
                
                if self.broken_body_path:
                    painter.drawPath(self.broken_body_path)
            
            self._draw_text(painter, strike=True, color="#666666")
            return
        
        if self.is_done:
            base_color = QColor(self.accent)
            land_color = self.accent.lighter(130); land_color.setAlpha(200)
            atmos_color = self.accent
            atmos_alpha = 255 
            shadow_alpha = 80 
        else:
            base_color = QColor("#1a1a1a") 
            land_color = QColor("#2a2a2a") 
            atmos_color = QColor("#555555")
            atmos_alpha = 50 
            shadow_alpha = 240 

        painter.save()
        planet_path = QPainterPath()
        planet_path.addEllipse(self.rect)
        painter.setClipPath(planet_path)
        
        ocean_grad = QRadialGradient(QPointF(0,0), self.radius)
        if self.is_done:
            ocean_grad.setColorAt(0, base_color.lighter(130))
            ocean_grad.setColorAt(1, base_color.darker(110))
        else:
            ocean_grad.setColorAt(0, QColor("#252525"))
            ocean_grad.setColorAt(1, QColor("#101010"))
        
        painter.fillPath(planet_path, QBrush(ocean_grad))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(land_color))
        for continent in self.continents:
            painter.drawPath(continent)
        
        shadow_grad = QRadialGradient(QPointF(0, 0), self.radius)
        shadow_grad.setColorAt(0.65, QColor(0,0,0,0))
        shadow_grad.setColorAt(1.0, QColor(0,0,0, shadow_alpha))
        painter.fillPath(planet_path, QBrush(shadow_grad))
        
        painter.restore()

        if not self.is_done: 
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#404040"), 2))
            painter.drawEllipse(self.rect)

        atmos_gap = self.radius * 0.15
        atmos_rect = self.rect.adjusted(-atmos_gap, -atmos_gap, atmos_gap, atmos_gap)
        pen_width = max(3, self.radius * 0.04)
        
        atmos_pen = QPen(atmos_color, pen_width)
        atmos_pen.setDashPattern([15, 15])
        
        atmos_pen.setDashOffset(self.dash_offset) 
        
        final_alpha = atmos_alpha
        if self.is_hovered or self.state == self.STATE_PINNED: 
            final_alpha = 255 
            if not self.is_done: atmos_pen.setColor(QColor("#888888"))
        
        color = QColor(atmos_color)
        color.setAlpha(final_alpha)
        atmos_pen.setColor(color)
        
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(atmos_pen)
        painter.drawEllipse(atmos_rect)

        text_color = "#ffffff"
        if not self.is_done and not self.is_hovered and self.state != self.STATE_PINNED:
            text_color = "#666666"
        elif self.is_done:
            text_color = "#ffffff"
            
        self._draw_text(painter, strike=False, color=text_color)

    def _draw_text(self, painter, strike, color):
        base_size = max(14, self.radius * 0.1)
        font_text = QFont("Arial", int(base_size), QFont.Weight.Bold)
        font_text.setStrikeOut(strike)
        painter.setPen(QColor(color))
        painter.setFont(font_text)
        
        box_w = self.radius * 4 
        fm = QFontMetrics(font_text)
        elided = fm.elidedText(self.text, Qt.TextElideMode.ElideRight, int(box_w))
        
        offset_y = self.radius + (base_size * 2)
        text_rect = QRectF(-box_w/2, offset_y, box_w, 100)
        
        if not self.is_cancelled and (self.is_hovered or self.state == self.STATE_PINNED):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0,0,0,180)))
            painter.drawRoundedRect(text_rect.adjusted(-5,0,5,0), 8, 8)
            painter.setPen(QColor(color))
        
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)