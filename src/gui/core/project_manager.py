import json
import os
from utils.tool import get_project_root

class ProjectManager:
    def __init__(self, dict_data:dict=None):


        if not dict_data:
            return
        
        self.dict_data = dict_data if dict_data else {}

        self.filepath = os.path.join(dict_data.get("save_path", "default_project.json")) if dict_data else os.path.join(get_project_root(), "default_project.json")
        
        # self.filepath = os.path.join(get_project_root(), filename)
        

    def save_project(self, data: dict):
        """將資料寫入 JSON 檔案"""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"存檔失敗: {e}")
            return False

    def load_project(self):
        """讀取 JSON 檔案"""
        if not self.filepath.exists():
            return None
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"讀檔失敗: {e}")
            return None