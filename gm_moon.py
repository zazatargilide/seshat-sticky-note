import math
import random

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QPolygonF,
    QRadialGradient,
)
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QMenu


class SubTaskMoonItem(QGraphicsItem):
    def __init__(
        self,
        data,
        accent_color,
        orbit_radius,
        start_angle,
        speed,
        status_callback=None,
        sibling_count=1,
        parent_radius=100,
    ):
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

        # --- НОВАЯ ЛОГИКА РАЗМЕРА (БОЛЬШЕ ВАРИАТИВНОСТИ) ---
        # Раньше было фикс 15%. Теперь от 10% до 28% от размера планеты.
        # Это создает "гигантов" и "карликов".
        percent = random.uniform(0.10, 0.28)
        base_from_parent = parent_radius * percent

        # Фактор "тесноты"
        sibling_factor = 1.0
        if sibling_count > 4:
            # Если лун много, чуть уменьшаем общую массу, но не так сильно, как раньше
            sibling_factor = max(0.5, 1.0 - (sibling_count - 4) * 0.03)

        text_bonus = min(len(self.text), 15) * 0.3 * sibling_factor
        chaos_bonus = random.uniform(-2, 8)

        final_r = (base_from_parent * sibling_factor) + text_bonus + chaos_bonus

        # Лимиты: минимум 6px, максимум 45% от планеты
        self.radius = max(6, min(final_r, parent_radius * 0.45))

        self.rect = QRectF(-self.radius, -self.radius, self.radius * 2, self.radius * 2)

        self.is_hovered = False
        # is_title_pinned убрали из логики "родителя", но оставили для клика по самой луне
        self.is_title_pinned = False
        self.pulse_phase = random.uniform(0, 10)

        self.title_item = QGraphicsTextItem(self.text, self)
        font_size = max(8, int(self.radius * 0.8))
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        self.title_item.setFont(font)
        self.title_item.setDefaultTextColor(QColor("#ffffff"))
        txt_rect = self.title_item.boundingRect()
        self.title_item.setPos(-txt_rect.width() / 2, self.radius + 3)
        self.title_item.setVisible(False)

        self.craters = []
        self.broken_body = None
        self.shards = []
        self.dust = []

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
        self.craters = []
        self.broken_body = None
        self.shards = []
        self.dust = []
        if self.is_cancelled:
            self._generate_unique_break()
            self._generate_cosmic_dust()
        else:
            if self.radius > 8:
                num_craters = random.randint(2, 6)
                for _ in range(num_craters):
                    self.craters.append(self._generate_complex_crater())
        self.update()

    def set_status(self, done=None, cancelled=None, from_parent=False, silent=False):
        changed = False

        if cancelled is not None and self.is_cancelled != cancelled:
            self.is_cancelled = cancelled
            self.data["cancelled"] = cancelled
            self.refresh_geometry()
            changed = True

        if done is not None and self.is_done != done:
            self.is_done = done
            self.data["checked"] = done
            changed = True

        if changed:
            self.update()
            if (
                not from_parent
                and self.parentItem()
                and hasattr(self.parentItem(), "on_moon_changed")
            ):
                self.parentItem().on_moon_changed()
            if not silent and self.status_callback:
                self.status_callback()

    # Этот метод больше не вызывается родителем для "показа", но оставим его для совместимости
    def set_show_title(self, visible):
        # Игнорируем принудительный показ от родителя, если хотим только hover
        # Но если нужно клик по луне - оставляем логику в mousePress
        pass

    def mousePressEvent(self, event):
        # Клик по самой луне переключает название
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_title_pinned = not self.is_title_pinned
            self.title_item.setVisible(self.is_title_pinned or self.is_hovered)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet(
            "QMenu { background-color: #202020; color: white; border: 1px solid #555; } QMenu::item:selected { background-color: #404040; }"
        )
        action_done = menu.addAction("✅ Выполнено" if not self.is_done else "Вернуть в работу")
        action_cancel = menu.addAction(
            "❌ Зачеркнуть" if not self.is_cancelled else "✨ Восстановить"
        )
        res = menu.exec(event.screenPos())
        if res == action_done:
            self.set_status(done=not self.is_done)
        elif res == action_cancel:
            new_cancel = not self.is_cancelled
            self.set_status(cancelled=new_cancel, done=False if new_cancel else self.is_done)

    def advance(self, phase):
        if not phase:
            return
        self.current_angle += self.speed
        rad = math.radians(self.current_angle)
        x = self.orbit_radius * math.cos(rad)
        y = self.orbit_radius * math.sin(rad)
        self.setPos(x, y)
        self.pulse_phase += 0.1

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.title_item.setVisible(True)
        self.update()

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        # Скрываем, если не закреплено кликом по ЛУНЕ (не по планете)
        if not self.is_title_pinned:
            self.title_item.setVisible(False)
        self.update()

    def _generate_complex_crater(self):
        cx = random.uniform(-self.radius * 0.6, self.radius * 0.6)
        cy = random.uniform(-self.radius * 0.6, self.radius * 0.6)
        r_outer = random.uniform(self.radius * 0.15, self.radius * 0.3)
        r_inner = r_outer * random.uniform(0.6, 0.8)
        scale_x = random.uniform(0.9, 1.1)
        scale_y = random.uniform(0.9, 1.1)

        dist_from_center = math.hypot(cx, cy)
        offset_factor = dist_from_center / self.radius * r_inner * 0.2
        angle_from_center = math.atan2(cy, cx)
        inner_ox = cx + math.cos(angle_from_center) * offset_factor
        inner_oy = cy + math.sin(angle_from_center) * offset_factor

        outer_path = QPainterPath()
        outer_path.addEllipse(QPointF(cx, cy), r_outer * scale_x, r_outer * scale_y)
        inner_path = QPainterPath()
        inner_path.addEllipse(QPointF(inner_ox, inner_oy), r_inner * scale_x, r_inner * scale_y)
        return {"outer": outer_path, "inner": inner_path}

    def _generate_unique_break(self):
        full_moon = QPainterPath()
        full_moon.addEllipse(self.rect)
        angle = random.uniform(0, 360)
        r_outer = self.radius * 2
        cutter = QPainterPath()
        p0 = QPointF(
            math.cos(math.radians(angle)) * r_outer, math.sin(math.radians(angle)) * r_outer
        )
        cutter.moveTo(p0)
        offset_x = random.uniform(-3, 3)
        offset_y = random.uniform(-3, 3)
        cutter.lineTo(offset_x, offset_y)
        cutter.lineTo(
            math.cos(math.radians(angle + 50)) * r_outer,
            math.sin(math.radians(angle + 50)) * r_outer,
        )
        cutter.lineTo(
            math.cos(math.radians(angle - 50)) * r_outer,
            math.sin(math.radians(angle - 50)) * r_outer,
        )
        cutter.closeSubpath()
        stroker = QPainterPathStroker()
        stroker.setWidth(random.uniform(2, 8))
        stroker.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        cut_poly = stroker.createStroke(cutter)
        self.broken_body = full_moon.subtracted(cut_poly)
        debris_source = full_moon.intersected(cut_poly)
        num_shards = random.randint(3, 7)
        for _ in range(num_shards):
            sx = random.uniform(-self.radius, self.radius)
            sy = random.uniform(-self.radius, self.radius)
            shard_poly = QPolygonF()
            for _ in range(random.randint(3, 5)):
                shard_poly.append(QPointF(sx + random.uniform(-4, 4), sy + random.uniform(-4, 4)))
            shard_path = QPainterPath()
            shard_path.addPolygon(shard_poly)
            final_shard = debris_source.intersected(shard_path)
            if not final_shard.isEmpty():
                move_dist = random.uniform(2, 10)
                move_angle = math.atan2(sy, sx)
                dx = math.cos(move_angle) * move_dist
                dy = math.sin(move_angle) * move_dist
                final_shard.translate(dx, dy)
                self.shards.append(final_shard)

    def _generate_cosmic_dust(self):
        dust_count = random.randint(5, 15)
        for _ in range(dust_count):
            dist = random.uniform(self.radius * 1.2, self.radius * 3.0)
            angle = random.uniform(0, 360)
            dx = math.cos(math.radians(angle)) * dist
            dy = math.sin(math.radians(angle)) * dist
            size = random.uniform(0.5, 3.0)
            poly = QPolygonF()
            poly.append(QPointF(dx, dy))
            poly.append(QPointF(dx + size, dy + size))
            poly.append(QPointF(dx - size, dy + size / 2))
            self.dust.append(poly)

    def boundingRect(self):
        return self.rect.adjusted(-50, -50, 50, 50)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.is_cancelled:
            painter.setPen(QPen(QColor("#555555"), 1))
            painter.setBrush(QBrush(QColor("#333333")))
            if self.broken_body:
                painter.drawPath(self.broken_body)
            painter.setBrush(QBrush(QColor("#444444")))
            for shard in self.shards:
                painter.drawPath(shard)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#777777")))
            for speck in self.dust:
                painter.drawPolygon(speck)
            return

        if self.is_done:
            base_color = self.accent
            shadow_alpha = 80
        else:
            base_color = QColor("#1a1a1a")
            shadow_alpha = 240

        if self.is_hovered:
            if not self.is_done:
                base_color = QColor("#252525")

        painter.save()
        moon_path = QPainterPath()
        moon_path.addEllipse(self.rect)
        painter.setClipPath(moon_path)

        ocean_grad = QRadialGradient(QPointF(0, 0), self.radius)
        if self.is_done:
            ocean_grad.setColorAt(0, base_color.lighter(130))
            ocean_grad.setColorAt(1, base_color.darker(110))
        else:
            ocean_grad.setColorAt(0, QColor("#252525"))
            ocean_grad.setColorAt(1, QColor("#101010"))
        painter.fillPath(moon_path, QBrush(ocean_grad))

        rim_color = base_color.lighter(120)
        if self.is_done:
            rim_color.setAlpha(180)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(rim_color))
        for crater in self.craters:
            painter.drawPath(crater["outer"])

        pit_color = base_color.darker(150)
        if self.is_done:
            pit_color.setAlpha(200)
        painter.setBrush(QBrush(pit_color))
        for crater in self.craters:
            painter.drawPath(crater["inner"])

        shadow_grad = QRadialGradient(QPointF(0, 0), self.radius)
        shadow_grad.setColorAt(0.65, QColor(0, 0, 0, 0))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, shadow_alpha))
        painter.fillPath(moon_path, QBrush(shadow_grad))
        painter.restore()
