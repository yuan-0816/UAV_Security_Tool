"""
附件元件模組
"""

import os
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
)

from styles import Styles
from .aspect_label import AspectLabel


class AttachmentItemWidget(QWidget):
    """附件項目元件"""

    on_delete = Signal(QWidget)

    def __init__(self, file_path, title="", file_type="image", row_height=100):
        super().__init__()
        self.file_path = file_path
        self.file_type = file_type
        self.row_height = row_height

        # 強制設定整列的高度 (包含 padding)
        self.setFixedHeight(self.row_height)

        self._init_ui(title)

    def _init_ui(self, title):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # --- 1. 拖曳手柄 ---
        lbl_handle = QLabel("☰")
        lbl_handle.setStyleSheet("color: #aaa; font-size: 16pt;")
        lbl_handle.setCursor(Qt.SizeAllCursor)
        lbl_handle.setFixedWidth(25)
        lbl_handle.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_handle)

        # --- 2. 圖片 (AspectLabel) ---
        self.lbl_icon = AspectLabel()
        self.lbl_icon.setFixedWidth(int(self.row_height * 1.3))
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setStyleSheet(Styles.THUMBNAIL)

        if self.file_type == "image" and os.path.exists(self.file_path):
            pix = QPixmap(self.file_path)
            if not pix.isNull():
                self.lbl_icon.setPixmap(pix)
            else:
                self.lbl_icon.setText("Error")
        else:
            self.lbl_icon.setText("FILE")

        layout.addWidget(self.lbl_icon)

        # --- 3. 資訊區 ---
        v_info = QVBoxLayout()
        v_info.setSpacing(2)
        v_info.setContentsMargins(0, 5, 0, 5)

        # 標題
        self.edit_title = QLineEdit(title)
        self.edit_title.setPlaceholderText("請輸入說明...")
        self.edit_title.setStyleSheet(Styles.ATTACHMENT_TITLE)

        # 檔名顯示
        filename = os.path.basename(self.file_path)
        self.lbl_filename = QLabel(filename)
        self.lbl_filename.setStyleSheet("color: #555; font-size: 9pt;")
        self.lbl_filename.setWordWrap(True)
        self.lbl_filename.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.lbl_filename.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)

        v_info.addWidget(self.edit_title)
        v_info.addWidget(self.lbl_filename, 1)

        layout.addLayout(v_info, 1)

        # --- 4. 刪除按鈕 ---
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(30, 30)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet(Styles.BTN_DANGER)
        btn_del.clicked.connect(lambda: self.on_delete.emit(self))
        layout.addWidget(btn_del)

    def get_data(self):
        return {
            "type": self.file_type,
            "path": self.file_path,
            "title": self.edit_title.text(),
        }


class AttachmentListWidget(QListWidget):
    """支援拖曳排序且高度自適應的列表元件"""

    def __init__(self):
        super().__init__()
        self.setDragDropMode(QListWidget.InternalMove)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setSpacing(2)
        self.setResizeMode(QListWidget.Adjust)
        self.setStyleSheet(Styles.ATTACHMENT_LIST)

        # 一列高度 (包含圖片和多行文字的最大高度)
        self.row_height = 60

    def add_attachment(self, file_path, title="", file_type="image"):
        item = QListWidgetItem(self)

        # 建立 Widget，傳入高度限制
        widget = AttachmentItemWidget(
            file_path, title, file_type, row_height=self.row_height
        )

        self.setItemWidget(item, widget)

        # 設定 Item 的 SizeHint 與 Widget 高度一致
        item.setSizeHint(QSize(widget.sizeHint().width(), self.row_height))

        widget.on_delete.connect(self.remove_attachment_row)

    def remove_attachment_row(self, widget):
        for i in range(self.count()):
            item = self.item(i)
            if self.itemWidget(item) == widget:
                self.takeItem(i)
                break

    def get_all_attachments(self) -> list:
        results = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget:
                results.append(widget.get_data())
        return results
