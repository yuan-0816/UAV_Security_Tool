import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QFrame, QLabel, QPushButton, QHBoxLayout, QStatusBar, QMenuBar
)
from PySide6.QtCore import Qt, QPoint, QRect, QEvent
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QCursor, QColor, QPalette

# =====================================================
# 1. 定義主題配色
# =====================================================
THEMES = {
    "light": {
        "bg_color": "#FFFFFF",
        "text_color": "#000000",
        "title_bar_bg": "transparent",
        "title_text": "#333333",
        "border": "#CCCCCC",
        "btn_hover": "#E0E0E0",
        "btn_text": "#333333",
        "shadow": "#000000"
    },
    "dark": {
        "bg_color": "#202020",
        "text_color": "#FFFFFF",
        "title_bar_bg": "transparent",
        "title_text": "#DDDDDD",
        "border": "#444444",
        "btn_hover": "#3D3D3D",
        "btn_text": "#FFFFFF",
        "shadow": "#000000"
    }
}

# =====================================================
# Custom Title Bar
# =====================================================
class CustomTitleBar(QWidget):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setFixedHeight(36)
        self.setMouseTracking(True)

        # 標題 Label (獨立層，不加入 Layout)
        # 這是為了達成嚴格置中，不受右邊按鈕擠壓
        self.title_label = QLabel("MainWindow", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # 按鈕 Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(4)
        
        # 使用 Stretch 把按鈕頂到最右邊
        layout.addStretch()

        self.btn_min = QPushButton("─")
        self.btn_max = QPushButton("□")
        self.btn_close = QPushButton("✕")
        self.buttons = [self.btn_min, self.btn_max, self.btn_close]

        for b in self.buttons:
            b.setFixedSize(36, 36)

        self.btn_min.clicked.connect(parent_window.showMinimized)
        self.btn_max.clicked.connect(parent_window.toggle_maximize)
        self.btn_close.clicked.connect(parent_window.close)

        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

    def resizeEvent(self, event):
        """當 TitleBar 大小改變時，強制將 Label 覆蓋整個區域以達成置中"""
        super().resizeEvent(event)
        self.title_label.setGeometry(0, 0, self.width(), self.height())

    def update_theme(self, theme):
        self.setStyleSheet("background-color: transparent;")
        
        self.title_label.setStyleSheet(f"font-weight:bold; background:transparent; color: {theme['title_text']};")
        
        btn_style = f"""
            QPushButton {{
                border: none;
                color: {theme['btn_text']};
                background: transparent;
            }}
            QPushButton:hover {{
                background-color: {theme['btn_hover']};
            }}
        """
        for b in self.buttons:
            b.setStyleSheet(btn_style)
        
        # 關閉按鈕特例 (Hover 紅色)
        self.btn_close.setStyleSheet(btn_style + "QPushButton:hover { background-color: #E81123; color: white; }")

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
            
        # 檢查是否點擊在視窗頂部邊緣 (Resize 區域)
        top_resize_limit = self.parent_window.y() + self.parent_window.BORDER_WIDTH + 10
        if event.globalPosition().y() < top_resize_limit and not self.parent_window.isMaximized():
            event.ignore() # 讓事件傳給 Main Window 處理 Resize
            return
            
        # 觸發系統移動
        if self.parent_window.windowHandle().startSystemMove():
            event.accept()

    def mouseDoubleClickEvent(self, event):
        top_resize_limit = self.parent_window.y() + self.parent_window.BORDER_WIDTH + 10
        if event.button() == Qt.LeftButton and event.globalPosition().y() > top_resize_limit:
            self.parent_window.toggle_maximize()

# =====================================================
# 通用無邊框視窗 (BorderedMainWindow)
# =====================================================
class BorderedMainWindow(QMainWindow):
    SHADOW_WIDTH = 10 
    BORDER_WIDTH = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. 基礎設定
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self._is_max = False
        self._resize_dir = None
        
        # 2. 建立陰影容器 (Shadow Container)
        # 這是最外層的 Widget，用來承載陰影
        self._shadow_container = QWidget()
        self._shadow_container.setMouseTracking(True)
        super().setCentralWidget(self._shadow_container)

        # 3. 容器佈局 (預留陰影邊距)
        self._container_layout = QVBoxLayout(self._shadow_container)
        self._container_layout.setContentsMargins(
            self.SHADOW_WIDTH, self.SHADOW_WIDTH, 
            self.SHADOW_WIDTH, self.SHADOW_WIDTH
        )
        
        # 4. 視覺邊框 Frame (Visible Frame)
        self.frame = QFrame()
        self.frame.setObjectName("CentralFrame") # 關鍵：設定 ID 以避免 CSS 汙染
        self.frame.setMouseTracking(True)
        self._container_layout.addWidget(self.frame)

        # 5. 陰影特效
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 0)
        self.frame.setGraphicsEffect(self.shadow)

        # 6. Frame 內部佈局 (垂直：標題列 + 內部視窗)
        self._frame_layout = QVBoxLayout(self.frame)
        self._frame_layout.setContentsMargins(0, 0, 0, 0)
        self._frame_layout.setSpacing(0)

        # 7. 加入自定義標題列
        self.title_bar = CustomTitleBar(self)
        self._frame_layout.addWidget(self.title_bar)

        # =========================================================
        # [關鍵] 內部代理視窗 (Inner Proxy Window)
        # 這是實際承載使用者內容的視窗，負責 Menu, Status, Content
        # =========================================================
        self._inner_window = QMainWindow()
        self._inner_window.setWindowFlags(Qt.Widget) # 設為 Widget 才能嵌入
        self._inner_window.setAttribute(Qt.WA_TranslucentBackground) # 確保圓角不被遮擋
        
        self._frame_layout.addWidget(self._inner_window)

        # 初始化事件監聽與主題
        self.installEventFilter(self)
        self.apply_system_theme()

    # =========================================================
    #  Method Overrides (代理方法)
    #  讓此類別表現得像標準 QMainWindow
    # =========================================================

    def setCentralWidget(self, widget):
        """將內容轉發給內部視窗"""
        self._inner_window.setCentralWidget(widget)

    def centralWidget(self):
        return self._inner_window.centralWidget()

    def setMenuBar(self, menu_bar):
        self._inner_window.setMenuBar(menu_bar)

    def menuBar(self):
        return self._inner_window.menuBar()

    def setStatusBar(self, status_bar):
        self._inner_window.setStatusBar(status_bar)
    
    def statusBar(self):
        return self._inner_window.statusBar()

    def setWindowTitle(self, title):
        """同時更新系統標題與自定義標題列"""
        super().setWindowTitle(title)
        if hasattr(self, 'title_bar'):
            self.title_bar.title_label.setText(title)

    # =========================================================
    #  主題與外觀邏輯
    # =========================================================
    def apply_system_theme(self):
        palette = QApplication.palette()
        bg_color = palette.color(QPalette.Window)
        is_dark = bg_color.lightness() < 128
        theme_key = "dark" if is_dark else "light"
        self._apply_theme(THEMES[theme_key])

    def _apply_theme(self, theme):
        # 使用 ID Selector (#CentralFrame) 避免汙染子元件
        self.frame.setStyleSheet(f"""
            #CentralFrame {{
                background-color: {theme['bg_color']};
                border: 1px solid {theme['border']};
                border-radius: 6px;
            }}
        """)
        
        # 設定內部視窗樣式
        self._inner_window.setStyleSheet(f"""
            QMainWindow {{ background: transparent; }}
            QWidget {{ color: {theme['text_color']}; }}
            QMenuBar {{ background: transparent; color: {theme['text_color']}; }}
            QMenuBar::item:selected {{ background: {theme['btn_hover']}; }}
            QStatusBar {{ background: transparent; color: {theme['text_color']}; }}
        """)

        self.shadow.setColor(QColor(theme['shadow']))
        self.title_bar.update_theme(theme)

    def changeEvent(self, event):
        if event.type() == QEvent.PaletteChange:
            self.apply_system_theme()
        super().changeEvent(event)

    # =========================================================
    #  Resize & Event Handling
    # =========================================================
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove or event.type() == QEvent.HoverMove:
            if self._resize_dir:
                return False
            global_pos = QCursor.pos()
            local_pos = self.mapFromGlobal(global_pos)
            self._update_cursor(local_pos)
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.mapFromGlobal(event.globalPosition().toPoint())
            self._resize_dir = self._get_resize_direction(pos)
            
            if self._resize_dir:
                # 使用 startSystemResize 解決 Linux 下的座標問題
                edges = self._convert_dir_to_edges(self._resize_dir)
                if self.windowHandle().startSystemResize(edges):
                    event.accept()
                    self._resize_dir = None
                    return

    def mouseReleaseEvent(self, event):
        self._resize_dir = None
        self.setCursor(Qt.ArrowCursor)

    def _convert_dir_to_edges(self, d):
        edges = Qt.Edges()
        if "l" in d: edges |= Qt.LeftEdge
        if "r" in d: edges |= Qt.RightEdge
        if "t" in d: edges |= Qt.TopEdge
        if "b" in d: edges |= Qt.BottomEdge
        return edges

    def _get_resize_direction(self, pos):
        w = self.width()
        h = self.height()
        margin = self.SHADOW_WIDTH + self.BORDER_WIDTH
        x, y = pos.x(), pos.y()
        left, right = x < margin, x > w - margin
        top, bottom = y < margin, y > h - margin

        if top and left: return "tl"
        if top and right: return "tr"
        if bottom and left: return "bl"
        if bottom and right: return "br"
        if left: return "l"
        if right: return "r"
        if top: return "t"
        if bottom: return "b"
        return None

    def _update_cursor(self, pos):
        d = self._get_resize_direction(pos)
        if d and not self._is_max:
            cursors = {
                "l": Qt.SizeHorCursor, "r": Qt.SizeHorCursor,
                "t": Qt.SizeVerCursor, "b": Qt.SizeVerCursor,
                "tl": Qt.SizeFDiagCursor, "br": Qt.SizeFDiagCursor,
                "tr": Qt.SizeBDiagCursor, "bl": Qt.SizeBDiagCursor,
            }
            self.setCursor(cursors[d])
        else:
            self.setCursor(Qt.ArrowCursor)

    def toggle_maximize(self):
        if self._is_max:
            self.showNormal()
            self._is_max = False
            self._container_layout.setContentsMargins(
                self.SHADOW_WIDTH, self.SHADOW_WIDTH, 
                self.SHADOW_WIDTH, self.SHADOW_WIDTH
            )
            # 恢復圓角
            self.frame.setStyleSheet(self.frame.styleSheet().replace("border-radius: 0px;", "border-radius: 6px;"))
        else:
            self.showMaximized()
            self._is_max = True
            self._container_layout.setContentsMargins(0, 0, 0, 0)
            # 移除圓角
            self.frame.setStyleSheet(self.frame.styleSheet().replace("border-radius: 6px;", "border-radius: 0px;"))

# =====================================================
# MainApp 測試範例
# =====================================================
if __name__ == "__main__":
    
    # 這是您的 MainApp，繼承 BorderedMainWindow 即可
    class MainApp(BorderedMainWindow):
        def __init__(self):
            super().__init__()
            
            # --- 以下代碼完全不需要因為用了 BorderedMainWindow 而修改 ---
            
            # 1. 設定標題
            self.setWindowTitle("無人機資安檢測工具 - 測試專案")

            # 2. 建立 Central Widget
            self.cw = QWidget()
            self.setCentralWidget(self.cw)
            
            layout = QVBoxLayout(self.cw)
            
            # 3. 建立選單
            mb = self.menuBar()
            f_menu = mb.addMenu("檔案")
            f_menu.addAction("新建")
            f_menu.addAction("開啟")
            
            # 4. 建立狀態列
            self.setStatusBar(QStatusBar(self))
            self.statusBar().showMessage("就緒 (Ready)")

            # 5. 加入內容
            btn = QPushButton("這是一個測試按鈕")
            layout.addWidget(QLabel("這是標準 QMainWindow 的內容區域"))
            layout.addWidget(btn)
            layout.addStretch()

    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    w = MainApp()
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec())