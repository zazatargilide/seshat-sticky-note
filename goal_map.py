#goal_map.py

import math
import re
import random
import os
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
                             QGraphicsItem, QMenu, QApplication)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import (QColor, QBrush, QPainter, QPen, 
                         QPixmap, QRadialGradient, QTransform)

# Импортируем наши классы
from gm_planet import TaskPlanetItem
from gm_sun import SunItem

# --- ДАННЫЕ ЗОДИАКА ---
ZODIAC_SIGNS = [
    ("Capricorn", (12, 22), (1, 19)), ("Aquarius", (1, 20), (2, 18)),
    ("Pisces", (2, 19), (3, 20)),     ("Aries", (3, 21), (4, 19)),
    ("Taurus", (4, 20), (5, 20)),     ("Gemini", (5, 21), (6, 20)),
    ("Cancer", (6, 21), (7, 22)),     ("Leo", (7, 23), (8, 22)),
    ("Virgo", (8, 23), (9, 22)),      ("Libra", (9, 23), (10, 22)),
    ("Scorpio", (10, 23), (11, 21)),  ("Sagittarius", (11, 22), (12, 21))
]

ZODIAC_PATTERNS = {
    "Aries": [(0,20), (30,0), (60,10), (80,30)],
    "Taurus": [(0,0), (20,20), (40,10), (20,-20), (60,-30)],
    "Gemini": [(0,0), (0,60), (40,60), (40,0)],
    "Cancer": [(0,0), (20,20), (40,0), (20,-20)],
    "Leo": [(0,0), (20,-20), (40,-10), (50,10), (40,30), (10,40)],
    "Virgo": [(0,0), (20,20), (40,10), (60,30), (50,50)],
    "Libra": [(0,20), (30,20), (15,0), (15,40)],
    "Scorpio": [(0,0), (10,20), (20,10), (30,30), (40,20), (40,50)],
    "Sagittarius": [(0,0), (20,0), (10,20), (30,20), (20,40), (40,40)],
    "Capricorn": [(0,0), (20,10), (40,0), (30,-20)],
    "Aquarius": [(0,0), (10,10), (20,0), (30,10), (40,0)],
    "Pisces": [(0,0), (20,20), (40,0)]
}

class ZodiacOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        now = datetime.now()
        self.sign_name = "Unknown"
        for name, (sm, sd), (em, ed) in ZODIAC_SIGNS:
            start = datetime(now.year, sm, sd)
            end = datetime(now.year, em, ed)
            if name == "Capricorn":
                if (now.month == 12 and now.day >= 22) or (now.month == 1 and now.day <= 19):
                    self.sign_name = name; break
            elif start <= now <= end:
                self.sign_name = name; break
        
        self.points = ZODIAC_PATTERNS.get(self.sign_name, [])

    def paintEvent(self, event):
        if self.sign_name == "Unknown" or not self.points: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(60, 60) 
        
        pen = QPen(QColor(255,255,255,150), 2) 
        painter.setPen(pen)
        if len(self.points) > 1:
            for i in range(len(self.points)-1):
                painter.drawLine(QPointF(*self.points[i]), QPointF(*self.points[i+1]))
        
        painter.setPen(Qt.PenStyle.NoPen)
        for x, y in self.points:
            grad = QRadialGradient(QPointF(x,y), 8)
            grad.setColorAt(0, QColor(255,255,255,255))
            grad.setColorAt(1, QColor(255,255,255,0))
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(QPointF(x, y), 8, 8)
            
            painter.setBrush(QBrush(QColor(255,255,255,255)))
            painter.drawEllipse(QPointF(x, y), 3, 3)

