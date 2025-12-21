#app.py

import sys
# Исправленный импорт для QSystemTrayIcon (он в QtWidgets)
from PyQt6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon
from PyQt6.QtCore import Qt

# 1. UI и Компоненты (Импорт из widgets, а не components)
from ui_setup import UISetup
from widgets import FloatingUnlockBtn

# 2. Менеджеры
from data_manager import DataManager
from effects import RainbowManager
from localization import Loc 

# 3. Логические модули
from tree_logic import TreeLogic
from window_logic import WindowLogic
from input_logic import InputLogic
from menu_logic import MenuLogic
from style_logic import StyleLogic

class StickyNote(QMainWindow):
    def __init__(self):
        super().__init__()
        self.locked = False
        self.moving = False 
        
        # --- A. ИНИЦИАЛИЗАЦИЯ ДАННЫХ ---
        self.data = DataManager()
        self.rainbow = RainbowManager()
        self.default_accent = "#7c4dff"
        
        # --- B. ПОСТРОЕНИЕ UI ---
        self.unlock_overlay = FloatingUnlockBtn(self.toggle_lock_mode)
        UISetup.setup_ui(self) 
        
        # --- C. ПОДКЛЮЧЕНИЕ ЛОГИКИ ---
        self.tree_logic = TreeLogic(self)
        self.win_logic = WindowLogic(self)
        self.menu_logic = MenuLogic(self)
        self.title.doubleClicked.connect(self.menu_logic.rename_current_note)
        self.style_logic = StyleLogic(self)
        self.input_logic = InputLogic(self)
        
        # --- D. НАСТРОЙКА ---
        self.input_logic.setup()      
        self.menu_logic.setup_tray()  
        
        # --- E. СТАРТ ---
        # Подключаем сигнал радуги напрямую к логике стилей
        self.rainbow.color_changed.connect(self.style_logic.apply_dynamic_styles)
        
        # Применяем стартовый стиль
        self.style_logic.apply_dynamic_styles(self.default_accent)
        
        self.load_from_file()
        self.update_interface_texts()
        self.show()

    # --- PROXY METHODS (Связующие методы) ---
    
    # Этот метод вызывает TreeLogic, поэтому он должен быть здесь
    # Мы просто перенаправляем запрос в style_logic
    def apply_dynamic_styles(self, accent):
        self.style_logic.apply_dynamic_styles(accent)

    def refresh_ui(self): self.tree_logic.refresh_ui_from_data()
    def save_and_update(self): self.tree_logic.save_and_update()
    
    def update_interface_texts(self):
        self.inp.setPlaceholderText(Loc.t("new_task_hint"))
        self.tree_logic.update_title_ui()
        self.tree.viewport().update()

    def toggle_lock_mode(self): self.win_logic.toggle_lock_mode()
    
    # Events
    def mousePressEvent(self, e): self.win_logic.mousePressEvent(e)
    def mouseMoveEvent(self, e): self.win_logic.mouseMoveEvent(e)
    def mouseReleaseEvent(self, e): self.win_logic.mouseReleaseEvent(e)
    def resizeEvent(self, e): 
        self.win_logic.resizeEvent(e)
        super().resizeEvent(e)
    
    def wheelEvent(self, e):
        self.win_logic.wheelEvent(e)
        if self.locked: 
            e.accept()
            return
        super().wheelEvent(e)
    
    def keyPressEvent(self, e):
        if not self.locked and e.key() == Qt.Key.Key_Delete:
            item = self.tree.currentItem()
            if item: self.tree_logic.delete_item(item)
        super().keyPressEvent(e)
    
    def load_from_file(self):
        self.data.load_from_file()
        if self.data.current_note_id: self.refresh_ui()
    
    def on_map_data_changed(self):
        """
        Callback для карты планет.
        Вызывается, когда в космосе меняется статус задачи.
        """        
        self.data.save_to_disk()
        self.refresh_ui()

    def refresh_map_if_open(self):
        # Проверяем, есть ли окно карты
        if hasattr(self, 'menu_logic') and hasattr(self.menu_logic, 'map_window'):
            mw = self.menu_logic.map_window
            if mw and mw.isVisible():
                # 1. Получаем ID текущей заметки
                current_id = self.data.current_note_id
                if current_id in self.data.all_notes:
                    # 2. Берем САМУЮ СВЕЖУЮ версию данных этой заметки
                    fresh_data = self.data.all_notes[current_id]
                    
                    # 3. Вызываем наш новый метод "хирургической" замены
                    mw.update_data_snapshot(fresh_data)

    def closeEvent(self, e):
        # Закрываем карту, если открыта
        self.menu_logic.force_close_map()
        
        # Сохраняемся
        self.tree_logic.save_and_update()
        
        # Убираем иконку из трея, чтобы она не висела призраком
        if hasattr(self, 'tray'):
            self.tray.hide()
            
        # ЖЕСТКИЙ ВЫХОД: Убиваем приложение полностью
        QApplication.instance().quit()