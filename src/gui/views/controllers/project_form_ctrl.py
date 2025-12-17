import os
import logging

from PySide6.QtWidgets import (QDialog, QLineEdit, QDateEdit, QDialogButtonBox, 
                               QCheckBox, QToolButton, QWidget, QPlainTextEdit, QComboBox)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QDate

from gui.core.utils import *
from utils.tool import *

# --- Logging 設定 ---
DEBUG_MODE = True
LOG_LEVEL = logging.DEBUG if DEBUG_MODE else logging.ERROR

logging.basicConfig(
    level=LOG_LEVEL,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger("project_form_ctrl")

class ProjectFormController:
    def __init__(self, parent=None, existing_data=None):
        """
        初始化專案表單對話框
        :param parent: 父視窗
        :param existing_data: 整包專案資料 (包含 info, tests 等)。
                              如果是新建模式則為 None。
        """ 
        self.base_folder = os.path.expanduser("~")
        
        # 1. 載入 UI
        self.loader = QUiLoader()
        ui_path = os.path.join(get_project_root(), "src", "gui", "views", "project_form.ui")
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QFile.ReadOnly):
            logger.error(f"無法開啟 UI 檔案: {ui_path}")
            return
        
        self.dialog = self.loader.load(ui_file, parent)
        ui_file.close()

        # 2. 設定模式 (新建 vs 編輯)
        self.existing_data = existing_data
        self.is_edit_mode = existing_data is not None

        if self.is_edit_mode:
            self.dialog.setWindowTitle("編輯專案")
        else:
            self.dialog.setWindowTitle("新建專案")

        # 3. 綁定特殊邏輯元件 
        # (只有需要處理信號/互動的元件才需要手動 findChild，其他的靠自動化處理)
        
        # [專案名稱] 需要連動路徑，所以要抓出來
        self.input_project_name = self.dialog.findChild(QLineEdit, "lineEdit_ProjectName")
        if self.input_project_name:
            self.input_project_name.textChanged.connect(self.update_save_path)

        # [儲存路徑] 需要按鈕瀏覽，所以要抓出來
        self.input_SavePath = self.dialog.findChild(QLineEdit, "lineEdit_SavePath")
        self.toolButton_SavePath = self.dialog.findChild(QToolButton, "toolButton_SavePath")
        if self.toolButton_SavePath:
            self.toolButton_SavePath.clicked.connect(self.browse_save_path)

        # [按鈕盒] 處理 OK / Cancel
        self.button_box = self.dialog.findChild(QDialogButtonBox, "buttonBox")
        if self.button_box:
            self.button_box.accepted.connect(self.check_input_and_accept)
            self.button_box.rejected.connect(self.dialog.reject)

        # 4. 初始化資料填入邏輯
        if not self.is_edit_mode:
            # === 新建模式：設定預設值 ===
            date_edit = self.dialog.findChild(QDateEdit, "dateEdit_StartDate")
            if date_edit:
                date_edit.setDate(QDate.currentDate())
            
            if self.input_SavePath:
                self.input_SavePath.setText(self.base_folder)
            
        else:
            # === 編輯模式：回填資料 ===
            # 假設 ProjectForm 只負責編輯 "info" 區塊
            info_data = self.existing_data.get("info", {})
            self.load_from_dict(info_data)
            
            # 編輯模式下，鎖定關鍵欄位防止資料錯亂
            if self.input_SavePath: 
                self.input_SavePath.setReadOnly(True) 
            if self.toolButton_SavePath: 
                self.toolButton_SavePath.setEnabled(False) 
            if self.input_project_name: 
                self.input_project_name.setReadOnly(True)


    # --------------------------- 自動化讀寫 (Auto-Mapping) --------------------------- #
    def dump_to_dict(self) -> dict:
        """
        掃描所有 UI 元件，根據 json_key 屬性打包成字典
        """
        data = {}
        all_widgets = self.dialog.findChildren(QWidget)

        for widget in all_widgets:
            # 獲取在 Qt Designer 設定的 'json_key'
            key = widget.property("json_key")
            
            if not key:
                continue

            # 根據元件類型取出值
            if isinstance(widget, QLineEdit):
                data[key] = widget.text().strip()
            
            elif isinstance(widget, QCheckBox):
                data[key] = widget.isChecked()
            
            elif isinstance(widget, QDateEdit):
                data[key] = widget.date().toString("yyyy-MM-dd")
                
            elif isinstance(widget, QPlainTextEdit):
                data[key] = widget.toPlainText()
            
            elif isinstance(widget, QComboBox):
                data[key] = widget.currentText()

        logger.debug(f"打包後的資料: {data}")
        return data

    def load_from_dict(self, data: dict):
        """
        根據 json_key 自動將 data 的值填回 UI
        """
        all_widgets = self.dialog.findChildren(QWidget)

        for widget in all_widgets:
            key = widget.property("json_key")
            
            # 如果沒 Key 或資料裡沒這個 Key，就跳過
            if not key or key not in data:
                continue

            value = data[key]

            # 根據元件類型填入值
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            
            elif isinstance(widget, QDateEdit):
                qdate = QDate.fromString(str(value), "yyyy-MM-dd")
                widget.setDate(qdate)
                
            elif isinstance(widget, QPlainTextEdit):
                widget.setPlainText(str(value))
                
            elif isinstance(widget, QComboBox):
                idx = widget.findText(str(value))
                if idx >= 0: widget.setCurrentIndex(idx)

    def get_data(self):
        """
        取得最終表單資料 (給外部呼叫用)
        """
        return self.dump_to_dict()



    def check_input_and_accept(self):
        """
        通用檢查：掃描所有設定了 property("required") == True 的元件
        """
        # 搜尋所有可能的輸入元件
        all_widgets = self.dialog.findChildren(QWidget)
        has_error = False

        for widget in all_widgets:
            # 檢查是否有被標記為 'required'
            if widget.property("required"):
                
                # 取得值 (針對不同元件取值方式不同，這裡主要針對文字框)
                text_value = ""
                if isinstance(widget, QLineEdit):
                    text_value = widget.text().strip()
                elif isinstance(widget, QPlainTextEdit):
                    text_value = widget.toPlainText().strip()
                
                # 驗證
                if not text_value:
                    # 必填但為空 -> 變紅
                    widget.setStyleSheet("border: 1px solid red;")
                    has_error = True
                else:
                    # 有值 -> 恢復原狀
                    widget.setStyleSheet("")
        
        if has_error:
            show_error_message(parent=self.dialog, message="請檢查所有標示為紅色的必填欄位。")
            return

        self.dialog.accept()

    def update_save_path(self):
        """(僅新建模式) 根據專案名稱自動更新預設儲存路徑"""
        if not self.input_project_name or not self.input_SavePath:
            return

        project_name = self.input_project_name.text().strip()
        if project_name:
            new_path = os.path.join(self.base_folder, project_name)
        else:
            new_path = self.base_folder
        
        self.input_SavePath.setText(new_path)

    def browse_save_path(self):
        """瀏覽資料夾"""
        folder = select_folder(parent=self.dialog, title="選擇專案儲存資料夾")
        if folder:
            self.base_folder = folder
            self.update_save_path()

    def run(self):
        """顯示對話框 (Modal)，並回傳結果"""
        result = self.dialog.exec()
        
        if result == QDialog.Accepted:
            return self.get_data()
        else:
            return None

# --- 測試區塊 ---
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    # 模擬測試：傳入假資料模擬編輯模式
    fake_data = {
        "info": {
            "project_name": "TestProject",
            "report_id": "Rpt-001",
            "tester": "Admin",
            "date": "2023-12-25",
            
            "test_7": True,
        }
    }
    controller = ProjectFormController(existing_data=fake_data)
    
    # 正常測試：新建模式
    # controller = ProjectFormController()
    
    data = controller.run()
    # if data:
    #     print("使用者輸入的資料：", data)
    # else:
    #     print("使用者取消了對話框")