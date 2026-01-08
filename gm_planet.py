import math
import os
import random
from collections import deque

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QPixmap,
    QPolygonF,
    QRadialGradient,
    QTransform,
)
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QMenu

from gm_moon import SubTaskMoonItem


class TaskPlanetItem(QGraphicsItem):
    STATE_NORMAL = 0
    STATE_HOVERED = 1
    STATE_PINNED = 2

    def __init__(
        self,
        task_data,
        accent_color,
        orbit_radius,
        start_angle,
        pin_callback,
        status_callback,
        calculated_radius,
    ):
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

        dist_factor = 1000 / (orbit_radius if orbit_radius > 0 else 1)
        kepler_speed = math.sqrt(dist_factor) * 0.05
        personality_speed = random.uniform(0.8, 1.5)
        direction = 1 if random.random() > 0.5 else -1
        self.speed = kepler_speed * personality_speed * direction

        self.dash_offset = 0.0
        self.time_counter = random.uniform(0, 100)

        self.trail_points = deque(maxlen=20)

        self.state = self.STATE_NORMAL
        self.current_scale = 1.0
        self.target_scale = 1.0
        self.is_hovered = False

        self.base_z = 0

        self.setAcceptHoverEvents(True)

        self.continents = []
        self.broken_body_path = None
        self.shards = []
        self.debris_field = []
        self.broken_pixmap = None

        self.geo_seed = random.random() * 1000

        self.refresh_geometry()
        self._spawn_moons()

    def shape(self):
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

            count_scale = min(1.0, self.radius / 400.0)
            num_continents = int(2 + count_scale * 5) + random.randint(0, 2)

            for i in range(num_continents):
                offset_angle = random.uniform(0, 2 * math.pi)
                offset_r = random.uniform(0, self.radius * 0.5)
                cx = math.cos(offset_angle) * offset_r
                cy = math.sin(offset_angle) * offset_r

                base_size = self.radius * random.uniform(0.3, 0.6)
                self.continents.append(self._generate_smooth_continent(cx, cy, base_size, i))

        self.update()

    def set_status(self, done=None, cancelled=None, silent=False):
        changed = False
        if cancelled is not None and self.is_cancelled != cancelled:
            self.is_cancelled = cancelled
            self.data["cancelled"] = cancelled
            for child in self.childItems():
                if isinstance(child, SubTaskMoonItem):
                    child.set_status(cancelled=cancelled, from_parent=True, silent=silent)
            self.refresh_geometry()
            changed = True

        if done is not None and self.is_done != done:
            self.is_done = done
            self.data["checked"] = done
            for child in self.childItems():
                if isinstance(child, SubTaskMoonItem):
                    child.set_status(done=done, from_parent=True, silent=silent)
            self.update()
            changed = True

        if changed and not silent and self.status_callback:
            self.status_callback()

    def on_moon_changed(self):
        moons = [c for c in self.childItems() if isinstance(c, SubTaskMoonItem)]
        if not moons:
            return

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
            self.data["checked"] = True
            changed = True
        elif not all_done and self.is_done:
            self.is_done = False
            self.data["checked"] = False
            changed = True

        if changed:
            self.update()
            if self.status_callback:
                self.status_callback()

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet(
            "QMenu { background-color: #202020; color: white; border: 1px solid #555; } QMenu::item:selected { background-color: #404040; }"
        )

        action_done = menu.addAction("✅ Выполнено" if not self.is_done else "🔙 Вернуть в работу")
        action_cancel = menu.addAction(
            "❌ Зачеркнуть" if not self.is_cancelled else "✨ Восстановить"
        )
        menu.addSeparator()
        action_reroll = menu.addAction("🎲 Пересобрать ландшафт")

        res = menu.exec(event.screenPos())

        if res == action_done:
            self.set_status(done=not self.is_done)
        elif res == action_cancel:
            new_val = not self.is_cancelled
            self.set_status(cancelled=new_val, done=False if new_val else self.is_done)
        elif res == action_reroll:
            self.geo_seed = random.random() * 1000
            self.refresh_geometry()

    def advance(self, phase):
        if not phase:
            return

        self.time_counter += 0.05

        self.dash_offset -= 0.5
        self.dash_offset %= 30

        if self.state != self.STATE_PINNED:
            self.current_angle += self.speed
            rad = math.radians(self.current_angle)
            x = self.orbit_radius * math.cos(rad)
            y = self.orbit_radius * math.sin(rad)
            self.setPos(x, y)

            if not self.is_cancelled:
                self.trail_points.append(self.scenePos())

        if abs(self.current_scale - self.target_scale) > 0.0001:
            self.current_scale += (self.target_scale - self.current_scale) * 0.05
            self.setScale(self.current_scale)

        self._update_orbit_pulse()
        self.update()

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        if self.state == self.STATE_NORMAL:
            self.state = self.STATE_HOVERED
            self.target_scale = 1.1
            self.setZValue(500)
        self._update_links(True)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        if self.state == self.STATE_HOVERED:
            self.state = self.STATE_NORMAL
            self.target_scale = 1.0
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
            self.setZValue(1000)
            self.trail_points.clear()
        else:
            self.state = self.STATE_NORMAL
            self.target_scale = 1.0
            self.setZValue(self.base_z)

        self._update_links(pinned)
        # УБРАЛИ ПРИНУДИТЕЛЬНЫЙ ПОКАЗ ТИТРОВ ЛУН
        # for child in self.childItems():
        #     if isinstance(child, SubTaskMoonItem):
        #         child.set_show_title(pinned)

    def _update_links(self, highlighted):
        for child in self.childItems():
            if isinstance(child, QGraphicsPathItem):
                pen = child.pen()
                color = QColor(self.accent)
                color.setAlpha(150 if highlighted else 40)
                pen.setColor(color)
                child.setPen(pen)
        self.update()

    def _update_orbit_pulse(self):
        pulse = (math.sin(self.time_counter * 2) + 1) / 2
        for child in self.childItems():
            if isinstance(child, QGraphicsPathItem):
                pen = child.pen()
                base_color = QColor(self.accent)
                alpha = 30 + int(pulse * 40)
                if self.is_hovered or self.state == self.STATE_PINNED:
                    alpha = 150
                base_color.setAlpha(alpha)
                pen.setColor(base_color)
                child.setPen(pen)

    def _spawn_moons(self):
        if not self.children_data:
            return
        count = len(self.children_data)

        current_orbit_dist = self.radius + 30

        for i, child_data in enumerate(self.children_data):
            start_angle = (360 / count) * i + random.uniform(0, 90)
            speed = random.uniform(0.5, 1.5) * (1 if random.random() > 0.5 else -1)

            moon = SubTaskMoonItem(
                child_data,
                self.accent,
                0,
                start_angle,
                speed,
                self.status_callback,
                sibling_count=count,
                parent_radius=self.radius,
            )

            moon_space_needed = moon.radius + 5
            current_orbit_dist += moon_space_needed

            moon.orbit_radius = current_orbit_dist
            moon.setParentItem(self)
            moon.advance(1)

            orbit_path = QPainterPath()
            orbit_path.addEllipse(QPointF(0, 0), current_orbit_dist, current_orbit_dist)
            orbit_item = QGraphicsPathItem(orbit_path, self)
            pen = QPen(self.accent, 2)
            d1, d2 = 15, 15
            pen.setDashPattern([d1, d2])
            color = QColor(self.accent)
            color.setAlpha(40)
            pen.setColor(color)
            orbit_item.setPen(pen)
            orbit_item.setZValue(-1)

            # --- ХАОС В РАССТОЯНИИ МЕЖДУ ЛУНАМИ ---
            # Добавляем случайный разрыв между орбитами
            orbit_chaos = random.uniform(5, 30)
            current_orbit_dist += moon_space_needed + orbit_chaos

    def _generate_smooth_continent(self, cx, cy, base_size, index):
        path = QPainterPath()
        points = []
        num_points = int(max(30, base_size * 0.5))
        seed_offset = self.geo_seed + index * 100

        for i in range(num_points):
            angle = (2 * math.pi / num_points) * i
            n1 = math.sin(angle * 3 + seed_offset) * 0.3
            n2 = math.cos(angle * 7 - seed_offset * 0.5) * 0.15
            n3 = math.sin(angle * 13 + seed_offset * 2) * 0.05
            r = base_size * (1.0 + n1 + n2 + n3)
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
            for _ in range(random.randint(3, 5)):
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
            p1 = QPointF(
                math.cos(math.radians(angle)) * r_start, math.sin(math.radians(angle)) * r_start
            )
            p2 = QPointF(
                math.cos(math.radians(angle + 180)) * r_start,
                math.sin(math.radians(angle + 180)) * r_start,
            )
            path = QPainterPath()
            path.moveTo(p1)
            path.lineTo(p2)
            stroker = QPainterPathStroker()
            stroker.setWidth(random.uniform(10, 30))
            cuts.addPath(stroker.createStroke(path))
        self.broken_body_path = planet_shape.subtracted(cuts)

    def boundingRect(self):
        sys_r = self.get_system_radius() + 50
        text_bottom_margin = self.radius + 150
        rect = self.rect.adjusted(-sys_r - 200, -sys_r - 200, sys_r + 200, sys_r + 200)
        return rect.adjusted(0, 0, 0, text_bottom_margin)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.opacity() < 0.95 and not self.is_cancelled:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(20, 20, 20, 180)))
            painter.drawEllipse(self.rect)
            return

        if self.trail_points and not self.is_cancelled:
            painter.save()
            trail_len = len(self.trail_points)
            for i in range(trail_len - 1):
                opacity_factor = i / trail_len
                alpha = int(100 * opacity_factor * opacity_factor)
                p1 = self.mapFromScene(self.trail_points[i])
                p2 = self.mapFromScene(self.trail_points[i + 1])
                pen_color = QColor(self.accent)
                pen_color.setAlpha(alpha)
                width = self.radius * 0.8 * opacity_factor
                painter.setPen(
                    QPen(pen_color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
                )
                painter.drawLine(p1, p2)
            painter.restore()

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
            land_color = self.accent.lighter(130)
            land_color.setAlpha(200)
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

        ocean_grad = QRadialGradient(QPointF(0, 0), self.radius)
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
        shadow_grad.setColorAt(0.65, QColor(0, 0, 0, 0))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, shadow_alpha))
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
            if not self.is_done:
                atmos_pen.setColor(QColor("#888888"))

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

        box_w = self.radius * 4
        fm = QFontMetrics(font_text)
        elided = fm.elidedText(self.text, Qt.TextElideMode.ElideRight, int(box_w))

        offset_y = self.radius + (base_size * 2)
        text_x = -fm.horizontalAdvance(elided) / 2
        text_y = offset_y + fm.ascent()

        if not self.is_cancelled and (self.is_hovered or self.state == self.STATE_PINNED):
            path = QPainterPath()
            path.addText(text_x, text_y, font_text, elided)
            stroker = QPainterPathStroker()
            stroker.setWidth(3)
            stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            outline_path = stroker.createStroke(path)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
            painter.drawPath(outline_path)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawPath(path)
        else:
            painter.setPen(QColor(color))
            painter.setFont(font_text)
            painter.drawText(QPointF(text_x, text_y), elided)
