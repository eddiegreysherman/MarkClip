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
from PyQt6.QtCore import Qt, QTimer, QMimeData, pyqtSlot
from PyQt6.QtGui import QPalette, QColor, QGuiApplication, QIcon
import mistune


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

        self.editor = QTextEdit()
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

        html = re.sub(r'font-family:[^;"]*;?', "", html)
        html = re.sub(r"line-height:\d+(\.\d+)?;?", "", html)
        html = re.sub(r"font-size:\d+(\.\d+)?(px|pt|em|%)?;?", "", html)

        html = re.sub(r"color:\s*#1e1e1e;?", "#000000", html)
        html = re.sub(r"color:\s*#d4d4d4;?", "#000000", html)
        html = re.sub(r"color:\s*#ffffff;?", "#000000", html)
        html = re.sub(r"color:\s*#9a9a9a;?", "#444444", html)

        html = re.sub(r'(<code[^>]*)style="[^"]*"', r"\1", html)
        html = re.sub(r"(<code[^>]*)background-color:\s*#1e1e1e;?", r"\1", html)

        html = re.sub(
            r'(<span[^>]*style="[^"]*)color:\s*#569cd6;?', r"\1color: #0066cc;", html
        )
        html = re.sub(
            r'(<a[^>]*style="[^"]*)color:\s*#569cd6;?', r"\1color: #0066cc;", html
        )

        html = re.sub(r"-qt-list-indent:\s*\d+;?\s*", "", html)
        html = re.sub(r"-qt-block-indent:\s*\d+;?\s*", "", html)
        html = re.sub(r"text-indent:\s*0px;?\s*", "", html)

        html = re.sub(
            r'(<ul[^>]*style=")([^"]*)margin-left:\s*0px;?',
            r"\1\2margin-left: 24px;",
            html,
        )
        html = re.sub(
            r'(<ol[^>]*style=")([^"]*)margin-left:\s*0px;?',
            r"\1\2margin-left: 24px;",
            html,
        )

        html = re.sub(
            r'(<li[^>]*style=")([^"]*)margin-left:\s*\d+px;?\s*', r"\1\2", html
        )

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
