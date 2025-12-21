# menu_logic.py
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QInputDialog, QMessageBox
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QPoint
from localization import Loc
from styles import Styles

# [NEW] Импортируем нашу карту
from goal_map import GoalMapWindow

class MenuLogic:
    def __init__(self, main_window):
        self.mw = main_window

    def setup_tray(self):
        self.update_tray_menu()
        self.mw.tray.show()

    def update_tray_menu(self):
        tray_menu = QMenu()
        tray_menu.addAction(Loc.t("menu_exit")).triggered.connect(self.mw.close)
        self.mw.tray.setContextMenu(tray_menu)

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.mw.isMinimized() or not self.mw.isVisible():
                self.mw.showNormal()
                self.mw.activateWindow()
            else:
                self.mw.toggle_lock_mode()

    def show_main_menu(self):
        menu = QMenu(self.mw)
        menu.setStyleSheet(Styles.get_menu(self.mw.default_accent))
        
        # --- [NEW] КНОПКА КАРТЫ ЦЕЛЕЙ ---
        # Добавляем её в самый верх или перед разделителем
        map_text = f"🌌 {Loc.t('menu_map', 'Goal Map')}" 
        menu.addAction(map_text).triggered.connect(self.open_goal_map)
        
        menu.addSeparator()

        # 1. Новая заметка
        menu.addAction(Loc.t("menu_new_note")).triggered.connect(self.create_new_note)
        # 2. Переименовать
        menu.addAction(Loc.t("menu_rename")).triggered.connect(self.rename_current_note)
        
        # 3. УДАЛИТЬ ТЕКУЩУЮ ЗАМЕТКУ
        del_text = f"🗑 {Loc.t('ctx_delete')} {Loc.t('current_note', 'Current Note')}"
        del_action = menu.addAction(del_text) 
        del_action.triggered.connect(self.delete_current_note)
        
        # 4. Языки
        lang_menu = menu.addMenu(Loc.t("menu_language"))
        for code, name in Loc.lang_names.items():
            action = QAction(name, self.mw)
            action.setCheckable(True)
            if code == Loc.lang: action.setChecked(True)
            action.triggered.connect(lambda checked, c=code: self.set_language(c))
            lang_menu.addAction(action)
        
        menu.addSeparator()
        
        # 5. Переход к заметкам
        archive_menu = menu.addMenu(Loc.t("menu_go_to"))
        if not self.mw.data.all_notes:
            archive_menu.addAction(Loc.t("menu_empty")).setEnabled(False)
        else:
            for note_id, note_data in self.mw.data.all_notes.items():
                title = note_data.get("title", "No Title")
                action = QAction(title, self.mw)
                action.setCheckable(True)
                if note_id == self.mw.data.current_note_id: action.setChecked(True)
                action.triggered.connect(lambda checked, nid=note_id: self.switch_to_note(nid))
                archive_menu.addAction(action)
        
        menu.exec(self.mw.menu_btn.mapToGlobal(QPoint(0, self.mw.menu_btn.height())))

    # --- Actions ---
    def set_language(self, lang_code):
        Loc.lang = lang_code
        self.mw.update_interface_texts()
        self.update_tray_menu()
        self.mw.data.update_smart_title()
        self.mw.tree_logic.update_title_ui()
        self.mw.data.save_to_disk()
        self.mw.repaint() 

    def create_new_note(self):
        self.mw.save_and_update()
        self.mw.data.create_new_note()
        self.mw.refresh_ui()
        self.mw.inp.clear()

    def switch_to_note(self, nid):
        self.mw.save_and_update()
        if self.mw.data.switch_note(nid):
            self.mw.refresh_ui()

    def rename_current_note(self):
        if not self.mw.data.current_note_id: return
        current = self.mw.data.all_notes[self.mw.data.current_note_id].get("title", "")
        text, ok = QInputDialog.getText(self.mw, Loc.t("rename_title"), Loc.t("rename_label"), text=current)
        if ok and text:
            self.mw.data.rename_current(text)
            self.mw.tree_logic.update_title_ui()
            self.mw.repaint()

    def delete_current_note(self):
        reply = QMessageBox.question(
            self.mw, 
            Loc.t("delete_confirm_title", "Delete Note?"), 
            Loc.t("delete_confirm_text", "Delete this note forever?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self.mw.data, 'delete_note'):
                self.mw.data.delete_note(self.mw.data.current_note_id)
            else:
                cid = self.mw.data.current_note_id
                if cid in self.mw.data.all_notes:
                    del self.mw.data.all_notes[cid]
                    if self.mw.data.all_notes:
                        next_id = list(self.mw.data.all_notes.keys())[0]
                        self.mw.data.switch_note(next_id)
                    else:
                        self.mw.data.create_new_note()
            
            self.mw.data.save_to_disk()
            self.mw.refresh_ui()

    # --- [NEW] Метод открытия карты ---
    def open_goal_map(self):
        # Проверяем, выбрана ли заметка
        nid = self.mw.data.current_note_id
        if not nid or nid not in self.mw.data.all_notes:
            return 
        
        # Берем данные КОНКРЕТНОЙ заметки
        current_note_data = self.mw.data.all_notes[nid]
        
        # Если окно уже есть — закрываем старое (чтобы перерисовать под новую заметку)
        if hasattr(self, 'map_window') and self.map_window.isVisible():
            self.map_window.close()
        
        # [FIX] Передаем self.mw.on_map_data_changed как callback для сохранения!
        self.map_window = GoalMapWindow(
            current_note_data, 
            self.mw.default_accent,
            save_callback=self.mw.on_map_data_changed
        )
        self.map_window.show()

    def force_close_map(self):
        """Принудительно закрывает карту, если она открыта"""
        try:
            if hasattr(self, 'map_window') and self.map_window:
                # Проверяем isVisible, но ловим ошибку, если объект уже удален C++
                if self.map_window.isVisible():
                    self.map_window.close()
        except RuntimeError:
            # Если окно уже удалено (C++ object deleted), просто игнорируем
            pass