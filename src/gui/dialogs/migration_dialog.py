"""
規範遷移預覽對話框模組
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialogButtonBox,
)

from constants import COLOR_TEXT_PASS


class MigrationReportDialog(QDialog):
    """規範遷移預覽報告對話框"""

    def __init__(self, parent, report):
        super().__init__(parent)
        self.setWindowTitle("規範遷移預覽報告")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h3>即將切換規範版本，請確認以下變更：</h3>"))

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["測項名稱", "UID", "狀態", "說明"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.setRowCount(len(report))

        for i, row in enumerate(report):
            table.setItem(i, 0, QTableWidgetItem(row["name"]))
            table.setItem(i, 1, QTableWidgetItem(row["uid"]))
            status_item = QTableWidgetItem(row["status"])
            if row["status"] == "MATCH":
                pass  # 保持預設顏色
            elif row["status"] == "RESET":
                status_item.setForeground(Qt.red)
            elif row["status"] == "NEW":
                status_item.setForeground(Qt.blue)
            table.setItem(i, 2, status_item)
            table.setItem(i, 3, QTableWidgetItem(row["msg"]))

        layout.addWidget(table)

        hint = QLabel("注意：切換前系統將自動備份目前的專案設定檔。")
        hint.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(hint)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
