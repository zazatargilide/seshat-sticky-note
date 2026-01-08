import math
import os
import random
import re
from datetime import datetime

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
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
    QRadialGradient,
    QTransform,
)
from PyQt6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QMenu,
    QVBoxLayout,
    QWidget,
)

# Импортируем наши классы
from gm_planet import TaskPlanetItem
from gm_sun import SunItem

# --- ДАННЫЕ ЗОДИАКА (Шаблоны) ---
ZODIAC_PATTERNS_DATA = {
    "Aries": [(0, 20), (30, 0), (60, 10), (80, 30)],
    "Taurus": [(0, 0), (20, 20), (40, 10), (20, -20), (60, -30)],
    "Gemini": [(0, 0), (0, 60), (40, 60), (40, 0)],
    "Cancer": [(0, 0), (20, 20), (40, 0), (20, -20)],
    "Leo": [(0, 0), (20, -20), (40, -10), (50, 10), (40, 30), (10, 40)],
    "Virgo": [(0, 0), (20, 20), (40, 10), (60, 30), (50, 50)],
    "Libra": [(0, 20), (30, 20), (15, 0), (15, 40)],
    "Scorpio": [(0, 0), (10, 20), (20, 10), (30, 30), (40, 20), (40, 50)],
    "Sagittarius": [(0, 0), (20, 0), (10, 20), (30, 20), (20, 40), (40, 40)],
    "Capricorn": [(0, 0), (20, 10), (40, 0), (30, -20)],
    "Aquarius": [(0, 0), (10, 10), (20, 0), (30, 10), (40, 0)],
    "Pisces": [(0, 0), (20, 20), (40, 0)],
}

ZODIAC_DATES = [
    ("Capricorn", (12, 22), (1, 19)),
    ("Aquarius", (1, 20), (2, 18)),
    ("Pisces", (2, 19), (3, 20)),
    ("Aries", (3, 21), (4, 19)),
    ("Taurus", (4, 20), (5, 20)),
    ("Gemini", (5, 21), (6, 20)),
    ("Cancer", (6, 21), (7, 22)),
    ("Leo", (7, 23), (8, 22)),
    ("Virgo", (8, 23), (9, 22)),
    ("Libra", (9, 23), (10, 22)),
    ("Scorpio", (10, 23), (11, 21)),
    ("Sagittarius", (11, 22), (12, 21)),
]


# --- ЧАСЫ ---
class CosmicClock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setMinimumSize(400, 100)  # Широкие
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%d.%m.%Y")

        h = self.height()
        w = self.width()
        time_size = max(24, min(h * 0.45, w * 0.12))
        date_size = max(12, time_size * 0.4)

        font_time = QFont("Courier New", int(time_size), QFont.Weight.Light)
        font_time.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 130)

        font_date = QFont("Courier New", int(date_size), QFont.Weight.Normal)
        font_date.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 150)

        rect = self.rect()
        margin_right = 20
        margin_bottom = 15

        time_pos = QPointF(
            rect.width() - margin_right, rect.height() - date_size - margin_bottom - 5
        )
        date_pos = QPointF(rect.width() - margin_right - 2, rect.height() - margin_bottom)

        def draw_glowing_text(text, pos, font, glow_col, text_col):
            path = QPainterPath()
            fm = QFontMetrics(font)
            text_width = fm.horizontalAdvance(text)
            x = pos.x() - text_width
            y = pos.y()
            path.addText(x, y, font, text)

            stroker = QPainterPathStroker()
            stroker.setWidth(3)
            stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            glow_path = stroker.createStroke(path)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow_col))
            painter.drawPath(glow_path)
            painter.setBrush(QBrush(text_col))
            painter.drawPath(path)

        glow_color = QColor(100, 200, 255, 50)
        draw_glowing_text(time_str, time_pos, font_time, glow_color, QColor(240, 240, 255))
        draw_glowing_text(date_str, date_pos, font_date, glow_color, QColor(180, 180, 200))


