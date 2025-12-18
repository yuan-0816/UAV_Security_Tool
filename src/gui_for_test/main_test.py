import sys
import json
import os
import shutil
from datetime import datetime
from functools import partial

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QStackedWidget, QMessageBox, QLabel, QDialog, QFormLayout, 
    QLineEdit, QDateEdit, QToolButton, QDialogButtonBox, QFileDialog, 
    QTextEdit, QGroupBox, QCheckBox, QProgressBar, QFrame, QScrollArea,
    QComboBox, QSizePolicy, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QDate, QObject, Signal
from PySide6.QtGui import QPixmap

# ==========================================
# 1. 專案管理器 (Model & Logic Core)
# ==========================================
class ProjectManager(QObject): 
    data_changed = Signal()

    def __init__(self):
        super().__init__()
        self.current_project_path = None
        self.project_data = {}
        self.settings_filename = "project_settings.json"
        self.std_config = {} # 儲存標準設定檔，用於邏輯判斷

    def set_standard_config(self, config):
        """注入標準設定檔，讓 Manager 能進行範圍判斷"""
        self.std_config = config

    # --- 核心邏輯：範圍與可見性判斷 (Logic Separation) ---
    def get_current_project_type(self):
        return self.project_data.get("info", {}).get("project_type", "full")

    def is_item_visible(self, item_id):
        """判斷某個測項 ID 在當前專案中是否應該顯示"""
        if not self.current_project_path: return False
        
        info = self.project_data.get("info", {})
        p_type = info.get("project_type", "full")

        if p_type == "ad_hoc":
            # Ad-Hoc 模式：只顯示白名單內的項目
            whitelist = info.get("target_items", [])
            return item_id in whitelist
        else:
            # 完整模式：檢查該項目所屬的 Section 是否在 Scope 中
            # 這裡需要反查 Item ID 屬於哪個 Section (透過 std_config)
            scope = info.get("test_scope", [])
            # 兼容舊版：若無 scope 則預設全開
            if not scope and "test_scope" not in info: return True 
            
            section_id = self._find_section_id_by_item(item_id)
            return section_id in scope

    def is_section_visible(self, section_id):
        """判斷某個章節是否應該顯示"""
        if not self.current_project_path: return False
        
        info = self.project_data.get("info", {})
        p_type = info.get("project_type", "full")

        if p_type == "ad_hoc":
            # Ad-Hoc 模式：若該章節下有任何一個 Item 在白名單內，該章節就要顯示
            whitelist = info.get("target_items", [])
            section_items = self._get_items_in_section(section_id)
            return any(item['id'] in whitelist for item in section_items)
        else:
            # 完整模式：直接檢查 Scope
            scope = info.get("test_scope", [])
            if not scope and "test_scope" not in info: return True
            return str(section_id) in scope

    def _find_section_id_by_item(self, item_id):
        """輔助：從設定檔反查 Section ID"""
        for sec in self.std_config.get("test_standards", []):
            for item in sec['items']:
                if item['id'] == item_id:
                    return str(sec['section_id'])
        return ""

    def _get_items_in_section(self, section_id):
        """輔助：取得某章節下的所有 Item 定義"""
        for sec in self.std_config.get("test_standards", []):
            if str(sec['section_id']) == str(section_id):
                return sec['items']
        return []

    # --- 1.1 建立完整專案 ---
    def create_project(self, form_data: dict) -> tuple[bool, str]:
        raw_base_path = form_data.get("save_path")
        project_name = form_data.get("project_name")
        
        if not raw_base_path or not project_name:
            return False, "缺少儲存路徑或專案名稱"

        base_path = os.path.abspath(os.path.expanduser(raw_base_path))
        target_folder = os.path.join(base_path, project_name)
        final_path = self._get_unique_path(target_folder)
        
        # 標記為完整專案
        form_data['project_name'] = os.path.basename(final_path)
        form_data['project_type'] = "full" 

        self.project_data = {
            "version": "2.0",
            "info": form_data,
            "tests": {} 
        }

        return self._init_folder_and_save(final_path)

    # --- 1.2 建立各別檢測專案 (Ad-Hoc) ---
    def create_ad_hoc_project(self, selected_items: list, save_base_path: str) -> tuple[bool, str]:
        ts_str = datetime.now().strftime("%Y%m%d_%H%M")
        folder_name = f"QuickTest_{ts_str}"
        target_folder = os.path.join(save_base_path, folder_name)
        final_path = self._get_unique_path(target_folder)

        # 構造 Info
        info_data = {
            "project_name": os.path.basename(final_path),
            "project_type": "ad_hoc", # 關鍵標記
            "report_id": f"ADHOC-{ts_str}",
            "tester": "QuickUser",
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "target_items": selected_items, # 記錄這個資料夾只負責測這些項目
            "test_scope": [] # Ad-hoc 不需要 scope，由 target_items 決定
        }

        self.project_data = {
            "version": "2.0",
            "info": info_data,
            "tests": {}
        }

        return self._init_folder_and_save(final_path)

    def _get_unique_path(self, target_folder):
        final_path = target_folder
        if os.path.exists(final_path):
            i = 1
            while True:
                new_path = f"{target_folder}_{i}"
                if not os.path.exists(new_path):
                    final_path = new_path; break
                i += 1
        return final_path

    def _init_folder_and_save(self, path):
        try:
            os.makedirs(path, exist_ok=True)
            os.makedirs(os.path.join(path, "images"), exist_ok=True)
            os.makedirs(os.path.join(path, "reports"), exist_ok=True)
            
            self.current_project_path = path
            self.save_all()
            return True, path
        except Exception as e:
            return False, str(e)

    def load_project(self, folder_path: str) -> tuple[bool, str]:
        json_path = os.path.join(folder_path, self.settings_filename)
        if not os.path.exists(json_path): return False, "找不到專案設定檔"
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.project_data = json.load(f)
            self.current_project_path = folder_path
            self.data_changed.emit()
            return True, "讀取成功"
        except Exception as e:
            return False, f"讀取失敗: {e}"

    # --- 1.3 檔案匯入 ---
    def import_file(self, src_path: str, sub_folder: str = "images") -> str:
        if not self.current_project_path: return None
        try:
            filename = os.path.basename(src_path)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{ts}_{filename}"
            
            target_dir = os.path.join(self.current_project_path, sub_folder)
            if not os.path.exists(target_dir): os.makedirs(target_dir)
            
            dest_path = os.path.join(target_dir, new_filename)
            shutil.copy2(src_path, dest_path)
            
            return f"{sub_folder}/{new_filename}"
        except Exception as e:
            print(f"複製檔案失敗: {e}")
            return None

    # --- 1.4 合併外部專案 ---
    def merge_external_project(self, source_folder: str) -> tuple[bool, str]:
        if not self.current_project_path: return False, "請先開啟主專案"
        
        # 邏輯檢查：只有 Full 專案可以合併別人
        if self.get_current_project_type() != "full":
            return False, "目前開啟的不是完整專案，無法執行合併動作。"

        source_json_path = os.path.join(source_folder, self.settings_filename)
        if not os.path.exists(source_json_path): return False, "來源資料夾無效 (找不到設定檔)"

        try:
            with open(source_json_path, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
            
            src_info = source_data.get("info", {})
            if src_info.get("project_type") != "ad_hoc":
                return False, "錯誤：來源資料夾是一個「完整專案」，不允許合併！\n只能合併「各別檢測專案」。"

            # 搬移檔案
            for sub in ["images", "reports"]:
                src_sub_dir = os.path.join(source_folder, sub)
                if not os.path.exists(src_sub_dir): continue
                
                dest_sub_dir = os.path.join(self.current_project_path, sub)
                if not os.path.exists(dest_sub_dir): os.makedirs(dest_sub_dir)

                for filename in os.listdir(src_sub_dir):
                    s_file = os.path.join(src_sub_dir, filename)
                    d_file = os.path.join(dest_sub_dir, filename)
                    if os.path.exists(d_file):
                        d_file = os.path.join(dest_sub_dir, f"merged_{filename}")
                    
                    if os.path.isfile(s_file):
                        shutil.copy2(s_file, d_file)

            # 合併 Tests 資料
            source_tests = source_data.get("tests", {})
            current_tests = self.project_data.get("tests", {})
            
            merged_count = 0
            for test_id, targets_data in source_tests.items():
                if test_id not in current_tests:
                    current_tests[test_id] = {}
                
                for target, result_data in targets_data.items():
                    current_tests[test_id][target] = result_data
                    merged_count += 1
            
            self.save_all()
            self.data_changed.emit()
            return True, f"成功合併 {len(source_tests)} 個測項 ({merged_count} 筆資料)"

        except Exception as e:
            return False, f"合併失敗: {str(e)}"

    # --- 一般資料操作 ---
    def update_info(self, new_info):
        if not self.current_project_path: return False
        self.project_data.setdefault("info", {}).update(new_info)
        self.save_all(); self.data_changed.emit(); return True

    def update_test_result(self, test_id, target, result_data, is_shared=False):
        if "tests" not in self.project_data: self.project_data["tests"] = {}
        if test_id not in self.project_data["tests"]: self.project_data["tests"][test_id] = {}
        
        self.project_data["tests"][test_id][target] = result_data
        self.project_data["tests"][test_id][target]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.project_data["tests"][test_id].setdefault("__meta__", {})["is_shared"] = is_shared
        self.save_all(); self.data_changed.emit()

    def get_test_meta(self, test_id):
        return self.project_data.get("tests", {}).get(test_id, {}).get("__meta__", {})

    def save_all(self):
        if not self.current_project_path: return False, "No Path"
        path = os.path.join(self.current_project_path, self.settings_filename)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.project_data, f, ensure_ascii=False, indent=4)
            return True, "Saved"
        except Exception as e: return False, str(e)

    def get_test_status_detail(self, item_config):
        test_id = item_config['id']
        targets = item_config.get('targets', ["GCS"])
        item_data = self.project_data.get("tests", {}).get(test_id, {})
        status_map = {}
        for t in targets:
            if t not in item_data: status_map[t] = "未檢測"
            else:
                res = item_data[t].get("result", "未判定")
                if "未判定" in res: status_map[t] = "未檢測"
                elif "合格" in res and "不" not in res: status_map[t] = "Pass"
                elif "不合格" in res: status_map[t] = "Fail"
                elif "不適用" in res: status_map[t] = "N/A"
                else: status_map[t] = "Unknown"
        return status_map

    def is_test_fully_completed(self, item_config):
        test_id = item_config['id']
        targets = item_config.get('targets', ["GCS"])
        saved = self.project_data.get("tests", {}).get(test_id, {})
        for t in targets:
            if t not in saved: return False
            if "未判定" in saved[t].get("result", "未判定"): return False
        return True


