import ctypes
import ctypes.wintypes
from typing import Optional, Tuple
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


def parse_hotkey(hotkey_str: str) -> Tuple[int, int]:
    """
    解析形如 'Alt+R', 'Ctrl+Alt+R', 'F4', 'Alt+Space' 的热键字符串为 Win32 修饰键与虚拟键码
    """
    parts = [p.strip() for p in hotkey_str.split("+") if p.strip()]
    modifiers = MOD_NOREPEAT
    vk = 0

    vk_map = {
        "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
        "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
        "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
        "SPACE": 0x20, "TAB": 0x09, "ESC": 0x1B, "ESCAPE": 0x1B,
        "`": 0xC0, "~": 0xC0,
    }

    for p in parts:
        pu = p.upper()
        if pu in ("ALT", "MENU"):
            modifiers |= MOD_ALT
        elif pu in ("CTRL", "CONTROL"):
            modifiers |= MOD_CONTROL
        elif pu == "SHIFT":
            modifiers |= MOD_SHIFT
        elif pu in ("WIN", "WINDOWS", "SUPER"):
            modifiers |= MOD_WIN
        elif pu in vk_map:
            vk = vk_map[pu]
        elif len(p) == 1:
            vk = ord(pu)

    return modifiers, vk


class GlobalHotkeyThread(QThread):
    """
    Windows 全局热键监听线程：
    - 采用原生 Win32 RegisterHotKey 机制
    - 独立轻量消息泵，零 CPU 占用，零卡顿
    - 支持任意组合键与功能键动态配置解析
    - 触发后向 Qt 发射 hotkey_triggered 信号
    """
    hotkey_triggered = pyqtSignal()
    registration_result = pyqtSignal(bool, str)

    def __init__(self, hotkey_or_char: str = "Alt+R", use_alt: bool = True, parent=None, hotkey_str: Optional[str] = None, key_char: Optional[str] = None):
        super().__init__(parent)
        if hotkey_str is not None:
            self.hotkey_str = hotkey_str
        elif key_char is not None:
            prefix = "Alt+" if use_alt else ""
            self.hotkey_str = f"{prefix}{key_char.upper()}"
        elif len(hotkey_or_char) == 1 and hotkey_or_char.isalnum():
            prefix = "Alt+" if use_alt else ""
            self.hotkey_str = f"{prefix}{hotkey_or_char.upper()}"
        else:
            self.hotkey_str = hotkey_or_char

        self._running = True
        self._thread_id: Optional[int] = None
        self._registered = False

    def run(self):
        self._thread_id = kernel32.GetCurrentThreadId()

        modifiers, vk = parse_hotkey(self.hotkey_str)
        if vk == 0:
            msg = f"无效的热键定义: {self.hotkey_str}"
            print(f"[GlobalHotkey] {msg}")
            self.registration_result.emit(False, msg)
            return

        success = user32.RegisterHotKey(None, HOTKEY_ID, modifiers, vk)
        self._registered = bool(success)
        if not self._registered:
            err = kernel32.GetLastError()
            msg = f"注册全局热键 [{self.hotkey_str}] 失败 (可能被其他软件占用，错误码: {err})"
            print(f"[GlobalHotkey] {msg}")
            self.registration_result.emit(False, msg)
        else:
            msg = f"成功注册全局热键 [{self.hotkey_str}]"
            print(f"[GlobalHotkey] {msg}")
            self.registration_result.emit(True, msg)

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
            print(f"[GlobalHotkey] 已注销全局热键 [{self.hotkey_str}]")

    def stop(self):
        self._running = False
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        self.wait(1000)
