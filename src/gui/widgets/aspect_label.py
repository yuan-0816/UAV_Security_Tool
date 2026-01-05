"""
AspectLabel - 自動根據高度縮放圖片的標籤元件
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy


class AspectLabel(QLabel):
    """
    自動根據當前高度縮放圖片，保持比例
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(False)
        self._pixmap = None
        # 設定 Policy 為 Ignored，表示"我願意被縮小到比我原本內容更小"
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update_image()

    def resizeEvent(self, event):
        self.update_image()
        super().resizeEvent(event)

    def update_image(self):
        if self._pixmap and not self._pixmap.isNull():
            # 取得當前元件的實際高度 (由 Layout 決定)
            h = self.height()
            if h > 0:
                scaled = self._pixmap.scaledToHeight(h, Qt.SmoothTransformation)
                super().setPixmap(scaled)