# ==========================================
# 2. 各別檢測選擇器 (Quick Test Dialog) - 已修復
# ==========================================
class QuickTestSelector(QDialog):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.setWindowTitle("選擇檢測項目 (各別模式)")
        self.resize(400, 500)
        self.config = config
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("請勾選本次要進行檢測的項目："))
        self.list_widget = QListWidget()
        
        # 動態讀取 config 生成列表
        for section in self.config.get("test_standards", []):
            header = QListWidgetItem(f"--- {section['section_name']} ---")
            header.setFlags(Qt.NoItemFlags) 
            self.list_widget.addItem(header)
            for item in section['items']:
                li = QListWidgetItem(f"{item['id']} {item['name']}")
                li.setFlags(li.flags() | Qt.ItemIsUserCheckable)
                li.setCheckState(Qt.Unchecked)
                li.setData(Qt.UserRole, item['id'])
                self.list_widget.addItem(li)
        
        layout.addWidget(self.list_widget)
        
        # 路徑選擇
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(os.path.join(os.path.expanduser("~"), "Desktop"))
        btn_browse = QPushButton("...")
        btn_browse.clicked.connect(self._browse)
        path_layout.addWidget(QLabel("儲存位置:"))
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(btn_browse)
        layout.addLayout(path_layout)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if d: self.path_edit.setText(d)

    def get_data(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected, self.path_edit.text()

    def run(self):
        """標準化執行方法，類似 Controller"""
        if self.exec() == QDialog.Accepted:
            return self.get_data()
        return None, None


# ==========================================
# 3. 專案表單 (Project Form)
# ==========================================
class ProjectFormController:
    def __init__(self, parent_window, meta_schema, existing_data=None):
        self.meta_schema = meta_schema
        self.existing_data = existing_data
        self.is_edit_mode = existing_data is not None
        self.dialog = QDialog(parent_window)
        self.dialog.setWindowTitle("編輯專案" if self.is_edit_mode else "新建專案")
        self.dialog.resize(500, 500)
        self.inputs = {}
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self.dialog); form = QFormLayout()
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")

        for field in self.meta_schema:
            key = field['key']; f_type = field['type']; label = field['label']
            if f_type == 'hidden': continue
            widget = None
            
            if f_type == 'text':
                widget = QLineEdit()
                if self.is_edit_mode and key in self.existing_data:
                    widget.setText(str(self.existing_data[key]))
                    if key == "project_name": widget.setReadOnly(True); widget.setStyleSheet("background-color:#f0f0f0;")
            elif f_type == 'date': 
                widget = QDateEdit(); widget.setCalendarPopup(True)
                if self.is_edit_mode and key in self.existing_data:
                    widget.setDate(QDate.fromString(self.existing_data[key], "yyyy-MM-dd"))
                else: widget.setDate(QDate.currentDate())
            elif f_type == 'path_selector':
                widget = QWidget(); h = QHBoxLayout(widget); h.setContentsMargins(0,0,0,0)
                pe = QLineEdit(); btn = QToolButton(); btn.setText("...")
                if self.is_edit_mode: pe.setText(self.existing_data.get(key,"")); pe.setReadOnly(True); btn.setEnabled(False)
                else: pe.setText(desktop); btn.clicked.connect(lambda _, le=pe: self._browse(le))
                h.addWidget(pe); h.addWidget(btn); widget.line_edit = pe
            elif f_type == 'checkbox_group':
                widget = QGroupBox(); v = QVBoxLayout(widget); v.setContentsMargins(5,5,5,5)
                opts = field.get("options", []); chks = []
                vals = self.existing_data.get(key, []) if self.is_edit_mode else []
                for o in opts:
                    chk = QCheckBox(o['label']); chk.setProperty("val", o['value'])
                    if self.is_edit_mode: 
                        if o['value'] in vals: chk.setChecked(True)
                    else: chk.setChecked(True)
                    v.addWidget(chk); chks.append(chk)
                widget.checkboxes = chks

            if widget: form.addRow(label, widget); self.inputs[key] = {'w': widget, 't': f_type}
        
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.dialog.accept); btns.rejected.connect(self.dialog.reject)
        layout.addWidget(btns)
        
    def _browse(self, le):
        d = QFileDialog.getExistingDirectory(self.dialog, "選擇資料夾")
        if d: le.setText(d)
            
    def run(self):
        if self.dialog.exec() == QDialog.Accepted: return self._collect()
        return None
        
    def _collect(self):
        data = {}
        for key, inf in self.inputs.items():
            w = inf['w']; t = inf['t']
            if t == 'text': data[key] = w.text()
            elif t == 'date': data[key] = w.date().toString("yyyy-MM-dd")
            elif t == 'path_selector': data[key] = w.line_edit.text()
            elif t == 'checkbox_group': data[key] = [c.property("val") for c in w.checkboxes if c.isChecked()]
        return data

