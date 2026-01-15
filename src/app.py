from src.core.processor import process_document
import sys
import json
import os
import re
from src.core.bootstrap import setup_poppler

try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QPushButton, QLabel, QTextEdit,
        QFileDialog, QHBoxLayout, QVBoxLayout, QGroupBox, QMessageBox
    )
    from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
    from PyQt6.QtCore import Qt
    FROM_PYQT6 = True
except Exception:
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QPushButton, QLabel, QTextEdit,
        QFileDialog, QHBoxLayout, QVBoxLayout, QGroupBox, QMessageBox
    )
    from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
    from PyQt5.QtCore import Qt
    FROM_PYQT6 = False


# ====== Подсветка JSON ======
class JsonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Цвета
        self.color_key = QColor("#9CDCFE")      # голубой (ключи)
        self.color_number = QColor("#B5CEA8")   # зелёный (числа)
        self.color_string = QColor("#CE9178")   # терракотовый (строки)
        self.color_bracket = QColor("#D4D4D4")  # светло-серый (скобки)
        self.color_boolean = QColor("#569CD6")  # голубой для булевых

        # Паттерны
        self.re_string = re.compile(r'"([^"\\]|\\.)*"')                           # находит строки в двойных кавычках
        self.re_key = re.compile(r'"([^"\\]|\\.)*"\s*(?=:)')                      # ищет ключи
        self.re_boolean = re.compile(r'\b(true|false|null|True|False|Null)\b')    # ищет булево значение
        self.re_number = re.compile(r'\b-?\d+(\.\d+)?([eE][+-]?\d+)?\b')          # ищет числа с дробной частью
        self.re_bracket = re.compile(r'[{}\[\]]')                                 # отдельные строки {} []

        # Форматы
        self.fmt_string = QTextCharFormat()
        self.fmt_string.setForeground(self.color_string)

        self.fmt_key = QTextCharFormat()
        self.fmt_key.setForeground(self.color_key)

        self.fmt_boolean = QTextCharFormat()
        self.fmt_boolean.setForeground(self.color_boolean)

        self.fmt_number = QTextCharFormat()
        self.fmt_number.setForeground(self.color_number)

        self.fmt_bracket = QTextCharFormat()
        self.fmt_bracket.setForeground(self.color_bracket)

    def highlightBlock(self, text):
        string_ranges = []

        # 1) строки
        for m in self.re_string.finditer(text):
            start, end = m.start(), m.end()
            self.setFormat(start, end - start, self.fmt_string)
            string_ranges.append((start, end))

        def in_string(pos_start, pos_end):
            for s, e in string_ranges:
                if pos_start < e and pos_end > s:
                    return True
            return False

        # 2) ключи
        for m in self.re_key.finditer(text):
            s, e = m.start(), m.end()
            self.setFormat(s, e - s, self.fmt_key)

        # 3) булевы/null
        for m in self.re_boolean.finditer(text):
            s, e = m.start(), m.end()
            if not in_string(s, e):
                self.setFormat(s, e - s, self.fmt_boolean)

        # 4) числа
        for m in self.re_number.finditer(text):
            s, e = m.start(), m.end()
            if not in_string(s, e):
                self.setFormat(s, e - s, self.fmt_number)

        # 5) скобки
        for m in self.re_bracket.finditer(text):
            s, e = m.start(), m.end()
            self.setFormat(s, e - s, self.fmt_bracket)


class DarkMockupUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система распознавание документов")
        self.resize(1000, 600)

        self.loaded_file = None

        # ====== ТЁМНАЯ ТЕМА ======
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #dcdcdc;
                font-family: "Segoe UI", "Segoe UI Variable";
                font-size: 13pt;
            }

            QGroupBox {
                background: #252526;
                border: 1px solid #2e2e2e;
                border-radius: 12px;
                margin-top: 10px;
                padding: 12px;
                font-size: 15pt;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px; 
                top: 18px;
                font-size: 14pt;
                font-weight: 600;
            }

            QGroupBox#leftGroup::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                left: 0px;
                top: 18px;
                font-size: 14pt;
                font-weight: 600;
            }

            QPushButton {
                background-color: #2a2a2a;
                color: #e6e6e6;
                border: 1px solid #333333;
                border-radius: 10px;
                padding: 10px 14px;
                min-height: 36px;
            }

            QPushButton:hover {
                background-color: #323232;
            }

            QPushButton#mainBtn {
                background-color: #0063b1;
                border: 1px solid #00579a;
            }
            QPushButton#mainBtn:hover {
                background-color: #0078d4;
            }

            QTextEdit {
                background-color: #171717;
                color: #e6e6e6;
                border: 1px solid #2b2b2b;
                border-radius: 10px;
                padding: 10px;
            }

            QLabel {
                color: #dadada;
                background: transparent;
            }
        """)

        # ====== ЛЕВАЯ ПАНЕЛЬ ======
        self.btn_load = QPushButton("Загрузить файл")
        self.btn_load.clicked.connect(self.load_file)

        self.label_formats = QLabel("PDF, DOC, DOCX, PNG, JPG, JSON")
        self.label_formats.setStyleSheet("color: #a0a0a0; font-size: 9pt;")
        self.label_formats.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.label_filename = QLabel("Файл не выбран")
        self.label_filename.setStyleSheet("color: #c0c0c0; font-size: 9pt;")
        self.label_filename.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.btn_process = QPushButton("Извлечь данные")
        self.btn_process.setObjectName("mainBtn")
        self.btn_process.clicked.connect(self.extract_data)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)
        left_layout.addStretch(1)
        left_layout.addWidget(self.btn_load)
        left_layout.addWidget(self.label_formats)
        left_layout.addWidget(self.label_filename)
        left_layout.addSpacing(12)
        left_layout.addWidget(self.btn_process)
        left_layout.addStretch(1)

        left_group = QGroupBox("Загрузка файлов")
        left_group.setObjectName("leftGroup")
        left_group.setLayout(left_layout)

        # ====== ПРАВАЯ ПАНЕЛЬ ======
        right_layout = QVBoxLayout()
        right_layout.addSpacing(25)

        self.json_output = QTextEdit()
        self.json_output.setObjectName("jsonOutput")
        self.json_output.setReadOnly(False)
        right_layout.addWidget(self.json_output)

        # Подключаем подсветку
        self.highlighter = JsonHighlighter(self.json_output.document())

        self.btn_copy = QPushButton("Скопировать")
        self.btn_copy.clicked.connect(self.copy_output)

        self.btn_save = QPushButton("Скачать JSON")
        self.btn_save.clicked.connect(self.save_json)

        bottom_buttons = QHBoxLayout()
        bottom_buttons.addWidget(self.btn_copy)
        bottom_buttons.addWidget(self.btn_save)

        right_layout.addLayout(bottom_buttons)

        right_group = QGroupBox("Результат обработки (JSON)")
        right_group.setObjectName("rightGroup")
        right_group.setLayout(right_layout)

        # ====== ОСНОВНАЯ РАЗМЕТКА ======
        main = QHBoxLayout()
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(16)
        main.addWidget(left_group, 1)
        main.addWidget(right_group, 2)
        self.setLayout(main)

    # ====== ЛОГИКА ======
    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить файл",
            "",
            "Документы, сканы и JSON (*.pdf *.doc *.docx *.png *.jpg *.jpeg *.json)"
        )
        if path:
            self.loaded_file = path
            self.label_filename.setText(os.path.basename(path))

            if path.lower().endswith(".json"):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.json_output.setText(json.dumps(data, ensure_ascii=False, indent=4))
                except Exception as e:
                    self.show_error(f"Ошибка JSON:\n{e}")
                    self.json_output.clear()
            else:
                # Если выбран не JSON — очищаем поле
                self.json_output.clear()

    def extract_data(self):
        if not self.loaded_file:
            self.show_error("Файл не выбран")
            return

        try:
            result = process_document(self.loaded_file)

            if "error" in result:
                self.show_error(result["error"])
                return

            self.json_output.setText(
                json.dumps(result, ensure_ascii=False, indent=4)
            )

        except Exception as e:
            self.show_error(f"Ошибка обработки:\n{e}")

    def copy_output(self):
        QApplication.clipboard().setText(self.json_output.toPlainText())

    def save_json(self):
        if not self.json_output.toPlainText():
            return
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить JSON", "result.json", "JSON (*.json)")
        if path:
            try:
                data = json.loads(self.json_output.toPlainText())
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                self.show_error(f"Ошибка сохранения JSON:\n{e}")

    def show_error(self, message):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Ошибка")
        dlg.setText(message)
        dlg.setIcon(QMessageBox.Icon.Critical)
        dlg.exec()


def main():
    setup_poppler()
    app = QApplication(sys.argv)
    gui = DarkMockupUI()
    gui.show()
    if FROM_PYQT6:
        sys.exit(app.exec())
    else:
        sys.exit(app.exec_())
