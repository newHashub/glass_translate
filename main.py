import sys
import ctypes
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QFont
from PyQt6.QtWidgets import QApplication

from glass_window import GlassWindow
from tray_manager import TrayManager, generate_tray_icon
from global_hotkey import GlobalHotkeyThread


def hide_console_window():
    """若从 CMD 或批处理脚本启动，立即将控制台黑框隐藏至后台"""
    try:
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd_console = kernel32.GetConsoleWindow()
        if hwnd_console:
            user32.ShowWindow(hwnd_console, 0)  # SW_HIDE = 0
    except Exception:
        pass


def main():
    # 立即隐藏控制台黑框，确保完全无 CMD 弹窗显示在前台
    hide_console_window()

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("GlassTranslate")
    app.setApplicationDisplayName("Windows 实时透视翻译器")
    # 后台驻留模式：即使窗口关闭/隐藏，程序依然常驻系统托盘
    app.setQuitOnLastWindowClosed(False)

    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # 设置应用全局图标
    app_icon = generate_tray_icon()
    app.setWindowIcon(app_icon)

    # 创建翻译窗口与托盘管理器
    window = GlassWindow()
    tray_manager = TrayManager(window)
    window.tray_manager = tray_manager

    # 启动配置中指定的全局唤出热键监听线程 (默认 Alt+R)
    from config import config_manager
    current_hotkey = config_manager.get("hotkey_summon", "Alt+R")
    hotkey_thread = GlobalHotkeyThread(hotkey_str=current_hotkey)
    hotkey_thread.hotkey_triggered.connect(window.toggle_summon)
    hotkey_thread.start()
    window.hotkey_thread = hotkey_thread

    def on_about_to_quit():
        if hasattr(window, "hotkey_thread") and window.hotkey_thread:
            window.hotkey_thread.stop()
        if hasattr(window, "worker") and window.worker:
            window.worker.stop()

    app.aboutToQuit.connect(on_about_to_quit)

    # 呈现托盘图标与窗口
    tray_manager.show()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
