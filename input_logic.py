#input_logic.py
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt

class InputLogic:
    def __init__(self, main_window):
        self.mw = main_window

    def setup(self):
        self.connect_signals()
        self.setup_shortcuts()

    def connect_signals(self):
        # Кнопки
        self.mw.menu_btn.clicked.connect(self.mw.menu_logic.show_main_menu)
        self.mw.lock_btn.clicked.connect(self.mw.toggle_lock_mode)
        self.mw.close_btn.clicked.connect(self.mw.close)
        self.mw.unlock_overlay.btn.clicked.connect(self.mw.toggle_lock_mode)
        
        # Ввод
        self.mw.inp.returnPressed.connect(self.mw.tree_logic.add_task)
        
        # Дерево
        self.mw.tree.itemChanged.connect(self.mw.tree_logic.on_item_changed)
        self.mw.tree.customContextMenuRequested.connect(self.mw.tree_logic.show_context_menu)
        self.mw.tree.on_change_callback = self.mw.save_and_update
        
        # Трей
        self.mw.tray.activated.connect(self.mw.menu_logic.on_tray_click)

    def setup_shortcuts(self):
        # Undo / Redo
        QShortcut(QKeySequence("Ctrl+Z"), self.mw).activated.connect(self.perform_undo)
        QShortcut(QKeySequence("Ctrl+Y"), self.mw).activated.connect(self.perform_redo)
        
        # Создание
        QShortcut(QKeySequence("Ctrl+N"), self.mw).activated.connect(self.focus_input)
        QShortcut(QKeySequence("Ctrl+Alt+N"), self.mw).activated.connect(self.mw.menu_logic.create_new_note)
        
        # Навигация (делегируем в TreeLogic)
        tl = self.mw.tree_logic
        QShortcut(QKeySequence("Ctrl+Up"), self.mw).activated.connect(lambda: tl.move_item_vertical(-1))
        QShortcut(QKeySequence("Ctrl+Down"), self.mw).activated.connect(lambda: tl.move_item_vertical(1))
        QShortcut(QKeySequence("Ctrl+Right"), self.mw).activated.connect(tl.indent_item)
        QShortcut(QKeySequence("Ctrl+Left"), self.mw).activated.connect(tl.unindent_item)

    def perform_undo(self):
        if self.mw.data.undo(): self.mw.refresh_ui()

    def perform_redo(self):
        if self.mw.data.redo(): self.mw.refresh_ui()

    def focus_input(self):
        if not self.mw.locked:
            self.mw.inp.setFocus()
            self.mw.inp.selectAll()