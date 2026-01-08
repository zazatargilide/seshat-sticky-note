# data_history.py
import json


class DataHistory:
    def __init__(self, data_manager):
        self.dm = data_manager  # Ссылка на DataManager
        self.history = []
        self.history_index = -1

    def add_to_history(self, tasks):
        """Сохраняет список задач текущей заметки в историю (Легкий снепшот)"""
        # Глубокая копия списка задач через JSON (самый простой способ для PySide)
        snapshot = json.loads(json.dumps(tasks))

        # Обрезаем "будущее", если пользователь откатывался назад и начал новое действие
        if self.history_index < len(self.history) - 1:
            self.history = self.history[: self.history_index + 1]

        self.history.append(snapshot)
        self.history_index += 1

        # Ограничение размера
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            tasks = self.history[self.history_index]
            self.dm.all_notes[self.dm.current_note_id]["tasks"] = tasks
            self.dm.save_to_disk(skip_history=True)  # Не писать в историю
            return True
        return False

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            tasks = self.history[self.history_index]
            self.dm.all_notes[self.dm.current_note_id]["tasks"] = tasks
            self.dm.save_to_disk(skip_history=True)  # Не писать в историю
            return True
        return False
