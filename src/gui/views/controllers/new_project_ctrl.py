'''
載入 new_project.ui，處理 OK/Cancel，並把使用者輸入的東西打包回傳
'''
import os

from PySide6.QtWidgets import QDialog, QLineEdit, QDateEdit,  QDialogButtonBox, QCheckBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QDate

from utils.tool import get_project_root


class NewProjectController:
    def __init__(self):
        
        self.loader = QUiLoader()
        ui_path = os.path.join(get_project_root(), "src", "gui", "views", "new_project.ui")
        ui_file = QFile(str(ui_path))
        ui_file.open(QFile.ReadOnly)
        self.dialog = self.loader.load(ui_file)
        ui_file.close()

        
        self.input_id = self.dialog.findChild(QLineEdit, "lineEdit_ReportId") # 報告編號
        self.input_tester = self.dialog.findChild(QLineEdit, "lineEdit_Tester") # 檢測人員
        self.input_date = self.dialog.findChild(QDateEdit,  "dateEdit_StartDate")   # 日期
        if self.input_date:
            self.input_date.setDate(QDate.currentDate())
        
        self.chk_6 = self.dialog.findChild(QCheckBox, "checkBox_6") 
        self.chk_7 = self.dialog.findChild(QCheckBox, "checkBox_7")
        self.chk_81 = self.dialog.findChild(QCheckBox, "checkBox_81")
        self.chk_82 = self.dialog.findChild(QCheckBox, "checkBox_82")


        self.button_box = self.dialog.findChild(QDialogButtonBox, "buttonBox") # 下方的 OK/Cancel

        # 3. 連接信號
        # QDialogButtonBox 自動處理 accept/reject
        self.button_box.accepted.connect(self.dialog.accept)
        self.button_box.rejected.connect(self.dialog.reject)

        print(f"Debug: input_date found? {self.input_date is not None}")

    def run(self):
        """顯示對話框 (Modal)，並回傳結果"""
        result = self.dialog.exec() # 卡在這裡等待使用者操作
        
        if result == QDialog.Accepted:
            return self.get_data() # 如果按 OK，回傳資料
        else:
            return None # 如果按 Cancel，回傳 None

    def get_data(self):
            """收集所有輸入框的資料打包成字典"""
            
            # 防止有人沒填日期導致崩潰
            date_str = ""
            if self.input_date:
                date_str = self.input_date.date().toString("yyyy-MM-dd")
            
            # 收集資料
            data = {
                "report_id": self.input_id.text() if self.input_id else "",
                "tester": self.input_tester.text() if self.input_tester else "",
                "date": date_str,
                
                # --- 【新增】取得 CheckBox 狀態 (True/False) ---
                "enable_6": self.chk_6.isChecked() if self.chk_6 else False,
                "enable_7": self.chk_7.isChecked() if self.chk_7 else False,
                "enable_81": self.chk_81.isChecked() if self.chk_81 else False,
                "enable_82": self.chk_82.isChecked() if self.chk_82 else False,
            }
            return data
    

if __name__ == "__main__":
    # 測試用
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    controller = NewProjectController()
    data = controller.run()
    if data:
        print("使用者輸入的資料：", data)
    else:
        print("使用者取消了對話框")