# ==========================================
# 4. 總覽頁面 (Overview) - 使用 ProjectManager 邏輯
# ==========================================
class OverviewPage(QWidget):
    def __init__(self, pm, config):
        super().__init__(); self.pm = pm; self.config = config; self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        info_g = QGroupBox("專案資訊"); f = QFormLayout()
        self.l_name = QLabel("-"); self.l_id = QLabel("-"); self.l_tester = QLabel("-")
        f.addRow("專案名稱:", self.l_name); f.addRow("報告編號:", self.l_id); f.addRow("檢測人員:", self.l_tester)
        info_g.setLayout(f); self.layout.addWidget(info_g)

        photo_g = QGroupBox("受測物照片"); h = QHBoxLayout()
        self.img_uav = self._mk_img_lbl(); b_uav = QPushButton("上傳 UAV"); b_uav.clicked.connect(lambda: self.up_photo("uav"))
        self.img_gcs = self._mk_img_lbl(); b_gcs = QPushButton("上傳 GCS"); b_gcs.clicked.connect(lambda: self.up_photo("gcs"))
        v1 = QVBoxLayout(); v1.addWidget(QLabel("UAV")); v1.addWidget(self.img_uav); v1.addWidget(b_uav)
        v2 = QVBoxLayout(); v2.addWidget(QLabel("GCS")); v2.addWidget(self.img_gcs); v2.addWidget(b_gcs)
        h.addLayout(v1); h.addLayout(v2); photo_g.setLayout(h); self.layout.addWidget(photo_g)

        self.prog_g = QGroupBox("檢測進度"); self.prog_l = QVBoxLayout(); self.prog_g.setLayout(self.prog_l)
        self.layout.addWidget(self.prog_g); self.layout.addStretch()

    def _mk_img_lbl(self):
        l = QLabel("無照片"); l.setFrameShape(QFrame.Box); l.setFixedSize(200, 150)
        l.setAlignment(Qt.AlignCenter); l.setScaledContents(True); return l

    def refresh_data(self):
        if not self.pm.current_project_path: return
        data = self.pm.project_data.get("info", {})
        self.l_name.setText(data.get("project_name", "-"))
        self.l_id.setText(data.get("report_id", "-"))
        self.l_tester.setText(data.get("tester", "-"))
        self._load_img(data.get("uav_photo_path"), self.img_uav)
        self._load_img(data.get("gcs_photo_path"), self.img_gcs)

        # 清空舊進度條
        while self.prog_l.count(): child = self.prog_l.takeAt(0); child.widget().deleteLater() if child.widget() else None

        # 使用 config 遍歷所有 Section，並詢問 pm 是否顯示
        for section in self.config.get("test_standards", []):
            sec_id = section['section_id']
            sec_name = section['section_name']
            
            # 【關鍵】直接詢問 Manager 該章節是否可見
            is_visible = self.pm.is_section_visible(sec_id)

            h = QHBoxLayout(); lbl = QLabel(sec_name); lbl.setFixedWidth(150); p = QProgressBar()
            
            if is_visible:
                items = section['items']
                # 【關鍵】過濾出「有效」的 items
                active_items = [i for i in items if self.pm.is_item_visible(i['id'])]
                
                total = len(active_items)
                done = sum(1 for i in active_items if self.pm.is_test_fully_completed(i))
                
                if total > 0:
                    p.setRange(0, total); p.setValue(done)
                    p.setFormat(f"%v / %m ({int(done/total*100)}%)")
                else:
                    p.setRange(0, 100); p.setValue(0); p.setFormat("無項目")
            else:
                p.setRange(0, 100); p.setValue(0); p.setFormat("不適用 (N/A)")
                p.setStyleSheet("QProgressBar { color: gray; background-color: #f0f0f0; }")
                lbl.setStyleSheet("color: gray;")

            h.addWidget(lbl); h.addWidget(p); w = QWidget(); w.setLayout(h); self.prog_l.addWidget(w)

    def _load_img(self, path, lbl):
        if path:
            full = os.path.join(self.pm.current_project_path, path)
            if os.path.exists(full): lbl.setPixmap(QPixmap(full)); return
        lbl.setText("無照片")

    def up_photo(self, type_):
        if not self.pm.current_project_path: return
        f, _ = QFileDialog.getOpenFileName(self, "選圖", "", "Images (*.png *.jpg)")
        if f:
            rel = self.pm.import_file(f, "images")
            if rel: self.pm.update_info({f"{type_}_photo_path": rel})