# --- СЦЕНА ---
class DynamicStarryScene(QGraphicsScene):
    def __init__(self, background_click_callback=None):
        super().__init__()
        self.stars = []
        self.nebulae = []
        self.procedural_constellations = []
        self.random_links = []
        self.seasonal_zodiac = None
        self.bg_pixmap = None
        self.time_counter = 0
        self.click_callback = background_click_callback
        self.global_rotation = 0.0

        for ext in ["jpg", "png", "jpeg"]:
            if os.path.exists(f"space_bg.{ext}"):
                self.bg_pixmap = QPixmap(f"space_bg.{ext}")
                break

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        if not item:
            if self.click_callback:
                self.click_callback()
        super().mousePressEvent(event)

    def clear_items(self):
        self.clear()
        self.stars = []
        self.nebulae = []
        self.procedural_constellations = []
        self.random_links = []
        self.seasonal_zodiac = None

    def init_background(self, rect):
        if self.stars:
            return
        area = rect.adjusted(-3000, -3000, 3000, 3000)
        w, h = int(area.width()), int(area.height())
        self.center_x, self.center_y = area.center().x(), area.center().y()

        for _ in range(6):
            nx = self.center_x + random.uniform(-w / 3, w / 3)
            ny = self.center_y + random.uniform(-h / 3, h / 3)
            nr = random.uniform(2000, 4000)
            colors = ["#1a0b2e", "#0f172a", "#1e1b4b", "#312e81"]
            base_color = QColor(random.choice(colors))
            base_color.setAlpha(60)
            self.nebulae.append(
                {
                    "x": nx,
                    "y": ny,
                    "r": nr,
                    "c": base_color,
                    "rs": random.uniform(-0.01, 0.01),
                    "a": random.uniform(0, 360),
                }
            )

        self._init_seasonal_zodiac()

        star_colors = [QColor(200, 230, 255), QColor(255, 255, 255), QColor(220, 210, 255)]
        max_radius = max(w, h) / 1.5

        # --- 3000 ЗВЕЗД ---
        for _ in range(3000):
            angle = random.uniform(0, math.pi * 2)
            radius = random.triangular(0, max_radius, max_radius * 0.4)
            sx = self.center_x + math.cos(angle) * radius
            sy = self.center_y + math.sin(angle) * radius

            rnd = random.random()
            if rnd > 0.95:
                stype = "cross"
                size = random.uniform(5.0, 10.0)
            elif rnd > 0.85:
                stype = "x_mark"
                size = random.uniform(4.0, 8.0)
            else:
                stype = "dot"
                size = random.uniform(1.0, 2.5)

            color = QColor(random.choice(star_colors))
            alpha = random.randint(100, 255)
            color.setAlpha(alpha)

            self.stars.append(
                {
                    "angle": angle,
                    "radius": radius,
                    "x": sx,
                    "y": sy,
                    "s": size,
                    "t": stype,
                    "c": color,
                    "flash_timer": random.randint(0, 500),
                }
            )

    def _init_seasonal_zodiac(self):
        now = datetime.now()
        sign_name = "Unknown"
        for name, (sm, sd), (em, ed) in ZODIAC_DATES:
            start = datetime(now.year, sm, sd)
            end = datetime(now.year, em, ed)
            if name == "Capricorn":
                if (now.month == 12 and now.day >= 22) or (now.month == 1 and now.day <= 19):
                    sign_name = name
                    break
            elif start <= now <= end:
                sign_name = name
                break

        points_template = ZODIAC_PATTERNS_DATA.get(sign_name, [])
        if not points_template:
            return

        z_angle = math.radians(-135)
        z_radius = 1800

        cx = self.center_x + math.cos(z_angle) * z_radius
        cy = self.center_y + math.sin(z_angle) * z_radius

        scale = 8.0
        rotation = -45

        transform = QTransform()
        transform.translate(cx, cy)
        transform.rotate(rotation)
        transform.scale(scale, scale)

        scene_points = []
        for px, py in points_template:
            pt = transform.map(QPointF(px, py))
            dx = pt.x() - self.center_x
            dy = pt.y() - self.center_y
            pt_angle = math.atan2(dy, dx)
            pt_radius = math.hypot(dx, dy)

            scene_points.append({"angle": pt_angle, "radius": pt_radius, "x": pt.x(), "y": pt.y()})

        self.seasonal_zodiac = {"name": sign_name, "points": scene_points}

    def advance(self):
        super().advance()
        self.time_counter += 1
        self.global_rotation += 0.0002

        for s in self.stars:
            cur_angle = s["angle"] + self.global_rotation
            s["x"] = self.center_x + math.cos(cur_angle) * s["radius"]
            s["y"] = self.center_y + math.sin(cur_angle) * s["radius"]

            if random.random() > 0.995:
                s["flash_timer"] = 100
            if s["flash_timer"] > 0:
                s["flash_timer"] -= 1

        if self.seasonal_zodiac:
            for pt in self.seasonal_zodiac["points"]:
                cur_angle = pt["angle"] + self.global_rotation
                pt["x"] = self.center_x + math.cos(cur_angle) * pt["radius"]
                pt["y"] = self.center_y + math.sin(cur_angle) * pt["radius"]

        for n in self.nebulae:
            n["a"] += n["rs"]

        if self.time_counter % 250 == 0 and len(self.procedural_constellations) < 2:
            self._spawn_large_constellation()

        for c in self.procedural_constellations[:]:
            if c["state"] == 0:
                c["opacity"] += 0.005
                if c["opacity"] >= 1.0:
                    c["opacity"] = 1.0
                    c["state"] = 1
                    c["timer"] = random.randint(300, 600)
            elif c["state"] == 1:
                c["timer"] -= 1
                if c["timer"] <= 0:
                    c["state"] = 2
            elif c["state"] == 2:
                c["opacity"] -= 0.005
                if c["opacity"] <= 0:
                    self.procedural_constellations.remove(c)

        if self.time_counter % 5 == 0 and len(self.random_links) < 15:
            if self.stars:
                s1 = random.choice(self.stars)
                for s2 in random.sample(self.stars, min(len(self.stars), 20)):
                    if s1 == s2:
                        continue
                    dist = math.hypot(s1["x"] - s2["x"], s1["y"] - s2["y"])
                    if 100 < dist < 400:
                        self.random_links.append({"s1": s1, "s2": s2, "life": 100, "max_life": 100})
                        break

        for link in self.random_links[:]:
            link["life"] -= 1
            if link["life"] <= 0:
                self.random_links.remove(link)

        self.update()

    def _spawn_large_constellation(self):
        pattern_name = random.choice(list(ZODIAC_PATTERNS_DATA.keys()))
        pattern_points = ZODIAC_PATTERNS_DATA[pattern_name]

        cx = self.center_x + random.uniform(-3000, 3000)
        cy = self.center_y + random.uniform(-3000, 3000)
        scale = random.uniform(6.0, 9.0)
        rotation = random.uniform(0, 360)

        transform = QTransform()
        transform.translate(cx, cy)
        transform.rotate(rotation)
        transform.scale(scale, scale)

        scene_points = []
        for px, py in pattern_points:
            scene_points.append(transform.map(QPointF(px, py)))

        self.procedural_constellations.append(
            {"points": scene_points, "state": 0, "opacity": 0.0, "timer": 0}
        )

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QBrush(QColor("#08080a")))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.bg_pixmap:
            painter.drawPixmap(
                rect.toRect(),
                self.bg_pixmap.scaled(
                    rect.size().toSize(), Qt.AspectRatioMode.KeepAspectRatioByExpanding
                ),
            )

        painter.setPen(Qt.PenStyle.NoPen)

        painter.save()
        painter.translate(self.center_x, self.center_y)
        painter.rotate(math.degrees(self.global_rotation))
        painter.translate(-self.center_x, -self.center_y)

        for n in self.nebulae:
            painter.save()
            painter.translate(n["x"], n["y"])
            painter.rotate(n["a"])
            grad = QRadialGradient(QPointF(0, 0), n["r"])
            grad.setColorAt(0, n["c"])
            grad.setColorAt(0.7, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(QRectF(-n["r"], -n["r"] * 0.8, n["r"] * 2, n["r"] * 1.6))
            painter.restore()

        pen = QPen(Qt.PenStyle.SolidLine)
        pen.setWidthF(1.5)
        for c in self.procedural_constellations:
            alpha = int(100 * c["opacity"])
            if alpha > 0:
                pen.setColor(QColor(150, 200, 255, alpha))
                painter.setPen(pen)
                points = c["points"]
                if len(points) > 1:
                    for i in range(len(points) - 1):
                        painter.drawLine(points[i], points[i + 1])
                painter.setPen(Qt.PenStyle.NoPen)
                star_col = QColor(255, 255, 255, int(180 * c["opacity"]))
                painter.setBrush(QBrush(star_col))
                for pt in points:
                    painter.drawEllipse(pt, 3.0, 3.0)

        if self.seasonal_zodiac:
            pen.setColor(QColor(200, 220, 255, 60))
            pen.setWidthF(1.2)
            painter.setPen(pen)

            points = self.seasonal_zodiac["points"]
            if len(points) > 1:
                for i in range(len(points) - 1):
                    p1 = QPointF(points[i]["x"], points[i]["y"])
                    p2 = QPointF(points[i + 1]["x"], points[i + 1]["y"])
                    painter.drawLine(p1, p2)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
            for pt_data in points:
                painter.drawEllipse(QPointF(pt_data["x"], pt_data["y"]), 2.5, 2.5)

        pen_link = QPen(Qt.PenStyle.SolidLine)
        pen_link.setWidthF(0.8)
        for link in self.random_links:
            life_ratio = link["life"] / link["max_life"]
            alpha = int(80 * math.sin(life_ratio * math.pi))
            if alpha > 0:
                pen_link.setColor(QColor(200, 220, 255, alpha))
                painter.setPen(pen_link)
                painter.drawLine(
                    QPointF(link["s1"]["x"], link["s1"]["y"]),
                    QPointF(link["s2"]["x"], link["s2"]["y"]),
                )

        painter.restore()

        for s in self.stars:
            pt = QPointF(s["x"], s["y"])
            size = s["s"]

            alpha_mod = 1.0
            if s["flash_timer"] > 0:
                alpha_mod = 1.5 + math.sin((s["flash_timer"] / 50.0) * math.pi) * 0.5

            col = QColor(s["c"])
            new_alpha = min(255, int(col.alpha() * alpha_mod))
            col.setAlpha(new_alpha)

            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(col, 1.5))

            if s["t"] == "cross":
                half = size * 0.5
                painter.drawLine(QPointF(pt.x() - half, pt.y()), QPointF(pt.x() + half, pt.y()))
                painter.drawLine(QPointF(pt.x(), pt.y() - half), QPointF(pt.x(), pt.y() + half))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 255, 120)))
                painter.drawEllipse(pt, 1.0, 1.0)
            elif s["t"] == "x_mark":
                half = size * 0.4
                painter.drawLine(
                    QPointF(pt.x() - half, pt.y() - half), QPointF(pt.x() + half, pt.y() + half)
                )
                painter.drawLine(
                    QPointF(pt.x() + half, pt.y() - half), QPointF(pt.x() - half, pt.y() + half)
                )
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(col))
                painter.drawEllipse(pt, size, size)


