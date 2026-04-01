#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QSplitter,
)
from PyQt6.QtCore import Qt, QTimer, QMimeData, pyqtSlot, QRegularExpression
from PyQt6.QtGui import (
    QPalette,
    QColor,
    QGuiApplication,
    QIcon,
    QSyntaxHighlighter,
    QTextCharFormat,
    QFont,
)
import mistune


class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._highlighting_rules = []

        header_fmt = QTextCharFormat()
        header_fmt.setForeground(QColor("#7CB9E8"))
        header_fmt.setFontWeight(QFont.Weight.Bold)
        self._highlighting_rules.append(
            (QRegularExpression(r"^#{1,6}\s.+"), header_fmt)
        )

        bold_fmt = QTextCharFormat()
        bold_fmt.setForeground(QColor("#FFEB3B"))
        bold_fmt.setFontWeight(QFont.Weight.Bold)
        self._highlighting_rules.append((QRegularExpression(r"\*\*.+?\*\*"), bold_fmt))
        self._highlighting_rules.append((QRegularExpression(r"__.+?__"), bold_fmt))

        italic_fmt = QTextCharFormat()
        italic_fmt.setForeground(QColor("#E1BEE7"))
        self._highlighting_rules.append(
            (QRegularExpression(r"(?<!\*)\*[^*]+\*(?!\*)"), italic_fmt)
        )
        self._highlighting_rules.append(
            (QRegularExpression(r"(?<!_)_[^_]+_(?!_)"), italic_fmt)
        )

        blockquote_fmt = QTextCharFormat()
        blockquote_fmt.setForeground(QColor("#90EE90"))
        self._highlighting_rules.append((QRegularExpression(r"^>\s.+"), blockquote_fmt))

        bullet_fmt = QTextCharFormat()
        bullet_fmt.setForeground(QColor("#FF9800"))
        self._highlighting_rules.append(
            (QRegularExpression(r"^[\-\*]\s.+"), bullet_fmt)
        )

    def highlightBlock(self, text):
        for pattern, fmt in self._highlighting_rules:
            match = pattern.match(text)
            while match.hasMatch():
                length = match.capturedLength()
                self.setFormat(match.capturedStart(), length, fmt)
                match = pattern.match(text, match.capturedEnd())


class MarkdownEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        import re

        self._re = re

    def keyPressEvent(self, e):
        key = e.key()
        modifiers = e.modifiers()

        if key == Qt.Key.Key_Return and not (
            modifiers & Qt.KeyboardModifier.ShiftModifier
        ):
            if self._handle_list_enter():
                return
        elif key == Qt.Key.Key_Backspace:
            if self._handle_list_backspace():
                return
        elif key == Qt.Key.Key_Tab:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                if self._handle_list_dedent():
                    return
            else:
                if self._handle_list_indent():
                    return

        super().keyPressEvent(e)

    def _get_current_line(self):
        cursor = self.textCursor()
        cursor.select(cursor.SelectionType.LineUnderCursor)
        return cursor.selectedText()

    def _get_line_before_cursor(self):
        cursor = self.textCursor()
        text = cursor.block().text()
        col = cursor.columnNumber()
        return text[:col]

    def _is_list_item(self, line):
        re = self._re
        bullet_match = re.match(r"^(\s*)([-*+])\s+(.+)$", line)
        if bullet_match:
            return ("bullet", bullet_match.group(1), bullet_match.group(2), None, True)

        bullet_empty_match = re.match(r"^(\s*)([-*+])\s*$", line)
        if bullet_empty_match:
            return (
                "bullet",
                bullet_empty_match.group(1),
                bullet_empty_match.group(2),
                None,
                False,
            )

        ordered_match = re.match(r"^(\s*)(\d+)\.\s+(.+)$", line)
        if ordered_match:
            return (
                "ordered",
                ordered_match.group(1),
                None,
                int(ordered_match.group(2)),
                True,
            )

        ordered_empty_match = re.match(r"^(\s*)(\d+)\.\s*$", line)
        if ordered_empty_match:
            return (
                "ordered",
                ordered_empty_match.group(1),
                None,
                int(ordered_empty_match.group(2)),
                False,
            )

        return None

    def _handle_list_enter(self):
        cursor = self.textCursor()
        line = self._get_current_line()
        list_info = self._is_list_item(line)

        if not list_info:
            return False

        list_type, indent, marker, number, has_content = list_info

        if not has_content:
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.insertText("\n")
            return True

        if list_type == "bullet":
            next_marker = marker
            next_item = f"{indent}{next_marker} "
        else:
            next_number = number + 1
            next_item = f"{indent}{next_number}. "

        cursor.movePosition(cursor.MoveOperation.EndOfLine)
        cursor.insertText(f"\n{next_item}")
        return True

    def _handle_list_backspace(self):
        cursor = self.textCursor()
        line = self._get_current_line()
        col = cursor.columnNumber()
        list_info = self._is_list_item(line)

        if not list_info:
            return False

        list_type, indent, marker, number, has_content = list_info

        if list_type == "bullet":
            prefix = f"{indent}{marker} "
        else:
            prefix = f"{indent}{number}. "

        if col <= len(prefix) and not has_content:
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            return True

        if col <= len(prefix) and has_content:
            new_line = line[len(prefix) :]
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.insertText(new_line)
            return True

        return False

    def _handle_list_indent(self):
        cursor = self.textCursor()
        line = self._get_current_line()
        list_info = self._is_list_item(line)

        if not list_info:
            return False

        list_type, indent, marker, number, has_content = list_info
        new_indent = indent + "  "

        if list_type == "bullet":
            new_line = f"{new_indent}{marker} {line.lstrip()[2:]}"
        else:
            new_line = f"{new_indent}{number}. {line.lstrip()[len(str(number)) + 2 :]}"

        cursor.select(cursor.SelectionType.LineUnderCursor)
        cursor.insertText(new_line)
        return True

    def _handle_list_dedent(self):
        cursor = self.textCursor()
        line = self._get_current_line()
        list_info = self._is_list_item(line)

        if not list_info:
            return False

        list_type, indent, marker, number, has_content = list_info

        if len(indent) < 2:
            return False

        new_indent = indent[2:]

        if list_type == "bullet":
            new_line = f"{new_indent}{marker} {line.lstrip()[2:]}"
        else:
            new_line = f"{new_indent}{number}. {line.lstrip()[len(str(number)) + 2 :]}"

        cursor.select(cursor.SelectionType.LineUnderCursor)
        cursor.insertText(new_line)
        return True


