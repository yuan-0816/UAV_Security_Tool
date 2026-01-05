"""
快速測試選擇器模組
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QFileDialog,
)

from constants import DEFAULT_DESKTOP_PATH


class QuickTestSelector(QDialog):
    """快速測試選擇器對話框"""

    def __init__(self, parent, config):
        super().__init__(parent)
        self.setWindowTitle("選擇檢測項目 (各別模式)")
        self.resize(400, 500)
        self.config = config
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("請勾選本次要進行檢測的項目："))

        self.list_widget = QListWidget()
        for section in self.config.get("test_standards", []):
            header = QListWidgetItem(f"--- {section['section_name']} ---")
            header.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(header)
            for item in section["items"]:
                li = QListWidgetItem(f"{item['id']} {item['name']}")
                li.setFlags(li.flags() | Qt.ItemIsUserCheckable)
                li.setCheckState(Qt.Unchecked)
                li.setData(Qt.UserRole, item.get("uid", item.get("id")))
                self.list_widget.addItem(li)
        layout.addWidget(self.list_widget)

        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(DEFAULT_DESKTOP_PATH)
        btn_browse = QPushButton("...")
        btn_browse.clicked.connect(self._browse)
        path_layout.addWidget(QLabel("儲存位置:"))
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(btn_browse)
        layout.addLayout(path_layout)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if d:
            self.path_edit.setText(d)

    def get_data(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected, self.path_edit.text()

    def run(self):
        if self.exec() == QDialog.Accepted:
            return self.get_data()
        return None, None
