"""
自訂標題列模組
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from styles import Styles


class CustomTitleBar(QWidget):
    """自訂標題列"""

    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setFixedHeight(36)
        self.setMouseTracking(True)

        # 標題 Label (獨立層，不加入 Layout)
        self.title_label = QLabel("MainWindow", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        # 按鈕 Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(4)
        layout.addStretch()

        self.btn_min = QPushButton("─")
        self.btn_max = QPushButton("□")
        self.btn_close = QPushButton("✕")
        self.buttons = [self.btn_min, self.btn_max, self.btn_close]

        for b in self.buttons:
            b.setFixedSize(36, 36)

        self.btn_min.clicked.connect(parent_window.showMinimized)
        self.btn_max.clicked.connect(parent_window.toggle_maximize)
        self.btn_close.clicked.connect(parent_window.close)

        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.title_label.setGeometry(0, 0, self.width(), self.height())

    def update_theme(self, theme):
        self.setStyleSheet("background-color: transparent;")
        self.title_label.setStyleSheet(
            f"font-weight:bold; background:transparent; color: {theme['title_text']};"
        )
        btn_style = Styles.TITLE_BTN.format(**theme)
        for b in self.buttons:
            b.setStyleSheet(btn_style)
        self.btn_close.setStyleSheet(btn_style + Styles.TITLE_BTN_CLOSE)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        top_resize_limit = self.parent_window.y() + self.parent_window.BORDER_WIDTH + 10
        if (
            event.globalPosition().y() < top_resize_limit
            and not self.parent_window.isMaximized()
        ):
            event.ignore()
            return

        if self.parent_window.windowHandle().startSystemMove():
            event.accept()

    def mouseDoubleClickEvent(self, event):
        top_resize_limit = self.parent_window.y() + self.parent_window.BORDER_WIDTH + 10
        if (
            event.button() == Qt.LeftButton
            and event.globalPosition().y() > top_resize_limit
        ):
            self.parent_window.toggle_maximize()