class MarkClip(QMainWindow):
    def __init__(self):
        super().__init__()
        self.markdown = mistune.create_markdown(
            hard_wrap=True, plugins=["table", "strikethrough"]
        )
        self.init_ui()
        self.init_dark_theme()

    def init_ui(self):
        self.setWindowTitle("MarkClip")
        self.setGeometry(100, 100, 1200, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #333333;
            }
        """)

        self.editor = MarkdownEditor()
        self.editor.setPlaceholderText("Write your markdown here...")
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                padding: 16px;
                font-family: 'JetBrains Mono Nerd Font', 'JetBrains Mono', 'SF Mono', 'Cascadia Code', Consolas, monospace;
                font-size: 14px;
                line-height: 1.6;
            }
            QTextEdit::placeholder {
                color: #6a6a6a;
            }
        """)
        self.highlighter = MarkdownHighlighter(self.editor.document())

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setStyleSheet("""
            QTextEdit {
                background-color: #252526;
                color: #d4d4d4;
                border: none;
                padding: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
                line-height: 1.6;
            }
        """)

        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        button_container = QWidget()
        button_container.setFixedHeight(48)
        button_container.setStyleSheet("background-color: #252526;")
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 16, 8)
        button_layout.addStretch()

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setFixedSize(80, 32)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5689;
            }
        """)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(self.copy_btn)

        main_layout.addWidget(splitter)
        main_layout.addWidget(button_container)

        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.update_preview)

    def init_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(0x1E, 0x1E, 0x1E))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(0xD4, 0xD4, 0xD4))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(0x25, 0x25, 0x26))
        dark_palette.setColor(
            QPalette.ColorRole.AlternateBase, QColor(0x33, 0x33, 0x33)
        )
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0xD4, 0xD4, 0xD4))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0x1E, 0x1E, 0x1E))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(0xD4, 0xD4, 0xD4))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(0x25, 0x25, 0x26))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(0xD4, 0xD4, 0xD4))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(0xFF, 0xFF, 0xFF))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(0x0E, 0x63, 0x9C))
        dark_palette.setColor(
            QPalette.ColorRole.HighlightedText, QColor(0xFF, 0xFF, 0xFF)
        )
        QApplication.setPalette(dark_palette)

    @pyqtSlot()
    def on_text_changed(self):
        self.debounce_timer.start(100)

    def update_preview(self):
        markdown_text = self.editor.toPlainText()
        if markdown_text.strip():
            html_content = self.markdown(markdown_text)
            styled_html = self.wrap_with_styles(html_content)
            self.preview.setHtml(styled_html)
        else:
            self.preview.clear()

    def wrap_with_styles(self, html_content):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #d4d4d4;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #ffffff;
                margin-top: 24px;
                margin-bottom: 16px;
            }}
            h1 {{ font-size: 2em; border-bottom: 1px solid #333; padding-bottom: 8px; }}
            h2 {{ font-size: 1.5em; border-bottom: 1px solid #333; padding-bottom: 6px; }}
            h3 {{ font-size: 1.25em; }}
            h4 {{ font-size: 1em; }}
            p {{ margin-bottom: 16px; }}
            a {{ color: #569cd6; }}
            code {{
                background-color: #1e1e1e;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'JetBrains Mono Nerd Font', 'JetBrains Mono', 'SF Mono', 'Cascadia Code', Consolas, monospace;
                font-size: 0.9em;
            }}
            pre {{
                background-color: #1e1e1e;
                padding: 16px;
                border-radius: 4px;
                overflow-x: auto;
                margin-bottom: 16px;
            }}
            pre code {{
                background: none;
                padding: 0;
            }}
            blockquote {{
                border-left: 4px solid #569cd6;
                padding-left: 16px;
                margin: 16px 0;
                color: #9a9a9a;
            }}
            ul, ol {{
                margin-bottom: 16px;
                padding-left: 32px;
            }}
            li {{
                margin-bottom: 8px;
                margin-left: 8px;
            }}
            hr {{
                border: none;
                border-top: 1px solid #333;
                margin: 24px 0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 16px;
            }}
            th, td {{
                border: 1px solid #333;
                padding: 8px 12px;
                text-align: left;
            }}
            th {{
                background-color: #1e1e1e;
            }}
            img {{
                max-width: 100%;
                height: auto;
            }}
        </style>
        </head>
        <body>{html_content}</body>
        </html>
        """

    def create_clean_html_for_clipboard(self, html_content):
        import re

        html = html_content

        html = re.sub(r"<!DOCTYPE html[^>]*>", "", html, flags=re.IGNORECASE)
        html = re.sub(r"<html[^>]*>", "", html, flags=re.IGNORECASE)
        html = re.sub(r"</html>", "", html, flags=re.IGNORECASE)
        html = re.sub(
            r"<head[^>]*>.*?</head>", "", html, flags=re.DOTALL | re.IGNORECASE
        )
        html = re.sub(r"<body[^>]*>", "", html, flags=re.IGNORECASE)
        html = re.sub(r"</body>", "", html, flags=re.IGNORECASE)
        html = re.sub(
            r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE
        )

        html = re.sub(
            r"<span[^>]*font-weight:\s*(?:bold|700)[^>]*font-style:\s*italic[^>]*>(.*?)</span>",
            r"<strong><em>\1</em></strong>",
            html,
            flags=re.DOTALL,
        )
        html = re.sub(
            r"<span[^>]*font-style:\s*italic[^>]*font-weight:\s*(?:bold|700)[^>]*>(.*?)</span>",
            r"<strong><em>\1</em></strong>",
            html,
            flags=re.DOTALL,
        )
        html = re.sub(
            r"<span[^>]*font-weight:\s*(?:bold|700)[^>]*>(.*?)</span>",
            r"<strong>\1</strong>",
            html,
            flags=re.DOTALL,
        )
        html = re.sub(
            r"<span[^>]*font-style:\s*italic[^>]*>(.*?)</span>",
            r"<em>\1</em>",
            html,
            flags=re.DOTALL,
        )
        html = re.sub(
            r"<span[^>]*text-decoration:\s*line-through[^>]*>(.*?)</span>",
            r"<del>\1</del>",
            html,
            flags=re.DOTALL,
        )

        html = re.sub(r'\s*style="[^"]*"', "", html)

        return html

    def copy_to_clipboard(self):
        html_content = self.preview.toHtml()
        clean_html = self.create_clean_html_for_clipboard(html_content)
        plain_text = self.editor.toPlainText()

        mime_data = QMimeData()
        mime_data.setHtml(clean_html)
        mime_data.setText(plain_text)

        clipboard = QGuiApplication.clipboard()
        clipboard.setMimeData(mime_data)

        self.copy_btn.setText("Copied!")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d8a2d;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
        """)

        QTimer.singleShot(1500, self.reset_copy_button)

    def reset_copy_button(self):
        self.copy_btn.setText("Copy")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5689;
            }
        """)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MarkClip")

    import os

    icon_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "icon-final.png"
    )
    icon = QIcon(icon_path)
    if not icon.isNull():
        app.setWindowIcon(icon)

    window = MarkClip()
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
