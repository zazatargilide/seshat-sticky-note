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

    def __init__(self, task_data, accent_color, orbit_radius, start_angle, pin_callback, status_callback, size_mode=3):
        super().__init__()
        self.data = task_data
        self.text = task_data.get("text", "Task")
        self.children_data = task_data.get("children", [])
        self.accent = QColor(accent_color)
        self.pin_callback = pin_callback
        self.status_callback = status_callback
        self.size_mode = size_mode
        
        self.is_done = task_data.get("checked", False)
        self.is_cancelled = task_data.get("cancelled", False)
        
        moon_count = len(self.children_data)
        if self.size_mode == 1:   
            base_size = 120; size_variation = random.uniform(-20, 40); moons_bonus = moon_count * 10; max_limit = 250
        elif self.size_mode == 2: 
            base_size = 200; size_variation = random.uniform(-40, 60); moons_bonus = moon_count * 20; max_limit = 500
        else:                     
            base_size = 350; size_variation = random.uniform(-100, 150); moons_bonus = moon_count * 40; max_limit = 1200
        
        raw_radius = base_size + size_variation + moons_bonus
        self.radius = max(80, min(raw_radius, max_limit))
        
        self.rect = QRectF(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        
        self.orbit_radius = orbit_radius
        self.current_angle = start_angle
        
        dist_factor = 500 / (orbit_radius if orbit_radius > 0 else 1)
        base_speed = math.sqrt(dist_factor) * 0.5
        random_speed = random.uniform(0.8, 1.2)
        direction = 1 if random.random() > 0.5 else -1
        self.speed = (base_speed * random_speed * direction) / 10.0
        
        self.state = self.STATE_NORMAL
        self.current_scale = 1.0
        self.target_scale = 1.0
        self.is_hovered = False
        
        self.setAcceptHoverEvents(True)
        
        self.continents = []
        self.broken_body_path = None; self.shards = []; self.debris_field = []
        self.broken_pixmap = None
        
        self.refresh_geometry()
        self._spawn_moons()

    def sync_with_data(self):
        """
        Метод вызывается из goal_map.py.
        Сравнивает текущие флаги с данными в self.data (которые только что обновили).
        """
        real_done = self.data.get("checked", False)
        real_cancel = self.data.get("cancelled", False)
        
        need_update = False
        
        # Если статус отмены изменился
        if self.is_cancelled != real_cancel:
            self.is_cancelled = real_cancel
            self.refresh_geometry() # Перестраиваем форму (взрыв/сборка)
            need_update = True
            
        # Если статус выполнения изменился
        if self.is_done != real_done:
            self.is_done = real_done
            # Тут refresh_geometry не нужен, только смена цвета (update)
            need_update = True
            
        if need_update:
            self.update()

    def refresh_geometry(self):
        """Перестройка графики (континенты или осколки)"""
        self.continents = []
        self.broken_body_path = None; self.shards = []; self.debris_field = []
        self.chaos_level = 0
        
        # ВАЖНО: Используем self.children_data, который должен быть обновлен!
        for child in self.children_data:
            if child.get("cancelled", False): self.chaos_level += 1
        
        if self.is_cancelled:
            self.chaos_level += 3 
            if self.chaos_level > 0: self._generate_diverse_debris()
            if os.path.exists("broken.png"): self.broken_pixmap = QPixmap("broken.png")
            else: self._generate_unique_shatter()
        else:
            if self.chaos_level > 0: self._generate_diverse_debris()
            base_count = 6 if self.size_mode == 1 else (9 if self.size_mode == 2 else 14)
            num_continents = random.randint(base_count, base_count + 6)
            for _ in range(num_continents): self.continents.append(self._generate_jagged_continent())
        self.update()

    def set_status(self, done=None, cancelled=None, silent=False):
        """
        Ручная установка статуса (через контекстное меню планеты).
        Передает изменения детям (лунам).
        """
        changed = False
        
        # 1. ОТМЕНА / ВОССТАНОВЛЕНИЕ
        if cancelled is not None and self.is_cancelled != cancelled:
            self.is_cancelled = cancelled
            self.data['cancelled'] = cancelled
            
            # Передаем статус всем лунам
            for child in self.childItems():
                if isinstance(child, SubTaskMoonItem):
                    child.set_status(cancelled=cancelled, from_parent=True, silent=silent)
            
            self.refresh_geometry()
            changed = True

        # 2. ВЫПОЛНЕНИЕ / ДЕ-ВЫПОЛНЕНИЕ
        if done is not None and self.is_done != done:
            self.is_done = done
            self.data['checked'] = done
            
            # [FIX] Теперь передаем done всегда, даже если это False
            for child in self.childItems():
                if isinstance(child, SubTaskMoonItem):
                    child.set_status(done=done, from_parent=True, silent=silent)
            
            self.update()
            changed = True
            
        if changed and not silent and self.status_callback: 
            self.status_callback()

    def on_moon_changed(self):
        """Реакция на изменение состояния луны"""
        moons = [c for c in self.childItems() if isinstance(c, SubTaskMoonItem)]
        if not moons: return

        changed = False
        
        # Если все луны отменены -> отменяем планету
        all_cancelled = all(m.is_cancelled for m in moons)
        if all_cancelled and not self.is_cancelled:
             self.set_status(cancelled=True)
             return

        # Если хоть одна луна ожила -> восстанавливаем планету
        any_alive = any(not m.is_cancelled for m in moons)
        if any_alive and self.is_cancelled:
            self.set_status(cancelled=False)
            return

        # Если все луны выполнены -> выполняем планету
        all_done = all(m.is_done for m in moons)
        if all_done and not self.is_done:
            self.is_done = True
            self.data['checked'] = True
            changed = True
        # Если хоть одна не выполнена -> снимаем выполнение с планеты
        elif not all_done and self.is_done:
             self.is_done = False
             self.data['checked'] = False
             changed = True
        
        if changed: 
            self.update()
            if self.status_callback: self.status_callback()

    # --- Остальные методы (без изменений) ---
    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #202020; color: white; border: 1px solid #555; } QMenu::item:selected { background-color: #404040; }")
        action_done = menu.addAction("✅ Выполнено" if not self.is_done else "🔙 Вернуть в работу")
        action_cancel = menu.addAction("❌ Зачеркнуть" if not self.is_cancelled else "✨ Восстановить")
        menu.addSeparator()
        action_reroll = menu.addAction("🎲 Пересобрать ландшафт")
        res = menu.exec(event.screenPos())
        if res == action_done: self.set_status(done=not self.is_done)
        elif res == action_cancel:
            new_val = not self.is_cancelled
            self.set_status(cancelled=new_val, done=False if new_val else self.is_done)
        elif res == action_reroll: self.refresh_geometry()

    def advance(self, phase):
        if not phase: return
        if self.state != self.STATE_PINNED:
            self.current_angle += self.speed
            rad = math.radians(self.current_angle)
            x = self.orbit_radius * math.cos(rad); y = self.orbit_radius * math.sin(rad)
            self.setPos(x, y)
        if abs(self.current_scale - self.target_scale) > 0.0001:
            self.current_scale += (self.target_scale - self.current_scale) * 0.05
            self.setScale(self.current_scale)

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        if self.state == self.STATE_NORMAL: self.state = self.STATE_HOVERED; self.target_scale = 1.1; self.setZValue(10)
        self._update_links(True)
    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        if self.state == self.STATE_HOVERED: self.state = self.STATE_NORMAL; self.target_scale = 1.0; self.setZValue(0)
        self._update_links(False)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.state == self.STATE_PINNED: self.set_pinned(False); self.pin_callback(None)
            else: self.set_pinned(True); self.pin_callback(self)
        super().mousePressEvent(event)
    def set_pinned(self, pinned):
        if pinned: self.state = self.STATE_PINNED; self.target_scale = 2.5; self.setZValue(100)
        else: self.state = self.STATE_NORMAL; self.target_scale = 1.0; self.setZValue(0)
        self._update_links(pinned)
        for child in self.childItems():
            if isinstance(child, SubTaskMoonItem): child.set_show_title(pinned)
    def _update_links(self, highlighted):
        for child in self.childItems():
             if isinstance(child, QGraphicsPathItem):
                 pen = child.pen(); color = QColor(self.accent); color.setAlpha(150 if highlighted else self.orbit_alpha); pen.setColor(color); child.setPen(pen)
        self.update()

    def _spawn_moons(self):
        if not self.children_data: return
        count = len(self.children_data)
        base_dist = self.radius + (150 if self.size_mode == 3 else (100 if self.size_mode == 2 else 60))
        for i, child_data in enumerate(self.children_data):
            spread = 100 if self.size_mode == 3 else 60
            orbit_dist = base_dist + (i * random.randint(spread - 20, spread + 20))
            start_angle = (360 / count) * i + random.uniform(0, 90)
            speed = random.uniform(0.5, 1.5) * (1 if random.random() > 0.5 else -1)
            moon = SubTaskMoonItem(child_data, self.accent, orbit_dist, start_angle, speed, self.status_callback)
            moon.setParentItem(self); moon.advance(1)
            orbit_path = QPainterPath(); orbit_path.addEllipse(QPointF(0,0), orbit_dist, orbit_dist)
            orbit_item = QGraphicsPathItem(orbit_path, self); pen = QPen(self.accent, 2)
            d1 = random.randint(5, 25); d2 = random.randint(10, 30); pen.setDashPattern([d1, d2])
            color = QColor(self.accent); self.orbit_alpha = random.randint(30, 80); color.setAlpha(self.orbit_alpha); pen.setColor(color)
            orbit_item.setPen(pen); orbit_item.setZValue(-1)

    def _generate_jagged_continent(self):
        path = QPainterPath(); cx = random.uniform(-self.radius*0.8, self.radius*0.8); cy = random.uniform(-self.radius*0.8, self.radius*0.8)
        detail_factor = max(1, int(self.radius / 30))
        num_points = random.randint(10 + detail_factor, 20 + detail_factor)
        min_size = self.radius * 0.15; max_size = self.radius * 0.35; base_radius = random.uniform(min_size, max_size)
        points = []
        for i in range(num_points):
            angle = math.radians((360 / num_points) * i); noise = random.uniform(-base_radius * 0.3, base_radius * 0.3); r = base_radius + noise
            px = cx + math.cos(angle) * r; py = cy + math.sin(angle) * r; points.append(QPointF(px, py))
        polygon = QPolygonF(points); path.addPolygon(polygon); return path

    def _generate_diverse_debris(self):
        count = random.randint(10, 20) + (self.chaos_level * 8)
        for _ in range(count):
            dist_factor = random.triangular(1.1, 3.0, 1.4); dist = self.radius * dist_factor
            angle = random.uniform(0, 360); dx = math.cos(math.radians(angle)) * dist; dy = math.sin(math.radians(angle)) * dist
            scale_mult = 1.0 if self.size_mode == 1 else (1.5 if self.size_mode == 2 else 2.5)
            size_base = (20.0 if self.is_cancelled else 8.0) * scale_mult
            size = max(2.0, random.uniform(2.0, size_base) * (2.5 / dist_factor))
            shape_type = random.choice(['tri', 'quad', 'poly', 'speck']); poly = QPolygonF()
            if shape_type == 'tri': poly.append(QPointF(-size, -size/2)); poly.append(QPointF(size, 0)); poly.append(QPointF(-size/2, size))
            elif shape_type == 'quad': poly.append(QPointF(-size, -size)); poly.append(QPointF(size, -size*0.5)); poly.append(QPointF(size*0.8, size)); poly.append(QPointF(-size*0.6, size*0.9))
            elif shape_type == 'poly':
                 for _ in range(random.randint(4,6)): poly.append(QPointF(random.uniform(-size, size), random.uniform(-size, size)))
            elif shape_type == 'speck': s = size * 0.7; poly.append(QPointF(-s, -s)); poly.append(QPointF(s, -s)); poly.append(QPointF(s, s)); poly.append(QPointF(-s, s))
            rotation = random.uniform(0, 360); transform = QTransform().translate(dx, dy).rotate(rotation); final_poly = transform.map(poly)
            gray = random.randint(50, 120); alpha = random.randint(100, 255); color = QColor(gray, gray, gray, alpha)
            self.debris_field.append((final_poly, color))

    def _generate_unique_shatter(self):
        planet_shape = QPainterPath(); planet_shape.addEllipse(self.rect); cuts = QPainterPath(); num_cuts = random.randint(2, 3)
        for _ in range(num_cuts):
            angle = random.uniform(0, 360); r_start = self.radius * 1.8; start_p = QPointF(math.cos(math.radians(angle))*r_start, math.sin(math.radians(angle))*r_start)
            end_angle = angle + 180 + random.uniform(-40, 40); end_p = QPointF(math.cos(math.radians(end_angle))*r_start, math.sin(math.radians(end_angle))*r_start)
            single_cut = QPainterPath(); single_cut.moveTo(start_p)
            steps = random.randint(4, 7)
            for i in range(1, steps):
                t = i / steps; bx = start_p.x() + (end_p.x() - start_p.x()) * t; by = start_p.y() + (end_p.y() - start_p.y()) * t; jitter = random.uniform(-20, 20)
                single_cut.lineTo(bx + jitter, by + jitter)
            single_cut.lineTo(end_p); stroker = QPainterPathStroker(); stroker.setWidth(random.uniform(15, 35)); stroker.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            cuts.addPath(stroker.createStroke(single_cut))
        self.broken_body_path = planet_shape.subtracted(cuts); debris_source = planet_shape.intersected(cuts); num_shards = random.randint(5, 12)
        for _ in range(num_shards):
            sx = random.uniform(-self.radius, self.radius); sy = random.uniform(-self.radius, self.radius); shard_poly = QPolygonF()
            for _ in range(random.randint(3, 6)): shard_poly.append(QPointF(sx + random.uniform(-15,15), sy + random.uniform(-15,15)))
            shard_path = QPainterPath(); shard_path.addPolygon(shard_poly); final_shard = debris_source.intersected(shard_path)
            if not final_shard.isEmpty():
                move_dist = random.uniform(10, 40); move_angle = math.atan2(sy, sx) + random.uniform(-0.5, 0.5); dx = math.cos(move_angle) * move_dist; dy = math.sin(move_angle) * move_dist; final_shard.translate(dx, dy); self.shards.append(final_shard)

    def boundingRect(self): return self.rect.adjusted(-600, -600, 600, 600)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.debris_field:
            painter.setPen(Qt.PenStyle.NoPen)
            for poly, color in self.debris_field: painter.setBrush(QBrush(color)); painter.drawPolygon(poly)
        if self.is_cancelled:
            if self.broken_pixmap:
                target_rect = QRectF(-self.radius, -self.radius, self.radius*2, self.radius*2); painter.setOpacity(0.8); painter.drawPixmap(target_rect.toRect(), self.broken_pixmap); painter.setOpacity(1.0)
            else:
                dead_color = QColor("#2b2b2b"); painter.setBrush(QBrush(dead_color)); painter.setPen(QPen(QColor("#555555"), 1))
                if self.broken_body_path: painter.drawPath(self.broken_body_path)
                shard_color = QColor("#353535"); painter.setBrush(QBrush(shard_color))
                for shard in self.shards: painter.drawPath(shard)
            self._draw_text(painter, strike=True, color="#666666")
            return
        
        if self.is_done:
            base_color = self.accent.darker(180); base_color.setAlpha(220)
            land_color = self.accent.darker(130)
            atmos_color = self.accent
        else:
            base_color = self.accent.darker(350); base_color.setAlpha(220)
            land_color = self.accent.darker(250)
            atmos_color = QColor("#a0a0ff")

        painter.save(); planet_path = QPainterPath(); planet_path.addEllipse(self.rect); painter.setClipPath(planet_path)
        ocean_grad = QRadialGradient(QPointF(0,0), self.radius); ocean_grad.setColorAt(0, base_color.lighter(120)); ocean_grad.setColorAt(1, base_color)
        painter.fillPath(planet_path, QBrush(ocean_grad)); painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QBrush(land_color))
        for continent in self.continents: painter.drawPath(continent)
        shadow_grad = QRadialGradient(QPointF(0, 0), self.radius); shadow_grad.setColorAt(0.8, QColor(0,0,0,0)); shadow_grad.setColorAt(1.0, QColor(0,0,0,180))
        painter.fillPath(planet_path, QBrush(shadow_grad)); painter.restore()

        atmos_gap = 20 if self.size_mode == 1 else (35 if self.size_mode == 2 else 50)
        atmos_rect = self.rect.adjusted(-atmos_gap, -atmos_gap, atmos_gap, atmos_gap)
        pen_width = 3 if self.size_mode == 1 else 5
        atmos_pen = QPen(atmos_color, pen_width); atmos_pen.setDashPattern([15, 15]) 
        alpha = 60
        if self.is_hovered or self.state == self.STATE_PINNED or self.is_done: alpha = 200
        color = QColor(atmos_color); color.setAlpha(alpha); atmos_pen.setColor(color)
        painter.setBrush(Qt.BrushStyle.NoBrush); painter.setPen(atmos_pen); painter.drawEllipse(atmos_rect)

        text_color = "#ffffff" if (self.is_hovered or self.state==self.STATE_PINNED) else "#e0e0e0"
        if self.is_done: text_color = self.accent.lighter(180).name()
        self._draw_text(painter, strike=False, color=text_color)

    def _draw_text(self, painter, strike, color):
        f_size = 14 if self.size_mode == 1 else (18 if self.size_mode == 2 else 24)
        font_text = QFont("Arial", f_size, QFont.Weight.Bold); font_text.setStrikeOut(strike); painter.setPen(QColor(color)); painter.setFont(font_text)
        box_w = 250 if self.size_mode == 1 else (300 if self.size_mode == 2 else 400)
        fm = QFontMetrics(font_text); elided = fm.elidedText(self.text, Qt.TextElideMode.ElideRight, box_w)
        offset_y = self.radius + (50 if self.size_mode == 1 else 80)
        text_rect = QRectF(-box_w/2, offset_y, box_w, 50)
        if not self.is_cancelled and (self.is_hovered or self.state == self.STATE_PINNED):
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QBrush(QColor(0,0,0,150))); painter.drawRoundedRect(text_rect.adjusted(-5,0,5,0), 8, 8); painter.setPen(QColor(color))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)