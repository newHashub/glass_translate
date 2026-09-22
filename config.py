import json
import os
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    # 窗口几何配置
    "window_x": 200,
    "window_y": 200,
    "window_width": 600,
    "window_height": 360,
    "always_on_top": True,
    # 玻璃透明度与质感 (0.0: 完全透明纯玻璃, 0.1~0.8: 半透磨砂)
    "glass_opacity": 0.0,       # 默认 0.0 完全透明，底色完全不变
    "enable_blur": False,       # 是否开启背景模糊 (默认关闭以保持底层内容清晰)
    "theme_mode": "dark",
    # 显示模式: "inplace" (原地文字替换) 或 "card" (悬浮字幕卡片)
    "display_mode": "inplace",
    "replace_bg_mode": "adaptive", # "adaptive" 自适应吸色盖字, "dark", "light"
    # 翻译与识别配置
    "auto_translate": True,
    "scan_interval_ms": 300,    # 300ms 极速高频检测
    "source_lang": "auto",      # "auto", "en", "ja", "ko", "zh"
    "target_lang": "zh-CN",     # "zh-CN", "en", "ja", "ko"
    "engine": "youdao",         # 默认极速毫秒级 Youdao 引擎
    # 自定义 API 配置 (选填)
    "api_url": "https://api.openai.com/v1/chat/completions",
    "api_key": "",
    "api_model": "gpt-4o-mini",
    # 字体与尺寸
    "font_scale": 1.0,          # 自适应字号缩放系数 (0.8 ~ 1.5)
    "show_original": False,
    # 快捷键与缩放交互
    "wheel_zoom_enabled": True, # 鼠标在框内直接使用滚轮缩放窗口大小
    "show_status_pill": False,  # 是否在窗口底部显示状态提示胶囊 (默认关闭保持极简干净)
    "hotkey_summon": "Alt+R",   # 全局呼出/收起快捷键
}



CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


class ConfigManager:
    """管理并持久化保存用户偏好设置"""

    def __init__(self, filepath: str = CONFIG_FILE):
        self.filepath = filepath
        self.config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> Dict[str, Any]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except Exception as e:
                print(f"[Config] 加载配置文件失败，将使用默认配置: {e}")
        return self.config

    def save(self) -> None:
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Config] 保存配置文件失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        self.config[key] = value
        if auto_save:
            self.save()


# 全局单例配置管理器
config_manager = ConfigManager()
