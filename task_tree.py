# task_tree.py

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QTreeWidget, QTreeWidgetItem


class DraggableTreeWidget(QTreeWidget):
    def __init__(self, on_change_callback):
        super().__init__()
        self.on_change_callback = on_change_callback

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setUniformRowHeights(True)

    def dropEvent(self, event):
        super().dropEvent(event)
        if self.on_change_callback:
            self.on_change_callback()


class TodoItem(QTreeWidgetItem):
    def __init__(self, parent, text, done_date=None, cancelled=False):
        super().__init__(parent)
        self.setText(0, text)
        self.setFlags(
            Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsDragEnabled
            | Qt.ItemFlag.ItemIsDropEnabled
        )
        self.setCheckState(0, Qt.CheckState.Unchecked)
        self.setExpanded(True)
        self.cancelled = cancelled

        if done_date:
            self.setData(0, Qt.ItemDataRole.UserRole, done_date)
