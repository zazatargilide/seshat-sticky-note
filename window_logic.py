#window_logic.py
from PyQt6.QtCore import Qt, QPoint
from styles import WinUtils

class WindowLogic:
    def __init__(self, main_window):
        self.mw = main_window
        self.moving = False
        self.drag_start_position = None
        self.current_opacity = 0.3 

    def toggle_lock_mode(self):
        self.mw.locked = not self.mw.locked
        hwnd = self.mw.winId().__int__()
        WinUtils.set_click_through(hwnd, self.mw.locked)

        if self.mw.locked:
            # --- РЕЖИМ БЛОКИРОВКИ ---
            
            # 1. Вычисляем АБСОЛЮТНУЮ позицию кнопки блокировки на экране
            # mapToGlobal(QPoint(0,0)) дает координаты левого верхнего угла кнопки lock_btn
            target_pos = self.mw.lock_btn.mapToGlobal(QPoint(0, 0))
            
            # 2. Перемещаем оверлей ровно в эту точку
            self.mw.unlock_overlay.move(target_pos)
            self.mw.unlock_overlay.show()
            
            # 3. Скрываем элементы (благодаря RetainSize текст не сдвинется)
            self.mw.inp.hide(); self.mw.lock_btn.hide()
            self.mw.grip_indicator.hide(); self.mw.menu_btn.hide(); self.mw.close_btn.hide()
            
            self.mw.tree.setDragEnabled(False)
            self.mw.setWindowOpacity(self.current_opacity)
            
        else:
            # --- ОБЫЧНЫЙ РЕЖИМ ---
            self.mw.unlock_overlay.hide()
            self.mw.setWindowOpacity(1.0)
            
            self.mw.inp.show(); self.mw.lock_btn.show()
            self.mw.grip_indicator.show(); self.mw.menu_btn.show(); self.mw.close_btn.show()
            
            self.mw.tree.setDragEnabled(True)

    def mousePressEvent(self, event):
        if self.mw.locked: return
        if event.button() == Qt.MouseButton.LeftButton:
            self.moving = True
            self.drag_start_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.mw.locked: return
        if self.moving and self.drag_start_position:
            delta = QPoint(event.globalPosition().toPoint() - self.drag_start_position)
            
            # Двигаем окно
            new_pos = self.mw.pos() + delta
            self.mw.move(new_pos.x(), new_pos.y())
            
            self.drag_start_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.moving = False
        self.drag_start_position = None
        self.mw.setCursor(Qt.CursorShape.ArrowCursor)

    def resizeEvent(self, event):
        padding_x = 6 
        padding_y = 4
        
        rect = self.mw.rect()
        grip_w = self.mw.grip_indicator.width()
        grip_h = self.mw.grip_indicator.height()
        
        self.mw.grip_indicator.move(
            rect.right() - grip_w - padding_x, 
            rect.bottom() - grip_h - padding_y
        )
        
        # ВАЖНО: Если мы меняем размер в режиме блокировки (теоретически невозможно, 
        # но если вдруг), оверлей должен двигаться вместе с кнопкой.
        # Но так как ресайз в блоке отключен, это просто страховка.

    def wheelEvent(self, event):
        if self.mw.locked:
            delta = event.angleDelta().y()
            step = 0.05
            if delta > 0:
                self.current_opacity = min(1.0, self.current_opacity + step)
            else:
                self.current_opacity = max(0.1, self.current_opacity - step)
            self.mw.setWindowOpacity(self.current_opacity)