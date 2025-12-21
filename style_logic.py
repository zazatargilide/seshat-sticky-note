#style_logic.py

from styles import Styles
from widgets import CyberGrip, ElidedLabel, FloatingUnlockBtn
from task_tree import DraggableTreeWidget, TodoItem
from delegates import DateDelegate

class StyleLogic:
    def __init__(self, main_window):
        self.mw = main_window

    def apply_dynamic_styles(self, accent):
        # Основной фрейм
        self.mw.central_widget.setStyleSheet(Styles.get_main_frame(accent))
        
        # Прогрессбар
        self.mw.progress.setStyleSheet(Styles.get_progress_bar(accent))
        
        # Дерево (включая фон для фикса отрисовки текста)
        self.mw.tree.setStyleSheet(Styles.get_tree_widget(accent))
        
        # Поле ввода
        self.mw.inp.setStyleSheet(Styles.get_input_field(accent))
        
        # Проценты
        self.mw.lbl_percent.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {accent};")
        
        # Делегат (даты)
        if hasattr(self.mw.date_delegate, 'set_accent_color'):
             self.mw.date_delegate.set_accent_color(accent)
        
        # Кнопка разблокировки
        if self.mw.rainbow.timer.isActive():
             self.mw.unlock_overlay.set_color(accent)
        else:
             self.mw.unlock_overlay.set_color("#757575")