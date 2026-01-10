# ui_setup.py
import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from delegates import DateDelegate
from styles import Styles
from task_tree import DraggableTreeWidget

# Импортируем кастомные виджеты
from widgets import CyberGrip, FloatingUnlockBtn, TitleLabel


class UISetup:
    @staticmethod
    def setup_ui(window):
        """Создает и размещает все элементы интерфейса на главном окне"""

        # --- 1. НАСТРОЙКИ ОКНА ---
        # Убрали Qt.WindowType.Tool, чтобы окно появилось в панели задач.
        # Оставили Frameless (без рамок) и StaysOnTop (поверх всех).
        window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        
        window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        window.setMinimumSize(200, 150)

        # --- 2. УСТАНОВКА ИКОНКИ ---
        # Чтобы в панели задач было красиво
        if os.path.exists("icon.ico"):
            window.setWindowIcon(QIcon("icon.ico"))
        else:
            # Фолбек: если иконки нет, берем стандартную системную
            window.setWindowIcon(window.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))

        # --- 3. Центральный виджет ---
        window.central_widget = QWidget()
        window.central_widget.setObjectName("MainFrame")
        window.setCentralWidget(window.central_widget)

        # --- 4. Основной лейаут ---
        window.layout = QVBoxLayout(window.central_widget)

        # Отступы: Слева/Справа = 8px, Снизу = 20px (для треугольника изменения размера)
        window.layout.setContentsMargins(8, 12, 8, 20)
        window.layout.setSpacing(10)

        # --- 5. Шапка (Header) ---
        header = QHBoxLayout()
        header.setSpacing(5)

        # Политика для кнопок, чтобы они не исчезали при скрытии, а просто прятались
        retain_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        retain_policy.setRetainSizeWhenHidden(True)

        # Кнопка Меню
        window.menu_btn = QPushButton("☰")
        window.menu_btn.setFixedSize(24, 24)
        window.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        window.menu_btn.setStyleSheet(Styles.BTN_MENU)
        window.menu_btn.setSizePolicy(retain_policy)
        header.addWidget(window.menu_btn)

        # Заголовок (TitleLabel)
        window.title = TitleLabel("TO-DO")
        window.title.setStyleSheet(
            "font-weight: 700; font-size: 12px; letter-spacing: 1px; color: #9e9e9e; margin-left: 5px;"
        )
        header.addWidget(window.title, 1)

        # Кнопка Блокировки
        window.lock_btn = QPushButton("⚿")
        window.lock_btn.setFixedSize(24, 24)
        window.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        window.lock_btn.setToolTip("Заблокировать")
        window.lock_btn.setStyleSheet(Styles.BTN_LOCK)
        window.lock_btn.setSizePolicy(retain_policy)
        header.addWidget(window.lock_btn)

        # Кнопка Закрытия
        window.close_btn = QPushButton("✕")
        window.close_btn.setFixedSize(24, 24)
        window.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        window.close_btn.setToolTip("Закрыть приложение")
        window.close_btn.setStyleSheet(Styles.BTN_CLOSE)
        window.close_btn.setSizePolicy(retain_policy)
        header.addWidget(window.close_btn)

        window.layout.addLayout(header)

        # --- 6. Прогрессбар ---
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(2)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        window.progress = QProgressBar()
        window.progress.setFixedHeight(6)
        window.progress.setTextVisible(False)
        window.progress.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        progress_layout.addWidget(window.progress, 1)

        window.lbl_percent = QLabel("0%")
        window.lbl_percent.setFixedWidth(37)
        window.lbl_percent.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        progress_layout.addWidget(window.lbl_percent)

        window.layout.addLayout(progress_layout)

        # --- 7. Дерево задач ---
        window.tree = DraggableTreeWidget(on_change_callback=None)
        window.tree.setHeaderHidden(True)
        window.tree.setIndentation(20)
        window.tree.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        window.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        window.tree.setStyleSheet("""
            QTreeWidget { 
                background-color: #1e1e1e; 
                border: none;
                padding-right: 5px; 
            }
            
            /* Кастомный скроллбар */
            QScrollBar:vertical {
                background: transparent;
                width: 18px; 
                margin: 0px 10px 0px 0px;
            }

            QScrollBar::handle:vertical {
                background: #424242;      
                min-height: 20px;
                border-radius: 4px;       
            }
            QScrollBar::handle:vertical:hover {
                background: #606060;      
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { 
                height: 0px; 
                background: none; 
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { 
                background: none; 
            }
        """)

        window.date_delegate = DateDelegate(window.tree)
        window.tree.setItemDelegate(window.date_delegate)

        window.layout.addWidget(window.tree)

        # --- 8. Поле ввода ---
        window.inp = QLineEdit()
        window.inp.setPlaceholderText("+ Новая задача")
        window.layout.addWidget(window.inp)

        # --- 9. Grip (Треугольник ресайза) ---
        window.grip_indicator = CyberGrip(window)
        window.grip_indicator.setFixedSize(24, 24)
        window.grip_indicator.raise_()

        # --- 10. Трей ---
        window.tray = QSystemTrayIcon(window)
        # Используем ту же логику для иконки трея
        if os.path.exists("icon.ico"):
            window.tray.setIcon(QIcon("icon.ico"))
        else:
            window.tray.setIcon(window.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))

        # --- 11. Оверлей (Кнопка разблокировки) ---
        window.unlock_overlay = FloatingUnlockBtn(callback=None)