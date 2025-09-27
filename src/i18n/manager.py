import logging
from pathlib import Path
from typing import Dict, Callable, List
from PyQt6.QtCore import QObject, pyqtSignal

from src.config import cfg
from src.i18n.loader import PropertiesLoader

class I18nManager(QObject):

    language_changed = pyqtSignal(str)

    def __init__(self, resources_dir: Path):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.loader = PropertiesLoader(resources_dir)
        self._translations: Dict[str, Dict[str, str]] = {}
        
        # 处理cfg.language.value可能为列表的情况
        lang_value = cfg.language.value
        if isinstance(lang_value, list):
            # 如果是列表，取第一个元素作为当前语言
            self._current_language = lang_value[0] if lang_value else "zh_CN"
            # 修正配置值为字符串
            cfg.language.value = self._current_language
        else:
            self._current_language = lang_value
            
        self._fallback_language = "en_US"
        self._listeners: List[Callable] = []

        self._preload_languages()

    def _preload_languages(self):
        """预加载所有可用的语言文件"""
        available_langs = self.loader.get_available_languages()

        for lang_code in available_langs.keys():
            file_path = self.loader.resources_dir / f"{lang_code}.properties"
            self._translations[lang_code] = self.loader.load_properties(file_path)

        self.logger.info(f"预加载了 {len(self._translations)} 种语言")

    def i18n(self, key: str, default: str = None, **kwargs) -> str:
        if not key:
            return default or ""

        # 优先使用当前语言
        current_translations = self._translations.get(self._current_language, {})
        if key in current_translations:
            translation = current_translations[key]
            if kwargs:
                try:
                    return translation.format(**kwargs)
                except Exception as e:
                    self.logger.error(f"格式化翻译失败 key='{key}': {e}")
                    return translation
            return translation

        fallback_translations = self._translations.get(self._fallback_language, {})
        if key in fallback_translations:
            self.logger.warning(f"词条 '{key}' 在语言 {self._current_language} 中未找到，使用回退语言")
            translation = fallback_translations[key]
            if kwargs:
                try:
                    return translation.format(**kwargs)
                except Exception as e:
                    self.logger.error(f"格式化回退翻译失败 key='{key}': {e}")
                    return translation
            return translation

        # 使用提供的默认值或键本身
        if default is not None:
            self.logger.warning(f"词条 '{key}' 未找到，使用提供的默认值")
            # 进行格式化
            if kwargs:
                try:
                    return default.format(**kwargs)
                except Exception as e:
                    self.logger.error(f"格式化默认值失败 key='{key}': {e}")
                    return default
            return default

        self.logger.error(f"词条 '{key}' 未在任何语言中找到")
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception as e:
                self.logger.error(f"格式化键失败 key='{key}': {e}")
                return key
        return key

    def _set_language(self, language: str):
        if language not in self._translations:
            self.logger.error(f"不支持的语言: {language}")
            return False

        old_language = self._current_language
        self._current_language = language

        cfg.language.value = language

        # 发出信号通知语言改变
        if old_language != language:
            self.language_changed.emit(language)
            self._notify_listeners()

        self.logger.info(f"语言已切换到: {language}")
        return True

    def get_current_language(self) -> str:
        return self._current_language

    def get_available_languages(self) -> Dict[str, str]:
        return self.loader.get_available_languages()

    def add_change_listener(self, listener: Callable):
        """添加语言改变监听器"""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def set_language_with_restart(self, language: str, main_window):
        """设置语言并标记需要重启"""
        if self._set_language(language):
            main_window.is_language_restart = True
            return True
        return False

    def remove_change_listener(self, listener: Callable):
        """移除语言改变监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self):
        """通知所有监听器"""
        for listener in self._listeners:
            try:
                listener()
            except Exception as e:
                self.logger.error(f"语言改变监听器执行失败: {e}")