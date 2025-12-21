import math
import re
import random
import os
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
                             QGraphicsItem, QGraphicsPathItem, QMenu, QApplication)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import (QColor, QBrush, QPainter, QPainterPath, QPen, 
                         QPixmap, QPolygonF, QRadialGradient, QFont, QAction, QScreen)

from gm_planet import TaskPlanetItem
from gm_sun import SunItem

# --- ZODIAC DATA ---
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
                if now.month == 12 and now.day >= 22: self.sign_name = name; break
                if now.month == 1 and now.day <= 19: self.sign_name = name; break
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
        painter.setBrush(QBrush(QColor(255,255,255,255))) 
        for x, y in self.points:
            grad = QRadialGradient(QPointF(x,y), 8)
            grad.setColorAt(0, QColor(255,255,255,255))
            grad.setColorAt(1, QColor(255,255,255,0))
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(QPointF(x, y), 8, 8)
            painter.setBrush(QBrush(QColor(255,255,255,255)))
            painter.drawEllipse(QPointF(x, y), 3, 3)

class GoalMapWindow(QWidget):
    def __init__(self, note_data, default_accent, save_callback=None):
        super().__init__()
        self.note_data = note_data
        self.accent = QColor(default_accent)
        self.save_callback = save_callback
        
        self.planet_size_mode = 3
        
        raw_title = self.note_data.get("title", "Note")
        clean_title = raw_title.split(" - ")[0]
        clean_title = re.sub(r'[:]?\s*\d{2}\.\d{2}\.\d{4}.*', '', clean_title).strip()
        if clean_title.endswith(" от"): clean_title = clean_title[:-3]
        self.note_title = clean_title if clean_title else "System"
            
        self.setWindowTitle(self.note_title) 
        self.resize(1200, 900)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene = DynamicStarryScene() 
        self.scene.setBackgroundBrush(QBrush(QColor("#050505")))
        
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

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #202020; color: white; border: 1px solid #555; } QMenu::item:selected { background-color: #404040; }")
        
        size_menu = menu.addMenu(f"🌍 Размер планет (Сейчас: {self.planet_size_mode})")
        size_menu.setStyleSheet("QMenu { background-color: #252525; }")
        
        a1 = size_menu.addAction("Размер 1 (Компактный)")
        a2 = size_menu.addAction("Размер 2 (Средний)")
        a3 = size_menu.addAction("Размер 3 (Огромный)")
        
        a1.triggered.connect(lambda: self.set_planet_size(1))
        a2.triggered.connect(lambda: self.set_planet_size(2))
        a3.triggered.connect(lambda: self.set_planet_size(3))
        
        menu.addSeparator()

        if not self.is_wallpaper_mode:
            action_wall = menu.addAction("🖼 Режим обоев (Поверх иконок)")
            action_wall.triggered.connect(self.toggle_wallpaper_mode)
        else:
            action_window = menu.addAction("🔙 Вернуть в окно")
            action_window.triggered.connect(self.toggle_wallpaper_mode)
            
        menu.exec(event.globalPos())

    def set_planet_size(self, mode):
        if self.planet_size_mode != mode:
            self.planet_size_mode = mode
            self.build_map()

    def toggle_wallpaper_mode(self):
        if not self.is_wallpaper_mode:
            self.is_wallpaper_mode = True
            flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.Tool
            self.hide()
            self.setWindowFlags(flags)
            self.scene.setBackgroundBrush(QBrush(Qt.BrushStyle.NoBrush))
            self.showFullScreen()
        else:
            self.is_wallpaper_mode = False
            self.hide()
            self.setWindowFlags(Qt.WindowType.Window)
            self.scene.setBackgroundBrush(QBrush(QColor("#050505")))
            self.showNormal()
            self.activateWindow()

    def refresh_map_state(self):
        pass

    def update_data_snapshot(self, new_note_data):
        """
        ЖЕСТКОЕ обновление данных
        """
        self.note_data = new_note_data
        new_tasks = self.note_data.get("tasks", [])
        
        # Если число задач изменилось — перестраиваем всё
        if len(new_tasks) != len(self.planets):
            self.build_map()
            return

        for i, planet in enumerate(self.planets):
            new_p_data = new_tasks[i]
            
            # [FIX] ОБЯЗАТЕЛЬНО обновляем ссылку на данные в самой планете
            planet.data = new_p_data 
            
            # [FIX] И самое главное — обновляем список детей!
            # Иначе при повторном клике refresh_geometry будет смотреть в старый список детей
            planet.children_data = new_p_data.get("children", [])
            
            # Принудительно вызываем sync_with_data, чтобы применились цвета и разрушения
            planet.sync_with_data()
            
            # Теперь синхронизируем луны
            from gm_moon import SubTaskMoonItem
            moons = [c for c in planet.childItems() if isinstance(c, SubTaskMoonItem)]
            
            new_children_list = planet.children_data
            if len(new_children_list) == len(moons):
                for j, moon in enumerate(moons):
                    moon.data = new_children_list[j]
                    moon.sync_with_data()
            
        self.update_progress()
        self.scene.update() # Форсируем перерисовку сцены

    def build_map(self):
        self.scene.clear_items()
        self.planets = []
        self.pinned_planet = None
        
        tasks = self.note_data.get("tasks", [])
        
        self.sun = SunItem(self.note_title, self.accent, self._calculate_progress(), self.on_sun_pinned)
        self.sun.setPos(0, 0)
        self.scene.addItem(self.sun)
        
        if tasks:
            count = len(tasks)
            start_orbit = 350 if self.planet_size_mode == 1 else (500 if self.planet_size_mode == 2 else 850)
            current_orbit_r = start_orbit
            angle_step = 360 / count if count > 0 else 0
            
            for i, task in enumerate(tasks):
                moons_count = len(task.get("children", []))
                
                base_p_size = 150 if self.planet_size_mode == 1 else (250 if self.planet_size_mode == 2 else 400)
                moon_mult = 15 if self.planet_size_mode == 1 else (30 if self.planet_size_mode == 2 else 60)
                
                system_radius = base_p_size + (moons_count * moon_mult)
                current_orbit_r += system_radius
                
                start_angle = i * angle_step
                
                planet = TaskPlanetItem(task, self.accent, current_orbit_r, start_angle, self.on_planet_pinned, self.update_progress, size_mode=self.planet_size_mode)
                self.scene.addItem(planet)
                self.planets.append(planet)
                
                current_orbit_r += system_radius + (50 if self.planet_size_mode == 1 else 150)

        max_r = self.planets[-1].orbit_radius + 1500 if self.planets else 2000
        rect = QRectF(-max_r, -max_r, max_r*2, max_r*2)
        self.scene.init_background(rect)
        QTimer.singleShot(50, self._initial_fit)

    def _calculate_progress(self):
        tasks = self.note_data.get("tasks", [])
        if not tasks: return 0.0
        
        total_percentage_sum = 0.0
        
        for task in tasks:
            children = task.get("children", [])
            
            if children:
                done_moons = sum(1 for c in children if c.get("checked", False))
                task_percent = done_moons / len(children)
                if task.get("checked", False):
                    task_percent = 1.0
            else:
                task_percent = 1.0 if task.get("checked", False) else 0.0
            
            total_percentage_sum += task_percent

        return total_percentage_sum / len(tasks)

    def update_progress(self):
        ratio = self._calculate_progress()
        self.sun.set_progress(ratio)
        if self.save_callback:
            self.save_callback()

    def _initial_fit(self):
        self.view.fitInView(self.scene.itemsBoundingRect().adjusted(-200,-200,200,200), Qt.AspectRatioMode.KeepAspectRatio)

    def on_sun_pinned(self, sun):
        if sun:
            self.pinned_planet = None
            self.on_planet_pinned(None) # Reset planets
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
            item_rect = self.pinned_planet.boundingRect()
            target_rect = self.pinned_planet.mapRectToScene(item_rect)
            margin = 250
            target_rect = target_rect.adjusted(-margin, -margin, margin, margin)
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

class DynamicStarryScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.stars = []
        self.constellations = []
        self.ghost_galaxies = [] 
        self.bg_pixmap = None
        self.time_counter = 0
        
        for ext in ["jpg", "png", "jpeg"]:
             if os.path.exists(f"space_bg.{ext}"):
                 self.bg_pixmap = QPixmap(f"space_bg.{ext}")
                 break

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

        for _ in range(1000):
            sx = cx + random.uniform(-w/2, w/2)
            sy = cy + random.uniform(-h/2, h/2)
            vx = random.uniform(-0.05, 0.05)
            vy = random.uniform(-0.05, 0.05)
            stype = random.choice(['dot', 'dot', 'cross4'])
            
            if random.random() > 0.99: 
                size = random.uniform(5.0, 9.0)
                stype = 'giant'
            else: 
                size = random.uniform(1.0, 3.5)
            
            color = QColor(255, 255, 255)
            color.setAlpha(random.randint(150, 255))
            self.stars.append({'x': sx, 'y': sy, 'vx': vx, 'vy': vy, 's': size, 't': stype, 'c': color, 'flash_timer': random.randint(0, 500)})

    def advance(self):
        super().advance()
        self.time_counter += 1
        
        for s in self.stars:
            s['x'] += s['vx']
            s['y'] += s['vy']
            if random.random() > 0.9998: s['flash_timer'] = 200
            if s['flash_timer'] > 0: s['flash_timer'] -= 1
        
        if self.time_counter % 200 == 0:
            sample = random.sample(self.stars, min(len(self.stars), 60))
            for i in range(len(sample)):
                s1 = sample[i]
                for j in range(i+1, len(sample)):
                    s2 = sample[j]
                    dist = math.hypot(s1['x']-s2['x'], s1['y']-s2['y'])
                    if 50 < dist < 300 and random.random() > 0.85:
                         self.constellations.append({'s1':s1, 's2':s2, 'life': 400, 'max_life': 400})
        
        self.constellations = [c for c in self.constellations if c['life'] > 0]
        for c in self.constellations: c['life'] -= 1

    def drawBackground(self, painter, rect):
        bg_brush = self.backgroundBrush()
        
        if bg_brush.style() == Qt.BrushStyle.NoBrush:
            return

        painter.fillRect(rect, bg_brush)

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
            alpha = int(180 * math.sin((c['life']/c['max_life']) * math.pi))
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
                 painter.drawEllipse(pt, size, size)
                 
            elif s['t'] == 'dot': 
                painter.drawEllipse(pt, size, size)
                
            elif s['t'] == 'cross4':
                arms = 4
                radius = size * 4
                rotation = self.time_counter * 0.05
                painter.setPen(QPen(s['c'], 1.0))
                for i in range(arms):
                    rad = math.radians((i * 90) + rotation)
                    painter.drawLine(pt, QPointF(pt.x() + math.cos(rad)*radius, pt.y() + math.sin(rad)*radius))
                painter.setPen(Qt.PenStyle.NoPen)