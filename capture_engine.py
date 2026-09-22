import time
from typing import Optional, Tuple
from PIL import Image, ImageChops, ImageStat
from PyQt6.QtGui import QGuiApplication, QImage, QPixmap


class CaptureEngine:
    """屏幕区域捕获与画面变化检测引擎"""

    def __init__(self, diff_threshold: float = 2.0):
        self.diff_threshold = diff_threshold
        self._last_thumbnail: Optional[Image.Image] = None
        self._last_rect: Optional[Tuple[int, int, int, int]] = None

    def capture_screen_rect(self, x: int, y: int, w: int, h: int) -> Optional[Image.Image]:
        """
        截取指定屏幕逻辑坐标区域 (x, y, w, h)。
        由于窗口已设置 WDA_EXCLUDEFROMCAPTURE，截屏时 Windows 会自动剔除本翻译器窗口。
        """
        if w <= 10 or h <= 10:
            return None

        screens = QGuiApplication.screens()
        if not screens:
            return None

        # 找到包含该矩形中心的屏幕，若无则使用主屏幕
        target_screen = None
        center_x = x + w // 2
        center_y = y + h // 2
        for s in screens:
            geom = s.geometry()
            if geom.contains(center_x, center_y):
                target_screen = s
                break
        if target_screen is None:
            target_screen = QGuiApplication.primaryScreen()

        if not target_screen:
            return None

        try:
            pixmap: QPixmap = target_screen.grabWindow(0, x, y, w, h)
            if pixmap.isNull() or pixmap.width() == 0 or pixmap.height() == 0:
                return None

            qimg: QImage = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
            width = qimg.width()
            height = qimg.height()
            ptr = qimg.bits()
            ptr.setsize(height * width * 4)
            pil_img = Image.frombuffer("RGBA", (width, height), bytes(ptr), "raw", "RGBA", 0, 1)
            # 转换为 RGB 格式
            return pil_img.convert("RGB")
        except Exception as e:
            print(f"[CaptureEngine] 截屏错误: {e}")
            return None

    def check_has_changed(self, img: Image.Image, rect: Tuple[int, int, int, int]) -> bool:
        """
        通过缩略图差分比对，快速判断框内画面是否发生了变动。
        若画面静止且坐标未变，则无需重复进行 OCR 与翻译，极度节约性能。
        """
        # 如果窗口移动或缩放了尺寸，视为发生变动
        if self._last_rect != rect:
            self._last_rect = rect
            self._update_thumbnail(img)
            return True

        # 生成 80x80 灰度缩略图做快速差异比对
        thumb = img.resize((80, 80), Image.Resampling.BILINEAR).convert("L")

        if self._last_thumbnail is None:
            self._last_thumbnail = thumb
            return True

        # 计算两张缩略图的绝对差异
        diff = ImageChops.difference(thumb, self._last_thumbnail)
        stat = ImageStat.Stat(diff)
        mean_diff = stat.mean[0]  # 平均灰度差值 (0 ~ 255)

        # 转换为百分比差异
        diff_percent = (mean_diff / 255.0) * 100.0

        if diff_percent >= self.diff_threshold:
            self._last_thumbnail = thumb
            return True
        return False

    def _update_thumbnail(self, img: Image.Image) -> None:
        self._last_thumbnail = img.resize((80, 80), Image.Resampling.BILINEAR).convert("L")

    def force_reset(self) -> None:
        """强制重置比对缓存，触发下一次刷新"""
        self._last_thumbnail = None
        self._last_rect = None
