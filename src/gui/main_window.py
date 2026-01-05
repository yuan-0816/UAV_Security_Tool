#!/usr/bin/env python3
"""
GUI 應用程式入口點
執行此檔案啟動應用程式

使用方式:
    cd src/gui && python main_window.py
"""

import sys
import os

# 確保可以從 src/gui 目錄直接執行
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QPalette, QColor

# 從新模組匯入
from windows.main_app import MainApp

# 從新模組匯入設定管理器
from core.config_manager import ConfigManager
from constants import CONFIG_DIR


def create_light_theme_palette() -> QPalette:
    """建立亮色主題 Palette"""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#FFFFFF"))
    palette.setColor(QPalette.WindowText, QColor("#000000"))
    palette.setColor(QPalette.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.AlternateBase, QColor("#F0F0F0"))
    palette.setColor(QPalette.ToolTipBase, QColor("#FFFFDC"))
    palette.setColor(QPalette.ToolTipText, QColor("#000000"))
    palette.setColor(QPalette.Text, QColor("#000000"))
    palette.setColor(QPalette.Button, QColor("#F0F0F0"))
    palette.setColor(QPalette.ButtonText, QColor("#000000"))
    palette.setColor(QPalette.BrightText, QColor("#FF0000"))
    palette.setColor(QPalette.Link, QColor("#0000FF"))
    palette.setColor(QPalette.Highlight, QColor("#2196F3"))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    return palette


def get_global_stylesheet() -> str:
    """取得全域樣式表"""
    font_family = '"Microsoft JhengHei", "Segoe UI", sans-serif'
    return f"""
        QWidget {{ 
            font-family: {font_family}; 
            font-size: 10pt; 
            color: #000000;
        }}
        QWidget:window {{
            background-color: #FFFFFF;
        }}
        QToolTip {{ 
            color: #000000; 
            background-color: #FFFFDC; 
            border: 1px solid black; 
        }}
    """


def main():
    """應用程式入口點"""
    # 建立 QApplication
    app = QApplication(sys.argv)

    # 使用 Fusion 風格以獲得跨平台一致外觀
    app.setStyle("Fusion")

    # 套用亮色主題
    app.setPalette(create_light_theme_palette())
    app.setStyleSheet(get_global_stylesheet())

    # 初始化設定管理器
    config_mgr = ConfigManager(config_dir=CONFIG_DIR)

    # 檢查設定檔
    if not config_mgr.list_available_configs():
        QMessageBox.warning(
            None, "警告", "未偵測到設定檔，請將 json 放入 configs 資料夾"
        )

    # 建立並顯示主視窗
    window = MainApp(config_mgr)
    window.show()

    # 開始事件迴圈
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
