import os
from PySide6.QtWidgets import QFileDialog



def select_folder(parent=None, title="選擇資料夾", initial_path=os.path.expanduser("~")) -> str:
    """
    開啟資料夾選擇對話框，並回傳選擇的路徑
    :param parernt: 對話框的父視窗
    :param title: 對話框標題
    :param initial_path: 初始路徑
    :return: 選擇的資料夾路徑，若取消則回傳 None
    """

    if initial_path is None:
        initial_path = os.path.expanduser("~")

    folder = QFileDialog.getExistingDirectory(
            parent,
            title,
            initial_path
        )
        
    return folder


def show_error_message(parent=None, title="錯誤", message=""):
    from PySide6.QtWidgets import QMessageBox
    
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec() # 顯示並等待使用者關閉