"""
GUI 樣式定義模組
包含主題配色和 Styles 類別
"""

# ==============================================================================
# 顏色配置 (HEX)
# ==============================================================================

# 背景色
COLOR_BG_PASS = "#d4edda"
COLOR_BG_FAIL = "#f8d7da"
COLOR_BG_NA = "#e2e3e5"
COLOR_BG_DEFAULT = "#dddddd"
COLOR_BG_WARN = "#fff3cd"
COLOR_BG_GRAY_LIGHT = "#f5f5f5"
COLOR_BG_THUMBNAIL = "#f0f0f0"
COLOR_BG_TERMINAL = "#2d2d2d"
COLOR_BG_TERMINAL_RESULT = "#1e1e1e"

# 文字色
COLOR_TEXT_PASS = "#155724"
COLOR_TEXT_FAIL = "#721c24"
COLOR_TEXT_NORMAL = "#333333"
COLOR_TEXT_WHITE = "white"
COLOR_TEXT_GRAY = "#666666"
COLOR_TEXT_WARN = "#856404"
COLOR_TEXT_SUBTITLE = "#555555"
COLOR_TEXT_TERMINAL_GREEN = "#00ff00"
COLOR_TEXT_TERMINAL_GRAY = "#d4d4d4"

# 按鈕色
COLOR_BTN_ACTIVE = "#2196F3"
COLOR_BTN_HOVER = "#1976D2"
COLOR_BTN_SUCCESS = "#4CAF50"
COLOR_BTN_DANGER = "#d9534f"
COLOR_BTN_CLOSE_HOVER = "#E81123"

# 邊框色
COLOR_BORDER = "#CCCCCC"
COLOR_BORDER_LIGHT = "#dddddd"
COLOR_CHECKBOX_SHARE = "blue"

# ==============================================================================
# 主題配色 (僅淺色模式)
# ==============================================================================

THEME = {
    "bg_color": "#FFFFFF",
    "text_color": "#000000",
    "title_bar_bg": "transparent",
    "title_text": COLOR_TEXT_NORMAL,
    "border": COLOR_BORDER,
    "btn_hover": "#E0E0E0",
    "btn_text": COLOR_TEXT_NORMAL,
    "shadow": "#000000",
}


# ==============================================================================
# Styles 類別
# ==============================================================================


class Styles:
    """集中管理 UI 樣式"""

    # 邏輯提示標籤
    LOGIC_HINT = f"color: {COLOR_BTN_HOVER}; font-weight: bold; font-size: 11pt;"

    # 規範說明區
    DESC_BOX = f"background-color: {COLOR_BG_GRAY_LIGHT}; border: 1px solid {COLOR_BORDER_LIGHT}; border-radius: 4px; font-size: 11pt; padding: 5px;"

    # Checkbox 指示器
    CHECKBOX = "QCheckBox::indicator { width: 20px; height: 20px; }"

    # 標籤文字
    LABEL_NORMAL = "font-size: 11pt; line-height: 1.2;"
    LABEL_GRAY = "color: gray; font-size: 10pt;"
    LABEL_RED = "color: red; font-weight: bold;"
    LABEL_TITLE = "font-weight: bold; font-size: 16pt; padding: 5px;"

    # 指令輸入框 (深色終端風格)
    INPUT_COMMAND = f"font-family: monospace; background-color: {COLOR_BG_TERMINAL}; color: {COLOR_TEXT_TERMINAL_GREEN}; padding: 5px;"

    # 結果顯示區 (深色終端風格)
    TEXT_RESULT = f"font-family: monospace; background-color: {COLOR_BG_TERMINAL_RESULT}; color: {COLOR_TEXT_TERMINAL_GREEN}; font-size: 10pt;"

    # 按鈕樣式
    BTN_PRIMARY = f"background-color: {COLOR_BTN_SUCCESS}; color: white; font-weight: bold; padding: 8px;"
    BTN_DANGER = f"background-color : {COLOR_BTN_DANGER}; color: white; font-weight: bold; padding: 8px;"
    BTN_PADDING = "padding: 6px;"

    # 共用 Checkbox 文字
    CHECKBOX_SHARE = f"color: {COLOR_CHECKBOX_SHARE}; font-weight: bold;"

    # 圖片縮圖區
    THUMBNAIL = f"""
        background-color: {COLOR_BG_THUMBNAIL};
        border: 1px solid #ccc;
        border-radius: 4px;
    """

    # 標題欄按鈕
    TITLE_BTN = """
        QPushButton {{
            background-color: transparent;
            border: none;
            font-size: 14px;
            color: {btn_text};
            padding: 0px;
        }}
        QPushButton:hover {{
            background-color: {btn_hover};
        }}
    """

    TITLE_BTN_CLOSE = f"QPushButton:hover {{ background-color: {COLOR_BTN_CLOSE_HOVER}; color: white; }}"

    # 視窗框架
    FRAME_NORMAL = """
        QFrame#CentralFrame {{
            background-color: {bg_color};
            border: 1px solid {border};
            border-radius: 6px;
        }}
    """

    FRAME_MAXIMIZED = """
        QFrame#CentralFrame {{
            background-color: {bg_color};
            border: 1px solid {border};
            border-radius: 0px;
        }}
    """

    # 內部視窗
    INNER_WINDOW = """
        QMainWindow {{
            background-color: {bg_color};
        }}
    """

    # 附件清單
    ATTACHMENT_LIST = """
        QListWidget {
            border: 1px solid #ccc;
            border-radius: 4px;
            background: #fafafa;
        }
        QListWidget::item {
            border-bottom: 1px solid #eee;
        }
    """

    # 附件標題輸入
    ATTACHMENT_TITLE = """
        font-weight: bold;
        font-size: 10pt;
        border: none;
        border-bottom: 1px solid #ccc;
        padding: 2px;
    """

    # 狀態下拉選單 (依狀態變色)
    @staticmethod
    def combo_status(bg_color: str, text_color: str) -> str:
        return f"background-color: {bg_color}; color: {text_color}; font-weight: bold; padding: 5px;"

    # 測項按鈕 (依狀態變色)
    @staticmethod
    def test_button(bg_color: str, text_color: str) -> str:
        return f"text-align: left; padding: 10px; border-radius: 6px; background-color: {bg_color}; color: {text_color};"
