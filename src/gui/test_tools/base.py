"""
基礎測項工具模組
包含 BaseTestToolStrings, BaseTestToolView, BaseTestTool
"""

from typing import Dict, Optional, Tuple

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QTextEdit,
    QGroupBox,
)

from styles import Styles
from constants import STATUS_PASS, STATUS_FAIL


# ==============================================================================
# 字串常數
# ==============================================================================


class BaseTestToolStrings:
    """BaseTestToolView 字串常數"""

    # 判定邏輯
    LOGIC_AND = "須符合所有項目 (AND)"
    LOGIC_OR = "符合任一項目即可 (OR)"
    LOGIC_PREFIX = "判定邏輯: "

    # 規範說明
    CRITERIA_ALL = "符合下列【所有】項目者為通過"
    CRITERIA_ANY = "符合下列【任一】項目者為通過"
    CRITERIA_ELSE = "，否則為未通過：\n"
    NO_METHOD_DESC = "無測試方法描述"

    # HTML 標籤
    HTML_METHOD_TITLE = "<b style='color:#333;'>【測試方法】</b>"
    HTML_CRITERIA_TITLE = "<b style='color:#333;'>【判定標準】</b>"

    # GroupBox 標題
    GB_NARRATIVE = "規範說明"
    GB_CHECKLIST = "細項檢查表 (Checklist)"
    GB_NOTE = "判定原因 / 備註"

    # Placeholder
    HINT_NOTE = "合格時可留空，不合格時系統將自動帶入原因..."


# ==============================================================================
# View 類別
# ==============================================================================


class BaseTestToolView(QWidget):
    """
    基礎測項 UI 視圖
    職責：只負責 UI 呈現，透過 Signal 發送使用者操作事件
    子類別可覆寫 _build_custom_section() 來新增專屬 UI
    """

    # Signals - 發送給 Controller
    check_changed = Signal(str, bool)  # (item_id, checked)
    note_changed = Signal(str)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = config.get("logic", "AND").upper()
        self.checks: Dict[str, QCheckBox] = {}
        self._init_ui()

    def _init_ui(self):
        """建構 UI - 使用 Template Method Pattern"""
        # 主佈局：水平排列（左：基礎 UI，右：客製化區域）
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        # 左側容器：基礎測項 UI
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # 1. 邏輯提示
        self._build_logic_hint(left_layout)

        # 2. 規範敘述區
        self._build_narrative(left_layout)

        # 3. Checkbox 區塊
        self._build_checklist(left_layout)

        # 4. 備註區
        self._build_note_section(left_layout)

        main_layout.addWidget(left_widget, stretch=1)

        # 右側容器：客製化區域 (子類別覆寫此方法)
        right_widget = self._build_custom_section()
        if right_widget:
            main_layout.addWidget(right_widget, stretch=1)

    def _build_logic_hint(self, layout: QVBoxLayout):
        """建立判定邏輯提示"""
        S = BaseTestToolStrings
        logic_desc = S.LOGIC_AND if self.logic == "AND" else S.LOGIC_OR
        lbl_logic = QLabel(f"{S.LOGIC_PREFIX}{logic_desc}")
        lbl_logic.setStyleSheet(Styles.LOGIC_HINT)
        layout.addWidget(lbl_logic)

    def _build_narrative(self, layout: QVBoxLayout):
        """建立規範敘述區"""
        S = BaseTestToolStrings
        narrative = self.config.get("narrative", {})
        checklist_data = self.config.get("checklist", [])

        method_text = narrative.get("method", S.NO_METHOD_DESC)
        criteria_text = narrative.get("criteria", "")

        # 自動生成判定標準
        if not criteria_text and checklist_data:
            header = S.CRITERIA_ANY if self.logic == "OR" else S.CRITERIA_ALL
            lines = [
                f"({i+1}) {item.get('content', '')}"
                for i, item in enumerate(checklist_data)
            ]
            criteria_text = f"{header}{S.CRITERIA_ELSE}" + "\n".join(lines)

        method_html = method_text.replace("\n", "<br>")
        criteria_html = criteria_text.replace("\n", "<br>")

        display_html = (
            f"{S.HTML_METHOD_TITLE}"
            f"<div style='margin-left:10px; color:#555;'>{method_html}</div>"
            f"{S.HTML_CRITERIA_TITLE}"
            f"<div style='margin-left:10px; color:#D32F2F;'>{criteria_html}</div>"
        )

        self.desc_edit = QTextEdit()
        self.desc_edit.setHtml(display_html)
        self.desc_edit.setReadOnly(True)
        self.desc_edit.setStyleSheet(Styles.DESC_BOX)
        self.desc_edit.setMinimumHeight(150)
        self.desc_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.desc_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        g1 = QGroupBox(S.GB_NARRATIVE)
        v1 = QVBoxLayout()
        v1.addWidget(self.desc_edit)
        g1.setLayout(v1)
        layout.addWidget(g1)

    def _build_checklist(self, layout: QVBoxLayout):
        """建立 Checkbox 列表"""
        S = BaseTestToolStrings
        checklist_data = self.config.get("checklist", [])
        if not checklist_data:
            return

        gb = QGroupBox(S.GB_CHECKLIST)
        gb_layout = QVBoxLayout()
        gb_layout.setSpacing(8)

        for item in checklist_data:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(10)

            chk = QCheckBox()
            chk.setFixedWidth(25)
            chk.setStyleSheet(Styles.CHECKBOX)

            content = item.get("content", item.get("id"))
            item_id = item["id"]

            lbl = QLabel(content)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(Styles.LABEL_NORMAL)
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

            # 綁定事件 - 發送 Signal
            chk.stateChanged.connect(
                lambda state, cid=item_id: self.check_changed.emit(
                    cid, state == Qt.Checked
                )
            )
            self.checks[item_id] = chk

            row_layout.addWidget(chk, 0, Qt.AlignTop)
            row_layout.addWidget(lbl, 1)
            gb_layout.addWidget(row_widget)

        gb.setLayout(gb_layout)
        layout.addWidget(gb)

    def _build_custom_section(self) -> Optional[QWidget]:
        """
        子類別擴展區 - 子類別覆寫此方法來新增專屬 UI
        回傳 QWidget 將顯示在右側，回傳 None 則不顯示
        """
        return None

    def _build_note_section(self, layout: QVBoxLayout):
        """建立備註區"""
        S = BaseTestToolStrings
        g3 = QGroupBox(S.GB_NOTE)
        v3 = QVBoxLayout()
        self.user_note = QTextEdit()
        self.user_note.setPlaceholderText(S.HINT_NOTE)
        self.user_note.setFixedHeight(80)
        self.user_note.textChanged.connect(
            lambda: self.note_changed.emit(self.user_note.toPlainText())
        )
        v3.addWidget(self.user_note)
        g3.setLayout(v3)
        layout.addWidget(g3)

    # ----- View 的 Getter/Setter 方法 (供 Controller 使用) -----

    def set_check_state(self, item_id: str, checked: bool, block_signal: bool = False):
        """設定 checkbox 狀態"""
        if item_id in self.checks:
            chk = self.checks[item_id]
            if block_signal:
                chk.blockSignals(True)
            chk.setChecked(checked)
            if block_signal:
                chk.blockSignals(False)

    def get_check_states(self) -> Dict[str, bool]:
        """取得所有 checkbox 狀態"""
        return {k: c.isChecked() for k, c in self.checks.items()}

    def get_note(self) -> str:
        return self.user_note.toPlainText()

    def set_note(self, text: str):
        if self.user_note.toPlainText() != text:
            self.user_note.setPlainText(text)


