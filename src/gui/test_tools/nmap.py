"""
Nmap 網路埠掃描測項工具模組
包含 NmapTestToolStrings, NmapTestToolView, NmapTestTool
"""

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QMessageBox,
    QSizePolicy,
)

from .command import CommandTestToolView, CommandTestTool


# ==============================================================================
# 字串常數
# ==============================================================================


class NmapTestToolStrings:
    """NmapTestToolView 字串常數"""

    # Labels
    LBL_TARGET_IP = "目標 IP："
    LBL_SCAN_TYPE = "掃描類型："
    LBL_PORT_RANGE = "Port 範圍："

    # Placeholder
    HINT_IP = "例如：192.168.1.1"
    HINT_PORT = "例如：1-1024 或 0-65535"
    DEFAULT_PORT = "0-65535"
    HINT_RESULT = "掃描結果將顯示於此..."

    # 掃描類型選項
    SCAN_TCP_CONNECT = "-sT (TCP Connect - 不需 root)"
    SCAN_TCP_SYN = "-sS (TCP SYN - 需 root)"
    SCAN_UDP = "-sU (UDP - 需 root)"

    # 掃描速度選項
    LBL_TIMING = "掃描速度："
    TIMING_T0 = "-T0 (Paranoid - 極慢)"
    TIMING_T1 = "-T1 (Sneaky - 很慢)"
    TIMING_T2 = "-T2 (Polite - 較慢)"
    TIMING_T3 = "-T3 (Normal - 正常)"
    TIMING_T4 = "-T4 (Aggressive - 快速)"
    TIMING_T5 = "-T5 (Insane - 極快)"
    DEFAULT_TIMING_INDEX = 4  # 預設 -T4

    # 詳細輸出選項
    LBL_VERBOSE = "詳細輸出 (-v)"

    # 工具標題
    GB_TOOL = "🔍 網路埠掃描設定"
    BTN_RUN = "▶️ 開始掃描"
    BTN_RUNNING = "⏳ 掃描中..."

    # 錯誤訊息
    ERR_NO_IP = "請先輸入目標 IP"
    TITLE_ERROR = "錯誤"

    # 指令模板
    CMD_TEMPLATE = "nmap {scan_type} -p {port_range} {ip}"
    CMD_PLACEHOLDER_IP = "<目標IP>"


# ==============================================================================
# View 類別
# ==============================================================================


