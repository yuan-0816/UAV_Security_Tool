"""
測試頁面模組
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QStackedWidget,
    QTabWidget,
    QMessageBox,
)

from constants import TARGET_UAV

from .single_target import SingleTargetTestWidget


class UniversalTestPage(QWidget):
    """
    通用測試頁面 - 一個測項的完整頁面
    負責管理 Tab 分頁 (UAV/GCS)
    """

    def __init__(self, config, pm):
        super().__init__()
        self.config = config
        self.pm = pm
        self.targets = config.get("targets", [TARGET_UAV])
        self.allow_share = config.get("allow_share", False)
        self._init_ui()
        self._load_state()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        h = QHBoxLayout()
        h.addWidget(QLabel(f"<h2>{self.config['name']}</h2>"))
        layout.addLayout(h)

        self.chk = None
        if len(self.targets) > 1:
            self.chk = QCheckBox("共用結果")
            self.chk.setStyleSheet("color: blue; font-weight: bold;")
            self.chk.toggled.connect(self.on_share)
            h.addStretch()
            h.addWidget(self.chk)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.p_sep = QWidget()
        v = QVBoxLayout(self.p_sep)
        v.setContentsMargins(0, 0, 0, 0)

        if len(self.targets) > 1:
            tabs = QTabWidget()
            for t in self.targets:
                tabs.addTab(SingleTargetTestWidget(t, self.config, self.pm), t)
            v.addWidget(tabs)
        else:
            v.addWidget(SingleTargetTestWidget(self.targets[0], self.config, self.pm))

        self.stack.addWidget(self.p_sep)

        if len(self.targets) > 1:
            self.p_share = SingleTargetTestWidget(
                "Shared", self.config, self.pm, save_cb=self.save_share
            )
            self.stack.addWidget(self.p_share)

    def _load_state(self):
        uid = self.config.get("uid", self.config.get("id"))
        meta = self.pm.get_test_meta(uid)
        if self.chk and meta.get("is_shared"):
            self.chk.setChecked(True)
            self.stack.setCurrentWidget(self.p_share)

    def on_share(self, checked):
        self.stack.setCurrentWidget(self.p_share if checked else self.p_sep)

    def save_share(self, data):
        uid = self.config.get("uid", self.config.get("id"))
        for t in self.targets:
            self.pm.update_test_result(uid, t, data, is_shared=True)
        QMessageBox.information(self, "成功", "共用儲存完成")