# ==============================================================================
# Tool 類別 (邏輯 + 控制層)
# ==============================================================================


class BaseTestTool(QObject):
    """
    基礎測項工具 (邏輯 + 控制層)
    職責：
    - 建立並管理 View
    - 處理 checkbox 判定邏輯 (AND/OR)
    - 計算 Pass/Fail 結果
    - 資料存取
    """

    data_updated = Signal(dict)
    status_changed = Signal(str)
    checklist_changed = Signal()

    def __init__(self, config, result_data, target):
        super().__init__()
        self.config = config
        self.result_data = result_data
        self.target = target
        self.logic = config.get("logic", "AND").upper()

        # 內容對照 (用於產生失敗原因)
        self.item_content_map = {}
        for item in config.get("checklist", []):
            self.item_content_map[item["id"]] = item.get("content", item["id"])

        # 建立 View
        self.view = self._create_view(config)

        # 綁定 View 事件
        self.view.check_changed.connect(self._on_check_changed)

        # 載入已存資料
        if result_data:
            self._load_data(result_data)

    def _create_view(self, config) -> BaseTestToolView:
        """
        建立 View - 子類別覆寫此方法回傳不同的 View 類別
        """
        return BaseTestToolView(config)

    def get_widget(self) -> QWidget:
        """回傳 UI Widget"""
        return self.view

    def get_user_note(self) -> str:
        return self.view.get_note()

    def set_user_note(self, text: str):
        self.view.set_note(text)

    def _on_check_changed(self, item_id: str, checked: bool):
        """處理 checkbox 變更"""
        status, fail_reason = self.calculate_result()
        self.status_changed.emit(status)

        if status == STATUS_FAIL:
            self.view.set_note(fail_reason)
        else:
            curr_text = self.view.get_note()
            if "未通過" in curr_text or "未符合" in curr_text:
                self.view.set_note("符合規範要求。")

    def calculate_result(self) -> Tuple[str, str]:
        """計算判定結果"""
        check_states = self.view.get_check_states()
        if not check_states:
            return STATUS_FAIL, "無檢查項目"

        values = list(check_states.values())

        if self.logic == "OR":
            is_pass = any(values)
        else:
            is_pass = all(values)

        status = STATUS_PASS if is_pass else STATUS_FAIL
        fail_reason = ""

        if status == STATUS_FAIL:
            if self.logic == "AND":
                fail_list = [
                    self.item_content_map.get(cid, cid)
                    for cid, checked in check_states.items()
                    if not checked
                ]
                if fail_list:
                    fail_reason = "未通過，原因如下：\n" + "\n".join(
                        f"- 未符合：{r}" for r in fail_list
                    )
            else:  # OR
                fail_reason = "未通過，原因：上述所有項目皆未符合。"

        return status, fail_reason

    def get_result(self) -> Dict:
        """取得結果資料 (供儲存)"""
        status, _ = self.calculate_result()
        return {
            "criteria": self.view.get_check_states(),
            "description": self.view.get_note(),
            "auto_suggest_result": status,
        }

    def _load_data(self, data):
        """載入已存資料"""
        saved_criteria = data.get("criteria", {})

        # 回填 Checkbox
        for cid, checked in saved_criteria.items():
            self.view.set_check_state(cid, checked, block_signal=True)

        # 回填備註
        self.view.set_note(data.get("description", ""))

    def load_data(self, data):
        """公開的載入方法"""
        self._load_data(data)