class DynamicStarryScene(QGraphicsScene):
    def __init__(self, background_click_callback=None):
        super().__init__()
        self.stars = []
        self.constellations = []
        self.ghost_galaxies = [] 
        self.bg_pixmap = None
        self.time_counter = 0
        self.click_callback = background_click_callback
        
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
        self.constellations = []
        self.ghost_galaxies = []

    def init_background(self, rect):
        if self.stars: return 
        area = rect.adjusted(-3000, -3000, 3000, 3000)
        w, h = int(area.width()), int(area.height())
        cx, cy = area.center().x(), area.center().y()
        
        for _ in range(5):
            gx = cx + random.uniform(-w/2, w/2)
            gy = cy + random.uniform(-h/2, h/2)
            gw = random.uniform(500, 1200)
            gh = random.uniform(300, 800)
            angle = random.uniform(0, 360)
            color = QColor(random.choice(["#330044", "#002244", "#004444"]))
            color.setAlpha(40) 
            self.ghost_galaxies.append((gx, gy, gw, gh, angle, color))

        for _ in range(1200):
            sx = cx + random.uniform(-w/2, w/2)
            sy = cy + random.uniform(-h/2, h/2)
            vx = random.uniform(-0.05, 0.05)
            vy = random.uniform(-0.05, 0.05)
            stype = random.choice(['dot', 'dot', 'dot', 'cross4'])
            if random.random() > 0.99: 
                size = random.uniform(5.0, 9.0)
                stype = 'giant'
            else: 
                size = random.uniform(1.0, 3.5)
            color = QColor(255, 255, 255)
            color.setAlpha(random.randint(100, 255))
            self.stars.append({'x': sx, 'y': sy, 'vx': vx, 'vy': vy, 's': size, 't': stype, 'c': color, 'flash_timer': random.randint(0, 500)})

    def advance(self):
        super().advance()
        self.time_counter += 1
        for s in self.stars:
            s['x'] += s['vx']
            s['y'] += s['vy']
            if random.random() > 0.999: s['flash_timer'] = 200
            if s['flash_timer'] > 0: s['flash_timer'] -= 1
            
        if self.time_counter % 150 == 0:
            sample = random.sample(self.stars, min(len(self.stars), 60))
            for i in range(len(sample)):
                s1 = sample[i]
                for j in range(i+1, len(sample)):
                    s2 = sample[j]
                    dist = math.hypot(s1['x']-s2['x'], s1['y']-s2['y'])
                    if 50 < dist < 300 and random.random() > 0.9:
                         self.constellations.append({'s1':s1, 's2':s2, 'life': 400, 'max_life': 400})
        
        self.constellations = [c for c in self.constellations if c['life'] > 0]
        for c in self.constellations: c['life'] -= 1
        self.update() 

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QBrush(QColor("#050505")))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.bg_pixmap: 
            painter.drawPixmap(rect.toRect(), self.bg_pixmap.scaled(rect.size().toSize(), Qt.AspectRatioMode.KeepAspectRatioByExpanding))
        painter.setPen(Qt.PenStyle.NoPen)
        for gx, gy, gw, gh, angle, color in self.ghost_galaxies:
            painter.save()
            painter.translate(gx, gy)
            painter.rotate(angle)
            grad = QRadialGradient(QPointF(0,0), gw/2)
            grad.setColorAt(0, color)
            grad.setColorAt(1, QColor(0,0,0,0))
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(QRectF(-gw/2, -gh/2, gw, gh))
            painter.restore()
        pen = QPen(QColor(255,255,255), 1.5)
        for c in self.constellations:
            life_ratio = c['life'] / c['max_life']
            alpha = int(150 * math.sin(life_ratio * math.pi))
            if alpha > 0: 
                pen.setColor(QColor(200, 220, 255, alpha))
                painter.setPen(pen)
                painter.drawLine(QPointF(c['s1']['x'], c['s1']['y']), QPointF(c['s2']['x'], c['s2']['y']))
        painter.setPen(Qt.PenStyle.NoPen)
        for s in self.stars:
            painter.setBrush(QBrush(s['c']))
            pt = QPointF(s['x'], s['y'])
            size = s['s']
            if s['flash_timer'] > 0:
                ratio = math.sin((s['flash_timer']/200.0)*math.pi)
                size += ratio * 3.0
                painter.setBrush(QBrush(QColor(255,255,255,255)))
            if s['t'] == 'giant':
                 glow = QRadialGradient(pt, size*5)
                 glow.setColorAt(0, QColor(255,255,255,100))
                 glow.setColorAt(1, QColor(0,0,0,0))
                 painter.setBrush(QBrush(glow))
                 painter.drawEllipse(pt, size*5, size*5)
                 painter.setBrush(QBrush(QColor(255,255,255,255)))
            elif s['t'] == 'cross4':
                painter.setPen(QPen(s['c'], 1.0))
                rot = self.time_counter * 0.05
                for i in range(4): 
                    rad = math.radians((i * 90) + rot)
                    painter.drawLine(pt, QPointF(pt.x() + math.cos(rad)*size*4, pt.y() + math.sin(rad)*size*4))
                painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(pt, size, size)

