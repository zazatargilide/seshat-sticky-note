#tree_menu

from PyQt6.QtWidgets import QMenu
from localization import Loc
from task_tree import TodoItem

class TreeMenu:
    def __init__(self, main_window, core_logic):
        self.mw = main_window
        self.core = core_logic 

    def show(self, position):
        if self.mw.locked: return
        item = self.mw.tree.itemAt(position)
        if not item: return 
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background-color: #2d2d2d; border: 1px solid #444; padding: 5px; }
            QMenu::item { padding: 5px 20px; color: #e0e0e0; }
            QMenu::item:selected { background-color: #7c4dff; color: white; }
        """)
        
        # 1. Удаление
        menu.addAction(Loc.t("ctx_delete")).triggered.connect(lambda: self.core.delete_item(item))
        
        menu.addSeparator()

        # --- [NEW] Логика Зачеркнуть / Восстановить ---
        is_cancelled = getattr(item, 'cancelled', False)
        
        if is_cancelled:
            # Если уже зачеркнуто -> показываем "Восстановить"
            menu.addAction(Loc.t("ctx_restore")).triggered.connect(lambda: self._toggle_cancel(item))
        else:
            # Если активно -> показываем "Зачеркнуть"
            menu.addAction(Loc.t("ctx_cancel")).triggered.connect(lambda: self._toggle_cancel(item))
        # ----------------------------------------------
        
        menu.addSeparator()
        
        # 3. Подзадача
        menu.addAction(Loc.t("ctx_subtask")).triggered.connect(lambda: self._add_sub(item))
        
        menu.exec(self.mw.tree.viewport().mapToGlobal(position))

    def _toggle_cancel(self, item):
        # Переключаем статус
        is_canc = getattr(item, 'cancelled', False)
        item.cancelled = not is_canc
        
        # Перерисовываем дерево, чтобы сработал стиль зачеркивания
        self.mw.tree.viewport().update()
        # Сохраняем
        self.core.callback_save()
        self.mw.refresh_map_if_open()

    def _add_sub(self, item):
        # Создаем подпункт
        child = TodoItem(item, "Подпункт")
        # Разворачиваем родителя, чтобы видеть дитя
        item.setExpanded(True)
        
        # Принудительно скроллим экран к новому элементу
        self.mw.tree.scrollToItem(child)
        
        # Включаем редактирование
        self.mw.tree.editItem(child, 0)
        self.core.callback_save()