from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPen, QBrush, QAction, QActionGroup
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication

from config import config_manager


def generate_tray_icon() -> QIcon:
    """程序化生成高分辨率玻璃质感托盘图标"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # 绘制青蓝渐变微光圆角卡片
    painter.setBrush(QBrush(QColor(2, 132, 199, 235)))
    painter.setPen(QPen(QColor(56, 189, 248, 220), 2))
    painter.drawRoundedRect(4, 4, 56, 56, 16, 16)

    # 绘制中文字符“译”
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Microsoft YaHei", 28, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), int(Qt.AlignmentFlag.AlignCenter), "译")
    painter.end()

    return QIcon(pixmap)


class TrayManager:
    """管理系统托盘图标与全局右键控制菜单"""

    def __init__(self, window):
        self.window = window
        self.tray_icon = QSystemTrayIcon(generate_tray_icon(), window)
        self.tray_icon.setToolTip("Windows 实时透视翻译器 (后台运行中)")

        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: rgba(18, 24, 38, 0.95);
                border: 1px solid rgba(56, 189, 248, 0.35);
                border-radius: 8px;
                padding: 6px;
                color: #e2e8f0;
                font-family: 'Segoe UI', 'Microsoft YaHei';
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0284c7;
                color: #ffffff;
            }
            QMenu::item:checked {
                font-weight: bold;
                color: #38bdf8;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 0.12);
                margin: 4px 6px;
            }
        """)

        self._build_menu()
        self.tray_icon.setContextMenu(self.menu)

        # 托盘点击交互
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _build_menu(self):
        self.menu.clear()

        # 1. 窗口显示/隐藏
        self.action_toggle = QAction("🪟 显示翻译框", self.menu)
        self.action_toggle.setCheckable(True)
        self.action_toggle.setChecked(self.window.isVisible())
        self.action_toggle.triggered.connect(self._toggle_window_visibility)
        self.menu.addAction(self.action_toggle)

        self.menu.addSeparator()

        # 2. 实时翻译与单次刷新
        self.action_auto = QAction("⏸️ 实时自动翻译", self.menu)
        self.action_auto.setCheckable(True)
        self.action_auto.setChecked(config_manager.get("auto_translate", True))
        self.action_auto.triggered.connect(self._toggle_auto_translate)
        self.menu.addAction(self.action_auto)

        action_refresh = QAction("⚡ 立即识别刷新", self.menu)
        action_refresh.triggered.connect(self.window.trigger_refresh)
        self.menu.addAction(action_refresh)

        self.menu.addSeparator()

        # 3. 语言选择子菜单
        lang_menu = self.menu.addMenu("🌐 翻译语言")
        lang_menu.setStyleSheet(self.menu.styleSheet())
        self.lang_group = QActionGroup(self.menu)
        self.lang_group.setExclusive(True)
        self.lang_actions = []

        lang_options = [
            ("自动 ➔ 中文", "auto", "zh-CN"),
            ("英文 ➔ 中文", "en", "zh-CN"),
            ("日文 ➔ 中文", "ja", "zh-CN"),
            ("中文 ➔ 英文", "zh", "en"),
        ]
        cur_src = config_manager.get("source_lang", "auto")
        cur_tgt = config_manager.get("target_lang", "zh-CN")

        for label, src, tgt in lang_options:
            act = QAction(label, lang_menu)
            act.setCheckable(True)
            act.setData((src, tgt))
            if cur_src == src and cur_tgt == tgt:
                act.setChecked(True)
            act.triggered.connect(lambda checked, s=src, t=tgt: self._set_language(s, t))
            self.lang_group.addAction(act)
            lang_menu.addAction(act)
            self.lang_actions.append(act)

        # 4. 翻译引擎子菜单
        engine_menu = self.menu.addMenu("🚀 翻译引擎")
        engine_menu.setStyleSheet(self.menu.styleSheet())
        self.engine_group = QActionGroup(self.menu)
        self.engine_group.setExclusive(True)
        self.engine_actions = []

        engine_options = [
            ("⚡ 有道官方直连 (毫秒级·免Key)", "youdao"),
            ("🌐 MyMemory (免费备用通道)", "mymemory"),
            ("🤖 自定义大模型 (OpenAI协议)", "openai"),
        ]
        cur_engine = config_manager.get("engine", "youdao")
        for label, eng_id in engine_options:
            act = QAction(label, engine_menu)
            act.setCheckable(True)
            act.setData(eng_id)
            if cur_engine == eng_id:
                act.setChecked(True)
            act.triggered.connect(lambda checked, eid=eng_id: self._set_engine(eid))
            self.engine_group.addAction(act)
            engine_menu.addAction(act)
            self.engine_actions.append(act)

        # 5. 显示模式子菜单
        mode_menu = self.menu.addMenu("🔤 显示模式")
        mode_menu.setStyleSheet(self.menu.styleSheet())
        self.mode_group = QActionGroup(self.menu)
        self.mode_group.setExclusive(True)
        self.mode_actions = []

        cur_mode = config_manager.get("display_mode", "inplace")
        act_inplace = QAction("原地文字替换 (完全透明覆盖)", mode_menu)
        act_inplace.setCheckable(True)
        act_inplace.setData("inplace")
        act_inplace.setChecked(cur_mode == "inplace")
        act_inplace.triggered.connect(lambda: self._set_display_mode("inplace"))
        self.mode_group.addAction(act_inplace)
        mode_menu.addAction(act_inplace)
        self.mode_actions.append(act_inplace)

        act_card = QAction("悬浮卡片字幕 (独立卡片气泡)", mode_menu)
        act_card.setCheckable(True)
        act_card.setData("card")
        act_card.setChecked(cur_mode == "card")
        act_card.triggered.connect(lambda: self._set_display_mode("card"))
        self.mode_group.addAction(act_card)
        mode_menu.addAction(act_card)
        self.mode_actions.append(act_card)

        # 6. 译文字号自适应缩放子菜单
        font_menu = self.menu.addMenu("🔍 译文字号")
        font_menu.setStyleSheet(self.menu.styleSheet())
        self.font_group = QActionGroup(self.menu)
        self.font_group.setExclusive(True)
        self.font_actions = []

        cur_scale = config_manager.get("font_scale", 1.0)
        font_options = [
            ("紧凑 (85%)", 0.85),
            ("标准 (100% 默认)", 1.0),
            ("稍大 (115%)", 1.15),
            ("醒目 (130%)", 1.30),
        ]
        for label, val in font_options:
            act = QAction(label, font_menu)
            act.setCheckable(True)
            act.setData(val)
            if abs(cur_scale - val) < 0.05:
                act.setChecked(True)
            act.triggered.connect(lambda checked, v=val: self._set_font_scale(v))
            self.font_group.addAction(act)
            font_menu.addAction(act)
            self.font_actions.append(act)

        # 7. 扫描频率子菜单
        speed_menu = self.menu.addMenu("⏱️ 识别频率")
        speed_menu.setStyleSheet(self.menu.styleSheet())
        self.speed_group = QActionGroup(self.menu)
        self.speed_group.setExclusive(True)
        self.speed_actions = []

        cur_interval = config_manager.get("scan_interval_ms", 300)
        speed_options = [
            ("⚡ 极速 (200ms)", 200),
            ("🚀 均衡 (300ms 默认)", 300),
            ("🍃 节能 (600ms)", 600),
            ("🐢 慢速 (1000ms)", 1000),
        ]
        for label, val in speed_options:
            act = QAction(label, speed_menu)
            act.setCheckable(True)
            act.setData(val)
            if cur_interval == val:
                act.setChecked(True)
            act.triggered.connect(lambda checked, v=val: self._set_interval(v))
            self.speed_group.addAction(act)
            speed_menu.addAction(act)
            self.speed_actions.append(act)

        # 8. 唤出快捷键配置子菜单
        hotkey_menu = self.menu.addMenu("⌨️ 唤出快捷键")
        hotkey_menu.setStyleSheet(self.menu.styleSheet())
        self.hotkey_group = QActionGroup(self.menu)
        self.hotkey_group.setExclusive(True)
        self.hotkey_actions = []

        hotkey_options = [
            ("Alt + R (默认·推荐)", "Alt+R"),
            ("Alt + Q", "Alt+Q"),
            ("Alt + W", "Alt+W"),
            ("Alt + D", "Alt+D"),
            ("Alt + Space", "Alt+Space"),
            ("Ctrl + Shift + R", "Ctrl+Shift+R"),
            ("F4", "F4"),
        ]
        cur_hotkey = config_manager.get("hotkey_summon", "Alt+R")
        for label, hk in hotkey_options:
            act = QAction(label, hotkey_menu)
            act.setCheckable(True)
            act.setData(hk)
            if cur_hotkey.upper() == hk.upper():
                act.setChecked(True)
            act.triggered.connect(lambda checked, k=hk: self._set_hotkey(k))
            self.hotkey_group.addAction(act)
            hotkey_menu.addAction(act)
            self.hotkey_actions.append(act)

        hotkey_menu.addSeparator()
        act_custom_hk = QAction("⌨️ 自定义快捷键...", hotkey_menu)
        if hasattr(self.window, "open_hotkey_settings"):
            act_custom_hk.triggered.connect(self.window.open_hotkey_settings)
        hotkey_menu.addAction(act_custom_hk)

        self.menu.addSeparator()

        # 8. 交互快捷开关
        self.action_wheel_zoom = QAction("🖱️ 框内滚轮缩放窗口", self.menu)
        self.action_wheel_zoom.setCheckable(True)
        self.action_wheel_zoom.setChecked(config_manager.get("wheel_zoom_enabled", True))
        self.action_wheel_zoom.triggered.connect(self._toggle_wheel_zoom)
        self.menu.addAction(self.action_wheel_zoom)

        self.action_status_pill = QAction("💡 显示底部状态提示", self.menu)
        self.action_status_pill.setCheckable(True)
        self.action_status_pill.setChecked(config_manager.get("show_status_pill", False))
        self.action_status_pill.triggered.connect(self._toggle_status_pill)
        self.menu.addAction(self.action_status_pill)

        self.action_pin = QAction("📌 窗口始终置顶", self.menu)
        self.action_pin.setCheckable(True)
        self.action_pin.setChecked(config_manager.get("always_on_top", True))
        self.action_pin.triggered.connect(self._toggle_always_on_top)
        self.menu.addAction(self.action_pin)

        self.menu.addSeparator()

        # 9. 复制译文与 API 配置
        action_copy = QAction("📋 复制最新译文", self.menu)
        action_copy.triggered.connect(self.window.copy_translation)
        self.menu.addAction(action_copy)

        action_api = QAction("🔑 自定义 API 配置...", self.menu)
        action_api.triggered.connect(self.window.open_api_settings)
        self.menu.addAction(action_api)

        self.menu.addSeparator()

        # 10. 退出程序
        action_quit = QAction("❌ 退出程序", self.menu)
        action_quit.triggered.connect(self._quit_app)
        self.menu.addAction(action_quit)

    def sync_states(self):
        """同步菜单所有单选与多选选中状态"""
        self.action_toggle.setChecked(self.window.isVisible())
        self.action_auto.setChecked(config_manager.get("auto_translate", True))
        self.action_wheel_zoom.setChecked(config_manager.get("wheel_zoom_enabled", True))
        self.action_status_pill.setChecked(config_manager.get("show_status_pill", False))
        self.action_pin.setChecked(config_manager.get("always_on_top", True))

        # 同步语种
        cur_src = config_manager.get("source_lang", "auto")
        cur_tgt = config_manager.get("target_lang", "zh-CN")
        for act in getattr(self, "lang_actions", []):
            src, tgt = act.data()
            act.setChecked(cur_src == src and cur_tgt == tgt)

        # 同步引擎
        cur_eng = config_manager.get("engine", "youdao")
        for act in getattr(self, "engine_actions", []):
            act.setChecked(act.data() == cur_eng)

        # 同步显示模式
        cur_mode = config_manager.get("display_mode", "inplace")
        for act in getattr(self, "mode_actions", []):
            act.setChecked(act.data() == cur_mode)

        # 同步字号缩放
        cur_scale = config_manager.get("font_scale", 1.0)
        for act in getattr(self, "font_actions", []):
            act.setChecked(abs(act.data() - cur_scale) < 0.05)

        # 同步扫描频率
        cur_interval = config_manager.get("scan_interval_ms", 300)
        for act in getattr(self, "speed_actions", []):
            act.setChecked(act.data() == cur_interval)

        # 同步唤出快捷键
        cur_hk = config_manager.get("hotkey_summon", "Alt+R").upper()
        for act in getattr(self, "hotkey_actions", []):
            act.setChecked(act.data().upper() == cur_hk)

    def _set_hotkey(self, hk: str):
        if hasattr(self.window, "reload_hotkey"):
            self.window.reload_hotkey(hk)
        self.sync_states()

    def _set_engine(self, engine_id: str):
        config_manager.set("engine", engine_id)
        if engine_id == "openai":
            # 若尚未配置自定义 Key，主动唤出配置面板
            if not config_manager.get("api_key", "").strip():
                self.window.open_api_settings()
        self.sync_states()
        self.window.trigger_refresh()

    def _set_display_mode(self, mode: str):
        config_manager.set("display_mode", mode)
        self.window.apply_mode(mode)
        self.sync_states()

    def _set_font_scale(self, scale: float):
        config_manager.set("font_scale", scale)
        self.sync_states()
        self.window.update()

    def _set_interval(self, interval_ms: int):
        config_manager.set("scan_interval_ms", interval_ms)
        self.sync_states()

    def _toggle_wheel_zoom(self):
        enabled = self.action_wheel_zoom.isChecked()
        config_manager.set("wheel_zoom_enabled", enabled)

    def _toggle_status_pill(self):
        show = self.action_status_pill.isChecked()
        config_manager.set("show_status_pill", show)
        if hasattr(self.window, "set_show_status_pill"):
            self.window.set_show_status_pill(show)

    def _on_tray_activated(self, reason):
        if reason in [QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger]:
            self._toggle_window_visibility()

    def _toggle_window_visibility(self):
        if self.window.isVisible():
            self.window.hide()
            self.action_toggle.setChecked(False)
            self.action_toggle.setText("🪟 显示翻译框")
        else:
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()
            self.action_toggle.setChecked(True)
            self.action_toggle.setText("🪟 隐藏翻译框")

    def _toggle_auto_translate(self):
        is_auto = self.action_auto.isChecked()
        config_manager.set("auto_translate", is_auto)
        self.window.set_auto_translate(is_auto)

    def _set_language(self, src: str, tgt: str):
        config_manager.set("source_lang", src, auto_save=False)
        config_manager.set("target_lang", tgt, auto_save=True)
        self.sync_states()
        self.window.trigger_refresh()

    def _toggle_always_on_top(self):
        is_top = self.action_pin.isChecked()
        self.window.set_always_on_top(is_top)

    def _quit_app(self):
        self.window._force_close = True
        self.window.close()
        self.tray_icon.hide()
        QApplication.quit()


    def show(self):
        self.tray_icon.show()
