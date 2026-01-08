# tree_io.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor

from task_tree import TodoItem


class TreeIO:
    def __init__(self, tree_widget):
        self.tree = tree_widget

    def collect_data(self):
        """Собирает всё дерево в список словарей"""
        return self._collect_recursive(self.tree.invisibleRootItem())

    def _collect_recursive(self, parent_item):
        tasks = []
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            tasks.append(
                {
                    "text": item.text(0),
                    "checked": item.checkState(0) == Qt.CheckState.Checked,
                    "done_date": item.data(0, Qt.ItemDataRole.UserRole),
                    "cancelled": getattr(item, "cancelled", False),
                    "children": self._collect_recursive(item),
                }
            )
        return tasks

    def load_data(self, tasks_data):
        """Очищает дерево и строит его заново из данных"""
        self.tree.blockSignals(True)
        self.tree.clear()
        for task_data in tasks_data:
            self._build_item_recursive(task_data, self.tree)
        self.tree.blockSignals(False)

    def _build_item_recursive(self, data, parent):
        item = TodoItem(parent, data["text"], data.get("done_date"), data.get("cancelled", False))

        state = Qt.CheckState.Checked if data["checked"] else Qt.CheckState.Unchecked
        item.setCheckState(0, state)

        # Красим сразу при загрузке
        if data.get("cancelled", False):
            item.setForeground(0, QBrush(QColor("#606060")))
        elif state == Qt.CheckState.Checked:
            item.setForeground(0, QBrush(QColor("#606060")))
        else:
            item.setForeground(0, QBrush(QColor("#e0e0e0")))

        for child in data.get("children", []):
            self._build_item_recursive(child, item)
