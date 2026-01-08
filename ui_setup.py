# ui_setup.py
from PyQt6.QtCore import Qt
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

# Импортируем TitleLabel (убедись, что он есть в widgets.py)
from widgets import CyberGrip, FloatingUnlockBtn, TitleLabel


class UISetup:
    @staticmethod
    def setup_ui(window):
        """Создает и размещает все элементы интерфейса на главном окне"""

        # --- Настройки окна ---
        window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        window.setMinimumSize(200, 150)

        # --- Центральный виджет ---
        window.central_widget = QWidget()
        window.central_widget.setObjectName("MainFrame")
        window.setCentralWidget(window.central_widget)

        # --- Основной лейаут ---
        window.layout = QVBoxLayout(window.central_widget)

        # 1. ОТСТУПЫ ОКНА (Левый/Правый = 8px для максимальной ширины контента)
        # Нижний = 20px для треугольника изменения размера
        window.layout.setContentsMargins(8, 12, 8, 20)
        window.layout.setSpacing(10)

        # ---  2. Шапка (Header) ---
        header = QHBoxLayout()
        header.setSpacing(5)

        # 2.1 СОЗДАЕМ ПОЛИТИКУ "СОХРАНЯТЬ МЕСТО"
        retain_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        retain_policy.setRetainSizeWhenHidden(True)

        window.menu_btn = QPushButton("☰")
        window.menu_btn.setFixedSize(24, 24)
        window.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        window.menu_btn.setStyleSheet(Styles.BTN_MENU)
        # Применяем политику
        window.menu_btn.setSizePolicy(retain_policy)
        header.addWidget(window.menu_btn)

        # --- ИЗМЕНЕНИЕ ЗДЕСЬ: Используем TitleLabel вместо ElidedLabel ---
        window.title = TitleLabel("TO-DO")
        window.title.setStyleSheet(
            "font-weight: 700; font-size: 12px; letter-spacing: 1px; color: #9e9e9e; margin-left: 5px;"
        )
        header.addWidget(window.title, 1)

        window.lock_btn = QPushButton("⚿")
        window.lock_btn.setFixedSize(24, 24)
        window.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        window.lock_btn.setToolTip("Заблокировать")
        window.lock_btn.setStyleSheet(Styles.BTN_LOCK)
        # Применяем политику
        window.lock_btn.setSizePolicy(retain_policy)
        header.addWidget(window.lock_btn)

        window.close_btn = QPushButton("✕")
        window.close_btn.setFixedSize(24, 24)
        window.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        window.close_btn.setToolTip("Закрыть приложение")
        window.close_btn.setStyleSheet(Styles.BTN_CLOSE)
        # Применяем политику
        window.close_btn.setSizePolicy(retain_policy)
        header.addWidget(window.close_btn)

        window.layout.addLayout(header)
        # --- 3. Прогрессбар ---
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(2)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        window.progress = QProgressBar()
        window.progress.setFixedHeight(6)
        window.progress.setTextVisible(False)
        window.progress.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # stretch=1 -> бар занимает всё место
        progress_layout.addWidget(window.progress, 1)

        window.lbl_percent = QLabel("0%")
        window.lbl_percent.setFixedWidth(37)
        window.lbl_percent.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        progress_layout.addWidget(window.lbl_percent)

        window.layout.addLayout(progress_layout)

        # --- 4. Дерево задач (С ПРАВИЛЬНЫМ ОТСТУПОМ СКРОЛЛБАРА) ---
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
                /* Небольшой отступ справа для текста, чтобы не прилипал к скроллу */
                padding-right: 5px; 
            }
            
            /* Настройка вертикального скроллбара */
            QScrollBar:vertical {
                background: transparent;
                /* ХИТРОСТЬ: Делаем общую ширину больше (18px) */
                width: 18px; 
                /* И задаем отступ справа 10px. В итоге ползунок будет 8px и сдвинут влево. */
                margin: 0px 10px 0px 0px;
            }

            /* Сам ползунок */
            QScrollBar::handle:vertical {
                background: #424242;      
                min-height: 20px;
                border-radius: 4px;       
            }
            QScrollBar::handle:vertical:hover {
                background: #606060;      
            }

            /* Скрываем кнопки вверх/вниз и фон */
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

        # --- 5. Поле ввода ---
        window.inp = QLineEdit()
        window.inp.setPlaceholderText("+ Новая задача")
        window.layout.addWidget(window.inp)

        # --- 6. Grip (CyberGrip - ручная рисовка) ---
        window.grip_indicator = CyberGrip(window)
        window.grip_indicator.setFixedSize(24, 24)
        window.grip_indicator.raise_()

        # --- 7. Трей ---
        window.tray = QSystemTrayIcon(window)
        window.tray.setIcon(window.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))

        # --- 8. Оверлей ---
        window.unlock_overlay = FloatingUnlockBtn(callback=None)
