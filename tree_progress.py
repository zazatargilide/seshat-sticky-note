# tree_progress.py
from PyQt6.QtCore import QDateTime, Qt


class TreeProgress:
    def __init__(self, main_window):
        self.mw = main_window
        self.tree = main_window.tree

    def calculate_and_update(self):
        root_count = self.tree.topLevelItemCount()
        if root_count == 0:
            self._reset()
            return

        total = 0.0
        completed = 0.0
        cancelled = 0.0

        for i in range(root_count):
            item = self.tree.topLevelItem(i)
            total += 1.0

            # Если родитель отменен, он считается "нейтрализованным"
            if getattr(item, "cancelled", False):
                cancelled += 1.0
                continue

            # Если есть дети
            if item.childCount() > 0:
                c_total = item.childCount()
                c_done = 0
                c_canc = 0
                for j in range(c_total):
                    child = item.child(j)
                    if getattr(child, "cancelled", False):
                        c_canc += 1
                    elif child.checkState(0) == Qt.CheckState.Checked:
                        c_done += 1

                completed += c_done / c_total
                cancelled += c_canc / c_total
            else:
                if item.checkState(0) == Qt.CheckState.Checked:
                    completed += 1.0

        # Считаем процент (отмененные в знаменателе, но не в числителе)
        if total == 0:
            val = 0
        else:
            val = int((completed / total) * 100)

        self.mw.progress.setValue(val)
        self.mw.lbl_percent.setText(f"{val}%")

        # Радуга: если (Сделано + Отменено) == Всего
        is_done = (completed + cancelled) >= (total - 0.001)

        if is_done and total > 0:
            if not self.mw.data.finish_time:
                self.mw.data.finish_time = QDateTime.currentDateTime()
            self.mw.rainbow.start()
        else:
            self.mw.data.finish_time = None
            self.mw.rainbow.stop()
            # Возврат обычного стиля
            if hasattr(self.mw, "style_logic"):
                self.mw.style_logic.apply_dynamic_styles(self.mw.default_accent)

        self.mw.data.update_smart_title()
        # Обновляем заголовок через контроллер (будет подключено позже)
        # self.mw.tree_controller.update_title_ui() -> вызовется в save_and_update

    def _reset(self):
        self.mw.progress.setValue(0)
        self.mw.lbl_percent.setText("0%")
        self.mw.rainbow.stop()
        if hasattr(self.mw, "style_logic"):
            self.mw.style_logic.apply_dynamic_styles(self.mw.default_accent)