class GoalMapWindow(QWidget):
    def __init__(self, note_data, default_accent, save_callback=None):
        super().__init__()
        self.note_data = note_data
        self.accent = QColor(default_accent)
        self.save_callback = save_callback

        raw_title = self.note_data.get("title", "Note")
        clean_title = raw_title.split(" - ")[0]
        self.note_title = re.sub(r"[:]?\s*\d{2}\.\d{2}\.\d{4}.*", "", clean_title).strip()
        if self.note_title.endswith(" от"):
            self.note_title = self.note_title[:-3]

        self.setWindowTitle(self.note_title)
        self.resize(1200, 900)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = DynamicStarryScene(background_click_callback=self.on_background_click)

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.setStyleSheet("border: none; background: transparent;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        layout.addWidget(self.view)

        self.overlay_container = QWidget(self)
        self.overlay_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        main_overlay_layout = QVBoxLayout(self.overlay_container)
        main_overlay_layout.setContentsMargins(20, 20, 20, 20)

        top_layout = QHBoxLayout()
        top_layout.addStretch()

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.clock = CosmicClock()
        bottom_layout.addWidget(
            self.clock, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight
        )

        main_overlay_layout.addLayout(top_layout)
        main_overlay_layout.addStretch()
        main_overlay_layout.addLayout(bottom_layout)

        self.overlay_container.raise_()

        self.planets = []
        self.pinned_planet = None
        self.is_wallpaper_mode = False

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.game_loop)
        self.anim_timer.start(33)

        self.build_map()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay_container.resize(self.size())

    def on_background_click(self):
        if self.pinned_planet:
            self.on_planet_pinned(None)
        elif self.sun.pinned:
            self.on_sun_pinned(None)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background-color: #202020; color: white; border: 1px solid #555; } QMenu::item:selected { background-color: #404040; }"
        )

        if not self.is_wallpaper_mode:
            menu.addAction("🖼 Режим обоев").triggered.connect(self.toggle_wallpaper_mode)
        else:
            menu.addAction("🔙 Вернуть в окно").triggered.connect(self.toggle_wallpaper_mode)

        menu.exec(event.globalPos())

    def toggle_wallpaper_mode(self):
        if not self.is_wallpaper_mode:
            self.is_wallpaper_mode = True
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnBottomHint
                | Qt.WindowType.Tool
            )
            self.hide()
            self.scene.setBackgroundBrush(QBrush(Qt.BrushStyle.NoBrush))
            self.showFullScreen()
        else:
            self.is_wallpaper_mode = False
            self.setWindowFlags(Qt.WindowType.Window)
            self.hide()
            self.scene.setBackgroundBrush(QBrush(QColor("#050505")))
            self.showNormal()
            self.activateWindow()

    def update_data_snapshot(self, new_note_data):
        self.note_data = new_note_data
        new_tasks = self.note_data.get("tasks", [])

        if len(new_tasks) != len(self.planets):
            self.build_map()
            return

        for i, planet in enumerate(self.planets):
            new_p_data = new_tasks[i]
            planet.data = new_p_data
            planet.children_data = new_p_data.get("children", [])
            planet.sync_with_data()

            from gm_moon import SubTaskMoonItem

            moons = [c for c in planet.childItems() if isinstance(c, SubTaskMoonItem)]
            new_children_list = planet.children_data
            if len(new_children_list) == len(moons):
                for j, moon in enumerate(moons):
                    moon.data = new_children_list[j]
                    moon.sync_with_data()

        self.update_progress()
        self.scene.update()

    def build_map(self):
        self.scene.clear_items()
        self.planets = []
        self.pinned_planet = None

        tasks = self.note_data.get("tasks", [])

        self.sun = SunItem(
            self.note_title, self.accent, self._calculate_progress(), self.on_sun_pinned
        )
        self.sun.setPos(0, 0)
        self.scene.addItem(self.sun)

        if tasks:
            total_system_moons = 0
            max_potential_radius = 50

            for t in tasks:
                children = t.get("children", [])
                total_system_moons += len(children)

            if total_system_moons == 0:
                total_system_moons = len(tasks)
            saturation_threshold = 200
            density_factor = min(1.0, total_system_moons / saturation_threshold)

            for task in tasks:
                children = task.get("children", [])
                task_moons_count = len(children)
                ratio = task_moons_count / total_system_moons if total_system_moons > 0 else 0.1

                min_r = 50
                max_potential_bonus = 1000
                calc_r = min_r + (ratio * max_potential_bonus * density_factor)
                calc_r = max(min_r, calc_r)
                if calc_r > max_potential_radius:
                    max_potential_radius = calc_r

            target_sun_radius = max(250, max_potential_radius * 1.2)
            self.sun.update_size(target_sun_radius)

            current_orbit_r = target_sun_radius + 150

            for task in tasks:
                children = task.get("children", [])
                task_moons_count = len(children)
                ratio = task_moons_count / total_system_moons if total_system_moons > 0 else 0.1

                min_r = 50
                max_potential_bonus = 1000

                calculated_radius = min_r + (ratio * max_potential_bonus * density_factor)
                calculated_radius += random.uniform(-10, 20)
                calculated_radius = max(min_r, calculated_radius)

                moon_mult = 25
                system_width = calculated_radius + (task_moons_count * moon_mult)
                chaos_gap = random.randint(50, 150)

                current_orbit_r += (system_width / 2) + chaos_gap

                start_angle = random.uniform(0, 360)

                planet = TaskPlanetItem(
                    task,
                    self.accent,
                    current_orbit_r,
                    start_angle,
                    self.on_planet_pinned,
                    self.update_progress,
                    calculated_radius=calculated_radius,
                )
                self.scene.addItem(planet)
                self.planets.append(planet)

                current_orbit_r += system_width / 2

            max_r_in_list = max(p.radius for p in self.planets) if self.planets else 1
            for p in self.planets:
                new_z = 10 + (max_r_in_list - p.radius)
                p.base_z = new_z
                p.setZValue(new_z)

        max_r = self.planets[-1].orbit_radius + 1500 if self.planets else 1000
        rect = QRectF(-max_r, -max_r, max_r * 2, max_r * 2)

        self.scene.init_background(rect)

        QTimer.singleShot(50, self._initial_fit)

    def _calculate_progress(self):
        tasks = self.note_data.get("tasks", [])
        if not tasks:
            return 0.0
        total = 0.0
        for task in tasks:
            children = task.get("children", [])
            if children:
                done_moons = sum(1 for c in children if c.get("checked", False))
                task_percent = done_moons / len(children)
                if task.get("checked", False):
                    task_percent = 1.0
            else:
                task_percent = 1.0 if task.get("checked", False) else 0.0
            total += task_percent
        return total / len(tasks)

    def update_progress(self):
        ratio = self._calculate_progress()
        self.sun.set_progress(ratio)
        if self.save_callback:
            self.save_callback()

    def _initial_fit(self):
        self.view.fitInView(
            self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50),
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def on_sun_pinned(self, sun):
        if sun:
            self.pinned_planet = None
            self.on_planet_pinned(None)
            self.sun.set_pinned_visual(True)
            self._focus_on_rect(self.sun.boundingRect())
        else:
            self.sun.set_pinned_visual(False)
            self._initial_fit()

    def on_planet_pinned(self, planet):
        for p in self.planets:
            if p != planet:
                p.set_pinned(False)
        self.pinned_planet = planet
        if self.pinned_planet:
            self.sun.setOpacity(0.1)
            self.sun.set_pinned_visual(False)
        else:
            self.sun.setOpacity(1.0)

        for p in self.planets:
            if p == self.pinned_planet:
                p.set_pinned(True)
                p.setOpacity(1.0)
            else:
                p.set_pinned(False)
                p.setOpacity(0.15 if self.pinned_planet else 1.0)

    def _focus_on_rect(self, rect):
        self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def game_loop(self):
        self.scene.advance()
        self.sun.advance(1)

        if self.pinned_planet:
            sys_r = self.pinned_planet.get_system_radius()
            planet_scene_pos = self.pinned_planet.scenePos()
            margin = sys_r * 0.1
            total_r = sys_r + margin

            min_view_size = 800
            zoom_size = max(total_r * 2, min_view_size)

            target_rect = QRectF(
                planet_scene_pos.x() - zoom_size / 2,
                planet_scene_pos.y() - zoom_size / 2,
                zoom_size,
                zoom_size,
            )

        elif self.sun.pinned:
            margin = 250
            target_rect = self.sun.boundingRect().adjusted(-margin, -margin, margin, margin)
        else:
            target_rect = self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)

        current_rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
        lerp_speed = 0.05
        new_left = current_rect.left() + (target_rect.left() - current_rect.left()) * lerp_speed
        new_top = current_rect.top() + (target_rect.top() - current_rect.top()) * lerp_speed
        new_width = current_rect.width() + (target_rect.width() - current_rect.width()) * lerp_speed
        new_height = (
            current_rect.height() + (target_rect.height() - current_rect.height()) * lerp_speed
        )
        new_rect = QRectF(new_left, new_top, new_width, new_height)
        self.view.fitInView(new_rect, Qt.AspectRatioMode.KeepAspectRatio)