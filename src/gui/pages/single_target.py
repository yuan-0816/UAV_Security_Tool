"""
單一目標測試元件模組
"""

import os
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QGroupBox,
    QScrollArea,
    QFrame,
    QFileDialog,
    QMessageBox,
)

from constants import (
    STATUS_PASS,
    STATUS_FAIL,
    STATUS_NA,
    STATUS_UNCHECKED,
    COLOR_BG_PASS,
    COLOR_BG_FAIL,
    COLOR_BG_NA,
    COLOR_TEXT_PASS,
    COLOR_TEXT_FAIL,
    DIR_REPORTS,
    TARGET_GCS,
)

from widgets.attachment import AttachmentListWidget
from test_tools.factory import ToolFactory
from dialogs.qr_dialog import QRCodeDialog


class SingleTargetTestWidget(QWidget):
    """單一目標測試元件 - 用於 UAV 或 GCS 的單獨測項"""

    def __init__(self, target, config, pm, save_cb=None):
        super().__init__()
        self.target = target
        self.config = config
        self.pm = pm
        self.item_uid = config.get("uid", config.get("id"))
        self.save_cb = save_cb
        self.logic = config.get("logic", "AND").upper()

        handler_cfg = config.get("handler", {})
        class_name = handler_cfg.get("class_name", "BaseTestTool")

        # Read project data
        item_data = self.pm.project_data.get("tests", {}).get(self.item_uid, {})
        target_key = self.target
        if self.target == "Shared":
            target_key = self.config.get("targets", [TARGET_GCS])[0]
        self.saved_data = item_data.get(target_key, {})

        self.tool = ToolFactory.create_tool(class_name, config, self.saved_data, target)

        # 如果是 NmapTestTool，設定專案路徑並綁定 Signal
        if hasattr(self.tool, "set_project_path"):
            self.tool.set_project_path(self.pm.current_project_path)

        if hasattr(self.tool, "screenshot_taken"):
            self.tool.screenshot_taken.connect(self._on_screenshot_taken)

        # Initialize UI with Scroll Area
        self._init_ui()

        # Load saved attachments
        self._load_attachments()

        self.tool.status_changed.connect(self.update_combo_from_tool)
        self.pm.photo_received.connect(self.on_photo_received)

    def _on_screenshot_taken(self, image_path: str, suggested_title: str):
        """處理 NmapTestTool 發送的截圖事件，加入佐證資料"""
        if self.pm.current_project_path:
            rel_path = os.path.relpath(image_path, self.pm.current_project_path)
        else:
            rel_path = image_path
        self.attachment_list.add_attachment(rel_path, suggested_title, "image")

    def update_combo_from_tool(self, new_status):
        self.combo.setCurrentText(new_status)

    def _init_ui(self):
        self.setMinimumWidth(800)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(15)

        # 左側區塊
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Header
        h = QHBoxLayout()
        h.addWidget(QLabel(f"<h3>對象: {self.target}</h3>"))
        h.addWidget(QLabel(f"({self.logic})"))
        h.addStretch()
        left_layout.addLayout(h)

        # Tool Widget
        tool_widget = self.tool.get_widget()
        has_custom_ui = (
            tool_widget.layout()
            and isinstance(tool_widget.layout(), QHBoxLayout)
            and tool_widget.layout().count() > 1
        )

        if has_custom_ui:
            tool_layout = tool_widget.layout()
            right_item = tool_layout.itemAt(1)
            right_custom_widget = right_item.widget() if right_item else None
            left_item = tool_layout.itemAt(0)
            left_base_widget = left_item.widget() if left_item else None
            if left_base_widget:
                left_layout.addWidget(left_base_widget)
        else:
            left_layout.addWidget(tool_widget)
            right_custom_widget = None

        # Attachments Group
        g_file = QGroupBox("佐證資料 (圖片/檔案)")
        v_file = QVBoxLayout()

        h_btn = QHBoxLayout()
        btn_pc = QPushButton("📂 加入檔案 (多選)")
        btn_pc.clicked.connect(self.upload_report_pc)
        btn_mobile = QPushButton("📱 手機拍照上傳")
        btn_mobile.clicked.connect(self.upload_report_mobile)
        h_btn.addWidget(btn_pc)
        h_btn.addWidget(btn_mobile)
        h_btn.addStretch()
        v_file.addLayout(h_btn)

        self.attachment_list = AttachmentListWidget()
        self.attachment_list.setMinimumHeight(150)
        v_file.addWidget(self.attachment_list)

        g_file.setLayout(v_file)
        left_layout.addWidget(g_file)

        # Result Group
        g3 = QGroupBox("最終判定")
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("結果:"))
        self.combo = QComboBox()
        self.combo.addItems([STATUS_UNCHECKED, STATUS_PASS, STATUS_FAIL, STATUS_NA])
        self.combo.currentTextChanged.connect(self.update_color)

        saved_res = self.saved_data.get("result", STATUS_UNCHECKED)
        idx = self.combo.findText(saved_res)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)
        self.update_color(saved_res)

        h3.addWidget(self.combo)
        g3.setLayout(h3)
        left_layout.addWidget(g3)

        # Save Button
        btn = QPushButton(f"儲存 ({self.target})")
        btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;"
        )
        btn.clicked.connect(self.on_save)
        left_layout.addWidget(btn)

        left_layout.addStretch()
        content_layout.addWidget(left_widget, stretch=1)

        # 右側區塊
        if has_custom_ui and right_custom_widget:
            content_layout.addWidget(right_custom_widget, stretch=1)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _load_attachments(self):
        attachments = self.saved_data.get("attachments", [])
        for item in attachments:
            rel_path = item["path"]
            full_path = rel_path
            if not os.path.isabs(rel_path) and self.pm.current_project_path:
                full_path = os.path.join(self.pm.current_project_path, rel_path)
            self.attachment_list.add_attachment(
                full_path, item.get("title", ""), item.get("type", "image")
            )

    def upload_report_pc(self):
        if not self.pm.current_project_path:
            return
        files, _ = QFileDialog.getOpenFileNames(
            self, "選擇檔案", "", "Images (*.jpg *.png *.jpeg);;Files (*.pdf *.txt)"
        )
        if files:
            for f_path in files:
                rel_path = self.pm.import_file(f_path, DIR_REPORTS)
                if rel_path:
                    ext = os.path.splitext(f_path)[1].lower()
                    ftype = (
                        "image" if ext in [".jpg", ".jpeg", ".png", ".bmp"] else "file"
                    )
                    full_display_path = os.path.join(
                        self.pm.current_project_path, rel_path
                    )
                    self.attachment_list.add_attachment(full_display_path, "", ftype)

    def upload_report_mobile(self):
        if not self.pm.current_project_path:
            return
        title = f"{self.item_uid} 佐證 ({self.target})"
        url = self.pm.generate_mobile_link(self.item_uid, title, is_report=False)
        if url:
            QRCodeDialog(self, self.pm, url, title).exec()

    @Slot(str, str, str)
    def on_photo_received(self, target_id, category, path):
        if target_id == self.item_uid:
            self.attachment_list.add_attachment(path, category, "image")

    def update_color(self, t):
        s = ""
        current_note = self.tool.get_user_note()

        if STATUS_PASS in t:
            s = f"background-color: {COLOR_BG_PASS}; color: {COLOR_TEXT_PASS};"
            if not current_note or "未通過" in current_note or "不適用" in current_note:
                self.tool.set_user_note("符合規範要求。")
        elif STATUS_FAIL in t:
            s = f"background-color: {COLOR_BG_FAIL}; color: {COLOR_TEXT_FAIL};"
            if "符合規範" in current_note or "不適用" in current_note:
                _, fail_reason = self.tool.calculate_result()
                self.tool.set_user_note(
                    fail_reason if fail_reason else "未通過，原因："
                )
        elif STATUS_NA in t:
            s = f"background-color: {COLOR_BG_NA};"
            if (
                not current_note
                or "符合規範" in current_note
                or "未通過" in current_note
            ):
                self.tool.set_user_note("不適用，原因如下：\n")

        self.combo.setStyleSheet(s)

    def on_save(self):
        if not self.pm.current_project_path:
            return

        tool_data = self.tool.get_result()
        final_data = tool_data.copy()

        if "auto_suggest_result" in final_data:
            del final_data["auto_suggest_result"]

        attachments = self.attachment_list.get_all_attachments()

        for att in attachments:
            full_path = att["path"]
            if os.path.isabs(full_path) and full_path.startswith(
                self.pm.current_project_path
            ):
                rel = os.path.relpath(full_path, self.pm.current_project_path)
                att["path"] = rel.replace("\\", "/")

        final_data.update(
            {
                "result": self.combo.currentText(),
                "attachments": attachments,
                "criteria_version_snapshot": self.config.get("criteria_version"),
            }
        )

        if self.save_cb:
            self.save_cb(final_data)
        else:
            self.pm.update_test_result(self.item_uid, self.target, final_data)
            QMessageBox.information(self, "成功", "已儲存")
