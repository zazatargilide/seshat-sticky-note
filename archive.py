#archive.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QPushButton, 
                             QHBoxLayout, QMessageBox, QListWidgetItem)
from PyQt6.QtCore import Qt

# --- ВОТ ЭТОГО ИМПОРТА НЕ ХВАТАЛО ---
from localization import Loc 

class ArchiveDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mw = parent # Ссылка на главное окно (StickyNote)
        
        self.setWindowTitle(Loc.t("archive_title"))
        self.setMinimumSize(300, 400)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: #e0e0e0; }
            QListWidget { background-color: #252525; border: 1px solid #333; color: #e0e0e0; font-size: 14px; }
            QListWidget::item { padding: 5px; }
            QListWidget::item:selected { background-color: #7c4dff; color: white; }
            QPushButton { background-color: #333; color: #e0e0e0; border: none; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #444; }
            QPushButton:pressed { background-color: #7c4dff; color: white; }
        """)

        layout = QVBoxLayout(self)

        # Список заметок
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.btn_open = QPushButton(Loc.t("btn_open"))
        self.btn_open.clicked.connect(self.open_note)
        btn_layout.addWidget(self.btn_open)

        self.btn_delete = QPushButton(Loc.t("btn_delete"))
        self.btn_delete.clicked.connect(self.delete_note)
        self.btn_delete.setStyleSheet("QPushButton:hover { background-color: #c62828; }")
        btn_layout.addWidget(self.btn_delete)

        self.btn_close = QPushButton(Loc.t("btn_close"))
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)
        
        # Двойной клик для открытия
        self.list_widget.itemDoubleClicked.connect(self.open_note)

        self.populate_list()

    def populate_list(self):
        self.list_widget.clear()
        current_id = self.mw.data.current_note_id
        
        # Перебираем все заметки
        for note_id, note_data in self.mw.data.all_notes.items():
            # Не показываем текущую открытую заметку в архиве (опционально)
            # if note_id == current_id: continue
            
            title = note_data.get("title", "Untitled")
            
            # Маркируем текущую
            display_text = title
            if note_id == current_id:
                display_text = f"➤ {title}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, note_id)
            self.list_widget.addItem(item)

    def open_note(self):
        items = self.list_widget.selectedItems()
        if not items: return
        
        note_id = items[0].data(Qt.ItemDataRole.UserRole)
        
        # Переключаемся
        if self.mw.data.switch_note(note_id):
            self.mw.refresh_ui()
            self.close()

    def delete_note(self):
        items = self.list_widget.selectedItems()
        if not items: return
        
        note_id = items[0].data(Qt.ItemDataRole.UserRole)
        
        # Спрашиваем подтверждение
        reply = QMessageBox.question(
            self, 
            Loc.t("msg_del_title"), 
            Loc.t("msg_del_text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Удаляем в менеджере данных
            # (Функция delete_note должна быть в DataManager, если её нет - добавим ниже)
            if hasattr(self.mw.data, 'delete_note'):
                self.mw.data.delete_note(note_id)
                self.mw.refresh_ui()
                self.populate_list()
            else:
                # Фолбек на случай, если метода нет (ручное удаление)
                if note_id in self.mw.data.all_notes:
                    del self.mw.data.all_notes[note_id]
                    # Если удалили текущую - переключаемся на другую
                    if note_id == self.mw.data.current_note_id:
                        if self.mw.data.all_notes:
                            new_id = list(self.mw.data.all_notes.keys())[0]
                            self.mw.data.switch_note(new_id)
                        else:
                            self.mw.data.create_new_note()
                    
                    self.mw.data.save_to_disk()
                    self.mw.refresh_ui()
                    self.populate_list()