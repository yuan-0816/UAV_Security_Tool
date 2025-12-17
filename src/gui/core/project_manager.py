import json
import os
import shutil
from datetime import datetime

from src.utils.tool import * 

class ProjectManager:
    def __init__(self):
        self.current_project_path = None  # 目前開啟的專案路徑
        self.project_data = {}            # 目前記憶體中的專案資料 (JSON內容)
        self.settings_filename = "project_settings.json" # 設定檔名稱

    def create_project(self, form_data: dict) -> tuple[bool, str]:
        """
        建立新專案
        :param form_data: 從 ProjectFormController 傳來的扁平字典
        :return: (bool, msg/path) -> (是否成功, 成功回傳路徑/失敗回傳錯誤訊息)
        """
        
        # 1. 取得基本路徑與專案名稱
        raw_base_path = form_data.get("save_path")
        project_name = form_data.get("project_name")
        
        if not raw_base_path or not project_name:
            return False, "缺少儲存路徑或專案名稱"

        base_path = os.path.abspath(os.path.expanduser(raw_base_path))

        # 2. 組合預期路徑
        target_folder = os.path.join(base_path, project_name)

        # print(f"目標資料夾: {target_folder}")

        # 3. 處理資料夾名稱重複 (保留您的邏輯)
        final_path = target_folder
        if check_folder_exists(final_path):
            i = 1
            while True:
                new_path = f"{target_folder}_{i}"
                if not check_folder_exists(new_path):
                    final_path = new_path
                    break
                i += 1
        
        # 如果因為重複而改名了，要把真實的名稱更新回資料裡，以免混淆
        actual_project_name = os.path.basename(final_path)
        form_data['project_name'] = actual_project_name

        # 4. 【關鍵】建構巢狀 JSON 結構
        # 我們將表單資料放入 'info'，並預留 'tests' 給檢測結果用
        self.project_data = {
            "version": "1.0",
            "info": form_data,  # 這裡放 UI 表單的輸入
            "tests": {}         # 這裡放未來的檢測結果 (6.2.1, 6.2.2...)
        }

        try:
            # 5. 建立實體資料夾
            os.makedirs(final_path, exist_ok=True)
            
            # (選用) 建立圖片資料夾，方便之後存截圖
            os.makedirs(os.path.join(final_path, "images"), exist_ok=True)

            # 6. 存檔
            self.current_project_path = final_path
            self.save_all()

            return True, final_path

        except OSError as e:
            return False, f"建立資料夾失敗: {e}"
        except Exception as e:
            return False, f"未預期的錯誤: {e}"

    def load_project(self, folder_path: str) -> tuple[bool, str]:
        """
        讀取舊專案
        """
        json_path = os.path.join(folder_path, self.settings_filename)
        
        if not os.path.exists(json_path):
            return False, "找不到專案設定檔 (project_settings.json)"
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.project_data = json.load(f)
            
            self.current_project_path = folder_path
            return True, "讀取成功"
            
        except Exception as e:
            return False, f"讀取失敗: {e}"

    def update_info(self, new_info: dict):
        """
        更新專案基本資料 (由 ProjectFormController 編輯模式呼叫)
        只更新 'info' 區塊，不動 'tests'
        """
        if not self.current_project_path:
            return False, "未開啟專案"

        # 更新記憶體資料
        if "info" not in self.project_data:
            self.project_data["info"] = {}
            
        self.project_data["info"].update(new_info)
        
        # 寫回硬碟
        return self.save_all()

    def update_test_result(self, test_id: str, result_data: dict):
        """
        更新特定測項結果 (由檢測頁面呼叫)
        :param test_id: 例如 "6.2.1"
        """
        if "tests" not in self.project_data:
            self.project_data["tests"] = {}
            
        if test_id not in self.project_data["tests"]:
            self.project_data["tests"][test_id] = {}
            
        # 更新該測項
        self.project_data["tests"][test_id].update(result_data)
        
        # 自動壓上最後更新時間
        self.project_data["tests"][test_id]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.save_all()

    def save_all(self):
        """內部 helper: 將記憶體中的 project_data 寫入 JSON"""
        if not self.current_project_path:
            return False, "無路徑"
            
        json_path = os.path.join(self.current_project_path, self.settings_filename)
        
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.project_data, f, ensure_ascii=False, indent=4)
            return True, "儲存成功"
        except Exception as e:
            return False, str(e)
        

if __name__ == "__main__":
    # 測試區塊
    pm = ProjectManager()
    success, msg = pm.create_project({
        "save_path": "~/Desktop",
        "project_name": "MyDroneTest",
        "report_id": "Rpt-123",
        "tester": "Alice",
        "date": "2024-06-15"
    })
    print("Create Project:", success, msg)