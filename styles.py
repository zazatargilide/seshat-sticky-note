# styles.py

try:
    import ctypes

    user32 = ctypes.windll.user32
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020
except Exception:
    pass

import sys


class WinUtils:
    @staticmethod
    def set_click_through(hwnd, enable: bool):
        """Включает или выключает пропуск кликов сквозь окно (только Windows)"""
        if sys.platform != "win32":
            return

        try:
            hwnd = int(hwnd)
            styles = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

            if enable:
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, styles | WS_EX_TRANSPARENT)
            else:
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, styles & ~WS_EX_TRANSPARENT)
        except Exception as e:
            print(f"WinAPI Error: {e}")


class Styles:
    # Базовые стили кнопок
    BTN_MENU = "QPushButton { background: transparent; border: none; color: #757575; font-size: 16px; font-weight: bold; } QPushButton:hover { color: #7c4dff; }"
    BTN_LOCK = "QPushButton { background: transparent; border: none; color: #757575; font-size: 18px; } QPushButton:hover { color: #e0e0e0; }"
    BTN_CLOSE = "QPushButton { background: transparent; border: none; color: #757575; font-size: 16px; } QPushButton:hover { color: #ef5350; }"

    @staticmethod
    def get_main_frame(accent):
        return f"#MainFrame {{ background-color: #1e1e1e; border: 1px solid {accent}; border-radius: 12px; }}"

    @staticmethod
    def get_progress_bar(accent):
        return f"""
            QProgressBar {{ background: #2d2d2d; border: none; border-radius: 3px; }} 
            QProgressBar::chunk {{ background-color: {accent}; border-radius: 3px; }}
        """

    @staticmethod
    def get_tree_widget(accent):
        return f"""
            QTreeWidget {{ background: transparent; border: none; font-size: 14px; outline: none; }}
            QTreeWidget::item {{ padding: 4px; min-height: 24px; border-radius: 6px; }}
            
            QTreeWidget QLineEdit {{ 
                color: #e0e0e0; background-color: #2d2d2d; 
                border: 1px solid {accent}; border-radius: 4px; padding: 0px 4px; margin: 0px; 
            }}
            
            QTreeWidget::indicator {{ width: 16px; height: 16px; border: 2px solid #555555; border-radius: 5px; background-color: #2d2d2d; }}
            QTreeWidget::indicator:checked {{ background-color: {accent}; border: 2px solid {accent}; }}
            QTreeWidget::indicator:hover {{ border-color: #9e9e9e; }}
        """

    @staticmethod
    def get_input_field(accent):
        return f"""
            QLineEdit {{ background: #252525; border: 1px solid transparent; border-radius: 8px; padding: 8px 10px; color: #e0e0e0; font-size: 13px; }}
            QLineEdit:focus {{ background: #2d2d2d; border: 1px solid {accent}; }}
        """

    @staticmethod
    def get_menu(accent):
        return f"""
            QMenu {{ background-color: #2d2d2d; border: 1px solid #444; padding: 5px; }}
            QMenu::item {{ padding: 5px 20px; color: #e0e0e0; }}
            QMenu::item:selected {{ background-color: {accent}; color: white; }}
        """
