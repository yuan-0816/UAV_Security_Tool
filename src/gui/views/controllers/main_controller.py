import os

from PySide6.QtWidgets import (
    QStackedWidget, QPushButton, QDialog, QLineEdit, QDateEdit, QDialogButtonBox, QCheckBox, QMessageBox
)
from PySide6.QtCore import QFile, QObject
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QAction


# 匯入子頁面的 Controller
from gui.views.controllers.page_621 import Page621Controller

from gui.core.project_manager import ProjectManager

from utils.tool import get_project_root

class MainController(QObject):
    def __init__(self):
        super().__init__()
        
        self.views_path = os.path.join(get_project_root(), "src", "gui", "views")
        
        # 1. 載入主視窗 UI
        self.window = self.load_ui("mainGUI.ui")
        if not self.window:
            raise RuntimeError("無法載入 mainGUI.ui")

        # ----------------------------------- 主視窗元件 ---------------------------------- #
        # tab overview
        self.action_create = self.window.findChild(QAction, "action_create")



        # tab 6
        self.stacked_widget = self.window.findChild(QStackedWidget, "stackedWidget")
        self.btn_621 = self.window.findChild(QPushButton, "btn_621")

        # tab 7

        # tab 81

        # tab 82

        # TODO: 要檢查很多
        if not self.stacked_widget or not self.btn_621:
            print("警告：主視窗找不到 stackedWidget 或 btn_621，請檢查 UI 檔 ObjectName")

        # 3. 初始化儲存空間
        self.controllers = {}   # 用來存活著的 controller
        self.loaded_pages = {}  # 用來存已經載入的 widget (懶加載用)

        # ---------------------------------- 連接主選單按鈕 --------------------------------- #
        # tab overview
        if self.action_create:
            self.action_create.triggered.connect(self.open_new_project)




        if self.btn_621:
            self.btn_621.clicked.connect(self.switch_to_621)
    
    def open_new_project(self):
        """按下 [新建專案] 後的邏輯"""
        # 1. 實例化對話框控制器
        dialog_controller = NewProjectController()
        
        # 2. 執行並等待結果 (Blocking)
        data = dialog_controller.run()
        
        # 3. 判斷結果
        if data:
            print(f"使用者輸入資料: {data}")
            
            # 4. 呼叫 Model 存檔
            if self.project_manager.save_project(data):
                QMessageBox.information(self.window, "成功", "專案已建立並儲存！")
                
                # 5. 更新主畫面
                self.update_main_ui(data)
            else:
                QMessageBox.warning(self.window, "錯誤", "存檔失敗！")

    def load_ui(self, filename):
        """通用的 UI 載入器"""
        ui_file_path = os.path.join(self.views_path, filename)
        ui_file = QFile(str(ui_file_path))
        
        if not ui_file.open(QFile.ReadOnly):
            print(f"錯誤：找不到檔案 {ui_file_path}")
            return None
            
        loader = QUiLoader()
        widget = loader.load(ui_file)
        ui_file.close()
        return widget

    def switch_to_621(self):
        """切換到 6.2.1 頁面 (懶加載模式)"""
        page_id = "621"

        # 如果已經載入過，直接切換，不重新讀檔
        if page_id in self.loaded_pages:
            self.stacked_widget.setCurrentWidget(self.loaded_pages[page_id])
            print("切換至已快取的 6.2.1 頁面")
            return

        print("正在首次載入 6.2.1...")
        # 1. 載入子 UI
        widget = self.load_ui("widget_621.ui")
        if not widget:
            return

        # 2. 建立專屬 Controller (這時候才把 widget 交給它管)
        controller = Page621Controller(widget)
        
        # 3. 重要！存入字典防止被垃圾回收 (Garbage Collection)
        self.controllers[page_id] = controller
        self.loaded_pages[page_id] = widget

        # 4. 放入介面並顯示
        self.stacked_widget.addWidget(widget)
        self.stacked_widget.setCurrentWidget(widget)

    def show(self):
        """顯示主視窗"""
        self.window.show()