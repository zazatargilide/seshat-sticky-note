import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTextEdit, 
                             QPushButton, QLabel, QMessageBox, QHBoxLayout, 
                             QComboBox, QFrame, QSplitter)
from PyQt6.QtCore import Qt

class DatabaseInjector(QWidget):
    def __init__(self):
        super().__init__()
        self.db_filename = "seshat_db.json"
        self.init_ui()
        self.refresh_notes_list() # Сразу загружаем список заметок

    def init_ui(self):
        self.setWindowTitle("Seshat DB Injector v2.0 💉")
        self.resize(900, 700)
        
        # --- СТИЛИ (Dark Theme) ---
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #e0e0e0; font-family: Consolas, 'Segoe UI', monospace; font-size: 14px; }
            QTextEdit { background-color: #252526; border: 1px solid #3e3e42; color: #dcdcdc; border-radius: 5px; padding: 8px; }
            QPushButton { background-color: #3a3a3a; color: white; border: 1px solid #555; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #4a4a4a; border-color: #777; }
            QPushButton:pressed { background-color: #2a2a2a; }
            
            /* Кнопка слияния (Синяя) */
            QPushButton#btn_merge { background-color: #0e639c; border: none; font-weight: bold; }
            QPushButton#btn_merge:hover { background-color: #1177bb; }
            
            /* Кнопка добавления (Зеленая) */
            QPushButton#btn_append { background-color: #2da042; border: none; font-weight: bold; }
            QPushButton#btn_append:hover { background-color: #3fb950; }

            QComboBox { background-color: #252526; border: 1px solid #3e3e42; padding: 5px; border-radius: 4px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #252526; selection-background-color: #094770; }
            
            QLabel { color: #aaaaaa; font-weight: bold; margin-top: 10px; }
            QFrame#Line { background-color: #3e3e42; border: none; max-height: 1px; }
        """)

        layout = QVBoxLayout()

        # --- БЛОК 1: ВВОД КОДА ---
        layout.addWidget(QLabel("1. Вставьте JSON код (новые заметки ИЛИ список задач):"))
        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText('Например:\n[\n  { "text": "Новая задача", "checked": false, "children": [] }\n]')
        layout.addWidget(self.text_area)

        # Кнопка очистки
        btn_clear = QPushButton("Очистить поле")
        btn_clear.clicked.connect(self.text_area.clear)
        layout.addWidget(btn_clear)

        # Разделитель
        line = QFrame()
        line.setObjectName("Line")
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        # --- БЛОК 2: УПРАВЛЕНИЕ ---
        
        # Секция А: Добавление новой заметки целиком
        layout.addWidget(QLabel("ВАРИАНТ А: Создать новые заметки (Merge)"))
        self.btn_merge = QPushButton("СОЗДАТЬ НОВЫЕ ЗАМЕТКИ ИЗ КОДА")
        self.btn_merge.setObjectName("btn_merge")
        self.btn_merge.clicked.connect(self.merge_new_notes)
        layout.addWidget(self.btn_merge)

        # Разделитель
        layout.addSpacing(10)
        line2 = QFrame()
        line2.setObjectName("Line")
        line2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line2)

        # Секция Б: Добавление задач в существующую
        layout.addWidget(QLabel("ВАРИАНТ Б: Добавить задачи в существующую заметку"))
        
        hbox_append = QHBoxLayout()
        self.combo_notes = QComboBox()
        self.combo_notes.setPlaceholderText("Выберите заметку...")
        
        btn_refresh = QPushButton("🔄")
        btn_refresh.setToolTip("Обновить список заметок")
        btn_refresh.setFixedWidth(40)
        btn_refresh.clicked.connect(self.refresh_notes_list)

        hbox_append.addWidget(self.combo_notes, 1)
        hbox_append.addWidget(btn_refresh)
        layout.addLayout(hbox_append)

        self.btn_append = QPushButton("ДОБАВИТЬ ЗАДАЧИ В ВЫБРАННУЮ ЗАМЕТКУ")
        self.btn_append.setObjectName("btn_append")
        self.btn_append.clicked.connect(self.append_tasks_to_existing)
        layout.addWidget(self.btn_append)

        self.setLayout(layout)

    # --- ЛОГИКА ---

    def load_db(self):
        if not os.path.exists(self.db_filename):
            return None
        try:
            with open(self.db_filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось прочитать файл:\n{e}")
            return None

    def save_db(self, data):
        try:
            with open(self.db_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", f"Не удалось записать файл:\n{e}")
            return False

    def refresh_notes_list(self):
        """Загружает заголовки заметок в выпадающий список"""
        self.combo_notes.clear()
        data = self.load_db()
        if not data or "notes" not in data:
            return

        for note_id, note_data in data["notes"].items():
            title = note_data.get("title", "Без названия")
            # Добавляем ID в скрытые данные элемента (UserRole)
            self.combo_notes.addItem(f"{title} ({note_id})", note_id)

    def get_json_input(self):
        raw = self.text_area.toPlainText()
        if not raw.strip():
            QMessageBox.warning(self, "Пусто", "Поле ввода пустое!")
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Ошибка JSON", f"Некорректный код:\n{e}")
            return None

    # --- ВАРИАНТ А: СЛИЯНИЕ (СТАРЫЙ МЕТОД) ---
    def merge_new_notes(self):
        new_data = self.get_json_input()
        if not new_data: return

        if "notes" not in new_data:
            QMessageBox.warning(self, "Ошибка структуры", "Для создания заметок нужен JSON с ключом 'notes'.")
            return

        current_db = self.load_db()
        if not current_db:
            current_db = {"language": "ru", "notes": {}}

        if "notes" not in current_db: current_db["notes"] = {}

        added = 0
        overwritten = 0
        for nid, ncontent in new_data["notes"].items():
            if nid in current_db["notes"]: overwritten += 1
            else: added += 1
            current_db["notes"][nid] = ncontent

        if "current_note_id" in new_data:
            current_db["current_note_id"] = new_data["current_note_id"]

        if self.save_db(current_db):
            QMessageBox.information(self, "Успех", f"Создано: {added}, Обновлено: {overwritten}")
            self.refresh_notes_list()

    # --- ВАРИАНТ Б: ДОБАВЛЕНИЕ ЗАДАЧ (НОВЫЙ МЕТОД) ---
    def append_tasks_to_existing(self):
        # 1. Получаем ID выбранной заметки
        index = self.combo_notes.currentIndex()
        if index == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите заметку из списка!")
            return
        target_id = self.combo_notes.itemData(index)

        # 2. Получаем задачи из текста
        input_data = self.get_json_input()
        if not input_data: return

        tasks_to_append = []

        # Умный парсинг: понимаем и список, и объект заметки
        if isinstance(input_data, list):
            # Если вставили просто список задач [ {...}, {...} ]
            tasks_to_append = input_data
        elif isinstance(input_data, dict):
            # Если вставили объект заметки { "text": "...", "children": [...] }
            if "text" in input_data: # Это одна задача
                tasks_to_append = [input_data]
            elif "tasks" in input_data: # Это структура заметки { "title":..., "tasks": [...] }
                tasks_to_append = input_data["tasks"]
            elif "notes" in input_data: # Вставили целый дамп БД?
                QMessageBox.warning(self, "Ошибка", "Вы вставили полный дамп базы. Для добавления задач нужен список или объект одной задачи.")
                return
            else:
                # Пробуем предположить, что это задача без некоторых полей, или список в словаре
                QMessageBox.warning(self, "Ошибка", "Непонятная структура. Нужен список задач или объект задачи.")
                return

        if not tasks_to_append:
            QMessageBox.warning(self, "Пусто", "Не найдено задач для добавления.")
            return

        # 3. Обновляем базу
        current_db = self.load_db()
        if not current_db or target_id not in current_db["notes"]:
            QMessageBox.critical(self, "Ошибка", "Целевая заметка не найдена в базе (возможно, файл был изменен извне).")
            return

        # Добавляем
        current_tasks = current_db["notes"][target_id].get("tasks", [])
        current_tasks.extend(tasks_to_append)
        current_db["notes"][target_id]["tasks"] = current_tasks

        if self.save_db(current_db):
            note_title = current_db["notes"][target_id].get("title", "???")
            QMessageBox.information(self, "Успех", f"Добавлено {len(tasks_to_append)} задач(и) в заметку:\n'{note_title}'")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseInjector()
    window.show()
    sys.exit(app.exec())