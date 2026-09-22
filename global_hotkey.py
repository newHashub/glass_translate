import ctypes
import ctypes.wintypes
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

HOTKEY_ID = 9527
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012


class GlobalHotkeyThread(QThread):
    """
    Windows 全局热键监听线程：
    - 采用原生 Win32 RegisterHotKey 机制
    - 独立轻量消息泵，零 CPU 占用，零卡顿
    - 触发后向 Qt 发射 hotkey_triggered 信号
    """
    hotkey_triggered = pyqtSignal()

    def __init__(self, key_char: str = "R", use_alt: bool = True, parent=None):
        super().__init__(parent)
        self.key_char = key_char.upper()
        self.use_alt = use_alt
        self._running = True
        self._thread_id: Optional[int] = None
        self._registered = False

    def run(self):
        self._thread_id = kernel32.GetCurrentThreadId()

        modifiers = MOD_NOREPEAT
        if self.use_alt:
            modifiers |= MOD_ALT

        vk = ord(self.key_char)
        success = user32.RegisterHotKey(None, HOTKEY_ID, modifiers, vk)
        self._registered = bool(success)
        if not self._registered:
            err = kernel32.GetLastError()
            print(f"[GlobalHotkey] 注册全局热键 Alt+{self.key_char} 失败 (错误码: {err})")
        else:
            print(f"[GlobalHotkey] 成功注册全局热键 Alt+{self.key_char}")

        msg = ctypes.wintypes.MSG()
        while self._running:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break

            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.hotkey_triggered.emit()

            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self._registered:
            user32.UnregisterHotKey(None, HOTKEY_ID)
            self._registered = False
            print("[GlobalHotkey] 已注销全局热键")

    def stop(self):
        self._running = False
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        self.wait(1000)