# ==========================================
# 5. 單一檢測填寫 (Single Target)
# ==========================================
class SingleTargetTestWidget(QWidget):
    def __init__(self, target, config, pm, save_cb=None):
        super().__init__()
        self.target = target; self.config = config; self.pm = pm
        self.item_id = config['id']; self.save_cb = save_cb
        self.logic = config.get("logic", "AND").upper()
        self._init_ui(); self._load()

    def _init_ui(self):
        l = QVBoxLayout(self)
        h = QHBoxLayout(); h.addWidget(QLabel(f"<h3>對象: {self.target}</h3>"))
        h.addWidget(QLabel("(全選通過)" if self.logic == "AND" else "(擇一通過)")); h.addStretch()
        l.addLayout(h)

        self.desc = QTextEdit(); self.desc.setPlaceholderText(self.config.get('evidence_block', {}).get('description_template', ''))
        g1 = QGroupBox("說明"); v1 = QVBoxLayout(); v1.addWidget(self.desc); g1.setLayout(v1); l.addWidget(g1)

        self.checks = {}; criteria = self.config.get('sub_criteria', [])
        if criteria:
            g2 = QGroupBox("標準"); v2 = QVBoxLayout()
            for c in criteria:
                chk = QCheckBox(c['content']); chk.stateChanged.connect(self.auto_judge)
                self.checks[c['id']] = chk; v2.addWidget(chk)
            g2.setLayout(v2); l.addWidget(g2)

        g_file = QGroupBox("附加報告/檔案 (PDF/HTML)"); h_file = QHBoxLayout()
        self.lbl_file = QLabel("未選擇檔案")
        btn_file = QPushButton("上傳報告..."); btn_file.clicked.connect(self.upload_report)
        h_file.addWidget(self.lbl_file); h_file.addWidget(btn_file); g_file.setLayout(h_file)
        l.addWidget(g_file)
        self.current_report_path = None 

        g3 = QGroupBox("判定"); h3 = QHBoxLayout(); h3.addWidget(QLabel("結果:"))
        self.combo = QComboBox(); self.combo.addItems(["未判定", "合格 (Pass)", "不合格 (Fail)", "不適用 (N/A)"])
        self.combo.currentTextChanged.connect(self.update_color); h3.addWidget(self.combo)
        g3.setLayout(h3); l.addWidget(g3); l.addStretch()

        btn = QPushButton(f"儲存 ({self.target})"); btn.setStyleSheet("background-color: #4CAF50; color: white;")
        btn.clicked.connect(self.on_save); l.addWidget(btn)

    def upload_report(self):
        if not self.pm.current_project_path:
            QMessageBox.warning(self, "警告", "請先建立專案"); return
        f, _ = QFileDialog.getOpenFileName(self, "選擇報告", "", "Files (*.pdf *.html *.txt)")
        if f:
            rel_path = self.pm.import_file(f, "reports")
            if rel_path:
                self.current_report_path = rel_path
                self.lbl_file.setText(os.path.basename(rel_path))

    def auto_judge(self):
        if not self.checks: return
        checked = sum(1 for c in self.checks.values() if c.isChecked())
        total = len(self.checks)
        is_pass = (checked == total) if self.logic == "AND" else (checked > 0)
        self.combo.setCurrentText("合格 (Pass)" if is_pass else "不合格 (Fail)")

    def update_color(self, t):
        s = ""
        if "合格" in t and "不" not in t: s = "background-color: #d4edda; color: #155724;"
        elif "不合格" in t: s = "background-color: #f8d7da; color: #721c24;"
        elif "不適用" in t: s = "background-color: #e2e3e5;"
        self.combo.setStyleSheet(s)

    def on_save(self):
        if not self.pm.current_project_path: return
        data = {
            "description": self.desc.toPlainText(),
            "criteria": {k: c.isChecked() for k,c in self.checks.items()},
            "result": self.combo.currentText(),
            "report_path": self.current_report_path,
            "status": "checked"
        }
        if self.save_cb: self.save_cb(data)
        else: 
            self.pm.update_test_result(self.item_id, self.target, data)
            QMessageBox.information(self, "成功", "已儲存")

    def _load(self):
        if not self.pm.project_data: return
        item = self.pm.project_data.get("tests", {}).get(self.item_id, {})
        key = self.target
        if self.target == "Shared":
            key = self.config.get("targets", ["GCS"])[0]
        data = item.get(key, {})
        if data:
            self.desc.setPlainText(data.get("description", ""))
            for k, v in data.get("criteria", {}).items():
                if k in self.checks: 
                    self.checks[k].blockSignals(True); self.checks[k].setChecked(v); self.checks[k].blockSignals(False)
            res = data.get("result", "未判定")
            idx = self.combo.findText(res)
            if idx >= 0: self.combo.setCurrentIndex(idx)
            self.update_color(res)
            rp = data.get("report_path")
            if rp:
                self.current_report_path = rp
                self.lbl_file.setText(os.path.basename(rp))


