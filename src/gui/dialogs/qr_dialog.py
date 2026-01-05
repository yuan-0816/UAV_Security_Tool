"""
QR Code 對話框模組
"""

from io import BytesIO
import qrcode

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QApplication,
    QMessageBox,
)


class QRCodeDialog(QDialog):
    """手機掃碼上傳對話框"""

    def __init__(self, parent, pm, url, title="手機掃碼上傳"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 500)
        self.pm = pm
        self.url = url
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        lbl_hint = QLabel("請使用手機掃描下方 QR Code\n(需連接同一 Wi-Fi)")
        lbl_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_hint)

        qr_lbl = QLabel()
        qr_lbl.setAlignment(Qt.AlignCenter)

        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(self.url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qimg = QImage.fromData(buffer.getvalue())

        qr_lbl.setPixmap(QPixmap.fromImage(qimg).scaled(300, 300, Qt.KeepAspectRatio))
        layout.addWidget(qr_lbl)

        link_layout = QHBoxLayout()
        self.link_edit = QLineEdit(self.url)
        self.link_edit.setReadOnly(True)
        btn_copy = QPushButton("複製連結")
        btn_copy.clicked.connect(self.copy_link)

        link_layout.addWidget(self.link_edit)
        link_layout.addWidget(btn_copy)
        layout.addLayout(link_layout)

        btn_close = QPushButton("關閉 (停止伺服器)")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

    def copy_link(self):
        cb = QApplication.clipboard()
        cb.setText(self.url)
        QMessageBox.information(self, "複製成功", "網址已複製到剪貼簿")

    def closeEvent(self, event):
        self.pm.stop_server()
        event.accept()