class GoalMapWindow(QWidget):
    def __init__(self, note_data, default_accent, save_callback=None):
        super().__init__()
        self.note_data = note_data
        self.accent = QColor(default_accent)
        self.save_callback = save_callback
        
        raw_title = self.note_data.get("title", "Note")
        clean_title = raw_title.split(" - ")[0]
        self.note_title = re.sub(r'[:]?\s*\d{2}\.\d{2}\.\d{4}.*', '', clean_title).strip()
        if self.note_title.endswith(" от"): self.note_title = self.note_title[:-3]
            
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
        layout.addWidget(self.view)
        
        self.zodiac = ZodiacOverlay(self)
        self.zodiac.move(20, 20)
        self.zodiac.raise_()
        
        self.planets = []
        self.pinned_planet = None
        self.is_wallpaper_mode = False 
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.game_loop)
        self.anim_timer.start(16)

        self.build_map()

    def on_background_click(self):
        if self.pinned_planet:
            self.on_planet_pinned(None)
        elif self.sun.pinned:
            self.on_sun_pinned(None)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #202020; color: white; border: 1px solid #555; } QMenu::item:selected { background-color: #404040; }")
        
        if not self.is_wallpaper_mode:
            menu.addAction("🖼 Режим обоев").triggered.connect(self.toggle_wallpaper_mode)
        else:
            menu.addAction("🔙 Вернуть в окно").triggered.connect(self.toggle_wallpaper_mode)
            
        menu.exec(event.globalPos())

    def toggle_wallpaper_mode(self):
        if not self.is_wallpaper_mode:
            self.is_wallpaper_mode = True
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.Tool)
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
        
        self.sun = SunItem(self.note_title, self.accent, self._calculate_progress(), self.on_sun_pinned)
        self.sun.setPos(0, 0)
        self.scene.addItem(self.sun)
        
        if tasks:
            total_system_moons = 0
            for t in tasks:
                total_system_moons += len(t.get("children", []))
            
            if total_system_moons == 0: total_system_moons = len(tasks) 

            saturation_threshold = 200 
            density_factor = min(1.0, total_system_moons / saturation_threshold)
            
            current_orbit_r = 400 + (total_system_moons * 2) 
            
            max_planet_radius_generated = 0 

            for task in tasks:
                children = task.get("children", [])
                task_moons_count = len(children)
                
                ratio = task_moons_count / total_system_moons if total_system_moons > 0 else 0.1
                
                min_r = 60 
                max_potential_bonus = 8000 
                
                calculated_radius = min_r + (ratio * max_potential_bonus * density_factor)
                
                calculated_radius += random.uniform(-20, 30)
                calculated_radius = max(min_r, calculated_radius)
                
                if calculated_radius > max_planet_radius_generated:
                    max_planet_radius_generated = calculated_radius

                moon_mult = 30 
                system_width = calculated_radius + (task_moons_count * moon_mult)
                chaos_gap = random.randint(100, 500)
                
                current_orbit_r += (system_width / 2) + chaos_gap
                
                start_angle = random.uniform(0, 360)
                
                planet = TaskPlanetItem(
                    task, 
                    self.accent, 
                    current_orbit_r, 
                    start_angle, 
                    self.on_planet_pinned, 
                    self.update_progress, 
                    calculated_radius=calculated_radius
                )
                self.scene.addItem(planet)
                self.planets.append(planet)
                
                current_orbit_r += (system_width / 2)
            
            # --- ИСПРАВЛЕНИЕ СЛОЕВ (Z-ORDER) ---
            # Чем больше радиус планеты, тем ниже она лежит. 
            # Маленькие планеты будут "всплывать" над орбитами больших.
            max_r_in_list = max(p.radius for p in self.planets) if self.planets else 1
            for p in self.planets:
                # 100 - это запас, (max_r - p.radius) дает преимущество маленьким
                new_z = 10 + (max_r_in_list - p.radius)
                p.base_z = new_z # Запоминаем базовый уровень
                p.setZValue(new_z)

            target_sun_radius = max(400, max_planet_radius_generated * 1.5)
            self.sun.update_size(target_sun_radius)

        max_r = self.planets[-1].orbit_radius + 3000 if self.planets else 2000
        rect = QRectF(-max_r, -max_r, max_r*2, max_r*2)
        
        self.scene.init_background(rect)
        
        QTimer.singleShot(50, self._initial_fit)

    def _calculate_progress(self):
        tasks = self.note_data.get("tasks", [])
        if not tasks: return 0.0
        total = 0.0
        for task in tasks:
            children = task.get("children", [])
            if children:
                done_moons = sum(1 for c in children if c.get("checked", False))
                task_percent = done_moons / len(children)
                if task.get("checked", False): task_percent = 1.0
            else:
                task_percent = 1.0 if task.get("checked", False) else 0.0
            total += task_percent
        return total / len(tasks)

    def update_progress(self):
        ratio = self._calculate_progress()
        self.sun.set_progress(ratio)
        if self.save_callback: self.save_callback()

    def _initial_fit(self):
        self.view.fitInView(self.scene.itemsBoundingRect().adjusted(-200,-200,200,200), Qt.AspectRatioMode.KeepAspectRatio)

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
            if p != planet: p.set_pinned(False)
        self.pinned_planet = planet
        if self.pinned_planet:
            self.sun.setOpacity(0.1); self.sun.set_pinned_visual(False)
        else:
            self.sun.setOpacity(1.0)
            
        for p in self.planets:
            if p == self.pinned_planet:
                p.set_pinned(True); p.setOpacity(1.0)
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
            
            target_rect = QRectF(
                planet_scene_pos.x() - total_r, 
                planet_scene_pos.y() - total_r, 
                total_r * 2, 
                total_r * 2
            )
            
        elif self.sun.pinned:
             margin = 250
             target_rect = self.sun.boundingRect().adjusted(-margin, -margin, margin, margin)
        else:
            target_rect = self.scene.itemsBoundingRect().adjusted(-300, -300, 300, 300)
            
        current_rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
        lerp_speed = 0.05 
        new_left = current_rect.left() + (target_rect.left() - current_rect.left()) * lerp_speed
        new_top = current_rect.top() + (target_rect.top() - current_rect.top()) * lerp_speed
        new_width = current_rect.width() + (target_rect.width() - current_rect.width()) * lerp_speed
        new_height = current_rect.height() + (target_rect.height() - current_rect.height()) * lerp_speed
        new_rect = QRectF(new_left, new_top, new_width, new_height)
        self.view.fitInView(new_rect, Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.zodiac.move(20, 20)