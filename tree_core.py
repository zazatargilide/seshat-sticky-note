# tree_core.py
from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtGui import QBrush, QColor

from localization import Loc
from task_tree import TodoItem


class TreeCore:
    def __init__(self, main_window, callback_save):
        self.mw = main_window
        self.tree = main_window.tree
        self.callback_save = callback_save  # Функция сохранения

    def add_task(self, text):
        if not text:
            return
        if self.tree.topLevelItemCount() == 0 and not self.mw.data.start_time:
            self.mw.data.start_time = QDateTime.currentDateTime()

        item = TodoItem(self.tree, text)
        self.mw.inp.clear()
        item.setForeground(0, QBrush(QColor("#e0e0e0")))
        self.callback_save()

    def delete_item(self, item):
        parent = item.parent()
        if parent:
            parent.removeChild(item)
            self.check_parent_state(parent)
        else:
            self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))

        if self.tree.topLevelItemCount() == 0:
            self.mw.data.start_time = None
            self.mw.data.finish_time = None
            self.mw.title.setText(Loc.t("title_default"))

        self.callback_save()

    def on_item_changed(self, item):
        self.tree.blockSignals(True)
        state = item.checkState(0)
        is_cancelled = getattr(item, "cancelled", False)

        # 1. Красим сам элемент
        self._colorize_item(item, state, is_cancelled)

        # 2. Красим детей
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            c_canc = getattr(child, "cancelled", False)
            self._colorize_item(child, state, c_canc)

        # 3. Проверяем родителя
        parent = item.parent()
        if parent:
            self.check_parent_state(parent)

        self.tree.blockSignals(False)
        self.callback_save()

    def _colorize_item(self, item, state, is_cancelled):
        if is_cancelled:
            item.setForeground(0, QBrush(QColor("#606060")))
        elif state == Qt.CheckState.Checked:
            item.setForeground(0, QBrush(QColor("#606060")))
            if not item.data(0, Qt.ItemDataRole.UserRole):
                item.setData(
                    0,
                    Qt.ItemDataRole.UserRole,
                    QDateTime.currentDateTime().toString("dd.MM.yyyy, HH:mm"),
                )
        else:
            item.setForeground(0, QBrush(QColor("#e0e0e0")))
            item.setData(0, Qt.ItemDataRole.UserRole, None)

    def check_parent_state(self, parent):
        if parent.childCount() == 0:
            parent.setCheckState(0, Qt.CheckState.Unchecked)
            return

        all_checked = True
        for i in range(parent.childCount()):
            if parent.child(i).checkState(0) != Qt.CheckState.Checked:
                all_checked = False
                break

        new_state = Qt.CheckState.Checked if all_checked else Qt.CheckState.Unchecked
        parent.setCheckState(0, new_state)
        # Красим родителя после смены статуса
        p_canc = getattr(parent, "cancelled", False)
        self._colorize_item(parent, new_state, p_canc)

    # --- Навигация ---
    def move_vertical(self, direction):
        item = self.tree.currentItem()
        if not item:
            return
        parent = item.parent()
        target = parent if parent else self.tree.invisibleRootItem()
        idx = target.indexOfChild(item)
        new_idx = idx + direction
        if 0 <= new_idx < target.childCount():
            taken = target.takeChild(idx)
            target.insertChild(new_idx, taken)
            self.tree.setCurrentItem(taken)
            self.callback_save()

    def indent(self):
        item = self.tree.currentItem()
        if not item:
            return
        parent = item.parent()
        target = parent if parent else self.tree.invisibleRootItem()
        idx = target.indexOfChild(item)
        if idx == 0:
            return
        new_parent = target.child(idx - 1)
        taken = target.takeChild(idx)
        new_parent.addChild(taken)
        new_parent.setExpanded(True)
        self.tree.setCurrentItem(taken)
        self.callback_save()

    def unindent(self):
        item = self.tree.currentItem()
        if not item or not item.parent():
            return
        parent = item.parent()
        grand = parent.parent()
        target = grand if grand else self.tree.invisibleRootItem()
        p_idx = target.indexOfChild(parent)
        taken = parent.takeChild(parent.indexOfChild(item))
        target.insertChild(p_idx + 1, taken)
        self.tree.setCurrentItem(taken)
        self.callback_save()
