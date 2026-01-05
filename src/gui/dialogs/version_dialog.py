"""
規範版本選擇對話框模組
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QDialogButtonBox,
    QMessageBox,
)


class VersionSelectionDialog(QDialog):
    """規範版本選擇對話框"""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("選擇檢測規範版本")
        self.resize(400, 200)
        self.cm = config_manager
        self.selected_config = None
        self.selected_path = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>請選擇本次檢測使用的規範版本：</h2>"))
        self.combo = QComboBox()
        self.configs = self.cm.list_available_configs()
        if not self.configs:
            self.combo.addItem("找不到設定檔 (請檢查 configs 資料夾)")
            self.combo.setEnabled(False)
        else:
            for cfg in self.configs:
                self.combo.addItem(cfg["name"], cfg["path"])
        layout.addWidget(self.combo)
        hint = QLabel("設定檔請放置於程式目錄下的 'configs' 資料夾中")
        hint.setStyleSheet("color: gray; font-size: 10pt;")
        layout.addWidget(hint)
        layout.addStretch()
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def on_accept(self):
        if not self.configs:
            return
        idx = self.combo.currentIndex()
        path = self.combo.itemData(idx)
        try:
            data = self.cm.load_config(path)
            if "test_standards" not in data:
                raise ValueError("JSON 格式不符 (缺少 test_standards)")
            self.selected_config = data
            self.selected_path = path
            self.accept()
        except ValueError as ve:
            QMessageBox.critical(self, "規範驗證失敗", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "讀取失敗", f"設定檔無效：\n{str(e)}")
