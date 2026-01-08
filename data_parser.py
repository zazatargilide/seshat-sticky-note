# data_parser.py
from PyQt6.QtCore import QDateTime

from localization import Loc


class DataParser:
    def __init__(self, data_manager):
        self.dm = data_manager

    def load_timings(self):
        """Парсит время из JSON (без изменений)"""
        if not self.dm.current_note_id:
            return
        note = self.dm.all_notes[self.dm.current_note_id]

        st_str = note.get("start_time_str")
        st_sec = note.get("start_time")
        if st_str:
            self.dm.start_time = QDateTime.fromString(st_str, "dd.MM.yyyy HH:mm:ss")
        elif isinstance(st_sec, (int, float)):
            self.dm.start_time = QDateTime.fromSecsSinceEpoch(int(st_sec))
        else:
            self.dm.start_time = None

        ft_str = note.get("finish_time_str")
        ft_sec = note.get("finish_time")
        if ft_str:
            self.dm.finish_time = QDateTime.fromString(ft_str, "dd.MM.yyyy HH:mm:ss")
        elif isinstance(ft_sec, (int, float)):
            self.dm.finish_time = QDateTime.fromSecsSinceEpoch(int(ft_sec))
        else:
            self.dm.finish_time = None

    def update_smart_title(self):
        """
        Генерирует умный заголовок.
        Теперь добавляет дату завершения ДАЖЕ к кастомным названиям.
        """
        if not self.dm.current_note_id:
            return

        note = self.dm.all_notes[self.dm.current_note_id]
        curr_title = note.get("title", "")

        # Разделитель, который мы используем для времени завершения (например " - Завершено: ")
        finish_separator = f" {Loc.t('note_to')} "

        # 1. ПЫТАЕМСЯ НАЙТИ "ЧИСТОЕ" НАЗВАНИЕ (без хвоста с датой завершения)
        # Если мы уже добавляли дату завершения раньше, её надо отрезать, чтобы не дублировать
        clean_title = curr_title.split(finish_separator)[0]

        # 2. ПРОВЕРЯЕМ: ЭТО АВТО-ЗАГОЛОВОК ИЛИ КАСТОМНЫЙ?
        is_auto = False
        if clean_title == "TO-DO" or clean_title == Loc.t("title_default"):
            is_auto = True
        else:
            for lang in Loc.data:
                prefix = Loc.data[lang]["note_prefix"]
                if clean_title.startswith(prefix):
                    is_auto = True
                    break

        # 3. ЕСЛИ НЕТ ДАТЫ НАЧАЛА (АВТО-ЛЕЧЕНИЕ)
        if not self.dm.start_time:
            tasks = note.get("tasks", [])
            if tasks:
                self.dm.start_time = QDateTime.currentDateTime()
            else:
                # Если задач нет и времени нет — просто дефолт
                note["title"] = Loc.t("title_default")
                return

        full_format = "dd.MM.yyyy HH:mm"

        # 4. ФОРМИРУЕМ НОВЫЙ ЗАГОЛОВОК
        new_title = ""

        if is_auto:
            # Если название было автоматическое — пересобираем с нуля
            base_date = self.dm.start_time.toString(full_format)
            new_title = f"{Loc.t('note_prefix')} {base_date}"
        else:
            # Если название кастомное (твое) — оставляем его как базу
            new_title = clean_title

        # 5. ДОБАВЛЯЕМ ВРЕМЯ ЗАВЕРШЕНИЯ (ЕСЛИ ЕСТЬ)
        if self.dm.finish_time:
            end_str = self.dm.finish_time.toString(full_format)
            new_title += f"{finish_separator}{end_str}"

        note["title"] = new_title