# ==========================================
# 6. 通用頁面 (Container)
# ==========================================
class UniversalTestPage(QWidget):
    def __init__(self, config, pm):
        super().__init__()
        self.config = config; self.pm = pm
        self.targets = config.get("targets", ["GCS"])
        self.allow_share = config.get("allow_share", False)
        self._init_ui(); self._load_state()

    def _init_ui(self):
        l = QVBoxLayout(self)
        h = QHBoxLayout(); h.addWidget(QLabel(f"<h2>{self.config['name']}</h2>")); l.addLayout(h)
        self.chk = None
        if len(self.targets) > 1 and self.allow_share:
            self.chk = QCheckBox("共用結果"); self.chk.setStyleSheet("color: blue; font-weight: bold;")
            self.chk.toggled.connect(self.on_share); h.addStretch(); h.addWidget(self.chk)

        self.stack = QStackedWidget(); l.addWidget(self.stack)
        self.p_sep = QWidget(); v = QVBoxLayout(self.p_sep); v.setContentsMargins(0,0,0,0)
        if len(self.targets) > 1:
            tabs = QTabWidget()
            for t in self.targets: tabs.addTab(SingleTargetTestWidget(t, self.config, self.pm), t)
            v.addWidget(tabs)
        else:
            v.addWidget(SingleTargetTestWidget(self.targets[0], self.config, self.pm))
        self.stack.addWidget(self.p_sep)

        if len(self.targets) > 1:
            self.p_share = SingleTargetTestWidget("Shared", self.config, self.pm, save_cb=self.save_share)
            self.stack.addWidget(self.p_share)

    def _load_state(self):
        meta = self.pm.get_test_meta(self.config['id'])
        if self.chk and meta.get("is_shared"):
            self.chk.setChecked(True); self.stack.setCurrentWidget(self.p_share)

    def on_share(self, checked):
        self.stack.setCurrentWidget(self.p_share if checked else self.p_sep)

    def save_share(self, data):
        for t in self.targets: self.pm.update_test_result(self.config['id'], t, data, is_shared=True)
        QMessageBox.information(self, "成功", "共用儲存完成")