class NmapTestToolView(CommandTestToolView):
    """
    Nmap 網路埠掃描測項 UI
    繼承 CommandTestToolView，新增 Nmap 專屬輸入欄位
    """

    def _build_input_section(self) -> QWidget:
        """覆寫：建立 Nmap 專屬輸入區"""
        S = NmapTestToolStrings
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 目標 IP 輸入
        h_ip = QHBoxLayout()
        h_ip.addWidget(QLabel(S.LBL_TARGET_IP))
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText(S.HINT_IP)
        self.ip_input.textChanged.connect(self._update_command_preview)
        h_ip.addWidget(self.ip_input)
        layout.addLayout(h_ip)

        # 掃描類型選擇
        h_type = QHBoxLayout()
        h_type.addWidget(QLabel(S.LBL_SCAN_TYPE))
        self.combo_scan_type = QComboBox()
        self.combo_scan_type.addItems([S.SCAN_TCP_CONNECT, S.SCAN_TCP_SYN, S.SCAN_UDP])
        self.combo_scan_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_scan_type.currentTextChanged.connect(self._update_command_preview)
        h_type.addWidget(self.combo_scan_type)
        layout.addLayout(h_type)

        # Port 範圍
        h_port = QHBoxLayout()
        h_port.addWidget(QLabel(S.LBL_PORT_RANGE))
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText(S.HINT_PORT)
        self.port_input.setText(S.DEFAULT_PORT)
        self.port_input.textChanged.connect(self._update_command_preview)
        h_port.addWidget(self.port_input)
        layout.addLayout(h_port)

        # 掃描速度選擇
        h_timing = QHBoxLayout()
        h_timing.addWidget(QLabel(S.LBL_TIMING))
        self.combo_timing = QComboBox()
        self.combo_timing.addItems([
            S.TIMING_T0, S.TIMING_T1, S.TIMING_T2,
            S.TIMING_T3, S.TIMING_T4, S.TIMING_T5
        ])
        self.combo_timing.setCurrentIndex(S.DEFAULT_TIMING_INDEX)  # 預設 -T4
        self.combo_timing.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_timing.currentTextChanged.connect(self._update_command_preview)
        h_timing.addWidget(self.combo_timing)
        layout.addLayout(h_timing)

        # 詳細輸出選項
        self.chk_verbose = QCheckBox(S.LBL_VERBOSE)
        self.chk_verbose.setChecked(True)  # 預設啟用
        self.chk_verbose.stateChanged.connect(self._update_command_preview)
        layout.addWidget(self.chk_verbose)

        return widget

    def _get_tool_title(self) -> str:
        return NmapTestToolStrings.GB_TOOL

    def _get_run_button_text(self) -> str:
        return NmapTestToolStrings.BTN_RUN

    def _get_running_button_text(self) -> str:
        return NmapTestToolStrings.BTN_RUNNING

    def _get_result_placeholder(self) -> str:
        return NmapTestToolStrings.HINT_RESULT

    def _update_command_preview(self):
        """覆寫：更新 Nmap 指令預覽"""
        S = NmapTestToolStrings
        ip = self.ip_input.text().strip()
        scan_type = self.combo_scan_type.currentText().split()[0]  # -sT/-sS/-sU
        port_range = self.port_input.text().strip()
        timing = self.combo_timing.currentText().split()[0]  # -T0~-T5
        verbose = "-v" if self.chk_verbose.isChecked() else ""

        # 組合指令
        parts = ["nmap", scan_type, timing]
        if verbose:
            parts.append(verbose)
        parts.extend(["-p", port_range])
        
        if ip:
            parts.append(ip)
        else:
            parts.append(S.CMD_PLACEHOLDER_IP)

        self.command_edit.setText(" ".join(parts))

    def _validate_before_run(self) -> bool:
        """覆寫：驗證 IP 是否已輸入"""
        S = NmapTestToolStrings
        cmd = self.command_edit.text().strip()
        if S.CMD_PLACEHOLDER_IP in cmd or not cmd:
            QMessageBox.warning(self, S.TITLE_ERROR, S.ERR_NO_IP)
            return False
        return True

    def _set_inputs_enabled(self, enabled: bool):
        """覆寫：設定 Nmap 專屬輸入欄位的啟用狀態"""
        self.ip_input.setEnabled(enabled)
        self.combo_scan_type.setEnabled(enabled)
        self.port_input.setEnabled(enabled)
        self.combo_timing.setEnabled(enabled)
        self.chk_verbose.setEnabled(enabled)

    # ----- Nmap 專用方法 (保持相容性) -----

    def set_scanning(self, is_scanning: bool):
        """相容舊 API"""
        self.set_running(is_scanning)

    def get_scan_result(self) -> str:
        """相容舊 API"""
        return self.get_result_text()


# ==============================================================================
# Tool 類別 (邏輯 + 控制層)
# ==============================================================================


class NmapTestTool(CommandTestTool):
    """
    Nmap 網路埠掃描測項工具
    繼承 CommandTestTool，只需覆寫專屬方法
    """

    def _create_view(self, config) -> NmapTestToolView:
        """覆寫：回傳 NmapTestToolView"""
        return NmapTestToolView(config)

    def _get_tool_name(self) -> str:
        return "nmap"

    def _get_screenshot_title(self, timestamp: str) -> str:
        ip = self.view.ip_input.text() if hasattr(self.view, "ip_input") else ""
        return f"Nmap 掃描結果 - {ip} ({timestamp})"

    def _get_log_header(self) -> str:
        return "# Nmap 掃描紀錄\n"

    def _needs_root(self, command: str) -> bool:
        """Nmap 的 -sS 和 -sU 需要 root 權限"""
        return "-sS" in command or "-sU" in command

    def _get_command_data_key(self) -> str:
        return "nmap"

    # 相容舊 API
    def _run_nmap(self, command: str):
        """相容舊 API"""
        self._run_command(command)

    def _load_nmap_data(self, data):
        """相容舊 API"""
        self._load_command_data(data)


if __name__ == "__main__":
    import sys
    import os
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dummy_config = {
        "id": "test_cmd",
        "name": "獨立測試視窗",
        "logic": "AND",
        "checklist": [{"id": "chk1", "content": "測試檢查點"}],
    }

    # 直接實例化 Tool (包含邏輯與控制)
    tool = NmapTestTool(dummy_config, {}, "test_target")
    tool.set_project_path(os.path.join(os.path.expanduser("~"), "Desktop"))

    tool.get_widget().show()
    sys.exit(app.exec())
