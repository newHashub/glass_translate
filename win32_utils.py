import ctypes
from ctypes import wintypes
import sys

# Win32 常量定义
WDA_NONE = 0x00000000
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011

# DwmSetWindowAttribute 常量
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2
DWMWCP_ROUNDSMALL = 3
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMSBT_AUTO = 0
DWMSBT_NONE = 1
DWMSBT_MAINWINDOW = 2      # Mica
DWMSBT_TRANSIENTWINDOW = 3  # Acrylic
DWMSBT_TABBEDWINDOW = 4     # Tabbed Mica

# Accent Policy 常量 (Win10 / Win11 通用毛玻璃通道)
ACCENT_DISABLED = 0
ACCENT_ENABLE_GRADIENT = 1
ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
ACCENT_ENABLE_HOSTBACKDROP = 5
WCA_ACCENT_POLICY = 19


class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint32),
        ("AnimationId", ctypes.c_int),
    ]


class WINCOMPATTRDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t),
    ]


def set_exclude_from_capture(hwnd: int, exclude: bool = True) -> bool:
    """
    使窗口在截屏工具（包括 GDI BitBlt、DirectX、桌面捕获）中变为隐形/被穿透。
    这样框内截屏可以直接抓取底层画面，而不会捕获到翻译窗口自身，实现 0 闪烁截屏！
    """
    try:
        user32 = ctypes.windll.user32
        if hasattr(user32, "SetWindowDisplayAffinity"):
            affinity = WDA_EXCLUDEFROMCAPTURE if exclude else WDA_NONE
            res = user32.SetWindowDisplayAffinity(wintypes.HWND(hwnd), affinity)
            return bool(res)
    except Exception as e:
        print(f"[Win32] SetWindowDisplayAffinity failed: {e}")
    return False


def set_rounded_corners(hwnd: int) -> bool:
    """在 Windows 11 上设置原生圆角外观"""
    try:
        dwmapi = ctypes.windll.dwmapi
        corner_pref = ctypes.c_int(DWMWCP_ROUND)
        res = dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            ctypes.c_uint(DWMWA_WINDOW_CORNER_PREFERENCE),
            ctypes.byref(corner_pref),
            ctypes.sizeof(corner_pref),
        )
        return res == 0
    except Exception:
        return False


def enable_acrylic(hwnd: int, tint_color_hex: int = 0x331E1E2E) -> bool:
    """
    为窗口开启 Windows 毛玻璃/亚克力特效。
    tint_color_hex: AABBGGRR 格式的色值
    """
    try:
        # 首先尝试 Windows 11 DWMWA_SYSTEMBACKDROP_TYPE
        dwmapi = ctypes.windll.dwmapi
        backdrop_type = ctypes.c_int(DWMSBT_TRANSIENTWINDOW)  # Acrylic
        hr = dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            ctypes.c_uint(DWMWA_SYSTEMBACKDROP_TYPE),
            ctypes.byref(backdrop_type),
            ctypes.sizeof(backdrop_type),
        )
        if hr == 0:
            set_rounded_corners(hwnd)
            return True
    except Exception:
        pass

    # 若系统版本或 DWMWA 不支持，回退到 SetWindowCompositionAttribute
    try:
        user32 = ctypes.windll.user32
        if hasattr(user32, "SetWindowCompositionAttribute"):
            accent = ACCENT_POLICY()
            accent.AccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND
            accent.AccentFlags = 2  # 绘制磨砂颗粒
            accent.GradientColor = tint_color_hex

            data = WINCOMPATTRDATA()
            data.Attribute = WCA_ACCENT_POLICY
            data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
            data.SizeOfData = ctypes.sizeof(accent)

            res = user32.SetWindowCompositionAttribute(
                wintypes.HWND(hwnd), ctypes.byref(data)
            )
            return bool(res)
    except Exception as e:
        print(f"[Win32] SetWindowCompositionAttribute failed: {e}")

    return False


def get_dpi_scale_for_window(hwnd: int) -> float:
    """获取窗口所在屏幕的高 DPI 缩放倍率 (例如 1.25, 1.5, 2.0)"""
    try:
        user32 = ctypes.windll.user32
        if hasattr(user32, "GetDpiForWindow"):
            dpi = user32.GetDpiForWindow(wintypes.HWND(hwnd))
            if dpi > 0:
                return dpi / 96.0
    except Exception:
        pass
    return 1.0