# ==========================================
# 7. 主程式 (MainApp)
# ==========================================
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("無人機資安檢測工具 v16.1 (Logic Separated)")
        self.resize(1000, 750)
        self.config = self._load_config()
        self.pm = ProjectManager()
        self.pm.set_standard_config(self.config) # 注入 config
        
        self.pm.data_changed.connect(self.refresh_ui)
        self.test_ui_elements = {}

        self.cw = QWidget(); self.setCentralWidget(self.cw); self.main_l = QVBoxLayout(self.cw)
        self._init_menu()
        self.tabs = QTabWidget(); self.tabs.currentChanged.connect(lambda i: self.overview.refresh_data() if i==0 else None)
        self.main_l.addWidget(self.tabs)
        
        self.overview = OverviewPage(self.pm, self.config)
        self.tabs.addTab(self.overview, "總覽 Overview")
        self._init_tabs()
        self._set_enabled(False)

    def _load_config(self):
        # 預設若是沒有檔案，提供空結構以免報錯
        cfg = {"test_standards": [], "project_meta_schema": []}
        if os.path.exists("standard_config.json"):
            try:
                with open("standard_config.json", "r", encoding='utf-8') as f: cfg = json.load(f)
            except Exception as e: print(f"Config Load Error: {e}")
        return cfg

    def _init_menu(self):
        mb = self.menuBar()
        f_menu = mb.addMenu("檔案"); f_menu.addAction("新建專案", self.on_new); f_menu.addAction("開啟專案", self.on_open)
        self.a_edit = f_menu.addAction("編輯專案", self.on_edit); self.a_edit.setEnabled(False)
        
        t_menu = mb.addMenu("工具")
        t_menu.addAction("各別檢測模式 (Ad-Hoc)", self.on_adhoc)
        self.a_merge = t_menu.addAction("匯入各別檢測結果", self.on_merge); self.a_merge.setEnabled(False)

    def _init_tabs(self):
        """根據 JSON 動態建立 Tabs，這裡不處理隱藏邏輯，只負責建立 UI"""
        for sec in self.config.get("test_standards", []):
            p = QWidget(); v = QVBoxLayout(p)
            v.addWidget(QLabel(f"<h3>{sec['section_name']}</h3>"))
            scr = QScrollArea(); scr.setWidgetResizable(True); v.addWidget(scr)
            cont = QWidget(); cv = QVBoxLayout(cont); scr.setWidget(cont)
            
            for item in sec['items']:
                row = QWidget(); rh = QHBoxLayout(row); rh.setContentsMargins(0,5,0,5)
                btn = QPushButton(f"{item['id']} {item['name']}")
                btn.setFixedHeight(40); btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                btn.clicked.connect(partial(self.open_test, item))
                
                st_cont = QWidget(); st_l = QHBoxLayout(st_cont); st_l.setContentsMargins(0,0,0,0); st_cont.setFixedWidth(240)
                rh.addWidget(btn); rh.addWidget(st_cont); cv.addWidget(row)
                self.test_ui_elements[item['id']] = (btn, st_l, item, row)
            cv.addStretch()
            self.tabs.addTab(p, sec['section_id']) # Tab 標題之後會被 update_tab_visibility 更新

    def refresh_ui(self):
        self.overview.refresh_data()
        self.update_status()
        self.update_tab_visibility()
        
        has_proj = self.pm.current_project_path is not None
        self.a_edit.setEnabled(has_proj)
        
        info = self.pm.project_data.get("info", {})
        is_full = info.get("project_type", "full") == "full"
        self.a_merge.setEnabled(has_proj and is_full)
        
        pname = info.get("project_name", "")
        ptype = "完整專案" if is_full else "各別檢測"
        self.setWindowTitle(f"無人機資安檢測工具 - {pname} ({ptype})")

    def update_status(self):
        """更新所有按鈕的狀態與顏色，並根據 Manager 決定顯示與否"""
        for tid, (btn, layout, conf, row) in self.test_ui_elements.items():
            
            # 【關鍵】UI 不做邏輯判斷，直接問 PM：這個 ID 該不該顯示？
            if not self.pm.is_item_visible(tid):
                row.hide()
                continue
            else:
                row.show()

            # 更新狀態顏色
            status_map = self.pm.get_test_status_detail(conf)
            is_any = any(s != "未檢測" for s in status_map.values())
            btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; } QPushButton:hover { background-color: #1976D2; }" if is_any else "")
            
            while layout.count(): layout.takeAt(0).widget().deleteLater()
            
            cnt = len(status_map)
            for t, s in status_map.items():
                lbl = QLabel(f"{t}: {s}" if cnt > 1 else s)
                lbl.setAlignment(Qt.AlignCenter); lbl.setFixedHeight(30)
                c = "#dddddd"; tc = "#666666"
                if s == "Pass": c="#4CAF50"; tc="white"
                elif s == "Fail": c="#F44336"; tc="white"
                elif s == "N/A": c="#9E9E9E"; tc="white"
                lbl.setStyleSheet(f"background-color:{c}; color:{tc}; border-radius:4px; font-weight:bold; font-size:12px;")
                layout.addWidget(lbl)

    def update_tab_visibility(self):
        """更新 Tabs 的可用性"""
        if not self.pm.current_project_path: return

        for i, sec in enumerate(self.config.get("test_standards", [])):
            t_idx = i + 1 # 0 是 Overview
            sec_id = sec['section_id']
            
            # 【關鍵】直接問 PM 這個 Section 該不該顯示
            is_visible = self.pm.is_section_visible(sec_id)

            self.tabs.setTabEnabled(t_idx, is_visible)
            title = sec['section_name']
            if not is_visible: title += " (N/A)"
            self.tabs.setTabText(t_idx, title)

    def _set_enabled(self, e):
        for i in range(1, self.tabs.count()): self.tabs.setTabEnabled(i, e)

    # Slots
    def on_new(self):
        c = ProjectFormController(self, self.config['project_meta_schema'])
        d = c.run()
        if d: 
            ok, r = self.pm.create_project(d)
            if ok: QMessageBox.information(self, "OK", f"建立於 {r}"); self.project_ready()
            else: QMessageBox.warning(self, "Fail", r)

    def on_open(self):
        d = QFileDialog.getExistingDirectory(self, "選專案")
        if d:
            ok, m = self.pm.load_project(d)
            if ok: QMessageBox.information(self, "OK", "讀取成功"); self.project_ready()
            else: QMessageBox.warning(self, "Fail", m)

    def on_edit(self):
        if not self.pm.current_project_path: return
        old = self.pm.project_data.get("info", {})
        c = ProjectFormController(self, self.config['project_meta_schema'], old)
        d = c.run()
        if d:
            if self.pm.update_info(d): QMessageBox.information(self, "OK", "已更新"); self.overview.refresh_data()

    def on_adhoc(self):
        d = QuickTestSelector(self, self.config)
        # 【關鍵修復】使用 run() 方法（內部封裝 exec()），確保對話框彈出
        selected, path = d.run() 
        if selected and path:
            ok, r = self.pm.create_ad_hoc_project(selected, path)
            if ok: QMessageBox.information(self, "OK", f"各別檢測專案已建立:\n{r}"); self.project_ready()
            else: QMessageBox.warning(self, "Fail", r)

    def on_merge(self):
        d = QFileDialog.getExistingDirectory(self, "選擇要匯入的各別檢測資料夾")
        if d:
            ok, msg = self.pm.merge_external_project(d)
            if ok: QMessageBox.information(self, "OK", msg)
            else: QMessageBox.warning(self, "Fail", msg)

    def project_ready(self):
        self._set_enabled(True); self.refresh_ui(); self.tabs.setCurrentIndex(0)

    def open_test(self, item):
        self.win = QWidget(); self.win.setWindowTitle(f"檢測 {item['id']}")
        self.win.resize(600, 700); l = QVBoxLayout(self.win)
        l.addWidget(UniversalTestPage(item, self.pm)); self.win.show()

if __name__ == "__main__":
    app = QApplication(sys.argv); window = MainApp(); window.show(); sys.exit(app.exec())