"""
相簿視窗模組 - 六視角照片檢視
"""

import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
)

from constants import PHOTO_ANGLES_ORDER, PHOTO_ANGLES_NAME


class GalleryWindow(QDialog):
    """六視角照片檢視視窗"""

    def __init__(self, parent, pm, target_name):
        super().__init__(parent)
        self.pm = pm
        self.target_name = target_name
        self.setWindowTitle(f"{target_name.upper()} - 六視角照片檢視")
        self.resize(1000, 700)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        grid = QGridLayout()
        layout.addLayout(grid)

        positions = {
            "front": (0, 0),
            "back": (0, 1),
            "top": (0, 2),
            "side1": (1, 0),
            "side2": (1, 1),
            "bottom": (1, 2),
        }

        info_data = self.pm.project_data.get("info", {})

        for angle in PHOTO_ANGLES_ORDER:
            row, col = positions.get(angle, (0, 0))
            container = QFrame()
            container.setFrameShape(QFrame.Box)
            v_box = QVBoxLayout(container)

            lbl_title = QLabel(PHOTO_ANGLES_NAME[angle])
            lbl_title.setAlignment(Qt.AlignCenter)
            lbl_title.setStyleSheet("font-weight: bold; background-color: #eee;")

            lbl_img = QLabel()
            lbl_img.setAlignment(Qt.AlignCenter)
            lbl_img.setMinimumSize(300, 200)

            path_key = f"{self.target_name}_{angle}_path"
            rel_path = info_data.get(path_key)

            if rel_path and self.pm.current_project_path:
                full_path = os.path.join(self.pm.current_project_path, rel_path)
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    lbl_img.setPixmap(
                        pixmap.scaled(
                            320, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                    )
                else:
                    lbl_img.setText("檔案遺失")
                    lbl_img.setStyleSheet("color: red;")
            else:
                lbl_img.setText("未上傳")
                lbl_img.setStyleSheet("color: gray; font-size: 14pt;")

            v_box.addWidget(lbl_title)
            v_box.addWidget(lbl_img)
            grid.addWidget(container, row, col)

        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
