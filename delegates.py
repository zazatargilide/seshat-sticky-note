#delegates.py
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QApplication, QStyle
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QFontMetrics
from localization import Loc 

class DateDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.accent_color = QColor(124, 77, 255) 

    def set_accent_color(self, hex_color):
        self.accent_color = QColor(hex_color)

    def paint(self, painter, option, index):
        tree_widget = self.parent()
        item = tree_widget.itemFromIndex(index)
        
        # Проверяем, отменена ли задача (безопасно)
        is_cancelled = getattr(item, 'cancelled', False)

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        style = tree_widget.style() or QApplication.style()

        painter.save()

        # 1. ОЧИСТКА ФОНА
        painter.fillRect(option.rect, QColor("#1e1e1e"))

        # 2. ВЫДЕЛЕНИЕ
        if opt.state & QStyle.StateFlag.State_Selected:
            bg_color = QColor(self.accent_color)
            bg_color.setAlpha(40) 
            painter.fillRect(option.rect, bg_color)

        # 3. ЧЕКБОКС (Если отменено - рисуем полупрозрачным или обычным)
        check_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemCheckIndicator, opt, tree_widget)
        check_opt = QStyleOptionViewItem(opt)
        check_opt.rect = check_rect
        check_opt.state = opt.state 
        
        if item.checkState(0) == Qt.CheckState.Checked:
            check_opt.state |= QStyle.StateFlag.State_On
        else:
            check_opt.state |= QStyle.StateFlag.State_Off
            
        # Если отменено - делаем чекбокс бледным
        if is_cancelled:
            painter.setOpacity(0.3)
            
        style.drawPrimitive(QStyle.PrimitiveElement.PE_IndicatorItemViewItemCheck, check_opt, painter, tree_widget)
        
        if is_cancelled:
            painter.setOpacity(1.0) # Возвращаем непрозрачность для текста

        # 4. ДАННЫЕ
        main_text = item.text(0)
        date_str = item.data(0, Qt.ItemDataRole.UserRole)
        is_checked = (item.checkState(0) == Qt.CheckState.Checked)
        
        content_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, opt, tree_widget)
        content_rect.setLeft(content_rect.left() + 15)

        # 5. НАСТРОЙКА ШРИФТА (Зачеркивание)
        font = painter.font()
        if is_cancelled:
            font.setStrikeOut(True) # <--- ЗАЧЕРКИВАНИЕ
            painter.setFont(font)
            # Цвет для отмененных (темно-серый)
            painter.setPen(QColor("#606060")) 
        elif opt.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QColor("white"))
        elif is_checked:
            painter.setPen(QColor("#606060")) # Цвет выполненных
        else:
            painter.setPen(QColor("#e0e0e0")) # Обычный цвет

        # 6. ЛОГИКА ДАТЫ (Скрываем дату, если отменено)
        date_width = 0
        if is_checked and date_str and not is_cancelled:
            # ... (Ваш код отрисовки даты, без изменений) ...
            # Копируйте старую логику сюда
            font_date = painter.font() # Важно брать текущий шрифт painter'а
            font_date.setPointSize(9)
            font_date.setItalic(True)
            font_date.setStrikeOut(False) # У даты зачеркивание убираем
            fm_date = QFontMetrics(font_date)
            
            try:
                parts = date_str.split(',') 
                date_part = parts[0].strip()
                time_part = parts[1].strip()
                short_date = date_part[:5]
            except:
                date_part, time_part, short_date = date_str, "", ""

            done_txt = Loc.t("done_by") 
            candidates = [
                f"{done_txt}: {date_part}, {time_part}",
                f"{done_txt}: {short_date}, {time_part}",
                f"{done_txt}: {time_part}",
                f"{done_txt}..."
            ]
            
            minimum_text_space = 160 
            gap = 20
            available_for_date = content_rect.width() - minimum_text_space - gap
            
            for candidate in candidates:
                w = fm_date.horizontalAdvance(candidate)
                if w <= available_for_date:
                    text_to_draw_date = candidate
                    date_width = w
                    break
            
            if date_width == 0 and available_for_date > 20:
                text_to_draw_date = candidates[-1]
                date_width = fm_date.horizontalAdvance(text_to_draw_date)

            if date_width > 0:
                date_rect = QRect(content_rect)
                date_rect.setLeft(content_rect.right() - date_width)
                
                painter.setFont(font_date)
                painter.setPen(QColor(140, 140, 140))
                painter.drawText(date_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, text_to_draw_date)
                
                # Возвращаем шрифт для основного текста
                painter.setFont(font) 
                if is_cancelled: painter.setPen(QColor("#606060"))
                elif is_checked: painter.setPen(QColor("#606060"))
                else: painter.setPen(QColor("#e0e0e0"))

        # 7. ОТРИСОВКА ТЕКСТА
        text_rect = QRect(content_rect)
        if date_width > 0:
            text_rect.setRight(content_rect.right() - date_width - 20)
        else:
            text_rect.setRight(content_rect.right() - 5)
            
        elided_text = painter.fontMetrics().elidedText(main_text, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_text)
        
        painter.restore()