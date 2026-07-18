"""HashMate 图形界面（PySide6）。

布局：
- 文件路径输入 + 浏览按钮（支持拖拽文件）
- 自由文本输入 + 「解析文本」
- 解析结果表格：类型（下拉，可改）、哈希值（可改）、置信度、来源、校验结果
  支持「添加行 / 删除选中行」进行人工纠错
- 「校验文件哈希」对比文件实际哈希与表格中的目标值
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .hasher import compute_hashes
from .parser import HASH_TYPES, parse_text

# 类型下拉框数据：("显示名", key)；key 为 None 表示「未知 / 待定」。
TYPE_ITEMS = [("未知", None)] + [(ht.label, ht.key) for ht in HASH_TYPES.values()]


def _make_type_combo(current_key: str | None) -> QComboBox:
    combo = QComboBox()
    for label, key in TYPE_ITEMS:
        combo.addItem(label, key)
    idx = next((i for i, (_, k) in enumerate(TYPE_ITEMS) if k == current_key), 0)
    combo.setCurrentIndex(idx)
    return combo


class FilePathEdit(QLabel):
    """支持拖拽文件的路径显示框。"""

    def __init__(self, parent: MainWindow):
        super().__init__("拖拽文件到此处，或点击右侧「浏览」")
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 1px solid #999; padding: 6px; border-radius: 4px;")
        self._parent = parent

    def set_path(self, path: str) -> None:
        self.setText(path or "拖拽文件到此处，或点击右侧「浏览」")

    def dragEnterEvent(self, event):  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802
        urls = event.mimeData().urls()
        if urls:
            self._parent.set_file(urls[0].toLocalFile())


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HashMate · 哈希校验工具")
        icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "icon.ico"
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(900, 720)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        root.addWidget(self._build_file_group(), 0)
        root.addWidget(self._build_text_group(), 0)
        root.addWidget(self._build_result_group(), 1)
        root.addWidget(self._build_verify_group(), 0)

        self._file_path: str | None = None
        self._cached_hashes: dict[str, str] | None = None

    # ----------------------------- 文件组 ----------------------------- #
    def _build_file_group(self) -> QWidget:
        box = QGroupBox("文件")
        layout = QHBoxLayout(box)

        self._path_label = FilePathEdit(self)
        layout.addWidget(self._path_label, 1)

        browse = QPushButton("浏览…")
        browse.clicked.connect(self._browse)
        layout.addWidget(browse)
        return box

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if path:
            self.set_file(path)

    def set_file(self, path: str) -> None:
        self._file_path = path
        self._path_label.set_path(path)
        self._refresh_file_hashes()

    # ----------------------------- 文本组 ----------------------------- #
    def _build_text_group(self) -> QWidget:
        box = QGroupBox("提供的文本（哈希信息，自由格式）")
        layout = QVBoxLayout(box)

        self._text_edit = QTextEdit()
        self._text_edit.setFont(QFont("Microsoft YaHei UI", 10))
        self._text_edit.setMaximumHeight(120)
        self._text_edit.setPlaceholderText(
            "粘贴包含哈希值的文本，例如：\n"
            "MD5： 6c8000da9731a35fa6ad37132c4005ee\n"
            "SHA-256： 591ae6d22871a6e7918fbe8ccc0c9d0279c771a0b0a3d8e7dbec4abfe78335b7"
        )
        layout.addWidget(self._text_edit)

        parse_btn = QPushButton("解析文本")
        parse_btn.clicked.connect(self._parse_text)
        layout.addWidget(parse_btn)
        return box

    def _parse_text(self) -> None:
        text = self._text_edit.toPlainText()
        result = parse_text(text)
        self._table.setRowCount(0)
        for m in result:
            self._add_row(m.hash_type, m.value, f"{m.confidence:.2f}", m.source)
        QMessageBox.information(
            self, "解析完成", f"共解析出 {len(result)} 条哈希候选，可人工核对并修正。"
        )

    # ----------------------------- 结果表 ----------------------------- #
    def _build_result_group(self) -> QWidget:
        box = QGroupBox("解析结果（可编辑 / 纠错）")
        layout = QVBoxLayout(box)

        toolbar = QHBoxLayout()
        add_btn = QPushButton("+ 添加行")
        add_btn.clicked.connect(lambda: self._add_row(None, "", "", ""))
        del_btn = QPushButton("- 删除选中行")
        del_btn.clicked.connect(self._delete_selected)
        toolbar.addWidget(add_btn)
        toolbar.addWidget(del_btn)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["类型", "哈希值", "置信度", "来源", "校验结果"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setFont(QFont("Consolas", 10))
        self._table.horizontalHeader().setFont(QFont("Microsoft YaHei UI", 9))
        self._table.verticalHeader().setDefaultSectionSize(28)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, 1)
        return box

    def _add_row(
        self,
        key: str | None,
        value: str,
        confidence: str,
        source: str,
    ) -> None:
        r = self._table.rowCount()
        self._table.insertRow(r)
        self._table.setCellWidget(r, 0, _make_type_combo(key))

        val_item = QTableWidgetItem(value)
        self._table.setItem(r, 1, val_item)

        for col, text in ((2, confidence), (3, source), (4, "")):
            item = QTableWidgetItem(text)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self._table.setItem(r, col, item)

    def _delete_selected(self) -> None:
        rows = sorted({idx.row() for idx in self._table.selectedIndexes()}, reverse=True)
        for r in rows:
            self._table.removeRow(r)

    # ----------------------------- 校验组 ----------------------------- #
    def _build_verify_group(self) -> QWidget:
        box = QGroupBox("校验")
        layout = QVBoxLayout(box)

        verify_btn = QPushButton("校验文件哈希")
        verify_btn.clicked.connect(self._verify)
        layout.addWidget(verify_btn)

        self._file_hash_view = QPlainTextEdit()
        self._file_hash_view.setReadOnly(True)
        self._file_hash_view.setMaximumHeight(110)
        layout.addWidget(QLabel("文件实际哈希值："))
        layout.addWidget(self._file_hash_view)

        self._summary = QLabel("")
        layout.addWidget(self._summary)
        return box

    def _refresh_file_hashes(self) -> None:
        self._file_hash_view.clear()
        self._summary.clear()
        self._cached_hashes = None
        if not self._file_path or not os.path.isfile(self._file_path):
            return
        try:
            self._cached_hashes = compute_hashes(self._file_path)
        except OSError as exc:
            self._file_hash_view.setPlainText(f"读取失败：{exc}")
            return
        lines = [f"{HASH_TYPES[k].label}: {v}" for k, v in self._cached_hashes.items()]
        self._file_hash_view.setPlainText("\n".join(lines))

    def _verify(self) -> None:
        if not self._file_path or not os.path.isfile(self._file_path):
            QMessageBox.warning(self, "提示", "请先选择有效文件。")
            return

        rows = []
        for r in range(self._table.rowCount()):
            combo = self._table.cellWidget(r, 0)
            key = combo.currentData() if combo else None
            val_item = self._table.item(r, 1)
            value = val_item.text().strip().lower() if val_item else ""
            if not value:
                continue
            rows.append((r, key, value))

        if not rows:
            QMessageBox.information(self, "提示", "表格中没有可校验的哈希值。")
            return

        if self._cached_hashes is None:
            QMessageBox.warning(self, "提示", "请先选择一个文件。")
            return

        matched = 0
        for r, key, value in rows:
            if key:
                ok = self._cached_hashes.get(key) == value
                result = (
                    "匹配 ✓"
                    if ok
                    else (
                        f"不匹配 ✗（文件{HASH_TYPES[key].label}: {self._cached_hashes[key][:10]}…）"
                    )
                )
                if ok:
                    matched += 1
            else:
                found = [k for k, v in self._cached_hashes.items() if v == value]
                if found:
                    matched += 1
                    result = f"匹配 ✓（推断为 {HASH_TYPES[found[0]].label}）"
                else:
                    result = "不匹配 ✗"
            item = QTableWidgetItem(result)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if "匹配" in result:
                item.setForeground(QColor("#1b7e1b"))
            elif "不匹配" in result:
                item.setForeground(QColor("#c0392b"))
            self._table.setItem(r, 4, item)

        total = len(rows)
        self._summary.setText(f"校验完成：{matched} / {total} 条匹配。")
        if matched == total:
            self._summary.setStyleSheet("color: green;")
        else:
            self._summary.setStyleSheet("color: #c0392b;")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(
        """
        QPushButton {
            padding: 6px 18px;
            border: none;
            border-radius: 4px;
            color: #fff;
            font-weight: bold;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2196F3, stop:1 #1565C0);
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #42A5F5, stop:1 #1976D2);
        }
        QPushButton:pressed {
            background: #0D47A1;
        }
        """
    )
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
