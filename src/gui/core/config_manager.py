"""
規範設定管理模組
"""

import os
import json
from typing import Dict, List, Optional

from constants import CONFIG_DIR


class ConfigManager:
    """規範設定管理器 - 負責載入和驗證規範設定檔"""

    def __init__(self, config_dir=CONFIG_DIR):
        self.config_dir = config_dir
        self._ensure_dir()

    def _ensure_dir(self):
        if not os.path.exists(self.config_dir):
            try:
                os.makedirs(self.config_dir)
            except OSError as e:
                print(f"Error creating config dir: {e}")

    def list_available_configs(self) -> List[Dict[str, str]]:
        configs = []
        if not os.path.exists(self.config_dir):
            return configs
        for filename in os.listdir(self.config_dir):
            if filename.endswith(".json"):
                full_path = os.path.join(self.config_dir, filename)
                display_name = filename
                try:
                    with open(full_path, "r", encoding="utf-8-sig") as f:
                        data = json.load(f)
                        if "standard_name" in data:
                            display_name = data["standard_name"]
                        elif "standard_version" in data:
                            display_name = (
                                f"規範版本 {data['standard_version']} ({filename})"
                            )
                except Exception as e:
                    display_name = f"{filename} (讀取錯誤)"
                configs.append({"name": display_name, "path": full_path})
        configs.sort(key=lambda x: x["name"], reverse=True)
        return configs

    def _validate_config_integrity(self, data: Dict, filename: str):
        if "test_standards" not in data:
            raise ValueError(f"檔案 {filename} 格式錯誤：缺少 'test_standards' 欄位")
        for section in data.get("test_standards", []):
            sec_id = section.get("section_id", "Unknown")
            for item in section.get("items", []):
                item_id = item.get("id", "Unknown ID")
                if "uid" not in item or not item["uid"]:
                    raise ValueError(
                        f"規範完整性檢查失敗！\n檔案: {filename}\n位置: Section {sec_id} -> Item {item_id}\n原因: 缺少必要的 'uid' 欄位。\n無法載入不含 UID 的規範。"
                    )

    def load_config(self, path: str) -> Dict:
        filename = os.path.basename(path)
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            self._validate_config_integrity(data, filename)
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"檔案 {filename} 不是有效的 JSON 格式")
        except Exception as e:
            print(f"Loading config failed: {e}")
            raise e

    def find_config_by_name(self, target_name: str) -> Optional[Dict]:
        configs = self.list_available_configs()
        for cfg in configs:
            if cfg["name"] == target_name:
                try:
                    return self.load_config(cfg["path"])
                except:
                    return None
        return None

    def get_latest_config(self) -> Optional[Dict]:
        """取得列表中的第一個（最新）規範設定"""
        configs = self.list_available_configs()
        if configs:
            try:
                return self.load_config(configs[0]["path"])
            except:
                return None
        return None
