import os

from PySide6.QtWidgets import (
    QStackedWidget, QPushButton, QDialog, QLineEdit, QDateEdit, QDialogButtonBox, QCheckBox, QMessageBox, QTextBrowser
)
from PySide6.QtCore import QFile, QObject
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QAction


# 匯入子頁面的 Controller
from gui.views.controllers.project_form_ctrl import ProjectFormController

from gui.views.controllers.widget_621_ctrl import Page621Controller


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
        
        self.project_manager = ProjectManager()

        # ----------------------------------- 主視窗元件 ---------------------------------- #
        # menubar
        self.action_create = self.window.findChild(QAction, "action_create")
        if self.action_create:
            self.action_create.triggered.connect(self.create_new_project)

        self.action_open = self.window.findChild(QAction, "action_open")
        if self.action_open:
            self.action_open.triggered.connect(self.open_project)


        # tab overview
        self.textBrowser_info = self.window.findChild(QTextBrowser, "textBrowser_info")


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


        if self.btn_621:
            self.btn_621.clicked.connect(self.switch_to_621)

    
    def create_new_project(self):
        """按下 [新建專案] 後的邏輯"""
        
        # 1. 實例化對話框控制器 (傳入 self.window 當父視窗，確保置中)
        dialog_controller = ProjectFormController(parent=self.window)
        
        # 2. 執行並等待結果 (Blocking)
        # 這裡拿到的 data 是一個單純的 dict，包含所有表單資料
        form_data = dialog_controller.run()
        
        # 3. 判斷結果
        if form_data:
            print(f"使用者輸入資料: {form_data}")

            # 【修改 2】呼叫 ProjectManager 的新介面
            # create_project 現在回傳 (bool, str)
            success, result = self.project_manager.create_project(form_data)

            if success:
                project_path = result
                QMessageBox.information(self.window, "成功", f"專案已建立於：\n{project_path}")
                
                # 4. 更新主畫面資訊 (顯示漂亮的排版)
                self.update_project_info_display(form_data)
                
                # (選用) 更新視窗標題
                self.window.setWindowTitle(f"無人機檢測工具 - {form_data.get('project_name')}")
            else:
                error_msg = result
                QMessageBox.warning(self.window, "建立失敗", f"無法建立專案：{error_msg}")


    def update_project_info_display(self, info_data: dict):
        """
        【修改 3】將專案資訊格式化為漂亮的 HTML 並顯示在 textBrowser
        """
        if not self.textBrowser_info:
            return

        # 定義欄位名稱對照 (讓顯示更人性化)
        field_map = {
            "project_name": "專案名稱",
            "report_id": "報告編號",
            "tester": "檢測人員",
            "date": "檢測日期",
            "save_path": "儲存路徑",
            "enable_6": "6. 系統檢測",
            "enable_7": "7. 群飛系統安全檢測",
            "enable_81": "8.1 一般要求增項",
            "enable_82": "8.2 特殊要求增項"
        }

        # 組合 HTML 表格
        html = """
        <style>
            h3 { color: #2c3e50; }
            table { border-collapse: collapse; width: 100%; }
            td, th { border: 1px solid #dddddd; text-align: left; padding: 8px; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            .label { font-weight: bold; color: #555; width: 30%; }
            .value { color: #000; }
        </style>
        <h3>當前專案資訊</h3>
        <table>
        """

        # 1. 先顯示一般文字資訊
        for key, value in info_data.items():
            # 跳過 checkbox 的 boolean 值，稍後處理，或是只顯示文字類的
            if key.startswith("enable_"):
                continue
            
            display_name = field_map.get(key, key) # 如果字典裡沒有就顯示原文
            html += f"<tr><td class='label'>{display_name}</td><td class='value'>{value}</td></tr>"

        html += "</table><br><h3>檢測項目啟用狀態</h3><ul>"

        # 2. 顯示 Checkbox 狀態 (用列表顯示)
        for key, value in info_data.items():
            if key.startswith("enable_"):
                display_name = field_map.get(key, key)
                status = "<span style='color:green'>啟用</span>" if value else "<span style='color:gray'>未啟用</span>"
                html += f"<li><b>{display_name}:</b> {status}</li>"

        html += "</ul>"

        # 設定到 TextBrowser (支援 HTML)
        self.textBrowser_info.setHtml(html)

    # TODO: open project method
    def open_project(self):
        pass


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