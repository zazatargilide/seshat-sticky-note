# data_manager.py
import json
import os
import uuid

from PyQt6.QtCore import QDateTime

# Импортируем наши новые модули
from data_history import DataHistory
from data_parser import DataParser
from localization import Loc


class DataManager:
    def __init__(self):
        self.filename = "seshat_db.json"
        self.all_notes = {}
        self.current_note_id = None

        self.start_time = None
        self.finish_time = None

        # --- Инициализация модулей ---
        self.history = DataHistory(self)
        self.parser = DataParser(self)

        self.load_from_file()

    def load_from_file(self):
        if not os.path.exists(self.filename):
            self.create_new_note()
            return

        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)

                if "language" in data:
                    Loc.lang = data["language"]

                self.all_notes = data.get("notes", {})
                self.current_note_id = data.get("current_note_id")

                if not self.all_notes:
                    self.create_new_note()
                    return

                if not self.current_note_id or self.current_note_id not in self.all_notes:
                    self.current_note_id = list(self.all_notes.keys())[0]

                # Делегируем парсинг времени
                self.parser.load_timings()

        except Exception as e:
            print(f"Error loading: {e}")
            # Если файл битый, не затираем его сразу, а создаем новую сессию в памяти
            # (но лучше бы сделать бэкап битого файла, если это критично)
            self.create_new_note()

    def save_current_state(self, tasks):
        """Единая точка сохранения состояния задачи (вызывается из TreeLogic)"""
        if not self.current_note_id:
            return

        self.all_notes[self.current_note_id]["tasks"] = tasks

        # --- ЛОГИКА ВРЕМЕНИ (FIX/UPDATE) ---
        if tasks and not self.start_time:
            self.start_time = QDateTime.currentDateTime()

        if self.start_time:
            self.all_notes[self.current_note_id]["start_time_str"] = self.start_time.toString(
                "dd.MM.yyyy HH:mm:ss"
            )
        else:
            self.all_notes[self.current_note_id]["start_time_str"] = None

        if self.finish_time:
            self.all_notes[self.current_note_id]["finish_time_str"] = self.finish_time.toString(
                "dd.MM.yyyy HH:mm:ss"
            )
        else:
            self.all_notes[self.current_note_id]["finish_time_str"] = None

        # Делегируем обновление заголовка
        self.parser.update_smart_title()

        self.save_to_disk()

        # Делегируем запись в историю
        self.history.add_to_history(tasks)

    def save_to_disk(self, skip_history=False):
        """
        АТОМАРНАЯ ЗАПИСЬ НА ДИСК.
        Защищает от потери данных при отключении электричества.
        """
        data = {
            "language": Loc.lang,
            "notes": self.all_notes,
            "current_note_id": self.current_note_id,
        }
        
        # Временное имя файла
        temp_file = f"{self.filename}.tmp"
        
        try:
            # 1. Пишем во временный файл
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
                # 2. Принудительно сбрасываем буферы на физический диск
                f.flush()
                os.fsync(f.fileno())
            
            # 3. Атомарно подменяем старый файл новым
            # На Windows начиная с Python 3.3 os.replace() атомарен
            os.replace(temp_file, self.filename)
            
        except Exception as e:
            print(f"CRITICAL ERROR SAVING: {e}")
            # Если что-то пошло не так, удаляем временный файл, чтобы не мусорить
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    # --- УПРАВЛЕНИЕ ЗАМЕТКАМИ ---

    def create_new_note(self):
        new_id = str(uuid.uuid4())
        self.current_note_id = new_id

        self.start_time = QDateTime.currentDateTime()
        self.finish_time = None

        self.all_notes[new_id] = {
            "title": Loc.t("title_default"),
            "tasks": [],
            "start_time_str": self.start_time.toString("dd.MM.yyyy HH:mm:ss"),
            "finish_time_str": None,
        }

        self.parser.update_smart_title()
        self.save_to_disk()

    def switch_note(self, note_id):
        if note_id in self.all_notes:
            self.current_note_id = note_id
            self.parser.load_timings()
            self.history.history = []
            self.history.history_index = -1
            return True
        return False

    def rename_current(self, new_title):
        if self.current_note_id:
            self.all_notes[self.current_note_id]["title"] = new_title
            self.save_to_disk()

    def undo(self):
        if self.history.undo():
            self.parser.load_timings()
            return True
        return False

    def redo(self):
        if self.history.redo():
            self.parser.load_timings()
            return True
        return False

    def delete_note(self, note_id):
        """Удаляет заметку по ID"""
        if note_id in self.all_notes:
            del self.all_notes[note_id]
            
            # Если удалили текущую
            if note_id == self.current_note_id:
                if self.all_notes:
                    # Переключаемся на первую попавшуюся
                    new_id = list(self.all_notes.keys())[0]
                    self.switch_note(new_id)
                else:
                    # Если ничего не осталось - создаем новую
                    self.create_new_note()
            
            self.save_to_disk()

    def update_smart_title(self):
        self.parser.update_smart_title()