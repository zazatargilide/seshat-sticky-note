# tree_logic.py
from localization import Loc
from tree_core import TreeCore

# Импортируем наши 4 модуля
from tree_io import TreeIO
from tree_menu import TreeMenu
from tree_progress import TreeProgress


class TreeLogic:
    def __init__(self, main_window):
        self.mw = main_window

        # 1. Инициализируем модули
        self.io = TreeIO(main_window.tree)
        self.progress = TreeProgress(main_window)

        # Core нужно передать функцию сохранения, так как она вызывается отовсюду
        self.core = TreeCore(main_window, callback_save=self.save_and_update)

        self.menu = TreeMenu(main_window, self.core)

    # --- Главные методы (Facade) ---

    def save_and_update(self):
        """Главная точка синхронизации: UI -> Data -> UI"""
        # 1. Собираем данные
        tasks = self.io.collect_data()
        # 2. Сохраняем в менеджер данных
        self.mw.data.save_current_state(tasks)
        # 3. Обновляем прогрессбар
        self.progress.calculate_and_update()
        # 4. Обновляем заголовок
        self.update_title_ui()

    def refresh_ui_from_data(self):
        """Загрузка: Data -> UI"""
        note_data = self.mw.data.all_notes.get(self.mw.data.current_note_id, {})
        tasks = note_data.get("tasks", [])
        self.io.load_data(tasks)
        self.progress.calculate_and_update()
        self.update_title_ui()

    def update_title_ui(self):
        if self.mw.data.current_note_id:
            title = self.mw.data.all_notes[self.mw.data.current_note_id].get(
                "title", Loc.t("title_default")
            )
            self.mw.title.setText(title)

    # --- Проброс событий (Proxy) ---
    # App.py и InputLogic будут дергать эти методы, а мы перекинем их в Core или Menu

    def add_task(self):
        text = self.mw.inp.text().strip()
        self.core.add_task(text)

    def delete_item(self, item):
        self.core.delete_item(item)

    def on_item_changed(self, item, col):
        self.core.on_item_changed(item)

    def show_context_menu(self, pos):
        self.menu.show(pos)

    def move_item_vertical(self, direction):
        self.core.move_vertical(direction)

    def indent_item(self):
        self.core.indent()

    def unindent_item(self):
        self.core.unindent()
